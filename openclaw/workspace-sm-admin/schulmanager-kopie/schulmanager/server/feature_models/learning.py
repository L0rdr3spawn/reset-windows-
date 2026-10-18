"""Lernaktivitäten im Kursraum und im Chat (Doku: docs/LERNAKTIVITAETEN.md).

Abstimmung
----------
* ``learning_polls`` – eine Abstimmung im Kursraum (``channel_id``; Frage und Antworten serverseitig verschlüsselt, AAD
  ``learning_polls.question|options:<id>``) oder an einer Chat-Nachricht (``chat_id`` + ``chat_message_id``; Frage und
  Antworten stehen **nur** Ende-zu-Ende verschlüsselt in der Nachricht, der Server kennt nur die Zahl der Antworten).
* ``learning_poll_participants`` – wer abgestimmt hat (einmal je Person), auch bei anonymen Abstimmungen.
* ``learning_poll_votes`` – namentliche Stimmen (Person + Antwort). **Anonyme** Abstimmungen speichern hier nichts,
  sondern nur Zähler in ``learning_poll_tally``: Stimme und Person sind in der Datenbank nicht verknüpft.

Umfrage (Feedback)
------------------
* ``learning_surveys`` – Fragebogen im Kursraum (Felder wie im Formular-Baukasten, ``schulmanager/forms.py``).
* ``learning_survey_responses`` – Antworten verschlüsselt; bei anonymen Umfragen ohne ``user_id`` und nur mit Tagesdatum.
* ``learning_survey_participants`` – wer geantwortet hat (verhindert Doppelabgaben).

Selbsttest
----------
* ``learning_questions`` – Fragensammlung eines Kursraums (Frage samt Lösung verschlüsselt).
* ``learning_selftests`` – Test: Auswahl und Reihenfolge der Fragen, Versuche, Zeitlimit, Mischen, Rückmeldung.
* ``learning_attempts`` – Versuch einer Schülerin/eines Schülers: Abbild der Fragen zum Startzeitpunkt (spätere
  Änderungen an der Sammlung ändern keine Ergebnisse), Antworten, Ergebnis je Frage (alles verschlüsselt) und die
  Punkte im Klartext (für Notenbuch und Abschlussbedingung).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow
from .channels import EncryptedText


class LearningPoll(EncryptedText, Base):
    __tablename__ = "learning_polls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), nullable=True,
                                                      index=True)
    chat_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    chat_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True)
    question_enc: Mapped[str] = mapped_column(Text, default="")
    options_enc: Mapped[str] = mapped_column(Text, default="")
    option_count: Mapped[int] = mapped_column(Integer, default=2)
    multiple: Mapped[bool] = mapped_column(Boolean, default=False)
    max_choices: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    results: Mapped[str] = mapped_column(String(12), default="live")          # live|after_vote|after_end
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)       # UTC
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)     # UTC, vorzeitig beendet
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearningPollParticipant(Base):
    __tablename__ = "learning_poll_participants"
    __table_args__ = (UniqueConstraint("poll_id", "user_id", name="uq_learning_poll_participants_poll_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("learning_polls.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class LearningPollVote(Base):
    """Namentliche Stimme (nur bei nicht anonymen Abstimmungen)."""
    __tablename__ = "learning_poll_votes"
    __table_args__ = (UniqueConstraint("poll_id", "user_id", "option_index", name="uq_learning_poll_votes_choice"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("learning_polls.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    option_index: Mapped[int] = mapped_column(Integer)


class LearningPollTally(Base):
    """Zähler je Antwort bei anonymen Abstimmungen (ohne Bezug zu einer Person)."""
    __tablename__ = "learning_poll_tally"
    __table_args__ = (UniqueConstraint("poll_id", "option_index", name="uq_learning_poll_tally_option"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("learning_polls.id", ondelete="CASCADE"), index=True)
    option_index: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer, default=0)


class LearningSurvey(EncryptedText, Base):
    __tablename__ = "learning_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    intro_enc: Mapped[str] = mapped_column(Text, default="")
    fields: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(12), default="entwurf")        # entwurf|offen|geschlossen
    closes_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)     # UTC
    results_to_students: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class LearningSurveyResponse(EncryptedText, Base):
    __tablename__ = "learning_survey_responses"
    __table_args__ = (UniqueConstraint("survey_id", "user_id", name="uq_learning_survey_responses_survey_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("learning_surveys.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    answers_enc: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearningSurveyParticipant(Base):
    __tablename__ = "learning_survey_participants"
    __table_args__ = (UniqueConstraint("survey_id", "user_id", name="uq_learning_survey_participants_survey_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("learning_surveys.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class LearningQuestion(EncryptedText, Base):
    __tablename__ = "learning_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    qtype: Mapped[str] = mapped_column(String(12))
    category: Mapped[str] = mapped_column(String(60), default="")
    data_enc: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class LearningSelftest(EncryptedText, Base):
    __tablename__ = "learning_selftests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description_enc: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(12), default="entwurf")        # entwurf|offen|geschlossen
    question_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_limit_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False)
    shuffle_answers: Mapped[bool] = mapped_column(Boolean, default=True)
    immediate_feedback: Mapped[bool] = mapped_column(Boolean, default=False)
    review: Mapped[str] = mapped_column(String(8), default="full")            # none|score|full
    pass_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    opens_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)      # UTC
    closes_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)     # UTC
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class LearningAttempt(EncryptedText, Base):
    __tablename__ = "learning_attempts"
    __table_args__ = (UniqueConstraint("test_id", "user_id", "number", name="uq_learning_attempts_test_user_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("learning_selftests.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer, default=1)
    seed: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # UTC
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # UTC
    snapshot_enc: Mapped[str] = mapped_column(Text, default="")
    answers_enc: Mapped[str] = mapped_column(Text, default="")
    result_enc: Mapped[str] = mapped_column(Text, default="")
    points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


ENCRYPTED_COLUMNS: tuple[tuple[type, str], ...] = (
    (LearningPoll, "question_enc"),
    (LearningPoll, "options_enc"),
    (LearningSurvey, "intro_enc"),
    (LearningSurveyResponse, "answers_enc"),
    (LearningQuestion, "data_enc"),
    (LearningSelftest, "description_enc"),
    (LearningAttempt, "snapshot_enc"),
    (LearningAttempt, "answers_enc"),
    (LearningAttempt, "result_enc"),
)


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): verschlüsselte Texte der Lernaktivitäten neu verpacken."""
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    for model, column in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"{model.__tablename__}.{column}",
                               lambda db, model=model, column=column: crypto.rewrap_column(db, model, column))


_register_rewrap()
