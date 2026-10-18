"""Webhook-Nutzlasten und Signaturen (HMAC-SHA256).

Ablauf für Empfänger (z. B. Schul-App, Infobildschirm, n8n/Zapier, Schulmanager-Online-Bridge):

1. Der Schulmanager sendet ``POST`` mit JSON-Body (UTF-8) und den Headern
   ``X-Schulmanager-Event``, ``X-Schulmanager-Delivery`` (eindeutige ID),
   ``X-Schulmanager-Timestamp`` (Unix-Sekunden) und
   ``X-Schulmanager-Signature: sha256=<hex>`` = HMAC-SHA256 über die **rohen Body-Bytes**
   mit dem gemeinsamen Geheimnis (``SM_WEBHOOK_SECRET``).
2. Empfänger prüft mit :func:`verify` (konstante Laufzeit) und verwirft ältere
   Zustellungen anhand von ``sent_at``/Timestamp (Replay-Schutz) bzw. doppelte ``id``.

Nutzlast (Schema-Version 1)::

    {"schema": "schulmanager.webhook", "schema_version": 1, "id": "<uuid>",
     "event": "substitutions.changed", "sent_at": "2026-10-06T07:12:00Z",
     "school": "Gesamtschule …", "data": {...}}

Bekannte Ereignisse siehe :data:`EVENTS` (weitere sind erlaubt, Format ``bereich.aktion``).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

__all__ = ["SCHEMA", "SCHEMA_VERSION", "SIGNATURE_HEADER", "EVENTS", "payload", "encode", "sign", "verify",
           "headers"]

SCHEMA = "schulmanager.webhook"
SCHEMA_VERSION = 1
SIGNATURE_HEADER = "X-Schulmanager-Signature"
EVENT_HEADER = "X-Schulmanager-Event"
DELIVERY_HEADER = "X-Schulmanager-Delivery"
TIMESTAMP_HEADER = "X-Schulmanager-Timestamp"

EVENTS = {
    "substitutions.changed": "Vertretungsplan für einen/mehrere Tage geändert (data: dates, entries/plan)",
    "timetable.changed": "Stundenplan geändert/veröffentlicht (data: version, scope)",
    "absence.reported": "Krankmeldung einer Lehrkraft eingegangen",
    "announcement.created": "Neue Mitteilung",
    "exam.changed": "Klausur angelegt/geändert",
    "student_absence.reported": "Schüler-Krankmeldung (ohne Gesundheitsdaten)",
    "ping": "Testzustellung",
}
_EVENT_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$|^ping$")


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    raise TypeError(f"nicht serialisierbar: {type(obj).__name__}")


def payload(event: str, data: Any, *, school: Any = None, sent_at: Optional[datetime] = None,
            delivery_id: Optional[str] = None) -> dict:
    """Baut die Webhook-Nutzlast.

    ``school``: ``School``-Objekt oder Schulname (optional). ``data`` muss JSON-serialisierbar
    sein (Objekte mit ``to_dict``/``isoformat`` werden umgewandelt).
    """
    if not isinstance(event, str) or not _EVENT_RE.match(event):
        raise ValueError(f"Ungültiger Ereignisname {event!r} (Format: bereich.aktion)")
    name = ""
    if school is not None:
        name = school if isinstance(school, str) else getattr(getattr(school, "settings", None), "school_name", "")
    ts = (sent_at or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    body = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "id": delivery_id or str(uuid.uuid4()),
        "event": event,
        "sent_at": ts.isoformat().replace("+00:00", "Z"),
        "school": name,
        "data": json.loads(json.dumps(data, default=_json_default, ensure_ascii=False)),
    }
    return body


def encode(body: dict) -> bytes:
    """Kanonische JSON-Bytes (UTF-8, sortierte Schlüssel, kompakt) – genau diese Bytes signieren & senden."""
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      default=_json_default).encode("utf-8")


def sign(body: bytes, secret: str) -> str:
    """``sha256=<hex>`` = HMAC-SHA256(secret, body)."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    if not secret:
        raise ValueError("Webhook-Geheimnis fehlt")
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify(body: bytes, secret: str, signature: str, *, timestamp: Any = None, tolerance: int = 300) -> bool:
    """Prüft die Signatur (konstante Laufzeit).

    Optional ``timestamp`` (Unix-Sekunden oder ISO-8601, z. B. ``sent_at`` aus der signierten
    Nutzlast): Zustellungen, die älter/neuer als ``tolerance`` Sekunden sind, werden abgelehnt.
    """
    if not signature or not secret:
        return False
    try:
        expected = sign(body, secret)
    except ValueError:
        return False
    if not hmac.compare_digest(expected, str(signature).strip()):
        return False
    if timestamp is not None:
        try:
            ts = str(timestamp).strip()
            if re.fullmatch(r"\d+(\.\d+)?", ts):
                epoch = float(ts)
            else:
                epoch = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            if abs(time.time() - epoch) > tolerance:
                return False
        except (TypeError, ValueError):
            return False
    return True


def headers(body: bytes, secret: str, event: str, delivery_id: Optional[str] = None) -> dict[str, str]:
    """HTTP-Header für eine Zustellung (Content-Type, Event, Delivery, Timestamp, Signatur)."""
    return {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Schulmanager-Webhook/1",
        EVENT_HEADER: event,
        DELIVERY_HEADER: delivery_id or str(uuid.uuid4()),
        TIMESTAMP_HEADER: str(int(time.time())),
        SIGNATURE_HEADER: sign(body, secret),
    }
