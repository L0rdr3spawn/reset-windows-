"""Sicherheits-Einstellungen und Anmelde-Drosselung verwalten (Bericht S-04, S-06, S-17).

* ``GET  /security/settings`` – Zwei-Faktor-Vorgabe für Personal, Abmeldung bei Inaktivität, Frist für Startpasswörter
  (Recht ``login_policy.manage``: Administration, Schulleitung)
* ``PUT  /security/settings`` – Teil-Update
* ``GET  /login-locks`` – aktuell gedrosselte Benutzernamen/IPs (Recht ``users.manage``)
* ``DELETE /login-locks?username=`` bzw. ``?ip=`` – Drosselung aufheben (Benutzername: ``users.manage`` und Zugriff auf
  die Rolle des Kontos; IP: ``login_policy.manage``)

Alle Änderungen stehen im Protokoll (``security.settings``, ``login_lock.clear``).
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager.server import login_throttle, security_settings as ss
from schulmanager.server.audit import audit
from schulmanager.server.config import config
from schulmanager.server.db import get_db, iso
from schulmanager.server.db_models import User
from schulmanager.server.deps import AuthUser, client_ip, require
from schulmanager.server.permissions import ROLE_LABELS, can_manage_role

router = APIRouter(tags=["Sicherheit"])


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    twofa_mode: Optional[Literal["off", "recommended", "required"]] = None
    twofa_roles: Optional[list[str]] = Field(None, max_length=20)
    staff_idle_minutes: Optional[int] = Field(None, ge=ss.IDLE_RANGE[0], le=ss.IDLE_RANGE[1])
    initial_password_days: Optional[int] = Field(None, ge=ss.PASSWORD_DAYS_RANGE[0], le=ss.PASSWORD_DAYS_RANGE[1])


def _view(db: Session) -> dict:
    values = ss.load(db)
    return {**values,
            "env_required_roles": sorted(config.require_2fa_roles),
            "role_choices": [{"id": r, "label": ROLE_LABELS.get(r, r)} for r in ss.TWOFA_ROLE_CHOICES],
            "staff_roles": sorted(ss.STAFF_ROLES),
            "idle_range": list(ss.IDLE_RANGE), "password_days_range": list(ss.PASSWORD_DAYS_RANGE),
            "student_idle_minutes": config.session_idle_minutes,
            "lock": {"max_failures": config.login_max_failures, "max_failures_ip": config.login_max_failures_ip,
                     "base_delay_seconds": login_throttle.BASE_DELAY, "max_delay_seconds": config.login_lock_minutes * 60}}


@router.get("/security/settings")
def get_settings(user: AuthUser = Depends(require("login_policy.manage")), db: Session = Depends(get_db)) -> dict:
    return _view(db)


@router.put("/security/settings")
def put_settings(body: SettingsIn, request: Request, user: AuthUser = Depends(require("login_policy.manage")),
                 db: Session = Depends(get_db)) -> dict:
    patch = body.model_dump(exclude_unset=True, exclude_none=True)
    try:
        ss.save(db, patch, user.id)
    except ss.SettingError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from None
    audit(db, user, "security.settings", "security_settings", patch, ip=client_ip(request))
    db.commit()
    return _view(db)


def _lock_view(row: dict) -> dict:
    return {**row, "last_failure": iso(row["last_failure"])}


@router.get("/login-locks")
def list_locks(user: AuthUser = Depends(require("users.manage")), db: Session = Depends(get_db)) -> dict:
    rows = login_throttle.active_locks(db)
    roles = {u.username.lower(): u.role for u in db.scalars(select(User).where(
        func.lower(User.username).in_([r["username"] for r in rows if r["username"]])))} if rows else {}
    out = []
    for r in rows:
        role = roles.get(r["username"] or "")
        if r["username"] and role and not can_manage_role(user.role, role):
            continue                      # Konten, die diese Rolle nicht verwaltet, bleiben unsichtbar
        if r["kind"] == "ip" and "login_policy.manage" not in user.permissions:
            continue
        out.append({**_lock_view(r), "role": role, "role_label": ROLE_LABELS.get(role or "", None)})
    return {"locks": out, "known_user": None}


@router.delete("/login-locks")
def clear_lock(request: Request, username: Optional[str] = Query(None, max_length=80),
               ip: Optional[str] = Query(None, max_length=64), user: AuthUser = Depends(require("users.manage")),
               db: Session = Depends(get_db)) -> dict:
    if bool(username) == bool(ip):
        raise HTTPException(422, "Entweder Benutzername oder IP angeben.")
    if username:
        target = db.scalar(select(User).where(func.lower(User.username) == username.strip().lower()))
        if target is not None and not can_manage_role(user.role, target.role):
            raise HTTPException(403, "Konten dieser Rolle darf die Verwaltung nicht entsperren.")
        n = login_throttle.clear_user(db, username)
        what = f"user:{target.id}" if target is not None else f"login:{username.strip().lower()[:80]}"
    else:
        if "login_policy.manage" not in user.permissions:
            raise HTTPException(403, "IP-Sperren heben nur Administration und Schulleitung auf.")
        n = login_throttle.clear_ip(db, ip or "")
        what = f"ip:{ip}"
    audit(db, user, "login_lock.clear", what, {"cleared": n}, ip=client_ip(request))
    db.commit()
    return {"cleared": n}
