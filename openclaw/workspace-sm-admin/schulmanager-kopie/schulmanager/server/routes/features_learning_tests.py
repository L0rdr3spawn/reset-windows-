"""Fragensammlung und Selbsttests im Kursraum (Doku: docs/LERNAKTIVITAETEN.md) – bewusst kein volles Quiz-System.

Fragensammlung (nur Lehrende; Fragen samt Lösung verlassen den Server nie in Richtung Schüler/in):

* ``GET/POST /channels/{id}/questions`` · ``PUT/DELETE /channels/{id}/questions/{qid}``
* ``POST /channels/{id}/questions/import`` ``{gift}`` · ``GET /channels/{id}/questions/export.gift?ids=``
* ``POST /channels/{id}/questions/copy`` ``{from_channel_id, ids}`` – Fragen aus einem anderen eigenen Kursraum

Selbsttests:

* ``GET/POST /channels/{id}/selftests`` · ``GET/PATCH/DELETE /channels/{id}/selftests/{tid}``
* Versuch: ``POST …/attempts`` (neu oder fortsetzen) · ``GET …/attempts/{aid}`` · ``PUT …/attempts/{aid}/answer``
  ``{question_id, answer}`` · ``POST …/attempts/{aid}/finish``
* Lehrende: ``GET …/results`` (je Schüler/in und Frage) · ``GET …/results.csv`` · ``GET …/grades`` (Punkte für das
  Notenbuch) · ``GET /channels/{id}/learning/elements`` (Elemente für Notenbuch/Abschlussbedingung)

Gewertet wird immer auf dem Server mit dem Abbild der Fragen vom Start des Versuchs. Ein abgelaufener Versuch wird beim
nächsten Zugriff mit den bis dahin gespeicherten Antworten abgeschlossen.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager import channels as chx
from schulmanager import forms as fx
from schulmanager import learning as lx
from schulmanager.server import learning_service as ls
from schulmanager.server.audit import audit
from schulmanager.server.learning_notify import announce
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import User
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.feature_models.channels import ChannelExtraMember
from schulmanager.server.feature_models.learning import LearningAttempt, LearningQuestion, LearningSelftest

from .features_channels import Ctx, _ctx, _notify, _to_utc

router = APIRouter(tags=["Lernaktivitäten"])

MAX_QUESTIONS = 1000        # Fragen je Kursraum
MAX_TESTS = 200
MAX_TEST_QUESTIONS = 100
MAX_IMPORT = 200


def _bad(exc: Exception) -> HTTPException:
    return HTTPException(422, str(exc))


# =========================================================================== Fragensammlung
class GiftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gift: str = Field(min_length=1, max_length=400_000)


class CopyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_channel_id: int
    ids: list[int] = Field(min_length=1, max_length=200)


def _question_row(ctx: Ctx, data: dict) -> LearningQuestion:
    return LearningQuestion(channel_id=ctx.ch.id, qtype=data["type"], category=data.get("category", ""),
                            created_by=ctx.user.id, created_at=utcnow())


def _store_question(db: Session, ctx: Ctx, data: dict) -> LearningQuestion:
    row = _question_row(ctx, data)
    db.add(row)
    db.flush()
    ls.write_json(row, "data", data)
    return row


def _usage(db: Session, channel_id: int) -> dict[int, list[dict]]:
    used: dict[int, list[dict]] = {}
    for t in db.scalars(select(LearningSelftest).where(LearningSelftest.channel_id == channel_id)):
        for qid in t.question_ids or []:
            used.setdefault(int(qid), []).append({"id": t.id, "title": t.title})
    return used


def _question_out(ctx: Ctx, row: LearningQuestion, data: dict, used: dict[int, list[dict]]) -> dict:
    return {"id": row.id, "type": data["type"], "category": data.get("category", ""), "title": lx.question_title(data),
            "points": data.get("points", 1), "data": data, "used_in": used.get(row.id, []),
            "editable": ctx.may_edit(row.created_by), "created_at": iso(row.created_at)}


def _need_questions(db: Session, user: AuthUser, channel_id: int, *, write: bool = False) -> Ctx:
    return _ctx(db, user, channel_id, manage=True)


def _count_questions(db: Session, channel_id: int) -> int:
    return int(db.scalar(select(func.count()).select_from(LearningQuestion).where(
        LearningQuestion.channel_id == channel_id)) or 0)


@router.get("/channels/{channel_id}/questions")
def list_questions(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _need_questions(db, user, channel_id)
    used = _usage(db, ctx.ch.id)
    out = []
    for row in db.scalars(select(LearningQuestion).where(LearningQuestion.channel_id == ctx.ch.id)
                          .order_by(LearningQuestion.id)):
        data = ls.load_question(row)
        if data is not None:
            out.append(_question_out(ctx, row, data, used))
    return {"questions": out, "types": lx.QUESTION_TYPES}


@router.post("/channels/{channel_id}/questions", status_code=201)
def create_question(channel_id: int, body: dict[str, Any], request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    ctx = _need_questions(db, user, channel_id)
    if _count_questions(db, ctx.ch.id) >= MAX_QUESTIONS:
        raise HTTPException(409, "Die Fragensammlung ist voll – bitte nicht benötigte Fragen löschen")
    try:
        data = lx.normalize_question(body)
    except lx.LearningError as exc:
        raise _bad(exc) from None
    row = _store_question(db, ctx, data)
    audit(db, user, "question.create", f"learning_question:{row.id}", {"channel_id": ctx.ch.id, "type": data["type"]},
          ip=client_ip(request))
    db.commit()
    return _question_out(ctx, row, data, {})


def _get_question(db: Session, ctx: Ctx, question_id: int) -> LearningQuestion:
    row = db.get(LearningQuestion, question_id)
    if row is None or row.channel_id != ctx.ch.id:
        raise HTTPException(404, "Frage nicht gefunden")
    return row


@router.put("/channels/{channel_id}/questions/{question_id}")
def update_question(channel_id: int, question_id: int, body: dict[str, Any], request: Request,
                    user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _need_questions(db, user, channel_id)
    row = _get_question(db, ctx, question_id)
    ctx.need_edit(row.created_by)
    try:
        data = lx.normalize_question(body)
    except lx.LearningError as exc:
        raise _bad(exc) from None
    row.qtype, row.category, row.updated_at = data["type"], data.get("category", ""), utcnow()
    ls.write_json(row, "data", data)
    audit(db, user, "question.update", f"learning_question:{row.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    return _question_out(ctx, row, data, _usage(db, ctx.ch.id))


@router.delete("/channels/{channel_id}/questions/{question_id}")
def delete_question(channel_id: int, question_id: int, request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    ctx = _need_questions(db, user, channel_id)
    row = _get_question(db, ctx, question_id)
    ctx.need_edit(row.created_by)
    removed = 0
    for t in db.scalars(select(LearningSelftest).where(LearningSelftest.channel_id == ctx.ch.id)):
        if question_id in (t.question_ids or []):
            t.question_ids = [i for i in t.question_ids if i != question_id]
            removed += 1
    db.delete(row)
    audit(db, user, "question.delete", f"learning_question:{question_id}", {"channel_id": ctx.ch.id},
          ip=client_ip(request))
    db.commit()
    return {"deleted": question_id, "removed_from_tests": removed}


@router.post("/channels/{channel_id}/questions/import", status_code=201)
def import_questions(channel_id: int, body: GiftIn, request: Request, user: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> dict:
    ctx = _need_questions(db, user, channel_id)
    questions, errors = lx.parse_gift(body.gift, limit=MAX_IMPORT)
    room = MAX_QUESTIONS - _count_questions(db, ctx.ch.id)
    if len(questions) > room:
        errors.append(f"Nur {max(room, 0)} Fragen passen noch in die Sammlung – der Rest wurde nicht übernommen")
        questions = questions[:max(room, 0)]
    rows = [_store_question(db, ctx, q) for q in questions]
    if rows:
        audit(db, user, "question.import", f"channel:{ctx.ch.id}", {"count": len(rows)}, ip=client_ip(request))
    db.commit()
    used = _usage(db, ctx.ch.id)
    return {"created": len(rows), "errors": errors,
            "questions": [_question_out(ctx, r, q, used) for r, q in zip(rows, questions)]}


@router.get("/channels/{channel_id}/questions/export.gift")
def export_questions(channel_id: int, ids: str = Query("", max_length=4000), user: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> Response:
    ctx = _need_questions(db, user, channel_id)
    wanted = {int(x) for x in ids.split(",") if x.strip().isdigit()}
    questions = []
    for row in db.scalars(select(LearningQuestion).where(LearningQuestion.channel_id == ctx.ch.id)
                          .order_by(LearningQuestion.id)):
        if wanted and row.id not in wanted:
            continue
        data = ls.load_question(row)
        if data is not None:
            questions.append(data)
    text, skipped = lx.export_gift(questions)
    if skipped:
        text = "".join(f"// {s}\n" for s in skipped) + "\n" + text
    return Response(text, media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="fragen.gift"'})


@router.post("/channels/{channel_id}/questions/copy", status_code=201)
def copy_questions(channel_id: int, body: CopyIn, request: Request, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    ctx = _need_questions(db, user, channel_id)
    source = _need_questions(db, user, body.from_channel_id)          # nur aus Kursräumen, in denen man lehrt
    if source.ch.id == ctx.ch.id:
        raise HTTPException(422, "Quelle und Ziel sind derselbe Kursraum")
    made = 0
    for row in db.scalars(select(LearningQuestion).where(LearningQuestion.channel_id == source.ch.id,
                                                         LearningQuestion.id.in_(body.ids))):
        data = ls.load_question(row)
        if data is None or _count_questions(db, ctx.ch.id) >= MAX_QUESTIONS:
            continue
        _store_question(db, ctx, data)
        made += 1
    audit(db, user, "question.copy", f"channel:{ctx.ch.id}", {"from": source.ch.id, "count": made},
          ip=client_ip(request))
    db.commit()
    return {"created": made}


# =========================================================================== Selbsttests
class TestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field("", max_length=3000)
    status: Literal["entwurf", "offen", "geschlossen"] = "entwurf"
    question_ids: list[int] = Field(default_factory=list, max_length=MAX_TEST_QUESTIONS)
    max_attempts: Optional[int] = Field(None, ge=1, le=50)
    time_limit_min: Optional[int] = Field(None, ge=1, le=600)
    shuffle_questions: bool = False
    shuffle_answers: bool = True
    immediate_feedback: bool = False
    review: Literal["none", "score", "full"] = "full"
    pass_percent: Optional[float] = Field(None, ge=0, le=100)
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None


class TestPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=3000)
    status: Optional[Literal["entwurf", "offen", "geschlossen"]] = None
    question_ids: Optional[list[int]] = Field(None, max_length=MAX_TEST_QUESTIONS)
    max_attempts: Optional[int] = Field(None, ge=1, le=50)
    clear_max_attempts: bool = False
    time_limit_min: Optional[int] = Field(None, ge=1, le=600)
    clear_time_limit: bool = False
    shuffle_questions: Optional[bool] = None
    shuffle_answers: Optional[bool] = None
    immediate_feedback: Optional[bool] = None
    review: Optional[Literal["none", "score", "full"]] = None
    pass_percent: Optional[float] = Field(None, ge=0, le=100)
    clear_pass_percent: bool = False
    opens_at: Optional[datetime] = None
    clear_opens_at: bool = False
    closes_at: Optional[datetime] = None
    clear_closes_at: bool = False


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: int
    answer: Any = None


def _get_test(db: Session, ctx: Ctx, test_id: int) -> LearningSelftest:
    test = db.get(LearningSelftest, test_id)
    if test is None or test.channel_id != ctx.ch.id:
        raise HTTPException(404, "Selbsttest nicht gefunden")
    return test


def _check_question_ids(db: Session, ctx: Ctx, ids: list[int]) -> list[int]:
    ids = list(dict.fromkeys(ids))
    if ids:
        found = set(db.scalars(select(LearningQuestion.id).where(LearningQuestion.channel_id == ctx.ch.id,
                                                                 LearningQuestion.id.in_(ids))))
        if set(ids) - found:
            raise HTTPException(422, "Eine ausgewählte Frage gibt es nicht (mehr)")
    return ids


def _state_of(test: LearningSelftest) -> str:
    if test.status != "offen":
        return test.status
    now = utcnow()
    if test.opens_at is not None and now < test.opens_at:
        return "geplant"
    if test.closes_at is not None and now >= test.closes_at:
        return "geschlossen"
    return "offen"


def _test_config(test: LearningSelftest) -> dict:
    return {"id": test.id, "title": test.title, "status": test.status, "state": _state_of(test),
            "max_attempts": test.max_attempts, "time_limit_min": test.time_limit_min,
            "shuffle_questions": test.shuffle_questions, "shuffle_answers": test.shuffle_answers,
            "immediate_feedback": test.immediate_feedback, "review": test.review, "pass_percent": test.pass_percent,
            "opens_at": iso(test.opens_at), "closes_at": iso(test.closes_at), "created_by": test.created_by,
            "question_count": len(test.question_ids or [])}


def _test_out(db: Session, ctx: Ctx, test: LearningSelftest, *, detail: bool = False) -> dict:
    out = _test_config(test)
    out["max_points"] = ls.test_max_points(db, test)
    out["editable"] = ctx.teacher and ctx.may_edit(test.created_by)
    if detail or ctx.teacher:
        out["description"] = test.read_text("description")
    if ctx.teacher:
        out["question_ids"] = list(test.question_ids or [])
        out["attempt_count"] = int(db.scalar(select(func.count()).select_from(LearningAttempt).where(
            LearningAttempt.test_id == test.id)) or 0)
    if ctx.student or ctx.teacher:
        mine = list(db.scalars(select(LearningAttempt).where(LearningAttempt.test_id == test.id,
                                                             LearningAttempt.user_id == ctx.user.id)
                               .order_by(LearningAttempt.number)))
        if ls.settle_all(db, mine):
            db.commit()
        best = ls.best_attempt(mine)
        running = next((a for a in mine if a.finished_at is None), None)
        out["mine"] = {
            "attempts": len(mine), "running_attempt": running.id if running else None,
            "best_attempt": best.id if best else None,
            "last_attempt": next((a.id for a in reversed(mine) if a.finished_at is not None), None),
            "best_points": best.points if best else None, "best_percent": best.percent if best else None,
            "max_points": best.max_points if best else None,
            "passed": ls.passed(test, best) if test.review != "none" else None,
            "done": best is not None and ls.passed(test, best) is not False,
            "attempts_left": None if (test.max_attempts is None or ctx.teacher) else max(test.max_attempts - len(mine), 0),
        }
    return out


@router.get("/channels/{channel_id}/selftests")
def list_tests(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id)
    if not (ctx.teacher or ctx.student):
        return {"tests": [], "can_create": False}
    rows = [t for t in db.scalars(select(LearningSelftest).where(LearningSelftest.channel_id == ctx.ch.id)
                                  .order_by(LearningSelftest.id.desc())) if ctx.teacher or t.status != "entwurf"]
    return {"tests": [_test_out(db, ctx, t) for t in rows], "can_create": ctx.teacher and not ctx.ch.archived}


def _apply_test(db: Session, ctx: Ctx, test: LearningSelftest, body: TestIn | TestPatch, *, patch: bool) -> None:
    fields = body.model_fields_set
    if body.title is not None:
        test.title = fx.clean_text(body.title, 200)
        if not test.title:
            raise HTTPException(422, "Bitte einen Titel eingeben")
    if body.description is not None:
        test.write_text("description", fx.clean_text(body.description, 3000, multiline=True))
    if body.question_ids is not None:
        test.question_ids = _check_question_ids(db, ctx, body.question_ids)
    for name in ("shuffle_questions", "shuffle_answers", "immediate_feedback", "review"):
        value = getattr(body, name)
        if value is not None:
            setattr(test, name, value)
    for name in ("max_attempts", "time_limit_min", "pass_percent"):
        if getattr(body, name) is not None or (not patch and name in fields):
            setattr(test, name, getattr(body, name))
        if patch and getattr(body, f"clear_{'time_limit' if name == 'time_limit_min' else name}", False):
            setattr(test, name, None)
    for name in ("opens_at", "closes_at"):
        if getattr(body, name) is not None:
            setattr(test, name, _to_utc(getattr(body, name), "den Zeitraum"))
        if patch and getattr(body, f"clear_{name}", False):
            setattr(test, name, None)
    if test.opens_at and test.closes_at and test.closes_at <= test.opens_at:
        raise HTTPException(422, "Das Ende liegt vor dem Beginn")
    if body.status is not None:
        test.status = body.status
    if test.status == "offen" and not ls.test_questions(db, test):
        raise HTTPException(422, "Zum Freigeben braucht der Test mindestens eine Frage")


@router.post("/channels/{channel_id}/selftests", status_code=201)
def create_test(channel_id: int, body: TestIn, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    if int(db.scalar(select(func.count()).select_from(LearningSelftest).where(
            LearningSelftest.channel_id == ctx.ch.id)) or 0) >= MAX_TESTS:
        raise HTTPException(409, "Zu viele Selbsttests in diesem Kursraum – bitte alte löschen")
    test = LearningSelftest(channel_id=ctx.ch.id, title="x", created_by=user.id, created_at=utcnow())
    db.add(test)
    db.flush()
    _apply_test(db, ctx, test, body, patch=False)
    if test.status == "offen":
        announce(db, ctx, "selftest", test.id)
    audit(db, user, "selftest.create", f"learning_selftest:{test.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _test_out(db, ctx, test, detail=True)


@router.get("/channels/{channel_id}/selftests/{test_id}")
def get_test(channel_id: int, test_id: int, user: AuthUser = Depends(current_user),
             db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id)
    test = _get_test(db, ctx, test_id)
    if not (ctx.teacher or (ctx.student and test.status != "entwurf")):
        raise HTTPException(404, "Selbsttest nicht gefunden")
    return _test_out(db, ctx, test, detail=True)


@router.patch("/channels/{channel_id}/selftests/{test_id}")
def patch_test(channel_id: int, test_id: int, body: TestPatch, request: Request,
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    test = _get_test(db, ctx, test_id)
    ctx.need_edit(test.created_by)
    was = test.status
    _apply_test(db, ctx, test, body, patch=True)
    if test.status == "offen" and was != "offen":
        announce(db, ctx, "selftest", test.id)
    test.updated_at = utcnow()
    db.flush()
    ls.publish_grades(db, test)
    audit(db, user, "selftest.update", f"learning_selftest:{test.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _test_out(db, ctx, test, detail=True)


@router.delete("/channels/{channel_id}/selftests/{test_id}")
def delete_test(channel_id: int, test_id: int, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    test = _get_test(db, ctx, test_id)
    ctx.need_edit(test.created_by)
    ls.withdraw_grades(db, test.id)
    db.delete(test)
    audit(db, user, "selftest.delete", f"learning_selftest:{test_id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"deleted": test_id}


# =========================================================================== Versuche
def _own_attempt(db: Session, ctx: Ctx, test: LearningSelftest, attempt_id: int) -> LearningAttempt:
    att = db.get(LearningAttempt, attempt_id)
    if att is None or att.test_id != test.id or att.user_id != ctx.user.id:
        raise HTTPException(404, "Versuch nicht gefunden")
    if ls.settle(att):
        db.commit()
    return att


def _checked_view(q: dict, answer: Any) -> dict:
    frac = lx.grade_question(q, answer) if lx.is_answered(q, answer) else 0.0
    return {"fraction": round(frac, 4), "correct": frac >= 0.999999,
            "points": round(float(q.get("points") or 0) * frac, 2), "max": q.get("points", 1),
            "solution": lx.solution_view(q), "feedback": lx.feedback_view(q, answer)}


def _attempt_out(db: Session, test: LearningSelftest, att: LearningAttempt, *, teacher_view: bool = False) -> dict:
    snapshot = ls.attempt_snapshot(att)
    state = ls.attempt_state(att)
    finished = att.finished_at is not None
    by_id = {item["qid"]: item["q"] for item in snapshot}
    review = "full" if teacher_view else test.review
    out: dict[str, Any] = {
        "id": att.id, "test_id": test.id, "number": att.number, "started_at": iso(att.started_at),
        "deadline_at": iso(att.deadline_at), "finished_at": iso(att.finished_at),
        "state": "finished" if finished else "running", "immediate_feedback": test.immediate_feedback,
        "time_left_s": None if finished or att.deadline_at is None
        else max(int((att.deadline_at - utcnow()).total_seconds()), 0),
        "answers": state["answers"], "checked": {}, "result": None, "title": test.title,
        "max_points": ls.attempt_max(snapshot),
    }
    show_questions = (not finished) or review == "full"
    if show_questions:
        out["questions"] = [lx.public_question(item["q"], item["qid"], att.seed, shuffle_answers=test.shuffle_answers)
                            for item in snapshot]
    if not finished and test.immediate_feedback:
        out["checked"] = {str(qid): _checked_view(by_id[int(qid)], state["answers"].get(str(qid)))
                          for qid in state["checked"] if int(qid) in by_id}
        out["running_points"] = round(sum(v["points"] for v in out["checked"].values()), 2)
    if finished:
        res: dict[str, Any] = {"finished": True}
        if review in ("score", "full"):
            res.update(points=att.points, max_points=att.max_points, percent=att.percent,
                       passed=ls.passed(test, att))
        if review == "full":
            rows = ls.read_json(att, "result", [])
            res["rows"] = rows
            res["details"] = {str(qid): _checked_view(q, state["answers"].get(str(qid))) for qid, q in by_id.items()}
        out["result"] = res
    return out


@router.post("/channels/{channel_id}/selftests/{test_id}/attempts", status_code=201)
def start_attempt(channel_id: int, test_id: int, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, write=True)
    test = _get_test(db, ctx, test_id)
    preview = ctx.teacher
    if not (preview or ctx.student) or (not preview and test.status == "entwurf"):
        raise HTTPException(404, "Selbsttest nicht gefunden")
    mine = list(db.scalars(select(LearningAttempt).where(LearningAttempt.test_id == test.id,
                                                         LearningAttempt.user_id == user.id)
                           .order_by(LearningAttempt.number)))
    if ls.settle_all(db, mine):
        db.commit()
    running = next((a for a in mine if a.finished_at is None), None)
    if running is not None:
        return _attempt_out(db, test, running)
    if not preview:
        state = _state_of(test)
        if state == "geplant":
            raise HTTPException(409, "Der Selbsttest ist noch nicht freigegeben")
        if state != "offen":
            raise HTTPException(409, "Der Selbsttest ist nicht (mehr) offen")
        if test.max_attempts is not None and len(mine) >= test.max_attempts:
            raise HTTPException(409, "Alle Versuche sind verbraucht")
    if not ls.test_questions(db, test):
        raise HTTPException(409, "Der Selbsttest hat keine Fragen")
    att = ls.start_attempt(db, test, user.id)
    audit(db, user, "selftest.start", f"learning_selftest:{test.id}", {"attempt": att.number}, ip=client_ip(request))
    db.commit()
    return _attempt_out(db, test, att)


@router.get("/channels/{channel_id}/selftests/{test_id}/attempts/{attempt_id}")
def get_attempt(channel_id: int, test_id: int, attempt_id: int, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id)
    test = _get_test(db, ctx, test_id)
    att = db.get(LearningAttempt, attempt_id)
    if att is None or att.test_id != test.id:
        raise HTTPException(404, "Versuch nicht gefunden")
    if att.user_id != user.id:
        if not (ctx.teacher and ctx.may_edit(test.created_by)):
            raise HTTPException(404, "Versuch nicht gefunden")
        if ls.settle(att):
            db.commit()
        return _attempt_out(db, test, att, teacher_view=True)
    if ls.settle(att):
        db.commit()
    return _attempt_out(db, test, att)


@router.put("/channels/{channel_id}/selftests/{test_id}/attempts/{attempt_id}/answer")
def save_answer(channel_id: int, test_id: int, attempt_id: int, body: AnswerIn, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, write=True)
    test = _get_test(db, ctx, test_id)
    att = _own_attempt(db, ctx, test, attempt_id)
    if att.finished_at is not None:
        raise HTTPException(409, "Der Versuch ist schon beendet" + (" – die Zeit ist abgelaufen" if att.deadline_at
                                                                       and att.finished_at >= att.deadline_at else ""))
    snapshot = ls.attempt_snapshot(att)
    q = next((item["q"] for item in snapshot if item["qid"] == body.question_id), None)
    if q is None:
        raise HTTPException(404, "Frage nicht gefunden")
    state = ls.attempt_state(att)
    key = str(body.question_id)
    if body.question_id in state["checked"]:
        raise HTTPException(409, "Diese Frage ist schon beantwortet und lässt sich nicht mehr ändern")
    try:
        answer = lx.clean_answer(q, body.answer)
    except lx.LearningError as exc:
        raise _bad(exc) from None
    if answer is None:
        state["answers"].pop(key, None)
    else:
        state["answers"][key] = answer
    out: dict[str, Any] = {"saved": True}
    if test.immediate_feedback and answer is not None:
        state["checked"].append(body.question_id)
        out["checked"] = _checked_view(q, answer)
    ls.save_attempt_state(att, state)
    db.commit()
    return out


@router.post("/channels/{channel_id}/selftests/{test_id}/attempts/{attempt_id}/finish")
def finish(channel_id: int, test_id: int, attempt_id: int, request: Request, user: AuthUser = Depends(current_user),
           db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, write=True)
    test = _get_test(db, ctx, test_id)
    att = _own_attempt(db, ctx, test, attempt_id)
    if att.finished_at is None:
        ls.finish_attempt(att)
        db.flush()
        ls.publish_grades(db, test)
        audit(db, user, "selftest.finish", f"learning_selftest:{test.id}", {"attempt": att.number},
              ip=client_ip(request))
        db.commit()
    return _attempt_out(db, test, att)


# =========================================================================== Auswertung (Lehrende)
def channel_students(db: Session, ctx: Ctx) -> list[tuple[int, str]]:
    """Teilnehmende Schüler/innen mit Konto: [(Konto-ID, Name)], nach Name sortiert."""
    ids: dict[int, str] = {}
    sids = chx.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "") if ctx.spec is not None else []
    if sids:
        for uid, dn, un in db.execute(select(User.id, User.display_name, User.username).where(
                User.role == "schueler", User.active.is_(True), User.student_id.in_(list(sids)))):
            ids[uid] = dn or un
    excluded = set()
    for uid, role, dn, un in db.execute(select(ChannelExtraMember.user_id, ChannelExtraMember.role, User.display_name,
                                               User.username).join(User, User.id == ChannelExtraMember.user_id)
                                        .where(ChannelExtraMember.channel_id == ctx.ch.id)):
        if role == "student":
            ids[uid] = dn or un
        elif role == "excluded":
            excluded.add(uid)
    return sorted(((uid, name) for uid, name in ids.items() if uid not in excluded), key=lambda t: t[1].casefold())


def _results_access(db: Session, user: AuthUser, channel_id: int, test_id: int) -> tuple[Ctx, LearningSelftest]:
    ctx = _ctx(db, user, channel_id, manage=True)
    test = _get_test(db, ctx, test_id)
    ctx.need_edit(test.created_by)
    return ctx, test


def _results(db: Session, ctx: Ctx, test: LearningSelftest) -> dict:
    students = channel_students(db, ctx)
    attempts = ls.attempts_by_user(db, test.id, [uid for uid, _n in students])
    db.commit()
    max_points = ls.test_max_points(db, test)
    q_titles: dict[int, dict] = {}
    q_stats: dict[int, dict] = {}
    rows = []
    for uid, name in students:
        mine = attempts.get(uid, [])
        best = ls.best_attempt(mine)
        per_q: dict[str, float] = {}
        if best is not None:
            for item in ls.attempt_snapshot(best):
                q_titles.setdefault(item["qid"], {"qid": item["qid"], "title": lx.question_title(item["q"]),
                                                  "type": item["q"]["type"], "max": item["q"].get("points", 1)})
            for r in ls.read_json(best, "result", []):
                per_q[str(r["qid"])] = r["fraction"]
        for a in mine:
            if a.finished_at is None:
                continue
            for r in ls.read_json(a, "result", []):
                st = q_stats.setdefault(r["qid"], {"n": 0, "sum": 0.0, "correct": 0})
                st["n"] += 1
                st["sum"] += r["fraction"]
                st["correct"] += 1 if r["correct"] else 0
        rows.append({"user_id": uid, "name": name, "attempts": len(mine),
                     "finished": sum(1 for a in mine if a.finished_at is not None),
                     "running": any(a.finished_at is None for a in mine),
                     "best_points": best.points if best else None, "best_percent": best.percent if best else None,
                     "max_points": best.max_points if best else None, "passed": ls.passed(test, best),
                     "last_at": iso(max((a.finished_at or a.started_at) for a in mine)) if mine else None,
                     "per_question": per_q,
                     "attempt_ids": [a.id for a in mine]})
    questions = []
    for qid, info in q_titles.items():
        st = q_stats.get(qid, {"n": 0, "sum": 0.0, "correct": 0})
        questions.append({**info, "attempts": st["n"], "mean": round(st["sum"] / st["n"], 3) if st["n"] else None,
                          "correct_share": round(st["correct"] / st["n"], 3) if st["n"] else None})
    return {"test": _test_config(test), "max_points": max_points, "students": rows, "questions": questions}


@router.get("/channels/{channel_id}/selftests/{test_id}/results")
def results(channel_id: int, test_id: int, user: AuthUser = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    ctx, test = _results_access(db, user, channel_id, test_id)
    return _results(db, ctx, test)


@router.get("/channels/{channel_id}/selftests/{test_id}/results.csv")
def results_csv(channel_id: int, test_id: int, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> Response:
    ctx, test = _results_access(db, user, channel_id, test_id)
    data = _results(db, ctx, test)
    qs = data["questions"]
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    writer.writerow(["Name", "Versuche", "Bester Versuch (Punkte)", "Mögliche Punkte", "Prozent", "Bestanden"]
                    + [fx.csv_cell(f"{q['title']} (Anteil)") for q in qs])
    for r in data["students"]:
        writer.writerow([fx.csv_cell(r["name"]), r["attempts"], _num(r["best_points"]), _num(r["max_points"]),
                         _num(r["best_percent"]), {True: "ja", False: "nein", None: ""}[r["passed"]]]
                        + [_num(r["per_question"].get(str(q["qid"]))) for q in qs])
    audit(db, user, "selftest.export", f"learning_selftest:{test.id}", {"rows": len(data["students"])},
          ip=client_ip(request))
    db.commit()
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="selbsttest-%d.csv"' % test.id})


def _num(value: Any) -> str:
    return "" if value is None else str(value).replace(".", ",")


@router.get("/channels/{channel_id}/selftests/{test_id}/grades")
def grades(channel_id: int, test_id: int, user: AuthUser = Depends(current_user),
           db: Session = Depends(get_db)) -> dict:
    """Punkte je Schüler/in (bester Versuch) für das Notenbuch: Elementtyp ``selftest``, Kennung = Test, Punkte."""
    ctx, test = _results_access(db, user, channel_id, test_id)
    students = dict(channel_students(db, ctx))
    out = []
    for g in ls.selftest_grades(db, test.id, list(students)):
        out.append({**g, "name": students.get(g["user_id"], "")})
    db.commit()
    return {"element_type": "selftest", "element_id": test.id, "max_points": ls.test_max_points(db, test),
            "grades": out}


@router.get("/channels/{channel_id}/learning/elements")
def elements(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Abstimmungen, Umfragen und Selbsttests des Kursraums (für Notenbuch und Abschlussbedingungen)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    return {"elements": ls.list_elements(db, ctx.ch.id)}
