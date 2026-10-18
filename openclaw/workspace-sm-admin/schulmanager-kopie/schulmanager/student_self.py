"""Schüler-Selbstbedienung (ARCHITECTURE.md §9.6): reine Logik ohne Datenbank.

* Attestpflicht: Eine Krankmeldung braucht ein Attest, wenn sie mindestens ``settings.sick_note_after_days``
  Schultage umfasst (0 = keine Attestpflicht). Fällig ist es am N-ten Schultag der Abwesenheit; erst danach gilt
  es als „fehlt“ (vorher „erforderlich“).
* Zustände eines Attests je Krankmeldung: ``nicht_noetig`` · ``erforderlich`` · ``fehlt`` · ``eingereicht`` ·
  ``geprueft`` · ``abgelehnt`` (nur abgelehnte Atteste vorhanden → wieder fällig).
* Wer darf sich selbst krankmelden: volljährige Schüler/innen (``users.adult``) für sich, Eltern für ihre Kinder,
  Schulpersonal laut Rechte-Matrix – minderjährige Schüler/innen nicht (Hinweis statt Knopf).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Optional

from .calendar_utils import as_date, school_days
from .models import School

CATEGORIES: dict[str, str] = {
    "attest": "Ärztliches Attest",
    "entschuldigung": "Entschuldigung",
    "beurlaubung": "Antrag auf Beurlaubung (unterschrieben)",
    "einverstaendnis": "Einverständniserklärung",
    "sonstiges": "Sonstiges Dokument",
}
DOC_STATUSES: dict[str, str] = {"eingegangen": "eingereicht", "geprueft": "genehmigt", "abgelehnt": "abgelehnt"}
ATTEST_LABELS: dict[str, str] = {
    "nicht_noetig": "kein Attest nötig",
    "erforderlich": "Attest erforderlich",
    "fehlt": "Attest fehlt",
    "eingereicht": "Attest eingereicht",
    "geprueft": "Attest genehmigt",
    "abgelehnt": "Attest abgelehnt",
}


@dataclass(frozen=True)
class AttestInfo:
    required: bool
    school_days: int
    due: Optional[str]          # ISO-Datum des Fälligkeitstags (N-ter Schultag) oder None
    state: str                  # siehe ATTEST_LABELS

    @property
    def missing(self) -> bool:
        """Handlungsbedarf: fällig und keins da – oder nur abgelehnte Atteste (bei Attestpflicht)."""
        return self.state == "fehlt" or (self.required and self.state == "abgelehnt")

    def to_dict(self) -> dict:
        return {"required": self.required, "school_days": self.school_days, "due": self.due, "state": self.state,
                "label": ATTEST_LABELS[self.state], "missing": self.missing}


def absence_school_days(school: School, date_from: date | str, date_to: date | str,
                        cls: Any = None) -> list[date]:
    """Schultage einer Abwesenheit (Tage ohne Unterricht der Klasse und Ferien zählen nicht; ``cls`` = Klasse bzw.
    deren ID, ohne Klasse die Schulöffnungstage)."""
    d1, d2 = as_date(date_from), as_date(date_to)
    if d2 < d1:
        return []
    return school_days(school, d1, d2, cls)


def attest_info(school: School, date_from: date | str, date_to: date | str,
                doc_statuses: Iterable[str] = (), today: Optional[date] = None, cls: Any = None) -> AttestInfo:
    """Attest-Zustand einer Krankmeldung aus Zeitraum und den Status der zugeordneten Atteste (gezählt werden die
    Unterrichtstage der Klasse ``cls``)."""
    limit = max(0, int(getattr(school.settings, "sick_note_after_days", 0) or 0))
    days = absence_school_days(school, date_from, date_to, cls)
    statuses = list(doc_statuses)
    required = limit > 0 and len(days) >= limit
    due = days[limit - 1].isoformat() if required else None
    if "geprueft" in statuses:
        state = "geprueft"
    elif "eingegangen" in statuses:
        state = "eingereicht"
    elif not required:
        state = "nicht_noetig"
    elif "abgelehnt" in statuses:
        state = "abgelehnt"
    else:
        state = "fehlt" if due is not None and (today or date.today()).isoformat() >= due else "erforderlich"
    return AttestInfo(required=required, school_days=len(days), due=due, state=state)


def self_report_hint(role: str, adult: bool) -> Optional[str]:
    """Hinweis, warum (bzw. ``None``, wenn) eine Person keine eigene Krankmeldung abgeben darf."""
    if role == "schueler" and not adult:
        return ("Sie dürfen selbst keine Krankmeldung und keine Beurlaubung abgeben, weil Sie noch nicht volljährig "
                "sind. Das machen Ihre Erziehungsberechtigten über ihr Eltern-Konto. Werden Sie volljährig, schaltet "
                "das Sekretariat Ihr Konto dafür frei.")
    return None


def clean_title(text: str, category: str) -> str:
    title = " ".join((text or "").split())[:200]
    return title or CATEGORIES.get(category, "Dokument")
