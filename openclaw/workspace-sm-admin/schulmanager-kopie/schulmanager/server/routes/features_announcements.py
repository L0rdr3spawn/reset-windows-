"""Mitteilungen (Tabelle ``announcements``).

Zielgruppen: ``all`` (alle), ``staff`` (Kollegium), ``classes`` (bestimmte Klassen – Schüler,
Eltern und Lehrkräfte dieser Klassen); optional zusätzlich auf Rollen (``audience_roles``)
und einen Standort beschränkt. ``monitor: true`` zeigt die Mitteilung auf der Monitor-Ansicht.
Lehrkräfte (``announcement.post`` mit Scope ``own_classes``) dürfen nur an eigene Klassen schreiben.
"""
from __future__ import annotations

import threading
import time
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server.db import get_db, iso
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import (has, index, own_class_ids, parse_date, perm_scope, publish_change, snapshot,
                              write_audit)

router = APIRouter(tags=["Mitteilungen"])

STAFF = {"admin", "schulleitung", "planer", "sekretariat", "lehrer"}
CACHE_TTL = 15.0

_cache_lock = threading.Lock()
_cache: dict = {"at": 0.0, "rows": None}


def invalidate_cache() -> None:
    with _cache_lock:
        _cache["rows"] = None


def _row_dict(a) -> dict:
    return {"id": a.id, "title": a.title, "body": a.body, "author_id": a.author_id, "author_name": a.author_name,
            "audience": a.audience, "audience_roles": list(a.audience_roles or []),
            "class_ids": list(a.class_ids or []),
            "site": a.site, "valid_from": a.valid_from, "valid_to": a.valid_to, "pinned": bool(a.pinned),
            "priority": a.priority, "monitor": bool(a.monitor), "created_at": iso(a.created_at)}


def _all_rows(db: Session) -> list[dict]:
    from schulmanager.server.db_models import Announcement
    with _cache_lock:
        rows = _cache["rows"]
        if rows is not None and time.monotonic() - _cache["at"] < CACHE_TTL:
            return rows
    rows = [_row_dict(a) for a in db.scalars(select(Announcement).order_by(Announcement.created_at.desc()))]
    with _cache_lock:
        _cache["rows"], _cache["at"] = rows, time.monotonic()
    return rows


def _user_site(user, snap) -> Optional[str]:
    site = getattr(user, "site", None)
    if site:
        return site
    students = index("students", snap)
    classes = index("classes", snap)
    for sid in getattr(user, "student_ids", None) or []:
        st = students.get(sid)
        if st and st.class_id in classes:
            return classes[st.class_id].site or None
    return None


def _audience_classes(db: Optional[Session], user, snap) -> frozenset[str]:
    """Klassen, über die ``user`` klassenbezogene Mitteilungen bekommt. Eltern volljähriger Kinder nur mit Freigabe
    „mitteilungen“ (:mod:`parent_access`)."""
    if db is None or getattr(user, "role", "") != "eltern":
        return own_class_ids(user, snap)
    from schulmanager.server import parent_access as pa

    students = index("students", snap)
    kids = pa.visible_children(db, getattr(user, "student_ids", None) or [], pa.AREA_ANNOUNCEMENTS, school=snap[1])
    return frozenset(students[k].class_id for k in kids if k in students)


def is_visible(a: dict, user, snap, classes: Optional[frozenset[str]] = None) -> bool:
    role = getattr(user, "role", "")
    if a.get("author_id") is not None and a["author_id"] == getattr(user, "id", None):
        return True
    roles = a.get("audience_roles") or []
    if roles and role not in roles:
        return False
    if a["audience"] == "staff":
        if role not in STAFF:
            return False
    elif a["audience"] == "classes":
        if role in STAFF and role != "lehrer":
            pass
        elif not set(a.get("class_ids") or []) & set(classes if classes is not None else own_class_ids(user, snap)):
            return False
    if a.get("site"):
        site = _user_site(user, snap)
        if site and site != a["site"]:
            return False
    return True


def _sorted(rows: list[dict]) -> list[dict]:
    """Angeheftet zuerst, dann „wichtig“, sonst neueste zuerst."""
    rows = sorted(rows, key=lambda a: a.get("created_at") or "", reverse=True)
    return sorted(rows, key=lambda a: (not a["pinned"], a["priority"] != "wichtig"))


def visible_announcements(db: Session, user, day: date, snap=None, *, until: Optional[date] = None,
                          monitor: bool = False) -> list[dict]:
    """Mitteilungen, die ``user`` am Tag ``day`` (bis ``until``) sehen darf."""
    snap = snap or snapshot()
    d1, d2 = day.isoformat(), (until or day).isoformat()
    out = []
    classes = _audience_classes(db, user, snap)
    for a in _all_rows(db):
        if a["valid_to"] and a["valid_to"] < d1:
            continue
        if a["valid_from"] and a["valid_from"] > d2:
            continue
        if monitor:
            if not a["monitor"]:
                continue
            if a["audience"] != "all" or (a.get("audience_roles") and "monitor" not in a["audience_roles"]):
                continue
        elif not is_visible(a, user, snap, classes):
            continue
        out.append({**a, "can_delete": can_delete(user, a)})
    return _sorted(out)


def can_delete(user, a: dict) -> bool:
    if a.get("author_id") is not None and a["author_id"] == getattr(user, "id", None):
        return True
    return has(user, "announcement.post") and perm_scope(user, "announcement.post") is None


class AnnouncementIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field("", max_length=20000)
    audience: Literal["all", "staff", "classes"] = "all"
    audience_roles: list[Literal["admin", "schulleitung", "planer", "sekretariat", "lehrer", "schueler",
                                 "eltern", "monitor"]] = Field(default_factory=list)
    class_ids: list[str] = Field(default_factory=list)
    site: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    pinned: bool = False
    priority: Literal["normal", "wichtig"] = "normal"
    monitor: bool = False


def _validate(body: AnnouncementIn, user, snap) -> None:
    school = snap[1]
    if body.audience == "classes" and not body.class_ids:
        raise HTTPException(422, "Bitte mindestens eine Klasse auswählen")
    unknown = [c for c in body.class_ids if c not in school.index("classes")]
    if unknown:
        raise HTTPException(422, f"Unbekannte Klasse(n): {', '.join(unknown)}")
    if body.site and body.site not in school.index("sites"):
        raise HTTPException(422, f"Standort „{body.site}“ existiert nicht")
    if body.valid_from and body.valid_to and body.valid_to < body.valid_from:
        raise HTTPException(422, "„Gültig bis“ liegt vor „Gültig ab“")
    if perm_scope(user, "announcement.post") == "own_classes":
        own = own_class_ids(user, snap)
        if body.audience != "classes":
            raise HTTPException(403, "Lehrkräfte können Mitteilungen nur an eigene Klassen richten")
        foreign = [c for c in body.class_ids if c not in own]
        if foreign:
            raise HTTPException(403, f"Keine eigene Klasse: {', '.join(foreign)}")
        if body.monitor or body.pinned:
            raise HTTPException(403, "Monitor-Anzeige und Anheften nur durch Schulleitung/Sekretariat")


def _apply(row, body: AnnouncementIn) -> None:
    row.title = body.title.strip()
    row.body = body.body
    row.audience = body.audience
    row.audience_roles = list(dict.fromkeys(body.audience_roles)) or None
    row.class_ids = list(dict.fromkeys(body.class_ids)) if body.audience == "classes" else []
    row.site = body.site or None
    row.valid_from = body.valid_from.isoformat() if body.valid_from else None
    row.valid_to = body.valid_to.isoformat() if body.valid_to else None
    row.pinned = body.pinned
    row.priority = body.priority
    row.monitor = body.monitor


@router.get("/announcements")
def list_announcements(date_: Optional[str] = Query(None, alias="date"), all_: bool = Query(False, alias="all"),
                       user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Sichtbare, aktuell gültige Mitteilungen. ``?all=1`` (mit ``announcement.post``): auch
    abgelaufene/künftige (eigene bzw. alle ohne Scope-Einschränkung)."""
    snap = snapshot()
    if all_ and has(user, "announcement.post"):
        rows = _all_rows(db)
        if perm_scope(user, "announcement.post") is not None:
            rows = [a for a in rows if is_visible(a, user, snap)]
        return _sorted([{**a, "can_delete": can_delete(user, a)} for a in rows])
    return visible_announcements(db, user, parse_date(date_), snap)


@router.post("/announcements", status_code=201)
def create_announcement(body: AnnouncementIn, user: AuthUser = Depends(require("announcement.post")),
                        db: Session = Depends(get_db)):
    from schulmanager.server.db_models import Announcement
    snap = snapshot()
    _validate(body, user, snap)
    row = Announcement(author_id=user.id or None, author_name=user.display_name or user.username)
    _apply(row, body)
    db.add(row)
    db.flush()
    write_audit(db, user, "announcement.create", f"announcement:{row.id}",
                {"title": row.title, "audience": row.audience, "class_ids": row.class_ids})
    db.commit()
    invalidate_cache()
    publish_change(["announcements"], [d for d in (row.valid_from,) if d])
    return {**_row_dict(row), "can_delete": True}


@router.put("/announcements/{announcement_id}")
def update_announcement(announcement_id: int, body: AnnouncementIn,
                        user: AuthUser = Depends(require("announcement.post")), db: Session = Depends(get_db)):
    from schulmanager.server.db_models import Announcement
    row = db.get(Announcement, announcement_id)
    if row is None:
        raise HTTPException(404, "Mitteilung nicht gefunden")
    if not can_delete(user, _row_dict(row)):
        raise HTTPException(403, "Nur eigene Mitteilungen können bearbeitet werden")
    _validate(body, user, snapshot())
    _apply(row, body)
    write_audit(db, user, "announcement.update", f"announcement:{row.id}", {"title": row.title})
    db.commit()
    invalidate_cache()
    publish_change(["announcements"])
    return {**_row_dict(row), "can_delete": True}


@router.delete("/announcements/{announcement_id}")
def delete_announcement(announcement_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Löschen: Autor/in oder Benutzer mit uneingeschränktem ``announcement.post``."""
    from schulmanager.server.db_models import Announcement
    row = db.get(Announcement, announcement_id)
    if row is None:
        raise HTTPException(404, "Mitteilung nicht gefunden")
    if not can_delete(user, _row_dict(row)):
        raise HTTPException(403, "Keine Berechtigung")
    write_audit(db, user, "announcement.delete", f"announcement:{row.id}", {"title": row.title})
    db.delete(row)
    db.commit()
    invalidate_cache()
    publish_change(["announcements"])
    return {"deleted": announcement_id}

