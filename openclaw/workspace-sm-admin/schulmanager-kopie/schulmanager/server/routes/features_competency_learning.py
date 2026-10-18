"""Lernstand, Selbsteinschätzung, Klassenübersicht, Lernpläne und Abzeichen (Moodle-Lücke M5,
``docs/KOMPETENZEN.md``). Rahmen und Zuordnungen: ``features_competency.py``.

Lernstand
* ``GET  /competency/students/{sid}`` – Rahmen mit Stufe der Lehrkraft, Selbsteinschätzung, Verlauf, Fortschritt,
  Abzeichen. Sicht je Konto: Lehrkraft (``competency.read``, im Umfang), Schüler/in selbst, Eltern (volljährige Kinder
  nur mit Freigabe „kompetenzen“). Fremde Kinder → 404.
* ``POST /competency/assessments`` – Stufe setzen (``competency.assess``; Datum, Nachweis, Kommentar, auch mehrere)
* ``POST /competency/self`` – Selbsteinschätzung der Schülerin/des Schülers
* ``POST /competency/self/{id}/confirm`` – Lehrkraft bestätigt (oder korrigiert) die Selbsteinschätzung
* ``GET  /competency/overview`` – Klasse × Kompetenzen (Tabelle/Heatmap), „braucht Unterstützung“
* ``GET  /competency/students/{sid}/report.pdf`` – Lernentwicklungsbericht (nur Lehrkraft/Leitung)

Lernplan / Wochenplan
* ``GET|POST /competency/plans`` · ``PATCH|DELETE /competency/plans/{id}``

Abzeichen
* ``GET|POST /competency/badges`` · ``PUT|DELETE /competency/badges/{id}`` (``competency.manage``)
* ``POST /competency/badges/{id}/award`` · ``DELETE /competency/badges/{id}/award/{sid}`` (``competency.assess``)
* ``POST /competency/badges/evaluate`` – automatische Abzeichen für alle prüfen (``competency.manage``)
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from schulmanager import competency as logic
from schulmanager.server import competency_db as cdb
from schulmanager.server import crypto
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.competency import (
    CompAssessment,
    CompBadge,
    CompBadgeAward,
    CompPlan,
)

from .features_common import has, need, own_student_ids, publish_change, write_audit

router = APIRouter(tags=["Kompetenzen"])
MAX_PLANS_PER_STUDENT = 300
NOT_FOUND = "Schüler/in nicht gefunden"


class AssessEntry(BaseModel):
    student_id: str = Field(min_length=1, max_length=40)
    competency_id: int
    level: int = Field(ge=1, le=logic.MAX_LEVELS)
    date: Optional[str] = Field(None, max_length=10)
    evidence_type: str = Field("", max_length=20)
    evidence_ref: str = Field("", max_length=100)
    evidence_text: str = Field("", max_length=1000)
    comment: str = Field("", max_length=1000)


class AssessIn(BaseModel):
    entries: list[AssessEntry] = Field(min_length=1, max_length=300)


class SelfIn(BaseModel):
    competency_id: int
    level: int = Field(ge=1, le=logic.MAX_LEVELS)
    comment: str = Field("", max_length=500)


class ConfirmIn(BaseModel):
    level: Optional[int] = Field(None, ge=1, le=logic.MAX_LEVELS)
    comment: str = Field("", max_length=1000)


class PlanIn(BaseModel):
    student_id: Optional[str] = Field(None, max_length=40)
    student_ids: list[str] = Field(default_factory=list, max_length=60)
    competency_id: Optional[int] = None
    title: str = Field("", max_length=300)
    note: str = Field("", max_length=1000)
    week_start: Optional[str] = Field(None, max_length=10)
    due_date: Optional[str] = Field(None, max_length=10)
    item_type: str = Field("", max_length=30)
    item_id: str = Field("", max_length=60)


class PlanPatch(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    note: Optional[str] = Field(None, max_length=1000)
    week_start: Optional[str] = Field(None, max_length=10)
    due_date: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = Field(None, max_length=12)


class BadgeIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field("", max_length=300)
    icon: str = Field("star", max_length=30)
    color: str = Field("gold", max_length=20)
    criteria: Optional[dict] = None
    active: bool = True


class AwardIn(BaseModel):
    student_ids: list[str] = Field(min_length=1, max_length=100)
    note: str = Field("", max_length=300)


def _access(user: AuthUser, db: Session) -> cdb.Access:
    return cdb.Access(user, db)


def _day(value: Optional[str], name: str, *, default: Optional[date] = None, allow_empty: bool = False) -> Optional[date]:
    if value in (None, ""):
        if allow_empty:
            return None
        return default
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise HTTPException(422, f"{name} ist kein gültiges Datum") from exc


def _evidence(entry: AssessEntry) -> tuple[str, str, str]:
    """(Art, Verweis, Text) prüfen. Beobachtungsnotiz und Link tragen ihren Text, Abgabe/Material einen Verweis."""
    kind = entry.evidence_type
    if kind not in logic.EVIDENCE_TYPES:
        raise HTTPException(422, "Unbekannte Art des Nachweises")
    text = entry.evidence_text.strip()
    ref = entry.evidence_ref.strip()
    if kind == "":
        if text or ref:
            raise HTTPException(422, "Bitte die Art des Nachweises wählen")
        return "", "", ""
    if kind == "note":
        if not text:
            raise HTTPException(422, "Die Beobachtungsnotiz ist leer")
        return kind, "", text
    if kind == "link":
        low = text.lower()
        if not (low.startswith("https://") or low.startswith("http://") or text.startswith("/")) or " " in text:
            raise HTTPException(422, "Der Link muss mit https:// oder / beginnen")
        return kind, "", text
    if not cdb.REF_RE.match(ref):
        raise HTTPException(422, "Der Verweis auf Abgabe/Material ist ungültig")
    return kind, ref, text


def _student_info(acc: cdb.Access, sid: str) -> dict:
    st = acc.student(sid)
    return {"id": st.id, "name": st.name, "class_id": st.class_id}


# --------------------------------------------------------------------------------------------- Lernstand
@router.get("/competency/students/{sid}")
def student(sid: str, framework_id: Optional[int] = Query(None), user: AuthUser = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    acc = _access(user, db)
    kind = acc.view_kind(sid)
    if kind is None:
        raise HTTPException(404, NOT_FOUND)
    data = cdb.student_view(db, sid, kind, [framework_id] if framework_id else None)
    return {"student": _student_info(acc, sid), "kind": kind, "can_assess": acc.can_assess(sid), **data}


@router.post("/competency/assessments", status_code=201)
def assess(body: AssessIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.assess")
    acc = _access(user, db)
    idx = cdb.competency_index(db)
    created, skipped = 0, 0
    touched: list[str] = []
    today = cdb.today()
    for e in body.entries:
        comp = idx.get(e.competency_id)
        if comp is None or comp["archived"]:
            raise HTTPException(422, "Diese Kompetenz gibt es nicht (mehr)")
        if not acc.can_assess(e.student_id):
            raise HTTPException(404, NOT_FOUND)
        if e.level > comp["max_level"]:
            raise HTTPException(422, f"Der Rahmen hat nur {comp['max_level']} Niveaustufen")
        day = _day(e.date, "Datum", default=today)
        assert day is not None
        if day > today + timedelta(days=1):
            raise HTTPException(422, "Das Datum liegt in der Zukunft")
        ev_type, ev_ref, ev_text = _evidence(e)
        comment = e.comment.strip()
        teacher, _own = cdb.current_levels(cdb.student_rows(db, e.student_id, [e.competency_id]))
        last = teacher.get(e.competency_id)
        if last is not None and last.level == e.level and not (ev_type or comment):
            skipped += 1
            continue
        row = CompAssessment(student_id=e.student_id, competency_id=e.competency_id, kind="teacher", level=e.level,
                             assessed_on=day.isoformat(), evidence_type=ev_type, evidence_ref=ev_ref,
                             evidence_enc="", comment_enc="", by_user_id=getattr(user, "id", None) or None,
                             by_name=user.display_name or user.username, created_at=utcnow())
        db.add(row)
        db.flush()
        row.evidence_enc = crypto.encrypt_text(ev_text, row.aad("evidence")) if ev_text else ""
        row.comment_enc = crypto.encrypt_text(comment, row.aad("comment")) if comment else ""
        created += 1
        touched.append(e.student_id)
    awards = cdb.auto_award(db, touched, user)
    if created:
        write_audit(db, user, "competency.assess", f"students:{len(set(touched))}",
                    {"entries": created, "badges": len(awards)})
    db.commit()
    if created:
        publish_change(["competency"])
    return {"created": created, "skipped": skipped, "badges": awards}


@router.post("/competency/self", status_code=201)
def self_assess(body: SelfIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if getattr(user, "role", "") != "schueler":
        raise HTTPException(403, "Die Selbsteinschätzung machen die Schüler/innen selbst")
    own = own_student_ids(user)
    if not own:
        raise HTTPException(404, NOT_FOUND)
    sid = own[0]
    comp = cdb.competency_index(db).get(body.competency_id)
    if comp is None or comp["archived"]:
        raise HTTPException(422, "Diese Kompetenz gibt es nicht (mehr)")
    if body.level > comp["max_level"]:
        raise HTTPException(422, f"Der Rahmen hat nur {comp['max_level']} Niveaustufen")
    row = CompAssessment(student_id=sid, competency_id=body.competency_id, kind="self", level=body.level,
                         assessed_on=cdb.today().isoformat(), evidence_type="", evidence_ref="", evidence_enc="",
                         comment_enc="", by_user_id=getattr(user, "id", None) or None,
                         by_name=user.display_name or user.username, created_at=utcnow())
    db.add(row)
    db.flush()
    comment = body.comment.strip()
    row.comment_enc = crypto.encrypt_text(comment, row.aad("comment")) if comment else ""
    write_audit(db, user, "competency.self", f"student:{sid}", {"competency": body.competency_id, "level": body.level})
    db.commit()
    publish_change(["competency"])
    return cdb.assessment_dict(row, "self")


@router.post("/competency/self/{assessment_id}/confirm")
def confirm_self(assessment_id: int, body: ConfirmIn, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    need(user, "competency.assess")
    acc = _access(user, db)
    row = db.get(CompAssessment, assessment_id)
    if row is None or row.kind != "self" or not acc.can_assess(row.student_id):
        raise HTTPException(404, "Selbsteinschätzung nicht gefunden")
    comp = cdb.competency_index(db).get(row.competency_id)
    if comp is None:
        raise HTTPException(404, "Selbsteinschätzung nicht gefunden")
    level = body.level or row.level
    if level > comp["max_level"]:
        raise HTTPException(422, f"Der Rahmen hat nur {comp['max_level']} Niveaustufen")
    name = user.display_name or user.username
    row.confirmed_at, row.confirmed_by = utcnow(), name
    t = CompAssessment(student_id=row.student_id, competency_id=row.competency_id, kind="teacher", level=level,
                       assessed_on=cdb.today().isoformat(), evidence_type="", evidence_ref="", evidence_enc="",
                       comment_enc="", by_user_id=getattr(user, "id", None) or None, by_name=name,
                       created_at=utcnow())
    db.add(t)
    db.flush()
    comment = body.comment.strip()
    t.comment_enc = crypto.encrypt_text(comment, t.aad("comment")) if comment else ""
    awards = cdb.auto_award(db, [row.student_id], user)
    write_audit(db, user, "competency.confirm", f"student:{row.student_id}",
                {"competency": row.competency_id, "level": level, "self_level": row.level})
    db.commit()
    publish_change(["competency"])
    return {"teacher": cdb.assessment_dict(t, "staff"), "self": cdb.assessment_dict(row, "staff"), "badges": awards}


# ----------------------------------------------------------------------------------------- Klassenübersicht
@router.get("/competency/overview")
def overview(framework_id: Optional[int] = Query(None), class_id: Optional[str] = Query(None, max_length=40),
             area_id: Optional[int] = Query(None), user: AuthUser = Depends(current_user),
             db: Session = Depends(get_db)) -> dict:
    need(user, "competency.read")
    acc = _access(user, db)
    scope = acc.read_scope()
    school = acc.school
    visible = [s for s in school.students if scope is None or s.id in scope]
    class_ids = {s.class_id for s in visible}
    classes = [{"id": c.id, "name": c.name} for c in sorted(school.classes, key=lambda c: (c.grade, c.name))
               if c.id in class_ids]
    frameworks = cdb.tree(db)
    out: dict[str, Any] = {"classes": classes, "frameworks": [cdb.framework_summary(f) for f in frameworks],
                           "framework": None, "class": None, "students": [], "summary": {}}
    if not frameworks or not classes:
        return out
    fw = next((f for f in frameworks if f["id"] == framework_id), frameworks[0]) if framework_id else frameworks[0]
    cls = next((c for c in classes if c["id"] == class_id), classes[0]) if class_id else classes[0]
    areas = [a for a in fw["areas"] if area_id in (None, a["id"])]
    comp_ids = [c["id"] for a in areas for c in a["competencies"]]
    all_ids = [c["id"] for a in fw["areas"] for c in a["competencies"]]
    students = sorted((s for s in visible if s.class_id == cls["id"]), key=lambda s: s.name.lower())
    n = len(fw["levels"])
    rows_by: dict[str, list[CompAssessment]] = {s.id: [] for s in students}
    if students and all_ids:
        for r in db.scalars(select(CompAssessment).where(CompAssessment.student_id.in_(list(rows_by)),
                                                         CompAssessment.competency_id.in_(all_ids))
                            .order_by(CompAssessment.assessed_on, CompAssessment.id)):
            rows_by[r.student_id].append(r)
    out_students = []
    for s in students:
        teacher, own = cdb.current_levels(rows_by[s.id])
        cells = {}
        support = pending = 0
        for cid in comp_ids:
            t, o = teacher.get(cid), own.get(cid)
            if t is None and o is None:
                continue
            p = bool(o and o.confirmed_at is None)
            cells[str(cid)] = {"t": t.level if t else None, "s": o.level if o else None, "p": p}
            support += logic.needs_support(t.level if t else None, o.level if o else None, fw["support_level"])
            pending += p
        levels = {cid: r.level for cid, r in teacher.items() if cid in comp_ids}
        out_students.append({"id": s.id, "name": s.name, "cells": cells, "support": support, "pending": pending,
                             "progress": round(logic.progress(levels, comp_ids, n), 3)})
    out.update({"framework": {**{k: fw[k] for k in ("id", "name", "subject", "levels", "support_level")},
                              "areas": areas, "all_areas": [{"id": a["id"], "name": a["name"]} for a in fw["areas"]]},
                "class": cls, "students": out_students,
                "summary": {"students": len(out_students),
                            "support_students": sum(1 for x in out_students if x["support"]),
                            "pending": sum(x["pending"] for x in out_students)}})
    return out


# ------------------------------------------------------------------------------------------------- Pläne
def _plan_dict(p: CompPlan, idx: dict[int, dict], viewer: str, user_id: Optional[int]) -> dict:
    comp = idx.get(p.competency_id) if p.competency_id else None
    today = cdb.today().isoformat()
    return {"id": p.id, "student_id": p.student_id, "competency_id": p.competency_id,
            "competency_title": comp["title"] if comp else "", "framework_name": comp["framework_name"] if comp else "",
            "area_name": comp["area_name"] if comp else "",
            "title": cdb.dec(p.title_enc, p.aad("title")) or (comp["title"] if comp else ""),
            "note": cdb.dec(p.note_enc, p.aad("note")), "week_start": p.week_start, "due_date": p.due_date,
            "status": p.status, "source": p.source, "item_type": p.item_type, "item_id": p.item_id,
            "overdue": bool(p.status != "erledigt" and p.due_date and p.due_date < today),
            "done_at": iso(p.done_at),
            "can_edit": viewer == "staff" or (viewer == "self" and p.source == "schueler"),
            "can_status": viewer in ("staff", "self")}


def _plan_access(acc: cdb.Access, sid: str, write: bool) -> str:
    kind = acc.view_kind(sid)
    if kind is None:
        raise HTTPException(404, NOT_FOUND)
    if write and kind == "staff" and not acc.can_assess(sid):
        raise HTTPException(403, "Keine Berechtigung")
    if write and kind == "family":
        raise HTTPException(403, "Eltern können den Lernplan ansehen, aber nicht ändern")
    return kind


@router.get("/competency/plans")
def list_plans(student_id: str = Query(..., max_length=40), user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    acc = _access(user, db)
    kind = _plan_access(acc, student_id, False)
    idx = cdb.competency_index(db)
    rows = db.scalars(select(CompPlan).where(CompPlan.student_id == student_id)
                      .order_by(CompPlan.week_start.is_(None), CompPlan.week_start.desc(), CompPlan.due_date,
                                CompPlan.id))
    return {"student": _student_info(acc, student_id), "kind": kind, "can_assess": acc.can_assess(student_id),
            "current_week": logic.week_start(cdb.today()).isoformat(),
            "plans": [_plan_dict(p, idx, kind, getattr(user, "id", None)) for p in rows]}


def _plan_days(week: Optional[str], due: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    w = _day(week, "Die Woche", allow_empty=True)
    d = _day(due, "Die Fälligkeit", allow_empty=True)
    return (logic.week_start(w).isoformat() if w else None), (d.isoformat() if d else None)


@router.post("/competency/plans", status_code=201)
def create_plans(body: PlanIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    acc = _access(user, db)
    role = getattr(user, "role", "")
    ids = list(dict.fromkeys([*(body.student_ids or []), *([body.student_id] if body.student_id else [])]))
    if role == "schueler":
        own = own_student_ids(user)
        ids = own[:1]
    if not ids:
        raise HTTPException(422, "Bitte mindestens eine Schülerin/einen Schüler wählen")
    comp = None
    if body.competency_id is not None:
        comp = cdb.competency_index(db).get(body.competency_id)
        if comp is None:
            raise HTTPException(422, "Diese Kompetenz gibt es nicht (mehr)")
    title = body.title.strip() or (comp["title"] if comp else "")
    if not title:
        raise HTTPException(422, "Bitte ein Ziel angeben oder eine Kompetenz wählen")
    if body.item_type or body.item_id:
        if not cdb.ITEM_TYPE_RE.match(body.item_type) or not cdb.ITEM_ID_RE.match(body.item_id):
            raise HTTPException(422, "Elementtyp oder Element-ID ist ungültig")
    week, due = _plan_days(body.week_start, body.due_date)
    created = []
    for sid in ids:
        kind = _plan_access(acc, sid, True)
        if db.scalar(select(func.count(CompPlan.id)).where(CompPlan.student_id == sid)) >= MAX_PLANS_PER_STUDENT:
            raise HTTPException(422, f"Höchstens {MAX_PLANS_PER_STUDENT} Einträge im Lernplan")
        p = CompPlan(student_id=sid, competency_id=body.competency_id, title_enc="", note_enc="", week_start=week,
                     due_date=due, status="offen", source="schueler" if kind == "self" else "lehrkraft",
                     item_type=body.item_type, item_id=body.item_id, created_by=getattr(user, "id", None) or None,
                     created_at=utcnow(), updated_at=utcnow())
        db.add(p)
        db.flush()
        p.title_enc = crypto.encrypt_text(title, p.aad("title"))
        p.note_enc = crypto.encrypt_text(body.note.strip(), p.aad("note")) if body.note.strip() else ""
        created.append(p)
    write_audit(db, user, "competency.plan.create", f"students:{len(ids)}", {"count": len(created)})
    db.commit()
    publish_change(["competency"])
    idx = cdb.competency_index(db)
    return {"created": [_plan_dict(p, idx, "staff" if role != "schueler" else "self", None) for p in created]}


def _own_plan(db: Session, acc: cdb.Access, plan_id: int, write: bool = True) -> tuple[CompPlan, str]:
    p = db.get(CompPlan, plan_id)
    if p is None:
        raise HTTPException(404, "Eintrag nicht gefunden")
    return p, _plan_access(acc, p.student_id, write)


@router.patch("/competency/plans/{plan_id}")
def patch_plan(plan_id: int, body: PlanPatch, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    acc = _access(user, db)
    p, kind = _own_plan(db, acc, plan_id)
    fields = body.model_dump(exclude_unset=True)
    if kind == "self" and p.source != "schueler" and set(fields) - {"status"}:
        raise HTTPException(403, "Ziele der Lehrkraft können Sie nur abhaken")
    if "status" in fields:
        if fields["status"] not in logic.PLAN_STATUS:
            raise HTTPException(422, "Unbekannter Status")
        if p.status != fields["status"]:
            p.status = fields["status"]
            p.done_at = utcnow() if p.status == "erledigt" else None
    if "title" in fields:
        title = (fields["title"] or "").strip()
        if not title:
            raise HTTPException(422, "Das Ziel darf nicht leer sein")
        p.title_enc = crypto.encrypt_text(title, p.aad("title"))
    if "note" in fields:
        note = (fields["note"] or "").strip()
        p.note_enc = crypto.encrypt_text(note, p.aad("note")) if note else ""
    if "week_start" in fields or "due_date" in fields:
        week, due = _plan_days(fields.get("week_start", p.week_start), fields.get("due_date", p.due_date))
        p.week_start, p.due_date = week, due
    p.updated_at = utcnow()
    write_audit(db, user, "competency.plan.update", f"plan:{p.id}", {"fields": sorted(fields)})
    db.commit()
    publish_change(["competency"])
    return _plan_dict(p, cdb.competency_index(db), kind, getattr(user, "id", None))


@router.delete("/competency/plans/{plan_id}")
def delete_plan(plan_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    acc = _access(user, db)
    p, kind = _own_plan(db, acc, plan_id)
    if kind == "self" and p.source != "schueler":
        raise HTTPException(403, "Ziele der Lehrkraft können Sie nur abhaken")
    db.delete(p)
    write_audit(db, user, "competency.plan.delete", f"plan:{plan_id}", {})
    db.commit()
    publish_change(["competency"])
    return {"deleted": plan_id}


# --------------------------------------------------------------------------------------------- Abzeichen
def _check_badge(db: Session, body: BadgeIn) -> Optional[dict]:
    if body.icon not in logic.BADGE_ICONS:
        raise HTTPException(422, "Dieses Symbol gibt es nicht")
    if body.color not in logic.BADGE_COLORS:
        raise HTTPException(422, "Diese Farbe gibt es nicht")
    try:
        criteria = logic.validate_criteria(body.criteria)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if criteria:
        idx = cdb.competency_index(db)
        if criteria["type"] == "competencies":
            refs = [idx.get(i) for i in criteria["competency_ids"]]
        elif criteria["type"] == "area":
            refs = [v for v in idx.values() if v["area_id"] == criteria["area_id"]]
        else:
            refs = [v for v in idx.values() if v["framework_id"] == criteria["framework_id"]]
        if not refs or any(r is None for r in refs):
            raise HTTPException(422, "Die gewählten Kompetenzen gibt es nicht (mehr)")
        if criteria["min_level"] > min(r["max_level"] for r in refs if r):
            raise HTTPException(422, "Die Mindeststufe ist höher als die Niveaustufen des Rahmens")
    return criteria


@router.get("/competency/badges")
def list_badges(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    if not (getattr(user, "role", "") in ("schueler", "eltern")
            or any(has(user, p) for p in ("competency.read", "competency.assess", "competency.manage"))):
        raise HTTPException(403, "Keine Berechtigung")
    counts = dict(db.execute(select(CompBadgeAward.badge_id, func.count(CompBadgeAward.id))
                             .group_by(CompBadgeAward.badge_id)).all())
    idx = cdb.competency_index(db)
    manage = has(user, "competency.manage")
    return [cdb.badge_dict(b, counts.get(b.id, 0), cdb.criteria_text(db, b.criteria, idx))
            for b in db.scalars(select(CompBadge).order_by(CompBadge.name, CompBadge.id))
            if b.active or manage]


@router.post("/competency/badges", status_code=201)
def create_badge(body: BadgeIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    criteria = _check_badge(db, body)
    b = CompBadge(name=body.name.strip(), description=body.description.strip(), icon=body.icon, color=body.color,
                  criteria=criteria, active=body.active, created_by=getattr(user, "id", None) or None)
    db.add(b)
    db.flush()
    write_audit(db, user, "competency.badge.create", f"badge:{b.id}", {"name": b.name})
    db.commit()
    publish_change(["competency"])
    return cdb.badge_dict(b, 0, cdb.criteria_text(db, b.criteria))


@router.put("/competency/badges/{badge_id}")
def update_badge(badge_id: int, body: BadgeIn, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    b = db.get(CompBadge, badge_id)
    if b is None:
        raise HTTPException(404, "Abzeichen nicht gefunden")
    b.criteria = _check_badge(db, body)
    b.name, b.description, b.icon, b.color = body.name.strip(), body.description.strip(), body.icon, body.color
    b.active = body.active
    write_audit(db, user, "competency.badge.update", f"badge:{b.id}", {"name": b.name})
    db.commit()
    publish_change(["competency"])
    n = db.scalar(select(func.count(CompBadgeAward.id)).where(CompBadgeAward.badge_id == b.id)) or 0
    return cdb.badge_dict(b, n, cdb.criteria_text(db, b.criteria))


@router.delete("/competency/badges/{badge_id}")
def delete_badge(badge_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    b = db.get(CompBadge, badge_id)
    if b is None:
        raise HTTPException(404, "Abzeichen nicht gefunden")
    n = db.scalar(select(func.count(CompBadgeAward.id)).where(CompBadgeAward.badge_id == b.id)) or 0
    db.execute(delete(CompBadgeAward).where(CompBadgeAward.badge_id == b.id))
    db.delete(b)
    write_audit(db, user, "competency.badge.delete", f"badge:{badge_id}", {"name": b.name, "awards": n})
    db.commit()
    publish_change(["competency"])
    return {"deleted": badge_id, "awards": n}


@router.post("/competency/badges/{badge_id}/award", status_code=201)
def award_badge(badge_id: int, body: AwardIn, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    need(user, "competency.assess")
    acc = _access(user, db)
    b = db.get(CompBadge, badge_id)
    if b is None or not b.active:
        raise HTTPException(404, "Abzeichen nicht gefunden")
    ids = list(dict.fromkeys(body.student_ids))
    if any(not acc.can_assess(s) for s in ids):
        raise HTTPException(404, NOT_FOUND)
    have = set(db.scalars(select(CompBadgeAward.student_id).where(CompBadgeAward.badge_id == badge_id)))
    created = 0
    for sid in ids:
        if sid in have:
            continue
        a = CompBadgeAward(badge_id=badge_id, student_id=sid, awarded_on=cdb.today().isoformat(),
                           awarded_by=getattr(user, "id", None) or None,
                           awarded_by_name=user.display_name or user.username, auto=False, note_enc="")
        db.add(a)
        db.flush()
        if body.note.strip():
            a.note_enc = crypto.encrypt_text(body.note.strip(), a.aad("note"))
        created += 1
    if created:
        write_audit(db, user, "competency.badge.award", f"badge:{badge_id}", {"students": created})
    db.commit()
    if created:
        publish_change(["competency"])
    return {"awarded": created, "already": len(ids) - created}


@router.delete("/competency/badges/{badge_id}/award/{sid}")
def revoke_badge(badge_id: int, sid: str, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    need(user, "competency.assess")
    acc = _access(user, db)
    if not acc.can_assess(sid):
        raise HTTPException(404, NOT_FOUND)
    a = db.scalar(select(CompBadgeAward).where(CompBadgeAward.badge_id == badge_id, CompBadgeAward.student_id == sid))
    if a is None:
        raise HTTPException(404, "Das Abzeichen wurde nicht vergeben")
    db.delete(a)
    write_audit(db, user, "competency.badge.revoke", f"badge:{badge_id}", {"student": sid})
    db.commit()
    publish_change(["competency"])
    return {"revoked": sid}


@router.post("/competency/badges/evaluate")
def evaluate_badges(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    need(user, "competency.manage")
    sids = list(db.scalars(select(CompAssessment.student_id).where(CompAssessment.kind == "teacher").distinct()))
    awards = cdb.auto_award(db, sids, user)
    if awards:
        write_audit(db, user, "competency.badge.evaluate", "badges", {"awarded": len(awards)})
    db.commit()
    if awards:
        publish_change(["competency"])
    return {"awarded": len(awards), "badges": awards}


# ----------------------------------------------------------------------------------------------- Bericht
@router.get("/competency/students/{sid}/report.pdf")
def report(sid: str, framework_id: Optional[int] = Query(None), user: AuthUser = Depends(current_user),
           db: Session = Depends(get_db)) -> Response:
    """Lernentwicklungsbericht als PDF: Stufen je Kompetenz (Lehrkraft und Selbsteinschätzung), Kommentare, Abzeichen,
    Lernplan und Platz für Bemerkungen. Nur für Lehrkräfte/Leitung im Umfang; ohne Beobachtungsnotizen."""
    from schulmanager.server.competency_report import build_report
    from schulmanager.server.files import content_disposition

    acc = _access(user, db)
    if acc.view_kind(sid) != "staff":
        raise HTTPException(404, NOT_FOUND)
    view = cdb.student_view(db, sid, "family", [framework_id] if framework_id else None)
    plans = [_plan_dict(p, cdb.competency_index(db), "family", None)
             for p in db.scalars(select(CompPlan).where(CompPlan.student_id == sid))]
    info = _student_info(acc, sid)
    cls = next((c.name for c in acc.school.classes if c.id == info["class_id"]), info["class_id"])
    pdf = build_report(info["name"], cls, view["frameworks"], view["badges"], plans, cdb.today())
    write_audit(db, user, "competency.report", f"student:{sid}", {})
    db.commit()
    safe = "".join(ch if ch.isalnum() else "_" for ch in info["name"]).strip("_") or "Kind"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": content_disposition(f"Lernentwicklungsbericht_{safe}.pdf")})
