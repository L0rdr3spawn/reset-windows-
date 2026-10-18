"""Meldungsprotokoll der Fehlzeiten (Tabelle ``student_absence_events``): unveränderlich, nur anhängen.

Jede Krankmeldung/Beurlaubung/Fehlzeit bekommt hier eine lückenlose Zeitleiste: angelegt von wem (Rolle), wann und über
welchen Kanal, danach jede Änderung (Zeitraum, Status, Art, Attest/Entschuldigung eingereicht/geprüft/abgelehnt,
Zurücknahme) mit vorher → nachher. Die Zeilen verweisen bewusst **ohne Fremdschlüssel** auf ``absence_id``: das Protokoll
überlebt das Löschen/Zurücknehmen der Meldung. Gründe, Vermerke und Diagnosen stehen nie im Protokoll (Gesundheitsdaten);
``detail`` enthält nur Zeiträume, Stunden, Status, Art und Kanal.

Ändern und Löschen einzelner Zeilen über das ORM wird abgelehnt (:func:`_forbid`); beim Löschen eines Kontos werden nur
Konto-Verweis und Name pseudonymisiert (``accounts.delete_user``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Index, Integer, String, event
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base, utcnow


class AbsenceEvent(Base):
    __tablename__ = "student_absence_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    absence_id: Mapped[int] = mapped_column(Integer, index=True)           # kein Fremdschlüssel (bleibt nach Löschen)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    # angelegt|zusammengefuehrt|aenderung|zurueckgenommen|dokument_eingereicht|dokument_geprueft|dokument_abgelehnt|
    # dokument_zurueckgezogen|verkuerzt|verlaengert|verlaengerung_beantragt|ruecknahme_angefragt|
    # beurlaubung_zurueckgegeben (Einzelheiten in ``detail``)
    event: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_name: Mapped[str] = mapped_column(String(200), default="")
    actor_role: Mapped[str] = mapped_column(String(40), default="")        # Eltern, Sekretariat, Klassenleitung, …
    channel: Mapped[str] = mapped_column(String(20), default="")           # online|telefon|schriftlich|formular|klassenbuch|lehrkraft|import|system
    detail: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


Index("ix_student_absence_events_absence_at", AbsenceEvent.absence_id, AbsenceEvent.at)


def _forbid(_mapper, _conn, target) -> None:
    raise RuntimeError("Das Meldungsprotokoll ist unveränderlich (nur anhängen)")


event.listen(AbsenceEvent, "before_update", _forbid)
event.listen(AbsenceEvent, "before_delete", _forbid)
