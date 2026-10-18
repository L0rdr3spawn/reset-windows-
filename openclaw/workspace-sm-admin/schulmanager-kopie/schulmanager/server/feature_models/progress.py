"""Lernfortschritt im Kursraum (Moodle-Lücken M2): Abschlussbedingungen, „Erledigt“-Häkchen, bedingte Freigabe.

Tabellen
--------
* ``completion_rules`` – je Element (``element_type`` + ``element_id``, z. B. ``item`` = Material/Aufgabe des Kursraums)
  die Abschlussbedingung: ``manual`` (Schüler/in hakt ab), ``viewed`` (geöffnet), ``submitted`` (abgegeben),
  ``graded`` (bewertet), ``passed`` (bestanden, ``pass_percent``). Ohne Zeile wird das Element nicht verfolgt.
* ``completion_marks`` – manuelle Häkchen (nur bei ``manual``). Die übrigen Bedingungen werden aus den vorhandenen
  Daten (Ansichten, Abgaben, Bewertung) berechnet – nichts wird doppelt gespeichert.
* ``availability_rules`` – bedingte Freigabe: ``tree`` = verschachtelte UND/ODER-Bedingungen (siehe
  ``schulmanager/server/progress.py``).

``element_type``/``element_id`` sind bewusst generisch (kein Fremdschlüssel): neue Elementarten (Abstimmung, Selbsttest …)
melden sich über ``progress.register_provider`` an. Beim endgültigen Löschen eines Elements räumt
``progress.forget_element`` die Zeilen weg; beim Löschen des Kursraums über den Fremdschlüssel ``channel_id``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class CompletionRule(Base):
    """Abschlussbedingung eines Elements."""
    __tablename__ = "completion_rules"
    __table_args__ = (UniqueConstraint("channel_id", "element_type", "element_id",
                                       name="uq_completion_rules_element"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    element_type: Mapped[str] = mapped_column(String(30))
    element_id: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(20), default="manual")
    pass_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CompletionMark(Base):
    """Manuelles „Erledigt“ einer Schülerin/eines Schülers."""
    __tablename__ = "completion_marks"
    __table_args__ = (UniqueConstraint("element_type", "element_id", "user_id", name="uq_completion_marks_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    element_type: Mapped[str] = mapped_column(String(30))
    element_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    done_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AvailabilityRule(Base):
    """Bedingte Freigabe eines Elements (UND/ODER-Baum in ``tree``)."""
    __tablename__ = "availability_rules"
    __table_args__ = (UniqueConstraint("channel_id", "element_type", "element_id",
                                       name="uq_availability_rules_element"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    element_type: Mapped[str] = mapped_column(String(30))
    element_id: Mapped[int] = mapped_column(Integer)
    tree: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
