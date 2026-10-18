"""Elternzugriff volljähriger Schüler/innen (A-44) – Tabelle ``parent_access`` (Migration 0013_parent_access).

Je Schüler/in (ID aus dem Planungsdokument) und Bereich (``kursraeume``, ``krankmeldungen``, ``dokumente``,
``stundenplan`` …) ein Eintrag „Eltern dürfen sehen: ja/nein“. Gilt nur für Volljährige; Minderjährige: Eltern
sehen immer alles, was das Kind sieht. Fehlt ein Eintrag, gilt für Volljährige „nein“. Logik:
``schulmanager/server/parent_access.py`` (:func:`parent_may_see`).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class ParentAccess(Base):
    """Einstellung einer/eines volljährigen Schüler/in: Eltern dürfen einen Bereich sehen (ja/nein)."""
    __tablename__ = "parent_access"
    __table_args__ = (UniqueConstraint("student_id", "area", name="uq_parent_access_student_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)             # Planungsdokument
    area: Mapped[str] = mapped_column(String(40))                                # kursraeume|krankmeldungen|…
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    set_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudentPrefs(Base):
    """Persönliche Einstellungen einer/eines Schüler/in zum Elternzugriff (je Schüler-ID eine Zeile).

    ``delivery``: wohin Informationen der Schule (Rundschreiben im Postfach) gehen, sobald die Person volljährig ist –
    ``self`` (nur an sie/ihn), ``parents`` (nur an die Eltern), ``both``. Minderjährig gilt immer „beide“.
    ``decided_at``: wann die volljährige Person ihre Freigaben zum ersten Mal bewusst gespeichert hat (leer = der
    Hinweis „Du bist volljährig – lege fest, was deine Eltern sehen“ bleibt sichtbar)."""
    __tablename__ = "student_prefs"

    student_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    delivery: Mapped[str] = mapped_column(String(10), default="self")
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
