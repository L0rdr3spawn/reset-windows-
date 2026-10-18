"""Elternzugriff (A-44): volljährige Schüler/innen legen je Bereich fest, was ihre Eltern sehen dürfen.

* ``GET /parent-access`` – eigene Einstellung (nur Schüler/innen): volljährig?, Bereiche mit ja/nein (nur
  ``ACTIVE_AREAS`` – Bereiche, die die Einwilligung schon prüfen), Zustellung von Rundschreiben (``delivery``:
  ``self|parents|both``), ``needs_decision`` (volljährig, aber noch nie gespeichert → Hinweis in der Oberfläche),
  verknüpfte Elternkonten (Namen).
* ``PUT /parent-access`` – ``{"areas": {"kursraeume": true, …}, "delivery": "both", "confirm": true}``; nur
  volljährig, sonst 403. Jedes Speichern gilt als Entscheidung (der Hinweis verschwindet). Protokolliert.

* ``PUT /students/{id}/birth-date`` – Geburtsdatum setzen oder löschen (Recht ``students.birth_date``; Klassenleitung nur
  für die eigene Klasse). Daraus folgt die Volljährigkeit (:func:`parent_access.is_adult`). Protokolliert.

Die Prüfung in den Features läuft über :func:`schulmanager.server.parent_access.parent_may_see`.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import parent_access as pa
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db
from schulmanager.server.db_models import ParentLink, User
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.events import bus

router = APIRouter(tags=["Elternzugriff"])


class ParentAccessIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    areas: dict[str, bool] = Field(default_factory=dict, max_length=len(pa.AREAS))
    delivery: Optional[Literal["self", "parents", "both"]] = None
    confirm: bool = False


def _student(user: AuthUser) -> str:
    if user.role != "schueler" or not user.student_id:
        raise HTTPException(403, "Nur Schüler/innen legen fest, was ihre Eltern sehen")
    return user.student_id


def _parents(db: Session, student_id: str) -> list[tuple[int, str]]:
    rows = db.execute(select(User.id, User.display_name, User.username)
                      .join(ParentLink, ParentLink.parent_user_id == User.id)
                      .where(ParentLink.student_id == student_id, User.active.is_(True))
                      .order_by(User.display_name, User.id)).all()
    return [(uid, dn or un) for uid, dn, un in rows]


def _out(db: Session, student_id: str) -> dict:
    adult = pa.is_adult(db, student_id)
    stored = pa.allowed_areas(db, student_id)
    return {
        "adult": adult, "editable": adult, "needs_decision": pa.decision_pending(db, student_id),
        "delivery": pa.delivery_of(db, student_id),
        "delivery_options": [{"key": k, "label": v} for k, v in pa.DELIVERY.items()],
        "areas": [{"key": key, "label": pa.AREAS[key], "allowed": True if not adult else stored[key]}
                  for key in pa.ACTIVE_AREAS],
        "parents": [{"name": name} for _, name in _parents(db, student_id)],
    }


@router.get("/parent-access")
def get_parent_access(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Was dürfen meine Eltern sehen? (Minderjährig: alles, nicht änderbar.)"""
    return _out(db, _student(user))


@router.put("/parent-access")
def put_parent_access(body: ParentAccessIn, request: Request, user: AuthUser = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    sid = _student(user)
    unknown = sorted(set(body.areas) - set(pa.ACTIVE_AREAS))
    if unknown:
        raise HTTPException(422, f"Nicht einstellbarer Bereich: {', '.join(unknown)}")
    if not pa.is_adult(db, sid):
        raise HTTPException(403, "Solange Sie noch nicht volljährig sind, sehen Ihre Eltern, was Sie sehen")
    if not (body.areas or body.delivery or body.confirm):
        raise HTTPException(422, "Nichts zu speichern")
    changed = pa.set_areas(db, sid, body.areas, user)
    if body.delivery and pa.set_delivery(db, sid, body.delivery):
        changed["zustellung"] = body.delivery   # type: ignore[assignment]
    pa.mark_decided(db, sid)
    if changed:
        audit(db, user, "parent_access.update", f"student:{sid}", {"changes": changed}, ip=client_ip(request))
    db.commit()
    if changed:
        ids = {uid for uid, _ in _parents(db, sid)} | {user.id}
        bus.publish("change", {"version": None, "scope": ["parent_access", "channels", "student_absences", "timetable", "announcements",
                                                       "student_documents", "messages"], "dates": []},
                    user_ids=ids)
    return _out(db, sid)


# =========================================================================== Geburtsdatum (Volljährigkeit)
BIRTH_PERM = "students.birth_date"
MIN_AGE, MAX_AGE = 3, 100


class BirthDateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    birth_date: Optional[date] = None


def may_set_birth_date(user: AuthUser, student_id: str, snap) -> bool:
    """Recht ``students.birth_date``; mit Scope ``class_teacher`` nur Schüler/innen der geleiteten Klassen."""
    from .features_common import has, perm_scope

    if not has(user, BIRTH_PERM) or user.role in ("schueler", "eltern"):
        return False
    scope = perm_scope(user, BIRTH_PERM)
    if scope is None:
        return True
    if scope == "class_teacher":
        from schulmanager.server.absence_access import class_teacher_students
        return student_id in class_teacher_students(snap[1], getattr(user, "teacher_id", None))
    return False


def check_birth_date(value: Optional[date], today: Optional[date] = None) -> None:
    if value is None:
        return
    today = today or date.today()
    if not MIN_AGE <= pa.age_on(value, today) <= MAX_AGE:
        raise HTTPException(422, f"Das Geburtsdatum ist nicht plausibel (Alter {MIN_AGE} bis {MAX_AGE} Jahre)")


@router.put("/students/{student_id}/birth-date")
def put_birth_date(student_id: str, body: BirthDateIn, request: Request, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Geburtsdatum einer Schülerin/eines Schülers setzen (``null`` = löschen; dann zählt wieder das Konto-Merkmal)."""
    from .features_common import index, mutate, snapshot

    snap = snapshot()
    st = index("students", snap).get(student_id)
    if st is None or not may_set_birth_date(user, student_id, snap):
        raise HTTPException(404 if st is None else 403, "Schüler/in nicht gefunden" if st is None else "Keine Berechtigung")
    check_birth_date(body.birth_date)
    new = body.birth_date.isoformat() if body.birth_date else None
    before = pa.is_adult(db, student_id, school=snap[1])
    if (st.birth_date or None) != new:
        def fn(school):
            school.index("students")[student_id].birth_date = new
        mutate(user, f"Geburtsdatum geändert ({student_id})", fn, scope=["students"])
    adult = pa.is_adult(db, student_id)
    for acct in db.scalars(select(User).where(User.student_id == student_id, User.role == "schueler")):
        acct.adult = adult   # Konto-Merkmal mitführen (Briefe, Rechte)
    audit(db, user, "student.birth_date", f"student:{student_id}",
          {"set": new is not None, "adult": adult, "was_adult": before}, ip=client_ip(request))
    db.commit()
    ids = {uid for uid in db.scalars(select(User.id).where(User.student_id == student_id, User.role == "schueler"))}
    if ids:
        bus.publish("change", {"version": None, "scope": ["parent_access", "student_absences", "me"], "dates": []},
                    user_ids=ids)
    return {"student_id": student_id, "birth_date": new, "adult": adult}
