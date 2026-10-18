"""Nachschreibtermine: Wer eine Klausur/einen Test wegen Krankheit oder Fehlens verpasst hat, schreibt nach.

* ``exam_makeup_dates`` – ein Nachschreibtermin (Datum, Stunden, Raum) zu einer Klausur des Planungsdokuments;
  mehrere Schüler/innen können denselben Termin teilen.
* ``exam_makeups`` – je verpasster Klausur und Person eine Zeile (Status ``offen`` → ``angesetzt`` → ``erledigt``
  bzw. ``entfallen``). Das Attest wird nicht hier gespeichert, sondern aus den Dokumenten der Fehlzeit abgeleitet
  (``student_documents``); ``attest_waived`` = Klassenleitung/Sekretariat verzichten auf das Attest.
Klausur und Person verweisen nur per ID auf das Planungsdokument (kein Fremdschlüssel).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

MAKEUP_STATUS = {"offen": "Termin offen", "angesetzt": "Termin festgelegt", "erledigt": "nachgeschrieben",
                 "entfallen": "entfällt"}


class ExamMakeupDate(Base):
    __tablename__ = "exam_makeup_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[str] = mapped_column(String(80), index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    start: Mapped[int] = mapped_column(Integer, default=0)
    length: Mapped[int] = mapped_column(Integer, default=1)
    room: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ExamMakeup(Base):
    __tablename__ = "exam_makeups"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_exam_makeups_exam_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[str] = mapped_column(String(80), index=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    course_id: Mapped[str] = mapped_column(String(80), default="")
    exam_date: Mapped[str] = mapped_column(String(10), index=True)
    source: Mapped[str] = mapped_column(String(20), default="krank")          # krank | fehlt (Klassenbuch)
    absence_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="offen", index=True)
    date_id: Mapped[Optional[int]] = mapped_column(ForeignKey("exam_makeup_dates.id", ondelete="SET NULL"),
                                                   nullable=True, index=True)
    attest_waived: Mapped[bool] = mapped_column(Boolean, default=False)
    waived_by_name: Mapped[str] = mapped_column(String(200), default="")
    handled_by_name: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
