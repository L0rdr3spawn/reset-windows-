"""Umfragen (Feedback-Fragebögen) im Kursraum (Doku: docs/LERNAKTIVITAETEN.md).

Die Fragen nutzen dieselben Feldarten und Prüfungen wie der Formular-Baukasten (``schulmanager/forms.py``): Auswahl,
Mehrfachauswahl, Ja/Nein, Skala 1–5, kurzer/langer Text, Zahl. Anders als Formulare gibt es keinen Genehmigungsablauf,
dafür eine Auswertung (Zählungen, Mittelwert, Texte) und den CSV-Export.

* ``GET/POST /channels/{id}/surveys`` · ``GET/PATCH/DELETE /channels/{id}/surveys/{sid}``
* ``POST /channels/{id}/surveys/{sid}/respond`` ``{answers}`` – Teilnehmende, einmal je Person
* ``GET /channels/{id}/surveys/{sid}/results`` · ``GET …/export.csv`` – Lehrende (Klassenräume: wer die Umfrage
  angelegt hat bzw. Klassenleitung); Teilnehmende nur, wenn die Umfrage beendet ist und die Ergebnisse freigegeben sind

Anonyme Umfragen speichern die Antworten ohne Konto und nur mit Tagesdatum; getrennt davon steht, **dass** jemand
geantwortet hat. In der Auswertung erscheinen anonyme Antworten in zufälliger Reihenfolge.
"""
from __future__ import annotations

import csv
import io
import random
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from schulmanager import forms as fx
from schulmanager import learning as lx
from schulmanager.server import learning_service as ls
from schulmanager.server.audit import audit
from schulmanager.server.learning_notify import announce
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.feature_models.learning import (LearningSurvey, LearningSurveyParticipant,
                                                         LearningSurveyResponse)

from .features_channels import Ctx, _ctx, _notify, _to_utc, _user_names

router = APIRouter(tags=["Lernaktivitäten"])

MAX_SURVEYS = 200
MAX_QUESTIONS = 30


class SurveyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    intro: str = Field("", max_length=1500)
    fields: list[dict[str, Any]] = Field(max_length=MAX_QUESTIONS + 5)
    anonymous: bool = False
    status: str = Field("offen", pattern="^(entwurf|offen)$")
    closes_at: Optional[datetime] = None
    results_to_students: bool = False


class SurveyPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    intro: Optional[str] = Field(None, max_length=1500)
    fields: Optional[list[dict[str, Any]]] = Field(None, max_length=MAX_QUESTIONS + 5)
    anonymous: Optional[bool] = None
    status: Optional[str] = Field(None, pattern="^(entwurf|offen|geschlossen)$")
    closes_at: Optional[datetime] = None
    clear_closes_at: bool = False
    results_to_students: Optional[bool] = None


class RespondIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: dict[str, Any] = Field(default_factory=dict)


def _bad(exc: Exception) -> HTTPException:
    return HTTPException(422, str(exc))


def _clean_fields(raw: Any) -> list[dict]:
    try:
        return fx.normalize_fields(raw, allowed=lx.SURVEY_FIELD_TYPES, limit=MAX_QUESTIONS)
    except fx.FormError as exc:
        raise _bad(exc) from None


def _effective(sv: LearningSurvey) -> str:
    return "geschlossen" if sv.status == "offen" and not ls.survey_open(sv) else sv.status


def _get(db: Session, ctx: Ctx, survey_id: int) -> LearningSurvey:
    sv = db.get(LearningSurvey, survey_id)
    if sv is None or sv.channel_id != ctx.ch.id:
        raise HTTPException(404, "Umfrage nicht gefunden")
    return sv


def _can_see(ctx: Ctx, sv: LearningSurvey) -> bool:
    if ctx.teacher:
        return True
    return ctx.student and sv.status != "entwurf"


def _survey_out(db: Session, ctx: Ctx, sv: LearningSurvey, *, detail: bool = False) -> dict:
    editable = ctx.teacher and ctx.may_edit(sv.created_by)
    count = ls.survey_response_count(db, sv.id) if editable else None
    out: dict[str, Any] = {
        "id": sv.id, "title": sv.title, "anonymous": sv.anonymous, "status": sv.status, "state": _effective(sv),
        "closes_at": iso(sv.closes_at), "results_to_students": sv.results_to_students,
        "question_count": len(sv.fields or []), "done": ls.survey_done(db, sv.id, ctx.user.id) if ctx.student else False,
        "editable": editable, "response_count": count, "created_by": sv.created_by, "created_at": iso(sv.created_at),
        "results_visible": editable or (ctx.student and sv.results_to_students and _effective(sv) == "geschlossen"),
    }
    if detail:
        out["intro"] = sv.read_text("intro")
        out["fields"] = sv.fields or []
    return out


@router.get("/channels/{channel_id}/surveys")
def list_surveys(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id)
    if not (ctx.teacher or ctx.student):
        return {"surveys": [], "can_create": False}
    rows = [s for s in db.scalars(select(LearningSurvey).where(LearningSurvey.channel_id == ctx.ch.id)
                                  .order_by(LearningSurvey.id.desc())) if _can_see(ctx, s)]
    return {"surveys": [_survey_out(db, ctx, s) for s in rows], "can_create": ctx.teacher and not ctx.ch.archived}


@router.post("/channels/{channel_id}/surveys", status_code=201)
def create_survey(channel_id: int, body: SurveyIn, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    if int(db.scalar(select(func.count()).select_from(LearningSurvey).where(
            LearningSurvey.channel_id == ctx.ch.id)) or 0) >= MAX_SURVEYS:
        raise HTTPException(409, "Zu viele Umfragen in diesem Kursraum – bitte alte löschen")
    sv = LearningSurvey(channel_id=ctx.ch.id, title=fx.clean_text(body.title, 200), fields=_clean_fields(body.fields),
                        anonymous=body.anonymous, status=body.status,
                        closes_at=_to_utc(body.closes_at, "das Ende der Umfrage"),
                        results_to_students=body.results_to_students, created_by=user.id, created_at=utcnow())
    if not sv.title:
        raise HTTPException(422, "Bitte einen Titel eingeben")
    db.add(sv)
    db.flush()
    sv.write_text("intro", fx.clean_text(body.intro, 1500, multiline=True))
    audit(db, user, "survey.create", f"learning_survey:{sv.id}", {"channel_id": ctx.ch.id, "anonymous": sv.anonymous},
          ip=client_ip(request))
    if sv.status == "offen":
        announce(db, ctx, "survey", sv.id)
    db.commit()
    _notify(db, ctx)
    return _survey_out(db, ctx, sv, detail=True)


@router.get("/channels/{channel_id}/surveys/{survey_id}")
def get_survey(channel_id: int, survey_id: int, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id)
    sv = _get(db, ctx, survey_id)
    if not _can_see(ctx, sv):
        raise HTTPException(404, "Umfrage nicht gefunden")
    return _survey_out(db, ctx, sv, detail=True)


@router.patch("/channels/{channel_id}/surveys/{survey_id}")
def patch_survey(channel_id: int, survey_id: int, body: SurveyPatch, request: Request,
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    sv = _get(db, ctx, survey_id)
    ctx.need_edit(sv.created_by)
    has_answers = ls.survey_response_count(db, sv.id) > 0
    was = sv.status
    if body.fields is not None or body.anonymous is not None and body.anonymous != sv.anonymous:
        if has_answers:
            raise HTTPException(409, "Es gibt schon Antworten – Fragen und Anonymität lassen sich nicht mehr ändern. "
                                "Beenden Sie die Umfrage und legen Sie bei Bedarf eine neue an.")
    if body.fields is not None:
        sv.fields = _clean_fields(body.fields)
    if body.anonymous is not None:
        sv.anonymous = body.anonymous
    if body.title is not None:
        sv.title = fx.clean_text(body.title, 200) or sv.title
    if body.intro is not None:
        sv.write_text("intro", fx.clean_text(body.intro, 1500, multiline=True))
    if body.status is not None:
        if body.status == "entwurf" and has_answers:
            raise HTTPException(409, "Es gibt schon Antworten – die Umfrage kann nicht zurück in den Entwurf")
        sv.status = body.status
    if body.clear_closes_at:
        sv.closes_at = None
    elif body.closes_at is not None:
        sv.closes_at = _to_utc(body.closes_at, "das Ende der Umfrage")
    if body.results_to_students is not None:
        sv.results_to_students = body.results_to_students
    sv.updated_at = utcnow()
    if body.status == "offen" and was != "offen":
        announce(db, ctx, "survey", sv.id)
    audit(db, user, "survey.update", f"learning_survey:{sv.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _survey_out(db, ctx, sv, detail=True)


@router.delete("/channels/{channel_id}/surveys/{survey_id}")
def delete_survey(channel_id: int, survey_id: int, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    sv = _get(db, ctx, survey_id)
    ctx.need_edit(sv.created_by)
    db.delete(sv)
    audit(db, user, "survey.delete", f"learning_survey:{survey_id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"deleted": survey_id}


@router.post("/channels/{channel_id}/surveys/{survey_id}/respond", status_code=201)
def respond(channel_id: int, survey_id: int, body: RespondIn, request: Request,
            user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, write=True)
    if not ctx.student:
        raise HTTPException(403, "Nur Teilnehmende beantworten Umfragen")
    sv = _get(db, ctx, survey_id)
    if not _can_see(ctx, sv):
        raise HTTPException(404, "Umfrage nicht gefunden")
    if not ls.survey_open(sv):
        raise HTTPException(409, "Die Umfrage ist nicht (mehr) offen")
    if ls.survey_done(db, sv.id, user.id):
        raise HTTPException(409, "Sie haben diese Umfrage schon beantwortet")
    try:
        answers = fx.clean_answers({"fields": sv.fields}, body.answers, student_id=None, periods=0, today=date.today())
    except fx.FormError as exc:
        raise _bad(exc) from None
    db.add(LearningSurveyParticipant(survey_id=sv.id, user_id=user.id))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Sie haben diese Umfrage schon beantwortet") from None
    stamp = utcnow()
    row = LearningSurveyResponse(survey_id=sv.id, user_id=None if sv.anonymous else user.id,
                                 created_at=stamp.replace(hour=0, minute=0, second=0, microsecond=0)
                                 if sv.anonymous else stamp)
    db.add(row)
    db.flush()
    ls.write_json(row, "answers", answers)
    audit(db, user, "survey.respond", f"learning_survey:{sv.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"done": True}


def _results_ctx(db: Session, user: AuthUser, channel_id: int, survey_id: int) -> tuple[Ctx, LearningSurvey]:
    ctx = _ctx(db, user, channel_id)
    sv = _get(db, ctx, survey_id)
    if ctx.teacher and ctx.may_edit(sv.created_by):
        return ctx, sv
    if ctx.student and sv.results_to_students and _effective(sv) == "geschlossen":
        return ctx, sv
    raise HTTPException(403, "Die Ergebnisse dieser Umfrage sind für Sie nicht freigegeben")


def _respondent_rows(db: Session, sv: LearningSurvey) -> list[dict]:
    answers = ls.survey_answers(db, sv)
    names = _user_names(db, [uid for uid, _at, _a in answers]) if not sv.anonymous else {}
    rows = [{"name": names.get(uid, "") if uid else "", "at": at, "answers": data} for uid, at, data in answers]
    if sv.anonymous:
        random.SystemRandom().shuffle(rows)
    return rows


@router.get("/channels/{channel_id}/surveys/{survey_id}/results")
def results(channel_id: int, survey_id: int, user: AuthUser = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    ctx, sv = _results_ctx(db, user, channel_id, survey_id)
    rows = _respondent_rows(db, sv)
    teacher = ctx.teacher
    members = None
    if teacher:
        members = _member_count(db, ctx)
    return {
        "survey": _survey_out(db, ctx, sv, detail=True), "response_count": len(rows), "member_count": members,
        "items": lx.aggregate_survey(sv.fields or [], [r["answers"] for r in rows]),
        # Einzelantworten nur für Lehrende; bei anonymen Umfragen ohne Namen und in zufälliger Reihenfolge
        "responses": [{"name": r["name"], "at": iso(r["at"]), "answers": r["answers"]} for r in rows]
        if teacher else [],
    }


def _member_count(db: Session, ctx: Ctx) -> int:
    from .features_channels import _member_user_ids
    ids = _member_user_ids(db, ctx.ch, ctx.spec, ctx.school)
    from schulmanager.server.db_models import User
    return int(db.scalar(select(func.count()).select_from(User).where(User.id.in_(list(ids)), User.role == "schueler"))
               or 0) if ids else 0


@router.get("/channels/{channel_id}/surveys/{survey_id}/export.csv")
def export_csv(channel_id: int, survey_id: int, request: Request, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> Response:
    ctx = _ctx(db, user, channel_id, manage=True)
    sv = _get(db, ctx, survey_id)
    ctx.need_edit(sv.created_by)
    rows = _respondent_rows(db, sv)
    fields = sv.fields or []
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    head = ([] if sv.anonymous else ["Name"]) + ["Datum"] + [fx.csv_cell(f["label"]) for f in fields]
    writer.writerow(head)
    for r in rows:
        cells = [] if sv.anonymous else [fx.csv_cell(r["name"])]
        cells.append(r["at"].strftime("%d.%m.%Y"))
        for f in fields:
            cells.append(fx.csv_cell(fx.display_value(f, r["answers"].get(f["id"]))))
        writer.writerow(cells)
    audit(db, user, "survey.export", f"learning_survey:{sv.id}", {"channel_id": ctx.ch.id, "rows": len(rows)},
          ip=client_ip(request))
    db.commit()
    data = "﻿" + buf.getvalue()
    return Response(data, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="umfrage-%d.csv"' % sv.id})
