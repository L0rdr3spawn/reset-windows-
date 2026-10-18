"""Rollen & Rechte: Katalog, wirksame Matrix, Änderungen je Rolle, Schulzweige und Zuordnungen.

* ``GET  /rights`` – Katalog, Rollen, Matrix (Standard vs. wirksam), feste Regeln.
* ``PUT  /rights/roles/{role}`` / ``POST /rights/roles/{role}/reset`` – Rechte einer Rolle ändern/zurücksetzen.
* ``GET/POST/PUT/DELETE /rights/branches`` – Schulzweige (Abteilungsleitung).
* ``GET /rights/assignments`` / ``PUT /rights/assignments/{user_id}`` – Zweige bzw. Kinder (Schulbegleitung) zuordnen.
* ``GET /rights/me`` – „Ihre Rolle“ inkl. abgeleiteter Titel (Klassenleitung, Zweig).
Jede Änderung wird im Audit-Protokoll festgehalten.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import rights
from ..audit import audit
from ..db import get_db
from ..db_models import Branch, User, UserBranch
from ..deps import AuthUser, client_ip, current_user, require
from ..permissions import ROLE_LABELS, ROLES, can_manage_role
from ..store import get_store

router = APIRouter(tags=["Rollen & Rechte"])
_view = require("rights.manage", "users.manage", "audit.read", any_of=True)


class PermChange(BaseModel):
    granted: bool = True
    scope: str | None = Field(None, max_length=30)   # None = Standard der Rolle, "all" = uneingeschränkt


class RoleChanges(BaseModel):
    # ``null`` als Wert = Recht dieser Rolle auf Standard zurücksetzen
    permissions: dict[str, PermChange | None] = Field(default_factory=dict)


class BranchIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    sites: list[str] = Field(default_factory=list, max_length=100)
    grades: list[int] = Field(default_factory=list, max_length=30)
    class_ids: list[str] = Field(default_factory=list, max_length=500)


class AssignmentIn(BaseModel):
    branch_ids: list[int] | None = None
    student_ids: list[str] | None = None


@router.get("/rights")
def get_rights(_user: AuthUser = Depends(_view), db: Session = Depends(get_db)) -> dict:
    """Katalog, Rollen und wirksame Matrix. ``cells[rolle][recht]``: ``granted``, ``scope``, ``locked``, ``changed`` …"""
    return rights.describe(db)


@router.put("/rights/roles/{role}")
def put_role(role: str, body: RoleChanges, request: Request, actor: AuthUser = Depends(require("rights.manage")),
             db: Session = Depends(get_db)) -> dict:
    if role not in ROLES:
        raise HTTPException(404, f"Unbekannte Rolle: {role}")
    changes: dict[str, Any] = {p: (c.model_dump() if c is not None else None) for p, c in body.permissions.items()}
    try:
        diff = rights.apply_changes(db, role, changes, actor.username)
    except ValueError as e:
        db.rollback()
        raise HTTPException(422, str(e)) from None
    audit(db, actor, "rights.update", f"role:{role}", {"role": role, "changes": diff}, ip=client_ip(request))
    db.commit()
    return rights.describe(db)


@router.post("/rights/roles/{role}/reset")
def reset_role(role: str, request: Request, actor: AuthUser = Depends(require("rights.manage")),
               db: Session = Depends(get_db)) -> dict:
    if role not in ROLES:
        raise HTTPException(404, f"Unbekannte Rolle: {role}")
    n = rights.reset_role(db, role)
    audit(db, actor, "rights.reset", f"role:{role}", {"role": role, "removed": n}, ip=client_ip(request))
    db.commit()
    return rights.describe(db)


# ------------------------------------------------------------------------------------------ Zweige
def _check_branch(body: BranchIn) -> BranchIn:
    school = get_store().school
    sites, classes = school.index("sites"), school.index("classes")
    bad_site = [s for s in body.sites if s not in sites]
    bad_cls = [c for c in body.class_ids if c not in classes]
    if bad_site:
        raise HTTPException(422, f"Unbekannter Standort: {bad_site[0]}")
    if bad_cls:
        raise HTTPException(422, f"Unbekannte Klasse: {bad_cls[0]}")
    body.name = body.name.strip()
    return body


@router.get("/rights/branches")
def list_branches(_user: AuthUser = Depends(_view), db: Session = Depends(get_db)) -> list[dict]:
    out = []
    for b in db.scalars(select(Branch).order_by(Branch.name)):
        d = rights.branch_dict(b)
        d["user_ids"] = list(db.scalars(select(UserBranch.user_id).where(UserBranch.branch_id == b.id)))
        out.append(d)
    return out


@router.post("/rights/branches", status_code=201)
def create_branch(body: BranchIn, request: Request, actor: AuthUser = Depends(require("rights.manage")),
                  db: Session = Depends(get_db)) -> dict:
    body = _check_branch(body)
    b = Branch(name=body.name, sites=body.sites, grades=body.grades, class_ids=body.class_ids)
    db.add(b)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ein Zweig mit diesem Namen existiert bereits") from None
    audit(db, actor, "branch.create", f"branch:{b.id}", rights.branch_dict(b), ip=client_ip(request))
    db.commit()
    return rights.branch_dict(b)


@router.put("/rights/branches/{branch_id}")
def update_branch(branch_id: int, body: BranchIn, request: Request,
                  actor: AuthUser = Depends(require("rights.manage")), db: Session = Depends(get_db)) -> dict:
    b = db.get(Branch, branch_id)
    if b is None:
        raise HTTPException(404, "Zweig nicht gefunden")
    body = _check_branch(body)
    b.name, b.sites, b.grades, b.class_ids = body.name, body.sites, body.grades, body.class_ids
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ein Zweig mit diesem Namen existiert bereits") from None
    audit(db, actor, "branch.update", f"branch:{b.id}", rights.branch_dict(b), ip=client_ip(request))
    db.commit()
    return rights.branch_dict(b)


@router.delete("/rights/branches/{branch_id}", status_code=204)
def delete_branch(branch_id: int, request: Request, actor: AuthUser = Depends(require("rights.manage")),
                  db: Session = Depends(get_db)) -> None:
    b = db.get(Branch, branch_id)
    if b is None:
        raise HTTPException(404, "Zweig nicht gefunden")
    db.execute(delete(UserBranch).where(UserBranch.branch_id == b.id))
    audit(db, actor, "branch.delete", f"branch:{b.id}", {"name": b.name}, ip=client_ip(request))
    db.delete(b)
    db.commit()


# ------------------------------------------------------------------------------------ Zuordnungen
_LINK_ROLES = ("abteilungsleitung", "schulbegleitung")


@router.get("/rights/assignments")
def list_assignments(actor: AuthUser = Depends(require("rights.manage", "users.manage", any_of=True)),
                     db: Session = Depends(get_db)) -> list[dict]:
    """Konten mit Zuordnung: Abteilungsleitung (Zweige) und Schulbegleitung (begleitete Kinder)."""
    students = get_store().school.index("students")
    out = []
    for u in db.scalars(select(User).where(User.role.in_(_LINK_ROLES)).order_by(User.role, User.username)):
        if not (actor.has("rights.manage") or can_manage_role(actor.role, u.role)):
            continue
        ids = rights.user_children(db, u.id) if u.role == "schulbegleitung" else []
        out.append({"id": u.id, "username": u.username, "display_name": u.display_name, "role": u.role,
                    "role_label": ROLE_LABELS[u.role], "active": bool(u.active),
                    "branch_ids": [b["id"] for b in rights.user_branches(db, u.id)] if u.role == "abteilungsleitung" else [],
                    "student_ids": ids,
                    "students": [{"id": s, "name": students[s].name, "class_id": students[s].class_id}
                                 for s in ids if s in students]})
    return out


@router.put("/rights/assignments/{user_id}")
def put_assignment(user_id: int, body: AssignmentIn, request: Request,
                   actor: AuthUser = Depends(require("rights.manage", "users.manage", any_of=True)),
                   db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None or user.role not in _LINK_ROLES:
        raise HTTPException(404, "Konto nicht gefunden oder ohne Zuordnung")
    if not (actor.has("rights.manage") or (actor.has("users.manage") and can_manage_role(actor.role, user.role))):
        raise HTTPException(403, "Keine Berechtigung für dieses Konto")
    details: dict[str, Any] = {"username": user.username, "role": user.role}
    if user.role == "abteilungsleitung" and body.branch_ids is not None:
        try:
            rights.set_user_branches(db, user, body.branch_ids)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        details["branch_ids"] = body.branch_ids
    if user.role == "schulbegleitung" and body.student_ids is not None:
        students = get_store().school.index("students")
        unknown = [s for s in body.student_ids if s not in students]
        if unknown:
            raise HTTPException(422, f"Unbekannte Schüler: {', '.join(unknown[:10])}")
        rights.set_user_children(db, user, body.student_ids)
        details["student_ids"] = body.student_ids
    audit(db, actor, "rights.assign", f"user:{user.id}", details, ip=client_ip(request))
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------------------------ Ihre Rolle
@router.get("/rights/me")
def my_role(user: AuthUser = Depends(current_user)) -> dict:
    """„Ihre Rolle“: Rollenname, abgeleitete Titel (Klassenleitung, Zweig) und – bei Schulbegleitung – Kinder."""
    school = get_store().school
    students = school.index("students")
    return {"role": user.role, "role_label": ROLE_LABELS.get(user.role, user.role),
            "titles": rights.role_titles(school, user),
            "branches": [b["name"] for b in user.branches],
            "children": [students[s].name for s in user.student_ids if s in students]
            if user.role in ("schulbegleitung", "eltern") else []}
