"""Meldungsprotokoll der Fehlzeiten lesen (Schreiben: :mod:`schulmanager.server.absence_log`).

* ``GET /student-absences/{id}/history`` – Verlauf einer Meldung (auch einer zurückgenommenen, solange das Protokoll
  besteht): wer hat wann über welchen Kanal gemeldet, jede Änderung mit vorher → nachher.
* ``GET /channels/{id}/klasse/absences?from=&to=`` – Klassenraum, Bereich „Klasse“: „Fehlzeiten & Meldungen“ je
  Schüler/in der Klasse (Zeitpunkt, Kanal, bei voller Sicht Verlauf). Nur für Lehrkräfte des Klassenraums und die
  Schulleitung – Schüler/innen und Eltern bekommen 403.

Rechtestufen (Details in :mod:`schulmanager.server.absence_log`): Klassenleitung/Sekretariat/Schulleitung sehen den vollen
Verlauf, Fachlehrkräfte der Klasse nur „abwesend gemeldet“ mit Zeitpunkt und Kanal (keine Person, Art, Status,
Gründe, Dokumente), die technische Administration nichts.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import absence_log as alog
from schulmanager.server.absence_access import AbsenceAccess
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user

from .features_class_info import _class_ctx
from .features_common import parse_date, snapshot

router = APIRouter(tags=["Krankmeldungen"])

DEFAULT_PAST_DAYS = 30
DEFAULT_FUTURE_DAYS = 14
MAX_RANGE_DAYS = 400


@router.get("/student-absences/{absence_id}/history")
def absence_history(absence_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    from schulmanager.server.db_models import StudentAbsence

    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    evs = alog.events_for(db, absence_ids=[absence_id])
    row = db.get(StudentAbsence, absence_id)
    sid = row.student_id if row is not None else (evs[0].student_id if evs else None)
    level = alog.log_level(acc, sid) if sid else None
    if level is None:
        raise HTTPException(404, "Krankmeldung nicht gefunden")
    kind = (row.kind if row is not None else None) or "krank"
    return {"absence_id": absence_id, "student_id": sid, "level": level, "withdrawn": row is None,
            "events": alog.timeline(evs, level, kind)}


@router.get("/channels/{channel_id}/klasse/absences")
def class_absences(channel_id: int, date_from: Optional[str] = Query(None, alias="from"),
                   date_to: Optional[str] = Query(None, alias="to"), user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """„Fehlzeiten & Meldungen“ der Klasse (Standard: letzte 30 Tage bis 14 Tage voraus), Schüler/innen mit Meldungen."""
    from schulmanager.server.db_models import StudentAbsence

    ctx = _class_ctx(db, user, channel_id)
    if not ctx.staff_view:  # Schüler/innen und Eltern nie
        raise HTTPException(403, "Fehlzeiten und Meldungen sehen nur die Lehrkräfte des Klassenraums")
    acc = AbsenceAccess(user, ctx.snap, db)
    if not acc.can_read:
        raise HTTPException(403, "Keine Berechtigung")
    today = parse_date(None)
    d1 = parse_date(date_from, today - timedelta(days=DEFAULT_PAST_DAYS), name="from")
    d2 = parse_date(date_to, today + timedelta(days=DEFAULT_FUTURE_DAYS), name="to")
    if d2 < d1 or (d2 - d1).days > MAX_RANGE_DAYS:
        raise HTTPException(422, "Ungültiger Zeitraum")
    class_id = ctx.ch.ref or ""
    pupils = sorted((s for s in ctx.school.students if s.class_id == class_id), key=lambda s: s.name)
    levels = {s.id: alog.log_level(acc, s.id) for s in pupils}
    visible = [s for s in pupils if levels[s.id] is not None]
    rows = list(db.scalars(select(StudentAbsence).where(
        StudentAbsence.student_id.in_([s.id for s in visible]), StudentAbsence.date_to >= d1.isoformat(),
        StudentAbsence.date_from <= d2.isoformat()).order_by(StudentAbsence.date_from.desc(), StudentAbsence.id.desc())))
    logs = alog.events_by_absence(db, [r.id for r in rows])
    from .features_student_absences import KIND_LABELS, status_label

    by_student: dict[str, list[dict]] = {}
    for r in rows:
        level = levels[r.student_id]
        evs = logs.get(r.id, [])
        first = next((e for e in evs if e.event == "angelegt"), None)
        kind = r.kind or "krank"
        item = {"absence_id": r.id, "date_from": r.date_from, "date_to": r.date_to, "periods": list(r.periods or []),
                **alog.report_info(r, first, level)}
        if level == alog.FULL:
            last = evs[-1] if evs else None
            item.update(kind=kind, kind_label=KIND_LABELS.get(kind, kind), status=r.status,
                        status_label=status_label(kind, r.status), history=alog.timeline(evs, alog.FULL, kind),
                        last_change=(alog.event_out(last, alog.FULL, kind) if last is not None and last is not first
                                     else None))
        else:
            item.update(kind="abwesend", kind_label="abwesend gemeldet")
        by_student.setdefault(r.student_id, []).append(item)
    students = [{"id": s.id, "name": s.name, "level": levels[s.id], "reports": by_student.get(s.id, [])}
                for s in visible if by_student.get(s.id)]
    return {"class_id": class_id, "from": d1.isoformat(), "to": d2.isoformat(), "students": students,
            "pupils": len(visible), "full": any(v == alog.FULL for v in levels.values())}
