"""Betrieb & Einrichtung (``docs/PRODUKTREIFE.md``): Zustandsspeicher und Fehlerprotokoll.

* ``system_state`` – kleine Schlüssel/Wert-Ablage für Systemzustand ohne eigene Tabelle: Fortschritt des
  Einrichtungsassistenten (``setup``), Schulprofil (``school_profile``), Läufe des Schuljahreswechsels
  (``yearchange``), letzter Wartungslauf (``maintenance``). Keine Freitexte über Personen.
* ``error_log`` – Fehlerprotokoll für die Administration (nur ``ERROR``/``CRITICAL``, höchstens 30 Tage bzw.
  1000 Einträge, siehe ``ops.prune_error_log``). Meldungen werden gekürzt; Anfragepfade ohne Query und mit
  maskierten Kennungen (``middleware.mask_path``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class SystemState(Base):
    """Schlüssel/Wert-Zustand des Systems (JSON)."""
    __tablename__ = "system_state"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    updated_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)


class ErrorLogEntry(Base):
    """Ein Eintrag im Fehlerprotokoll (``/admin/errors``)."""
    __tablename__ = "error_log"
    __table_args__ = (Index("ix_error_log_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    level: Mapped[str] = mapped_column(String(10), default="ERROR")
    logger: Mapped[str] = mapped_column(String(120), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    request_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
