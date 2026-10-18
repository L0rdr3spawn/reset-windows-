"""Zugangsbriefe (§11.3): kurzlebige Stapel mit Startpasswörtern (Tabelle ``letter_batches``).

Ein Stapel entsteht beim Anlegen von Konten bzw. beim Erzeugen neuer Startpasswörter und hält die Einträge (Konto,
Name, Klasse, Startpasswort, bei Eltern die Kinder) **nur verschlüsselt** (``crypto.encrypt_text``, AAD
``letter_batches:<id>``) bis ``expires_at`` (Standard 60 min, ``SM_LETTER_BATCH_MINUTES``). Danach löscht ihn die
Wartung bzw. der nächste Zugriff. Zugriff hat nur die anlegende Person (oder die Rolle admin).

``account_initial_passwords`` vermerkt je Konto, dass das aktuelle Passwort ein **Startpasswort** ist: nur dessen
Hash (Kopie des Konto-Hashs zum Zeitpunkt der Vergabe) und die Frist (``expires_at``, Standard 14 Tage). Das Klartext-
Passwort wird nie aufbewahrt; nach Ablauf lässt sich das Startpasswort nicht mehr verwenden (neues erzeugen). Die Zeile
verschwindet beim Passwortwechsel und beim Löschen des Kontos.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class LetterBatch(Base):
    __tablename__ = "letter_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)                 # UUID
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True,
                                                      index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    count: Mapped[int] = mapped_column(Integer, default=0)
    data_enc: Mapped[str] = mapped_column(Text, default="")                       # verschlüsselt (SM1…)


class AccountInitialPassword(Base):
    """Das Passwort dieses Kontos ist ein Startpasswort mit Frist (nur Hash, kein Klartext – S-06)."""
    __tablename__ = "account_initial_passwords"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), default="")           # Hash des Startpassworts
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): Stapel neu verpacken."""
    from .. import crypto

    crypto.register_rewrap("letter_batches.data_enc",
                           lambda db: crypto.rewrap_column(db, LetterBatch, "data_enc"))


_register_rewrap()
