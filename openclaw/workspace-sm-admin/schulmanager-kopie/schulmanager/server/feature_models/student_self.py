"""Schüler-Selbstbedienung (Erweiterung 2, §9.6): eingereichte Dokumente/Atteste (Tabelle ``student_documents``).

Die Datei liegt verschlüsselt in ``stored_files`` (Zweck ``student_document``, angehängt als
``ref_type="student_document"``). Titel und Vermerk werden nur **verschlüsselt** gespeichert
(``crypto.encrypt_text``, AAD ``student_documents.<feld>:<id>``). ``file_id`` ist leer, wenn das Sekretariat nur
vermerkt, dass ein Papier-Attest vorliegt.

Kategorien: ``attest | entschuldigung | beurlaubung | einverstaendnis | sonstiges``; Status: ``eingegangen | geprueft | abgelehnt``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class StudentDocument(Base):
    __tablename__ = "student_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    absence_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("student_absences.id", ondelete="SET NULL"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(20))
    title_enc: Mapped[str] = mapped_column(Text, default="")             # verschlüsselt (SM1…)
    file_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("stored_files.id", ondelete="SET NULL"), nullable=True)
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                       index=True)
    uploaded_by_name: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="eingegangen", index=True)
    handled_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    handled_by_name: Mapped[str] = mapped_column(String(200), default="")
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    note_enc: Mapped[str] = mapped_column(Text, default="")              # verschlüsselt (SM1…) oder leer
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    # zurückgezogen/archiviert (Migration 0024): Dokument und Datei bleiben erhalten, erscheinen aber nicht mehr in
    # den Listen; endgültig gelöscht wird nur nach der Aufbewahrungsfrist (``run_retention``)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    withdrawn_by_name: Mapped[str] = mapped_column(String(200), default="", server_default="")


Index("ix_student_documents_student_created", StudentDocument.student_id, StudentDocument.created_at)

ENCRYPTED_COLUMNS = ("title_enc", "note_enc")


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): verschlüsselte Texte neu verpacken – auch die (seit §9.6
    verschlüsselten) Gründe/Vermerke der Krankmeldungen."""
    from .. import crypto
    from ..db_models import StudentAbsence

    for col in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"student_documents.{col}",
                               lambda db, col=col: crypto.rewrap_column(db, StudentDocument, col))
    for col in ("reason", "note"):
        crypto.register_rewrap(f"student_absences.{col}",
                               lambda db, col=col: crypto.rewrap_column(db, StudentAbsence, col))


_register_rewrap()
