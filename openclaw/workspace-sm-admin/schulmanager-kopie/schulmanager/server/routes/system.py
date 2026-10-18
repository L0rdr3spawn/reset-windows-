"""Allgemeine Informationen: Rollen-/Rechtematrix, Version."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import rights
from ..config import APP_VERSION, config
from ..db import get_db
from ..deps import AuthUser, current_user
from ..permissions import matrix
from ..store import get_store

router = APIRouter(tags=["System"])


@router.get("/roles")
def roles(_user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Rollen, Rechte und Einschränkungen (für Benutzerverwaltung im Frontend) – wirksam laut Schul-Einstellungen;
    Details und Änderungen: ``/rights``."""
    out = matrix()
    eff = rights.effective_matrix(db)
    out["matrix"] = {r: sorted(eff[r][0]) for r in out["matrix"]}
    out["scopes"] = {r: eff[r][1] for r in eff}
    return out


@router.get("/version")
def version() -> dict:
    """Öffentlich: App-Version und Schulname."""
    return {"version": APP_VERSION, "app_name": config.app_name, "mode": config.mode,
            "school_name": get_store().school.settings.school_name}
