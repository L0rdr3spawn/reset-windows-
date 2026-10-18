"""Schutz der öffentlichen Demo (``SM_DEMO_PUBLIC=1``) – Allowlist statt Blocklist (S-03).

In der öffentlichen Demo sind Demo-Zugänge der Art ``admin``/``schulleitung`` echte Konten mit weitreichenden Rechten
und beliebige Besucher können sich damit anmelden. Deshalb sind **alle schreibenden Anfragen (POST/PUT/PATCH/DELETE)
gesperrt, außer sie stehen in** :data:`ALLOW` – also nur, was eine Vorführung braucht (Stundenplan, Vertretungen,
Klassen, Konten anlegen, Kursräume, Nachrichten …). Eine **neue Route ist damit standardmäßig gesperrt**; wer sie für
die Demo freigeben will, trägt sie hier bewusst ein (und `tests/test_demo_guard.py` zeigt, was erlaubt ist).

Gesperrt bleiben insbesondere (alles mit Außenwirkung oder Wirkung auf alle Besucher): Anmeldedienste (SSO), Rechte
und Rollen, Anmelde-Richtlinien, JSON-/CSV-/Untis-Import, Verlauf/Rückgängig, API-Zugänge, Mail-Konten, Lizenz,
Benachrichtigungs-Einstellungen der Schule/Postausgang, Ferien-Import (Fremddienst), Webhooks in den Einstellungen,
Sicherheits-Einstellungen, Versand von Zugangsbriefen per E-Mail, Kontakt-/Identitäts-Verknüpfungen, Systemverwaltung.

Zusätzlich (``deps._guard_demo``): Demo-Konten selbst bleiben für alle gleich (Passwort/2FA/Änderung durch Verwaltung).
Die Prüfung gilt für angemeldete Anfragen; öffentliche Endpunkte (Anmelden, Passwort vergessen …) bleiben unberührt.
"""
from __future__ import annotations

import re
from typing import Iterable

from fastapi import HTTPException

from .config import config

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
NOT_POSSIBLE = "In der öffentlichen Demo nicht möglich (die Demo-Konten bleiben für alle Besucher gleich)."
ALL = ("POST", "PUT", "PATCH", "DELETE")

#: (Methoden, Pfadvorlage ohne ``/api/v1``). ``{x}`` = ein Pfadteil, ``{x:int}`` = nur Ziffern, ``/**`` am Ende = beliebig tief darunter.
ALLOW: tuple[tuple[tuple[str, ...], str], ...] = (
    # Alltag einer Schule
    (ALL, "/absences/**"), (ALL, "/announcements/**"), (ALL, "/classes/**"), (ALL, "/data/**"),
    (ALL, "/duties/generate"), (ALL, "/exam-makeups/**"), (ALL, "/exams/**"), (ALL, "/grade-levels/**"),
    (ALL, "/overrides/**"), (ALL, "/parent-access"), (ALL, "/planning/**"), (ALL, "/register/lesson"),
    (ALL, "/student-absences/**"), (ALL, "/student-documents/**"), (ALL, "/students/**"),
    (ALL, "/substitutions/release"), (ALL, "/support/**"), (ALL, "/teacher-profiles/**"),
    (ALL, "/teacher-requests/**"), (ALL, "/timetable/**"), (ALL, "/monitor/config/{site}"),
    # Lernen, Kursräume, Kommunikation (intern)
    (ALL, "/channels/**"), (ALL, "/chat-keys/**"), (ALL, "/chat-links/**"), (ALL, "/chat-reports/{id}"),
    (ALL, "/chats/**"), (ALL, "/competency/**"), (ALL, "/files"), (ALL, "/files/{id}"), (ALL, "/forms/**"),
    (ALL, "/gradebook/**"), (ALL, "/grading/**"),
    (ALL, "/messages/blocks/**"), (ALL, "/messages/conversations/**"), (ALL, "/messages/drafts/**"),
    (ALL, "/messages/read-all"), (ALL, "/messages/settings"), (("POST",), "/messages/moderation/reports/{id}/resolve"),
    (ALL, "/notifications"), (ALL, "/notifications/read"), (ALL, "/notifications/settings"),
    (("DELETE",), "/notifications/{id:int}"),
    # Einstellungen ohne Außenwirkung (Webhooks in /settings prüft ``forbid_fields``)
    (("PUT",), "/settings"), (("POST",), "/settings/calendar-preview"), (ALL, "/settings/rules"),
    (ALL, "/settings/rules/**"),
    # Konten: anlegen, ändern, Passwörter/Briefe (ohne E-Mail-Versand, API-Token, Verknüpfungen, Kontakte)
    (("POST",), "/users"), (("POST",), "/users/bulk"), (("POST",), "/users/letters.pdf"),
    (("PATCH", "DELETE"), "/users/{id}"), (("POST",), "/users/{id}/password"), (("POST",), "/users/{id}/reset-password"),
    (("PUT",), "/users/{id}/children"), (ALL, "/users/{id}/children/{sid}"), (("DELETE",), "/users/{id}/sessions"),
    (("POST",), "/letters/batches"),
    (("DELETE",), "/sessions/{id}"),
    # Eigenes Profil (ohne Kontakt-/Anbieter-Verknüpfung)
    (ALL, "/me/ical-url"), (ALL, "/me/teacher-profile/**"), (ALL, "/me/teacher-requests/**"),
    # Anmelden/Abmelden/Kontowechsel (eigenes Passwort/2FA der Demo-Konten sperrt ``deps._guard_demo``)
    (ALL, "/auth/**"),
    # Vorführ-Verwaltung durch den Inhaber (prüft die Route selbst)
    (("POST",), "/demo-access"),
)


def _compile(template: str) -> re.Pattern[str]:
    deep = template.endswith("/**")
    if deep:
        template = template[:-3]
    rx = re.escape(template)
    rx = re.sub(r"\\\{[a-z_]+:int\\\}", lambda _m: r"\d+", rx)
    rx = re.sub(r"\\\{[a-z_]+\\\}", "[^/]+", rx)
    return re.compile("^" + rx + ("(/.*)?" if deep else "") + "$")


_COMPILED = tuple((frozenset(m), _compile(t), t) for m, t in ALLOW)


def is_allowed(method: str, path: str) -> bool:
    """Darf diese schreibende Anfrage in der Demo ausgeführt werden? (``path`` ohne ``/api/v1``)"""
    method = method.upper()
    path = "/" + path.strip("/") if path.strip("/") else "/"
    return any(method in methods and rx.match(path) for methods, rx, _ in _COMPILED)


def matching_rule(method: str, path: str) -> str | None:
    path = "/" + path.strip("/")
    for methods, rx, template in _COMPILED:
        if method.upper() in methods and rx.match(path):
            return template
    return None


def check(method: str, path: str) -> None:
    """Wirft 403, wenn die Demo diese schreibende Anfrage nicht erlaubt. Ohne ``SM_DEMO_PUBLIC`` wirkungslos."""
    if not config.demo_public or method.upper() not in UNSAFE_METHODS:
        return
    if not is_allowed(method, path):
        raise HTTPException(403, NOT_POSSIBLE)


def forbid_fields(patch: dict, fields: Iterable[str]) -> None:
    """Felder, die in der Demo nicht gesetzt werden dürfen (z. B. ``webhooks`` in ``PUT /settings``)."""
    if not config.demo_public:
        return
    for name in fields:
        if patch.get(name):
            raise HTTPException(403, NOT_POSSIBLE)
