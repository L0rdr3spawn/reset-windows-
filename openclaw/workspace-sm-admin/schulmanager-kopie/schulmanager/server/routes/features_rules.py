"""Regeln und Prioritäten der Stundenplan-Optimierung als Bausteine (``schulmanager/rules.py``).

* ``GET /settings/rules`` – Katalog, aktuelle Bausteine (Stufe, Parameter, Ausnahmen), Vorlagen je Schulart,
  Datenbezug („nur ein Standort“), Wirkung („betrifft 12 Klassen · aktuell 5 Verstöße“) und Auswahllisten.
* ``PUT /settings/rules`` – Bausteine speichern (Teil-Update: ``profile``, ``advanced``, ``items``, ``templates``);
  die Zahlenfelder der Einstellungen (``weights`` …) werden daraus abgeleitet.
* ``POST /settings/rules/template`` – Vorlage anwenden (eingebaut oder eigene) → neue Bausteine, **nicht**
  gespeichert (die Oberfläche zeigt den Entwurf, Speichern über ``PUT``).
* ``POST /settings/rules/templates`` – aktuellen Entwurf als eigene Vorlage sichern.
* ``GET /settings/rules/export`` – Bausteine und eigene Vorlagen als JSON-Datei (Import = ``PUT`` mit dem Inhalt).

Lesen dürfen alle, die planen (``settings.edit``, ``timetable.edit``, ``timetable.generate``); schreiben nur
``settings.edit``.
"""
from __future__ import annotations

import copy
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from schulmanager import rules as rl
from schulmanager.models import School
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import cached, mutate, snapshot

router = APIRouter(tags=["Planung"])


def _may_read(user) -> None:
    if not any(user.has(p) for p in ("settings.edit", "timetable.edit", "timetable.generate")):
        raise HTTPException(403, "Keine Berechtigung")


def _report_stats(snap) -> Optional[dict]:
    """Kennzahlen des Qualitätsberichts (gecacht je Stand) – für die Wirkung je Baustein."""
    def compute():
        from schulmanager.timetable import validate_school
        return validate_school(snap[1])["stats"]
    try:
        return cached("planning_rules_stats", (), compute, snap)
    except Exception:  # noqa: BLE001 – Wirkung ist Zusatzinformation
        return None


class RulesIn(BaseModel):
    """Teil-Update von ``settings.rules``; ``items`` ersetzt die gesamten Bausteine."""
    model_config = ConfigDict(extra="forbid")
    profile: Optional[str] = Field(None, max_length=60)
    advanced: Optional[bool] = None
    items: Optional[dict[str, Any]] = None
    templates: Optional[list[dict[str, Any]]] = None


class TemplateApplyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    template: str = Field(min_length=1, max_length=60)


class TemplateSaveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field("", max_length=300)
    items: dict[str, Any]
    show: Optional[list[str]] = None


@router.get("/settings/rules")
def get_rules(user: AuthUser = Depends(current_user)):
    """Regel-Bausteine samt Katalog, Vorlagen, Datenbezug und Wirkung."""
    _may_read(user)
    snap = snapshot()
    return rl.for_api(snap[1], _report_stats(snap))


def _merge(cur: dict, body: RulesIn) -> dict:
    new = copy.deepcopy(cur)
    patch = body.model_dump(exclude_unset=True)
    for k in ("profile", "advanced", "items", "templates"):
        if patch.get(k) is not None:
            new[k] = patch[k]
    return new


@router.put("/settings/rules")
def put_rules(body: RulesIn, user: AuthUser = Depends(require("settings.edit"))):
    """Bausteine speichern; die Zahlenfelder (``weights``, ``core_latest_period`` …) folgen daraus."""
    def fn(school: School):
        cur = rl.resolve(school.settings)
        new = _merge(cur, body)
        errs = rl.rule_errors(new, school)
        if errs:
            raise HTTPException(422, "; ".join(errs))
        rl.apply_to_settings(school.settings, new)
        return rl.for_api(school, None)

    out = mutate(user, "Regeln und Prioritäten geändert", fn, scope=["settings"])
    snap = snapshot()
    out.update({k: v for k, v in rl.for_api(snap[1], _report_stats(snap)).items() if k == "catalog"})
    return out


@router.post("/settings/rules/template")
def apply_template(body: TemplateApplyIn, user: AuthUser = Depends(require("settings.edit"))):
    """Vorlage anwenden – liefert die neuen Bausteine als Entwurf (nichts wird gespeichert)."""
    school = snapshot()[1]
    items = rl.template_items(body.template, school.settings)
    if items is None:
        raise HTTPException(404, "Vorlage nicht gefunden")
    cur = rl.resolve(school.settings)
    draft = {"profile": body.template, "advanced": cur["advanced"], "items": items, "templates": cur["templates"]}
    norm = rl.normalize(draft, school.settings)
    # fehlende Bausteine mit den Standardwerten (Stufe „wichtig“) ergänzen
    for rid, item in rl.derive_from_numbers(rl.apply_to_settings(copy.deepcopy(school.settings), norm)).items():
        norm["items"].setdefault(rid, item)
    return {"profile": norm["profile"], "items": norm["items"], "show": sorted(rl.shown_ids(body.template, school.settings) or [])}


@router.post("/settings/rules/templates", status_code=201)
def save_template(body: TemplateSaveIn, user: AuthUser = Depends(require("settings.edit"))):
    """Aktuelle Bausteine als eigene Vorlage sichern (export-/importierbar, in den Einstellungen gespeichert)."""
    def fn(school: School):
        cur = rl.resolve(school.settings)
        existing = {t["id"] for t in cur["templates"]} | set(rl.TEMPLATE_BY_ID)
        base = "eigene-" + "".join(ch for ch in body.name.lower() if ch.isalnum())[:30] or "eigene"
        tid, n = base, 1
        while tid in existing:
            n += 1
            tid = f"{base}-{n}"
        cur["templates"].append({"id": tid, "name": body.name.strip(), "description": body.description.strip(),
                                 "items": body.items, "show": body.show or []})
        errs = rl.rule_errors(cur, school)
        if errs:
            raise HTTPException(422, "; ".join(errs))
        rl.apply_to_settings(school.settings, cur)
        return {"id": tid, "templates": rl.for_api(school, None)["templates"]}

    return mutate(user, f"Regel-Vorlage „{body.name.strip()}“ gespeichert", fn, scope=["settings"])


@router.delete("/settings/rules/templates/{template_id}")
def delete_template(template_id: str, user: AuthUser = Depends(require("settings.edit"))):
    def fn(school: School):
        cur = rl.resolve(school.settings)
        before = len(cur["templates"])
        cur["templates"] = [t for t in cur["templates"] if t["id"] != template_id]
        if len(cur["templates"]) == before:
            raise HTTPException(404, "Eigene Vorlage nicht gefunden")
        rl.apply_to_settings(school.settings, cur)
        return {"templates": rl.for_api(school, None)["templates"]}

    return mutate(user, "Regel-Vorlage gelöscht", fn, scope=["settings"])


@router.get("/settings/rules/export")
def export_rules(user: AuthUser = Depends(current_user)):
    """Bausteine und eigene Vorlagen als JSON-Datei."""
    _may_read(user)
    import json
    school = snapshot()[1]
    cur = rl.resolve(school.settings)
    payload = {"format": "schulmanager-regeln", "version": 1, "school": school.settings.school_name,
               "profile": cur["profile"], "items": cur["items"], "templates": cur["templates"]}
    return Response(json.dumps(payload, ensure_ascii=False, indent=2), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="regeln-und-prioritaeten.json"'})
