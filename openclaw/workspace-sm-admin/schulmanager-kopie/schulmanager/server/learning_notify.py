"""Benachrichtigungen der Lernaktivitäten (Glocke, ``notifications.notify``; Doku: docs/BENACHRICHTIGUNGEN.md).

Teilnehmende erfahren, wenn im Kursraum eine Abstimmung, Umfrage oder ein Selbsttest bereitsteht. Die Texte nennen nur den
Kursraum und die Art – nie Frage, Titel des Tests oder Ergebnisse."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select

from . import notifications
from .db_models import User

AREAS = {"poll": "abstimmungen", "survey": "umfragen", "selftest": "selbsttests"}
TITLES = {"poll": "Neue Abstimmung", "survey": "Neue Umfrage", "selftest": "Neuer Selbsttest"}


def announce(db: Any, ctx: Any, element: str, element_id: int) -> None:
    """Teilnehmende (Schüler/innen) des Kursraums benachrichtigen; die auslösende Person nicht. Wirft nie."""
    try:
        from .routes.features_channels import _member_user_ids
        ids = _member_user_ids(db, ctx.ch, ctx.spec, ctx.school)
        ids.discard(ctx.user.id)
        if not ids:
            return
        students = set(db.scalars(select(User.id).where(User.id.in_(list(ids)), User.role == "schueler")))
        notifications.notify(
            students, "selftest" if element == "selftest" else "poll", f"{TITLES[element]} im Kursraum",
            f"/kursraeume/{ctx.ch.id}?tab=tests&bereich={AREAS[element]}", body=ctx.ch.title[:120],
            ref=f"channel:{ctx.ch.id}", dedupe=notifications.dedupe_key("learning", element, element_id), actor_id=ctx.user.id,
            db=db)
    except Exception:  # noqa: BLE001 - eine Benachrichtigung darf nie die Aktion verhindern
        pass
