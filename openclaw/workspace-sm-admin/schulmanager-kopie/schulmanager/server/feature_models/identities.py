"""Verbundene Anbieter-Konten und Anbieter-Einrichtung (Erweiterung 4, docs/ARCHITECTURE.md §11.4).

* ``user_identities`` – Verknüpfung eines Schulmanager-Kontos mit einem Konto bei Microsoft, Apple, Google oder dem
  Schulkonto (``oidc``). ``subject`` ist die stabile Kennung beim Anbieter (``sub``; beim Schulkonto
  ``"<issuer>|<sub>"`` wie früher ``users.oidc_sub``, beim Test-Anbieter ``mock:<hash>``). ``subject`` NULL = vom
  Admin/Sekretariat **vorgemerkte** Verknüpfung: beim ersten Anmelden mit genau dieser, vom Anbieter bestätigten
  E-Mail wird sie übernommen. Je Konto und Anbieter höchstens eine Zeile; je Anbieter-Konto höchstens ein Konto.
* ``sso_providers`` – Einrichtung der Anbieter durch die Administration. Client-Secret und Apple-Schlüssel
  (``.p8``) nur **verschlüsselt** (``crypto.encrypt_text``, AAD ``sso_providers.<feld>:<anbieter>``).
  Umgebungsvariablen (``SM_SSO_*``, ``SM_OIDC_*``) haben Vorrang (siehe ``server/sso_providers.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class UserIdentity(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_user_identities_provider_subject"),
        UniqueConstraint("user_id", "provider", name="uq_user_identities_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # NULL = vorgemerkt
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True, index=True)  # klein geschrieben
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class SsoProvider(Base):
    __tablename__ = "sso_providers"

    provider: Mapped[str] = mapped_column(String(20), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_secret_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # verschlüsselt (SM1…)
    tenant: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)          # Microsoft
    hosted_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # Google (hd)
    team_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)          # Apple
    key_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)           # Apple
    private_key_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)        # Apple .p8, verschlüsselt
    issuer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)          # allgemeines OIDC
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    allowed_domains: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)  # ["schule.de", …]
    auto_signin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())  # automatische Anmeldung
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


ENCRYPTED_COLUMNS = ("client_secret_enc", "private_key_enc")


def _register_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): Geheimnisse der Anbieter neu verpacken."""
    from .. import crypto

    for col in ENCRYPTED_COLUMNS:
        crypto.register_rewrap(f"sso_providers.{col}", lambda db, col=col: crypto.rewrap_column(db, SsoProvider, col))


_register_rewrap()
