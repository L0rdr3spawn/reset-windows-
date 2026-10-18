"""Verbundene E-Mail-Konten (Google, Apple/iCloud, Microsoft/Outlook, GMX, Web.de, T-Online, Yahoo, eigener Server).

Über ein verbundenes Konto verschickt das Postfach Nachrichten an externe E-Mail-Adressen, und eingehende E-Mails
des Kontos erscheinen im Postfach (``server/mailbridge.py``). Zugangsdaten (App-Passwort bzw. OAuth-Token) liegen nur
verschlüsselt in ``secret_enc`` (AAD ``mail_accounts.secret:<id>``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

PROVIDERS = ("google", "apple", "microsoft", "gmx", "webde", "tonline", "yahoo", "custom")
AUTH_KINDS = ("password", "oauth2")


class MailAccount(Base):
    __tablename__ = "mail_accounts"
    __table_args__ = (UniqueConstraint("user_id", "email", name="uq_mail_accounts_user_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(20), default="custom")
    email: Mapped[str] = mapped_column(String(254))
    display_name: Mapped[str] = mapped_column(String(200), default="")
    auth: Mapped[str] = mapped_column(String(10), default="password")          # password|oauth2
    username: Mapped[str] = mapped_column(String(254), default="")
    secret_enc: Mapped[str] = mapped_column(Text, default="")                    # verschlüsseltes JSON
    imap_host: Mapped[str] = mapped_column(String(200), default="")
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    smtp_host: Mapped[str] = mapped_column(String(200), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_security: Mapped[str] = mapped_column(String(10), default="starttls")  # ssl|starttls
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    uidvalidity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_uid: Mapped[int] = mapped_column(Integer, default=0)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def secret_aad(self) -> str:
        return f"mail_accounts.secret:{self.id}"


def _rewrap(db) -> int:
    from .. import crypto
    return crypto.rewrap_column(db, MailAccount, "secret_enc")


def _register_rewrap() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("mail_accounts", _rewrap)


_register_rewrap()
