"""Klassenbuch: eine Zeile je gehaltener Unterrichtsstunde (Datum, Stunde, Kurs/Kursteil) mit Thema, Hausaufgabe und
Anwesenheit. Fehlen, Verspätung und früheres Gehen werden als ``student_absences`` (``register_id``) geführt und
müssen dort entschuldigt werden. Thema/Hausaufgabe/Anwesenheit verschlüsselt (AAD ``register_lessons.<feld>:<id>``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class RegisterLesson(Base):
    __tablename__ = "register_lessons"
    __table_args__ = (UniqueConstraint("date", "lesson_id", "period", "part", name="uq_register_lessons_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    lesson_id: Mapped[str] = mapped_column(String(40))
    period: Mapped[int] = mapped_column(Integer)
    part: Mapped[int] = mapped_column(Integer, default=0)
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    class_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    subject: Mapped[str] = mapped_column(String(40), default="")
    teacher_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    topic_enc: Mapped[str] = mapped_column(Text, default="")
    homework_enc: Mapped[str] = mapped_column(Text, default="")
    attendance_enc: Mapped[str] = mapped_column(Text, default="")      # JSON {student_id: {status, minutes}}
    checked_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checked_by_name: Mapped[str] = mapped_column(String(200), default="")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def aad(self, field: str) -> str:
        return f"register_lessons.{field}:{self.id}"


def _rewrap(db) -> int:
    from .. import crypto
    return sum(crypto.rewrap_column(db, RegisterLesson, c) for c in ("topic_enc", "homework_enc", "attendance_enc"))


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("register_lessons", _rewrap)


_register()
