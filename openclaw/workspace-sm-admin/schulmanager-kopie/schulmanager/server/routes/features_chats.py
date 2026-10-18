"""Chats: Einzelchats, selbst erstellte Gruppen, Klassenchats (mit/ohne Lehrkräfte, Elternchats) – Ende-zu-Ende
verschlüsselt (siehe ``feature_models/chats.py``). Der Server prüft nur, **wer** mit **wem** chatten darf, und
verteilt Chiffrate; Inhalte kann er nicht lesen.

Rechte: ``messages.use``. Wer wen hinzufügen darf, folgt den Regeln des Postfachs (``schulmanager/messaging.py``:
Blockierungen, ``messaging_students_to_students``, nur erreichbare Konten). Klassen als Ganzes:

* Personal: eigene Klassen (Lehrkräfte mit Scope ``own_classes``) bzw. alle – Schüler/innen, Eltern, Lehrkräfte
* Schüler/innen: die eigene Klasse (nur Mitschüler/innen)
* Eltern: Elternchat der Klassen ihrer Kinder

Endpunkte (Präfix ``/api/v1``)
-----------------------------
* ``POST/GET /chats/devices``, ``DELETE /chats/devices/{id}`` – Geräte mit öffentlichem Schlüssel
* ``POST /chats/devices/reset`` (alle Geräteschlüssel widerrufen, neues Gerät anlegen) ·
  ``POST /chats/devices/{id}/ack`` (unbekanntes Gerät als bekannt bestätigen)
* Verlauf auf ein neues Gerät übertragen: ``POST /chat-links`` (Anfrage mit Code), ``POST /chat-links/lookup``,
  ``POST /chat-links/{id}/approve``, ``GET/DELETE /chat-links/{id}``; ``GET /chat-keys/pending`` (lesbare Schlüssel
  zum Neuverpacken) und ``POST /chat-keys`` (neu verpackte Schlüssel ergänzen – nur eigene Geräte, nur Nachrichten,
  die man selbst lesen darf)
* Wiederherstellung mit Passwort (optional): ``GET/PUT/DELETE /chat-keys/backup`` – der Server speichert nur den
  öffentlichen Archivschlüssel (als Gerät ``kind="archive"``) und das im Browser verschlüsselte Blob
* ``GET /chats`` · ``POST /chats`` ``{kind:"direct", user_ids:[id]}`` bzw. ``{kind:"group", title, user_ids,
  classes:[{class_id, students, teachers, parents}]}`` · ``GET/PATCH /chats/{id}``
* ``GET /chats/{id}/devices`` – öffentliche Schlüssel aller Mitgliedsgeräte (zum Verschlüsseln)
* ``GET /chats/{id}/messages?device_id=&before=`` · ``POST /chats/{id}/messages`` ``{device_id, nonce, ciphertext,
  keys:[{device_id, nonce, wrapped}], reply_to?}`` – 409 ``devices_changed``, wenn Geräte fehlen
* ``DELETE /chats/{id}/messages/{mid}`` (eigene, für alle) · ``POST /chats/{id}/read``
* ``POST/DELETE /chats/{id}/members`` · ``PATCH /chats/{id}/members/{uid}`` ``{admin?, can_post?}``
* ``PATCH /chats/{id}`` ``{title?, post_mode?, muted?, archived?}`` – ``muted``/``archived`` gelten je Person

Schreibrechte (der Server erzwingt sie bei Nachrichten und Bild-Uploads): ``post_mode`` ``all`` (alle Mitglieder),
``admins`` (nur Admins – z. B. Lehrkraft-Chat, Schüler/innen lesen nur) oder ``selected`` (Admins und Mitglieder mit
``can_post``). ``only_admins_post`` bleibt als Kurzform von ``post_mode == "admins"`` erhalten.
Archiv: je Person; eine neue Nachricht holt den Chat zurück in die Liste, außer er ist stummgeschaltet.
* ``POST /chats/{id}/attachments`` (roher, im Browser verschlüsselter Bild-Blob, ≤ 5 MB) · ``GET
  /chats/{id}/attachments/{aid}`` – die Nachricht nennt die Blobs per ``attachment_ids``; Schlüssel/Typ stehen nur im
  verschlüsselten Inhalt
* ``POST /chats/{id}/messages/{mid}/report`` ``{reason, content, images:[{data}]}`` (Klartext/Bilder schickt die
  meldende Person freiwillig; erneutes Melden aktualisiert die offene Meldung) · ``GET /chat-reports/{id}/images/{n}``
* ``GET /chats/unread`` · Moderation (``messages.moderate``): ``GET /chat-reports``, ``POST /chat-reports/{id}``
Live: ``change`` ``{scope:["chats"], chat_id}`` nur an Mitglieder (ohne Inhalt).
"""
from __future__ import annotations

import base64
import binascii
import logging
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, exists, func, select, update
from sqlalchemy.orm import Session, aliased

from schulmanager import learning as lx
from schulmanager import messaging as mx
from schulmanager.server import crypto
from schulmanager.server.config import config
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, require
from schulmanager.server.events import bus
from schulmanager.server.feature_models.chats import (Chat, ChatAttachment, ChatDevice, ChatKeyBackup, ChatLinkRequest,
                                                      ChatMember, ChatMessage, ChatMessageKey, ChatReport,
                                                      ChatReportImage)

from schulmanager.server.learning_service import ChatPollMeta, chat_poll_row, chat_poll_states, delete_chat_poll, delete_chat_polls

from .features_common import has, snapshot
from .features_messages import (MODERATE, USE, _blocked_by, _directory, _ensure_can_send, _fail, _index, _mx_error,
                                _person, _policy)

log = logging.getLogger("schulmanager.chats")
router = APIRouter(tags=["Chats"])

LIVE_SCOPE = "chats"
MAX_DEVICES = 10
LINK_TTL = timedelta(minutes=15)          # Code gilt so lange zum Freigeben
LINK_APPROVED_TTL = timedelta(hours=2)    # nach der Freigabe so lange darf übertragen werden
LINK_PER_HOUR = 6                         # neue Anfragen je Konto und Stunde
LOOKUP_FAILS = 10                         # falsche Codes je Konto und 10 Minuten
TRANSFER_BATCH = 200
MAX_BACKUP_BLOB = 2000
MAX_MEMBERS = 400
MAX_CIPHERTEXT = 120_000          # Base64-Zeichen (≈ 90 KB Text)
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # Bild/GIF im Klartext (der Browser prüft vor dem Verschlüsseln)
MAX_BLOB_BYTES = MAX_IMAGE_BYTES + 64   # verschlüsselt: + 16 Byte Authentisierung (Reserve)
MAX_IMAGES = 4                    # Bilder je Nachricht bzw. Meldung
MAX_PENDING = 12                  # noch nicht gesendete Uploads je Person
PENDING_TTL = timedelta(hours=24)
# Bilder, die die meldende Person für die Moderation mitschickt: nur Rasterformate (nie SVG), Typ aus dem Inhalt
IMAGE_MAGIC = ((b"\x89PNG\r\n\x1a\n", "image/png"), (b"\xff\xd8\xff", "image/jpeg"), (b"GIF87a", "image/gif"),
               (b"GIF89a", "image/gif"))
PAGE = 50


# =========================================================================== Hilfen
def _b64(value: str, size: Optional[int] = None, what: str = "Wert") -> str:
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise _fail(422, "invalid_base64", f"{what}: kein gültiges Base64.") from None
    if size is not None and len(raw) != size:
        raise _fail(422, "invalid_length", f"{what}: falsche Länge.")
    return value


def _dec(token: str, aad: str) -> str:
    if not token:
        return ""
    try:
        return crypto.decrypt_text(token, aad)
    except Exception:  # noqa: BLE001
        return ""


def _publish(user_ids, chat_id: int) -> None:
    ids = {int(i) for i in user_ids if i}
    if not ids:
        return
    try:
        bus.publish("change", {"version": None, "scope": [LIVE_SCOPE], "dates": [], "chat_id": chat_id},
                    user_ids=ids)
    except Exception:  # noqa: BLE001
        log.exception("Chats: Live-Ereignis konnte nicht verteilt werden")


def _member_ids(db: Session, chat_id: int) -> list[int]:
    return list(db.scalars(select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)))


def _membership(db: Session, chat_id: int, user: AuthUser) -> tuple[Chat, ChatMember]:
    chat = db.get(Chat, chat_id)
    mem = db.scalar(select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user.id))
    if chat is None or mem is None:
        raise _fail(404, "not_found", "Chat nicht gefunden.")
    return chat, mem


def _own_device(db: Session, user: AuthUser, device_id: int) -> ChatDevice:
    dev = db.get(ChatDevice, device_id)
    if dev is None or dev.user_id != user.id or dev.revoked_at is not None or dev.kind != "device":
        raise _fail(409, "device_unknown", "Dieses Gerät ist für Chats nicht (mehr) eingerichtet.")
    return dev


POST_MODES = ("all", "admins", "selected")


def _can_post(chat: Chat, mem: ChatMember) -> bool:
    """Darf diese Person schreiben? Einzelchats: immer; Gruppen nach ``post_mode``."""
    if chat.kind == "direct" or mem.admin:
        return True
    if chat.post_mode == "admins" or chat.only_admins_post:
        return False
    return chat.post_mode != "selected" or bool(mem.can_post)


def _require_post(chat: Chat, mem: ChatMember) -> None:
    if not _can_post(chat, mem):
        raise _fail(403, "read_only", "In diesem Chat dürfen Sie nur lesen.")


def _set_post_mode(db: Session, chat: Chat, mode: str) -> None:
    if mode == chat.post_mode:
        return
    chat.post_mode = mode
    chat.only_admins_post = mode == "admins"
    if mode == "selected":
        # Auswahl beginnt leer: Admins schreiben immer, alle anderen werden einzeln freigegeben
        for m in db.scalars(select(ChatMember).where(ChatMember.chat_id == chat.id)):
            m.can_post = False
    _system(db, chat, {"all": "Alle Mitglieder können schreiben.",
                       "admins": "Nur Admins können schreiben.",
                       "selected": "Nur ausgewählte Mitglieder und Admins können schreiben."}[mode])


def _system(db: Session, chat: Chat, text: str) -> None:
    db.add(ChatMessage(chat_id=chat.id, system_text=text[:400], created_at=utcnow()))
    chat.last_activity_at = utcnow()


def _names(db: Session, ids) -> dict[int, str]:
    directory = _directory(db)
    out = {}
    for i in ids:
        acc = directory.get(i)
        out[i] = acc.name if acc else "Gelöschtes Konto"
    return out


# =========================================================================== Geräte
class DeviceIn(BaseModel):
    public_key: str = Field(min_length=40, max_length=64)
    label: str = Field("", max_length=120)


_hits: dict[tuple[str, int], list[float]] = {}


def _rate(kind: str, user_id: int, limit: int, window: float, *, count: bool = True) -> None:
    """Einfaches Ratenlimit je Konto (im Speicher dieses Prozesses; reicht gegen Durchprobieren von Codes)."""
    now = time.monotonic()
    hits = [t for t in _hits.get((kind, user_id), []) if now - t < window]
    if len(hits) >= limit:
        _hits[(kind, user_id)] = hits
        raise HTTPException(429, "Zu viele Versuche – bitte später erneut.", headers={"Retry-After": str(int(window))})
    if count:
        hits.append(now)
    _hits[(kind, user_id)] = hits


def _active_devices(db: Session, user_id: int, kinds: tuple[str, ...] = ("device",)) -> list[ChatDevice]:
    return list(db.scalars(select(ChatDevice).where(ChatDevice.user_id == user_id, ChatDevice.kind.in_(kinds),
                                                    ChatDevice.revoked_at.is_(None)).order_by(ChatDevice.id)))


def _new_device(db: Session, user: AuthUser, public_key: str, label: str, *, kind: str = "device",
                known: bool = False) -> ChatDevice:
    """Legt ein Gerät an; das erste Gerät eines Kontos (oder ``known``) gilt sofort als bekannt, jedes weitere
    wird den anderen Geräten als „neu“ gemeldet, bis jemand es bestätigt."""
    _b64(public_key, 32, "Öffentlicher Schlüssel")
    active = _active_devices(db, user.id)
    if kind == "device":
        for old in sorted(active, key=lambda d: (d.last_seen_at is not None, d.last_seen_at or d.created_at, d.id))[
                :max(0, len(active) - MAX_DEVICES + 1)]:
            _revoke(db, old)
    first = kind == "device" and not active
    dev = ChatDevice(user_id=user.id, public_key=public_key, label=label.strip()[:120], created_at=utcnow(),
                     last_seen_at=utcnow(), kind=kind,
                     acked_at=utcnow() if (known or first or kind != "device") else None)
    db.add(dev)
    db.flush()
    return dev


def _revoke(db: Session, dev: ChatDevice) -> None:
    if dev.revoked_at is None:
        dev.revoked_at = utcnow()
    db.execute(delete(ChatMessageKey).where(ChatMessageKey.device_id == dev.id))
    for req in db.scalars(select(ChatLinkRequest).where(ChatLinkRequest.device_id == dev.id,
                                                        ChatLinkRequest.status != "cancelled")):
        req.status = "cancelled"


@router.post("/chats/devices", status_code=201)
def register_device(body: DeviceIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    dev = _new_device(db, user, body.public_key, body.label)
    db.commit()
    _publish(_contacts(db, user.id) | {user.id}, 0)
    return _device_out(dev)


def _contacts(db: Session, user_id: int) -> set[int]:
    chats = select(ChatMember.chat_id).where(ChatMember.user_id == user_id)
    return set(db.scalars(select(ChatMember.user_id).where(ChatMember.chat_id.in_(chats))))


def _device_out(d: ChatDevice) -> dict:
    return {"id": d.id, "public_key": d.public_key, "label": d.label, "created_at": iso(d.created_at),
            "last_seen_at": iso(d.last_seen_at), "revoked": d.revoked_at is not None, "kind": d.kind,
            "acked": d.acked_at is not None}


@router.get("/chats/devices")
def list_devices(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    return {"devices": [_device_out(d) for d in _active_devices(db, user.id)]}


def _own_active(db: Session, user: AuthUser, device_id: int, *, kinds: tuple[str, ...] = ("device",)) -> ChatDevice:
    dev = db.get(ChatDevice, device_id)
    if dev is None or dev.user_id != user.id or dev.revoked_at is not None or dev.kind not in kinds:
        raise _fail(404, "not_found", "Gerät nicht gefunden.")
    return dev


@router.delete("/chats/devices/{device_id}")
def revoke_device(device_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    dev = db.get(ChatDevice, device_id)
    if dev is None or dev.user_id != user.id:
        raise _fail(404, "not_found", "Gerät nicht gefunden.")
    if dev.kind != "device":
        raise _fail(422, "use_backup", "Das Wiederherstellungs-Backup löschen Sie unter „Wiederherstellung“.")
    _revoke(db, dev)
    db.commit()
    _publish(_contacts(db, user.id) | {user.id}, 0)
    return {"revoked": device_id}


class AckIn(BaseModel):
    by_device_id: int


@router.post("/chats/devices/{device_id}/ack")
def ack_device(device_id: int, body: AckIn, user: AuthUser = Depends(require(USE)),
               db: Session = Depends(get_db)) -> dict:
    """Ein *anderes* eigenes Gerät bestätigt ein neues Gerät als bekannt (das neue Gerät kann sich nicht selbst
    bestätigen)."""
    dev = _own_active(db, user, device_id)
    if body.by_device_id == device_id:
        raise _fail(422, "self_ack", "Ein Gerät kann sich nicht selbst bestätigen.")
    _own_active(db, user, body.by_device_id)
    dev.acked_at = dev.acked_at or utcnow()
    db.commit()
    return _device_out(dev)


class ResetIn(DeviceIn):
    keep_backup: bool = True


@router.post("/chats/devices/reset", status_code=201)
def reset_devices(body: ResetIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Alle Geräteschlüssel des Kontos widerrufen (z. B. nach Verlust eines Geräts) und ein neues Gerät anlegen.
    Gesprächspartner verwenden automatisch den neuen Schlüssel; der Verlauf ist danach nur über eine Verknüpfung
    mit einem noch vorhandenen Gerät oder das Wiederherstellungs-Backup lesbar."""
    for old in _active_devices(db, user.id, ("device",) if body.keep_backup else ("device", "archive")):
        _revoke(db, old)
    if not body.keep_backup:
        db.execute(delete(ChatKeyBackup).where(ChatKeyBackup.user_id == user.id))
    dev = _new_device(db, user, body.public_key, body.label, known=True)
    db.commit()
    _publish(_contacts(db, user.id) | {user.id}, 0)
    return _device_out(dev)


# ---------------------------------------------------------------------------- Verknüpfen (Verlauf übertragen)
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _norm_code(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch in CODE_ALPHABET)


def _link_status(req: ChatLinkRequest) -> str:
    if req.status in ("pending", "approved") and req.expires_at < utcnow():
        return "expired"
    return req.status


def _visible(user_id: int):
    """Nachrichten, die das Konto lesen durfte: Mitglied und nach der Beitrittsgrenze, nicht gelöscht."""
    return and_(ChatMember.user_id == user_id, ChatMessage.id > ChatMember.first_message_id,
                ChatMessage.deleted_at.is_(None))


def _coverage(db: Session, user_id: int, target_id: int) -> dict:
    """Fortschritt: von allen Nachrichten, die irgendein anderes eigenes Gerät lesen kann, wie viele schon das Ziel."""
    own = select(ChatDevice.id).where(ChatDevice.user_id == user_id, ChatDevice.revoked_at.is_(None),
                                      ChatDevice.id != target_id)
    other = aliased(ChatMessageKey)
    mine = aliased(ChatMessageKey)
    base = (select(func.count(func.distinct(ChatMessage.id)))
            .join(ChatMember, ChatMember.chat_id == ChatMessage.chat_id)
            .join(other, other.message_id == ChatMessage.id)
            .where(_visible(user_id), other.device_id.in_(own)))
    total = int(db.scalar(base) or 0)
    left = int(db.scalar(base.where(~exists().where(mine.message_id == ChatMessage.id,
                                                    mine.device_id == target_id))) or 0)
    return {"done": total - left, "total": total}


def _link_out(db: Session, req: ChatLinkRequest, *, with_progress: bool = False) -> dict:
    dev = db.get(ChatDevice, req.device_id)
    out = {"id": req.id, "device_id": req.device_id, "status": _link_status(req), "created_at": iso(req.created_at),
           "expires_at": iso(req.expires_at), "label": dev.label if dev else "",
           "public_key": dev.public_key if dev else ""}
    if with_progress:
        out.update(_coverage(db, req.user_id, req.device_id))
    return out


class LinkIn(BaseModel):
    device_id: int
    # Neuverschlüsselung des eigenen Geräts: das alte Gerät gibt sofort frei (kein Code nötig)
    approve_by_device_id: Optional[int] = None


@router.post("/chat-links", status_code=201)
def create_link(body: LinkIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    target = _own_active(db, user, body.device_id)
    _rate("link", user.id, LINK_PER_HOUR, 3600)
    now = utcnow()
    for old in db.scalars(select(ChatLinkRequest).where(ChatLinkRequest.user_id == user.id)):
        if old.device_id == target.id and old.status != "cancelled":
            old.status = "cancelled"
        elif old.created_at < now - timedelta(days=1):
            db.delete(old)
    code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
    req = ChatLinkRequest(user_id=user.id, device_id=target.id, code=code, status="pending", created_at=now,
                          expires_at=now + LINK_TTL)
    if body.approve_by_device_id is not None:
        if body.approve_by_device_id == target.id:
            raise _fail(422, "self", "Ein Gerät kann sich nicht selbst freigeben.")
        _own_active(db, user, body.approve_by_device_id)
        req.status, req.approved_by_device_id, req.approved_at = "approved", body.approve_by_device_id, now
        req.expires_at = now + LINK_APPROVED_TTL
    db.add(req)
    db.commit()
    return {**_link_out(db, req), "code": code}


class LookupIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)


@router.post("/chat-links/lookup")
def lookup_link(body: LookupIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Findet die offene Anfrage zu einem Code (nur im eigenen Konto). Falsche Codes zählen gegen das Ratenlimit."""
    _rate("lookup", user.id, LOOKUP_FAILS, 600, count=False)
    code = _norm_code(body.code)
    req = db.scalar(select(ChatLinkRequest).where(ChatLinkRequest.user_id == user.id, ChatLinkRequest.code == code,
                                                  ChatLinkRequest.status.in_(("pending", "approved")))
                  ) if len(code) == 8 else None
    dev = db.get(ChatDevice, req.device_id) if req else None
    if req is None or _link_status(req) not in ("pending", "approved") or dev is None or dev.revoked_at is not None:
        _rate("lookup", user.id, LOOKUP_FAILS, 600)
        raise _fail(404, "not_found", "Zu diesem Code gibt es keine offene Anfrage (abgelaufen oder vertippt?).")
    return _link_out(db, req)


def _own_request(db: Session, user: AuthUser, link_id: int) -> ChatLinkRequest:
    req = db.get(ChatLinkRequest, link_id)
    if req is None or req.user_id != user.id:
        raise _fail(404, "not_found", "Anfrage nicht gefunden.")
    return req


@router.get("/chat-links/{link_id}")
def get_link(link_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    return _link_out(db, _own_request(db, user, link_id), with_progress=True)


class ApproveIn(BaseModel):
    by_device_id: int


@router.post("/chat-links/{link_id}/approve")
def approve_link(link_id: int, body: ApproveIn, user: AuthUser = Depends(require(USE)),
                 db: Session = Depends(get_db)) -> dict:
    req = _own_request(db, user, link_id)
    if _link_status(req) not in ("pending", "approved"):      # erneut freigeben = Übertragung fortsetzen
        raise _fail(409, "not_pending", "Die Anfrage ist abgelaufen oder bereits bearbeitet.")
    target = _own_active(db, user, req.device_id)
    if body.by_device_id == target.id:
        raise _fail(422, "self", "Die Freigabe muss von einem bereits eingerichteten Gerät kommen.")
    _own_active(db, user, body.by_device_id)
    req.status, req.approved_by_device_id, req.approved_at = "approved", body.by_device_id, utcnow()
    req.expires_at = utcnow() + LINK_APPROVED_TTL
    target.acked_at = target.acked_at or utcnow()
    db.commit()
    return _link_out(db, req, with_progress=True)


@router.delete("/chat-links/{link_id}")
def cancel_link(link_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    req = _own_request(db, user, link_id)
    req.status = "cancelled"
    db.commit()
    return {"cancelled": link_id}


# ---------------------------------------------------------------------------- Schlüssel nachträglich verpacken
def _own_target(db: Session, user: AuthUser, target_id: int, source_id: int) -> ChatDevice:
    """Zielgerät: das Archiv, das Quellgerät selbst oder ein eigenes Gerät mit freigegebener Verknüpfung."""
    target = _own_active(db, user, target_id, kinds=("device", "archive"))
    if target.kind == "archive" or target_id == source_id:
        return target
    req = db.scalar(select(ChatLinkRequest).where(ChatLinkRequest.user_id == user.id,
                                                  ChatLinkRequest.device_id == target_id,
                                                  ChatLinkRequest.status == "approved")
                    .order_by(ChatLinkRequest.id.desc()))
    if req is None or _link_status(req) != "approved":
        raise _fail(403, "not_approved", "Dieses Gerät wurde nicht (oder nicht mehr) für die Übertragung freigegeben.")
    return target


@router.get("/chat-keys/pending")
def pending_keys(source_device_id: int = Query(..., ge=1), target_device_id: int = Query(..., ge=1),
                 after: int = Query(0, ge=0), limit: int = Query(TRANSFER_BATCH, ge=1, le=TRANSFER_BATCH),
                 user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Nachrichten, deren Schlüssel das Quellgerät besitzt, das Zielgerät aber noch nicht – in Paketen nach
    Nachrichten-ID (``after`` = letzte verarbeitete ID). Das Quellgerät verpackt die Schlüssel neu für das Ziel.
    Quelle kann auch das Archiv sein (Wiederherstellung): dann ist das Ziel das eigene, neue Gerät."""
    src = _own_active(db, user, source_device_id, kinds=("device", "archive"))
    _own_target(db, user, target_device_id, source_device_id if src.kind == "device" else target_device_id)
    tk = aliased(ChatMessageKey)
    rows = list(db.execute(
        select(ChatMessage, ChatMessageKey).join(ChatMessageKey, and_(ChatMessageKey.message_id == ChatMessage.id,
                                                                     ChatMessageKey.device_id == source_device_id))
        .join(ChatMember, ChatMember.chat_id == ChatMessage.chat_id)
        .where(_visible(user.id), ChatMessage.id > after,
               ~exists().where(tk.message_id == ChatMessage.id, tk.device_id == target_device_id))
        .order_by(ChatMessage.id).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    dev_ids = {m.sender_device_id for m, _k in rows if m.sender_device_id} | \
              {k.wrapper_device_id for _m, k in rows if k.wrapper_device_id}
    pubs = {d.id: d.public_key for d in db.scalars(select(ChatDevice).where(ChatDevice.id.in_(dev_ids)))} \
        if dev_ids else {}
    items = [{"message_id": m.id, "wrapper_key": pubs.get(k.wrapper_device_id or m.sender_device_id or -1, ""),
              "nonce": k.nonce, "wrapped": k.wrapped} for m, k in rows]
    return {"items": items, "more": more, "last_id": rows[-1][0].id if rows else after}


class WrappedIn(BaseModel):
    message_id: int
    nonce: str = Field(min_length=32, max_length=40)
    wrapped: str = Field(min_length=40, max_length=120)


class WrappedBatch(BaseModel):
    target_device_id: int
    wrapper_device_id: int
    keys: list[WrappedIn] = Field(max_length=TRANSFER_BATCH)


@router.post("/chat-keys")
def add_keys(body: WrappedBatch, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Ergänzt für ein eigenes Zielgerät neu verpackte Nachrichtenschlüssel. Der Server prüft Besitz der Geräte,
    Freigabe und dass die Person die Nachricht lesen durfte (Mitgliedschaft, Beitrittsgrenze) – Inhalte sieht er nie."""
    _own_active(db, user, body.wrapper_device_id)
    _own_target(db, user, body.target_device_id, body.wrapper_device_id)
    ids = {k.message_id for k in body.keys}
    allowed = set(db.scalars(select(ChatMessage.id).join(ChatMember, ChatMember.chat_id == ChatMessage.chat_id)
                             .where(_visible(user.id), ChatMessage.id.in_(ids)))) if ids else set()
    have = set(db.scalars(select(ChatMessageKey.message_id).where(
        ChatMessageKey.device_id == body.target_device_id, ChatMessageKey.message_id.in_(ids)))) if ids else set()
    added = skipped = 0
    for k in body.keys:
        if k.message_id not in allowed or k.message_id in have:
            skipped += 1
            continue
        _b64(k.nonce, 24, "Nonce")
        _b64(k.wrapped, None, "Schlüssel")
        db.add(ChatMessageKey(message_id=k.message_id, device_id=body.target_device_id, nonce=k.nonce,
                              wrapped=k.wrapped, wrapper_device_id=body.wrapper_device_id))
        have.add(k.message_id)
        added += 1
    db.commit()
    if added:
        _publish([user.id], 0)                      # andere eigene Geräte laden den Verlauf neu
    return {"added": added, "skipped": skipped}


# ---------------------------------------------------------------------------- Wiederherstellung mit Passwort
def _backup_out(db: Session, user_id: int, *, blob: bool) -> dict:
    row = db.get(ChatKeyBackup, user_id)
    dev = db.get(ChatDevice, row.archive_device_id) if row else None
    if row is None or dev is None or dev.revoked_at is not None:
        return {"enabled": False}
    out = {"enabled": True, "archive_device_id": dev.id, "public_key": dev.public_key,
           "created_at": iso(row.created_at), "updated_at": iso(row.updated_at)}
    if blob:
        out["blob"] = row.blob
    return out


class BackupIn(BaseModel):
    public_key: str = Field(min_length=40, max_length=64)
    blob: str = Field(min_length=20, max_length=MAX_BACKUP_BLOB)


@router.get("/chat-keys/backup")
def get_backup(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    _rate("backup-get", user.id, 30, 600)
    return _backup_out(db, user.id, blob=True)


@router.put("/chat-keys/backup")
def put_backup(body: BackupIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    """Backup einrichten bzw. (Passwort ändern) das verschlüsselte Blob ersetzen. Der Archiv-Schlüssel bleibt gleich."""
    _b64(body.public_key, 32, "Öffentlicher Schlüssel")
    row = db.get(ChatKeyBackup, user.id)
    dev = db.get(ChatDevice, row.archive_device_id) if row else None
    if row is not None and dev is not None and dev.revoked_at is None:
        if dev.public_key != body.public_key:
            raise _fail(409, "backup_exists", "Es gibt bereits ein Backup – zuerst löschen.")
        row.blob, row.updated_at = body.blob, utcnow()
    else:
        dev = _new_device(db, user, body.public_key, "Wiederherstellungsschlüssel", kind="archive")
        if row is None:
            db.add(ChatKeyBackup(user_id=user.id, archive_device_id=dev.id, blob=body.blob, created_at=utcnow(),
                                 updated_at=utcnow()))
        else:
            row.archive_device_id, row.blob, row.created_at, row.updated_at = dev.id, body.blob, utcnow(), utcnow()
    db.commit()
    _publish(_contacts(db, user.id) | {user.id}, 0)
    return _backup_out(db, user.id, blob=False)


@router.delete("/chat-keys/backup")
def delete_backup(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    row = db.get(ChatKeyBackup, user.id)
    if row is not None:
        dev = db.get(ChatDevice, row.archive_device_id)
        if dev is not None:
            _revoke(db, dev)
        db.delete(row)
    db.commit()
    _publish(_contacts(db, user.id) | {user.id}, 0)
    return {"enabled": False}


# =========================================================================== Mitglieder auflösen
class ClassPick(BaseModel):
    class_id: str = Field(max_length=40)
    students: bool = True
    teachers: bool = False
    parents: bool = False


def _class_members(idx: mx.SchoolIndex, directory: mx.Directory, user: AuthUser, pick: ClassPick) -> set[int]:
    if pick.class_id not in idx.classes:
        raise _fail(404, "not_found", "Klasse nicht gefunden.")
    label = idx.class_name(pick.class_id)
    if mx.is_staff(user):
        scope = user.scope("students.read") if has(user, "students.read") else "own_classes"
        if scope == "own_classes" and pick.class_id not in idx.teacher_classes.get(user.teacher_id or "", set()):
            raise _fail(403, "foreign_class", f"Die Klasse {label} gehört nicht zu Ihren Klassen.")
    elif user.role == "schueler":
        if idx.student_class(user.student_id) != pick.class_id or pick.teachers or pick.parents or not pick.students:
            raise _fail(403, "forbidden", "Schüler/innen können einen Chat mit der eigenen Klasse anlegen "
                                          "(ohne Lehrkräfte und Eltern – Lehrkräfte einzeln hinzufügen).")
    elif user.role == "eltern":
        own = {idx.student_class(s) for s in (user.student_ids or [])}
        if pick.class_id not in own or pick.students or pick.teachers or not pick.parents:
            raise _fail(403, "forbidden", "Eltern können einen Elternchat der Klasse ihres Kindes anlegen.")
    else:
        raise _fail(403, "forbidden", "Keine Berechtigung.")
    sids = idx.students_by_class.get(pick.class_id, [])
    out: set[int] = set()
    if pick.students:
        out |= directory.students(sids)
    if pick.parents:
        out |= directory.parents(sids)
    if pick.teachers:
        out |= directory.teachers(idx.class_teachers.get(pick.class_id, set()))
    return out


def _resolve(db: Session, user: AuthUser, user_ids: list[int], classes: list[ClassPick]) -> set[int]:
    snap = snapshot()
    idx = _index(snap)
    s2s, _days = _policy(snap)
    directory = _directory(db)
    blocked_me = _blocked_by(db, user.id)
    out: set[int] = set()
    for uid in user_ids:
        if uid == user.id:
            continue
        acc = directory.get(uid)
        try:
            mx.check_direct(user, acc, students_to_students=s2s, blocked=acc is not None and acc.id in blocked_me)
        except mx.MessagingError as exc:
            raise _mx_error(exc) from None
        out.add(acc.id)
    for pick in classes:
        out |= {i for i in _class_members(idx, directory, user, pick) if directory.get(i) and directory.get(i).reachable}
    out.discard(user.id)
    if not s2s:
        everyone = [directory.get(i) for i in out | {user.id}]
        students = [a for a in everyone if a and a.role == "schueler"]
        staff = [a for a in everyone if a and mx.is_staff(a)]
        if len(students) >= 2 and not staff:
            raise _fail(403, "students_to_students", "Chats nur unter Schülerinnen und Schülern sind an dieser "
                                                      "Schule abgeschaltet – bitte eine Lehrkraft hinzufügen.")
    return out


# =========================================================================== Chats
class ChatIn(BaseModel):
    kind: Literal["direct", "group"] = "group"
    title: str = Field("", max_length=80)
    user_ids: list[int] = Field(default_factory=list, max_length=MAX_MEMBERS)
    classes: list[ClassPick] = Field(default_factory=list, max_length=10)
    only_admins_post: bool = False
    post_mode: Optional[Literal["all", "admins", "selected"]] = None


def _last_message_id(db: Session, chat_id: int) -> int:
    return int(db.scalar(select(func.max(ChatMessage.id)).where(ChatMessage.chat_id == chat_id)) or 0)


@router.post("/chats", status_code=201)
def create_chat(body: ChatIn, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    _ensure_can_send(db, user)
    if body.kind == "direct":
        if len(body.user_ids) != 1 or body.classes:
            raise _fail(422, "invalid", "Ein Einzelchat braucht genau eine Person.")
        other = _resolve(db, user, body.user_ids, [])
        if not other:
            raise _fail(422, "self", "Sie können keinen Chat mit sich selbst beginnen.")
        oid = next(iter(other))
        key = f"{min(user.id, oid)}:{max(user.id, oid)}"
        chat = db.scalar(select(Chat).where(Chat.direct_key == key))
        if chat is None:
            chat = Chat(kind="direct", title_enc="", direct_key=key, created_by=user.id, created_at=utcnow(),
                        last_activity_at=utcnow())
            db.add(chat)
            db.flush()
        present = set(_member_ids(db, chat.id))
        first = _last_message_id(db, chat.id)
        for uid in (user.id, oid):
            if uid not in present:
                db.add(ChatMember(chat_id=chat.id, user_id=uid, admin=True, joined_at=utcnow(),
                                  first_message_id=first if present else 0))
        db.commit()
        _publish({user.id, oid}, chat.id)
        return chat_detail(chat.id, user, db)
    members = _resolve(db, user, body.user_ids, body.classes)
    if not members:
        raise _fail(422, "empty", "Bitte mindestens eine weitere Person oder Klasse auswählen.")
    if len(members) + 1 > MAX_MEMBERS:
        raise _fail(422, "too_many", f"Höchstens {MAX_MEMBERS} Mitglieder je Chat.")
    title = " ".join(body.title.split())
    if not title:
        snap = snapshot()
        idx = _index(snap)
        if body.classes:
            c = body.classes[0]
            title = f"Klasse {idx.class_name(c.class_id)}" + (" – Eltern" if c.parents and not c.students else "") + \
                    (" mit Lehrkräften" if c.teachers else "")
        else:
            names = _names(db, sorted(members)[:3])
            title = ", ".join(names.values()) + (" …" if len(members) > 3 else "")
    mode = body.post_mode or ("admins" if body.only_admins_post else "all")
    chat = Chat(kind="group", title_enc="", created_by=user.id, created_at=utcnow(), last_activity_at=utcnow(),
                only_admins_post=mode == "admins", post_mode=mode)
    db.add(chat)
    db.flush()
    chat.title_enc = crypto.encrypt_text(title[:80], chat.title_aad)
    db.add(ChatMember(chat_id=chat.id, user_id=user.id, admin=True, joined_at=utcnow()))
    for uid in sorted(members):
        db.add(ChatMember(chat_id=chat.id, user_id=uid, admin=False, joined_at=utcnow(), can_post=mode != "selected"))
    _system(db, chat, f"{user.display_name or user.username} hat den Chat erstellt.")
    db.commit()
    _publish(members | {user.id}, chat.id)
    return chat_detail(chat.id, user, db)


def _unread(db: Session, chat_id: int, mem: ChatMember, user_id: int) -> int:
    return int(db.scalar(select(func.count(ChatMessage.id)).where(
        ChatMessage.chat_id == chat_id, ChatMessage.id > max(mem.last_read_id, mem.first_message_id),
        ChatMessage.sender_id.is_not(None), ChatMessage.sender_id != user_id,
        ChatMessage.deleted_at.is_(None))) or 0)


def _title(db: Session, chat: Chat, user_id: int, names: dict[int, str]) -> str:
    if chat.kind == "direct":
        other = [u for u in names if u != user_id]
        return names.get(other[0], "Unbekannt") if other else "Nur noch Sie"
    return _dec(chat.title_enc, chat.title_aad) or "Gruppe"


@router.get("/chats")
def list_chats(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    mems = {m.chat_id: m for m in db.scalars(select(ChatMember).where(ChatMember.user_id == user.id))}
    if not mems:
        return {"chats": []}
    chats = list(db.scalars(select(Chat).where(Chat.id.in_(mems)).order_by(Chat.last_activity_at.desc())))
    member_rows = list(db.execute(select(ChatMember.chat_id, ChatMember.user_id).where(ChatMember.chat_id.in_(mems))))
    by_chat: dict[int, list[int]] = {}
    for cid, uid in member_rows:
        by_chat.setdefault(cid, []).append(uid)
    directory = _directory(db)
    out = []
    for chat in chats:
        ids = by_chat.get(chat.id, [])
        names = {i: (directory.get(i).name if directory.get(i) else "Gelöschtes Konto") for i in ids}
        last = db.scalar(select(ChatMessage).where(ChatMessage.chat_id == chat.id,
                                                   ChatMessage.id > mems[chat.id].first_message_id)
                         .order_by(ChatMessage.id.desc()).limit(1))
        out.append({"id": chat.id, "kind": chat.kind, "title": _title(db, chat, user.id, names),
                    "members": len(ids), "last_activity_at": iso(chat.last_activity_at),
                    "last": None if last is None else {
                        "id": last.id, "sender_name": names.get(last.sender_id or -1, "") if last.sender_id else "",
                        "mine": last.sender_id == user.id, "system_text": last.system_text,
                        "deleted": last.deleted_at is not None, "created_at": iso(last.created_at)},
                    "unread": _unread(db, chat.id, mems[chat.id], user.id), "muted": mems[chat.id].muted,
                    "archived": mems[chat.id].archived, "can_post": _can_post(chat, mems[chat.id])})
    return {"chats": out}


@router.get("/chats/unread")
def unread(user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    n = 0
    for m in db.scalars(select(ChatMember).where(ChatMember.user_id == user.id, ChatMember.muted.is_(False),
                                                 ChatMember.archived.is_(False))):
        if _unread(db, m.chat_id, m, user.id):
            n += 1
    return {"unread": n}


@router.get("/chats/class-options")
def class_options(user: AuthUser = Depends(require(USE))) -> dict:
    """Klassen, mit denen das Konto einen Klassenchat anlegen darf, und welche Varianten erlaubt sind."""
    idx = _index(snapshot())
    out = []
    if mx.is_staff(user):
        scope = user.scope("students.read") if has(user, "students.read") else "own_classes"
        ids = idx.teacher_classes.get(user.teacher_id or "", set()) if scope == "own_classes" else set(idx.classes)
        for cid in sorted(ids, key=lambda c: mx.natural_key(idx.class_name(c))):
            out.append({"class_id": cid, "name": idx.class_name(cid), "students": True, "teachers": True,
                        "parents": True})
    elif user.role == "schueler":
        cid = idx.student_class(user.student_id)
        if cid:
            out.append({"class_id": cid, "name": idx.class_name(cid), "students": True, "teachers": False,
                        "parents": False})
    elif user.role == "eltern":
        for cid in sorted({idx.student_class(s) for s in (user.student_ids or [])} - {None}):
            out.append({"class_id": cid, "name": idx.class_name(cid), "students": False, "teachers": False,
                        "parents": True})
    return {"classes": out}


@router.get("/chats/{chat_id}")
def chat_detail(chat_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    chat, mem = _membership(db, chat_id, user)
    snap = snapshot()
    idx = _index(snap)
    directory = _directory(db)
    rows = list(db.scalars(select(ChatMember).where(ChatMember.chat_id == chat_id).order_by(ChatMember.id)))
    names = {r.user_id: (directory.get(r.user_id).name if directory.get(r.user_id) else "Gelöschtes Konto")
             for r in rows}
    members = []
    for r in rows:
        p = _person(directory.get(r.user_id), idx, user)
        p["admin"] = r.admin
        p["can_post"] = _can_post(chat, r)
        members.append(p)
    imported = bool(db.scalar(select(func.count(ChatMessage.id)).where(
        ChatMessage.chat_id == chat_id, ChatMessage.legacy_source_message_id.is_not(None),
        ChatMessage.id > mem.first_message_id)))
    return {"id": chat.id, "kind": chat.kind, "title": _title(db, chat, user.id, names),
            "only_admins_post": chat.post_mode == "admins" or chat.only_admins_post, "post_mode": chat.post_mode,
            "admin": mem.admin, "muted": mem.muted, "archived": mem.archived,
            "can_post": _can_post(chat, mem), "has_imported": imported, "members": members,
            "created_at": iso(chat.created_at)}


class ChatPatch(BaseModel):
    title: Optional[str] = Field(None, max_length=80)
    only_admins_post: Optional[bool] = None
    post_mode: Optional[Literal["all", "admins", "selected"]] = None
    muted: Optional[bool] = None
    archived: Optional[bool] = None


@router.patch("/chats/{chat_id}")
def patch_chat(chat_id: int, body: ChatPatch, user: AuthUser = Depends(require(USE)),
               db: Session = Depends(get_db)) -> dict:
    chat, mem = _membership(db, chat_id, user)
    if body.muted is not None:
        mem.muted = body.muted
    if body.archived is not None:
        mem.archived = body.archived
    mode = body.post_mode or (None if body.only_admins_post is None else ("admins" if body.only_admins_post else "all"))
    if body.title is not None or mode is not None:
        if chat.kind != "group" or not mem.admin:
            raise _fail(403, "forbidden", "Nur Admins der Gruppe können das ändern.")
        if body.title is not None and " ".join(body.title.split()):
            chat.title_enc = crypto.encrypt_text(" ".join(body.title.split())[:80], chat.title_aad)
            _system(db, chat, f"{user.display_name or user.username} hat den Namen geändert.")
        if mode is not None:
            _set_post_mode(db, chat, mode)
    db.commit()
    _publish(_member_ids(db, chat_id) if (body.title is not None or mode is not None) else [user.id], chat_id)
    return chat_detail(chat_id, user, db)


# =========================================================================== Mitglieder
class MembersIn(BaseModel):
    user_ids: list[int] = Field(default_factory=list, max_length=MAX_MEMBERS)
    classes: list[ClassPick] = Field(default_factory=list, max_length=10)


@router.post("/chats/{chat_id}/members")
def add_members(chat_id: int, body: MembersIn, user: AuthUser = Depends(require(USE)),
                db: Session = Depends(get_db)) -> dict:
    chat, mem = _membership(db, chat_id, user)
    if chat.kind != "group" or not mem.admin:
        raise _fail(403, "forbidden", "Nur Admins der Gruppe können Mitglieder hinzufügen.")
    present = set(_member_ids(db, chat_id))
    new = _resolve(db, user, body.user_ids, body.classes) - present
    if len(present) + len(new) > MAX_MEMBERS:
        raise _fail(422, "too_many", f"Höchstens {MAX_MEMBERS} Mitglieder je Chat.")
    first = _last_message_id(db, chat_id)
    for uid in sorted(new):
        db.add(ChatMember(chat_id=chat_id, user_id=uid, admin=False, joined_at=utcnow(), first_message_id=first,
                          can_post=chat.post_mode != "selected"))
    if new:
        names = _names(db, sorted(new)[:5])
        more = f" und {len(new) - 5} weitere" if len(new) > 5 else ""
        _system(db, chat, f"{user.display_name or user.username} hat {', '.join(names.values())}{more} hinzugefügt.")
    db.commit()
    _publish(present | new, chat_id)
    return chat_detail(chat_id, user, db)


@router.delete("/chats/{chat_id}/members/{member_id}")
def remove_member(chat_id: int, member_id: int, user: AuthUser = Depends(require(USE)),
                  db: Session = Depends(get_db)) -> dict:
    chat, mem = _membership(db, chat_id, user)
    if member_id != user.id and (chat.kind != "group" or not mem.admin):
        raise _fail(403, "forbidden", "Nur Admins können andere entfernen.")
    target = db.scalar(select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == member_id))
    if target is None:
        raise _fail(404, "not_found", "Mitglied nicht gefunden.")
    before = set(_member_ids(db, chat_id))
    db.delete(target)
    db.flush()
    rest = list(db.scalars(select(ChatMember).where(ChatMember.chat_id == chat_id).order_by(ChatMember.id)))
    name = _names(db, [member_id])[member_id]
    if not rest:
        ids = list(db.scalars(select(ChatMessage.id).where(ChatMessage.chat_id == chat_id)))
        if ids:
            db.execute(delete(ChatMessageKey).where(ChatMessageKey.message_id.in_(ids)))
        db.execute(delete(ChatAttachment).where(ChatAttachment.chat_id == chat_id))
        delete_chat_polls(db, chat_id)
        db.execute(delete(ChatMessage).where(ChatMessage.chat_id == chat_id))
        db.delete(chat)
    else:
        if chat.kind == "group" and not any(r.admin for r in rest):
            rest[0].admin = True
        _system(db, chat, f"{name} hat den Chat verlassen." if member_id == user.id else
                f"{user.display_name or user.username} hat {name} entfernt.")
    db.commit()
    _publish(before, chat_id)
    return {"removed": member_id, "chat_deleted": not rest}


class AdminIn(BaseModel):
    admin: Optional[bool] = None
    can_post: Optional[bool] = None


@router.patch("/chats/{chat_id}/members/{member_id}")
def set_admin(chat_id: int, member_id: int, body: AdminIn, user: AuthUser = Depends(require(USE)),
              db: Session = Depends(get_db)) -> dict:
    chat, mem = _membership(db, chat_id, user)
    if chat.kind != "group" or not mem.admin:
        raise _fail(403, "forbidden", "Nur Admins können Admins und Schreibrechte festlegen.")
    target = db.scalar(select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == member_id))
    if target is None:
        raise _fail(404, "not_found", "Mitglied nicht gefunden.")
    if body.admin is False and member_id == user.id and not db.scalar(select(func.count(ChatMember.id)).where(
            ChatMember.chat_id == chat_id, ChatMember.admin.is_(True), ChatMember.user_id != user.id)):
        raise _fail(422, "last_admin", "Die Gruppe braucht mindestens einen Admin.")
    if body.admin is not None:
        target.admin = body.admin
    if body.can_post is not None:
        target.can_post = body.can_post
    db.commit()
    _publish(_member_ids(db, chat_id), chat_id)
    return chat_detail(chat_id, user, db)


# =========================================================================== Schlüssel & Nachrichten
def _member_devices(db: Session, chat_id: int) -> list[ChatDevice]:
    members = select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
    return list(db.scalars(select(ChatDevice).where(ChatDevice.user_id.in_(members), ChatDevice.revoked_at.is_(None))
                           .order_by(ChatDevice.id)))


def _devices_out(devs: list[ChatDevice]) -> list[dict]:
    return [{"device_id": d.id, "user_id": d.user_id, "public_key": d.public_key, "kind": d.kind} for d in devs]


@router.get("/chats/{chat_id}/devices")
def chat_devices(chat_id: int, user: AuthUser = Depends(require(USE)), db: Session = Depends(get_db)) -> dict:
    _membership(db, chat_id, user)
    return {"devices": _devices_out(_member_devices(db, chat_id))}


def _message_out(m: ChatMessage, key: Optional[ChatMessageKey], sender_keys: dict[int, str], names: dict[int, str],
                 user_id: int, reported: bool = False, wrapper_keys: Optional[dict[int, str]] = None) -> dict:
    deleted = m.deleted_at is not None
    imported = m.legacy_source_message_id is not None
    return {"imported": imported, "legacy_text": _dec(m.legacy_body_enc, m.legacy_aad) if imported and not deleted else "",
            "id": m.id, "sender_id": m.sender_id, "sender_name": names.get(m.sender_id or -1, ""),
            "mine": m.sender_id == user_id, "system_text": m.system_text, "created_at": iso(m.created_at),
            "reply_to": m.reply_to, "deleted": deleted, "reported": reported and not deleted,
            "nonce": "" if deleted else m.nonce, "ciphertext": "" if deleted else m.ciphertext,
            "sender_key": sender_keys.get(m.sender_device_id or -1, ""),
            "key": None if (deleted or key is None) else {
                "nonce": key.nonce, "wrapped": key.wrapped,
                # nachträglich neu verpackt (Verknüpfung/Wiederherstellung): öffentlicher Schlüssel des Verpackers
                "wrapper_key": (wrapper_keys or {}).get(key.wrapper_device_id or -1, "")}}


def _load_messages(db: Session, msgs: list[ChatMessage], device_id: int, user_id: int) -> list[dict]:
    ids = [m.id for m in msgs]
    keys = {k.message_id: k for k in db.scalars(select(ChatMessageKey).where(
        ChatMessageKey.message_id.in_(ids), ChatMessageKey.device_id == device_id))} if ids else {}
    dev_ids = {m.sender_device_id for m in msgs if m.sender_device_id}
    sender_keys = {d.id: d.public_key for d in db.scalars(select(ChatDevice).where(ChatDevice.id.in_(dev_ids)))} \
        if dev_ids else {}
    wrap_ids = {k.wrapper_device_id for k in keys.values() if k.wrapper_device_id}
    wrapper_keys = {d.id: d.public_key for d in db.scalars(select(ChatDevice).where(ChatDevice.id.in_(wrap_ids)))}         if wrap_ids else {}
    names = _names(db, {m.sender_id for m in msgs if m.sender_id})
    reported = set(db.scalars(select(ChatReport.message_id).where(
        ChatReport.reporter_id == user_id, ChatReport.message_id.in_(ids)))) if ids else set()
    out = [_message_out(m, keys.get(m.id), sender_keys, names, user_id, m.id in reported, wrapper_keys)
           for m in msgs]
    # Umfragen (Einstellungen + Stimmen; Frage und Antworten stehen verschlüsselt in der Nachricht)
    polls = chat_poll_states(db, [m.id for m in msgs if m.deleted_at is None], user_id, lambda ids: _names(db, ids))
    for item in out:
        if item["id"] in polls:
            item["poll"] = polls[item["id"]]
    return out


@router.get("/chats/{chat_id}/messages")
def list_messages(chat_id: int, device_id: int = Query(..., ge=1), before: Optional[int] = Query(None, ge=1),
                  limit: int = Query(PAGE, ge=1, le=200), user: AuthUser = Depends(require(USE)),
                  db: Session = Depends(get_db)) -> dict:
    _chat, mem = _membership(db, chat_id, user)
    dev = _own_device(db, user, device_id)
    dev.last_seen_at = utcnow()
    q = select(ChatMessage).where(ChatMessage.chat_id == chat_id, ChatMessage.id > mem.first_message_id)
    if before:
        q = q.where(ChatMessage.id < before)
    msgs = list(db.scalars(q.order_by(ChatMessage.id.desc()).limit(limit + 1)))
    more = len(msgs) > limit
    msgs = list(reversed(msgs[:limit]))
    out = _load_messages(db, msgs, device_id, user.id)
    db.commit()
    return {"messages": out, "more": more, "last_read_id": mem.last_read_id}


class KeyIn(BaseModel):
    device_id: int
    nonce: str = Field(min_length=32, max_length=40)
    wrapped: str = Field(min_length=40, max_length=120)


class MessageIn(BaseModel):
    device_id: int
    nonce: str = Field(min_length=32, max_length=40)
    ciphertext: str = Field(min_length=24, max_length=MAX_CIPHERTEXT)
    keys: list[KeyIn] = Field(max_length=4000)
    reply_to: Optional[int] = None
    attachment_ids: list[str] = Field(default_factory=list, max_length=MAX_IMAGES)
    # Umfrage: Einstellungen im Klartext, Frage und Antworten nur im verschlüsselten Inhalt
    poll: Optional[ChatPollMeta] = None


@router.post("/chats/{chat_id}/messages", status_code=201)
def send_message(chat_id: int, body: MessageIn, user: AuthUser = Depends(require(USE)),
                 db: Session = Depends(get_db)) -> dict:
    chat, mem = _membership(db, chat_id, user)
    _ensure_can_send(db, user)
    _own_device(db, user, body.device_id)
    _require_post(chat, mem)
    members = _member_ids(db, chat_id)
    if chat.kind == "direct":
        others = [u for u in members if u != user.id]
        if not others:
            raise _fail(422, "alone", "Die andere Person hat den Chat verlassen.")
        if others[0] in _blocked_by(db, user.id):
            raise _fail(403, "blocked", "Diese Person nimmt keine Nachrichten von Ihnen an.")
    _b64(body.nonce, 24, "Nonce")
    _b64(body.ciphertext, None, "Nachricht")
    devices = _member_devices(db, chat_id)
    wanted = {d.id for d in devices}
    given = {k.device_id: k for k in body.keys if k.device_id in wanted}
    if wanted - set(given):
        raise HTTPException(409, {"code": "devices_changed", "message": "Die Geräte der Mitglieder haben sich "
                                  "geändert – bitte erneut senden.", "devices": _devices_out(devices)})
    if body.reply_to is not None:
        ref = db.get(ChatMessage, body.reply_to)
        if ref is None or ref.chat_id != chat_id:
            raise _fail(422, "invalid_reply", "Die beantwortete Nachricht gibt es nicht.")
    blobs = _pending_blobs(db, user, chat_id, body.attachment_ids)
    msg = ChatMessage(chat_id=chat_id, sender_id=user.id, sender_device_id=body.device_id, nonce=body.nonce,
                      ciphertext=body.ciphertext, reply_to=body.reply_to, created_at=utcnow())
    db.add(msg)
    db.flush()
    for blob in blobs:
        blob.message_id = msg.id
    if body.poll is not None:
        try:
            chat_poll_row(db, chat_id, msg.id, body.poll, user.id)
        except lx.LearningError as exc:
            raise _fail(422, "invalid_poll", str(exc)) from None
    for k in given.values():
        _b64(k.nonce, 24, "Nonce")
        _b64(k.wrapped, None, "Schlüssel")
        db.add(ChatMessageKey(message_id=msg.id, device_id=k.device_id, nonce=k.nonce, wrapped=k.wrapped))
    chat.last_activity_at = utcnow()
    mem.last_read_id = msg.id
    # Archivierte Chats kommen bei einer neuen Nachricht zurück in die Liste (stummgeschaltete bleiben archiviert)
    db.execute(update(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id != user.id,
                                        ChatMember.archived.is_(True), ChatMember.muted.is_(False))
               .values(archived=False))
    db.commit()
    _publish(members, chat_id)
    return _load_messages(db, [msg], body.device_id, user.id)[0]


@router.delete("/chats/{chat_id}/messages/{message_id}")
def delete_message(chat_id: int, message_id: int, user: AuthUser = Depends(require(USE)),
                   db: Session = Depends(get_db)) -> dict:
    _membership(db, chat_id, user)
    msg = db.get(ChatMessage, message_id)
    if msg is None or msg.chat_id != chat_id or msg.sender_id != user.id:
        raise _fail(404, "not_found", "Nachricht nicht gefunden.")
    _wipe(db, msg)
    db.commit()
    _publish(_member_ids(db, chat_id), chat_id)
    return {"deleted": message_id}


def _wipe(db: Session, msg: ChatMessage) -> None:
    msg.deleted_at = utcnow()
    msg.ciphertext = ""
    msg.nonce = ""
    msg.legacy_body_enc = ""
    db.execute(delete(ChatMessageKey).where(ChatMessageKey.message_id == msg.id))
    db.execute(delete(ChatAttachment).where(ChatAttachment.message_id == msg.id))
    delete_chat_poll(db, msg.id)


# =========================================================================== Bilder & GIFs (nur verschlüsselte Blobs)
def _pending_blobs(db: Session, user: AuthUser, chat_id: int, ids: list[str]) -> list[ChatAttachment]:
    """Die beim Senden genannten Uploads: müssen der Person gehören, zu diesem Chat passen und noch frei sein."""
    unique = list(dict.fromkeys(ids))
    if not unique:
        return []
    rows = {a.id: a for a in db.scalars(select(ChatAttachment).where(ChatAttachment.id.in_(unique)))}
    out = []
    for aid in unique:
        a = rows.get(aid)
        if a is None or a.uploader_id != user.id or a.chat_id != chat_id or a.message_id is not None:
            raise _fail(422, "invalid_attachment", "Ein Bild wurde nicht gefunden – bitte erneut anhängen.")
        out.append(a)
    return out


def _mb(n: float) -> str:
    return f"{n / (1024 * 1024):.0f} MB" if n >= 10 * 1024 * 1024 else f"{n / (1024 * 1024):.1f} MB".replace(".", ",")


def attachment_quota_bytes(user: AuthUser) -> int | None:
    """Kontingent für Chat-Bilder je Konto (``SM_CHAT_QUOTA_MB_STAFF/_STUDENT``); ``None`` = unbegrenzt."""
    from schulmanager.server.permissions import STAFF_ROLES

    mb = config.chat_quota_mb_staff if user.role in STAFF_ROLES else config.chat_quota_mb_student
    return int(mb * 1024 * 1024) if mb > 0 else None


def attachment_usage(db: Session, user_id: int) -> int:
    """Von diesem Konto hochgeladene, noch vorhandene Chat-Bilder (gesendete und noch nicht gesendete) in Byte."""
    return int(db.scalar(select(func.coalesce(func.sum(ChatAttachment.size), 0))
                         .where(ChatAttachment.uploader_id == user_id)) or 0)


def _check_attachment_quota(db: Session, user: AuthUser, chat_id: int, extra: int, now: datetime) -> None:
    """S-13: Bilder liegen als Blobs in der Datenbank – Kontingent je Konto und je Chat sowie Rate-Limit."""
    if config.chat_uploads_per_10min > 0:
        recent = db.scalar(select(func.count()).select_from(ChatAttachment).where(
            ChatAttachment.uploader_id == user.id, ChatAttachment.created_at >= now - timedelta(minutes=10))) or 0
        if recent >= config.chat_uploads_per_10min:
            raise _fail(429, "too_many_uploads", "Zu viele Bilder in kurzer Zeit – bitte warten Sie ein paar Minuten.")
    quota = attachment_quota_bytes(user)
    if quota is not None:
        used = attachment_usage(db, user.id)
        if used + extra > quota:
            raise _fail(413, "chat_quota_exceeded",
                        f"Ihr Platz für Chat-Bilder ist voll ({_mb(used)} von {_mb(quota)}). "
                        "Löschen Sie Nachrichten mit Bildern, um wieder Platz zu schaffen.")
    if config.chat_quota_mb_chat > 0:
        limit = int(config.chat_quota_mb_chat * 1024 * 1024)
        in_chat = int(db.scalar(select(func.coalesce(func.sum(ChatAttachment.size), 0))
                                .where(ChatAttachment.chat_id == chat_id)) or 0)
        if in_chat + extra > limit:
            raise _fail(413, "chat_quota_exceeded",
                        f"In diesem Chat ist der Platz für Bilder voll ({_mb(in_chat)} von {_mb(limit)}). "
                        "Löschen Sie ältere Nachrichten mit Bildern oder starten Sie einen neuen Chat.")


@router.post("/chats/{chat_id}/attachments", status_code=201)
async def upload_attachment(chat_id: int, request: Request, user: AuthUser = Depends(require(USE)),
                            db: Session = Depends(get_db)) -> dict:
    """Roher, im Browser verschlüsselter Bild-Blob (``application/octet-stream``). Der Server prüft nur die Größe."""
    chat, mem = _membership(db, chat_id, user)
    _ensure_can_send(db, user)
    _require_post(chat, mem)
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BLOB_BYTES:
        raise _fail(413, "too_large", "Das Bild ist zu groß (höchstens 5 MB).")
    data = await request.body()
    if len(data) > MAX_BLOB_BYTES:
        raise _fail(413, "too_large", "Das Bild ist zu groß (höchstens 5 MB).")
    if len(data) < 17:
        raise _fail(422, "empty", "Leere Datei.")
    now = utcnow()
    db.execute(delete(ChatAttachment).where(ChatAttachment.message_id.is_(None),
                                            ChatAttachment.created_at < now - PENDING_TTL))
    _check_attachment_quota(db, user, chat_id, len(data), now)
    pending = db.scalar(select(func.count()).select_from(ChatAttachment).where(
        ChatAttachment.uploader_id == user.id, ChatAttachment.message_id.is_(None))) or 0
    if pending >= MAX_PENDING:
        raise _fail(429, "too_many_pending", "Zu viele noch nicht gesendete Bilder – bitte erst Nachrichten senden.")
    blob = ChatAttachment(id=uuid.uuid4().hex, chat_id=chat_id, uploader_id=user.id, size=len(data), data=data,
                          created_at=now)
    db.add(blob)
    db.commit()
    return {"id": blob.id, "size": blob.size}


@router.get("/chats/{chat_id}/attachments/{attachment_id}")
def download_attachment(chat_id: int, attachment_id: str, user: AuthUser = Depends(require(USE)),
                        db: Session = Depends(get_db)) -> Response:
    _chat, mem = _membership(db, chat_id, user)
    blob = db.get(ChatAttachment, attachment_id)
    if blob is None or blob.chat_id != chat_id:
        raise _fail(404, "not_found", "Bild nicht gefunden.")
    if blob.message_id is None:
        if blob.uploader_id != user.id:
            raise _fail(404, "not_found", "Bild nicht gefunden.")
    else:
        msg = db.get(ChatMessage, blob.message_id)
        if msg is None or msg.deleted_at is not None or msg.id <= mem.first_message_id:
            raise _fail(404, "not_found", "Bild nicht gefunden.")
    return Response(blob.data, media_type="application/octet-stream",
                    headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"})


class ReadIn(BaseModel):
    up_to: Optional[int] = None


@router.post("/chats/{chat_id}/read")
def mark_read(chat_id: int, body: ReadIn, user: AuthUser = Depends(require(USE)),
              db: Session = Depends(get_db)) -> dict:
    _chat, mem = _membership(db, chat_id, user)
    last = _last_message_id(db, chat_id)
    mem.last_read_id = max(mem.last_read_id, min(body.up_to or last, last))
    db.commit()
    _publish([user.id], chat_id)
    return {"last_read_id": mem.last_read_id}


# =========================================================================== Melden & Moderation
class ReportImage(BaseModel):
    data: str = Field(min_length=8, max_length=(MAX_IMAGE_BYTES * 4) // 3 + 8)     # Base64


class ReportIn(BaseModel):
    reason: str = Field("", max_length=1000)
    content: str = Field("", max_length=20000)
    images: list[ReportImage] = Field(default_factory=list, max_length=MAX_IMAGES)


def _image_mime(raw: bytes) -> str:
    for magic, mime in IMAGE_MAGIC:
        if raw.startswith(magic):
            return mime
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return ""


@router.post("/chats/{chat_id}/messages/{message_id}/report", status_code=201)
def report_message(chat_id: int, message_id: int, body: ReportIn, user: AuthUser = Depends(require(USE)),
                   db: Session = Depends(get_db)) -> dict:
    """Meldet eine fremde Nachricht. Mehrfaches Melden derselben Nachricht durch dieselbe Person aktualisiert die
    offene Meldung (keine Dubletten). Klartext/Bilder schickt die meldende Person freiwillig mit."""
    _chat, mem = _membership(db, chat_id, user)
    msg = db.get(ChatMessage, message_id)
    if (msg is None or msg.chat_id != chat_id or not msg.sender_id or msg.sender_id == user.id
            or msg.id <= mem.first_message_id):
        raise _fail(404, "not_found", "Nachricht nicht gefunden.")
    if msg.deleted_at is not None:
        raise _fail(422, "deleted", "Diese Nachricht wurde bereits gelöscht.")
    images: list[tuple[str, bytes]] = []
    for img in body.images:
        try:
            raw = base64.b64decode(img.data, validate=True)
        except (binascii.Error, ValueError):
            raise _fail(422, "invalid_base64", "Bild: kein gültiges Base64.") from None
        mime = _image_mime(raw)
        if not mime or len(raw) > MAX_IMAGE_BYTES:
            raise _fail(422, "invalid_image", "Bild: nur PNG, JPEG, GIF oder WebP bis 5 MB.")
        images.append((mime, raw))
    rep = db.scalar(select(ChatReport).where(ChatReport.message_id == message_id, ChatReport.reporter_id == user.id,
                                             ChatReport.status == "open"))
    if rep is None:
        rep = ChatReport(chat_id=chat_id, message_id=message_id, reporter_id=user.id, sender_id=msg.sender_id,
                         created_at=utcnow())
        db.add(rep)
        db.flush()
    else:
        db.execute(delete(ChatReportImage).where(ChatReportImage.report_id == rep.id))
    rep.reason_enc = crypto.encrypt_text(body.reason.strip(), rep.aad("reason"))
    rep.content_enc = crypto.encrypt_text(body.content, rep.aad("content"))
    for mime, raw in images:
        row = ChatReportImage(report_id=rep.id, mime=mime, data_enc=b"")
        db.add(row)
        db.flush()
        row.data_enc = crypto.encrypt(raw, row.aad().encode())
    db.commit()
    try:
        bus.publish("change", {"version": None, "scope": ["chat_reports"], "dates": []}, permission=MODERATE)
    except Exception:  # noqa: BLE001
        log.exception("Chats: Moderations-Ereignis konnte nicht verteilt werden")
    _publish([user.id], chat_id)
    return {"id": rep.id}


@router.get("/chat-reports")
def list_reports(status: Literal["open", "all"] = "open", user: AuthUser = Depends(require(MODERATE)),
                 db: Session = Depends(get_db)) -> dict:
    q = select(ChatReport).order_by(ChatReport.id.desc()).limit(200)
    if status == "open":
        q = q.where(ChatReport.status == "open")
    rows = list(db.scalars(q))
    names = _names(db, {r.reporter_id for r in rows} | {r.sender_id for r in rows if r.sender_id})
    imgs: dict[int, list[ChatReportImage]] = {}
    if rows:
        for im in db.scalars(select(ChatReportImage).where(ChatReportImage.report_id.in_([r.id for r in rows]))
                             .order_by(ChatReportImage.id)):
            imgs.setdefault(im.report_id, []).append(im)
    out = []
    for r in rows:
        msg = db.get(ChatMessage, r.message_id)
        out.append({"id": r.id, "chat_id": r.chat_id, "message_id": r.message_id, "status": r.status,
                    "reporter_name": names.get(r.reporter_id, ""), "sender_name": names.get(r.sender_id or -1, ""),
                    "reason": _dec(r.reason_enc, r.aad("reason")), "content": _dec(r.content_enc, r.aad("content")),
                    "images": [{"id": im.id, "mime": im.mime} for im in imgs.get(r.id, [])],
                    "sent_at": iso(msg.created_at) if msg else None, "created_at": iso(r.created_at),
                    "message_deleted": msg is None or msg.deleted_at is not None})
    return {"reports": out}


@router.get("/chat-reports/{report_id}/images/{image_id}")
def report_image(report_id: int, image_id: int, user: AuthUser = Depends(require(MODERATE)),
                 db: Session = Depends(get_db)) -> Response:
    im = db.get(ChatReportImage, image_id)
    if im is None or im.report_id != report_id:
        raise _fail(404, "not_found", "Bild nicht gefunden.")
    try:
        raw = crypto.decrypt(im.data_enc, im.aad().encode())
    except Exception:  # noqa: BLE001
        raise _fail(404, "not_found", "Bild nicht lesbar.") from None
    return Response(raw, media_type=im.mime, headers={
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store",
        "Content-Security-Policy": "sandbox; default-src 'none'", "Content-Disposition": "inline"})


class ResolveIn(BaseModel):
    action: Literal["dismiss", "remove"]


@router.post("/chat-reports/{report_id}")
def resolve_report(report_id: int, body: ResolveIn, user: AuthUser = Depends(require(MODERATE)),
                   db: Session = Depends(get_db)) -> dict:
    rep = db.get(ChatReport, report_id)
    if rep is None:
        raise _fail(404, "not_found", "Meldung nicht gefunden.")
    if body.action == "remove":
        msg = db.get(ChatMessage, rep.message_id)
        if msg is not None and msg.deleted_at is None:
            _wipe(db, msg)
            msg.system_text = "Von der Moderation entfernt."
        rep.status = "removed"
    else:
        rep.status = "dismissed"
    rep.resolved_by = user.id
    rep.resolved_at = utcnow()
    db.commit()
    _publish(_member_ids(db, rep.chat_id), rep.chat_id)
    return {"id": rep.id, "status": rep.status}

