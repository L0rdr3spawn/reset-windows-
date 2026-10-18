"""Internes Postfach (ARCHITECTURE.md §9.5, Agent Postfach): Tabellen für Unterhaltungen und Nachrichten.

Verschlüsselung (``crypto.encrypt_text``, Spalten ``*_enc``, nie Klartext in der Datenbank):

* ``conversations.subject_enc`` – AAD ``conversations.subject:<conversation_id>``
* ``messages.body_enc`` – AAD ``messages.body:<conversation_id>:<message_id>`` (bindet die Nachricht an ihre
  Unterhaltung: verschobene oder vertauschte Chiffrate werden beim Lesen als Manipulation erkannt)
* ``message_reports.reason_enc`` / ``resolution_enc`` – AAD ``message_reports.<feld>:<report_id>``
* ``message_drafts.data_enc`` (JSON des Entwurfs) – AAD ``message_drafts.data:<user_id>:<draft_id>``
* ``message_user_settings.suspension_reason_enc`` – AAD ``message_user_settings.suspension_reason:<user_id>``

Die Absender-ID gehört bewusst **nicht** zum AAD: sie wird beim Löschen eines Kontos per ``ON DELETE SET NULL``
geleert (sonst wären die Nachrichten danach unlesbar, und SQLite könnte die ID neu vergeben).

Anhänge liegen verschlüsselt in der Dateiablage (``stored_files``, ``ref_type="message"``, ``ref_id`` =
Nachrichten-ID; Entwürfe ``ref_type="message_draft"``). Schlüsselrotation: ``crypto.register_rewrap("messages", …)``
(``cli rotate-keys``) wrappt alle Spalten oben neu.

Ungelesen-Zähler: ``conversation_participants.last_read_id`` (höchste gelesene Nachrichten-ID). „Für mich löschen“
setzt ``deleted`` und ``cleared_id`` (ältere Nachrichten bleiben für diese Person ausgeblendet; eine neue Nachricht holt
die Unterhaltung zurück in den Posteingang).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow

CONVERSATION_KINDS = ("direct", "group", "broadcast")
REPLY_MODES = ("all", "sender", "none")
REPORT_STATUSES = ("offen", "erledigt", "abgelehnt")
REPORT_CATEGORIES = ("belaestigung", "beleidigung", "bedrohung", "spam", "unangemessen", "sonstiges")


class Conversation(Base):
    """Unterhaltung: ``direct`` (zwei Personen), ``group`` (mehrere Einzelpersonen), ``broadcast`` (Rundschreiben an
    Gruppen, nur mit ``messages.broadcast``). ``parent_id`` verweist bei privaten Antworten auf ein Rundschreiben
    (``allow_replies = "sender"``) auf das Rundschreiben."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_enc: Mapped[str] = mapped_column(Text, default="")                  # verschlüsselt (SM1…) oder leer
    kind: Mapped[str] = mapped_column(String(20), default="direct")
    allow_replies: Mapped[str] = mapped_column(String(10), default="all")      # all|sender|none
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                      index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"),
                                                     nullable=True, index=True)
    # Zielgruppen eines Rundschreibens (nur Bezeichnungen, keine Namen): [{"kind","ref","label"}]
    audience: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    # Externe E-Mail-Beteiligte: [{"email","name","role": to|cc|bcc|from}] (Migration 0009)
    external: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    # Verbundenes E-Mail-Konto, über das die Unterhaltung mit Externen läuft bzw. empfangen wurde
    # (Fremdschlüssel nur außerhalb von SQLite, siehe Migration 0009)
    mail_account_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_id: Mapped[int] = mapped_column(Integer, default=0)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    # Trennung Postfach/Chats (Migration 0030): ``mail_native`` = nach der Trennung als Brief angelegt (bleibt im
    # Postfach, wird nie zum Chat übernommen); ältere Zeilen haben ``False`` und werden von
    # ``chat_migration`` geprüft. ``migrated_chat_id`` = Chat, in den der Verlauf kopiert wurde (die Unterhaltung
    # bleibt unverändert erhalten, erscheint aber nicht mehr im Postfach).
    mail_native: Mapped[bool] = mapped_column(Boolean, default=True, server_default=false())
    migrated_chat_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    @property
    def subject_aad(self) -> str:
        return f"conversations.subject:{self.id}"


class ConversationParticipant(Base):
    """Teilnahme eines Kontos an einer Unterhaltung (Lesestand, Archiv, Stummschalten, „für mich gelöscht“)."""
    __tablename__ = "conversation_participants"

    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"),
                                                 primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_read_id: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    muted: Mapped[bool] = mapped_column(Boolean, default=False)
    cleared_id: Mapped[int] = mapped_column(Integer, default=0)          # Nachrichten bis zu dieser ID ausgeblendet
    has_incoming: Mapped[bool] = mapped_column(Boolean, default=False)   # mind. eine Nachricht anderer (Posteingang)
    has_sent: Mapped[bool] = mapped_column(Boolean, default=False)       # mind. eine eigene Nachricht (Gesendet)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # An/CC/BCC (Migration 0009): BCC-Empfangende sehen nur sich selbst, die anderen sehen sie nicht
    recipient_role: Mapped[str] = mapped_column(String(4), default="to", server_default="to")


Index("ix_conversation_participants_user_folder", ConversationParticipant.user_id, ConversationParticipant.deleted,
      ConversationParticipant.archived)


class Message(Base):
    """Nachricht. ``body_enc`` verschlüsselt; ``removed_at`` = von der Moderation ausgeblendet (Inhalt bleibt als
    Beleg verschlüsselt erhalten, bis die Aufbewahrungsfrist abläuft)."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                     index=True)
    body_enc: Mapped[str] = mapped_column(Text, default="")
    attachment_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    removed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # E-Mail (Migration 0009): Absender einer eingegangenen E-Mail, Message-ID (Zuordnung von Antworten),
    # Versandstatus an externe Adressen {"status": sent|failed|pending, "error", "at", "to": [..]}
    external_from: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    external_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    mail_message_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    delivery: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    @property
    def body_aad(self) -> str:
        return f"messages.body:{self.conversation_id}:{self.id}"


Index("ix_messages_conversation_order", Message.conversation_id, Message.id)
Index("ix_messages_sender_time", Message.sender_id, Message.created_at)


class MessageReport(Base):
    """Meldung einer Nachricht an die Moderation (``messages.moderate``). Begründung und Vermerk verschlüsselt."""
    __tablename__ = "message_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    reporter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
                                                       index=True)
    category: Mapped[str] = mapped_column(String(20), default="sonstiges")
    reason_enc: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="offen", index=True)   # offen|erledigt|abgelehnt
    handled_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_enc: Mapped[str] = mapped_column(Text, default="")
    actions: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)       # z. B. ["removed", "suspended"]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class UserBlock(Base):
    """``user_id`` nimmt keine Nachrichten von ``blocked_user_id`` mehr an."""
    __tablename__ = "user_blocks"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blocked_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True,
                                                 index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MessageUserSettings(Base):
    """Postfach-Einstellungen eines Kontos (E-Mail-Hinweis) und Sperre durch die Moderation."""
    __tablename__ = "message_user_settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_notify: Mapped[bool] = mapped_column(Boolean, default=True)
    suspended_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    suspended_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    suspension_reason_enc: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class MessageDraft(Base):
    """Entwurf (neue Nachricht oder Antwort, ``conversation_id``) – Inhalt als verschlüsseltes JSON."""
    __tablename__ = "message_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"),
                                                           nullable=True, index=True)
    data_enc: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


# (Modell, Spalte) aller verschlüsselten Spalten – für die Schlüsselrotation und den Klartext-Test
ENCRYPTED_COLUMNS: tuple[tuple[type, str], ...] = (
    (Conversation, "subject_enc"),
    (Message, "body_enc"),
    (MessageReport, "reason_enc"),
    (MessageReport, "resolution_enc"),
    (MessageDraft, "data_enc"),
    (MessageUserSettings, "suspension_reason_enc"),
)


def _rewrap_all(db) -> int:
    """Schlüsselrotation (``cli rotate-keys``): alle Tokens des Postfachs mit dem aktiven Master-Schlüssel neu
    wrappen (die Nutzdaten und damit das AAD bleiben unverändert)."""
    from .. import crypto

    return sum(crypto.rewrap_column(db, model, column) for model, column in ENCRYPTED_COLUMNS)


def _register_rewrap() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover - Basisdienst fehlt
        return
    crypto.register_rewrap("messages", _rewrap_all)


_register_rewrap()
