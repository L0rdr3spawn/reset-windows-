"""Verlauf des Planungsdokuments (Versionen, Wiederherstellen, Rückgängig) und Audit-Protokoll."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import COLLECTIONS
from ..audit import audit_dict
from ..db import get_db
from ..db_models import AuditLog
from ..deps import AuthUser, require
from ..store import StoreError, get_store

router = APIRouter(tags=["Verlauf"])


@router.get("/history")
def history(limit: int = Query(50, ge=1, le=1000), offset: int = Query(0, ge=0),
            _user: AuthUser = Depends(require("history.restore"))) -> list[dict]:
    """Versionen des Planungsdokuments (neueste zuerst)."""
    return get_store().history(limit, offset)


@router.get("/history/{version}")
def history_version(version: int, _user: AuthUser = Depends(require("history.restore"))) -> dict:
    """Kurzüberblick einer Version (Anzahl Einträge je Sammlung)."""
    store = get_store()
    try:
        school = store.get_version(version)
    except StoreError as exc:
        raise HTTPException(404, str(exc)) from None
    meta = next((h for h in store.history(1000) if h["version"] == version), {"version": version})
    return {**meta, "school_name": school.settings.school_name,
            "counts": {name: len(getattr(school, name)) for name in COLLECTIONS}}


@router.post("/history/{version}/restore")
def restore(version: int, user: AuthUser = Depends(require("history.restore"))) -> dict:
    """Stellt eine ältere Version als neue Version wieder her."""
    store = get_store()
    try:
        new_version = store.restore(user, version)
    except StoreError as exc:
        raise HTTPException(404, str(exc)) from None
    return {"version": new_version, "restored_from": version}


@router.post("/history/undo")
def undo(user: AuthUser = Depends(require("history.restore"))) -> dict:
    """Macht die letzte Änderung rückgängig (schrittweise wiederholbar)."""
    try:
        new_version = get_store().undo(user)
    except StoreError as exc:
        raise HTTPException(409, str(exc)) from None
    return {"version": new_version}


@router.get("/audit")
def audit_log(request: Request, limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0),
              user: str | None = None, action: str | None = None, target: str | None = None,
              since: datetime | None = None, until: datetime | None = None,
              _actor: AuthUser = Depends(require("audit.read")), db: Session = Depends(get_db)) -> list[dict]:
    """Audit-Protokoll (Filter: Benutzername, Aktion als Präfix, Ziel, Zeitraum)."""
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if user:
        stmt = stmt.where(AuditLog.username == user)
    if action:
        stmt = stmt.where(AuditLog.action.startswith(action))
    if target:
        stmt = stmt.where(AuditLog.target == target)
    if since:
        stmt = stmt.where(AuditLog.created_at >= since.replace(tzinfo=None))
    if until:
        stmt = stmt.where(AuditLog.created_at <= until.replace(tzinfo=None))
    rows = db.scalars(stmt.offset(offset).limit(limit)).all()
    return [audit_dict(r) for r in rows]
