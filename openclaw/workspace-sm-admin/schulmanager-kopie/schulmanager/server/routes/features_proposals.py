"""Plan prüfen: Vorschlagspakete der Dauerprüfung (``docs/PLAN-PRUEFUNG.md``).

Berechtigte (Planung, Schulleitung): ``timetable.generate``, ``timetable.edit`` oder ``settings.edit``. Lesen und
Entscheiden haben dieselbe Berechtigung; jede Entscheidung steht im Verlauf des Pakets, im Audit und – bei Annahme –
als Version des Plans (rückgängig über „Verlauf & Audit“).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from schulmanager.server.deps import AuthUser, current_user

from .features_common import has, parse_date, snapshot, write_audit

router = APIRouter(tags=["Planung"])

PERMS = ("timetable.generate", "timetable.edit", "settings.edit")


def _need(user: AuthUser) -> None:
    if not any(has(user, p) for p in PERMS):
        raise HTTPException(403, "Keine Berechtigung")


def _proposals():
    from schulmanager.server import proposals
    return proposals


def _error(exc) -> HTTPException:
    return HTTPException(getattr(exc, "status", 409), str(exc))


class AcceptIn(BaseModel):
    note: str = Field("", max_length=500, description="Anmerkung zur Entscheidung (optional)")


class DiscardIn(BaseModel):
    reason: str = Field("", max_length=500, description="Grund (optional)")


class PostponeIn(BaseModel):
    hours: int = Field(24, ge=1, le=24 * 14, description="Zurückstellen für so viele Stunden")


def _status_block() -> dict:
    """Status der Dauerprüfung für die Seite „Plan prüfen“."""
    from schulmanager.autoplan import find_problems
    from schulmanager.server.autoplan import planner
    from .features_common import cached

    out = planner.status()
    snap = snapshot()
    problems = cached("planning_problems", (), lambda: find_problems(snap[1]), snap)
    out["version"] = snap[0]
    out["setting"] = bool(getattr(snap[1].settings, "auto_replan", True))
    out["auto_apply"] = getattr(snap[1].settings, "plan_auto_apply", "aus")
    out["open_problems"] = problems.summary(snap[1], limit=30)
    out["open_count"] = problems.count()
    return out


@router.get("/planning/proposals")
def list_proposals(user: AuthUser = Depends(current_user)):
    """Offene Vorschlagspakete (mit Varianten), zuletzt entschiedene und der Status der Dauerprüfung."""
    _need(user)
    p = _proposals()
    return {"summary": p.summary(), "open": p.list_open(), "recent": p.list_recent(10), "check": _status_block()}


@router.get("/planning/proposals/summary")
def proposals_summary(user: AuthUser = Depends(current_user)):
    """Zähler für Menü-Badge und Startseiten-Kachel (``open`` = entscheidungsreife, nicht zurückgestellte Pakete)."""
    _need(user)
    return _proposals().summary()


@router.get("/planning/proposals/{package_id}")
def get_proposal(package_id: int, user: AuthUser = Depends(current_user)):
    _need(user)
    out = _proposals().get_package(package_id, with_log=True)
    if out is None:
        raise HTTPException(404, "Vorschlag nicht gefunden")
    snap = snapshot()
    from schulmanager import plan_proposals as pp
    out["outdated"] = out["status"] == "offen" and pp.state_hash(snap[1]) != _state_of(package_id)
    return out


def _state_of(package_id: int) -> str:
    from sqlalchemy import select

    from schulmanager.server.db import SessionLocal
    from schulmanager.server.feature_models.plan_proposals import PlanProposal
    with SessionLocal() as db:
        return db.scalar(select(PlanProposal.state_hash).where(PlanProposal.id == package_id)) or ""


@router.get("/planning/proposals/{package_id}/variants/{variant_id}/timetable/{kind}/{ref}")
def variant_timetable(package_id: int, variant_id: int, kind: str, ref: str,
                      date_: Optional[str] = Query(None, alias="date"), all_days: bool = Query(True),
                      user: AuthUser = Depends(current_user)):
    """Stundenplan-Entwurf: Wochenraster (wie ``/timetable/{kind}/{ref}``) mit angewendeter Variante, nichts wird
    gespeichert."""
    _need(user)
    if kind not in ("class", "teacher", "room"):
        raise HTTPException(422, "Nur Klasse, Lehrkraft oder Raum")
    school = _proposals().preview_school(package_id, variant_id)
    if school is None:
        raise HTTPException(404, "Entwurf nicht mehr verfügbar (Vorschlag ist entschieden oder veraltet)")
    from schulmanager.calendar_utils import monday_of
    from schulmanager.timetable import timetable_view
    day = parse_date(date_, date.today())
    try:
        return timetable_view(school, kind, ref, when=monday_of(day), all_days=all_days)
    except KeyError as exc:
        raise HTTPException(404, str(exc.args[0]) if exc.args else "Nicht gefunden") from None


@router.post("/planning/proposals/{package_id}/variants/{variant_id}/accept")
def accept_variant(package_id: int, variant_id: int, body: Optional[AcceptIn] = None,
                   user: AuthUser = Depends(current_user)):
    """„Wir nehmen diesen Plan“: übernimmt die Variante. 409, wenn Plan oder Problemlage seit der Berechnung
    geändert wurden (der Vorschlag gilt dann als veraltet und wird neu berechnet)."""
    _need(user)
    p = _proposals()
    note = (body.note if body else "").strip()
    try:
        out = p.accept(package_id, variant_id, user, note)
    except p.ProposalError as exc:
        raise _error(exc) from None
    from schulmanager.server.db import session_scope
    with session_scope() as db:
        write_audit(db, user, "plan.proposal_accept", f"proposal:{package_id}",
                    {"variant": variant_id, "note": note})
    return out


@router.post("/planning/proposals/{package_id}/discard")
def discard_proposal(package_id: int, body: Optional[DiscardIn] = None, user: AuthUser = Depends(current_user)):
    """Verwirft das Paket (Grund optional). Dieselbe Problemlage wird erst nach der nächsten Änderung erneut
    vorgeschlagen."""
    _need(user)
    p = _proposals()
    reason = (body.reason if body else "").strip()
    try:
        out = p.discard(package_id, user, reason)
    except p.ProposalError as exc:
        raise _error(exc) from None
    from schulmanager.server.db import session_scope
    with session_scope() as db:
        write_audit(db, user, "plan.proposal_discard", f"proposal:{package_id}", {"reason": reason})
    return out


@router.post("/planning/proposals/{package_id}/postpone")
def postpone_proposal(package_id: int, body: Optional[PostponeIn] = None, user: AuthUser = Depends(current_user)):
    """„Später“: blendet das Paket aus Zähler und Kachel aus (Standard 24 Stunden), es bleibt offen."""
    _need(user)
    p = _proposals()
    try:
        return p.postpone(package_id, user, (body or PostponeIn()).hours)
    except p.ProposalError as exc:
        raise _error(exc) from None


@router.post("/planning/proposals/{package_id}/wake")
def wake_proposal(package_id: int, user: AuthUser = Depends(current_user)):
    """Zurückgestelltes Paket wieder anzeigen."""
    _need(user)
    p = _proposals()
    try:
        return p.wake(package_id, user)
    except p.ProposalError as exc:
        raise _error(exc) from None
