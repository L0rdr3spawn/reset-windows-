"""Importe aus Fremdsystemen: Läufe (Protokoll) und Verknüpfungen (Idempotenz, Rückgängig).

* ``import_runs`` – ein Eintrag je **echtem** Import (Trockenläufe werden nicht gespeichert): Quelle, Prüfsumme der Datei,
  Optionen, Zähler und – **verschlüsselt** (``report_enc``, enthält Namen) – der vollständige Bericht.
* ``import_links`` – ordnet ein Element des Quellsystems (``system``, ``instance``, ``kind``, ``source_key``) dem
  angelegten Ziel zu (``target_kind``/``target_id``). Ein zweiter Import findet darüber vorhandene Objekte wieder
  (keine Dubletten); „Rückgängig“ entfernt alles, was ein Lauf angelegt hat (``created_run``).
  ``fingerprint`` erkennt unveränderte Elemente (dann wird nichts geschrieben).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow
from .channels import EncryptedText


class ImportRun(EncryptedText, Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system: Mapped[str] = mapped_column(String(30), index=True)
    instance: Mapped[str] = mapped_column(String(60), default="standard")
    source_name: Mapped[str] = mapped_column(String(200), default="")
    source_hash: Mapped[str] = mapped_column(String(64), default="")
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(80), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="ok")        # ok | teilweise | fehler | zurueckgenommen
    options: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    summary: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    report_enc: Mapped[str] = mapped_column(Text, default="")
    undone_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    undone_by: Mapped[str] = mapped_column(String(80), default="")


class ImportLink(Base):
    __tablename__ = "import_links"
    __table_args__ = (UniqueConstraint("system", "instance", "kind", "source_key", name="uq_import_links_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system: Mapped[str] = mapped_column(String(30))
    instance: Mapped[str] = mapped_column(String(60), default="standard")
    kind: Mapped[str] = mapped_column(String(30))                      # person|course|group|assign|submission|…
    source_key: Mapped[str] = mapped_column(String(120))
    target_kind: Mapped[str] = mapped_column(String(30))               # student|teacher|class|channel|item|…
    target_id: Mapped[str] = mapped_column(String(120), default="")
    fingerprint: Mapped[str] = mapped_column(String(40), default="")
    created_run: Mapped[Optional[int]] = mapped_column(ForeignKey("import_runs.id", ondelete="SET NULL"),
                                                       nullable=True, index=True)
    updated_run: Mapped[Optional[int]] = mapped_column(ForeignKey("import_runs.id", ondelete="SET NULL"),
                                                       nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


def _register_rewrap() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("import_runs.report_enc", lambda db: crypto.rewrap_column(db, ImportRun, "report_enc"))


_register_rewrap()
