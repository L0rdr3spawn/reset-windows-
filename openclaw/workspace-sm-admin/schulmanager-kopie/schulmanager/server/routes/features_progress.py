"""Lernfortschritt im Kursraum (Moodle-Lücken M2, ``docs/LERNFORTSCHRITT.md``): Abschlussbedingungen, „Erledigt“-Häkchen,
Fortschrittsübersicht und bedingte Freigabe. Die Logik steht in ``schulmanager/server/progress.py``; Rollen und Zugriff
kommen aus ``features_channels`` (``_ctx``).

* ``GET  /channels/{id}/elements`` – Lehrende: alle Elemente (Material, Aufgaben, Elemente anderer Module) mit
  Abschlussbedingung und Freigaberegel, dazu die wählbaren Gruppen.
* ``PUT/DELETE /channels/{id}/elements/{typ}/{eid}/completion`` – Abschlussbedingung festlegen/entfernen.
* ``POST /channels/{id}/completion/bulk`` – dieselbe Bedingung für mehrere Elemente.
* ``PUT  /channels/{id}/elements/{typ}/{eid}/availability`` – bedingte Freigabe (UND/ODER-Baum; ``tree: null`` entfernt).
* ``POST /channels/{id}/elements/{typ}/{eid}/done`` – Schüler/in hakt ab (nur bei „Selbst abhaken“).
* ``GET  /channels/{id}/progress/me`` – Fortschritt der Schülerin/des Schülers (bzw. des Kindes, wenn die Lehrkraft die
  Ansicht für Eltern freigegeben hat: Kursraum-Einstellung ``progress_parents``).
* ``GET  /channels/{id}/progress`` – Lehrende: Tabelle Schüler/in × Elemente.

Alles Schreibende wird protokolliert (Audit, ohne Inhalte).
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager import channels as logic
from schulmanager.server import progress
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.feature_models.channels import ChannelExtraMember
from schulmanager.server.feature_models.progress import AvailabilityRule, CompletionMark, CompletionRule

from . import features_channels as fc

router = APIRouter(tags=["Lernfortschritt"])

MAX_BULK = 300
Mode = Literal["manual", "viewed", "submitted", "graded", "passed"]


class CompletionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Mode
    pass_percent: Optional[int] = Field(None, ge=0, le=100)


class BulkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    elements: list[dict[str, Any]] = Field(min_length=1, max_length=MAX_BULK)
    mode: Optional[Mode] = None          # None = Abschlussbedingung entfernen
    pass_percent: Optional[int] = Field(None, ge=0, le=100)


class AvailabilityIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tree: Optional[dict[str, Any]] = None


class DoneIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    done: bool = True


# =========================================================================== Hilfen
def _all_elements(db: Session, channel_id: int) -> dict[tuple[str, int], progress.Element]:
    out: dict[tuple[str, int], progress.Element] = {}
    for provider in progress.providers().values():
        try:
            for el in provider.elements(db, channel_id):
                out[(el.type, el.id)] = el
        except Exception:  # noqa: BLE001 - ein defektes Modul darf die Kursraum-Seite nicht kippen
            fc.log.exception("Elemente von %s nicht lesbar", getattr(provider, "type", "?"))
    return out


def _element_or_404(db: Session, ctx: fc.Ctx, etype: str, eid: int) -> progress.Element:
    el = _all_elements(db, ctx.ch.id).get((etype, eid))
    if el is None:
        raise HTTPException(404, "Element nicht gefunden")
    return el


def _need_edit(db: Session, ctx: fc.Ctx, el: progress.Element) -> None:
    provider = progress.providers().get(el.type)
    getter = getattr(provider, "created_by", None)
    created_by = getter(db, el.id) if callable(getter) else None
    if getter is None:
        if not ctx.teacher:
            raise HTTPException(403, "Nur Lehrende dieses Kursraums dürfen das")
        return
    ctx.need_edit(created_by)


def _groups(db: Session, channel_id: int) -> list[dict[str, Any]]:
    gp = progress.group_provider()
    if gp is None:
        return []
    try:
        return [{"id": int(g["id"]), "name": str(g["name"])} for g in gp.list_groups(db, channel_id)]
    except Exception:  # noqa: BLE001
        fc.log.exception("Gruppen nicht lesbar")
        return []


def _rule_out(rule: Optional[CompletionRule]) -> Optional[dict[str, Any]]:
    if rule is None:
        return None
    return {"mode": rule.mode, "mode_label": progress.MODE_LABELS.get(rule.mode, rule.mode),
            "pass_percent": rule.pass_percent}


def _visible_ids(db: Session, ctx: fc.Ctx, clock: fc.Clock, prog: progress.Progress, uid: Optional[int],
                 els: list[progress.Element]) -> dict[tuple[str, int], progress.Gate]:
    """Welche Elemente sieht die Schülerin/der Schüler (``Gate``)? Material/Aufgaben nach Zeitfreigabe, Ordner und
    Bedingungen; andere Elementarten nach ``visible_ids`` ihres Anbieters (fehlt es, gelten sie als sichtbar)."""
    gates: dict[tuple[str, int], progress.Gate] = {}
    item_ids = {e.id for e in els if e.type == progress.ELEMENT_ITEM}
    if item_ids:
        states = clock.folder_states(fc._folders(db, ctx.ch.id))
        for item, _ in fc._load_items(db, [ctx.ch.id]):
            if item.id in item_ids:
                gates[(progress.ELEMENT_ITEM, item.id)] = prog.gate(
                    uid, progress.ELEMENT_ITEM, item.id, clock.visibility(item, states), ctx.ch.id)
    for etype in {e.type for e in els} - {progress.ELEMENT_ITEM}:
        ids = [e.id for e in els if e.type == etype]
        fn = getattr(progress.providers().get(etype), "visible_ids", None)
        shown = set(fn(db, ctx.ch.id, uid, ids)) if callable(fn) and uid else set(ids)
        for i in ids:
            gates[(etype, i)] = progress.Gate(i in shown)
    return gates


def _pupil_progress(db: Session, ctx: fc.Ctx, uid: Optional[int]) -> dict[str, Any]:
    clock = fc.Clock(ctx.snap, channels=[ctx.ch])
    prog = progress.Progress(db, [ctx.ch.id], [uid])
    elements = _all_elements(db, ctx.ch.id)
    tracked = [elements[key] for key in prog.rules if key in elements]
    gates = _visible_ids(db, ctx, clock, prog, uid, tracked)
    prog.prefetch([uid])
    rows, refs = [], []
    for el in tracked:
        gate = gates.get((el.type, el.id), progress.Gate(True))
        if not gate.show:
            continue
        rule = prog.rule(el.type, el.id)
        assert rule is not None
        refs.append((el.type, el.id))
        rows.append({"element_type": el.type, "element_id": el.id, "title": el.title, "kind_label": el.kind_label,
                     "folder_id": el.folder_id, "mode": rule.mode,
                     "mode_label": progress.MODE_LABELS.get(rule.mode, rule.mode),
                     "done": bool(prog.done(uid, el.type, el.id)), "locked": gate.locked, "locked_text": gate.text,
                     "can_toggle": bool(ctx.student and rule.mode == "manual" and not gate.locked
                                        and not ctx.ch.archived)})
    return {"enabled": bool(rows), "elements": rows, **prog.summary(uid, refs)}


# =========================================================================== Lehrende: Regeln
@router.get("/channels/{channel_id}/elements")
def list_elements(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    prog = progress.Progress(db, [ctx.ch.id])
    rows = []
    for el in _all_elements(db, ctx.ch.id).values():
        tree = prog.avail.get((el.type, el.id))
        rows.append({"element_type": el.type, "element_id": el.id, "title": el.title, "kind_label": el.kind_label,
                     "folder_id": el.folder_id, "modes": [{"mode": m, "label": progress.MODE_LABELS[m]} for m in el.modes],
                     "completion": _rule_out(prog.rule(el.type, el.id)),
                     "availability": {"tree": tree, "text": prog.describe(el.type, el.id, ctx.ch.id)} if tree else None})
    groups = _groups(db, ctx.ch.id)
    return {"elements": rows, "groups": groups, "groups_available": progress.group_provider() is not None,
            "types": {t: p.label for t, p in progress.providers().items()},
            "progress_parents": bool(ctx.ch.setting("progress_parents"))}


def _set_rule(db: Session, ctx: fc.Ctx, el: progress.Element, mode: Optional[str], pass_percent: Optional[int]) -> str:
    row = db.scalar(select(CompletionRule).where(CompletionRule.element_type == el.type,
                                                 CompletionRule.element_id == el.id))
    if mode is None:
        if row is not None:
            db.delete(row)
        return "removed"
    if mode not in el.modes:
        raise HTTPException(422, f"„{progress.MODE_LABELS[mode]}“ passt nicht zu „{el.title}“")
    if mode != "passed":
        pass_percent = None
    elif pass_percent is None:
        pass_percent = progress.DEFAULT_PASS_PERCENT
    if row is None:
        db.add(CompletionRule(channel_id=ctx.ch.id, element_type=el.type, element_id=el.id, mode=mode,
                              pass_percent=pass_percent, created_by=ctx.user.id, created_at=utcnow()))
    else:
        row.mode, row.pass_percent, row.updated_at = mode, pass_percent, utcnow()
    return "set"


@router.put("/channels/{channel_id}/elements/{element_type}/{element_id}/completion")
def put_completion(channel_id: int, element_type: str, element_id: int, body: CompletionIn, request: Request,
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    el = _element_or_404(db, ctx, element_type, element_id)
    _need_edit(db, ctx, el)
    _set_rule(db, ctx, el, body.mode, body.pass_percent)
    audit(db, user, "completion.rule", f"{el.type}:{el.id}",
          {"channel_id": ctx.ch.id, "mode": body.mode, "pass_percent": body.pass_percent}, ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    rule = db.scalar(select(CompletionRule).where(CompletionRule.element_type == el.type,
                                                  CompletionRule.element_id == el.id))
    return {"completion": _rule_out(rule)}


@router.delete("/channels/{channel_id}/elements/{element_type}/{element_id}/completion")
def delete_completion(channel_id: int, element_type: str, element_id: int, request: Request,
                      user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    el = _element_or_404(db, ctx, element_type, element_id)
    _need_edit(db, ctx, el)
    _remove_dependents(db, ctx, el)
    _set_rule(db, ctx, el, None, None)
    audit(db, user, "completion.rule", f"{el.type}:{el.id}", {"channel_id": ctx.ch.id, "mode": None},
          ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    return {"completion": None}


def _remove_dependents(db: Session, ctx: fc.Ctx, el: progress.Element) -> None:
    """Ohne Abschlussbedingung kann kein anderes Element mehr darauf warten (sonst bliebe es für immer gesperrt)."""
    users = [r.element_type + ":" + str(r.element_id) for r in db.scalars(
        select(AvailabilityRule).where(AvailabilityRule.channel_id == ctx.ch.id))
        if (el.type, el.id) in progress.tree_refs(r.tree)]
    if users:
        raise HTTPException(409, {"message": "Andere Elemente werden erst nach diesem Element freigegeben. "
                                  "Bitte zuerst deren Freigaberegel ändern.", "elements": users})


@router.post("/channels/{channel_id}/completion/bulk")
def bulk_completion(channel_id: int, body: BulkIn, request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    known = _all_elements(db, ctx.ch.id)
    done = skipped = 0
    for ref in body.elements:
        try:
            el = known.get((str(ref.get("element_type")), int(ref.get("element_id"))))
        except (TypeError, ValueError):
            el = None
        if el is None:
            skipped += 1
            continue
        try:
            _need_edit(db, ctx, el)
        except HTTPException:
            skipped += 1
            continue
        if body.mode is not None and body.mode not in el.modes:
            skipped += 1
            continue
        if body.mode is None:
            try:
                _remove_dependents(db, ctx, el)
            except HTTPException:
                skipped += 1
                continue
        _set_rule(db, ctx, el, body.mode, body.pass_percent)
        done += 1
    audit(db, user, "completion.bulk", f"channel:{ctx.ch.id}",
          {"mode": body.mode, "changed": done, "skipped": skipped}, ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    return {"changed": done, "skipped": skipped}


@router.put("/channels/{channel_id}/elements/{element_type}/{element_id}/availability")
def put_availability(channel_id: int, element_type: str, element_id: int, body: AvailabilityIn, request: Request,
                     user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, manage=True)
    el = _element_or_404(db, ctx, element_type, element_id)
    _need_edit(db, ctx, el)
    known = _all_elements(db, ctx.ch.id)
    prog = progress.Progress(db, [ctx.ch.id])
    groups = {g["id"] for g in _groups(db, ctx.ch.id)}
    start = (el.type, el.id)

    def valid_ref(etype: str, eid: int, leaf: str) -> Optional[str]:
        other = known.get((etype, eid))
        if other is None:
            return "Das gewählte Element gibt es in diesem Kursraum nicht"
        if (etype, eid) == start:
            return "Ein Element kann nicht von sich selbst abhängen"
        if leaf == "completed" and prog.rule(etype, eid) is None:
            return f"„{other.title}“ hat keine Abschlussbedingung – bitte dort zuerst eine festlegen"
        if leaf in ("score", "note"):
            rule = prog.rule(etype, eid)
            if "graded" not in other.modes or rule is None:
                return f"„{other.title}“ wird nicht bewertet"
        return None

    try:
        tree = progress.normalize_tree(body.tree, valid_ref=valid_ref, group_ok=lambda gid: gid in groups)
    except progress.TreeError as exc:
        raise HTTPException(422, str(exc)) from exc
    if tree and progress.would_cycle(prog.avail, start, tree):
        raise HTTPException(422, "Die Bedingungen hängen im Kreis voneinander ab")
    row = db.scalar(select(AvailabilityRule).where(AvailabilityRule.element_type == el.type,
                                                   AvailabilityRule.element_id == el.id))
    if tree is None:
        if row is not None:
            db.delete(row)
    elif row is None:
        db.add(AvailabilityRule(channel_id=ctx.ch.id, element_type=el.type, element_id=el.id, tree=tree,
                                created_by=user.id, created_at=utcnow()))
    else:
        row.tree, row.updated_at = tree, utcnow()
    audit(db, user, "availability.rule", f"{el.type}:{el.id}",
          {"channel_id": ctx.ch.id, "conditions": len(list(progress._walk_leaves(tree))) if tree else 0},
          ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx)
    prog = progress.Progress(db, [ctx.ch.id])
    return {"availability": {"tree": tree, "text": prog.describe(el.type, el.id, ctx.ch.id)} if tree else None}


# =========================================================================== Schüler/innen
@router.post("/channels/{channel_id}/elements/{element_type}/{element_id}/done")
def mark_done(channel_id: int, element_type: str, element_id: int, body: DoneIn, request: Request,
              user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, write=True)
    if not ctx.student:
        raise HTTPException(403, "Nur Teilnehmende haken ab")
    el = _element_or_404(db, ctx, element_type, element_id)
    rule = db.scalar(select(CompletionRule).where(CompletionRule.element_type == el.type,
                                                  CompletionRule.element_id == el.id))
    if rule is None or rule.mode != "manual":
        raise HTTPException(409, "Dieses Element wird nicht von Hand abgehakt")
    if el.type == progress.ELEMENT_ITEM:                      # sichtbar und nicht gesperrt?
        fc._visible_item_or_404(db, ctx, el.id, fc.Clock(ctx.snap, channels=[ctx.ch]))
    mark = db.scalar(select(CompletionMark).where(CompletionMark.element_type == el.type,
                                                  CompletionMark.element_id == el.id,
                                                  CompletionMark.user_id == user.id))
    if body.done and mark is None:
        db.add(CompletionMark(channel_id=ctx.ch.id, element_type=el.type, element_id=el.id, user_id=user.id,
                              done_at=utcnow()))
    elif not body.done and mark is not None:
        db.delete(mark)
    audit(db, user, "completion.mark", f"{el.type}:{el.id}", {"channel_id": ctx.ch.id, "done": body.done},
          ip=client_ip(request))
    db.commit()
    fc._notify(db, ctx, teachers_only=True)
    return {"done": body.done}


@router.get("/channels/{channel_id}/progress/me")
def my_progress(channel_id: int, student_id: Optional[str] = Query(None, max_length=40, description="Eltern: Kind"),
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = fc._ctx(db, user, channel_id, child=student_id)
    if ctx.parent:
        if not ctx.ch.setting("progress_parents"):
            raise HTTPException(403, "Die Lehrkraft hat den Lernfortschritt für Eltern nicht freigegeben")
    elif not ctx.student:
        raise HTTPException(403, "Den Fortschritt sehen Teilnehmende; Lehrende nutzen die Übersicht")
    return _pupil_progress(db, ctx, ctx.pupil_uid)


# =========================================================================== Lehrende: Übersicht
def _students(db: Session, ctx: fc.Ctx) -> list[dict[str, Any]]:
    """Teilnehmende des Kursraums (Stundenplan + eingetragene, ohne Ausgetragene) mit Konto, sortiert."""
    idx = logic.index_for(ctx.school)
    sids = logic.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "") if ctx.spec else []
    accounts = fc._child_accounts(db, sids)
    extra = db.execute(select(ChannelExtraMember.user_id, ChannelExtraMember.role)
                       .where(ChannelExtraMember.channel_id == ctx.ch.id)).all()
    excluded = {uid for uid, role in extra if role == fc.EXCLUDED}
    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for sid in sids:
        acc = accounts.get(sid)
        if acc is not None and acc.id in excluded:
            continue
        st = idx.students.get(sid)
        rows.append({"student_id": sid, "user_id": acc.id if acc else None, "name": st.name if st else sid,
                     "class_id": st.class_id if st else None})
        if acc is not None:
            seen.add(acc.id)
    extra_ids = [uid for uid, role in extra if role == fc.STUDENT and uid not in seen]
    if extra_ids:
        from schulmanager.server.db_models import User

        for u in db.scalars(select(User).where(User.id.in_(extra_ids))):
            st = idx.students.get(u.student_id or "")
            rows.append({"student_id": u.student_id, "user_id": u.id, "name": u.display_name or u.username,
                         "class_id": st.class_id if st else None})
    rows.sort(key=lambda r: ((r["class_id"] or ""), r["name"].lower()))
    return rows


@router.get("/channels/{channel_id}/progress")
def progress_table(channel_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Tabelle Schüler/in × Elemente mit Abschlussbedingung (``done``: ``true``/``false``; ``null`` = nicht einsehbar
    oder kein Konto)."""
    ctx = fc._ctx(db, user, channel_id, manage=True)
    prog = progress.Progress(db, [ctx.ch.id])
    elements = _all_elements(db, ctx.ch.id)
    tracked = [el for key, el in elements.items() if key in prog.rules]
    students = _students(db, ctx)
    uids = [s["user_id"] for s in students if s["user_id"]]
    prog = progress.Progress(db, [ctx.ch.id], uids)
    prog.prefetch(uids, [(e.type, e.id) for e in tracked])
    hidden_for_me: set[tuple[str, int]] = set()
    for el in tracked:
        rule = prog.rule(el.type, el.id)
        if rule is None or rule.mode in ("manual", "viewed"):
            continue
        provider = progress.providers().get(el.type)
        getter = getattr(provider, "created_by", None)
        owner = getter(db, el.id) if callable(getter) else None
        if not fc._responsible_for(ctx.user, ctx.ch, ctx.role, ctx.manages_all, owner):
            hidden_for_me.add((el.type, el.id))
    out_students = []
    totals = {(e.type, e.id): [0, 0] for e in tracked}
    for s in students:
        cells: dict[str, Optional[bool]] = {}
        done = total = 0
        for el in tracked:
            key = (el.type, el.id)
            if not s["user_id"] or key in hidden_for_me:
                cells[f"{el.type}:{el.id}"] = None
                continue
            state = bool(prog.done(s["user_id"], el.type, el.id))
            cells[f"{el.type}:{el.id}"] = state
            total += 1
            done += 1 if state else 0
            totals[key][1] += 1
            totals[key][0] += 1 if state else 0
        out_students.append({**s, "has_account": s["user_id"] is not None, "cells": cells, "done": done,
                             "total": total, "percent": round(done * 100 / total) if total else 0})
    return {
        "elements": [{"element_type": e.type, "element_id": e.id, "key": f"{e.type}:{e.id}", "title": e.title,
                      "kind_label": e.kind_label, "folder_id": e.folder_id,
                      "mode": prog.rule(e.type, e.id).mode,                       # type: ignore[union-attr]
                      "mode_label": progress.MODE_LABELS[prog.rule(e.type, e.id).mode],  # type: ignore[union-attr]
                      "done": totals[(e.type, e.id)][0], "of": totals[(e.type, e.id)][1],
                      "restricted": (e.type, e.id) in hidden_for_me} for e in tracked],
        "students": out_students, "classes": sorted({s["class_id"] for s in students if s["class_id"]}),
        "progress_parents": bool(ctx.ch.setting("progress_parents")), "generated_at": iso(utcnow()),
    }
