"""Plan-Stände: den aktuellen Plan oder einen Entwurf des Generators unter einem Namen speichern, ansehen,
mit dem aktuellen Plan vergleichen, wiederherstellen und löschen (Tabelle ``plan_snapshots``).

Rechte wie der Generator: Lesen ``timetable.generate`` oder ``timetable.edit``, Speichern/Wiederherstellen/Löschen
``timetable.generate``. Wiederherstellen ist eine normale Planänderung (neue Version, rückgängig über „Verlauf“) und
steht mit Audit-Eintrag ``plan.snapshot_restore`` im Protokoll.
"""
from __future__ import annotations

import json
import zlib
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from schulmanager.server.db import SessionLocal, iso, session_scope
from schulmanager.server.deps import AuthUser, current_user, require
from schulmanager.server.feature_models.plan_snapshots import PlanSnapshot

from .features_common import mutate, need, parse_date, snapshot, write_audit

router = APIRouter(tags=["Planung"])

MAX_SNAPSHOTS = 50


class SnapshotIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    note: str = Field("", max_length=500)
    job_id: Optional[str] = Field(None, description="Entwurf eines Generator-Laufs statt des aktuellen Plans")
    variant: Optional[int] = Field(None, ge=0, le=4)
    period: Optional[str] = Field(None, max_length=20, description="Planzeitraum (nur dessen Stunden); ohne Angabe der "
                                  "laufende bzw. nächste Zeitraum")
    whole: bool = Field(False, description="Ausdrücklich den ganzen Plan speichern (alle Zeiträume)")


class RestoreIn(BaseModel):
    regenerate_duties: bool = Field(True, description="Pausenaufsichten für den wiederhergestellten Plan neu berechnen")


def encode_lessons(lessons: list[dict]) -> bytes:
    return zlib.compress(json.dumps(lessons, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 6)


def decode_lessons(data: bytes) -> list[dict]:
    return json.loads(zlib.decompress(data).decode("utf-8"))


def _period_name(school, period: str) -> str:
    if not period:
        return ""
    from schulmanager import plan_periods as pp
    p = pp.get(school, period)
    return p["name"] if p else "(Zeitraum nicht mehr vorhanden)"


def _meta(row: PlanSnapshot, school=None) -> dict:
    period = row.period or ""
    return {"period": period, "period_name": _period_name(school, period) if school is not None else "",
            "scope": "period" if period else "whole",
            "id": row.id, "name": row.name, "note": row.note, "created_at": iso(row.created_at),
            "user": row.user_name, "source": row.source, "source_version": row.source_version,
            "lessons_count": row.lessons_count, "metrics": row.metrics or {}}


def _row(db, snap_id: int) -> PlanSnapshot:
    row = db.get(PlanSnapshot, snap_id)
    if row is None:
        raise HTTPException(404, "Plan-Stand nicht gefunden")
    return row


def lessons_for(school, lessons: list[dict]) -> list:
    """Stunden des Plan-Stands für ``school`` (Kurse, die es nicht mehr gibt, entfallen)."""
    from schulmanager.models import Lesson
    courses = school.index("courses")
    out = []
    for d in lessons:
        le = Lesson.from_dict(d)
        c = courses.get(le.course_id)
        if c is None:
            continue
        le.rooms = (list(le.rooms) + [None] * len(c.parts))[:len(c.parts)]
        out.append(le)
    return out


def school_with(lessons: list[dict]):
    """Kopie des aktuellen Planungsdokuments mit den Stunden des Plan-Stands."""
    from schulmanager.models import School
    school = School.from_dict(snapshot()[1].to_dict())
    school.lessons = lessons_for(school, lessons)
    return school


def with_period_only(school, period: str):
    """Kopie von ``school`` mit nur den Stunden des Zeitraums (leer ``period``: unverändert, ganzer Plan)."""
    from schulmanager.models import School
    out = School.from_dict(school.to_dict())
    if period:
        ids = {le.id for le in out.lessons if le.period == period}
        out.lessons = [le for le in out.lessons if le.id in ids]
        out.overrides = [o for o in out.overrides if o.lesson_id in ids]
    return out


def plan_metrics(school) -> dict:
    from schulmanager.timetable import validate_school
    st = validate_school(school)["stats"]
    keys = ("lessons", "class_gaps", "teacher_gaps", "site_changes", "core_late", "conflicts", "unplaced_hours")
    return {k: st.get(k) for k in keys}


@router.get("/planning/snapshots")
def list_snapshots(user: AuthUser = Depends(current_user)):
    need(user, "timetable.generate", "timetable.edit")
    with SessionLocal() as db:
        rows = db.scalars(select(PlanSnapshot).order_by(PlanSnapshot.id.desc())).all()
        school = snapshot()[1]
        return [_meta(r, school) for r in rows]


@router.post("/planning/snapshots", status_code=201)
def create_snapshot(body: SnapshotIn, user: AuthUser = Depends(require("timetable.generate"))):
    """Speichert den aktuellen Plan (oder mit ``job_id`` einen Entwurf bzw. eine Variante) unter einem Namen."""
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Bitte einen Namen angeben")
    from schulmanager import plan_periods as pp
    ver, current = snapshot()
    source = "aktuell"
    period = ""
    if pp.active(current) and not body.whole:
        period = body.period or ""
        if body.job_id and not period:
            from schulmanager.server.jobs import manager as _m
            _job = _m.get(body.job_id)
            period = str((_job.params if _job else {}).get("period") or "")
        period = period or (pp.default_target(current) or "")
        if pp.get(current, period) is None:
            raise HTTPException(422, "Bitte einen Zeitraum wählen oder ausdrücklich den ganzen Plan speichern")
    if body.job_id:
        from schulmanager.models import Lesson
        from schulmanager.server.jobs import JobError, manager
        job = manager.get(body.job_id)
        if job is None or job.result is None:
            raise HTTPException(404, "Entwurf nicht gefunden")
        try:
            lessons = list(manager.variant_of(body.job_id, body.variant)["lessons"])
        except JobError:
            lessons = list(job.result.get("lessons", []))
        job_period = str(job.params.get("period") or "")
        if job_period:
            # Entwurf eines Zeitraums: enthält nur dessen Stunden
            if period and period != job_period:
                raise HTTPException(422, "Der Entwurf gehört zu einem anderen Zeitraum")
            if period:
                school = school_with(lessons)
            else:
                school = with_period_only(current, "")
                pp.merge_generated(school, [Lesson.from_dict(d) for d in lessons], job_period,
                                   job.params.get("period_keep") or [])
        else:
            school = school_with(lessons)
            if period:       # Entwurf ohne Zeitraum, aber Zeiträume eingerichtet: Stunden dem Zeitraum zuordnen
                for le in school.lessons:
                    pp._stamp(le, pp.get(school, period))
        source = "entwurf"
    else:
        school = with_period_only(current, period)
    lessons = [le.to_dict() for le in school.lessons]
    with session_scope() as db:
        if (db.scalar(select(func.count(PlanSnapshot.id))) or 0) >= MAX_SNAPSHOTS:
            raise HTTPException(409, f"Es sind höchstens {MAX_SNAPSHOTS} Plan-Stände möglich – bitte einen löschen")
        row = PlanSnapshot(name=name, note=body.note.strip(), user_id=user.id,
                           user_name=user.display_name or user.username, source=source, source_version=ver,
                           period=period, lessons_count=len(lessons), data=encode_lessons(lessons), metrics=plan_metrics(school))
        db.add(row)
        db.flush()
        write_audit(db, user, "plan.snapshot_create", f"snapshot:{row.id}",
                    {"name": name, "source": source, "lessons": len(lessons), "period": period or "ganzer Plan"})
        return _meta(row, current)


@router.get("/planning/snapshots/{snap_id}")
def snapshot_detail(snap_id: int, user: AuthUser = Depends(current_user)):
    """Plan-Stand mit Vergleich zum aktuellen Plan (Auswertung wie beim Generator: Kennzahlen, Verschiebungen, …)."""
    need(user, "timetable.generate", "timetable.edit")
    with SessionLocal() as db:
        row = _row(db, snap_id)
        current = snapshot()[1]
        meta, lessons, period = _meta(row, current), decode_lessons(row.data), row.period or ""
    from schulmanager import generator_report as gr
    ev = gr.evaluate(with_period_only(current, period), school_with(lessons))
    return {**meta, "evaluation": ev}


@router.get("/planning/snapshots/{snap_id}/timetable/{kind}/{ref}")
def snapshot_timetable(snap_id: int, kind: str, ref: str, date_: Optional[str] = Query(None, alias="date"),
                       all_days: bool = Query(True), user: AuthUser = Depends(current_user)):
    """Wochenraster des Plan-Stands (wie ``/timetable/{kind}/{ref}``)."""
    need(user, "timetable.generate", "timetable.edit")
    if kind not in ("class", "teacher", "room"):
        raise HTTPException(422, "Nur Klasse, Lehrkraft oder Raum")
    with SessionLocal() as db:
        lessons = decode_lessons(_row(db, snap_id).data)
    from schulmanager.calendar_utils import monday_of
    from schulmanager.timetable import timetable_view
    day = parse_date(date_, date.today())
    try:
        return timetable_view(school_with(lessons), kind, ref, when=monday_of(day), all_days=all_days)
    except KeyError as exc:
        raise HTTPException(404, str(exc.args[0]) if exc.args else "Nicht gefunden") from None


@router.post("/planning/snapshots/{snap_id}/restore")
def restore_snapshot(snap_id: int, body: Optional[RestoreIn] = None,
                     user: AuthUser = Depends(require("timetable.generate"))):
    """Stellt den Plan-Stand als neuen Stundenplan her (neue Version; Tagesentscheidungen zu geänderten Stunden
    entfallen)."""
    body = body or RestoreIn()
    with SessionLocal() as db:
        row = _row(db, snap_id)
        name, lessons, period = row.name, decode_lessons(row.data), row.period or ""
    info: dict = {}

    def fn(school):
        from schulmanager import plan_periods as pp
        restored = lessons_for(school, lessons)
        if period:
            # Zeitraum-Stand: ersetzt nur den Plan dieses Zeitraums, alle anderen Zeiträume bleiben
            if pp.get(school, period) is None:
                raise HTTPException(409, "Der Zeitraum dieses Plan-Stands gibt es nicht mehr. Bitte zuerst unter "
                                         "Planung › Zeitraster & Schuljahr anlegen.")
            keep = [[le.course_id, le.day, le.start, le.length] for le in restored if le.locked]
            res = pp.merge_generated(school, restored, period, keep)
            info.update(lessons=res["lessons"], dropped=len(lessons) - len(restored), period=period)
            if body.regenerate_duties:
                from schulmanager.duties import generate_duties
                school.duties = list(generate_duties(school))
                info.update(duties=len(school.duties), duties_open=sum(1 for d in school.duties if not d.teacher))
            return info
        before = {le.id: (le.course_id, le.day, le.start, le.length) for le in school.lessons}
        after = {le.id: (le.course_id, le.day, le.start, le.length) for le in restored}
        school.lessons = restored
        school.overrides = [o for o in school.overrides
                            if o.lesson_id in after and before.get(o.lesson_id) == after[o.lesson_id]]
        info.update(lessons=len(restored), dropped=len(lessons) - len(restored))
        if body.regenerate_duties:
            from schulmanager.duties import generate_duties
            school.duties = list(generate_duties(school))
            info.update(duties=len(school.duties), duties_open=sum(1 for d in school.duties if not d.teacher))
        return info

    mutate(user, f"Plan-Stand „{name}“ wiederhergestellt", fn,
           scope=["timetable", "duties"] if body.regenerate_duties else ["timetable"],
           action="plan.snapshot_restore", details={"snapshot": snap_id, "name": name})
    return info


@router.delete("/planning/snapshots/{snap_id}")
def delete_snapshot(snap_id: int, user: AuthUser = Depends(require("timetable.generate"))):
    with session_scope() as db:
        row = _row(db, snap_id)
        write_audit(db, user, "plan.snapshot_delete", f"snapshot:{snap_id}", {"name": row.name})
        db.delete(row)
    return {"ok": True}
