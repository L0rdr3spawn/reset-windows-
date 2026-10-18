"""Klassenbuch: Anwesenheit je Unterrichtsstunde, Thema und Hausaufgabe.

* ``GET /register/day?class_id=&date=`` – alle Stunden der Klasse an dem Tag (tatsächlicher Plan inkl. Vertretung/
  Entfall) mit Schülerliste; Krankmeldungen (auch „Jetzt krank melden“ der Schüler/innen) sind vorausgefüllt.
* ``PUT /register/lesson`` – Anwesenheit, Thema, Hausaufgabe speichern. Nur eingetragene Schüler/innen werden
  geschickt (sonst „nicht eingetragen“); ``present`` / ``absent``, ``late`` = anwesend mit Verspätung (Minuten),
  ``left`` nur noch für alte Einträge; ``note`` = Notiz der Lehrkraft (z. B. „krank nach Hause“). Fehlen und
  Verspätung werden als offene Fehlzeiten (``student_absences``, ``source=lehrkraft``, ``register_id``, Notiz in
  ``note``) geführt – entschuldigt erst über Entschuldigung (Eltern bzw. Volljährige) + Bestätigung.

Rechte: Lesen wie Krankmeldungen (``student_absence.read`` im Scope, z. B. Lehrkräfte ihrer Klassen); Schreiben
Lehrkraft bzw. Vertretung der Stunde, Klassenleitung oder Personal mit ``student_absence.report`` ohne Einschränkung.
Fachlehrkräfte sehen im Klassenbuch nur ihre eigenen Stunden; die Klassenleitung (und Verwaltung ohne Einschränkung)
sieht das ganze Klassenbuch und die Übersicht ``GET /register/overview`` (Schüler/innen × Stunden).
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import absence_log as alog
from schulmanager.server import crypto
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.register import RegisterLesson

from .features_common import effective_cells, has, parse_date, perm_scope, publish_change, snapshot, \
    students_in_scope, write_audit

router = APIRouter(tags=["Klassenbuch"])
STATUSES = ("present", "absent", "late", "left")


class AttendanceIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=40)
    status: Literal["present", "absent", "late", "left"]
    minutes: Optional[int] = Field(None, ge=1, le=600)
    note: str = Field("", max_length=500)
    # Nur bei Doppelstunden (``LessonIn.block``): ``absent`` gilt für alle Stunden des Blocks; ``missing`` nennt
    # stattdessen nur einzelne Stunden („nur die 2. Stunde gefehlt“). ``left_from`` = erste Stunde des Blocks, die
    # nach dem früheren Gehen (``left``) versäumt wird (Standard: die letzte).
    missing: list[int] = Field(default_factory=list, max_length=20)
    left_from: Optional[int] = Field(None, ge=0, le=20)


class LessonIn(BaseModel):
    date: date
    lesson_id: str = Field(min_length=1, max_length=40)
    period: int = Field(ge=0, le=20)
    part: int = Field(0, ge=0, le=20)
    topic: str = Field("", max_length=2000)
    homework: str = Field("", max_length=2000)
    # Doppelstunde/Block: alle aufeinanderfolgenden Stunden desselben Unterrichts (einschließlich ``period``); die
    # Eingaben gelten für jede Stunde des Blocks. Leer = nur ``period``.
    block: list[int] = Field(default_factory=list, max_length=12)
    attendance: list[AttendanceIn] = Field(default_factory=list, max_length=200)


def _dec(token: str, aad: str) -> str:
    if not token:
        return ""
    try:
        return crypto.decrypt_text(token, aad)
    except Exception:  # noqa: BLE001
        return ""


def _class_cells(day: date, class_id: str, snap) -> list[dict]:
    return [c for c in effective_cells(day, "class", class_id, snap) if c.get("lesson_id") and c.get("kind") != "aufsicht"]


def _students_of(school, class_id: str, cell: dict) -> list[str]:
    """Schüler/innen der Klasse, die diese Stunde (Kursteil) besuchen."""
    from schulmanager import channels as logic
    course = school.index("courses").get(cell.get("course_id") or "")
    in_class = [s.id for s in school.students if s.class_id == class_id]
    if course is None or len(course.parts) <= 1:
        return in_class
    members = set(logic.channel_student_ids(school, logic.COURSE, logic.course_ref(course.id, int(cell.get("part") or 0))))
    return [s for s in in_class if s in members]


def _reported(db: Session, student_ids: list[str], day: date) -> dict[str, list[Any]]:
    from schulmanager.server.db_models import StudentAbsence
    if not student_ids:
        return {}
    d = day.isoformat()
    out: dict[str, list[Any]] = {}
    for a in db.scalars(select(StudentAbsence).where(StudentAbsence.student_id.in_(student_ids),
                                                     StudentAbsence.date_from <= d, StudentAbsence.date_to >= d)):
        out.setdefault(a.student_id, []).append(a)
    return out


def _covers(a, period: int) -> bool:
    return not a.periods or period in a.periods


def _may_read(user, class_id: str, snap) -> bool:
    if not has(user, "student_absence.read") or getattr(user, "role", "") in ("schueler", "eltern"):
        return False
    scope = students_in_scope(user, "student_absence.read", snap)
    if scope is None:
        return True
    # Klassenbuch: Lehrkräfte, die in der Klasse unterrichten oder sie leiten (Krankmeldungen selbst sehen
    # Fachlehrkräfte nur als „abwesend gemeldet“, siehe register_day)
    from schulmanager.server.permissions import teacher_class_ids
    if class_id in teacher_class_ids(snap[1], getattr(user, "teacher_id", None)):
        return True
    return any(s.class_id == class_id and s.id in scope for s in snap[1].students)


def _full_access(user, class_id: str, snap) -> bool:
    """Ganzes Klassenbuch: Verwaltung ohne Einschränkung oder Klassenleitung der Klasse."""
    if not has(user, "student_absence.read") or getattr(user, "role", "") in ("schueler", "eltern"):
        return False
    if perm_scope(user, "student_absence.read") is None:
        return True
    cls = snap[1].index("classes").get(class_id)
    return bool(cls and getattr(user, "teacher_id", None) and cls.class_teacher == user.teacher_id)


def _own_cell(user, cell: dict) -> bool:
    tid = getattr(user, "teacher_id", None)
    return bool(tid) and tid in (cell.get("teacher"), cell.get("original_teacher"))


def _may_write(user, class_id: str, cell: dict, snap) -> bool:
    if getattr(user, "role", "") in ("schueler", "eltern") or not has(user, "student_absence.report"):
        return False
    if perm_scope(user, "student_absence.report") is None:
        return True
    tid = getattr(user, "teacher_id", None)
    if not tid:
        return False
    if tid in (cell.get("teacher"), cell.get("original_teacher")):
        return True
    cls = snap[1].index("classes").get(class_id)
    return bool(cls and cls.class_teacher == tid)


def _entry_out(e: Optional[RegisterLesson]) -> Optional[dict]:
    if e is None:
        return None
    try:
        att = json.loads(_dec(e.attendance_enc, e.aad("attendance")) or "{}")
    except ValueError:
        att = {}
    return {"id": e.id, "topic": _dec(e.topic_enc, e.aad("topic")), "homework": _dec(e.homework_enc, e.aad("homework")),
            "attendance": att, "checked_by_name": e.checked_by_name, "checked_at": iso(e.checked_at)}


@router.get("/register/day")
def register_day(class_id: str = Query(..., max_length=40), date_: Optional[str] = Query(None, alias="date"),
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    from schulmanager.server.routes.features_student_absences import KIND_LABELS, status_label
    snap = snapshot()
    school = snap[1]
    cls = school.index("classes").get(class_id)
    if cls is None:
        raise HTTPException(404, "Klasse nicht gefunden")
    if not _may_read(user, class_id, snap):
        raise HTTPException(403, "Kein Zugriff auf das Klassenbuch dieser Klasse")
    day = parse_date(date_)
    full = _full_access(user, class_id, snap)
    cells = [c for c in _class_cells(day, class_id, snap) if full or _own_cell(user, c)]
    students = school.index("students")
    subjects = school.index("subjects")
    teachers = school.index("teachers")
    all_ids = [s.id for s in school.students if s.class_id == class_id]
    reported = _reported(db, all_ids, day)
    logs = alog.events_by_absence(db, [a.id for lst in reported.values() for a in lst])
    level = alog.FULL if full else alog.PRESENCE
    from .features_support import support_flags
    support = support_flags(db, all_ids, user, snap)
    entries = {(e.lesson_id, e.period, e.part): e for e in db.scalars(
        select(RegisterLesson).where(RegisterLesson.date == day.isoformat()))}
    st = school.settings
    lessons = []
    for c in sorted(cells, key=lambda x: (x["period"], x.get("part") or 0)):
        period, part = int(c["period"]), int(c.get("part") or 0)
        entry = entries.get((c["lesson_id"], period, part))
        eo = _entry_out(entry)
        att = (eo or {}).get("attendance", {})
        rows = []
        for sid in sorted(_students_of(school, class_id, c), key=lambda s: students[s].name if s in students else s):
            rep = [a for a in reported.get(sid, []) if _covers(a, period) and a.register_id != (entry.id if entry else -1)]
            info = None
            if rep:
                a = rep[0]
                evs = logs.get(a.id, [])
                first = next((e for e in evs if e.event == "angelegt"), None)
                when = {"absence_id": a.id, **alog.report_info(a, first, level)}
                if full:
                    info = {"kind": a.kind or "krank", "kind_label": KIND_LABELS.get(a.kind or "krank", a.kind),
                            "status": a.status, "status_label": status_label(a.kind or "krank", a.status),
                            "from_register": a.register_id is not None, **when,
                            "history": alog.timeline(evs, alog.FULL, a.kind or "krank")}
                else:  # Fachlehrkraft: nur „abwesend gemeldet“ – Art/Grund sind Gesundheitsdaten (B-06)
                    info = {"kind": "abwesend", "kind_label": "Abwesenheit", "status": "", "status_label": "",
                            "from_register": a.register_id is not None, **when}
            rows.append({"id": sid, "name": students[sid].name if sid in students else sid, "reported": info,
                         "attendance": att.get(sid), "support": support.get(sid, [])})
        cancelled = c.get("status") == "entfall" or c.get("kind") in ("entfall", "klasse_abwesend")
        tid = c.get("teacher")
        lessons.append({"period": period, "time": st.period_times[period] if period < len(st.period_times) else "",
                        "lesson_id": c["lesson_id"], "part": part, "course_id": c.get("course_id"),
                        "subject": c.get("subject"),
                        "subject_name": subjects[c["subject"]].name if c.get("subject") in subjects else c.get("subject"),
                        "teacher": tid, "teacher_name": teachers[tid].name if tid in teachers else tid,
                        "kind": c.get("kind"), "note": c.get("note") or "", "cancelled": cancelled,
                        "entry": eo, "students": rows, "can_edit": not cancelled and _may_write(user, class_id, c, snap)})
    _mark_blocks(lessons)
    return {"class": {"id": cls.id, "name": cls.name}, "date": day.isoformat(), "lessons": lessons, "full": full}


@router.get("/register/classes")
def register_classes(user: AuthUser = Depends(current_user)) -> dict:
    """Klassen fürs Klassenbuch: Verwaltung alle; Lehrkräfte geleitete (``full``) und unterrichtete Klassen."""
    from schulmanager.server.permissions import teacher_class_ids
    snap = snapshot()
    school = snap[1]
    if not has(user, "student_absence.read") or getattr(user, "role", "") in ("schueler", "eltern"):
        raise HTTPException(403, "Kein Zugriff auf das Klassenbuch")
    if perm_scope(user, "student_absence.read") is None:
        ids = [c.id for c in school.classes]
    else:
        ids = sorted(teacher_class_ids(school, getattr(user, "teacher_id", None)))
    by_id = school.index("classes")
    out = [{"id": cid, "name": by_id[cid].name, "full": _full_access(user, cid, snap)} for cid in ids if cid in by_id]
    from schulmanager.messaging import natural_key
    out.sort(key=lambda c: natural_key(c["name"]))
    return {"classes": out}


@router.get("/register/overview")
def register_overview(class_id: str = Query(..., max_length=40), from_: Optional[str] = Query(None, alias="from"),
                      to: Optional[str] = Query(None), user: AuthUser = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    """Übersicht der Klassenleitung: je Schüler/in und Unterrichtsstunde (Zeitraum, höchstens 31 Tage; Standard:
    aktuelle Woche) ``present``/``absent``/``late``/``left`` aus dem Klassenbuch, ``reported`` (gemeldet, z. B.
    krank) oder ``null`` (nicht eingetragen); dazu Summen je Schüler/in."""
    from datetime import timedelta

    from schulmanager.calendar_utils import is_school_day
    snap = snapshot()
    school = snap[1]
    cls = school.index("classes").get(class_id)
    if cls is None:
        raise HTTPException(404, "Klasse nicht gefunden")
    if not _full_access(user, class_id, snap):
        raise HTTPException(403, "Die Übersicht des Klassenbuchs sieht die Klassenleitung")
    start = parse_date(from_) if from_ else parse_date(None) - timedelta(days=parse_date(None).weekday())
    end = parse_date(to) if to else start + timedelta(days=6)
    if end < start or (end - start).days > 30:
        raise HTTPException(422, "Zeitraum: höchstens 31 Tage")
    sids = [s.id for s in sorted((s for s in school.students if s.class_id == class_id), key=lambda s: s.name)]
    names = {s.id: s.name for s in school.students if s.class_id == class_id}
    slots, cells_out = [], {sid: {} for sid in sids}
    totals = {sid: {"absent": 0, "late": 0, "reported": 0, "open": 0} for sid in sids}
    d = start
    while d <= end:
        if is_school_day(school, d)[0]:
            cells = [c for c in _class_cells(d, class_id, snap)
                     if not (c.get("status") == "entfall" or c.get("kind") in ("entfall", "klasse_abwesend"))]
            entries = {(e.lesson_id, e.period, e.part): e for e in db.scalars(
                select(RegisterLesson).where(RegisterLesson.date == d.isoformat()))}
            reported = _reported(db, sids, d)
            for c in sorted(cells, key=lambda x: (x["period"], x.get("part") or 0)):
                period, part = int(c["period"]), int(c.get("part") or 0)
                key = f"{d.isoformat()}|{period}|{part}|{c['lesson_id']}"
                entry = entries.get((c["lesson_id"], period, part))
                att = (_entry_out(entry) or {}).get("attendance", {}) if entry else {}
                attendees = set(_students_of(school, class_id, c))
                slots.append({"key": key, "date": d.isoformat(), "period": period, "part": part,
                              "subject": c.get("subject"), "entered": entry is not None})
                for sid in sids:
                    if sid not in attendees:
                        continue
                    a = att.get(sid)
                    status = a.get("status") if a else None
                    if status is None and any(_covers(x, period) for x in reported.get(sid, [])):
                        status = "reported"
                    cells_out[sid][key] = status
                    if status in ("absent", "left"):
                        totals[sid]["absent"] += 1
                    elif status == "late":
                        totals[sid]["late"] += 1
                    elif status == "reported":
                        totals[sid]["reported"] += 1
                    elif status is None:
                        totals[sid]["open"] += 1
        d += timedelta(days=1)
    from schulmanager.server.db_models import StudentAbsence
    from .features_student_absences import KIND_LABELS, status_label
    rows = list(db.scalars(select(StudentAbsence).where(StudentAbsence.student_id.in_(sids),
                                                        StudentAbsence.date_from <= end.isoformat(),
                                                        StudentAbsence.date_to >= start.isoformat())
                           .order_by(StudentAbsence.date_from, StudentAbsence.id)))
    logs = alog.events_by_absence(db, [r.id for r in rows])
    reports: dict[str, list[dict]] = {}
    for r in rows:
        evs = logs.get(r.id, [])
        first = next((e for e in evs if e.event == "angelegt"), None)
        kind = r.kind or "krank"
        reports.setdefault(r.student_id, []).append({
            "absence_id": r.id, "kind": kind, "kind_label": KIND_LABELS.get(kind, kind), "date_from": r.date_from,
            "date_to": r.date_to, "periods": list(r.periods or []), "status": r.status,
            "status_label": status_label(kind, r.status), **alog.report_info(r, first, alog.FULL),
            "history": alog.timeline(evs, alog.FULL, kind)})
    return {"class": {"id": cls.id, "name": cls.name}, "from": start.isoformat(), "to": end.isoformat(),
            "students": [{"id": sid, "name": names[sid]} for sid in sids], "slots": slots, "cells": cells_out,
            "totals": totals, "reports": reports}


@router.get("/register/now")
def register_now(user: AuthUser = Depends(current_user)) -> dict:
    """Startseite der Lehrkraft: die Stunde, die gerade läuft (oder in den nächsten 15 Minuten beginnt) – je Klasse
    mit Stunde/Teil, damit dort direkt die Anwesenheit erfasst werden kann (Krankmeldungen sind vorausgefüllt)."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    tid = getattr(user, "teacher_id", None)
    if not tid:
        return {"date": None, "lessons": []}
    snap = snapshot()
    st = snap[1].settings
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    today = now.date()
    minutes = max(1, int(getattr(st, "period_minutes", 45) or 45))
    cells = [c for c in effective_cells(today, "teacher", tid, snap)
             if c.get("lesson_id") and c.get("kind") != "aufsicht" and c.get("status") != "entfall"]
    current = None
    for c in sorted(cells, key=lambda x: x["period"]):
        t = (st.period_times[c["period"]] if c["period"] < len(st.period_times) else "") or ""
        try:
            hh, mm = (int(x) for x in t.split(":"))
        except ValueError:
            continue
        start = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if start - timedelta(minutes=15) <= now < start + timedelta(minutes=minutes):
            current = c["period"]
            break
    if current is None:
        return {"date": today.isoformat(), "lessons": []}
    out, seen = [], set()
    for c in cells:
        if c["period"] != current:
            continue
        for cid in c.get("classes") or []:
            key = (cid, c["lesson_id"], c.get("part") or 0)
            if key in seen:
                continue
            seen.add(key)
            out.append({"class_id": cid, "lesson_id": c["lesson_id"], "period": current, "part": c.get("part") or 0,
                        "subject": c.get("subject"), "time": c.get("time")})
    return {"date": today.isoformat(), "period": current, "lessons": out}


def _mark_blocks(lessons: list[dict]) -> None:
    """Doppelstunden: ``block`` = Stunden (aufeinanderfolgend, gleicher Unterricht/Teil, gleiche Lehrkraft und Art), die
    gemeinsam erfasst werden; eine einzelne Stunde hat ``[period]``."""
    def key(le: dict) -> tuple:
        return (le["lesson_id"], le["part"], le["teacher"], le["kind"], le["cancelled"], le["can_edit"])

    groups: list[list[dict]] = []
    for le in sorted(lessons, key=lambda x: (x["lesson_id"], x["part"], x["period"])):
        last = groups[-1][-1] if groups else None
        if last is not None and key(last) == key(le) and le["period"] == last["period"] + 1:
            groups[-1].append(le)
        else:
            groups.append([le])
    for g in groups:
        periods = [le["period"] for le in g]
        for le in g:
            le["block"] = periods


def _block_periods(body: "LessonIn", cells: list[dict], cell: dict) -> list[int]:
    """Geprüfter Block der Anfrage (aufsteigend, alle Stunden gibt es für denselben Unterricht an dem Tag)."""
    block = sorted(set(body.block) | {body.period})
    if len(block) > 1:
        same = {int(c["period"]) for c in cells if c["lesson_id"] == body.lesson_id
                and int(c.get("part") or 0) == body.part and c.get("status") != "entfall"
                and c.get("kind") not in ("entfall", "klasse_abwesend") and c.get("teacher") == cell.get("teacher")}
        if not set(block) <= same or block != list(range(block[0], block[-1] + 1)):
            raise HTTPException(422, "Die Stunden gehören nicht zu einer zusammenhängenden Doppelstunde")
    return block


def _derive(a: AttendanceIn, i: int, block: list[int]) -> dict:
    """Anwesenheit einer Person in der ``i``-ten Stunde des Blocks aus der einmaligen Eingabe: ``fehlt`` gilt für alle
    (oder nur die genannten) Stunden, „zu spät“ zählt in der ersten, „früher gegangen“ ab ``left_from``."""
    p = block[i]
    extra = {"note": a.note.strip()} if a.note.strip() else {}
    status: dict = {"status": "present"}
    if a.status == "absent":
        if not a.missing or p in a.missing:
            status = {"status": "absent"}
    elif a.status == "late":
        if i == 0:
            status = {"status": "late", **({"minutes": a.minutes} if a.minutes else {})}
    elif a.status == "left":
        if len(block) == 1:
            status = {"status": "left"}
        else:
            start = a.left_from if a.left_from in block[1:] else block[-1]
            j = block.index(start)
            if i == j - 1:
                status = {"status": "left"}
            elif i >= j:
                status = {"status": "left", "gone": True}
    return {**status, **extra}


def _log_withdrawn(db: Session, row, user, lead: bool) -> None:
    alog.record(db, row.id, row.student_id, "zurueckgenommen", user, class_lead=lead, channel="klassenbuch",
                detail={"kind": row.kind or "krank", "date_from": row.date_from, "date_to": row.date_to,
                        "periods": list(row.periods or []), "status": row.status, "register_id": row.register_id})


@router.put("/register/lesson")
def save_lesson(body: LessonIn, class_id: str = Query(..., max_length=40), user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    from schulmanager.server.db_models import StudentAbsence
    snap = snapshot()
    school = snap[1]
    if school.index("classes").get(class_id) is None:
        raise HTTPException(404, "Klasse nicht gefunden")
    cells = _class_cells(body.date, class_id, snap)
    cell = next((c for c in cells if c["lesson_id"] == body.lesson_id and int(c["period"]) == body.period
                 and int(c.get("part") or 0) == body.part), None)
    if cell is None:
        raise HTTPException(404, "Diese Stunde findet an dem Tag für die Klasse nicht statt")
    if not _may_write(user, class_id, cell, snap):
        raise HTTPException(403, "Das Klassenbuch dieser Stunde führt die Lehrkraft der Stunde bzw. die Klassenleitung")
    allowed = set(_students_of(school, class_id, cell))
    for a in body.attendance:
        if a.student_id not in allowed:
            raise HTTPException(422, f"{a.student_id} ist in dieser Stunde nicht eingetragen")
    block = _block_periods(body, cells, cell)
    block_cells = {p: next(c for c in cells if c["lesson_id"] == body.lesson_id and int(c["period"]) == p
                           and int(c.get("part") or 0) == body.part) for p in block}
    entries: list[RegisterLesson] = []
    for p in block:
        c = block_cells[p]
        entry = db.scalar(select(RegisterLesson).where(RegisterLesson.date == body.date.isoformat(),
                                                       RegisterLesson.lesson_id == body.lesson_id,
                                                       RegisterLesson.period == p, RegisterLesson.part == body.part))
        if entry is None:
            entry = RegisterLesson(date=body.date.isoformat(), lesson_id=body.lesson_id, period=p, part=body.part,
                                   course_id=c.get("course_id") or "", class_ids=list(c.get("classes") or []),
                                   subject=c.get("subject") or "", teacher_id=c.get("teacher"), topic_enc="",
                                   homework_enc="", attendance_enc="", checked_by_name="", checked_at=utcnow())
            db.add(entry)
            db.flush()
        entries.append(entry)
    block_ids = {e.id for e in entries}
    # Fehlzeiten abgleichen (Meldungen von außen, z. B. Krankmeldung, vor allen Änderungen lesen)
    reported = _reported(db, list(allowed), body.date)

    def external(sid: str, p: int) -> bool:
        return any(x.register_id not in block_ids and _covers(x, p) for x in reported.get(sid, []))

    atts = [{a.student_id: _derive(a, i, block) for a in body.attendance} for i in range(len(block))]
    lead = _full_access(user, class_id, snap) and getattr(user, "role", "") == "lehrer"
    created = removed = 0
    for i, entry in enumerate(entries):
        period = block[i]
        att = atts[i]
        entry.topic_enc = crypto.encrypt_text(body.topic.strip(), entry.aad("topic"))
        entry.homework_enc = crypto.encrypt_text(body.homework.strip(), entry.aad("homework"))
        entry.attendance_enc = crypto.encrypt_text(json.dumps(att), entry.aad("attendance"))
        entry.checked_by, entry.checked_by_name, entry.checked_at = (user.id or None, user.display_name or user.username,
                                                                     utcnow())
        own = {a.student_id: a for a in db.scalars(select(StudentAbsence).where(StudentAbsence.register_id == entry.id))}
        later = sorted({int(c["period"]) for c in cells if int(c["period"]) > period and c.get("kind") != "entfall"})
        for sid, a in att.items():
            status = a["status"]
            want: Optional[tuple[str, list[int], Optional[int]]] = None
            if status == "absent" and not external(sid, period):
                if i > 0 and atts[i - 1][sid]["status"] == "absent" and not external(sid, block[i - 1]):
                    want = None                      # gehört zum Eintrag der vorigen Stunde des Blocks
                else:
                    run = [period]
                    for j in range(i + 1, len(block)):
                        if atts[j][sid]["status"] != "absent" or external(sid, block[j]):
                            break
                        run.append(block[j])
                    want = ("fehlt", run, None)
            elif status == "late":
                want = ("verspaetung", [period], a.get("minutes"))
            elif status == "left" and later and not a.get("gone"):
                want = ("frueh", later, None)
            row = own.get(sid)
            if want is None:
                if row is not None:
                    _log_withdrawn(db, row, user, lead)
                    db.delete(row)
                    removed += 1
                continue
            kind, periods, minutes = want
            if row is None:
                row = StudentAbsence(student_id=sid, date_from=body.date.isoformat(), date_to=body.date.isoformat(),
                                     periods=periods, reason="", status="gemeldet", note=a.get("note", ""),
                                     reported_by=user.id or None, reported_by_name=user.display_name or user.username,
                                     created_at=utcnow(), kind=kind, minutes=minutes, source="lehrkraft",
                                     excused_by_name="", register_id=entry.id)
                db.add(row)
                db.flush()
                alog.record(db, row.id, sid, "angelegt", user, class_lead=lead, channel="klassenbuch",
                            detail={"kind": kind, "date_from": row.date_from, "date_to": row.date_to,
                                    "periods": list(periods), "status": "gemeldet", "register_id": entry.id,
                                    "lesson_period": period,
                                    **({"minutes": minutes} if minutes else {})})
                created += 1
            else:
                diff = {k: [old, new] for k, old, new in (("kind", row.kind, kind), ("periods", list(row.periods or []), periods),
                                                        ("minutes", row.minutes, minutes)) if old != new}
                row.kind, row.periods, row.minutes, row.updated_at = kind, periods, minutes, utcnow()
                row.note = a.get("note", "")
                if diff:
                    alog.record(db, row.id, sid, "aenderung", user, class_lead=lead, channel="klassenbuch", changes=diff,
                                detail={"kind": kind, "register_id": entry.id})
        for sid, row in own.items():
            if sid not in att:
                _log_withdrawn(db, row, user, lead)
                db.delete(row)
                removed += 1
        write_audit(db, user, "register.save", f"register:{entry.id}",
                    {"class_id": class_id, "date": entry.date, "period": entry.period, "absences_created": created,
                     "absences_removed": removed, **({"block": block} if len(block) > 1 else {})})
    db.commit()
    publish_change(["register", "student_absences"], [body.date.isoformat()])
    return register_day(class_id, body.date.isoformat(), user, db)
