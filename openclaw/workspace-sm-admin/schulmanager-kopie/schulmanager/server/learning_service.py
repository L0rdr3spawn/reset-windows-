"""Dienstfunktionen der Lernaktivitäten (Abstimmung, Umfrage, Selbsttest) – ohne HTTP, von den Routen und von
anderen Bereichen nutzbar (Doku: docs/LERNAKTIVITAETEN.md).

**Anbindung für Notenbuch und Abschlussbedingungen**

* Elementtyp ``selftest`` / ``survey`` / ``poll`` + Kennung (``learning_selftests.id`` …) benennen ein Element.
* :func:`element_status` – Zustand für ein Konto: ``{"done", "points", "max_points", "percent", "passed"}``.
* :func:`selftest_grades` – Punkte aller Teilnehmenden eines Selbsttests (bester Versuch) für das Notenbuch.
* :func:`selftest_done` / :func:`survey_done` / :func:`poll_done` – Abschlussbedingung („erledigt“).
* :func:`list_elements` – Elemente eines Kursraums (zum Auswählen).
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import Any, Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field
from typing import Callable, Literal
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from schulmanager import learning as lx
from schulmanager.server.db import iso, utcnow
from schulmanager.server.db_models import User
from schulmanager.server.feature_models.learning import (LearningAttempt, LearningPoll, LearningPollParticipant,
                                                         LearningPollTally, LearningPollVote, LearningQuestion,
                                                         LearningSelftest, LearningSurvey, LearningSurveyParticipant,
                                                         LearningSurveyResponse)

ELEMENT_TYPES = ("selftest", "survey", "poll")
GRACE = timedelta(seconds=8)      # Toleranz für Netz-/Uhrabweichung beim Zeitlimit


# ============================================================================ JSON in verschlüsselten Feldern
def read_json(row: Any, field: str, default: Any) -> Any:
    raw = row.read_text(field)
    if not raw or raw == "[nicht lesbar]":
        return default
    try:
        return json.loads(raw)
    except ValueError:
        return default


def write_json(row: Any, field: str, value: Any) -> None:
    row.write_text(field, json.dumps(value, ensure_ascii=False, separators=(",", ":")))


# ============================================================================ Abstimmung
def poll_closed(poll: LearningPoll, now: Optional[datetime] = None) -> bool:
    now = now or utcnow()
    return poll.closed_at is not None or (poll.ends_at is not None and poll.ends_at <= now)


def poll_texts(poll: LearningPoll) -> tuple[str, list[str]]:
    """Frage und Antworten (nur Kursraum-Abstimmungen; im Chat liegen sie in der verschlüsselten Nachricht)."""
    if poll.channel_id is None:
        return "", []
    return poll.read_text("question"), read_json(poll, "options", [])


def poll_counts(db: Session, poll: LearningPoll) -> list[int]:
    counts = [0] * poll.option_count
    if poll.anonymous:
        for idx, n in db.execute(select(LearningPollTally.option_index, LearningPollTally.count)
                                 .where(LearningPollTally.poll_id == poll.id)):
            if 0 <= idx < len(counts):
                counts[idx] = int(n)
    else:
        for idx, n in db.execute(select(LearningPollVote.option_index, func.count())
                                 .where(LearningPollVote.poll_id == poll.id).group_by(LearningPollVote.option_index)):
            if 0 <= idx < len(counts):
                counts[idx] = int(n)
    return counts


def poll_state(db: Session, poll: LearningPoll, user_id: int, *, staff: bool = False, can_vote: bool = True,
               names: Optional[dict[int, str]] = None, show_names: bool = True) -> dict:
    """Zustand einer Abstimmung für ein Konto. ``staff`` sieht das Ergebnis immer; ``can_vote=False`` (Eltern,
    Aufsicht) = nur lesen. ``names``: Namen der Konten, falls Stimmen mit Namen gezeigt werden dürfen."""
    now = utcnow()
    closed = poll_closed(poll, now)
    voted = db.scalar(select(LearningPollParticipant.id).where(LearningPollParticipant.poll_id == poll.id,
                                                              LearningPollParticipant.user_id == user_id)) is not None
    visible = lx.results_visible(poll.results, voted=voted, closed=closed, staff=staff)
    mine: list[int] = []
    if voted and not poll.anonymous:
        mine = sorted(db.scalars(select(LearningPollVote.option_index).where(
            LearningPollVote.poll_id == poll.id, LearningPollVote.user_id == user_id)))
    out: dict[str, Any] = {
        "id": poll.id, "option_count": poll.option_count, "multiple": poll.multiple, "max_choices": poll.max_choices,
        "anonymous": poll.anonymous, "results": poll.results, "ends_at": iso(poll.ends_at),
        "closed": closed, "closed_at": iso(poll.closed_at), "voted": voted, "mine": mine,
        "can_vote": bool(can_vote and not closed and not (voted and poll.anonymous)),
        "created_by": poll.created_by, "created_at": iso(poll.created_at),
        "counts": None, "total": None, "voters": None, "show_results": visible,
    }
    if visible:
        out["counts"] = poll_counts(db, poll)
        out["total"] = int(db.scalar(select(func.count()).select_from(LearningPollParticipant).where(
            LearningPollParticipant.poll_id == poll.id)) or 0)
        if not poll.anonymous and show_names and names is not None:
            voters: dict[str, list[str]] = {}
            for uid, idx in db.execute(select(LearningPollVote.user_id, LearningPollVote.option_index)
                                       .where(LearningPollVote.poll_id == poll.id)
                                       .order_by(LearningPollVote.option_index, LearningPollVote.id)):
                voters.setdefault(str(idx), []).append(names.get(uid, "?"))
            out["voters"] = voters
    return out


class ChatPollMeta(BaseModel):
    """Einstellungen einer Chat-Abstimmung (Texte stehen nur in der verschlüsselten Nachricht)."""
    model_config = ConfigDict(extra="forbid")
    option_count: int = Field(ge=lx.MIN_POLL_OPTIONS, le=lx.MAX_POLL_OPTIONS)
    multiple: bool = False
    max_choices: Optional[int] = Field(None, ge=1, le=lx.MAX_POLL_OPTIONS)
    anonymous: bool = False
    results: Literal["live", "after_vote", "after_end"] = "live"
    ends_at: Optional[datetime] = None


def to_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Zeitpunkt → naive UTC (ohne Zeitzone = Ortszeit des Servers)."""
    if value is None:
        return None
    from schulmanager.channels import local_to_utc
    from datetime import timezone
    dt = value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else local_to_utc(value)
    if not 2000 <= dt.year <= 2100:
        raise lx.LearningError("Ungültiger Zeitpunkt")
    return dt.replace(microsecond=0)


def new_poll(norm: dict, *, user_id: int, ends_at: Optional[datetime]) -> LearningPoll:
    """Neue Abstimmung aus geprüften Einstellungen (ohne Commit; Ende muss in der Zukunft liegen)."""
    if ends_at is not None and ends_at <= utcnow():
        raise lx.LearningError("Das Ende der Abstimmung muss in der Zukunft liegen")
    return LearningPoll(option_count=norm["option_count"], multiple=norm["multiple"], max_choices=norm["max_choices"],
                        anonymous=norm["anonymous"], results=norm["results"], ends_at=ends_at, created_by=user_id,
                        created_at=utcnow())


def chat_poll_row(db: Session, chat_id: int, message_id: int, meta: ChatPollMeta, user_id: int) -> LearningPoll:
    """Abstimmung zu einer Chat-Nachricht anlegen (ohne Commit; ``LearningError`` bei ungültigen Angaben)."""
    norm = lx.normalize_poll(meta.model_dump(), with_texts=False)
    poll = new_poll(norm, user_id=user_id, ends_at=to_utc(meta.ends_at))
    poll.chat_id, poll.chat_message_id = chat_id, message_id
    db.add(poll)
    return poll


def chat_poll_states(db: Session, message_ids: list[int], user_id: int,
                     names_of: Callable[[list[int]], dict[int, str]]) -> dict[int, dict]:
    """Zustand der Abstimmungen für die Nachrichten einer Seite (``names_of`` liefert Kontonamen)."""
    polls = chat_polls(db, message_ids)
    out: dict[int, dict] = {}
    voter_names: dict[int, str] = {}
    for mid, poll in polls.items():
        names: Optional[dict[int, str]] = None
        if not poll.anonymous:
            missing = [i for i in poll_voter_ids(db, poll.id) if i not in voter_names]
            if missing:
                voter_names.update(names_of(missing))
            names = voter_names
        out[mid] = poll_state(db, poll, user_id, staff=poll.created_by == user_id, names=names)
    return out


def poll_voter_ids(db: Session, poll_id: int) -> list[int]:
    return list(db.scalars(select(LearningPollVote.user_id).where(LearningPollVote.poll_id == poll_id).distinct()))


def poll_names(db: Session, poll: LearningPoll) -> dict[int, str]:
    if poll.anonymous:
        return {}
    ids = poll_voter_ids(db, poll.id)
    if not ids:
        return {}
    return {uid: dn or un for uid, dn, un in db.execute(
        select(User.id, User.display_name, User.username).where(User.id.in_(ids)))}


class AlreadyVoted(Exception):
    """Anonyme Stimme lässt sich nicht ändern."""


def cast_vote(db: Session, poll: LearningPoll, user_id: int, choices: Any) -> list[int]:
    """Stimme abgeben (ohne Commit). Namentlich: ersetzt die frühere Stimme; anonym: nur einmal."""
    picked = lx.clean_choices(choices, poll.option_count, poll.multiple, poll.max_choices)
    if poll.anonymous:
        if db.scalar(select(LearningPollParticipant.id).where(LearningPollParticipant.poll_id == poll.id,
                                                             LearningPollParticipant.user_id == user_id)):
            raise AlreadyVoted
        db.add(LearningPollParticipant(poll_id=poll.id, user_id=user_id))
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise AlreadyVoted from None
        for idx in picked:
            row = db.scalar(select(LearningPollTally).where(LearningPollTally.poll_id == poll.id,
                                                            LearningPollTally.option_index == idx))
            if row is None:
                db.add(LearningPollTally(poll_id=poll.id, option_index=idx, count=1))
            else:
                row.count += 1
        return picked
    db.execute(delete(LearningPollVote).where(LearningPollVote.poll_id == poll.id,
                                              LearningPollVote.user_id == user_id))
    if not db.scalar(select(LearningPollParticipant.id).where(LearningPollParticipant.poll_id == poll.id,
                                                             LearningPollParticipant.user_id == user_id)):
        db.add(LearningPollParticipant(poll_id=poll.id, user_id=user_id))
    for idx in picked:
        db.add(LearningPollVote(poll_id=poll.id, user_id=user_id, option_index=idx))
    return picked


def delete_chat_poll(db: Session, message_id: int) -> None:
    """Abstimmung einer gelöschten Chat-Nachricht samt Stimmen entfernen (ohne Commit)."""
    poll_id = db.scalar(select(LearningPoll.id).where(LearningPoll.chat_message_id == message_id))
    if poll_id is not None:
        db.execute(delete(LearningPoll).where(LearningPoll.id == poll_id))


def delete_chat_polls(db: Session, chat_id: int) -> None:
    """Alle Abstimmungen eines gelöschten Chats entfernen (ohne Commit)."""
    db.execute(delete(LearningPoll).where(LearningPoll.chat_id == chat_id))


def chat_polls(db: Session, message_ids: Iterable[int]) -> dict[int, LearningPoll]:
    ids = list(message_ids)
    if not ids:
        return {}
    return {p.chat_message_id: p for p in db.scalars(select(LearningPoll).where(
        LearningPoll.chat_message_id.in_(ids)))}


def poll_done(db: Session, poll_id: int, user_id: int) -> bool:
    return db.scalar(select(LearningPollParticipant.id).where(
        LearningPollParticipant.poll_id == poll_id, LearningPollParticipant.user_id == user_id)) is not None


# ============================================================================ Umfrage
def survey_open(sv: LearningSurvey, now: Optional[datetime] = None) -> bool:
    now = now or utcnow()
    return sv.status == "offen" and not (sv.closes_at is not None and sv.closes_at <= now)


def survey_done(db: Session, survey_id: int, user_id: int) -> bool:
    return db.scalar(select(LearningSurveyParticipant.id).where(
        LearningSurveyParticipant.survey_id == survey_id, LearningSurveyParticipant.user_id == user_id)) is not None


def survey_response_count(db: Session, survey_id: int) -> int:
    return int(db.scalar(select(func.count()).select_from(LearningSurveyParticipant).where(
        LearningSurveyParticipant.survey_id == survey_id)) or 0)


def survey_answers(db: Session, sv: LearningSurvey) -> list[tuple[Optional[int], datetime, dict]]:
    """Alle Antworten: (Konto oder None bei anonym, Zeitpunkt, Antworten)."""
    rows = []
    for r in db.scalars(select(LearningSurveyResponse).where(LearningSurveyResponse.survey_id == sv.id)
                        .order_by(LearningSurveyResponse.id)):
        data = read_json(r, "answers", {})
        rows.append((r.user_id, r.created_at, data if isinstance(data, dict) else {}))
    return rows


# ============================================================================ Selbsttest
def load_question(row: LearningQuestion) -> Optional[dict]:
    data = read_json(row, "data", None)
    return data if isinstance(data, dict) and data.get("type") in lx.QUESTION_TYPES else None


def test_questions(db: Session, test: LearningSelftest) -> list[tuple[int, dict]]:
    ids = [int(i) for i in test.question_ids or []]
    if not ids:
        return []
    rows = {r.id: r for r in db.scalars(select(LearningQuestion).where(LearningQuestion.id.in_(ids),
                                                                       LearningQuestion.channel_id == test.channel_id))}
    out = []
    for qid in ids:
        row = rows.get(qid)
        q = load_question(row) if row is not None else None
        if q is not None:
            out.append((qid, q))
    return out


def test_max_points(db: Session, test: LearningSelftest) -> float:
    return lx.max_points([q for _id, q in test_questions(db, test)])


def attempt_snapshot(att: LearningAttempt) -> list[dict]:
    data = read_json(att, "snapshot", [])
    return data if isinstance(data, list) else []


def attempt_max(snapshot: list[dict]) -> float:
    return lx.max_points([item["q"] for item in snapshot])


def attempt_state(att: LearningAttempt) -> dict:
    data = read_json(att, "answers", {})
    if not isinstance(data, dict):
        data = {}
    data.setdefault("answers", {})
    data.setdefault("checked", [])
    return data


def save_attempt_state(att: LearningAttempt, state: dict) -> None:
    write_json(att, "answers", state)


def new_seed() -> int:
    return random.SystemRandom().randrange(1, 2 ** 31 - 1)


def test_open_now(test: LearningSelftest, now: Optional[datetime] = None) -> bool:
    now = now or utcnow()
    if test.status != "offen":
        return False
    if test.opens_at is not None and now < test.opens_at:
        return False
    return not (test.closes_at is not None and now >= test.closes_at)


def start_attempt(db: Session, test: LearningSelftest, user_id: int) -> LearningAttempt:
    """Neuen Versuch anlegen (ohne Commit); Prüfungen (offen, Versuchszahl) macht die Route."""
    pairs = test_questions(db, test)
    seed = new_seed()
    order = lx.build_order([qid for qid, _q in pairs], seed, test.shuffle_questions)
    by_id = dict(pairs)
    number = int(db.scalar(select(func.coalesce(func.max(LearningAttempt.number), 0)).where(
        LearningAttempt.test_id == test.id, LearningAttempt.user_id == user_id)) or 0) + 1
    now = utcnow()
    deadline: Optional[datetime] = None
    if test.time_limit_min:
        deadline = now + timedelta(minutes=test.time_limit_min)
    if test.closes_at is not None:
        deadline = min(deadline, test.closes_at) if deadline else test.closes_at
    att = LearningAttempt(test_id=test.id, user_id=user_id, number=number, seed=seed, started_at=now,
                          deadline_at=deadline)
    db.add(att)
    db.flush()
    write_json(att, "snapshot", [{"qid": qid, "q": by_id[qid]} for qid in order])
    save_attempt_state(att, {"answers": {}, "checked": []})
    return att


def attempt_expired(att: LearningAttempt, now: Optional[datetime] = None) -> bool:
    return att.finished_at is None and att.deadline_at is not None and (now or utcnow()) > att.deadline_at + GRACE


def finish_attempt(att: LearningAttempt, *, at: Optional[datetime] = None) -> None:
    """Versuch auswerten und abschließen (ohne Commit)."""
    if att.finished_at is not None:
        return
    snapshot = attempt_snapshot(att)
    state = attempt_state(att)
    points, maximum, rows = lx.grade_attempt(snapshot, state["answers"])
    write_json(att, "result", rows)
    att.points, att.max_points = points, maximum
    att.percent = lx.percent(points, maximum)
    att.finished_at = at or utcnow()
    if att.deadline_at is not None and att.finished_at > att.deadline_at:
        att.finished_at = att.deadline_at


def settle(att: LearningAttempt) -> bool:
    """Abgelaufenen Versuch automatisch abschließen (Zeitlimit). ``True``, wenn etwas geändert wurde."""
    if attempt_expired(att):
        finish_attempt(att)
        return True
    return False


def settle_all(db: Session, attempts: Iterable[LearningAttempt]) -> bool:
    changed = False
    for att in attempts:
        changed = settle(att) or changed
    return changed


def best_attempt(attempts: list[LearningAttempt]) -> Optional[LearningAttempt]:
    done = [a for a in attempts if a.finished_at is not None and a.percent is not None]
    if not done:
        return None
    return max(done, key=lambda a: (a.percent or 0, a.finished_at or datetime.min))


def passed(test: LearningSelftest, att: Optional[LearningAttempt]) -> Optional[bool]:
    if att is None:
        return None
    if test.pass_percent is None:
        return None
    return (att.percent or 0) + 1e-9 >= test.pass_percent


def attempts_by_user(db: Session, test_id: int, user_ids: Optional[Iterable[int]] = None) -> dict[int, list[LearningAttempt]]:
    stmt = select(LearningAttempt).where(LearningAttempt.test_id == test_id).order_by(LearningAttempt.number)
    if user_ids is not None:
        stmt = stmt.where(LearningAttempt.user_id.in_(list(user_ids)))
    out: dict[int, list[LearningAttempt]] = {}
    rows = list(db.scalars(stmt))
    if settle_all(db, rows):
        db.flush()
    for a in rows:
        out.setdefault(a.user_id, []).append(a)
    return out


def selftest_grade_of(test: LearningSelftest, attempts: list[LearningAttempt]) -> dict:
    best = best_attempt(attempts)
    return {"element_type": "selftest", "element_id": test.id, "title": test.title,
            "done": best is not None and passed(test, best) is not False,
            "points": best.points if best else None, "max_points": best.max_points if best else None,
            "percent": best.percent if best else None, "passed": passed(test, best),
            "attempts": len(attempts), "finished_at": iso(best.finished_at) if best else None}


def selftest_grades(db: Session, test_id: int, user_ids: Optional[Iterable[int]] = None) -> list[dict]:
    """Ergebnis je Konto (bester Versuch) – für das Notenbuch. Nur Konten mit mindestens einem Versuch."""
    test = db.get(LearningSelftest, test_id)
    if test is None:
        return []
    out = []
    for uid, attempts in attempts_by_user(db, test_id, user_ids).items():
        out.append({"user_id": uid, **selftest_grade_of(test, attempts)})
    return out


def publish_grades(db: Session, test: LearningSelftest) -> int:
    """Punkte (bester Versuch) dem Notenbuch anbieten: Quelle ``selbsttest`` + Test-ID (Doku: NOTENBUCH.md §6).
    Nur Kursräume eines Kursteils haben ein Notenbuch. Ohne Commit; Fehler werden geschluckt (Savepoint)."""
    import logging

    from sqlalchemy import select as _select

    from . import gradebook_sources as gs
    from .feature_models.channels import Channel
    try:
        ch = db.get(Channel, test.channel_id)
        if ch is None or ch.kind != "course" or not ch.ref or "#" not in ch.ref:
            return 0
        course_id, part = ch.ref.rsplit("#", 1)
        grades = selftest_grades(db, test.id)
        sid_of = {uid: sid for uid, sid in db.execute(_select(User.id, User.student_id).where(
            User.id.in_([g["user_id"] for g in grades] or [0])))}
        results = [gs.SourceResult(sid_of[g["user_id"]], points=g["points"]) for g in grades
                   if g["points"] is not None and sid_of.get(g["user_id"])]
        with db.begin_nested():
            return gs.publish_results(db, source_type="selbsttest", source_id=str(test.id), course_id=course_id,
                                      part=int(part), title=test.title, date=(test.closes_at or test.created_at).date().isoformat(),
                                      max_points=test_max_points(db, test), results=results)
    except Exception:  # noqa: BLE001 - das Notenbuch darf den Test nie stören
        logging.getLogger("schulmanager.learning").exception("Selbsttest %s: Übergabe ans Notenbuch fehlgeschlagen", test.id)
        return 0


def withdraw_grades(db: Session, test_id: int) -> None:
    from . import gradebook_sources as gs
    try:
        with db.begin_nested():
            gs.withdraw_results(db, "selbsttest", str(test_id))
    except Exception:  # noqa: BLE001
        pass


def selftest_done(db: Session, test_id: int, user_id: int) -> bool:
    """Abschlussbedingung: mindestens ein beendeter Versuch – und, falls festgelegt, die Bestehensgrenze erreicht."""
    test = db.get(LearningSelftest, test_id)
    if test is None:
        return False
    attempts = attempts_by_user(db, test_id, [user_id]).get(user_id, [])
    best = best_attempt(attempts)
    if best is None:
        return False
    return passed(test, best) is not False


def element_status(db: Session, element_type: str, element_id: int, user_id: int) -> dict:
    """Zustand eines Elements für ein Konto: ``{"done", "points", "max_points", "percent", "passed"}``."""
    base = {"element_type": element_type, "element_id": element_id, "done": False, "points": None,
            "max_points": None, "percent": None, "passed": None}
    if element_type == "selftest":
        test = db.get(LearningSelftest, element_id)
        if test is None:
            return base
        info = selftest_grade_of(test, attempts_by_user(db, element_id, [user_id]).get(user_id, []))
        base.update({k: info[k] for k in ("done", "points", "max_points", "percent", "passed")})
        if info["max_points"] is None:
            base["max_points"] = test_max_points(db, test)
    elif element_type == "survey":
        base["done"] = survey_done(db, element_id, user_id)
    elif element_type == "poll":
        base["done"] = poll_done(db, element_id, user_id)
    return base


def list_elements(db: Session, channel_id: int) -> list[dict]:
    """Abstimmungen, Umfragen und Selbsttests eines Kursraums (Auswahl für Notenbuch / Abschlussbedingung)."""
    out: list[dict] = []
    for t in db.scalars(select(LearningSelftest).where(LearningSelftest.channel_id == channel_id)
                        .order_by(LearningSelftest.id)):
        out.append({"type": "selftest", "id": t.id, "title": t.title, "status": t.status,
                    "max_points": test_max_points(db, t), "pass_percent": t.pass_percent})
    for s in db.scalars(select(LearningSurvey).where(LearningSurvey.channel_id == channel_id)
                        .order_by(LearningSurvey.id)):
        out.append({"type": "survey", "id": s.id, "title": s.title, "status": s.status, "max_points": None,
                    "pass_percent": None})
    for p in db.scalars(select(LearningPoll).where(LearningPoll.channel_id == channel_id).order_by(LearningPoll.id)):
        question, _opts = poll_texts(p)
        out.append({"type": "poll", "id": p.id, "title": question, "status": "geschlossen" if poll_closed(p) else "offen",
                    "max_points": None, "pass_percent": None})
    return out
