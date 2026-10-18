"""Kompetenzraster und Lernstand (Moodle-Lücke M5, ``docs/KOMPETENZEN.md``).

* ``comp_frameworks`` → ``comp_areas`` → ``comp_competencies``: Rahmen mit Bereichen, Kompetenzen und Niveaustufen
  (``levels`` = Beschriftungen der Stufen 1…n). Schulweite Lehrplan-Inhalte, keine personenbezogenen Daten.
* ``comp_assessments``: Lernstand je Schüler/in und Kompetenz, nur anhängend (Verlauf bleibt). ``kind`` ``teacher``
  oder ``self`` (Selbsteinschätzung). Nachweis und Kommentar verschlüsselt (AAD ``comp_assessments.<feld>:<id>``).
* ``comp_links``: generische Zuordnung ``(item_type, item_id)`` → Kompetenz (Aufgaben/Material der Kursräume u. a.).
* ``comp_plans``: Lernplan/Wochenplan je Schüler/in (Titel und Notiz verschlüsselt).
* ``comp_badges`` / ``comp_badge_awards``: Abzeichen und ihre Vergabe (Notiz verschlüsselt).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class CompFramework(Base):
    __tablename__ = "comp_frameworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(40), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    levels: Mapped[list] = mapped_column(JSON, default=list)          # Beschriftungen Stufe 1…n
    support_level: Mapped[int] = mapped_column(Integer, default=1)    # bis zu dieser Stufe: „braucht Unterstützung“
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CompArea(Base):
    __tablename__ = "comp_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    framework_id: Mapped[int] = mapped_column(ForeignKey("comp_frameworks.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(Integer, default=0)


class CompCompetency(Base):
    __tablename__ = "comp_competencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    framework_id: Mapped[int] = mapped_column(ForeignKey("comp_frameworks.id", ondelete="CASCADE"), index=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("comp_areas.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(20), default="")
    title: Mapped[str] = mapped_column(String(300))                    # „Ich kann …“
    descriptors: Mapped[list] = mapped_column(JSON, default=list)      # optional je Stufe ein Text
    position: Mapped[int] = mapped_column(Integer, default=0)


class CompAssessment(Base):
    __tablename__ = "comp_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("comp_competencies.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10), default="teacher")   # teacher | self
    level: Mapped[int] = mapped_column(Integer)
    assessed_on: Mapped[str] = mapped_column(String(10))               # ISO-Datum
    evidence_type: Mapped[str] = mapped_column(String(20), default="")  # "" | note | link | assignment | material
    evidence_ref: Mapped[str] = mapped_column(String(100), default="")  # z. B. channel:12
    evidence_enc: Mapped[str] = mapped_column(Text, default="")
    comment_enc: Mapped[str] = mapped_column(Text, default="")
    by_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    by_name: Mapped[str] = mapped_column(String(200), default="")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # nur ``self``
    confirmed_by: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def aad(self, field: str) -> str:
        return f"comp_assessments.{field}:{self.id}"


class CompLink(Base):
    __tablename__ = "comp_links"
    __table_args__ = (UniqueConstraint("competency_id", "item_type", "item_id", name="uq_comp_links_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("comp_competencies.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[str] = mapped_column(String(30))
    item_id: Mapped[str] = mapped_column(String(60))
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CompPlan(Base):
    __tablename__ = "comp_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    competency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comp_competencies.id", ondelete="SET NULL"),
                                                          nullable=True, index=True)
    title_enc: Mapped[str] = mapped_column(Text, default="")
    note_enc: Mapped[str] = mapped_column(Text, default="")
    week_start: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # Montag der Woche
    due_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="offen")   # offen | in_arbeit | erledigt
    source: Mapped[str] = mapped_column(String(10), default="lehrkraft")  # lehrkraft | schueler
    item_type: Mapped[str] = mapped_column(String(30), default="")
    item_id: Mapped[str] = mapped_column(String(60), default="")
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def aad(self, field: str) -> str:
        return f"comp_plans.{field}:{self.id}"


class CompBadge(Base):
    __tablename__ = "comp_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(300), default="")
    icon: Mapped[str] = mapped_column(String(30), default="star")
    color: Mapped[str] = mapped_column(String(20), default="gold")
    criteria: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)   # None = nur manuell
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CompBadgeAward(Base):
    __tablename__ = "comp_badge_awards"
    __table_args__ = (UniqueConstraint("badge_id", "student_id", name="uq_comp_badge_awards_badge_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    badge_id: Mapped[int] = mapped_column(ForeignKey("comp_badges.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    awarded_on: Mapped[str] = mapped_column(String(10))
    awarded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    awarded_by_name: Mapped[str] = mapped_column(String(200), default="")
    auto: Mapped[bool] = mapped_column(Boolean, default=False)
    note_enc: Mapped[str] = mapped_column(Text, default="")

    def aad(self, field: str) -> str:
        return f"comp_badge_awards.{field}:{self.id}"


def _rewrap(db) -> int:
    from .. import crypto
    return (crypto.rewrap_column(db, CompAssessment, "evidence_enc")
            + crypto.rewrap_column(db, CompAssessment, "comment_enc")
            + crypto.rewrap_column(db, CompPlan, "title_enc") + crypto.rewrap_column(db, CompPlan, "note_enc")
            + crypto.rewrap_column(db, CompBadgeAward, "note_enc"))


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("competency", _rewrap)


_register()
