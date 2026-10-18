"""Stammdaten: generisches CRUD über ``models.COLLECTIONS`` und Einstellungen.

* ``GET/POST /data/{collection}``, ``GET/PUT/DELETE /data/{collection}/{id}``
  (alle Sammlungen außer ``lessons``, ``absences``, ``overrides`` – diese haben eigene Endpunkte)
* ``GET/PUT /settings``

Validierung: Typen (Pydantic über die Dataclasses), Referenzen existieren, IDs eindeutig.
``DELETE`` verweigert mit 409 ``{"detail":{"message","references":[...]}}``, solange noch
Verweise bestehen – ``?force=1`` entfernt/leert die Verweise (Kaskade).

Wochen (52-Wochen-System): Wochenangaben sind ``weeks`` (laufende Wochen 1 … 53) oder ``rhythm`` (alle k Wochen ab
Woche s, optional bis Woche e), nie beides; ältere Requests dürfen ``week_pattern`` senden (wird zum Rhythmus).
Das Planungsfeld einer Klasse ``school_days`` braucht ``timetable.edit``. Ändern sich Unterrichtstage oder das
Zeitraster so, dass Stunden wegfallen, antwortet 409 ``{"code": "plan_change"|"grid_change", "message", "changes"}``;
``?force=1`` übernimmt. Veraltete Felder älterer Oberflächen (``legacy.LEGACY_REQUEST_FIELDS``) werden ignoriert.
"""
from __future__ import annotations

import copy
import re
from datetime import date
from typing import Any, Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from schulmanager import weeks as wk
from schulmanager.models import COLLECTIONS, HOLIDAY_KINDS, School, Settings
from schulmanager.server import net_guard
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import (check_id, has, is_scoped_teacher, mutate, need, new_id, own_class_ids,
                              own_student_ids, perm_scope, plan_course_ids, reads_all_plans, snapshot,
                              teacher_course_ids, visible_student_ids)

router = APIRouter(tags=["Stammdaten"])

EXCLUDED = {"lessons", "absences", "overrides"}
EDITABLE = {k: v for k, v in COLLECTIONS.items() if k not in EXCLUDED}

WRITE_PERM = {
    "sites": "masterdata.edit", "subjects": "masterdata.edit", "teachers": "masterdata.edit",
    "rooms": "masterdata.edit", "classes": "masterdata.edit", "students": "masterdata.edit",
    "holidays": "masterdata.edit", "areas": "masterdata.edit",
    "curricula": "timetable.edit", "courses": "timetable.edit", "duties": "timetable.edit",
    "exams": "exam.edit", "events": "masterdata.edit", "grade_profiles": "timetable.edit",
}
ID_PREFIX = {"events": "T", "holidays": "H", "areas": "AUF", "duties": "D", "exams": "KA", "curricula": "ST",
             "courses": "K", "students": "S", "sites": "S", "rooms": "R", "grade_profiles": "JG"}
LABELS = {"sites": "Standort", "subjects": "Fach", "teachers": "Lehrkraft", "rooms": "Raum",
          "classes": "Klasse", "students": "Schüler/in", "curricula": "Stundentafel", "courses": "Kurs",
          "holidays": "Ferien/Feiertag", "areas": "Aufsichtsbereich", "duties": "Aufsicht", "exams": "Klausur",
          "lessons": "Stunde", "events": "Termin", "grade_profiles": "Jahrgang"}
SCOPES = {"courses": ["courses", "timetable"], "classes": ["classes", "timetable"],
          "grade_profiles": ["grade_profiles", "classes", "curricula"],
          "exams": ["exams"], "duties": ["duties"], "holidays": ["holidays", "substitutions"],
          "events": ["events", "holidays", "substitutions", "duties"]}

#: erlaubte Jahrgangsstufen (Klassen und Stundentafeln; 0 = Vorklasse/Schulkindergarten)
GRADE_MIN, GRADE_MAX = 0, 20

_adapters: dict[str, TypeAdapter] = {}


def _adapter(collection: str) -> TypeAdapter:
    if collection not in _adapters:
        _adapters[collection] = TypeAdapter(COLLECTIONS[collection])
    return _adapters[collection]


def _collection(name: str) -> str:
    if name in EXCLUDED:
        raise HTTPException(404, f"Sammlung {name} wird über eigene Endpunkte bearbeitet")
    if name not in EDITABLE:
        raise HTTPException(404, f"Unbekannte Sammlung {name}")
    return name


def _validation_detail(exc: ValidationError) -> str:
    msgs = []
    for err in exc.errors()[:10]:
        loc = ".".join(str(x) for x in err.get("loc", ()))
        msgs.append(f"{loc}: {err.get('msg')}" if loc else str(err.get("msg")))
    return "Ungültige Daten – " + "; ".join(msgs)


def parse_item(collection: str, data: dict):
    try:
        return _adapter(collection).validate_python(data)
    except ValidationError as exc:
        raise HTTPException(422, _validation_detail(exc)) from None


# ------------------------------------------------------------------ Validierung
def _date_ok(value: Any) -> bool:
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def _rules_errors(school: School, rules, what: str) -> list[str]:
    """Regeln prüfen (Wochen oder Rhythmus, Tage 0–6, Stunden, U-15)."""
    st = school.settings
    out = []
    for r in rules:
        out += wk.rule_errors(r, st.periods, what)
    return out


#: Planungsfelder einer Klasse – nur mit ``timetable.edit`` (R1, §14.3)
CLASS_PLAN_FIELDS = ("school_days",)
PLAN_FIELDS_403 = "Für Zeitraster und Unterrichtstage brauchen Sie das Recht „Stundenplan bearbeiten“."


def class_plan_errors(item) -> list[str]:
    errs = []
    days = item.school_days or []
    if any(not isinstance(d, int) or not 0 <= d <= 6 for d in days) or len(set(days)) != len(days):
        errs.append("Unterrichtstage: nur Montag bis Sonntag, jeder Tag einmal")
    return errs


class _Ids:
    """Lazily berechnete ID-Mengen je Sammlung; mit ``cache`` über viele Aufrufe wiederverwendbar (CSV-Import:
    neu angehängte Einträge werden über die Listenlänge erkannt)."""

    def __init__(self, school: School, cache: Optional[dict] = None):
        self.school, self.cache = school, cache if cache is not None else {}

    def __getitem__(self, name: str) -> set:
        items = getattr(self.school, name)
        hit = self.cache.get(name)
        if hit is None or hit[0] != len(items) or hit[1] is not items:
            hit = self.cache[name] = (len(items), items, {x.id for x in items})
        return hit[2]


def validate_item(school: School, collection: str, item, _cache: Optional[dict] = None) -> list[str]:
    """Prüft Referenzen und Wertebereiche. Liefert Fehlermeldungen (leer = ok).

    Wird auch vom CSV-Import je Zeile genutzt (``_cache`` = gemeinsamer Zwischenspeicher der ID-Mengen)."""
    st = school.settings
    errs: list[str] = []
    ids = _Ids(school, _cache)

    def ref(kind: str, value: Optional[str], label: str) -> None:
        if value and value not in ids[kind]:
            errs.append(f"{label} „{value}“ existiert nicht")

    if collection == "teachers":
        for s in item.subjects:
            ref("subjects", s, "Fach")
        for s in item.sites:
            ref("sites", s, "Standort")
        for c in getattr(item, "preferred_classes", []) or []:
            ref("classes", c, "Wunschklasse")
        if item.max_hours < 0 or item.max_per_day < 0 or item.max_subs_per_week < 0:
            errs.append("Stundenwerte dürfen nicht negativ sein")
        errs += _rules_errors(school, item.unavailable, "Sperrzeit")
        errs += _rules_errors(school, getattr(item, "wishes", []) or [], "Wunsch")
        from schulmanager.teacher_profile import ProfileError, normalize_windows, normalize_work_grid
        try:
            normalize_windows(getattr(item, "time_windows", []) or [], st)
            normalize_work_grid(getattr(item, "work_grid", None) or {}, st)
        except ProfileError as exc:
            errs += exc.errors
        email = getattr(item, "email", "") or ""
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errs.append(f"Ungültige E-Mail-Adresse „{email}“")
    elif collection == "rooms":
        ref("sites", item.site, "Standort")
        if item.capacity < 0:
            errs.append("Kapazität darf nicht negativ sein")
    elif collection == "classes":
        ref("sites", item.site, "Standort")
        ref("rooms", item.home_room, "Raum")
        ref("teachers", item.class_teacher, "Lehrkraft")
        ref("grade_profiles", item.profile, "Jahrgang")
        if not GRADE_MIN <= item.grade <= GRADE_MAX:
            errs.append(f"Jahrgangsstufe muss zwischen {GRADE_MIN} und {GRADE_MAX} liegen")
        if not 1 <= item.max_periods_per_day <= st.periods:
            errs.append(f"Max. Stunden pro Tag muss zwischen 1 und {st.periods} liegen")
        for key, label, hi in (("max_exams_per_week", "Klassenarbeiten je Woche", 20),
                               ("max_exams_per_day", "Klassenarbeiten je Tag", 5)):
            v = getattr(item, key, None)
            if v is not None and (isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= hi):
                errs.append(f"{label}: Zahl zwischen 0 und {hi} oder leer (Vorgabe von Jahrgang/Schule)")
        errs += class_plan_errors(item)
        errs += _rules_errors(school, item.unavailable, "Wochen-Regel")
    elif collection == "students":
        if not item.class_id:
            errs.append("Klasse fehlt")
        ref("classes", item.class_id, "Klasse")
        courses = _course_index(school, _cache)
        for cref in item.courses:
            cid, _, idx = cref.rpartition("#")
            c = courses.get(cid)
            if c is None or not idx.isdigit() or int(idx) >= len(c.parts):
                errs.append(f"Kursteil „{cref}“ existiert nicht")
    elif collection == "curricula":
        if not (item.name or "").strip():
            errs.append("Name der Stundentafel fehlt")
        seen: set[str] = set()
        for e in item.entries:
            if not e.subject:
                errs.append("Fach fehlt in einer Zeile der Stundentafel")
                continue
            ref("subjects", e.subject, "Fach")
            if e.subject in seen:
                errs.append(f"Fach „{e.subject}“ ist mehrfach eingetragen")
            seen.add(e.subject)
            if not 0 <= e.hours <= 40:
                errs.append(f"Wochenstunden für „{e.subject}“ müssen zwischen 0 und 40 liegen")
        for c in item.classes:
            ref("classes", c, "Klasse")
        if len(set(item.classes)) != len(item.classes):
            errs.append("Klasse mehrfach eingetragen")
        bad = sorted({g for g in item.grades if not GRADE_MIN <= g <= GRADE_MAX})
        if bad:
            errs.append(f"Klassenstufe {', '.join(map(str, bad))} ungültig (erlaubt {GRADE_MIN}–{GRADE_MAX})")
        from schulmanager.grade_profiles import curriculum_base_errors
        errs += curriculum_base_errors(school, item)
        seen_d: set[str] = set()
        for d in item.deltas:
            if not d.subject:
                errs.append("Fach fehlt in einer Abweichung der Stundentafel")
                continue
            ref("subjects", d.subject, "Fach")
            if d.subject in seen_d:
                errs.append(f"Abweichung für „{d.subject}“ ist mehrfach eingetragen")
            seen_d.add(d.subject)
            if not -40 <= d.hours <= 40:
                errs.append(f"Abweichung für „{d.subject}“ muss zwischen -40 und 40 Stunden liegen")
    elif collection == "grade_profiles":
        from schulmanager.grade_profiles import validate_profile
        errs += validate_profile(school, item, GRADE_MIN, GRADE_MAX)
    elif collection == "courses":
        if not item.classes:
            errs.append("Ein Kurs braucht mindestens eine Klasse")
        if not item.parts:
            errs.append("Ein Kurs braucht mindestens einen Teil")
        for c in item.classes:
            ref("classes", c, "Klasse")
        for p in item.parts:
            ref("subjects", p.subject, "Fach")
            ref("teachers", p.teacher, "Lehrkraft")
            ref("rooms", p.room, "Raum")
            for s in p.students or []:
                ref("students", s, "Schüler/in")
        if item.hours < 0:
            errs.append("Wochenstunden dürfen nicht negativ sein")
        errs += wk.spec_errors(item.weeks, item.rhythm, "Wochen")
    elif collection == "holidays":
        if not (_date_ok(item.date_from) and _date_ok(item.date_to)):
            errs.append("Ungültiges Datum")
        elif item.date_to < item.date_from:
            errs.append("Das Enddatum liegt vor dem Startdatum")
        if item.kind not in HOLIDAY_KINDS:
            errs.append("Art: Ferien, Feiertag, beweglicher Ferientag oder unterrichtsfrei")
    elif collection == "events":
        if not item.title.strip():
            errs.append("Bitte einen Titel angeben")
        if not (_date_ok(item.date_from) and (not item.date_to or _date_ok(item.date_to))):
            errs.append("Ungültiges Datum")
        elif item.date_to and item.date_to < item.date_from:
            errs.append("Das Enddatum liegt vor dem Startdatum")
        if item.kind not in ("termin", "pflicht"):
            errs.append("Art muss „termin“ oder „pflicht“ sein")
        for t in (item.time_from, item.time_to):
            if t and not _TIME.match(t):
                errs.append(f"Ungültige Uhrzeit {t} (Format HH:MM)")
        for c in item.classes:
            ref("classes", c, "Klasse")
        for t in item.teachers:
            ref("teachers", t, "Lehrkraft")
    elif collection == "areas":
        ref("sites", item.site, "Standort")
        if item.needed < 0:
            errs.append("Anzahl Aufsichten darf nicht negativ sein")
    elif collection == "duties":
        ref("areas", item.area, "Aufsichtsbereich")
        ref("teachers", item.teacher, "Lehrkraft")
        if not item.area:
            errs.append("Aufsichtsbereich fehlt")
        if not 0 <= item.day <= 6:
            errs.append("Ungültiger Wochentag")
        if not 0 <= item.break_index < len(st.breaks):
            errs.append("Ungültige Pause")
        errs += wk.spec_errors(item.weeks, item.rhythm)
    elif collection == "exams":
        errs += exam_errors(school, item)
    return errs


def _course_index(school: School, cache: Optional[dict]) -> dict:
    if cache is None:
        return school.index("courses")
    hit = cache.get("_course_index")
    if hit is None or hit[0] != len(school.courses) or hit[1] is not school.courses:
        hit = cache["_course_index"] = (len(school.courses), school.courses, school.index("courses"))
    return hit[2]


def curriculum_conflict_error(school: School, item_id: str) -> Optional[dict]:
    """409-Detail, wenn die Tafel ``item_id`` (bereits in ``school``) sich mit anderen überschneidet."""
    from schulmanager.planning import curriculum_conflicts
    groups = curriculum_conflicts(school, only=item_id)
    if not groups:
        return None
    names = {c.id: c.name for c in school.curricula}
    cls = {c.id: c.name for c in school.classes}
    lines = [f"{', '.join(cls.get(x, x) for x in g['classes'])}: "
             f"{' / '.join(names.get(i, i) for i in g['curricula'])}" for g in groups]
    return {"message": "Für einige Klassen gelten dann mehrere Stundentafeln", "conflicts": lines,
            "groups": groups}


def exam_errors(school: School, exam) -> list[str]:
    st = school.settings
    errs = []
    course = school.index("courses").get(exam.course_id)
    if course is None:
        errs.append(f"Kurs „{exam.course_id}“ existiert nicht")
    if not _date_ok(exam.date):
        errs.append("Ungültiges Datum")
    if exam.length < 1 or exam.start < 0 or exam.start + exam.length > st.periods:
        errs.append("Stunde außerhalb des Zeitrasters")
    if exam.part is not None and course is not None and not 0 <= exam.part < len(course.parts):
        errs.append("Ungültiger Kursteil")
    if exam.room and exam.room not in school.index("rooms"):
        errs.append(f"Raum „{exam.room}“ existiert nicht")
    return errs


def _raise_errors(errs: list[str]) -> None:
    if errs:
        raise HTTPException(422, "; ".join(dict.fromkeys(errs)))


# ------------------------------------------------------------------ Referenzen
def references(school: School, collection: str, item_id: str) -> list[str]:
    """Lesbare Liste der Stellen, die auf ``collection/item_id`` verweisen."""
    out: list[str] = []
    if collection == "sites":
        out += [f"Raum {r.id}" for r in school.rooms if r.site == item_id]
        out += [f"Klasse {c.id}" for c in school.classes if c.site == item_id]
        out += [f"Lehrkraft {t.id}" for t in school.teachers if item_id in t.sites]
        out += [f"Aufsichtsbereich {a.id}" for a in school.areas if a.site == item_id]
    elif collection == "subjects":
        out += [f"Lehrkraft {t.id}" for t in school.teachers if item_id in t.subjects]
        out += [f"Stundentafel {c.id}" for c in school.curricula
                if any(e.subject == item_id for e in [*c.entries, *c.deltas])]
        out += [f"Kurs {c.id}" for c in school.courses if any(p.subject == item_id for p in c.parts)]
    elif collection == "teachers":
        out += [f"Kurs {c.id}" for c in school.courses if any(p.teacher == item_id for p in c.parts)]
        out += [f"Klasse {c.id} (Klassenleitung)" for c in school.classes if c.class_teacher == item_id]
        out += [f"Aufsicht {d.id}" for d in school.duties if d.teacher == item_id]
        out += [f"Abwesenheit {a.id}" for a in school.absences if a.kind == "teacher" and a.ref == item_id]
        out += [f"Vertretung {o.id}" for o in school.overrides if o.teacher == item_id]
    elif collection == "rooms":
        out += [f"Klasse {c.id} (Klassenraum)" for c in school.classes if c.home_room == item_id]
        out += [f"Kurs {c.id}" for c in school.courses if any(p.room == item_id for p in c.parts)]
        n = sum(1 for le in school.lessons if item_id in le.rooms)
        if n:
            out.append(f"{n} Stunden im Stundenplan")
        out += [f"Raumsperre {a.id}" for a in school.absences if a.kind == "room" and a.ref == item_id]
        out += [f"Vertretung {o.id}" for o in school.overrides if o.room == item_id]
        out += [f"Klausur {e.id}" for e in school.exams if e.room == item_id]
    elif collection == "classes":
        n = sum(1 for s in school.students if s.class_id == item_id)
        if n:
            out.append(f"{n} Schüler/innen")
        out += [f"Kurs {c.id}" for c in school.courses if item_id in c.classes]
        out += [f"Stundentafel {c.id}" for c in school.curricula if item_id in c.classes]
        out += [f"Abwesenheit {a.id}" for a in school.absences if a.kind == "class" and a.ref == item_id]
    elif collection == "curricula":
        out += [f"Jahrgang {p.id}" for p in school.grade_profiles if p.curriculum == item_id]
        out += [f"Stundentafel {c.id} (abgeleitet)" for c in school.curricula if c.base == item_id]
    elif collection == "grade_profiles":
        out += [f"Klasse {c.id}" for c in school.classes if c.profile == item_id]
    elif collection == "students":
        out += [f"Kurs {c.id}" for c in school.courses if any(item_id in (p.students or []) for p in c.parts)]
    elif collection == "courses":
        n = sum(1 for le in school.lessons if le.course_id == item_id)
        if n:
            out.append(f"{n} Stunden im Stundenplan")
        out += [f"Klausur {e.id}" for e in school.exams if e.course_id == item_id]
        out += [f"Unterrichtsausfall {a.id}" for a in _lesson_absences(school, item_id)]
        n = sum(1 for s in school.students if any(r.rpartition("#")[0] == item_id for r in s.courses))
        if n:
            out.append(f"Kurswahlen von {n} Schüler/innen")
    elif collection == "areas":
        out += [f"Aufsicht {d.id}" for d in school.duties if d.area == item_id]
    return out


def cascade_delete(school: School, collection: str, item_id: str) -> None:
    """Entfernt bzw. leert alle Verweise auf ``collection/item_id`` (``?force=1``)."""
    if collection == "sites":
        for r in school.rooms:
            if r.site == item_id:
                r.site = ""
        for c in school.classes:
            if c.site == item_id:
                c.site = ""
        for t in school.teachers:
            t.sites = [s for s in t.sites if s != item_id]
        for a in school.areas:
            if a.site == item_id:
                a.site = ""
    elif collection == "subjects":
        for t in school.teachers:
            t.subjects = [s for s in t.subjects if s != item_id]
        for cur in school.curricula:
            cur.entries = [e for e in cur.entries if e.subject != item_id]
            cur.deltas = [e for e in cur.deltas if e.subject != item_id]
        gone = set()
        for c in school.courses:
            if any(p.subject == item_id for p in c.parts):
                gone.add(c.id)
        for cid in gone:
            cascade_delete(school, "courses", cid)
        school.courses = [c for c in school.courses if c.id not in gone]
    elif collection == "teachers":
        for c in school.courses:
            for p in c.parts:
                if p.teacher == item_id:
                    p.teacher = None
        for c in school.classes:
            if c.class_teacher == item_id:
                c.class_teacher = None
        for d in school.duties:
            if d.teacher == item_id:
                d.teacher = None
        school.absences = [a for a in school.absences if not (a.kind == "teacher" and a.ref == item_id)]
        school.overrides = [o for o in school.overrides if o.teacher != item_id]
    elif collection == "rooms":
        for c in school.classes:
            if c.home_room == item_id:
                c.home_room = None
        for c in school.courses:
            for p in c.parts:
                if p.room == item_id:
                    p.room = None
        for le in school.lessons:
            le.rooms = [None if r == item_id else r for r in le.rooms]
        school.absences = [a for a in school.absences if not (a.kind == "room" and a.ref == item_id)]
        school.overrides = [o for o in school.overrides if o.room != item_id]
        for e in school.exams:
            if e.room == item_id:
                e.room = None
    elif collection == "classes":
        school.students = [s for s in school.students if s.class_id != item_id]
        gone = set()
        for c in school.courses:
            if item_id in c.classes:
                c.classes = [x for x in c.classes if x != item_id]
                if not c.classes:
                    gone.add(c.id)
        for cid in gone:
            cascade_delete(school, "courses", cid)
        school.courses = [c for c in school.courses if c.id not in gone]
        for cur in school.curricula:
            cur.classes = [x for x in cur.classes if x != item_id]
        school.absences = [a for a in school.absences if not (a.kind == "class" and a.ref == item_id)]
    elif collection == "curricula":
        from schulmanager.grade_profiles import materialize
        for c in school.curricula:
            if c.base == item_id:
                materialize(school, c)
        for p in school.grade_profiles:
            if p.curriculum == item_id:
                p.curriculum = None
    elif collection == "grade_profiles":
        for c in school.classes:
            if c.profile == item_id:
                c.profile = None
    elif collection == "students":
        for c in school.courses:
            for p in c.parts:
                if p.students and item_id in p.students:
                    p.students = [s for s in p.students if s != item_id]
    elif collection == "courses":
        lesson_ids = {le.id for le in school.lessons if le.course_id == item_id}
        school.lessons = [le for le in school.lessons if le.course_id != item_id]
        school.overrides = [o for o in school.overrides if o.lesson_id not in lesson_ids]
        school.exams = [e for e in school.exams if e.course_id != item_id]
        for s in school.students:
            s.courses = [r for r in s.courses if r.rpartition("#")[0] != item_id]
        # „Unterricht findet nicht statt“ (kind="lesson", ref="<kurs>[#<teil>]") des Kurses entfernen
        gone_abs = {id(a) for a in _lesson_absences(school, item_id)}
        school.absences = [a for a in school.absences if id(a) not in gone_abs]
    elif collection == "areas":
        school.duties = [d for d in school.duties if d.area != item_id]


def _lesson_absences(school: School, course_id: str, min_part: Optional[int] = None) -> list:
    """``lesson``-Abwesenheiten des Kurses (``ref="<kurs>"`` bzw. ``"<kurs>#<teil>"``);
    mit ``min_part`` nur solche für Kursteile ``>= min_part``."""
    from schulmanager.substitution import split_lesson_ref

    out = []
    for a in school.absences:
        if a.kind != "lesson":
            continue
        try:
            cid, part = split_lesson_ref(a.ref)
        except ValueError:
            continue
        if cid == course_id and (min_part is None or (part is not None and part >= min_part)):
            out.append(a)
    return out


def _sync_course_change(school: School, course) -> None:
    """Nach Änderung eines Kurses: Raumlisten der Stunden an die Teilezahl anpassen,
    Kurswahlen und Unterrichtsausfälle (``lesson``) nicht mehr vorhandener Kursteile entfernen."""
    n = len(course.parts)
    for le in school.lessons:
        if le.course_id == course.id and len(le.rooms) != n:
            le.rooms = (list(le.rooms) + [None] * n)[:n]
    for s in school.students:
        s.courses = [r for r in s.courses
                     if r.rpartition("#")[0] != course.id or int(r.rpartition("#")[2] or 0) < n]
    gone = {id(a) for a in _lesson_absences(school, course.id, min_part=n)}
    if gone:
        school.absences = [a for a in school.absences if id(a) not in gone]


# ------------------------------------------------------------------ Lesen
def _exam_visible(user, school: School, exam, snap, allowed_courses=None) -> bool:
    if reads_all_plans(user) or has(user, "masterdata.edit") or has(user, "timetable.edit"):
        return True
    if has(user, "plans.read_all"):  # Lehrkraft: Kurse eigener Klassen + eigene Kurse
        return exam.course_id in (allowed_courses if allowed_courses is not None else plan_course_ids(user, snap))
    from .features_common import student_parts
    for sid in own_student_ids(user):
        parts = student_parts(sid, snap)
        if exam.course_id in parts and (exam.part is None or exam.part in parts[exam.course_id]):
            return True
    return False


def _public_teacher(t) -> dict:
    return {"id": t.id, "name": t.name, "subjects": list(t.subjects)}


def _student_view(user, student, snap, staff: bool, own_ids=frozenset()) -> dict:
    """Datensparsame Sicht auf eine Schülerzeile (S-08): Geburtsdatum nur mit Recht „Geburtsdatum pflegen“
    (bzw. für die eigene Person/Eltern), Kurswahl vollständig nur für Planung/Verwaltung und die Betroffenen;
    übrige Lehrkräfte sehen nur echte Wahlen in mehrteiligen Kursen (wie die Klassenseite)."""
    from .features_parent_access import may_set_birth_date

    d = student.to_dict()
    own = student.id in own_ids
    if not own and not may_set_birth_date(user, student.id, snap):
        d.pop("birth_date", None)
    editor = has(user, "masterdata.edit") or has(user, "timetable.edit")
    if not own and not editor and not (staff and not is_scoped_teacher(user)):
        courses = snap[1].index("courses")
        keep = []
        for ref in student.courses:
            cid, _, part = ref.rpartition("#")
            c = courses.get(cid)
            if c is not None and len(c.parts) > 1:
                keep.append(ref)
        d["courses"] = keep
    return d


def readable_items(user, collection: str, snap) -> list[dict]:
    """Liste einer Sammlung, gefiltert nach Rolle.

    Lehrkräfte (``plans.read_all`` → ``own_classes``) sehen nur, was sie brauchen: Klassen/Kurse/Klausuren
    ihrer Klassen, eigene Aufsichten, die eigene Lehrkraft vollständig (andere nur Name/Fächer), keine
    Stundentafeln. Räume, Fächer, Standorte, Ferien und Aufsichtsbereiche sind für alle lesbar."""
    school = snap[1]
    items = getattr(school, collection)
    editor = has(user, "masterdata.edit") or has(user, "timetable.edit")
    staff = editor or reads_all_plans(user)
    scoped = not editor and is_scoped_teacher(user)
    tid = getattr(user, "teacher_id", None)
    if collection == "students":
        vis = visible_student_ids(user, snap)
        if vis is not None and not vis and not has(user, "students.read"):
            raise HTTPException(403, "Keine Berechtigung")
        own_ids = frozenset(own_student_ids(user))
        return [_student_view(user, s, snap, staff, own_ids) for s in items if vis is None or s.id in vis]
    if collection == "teachers":
        if staff:
            return [t.to_dict() for t in items]
        return [t.to_dict() if scoped and t.id == tid else _public_teacher(t) for t in items]
    if collection == "duties":
        need(user, "plans.read_all", "timetable.edit", "substitution.edit")
        if scoped and not has(user, "substitution.edit"):
            return [d.to_dict() for d in items if tid and d.teacher == tid]
        return [d.to_dict() for d in items]
    if collection == "exams":
        allowed = plan_course_ids(user, snap) if scoped else None
        return [e.to_dict() for e in items if _exam_visible(user, school, e, snap, allowed)]
    if collection == "courses":
        out = []
        vis = visible_student_ids(user, snap)
        allowed = plan_course_ids(user, snap) if scoped else None
        for c in items:
            if allowed is not None and c.id not in allowed:
                continue
            d = c.to_dict()
            if vis is not None:
                for p in d["parts"]:
                    if p.get("students"):
                        p["students"] = [s for s in p["students"] if s in vis]
            out.append(d)
        return out
    if collection == "classes" and scoped:
        own = own_class_ids(user, snap)
        return [c.to_dict() for c in items if c.id in own]
    if collection in ("curricula",) and not staff:
        raise HTTPException(403, "Keine Berechtigung")
    return [x.to_dict() for x in items]


@router.get("/data/{collection}")
def list_items(collection: str, class_id: Optional[str] = None, q: Optional[str] = None,
               user: AuthUser = Depends(current_user)):
    """Alle Einträge einer Sammlung (nach Rolle gefiltert). Filter: ``class_id`` (Schüler/Kurse), ``q`` (Suche)."""
    collection = _collection(collection)
    snap = snapshot()
    items = readable_items(user, collection, snap)
    if class_id:
        if collection == "students":
            items = [x for x in items if x.get("class_id") == class_id]
        elif collection == "courses":
            items = [x for x in items if class_id in x.get("classes", [])]
    if q:
        ql = q.lower()
        items = [x for x in items if ql in str(x.get("id", "")).lower() or ql in str(x.get("name", "")).lower()
                 or ql in str(x.get("label", "")).lower() or ql in str(x.get("title", "")).lower()]
    return items


@router.get("/data/{collection}/{item_id}")
def get_item(collection: str, item_id: str, user: AuthUser = Depends(current_user)):
    collection = _collection(collection)
    for x in readable_items(user, collection, snapshot()):
        if x.get("id") == item_id:
            return x
    raise HTTPException(404, f"{LABELS.get(collection, 'Eintrag')} {item_id} nicht gefunden")


# ------------------------------------------------------------------ Schreiben
def _check_write(user, collection: str, school: School, item=None, old=None) -> None:
    need(user, WRITE_PERM[collection])
    if collection == "students" and item is not None and (item.birth_date or None) != (getattr(old, "birth_date", None) or None):
        from .features_parent_access import check_birth_date, may_set_birth_date
        if not may_set_birth_date(user, item.id, (None, school)):
            raise HTTPException(403, "Das Geburtsdatum dürfen nur Berechtigte ändern (Recht „Geburtsdatum pflegen“)")
        try:
            check_birth_date(date.fromisoformat(str(item.birth_date)[:10]) if item.birth_date else None)
        except ValueError:
            raise HTTPException(422, "Geburtsdatum bitte als Datum (JJJJ-MM-TT) angeben") from None
    if collection == "exams" and perm_scope(user, "exam.edit") == "own_courses":
        own = teacher_course_ids(getattr(user, "teacher_id", None))
        for e in (item, old):
            if e is not None and e.course_id not in own:
                raise HTTPException(403, "Klausuren nur für eigene Kurse")


def _rule_date_errors(rule) -> list[str]:
    value = getattr(rule, "valid_from", "") or ""
    if not value:
        return []
    try:
        date.fromisoformat(str(value))
    except ValueError:
        return ["„Gilt ab“ bitte als Datum angeben"]
    return []


def _apply_teacher_windows(school: School, teacher) -> None:
    """Zeitfenster normalisieren und in Sperrzeiten umrechnen (alte Zeitfenster-Regeln werden ersetzt)."""
    from schulmanager.teacher_profile import ProfileError, apply_windows, normalize_windows, normalize_work_grid
    try:
        teacher.time_windows = normalize_windows(teacher.time_windows or [], school.settings)
        teacher.work_grid = normalize_work_grid(getattr(teacher, "work_grid", None) or {}, school.settings)
    except ProfileError as exc:
        raise HTTPException(422, "; ".join(exc.errors)) from None
    errs: list[str] = []
    for key, what in (("unavailable", "Sperrzeit"), ("wishes", "Wunsch")):
        for i, r in enumerate(getattr(teacher, key) or [], 1):
            errs += [f"{what} {i}: {m}" for m in _rule_date_errors(r)]
    if getattr(teacher, "commute_mode", "") not in ("", "never", "once", "free"):
        errs.append("Pendeln: ungültige Auswahl")
    if not 0 <= int(getattr(teacher, "commute_gap", 0) or 0) <= 240:
        errs.append("Pendeln: Mindestpause 0 bis 240 Minuten")
    if errs:
        raise HTTPException(422, "; ".join(errs))
    apply_windows(teacher, school.settings)


def _scope(collection: str) -> list[str]:
    return SCOPES.get(collection, [collection])


def expand_week_patterns(school: School, collection: str, data: dict) -> None:
    """Ältere Anfrage-Felder zu Wochen (``week_pattern``) im Request durch ``rhythm`` ersetzen und veraltete Felder
    entfernen. 422 bei ungültigem Muster oder wenn Wochen und Rhythmus zugleich gesetzt sind."""
    from schulmanager.legacy import strip_legacy_fields
    del school
    errs: list[str] = []
    strip_legacy_fields(data)
    if collection in ("courses", "duties"):
        errs += wk.parse_weeks_input(data)
    elif collection == "classes":
        for r in data.get("unavailable") or []:
            errs += wk.parse_weeks_input(r)
    elif collection == "teachers":
        for key in ("unavailable", "wishes"):
            for r in data.get(key) or []:
                errs += wk.parse_weeks_input(r)
    _raise_errors(errs)


def _plan_fields_changed(old, item) -> bool:
    if old is None:
        return any(getattr(item, f) != getattr(type(item)(item.id, item.name, item.grade), f) for f in CLASS_PLAN_FIELDS)
    return any(getattr(old, f) != getattr(item, f) for f in CLASS_PLAN_FIELDS)


def class_plan_change(school: School, old, item, force: bool) -> list[dict]:
    """Planungsfelder einer Klasse geändert (``item`` liegt schon im Dokument): Stunden an entfallenen
    Unterrichtstagen und gekoppelte Kurse melden. Verlust ohne ``force`` → 409 ``plan_change``.
    Rückgabe: alle Änderungen."""
    from schulmanager.calendar_utils import class_days

    day_short = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
    changes: list[dict] = []
    removed_days = set(class_days(school, old)) - set(class_days(school, item))
    if removed_days:
        courses = school.index("courses")
        for les in school.lessons:
            c = courses.get(les.course_id)
            if c is not None and item.id in c.classes and les.day in removed_days:
                changes.append({"kind": "lesson", "id": les.id, "exact": False,
                                "label": f"Stunde {day_short[les.day]} {les.start + 1}. Std. {c.label or c.id}",
                                "before": day_short[les.day], "after": "kein Unterrichtstag"})
        for c in school.courses:
            if item.id in c.classes and len(c.classes) > 1 and not any(x["id"] == c.id for x in changes):
                changes.append({"kind": "coupling", "id": c.id, "exact": False,
                                "label": f"Kurs {c.label or c.id} (Kopplung)", "before": "gemeinsame Unterrichtstage",
                                "after": "Unterrichtstage der Klasse geändert"})
    lossy = [{k: v for k, v in c.items() if k != "exact"} for c in changes if not c["exact"]]
    if lossy and not force:
        raise HTTPException(409, {"code": "plan_change", "changes": lossy,
                                  "message": f"Die Änderung betrifft {len(lossy)} Einträge"})
    return changes


def _dates(collection: str, *values) -> Optional[list[str]]:
    """Betroffene Tage (für das Event), derzeit nur bei Klausuren."""
    if collection != "exams":
        return None
    out = []
    for v in values:
        v = getattr(v, "date", v)
        if isinstance(v, str) and len(v) >= 10:
            out.append(v[:10])
    return out


def _check_curriculum(school: School, item_id: str, force: bool) -> None:
    """Überschneidung mit anderen Stundentafeln → 409 (``?force=1`` speichert trotzdem)."""
    detail = curriculum_conflict_error(school, item_id)
    if detail and not force:
        raise HTTPException(409, detail)


def _pin_course(old, item, data: dict) -> None:
    """Stundentafel-Kurs im Editor geändert: geänderte Felder merken (bleiben beim erneuten Erzeugen erhalten).
    ``pinned`` im Body wird übernommen (``[]`` = Anpassungen verwerfen); geänderte Klassen machen den Kurs
    zu einem manuellen Kurs (Kopplung)."""
    from schulmanager.planning import PINNABLE, changed_fields
    if old.origin != "curriculum" or item.origin != "curriculum":
        item.pinned = []
        return
    if sorted(old.classes) != sorted(item.classes):
        item.origin, item.pinned = "manual", []
        return
    base = data.get("pinned", old.pinned) if isinstance(data.get("pinned", old.pinned), list) else old.pinned
    pins = {f for f in base if f in PINNABLE} | set(changed_fields(old, item))
    item.pinned = [f for f in PINNABLE if f in pins]


@router.post("/data/{collection}", status_code=201)
def create_item(collection: str, data: dict[str, Any] = Body(...), force: bool = Query(False),
                user: AuthUser = Depends(current_user)):
    """Neuen Eintrag anlegen. Fehlt ``id``, wird eine erzeugt (außer bei Lehrkräften/Klassen/Fächern).
    Stundentafeln: Überschneidung mit einer anderen Tafel → 409 mit Klassenliste (``?force=1`` = trotzdem)."""
    collection = _collection(collection)
    need(user, WRITE_PERM[collection])
    data = dict(data)
    label = LABELS.get(collection, "Eintrag")

    def fn(school: School):
        existing = [x.id for x in getattr(school, collection)]
        if not data.get("id"):
            if collection in ("teachers", "classes", "subjects"):
                raise HTTPException(422, f"{label}: ID (Kürzel) fehlt")
            data["id"] = new_id(existing, ID_PREFIX.get(collection, collection[:1].upper()))
        data["id"] = check_id(str(data["id"]))
        if data["id"] in existing:
            raise HTTPException(409, f"{label} mit ID „{data['id']}“ existiert bereits")
        expand_week_patterns(school, collection, data)
        item = parse_item(collection, data)
        _check_write(user, collection, school, item)
        if collection == "classes" and _plan_fields_changed(None, item) and not has(user, "timetable.edit"):
            raise HTTPException(403, PLAN_FIELDS_403)
        _raise_errors(validate_item(school, collection, item))
        if collection == "teachers":
            _apply_teacher_windows(school, item)
        if collection == "courses":
            item.pinned = []
        getattr(school, collection).append(item)
        if collection == "curricula":
            _check_curriculum(school, item.id, force)
        return item.to_dict()

    return mutate(user, f"{label} {data.get('id') or ''} angelegt".replace("  ", " "), fn,
                  scope=_scope(collection), dates=_dates(collection, data.get("date")))


@router.put("/data/{collection}/{item_id}")
def update_item(collection: str, item_id: str, data: dict[str, Any] = Body(...), force: bool = Query(False),
                user: AuthUser = Depends(current_user)):
    """Eintrag ändern. Fehlende Felder bleiben erhalten (Merge); die ID ist unveränderlich.
    Kurse aus der Stundentafel merken geänderte Felder in ``pinned``; Stundentafeln wie beim Anlegen (409)."""
    collection = _collection(collection)
    need(user, WRITE_PERM[collection])
    label = LABELS.get(collection, "Eintrag")
    if data.get("id") not in (None, "", item_id):
        raise HTTPException(422, "Die ID kann nicht geändert werden (neu anlegen und alten Eintrag löschen)")
    def fn(school: School):
        items = getattr(school, collection)
        for i, old in enumerate(items):
            if old.id == item_id:
                break
        else:
            raise HTTPException(404, f"{label} {item_id} nicht gefunden")
        merged = {**old.to_dict(), **data, "id": item_id}
        if "week_pattern" in data and "weeks" not in data:
            merged["weeks"], merged["rhythm"] = [], None       # das Muster ersetzt die gespeicherte Angabe
        elif data.get("weeks") and "rhythm" not in data:
            merged["rhythm"] = None
        elif data.get("rhythm") and "weeks" not in data:
            merged["weeks"] = []
        expand_week_patterns(school, collection, merged)
        item = parse_item(collection, merged)
        _check_write(user, collection, school, item, old)
        plan_change = collection == "classes" and _plan_fields_changed(old, item)
        if plan_change and not has(user, "timetable.edit"):
            raise HTTPException(403, PLAN_FIELDS_403)
        if plan_change:
            items[i] = item
            class_plan_change(school, old, item, force)
        _raise_errors(validate_item(school, collection, item))
        if collection == "teachers":
            _apply_teacher_windows(school, item)
        if collection == "courses":
            _pin_course(old, item, data)
        items[i] = item
        if collection == "courses":
            _sync_course_change(school, item)
        if collection == "curricula":
            _check_curriculum(school, item_id, force)
        return item.to_dict()

    old = next((x for x in getattr(snapshot()[1], collection) if x.id == item_id), None)
    scope = _scope(collection)
    if collection == "classes" and any(k in data for k in CLASS_PLAN_FIELDS):
        scope = ["classes", "courses", "timetable", "substitutions"]
    return mutate(user, f"{label} {item_id} geändert", fn, scope=scope,
                  dates=_dates(collection, old, data.get("date")))


@router.delete("/data/{collection}/{item_id}")
def delete_item(collection: str, item_id: str, force: bool = Query(False),
                user: AuthUser = Depends(current_user)):
    """Eintrag löschen. Bestehen Verweise → 409 mit Liste; ``?force=1`` entfernt die Verweise."""
    collection = _collection(collection)
    need(user, WRITE_PERM[collection])
    label = LABELS.get(collection, "Eintrag")

    def fn(school: School):
        items = getattr(school, collection)
        old = next((x for x in items if x.id == item_id), None)
        if old is None:
            raise HTTPException(404, f"{label} {item_id} nicht gefunden")
        _check_write(user, collection, school, None, old)
        refs = references(school, collection, item_id)
        if refs and not force:
            raise HTTPException(409, {"message": f"{label} {item_id} wird noch verwendet", "references": refs[:50]})
        if refs:
            cascade_delete(school, collection, item_id)
        setattr(school, collection, [x for x in getattr(school, collection) if x.id != item_id])
        return {"deleted": item_id, "references_removed": len(refs)}

    old = next((x for x in getattr(snapshot()[1], collection) if x.id == item_id), None)
    result = mutate(user, f"{label} {item_id} gelöscht", fn, scope=_scope(collection),
                    dates=_dates(collection, old))
    if collection in ("students", "classes"):
        _note_leavers()
    return result


def _note_leavers() -> None:
    """Löschkonzept (S-01): entfernte Schüler/innen kommen in die Warteliste „ausgetreten“ (Konto gesperrt)."""
    try:
        from schulmanager.server import retention
        from schulmanager.server.db import session_scope

        with session_scope() as db:
            retention.sync_leavers(db)
    except Exception:  # noqa: BLE001 - das Löschen im Planungsdokument darf daran nie scheitern
        import logging
        logging.getLogger("schulmanager.retention").exception("Abgleich der Warteliste fehlgeschlagen")


# ------------------------------------------------------------------ Einstellungen
_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class SiteTravelIn(BaseModel):
    """Wegezeit zwischen zwei Standorten in Minuten (gilt in beide Richtungen)."""
    model_config = ConfigDict(extra="forbid")
    a: str = Field(min_length=1, max_length=40)
    b: str = Field(min_length=1, max_length=40)
    minutes: int = Field(ge=0, le=240)


class WeightsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_gap: Optional[float] = Field(None, ge=0)
    teacher_gap: Optional[float] = Field(None, ge=0)
    late_start: Optional[float] = Field(None, ge=0)
    position: Optional[float] = Field(None, ge=0)
    core_late: Optional[float] = Field(None, ge=0)
    day_balance: Optional[float] = Field(None, ge=0)
    spread: Optional[float] = Field(None, ge=0)
    site_change: Optional[float] = Field(None, ge=0)
    double_split: Optional[float] = Field(None, ge=0)
    teacher_wish: Optional[float] = Field(None, ge=0)


class PolicyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cancel_min_grade: Optional[int] = Field(None, ge=1, le=14)
    edge_strategy: Optional[Literal["cancel", "substitute_if_qualified", "substitute"]] = None
    middle_strategy: Optional[Literal["shift_first", "substitute_first"]] = None
    allow_unqualified: Optional[bool] = None
    max_subs_per_day: Optional[int] = Field(None, ge=0, le=10)


class BreakIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    after: int = Field(ge=0)
    name: str = Field(min_length=1, max_length=80)
    minutes: int = Field(ge=0, le=180)


class SettingsIn(BaseModel):
    """Teil-Update der Einstellungen (nur gesetzte Felder werden übernommen)."""
    model_config = ConfigDict(extra="forbid")
    school_name: Optional[str] = Field(None, min_length=1, max_length=200)
    days: Optional[int] = Field(None, ge=1, le=7)
    periods: Optional[int] = Field(None, ge=1, le=16)
    period_times: Optional[list[str]] = None
    cycle_start: Optional[str] = Field(None, description="Altfeld: Schuljahresbeginn älterer Oberflächen (ein Montag)")
    # Wochen und Schuljahr (R3, §15.3)
    week_numbering: Optional[Literal["school_year", "iso"]] = None
    school_year_start: Optional[str] = Field(None, max_length=10)
    year_start_mode: Optional[Literal["auto", "own"]] = None
    school_year_history: Optional[list[str]] = Field(None, max_length=20)
    school_days: Optional[list[int]] = Field(None, max_length=7)
    # veraltet, wird ignoriert (ältere Oberflächen)
    cycle_weeks: Optional[int] = Field(None, exclude=True)
    cycle_start_week: Optional[int] = Field(None, exclude=True)
    cycle_shifts: Optional[list] = Field(None, exclude=True)
    # Planzeiträume ändert nur ``PUT /calendar/plan-periods``; die Oberfläche schickt das gelesene Feld zurück
    plan_periods: Optional[list] = Field(None, exclude=True)
    site_travel_periods: Optional[int] = Field(None, ge=0, le=5)
    site_travel: Optional[list[SiteTravelIn]] = Field(None, max_length=60)
    core_latest_period: Optional[int] = Field(None, ge=0, le=15)
    weights: Optional[WeightsIn] = None
    policy: Optional[PolicyIn] = None
    public_absent_teachers: Optional[Literal["off", "short", "name"]] = None
    webhooks: Optional[list[str]] = None
    breaks: Optional[list[BreakIn]] = None
    max_exams_per_week: Optional[int] = Field(None, ge=0, le=20)
    max_exams_per_day: Optional[int] = Field(None, ge=0, le=5)
    # Vorgaben je Jahrgang ``{"5": {"per_week": 2, "per_day": 1}}`` (Schule → Jahrgang → Klasse)
    exam_limits_by_grade: Optional[dict[str, dict]] = None
    # Regeln und Prioritäten als Bausteine (``schulmanager/rules.py``); bequemer über ``/settings/rules``
    rules: Optional[dict] = None
    # Erweiterung 2 (§9.1)
    period_minutes: Optional[int] = Field(None, ge=5, le=240, description="Dauer einer Unterrichtsstunde (Minuten)")
    teacher_self_service: Optional[Literal["approval", "direct"]] = None
    sick_note_after_days: Optional[int] = Field(None, ge=0, le=60)
    sick_phone: Optional[str] = Field(None, max_length=60)
    sick_phone_hours: Optional[str] = Field(None, max_length=120)
    messaging_students_to_students: Optional[bool] = None
    messaging_retention_days: Optional[int] = Field(None, ge=0, le=3650)
    trash_retention_days: Optional[int] = Field(None, ge=1, le=365, description="Kursraum-Papierkorb: Tage bis zum endgültigen Löschen")
    subject_teacher_absence_view: Optional[Literal["none", "presence"]] = None
    absence_limit_percent: Optional[float] = Field(None, ge=0, le=100, description="Zulässige Fehlzeit je Fach in % (0 = keine)")
    absence_limit_unexcused_percent: Optional[float] = Field(None, ge=0, le=100)
    auto_replan: Optional[bool] = Field(None, description="Stundenplan nach Änderungen automatisch reparieren")
    plan_auto_apply: Optional[Literal["aus", "raeume"]] = Field(
        None, description="Kleine Lösungen (nur Räume) ohne Rückfrage übernehmen; Standard aus")
    substitution_confirm: Optional[bool] = Field(
        None, description="Vertretungsvorschläge erst nach Freigabe aktiv (Bestätigungsmodus)")
    prefer_doubles: Optional[bool] = Field(None, description="Fächer ab 2 Wochenstunden als Doppelstunden planen")
    teacher_times_self: Optional[bool] = Field(None, description="Lehrkräfte dürfen Arbeitszeiten selbst festlegen")
    double_alignment: Optional[Literal["bloecke", "pausen", "frei"]] = Field(
        None, description="Doppelstunden nur in Pausenblöcken / nicht über Pausen / frei")


def settings_errors(s: Settings) -> list[str]:
    errs = []
    if len(s.period_times) < s.periods:
        errs.append(f"Für {s.periods} Stunden werden {s.periods} Anfangszeiten benötigt")
    bad = [t for t in s.period_times if not _TIME.match(t)]
    if bad:
        errs.append(f"Ungültige Uhrzeit(en): {', '.join(bad[:5])} (Format HH:MM)")
    elif s.period_times != sorted(s.period_times):
        errs.append("Die Anfangszeiten müssen aufsteigend sein")
    try:
        date.fromisoformat(s.cycle_start)
    except ValueError:
        errs.append("Ungültiger Schuljahresbeginn (cycle_start)")
    errs += calendar_errors(s)
    for b in s.breaks:
        if not 0 <= int(b.get("after", -1)) < s.periods - 1:
            errs.append(f"Pause „{b.get('name')}“ liegt außerhalb des Zeitrasters")
    for url in s.webhooks:
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", url):
            errs.append(f"Ungültige Webhook-URL: {url}")
        else:
            problem = net_guard.validate_url(url, "webhook")     # SSRF: nur öffentliche https-Ziele (S-05)
            if problem:
                errs.append(f"Webhook-URL {url[:80]}: {problem}")
    if s.core_latest_period >= s.periods:
        errs.append("Späteste Hauptfachstunde liegt außerhalb des Zeitrasters")
    return errs


def calendar_errors(s: Settings) -> list[str]:
    """Prüft Schuljahr, Zählung und Unterrichtstage (Grenzen §14.6/§15.3)."""
    from schulmanager.calendar_utils import year_bounds
    errs: list[str] = []
    if s.school_year_start and not _date_ok(s.school_year_start):
        errs.append("Ungültiger Schuljahresbeginn")
    hist = []
    for x in s.school_year_history:
        if not _date_ok(x):
            errs.append(f"Ungültiges Datum im Schuljahresverlauf: {x}")
        else:
            hist.append(date.fromisoformat(x))
    if hist != sorted(hist) or any((b - a).days < 300 for a, b in zip(hist, hist[1:])):
        errs.append("Frühere Schuljahre: aufsteigend und mindestens 300 Tage auseinander")
    days = s.school_days
    if days and (any(not isinstance(d, int) or not 0 <= d <= 6 for d in days) or len(set(days)) != len(days)):
        errs.append("Unterrichtstage: nur Montag bis Sonntag, jeder Tag einmal")
    if not errs:
        try:
            year_bounds(s, date.today())
        except (ValueError, OverflowError):
            errs.append("Ungültiges Schuljahr")
    return errs


def _calendar_patch(old: Settings, cur: dict, patch: dict) -> Settings:
    """Wendet die Kalenderregeln beim Speichern an: ``days`` ↔ ``school_days``, ``cycle_start`` (alt) →
    ``school_year_start``, Schuljahresverlauf (W4)."""
    from schulmanager.calendar_utils import base_start
    if patch.get("school_days"):
        cur["school_days"] = sorted(set(patch["school_days"]))
        cur["days"] = max(cur["school_days"]) + 1
    elif patch.get("days") is not None and patch["days"] != old.days and "school_days" not in patch:
        cur["school_days"] = []
    if patch.get("cycle_start") and patch["cycle_start"] != old.cycle_start and not old.school_year_start \
            and "school_year_start" not in patch:
        cur["school_year_start"] = patch["cycle_start"]   # ältere Oberfläche: Woche 1 beginnt ab hier
    if patch.get("school_year_start") and "year_start_mode" not in patch \
            and patch["school_year_start"] != (old.school_year_start or old.cycle_start):
        cur["year_start_mode"] = "own"        # eigenes Datum eingetragen = eigener Schulstart
    new = Settings.from_dict(cur)
    old_start, new_start = base_start(old), base_start(new)
    if new.school_year_start and old_start != new_start and (new_start - old_start).days >= 300:
        hist = sorted(set(new.school_year_history) | {old_start.isoformat()})
        new.school_year_history = hist[-20:]
    return new


@router.get("/settings")
def get_settings(user: AuthUser = Depends(current_user)):
    """Einstellungen (Webhook-URLs nur mit ``settings.edit``)."""
    data = snapshot()[1].settings.to_dict()
    if not has(user, "settings.edit"):
        data["webhooks"] = []
    return data


def _merged_settings(school: School, patch: dict) -> Settings:
    from schulmanager import rules as rl
    cur = copy.deepcopy(school.settings.to_dict())
    for key, value in patch.items():
        if key in ("weights", "policy") and isinstance(value, dict):
            cur[key] = {**cur.get(key, {}), **{k: v for k, v in value.items() if v is not None}}
        elif value is not None:
            cur[key] = value
    new = _calendar_patch(school.settings, cur, patch)
    if patch.get("exam_limits_by_grade") is not None:
        _raise_errors(rl.exam_limit_errors(patch["exam_limits_by_grade"]))
        new.exam_limits_by_grade = rl.normalize_exam_limits(patch["exam_limits_by_grade"])
    # Regel-Bausteine und Zahlen in beide Richtungen angleichen (ältere Oberflächen setzen nur die Zahlen)
    if patch.get("rules") is not None:
        _raise_errors(rl.rule_errors(patch["rules"], school))
        rl.apply_to_settings(new, patch["rules"])
    else:
        numeric = {f"weights.{k}" for k, v in (patch.get("weights") or {}).items() if v is not None}
        numeric |= {k for k in ("core_latest_period", "site_travel_periods", "prefer_doubles", "double_alignment",
                                "auto_replan") if patch.get(k) is not None}
        if numeric:
            rl.sync_from_numbers(new, numeric)
    return new


RASTER_KEYS = ("days", "periods", "period_times", "period_minutes", "school_days")


@router.put("/settings")
def put_settings(body: SettingsIn, user: AuthUser = Depends(require("settings.edit"))):
    """Einstellungen ändern (Teil-Update; verschachtelte ``weights``/``policy`` werden gemischt).

    Wochenangaben (Kurse, Sperrzeiten, Aufsichten …) zählen die laufenden Wochen ab dem Schuljahresbeginn."""
    patch = body.model_dump(exclude_unset=True)
    from schulmanager.server import demo_guard
    demo_guard.forbid_fields(patch, ("webhooks",))          # Webhooks haben Außenwirkung (S-03/S-05)
    from schulmanager.legacy import strip_legacy_fields
    strip_legacy_fields(patch)

    def fn(school: School):
        cs = patch.get("cycle_start")
        if cs and cs != school.settings.cycle_start and (not _date_ok(cs) or date.fromisoformat(cs).weekday() != 0):
            raise HTTPException(422, "Schuljahresbeginn (cycle_start) muss ein Montag sein")
        new = _merged_settings(school, patch)
        _raise_errors(settings_errors(new))
        changed_raster = any(getattr(school.settings, k) != getattr(new, k) for k in RASTER_KEYS)
        old_settings = school.settings
        school.settings = new
        if patch.get("year_start_mode") == "auto":
            from schulmanager.calendar_utils import apply_auto_year_start
            apply_auto_year_start(school)     # Beginn aus den Sommerferien; ohne Ferien bleibt das Datum
        calendar_changed = any(getattr(school.settings, k, None) != getattr(old_settings, k, None)
                               for k in ("school_year_start", "week_numbering", "cycle_start"))
        if calendar_changed:                    # Planzeiträume: Wochen aus den Daten neu berechnen
            from schulmanager.plan_periods import refresh
            refresh(school)
        if changed_raster or calendar_changed:  # Zeitfenster → Sperrzeiten; „gilt ab“-Wochen der Regeln neu berechnen
            from schulmanager.teacher_profile import refresh_all_windows
            refresh_all_windows(school)
        return new.to_dict()

    scope = ["settings", "teachers"] if set(RASTER_KEYS) & set(patch) else ["settings"]
    calendar_keys = {"school_year_start", "year_start_mode", "week_numbering", "cycle_start"}
    if calendar_keys & set(patch):
        scope = sorted(set(scope) | {"settings", "timetable", "substitutions", "teachers"})
    return mutate(user, "Einstellungen geändert", fn, scope=scope)


class CalendarPreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    week_numbering: Optional[Literal["school_year", "iso"]] = None
    year_start_mode: Optional[Literal["auto", "own"]] = None
    school_year_start: Optional[str] = Field(None, max_length=10)
    school_days: Optional[list[int]] = Field(None, max_length=7)
    # veraltet, wird ignoriert (ältere Oberflächen)
    cycle_weeks: Optional[int] = Field(None, exclude=True)
    cycle_start_week: Optional[int] = Field(None, exclude=True)
    cycle_shifts: Optional[list] = Field(None, exclude=True)


@router.post("/settings/calendar-preview")
def calendar_preview(body: CalendarPreviewIn, user: AuthUser = Depends(require("settings.edit"))):
    """Wirkung einer Kalenderänderung vorab: ``{today_before, today_after, warnings}`` (speichert nichts)."""
    from schulmanager.calendar_utils import week_info, year_warnings
    from schulmanager.server.store import copy_school

    patch = body.model_dump(exclude_unset=True)
    school = copy_school(snapshot()[1])
    today = date.today()
    new = _merged_settings(school, patch)
    _raise_errors(calendar_errors(new))
    before = week_info(school, today)
    school.settings = new
    return {"today_before": before, "today_after": week_info(school, today),
            "warnings": year_warnings(school, today)}
