"""Notenbuch (B-52, ``docs/NOTENBUCH.md``): Konfiguration, Notenbücher je Kurs(teil) und Halbjahr, Kategorien,
Leistungen, Eintragungen, Halbjahres-/Zeugnisnoten, Änderungsprotokoll und Ergebnisse anderer Bereiche.

Verschlüsselt (``crypto.encrypt_text``, AAD ``<tabelle>.<feld>:<id>``): Noten/Punkte (``value_enc``) und Bemerkungen
(``note_enc``) der Eintragungen und Endnoten sowie die Einzelheiten des Protokolls (``detail_enc``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class GradebookConfig(Base):
    """Schulweite Einstellungen als Schlüssel/Wert (``settings`` – siehe ``gradebook_store.DEFAULT_SETTINGS``)."""
    __tablename__ = "gb_config"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class GradeBook(Base):
    """Notenbuch eines Kursteils in einem Halbjahr (``term`` z. B. ``2026-1``)."""
    __tablename__ = "gb_books"
    __table_args__ = (UniqueConstraint("course_id", "part", "term", name="uq_gb_books_course_part_term"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    part: Mapped[int] = mapped_column(Integer, default=0)
    term: Mapped[str] = mapped_column(String(10), index=True)
    scale_id: Mapped[str] = mapped_column(String(40), default="note6")
    key_id: Mapped[str] = mapped_column(String(40), default="")
    rounding: Mapped[str] = mapped_column(String(10), default="ganz")
    decimals: Mapped[int] = mapped_column(Integer, default=2)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    locked_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locked_by_name: Mapped[str] = mapped_column(String(200), default="")


class GradeCategory(Base):
    """Leistungsart (z. B. „Schriftlich“, „Sonstige Mitarbeit“, darunter „Tests“); verschachtelbar."""
    __tablename__ = "gb_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("gb_books.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    position: Mapped[int] = mapped_column(Integer, default=0)


class GradeItem(Base):
    """Eine Leistung (Spalte der Notentabelle): Klausur, Test, Referat …"""
    __tablename__ = "gb_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("gb_books.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(120))
    date: Mapped[str] = mapped_column(String(10), default="")
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    key_id: Mapped[str] = mapped_column(String(40), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    released: Mapped[bool] = mapped_column(Boolean, default=False)
    makeup_date: Mapped[str] = mapped_column(String(10), default="")
    source_type: Mapped[str] = mapped_column(String(30), default="")
    source_id: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class GradeEntry(Base):
    """Note/Punkte einer Person bei einer Leistung. ``status`` siehe ``gradebook.STATUS_LABELS``."""
    __tablename__ = "gb_entries"
    __table_args__ = (UniqueConstraint("item_id", "student_id", name="uq_gb_entries_item_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("gb_items.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    value_enc: Mapped[str] = mapped_column(Text, default="")
    note_enc: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="")
    makeup_date: Mapped[str] = mapped_column(String(10), default="")
    from_source: Mapped[bool] = mapped_column(Boolean, default=False)
    entered_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entered_by_name: Mapped[str] = mapped_column(String(200), default="")
    entered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def aad(self, field: str) -> str:
        return f"gb_entries.{field}:{self.id}"


class GradeFinal(Base):
    """Festgelegte Halbjahres-/Zeugnisnote einer Person (die Vorschlagsnote wird immer neu berechnet)."""
    __tablename__ = "gb_finals"
    __table_args__ = (UniqueConstraint("book_id", "student_id", name="uq_gb_finals_book_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("gb_books.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    value_enc: Mapped[str] = mapped_column(Text, default="")
    note_enc: Mapped[str] = mapped_column(Text, default="")
    set_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    set_by_name: Mapped[str] = mapped_column(String(200), default="")
    set_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def aad(self, field: str) -> str:
        return f"gb_finals.{field}:{self.id}"


class GradeLog(Base):
    """Änderungsprotokoll je Notenbuch (wer hat wann welche Note von … auf … gesetzt); Einzelheiten verschlüsselt."""
    __tablename__ = "gb_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, index=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_name: Mapped[str] = mapped_column(String(200), default="")
    action: Mapped[str] = mapped_column(String(30))
    item_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    student_id: Mapped[str] = mapped_column(String(40), default="")
    detail_enc: Mapped[str] = mapped_column(Text, default="")

    def aad(self, field: str) -> str:
        return f"gb_log.{field}:{self.id}"


class GradeSourceResult(Base):
    """Ergebnis aus einem anderen Bereich (Aufgabe, Selbsttest …), das die Lehrkraft übernehmen kann.
    Schnittstelle: ``gradebook_sources.publish_results``."""
    __tablename__ = "gb_source_results"
    __table_args__ = (UniqueConstraint("source_type", "source_id", "student_id", name="uq_gb_source_results"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(30), index=True)
    source_id: Mapped[str] = mapped_column(String(80))
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    part: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(120), default="")
    date: Mapped[str] = mapped_column(String(10), default="")
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[str] = mapped_column(String(20), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class GradeSourceLink(Base):
    """Entscheidung der Lehrkraft je Quelle und Notenbuch: übernommen (``adopted``) oder abgewählt (``dismissed``)."""
    __tablename__ = "gb_source_links"
    __table_args__ = (UniqueConstraint("book_id", "source_type", "source_id", name="uq_gb_source_links"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("gb_books.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(30))
    source_id: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(12), default="adopted")
    item_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


def _rewrap(db) -> int:
    from .. import crypto
    return (crypto.rewrap_column(db, GradeEntry, "value_enc") + crypto.rewrap_column(db, GradeEntry, "note_enc")
            + crypto.rewrap_column(db, GradeFinal, "value_enc") + crypto.rewrap_column(db, GradeFinal, "note_enc")
            + crypto.rewrap_column(db, GradeLog, "detail_enc"))


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("gradebook", _rewrap)


_register()
