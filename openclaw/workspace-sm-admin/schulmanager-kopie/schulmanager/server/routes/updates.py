"""Updates der Instanz (nur ``system.admin``): anstehendes Update und Zeitfenster sehen, einmal verschieben, „Jetzt
installieren“, Modus „automatisch/nur manuell“ (siehe ``docs/UPDATES-UND-HOCHVERFUEGBARKEIT.md``).

Die App führt nie selbst ein Update aus: sie schreibt nur Wünsche in ``updater/plan.json``; der Update-Agent (Begleitdienst)
liest sie, prüft die Grenzen und setzt sie um. Alle Aktionen landen im Audit-Protokoll.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import update_state
from ..audit import audit
from ..db import get_db
from ..deps import AuthUser, client_ip, require

router = APIRouter(prefix="/admin/updates", tags=["Updates"])


class PostponeIn(BaseModel):
    version: str = Field(min_length=3, max_length=20)
    days: int = Field(ge=1, le=update_state.MAX_POSTPONE_DAYS)


class VersionIn(BaseModel):
    version: str = Field(min_length=3, max_length=20)


class ModeIn(BaseModel):
    mode: str = Field(pattern="^(auto|manual)$")


class StrategyIn(BaseModel):
    strategy: str = Field(pattern="^(simultaneous|rolling)$")


@router.get("")
def get_updates(_user: AuthUser = Depends(require("system.admin"))) -> dict:
    return update_state.overview()


def _done(db: Session, user: AuthUser, request: Request, action: str, details: dict) -> dict:
    audit(db, user, action, "update", details, ip=client_ip(request))
    db.commit()
    return update_state.overview()


@router.post("/postpone")
def postpone(body: PostponeIn, request: Request, user: AuthUser = Depends(require("system.admin")),
             db: Session = Depends(get_db)) -> dict:
    try:
        req = update_state.postpone(body.version, body.days)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _done(db, user, request, "update.postpone", req)


@router.post("/install-now")
def install_now(body: VersionIn, request: Request, user: AuthUser = Depends(require("system.admin")),
                db: Session = Depends(get_db)) -> dict:
    try:
        req = update_state.install_now(body.version)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _done(db, user, request, "update.install_now", {"version": req["version"]})


@router.put("/mode")
def set_mode(body: ModeIn, request: Request, user: AuthUser = Depends(require("system.admin")),
             db: Session = Depends(get_db)) -> dict:
    st = update_state.read_status() or {}
    if body.mode == "auto" and st.get("mode") == "manual" and st.get("contract_manual"):
        raise HTTPException(409, "Laut Vertrag werden Updates nur manuell installiert.")
    update_state.set_mode(body.mode)
    return _done(db, user, request, "update.mode", {"mode": body.mode})


@router.put("/strategy")
def set_strategy(body: StrategyIn, request: Request, user: AuthUser = Depends(require("system.admin")),
                 db: Session = Depends(get_db)) -> dict:
    st = update_state.read_status() or {}
    if not st.get("may_choose_strategy"):
        raise HTTPException(409, "Die Reihenfolge der Server legt Ihr Anbieter fest.")
    update_state.set_strategy(body.strategy)
    return _done(db, user, request, "update.strategy", {"strategy": body.strategy})
