"""E-Mail/SMS für Konto-Vorgänge (Codes, Links, Zugangsbriefe) – docs/ARCHITECTURE.md §11.2.

VERTRAG (Besitzer: Agent Kontakt). Signaturen bleiben stabil.

* :func:`queue_email` – E-Mail in die Outbox (zugestellt vom Dispatcher in ``notify.py``); ``attachments`` =
  ``[{"filename": str, "content_type": str, "data": bytes}]``. Rückgabe: Outbox-ID oder ``None`` (nicht verfügbar).
* :func:`queue_sms` – SMS an eine E.164-Nummer (``+4917…``).
* :func:`email_available` / :func:`sms_available` – kann gerade zugestellt werden (SMTP/SMS konfiguriert oder Test-Postausgang).

Umsetzung
---------
* Outbox-Arten ``secure_email`` und ``sms``: Empfänger, Betreff, Text und Anhänge (base64) liegen **nur verschlüsselt**
  in ``notifications_outbox.payload`` (``crypto.encrypt_text``, AAD ``notifications_outbox:<id>``). ``target`` enthält
  nur eine maskierte Form (``m•••@schule.de`` bzw. ``+49 171 •••••67``), ``subject`` den Zweck (z. B. ``password_reset``).
  Nach der Zustellung (oder endgültigem Fehlschlag) leert ``notify.dispatch_pending`` den Payload.
* **Test-Postausgang** (``SM_DEV_OUTBOX``, nur Entwicklung): Nachrichten bekommen den Status ``test`` – der Dispatcher
  stellt sie nie zu; :func:`dev_outbox_messages` zeigt die letzten 50 (Seite ``/test-postausgang``), die Wartung löscht
  sie nach :data:`DEV_OUTBOX_HOURS` Stunden (:func:`purge_dev_outbox`).
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Any

from ..branding import PRODUCT_NAME

log = logging.getLogger("schulmanager.auth_messages")

SECURE_KINDS: tuple[str, ...] = ("secure_email", "sms")
STATUS_TEST = "test"
DEV_OUTBOX_LIMIT = 50
DEV_OUTBOX_HOURS = 24
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_EMAIL_RE = re.compile(r"^[^@\s<>\"',;]+@[^@\s<>\"',;]+\.[^@\s<>\"',;.]{2,}$")


# =========================================================================== Verfügbarkeit
def email_available() -> bool:
    """E-Mail lässt sich wirklich zustellen: SMTP eingerichtet **und** Versand (Dispatcher) nicht abgeschaltet.
    Der Test-Postausgang zählt nur in der Entwicklung (nie in Produktion)."""
    from .config import config
    return bool((config.smtp_enabled and config.notify_dispatcher) or dev_outbox_enabled())


def sms_available() -> bool:
    """Ein SMS-Anbieter ist eingerichtet (oder – nur in der Entwicklung – der Test-Postausgang)."""
    from . import sms
    return bool(sms.configured() or dev_outbox_enabled())


def dev_outbox_enabled() -> bool:
    from .config import config
    return bool(config.dev_outbox) and not config.is_production


def valid_email(address: str | None) -> bool:
    """Einfache Formatprüfung (eine Adresse, keine Kopfzeilen-Sonderzeichen)."""
    return bool(address) and len(address or "") <= 254 and bool(_EMAIL_RE.match(address or ""))


def mask_email(address: str) -> str:
    """``maria.muster@schule.de`` → ``m•••@schule.de`` (für ``notifications_outbox.target`` und Anzeigen)."""
    local, _, domain = (address or "").partition("@")
    if not domain:
        return "•••"
    return f"{local[:1]}•••@{domain}"


# =========================================================================== Einreihen
def _aad(row_id: int) -> str:
    return f"notifications_outbox:{row_id}"


def _queue(db, kind: str, masked: str, purpose: str, data: dict[str, Any]) -> int:
    from . import crypto, notify
    from .db import utcnow
    from .db_models import NotificationOutbox

    test = dev_outbox_enabled()
    row = NotificationOutbox(kind=kind, target=masked[:500], subject=(purpose or "auth")[:300], payload="",
                             status=STATUS_TEST if test else "pending", attempts=0, next_attempt_at=utcnow(),
                             dedupe_key=f"{kind}:{purpose}:{secrets.token_hex(12)}"[:200], created_at=utcnow())
    db.add(row)
    db.flush()
    row.payload = crypto.encrypt_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), _aad(row.id))
    db.flush()
    if not test:
        notify.kick()
    return row.id


def queue_email(db, to: str, subject: str, text: str, *, attachments: list[dict] | None = None,
                purpose: str = "auth") -> int | None:
    """E-Mail (verschlüsselt) in die Outbox. ``None``, wenn weder SMTP noch Test-Postausgang verfügbar sind.

    Wirft ``ValueError`` bei ungültiger Adresse oder zu großen Anhängen (> 20 MB). Commit macht der Aufrufer."""
    if not email_available():
        return None
    to = (to or "").strip()
    if not valid_email(to):
        raise ValueError("Ungültige E-Mail-Adresse")
    files = []
    total = 0
    for att in attachments or []:
        raw = att.get("data") or b""
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        total += len(raw)
        files.append({"filename": str(att.get("filename") or "anhang.bin")[:200],
                      "content_type": str(att.get("content_type") or "application/octet-stream")[:100],
                      "data": base64.b64encode(bytes(raw)).decode("ascii")})
    if total > MAX_ATTACHMENT_BYTES:
        raise ValueError("Die Anhänge sind zu groß für eine E-Mail (höchstens 20 MB)")
    data = {"to": to, "subject": (subject or PRODUCT_NAME)[:300], "text": text or "", "attachments": files}
    return _queue(db, "secure_email", mask_email(to), purpose, data)


def queue_sms(db, to: str, text: str, *, purpose: str = "auth") -> int | None:
    """SMS (verschlüsselt) in die Outbox. ``None``, wenn weder Anbieter noch Test-Postausgang verfügbar sind."""
    from . import sms

    if not sms_available():
        return None
    number = sms.normalize_phone(to)
    if number is None:
        raise ValueError("Ungültige Telefonnummer")
    data = {"to": number, "subject": "SMS", "text": (text or "")[:sms.MAX_TEXT], "attachments": []}
    return _queue(db, "sms", sms.mask_phone(number), purpose, data)


# =========================================================================== Zustellen (notify._deliver)
def _decode(payload: str, row_id: Any) -> dict[str, Any]:
    from . import crypto

    if not payload:
        raise ValueError("Nachricht bereits zugestellt oder gelöscht")
    data = json.loads(crypto.decrypt_text(payload, _aad(int(row_id))))
    if not isinstance(data, dict):
        raise ValueError("Ungültiger Outbox-Eintrag")
    return data


def _attachments(data: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for att in data.get("attachments") or []:
        try:
            raw = base64.b64decode(att.get("data") or "", validate=True)
        except (binascii.Error, ValueError):
            raw = b""
        out.append({"filename": att.get("filename") or "anhang.bin",
                    "content_type": att.get("content_type") or "application/octet-stream", "data": raw})
    return out


def deliver(kind: str, payload: str, row_id: Any) -> None:
    """Stellt einen ``secure_email``/``sms``-Eintrag zu (vom Dispatcher aufgerufen; wirft bei Fehlern)."""
    from . import notify, sms
    from .config import config

    if dev_outbox_enabled():  # Sicherheitsnetz: im Test-Postausgang nie nach außen zustellen
        raise ValueError("Test-Postausgang aktiv – keine Zustellung")
    data = _decode(payload, row_id)
    to = str(data.get("to") or "")
    try:
        if kind == "secure_email":
            if not config.smtp_enabled:
                raise RuntimeError("SMTP ist nicht konfiguriert")
            notify.send_email(to, data.get("subject") or PRODUCT_NAME, data.get("text") or "",
                              attachments=_attachments(data))
        elif kind == "sms":
            sms.send_sms(to, data.get("text") or "")
        else:
            raise ValueError(f"Unbekannte Art {kind}")
    except Exception as exc:  # noqa: BLE001 - Fehlertext ohne Empfänger im Klartext (landet in last_error)
        masked = mask_email(to) if kind == "secure_email" else sms.mask_phone(sms.normalize_phone(to))
        message = str(exc).replace(to, masked) if to else str(exc)
        raise RuntimeError(f"{type(exc).__name__}: {message}"[:500]) from None


# =========================================================================== Test-Postausgang
def _dev_item(row, data: dict[str, Any]) -> dict[str, Any]:
    from .db import iso

    attachments = []
    for i, att in enumerate(data.get("attachments") or []):
        b64 = att.get("data") or ""
        size = (len(b64) * 3) // 4 - b64[-2:].count("=")
        attachments.append({"index": i, "filename": att.get("filename") or "anhang.bin",
                            "content_type": att.get("content_type") or "application/octet-stream", "size": size})
    return {"id": row.id, "channel": "sms" if row.kind == "sms" else "email", "to": data.get("to") or "",
            "subject": data.get("subject") or "", "text": data.get("text") or "", "purpose": row.subject or "",
            "created_at": iso(row.created_at), "attachments": attachments}


def dev_outbox_messages(db, limit: int = DEV_OUTBOX_LIMIT) -> list[dict[str, Any]]:
    """Die letzten Test-Nachrichten (neueste zuerst), entschlüsselt."""
    from sqlalchemy import select

    from .db_models import NotificationOutbox as O

    rows = db.scalars(select(O).where(O.kind.in_(SECURE_KINDS), O.status == STATUS_TEST)
                      .order_by(O.id.desc()).limit(max(1, min(limit, DEV_OUTBOX_LIMIT)))).all()
    out = []
    for row in rows:
        try:
            out.append(_dev_item(row, _decode(row.payload, row.id)))
        except Exception:  # noqa: BLE001 - z. B. Schlüssel gewechselt: Eintrag überspringen
            log.debug("Test-Nachricht %s nicht lesbar", row.id, exc_info=True)
    return out


def dev_outbox_attachment(db, message_id: int, index: int) -> dict[str, Any] | None:
    """Anhang ``index`` einer Test-Nachricht oder ``None``."""
    from .db_models import NotificationOutbox as O

    row = db.get(O, message_id)
    if row is None or row.kind != "secure_email" or row.status != STATUS_TEST:
        return None
    try:
        files = _attachments(_decode(row.payload, row.id))
    except Exception:  # noqa: BLE001
        return None
    if not 0 <= index < len(files):
        return None
    return files[index]


def purge_dev_outbox(now: datetime | None = None) -> int:
    """Wartung: Test-Nachrichten älter als :data:`DEV_OUTBOX_HOURS` löschen; Klartext (verschlüsselt) endgültig
    fehlgeschlagener Konto-Nachrichten nach derselben Frist leeren."""
    from sqlalchemy import delete, update

    from .db import session_scope, utcnow
    from .db_models import NotificationOutbox as O

    cutoff = (now or utcnow()) - timedelta(hours=DEV_OUTBOX_HOURS)
    with session_scope() as db:
        n = db.execute(delete(O).where(O.kind.in_(SECURE_KINDS), O.status == STATUS_TEST,
                                       O.created_at < cutoff)).rowcount or 0
        db.execute(update(O).where(O.kind.in_(SECURE_KINDS), O.status.in_(("failed", "sent")), O.payload != "",
                                   O.created_at < cutoff).values(payload=""))
    return int(n)

