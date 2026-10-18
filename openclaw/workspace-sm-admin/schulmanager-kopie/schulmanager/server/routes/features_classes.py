"""Klassen-Seite (ARCHITECTURE.md §10.2): Suche, Personen, Klassenraum/Klassenleitung, Wochenplan und
„findet nicht statt“ mit automatischer Umstellung.

* ``GET /classes?q=&site=`` – Klassenliste (natürlich sortiert) mit Klassenraum, Klassenleitung und Zahlen
* ``GET /classes/{id}`` – Kopf, Fächer → Kurs/Kursteil → Lehrkraft, Lehrkräfte, Schüler/innen mit Kurswahl
* ``PATCH /classes/{id}`` – Klassenraum/Klassenleitung setzen (``masterdata.edit``), optional den Klassenraum
  in den Stunden der Klasse ersetzen (``apply_to_timetable``); Planungsfeld ``school_days``
  nur mit ``timetable.edit`` (409 ``plan_change`` ohne ``?force=1``)
* ``GET /classes/{id}/week?date=`` – Wochenplan einer Kalenderwoche inkl. Vertretungen und Ausfällen
* ``POST /classes/{id}/not-taking-place`` – Unterricht entfällt (``lesson``) bzw. Klasse ist nicht da
  (``class`` + Begleitlehrkräfte) mit Vorschau (``dry_run``) als Unterschied der Tagespläne vorher/nachher
* Zurücknehmen über das bestehende ``DELETE /absences/{id}``
* ``POST /classes`` – Klasse komplett anlegen (Schülerliste, optional Schüler-/Elternkonten + Zugangsbriefe, §11.3)
* ``POST /classes/{id}/students`` – Schüler/innen nachlegen (gleiches Format, Konten optional)

Sichtbarkeit wie Klassenpläne (``plan_class_ids`` / ``check_view_access``): Lehrkräfte nur eigene Klassen,
Schüler/innen, Eltern und Monitor gar nicht. Schülerlisten nur mit ``students.read`` im Scope, Abwesenheits-
gründe nur mit ``substitution.edit``.
"""
from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from schulmanager.models import Absence, Course, Lesson, Room, School, SchoolClass, Student
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, client_ip, current_user, require

from .features_common import (absence_reasons, cached, check_id, check_range, date_range, day_plan, effective_cells,
                              has, iso_dates, mutate, parse_date, plan_class_ids, snapshot, student_parts,
                              visible_student_ids)
from .features_substitutions import _absence_out, _clean_cells, _day_header, _validate_absence
from .features_timetable import check_view_access

router = APIRouter(tags=["Klassen"])

MAX_NOT_TAKING_PLACE_DAYS = 14
NO_ACCESS_ROLES = {"schueler", "eltern", "monitor"}
STAFF_PERMS = ("plans.read_all", "masterdata.edit", "substitution.edit", "timetable.edit")
WEEKDAY_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
KIND_LABELS = {"vertretung": "Vertretung", "betreuung": "Betreuung", "mitbetreuung": "Mitbetreuung",
               "entfall": "Entfall", "verlegung": "Verlegung", "raumaenderung": "Raumänderung",
               "klasse_abwesend": "Klasse abwesend", "aufsicht": "Aufsicht", "klausur": "Klausur"}
CHANGE_ORDER = {"added": 0, "changed": 1, "removed": 2}


# =================================================================== Hilfen
def _natural(value: str) -> tuple:
    """Natürliche Sortierung („5a“ < „10a“ < „Q1-1“); Positionen abwechselnd Text/Zahl."""
    return tuple(int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", value or ""))


def _guard(user) -> None:
    """Klassen-Seite nur für Personal mit Planzugriff; Schüler/innen, Eltern, Monitor → 403."""
    if getattr(user, "role", "") in NO_ACCESS_ROLES or not any(has(user, p) for p in STAFF_PERMS):
        raise HTTPException(403, "Keine Berechtigung für die Klassenansicht")


def _class_or_404(school: School, class_id: str) -> SchoolClass:
    cls = school.index("classes").get(class_id)
    if cls is None:
        raise HTTPException(404, f"Klasse „{class_id}“ nicht gefunden")
    return cls


def _named(items: dict, ref: Optional[str]) -> Optional[dict]:
    if not ref:
        return None
    obj = items.get(ref)
    return {"id": ref, "name": getattr(obj, "name", "") or ref}


def _student_count(school: School, cls: SchoolClass) -> int:
    """Schülerzahl: erfasste Schüler/innen, sonst die geplante Klassenstärke (``SchoolClass.students``)."""
    return sum(1 for s in school.students if s.class_id == cls.id) or int(cls.students or 0)


def _course_label(course: Course, part: Optional[int]) -> str:
    """Kursbezeichnung wie ``ref_name`` der Abwesenheiten: bei mehreren Teilen mit Kursteil („Religion 7a+7b – ev“)."""
    name = course.label or course.id
    if part is not None and len(course.parts) > 1 and 0 <= part < len(course.parts):
        p = course.parts[part]
        name += f" – {p.label or p.subject}"
    return name


def _slot_text(school: School, les: Lesson, course: Optional[Course]) -> str:
    """„Di 3.–4. Std. (Woche 1)“"""
    from schulmanager.timetable import weeks_text
    span = f"{les.start + 1}." + (f"–{les.start + les.length}." if les.length > 1 else "")
    text = f"{WEEKDAY_SHORT[les.day % 7]} {span} Std."
    from schulmanager.weeks import WeekLabels
    wt = weeks_text(les, course, WeekLabels(school.settings))
    if wt != "jede Woche":
        text += f" ({wt})"
    return text


def _de_date(d: date, weekday: bool = False) -> str:
    return (f"{WEEKDAY_SHORT[d.weekday()]}, " if weekday else "") + d.strftime("%d.%m.%Y")


def _when(d1: date, d2: date) -> str:
    if d1 == d2:
        return f"am {_de_date(d1, weekday=True)}"
    head = d1.strftime("%d.%m.") if d1.year == d2.year else _de_date(d1)
    return f"vom {head} bis {_de_date(d2)}"


def _periods_text(periods: list[int]) -> str:
    return ", ".join(f"{p + 1}." for p in sorted(periods)) + " Std." if periods else ""


# =================================================================== Ausgabe
def _class_info(school: School, cls: SchoolClass) -> dict:
    rooms, teachers, sites = school.index("rooms"), school.index("teachers"), school.index("sites")
    room = rooms.get(cls.home_room) if cls.home_room else None
    home = None
    if cls.home_room:
        home = {"id": cls.home_room, "name": room.name if room else cls.home_room,
                "type": room.type if room else "", "capacity": room.capacity if room else 0,
                "site": room.site if room else ""}
    site = sites.get(cls.site)
    from schulmanager.calendar_utils import class_days
    from schulmanager.rules import exam_limits_for_class, exam_limits_text
    days = class_days(school, cls)
    limits = exam_limits_for_class(school, cls)
    return {"id": cls.id, "name": cls.name, "grade": cls.grade, "site": cls.site,
            "site_name": site.name if site else "", "max_periods_per_day": cls.max_periods_per_day,
            "unavailable": [r.to_dict() for r in cls.unavailable], "home_room": home,
            "class_teacher": _named(teachers, cls.class_teacher),
            "profile": _named(school.index("grade_profiles"), cls.profile),
            "school_days": list(cls.school_days),
            "plan": {"school_days": days, "text": f"{'Standard' if not cls.school_days else 'Eigene Tage'} · {_days_text(days)}"},
            "max_exams_per_week": cls.max_exams_per_week, "max_exams_per_day": cls.max_exams_per_day,
            "exam_limits": {**limits, "text": exam_limits_text(limits)}}


def _days_text(days: list[int]) -> str:
    """„Mo–Fr“, „Mo, Di, Sa“."""
    if len(days) > 2 and days == list(range(days[0], days[-1] + 1)):
        return f"{WEEKDAY_SHORT[days[0]]}–{WEEKDAY_SHORT[days[-1]]}"
    return ", ".join(WEEKDAY_SHORT[d] for d in days)


def _overview(snap) -> list[dict]:
    """Alle Klassen (natürlich sortiert) mit Zahlen – pro Planversion gecacht (nicht verändern!)."""
    def compute():
        school = snap[1]
        rooms, teachers, sites = school.index("rooms"), school.index("teachers"), school.index("sites")
        n_students = Counter(s.class_id for s in school.students)
        n_courses: Counter = Counter()
        class_teachers: dict[str, set[str]] = defaultdict(set)
        for c in school.courses:
            for cid in set(c.classes):
                n_courses[cid] += 1
                class_teachers[cid].update(p.teacher for p in c.parts if p.teacher)
        rows = []
        for cls in sorted(school.classes, key=lambda c: _natural(c.name or c.id)):
            ts = class_teachers.get(cls.id, set()) | ({cls.class_teacher} if cls.class_teacher else set())
            site = sites.get(cls.site)
            rows.append({"id": cls.id, "name": cls.name, "grade": cls.grade, "site": cls.site,
                         "site_name": site.name if site else "", "home_room": _named(rooms, cls.home_room),
                         "class_teacher": _named(teachers, cls.class_teacher),
                         "student_count": n_students.get(cls.id) or int(cls.students or 0),
                         "course_count": n_courses.get(cls.id, 0), "teacher_count": len(ts)})
        return rows

    return cached("classes_overview", (), compute, snap)


def _matches(row: dict, q: str) -> bool:
    hay = [row["id"], row["name"]]
    for key in ("home_room", "class_teacher"):
        if row.get(key):
            hay += [row[key]["id"], row[key]["name"]]
    return any(q in (h or "").lower() for h in hay)


def _subject_rows(school: School, cls: SchoolClass) -> list[dict]:
    """Fächer → Kurs/Kursteil → Lehrkraft (ein Eintrag je Kursteil)."""
    subjects, teachers = school.index("subjects"), school.index("teachers")
    rows = []
    for course in school.courses:
        if cls.id not in course.classes:
            continue
        multi = len(course.parts) > 1
        for i, p in enumerate(course.parts):
            subj = subjects.get(p.subject)
            rows.append({"course_id": course.id, "part": i if multi else None,
                         "label": _course_label(course, i if multi else None), "subject": p.subject,
                         "subject_name": subj.name if subj else p.subject, "teacher": _named(teachers, p.teacher),
                         "hours": course.hours, "classes": list(course.classes),
                         "coupled": multi or len(course.classes) > 1})
    rows.sort(key=lambda r: (r["subject_name"].lower(), _natural(r["label"]), r["part"] or 0))
    return rows


def _teacher_rows(school: School, cls: SchoolClass, subjects: list[dict]) -> list[dict]:
    teachers = school.index("teachers")
    out: dict[str, dict] = {}

    def row(tid: str) -> dict:
        if tid not in out:
            t = teachers.get(tid)
            out[tid] = {"id": tid, "name": t.name if t else tid, "is_class_teacher": tid == cls.class_teacher,
                        "subjects": [], "hours": 0}
        return out[tid]

    if cls.class_teacher:
        row(cls.class_teacher)
    for s in subjects:
        if not s["teacher"]:
            continue
        r = row(s["teacher"]["id"])
        if s["subject"] not in r["subjects"]:
            r["subjects"].append(s["subject"])
        r["hours"] += int(s["hours"] or 0)
    return sorted(out.values(), key=lambda r: (not r["is_class_teacher"], r["name"].lower(), r["id"]))


def _student_rows(user, school: School, cls: SchoolClass, snap) -> Optional[list[dict]]:
    from .features_parent_access import may_set_birth_date

    """Schüler/innen mit Kurswahl (nur echte Wahlen in Kursen mit mehreren Teilen) – ``None`` ohne ``students.read``."""
    if not has(user, "students.read"):
        return None
    vis = visible_student_ids(user, snap)
    courses = school.index("courses")
    out = []
    for s in school.students:
        if s.class_id != cls.id or (vis is not None and s.id not in vis):
            continue
        chosen = []
        for cid, sel in student_parts(s.id, snap).items():
            course = courses.get(cid)
            if course is None or len(course.parts) <= 1 or len(sel) >= len(course.parts):
                continue
            chosen += [{"course_id": cid, "part": p, "label": _course_label(course, p)} for p in sel]
        chosen.sort(key=lambda c: _natural(c["label"]))
        row = {"id": s.id, "name": s.name, "courses": chosen}
        if may_set_birth_date(user, s.id, snap):   # Geburtsdatum nur für Berechtigte (Recht „Geburtsdatum pflegen“)
            row.update(birth_date=s.birth_date or None, can_set_birth_date=True)
        out.append(row)
    if vis is not None and not out and any(s.class_id == cls.id for s in school.students):
        return None
    return sorted(out, key=lambda s: (s["name"].lower(), s["id"]))


def _room_choices(school: School, cls: SchoolClass) -> list[dict]:
    home_of: dict[str, list[str]] = defaultdict(list)
    for c in school.classes:
        if c.home_room:
            home_of[c.home_room].append(c.id)
    rooms = sorted(school.rooms, key=lambda r: (bool(cls.site) and r.site != cls.site, r.type != "Klassenraum",
                                                _natural(r.name or r.id)))
    return [{"id": r.id, "name": r.name, "type": r.type, "site": r.site, "capacity": r.capacity,
             "home_of": sorted(home_of.get(r.id, []), key=_natural)} for r in rooms]


# =================================================================== Liste & Detail
@router.get("/classes")
def list_classes(q: Optional[str] = Query(None, max_length=100), site: Optional[str] = None,
                 user: AuthUser = Depends(current_user)):
    """Klassen suchen (Name, Klassenleitung, Klassenraum) und nach Standort filtern; Lehrkräfte: eigene Klassen."""
    _guard(user)
    snap = snapshot()
    allowed = plan_class_ids(user, snap)
    ql = (q or "").strip().lower()
    rows = [r for r in _overview(snap)
            if (allowed is None or r["id"] in allowed) and (not site or r["site"] == site)
            and (not ql or _matches(r, ql))]
    return {"classes": rows, "can_edit": has(user, "masterdata.edit"), "can_plan": has(user, "substitution.edit")}


@router.get("/classes/{class_id}")
def class_detail(class_id: str, user: AuthUser = Depends(current_user)):
    """Kopf, Fächer/Kursteile mit Lehrkräften, Lehrkräfte der Klasse, Schüler/innen (mit ``students.read``)."""
    _guard(user)
    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    school = snap[1]
    cls = _class_or_404(school, class_id)
    subjects = _subject_rows(school, cls)
    can_edit = has(user, "masterdata.edit")
    out = {"class": _class_info(school, cls), "subjects": subjects,
           "teachers": _teacher_rows(school, cls, subjects), "students": _student_rows(user, school, cls, snap),
           "student_count": _student_count(school, cls), "can_edit": can_edit,
           "can_plan": has(user, "substitution.edit"), "can_edit_plan": has(user, "timetable.edit"),
           "version": snap[0]}
    if can_edit:
        out["room_choices"] = _room_choices(school, cls)
        out["teacher_choices"] = [{"id": t.id, "name": t.name}
                                  for t in sorted(school.teachers, key=lambda t: (t.name.lower(), t.id))]
    return out


# =================================================================== Klassenraum / Klassenleitung
class ClassPatchIn(BaseModel):
    home_room: Optional[str] = Field(None, max_length=64)
    class_teacher: Optional[str] = Field(None, max_length=64)
    apply_to_timetable: bool = False
    # Planungsfelder (V12, nur mit ``timetable.edit``)
    school_days: Optional[list[int]] = Field(None, max_length=7)
    # Klassenarbeiten je Woche/Tag (``masterdata.edit``); ``exam_limits_inherit`` = Werte löschen → Vorgabe gilt
    max_exams_per_week: Optional[int] = Field(None, ge=0, le=20)
    max_exams_per_day: Optional[int] = Field(None, ge=0, le=5)
    exam_limits_inherit: bool = False
    # Jahrgang/Profil (``masterdata.edit`` oder ``timetable.edit``); ``""``/null = keine Zuordnung
    profile: Optional[str] = Field(None, max_length=64)


def _room_warnings(school: School, cls: SchoolClass, room: Room) -> list[str]:
    out = []
    others = sorted((c.name or c.id for c in school.classes if c.id != cls.id and c.home_room == room.id),
                    key=_natural)
    if others:
        out.append(f"{room.name} ist schon Klassenraum von {', '.join(others)}")
    if room.site and cls.site and room.site != cls.site:
        sites = school.index("sites")
        rs, cs = sites.get(room.site), sites.get(cls.site)
        out.append(f"{room.name} liegt an einem anderen Standort ({rs.name if rs else room.site}) "
                   f"als die Klasse ({cs.name if cs else cls.site})")
    n = _student_count(school, cls)
    if room.capacity and n > room.capacity:
        out.append(f"{room.name} hat nur {room.capacity} Plätze für {n} Schüler/innen")
    if room.type != "Klassenraum":
        out.append(f"{room.name} ist kein Klassenraum (Raumtyp „{room.type}“)")
    return out


def _teacher_warnings(school: School, cls: SchoolClass, tid: str) -> list[str]:
    t = school.index("teachers").get(tid)
    name = t.name if t else tid
    out = []
    if not any(cls.id in c.classes and any(p.teacher == tid for p in c.parts) for c in school.courses):
        out.append(f"{name} unterrichtet die Klasse {cls.name} bisher nicht")
    others = sorted((c.name or c.id for c in school.classes if c.id != cls.id and c.class_teacher == tid),
                    key=_natural)
    if others:
        out.append(f"{name} ist schon Klassenleitung von {', '.join(others)}")
    return out


def _apply_room(school: School, cls: SchoolClass, old: str, new: str) -> tuple[int, list[str]]:
    """Ersetzt in Stunden von Kursen **nur dieser Klasse** den alten Klassenraum durch den neuen, wo der neue Raum zur
    selben Zeit (Tag/Stunde/Woche) frei ist. Rückgabe: (geänderte Stunden, übersprungene als Text)."""
    courses = school.index("courses")
    occupied: dict[tuple[int, int, int], str] = {}

    from schulmanager.weeks import PlanWeeks
    pw = PlanWeeks(school)

    def slots(les: Lesson, course: Optional[Course]) -> list[tuple[int, int, int]]:
        return [(w, les.day, p) for w in pw.lesson_groups(les, course)
                for p in range(les.start, les.start + max(1, les.length))]

    for les in school.lessons:
        if new in les.rooms:
            course = courses.get(les.course_id)
            label = _course_label(course, None) if course else les.course_id
            for s in slots(les, course):
                occupied.setdefault(s, label)
    moved, skipped = 0, []
    for les in sorted(school.lessons, key=lambda le: (le.day, le.start, le.id)):
        course = courses.get(les.course_id)
        if course is None or set(course.classes) != {cls.id}:
            continue
        idx = [i for i, r in enumerate(les.rooms) if r == old]
        if not idx:
            continue
        mine = slots(les, course)
        clash = next((occupied[s] for s in mine if s in occupied), None)
        if clash is not None:
            skipped.append(f"{_slot_text(school, les, course)} {_course_label(course, None)}: "
                           f"Raum ist dann belegt ({clash})")
            continue
        for i in idx:
            les.rooms[i] = new
        for s in mine:
            occupied[s] = _course_label(course, None)
        moved += 1
    return moved, skipped


@router.patch("/classes/{class_id}")
def patch_class(class_id: str, body: ClassPatchIn, force: bool = Query(False),
                user: AuthUser = Depends(current_user)):
    """Klassenraum und/oder Klassenleitung setzen (nur übergebene Felder; ``null`` entfernt, ``masterdata.edit``).

    Mit ``apply_to_timetable`` wird der alte Klassenraum in den Stunden der Klasse ersetzt (wo der neue frei ist).
    Das Planungsfeld ``school_days`` (leer = Schulvorgabe) braucht ``timetable.edit``; Stunden an entfallenen Tagen
    → 409 ``plan_change`` (``?force=1`` übernimmt)."""
    from .features_data import (CLASS_PLAN_FIELDS, PLAN_FIELDS_403, class_plan_change, class_plan_errors)

    fields = set(body.model_fields_set)
    exam_fields = {f for f in ("max_exams_per_week", "max_exams_per_day") if f in fields}
    if body.exam_limits_inherit:
        exam_fields |= {"max_exams_per_week", "max_exams_per_day"}
        fields |= exam_fields
    plan_fields = [f for f in CLASS_PLAN_FIELDS if f in fields and getattr(body, f) is not None]
    set_profile = "profile" in fields
    if set_profile and not (has(user, "masterdata.edit") or has(user, "timetable.edit")):
        raise HTTPException(403, "Keine Berechtigung")
    if (fields - set(CLASS_PLAN_FIELDS) - {"profile"}) and not has(user, "masterdata.edit"):
        raise HTTPException(403, "Keine Berechtigung")
    if (fields & set(CLASS_PLAN_FIELDS)) and not has(user, "timetable.edit"):   # auch mit ``null``
        raise HTTPException(403, PLAN_FIELDS_403)
    if not fields:
        need_any = has(user, "masterdata.edit") or has(user, "timetable.edit")
        if not need_any:
            raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    set_room, set_teacher = "home_room" in fields, "class_teacher" in fields
    new_room = (body.home_room or "").strip() or None
    new_teacher = (body.class_teacher or "").strip() or None

    def fn(school: School):
        cls = _class_or_404(school, class_id)
        warnings: list[str] = []
        moved, skipped = 0, []
        changes: list[dict] = []
        if plan_fields:
            import copy as _copy
            old = _copy.deepcopy(cls)
            for f in plan_fields:
                value = getattr(body, f)
                setattr(cls, f, sorted(set(value)) if f == "school_days" else value)
            errs = class_plan_errors(cls)
            if errs:
                raise HTTPException(422, "; ".join(errs))
            changes = [{k: v for k, v in c.items() if k != "exact"}
                       for c in class_plan_change(school, old, cls, force)]
        if set_room:
            room = school.index("rooms").get(new_room) if new_room else None
            if new_room and room is None:
                raise HTTPException(422, f"Raum „{new_room}“ existiert nicht")
            old = cls.home_room
            cls.home_room = new_room
            if room is not None:
                warnings += _room_warnings(school, cls, room)
                if body.apply_to_timetable and old and old != new_room:
                    moved, skipped = _apply_room(school, cls, old, new_room)
        if set_teacher:
            if new_teacher and new_teacher not in school.index("teachers"):
                raise HTTPException(422, f"Lehrkraft „{new_teacher}“ existiert nicht")
            cls.class_teacher = new_teacher
            if new_teacher:
                warnings += _teacher_warnings(school, cls, new_teacher)
        for f in exam_fields:     # Klassenarbeiten je Woche/Tag: Zahl = eigener Wert, null/inherit = Vorgabe
            setattr(cls, f, None if body.exam_limits_inherit else getattr(body, f))
        if set_profile:
            new_profile = (body.profile or "").strip() or None
            if new_profile and new_profile not in school.index("grade_profiles"):
                raise HTTPException(422, f"Jahrgang „{new_profile}“ existiert nicht")
            cls.profile = new_profile
        return {"class": _class_info(school, cls), "warnings": warnings, "moved_lessons": moved, "skipped": skipped,
                "changes": changes}

    what = []
    if set_room:
        what.append(f"Klassenraum {new_room or '–'}" + (" (auch im Stundenplan)" if body.apply_to_timetable else ""))
    if set_teacher:
        what.append(f"Klassenleitung {new_teacher or '–'}")
    if plan_fields:
        what.append("Planung (Unterrichtstage)")
    if exam_fields:
        what.append("Klassenarbeiten je Woche/Tag" + (" (Vorgabe)" if body.exam_limits_inherit else ""))
    if set_profile:
        what.append(f"Jahrgang {body.profile or '–'}")
    message = f"Klasse {class_id}: " + (", ".join(what) or "keine Änderung")
    scope = ["classes", "timetable", "substitutions"] + (["courses"] if plan_fields else [])         + (["curricula"] if set_profile else [])
    return mutate(user, message, fn, scope=scope)


# =================================================================== Stundentafel der Klasse
class CurriculumEntryIn(BaseModel):
    subject: str = Field(min_length=1, max_length=40)
    hours: int = Field(ge=0, le=20)
    double: bool = False


class ClassCurriculumIn(BaseModel):
    entries: list[CurriculumEntryIn] = Field(default_factory=list, max_length=60)


def _can_edit_curriculum(user, cls: SchoolClass) -> bool:
    """Stammdaten/Planung oder die Klassenleitung dieser Klasse."""
    if has(user, "masterdata.edit") or has(user, "timetable.edit"):
        return True
    tid = getattr(user, "teacher_id", None)
    return bool(tid and cls.class_teacher == tid)


def _curriculum_out(school: School, cls: SchoolClass, user) -> dict:
    from schulmanager.planning import class_curriculum_id, curriculum_for_class, effective_entries, resolve_curricula

    cur = curriculum_for_class(school, cls.id)
    subjects = school.index("subjects")
    own = cur is not None and cur.id == class_curriculum_id(cls.id) or (cur is not None and cls.id in cur.classes)
    res = resolve_curricula(school).get(cls.id, {})
    prof = school.index("grade_profiles").get(cls.profile or "")
    courses = [c for c in school.courses if cls.id in c.classes]
    per_subject: dict[str, dict] = {}
    for c in courses:
        for p in c.parts:
            d = per_subject.setdefault(p.subject, {"courses": 0, "hours": 0, "teachers": set()})
            d["courses"] += 1
            d["hours"] = max(d["hours"], c.hours)
            if p.teacher:
                d["teachers"].add(p.teacher)
    entries = []
    for e in effective_entries(school, cur):
        info = per_subject.get(e.subject, {})
        entries.append({"subject": e.subject, "subject_name": subjects[e.subject].name if e.subject in subjects
                        else e.subject, "hours": e.hours, "double": e.double,
                        "teachers": sorted(info.get("teachers", set()))})
    return {
        "class_id": cls.id, "class_name": cls.name, "grade": cls.grade,
        "source": "class" if own else res.get("source") if cur is not None else None,
        "profile": ({"id": prof.id, "name": prof.name, "color": prof.color} if prof else None),
        "curriculum_id": cur.id if cur else None, "curriculum_name": cur.name if cur else None,
        "entries": entries, "total_hours": sum(e["hours"] for e in entries),
        "subjects": sorted(({"id": s.id, "name": s.name, "room_type": s.room_type} for s in school.subjects),
                           key=lambda x: x["name"].lower()),
        "can_edit": _can_edit_curriculum(user, cls),
    }


@router.get("/classes/{class_id}/curriculum")
def get_class_curriculum(class_id: str, user: AuthUser = Depends(current_user)):
    """Stundentafel der Klasse: Fach → Wochenstunden (eigene Tafel der Klasse oder die des Jahrgangs)."""
    _guard(user)
    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    school = snap[1]
    return _curriculum_out(school, _class_or_404(school, class_id), user)


@router.put("/classes/{class_id}/curriculum")
def put_class_curriculum(class_id: str, body: ClassCurriculumIn, user: AuthUser = Depends(current_user)):
    """Eigene Stundentafel der Klasse speichern (Stammdaten/Planung oder Klassenleitung). Die Kurse der Klasse werden
    sofort angepasst und Lehrkräfte zugewiesen; der Auto-Planer legt neue/fehlende Stunden in den Stundenplan.
    Leere Liste = eigene Tafel entfernen (es gilt wieder die Jahrgangs-Stundentafel)."""
    from schulmanager.models import CurriculumEntry
    from schulmanager.planning import set_class_curriculum

    _guard(user)
    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    if not _can_edit_curriculum(user, _class_or_404(snap[1], class_id)):
        raise HTTPException(403, "Die Stundentafel ändern Stammdaten/Planung oder die Klassenleitung")
    seen: set[str] = set()
    entries = []
    for e in body.entries:
        if e.subject in seen:
            raise HTTPException(422, f"Fach {e.subject} steht doppelt in der Stundentafel")
        seen.add(e.subject)
        if e.hours > 0:
            entries.append(CurriculumEntry(subject=e.subject, hours=e.hours, double=e.double))

    def fn(school: School):
        cls = _class_or_404(school, class_id)
        subjects = school.index("subjects")
        unknown = [e.subject for e in entries if e.subject not in subjects]
        if unknown:
            raise HTTPException(422, "Unbekannte Fächer: " + ", ".join(unknown))
        result = set_class_curriculum(school, class_id, entries)
        return {**result, "curriculum": _curriculum_out(school, cls, user)}

    total = sum(e.hours for e in entries)
    message = (f"Klasse {class_id}: Stundentafel gespeichert ({len(entries)} Fächer, {total} Wochenstunden)"
               if entries else f"Klasse {class_id}: eigene Stundentafel entfernt")
    return mutate(user, message, fn, scope=["curricula", "courses", "timetable"])


# =================================================================== Wochenplan
def _absence_row(a: Absence, user, school: School) -> dict:
    d = _absence_out(a, user, school)
    row = {k: d[k] for k in ("id", "kind", "ref", "ref_name", "date_from", "date_to", "periods")}
    editor = has(user, "substitution.edit")
    if editor:
        row["reason"] = d.get("reason", "")
    row["can_delete"] = editor
    return row


def _week_absences(user, school: School, cls: SchoolClass, d1: date, d2: date) -> list[dict]:
    """Klassen-Abwesenheiten der Klasse und ``lesson``-Abwesenheiten ihrer Kurse im Zeitraum; mit
    ``substitution.edit`` zusätzlich die Begleitungen („Begleitung <Klasse>“, Lehrkraft-Abwesenheiten)."""
    from schulmanager.substitution import split_lesson_ref

    courses = school.index("courses")
    escort = re.compile(rf"^Begleitung\s+({re.escape(cls.name)}|{re.escape(cls.id)})(?![\w-])")
    editor = has(user, "substitution.edit")
    out = []
    for a in school.absences:
        try:
            if date.fromisoformat(a.date_to) < d1 or date.fromisoformat(a.date_from) > d2:
                continue
        except ValueError:
            continue
        if a.kind == "class":
            ok = a.ref == cls.id
        elif a.kind == "lesson":
            try:
                course = courses.get(split_lesson_ref(a.ref)[0])
            except ValueError:
                course = None
            ok = course is not None and cls.id in course.classes
        else:
            ok = editor and a.kind == "teacher" and bool(escort.match(a.reason or ""))
        if ok:
            out.append(_absence_row(a, user, school))
    rank = {"class": 0, "lesson": 1, "teacher": 2}
    out.sort(key=lambda x: (x["date_from"], rank.get(x["kind"], 9), x["periods"][:1], x["ref"], x["id"]))
    return out


@router.get("/classes/{class_id}/week")
def class_week(class_id: str, date_: Optional[str] = Query(None, alias="date"),
               user: AuthUser = Depends(current_user)):
    """Wochenplan der Kalenderwoche von ``date`` (Standard: heute) inkl. Vertretungen, Entfall, Verlegungen."""
    _guard(user)
    day = parse_date(date_)
    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    school = snap[1]
    cls = _class_or_404(school, class_id)
    from schulmanager.calendar_utils import class_days, day_kind, week_info
    st = school.settings
    monday = day - timedelta(days=day.weekday())
    editor = has(user, "substitution.edit")
    teaching = class_days(school, cls)
    days = []
    for i in range(7):               # immer Mo–So (§14.6); Tage ohne Unterricht der Klasse ohne Einträge
        d = monday + timedelta(days=i)
        _, plan = day_plan(d, snap)
        cells: list[dict] = []
        kind = day_kind(school, d, cls)
        if not plan.get("holiday") and i in teaching:
            reasons = [] if editor else absence_reasons(school, d)
            cells = _clean_cells(effective_cells(d, "class", class_id, snap), reasons)
        head = _day_header(school, d, plan)
        if kind == "kein_unterrichtstag" and not head.get("holiday"):
            head["holiday"] = "Kein Unterricht"
        days.append({**head, "cells": cells, "day_kind": kind, "has_items": bool(cells)})
    return {"class_id": class_id, "week_start": monday.isoformat(),
            "week_info": week_info(school, monday, cls),
            "periods": st.periods, "period_times": st.period_times[:st.periods], "days": days,
            "absences": _week_absences(user, school, cls, monday, monday + timedelta(days=6)),
            "can_plan": editor, "version": snap[0]}


# =================================================================== Findet nicht statt
class NotTakingPlaceIn(BaseModel):
    mode: Literal["lesson", "class"]
    date_from: date
    date_to: Optional[date] = None
    periods: list[int] = Field(default_factory=list, max_length=16)
    course_id: Optional[str] = Field(None, max_length=64)
    part: Optional[int] = Field(None, ge=0)
    reason: str = Field(max_length=500)
    escort_teachers: list[str] = Field(default_factory=list, max_length=30)
    dry_run: bool


def _teaching_error(school: School, d1: date, d2: date, periods: list[int], courses: list[Course],
                    what: str) -> Optional[str]:
    """Fehlertext, wenn ``courses`` im Zeitraum (in den Stunden ``periods``, leer = alle) keinen Unterricht haben."""
    from schulmanager.calendar_utils import is_school_day

    from schulmanager.weeks import ActiveIndex
    by_id = {c.id: c for c in courses}
    lessons = [le for le in school.lessons if le.course_id in by_id]
    wanted = set(periods)
    aidx = ActiveIndex(school)
    days = [d for d in date_range(d1, d2) if is_school_day(school, d)[0]]
    when = f"am {_de_date(d1)}" if d1 == d2 else f"vom {_de_date(d1)} bis {_de_date(d2)}"
    if not days:
        reason = is_school_day(school, d1)[1] if d1 == d2 else "keine Schultage"
        return f"{when[0].upper()}{when[1:]} findet kein Unterricht statt ({reason})"
    for d in days:
        for le in lessons:
            if not aidx.active_on(le, by_id[le.course_id], d):
                continue
            if not wanted or wanted & set(range(le.start, le.start + max(1, le.length))):
                return None
    per = f" in der {_periods_text(periods)}" if periods else ""
    return f"{what} hat {when}{per} keinen Unterricht"


def _add_absences(school: School, class_id: str, body: NotTakingPlaceIn, d1: date,
                  d2: date) -> tuple[list[tuple[Absence, bool]], str]:
    """Legt die Abwesenheiten in ``school`` an (geprüft, ohne Duplikate).

    Rückgabe: ``[(Absence, schon_vorhanden)]`` und eine Beschreibung für Zusammenfassung/Verlauf."""
    cls = _class_or_404(school, class_id)
    periods = sorted(set(body.periods))
    reason = body.reason.strip()
    teachers = school.index("teachers")
    specs: list[tuple[str, str, str]] = []
    if body.mode == "lesson":
        if body.escort_teachers:
            raise HTTPException(422, "Begleitlehrkräfte gibt es nur bei „Klasse ist nicht da“")
        cid = (body.course_id or "").strip()
        if not cid:
            raise HTTPException(422, "Bitte den Kurs angeben, der nicht stattfindet")
        course = school.index("courses").get(cid)
        if course is None:
            raise HTTPException(422, f"Kurs „{cid}“ existiert nicht")
        if class_id not in course.classes:
            raise HTTPException(422, f"Kurs „{course.label or course.id}“ gehört nicht zur Klasse {cls.name}")
        part = body.part
        if part is not None and len(course.parts) == 1 and part == 0:
            part = None                      # Kurs ohne Teilung: ganzer Kurs
        ref = course.id if part is None else f"{course.id}#{part}"
        specs.append(("lesson", ref, reason))
        check = ([course], f"„{_course_label(course, part)}“")
        desc = f"„{_course_label(course, part)}“ findet {_when(d1, d2)}"
        desc += (f" ({_periods_text(periods)})" if periods else "") + " nicht statt"
    else:
        escorts = list(dict.fromkeys(t.strip() for t in body.escort_teachers if t.strip()))
        for tid in escorts:
            if tid not in teachers:
                raise HTTPException(422, f"Lehrkraft „{tid}“ existiert nicht")
        specs.append(("class", cls.id, reason))
        specs += [("teacher", tid, f"Begleitung {cls.name}") for tid in escorts]
        check = ([c for c in school.courses if class_id in c.classes], f"Klasse {cls.name}")
        desc = f"Klasse {cls.name} ist {_when(d1, d2)}" + (f" ({_periods_text(periods)})" if periods else "")
        desc += " nicht da"
        if escorts:
            desc += " – Begleitung: " + ", ".join(teachers[t].name or t for t in escorts)
    taken = {a.id for a in school.absences}
    pending: list[Absence] = []
    for kind, ref, why in specs:
        n = len(taken) + 1
        while f"A{n}" in taken:
            n += 1
        taken.add(f"A{n}")
        a = Absence(id=f"A{n}", kind=kind, ref=ref, date_from=d1.isoformat(), date_to=d2.isoformat(),
                    periods=list(periods), reason=why)
        _validate_absence(school, a)
        pending.append(a)
    err = _teaching_error(school, d1, d2, periods, *check)
    if err:
        raise HTTPException(422, err)
    out: list[tuple[Absence, bool]] = []
    for a in pending:
        key = (a.kind, a.ref, a.date_from, a.date_to, sorted(a.periods))
        dup = next((x for x in school.absences
                    if (x.kind, x.ref, x.date_from, x.date_to, sorted(x.periods)) == key), None)
        if dup is not None:
            out.append((dup, True))
        else:
            school.absences.append(a)
            out.append((a, False))
    return out, desc


def _change(e: dict, op: str) -> dict:
    """Änderung im Vertretungsplan (Vertragsfelder + ``op``, ``moved_from`` und Zusatzfelder)."""
    return {"kind": e.get("kind"), "classes": list(e.get("classes") or []), "period": e.get("period", 0),
            "subject": e.get("subject"), "teacher": e.get("teacher"), "substitute": e.get("substitute"),
            "room": e.get("new_room") or e.get("room"), "note": e.get("note") or "",
            "moved_from": e.get("moved_from"), "op": op, "period_label": e.get("period_label"),
            "time": e.get("time"), "lesson_id": e.get("lesson_id"), "part": e.get("part", 0),
            "warning": bool(e.get("warning")), "dropped": bool(e.get("dropped")), "entry_id": e.get("id")}


def _diff(before: dict, after: dict) -> list[dict]:
    """Geänderte/neue Einträge (``added``/``changed``) und weggefallene (``removed``) – alle Klassen."""
    old = {e.get("id"): e for e in before.get("entries") or []}
    new = {e.get("id"): e for e in after.get("entries") or []}
    out = [_change(e, "added" if eid not in old else "changed") for eid, e in new.items() if old.get(eid) != e]
    out += [_change(e, "removed") for eid, e in old.items() if eid not in new]
    out.sort(key=lambda c: (c["period"], _natural(c["classes"][0] if c["classes"] else "~"),
                            CHANGE_ORDER[c["op"]], c["lesson_id"] or "", c["part"]))
    return out


def _preview(before: dict[str, dict], after: dict[str, dict]) -> list[dict]:
    out = []
    for iso in sorted(after):
        b, a = before.get(iso) or {}, after[iso]
        if a.get("holiday"):
            continue
        warnings = [w for w in a.get("warnings") or [] if w not in set(b.get("warnings") or [])]
        out.append({"date": iso, "weekday": date.fromisoformat(iso).weekday(), "changes": _diff(b, a),
                    "warnings": warnings})
    return out


def _summary(desc: str, preview: list[dict], class_id: str, *, dry_run: bool, duplicate: bool) -> str:
    changes = [c for d in preview for c in d["changes"]]
    if not changes:
        text = f"{desc} – keine Änderungen im Vertretungsplan"
    else:
        days = sum(1 for d in preview if d["changes"])
        text = f"{desc} – {len(changes)} {'Änderung' if len(changes) == 1 else 'Änderungen'} im Vertretungsplan"
        if days > 1:
            text += f" an {days} Tagen"
        counts = Counter(c["kind"] for c in changes if c["op"] != "removed")
        if counts:
            order = list(KIND_LABELS)
            kinds = sorted(counts, key=lambda k: order.index(k) if k in order else 99)
            text += " (" + ", ".join(f"{counts[k]}× {KIND_LABELS.get(k, k)}" for k in kinds) + ")"
        others = sorted({k for c in changes for k in c["classes"] if k != class_id}, key=_natural)
        if others:
            text += "; auch betroffen: " + ", ".join(others)
    text += "."
    if duplicate:
        text += " War bereits erfasst."
    if dry_run:
        text += " Vorschau – noch nichts gespeichert."
    return text


@router.post("/classes/{class_id}/not-taking-place")
def not_taking_place(class_id: str, body: NotTakingPlaceIn,
                     user: AuthUser = Depends(require("substitution.edit"))):
    """Unterricht eines Kurses/Kursteils entfällt (``mode=lesson``) bzw. die Klasse ist nicht da (``mode=class``,
    Begleitlehrkräfte werden als abwesend eingetragen) – der Vertretungsplan stellt automatisch um.

    ``dry_run=true`` speichert nichts und liefert nur die Vorschau (Unterschied der Tagespläne vorher/nachher,
    auch anderer Klassen). Höchstens 14 Tage; 422, wenn an den Tagen kein Unterricht stattfindet."""
    from schulmanager.server.store import copy_school
    from schulmanager.substitution import compute_range

    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    d1 = body.date_from
    d2 = body.date_to or d1
    check_range(d1, d2, MAX_NOT_TAKING_PLACE_DAYS)
    from schulmanager.calendar_utils import open_days
    open_ = set(open_days(snap[1]))
    days = [d for d in date_range(d1, d2) if d.weekday() in open_]

    if body.dry_run:
        work = copy_school(snap[1])
        created, desc = _add_absences(work, class_id, body, d1, d2)
        after = {p.date.isoformat(): p.to_dict() for p in compute_range(work, d1, d2)}
        before = {d.isoformat(): day_plan(d, snap)[1] for d in days}
        preview = _preview(before, after)
        duplicate = all(dup for _, dup in created)
        return {"preview": preview, "dry_run": True,
                "summary": _summary(desc, preview, class_id, dry_run=True, duplicate=duplicate)}

    info: dict = {}

    def fn(school: School):
        created, desc = _add_absences(school, class_id, body, d1, d2)
        info["desc"] = desc
        info["duplicate"] = all(dup for _, dup in created)
        return [{**_absence_row(a, user, school), "duplicate": dup} for a, dup in created]

    label = ("Unterricht entfällt " + (body.course_id or "") if body.mode == "lesson" else f"Klasse {class_id} nicht da")
    label += f" {d1.isoformat()}" + (f"–{d2.isoformat()}" if d2 != d1 else "")
    if body.escort_teachers:
        label += " (Begleitung " + ", ".join(body.escort_teachers) + ")"
    rows = mutate(user, label, fn, scope=["absences", "substitutions"], dates=iso_dates(d1, d2))
    new_snap = snapshot()
    before = {d.isoformat(): day_plan(d, snap)[1] for d in days}
    after = {d.isoformat(): day_plan(d, new_snap)[1] for d in days}
    preview = _preview(before, after)
    return {"preview": preview, "dry_run": False, "absences": rows, "version": new_snap[0],
            "summary": _summary(info.get("desc", ""), preview, class_id, dry_run=False,
                                duplicate=bool(info.get("duplicate")))}


# =================================================================== Klasse anlegen / Schüler nachlegen (§11.3)
MAX_NEW_STUDENTS = 60
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ParentIn(BaseModel):
    name: str = Field("", max_length=200)
    email: Optional[str] = Field(None, max_length=254)


class NewStudentIn(BaseModel):
    first_name: str = Field("", max_length=100)
    last_name: str = Field("", max_length=100)
    email: Optional[str] = Field(None, max_length=254)
    birth_date: Optional[date] = None
    adult: bool = False                       # nur maßgeblich ohne Geburtsdatum
    parents: list[ParentIn] = Field(default_factory=list, max_length=2)


class AccountOptionsIn(BaseModel):
    create_student_accounts: bool = True
    create_parent_accounts: bool = False
    send_email: bool = False                  # Zugangsbriefe nach dem Anlegen sofort per E-Mail
    send_to: Literal["student", "parents", "both"] = "student"   # Ziel bei Minderjährigen (Volljährige: selbst)
    dry_run: bool = False


class ClassCreateIn(AccountOptionsIn):
    id: str = Field(max_length=64)
    name: Optional[str] = Field(None, max_length=100)
    grade: int
    site: Optional[str] = Field(None, max_length=64)
    home_room: Optional[str] = Field(None, max_length=64)
    class_teacher: Optional[str] = Field(None, max_length=64)
    students: list[NewStudentIn] = Field(default_factory=list, max_length=500)


class StudentsAddIn(AccountOptionsIn):
    students: list[NewStudentIn] = Field(max_length=500)


def _age(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _clean_students(school: School, rows: list[NewStudentIn], class_id: str) -> tuple[list[dict], list[str]]:
    """Eingabezeilen prüfen/normalisieren → ``([{index, first_name, last_name, name, email, birth_date, adult,
    parents}], warnungen)``; Fehler → 422 (mit Zeilennummern). Volljährigkeit aus dem Geburtsdatum (Stichtag heute)."""
    if len(rows) > MAX_NEW_STUDENTS:
        raise HTTPException(422, f"Höchstens {MAX_NEW_STUDENTS} Schüler/innen je Aufruf")
    today = date.today()
    errors: list[str] = []
    age_warnings: list[str] = []
    out: list[dict] = []
    for i, r in enumerate(rows):
        line = i + 1
        first, last = " ".join(r.first_name.split()), " ".join(r.last_name.split())
        if not first or not last:
            errors.append(f"Zeile {line}: Vor- und Nachname angeben")
        email = (r.email or "").strip() or None
        if email and not _EMAIL_RE.match(email):
            errors.append(f"Zeile {line}: ungültige E-Mail-Adresse „{email}“")
        born = r.birth_date
        if born and (born > today or born.year < 1900 or _age(born, today) > 120):
            errors.append(f"Zeile {line}: Geburtsdatum {born.strftime('%d.%m.%Y')} ist nicht plausibel")
        elif born and not 4 <= _age(born, today) <= 30:      # wie die Vorschau im Assistenten: nur Hinweis
            age_warnings.append(f"Zeile {line}: Alter {_age(born, today)} Jahre – bitte Geburtsdatum prüfen")
        parents = []
        for p in r.parents[:2]:
            pname, pmail = " ".join(p.name.split()), (p.email or "").strip()
            if not pname and not pmail:
                continue
            if pmail and not _EMAIL_RE.match(pmail):
                errors.append(f"Zeile {line}: ungültige E-Mail-Adresse der Eltern „{pmail}“")
            parents.append({"name": pname, "email": pmail or None})
        out.append({"index": i, "first_name": first, "last_name": last, "name": f"{first} {last}".strip(),
                    "email": email, "birth_date": born.isoformat() if born else None,
                    "adult": _age(born, today) >= 18 if born else bool(r.adult), "parents": parents})
    if errors:
        more = f" (und {len(errors) - 15} weitere)" if len(errors) > 15 else ""
        raise HTTPException(422, "; ".join(errors[:15]) + more)
    warnings: list[str] = age_warnings[:10]
    lines: dict[str, list[int]] = defaultdict(list)
    for s in out:
        lines[s["name"].lower()].append(s["index"] + 1)
    for s in out:
        nums = lines[s["name"].lower()]
        if len(nums) > 1 and nums[0] == s["index"] + 1:
            warnings.append(f"{s['name']} steht mehrfach in der Liste (Zeilen {', '.join(map(str, nums))})")
    names = {s["name"].lower() for s in out}
    for st in school.students:
        if st.name.lower() in names:
            where = "in dieser Klasse" if st.class_id == class_id else f"in Klasse {st.class_id}"
            warnings.append(f"Es gibt schon eine/n {st.name} {where}")
    return out, warnings[:30]


def _account_rights(user, body: AccountOptionsIn) -> None:
    roles = ["schueler"] * body.create_student_accounts + ["eltern"] * body.create_parent_accounts
    if roles and not has(user, "users.manage"):
        raise HTTPException(403, "Konten anlegen erfordert die Berechtigung zur Benutzerverwaltung")
    from .users import _check_manage

    for role in roles:
        _check_manage(user, role)


def _new_student_ids(school: School, n: int) -> list[str]:
    """Freie Schüler-IDs im vorhandenen Schema ``S00001`` (fortlaufend nach der höchsten Nummer)."""
    taken = {s.id for s in school.students}
    nums = [int(m.group(1)) for sid in taken if (m := re.fullmatch(r"S(\d+)", sid))]
    nxt = max(nums, default=0) + 1
    out: list[str] = []
    while len(out) < n:
        sid = f"S{nxt:05d}"
        if sid not in taken:
            out.append(sid)
        nxt += 1
    return out


def _with_accounts(students: list[dict], plan: list[dict]) -> list[dict]:
    """Vorschau/Antwort: je Schüler/in Benutzername des Schülerkontos und die Elternkonten."""
    by_index: dict[int, dict] = {s["index"]: {**s, "username": None, "parent_accounts": []} for s in students}
    for item in plan:
        for idx in item["indexes"]:
            row = by_index[idx]
            if item["role"] == "schueler":
                row["username"] = item["username"]
            else:
                row["parent_accounts"].append({"username": item["username"], "display_name": item["display_name"],
                                               "email": item.get("email"), "existing": item["kind"] == "existing"})
    return [by_index[s["index"]] for s in students]


def _undo_students(user, class_id: str, ids: list[str], *, drop_class: bool) -> None:
    """Gerade angelegte Schüler/innen (und die neue, leere Klasse) wieder aus dem Planungsdokument entfernen."""
    gone = set(ids)

    def fn(work: School):
        work.students = [s for s in work.students if s.id not in gone]
        if drop_class and not any(s.class_id == class_id for s in work.students):
            work.classes = [c for c in work.classes if c.id != class_id]

    try:
        mutate(user, f"Klasse {class_id}: Anlegen zurückgenommen (Konten fehlgeschlagen)", fn,
               scope=["classes", "students"])
    except Exception:  # noqa: BLE001 - ursprünglicher Fehler ist wichtiger
        logging.getLogger("schulmanager.classes").exception("Klasse %s nicht zurückgenommen", class_id)


def _create_students(user, db: Session, request: Request, body: AccountOptionsIn, school: School, class_id: str,
                     students: list[dict], warnings: list[str], new_class: Optional[SchoolClass]) -> dict:
    """Gemeinsamer Ablauf: Konten planen → (Vorschau) → Planungsdokument ändern → Konten + Brief-Stapel → Versand."""
    from schulmanager.server import letters
    from schulmanager.server.audit import audit

    accounts = body.create_student_accounts or body.create_parent_accounts
    plan, plan_warnings = (letters.plan_accounts(db, students, student_accounts=body.create_student_accounts,
                                                 parent_accounts=body.create_parent_accounts)
                           if accounts and students else ([], []))
    warnings = warnings + plan_warnings
    cls_info = _class_info(school, new_class) if new_class is not None else _class_info(school, _class_or_404(
        school, class_id))
    if body.dry_run:
        ids = _new_student_ids(school, len(students))
        rows = _with_accounts([{**s, "id": sid} for s, sid in zip(students, ids)], plan)
        return {"dry_run": True, "class": cls_info, "students": rows, "warnings": warnings, "accounts": [],
                "linked_parents": [], "letter_batch": None, "email": None}

    def fn(work: School):
        if new_class is not None:
            if class_id in work.index("classes"):
                raise HTTPException(409, f"Klasse „{class_id}“ existiert bereits")
            work.classes.append(SchoolClass.from_dict(new_class.to_dict()))
        else:
            _class_or_404(work, class_id)
        ids = _new_student_ids(work, len(students))
        for s, sid in zip(students, ids):
            work.students.append(Student(sid, s["name"], class_id, [], birth_date=s["birth_date"]))
        return ids

    n = len(students)
    what = f"{n} Schüler/in" if n == 1 else f"{n} Schüler/innen"
    message = f"Klasse {class_id} angelegt ({what})" if new_class is not None else f"Klasse {class_id}: {what} hinzugefügt"
    ids = mutate(user, message, fn, scope=["classes", "students"])
    try:
        school = snapshot()[1]
        infos = {s["index"]: {**s, "student_id": sid, "class_id": class_id, "class_name": class_id}
                 for s, sid in zip(students, ids)}
        entries, linked = letters.create_planned(db, plan, infos) if plan else ([], [])
        batch = None
        if entries:
            title = (f"Klasse {class_id} – neue Konten" if new_class is not None
                     else f"Klasse {class_id} – {len(entries)} neue Konten")
            batch = letters.create_batch(db, user, entries, title)
        audit(db, user, "class.create" if new_class is not None else "class.add_students", f"class:{class_id}",
              {"students": ids, "accounts": [e["user_id"] for e in entries],
               "linked_parents": [p["user_id"] for p in linked]}, ip=client_ip(request))
        db.commit()
    except Exception as exc:
        # Konten/Stapel gescheitert → Planungsdokument zurücknehmen (sonst Klasse ohne Konten, Wiederholung → 409)
        db.rollback()
        _undo_students(user, class_id, ids, drop_class=new_class is not None)
        if isinstance(exc, HTTPException):
            raise
        logging.getLogger("schulmanager.classes").exception("Konten für Klasse %s nicht angelegt", class_id)
        raise HTTPException(500, "Die Konten konnten nicht angelegt werden – es wurde nichts gespeichert. "
                                 "Bitte erneut versuchen.") from None
    email = None
    if batch is not None and body.send_email:
        stored = sorted(entries, key=letters._sort_key)
        email = letters.send_entries(db, stored, to=body.send_to, adults_to="student", created_at=batch.created_at)
        audit(db, user, "letters.send", f"letter_batch:{batch.id}",
              {"to": body.send_to, "auto": True, "sent": len(email["sent"]), "no_address": len(email["no_address"]),
               "unavailable": len(email["unavailable"])}, ip=client_ip(request))
        db.commit()
        letters.kick_outbox()
    rows = _with_accounts([{**s, "id": sid} for s, sid in zip(students, ids)], plan)
    by_student = {e["student_id"]: e["user_id"] for e in entries if e["role"] == "schueler"}
    for row in rows:
        row["user_id"] = by_student.get(row["id"])
    cls = school.index("classes").get(class_id)
    return {"dry_run": False, "class": _class_info(school, cls) if cls else cls_info, "students": rows,
            "warnings": warnings,
            "accounts": [{k: e[k] for k in ("user_id", "username", "display_name", "role", "student_id")}
                         | {"children": [c["student_id"] for c in e.get("children") or []]} for e in entries],
            "linked_parents": linked, "letter_batch": letters.batch_ref(batch), "email": email}


@router.post("/classes", status_code=201)
def create_class(body: ClassCreateIn, request: Request, user: AuthUser = Depends(require("masterdata.edit")),
                 db: Session = Depends(get_db)):
    """Klasse komplett anlegen: Stammdaten, Schülerliste, optional Schüler-/Elternkonten mit Startpasswort
    (Passwortwechsel beim ersten Anmelden) und Zugangsbriefen; ``dry_run`` = nur Vorschau (nichts gespeichert)."""
    from schulmanager.integrations._common import grade_from_name

    _account_rights(user, body)
    school = snapshot()[1]
    cid = check_id(body.id)
    if cid in school.index("classes"):
        raise HTTPException(409, f"Klasse „{cid}“ existiert bereits")
    from .features_data import GRADE_MAX, GRADE_MIN
    if not GRADE_MIN <= body.grade <= GRADE_MAX:
        raise HTTPException(422, f"Klassenstufe muss zwischen {GRADE_MIN} und {GRADE_MAX} liegen")
    warnings: list[str] = []
    guessed = grade_from_name(cid)
    if guessed and guessed != body.grade:
        warnings.append(f"Jahrgang {body.grade} passt nicht zur Bezeichnung „{cid}“ (erwartet {guessed})")
    sites, rooms, teachers = school.index("sites"), school.index("rooms"), school.index("teachers")
    site = (body.site or "").strip()
    room_id = (body.home_room or "").strip() or None
    teacher_id = (body.class_teacher or "").strip() or None
    if site and site not in sites:
        raise HTTPException(422, f"Standort „{site}“ existiert nicht")
    room = rooms.get(room_id) if room_id else None
    if room_id and room is None:
        raise HTTPException(422, f"Raum „{room_id}“ existiert nicht")
    if teacher_id and teacher_id not in teachers:
        raise HTTPException(422, f"Lehrkraft „{teacher_id}“ existiert nicht")
    if not site:
        site = room.site if room is not None and room.site else (school.sites[0].id if len(school.sites) == 1 else "")
    students, student_warnings = _clean_students(school, body.students, cid)
    cls = SchoolClass(cid, (body.name or "").strip() or cid, body.grade, students=len(students) or 25,
                      home_room=room_id, site=site, class_teacher=teacher_id)
    if room is not None:
        warnings += _room_warnings(school, cls, room)
    if teacher_id:
        warnings += [w for w in _teacher_warnings(school, cls, teacher_id) if "bisher nicht" not in w]
    return _create_students(user, db, request, body, school, cid, students, warnings + student_warnings, cls)


@router.post("/classes/{class_id}/students", status_code=201)
def add_students(class_id: str, body: StudentsAddIn, request: Request,
                 user: AuthUser = Depends(require("masterdata.edit")), db: Session = Depends(get_db)):
    """Schüler/innen nachlegen (gleiches Format wie ``POST /classes``), Konten und Zugangsbriefe optional."""
    _account_rights(user, body)
    snap = snapshot()
    check_view_access(user, "class", class_id, snap)
    school = snap[1]
    _class_or_404(school, class_id)
    if not body.students:
        raise HTTPException(422, "Bitte mindestens eine Schülerin oder einen Schüler angeben")
    students, warnings = _clean_students(school, body.students, class_id)
    return _create_students(user, db, request, body, school, class_id, students, warnings, None)
