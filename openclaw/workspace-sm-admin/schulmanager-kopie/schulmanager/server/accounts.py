"""Kontenlogik (von Routern, Bootstrap, Demo und SSO gemeinsam genutzt)."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any, Iterable

from fastapi import HTTPException, Request
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from ..models import School
from .config import config
from .db import iso, utcnow
from .db_models import (
    Announcement,
    ApiToken,
    AuditLog,
    LoginAttempt,
    ParentLink,
    SchoolVersion,
    StudentAbsence,
    User,
    UserSession,
)
from .permissions import ROLES, teacher_class_ids
from .security import TEMP_PASSWORD_N, ascii_slug, generate_password, hash_password, hash_token, new_token

log = logging.getLogger("schulmanager.accounts")

USERNAME_MAX = 80


# --------------------------------------------------------------------------- Darstellung
def user_dict(db: Session, user: User, *, children: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role,
        "teacher_id": user.teacher_id, "student_id": user.student_id, "site": user.site, "email": user.email,
        "active": bool(user.active), "adult": bool(user.adult), "must_change_password": bool(user.must_change_password),
        "totp_enabled": bool(user.totp_enabled), "sso": bool(user.oidc_sub), "created_at": iso(user.created_at),
        "last_login": iso(user.last_login),
    }
    if children and user.role == "eltern":
        out["student_ids"] = list(db.scalars(select(ParentLink.student_id)
                                             .where(ParentLink.parent_user_id == user.id).order_by(ParentLink.id)))
    return out


def normalize_username(name: str) -> str:
    """Erlaubt: a-z 0-9 . _ - (klein); Umlaute werden umgeschrieben."""
    slug = ascii_slug(name, keep="._-")
    return slug[:USERNAME_MAX]


def username_taken(db: Session, username: str) -> bool:
    return db.scalar(select(func.count(User.id)).where(func.lower(User.username) == username.lower())) > 0


def unique_username(db: Session, base: str, reserved: set[str] | None = None, *, check_db: bool = True) -> str:
    """``base``, sonst ``base2``, ``base3`` … (prüft ``reserved`` und – mit ``check_db`` – die DB)."""
    base = normalize_username(base) or "benutzer"
    reserved = reserved if reserved is not None else set()
    candidate, n = base, 1
    while candidate in reserved or (check_db and username_taken(db, candidate)):
        n += 1
        candidate = f"{base[:USERNAME_MAX - len(str(n))]}{n}"
    reserved.add(candidate)
    return candidate


# --------------------------------------------------------------------------- Anlegen
def create_user(db: Session, *, username: str, role: str, display_name: str = "", password: str | None = None,
                must_change_password: bool = True, teacher_id: str | None = None, student_id: str | None = None,
                site: str | None = None, email: str | None = None, adult: bool = False,
                password_hash: str | None = None) -> tuple[User, str | None]:
    """Legt ein Konto an (ohne Commit). Ohne ``password`` wird ein Startpasswort erzeugt und zurückgegeben."""
    if role not in ROLES:
        raise HTTPException(422, f"Unbekannte Rolle: {role}")
    username = normalize_username(username)
    if not username:
        raise HTTPException(422, "Benutzername fehlt oder enthält keine gültigen Zeichen")
    if username_taken(db, username):
        raise HTTPException(409, f"Benutzername {username} ist bereits vergeben")
    temp = None
    if password_hash is None:
        if password is None:
            temp = generate_password()
            password_hash = hash_password(temp, n=min(TEMP_PASSWORD_N, config.scrypt_n))
            must_change_password = True
        else:
            password_hash = hash_password(password)
    user = User(username=username, role=role, display_name=display_name or username, password_hash=password_hash,
                must_change_password=must_change_password, teacher_id=teacher_id or None,
                student_id=student_id or None, site=site or None, email=email or None, adult=adult, active=True,
                totp_enabled=False, created_at=utcnow())
    db.add(user)
    db.flush()
    return user, temp


def set_children(db: Session, parent: User, student_ids: Iterable[str]) -> list[str]:
    ids = list(dict.fromkeys(s for s in student_ids if s))
    db.execute(delete(ParentLink).where(ParentLink.parent_user_id == parent.id))
    for sid in ids:
        db.add(ParentLink(parent_user_id=parent.id, student_id=sid))
    db.flush()
    return ids


# --------------------------------------------------------------------------- Massenanlage
def _split_name(name: str) -> tuple[str, str]:
    parts = name.replace(",", " ").split()
    if not parts:
        return "", ""
    if "," in name:  # "Nachname, Vorname"
        last, first = name.split(",", 1)
        return first.strip().split()[0] if first.strip() else "", last.strip()
    return parts[0], " ".join(parts[1:])


def student_username_base(name: str) -> str:
    first, last = _split_name(name)
    first_s, last_s = ascii_slug(first), ascii_slug(last)
    return f"{first_s}.{last_s}" if first_s and last_s else (first_s or last_s or "schueler")


def _hash_many(passwords: list[str]) -> list[str]:
    n = min(TEMP_PASSWORD_N, config.scrypt_n)
    if len(passwords) < 8:
        return [hash_password(p, n=n) for p in passwords]
    with ThreadPoolExecutor(max_workers=8) as pool:  # hashlib.scrypt gibt den GIL frei
        return list(pool.map(lambda p: hash_password(p, n=n), passwords))


def bulk_create(db: Session, school: School, role: str, class_ids: list[str] | None = None) -> dict[str, Any]:
    """Legt Konten für alle Schüler/Lehrkräfte/Eltern ohne Konto an (ohne Commit).

    * Schüler: ``vorname.nachname`` (ASCII), Zähler bei Duplikaten.
    * Lehrkräfte: Kürzel klein (nur Lehrkräfte, die in ``class_ids`` unterrichten, falls angegeben).
    * Eltern: ``eltern.<vorname.nachname>`` je Schüler ohne verknüpftes Elternkonto.
    Rückgabe ``{"created": [{id, username, display_name, temp_password, class, role, student_id|teacher_id}],
    "skipped": n}``.
    """
    wanted = set(class_ids or [])
    reserved: set[str] = {u.lower() for u in db.scalars(select(User.username))}
    plan: list[dict[str, Any]] = []
    skipped = 0
    if role in ("schueler", "eltern"):
        students = [s for s in school.students if not wanted or s.class_id in wanted]
        if role == "schueler":
            have = set(db.scalars(select(User.student_id).where(User.role == "schueler", User.student_id.is_not(None))))
        else:
            have = set(db.scalars(select(ParentLink.student_id)))
        for s in students:
            if s.id in have:
                skipped += 1
                continue
            base = student_username_base(s.name)
            if role == "schueler":
                plan.append({"username": unique_username(db, base, reserved, check_db=False), "display_name": s.name,
                             "student_id": s.id, "class": s.class_id})
            else:
                plan.append({"username": unique_username(db, f"eltern.{base}", reserved, check_db=False),
                             "display_name": f"Eltern von {s.name}", "child": s.id, "class": s.class_id})
    elif role == "lehrer":
        teachers = school.teachers
        if wanted:
            teachers = [t for t in teachers if teacher_class_ids(school, t.id) & wanted]
        have = set(db.scalars(select(User.teacher_id).where(User.teacher_id.is_not(None))))
        for t in teachers:
            if t.id in have:
                skipped += 1
                continue
            plan.append({"username": unique_username(db, t.id.lower(), reserved, check_db=False),
                         "display_name": t.name,
                         "teacher_id": t.id, "class": None})
    else:
        raise HTTPException(422, "Massenanlage nur für Rollen schueler, lehrer oder eltern")

    passwords = [generate_password() for _ in plan]
    hashes = _hash_many(passwords)
    created = []
    now = utcnow()
    for item, pw, pw_hash in zip(plan, passwords, hashes):
        user = User(username=item["username"], display_name=item["display_name"], role=role, password_hash=pw_hash,
                    must_change_password=True, teacher_id=item.get("teacher_id"), student_id=item.get("student_id"),
                    active=True, totp_enabled=False, adult=False, created_at=now)
        db.add(user)
        db.flush()
        if role == "eltern":
            db.add(ParentLink(parent_user_id=user.id, student_id=item["child"]))
        entry = {"id": user.id, "username": user.username, "display_name": user.display_name, "temp_password": pw,
                 "class": item["class"], "role": role}
        for key in ("teacher_id", "student_id"):
            if item.get(key):
                entry[key] = item[key]
        if role == "eltern":
            entry["student_ids"] = [item["child"]]
        created.append(entry)
    db.flush()
    return {"created": created, "skipped": skipped}


# --------------------------------------------------------------------------- Sitzungen
def create_session(db: Session, user: User, request: Request | None, ip: str | None = None) -> tuple[str, UserSession]:
    """Neue Sitzung (ohne Commit). Gibt (Klartext-Token für das Cookie, Sitzung) zurück."""
    token = new_token()
    now = utcnow()
    hard = now + timedelta(days=config.session_max_days)
    from . import security_settings
    idle = security_settings.idle_minutes(db, user.role)         # Personal: kürzere Inaktivitäts-Abmeldung (S-17)
    sess = UserSession(token_hash=hash_token(token), csrf_token=new_token(24), user_id=user.id, created_at=now,
                       last_seen=now, expires_at=min(now + timedelta(minutes=idle), hard),
                       ip=ip, user_agent=(request.headers.get("user-agent", "")[:300] if request else None))
    db.add(sess)
    db.flush()
    return token, sess


def revoke_sessions(db: Session, user_id: int, except_session_id: int | None = None) -> int:
    stmt = delete(UserSession).where(UserSession.user_id == user_id)
    if except_session_id is not None:
        stmt = stmt.where(UserSession.id != except_session_id)
    return db.execute(stmt).rowcount or 0


def session_dict(sess: UserSession, current_id: int | None = None) -> dict[str, Any]:
    return {"id": sess.id, "created_at": iso(sess.created_at), "last_seen": iso(sess.last_seen),
            "expires_at": iso(sess.expires_at), "ip": sess.ip, "user_agent": sess.user_agent,
            "current": sess.id == current_id}


def token_dict(tok: ApiToken) -> dict[str, Any]:
    return {"id": tok.id, "name": tok.name, "prefix": tok.prefix, "created_at": iso(tok.created_at),
            "last_used": iso(tok.last_used), "expires_at": iso(tok.expires_at),
            "scoped": tok.scope is not None}


# --------------------------------------------------------------------------- Löschen (DSGVO)
def delete_user(db: Session, user: User) -> None:
    """Löscht ein Konto vollständig; Protokolle werden pseudonymisiert (ohne Commit)."""
    pseudo = f"gelöscht#{user.id}"
    db.execute(update(AuditLog).where(AuditLog.user_id == user.id).values(user_id=None, username=pseudo))
    db.execute(update(AuditLog).where(AuditLog.username == user.username).values(username=pseudo))
    db.execute(update(SchoolVersion).where(SchoolVersion.user_id == user.id).values(user_id=None))
    db.execute(update(Announcement).where(Announcement.author_id == user.id).values(author_id=None))
    db.execute(update(StudentAbsence).where(StudentAbsence.reported_by == user.id).values(reported_by=None))
    from .feature_models.absence_log import AbsenceEvent
    db.execute(update(AbsenceEvent).where(AbsenceEvent.actor_id == user.id).values(actor_id=None, actor_name=pseudo))
    db.execute(delete(LoginAttempt).where(LoginAttempt.username == user.username))
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.execute(delete(ApiToken).where(ApiToken.user_id == user.id))
    db.execute(delete(ParentLink).where(ParentLink.parent_user_id == user.id))
    db.delete(user)
    db.flush()


def count_active_admins(db: Session) -> int:
    return int(db.scalar(select(func.count(User.id)).where(User.role == "admin", User.active.is_(True))) or 0)
