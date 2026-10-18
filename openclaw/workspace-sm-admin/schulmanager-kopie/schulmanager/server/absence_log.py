"""Meldungsprotokoll der Fehlzeiten: schreiben und – je nach Rechtestufe – ausgeben.

Geschrieben wird mit :func:`record` in derselben Transaktion wie die Änderung an der Meldung (der Aufrufer committet).
Das Protokoll ist nur anhängend (siehe :mod:`schulmanager.server.feature_models.absence_log`).

Wer was sieht (:func:`log_level`, Stufen aus :mod:`schulmanager.server.absence_access`):

* ``full``     – Klassenleitung, Sekretariat, Schulleitung: der volle Verlauf mit Person, Rolle, Kanal und jeder
  Änderung (vorher → nachher). Gründe, Vermerke und Diagnosen stehen auch hier nie im Protokoll.
* ``presence`` – Lehrkräfte, die in der Klasse unterrichten: nur „abwesend gemeldet“ mit Zeitpunkt und Kanal – keine
  Person, keine Art (krank/Beurlaubung), kein Status, keine Dokumente.
* ``None``     – alle anderen (Familie, technische Administration, fremde Lehrkräfte): nichts.
"""
from __future__ import annotations

import contextlib
import contextvars
from datetime import date
from typing import Any, Iterable, Iterator, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..branding import PRODUCT_NAME
from .absence_access import FULL, AbsenceAccess
from .db import iso, utcnow
from .feature_models.absence_log import AbsenceEvent

PRESENCE = "presence"

CHANNEL_LABELS = {"online": f"online im {PRODUCT_NAME}", "telefon": "telefonisch", "schriftlich": "schriftlich",
                  "formular": "über ein Formular", "klassenbuch": "im Klassenbuch",
                  "lehrkraft": "von einer Lehrkraft erfasst", "import": "Import", "system": "automatisch"}
SOURCE_CHANNELS = {"online": "online", "telefon": "telefon", "schriftlich": "schriftlich", "lehrkraft": "lehrkraft"}
ROLE_LABELS = {"eltern": "Eltern", "schueler": "Schüler/in (volljährig)", "sekretariat": "Sekretariat",
               "schulleitung": "Schulleitung", "abteilungsleitung": "Abteilungsleitung", "lehrer": "Lehrkraft",
               "admin": "Administration", "planer": "Planung", "schulbegleitung": "Schulbegleitung"}
FIELD_LABELS = {"status": "Status", "kind": "Art", "source": "Herkunft", "minutes": "Minuten",
                "date_from": "Beginn", "date_to": "Ende", "periods": "Stunden", "reason": "Grund", "note": "Vermerk"}

_channel: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("absence_log_channel", default=None)


@contextlib.contextmanager
def channel_override(channel: str) -> Iterator[None]:
    """Alle Einträge in diesem Block tragen den Kanal (z. B. ``formular`` für Aktionen von Formularen)."""
    token = _channel.set(channel)
    try:
        yield
    finally:
        _channel.reset(token)


def role_label(user: Any, class_lead: bool = False) -> str:
    role = getattr(user, "role", "") or ""
    if role == "lehrer" and class_lead:
        return "Klassenleitung"
    return ROLE_LABELS.get(role, role.capitalize() if role else "System")


def channel_for(user: Any, source: Optional[str]) -> str:
    """Kanal einer neuen Meldung: Eltern/Schüler/innen melden online, Personal nach der gewählten Herkunft."""
    if getattr(user, "role", "") in ("eltern", "schueler"):
        return "online"
    return SOURCE_CHANNELS.get(source or "", "lehrkraft")


def record(db: Session, absence_id: int, student_id: str, event: str, user: Any, *, class_lead: bool = False,
           channel: str = "", changes: Optional[dict] = None, detail: Optional[dict] = None) -> AbsenceEvent:
    """Hängt einen Eintrag an das Protokoll (ohne Commit). ``changes``: ``{feld: [vorher, nachher]}``."""
    data: dict[str, Any] = dict(detail or {})
    if changes:
        data["changes"] = changes
    uid = getattr(user, "id", None) or None
    row = AbsenceEvent(absence_id=absence_id, student_id=student_id, at=utcnow(), event=event, actor_id=uid,
                       actor_name=(getattr(user, "display_name", None) or getattr(user, "username", None) or "System")[:200]
                       if user is not None else "System",
                       actor_role=role_label(user, class_lead) if user is not None else "System",
                       channel=(_channel.get() or channel or "")[:20], detail=data or None)
    db.add(row)
    return row


# ----------------------------------------------------------------------------- Stufe
def log_level(acc: AbsenceAccess, student_id: str) -> Optional[str]:
    """``full`` | ``presence`` | ``None`` – siehe Moduldoku."""
    if acc.role in ("schueler", "eltern") or not acc.can_read:
        return None
    if acc.level(student_id) == FULL:
        return FULL
    tid = acc.teacher_id
    if tid:
        from .permissions import teacher_class_ids

        st = acc.school.index("students").get(student_id)
        if st is not None and st.class_id in teacher_class_ids(acc.school, tid):
            return PRESENCE
    return None


# ----------------------------------------------------------------------------- Lesen
def events_for(db: Session, *, absence_ids: Iterable[int] = (), student_ids: Iterable[str] = ()) -> list[AbsenceEvent]:
    q = select(AbsenceEvent)
    ids, sids = list(absence_ids), list(student_ids)
    if ids:
        q = q.where(AbsenceEvent.absence_id.in_(ids))
    elif sids:
        q = q.where(AbsenceEvent.student_id.in_(sids))
    else:
        return []
    return list(db.scalars(q.order_by(AbsenceEvent.at, AbsenceEvent.id)))


def events_by_absence(db: Session, absence_ids: Iterable[int]) -> dict[int, list[AbsenceEvent]]:
    out: dict[int, list[AbsenceEvent]] = {}
    ids = sorted(set(absence_ids))
    for i in range(0, len(ids), 500):
        for ev in events_for(db, absence_ids=ids[i:i + 500]):
            out.setdefault(ev.absence_id, []).append(ev)
    return out


def _fmt_day(value: Any) -> str:
    try:
        return date.fromisoformat(str(value)).strftime("%d.%m.%Y")
    except ValueError:
        return str(value)


def _value_text(field: str, value: Any, kind: str) -> str:
    from .routes.features_student_absences import KIND_LABELS, SOURCE_LABELS, status_label

    if value is None or value == "":
        return "–"
    if field == "status":
        return status_label(kind, str(value))
    if field == "kind":
        return KIND_LABELS.get(str(value), str(value))
    if field == "source":
        return SOURCE_LABELS.get(str(value), str(value))
    if field in ("date_from", "date_to"):
        return _fmt_day(value)
    if field == "periods":
        return ", ".join(f"{int(p) + 1}." for p in sorted(value)) + " Std." if value else "ganztägig"
    return str(value)


def _range_text(d: dict) -> str:
    d1, d2 = d.get("date_from"), d.get("date_to")
    if not d1:
        return ""
    text = _fmt_day(d1) if d1 == d2 or not d2 else f"{_fmt_day(d1)} bis {_fmt_day(d2)}"
    periods = d.get("periods") or []
    if periods:
        text += f" ({', '.join(str(int(p) + 1) for p in sorted(periods))}. Stunde)"
    return text


def describe(ev: AbsenceEvent, kind: str = "krank") -> str:
    """Kurzer Text zu einem Eintrag (nur für die volle Sicht)."""
    d = ev.detail or {}
    kind = d.get("kind") or kind
    if ev.event == "angelegt":
        from .routes.features_student_absences import KIND_LABELS

        extra = f" für {_range_text(d)}" if d.get("date_from") else ""
        if d.get("extension_of"):
            return f"{KIND_LABELS.get(kind, kind)}: Verlängerung{extra}"
        return f"{KIND_LABELS.get(kind, kind)} gemeldet{extra}"
    if ev.event in ("aenderung", "zusammengefuehrt", "verkuerzt", "verlaengert"):
        parts = []
        for field, pair in (d.get("changes") or {}).items():
            if field in ("reason", "note") and pair is True:
                parts.append("Grund ergänzt" if field == "reason" else "Vermerk geändert")
            elif isinstance(pair, list) and len(pair) == 2:
                parts.append(f"{FIELD_LABELS.get(field, field)}: {_value_text(field, pair[0], kind)} → "
                             f"{_value_text(field, pair[1], kind)}")
        head = {"zusammengefuehrt": "Meldung ergänzt/verlängert", "verkuerzt": "Meldung verkürzt (früher zurück)",
                "verlaengert": "Meldung verlängert"}.get(ev.event, "Geändert")
        if d.get("new_absence_id"):
            head += " (Folgemeldung angelegt)"
        if d.get("taken_over"):
            head += " (Stundenmeldung der Lehrkraft übernommen)"
        return head + (": " + "; ".join(parts) if parts else "")
    if ev.event == "zurueckgenommen":
        what = "Beurlaubungsantrag zurückgezogen" if kind == "beurlaubung" else "Meldung zurückgenommen/gelöscht"
        return what + (f" ({_range_text(d)})" if d.get("date_from") else "")
    if ev.event == "ruecknahme_angefragt":
        return "Rücknahme angefragt (Meldung ist schon bearbeitet – bitte klären)"
    if ev.event == "beurlaubung_zurueckgegeben":
        return "Beurlaubung zurückgegeben – nicht mehr nötig" + (f" ({_range_text(d)})" if d.get("date_from") else "")
    if ev.event == "verlaengerung_beantragt":
        return "Verlängerung der Beurlaubung beantragt" + (f" ({_range_text(d)})" if d.get("date_from") else "")
    cat = {"attest": "Attest", "entschuldigung": "Entschuldigung", "beurlaubung": "Beurlaubungsantrag"}.get(
        str(d.get("category") or ""), "Dokument")
    return {"dokument_eingereicht": f"{cat} eingereicht", "dokument_geprueft": f"{cat} geprüft/genehmigt",
            "dokument_abgelehnt": f"{cat} abgelehnt", "dokument_zurueckgezogen": f"{cat} zurückgezogen"}.get(
        ev.event, ev.event)


def event_out(ev: AbsenceEvent, level: str, kind: str = "krank") -> dict:
    """Eintrag in der Sicht der Stufe (``presence``: nur Zeitpunkt und Kanal der Meldung)."""
    base = {"id": ev.id, "absence_id": ev.absence_id, "at": iso(ev.at), "channel": ev.channel or "",
            "channel_label": CHANNEL_LABELS.get(ev.channel or "", ev.channel or "")}
    if level != FULL:
        return {**base, "event": "abwesend", "text": "abwesend gemeldet"}
    return {**base, "event": ev.event, "text": describe(ev, kind), "actor_name": ev.actor_name,
            "actor_role": ev.actor_role}


def timeline(events: list[AbsenceEvent], level: str, kind: str = "krank") -> list[dict]:
    """Verlauf einer Meldung: voll = alle Einträge; ``presence`` = nur die Meldung selbst (Zeitpunkt/Kanal)."""
    if level == FULL:
        return [event_out(e, level, kind) for e in events]
    first = next((e for e in events if e.event == "angelegt"), None)
    return [event_out(first, level)] if first is not None else []


def first_events(db: Session, absence_ids: Iterable[int]) -> dict[int, AbsenceEvent]:
    """Der Eintrag „angelegt“ je Meldung (Zeitpunkt, Person, Kanal der Meldung)."""
    out: dict[int, AbsenceEvent] = {}
    for aid, evs in events_by_absence(db, absence_ids).items():
        first = next((e for e in evs if e.event == "angelegt"), None)
        if first is not None:
            out[aid] = first
    return out


def report_info(row: Any, first: Optional[AbsenceEvent], level: str) -> dict:
    """Wann/von wem/wie eine Meldung einging (Fallback ohne Protokoll: Felder der Meldung selbst)."""
    channel = (first.channel if first else "") or ("klassenbuch" if row.register_id else
                                                    SOURCE_CHANNELS.get(row.source or "online", "lehrkraft"))
    at = first.at if first else row.created_at
    info = {"reported_at": iso(at), "channel": channel, "channel_label": CHANNEL_LABELS.get(channel, channel)}
    if level == FULL:
        info["reported_by_name"] = (first.actor_name if first else "") or row.reported_by_name or ""
        info["reported_by_role"] = (first.actor_role if first else "") or ""
    return info
