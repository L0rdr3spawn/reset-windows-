"""Benachrichtigungszentrale (Glocke) – zentrale Funktion :func:`notify` (``docs/BENACHRICHTIGUNGEN.md``).

Abgrenzung: ``notify.py`` (ohne „ung“) ist der Zusteller für Vertretungsplan-Webhooks/E-Mails; hier geht es um die
Benachrichtigungen **je Konto** in der Web-App. Chats und Postfach behalten ihren eigenen Zähler („Nachrichten“); die
Glocke ist für Systemereignisse – Nachrichten erscheinen dort nur, wenn die Person die Art ``message`` einschaltet.

Aufruf (aus jedem Feature, nach dem Commit der eigentlichen Änderung)::

    from schulmanager.server import notifications
    notifications.notify([user_id, ...], "course_item", "Neues Material im Kursraum", "/kursraeume/5",
                         body="Mathe 8a", student_id="S12", dedupe="item:41")

* ``user_ids`` – Empfänger-Konten; unbekannte/inaktive Konten und ``actor_id`` (wer die Aktion ausgelöst hat) werden
  übersprungen.
* ``kind`` – Ereignisart (:data:`KINDS`); unbekannte Arten gelten als „Sonstiges“ mit der Voreinstellung „in der App“.
  Neue Arten meldet ein Feature mit :func:`register_kind` an, dann erscheinen sie in den Einstellungen.
* ``title``/``body`` – **ohne sensible Einzelheiten** (keine Diagnosen, Noten, Gründe). Beides wird verschlüsselt
  gespeichert.
* ``link`` – relativer Pfad der Oberfläche (``/…``); Klick auf die Benachrichtigung führt dorthin.
* ``dedupe`` – optionaler Schlüssel; dieselbe Meldung wird je Konto nur einmal angelegt.
* Rückgabe: Liste der neu angelegten Benachrichtigungs-IDs (leer, wenn alle Empfänger die Art ausgeschaltet haben).

Wirkung je Empfänger richtet sich nach den Einstellungen (Schulvorgabe → eigene Wahl): ``aus`` | ``app`` | ``mail``
(zusätzlich E-Mail, nur wenn der Versand eingerichtet ist und das Konto eine Adresse hat). Optional tägliche
Zusammenfassung und Ruhezeiten (verschieben nur E-Mails). Live: SSE-Ereignis ``change`` mit Bereich ``notifications``.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Iterable, Optional

from sqlalchemy import delete, event, func, select, update
from sqlalchemy.orm import Session

from ..branding import PRODUCT_NAME
from .db import session_scope, utcnow
from .db_models import ParentLink, User
from .feature_models.notifications import (Notification, NotificationConfig, NotificationPref, NotificationSchool,
                                           NotificationUserSettings)

log = logging.getLogger("schulmanager.notifications")

MODES = ("aus", "app", "mail")
MODE_LABELS = {"aus": "Aus", "app": "In der App", "mail": "In der App und per E-Mail"}
DEFAULT_RETENTION_DAYS = 90
MIN_RETENTION_DAYS = 7
MAX_RETENTION_DAYS = 730
DIGEST_HOUR = 7                 # frühestens ab dieser Ortszeit geht die tägliche Zusammenfassung raus
MAX_TITLE = 200
MAX_BODY = 400
LIST_LIMIT = 100
SCOPE = "notifications"


# =========================================================================== Katalog der Ereignisarten
KINDS: dict[str, dict[str, Any]] = {}


def register_kind(kind: str, label: str, group: str = "Sonstiges", default: str = "app", help: str = "",
                  needs: tuple[str, ...] = ()) -> None:
    """Meldet eine Ereignisart an (idempotent). ``default``: Voreinstellung ohne Schulvorgabe und ohne eigene Wahl;
    ``needs``: nur Konten mit mindestens einem dieser Rechte sehen die Art in ihren Einstellungen."""
    if default not in MODES:
        raise ValueError(f"Unbekannter Modus {default!r}")
    KINDS[kind] = {"kind": kind, "label": label, "group": group, "default": default, "help": help,
                   "needs": list(needs)}


# Vorhandene Ereignisquellen
register_kind("substitution", "Vertretung oder Entfall meiner Stunden", "Stundenplan", "app",
              "Gilt für Lehrkräfte (eigene Stunden), Schüler/innen (Unterricht der Klasse bzw. des Kurses) und Eltern "
              "(je Kind).")
register_kind("duty", "Pausenaufsicht geändert", "Stundenplan", "app")
register_kind("exam", "Klausur angesetzt oder verschoben", "Stundenplan", "app")
register_kind("absence", "Krankmeldung eingegangen oder bestätigt", "Fehlzeiten", "app")
register_kind("attest_missing", "Attest fehlt", "Fehlzeiten", "app")
register_kind("request_decided", "Antrag genehmigt oder abgelehnt", "Anträge", "app",
              "Formulare und Ausnahmen von Lehrkräften.")
register_kind("course_item", "Neue Aufgabe oder neues Material im Kursraum", "Kursräume", "app")
register_kind("task_graded", "Abgabe bewertet", "Kursräume", "app")
register_kind("task_due", "Aufgabe ist morgen fällig", "Kursräume", "app")
register_kind("plan_proposal", "Plan-Prüfung: neuer Vorschlag", "Planung", "app",
              "Für Planende, wenn die Dauerprüfung einen Vorschlag zur Entscheidung bereithält.",
              needs=("timetable.generate", "timetable.edit", "settings.edit"))
register_kind("message", "Neue Nachricht (Postfach, Chats)", "Nachrichten", "aus",
              "Nachrichten haben ihren eigenen Zähler. Hier nur einschalten, wenn die Glocke sie ebenfalls melden soll.")
# Platzhalter für weitere Funktionen (Aufgaben, Gruppen, Fortschritt, Abstimmungen, Notenbuch, Kompetenzen):
# Features rufen ``notify`` auf und können mit ``register_kind`` eine genauere Beschriftung setzen.
register_kind("assignment", "Aufgaben: Frist, Verlängerung, Wiederabgabe", "Kursräume", "app")
register_kind("group", "Kursgruppen", "Kursräume", "app")
register_kind("progress", "Lernfortschritt und Freigaben", "Kursräume", "app")
register_kind("poll", "Abstimmung oder Umfrage", "Kursräume", "app")
register_kind("selftest", "Selbsttest", "Kursräume", "app")
register_kind("gradebook", "Notenbuch", "Noten", "app")
register_kind("competence", "Kompetenzen und Lernstand", "Noten", "app")
register_kind("license", "Lizenz läuft ab, ist abgelaufen oder gesperrt", "Betrieb", "app",
              "Vorwarnung 30, 14, 7 und 1 Tag vor Ablauf, Beginn der Kulanzzeit und Sperre.", needs=("license.manage",))
register_kind("other", "Sonstiges", "Sonstiges", "app")


def kind_label(kind: str) -> str:
    return (KINDS.get(kind) or KINDS["other"])["label"]


def kind_default(kind: str) -> str:
    return (KINDS.get(kind) or KINDS["other"])["default"]


# =========================================================================== Einstellungen
def _retention_value(db: Session) -> int:
    raw = db.scalar(select(NotificationConfig.value).where(NotificationConfig.key == "retention_days"))
    try:
        days = int(raw) if raw is not None else DEFAULT_RETENTION_DAYS
    except ValueError:
        days = DEFAULT_RETENTION_DAYS
    return min(MAX_RETENTION_DAYS, max(MIN_RETENTION_DAYS, days))


def retention_days(db: Optional[Session] = None) -> int:
    if db is not None:
        return _retention_value(db)
    with session_scope() as own:
        return _retention_value(own)


def school_rules(db: Session) -> dict[str, dict[str, Any]]:
    """``{art: {"mode", "locked"}}`` – Schulvorgabe (ohne Eintrag: Voreinstellung der Art, nicht gesperrt)."""
    rows = {r.kind: r for r in db.scalars(select(NotificationSchool))}
    out = {}
    for kind in KINDS:
        r = rows.get(kind)
        out[kind] = {"mode": r.mode if r else kind_default(kind), "locked": bool(r.locked) if r else False}
    return out


def _chunks(values: list, size: int = 400):
    for i in range(0, len(values), size):
        yield values[i:i + size]


def modes_for(db: Session, user_ids: Iterable[int], kind: str) -> dict[int, str]:
    """Wirksamer Modus je Konto: gesperrte Schulvorgabe → eigene Wahl → Schulvorgabe → Voreinstellung der Art."""
    ids = sorted(set(user_ids))
    row = db.get(NotificationSchool, kind)
    base = row.mode if row else kind_default(kind)
    if row is not None and row.locked:
        return dict.fromkeys(ids, row.mode)
    out = dict.fromkeys(ids, base)
    for chunk in _chunks(ids):
        for uid, mode in db.execute(select(NotificationPref.user_id, NotificationPref.mode)
                                    .where(NotificationPref.kind == kind, NotificationPref.user_id.in_(chunk))):
            if mode in MODES:
                out[uid] = mode
    return out


def user_prefs(db: Session, user_id: int, permissions: Optional[Iterable[str]] = None) -> dict[str, Any]:
    """Einstellungen eines Kontos für die Oberfläche (wirksamer Modus je Art, Sperren, Zusammenfassung, Ruhezeiten).
    Mit ``permissions`` entfallen Arten, die ein Recht voraussetzen (``needs``), das das Konto nicht hat."""
    perms = set(permissions) if permissions is not None else None
    rules = school_rules(db)
    own = {r.kind: r.mode for r in db.scalars(select(NotificationPref).where(NotificationPref.user_id == user_id))}
    st = db.get(NotificationUserSettings, user_id)
    kinds = []
    for kind, meta in KINDS.items():
        if perms is not None and meta.get("needs") and not perms.intersection(meta["needs"]):
            continue
        rule = rules[kind]
        mode = rule["mode"] if rule["locked"] else own.get(kind, rule["mode"])
        kinds.append({**meta, "mode": mode if mode in MODES else rule["mode"], "school_mode": rule["mode"],
                      "locked": rule["locked"], "own": kind in own and not rule["locked"]})
    return {
        "kinds": kinds,
        "modes": [{"value": m, "label": MODE_LABELS[m]} for m in MODES],
        "digest": bool(st.digest) if st else False,
        "quiet_enabled": bool(st.quiet_enabled) if st else False,
        "quiet_from": st.quiet_from if st else "21:00",
        "quiet_to": st.quiet_to if st else "07:00",
        "mail_available": mail_available(),
        "retention_days": _retention_value(db),
    }


def _valid_hhmm(value: str) -> bool:
    try:
        h, m = (int(x) for x in str(value).split(":"))
    except (TypeError, ValueError):
        return False
    return len(str(value)) == 5 and 0 <= h <= 23 and 0 <= m <= 59


def save_user_prefs(db: Session, user_id: int, *, modes: Optional[dict[str, str]] = None,
                    digest: Optional[bool] = None, quiet_enabled: Optional[bool] = None,
                    quiet_from: Optional[str] = None, quiet_to: Optional[str] = None) -> list[str]:
    """Speichert die eigenen Einstellungen (ohne Commit). Gesperrte Arten werden abgelehnt (``ValueError``).
    Rückgabe: geänderte Felder (für das Audit, ohne Inhalte)."""
    changed: list[str] = []
    rules = school_rules(db)
    for kind, mode in (modes or {}).items():
        if kind not in KINDS:
            raise ValueError(f"Unbekannte Ereignisart: {kind}")
        if mode not in MODES:
            raise ValueError(f"Unbekannter Modus: {mode}")
        if rules[kind]["locked"]:
            raise ValueError(f"„{kind_label(kind)}“ ist von der Schule vorgegeben")
        row = db.scalar(select(NotificationPref).where(NotificationPref.user_id == user_id,
                                                       NotificationPref.kind == kind))
        if row is None:
            if mode == rules[kind]["mode"]:
                continue
            db.add(NotificationPref(user_id=user_id, kind=kind, mode=mode))
            changed.append(f"art:{kind}")
        elif row.mode != mode:
            row.mode = mode
            changed.append(f"art:{kind}")
    st = db.get(NotificationUserSettings, user_id)
    if st is None:
        st = NotificationUserSettings(user_id=user_id, digest=False, quiet_enabled=False, quiet_from="21:00",
                                      quiet_to="07:00", updated_at=utcnow())
        db.add(st)
    for field, value in (("digest", digest), ("quiet_enabled", quiet_enabled)):
        if value is not None and bool(getattr(st, field)) != bool(value):
            setattr(st, field, bool(value))
            changed.append(field)
    for field, value in (("quiet_from", quiet_from), ("quiet_to", quiet_to)):
        if value is None:
            continue
        if not _valid_hhmm(value):
            raise ValueError("Uhrzeit bitte als HH:MM angeben")
        if getattr(st, field) != value:
            setattr(st, field, value)
            changed.append(field)
    if changed:
        st.updated_at = utcnow()
    return changed


def save_school_rules(db: Session, rules: dict[str, dict[str, Any]], retention: Optional[int] = None) -> list[str]:
    """Schulvorgaben (ohne Commit): ``{art: {"mode", "locked"}}`` und Aufbewahrung in Tagen."""
    changed: list[str] = []
    for kind, rule in rules.items():
        if kind not in KINDS:
            raise ValueError(f"Unbekannte Ereignisart: {kind}")
        mode = rule.get("mode", kind_default(kind))
        if mode not in MODES:
            raise ValueError(f"Unbekannter Modus: {mode}")
        locked = bool(rule.get("locked", False))
        row = db.get(NotificationSchool, kind)
        if row is None:
            if mode == kind_default(kind) and not locked:
                continue
            db.add(NotificationSchool(kind=kind, mode=mode, locked=locked, updated_at=utcnow()))
            changed.append(kind)
        elif row.mode != mode or bool(row.locked) != locked:
            row.mode, row.locked, row.updated_at = mode, locked, utcnow()
            changed.append(kind)
    if retention is not None:
        days = int(retention)
        if not MIN_RETENTION_DAYS <= days <= MAX_RETENTION_DAYS:
            raise ValueError(f"Aufbewahrung: {MIN_RETENTION_DAYS} bis {MAX_RETENTION_DAYS} Tage")
        cfg = db.get(NotificationConfig, "retention_days")
        if cfg is None:
            db.add(NotificationConfig(key="retention_days", value=str(days)))
            changed.append("retention_days")
        elif cfg.value != str(days):
            cfg.value = str(days)
            changed.append("retention_days")
    return changed


# =========================================================================== Empfänger-Hilfen
def users_of_teachers(db: Session, teacher_ids: Iterable[str]) -> list[int]:
    ids = sorted({t for t in teacher_ids if t})
    out: list[int] = []
    for chunk in _chunks(ids):
        out += db.scalars(select(User.id).where(User.active.is_(True), User.teacher_id.in_(chunk)))
    return out


def users_of_students(db: Session, student_ids: Iterable[str]) -> list[int]:
    ids = sorted({s for s in student_ids if s})
    out: list[int] = []
    for chunk in _chunks(ids):
        out += db.scalars(select(User.id).where(User.active.is_(True), User.role == "schueler",
                                                User.student_id.in_(chunk)))
    return out


def parents_by_student(db: Session, student_ids: Iterable[str], area: Optional[str] = None,
                       school: Any = None) -> dict[str, list[int]]:
    """Eltern-Konten je Kind. Mit ``area``: nur, wenn die Eltern den Bereich sehen dürfen (volljährige Kinder
    entscheiden über ``parent_access``)."""
    from . import parent_access
    ids = sorted({s for s in student_ids if s})
    out: dict[str, list[int]] = {}
    for chunk in _chunks(ids):
        rows = db.execute(select(ParentLink.student_id, ParentLink.parent_user_id)
                          .join(User, User.id == ParentLink.parent_user_id)
                          .where(ParentLink.student_id.in_(chunk), User.active.is_(True))).all()
        for sid, uid in rows:
            out.setdefault(sid, []).append(uid)
    if area:
        for sid in list(out):
            if not parent_access.parent_may_see(db, sid, area, school=school):
                del out[sid]
    return out


def family_of(db: Session, student_id: str, area: Optional[str] = None, *, include_student: bool = True,
              school: Any = None) -> list[int]:
    """Konten rund um ein Kind: das Schülerkonto und die Eltern (letztere nur, wo ``area`` es erlaubt)."""
    out = users_of_students(db, [student_id]) if include_student else []
    out += parents_by_student(db, [student_id], area, school).get(student_id, [])
    return list(dict.fromkeys(out))


def users_with_permission(db: Session, *perms: str) -> list[int]:
    """Aktive Konten, deren Rolle (Standardrechte) mindestens eines der Rechte hat."""
    from .permissions import ROLE_PERMISSIONS
    roles = [r for r, p in ROLE_PERMISSIONS.items() if any(x in p for x in perms)]
    return list(db.scalars(select(User.id).where(User.active.is_(True), User.role.in_(roles)))) if roles else []


# =========================================================================== Anlegen
def _clean_link(link: str) -> str:
    link = (link or "").strip()
    if not link.startswith("/") or link.startswith("//") or len(link) > 300 or "\n" in link:
        return ""
    return link


def dedupe_key(*parts: Any) -> str:
    """Kurzer Schlüssel aus beliebigen Teilen (für ``dedupe``)."""
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:40]


def mail_available() -> bool:
    try:
        from .auth_messages import email_available
        return bool(email_available())
    except Exception:  # noqa: BLE001
        return False


def _publish(user_ids: Iterable[int]) -> None:
    ids = set(user_ids)
    if not ids:
        return
    try:
        from .events import bus
        bus.publish("change", {"version": None, "scope": [SCOPE], "dates": []}, user_ids=ids)
    except Exception:  # noqa: BLE001 - Live-Hinweise dürfen nie stören
        log.debug("Live-Hinweis fehlgeschlagen", exc_info=True)


def _in_quiet(st: Optional[NotificationUserSettings], now_local: datetime) -> bool:
    if st is None or not st.quiet_enabled or not _valid_hhmm(st.quiet_from) or not _valid_hhmm(st.quiet_to):
        return False
    cur = now_local.strftime("%H:%M")
    a, b = st.quiet_from, st.quiet_to
    if a == b:
        return False
    return (a <= cur < b) if a < b else (cur >= a or cur < b)


def _local_now(now: Optional[datetime] = None) -> datetime:
    from schulmanager.channels import utc_to_local
    return utc_to_local(now or utcnow())


def _mail_text(db: Session, rows: list[Notification]) -> str:
    from .config import config
    lines = ["Guten Tag,", "", f"im {PRODUCT_NAME} gibt es Neues für Sie:", ""]
    for n in rows:
        lines.append(f"• {n.read_text('title')}")
        body = n.read_text("body")
        if body:
            lines.append(f"  {body}")
        if n.link:
            lines.append(f"  {config.base_url}{n.link}")
    lines += ["", "Einzelheiten sehen Sie nach der Anmeldung. Welche Hinweise Sie per E-Mail bekommen, stellen Sie im "
              f"{PRODUCT_NAME} unter „Benachrichtigungen“ ein ({config.base_url}/benachrichtigungen)."]
    return "\n".join(lines)


def _send_mail(db: Session, user: User, rows: list[Notification], subject: str) -> bool:
    from .auth_messages import queue_email, valid_email
    if not user.email or not valid_email(user.email):
        return False
    try:
        return queue_email(db, user.email, subject, _mail_text(db, rows), purpose="notification") is not None
    except ValueError:
        return False


def notify(user_ids: Iterable[int], kind: str, title: str, link: str = "", *, body: str = "",
           student_id: Optional[str] = None, ref: Optional[str] = None, dedupe: Optional[str] = None,
           actor_id: Optional[int] = None, db: Optional[Session] = None) -> list[int]:
    """Legt für jedes Empfänger-Konto eine Benachrichtigung an (siehe Modulbeschreibung). Wirft nie: Fehler werden
    geloggt und ergeben eine leere Liste – eine Benachrichtigung darf die eigentliche Aktion nie verhindern.

    Ohne ``db`` läuft alles in einer eigenen Transaktion; mit ``db`` wird die Zeile nur hinzugefügt (Commit und
    Live-Hinweis nach dem Commit des Aufrufers)."""
    try:
        if db is None:
            with session_scope() as own:
                created, notified = _notify(own, user_ids, kind, title, link, body, student_id, ref, dedupe,
                                            actor_id)
            _publish(notified)
            return created
        created, notified = _notify(db, user_ids, kind, title, link, body, student_id, ref, dedupe, actor_id)
        if notified:
            ids = frozenset(notified)

            def after_commit(_session) -> None:
                _publish(ids)

            event.listen(db, "after_commit", after_commit, once=True)
        return created
    except Exception:  # noqa: BLE001
        log.exception("Benachrichtigung %s konnte nicht angelegt werden", kind)
        return []


def _notify(db: Session, user_ids: Iterable[int], kind: str, title: str, link: str, body: str,
            student_id: Optional[str], ref: Optional[str], dedupe: Optional[str],
            actor_id: Optional[int]) -> tuple[list[int], set[int]]:
    title = (title or "").strip()[:MAX_TITLE]
    if not title:
        raise ValueError("Titel fehlt")
    ids = {int(u) for u in user_ids if u} - ({actor_id} if actor_id else set())
    if not ids:
        return [], set()
    active = {u.id: u for chunk in _chunks(sorted(ids)) for u in db.scalars(
        select(User).where(User.id.in_(chunk), User.active.is_(True)))}
    modes = modes_for(db, active, kind)
    link = _clean_link(link)
    body = (body or "").strip()[:MAX_BODY]
    key = (dedupe or "")[:64] or None
    now = utcnow()
    local = _local_now(now)
    mails = mail_available()
    created: list[int] = []
    notified: set[int] = set()
    for uid in sorted(active):
        mode = modes.get(uid, "app")
        if mode == "aus":
            continue
        if key and db.scalar(select(Notification.id).where(Notification.user_id == uid,
                                                           Notification.dedupe_key == key).limit(1)) is not None:
            continue
        n = Notification(user_id=uid, kind=kind[:40], link=link, student_id=student_id, ref=(ref or None) and ref[:80],
                         dedupe_key=key, created_at=now, mail_state="")
        db.add(n)
        db.flush()
        n.write_text("title", title)
        n.write_text("body", body)
        if mode == "mail" and mails and active[uid].email:
            st = db.get(NotificationUserSettings, uid)
            if st is not None and st.digest:
                n.mail_state = "digest"
            elif _in_quiet(st, local):
                n.mail_state = "later"
            elif _send_mail(db, active[uid], [n], f"{PRODUCT_NAME}: {title}"):
                n.mail_state = "sent"
        created.append(n.id)
        notified.add(uid)
    return created, notified


# =========================================================================== Lesen und Bearbeiten (je Konto)
def notification_dict(n: Notification, *, with_child: Optional[dict[str, str]] = None) -> dict[str, Any]:
    from .db import iso
    out = {"id": n.id, "kind": n.kind, "kind_label": kind_label(n.kind), "title": n.read_text("title"),
           "body": n.read_text("body"), "link": n.link, "read": n.read_at is not None,
           "created_at": iso(n.created_at), "student_id": n.student_id}
    if with_child is not None:
        out["child"] = with_child.get(n.student_id or "", "") if n.student_id else ""
    return out


def unread_count(db: Session, user_id: int) -> int:
    return int(db.scalar(select(func.count()).select_from(Notification)
                         .where(Notification.user_id == user_id, Notification.read_at.is_(None))) or 0)


def list_for(db: Session, user_id: int, *, unread_only: bool = False, limit: int = 50, before: Optional[int] = None,
             children: Optional[dict[str, str]] = None) -> list[dict[str, Any]]:
    """Eigene Benachrichtigungen, neueste zuerst (``before`` = ID für das Nachladen)."""
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    if before:
        stmt = stmt.where(Notification.id < before)
    rows = db.scalars(stmt.order_by(Notification.id.desc()).limit(max(1, min(limit, LIST_LIMIT))))
    return [notification_dict(n, with_child=children) for n in rows]


def mark_read(db: Session, user_id: int, ids: Optional[Iterable[int]] = None, read: bool = True) -> int:
    """Markiert eigene Benachrichtigungen (``ids=None``: alle) als gelesen bzw. ungelesen; fremde IDs bleiben
    unberührt. Rückgabe: Anzahl geänderter Zeilen."""
    stmt = update(Notification).where(Notification.user_id == user_id)
    if ids is not None:
        stmt = stmt.where(Notification.id.in_([int(i) for i in ids] or [-1]))
    if read:
        stmt = stmt.where(Notification.read_at.is_(None)).values(read_at=utcnow())
    else:
        stmt = stmt.where(Notification.read_at.is_not(None)).values(read_at=None)
    return db.execute(stmt).rowcount or 0


def delete_own(db: Session, user_id: int, ids: Optional[Iterable[int]] = None, only_read: bool = False) -> int:
    stmt = delete(Notification).where(Notification.user_id == user_id)
    if ids is not None:
        stmt = stmt.where(Notification.id.in_([int(i) for i in ids] or [-1]))
    if only_read:
        stmt = stmt.where(Notification.read_at.is_not(None))
    return db.execute(stmt).rowcount or 0


# =========================================================================== Regelmäßige Arbeit
def cleanup(db: Session, now: Optional[datetime] = None) -> int:
    """Löscht Benachrichtigungen, die älter als die eingestellte Aufbewahrung sind."""
    db.flush()
    cutoff = (now or utcnow()) - timedelta(days=_retention_value(db))
    return db.execute(delete(Notification).where(Notification.created_at < cutoff)).rowcount or 0


def release_mails(db: Session, now: Optional[datetime] = None) -> dict[str, int]:
    """Versendet zurückgestellte E-Mails (Ruhezeit vorbei) und die tägliche Zusammenfassung."""
    now = now or utcnow()
    local = _local_now(now)
    stats = {"later": 0, "digest": 0}
    if not mail_available():
        return stats
    pending = list(db.scalars(select(Notification).where(Notification.mail_state.in_(("later", "digest")))
                              .order_by(Notification.id)))
    by_user: dict[int, list[Notification]] = {}
    for n in pending:
        by_user.setdefault(n.user_id, []).append(n)
    for uid, rows in by_user.items():
        user = db.get(User, uid)
        st = db.get(NotificationUserSettings, uid)
        if user is None or not user.active or not user.email:
            for n in rows:
                n.mail_state = ""
            continue
        later = [n for n in rows if n.mail_state == "later"]
        if later and not _in_quiet(st, local):
            subject = f"{PRODUCT_NAME}: {later[0].read_text('title')}" if len(later) == 1 else \
                f"{PRODUCT_NAME}: {len(later)} neue Benachrichtigungen"
            ok = _send_mail(db, user, later, subject)
            for n in later:
                n.mail_state = "sent" if ok else ""
            stats["later"] += len(later)
        digest = [n for n in rows if n.mail_state == "digest"]
        today = local.date().isoformat()
        if digest and local.hour >= DIGEST_HOUR and (st is None or st.digest_sent_on != today):
            # nur ungelesene fassen zusammen; was die Person schon gesehen hat, braucht keine Mail
            fresh = [n for n in digest if n.read_at is None]
            if fresh:
                _send_mail(db, user, fresh, f"{PRODUCT_NAME}: Zusammenfassung vom {local.strftime('%d.%m.%Y')}")
            for n in digest:
                n.mail_state = "digested"
            if st is not None:
                st.digest_sent_on = today
            stats["digest"] += len(fresh)
    return stats


def run_periodic(now: Optional[datetime] = None) -> dict[str, int]:
    """Wartungslauf (stündlich aus ``maintenance.run_maintenance``): Fristerinnerungen, Attest-Erinnerungen,
    zurückgestellte E-Mails/Zusammenfassung, Aufräumen."""
    out: dict[str, int] = {}
    try:
        from . import notification_hooks
        out.update(notification_hooks.reminders(now))
    except Exception:  # noqa: BLE001
        log.exception("Erinnerungen fehlgeschlagen")
    try:
        with session_scope() as db:
            out.update({f"mail_{k}": v for k, v in release_mails(db, now).items()})
            out["deleted"] = cleanup(db, now)
    except Exception:  # noqa: BLE001
        log.exception("Aufräumen der Benachrichtigungen fehlgeschlagen")
    return out
