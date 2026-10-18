"""Schuljahr und Wochen (Entwurf KALENDER-ZEITRASTER §15.3, R3).

* ``GET /calendar/school-year?date=&class_id=`` – alle Wochen 1 … Y des Schuljahres von ``date`` (Standard: heute)
  mit KW, Zeitraum, Ferien; dazu Beginn/Ende, Zählung, Schulöffnungstage und Hinweise.
  Für alle Angemeldeten lesbar (keine Personendaten); ``class_id`` nur mit Sichtrecht auf die Klasse (sonst 404),
  dann gelten die Unterrichtstage der Klasse.
* ``GET /calendar/week?date=&class_id=`` – ``WeekInfo`` einer Woche (gleiche Rechte).
* ``GET /calendar/school-day?date=&dir=&class_id=`` – nächster/vorheriger Schultag (ohne Ferien, Feiertage, freie Tage).

Die Vorschau einer Kalenderänderung liegt bei den Einstellungen (``POST /settings/calendar-preview``).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import (absence_reasons, cached, day_plan, effective_cells, has, mutate, parse_date,
                              plan_class_ids, snapshot, student_parts)
from .features_substitutions import _clean_cells, _day_header
from .features_timetable import check_view_access

router = APIRouter(tags=["Kalender"])


def _date(value: Optional[str]) -> date:
    if not value:
        return date.today()
    try:
        day = date.fromisoformat(value[:10])
    except ValueError:
        day = None
    if day is None or not 1900 <= day.year <= 2199:    # außerhalb: 422 statt Überlauf (500)
        raise HTTPException(422, "Ungültiges Datum (JJJJ-MM-TT)")
    return day


def _class(user, class_id: Optional[str], snap):
    if not class_id:
        return None
    cls = snap[1].index("classes").get(class_id)
    allowed = plan_class_ids(user, snap)
    if cls is None or (allowed is not None and class_id not in allowed):
        raise HTTPException(404, f"Klasse „{class_id}“ nicht gefunden")
    return cls


@router.get("/calendar/school-year")
def school_year(date_: Optional[str] = Query(None, alias="date"), class_id: Optional[str] = Query(None, max_length=64),
                user: AuthUser = Depends(current_user)):
    """Wochenübersicht des Schuljahres (``SchoolYear``)."""
    from schulmanager.calendar_utils import school_year_info

    snap = snapshot()
    day = _date(date_)
    cls = _class(user, class_id, snap)
    return cached("school_year", (day.isoformat(), class_id or ""), lambda: school_year_info(snap[1], day, cls), snap)


@router.get("/calendar/week")
def week(date_: Optional[str] = Query(None, alias="date"), class_id: Optional[str] = Query(None, max_length=64),
         kind: Optional[Literal["class", "teacher", "room", "student"]] = Query(None),
         ref: Optional[str] = Query(None, max_length=64), user: AuthUser = Depends(current_user),
         db: Session = Depends(get_db)):
    """Mit ``kind``+``ref``: Kalenderwoche mit Stunden, Terminen, Klausuren und Hausaufgaben; sonst ``WeekInfo``
    (KW, Zeitraum, Ferien) der Woche von ``date``."""
    if kind is not None and ref:
        return calendar_week(kind, ref, date_, user, db)
    from schulmanager.calendar_utils import week_info

    snap = snapshot()
    day = _date(date_)
    cls = _class(user, class_id, snap)
    return week_info(snap[1], day, cls)


@router.get("/calendar/school-day")
def neighbour_school_day(date_: Optional[str] = Query(None, alias="date"), direction: int = Query(1, alias="dir", ge=-1, le=1),
                         class_id: Optional[str] = Query(None, max_length=64), user: AuthUser = Depends(current_user)):
    """Nächster (``dir=1``) bzw. vorheriger (``dir=-1``) Schultag vor/nach ``date``: überspringt Wochenenden,
    Ferien, Feiertage und unterrichtsfreie Tage (gleiche Grundlage wie „Kein Unterricht – …“). Gibt es binnen
    eines Jahres keinen, bleibt ``date`` (``found: false``)."""
    from schulmanager.calendar_utils import is_school_day

    snap = snapshot()
    day = _date(date_)
    cls = _class(user, class_id, snap)
    step = -1 if direction < 0 else 1
    cur = day
    for _ in range(400):
        try:
            cur = cur + timedelta(days=step)
        except OverflowError:
            break
        if is_school_day(snap[1], cur, cls)[0]:
            return {"date": cur.isoformat(), "found": True}
    return {"date": day.isoformat(), "found": False}


WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _scope(school, kind: str, ref: str) -> tuple[set[str], set[int], Optional[dict[str, list[int]]], set[str]]:
    """(Klassen, Jahrgänge, Kursteile des Schülers bzw. None, Kurse) der Ansicht – für Termine/Klausuren."""
    classes = school.index("classes")
    courses = school.index("courses")
    if kind == "class":
        cl = classes.get(ref)
        return {ref}, {cl.grade} if cl else set(), None, {c.id for c in school.courses if ref in c.classes}
    if kind == "student":
        st = school.index("students").get(ref)
        cid = st.class_id if st else None
        cl = classes.get(cid) if cid else None
        parts = student_parts(ref)
        return ({cid} if cid else set()), ({cl.grade} if cl else set()), parts, set(parts)
    if kind == "teacher":
        own = {c.id for c in school.courses if any(p.teacher == ref for p in c.parts)}
        cls = {x for c in own if c in courses for x in courses[c].classes}
        cls |= {c.id for c in school.classes if c.class_teacher == ref}
        return cls, {classes[c].grade for c in cls if c in classes}, None, own
    return set(), set(), None, set()


def _exams(school, d: date, kind: str, ref: str, course_ids: set[str], parts: Optional[dict[str, list[int]]]
           ) -> list[dict[str, Any]]:
    from .features_exams import exam_info
    out = []
    for e in school.exams:
        if str(e.date)[:10] != d.isoformat():
            continue
        if kind == "room":
            ok = e.room == ref
        elif parts is not None:
            ok = e.course_id in parts and (e.part is None or e.part in parts[e.course_id])
        else:
            ok = e.course_id in course_ids
        if ok:
            info = exam_info(school, e)
            out.append({"id": e.id, "kind": getattr(e, "kind", "klausur"),
                        "kind_label": "Test" if getattr(e, "kind", "klausur") == "test" else "Klausur/Arbeit",
                        "title": e.title or info.get("label", ""), "label": info.get("label", ""),
                        "subject": info.get("subject", ""), "start": e.start, "length": e.length,
                        "time": info.get("time", ""), "room": e.room or info.get("room_lesson"),
                        "course_id": e.course_id, "part": e.part, "classes": info.get("classes", []),
                        "teachers": info.get("teachers", [])})
    return sorted(out, key=lambda x: (x["start"], x["label"]))


def _events(school, d: date, kind: str, classes: set[str], grades: set[int]) -> list[dict[str, Any]]:
    out = []
    for ev in getattr(school, "events", []):
        try:
            if not ev.covers(d):
                continue
        except ValueError:
            continue
        if kind != "room" and not (not ev.classes and not ev.grades) and not (
                set(ev.classes) & classes or set(ev.grades) & grades):
            continue
        out.append({"id": ev.id, "title": ev.title, "kind": ev.kind,
                    "kind_label": "Anwesenheit Pflicht" if ev.kind == "pflicht" else "Termin",
                    "time_from": ev.time_from, "time_to": ev.time_to, "location": ev.location, "note": ev.note,
                    "all_school": not ev.classes and not ev.grades})
    return sorted(out, key=lambda x: (x["time_from"] or "", x["title"]))


HW_LOOKBACK = 14        # so viele Tage vor der Fälligkeit wird nach der Stunde des Fachs gesucht


def _hw_matches(cell: dict, hw: dict) -> bool:
    if hw.get("course_id"):
        return cell.get("course_id") == hw["course_id"] and (hw.get("part") is None or cell.get("part") == hw["part"])
    return True                                       # Klassenraum: ohne Fach – jede Stunde der Klasse


def _place_homework(snap, kind: str, ref: str, due: dict[str, list[dict]], monday: date, sunday: date
                    ) -> dict[str, list[dict]]:
    """Ordnet Hausaufgaben einer Stunde zu (Regel): Am Fälligkeitstag die **erste Stunde des Kurses/Kursteils**
    (Zuordnung über ``course_id``/``part`` des Kursraums, nicht über das Fachkürzel); gibt es an dem Tag keine, die
    **letzte Stunde davor** (bis ``HW_LOOKBACK`` Tage zurück, ausgefallene Stunden und Ferien zählen nicht) – dort wird
    die Aufgabe gestellt/bearbeitet. Klassenräume ohne Fach: erste Stunde des Tages (bevorzugt die der
    Klassenleitung). Ohne Treffer bleibt die Aufgabe am Fälligkeitstag ohne ``slot`` (Hinweis im Tageskopf).
    Ergebnis: je Tag der **Anzeigewoche** die dort liegenden Aufgaben mit ``slot`` (Stunde), ``due_date``."""
    memo: dict[date, list[dict]] = {}

    def cells_on(d: date) -> list[dict]:
        if d not in memo:
            _, plan = day_plan(d, snap)
            memo[d] = [] if plan.get("holiday") else [
                c for c in effective_cells(d, kind, ref, snap)
                if c.get("kind") != "aufsicht" and c.get("status") != "entfall" and not c.get("dropped")]
        return memo[d]

    out: dict[str, list[dict]] = {}
    for due_iso, items in due.items():
        due_day = date.fromisoformat(due_iso)
        for hw in items:
            placed, slot = due_day, None
            for back in range(HW_LOOKBACK + 1):
                d = due_day - timedelta(days=back)
                hits = [c for c in cells_on(d) if _hw_matches(c, hw)]
                if not hits:
                    continue
                if not hw.get("course_id") and hw.get("class_teacher"):
                    hits.sort(key=lambda c: (c.get("teacher") != hw["class_teacher"], c["period"]))
                else:
                    hits.sort(key=lambda c: c["period"])
                placed, slot = d, hits[0]["period"]
                break
            if monday <= placed <= sunday:
                out.setdefault(placed.isoformat(), []).append({**hw, "due_date": due_iso, "slot": slot})
    for lst in out.values():
        lst.sort(key=lambda e: (e["slot"] if e["slot"] is not None else 99, e["due_date"], e["time"], e["title"]))
    return out


def calendar_week(kind: str, ref: str, date_: Optional[str], user: AuthUser, db: Session) -> dict:
    snap = snapshot()
    check_view_access(user, kind, ref, snap)
    school = snap[1]
    st = school.settings
    day = parse_date(date_)
    monday = day - timedelta(days=day.weekday())
    sunday = monday + timedelta(days=6)
    editor = has(user, "substitution.edit")
    classes, grades, parts, course_ids = _scope(school, kind, ref)
    from .features_channels import homework_due
    homework = _place_homework(snap, kind, ref, homework_due(db, user, snap, kind, ref, monday,
                                                             sunday + timedelta(days=HW_LOOKBACK)), monday, sunday)
    attendance = _attendance(db, user, snap, kind, ref, monday, sunday)
    from .features_makeups import calendar_items
    makeups = calendar_items(db, user, snap, kind, ref, monday, sunday)
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        _, plan = day_plan(d, snap)
        header = _day_header(school, d, plan)
        cells: list[dict] = []
        if not plan.get("holiday"):
            reasons = [] if editor else absence_reasons(school, d)
            cells = _clean_cells(effective_cells(d, kind, ref, snap), reasons)
        weekend = d.weekday() >= max(1, min(7, st.days))
        if weekend and header.get("holiday") == "Wochenende":
            header["holiday"] = None
        if not header.get("holiday") and not weekend:
            note = _class_away(school, kind, ref, d)
            if note:
                header["holiday"] = note
        events = _events(school, d, kind, classes, grades)
        exams = _exams(school, d, kind, ref, course_ids, parts) + makeups.get(d.isoformat(), [])
        hw = homework.get(d.isoformat(), [])
        days.append({**header, "weekday_name": WEEKDAYS[d.weekday()], "weekend": weekend, "cells": cells,
                     "events": events, "exams": exams, "homework": hw,
                     "attendance": attendance.get(d.isoformat(), []),
                     "duty": any(e["kind"] == "pflicht" for e in events)})
    from .features_exams import attach_channels
    attach_channels(db, user, snap, [x for d in days for x in d["exams"] if x["kind"] != "nachschreiben"])
    attach_channels(db, user, snap, [x for d in days for x in d["exams"] if x["kind"] == "nachschreiben"], "exam_id")
    show = [d["date"] for d in days]                      # Samstag/Sonntag immer anzeigen
    iso = monday.isocalendar()
    out = {"kind": kind, "ref": ref, "week_start": monday.isoformat(), "week_end": sunday.isoformat(),
           "iso_week": iso[1], "iso_year": iso[0], "periods": st.periods,
           "period_times": st.period_times[:st.periods], "breaks": st.breaks, "days": days, "show_days": show,
           "names": _names(school, days), "version": snap[0]}
    from schulmanager.plan_periods import active, state_for_date
    if active(school):                 # Planzeiträume: Zustand des Plans dieser Woche (ok | missing | none)
        out["plan"] = state_for_date(school, monday)
    return out


def _class_away(school, kind: str, ref: str, d: date) -> Optional[str]:
    """Klasse ist laut Rhythmus den ganzen Tag nicht im Haus (z. B. Praxistag im Betrieb) → Hinweis im Tageskopf."""
    if kind == "student":
        st = school.index("students").get(ref)
        ref = st.class_id if st else ""
    elif kind != "class":
        return None
    cls = school.index("classes").get(ref)
    if cls is None:
        return None
    from schulmanager.weeks import real_week
    week = real_week(school, d)
    for rule in cls.unavailable or []:
        if not rule.periods and rule.matches(week, d.weekday(), 0):
            return rule.note or "Klasse nicht im Haus"
    return None


def _names(school, days: list[dict]) -> dict[str, dict[str, str]]:
    """Volle Namen zu Kürzeln (Lehrkräfte, Räume, Klassen), die in der Woche vorkommen."""
    teachers, rooms, classes = school.index("teachers"), school.index("rooms"), school.index("classes")
    out: dict[str, dict[str, str]] = {"teachers": {}, "rooms": {}, "classes": {}}
    for d in days:
        for c in d["cells"]:
            for tid in (c.get("teacher"), c.get("original_teacher")):
                if tid and tid in teachers:
                    out["teachers"][tid] = teachers[tid].name or tid
            for rid in (c.get("room"), c.get("original_room")):
                if rid and rid in rooms:
                    out["rooms"][rid] = rooms[rid].name or rid
            for cid in c.get("classes") or []:
                if cid in classes:
                    out["classes"][cid] = classes[cid].name or cid
    return out


def _attendance(db: Session, user, snap, kind: str, ref: str, d1: date, d2: date) -> dict[str, list[dict]]:
    """Schüleransicht: Krankmeldungen/Verspätungen/Fehlzeiten des Kindes je Tag – nur für Berechtigte (das Kind,
    die Familie, Personal mit Sicht auf die Schülerin/den Schüler)."""
    if kind != "student":
        return {}
    from sqlalchemy import select

    from schulmanager.server.db_models import StudentAbsence

    from .features_grades import _may_see
    from .features_student_absences import KIND_LABELS, status_label
    if not _may_see(db, user, ref, snap):
        return {}
    out: dict[str, list[dict]] = {}
    rows = db.scalars(select(StudentAbsence).where(StudentAbsence.student_id == ref,
                                                   StudentAbsence.date_from <= d2.isoformat(),
                                                   StudentAbsence.date_to >= d1.isoformat()))
    for r in rows:
        cur = max(date.fromisoformat(r.date_from), d1)
        end = min(date.fromisoformat(r.date_to), d2)
        while cur <= end:
            out.setdefault(cur.isoformat(), []).append({
                "id": r.id, "kind": r.kind, "kind_label": KIND_LABELS.get(r.kind, r.kind), "status": r.status,
                "status_label": status_label(r.kind or "krank", r.status), "minutes": r.minutes,
                "periods": list(r.periods or []), "excused": r.status == "entschuldigt"})
            cur += timedelta(days=1)
    return out


# ---------------------------------------------------------------------------- Planzeiträume
class PeriodIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[str] = Field(None, max_length=20)
    name: str = Field(max_length=60)
    date_from: str = Field(max_length=10)
    date_to: str = Field(max_length=10)


class PeriodsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    periods: list[PeriodIn] = Field(max_length=12)
    adopt: str = Field("all", max_length=20, description="Erstes Einrichten: bisheriger Plan für „all“, einen Zeitraum "
                       "(Kennung) oder „none“ (bleibt ohne Zeitraum)")
    confirm_delete: bool = Field(False, description="Zeiträume mit Plan dürfen entfallen")


def _periods_view(school) -> dict:
    from schulmanager import plan_periods as pp
    return {"active": pp.active(school), "periods": [pp.public(school, p) for p in pp.periods(school)],
            "suggested": [] if pp.active(school) else pp.default_periods(school),
            "target": pp.default_target(school)}


@router.get("/calendar/plan-periods")
def get_plan_periods(user: AuthUser = Depends(current_user)):
    """Planzeiträume (z. B. Halbjahre) mit Angabe, ob sie einen Plan haben; ``suggested`` = Vorschlag zum Einrichten,
    ``target`` = Voreinstellung für den Generator (laufender bzw. nächster Zeitraum ohne Plan)."""
    snap = snapshot()
    return cached("plan_periods", (), lambda: _periods_view(snap[1]), snap)


@router.put("/calendar/plan-periods")
def put_plan_periods(body: PeriodsIn, user: AuthUser = Depends(require("settings.edit"))):
    """Zeiträume anlegen, umbenennen, Grenzen ändern oder löschen. Beim ersten Einrichten wird der bisherige Plan
    übernommen (``adopt``). Zeiträume mit Plan entfallen nur mit ``confirm_delete``."""
    from schulmanager import plan_periods as pp

    raw = [p.model_dump() for p in body.periods]

    def fn(school):
        errs = pp.normalize(school, raw)[1]
        if errs:
            raise HTTPException(422, " ".join(errs))
        if pp.active(school) and not body.confirm_delete:
            keep = {str(r.get("id") or "") for r in raw}
            lost = [p for p in pp.periods(school) if p["id"] not in keep and pp.lessons_of(school, p["id"])]
            if lost:
                raise HTTPException(409, "Zeitraum mit Stundenplan: " + ", ".join(p["name"] for p in lost)
                                    + ". Löschen bitte bestätigen.")
        errs = pp.setup(school, raw, body.adopt)
        if errs:
            raise HTTPException(422, " ".join(errs))
        return _periods_view(school)

    return mutate(user, "Planzeiträume geändert", fn, scope=["settings", "timetable", "substitutions"])


@router.post("/calendar/plan-periods/{period_id}/copy/{source_id}")
def copy_plan_period(period_id: str, source_id: str, replace: bool = Query(False),
                     user: AuthUser = Depends(require("timetable.generate"))):
    """Stundenplan eines Zeitraums als Plan eines anderen übernehmen (ohne ``replace`` nur in einen leeren)."""
    from schulmanager import plan_periods as pp

    def fn(school):
        try:
            info = pp.copy_period(school, source_id, period_id, replace)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        return {**info, **_periods_view(school)}

    return mutate(user, "Plan aus Zeitraum übernommen", fn, scope=["timetable", "substitutions"])


@router.delete("/calendar/plan-periods/{period_id}/plan")
def clear_plan_period(period_id: str, user: AuthUser = Depends(require("timetable.generate"))):
    """Stundenplan eines Zeitraums leeren (der Zeitraum bleibt)."""
    from schulmanager import plan_periods as pp

    def fn(school):
        if pp.get(school, period_id) is None:
            raise HTTPException(404, "Zeitraum nicht gefunden")
        return {"removed": pp.clear_period(school, period_id), **_periods_view(school)}

    return mutate(user, "Plan eines Zeitraums geleert", fn, scope=["timetable", "substitutions"])
