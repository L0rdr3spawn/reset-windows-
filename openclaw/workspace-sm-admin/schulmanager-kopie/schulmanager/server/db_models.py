"""Relationale Tabellen (SQLAlchemy 2, typisierte ``Mapped``-Spalten).

Zeitstempel: naive UTC (``db.utcnow``). Datumsfelder (Krankmeldungen, Mitteilungen):
ISO-Strings ``YYYY-MM-DD`` wie im Planungsmodell. Jede Schemaänderung braucht eine
neue Alembic-Revision in ``server/migrations/versions``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, utcnow

ROLES = ("admin", "schulleitung", "abteilungsleitung", "planer", "sekretariat", "lehrer", "hausmeister",
         "schulbegleitung", "schueler", "eltern", "monitor", "zuschauer")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(20), index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)   # veraltet: Klartext vor Migration 0045, danach leer
    totp_secret_enc: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # verschlüsselt (crypto, AAD users.totp_secret:<id>)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    teacher_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    site: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    ical_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)   # nur HMAC-Hash (hash_token)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Erweiterungen gegenüber §6 (siehe AGENT_NOTES):
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    adult: Mapped[bool] = mapped_column(Boolean, default=False)          # volljährige Schüler: Krankmeldung selbst
    # Volljährige Schüler/innen: Eltern dürfen die Kursräume sehen (Freigabe des Kontos, Migration 0008)
    oidc_sub: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)


class UserSession(Base):
    """Anmeldesitzung (Cookie ``sm_session``). Gespeichert wird nur der Hash des Tokens."""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)


class ApiToken(Base):
    """API-Token (``Authorization: Bearer``), nur als Hash gespeichert."""
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prefix: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # API-Zugang mit Umfang (docs/API-ZUGAENGE.md): ``scope`` = None → persönliches Token wie bisher (alles, was das
    # Konto darf); sonst nur die öffentliche API ``/api/v1/open/…`` mit Bereichen und Filtern (``api_scopes.py``).
    purpose: Mapped[str] = mapped_column(String(300), default="", server_default="")
    scope: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_allow: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)       # Anfragen pro Minute
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80))
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class ParentLink(Base):
    """Eltern-Konto ↔ Kind (``Student.id`` im Planungsdokument)."""
    __tablename__ = "parent_links"
    __table_args__ = (UniqueConstraint("parent_user_id", "student_id", name="uq_parent_links_parent_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)


class RoleOverride(Base):
    """Schulspezifische Abweichung vom Standard der Rollenrechte (``permissions.effective_rights``).

    ``granted`` erteilt/entzieht das Recht; ``scope``: ``None`` = Standardumfang der Rolle, ``all`` =
    uneingeschränkt, sonst z. B. ``own_classes``. Feste Mindestregeln gelten immer zusätzlich (im Code)."""
    __tablename__ = "role_overrides"

    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    permission: Mapped[str] = mapped_column(String(60), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, default=True)
    scope: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_by: Mapped[str] = mapped_column(String(80), default="")


class Branch(Base):
    """Schulzweig/Abteilung: Klassen über Standort, Klassenstufe oder einzelne Klassen (Abteilungsleitung)."""
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    sites: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    grades: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)
    class_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)


class UserBranch(Base):
    """Zuordnung Konto (Abteilungsleitung) ↔ Zweig."""
    __tablename__ = "user_branches"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                   index=True)
    username: Mapped[str] = mapped_column(String(80), default="")
    action: Mapped[str] = mapped_column(String(80), index=True)
    target: Mapped[str] = mapped_column(String(200), default="")
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class SchoolVersion(Base):
    """Version des Planungsdokuments (``School`` als zlib-komprimiertes JSON)."""
    __tablename__ = "school_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message: Mapped[str] = mapped_column(String(500), default="")
    scope: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    data: Mapped[bytes] = mapped_column(LargeBinary)
    restored_from: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Restore/Undo-Quelle


class Announcement(Base):
    """Mitteilung (Backend-Features)."""
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author_name: Mapped[str] = mapped_column(String(200), default="")
    audience: Mapped[str] = mapped_column(String(20), default="all")          # all|staff|classes
    audience_roles: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    class_ids: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    site: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    valid_from: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    valid_to: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal")       # normal|wichtig
    monitor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class StudentAbsence(Base):
    """Krankmeldung/Abwesenheit eines Schülers (Backend-Features)."""
    __tablename__ = "student_absences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    date_from: Mapped[str] = mapped_column(String(10), index=True)
    date_to: Mapped[str] = mapped_column(String(10))
    periods: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    # gemeldet|teilweise (telefonisch gemeldet, schriftliche Entschuldigung fehlt)|entschuldigt|unentschuldigt
    status: Mapped[str] = mapped_column(String(20), default="gemeldet")
    note: Mapped[str] = mapped_column(Text, default="")
    # Fehlzeiten (Migration 0010): krank|verspaetung|frueh|fehlt, Minuten (zu spät/früher gegangen),
    # Herkunft online|telefon|schriftlich|lehrkraft und wer entschuldigt hat
    kind: Mapped[str] = mapped_column(String(20), default="krank", server_default="krank", index=True)
    minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="online", server_default="online")
    excused_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excused_by_name: Mapped[str] = mapped_column(String(200), default="", server_default="")
    excused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # aus dem Klassenbuch erfasst (Migration 0012) – wird beim erneuten Speichern der Stunde angepasst
    register_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    reported_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reported_by_name: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class NotificationOutbox(Base):
    """Ausgehende Benachrichtigungen (Webhook/E-Mail) mit Retry (Backend-Features)."""
    __tablename__ = "notifications_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))                              # webhook|email
    target: Mapped[str] = mapped_column(String(500))
    subject: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    payload: Mapped[str] = mapped_column(Text, default="")                     # JSON-Body bzw. Mailtext
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|sending|sent|failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


Index("ix_login_attempts_user_time", LoginAttempt.username, LoginAttempt.created_at)
Index("ix_login_attempts_ip_time", LoginAttempt.ip, LoginAttempt.created_at)

ALL_TABLES = [User, UserSession, ApiToken, LoginAttempt, ParentLink, AuditLog, SchoolVersion,
              Announcement, StudentAbsence, NotificationOutbox]


# Feature-Modelle (Erweiterung 2) mitregistrieren – siehe feature_models/__init__.py
from schulmanager.server import feature_models as _feature_models  # noqa: E402

_feature_models.load_all()


def _register_user_rewrap() -> None:
    """Schlüsselrotation (``cli rotate-keys``): TOTP-Geheimnisse (S-09) neu verpacken."""
    from schulmanager.server import crypto

    crypto.register_rewrap("users.totp_secret_enc", lambda db: crypto.rewrap_column(db, User, "totp_secret_enc"))


_register_user_rewrap()
