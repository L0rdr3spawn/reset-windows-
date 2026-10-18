"""Aufgaben-Erweiterungen im Kursraum (Migration 0036): Bewertungsraster, Fristverlängerung, Versionen.

* ``assignment_settings`` – je Aufgabe (1:1 zu ``channel_items``): Gruppenabgabe, Höchstpunkte, Notenschlüssel und das
  **Raster** (Kopie der Vorlage, damit spätere Änderungen an der Vorlage ausgefüllte Bewertungen nicht verfälschen).
  Kriterien-Texte liegen verschlüsselt in ``rubric_enc`` (JSON).
* ``grading_templates`` – Raster-Vorlagen einer Lehrkraft (wiederverwendbar über Kursräume hinweg).
* ``assignment_extensions`` – verlängerte Frist je Schüler/in **oder** Gruppe (Begründung verschlüsselt).
* ``assignment_submission_versions`` – frühere Versionen einer Abgabe samt Rückmeldung, wenn eine Überarbeitung
  angefordert wurde; die aktuelle Version bleibt in ``assignment_submissions``.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow
from .channels import EncryptedText


class GradingTemplate(EncryptedText, Base):
    __tablename__ = "grading_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10))                            # rubric|guide
    criteria_enc: Mapped[str] = mapped_column(Text, default="")
    grade_scale: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def rubric(self) -> Optional[dict[str, Any]]:
        raw = self.read_text("criteria")
        try:
            data = json.loads(raw) if raw else None
        except ValueError:
            return None
        return data if isinstance(data, dict) else None


class AssignmentSettings(EncryptedText, Base):
    __tablename__ = "assignment_settings"
    __table_args__ = (UniqueConstraint("item_id", name="uq_assignment_settings_item_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("channel_items.id", ondelete="CASCADE"))
    group_mode: Mapped[bool] = mapped_column(Boolean, default=False)         # Gruppenabgabe
    group_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_group_sets.id", ondelete="SET NULL"),
                                                        nullable=True)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # ohne Raster: freie Höchstpunktzahl
    grade_scale: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    rubric_kind: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # rubric|guide
    rubric_enc: Mapped[str] = mapped_column(Text, default="")                # JSON der Kriterien, verschlüsselt
    rubric_title: Mapped[str] = mapped_column(String(200), default="")
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("grading_templates.id", ondelete="SET NULL"),
                                                       nullable=True)
    show_parents: Mapped[bool] = mapped_column(Boolean, default=False)       # Eltern sehen das ausgefüllte Raster
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def rubric(self) -> Optional[dict[str, Any]]:
        raw = self.read_text("rubric")
        try:
            data = json.loads(raw) if raw else None
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def set_rubric(self, rubric: Optional[dict[str, Any]]) -> None:
        self.rubric_kind = rubric["kind"] if rubric else None
        self.write_text("rubric", json.dumps(rubric, ensure_ascii=False) if rubric else "")


class AssignmentExtension(EncryptedText, Base):
    __tablename__ = "assignment_extensions"
    __table_args__ = (UniqueConstraint("item_id", "user_id", name="uq_assignment_extensions_item_user"),
                      UniqueConstraint("item_id", "group_id", name="uq_assignment_extensions_item_group"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("channel_items.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True,
                                                   index=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("channel_groups.id", ondelete="CASCADE"),
                                                    nullable=True, index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime)                       # UTC
    reason_enc: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AssignmentSubmissionVersion(EncryptedText, Base):
    __tablename__ = "assignment_submission_versions"
    __table_args__ = (UniqueConstraint("submission_id", "attempt", name="uq_assignment_submission_versions_sub_att"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("assignment_submissions.id", ondelete="CASCADE"),
                                               index=True)
    attempt: Mapped[int] = mapped_column(Integer)
    text_enc: Mapped[str] = mapped_column(Text, default="")
    file_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="abgegeben")     # Status der Version beim Abschluss
    feedback_enc: Mapped[str] = mapped_column(Text, default="")
    grade_enc: Mapped[str] = mapped_column(Text, default="")
    rubric_enc: Mapped[str] = mapped_column(Text, default="")
    points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_points: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_file_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    feedback_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


ENCRYPTED_COLUMNS: tuple[tuple[type, str], ...] = (
    (AssignmentSettings, "rubric_enc"),
    (GradingTemplate, "criteria_enc"),
    (AssignmentExtension, "reason_enc"),
    (AssignmentSubmissionVersion, "text_enc"),
    (AssignmentSubmissionVersion, "feedback_enc"),
    (AssignmentSubmissionVersion, "grade_enc"),
    (AssignmentSubmissionVersion, "rubric_enc"),
)


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): verschlüsselte Texte neu verpacken."""
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover - Basisdienst fehlt
        return
    for model, column in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"{model.__tablename__}.{column}",
                               lambda db, model=model, column=column: crypto.rewrap_column(db, model, column))


_register_rewrap()
