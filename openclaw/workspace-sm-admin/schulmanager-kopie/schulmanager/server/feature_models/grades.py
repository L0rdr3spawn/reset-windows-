"""Noten zu Klausuren/Tests (``exam_results``). Note und Bemerkung verschlüsselt (AAD ``exam_results.<feld>:<id>``)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class ExamResult(Base):
    __tablename__ = "exam_results"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_exam_results_exam_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[str] = mapped_column(String(40), index=True)        # Exam.id im Planungsdokument
    course_id: Mapped[str] = mapped_column(String(64), default="")
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    grade_enc: Mapped[str] = mapped_column(Text, default="")
    note_enc: Mapped[str] = mapped_column(Text, default="")
    graded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    graded_by_name: Mapped[str] = mapped_column(String(200), default="")
    graded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def aad(self, field: str) -> str:
        return f"exam_results.{field}:{self.id}"


def _rewrap(db) -> int:
    from .. import crypto
    return crypto.rewrap_column(db, ExamResult, "grade_enc") + crypto.rewrap_column(db, ExamResult, "note_enc")


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("exam_results", _rewrap)


_register()
