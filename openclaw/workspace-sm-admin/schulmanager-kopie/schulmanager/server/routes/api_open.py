"""Öffentliche, versionierte API für Apps und KI-Werkzeuge: ``/api/v1/open/…`` (docs/API-ZUGAENGE.md).

Jede Route hängt über ``Depends(open_access("<bereich>"))`` an einem Bereich (``api_scopes.AREAS``); Zugänge mit
Umfang (Token ``sma_…``) erreichen nur diese Routen. Die Handler benutzen die bestehenden Funktionen mit dem Konto des
Zugangs – es gelten also Rechte und Datenumfang des Kontos – und beschneiden das Ergebnis zusätzlich auf die Filter des
Zugangs. Gesundheits-/Förderdaten gibt keine dieser Routen aus.

Neue Funktion für Apps/KIs? Bereich in ``api_scopes.AREAS`` festlegen, hier die Route mit ``open_access`` anbinden,
Beschreibung (``summary``/``description``/Beispiel) schreiben – ``/llms.txt`` und ``/api/v1/meta/openapi.json``
übernehmen sie automatisch.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from schulmanager.server.api_scopes import Access, open_access, strip_private
from schulmanager.server.db import get_db

from .features_common import (check_range, has, parse_date, plan_class_ids, range_plans, reads_all_plans, snapshot)

router = APIRouter(prefix="/open", tags=["Öffentliche API"])

Kind = Literal["class", "teacher", "room", "student"]
_DENIED = "Nicht im Umfang dieses Zugangs."


def _example(data: Any, description: str = "Erfolg") -> dict:
    return {200: {"description": description, "content": {"application/json": {"example": data}}}}


# ------------------------------------------------------------------------------------ Hilfen
def _site_of(snap, kind: str, ref: str) -> Optional[set[str]]:
    """Standort(e) eines Plans (``None`` = keine Angabe → nicht einschränkbar)."""
    school = snap[1]
    if kind == "class":
        c = school.index("classes").get(ref)
        return {c.site} if c and c.site else None
    if kind == "student":
        st = school.index("students").get(ref)
        c = school.index("classes").get(st.class_id) if st else None
        return {c.site} if c and c.site else None
    if kind == "room":
        r = school.index("rooms").get(ref)
        return {r.site} if r and r.site else None
    t = school.index("teachers").get(ref)
    return set(t.sites) if t and t.sites else None


def _check_plan(acc: Access, kind: str, ref: str, snap) -> None:
    f = acc.filters
    if acc.scoped and kind == "room" and "rooms" not in (acc.scope.get("areas") or []):
        raise HTTPException(403, "Raumpläne gehören zum Bereich „Räume“, den dieser Zugang nicht umfasst.")
    if not f.plan_allowed(kind, ref):
        raise HTTPException(403, _DENIED)
    if f.sites:
        sites = _site_of(snap, kind, ref)
        if sites is not None and not (sites & f.sites):
            raise HTTPException(403, _DENIED)


def _day_out(acc: Access, plan: dict, snap) -> dict:
    """Vertretungsplan eines Tages im Umfang des Zugangs (ohne Abwesenheitslisten, Warnungen, Gründe, Aufsichten)."""
    entries = [e for e in plan.get("entries") or [] if acc.filters.entry_allowed(e, snap)]
    out = {k: v for k, v in plan.items() if not k.startswith("absent") and k not in
           ("warnings", "absences", "overrides", "stats", "entries")}
    counts: dict[str, int] = {}
    for e in entries:
        counts[e.get("kind") or "?"] = counts.get(e.get("kind") or "?", 0) + 1
    out["entries"] = entries
    out["stats"] = counts
    return strip_private(out)


# ---------------------------------------------------------------------------------- Stundenplan
@router.get("/timetable/{kind}/{ref}", summary="Stundenplan einer Klasse, Lehrkraft, eines Raums oder Schülers",
            description="Wochenraster (Zellen je Tag und Stunde) für die Woche, in der `date` liegt (Standard: "
                        "diese Woche). `kind`: `class`, `teacher`, `room` (zusätzlich Bereich „Räume“) oder "
                        "`student`. Kürzel/IDs siehe `/open/classes`, `/open/teachers`, `/open/rooms`. Vertretungen "
                        "und Entfall sind bereits eingerechnet.",
            responses=_example({"kind": "class", "ref": "5a", "cells": [{"day": 0, "start": 0, "subject": "Mathematik",
                                                                         "teacher": "MUS", "room": "R101"}]}))
def timetable(kind: Kind, ref: str, date_: Optional[str] = Query(None, alias="date", description="Ein Tag der Woche, JJJJ-MM-TT"),
              all_days: bool = Query(True, description="Auch Samstag/Sonntag"),
              acc: Access = Depends(open_access("timetable"))) -> Any:
    from .features_timetable import view
    snap = snapshot()
    _check_plan(acc, kind, ref, snap)
    return strip_private(view(kind, ref, week=None, week_no=None, date_=date_, all_days=all_days, user=acc.user))


# ------------------------------------------------------------------------------------ Vertretung
@router.get("/substitutions", summary="Vertretungsplan eines Tages",
            description="Vertretung, Entfall, Raumänderung und Klausuren des Tages `date` (Standard: heute) – ohne "
                        "Abwesenheitsgründe, Aufsichten und interne Warnungen. Mit Filtern des Zugangs "
                        "(Klassen/Lehrkräfte/Räume/Standorte) beschnitten.",
            responses=_example({"date": "2026-10-12", "entries": [{"kind": "vertretung", "period": 2,
                                                                    "classes": ["5a"], "teacher": "MUS",
                                                                    "substitute": "ABC", "room": "R101"}],
                                "stats": {"vertretung": 1}}))
def substitutions_day(date_: Optional[str] = Query(None, alias="date", description="JJJJ-MM-TT, Standard heute"),
                      acc: Access = Depends(open_access("substitutions"))) -> Any:
    if not has(acc.user, "substitution.read"):
        raise HTTPException(403, "Keine Berechtigung")
    from .features_substitutions import substitutions
    snap = snapshot()
    day = parse_date(date_)
    plan = substitutions(date_=day.isoformat(), site=None, class_id=None, teacher=None, public=True, user=acc.user)
    return _day_out(acc, plan, snap)


@router.get("/substitutions/range", summary="Vertretungspläne für einen Zeitraum",
            description="Liste von Tagesplänen von `from` bis `to` (höchstens 31 Tage; Standard: 7 Tage ab `from`).")
def substitutions_range(date_from: Optional[str] = Query(None, alias="from"),
                        date_to: Optional[str] = Query(None, alias="to"),
                        acc: Access = Depends(open_access("substitutions"))) -> Any:
    if not has(acc.user, "substitution.read"):
        raise HTTPException(403, "Keine Berechtigung")
    from .features_substitutions import substitutions
    d1 = parse_date(date_from, name="from")
    d2 = parse_date(date_to, d1 + timedelta(days=6), name="to")
    check_range(d1, d2, 31)
    snap = snapshot()
    out = []
    for p in range_plans(d1, d2, snap):
        day = p.get("date") or ""
        plan = substitutions(date_=day, site=None, class_id=None, teacher=None, public=True, user=acc.user)
        out.append(_day_out(acc, plan, snap))
    return out


# ------------------------------------------------------------------------------------- Kalender
@router.get("/calendar/school-year", summary="Schuljahr: Wochen, Ferien, Feiertage",
            description="Wochenübersicht des Schuljahres um `date` (Ferien, Feiertage, Unterrichtswochen). "
                        "Optional für eine Klasse (`class_id`, muss im Umfang des Zugangs liegen).")
def calendar_school_year(date_: Optional[str] = Query(None, alias="date"),
                         class_id: Optional[str] = Query(None, max_length=64),
                         acc: Access = Depends(open_access("calendar"))) -> Any:
    from .features_calendar import school_year
    if class_id and not acc.filters.plan_allowed("class", class_id):
        raise HTTPException(403, _DENIED)
    return strip_private(school_year(date_=date_, class_id=class_id, user=acc.user))


_EXAM_KEYS = ("id", "date", "start", "length", "title", "label", "subject", "subjects", "classes", "teachers", "time",
              "room", "room_lesson", "kind")


@router.get("/calendar/week", summary="Kalenderwoche mit Stunden, Terminen und Klausuren",
            description="Pro Tag: Stunden (mit Vertretung/Entfall), Schultermine und Klausuren für eine Klasse, "
                        "Lehrkraft, einen Raum oder Schüler. Ohne Fehlzeiten, Hausaufgaben und Nachschreibtermine.")
def calendar_week(kind: Kind = Query(...), ref: str = Query(..., max_length=64),
                  date_: Optional[str] = Query(None, alias="date"),
                  acc: Access = Depends(open_access("calendar")), db: Session = Depends(get_db)) -> Any:
    from .features_calendar import calendar_week as week
    snap = snapshot()
    _check_plan(acc, kind, ref, snap)
    data = week(kind, ref, date_, acc.user, db)
    for d in data.get("days") or []:
        d.pop("attendance", None)
        d.pop("homework", None)
        d["exams"] = [{k: e[k] for k in _EXAM_KEYS if k in e} for e in d.get("exams") or []
                      if e.get("kind") != "nachschreiben"]
    return strip_private(data)


# ------------------------------------------------------------------------------- Räume, Verzeichnis
@router.get("/rooms", summary="Liste der Räume", description="Räume mit Standort, Art und Kapazität. Belegung: "
            "`/open/timetable/room/{id}`.",
            responses=_example([{"id": "R101", "name": "Raum 101", "type": "Klassenraum", "site": "", "capacity": 30}]))
def rooms(acc: Access = Depends(open_access("rooms"))) -> Any:
    if not (has(acc.user, "rooms.read") or has(acc.user, "timetable.edit") or reads_all_plans(acc.user)):
        raise HTTPException(403, "Raumlisten sehen nur Konten mit dem Recht „Raumpläne lesen“.")
    snap = snapshot()
    f = acc.filters
    return [{"id": r.id, "name": r.name, "type": r.type, "site": r.site, "capacity": r.capacity}
            for r in snap[1].rooms if (not f.rooms or r.id in f.rooms) and (not f.sites or not r.site or r.site in f.sites)]


@router.get("/classes", summary="Liste der Klassen",
            description="Klassen (Kürzel, Name, Stufe, Standort), soweit das Konto sie sehen darf und der Zugang sie "
                        "umfasst.", responses=_example([{"id": "5a", "name": "5a", "grade": 5, "site": ""}]))
def classes(acc: Access = Depends(open_access("directory"))) -> Any:
    snap = snapshot()
    f = acc.filters
    visible = plan_class_ids(acc.user, snap)
    return [{"id": c.id, "name": c.name, "grade": c.grade, "site": c.site} for c in snap[1].classes
            if (visible is None or c.id in visible) and (not f.classes or c.id in f.classes)
            and (not f.sites or not c.site or c.site in f.sites)]


@router.get("/teachers", summary="Liste der Lehrkräfte (Kürzel und Name)",
            description="Kürzel und Name – ohne Kontaktdaten, Stundenzahlen oder Wünsche. Ohne Recht auf alle Pläne "
                        "nur die eigene Lehrkraft.", responses=_example([{"id": "MUS", "name": "Frau Muster"}]))
def teachers(acc: Access = Depends(open_access("directory"))) -> Any:
    snap = snapshot()
    f = acc.filters
    everyone = reads_all_plans(acc.user) or has(acc.user, "masterdata.read") or has(acc.user, "timetable.edit")
    tid = getattr(acc.user, "teacher_id", None)
    return [{"id": t.id, "name": t.name} for t in snap[1].teachers
            if (everyone or t.id == tid) and (not f.teachers or t.id in f.teachers)
            and (not f.sites or not t.sites or set(t.sites) & f.sites)]


@router.get("/sites", summary="Liste der Standorte", description="Standorte der Schule (Kürzel, Name).",
            responses=_example([{"id": "haupt", "name": "Hauptgebäude"}]))
def sites(acc: Access = Depends(open_access("directory"))) -> Any:
    snap = snapshot()
    f = acc.filters
    return [{"id": s.id, "name": s.name} for s in snap[1].sites if not f.sites or s.id in f.sites]


# -------------------------------------------------------------------------------- Mitteilungen
_ANN_KEYS = ("id", "title", "body", "audience", "class_ids", "site", "valid_from", "valid_to", "pinned", "priority",
             "created_at")


@router.get("/announcements", summary="Aktuelle Mitteilungen",
            description="Gültige Mitteilungen (schwarzes Brett) für alle bzw. bestimmte Klassen am Tag `date` "
                        "(Standard: heute) – ohne Autor/in und ohne reine Kollegiums-Mitteilungen.",
            responses=_example([{"id": 1, "title": "Elternabend", "body": "Am Donnerstag …", "audience": "all",
                                 "class_ids": [], "valid_to": "2026-10-20", "priority": "normal"}]))
def announcements(date_: Optional[str] = Query(None, alias="date"),
                  acc: Access = Depends(open_access("announcements")), db: Session = Depends(get_db)) -> Any:
    from .features_announcements import visible_announcements
    snap = snapshot()
    f = acc.filters
    rows = visible_announcements(db, acc.user, parse_date(date_), snap)
    out = []
    for a in rows:
        if a.get("audience") not in ("all", "classes"):
            continue
        if f.classes and a["audience"] == "classes" and not set(a.get("class_ids") or []) & f.classes:
            continue
        if f.sites and a.get("site") and a["site"] not in f.sites:
            continue
        out.append({k: a.get(k) for k in _ANN_KEYS})
    return strip_private(out)


def _post_announcement(body, acc: Access, db: Session):
    from schulmanager.server.audit import audit
    from .features_announcements import create_announcement
    if not has(acc.user, "announcement.post"):
        raise HTTPException(403, "Keine Berechtigung")
    f = acc.filters
    if acc.scoped:
        if body.audience == "staff":
            raise HTTPException(403, "Über API-Zugänge nur Mitteilungen an alle oder an Klassen.")
        if body.pinned or body.monitor:
            raise HTTPException(403, "Anheften und Monitor-Anzeige sind über API-Zugänge nicht möglich.")
        if f.classes and (body.audience != "classes" or not set(body.class_ids) <= f.classes):
            raise HTTPException(403, "Dieser Zugang darf nur an die freigegebenen Klassen schreiben.")
        if f.sites and body.site and body.site not in f.sites:
            raise HTTPException(403, _DENIED)
    res = create_announcement(body, user=acc.user, db=db)
    audit(db, acc.user, "api_access.announcement", f"announcement:{res['id']}",
          {"token_id": getattr(acc.user, "api_token_id", None)})
    db.commit()
    return {k: res.get(k) for k in _ANN_KEYS}


from .features_announcements import AnnouncementIn as _AnnouncementIn  # noqa: E402  (Rumpf der Mitteilung)


@router.post("/announcements", status_code=201, summary="Mitteilung veröffentlichen (Schreibzugriff)",
             description="Nur für Zugänge mit Schreibrecht im Bereich „Mitteilungen“ und Konten mit dem Recht, "
                         "Mitteilungen zu veröffentlichen (Lehrkräfte: nur eigene Klassen). Ohne Anheften/Monitor.")
def post_announcement(body: _AnnouncementIn, acc: Access = Depends(open_access("announcements", write=True)),
                      db: Session = Depends(get_db)) -> Any:
    return _post_announcement(body, acc, db)
