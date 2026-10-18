"""Dateien: verschlüsselter Upload/Download (Basisdienst, ARCHITECTURE.md §9.2).

* ``POST /files`` – ``multipart/form-data`` mit ``file`` (+ ``purpose`` als Feld oder ``?purpose=``) → 201
  ``{id, filename, size, content_type, kind, …}``. Fehler: 413 ``file_too_large``/``quota_exceeded``,
  415 ``unsupported_type``/``blocked_type``, 422 ``virus_found``/``empty_file``, 503 ``scan_failed``
  (``detail = {"code", "message"}``).
* ``GET /files/{id}`` (``?inline=1`` nur für PDF/Bilder außer SVG) – Eigentümer oder registrierter Access-Check des
  ``ref_type``; sonst 404. Abrufe fremder Dateien werden protokolliert (``file.download``, je Tag einmal).
* ``GET /files/{id}/meta``, ``DELETE /files/{id}`` (nur Eigentümer, nur nicht angehängte Dateien),
  ``GET /files`` (eigene Dateien), ``GET /files/limits`` (Limits, Kontingent, erlaubte Typen).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .. import files
from ..db import get_db
from ..deps import AuthUser, client_ip, current_user
from ..events import bus

router = APIRouter(tags=["Dateien"])


def _publish(user: AuthUser) -> None:
    """Live-Hinweis an die eigenen Sitzungen (z. B. Dateilisten in anderen Tabs)."""
    bus.publish("change", {"version": None, "scope": ["files"], "dates": []}, user_ids={user.id})


def _need_upload_right(user: AuthUser) -> None:
    if not files.may_upload(user):
        raise HTTPException(403, "Keine Berechtigung zum Hochladen von Dateien")


@router.get("/files/limits")
def file_limits(purpose: Optional[str] = Query(None, max_length=40), user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Größenlimit, Kontingent (belegt/gesamt), erlaubte Dateiarten (für ``accept`` und Vorabprüfung)."""
    info = files.limits_info(db, user, purpose)
    info["can_upload"] = files.may_upload(user)
    return info


@router.get("/files")
def my_files(purpose: Optional[str] = Query(None, max_length=40), unattached: bool = False,
             limit: int = Query(100, ge=1, le=500), user: AuthUser = Depends(current_user),
             db: Session = Depends(get_db)) -> list[dict]:
    """Eigene Dateien (neueste zuerst), optional nur nicht angehängte bzw. eines Zwecks."""
    return [files.file_info(m, user) for m in files.list_own(db, user, purpose=purpose, unattached=unattached,
                                                             limit=limit)]


@router.post("/files", status_code=201)
async def upload_file(request: Request, user: AuthUser = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    """Datei hochladen (gestreamt, geprüft, verschlüsselt). Nicht angehängte Uploads verfallen nach 24 h."""
    _need_upload_right(user)
    meta = await files.store_upload(request, db, user)
    await run_in_threadpool(db.commit)
    info = await run_in_threadpool(files.file_info, meta, user)
    _publish(user)
    return info


@router.get("/files/{file_id}/meta")
def file_meta(file_id: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    meta = files.require_readable(db, user, file_id)
    return files.file_info(meta, user)


@router.get("/files/{file_id}")
def download_file(file_id: str, request: Request, inline: bool = False, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> Response:
    """Inhalt (entschlüsselt) mit sicheren Headern; ``?inline=1`` zeigt PDF/Bilder im Browser an."""
    meta = files.require_readable(db, user, file_id)
    response = files.stream_response(meta, inline)
    if files.audit_download(db, user, meta, client_ip(request)):
        db.commit()
    return response


@router.delete("/files/{file_id}")
def delete_file(file_id: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eigene, noch nicht angehängte Datei löschen (angehängte bitte im jeweiligen Bereich entfernen)."""
    meta = files.require_readable(db, user, file_id)
    if meta.owner_user_id != user.id:
        raise HTTPException(403, "Nur die hochladende Person kann diese Datei löschen")
    if meta.attached:
        raise files.FileError(409, "attached", "Die Datei ist angehängt – bitte dort entfernen, wo sie verwendet wird.")
    files.delete(db, meta.id, user, hard=True)
    db.commit()
    _publish(user)
    return {"deleted": file_id}
