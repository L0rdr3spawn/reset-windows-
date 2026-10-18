"""Datenarten der mitgelieferten Module im Löschkonzept (``retention.register``).

Neue Module melden sich entweder hier oder (besser) in ihrem eigenen Modul mit :func:`retention.register` an – die
Registrierung ist die einzige Stelle, an der Löschen **und** Auskunft einer Datenart zusammenlaufen. Dieses Modul wird
beim ersten Zugriff auf die Registry geladen (``retention.kinds()``).

Jede ``purge_fn`` zählt bei ``ctx.dry_run`` nur; jede ``export_fn`` liefert die Abschnitte der Auskunft (Klartext, soweit
die Person die Daten auch in der Oberfläche sieht). Rechtsgrundlagen sind Hinweise, keine Rechtsberatung.
"""
from __future__ import annotations

import json
import logging
import zlib
from datetime import date
from typing import Any, Optional

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from . import crypto, files, parent_access, retention
from .db import iso
from .db_models import AuditLog, ParentLink, SchoolVersion, StudentAbsence, User
from .retention import PurgeContext, Subject, count_rows, purge_rows, register

log = logging.getLogger("schulmanager.retention")

LEGAL_SCHULE = "Art. 6 Abs. 1 lit. e DSGVO i. V. m. Landesschulgesetz (Bildungsauftrag)"
LEGAL_GESUNDHEIT = "Art. 9 Abs. 2 DSGVO i. V. m. Landesschulgesetz / Schuldatenverordnung"
UNREADABLE = "[nicht lesbar]"


def _dec(token: Optional[str], aad: str) -> str:
    if not token:
        return ""
    if not crypto.is_token(token):
        return token
    try:
        return crypto.decrypt_text(token, aad)
    except crypto.CryptoError:
        return UNREADABLE


def _any(*conds: Any) -> Any:
    """ODER über die nicht leeren Bedingungen; ``None``, wenn es keine gibt."""
    real = [c for c in conds if c is not None]
    if not real:
        return None
    return real[0] if len(real) == 1 else or_(*real)


def _by(ctx: PurgeContext, student_col: Any = None, user_col: Any = None) -> Any:
    return _any(student_col.in_(ctx.student_ids) if student_col is not None and ctx.student_ids else None,
                user_col.in_(ctx.user_ids) if user_col is not None and ctx.user_ids else None)


def _sids(db: Session, model: Any, col: Any, *conds: Any) -> set[str]:
    return {str(i) for i in db.scalars(select(col).where(col.is_not(None), *conds).distinct()) if i}


def _hard_delete_files(db: Session, ids: list[str], ctx: PurgeContext) -> int:
    ids = [i for i in dict.fromkeys(ids) if i]
    if ctx.dry_run:
        return len(ids)
    return files.delete_many(db, ids, None, hard=True)


# ================================================================================================ Gesundheit
def _purge_absences(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.absence_log import AbsenceEvent
    from .feature_models.makeups import ExamMakeup

    if not ctx.student_ids:
        return 0
    n = purge_rows(db, ctx, AbsenceEvent, AbsenceEvent.student_id.in_(ctx.student_ids))
    n += purge_rows(db, ctx, ExamMakeup, ExamMakeup.student_id.in_(ctx.student_ids))
    n += purge_rows(db, ctx, StudentAbsence, StudentAbsence.student_id.in_(ctx.student_ids))
    return n


def _expire_absences(db: Session, today: date, days: int, dry_run: bool) -> int:
    """Krankmeldungen: Ende des Schuljahres (31. Juli) + ``days`` Tage."""
    from .feature_models.absence_log import AbsenceEvent
    from .feature_models.makeups import ExamMakeup

    end = retention.school_year_end_before(today, days).isoformat()
    ids = list(db.scalars(select(StudentAbsence.id).where(StudentAbsence.date_to <= end)))
    if not ids or dry_run:
        return len(ids)
    n = 0
    for i in range(0, len(ids), 500):
        part = ids[i:i + 500]
        n += int(db.execute(delete(AbsenceEvent).where(AbsenceEvent.absence_id.in_(part))).rowcount or 0)
        n += int(db.execute(delete(ExamMakeup).where(ExamMakeup.absence_id.in_(part))).rowcount or 0)
        n += int(db.execute(delete(StudentAbsence).where(StudentAbsence.id.in_(part))).rowcount or 0)
    return n


def _export_absences(db: Session, s: Subject) -> dict:
    from .routes.features_student_absences import export_rows
    return {"student_absences": export_rows(db, s.user)}


register("absences", _purge_absences, _export_absences, label="Krankmeldungen und Fehlzeiten",
         category="gesundheit", legal=LEGAL_GESUNDHEIT, default_days=30, age_default=365,
         expire_fn=_expire_absences, order=10,
         ids_fn=lambda db: _sids(db, StudentAbsence, StudentAbsence.student_id),
         description="Meldungen mit Grund und Vermerk, Meldungsprotokoll, Nachschreibtermine. Laufend: Ende des "
                     "Schuljahres (31. Juli) plus Frist; nach Austritt: Frist ab Austritt.")


def _purge_documents(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.student_self import StudentDocument

    cond = _by(ctx, StudentDocument.student_id, StudentDocument.uploaded_by)
    if cond is None:
        return 0
    docs = db.execute(select(StudentDocument.id, StudentDocument.file_id).where(cond)).all()
    n = _hard_delete_files(db, [f for _i, f in docs if f], ctx)
    return n + purge_rows(db, ctx, StudentDocument, cond)


def _export_documents(db: Session, s: Subject) -> dict:
    from .routes.features_student_self import export_documents
    return {"student_documents": export_documents(db, s.user, list(s.user.student_ids))}


def _doc_ids(db: Session) -> set[str]:
    from .feature_models.student_self import StudentDocument
    return _sids(db, StudentDocument, StudentDocument.student_id)


register("documents", _purge_documents, _export_documents, label="Atteste und Dokumente", category="gesundheit",
         legal=LEGAL_GESUNDHEIT, default_days=30, age_default=400, order=11, ids_fn=_doc_ids,
         description="Eingereichte Atteste und Bescheinigungen samt Datei. Die Alters-Frist (Standard 400 Tage, "
                     "`SM_STUDENT_DOCS_RETENTION_DAYS`) führt die Wartung getrennt aus.")


def _purge_support(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.support import StudentSupport

    if not ctx.student_ids:
        return 0
    rows = db.scalars(select(StudentSupport.file_ids).where(StudentSupport.student_id.in_(ctx.student_ids))).all()
    n = _hard_delete_files(db, [f for ids in rows for f in (ids or [])], ctx)
    return n + purge_rows(db, ctx, StudentSupport, StudentSupport.student_id.in_(ctx.student_ids))


def _export_support(db: Session, s: Subject) -> dict:
    from .feature_models.support import StudentSupport

    sids = s.is_minor_child_ids(db)
    if not sids:
        return {}
    out = []
    for r in db.scalars(select(StudentSupport).where(StudentSupport.student_id.in_(sids)).order_by(StudentSupport.id)):
        out.append({"id": r.id, "student_id": r.student_id, "kind": r.kind, "title": _dec(r.title_enc, r.aad("title")),
                    "details": _dec(r.details_enc, r.aad("details")), "valid_from": r.valid_from,
                    "valid_to": r.valid_to, "minutes": r.minutes, "subjects": r.subjects,
                    "aids": _dec(r.aids_enc, r.aad("aids")), "created_by_name": r.created_by_name,
                    "created_at": iso(r.created_at)})
    return {"support": out}


def _support_ids(db: Session) -> set[str]:
    from .feature_models.support import StudentSupport
    return _sids(db, StudentSupport, StudentSupport.student_id)


register("support", _purge_support, _export_support, label="Förder- und Unterstützungsdaten", category="gesundheit",
         legal=LEGAL_GESUNDHEIT, default_days=30, order=12, ids_fn=_support_ids,
         description="Nachteilsausgleich, Förderpläne, Hilfsmittel samt Dateien.")


def _purge_forms(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.forms import FormSubmission
    from .routes.features_forms import REF_TYPE

    cond = _by(ctx, FormSubmission.student_id, FormSubmission.submitted_by)
    if cond is None:
        return 0
    ids = list(db.scalars(select(FormSubmission.id).where(cond)))
    n = 0
    for sub_id in ids:
        if ctx.dry_run:
            n += int(count_rows(db, files.StoredFile, files.StoredFile.ref_type == REF_TYPE,
                                files.StoredFile.ref_id == str(sub_id)))
        else:
            n += files.delete_for_ref(db, REF_TYPE, sub_id, hard=True)
    return n + purge_rows(db, ctx, FormSubmission, cond)


def _export_forms(db: Session, s: Subject) -> dict:
    from .routes.features_forms import export_rows
    return {"forms": export_rows(db, s.user)}


def _forms_ids(db: Session) -> set[str]:
    from .feature_models.forms import FormSubmission
    return _sids(db, FormSubmission, FormSubmission.student_id)


register("forms", _purge_forms, _export_forms, label="Formular-Einreichungen", category="gesundheit",
         legal=LEGAL_GESUNDHEIT, default_days=90, age_default=400, order=13, ids_fn=_forms_ids,
         description="Ausgefüllte Formulare (z. B. Beurlaubung, Einwilligung) samt Anhängen und Verlauf.")


# ================================================================================================ Leistung
def _purge_exam_results(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.grades import ExamResult
    if not ctx.student_ids:
        return 0
    return purge_rows(db, ctx, ExamResult, ExamResult.student_id.in_(ctx.student_ids))


def _export_exam_results(db: Session, s: Subject) -> dict:
    from .feature_models.grades import ExamResult
    from .store import get_store

    sids = s.children(db, parent_access.AREA_GRADES)
    if not sids:
        return {}
    exams = get_store().school.index("exams")
    out = []
    for r in db.scalars(select(ExamResult).where(ExamResult.student_id.in_(sids)).order_by(ExamResult.id)):
        ex = exams.get(r.exam_id)
        out.append({"student_id": r.student_id, "exam": getattr(ex, "title", "") or r.exam_id,
                    "date": getattr(ex, "date", None), "course_id": r.course_id,
                    "grade": _dec(r.grade_enc, r.aad("grade")), "note": _dec(r.note_enc, r.aad("note")),
                    "graded_by_name": r.graded_by_name, "graded_at": iso(r.graded_at)})
    return {"exam_results": out}


def _exam_ids(db: Session) -> set[str]:
    from .feature_models.grades import ExamResult
    return _sids(db, ExamResult, ExamResult.student_id)


register("exam_results", _purge_exam_results, _export_exam_results, label="Klausurergebnisse", category="leistung",
         legal=LEGAL_SCHULE, default_days=180, order=20, ids_fn=_exam_ids,
         description="Noten und Anmerkungen zu Klassenarbeiten und Klausuren.")


def _purge_gradebook(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.gradebook import GradeEntry, GradeFinal, GradeLog, GradeSourceResult
    if not ctx.student_ids:
        return 0
    n = 0
    for model in (GradeEntry, GradeFinal, GradeLog, GradeSourceResult):
        n += purge_rows(db, ctx, model, model.student_id.in_(ctx.student_ids))
    return n


def _export_gradebook(db: Session, s: Subject) -> dict:
    from .feature_models.gradebook import GradeBook, GradeEntry, GradeFinal, GradeItem, GradeSourceResult

    sids = s.children(db, parent_access.AREA_GRADES)
    if not sids:
        return {}
    items = {i.id: i for i in db.scalars(select(GradeItem))}
    books = {b.id: b for b in db.scalars(select(GradeBook))}
    entries = []
    for e in db.scalars(select(GradeEntry).where(GradeEntry.student_id.in_(sids)).order_by(GradeEntry.id)):
        it = items.get(e.item_id)
        bk = books.get(it.book_id) if it else None
        entries.append({"student_id": e.student_id, "item": it.title if it else "", "date": it.date if it else "",
                        "course_id": bk.course_id if bk else "", "term": bk.term if bk else "",
                        "value": _dec(e.value_enc, e.aad("value")), "status": e.status,
                        "note": _dec(e.note_enc, e.aad("note")), "entered_by_name": e.entered_by_name,
                        "entered_at": iso(e.entered_at)})
    finals = []
    for f in db.scalars(select(GradeFinal).where(GradeFinal.student_id.in_(sids)).order_by(GradeFinal.id)):
        bk = books.get(f.book_id)
        finals.append({"student_id": f.student_id, "course_id": bk.course_id if bk else "",
                       "term": bk.term if bk else "", "value": _dec(f.value_enc, f.aad("value")),
                       "note": _dec(f.note_enc, f.aad("note")), "set_by_name": f.set_by_name,
                       "set_at": iso(f.set_at)})
    sources = [{"student_id": r.student_id, "type": r.source_type, "title": r.title, "date": r.date,
                "points": r.points, "max_points": r.max_points, "grade": r.grade}
               for r in db.scalars(select(GradeSourceResult).where(GradeSourceResult.student_id.in_(sids)))]
    return {"gradebook_entries": entries, "gradebook_finals": finals, "gradebook_source_results": sources}


def _gradebook_ids(db: Session) -> set[str]:
    from .feature_models.gradebook import GradeEntry, GradeFinal
    return _sids(db, GradeEntry, GradeEntry.student_id) | _sids(db, GradeFinal, GradeFinal.student_id)


register("gradebook", _purge_gradebook, _export_gradebook, label="Notenbuch", category="leistung",
         legal=LEGAL_SCHULE, default_days=180, order=21, ids_fn=_gradebook_ids,
         description="Einzelnoten, Halbjahres-/Zeugnisnoten, Änderungsprotokoll und übernommene Ergebnisse.")


def _purge_competencies(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.competency import CompAssessment, CompBadgeAward, CompPlan
    if not ctx.student_ids:
        return 0
    return sum(purge_rows(db, ctx, m, m.student_id.in_(ctx.student_ids))
               for m in (CompAssessment, CompPlan, CompBadgeAward))


def _export_competencies(db: Session, s: Subject) -> dict:
    from .feature_models.competency import (CompAssessment, CompBadge, CompBadgeAward, CompCompetency, CompPlan)

    sids = s.children(db, parent_access.AREA_COMPETENCIES)
    if not sids:
        return {}
    comps = {c.id: c for c in db.scalars(select(CompCompetency))}
    badges = {b.id: b for b in db.scalars(select(CompBadge))}
    assessments = []
    for a in db.scalars(select(CompAssessment).where(CompAssessment.student_id.in_(sids)).order_by(CompAssessment.id)):
        c = comps.get(a.competency_id)
        assessments.append({"student_id": a.student_id, "competency": (c.title if c else ""), "code": c.code if c else "",
                            "kind": a.kind, "level": a.level, "assessed_on": a.assessed_on,
                            "evidence": _dec(a.evidence_enc, a.aad("evidence")),
                            "comment": _dec(a.comment_enc, a.aad("comment")), "by_name": a.by_name})
    plans = [{"student_id": p.student_id, "title": _dec(p.title_enc, p.aad("title")),
              "note": _dec(p.note_enc, p.aad("note")), "week_start": p.week_start, "due_date": p.due_date,
              "status": p.status, "source": p.source}
             for p in db.scalars(select(CompPlan).where(CompPlan.student_id.in_(sids)).order_by(CompPlan.id))]
    awards = [{"student_id": w.student_id, "badge": badges[w.badge_id].name if w.badge_id in badges else "",
               "awarded_on": w.awarded_on, "awarded_by_name": w.awarded_by_name,
               "note": _dec(w.note_enc, w.aad("note"))}
              for w in db.scalars(select(CompBadgeAward).where(CompBadgeAward.student_id.in_(sids)))]
    return {"competency_assessments": assessments, "competency_plans": plans, "competency_badges": awards}


def _comp_ids(db: Session) -> set[str]:
    from .feature_models.competency import CompAssessment, CompPlan
    return _sids(db, CompAssessment, CompAssessment.student_id) | _sids(db, CompPlan, CompPlan.student_id)


register("competencies", _purge_competencies, _export_competencies, label="Lernstand und Kompetenzen",
         category="leistung", legal=LEGAL_SCHULE, default_days=180, order=22, ids_fn=_comp_ids,
         description="Kompetenzstufen, Selbsteinschätzungen, Lernpläne und Abzeichen.")


def _attendance_rows(db: Session):
    from .feature_models.register import RegisterLesson
    for row in db.scalars(select(RegisterLesson).where(RegisterLesson.attendance_enc != "")):
        try:
            att = json.loads(_dec(row.attendance_enc, row.aad("attendance")) or "{}")
        except ValueError:
            continue
        if isinstance(att, dict):
            yield row, att


def _purge_attendance(db: Session, ctx: PurgeContext) -> int:
    if not ctx.student_ids:
        return 0
    n = 0
    for row, att in list(_attendance_rows(db)):
        hit = [s for s in ctx.student_ids if s in att]
        if not hit:
            continue
        n += len(hit)
        if not ctx.dry_run:
            for s in hit:
                att.pop(s, None)
            row.attendance_enc = crypto.encrypt_text(json.dumps(att), row.aad("attendance"))
    return n


def _export_attendance(db: Session, s: Subject) -> dict:
    sids = set(s.children(db, parent_access.AREA_SICK_NOTES))
    if not sids:
        return {}
    out = []
    for row, att in _attendance_rows(db):
        for sid in sids & set(att):
            val = att[sid] if isinstance(att[sid], dict) else {"status": att[sid]}
            out.append({"student_id": sid, "date": row.date, "period": row.period, "course_id": row.course_id,
                        "subject": row.subject, "status": val.get("status"), "minutes": val.get("minutes"),
                        "recorded_by_name": row.checked_by_name})
    out.sort(key=lambda r: (r["date"], r["period"]))
    return {"register_attendance": out}


def _attendance_ids(db: Session) -> set[str]:
    out: set[str] = set()
    for _row, att in _attendance_rows(db):
        out |= {str(k) for k in att}
    return out


register("attendance", _purge_attendance, _export_attendance, label="Klassenbuch-Anwesenheit", category="leistung",
         legal=LEGAL_SCHULE + " (Klassenbuch-Aufbewahrung nach Landesrecht prüfen)", default_days=365, order=23,
         ids_fn=_attendance_ids, how="anonymisiert",
         description="Anwesenheitsvermerke der Person in den Klassenbuch-Einträgen (Thema und Hausaufgabe bleiben).")


# ================================================================================================ Unterricht
def _purge_submissions(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.channels import AssignmentSubmission

    cond = _by(ctx, AssignmentSubmission.student_id, AssignmentSubmission.student_user_id)
    if cond is None:
        return 0
    file_ids: list[str] = []
    for sub in db.scalars(select(AssignmentSubmission).where(cond)):
        file_ids += list(sub.file_ids or []) + list(sub.feedback_file_ids or [])
        for v in _versions(db, sub.id):
            file_ids += list(v.file_ids or []) + list(v.feedback_file_ids or [])
    n = _hard_delete_files(db, file_ids, ctx)
    return n + purge_rows(db, ctx, AssignmentSubmission, cond)


def _versions(db: Session, submission_id: int):
    from .feature_models.assignments import AssignmentSubmissionVersion
    return db.scalars(select(AssignmentSubmissionVersion).where(
        AssignmentSubmissionVersion.submission_id == submission_id))


def _file_names(db: Session, ids: Any) -> list[str]:
    out = []
    for fid in ids or []:
        meta = files.get_file(db, fid, include_deleted=True)
        if meta is not None:
            try:
                out.append(meta.filename)
            except crypto.CryptoError:
                out.append(UNREADABLE)
    return out


def _export_submissions(db: Session, s: Subject) -> dict:
    from .feature_models.channels import AssignmentSubmission, ChannelItem

    uids = s.child_user_ids(db, parent_access.AREA_CHANNELS)
    if not uids:
        return {}
    out = []
    for sub in db.scalars(select(AssignmentSubmission).where(AssignmentSubmission.student_user_id.in_(uids))
                          .order_by(AssignmentSubmission.id)):
        item = db.scalar(select(ChannelItem).where(ChannelItem.id == sub.item_id),
                         execution_options={"include_trashed": True})
        out.append({
            "student_id": sub.student_id, "channel_id": item.channel_id if item else None,
            "assignment": item.title if item else "", "attempt": sub.attempt, "status": sub.status,
            "submitted_at": iso(sub.submitted_at), "text": sub.read_text("text"), "files": _file_names(db, sub.file_ids),
            "feedback": sub.read_text("feedback"), "feedback_files": _file_names(db, sub.feedback_file_ids),
            "grade": sub.read_text("grade"), "points": sub.points, "max_points": sub.max_points,
            "rubric": sub.read_text("rubric"), "feedback_at": iso(sub.feedback_at),
            "earlier_versions": [{"attempt": v.attempt, "submitted_at": iso(v.submitted_at),
                                  "text": v.read_text("text"), "feedback": v.read_text("feedback"),
                                  "grade": v.read_text("grade"), "points": v.points}
                                 for v in _versions(db, sub.id)]})
    return {"assignment_submissions": out}


def _submission_ids(db: Session) -> set[str]:
    from .feature_models.channels import AssignmentSubmission
    return _sids(db, AssignmentSubmission, AssignmentSubmission.student_id)


register("submissions", _purge_submissions, _export_submissions, label="Abgaben und Rückmeldungen",
         category="unterricht", legal=LEGAL_SCHULE, default_days=90, order=30, ids_fn=_submission_ids,
         description="Abgegebene Aufgaben samt Dateien, Versionen, Bewertungen und Rückmeldungen.")


def _purge_learning(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.learning import (LearningAttempt, LearningPollParticipant, LearningPollVote,
                                          LearningSurveyParticipant, LearningSurveyResponse)
    if not ctx.user_ids:
        return 0
    return sum(purge_rows(db, ctx, m, m.user_id.in_(ctx.user_ids))
               for m in (LearningAttempt, LearningPollVote, LearningPollParticipant, LearningSurveyResponse,
                         LearningSurveyParticipant))


def _export_learning(db: Session, s: Subject) -> dict:
    from .feature_models.learning import (LearningAttempt, LearningPoll, LearningPollParticipant, LearningPollVote,
                                          LearningSelftest, LearningSurvey, LearningSurveyParticipant,
                                          LearningSurveyResponse)

    uids = s.child_user_ids(db, parent_access.AREA_CHANNELS)
    if not uids:
        return {}
    tests = {t.id: t.title for t in db.scalars(select(LearningSelftest))}
    attempts = [{"test": tests.get(a.test_id, ""), "number": a.number, "started_at": iso(a.started_at),
                 "finished_at": iso(a.finished_at), "points": a.points, "max_points": a.max_points,
                 "percent": a.percent, "answers": a.read_text("answers")}
                for a in db.scalars(select(LearningAttempt).where(LearningAttempt.user_id.in_(uids))
                                    .order_by(LearningAttempt.id))]
    polls = {p.id: p for p in db.scalars(select(LearningPoll))}
    votes: dict[int, list[int]] = {}
    for v in db.scalars(select(LearningPollVote).where(LearningPollVote.user_id.in_(uids))):
        votes.setdefault(v.poll_id, []).append(v.option_index)
    poll_rows = [{"poll": polls[p.poll_id].read_text("question") if p.poll_id in polls else "",
                  "anonymous": bool(polls[p.poll_id].anonymous) if p.poll_id in polls else None,
                  "chosen_options": votes.get(p.poll_id, [])}
                 for p in db.scalars(select(LearningPollParticipant).where(LearningPollParticipant.user_id.in_(uids)))]
    surveys = {x.id: x for x in db.scalars(select(LearningSurvey))}
    answers = {r.survey_id: r.read_text("answers") for r in db.scalars(
        select(LearningSurveyResponse).where(LearningSurveyResponse.user_id.in_(uids)))}
    survey_rows = [{"survey": surveys[p.survey_id].title if p.survey_id in surveys else "",
                    "answers": answers.get(p.survey_id, "(anonym gespeichert)")}
                   for p in db.scalars(select(LearningSurveyParticipant).where(
                       LearningSurveyParticipant.user_id.in_(uids)))]
    return {"selftest_attempts": attempts, "poll_participation": poll_rows, "survey_participation": survey_rows}


register("learning", _purge_learning, _export_learning, label="Selbsttests, Abstimmungen, Umfragen",
         category="unterricht", legal=LEGAL_SCHULE, default_days=90, order=31,
         description="Selbsttest-Versuche mit Antworten, namentliche Stimmen, Umfrage-Teilnahme. Anonym gespeicherte "
                     "Antworten sind keiner Person zuzuordnen und bleiben.")


def _purge_progress(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.assignments import AssignmentExtension
    from .feature_models.channel_groups import ChannelGroupMember
    from .feature_models.channels import ChannelExtraMember, ChannelItemView, ChannelRead
    from .feature_models.progress import CompletionMark
    if not ctx.user_ids:
        return 0
    return sum(purge_rows(db, ctx, m, m.user_id.in_(ctx.user_ids))
               for m in (CompletionMark, ChannelRead, ChannelItemView, ChannelGroupMember, ChannelExtraMember,
                         AssignmentExtension))


def _export_progress(db: Session, s: Subject) -> dict:
    from .feature_models.channel_groups import ChannelGroupMember
    from .feature_models.channels import ChannelExtraMember, ChannelItemView
    from .feature_models.progress import CompletionMark

    uids = s.child_user_ids(db, parent_access.AREA_CHANNELS)
    if not uids:
        return {}
    marks = [{"channel_id": m.channel_id, "element_type": m.element_type, "element_id": m.element_id,
              "done_at": iso(m.done_at)}
             for m in db.scalars(select(CompletionMark).where(CompletionMark.user_id.in_(uids)))]
    views = int(db.scalar(select(func.count()).select_from(ChannelItemView).where(ChannelItemView.user_id.in_(uids)))
                or 0)
    groups = [{"channel_id": g.channel_id, "group_id": g.group_id}
              for g in db.scalars(select(ChannelGroupMember).where(ChannelGroupMember.user_id.in_(uids)))]
    extra = [{"channel_id": e.channel_id, "role": e.role}
             for e in db.scalars(select(ChannelExtraMember).where(ChannelExtraMember.user_id.in_(uids)))]
    return {"progress_completion_marks": marks, "progress_opened_materials_count": views,
            "channel_groups": groups, "channel_extra_memberships": extra}


register("progress", _purge_progress, _export_progress, label="Fortschritt und Kursraum-Nutzung",
         category="unterricht", legal=LEGAL_SCHULE, default_days=90, order=32,
         description="Erledigt-Markierungen, geöffnetes Material, Gruppen- und Zusatzmitgliedschaften, Fristverlängerungen.")


# ================================================================================================ Kommunikation
def _purge_notifications(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.notifications import Notification, NotificationPref, NotificationUserSettings
    n = 0
    cond = _by(ctx, Notification.student_id, Notification.user_id)
    if cond is not None:
        n += purge_rows(db, ctx, Notification, cond)
    if ctx.user_ids:
        n += purge_rows(db, ctx, NotificationPref, NotificationPref.user_id.in_(ctx.user_ids))
        n += purge_rows(db, ctx, NotificationUserSettings, NotificationUserSettings.user_id.in_(ctx.user_ids))
    return n


def _export_notifications(db: Session, s: Subject) -> dict:
    from .feature_models.notifications import Notification, NotificationPref

    rows = [{"kind": n.kind, "title": n.read_text("title"), "text": n.read_text("body"), "link": n.link,
             "student_id": n.student_id, "created_at": iso(n.created_at), "read_at": iso(n.read_at)}
            for n in db.scalars(select(Notification).where(Notification.user_id == s.uid)
                                .order_by(Notification.id.desc()).limit(5000))]
    prefs = [{"kind": p.kind, **{c.key: getattr(p, c.key) for c in p.__table__.columns
                                 if c.key not in ("id", "user_id", "kind")}}
             for p in db.scalars(select(NotificationPref).where(NotificationPref.user_id == s.uid))]
    return {"notifications": rows, "notification_settings": prefs}


def _notif_ids(db: Session) -> set[str]:
    from .feature_models.notifications import Notification
    return _sids(db, Notification, Notification.student_id)


register("notifications", _purge_notifications, _export_notifications, label="Benachrichtigungen",
         category="kommunikation", legal=LEGAL_SCHULE, default_days=30, order=40, ids_fn=_notif_ids,
         description="Benachrichtigungen der Person und solche über sie (z. B. an Eltern), Einstellungen.")


def _purge_messages(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.messages import (Conversation, ConversationParticipant, Message, MessageDraft,
                                          MessageUserSettings, UserBlock)
    if not ctx.user_ids:
        return 0
    uids = ctx.user_ids
    conv_ids = list(db.scalars(select(ConversationParticipant.conversation_id).where(
        ConversationParticipant.user_id.in_(uids))))
    n = purge_rows(db, ctx, Message, Message.sender_id.in_(uids))
    n += purge_rows(db, ctx, MessageDraft, MessageDraft.user_id.in_(uids))
    n += purge_rows(db, ctx, UserBlock, or_(UserBlock.user_id.in_(uids), UserBlock.blocked_user_id.in_(uids)))
    n += purge_rows(db, ctx, MessageUserSettings, MessageUserSettings.user_id.in_(uids))
    n += purge_rows(db, ctx, ConversationParticipant, ConversationParticipant.user_id.in_(uids))
    if not ctx.dry_run and conv_ids:
        # Unterhaltungen, die nun niemanden mehr haben, samt Resten entfernen
        empty = select(Conversation.id).where(
            Conversation.id.in_(conv_ids), ~Conversation.id.in_(select(ConversationParticipant.conversation_id)))
        n += int(db.execute(delete(Conversation).where(Conversation.id.in_(empty))).rowcount or 0)
    return n


def _export_messages(db: Session, s: Subject) -> dict:
    from .feature_models.messages import Conversation, ConversationParticipant, Message

    names = {u.id: (u.display_name or u.username) for u in db.scalars(select(User))}
    convs = []
    for part in db.scalars(select(ConversationParticipant).where(ConversationParticipant.user_id == s.uid)):
        conv = db.get(Conversation, part.conversation_id)
        if conv is None:
            continue
        msgs = []
        for m in db.scalars(select(Message).where(Message.conversation_id == conv.id,
                                                  Message.id > (part.cleared_id or 0)).order_by(Message.id)):
            msgs.append({"id": m.id, "from": names.get(m.sender_id) or m.external_name or m.external_from or "",
                         "sent_at": iso(m.created_at),
                         "text": "[von der Moderation ausgeblendet]" if m.removed_at else _dec(m.body_enc, m.body_aad),
                         "attachments": _file_names(db, m.attachment_ids)})
        others = [names.get(p) or "" for p in db.scalars(select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conv.id, ConversationParticipant.user_id != s.uid))
                  if part.recipient_role != "bcc"]
        convs.append({"id": conv.id, "kind": conv.kind, "subject": _dec(conv.subject_enc, conv.subject_aad),
                      "created_at": iso(conv.created_at), "participants": others,
                      "archived": part.archived, "messages": msgs})
    return {"mailbox_conversations": convs}


register("messages", _purge_messages, _export_messages, label="Postfach-Nachrichten", category="kommunikation",
         legal=LEGAL_SCHULE, default_days=30, order=41,
         description="Eigene gesendete Nachrichten, Entwürfe, Sperrlisten, Teilnahmen an Unterhaltungen. Nachrichten "
                     "anderer an die Person bleiben bei den anderen, bis deren Aufbewahrungsfrist (`messaging_retention_days`) "
                     "endet.")


def _purge_chats(db: Session, ctx: PurgeContext) -> int:
    from .feature_models.chats import (Chat, ChatAttachment, ChatDevice, ChatKeyBackup, ChatLinkRequest, ChatMember,
                                       ChatMessage, ChatMessageKey, ChatReport, ChatReportImage)
    if not ctx.user_ids:
        return 0
    uids = ctx.user_ids
    direct = select(Chat.id).where(Chat.kind == "direct",
                                   Chat.id.in_(select(ChatMember.chat_id).where(ChatMember.user_id.in_(uids))))
    direct_ids = list(db.scalars(direct))
    msg_ids = list(db.scalars(select(ChatMessage.id).where(or_(ChatMessage.sender_id.in_(uids),
                                                              ChatMessage.chat_id.in_(direct_ids)
                                                              if direct_ids else ChatMessage.sender_id.in_(uids)))))
    rep_ids = list(db.scalars(select(ChatReport.id).where(or_(ChatReport.reporter_id.in_(uids),
                                                              ChatReport.sender_id.in_(uids)))))
    n = len(msg_ids) + len(rep_ids) + len(direct_ids)
    devices = list(db.scalars(select(ChatDevice.id).where(ChatDevice.user_id.in_(uids))))
    n += len(devices)
    n += purge_rows(db, ctx, ChatMember, ChatMember.user_id.in_(uids))
    n += purge_rows(db, ctx, ChatKeyBackup, ChatKeyBackup.user_id.in_(uids))
    n += purge_rows(db, ctx, ChatLinkRequest, ChatLinkRequest.user_id.in_(uids))
    if ctx.dry_run:
        return n
    for i in range(0, len(msg_ids), 500):
        part = msg_ids[i:i + 500]
        db.execute(delete(ChatMessageKey).where(ChatMessageKey.message_id.in_(part)))
        db.execute(delete(ChatAttachment).where(ChatAttachment.message_id.in_(part)))
        db.execute(delete(ChatMessage).where(ChatMessage.id.in_(part)))
    if devices:
        db.execute(delete(ChatMessageKey).where(ChatMessageKey.device_id.in_(devices)))
    db.execute(delete(ChatAttachment).where(ChatAttachment.uploader_id.in_(uids)))
    if rep_ids:
        db.execute(delete(ChatReportImage).where(ChatReportImage.report_id.in_(rep_ids)))
        db.execute(delete(ChatReport).where(ChatReport.id.in_(rep_ids)))
    db.execute(delete(ChatDevice).where(ChatDevice.user_id.in_(uids)))
    if direct_ids:
        db.execute(delete(ChatMember).where(ChatMember.chat_id.in_(direct_ids)))
        db.execute(delete(Chat).where(Chat.id.in_(direct_ids)))
    # Gruppen ohne Mitglieder entfernen
    empty = select(Chat.id).where(~Chat.id.in_(select(ChatMember.chat_id)))
    n += int(db.execute(delete(Chat).where(Chat.id.in_(empty))).rowcount or 0)
    return n


def _export_chats(db: Session, s: Subject) -> dict:
    from .feature_models.chats import (Chat, ChatDevice, ChatKeyBackup, ChatMember, ChatMessage, ChatReport)

    chats = []
    for mem in db.scalars(select(ChatMember).where(ChatMember.user_id == s.uid)):
        chat = db.get(Chat, mem.chat_id)
        if chat is None:
            continue
        own = db.scalars(select(ChatMessage).where(ChatMessage.chat_id == chat.id, ChatMessage.sender_id == s.uid)
                         .order_by(ChatMessage.id)).all()
        chats.append({"id": chat.id, "kind": chat.kind, "title": _dec(chat.title_enc, chat.title_aad),
                      "member_count": int(db.scalar(select(func.count()).select_from(ChatMember)
                                                    .where(ChatMember.chat_id == chat.id)) or 0),
                      "admin": mem.admin, "joined_at": iso(mem.joined_at), "muted": mem.muted,
                      "archived": mem.archived, "own_message_count": len(own),
                      "own_messages_encrypted": [{"id": m.id, "sent_at": iso(m.created_at),
                                                  "deleted_at": iso(m.deleted_at), "nonce": m.nonce,
                                                  "ciphertext": m.ciphertext} for m in own]})
    devices = [{"id": d.id, "label": d.label, "kind": d.kind, "created_at": iso(d.created_at),
                "last_seen_at": iso(d.last_seen_at), "revoked_at": iso(d.revoked_at)}
               for d in db.scalars(select(ChatDevice).where(ChatDevice.user_id == s.uid))]
    reports = [{"chat_id": r.chat_id, "reason": _dec(r.reason_enc, r.aad("reason")), "status": r.status,
                "created_at": iso(r.created_at)}
               for r in db.scalars(select(ChatReport).where(ChatReport.reporter_id == s.uid))]
    return {
        "hinweis_chats": "Chats sind Ende-zu-Ende-verschlüsselt: Der Server kann die Inhalte nicht lesen. Hier stehen "
                         "Mitgliedschaften, Zeitpunkte und die eigenen Nachrichten als verschlüsselte Daten; lesbar "
                         "sind sie nur auf Ihren Geräten.",
        "chats": chats, "chat_devices": devices,
        "chat_key_backup_exists": db.get(ChatKeyBackup, s.uid) is not None, "chat_reports_filed": reports}


register("chats", _purge_chats, _export_chats, label="Chats (Ende-zu-Ende-verschlüsselt)", category="kommunikation",
         legal=LEGAL_SCHULE, default_days=30, order=42, how="gelöscht",
         description="Mitgliedschaften, Geräte, Schlüssel-Backup, eigene Nachrichten und Anhänge; Einzelchats werden "
                     "ganz entfernt, Gruppenchats ohne Mitglieder ebenfalls.")


def _purge_files(db: Session, ctx: PurgeContext) -> int:
    if not ctx.user_ids:
        return 0
    ids = list(db.scalars(select(files.StoredFile.id).where(files.StoredFile.owner_user_id.in_(ctx.user_ids))))
    return _hard_delete_files(db, ids, ctx)


def _export_files(db: Session, s: Subject) -> dict:
    rows = []
    for f in db.scalars(select(files.StoredFile).where(files.StoredFile.owner_user_id == s.uid)
                        .order_by(files.StoredFile.created_at)):
        try:
            name = f.filename
        except crypto.CryptoError:
            name = UNREADABLE
        rows.append({"id": f.id, "filename": name, "type": f.content_type, "size_bytes": f.size,
                     "purpose": f.purpose, "uploaded_at": iso(f.created_at), "deleted_at": iso(f.deleted_at)})
    return {"files": rows}


register("files", _purge_files, _export_files, label="Hochgeladene Dateien", category="unterricht",
         legal=LEGAL_SCHULE, default_days=30, order=43,
         description="Dateien, deren Eigentümer das Konto ist (Inhalt und Eintrag).")


# ================================================================================================ Konten
def _purge_parents(db: Session, ctx: PurgeContext) -> int:
    from .accounts import delete_user
    from .feature_models.parent_access import ParentAccess, StudentPrefs

    if not ctx.student_ids:
        return 0
    n = 0
    parent_ids = set(db.scalars(select(ParentLink.parent_user_id).where(ParentLink.student_id.in_(ctx.student_ids))))
    n += purge_rows(db, ctx, ParentLink, ParentLink.student_id.in_(ctx.student_ids))
    n += purge_rows(db, ctx, ParentAccess, ParentAccess.student_id.in_(ctx.student_ids))
    n += purge_rows(db, ctx, StudentPrefs, StudentPrefs.student_id.in_(ctx.student_ids))
    for pid in sorted(parent_ids):
        parent = db.get(User, pid)
        if parent is None or parent.role not in ("eltern", "schulbegleitung"):
            continue
        if ctx.dry_run:
            others = count_rows(db, ParentLink, ParentLink.parent_user_id == pid,
                                ~ParentLink.student_id.in_(ctx.student_ids))
        else:
            others = count_rows(db, ParentLink, ParentLink.parent_user_id == pid)
        if others == 0:            # kein weiteres Kind: das Konto hat keinen Zweck mehr
            n += 1
            if not ctx.dry_run:
                _purge_account_data(db, [pid])
                delete_user(db, parent)
    return n


def _purge_account_data(db: Session, user_ids: list[int]) -> None:
    """Räumt die kontogebundenen Daten aller registrierten Datenarten (außer Konto/Verknüpfung), bevor ein Konto geht."""
    ctx = PurgeContext(user_ids=user_ids)
    for k in retention.kinds():
        if k.purge_fn is None or k.key in ("parents", "accounts", "history") or k.key in retention._STUDENT_ONLY:
            continue
        try:
            with db.begin_nested():
                k.purge_fn(db, ctx)
        except Exception:  # noqa: BLE001
            log.exception("Kontodaten der Datenart %s nicht bereinigt", k.key)


def _export_parents(db: Session, s: Subject) -> dict:
    from .feature_models.parent_access import ParentAccess
    from .store import get_store

    out: dict[str, Any] = {}
    if s.row.role == "schueler" and s.row.student_id:
        links = db.scalars(select(ParentLink.parent_user_id).where(ParentLink.student_id == s.row.student_id)).all()
        out["parent_accounts"] = [(db.get(User, p).display_name or db.get(User, p).username)
                                  for p in links if db.get(User, p)]
        out["parent_access_settings"] = [{"area": a.area, "allowed": a.allowed}
                                         for a in db.scalars(select(ParentAccess).where(
                                             ParentAccess.student_id == s.row.student_id))]
    elif s.row.role in ("eltern", "schulbegleitung"):
        students = get_store().school.index("students")
        out["linked_children"] = [{"student_id": sid, "name": students[sid].name if sid in students else ""}
                                  for sid in db.scalars(select(ParentLink.student_id).where(
                                      ParentLink.parent_user_id == s.uid))]
    return out


def _parent_ids(db: Session) -> set[str]:
    from .feature_models.parent_access import ParentAccess, StudentPrefs
    return (_sids(db, ParentLink, ParentLink.student_id) | _sids(db, ParentAccess, ParentAccess.student_id)
            | _sids(db, StudentPrefs, StudentPrefs.student_id))


register("parents", _purge_parents, _export_parents, label="Eltern-Verknüpfungen und Freigaben", category="konto",
         legal=LEGAL_SCHULE, default_days=30, order=50, ids_fn=_parent_ids,
         description="Verknüpfung Eltern–Kind, Freigaben volljähriger Schüler/innen, Einstellungen; Eltern-Konten ohne "
                     "weiteres Kind werden mit ihren Daten gelöscht.")


def _purge_accounts(db: Session, ctx: PurgeContext) -> int:
    from .accounts import delete_user
    n = 0
    for uid in ctx.user_ids:
        user = db.get(User, uid)
        if user is None or user.role == "admin":
            continue
        n += 1
        if not ctx.dry_run:
            delete_user(db, user)
    return n


register("accounts", _purge_accounts, None, label="Schüler-Konten", category="konto", legal=LEGAL_SCHULE,
         default_days=30, order=900, last=True,
         description="Das Konto wird zuletzt gelöscht (Anmeldung, Sitzungen, Tokens, Kontakt, Verknüpfungen, "
                     "Protokoll-Bezüge werden pseudonymisiert).")


# ================================================================================================ Verlauf
def _purge_history(db: Session, ctx: PurgeContext) -> int:
    """Entfernt die Person aus allen gespeicherten Planversionen und pseudonymisiert Protokoll-Bezüge."""
    from .routes.features_data import cascade_delete
    from .store import decode_school, encode_school, get_store

    if not ctx.student_ids:
        return 0
    present = get_store().school.index("students")
    sids = [s for s in ctx.student_ids if s not in present]       # Wer wieder im Dokument steht, bleibt unberührt
    if not sids:
        return 0
    needles = [json.dumps(s).encode("utf-8") for s in sids]
    name_needles = [json.dumps(n, ensure_ascii=False)[1:-1].encode("utf-8") for n in ctx.names if n]
    changed = 0
    for row in db.scalars(select(SchoolVersion)):
        try:
            raw = zlib.decompress(row.data)
        except zlib.error:
            continue
        if not any(x in raw for x in needles + name_needles):
            continue
        changed += 1
        if ctx.dry_run:
            continue
        try:
            school = decode_school(row.data)
        except Exception:  # noqa: BLE001
            continue
        for sid in sids:
            cascade_delete(school, "students", sid)
        school.students = [s for s in school.students if s.id not in sids]
        row.data = encode_school(school)[0]
        for name in ctx.names:
            if name and name in (row.message or ""):
                row.message = row.message.replace(name, "[gelöscht]")
    for sid in sids:
        targets = [f"student:{sid}", f"students:{sid}"]
        cond = AuditLog.target.in_(targets)
        if ctx.dry_run:
            changed += count_rows(db, AuditLog, cond)
        else:
            changed += int(db.execute(update(AuditLog).where(cond).values(target="student:gelöscht", details=None))
                           .rowcount or 0)
    return changed


register("history", _purge_history, None, label="Planverlauf und Protokoll-Bezüge", category="system",
         legal="Art. 5 Abs. 1 lit. c, e DSGVO (Datenminimierung, Speicherbegrenzung)", default_days=30, order=800,
         how="anonymisiert",
         description="Die Person wird aus allen gespeicherten Planversionen (Verlauf/Rückgängig) entfernt; "
                     "Audit-Einträge zur Person verlieren den Bezug.")
