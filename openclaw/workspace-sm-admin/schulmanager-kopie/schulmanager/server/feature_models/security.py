"""Sicherheits-Einstellungen der Schule (S-04/S-06/S-17): Schlüssel/Wert-Tabelle ``security_settings``.

Werte sind JSON; gültige Schlüssel und Standardwerte stehen in ``security_settings.py``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class SecuritySetting(Base):
    __tablename__ = "security_settings"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                                                      nullable=True)
