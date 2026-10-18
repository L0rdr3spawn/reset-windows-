"""Löschkonzept (DSGVO Art. 5 Abs. 1 lit. e, Art. 17): Einstellungen, Warteliste „ausgetreten“, Löschprotokoll.

* ``retention_settings`` – Schlüssel/Wert (Fristen in Tagen, Schalter); fehlt ein Schlüssel, gilt der Standard aus
  ``schulmanager/server/retention.py``.
* ``retention_leavers`` – Personen (``student_id``), die nicht mehr im Planungsdokument stehen. Der Anzeigename liegt nur
  **verschlüsselt** (AAD ``retention_leavers.name:<id>``) und wird beim Abschluss geleert.
* ``retention_log`` – Löschprotokoll: was (Datenart, Anzahl) wann für wen (nur ID) gelöscht wurde – **ohne Inhalte**.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class RetentionSetting(Base):
    __tablename__ = "retention_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_by: Mapped[str] = mapped_column(String(80), default="")


class RetentionLeaver(Base):
    __tablename__ = "retention_leavers"
    __table_args__ = (UniqueConstraint("student_id", name="uq_retention_leavers_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(12), default="wartend", index=True)   # wartend | erledigt
    source: Mapped[str] = mapped_column(String(12), default="planung")               # planung | abgleich
    left_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    name_enc: Mapped[str] = mapped_column(Text, default="")
    class_id: Mapped[str] = mapped_column(String(40), default="")
    purged: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)         # bereits bereinigte Datenarten
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @property
    def name_aad(self) -> str:
        return f"retention_leavers.name:{self.id}"


class RetentionLog(Base):
    __tablename__ = "retention_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    action: Mapped[str] = mapped_column(String(20), default="geloescht")   # geloescht | anonymisiert
    mode: Mapped[str] = mapped_column(String(12), default="automatik")     # automatik | frist | sofort
    subject: Mapped[str] = mapped_column(String(60), default="")           # student:S12 | user:7 | ""
    count: Mapped[int] = mapped_column(Integer, default=0)
    actor: Mapped[str] = mapped_column(String(80), default="system")
    note: Mapped[str] = mapped_column(String(200), default="")             # kurzer Anlass, nie Inhalte


def _rewrap(db) -> int:
    from .. import crypto
    return crypto.rewrap_column(db, RetentionLeaver, "name_enc")


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("retention_leavers.name_enc", _rewrap)


_register()
