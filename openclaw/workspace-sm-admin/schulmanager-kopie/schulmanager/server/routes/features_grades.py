"""Noten: Klausuren/Tests (``exam_results``) und bewertete Hausaufgaben der Kursräume.

* ``GET  /exams/{exam_id}/results`` – Schüler/innen des Kurses (bzw. Kursteils) mit Note/Bemerkung
  (Lehrkraft des Kurses oder Personal mit ``exam.edit`` ohne Einschränkung)
* ``PUT  /exams/{exam_id}/results`` – Noten eintragen/ändern (leere Note = löschen)
* ``GET  /grades?student_id=`` – „Meine Noten“: alle Noten eines Kindes nach Fach (Schüler/in selbst, Eltern –
  bei volljährigen Kindern nur mit deren Freigabe –, Klassenleitung/Lehrkräfte der Klasse, Sekretariat/Leitung)
Noten und Bemerkungen liegen nur verschlüsselt in der Datenbank. Mitschüler/innen sehen nie fremde Noten.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import crypto
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import User
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.grades import ExamResult

from .features_common import has, own_student_ids, publish_change, snapshot, students_in_scope, write_audit

router = APIRouter(tags=["Noten"])
MAX_GRADE = 20


class ResultIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=40)
    grade: str = Field("", max_length=MAX_GRADE)
    note: str = Field("", max_length=500)


class ResultsIn(BaseModel):
    results: list[ResultIn] = Field(default_factory=list, max_length=400)


def _dec(token: str, aad: str) -> str:
    if not token:
        return ""
    try:
        return crypto.decrypt_text(token, aad)
    except Exception:  # noqa: BLE001
        return ""


def _exam(school, exam_id: str):
    e = next((x for x in school.exams if x.id == exam_id), None)
    if e is None:
        raise HTTPException(404, "Klausur/Test nicht gefunden")
    return e


def _exam_students(school, e) -> list[str]:
    from schulmanager import channels as logic
    course = school.index("courses").get(e.course_id)
    if course is None:
        return []
    parts = [e.part] if e.part is not None else list(range(len(course.parts)))
    out: list[str] = []
    for p in parts:
        for sid in logic.channel_student_ids(school, logic.COURSE, logic.course_ref(course.id, p)):
            if sid not in out:
                out.append(sid)
    return out


def _may_grade(user, school, e) -> bool:
    from .features_exams import _can_edit
    return has(user, "exam.edit") and _can_edit(user, school, e)


@router.get("/exams/{exam_id}/results")
def get_results(exam_id: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    school = snap[1]
    e = _exam(school, exam_id)
    if not _may_grade(user, school, e):
        raise HTTPException(403, "Noten trägt die Lehrkraft des Kurses ein")
    students = school.index("students")
    rows = {r.student_id: r for r in db.scalars(select(ExamResult).where(ExamResult.exam_id == exam_id))}
    out = []
    for sid in sorted(_exam_students(school, e), key=lambda s: (students[s].class_id, students[s].name)
                      if s in students else ("", s)):
        r = rows.get(sid)
        st = students.get(sid)
        out.append({"student_id": sid, "name": st.name if st else sid, "class_id": st.class_id if st else None,
                    "grade": _dec(r.grade_enc, r.aad("grade")) if r else "",
                    "note": _dec(r.note_enc, r.aad("note")) if r else "",
                    "graded_at": iso(r.graded_at) if r else None})
    return {"exam_id": exam_id, "title": e.title, "kind": getattr(e, "kind", "klausur"), "date": e.date,
            "course_id": e.course_id, "students": out}


@router.put("/exams/{exam_id}/results")
def put_results(exam_id: str, body: ResultsIn, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    school = snap[1]
    e = _exam(school, exam_id)
    if not _may_grade(user, school, e):
        raise HTTPException(403, "Noten trägt die Lehrkraft des Kurses ein")
    allowed = set(_exam_students(school, e))
    rows = {r.student_id: r for r in db.scalars(select(ExamResult).where(ExamResult.exam_id == exam_id))}
    changed = 0
    for item in body.results:
        if item.student_id not in allowed:
            raise HTTPException(422, f"{item.student_id} schreibt diese Klausur/diesen Test nicht mit")
        grade, note = item.grade.strip(), item.note.strip()
        r = rows.get(item.student_id)
        if not grade and not note:
            if r is not None:
                db.delete(r)
                changed += 1
            continue
        if r is None:
            r = ExamResult(exam_id=exam_id, course_id=e.course_id, student_id=item.student_id, grade_enc="",
                           note_enc="", graded_at=utcnow())
            db.add(r)
            db.flush()
        elif _dec(r.grade_enc, r.aad("grade")) == grade and _dec(r.note_enc, r.aad("note")) == note:
            continue
        r.grade_enc = crypto.encrypt_text(grade, r.aad("grade"))
        r.note_enc = crypto.encrypt_text(note, r.aad("note"))
        r.graded_by, r.graded_by_name, r.graded_at = user.id or None, user.display_name or user.username, utcnow()
        changed += 1
    if changed:
        write_audit(db, user, "exam.grades", f"exam:{exam_id}", {"changed": changed})
        db.commit()
        try:    # Notenbuch: schon übernommene Klausurnoten nachziehen (docs/NOTENBUCH.md)
            from schulmanager.server import gradebook_sources
            if gradebook_sources.sync_links(db, "klausur", exam_id):
                db.commit()
                publish_change(["gradebook"])
        except Exception:  # noqa: BLE001 - das Notenbuch darf das Eintragen der Klausurnoten nie verhindern
            db.rollback()
        publish_change(["grades"])
    return {"changed": changed, **get_results(exam_id, user, db)}


def _may_see(db: Session, user, sid: str, snap, area: str = "noten") -> bool:
    """Schüler/in selbst; Eltern (volljährige Kinder nur mit Einwilligung im Bereich ``area``, Elternzugriff);
    Personal mit Sicht auf die Schülerin/den Schüler (``students.read`` im eigenen Umfang)."""
    from schulmanager.server import parent_access as pa
    role = getattr(user, "role", "")
    if role in ("schueler", "eltern"):
        if sid not in own_student_ids(user):
            return False
        return role == "schueler" or pa.parent_may_see(db, sid, area, school=snap[1])
    if not has(user, "students.read"):
        return False
    scope = students_in_scope(user, "students.read", snap)
    return scope is None or sid in scope


@router.get("/grades")
def student_grades(student_id: Optional[str] = Query(None, max_length=40), user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Alle Noten eines Kindes nach Fach: Klausuren/Tests und bewertete Hausaufgaben."""
    from schulmanager import channels as logic
    from schulmanager.server.feature_models.channels import AssignmentSubmission, Channel, ChannelItem

    snap = snapshot()
    school = snap[1]
    if not student_id:
        own = own_student_ids(user)
        if len(own) != 1:
            raise HTTPException(422, "Bitte die Schülerin/den Schüler angeben")
        student_id = own[0]
    st = school.index("students").get(student_id)
    if st is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    if not _may_see(db, user, student_id, snap):
        raise HTTPException(403, "Keine Berechtigung für diese Noten")
    courses = school.index("courses")
    subjects = school.index("subjects")
    exams = {x.id: x for x in school.exams}
    by_subject: dict[str, list[dict[str, Any]]] = {}

    def subj_of(course_id: str, part: Optional[int]) -> str:
        c = courses.get(course_id)
        if c is None or not c.parts:
            return ""
        return c.parts[part if part is not None and part < len(c.parts) else 0].subject

    for r in db.scalars(select(ExamResult).where(ExamResult.student_id == student_id)):
        e = exams.get(r.exam_id)
        grade = _dec(r.grade_enc, r.aad("grade"))
        if not grade and not _dec(r.note_enc, r.aad("note")):
            continue
        subj = subj_of(e.course_id, e.part) if e else ""
        by_subject.setdefault(subj, []).append({
            "kind": getattr(e, "kind", "klausur") if e else "klausur", "title": (e.title if e else "") or "Klausur",
            "date": e.date if e else iso(r.graded_at)[:10], "grade": grade, "note": _dec(r.note_enc, r.aad("note")),
            "by": r.graded_by_name})
    pupil_uid = db.scalar(select(User.id).where(User.student_id == student_id, User.role == "schueler")
                          .order_by(User.id).limit(1))
    if pupil_uid:
        rows = db.execute(select(AssignmentSubmission, ChannelItem.title, ChannelItem.due_at, Channel)
                          .join(ChannelItem, ChannelItem.id == AssignmentSubmission.item_id)
                          .join(Channel, Channel.id == ChannelItem.channel_id)
                          .where(AssignmentSubmission.student_user_id == pupil_uid,
                                 AssignmentSubmission.status == "bewertet")).all()
        for sub, title, due_at, ch in rows:
            grade = sub.read_text("grade") if hasattr(sub, "read_text") else ""
            if not grade:
                continue
            subj = ""
            if ch.kind == logic.COURSE and ch.ref:
                parsed = logic.parse_course_ref(ch.ref)
                if parsed:
                    subj = subj_of(parsed[0], parsed[1])
            by_subject.setdefault(subj, []).append({
                "kind": "hausaufgabe", "title": title, "date": iso(due_at)[:10] if due_at else
                (iso(sub.feedback_at) or "")[:10], "grade": grade, "note": "", "by": ""})
    out = []
    for subj, entries in by_subject.items():
        entries.sort(key=lambda x: x["date"] or "", reverse=True)
        out.append({"subject": subj, "subject_name": subjects[subj].name if subj in subjects else (subj or "Sonstiges"),
                    "entries": entries})
    out.sort(key=lambda x: x["subject_name"].lower())
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id}, "subjects": out}
