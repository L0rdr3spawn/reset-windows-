"""Formular-Baukasten (Doku: docs/FORMULARE.md).

* ``form_templates``   – Vorlage einer Schule (Titel, Kategorie, Status ``entwurf|aktiv|archiviert``, aktuelle Version).
* ``form_versions``    – unveränderliche Fassung (Felder, Zielgruppe, Ablauf, Aktionen als JSON). Jede inhaltliche
  Änderung legt eine neue Version an; Einreichungen bleiben bei der Version, mit der sie ausgefüllt wurden.
* ``form_submissions`` – Einreichung. Antworten und Entscheidungsvermerk **verschlüsselt** (AAD
  ``form_submissions.answers:<id>``), Scans/Uploads in der verschlüsselten Dateiablage (``ref_type=form_submission``).
* ``form_events``      – Verlauf einer Einreichung (eingereicht, geprüft, genehmigt, abgelehnt, Scan, Erinnerung).
Schüler und Klasse verweisen nur per ID auf das Planungsdokument (kein Fremdschlüssel).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class FormTemplate(Base):
    __tablename__ = "form_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(30), default="sonstiges", index=True)
    status: Mapped[str] = mapped_column(String(12), default="entwurf", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    library_key: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class FormVersion(Base):
    __tablename__ = "form_versions"
    __table_args__ = (UniqueConstraint("template_id", "version", name="uq_form_versions_template_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("form_templates.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200), default="")
    definition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_by_name: Mapped[str] = mapped_column(String(200), default="")


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("form_templates.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("form_versions.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    class_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    submitted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                        index=True)
    submitted_by_name: Mapped[str] = mapped_column(String(200), default="")
    submitted_role: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(14), default="eingereicht", index=True)
    step: Mapped[int] = mapped_column(Integer, default=0)
    answers_enc: Mapped[str] = mapped_column(Text, default="")
    decision_note_enc: Mapped[str] = mapped_column(Text, default="")
    scan_file_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    due_on: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    reminded_on: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_by_name: Mapped[str] = mapped_column(String(200), default="")


class FormEvent(Base):
    __tablename__ = "form_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("form_submissions.id", ondelete="CASCADE"), index=True)
    step: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(200), default="")
    note_enc: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
