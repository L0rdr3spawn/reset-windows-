"""Aufgaben im Kursraum: Abgaben, Bewertung mit Raster/Punkten/Note, Fristverlängerung, Wiederabgabe, Gruppenabgabe
und Gruppen im Kursraum (Ergänzung zu ``features_channels.py``, Migration 0036).

Funktionen (Moodle-Vergleich: ``assign``, ``grade/grading/form/rubric|guide``, ``group``)

* **Bewertungsraster / Leitfaden**: je Aufgabe ein Raster (Kopie einer Vorlage der Lehrkraft, ``/grading/templates``);
  Stufen anklicken → Punkte → Note nach Notenschlüssel (``schulmanager/grading.py``). Schüler/innen sehen das Raster
  vorab und das ausgefüllte nach der Bewertung, Eltern nur bei Freigabe (``show_parents``).
* **Fristverlängerung** je Schüler/in oder Gruppe (``…/extensions``) mit Hinweis auf Nachteilsausgleich (``support``).
* **Wiederabgabe**: „Überarbeitung anfordern“ (``status="zurueckgegeben"``) legt eine neue Version an; frühere Versionen
  mit Rückmeldung bleiben sichtbar (``versions``).
* **Späte Abgaben** zulassen/sperren (``allow_late`` der Aufgabe), Kennzeichnung ``late``.
* **Gruppen**: Einteilungen mit Gruppen (von Hand/zufällig/nach Größe), Gruppenabgabe (jedes Mitglied hat eine Zeile mit
  demselben Inhalt, siehe ``assignment_tools``), gemeinsame Bewertung mit Einzelanpassung, Material/Ordner nur für
  bestimmte Gruppen (``channel_groups``).
* **Ergebnisse** für das Notenbuch: ``GET /channels/{id}/assignment-results`` bzw.
  ``assignment_tools.list_results``.

Datenschutz wie in ``features_channels.py``: Freitexte, Raster und Begründungen nur verschlüsselt, Audit ohne Inhalte.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from schulmanager import channels as logic
from schulmanager import grading
from schulmanager.server import assignment_tools as at
from schulmanager.server import channel_groups as cg
from schulmanager.server import files
from schulmanager.server.audit import audit
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import User
from schulmanager.server.deps import AuthUser, client_ip, current_user
from schulmanager.server.feature_models.assignments import (AssignmentExtension, AssignmentSettings,
                                                            AssignmentSubmissionVersion, GradingTemplate)
from schulmanager.server.feature_models.channel_groups import ChannelGroup, ChannelGroupMember, ChannelGroupSet
from schulmanager.server.feature_models.channels import (AssignmentSubmission, ChannelExtraMember, ChannelFolder,
                                                         ChannelItem)

from .features_channels import (EXCLUDED, MAX_ATTACHMENTS, MAX_FEEDBACK, MAX_GRADE, MAX_SUBMISSION_TEXT, REF_SUBMISSION,
                                STUDENT, Clock, Ctx, _chunks, _ctx, _notify, _single_item_out, _to_utc, _user_names,
                                _visible_item_or_404, takes_submissions)
from .features_common import has

router = APIRouter(tags=["Kursräume – Aufgaben"])

MAX_GROUPS = 60                 # Gruppen je Kursraum
MAX_SETS = 10                   # Einteilungen je Kursraum
MAX_REASON = 500
MAX_TEMPLATES = 100             # Vorlagen je Lehrkraft
OPEN_STATUSES = ("abgegeben", "verspaetet")


# =========================================================================== Eingaben
class SubmissionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field("", max_length=MAX_SUBMISSION_TEXT)
    file_ids: list[str] = Field(default_factory=list, max_length=MAX_ATTACHMENTS)


class FeedbackIn(BaseModel):
    """Rückmeldung/Bewertung. ``rubric`` = ausgefülltes Raster (``{kriterium: {level|points, comment}}``);
    ``scope="self"`` = Einzelanpassung innerhalb einer Gruppenbewertung; ``zurueckgegeben`` = Überarbeitung anfordern."""
    model_config = ConfigDict(extra="forbid")
    feedback: str = Field("", max_length=MAX_FEEDBACK)
    grade: str = Field("", max_length=MAX_GRADE)
    status: Literal["bewertet", "zurueckgegeben"] = "bewertet"
    file_ids: Optional[list[str]] = Field(None, max_length=10)
    points: Optional[float] = Field(None, ge=0, le=grading.MAX_POINTS)
    rubric: Optional[dict[str, Any]] = None
    auto_grade: bool = True
    scope: Literal["group", "self"] = "group"
    overwrite_individual: bool = False
    revision_due_at: Optional[datetime] = None


class SettingsIn(BaseModel):
    """Felder, die fehlen, bleiben unverändert; ``null`` bei ``group_set_id``/``max_points``/``grade_scale`` = entfernen."""
    model_config = ConfigDict(extra="forbid")
    group_mode: Optional[bool] = None
    group_set_id: Optional[int] = None
    max_points: Optional[float] = Field(None, gt=0, le=grading.MAX_POINTS)
    grade_scale: Optional[dict[str, Any]] = None
    rubric: Optional[dict[str, Any]] = None
    rubric_title: Optional[str] = Field(None, max_length=200)
    template_id: Optional[int] = None
    clear_rubric: bool = False
    show_parents: Optional[bool] = None


class TemplateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    rubric: dict[str, Any]
    grade_scale: Optional[dict[str, Any]] = None


class ExtensionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    due_at: datetime
    reason: str = Field("", max_length=MAX_REASON)


class GroupSetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)


class GroupIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)


class MembersIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_ids: list[int] = Field(default_factory=list, max_length=500)


class AutoGroupsIn(BaseModel):
    """Einteilung: ``count`` Gruppen **oder** Gruppen der Größe ``size``; ``shuffle`` = zufällig, sonst alphabetisch;
    ``mode="new"`` ersetzt alle Gruppen der Einteilung, ``"fill"`` verteilt nur die noch nicht eingeteilten."""
    model_config = ConfigDict(extra="forbid")
    count: Optional[int] = Field(None, ge=1, le=MAX_GROUPS)
    size: Optional[int] = Field(None, ge=1, le=200)
    shuffle: bool = True
    mode: Literal["new", "fill"] = "new"
    name_prefix: str = Field("Gruppe", min_length=1, max_length=60)
    seed: Optional[int] = None


class GateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_ids: list[int] = Field(default_factory=list, max_length=MAX_GROUPS)


# =========================================================================== Hilfen
def _clean_name(value: str, what: str = "Name") -> str:
    name = logic.clean_name(value, 120)
    if not name:
        raise HTTPException(422, f"Bitte einen {what} angeben")
    return name


def _responsible_item(db: Session, ctx: Ctx, item_id: int, clock: Clock) -> ChannelItem:
    """Aufgabe, die die Lehrkraft bewerten darf (Klassenräume: nur wer sie gestellt hat)."""
    item, _ = _visible_item_or_404(db, ctx, item_id, clock)
    if not takes_submissions(item):
        raise HTTPException(422, "Zu diesem Material ist keine Abgabe vorgesehen")
    if not ctx.responsible(item):
        raise HTTPException(403, "Das darf nur die Lehrkraft, die die Aufgabe gestellt hat")
    return item


def _assignment(db: Session, ctx: Ctx, item_id: int, clock: Clock) -> ChannelItem:
    item, _ = _visible_item_or_404(db, ctx, item_id, clock)
    if not takes_submissions(item):
        raise HTTPException(422, "Zu diesem Material ist keine Abgabe vorgesehen")
    return item


def _roster(db: Session, ctx: Ctx) -> list[dict[str, Any]]:
    """Teilnehmende Schüler/innen eines Kursraums (Planungsdokument + Zusatzmitglieder, ohne Ausgetragene)."""
    idx = logic.index_for(ctx.school)
    student_ids = logic.channel_student_ids(ctx.school, ctx.ch.kind, ctx.ch.ref or "") if ctx.spec else []
    accounts: dict[str, int] = {}
    for chunk in _chunks(student_ids):
        for uid, sid in db.execute(select(User.id, User.student_id).where(
                User.student_id.in_(chunk), User.role == "schueler", User.active.is_(True)).order_by(User.id)):
            accounts.setdefault(sid, uid)
    extra = db.execute(select(ChannelExtraMember.user_id, User.display_name, User.username, User.student_id)
                       .join(User, User.id == ChannelExtraMember.user_id)
                       .where(ChannelExtraMember.channel_id == ctx.ch.id, ChannelExtraMember.role == STUDENT)).all()
    excluded = set(db.scalars(select(ChannelExtraMember.user_id).where(
        ChannelExtraMember.channel_id == ctx.ch.id, ChannelExtraMember.role == EXCLUDED)))
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for sid in sorted(student_ids, key=lambda s: (idx.students[s].class_id, idx.students[s].name)
                      if s in idx.students else ("", s)):
        st = idx.students.get(sid)
        uid = accounts.get(sid)
        if uid in excluded:
            continue
        out.append({"student_id": sid, "name": st.name if st else sid, "class_id": st.class_id if st else None,
                    "user_id": uid, "has_account": uid is not None, "member": True})
        if uid:
            seen.add(uid)
    for uid, dn, un, sid in extra:
        if uid in seen:
            continue
        st = idx.students.get(sid) if sid else None
        out.append({"student_id": sid, "name": dn or un, "class_id": st.class_id if st else None, "user_id": uid,
                    "has_account": True, "member": True})
        seen.add(uid)
    return out


def _nta_hints(db: Session, user: AuthUser, snap: Any, student_ids: list[str]) -> dict[str, list[str]]:
    """Nachteilsausgleich-Hinweise je Schüler/in (nur Art/Minuten; nur für Berechtigte, nie Diagnosen)."""
    from schulmanager.server.feature_models.support import StudentSupport

    from .features_support import _cat_map, _label, _mode, _teacher_visible, _valid_on

    ids = [s for s in dict.fromkeys(student_ids) if s]
    if not ids or not (has(user, "support.hints") or has(user, "support.read")):
        return {}
    today = utcnow().date().isoformat()
    cats = _cat_map(db)
    modes: dict[str, Optional[str]] = {}
    out: dict[str, list[str]] = {}
    for chunk in _chunks(ids):
        for r in db.scalars(select(StudentSupport).where(StudentSupport.student_id.in_(chunk))):
            cat = cats.get(r.catalog_id or 0)
            kind = cat.kind if cat is not None else r.kind
            if kind != "nachteilsausgleich" or not _valid_on(r, today):
                continue
            if r.student_id not in modes:
                modes[r.student_id] = _mode(db, user, r.student_id, snap)
            mode = modes[r.student_id]
            if mode is None or (mode == "hints" and not _teacher_visible(r, cat)):
                continue
            label = _label(r, cat)
            if r.minutes:
                label = f"{label} (+{r.minutes} min)"
            if label not in out.setdefault(r.student_id, []):
                out[r.student_id].append(label)
    return out


def _due_for(item: ChannelItem, override: Optional[datetime], sub: Optional[AssignmentSubmission]) -> Optional[datetime]:
    """Frist, die für diese Abgabe gilt: bei einer Überarbeitung (ab Version 2) deren eigene Frist, sonst die
    allgemeine Frist bzw. die verlängerte."""
    if sub is not None and (sub.attempt or 1) > 1:
        return sub.revision_due_at
    return at.effective_due(item.due_at, override)


def _settings_out(db: Session, settings: Optional[AssignmentSettings], item_id: int, *, with_counts: bool = False
                  ) -> dict[str, Any]:
    rubric = settings.rubric() if settings is not None else None
    scale = at.scale_of(settings)
    out: dict[str, Any] = {
        "group_mode": bool(settings and settings.group_mode),
        "group_set_id": settings.group_set_id if settings is not None else None,
        "max_points": at.max_points_of(settings),
        "free_max_points": settings.max_points if settings is not None else None,
        "rubric": rubric, "rubric_title": settings.rubric_title if settings is not None else "",
        "template_id": settings.template_id if settings is not None else None,
        "grade_scale": scale,
        "scale_steps": [{"min": m, "label": label} for m, label in grading.scale_steps(scale)],
        "show_parents": bool(settings and settings.show_parents),
    }
    if with_counts:
        out["submission_count"] = at.count_rows(db, item_id)
        out["has_rubric_grades"] = bool(db.scalar(select(AssignmentSubmission.id).where(
            AssignmentSubmission.item_id == item_id, AssignmentSubmission.rubric_enc != "").limit(1)))
    return out


def _fill_of(sub: Any) -> Optional[dict[str, Any]]:
    raw = sub.read_text("rubric")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _version_out(v: AssignmentSubmissionVersion, infos: dict[str, dict], names: dict[int, str], hide_scores: bool
                 ) -> dict[str, Any]:
    return {"attempt": v.attempt, "status": v.status, "submitted_at": iso(v.submitted_at),
            "text": v.read_text("text"), "files": [infos[i] for i in v.file_ids or [] if i in infos],
            "feedback": v.read_text("feedback"), "grade": v.read_text("grade"),
            "points": None if hide_scores else v.points, "max_points": None if hide_scores else v.max_points,
            "rubric": None if hide_scores else _fill_of(v),
            "feedback_files": [infos[i] for i in v.feedback_file_ids or [] if i in infos],
            "feedback_at": iso(v.feedback_at), "feedback_by_name": names.get(v.feedback_by or 0, ""),
            "closed_at": iso(v.closed_at)}


def _submission_out(db: Session, ctx: Ctx, item: ChannelItem, sub: AssignmentSubmission, clock: Clock, *,
                    names: Optional[dict[int, str]] = None, settings: Optional[AssignmentSettings] = None,
                    versions: Optional[list[AssignmentSubmissionVersion]] = None,
                    override: Optional[datetime] = None) -> dict[str, Any]:
    versions = versions if versions is not None else at.versions_of(db, [sub.id]).get(sub.id, [])
    ids = [*(sub.file_ids or []), *(sub.feedback_file_ids or [])]
    for v in versions:
        ids.extend([*(v.file_ids or []), *(v.feedback_file_ids or [])])
    infos = {f["id"]: f for f in files.files_info(db, ids, ctx.user, check_access=False)}
    names = names if names is not None else {}
    due = _due_for(item, override, sub)
    status = logic.submission_status(due, sub.submitted_at, sub.status, clock.now)
    hide = ctx.parent and not (settings is not None and settings.show_parents)
    late = bool(due is not None and sub.submitted_at is not None and sub.submitted_at > due)
    return {
        "id": sub.id, "item_id": sub.item_id, "status": status,
        "status_label": logic.SUBMISSION_LABELS.get(status, status), "submitted_at": iso(sub.submitted_at),
        "late": late, "text": sub.read_text("text"),
        "files": [infos[i] for i in sub.file_ids or [] if i in infos],
        "feedback": sub.read_text("feedback"), "grade": sub.read_text("grade"),
        "feedback_files": [infos[i] for i in sub.feedback_file_ids or [] if i in infos],
        "feedback_at": iso(sub.feedback_at), "feedback_by_name": names.get(sub.feedback_by or 0, ""),
        "updated_at": iso(sub.updated_at),
        "can_edit": ctx.student and sub.status != "bewertet" and not ctx.ch.archived,
        "attempt": sub.attempt or 1, "revision_due_at": iso(sub.revision_due_at) if (sub.attempt or 1) > 1 else None,
        "points": None if hide else sub.points, "max_points": None if hide else sub.max_points,
        "percent": None if hide else grading.percent(sub.points, sub.max_points),
        "rubric": None if hide else _fill_of(sub), "individual": bool(sub.individual), "group_id": sub.group_id,
        "versions": [_version_out(v, infos, names, hide) for v in versions],
    }


def _group_out(db: Session, group: Optional[ChannelGroup], *, with_members: bool = True) -> Optional[dict[str, Any]]:
    if group is None:
        return None
    out: dict[str, Any] = {"id": group.id, "name": group.name, "set_id": group.set_id}
    if with_members:
        uids = cg.members_of(db, group.id)
        names = _user_names(db, uids)
        out["members"] = [{"user_id": u, "name": names.get(u, "")} for u in uids]
    return out


def _extension_out(db: Session, ext: AssignmentExtension, names: dict[int, str], group_names: dict[int, str]
                   ) -> dict[str, Any]:
    return {"id": ext.id, "user_id": ext.user_id, "group_id": ext.group_id,
            "name": names.get(ext.user_id or 0, "") if ext.user_id else group_names.get(ext.group_id or 0, ""),
            "due_at": iso(ext.due_at), "reason": ext.read_text("reason"),
            "created_by_name": names.get(ext.created_by or 0, ""), "created_at": iso(ext.created_at)}


def _restatus(db: Session, item: ChannelItem, user_ids: Optional[list[int]] = None) -> None:
    """Gleicht gespeicherte Abgabe-Status (abgegeben/verspätet) nach einer Änderung der Fristverlängerung an."""
    stmt = select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id,
                                              AssignmentSubmission.status.in_(OPEN_STATUSES),
                                              AssignmentSubmission.attempt <= 1)
    if user_ids is not None:
        stmt = stmt.where(AssignmentSubmission.student_user_id.in_(user_ids or [0]))
    for sub in db.scalars(stmt):
        ov = at.due_overrides(db, [item.id], sub.student_user_id).get(item.id)
        want = logic.submit_status(at.effective_due(item.due_at, ov), sub.submitted_at) \
            if sub.submitted_at else sub.status
        if want != sub.status:
            sub.status = want


# =========================================================================== Abgabe (Schüler/in)
@router.get("/channels/{channel_id}/items/{item_id}/submission")
def my_submission(channel_id: int, item_id: int, student_id: Optional[str] = Query(None, max_length=40),
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eigene Abgabe (Schüler/in) inkl. Rückmeldung, Raster, Versionen und Gruppe; Eltern: die des eigenen Kindes."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    if not ctx.pupil:
        raise HTTPException(403, "Abgaben gibt es nur für Teilnehmende")
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    item = _assignment(db, ctx, item_id, clock)
    settings = at.settings_for(db, item.id)
    uid = ctx.pupil_uid
    sub = db.scalar(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id,
                                                       AssignmentSubmission.student_user_id == uid)) if uid else None
    group = at.group_for_user(db, settings, uid)
    if sub is not None and settings is not None and settings.group_mode and sub.group_id != (group.id if group else None):
        sub = None                            # Zeile aus einer früheren Gruppe
    ov = at.due_overrides(db, [item.id], uid).get(item.id) if uid else None
    ext = at.extension_hint(db, item.id, uid)
    due = _due_for(item, ov, sub)
    status = logic.submission_status(due, sub.submitted_at if sub else None, sub.status if sub else None, clock.now)
    needs_group = bool(settings is not None and settings.group_mode and group is None)
    can_submit = (ctx.student and not ctx.ch.archived and not needs_group
                  and (sub is None or sub.status != "bewertet")
                  and (item.allow_late or due is None or clock.now <= due))
    names = _user_names(db, [sub.feedback_by]) if sub else {}
    versions = at.versions_of(db, [sub.id]).get(sub.id, []) if sub else []
    if versions:
        names.update(_user_names(db, [v.feedback_by for v in versions]))
    return {"item_id": item.id, "status": status, "status_label": logic.SUBMISSION_LABELS.get(status, status),
            "due_at": iso(item.due_at), "effective_due_at": iso(due),
            "extension": {"due_at": iso(ext.due_at), "reason": ext.read_text("reason")} if ext else None,
            "allow_late": bool(item.allow_late), "can_submit": bool(can_submit), "needs_group": needs_group,
            "group": _group_out(db, group), "settings": _settings_out(db, settings, item.id),
            "submission": _submission_out(db, ctx, item, sub, clock, names=names, settings=settings,
                                          versions=versions, override=ov) if sub else None}


@router.put("/channels/{channel_id}/items/{item_id}/submission")
def submit(channel_id: int, item_id: int, body: SubmissionIn, request: Request,
           user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Abgeben bzw. Abgabe ersetzen (Text + eigene Uploads ``POST /files?purpose=submission``); nach Fristende
    „verspätet“ (wenn erlaubt), nicht mehr nach der Bewertung. Gruppenabgabe: gilt für alle Mitglieder."""
    ctx = _ctx(db, user, channel_id, write=True)
    if not ctx.student:
        raise HTTPException(403, "Abgeben können nur Teilnehmende")
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    item = _assignment(db, ctx, item_id, clock)
    settings = at.settings_for(db, item.id)
    group = at.group_for_user(db, settings, user.id)
    if settings is not None and settings.group_mode:
        if group is None:
            raise HTTPException(409, "Sie sind noch keiner Gruppe zugeordnet – bitte die Lehrkraft fragen")
        at.normalize_item_groups(db, item, settings)
    text = logic.clean_text(body.text, MAX_SUBMISSION_TEXT)
    file_ids = list(dict.fromkeys(body.file_ids))
    if not text and not file_ids:
        raise HTTPException(422, "Bitte einen Text eingeben oder Dateien anhängen")
    sub = db.scalar(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id,
                                                       AssignmentSubmission.student_user_id == user.id))
    if sub is not None and sub.status == "bewertet":
        raise HTTPException(409, "Die Abgabe ist bereits bewertet und kann nicht mehr geändert werden")
    ov = at.due_overrides(db, [item.id], user.id).get(item.id)
    due = _due_for(item, ov, sub)
    if due is not None and clock.now > due and not item.allow_late:
        raise HTTPException(409, "Die Abgabefrist ist abgelaufen")
    now = clock.now.replace(microsecond=0)         # dieselbe Uhr wie die Fristprüfung
    was_revision = sub is not None and sub.status == "zurueckgegeben"
    if sub is None:
        sub = AssignmentSubmission(item_id=item.id, student_user_id=user.id, student_id=user.student_id,
                                   group_id=group.id if group else None, created_at=now, text_enc="",
                                   feedback_enc="", grade_enc="", rubric_enc="", attempt=1)
        db.add(sub)
        try:
            db.flush()
        except IntegrityError:  # gleichzeitige Abgabe aus zwei Tabs
            db.rollback()
            raise HTTPException(409, "Die Abgabe wurde gerade gespeichert – bitte neu laden") from None
    old_ids = list(sub.file_ids or [])
    added = [i for i in file_ids if i not in old_ids]
    removed = [i for i in old_ids if i not in file_ids]
    if added:
        files.attach_many(db, added, user, REF_SUBMISSION, sub.id, max_files=MAX_ATTACHMENTS)
    if removed:
        keep = at.versioned_file_ids(db, item.id)           # Dateien früherer Versionen bleiben erhalten
        for fid in removed:
            if fid not in keep:
                files.delete(db, fid, user, hard=True)
    sub.file_ids = file_ids or None
    sub.write_text("text", text)
    sub.status = logic.submit_status(due, clock.now)
    sub.submitted_at = now
    sub.updated_at = now
    if was_revision:
        at.clear_results(sub)              # die Bewertung der letzten Version steht in deren Version
    if group is not None:
        sub.group_id = group.id
        at.propagate(db, sub)
        if was_revision:
            for r in at.group_rows(db, item.id, group.id):
                at.clear_results(r)
    audit(db, user, "submission.submit", f"submission:{sub.id}",
          {"channel_id": ctx.ch.id, "item_id": item.id, "status": sub.status, "files": len(file_ids),
           "attempt": sub.attempt or 1, "group_id": sub.group_id}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx, teachers_only=True)
    return _submission_out(db, ctx, item, sub, clock, settings=settings, override=ov)


@router.delete("/channels/{channel_id}/items/{item_id}/submission")
def withdraw(channel_id: int, item_id: int, request: Request, user: AuthUser = Depends(current_user),
             db: Session = Depends(get_db)) -> dict:
    """Abgabe zurückziehen (solange nicht bewertet und keine Überarbeitung angefordert); Dateien werden gelöscht.
    Gruppenabgabe: zieht die Abgabe der ganzen Gruppe zurück."""
    ctx = _ctx(db, user, channel_id, write=True)
    if not ctx.student:
        raise HTTPException(403, "Nur für Teilnehmende")
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    item = _assignment(db, ctx, item_id, clock)
    sub = db.scalar(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id,
                                                       AssignmentSubmission.student_user_id == user.id))
    if sub is None:
        raise HTTPException(404, "Keine Abgabe vorhanden")
    rows = at.group_rows(db, item.id, sub.group_id) if sub.group_id else [sub]
    if any(r.status == "bewertet" for r in rows):
        raise HTTPException(409, "Die Abgabe ist bereits bewertet")
    if any((r.attempt or 1) > 1 for r in rows) or at.versions_of(db, [r.id for r in rows]):
        raise HTTPException(409, "Nach einer Überarbeitung kann die Abgabe nicht mehr zurückgezogen werden")
    for r in rows:
        files.delete_for_ref(db, REF_SUBMISSION, r.id, hard=True)
    audit(db, user, "submission.withdraw", f"submission:{sub.id}",
          {"channel_id": ctx.ch.id, "item_id": item.id, "group_id": sub.group_id}, ip=client_ip(request))
    for r in rows:
        db.delete(r)
    db.commit()
    _notify(db, ctx, teachers_only=True)
    return {"deleted": True}


# =========================================================================== Bewertungsübersicht (Lehrende)
@router.get("/channels/{channel_id}/items/{item_id}/submissions")
def list_submissions(channel_id: int, item_id: int, user: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> dict:
    """Tabelle „Abgaben“ einer Aufgabe (nur Lehrende; Klassenräume: nur wer die Aufgabe gestellt hat): alle
    Teilnehmenden mit Status (abgegeben, verspätet, fehlt, bewertet), Gruppe, Frist, Hinweis Nachteilsausgleich."""
    ctx = _ctx(db, user, channel_id)
    if not ctx.teacher:
        raise HTTPException(403, "Abgaben sehen nur die Lehrenden dieses Kursraums")
    clock = Clock(ctx.snap, channels=[ctx.ch])
    item = _assignment(db, ctx, item_id, clock)
    if not ctx.responsible(item):
        raise HTTPException(403, "Abgaben und Rückmeldungen sieht nur die Lehrkraft, die die Aufgabe gestellt hat")
    settings = at.settings_for(db, item.id)
    roster = _roster(db, ctx)
    subs = {s.student_user_id: s for s in db.scalars(select(AssignmentSubmission)
                                                     .where(AssignmentSubmission.item_id == item.id))}
    versions = at.versions_of(db, [s.id for s in subs.values()])
    exts = list(db.scalars(select(AssignmentExtension).where(AssignmentExtension.item_id == item.id)))
    member_group: dict[int, int] = {}
    groups: dict[int, ChannelGroup] = {}
    if settings is not None and settings.group_mode and settings.group_set_id:
        for uid, gid in db.execute(select(ChannelGroupMember.user_id, ChannelGroupMember.group_id)
                                   .where(ChannelGroupMember.set_id == settings.group_set_id)):
            member_group[uid] = gid
        groups = {g.id: g for g in db.scalars(select(ChannelGroup).where(
            ChannelGroup.set_id == settings.group_set_id).order_by(ChannelGroup.position, ChannelGroup.id))}
    all_groups = {g.id: g for g in db.scalars(select(ChannelGroup).where(ChannelGroup.channel_id == ctx.ch.id))}
    all_member_groups = defaultdict(set)
    for uid, gid in db.execute(select(ChannelGroupMember.user_id, ChannelGroupMember.group_id)
                               .where(ChannelGroupMember.channel_id == ctx.ch.id)):
        all_member_groups[uid].add(gid)
    names = _user_names(db, [*subs, *(s.feedback_by for s in subs.values()), *(e.user_id for e in exts),
                             *(e.created_by for e in exts),
                             *(v.feedback_by for vs in versions.values() for v in vs)])
    hints = _nta_hints(db, user, ctx.snap, [r["student_id"] for r in roster if r["student_id"]])
    rows: list[dict[str, Any]] = []
    seen_users: set[int] = set()

    def ext_for(uid: Optional[int]) -> Optional[AssignmentExtension]:
        if not uid:
            return None
        mine = [e for e in exts if e.user_id == uid or (e.group_id and e.group_id in all_member_groups.get(uid, ()))]
        return max(mine, key=lambda e: e.due_at, default=None)

    def row(name: str, class_id: Optional[str], student_id: Optional[str], uid: Optional[int],
            member: bool = True) -> dict:
        sub = subs.get(uid) if uid else None
        ext = ext_for(uid)
        due = _due_for(item, ext.due_at if ext else None, sub)
        status = logic.submission_status(due, sub.submitted_at if sub else None, sub.status if sub else None, clock.now)
        gid = member_group.get(uid) if uid else None
        g = groups.get(gid) if gid else None
        out = _submission_out(db, ctx, item, sub, clock, names=names, settings=settings,
                              versions=versions.get(sub.id, []), override=ext.due_at if ext else None) if sub else None
        entry = {"student_id": student_id, "name": name, "class_id": class_id, "user_id": uid,
                 "has_account": uid is not None, "member": member, "status": status,
                 "status_label": logic.SUBMISSION_LABELS.get(status, status),
                 "late": bool(out and out["late"]), "due_at": iso(due),
                 "extension": ({"id": ext.id, "due_at": iso(ext.due_at), "reason": ext.read_text("reason"),
                                "kind": "group" if ext.group_id else "user"} if ext else None),
                 "group": {"id": g.id, "name": g.name} if g else None,
                 "support": hints.get(student_id or "", []), "submission": out}
        if uid:
            seen_users.add(uid)
        return entry

    for r in roster:
        rows.append(row(r["name"], r["class_id"], r["student_id"], r["user_id"]))
    for uid, sub in subs.items():  # Abgaben von Schüler/innen, die nicht mehr im Kurs sind
        if uid not in seen_users:
            rows.append(row(names.get(uid, f"Konto {uid}"), None, sub.student_id, uid, member=False))
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
        if r["late"]:
            counts["late"] += 1
    group_names = {g.id: g.name for g in all_groups.values()}
    return {"item": _single_item_out(db, ctx, item, clock), "rows": rows, "counts": dict(counts),
            "total": len(rows), "settings": _settings_out(db, settings, item.id, with_counts=True),
            "groups": [{"id": g.id, "name": g.name} for g in groups.values()],
            "without_group": sum(1 for r in rows if settings is not None and settings.group_mode
                                 and r["user_id"] and r["group"] is None),
            "extensions": [_extension_out(db, e, names, group_names) for e in exts]}


def _apply_result(row: AssignmentSubmission, *, feedback: str, grade: str, fill: Optional[dict[str, Any]],
                  points: Optional[float], top: Optional[float], status: str, files_ids: Optional[list[str]],
                  user: AuthUser, now: datetime) -> None:
    row.write_text("feedback", feedback)
    row.write_text("grade", grade)
    row.write_text("rubric", json.dumps(fill, ensure_ascii=False) if fill else "")
    row.points = points
    row.max_points = top if points is not None else None
    if files_ids is not None:
        row.feedback_file_ids = files_ids or None
    row.status = status
    row.feedback_by = user.id
    row.feedback_at = now
    row.updated_at = now


def _open_revision(db: Session, row: AssignmentSubmission, due: Optional[datetime]) -> None:
    """Hält die Version samt Rückmeldung fest und öffnet die nächste. Rückmeldung/Note bleiben für die Überarbeitung
    sichtbar und werden erst bei der erneuten Abgabe geleert (:func:`at.clear_results`)."""
    at.snapshot_version(db, row)
    row.attempt = (row.attempt or 1) + 1
    row.revision_due_at = due
    row.status = "zurueckgegeben"


@router.put("/channels/{channel_id}/submissions/{submission_id}/feedback")
def give_feedback(channel_id: int, submission_id: int, body: FeedbackIn, request: Request,
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Rückmeldung + Bewertung (Freitext-Note, Punkte oder ausgefülltes Raster; Note automatisch aus den Punkten, wenn
    leer) bzw. „Überarbeitung anfordern“ (``zurueckgegeben``, optional neue Frist). Gruppenabgaben: gilt für die ganze
    Gruppe, mit ``scope="self"`` nur für diese Person (Einzelanpassung)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch])
    sub = db.get(AssignmentSubmission, submission_id)
    item = db.get(ChannelItem, sub.item_id) if sub else None
    if sub is None or item is None or item.channel_id != ctx.ch.id:
        raise HTTPException(404, "Abgabe nicht gefunden")
    if not ctx.responsible(item):
        raise HTTPException(403, "Abgaben und Rückmeldungen sieht nur die Lehrkraft, die die Aufgabe gestellt hat")
    if sub.submitted_at is None:
        raise HTTPException(409, "Es liegt noch keine Abgabe vor")
    settings = at.settings_for(db, item.id)
    rubric = settings.rubric() if settings is not None else None
    top = at.max_points_of(settings)
    feedback = logic.clean_text(body.feedback, MAX_FEEDBACK)
    grade = logic.clean_name(body.grade, MAX_GRADE)
    points: Optional[float] = None
    fill: Optional[dict[str, Any]] = None
    if body.rubric is not None and body.rubric:
        if not rubric:
            raise HTTPException(422, "Für diese Aufgabe gibt es kein Bewertungsraster")
        try:
            points, fill, complete = grading.score_fill(rubric, body.rubric)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        if body.status == "bewertet" and not complete:
            raise HTTPException(422, "Bitte jedes Kriterium des Rasters bewerten")
    elif body.points is not None:
        if rubric:
            raise HTTPException(422, "Die Punkte ergeben sich aus dem Raster")
        points = round(float(body.points), 2)
        if top is not None and points > top + 1e-9:
            raise HTTPException(422, f"Höchstens {grading.fmt_points(top)} Punkte")
    if points is not None and not grade and body.auto_grade and body.status == "bewertet":
        grade = at.grade_for_points(settings, points) or ""
    now = utcnow()
    prev = sub.status
    group_scope = bool(sub.group_id) and body.scope == "group"
    targets = [r for r in at.group_rows(db, item.id, sub.group_id)
               if r.id == sub.id or body.overwrite_individual or not r.individual] if group_scope else [sub]
    if body.status == "zurueckgegeben":
        rev_due = _to_utc(body.revision_due_at, "die neue Frist") if body.revision_due_at else None
        ov = at.due_overrides(db, [item.id], sub.student_user_id).get(item.id)
        general = _due_for(item, ov, sub)
        if rev_due is None and not item.allow_late and general is not None and general < clock.now:
            raise HTTPException(422, "Die Frist ist abgelaufen und späte Abgaben sind gesperrt – bitte eine neue Frist "
                                "für die Überarbeitung angeben")
    else:
        rev_due = None
    new_files: Optional[list[str]] = None
    if body.file_ids is not None:
        new_files = list(dict.fromkeys(body.file_ids))
        old_ids = list(sub.feedback_file_ids or [])
        added = [i for i in new_files if i not in old_ids]
        if added:
            files.attach_many(db, added, user, REF_SUBMISSION, sub.id, max_files=10)
        keep = at.versioned_file_ids(db, item.id)
        for fid in old_ids:
            if fid not in new_files and fid not in keep:
                files.delete(db, fid, user, hard=True)
    for r in targets:
        _apply_result(r, feedback=feedback, grade=grade, fill=fill, points=points, top=top, status=body.status,
                      files_ids=new_files, user=user, now=now)
        if sub.group_id:
            r.individual = body.scope == "self"
        if body.status == "zurueckgegeben":
            _open_revision(db, r, rev_due)
    audit(db, user, "submission.feedback", f"submission:{sub.id}",
          {"channel_id": ctx.ch.id, "item_id": item.id, "student_user_id": sub.student_user_id,
           "status": [prev, body.status], "points": points, "group": group_scope,
           "rows": [r.student_user_id for r in targets] if group_scope else None}, ip=client_ip(request))
    at.publish_to_gradebook(db, item)  # Notenbuch: Quelle „Aufgabe“ aktualisieren (Übernahme entscheidet die Lehrkraft)
    db.commit()
    _notify(db, ctx, teachers_only=True, extra_ids=[r.student_user_id for r in targets])
    from schulmanager.server import notification_hooks  # Glocke: Abgabe bewertet / zurückgegeben
    for r in targets:
        notification_hooks.submission_graded(db, ctx, item, r)
    return _submission_out(db, ctx, item, sub, clock, names=_user_names(db, [user.id]), settings=settings)


# =========================================================================== Einstellungen je Aufgabe
def _template_or_404(db: Session, user: AuthUser, template_id: int) -> GradingTemplate:
    tpl = db.get(GradingTemplate, template_id)
    if tpl is None or tpl.owner_user_id != user.id:
        raise HTTPException(404, "Vorlage nicht gefunden")
    return tpl


@router.get("/channels/{channel_id}/items/{item_id}/assignment")
def get_assignment_settings(channel_id: int, item_id: int, user: AuthUser = Depends(current_user),
                            db: Session = Depends(get_db)) -> dict:
    """Einstellungen der Aufgabe: Raster/Punkte/Notenschlüssel, Gruppenabgabe (Lehrende; Teilnehmende sehen das Raster
    auch über ``…/submission``)."""
    ctx = _ctx(db, user, channel_id)
    clock = Clock(ctx.snap, channels=[ctx.ch]).restrict(db, ctx)
    item = _assignment(db, ctx, item_id, clock)
    settings = at.settings_for(db, item.id)
    out = _settings_out(db, settings, item.id, with_counts=ctx.teacher)
    out["presets"] = [{"id": k, "label": v} for k, v in grading.PRESET_LABELS.items()]
    return out


@router.put("/channels/{channel_id}/items/{item_id}/assignment")
def put_assignment_settings(channel_id: int, item_id: int, body: SettingsIn, request: Request,
                            user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch])
    item = _responsible_item(db, ctx, item_id, clock)
    settings = at.get_or_create_settings(db, item.id)
    fields = body.model_fields_set
    has_rows = at.count_rows(db, item.id) > 0
    if "group_mode" in fields or "group_set_id" in fields:
        mode = body.group_mode if "group_mode" in fields else settings.group_mode
        set_id = body.group_set_id if "group_set_id" in fields else settings.group_set_id
        if mode and (set_id is None or not cg.set_exists(db, ctx.ch.id, set_id)):
            raise HTTPException(422, "Bitte eine Gruppeneinteilung wählen")
        if (bool(mode), set_id if mode else None) != (settings.group_mode, settings.group_set_id if settings.group_mode
                                                      else None) and has_rows:
            raise HTTPException(409, "Es liegen schon Abgaben vor – die Gruppenabgabe lässt sich nicht mehr ändern")
        settings.group_mode = bool(mode)
        settings.group_set_id = set_id if mode else None
    changed_rubric = False
    if body.template_id is not None:
        tpl = _template_or_404(db, user, body.template_id)
        new_rubric = tpl.rubric()
        if not new_rubric:
            raise HTTPException(422, "Die Vorlage ist leer")
        changed_rubric = True
        rubric_title = tpl.title
        if tpl.grade_scale:
            settings.grade_scale = tpl.grade_scale
        settings.template_id = tpl.id
    elif body.rubric is not None:
        try:
            new_rubric = grading.normalize_rubric(body.rubric)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        changed_rubric = True
        rubric_title = body.rubric_title if body.rubric_title is not None else settings.rubric_title
        settings.template_id = None
    elif body.clear_rubric:
        new_rubric = None
        changed_rubric = True
        rubric_title = ""
        settings.template_id = None
    if changed_rubric:
        graded = db.scalar(select(AssignmentSubmission.id).where(AssignmentSubmission.item_id == item.id,
                                                                 AssignmentSubmission.rubric_enc != "").limit(1))
        if graded is not None and new_rubric != settings.rubric():
            raise HTTPException(409, "Es gibt schon Bewertungen mit diesem Raster – es lässt sich nicht mehr ändern")
        settings.set_rubric(new_rubric)
        settings.rubric_title = (rubric_title or "")[:200] if new_rubric else ""
        if new_rubric:
            settings.max_points = None
    elif body.rubric_title is not None:
        settings.rubric_title = body.rubric_title[:200]
    if "max_points" in fields and not settings.rubric():
        settings.max_points = round(body.max_points, 2) if body.max_points is not None else None
    if "grade_scale" in fields:
        try:
            settings.grade_scale = grading.normalize_scale(body.grade_scale) if body.grade_scale else None
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
    if body.show_parents is not None:
        settings.show_parents = bool(body.show_parents)
    settings.updated_at = utcnow()
    if settings.group_mode:
        at.normalize_item_groups(db, item, settings)
    audit(db, user, "assignment.settings", f"channel_item:{item.id}",
          {"channel_id": ctx.ch.id, "group_mode": settings.group_mode, "rubric": settings.rubric_kind,
           "max_points": at.max_points_of(settings)}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    out = _settings_out(db, settings, item.id, with_counts=True)
    out["presets"] = [{"id": k, "label": v} for k, v in grading.PRESET_LABELS.items()]
    return out


# =========================================================================== Vorlagen
def _need_teacher(user: AuthUser) -> None:
    if not has(user, "channels.manage"):
        raise HTTPException(403, "Keine Berechtigung")


def _template_out(tpl: GradingTemplate) -> dict[str, Any]:
    rubric = tpl.rubric()
    return {"id": tpl.id, "title": tpl.title, "kind": tpl.kind, "kind_label": grading.KIND_LABELS.get(tpl.kind, tpl.kind),
            "rubric": rubric, "max_points": grading.max_points(rubric) if rubric else None,
            "criteria_count": len(rubric.get("criteria", [])) if rubric else 0, "grade_scale": tpl.grade_scale,
            "updated_at": iso(tpl.updated_at or tpl.created_at)}


@router.get("/grading/templates")
def list_templates(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eigene Raster-Vorlagen der Lehrkraft."""
    _need_teacher(user)
    rows = db.scalars(select(GradingTemplate).where(GradingTemplate.owner_user_id == user.id)
                      .order_by(GradingTemplate.title, GradingTemplate.id))
    return {"templates": [_template_out(t) for t in rows],
            "presets": [{"id": k, "label": v} for k, v in grading.PRESET_LABELS.items()]}


def _fill_template(db: Session, tpl: GradingTemplate, body: TemplateIn) -> None:
    try:
        rubric = grading.normalize_rubric(body.rubric)
        scale = grading.normalize_scale(body.grade_scale) if body.grade_scale else None
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    tpl.title = _clean_name(body.title, "Titel")
    tpl.kind = rubric["kind"]
    tpl.grade_scale = scale
    tpl.write_text("criteria", json.dumps(rubric, ensure_ascii=False))
    tpl.updated_at = utcnow()


@router.post("/grading/templates", status_code=201)
def create_template(body: TemplateIn, request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    _need_teacher(user)
    count = db.scalar(select(func.count()).select_from(GradingTemplate).where(
        GradingTemplate.owner_user_id == user.id)) or 0
    if count >= MAX_TEMPLATES:
        raise HTTPException(409, f"Höchstens {MAX_TEMPLATES} Vorlagen")
    tpl = GradingTemplate(owner_user_id=user.id, title="", kind="rubric", criteria_enc="", created_at=utcnow())
    db.add(tpl)
    db.flush()
    _fill_template(db, tpl, body)
    audit(db, user, "grading_template.create", f"grading_template:{tpl.id}", {"kind": tpl.kind},
          ip=client_ip(request))
    db.commit()
    return _template_out(tpl)


@router.put("/grading/templates/{template_id}")
def update_template(template_id: int, body: TemplateIn, request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    _need_teacher(user)
    tpl = _template_or_404(db, user, template_id)
    _fill_template(db, tpl, body)
    audit(db, user, "grading_template.update", f"grading_template:{tpl.id}", {"kind": tpl.kind},
          ip=client_ip(request))
    db.commit()
    return _template_out(tpl)


@router.delete("/grading/templates/{template_id}")
def delete_template(template_id: int, request: Request, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    _need_teacher(user)
    tpl = _template_or_404(db, user, template_id)
    audit(db, user, "grading_template.delete", f"grading_template:{tpl.id}", {}, ip=client_ip(request))
    db.delete(tpl)
    db.commit()
    return {"deleted": template_id}


# =========================================================================== Fristverlängerung
@router.get("/channels/{channel_id}/items/{item_id}/extensions")
def list_extensions(channel_id: int, item_id: int, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id)
    if not ctx.teacher:
        raise HTTPException(403, "Nur für Lehrende")
    clock = Clock(ctx.snap, channels=[ctx.ch])
    item = _responsible_item(db, ctx, item_id, clock)
    exts = list(db.scalars(select(AssignmentExtension).where(AssignmentExtension.item_id == item.id)
                           .order_by(AssignmentExtension.id)))
    names = _user_names(db, [*(e.user_id for e in exts), *(e.created_by for e in exts)])
    group_names = {g.id: g.name for g in db.scalars(select(ChannelGroup).where(ChannelGroup.channel_id == ctx.ch.id))}
    return {"extensions": [_extension_out(db, e, names, group_names) for e in exts], "due_at": iso(item.due_at)}


@router.put("/channels/{channel_id}/items/{item_id}/extensions")
def put_extension(channel_id: int, item_id: int, body: ExtensionIn, request: Request,
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Frist für eine Schülerin/einen Schüler **oder** eine Gruppe verlängern (ersetzt eine vorhandene Verlängerung)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch])
    item = _responsible_item(db, ctx, item_id, clock)
    if (body.user_id is None) == (body.group_id is None):
        raise HTTPException(422, "Bitte eine Person oder eine Gruppe wählen")
    if item.due_at is None:
        raise HTTPException(422, "Die Aufgabe hat keine Frist – es gibt nichts zu verlängern")
    due = _to_utc(body.due_at, "die Frist")
    if due is None or due <= item.due_at:
        raise HTTPException(422, "Die verlängerte Frist muss nach der allgemeinen Frist liegen")
    affected: list[int]
    if body.user_id is not None:
        if body.user_id not in {r["user_id"] for r in _roster(db, ctx) if r["user_id"]}:
            raise HTTPException(404, "Teilnehmende/r nicht gefunden")
        affected = [body.user_id]
        cond = AssignmentExtension.user_id == body.user_id
    else:
        grp = db.get(ChannelGroup, body.group_id)
        if grp is None or grp.channel_id != ctx.ch.id:
            raise HTTPException(404, "Gruppe nicht gefunden")
        affected = cg.members_of(db, grp.id)
        cond = AssignmentExtension.group_id == body.group_id
    ext = db.scalar(select(AssignmentExtension).where(AssignmentExtension.item_id == item.id, cond))
    if ext is None:
        ext = AssignmentExtension(item_id=item.id, user_id=body.user_id, group_id=body.group_id, due_at=due,
                                  reason_enc="", created_by=user.id, created_at=utcnow())
        db.add(ext)
        db.flush()
    ext.due_at = due
    ext.created_by = user.id
    ext.write_text("reason", logic.clean_text(body.reason, MAX_REASON))
    db.flush()
    _restatus(db, item, affected)
    audit(db, user, "assignment.extension", f"channel_item:{item.id}",
          {"channel_id": ctx.ch.id, "user_id": body.user_id, "group_id": body.group_id, "due_at": iso(due)},
          ip=client_ip(request))
    db.commit()
    _notify(db, ctx, teachers_only=True, extra_ids=affected)
    names = _user_names(db, [ext.user_id, ext.created_by])
    group_names = {g.id: g.name for g in db.scalars(select(ChannelGroup).where(ChannelGroup.channel_id == ctx.ch.id))}
    return _extension_out(db, ext, names, group_names)


@router.delete("/channels/{channel_id}/items/{item_id}/extensions/{extension_id}")
def delete_extension(channel_id: int, item_id: int, extension_id: int, request: Request,
                     user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    clock = Clock(ctx.snap, channels=[ctx.ch])
    item = _responsible_item(db, ctx, item_id, clock)
    ext = db.get(AssignmentExtension, extension_id)
    if ext is None or ext.item_id != item.id:
        raise HTTPException(404, "Verlängerung nicht gefunden")
    affected = [ext.user_id] if ext.user_id else cg.members_of(db, ext.group_id or 0)
    audit(db, user, "assignment.extension_delete", f"channel_item:{item.id}",
          {"channel_id": ctx.ch.id, "user_id": ext.user_id, "group_id": ext.group_id}, ip=client_ip(request))
    db.delete(ext)
    db.flush()
    _restatus(db, item, affected)
    db.commit()
    _notify(db, ctx, teachers_only=True, extra_ids=affected)
    return {"deleted": extension_id}


# =========================================================================== Ergebnisse (Notenbuch)
@router.get("/channels/{channel_id}/assignment-results")
def assignment_results(channel_id: int, item_id: Optional[int] = None, user: AuthUser = Depends(current_user),
                       db: Session = Depends(get_db)) -> dict:
    """Bewertete Abgaben des Kursraums als flache Ergebnisse (Aufgabe, Schüler/in, Punkte, Note, Datum) – Format siehe
    ``assignment_tools.list_results``; nur Aufgaben, die die Lehrkraft bewerten darf."""
    ctx = _ctx(db, user, channel_id)
    if not ctx.teacher:
        raise HTTPException(403, "Nur für Lehrende")
    items = [i for i in db.scalars(select(ChannelItem).where(ChannelItem.channel_id == ctx.ch.id))
             if takes_submissions(i) and ctx.responsible(i) and (item_id is None or i.id == item_id)]
    return {"results": at.list_results(db, channel_id=ctx.ch.id, item_ids=[i.id for i in items])}


# =========================================================================== Gruppen im Kursraum
def _group_or_404(db: Session, ctx: Ctx, group_id: int) -> ChannelGroup:
    grp = db.get(ChannelGroup, group_id)
    if grp is None or grp.channel_id != ctx.ch.id:
        raise HTTPException(404, "Gruppe nicht gefunden")
    return grp


def _set_or_404(db: Session, ctx: Ctx, set_id: int) -> ChannelGroupSet:
    row = db.get(ChannelGroupSet, set_id)
    if row is None or row.channel_id != ctx.ch.id:
        raise HTTPException(404, "Einteilung nicht gefunden")
    return row


def _after_group_change(db: Session, ctx: Ctx) -> None:
    at.normalize_channel(db, ctx.ch.id)


def _groups_overview(db: Session, ctx: Ctx) -> dict[str, Any]:
    sets = list(db.scalars(select(ChannelGroupSet).where(ChannelGroupSet.channel_id == ctx.ch.id)
                           .order_by(ChannelGroupSet.id)))
    groups = list(db.scalars(select(ChannelGroup).where(ChannelGroup.channel_id == ctx.ch.id)
                             .order_by(ChannelGroup.position, ChannelGroup.id)))
    members = list(db.execute(select(ChannelGroupMember.group_id, ChannelGroupMember.user_id)
                              .where(ChannelGroupMember.channel_id == ctx.ch.id).order_by(ChannelGroupMember.id)))
    roster = _roster(db, ctx) if ctx.teacher else []
    by_user = {r["user_id"]: r for r in roster if r["user_id"]}
    mine = cg.user_group_ids(db, ctx.ch.id, ctx.pupil_uid if ctx.pupil else ctx.user.id)
    names = _user_names(db, [uid for _, uid in members]) if not ctx.teacher else {}
    by_group: dict[int, list[int]] = defaultdict(list)
    for gid, uid in members:
        by_group[gid].append(uid)
    out_sets = []
    for s in sets:
        sgroups = [g for g in groups if g.set_id == s.id]
        if not ctx.teacher:
            sgroups = [g for g in sgroups if g.id in mine]
            if not sgroups:
                continue
        assigned = {uid for g in sgroups for uid in by_group.get(g.id, [])}
        entry = {"id": s.id, "name": s.name, "groups": [
            {"id": g.id, "name": g.name, "position": g.position, "members": [
                {"user_id": uid, "name": (by_user.get(uid) or {}).get("name") or names.get(uid, ""),
                 "class_id": (by_user.get(uid) or {}).get("class_id")} for uid in by_group.get(g.id, [])]}
            for g in sgroups]}
        if ctx.teacher:
            entry["unassigned"] = [{"user_id": r["user_id"], "name": r["name"], "class_id": r["class_id"]}
                                   for r in roster if r["user_id"] and r["user_id"] not in assigned]
        out_sets.append(entry)
    out: dict[str, Any] = {"sets": out_sets, "can_manage": ctx.teacher, "limits": {"groups": MAX_GROUPS,
                                                                                    "sets": MAX_SETS}}
    if ctx.teacher:
        items_gate, folders_gate = cg.gate_map(db, [ctx.ch.id])
        out["gates"] = {"items": {str(k): sorted(v) for k, v in items_gate.items()},
                        "folders": {str(k): sorted(v) for k, v in folders_gate.items()}}
        out["without_account"] = sum(1 for r in roster if not r["user_id"])
    return out


@router.get("/channels/{channel_id}/groups")
def list_groups(channel_id: int, student_id: Optional[str] = Query(None, max_length=40),
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Einteilungen und Gruppen. Lehrende: alle mit Mitgliedern, nicht Eingeteilten und den Gruppen-Beschränkungen von
    Material/Ordnern; Teilnehmende (und Eltern für ihr Kind): nur die eigene(n) Gruppe(n)."""
    ctx = _ctx(db, user, channel_id, child=student_id)
    if ctx.supervisor:
        raise HTTPException(403, "Nur für Lehrende und Teilnehmende")
    return _groups_overview(db, ctx)


@router.post("/channels/{channel_id}/group-sets", status_code=201)
def create_group_set(channel_id: int, body: GroupSetIn, request: Request, user: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    if int(db.scalar(select(func.count()).select_from(ChannelGroupSet).where(
            ChannelGroupSet.channel_id == ctx.ch.id)) or 0) >= MAX_SETS:
        raise HTTPException(409, f"Höchstens {MAX_SETS} Einteilungen je Kursraum")
    row = ChannelGroupSet(channel_id=ctx.ch.id, name=_clean_name(body.name), created_by=user.id)
    db.add(row)
    db.flush()
    audit(db, user, "channel_group_set.create", f"channel_group_set:{row.id}", {"channel_id": ctx.ch.id},
          ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _groups_overview(db, ctx)


@router.patch("/channels/{channel_id}/group-sets/{set_id}")
def rename_group_set(channel_id: int, set_id: int, body: GroupSetIn, request: Request,
                     user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    row = _set_or_404(db, ctx, set_id)
    row.name = _clean_name(body.name)
    audit(db, user, "channel_group_set.update", f"channel_group_set:{row.id}", {"channel_id": ctx.ch.id},
          ip=client_ip(request))
    db.commit()
    return _groups_overview(db, ctx)


@router.delete("/channels/{channel_id}/group-sets/{set_id}")
def delete_group_set(channel_id: int, set_id: int, request: Request, user: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    row = _set_or_404(db, ctx, set_id)
    used = db.scalar(select(AssignmentSettings.id).where(AssignmentSettings.group_set_id == row.id,
                                                         AssignmentSettings.group_mode.is_(True)).limit(1))
    if used is not None:
        raise HTTPException(409, "Diese Einteilung wird für eine Gruppenabgabe verwendet")
    audit(db, user, "channel_group_set.delete", f"channel_group_set:{row.id}", {"channel_id": ctx.ch.id},
          ip=client_ip(request))
    db.delete(row)
    db.commit()
    _notify(db, ctx)
    return _groups_overview(db, ctx)


@router.post("/channels/{channel_id}/group-sets/{set_id}/groups", status_code=201)
def create_group(channel_id: int, set_id: int, body: GroupIn, request: Request,
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    gset = _set_or_404(db, ctx, set_id)
    n = int(db.scalar(select(func.count()).select_from(ChannelGroup).where(
        ChannelGroup.channel_id == ctx.ch.id)) or 0)
    if n >= MAX_GROUPS:
        raise HTTPException(409, f"Höchstens {MAX_GROUPS} Gruppen je Kursraum")
    grp = ChannelGroup(channel_id=ctx.ch.id, set_id=gset.id, name=_clean_name(body.name), position=n + 1)
    db.add(grp)
    db.flush()
    audit(db, user, "channel_group.create", f"channel_group:{grp.id}", {"channel_id": ctx.ch.id, "set_id": gset.id},
          ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _groups_overview(db, ctx)


@router.patch("/channels/{channel_id}/groups/{group_id}")
def rename_group(channel_id: int, group_id: int, body: GroupIn, request: Request,
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    grp = _group_or_404(db, ctx, group_id)
    grp.name = _clean_name(body.name)
    audit(db, user, "channel_group.update", f"channel_group:{grp.id}", {"channel_id": ctx.ch.id},
          ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return _groups_overview(db, ctx)


@router.delete("/channels/{channel_id}/groups/{group_id}")
def delete_group(channel_id: int, group_id: int, request: Request, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    grp = _group_or_404(db, ctx, group_id)
    in_use = db.scalar(select(AssignmentSubmission.id).where(AssignmentSubmission.group_id == grp.id).limit(1))
    if in_use is not None:
        raise HTTPException(409, "Die Gruppe hat schon abgegeben und lässt sich nicht löschen")
    audit(db, user, "channel_group.delete", f"channel_group:{grp.id}", {"channel_id": ctx.ch.id},
          ip=client_ip(request))
    db.delete(grp)
    db.commit()
    _after_group_change(db, ctx)
    db.commit()
    _notify(db, ctx)
    return _groups_overview(db, ctx)


def _set_members(db: Session, ctx: Ctx, grp: ChannelGroup, user_ids: list[int], roster_ids: set[int]) -> None:
    wanted = list(dict.fromkeys(user_ids))
    bad = [u for u in wanted if u not in roster_ids]
    if bad:
        raise HTTPException(422, "Nur Teilnehmende des Kursraums (mit Konto) können in Gruppen")
    db.execute(delete(ChannelGroupMember).where(ChannelGroupMember.group_id == grp.id))
    if wanted:
        db.execute(delete(ChannelGroupMember).where(ChannelGroupMember.set_id == grp.set_id,
                                                    ChannelGroupMember.user_id.in_(wanted)))
    for uid in wanted:
        db.add(ChannelGroupMember(channel_id=ctx.ch.id, set_id=grp.set_id, group_id=grp.id, user_id=uid))
    db.flush()


@router.put("/channels/{channel_id}/groups/{group_id}/members")
def put_group_members(channel_id: int, group_id: int, body: MembersIn, request: Request,
                      user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Mitglieder einer Gruppe festlegen (ersetzt die Liste); wer schon in einer anderen Gruppe derselben Einteilung
    ist, wird dorthin umgesetzt. Bei Gruppenabgaben werden die Abgaben der Mitglieder abgeglichen."""
    ctx = _ctx(db, user, channel_id, manage=True)
    grp = _group_or_404(db, ctx, group_id)
    roster_ids = {r["user_id"] for r in _roster(db, ctx) if r["user_id"]}
    _set_members(db, ctx, grp, body.user_ids, roster_ids)
    audit(db, user, "channel_group.members", f"channel_group:{grp.id}",
          {"channel_id": ctx.ch.id, "count": len(set(body.user_ids))}, ip=client_ip(request))
    _after_group_change(db, ctx)
    db.commit()
    _notify(db, ctx, extra_ids=body.user_ids)
    return _groups_overview(db, ctx)


@router.post("/channels/{channel_id}/group-sets/{set_id}/auto")
def auto_groups(channel_id: int, set_id: int, body: AutoGroupsIn, request: Request,
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Teilnehmende automatisch einteilen (zufällig oder alphabetisch, nach Gruppenzahl oder Gruppengröße)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    gset = _set_or_404(db, ctx, set_id)
    if (body.count is None) == (body.size is None):
        raise HTTPException(422, "Bitte Gruppenzahl oder Gruppengröße angeben")
    roster = [r for r in _roster(db, ctx) if r["user_id"]]
    if not roster:
        raise HTTPException(422, "Keine Teilnehmenden mit Konto vorhanden")
    rng = random.Random(body.seed) if body.seed is not None else None
    groups = list(db.scalars(select(ChannelGroup).where(ChannelGroup.set_id == gset.id)
                             .order_by(ChannelGroup.position, ChannelGroup.id)))
    if body.mode == "new":
        in_use = db.scalar(select(AssignmentSubmission.id).where(
            AssignmentSubmission.group_id.in_([g.id for g in groups] or [0])).limit(1))
        used_set = db.scalar(select(AssignmentSettings.id).where(AssignmentSettings.group_set_id == gset.id,
                                                                 AssignmentSettings.group_mode.is_(True)).limit(1))
        if in_use is not None or used_set is not None:
            raise HTTPException(409, "Die Einteilung wird für eine Gruppenabgabe verwendet – bitte „Nur noch nicht "
                                "Eingeteilte verteilen“ wählen")
        parts = grading.auto_divide([r["user_id"] for r in roster], count=body.count, size=body.size,
                                    shuffle=body.shuffle, rng=rng)
        if len(parts) + int(db.scalar(select(func.count()).select_from(ChannelGroup).where(
                ChannelGroup.channel_id == ctx.ch.id)) or 0) - len(groups) > MAX_GROUPS:
            raise HTTPException(409, f"Höchstens {MAX_GROUPS} Gruppen je Kursraum")
        for g in groups:
            db.delete(g)
        db.flush()
        for n, members in enumerate(parts, 1):
            grp = ChannelGroup(channel_id=ctx.ch.id, set_id=gset.id, name=f"{body.name_prefix.strip()} {n}",
                               position=n)
            db.add(grp)
            db.flush()
            for uid in members:
                db.add(ChannelGroupMember(channel_id=ctx.ch.id, set_id=gset.id, group_id=grp.id, user_id=uid))
    else:
        if not groups:
            raise HTTPException(422, "Es gibt noch keine Gruppen – bitte zuerst Gruppen anlegen oder neu einteilen")
        assigned = {uid for uid in db.scalars(select(ChannelGroupMember.user_id).where(
            ChannelGroupMember.set_id == gset.id))}
        todo = [r["user_id"] for r in roster if r["user_id"] not in assigned]
        if body.shuffle:
            (rng or random).shuffle(todo)
        sizes = {g.id: int(db.scalar(select(func.count()).select_from(ChannelGroupMember)
                                     .where(ChannelGroupMember.group_id == g.id)) or 0) for g in groups}
        for uid in todo:
            gid = min(sizes, key=lambda k: (sizes[k], k))
            db.add(ChannelGroupMember(channel_id=ctx.ch.id, set_id=gset.id, group_id=gid, user_id=uid))
            sizes[gid] += 1
    audit(db, user, "channel_group.auto", f"channel_group_set:{gset.id}",
          {"channel_id": ctx.ch.id, "mode": body.mode, "count": body.count, "size": body.size,
           "shuffle": body.shuffle}, ip=client_ip(request))
    db.flush()
    _after_group_change(db, ctx)
    db.commit()
    _notify(db, ctx, extra_ids=[r["user_id"] for r in roster])
    return _groups_overview(db, ctx)


def _put_gate(db: Session, ctx: Ctx, body: GateIn, request: Request, user: AuthUser, *, item: Optional[ChannelItem] = None,
              folder: Optional[ChannelFolder] = None) -> dict:
    if item is not None and not ctx.may_edit(item.created_by):
        ctx.need_edit(item.created_by)
    if folder is not None and not ctx.may_edit(folder.created_by):
        ctx.need_edit(folder.created_by)
    gids = cg.set_gate(db, ctx.ch.id, body.group_ids, item_id=item.id if item else None,
                       folder_id=folder.id if folder else None)
    audit(db, user, "channel_group.gate", f"channel_{'item' if item else 'folder'}:{(item or folder).id}",
          {"channel_id": ctx.ch.id, "groups": gids}, ip=client_ip(request))
    db.commit()
    _notify(db, ctx)
    return {"group_ids": gids}


@router.put("/channels/{channel_id}/items/{item_id}/groups")
def put_item_groups(channel_id: int, item_id: int, body: GateIn, request: Request,
                    user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Material/Aufgabe nur für bestimmte Gruppen sichtbar machen (leere Liste = für alle)."""
    ctx = _ctx(db, user, channel_id, manage=True)
    item = db.get(ChannelItem, item_id)
    if item is None or item.channel_id != ctx.ch.id:
        raise HTTPException(404, "Material nicht gefunden")
    return _put_gate(db, ctx, body, request, user, item=item)


@router.put("/channels/{channel_id}/folders/{folder_id}/groups")
def put_folder_groups(channel_id: int, folder_id: int, body: GateIn, request: Request,
                      user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = _ctx(db, user, channel_id, manage=True)
    folder = db.get(ChannelFolder, folder_id)
    if folder is None or folder.channel_id != ctx.ch.id:
        raise HTTPException(404, "Ordner nicht gefunden")
    return _put_gate(db, ctx, body, request, user, folder=folder)
