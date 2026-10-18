"""Abstimmungen im Kursraum und im Chat (Doku: docs/LERNAKTIVITAETEN.md).

Kursraum (Rechte wie im Kursraum: Lehrende stellen ein, Teilnehmende und Lehrende stimmen ab, Eltern/Aufsicht lesen):

* ``GET/POST /channels/{id}/polls`` · ``PUT /channels/{id}/polls/{pid}/vote`` ``{choices:[Index]}`` ·
  ``POST /channels/{id}/polls/{pid}/close`` · ``DELETE /channels/{id}/polls/{pid}``

Chat (Ende-zu-Ende): Frage und Antworten stehen verschlüsselt in der Nachricht (``POST /chats/{id}/messages`` mit
``poll``); der Server kennt nur Einstellungen, Zahl der Antworten und Stimmen:

* ``PUT /chats/{id}/messages/{mid}/vote`` · ``POST /chats/{id}/messages/{mid}/poll/close``

Anonym heißt: Es wird nur gespeichert, **dass** jemand abgestimmt hat, und ein Zähler je Antwort – nicht, wer was
gewählt hat (daher lässt sich eine anonyme Stimme nicht ändern). Namentliche Stimmen können nachträglich geändert werden.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager import learning as lx
from schulmanager.server import learning_service as ls
from schulmanager.server.learning_service import ChatPollMeta, chat_poll_states, new_poll  # noqa: F401
from schulmanager.server.audit import audit
from schulmanager.server.learning_notify import announce
from schulmanager.server.db import get_db, utcnow
from schulmanager.server.deps import AuthUser, client_ip, current_user, require
from schulmanager.server.feature_models.chats import ChatMessage
from schulmanager.server.feature_models.learning import LearningPoll

from .features_channels import Ctx, _ctx, _notify, _to_utc
from .features_chats import _member_ids, _membership, _names, _publish
from .features_messages import USE, _fail

router = APIRouter(tags=["Lernaktivitäten"])


# =========================================================================== Eingaben
class PollIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=300)
    options: list[str] = Field(max_length=lx.MAX_POLL_OPTIONS + 5)
    multiple: bool = False
    max_choices: Optional[int] = Field(None, ge=1, le=lx.MAX_POLL_OPTIONS)
    anonymous: bool = False
    results: Literal["live", "after_vote", "after_end"] = "live"
    ends_at: Optional[datetime] = None


class VoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choices: list[int] = Field(max_length=lx.MAX_POLL_OPTIONS)


def _bad(exc: Exception) -> HTTPException:
    return HTTPException(422, str(exc))


# =========================================================================== Kursraum
def _poll_out(db: Session, ctx: Ctx, poll: LearningPoll) -> dict:
    question, options = ls.poll_texts(poll)
    can_vote = ctx.role in ("student", "teacher") and not ctx.ch.archived
    names = ls.poll_names(db, poll) if not poll.anonymous else None
    state = ls.poll_state(db, poll, ctx.user.id, staff=ctx.staff_view, can_vote=can_vote, names=names,
                          show_names=not ctx.parent)
    state.update(question=question, options=options, editable=ctx.teacher and ctx.may_edit(poll.created_by))
    return state


def _get_poll(db: Session, ctx: Ctx, poll_id: int) -> LearningPoll:
    poll = db.get(LearningPoll, poll_id)
    if poll is None or poll.channel_id != ctx.ch.id:
        raise HTTPException(404, "Abstimmung nicht gefunden")
    return poll


@router.get("/channels/{channel_id}/polls")
def list_polls(channel_id: int, student_id: Optional[str] = None, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, child=student_id)
    rows = list(db.scalars(select(LearningPoll).where(LearningPoll.channel_id == ctx.ch.id)
                           .order_by(LearningPoll.id.desc())))
    return {"polls": [_poll_out(db, ctx, p) for p in rows],
            "can_create": ctx.teacher and not ctx.ch.archived}


@router.post("/channels/{channel_id}/polls", status_code=201)
def create_poll(channel_id: int, body: PollIn, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    try:
        norm = lx.normalize_poll(body.model_dump())
        poll = new_poll(norm, user_id=user.id, ends_at=_to_utc(body.ends_at, "das Ende der Abstimmung"))
    except lx.LearningError as exc:
        raise _bad(exc) from None
    count = db.scalar(select(func.count()).select_from(LearningPoll).where(
        LearningPoll.channel_id == ctx.ch.id))
    if (count or 0) >= 300:
        raise HTTPException(409, "Zu viele Abstimmungen in diesem Kursraum – bitte alte löschen")
    poll.channel_id = ctx.ch.id
    db.add(poll)
    db.flush()
    poll.write_text("question", norm["question"])
    ls.write_json(poll, "options", norm["options"])
    audit(db, user, "poll.create", f"learning_poll:{poll.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    announce(db, ctx, "poll", poll.id)
    db.commit()
    _notify(db, ctx)
    return _poll_out(db, ctx, poll)


@router.put("/channels/{channel_id}/polls/{poll_id}/vote")
def vote(channel_id: int, poll_id: int, body: VoteIn, request: Request, user: AuthUser = Depends(current_user),
         db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, write=True)
    poll = _get_poll(db, ctx, poll_id)
    if ls.poll_closed(poll):
        raise HTTPException(409, "Die Abstimmung ist beendet")
    try:
        ls.cast_vote(db, poll, user.id, body.choices)
    except ls.AlreadyVoted:
        raise HTTPException(409, "Sie haben bereits abgestimmt – bei anonymen Abstimmungen lässt sich die Stimme "
                            "nicht ändern") from None
    except lx.LearningError as exc:
        raise _bad(exc) from None
    audit(db, user, "poll.vote", f"learning_poll:{poll.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _poll_out(db, ctx, poll)


@router.post("/channels/{channel_id}/polls/{poll_id}/close")
def close_poll(channel_id: int, poll_id: int, request: Request, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    poll = _get_poll(db, ctx, poll_id)
    ctx.need_edit(poll.created_by)
    if not ls.poll_closed(poll):
        poll.closed_at = utcnow()
        audit(db, user, "poll.close", f"learning_poll:{poll.id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _poll_out(db, ctx, poll)


@router.delete("/channels/{channel_id}/polls/{poll_id}")
def delete_poll(channel_id: int, poll_id: int, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    poll = _get_poll(db, ctx, poll_id)
    ctx.need_edit(poll.created_by)
    db.delete(poll)
    audit(db, user, "poll.delete", f"learning_poll:{poll_id}", {"channel_id": ctx.ch.id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"deleted": poll_id}


# =========================================================================== Chat
def _chat_poll(db: Session, chat_id: int, message_id: int) -> LearningPoll:
    msg = db.get(ChatMessage, message_id)
    poll = db.scalar(select(LearningPoll).where(LearningPoll.chat_message_id == message_id))
    if msg is None or msg.chat_id != chat_id or msg.deleted_at is not None or poll is None:
        raise _fail(404, "not_found", "Umfrage nicht gefunden.")
    return poll


@router.put("/chats/{chat_id}/messages/{message_id}/vote")
def chat_vote(chat_id: int, message_id: int, body: VoteIn, request: Request, user: AuthUser = Depends(require(USE)),
              db: Session = Depends(get_db)) -> dict:
    _membership(db, chat_id, user)
    poll = _chat_poll(db, chat_id, message_id)
    if ls.poll_closed(poll):
        raise _fail(409, "poll_closed", "Die Umfrage ist beendet.")
    try:
        ls.cast_vote(db, poll, user.id, body.choices)
    except ls.AlreadyVoted:
        raise _fail(409, "already_voted", "Sie haben bereits abgestimmt – bei anonymen Umfragen lässt sich die "
                    "Stimme nicht ändern.") from None
    except lx.LearningError as exc:
        raise _bad(exc) from None
    audit(db, user, "poll.vote", f"learning_poll:{poll.id}", {"chat_id": chat_id}, ip=client_ip(request))
    db.commit()
    _publish(_member_ids(db, chat_id), chat_id)
    return chat_poll_states(db, [message_id], user.id, lambda ids: _names(db, ids))[message_id]


@router.post("/chats/{chat_id}/messages/{message_id}/poll/close")
def chat_close(chat_id: int, message_id: int, request: Request, user: AuthUser = Depends(require(USE)),
               db: Session = Depends(get_db)) -> dict:
    _chat, mem = _membership(db, chat_id, user)
    poll = _chat_poll(db, chat_id, message_id)
    if poll.created_by != user.id and not mem.admin:
        raise _fail(403, "forbidden", "Nur wer die Umfrage gestellt hat (oder ein Admin) kann sie beenden.")
    if not ls.poll_closed(poll):
        poll.closed_at = utcnow()
        audit(db, user, "poll.close", f"learning_poll:{poll.id}", {"chat_id": chat_id}, ip=client_ip(request))
    db.commit()
    _publish(_member_ids(db, chat_id), chat_id)
    return chat_poll_states(db, [message_id], user.id, lambda ids: _names(db, ids))[message_id]

