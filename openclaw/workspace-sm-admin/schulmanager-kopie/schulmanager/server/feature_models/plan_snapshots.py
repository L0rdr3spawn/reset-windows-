"""Gespeicherte Plan-Stände („Stand Herbst A“): der Stundenplan (nur die Unterrichtsblöcke) unter einem Namen.

Der Versionsverlauf des Planungsdokuments (``school_versions``, ``SM_KEEP_VERSIONS``) wird nach 300 Änderungen
gekürzt und kennt keine Namen. Ein Plan-Stand bleibt dagegen erhalten, bis er gelöscht wird. Wiederherstellen legt wie
jede Änderung eine neue Version an (rückgängig über „Verlauf“).

Es gibt keine personenbezogenen Freitexte: Name und Notiz sind Bezeichnungen des Plans.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class PlanSnapshot(Base):
    """Ein benannter Plan-Stand (Stunden als zlib-JSON, Kennzahlen zum Zeitpunkt des Speicherns)."""
    __tablename__ = "plan_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    note: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(200), default="")
    source: Mapped[str] = mapped_column(String(20), default="aktuell")        # aktuell | entwurf
    source_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # Planversion beim Speichern
    lessons_count: Mapped[int] = mapped_column(Integer, default=0)
    # Planzeitraum (``plan_periods``): leer = ganzer Plan, sonst nur die Stunden dieses Zeitraums
    period: Mapped[str] = mapped_column(String(20), default="", server_default="")
    data: Mapped[bytes] = mapped_column(LargeBinary)                           # zlib-JSON der Stunden
    metrics: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
