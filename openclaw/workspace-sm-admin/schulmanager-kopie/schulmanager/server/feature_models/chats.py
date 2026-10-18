"""Chats (Einzel-, Gruppen- und Klassenchats) mit Ende-zu-Ende-Verschlüsselung.

Der Server sieht keine Inhalte: jede Nachricht ist im Browser mit einem zufälligen Schlüssel verschlüsselt
(XSalsa20-Poly1305, ``nacl.secretbox``); dieser Schlüssel liegt je **Gerät** jedes Mitglieds mit dessen öffentlichem
Schlüssel verpackt vor (X25519 + XSalsa20-Poly1305, ``nacl.box``, vom Absendergerät signiert/authentisiert). Die
privaten Schlüssel verlassen das Gerät nie. Der Server speichert nur Chiffrate, Mitglieder und Zeitpunkte.

Chat-Namen sind Server-seitig verschlüsselt (AAD ``chats.title:<id>``) – sie müssen Mitgliedern auf neuen Geräten
angezeigt werden können. Meldungen (``ChatReport``) enthalten den von der meldenden Person freiwillig mitgeschickten
Klartext, ebenfalls Server-seitig verschlüsselt.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, LargeBinary, String, Text, UniqueConstraint, false, true
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class ChatDevice(Base):
    """Ein Browser/Gerät eines Kontos mit seinem öffentlichen Schlüssel (X25519, Base64)."""
    __tablename__ = "chat_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    public_key: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # device = Browser/Gerät; archive = Wiederherstellungsschlüssel des Kontos (privater Teil nur im Passwort-Backup)
    kind: Mapped[str] = mapped_column(String(10), default="device", server_default="device")
    # von einem anderen eigenen Gerät als „bekannt“ bestätigt (None = noch unbekannt → Hinweis an die anderen Geräte)
    acked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ChatLinkRequest(Base):
    """Anfrage eines neuen Geräts, den Verlauf von einem eingerichteten Gerät desselben Kontos zu erhalten.
    Kurzlebig; der Code dient nur dem Auffinden – die Freigabe erfolgt nach Vergleich des Fingerabdrucks."""
    __tablename__ = "chat_link_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    device_id: Mapped[int] = mapped_column(Integer, index=True)
    code: Mapped[str] = mapped_column(String(12), index=True)
    status: Mapped[str] = mapped_column(String(10), default="pending")     # pending | approved | cancelled
    approved_by_device_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ChatKeyBackup(Base):
    """Optionales Wiederherstellungs-Backup: der private Archivschlüssel des Kontos, im Browser mit einem aus
    Passwort/Code abgeleiteten Schlüssel verschlüsselt (``blob`` ist für den Server undurchsichtig)."""
    __tablename__ = "chat_key_backups"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    archive_device_id: Mapped[int] = mapped_column(Integer)
    blob: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), default="group")          # direct | group
    title_enc: Mapped[str] = mapped_column(Text, default="")
    direct_key: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, unique=True)
    only_admins_post: Mapped[bool] = mapped_column(Boolean, default=False)   # = (post_mode == "admins")
    # Wer schreiben darf: all (alle Mitglieder) | admins (nur Admins, z. B. Lehrkraft-Chat, Schüler lesen nur)
    # | selected (Admins und Mitglieder mit ``can_post``)
    post_mode: Mapped[str] = mapped_column(String(10), default="all", server_default="all")
    # Chat wurde bei der Übernahme aus dem Postfach angelegt (Migration 0030, ``chat_migration``)
    postfach_import: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    @property
    def title_aad(self) -> str:
        return f"chats.title:{self.id}"


class ChatMember(Base):
    __tablename__ = "chat_members"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_chat_members_chat_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # neue Mitglieder sehen keine älteren Nachrichten (wie bei Signal)
    first_message_id: Mapped[int] = mapped_column(Integer, default=0)
    last_read_id: Mapped[int] = mapped_column(Integer, default=0)
    muted: Mapped[bool] = mapped_column(Boolean, default=False)
    # je Person: archiviert (aus der Liste; kommt bei neuer Nachricht zurück, außer stumm) und Schreibrecht
    # (gilt bei ``Chat.post_mode == "selected"``)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    can_post: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, index=True)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sender_device_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nonce: Mapped[str] = mapped_column(String(40), default="")
    ciphertext: Mapped[str] = mapped_column(Text, default="")
    reply_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Systemhinweis („X hat Y hinzugefügt“) – kein Nutzerinhalt, daher Klartext
    system_text: Mapped[str] = mapped_column(String(400), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Aus dem Postfach übernommene Nachricht (Migration 0030): Text bleibt serverseitig verschlüsselt (das Chiffrat
    # der Original-Nachricht, AAD ``messages.body:<Unterhaltung>:<Nachricht>`` aus den beiden Quell-IDs). Eine
    # Markierungsnachricht („übernommen aus dem Postfach“) hat nur ``legacy_source_conversation_id``.
    legacy_body_enc: Mapped[str] = mapped_column(Text, default="", server_default="")
    legacy_source_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True, index=True)
    legacy_source_conversation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    @property
    def legacy_aad(self) -> str:
        return f"messages.body:{self.legacy_source_conversation_id}:{self.legacy_source_message_id}"


class ChatMessageKey(Base):
    """Nachrichtenschlüssel, verpackt für ein Empfängergerät."""
    __tablename__ = "chat_message_keys"
    __table_args__ = (UniqueConstraint("message_id", "device_id", name="uq_chat_message_keys_message_device"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, index=True)
    device_id: Mapped[int] = mapped_column(Integer, index=True)
    nonce: Mapped[str] = mapped_column(String(40))
    wrapped: Mapped[str] = mapped_column(String(120))
    # Gerät, das den Schlüssel nachträglich verpackt hat (Verknüpfung/Wiederherstellung); leer = Absendergerät
    wrapper_device_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class ChatReport(Base):
    __tablename__ = "chat_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, index=True)
    message_id: Mapped[int] = mapped_column(Integer, index=True)
    reporter_id: Mapped[int] = mapped_column(Integer)
    sender_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reason_enc: Mapped[str] = mapped_column(Text, default="")
    content_enc: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")         # open | dismissed | removed
    resolved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    def aad(self, field: str) -> str:
        return f"chat_reports.{field}:{self.id}"


class ChatAttachment(Base):
    """Bild/GIF einer Chat-Nachricht: **im Browser verschlüsseltes** Blob (Schlüssel steht nur in der verschlüsselten
    Nachricht). Der Server sieht weder Inhalt noch Dateityp. ``message_id`` ist leer, bis die Nachricht gesendet wurde
    (lose Uploads verfallen nach 24 h)."""
    __tablename__ = "chat_attachments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, index=True)
    uploader_id: Mapped[int] = mapped_column(Integer, index=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ChatReportImage(Base):
    """Bild, das die meldende Person freiwillig für die Moderation mitschickt (Server-seitig verschlüsselt)."""
    __tablename__ = "chat_report_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(Integer, index=True)
    mime: Mapped[str] = mapped_column(String(40), default="")
    data_enc: Mapped[bytes] = mapped_column(LargeBinary)

    def aad(self) -> str:
        return f"chat_report_images.data:{self.id}"


def _rewrap(db) -> int:
    from .. import crypto
    return (crypto.rewrap_column(db, Chat, "title_enc") + crypto.rewrap_column(db, ChatMessage, "legacy_body_enc") + crypto.rewrap_column(db, ChatReport, "reason_enc")
            + crypto.rewrap_column(db, ChatReport, "content_enc")
            + crypto.rewrap_column(db, ChatReportImage, "data_enc", batch=20))


def _register() -> None:
    try:
        from .. import crypto
    except ImportError:  # pragma: no cover
        return
    crypto.register_rewrap("chats", _rewrap)


_register()
