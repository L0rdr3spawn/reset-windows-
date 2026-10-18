"""Vorschlagspakete der Plan-Prüfung (``docs/PLAN-PRUEFUNG.md``).

Ein *Paket* (``plan_proposals``) entsteht, wenn die Dauerprüfung Probleme im regulären Stundenplan findet: Anlass,
Problemliste und Stand des Plans zum Zeitpunkt der Berechnung (``state_hash``). Die *Varianten*
(``plan_proposal_variants``) sind die zur Wahl stehenden Lösungen mit Kennzahlen vorher/nachher, Änderungsliste und
dem Unterschied zum Plan (``diff``: ``{"upsert": [Stunden], "delete": [IDs]}``). Die Entscheidung („Wir nehmen diesen
Plan“) und jeder Zwischenschritt stehen unveränderlich in ``plan_proposal_log``.

Es gibt keine personenbezogenen Freitexte: Gründe nennen Lehrkräfte nur mit Kürzel, Klassen mit Namen.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

PACKAGE_STATES = ("berechnung", "offen", "angenommen", "verworfen", "ersetzt", "erledigt", "veraltet", "fehlgeschlagen")


class PlanProposal(Base):
    """Ein Vorschlagspaket: Anlass + Varianten (``berechnung`` → ``offen`` → Entscheidung)."""
    __tablename__ = "plan_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # berechnung|offen|angenommen|verworfen|ersetzt|erledigt|veraltet|fehlgeschlagen
    status: Mapped[str] = mapped_column(String(20), default="berechnung", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    base_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)       # Stand des Plans (Anzeige)
    state_hash: Mapped[str] = mapped_column(String(32), default="", index=True)       # Stunden + Problemlage
    signature: Mapped[str] = mapped_column(String(32), default="")                    # Problemlage (autoplan)
    title: Mapped[str] = mapped_column(String(300), default="")
    reasons: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)         # lesbare Probleme
    trigger_scope: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)   # Änderungsquellen (scope)
    problem_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_from: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)      # ISO-Datum, ab dem der Anlass gilt
    postponed_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # „später“
    postponed_by: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # kein Fremdschlüssel (Audit bleibt)
    decided_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    decision_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    chosen_variant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    applied_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)     # Version nach der Übernahme
    informed: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)         # nach Annahme informierte Lehrkräfte


class PlanProposalVariant(Base):
    """Eine Lösung eines Pakets (``key``: minimal|lokal|gruendlich|vertretung|raeume)."""
    __tablename__ = "plan_proposal_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("plan_proposals.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(20))
    position: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="berechnung")   # berechnung|bereit|keine_loesung|fehlgeschlagen
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    metrics_before: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metrics_after: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    changes: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)         # Diff-Liste (lesbar)
    affected_classes: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    affected_teachers: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    moved_lessons: Mapped[int] = mapped_column(Integer, default=0)
    remaining: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)        # danach noch offene Probleme
    valid_from: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    diff: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)        # Unterschied zum Plan
    compute_seconds: Mapped[float] = mapped_column(Float, default=0.0)


Index("ix_plan_proposal_variants_pkg_pos", PlanProposalVariant.package_id, PlanProposalVariant.position)


class PlanProposalLog(Base):
    """Verlauf eines Pakets (nur anhängen): erzeugt, ersetzt, später, angenommen, verworfen, informiert …"""
    __tablename__ = "plan_proposal_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[int] = mapped_column(Integer, index=True)                       # kein Fremdschlüssel
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    action: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_name: Mapped[str] = mapped_column(String(200), default="")
    variant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    detail: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
