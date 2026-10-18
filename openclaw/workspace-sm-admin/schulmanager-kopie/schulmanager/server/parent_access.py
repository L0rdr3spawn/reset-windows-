"""Elternzugriff (A-44) – wiederverwendbarer Baustein für alle Bereiche.

Regel: Eltern sehen alles, was ihr Kind sieht, solange es **minderjährig** ist. Volljährige Schüler/innen legen je
Bereich fest, ob ihre Eltern ihn sehen dürfen (Tabelle ``parent_access``, ohne Eintrag: nein).

Volljährigkeit (:func:`is_adult`): aus ``Student.birth_date`` (Planungsdokument, ISO-Datum) – ist es nicht gepflegt,
zählt das Konto-Merkmal ``users.adult`` (Schülerkonto).

Nutzung in einem Feature (Bereichsschlüssel aus :data:`AREAS`)::

    from schulmanager.server import parent_access
    if not parent_access.parent_may_see(db, student_id, "krankmeldungen"):
        raise HTTPException(404, ...)

Im Profil erscheinen nur :data:`ACTIVE_AREAS` (Bereiche, die die Einwilligung schon prüfen) – ein Feature, das umstellt,
nimmt seinen Schlüssel dort auf. Einstellungen ändern nur die volljährigen Schüler/innen selbst (Routen ``routes/features_parent_access.py``:
``GET/PUT /parent-access``); jede Änderung wird protokolliert (``parent_access.update``, ohne Inhalte).
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Mapping, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import utcnow
from .db_models import User
from .feature_models.parent_access import ParentAccess, StudentPrefs

ADULT_AGE = 18
AREA_CHANNELS = "kursraeume"
AREA_SICK_NOTES = "krankmeldungen"
AREA_DOCUMENTS = "dokumente"
AREA_TIMETABLE = "stundenplan"
AREA_GRADES = "noten"
AREA_ANNOUNCEMENTS = "mitteilungen"
AREA_COMPETENCIES = "kompetenzen"
AREAS: dict[str, str] = {
    AREA_CHANNELS: "Kursräume (freigegebenes Material, Aufgaben, Rückmeldungen)",
    AREA_SICK_NOTES: "Krankmeldungen und Fehlzeiten",
    AREA_DOCUMENTS: "Eingereichte Dokumente und Atteste",
    AREA_TIMETABLE: "Mein persönlicher Stundenplan und Vertretungen",
    AREA_GRADES: "Noten (Klassenarbeiten, Tests, bewertete Aufgaben)",
    AREA_ANNOUNCEMENTS: "Mitteilungen der Schule an meine Klasse (Aushänge, Newsletter)",
    AREA_COMPETENCIES: "Lernstand (Kompetenzen, Lernplan, Abzeichen)",
}
# Bereiche, deren Feature die Einwilligung schon prüft: nur diese zeigt das Profil, nur diese lassen sich einstellen
# (ein Schalter ohne Wirkung täuscht Schutz vor). Stellt ein Bereich auf :func:`parent_may_see` um, kommt er hierher.
ACTIVE_AREAS: tuple[str, ...] = (AREA_CHANNELS, AREA_TIMETABLE, AREA_SICK_NOTES, AREA_DOCUMENTS, AREA_ANNOUNCEMENTS,
                                 AREA_GRADES, AREA_COMPETENCIES)
# „Fehlzeiten“ (Übersicht je Fach, Prozent) gehören zu ``krankmeldungen``; Hausaufgaben zu ``kursraeume``.
# Rundschreiben im Postfach steuert nicht ein Bereich, sondern die Zustellung (:data:`DELIVERY`).
DELIVERY: dict[str, str] = {"self": "Nur an mich", "parents": "Nur an meine Eltern",
                            "both": "An mich und an meine Eltern"}
DEFAULT_DELIVERY = "self"   # volljährig ohne Wahl: die Person selbst (Eltern nur auf ihren Wunsch)


def _school(school: Any = None) -> Any:
    if school is not None:
        return school
    from .store import get_store

    return get_store().school


def _birth_date(school: Any, student_id: str) -> Optional[date]:
    st = school.index("students").get(student_id) if school is not None else None
    raw = getattr(st, "birth_date", None) if st is not None else None
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def age_on(birth: date, day: date) -> int:
    """Alter in vollen Jahren am ``day`` (29.02. zählt im Nicht-Schaltjahr ab 01.03.)."""
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def is_adult(db: Session, student_id: str, *, school: Any = None, today: Optional[date] = None) -> bool:
    """Volljährig? Geburtsdatum (Planungsdokument) vor dem Konto-Merkmal ``users.adult``."""
    birth = _birth_date(_school(school), student_id)
    if birth is not None:
        return age_on(birth, today or date.today()) >= ADULT_AGE
    flags = db.scalars(select(User.adult).where(User.student_id == student_id, User.role == "schueler"))
    return any(bool(f) for f in flags)


def _check_area(area: str) -> str:
    if area not in AREAS:
        raise ValueError(f"Unbekannter Bereich {area!r} (erlaubt: {', '.join(AREAS)})")
    return area


def allowed_areas(db: Session, student_id: str) -> dict[str, bool]:
    """Gespeicherte Einstellungen einer/eines Schüler/in (alle Bereiche, ohne Eintrag ``False``)."""
    out = dict.fromkeys(AREAS, False)
    for area, allowed in db.execute(select(ParentAccess.area, ParentAccess.allowed)
                                    .where(ParentAccess.student_id == student_id)):
        if area in out:
            out[area] = bool(allowed)
    return out


def parent_may_see(db: Session, student_id: str, area: str, *, school: Any = None,
                   today: Optional[date] = None) -> bool:
    """Dürfen die Eltern den Bereich ``area`` dieses Kindes sehen? Minderjährig → immer ja; volljährig → nur mit
    Einwilligung (``parent_access``). Die Prüfung, ob das Konto überhaupt Elternteil dieses Kindes ist, macht der
    Aufrufer (``AuthUser.student_ids``)."""
    _check_area(area)
    if not student_id:
        return False
    if not is_adult(db, student_id, school=school, today=today):
        return True
    allowed = db.scalar(select(ParentAccess.allowed).where(ParentAccess.student_id == student_id,
                                                           ParentAccess.area == area))
    return bool(allowed)


def visible_children(db: Session, student_ids: Iterable[str], area: str, *, school: Any = None,
                     today: Optional[date] = None) -> list[str]:
    """Die Kinder aus ``student_ids``, deren Bereich ``area`` die Eltern sehen dürfen (Reihenfolge bleibt)."""
    school = _school(school)
    return [sid for sid in dict.fromkeys(student_ids)
            if parent_may_see(db, sid, area, school=school, today=today)]


def set_areas(db: Session, student_id: str, changes: Mapping[str, bool], user: Any) -> dict[str, bool]:
    """Speichert Einwilligungen (ohne Commit, ohne Rechteprüfung) und liefert die tatsächlich geänderten Bereiche."""
    changed: dict[str, bool] = {}
    rows = {r.area: r for r in db.scalars(select(ParentAccess).where(ParentAccess.student_id == student_id))}
    for area, value in changes.items():
        _check_area(area)
        row = rows.get(area)
        if row is None:
            if not value:
                continue
            db.add(ParentAccess(student_id=student_id, area=area, allowed=True, set_by=getattr(user, "id", None),
                                updated_at=utcnow()))
            changed[area] = True
        elif bool(row.allowed) != bool(value):
            row.allowed = bool(value)
            row.set_by = getattr(user, "id", None)
            row.updated_at = utcnow()
            changed[area] = bool(value)
    return changed


# --------------------------------------------------------------------------- Zustellung und Entscheidung
def delivery_of(db: Session, student_id: str, *, school: Any = None, today: Optional[date] = None) -> str:
    """Wohin gehen Rundschreiben der Schule? Minderjährig immer ``both``; volljährig die gespeicherte Wahl."""
    if not is_adult(db, student_id, school=school, today=today):
        return "both"
    value = db.scalar(select(StudentPrefs.delivery).where(StudentPrefs.student_id == student_id))
    return value if value in DELIVERY else DEFAULT_DELIVERY


def delivery_routing(db: Session, *, school: Any = None, today: Optional[date] = None) -> dict[str, str]:
    """``{schüler_id: "self"|"parents"}`` für alle volljährigen Schüler/innen, deren Rundschreiben nicht an beide gehen
    (für die Gruppenauflösung im Postfach). Wer fehlt, bekommt beides."""
    school = _school(school)
    if school is None:
        return {}
    chosen = dict(db.execute(select(StudentPrefs.student_id, StudentPrefs.delivery)).all())
    flagged = {sid for sid in db.scalars(select(User.student_id).where(User.role == "schueler", User.adult.is_(True)))
               if sid}
    day = today or date.today()
    out: dict[str, str] = {}
    for st in school.students:
        birth = _birth_date(school, st.id)
        adult = age_on(birth, day) >= ADULT_AGE if birth is not None else st.id in flagged
        if not adult:
            continue
        value = chosen.get(st.id)
        value = value if value in DELIVERY else DEFAULT_DELIVERY
        if value != "both":
            out[st.id] = value
    return out


def set_delivery(db: Session, student_id: str, value: str) -> bool:
    """Speichert die Zustellung (ohne Commit); ``True`` bei Änderung."""
    if value not in DELIVERY:
        raise ValueError(f"Unbekannte Zustellung {value!r}")
    row = db.get(StudentPrefs, student_id)
    if row is None:
        db.add(StudentPrefs(student_id=student_id, delivery=value, updated_at=utcnow()))
        db.flush()
        return value != DEFAULT_DELIVERY
    changed = row.delivery != value
    row.delivery = value
    row.updated_at = utcnow()
    return changed


def mark_decided(db: Session, student_id: str) -> None:
    row = db.get(StudentPrefs, student_id)
    if row is None:
        row = StudentPrefs(student_id=student_id, delivery=DEFAULT_DELIVERY, updated_at=utcnow())
        db.add(row)
        db.flush()
    if row.decided_at is None:
        row.decided_at = utcnow()


def decision_pending(db: Session, student_id: str, *, school: Any = None, today: Optional[date] = None) -> bool:
    """Volljährig, aber die Freigaben wurden noch nie bewusst gespeichert (→ Hinweis in der Oberfläche)."""
    if not is_adult(db, student_id, school=school, today=today):
        return False
    return db.scalar(select(StudentPrefs.decided_at).where(StudentPrefs.student_id == student_id)) is None


def effective_adult(db: Session, user: User) -> bool:
    """Gilt das Konto als volljährig? Schüler: Geburtsdatum vor Konto-Merkmal (``is_adult``); sonst das Merkmal."""
    if user.role == "schueler" and user.student_id:
        try:
            return is_adult(db, user.student_id)
        except Exception:  # noqa: BLE001 - ohne geladenen Plan zählt das Konto-Merkmal
            return bool(user.adult)
    return bool(user.adult)
