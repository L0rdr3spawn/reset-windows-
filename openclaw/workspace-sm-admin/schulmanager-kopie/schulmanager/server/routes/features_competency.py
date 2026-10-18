"""Kompetenzrahmen: Rahmen, Bereiche, Kompetenzen, Niveaustufen, Vorlagen/Import und Zuordnung zu Aufgaben/Material
(Moodle-Lücke M5, ``docs/KOMPETENZEN.md``). Lernstand, Pläne und Abzeichen: ``features_competency_learning.py``.

* ``GET  /competency/frameworks`` – Rahmen (Kurzform); ``?archived=1`` auch archivierte
* ``POST /competency/frameworks`` – neuer Rahmen mit Bereichen und Kompetenzen (``competency.manage``)
* ``GET|PUT|DELETE /competency/frameworks/{id}`` – lesen / ersetzen (Einträge mit ``id`` bleiben samt Lernständen
  erhalten, fehlende werden gelöscht – mit Lernständen nur mit ``?force=1``) / löschen (nur ohne Lernstände)
* ``POST /competency/frameworks/{id}/archive`` – archivieren bzw. zurückholen
* ``POST /competency/frameworks/import`` – JSON oder CSV (``format``) einlesen; ``GET …/{id}/export?format=json|csv``
* ``GET  /competency/templates`` · ``POST /competency/templates/{key}/use`` – eingebaute Beispielrahmen
* ``GET  /competency/links?item_type=&item_id=`` · ``PUT /competency/links`` – generische Zuordnung von Aufgaben,
  Material u. a. zu Kompetenzen (Schnittstelle für andere Module, siehe Doku)
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager import competency as logic
from schulmanager.server import competency_db as cdb
from schulmanager.server.db import get_db, utcnow
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.competency import (
    CompArea,
    CompAssessment,
    CompCompetency,
    CompFramework,
    CompLink,
    CompPlan,
)

from .features_common import has, need, publish_change, write_audit

router = APIRouter(tags=["Kompetenzen"])
NOT_FOUND = "Kompetenzrahmen nicht gefunden"


class CompetencyIn(BaseModel):
    id: Optional[int] = None
    code: str = Field("", max_length=20)
    title: str = Field(min_length=1, max_length=300)
    descriptors: list[str] = Field(default_factory=list, max_length=logic.MAX_LEVELS)


class AreaIn(BaseModel):
    id: Optional[int] = None
    name: str = Field(min_length=1, max_length=200)
    competencies: list[CompetencyIn] = Field(default_factory=list, max_length=logic.MAX_COMPETENCIES)


class FrameworkIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subject: str = Field("", max_length=40)
    description: str = Field("", max_length=500)
    levels: list[str] = Field(default_factory=lambda: list(logic.DEFAULT_LEVELS), max_length=logic.MAX_LEVELS)
    support_level: int = Field(1, ge=0, le=logic.MAX_LEVELS)
    areas: list[AreaIn] = Field(default_factory=list, max_length=logic.MAX_AREAS)


class ImportIn(BaseModel):
    format: Literal["json", "csv"] = "json"
    content: str = Field(min_length=1, max_length=400_000)
    name: str = Field("", max_length=200)
    subject: str = Field("", max_length=40)
    levels: Optional[list[str]] = Field(None, max_length=logic.MAX_LEVELS)


class LinksIn(BaseModel):
    item_type: str = Field(min_length=1, max_length=30)
    item_id: str = Field(min_length=1, max_length=60)
    competency_ids: list[int] = Field(default_factory=list, max_length=40)


def _viewer(user: AuthUser) -> bool:
    return (getattr(user, "role", "") in ("schueler", "eltern")
            or any(has(user, p) for p in ("competency.read", "competency.assess", "competency.manage")))


def _check(user: AuthUser) -> None:
    if not _viewer(user):
        raise HTTPException(403, "Keine Berechtigung")


def _template_error(exc: Exception) -> HTTPException:
    return HTTPException(422, str(exc))


def _one(db: Session, framework_id: int) -> dict:
    found = cdb.tree(db, [framework_id], archived=True)
    if not found:
        raise HTTPException(404, NOT_FOUND)
    return found[0]


# ------------------------------------------------------------------------------------------------- Rahmen
@router.get("/competency/frameworks")
def list_frameworks(archived: bool = Query(False), user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> list[dict]:
    _check(user)
    return [cdb.framework_summary(f) for f in cdb.tree(db, archived=archived and has(user, "competency.manage"))
            if not f["archived"] or has(user, "competency.manage")]


@router.get("/competency/frameworks/{framework_id}")
def get_framework(framework_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _check(user)
    return _one(db, framework_id)


def _template_of(body: FrameworkIn) -> dict:
    """Prüfung der Pflichtfelder wie bei Vorlagen (ohne die IDs)."""
    try:
        levels = logic.check_levels(body.levels)
        if body.support_level >= len(levels):
            raise logic.TemplateError("Die Stufe für „braucht Unterstützung“ liegt außerhalb der Niveaustufen")
        for a in body.areas:
            for c in a.competencies:
                if len(c.descriptors) > len(levels):
                    raise logic.TemplateError("Höchstens ein Text je Niveaustufe")
        if sum(len(a.competencies) for a in body.areas) > logic.MAX_COMPETENCIES:
            raise logic.TemplateError(f"Höchstens {logic.MAX_COMPETENCIES} Kompetenzen je Rahmen")
    except logic.TemplateError as exc:
        raise _template_error(exc) from exc
    return {"levels": levels}


@router.post("/competency/frameworks", status_code=201)
def create_framework(body: FrameworkIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    levels = _template_of(body)["levels"]
    tmpl = {"name": body.name.strip(), "subject": body.subject.strip(), "description": body.description.strip(),
            "levels": levels, "support_level": body.support_level,
            "areas": [{"name": a.name.strip(), "competencies": [
                {"code": c.code.strip(), "title": c.title.strip(), "descriptors": [d.strip() for d in c.descriptors]}
                for c in a.competencies]} for a in body.areas]}
    fw = cdb.create_framework(db, tmpl, user)
    write_audit(db, user, "competency.framework.create", f"framework:{fw.id}", {"name": fw.name})
    db.commit()
    publish_change(["competency"])
    return _one(db, fw.id)


@router.put("/competency/frameworks/{framework_id}")
def replace_framework(framework_id: int, body: FrameworkIn, force: bool = Query(False),
                      user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    fw = db.get(CompFramework, framework_id)
    if fw is None:
        raise HTTPException(404, NOT_FOUND)
    levels = _template_of(body)["levels"]
    top = db.scalar(select(func.max(CompAssessment.level)).join(
        CompCompetency, CompCompetency.id == CompAssessment.competency_id).where(
        CompCompetency.framework_id == framework_id))
    if top and top > len(levels):
        raise HTTPException(422, f"Es gibt Lernstände mit Stufe {top} – so viele Niveaustufen müssen bleiben")
    areas = {a.id: a for a in db.scalars(select(CompArea).where(CompArea.framework_id == framework_id))}
    comps = {c.id: c for c in db.scalars(select(CompCompetency).where(CompCompetency.framework_id == framework_id))}
    keep_areas = {a.id for a in body.areas if a.id is not None}
    keep_comps = {c.id for a in body.areas for c in a.competencies if c.id is not None}
    if not keep_areas <= set(areas) or not keep_comps <= set(comps):
        raise HTTPException(422, "Bereich oder Kompetenz gehört nicht zu diesem Rahmen")
    drop = [cid for cid in comps if cid not in keep_comps]
    if drop and not force:
        used = db.scalar(select(func.count(CompAssessment.id)).where(CompAssessment.competency_id.in_(drop))) or 0
        if used:
            raise HTTPException(409, f"{used} Lernstand-Einträge gehören zu Kompetenzen, die entfernt würden. "
                                     "Bitte bestätigen.")
    cdb.delete_competencies(db, drop)
    for aid in [a for a in areas if a not in keep_areas]:
        db.delete(areas[aid])
    fw.name, fw.subject, fw.description = body.name.strip(), body.subject.strip(), body.description.strip()
    fw.levels, fw.support_level, fw.updated_at = levels, body.support_level, utcnow()
    for ai, a_in in enumerate(body.areas):
        area = areas.get(a_in.id) if a_in.id is not None else None
        if area is None:
            area = CompArea(framework_id=framework_id, name=a_in.name.strip(), position=ai)
            db.add(area)
            db.flush()
        else:
            area.name, area.position = a_in.name.strip(), ai
        for ci, c_in in enumerate(a_in.competencies):
            c = comps.get(c_in.id) if c_in.id is not None else None
            if c is None:
                c = CompCompetency(framework_id=framework_id, area_id=area.id, position=ci, code="", title="")
                db.add(c)
            c.area_id, c.position = area.id, ci
            c.code, c.title = c_in.code.strip(), c_in.title.strip()
            c.descriptors = [d.strip() for d in c_in.descriptors]
    write_audit(db, user, "competency.framework.update", f"framework:{framework_id}",
                {"name": fw.name, "removed": len(drop)})
    db.commit()
    publish_change(["competency"])
    return _one(db, framework_id)


@router.post("/competency/frameworks/{framework_id}/archive")
def archive_framework(framework_id: int, archived: bool = Query(True), user: AuthUser = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    fw = db.get(CompFramework, framework_id)
    if fw is None:
        raise HTTPException(404, NOT_FOUND)
    fw.archived, fw.updated_at = archived, utcnow()
    write_audit(db, user, "competency.framework.archive", f"framework:{framework_id}", {"archived": archived})
    db.commit()
    publish_change(["competency"])
    return {"id": framework_id, "archived": archived}


@router.delete("/competency/frameworks/{framework_id}")
def delete_framework(framework_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    fw = db.get(CompFramework, framework_id)
    if fw is None:
        raise HTTPException(404, NOT_FOUND)
    comp_ids = list(db.scalars(select(CompCompetency.id).where(CompCompetency.framework_id == framework_id)))
    if comp_ids and db.scalar(select(func.count(CompAssessment.id)).where(CompAssessment.competency_id.in_(comp_ids))):
        raise HTTPException(409, "Der Rahmen hat Lernstände – bitte archivieren statt löschen.")
    if comp_ids and db.scalar(select(func.count(CompPlan.id)).where(CompPlan.competency_id.in_(comp_ids))):
        raise HTTPException(409, "Lernpläne verweisen auf den Rahmen – bitte archivieren statt löschen.")
    cdb.delete_competencies(db, comp_ids)
    for a in db.scalars(select(CompArea).where(CompArea.framework_id == framework_id)):
        db.delete(a)
    db.delete(fw)
    write_audit(db, user, "competency.framework.delete", f"framework:{framework_id}", {"name": fw.name})
    db.commit()
    publish_change(["competency"])
    return {"deleted": framework_id}


# ------------------------------------------------------------------------------------- Import und Export
@router.post("/competency/frameworks/import", status_code=201)
def import_framework(body: ImportIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    try:
        if body.format == "json":
            tmpl = logic.parse_json(body.content)
            if body.name.strip():
                tmpl["name"] = body.name.strip()
        else:
            if not body.name.strip():
                raise logic.TemplateError("Bitte einen Namen für den Rahmen angeben")
            tmpl = logic.parse_csv(body.content, name=body.name.strip(), levels=body.levels, subject=body.subject)
    except logic.TemplateError as exc:
        raise _template_error(exc) from exc
    fw = cdb.create_framework(db, tmpl, user)
    write_audit(db, user, "competency.framework.import", f"framework:{fw.id}", {"name": fw.name, "format": body.format})
    db.commit()
    publish_change(["competency"])
    return _one(db, fw.id)


@router.get("/competency/frameworks/{framework_id}/export")
def export_framework(framework_id: int, format: Literal["json", "csv"] = Query("json"),
                     user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    _check(user)
    import json

    from schulmanager.server.files import content_disposition

    fw = _one(db, framework_id)
    tmpl = {"name": fw["name"], "subject": fw["subject"], "description": fw["description"], "levels": fw["levels"],
            "support_level": fw["support_level"],
            "areas": [{"name": a["name"], "competencies": [
                {"code": c["code"], "title": c["title"], "descriptors": c["descriptors"]} for c in a["competencies"]]}
                for a in fw["areas"]]}
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in fw["name"]).strip() or "Rahmen"
    if format == "csv":
        return Response(logic.to_csv(tmpl).encode("utf-8-sig"), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": content_disposition(f"{safe}.csv")})
    return Response(json.dumps(tmpl, ensure_ascii=False, indent=2).encode("utf-8"), media_type="application/json",
                    headers={"Content-Disposition": content_disposition(f"{safe}.json")})


@router.get("/competency/templates")
def list_templates(user: AuthUser = Depends(current_user)) -> list[dict]:
    need(user, "competency.manage")
    return [{"key": k, "name": t["name"], "description": t["description"], "levels": t["levels"],
             "areas": len(t["areas"]), "competencies": sum(len(a["competencies"]) for a in t["areas"])}
            for k, t in logic.TEMPLATES.items()]


@router.post("/competency/templates/{key}/use", status_code=201)
def use_template(key: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    tmpl = logic.TEMPLATES.get(key)
    if tmpl is None:
        raise HTTPException(404, "Vorlage nicht gefunden")
    fw = cdb.create_framework(db, logic.normalize_template(tmpl), user)
    write_audit(db, user, "competency.framework.create", f"framework:{fw.id}", {"name": fw.name, "template": key})
    db.commit()
    publish_change(["competency"])
    return _one(db, fw.id)


# -------------------------------------------------------------------------------------------- Zuordnungen
def _check_item(item_type: str, item_id: str) -> None:
    if not cdb.ITEM_TYPE_RE.match(item_type) or not cdb.ITEM_ID_RE.match(item_id):
        raise HTTPException(422, "Elementtyp oder Element-ID ist ungültig")


@router.get("/competency/links")
def get_links(item_type: str = Query(..., max_length=30), item_id: str = Query(..., max_length=60),
              user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Kompetenzen, die einer Aufgabe/einem Material zugeordnet sind (Kurzform; Lehrstoff, keine Personendaten)."""
    _check_item(item_type, item_id)
    idx = cdb.competency_index(db)
    rows = db.scalars(select(CompLink).where(CompLink.item_type == item_type, CompLink.item_id == item_id)
                      .order_by(CompLink.id))
    return [{"competency_id": r.competency_id, "title": idx[r.competency_id]["title"],
             "code": idx[r.competency_id]["code"], "framework_id": idx[r.competency_id]["framework_id"],
             "framework_name": idx[r.competency_id]["framework_name"],
             "area_name": idx[r.competency_id]["area_name"]} for r in rows if r.competency_id in idx]


@router.put("/competency/links")
def put_links(body: LinksIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Ersetzt die Kompetenzen eines Elements (leere Liste = alle Zuordnungen entfernen)."""
    need(user, "competency.assess")
    _check_item(body.item_type, body.item_id)
    idx = cdb.competency_index(db)
    wanted = list(dict.fromkeys(body.competency_ids))
    if any(i not in idx for i in wanted):
        raise HTTPException(422, "Eine der Kompetenzen gibt es nicht")
    rows = {r.competency_id: r for r in db.scalars(select(CompLink).where(
        CompLink.item_type == body.item_type, CompLink.item_id == body.item_id))}
    for cid, row in rows.items():
        if cid not in wanted:
            db.delete(row)
    for cid in wanted:
        if cid not in rows:
            db.add(CompLink(competency_id=cid, item_type=body.item_type, item_id=body.item_id,
                            created_by=getattr(user, "id", None)))
    write_audit(db, user, "competency.links", f"{body.item_type}:{body.item_id}", {"competencies": wanted})
    db.commit()
    publish_change(["competency"])
    return {"item_type": body.item_type, "item_id": body.item_id, "competency_ids": wanted}
