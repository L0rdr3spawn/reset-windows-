"""Datenschutz-Verwaltung: Löschkonzept (Art. 5, 17 DSGVO) und Auskunft (Art. 15, 20) – ``docs/DATENSCHUTZ-LOESCHKONZEPT.md``.

* ``GET  /privacy/overview`` – Datenarten mit Fristen, Warteliste-Zähler, letzte Läufe (`privacy.manage`).
* ``PUT  /privacy/settings`` – Fristen/Schalter ändern (`privacy.manage`, Audit ``privacy.settings``).
* ``GET  /privacy/leavers`` – Warteliste „ausgetreten“ mit Fälligkeiten; ``POST /privacy/leavers/{id}/cancel`` nimmt
  einen Austritt zurück (Person steht wieder im Planungsdokument).
* ``GET  /privacy/preview`` – „Was würde gelöscht“ (nur Zahlen; ``?student_id=``).
* ``POST /privacy/run`` – Löschlauf sofort ausführen (fällige Datenarten; `privacy.manage`).
* ``GET  /privacy/log`` – Löschprotokoll (Datenart, Anzahl, Zeitpunkt, ohne Inhalte).
* ``GET  /privacy/erase/preview`` + ``POST /privacy/erase`` – Sofort-Löschen einer Person (Art. 17), nur `privacy.subject`,
  mit Bestätigung (ID bzw. Benutzername eintippen) und Audit.
* ``GET  /privacy/export`` bzw. ``GET /users/{id}/export`` – Auskunft für eine Person als ZIP (`daten.json` +
  `uebersicht.html`), nur `privacy.subject`, Audit ``privacy.export``.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager.server import retention
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import User
from schulmanager.server.deps import AuthUser, build_auth_user, client_ip, current_user
from schulmanager.server.feature_models.retention import RetentionLeaver, RetentionLog

from .features_common import need

router = APIRouter(tags=["Datenschutz"])


class KindIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: Optional[int] = Field(None, ge=0, le=3650)
    age_days: Optional[int] = Field(None, ge=0, le=3650)


class SettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grace_days: Optional[int] = Field(None, ge=0, le=3650)
    auto_purge: Optional[bool] = None
    audit_days: Optional[int] = Field(None, ge=0, le=3650)
    log_days: Optional[int] = Field(None, ge=0, le=3650)
    kinds: dict[str, KindIn] = Field(default_factory=dict)


class EraseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: Optional[str] = Field(None, max_length=40)
    user_id: Optional[int] = None
    confirm: str = Field(max_length=120)
    reason: str = Field("", max_length=200)


@router.get("/privacy/overview")
def overview(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    settings = retention.get_settings(db)
    waiting = int(db.scalar(select(func.count()).select_from(RetentionLeaver)
                            .where(RetentionLeaver.status == "wartend")) or 0)
    last = db.scalar(select(RetentionLog.at).order_by(RetentionLog.id.desc()).limit(1))
    return {"settings": settings, "categories": retention.CATEGORIES, "waiting": waiting, "last_log_at": iso(last),
            "can_subject": "privacy.subject" in user.permissions}


@router.put("/privacy/settings")
def save_settings(body: SettingsIn, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    changes = body.model_dump(exclude_unset=True)
    changes["kinds"] = {k: v for k, v in changes.get("kinds", {}).items()}
    changed = retention.save_settings(db, changes, user.username)
    if changed:
        audit(db, user, "privacy.settings", "retention", {"geaendert": changed}, ip=client_ip(request))
    db.commit()
    return retention.get_settings(db)


@router.get("/privacy/leavers")
def leavers(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    now = utcnow()
    stored = retention._load_settings(db)
    kinds = [k for k in retention.kinds() if k.purge_fn is not None]
    out = []
    for row in db.scalars(select(RetentionLeaver).order_by(RetentionLeaver.left_at.desc())).all():
        purged = set(row.purged or [])
        due = [retention._due_at(row, retention.days_after_exit(db, k, stored)) for k in kinds if k.key not in purged]
        last_due = max(due) if due else None
        out.append({"student_id": row.student_id, "name": retention.leaver_name(row), "class_id": row.class_id,
                    "status": row.status, "source": row.source, "left_at": iso(row.left_at),
                    "done_at": iso(row.done_at), "purged": sorted(purged), "open": len(kinds) - len(purged),
                    "last_due_at": iso(last_due), "days_left": None if last_due is None else
                    max(0, (last_due - now).days)})
    return {"leavers": out, "grace_days": retention.grace_days(db, stored)}


@router.post("/privacy/leavers/{student_id}/cancel")
def cancel_leaver(student_id: str, request: Request, user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    try:
        ok = retention.cancel_leaver(db, student_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if not ok:
        raise HTTPException(404, "Kein offener Austritt für diese Person")
    audit(db, user, "privacy.leaver_cancel", f"student:{student_id}", ip=client_ip(request))
    db.commit()
    return {"ok": True}


@router.get("/privacy/preview")
def preview(student_id: Optional[str] = Query(None, max_length=40), user: AuthUser = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    result = retention.preview(db, student_id=student_id)
    db.rollback()                                   # reine Vorschau
    return result


@router.post("/privacy/run")
def run_now(request: Request, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    db.rollback()
    result = retention.run()
    audit(db, user, "privacy.run", "retention", {k: v for k, v in result.items() if v}, ip=client_ip(request))
    db.commit()
    return result


@router.get("/privacy/log")
def log_entries(limit: int = Query(200, ge=1, le=1000), user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.manage")
    kinds = {k.key: k.label for k in retention.kinds()}
    kinds.update({"audit": "Audit-Protokoll", "person": "Person abgeschlossen"})
    rows = db.scalars(select(RetentionLog).order_by(RetentionLog.id.desc()).limit(limit)).all()
    return {"entries": [{"id": r.id, "at": iso(r.at), "kind": r.kind, "label": kinds.get(r.kind, r.kind),
                         "action": r.action, "mode": r.mode, "subject": r.subject, "count": r.count,
                         "actor": r.actor, "note": r.note} for r in rows]}


def _target(db: Session, student_id: Optional[str], user_id: Optional[int]) -> tuple[Optional[str], Optional[User]]:
    """Person eindeutig bestimmen: Schüler/in (``student_id``) oder Konto (``user_id``)."""
    if bool(student_id) == bool(user_id):
        raise HTTPException(422, "Entweder student_id oder user_id angeben")
    if user_id:
        row = db.get(User, user_id)
        if row is None:
            raise HTTPException(404, "Konto nicht gefunden")
        if row.role == "schueler" and row.student_id:
            return row.student_id, row
        return None, row
    return student_id, None


@router.get("/privacy/erase/preview")
def erase_preview(student_id: Optional[str] = Query(None, max_length=40), user_id: Optional[int] = Query(None),
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "privacy.subject")
    sid, row = _target(db, student_id, user_id)
    items = []
    if sid:
        ctx = retention.PurgeContext(student_ids=[sid], user_ids=retention._student_users(db, sid), dry_run=True)
        names = retention._history_names({sid}).get(sid)
        from schulmanager.server.store import get_store
        doc = get_store().school.index("students")
        label = doc[sid].name if sid in doc else (names[0] if names else "")
        ctx.names = [label] if label else []
    else:
        ctx = retention.PurgeContext(user_ids=[row.id], dry_run=True)       # type: ignore[union-attr]
        label = (row.display_name or row.username) if row else ""
    for k in retention.kinds():
        if k.purge_fn is None or (not sid and k.key in retention._STUDENT_ONLY):
            continue
        with db.begin_nested():
            n = int(k.purge_fn(db, ctx) or 0)
        items.append({"kind": k.key, "label": k.label, "count": n, "how": k.how})
    db.rollback()
    return {"student_id": sid, "user_id": row.id if row else None, "name": label,
            "confirm_with": sid or (row.username if row else ""), "items": items,
            "total": sum(i["count"] for i in items)}


@router.post("/privacy/erase")
def erase(body: EraseIn, request: Request, user: AuthUser = Depends(current_user),
          db: Session = Depends(get_db)) -> dict:
    """Sofort-Löschen (Art. 17): unwiderruflich. Bestätigung: ID bzw. Benutzername exakt eintippen."""
    need(user, "privacy.subject")
    sid, row = _target(db, body.student_id, body.user_id)
    expected = sid or (row.username if row else "")
    if (body.confirm or "").strip() != expected:
        raise HTTPException(422, "Die Bestätigung stimmt nicht mit der Person überein.")
    if row is not None and (row.id == user.id or row.role == "admin"):
        raise HTTPException(409, "Dieses Konto kann hier nicht gelöscht werden (eigenes Konto oder Administration).")
    if sid:
        result = retention.erase_student(db, sid, user, reason=body.reason, ip=client_ip(request))
    else:
        result = retention.erase_user(db, row.id, user, reason=body.reason)           # type: ignore[union-attr]
    db.commit()
    return result


def _export_for(db: Session, user: AuthUser, request: Request, student_id: Optional[str],
                user_id: Optional[int]) -> Response:
    need(user, "privacy.subject")
    sid, row = _target(db, student_id, user_id)
    if row is None:
        row = db.scalar(select(User).where(User.student_id == sid, User.role == "schueler").order_by(User.id))
        if row is None:
            raise HTTPException(404, "Zu dieser Person gibt es kein Konto. Daten ohne Konto: Auskunft manuell aus "
                                     "der Schülerakte erstellen.")
    from .me import build_export
    auth = build_auth_user(db, row)
    data = build_export(db, row, auth)
    audit(db, user, "privacy.export", f"user:{row.id}", {"fuer": row.username}, ip=client_ip(request))
    db.commit()
    body = retention.export_zip(data, f"Auskunft nach Art. 15 DSGVO – {row.display_name or row.username}")
    return Response(body, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="auskunft-{row.username}.zip"'})


@router.get("/privacy/export")
def export_person(request: Request, student_id: Optional[str] = Query(None, max_length=40),
                  user_id: Optional[int] = Query(None), user: AuthUser = Depends(current_user),
                  db: Session = Depends(get_db)) -> Response:
    return _export_for(db, user, request, student_id, user_id)


@router.get("/users/{user_id}/export")
def export_user(user_id: int, request: Request, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> Response:
    return _export_for(db, user, request, None, user_id)
