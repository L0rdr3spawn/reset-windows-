"""Schuljahreswechsel-Assistent (``server/year_change.py``): Vorschau → Ausführen → Rückgängig.

* ``POST /year-change/preview``  Was würde passieren? Ändert nichts, liefert ein ``token`` für das Ausführen
* ``POST /year-change/execute``  Führt genau die vorgeschaute Planung aus (Token + gleicher Plan-Stand nötig)
* ``GET  /year-change/runs``     Frühere Läufe (die letzten 5), mit Zusammenfassung
* ``POST /year-change/undo``     Letzten Lauf rückgängig machen (nur wenn der Plan seitdem unverändert ist)

Recht: ``settings.edit`` + ``masterdata.edit`` + ``users.manage`` (Administration, Schulleitung) – der Wechsel betrifft
Klassen, Schülerlisten und Konten der ganzen Schule. Jede Aktion steht im Audit.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from .. import year_change as yc
from ..deps import AuthUser, client_ip, require

router = APIRouter(prefix="/year-change", tags=["Schuljahreswechsel"])

NEED = ("settings.edit", "masterdata.edit", "users.manage")


class ExecuteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan: yc.Plan
    token: str = Field(min_length=10, max_length=200)


@router.post("/preview")
def preview(plan: yc.Plan, _user: AuthUser = Depends(require(*NEED))) -> dict:
    return yc.preview(plan)


@router.post("/execute")
def execute(body: ExecuteIn, request: Request, user: AuthUser = Depends(require(*NEED))) -> dict:
    return yc.execute(body.plan, body.token, user, client_ip(request))


@router.get("/runs")
def runs(_user: AuthUser = Depends(require(*NEED))) -> list[dict]:
    return yc.runs()


@router.post("/undo")
def undo(request: Request, user: AuthUser = Depends(require(*NEED))) -> dict:
    return yc.undo(user, client_ip(request))
