"""Benachrichtigungen bei Änderungen im Vertretungsplan.

Ablauf
------
1. Jede Änderung (Event ``change`` auf dem Bus, ``features_common.mutate``) weckt den
   Hintergrund-Thread (:func:`kick`).
2. :func:`check_changes` berechnet die Vertretungspläne für **heute** und den **nächsten
   Schultag** (gecacht, siehe ``features_common.day_plan``) und vergleicht sie mit dem
   zuletzt bekannten Stand. Der erste Stand eines Tages ist nur die Ausgangsbasis.
3. Unterschiede → Einträge in ``notifications_outbox``:
   * Webhooks an ``settings.webhooks`` (Payload/Signatur aus ``integrations.webhooks``,
     Secret ``SM_WEBHOOK_SECRET``, Header ``X-Schulmanager-Signature``),
   * E-Mails an betroffene Lehrkräfte (wenn SMTP konfiguriert; Adresse aus dem verknüpften
     Benutzerkonto, sonst ``Teacher.email``).
4. :func:`dispatch_pending` stellt zu – mit Retry und exponentiellem Backoff.

:func:`start_dispatcher` / :func:`stop_dispatcher` werden vom Lifespan der App aufgerufen
(no-op bei ``SM_NOTIFY_DISPATCHER=0``).
"""
from __future__ import annotations

import hashlib
import json
import logging
import smtplib
import ssl
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Optional

from ..branding import PRODUCT_NAME
from . import net_guard

log = logging.getLogger("schulmanager.notify")

EVENT_NAME = "substitutions.changed"
MAX_ATTEMPTS = 8
BACKOFF_BASE = 30          # Sekunden; danach 60, 120, ... (max. BACKOFF_MAX)
BACKOFF_MAX = 6 * 3600
HTTP_TIMEOUT = 10
DEFAULT_INTERVAL = 5.0
SIGNIFICANT = ("kind", "period", "classes", "subject", "teacher", "substitute", "room", "new_room", "moved_from",
               "note", "part", "lesson_id", "warning")
KIND_LABELS = {
    "vertretung": "Vertretung", "betreuung": "Betreuung", "entfall": "Entfall", "verlegung": "Verlegung",
    "raumaenderung": "Raumänderung", "mitbetreuung": "Mitbetreuung", "klasse_abwesend": "Klasse abwesend",
    "aufsicht": "Pausenaufsicht", "klausur": "Klausur",
}
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
SECURE_KINDS = ("secure_email", "sms")  # Konto-Nachrichten (§11.2, server/auth_messages.py)

_lock = threading.RLock()
_wake = threading.Event()
_stop = threading.Event()
_thread: Optional[threading.Thread] = None
_state: dict[str, Any] = {"baseline": {}, "version": None, "days": None}
_interval = DEFAULT_INTERVAL


# =================================================================== Steuerung
def kick() -> None:
    """Weckt den Dispatcher (nach einer Änderung)."""
    _wake.set()


def _listener(event: str, data: dict) -> None:
    if event == "change":
        _wake.set()


def start_dispatcher(interval: float = DEFAULT_INTERVAL) -> bool:
    """Startet den Hintergrund-Thread (idempotent). ``False`` wenn per Konfiguration deaktiviert."""
    global _thread, _interval
    from .config import config
    if not getattr(config, "notify_dispatcher", True):
        log.info("Benachrichtigungs-Dispatcher deaktiviert (SM_NOTIFY_DISPATCHER=0)")
        return False
    with _lock:
        if _thread is not None and _thread.is_alive():
            return True
        _interval = max(0.5, float(interval))
        _stop.clear()
        try:
            from .events import bus
            bus.add_listener(_listener)
        except Exception:  # pragma: no cover
            log.debug("Event-Listener konnte nicht registriert werden", exc_info=True)
        _reset_stale()
        _thread = threading.Thread(target=_loop, name="sm-notify", daemon=True)
        _thread.start()
    log.info("Benachrichtigungs-Dispatcher gestartet")
    return True


def stop_dispatcher(timeout: float = 5.0) -> None:
    global _thread
    with _lock:
        t = _thread
        _thread = None
    _stop.set()
    _wake.set()
    try:
        from .events import bus
        bus.remove_listener(_listener)
    except Exception:  # pragma: no cover
        pass
    if t is not None and t.is_alive() and t is not threading.current_thread():
        t.join(timeout)


def is_running() -> bool:
    return _thread is not None and _thread.is_alive()


def reset_state() -> None:
    """Vergisst den zuletzt bekannten Planstand (Tests / nach Komplettimport)."""
    with _lock:
        _state.update(baseline={}, version=None, days=None)


def _loop() -> None:
    while not _stop.is_set():
        try:
            check_changes()
        except Exception:  # noqa: BLE001
            log.exception("Prüfung auf Vertretungsplan-Änderungen fehlgeschlagen")
        try:
            dispatch_pending()
        except Exception:  # noqa: BLE001
            log.exception("Zustellung der Benachrichtigungen fehlgeschlagen")
        _wake.wait(_interval)
        _wake.clear()


# =================================================================== Änderungen erkennen
def _days(school, today: date) -> list[date]:
    from schulmanager.calendar_utils import is_school_day
    out = [today]
    d = today
    for _ in range(14):
        d += timedelta(days=1)
        if is_school_day(school, d)[0]:
            out.append(d)
            break
    return out


def _signature(entry: dict) -> dict:
    return {k: entry.get(k) for k in SIGNIFICANT}


def _entry_key(entry: dict) -> str:
    return str(entry.get("id") or f"{entry.get('lesson_id')}:{entry.get('period')}:{entry.get('part')}"
               f":{entry.get('kind')}")


def diff_entries(old: dict[str, dict], new: dict[str, dict]) -> dict[str, list]:
    """Vergleicht zwei Stände ``{key: entry}`` → ``{"added","changed","removed"}``."""
    added = [new[k] for k in new if k not in old]
    removed = [old[k] for k in old if k not in new]
    changed = [new[k] for k in new if k in old and _signature(new[k]) != _signature(old[k])]
    return {"added": added, "changed": changed, "removed": removed}


def check_changes(today: Optional[date] = None) -> int:
    """Vergleicht heute/nächster Schultag mit dem letzten Stand, erzeugt Outbox-Einträge.

    Gibt die Anzahl neu erzeugter Outbox-Einträge zurück."""
    from .routes.features_common import absence_reasons, day_plan, scrub, snap_key, snapshot
    today = today or date.today()
    created = 0
    with _lock:
        snap = snapshot()
        ver, school = snap
        key = snap_key(snap)
        days = _days(school, today)
        if key == _state["version"] and days == _state["days"]:
            return 0
        if _state["version"] is not None and isinstance(key, tuple) and isinstance(_state["version"], tuple) \
                and key[0] < _state["version"][0]:
            _state["baseline"] = {}  # andere Datenbank / Neuinstallation: Basis neu aufbauen
        baseline: dict = _state["baseline"]
        for d in days:
            _, plan = day_plan(d, snap)
            reasons = absence_reasons(school, d)
            current = {}
            for e in plan.get("entries") or []:
                e = {k: v for k, v in e.items() if k not in ("reason", "absence_reason")}
                if reasons and e.get("note"):
                    e["note"] = scrub(e["note"], reasons)
                current[_entry_key(e)] = e
            old = baseline.get(d.isoformat())
            baseline[d.isoformat()] = current
            if old is None:
                continue
            diff = diff_entries(old, current)
            if any(diff.values()):
                created += _enqueue(school, d, ver, diff, plan)
                try:  # Glocke in der App (Benachrichtigungszentrale), siehe notification_hooks.plan_changes
                    from . import notification_hooks
                    notification_hooks.plan_changes(school, d, diff, plan)
                except Exception:  # noqa: BLE001
                    log.debug("Benachrichtigungszentrale: Planänderung nicht gemeldet", exc_info=True)
        for key in list(baseline):
            if key not in {d.isoformat() for d in days}:
                baseline.pop(key, None)
        _state["version"], _state["days"] = key, days
    if created:
        _wake.set()
    return created


# =================================================================== Outbox
def _webhook_data(d: date, ver: Any, diff: dict) -> dict:
    return {"date": d.isoformat(), "dates": [d.isoformat()], "version": ver, "added": diff["added"],
            "changed": diff["changed"],
            "removed": [{"id": e.get("id"), "period": e.get("period"), "classes": e.get("classes"),
                         "kind": e.get("kind"), "lesson_id": e.get("lesson_id"), "part": e.get("part")}
                        for e in diff["removed"]]}


def _encode(body: dict) -> str:
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


def _webhook_body(school, data: dict) -> str:
    try:
        from schulmanager.integrations.webhooks import payload
        body = payload(EVENT_NAME, data, school=school)
    except ImportError:  # pragma: no cover - Integrationen fehlen
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        body = {"event": EVENT_NAME, "sent_at": now, "data": data}
    return _encode(body)


def _dedupe(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:48]


def _add(db, kind: str, target: str, subject: str, payload: str, key: str) -> bool:
    from sqlalchemy import select

    from .db import utcnow
    from .db_models import NotificationOutbox as O
    if db.scalar(select(O.id).where(O.dedupe_key == key).limit(1)) is not None:
        return False
    db.add(O(kind=kind, target=target[:500], subject=subject[:300], payload=payload, status="pending",
             attempts=0, next_attempt_at=utcnow(), dedupe_key=key, created_at=utcnow()))
    return True


def _enqueue(school, d: date, ver: Any, diff: dict, plan: dict) -> int:
    from .config import config
    from .db import session_scope
    n = 0
    with session_scope() as db:
        hooks = [u for u in (school.settings.webhooks or []) if u]
        if hooks:
            data = _webhook_data(d, ver, diff)
            # R3: Woche als Ziffer bzw. WeekInfo, Art des Tages (Schema v1 bleibt, Felder kommen hinzu)
            data.update(week_no=(plan or {}).get("week_no", 0), week_info=(plan or {}).get("week_info") or {},
                        day_kind=(plan or {}).get("day_kind") or "unterricht")
            key_data = _encode({k: v for k, v in data.items() if k != "version"})
            for url in hooks:
                if _add(db, "webhook", url, EVENT_NAME, _webhook_body(school, data), _dedupe("wh", url, key_data)):
                    n += 1
        if getattr(config, "smtp_enabled", False):
            for tid, (address, name, lines) in _emails(db, school, d, diff, plan).items():
                text = _mail_text(school, d, name, lines)
                subject = f"Vertretungsplan {WEEKDAYS[d.weekday()]}, {d.strftime('%d.%m.%Y')}: Änderungen für Sie"
                if _add(db, "email", address, subject, text, _dedupe("mail", address, d.isoformat(), str(ver), text)):
                    n += 1
    return n


def _affected(entry: dict, absent: set[str]) -> set[str]:
    out = set()
    sub = entry.get("substitute")
    if sub:
        out.add(sub)
    t = entry.get("teacher")
    if t and t not in absent and entry.get("kind") in ("verlegung", "raumaenderung", "aufsicht", "klausur",
                                                        "mitbetreuung", "klasse_abwesend"):
        out.add(t)
    return out


def _line(school, entry: dict, tid: str, removed: bool = False) -> str:
    st = school.settings
    p = entry.get("period")
    label = entry.get("period_label") or (f"{p + 1}." if isinstance(p, int) else "")
    time = entry.get("time") or (st.period_times[p] if isinstance(p, int) and 0 <= p < len(st.period_times) else "")
    head = f"{label} Stunde" + (f" ({time})" if time else "")
    classes = ", ".join(entry.get("classes") or [])
    what = KIND_LABELS.get(entry.get("kind") or "", entry.get("kind") or "Änderung")
    if entry.get("kind") == "aufsicht":
        head = entry.get("break_name") or "Pause"
    parts = [f"{head}: {classes} {entry.get('subject') or ''}".strip(), what]
    if entry.get("substitute") == tid and entry.get("teacher") and entry.get("teacher") != tid:
        parts.append(f"für {entry['teacher']}")
    room = entry.get("new_room") or entry.get("room")
    if room:
        parts.append(f"Raum {room}")
    if entry.get("note"):
        parts.append(str(entry["note"]))
    text = " – ".join(x for x in parts if x)
    return f"• {text} (aufgehoben)" if removed else f"• {text}"


def _emails(db, school, d: date, diff: dict, plan: dict) -> dict[str, tuple[str, str, list[str]]]:
    from sqlalchemy import select

    from .db_models import User
    absent = set(plan.get("absent_teachers") or [])
    lines: dict[str, list[str]] = {}
    for key in ("added", "changed", "removed"):
        for e in diff[key]:
            for tid in _affected(e, absent):
                lines.setdefault(tid, []).append(_line(school, e, tid, removed=key == "removed"))
    if not lines:
        return {}
    teachers = school.index("teachers")
    users = {u.teacher_id: u for u in db.scalars(select(User).where(User.teacher_id.in_(sorted(lines)),
                                                                     User.active.is_(True)))}
    out = {}
    for tid, ls in lines.items():
        t = teachers.get(tid)
        u = users.get(tid)
        address = (u.email if u and u.email else None) or (getattr(t, "email", "") if t else "")
        if not address or "@" not in address:
            continue
        name = (t.name if t else None) or (u.display_name if u else tid)
        out[tid] = (address, name, sorted(set(ls)))
    return out


def _mail_text(school, d: date, name: str, lines: list[str]) -> str:
    from .config import config
    greeting = f"Guten Tag {name}," if name else "Guten Tag,"
    url = f"{config.base_url}/vertretungsplan?date={d.isoformat()}"
    return "\n".join([
        greeting, "",
        f"im Vertretungsplan für {WEEKDAYS[d.weekday()]}, {d.strftime('%d.%m.%Y')} gibt es Änderungen, "
        "die Sie betreffen:", "",
        *lines, "",
        f"Aktueller Plan: {url}", "",
        f"Bitte beachten Sie immer den aktuellen Vertretungsplan im {PRODUCT_NAME}.",
        f"Diese Nachricht wurde automatisch erzeugt ({school.settings.school_name}).",
    ])


# =================================================================== Zustellung
def _reset_stale() -> None:
    """Nach einem Absturz hängende ``sending``-Einträge wieder freigeben."""
    try:
        from sqlalchemy import update

        from .db import session_scope
        from .db_models import NotificationOutbox as O
        with session_scope() as db:
            db.execute(update(O).where(O.status == "sending").values(status="pending"))
    except Exception:  # pragma: no cover
        log.debug("Outbox konnte nicht zurückgesetzt werden", exc_info=True)


def backoff_seconds(attempts: int) -> int:
    return int(min(BACKOFF_MAX, BACKOFF_BASE * (2 ** max(0, attempts - 1))))


def _sign(raw: bytes) -> Optional[str]:
    from .config import config
    secret = getattr(config, "webhook_secret", None)
    if not secret:
        return None
    try:
        from schulmanager.integrations.webhooks import sign
    except ImportError:  # pragma: no cover - Integrationen fehlen: gleiches Verfahren lokal
        import hmac
        return "sha256=" + hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return sign(raw, secret)


def prepare_webhook(body: str, event: str, delivery_id: Any = None) -> tuple[bytes, dict[str, str]]:
    """Body für die Zustellung: ``sent_at`` wird beim (erneuten) Senden aktualisiert (Replay-Schutz
    der Empfänger), die Zustell-ID bleibt gleich. Liefert ``(rohe Bytes, Header)``."""
    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        obj = None
    if isinstance(obj, dict):
        if "sent_at" in obj:
            obj["sent_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        delivery_id = obj.get("id") or delivery_id
        try:
            from schulmanager.integrations.webhooks import encode
            raw = encode(obj)
        except ImportError:  # pragma: no cover
            raw = _encode(obj).encode("utf-8")
    else:
        raw = body.encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8", "User-Agent": "Schulmanager-Webhook/1",
               "X-Schulmanager-Event": event, "X-Schulmanager-Timestamp": str(int(time.time()))}
    if delivery_id is not None:
        headers["X-Schulmanager-Delivery"] = str(delivery_id)
    sig = _sign(raw)
    if sig:
        headers["X-Schulmanager-Signature"] = sig
    return raw, headers


def send_webhook(url: str, body: str, event: str, delivery_id: Any = None) -> None:
    """POST mit JSON-Body (signiert); wirft bei Fehler/Nicht-2xx."""
    raw, headers = prepare_webhook(body, event, delivery_id)
    req = urllib.request.Request(url, data=raw, headers=headers, method="POST")
    try:
        with net_guard.urlopen(req, "webhook", timeout=HTTP_TIMEOUT) as resp:   # Zielprüfung gegen SSRF
            if not 200 <= resp.status < 300:
                raise RuntimeError(f"HTTP {resp.status}")
    except net_guard.BlockedTarget as exc:
        raise RuntimeError(net_guard.GENERIC) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, net_guard.BlockedTarget):
            raise RuntimeError(net_guard.GENERIC) from exc
        raise


def send_email(to: str, subject: str, text: str, attachments: Optional[list[dict]] = None) -> None:
    """SMTP-Versand; ``attachments`` = ``[{"filename", "content_type", "data": bytes}]`` (§11.2)."""
    from .config import config
    msg = EmailMessage()
    msg["From"] = config.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    for att in attachments or []:
        maintype, _, subtype = (att.get("content_type") or "application/octet-stream").partition("/")
        msg.add_attachment(att.get("data") or b"", maintype=maintype or "application",
                           subtype=subtype or "octet-stream", filename=att.get("filename") or "anhang.bin")
    mode = (getattr(config, "smtp_tls", "starttls") or "starttls").lower()
    ctx = ssl.create_default_context()
    if mode == "ssl":
        server: smtplib.SMTP = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=20, context=ctx)
    else:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=20)
    with server:
        if mode == "starttls":
            server.starttls(context=ctx)
        if config.smtp_user:
            server.login(config.smtp_user, config.smtp_password or "")
        server.send_message(msg)


def _deliver(kind: str, target: str, subject: str, payload: str, row_id: Any) -> None:
    if kind == "webhook":
        send_webhook(target, payload, subject or EVENT_NAME, row_id)
    elif kind == "email":
        send_email(target, subject or PRODUCT_NAME, payload)
    elif kind in SECURE_KINDS:  # §11.2: verschlüsselter Payload (Empfänger, Text, Anhänge)
        from .auth_messages import deliver
        deliver(kind, payload, row_id)
    else:
        raise ValueError(f"Unbekannte Art {kind}")


def dispatch_pending(limit: int = 50, now: Optional[datetime] = None) -> dict[str, int]:
    """Stellt fällige Outbox-Einträge zu (Retry mit exponentiellem Backoff)."""
    from sqlalchemy import or_, select, update

    from .db import session_scope, utcnow
    from .db_models import NotificationOutbox as O
    now = now or utcnow()
    stats = {"sent": 0, "retry": 0, "failed": 0}
    with session_scope() as db:
        ids = list(db.scalars(select(O.id).where(O.status == "pending")
                              .where(or_(O.next_attempt_at.is_(None), O.next_attempt_at <= now))
                              .order_by(O.id).limit(limit)))
    for oid in ids:
        with session_scope() as db:
            claimed = db.execute(update(O).where(O.id == oid, O.status == "pending").values(status="sending"))
            if claimed.rowcount != 1:
                continue
            row = db.get(O, oid)
            kind, target, subject, payload = row.kind, row.target, row.subject or "", row.payload
        error = None
        try:
            _deliver(kind, target, subject, payload, oid)
        except (urllib.error.URLError, OSError, smtplib.SMTPException, RuntimeError, ValueError) as exc:
            error = f"{type(exc).__name__}: {exc}"[:2000]
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"[:2000]
        with session_scope() as db:
            row = db.get(O, oid)
            if row is None:
                continue
            row.attempts = (row.attempts or 0) + 1
            if error is None:
                row.status, row.sent_at, row.last_error = "sent", utcnow(), None
                stats["sent"] += 1
            elif row.attempts >= MAX_ATTEMPTS:
                row.status, row.last_error = "failed", error
                stats["failed"] += 1
                log.warning("Benachrichtigung %s an %s endgültig fehlgeschlagen: %s", oid, target, error)
            else:
                row.status, row.last_error = "pending", error
                row.next_attempt_at = utcnow() + timedelta(seconds=backoff_seconds(row.attempts))
                stats["retry"] += 1
            if kind in SECURE_KINDS and row.status in ("sent", "failed"):
                row.payload = ""  # §11.2: Inhalt (verschlüsselt) nach Zustellung nicht aufbewahren
    return stats
