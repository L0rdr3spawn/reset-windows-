"""Systemverwaltung (nur ``system.admin``): Systeminfo, Sicherungen, Demo-Schule, Wartung."""
from __future__ import annotations

import platform
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import runtime
from ..audit import audit
from ..backups import backup_path, create_backup, delete_backup, list_backups
from ..config import APP_VERSION, config
from ..db import get_db, utcnow
from ..db_models import SchoolVersion, User, UserSession
from ..deps import AuthUser, client_ip, require
from ..events import bus
from ..store import get_store

router = APIRouter(prefix="/admin", tags=["System"])


class DemoBody(BaseModel):
    time_limit: float | None = Field(default=None, gt=0, le=600)
    accounts: bool = True
    classes_per_grade: int = Field(default=14, ge=1, le=23)


@router.get("/system")
def system_info(_user: AuthUser = Depends(require("system.admin")), db: Session = Depends(get_db)) -> dict:
    """Version, Datenbank, Anzahl Konten/Versionen, Laufzeit."""
    from .. import migrate

    store = get_store()
    by_role = {r: n for r, n in db.execute(select(User.role, func.count(User.id)).group_by(User.role)).all()}
    try:
        revision = migrate.current_revision()
    except Exception:  # noqa: BLE001
        revision = None
    return {
        "version": APP_VERSION,
        "python": platform.python_version(),
        "db": config.db_kind,
        "db_revision": revision,
        "users": sum(by_role.values()),
        "users_by_role": by_role,
        "active_sessions": db.scalar(select(func.count(UserSession.id)).where(UserSession.expires_at > utcnow())),
        "versions": db.scalar(select(func.count(SchoolVersion.id))),
        "plan_version": store.version,
        "plan_updated_at": store.info()["updated_at"],
        "school_name": store.school.settings.school_name,
        "counts": {"classes": len(store.school.classes), "teachers": len(store.school.teachers),
                   "students": len(store.school.students), "lessons": len(store.school.lessons)},
        "uptime_seconds": round(time.time() - runtime.started_at, 1),
        "sse_clients": bus.client_count,
        "backups": len(list_backups()),
        "config": config.public_dict(),
    }


@router.get("/backups")
def backups(_user: AuthUser = Depends(require("system.admin"))) -> list[dict]:
    return list_backups()


@router.post("/backups", status_code=201)
def make_backup(request: Request, user: AuthUser = Depends(require("system.admin"))) -> dict:
    """Erstellt sofort eine Sicherung (SQLite-Datei bzw. JSON-Export)."""
    return create_backup(user, client_ip(request))


@router.get("/backups/{name}")
def download_backup(name: str, _user: AuthUser = Depends(require("system.admin"))) -> FileResponse:
    path = backup_path(name)
    if path is None:
        raise HTTPException(404, "Sicherung nicht gefunden")
    media = "application/vnd.sqlite3" if name.endswith(".db") else "application/gzip"
    return FileResponse(path, media_type=media, filename=name)


@router.delete("/backups/{name}")
def remove_backup(name: str, request: Request, user: AuthUser = Depends(require("system.admin")),
                  db: Session = Depends(get_db)) -> dict:
    if not delete_backup(name):
        raise HTTPException(404, "Sicherung nicht gefunden")
    audit(db, user, "system.backup_delete", name, ip=client_ip(request))
    db.commit()
    return {"ok": True}


@router.get("/status")
def status(_user: AuthUser = Depends(require("system.admin"))) -> dict:
    """Status-Seite: Version, Datenbankstand, Speicher, Mail, letzte Sicherung, Wartungslauf, Prüfliste."""
    from .. import ops

    return ops.status_report()


@router.get("/errors")
def errors(limit: int = 100, offset: int = 0, level: str | None = None,
           _user: AuthUser = Depends(require("system.admin"))) -> dict:
    """Fehlerprotokoll (ERROR/CRITICAL, 30 Tage bzw. 1000 Einträge)."""
    from .. import ops

    ops.flush_error_log(0.5)
    return ops.list_errors(min(max(limit, 1), 500), max(offset, 0), level)


@router.delete("/errors")
def clear_errors(request: Request, user: AuthUser = Depends(require("system.admin")),
                 db: Session = Depends(get_db)) -> dict:
    from .. import ops

    removed = ops.clear_errors()
    audit(db, user, "system.errors_clear", "error_log", {"removed": removed}, ip=client_ip(request))
    db.commit()
    return {"removed": removed}


@router.post("/backups/{name}/verify")
def verify_backup_route(name: str, user: AuthUser = Depends(require("system.admin"))) -> dict:
    """Test-Restore: Sicherung in eine Wegwerf-Kopie einspielen und prüfen (Live-Daten bleiben unberührt)."""
    from .. import ops

    try:
        return ops.verify_backup(name)
    except FileNotFoundError:
        raise HTTPException(404, "Sicherung nicht gefunden") from None


@router.post("/demo")
def load_demo_school(request: Request, body: DemoBody | None = None,
                     user: AuthUser = Depends(require("system.admin"))) -> dict:
    """Lädt die Demo-Schule (ersetzt das Planungsdokument als neue Version, Undo möglich) und legt Demo-Konten an.

    Läuft synchron (Dauer ≈ ``time_limit``, Default ``SM_GENERATE_TIME_LIMIT``); Fortschritt als ``job``-Events
    (``id: "demo"``).
    """
    from ..audit import audit_now
    from ..demo_loader import load_demo

    if config.is_production_mode:
        raise HTTPException(404, "Demo-Funktionen sind im Echtbetrieb (SM_MODE=production) abgeschaltet")
    body = body or DemoBody()
    result = load_demo(user, body.time_limit, body.accounts, body.classes_per_grade)
    audit_now(user, "system.demo", f"version:{result['version']}",
              {"accounts": [a["username"] for a in result["accounts"]]}, ip=client_ip(request))
    return result


@router.post("/maintenance")
def maintenance(_user: AuthUser = Depends(require("system.admin"))) -> dict:
    """Wartungslauf sofort ausführen (abgelaufene Sitzungen/Tokens, alte Login-Versuche)."""
    from ..maintenance import run_maintenance

    return {"deleted": run_maintenance()}
