"""Klassenraum, Bereich „Klasse“ (Startansicht): Regelplan, Termine/Elternabende, Ansprechpersonen.

Die angehefteten **Infokarten** sind gewöhnliche Textseiten des Klassenraums mit ``info_card = true``
(``POST /channels/{id}/items`` mit ``info_card``; ändern/löschen/sortieren wie jedes Material, siehe
``features_channels.py``) – hier gibt es dafür keine zweite Verwaltung.

* ``GET    /channels/{id}/klasse``                – Klasse, Ansprechpersonen (Klassenleitung, Fachlehrkräfte mit Fächern),
  kommende Termine der Klasse, Links zu weiteren Plänen, Rechte (``can_add_event``)
* ``GET    /channels/{id}/klasse/plan?date=``     – Regelplan (Wochenraster) der Klasse, für alle Mitglieder des
  Klassenraums (auch Schüler/Eltern, die sonst nur den eigenen Schülerplan sehen)
* ``POST   /channels/{id}/klasse/termine``        – Termin (z. B. Elternabend) nur für diese Klasse; Klassenleitung und
  Kursraum-Verwaltung
* ``DELETE /channels/{id}/klasse/termine/{eid}``  – nur Termine, die ausschließlich diese Klasse betreffen

Datenschutz: Zugriff wie auf den Klassenraum (``_ctx``: Schüler/Eltern nur der eigenen Klasse); die Antwort enthält
keine Angaben zu einzelnen Schüler/innen und keine E-Mail-Adressen.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from schulmanager import channels as logic
from schulmanager.models import Event
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user

from .features_channels import Ctx, _ctx
from .features_common import cached, check_id, mutate, new_id
from .features_timetable import check_view_access, view_monday

router = APIRouter(tags=["Kursräume"])

MAX_EVENTS = 60
ELTERNABEND = "Elternabend"


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(ELTERNABEND, min_length=1, max_length=120)
    date_from: date
    date_to: Optional[date] = None
    time_from: str = Field("", max_length=5)
    time_to: str = Field("", max_length=5)
    location: str = Field("", max_length=120)
    note: str = Field("", max_length=1000)


def _class_ctx(db: Session, user: AuthUser, channel_id: int, child: Optional[str] = None) -> Ctx:
    ctx = _ctx(db, user, channel_id, child=child)
    if ctx.ch.kind != logic.CLASS or not ctx.ch.ref or ctx.spec is None:
        raise HTTPException(404, "Diesen Bereich gibt es nur im Klassenraum")
    return ctx


def _may_add_event(ctx: Ctx) -> bool:
    return bool(ctx.manages_all and not ctx.ch.archived)


def _event_out(ev: Event, class_id: str, can_delete: bool) -> dict[str, Any]:
    own = list(ev.classes) == [class_id] and not ev.grades
    return {"id": ev.id, "title": ev.title, "kind": ev.kind, "date_from": ev.date_from[:10],
            "date_to": (ev.date_to or ev.date_from)[:10], "time_from": ev.time_from, "time_to": ev.time_to,
            "location": ev.location, "note": ev.note, "parents_evening": ELTERNABEND.lower() in ev.title.lower(),
            "own": own, "can_delete": bool(own and can_delete)}


def _class_events(ctx: Ctx, today: date) -> list[Event]:
    """Kommende Termine, die gezielt diese Klasse oder ihre Jahrgangsstufe betreffen (keine schulweiten)."""
    cls = ctx.school.index("classes").get(ctx.ch.ref or "")
    grade = cls.grade if cls else None
    out = []
    for ev in ctx.school.events:
        if not (ev.classes or ev.grades) or not ev.for_class(ctx.ch.ref, grade):
            continue
        try:
            end = date.fromisoformat((ev.date_to or ev.date_from)[:10])
        except ValueError:
            continue
        if end >= today:
            out.append(ev)
    out.sort(key=lambda e: (e.date_from, e.time_from, e.title))
    return out[:MAX_EVENTS]


def _contacts(ctx: Ctx) -> list[dict[str, Any]]:
    idx = logic.index_for(ctx.school)
    class_id = ctx.ch.ref or ""
    subjects: dict[str, dict[str, str]] = {}
    for course in idx.courses_by_class.get(class_id, ()):
        for part in course.parts:
            if part.teacher and part.subject:
                subjects.setdefault(part.teacher, {})[part.subject] = idx.subject_name(part.subject)
    lead = ctx.spec.class_teacher if ctx.spec else None
    out = []
    for tid in ctx.spec.teacher_ids if ctx.spec else ():
        subs = sorted(subjects.get(tid, {}).items(), key=lambda kv: kv[1].lower())
        out.append({"teacher_id": tid, "name": idx.teacher_name(tid), "class_teacher": tid == lead,
                    "subjects": [{"id": k, "name": v} for k, v in subs]})
    if lead and all(c["teacher_id"] != lead for c in out):
        out.insert(0, {"teacher_id": lead, "name": idx.teacher_name(lead), "class_teacher": True, "subjects": []})
    out.sort(key=lambda c: (not c["class_teacher"], c["name"].lower()))
    return out


def _plan_links(ctx: Ctx, user: AuthUser) -> list[dict[str, str]]:
    """Weitere Pläne, die dieses Konto öffnen darf (Rechte wie auf der Stundenplan-Seite)."""
    cid = ctx.ch.ref or ""
    try:
        check_view_access(user, "class", cid, ctx.snap)
        return [{"label": "Stundenplan der Klasse mit Änderungen", "to": f"/stundenplan/class/{cid}"}]
    except HTTPException:
        pass
    sid = ctx.child or getattr(user, "student_id", None)
    if sid:
        try:
            check_view_access(user, "student", sid, ctx.snap)
            return [{"label": "Stundenplan mit Änderungen" + (" (Kind)" if ctx.parent else ""),
                     "to": f"/stundenplan/student/{sid}"}]
        except HTTPException:
            pass
    return []


@router.get("/channels/{channel_id}/klasse")
def class_overview(channel_id: int, student_id: Optional[str] = Query(None, max_length=40),
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Übersicht für den Bereich „Klasse“ (ohne Infokarten – die stehen in ``GET /channels/{id}``)."""
    ctx = _class_ctx(db, user, channel_id, student_id)
    cls = ctx.school.index("classes").get(ctx.ch.ref or "")
    can_edit = _may_add_event(ctx)
    return {
        "class_id": ctx.ch.ref, "class_name": (cls.name if cls and cls.name else ctx.ch.ref),
        "contacts": _contacts(ctx),
        "events": [_event_out(e, ctx.ch.ref or "", can_edit) for e in _class_events(ctx, date.today())],
        "plan_links": _plan_links(ctx, user),
        "can_add_event": can_edit,
        "default_event_title": ELTERNABEND,
    }


@router.get("/channels/{channel_id}/klasse/plan")
def class_plan(channel_id: int, date_: Optional[str] = Query(None, alias="date"),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Regelplan (Wochenraster, ohne Vertretungen) der Klasse des Klassenraums."""
    ctx = _class_ctx(db, user, channel_id)
    school = ctx.school
    monday = view_monday(school, date_, None, None)
    cid = ctx.ch.ref or ""

    def compute():
        from schulmanager.timetable import timetable_view
        try:
            return timetable_view(school, "class", cid, when=monday, all_days=False)
        except KeyError as exc:
            raise HTTPException(404, str(exc.args[0]) if exc.args else "Nicht gefunden") from None

    return cached("class_room_plan", (cid, monday.isoformat()), compute, ctx.snap)


@router.post("/channels/{channel_id}/klasse/termine", status_code=201)
def add_event(channel_id: int, body: EventIn, user: AuthUser = Depends(current_user),
              db: Session = Depends(get_db)) -> dict:
    """Termin (z. B. Elternabend) für genau diese Klasse anlegen – Klassenleitung/Kursraum-Verwaltung."""
    ctx = _class_ctx(db, user, channel_id)
    if not _may_add_event(ctx):
        raise HTTPException(403, "Termine der Klasse legen die Klassenleitung und die Kursraum-Verwaltung an")
    class_id = ctx.ch.ref or ""
    title = logic.clean_name(body.title, 120)
    if not title:
        raise HTTPException(422, "Bitte einen Titel angeben")
    day_to = body.date_to or body.date_from
    if day_to < body.date_from:
        raise HTTPException(422, "Das Enddatum liegt vor dem Startdatum")

    def fn(school):
        from .features_data import _raise_errors, validate_item
        ev = Event(id=check_id(new_id([e.id for e in school.events], "T")), title=title,
                   date_from=body.date_from.isoformat(),
                   date_to=day_to.isoformat() if day_to != body.date_from else "",
                   time_from=body.time_from.strip(), time_to=body.time_to.strip(), kind="termin",
                   classes=[class_id], grades=[], location=logic.clean_name(body.location, 120),
                   note=logic.clean_text(body.note, 1000))
        _raise_errors(validate_item(school, "events", ev))
        school.events.append(ev)
        return ev.to_dict()

    out = mutate(user, f"Termin „{title}“ für Klasse {class_id} angelegt", fn, scope=["events", "holidays"],
                 dates=[body.date_from.isoformat(), day_to.isoformat()])
    return _event_out(Event(**out), class_id, True)


@router.delete("/channels/{channel_id}/klasse/termine/{event_id}")
def delete_event(channel_id: int, event_id: str, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    ctx = _class_ctx(db, user, channel_id)
    if not _may_add_event(ctx):
        raise HTTPException(403, "Termine der Klasse löschen die Klassenleitung und die Kursraum-Verwaltung")
    class_id = ctx.ch.ref or ""

    def fn(school):
        for i, ev in enumerate(school.events):
            if ev.id == event_id:
                if list(ev.classes) != [class_id] or ev.grades:
                    raise HTTPException(403, "Dieser Termin betrifft mehr als diese Klasse – bitte in den "
                                        "Stammdaten ändern")
                del school.events[i]
                return {"deleted": event_id}
        raise HTTPException(404, "Termin nicht gefunden")

    return mutate(user, f"Termin {event_id} der Klasse {class_id} gelöscht", fn, scope=["events", "holidays"])
