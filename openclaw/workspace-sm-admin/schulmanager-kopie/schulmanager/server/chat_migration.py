"""Übernahme von Postfach-Unterhaltungen, die eigentlich Chats sind, nach „Chats & Gruppen“.

Kriterium (Postfach = Brief/E-Mail, Chats = Unterhaltung ohne Brief-Charakter):

* ``group`` (mehrere Einzelpersonen, „alle sehen alle“) → **Chat-Gruppe** (Betreff wird zum Gruppennamen),
* ``direct`` **ohne Betreff** → **Einzelchat**,

jeweils nur, wenn es kein Brief im engeren Sinn ist: keine externe E-Mail (``external``/``mail_account_id``), keine
private Antwort auf ein Rundschreiben (``parent_id``), kein Anhang in irgendeiner Nachricht (Chats kennen nur
Bilder/GIFs), keine Kopie/Blindkopie. ``direct`` mit Betreff, ``broadcast`` (Rundschreiben) und ``email`` bleiben im
Postfach. Unterhaltungen, die nach der Trennung angelegt wurden (``Conversation.mail_native``), werden nie übernommen.

Vorgehen (verlustfrei, wiederholbar):

* Die **Originale bleiben unverändert** in ``conversations``/``messages`` (Moderation und Meldungen verweisen weiter
  darauf); die Unterhaltung wird nur mit ``migrated_chat_id`` markiert und erscheint nicht mehr im Postfach.
* Die Nachrichten werden als ``chat_messages`` **kopiert**. Alte Nachrichten lassen sich serverseitig nicht in die
  Ende-zu-Ende-Verschlüsselung umpacken – sie behalten das serverseitig verschlüsselte Chiffrat der Originalnachricht
  (``legacy_body_enc``, AAD aus den Quell-IDs) und werden im Chat als „aus dem Postfach übernommen“ gezeigt. Alles
  Neue läuft Ende-zu-Ende.
* Je Person werden Lesestand, Archiv, Stumm und „für mich gelöscht“ (→ nicht Mitglied bzw. ältere Nachrichten
  ausgeblendet) übernommen. Mehrere Postfach-Einzelunterhaltungen derselben zwei Personen laufen in einem Einzelchat
  zusammen (Einzelchats sind je Paar eindeutig).
* ``migrated_chat_id``: ``NULL`` = noch nicht geprüft, ``0`` = geprüft und bleibt im Postfach (oder Rückweg
  genommen), ``> 0`` = Chat. Wiederholte Läufe fassen Erledigtes nicht erneut an und ergänzen höchstens fehlende
  Nachrichten.
* **Rückweg:** :func:`rollback` entfernt die kopierten Nachrichten (und einen leeren, bei der Übernahme angelegten
  Chat) und blendet das Original im Postfach wieder ein (``cli migrate-chats --rollback``). Ende-zu-Ende-Nachrichten,
  die inzwischen im Chat entstanden sind, bleiben dabei erhalten.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import crypto
from .db import session_scope
from .feature_models.chats import Chat, ChatMember, ChatMessage
from .feature_models.messages import Conversation, ConversationParticipant, Message

log = logging.getLogger("schulmanager.chat_migration")

Part = ConversationParticipant

KEEP = 0                      # migrated_chat_id: geprüft, bleibt im Postfach
MARKER_TEXT = ("Ab hier: aus dem Postfach übernommener Verlauf. Diese älteren Nachrichten sind serverseitig "
               "verschlüsselt (nicht Ende-zu-Ende); alles Neue ist Ende-zu-Ende-verschlüsselt.")


def _subject(conv: Conversation) -> Optional[str]:
    """Klartext-Betreff, ``None`` wenn nicht lesbar (dann nicht anfassen)."""
    if not conv.subject_enc:
        return ""
    try:
        return " ".join(crypto.decrypt_text(conv.subject_enc, conv.subject_aad).split())
    except Exception:  # noqa: BLE001
        return None


def classify(db: Session, conv: Conversation, msgs: list[Message], parts: list[Part]) -> tuple[Optional[str], str]:
    """``("direct"|"group"|None, Begründung)`` – wohin die Unterhaltung gehört."""
    if conv.kind not in ("direct", "group"):
        return None, f"Art {conv.kind}"
    if conv.external or conv.mail_account_id:
        return None, "externe E-Mail"
    if conv.parent_id:
        return None, "Antwort auf Rundschreiben"
    if any(m.external_from or m.mail_message_id or m.delivery for m in msgs):
        return None, "E-Mail-Nachricht"
    if any(m.attachment_ids for m in msgs):
        return None, "mit Anhängen"
    if any((p.recipient_role or "to") in ("cc", "bcc") for p in parts):
        return None, "Kopie/Blindkopie"
    subject = _subject(conv)
    if subject is None:
        return None, "Betreff nicht lesbar"
    if conv.kind == "direct":
        if subject:
            return None, "Brief mit Betreff"
        if len(parts) > 2:
            return None, "mehr als zwei Teilnehmende"
        return "direct", "Einzelunterhaltung ohne Betreff"
    return "group", "Gruppenunterhaltung"


def _names(db: Session, ids: list[int]) -> list[str]:
    from .db_models import User

    if not ids:
        return []
    rows = {u.id: (u.display_name or u.username) for u in db.scalars(select(User).where(User.id.in_(ids)))}
    return [rows[i] for i in ids if i in rows]


def _title(db: Session, conv: Conversation, subject: str, member_ids: list[int]) -> str:
    if subject:
        return subject[:80]
    names = _names(db, member_ids[:4])
    text = ", ".join(names[:3]) + (" …" if len(member_ids) > 3 else "")
    return (text or "Gruppe")[:80]


def _target_chat(db: Session, conv: Conversation, kind: str, parts: list[Part], subject: str) -> Chat:
    created_by = conv.created_by if conv.created_by and any(p.user_id == conv.created_by for p in parts) else None
    if kind == "direct":
        ids = sorted(p.user_id for p in parts)
        key = f"{ids[0]}:{ids[-1]}" if len(ids) == 2 else f"{ids[0]}:{ids[0]}"
        chat = db.scalar(select(Chat).where(Chat.direct_key == key))
        if chat is None:
            chat = Chat(kind="direct", title_enc="", direct_key=key, created_by=created_by, created_at=conv.created_at,
                        last_activity_at=conv.last_message_at, postfach_import=True)
            db.add(chat)
            db.flush()
        return chat
    chat = Chat(kind="group", title_enc="", created_by=created_by or (parts[0].user_id if parts else None),
                created_at=conv.created_at, last_activity_at=conv.last_message_at, postfach_import=True)
    db.add(chat)
    db.flush()
    members = [p.user_id for p in parts if not p.deleted]
    chat.title_enc = crypto.encrypt_text(_title(db, conv, subject, members), chat.title_aad)
    return chat


def _copy_messages(db: Session, conv: Conversation, chat: Chat, msgs: list[Message]) -> dict[int, int]:
    """Kopiert noch nicht übernommene Nachrichten; gibt ``{Quell-ID: Chat-Nachrichten-ID}`` aller zurück."""
    done = {sid: mid for sid, mid in db.execute(select(ChatMessage.legacy_source_message_id, ChatMessage.id).where(
        ChatMessage.legacy_source_conversation_id == conv.id, ChatMessage.legacy_source_message_id.is_not(None)))}
    marked = db.scalar(select(func.count(ChatMessage.id)).where(
        ChatMessage.legacy_source_conversation_id == conv.id, ChatMessage.legacy_source_message_id.is_(None))) or 0
    if not marked and msgs:
        db.add(ChatMessage(chat_id=chat.id, system_text=MARKER_TEXT, created_at=msgs[0].created_at,
                           legacy_source_conversation_id=conv.id))
        db.flush()
    for m in msgs:
        if m.id in done:
            continue
        row = ChatMessage(chat_id=chat.id, sender_id=m.sender_id, nonce="", ciphertext="", created_at=m.created_at,
                          deleted_at=m.removed_at, legacy_body_enc="" if m.removed_at else m.body_enc,
                          legacy_source_message_id=m.id, legacy_source_conversation_id=conv.id)
        db.add(row)
        db.flush()
        done[m.id] = row.id
    return done


def _mapped(mapping: dict[int, int], source_limit: int) -> int:
    """Höchste Chat-Nachrichten-ID einer Quell-Nachricht mit ID ≤ ``source_limit`` (0 = keine)."""
    return max((new for src, new in mapping.items() if src <= source_limit), default=0)


def _members(db: Session, chat: Chat, kind: str, conv: Conversation, parts: list[Part],
             mapping: dict[int, int]) -> None:
    present = {m.user_id: m for m in db.scalars(select(ChatMember).where(ChatMember.chat_id == chat.id))}
    fresh = not present
    for p in parts:
        if p.deleted:
            continue
        mem = present.get(p.user_id)
        if mem is None:
            mem = ChatMember(chat_id=chat.id, user_id=p.user_id, admin=(kind == "direct" or p.user_id == chat.created_by),
                             joined_at=p.joined_at, first_message_id=0, last_read_id=0, muted=bool(p.muted),
                             archived=bool(p.archived))
            db.add(mem)
            present[p.user_id] = mem
        else:
            mem.archived = mem.archived and bool(p.archived)   # in einem zusammengeführten Chat nicht verstecken
        mem.last_read_id = max(mem.last_read_id or 0, _mapped(mapping, p.last_read_id or 0))
        if p.cleared_id:
            mem.first_message_id = max(mem.first_message_id or 0, _mapped(mapping, p.cleared_id))
    if kind == "group" and fresh and present and not any(m.admin for m in present.values()):
        next(iter(present.values())).admin = True


def migrate_conversation(db: Session, conv: Conversation) -> dict[str, Any]:
    """Prüft/übernimmt eine Unterhaltung (im Aufrufer-Savepoint); setzt ``migrated_chat_id``."""
    msgs = list(db.scalars(select(Message).where(Message.conversation_id == conv.id).order_by(Message.id)))
    parts = list(db.scalars(select(Part).where(Part.conversation_id == conv.id).order_by(Part.joined_at, Part.user_id)))
    kind, why = classify(db, conv, msgs, parts)
    if kind is None or not parts or not msgs:
        conv.migrated_chat_id = KEEP
        return {"moved": False, "why": why if kind is None else "leer"}
    if all(p.deleted for p in parts):
        conv.migrated_chat_id = KEEP
        return {"moved": False, "why": "niemand sieht sie mehr"}
    subject = _subject(conv) or ""
    chat = db.get(Chat, conv.migrated_chat_id) if conv.migrated_chat_id and conv.migrated_chat_id > 0 else None
    new_chat = chat is None
    if chat is None:
        chat = _target_chat(db, conv, kind, parts, subject)
        new_chat = new_chat and chat.postfach_import and not db.scalar(
            select(func.count(ChatMessage.id)).where(ChatMessage.chat_id == chat.id))
    mapping = _copy_messages(db, conv, chat, msgs)
    _members(db, chat, kind, conv, parts, mapping)
    last = max((m.created_at for m in msgs), default=None)
    if last is not None and (chat.last_activity_at is None or chat.last_activity_at < last):
        chat.last_activity_at = last
    conv.migrated_chat_id = chat.id
    return {"moved": True, "kind": kind, "chat_id": chat.id, "messages": len(mapping), "new_chat": new_chat}


def migrate_postfach(db: Session, *, force: bool = False, conversation_ids: Optional[list[int]] = None,
                     dry_run: bool = False) -> dict[str, Any]:
    """Übernimmt alle geeigneten, noch nicht geprüften Postfach-Unterhaltungen. ``force`` prüft auch bereits
    geprüfte noch einmal (z. B. nach einem Rückweg); ``dry_run`` ändert nichts und zählt nur."""
    q = select(Conversation).where(Conversation.mail_native.is_(False), Conversation.kind.in_(("direct", "group")))
    if conversation_ids:
        q = q.where(Conversation.id.in_(conversation_ids))
    if not force:
        q = q.where(Conversation.migrated_chat_id.is_(None))
    result: dict[str, Any] = {"checked": 0, "moved": 0, "kept": 0, "errors": 0, "messages": 0, "chats": set(),
                              "reasons": {}}
    for conv in list(db.scalars(q.order_by(Conversation.id))):
        result["checked"] += 1
        if dry_run:
            msgs = list(db.scalars(select(Message).where(Message.conversation_id == conv.id)))
            parts = list(db.scalars(select(Part).where(Part.conversation_id == conv.id)))
            kind, why = classify(db, conv, msgs, parts)
            key = "wird Chat" if kind else why
            result["reasons"][key] = result["reasons"].get(key, 0) + 1
            result["moved" if kind else "kept"] += 1
            continue
        try:
            with db.begin_nested():
                info = migrate_conversation(db, conv)
        except Exception:  # noqa: BLE001 - eine fehlerhafte Unterhaltung darf die übrigen nicht aufhalten
            log.exception("Chat-Übernahme der Postfach-Unterhaltung %s fehlgeschlagen", conv.id)
            result["errors"] += 1
            continue
        if info["moved"]:
            result["moved"] += 1
            result["messages"] += info["messages"]
            result["chats"].add(info["chat_id"])
        else:
            result["kept"] += 1
            result["reasons"][info["why"]] = result["reasons"].get(info["why"], 0) + 1
    result["chats"] = len(result["chats"])
    return result


def rollback(db: Session, conversation_ids: Optional[list[int]] = None) -> dict[str, int]:
    """Rückweg: kopierte Nachrichten entfernen, Original im Postfach wieder einblenden (``migrated_chat_id = 0``,
    wird dadurch nicht automatisch erneut übernommen; mit ``migrate_postfach(force=True)`` jederzeit wieder möglich).
    Ein bei der Übernahme angelegter Chat ohne weitere Nachrichten wird entfernt."""
    q = select(Conversation).where(Conversation.migrated_chat_id > 0)
    if conversation_ids:
        q = q.where(Conversation.id.in_(conversation_ids))
    out = {"conversations": 0, "messages_removed": 0, "chats_removed": 0}
    for conv in list(db.scalars(q)):
        chat = db.get(Chat, conv.migrated_chat_id)
        if chat is not None:
            rows = list(db.scalars(select(ChatMessage).where(ChatMessage.legacy_source_conversation_id == conv.id)))
            for r in rows:
                db.delete(r)
            out["messages_removed"] += len(rows)
            db.flush()
            left = db.scalar(select(func.count(ChatMessage.id)).where(ChatMessage.chat_id == chat.id)) or 0
            if chat.postfach_import and not left:
                for mem in db.scalars(select(ChatMember).where(ChatMember.chat_id == chat.id)):
                    db.delete(mem)
                db.delete(chat)
                out["chats_removed"] += 1
        conv.migrated_chat_id = KEEP
        out["conversations"] += 1
    return out


def run_startup() -> Optional[dict[str, Any]]:
    """Einmalig beim Start (idempotent, billig, wenn nichts mehr zu tun ist). Fehler stoppen den Start nicht."""
    try:
        with session_scope() as db:
            pending = db.scalar(select(Conversation.id).where(
                Conversation.mail_native.is_(False), Conversation.migrated_chat_id.is_(None),
                Conversation.kind.in_(("direct", "group"))).limit(1))
            if pending is None:
                return None
            result = migrate_postfach(db)
        log.info("Postfach → Chats: %s", result)
        return result
    except Exception:  # noqa: BLE001
        log.exception("Übernahme der Postfach-Chats fehlgeschlagen (wird beim nächsten Start erneut versucht)")
        return None

