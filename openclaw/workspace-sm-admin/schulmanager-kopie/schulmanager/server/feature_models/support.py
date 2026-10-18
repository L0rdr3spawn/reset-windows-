"""Förderinformationen je Schüler/in: Nachteilsausgleich, Schulbegleitung, Förderplan, Sonstiges – mit Dokumenten.
Titel/Details verschlüsselt (AAD ``student_support.<feld>:<id>``), Dateien über die verschlüsselte Dateiablage
(``ref_type="student_support"``)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

SUPPORT_KINDS = {"nachteilsausgleich": "Nachteilsausgleich", "schulbegleitung": "Schulbegleitung",
                 "foerderplan": "Förderplan", "sonstiges": "Sonstiges"}


class StudentSupport(Base):
    __tablename__ = "student_support"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    kind: Mapped[str] = mapped_column(String(30), default="nachteilsausgleich")
    title_enc: Mapped[str] = mapped_column(Text, default="")
    details_enc: Mapped[str] = mapped_column(Text, default="")
    valid_from: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    valid_to: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    file_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    # Katalog-Zuordnung (Migration 0023): Merkmal, Zeitzuschlag, Fächer (leer = alle), Hilfsmittel (verschlüsselt)
    catalog_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    subjects: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    aids_enc: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def aad(self, field: str) -> str:
        return f"student_support.{field}:{self.id}"


class SupportCatalog(Base):
    """Katalog der Merkmale/Nachteilsausgleiche, den die Schule pflegt (Migration 0023).

    ``teacher_visible``: Lehrkräfte sehen Art, Minuten, Fächer und Hilfsmittel bei Klausuren (Ausgleichsart);
    ``False`` = Diagnose-/Förderbedarfsmerkmal, nur für Berechtigte (Klassenleitung, Verwaltung, Familie)."""
    __tablename__ = "support_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(30), default="nachteilsausgleich")
    uses_minutes: Mapped[bool] = mapped_column(Boolean, default=False)
    default_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    teacher_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


# (Bezeichnung, Art, Minuten?, Standardminuten, für Lehrkräfte sichtbar)
DEFAULT_CATALOG: list[tuple[str, str, bool, Optional[int], bool]] = [
    ("Zeitzuschlag", "nachteilsausgleich", True, 15, True),
    ("Wörterbuch/Duden erlaubt", "nachteilsausgleich", False, None, True),
    ("Eigener Raum", "nachteilsausgleich", False, None, True),
    ("Pausen/Bewegungspausen", "nachteilsausgleich", False, None, True),
    ("Vergrößerte Schrift/Lesehilfe", "nachteilsausgleich", False, None, True),
    ("Laptop/Tablet erlaubt", "nachteilsausgleich", False, None, True),
    ("ADHS", "sonstiges", False, None, False),
    ("Körperliche Behinderung (k)", "sonstiges", False, None, False),
    ("Geistige Behinderung (g)", "sonstiges", False, None, False),
    ("Förderbedarf Lernen", "foerderplan", False, None, False),
    ("Schulbegleitung", "schulbegleitung", False, None, False),
]


def _rewrap(db) -> int:
    from .. import crypto
    return sum(crypto.rewrap_column(db, StudentSupport, c) for c in ("title_enc", "details_enc", "aids_enc"))


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("student_support", _rewrap)


_register()
