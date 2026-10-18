"""Formular-Baukasten: Vorlagen, Ausfüllen, Genehmigung, PDF, Export (Doku: docs/FORMULARE.md).

Rechte (``permissions.py``)
---------------------------
* ``forms.manage`` (Administration, Schulleitung, Sekretariat) – Vorlagen anlegen/ändern/archivieren, Ablauf und
  Aktionen festlegen, Bibliothek übernehmen. **Kein** Einblick in ausgefüllte Formulare.
* ``forms.inbox`` (Schulleitung, Sekretariat; Lehrkräfte/Abteilungsleitung nur als Klassenleitung der eigenen Klasse) –
  Eingang: Einreichungen ansehen, genehmigen/ablehnen, Scans, Export. Nie für die technische Administration.
* ``forms.submit`` (Eltern, Schüler/innen, Lehrkräfte, Sekretariat, Schulleitung) – ausfüllen; **welche** Formulare,
  bestimmt die Zielgruppe des Formulars (Rollen, Klassen/Jahrgänge).

Sichtbarkeit einer Einreichung (:meth:`Ctx.can_view`): die einreichende Person, Eltern des Kindes (bei Volljährigen nur
mit Freigabe „Dokumente“), die Schülerin/der Schüler selbst, Personal mit ``forms.inbox`` im Umfang des Rechts
(Klassenleitung: nur die eigene Klasse) und die in einem Prüfschritt benannte Person. Fremde → 404.
Antworten und Vermerke liegen verschlüsselt (AAD ``form_submissions.answers:<id>``); Dateien verschlüsselt in der
Dateiablage (``ref_type=form_submission``, Zweck ``form_file``). Das Ansehen von Formularen mit sensiblen Angaben
(Gesundheit/Förderung) wird protokolliert.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager import forms as logic
from schulmanager.server import files
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.forms import FormEvent, FormSubmission, FormTemplate, FormVersion

from .features_common import has, index, perm_scope, publish_change, snapshot, write_audit

router = APIRouter(tags=["Formulare"])

REF_TYPE = "form_submission"
PURPOSE = "form_file"
INBOX_ROLES = ("schulleitung", "sekretariat", "lehrer", "abteilungsleitung")
VIEW_ROLES = (*INBOX_ROLES, "zuschauer")      # Ansichtskonto: liest wie die Leitung, ändert nie
LEAD_ROLES = ("lehrer", "abteilungsleitung")
MAX_LIST = 2000
NOT_FOUND = "Formular nicht gefunden"

files.register_purpose(PURPOSE, kinds=["pdf", "image"], max_mb=15)


def _today() -> date:
    """Heutiges Datum (eigene Funktion, damit Tests einen festen Tag setzen können)."""
    return date.today()


# =========================================================================== Verschlüsselung
def _enc(value: str, col: str, ident: Any) -> str:
    from .features_student_self import enc
    return enc(value, "form_submissions", col, ident)


def _dec(value: Optional[str], col: str, ident: Any) -> str:
    from .features_student_self import dec
    return dec(value, "form_submissions", col, ident)


def _answers_of(sub: FormSubmission) -> dict:
    raw = _dec(sub.answers_enc, "answers", sub.id)
    try:
        data = json.loads(raw) if raw else {}
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _set_answers(sub: FormSubmission, answers: dict) -> None:
    sub.answers_enc = _enc(json.dumps(answers, ensure_ascii=False), "answers", sub.id)


# =========================================================================== Zugriff
class Ctx:
    """Rechte und Datenumfang eines Kontos für Formulare (je Anfrage)."""

    def __init__(self, user: AuthUser, db: Session, snap=None):
        from schulmanager.server import parent_access as pa
        self.pa = pa
        self.user, self.db = user, db
        self.snap = snap or snapshot()
        self.school = self.snap[1]
        self.role = user.role
        self.students = index("students", self.snap)
        self.classes = index("classes", self.snap)
        self.inbox = has(user, "forms.inbox") and self.role in VIEW_ROLES
        self.manage = has(user, "forms.manage")
        self.submit = has(user, "forms.submit")
        scope = perm_scope(user, "forms.inbox") if self.inbox else None
        self.all_classes = self.inbox and scope is None
        self.lead = {c.id for c in self.school.classes if user.teacher_id and c.class_teacher == user.teacher_id} \
            if self.inbox and scope == "class_teacher" and self.role in LEAD_ROLES else set()
        self.own_ids = list(user.student_ids or ([user.student_id] if user.student_id else []))
        self._adult: dict[str, bool] = {}
        self._versions: dict[int, FormVersion] = {}
        self._templates: dict[int, FormTemplate] = {}

    # -- Hilfen
    def adult(self, sid: str) -> bool:
        if sid not in self._adult:
            self._adult[sid] = self.pa.is_adult(self.db, sid, school=self.school)
        return self._adult[sid]

    def parent_ok(self, sid: str) -> bool:
        """Eltern dürfen Formulare des Kindes sehen/ausfüllen: minderjährig oder Freigabe „Dokumente“."""
        return (not self.adult(sid)) or self.pa.parent_may_see(self.db, sid, self.pa.AREA_DOCUMENTS,
                                                               school=self.school)

    def version(self, version_id: int) -> FormVersion:
        if version_id not in self._versions:
            self._versions[version_id] = self.db.get(FormVersion, version_id)
        return self._versions[version_id]

    def template(self, template_id: int) -> FormTemplate:
        if template_id not in self._templates:
            self._templates[template_id] = self.db.get(FormTemplate, template_id)
        return self._templates[template_id]

    def class_leader(self, class_id: Optional[str]) -> Optional[str]:
        cls = self.classes.get(class_id) if class_id else None
        return cls.class_teacher if cls else None

    # -- Sichtbarkeit
    def can_view(self, sub: FormSubmission) -> bool:
        user = self.user
        if self.role == "admin":
            return False                     # technische Administration: nie Einblick
        if sub.submitted_by is not None and sub.submitted_by == user.id:
            return True
        sid = sub.student_id
        if self.role == "eltern":
            return bool(sid) and sid in self.own_ids and self.parent_ok(sid)
        if self.role == "schueler":
            return bool(sid) and sid in self.own_ids
        if not self.inbox:
            return False
        if self.all_classes or (sub.class_id and sub.class_id in self.lead):
            return True
        steps = (self.version(sub.version_id).definition.get("workflow") or {}).get("steps") or []
        return any(s.get("approver") == "user" and s.get("user_id") == user.id for s in steps)

    def is_approver(self, sub: FormSubmission, step: dict) -> bool:
        user, kind = self.user, step.get("approver")
        if not self.inbox or sub.submitted_by == user.id:
            return False
        if self.role == "schulleitung":
            return True                      # die Schulleitung kann jeden Schritt übernehmen
        if kind == "user":
            return step.get("user_id") == user.id
        if kind == "sekretariat":
            return self.role == "sekretariat"
        if kind == "schulleitung":
            return False
        if kind == "class_teacher":
            leader = self.class_leader(sub.class_id)
            if leader:
                return self.role in LEAD_ROLES and user.teacher_id == leader
            return self.role == "sekretariat"           # Klasse ohne Klassenleitung: Sekretariat
        return False

    def current_step(self, sub: FormSubmission) -> Optional[dict]:
        steps = (self.version(sub.version_id).definition.get("workflow") or {}).get("steps") or []
        return steps[sub.step] if sub.status in logic.OPEN_STATUSES and sub.step < len(steps) else None

    def can_decide(self, sub: FormSubmission) -> bool:
        step = self.current_step(sub)
        return step is not None and self.is_approver(sub, step)

    def can_complete(self, sub: FormSubmission) -> bool:
        """Als „erledigt“ abschließen: Einreichungen ohne Prüfschritte bzw. bereits genehmigte – nur mit Vollzugriff
        auf die Klasse (Eingang) oder als Klassenleitung der Klasse."""
        if not self.inbox or self.role == "zuschauer" or sub.status in ("erledigt", "abgelehnt", "zurueckgezogen"):
            return False
        steps = (self.version(sub.version_id).definition.get("workflow") or {}).get("steps") or []
        if sub.status in logic.OPEN_STATUSES and steps:
            return False
        return self.can_view(sub)

    def can_withdraw(self, sub: FormSubmission) -> bool:
        if sub.status != "eingereicht" or sub.step > 0:
            return False
        if sub.submitted_by is not None and sub.submitted_by == self.user.id:
            return True
        return self.role == "eltern" and bool(sub.student_id) and sub.student_id in self.own_ids \
            and self.parent_ok(sub.student_id)

    def can_scan(self, sub: FormSubmission) -> bool:
        return self.can_view(sub) and sub.status not in ("abgelehnt", "zurueckgezogen")


def _need_manage(user: AuthUser) -> None:
    if not has(user, "forms.manage"):
        raise HTTPException(403, "Keine Berechtigung")


def _get_template(db: Session, template_id: int) -> FormTemplate:
    tmpl = db.get(FormTemplate, template_id)
    if tmpl is None:
        raise HTTPException(404, NOT_FOUND)
    return tmpl


def _current_version(db: Session, tmpl: FormTemplate) -> FormVersion:
    ver = db.scalar(select(FormVersion).where(FormVersion.template_id == tmpl.id,
                                              FormVersion.version == tmpl.version))
    if ver is None:  # pragma: no cover - Datenfehler
        raise HTTPException(500, "Version des Formulars fehlt")
    return ver


def _get_sub(ctx: Ctx, sub_id: int) -> FormSubmission:
    sub = ctx.db.get(FormSubmission, sub_id)
    if sub is None or not ctx.can_view(sub):
        raise HTTPException(404, "Einreichung nicht gefunden")
    return sub


# =========================================================================== Ziel- und Ausfüll-Regeln
def _student_row(ctx: Ctx, sid: str) -> dict:
    st = ctx.students[sid]
    return {"id": sid, "name": st.name, "class_id": st.class_id}


def _grade_of(ctx: Ctx, class_id: Optional[str]) -> Optional[int]:
    cls = ctx.classes.get(class_id) if class_id else None
    return cls.grade if cls else None


def fill_students(ctx: Ctx, defn: dict) -> Optional[list[str]]:
    """Schüler/innen, für die das Konto das Formular ausfüllen darf (Zielgruppe berücksichtigt); ``None`` = das Konto
    gehört nicht zur Zielgruppe. Leere Liste bei Formularen ohne Kind-Bezug von Lehrkräften/Verwaltung."""
    if not ctx.submit:
        return None
    roles = set(defn["audience"]["roles"])
    role = ctx.role

    def target(sid: str) -> bool:
        st = ctx.students.get(sid)
        return st is not None and logic.class_in_target(defn, st.class_id, _grade_of(ctx, st.class_id))

    if role == "eltern":
        if "eltern" not in roles:
            return None
        return [s for s in ctx.own_ids if s in ctx.students and target(s) and ctx.parent_ok(s)]
    if role == "schueler":
        sid = ctx.own_ids[0] if ctx.own_ids else None
        if not sid or sid not in ctx.students:
            return None
        if "schueler" in roles or ("schueler_adult" in roles and ctx.adult(sid)):
            return [sid] if target(sid) else []
        return None
    if role in LEAD_ROLES:
        if "lehrer" not in roles:
            return None
        if not logic.has_student_field(defn):
            return []
        from schulmanager.server.permissions import own_class_ids
        mine = own_class_ids(ctx.school, ctx.user)
        return sorted((s.id for s in ctx.school.students if s.class_id in mine and target(s.id)), key=lambda x: x)
    if role in ("sekretariat", "schulleitung"):
        if role not in roles:
            return None
        if not logic.has_student_field(defn):
            return []
        return [s.id for s in ctx.school.students if target(s.id)][:3000]
    return None


def _may_fill(tmpl: FormTemplate, defn: dict, today: date) -> bool:
    return tmpl.status == "aktiv" and logic.in_window(defn, today)


def _subject_text(ctx: Ctx, sid: Optional[str]) -> str:
    st = ctx.students.get(sid) if sid else None
    return f"{st.name} ({st.class_id})" if st else ""


# =========================================================================== Ausgabe
STATUS_LABELS = logic.STATUS_LABELS


def _template_out(tmpl: FormTemplate, ver: FormVersion, *, counts: Optional[dict] = None) -> dict:
    defn = ver.definition
    return {"id": tmpl.id, "title": tmpl.title, "description": tmpl.description, "category": tmpl.category,
            "category_label": logic.CATEGORIES.get(tmpl.category, tmpl.category), "status": tmpl.status,
            "version": tmpl.version, "library_key": tmpl.library_key, "sensitive": tmpl.sensitive,
            "created_by_name": tmpl.created_by_name, "created_at": iso(tmpl.created_at),
            "updated_at": iso(tmpl.updated_at), "definition": defn, "counts": counts}


def _steps_out(defn: dict) -> list[dict]:
    return [{"approver": s["approver"], "label": s.get("label") or logic.APPROVERS[s["approver"]]}
            for s in (defn.get("workflow") or {}).get("steps") or []]


def _events_out(db: Session, sub: FormSubmission) -> list[dict]:
    rows = db.scalars(select(FormEvent).where(FormEvent.submission_id == sub.id).order_by(FormEvent.id)).all()
    return [{"id": e.id, "action": e.action, "step": e.step, "actor_name": e.actor_name,
             "note": _dec(e.note_enc, "event", f"{sub.id}.{e.id}"), "at": iso(e.created_at)} for e in rows]


def _sub_out(ctx: Ctx, sub: FormSubmission, *, detail: bool = False) -> dict:
    tmpl, ver = ctx.template(sub.template_id), ctx.version(sub.version_id)
    defn = ver.definition
    steps = _steps_out(defn)
    st = ctx.students.get(sub.student_id) if sub.student_id else None
    today = _today()
    staff = ctx.inbox or ctx.manage
    step = steps[sub.step] if sub.status in logic.OPEN_STATUSES and sub.step < len(steps) else None
    out = {"id": sub.id, "template_id": sub.template_id, "template_title": ver.title or tmpl.title,
           "category": tmpl.category, "sensitive": tmpl.sensitive, "version": ver.version,
           "student_id": sub.student_id, "student_name": st.name if st else None,
           "class_id": sub.class_id, "submitted_by_name": sub.submitted_by_name, "submitted_role": sub.submitted_role,
           "status": sub.status, "status_label": STATUS_LABELS.get(sub.status, sub.status), "step": sub.step,
           "steps": steps, "current_step": step["label"] if step else None,
           "created_at": iso(sub.created_at), "updated_at": iso(sub.updated_at), "decided_at": iso(sub.decided_at),
           "decided_by_name": sub.decided_by_name or None, "due_on": sub.due_on,
           "overdue": bool(sub.due_on and sub.status in logic.OPEN_STATUSES and sub.due_on < today.isoformat()),
           "can_decide": ctx.can_decide(sub), "can_complete": ctx.can_complete(sub),
           "can_withdraw": ctx.can_withdraw(sub), "can_scan": ctx.can_scan(sub),
           "scan_count": len(sub.scan_file_ids or []), "staff": staff and ctx.inbox}
    if detail:
        answers = _answers_of(sub)
        out["answers"] = [{"id": f["id"], "label": f["label"], "type": f["type"], "value": answers.get(f["id"]),
                           "display": logic.display_value(f, answers.get(f["id"]))} for f in defn["fields"]]
        out["definition"] = defn
        out["events"] = _events_out(ctx.db, sub)
        out["decision_note"] = _dec(sub.decision_note_enc, "decision", sub.id)
        out["scans"] = files.files_info(ctx.db, sub.scan_file_ids or [], ctx.user)
        file_ids = [fid for f in defn["fields"] if f["type"] == "file" for fid in (answers.get(f["id"]) or [])]
        out["attachments"] = files.files_info(ctx.db, file_ids, ctx.user)
        out["result"] = sub.result
        out["legacy_pdf"] = defn.get("legacy_pdf")
    return out


# =========================================================================== Meta
@router.get("/forms/meta")
def forms_meta(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Bausteine für die Oberfläche: Feldarten, Kategorien, Rollen, Prüfer, Aktionen, Status."""
    ctx = Ctx(user, db)
    if not (ctx.manage or ctx.inbox or ctx.submit):
        raise HTTPException(403, "Keine Berechtigung")
    return {"field_types": logic.FIELD_TYPES, "categories": logic.CATEGORIES, "audience_roles": logic.AUDIENCE_ROLES,
            "approvers": logic.APPROVERS, "action_types": logic.ACTION_TYPES, "statuses": logic.STATUS_LABELS,
            "absence_kinds": {"beurlaubung": "Beurlaubung", "krank": "Krankmeldung", "fehlt": "Gefehlt"},
            "manage": ctx.manage, "inbox": ctx.inbox, "submit": ctx.submit,
            "periods": ctx.school.settings.periods,
            "classes": [{"id": c.id, "name": c.name, "grade": c.grade} for c in ctx.school.classes]
            if ctx.manage else []}


@router.get("/forms/approvers")
def forms_approvers(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Konten, die als „bestimmte Person“ einen Prüfschritt übernehmen können (Schulleitung, Sekretariat, Lehrkräfte)."""
    from schulmanager.server.db_models import User
    _need_manage(user)
    rows = db.scalars(select(User).where(User.active.is_(True), User.role.in_(INBOX_ROLES))
                      .order_by(User.display_name, User.username)).all()
    from schulmanager.server.permissions import ROLE_LABELS
    return [{"id": u.id, "name": u.display_name or u.username, "role": u.role,
             "role_label": ROLE_LABELS.get(u.role, u.role)} for u in rows]


# =========================================================================== Vorlagen (Verwaltung)
class TemplateIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    category: str = "sonstiges"
    sensitive: bool = False
    status: Optional[Literal["entwurf", "aktiv", "archiviert"]] = None
    definition: dict


def _check_template_in(db: Session, body: TemplateIn) -> tuple[str, str, str, dict]:
    from schulmanager.server.db_models import User
    title = logic.clean_text(body.title, 200)
    if not title:
        raise HTTPException(422, "Bitte einen Titel angeben")
    category = body.category if body.category in logic.CATEGORIES else "sonstiges"
    try:
        defn = logic.normalize_definition(body.definition)
    except logic.FormError as exc:
        raise HTTPException(422, str(exc)) from None
    for step in defn["workflow"]["steps"]:
        if step["approver"] == "user":
            account = db.get(User, step["user_id"])
            if account is None or not account.active or account.role not in INBOX_ROLES:
                raise HTTPException(422, "Die gewählte Person kann keine Formulare prüfen (nur Schulleitung, "
                                         "Sekretariat und Lehrkräfte).")
    return title, logic.clean_text(body.description, 2000, multiline=True), category, defn


def _counts(db: Session, ids: list[int]) -> dict[int, dict]:
    out = {i: {"total": 0, "open": 0} for i in ids}
    if not ids:
        return out
    for tid, status, n in db.execute(select(FormSubmission.template_id, FormSubmission.status, func.count())
                                     .where(FormSubmission.template_id.in_(ids))
                                     .group_by(FormSubmission.template_id, FormSubmission.status)):
        out[tid]["total"] += n
        if status in logic.OPEN_STATUSES:
            out[tid]["open"] += n
    return out


@router.get("/forms/templates")
def list_templates(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Alle Vorlagen der Schule mit Zählern (nur Anzahl, kein Inhalt) – Verwaltung."""
    _need_manage(user)
    rows = db.scalars(select(FormTemplate).order_by(FormTemplate.status, FormTemplate.title)).all()
    counts = _counts(db, [r.id for r in rows])
    out = []
    for tmpl in rows:
        item = _template_out(tmpl, _current_version(db, tmpl), counts=counts[tmpl.id])
        out.append(item)
    return out


def _new_version(db: Session, tmpl: FormTemplate, defn: dict, user: AuthUser, version: int) -> FormVersion:
    ver = FormVersion(template_id=tmpl.id, version=version, title=tmpl.title, definition=defn,
                      created_by_name=user.display_name or user.username, created_at=utcnow())
    db.add(ver)
    db.flush()
    return ver


@router.post("/forms/templates", status_code=201)
def create_template(body: TemplateIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_manage(user)
    title, description, category, defn = _check_template_in(db, body)
    tmpl = FormTemplate(title=title, description=description, category=category, status=body.status or "entwurf",
                        version=1, sensitive=body.sensitive, created_by=user.id or None,
                        created_by_name=user.display_name or user.username, created_at=utcnow())
    db.add(tmpl)
    db.flush()
    ver = _new_version(db, tmpl, defn, user, 1)
    write_audit(db, user, "form_template.create", f"form_template:{tmpl.id}", {"title": title})
    db.commit()
    publish_change(["forms"])
    return _template_out(tmpl, ver, counts={"total": 0, "open": 0})


@router.get("/forms/templates/{template_id}")
def get_template(template_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_manage(user)
    tmpl = _get_template(db, template_id)
    out = _template_out(tmpl, _current_version(db, tmpl), counts=_counts(db, [tmpl.id])[tmpl.id])
    out["versions"] = [{"version": v.version, "created_at": iso(v.created_at), "created_by_name": v.created_by_name,
                        "submissions": db.scalar(select(func.count()).select_from(FormSubmission)
                                                 .where(FormSubmission.version_id == v.id)) or 0}
                       for v in db.scalars(select(FormVersion).where(FormVersion.template_id == tmpl.id)
                                           .order_by(FormVersion.version.desc()))]
    return out


@router.put("/forms/templates/{template_id}")
def update_template(template_id: int, body: TemplateIn, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    """Vorlage ändern. Ändern sich Felder, Zielgruppe, Ablauf oder Aktionen und gibt es schon Einreichungen mit der
    aktuellen Fassung, entsteht eine **neue Version** (neue Einreichungen nutzen sie, alte bleiben unverändert);
    sonst wird die Fassung direkt angepasst."""
    _need_manage(user)
    tmpl = _get_template(db, template_id)
    title, description, category, defn = _check_template_in(db, body)
    cur = _current_version(db, tmpl)
    changes: dict[str, Any] = {}
    if defn != cur.definition:
        used = db.scalar(select(func.count()).select_from(FormSubmission)
                         .where(FormSubmission.version_id == cur.id)) or 0
        if used:
            tmpl.version += 1
            cur = _new_version(db, tmpl, defn, user, tmpl.version)
            changes["new_version"] = tmpl.version
        else:
            cur.definition = defn
            cur.title = title
            changes["definition"] = True
    for key, value in (("title", title), ("description", description), ("category", category),
                       ("sensitive", body.sensitive)):
        if getattr(tmpl, key) != value:
            setattr(tmpl, key, value)
            changes[key] = True
    if body.status and body.status != tmpl.status:
        changes["status"] = [tmpl.status, body.status]
        tmpl.status = body.status
    if changes:
        cur.title = tmpl.title
        tmpl.updated_at = utcnow()
        write_audit(db, user, "form_template.update", f"form_template:{tmpl.id}", changes)
        db.commit()
        publish_change(["forms"])
    return _template_out(tmpl, cur, counts=_counts(db, [tmpl.id])[tmpl.id])


class StatusIn(BaseModel):
    status: Literal["entwurf", "aktiv", "archiviert"]


@router.post("/forms/templates/{template_id}/status")
def set_template_status(template_id: int, body: StatusIn, user: AuthUser = Depends(current_user),
                        db: Session = Depends(get_db)) -> dict:
    """Veröffentlichen (``aktiv``), zurück in den Entwurf oder archivieren (bestehende Einreichungen bleiben)."""
    _need_manage(user)
    tmpl = _get_template(db, template_id)
    if body.status != tmpl.status:
        write_audit(db, user, "form_template.status", f"form_template:{tmpl.id}", {"status": [tmpl.status, body.status]})
        tmpl.status = body.status
        tmpl.updated_at = utcnow()
        db.commit()
        publish_change(["forms"])
    return _template_out(tmpl, _current_version(db, tmpl), counts=_counts(db, [tmpl.id])[tmpl.id])


@router.post("/forms/templates/{template_id}/duplicate", status_code=201)
def duplicate_template(template_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_manage(user)
    src = _get_template(db, template_id)
    tmpl = FormTemplate(title=f"{src.title} (Kopie)"[:200], description=src.description, category=src.category,
                        status="entwurf", version=1, sensitive=src.sensitive, library_key=src.library_key,
                        created_by=user.id or None, created_by_name=user.display_name or user.username,
                        created_at=utcnow())
    db.add(tmpl)
    db.flush()
    ver = _new_version(db, tmpl, json.loads(json.dumps(_current_version(db, src).definition)), user, 1)
    write_audit(db, user, "form_template.create", f"form_template:{tmpl.id}", {"copy_of": src.id})
    db.commit()
    publish_change(["forms"])
    return _template_out(tmpl, ver, counts={"total": 0, "open": 0})


@router.delete("/forms/templates/{template_id}")
def delete_template(template_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Löschen nur ohne Einreichungen (sonst archivieren – Einreichungen bleiben erhalten)."""
    _need_manage(user)
    tmpl = _get_template(db, template_id)
    if db.scalar(select(func.count()).select_from(FormSubmission).where(FormSubmission.template_id == tmpl.id)):
        raise HTTPException(409, "Zu diesem Formular gibt es Einreichungen – bitte archivieren statt löschen.")
    write_audit(db, user, "form_template.delete", f"form_template:{tmpl.id}", {"title": tmpl.title})
    db.delete(tmpl)
    db.commit()
    publish_change(["forms"])
    return {"deleted": template_id}


# -- Bibliothek
@router.get("/forms/library")
def library(user: AuthUser = Depends(current_user)) -> list[dict]:
    _need_manage(user)
    return [{"key": e["key"], "title": e["title"], "description": e["description"], "category": e["category"],
             "category_label": logic.CATEGORIES[e["category"]], "sensitive": e["sensitive"],
             "definition": logic.normalize_definition(e["definition"]),
             "legacy_pdf": e["definition"].get("legacy_pdf")} for e in logic.LIBRARY]


@router.post("/forms/library/{key}/adopt", status_code=201)
def adopt_library(key: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Beispiel übernehmen: legt eine Kopie als Entwurf an, die die Schule anpasst und dann veröffentlicht."""
    _need_manage(user)
    entry = logic.library_entry(key)
    if entry is None:
        raise HTTPException(404, "Beispiel nicht gefunden")
    defn = logic.normalize_definition(entry["definition"])
    tmpl = FormTemplate(title=entry["title"], description=entry["description"], category=entry["category"],
                        status="entwurf", version=1, library_key=key, sensitive=entry["sensitive"],
                        created_by=user.id or None, created_by_name=user.display_name or user.username,
                        created_at=utcnow())
    db.add(tmpl)
    db.flush()
    ver = _new_version(db, tmpl, defn, user, 1)
    write_audit(db, user, "form_template.create", f"form_template:{tmpl.id}", {"library": key})
    db.commit()
    publish_change(["forms"])
    return _template_out(tmpl, ver, counts={"total": 0, "open": 0})


# =========================================================================== PDF
def _pdf_response(data: bytes, name: str) -> Response:
    from schulmanager.server.files import content_disposition
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name)
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": content_disposition(safe)})


def _blank_pdf(ctx: Ctx, title: str, description: str, defn: dict, version: int) -> bytes:
    from schulmanager.server.form_pdf import render_form
    return render_form(title, description, defn["fields"], school_name=ctx.school.settings.school_name or "Schule",
                       intro=defn.get("intro") or "", periods=ctx.school.settings.periods, version=version)


@router.get("/forms/templates/{template_id}/blank.pdf")
def blank_pdf(template_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    """Leeres Formular zum Ausdrucken – für die Verwaltung (auch Entwürfe) und alle, die es ausfüllen dürfen."""
    ctx = Ctx(user, db)
    tmpl = _get_template(db, template_id)
    ver = _current_version(db, tmpl)
    if not ctx.manage:
        if not _may_fill(tmpl, ver.definition, _today()) or fill_students(ctx, ver.definition) is None:
            raise HTTPException(404, NOT_FOUND)
    return _pdf_response(_blank_pdf(ctx, tmpl.title, tmpl.description, ver.definition, ver.version),
                         f"{tmpl.title}.pdf")


class PreviewIn(BaseModel):
    title: str = Field("Formular", max_length=200)
    description: str = Field("", max_length=2000)
    definition: dict


@router.post("/forms/preview.pdf")
def preview_pdf(body: PreviewIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    """Vorschau eines noch ungespeicherten Formulars als PDF (Baukasten)."""
    _need_manage(user)
    try:
        defn = logic.normalize_definition(body.definition)
    except logic.FormError as exc:
        raise HTTPException(422, str(exc)) from None
    return _pdf_response(_blank_pdf(Ctx(user, db), logic.clean_text(body.title, 200) or "Formular",
                                    body.description, defn, 0), "Vorschau.pdf")


def _filled_item(ctx: Ctx, sub: FormSubmission) -> dict:
    tmpl, ver = ctx.template(sub.template_id), ctx.version(sub.version_id)
    meta = {"Status": STATUS_LABELS.get(sub.status, sub.status),
            "Eingereicht von": f"{sub.submitted_by_name} am {logic.fmt_date(iso(sub.created_at)[:10])}",
            "Schüler/in": _subject_text(ctx, sub.student_id)}
    if sub.decided_at:
        meta["Entscheidung"] = f"{sub.decided_by_name} am {logic.fmt_date(str(iso(sub.decided_at))[:10])}"
    note = _dec(sub.decision_note_enc, "decision", sub.id)
    if note:
        meta["Vermerk"] = note
    history = [f"{logic.fmt_date(iso(e.created_at)[:10])} · {e.actor_name or 'System'} · {_event_label(e.action)}"
               for e in ctx.db.scalars(select(FormEvent).where(FormEvent.submission_id == sub.id)
                                       .order_by(FormEvent.id))]
    return {"title": ver.title or tmpl.title, "description": "", "fields": ver.definition["fields"],
            "answers": _answers_of(sub), "meta": meta, "student_text": _subject_text(ctx, sub.student_id),
            "periods": ctx.school.settings.periods, "history": history, "version": ver.version}


def _filled_pdf(ctx: Ctx, sub: FormSubmission) -> bytes:
    from schulmanager.server.form_pdf import render_form
    item = _filled_item(ctx, sub)
    return render_form(item.pop("title"), item.pop("description"), item.pop("fields"),
                       school_name=ctx.school.settings.school_name or "Schule", **item)


EVENT_LABELS = {"eingereicht": "eingereicht", "geprueft": "Schritt freigegeben", "genehmigt": "genehmigt",
                "abgelehnt": "abgelehnt", "erledigt": "als erledigt markiert", "zurueckgezogen": "zurückgezogen",
                "scan": "unterschriebener Scan hochgeladen", "aktion": "Aktion ausgeführt",
                "erinnerung": "Erinnerung", "kommentar": "Vermerk"}


def _event_label(action: str) -> str:
    return EVENT_LABELS.get(action, action)


def _audit_view(ctx: Ctx, sub: FormSubmission, what: str = "form_submission.view") -> None:
    """Ansehen/Exportieren sensibler Formulare protokollieren (nicht bei der einreichenden Person selbst)."""
    if ctx.template(sub.template_id).sensitive and sub.submitted_by != ctx.user.id:
        write_audit(ctx.db, ctx.user, what, f"form_submission:{sub.id}", {"template_id": sub.template_id})
        ctx.db.commit()


@router.get("/forms/submissions/{sub_id}/pdf")
def submission_pdf(sub_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    """Ausgefülltes Formular als PDF (Archiv)."""
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    _audit_view(ctx, sub, "form_submission.pdf")
    return _pdf_response(_filled_pdf(ctx, sub), f"{ctx.template(sub.template_id).title}_{sub.id}.pdf")


# =========================================================================== Ausfüllen
def _available_item(ctx: Ctx, tmpl: FormTemplate, defn: dict, students: list[str], mine: dict) -> dict:
    needs_student = ctx.role in ("eltern", "schueler") or logic.has_student_field(defn)
    return {"id": tmpl.id, "title": tmpl.title, "description": tmpl.description, "category": tmpl.category,
            "category_label": logic.CATEGORIES.get(tmpl.category, tmpl.category), "sensitive": tmpl.sensitive,
            "version": tmpl.version, "open_until": (defn.get("deadline") or {}).get("open_until"),
            "needs_student": needs_student, "once": bool(defn.get("once")),
            "students": [{**_student_row(ctx, s), "submission_id": mine.get((tmpl.id, s))} for s in students],
            "submission_id": mine.get((tmpl.id, None)), "legacy_pdf": defn.get("legacy_pdf"),
            "fields": len(defn["fields"])}


def _my_open_map(ctx: Ctx) -> dict:
    """(Vorlage, Kind) → ID der letzten gültigen Einreichung der eigenen Familie/Person."""
    out: dict = {}
    for sub in ctx.db.scalars(select(FormSubmission).where(FormSubmission.submitted_by == ctx.user.id,
                                                           FormSubmission.status.not_in(("abgelehnt",
                                                                                         "zurueckgezogen")))
                              .order_by(FormSubmission.id)):
        out[(sub.template_id, sub.student_id)] = sub.id
    return out


@router.get("/forms/available")
def available_forms(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Offene Formulare für das Konto (Zielgruppe, Frist, Kind), mit Hinweis auf bereits abgegebene."""
    ctx = Ctx(user, db)
    if not ctx.submit:
        raise HTTPException(403, "Keine Berechtigung")
    today, mine, out = _today(), _my_open_map(ctx), []
    for tmpl in db.scalars(select(FormTemplate).where(FormTemplate.status == "aktiv").order_by(FormTemplate.title)):
        defn = _current_version(db, tmpl).definition
        if not logic.in_window(defn, today):
            continue
        students = fill_students(ctx, defn)
        if students is None or (not students and (ctx.role in ("eltern", "schueler")
                                                  or logic.has_student_field(defn))):
            continue
        out.append(_available_item(ctx, tmpl, defn, students if ctx.role in ("eltern", "schueler")
                                   or len(students) <= 500 else [], mine))
    return out


@router.get("/forms/templates/{template_id}/fill")
def fill_info(template_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Formular zum Ausfüllen: Felder, Hinweise und die wählbaren Kinder."""
    ctx = Ctx(user, db)
    tmpl = _get_template(db, template_id)
    ver = _current_version(db, tmpl)
    students = fill_students(ctx, ver.definition)
    if students is None or not _may_fill(tmpl, ver.definition, _today()):
        raise HTTPException(404, NOT_FOUND)
    item = _available_item(ctx, tmpl, ver.definition, students, _my_open_map(ctx))
    item["definition"] = ver.definition
    item["periods"] = ctx.school.settings.periods
    item["signer"] = user.display_name or user.username
    return item


class SubmitIn(BaseModel):
    student_id: Optional[str] = Field(None, max_length=40)
    answers: dict = Field(default_factory=dict)


def _attach_answer_files(ctx: Ctx, sub: FormSubmission, defn: dict, answers: dict) -> None:
    for f in defn["fields"]:
        if f["type"] == "file":
            for fid in answers.get(f["id"]) or []:
                try:
                    files.attach(ctx.db, fid, ctx.user, REF_TYPE, sub.id)
                except HTTPException as exc:
                    raise HTTPException(422, f"Die Datei bei „{f['label']}“ konnte nicht angehängt werden "
                                             "(bitte erneut hochladen).") from exc


def _event(db: Session, sub: FormSubmission, action: str, user: Any, note: str = "", step: Optional[int] = None) -> None:
    ev = FormEvent(submission_id=sub.id, step=sub.step if step is None else step, action=action,
                   actor_id=(getattr(user, "id", None) or None) if user is not None else None,
                   actor_name=(getattr(user, "display_name", "") or getattr(user, "username", "")) if user else "",
                   created_at=utcnow())
    db.add(ev)
    db.flush()
    if note:
        ev.note_enc = _enc(note, "event", f"{sub.id}.{ev.id}")


@router.post("/forms/templates/{template_id}/submit", status_code=201)
def submit_form(template_id: int, body: SubmitIn, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Formular abgeben. Antworten werden gegen die Fassung des Formulars geprüft; bei „Sofort erledigt“ laufen die
    Aktionen direkt, sonst geht die Einreichung an den ersten Prüfschritt."""
    ctx = Ctx(user, db)
    tmpl = _get_template(db, template_id)
    ver = _current_version(db, tmpl)
    defn = ver.definition
    allowed = fill_students(ctx, defn)
    if allowed is None:
        raise HTTPException(403, "Dieses Formular ist für Ihr Konto nicht vorgesehen.")
    if tmpl.status != "aktiv":
        raise HTTPException(409, "Dieses Formular ist nicht geöffnet.")
    if not logic.in_window(defn, _today()):
        raise HTTPException(409, "Die Frist für dieses Formular ist abgelaufen oder noch nicht begonnen.")
    sid = body.student_id or (allowed[0] if len(allowed) == 1 and (ctx.role in ("eltern", "schueler")
                                                                    or logic.has_student_field(defn)) else None)
    if sid is not None and sid not in allowed:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    if sid is None and (ctx.role in ("eltern", "schueler") or logic.has_student_field(defn)):
        raise HTTPException(422, "Bitte die Schülerin / den Schüler auswählen")
    if defn.get("once") and sid is not None and db.scalar(
            select(func.count()).select_from(FormSubmission).where(
                FormSubmission.template_id == tmpl.id, FormSubmission.student_id == sid,
                FormSubmission.status.not_in(("abgelehnt", "zurueckgezogen")))):
        raise HTTPException(409, f"Für {ctx.students[sid].name} liegt dieses Formular bereits vor.")
    today = _today()
    try:
        answers = logic.clean_answers(defn, body.answers, student_id=sid, periods=ctx.school.settings.periods,
                                      today=today, signer=user.display_name or user.username)
    except logic.FormError as exc:
        raise HTTPException(422, str(exc)) from None
    st = ctx.students.get(sid) if sid else None
    sub = FormSubmission(template_id=tmpl.id, version_id=ver.id, student_id=sid, class_id=st.class_id if st else None,
                         submitted_by=user.id or None, submitted_by_name=user.display_name or user.username,
                         submitted_role=user.role, status="eingereicht", step=0, scan_file_ids=[],
                         due_on=logic.due_date(defn, today), created_at=utcnow())
    db.add(sub)
    db.flush()
    _set_answers(sub, answers)
    _attach_answer_files(ctx, sub, defn, answers)
    _event(db, sub, "eingereicht", user)
    write_audit(db, user, "form_submission.create", f"form_submission:{sub.id}",
                {"template_id": tmpl.id, "version": ver.version, "student_id": sid})
    if (defn.get("workflow") or {}).get("auto_complete"):
        sub.status = "erledigt"
        sub.decided_at, sub.decided_by_name = utcnow(), "automatisch"
        _event(db, sub, "erledigt", None)
        _run_actions(ctx, sub, defn, answers, user)
    db.commit()
    _notify_submitted(ctx, sub, defn)
    return _sub_out(ctx, sub, detail=True)


# =========================================================================== Benachrichtigung
def _publish_users(ids: set[int]) -> None:
    ids = {i for i in ids if i}
    if ids:
        try:
            from schulmanager.server.events import bus
            bus.publish("change", {"version": None, "scope": ["forms"], "dates": []}, user_ids=ids)
        except Exception:  # pragma: no cover - Hinweise dürfen nie stören
            pass


def approver_user_ids(ctx: Ctx, sub: FormSubmission, step: Optional[dict]) -> set[int]:
    """Konten, die den aktuellen Prüfschritt bearbeiten können (für Live-Hinweise); die Schulleitung immer."""
    from schulmanager.server.db_models import User
    ids: set[int] = set(ctx.db.scalars(select(User.id).where(User.role == "schulleitung", User.active.is_(True))))
    if step is None:
        return ids
    kind = step.get("approver")
    if kind == "user" and step.get("user_id"):
        ids.add(step["user_id"])
    elif kind == "sekretariat":
        ids |= set(ctx.db.scalars(select(User.id).where(User.role == "sekretariat", User.active.is_(True))))
    elif kind == "class_teacher":
        leader = ctx.class_leader(sub.class_id)
        if leader:
            ids |= set(ctx.db.scalars(select(User.id).where(User.teacher_id == leader, User.active.is_(True),
                                                            User.role.in_(LEAD_ROLES))))
        else:
            ids |= set(ctx.db.scalars(select(User.id).where(User.role == "sekretariat", User.active.is_(True))))
    return ids


def family_user_ids(ctx: Ctx, sub: FormSubmission) -> set[int]:
    from schulmanager.server.db_models import ParentLink, User
    ids: set[int] = {sub.submitted_by} if sub.submitted_by else set()
    if sub.student_id:
        ids |= set(ctx.db.scalars(select(ParentLink.parent_user_id).where(ParentLink.student_id == sub.student_id)))
        ids |= set(ctx.db.scalars(select(User.id).where(User.student_id == sub.student_id, User.role == "schueler",
                                                        User.active.is_(True))))
    return ids


def _notify_submitted(ctx: Ctx, sub: FormSubmission, defn: dict) -> None:
    steps = (defn.get("workflow") or {}).get("steps") or []
    step = steps[0] if sub.status in logic.OPEN_STATUSES and steps else None
    ids = approver_user_ids(ctx, sub, step) if step else set()
    if sub.status == "erledigt" or not steps:           # ohne Prüfschritte: Eingang der Verwaltung zeigen
        from schulmanager.server.db_models import User
        ids |= set(ctx.db.scalars(select(User.id).where(User.role.in_(("schulleitung", "sekretariat")),
                                                        User.active.is_(True))))
        leader = ctx.class_leader(sub.class_id)
        if leader:
            ids |= set(ctx.db.scalars(select(User.id).where(User.teacher_id == leader, User.active.is_(True),
                                                            User.role.in_(LEAD_ROLES))))
    ids |= {sub.submitted_by} if sub.submitted_by else set()
    _publish_users(ids)
    publish_change(["forms"])


# =========================================================================== Aktionen bei Genehmigung
def _run_actions(ctx: Ctx, sub: FormSubmission, defn: dict, answers: dict, actor: AuthUser) -> None:
    """Aktionen des Formulars ausführen; Fehler brechen die Entscheidung nicht ab, sondern stehen im Ergebnis."""
    results: list[dict] = []
    for action in defn.get("actions") or []:
        kind = action["type"]
        try:
            if kind == "create_absence":
                results.append(_action_absence(ctx, sub, action, answers, actor))
            elif kind == "inform_teachers":
                results.append(_action_inform(ctx, sub, defn, answers))
            elif kind == "calendar_entry":
                results.append(_action_calendar(ctx, sub, action, answers, actor))
        except HTTPException as exc:
            message = str(exc.detail)
            if exc.status_code in (403, 404):
                message = ("Der Eintrag konnte mit den Rechten dieses Kontos nicht angelegt werden – bitte "
                           "Klassenleitung oder Sekretariat: „Aktionen erneut ausführen“.")
            results.append({"type": kind, "ok": False, "message": message})
        except Exception as exc:  # noqa: BLE001 - eine Aktion darf die Entscheidung nie verhindern
            results.append({"type": kind, "ok": False, "message": f"Nicht ausgeführt ({type(exc).__name__})"})
    sub.result = {"actions": results, "at": iso(utcnow())} if results else sub.result
    if results:
        _event(ctx.db, sub, "aktion", None, "; ".join(
            f"{logic.ACTION_TYPES.get(r['type'], r['type'])}: {'ok' if r['ok'] else r['message']}" for r in results))


def _range_of(answers: dict, fid: Optional[str]) -> tuple[date, date]:
    value = answers.get(fid or "")
    if isinstance(value, dict):
        d1 = date.fromisoformat(value["from"])
        return d1, date.fromisoformat(value.get("to") or value["from"])
    d1 = date.fromisoformat(str(value))
    return d1, d1


def _action_absence(ctx: Ctx, sub: FormSubmission, action: dict, answers: dict, actor: AuthUser) -> dict:
    from .features_student_absences import StudentAbsenceIn, report_student_absence
    sid = answers.get(action.get("student") or "") or sub.student_id
    if not sid:
        raise HTTPException(422, "Kein Kind angegeben")
    d1, d2 = _range_of(answers, action.get("range"))
    periods = answers.get(action.get("periods") or "") or []
    reason = str(answers.get(action.get("reason") or "") or "")
    kind = action["kind"]
    if kind == "beurlaubung" and not reason.strip():
        reason = "Beurlaubung laut Antrag"
    body = StudentAbsenceIn(student_id=sid, date_from=d1, date_to=d2, periods=list(periods), reason=reason[:1000],
                            kind=kind, source="schriftlich", status=action.get("status") or "entschuldigt")
    from schulmanager.server.absence_log import channel_override
    with channel_override("formular"):
        out = report_student_absence(body, Response(), user=actor, db=ctx.db)
    return {"type": "create_absence", "ok": True, "absence_id": out.get("id"), "message": "Eintrag angelegt"}


def _action_inform(ctx: Ctx, sub: FormSubmission, defn: dict, answers: dict) -> dict:
    """Lehrkräfte der betroffenen Stunden: Live-Hinweis (ohne Inhalt); der Eintrag selbst steht in „Fehlt heute in
    meiner Stunde“ bzw. in der genehmigten Beurlaubung."""
    from schulmanager.server.absence_access import taught_students
    from schulmanager.server.db_models import User
    sid = sub.student_id
    teachers = {t.id for t in ctx.school.teachers if sid and sid in taught_students(ctx.school, t.id)}
    leader = ctx.class_leader(sub.class_id)
    if leader:
        teachers.add(leader)
    ids = set(ctx.db.scalars(select(User.id).where(User.teacher_id.in_(sorted(teachers)), User.active.is_(True)))) \
        if teachers else set()
    try:
        from schulmanager.server.events import bus
        if ids:
            bus.publish("change", {"version": None, "scope": ["forms", "student_absences"], "dates": []},
                        user_ids=ids)
    except Exception:  # pragma: no cover
        pass
    return {"type": "inform_teachers", "ok": True, "message": f"{len(teachers)} Lehrkräfte informiert"}


def _action_calendar(ctx: Ctx, sub: FormSubmission, action: dict, answers: dict, actor: AuthUser) -> dict:
    from schulmanager.models import Event

    from .features_common import check_id, mutate, new_id
    d1, d2 = _range_of(answers, action.get("date"))
    class_id = sub.class_id
    title = action["title"]

    def fn(school):
        from .features_data import _raise_errors, validate_item
        for e in school.events:
            if e.title == title and e.date_from == d1.isoformat() and (not class_id or class_id in e.classes):
                return None
        ev = Event(id=check_id(new_id([e.id for e in school.events], "F")), title=title, date_from=d1.isoformat(),
                   date_to=d2.isoformat() if d2 != d1 else "", kind="termin",
                   classes=[class_id] if class_id else [], grades=[])
        _raise_errors(validate_item(school, "events", ev))
        school.events.append(ev)
        return ev.id

    mutate(actor, f"Termin „{title}“ aus Formular", fn, scope=["events", "holidays"],
           dates=[d1.isoformat(), d2.isoformat()])
    return {"type": "calendar_entry", "ok": True, "message": "Termin eingetragen"}


# =========================================================================== Eingang / Listen
def _sub_query(ctx: Ctx, **filters):
    q = select(FormSubmission)
    if filters.get("template_id"):
        q = q.where(FormSubmission.template_id == filters["template_id"])
    if filters.get("status"):
        q = q.where(FormSubmission.status == filters["status"])
    elif filters.get("open_only"):
        q = q.where(FormSubmission.status.in_(logic.OPEN_STATUSES))
    if filters.get("student_id"):
        q = q.where(FormSubmission.student_id == filters["student_id"])
    if filters.get("class_id"):
        q = q.where(FormSubmission.class_id == filters["class_id"])
    return q.order_by(FormSubmission.id.desc()).limit(MAX_LIST)


@router.get("/forms/submissions")
def list_submissions(template_id: Optional[int] = None, status: Optional[str] = Query(None, max_length=14),
                     class_id: Optional[str] = Query(None, max_length=40),
                     student_id: Optional[str] = Query(None, max_length=40),
                     scope: Literal["inbox", "mine", "all"] = "all", open_only: bool = False,
                     q: Optional[str] = Query(None, max_length=80),
                     user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Einreichungen im Umfang des Kontos (ohne Antworten). ``scope=inbox``: nur solche, die das Konto jetzt
    entscheiden kann; ``mine``: von mir bzw. meiner Familie."""
    ctx = Ctx(user, db)
    if status and status not in logic.STATUS_LABELS:
        raise HTTPException(422, "Unbekannter Status")
    if not (ctx.inbox or ctx.submit or ctx.role in ("eltern", "schueler")):
        raise HTTPException(403, "Keine Berechtigung")
    rows = db.scalars(_sub_query(ctx, template_id=template_id, status=status, class_id=class_id,
                                 student_id=student_id, open_only=open_only)).all()
    needle = (q or "").strip().lower()
    out = []
    for sub in rows:
        if not ctx.can_view(sub):
            continue
        if scope == "mine" and sub.submitted_by != user.id and sub.student_id not in ctx.own_ids:
            continue
        item = _sub_out(ctx, sub)
        if scope == "inbox" and not item["can_decide"]:
            continue
        if needle and needle not in " ".join(str(x or "") for x in (
                item["template_title"], item["student_name"], item["submitted_by_name"], item["class_id"])).lower():
            continue
        out.append(item)
    return out


@router.get("/forms/submissions/{sub_id}")
def get_submission(sub_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    _audit_view(ctx, sub)
    return _sub_out(ctx, sub, detail=True)


class DecideIn(BaseModel):
    action: Literal["approve", "reject", "complete", "comment"]
    note: str = Field("", max_length=1000)


@router.post("/forms/submissions/{sub_id}/decide")
def decide(sub_id: int, body: DecideIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Prüfschritt entscheiden: ``approve`` (nächster Schritt bzw. genehmigt + Aktionen), ``reject`` (Begründung
    nötig), ``complete`` (als erledigt abschließen), ``comment`` (Vermerk ohne Statusänderung)."""
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    defn = ctx.version(sub.version_id).definition
    note = logic.clean_text(body.note, 1000, multiline=True)
    now = utcnow()
    name = user.display_name or user.username
    if body.action == "comment":
        if not ctx.inbox:
            raise HTTPException(403, "Keine Berechtigung")
        if not note:
            raise HTTPException(422, "Bitte einen Vermerk eingeben")
        _event(db, sub, "kommentar", user, note)
    elif body.action == "complete":
        if not ctx.can_complete(sub):
            raise HTTPException(403, "Diese Einreichung können Sie nicht abschließen.")
        first = sub.status in logic.OPEN_STATUSES
        sub.status, sub.decided_at, sub.decided_by_name = "erledigt", now, name
        _event(db, sub, "erledigt", user, note)
        if first:
            _run_actions(ctx, sub, defn, _answers_of(sub), user)
    else:
        if not ctx.can_decide(sub):
            raise HTTPException(403, "Diesen Schritt entscheidet eine andere Stelle.")
        steps = defn["workflow"]["steps"]
        if body.action == "reject":
            if not note:
                raise HTTPException(422, "Bitte kurz begründen, warum das Formular abgelehnt wird.")
            sub.status, sub.decided_at, sub.decided_by_name = "abgelehnt", now, name
            sub.decision_note_enc = _enc(note, "decision", sub.id)
            _event(db, sub, "abgelehnt", user, note)
        else:
            last = sub.step + 1 >= len(steps)
            _event(db, sub, "genehmigt" if last else "geprueft", user, note)
            if last:
                sub.status, sub.decided_at, sub.decided_by_name = "genehmigt", now, name
                if note:
                    sub.decision_note_enc = _enc(note, "decision", sub.id)
                _run_actions(ctx, sub, defn, _answers_of(sub), user)
            else:
                sub.step += 1
                sub.status = "in_pruefung"
                sub.reminded_on = None
    sub.updated_at = now
    write_audit(db, user, f"form_submission.{body.action}", f"form_submission:{sub.id}",
                {"template_id": sub.template_id, "status": sub.status})
    db.commit()
    _publish_users(family_user_ids(ctx, sub) | (approver_user_ids(ctx, sub, ctx.current_step(sub))
                                                 if sub.status in logic.OPEN_STATUSES else set()))
    publish_change(["forms", "student_absences"] if sub.result else ["forms"])
    if body.action in ("approve", "reject", "complete"):  # Glocke: Antrag entschieden
        from schulmanager.server import notification_hooks
        notification_hooks.form_decided(sub.id, user.id or None)
    return _sub_out(ctx, sub, detail=True)


@router.post("/forms/submissions/{sub_id}/retry-actions")
def retry_actions(sub_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Aktionen einer genehmigten Einreichung erneut ausführen (z. B. nach einem Fehler: Zeitraum ohne Schultag)."""
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    if sub.status not in ("genehmigt", "erledigt") or not ctx.inbox:
        raise HTTPException(403, "Keine Berechtigung")
    done = {(r.get("type")) for r in (sub.result or {}).get("actions", []) if r.get("ok")}
    defn = dict(ctx.version(sub.version_id).definition)
    defn["actions"] = [a for a in defn.get("actions") or [] if a["type"] not in done]
    if not defn["actions"]:
        raise HTTPException(409, "Alle Aktionen sind bereits ausgeführt.")
    old = list((sub.result or {}).get("actions", []))
    _run_actions(ctx, sub, defn, _answers_of(sub), user)
    new = (sub.result or {}).get("actions", [])
    sub.result = {"actions": [r for r in old if r.get("ok")] + new, "at": iso(utcnow())}
    sub.updated_at = utcnow()
    write_audit(db, user, "form_submission.retry", f"form_submission:{sub.id}", {})
    db.commit()
    publish_change(["forms", "student_absences"])
    return _sub_out(ctx, sub, detail=True)


@router.post("/forms/submissions/{sub_id}/withdraw")
def withdraw(sub_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Einreichung zurückziehen, solange noch kein Prüfschritt begonnen hat (bleibt als „zurückgezogen“ erhalten)."""
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    if not ctx.can_withdraw(sub):
        raise HTTPException(403, "Diese Einreichung lässt sich nicht mehr zurückziehen.")
    sub.status, sub.updated_at = "zurueckgezogen", utcnow()
    _event(db, sub, "zurueckgezogen", user)
    write_audit(db, user, "form_submission.withdraw", f"form_submission:{sub.id}", {})
    db.commit()
    _publish_users(family_user_ids(ctx, sub) | approver_user_ids(ctx, sub, None))
    publish_change(["forms"])
    return _sub_out(ctx, sub, detail=True)


# -- Scans
class ScanIn(BaseModel):
    file_id: str = Field(..., max_length=36)


@router.post("/forms/submissions/{sub_id}/scan")
def add_scan(sub_id: int, body: ScanIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Unterschriebenen Scan/Foto anhängen (Datei vorher über ``POST /files?purpose=form_file``)."""
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    if not ctx.can_scan(sub):
        raise HTTPException(403, "Hier lässt sich nichts mehr hochladen.")
    if len(sub.scan_file_ids or []) >= logic.MAX_FILES * 2:
        raise HTTPException(409, "Es sind bereits genug Dateien angehängt.")
    files.attach(db, body.file_id, user, REF_TYPE, sub.id, kinds=["pdf", "image"])
    sub.scan_file_ids = [*(sub.scan_file_ids or []), body.file_id]
    sub.updated_at = utcnow()
    _event(db, sub, "scan", user)
    write_audit(db, user, "form_submission.scan", f"form_submission:{sub.id}", {})
    db.commit()
    publish_change(["forms"])
    return _sub_out(ctx, sub, detail=True)


@router.delete("/forms/submissions/{sub_id}/scan/{file_id}")
def remove_scan(sub_id: int, file_id: str, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    ctx = Ctx(user, db)
    sub = _get_sub(ctx, sub_id)
    ids = list(sub.scan_file_ids or [])
    if file_id not in ids:
        raise HTTPException(404, "Datei nicht gefunden")
    meta = files.get_file(db, file_id)
    if not (ctx.can_scan(sub) and (ctx.inbox or (meta is not None and meta.owner_user_id == user.id))):
        raise HTTPException(403, "Keine Berechtigung")
    ids.remove(file_id)
    sub.scan_file_ids = ids
    files.delete(db, file_id, user, hard=True)
    write_audit(db, user, "form_submission.scan_delete", f"form_submission:{sub.id}", {})
    db.commit()
    publish_change(["forms"])
    return _sub_out(ctx, sub, detail=True)


def _file_access(db: Session, user, meta) -> bool:
    try:
        sub = db.get(FormSubmission, int(meta.ref_id or 0))
    except (TypeError, ValueError):
        return False
    return sub is not None and Ctx(user, db).can_view(sub)


files.register_access_check(REF_TYPE, _file_access)


# =========================================================================== Export / Zähler
def _export_rows(ctx: Ctx, template_id: int, status: Optional[str]) -> tuple[list[str], list[list[str]], FormTemplate]:
    tmpl = _get_template(ctx.db, template_id)
    subs = [s for s in ctx.db.scalars(_sub_query(ctx, template_id=template_id, status=status)) if ctx.can_view(s)]
    subs.sort(key=lambda s: s.id)
    fields: dict[str, str] = {}
    for ver in ctx.db.scalars(select(FormVersion).where(FormVersion.template_id == template_id)
                              .order_by(FormVersion.version)):
        for f in ver.definition["fields"]:
            if f["type"] not in ("student",):
                fields.setdefault(f["id"], f["label"])
    header = ["Nr", "Version", "Status", "Schüler/in", "Klasse", "Eingereicht von", "Eingereicht am", "Entschieden von",
              "Entschieden am", *fields.values()]
    rows = []
    for sub in subs:
        ver = ctx.version(sub.version_id)
        answers = _answers_of(sub)
        by_id = {f["id"]: f for f in ver.definition["fields"]}
        st = ctx.students.get(sub.student_id) if sub.student_id else None
        rows.append([str(sub.id), str(ver.version), STATUS_LABELS.get(sub.status, sub.status),
                     st.name if st else "", sub.class_id or "", sub.submitted_by_name,
                     iso(sub.created_at)[:10], sub.decided_by_name or "", (iso(sub.decided_at) or "")[:10],
                     *[logic.display_value(by_id[fid], answers.get(fid)) if fid in by_id else "" for fid in fields]])
    return header, rows, tmpl


@router.get("/forms/export.csv")
def export_csv(template_id: int, status: Optional[str] = Query(None, max_length=14),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    """Einreichungen einer Vorlage als CSV (Semikolon, UTF-8 mit BOM für Excel) – nur im Umfang des Eingangs."""
    ctx = Ctx(user, db)
    if not ctx.inbox:
        raise HTTPException(403, "Keine Berechtigung")
    header, rows, tmpl = _export_rows(ctx, template_id, status)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    writer.writerow([logic.csv_cell(c) for c in header])
    for row in rows:
        writer.writerow([logic.csv_cell(c) for c in row])
    write_audit(db, user, "form_submission.export", f"form_template:{tmpl.id}", {"format": "csv", "rows": len(rows)})
    db.commit()
    from schulmanager.server.files import content_disposition
    name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in tmpl.title) + ".csv"
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": content_disposition(name)})


@router.get("/forms/export.pdf")
def export_pdf(template_id: int, status: Optional[str] = Query(None, max_length=14),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    """Alle sichtbaren Einreichungen einer Vorlage als ein PDF (jede beginnt auf einer neuen Seite)."""
    from schulmanager.server.form_pdf import render_forms
    ctx = Ctx(user, db)
    if not ctx.inbox:
        raise HTTPException(403, "Keine Berechtigung")
    tmpl = _get_template(db, template_id)
    subs = sorted((s for s in db.scalars(_sub_query(ctx, template_id=template_id, status=status))
                   if ctx.can_view(s)), key=lambda s: s.id)
    if not subs:
        raise HTTPException(404, "Keine Einreichungen im Umfang Ihres Kontos")
    items = []
    for sub in subs[:300]:
        item = _filled_item(ctx, sub)
        item.pop("version")
        items.append(item)
    pdf = render_forms(tmpl.title, items, school_name=ctx.school.settings.school_name or "Schule")
    write_audit(db, user, "form_submission.export", f"form_template:{tmpl.id}", {"format": "pdf", "rows": len(items)})
    db.commit()
    return _pdf_response(pdf, f"{tmpl.title}_Archiv.pdf")


@router.get("/forms/summary")
def summary(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Zähler für Menü-Badge und Startseite: ``to_decide`` (Eingang, jetzt zu entscheiden), ``overdue`` (davon
    überfällig), ``to_fill`` (offene Rückmeldungen/Einwilligungen mit Frist, die noch fehlen), ``mine_open``
    (eigene laufende Einreichungen)."""
    ctx = Ctx(user, db)
    to_decide = overdue = to_fill = mine_open = 0
    today = _today()
    if ctx.inbox:
        for sub in db.scalars(select(FormSubmission).where(FormSubmission.status.in_(logic.OPEN_STATUSES))
                              .limit(MAX_LIST)):
            if ctx.can_view(sub) and ctx.can_decide(sub):
                to_decide += 1
                overdue += bool(sub.due_on and sub.due_on < today.isoformat())
    if ctx.submit:
        mine = _my_open_map(ctx)
        for tmpl in db.scalars(select(FormTemplate).where(FormTemplate.status == "aktiv")):
            defn = _current_version(db, tmpl).definition
            deadline = (defn.get("deadline") or {}).get("open_until")
            if not logic.in_window(defn, today) or not (defn.get("once") or deadline):
                continue                    # nur Rückmeldungen/Einwilligungen werden „erwartet“
            students = fill_students(ctx, defn)
            if students:
                to_fill += sum(1 for s in students if (tmpl.id, s) not in mine)
            elif students == [] and ctx.role not in ("eltern", "schueler") and (tmpl.id, None) not in mine \
                    and not logic.has_student_field(defn):
                to_fill += 1
        mine_open = db.scalar(select(func.count()).select_from(FormSubmission).where(
            FormSubmission.submitted_by == user.id, FormSubmission.status.in_(logic.OPEN_STATUSES))) or 0
    return {"to_decide": to_decide, "overdue": overdue, "to_fill": to_fill, "mine_open": mine_open}


# =========================================================================== Wartung / Export (DSGVO)
def run_reminders(today: Optional[date] = None) -> int:
    """Erinnerung an die Prüfenden: offene Einreichungen, deren Vorlage eine Erinnerung (``remind_days``) kennt und die
    seit so vielen Tagen unbearbeitet sind (danach wieder nach derselben Zeit). Live-Hinweis + Verlaufseintrag."""
    from schulmanager.server.db import session_scope
    today = today or _today()
    n = 0
    with session_scope() as db:
        ctx = Ctx(AuthUser(id=0, username="system", display_name="System", role="admin"), db)
        for sub in db.scalars(select(FormSubmission).where(FormSubmission.status.in_(logic.OPEN_STATUSES))
                              .limit(MAX_LIST)):
            defn = ctx.version(sub.version_id).definition
            days = (defn.get("deadline") or {}).get("remind_days")
            if not days:
                continue
            base = date.fromisoformat(sub.reminded_on) if sub.reminded_on else (sub.updated_at or sub.created_at).date()
            if (today - base).days < days:
                continue
            sub.reminded_on = today.isoformat()
            _event(db, sub, "erinnerung", None)
            _publish_users(approver_user_ids(ctx, sub, ctx.current_step(sub)))
            n += 1
    return n


def run_retention(days: int) -> int:
    """Wartung: abgeschlossene Einreichungen älter als ``days`` Tage samt Dateien löschen; 0 = aus."""
    from schulmanager.server.db import session_scope
    if days <= 0:
        return 0
    cutoff = utcnow() - timedelta(days=days)
    n = 0
    with session_scope() as db:
        for sub in db.scalars(select(FormSubmission).where(FormSubmission.created_at < cutoff,
                                                           FormSubmission.status.in_(logic.FINAL_STATUSES))
                              .limit(5000)).all():
            files.delete_for_ref(db, REF_TYPE, sub.id, hard=True)
            db.delete(sub)
            n += 1
    return n


def export_rows(db: Session, user) -> list[dict]:
    """DSGVO-Export: eigene Einreichungen (Antworten als Text)."""
    ctx = Ctx(user, db)
    out = []
    for sub in db.scalars(select(FormSubmission).where(FormSubmission.submitted_by == user.id)
                          .order_by(FormSubmission.id)):
        ver = ctx.version(sub.version_id)
        answers = _answers_of(sub)
        out.append({"id": sub.id, "form": ver.title, "status": sub.status, "created_at": iso(sub.created_at),
                    "student_id": sub.student_id,
                    "answers": {f["label"]: logic.display_value(f, answers.get(f["id"])) for f in ver.definition["fields"]
                                if f["type"] != "signature"}})
    return out
