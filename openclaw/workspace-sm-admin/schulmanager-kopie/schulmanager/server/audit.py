"""Audit-Protokoll.

``audit(db, user, action, target, details)`` fügt einen Eintrag zur laufenden Session hinzu
(Commit durch den Aufrufer, damit Änderung und Protokoll in einer Transaktion landen).
``audit_now(...)`` schreibt sofort in einer eigenen Transaktion.

Konvention für ``action``: ``bereich.verb``, z. B. ``auth.login``, ``user.create``, ``plan.change``,
``announcement.create``, ``student_absence.update``.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from .db import session_scope
from .db_models import AuditLog

log = logging.getLogger("schulmanager.audit")


def _user_fields(user: Any) -> tuple[int | None, str]:
    if user is None:
        return None, "system"
    uid = getattr(user, "id", None)
    name = getattr(user, "username", None) or "system"
    if not uid:  # SYSTEM_USER (id 0) oder unbekannt
        return None, name
    return int(uid), name


def audit(db: Session, user: Any, action: str, target: str = "", details: dict | None = None,
          ip: str | None = None) -> AuditLog:
    """Protokolliert eine Aktion. ``user``: ``AuthUser``, ORM-``User`` oder ``None`` (System)."""
    uid, name = _user_fields(user)
    entry = AuditLog(user_id=uid, username=name, action=action[:80], target=str(target or "")[:200],
                     details=details or None, ip=ip)
    db.add(entry)
    return entry


def audit_now(user: Any, action: str, target: str = "", details: dict | None = None, ip: str | None = None) -> None:
    """Wie :func:`audit`, aber sofort in eigener Transaktion (Fehler werden nur geloggt)."""
    try:
        with session_scope() as db:
            audit(db, user, action, target, details, ip)
    except Exception:  # noqa: BLE001
        log.exception("Audit-Eintrag %s konnte nicht geschrieben werden", action)


def audit_dict(entry: AuditLog) -> dict:
    from .db import iso
    return {"id": entry.id, "created_at": iso(entry.created_at), "user_id": entry.user_id,
            "user": entry.username, "action": entry.action, "target": entry.target,
            "details": entry.details or {}, "ip": entry.ip}
