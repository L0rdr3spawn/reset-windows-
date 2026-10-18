"""Nachschreibtermine (Klausur/Test verpasst): Liste, Termin festlegen, Attest-Verzicht, Erledigt.

* ``GET    /exam-makeups`` (``?from=&to=&status=&exam_id=&student_id=``) – Zeilen, die das Konto sehen darf
  (gleicht vorher mit Klausuren und Fehlzeiten ab).
* ``GET    /exam-makeups/summary`` – Zähler für Menü/Kachel: ``{open, attest_missing}``.
* ``POST   /exam-makeups/dates`` – Termin für eine oder mehrere Zeilen derselben Klausur festlegen
  (``exam.edit`` für diese Klausur); Konflikte → 409 ``{"detail":{"conflicts":[…]}}``, ``force`` nur für
  Planung/Leitung.
* ``PUT/DELETE /exam-makeups/dates/{id}`` – Termin ändern bzw. zurücknehmen (Zeilen wieder „offen“).
* ``PATCH  /exam-makeups/{id}`` – Status (``offen|erledigt|entfallen``, Lehrkraft der Klausur) und
  ``attest_waived`` (Klassenleitung/Sekretariat/Schulleitung).

Datenschutz: Fachlehrkräfte sehen nur „abwesend“, den Attest-Status und den Termin – nie Grund, Quelle oder Dokument.
Die technische Administration hat keinen Zugriff. Logik: ``schulmanager/server/makeups.py``.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import makeups as mk
from schulmanager.server.db import get_db, utcnow
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.makeups import MAKEUP_STATUS, ExamMakeup, ExamMakeupDate

from .features_common import parse_date, perm_scope, publish_change, snapshot, write_audit

router = APIRouter(tags=["Nachschreibtermine"])
mk.install_hooks()


class DateIn(BaseModel):
    makeup_ids: list[int] = Field(min_length=1, max_length=200)
    date: date
    start: int = Field(ge=0, le=15)
    length: int = Field(1, ge=1, le=8)
    room: Optional[str] = Field(None, max_length=40)
    note: str = Field("", max_length=300)
    force: bool = False


class DatePut(BaseModel):
    date: date
    start: int = Field(ge=0, le=15)
    length: int = Field(1, ge=1, le=8)
    room: Optional[str] = Field(None, max_length=40)
    note: str = Field("", max_length=300)
    force: bool = False


class MakeupPatch(BaseModel):
    status: Optional[Literal["offen", "erledigt", "entfallen"]] = None
    attest_waived: Optional[bool] = None


# ----------------------------------------------------------------------------- Ausgabe
def _names(school: Any, exam: Any) -> dict[str, dict[str, str]]:
    teachers, subjects, rooms, classes = (school.index(n) for n in ("teachers", "subjects", "rooms", "classes"))
    return {"teachers": {k: v.name for k, v in teachers.items() if v.name},
            "subjects": {k: v.name for k, v in subjects.items() if v.name},
            "rooms": {k: (v.name or k) for k, v in rooms.items()},
            "classes": {k: (v.name or k) for k, v in classes.items()}}


def _date_out(school: Any, dt: ExamMakeupDate, count: int) -> dict:
    st = school.settings
    return {"id": dt.id, "date": dt.date, "start": dt.start, "length": dt.length, "room": dt.room, "note": dt.note,
            "time": st.period_times[dt.start] if 0 <= dt.start < len(st.period_times) else "",
            "students": count}


def _rows_out(db: Session, acc: mk.MakeupAccess, rows: list[ExamMakeup]) -> list[dict]:
    from .features_exams import exam_info
    school = acc.school
    students = school.index("students")
    attests = mk.attest_states(db, rows)
    dates = {d.id: d for d in db.scalars(select(ExamMakeupDate).where(
        ExamMakeupDate.id.in_({r.date_id for r in rows if r.date_id})))} if rows else {}
    counts: dict[int, int] = {}
    for did in {r.date_id for r in rows if r.date_id}:
        counts[did] = len(db.scalars(select(ExamMakeup.id).where(ExamMakeup.date_id == did)).all())
    out = []
    for r in rows:
        exam = acc.exam(r)
        lvl = acc.level(r)
        if exam is None or lvl is None:
            continue
        info = exam_info(school, exam)
        st = students.get(r.student_id)
        at = attests.get(r.id, {"state": "fehlt", "label": mk.ATTEST_LABELS["fehlt"], "missing": True,
                                "absence_ids": []})
        dt = dates.get(r.date_id) if r.date_id else None
        out.append({
            "id": r.id, "exam_id": r.exam_id, "course_id": r.course_id, "student_id": r.student_id,
            "student_name": st.name if st else r.student_id, "class_id": st.class_id if st else None,
            "exam_title": exam.title or info.get("label", ""), "exam_kind": getattr(exam, "kind", "klausur"),
            "label": info.get("label", ""), "subject": info.get("subject", ""),
            "classes": info.get("classes", []), "teachers": info.get("teachers", []),
            "exam_date": r.exam_date, "exam_start": exam.start, "exam_length": exam.length,
            "exam_time": info.get("time", ""), "exam_room": exam.room,
            "status": r.status, "status_label": MAKEUP_STATUS.get(r.status, r.status),
            "source": r.source if lvl != mk.TEACHER else "abwesend",
            "source_label": mk.SOURCE_LABELS.get(r.source, "") if lvl != mk.TEACHER else "abwesend",
            "attest": {k: v for k, v in at.items() if lvl != mk.TEACHER or k != "absence_ids"},
            "attest_waived": r.attest_waived, "level": lvl,
            "appointment": _date_out(school, dt, counts.get(dt.id, 1)) if dt else None,
            "can_schedule": lvl == mk.TEACHER or acc.teaches(exam),
            "can_waive": lvl == mk.FULL,
            "names": _names(school, exam),
        })
    from .features_exams import attach_channels
    attach_channels(db, acc.user, acc.snap, out, "exam_id")
    return out


def _visible(db: Session, acc: mk.MakeupAccess, d1: str, d2: Optional[str], status: Optional[str],
             exam_id: Optional[str], student_id: Optional[str]) -> list[ExamMakeup]:
    q = select(ExamMakeup).where(ExamMakeup.exam_date >= d1)
    if d2:
        q = q.where(ExamMakeup.exam_date <= d2)
    if status:
        q = q.where(ExamMakeup.status == status)
    if exam_id:
        q = q.where(ExamMakeup.exam_id == exam_id)
    if student_id:
        q = q.where(ExamMakeup.student_id == student_id)
    rows = db.scalars(q.order_by(ExamMakeup.exam_date, ExamMakeup.exam_id, ExamMakeup.student_id)).all()
    return [r for r in rows if acc.level(r) is not None]


def _sync(db: Session, snap: Any) -> None:
    created = mk.sync(db, snap[1])
    db.commit()
    if created:
        publish_change(["makeups"])


def _scoped(user: Any) -> bool:
    return perm_scope(user, "exam.edit") == "own_courses"


# ----------------------------------------------------------------------------- Lesen
@router.get("/exam-makeups")
def list_makeups(date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
                 status: Optional[Literal["offen", "angesetzt", "erledigt", "entfallen"]] = None,
                 exam_id: Optional[str] = Query(None, max_length=80), student_id: Optional[str] = Query(None, max_length=40),
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Nachschreib-Zeilen im Zeitraum (Standard: Klausuren der letzten 120 Tage und alle künftigen)."""
    snap = snapshot()
    _sync(db, snap)
    d1 = parse_date(date_from, date.today() - timedelta(days=120), name="from")
    d2 = parse_date(date_to, name="to") if date_to else None
    acc = mk.MakeupAccess(user, snap, db)
    return _rows_out(db, acc, _visible(db, acc, d1.isoformat(), d2.isoformat() if d2 else None, status, exam_id,
                                       student_id))


@router.get("/exam-makeups/summary")
def summary(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """``open`` = Termin noch offen (für Lehrkraft der Klausur), ``attest_missing`` = Attest fehlt/abgelehnt
    (für Betroffene und Klassenleitung/Sekretariat), ``total`` = alle sichtbaren, nicht abgeschlossenen Zeilen."""
    snap = snapshot()
    _sync(db, snap)
    acc = mk.MakeupAccess(user, snap, db)
    rows = [r for r in _visible(db, acc, (date.today() - timedelta(days=120)).isoformat(), None, None, None, None)
            if r.status in ("offen", "angesetzt")]
    attests = mk.attest_states(db, rows)
    open_n = sum(1 for r in rows if r.status == "offen" and (acc.level(r) == mk.TEACHER or acc.teaches(acc.exam(r))))
    miss = sum(1 for r in rows if acc.level(r) in (mk.FULL, mk.FAMILY) and attests[r.id]["missing"])
    return {"open": open_n, "attest_missing": miss, "total": len(rows)}


# ----------------------------------------------------------------------------- Termine
def _load_rows(db: Session, acc: mk.MakeupAccess, ids: list[int]) -> tuple[list[ExamMakeup], Any]:
    rows = [db.get(ExamMakeup, i) for i in sorted(set(ids))]
    if any(r is None for r in rows) or not rows:
        raise HTTPException(404, "Nachschreibtermin nicht gefunden")
    rows = [r for r in rows if r is not None]
    if len({r.exam_id for r in rows}) != 1:
        raise HTTPException(422, "Ein Termin gilt immer nur für eine Klausur")
    exam = acc.exam(rows[0])
    if exam is None or any(acc.level(r) is None for r in rows):
        raise HTTPException(404, "Nachschreibtermin nicht gefunden")
    if not acc.teaches(exam):
        raise HTTPException(403, "Nachschreibtermine legt die Lehrkraft der Klausur (bzw. Planung/Leitung) fest")
    return rows, exam


def _conflicts(acc: mk.MakeupAccess, db: Session, user: Any, exam: Any, body: Any, ignore: Optional[int],
               rows: Optional[list[ExamMakeup]] = None) -> None:
    problems = mk.check_date(acc.school, db, exam, body.date, body.start, body.length, body.room or None, ignore,
                             [r.student_id for r in rows or []])
    if body.room and body.room not in acc.school.index("rooms"):
        raise HTTPException(422, f"Raum {body.room} existiert nicht")
    if problems and (_scoped(user) or not body.force):
        raise HTTPException(409, {"conflicts": problems})


@router.get("/exam-makeups/suggestions")
def suggestions(makeup_ids: str = Query(min_length=1, max_length=2000, description="Zeilen-IDs, durch Komma getrennt"),
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Terminvorschläge für das Nachschreiben der gewählten Zeilen (einer Klausur; Lehrkraft der Klausur bzw.
    Planung/Leitung): eigene Stunden der Lehrkraft, in denen die Kinder ohnehin sitzen, und freie Zeiten
    (Randstunden, Freistunden) mit freier Lehrkraft, freien Kindern und freiem Raum – siehe ``makeups.suggest``."""
    try:
        wanted = [int(x) for x in makeup_ids.split(",") if x.strip()][:200]
    except ValueError:
        raise HTTPException(422, "makeup_ids: Zahlen, durch Komma getrennt") from None
    if not wanted:
        raise HTTPException(422, "Keine Zeilen gewählt")
    snap = snapshot()
    acc = mk.MakeupAccess(user, snap, db)
    rows, exam = _load_rows(db, acc, wanted)
    students = acc.school.index("students")
    ids = [r.student_id for r in rows]
    return {"suggestions": mk.suggest(acc.school, db, exam, ids),
            "students": {sid: (students[sid].name if sid in students else sid) for sid in ids}}


@router.post("/exam-makeups/dates", status_code=201)
def create_date(body: DateIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    acc = mk.MakeupAccess(user, snap, db)
    rows, exam = _load_rows(db, acc, body.makeup_ids)
    _conflicts(acc, db, user, exam, body, None, rows)
    dt = ExamMakeupDate(exam_id=exam.id, date=body.date.isoformat(), start=body.start, length=body.length,
                        room=body.room or None, note=body.note.strip(), created_by=user.id or None,
                        created_by_name=user.display_name or user.username, created_at=utcnow())
    db.add(dt)
    db.flush()
    for r in rows:
        r.date_id, r.status, r.updated_at = dt.id, "angesetzt", utcnow()
        r.handled_by_name = user.display_name or user.username
    write_audit(db, user, "exam_makeup.schedule", f"exam_makeup_date:{dt.id}",
                {"exam_id": exam.id, "date": dt.date, "students": len(rows), "room": dt.room})
    db.commit()
    publish_change(["makeups", "exams"], [dt.date, rows[0].exam_date])
    return _date_out(acc.school, dt, len(rows))


@router.put("/exam-makeups/dates/{date_id}")
def update_date(date_id: int, body: DatePut, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    acc = mk.MakeupAccess(user, snap, db)
    dt = db.get(ExamMakeupDate, date_id)
    if dt is None:
        raise HTTPException(404, "Termin nicht gefunden")
    rows = db.scalars(select(ExamMakeup).where(ExamMakeup.date_id == date_id)).all()
    if not rows:
        raise HTTPException(404, "Termin nicht gefunden")
    rows, exam = _load_rows(db, acc, [r.id for r in rows])
    _conflicts(acc, db, user, exam, body, date_id, rows)
    old = dt.date
    dt.date, dt.start, dt.length = body.date.isoformat(), body.start, body.length
    dt.room, dt.note, dt.updated_at = body.room or None, body.note.strip(), utcnow()
    write_audit(db, user, "exam_makeup.reschedule", f"exam_makeup_date:{dt.id}",
                {"exam_id": exam.id, "date": dt.date, "from": old})
    db.commit()
    publish_change(["makeups", "exams"], [dt.date, old])
    return _date_out(acc.school, dt, len(rows))


@router.delete("/exam-makeups/dates/{date_id}")
def delete_date(date_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    acc = mk.MakeupAccess(user, snap, db)
    dt = db.get(ExamMakeupDate, date_id)
    rows = db.scalars(select(ExamMakeup).where(ExamMakeup.date_id == date_id)).all() if dt else []
    if dt is None or not rows:
        raise HTTPException(404, "Termin nicht gefunden")
    rows, exam = _load_rows(db, acc, [r.id for r in rows])
    for r in rows:
        if r.status == "angesetzt":
            r.status = "offen"
        r.date_id, r.updated_at = None, utcnow()
    write_audit(db, user, "exam_makeup.unschedule", f"exam_makeup_date:{dt.id}", {"exam_id": exam.id})
    day = dt.date
    db.flush()
    db.delete(dt)
    db.commit()
    publish_change(["makeups", "exams"], [day])
    return {"deleted": date_id}


# ----------------------------------------------------------------------------- Zeile ändern
@router.patch("/exam-makeups/{makeup_id}")
def patch_makeup(makeup_id: int, body: MakeupPatch, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    acc = mk.MakeupAccess(user, snap, db)
    row = db.get(ExamMakeup, makeup_id)
    lvl = acc.level(row) if row is not None else None
    if row is None or lvl is None:
        raise HTTPException(404, "Nachschreibtermin nicht gefunden")
    changes: dict[str, Any] = {}
    if body.status is not None and body.status != row.status:
        if not acc.teaches(acc.exam(row)):
            raise HTTPException(403, "Den Stand setzt die Lehrkraft der Klausur")
        if body.status == "offen":
            row.date_id = None
        changes["status"] = [row.status, body.status]
        row.status = body.status
        row.handled_by_name = user.display_name or user.username
    if body.attest_waived is not None and body.attest_waived != row.attest_waived:
        if lvl != mk.FULL:
            raise HTTPException(403, "Über das Attest entscheiden Klassenleitung, Sekretariat und Schulleitung")
        row.attest_waived = body.attest_waived
        row.waived_by_name = (user.display_name or user.username) if body.attest_waived else ""
        changes["attest_waived"] = body.attest_waived
    if changes:
        row.updated_at = utcnow()
        write_audit(db, user, "exam_makeup.update", f"exam_makeup:{row.id}",
                    {"exam_id": row.exam_id, "student_id": row.student_id, **changes})
        db.flush()
        for dt in db.scalars(select(ExamMakeupDate)):
            if not db.scalar(select(ExamMakeup.id).where(ExamMakeup.date_id == dt.id).limit(1)):
                db.delete(dt)
        db.commit()
        publish_change(["makeups", "exams"], [row.exam_date])
    return _rows_out(db, acc, [row])[0]


# ----------------------------------------------------------------------------- Kalender
def calendar_items(db: Session, user: Any, snap: Any, kind: str, ref: str, d1: date, d2: date
                   ) -> dict[str, list[dict]]:
    """Nachschreibtermine im Zeitraum als Kalender-Einträge (``exams``-Format, ``kind="nachschreiben"``):
    Schüler/in: eigene Termine; Lehrkraft: Termine eigener Klausuren; Raum: belegte Termine (ohne Namen)."""
    if kind not in ("student", "teacher", "room"):
        return {}
    school = snap[1]
    acc = mk.MakeupAccess(user, snap, db)
    dts = {d.id: d for d in db.scalars(select(ExamMakeupDate).where(ExamMakeupDate.date >= d1.isoformat(),
                                                                    ExamMakeupDate.date <= d2.isoformat()))}
    if not dts:
        return {}
    rows = db.scalars(select(ExamMakeup).where(ExamMakeup.date_id.in_(list(dts)),
                                               ExamMakeup.status.in_(("angesetzt", "erledigt")))).all()
    courses = school.index("courses")
    seen: set[tuple[int, str]] = set()
    out: dict[str, list[dict]] = {}
    for r in rows:
        exam = acc.exam(r)
        dt = dts[r.date_id]
        if exam is None:
            continue
        c = courses.get(exam.course_id)
        if kind == "student":
            if r.student_id != ref or acc.level(r) is None:
                continue
        elif kind == "teacher":
            if c is None or not any(p.teacher == ref for p in c.parts) or acc.level(r) is None:
                continue
        elif dt.room != ref:
            continue
        key = (dt.id, "x" if kind != "student" else r.student_id)
        if key in seen:
            continue
        seen.add(key)
        from .features_exams import exam_info
        info = exam_info(school, exam)
        out.setdefault(dt.date, []).append({
            "id": f"nm{dt.id}", "kind": "nachschreiben", "kind_label": "Nachschreibtermin",
            "title": f"Nachschreiben: {exam.title or info.get('label', '')}".strip(),
            "label": info.get("label", ""), "subject": info.get("subject", ""), "start": dt.start,
            "length": dt.length, "time": school.settings.period_times[dt.start]
            if 0 <= dt.start < len(school.settings.period_times) else "", "room": dt.room,
            "course_id": exam.course_id, "part": exam.part, "classes": info.get("classes", []),
            "teachers": info.get("teachers", []), "exam_id": exam.id})
    for lst in out.values():
        lst.sort(key=lambda x: (x["start"], x["label"]))
    return out
