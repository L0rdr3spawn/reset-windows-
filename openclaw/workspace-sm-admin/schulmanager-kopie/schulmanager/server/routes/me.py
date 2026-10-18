"""Eigenes Konto: DSGVO-Datenexport, persönlicher iCal-Link."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import retention
from ..accounts import session_dict, token_dict, user_dict
from ..audit import audit, audit_dict
from ..config import config
from ..db import get_db, iso
from ..db_models import Announcement, ApiToken, AuditLog, LoginAttempt, User, UserSession
from ..deps import AuthUser, client_ip, current_user
from ..security import hash_token, new_token
from ..store import get_store

router = APIRouter(prefix="/me", tags=["Eigenes Konto"])


def ical_url(token: str) -> str:
    return f"{config.base_url}/ical/{token}.ics"


@router.get("/ical-url")
def get_ical_url(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Status des persönlichen Kalender-Feeds. Der Link selbst wird nur einmal beim Erzeugen angezeigt
    (in der Datenbank liegt nur ein Hash, S-09) – ``url`` ist hier immer ``null``."""
    row = db.get(User, user.id)
    assert row is not None
    return {"url": None, "active": bool(row.ical_token)}


@router.post("/ical-url")
def reset_ical_url(request: Request, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Erzeugt einen neuen Kalender-Link (der alte wird ungültig) und zeigt ihn einmalig an."""
    row = db.get(User, user.id)
    assert row is not None
    token = new_token(24)
    row.ical_token = hash_token(token)
    audit(db, user, "user.ical_reset", f"user:{row.id}", ip=client_ip(request))
    db.commit()
    return {"url": ical_url(token), "active": True}


@router.delete("/ical-url")
def delete_ical_url(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Deaktiviert den Kalender-Link."""
    row = db.get(User, user.id)
    assert row is not None
    row.ical_token = None
    db.commit()
    return {"ok": True}


def _row(obj) -> dict:
    out = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.key)
        out[col.key] = iso(value) if isinstance(value, datetime) else value
    return out


def build_export(db: Session, row: User, auth: AuthUser, *, session_id: int | None = None) -> dict:
    """Vollständige Auskunft (Art. 15/20) zu einem Konto aus Sicht ``auth`` (= die Person selbst, Rechte wie in der
    Oberfläche). Konto, Protokolle und Stammdaten stehen hier, alle Fachdaten liefern die im Löschkonzept
    angemeldeten Datenarten (:mod:`schulmanager.server.retention`) – neue Module klinken sich dort ein."""
    school = get_store().school
    data: dict = {
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "account": user_dict(db, row),
        "permissions": sorted(auth.permissions),
        "two_factor_enabled": bool(row.totp_enabled),
        "ical_link_active": bool(row.ical_token),
        "sessions": [session_dict(s, session_id) for s in
                     db.scalars(select(UserSession).where(UserSession.user_id == row.id))],
        "api_tokens": [token_dict(t) for t in db.scalars(select(ApiToken).where(ApiToken.user_id == row.id))],
        "login_attempts": [{"created_at": iso(a.created_at), "ip": a.ip, "success": a.success} for a in
                           db.scalars(select(LoginAttempt).where(LoginAttempt.username == row.username)
                                      .order_by(LoginAttempt.id.desc()).limit(1000))],
        "audit_log": [audit_dict(a) for a in
                      db.scalars(select(AuditLog).where(or_(AuditLog.user_id == row.id,
                                                            AuditLog.target == f"user:{row.id}"))
                                 .order_by(AuditLog.id.desc()).limit(5000))],
        "announcements_authored": [_row(a) for a in
                                   db.scalars(select(Announcement).where(Announcement.author_id == row.id))],
    }
    student_ids = list(auth.student_ids)
    students = school.index("students")
    data["students"] = [students[s].to_dict() for s in student_ids if s in students]
    if row.teacher_id:
        teacher = school.index("teachers").get(row.teacher_id)
        data["teacher"] = teacher.to_dict() if teacher else None
    if row.teacher_id or row.role == "lehrer":
        try:  # Lehrer-Selbstverwaltung: eigene Profil-Anträge (Freitexte entschlüsselt)
            from .features_teacher_profile import export_requests
            data["teacher_change_requests"] = export_requests(db, row.teacher_id, row.id)
        except Exception:  # noqa: BLE001 - Export darf daran nicht scheitern
            data["teacher_change_requests"] = None
    try:  # Konten & Anmeldung (§11): Kontaktdaten (Nummer entschlüsselt) und verbundene Anbieter-Konten
        from .. import identities
        from .features_contact import _contact, _email_verified, _phone_of, _phone_verified
        contact = _contact(db, row.id)
        data["contact"] = {"email": row.email, "email_verified": _email_verified(row, contact),
                           "phone": _phone_of(contact), "phone_verified": _phone_verified(contact)}
        data["identities"] = [identities.public_identity(r) for r in identities.identity_rows(db, row.id)]
    except Exception:  # noqa: BLE001 - Export darf daran nicht scheitern
        data.setdefault("contact", None)
        data.setdefault("identities", None)
    # Fachdaten: Krankmeldungen, Dokumente, Formulare, Postfach, Chats (Metadaten), Noten, Notenbuch, Lernstand,
    # Abgaben, Klassenbuch, Benachrichtigungen, Dateien … – je Datenart im Löschkonzept angemeldet
    data.update(retention.collect_export(db, retention.Subject(user=auth, row=row)))
    return data


@router.get("/export")
def export_my_data(request: Request, format: str = Query("json", pattern="^(json|zip)$"),
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    """DSGVO Art. 15/20: alle gespeicherten Daten zum eigenen Konto als JSON-Datei (``?format=zip``: mit lesbarer
    Übersicht). Eltern erhalten zusätzlich die Daten ihrer Kinder, soweit ``parent_access`` es erlaubt."""
    row = db.get(User, user.id)
    assert row is not None
    data = build_export(db, row, user, session_id=user.session_id)
    audit(db, user, "user.export", f"user:{row.id}", ip=client_ip(request))
    db.commit()
    if format == "zip":
        body = retention.export_zip(data, f"Meine Daten – {row.display_name or row.username}")
        return Response(body, media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="meine-daten-{row.username}.zip"'})
    body = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(body, media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="meine-daten-{row.username}.json"'})
