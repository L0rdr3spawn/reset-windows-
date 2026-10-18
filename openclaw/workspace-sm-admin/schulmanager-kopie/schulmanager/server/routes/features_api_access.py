"""API-Zugänge verwalten: ausgeben, auflisten, Nutzung ansehen, widerrufen (docs/API-ZUGAENGE.md).

* Anlegen: nur mit Anmeldung per Sitzung (kein Token stellt Zugänge aus) und Recht ``api.own`` bzw. ``api.manage``.
  Ein Konto gibt **höchstens aus, was es selbst sieht** (``api_scopes.normalize_scope``); Gesundheits-/Förderdaten
  gibt es in keinem Bereich.
* Das Token wird nur in der Antwort des Anlegens im Klartext geliefert, gespeichert wird nur der Hash.
* ``api.manage`` (Administration, Schulleitung): alle Zugänge sehen, Nutzung prüfen, widerrufen. ``api.own``: nur eigene.
"""
from __future__ import annotations

import ipaddress
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager.server import api_scopes as scopes
from schulmanager.server.audit import audit
from schulmanager.server.config import config
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import ApiToken, User
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.feature_models.api_access import ApiTokenLog
from schulmanager.server.security import hash_token, new_token

from .features_common import has, snapshot

router = APIRouter(tags=["API-Zugänge"])


class FiltersIn(BaseModel):
    classes: list[str] = Field(default_factory=list)
    teachers: list[str] = Field(default_factory=list)
    rooms: list[str] = Field(default_factory=list)
    students: list[str] = Field(default_factory=list)
    sites: list[str] = Field(default_factory=list)


class AccessIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    purpose: str = Field("", max_length=300)
    expires_days: int = Field(scopes.DEFAULT_EXPIRES_DAYS, ge=1, le=scopes.MAX_EXPIRES_DAYS)
    areas: list[str] = Field(default_factory=list)
    write: list[str] = Field(default_factory=list)
    filters: FiltersIn = Field(default_factory=FiltersIn)
    ip_allow: list[str] = Field(default_factory=list, max_length=20)
    rate_limit: int = Field(scopes.DEFAULT_RATE, ge=1, le=scopes.MAX_RATE)


# --------------------------------------------------------------------------------------- Hilfen
def _need_any(user: AuthUser) -> None:
    if not (has(user, "api.own") or has(user, "api.manage")):
        raise HTTPException(403, "Keine Berechtigung für API-Zugänge")


def _need_session(user: AuthUser) -> None:
    if user.auth_method != "session":
        raise HTTPException(403, "API-Zugänge können nur nach Anmeldung in der Oberfläche ausgegeben werden.")


def _status(row: ApiToken) -> str:
    if row.revoked_at is not None:
        return "revoked"
    if row.expires_at is not None and row.expires_at < utcnow():
        return "expired"
    return "active"


def _ip_list(values: list[str]) -> list[str]:
    out = []
    for v in values:
        v = v.strip()
        if not v:
            continue
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError:
            raise HTTPException(422, f"Ungültige IP-Adresse oder Netz: {v}") from None
        out.append(v)
    return list(dict.fromkeys(out))


def _scope_from(body: AccessIn, actor: AuthUser, snap) -> dict:
    return scopes.normalize_scope(actor, snap, areas=body.areas, write=body.write, filters=body.filters.model_dump())


def access_dict(row: ApiToken, owners: dict[int, str], school=None) -> dict[str, Any]:
    scope = row.scope or {}
    out = {
        "id": row.id, "name": row.name, "purpose": row.purpose or "", "prefix": row.prefix, "status": _status(row),
        "owner": {"id": row.user_id, "name": owners.get(row.user_id, "")}, "created_at": iso(row.created_at),
        "expires_at": iso(row.expires_at), "last_used": iso(row.last_used), "revoked_at": iso(row.revoked_at),
        "use_count": row.use_count or 0, "areas": scope.get("areas") or [], "write": scope.get("write") or [],
        "filters": scope.get("filters") or {}, "ip_allow": row.ip_allow or [],
        "rate_limit": row.rate_limit or scopes.DEFAULT_RATE,
    }
    if school is not None and row.scope:
        out["summary"] = scopes.describe(scope, school)["can"]
    return out


def _owners(db: Session, rows: list[ApiToken]) -> dict[int, str]:
    ids = {r.user_id for r in rows}
    if not ids:
        return {}
    return {u.id: (u.display_name or u.username) for u in db.scalars(select(User).where(User.id.in_(ids)))}


def _get_access(db: Session, actor: AuthUser, access_id: int) -> ApiToken:
    row = db.get(ApiToken, access_id)
    if row is None or row.scope is None or (row.user_id != actor.id and not has(actor, "api.manage")):
        raise HTTPException(404, "API-Zugang nicht gefunden")   # fremde Zugänge: nicht verraten
    return row


def _examples(token: str, scope: dict) -> list[str]:
    base = f"{config.base_url}/api/v1"
    return [f'curl -H "Authorization: Bearer {token}" "{base}{p}"' for p in scopes.example_paths(scope)]


# ------------------------------------------------------------------------------------ Endpunkte
@router.get("/api-access/meta", summary="Was darf dieses Konto freigeben? (Bereiche, Filterwerte)")
def access_meta(actor: AuthUser = Depends(current_user)) -> dict:
    _need_any(actor)
    snap = snapshot()
    school = snap[1]
    allowed = scopes.creatable_values(actor, snap)

    def pick(kind: str, items) -> Optional[list[dict]]:
        ok = allowed.get(kind)
        rows = [i for i in items if ok is None or i["id"] in ok]
        return rows

    students = []
    if allowed.get("students") != []:
        ok = allowed["students"]
        students = [{"id": s.id, "name": s.name, "class_id": s.class_id} for s in school.students
                    if ok is None or s.id in ok]
    return {
        "areas": [{"id": a, "label": m["label"], "description": m["description"], "filters": m["filters"],
                   "available": scopes.area_available(actor, a), "write": bool(m.get("write")),
                   "write_available": scopes.write_available(actor, a)} for a, m in scopes.AREAS.items()],
        "filters": [{"id": k, "label": v} for k, v in scopes.FILTER_LABELS.items()],
        "values": {
            "classes": pick("classes", [{"id": c.id, "name": c.name} for c in school.classes]),
            "teachers": pick("teachers", [{"id": t.id, "name": t.name} for t in school.teachers]),
            "rooms": pick("rooms", [{"id": r.id, "name": r.name} for r in school.rooms]),
            "sites": [{"id": s.id, "name": s.name} for s in school.sites],
            "students": students,
        },
        "not_offered": [{"id": k, "reason": v} for k, v in scopes.NOT_OFFERED.items()],
        "limits": {"default_expires_days": scopes.DEFAULT_EXPIRES_DAYS, "max_expires_days": scopes.MAX_EXPIRES_DAYS,
                   "default_rate": scopes.DEFAULT_RATE, "max_rate": scopes.MAX_RATE,
                   "max_access": scopes.MAX_ACCESS_PER_USER},
        "can_manage_all": has(actor, "api.manage"), "can_create": has(actor, "api.own"),
        "docs": {"llms": f"{config.base_url}/llms.txt", "openapi": f"{config.base_url}/api/v1/meta/openapi.json",
                 "scopes": f"{config.base_url}/api/v1/meta/scopes"},
    }


@router.post("/api-access/preview", summary="Vorschau: Was darf ein Zugang mit diesen Einstellungen?")
def access_preview(body: AccessIn, actor: AuthUser = Depends(current_user)) -> dict:
    _need_any(actor)
    snap = snapshot()
    scope = _scope_from(body, actor, snap)
    out = scopes.describe(scope, snap[1], actor)
    out["examples"] = _examples("<TOKEN>", scope)
    out["scope"] = scope
    return out


@router.get("/api-access", summary="API-Zugänge auflisten (eigene; mit api.manage alle)")
def list_access(all_: bool = Query(False, alias="all"), actor: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> list[dict]:
    _need_any(actor)
    q = select(ApiToken).where(ApiToken.scope.is_not(None)).order_by(ApiToken.id.desc())
    if not (all_ and has(actor, "api.manage")):
        q = q.where(ApiToken.user_id == actor.id)
    rows = list(db.scalars(q))
    rows = [r for r in rows if r.scope is not None]    # JSON-null (nicht SQL-NULL) zuverlässig ausschließen
    owners = _owners(db, rows)
    school = snapshot()[1]
    return [access_dict(r, owners, school) for r in rows]


@router.post("/api-access", status_code=201, summary="API-Zugang ausgeben (Token wird nur einmal angezeigt)")
def create_access(body: AccessIn, request: Request, actor: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    if not has(actor, "api.own"):
        raise HTTPException(403, "Keine Berechtigung für API-Zugänge")
    _need_session(actor)
    snap = snapshot()
    scope = _scope_from(body, actor, snap)
    active = sum(1 for r in db.scalars(select(ApiToken).where(ApiToken.user_id == actor.id)) if r.scope is not None
                 and _status(r) == "active")
    if active >= scopes.MAX_ACCESS_PER_USER:
        raise HTTPException(409, f"Höchstens {scopes.MAX_ACCESS_PER_USER} aktive API-Zugänge je Konto – bitte "
                                 "nicht mehr benötigte widerrufen.")
    token = scopes.TOKEN_PREFIX + new_token(32)
    now = utcnow()
    row = ApiToken(user_id=actor.id, name=body.name.strip(), purpose=body.purpose.strip(), token_hash=hash_token(token),
                   prefix=token[:10], created_at=now, expires_at=scopes.expires_at(body.expires_days), scope=scope,
                   ip_allow=_ip_list(body.ip_allow) or None, rate_limit=body.rate_limit)
    db.add(row)
    db.flush()
    audit(db, actor, "api_access.create", f"api_access:{row.id}",
          {"name": row.name, "areas": scope["areas"], "write": scope["write"],
           "filters": {k: len(v) for k, v in scope["filters"].items()}, "expires_days": body.expires_days},
          ip=client_ip(request))
    db.commit()
    out = access_dict(row, {actor.id: actor.display_name}, snap[1])
    out["token"] = token
    out["examples"] = _examples(token, scope)
    return out


@router.get("/api-access/{access_id}", summary="Ein API-Zugang mit den letzten Aufrufen")
def get_access(access_id: int, actor: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_any(actor)
    row = _get_access(db, actor, access_id)
    out = access_dict(row, _owners(db, [row]), snapshot()[1])
    logs = db.scalars(select(ApiTokenLog).where(ApiTokenLog.token_id == row.id).order_by(ApiTokenLog.id.desc()).limit(50))
    out["log"] = [{"at": iso(x.at), "method": x.method, "path": x.path, "area": x.area, "outcome": x.outcome,
                   "ip": x.ip} for x in logs]
    out["log_total"] = db.scalar(select(func.count(ApiTokenLog.id)).where(ApiTokenLog.token_id == row.id)) or 0
    return out


@router.delete("/api-access/{access_id}", summary="API-Zugang widerrufen")
def revoke_access(access_id: int, request: Request, actor: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    _need_any(actor)
    row = _get_access(db, actor, access_id)
    if row.revoked_at is None:
        row.revoked_at = utcnow()
        audit(db, actor, "api_access.revoke", f"api_access:{row.id}",
              {"name": row.name, "owner_id": row.user_id}, ip=client_ip(request))
        db.commit()
    return {"ok": True, "id": row.id, "status": _status(row)}
