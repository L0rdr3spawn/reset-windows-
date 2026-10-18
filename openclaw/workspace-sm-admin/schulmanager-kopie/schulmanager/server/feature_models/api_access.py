"""Nutzungsprotokoll der API-Zugänge (``api_token_log``; docs/API-ZUGAENGE.md).

Je Zugang werden die letzten ``api_scopes.LOG_KEEP`` Anfragen aufbewahrt (Zeit, Methode, Pfad ohne Query, Bereich,
Ergebnis, IP) – keine Antwortinhalte, keine Personendaten."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from schulmanager.server.db import Base, utcnow


class ApiTokenLog(Base):
    __tablename__ = "api_token_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("api_tokens.id", ondelete="CASCADE"), index=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    method: Mapped[str] = mapped_column(String(8), default="GET")
    path: Mapped[str] = mapped_column(String(200), default="")
    area: Mapped[str] = mapped_column(String(32), default="")
    outcome: Mapped[str] = mapped_column(String(40), default="ok")   # ok | ip_denied | rate_limited | area_denied …
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
