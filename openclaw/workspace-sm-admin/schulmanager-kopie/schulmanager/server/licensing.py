"""Lizenz der Schule: Lizenzschlüssel, den der Anbieter auf seinem Lizenzserver verwaltet (``lizenzserver/``).

Ablauf:

* Die Administration trägt den Schlüssel ein (``SPUL-XXXX-XXXX-XXXX-XXXX``, letzte Stelle = Prüfziffer). Die Instanz
  ruft ``POST /api/v1/activate`` auf (Schlüssel, stabile Instanz-ID, ``SM_BASE_URL``); der Server **bindet** den
  Schlüssel an diese Instanz, ein zweiter Server mit demselben Schlüssel wird abgelehnt.
* Danach fragt die Instanz beim Start und mindestens alle 24 Stunden ``POST /api/v1/check`` ab. Die Antwort ist mit dem
  privaten Schlüssel des Anbieters signiert (Ed25519, geprüft mit dem eingebauten ``VENDOR_PUBKEY``; Nonce und
  Instanz-ID müssen passen) und enthält ein kurzlebiges Bestätigungs-Token: Status, Lizenznehmer, Grenzen,
  „Abo aktiv bis“, ``confirmed_until``. Eine falsch oder gar nicht signierte Antwort zählt wie „Server nicht erreichbar“.
* Sofortsperre: Bei der Aktivierung erzeugt der Server je Server-Lizenz einen geheimen Sperr-Schlüssel (``lock_secret``,
  im signierten Ergebnis, nur dort). Drückt der Anbieter „Sofort sperren“ (Schule oder einzelner Server), liefert der Server
  beim nächsten Kontakt ``lock`` = ``{command, text, issued_at, mac}``; der MAC (HMAC-SHA256 mit dem Sperr-Schlüssel über
  Befehl, Text, Zeit, **Nonce der Anfrage** und Instanz-ID) macht den Befehl an Schlüssel, Instanz und genau diese Anfrage
  gebunden (kein Replay, kein Befehl einer anderen Schule). Mit gültigem MAC sperrt die Instanz sofort und ohne Kulanz
  (``reason=blocked``) bis ``unlock`` kommt. Zusätzlich zur täglichen Prüfung fragt die Instanz alle 15 Minuten kurz
  ``POST /api/v1/ping`` ab.
* Die Instanz kennt **kein festes Ablaufdatum**; alles steuert der Anbieter-Server. Gespeichert werden
  ``<data_dir>/license.json`` (nur der Schlüssel) und ``<data_dir>/license_state.json`` (Instanz-ID, letztes Token).
* Stufen (nur mit Durchsetzung, ``SM_LICENSE_ENFORCE``; in ``SM_MODE=production`` immer an):
  ``valid`` (ggf. mit Vorwarnung 30/14/7/1 Tage vor „Abo aktiv bis“) → ``grace`` (Kulanzzeit: für alle nur lesbar) →
  ``locked`` (gesperrt: API und Oberfläche für alle zu; offen bleiben Anmeldung/Abmeldung und die Lizenzseite für
  Konten mit ``license.manage``). Kein Schlüssel = ``locked`` mit ``reason=missing`` (Begrüßungsseite).
* Gründe (``reason``): ``paused``, ``cancelled``, ``unknown``, ``unbound``/``bound`` → sofort gesperrt;
  ``expired`` („Abo aktiv bis“ überschritten) → ``grace_days`` nur lesen, dann gesperrt; ``offline`` (``confirmed_until``
  überschritten, Server nicht erreichbar) → ``grace_days`` nur lesen, dann gesperrt; bis dahin läuft alles weiter.

Kanonische Bytes: ``json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()`` – gleiches
Protokoll wie der Lizenzserver.
"""
from __future__ import annotations

import base64
import json
import logging
import secrets
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from . import net_guard
from .config import config

log = logging.getLogger("schulmanager.license")

STATES = ("valid", "grace", "locked")
WARN_DAYS = (30, 14, 7, 1)      # Vorwarnung: Banner ab 30 Tagen, Benachrichtigung je Stufe
VENDOR_PUBKEY = "ilqnzjDQ5rEVEOrMwFoejEVWHJlX4UNEqdwy9mCXiOA="   # öffentlicher Schlüssel des Anbieters (base64)
VENDOR_SERVER = "https://lizenz.l0rdr3spawn.duckdns.org:10489"      # Lizenzserver des Anbieters
PREFIX = "SPUL"
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"        # wie im Lizenzserver (ohne 0/1/I/L/O)
CACHE_TTL = 30.0
CHECK_RETRY_HOURS = 1           # nach einer fehlgeschlagenen Prüfung stündlich erneut versuchen
OK_STATUS = ("active", "expired")
LOCK_REASON = {"paused": "paused", "cancelled": "cancelled", "unknown": "unknown", "unbound": "unbound",
               "bound_elsewhere": "bound"}
LOCK_TEXT = {
    "paused": "Lizenz pausiert – bitte Anbieter kontaktieren.",
    "cancelled": "Die Lizenz wurde gekündigt.",
    "unknown": "Der Lizenzschlüssel ist dem Anbieter nicht bekannt.",
    "unbound": "Der Schlüssel ist nicht mehr an diese Installation gebunden – bitte tragen Sie ihn neu ein.",
    "bound": "Der Schlüssel ist an eine andere Installation gebunden.",
}
_RANK = {"valid": 0, "grace": 1, "locked": 2}
_lock = threading.Lock()
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_cache: dict = {}


def _now() -> datetime:
    """Aktuelle Zeit (UTC); eigene Funktion, damit Tests die Uhr verstellen können."""
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- Schlüsseltext
def _check_char(body: str) -> str:
    return ALPHABET[sum((i + 1) * ALPHABET.index(c) for i, c in enumerate(body)) % len(ALPHABET)]


def normalize_key(text: str) -> str:
    """Eingabe → ``SPUL-XXXX-XXXX-XXXX-XXXX`` oder ``""`` (falsche Form oder Prüfziffer = Tippfehler)."""
    raw = "".join(ch for ch in (text or "").upper() if ch.isalnum())
    if not raw.startswith(PREFIX):
        return ""
    body = raw[len(PREFIX):]
    if len(body) != 16 or any(c not in ALPHABET for c in body) or _check_char(body[:15]) != body[15]:
        return ""
    return f"{PREFIX}-{body[0:4]}-{body[4:8]}-{body[8:12]}-{body[12:16]}"


# --------------------------------------------------------------------------- Signaturen
def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _pubkey_text() -> str:
    """Prüfschlüssel: im Betriebsmodus ``production`` zuerst der eingebaute (``VENDOR_PUBKEY``), sonst die Umgebung."""
    if VENDOR_PUBKEY and config.mode == "production":
        return VENDOR_PUBKEY.strip()
    return (config.license_pubkey or VENDOR_PUBKEY or "").strip()


def _server_url() -> str:
    """Lizenzserver: in Produktion immer der eingebaute, sonst ``SM_LICENSE_SERVER`` (Entwicklung/Test)."""
    if config.mode == "production":
        return VENDOR_SERVER
    return (config.license_server or VENDOR_SERVER).rstrip("/")


def _public_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    raw = _pubkey_text()
    if not raw:
        return None
    try:
        return Ed25519PublicKey.from_public_bytes(base64.b64decode(raw))
    except Exception:  # noqa: BLE001
        log.error("Der öffentliche Lizenz-Prüfschlüssel ist kein gültiger Ed25519-Schlüssel")
        return None


def verify(obj: Any, signature: str) -> bool:
    from cryptography.exceptions import InvalidSignature
    key = _public_key()
    if key is None or not signature:
        return False
    try:
        key.verify(base64.b64decode(signature), canonical(obj))
        return True
    except (InvalidSignature, ValueError):
        return False


# --------------------------------------------------------------------------- Dateien
def license_path() -> Path:
    return Path(config.license_file) if config.license_file else config.data_dir / "license.json"


def state_path() -> Path:
    return config.data_dir / "license_state.json"


def _read_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def load_state() -> dict:
    st = _read_json(state_path()) or {}
    if not st.get("instance_id"):
        st["instance_id"] = secrets.token_hex(12)
        try:
            _write_json(state_path(), st)
        except OSError:
            pass
    return st


def load_key() -> Optional[str]:
    """Der eingetragene Schlüssel (``None``, wenn keiner da ist oder die Datei kaputt/manipuliert ist)."""
    data = _read_json(license_path())
    key = normalize_key(str((data or {}).get("key") or ""))
    return key or None


def _parse_dt(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _day(text: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(text)[:10]) if text else None
    except ValueError:
        return None


def _token(st: dict, key: Optional[str]) -> Optional[dict]:
    """Letztes signiertes Ergebnis des Lizenzservers – nur, wenn Signatur, Instanz und Schlüssel (letzte 4 Zeichen)
    stimmen. Ein von Hand geändertes oder von einer anderen Instanz kopiertes Token zählt als nicht vorhanden."""
    tok = st.get("token")
    if not key or not isinstance(tok, dict) or not isinstance(tok.get("result"), dict):
        return None
    res = tok["result"]
    if not verify(res, str(tok.get("signature") or "")):
        return None
    if res.get("instance_id") != st.get("instance_id") or res.get("key_last4") not in (key[-4:], None):
        return None
    return res


# --------------------------------------------------------------------------- Zustand
def _counts() -> dict:
    out: dict = {"students": None, "users": None}
    try:
        from sqlalchemy import func, select

        from .db import session_scope
        from .db_models import User
        from .store import get_store
        out["students"] = len(get_store().school.students)
        with session_scope() as db:
            out["users"] = db.scalar(select(func.count(User.id)).where(User.active.is_(True))) or 0
    except Exception:  # noqa: BLE001
        pass
    return out


def _others(tok: dict) -> Optional[list]:
    """Die anderen Server der Schule laut Prüf-Antwort (Bezeichnung, Schlüssel, Zustand, URL, Version, letzte Prüfung)."""
    servers = tok.get("servers")
    if not isinstance(servers, list):
        return None
    return [s for s in servers if isinstance(s, dict) and not s.get("this")]


def _locks(ev: dict) -> bool:
    """Sperrt diese Stufe die Anwendung (mit Durchsetzung)? Auch „kein Schlüssel“: eine frische Instanz lässt nur die
    Administration weiter, die dann den Schlüssel eingibt (Begrüßungsseite)."""
    return ev["state"] == "locked"


def evaluate(*, now: Optional[datetime] = None) -> dict:
    """Stufe der Lizenz ohne Datenbankzugriff (schnell, für jede Anfrage): ``state``, ``stage``, ``reason``,
    ``message``, ``warning``, ``days_left``, ``grace_until`` u. a. Unabhängig von ``SM_LICENSE_ENFORCE`` (das
    entscheidet erst :func:`status`)."""
    now = now or _now()
    today = now.date()
    key = load_key()
    st = load_state()
    out: dict[str, Any] = {"state": "valid", "stage": "ok", "reason": "", "message": "", "warning": "", "days_left": None,
                           "grace_until": None, "licensee": None, "valid_until": None, "key_last4": key[-4:] if key else None,
                           "confirmed_until": None, "last_ok_at": None, "last_status": None, "max_users": None,
                           "max_students": None}
    if key is None:
        out.update(state="locked", stage="locked", reason="missing", message="Es ist noch kein Lizenzschlüssel eingetragen.")
        return out
    tok = _token(st, key)
    if tok is None:
        out.update(state="locked", stage="locked", reason="unconfirmed",
                   message="Die Lizenz wurde noch nicht vom Anbieter bestätigt.")
        return out
    status = str(tok.get("status") or "")
    checked = _parse_dt(tok.get("checked_at"))
    conf = _parse_dt(tok.get("confirmed_until"))
    valid_until = _day(tok.get("valid_until"))
    grace = int(tok["grace_days"]) if tok.get("grace_days") is not None else config.license_grace_days
    out.update(licensee=tok.get("licensee"), valid_until=valid_until.isoformat() if valid_until else None,
               days_left=(valid_until - today).days if valid_until else None, last_status=status,
               last_ok_at=tok.get("checked_at"), key_last4=key[-4:],
               confirmed_until=tok.get("confirmed_until"), max_users=tok.get("max_users"),
               max_students=tok.get("max_students"), grace_days=grace)
    out.update(group_id=tok.get("group_id"), server_label=tok.get("server_label"), servers=_others(tok),
               servers_booked=tok.get("servers_booked"), update=tok.get("update"))
    hard = st.get("hard_lock")
    if isinstance(hard, dict):                      # Sofortsperre des Anbieters: sofort, ohne Kulanz
        out.update(state="locked", stage="locked", reason="blocked",
                   message=str(hard.get("text") or "Die Lizenz wurde vom Anbieter gesperrt."))
        return out
    if status == "paused":                          # pausiert: Kulanz (nur lesen), danach gesperrt
        since = _parse_dt(tok.get("since")) or checked or now
        end = (since + timedelta(days=grace)).date()
        text = LOCK_TEXT["paused"]
        if today > end:
            out.update(state="locked", stage="locked", reason="paused", message=text)
        else:
            out.update(state="grace", stage="grace", reason="paused", grace_until=end.isoformat(),
                       message=f"{text} Bis zum {end:%d.%m.%Y} können Sie die Daten nur noch lesen.")
        return out
    if status not in OK_STATUS:
        reason = LOCK_REASON.get(status, "unknown")
        out.update(state="locked", stage="locked", reason=reason, message=LOCK_TEXT.get(reason, tok.get("message") or ""))
        return out
    # Jede Ursache liefert (Stufe, Grund, Meldung, Ende der Kulanz); die strengste gewinnt.
    cands: list[tuple[str, str, str, Optional[date]]] = []
    if valid_until is not None and today > valid_until:
        end = valid_until + timedelta(days=grace)
        if today > end:
            cands.append(("locked", "expired", f"Das Abo ist am {valid_until:%d.%m.%Y} abgelaufen.", None))
        else:
            cands.append(("grace", "expired", f"Das Abo ist am {valid_until:%d.%m.%Y} abgelaufen. Bis zum {end:%d.%m.%Y} "
                          "können Sie die Daten nur noch lesen; danach ist die Anwendung gesperrt.", end))
    if conf is not None:
        since = max((now - checked).days, 0) if checked else 0
        if now > conf:
            end = (conf + timedelta(days=grace)).date()
            text = f"Die Lizenz konnte seit {since} Tag(en) nicht bestätigt werden."
            if today > end:
                cands.append(("locked", "offline", text, None))
            else:
                cands.append(("grace", "offline", f"{text} Bis zum {end:%d.%m.%Y} können Sie die Daten nur noch lesen.", end))
        elif st.get("last_error"):
            left = max((conf - now).days, 0)
            out["warning"] = (f"Der Lizenzserver ist nicht erreichbar. Die letzte Bestätigung gilt noch {left} Tag(e).")
            out["offline_left"] = left
    if cands:
        state, reason, msg, end = max(cands, key=lambda c: _RANK[c[0]])
        out.update(state=state, stage=state, reason=reason, message=msg, grace_until=end.isoformat() if end else None)
        return out
    left = out["days_left"]
    if left is not None and 0 <= left <= WARN_DAYS[0]:
        out["stage"] = "warning"
        out["warn_level"] = min(d for d in WARN_DAYS if left <= d)
        out["warning"] = f"Das Abo läuft {'heute' if left == 0 else f'in {left} Tag(en)'} ab ({valid_until:%d.%m.%Y})."
    elif out["warning"]:
        out["stage"] = "warning"
    return out


def _mtime(p: Path) -> int:
    try:
        return p.stat().st_mtime_ns
    except OSError:
        return 0


def _evaluate_cached() -> dict:
    """``evaluate`` mit kurzer Zwischenspeicherung (jede API-Anfrage fragt die Sperre ab); ändert sich eine der
    beiden Dateien, der Tag oder der Prüfschlüssel, wird neu gerechnet."""
    key = (_mtime(license_path()), _mtime(state_path()), _now().date(), str(license_path()), _pubkey_text())
    hit = _cache.get("ev")
    t = time.monotonic()
    if hit and hit[0] == key and t - hit[1] < CACHE_TTL:
        return hit[2]
    ev = evaluate()
    _cache["ev"] = (key, t, ev)
    return ev


def reset_cache() -> None:
    _cache.clear()


def status(*, full: bool = False, now: Optional[datetime] = None) -> dict:
    """Aktueller Lizenzstand. ``read_only``: Kulanzzeit (nur lesen), ``locked``: gesperrt – beides nur mit
    ``SM_LICENSE_ENFORCE``."""
    ev = evaluate(now=now) if now is not None else _evaluate_cached()
    out: dict[str, Any] = {**ev, "enforced": config.license_enforce,
                           "read_only": bool(config.license_enforce and ev["state"] == "grace"),
                           "locked": bool(config.license_enforce and _locks(ev))}
    if full or ev.get("max_users") or ev.get("max_students"):
        counts = _counts()
        out["counts"] = counts
        if ev.get("max_students") and (counts.get("students") or 0) > int(ev["max_students"]):
            out["warning"] = out["warning"] or (
                f"Mehr Schüler/innen ({counts['students']}) als lizenziert ({ev['max_students']}).")
    if full:
        st = load_state()
        out.update({"instance_id": st.get("instance_id"), "last_attempt_at": st.get("last_attempt_at"),
                    "last_error": st.get("last_error"), "base_url": config.base_url})
    return out


def is_locked() -> bool:
    """Schnellabfrage für die Middleware: ist die Anwendung gesperrt?"""
    return bool(config.license_enforce and _locks(_evaluate_cached()))


def is_read_only() -> bool:
    """Kulanzzeit: Änderungen gesperrt, Lesen möglich."""
    return bool(config.license_enforce and _evaluate_cached()["state"] == "grace")


def lock_message() -> str:
    ev = _evaluate_cached()
    return ev.get("message") or ev.get("warning") or "Die Lizenz dieser Schule ist nicht gültig."


def user_limit() -> Optional[int]:
    """Höchstzahl aktiver Konten laut Lizenzserver (nur mit Durchsetzung), sonst ``None`` = unbegrenzt."""
    if not config.license_enforce:
        return None
    mx = _evaluate_cached().get("max_users")
    return int(mx) if mx else None


# --------------------------------------------------------------------------- Benachrichtigung
def notify_stage() -> list[str]:
    """Meldet Vorwarnung (30/14/7/1 Tage), Kulanzzeit und Sperre über die Glocke an Konten mit ``license.manage``
    (Administration, Schulleitung). Je Stufe und Schlüssel nur einmal (``dedupe``). Nur mit Durchsetzung."""
    if not config.license_enforce:
        return []
    ev = _evaluate_cached()
    ref = ev.get("key_last4")
    if not ref or ev.get("reason") in ("missing", "unconfirmed"):
        return []
    if ev["state"] == "locked":
        key, title = f"locked:{ev['reason']}", "Die Lizenz ist nicht mehr gültig – die Anwendung ist gesperrt"
    elif ev["state"] == "grace":
        key, title = f"grace:{ev['reason']}:{ev.get('grace_until')}", "Lizenz nicht bestätigt – Daten nur noch lesbar"
    elif ev.get("stage") == "warning" and ev.get("warn_level"):
        left = ev["days_left"]
        key = f"warn:{ev['warn_level']}"
        title = "Das Abo läuft heute ab" if left == 0 else f"Das Abo läuft in {left} Tag(en) ab"
    else:
        return []
    try:
        from . import notifications
        from .db import session_scope
        with session_scope() as db:
            users = notifications.users_with_permission(db, "license.manage")
        notifications.notify(users, "license", title, "/lizenz", body=ev.get("message") or ev.get("warning") or "",
                             dedupe=f"license:{ref}:{key}")
    except Exception:  # noqa: BLE001
        log.exception("Lizenz-Benachrichtigung fehlgeschlagen")
        return []
    return [key]


# --------------------------------------------------------------------------- Lizenzserver
def _post(url: str, body: dict, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "Schulpuls-Lizenz"})
    with net_guard.urlopen(req, "license", timeout=timeout) as r:     # Ziel fest eingebaut, trotzdem geprüft
        return json.loads(r.read().decode("utf-8"))


def _url_ok(url: str) -> bool:
    if url.startswith("https://"):
        return True
    # Entwicklung/Demo: ein lokaler Lizenzserver darf unverschlüsselt angesprochen werden (nie in Produktion)
    return config.mode != "production" and url.startswith(("http://127.0.0.1", "http://localhost"))


def _ask(path: str, key: str, st: dict, *, light: bool = False) -> dict:
    """``activate``/``check`` beim Lizenzserver; gibt das **signierte** Antwortobjekt zurück oder wirft ``ValueError``
    (nicht erreichbar, nicht signiert, passt nicht zur Anfrage – alles gleich behandelt)."""
    from .config import APP_VERSION

    base = _server_url()
    if not _url_ok(base):
        raise ValueError("Die Adresse des Lizenzservers ist nicht zulässig.")
    nonce = secrets.token_hex(16)
    counts = {} if light else _counts()          # ``ping``: kein Datenbankzugriff, winzige Anfrage
    body = {"key": key, "instance_id": st["instance_id"], "base_url": config.base_url[:300], "version": str(APP_VERSION)[:40],
            "students": counts.get("students"), "users": counts.get("users"), "nonce": nonce}
    try:
        resp = _post(f"{base}/api/v1/{path}", body)
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError(f"Der Lizenzserver ist nicht erreichbar ({str(exc)[:200]})") from exc
    result, sig = resp.get("result"), str(resp.get("signature") or "")
    if not isinstance(result, dict) or not verify(result, sig):
        raise ValueError("Die Antwort des Lizenzservers ist nicht korrekt signiert")
    if result.get("nonce") != nonce or result.get("instance_id") != st["instance_id"] or result.get("key_last4") not in (key[-4:], None):
        raise ValueError("Die Antwort des Lizenzservers passt nicht zur Anfrage")
    return {"result": result, "signature": sig}


def _apply_lock(st: dict, answer: dict, key: str) -> None:
    """Sperrbefehl des Anbieters prüfen und anwenden (``st`` wird geändert, der Aufrufer speichert).

    Nur ein Befehl mit gültigem MAC (Sperr-Schlüssel dieser Server-Lizenz, Nonce dieser Anfrage, Instanz-ID) zählt;
    ein fremder oder gefälschter Befehl wird ignoriert. ``lock`` setzt die Sofortsperre, ``unlock`` hebt sie auf."""
    import hashlib
    import hmac
    res = answer["result"]
    cmd, secret = res.get("lock"), str(st.get("lock_secret") or "")
    if not isinstance(cmd, dict) or not secret:
        return
    msg = canonical({"command": cmd.get("command"), "text": cmd.get("text"), "issued_at": cmd.get("issued_at"),
                     "nonce": res.get("nonce"), "instance_id": st.get("instance_id"), "key_last4": key[-4:]})
    expect = hmac.new(secret.encode("ascii"), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, str(cmd.get("mac") or "")):
        log.warning("Sperrbefehl mit ungültigem MAC ignoriert")
        return
    if cmd.get("command") == "lock":
        st["hard_lock"] = {"text": str(cmd.get("text") or "")[:300], "since": (st.get("hard_lock") or {}).get("since") or _now().isoformat()}
    elif cmd.get("command") == "unlock":
        st.pop("hard_lock", None)


ACTIVATE_ERRORS = {
    "unknown": "Der Lizenzschlüssel ist dem Anbieter nicht bekannt. Bitte prüfen Sie Ihre Eingabe.",
    "cancelled": "Diese Lizenz wurde gekündigt und kann nicht aktiviert werden.",
    "bound_elsewhere": "Dieser Schlüssel ist bereits an eine andere Installation gebunden. "
                       "Bei einem Serverumzug bitten Sie den Anbieter, die Bindung zu lösen.",
}


def install(text: str) -> dict:
    """Schlüssel eintragen: Prüfziffer, dann Aktivierung (Bindung) beim Lizenzserver; erst bei Erfolg gespeichert."""
    key = normalize_key(text)
    if not key:
        raise ValueError("Der Lizenzschlüssel ist nicht korrekt. Bitte prüfen Sie die Eingabe auf Tippfehler "
                         "(Aufbau: SPUL-XXXX-XXXX-XXXX-XXXX).")
    if _public_key() is None:
        raise ValueError("In dieser Installation ist kein Prüfschlüssel des Anbieters eingerichtet.")
    with _lock:
        st = load_state()
        answer = _ask("activate", key, st)
        res = answer["result"]
        if res.get("status") in ACTIVATE_ERRORS:
            raise ValueError(ACTIVATE_ERRORS[res["status"]])
        _write_json(license_path(), {"key": key, "activated_at": _now().isoformat()})
        if res.get("lock_secret"):
            st["lock_secret"] = res["lock_secret"]
        st.pop("hard_lock", None)
        _apply_lock(st, answer, key)
        st.update(token=answer, last_error="", last_attempt_at=_now().isoformat(), last_full_at=_now().isoformat())
        _write_json(state_path(), st)
    _cache.clear()
    notify_stage()
    return status(full=True)


def check_now(*, light: bool = False) -> dict:
    """Beim Lizenzserver nachfragen (``light``: kurze Statusabfrage ``ping``); speichert das signierte Ergebnis (Token)
    und gibt den neuen Stand zurück."""
    key = load_key()
    if not key:
        return status()
    with _lock:
        st = load_state()
        st["last_attempt_at"] = _now().isoformat()
        try:
            answer = _ask("ping" if light else "check", key, st, light=light)
            _apply_lock(st, answer, key)
            st["token"], st["last_error"] = answer, ""
            if not light:
                st["last_full_at"] = _now().isoformat()
            log.info("Lizenz ...%s %s: %s", key[-4:], "Ping" if light else "geprüft", answer["result"].get("status"))
        except ValueError as exc:
            st["last_error"] = str(exc)[:300]
            log.warning("Lizenzprüfung fehlgeschlagen: %s", exc)
        _write_json(state_path(), st)
    _cache.clear()
    return status()


def next_action(st: dict, now: datetime) -> Optional[str]:
    """Was ist jetzt fällig? ``"check"`` (ausführlich: beim Start, nach 24 h, nach Fehlern stündlich), ``"ping"`` (kurze
    Statusabfrage alle ``license_ping_minutes``) oder ``None``."""
    last = _parse_dt(st.get("last_attempt_at"))
    last_full = _parse_dt(st.get("last_full_at"))
    if last_full is None or now - last_full > timedelta(hours=config.license_check_hours):
        return "check"
    if st.get("last_error") and last is not None and now - last > timedelta(hours=CHECK_RETRY_HOURS):
        return "check"
    if config.license_ping_minutes > 0 and (last is None or now - last >= timedelta(minutes=config.license_ping_minutes)):
        return "ping"
    return None


def _loop() -> None:
    first = True
    while not _stop.is_set():
        if load_key():
            st = load_state()
            action = "check" if first else next_action(st, _now())
            if action:
                try:
                    check_now(light=action == "ping")
                except Exception:  # noqa: BLE001
                    log.exception("Lizenzprüfung abgebrochen")
        first = False
        try:
            notify_stage()
        except Exception:  # noqa: BLE001
            log.exception("Lizenz-Benachrichtigung abgebrochen")
        _stop.wait(max(60, config.license_ping_minutes * 60) if config.license_ping_minutes > 0 else 15 * 60)


def start() -> bool:
    """Hintergrund-Prüfung starten (``runtime.startup``): sofort beim Start und danach mindestens alle 24 Stunden."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return True
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="sm-license", daemon=True)
    _thread.start()
    return True


def stop() -> None:
    _stop.set()
    time.sleep(0)
