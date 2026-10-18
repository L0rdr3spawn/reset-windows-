"""Internes Postfach (ARCHITECTURE.md §9.5, Agent Postfach) – verschlüsselte Nachrichten für alle Konten.

Rechte
------
* ``messages.use`` (alle Rollen außer Monitor): eigenes Postfach, Einzelpersonen anschreiben, antworten, melden,
  blockieren. **Wer wem schreiben darf**, entscheidet die reine Logik in ``schulmanager/messaging.py``: jede/r jedem
  einzelnen erreichbaren Konto; Ausnahmen ``settings.messaging_students_to_students = False`` (Schüler → Schüler),
  Blockierungen, deaktivierte Konten, Monitor-Konten.
* ``messages.broadcast``: Rundschreiben an Gruppen (Klasse, Eltern einer Klasse, Lehrkräfte einer Klasse,
  Kurs/Kursteil, Jahrgang, Kollegium, alle Schüler/Eltern, ganze Schule – je Standort); Lehrkräfte (Scope
  ``own_classes``) nur eigene Klassen und Kurse.
* ``messages.moderate``: gemeldete Nachrichten prüfen (jede Ansicht des Inhalts wird protokolliert), Nachrichten
  ausblenden, Postfach-Sperren.

Datenschutz
-----------
* Betreff und Text liegen nur verschlüsselt in der Datenbank (``crypto.encrypt_text``; AAD
  ``conversations.subject:<cid>`` bzw. ``messages.body:<cid>:<mid>`` – vertauschte oder veränderte Chiffrate werden
  beim Lesen erkannt und als „beschädigt“ angezeigt). Ebenso Meldegründe, Moderationsvermerke, Sperrgründe, Entwürfe.
  Inhalte erscheinen nie in Logs, Audit-Einträgen, Live-Ereignissen oder E-Mail-Hinweisen.
* Wer nicht teilnimmt, bekommt 404 (auch Admins – es gibt keinen Generalschlüssel; nur die Moderation sieht
  **gemeldete** Nachrichten, protokolliert).
* Rundschreiben verraten den Empfangenden nicht, wer es sonst noch bekommen hat (nur die Zielgruppen).
* Anhänge: Dateiablage (verschlüsselt), ``purpose="message"``, Zugriff nur für Teilnehmende
  (``files.register_access_check("message", …)``) bzw. die Moderation bei gemeldeten Nachrichten.
* Suche: nur im eigenen Postfach, serverseitig **nach** dem Entschlüsseln (begrenzte Menge, paginiert).

Endpunkte (Präfix ``/api/v1``)
-----------------------------
* ``GET  /messages/unread`` → ``{unread, messages, muted, archived}`` (Menü-Badge, „Meine Übersicht“)
* ``GET  /messages/conversations?folder=inbox|sent|archive|all&q=&unread=1&offset=&limit=``
* ``POST /messages/conversations`` ``{recipients:[{type:"user",id}|{type:"group",kind,ref}], subject, body,
  attachment_ids, allow_replies, draft_id?}`` → 201 Unterhaltung (wie GET)
* ``GET  /messages/conversations/{id}?before=&limit=`` (Nachrichten aufsteigend, ältere per ``before``)
* ``PATCH /messages/conversations/{id}`` ``{archived?, muted?}``, ``DELETE /messages/conversations/{id}`` (für mich)
* ``POST /messages/conversations/{id}/messages`` ``{body, attachment_ids, draft_id?}`` → 201
  ``{conversation_id, private, message}`` (bei ``allow_replies="sender"`` in eine private Unterhaltung)
* ``POST /messages/conversations/{id}/read`` ``{up_to?}``, ``POST …/unread``, ``POST /messages/read-all``
* ``POST /messages/conversations/{id}/messages/{mid}/report`` ``{category, reason}``
* ``GET  /messages/recipients?q=`` (Adressbuch: Personen + Gruppen, nur Erlaubtes), ``GET /messages/recipients/lookup
  ?user_id=|teacher_id=|student_id=|parents_of=``
* ``GET/POST /messages/blocks``, ``DELETE /messages/blocks/{user_id}``; ``GET/PUT /messages/settings``
* ``GET/POST /messages/drafts``, ``GET/PUT/DELETE /messages/drafts/{id}``
* Moderation: ``GET /messages/moderation/reports?status=``, ``GET …/reports/{id}?context=``,
  ``POST …/reports/{id}/resolve``, ``GET /messages/moderation/suspensions``,
  ``POST/DELETE /messages/moderation/users/{user_id}/suspend``, ``POST /messages/moderation/retention``

Live-Ereignisse (ohne Inhalt, nur an Betroffene): ``change`` ``{scope:["messages"], conversation_id}`` und ``message``
``{conversation_id, message_id}`` an Empfangende; ``change`` ``{scope:["message_reports"]}`` an die Moderation.
E-Mail-Hinweis „Neue Nachricht“ ohne Inhalt/Absender über die Benachrichtigungs-Outbox (nur mit SMTP, Konto-E-Mail
und eingeschaltetem Hinweis; höchstens einer je Unterhaltung, bis sie gelesen wurde).

Wartung: :func:`run_retention` löscht Nachrichten nach ``settings.messaging_retention_days`` (0 = nie), leere
Unterhaltungen, alte Entwürfe, abgelaufene Sperren (für ``maintenance.run_maintenance`` gedacht; bis dahin stößt
``GET /messages/unread`` sie höchstens alle 6 Stunden im Hintergrund an, wenn die Wartung aktiv ist).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, delete, exists, func, insert, or_, select, update
from sqlalchemy.orm import Session

from schulmanager import messaging as mx
from schulmanager.server import crypto, files
from schulmanager.server.audit import audit
from schulmanager.server.config import config
from schulmanager.server.db import get_db, iso, session_scope, utcnow
from schulmanager.server.db_models import NotificationOutbox, ParentLink, User
from schulmanager.server.deps import AuthUser, client_ip, require
from schulmanager.server.events import bus
from schulmanager.server.feature_models.files import StoredFile
from schulmanager.server.feature_models.messages import (REPORT_CATEGORIES, Conversation, ConversationParticipant,
                                                         Message, MessageDraft, MessageReport, MessageUserSettings,
                                                         UserBlock)

from .features_common import cached, has, snapshot

log = logging.getLogger("schulmanager.messages")

router = APIRouter(tags=["Postfach"])

Part = ConversationParticipant

USE = mx.USE_PERMISSION
BROADCAST = mx.BROADCAST_PERMISSION
MODERATE = mx.MODERATE_PERMISSION

PURPOSE = "message"
REF_TYPE = "message"
DRAFT_REF_TYPE = "message_draft"
LIVE_SCOPE = "messages"
MODERATION_SCOPE = "message_reports"

PAGE_DEFAULT = 30
PAGE_MAX = 100
THREAD_DEFAULT = 50
THREAD_MAX = 200
SEARCH_SCAN_MESSAGES = 4000        # höchstens so viele Nachrichten je Suche entschlüsseln
SEARCH_SCAN_CONVERSATIONS = 3000
MAX_DRAFTS = 50
MAX_REASON = 2000
MAX_SUSPEND_DAYS = 365
MAX_CONTEXT = 10
CREATOR_RECIPIENTS_SHOWN = 100
CHUNK = 500
RETENTION_INTERVAL_SECONDS = 6 * 3600
PREVIEW_CHARS = 140

KIND_LABELS = {"direct": "Direkt", "group": "An mehrere", "broadcast": "Rundschreiben", "email": "E-Mail"}
ROLE_RANK = {"to": 0, "cc": 1, "bcc": 2}
ROLE_LABELS_RCPT = {"to": "An", "cc": "CC", "bcc": "BCC"}
FOLDERS = ("inbox", "sent", "archive", "all")
REPORT_CATEGORY_LABELS = {
    "belaestigung": "Belästigung/Mobbing", "beleidigung": "Beleidigung", "bedrohung": "Bedrohung",
    "spam": "Spam/Werbung", "unangemessen": "Unangemessener Inhalt", "sonstiges": "Sonstiges",
}
REPORT_STATUS_LABELS = {"offen": "offen", "erledigt": "erledigt", "abgelehnt": "abgelehnt"}
DELETED_NAME = "Gelöschtes Konto"


# =========================================================================== Eingaben
class RecipientIn(BaseModel):
    """Empfänger: Einzelperson (``type="user"``, ``id``), Gruppe (``type="group"``, ``kind``, ``ref``) oder E-Mail-Adresse
    (``type="email"``, ``email`` – Konto der Schule mit dieser Adresse, sonst extern über das eigene E-Mail-Konto).
    ``role``: ``to`` (An), ``cc`` (Kopie, für alle sichtbar) oder ``bcc`` (Blindkopie, für die anderen unsichtbar)."""
    model_config = ConfigDict(extra="forbid")
    type: Literal["user", "group", "email"]
    id: Optional[int] = Field(None, ge=1)
    kind: Optional[str] = Field(None, max_length=30)
    ref: str = Field("", max_length=80)
    email: str = Field("", max_length=254)
    name: str = Field("", max_length=200)
    role: Literal["to", "cc", "bcc"] = "to"


class ConversationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipients: list[RecipientIn] = Field(min_length=1, max_length=mx.MAX_INDIVIDUALS_BROADCAST + mx.MAX_GROUPS)
    subject: str = Field("", max_length=mx.MAX_SUBJECT * 2)
    body: str = Field("", max_length=mx.MAX_BODY)
    attachment_ids: list[str] = Field(default_factory=list, max_length=mx.MAX_ATTACHMENTS)
    allow_replies: Literal["all", "sender", "none"] = "all"
    draft_id: Optional[int] = Field(None, ge=1)
    mail_account_id: Optional[int] = Field(None, ge=1, description="E-Mail-Konto für externe Empfänger/innen")


class ReplyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field("", max_length=mx.MAX_BODY)
    attachment_ids: list[str] = Field(default_factory=list, max_length=mx.MAX_ATTACHMENTS)
    draft_id: Optional[int] = Field(None, ge=1)


class ParticipantPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    archived: Optional[bool] = None
    muted: Optional[bool] = None


class ReadIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    up_to: Optional[int] = Field(None, ge=0)


class ReportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal[REPORT_CATEGORIES] = "sonstiges"  # type: ignore[valid-type]
    reason: str = Field("", max_length=MAX_REASON)


class BlockIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int = Field(ge=1)


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email_notify: Optional[bool] = None


class DraftIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: Optional[int] = Field(None, ge=1)
    recipients: list[RecipientIn] = Field(default_factory=list,
                                          max_length=mx.MAX_INDIVIDUALS_BROADCAST + mx.MAX_GROUPS)
    subject: str = Field("", max_length=mx.MAX_SUBJECT * 2)
    body: str = Field("", max_length=mx.MAX_BODY)
    allow_replies: Literal["all", "sender", "none"] = "all"
    attachment_ids: list[str] = Field(default_factory=list, max_length=mx.MAX_ATTACHMENTS)


class ResolveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["erledigt", "abgelehnt"] = "erledigt"
    resolution: str = Field("", max_length=MAX_REASON)
    remove_message: bool = False
    suspend_days: Optional[int] = Field(None, ge=1, le=MAX_SUSPEND_DAYS)


class SuspendIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: int = Field(ge=1, le=MAX_SUSPEND_DAYS)
    reason: str = Field("", max_length=MAX_REASON)


# =========================================================================== Fehler, Zeiten, Hilfen
def _fail(status: int, code: str, message: str) -> HTTPException:
    """Fehler mit maschinenlesbarem Code (``detail = {"code", "message"}``, wie die Dateiablage)."""
    return HTTPException(status, {"code": code, "message": message})


def _mx_error(exc: mx.MessagingError) -> HTTPException:
    return _fail(exc.status, exc.code, exc.message)


def _not_found(what: str = "Unterhaltung") -> HTTPException:
    return _fail(404, "not_found", f"{what} nicht gefunden.")


def _local(dt: datetime) -> str:
    """Naive UTC → „06.10.2026, 14:30 Uhr“ in Server-Ortszeit (für Meldungstexte)."""
    return dt.replace(tzinfo=timezone.utc).astimezone().strftime("%d.%m.%Y, %H:%M Uhr")


def _chunks(seq: Sequence[Any], size: int = CHUNK) -> Iterator[Sequence[Any]]:
    for start in range(0, len(seq), size):
        yield seq[start:start + size]


def _decrypt(token: str, aad: str, what: str, ident: Any) -> tuple[str, bool]:
    """Entschlüsselt ein Token; ``("", False)`` bei Manipulation/fehlendem Schlüssel (nur Warnung ohne Inhalt)."""
    if not token:
        return "", True
    try:
        return crypto.decrypt_text(token, aad), True
    except crypto.CryptoError as exc:
        log.warning("Postfach: %s %s nicht entschlüsselbar (%s) – manipuliert oder Schlüssel fehlt", what, ident,
                    type(exc).__name__)
        return "", False


def _subject(conv: Conversation) -> tuple[str, bool]:
    return _decrypt(conv.subject_enc, conv.subject_aad, "Betreff der Unterhaltung", conv.id)


def _body(msg: Message) -> tuple[str, bool]:
    return _decrypt(msg.body_enc, msg.body_aad, "Nachricht", msg.id)


def _preview(text: str, chars: int = PREVIEW_CHARS) -> str:
    flat = " ".join((text or "").split())
    return flat if len(flat) <= chars else flat[:chars - 1].rstrip() + "…"


def _index(snap) -> mx.SchoolIndex:
    """Schnellzugriffe auf das Planungsdokument (je Planversion einmal aufgebaut)."""
    return cached("messaging_index", (), lambda: mx.SchoolIndex.build(snap[1]), snap)


def _policy(snap) -> tuple[bool, int]:
    """(Schüler dürfen Schülern schreiben, Aufbewahrungsfrist in Tagen)."""
    s = snap[1].settings
    return (bool(getattr(s, "messaging_students_to_students", True)),
            max(0, int(getattr(s, "messaging_retention_days", 365) or 0)))


def _publish(user_ids: Iterable[int], conversation_id: Optional[int] = None, message_id: Optional[int] = None,
             *, new_message: bool = False) -> None:
    """Live-Hinweis ohne Inhalt an die betroffenen Konten (``change`` für die Oberfläche, ``message`` für neue
    Nachrichten laut Vertrag)."""
    ids = {int(i) for i in user_ids if i}
    if not ids:
        return
    data: dict[str, Any] = {"version": None, "scope": [LIVE_SCOPE], "dates": []}
    if conversation_id:
        data["conversation_id"] = conversation_id
    try:
        bus.publish("change", data, user_ids=ids)
        if new_message and conversation_id and message_id:
            bus.publish("message", {"conversation_id": conversation_id, "message_id": message_id}, user_ids=ids)
    except Exception:  # noqa: BLE001 - Live-Ereignisse dürfen die Aktion nie verhindern
        log.exception("Postfach: Live-Ereignis konnte nicht verteilt werden")


def _publish_moderation() -> None:
    try:
        bus.publish("change", {"version": None, "scope": [MODERATION_SCOPE], "dates": []}, permission=MODERATE)
    except Exception:  # noqa: BLE001
        log.exception("Postfach: Moderations-Ereignis konnte nicht verteilt werden")


# =========================================================================== Konten
def _account_rows(db: Session, ids: Optional[Iterable[int]] = None) -> list[mx.Account]:
    cols = (User.id, User.role, User.display_name, User.username, User.active, User.teacher_id, User.student_id,
            User.site)
    wanted = sorted({int(i) for i in ids if i}) if ids is not None else None
    rows: list[Any] = []
    links: dict[int, list[str]] = defaultdict(list)
    if wanted is None:
        rows = list(db.execute(select(*cols)))
        for pid, sid in db.execute(select(ParentLink.parent_user_id, ParentLink.student_id).order_by(ParentLink.id)):
            links[pid].append(sid)
    else:
        for chunk in _chunks(wanted):
            rows += list(db.execute(select(*cols).where(User.id.in_(chunk))))
        parents = [r.id for r in rows if r.role == "eltern"]
        for chunk in _chunks(parents):
            for pid, sid in db.execute(select(ParentLink.parent_user_id, ParentLink.student_id)
                                       .where(ParentLink.parent_user_id.in_(chunk)).order_by(ParentLink.id)):
                links[pid].append(sid)
    return [mx.Account(id=r.id, role=r.role, name=(r.display_name or r.username), active=bool(r.active),
                       teacher_id=r.teacher_id, student_id=r.student_id, site=r.site,
                       children=tuple(links.get(r.id, ()))) for r in rows]


def _directory(db: Session) -> mx.Directory:
    """Alle Konten (für Gruppenauflösung und Adressbuch; erreichbar = aktiv + ``messages.use``)."""
    from schulmanager.server import parent_access as pa

    try:   # Zustellwahl volljähriger Schüler/innen (Rundschreiben an mich / Eltern / beide)
        routing = pa.delivery_routing(db)
    except Exception:  # noqa: BLE001 - ohne Plan oder Einstellung gilt die Standardzustellung
        log.exception("Postfach: Zustellwahl nicht lesbar")
        routing = {}
    return mx.Directory(_account_rows(db), routing)


def _accounts(db: Session, ids: Iterable[int]) -> dict[int, mx.Account]:
    return {a.id: a for a in _account_rows(db, ids)}


def _person(acc: Optional[mx.Account], idx: mx.SchoolIndex, viewer: AuthUser) -> dict[str, Any]:
    """Person für die Anzeige (datensparsam, siehe ``messaging.person_card``)."""
    if acc is None:
        return {"type": "user", "id": None, "name": DELETED_NAME, "role": None, "role_label": "", "info": "",
                "active": False, "me": False}
    card = mx.person_card(idx, viewer, acc)
    card["active"] = acc.reachable
    card["me"] = acc.id == viewer.id
    return card


def _external_person(address: str, name: str = "", role: Optional[str] = None) -> dict[str, Any]:
    out = {"type": "external", "id": None, "name": name or address, "email": address, "role": None,
           "role_label": "E-Mail", "info": address, "active": True, "me": False, "external": True}
    if role:
        out["recipient_role"] = role
    return out


def _visible_external(conv: Conversation, viewer_id: int) -> list[dict[str, Any]]:
    """Externe Beteiligte; BCC sieht nur, wer die Unterhaltung begonnen hat."""
    creator = conv.created_by == viewer_id
    return [_external_person(e.get("email", ""), e.get("name", ""), e.get("role"))
            for e in (conv.external or []) if isinstance(e, dict) and e.get("email")
            and (e.get("role") != "bcc" or creator)]


def _visible_members(rows: list[tuple[int, str]], conv: Conversation, viewer_id: int) -> list[tuple[int, str]]:
    """Teilnehmende ohne fremde BCC-Empfangende (die sieht nur, wer die Unterhaltung begonnen hat)."""
    creator = conv.created_by == viewer_id
    return [(uid, role) for uid, role in rows if role != "bcc" or creator or uid == viewer_id]


def _blocked_by(db: Session, user_id: int) -> set[int]:
    """Konten, die ``user_id`` blockiert haben."""
    return set(db.scalars(select(UserBlock.user_id).where(UserBlock.blocked_user_id == user_id)))


def _my_blocks(db: Session, user_id: int) -> set[int]:
    """Konten, die ``user_id`` blockiert hat."""
    return set(db.scalars(select(UserBlock.blocked_user_id).where(UserBlock.user_id == user_id)))


def _suspended_until(db: Session, user_id: int) -> Optional[datetime]:
    row = db.get(MessageUserSettings, user_id)
    if row is not None and row.suspended_until is not None and row.suspended_until > utcnow():
        return row.suspended_until
    return None


def _ensure_can_send(db: Session, user: AuthUser) -> None:
    until = _suspended_until(db, user.id)
    if until is not None:
        raise _fail(403, "suspended", f"Ihr Postfach ist bis {_local(until)} für das Senden gesperrt (Moderation). "
                                      "Lesen ist weiterhin möglich.")


def _check_rate(db: Session, user: AuthUser, *, new_conversation: bool) -> None:
    """Missbrauchsschutz: neue Unterhaltungen je Stunde, Nachrichten je 10 Minuten."""
    cls = mx.rate_class(user)
    now = utcnow()
    if new_conversation:
        n = db.scalar(select(func.count()).select_from(Conversation).where(
            Conversation.created_by == user.id, Conversation.created_at > now - timedelta(hours=1))) or 0
        if n >= mx.RATE_NEW_CONVERSATIONS[cls]:
            raise _fail(429, "rate_limited", "Sie haben in der letzten Stunde sehr viele neue Unterhaltungen begonnen. "
                                             "Bitte später erneut versuchen.")
    n = db.scalar(select(func.count()).select_from(Message).where(
        Message.sender_id == user.id, Message.created_at > now - timedelta(minutes=10))) or 0
    if n >= mx.RATE_MESSAGES[cls]:
        raise _fail(429, "rate_limited", "Sie haben in kurzer Zeit sehr viele Nachrichten gesendet. Bitte einige "
                                         "Minuten warten.")


# =========================================================================== Teilnahme, Ungelesen
def _membership(db: Session, conversation_id: int, user: AuthUser) -> tuple[Part, Conversation]:
    """Teilnahme (nicht „für mich gelöscht“) oder 404 – die Existenz fremder Unterhaltungen wird nicht verraten."""
    part = db.get(Part, (conversation_id, user.id))
    if part is None or part.deleted:
        raise _not_found()
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise _not_found()
    return part, conv


def _unread_filter(user_id: int):
    """Bedingung „ungelesen für ``user_id``“ (Join ``Part``–``Message``)."""
    blocked = select(UserBlock.blocked_user_id).where(UserBlock.user_id == user_id)
    return and_(Message.conversation_id == Part.conversation_id, Message.id > Part.last_read_id,
                Message.id > Part.cleared_id, Message.removed_at.is_(None),
                or_(Message.sender_id.is_(None),
                    and_(Message.sender_id != user_id, Message.sender_id.not_in(blocked))))


def _in_chats():
    """Bedingung „Verlauf wurde nach Chats & Gruppen übernommen“ (``chat_migration``) – nicht mehr im Postfach."""
    return func.coalesce(Conversation.migrated_chat_id, 0) > 0


def _unread_rows(db: Session, user_id: int) -> list[Any]:
    """``(conversation_id, muted, archived, anzahl)`` aller Unterhaltungen mit ungelesenen Nachrichten."""
    q = (select(Part.conversation_id, Part.muted, Part.archived, func.count(Message.id))
         .join(Message, _unread_filter(user_id))
         .join(Conversation, Conversation.id == Part.conversation_id)
         .where(Part.user_id == user_id, Part.deleted.is_(False), ~_in_chats())
         .group_by(Part.conversation_id, Part.muted, Part.archived))
    return list(db.execute(q))


def unread_counts(db: Session, user_id: int) -> dict[str, int]:
    """Zähler fürs Menü: ``unread`` = Unterhaltungen mit Ungelesenem (ohne stummgeschaltete/archivierte),
    ``messages`` = deren ungelesene Nachrichten, ``muted``/``archived`` = übrige Unterhaltungen mit Ungelesenem."""
    out = {"unread": 0, "messages": 0, "muted": 0, "archived": 0}
    for _cid, muted, archived, n in _unread_rows(db, user_id):
        if muted:
            out["muted"] += 1
        elif archived:
            out["archived"] += 1
        else:
            out["unread"] += 1
            out["messages"] += int(n)
    return out


# =========================================================================== Darstellung
def _audience(conv: Conversation) -> list[dict[str, Any]]:
    return [dict(a) for a in (conv.audience or []) if isinstance(a, dict)]


def _title(conv: Conversation, subject: str, other_names: list[str]) -> str:
    if subject:
        return subject
    if conv.kind == "email":
        ext = [e for e in (conv.external or []) if isinstance(e, dict) and e.get("role") != "bcc"]
        return ", ".join((e.get("name") or e.get("email", "")) for e in ext[:3]) or "(ohne Betreff)"
    if conv.kind == "broadcast":
        return ", ".join(a.get("label", "") for a in _audience(conv) if a.get("label")) or "Rundschreiben"
    return ", ".join(other_names) or "(ohne Betreff)"


def _message_preview(msg: Optional[Message], viewer_id: int, my_blocks: set[int]) -> Optional[dict[str, Any]]:
    if msg is None:
        return None
    own = msg.sender_id == viewer_id
    if msg.removed_at is not None:
        text, ok = "Nachricht von der Moderation entfernt", True
    elif not own and msg.sender_id in my_blocks:
        text, ok = "Nachricht einer blockierten Person (ausgeblendet)", True
    else:
        body, ok = _body(msg)
        text = _preview(body) if ok else "Nachricht beschädigt – nicht lesbar"
        if not text and msg.attachment_ids:
            n = len(msg.attachment_ids)
            text = "1 Anhang" if n == 1 else f"{n} Anhänge"
    return {"id": msg.id, "sender_id": msg.sender_id, "own": own, "preview": text, "integrity_ok": ok,
            "created_at": iso(msg.created_at), "attachments": len(msg.attachment_ids or []),
            "removed": msg.removed_at is not None}


def _summaries(db: Session, user: AuthUser, pairs: list[tuple[Part, Conversation]], idx: mx.SchoolIndex,
               unread: dict[int, int], matches: Optional[dict[int, dict[str, Any]]] = None) -> list[dict[str, Any]]:
    """Listeneinträge (Posteingang/Gesendet/Archiv/Suche)."""
    if not pairs:
        return []
    my_blocks = _my_blocks(db, user.id)
    last_ids = [c.last_message_id for _, c in pairs if c.last_message_id]
    last_msgs = {m.id: m for chunk in _chunks(last_ids)
                 for m in db.scalars(select(Message).where(Message.id.in_(chunk)))}
    small = [c.id for _, c in pairs if c.kind != "broadcast"]
    member_rows: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for chunk in _chunks(small):
        for cid, uid, role in db.execute(select(Part.conversation_id, Part.user_id, Part.recipient_role)
                                         .where(Part.conversation_id.in_(chunk))
                                         .order_by(Part.joined_at, Part.user_id)):
            member_rows[cid].append((uid, role or "to"))
    conv_by_id = {c.id: c for _, c in pairs}
    members: dict[int, list[int]] = {cid: [uid for uid, _r in _visible_members(rows, conv_by_id[cid], user.id)]
                                     for cid, rows in member_rows.items()}
    roles_of: dict[int, dict[int, str]] = {cid: dict(rows) for cid, rows in member_rows.items()}
    wanted = {uid for ids in members.values() for uid in ids}
    wanted |= {c.created_by for _, c in pairs if c.created_by}
    wanted |= {m.sender_id for m in last_msgs.values() if m.sender_id}
    accounts = _accounts(db, wanted)
    out = []
    for part, conv in pairs:
        subject, subject_ok = _subject(conv)
        others = [accounts.get(uid) for uid in members.get(conv.id, []) if uid != user.id]
        other_names = [a.name if a else DELETED_NAME for a in others]
        external = _visible_external(conv, user.id)
        other_names += [e["name"] for e in external]
        last = last_msgs.get(conv.last_message_id)
        preview = _message_preview(last, user.id, my_blocks)
        if preview is not None:
            sender = accounts.get(last.sender_id) if last and last.sender_id else None
            if last is not None and last.sender_id is None and last.external_from:
                preview["sender_name"] = last.external_name or last.external_from
            else:
                preview["sender_name"] = "Sie" if preview["own"] else (sender.name if sender else DELETED_NAME)
        creator = accounts.get(conv.created_by) if conv.created_by else None
        item: dict[str, Any] = {
            "id": conv.id, "kind": conv.kind, "kind_label": KIND_LABELS.get(conv.kind, conv.kind),
            "subject": subject, "integrity_ok": subject_ok, "title": _title(conv, subject, other_names),
            "allow_replies": conv.allow_replies, "created_at": iso(conv.created_at),
            "last_message_at": iso(conv.last_message_at), "last_message": preview,
            "unread": int(unread.get(conv.id, 0)), "archived": bool(part.archived), "muted": bool(part.muted),
            "is_creator": conv.created_by == user.id,
            "creator": _person(creator, idx, user) if conv.created_by else _person(None, idx, user),
            "participants": [{**_person(a, idx, user), "recipient_role": roles_of.get(conv.id, {}).get(a.id, "to")}
                             if a else _person(a, idx, user) for a in others] if conv.kind != "broadcast" else [],
            "participant_count": len(members.get(conv.id, [])) if conv.kind != "broadcast" else None,
            "external": external, "my_role": roles_of.get(conv.id, {}).get(user.id),
            "audience": _audience(conv) if conv.kind == "broadcast" else [],
            "recipient_count": conv.recipient_count, "parent_id": conv.parent_id,
            "chat_id": conv.migrated_chat_id if (conv.migrated_chat_id or 0) > 0 else None,
        }
        if matches and conv.id in matches:
            item["match"] = matches[conv.id]
        out.append(item)
    return out


# =========================================================================== Antwortregeln
def _has_other_students(db: Session, conversation_id: int, user_id: int) -> bool:
    return bool(db.scalar(select(exists().where(
        Part.conversation_id == conversation_id, Part.user_id != user_id, Part.user_id == User.id,
        User.role == "schueler", User.active.is_(True)))))


def _private_child(db: Session, conv: Conversation, user_id: int) -> Optional[Conversation]:
    """Bestehende private Antwort-Unterhaltung des Kontos zu einem Rundschreiben."""
    return db.scalar(select(Conversation).where(Conversation.parent_id == conv.id, Conversation.kind == "direct",
                                                Conversation.created_by == user_id).order_by(Conversation.id).limit(1))


def _reply_state(db: Session, conv: Conversation, user: AuthUser, s2s: bool,
                 accounts: Optional[dict[int, mx.Account]] = None) -> dict[str, Any]:
    """Darf ``user`` antworten, und wohin? → ``{mode: all|private|None, can_reply, code, reason,
    private_conversation_id}``."""
    is_creator = conv.created_by == user.id
    mode = mx.reply_mode(conv.kind, conv.allow_replies, is_creator=is_creator)
    my_role = db.scalar(select(Part.recipient_role).where(Part.conversation_id == conv.id, Part.user_id == user.id))
    if my_role == "bcc" and not is_creator and mode == "all" and conv.created_by:
        mode = "private"                 # Blindkopie: Antwort nur an die absendende Person
    code: Optional[str] = None
    reason: Optional[str] = None
    accounts = dict(accounts or {})
    blocked_me = _blocked_by(db, user.id)
    creator = None
    if conv.created_by:
        creator = accounts.get(conv.created_by) or _accounts(db, [conv.created_by]).get(conv.created_by)
    if mode is None:
        code, reason = "no_replies", "Für dieses Rundschreiben sind keine Antworten vorgesehen."
    elif mode == "private":
        if creator is None or not creator.reachable:
            mode, code, reason = None, "unreachable", "Die absendende Person ist nicht mehr erreichbar."
        elif creator.id in blocked_me:
            mode, code, reason = None, "blocked", f"{creator.name} nimmt keine Nachrichten von Ihnen an."
    elif conv.kind == "direct":
        other_id = db.scalar(select(Part.user_id).where(Part.conversation_id == conv.id, Part.user_id != user.id)
                             .limit(1))
        other = accounts.get(other_id) if other_id else None
        if other is None and other_id:
            other = _accounts(db, [other_id]).get(other_id)
        if other is None or not other.reachable:
            mode, code, reason = None, "unreachable", "Diese Person kann keine Nachrichten mehr empfangen."
        elif other.id in blocked_me:
            mode, code, reason = None, "blocked", f"{other.name} nimmt keine Nachrichten von Ihnen an."
        elif not s2s and user.role == "schueler" and other.role == "schueler":
            mode, code, reason = None, "students_to_students", ("Nachrichten zwischen Schülerinnen und Schülern "
                                                                "sind an dieser Schule abgeschaltet.")
    elif not s2s and user.role == "schueler" and _has_other_students(db, conv.id, user.id):
        # Antworten würden andere Schüler/innen erreichen → nur privat an die (erwachsene) absendende Person
        if not is_creator and creator is not None and creator.reachable and creator.role != "schueler" \
                and creator.id not in blocked_me:
            mode = "private"
        else:
            mode, code, reason = None, "students_to_students", ("Nachrichten zwischen Schülerinnen und Schülern "
                                                                "sind an dieser Schule abgeschaltet.")
    private_id = None
    if mode == "private":
        child = _private_child(db, conv, user.id)
        private_id = child.id if child is not None else None
    can_reply = mode is not None
    until = _suspended_until(db, user.id)
    if can_reply and until is not None:
        can_reply, code, reason = False, "suspended", f"Ihr Postfach ist bis {_local(until)} für das Senden gesperrt."
    hint = None
    if mode == "private" and creator is not None:
        hint = f"Ihre Antwort geht nur an {creator.name} (private Unterhaltung)."
    elif mode == "all" and conv.external:
        from .features_mail import sending_account
        ext = [e.get("email") for e in conv.external if isinstance(e, dict) and e.get("email")]
        acc = sending_account(db, user.id, conv.mail_account_id)
        if acc is None:
            hint = ("Externe Empfänger/innen (" + ", ".join(ext[:3]) + ") erhalten Ihre Antwort nicht – dafür unter "
                    "Postfach → Einstellungen ein E-Mail-Konto verbinden.")
        else:
            hint = f"Ihre Antwort geht auch per E-Mail ({acc.email}) an: " + ", ".join(ext[:5])
    return {"mode": mode, "can_reply": can_reply, "code": code, "reason": reason, "hint": hint,
            "private_conversation_id": private_id}


# =========================================================================== Nachrichten anlegen
def _check_content(text: str, attachment_ids: list[str]) -> None:
    if not text and not attachment_ids:
        raise _fail(422, "empty", "Bitte einen Nachrichtentext eingeben oder eine Datei anhängen.")
    if len(text) > mx.MAX_BODY:
        raise _fail(422, "too_long", f"Die Nachricht ist zu lang (höchstens {mx.MAX_BODY} Zeichen).")


def _draft_for(db: Session, user: AuthUser, draft_id: Optional[int]) -> Optional[MessageDraft]:
    if not draft_id:
        return None
    draft = db.get(MessageDraft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise _not_found("Entwurf")
    return draft


def _attach(db: Session, user: AuthUser, file_ids: list[str], msg: Message) -> None:
    """Hängt eigene Uploads an die Nachricht (Anhänge aus eigenen Entwürfen werden vorher gelöst)."""
    ids = list(dict.fromkeys(file_ids))
    if not ids:
        return
    if len(ids) > mx.MAX_ATTACHMENTS:
        raise _fail(422, "too_many_files", f"Höchstens {mx.MAX_ATTACHMENTS} Anhänge je Nachricht.")
    for fid in ids:
        meta = files.get_file(db, fid)
        if meta is not None and meta.owner_user_id == user.id and meta.ref_type == DRAFT_REF_TYPE:
            files.detach(db, fid)
    metas = files.attach_many(db, ids, user, REF_TYPE, msg.id, max_files=mx.MAX_ATTACHMENTS)
    msg.attachment_ids = [m.id for m in metas]


def _new_message(db: Session, conv: Conversation, user: AuthUser, text: str, attachment_ids: list[str]) -> Message:
    now = utcnow()
    msg = Message(conversation_id=conv.id, sender_id=user.id, body_enc="", attachment_ids=[], created_at=now)
    db.add(msg)
    db.flush()                                    # ID für das AAD
    msg.body_enc = crypto.encrypt_text(text, msg.body_aad)
    _attach(db, user, attachment_ids, msg)
    conv.last_message_id = msg.id
    conv.last_message_at = now
    return msg


def _drop_draft(db: Session, draft: Optional[MessageDraft], keep: Iterable[str] = ()) -> None:
    """Entwurf nach dem Senden löschen; nicht mitgesendete Anhänge werden gelöst (verfallen nach 24 h)."""
    if draft is None:
        return
    keep_set = set(keep)
    for meta in db.scalars(select(StoredFile).where(StoredFile.ref_type == DRAFT_REF_TYPE,
                                                     StoredFile.ref_id == str(draft.id))):
        if meta.id not in keep_set:
            files.detach(db, meta.id)
    db.delete(draft)


def _deliver(db: Session, conv: Conversation, msg: Message, sender_id: int, prev_last_id: int
             ) -> tuple[set[int], list[int]]:
    """Teilnahme nach einer Antwort aktualisieren → (Konten für Live-Ereignisse, Kandidaten für E-Mail-Hinweise).

    Nicht stummgeschaltete Empfangende: Unterhaltung kommt zurück in den Posteingang (auch nach „für mich gelöscht“).
    Stummgeschaltete und Konten, die den Absender blockiert haben, bekommen sie nur still.
    """
    now = utcnow()
    db.execute(update(Part).where(Part.conversation_id == conv.id, Part.user_id == sender_id)
               .values(has_sent=True, deleted=False, last_read_id=msg.id, last_read_at=now))
    rows = list(db.execute(select(Part.user_id, Part.muted, Part.last_read_id)
                           .where(Part.conversation_id == conv.id, Part.user_id != sender_id)))
    blockers = _blocked_by_among(db, sender_id, [r.user_id for r in rows])
    loud = [r.user_id for r in rows if not r.muted and r.user_id not in blockers]
    quiet = [r.user_id for r in rows if r.muted or r.user_id in blockers]
    for chunk in _chunks(loud):
        db.execute(update(Part).where(Part.conversation_id == conv.id, Part.user_id.in_(chunk))
                   .values(deleted=False, archived=False, has_incoming=True))
    for chunk in _chunks(quiet):
        db.execute(update(Part).where(Part.conversation_id == conv.id, Part.user_id.in_(chunk))
                   .values(has_incoming=True))
    mail = [r.user_id for r in rows if r.user_id in set(loud) and r.last_read_id >= prev_last_id]
    notify = set(loud) | {r.user_id for r in rows if r.muted and r.user_id not in blockers}
    return notify, mail


def _blocked_by_among(db: Session, sender_id: int, user_ids: list[int]) -> set[int]:
    out: set[int] = set()
    for chunk in _chunks(user_ids):
        out |= set(db.scalars(select(UserBlock.user_id).where(UserBlock.blocked_user_id == sender_id,
                                                               UserBlock.user_id.in_(chunk))))
    return out


def _queue_email_hints(db: Session, user_ids: list[int], conversation_id: int) -> int:
    """E-Mail „Neue Nachricht“ – ohne Inhalt, Betreff oder Absender (Transport per E-Mail ist unverschlüsselt)."""
    if not user_ids or not getattr(config, "smtp_enabled", False):
        return 0
    queued = 0
    now = utcnow()
    for chunk in _chunks(sorted(set(user_ids))):
        rows = db.execute(
            select(User.id, User.email, User.display_name, User.username, Part.last_read_id,
                   MessageUserSettings.email_notify)
            .join(Part, and_(Part.user_id == User.id, Part.conversation_id == conversation_id))
            .outerjoin(MessageUserSettings, MessageUserSettings.user_id == User.id)
            .where(User.id.in_(chunk), User.active.is_(True), User.email.is_not(None), User.email != ""))
        for r in rows:
            if r.email_notify is False:
                continue
            key = f"messages|{r.id}|{conversation_id}|{r.last_read_id}"
            if db.scalar(select(NotificationOutbox.id).where(NotificationOutbox.dedupe_key == key).limit(1)):
                continue
            name = r.display_name or r.username
            text = (f"Guten Tag {name},\n\nin Ihrem Postfach im {config.app_name} ist eine neue Nachricht eingegangen."
                    "\nAus Datenschutzgründen steht der Inhalt nicht in dieser E-Mail – bitte melden Sie sich an:\n"
                    f"{config.base_url}/postfach\n\nDiesen Hinweis können Sie im Postfach unter „Einstellungen“ "
                    "abschalten.\n")
            db.add(NotificationOutbox(kind="email", target=r.email[:500], subject=f"Neue Nachricht im {config.app_name}",
                                      payload=text, status="pending", attempts=0, next_attempt_at=now,
                                      dedupe_key=key, created_at=now))
            queued += 1
    return queued


def _kick_notify(queued: int) -> None:
    if not queued:
        return
    try:
        from schulmanager.server import notify
        notify.kick()
    except Exception:  # noqa: BLE001 - Benachrichtigungen dürfen nie stören
        pass


# =========================================================================== Anhänge: Zugriffsprüfung
def _attachment_access(db: Session, user: Any, meta: StoredFile) -> bool:
    """Anhang lesen: Teilnehmende, die die Nachricht sehen (nicht entfernt, nicht „für mich gelöscht“, nicht von
    selbst blockierten Personen), oder die Moderation bei gemeldeten Nachrichten."""
    try:
        mid = int(meta.ref_id or "")
    except ValueError:
        return False
    msg = db.get(Message, mid)
    if msg is None or meta.id not in (msg.attachment_ids or []):
        return False
    uid = int(getattr(user, "id", 0) or 0)
    if not uid:
        return False
    if has(user, USE):
        part = db.get(Part, (msg.conversation_id, uid))
        if part is not None and not part.deleted and msg.id > part.cleared_id and msg.removed_at is None:
            if msg.sender_id == uid or msg.sender_id is None or msg.sender_id not in _my_blocks(db, uid):
                return True
    if has(user, MODERATE):
        return bool(db.scalar(select(exists().where(MessageReport.message_id == msg.id))))
    return False


files.register_purpose(PURPOSE)
files.register_access_check(REF_TYPE, _attachment_access)


# =========================================================================== Ungelesen
@router.get("/messages/unread")
def get_unread(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Ungelesen-Zähler (Menü-Badge, Startseite, „Meine Übersicht“)."""
    _maybe_retention()
    return unread_counts(db, user.id)


@router.post("/messages/read-all")
def read_all(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Alle Unterhaltungen als gelesen markieren."""
    now = utcnow()
    ids = [r[0] for r in _unread_rows(db, user.id)]
    for chunk in _chunks(ids):
        last = select(Conversation.last_message_id).where(Conversation.id == Part.conversation_id).scalar_subquery()
        db.execute(update(Part).where(Part.user_id == user.id, Part.conversation_id.in_(chunk))
                   .values(last_read_id=last, last_read_at=now).execution_options(synchronize_session=False))
    db.commit()
    _publish([user.id])
    return {"updated": len(ids), "counts": unread_counts(db, user.id)}


# =========================================================================== Liste & Suche
def _folder_filter(q, folder: str):
    if folder == "inbox":
        return q.where(Part.archived.is_(False), Part.has_incoming.is_(True))
    if folder == "sent":
        return q.where(Part.has_sent.is_(True))
    if folder == "archive":
        return q.where(Part.archived.is_(True))
    return q


def _search(db: Session, user: AuthUser, pairs: list[tuple[Part, Conversation]], query: str
            ) -> tuple[list[tuple[Part, Conversation]], dict[int, dict[str, Any]], dict[str, Any]]:
    """Suche im eigenen Postfach – serverseitig nach dem Entschlüsseln (Betreff, Namen, Zielgruppen, Texte)."""
    my_blocks = _my_blocks(db, user.id)
    pairs = pairs[:SEARCH_SCAN_CONVERSATIONS]
    by_id = {c.id: (p, c) for p, c in pairs}
    matched: dict[int, dict[str, Any]] = {}
    # 1. Betreff und Zielgruppen
    for part, conv in pairs:
        subject, _ok = _subject(conv)
        labels = [a.get("label", "") for a in _audience(conv)]
        if mx.matches([subject, *labels], query):
            matched[conv.id] = {"in": "subject", "snippet": mx.snippet(subject or ", ".join(labels), query)}
    # 2. Namen der Teilnehmenden (nur kleine Unterhaltungen) und der Absender von Rundschreiben
    small = [c.id for _, c in pairs if c.kind != "broadcast" and c.id not in matched]
    members: dict[int, list[int]] = defaultdict(list)
    for chunk in _chunks(small):
        for cid, uid in db.execute(select(Part.conversation_id, Part.user_id).where(Part.conversation_id.in_(chunk))):
            if uid != user.id:
                members[cid].append(uid)
    creators = {c.id: c.created_by for _, c in pairs if c.kind == "broadcast" and c.created_by}
    accounts = _accounts(db, {u for ids in members.values() for u in ids} | set(creators.values()))
    for cid, ids in list(members.items()) + [(cid, [uid]) for cid, uid in creators.items()]:
        if cid in matched:
            continue
        names = [accounts[u].name for u in ids if u in accounts]
        if names and mx.matches([" ".join(names)], query):
            matched[cid] = {"in": "people", "snippet": ", ".join(names[:5])}
    # 3. Nachrichtentexte (neueste zuerst, begrenzt)
    scanned = 0
    truncated = False
    ids = list(by_id)
    if ids:
        q = (select(Message).join(Part, and_(Part.conversation_id == Message.conversation_id, Part.user_id == user.id))
             .where(Message.conversation_id.in_(ids) if len(ids) <= 900 else Part.deleted.is_(False),
                    Message.id > Part.cleared_id, Message.removed_at.is_(None))
             .order_by(Message.id.desc()).limit(SEARCH_SCAN_MESSAGES + 1))
        for msg in db.scalars(q):
            if msg.conversation_id not in by_id:
                continue
            scanned += 1
            if scanned > SEARCH_SCAN_MESSAGES:
                truncated = True
                break
            if msg.conversation_id in matched:
                continue
            if msg.sender_id and msg.sender_id != user.id and msg.sender_id in my_blocks:
                continue
            body, ok = _body(msg)
            if ok and body and mx.matches([body], query):
                matched[msg.conversation_id] = {"in": "message", "message_id": msg.id,
                                                "snippet": mx.snippet(body, query)}
    hits = [(p, c) for p, c in pairs if c.id in matched]
    return hits, matched, {"scanned_messages": min(scanned, SEARCH_SCAN_MESSAGES), "truncated": truncated}


@router.get("/messages/conversations")
def list_conversations(folder: Literal["inbox", "sent", "archive", "all"] = "inbox",
                       q: str = Query("", max_length=100), unread: bool = False,
                       offset: int = Query(0, ge=0, le=100_000), limit: int = Query(PAGE_DEFAULT, ge=1, le=PAGE_MAX),
                       user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Unterhaltungen eines Ordners (neueste zuerst). ``q`` durchsucht das eigene Postfach nach dem Entschlüsseln."""
    snap = snapshot()
    idx = _index(snap)
    unread_map = {cid: int(n) for cid, _m, _a, n in _unread_rows(db, user.id)}
    base = (select(Part, Conversation).join(Conversation, Conversation.id == Part.conversation_id)
            .where(Part.user_id == user.id, Part.deleted.is_(False), ~_in_chats()))
    base = _folder_filter(base, folder)
    if unread:
        if not unread_map:
            return {"items": [], "total": 0, "offset": offset, "limit": limit, "folder": folder, "query": q,
                    "search": None, "counts": unread_counts(db, user.id)}
        base = base.where(Part.conversation_id.in_(list(unread_map)[:5000]))
    order = (Conversation.last_message_at.desc(), Conversation.id.desc())
    query = q.strip()
    search_info = None
    matches = None
    if mx.query_tokens(query):
        pairs = [(p, c) for p, c in db.execute(base.order_by(*order).limit(SEARCH_SCAN_CONVERSATIONS))]
        hits, matches, search_info = _search(db, user, pairs, query)
        total = len(hits)
        page = hits[offset:offset + limit]
    else:
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        page = [(p, c) for p, c in db.execute(base.order_by(*order).offset(offset).limit(limit))]
    return {"items": _summaries(db, user, page, idx, unread_map, matches), "total": int(total), "offset": offset,
            "limit": limit, "folder": folder, "query": query, "search": search_info,
            "counts": unread_counts(db, user.id)}


# =========================================================================== Einzelansicht
def _message_out(msg: Message, viewer: AuthUser, accounts: dict[int, mx.Account], idx: mx.SchoolIndex,
                 my_blocks: set[int], attachments: dict[str, dict], reported: set[int], last_read_id: int
                 ) -> dict[str, Any]:
    own = msg.sender_id == viewer.id
    removed = msg.removed_at is not None
    blocked = (not own) and msg.sender_id is not None and msg.sender_id in my_blocks
    if removed or blocked:
        body, ok = "", True
    else:
        body, ok = _body(msg)
    sender = accounts.get(msg.sender_id) if msg.sender_id else None
    if msg.sender_id is None and msg.external_from:
        sender_out = _external_person(msg.external_from, msg.external_name or "")
    else:
        sender_out = _person(sender, idx, viewer)
    return {
        "id": msg.id, "conversation_id": msg.conversation_id, "sender": sender_out, "own": own,
        "delivery": msg.delivery if own else None, "email": bool(msg.external_from or msg.mail_message_id),
        "body": body, "integrity_ok": ok, "created_at": iso(msg.created_at),
        "attachments": [] if (removed or blocked) else [attachments[i] for i in (msg.attachment_ids or [])
                                                        if i in attachments],
        "removed": removed, "blocked_sender": blocked, "unread": (not own) and msg.id > last_read_id,
        "can_report": not own and not removed, "reported": msg.id in reported,
    }


def _detail(db: Session, user: AuthUser, conv: Conversation, part: Part, *, before: Optional[int] = None,
            limit: int = THREAD_DEFAULT) -> dict[str, Any]:
    snap = snapshot()
    idx = _index(snap)
    s2s, _days = _policy(snap)
    q = select(Message).where(Message.conversation_id == conv.id, Message.id > part.cleared_id)
    if before:
        q = q.where(Message.id < before)
    msgs = list(db.scalars(q.order_by(Message.id.desc()).limit(limit + 1)))
    has_more = len(msgs) > limit
    msgs = list(reversed(msgs[:limit]))
    member_ids: list[int] = []
    member_roles: dict[int, str] = {}
    if conv.kind != "broadcast":
        rows = [(r.user_id, r.recipient_role or "to") for r in db.execute(
            select(Part.user_id, Part.recipient_role).where(Part.conversation_id == conv.id)
            .order_by(Part.joined_at, Part.user_id))]
        rows = _visible_members(rows, conv, user.id)
        member_ids = [uid for uid, _r in rows]
        member_roles = dict(rows)
    wanted = set(member_ids) | {m.sender_id for m in msgs if m.sender_id} | ({conv.created_by} if conv.created_by
                                                                            else set())
    accounts = _accounts(db, wanted)
    my_blocks = _my_blocks(db, user.id)
    all_files = [fid for m in msgs if m.removed_at is None for fid in (m.attachment_ids or [])]
    attachments = {f["id"]: f for f in files.files_info(db, all_files, user, check_access=False)}
    reported = set(db.scalars(select(MessageReport.message_id).where(
        MessageReport.reporter_id == user.id, MessageReport.message_id.in_([m.id for m in msgs])))) if msgs else set()
    unread_map = {cid: int(n) for cid, _m, _a, n in _unread_rows(db, user.id) if cid == conv.id}
    summary = _summaries(db, user, [(part, conv)], idx, unread_map)[0]
    summary["participants"] = [{**_person(accounts.get(uid), idx, user), "recipient_role": member_roles.get(uid, "to")}
                               for uid in member_ids] if conv.kind != "broadcast" else []
    summary["reply"] = _reply_state(db, conv, user, s2s, accounts)
    other = None
    if conv.kind == "direct":
        other_id = next((uid for uid in member_ids if uid != user.id), None)
        other = accounts.get(other_id) if other_id else None
    summary["can_block"] = bool(other is not None and mx.can_block(other))
    summary["blocked"] = bool(other is not None and other.id in my_blocks)
    summary["other_user_id"] = other.id if other is not None else None
    if conv.kind == "broadcast" and conv.created_by == user.id:
        first_id = db.scalar(select(func.min(Message.id)).where(Message.conversation_id == conv.id)) or 0
        summary["read_count"] = db.scalar(select(func.count()).select_from(Part).where(
            Part.conversation_id == conv.id, Part.user_id != user.id, Part.last_read_id >= first_id)) or 0
        rows = list(db.execute(select(Part.user_id).where(Part.conversation_id == conv.id, Part.user_id != user.id)
                               .order_by(Part.user_id).limit(CREATOR_RECIPIENTS_SHOWN)))
        rec = _accounts(db, [r.user_id for r in rows])
        summary["recipients"] = sorted((_person(rec.get(r.user_id), idx, user) for r in rows),
                                       key=lambda p: mx.natural_key(p["name"]))
        summary["recipients_more"] = max(0, conv.recipient_count - len(rows))
    return {"conversation": summary,
            "messages": [_message_out(m, user, accounts, idx, my_blocks, attachments, reported, part.last_read_id)
                         for m in msgs],
            "has_more": has_more, "last_read_id": part.last_read_id}


@router.get("/messages/conversations/{conversation_id}")
def get_conversation(conversation_id: int, before: Optional[int] = Query(None, ge=1),
                     limit: int = Query(THREAD_DEFAULT, ge=1, le=THREAD_MAX),
                     user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Unterhaltung mit den neuesten Nachrichten (aufsteigend); ältere über ``before=<kleinste ID>``.
    Markiert nichts als gelesen (dafür ``POST …/read``)."""
    part, conv = _membership(db, conversation_id, user)
    return _detail(db, user, conv, part, before=before, limit=limit)


# =========================================================================== Neue Unterhaltung
@router.post("/messages/conversations", status_code=201)
def create_conversation(body: ConversationIn, request: Request, user: AuthUser = Depends(require(USE)),
                        db: Session = Depends(get_db)) -> dict:
    """Neue Unterhaltung: eine Person → ``direct``; mehrere Personen → ``group`` (alle sehen alle, Antworten an alle);
    Gruppen oder ``allow_replies`` ≠ ``all`` → ``broadcast`` (nur ``messages.broadcast``; Empfangende sehen nur die
    Zielgruppen, Antworten je nach ``allow_replies``)."""
    _ensure_can_send(db, user)
    snap = snapshot()
    idx = _index(snap)
    s2s, _days = _policy(snap)
    subject = mx.clean_subject(body.subject)
    text = mx.clean_body(body.body)
    _check_content(text, body.attachment_ids)
    draft = _draft_for(db, user, body.draft_id)
    can_broadcast = has(user, BROADCAST)
    user_recipients = [r for r in body.recipients if r.type == "user"]
    group_recipients = [r for r in body.recipients if r.type == "group"]
    externals, mail_account = _email_recipients(db, user, body, user_recipients)
    max_individuals = mx.MAX_INDIVIDUALS_BROADCAST if can_broadcast else mx.MAX_INDIVIDUALS
    if len({r.id for r in user_recipients}) > max_individuals:
        hint = "" if can_broadcast else " – für mehr Personen bitte eine Lehrkraft oder das Sekretariat fragen."
        raise _fail(422, "too_many_recipients",
                    f"Höchstens {max_individuals} einzelne Empfänger/innen je Nachricht{hint}")
    if len(group_recipients) > mx.MAX_GROUPS:
        raise _fail(422, "too_many_groups", f"Höchstens {mx.MAX_GROUPS} Gruppen je Rundschreiben.")
    directory = _directory(db)
    blocked_me = _blocked_by(db, user.id)
    individuals: dict[int, mx.Account] = {}
    for r in user_recipients:
        if r.id is None:
            raise _fail(422, "invalid_recipient", "Empfänger ohne Konto-ID.")
        acc = directory.get(r.id)
        try:
            mx.check_direct(user, acc, students_to_students=s2s, blocked=acc is not None and acc.id in blocked_me)
        except mx.MessagingError as exc:
            raise _mx_error(exc) from None
        individuals[acc.id] = acc
    roles: dict[int, str] = {}

    def _role(uid: int, role: str) -> None:
        if uid not in roles or ROLE_RANK[role] < ROLE_RANK[roles[uid]]:
            roles[uid] = role

    for r in user_recipients:
        if r.id is not None:
            _role(r.id, r.role)
    groups: list[mx.Group] = []
    members: set[int] = set()
    for r in group_recipients:
        try:
            group = mx.check_group(idx, user, r.kind or "", r.ref)
        except mx.MessagingError as exc:
            raise _mx_error(exc) from None
        if any(g.key == group.key for g in groups):
            continue
        groups.append(group)
        gm = mx.group_members(idx, directory, group.kind, group.ref)
        for uid in gm:
            _role(uid, r.role)
        members |= gm
    members.discard(user.id)
    members -= blocked_me          # Personal kann nicht blockiert werden – betrifft Rundschreiben praktisch nie
    recipients = set(individuals) | members
    if not recipients and not externals:
        raise _fail(422, "no_recipients", "Die ausgewählten Gruppen enthalten derzeit keine Personen mit Postfach.")
    if len(recipients) > mx.MAX_RECIPIENTS:
        raise _fail(422, "too_many_recipients", f"Zu viele Empfänger/innen (höchstens {mx.MAX_RECIPIENTS}).")
    if mx.students_conflict(user, (directory.by_id[i] for i in recipients if i in directory.by_id),
                            students_to_students=s2s):
        raise _fail(403, "students_to_students", "Nachrichten zwischen Schülerinnen und Schülern sind an dieser "
                                                 "Schule abgeschaltet.")
    allow = body.allow_replies if can_broadcast else "all"
    if groups or (allow != "all" and len(recipients) > 1):
        if not can_broadcast:
            raise _fail(403, "no_broadcast", "Rundschreiben sind für Ihr Konto nicht freigeschaltet.")
        kind = "broadcast"
    elif not recipients:
        kind, allow = "email", "all"               # nur externe E-Mail-Adressen
    elif len(recipients) == 1 and not externals and roles.get(next(iter(recipients)), "to") != "bcc":
        kind, allow = "direct", "all"
    else:
        kind = "group"
    if kind == "broadcast" and not subject:
        raise _fail(422, "subject_required", "Bitte einen Betreff für das Rundschreiben angeben.")
    _check_rate(db, user, new_conversation=True)
    now = utcnow()
    audience: list[dict[str, Any]] = [{"kind": g.kind, "ref": g.ref, "label": g.label} for g in groups]
    if kind == "broadcast" and individuals:
        n = len(individuals)
        audience.append({"kind": "individuals", "ref": "", "label": "1 einzelne Person" if n == 1
                         else f"{n} einzelne Personen"})
    conv = Conversation(kind=kind, allow_replies=allow, created_by=user.id, created_at=now,
                        audience=audience or None, recipient_count=len(recipients) + len(externals),
                        last_message_id=0, last_message_at=now, subject_enc="", external=externals or None,
                        mail_account_id=mail_account.id if mail_account is not None else None)
    db.add(conv)
    db.flush()                                    # ID für das AAD
    conv.subject_enc = crypto.encrypt_text(subject, conv.subject_aad)
    msg = _new_message(db, conv, user, text, body.attachment_ids)
    rows = [{"conversation_id": conv.id, "user_id": user.id, "last_read_id": msg.id, "last_read_at": now,
             "archived": False, "deleted": False, "muted": False, "cleared_id": 0, "has_incoming": False,
             "has_sent": True, "joined_at": now, "recipient_role": "from"}]
    rows += [{"conversation_id": conv.id, "user_id": uid, "last_read_id": 0, "last_read_at": None,
              "archived": False, "deleted": False, "muted": False, "cleared_id": 0, "has_incoming": True,
              "has_sent": False, "joined_at": now, "recipient_role": roles.get(uid, "to")}
             for uid in sorted(recipients)]
    for chunk in _chunks(rows):
        db.execute(insert(Part), list(chunk))
    _drop_draft(db, draft, keep=msg.attachment_ids or [])
    if kind == "broadcast":
        audit(db, user, "message.broadcast", f"conversation:{conv.id}",
              {"groups": [g.key for g in groups], "individuals": len(individuals), "recipients": len(recipients),
               "allow_replies": allow, "attachments": len(msg.attachment_ids or [])}, ip=client_ip(request))
    queued = _queue_email_hints(db, sorted(recipients), conv.id)
    db.commit()
    if externals:
        from .features_mail import deliver_external
        deliver_external(db, conv, msg, user.id, subject=subject, text=text,
                         preferred_account=mail_account.id if mail_account is not None else None)
        db.commit()
    _kick_notify(queued)
    _publish(recipients, conv.id, msg.id, new_message=True)
    _publish([user.id], conv.id)
    part = db.get(Part, (conv.id, user.id))
    return _detail(db, user, conv, part)


def _email_recipients(db: Session, user: AuthUser, body: "ConversationIn", user_recipients: list[RecipientIn]
                      ) -> tuple[list[dict[str, Any]], Any]:
    """E-Mail-Adressen auflösen: Adresse eines Schulkontos → wird zur Person (in ``user_recipients``), sonst extern
    (nur mit verbundenem E-Mail-Konto). Liefert ``(externe, Versandkonto)``."""
    from .features_mail import sending_account, valid_email

    externals: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for r in body.recipients:
        if r.type != "email":
            continue
        address = (r.email or "").strip().lower()
        if not valid_email(address):
            raise _fail(422, "invalid_email", f"Ungültige E-Mail-Adresse: {r.email}")
        internal = db.scalar(select(User.id).where(func.lower(User.email) == address, User.active.is_(True))
                             .order_by(User.id).limit(1))
        if internal is not None and internal != user.id:
            user_recipients.append(RecipientIn(type="user", id=internal, role=r.role))
            continue
        if address in seen:
            i = seen[address]
            if ROLE_RANK[r.role] < ROLE_RANK[externals[i]["role"]]:
                externals[i]["role"] = r.role
            continue
        seen[address] = len(externals)
        externals.append({"email": address, "name": (r.name or "").strip()[:200], "role": r.role})
    if len(externals) > mx.MAX_INDIVIDUALS_BROADCAST:
        raise _fail(422, "too_many_recipients", "Zu viele E-Mail-Adressen.")
    account = None
    if externals:
        account = sending_account(db, user.id, body.mail_account_id)
        if account is None:
            raise _fail(422, "no_mail_account", "Für Adressen außerhalb der Schule bitte zuerst unter Postfach → "
                                                "Einstellungen ein E-Mail-Konto verbinden.")
    return externals, account


# =========================================================================== Antworten
@router.post("/messages/conversations/{conversation_id}/messages", status_code=201)
def reply(conversation_id: int, body: ReplyIn, user: AuthUser = Depends(require(USE)),
          db: Session = Depends(get_db)) -> dict:
    """Antwort. Bei Rundschreiben mit ``allow_replies="sender"`` (oder bei abgeschaltetem Schüler-Austausch) entsteht
    eine **private** Unterhaltung mit der absendenden Person (``private: true``, ``conversation_id`` = neue ID)."""
    part, conv = _membership(db, conversation_id, user)
    if (conv.migrated_chat_id or 0) > 0:
        raise _fail(409, "moved_to_chats", "Diese Unterhaltung wurde nach „Chats & Gruppen“ verschoben – bitte dort "
                                           f"weiterschreiben (Chat {conv.migrated_chat_id}).")
    _ensure_can_send(db, user)
    snap = snapshot()
    s2s, _days = _policy(snap)
    text = mx.clean_body(body.body)
    _check_content(text, body.attachment_ids)
    draft = _draft_for(db, user, body.draft_id)
    state = _reply_state(db, conv, user, s2s)
    if not state["can_reply"]:
        raise _fail(403, state["code"] or "forbidden", state["reason"] or "Antworten ist hier nicht möglich.")
    target = conv
    private = state["mode"] == "private"
    if private:
        child = _private_child(db, conv, user.id)
        _check_rate(db, user, new_conversation=child is None)
        if child is None:
            now = utcnow()
            subject, _ok = _subject(conv)
            child = Conversation(kind="direct", allow_replies="all", created_by=user.id, created_at=now,
                                 parent_id=conv.id, audience=None, recipient_count=1, last_message_id=0,
                                 last_message_at=now, subject_enc="")
            db.add(child)
            db.flush()
            child.subject_enc = crypto.encrypt_text(mx.clean_subject(f"Re: {subject}") if subject else "",
                                                    child.subject_aad)
            db.add_all([Part(conversation_id=child.id, user_id=user.id, joined_at=now, has_sent=True),
                        Part(conversation_id=child.id, user_id=conv.created_by, joined_at=now, has_incoming=True)])
            db.flush()
        target = child
    else:
        _check_rate(db, user, new_conversation=False)
    prev = target.last_message_id
    msg = _new_message(db, target, user, text, body.attachment_ids)
    notify_ids, mail_ids = _deliver(db, target, msg, user.id, prev)
    _drop_draft(db, draft, keep=msg.attachment_ids or [])
    queued = _queue_email_hints(db, mail_ids, target.id)
    db.commit()
    if not private and target.external:
        from .features_mail import deliver_external
        subject, _ok = _subject(target)
        subj = subject if subject.lower().startswith(("re:", "aw:")) else (f"Re: {subject}" if subject else "")
        deliver_external(db, target, msg, user.id, subject=subj, text=text)
        db.commit()
    _kick_notify(queued)
    _publish(notify_ids, target.id, msg.id, new_message=True)
    _publish([user.id], target.id)
    snap_idx = _index(snap)
    accounts = _accounts(db, [user.id])
    my_part = db.get(Part, (target.id, user.id))
    attachments = {f["id"]: f for f in files.files_info(db, msg.attachment_ids or [], user, check_access=False)}
    return {"conversation_id": target.id, "private": private,
            "message": _message_out(msg, user, accounts, snap_idx, set(), attachments, set(),
                                    my_part.last_read_id if my_part else msg.id)}


# =========================================================================== Ordner, Lesestand, Löschen
@router.patch("/messages/conversations/{conversation_id}")
def patch_conversation(conversation_id: int, body: ParticipantPatch, user: AuthUser = Depends(require(USE)),
                       db: Session = Depends(get_db)) -> dict:
    """Archivieren/zurückholen, Stummschalten (keine Hinweise, kein Badge) – gilt nur für das eigene Postfach."""
    part, _conv = _membership(db, conversation_id, user)
    if body.archived is not None:
        part.archived = body.archived
    if body.muted is not None:
        part.muted = body.muted
    db.commit()
    _publish([user.id], conversation_id)
    return {"id": conversation_id, "archived": part.archived, "muted": part.muted,
            "counts": unread_counts(db, user.id)}


@router.post("/messages/conversations/{conversation_id}/read")
def mark_read(conversation_id: int, body: Optional[ReadIn] = None, user: AuthUser = Depends(require(USE)),
              db: Session = Depends(get_db)) -> dict:
    """Als gelesen markieren (bis ``up_to`` bzw. bis zur neuesten Nachricht)."""
    part, conv = _membership(db, conversation_id, user)
    up_to = conv.last_message_id if body is None or body.up_to is None else min(body.up_to, conv.last_message_id)
    if up_to > part.last_read_id:
        part.last_read_id = up_to
        part.last_read_at = utcnow()
        db.commit()
        _publish([user.id], conversation_id)
    return {"id": conversation_id, "last_read_id": part.last_read_id, "counts": unread_counts(db, user.id)}


@router.post("/messages/conversations/{conversation_id}/unread")
def mark_unread(conversation_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Als ungelesen markieren (ab der neuesten Nachricht anderer)."""
    part, conv = _membership(db, conversation_id, user)
    last_incoming = db.scalar(select(func.max(Message.id)).where(
        Message.conversation_id == conv.id, Message.id > part.cleared_id, Message.removed_at.is_(None),
        or_(Message.sender_id.is_(None), Message.sender_id != user.id)))
    if last_incoming:
        part.last_read_id = min(part.last_read_id, last_incoming - 1)
        db.commit()
        _publish([user.id], conversation_id)
    return {"id": conversation_id, "last_read_id": part.last_read_id, "counts": unread_counts(db, user.id)}


def _purge_conversation(db: Session, conv_id: int) -> int:
    """Unterhaltung endgültig löschen (inkl. Anhänge) – nur wenn niemand sie mehr sieht und nichts offen gemeldet ist."""
    msg_ids = list(db.scalars(select(Message.id).where(Message.conversation_id == conv_id)))
    removed = 0
    for chunk in _chunks(msg_ids):
        file_ids = list(db.scalars(select(StoredFile.id).where(StoredFile.ref_type == REF_TYPE,
                                                                StoredFile.ref_id.in_([str(i) for i in chunk]))))
        removed += files.delete_many(db, file_ids, hard=True)
    for draft_id in db.scalars(select(MessageDraft.id).where(MessageDraft.conversation_id == conv_id)):
        for fid in db.scalars(select(StoredFile.id).where(StoredFile.ref_type == DRAFT_REF_TYPE,
                                                           StoredFile.ref_id == str(draft_id))):
            files.detach(db, fid)
    db.execute(delete(Conversation).where(Conversation.id == conv_id))
    return removed


@router.delete("/messages/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, user: AuthUser = Depends(require(USE)),
                        db: Session = Depends(get_db)) -> dict:
    """„Für mich löschen“: ältere Nachrichten bleiben für mich ausgeblendet; eine neue Nachricht holt die
    Unterhaltung zurück (außer stummgeschaltet). Sieht niemand sie mehr, wird sie samt Anhängen endgültig gelöscht."""
    part, conv = _membership(db, conversation_id, user)
    part.deleted = True
    part.archived = False
    part.cleared_id = conv.last_message_id
    part.last_read_id = max(part.last_read_id, conv.last_message_id)
    db.flush()
    still_visible = db.scalar(select(exists().where(Part.conversation_id == conv.id, Part.deleted.is_(False))))
    open_reports = db.scalar(select(exists().where(MessageReport.message_id == Message.id,
                                                   Message.conversation_id == conv.id,
                                                   MessageReport.status == "offen")))
    purged = False
    if not still_visible and not open_reports:
        _purge_conversation(db, conv.id)
        purged = True
    db.commit()
    _publish([user.id], conversation_id)
    return {"deleted": conversation_id, "purged": purged, "counts": unread_counts(db, user.id)}


# =========================================================================== Melden
@router.post("/messages/conversations/{conversation_id}/messages/{message_id}/report", status_code=201)
def report_message(conversation_id: int, message_id: int, body: ReportIn, request: Request,
                   user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Nachricht an die Moderation melden (Grund wird verschlüsselt gespeichert). Eigene Nachrichten nicht."""
    part, _conv = _membership(db, conversation_id, user)
    msg = db.get(Message, message_id)
    if msg is None or msg.conversation_id != conversation_id or msg.id <= part.cleared_id:
        raise _not_found("Nachricht")
    if msg.sender_id == user.id:
        raise _fail(422, "own_message", "Eigene Nachrichten können nicht gemeldet werden.")
    if msg.removed_at is not None:
        raise _fail(409, "removed", "Diese Nachricht wurde bereits von der Moderation entfernt.")
    existing = db.scalar(select(MessageReport).where(MessageReport.message_id == msg.id,
                                                     MessageReport.reporter_id == user.id,
                                                     MessageReport.status == "offen"))
    if existing is not None:
        return {"id": existing.id, "status": existing.status, "duplicate": True}
    now = utcnow()
    report = MessageReport(message_id=msg.id, reporter_id=user.id, category=body.category, reason_enc="",
                           status="offen", resolution_enc="", created_at=now)
    db.add(report)
    db.flush()
    report.reason_enc = crypto.encrypt_text(body.reason.strip(), f"message_reports.reason:{report.id}")
    report.resolution_enc = crypto.encrypt_text("", f"message_reports.resolution:{report.id}")
    audit(db, user, "message.report", f"message:{msg.id}",
          {"report_id": report.id, "category": body.category, "conversation_id": conversation_id,
           "sender_id": msg.sender_id}, ip=client_ip(request))
    db.commit()
    _publish_moderation()
    return {"id": report.id, "status": report.status, "duplicate": False}


# =========================================================================== Adressbuch
@router.get("/messages/recipients")
def recipients(q: str = Query("", max_length=80), limit: int = Query(25, ge=1, le=50),
               user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Adressbuch: nur erlaubte Empfänger/Gruppen. Ohne Suchtext Vorschläge (Schüler/Eltern: Lehrkräfte der eigenen
    Klasse und Verwaltung; Personal: eigene Gruppen). Schüler/Eltern sehen von anderen nur Name, Rolle und Klasse."""
    snap = snapshot()
    idx = _index(snap)
    s2s, _days = _policy(snap)
    directory = _directory(db)
    blocked_me = _blocked_by(db, user.id)
    query = q.strip()
    if mx.query_tokens(query):
        people = mx.search_people(idx, directory, user, query, students_to_students=s2s, blocked_by=blocked_me,
                                  limit=limit)
        groups = mx.allowed_groups(idx, directory, user, query, limit=limit)
        suggested = False
    else:
        people = mx.suggestions(idx, directory, user, blocked_by=blocked_me, limit=min(limit, 12))
        groups = mx.allowed_groups(idx, directory, user, "", limit=40)
        suggested = True
    return {"people": people, "groups": groups, "suggestions": suggested, "query": query,
            "classes": mx.find_classes(idx, query) if query else [], "can_broadcast": has(user, BROADCAST)}


@router.get("/messages/recipients/class/{class_id}")
def recipients_class(class_id: str, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Klassenansicht im Adressbuch: Klassenleitung und Lehrkräfte; für Personal mit Sicht auf die Klasse auch alle
    Kinder mit ihren Eltern (Geschwister in anderen Klassen). ``groups``: erlaubte Rundschreiben an diese Klasse."""
    snap = snapshot()
    idx = _index(snap)
    s2s, _days = _policy(snap)
    try:
        return mx.class_roster(idx, _directory(db), user, class_id, students_to_students=s2s,
                               blocked_by=_blocked_by(db, user.id))
    except mx.MessagingError as exc:
        raise _fail(exc.status, exc.code, exc.message) from exc


@router.get("/messages/recipients/lookup")
def lookup_recipient(user_id: Optional[int] = Query(None, ge=1), teacher_id: Optional[str] = Query(None, max_length=40),
                     student_id: Optional[str] = Query(None, max_length=40),
                     parents_of: Optional[str] = Query(None, max_length=40),
                     user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Empfänger für Verknüpfungen aus anderen Bereichen („Nachricht an Lehrkraft XY“, „Eltern anschreiben“).

    ``user_id``/``teacher_id``: erreichbare Konten (jede/r darf jedem einzelnen Konto schreiben). ``student_id`` und
    ``parents_of`` nur für Personal, das die Schülerin/den Schüler sehen darf (``students.read`` mit Scope)."""
    snap = snapshot()
    idx = _index(snap)
    s2s, _days = _policy(snap)
    directory = _directory(db)
    blocked_me = _blocked_by(db, user.id)
    found: list[mx.Account] = []
    if user_id is not None:
        acc = directory.get(user_id)
        if acc is not None:
            found.append(acc)
    elif teacher_id:
        found = [directory.by_id[i] for i in directory.by_teacher.get(teacher_id, [])]
    elif student_id or parents_of:
        sid = student_id or parents_of or ""
        if not mx.is_staff(user) or not has(user, "students.read"):
            raise _fail(403, "forbidden", "Keine Berechtigung für diese Schülerin/diesen Schüler.")
        cl = idx.student_class(sid)
        if cl is None:
            raise _not_found("Schüler/in")
        if user.scope("students.read") == "own_classes" and cl not in idx.teacher_classes.get(
                user.teacher_id or "", set()):
            raise _fail(403, "forbidden", "Keine Berechtigung für diese Schülerin/diesen Schüler.")
        ids = directory.parents([sid]) if parents_of else directory.students([sid], routed=False)
        found = [directory.by_id[i] for i in sorted(ids)]
    else:
        raise _fail(422, "missing", "Bitte user_id, teacher_id, student_id oder parents_of angeben.")
    people = []
    for acc in found:
        if not acc.reachable or acc.id == user.id or acc.id in blocked_me:
            continue
        if not s2s and user.role == "schueler" and acc.role == "schueler":
            continue
        people.append(mx.person_card(idx, user, acc))
    if not people:
        raise _not_found("Empfänger/in")
    return {"people": people}


# =========================================================================== Blockieren
@router.get("/messages/blocks")
def list_blocks(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> list[dict]:
    """Von mir blockierte Konten."""
    snap = snapshot()
    idx = _index(snap)
    rows = list(db.execute(select(UserBlock.blocked_user_id, UserBlock.created_at)
                           .where(UserBlock.user_id == user.id).order_by(UserBlock.created_at)))
    accounts = _accounts(db, [r.blocked_user_id for r in rows])
    return [{"user": _person(accounts.get(r.blocked_user_id), idx, user), "user_id": r.blocked_user_id,
             "created_at": iso(r.created_at)} for r in rows]


@router.post("/messages/blocks", status_code=201)
def block_user(body: BlockIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Konto blockieren: es kann mir keine Nachrichten mehr schicken; seine Beiträge in Gruppen werden ausgeblendet.
    Schulpersonal kann nicht blockiert werden (bitte melden)."""
    if body.user_id == user.id:
        raise _fail(422, "self", "Sie können sich nicht selbst blockieren.")
    target = _accounts(db, [body.user_id]).get(body.user_id)
    if target is None:
        raise _not_found("Konto")
    if not mx.can_block(target):
        raise _fail(422, "staff", "Schulpersonal kann nicht blockiert werden. Problematische Nachrichten bitte melden – "
                                  "die Moderation kümmert sich darum.")
    if db.get(UserBlock, (user.id, target.id)) is None:
        db.add(UserBlock(user_id=user.id, blocked_user_id=target.id, created_at=utcnow()))
        db.commit()
    _publish([user.id])
    return {"blocked": target.id}


@router.delete("/messages/blocks/{blocked_user_id}")
def unblock_user(blocked_user_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    row = db.get(UserBlock, (user.id, blocked_user_id))
    if row is None:
        raise _not_found("Blockierung")
    db.delete(row)
    db.commit()
    _publish([user.id])
    return {"unblocked": blocked_user_id}


# =========================================================================== Einstellungen
def _settings_out(db: Session, user: AuthUser) -> dict[str, Any]:
    snap = snapshot()
    s2s, days = _policy(snap)
    row = db.get(MessageUserSettings, user.id)
    until = _suspended_until(db, user.id)
    reason = ""
    if until is not None and row is not None:
        reason, _ok = _decrypt(row.suspension_reason_enc, f"message_user_settings.suspension_reason:{user.id}",
                               "Sperrgrund", user.id)
    can_broadcast = has(user, BROADCAST)
    return {
        "email_notify": True if row is None else bool(row.email_notify),
        "email_available": bool(user.email) and bool(getattr(config, "smtp_enabled", False)),
        "has_email": bool(user.email),
        "suspended_until": iso(until), "suspension_reason": reason,
        "students_to_students": s2s, "retention_days": days,
        "can_broadcast": can_broadcast, "broadcast_scope": user.scope(BROADCAST) if can_broadcast else None,
        "can_moderate": has(user, MODERATE),
        "limits": {"subject": mx.MAX_SUBJECT, "body": mx.MAX_BODY, "attachments": mx.MAX_ATTACHMENTS,
                   "individuals": mx.MAX_INDIVIDUALS_BROADCAST if can_broadcast else mx.MAX_INDIVIDUALS,
                   "groups": mx.MAX_GROUPS},
        "report_categories": [{"key": k, "label": REPORT_CATEGORY_LABELS.get(k, k)} for k in REPORT_CATEGORIES],
        "reply_modes": [{"key": k, "label": v} for k, v in mx.REPLY_MODE_LABELS.items()],
        "purpose": PURPOSE,
    }


@router.get("/messages/settings")
def get_settings(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Eigene Postfach-Einstellungen, Grenzen, Schulregeln (Schüler-Austausch, Aufbewahrung), eigene Sperre."""
    return _settings_out(db, user)


@router.put("/messages/settings")
def put_settings(body: SettingsIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    row = db.get(MessageUserSettings, user.id)
    if row is None:
        row = MessageUserSettings(user_id=user.id, email_notify=True, suspension_reason_enc="")
        db.add(row)
    if body.email_notify is not None:
        row.email_notify = body.email_notify
    row.updated_at = utcnow()
    db.commit()
    return _settings_out(db, user)


# =========================================================================== Entwürfe
def _draft_aad(draft: MessageDraft) -> str:
    return f"message_drafts.data:{draft.user_id}:{draft.id}"


def _draft_labels(db: Session, user: AuthUser, recipients: list[dict[str, Any]], snap) -> list[str]:
    idx = _index(snap)
    ids = [r.get("id") for r in recipients if r.get("type") == "user" and r.get("id")]
    accounts = _accounts(db, ids)
    labels = []
    for r in recipients:
        if r.get("type") == "user":
            acc = accounts.get(int(r.get("id") or 0))
            labels.append(acc.name if acc else DELETED_NAME)
        elif r.get("type") == "email":
            labels.append(r.get("name") or r.get("email") or "")
        else:
            try:
                labels.append(mx.group_label(idx, r.get("kind") or "", r.get("ref") or ""))
            except mx.MessagingError:
                labels.append("Unbekannte Gruppe")
    return labels


def _draft_out(db: Session, user: AuthUser, draft: MessageDraft, *, full: bool = True) -> dict[str, Any]:
    raw, ok = _decrypt(draft.data_enc, _draft_aad(draft), "Entwurf", draft.id)
    data: dict[str, Any] = {}
    if ok and raw:
        try:
            data = json.loads(raw)
        except ValueError:
            ok = False
    out = {"id": draft.id, "conversation_id": draft.conversation_id, "subject": data.get("subject", ""),
           "preview": _preview(data.get("body", ""), 100), "recipient_labels": data.get("recipient_labels", []),
           "updated_at": iso(draft.updated_at), "created_at": iso(draft.created_at), "integrity_ok": ok}
    if full:
        out.update({"recipients": data.get("recipients", []), "body": data.get("body", ""),
                    "allow_replies": data.get("allow_replies", "all"),
                    "attachments": files.files_info(db, data.get("attachment_ids", []), user)})
    return out


def _save_draft(db: Session, user: AuthUser, draft: MessageDraft, body: DraftIn) -> None:
    snap = snapshot()
    if body.conversation_id:
        _membership(db, body.conversation_id, user)
    recipients = [r.model_dump() for r in body.recipients]
    old_ids = set(db.scalars(select(StoredFile.id).where(StoredFile.ref_type == DRAFT_REF_TYPE,
                                                          StoredFile.ref_id == str(draft.id))))
    new_ids = list(dict.fromkeys(body.attachment_ids))
    for fid in old_ids - set(new_ids):
        files.detach(db, fid)
    for fid in new_ids:
        if fid not in old_ids:
            files.attach(db, fid, user, DRAFT_REF_TYPE, draft.id)
    data = {"recipients": recipients, "recipient_labels": _draft_labels(db, user, recipients, snap),
            "subject": mx.clean_subject(body.subject), "body": body.body.replace("\r\n", "\n"),
            "allow_replies": body.allow_replies, "attachment_ids": new_ids}
    draft.conversation_id = body.conversation_id
    draft.data_enc = crypto.encrypt_text(json.dumps(data, ensure_ascii=False), _draft_aad(draft))
    draft.updated_at = utcnow()


@router.get("/messages/drafts")
def list_drafts(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(MessageDraft).where(MessageDraft.user_id == user.id)
                      .order_by(MessageDraft.updated_at.desc()).limit(MAX_DRAFTS))
    return [_draft_out(db, user, d, full=False) for d in rows]


@router.post("/messages/drafts", status_code=201)
def create_draft(body: DraftIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    count = db.scalar(select(func.count()).select_from(MessageDraft).where(MessageDraft.user_id == user.id)) or 0
    if count >= MAX_DRAFTS:
        raise _fail(409, "too_many_drafts", f"Höchstens {MAX_DRAFTS} Entwürfe – bitte alte Entwürfe löschen.")
    now = utcnow()
    draft = MessageDraft(user_id=user.id, data_enc="", created_at=now, updated_at=now)
    db.add(draft)
    db.flush()
    _save_draft(db, user, draft, body)
    db.commit()
    return _draft_out(db, user, draft)


@router.get("/messages/drafts/{draft_id}")
def get_draft(draft_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    return _draft_out(db, user, _draft_for(db, user, draft_id))


@router.put("/messages/drafts/{draft_id}")
def update_draft(draft_id: int, body: DraftIn, user: AuthUser = Depends(require(USE)),
                 db: Session = Depends(get_db)) -> dict:
    draft = _draft_for(db, user, draft_id)
    _save_draft(db, user, draft, body)
    db.commit()
    return _draft_out(db, user, draft)


@router.delete("/messages/drafts/{draft_id}")
def delete_draft(draft_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Entwurf löschen (angehängte Uploads werden gelöst und verfallen nach 24 h)."""
    draft = _draft_for(db, user, draft_id)
    _drop_draft(db, draft)
    db.commit()
    return {"deleted": draft_id}


# =========================================================================== Moderation
def _report_out(db: Session, report: MessageReport, msg: Optional[Message], accounts: dict[int, mx.Account],
                idx: mx.SchoolIndex, viewer: AuthUser, counts: dict[int, int]) -> dict[str, Any]:
    reason, ok = _decrypt(report.reason_enc, f"message_reports.reason:{report.id}", "Meldegrund", report.id)
    resolution, ok2 = _decrypt(report.resolution_enc, f"message_reports.resolution:{report.id}", "Vermerk",
                               report.id)
    sender_id = msg.sender_id if msg is not None else None
    conv = db.get(Conversation, msg.conversation_id) if msg is not None else None
    return {
        "id": report.id, "status": report.status, "status_label": REPORT_STATUS_LABELS.get(report.status, report.status),
        "category": report.category, "category_label": REPORT_CATEGORY_LABELS.get(report.category, report.category),
        "reason": reason, "resolution": resolution, "integrity_ok": ok and ok2,
        "created_at": iso(report.created_at), "handled_at": iso(report.handled_at),
        "actions": list(report.actions or []),
        "reporter": _person(accounts.get(report.reporter_id) if report.reporter_id else None, idx, viewer),
        "sender": _person(accounts.get(sender_id) if sender_id else None, idx, viewer),
        "sender_id": sender_id,
        "handled_by": _person(accounts.get(report.handled_by), idx, viewer) if report.handled_by else None,
        "message_id": report.message_id, "conversation_id": msg.conversation_id if msg is not None else None,
        "conversation_kind": conv.kind if conv is not None else None,
        "conversation_kind_label": KIND_LABELS.get(conv.kind, "") if conv is not None else "",
        "message_created_at": iso(msg.created_at) if msg is not None else None,
        "message_removed": bool(msg is not None and msg.removed_at is not None),
        "reports_on_message": counts.get(report.message_id, 1),
        "own": sender_id == viewer.id,
    }


def _report_accounts(db: Session, reports: list[MessageReport], msgs: dict[int, Message]) -> dict[int, mx.Account]:
    ids: set[int] = set()
    for r in reports:
        ids |= {i for i in (r.reporter_id, r.handled_by) if i}
        msg = msgs.get(r.message_id)
        if msg is not None and msg.sender_id:
            ids.add(msg.sender_id)
    return _accounts(db, ids)


@router.get("/messages/moderation/reports")
def list_reports(status: Literal["offen", "erledigt", "abgelehnt", "alle"] = "offen",
                 limit: int = Query(100, ge=1, le=500), user: AuthUser = Depends(require(MODERATE)),
                 db: Session = Depends(get_db)) -> dict:
    """Gemeldete Nachrichten (ohne Nachrichteninhalt – den zeigt erst die Einzelansicht, protokolliert)."""
    snap = snapshot()
    idx = _index(snap)
    q = select(MessageReport)
    if status != "alle":
        q = q.where(MessageReport.status == status)
    reports = list(db.scalars(q.order_by(MessageReport.created_at.desc(), MessageReport.id.desc()).limit(limit)))
    msg_ids = {r.message_id for r in reports}
    msgs = {m.id: m for chunk in _chunks(sorted(msg_ids)) for m in db.scalars(select(Message).where(
        Message.id.in_(chunk)))}
    counts = {mid: n for mid, n in db.execute(select(MessageReport.message_id, func.count(MessageReport.id))
                                              .where(MessageReport.message_id.in_(sorted(msg_ids)))
                                              .group_by(MessageReport.message_id))} if msg_ids else {}
    accounts = _report_accounts(db, reports, msgs)
    totals = {s: 0 for s in REPORT_STATUS_LABELS}
    for s, n in db.execute(select(MessageReport.status, func.count(MessageReport.id)).group_by(MessageReport.status)):
        totals[s] = int(n)
    return {"items": [_report_out(db, r, msgs.get(r.message_id), accounts, idx, user, counts) for r in reports],
            "counts": totals}


def _report_or_404(db: Session, report_id: int) -> tuple[MessageReport, Message]:
    report = db.get(MessageReport, report_id)
    msg = db.get(Message, report.message_id) if report is not None else None
    if report is None or msg is None:
        raise _not_found("Meldung")
    return report, msg


@router.get("/messages/moderation/reports/{report_id}")
def get_report(report_id: int, request: Request, context: int = Query(0, ge=0, le=MAX_CONTEXT),
               user: AuthUser = Depends(require(MODERATE)), db: Session = Depends(get_db)) -> dict:
    """Meldung mit **entschlüsselter** Nachricht (und auf Wunsch ``context`` Nachrichten davor/danach).
    Jede Ansicht wird im Audit-Protokoll vermerkt (``message.moderation_view``)."""
    report, msg = _report_or_404(db, report_id)
    snap = snapshot()
    idx = _index(snap)
    conv = db.get(Conversation, msg.conversation_id)
    shown = [msg]
    if context:
        before = list(db.scalars(select(Message).where(Message.conversation_id == msg.conversation_id,
                                                       Message.id < msg.id).order_by(Message.id.desc())
                                 .limit(context)))
        after = list(db.scalars(select(Message).where(Message.conversation_id == msg.conversation_id,
                                                      Message.id > msg.id).order_by(Message.id).limit(context)))
        shown = list(reversed(before)) + [msg] + after
    others = list(db.scalars(select(MessageReport).where(MessageReport.message_id == msg.id)
                             .order_by(MessageReport.created_at)))
    accounts = _report_accounts(db, others, {msg.id: msg})
    accounts.update(_accounts(db, {m.sender_id for m in shown if m.sender_id}))
    counts = {msg.id: len(others)}
    all_files = [fid for m in shown for fid in (m.attachment_ids or [])]
    attachments = {f["id"]: f for f in files.files_info(db, all_files, user, check_access=False)}
    out_msgs = []
    for m in shown:
        body, ok = _body(m)
        sender = accounts.get(m.sender_id) if m.sender_id else None
        out_msgs.append({"id": m.id, "body": body, "integrity_ok": ok, "created_at": iso(m.created_at),
                         "sender": _person(sender, idx, user), "reported": m.id == msg.id,
                         "removed": m.removed_at is not None,
                         "attachments": [attachments[i] for i in (m.attachment_ids or []) if i in attachments]})
    subject, _ok = _subject(conv) if conv is not None else ("", True)
    sender_reports = 0
    if msg.sender_id:
        sender_reports = db.scalar(select(func.count(MessageReport.id)).join(Message, Message.id ==
                                                                             MessageReport.message_id)
                                   .where(Message.sender_id == msg.sender_id)) or 0
    suspended = _suspended_until(db, msg.sender_id) if msg.sender_id else None
    audit(db, user, "message.moderation_view", f"message_report:{report.id}",
          {"message_ids": [m.id for m in shown], "conversation_id": msg.conversation_id}, ip=client_ip(request))
    db.commit()
    data = _report_out(db, report, msg, accounts, idx, user, counts)
    data.update({
        "messages": out_msgs, "subject": subject,
        "conversation": {"id": conv.id if conv else None, "kind": conv.kind if conv else None,
                         "kind_label": KIND_LABELS.get(conv.kind, "") if conv else "",
                         "recipient_count": conv.recipient_count if conv else 0,
                         "audience": _audience(conv) if conv else []},
        "other_reports": [_report_out(db, r, msg, accounts, idx, user, counts) for r in others if r.id != report.id],
        "sender_reports": int(sender_reports), "sender_suspended_until": iso(suspended),
        "can_resolve": msg.sender_id != user.id,
    })
    return data


def _suspend(db: Session, actor: AuthUser, target_id: int, days: int, reason: str) -> datetime:
    target = _accounts(db, [target_id]).get(target_id)
    if target is None:
        raise _not_found("Konto")
    if target.id == actor.id:
        raise _fail(422, "self", "Sie können Ihr eigenes Postfach nicht sperren.")
    if target.role == "admin" and actor.role != "admin":
        raise _fail(403, "forbidden", "Administrationskonten kann nur die Administration sperren.")
    now = utcnow()
    row = db.get(MessageUserSettings, target.id)
    if row is None:
        row = MessageUserSettings(user_id=target.id, email_notify=True, suspension_reason_enc="")
        db.add(row)
    row.suspended_until = now + timedelta(days=days)
    row.suspended_by = actor.id
    row.suspended_at = now
    row.suspension_reason_enc = crypto.encrypt_text(reason.strip(),
                                                    f"message_user_settings.suspension_reason:{target.id}")
    row.updated_at = now
    return row.suspended_until


@router.post("/messages/moderation/reports/{report_id}/resolve")
def resolve_report(report_id: int, body: ResolveIn, request: Request, user: AuthUser = Depends(require(MODERATE)),
                   db: Session = Depends(get_db)) -> dict:
    """Meldung abschließen (``erledigt``/``abgelehnt``), optional Nachricht ausblenden und das Postfach der
    absendenden Person vorübergehend sperren. Alle offenen Meldungen derselben Nachricht werden mit abgeschlossen."""
    report, msg = _report_or_404(db, report_id)
    if msg.sender_id == user.id:
        raise _fail(409, "own_message", "Meldungen über eigene Nachrichten bearbeitet bitte eine andere Person der "
                                        "Moderation.")
    if report.status != "offen":
        raise _fail(409, "closed", "Diese Meldung ist bereits abgeschlossen.")
    now = utcnow()
    actions: list[str] = []
    if body.remove_message and msg.removed_at is None:
        msg.removed_at = now
        msg.removed_by = user.id
        actions.append("removed")
    suspended_until = None
    if body.suspend_days:
        if not msg.sender_id:
            raise _fail(422, "no_sender", "Das Konto der absendenden Person gibt es nicht mehr.")
        suspended_until = _suspend(db, user, msg.sender_id, body.suspend_days, body.resolution or
                                   f"Meldung #{report.id}")
        actions.append("suspended")
    related = list(db.scalars(select(MessageReport).where(MessageReport.message_id == msg.id,
                                                          MessageReport.status == "offen")))
    for r in related:
        r.status = body.status
        r.handled_by = user.id
        r.handled_at = now
        r.resolution_enc = crypto.encrypt_text(body.resolution.strip(), f"message_reports.resolution:{r.id}")
        r.actions = actions
    audit(db, user, "message.moderate", f"message:{msg.id}",
          {"report_ids": [r.id for r in related], "status": body.status, "actions": actions,
           "sender_id": msg.sender_id, "suspend_days": body.suspend_days}, ip=client_ip(request))
    db.commit()
    _publish_moderation()
    if "removed" in actions:
        _publish(db.scalars(select(Part.user_id).where(Part.conversation_id == msg.conversation_id)),
                 msg.conversation_id)
    return {"id": report.id, "status": body.status, "actions": actions, "resolved": [r.id for r in related],
            "suspended_until": iso(suspended_until)}


@router.get("/messages/moderation/suspensions")
def list_suspensions(user: AuthUser = Depends(require(MODERATE)), db: Session = Depends(get_db)) -> list[dict]:
    """Aktuell gesperrte Postfächer."""
    snap = snapshot()
    idx = _index(snap)
    rows = list(db.scalars(select(MessageUserSettings).where(MessageUserSettings.suspended_until > utcnow())
                           .order_by(MessageUserSettings.suspended_until)))
    accounts = _accounts(db, {r.user_id for r in rows} | {r.suspended_by for r in rows if r.suspended_by})
    out = []
    for r in rows:
        reason, ok = _decrypt(r.suspension_reason_enc, f"message_user_settings.suspension_reason:{r.user_id}",
                              "Sperrgrund", r.user_id)
        out.append({"user_id": r.user_id, "user": _person(accounts.get(r.user_id), idx, user),
                    "suspended_until": iso(r.suspended_until), "suspended_at": iso(r.suspended_at),
                    "suspended_by": _person(accounts.get(r.suspended_by), idx, user) if r.suspended_by else None,
                    "reason": reason, "integrity_ok": ok})
    return out


@router.post("/messages/moderation/users/{target_id}/suspend")
def suspend_user(target_id: int, body: SuspendIn, request: Request, user: AuthUser = Depends(require(MODERATE)),
                 db: Session = Depends(get_db)) -> dict:
    """Postfach eines Kontos vorübergehend für das Senden sperren (Lesen bleibt möglich)."""
    until = _suspend(db, user, target_id, body.days, body.reason)
    audit(db, user, "message.suspend", f"user:{target_id}", {"days": body.days}, ip=client_ip(request))
    db.commit()
    _publish([target_id])
    return {"user_id": target_id, "suspended_until": iso(until)}


@router.delete("/messages/moderation/users/{target_id}/suspend")
def unsuspend_user(target_id: int, request: Request, user: AuthUser = Depends(require(MODERATE)),
                   db: Session = Depends(get_db)) -> dict:
    row = db.get(MessageUserSettings, target_id)
    if row is None or row.suspended_until is None:
        raise _not_found("Sperre")
    row.suspended_until = None
    row.suspended_by = None
    row.suspended_at = None
    row.suspension_reason_enc = ""
    row.updated_at = utcnow()
    audit(db, user, "message.unsuspend", f"user:{target_id}", {}, ip=client_ip(request))
    db.commit()
    _publish([target_id])
    return {"user_id": target_id, "suspended_until": None}


@router.post("/messages/moderation/retention")
def retention_now(request: Request, user: AuthUser = Depends(require(MODERATE)), db: Session = Depends(get_db)
                  ) -> dict:
    """Aufbewahrungsfrist sofort anwenden (sonst automatisch in der Wartung)."""
    result = run_retention()
    audit(db, user, "message.retention", "messages", result, ip=client_ip(request))
    db.commit()
    return result


# =========================================================================== Wartung: Aufbewahrungsfrist
_retention_lock = threading.Lock()
_last_retention = 0.0


def _expire_chat_copies(db: Session, cutoff: datetime) -> int:
    """Aus dem Postfach nach Chats übernommene (serverseitig verschlüsselte) Nachrichten unterliegen derselben
    Aufbewahrungsfrist wie das Original."""
    from schulmanager.server.feature_models.chats import ChatMessage

    return db.execute(delete(ChatMessage).where(ChatMessage.legacy_source_message_id.is_not(None),
                                                ChatMessage.created_at < cutoff)).rowcount or 0


def run_retention(now: Optional[datetime] = None, days: Optional[int] = None) -> dict[str, int]:
    """Wartung des Postfachs (für ``maintenance.run_maintenance``):

    * Nachrichten älter als ``settings.messaging_retention_days`` (0 = nie) samt Anhängen endgültig löschen –
      außer offen gemeldete (Beweissicherung bis zur Entscheidung); danach leere Unterhaltungen,
    * Entwürfe und abgeschlossene Meldungen, die älter als die Frist sind,
    * abgelaufene Postfach-Sperren aufheben.
    """
    global _last_retention
    with _retention_lock:
        _last_retention = time.monotonic()
        if days is None:
            from schulmanager.server.store import get_store

            days = max(0, int(getattr(get_store().school.settings, "messaging_retention_days", 365) or 0))
        now = now or utcnow()
        result = {"messages_expired": 0, "conversations_removed": 0, "attachments_removed": 0, "drafts_expired": 0,
                  "reports_removed": 0, "suspensions_ended": 0}
        with session_scope() as db:
            result["suspensions_ended"] = db.execute(
                update(MessageUserSettings).where(MessageUserSettings.suspended_until.is_not(None),
                                                  MessageUserSettings.suspended_until <= now)
                .values(suspended_until=None, suspended_by=None, suspended_at=None, suspension_reason_enc="")
            ).rowcount or 0
            if days > 0:
                cutoff = now - timedelta(days=days)
                open_reported = select(MessageReport.message_id).where(MessageReport.status == "offen")
                last = 0
                while True:
                    ids = list(db.scalars(select(Message.id).where(Message.created_at < cutoff, Message.id > last,
                                                                   Message.id.not_in(open_reported))
                                          .order_by(Message.id).limit(CHUNK)))
                    if not ids:
                        break
                    last = ids[-1]
                    file_ids = list(db.scalars(select(StoredFile.id).where(
                        StoredFile.ref_type == REF_TYPE, StoredFile.ref_id.in_([str(i) for i in ids]))))
                    result["attachments_removed"] += files.delete_many(db, file_ids, hard=True)
                    db.execute(delete(Message).where(Message.id.in_(ids)))
                    result["messages_expired"] += len(ids)
                empty = list(db.scalars(select(Conversation.id).where(
                    ~exists().where(Message.conversation_id == Conversation.id))))
                for cid in empty:
                    _purge_conversation(db, cid)
                result["conversations_removed"] = len(empty)
                old_drafts = list(db.scalars(select(MessageDraft.id).where(MessageDraft.updated_at < cutoff)))
                for chunk in _chunks(old_drafts):
                    file_ids = list(db.scalars(select(StoredFile.id).where(
                        StoredFile.ref_type == DRAFT_REF_TYPE, StoredFile.ref_id.in_([str(i) for i in chunk]))))
                    files.delete_many(db, file_ids, hard=True)
                    db.execute(delete(MessageDraft).where(MessageDraft.id.in_(chunk)))
                result["drafts_expired"] = len(old_drafts)
                result["messages_expired"] += _expire_chat_copies(db, cutoff)
                result["reports_removed"] = db.execute(
                    delete(MessageReport).where(MessageReport.status != "offen", MessageReport.handled_at.is_not(None),
                                                MessageReport.handled_at < cutoff)).rowcount or 0
        if any(result.values()):
            log.info("Postfach-Wartung: %s", result)
        return result


def _retention_safe() -> None:
    try:
        run_retention()
    except Exception:  # noqa: BLE001 - Hintergrundwartung darf nichts stören
        log.exception("Postfach-Wartung (Aufbewahrungsfrist) fehlgeschlagen")


def _maybe_retention() -> None:
    """Notbehelf, solange ``maintenance.run_maintenance`` die Postfach-Wartung nicht selbst aufruft: höchstens alle
    6 Stunden im Hintergrund (nur wenn die Wartung aktiv ist, ``SM_MAINTENANCE_INTERVAL`` > 0)."""
    global _last_retention
    if getattr(config, "maintenance_interval", 0) <= 0:
        return
    if _last_retention and time.monotonic() - _last_retention < RETENTION_INTERVAL_SECONDS:
        return
    if _retention_lock.locked():
        return
    _last_retention = time.monotonic()
    threading.Thread(target=_retention_safe, name="sm-messages-retention", daemon=True).start()
