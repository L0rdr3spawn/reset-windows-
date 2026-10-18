"""Handbuch in der App: Kurzanleitungen je Rolle aus ``docs/hilfe/*.md`` (``GET /manual``).

Die Markdown-Dateien liegen im Repository (``docs/hilfe``) und im Container-Image; ``SM_HELP_DIR`` überschreibt den
Ort. Jede Rolle bekommt nur die Anleitungen, die für sie gedacht sind (siehe :data:`GUIDES_BY_ROLE`). Der Text enthält
keine Schul- oder Personendaten.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends

from ..deps import AuthUser, current_user

log = logging.getLogger("schulmanager.manual")
router = APIRouter(tags=["Hilfe"])

_ROOT = Path(__file__).resolve().parents[3]

#: Anleitungen in Anzeigereihenfolge (Datei ohne ``.md``)
GUIDES = ("administration", "schulleitung", "lehrkraft", "eltern", "schueler")
GUIDES_BY_ROLE: dict[str, tuple[str, ...]] = {
    "admin": GUIDES,
    "zuschauer": GUIDES,
    "schulleitung": ("schulleitung", "lehrkraft", "eltern", "schueler"),
    "sekretariat": ("schulleitung", "lehrkraft"),
    "planer": ("schulleitung", "lehrkraft"),
    "abteilungsleitung": ("schulleitung", "lehrkraft"),
    "lehrer": ("lehrkraft",),
    "hausmeister": ("lehrkraft",),
    "schulbegleitung": ("schueler", "eltern"),
    "eltern": ("eltern",),
    "schueler": ("schueler",),
}


def help_dir() -> Path:
    return Path(os.environ.get("SM_HELP_DIR") or (_ROOT / "docs" / "hilfe"))


def load_guide(guide_id: str) -> dict | None:
    path = help_dir() / f"{guide_id}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        log.warning("Anleitung %s nicht gefunden (%s)", guide_id, path)
        return None
    title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), guide_id.capitalize())
    return {"id": guide_id, "title": title, "markdown": text}


@router.get("/manual")
def manual(user: AuthUser = Depends(current_user)) -> dict:
    """Kurzanleitungen für die Rolle der angemeldeten Person (Markdown)."""
    ids = GUIDES_BY_ROLE.get(user.role, ())
    guides = [g for g in (load_guide(i) for i in ids) if g]
    return {"role": user.role, "guides": guides}
