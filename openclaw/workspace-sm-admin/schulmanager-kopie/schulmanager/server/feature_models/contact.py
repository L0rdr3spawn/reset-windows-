"""Kontakt & Wiederherstellung (Erweiterung 4, §11.2): bestätigte E-Mail/Handynummer und Einmal-Codes.

``user_contacts`` (ein Eintrag je Konto, ``user_id`` = Primärschlüssel):

* Die E-Mail-Adresse selbst bleibt in ``users.email``. ``email_verified_value`` ist die bestätigte Adresse in
  Kleinschreibung – die Adresse gilt genau dann als bestätigt, wenn sie ``lower(users.email)`` entspricht (ändert
  jemand ``users.email`` auf anderem Weg, ist sie automatisch unbestätigt).
* Handynummer nur **verschlüsselt** (``phone_enc``, E.164, AAD ``user_contacts.phone:<user_id>``) und als HMAC
  (``phone_hash`` mit ``SM_SECRET_KEY``) zum Suchen („Passwort vergessen“ mit Nummer als Kennung).

``auth_codes`` (Einmal-Codes, Links und Rate-Limit-Protokoll):

* ``purpose``: ``verify_email`` | ``verify_phone`` | ``reset`` (6-stelliger Code, bei E-Mail zusätzlich Link-Token) |
  ``reset_token`` (kurzlebiges Token nach erfolgreicher Prüfung, für ``/auth/password-reset/confirm``) |
  ``rl_reset`` / ``rl_fail`` (nur Zähler für das Rate-Limit: Anfrage bzw. Fehlversuch, ohne Code).
* Code und Token nur als HMAC (``security.hash_token``), das Ziel (neue Adresse/Nummer) verschlüsselt
  (``target_enc``, AAD ``auth_codes.target:<id>``). ``ident_hash`` = HMAC der eingegebenen Kennung (Rate-Limit je
  Kennung, auch für unbekannte Kennungen). Ablauf ``SM_AUTH_CODE_MINUTES`` (15), höchstens 5 Versuche je Code.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

PURPOSES = ("verify_email", "verify_phone", "reset", "reset_token", "rl_reset", "rl_fail")
CHANNELS = ("email", "sms")


class UserContact(Base):
    __tablename__ = "user_contacts"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_verified_value: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    phone_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)             # verschlüsselt (SM1…)
    phone_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True,
                                                   index=True)
    purpose: Mapped[str] = mapped_column(String(20))
    channel: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    code_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    token_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    target_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)            # verschlüsselt (SM1…)
    ident_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


Index("ix_auth_codes_user_purpose", AuthCode.user_id, AuthCode.purpose, AuthCode.created_at)
Index("ix_auth_codes_ip_purpose", AuthCode.ip, AuthCode.purpose, AuthCode.created_at)


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): Nummern, Code-Ziele und verschlüsselte Outbox-Nachrichten."""
    from .. import crypto
    from ..db_models import NotificationOutbox

    crypto.register_rewrap("user_contacts.phone_enc", lambda db: crypto.rewrap_column(db, UserContact, "phone_enc"))
    crypto.register_rewrap("auth_codes.target_enc", lambda db: crypto.rewrap_column(db, AuthCode, "target_enc"))
    # Klartext-JSON anderer Outbox-Arten (Webhooks) ist kein Token und bleibt unverändert
    crypto.register_rewrap("notifications_outbox.payload",
                           lambda db: crypto.rewrap_column(db, NotificationOutbox, "payload"))


_register_rewrap()
