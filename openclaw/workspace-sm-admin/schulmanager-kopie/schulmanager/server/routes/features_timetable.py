"""Stundenplan-Ansichten, Verschieben (Drag & Drop) und Fixieren von Stunden.

Sichtbarkeit (§6/§9.3): ``plans.read_all`` ohne Einschränkung → alle Pläne. Lehrkräfte (Scope ``own_classes``)
→ Pläne ihrer Klassen (unterrichtet/Klassenleitung), der eigene Lehrerplan und Räume; Schülerpläne nur für
Schüler/innen eigener Klassen. Schüler/Eltern → eigene Klasse(n) und eigener Schülerplan.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import (cached, can_see_student, has, index, is_scoped_teacher, lesson_by_id, mutate,
                              family_student_ids, own_class_ids, own_student_ids, plan_class_ids, plan_course_ids, reads_all_plans,
                              snapshot)

router = APIRouter(tags=["Stundenplan"])

SCOPE_HINT = ("Lehrkräfte sehen ihren eigenen Plan und – als Klassenleitung – den Plan ihrer Klasse und ihrer "
              "Schüler/innen. Raumpläne und Pläne anderer Lehrkräfte sieht nur die Planung/Verwaltung.")

Kind = Literal["class", "teacher", "room", "student"]


class MoveIn(BaseModel):
    day: int = Field(ge=0, le=6)
    start: int = Field(ge=0, le=15)


class LockIn(BaseModel):
    locked: bool


def check_view_access(user, kind: str, ref: str, snap) -> None:
    """Rechte für Stundenplan-Ansichten (Rollenmatrix inkl. Lehrer-Scope).

    Unbekannte Klassen/Lehrkräfte/Räume → 404 (deren Kürzel sind nicht geheim, z. B. Aushang/Monitor);
    unbekannte Schüler-IDs → 403 wie fremde, damit sich keine Schüler-IDs erraten lassen."""
    collection = {"class": "classes", "teacher": "teachers", "room": "rooms"}.get(kind)
    if collection and ref not in index(collection, snap):
        what = {"class": "Klasse", "teacher": "Lehrkraft", "room": "Raum"}[kind]
        raise HTTPException(404, f"{what} „{ref}“ nicht gefunden")
    lead = plan_class_ids(user, snap)          # None = alle; Lehrkräfte: geleitete Klassen
    if kind == "student":
        if ref in own_student_ids(user):
            if ref not in family_student_ids(user, "stundenplan", snap):
                raise HTTPException(403, "Ihr Kind ist volljährig und hat den Stundenplan nicht für die Eltern freigegeben")
            return
        if lead is None and has(user, "students.read") and can_see_student(user, ref, snap):
            return
        st = index("students", snap).get(ref)
        if is_scoped_teacher(user) and st is not None and lead and st.class_id in lead:
            return
        raise HTTPException(403, "Keine Berechtigung für diesen Schülerplan"
                                 + (f" – {SCOPE_HINT}" if is_scoped_teacher(user) else ""))
    if reads_all_plans(user) or has(user, "timetable.edit"):
        return
    if kind == "room" and has(user, "rooms.read"):   # z. B. Hausmeister
        return
    if kind == "class" and lead is not None and ref in lead:
        return
    if kind == "teacher" and ref == getattr(user, "teacher_id", None):
        return
    if is_scoped_teacher(user):
        what = {"class": "Klassenplan", "teacher": "Lehrerplan"}.get(kind, "Plan")
        raise HTTPException(403, f"Keine Berechtigung für diesen {what} – {SCOPE_HINT}")
    raise HTTPException(403, "Keine Berechtigung für diesen Plan")


@router.get("/timetable/lessons")
def list_lessons(user: AuthUser = Depends(current_user)):
    """Stunden (Rohdaten) – Planung: alle; Lehrkräfte: Stunden ihrer Klassen und eigenen Kurse."""
    if not (has(user, "plans.read_all") or has(user, "timetable.edit")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    allowed = None if has(user, "timetable.edit") else plan_course_ids(user, snap)
    return [le.to_dict() for le in snap[1].lessons if allowed is None or le.course_id in allowed]


@router.get("/timetable/allowed")
def allowed_refs(user: AuthUser = Depends(current_user)):
    """Welche Pläne darf der Benutzer öffnen? (für Auswahllisten im Frontend)

    ``{"all": bool, "kinds": [...], "classes": [ids]|null, "teachers": [ids]|null, "rooms": null,
    "students": [ids]|null}`` – ``null`` = alle der Sammlung."""
    snap = snapshot()
    if reads_all_plans(user) or has(user, "timetable.edit"):
        return {"all": True, "kinds": ["class", "teacher", "room", "student"], "classes": None, "teachers": None,
                "rooms": None, "students": None if has(user, "students.read") else []}
    tid = getattr(user, "teacher_id", None)
    own_students = family_student_ids(user, "stundenplan", snap)
    if has(user, "rooms.read") and not is_scoped_teacher(user):
        return {"all": False, "kinds": ["room"], "classes": [], "teachers": [], "rooms": None, "students": []}
    if is_scoped_teacher(user):
        classes = sorted(plan_class_ids(user, snap) or [])
        students = sorted(s.id for s in snap[1].students if s.class_id in set(classes))
        kinds = ["teacher"] + (["class"] if classes else []) + (["student"] if students else [])
        return {"all": False, "kinds": kinds, "classes": classes, "teachers": [tid] if tid else [],
                "rooms": [], "students": students}
    return {"all": False, "kinds": ["student"] if own_students else [], "classes": sorted(own_class_ids(user, snap)),
            "teachers": [tid] if tid else [], "rooms": [], "students": own_students}


@router.get("/timetable/lessons/{lesson_id}/options")
def lesson_options(lesson_id: str, user: AuthUser = Depends(require("timetable.edit"))):
    """Mögliche Zielpositionen einer Stunde inkl. Konflikten (für Drag & Drop)."""
    snap = snapshot()
    if lesson_by_id(snap[1], lesson_id) is None:
        raise HTTPException(404, f"Stunde {lesson_id} nicht gefunden")

    def compute():
        from schulmanager.timetable import move_options
        return move_options(snap[1], lesson_id)

    return cached("move_options", (lesson_id,), compute, snap)


@router.post("/timetable/lessons/{lesson_id}/move")
def move(lesson_id: str, body: MoveIn, user: AuthUser = Depends(require("timetable.edit"))):
    """Verschiebt eine Stunde. Konflikte → 409 ``{"detail":{"conflicts":[...]}}``."""
    from schulmanager.timetable import check_move, lesson_info, move_lesson

    snap = snapshot()
    les = lesson_by_id(snap[1], lesson_id)
    if les is None:
        raise HTTPException(404, f"Stunde {lesson_id} nicht gefunden")
    st = snap[1].settings
    if body.start + les.length > st.periods:
        raise HTTPException(422, "Zielposition liegt außerhalb des Zeitrasters")
    conflicts = check_move(snap[1], lesson_id, body.day, body.start)
    if conflicts:
        raise HTTPException(409, {"conflicts": conflicts})

    def fn(school):
        try:
            moved = move_lesson(school, lesson_id, body.day, body.start)
        except KeyError:
            raise HTTPException(404, f"Stunde {lesson_id} nicht gefunden") from None
        except ValueError as exc:
            conf = exc.args[0] if exc.args and isinstance(exc.args[0], list) else [str(exc)]
            raise HTTPException(409, {"conflicts": conf}) from None
        return lesson_info(school, moved)

    return mutate(user, f"Stunde {lesson_id} verschoben", fn, scope=["timetable"])


@router.post("/timetable/lessons/{lesson_id}/lock")
def lock(lesson_id: str, body: LockIn, user: AuthUser = Depends(require("timetable.edit"))):
    """Fixiert eine Stunde (bleibt bei Neugenerierung mit ``keep_locked`` erhalten)."""
    from schulmanager.timetable import lesson_info

    def fn(school):
        les = lesson_by_id(school, lesson_id)
        if les is None:
            raise HTTPException(404, f"Stunde {lesson_id} nicht gefunden")
        les.locked = body.locked
        return lesson_info(school, les)

    verb = "fixiert" if body.locked else "freigegeben"
    return mutate(user, f"Stunde {lesson_id} {verb}", fn, scope=["timetable"])


def view_monday(school, date_: Optional[str], week_no: Optional[int], week: Optional[int],
                today: Optional[date] = None) -> date:
    """Woche einer Ansicht: ``date`` (kanonisch) > ``week_no`` (laufende Woche des aktuellen Schuljahres) > ``week``
    (alt, 0-basiert, gelesen als ``week_no = week + 1``) > heute."""
    from schulmanager.calendar_utils import monday_of, monday_of_week_no
    today = today or date.today()
    if date_:
        try:
            day = date.fromisoformat(date_[:10])
        except ValueError:
            day = None
        if day is None or not 1900 <= day.year <= 2199:    # außerhalb: 422 statt Überlauf (500)
            raise HTTPException(422, "Ungültiges Datum (JJJJ-MM-TT)")
        return monday_of(day)
    if week_no is not None:
        return monday_of_week_no(school.settings, week_no, today)
    if week is not None:
        return monday_of_week_no(school.settings, week + 1, today)
    return monday_of(today)


@router.get("/timetable/{kind}/{ref}")
def view(kind: Kind, ref: str, week: Optional[int] = Query(None, ge=0, le=52),
         week_no: Optional[int] = Query(None, ge=-60, le=120), date_: Optional[str] = Query(None, alias="date"),
         all_days: bool = Query(True), user: AuthUser = Depends(current_user)):
    """Wochenraster für Klasse, Lehrkraft, Raum oder Schüler/in.

    Woche: ``date`` (ein Tag der Woche, kanonisch), ``week_no`` (laufende Woche des aktuellen Schuljahres) oder alt
    ``week`` (0-basiert, = Woche ``week + 1``); ohne Angabe die heutige Woche. ``all_days=0`` zeigt nur Mo … bis zum
    letzten Tag mit Unterricht (mindestens Mo–Fr), sonst Mo–So. Nur in dieser Woche aktive Zellen."""
    snap = snapshot()
    check_view_access(user, kind, ref, snap)
    monday = view_monday(snap[1], date_, week_no, week)

    def compute():
        from schulmanager.timetable import timetable_view
        try:
            return timetable_view(snap[1], kind, ref, when=monday, all_days=all_days)
        except KeyError as exc:
            raise HTTPException(404, str(exc.args[0]) if exc.args else "Nicht gefunden") from None

    return cached("timetable_view", (kind, ref, monday.isoformat(), all_days), compute, snap)
