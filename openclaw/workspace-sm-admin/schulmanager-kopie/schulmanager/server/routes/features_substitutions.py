"""Vertretungsplan, Abwesenheiten, manuelle Entscheidungen (Overrides),
persönliche Tages-/Wochenansicht und Monitor.

Alle Änderungen laufen über ``store.mutate`` (Version, Audit, Event ``change`` mit
``dates``). Vertretungspläne werden pro ``(store.version, datum)`` gecacht.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from schulmanager.models import Absence, Course, Override, School
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import (absence_reasons, absences_for_day, cached, check_range, day_plan,
                              effective_cells, family_student_ids, filter_plan, has, index, is_scoped_teacher, iso_dates,
                              lesson_by_id, mutate, new_id, now_iso, own_class_ids, parse_date,
                              pupil_entry_filter, range_plan_objects, range_plans, scrub, snapshot,
                              teacher_course_ids, week_history)

router = APIRouter(tags=["Vertretungsplan"])

MAX_ABSENCE_DAYS = 366
MAX_SELF_REPORT_DAYS = 42

AbsenceKind = Literal["teacher", "class", "room", "lesson"]
_ABSENCE_COLL = {"teacher": "teachers", "class": "classes", "room": "rooms"}
_ABSENCE_WHAT = {"teacher": "Lehrkraft", "class": "Klasse", "room": "Raum", "lesson": "Unterricht"}


# =================================================================== Hilfen
def _clean_cells(cells: list[dict], reasons: list[str]) -> list[dict]:
    if not reasons:
        return cells
    out = []
    for c in cells:
        if c.get("note"):
            c = {**c, "note": scrub(c["note"], reasons)}
        out.append({k: v for k, v in c.items() if k not in ("reason", "absence_reason")})
    return out


def _class_key(value: str):
    m = re.match(r"^(\D*)(\d+)(.*)$", value or "")
    if not m:
        return (value or "", 0, "")
    return (m.group(1), int(m.group(2)), m.group(3))


def _entry_sort_key(e: dict):
    classes = e.get("classes") or []
    return (_class_key(classes[0]) if classes else ("~", 0, ""), e.get("period", 0), e.get("part", 0))


def _absence_dates(a: Absence) -> list[str]:
    try:
        return iso_dates(date.fromisoformat(a.date_from), date.fromisoformat(a.date_to))
    except ValueError:
        return []


def _lesson_target(courses: dict[str, Course], ref: str) -> tuple[Optional[Course], Optional[int]]:
    """Kurs und Kursteil einer ``lesson``-Referenz (``"<course_id>[#<part>]"``); ``(None, None)`` wenn ungültig."""
    from schulmanager.substitution import split_lesson_ref
    try:
        cid, part = split_lesson_ref(ref)
    except ValueError:
        return None, None
    return courses.get(cid), part


def _lesson_ref_name(school: School, ref: str) -> str:
    """Kursbezeichnung (bei gekoppelten Kursen mit Kursteil, z. B. „Religion/PP 5a+5b – ev“)."""
    course, part = _lesson_target(school.index("courses"), ref)
    if course is None:
        return ""
    name = course.label or course.id
    if part is not None and len(course.parts) > 1 and 0 <= part < len(course.parts):
        p = course.parts[part]
        name += f" – {p.label or p.subject}"
    return name


def _validate_lesson_ref(school: School, ref: str) -> None:
    from schulmanager.substitution import split_lesson_ref
    try:
        cid, part = split_lesson_ref(ref)
    except ValueError:
        raise HTTPException(422, f"Ungültiger Kursteil in „{ref}“ (erwartet Kurs oder Kurs#Teil)") from None
    course = school.index("courses").get(cid)
    if course is None:
        raise HTTPException(422, f"Kurs „{cid}“ existiert nicht")
    if part is not None and not 0 <= part < len(course.parts):
        raise HTTPException(422, f"Kurs „{course.label or course.id}“ hat keinen Kursteil {part}")


def _validate_absence(school: School, a: Absence) -> None:
    if a.kind == "lesson":
        _validate_lesson_ref(school, a.ref)
    elif a.ref not in school.index(_ABSENCE_COLL[a.kind]):
        raise HTTPException(422, f"{_ABSENCE_WHAT[a.kind]} „{a.ref}“ existiert nicht")
    d1, d2 = date.fromisoformat(a.date_from), date.fromisoformat(a.date_to)
    if d2 < d1:
        raise HTTPException(422, "Das Enddatum liegt vor dem Startdatum")
    if (d2 - d1).days >= MAX_ABSENCE_DAYS:
        raise HTTPException(422, f"Abwesenheit zu lang (maximal {MAX_ABSENCE_DAYS} Tage)")
    if any(not 0 <= p < school.settings.periods for p in a.periods):
        raise HTTPException(422, "Ungültige Stunde in der Abwesenheit")


def _absence_out(a: Absence, user, school: School) -> dict:
    d = a.to_dict()
    if not has(user, "substitution.edit"):
        own = a.kind == "teacher" and a.ref == getattr(user, "teacher_id", None)
        if not own:
            d["reason"] = ""
    ref_name = ""
    coll = _ABSENCE_COLL.get(a.kind)
    if coll:
        obj = school.index(coll).get(a.ref)
        ref_name = getattr(obj, "name", "") if obj else ""
    elif a.kind == "lesson":
        ref_name = _lesson_ref_name(school, a.ref)
    d["ref_name"] = ref_name
    return d


def _exam_rows(school: School, exams, parts_filter=None) -> list[dict]:
    from .features_exams import exam_info
    return [exam_info(school, e) for e in exams if parts_filter is None or parts_filter(e)]


def _student_exam_filter(snap, sid: str):
    from .features_common import student_parts
    parts = student_parts(sid, snap)

    def ok(e) -> bool:
        return e.course_id in parts and (e.part is None or e.part in parts[e.course_id])

    return ok


# =================================================================== Vertretungsplan
@router.get("/substitutions")
def substitutions(date_: Optional[str] = Query(None, alias="date"), site: Optional[str] = None,
                  class_id: Optional[str] = None, teacher: Optional[str] = None, public: bool = False,
                  user: AuthUser = Depends(require("substitution.read"))):
    """Vertretungsplan eines Tages (Standard: heute), nach Rolle gefiltert. Recht ``substitution.read`` – Schüler/innen
    und Eltern haben es nicht (ihre Änderungen stehen im eigenen Stundenplan: ``/calendar/week``, ``/me/week``).

    Mit ``substitution.edit`` zusätzlich ``absences`` (inkl. Gründe) und ``overrides`` des Tages.
    ``public=1`` (Druck/Aushang): öffentliche Sicht wie der Monitor (ohne Gründe, Aufsichten, Warnungen;
    abwesende Lehrkräfte laut ``settings.public_absent_teachers``) – im Datenumfang der Rolle."""
    day = parse_date(date_)
    snap = snapshot()
    # Vertretungsplanung sieht im Bestätigungsmodus auch die noch nicht freigegebenen Vorschläge (``proposed``)
    _, plan = day_plan(day, snap, proposals=has(user, "substitution.edit") and not public)
    out = filter_plan(user, plan, snap, site=site, class_id=class_id, teacher=teacher, public=public)
    out["version"] = snap[0]
    out["confirm_mode"] = bool(getattr(snap[1].settings, "substitution_confirm", False))
    if has(user, "substitution.edit") and not public:
        out["absences"] = [_absence_out(Absence.from_dict(a), user, snap[1])
                           for a in absences_for_day(snap[1], day)]
        out["overrides"] = [o.to_dict() for o in snap[1].overrides if o.date == day.isoformat()]
    return out


@router.get("/substitutions/range")
def substitutions_range(date_from: Optional[str] = Query(None, alias="from"),
                        date_to: Optional[str] = Query(None, alias="to"), site: Optional[str] = None,
                        class_id: Optional[str] = None, teacher: Optional[str] = None,
                        user: AuthUser = Depends(require("substitution.read"))):
    """Vertretungspläne für einen Zeitraum (max. 31 Tage, faire Historie über den Zeitraum)."""
    d1 = parse_date(date_from, name="from")
    d2 = parse_date(date_to, d1 + timedelta(days=6), name="to")
    check_range(d1, d2, 31)
    snap = snapshot()
    plans = range_plans(d1, d2, snap, proposals=has(user, "substitution.edit"))
    return [filter_plan(user, p, snap, site=site, class_id=class_id, teacher=teacher) for p in plans]


@router.get("/substitutions/candidates")
def candidates(date_: Optional[str] = Query(None, alias="date"), lesson_id: str = Query(...),
               period: int = Query(..., ge=0, le=15), part: int = Query(0, ge=0),
               user: AuthUser = Depends(require("substitution.edit"))):
    """Rangliste möglicher Vertretungslehrkräfte für eine Stunde."""
    day = parse_date(date_)
    snap = snapshot()
    if lesson_by_id(snap[1], lesson_id) is None:
        raise HTTPException(404, f"Stunde {lesson_id} nicht gefunden")

    def compute():
        from schulmanager.substitution import rank_candidates
        return rank_candidates(snap[1], day, lesson_id, period, part, week_history(day, snap))

    return cached("candidates", (day.isoformat(), lesson_id, period, part), compute, snap)


@router.get("/substitutions/stats")
def stats(date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
          user: AuthUser = Depends(current_user)):
    """Statistik je Lehrkraft (Vertretungen, Entfall, Aufsichten). Lehrkräfte sehen nur sich selbst."""
    if not has(user, "substitution.edit") and not getattr(user, "teacher_id", None):
        raise HTTPException(403, "Keine Berechtigung")
    today = date.today()
    d1 = parse_date(date_from, today - timedelta(days=today.weekday()), name="from")
    d2 = parse_date(date_to, d1 + timedelta(days=6), name="to")
    check_range(d1, d2, 190)
    snap = snapshot()

    def compute():
        from schulmanager.substitution import teacher_stats
        return teacher_stats(snap[1], d1, d2, range_plan_objects(d1, d2, snap))

    rows = cached("teacher_stats", (d1.isoformat(), d2.isoformat()), compute, snap)
    if not has(user, "substitution.edit"):
        rows = [r for r in rows if r.get("teacher") == user.teacher_id]
    return {"from": d1.isoformat(), "to": d2.isoformat(), "teachers": rows}


# =================================================================== Abwesenheiten
class AbsenceIn(BaseModel):
    kind: AbsenceKind
    # teacher/class/room: ID; lesson („Unterricht findet nicht statt“): "<course_id>" oder "<course_id>#<part>"
    ref: str = Field(min_length=1, max_length=80)
    date_from: date
    date_to: Optional[date] = None
    periods: list[int] = Field(default_factory=list)
    reason: str = Field("", max_length=500)


class SelfReportIn(BaseModel):
    date_from: date
    date_to: Optional[date] = None
    periods: list[int] = Field(default_factory=list)
    reason: str = Field("krank", max_length=500)


def _absence_from(body, absence_id: str, kind: str, ref: str) -> Absence:
    d2 = body.date_to or body.date_from
    return Absence(id=absence_id, kind=kind, ref=ref, date_from=body.date_from.isoformat(),
                   date_to=d2.isoformat(), periods=sorted(set(body.periods)), reason=body.reason.strip())


@router.get("/absences")
def list_absences(date_from: Optional[str] = Query(None, alias="from"),
                  date_to: Optional[str] = Query(None, alias="to"),
                  kind: Optional[AbsenceKind] = None, ref: Optional[str] = None,
                  user: AuthUser = Depends(current_user)):
    """Abwesenheiten (Standard: ab heute). Gründe nur mit ``substitution.edit`` (bzw. eigene).

    Lehrkräfte (Scope ``own_classes``) sehen nur die eigenen Abwesenheiten, Abwesenheiten ihrer Klassen und
    entfallenden Unterricht (``lesson``) eigener Kurse bzw. von Kursen ihrer Klassen. ``ref`` filtert bei
    ``lesson`` auch nach der Kurs-ID (``ref=K1`` findet ``K1`` und ``K1#0``)."""
    if not (has(user, "substitution.edit") or has(user, "plans.read_all")):
        if not has(user, "absence.report_self"):
            raise HTTPException(403, "Keine Berechtigung")
    d1 = parse_date(date_from, date.today(), name="from")
    d2 = parse_date(date_to, date(9999, 12, 31), name="to") if date_to else None
    snap = snapshot()
    full = has(user, "substitution.edit") or (has(user, "plans.read_all") and not is_scoped_teacher(user))
    own_classes = own_class_ids(user, snap) if is_scoped_teacher(user) else frozenset()
    tid = getattr(user, "teacher_id", None)
    own_courses = teacher_course_ids(tid, snap) if tid and not full else frozenset()
    courses = index("courses", snap)
    out = []
    for a in snap[1].absences:
        if kind and a.kind != kind:
            continue
        course = _lesson_target(courses, a.ref)[0] if a.kind == "lesson" else None
        if ref and a.ref != ref and not (course is not None and course.id == ref):
            continue
        if not full:
            own = a.kind == "teacher" and a.ref == tid
            own_class = a.kind == "class" and a.ref in own_classes
            own_lesson = course is not None and (course.id in own_courses or bool(set(course.classes) & own_classes))
            if not (own or own_class or own_lesson):
                continue
        try:
            if date.fromisoformat(a.date_to) < d1 or (d2 and date.fromisoformat(a.date_from) > d2):
                continue
        except ValueError:
            continue
        out.append(_absence_out(a, user, snap[1]))
    out.sort(key=lambda x: (x["date_from"], x["kind"], x["ref"]))
    return out


@router.post("/absences", status_code=201)
def create_absence(body: AbsenceIn, user: AuthUser = Depends(require("substitution.edit"))):
    """Abwesenheit von Lehrkraft, Klasse (Exkursion) oder Raum (Sperre) erfassen – bzw. ``kind="lesson"``:
    Unterricht eines Kurses (``ref="<course_id>"``) oder Kursteils (``"<course_id>#<part>"``) findet nicht statt."""

    def fn(school: School):
        a = _absence_from(body, new_id([x.id for x in school.absences], "A"), body.kind, body.ref.strip())
        _validate_absence(school, a)
        school.absences.append(a)
        return _absence_out(a, user, school)

    a_preview = _absence_from(body, "x", body.kind, body.ref)
    span = f"{body.ref} {a_preview.date_from}–{a_preview.date_to}"
    label = f"Unterricht entfällt {span}" if body.kind == "lesson" else f"Abwesenheit {_ABSENCE_WHAT[body.kind]} {span}"
    return mutate(user, label, fn, scope=["absences", "substitutions"], dates=_absence_dates(a_preview))


PREVIEW_MAX_SCHOOL_DAYS = 31      # darüber keine Zählung der betroffenen Stunden (Rechenzeit)


@router.post("/absences/preview")
def preview_absence(body: AbsenceIn, absence_id: Optional[str] = Query(None, max_length=40),
                    user: AuthUser = Depends(require("substitution.edit"))):
    """Vorschau vor dem Speichern (ändert nichts): Schultage im Zeitraum, Ferien/Feiertage darin und – bis
    ``PREVIEW_MAX_SCHOOL_DAYS`` Schultage – die Zahl der Plan-Einträge, die sich durch die Abwesenheit ändern
    (``affected``, sonst ``null``). ``absence_id``: beim Bearbeiten die bisherige Abwesenheit ausklammern."""
    from dataclasses import replace

    from schulmanager.calendar_utils import is_school_day
    from schulmanager.substitution import compute_range

    snap = snapshot()
    school: School = snap[1]
    a = _absence_from(body, "preview", body.kind, body.ref.strip())
    _validate_absence(school, a)
    d1, d2 = date.fromisoformat(a.date_from), date.fromisoformat(a.date_to)
    school_days: list[date] = []
    free_names: list[str] = []
    free_days = 0
    cur = d1
    while cur <= d2:
        ok, reason = is_school_day(school, cur)
        if ok:
            school_days.append(cur)
        elif reason not in ("Wochenende", "Kein Unterrichtstag"):
            free_days += 1
            if reason and reason not in free_names:
                free_names.append(reason)
        cur += timedelta(days=1)
    affected: Optional[int] = None
    if school_days and len(school_days) <= PREVIEW_MAX_SCHOOL_DAYS:
        rest = [x for x in school.absences if x.id != absence_id]
        first, last = school_days[0], school_days[-1]

        def signature(sch: School) -> set[tuple]:
            return {(e["id"], e["kind"], e.get("substitute"), e.get("room"), e.get("note"))
                    for plan in compute_range(sch, first, last) if plan.date in school_days for e in plan.entries}

        before = signature(replace(school, absences=rest))
        after = signature(replace(school, absences=[*rest, a]))
        affected = len(after - before)
    return {"days": (d2 - d1).days + 1, "school_days": len(school_days), "free_days": free_days,
            "free_names": free_names, "affected": affected}


@router.put("/absences/{absence_id}")
def update_absence(absence_id: str, body: AbsenceIn, user: AuthUser = Depends(require("substitution.edit"))):
    snap = snapshot()
    old = next((a for a in snap[1].absences if a.id == absence_id), None)
    if old is None:
        raise HTTPException(404, f"Abwesenheit {absence_id} nicht gefunden")
    new_preview = _absence_from(body, absence_id, body.kind, body.ref.strip())

    def fn(school: School):
        for i, a in enumerate(school.absences):
            if a.id == absence_id:
                _validate_absence(school, new_preview)
                new = Absence.from_dict(new_preview.to_dict())
                # bleibt eine Selbstmeldung, solange sie dieselbe Lehrkraft betrifft
                new.self_reported = a.self_reported and (a.kind, a.ref) == (new.kind, new.ref)
                school.absences[i] = new
                return _absence_out(school.absences[i], user, school)
        raise HTTPException(404, f"Abwesenheit {absence_id} nicht gefunden")

    return mutate(user, f"Abwesenheit {absence_id} geändert", fn, scope=["absences", "substitutions"],
                  dates=_absence_dates(old) + _absence_dates(new_preview))


@router.delete("/absences/{absence_id}")
def delete_absence(absence_id: str, user: AuthUser = Depends(current_user)):
    """Abwesenheit löschen (``substitution.edit``; Lehrkräfte: nur die eigene, selbst gemeldete und noch nicht
    vergangene Krankmeldung – vom Sekretariat erfasste Abwesenheiten wie Fortbildung oder Kur nicht)."""
    snap = snapshot()
    old = next((a for a in snap[1].absences if a.id == absence_id), None)
    if old is None:
        raise HTTPException(404, f"Abwesenheit {absence_id} nicht gefunden")
    if not has(user, "substitution.edit"):
        mine = (has(user, "absence.report_self") and old.kind == "teacher"
                and old.ref == getattr(user, "teacher_id", None))
        if not mine:
            raise HTTPException(403, "Keine Berechtigung")
        if not old.self_reported:
            raise HTTPException(403, "Löschen können Sie nur selbst gemeldete Krankmeldungen – bitte wenden Sie sich "
                                     "an das Sekretariat")
        if old.date_to < date.today().isoformat():
            raise HTTPException(403, "Vergangene Krankmeldungen können nicht mehr gelöscht werden")

    def fn(school: School):
        before = len(school.absences)
        school.absences = [a for a in school.absences if a.id != absence_id]
        if len(school.absences) == before:
            raise HTTPException(404, f"Abwesenheit {absence_id} nicht gefunden")
        return {"deleted": absence_id}

    return mutate(user, f"Abwesenheit {absence_id} gelöscht", fn, scope=["absences", "substitutions"],
                  dates=_absence_dates(old))


@router.post("/absences/report-self", status_code=201)
def report_self(body: SelfReportIn, user: AuthUser = Depends(require("absence.report_self"))):
    """Krankmeldung einer Lehrkraft für sich selbst (ab heute, max. 6 Wochen)."""
    tid = getattr(user, "teacher_id", None)
    if not tid:
        raise HTTPException(409, "Ihr Konto ist mit keiner Lehrkraft verknüpft")
    today = date.today()
    d2 = body.date_to or body.date_from
    if body.date_from < today:
        raise HTTPException(422, "Krankmeldungen sind nur ab heute möglich")
    if d2 < body.date_from:
        raise HTTPException(422, "Das Enddatum liegt vor dem Startdatum")
    if (d2 - body.date_from).days >= MAX_SELF_REPORT_DAYS:
        raise HTTPException(422, f"Zeitraum zu lang (maximal {MAX_SELF_REPORT_DAYS} Tage) – "
                                 "bitte das Sekretariat kontaktieren")
    preview = _absence_from(body, "x", "teacher", tid)

    def fn(school: School):
        if tid not in school.index("teachers"):
            raise HTTPException(409, f"Lehrkraft {tid} existiert nicht mehr")
        for a in school.absences:
            if (a.kind, a.ref, a.date_from, a.date_to, sorted(a.periods)) == (
                    "teacher", tid, preview.date_from, preview.date_to, preview.periods):
                return {**_absence_out(a, user, school), "duplicate": True}
        a = Absence.from_dict({**preview.to_dict(), "id": new_id([x.id for x in school.absences], "A")})
        a.reason = a.reason or "krank"
        a.self_reported = True
        _validate_absence(school, a)
        school.absences.append(a)
        return _absence_out(a, user, school)

    return mutate(user, f"Krankmeldung (Selbstmeldung) {tid} {preview.date_from}–{preview.date_to}", fn,
                  scope=["absences", "substitutions"], dates=_absence_dates(preview))


# =================================================================== Overrides
class OverrideIn(BaseModel):
    date: date
    lesson_id: str = Field(min_length=1)
    period: int = Field(ge=0, le=15)
    part: int = Field(0, ge=0)
    action: Literal["substitute", "cancel", "keep", "room"] = "substitute"
    teacher: Optional[str] = None
    room: Optional[str] = None
    note: str = Field("", max_length=500)
    all_periods: bool = Field(False, description="Für alle Stunden des Blocks (Doppelstunde) setzen")


@router.get("/overrides")
def list_overrides(date_: Optional[str] = Query(None, alias="date"),
                   date_from: Optional[str] = Query(None, alias="from"),
                   date_to: Optional[str] = Query(None, alias="to"),
                   user: AuthUser = Depends(require("substitution.edit"))):
    """Manuelle Entscheidungen (``date`` oder ``from``/``to``; ohne Angabe ab heute)."""
    snap = snapshot()
    if date_:
        d1 = d2 = parse_date(date_)
    else:
        d1 = parse_date(date_from, date.today(), name="from")
        d2 = parse_date(date_to, date(9999, 12, 31), name="to")
    out = [o.to_dict() for o in snap[1].overrides if d1.isoformat() <= o.date <= d2.isoformat()]
    return sorted(out, key=lambda o: (o["date"], o["period"], o["lesson_id"]))


@router.post("/overrides", status_code=201)
def create_override(body: OverrideIn, user: AuthUser = Depends(require("substitution.edit"))):
    """Setzt eine manuelle Entscheidung (ersetzt eine bestehende für dieselbe Stunde/denselben Teil)."""
    day = body.date.isoformat()

    def fn(school: School):
        les = lesson_by_id(school, body.lesson_id)
        if les is None:
            raise HTTPException(404, f"Stunde {body.lesson_id} nicht gefunden")
        course = school.index("courses").get(les.course_id)
        if course is None:
            raise HTTPException(409, f"Kurs {les.course_id} existiert nicht mehr")
        if not les.start <= body.period < les.start + les.length:
            raise HTTPException(422, "Die Stunde liegt nicht in diesem Unterrichtsblock")
        if body.part >= len(course.parts):
            raise HTTPException(422, "Ungültiger Kursteil")
        if body.action == "substitute":
            if not body.teacher:
                raise HTTPException(422, "Für eine Vertretung muss eine Lehrkraft angegeben werden")
        if body.teacher and body.teacher not in school.index("teachers"):
            raise HTTPException(422, f"Lehrkraft „{body.teacher}“ existiert nicht")
        if body.action == "room" and not body.room:
            raise HTTPException(422, "Für eine Raumänderung muss ein Raum angegeben werden")
        if body.room and body.room not in school.index("rooms"):
            raise HTTPException(422, f"Raum „{body.room}“ existiert nicht")
        periods = list(range(les.start, les.start + les.length)) if body.all_periods else [body.period]
        created = []
        for p in periods:
            school.overrides = [o for o in school.overrides
                                if not (o.date == day and o.lesson_id == les.id and o.period == p
                                        and o.part == body.part)]
            ov = Override(id=new_id([o.id for o in school.overrides], "O"), date=day, lesson_id=les.id,
                          period=p, part=body.part, action=body.action,
                          teacher=body.teacher if body.action != "cancel" else None,
                          room=body.room, note=body.note.strip())
            school.overrides.append(ov)
            created.append(ov.to_dict())
        return created[0] if len(created) == 1 else {**created[0], "created": created}

    return mutate(user, f"Vertretungsentscheidung {day} {body.lesson_id} ({body.action})", fn,
                  scope=["overrides", "substitutions"], dates=[day])


class ReleaseIn(BaseModel):
    date: date
    entry_ids: Optional[list[str]] = Field(None, max_length=500, description="Nur diese Vorschläge (IDs der Einträge); "
                                                                           "ohne Angabe alle des Tages")


@router.post("/substitutions/release")
def release_proposals(body: ReleaseIn, user: AuthUser = Depends(require("substitution.edit"))):
    """Bestätigungsmodus (``settings.substitution_confirm``): gibt automatisch berechnete Vertretungsvorschläge eines
    Tages frei. Jeder Vorschlag wird zur manuellen Entscheidung (Vertretung durch die vorgeschlagene Lehrkraft) und ist
    damit für alle sichtbar; Benachrichtigungen folgen wie bei jeder Änderung."""
    snap = snapshot()
    if not getattr(snap[1].settings, "substitution_confirm", False):
        raise HTTPException(409, "Der Bestätigungsmodus ist ausgeschaltet – alle Vorschläge gelten sofort")
    day = body.date.isoformat()
    _, plan = day_plan(body.date, snap, proposals=True)
    wanted = set(body.entry_ids or [])
    items = [e for e in plan.get("entries", []) if e.get("proposed") and (not wanted or e["id"] in wanted)]
    if not items:
        raise HTTPException(404, "Keine offenen Vorschläge zum Freigeben")

    def fn(school: School):
        for e in items:
            school.overrides = [o for o in school.overrides
                                if not (o.date == day and o.lesson_id == e["lesson_id"] and o.period == e["period"]
                                        and o.part == e["part"])]
            school.overrides.append(Override(id=new_id([o.id for o in school.overrides], "O"), date=day,
                                             lesson_id=e["lesson_id"], period=e["period"], part=e["part"],
                                             action="substitute", teacher=e["substitute"], room=None, note=""))
        return {"released": len(items), "date": day}

    return mutate(user, f"Vertretungsvorschläge {day} freigegeben ({len(items)})", fn,
                  scope=["overrides", "substitutions"], dates=[day])


@router.delete("/overrides/{override_id}")
def delete_override(override_id: str, user: AuthUser = Depends(require("substitution.edit"))):
    snap = snapshot()
    old = next((o for o in snap[1].overrides if o.id == override_id), None)
    if old is None:
        raise HTTPException(404, f"Entscheidung {override_id} nicht gefunden")

    def fn(school: School):
        school.overrides = [o for o in school.overrides if o.id != override_id]
        return {"deleted": override_id}

    return mutate(user, f"Vertretungsentscheidung {override_id} entfernt", fn,
                  scope=["overrides", "substitutions"], dates=[old.date])


# =================================================================== Persönliche Ansicht
def _day_header(school: School, day: date, plan: dict) -> dict:
    """Kopf eines Tages: Datum, Wochentag, laufende Woche (``week_no``), ``holiday``,
    ``day_kind`` und ``week_info`` (Schule)."""
    from schulmanager.calendar_utils import day_kind, week_info
    from schulmanager.weeks import real_week
    return {"date": day.isoformat(), "weekday": day.weekday(), "week_no": plan.get("week_no", real_week(school, day)),
            "holiday": plan.get("holiday"),
            "day_kind": plan.get("day_kind") or day_kind(school, day),
            "week_info": plan.get("week_info") or week_info(school, day)}


def build_day_view(user, day: date, snap, student_id: Optional[str] = None) -> dict:
    """Persönlicher Tag: eigene Vertretungsplan-Einträge, effektive Stunden, Klausuren."""
    school = snap[1]
    _, plan = day_plan(day, snap)
    reasons = [] if has(user, "substitution.edit") else absence_reasons(school, day)
    out = _day_header(school, day, plan)
    out.update(plan_entries=[], cells=[], exams=[])
    day_iso = day.isoformat()
    tid = getattr(user, "teacher_id", None)
    sids = family_student_ids(user, "stundenplan", snap)   # Eltern Volljähriger: nur mit Freigabe
    if tid:
        entries = [e for e in plan.get("entries") or [] if tid in (e.get("teacher"), e.get("substitute"))]
        out["plan_entries"] = filter_plan(user, {**plan, "entries": entries}, snap)["entries"]
        out["cells"] = _clean_cells(effective_cells(day, "teacher", tid, snap), reasons)
        courses = teacher_course_ids(tid, snap)
        out["exams"] = _exam_rows(school, [e for e in school.exams if e.date == day_iso and e.course_id in courses])
        out["kind"], out["ref"] = "teacher", tid
    elif sids:
        sid = student_id or sids[0]
        if sid not in sids:
            raise HTTPException(403, "Keine Berechtigung für diese Schülerin/diesen Schüler")
        if sid not in index("students", snap):
            raise HTTPException(404, "Schüler/in nicht gefunden")
        ok = pupil_entry_filter(user, snap, [sid])
        entries = [e for e in plan.get("entries") or [] if e.get("kind") != "aufsicht" and ok(e)]
        out["plan_entries"] = filter_plan(user, {**plan, "entries": entries}, snap)["entries"]
        out["cells"] = _clean_cells(effective_cells(day, "student", sid, snap), reasons)
        out["exams"] = _exam_rows(school, [e for e in school.exams if e.date == day_iso],
                                  _student_exam_filter(snap, sid))
        out["kind"], out["ref"] = "student", sid
        students = index("students", snap)
        out["children"] = [{"id": s, "name": students[s].name, "class_id": students[s].class_id}
                           for s in sids if s in students]
    else:
        out["kind"], out["ref"] = None, None
        if has(user, "plans.read_all") and not is_scoped_teacher(user):
            out["stats"] = plan.get("stats") or {}
    out["plan_entries"].sort(key=lambda e: (e.get("period", 0), e.get("part", 0)))
    return out


@router.get("/me/today")
def me_today(date_: Optional[str] = Query(None, alias="date"), student_id: Optional[str] = None,
             user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Persönlicher Tag (Lehrkraft, Schüler/in; Eltern mit ``student_id`` je Kind) inkl. Mitteilungen."""
    from .features_announcements import visible_announcements
    day = parse_date(date_)
    snap = snapshot()
    out = build_day_view(user, day, snap, student_id)
    from .features_exams import attach_channels
    attach_channels(db, user, snap, out["exams"])
    out["announcements"] = visible_announcements(db, user, day, snap)
    out["version"] = snap[0]
    return out


@router.get("/me/week")
def me_week(date_: Optional[str] = Query(None, alias="date"), student_id: Optional[str] = None,
            user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Persönliche Woche Mo–So der Woche von ``date`` (``days`` immer 7 Einträge mit ``day_kind`` und
    ``has_items``)."""
    from schulmanager.calendar_utils import week_info

    from .features_announcements import visible_announcements
    day = parse_date(date_)
    snap = snapshot()
    monday = day - timedelta(days=day.weekday())
    days = []
    for i in range(7):
        v = build_day_view(user, monday + timedelta(days=i), snap, student_id)
        v["has_items"] = bool(v.get("cells") or v.get("plan_entries") or v.get("exams"))
        days.append(v)
    return {"week_start": monday.isoformat(),
            "week_info": week_info(snap[1], monday),
            "days": days, "announcements": visible_announcements(db, user, day, snap, until=monday + timedelta(days=6)),
            "version": snap[0]}


# =================================================================== Monitor
MONITOR_DEFAULTS: dict = {"days": 2, "title": "", "ticker": "", "notices": [], "scroll": "normal",
                          "font_scale": 1.0, "show_absent_classes": True}


class MonitorNoticeIn(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    until: Optional[date] = None
    important: bool = False


class MonitorConfigIn(BaseModel):
    days: int = Field(2, ge=1, le=5)
    title: str = Field("", max_length=100)
    ticker: str = Field("", max_length=500)
    notices: list[MonitorNoticeIn] = Field(default_factory=list, max_length=10)
    scroll: Literal["langsam", "normal", "schnell"] = "normal"
    font_scale: float = Field(1.0, ge=0.7, le=1.8)
    show_absent_classes: bool = True


def monitor_config(school: School, site: Optional[str], today: Optional[date] = None) -> dict:
    """Einstellungen des Monitors (Standort, sonst „alle“), abgelaufene Hinweise ausgeblendet."""
    cfg = {**MONITOR_DEFAULTS, **(school.monitors.get(site or "") or {})}
    if today is not None:
        cfg["notices"] = [n for n in cfg.get("notices") or [] if not n.get("until") or n["until"] >= today.isoformat()]
    return cfg


@router.get("/monitor/config")
def monitor_config_list(user: AuthUser = Depends(require("monitor.manage"))) -> dict:
    """Alle Monitor-Einstellungen (je Standort und „alle Standorte“) für die Verwaltung."""
    school = snapshot()[1]
    entries = [{"site": "", "site_name": "Alle Standorte", "config": monitor_config(school, "")}]
    entries += [{"site": s.id, "site_name": s.name, "config": monitor_config(school, s.id)} for s in school.sites]
    return {"monitors": entries, "defaults": MONITOR_DEFAULTS}


@router.put("/monitor/config/{site}")
def monitor_config_save(site: str, body: MonitorConfigIn, user: AuthUser = Depends(require("monitor.manage"))) -> dict:
    """Monitor-Einstellungen eines Standorts speichern (``alle`` = Anzeige für alle Standorte). Die Monitore
    aktualisieren sich sofort (Live-Ereignis ``announcements``)."""
    key = "" if site == "alle" else site
    if key and key not in index("sites", snapshot()):
        raise HTTPException(404, f"Standort {site} nicht gefunden")
    data = body.model_dump(mode="json")

    def fn(school: School):
        school.monitors[key] = data
        return monitor_config(school, key)

    return mutate(user, f"Monitor {site} eingestellt", fn, scope=["announcements"])


@router.get("/monitor")
def monitor(site: Optional[str] = None, date_: Optional[str] = Query(None, alias="date"),
            days: Optional[int] = Query(None, ge=1, le=5), user: AuthUser = Depends(require("monitor.read")),
            db: Session = Depends(get_db)):
    """Monitor-Ansicht (öffentlich im Schulhaus): heute + nächste Schultage, ohne Gründe/Aufsichten, sortiert nach
    Klasse; abwesende Lehrkräfte nur laut ``settings.public_absent_teachers`` (``absent_teacher_details``).
    Monitor-Konten zeigen immer ihren eigenen Standort; Tage, Laufband, Hinweise und Darstellung kommen aus den
    Monitor-Einstellungen."""
    from schulmanager.calendar_utils import is_school_day

    from .features_announcements import visible_announcements
    day = parse_date(date_)
    snap = snapshot()
    school = snap[1]
    if user.role == "monitor" and user.site:
        site = user.site
    if site and site not in index("sites", snap):
        raise HTTPException(404, f"Standort {site} nicht gefunden")
    cfg = monitor_config(school, site, day)
    days = days or int(cfg.get("days") or 2)
    selected = [day]
    d = day
    for _ in range(14):
        if len(selected) >= days:
            break
        d += timedelta(days=1)
        if is_school_day(school, d)[0]:
            selected.append(d)
    out_days = []
    for d in selected:
        _, plan = day_plan(d, snap)
        p = filter_plan(user, plan, snap, site=site, public=True)
        p["entries"].sort(key=_entry_sort_key)
        out_days.append({**_day_header(school, d, plan), "entries": p["entries"],
                         "absent_classes": p.get("absent_classes") or [], "stats": p.get("stats") or {},
                         "absent_teacher_details": p.get("absent_teacher_details") or [],
                         "absent_class_details": p.get("absent_class_details") or []})
    st = school.settings
    site_obj = index("sites", snap).get(site) if site else None
    anns = [a for a in visible_announcements(db, user, day, snap, monitor=True)
            if not a.get("site") or not site or a.get("site") == site]
    return {"site": site, "site_name": site_obj.name if site_obj else "", "school_name": st.school_name,
            "generated_at": now_iso(), "version": snap[0], "period_times": st.period_times[:st.periods],
            "days": out_days, "announcements": anns, "config": cfg}
