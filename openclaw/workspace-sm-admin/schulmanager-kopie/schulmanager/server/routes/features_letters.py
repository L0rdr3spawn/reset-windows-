"""Zugangsbriefe (§11.3): Stapel mit Startpasswörtern als PDF/ZIP herunterladen oder per E-Mail versenden.

* ``POST /letters/batches`` ``{user_ids?, student_ids?, parents?, create_missing?}`` – neue Startpasswörter für
  vorhandene Konten (wie ``reset_password``); über ``student_ids`` die Schülerkonten dieser Schüler/innen, mit
  ``parents`` zusätzlich deren Elternkonten, mit ``create_missing`` fehlende Konten neu anlegen → ``{id, count,
  expires_at, reset, created}``
* ``GET /letters/batches/{id}`` – Metadaten + Einträge **ohne** Passwörter (``has_email``, ``parents_with_email`` …)
* ``GET /letters/batches/{id}/pdf`` (Sammel-PDF, eine Seite je Brief), ``…/zip`` (Einzel-PDFs),
  ``…/entries/{user_id}.pdf`` (ein Brief)
* ``POST /letters/batches/{id}/send`` ``{user_ids?, to: student|parents|both}`` – E-Mail je Person mit ihrem PDF
* ``GET /users/{id}/password`` – Startpasswort gespeichert? ``POST /users/{id}/password`` ``{mode: "new"|"set",
  password?, must_change?}`` – ``new``: **neues** Einmal-/Startpasswort erzeugen (Passwortwechsel-Zwang, Sitzungen
  beendet, Brief-Stapel mit PDF; das Passwort steht **einmalig** als ``temp_password`` in der Antwort, ``no-store``);
  Startpasswörter werden nicht aufbewahrt (nur Hash + Frist, S-06): „altes Startpasswort wiederherstellen“ gibt es nicht
  mehr, stattdessen ``new``;
  ``set``: selbst gewähltes Passwort setzen (Passwortregeln; „beim nächsten Anmelden ändern“, Standard an)
* ``GET /classes/{id}/accounts`` – Konten der Schüler/innen einer Klasse (für Klassenseite/Klassenleitung)

Rechte: ``users.manage`` und für jedes Konto ``_check_manage`` (Sekretariat nur Schüler/Eltern); Zurücksetzen und
eigene Stapel zusätzlich mit ``passwords.reset`` (Lehrkräfte: Scope ``class_teacher`` – nur Schülerkonten der
Klassen, die sie leiten; nie Personal/Admins). Einen Stapel sieht nur die anlegende Person (oder die Rolle admin);
fremde Stapel → 404, abgelaufene → 410. Jeder Download/Versand wird protokolliert (nie mit Passwort). Antworten mit
``Cache-Control: no-store``.
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from schulmanager.server import letters
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import User
from schulmanager.server.deps import AuthUser, client_ip, current_user, require
from schulmanager.server.feature_models.contact import AuthCode

log = logging.getLogger("schulmanager.letters")
router = APIRouter(tags=["Zugangsbriefe"])

MAX_ACCOUNTS = 500
NO_STORE = {"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache", "X-Content-Type-Options": "nosniff"}


class BatchIn(BaseModel):
    user_ids: list[int] = Field(default_factory=list, max_length=5000)
    student_ids: list[str] = Field(default_factory=list, max_length=5000)
    parents: bool = False
    create_missing: bool = False


class PasswordIn(BaseModel):
    mode: Literal["new", "set"]
    password: Optional[str] = Field(None, max_length=256)
    must_change: bool = True


class SendIn(BaseModel):
    user_ids: Optional[list[int]] = Field(None, max_length=5000)
    to: Literal["student", "parents", "both"] = "student"


# =================================================================== Hilfen
def _check(actor: AuthUser, role: str) -> None:
    from .users import _check_manage

    _check_manage(actor, role)


def resetter(actor: AuthUser = Depends(current_user)) -> AuthUser:
    """``users.manage`` oder ``passwords.reset`` (Datenumfang prüft :func:`letters.can_reset` je Konto)."""
    if not ({"users.manage", "passwords.reset"} & set(actor.permissions or ())):
        raise HTTPException(403, "Keine Berechtigung")
    return actor


def _batch(db: Session, actor: AuthUser, batch_id: str):
    batch, entries = letters.load_batch(db, actor, batch_id)
    return batch, letters.visible_entries(actor, entries)


def _file(data: bytes, filename: str, media_type: str, inline: bool = False) -> Response:
    disp = "inline" if inline else "attachment"
    return Response(content=data, media_type=media_type,
                    headers={**NO_STORE, "Content-Disposition": f'{disp}; filename="{filename}"'})


def _batch_filename(batch, ext: str) -> str:
    base = letters.ascii_part(batch.title or "")[:60] or "Stapel"
    return f"Zugangsbriefe_{base}.{ext}"


def _audit(db: Session, actor: AuthUser, request: Request, action: str, batch_id: str, details: dict) -> None:
    audit(db, actor, action, f"letter_batch:{batch_id}", details, ip=client_ip(request))
    db.commit()


# =================================================================== Stapel anlegen
@router.post("/letters/batches", status_code=201)
def create_batch(body: BatchIn, request: Request, actor: AuthUser = Depends(require("users.manage")),
                 db: Session = Depends(get_db)) -> dict:
    """Neue Startpasswörter (Passwortwechsel-Zwang, Sitzungen beendet) und ein Brief-Stapel dazu."""
    from schulmanager.server.store import get_store

    user_ids = list(dict.fromkeys(body.user_ids))
    student_ids = list(dict.fromkeys(s.strip() for s in body.student_ids if s and s.strip()))
    if not user_ids and not student_ids:
        raise HTTPException(422, "Bitte mindestens ein Konto oder eine Schülerin/einen Schüler auswählen")
    if len(user_ids) + len(student_ids) > MAX_ACCOUNTS:
        raise HTTPException(422, f"Höchstens {MAX_ACCOUNTS} Konten je Stapel")
    users: dict[int, User] = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids)))}
    missing = [i for i in user_ids if i not in users]
    if missing:
        raise HTTPException(404, f"Konto nicht gefunden: {', '.join(map(str, missing[:10]))}")
    school = get_store().school
    plan: list[dict] = []
    plan_students: dict[int, dict] = {}
    if student_ids:
        idx = school.index("students")
        unknown = [s for s in student_ids if s not in idx]
        if unknown:
            raise HTTPException(422, f"Unbekannte Schüler/innen: {', '.join(unknown[:10])}")
        accounts = db.scalars(select(User).where(User.role == "schueler", User.student_id.in_(student_ids))).all()
        have = {u.student_id for u in accounts}
        for u in accounts:
            users.setdefault(u.id, u)
        parents = letters._parents_of(db, student_ids) if body.parents else {}
        for plist in parents.values():
            for u in plist:
                users.setdefault(u.id, u)
        if body.create_missing:
            infos = []
            for i, sid in enumerate(student_ids):
                st = idx[sid]
                first, last = letters.split_name(st.name)
                info = {"index": i, "student_id": sid, "name": st.name, "first_name": first, "last_name": last,
                        "class_id": st.class_id, "class_name": st.class_id}
                plan_students[i] = info
                infos.append(info)
            no_account = [s for s in infos if s["student_id"] not in have]
            no_parent = [s for s in infos if body.parents and s["student_id"] not in parents]
            plan += letters.plan_accounts(db, no_account, student_accounts=True, parent_accounts=False)[0]
            plan += letters.plan_accounts(db, no_parent, student_accounts=False, parent_accounts=True)[0]
    if len(users) + len(plan) > MAX_ACCOUNTS:
        raise HTTPException(422, f"Höchstens {MAX_ACCOUNTS} Konten je Stapel")
    for u in users.values():
        _check(actor, u.role)
    for role in {p["role"] for p in plan}:
        _check(actor, role)
    if not users and not plan:
        raise HTTPException(422, "Zu den ausgewählten Schüler/innen gibt es keine Konten")
    passwords = letters.reset_passwords(db, users.values())
    entries = letters.entries_for_passwords(db, passwords, school=school)
    created: list[dict] = []
    if plan:
        created, _ = letters.create_planned(db, plan, plan_students)
    classes = {e.get("class_id") for e in entries + created if e.get("class_id")}
    classes |= {k.get("class_id") for e in entries + created for k in e.get("children") or [] if k.get("class_id")}
    n = len(entries) + len(created)
    title = (f"Klasse {next(iter(classes))} – neue Zugangsdaten" if len(classes) == 1
             else f"Neue Zugangsdaten ({n} {'Konto' if n == 1 else 'Konten'})")
    batch = letters.create_batch(db, actor, entries + created, title)
    audit(db, actor, "letters.batch_create", f"letter_batch:{batch.id}",
          {"count": batch.count, "reset_user_ids": sorted(passwords), "created_user_ids": [e["user_id"] for e in created]},
          ip=client_ip(request))
    db.commit()
    return {**letters.batch_ref(batch), "reset": len(passwords), "created": len(created), "title": batch.title}


# =================================================================== Lesen
@router.get("/letters/batches/{batch_id}")
def get_batch(batch_id: str, response: Response, actor: AuthUser = Depends(resetter),
              db: Session = Depends(get_db)) -> dict:
    """Stapel ohne Passwörter: Einträge mit E-Mail-Status und Anmelde-Hinweisen."""
    from schulmanager.server import auth_messages

    batch, entries = _batch(db, actor, batch_id)
    response.headers.update(NO_STORE)
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_([e["user_id"] for e in entries])))}
    parents = letters._parents_of(db, [e["student_id"] for e in entries if e.get("role") == "schueler" and e.get("student_id")])
    creator = db.get(User, batch.created_by) if batch.created_by else None
    used: set[str] = set()
    out = []
    for e in entries:
        user = users.get(e["user_id"])
        info = letters.policy_info(db, user)
        hints = letters.letter_hints(e, info, formal=letters._formal(e))
        adult = letters.is_adult_student(e, user)
        # Volljährige: Versand nie über die Eltern (siehe letters.send_entries)
        plist = parents.get(e.get("student_id") or "", []) if e.get("role") == "schueler" and not adult else []
        out.append({"user_id": e["user_id"], "username": e["username"], "display_name": e["display_name"],
                    "role": e["role"], "class_id": e.get("class_id"), "class_name": e.get("class_name"),
                    "student_id": e.get("student_id"), "adult": adult,
                    "children": [{"student_id": k["student_id"], "name": k["name"], "class_id": k.get("class_id")}
                                 for k in e.get("children") or []],
                    "exists": user is not None, "has_email": bool(user and user.email),
                    "parents": len(plist), "parents_with_email": sum(1 for p in plist if p.email),
                    "password_printed": hints["print_password"],
                    "login_methods": [letters._provider_label(p) for p in info["providers"]] if not info["password"]
                    else [],
                    "required_links": [letters._provider_label(p) for p in info["required"]],
                    "filename": letters.entry_filename(e, used), "title": letters.letter_title(e)})
    remaining = max(0, int((batch.expires_at - utcnow()).total_seconds()))
    return {"id": batch.id, "title": batch.title, "count": len(out), "created_at": iso(batch.created_at),
            "expires_at": iso(batch.expires_at), "expires_in": remaining,
            "created_by": {"id": creator.id, "name": creator.display_name or creator.username} if creator else None,
            "login_url": letters.login_url(), "email_available": bool(auth_messages.email_available()),
            "entries": out}


@router.get("/letters/batches/{batch_id}/pdf")
def batch_pdf(batch_id: str, request: Request, inline: bool = Query(False), actor: AuthUser = Depends(resetter),
              db: Session = Depends(get_db)) -> Response:
    """Sammel-PDF (eine Seite je Brief)."""
    batch, entries = _batch(db, actor, batch_id)
    if not entries:
        raise HTTPException(404, "Der Stapel enthält keine Briefe")
    data = letters.render_letters(db, entries, created_at=batch.created_at, title=batch.title or "Zugangsdaten")
    _audit(db, actor, request, "letters.download", batch.id, {"kind": "pdf", "count": len(entries)})
    return _file(data, _batch_filename(batch, "pdf"), "application/pdf", inline)


@router.get("/letters/batches/{batch_id}/zip")
def batch_zip(batch_id: str, request: Request, actor: AuthUser = Depends(resetter),
              db: Session = Depends(get_db)) -> Response:
    """ZIP mit einem PDF je Person (Dateinamen wie ``5a_Mustermann_Max.pdf``)."""
    batch, entries = _batch(db, actor, batch_id)
    if not entries:
        raise HTTPException(404, "Der Stapel enthält keine Briefe")
    data = letters.zip_letters(db, entries, created_at=batch.created_at)
    _audit(db, actor, request, "letters.download", batch.id, {"kind": "zip", "count": len(entries)})
    return _file(data, _batch_filename(batch, "zip"), "application/zip")


@router.get("/letters/batches/{batch_id}/entries/{user_id}.pdf")
def entry_pdf(batch_id: str, user_id: int, request: Request, inline: bool = Query(False),
              actor: AuthUser = Depends(resetter), db: Session = Depends(get_db)) -> Response:
    """Ein einzelner Brief."""
    batch, entries = _batch(db, actor, batch_id)
    used: set[str] = set()
    for e in entries:
        name = letters.entry_filename(e, used)
        if e["user_id"] == user_id:
            data = letters.render_letters(db, [e], created_at=batch.created_at, title=letters.letter_title(e))
            _audit(db, actor, request, "letters.download", batch.id, {"kind": "entry", "user_id": user_id})
            return _file(data, name, "application/pdf", inline)
    raise HTTPException(404, "Kein Brief für dieses Konto im Stapel")


# =================================================================== Versand
@router.post("/letters/batches/{batch_id}/send")
def send_batch(batch_id: str, body: SendIn, request: Request, actor: AuthUser = Depends(resetter),
               db: Session = Depends(get_db)) -> dict:
    """E-Mail je Person mit ihrem Brief (PDF) im Anhang. ``to``: ``student`` = an das Konto selbst, ``parents`` =
    an die verknüpften Elternkonten (bei Elternbriefen: an das Elternkonto), ``both`` = beides."""
    from schulmanager.server import auth_messages

    batch, entries = _batch(db, actor, batch_id)
    if body.user_ids is not None:
        wanted = set(body.user_ids)
        if wanted - {e["user_id"] for e in entries}:
            raise HTTPException(422, "Nicht alle ausgewählten Konten gehören zu diesem Stapel")
        entries = [e for e in entries if e["user_id"] in wanted]
    result = letters.send_entries(db, entries, to=body.to, created_at=batch.created_at)
    _audit(db, actor, request, "letters.send", batch.id,
           {"to": body.to, "sent": len(result["sent"]), "no_address": len(result["no_address"]),
            "unavailable": len(result["unavailable"]), "user_ids": [r["user_id"] for r in result["sent"]]})
    letters.kick_outbox()
    return {**result, "email_available": bool(auth_messages.email_available())}


# =================================================================== Passwort zurücksetzen (Verwaltung/Klassenleitung)
@router.get("/users/{user_id}/password")
def password_info(user_id: int, actor: AuthUser = Depends(resetter), db: Session = Depends(get_db)) -> dict:
    """Hat das Konto noch ein Startpasswort (mit Frist)? Das Passwort selbst wird nie aufbewahrt."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Benutzer nicht gefunden")
    letters.check_reset(actor, user)
    row = letters.initial_password_info(db, user.id)
    return {"user_id": user.id, "initial_pending": row is not None,
            "initial_expires_at": iso(row.expires_at) if row else None,
            "initial_expired": bool(row and row.expires_at <= utcnow()),
            "must_change_password": bool(user.must_change_password)}


@router.post("/users/{user_id}/password")
def set_password(user_id: int, body: PasswordIn, request: Request, response: Response,
                 actor: AuthUser = Depends(resetter), db: Session = Depends(get_db)) -> dict:
    """``new``: neues Einmalpasswort (wird einmalig zurückgegeben) + Brief als PDF, Passwortwechsel-Zwang;
    ``set``: selbst gewähltes Passwort (Passwortregeln, ``must_change`` = beim nächsten Anmelden ändern).
    Beides beendet alle Sitzungen des Kontos."""
    from schulmanager.server.accounts import revoke_sessions
    from schulmanager.server.security import hash_password, password_problems

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Benutzer nicht gefunden")
    letters.check_reset(actor, user)
    if user.id == actor.id:
        raise HTTPException(409, "Das eigene Passwort bitte im Profil ändern")
    out: dict = {"user_id": user.id, "mode": body.mode}
    response.headers.update(NO_STORE)
    if body.mode == "new":
        temp = letters.reset_passwords(db, [user])[user.id]   # Passwortwechsel-Zwang + alle Sitzungen beendet
        batch = letters.create_batch(db, actor, letters.entries_for_passwords(db, {user.id: temp}),
                                     f"Neues Einmalpasswort: {user.display_name}")
        audit(db, actor, "user.password_new", f"user:{user.id}",
              {"username": user.username, "letter_batch": batch.id}, ip=client_ip(request))
        out["letter_batch"] = letters.batch_ref(batch)
        out["temp_password"] = temp
    else:
        pw = body.password or ""
        problems = password_problems(pw, user.role, user.username)
        if problems:
            raise HTTPException(422, " ".join(problems))
        user.password_hash = hash_password(pw)
        user.must_change_password = bool(body.must_change)
        letters.clear_initial(db, user.id)
        revoke_sessions(db, user.id)
        audit(db, actor, "user.password_set", f"user:{user.id}",
              {"username": user.username, "must_change": bool(body.must_change)}, ip=client_ip(request))
    # offene „Passwort vergessen“-Codes/-Links entwerten – sie dürfen das neue Passwort nicht überschreiben
    db.execute(update(AuthCode).where(AuthCode.user_id == user.id, AuthCode.purpose.in_(("reset", "reset_token")),
                                      AuthCode.used_at.is_(None)).values(used_at=utcnow()))
    db.commit()
    out["must_change_password"] = bool(user.must_change_password)
    return out


@router.get("/classes/{class_id}/accounts")
def class_accounts(class_id: str, response: Response, actor: AuthUser = Depends(resetter),
                   db: Session = Depends(get_db)) -> dict:
    """Konten der Schüler/innen einer Klasse (und mit ``users.manage`` ihrer Eltern) – ohne Passwörter."""
    from schulmanager.server.permissions import can_manage_role
    from schulmanager.server.store import get_store

    school = get_store().school
    cls = school.index("classes").get(class_id)
    if cls is None:
        raise HTTPException(404, f"Klasse „{class_id}“ nicht gefunden")
    manage = "users.manage" in actor.permissions
    led = letters.led_student_ids(actor, school) if not manage else set()
    students = sorted((s for s in school.students if s.class_id == class_id), key=lambda s: (s.name.lower(), s.id))
    leads = bool(actor.teacher_id) and cls.class_teacher == actor.teacher_id   # ohne Kürzel nie Klassenleitung
    if not manage and not any(s.id in led for s in students) and not leads:
        raise HTTPException(403, "Nur die Klassenleitung oder die Verwaltung sieht die Konten dieser Klasse")
    sids = [s.id for s in students]
    accounts: dict[str, User] = {}
    for u in db.scalars(select(User).where(User.role == "schueler", User.student_id.in_(sids)).order_by(User.id)):
        accounts.setdefault(u.student_id, u)
    parents = letters._parents_of(db, sids) if manage and can_manage_role(actor.role, "eltern") else {}
    initial_rows: dict[int, object] = {}
    for uid in [u.id for u in accounts.values()] + [p.id for pl in parents.values() for p in pl]:
        row = letters.initial_password_info(db, uid)
        if row is not None:
            initial_rows[uid] = row
    initial = set(initial_rows)

    def acc(u: User) -> dict:
        return {"user_id": u.id, "username": u.username, "display_name": u.display_name, "role": u.role,
                "active": bool(u.active), "must_change_password": bool(u.must_change_password),
                "last_login": iso(u.last_login), "has_email": bool(u.email), "has_initial": u.id in initial,
                "initial_expires_at": iso(initial_rows[u.id].expires_at) if u.id in initial_rows else None,
                "can_reset": letters.can_reset(actor, u.role, u.student_id, led=led)}

    response.headers.update(NO_STORE)
    return {"class_id": class_id, "can_manage": manage and can_manage_role(actor.role, "schueler"),
            "students": [{"student_id": s.id, "name": s.name, "birth_date": s.birth_date,
                          "account": acc(accounts[s.id]) if s.id in accounts else None,
                          "parents": [acc(p) for p in parents.get(s.id, [])]} for s in students]}
