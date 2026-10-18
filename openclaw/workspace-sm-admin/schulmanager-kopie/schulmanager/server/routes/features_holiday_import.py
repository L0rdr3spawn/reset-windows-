"""Ferien/Feiertage aus öffentlicher API übernehmen (``server/holiday_import.py``).

* ``GET  /holiday-import``            Einstellungen + Status (Land, Region, Automatik, letzter Lauf)
* ``PUT  /holiday-import``            Einstellungen speichern (schaltet bei ``enabled`` die Automatik an)
* ``GET  /holiday-import/countries``  Länderliste (serverseitig abgerufen, 24 h gecacht)
* ``GET  /holiday-import/regions?country=DE``  Bundesländer/Regionen
* ``POST /holiday-import/preview``    Was würde sich ändern? (ändert nichts)
* ``POST /holiday-import/apply``      Jetzt übernehmen

Recht wie bei der Pflege der Ferien in den Stammdaten: ``masterdata.edit``.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from schulmanager.server import holiday_import as hi
from schulmanager.server.config import config
from schulmanager.server.deps import AuthUser, require

from .features_common import mutate, snapshot

router = APIRouter(tags=["Stammdaten"])


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    country: str = Field(min_length=2, max_length=2)
    region: str = Field("", max_length=16)
    language: str = Field("de", min_length=2, max_length=2)


class RunIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    #: Startjahre der Schuljahre (2026 = Schuljahr 2026/27); leer = laufendes und nächstes
    school_years: Optional[list[int]] = Field(None, max_length=4)


def _years(body: RunIn) -> Optional[list[int]]:
    ys = body.school_years or None
    if ys and any(not 2000 <= y <= 2100 for y in ys):
        raise HTTPException(422, "Ungültiges Schuljahr")
    return ys


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except hi.HolidayImportError as exc:
        raise HTTPException(exc.status, str(exc)) from None


def _state() -> dict:
    cfg = hi.get_settings(snapshot()[1])
    return {**cfg, "available": config.holiday_import, "status": hi.status(),
            "school_years": hi.current_school_years()}


@router.get("/holiday-import")
def get_state(user: AuthUser = Depends(require("masterdata.edit"))):
    return _state()


@router.put("/holiday-import")
def put_settings(body: SettingsIn, user: AuthUser = Depends(require("masterdata.edit"))):
    cfg = _call(hi.clean_settings, body.model_dump())

    def fn(school):
        school.holiday_import = {**(school.holiday_import or {}), **cfg}

    mutate(user, "Einstellungen für den Ferien-Import geändert", fn, scope=["settings"])
    if cfg["enabled"] and config.holiday_import:
        hi.kick()
    return _state()


@router.get("/holiday-import/countries")
def list_countries(lang: str = Query("de", min_length=2, max_length=2),
                   user: AuthUser = Depends(require("masterdata.edit"))):
    return _call(hi.countries, lang.lower())


@router.get("/holiday-import/regions")
def list_regions(country: str = Query(..., min_length=2, max_length=2),
                 lang: str = Query("de", min_length=2, max_length=2),
                 user: AuthUser = Depends(require("masterdata.edit"))):
    return _call(hi.regions, country, lang.lower())


@router.post("/holiday-import/preview")
def preview(body: RunIn, user: AuthUser = Depends(require("masterdata.edit"))):
    changes = _call(hi.preview, snapshot()[1], _years(body))
    return {"changes": changes, "counts": hi.counts(changes)}


@router.post("/holiday-import/apply")
def apply(body: RunIn, user: AuthUser = Depends(require("masterdata.edit"))):
    return _call(hi.run_import, user, _years(body))
