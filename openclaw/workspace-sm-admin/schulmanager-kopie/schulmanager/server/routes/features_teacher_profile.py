"""Lehrer-Selbstverwaltung (ARCHITECTURE.md §9.3).

Lehrkräfte (Recht ``profile.teacher_self``, Konto mit ``teacher_id``) pflegen Fächer, Wunschklassen, Deputat,
Arbeitszeitfenster und weiche Wünsche. Je nach ``settings.teacher_self_service``:

* ``"approval"`` – Änderung wird als Antrag gespeichert (ein offener Antrag je Lehrkraft, erneutes Absenden
  aktualisiert ihn); Planung/Schulleitung (``teacher_requests.review``) genehmigt oder lehnt ab (mit Kommentar).
* ``"direct"`` – Änderung wird sofort übernommen (protokolliert als genehmigter Antrag mit ``auto: true``).

Nicht vorhandene Fächer kann die Lehrkraft als ``new_subjects`` vorschlagen; solche Änderungen gehen **immer**
als Antrag an die Planung (auch im Modus ``direct``) und legen das Fach erst bei der Genehmigung an
(Prüfende brauchen zusätzlich ``masterdata.edit``).

Übernahme über ``store.mutate`` (neue Version, Audit, Event); Zeitfenster werden dabei in Sperrzeiten
(``Teacher.unavailable``, Notiz „Zeitfenster …“) umgerechnet. Jede Antwort enthält die **Konflikte** der Änderung
(Stunden außerhalb der Zeitfenster, nicht mehr angegebene Fächer, Deputat über/unter Ist). Freitexte werden nur
verschlüsselt gespeichert und nie protokolliert.
"""
from __future__ import annotations

from datetime import date as date_type
from typing import Annotated, Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager.models import School
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user, require
from schulmanager.teacher_profile import (ProfileError, apply_profile, availability_from_rules, conflicts, current_load,
                                          describe_availability, describe_exception, diff_profile,
                                          exception_impact, profile_rules, rules_from, teacher_profile,
                                          validate_exception, validate_profile)

from .features_common import has, mutate, new_id, snapshot, write_audit

router = APIRouter(tags=["Lehrer-Selbstverwaltung"])

STATUS_LABELS = {"offen": "offen", "genehmigt": "genehmigt", "abgelehnt": "abgelehnt",
                 "zurueckgezogen": "zurückgezogen"}
Short = Annotated[str, Field(min_length=1, max_length=40)]


# ----------------------------------------------------------------- Eingaben
class WeekPatternIn(BaseModel):
    """Älteres Muster „jede k. Woche ab Woche s (bis Woche e)“ (nur in Requests; wird zum Rhythmus)."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    every: int = Field(ge=1, le=53)
    from_: int = Field(alias="from", ge=1, le=53)
    to: Optional[int] = Field(None, ge=1, le=53)


class RhythmIn(BaseModel):
    """Rhythmus in laufenden Wochen (alle k Wochen ab Woche s; ``to_week`` 0 = offen)."""
    model_config = ConfigDict(extra="forbid")
    every: int = Field(ge=1, le=53)
    from_week: int = Field(ge=1, le=53)
    to_week: int = Field(0, ge=0, le=53)


Week = Annotated[int, Field(ge=1, le=53)]   # laufende Woche


class WindowIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: list[Annotated[int, Field(ge=0, le=6)]] = Field(min_length=1, max_length=7)
    start: str = Field(pattern=r"^\d{1,2}:\d{2}$")
    end: str = Field(pattern=r"^\d{1,2}:\d{2}$")
    weeks: list[Week] = Field(default_factory=list, max_length=53)
    rhythm: Optional[RhythmIn] = None
    week_pattern: Optional[WeekPatternIn] = None


class RuleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weeks: list[Week] = Field(default_factory=list, max_length=53)
    days: list[Annotated[int, Field(ge=0, le=6)]] = Field(default_factory=list, max_length=7)
    periods: list[Annotated[int, Field(ge=0, le=15)]] = Field(default_factory=list, max_length=16)
    note: str = Field("", max_length=200)
    rhythm: Optional[RhythmIn] = None
    week_pattern: Optional[WeekPatternIn] = None
    valid_from: str = Field("", max_length=10, description="gilt ab diesem Datum (ISO), leer = von Anfang an")


class NewSubjectIn(BaseModel):
    """Vorschlag für ein noch nicht vorhandenes Fach."""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=20, description="Kürzel")
    name: str = Field(min_length=1, max_length=80)
    room_type: Optional[str] = Field(None, max_length=40, description="Fachraum-Typ (leer = Klassenraum)")


class ProfileIn(BaseModel):
    """Profil (alle Felder optional – fehlende bleiben unverändert)."""
    model_config = ConfigDict(extra="forbid")
    subjects: Optional[list[Short]] = Field(None, max_length=20)
    new_subjects: Optional[list[NewSubjectIn]] = Field(None, max_length=5)
    preferred_classes: Optional[list[Short]] = Field(None, max_length=30)
    max_hours: Optional[int] = Field(None, ge=0, le=40)
    time_windows: Optional[list[WindowIn]] = Field(None, max_length=30)
    work_grid: Optional[dict] = Field(None, description="Arbeitszeiten-Raster: weeks (1-52) und blocked "
                                      "(Liste aus week, day, periods)")
    unavailable: Optional[list[RuleIn]] = Field(None, max_length=60, description="harte Sperrzeiten (Regeln mit "
                                                "Tagen, Stunden, Rhythmus und optional „gilt ab“)")
    wishes: Optional[list[RuleIn]] = Field(None, max_length=30)


class ProfileChangeIn(ProfileIn):
    note: str = Field("", max_length=2000, description="Begründung/Hinweis (wird verschlüsselt gespeichert)")


class ExceptionIn(BaseModel):
    """Einmalige Ausnahme: an diesem Tag (bzw. Zeitraum) in diesen Stunden nicht verfügbar."""
    model_config = ConfigDict(extra="forbid")
    date_from: date_type
    date_to: Optional[date_type] = None
    periods: list[Annotated[int, Field(ge=0, le=15)]] = Field(default_factory=list, max_length=16,
                                                                description="leer = ganzer Tag")
    reason: str = Field("", max_length=200, description="kurzer Anlass (z. B. Arzttermin)")
    note: str = Field("", max_length=2000, description="Begründung/Hinweis (wird verschlüsselt gespeichert)")


class ReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comment: str = Field("", max_length=2000)


# ----------------------------------------------------------------- Hilfen
def _model():
    from schulmanager.server.feature_models.teacher import TeacherChangeRequest
    return TeacherChangeRequest


def _crypto():
    try:
        from schulmanager.server import crypto
    except ImportError as exc:  # pragma: no cover - Basisdienst fehlt
        raise HTTPException(503, "Verschlüsselung ist nicht verfügbar") from exc
    return crypto


def _aad(row_id: int, field: str) -> str:
    return f"teacher_change_requests.{field}:{row_id}"


def _enc(text: str, row_id: int, field: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    return _crypto().encrypt_text(text, _aad(row_id, field))


def _dec(token: Optional[str], row_id: int, field: str) -> str:
    if not token:
        return ""
    try:
        return _crypto().decrypt_text(token, _aad(row_id, field))
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001 - beschädigt/falscher Schlüssel: nicht anzeigen, aber nicht abstürzen
        return "[nicht lesbar]"


def _mode(school: School) -> str:
    mode = getattr(school.settings, "teacher_self_service", "approval")
    return mode if mode in ("approval", "direct") else "approval"


def _own_teacher(user, school: School):
    tid = getattr(user, "teacher_id", None)
    if not tid:
        raise HTTPException(409, "Ihr Konto ist mit keiner Lehrkraft verknüpft – bitte die Schulverwaltung kontaktieren")
    teacher = school.index("teachers").get(tid)
    if teacher is None:
        raise HTTPException(409, f"Die verknüpfte Lehrkraft „{tid}“ existiert nicht (mehr)")
    return teacher


def _profile_data(body: ProfileIn) -> dict:
    data = body.model_dump(exclude_unset=True, exclude={"note"}, by_alias=True)
    return {k: v for k, v in data.items() if v is not None}


def _validate(school: School, data: dict, current: dict) -> dict:
    try:
        return validate_profile(school, data, current)
    except ProfileError as exc:
        raise HTTPException(422, "; ".join(exc.errors)) from None


def _days(school: School) -> list[int]:
    from schulmanager.calendar_utils import open_days
    return open_days(school)


def _users(db: Session, ids: set) -> dict[int, Any]:
    from schulmanager.server.db_models import User
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {u.id: u for u in db.scalars(select(User).where(User.id.in_(sorted(ids))))}


def _request_out(row, school: School, users: dict, *, with_note: bool = True) -> dict:
    teacher = school.index("teachers").get(row.teacher_id)
    kind = getattr(row, "kind", None) or "profil"
    current = teacher_profile(teacher) if teacher and kind == "profil" else None
    base = row.previous if row.status != "offen" else current
    author, reviewer = users.get(row.user_id), users.get(row.reviewer_id)
    exception = (row.payload or {}).get("exception") if kind == "ausnahme" else None
    return {
        "kind": kind, "exception": exception,
        "exception_text": describe_exception(exception, school.settings) if exception else "",
        "id": row.id, "teacher_id": row.teacher_id, "teacher_name": teacher.name if teacher else row.teacher_id,
        "user_id": row.user_id, "user_name": (author.display_name or author.username) if author else "",
        "status": row.status, "status_label": STATUS_LABELS.get(row.status, row.status), "auto": bool(row.auto),
        "payload": row.payload, "previous": row.previous, "current": current,
        "new_subjects": list((row.payload or {}).get("new_subjects") or []),
        "diff": diff_profile(base, row.payload, school.settings) if kind == "profil" else [],
        "note": _dec(row.note_enc, row.id, "note") if with_note else "",
        "review_comment": _dec(row.review_comment_enc, row.id, "review_comment") if with_note else "",
        "reviewer_id": row.reviewer_id,
        "reviewer_name": (reviewer.display_name or reviewer.username) if reviewer else "",
        "created_at": iso(row.created_at), "updated_at": iso(row.updated_at), "decided_at": iso(row.decided_at),
        "applied_version": row.applied_version,
    }


def _open_request(db: Session, teacher_id: str, kind: str = "profil"):
    R = _model()
    return db.scalar(select(R).where(R.teacher_id == teacher_id, R.status == "offen", R.kind == kind)
                     .order_by(R.id.desc()))


def _teacher_user_ids(db: Session, teacher_id: str) -> set[int]:
    from schulmanager.server.db_models import User
    return set(db.scalars(select(User.id).where(User.teacher_id == teacher_id, User.active.is_(True))))


def _publish(scope: list[str], data: dict, *, permission: Optional[str] = None,
             user_ids: Optional[set[int]] = None) -> None:
    try:
        from schulmanager.server.events import bus
        from schulmanager.server.store import get_store
        payload = {"version": get_store().version, "scope": scope, "dates": [], **data}
        bus.publish("change", payload, permission=permission, user_ids=user_ids)
    except Exception:  # pragma: no cover - Events dürfen nie stören
        pass


def _notify(db: Session, row, *, teacher: bool = True) -> None:
    """Live-Ereignis an Prüfende (Recht) und an die Konten der Lehrkraft (ohne Inhalte)."""
    data = {"request_id": row.id, "status": row.status, "teacher_id": row.teacher_id}
    _publish(["teacher_requests"], data, permission="teacher_requests.review")
    if teacher:
        ids = _teacher_user_ids(db, row.teacher_id)
        if row.user_id:
            ids.add(row.user_id)
        if ids:
            _publish(["teacher_requests", "teacher_profile"], data, user_ids=ids)
        from schulmanager.server import notification_hooks  # Glocke: Antrag genehmigt/abgelehnt
        notification_hooks.teacher_request_decided(row)


def _apply(user, school_teacher_id: str, profile: dict, message: str) -> int:
    from schulmanager.server.store import get_store

    def fn(school: School):
        try:
            apply_profile(school, school_teacher_id, profile)
        except KeyError:
            raise HTTPException(409, f"Lehrkraft „{school_teacher_id}“ existiert nicht (mehr)") from None
        return True

    mutate(user, message, fn, scope=["teachers", "subjects"] if profile.get("new_subjects") else ["teachers"])
    return get_store().version


def _preview(school: School, teacher, data: dict) -> dict:
    current = teacher_profile(teacher)
    profile = _validate(school, data, current)
    return {"teacher_id": teacher.id, "profile": profile, "diff": diff_profile(current, profile, school.settings),
            "conflicts": conflicts(school, teacher.id, profile),
            "availability": availability_from_rules(rules_from(profile["unavailable"], school.settings),
                                                    school.settings, _days(school)),
            "rules": profile["unavailable"], "description": describe_availability(profile)}


def _options(school: School) -> dict:
    st = school.settings
    return {"subjects": sorted(({"id": s.id, "name": s.name} for s in school.subjects), key=lambda x: x["id"]),
            "classes": sorted(({"id": c.id, "name": c.name, "grade": c.grade, "site": c.site}
                               for c in school.classes), key=lambda x: (x["grade"], x["id"])),
            "days": st.days, "periods": st.periods, "period_times": list(st.period_times[:st.periods]),
            "period_minutes": int(getattr(st, "period_minutes", 45) or 45), "school_days": _days(school)}


# ----------------------------------------------------------------- eigenes Profil
@router.get("/me/teacher-profile")
def my_profile(user: AuthUser = Depends(require("profile.teacher_self")), db: Session = Depends(get_db)):
    """Eigenes Lehrkraft-Profil inkl. Ist-Deputat, Verfügbarkeit, Antragsstatus und Konflikten."""
    R = _model()
    school = snapshot()[1]
    teacher = _own_teacher(user, school)
    profile = teacher_profile(teacher)
    rows = db.scalars(select(R).where(R.teacher_id == teacher.id).order_by(R.id.desc()).limit(20)).all()
    users = _users(db, {r.user_id for r in rows} | {r.reviewer_id for r in rows})
    pending = next((r for r in rows if r.status == "offen" and r.kind == "profil"), None)
    return {"teacher_id": teacher.id, "name": teacher.name, "mode": _mode(school), "profile": profile,
            "description": describe_availability(profile),
            "load": current_load(school, teacher.id),
            "availability": availability_from_rules(rules_from(profile["unavailable"], school.settings),
                                                    school.settings, _days(school)),
            "conflicts": conflicts(school, teacher.id, profile),
            "pending": _request_out(pending, school, users) if pending else None,
            "requests": [_request_out(r, school, users) for r in rows if r.kind == "profil"],
            "exceptions": [_request_out(r, school, users) for r in rows if r.kind == "ausnahme"],
            "can_edit_times": may_edit_times(school, teacher),
            "options": _options(school)}


def may_edit_times(school, teacher) -> bool:
    """Arbeitszeiten selbst festlegen: nur mit Freigabe der Schule (allgemein oder für diese Lehrkraft)."""
    return bool(getattr(school.settings, "teacher_times_self", False) or getattr(teacher, "times_self", False))


@router.post("/me/teacher-profile/preview")
def my_profile_preview(body: ProfileIn, user: AuthUser = Depends(require("profile.teacher_self"))):
    """Vorschau einer Änderung (Konflikte, verfügbare Stunden, erzeugte Sperrzeiten) – speichert nichts."""
    school = snapshot()[1]
    return _preview(school, _own_teacher(user, school), _profile_data(body))


@router.put("/me/teacher-profile")
def change_my_profile(body: ProfileChangeIn, user: AuthUser = Depends(require("profile.teacher_self")),
                      db: Session = Depends(get_db)):
    """Änderung beantragen (``approval``) bzw. sofort übernehmen (``direct``)."""
    R = _model()
    school = snapshot()[1]
    teacher = _own_teacher(user, school)
    current = teacher_profile(teacher)
    profile = _validate(school, _profile_data(body), current)
    changed = diff_profile(current, profile, school.settings)
    if not changed:
        raise HTTPException(422, "Es wurden keine Änderungen gegenüber dem aktuellen Profil angegeben")
    found = conflicts(school, teacher.id, profile)
    fields = [d["field"] for d in changed]
    # Sperrzeiten/Arbeitszeiten ändern Lehrkräfte ohne Freigabe nur als Antrag (Genehmigung durch die Planung), nie direkt
    times_need_review = bool({"unavailable", "time_windows", "work_grid"} & set(fields)) and not may_edit_times(
        school, teacher)
    now = utcnow()
    pending = _open_request(db, teacher.id)
    # neue Fächer legt erst die Planung an → immer als Antrag, auch im Modus „direct“
    if _mode(school) == "approval" or profile.get("new_subjects") or times_need_review:
        if pending is not None:
            row = pending
            row.payload, row.previous, row.updated_at, row.user_id = profile, current, now, user.id or None
            action = "teacher_request.update"
        else:
            row = R(teacher_id=teacher.id, user_id=user.id or None, payload=profile, previous=current,
                    status="offen", auto=False, note_enc="", review_comment_enc="", created_at=now)
            db.add(row)
            db.flush()
            action = "teacher_request.create"
        row.note_enc = _enc(body.note, row.id, "note")
        write_audit(db, user, action, f"teacher_request:{row.id}", {"teacher_id": teacher.id, "fields": fields})
        db.commit()
        _notify(db, row, teacher=False)
        users = _users(db, {row.user_id})
        return {"status": "pending", "mode": "approval", "request": _request_out(row, school, users),
                "conflicts": found, "reason": "mode" if _mode(school) == "approval" else
                "new_subjects" if profile.get("new_subjects") else "times"}
    # direkt übernehmen
    version = _apply(user, teacher.id, profile, f"Lehrkraft {teacher.id}: Profil selbst geändert "
                                                f"({', '.join(fields)})")
    if pending is not None:
        pending.status, pending.decided_at = "zurueckgezogen", now
    row = R(teacher_id=teacher.id, user_id=user.id or None, payload=profile, previous=current, status="genehmigt",
            auto=True, note_enc="", review_comment_enc="", applied_version=version, created_at=now, decided_at=now)
    db.add(row)
    db.flush()
    row.note_enc = _enc(body.note, row.id, "note")
    write_audit(db, user, "teacher_profile.update", f"teacher:{teacher.id}",
                {"teacher_id": teacher.id, "fields": fields, "request_id": row.id, "version": version})
    db.commit()
    _notify(db, row)
    users = _users(db, {row.user_id})
    return {"status": "applied", "mode": "direct", "request": _request_out(row, snapshot()[1], users),
            "conflicts": found, "version": version}


@router.delete("/me/teacher-profile/request")
def withdraw_my_request(user: AuthUser = Depends(require("profile.teacher_self")), db: Session = Depends(get_db)):
    """Eigenen offenen Antrag zurückziehen."""
    school = snapshot()[1]
    teacher = _own_teacher(user, school)
    row = _open_request(db, teacher.id)
    if row is None:
        raise HTTPException(404, "Es gibt keinen offenen Antrag")
    row.status, row.decided_at = "zurueckgezogen", utcnow()
    write_audit(db, user, "teacher_request.withdraw", f"teacher_request:{row.id}", {"teacher_id": teacher.id})
    db.commit()
    _notify(db, row)
    return _request_out(row, school, _users(db, {row.user_id}))


# ----------------------------------------------------------------- einmalige Ausnahme (Antrag)
@router.post("/me/teacher-requests/exception")
def request_exception(body: ExceptionIn, user: AuthUser = Depends(require("profile.teacher_self")),
                      db: Session = Depends(get_db)):
    """Einmalige Ausnahme beantragen (z. B. „Do 15.10. ab der 5. Stunde nicht da“). Geht immer als Antrag an die
    Prüfenden (Recht ``teacher_requests.review``); bei Genehmigung entsteht eine Abwesenheit für die Vertretung."""
    R = _model()
    school = snapshot()[1]
    teacher = _own_teacher(user, school)
    try:
        ex = validate_exception(school, {"date": body.date_from, "date_to": body.date_to, "periods": body.periods,
                                         "reason": body.reason})
    except ProfileError as exc:
        raise HTTPException(422, "; ".join(exc.errors)) from None
    for other in db.scalars(select(R).where(R.teacher_id == teacher.id, R.status == "offen", R.kind == "ausnahme")):
        if (other.payload or {}).get("exception") == ex:
            raise HTTPException(409, "Diese Ausnahme ist bereits beantragt")
    now = utcnow()
    row = R(teacher_id=teacher.id, user_id=user.id or None, kind="ausnahme", payload={"exception": ex},
            previous=None, status="offen", auto=False, note_enc="", review_comment_enc="", created_at=now)
    db.add(row)
    db.flush()
    row.note_enc = _enc(body.note, row.id, "note")
    write_audit(db, user, "teacher_request.create", f"teacher_request:{row.id}",
                {"teacher_id": teacher.id, "kind": "ausnahme", "date": ex["date"]})
    db.commit()
    _notify(db, row, teacher=False)
    return {"status": "pending", "request": _request_out(row, school, _users(db, {row.user_id})),
            "impact": exception_impact(school, teacher.id, ex)}


@router.delete("/me/teacher-requests/{request_id}")
def withdraw_my_exception(request_id: int, user: AuthUser = Depends(require("profile.teacher_self")),
                          db: Session = Depends(get_db)):
    """Eigenen offenen Ausnahme-Antrag zurückziehen."""
    school = snapshot()[1]
    teacher = _own_teacher(user, school)
    row = db.get(_model(), request_id)
    if row is None or row.teacher_id != teacher.id or row.kind != "ausnahme":
        raise HTTPException(404, "Antrag nicht gefunden")
    if row.status != "offen":
        raise HTTPException(409, f"Der Antrag ist nicht mehr offen ({STATUS_LABELS.get(row.status, row.status)})")
    row.status, row.decided_at = "zurueckgezogen", utcnow()
    write_audit(db, user, "teacher_request.withdraw", f"teacher_request:{row.id}", {"teacher_id": teacher.id})
    db.commit()
    _notify(db, row)
    return _request_out(row, school, _users(db, {row.user_id}))


# ----------------------------------------------------------------- Prüfung (Planung/Schulleitung)
@router.get("/teacher-requests/summary")
def requests_summary(user: AuthUser = Depends(require("teacher_requests.review")), db: Session = Depends(get_db)):
    """Anzahl offener Anträge (Dashboard-Widget) und die drei neuesten."""
    R = _model()
    school = snapshot()[1]
    n = db.scalar(select(func.count(R.id)).where(R.status == "offen")) or 0
    latest = db.scalars(select(R).where(R.status == "offen").order_by(R.created_at.desc()).limit(3)).all()
    teachers = school.index("teachers")
    return {"open": int(n), "latest": [{"id": r.id, "teacher_id": r.teacher_id,
                                        "teacher_name": teachers[r.teacher_id].name if r.teacher_id in teachers
                                        else r.teacher_id, "created_at": iso(r.created_at)} for r in latest]}


@router.get("/teacher-requests")
def list_requests(status: Literal["offen", "genehmigt", "abgelehnt", "zurueckgezogen", "alle"] = "offen",
                  teacher_id: Optional[str] = Query(None, max_length=40), limit: int = Query(100, ge=1, le=500),
                  user: AuthUser = Depends(require("teacher_requests.review")), db: Session = Depends(get_db)):
    """Anträge von Lehrkräften (Standard: offene) inkl. Vergleich alt/neu und – bei offenen – Konflikten."""
    R = _model()
    school = snapshot()[1]
    q = select(R)
    if status != "alle":
        q = q.where(R.status == status)
    if teacher_id:
        q = q.where(R.teacher_id == teacher_id)
    rows = db.scalars(q.order_by(R.created_at.desc(), R.id.desc()).limit(limit)).all()
    users = _users(db, {r.user_id for r in rows} | {r.reviewer_id for r in rows})
    out = []
    for r in rows:
        item = _request_out(r, school, users)
        if r.status == "offen" and r.teacher_id in school.index("teachers"):
            if r.kind == "ausnahme":
                item["impact"] = exception_impact(school, r.teacher_id, r.payload["exception"])
                item["conflicts"] = {"count": item["impact"]["count"]}
            else:
                item["conflicts"] = conflicts(school, r.teacher_id, r.payload)
        out.append(item)
    return out


def _get_request(db: Session, request_id: int):
    row = db.get(_model(), request_id)
    if row is None:
        raise HTTPException(404, "Antrag nicht gefunden")
    return row


@router.get("/teacher-requests/{request_id}")
def get_request(request_id: int, user: AuthUser = Depends(require("teacher_requests.review")),
                db: Session = Depends(get_db)):
    school = snapshot()[1]
    row = _get_request(db, request_id)
    item = _request_out(row, school, _users(db, {row.user_id, row.reviewer_id}))
    if row.kind == "ausnahme":
        if row.teacher_id in school.index("teachers"):
            item["impact"] = exception_impact(school, row.teacher_id, row.payload["exception"])
            item["load"] = current_load(school, row.teacher_id)
        return item
    if row.teacher_id in school.index("teachers"):
        item["conflicts"] = conflicts(school, row.teacher_id, row.payload)
        item["availability"] = availability_from_rules(profile_rules(school.index("teachers")[row.teacher_id],
                                                                     row.payload, school.settings),
                                                       school.settings, _days(school))
        item["rules"] = row.payload.get("unavailable")
        item["load"] = current_load(school, row.teacher_id)
    return item


@router.post("/teacher-requests/{request_id}/approve")
def approve_request(request_id: int, body: Optional[ReviewIn] = None,
                    user: AuthUser = Depends(require("teacher_requests.review")), db: Session = Depends(get_db)):
    """Genehmigt einen Antrag und übernimmt das Profil (Zeitfenster → Sperrzeiten)."""
    body = body or ReviewIn()
    row = _get_request(db, request_id)
    if row.status != "offen":
        raise HTTPException(409, f"Der Antrag ist nicht mehr offen ({STATUS_LABELS.get(row.status, row.status)})")
    school = snapshot()[1]
    teacher = school.index("teachers").get(row.teacher_id)
    if teacher is None:
        raise HTTPException(409, f"Lehrkraft „{row.teacher_id}“ existiert nicht (mehr)")
    if row.kind == "ausnahme":
        return _approve_exception(row, teacher, school, body, user, db)
    from schulmanager.legacy import migrate_profile_payload
    payload = migrate_profile_payload(row.payload or {})
    try:
        profile = validate_profile(school, payload, teacher_profile(teacher))
    except ProfileError as exc:
        raise HTTPException(409, {"message": "Der Antrag passt nicht mehr zu den Stammdaten",
                                  "conflicts": exc.errors}) from None
    new_subjects = [n["id"] for n in profile.get("new_subjects") or []]
    if new_subjects and not has(user, "masterdata.edit"):
        raise HTTPException(403, "Neue Fächer anlegen erfordert das Recht „Stammdaten bearbeiten“")
    found = conflicts(school, row.teacher_id, profile)
    fields = [d["field"] for d in diff_profile(teacher_profile(teacher), profile, school.settings)]
    extra = f", neue Fächer: {', '.join(new_subjects)}" if new_subjects else ""
    version = _apply(user, row.teacher_id, profile,
                     f"Lehrkraft {row.teacher_id}: Profiländerung genehmigt (Antrag {row.id}{extra})")
    row.status, row.reviewer_id, row.decided_at = "genehmigt", user.id or None, utcnow()
    row.applied_version, row.previous = version, teacher_profile(teacher)
    row.review_comment_enc = _enc(body.comment, row.id, "review_comment")
    write_audit(db, user, "teacher_request.approve", f"teacher_request:{row.id}",
                {"teacher_id": row.teacher_id, "fields": fields, "version": version, "new_subjects": new_subjects})
    db.commit()
    _notify(db, row)
    return {"request": _request_out(row, snapshot()[1], _users(db, {row.user_id, row.reviewer_id})),
            "conflicts": found, "version": version}


def _approve_exception(row, teacher, school: School, body: ReviewIn, user: AuthUser, db: Session) -> dict:
    """Genehmigung einer einmaligen Ausnahme: legt eine Abwesenheit der Lehrkraft an (Vertretungsfall)."""
    from schulmanager.models import Absence
    from schulmanager.server.routes.features_substitutions import _absence_dates, _validate_absence
    from schulmanager.server.store import get_store

    ex = row.payload["exception"]
    reason = ex.get("reason") or "Ausnahme beantragt"
    created: dict[str, Any] = {}

    def fn(sch: School):
        for a in sch.absences:      # schon erfasst (z. B. Krankmeldung): nicht doppelt anlegen
            if (a.kind, a.ref, a.date_from, a.date_to, sorted(a.periods)) == (
                    "teacher", teacher.id, ex["date"], ex["date_to"], sorted(ex["periods"])):
                created["id"] = a.id
                return {"id": a.id, "duplicate": True}
        a = Absence(id=new_id([x.id for x in sch.absences], "A"), kind="teacher", ref=teacher.id,
                    date_from=ex["date"], date_to=ex["date_to"], periods=sorted(ex["periods"]), reason=reason)
        _validate_absence(sch, a)
        sch.absences.append(a)
        created["id"] = a.id
        return {"id": a.id}

    probe = Absence(id="x", kind="teacher", ref=teacher.id, date_from=ex["date"], date_to=ex["date_to"],
                    periods=ex["periods"])
    mutate(user, f"Lehrkraft {teacher.id}: Ausnahme genehmigt (Antrag {row.id}, {ex['date']})", fn,
           scope=["absences", "substitutions"], dates=_absence_dates(probe))
    row.status, row.reviewer_id, row.decided_at = "genehmigt", user.id or None, utcnow()
    row.applied_version = get_store().version
    row.review_comment_enc = _enc(body.comment, row.id, "review_comment")
    write_audit(db, user, "teacher_request.approve", f"teacher_request:{row.id}",
                {"teacher_id": row.teacher_id, "kind": "ausnahme", "absence": created.get("id"),
                 "version": row.applied_version})
    db.commit()
    _notify(db, row)
    return {"request": _request_out(row, snapshot()[1], _users(db, {row.user_id, row.reviewer_id})),
            "impact": exception_impact(snapshot()[1], row.teacher_id, ex), "absence": created.get("id"),
            "version": row.applied_version}


@router.post("/teacher-requests/{request_id}/reject")
def reject_request(request_id: int, body: Optional[ReviewIn] = None,
                   user: AuthUser = Depends(require("teacher_requests.review")), db: Session = Depends(get_db)):
    """Lehnt einen Antrag ab (Kommentar an die Lehrkraft, verschlüsselt gespeichert)."""
    body = body or ReviewIn()
    row = _get_request(db, request_id)
    if row.status != "offen":
        raise HTTPException(409, f"Der Antrag ist nicht mehr offen ({STATUS_LABELS.get(row.status, row.status)})")
    row.status, row.reviewer_id, row.decided_at = "abgelehnt", user.id or None, utcnow()
    row.review_comment_enc = _enc(body.comment, row.id, "review_comment")
    write_audit(db, user, "teacher_request.reject", f"teacher_request:{row.id}", {"teacher_id": row.teacher_id})
    db.commit()
    _notify(db, row)
    return {"request": _request_out(row, snapshot()[1], _users(db, {row.user_id, row.reviewer_id}))}


@router.post("/teacher-profiles/{teacher_id}/preview")
def teacher_preview(teacher_id: str, body: ProfileIn, user: AuthUser = Depends(current_user)):
    """Vorschau für den Stammdaten-Editor (Planung) bzw. die eigene Lehrkraft."""
    own = has(user, "profile.teacher_self") and getattr(user, "teacher_id", None) == teacher_id
    if not (own or has(user, "masterdata.edit") or has(user, "teacher_requests.review")):
        raise HTTPException(403, "Keine Berechtigung")
    school = snapshot()[1]
    teacher = school.index("teachers").get(teacher_id)
    if teacher is None:
        raise HTTPException(404, f"Lehrkraft {teacher_id} nicht gefunden")
    return _preview(school, teacher, _profile_data(body))


# ----------------------------------------------------------------- DSGVO-Auskunft (für /me/export)
def export_requests(db: Session, teacher_id: Optional[str], user_id: Optional[int]) -> list[dict]:
    """Eigene Anträge (entschlüsselt) für den Datenexport des Kontos."""
    R = _model()
    if not teacher_id and not user_id:
        return []
    conds = []
    if teacher_id:
        conds.append(R.teacher_id == teacher_id)
    if user_id:
        conds.append(R.user_id == user_id)
    from sqlalchemy import or_
    rows = db.scalars(select(R).where(or_(*conds)).order_by(R.id)).all()
    return [{"id": r.id, "teacher_id": r.teacher_id, "status": r.status, "auto": bool(r.auto), "payload": r.payload,
             "previous": r.previous, "note": _dec(r.note_enc, r.id, "note"),
             "review_comment": _dec(r.review_comment_enc, r.id, "review_comment"),
             "created_at": iso(r.created_at), "decided_at": iso(r.decided_at)} for r in rows]
