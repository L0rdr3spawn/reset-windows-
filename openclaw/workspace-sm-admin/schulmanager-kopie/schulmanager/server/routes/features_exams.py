"""Klassenarbeiten/Klausuren.

Lehrkräfte (``exam.edit`` mit Scope ``own_courses``) dürfen nur Klausuren in eigenen Kursen
(bzw. im eigenen Kursteil) anlegen/ändern/löschen. Schüler/Eltern sehen die Klausuren
ihrer Kurse. Regelverstöße (``exams.check_exam``) → 409 ``{"detail":{"conflicts":[...]}}``,
außer ``force: true`` (nicht für Lehrkräfte).
"""
from __future__ import annotations

import dataclasses
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from schulmanager.models import Exam, School
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import (has, index, mutate, new_id, own_student_ids, parse_date, perm_scope, plan_course_ids,
                              reads_all_plans, snapshot, student_parts)

router = APIRouter(tags=["Klausuren"])


class ExamIn(BaseModel):
    id: Optional[str] = None
    course_id: str = Field(min_length=1)
    date: date
    start: int = Field(ge=0, le=15)
    length: int = Field(1, ge=1, le=8)
    title: str = Field("", max_length=200)
    part: Optional[int] = Field(None, ge=0)
    room: Optional[str] = None
    kind: Literal["klausur", "test"] = "klausur"
    force: bool = False


def exam_info(school: School, e: Exam) -> dict:
    """Klausur mit Anzeige-Informationen (Fach, Klassen, Lehrkraft, Uhrzeit)."""
    d = e.to_dict()
    c = school.index("courses").get(e.course_id)
    if c is not None:
        parts = [c.parts[e.part]] if e.part is not None and e.part < len(c.parts) else c.parts
        subjects = sorted({p.subject for p in parts})
        d.update(classes=list(c.classes), label=c.label or c.id, subject=subjects[0] if len(subjects) == 1 else "",
                 subjects=subjects, teachers=sorted({p.teacher for p in parts if p.teacher}))
    else:
        d.update(classes=[], label=e.course_id, subject="", subjects=[], teachers=[])
    st = school.settings
    d["time"] = st.period_times[e.start] if 0 <= e.start < len(st.period_times) else ""
    d["room_lesson"] = lesson_room(school, e, c)
    return d


def lesson_room(school: School, e: Exam, course) -> Optional[str]:
    """Raum der Unterrichtsstunde, in der die Klausur liegt (Ersatz, solange ``exam.room`` leer ist)."""
    if course is None:
        return None
    try:
        from schulmanager.exams import _course_lessons_on, _exam_date
        day = _exam_date(e)
        if day is None:
            return None
        rooms: list[str] = []
        for les in _course_lessons_on(school, course, day):
            if not les.start <= e.start < les.start + max(1, les.length):
                continue
            for i, r in enumerate(les.rooms or []):
                if r and (e.part is None or i == e.part) and r not in rooms:
                    rooms.append(r)
        if not rooms:
            parts = [course.parts[e.part]] if e.part is not None and e.part < len(course.parts) else course.parts
            rooms = sorted({p.room for p in parts if p.room})
        return ", ".join(rooms) or None
    except Exception:  # noqa: BLE001 - Anzeige-Zusatz darf die Liste nie verhindern
        return None


def channel_links(db: Session, user, snap, exams: list[Exam]) -> dict[str, int]:
    """Klausur-ID → Kursraum (Kursteil), den das Konto öffnen darf (sonst kein Eintrag)."""
    out: dict[str, int] = {}
    try:
        from schulmanager import channels as logic

        from . import features_channels as fc
        school = snap[1]
        idx = logic.index_for(school)
        courses = school.index("courses")
        for e in exams:
            c = courses.get(e.course_id)
            if c is None:
                continue
            for i in ([e.part] if e.part is not None and e.part < len(c.parts) else range(len(c.parts))):
                spec = logic.course_part_spec(idx, c, i)
                if spec is None:
                    continue
                row = fc._ensure_rows(db, [spec]).get((spec.kind, spec.ref))
                if row is not None and fc._role_for(db, user, row, spec, school) is not None:
                    out[e.id] = row.id
                    break
    except Exception:  # noqa: BLE001 - Link ist ein Zusatz
        return out
    return out


def attach_channels(db: Session, user, snap, rows: list[dict], key: str = "id") -> None:
    """Ergänzt Klausur-/Test-Zeilen um ``channel_id`` (Kursraum des Kurses/Kursteils) und ``can_open``: nur wenn das
    Konto den Kursraum öffnen darf, sonst ``None``/``False`` (dann bleibt der Klausur-Link). ``key``: Feld mit der
    Klausur-ID (bei Nachschreibterminen ``exam_id``)."""
    by_id = {e.id: e for e in snap[1].exams}
    wanted = [by_id[i] for i in dict.fromkeys(r.get(key) for r in rows) if i in by_id]
    links = channel_links(db, user, snap, wanted) if wanted else {}
    for r in rows:
        r["channel_id"] = links.get(r.get(key))
        r["can_open"] = r["channel_id"] is not None


def exam_names(school: School) -> dict[str, dict[str, str]]:
    """Volle Namen zu Kürzeln (Lehrkräfte, Fächer, Räume, Klassen) für Sprechblasen."""
    return {"teachers": {k: v.name for k, v in school.index("teachers").items() if v.name},
            "subjects": {k: v.name for k, v in school.index("subjects").items() if v.name},
            "rooms": {k: (v.name or k) for k, v in school.index("rooms").items()},
            "classes": {k: (v.name or k) for k, v in school.index("classes").items()}}


def _can_edit(user, school: School, e: Exam) -> bool:
    if not has(user, "exam.edit"):
        return False
    if perm_scope(user, "exam.edit") != "own_courses":
        return True
    tid = getattr(user, "teacher_id", None)
    c = school.index("courses").get(e.course_id)
    if not tid or c is None:
        return False
    if e.part is not None and e.part < len(c.parts):
        return c.parts[e.part].teacher == tid
    return any(p.teacher == tid for p in c.parts)


def _visible_filter(user, snap):
    """Sichtbare Klausuren: Planung/Leitung alle; Lehrkräfte (Scope) nur Kurse ihrer Klassen und eigene Kurse;
    Schüler/Eltern die gewählten Kursteile."""
    if reads_all_plans(user) or (has(user, "exam.edit") and perm_scope(user, "exam.edit") is None):
        return lambda e: True
    if has(user, "plans.read_all") or has(user, "exam.edit"):
        allowed = plan_course_ids(user, snap) or frozenset()
        return lambda e: e.course_id in allowed
    sels = [student_parts(sid, snap) for sid in own_student_ids(user)]
    if not sels:
        return None

    def ok(e: Exam) -> bool:
        return any(e.course_id in p and (e.part is None or e.part in p[e.course_id]) for p in sels)

    return ok


def _check(school: School, e: Exam) -> list[str]:
    from schulmanager.server.routes.features_data import exam_errors
    errs = exam_errors(school, e)
    if errs:
        raise HTTPException(422, "; ".join(errs))
    from schulmanager.exams import check_exam
    probe = dataclasses.replace(school, exams=[x for x in school.exams if x.id != e.id])
    return list(check_exam(probe, e))


def _sync_makeups() -> None:
    """Nachschreib-Zeilen mit den (geänderten) Klausuren abgleichen – nie mit Fehler für den Aufrufer."""
    from schulmanager.server import makeups
    makeups.sync_now()


def _to_exam(body: ExamIn, exam_id: str) -> Exam:
    return Exam(id=exam_id, course_id=body.course_id, date=body.date.isoformat(), start=body.start,
                length=body.length, title=body.title.strip(), part=body.part, room=body.room or None,
                kind=body.kind)


@router.get("/exams")
def list_exams(date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
               class_id: Optional[str] = None, course_id: Optional[str] = None, teacher: Optional[str] = None,
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Klausuren im Zeitraum (Standard: heute bis +8 Wochen), nach Rolle gefiltert."""
    d1 = parse_date(date_from, date.today(), name="from")
    d2 = parse_date(date_to, d1 + timedelta(weeks=8), name="to")
    snap = snapshot()
    school = snap[1]
    ok = _visible_filter(user, snap)
    if ok is None:
        raise HTTPException(403, "Keine Berechtigung")
    courses = index("courses", snap)
    out = []
    chosen = []
    for e in school.exams:
        if not (d1.isoformat() <= e.date <= d2.isoformat()) or not ok(e):
            continue
        c = courses.get(e.course_id)
        if course_id and e.course_id != course_id:
            continue
        if class_id and (c is None or class_id not in c.classes):
            continue
        if teacher and (c is None or not any(p.teacher == teacher for p in c.parts)):
            continue
        # can_edit: Lehrkräfte (own_courses) dürfen nur Klausuren eigener Kurse ändern (Anzeige der Knöpfe)
        chosen.append(e)
        out.append({**exam_info(school, e), "can_edit": _can_edit(user, school, e)})
    links = channel_links(db, user, snap, chosen)
    names = exam_names(school)
    for row in out:
        row["channel_id"] = links.get(row["id"])
        row["names"] = names
    out.sort(key=lambda x: (x["date"], x["start"]))
    return out


@router.post("/exams/check")
def check(body: ExamIn, user: AuthUser = Depends(require("exam.edit"))):
    """Prüft eine (geplante) Klausur ohne zu speichern → ``{"ok", "warnings"}``."""
    school = snapshot()[1]
    e = _to_exam(body, body.id or "__check__")
    warnings = _check(school, e)
    return {"ok": not warnings, "warnings": warnings, "allowed": _can_edit(user, school, e)}


@router.post("/exams", status_code=201)
def create_exam(body: ExamIn, user: AuthUser = Depends(require("exam.edit"))):
    lehrer = perm_scope(user, "exam.edit") == "own_courses"

    def fn(school: School):
        eid = (body.id or "").strip() or new_id([x.id for x in school.exams], "KA")
        if any(x.id == eid for x in school.exams):
            raise HTTPException(409, f"Klausur {eid} existiert bereits")
        e = _to_exam(body, eid)
        if not _can_edit(user, school, e):
            raise HTTPException(403, "Klausuren nur für eigene Kurse")
        warnings = _check(school, e)
        if warnings and (lehrer or not body.force):
            raise HTTPException(409, {"conflicts": warnings})
        school.exams.append(e)
        return {**exam_info(school, e), "warnings": warnings}

    res = mutate(user, f"Klausur {body.course_id} am {body.date.isoformat()} angelegt", fn, scope=["exams"],
                 dates=[body.date.isoformat()])
    _sync_makeups()
    _notify_exam(res.get("id"), "created", user)
    return res


@router.put("/exams/{exam_id}")
def update_exam(exam_id: str, body: ExamIn, user: AuthUser = Depends(require("exam.edit"))):
    lehrer = perm_scope(user, "exam.edit") == "own_courses"
    old = next((x for x in snapshot()[1].exams if x.id == exam_id), None)
    if old is None:
        raise HTTPException(404, f"Klausur {exam_id} nicht gefunden")

    def fn(school: School):
        for i, x in enumerate(school.exams):
            if x.id == exam_id:
                break
        else:
            raise HTTPException(404, f"Klausur {exam_id} nicht gefunden")
        e = _to_exam(body, exam_id)
        if not (_can_edit(user, school, x) and _can_edit(user, school, e)):
            raise HTTPException(403, "Klausuren nur für eigene Kurse")
        warnings = _check(school, e)
        if warnings and (lehrer or not body.force):
            raise HTTPException(409, {"conflicts": warnings})
        school.exams[i] = e
        return {**exam_info(school, e), "warnings": warnings}

    res = mutate(user, f"Klausur {exam_id} geändert", fn, scope=["exams"], dates=[old.date, body.date.isoformat()])
    _sync_makeups()
    _notify_exam(exam_id, "updated", user, old)
    return res


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: str, user: AuthUser = Depends(require("exam.edit"))):
    old = next((x for x in snapshot()[1].exams if x.id == exam_id), None)
    if old is None:
        raise HTTPException(404, f"Klausur {exam_id} nicht gefunden")

    def fn(school: School):
        x = next((e for e in school.exams if e.id == exam_id), None)
        if x is None:
            raise HTTPException(404, f"Klausur {exam_id} nicht gefunden")
        if not _can_edit(user, school, x):
            raise HTTPException(403, "Klausuren nur für eigene Kurse")
        school.exams = [e for e in school.exams if e.id != exam_id]
        return {"deleted": exam_id}

    res = mutate(user, f"Klausur {exam_id} gelöscht", fn, scope=["exams"], dates=[old.date])
    _sync_makeups()
    _notify_exam(exam_id, "deleted", user, old)
    return res


def _notify_exam(exam_id, action: str, user, old=None) -> None:
    """Glocke: Klausur angesetzt, verschoben oder abgesagt (siehe ``notification_hooks.exam_changed``)."""
    from schulmanager.server import notification_hooks
    exam = old if action == "deleted" else next((x for x in snapshot()[1].exams if x.id == exam_id), None)
    if exam is not None:
        notification_hooks.exam_changed(exam, action, user.id or None, old)
