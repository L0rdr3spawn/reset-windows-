"""Lehrer-Selbstverwaltung: Änderungsanträge von Lehrkräften (Tabelle ``teacher_change_requests``).

``payload`` = gewünschtes Profil ``{subjects, preferred_classes, max_hours, time_windows, wishes}``,
``previous`` = Profil zum Zeitpunkt des Antrags (Vergleich alt/neu). Freitexte (Begründung der Lehrkraft,
Kommentar der Prüfenden) werden nur **verschlüsselt** gespeichert (``crypto.encrypt_text``, AAD =
``teacher_change_requests:<id>:<feld>``). Status: ``offen | genehmigt | abgelehnt | zurueckgezogen``.
Direkt übernommene Änderungen (``settings.teacher_self_service = "direct"``) werden als ``genehmigt``
mit ``auto = True`` protokolliert.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

REQUEST_KINDS = ("profil", "ausnahme")
REQUEST_STATUSES = ("offen", "genehmigt", "abgelehnt", "zurueckgezogen")


class TeacherChangeRequest(Base):
    __tablename__ = "teacher_change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[str] = mapped_column(String(40), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                   index=True)
    # "profil" = Profiländerung (``payload`` = Profil), "ausnahme" = einmalige Ausnahme (``payload`` =
    # ``{"exception": {"date", "date_to", "periods", "reason"}}``, Genehmigung legt eine Abwesenheit an)
    kind: Mapped[str] = mapped_column(String(20), default="profil", server_default="profil", index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    previous: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    note_enc: Mapped[str] = mapped_column(Text, default="")              # verschlüsselt (SM1…) oder leer
    status: Mapped[str] = mapped_column(String(20), default="offen", index=True)
    auto: Mapped[bool] = mapped_column(Boolean, default=False)           # direkt übernommen (ohne Prüfung)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_comment_enc: Mapped[str] = mapped_column(Text, default="")    # verschlüsselt (SM1…) oder leer
    applied_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


Index("ix_teacher_change_requests_teacher_status", TeacherChangeRequest.teacher_id, TeacherChangeRequest.status)

ENCRYPTED_COLUMNS = ("note_enc", "review_comment_enc")


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): verschlüsselte Freitexte neu verpacken."""
    try:  # Basisdienst (Agent Basis)
        from .. import crypto
    except ImportError:  # pragma: no cover - crypto (noch) nicht vorhanden
        return
    for col in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"teacher_change_requests.{col}",
                               lambda db, col=col: crypto.rewrap_column(db, TeacherChangeRequest, col))


_register_rewrap()
