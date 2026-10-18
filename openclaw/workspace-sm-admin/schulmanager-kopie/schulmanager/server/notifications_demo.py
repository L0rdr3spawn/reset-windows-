"""Demo: ein paar erfundene Benachrichtigungen, damit die Glocke in der Vorführung etwas zeigt (``load_demo``).

Nur Beispieltexte ohne Personenbezug; ``dedupe`` verhindert Doppelte beim erneuten Laden der Demo."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select

from . import notifications as nt
from .db import session_scope
from .db_models import User

SAMPLES: dict[str, list[tuple[str, str, str, str, str]]] = {
    # Rolle → (Art, Titel, Text, Ziel, Schlüssel)
    "lehrer": [("substitution", "Vertretungsplan geändert – morgen", "3. Stunde: Vertretung", "/vertretung", "demo:l1"),
               ("course_item", "Neues Material im Kursraum", "Beispielkurs: Arbeitsblatt", "/kursraeume", "demo:l2")],
    "schueler": [("course_item", "Neue Aufgabe im Kursraum", "Beispielkurs: Steckbrief", "/kursraeume", "demo:s1"),
                 ("task_due", "Aufgabe ist morgen fällig", "Beispielkurs: Steckbrief", "/kursraeume", "demo:s2")],
    "eltern": [("substitution", "Vertretungsplan geändert – morgen", "3. Stunde: Entfall", "/stundenplan", "demo:e1"),
               ("absence", "Krankmeldung bestätigt", "", "/krankmeldungen", "demo:e2")],
    "sekretariat": [("absence", "Neue Krankmeldung", "Klasse 5a", "/krankmeldungen", "demo:k1")],
    "planer": [("plan_proposal", "Neuer Vorschlag für den Stundenplan", "", "/planung/vorschlaege", "demo:p1")],
    "schulleitung": [("plan_proposal", "Neuer Vorschlag für den Stundenplan", "", "/planung/vorschlaege", "demo:p1")],
}


def seed_demo(accounts: list[dict[str, Any]] | None = None) -> int:
    """Legt Beispiel-Benachrichtigungen für die Demo-Konten an. Rückgabe: Anzahl neuer Meldungen."""
    names = [a["username"] for a in accounts or [] if a.get("username")]
    if not names:
        return 0
    created = 0
    with session_scope() as db:
        users = list(db.execute(select(User.id, User.role).where(User.username.in_(names), User.active.is_(True))))
        for uid, role in users:
            for kind, title, body, link, key in SAMPLES.get(role, []):
                created += len(nt.notify([uid], kind, title, link, body=body, dedupe=key, db=db))
    return created
