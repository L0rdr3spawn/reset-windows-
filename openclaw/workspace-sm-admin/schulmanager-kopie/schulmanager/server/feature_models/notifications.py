"""Benachrichtigungszentrale (``docs/BENACHRICHTIGUNGEN.md``) – Migration 0041_notifications.

Tabellen
--------
* ``notifications`` – eine Benachrichtigung für genau ein Konto (``user_id``). Titel und Text liegen nur
  **verschlüsselt** (``title_enc``/``body_enc``, AAD ``notifications.<feld>:<id>``); beide enthalten laut Vorgabe keine
  sensiblen Einzelheiten („Neue Krankmeldung“ statt Diagnose). ``student_id`` = Kind, um das es geht (Eltern sehen es je
  Kind). ``dedupe_key`` verhindert Doppelte je Konto. ``mail_state``: ``""`` keine Mail, ``sent`` sofort versandt,
  ``later`` wartet auf das Ende der Ruhezeit, ``digest`` wartet auf die tägliche Zusammenfassung, ``digested`` darin
  versandt.
* ``notification_prefs`` – Einstellung je Konto und Ereignisart (``mode``: ``aus|app|mail``).
* ``notification_user_settings`` – je Konto: tägliche Zusammenfassung, Ruhezeiten (nur für E-Mails).
* ``notification_school`` – Schulvorgaben je Ereignisart (Standard-``mode``, ``locked`` = Pflicht, nicht änderbar).
* ``notification_config`` – Schlüssel/Wert für Schuleinstellungen (z. B. ``retention_days``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow
from .channels import EncryptedText


class Notification(EncryptedText, Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "dedupe_key", name="uq_notifications_user_id"),
                      Index("ix_notifications_user_read", "user_id", "read_at"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    title_enc: Mapped[str] = mapped_column(Text, default="")
    body_enc: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[str] = mapped_column(String(300), default="")
    student_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    ref: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mail_state: Mapped[str] = mapped_column(String(10), default="")


class NotificationPref(Base):
    __tablename__ = "notification_prefs"
    __table_args__ = (UniqueConstraint("user_id", "kind", name="uq_notification_prefs_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    mode: Mapped[str] = mapped_column(String(10), default="app")


class NotificationUserSettings(Base):
    __tablename__ = "notification_user_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    digest: Mapped[bool] = mapped_column(Boolean, default=False)
    digest_sent_on: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    quiet_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_from: Mapped[str] = mapped_column(String(5), default="21:00")
    quiet_to: Mapped[str] = mapped_column(String(5), default="07:00")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class NotificationSchool(Base):
    __tablename__ = "notification_school"

    kind: Mapped[str] = mapped_column(String(40), primary_key=True)
    mode: Mapped[str] = mapped_column(String(10), default="app")
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class NotificationConfig(Base):
    __tablename__ = "notification_config"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), default="")


ENCRYPTED_COLUMNS = ((Notification, "title_enc"), (Notification, "body_enc"))


def _register_rewrap() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    for model, column in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"{model.__tablename__}.{column}",
                               lambda db, model=model, column=column: crypto.rewrap_column(db, model, column))


_register_rewrap()
