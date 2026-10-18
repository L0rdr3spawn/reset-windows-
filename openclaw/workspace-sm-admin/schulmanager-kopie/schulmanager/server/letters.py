"""Zugangsbriefe als PDF (§11.3): kurzlebige, verschlüsselte Stapel mit Startpasswörtern, Briefe, ZIP, E-Mail-Text.

Ablauf: Konten anlegen bzw. neue Startpasswörter setzen → :func:`create_batch` legt einen Stapel an (Einträge inkl.
Startpasswort **nur verschlüsselt**, ``crypto.encrypt_text`` mit AAD ``letter_batches:<id>``) → Download als
Sammel-PDF (eine Seite je Brief), ZIP mit Einzel-PDFs oder Versand per E-Mail. Nach ``SM_LETTER_BATCH_MINUTES``
(Standard 60) ist der Stapel weg (Wartung bzw. nächster Zugriff).

Eintrag (JSON im Stapel)::

    {"user_id", "username", "display_name", "role", "first_name", "last_name", "class_id", "class_name",
     "student_id", "adult", "password", "children": [{"student_id", "name", "class_id"}]}

Briefvarianten: Schüler/innen (Sie-Form), Eltern („Zugangsdaten für die Eltern von …“,
Sie-Form), Personal (Sie-Form). Hinweise aus ``login_policy.effective_policy`` (lazy importiert): ohne erlaubte
Passwort-Anmeldung wird das Passwort nicht gedruckt („Melden Sie sich mit Ihrem Microsoft-Konto an“) – außer es sind
Verknüpfungen Pflicht (Ersteinrichtung braucht das Startpasswort einmal); Pflicht-Verknüpfungen → „Verbinde nach dem
ersten Anmelden Ihr …-Konto“.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import unicodedata
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import pdf
from ..branding import PRODUCT_NAME, draw_logo
from .config import config
from .db import iso, utcnow
from .db_models import ParentLink, User
from .feature_models.letters import AccountInitialPassword, LetterBatch

log = logging.getLogger("schulmanager.letters")

DEFAULT_BATCH_MINUTES = 60
MAX_BATCH_ENTRIES = 5000
ROLE_LABELS = {"admin": "Administration", "schulleitung": "Schulleitung", "planer": "Stundenplanung",
               "sekretariat": "Sekretariat", "lehrer": "Lehrkraft", "schueler": "Schüler/in", "eltern": "Eltern",
               "monitor": "Monitor"}
ROLE_ORDER = {"schueler": 0, "eltern": 1}
NAME_PARTICLES = {"von", "vom", "van", "de", "der", "den", "del", "della", "di", "da", "du", "dos", "das", "zu",
                  "zur", "zum", "ten", "ter", "la", "le", "el", "al", "bin", "ben", "ibn", "y", "op"}
_MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
           "November", "Dezember"]
_GENERATED_PW = re.compile(r"^[a-z2-9]{3,6}(-[a-z2-9]{3,6})+$")


# =================================================================== Konfiguration & Hilfen
def batch_minutes() -> int:
    """Lebensdauer eines Stapels in Minuten (``SM_LETTER_BATCH_MINUTES``, 1…1440, Standard 60)."""
    try:
        value = int(os.environ.get("SM_LETTER_BATCH_MINUTES", "") or DEFAULT_BATCH_MINUTES)
    except ValueError:
        value = DEFAULT_BATCH_MINUTES
    return max(1, min(1440, value))


def login_url() -> str:
    return f"{config.base_url.rstrip('/')}/login"


def school_name() -> str:
    try:
        from .store import get_store

        return (get_store().school.settings.school_name or "").strip() or PRODUCT_NAME
    except Exception:  # noqa: BLE001 - Brief soll auch ohne Planungsdokument entstehen
        return PRODUCT_NAME


def split_name(name: str) -> tuple[str, str]:
    """„Vorname Nachname“ bzw. „Nachname, Vorname“ → (Vorname, Nachname); Namenszusätze (von, van, de …) gehören
    zum Nachnamen („Max von der Heide“ → („Max“, „von der Heide“))."""
    name = " ".join((name or "").split())
    if "," in name:
        last, first = (p.strip() for p in name.split(",", 1))
        return first, last
    parts = name.split(" ")
    if len(parts) < 2:
        return "", name
    i = len(parts) - 1
    while i > 1 and parts[i - 1].lower() in NAME_PARTICLES:
        i -= 1
    return " ".join(parts[:i]), " ".join(parts[i:])


# Buchstaben ohne Unicode-Zerlegung (ı ł ø …) vor der ASCII-Umschrift ersetzen
_TRANSLIT = {"ı": "i", "İ": "I", "ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D", "ð": "d", "Ð": "D",
             "æ": "ae", "Æ": "Ae", "œ": "oe", "Œ": "Oe", "þ": "th", "Þ": "Th"}
_UMLAUT_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss",
                             **_TRANSLIT})
_TRANSLIT_MAP = str.maketrans(_TRANSLIT)


def ascii_part(text: str) -> str:
    """Teil eines Dateinamens: Umlaute umschreiben, Akzente entfernen, nur ``A-Za-z0-9-`` (Leerzeichen → ``-``)."""
    out = unicodedata.normalize("NFKD", (text or "").translate(_UMLAUT_MAP)).encode("ascii", "ignore").decode()
    out = re.sub(r"[^A-Za-z0-9-]+", "-", out.strip())
    return re.sub(r"-{2,}", "-", out).strip("-")


def entry_filename(entry: dict, used: set[str] | None = None) -> str:
    """ASCII-Dateiname wie ``5a_Mustermann_Max.pdf`` (Eltern: ``…_Eltern.pdf``), eindeutig innerhalb ``used``."""
    first, last = entry.get("first_name") or "", entry.get("last_name") or ""
    role = entry.get("role")
    if role == "eltern" and entry.get("children"):
        child = entry["children"][0]
        first, last = split_name(child.get("name") or "")
        prefix = child.get("class_id") or "Eltern"
    else:
        if not (first or last):
            first, last = split_name(entry.get("display_name") or "")
        prefix = entry.get("class_id") or ("Schueler" if role == "schueler" else ROLE_LABELS.get(role or "", "Konto"))
    parts = [ascii_part(p) for p in (prefix, last, first)]
    if role == "eltern":
        parts.append("Eltern")
    base = "_".join(p for p in parts if p) or ascii_part(entry.get("username") or "") or "Zugangsdaten"
    base = base[:100]
    name, n = f"{base}.pdf", 1
    if used is not None:
        while name.lower() in used:
            n += 1
            name = f"{base}_{n}.pdf"
        used.add(name.lower())
    return name


def _natural(value: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", value or ""))


def _sort_key(entry: dict) -> tuple:
    """Klasse → Nachname → Vorname des (Kindes) → Schüler/in vor Eltern → Personal zuletzt."""
    if entry.get("role") == "eltern" and entry.get("children"):
        child = entry["children"][0]
        first, last = split_name(child.get("name") or "")
        cls = child.get("class_id") or ""
    else:
        first, last = entry.get("first_name") or "", entry.get("last_name") or ""
        if not (first or last):
            first, last = split_name(entry.get("display_name") or "")
        cls = entry.get("class_id") or ""
    staff = entry.get("role") not in ROLE_ORDER
    return (staff, _natural(cls), last.lower(), first.lower(), ROLE_ORDER.get(entry.get("role") or "", 2),
            entry.get("username") or "")


# =================================================================== Einträge
def entry_for_user(user: User, password: str, *, school=None, children: list[str] | None = None,
                   first_name: str = "", last_name: str = "") -> dict[str, Any]:
    """Stapel-Eintrag für ein Konto (``children`` = Schüler-IDs eines Elternkontos)."""
    if school is None:
        from .store import get_store

        school = get_store().school
    students = school.index("students")
    classes = school.index("classes")

    def cls_name(cid: str | None) -> str | None:
        c = classes.get(cid) if cid else None
        return (c.name or c.id) if c else cid

    entry: dict[str, Any] = {"user_id": user.id, "username": user.username, "display_name": user.display_name,
                             "role": user.role, "first_name": first_name, "last_name": last_name, "class_id": None,
                             "class_name": None, "student_id": user.student_id, "adult": bool(user.adult),
                             "password": password, "children": []}
    if user.role == "schueler" and user.student_id and user.student_id in students:
        st = students[user.student_id]
        entry["class_id"], entry["class_name"] = st.class_id, cls_name(st.class_id)
        if not (first_name or last_name):
            entry["first_name"], entry["last_name"] = split_name(st.name)
    if user.role == "eltern":
        for sid in children or []:
            st = students.get(sid)
            entry["children"].append({"student_id": sid, "name": st.name if st else sid,
                                      "class_id": st.class_id if st else None})
    if not (entry["first_name"] or entry["last_name"]) and user.role != "eltern":
        entry["first_name"], entry["last_name"] = split_name(user.display_name or "")
    return entry


def entries_for_passwords(db: Session, passwords: dict[int, str], *, school=None) -> list[dict]:
    """Einträge für ``{user_id: startpasswort}`` (Konten werden in einem Rutsch geladen)."""
    if not passwords:
        return []
    ids = list(passwords)
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(ids)))}
    links: dict[int, list[str]] = {}
    for pid, sid in db.execute(select(ParentLink.parent_user_id, ParentLink.student_id)
                               .where(ParentLink.parent_user_id.in_(ids)).order_by(ParentLink.id)):
        links.setdefault(pid, []).append(sid)
    return [entry_for_user(users[uid], pw, school=school, children=links.get(uid))
            for uid, pw in passwords.items() if uid in users]


# =================================================================== Stapel
def _aad(batch_id: str) -> str:
    return f"letter_batches:{batch_id}"


def create_batch(db: Session, actor: Any, entries: list[dict], title: str, *, store_initial: bool = True) -> LetterBatch:
    """Legt einen Stapel an (ohne Commit). Einträge werden sortiert (Klasse, Name; Eltern nach dem Kind).

    ``store_initial``: für die Konten die Startpasswort-Frist vermerken (nur Hash und Ablaufdatum, kein Klartext)."""
    from . import crypto

    if not entries:
        raise HTTPException(422, "Keine Zugangsdaten für einen Brief-Stapel")
    if len(entries) > MAX_BATCH_ENTRIES:
        raise HTTPException(422, f"Höchstens {MAX_BATCH_ENTRIES} Briefe je Stapel")
    batch_id = str(uuid.uuid4())
    now = utcnow()
    ordered = sorted(entries, key=_sort_key)
    batch = LetterBatch(id=batch_id, created_by=getattr(actor, "id", None) or None, created_at=now,
                        expires_at=now + timedelta(minutes=batch_minutes()), title=(title or "")[:200],
                        count=len(ordered),
                        data_enc=crypto.encrypt_text(json.dumps(ordered, ensure_ascii=False), _aad(batch_id)))
    db.add(batch)
    if store_initial:
        store_initial_passwords(db, actor, {e["user_id"]: "" for e in ordered if e.get("password")})
    db.flush()
    return batch


def batch_ref(batch: LetterBatch | None) -> dict | None:
    if batch is None:
        return None
    return {"id": batch.id, "expires_at": iso(batch.expires_at), "count": batch.count}


def batch_from_passwords(db: Session, actor: Any, passwords: dict[int, str], title: str) -> dict | None:
    """Stapel zu frisch gesetzten Startpasswörtern (``{user_id: passwort}``) für ``reset_password``/``bulk``.

    Fehler hier dürfen die eigentliche Aktion nicht verhindern: Savepoint, Fehler nur protokollieren → ``None``."""
    if not passwords:
        return None
    try:
        with db.begin_nested():
            batch = create_batch(db, actor, entries_for_passwords(db, passwords), title)
        return batch_ref(batch)
    except Exception:  # noqa: BLE001
        log.exception("Brief-Stapel konnte nicht angelegt werden")
        return None


def load_batch(db: Session, actor: Any, batch_id: str) -> tuple[LetterBatch, list[dict]]:
    """Stapel lesen: nur anlegende Person oder Rolle admin (sonst 404), abgelaufen → gelöscht + 410."""
    from . import crypto

    batch = db.get(LetterBatch, batch_id) if batch_id and len(batch_id) <= 36 else None
    if batch is None or (batch.created_by != getattr(actor, "id", None) and getattr(actor, "role", "") != "admin"):
        raise HTTPException(404, "Brief-Stapel nicht gefunden")
    if batch.expires_at <= utcnow():
        db.delete(batch)
        db.commit()
        raise HTTPException(410, f"Der Brief-Stapel ist abgelaufen – Startpasswörter werden aus Sicherheitsgründen "
                                 f"nur {batch_minutes()} Minuten aufbewahrt. Bitte neue Zugangsdaten erzeugen.")
    try:
        entries = json.loads(crypto.decrypt_text(batch.data_enc, _aad(batch.id)))
    except Exception:  # noqa: BLE001 - manipuliert/falscher Schlüssel
        log.exception("Brief-Stapel %s nicht lesbar", batch.id)
        raise HTTPException(410, "Der Brief-Stapel ist nicht mehr lesbar – bitte neue Zugangsdaten erzeugen.") from None
    return batch, entries


def delete_expired(db: Session, now: datetime | None = None) -> int:
    """Abgelaufene Stapel löschen (Wartung)."""
    return db.execute(delete(LetterBatch).where(LetterBatch.expires_at <= (now or utcnow()))).rowcount or 0


# =================================================================== Startpasswort-Frist (nur Hash, S-06)
def store_initial_passwords(db: Session, actor: Any, passwords: dict[int, str]) -> None:
    """Vermerkt für diese Konten: das aktuelle Passwort ist ein Startpasswort mit Frist (ohne Commit).

    Aufbewahrt wird **kein Klartext**, nur der Hash des Kontos zum Zeitpunkt der Vergabe und das Ablaufdatum
    (Einstellung „Startpasswort gilt … Tage“, Standard 14). Muss nach dem Setzen des Passwort-Hashs am Konto laufen."""
    from . import security_settings

    if not passwords:
        return
    now = utcnow()
    expires = now + timedelta(days=security_settings.initial_password_days(db))
    db.flush()
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(list(passwords))))}
    have = {r.user_id: r for r in db.scalars(select(AccountInitialPassword)
                                             .where(AccountInitialPassword.user_id.in_(list(passwords))))}
    for uid in passwords:
        user = users.get(uid)
        if user is None:
            continue
        row = have.get(uid) or AccountInitialPassword(user_id=uid)
        row.password_hash = user.password_hash or ""
        row.expires_at = expires
        row.created_at = now
        row.created_by = getattr(actor, "id", None) or None
        db.add(row)


def initial_password_info(db: Session, user_id: int) -> AccountInitialPassword | None:
    """Gültige Startpasswort-Marke (Passwort ist noch das Startpasswort), sonst ``None``."""
    row = db.get(AccountInitialPassword, user_id)
    user = db.get(User, user_id)
    if row is None or user is None or row.password_hash != (user.password_hash or ""):
        return None
    return row


def clear_initial(db: Session, user_id: int) -> None:
    """Marke entfernen (Passwort wurde geändert; ohne Commit)."""
    db.execute(delete(AccountInitialPassword).where(AccountInitialPassword.user_id == user_id))


# =================================================================== Rechte (Passwörter zurücksetzen)
def led_student_ids(actor: Any, school=None) -> set[str]:
    """Schüler/innen der Klassen, die die Lehrkraft ``actor`` leitet (Klassenleitung)."""
    tid = getattr(actor, "teacher_id", None)
    if not tid:
        return set()
    if school is None:
        from .store import get_store

        school = get_store().school
    classes = {c.id for c in school.classes if c.class_teacher == tid}
    return {s.id for s in school.students if s.class_id in classes}


def can_reset(actor: Any, role: str, student_id: str | None, *, led: set[str] | None = None) -> bool:
    """Darf ``actor`` das Passwort eines Kontos (``role``/``student_id``) zurücksetzen?

    ``users.manage`` mit passender Rolle; ``passwords.reset`` mit Scope ``class_teacher`` nur für Schülerkonten der
    eigenen Klassenleitung – nie Personal/Admins."""
    from .permissions import can_manage_role, scope_for

    perms = getattr(actor, "permissions", None) or set()
    if "users.manage" in perms and can_manage_role(actor.role, role):
        return True
    if "passwords.reset" not in perms:
        return False
    scope = scope_for(actor.role, "passwords.reset")
    if scope is None:
        return can_manage_role(actor.role, role)
    if scope == "class_teacher" and role == "schueler" and student_id:
        return student_id in (led if led is not None else led_student_ids(actor))
    return False


def check_reset(actor: Any, user: User) -> None:
    if not can_reset(actor, user.role, user.student_id):
        raise HTTPException(403, "Keine Berechtigung, das Passwort dieses Kontos zurückzusetzen")


def visible_entries(actor: Any, entries: list[dict]) -> list[dict]:
    """Einträge eines Stapels, die ``actor`` (noch) sehen darf."""
    led = led_student_ids(actor) if "users.manage" not in (getattr(actor, "permissions", None) or set()) else set()
    return [e for e in entries if can_reset(actor, e.get("role") or "", e.get("student_id"), led=led)]


# =================================================================== Konten anlegen / Passwörter setzen
def reset_passwords(db: Session, users: Iterable[User]) -> dict[int, str]:
    """Neue Startpasswörter (wie ``POST /users/{id}/reset-password``): Passwortwechsel-Zwang, Sitzungen beendet."""
    from .accounts import _hash_many, revoke_sessions
    from .security import generate_password

    users = list(users)
    passwords = [generate_password() for _ in users]
    for user, pw, pw_hash in zip(users, passwords, _hash_many(passwords)):
        user.password_hash = pw_hash
        user.must_change_password = True
        revoke_sessions(db, user.id)
    db.flush()
    return {u.id: pw for u, pw in zip(users, passwords)}


def username_base(first_name: str, last_name: str) -> str:
    """``vorname.nachname`` (ASCII, Doppelnamen mit ``-``)."""
    from .security import ascii_slug

    first, last = ascii_slug(first_name.translate(_TRANSLIT_MAP)), ascii_slug(last_name.translate(_TRANSLIT_MAP))
    return f"{first}.{last}" if first and last else (first or last or "schueler")


def _parent_username_base(parent_name: str, child: dict) -> str:
    if parent_name.strip():
        first, last = split_name(parent_name)
        return f"eltern.{username_base(first, last)}"
    return f"eltern.{username_base(child.get('first_name', ''), child.get('last_name', ''))}"


def plan_accounts(db: Session, students: list[dict], *, student_accounts: bool,
                  parent_accounts: bool) -> tuple[list[dict], list[str]]:
    """Konten für neue Schüler/innen und ihre Eltern planen (ändert nichts). Rückgabe ``(plan, warnungen)``.

    ``students``: ``[{index, first_name, last_name, name, email?, adult?, parents?: [{name, email}]}]`` – ``index``
    verknüpft den Plan mit der Eingabezeile (Schüler-IDs entstehen erst beim Speichern).

    Plan-Einträge: ``{kind: "new"|"existing", role, indexes: [...], username, display_name, email, adult, user_id?}``.
    Elternkonten werden über die E-Mail zusammengeführt: ein Elternteil mit mehreren Kindern bekommt **ein** Konto;
    gibt es schon ein Elternkonto mit der Adresse, werden die Kinder dort ergänzt (``kind="existing"``, kein neues
    Passwort). Ohne Elternangaben entsteht je Kind ein Konto „Eltern von …“."""
    from .accounts import unique_username

    reserved: set[str] = {u.lower() for u in db.scalars(select(User.username))}
    plan: list[dict] = []
    warnings: list[str] = []
    for s in students:
        if student_accounts:
            plan.append({"kind": "new", "role": "schueler", "indexes": [s["index"]], "display_name": s["name"],
                         "username": unique_username(db, username_base(s.get("first_name", ""),
                                                                       s.get("last_name", "")), reserved,
                                                     check_db=False),
                         "email": (s.get("email") or None), "adult": bool(s.get("adult"))})
    if not parent_accounts:
        return plan, warnings
    emails = {(p.get("email") or "").strip().lower() for s in students for p in s.get("parents") or []}
    emails.discard("")
    by_email: dict[str, User] = {}
    other_roles: set[str] = set()
    if emails:
        from sqlalchemy import func

        for u in db.scalars(select(User).where(func.lower(User.email).in_(emails)).order_by(User.id)):
            key = (u.email or "").lower()
            if u.role == "eltern":
                by_email.setdefault(key, u)
            else:
                other_roles.add(key)
    groups: dict[str, dict] = {}
    for s in students:
        parents = [p for p in s.get("parents") or [] if (p.get("name") or "").strip() or (p.get("email") or "").strip()]
        if not parents:
            parents = [{"name": "", "email": ""}]
        seen: set[str] = set()
        for pos, p in enumerate(parents[:2]):
            name, email = (p.get("name") or "").strip(), (p.get("email") or "").strip()
            key = f"mail:{email.lower()}" if email else f"row:{s['index']}:{pos}"
            if key in seen:
                continue
            seen.add(key)
            item = groups.get(key)
            if item is not None:
                item["indexes"].append(s["index"])
                item["children"].append(s["name"])
                continue
            existing = by_email.get(email.lower()) if email else None
            if existing is not None:
                if not existing.active:
                    warnings.append(f"Das Elternkonto {existing.username} ({existing.email}) ist deaktiviert – "
                                    f"{s['name']} wird dort ergänzt, ein Zugang besteht erst nach der Aktivierung.")
                item = {"kind": "existing", "role": "eltern", "indexes": [s["index"]], "user_id": existing.id,
                        "username": existing.username, "display_name": existing.display_name, "email": existing.email,
                        "adult": False, "children": [s["name"]]}
            else:
                if email and email.lower() in other_roles:
                    warnings.append(f"Die E-Mail-Adresse {email} gehört schon zu einem Konto, das kein Elternkonto "
                                    "ist – es wird ein eigenes Elternkonto angelegt.")
                item = {"kind": "new", "role": "eltern", "indexes": [s["index"]], "parent_name": name,
                        "username": unique_username(db, _parent_username_base(name, s), reserved, check_db=False),
                        "display_name": name, "email": email or None, "adult": False, "children": [s["name"]]}
            groups[key] = item
            plan.append(item)
    for item in plan:
        if item["role"] == "eltern" and item["kind"] == "new" and not item.get("display_name"):
            item["display_name"] = "Eltern von " + _join(item["children"], "und")
        item.pop("children", None)
    return plan, warnings


def create_planned(db: Session, plan: list[dict], students: dict[int, dict]) -> tuple[list[dict], list[dict]]:
    """Legt die geplanten Konten an bzw. ergänzt Kinder bei vorhandenen Elternkonten (ohne Commit).

    ``students``: ``index → {student_id, first_name, last_name, name, class_id, class_name}``.
    Rückgabe ``(einträge_mit_startpasswort, ergänzte_elternkonten)``."""
    from .accounts import _hash_many, unique_username, username_taken
    from .security import generate_password

    new = [p for p in plan if p["kind"] == "new"]
    passwords = [generate_password() for _ in new]
    hashes = iter(_hash_many(passwords))
    pw_iter = iter(passwords)
    entries: list[dict] = []
    linked: list[dict] = []
    now = utcnow()
    for item in plan:
        kids = [students[i] for i in item["indexes"]]
        if item["kind"] == "existing":
            have = set(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == item["user_id"])))
            added = [k["student_id"] for k in kids if k["student_id"] not in have]
            for sid in added:
                db.add(ParentLink(parent_user_id=item["user_id"], student_id=sid))
            linked.append({"user_id": item["user_id"], "username": item["username"],
                           "display_name": item["display_name"], "role": "eltern", "existing": True,
                           "student_ids": added})
            continue
        pw, pw_hash = next(pw_iter), next(hashes)
        if username_taken(db, item["username"]):          # seit der Planung vergeben (gleichzeitige Anlage)
            item["username"] = unique_username(db, item["username"])
        st = kids[0]
        user = User(username=item["username"], display_name=item["display_name"], role=item["role"],
                    password_hash=pw_hash, must_change_password=True,
                    student_id=st["student_id"] if item["role"] == "schueler" else None,
                    email=item.get("email") or None, adult=bool(item.get("adult")) and item["role"] == "schueler",
                    active=True, totp_enabled=False, created_at=now)
        db.add(user)
        db.flush()
        entry = {"user_id": user.id, "username": user.username, "display_name": user.display_name,
                 "role": user.role, "first_name": st.get("first_name", ""), "last_name": st.get("last_name", ""),
                 "class_id": st.get("class_id"), "class_name": st.get("class_name"), "student_id": user.student_id,
                 "adult": bool(user.adult), "password": pw, "children": []}
        if item["role"] == "eltern":
            first, last = split_name(item.get("parent_name") or "")
            entry.update(first_name=first, last_name=last, class_id=None, class_name=None,
                         children=[{"student_id": k["student_id"], "name": k["name"], "class_id": k.get("class_id")}
                                   for k in kids])
            for k in kids:
                db.add(ParentLink(parent_user_id=user.id, student_id=k["student_id"]))
        entries.append(entry)
    db.flush()
    return entries, linked


# =================================================================== Richtlinien-Hinweise
def _provider_label(pid: str) -> str:
    try:
        from .identities import PROVIDER_LABELS

        return PROVIDER_LABELS.get(pid, pid)
    except Exception:  # noqa: BLE001
        return pid


def policy_info(db: Session, user: User | None) -> dict[str, Any]:
    """``{password: bool, providers: [ids], required: [ids]}`` aus ``login_policy.effective_policy``."""
    info: dict[str, Any] = {"password": True, "providers": [], "required": []}
    if user is None:
        return info
    try:
        from . import login_policy

        pol = login_policy.effective_policy(db, user)
        methods = set(pol.methods or ())
        order = list(getattr(login_policy, "METHODS", ()))
        rank = {m: i for i, m in enumerate(order)}
        info["password"] = "password" in methods
        info["providers"] = sorted((m for m in methods if m != "password"), key=lambda m: (rank.get(m, 99), m))
        info["required"] = sorted(set(pol.required_links or ()), key=lambda m: (rank.get(m, 99), m))
    except Exception:  # noqa: BLE001 - Richtlinie nicht auswertbar → Standard (Passwort)
        log.exception("Anmelde-Richtlinie für Konto %s nicht auswertbar", getattr(user, "id", "?"))
    return info


def _account_word(label: str) -> str:
    return label if label.lower().endswith("konto") else f"{label}-Konto"


def _join(items: list[str], word: str) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {word} " + items[-1]


def letter_hints(entry: dict, info: dict, *, formal: bool) -> dict[str, Any]:
    """Texte für den Brief abhängig von der Richtlinie. ``print_password`` = Startpasswort drucken."""
    labels = [_account_word(_provider_label(p)) for p in info.get("providers", [])]
    required = [_account_word(_provider_label(p)) for p in info.get("required", [])]
    has_pw = bool(entry.get("password"))
    print_password = has_pw and (info.get("password", True) or bool(required))
    out: dict[str, Any] = {"print_password": print_password, "login": None, "link": None, "first_only": False,
                           "after": None}
    poss, acc = "Ihrem", "Ihr"
    if not info.get("password", True) and labels:
        out["login"] = f"Melden Sie sich mit {poss} {_join(labels, 'oder')} an."
        out["first_only"] = print_password
        if print_password:
            out["after"] = (f"Das Startpasswort brauchen Sie nur für die erste Anmeldung – danach melden Sie sich "
                            f"nur noch mit {poss} {_join(labels, 'oder')} an.")
    if required:
        names = f"{acc} {_join(required, 'und')}"
        out["link"] = f"Verbinden Sie nach dem ersten Anmelden {names}."
    return out


# =================================================================== Brief (PDF)
MARGIN = 22 * pdf.MM
GRAY = 0.38
LIGHT = 0.955
ACCENT = (0.11, 0.29, 0.55)


def _de_date(dt: datetime) -> str:
    local = dt.replace(tzinfo=timezone.utc).astimezone() if dt.tzinfo is None else dt.astimezone()
    return f"{local.day}. {_MONTHS[local.month - 1]} {local.year}"


def _formal(entry: dict) -> bool:
    """Die App siezt alle, auch Schüler/innen."""
    return True


def letter_title(entry: dict) -> str:
    role = entry.get("role")
    if role == "eltern":
        kids = entry.get("children") or []
        if not kids:
            return f"Zugangsdaten für {entry.get('display_name') or 'die Eltern'}"
        if len(kids) == 1:
            k = kids[0]
            return f"Zugangsdaten für die Eltern von {k['name']}" + (f" (Klasse {k['class_id']})"
                                                                     if k.get("class_id") else "")
        names = [f"{k['name']} ({k['class_id']})" if k.get("class_id") else k["name"] for k in kids]
        return f"Zugangsdaten für die Eltern von {_join(names, 'und')}"
    name = entry.get("display_name") or entry.get("username") or ""
    if role == "schueler" and entry.get("class_id"):
        return f"Zugangsdaten für {name} (Klasse {entry['class_id']})"
    return f"Zugangsdaten für {name}"


def _parent_greeting(entry: dict) -> str:
    name = (entry.get("display_name") or "").strip()
    return f"Guten Tag {name}," if name and not name.startswith("Eltern") else "Sehr geehrte Eltern,"


def _intro(entry: dict, school: str) -> tuple[str, str]:
    role = entry.get("role")
    if role == "eltern":
        many = len(entry.get("children") or []) > 1
        kid, it = ("Ihrer Kinder", "sie") if many else ("Ihres Kindes", "es")
        return (_parent_greeting(entry),
                f"über {PRODUCT_NAME} der {school} sehen Sie den Stundenplan und die Vertretungen {kid}, "
                f"können {it} krankmelden und erhalten Mitteilungen der Schule. Hier sind Ihre persönlichen "
                "Zugangsdaten" + (" – ein Konto für alle Ihre Kinder." if many else "."))
    name = entry.get("display_name") or ""
    if role == "schueler":
        return (f"Guten Tag {name},".replace(" ,", ","),
                f"ab sofort können Sie {PRODUCT_NAME} der {school} nutzen – dort finden Sie Ihren Stundenplan, "
                "Vertretungen, Termine und Nachrichten. Hier sind Ihre persönlichen Zugangsdaten.")
    return (f"Guten Tag {name},".replace(" ,", ","),
            f"hier sind Ihre persönlichen Zugangsdaten für {PRODUCT_NAME} der {school}.")


def _draw_letter(page: pdf.Page, entry: dict, info: dict, *, school: str, url: str, date_text: str) -> None:
    formal = _formal(entry)
    hints = letter_hints(entry, info, formal=formal)
    w = page.width - 2 * MARGIN
    x = MARGIN
    # Kopf: Bildmarke, Schulname, Datum; Produktmarke klein rechts
    draw_logo(page, x, 42, 24)
    page.text(x + 32, 60, school, size=12, font="bold")
    page.text_right(page.width - MARGIN, 60, date_text, size=10, color=GRAY)
    page.text_right(page.width - MARGIN, 72 + 10, PRODUCT_NAME, size=8, color=GRAY)
    page.line(x, 70, page.width - MARGIN, 70, width=0.6, color=0.75)
    # Titel
    y = page.paragraph(x, 108, letter_title(entry), w, size=17, font="bold", leading=21)
    page.text(x, y - 4, "Persönlich – bitte sicher aufbewahren", size=9.5, color=GRAY)
    y += 22
    greet, intro = _intro(entry, school)
    y = page.paragraph(x, y, greet, w, size=11, leading=15)       # lange Namen umbrechen statt über den Rand
    y = page.paragraph(x, y + 2, intro, w, size=11, leading=15) + 8

    # Zugangsdaten-Kasten mit QR-Code rechts
    qr = 104
    pad = 14
    rows: list[tuple[str, str, str]] = [("Anmeldeadresse", url, "bold")]
    rows.append(("Benutzername", entry.get("username") or "", "mono-bold"))
    if hints["print_password"]:
        rows.append(("Startpasswort", entry.get("password") or "", "mono-bold"))
    else:
        rows.append(("Anmeldung", hints["login"] or "über die Anmeldeseite", "bold"))
    col = w - qr - 3 * pad
    heights = []
    for label, value, font in rows:
        size = 15 if font == "mono-bold" else 11.5
        lines = pdf.wrap(value, col, size, font)
        heights.append(14 + len(lines) * (size + 4) + 6)
    box_h = max(sum(heights) + 2 * pad - 6, qr + 2 * pad + 12)
    page.rect(x, y, w, box_h, fill=LIGHT, stroke=0.78, width=0.8)
    cy = y + pad
    for (label, value, font), h in zip(rows, heights):
        size = 15 if font == "mono-bold" else 11.5
        page.text(x + pad, cy + 9, label, size=8.5, color=GRAY)
        ly = cy + 14 + size
        for line in pdf.wrap(value, col, size, font):
            page.text(x + pad, ly, line, size=size, font=font, color=ACCENT if font == "mono-bold" else None)
            ly += size + 4
        cy += h
    qx = x + w - pad - qr
    page.rect(qx - 4, y + pad - 4, qr + 8, qr + 8, fill=1)
    page.qr(qx, y + pad, url, size=qr)
    page.text_center(qx + qr / 2, y + pad + qr + 15, "QR-Code zur Anmeldeseite", size=8, color=GRAY)
    y += box_h + 10
    if hints["print_password"] and _GENERATED_PW.match(entry.get("password") or ""):
        page.text(x, y + 2, "Das Startpasswort enthält nur Kleinbuchstaben, Ziffern und Bindestriche "
                            "(keine Verwechslungsgefahr: kein 0/o, 1/l/i).", size=8.5, color=GRAY)
        y += 12
    y += 18

    # So geht's
    page.text(x, y, "So melden Sie sich an", size=12.5, font="bold")
    y += 18
    steps = ["Öffnen Sie die Anmeldeadresse im Browser oder scannen Sie den QR-Code mit dem Handy."]
    if hints["print_password"]:
        steps.append("Geben Sie Benutzername und Startpasswort ein.")
        steps.append(f"Legen Sie ein eigenes Passwort fest – das verlangt {PRODUCT_NAME} beim ersten Anmelden.")
    else:
        steps.append(hints["login"] or "Melden Sie sich an.")
    if hints["link"]:
        steps.append(hints["link"])
    if hints["after"]:
        steps.append(hints["after"])
    for i, step in enumerate(steps, start=1):
        page.text(x, y, f"{i}.", size=11, font="bold")
        y = page.paragraph(x + 18, y, step, w - 18, size=11, leading=15) + 3
    y += 12

    # Wichtig
    page.text(x, y, "Wichtig", size=12.5, font="bold")
    y += 18
    notes = ["Beim ersten Anmelden legen Sie ein eigenes Passwort fest." if hints["print_password"] else
             "Ein Passwort brauchen Sie für die Anmeldung nicht.",
             "Bewahren Sie diesen Brief sicher auf und geben Sie das Passwort niemandem weiter."
             if hints["print_password"] else "Bewahren Sie diesen Brief sicher auf.",
             "Das Startpasswort gilt nur, bis Sie Ihr eigenes Passwort festgelegt haben."
             if hints["print_password"] else "",
             "Fragen oder Passwort vergessen? Wenden Sie sich bitte an das Sekretariat." if hints["print_password"]
             else "Fragen? Wenden Sie sich bitte an das Sekretariat."]
    for note in (n for n in notes if n):
        page.text(x + 2, y, "•", size=11, font="bold")
        y = page.paragraph(x + 14, y, note, w - 14, size=11, leading=15) + 2

    # Fuß
    page.line(x, page.height - 52, page.width - MARGIN, page.height - 52, width=0.4, color=0.8)
    page.text(x, page.height - 38, f"{school} · Zugangsbrief vom {date_text} · maschinell erstellt, ohne Unterschrift "
                                   "gültig", size=8, color=GRAY)


def render_letters(db: Session, entries: list[dict], *, created_at: datetime | None = None,
                   title: str = "Zugangsdaten") -> bytes:
    """PDF mit einer Seite je Eintrag (Richtlinien-Hinweise je Konto)."""
    school = school_name()
    url = login_url()
    date_text = _de_date(created_at or utcnow())
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_([e["user_id"] for e in entries])))}
    doc = pdf.Document(title=title, author=school, subject=f"Zugangsdaten für {PRODUCT_NAME}")
    for entry in entries:
        page = doc.add_page()
        _draw_letter(page, entry, policy_info(db, users.get(entry["user_id"])), school=school, url=url,
                     date_text=date_text)
    return doc.output()


def zip_letters(db: Session, entries: list[dict], *, created_at: datetime | None = None) -> bytes:
    """ZIP mit je einem PDF pro Eintrag (eindeutige ASCII-Dateinamen)."""
    buf = io.BytesIO()
    used: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            name = entry_filename(entry, used)
            zf.writestr(name, render_letters(db, [entry], created_at=created_at, title=letter_title(entry)))
    return buf.getvalue()


# =================================================================== E-Mail
def email_message(entry: dict, *, to_parents: bool) -> tuple[str, str]:
    """Betreff und Text einer E-Mail mit dem Brief im Anhang (ohne Passwort im Text)."""
    school = school_name()
    url = login_url()
    # Zeilenumbrüche im Namen würden den Betreff (E-Mail-Kopfzeile) unzustellbar machen
    name = " ".join((entry.get("display_name") or entry.get("username") or "").split())
    if to_parents and entry.get("role") == "schueler":
        cls = f" (Klasse {entry['class_id']})" if entry.get("class_id") else ""
        subject = f"Zugangsdaten Ihres Kindes {name} für {PRODUCT_NAME}"
        body = (f"Sehr geehrte Eltern,\n\nim Anhang finden Sie den Zugangsbrief Ihres Kindes {name}{cls} für "
                f"{PRODUCT_NAME} der {school}. Bitte geben Sie ihn an Ihr Kind weiter. Beim ersten Anmelden wird ein "
                f"eigenes Passwort festgelegt.\n\nAnmeldung: {url}\n\nBitte bewahren Sie die Zugangsdaten sicher auf "
                "und löschen Sie diese E-Mail, sobald das eigene Passwort festgelegt ist.\n\n"
                f"Mit freundlichen Grüßen\n{school}\n")
        return subject, body
    greet = _parent_greeting(entry).rstrip(",") if entry.get("role") == "eltern" else f"Guten Tag {name}"
    subject = f"Ihre Zugangsdaten für {PRODUCT_NAME}"
    body = (f"{greet},\n\nim Anhang finden Sie Ihren Zugangsbrief für {PRODUCT_NAME} der {school} mit "
            f"Benutzername und Startpasswort. Beim ersten Anmelden legen Sie ein eigenes Passwort fest.\n\n"
            f"Anmeldung: {url}\n\nBitte geben Sie das Passwort niemandem weiter und löschen Sie diese E-Mail, "
            f"sobald Sie Ihr eigenes Passwort festgelegt haben.\n\nMit freundlichen Grüßen\n{school}\n")
    return subject, body


def _parents_of(db: Session, student_ids: list[str]) -> dict[str, list[User]]:
    """Schüler-ID → verknüpfte (aktive) Elternkonten."""
    out: dict[str, list[User]] = {}
    if not student_ids:
        return out
    rows = db.execute(select(ParentLink.student_id, User).join(User, User.id == ParentLink.parent_user_id)
                      .where(ParentLink.student_id.in_(student_ids), User.active.is_(True)).order_by(User.id))
    for sid, user in rows:
        out.setdefault(sid, []).append(user)
    return out


def is_adult_student(entry: dict, user: User | None = None) -> bool:
    """Volljährige Schülerin/volljähriger Schüler (Stand im Stapel oder aktuell am Konto)?"""
    return entry.get("role") == "schueler" and (bool(entry.get("adult")) or bool(user is not None and user.adult))


def send_entries(db: Session, entries: list[dict], *, to: str, adults_to: str | None = None,
                 created_at: datetime | None = None) -> dict[str, Any]:
    """Je Person eine E-Mail mit ihrem Brief (PDF) über ``auth_messages.queue_email`` (ohne Commit).

    ``to``: ``student`` = an das Konto selbst, ``parents`` = an die verknüpften Elternkonten (Elternbriefe: an das
    Elternkonto), ``both`` = beides. Volljährige Schüler/innen bekommen ihren Brief immer nur selbst (nie über die
    Eltern); ``adults_to`` bleibt aus Kompatibilität und wird ignoriert.
    Rückgabe ``{sent, no_address, unavailable}`` (je ``{user_id, display_name, role, recipients}``)."""
    from . import auth_messages

    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_([e["user_id"] for e in entries])))}
    parents = _parents_of(db, [e["student_id"] for e in entries if e.get("role") == "schueler" and e.get("student_id")])
    used: set[str] = set()
    names = [entry_filename(e, used) for e in entries]
    sent, no_address, unavailable = [], [], []
    for e, fname in zip(entries, names):
        user = users.get(e["user_id"])
        target = to
        if is_adult_student(e, user):
            # Volljährige bekommen ihren Brief nie über die Eltern (kein Familienzugriff wie bei Dokumenten) – nur selbst
            target = "student"
        recipients: list[tuple[str, bool]] = []
        own = user.email if user is not None and user.active and user.email else None
        if own and (target in ("student", "both") or e.get("role") == "eltern"):
            recipients.append((own, False))
        if target in ("parents", "both") and e.get("role") == "schueler":
            recipients += [(p.email, True) for p in parents.get(e.get("student_id") or "", []) if p.email]
        seen: set[str] = set()
        recipients = [(a, p) for a, p in recipients if not (a.lower() in seen or seen.add(a.lower()))]
        row = {"user_id": e["user_id"], "display_name": e["display_name"], "role": e["role"]}
        if not recipients:
            no_address.append(row)
            continue
        data = render_letters(db, [e], created_at=created_at, title=letter_title(e))
        ok, failed = [], []
        for address, to_parents in recipients:
            subject, text = email_message(e, to_parents=to_parents)
            try:
                rid = auth_messages.queue_email(db, address, subject, text, purpose="letter",
                                                attachments=[{"filename": fname, "content_type": "application/pdf",
                                                              "data": data}])
            except Exception:  # noqa: BLE001 - ein Fehler darf den übrigen Versand nicht verhindern
                log.exception("Zugangsbrief konnte nicht in den Postausgang gelegt werden")
                rid = None
            (ok if rid is not None else failed).append(address)
        if ok:
            sent.append({**row, "recipients": ok, "failed": failed})
        else:
            unavailable.append({**row, "recipients": failed})
    return {"sent": sent, "no_address": no_address, "unavailable": unavailable}


def kick_outbox() -> None:
    try:
        from . import notify

        notify.kick()
    except Exception:  # noqa: BLE001
        pass
