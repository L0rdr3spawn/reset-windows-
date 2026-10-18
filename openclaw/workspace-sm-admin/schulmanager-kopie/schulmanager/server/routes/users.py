"""Benutzerverwaltung: Konten, Massenanlage, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..accounts import (
    bulk_create,
    count_active_admins,
    create_user,
    delete_user,
    revoke_sessions,
    session_dict,
    set_children,
    token_dict,
    user_dict,
)
from ...branding import PRODUCT_NAME, draw_logo_simple
from ..audit import audit
from ..config import config
from ..db import get_db, iso, utcnow
from ..db_models import ApiToken, ParentLink, User, UserSession
from ..deps import AuthUser, client_ip, current_user, require
from ..permissions import ROLES, can_manage_role, manageable_roles
from ..security import TEMP_PASSWORD_N, generate_password, hash_password, hash_token, new_token, password_problems, set_totp_secret
from ..store import get_store

router = APIRouter(tags=["Benutzer"])


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    role: str
    display_name: str = Field(default="", max_length=200)
    password: str | None = Field(default=None, max_length=256)
    must_change_password: bool = True
    teacher_id: str | None = None
    student_id: str | None = None
    student_ids: list[str] | None = None
    site: str | None = None
    email: str | None = Field(default=None, max_length=254)
    adult: bool = False


class UserPatch(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    role: str | None = None
    password: str | None = Field(default=None, max_length=256)
    must_change_password: bool | None = None
    teacher_id: str | None = None
    student_id: str | None = None
    student_ids: list[str] | None = None
    site: str | None = None
    email: str | None = Field(default=None, max_length=254)
    adult: bool | None = None
    active: bool | None = None
    totp_enabled: bool | None = None  # nur Abschalten (False) erlaubt


class BulkBody(BaseModel):
    role: str
    class_ids: list[str] | None = None


class ResetBody(BaseModel):
    disable_2fa: bool = False


class ChildrenBody(BaseModel):
    student_ids: list[str]


class TokenBody(BaseModel):
    name: str = Field(default="API-Token", max_length=100)
    expires_days: int | None = Field(default=None, ge=1, le=3650)


# --------------------------------------------------------------------------- Hilfen
def _get(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Benutzer nicht gefunden")
    return user


def _check_manage(actor: AuthUser, role: str) -> None:
    if "users.manage" not in actor.permissions or not can_manage_role(actor.role, role):
        raise HTTPException(403, f"Keine Berechtigung, Konten der Rolle „{role}“ zu verwalten")


def _check_self_or_manage(actor: AuthUser, target: User) -> None:
    if actor.id == target.id:
        return
    _check_manage(actor, target.role)


def _validate_links(role: str, teacher_id: str | None, student_id: str | None,
                    student_ids: list[str] | None) -> None:
    school = get_store().school
    if teacher_id and teacher_id not in school.index("teachers"):
        raise HTTPException(422, f"Lehrkraft {teacher_id} existiert nicht")
    students = school.index("students")
    if student_id and student_id not in students:
        raise HTTPException(422, f"Schüler {student_id} existiert nicht")
    unknown = [s for s in (student_ids or []) if s not in students]
    if unknown:
        raise HTTPException(422, f"Unbekannte Schüler: {', '.join(unknown[:10])}")
    if role == "schueler" and not student_id:
        pass  # Konto ohne Verknüpfung ist erlaubt (wird später zugeordnet)


def _with_class(items: list[dict]) -> list[dict]:
    students = get_store().school.index("students")
    for item in items:
        sid = item.get("student_id")
        if sid and sid in students:
            item["class"] = students[sid].class_id
    return items


# --------------------------------------------------------------------------- Konten
@router.get("/users")
def list_users(role: str | None = None, q: str | None = None, active: bool | None = None,
               class_id: str | None = None, limit: int = Query(0, ge=0, le=10000), offset: int = Query(0, ge=0),
               actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> list[dict]:
    """Konten der Rollen, die der Aufrufer verwalten darf (Filter: Rolle, Suche, aktiv, Klasse)."""
    roles = manageable_roles(actor.role)
    stmt = select(User).where(User.role.in_(roles)).order_by(User.role, User.username)
    if role:
        stmt = stmt.where(User.role == role)
    if active is not None:
        stmt = stmt.where(User.active.is_(active))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(User.username.ilike(like), User.display_name.ilike(like),
                              User.teacher_id.ilike(like), User.student_id.ilike(like)))
    if class_id:
        sids = [s.id for s in get_store().school.students if s.class_id == class_id]
        parent_ids = select(ParentLink.parent_user_id).where(ParentLink.student_id.in_(sids))
        stmt = stmt.where(or_(User.student_id.in_(sids), User.id.in_(parent_ids)))
    if offset:
        stmt = stmt.offset(offset)
    if limit:
        stmt = stmt.limit(limit)
    users = db.scalars(stmt).all()
    links: dict[int, list[str]] = {}
    for pid, sid in db.execute(select(ParentLink.parent_user_id, ParentLink.student_id).order_by(ParentLink.id)):
        links.setdefault(pid, []).append(sid)
    out = []
    for u in users:
        d = user_dict(db, u, children=False)
        if u.role == "eltern":
            d["student_ids"] = links.get(u.id, [])
        out.append(d)
    return _with_class(out)


def _check_user_limit(db: Session) -> None:
    """Lizenz: höchstens ``max_users`` aktive Konten (Testbetrieb ohne Lizenz: ``licensing.TRIAL_MAX_USERS``)."""
    from sqlalchemy import func

    from .. import licensing
    limit = licensing.user_limit()
    if limit is None:
        return
    active = db.scalar(select(func.count(User.id)).where(User.active.is_(True))) or 0
    if active >= limit:
        raise HTTPException(403, f"Die Lizenz erlaubt höchstens {limit} aktive Konten (aktiv: {active}).")


@router.post("/users", status_code=201)
def create(body: UserCreate, request: Request, actor: AuthUser = Depends(require("users.manage")),
           db: Session = Depends(get_db)) -> dict:
    """Konto anlegen. Ohne ``password`` wird ein Startpasswort erzeugt (``temp_password``)."""
    if body.role not in ROLES:
        raise HTTPException(422, f"Unbekannte Rolle: {body.role}")
    _check_manage(actor, body.role)
    _validate_links(body.role, body.teacher_id, body.student_id, body.student_ids)
    if body.password is not None:
        problems = password_problems(body.password, body.role, body.username)
        if problems:
            raise HTTPException(422, " ".join(problems))
    _check_user_limit(db)
    user, temp = create_user(db, username=body.username, role=body.role, display_name=body.display_name,
                             password=body.password, must_change_password=body.must_change_password,
                             teacher_id=body.teacher_id, student_id=body.student_id, site=body.site,
                             email=body.email, adult=body.adult)
    if body.role == "eltern" and body.student_ids:
        set_children(db, user, body.student_ids)
    audit(db, actor, "user.create", f"user:{user.id}", {"username": user.username, "role": user.role},
          ip=client_ip(request))
    letter_batch = None
    if temp:
        from ..letters import batch_from_passwords  # Zugangsbrief als PDF + Startpasswort aufbewahren (§11.3)
        letter_batch = batch_from_passwords(db, actor, {user.id: temp}, f"Neues Konto: {user.display_name}")
    db.commit()
    out = user_dict(db, user)
    if temp:
        out["temp_password"] = temp
        out["letter_batch"] = letter_batch
    return _with_class([out])[0]


@router.get("/users/{user_id}")
def get_user(user_id: int, actor: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    user = _get(db, user_id)
    _check_self_or_manage(actor, user)
    return _with_class([user_dict(db, user)])[0]


@router.patch("/users/{user_id}")
def patch_user(user_id: int, body: UserPatch, request: Request, actor: AuthUser = Depends(require("users.manage")),
               db: Session = Depends(get_db)) -> dict:
    """Konto ändern (Rolle, Verknüpfungen, aktiv/deaktiviert, Passwort setzen, 2FA abschalten)."""
    user = _get(db, user_id)
    _check_manage(actor, user.role)
    fields = body.model_dump(exclude_unset=True)
    changes: dict = {}
    if "role" in fields and fields["role"] != user.role:
        new_role = fields["role"]
        if new_role not in ROLES:
            raise HTTPException(422, f"Unbekannte Rolle: {new_role}")
        _check_manage(actor, new_role)
        if user.id == actor.id:
            raise HTTPException(409, "Die eigene Rolle kann nicht geändert werden")
        if user.role == "admin" and count_active_admins(db) <= 1:
            raise HTTPException(409, "Der letzte aktive Admin kann nicht herabgestuft werden")
        changes["role"] = [user.role, new_role]
        user.role = new_role
    _validate_links(user.role, fields.get("teacher_id"), fields.get("student_id"), fields.get("student_ids"))
    for key in ("display_name", "teacher_id", "student_id", "site", "email", "adult", "must_change_password"):
        if key in fields and getattr(user, key) != fields[key]:
            value = fields[key]
            if key in ("teacher_id", "student_id", "site", "email") and value == "":
                value = None
            if key in ("adult", "must_change_password") and value is None:
                continue
            changes[key] = value if key != "email" else "geändert"
            setattr(user, key, value)
    if "active" in fields and fields["active"] is not None and fields["active"] != user.active:
        if not fields["active"]:
            if user.id == actor.id:
                raise HTTPException(409, "Das eigene Konto kann nicht deaktiviert werden")
            if user.role == "admin" and count_active_admins(db) <= 1:
                raise HTTPException(409, "Der letzte aktive Admin kann nicht deaktiviert werden")
            revoke_sessions(db, user.id)
        user.active = bool(fields["active"])
        changes["active"] = user.active
    if fields.get("password"):
        problems = password_problems(fields["password"], user.role, user.username)
        if problems:
            raise HTTPException(422, " ".join(problems))
        user.password_hash = hash_password(fields["password"])
        user.must_change_password = bool(fields.get("must_change_password", True))
        revoke_sessions(db, user.id, except_session_id=actor.session_id if user.id == actor.id else None)
        changes["password"] = "gesetzt"
    if fields.get("totp_enabled") is False and user.totp_enabled:
        user.totp_enabled = False
        set_totp_secret(user, None)
        changes["totp_enabled"] = False
    elif fields.get("totp_enabled") is True and not user.totp_enabled:
        raise HTTPException(422, "2FA kann nur vom Benutzer selbst aktiviert werden")
    if body.student_ids is not None and user.role == "eltern":
        set_children(db, user, body.student_ids)
        changes["student_ids"] = body.student_ids
    if changes:
        audit(db, actor, "user.update", f"user:{user.id}", {"username": user.username, "changes": changes},
              ip=client_ip(request))
    db.commit()
    return _with_class([user_dict(db, user)])[0]


@router.delete("/users/{user_id}")
def remove_user(user_id: int, request: Request, actor: AuthUser = Depends(require("users.manage")),
                db: Session = Depends(get_db)) -> dict:
    """Konto endgültig löschen (DSGVO). Protokolle werden pseudonymisiert."""
    user = _get(db, user_id)
    _check_manage(actor, user.role)
    if user.id == actor.id:
        raise HTTPException(409, "Das eigene Konto kann nicht gelöscht werden")
    if user.role == "admin" and user.active and count_active_admins(db) <= 1:
        raise HTTPException(409, "Der letzte aktive Admin kann nicht gelöscht werden")
    info = {"username": user.username, "role": user.role}
    delete_user(db, user)
    audit(db, actor, "user.delete", f"user:{user_id}", info, ip=client_ip(request))
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, request: Request, body: ResetBody | None = None,
                   actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    """Setzt ein neues Startpasswort (Passwortwechsel-Zwang, alle Sitzungen beendet)."""
    user = _get(db, user_id)
    _check_manage(actor, user.role)
    temp = generate_password()
    user.password_hash = hash_password(temp, n=min(TEMP_PASSWORD_N, config.scrypt_n))
    user.must_change_password = True
    if body and body.disable_2fa:
        user.totp_enabled = False
        set_totp_secret(user, None)
    revoke_sessions(db, user.id)
    audit(db, actor, "user.reset_password", f"user:{user.id}",
          {"username": user.username, "disable_2fa": bool(body and body.disable_2fa)}, ip=client_ip(request))
    from ..letters import batch_from_passwords  # Zugangsbrief als PDF (§11.3)
    letter_batch = batch_from_passwords(db, actor, {user.id: temp}, f"Neues Startpasswort: {user.display_name}")
    db.commit()
    return {"temp_password": temp, "username": user.username, "display_name": user.display_name,
            "letter_batch": letter_batch}


@router.post("/users/bulk")
def bulk(body: BulkBody, request: Request, actor: AuthUser = Depends(require("users.manage")),
         db: Session = Depends(get_db)) -> dict:
    """Konten für alle Schüler/Lehrkräfte/Eltern ohne Konto (Zugangsbriefe: ``temp_password`` je Konto)."""
    if body.role not in ("schueler", "lehrer", "eltern"):
        raise HTTPException(422, "Massenanlage nur für Rollen schueler, lehrer oder eltern")
    _check_manage(actor, body.role)
    school = get_store().school
    if body.class_ids:
        known = {c.id for c in school.classes}
        unknown = [c for c in body.class_ids if c not in known]
        if unknown:
            raise HTTPException(422, f"Unbekannte Klassen: {', '.join(unknown)}")
    _check_user_limit(db)
    result = bulk_create(db, school, body.role, body.class_ids)
    audit(db, actor, "user.bulk_create", body.role,
          {"count": len(result["created"]), "skipped": result["skipped"], "class_ids": body.class_ids or []},
          ip=client_ip(request))
    from ..letters import batch_from_passwords  # Zugangsbriefe als PDF (§11.3)
    result["letter_batch"] = batch_from_passwords(
        db, actor, {c["id"]: c["temp_password"] for c in result["created"]},
        "Neue Konten: " + {"schueler": "Schüler/innen", "eltern": "Eltern", "lehrer": "Lehrkräfte"}[body.role] + (f" ({', '.join(body.class_ids[:5])})" if body.class_ids else ""))
    db.commit()
    return result


# --------------------------------------------------------------------------- Eltern ↔ Kinder
@router.get("/users/{user_id}/children")
def get_children(user_id: int, actor: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    user = _get(db, user_id)
    _check_self_or_manage(actor, user)
    ids = list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user.id)
                          .order_by(ParentLink.id)))
    students = get_store().school.index("students")
    return {"student_ids": ids,
            "students": [{"id": s, "name": students[s].name if s in students else None,
                          "class": students[s].class_id if s in students else None} for s in ids]}


@router.put("/users/{user_id}/children")
def put_children(user_id: int, body: ChildrenBody, request: Request,
                 actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    """Ersetzt die Kinder eines Elternkontos."""
    user = _get(db, user_id)
    _check_manage(actor, user.role)
    if user.role != "eltern":
        raise HTTPException(422, "Kinder können nur Elternkonten zugeordnet werden")
    _validate_links("eltern", None, None, body.student_ids)
    ids = set_children(db, user, body.student_ids)
    audit(db, actor, "user.children", f"user:{user.id}", {"student_ids": ids}, ip=client_ip(request))
    db.commit()
    return {"student_ids": ids}


@router.post("/users/{user_id}/children/{student_id}")
def add_child(user_id: int, student_id: str, request: Request, actor: AuthUser = Depends(require("users.manage")),
              db: Session = Depends(get_db)) -> dict:
    user = _get(db, user_id)
    _check_manage(actor, user.role)
    if user.role != "eltern":
        raise HTTPException(422, "Kinder können nur Elternkonten zugeordnet werden")
    _validate_links("eltern", None, None, [student_id])
    ids = list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user.id)))
    if student_id not in ids:
        db.add(ParentLink(parent_user_id=user.id, student_id=student_id))
        ids.append(student_id)
        audit(db, actor, "user.children", f"user:{user.id}", {"added": student_id}, ip=client_ip(request))
        db.commit()
    return {"student_ids": ids}


@router.delete("/users/{user_id}/children/{student_id}")
def remove_child(user_id: int, student_id: str, request: Request,
                 actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    user = _get(db, user_id)
    _check_manage(actor, user.role)
    link = db.scalar(select(ParentLink).where(ParentLink.parent_user_id == user.id,
                                              ParentLink.student_id == student_id))
    if link is not None:
        db.delete(link)
        audit(db, actor, "user.children", f"user:{user.id}", {"removed": student_id}, ip=client_ip(request))
        db.commit()
    ids = list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == user.id)))
    return {"student_ids": ids}


# --------------------------------------------------------------------------- Sitzungen
@router.get("/users/{user_id}/sessions")
def list_sessions(user_id: int, actor: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    user = _get(db, user_id)
    _check_self_or_manage(actor, user)
    rows = db.scalars(select(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at > utcnow())
                      .order_by(UserSession.last_seen.desc())).all()
    return [session_dict(s, actor.session_id) for s in rows]


@router.delete("/users/{user_id}/sessions")
def revoke_all_sessions(user_id: int, request: Request, actor: AuthUser = Depends(current_user),
                        db: Session = Depends(get_db)) -> dict:
    """Alle Sitzungen eines Kontos beenden (bei sich selbst: außer der aktuellen)."""
    user = _get(db, user_id)
    _check_self_or_manage(actor, user)
    n = revoke_sessions(db, user.id, except_session_id=actor.session_id if user.id == actor.id else None)
    audit(db, actor, "session.revoke_all", f"user:{user.id}", {"count": n}, ip=client_ip(request))
    db.commit()
    return {"revoked": n}


@router.delete("/sessions/{session_id}")
def revoke_session(session_id: int, request: Request, actor: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    sess = db.get(UserSession, session_id)
    if sess is None:
        raise HTTPException(404, "Sitzung nicht gefunden")
    owner = _get(db, sess.user_id)
    _check_self_or_manage(actor, owner)
    db.delete(sess)
    audit(db, actor, "session.revoke", f"user:{owner.id}", {"session_id": session_id}, ip=client_ip(request))
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- API-Tokens
def _issuing_token(request: Request, db: Session) -> ApiToken | None:
    """Das Bearer-Token, mit dem die Anfrage angemeldet ist (``None`` bei Sitzungs-Anmeldung)."""
    auth = request.headers.get("authorization", "")
    if auth[:7].lower() != "bearer ":
        return None
    return db.scalar(select(ApiToken).where(ApiToken.token_hash == hash_token(auth[7:].strip())))


@router.post("/users/{user_id}/api-token", status_code=201)
def create_api_token(user_id: int, request: Request, body: TokenBody | None = None,
                     actor: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Erzeugt ein API-Token (wird nur einmal im Klartext angezeigt) – nur für das **eigene** Konto (A-27: niemand
    meldet sich als jemand anderes an, U-02). Per API-Token angemeldet: Laufzeit ist Pflicht und reicht höchstens
    so weit wie die des ausstellenden Tokens."""
    user = _get(db, user_id)
    _check_self_or_manage(actor, user)
    if actor.id != user.id:
        raise HTTPException(403, "API-Tokens kann jede Person nur für das eigene Konto erzeugen.")
    body = body or TokenBody()
    now = utcnow()
    expires_at = now + timedelta(days=body.expires_days) if body.expires_days else None
    if actor.auth_method == "token":
        issuer = _issuing_token(request, db)
        if expires_at is None:
            raise HTTPException(422, "Bitte eine Laufzeit angeben (expires_days) – ein Token stellt kein "
                                     "unbefristetes Token aus.")
        if issuer is None or (issuer.expires_at is not None and expires_at > issuer.expires_at):
            left = max(0, (issuer.expires_at - now).days) if issuer is not None and issuer.expires_at else 0
            if left < 1:
                raise HTTPException(422, "Das verwendete Token läuft in weniger als einem Tag ab und kann kein "
                                         "weiteres Token ausstellen.")
            raise HTTPException(422, f"Die Laufzeit darf die des verwendeten Tokens nicht überschreiten "
                                     f"(höchstens {left} {'Tag' if left == 1 else 'Tage'}).")
    elif actor.auth_method != "session":
        raise HTTPException(403, "API-Tokens nur nach Anmeldung erzeugen.")
    token = "smt_" + new_token(32)
    row = ApiToken(user_id=user.id, name=body.name, token_hash=hash_token(token), prefix=token[:10],
                   created_at=now, expires_at=expires_at)
    db.add(row)
    db.flush()
    audit(db, actor, "api_token.create", f"user:{user.id}", {"token_id": row.id, "name": row.name},
          ip=client_ip(request))
    db.commit()
    return {**token_dict(row), "token": token}


@router.get("/users/{user_id}/api-tokens")
def list_api_tokens(user_id: int, actor: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    user = _get(db, user_id)
    _check_self_or_manage(actor, user)
    rows = db.scalars(select(ApiToken).where(ApiToken.user_id == user.id).order_by(ApiToken.id)).all()
    return [token_dict(t) for t in rows]


@router.delete("/api-tokens/{token_id}")
def delete_api_token(token_id: int, request: Request, actor: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> dict:
    row = db.get(ApiToken, token_id)
    if row is None:
        raise HTTPException(404, "Token nicht gefunden")
    _check_self_or_manage(actor, _get(db, row.user_id))
    db.delete(row)
    audit(db, actor, "api_token.delete", f"user:{row.user_id}", {"token_id": token_id}, ip=client_ip(request))
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------------------- Zugangsbriefe als PDF
class LetterIn(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    display_name: str = Field("", max_length=200)
    temp_password: str = Field(min_length=1, max_length=200)
    role: str = Field("", max_length=40)
    class_: str = Field("", max_length=40, alias="class")


class LettersBody(BaseModel):
    letters: list[LetterIn] = Field(min_length=1, max_length=2000)
    address: str = Field("", max_length=200)
    one_per_page: bool = True


@router.post("/users/letters.pdf")
def letters_pdf(body: LettersBody, request: Request, actor: AuthUser = Depends(require("users.manage")),
                db: Session = Depends(get_db)):
    """Zugangsbriefe direkt nach dem Anlegen/Zurücksetzen als PDF (die Startpasswörter kommen aus der Antwort des
    Anlegens im Browser – gespeichert wird nichts, nur protokolliert, für wie viele Konten ein PDF erzeugt wurde)."""
    from datetime import date

    from fastapi.responses import Response

    from ..files import content_disposition
    from ..pdf_simple import A4, MARGIN, Page, render
    from ..permissions import ROLE_LABELS

    school = get_store().school.settings.school_name or PRODUCT_NAME
    today = date.today().strftime("%d.%m.%Y")
    pages: list[Page] = []
    page = None
    for i, letter in enumerate(body.letters):
        if page is None or body.one_per_page or page.y < 300:
            page = Page()
            pages.append(page)
        elif i:
            page.line(MARGIN, page.y + 6, A4[0] - MARGIN, page.y + 6, 0.4, gray=0.6)
            page.y -= 24
        draw_logo_simple(page, MARGIN, page.y + 13, 18)
        page.text(MARGIN + 24, page.y, school, 14, bold=True)
        page.text(A4[0] - MARGIN - 70, page.y, today, 9, gray=0.35)
        page.y -= 30
        page.para(f"Ihre Zugangsdaten zum {PRODUCT_NAME}", 13, bold=True)
        who = letter.display_name or letter.username
        extra = (f" (Klasse {letter.class_})" if letter.class_ else "") + (
            f" – {ROLE_LABELS.get(letter.role, letter.role)}" if letter.role else "")
        page.para(f"für {who}{extra}", 10, gap=10)
        page.field("Adresse", body.address or "")
        page.field("Benutzername", letter.username, size=12)
        page.field("Startpasswort", letter.temp_password, size=12)
        page.para("Bei der ersten Anmeldung werden Sie aufgefordert, ein eigenes Passwort festzulegen. Bitte bewahren "
                  "Sie diesen Brief sicher auf und geben Sie Ihre Zugangsdaten nicht weiter. Auf dem Handy lässt sich "
                  "die Seite über „Zum Startbildschirm hinzufügen“ wie eine App nutzen.", 9, gap=18, gray=0.2)
    audit(db, actor, "user.letters_pdf", "users", {"count": len(body.letters)}, ip=client_ip(request))
    db.commit()
    pdf = render(pages, "Zugangsbriefe")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": content_disposition(f"Zugangsbriefe-{date.today().isoformat()}.pdf"),
                             "Cache-Control": "no-store"})


# --------------------------------------------------------------------------- Demo-Zugänge (Vorführ-Instanz)
class DemoAccessBody(BaseModel):
    name: str = Field(min_length=1, max_length=60, description="Für wen (z. B. „Gesamtschule Musterstadt“)")
    kinds: list[str] = Field(min_length=1, max_length=20)


@router.get("/demo-access")
def demo_access_info(actor: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    """Ausgegebene Demo-Zugänge und mögliche Arten (nur in der Vorführ-Instanz, nur Inhaber/Admin)."""
    from ..demo_loader import DEMO_ACCESS_KINDS, DEMO_ACCESS_PREFIX
    _demo_issuer(actor)
    users = db.scalars(select(User).where(User.username.like(f"{DEMO_ACCESS_PREFIX}%")).order_by(User.id)).all()
    return {"kinds": [{"kind": k, "label": label} for k, (_, label) in DEMO_ACCESS_KINDS.items()],
            "issued": [{"id": u.id, "username": u.username, "display_name": u.display_name, "role": u.role,
                        "active": u.active, "last_login": iso(u.last_login)}
                       for u in users]}


def _demo_issuer(actor: AuthUser) -> None:
    from ..demo_loader import DEMO_ACCESS_PREFIX
    if not config.demo_public:
        raise HTTPException(404, "Demo-Zugänge gibt es nur in der Vorführ-Instanz")
    if actor.role != "admin" or actor.username != config.admin_user or actor.username.startswith(DEMO_ACCESS_PREFIX):
        raise HTTPException(403, "Demo-Zugänge gibt nur der Inhaber der Vorführ-Instanz aus")


@router.post("/demo-access", status_code=201)
def demo_access(body: DemoAccessBody, request: Request, actor: AuthUser = Depends(require("users.manage")),
                db: Session = Depends(get_db)) -> dict:
    """Gibt einen Demo-Zugang aus: je gewählter Art ein Konto ``dz-<name>-<art>`` mit Zufallspasswort, verknüpft wie
    das passende Vorlage-Konto (gleiche simulierte Personen). Die Passwörter stehen nur in dieser Antwort
    (→ Zugangsbriefe/PDF). Ausgegebene Zugänge überstehen das nächtliche Neuaufsetzen (``reset.sh``)."""
    import re
    import unicodedata

    from ..demo_loader import DEMO_ACCESS_KINDS, DEMO_ACCESS_PREFIX
    _demo_issuer(actor)
    unknown = [k for k in body.kinds if k not in DEMO_ACCESS_KINDS]
    if unknown:
        raise HTTPException(422, f"Unbekannte Art: {', '.join(unknown)}")
    slug = unicodedata.normalize("NFKD", body.name).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "", slug)[:16] or "demo"
    letters = []
    for kind in dict.fromkeys(body.kinds):
        template_name, label = DEMO_ACCESS_KINDS[kind]
        tpl = db.scalar(select(User).where(User.username == template_name))
        if tpl is None:
            raise HTTPException(409, f"Vorlage-Konto {template_name!r} fehlt – Demo-Schule noch nicht fertig geladen?")
        base = f"{DEMO_ACCESS_PREFIX}{slug}-{kind.replace('_', '')}"
        username, n = base, 1
        while db.scalar(select(User.id).where(User.username == username)) is not None:
            n += 1
            username = f"{base}{n}"
        temp = generate_password()
        user, _ = create_user(db, username=username, role=tpl.role, display_name=f"{label} – {body.name.strip()}",
                              password=temp, must_change_password=False, teacher_id=tpl.teacher_id,
                              student_id=tpl.student_id, site=tpl.site, adult=bool(tpl.adult))
        children = list(db.scalars(select(ParentLink.student_id).where(ParentLink.parent_user_id == tpl.id)))
        if children:
            set_children(db, user, children)
        letters.append({"username": username, "display_name": user.display_name, "temp_password": temp,
                        "role": user.role})
    audit(db, actor, "user.demo_access", "users", {"name": body.name, "kinds": list(dict.fromkeys(body.kinds)),
                                                     "usernames": [x["username"] for x in letters]},
          ip=client_ip(request))
    db.commit()
    return {"letters": letters}

