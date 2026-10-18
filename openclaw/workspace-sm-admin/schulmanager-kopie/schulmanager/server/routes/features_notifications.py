"""Benachrichtigungszentrale (Glocke): eigene Benachrichtigungen und Einstellungen (``docs/BENACHRICHTIGUNGEN.md``).

Jedes angemeldete Konto sieht und ändert **nur die eigenen** Benachrichtigungen (fremde IDs bleiben wirkungslos bzw. 404).

* ``GET /notifications`` – Liste (neueste zuerst; ``unread=1``, ``limit``, ``before``) + ``unread`` (Zähler).
* ``GET /notifications/count`` – nur der Zähler (für die Glocke).
* ``POST /notifications/read`` – ``{"ids": [..] | null, "read": true}``: als gelesen/ungelesen markieren (ohne ``ids``: alle).
* ``DELETE /notifications/{id}`` und ``DELETE /notifications?read=1`` – eigene löschen.
* ``GET/PUT /notifications/settings`` – Einstellung je Ereignisart (``aus|app|mail``), Zusammenfassung, Ruhezeiten.
* ``GET/PUT /notifications/school`` – Schulvorgaben (Standard je Art, Pflicht = gesperrt, Aufbewahrung); Recht
  ``settings.edit``.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import notifications as nt
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user, require
from schulmanager.server.feature_models.notifications import Notification

router = APIRouter(tags=["Benachrichtigungen"])


def _children(user: AuthUser) -> Optional[dict[str, str]]:
    """Eltern: Kind-Namen für die Anzeige „für <Kind>“ (sonst ``None``)."""
    if user.role != "eltern" or not user.student_ids:
        return None
    try:
        from .features_common import snapshot
        idx = snapshot()[1].index("students")
        return {sid: idx[sid].name for sid in user.student_ids if sid in idx}
    except Exception:  # noqa: BLE001
        return {}


class ReadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ids: Optional[list[int]] = Field(None, max_length=500)
    read: bool = True


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modes: dict[str, str] = Field(default_factory=dict, max_length=60)
    digest: Optional[bool] = None
    quiet_enabled: Optional[bool] = None
    quiet_from: Optional[str] = Field(None, max_length=5)
    quiet_to: Optional[str] = Field(None, max_length=5)


class SchoolRuleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = Field("app", max_length=10)
    locked: bool = False


class SchoolIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rules: dict[str, SchoolRuleIn] = Field(default_factory=dict, max_length=60)
    retention_days: Optional[int] = Field(None, ge=1, le=3650)


@router.get("/notifications")
def list_notifications(unread: bool = Query(False), limit: int = Query(50, ge=1, le=100),
                       before: Optional[int] = Query(None, ge=1), user: AuthUser = Depends(current_user),
                       db: Session = Depends(get_db)) -> dict:
    """Eigene Benachrichtigungen, neueste zuerst."""
    items = nt.list_for(db, user.id, unread_only=unread, limit=limit, before=before, children=_children(user))
    return {"items": items, "unread": nt.unread_count(db, user.id), "more": len(items) >= limit}


@router.get("/notifications/count")
def notification_count(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"unread": nt.unread_count(db, user.id)}


@router.post("/notifications/read")
def mark_notifications(body: ReadIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Markiert eigene Benachrichtigungen als gelesen (oder ungelesen); ohne ``ids`` alle."""
    changed = nt.mark_read(db, user.id, body.ids, body.read)
    db.commit()
    if changed:
        nt._publish([user.id])  # weitere Fenster/Geräte derselben Person aktualisieren
    return {"changed": changed, "unread": nt.unread_count(db, user.id)}


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, user: AuthUser = Depends(current_user),
                        db: Session = Depends(get_db)) -> dict:
    own = db.scalar(select(Notification.id).where(Notification.id == notification_id,
                                                  Notification.user_id == user.id))
    if own is None:
        raise HTTPException(404, "Benachrichtigung nicht gefunden")
    nt.delete_own(db, user.id, [notification_id])
    db.commit()
    nt._publish([user.id])
    return {"unread": nt.unread_count(db, user.id)}


@router.delete("/notifications")
def delete_notifications(read: bool = Query(True, description="nur gelesene löschen"),
                         user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Löscht eigene gelesene Benachrichtigungen (``read=0``: alle eigenen)."""
    n = nt.delete_own(db, user.id, None, only_read=read)
    db.commit()
    if n:
        nt._publish([user.id])
    return {"deleted": n, "unread": nt.unread_count(db, user.id)}


@router.get("/notifications/settings")
def get_settings(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return nt.user_prefs(db, user.id, user.permissions)


@router.put("/notifications/settings")
def put_settings(body: SettingsIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    try:
        changed = nt.save_user_prefs(db, user.id, modes=body.modes, digest=body.digest,
                                     quiet_enabled=body.quiet_enabled, quiet_from=body.quiet_from,
                                     quiet_to=body.quiet_to)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from None
    if changed:
        audit(db, user, "notification_settings.update", f"user:{user.id}", {"changed": changed})
    db.commit()
    return nt.user_prefs(db, user.id, user.permissions)


@router.get("/notifications/school")
def get_school(user: AuthUser = Depends(require("settings.edit")), db: Session = Depends(get_db)) -> dict:
    rules = nt.school_rules(db)
    return {"kinds": [{**meta, **rules[kind], "default": meta["default"]} for kind, meta in nt.KINDS.items()],
            "modes": [{"value": m, "label": nt.MODE_LABELS[m]} for m in nt.MODES],
            "retention_days": nt.retention_days(db), "mail_available": nt.mail_available(),
            "retention_min": nt.MIN_RETENTION_DAYS, "retention_max": nt.MAX_RETENTION_DAYS}


@router.put("/notifications/school")
def put_school(body: SchoolIn, user: AuthUser = Depends(require("settings.edit")),
               db: Session = Depends(get_db)) -> dict:
    try:
        changed = nt.save_school_rules(db, {k: v.model_dump() for k, v in body.rules.items()}, body.retention_days)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from None
    if changed:
        audit(db, user, "notification_school.update", "notification_school", {"changed": changed})
    db.commit()
    return get_school(user, db)
