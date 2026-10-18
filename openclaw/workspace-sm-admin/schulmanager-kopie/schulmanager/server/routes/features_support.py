"""Förderinformationen je Schüler/in: Nachteilsausgleich, Schulbegleitung, Förderplan, Merkmale (mit Nachweisen).

* ``GET    /students/{sid}/support`` – Einträge; **Vollsicht** (Details, Diagnose, Nachweise): Schulleitung, Sekretariat,
  Klassenleitung (Recht ``support.read``), Schüler/in selbst bzw. Eltern (volljährige nur mit Freigabe „dokumente“);
  **Kurzsicht** für Lehrkräfte mit ``support.hints`` (nur Art, Minuten, Fächer, Hilfsmittel der für Lehrkräfte
  freigegebenen Katalogarten – weder Diagnose noch Nachweis); technische Administration nie.
* ``POST/PUT/DELETE /students/{sid}/support[/{id}]`` – Recht ``support.manage`` (Klassenleitung nur eigene Klasse)
* ``GET/POST/PUT/DELETE /support/catalog`` – Katalog der Merkmale (``support.catalog``)
* ``GET    /students/support-flags`` – Kennzeichen je Schüler/in für Listen/Klassenbuch (nach Sicht gefiltert)
* ``GET    /exams/support-hints`` – Hinweis je Klausur/Test: betroffene Schüler/innen mit Ausgleich
* ``GET    /students/{sid}/people`` – Eltern, Klassenleitung, Fachlehrkräfte
Titel, Details und Hilfsmittel verschlüsselt; Dateien (PDF/Fotos) verschlüsselt in der Dateiablage; Audit-Log bei
Lesen der Vollsicht und jeder Änderung.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server import crypto, files
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.db_models import ParentLink, User
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.support import DEFAULT_CATALOG, SUPPORT_KINDS, StudentSupport, SupportCatalog

from .features_common import (can_see_student, has, own_class_ids, parse_date, perm_scope, publish_change,
                              snapshot, student_parts, teacher_course_ids, write_audit)
from .features_grades import _may_see

router = APIRouter(tags=["Förderung"])
REF_TYPE = "student_support"
AREA = "dokumente"                # Elternzugriff: Förderinformationen gehören zu den Dokumenten


class SupportIn(BaseModel):
    kind: Literal["nachteilsausgleich", "schulbegleitung", "foerderplan", "sonstiges"] = "nachteilsausgleich"
    title: str = Field("", max_length=200)
    details: str = Field("", max_length=5000)
    catalog_id: Optional[int] = None
    minutes: Optional[int] = Field(None, ge=0, le=600)
    subjects: list[str] = Field(default_factory=list, max_length=30)
    aids: str = Field("", max_length=500)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    file_ids: list[str] = Field(default_factory=list, max_length=10)


class CatalogIn(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    kind: Literal["nachteilsausgleich", "schulbegleitung", "foerderplan", "sonstiges"] = "nachteilsausgleich"
    uses_minutes: bool = False
    default_minutes: Optional[int] = Field(None, ge=0, le=600)
    teacher_visible: bool = True
    active: bool = True
    sort: int = Field(0, ge=0, le=9999)


def _dec(token: str, aad: str) -> str:
    if not token:
        return ""
    try:
        return crypto.decrypt_text(token, aad)
    except Exception:  # noqa: BLE001
        return ""


# ------------------------------------------------------------------------------------------------ Katalog
def ensure_catalog(db: Session) -> list[SupportCatalog]:
    """Katalog der Schule; ist er leer, werden die Vorgaben angelegt."""
    rows = list(db.scalars(select(SupportCatalog).order_by(SupportCatalog.sort, SupportCatalog.id)))
    if rows:
        return rows
    for n, (label, kind, minutes, default, visible) in enumerate(DEFAULT_CATALOG):
        db.add(SupportCatalog(label=label, kind=kind, uses_minutes=minutes, default_minutes=default,
                              teacher_visible=visible, active=True, sort=(n + 1) * 10))
    db.commit()
    return list(db.scalars(select(SupportCatalog).order_by(SupportCatalog.sort, SupportCatalog.id)))


def _catalog_out(c: SupportCatalog) -> dict[str, Any]:
    return {"id": c.id, "label": c.label, "kind": c.kind, "kind_label": SUPPORT_KINDS.get(c.kind, c.kind),
            "uses_minutes": c.uses_minutes, "default_minutes": c.default_minutes,
            "teacher_visible": c.teacher_visible, "active": c.active, "sort": c.sort}


def _may_catalog(user) -> bool:
    return getattr(user, "role", "") not in ("schueler", "eltern") and has(user, "support.catalog")


# ------------------------------------------------------------------------------------------------ Rechte
def _is_class_teacher(user, sid: str, snap) -> bool:
    st = snap[1].index("students").get(sid)
    cls = snap[1].index("classes").get(st.class_id) if st else None
    tid = getattr(user, "teacher_id", None)
    return bool(cls and tid and cls.class_teacher == tid)


def _mode(db: Session, user, sid: str, snap) -> Optional[str]:
    """``"full"`` (Details, Diagnose, Nachweise), ``"hints"`` (nur Ausgleichsart für den Unterricht) oder ``None``."""
    role = getattr(user, "role", "")
    if role == "admin":                                   # technische Administration: nie (Gesundheitsdaten)
        return None
    if role in ("schueler", "eltern"):
        return "full" if _may_see(db, user, sid, snap, AREA) else None
    if has(user, "support.read"):
        scope = perm_scope(user, "support.read")
        if scope is None:
            return "full"
        if scope == "class_teacher" and _is_class_teacher(user, sid, snap):
            return "full"
        if scope == "own_branch":
            st = snap[1].index("students").get(sid)
            if st and st.class_id in own_class_ids(user, snap):
                return "full"
    if has(user, "support.hints") and can_see_student(user, sid, snap):
        return "hints"
    return None


def _may_edit(user, sid: str, snap) -> bool:
    if getattr(user, "role", "") in ("schueler", "eltern", "admin") or not has(user, "support.manage"):
        return False
    scope = perm_scope(user, "support.manage")
    return scope is None or (scope == "class_teacher" and _is_class_teacher(user, sid, snap))


def _valid_on(row: StudentSupport, day: str) -> bool:
    return not ((row.valid_from and row.valid_from > day) or (row.valid_to and row.valid_to < day))


def _teacher_visible(row: StudentSupport, cat: Optional[SupportCatalog]) -> bool:
    if cat is not None:
        return cat.teacher_visible
    return row.kind == "nachteilsausgleich"          # ältere Freitext-Einträge: nur Ausgleiche, nie Details


def _label(row: StudentSupport, cat: Optional[SupportCatalog]) -> str:
    if cat is not None:
        return cat.label
    return _dec(row.title_enc, row.aad("title")) or SUPPORT_KINDS.get(row.kind, row.kind)


def _out(db: Session, user, row: StudentSupport, can_edit: bool, cat: Optional[SupportCatalog]) -> dict[str, Any]:
    return {"id": row.id, "student_id": row.student_id, "kind": row.kind,
            "kind_label": SUPPORT_KINDS.get(row.kind, row.kind), "title": _dec(row.title_enc, row.aad("title")),
            "details": _dec(row.details_enc, row.aad("details")), "catalog_id": row.catalog_id,
            "label": _label(row, cat), "minutes": row.minutes, "subjects": list(row.subjects or []),
            "aids": _dec(row.aids_enc, row.aad("aids")), "valid_from": row.valid_from,
            "valid_to": row.valid_to, "files": files.files_info(db, row.file_ids or [], user, check_access=False),
            "created_by_name": row.created_by_name, "created_at": iso(row.created_at),
            "updated_at": iso(row.updated_at), "can_edit": can_edit, "level": "full"}


def _hint_out(row: StudentSupport, cat: Optional[SupportCatalog]) -> dict[str, Any]:
    """Kurzsicht für Lehrkräfte: Art des Ausgleichs – keine Diagnose, keine Details, keine Nachweise."""
    return {"id": row.id, "student_id": row.student_id, "kind": "nachteilsausgleich",
            "kind_label": SUPPORT_KINDS["nachteilsausgleich"], "label": _label(row, cat), "minutes": row.minutes,
            "subjects": list(row.subjects or []), "aids": _dec(row.aids_enc, row.aad("aids")),
            "valid_from": row.valid_from, "valid_to": row.valid_to, "files": [], "can_edit": False,
            "level": "hints"}


def _student_or_404(snap, sid: str):
    st = snap[1].index("students").get(sid)
    if st is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    return st


@router.get("/support/catalog")
def get_catalog(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    manage = _may_catalog(user)
    if getattr(user, "role", "") in ("schueler", "eltern") or not (
            manage or has(user, "support.manage") or has(user, "support.read")):
        raise HTTPException(403, "Keine Berechtigung")
    rows = ensure_catalog(db)
    return {"can_manage": manage, "kinds": SUPPORT_KINDS,
            "items": [_catalog_out(c) for c in rows if manage or c.active]}


def _catalog_apply(row: SupportCatalog, body: CatalogIn) -> None:
    row.label = body.label.strip()
    row.kind = body.kind
    row.uses_minutes = body.uses_minutes
    row.default_minutes = body.default_minutes if body.uses_minutes else None
    row.teacher_visible = body.teacher_visible
    row.active = body.active
    row.sort = body.sort


@router.post("/support/catalog", status_code=201)
def create_catalog(body: CatalogIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    if not _may_catalog(user):
        raise HTTPException(403, "Den Katalog pflegen Schulleitung und Sekretariat")
    rows = ensure_catalog(db)
    if any(c.label.lower() == body.label.strip().lower() for c in rows):
        raise HTTPException(409, "Diese Bezeichnung gibt es schon")
    row = SupportCatalog()
    _catalog_apply(row, body)
    if not body.sort:
        row.sort = max([c.sort for c in rows] + [0]) + 10
    db.add(row)
    db.flush()
    write_audit(db, user, "support_catalog.create", f"support_catalog:{row.id}", {"label": row.label})
    db.commit()
    publish_change(["support_catalog"])
    return _catalog_out(row)


@router.put("/support/catalog/{cid}")
def update_catalog(cid: int, body: CatalogIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    if not _may_catalog(user):
        raise HTTPException(403, "Den Katalog pflegen Schulleitung und Sekretariat")
    row = db.get(SupportCatalog, cid)
    if row is None:
        raise HTTPException(404, "Eintrag nicht gefunden")
    if any(c.id != cid and c.label.lower() == body.label.strip().lower() for c in ensure_catalog(db)):
        raise HTTPException(409, "Diese Bezeichnung gibt es schon")
    _catalog_apply(row, body)
    write_audit(db, user, "support_catalog.update", f"support_catalog:{cid}", {"label": row.label})
    db.commit()
    publish_change(["support_catalog"])
    return _catalog_out(row)


@router.delete("/support/catalog/{cid}")
def delete_catalog(cid: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    if not _may_catalog(user):
        raise HTTPException(403, "Den Katalog pflegen Schulleitung und Sekretariat")
    row = db.get(SupportCatalog, cid)
    if row is None:
        raise HTTPException(404, "Eintrag nicht gefunden")
    if db.scalar(select(StudentSupport.id).where(StudentSupport.catalog_id == cid).limit(1)) is not None:
        raise HTTPException(409, "Die Art ist Schüler/innen zugeordnet – bitte stattdessen deaktivieren")
    db.delete(row)
    write_audit(db, user, "support_catalog.delete", f"support_catalog:{cid}", {"label": row.label})
    db.commit()
    publish_change(["support_catalog"])
    return {"deleted": cid}


# ------------------------------------------------------------------------------------------------ Einträge
def _cat_map(db: Session) -> dict[int, SupportCatalog]:
    return {c.id: c for c in ensure_catalog(db)}


@router.get("/students/{sid}/support")
def list_support(sid: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    st = _student_or_404(snap, sid)
    mode = _mode(db, user, sid, snap)
    if mode is None:
        raise HTTPException(403, "Keine Berechtigung")
    can_edit = _may_edit(user, sid, snap)
    cats = _cat_map(db)
    today = date.today().isoformat()
    rows = list(db.scalars(select(StudentSupport).where(StudentSupport.student_id == sid)
                           .order_by(StudentSupport.id.desc())))
    if mode == "full":
        entries = [_out(db, user, r, can_edit, cats.get(r.catalog_id or 0)) for r in rows]
        write_audit(db, user, "student_support.read", f"student:{sid}", {"entries": len(entries)})
        db.commit()
    else:
        entries = [_hint_out(r, cats.get(r.catalog_id or 0)) for r in rows
                   if _valid_on(r, today) and _teacher_visible(r, cats.get(r.catalog_id or 0))]
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id}, "can_edit": can_edit, "level": mode,
            "kinds": SUPPORT_KINDS,
            "catalog": [_catalog_out(c) for c in cats.values() if c.active] if can_edit else [], "entries": entries}


def _apply(db: Session, user, row: StudentSupport, body: SupportIn, snap) -> None:
    if body.valid_from and body.valid_to and body.valid_to < body.valid_from:
        raise HTTPException(422, "„Bis“ liegt vor „Von“")
    cat = db.get(SupportCatalog, body.catalog_id) if body.catalog_id else None
    if body.catalog_id and cat is None:
        raise HTTPException(422, "Unbekannte Art im Katalog")
    title = body.title.strip() or (cat.label if cat else "")
    if not title:
        raise HTTPException(422, "Bitte eine Art aus dem Katalog oder eine Kurzbeschreibung angeben")
    if cat is not None and not cat.uses_minutes and body.minutes:
        raise HTTPException(422, f"„{cat.label}“ kennt keinen Zeitzuschlag")
    known = {x.id for x in snap[1].subjects}
    bad = [x for x in body.subjects if x not in known]
    if bad:
        raise HTTPException(422, f"Unbekanntes Fach: {bad[0]}")
    row.kind = cat.kind if cat is not None else body.kind
    row.catalog_id = cat.id if cat is not None else None
    row.minutes = body.minutes if (cat is None or cat.uses_minutes) else None
    row.subjects = list(dict.fromkeys(body.subjects)) or None
    row.title_enc = crypto.encrypt_text(title, row.aad("title"))
    row.details_enc = crypto.encrypt_text(body.details.strip(), row.aad("details"))
    row.aids_enc = crypto.encrypt_text(body.aids.strip(), row.aad("aids")) if body.aids.strip() else ""
    row.valid_from = body.valid_from.isoformat() if body.valid_from else None
    row.valid_to = body.valid_to.isoformat() if body.valid_to else None
    old = set(row.file_ids or [])
    new = list(dict.fromkeys(body.file_ids))
    for fid in old - set(new):
        files.detach(db, fid)
    for fid in new:
        if fid not in old:
            files.attach(db, fid, user, REF_TYPE, row.id)
    row.file_ids = new


@router.post("/students/{sid}/support", status_code=201)
def create_support(sid: str, body: SupportIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    snap = snapshot()
    _student_or_404(snap, sid)
    if not _may_edit(user, sid, snap):
        raise HTTPException(403, "Förderinformationen pflegen Sekretariat, Schulleitung und Klassenleitung")
    row = StudentSupport(student_id=sid, kind=body.kind, title_enc="", details_enc="", created_by=user.id or None,
                         created_by_name=user.display_name or user.username, created_at=utcnow())
    db.add(row)
    db.flush()
    _apply(db, user, row, body, snap)
    write_audit(db, user, "student_support.create", f"student_support:{row.id}", {"student_id": sid, "kind": row.kind})
    db.commit()
    publish_change(["student_support"])
    return _out(db, user, row, True, db.get(SupportCatalog, row.catalog_id) if row.catalog_id else None)


def _get(db: Session, sid: str, support_id: int) -> StudentSupport:
    row = db.get(StudentSupport, support_id)
    if row is None or row.student_id != sid:
        raise HTTPException(404, "Eintrag nicht gefunden")
    return row


@router.put("/students/{sid}/support/{support_id}")
def update_support(sid: str, support_id: int, body: SupportIn, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)):
    snap = snapshot()
    if not _may_edit(user, sid, snap):
        raise HTTPException(403, "Keine Berechtigung")
    row = _get(db, sid, support_id)
    _apply(db, user, row, body, snap)
    row.updated_at = utcnow()
    write_audit(db, user, "student_support.update", f"student_support:{row.id}", {"student_id": sid})
    db.commit()
    publish_change(["student_support"])
    return _out(db, user, row, True, db.get(SupportCatalog, row.catalog_id) if row.catalog_id else None)


@router.delete("/students/{sid}/support/{support_id}")
def delete_support(sid: str, support_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    snap = snapshot()
    if not _may_edit(user, sid, snap):
        raise HTTPException(403, "Keine Berechtigung")
    row = _get(db, sid, support_id)
    files.delete_for_ref(db, REF_TYPE, row.id, hard=True)
    db.delete(row)
    write_audit(db, user, "student_support.delete", f"student_support:{support_id}", {"student_id": sid})
    db.commit()
    publish_change(["student_support"])
    return {"deleted": support_id}


def support_flags(db: Session, student_ids: list[str], user=None, snap=None) -> dict[str, list[str]]:
    """Kennzeichen je Schüler/in (Bezeichnungen der aktuell gültigen Einträge) für Klassenbuch/Listen.

    Mit ``user``: nur das, was die Person sehen darf (Kurzsicht: nur für Lehrkräfte freigegebene Arten)."""
    today = date.today().isoformat()
    out: dict[str, list[str]] = {}
    if not student_ids:
        return out
    snap = snap or snapshot()
    cats = _cat_map(db)
    modes: dict[str, Optional[str]] = {}
    for r in db.scalars(select(StudentSupport).where(StudentSupport.student_id.in_(student_ids))):
        if not _valid_on(r, today):
            continue
        cat = cats.get(r.catalog_id or 0)
        if user is not None:
            if r.student_id not in modes:
                modes[r.student_id] = _mode(db, user, r.student_id, snap)
            mode = modes[r.student_id]
            if mode is None or (mode == "hints" and not _teacher_visible(r, cat)):
                continue
        label = cat.label if cat else SUPPORT_KINDS.get(r.kind, r.kind)
        if label not in out.setdefault(r.student_id, []):
            out[r.student_id].append(label)
    return out


@router.get("/students/support-flags")
def flags(class_id: Optional[str] = Query(None, max_length=40), user: AuthUser = Depends(current_user),
          db: Session = Depends(get_db)) -> dict:
    snap = snapshot()
    ids = [s.id for s in snap[1].students if not class_id or s.class_id == class_id]
    return {"flags": support_flags(db, ids, user, snap)}


# ------------------------------------------------------------------------------------------------ Klausur-Hinweise
def _summary(items: list[dict[str, Any]], subjects: dict[str, Any]) -> str:
    parts = []
    for it in items:
        if it["minutes"]:
            txt = f"+{it['minutes']} Min." if it["label"].lower().startswith("zeit") else \
                f"{it['label']} (+{it['minutes']} Min.)"
        else:
            txt = it["label"]
        if it["aids"]:
            txt += f": {it['aids']}"
        if it["subjects"]:
            txt += " (" + ", ".join(subjects[x].name if x in subjects else x for x in it["subjects"]) + ")"
        parts.append(txt)
    return ", ".join(parts)


@router.get("/exams/support-hints")
def exam_hints(date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Je Klausur/Test: Schüler/innen mit Nachteilsausgleich (nur Art, Minuten, Fächer, Hilfsmittel)."""
    if getattr(user, "role", "") == "admin" or not has(user, "support.hints"):
        raise HTTPException(403, "Keine Berechtigung")
    d1 = parse_date(date_from, date.today(), name="from")
    d2 = parse_date(date_to, d1 + timedelta(weeks=8), name="to")
    snap = snapshot()
    school = snap[1]
    scope = perm_scope(user, "support.hints")
    tid = getattr(user, "teacher_id", None)
    courses = school.index("courses")
    classes = school.index("classes")
    subjects = school.index("subjects")
    mine = teacher_course_ids(tid, snap) if tid else frozenset()
    chosen = []
    for e in school.exams:
        if not (d1.isoformat() <= e.date <= d2.isoformat()):
            continue
        c = courses.get(e.course_id)
        if c is None:
            continue
        if scope is not None:           # Lehrkräfte: eigene Kurse(-teile) und Klassen, die sie leiten
            teaches = e.course_id in mine and (e.part is None or e.part >= len(c.parts)
                                               or c.parts[e.part].teacher == tid)
            leads = any(cl in classes and classes[cl].class_teacher == tid for cl in c.classes)
            if not (teaches or leads):
                continue
        chosen.append((e, c))
    if not chosen:
        return {"hints": {}}
    cats = _cat_map(db)
    by_class: dict[str, list] = {}
    for stu in school.students:
        by_class.setdefault(stu.class_id, []).append(stu)
    members: dict[str, list[str]] = {}
    wanted: set[str] = set()
    for e, c in chosen:
        ids = []
        for cl in c.classes:
            for stu in by_class.get(cl, []):
                sel = student_parts(stu.id, snap).get(c.id)
                if sel is not None and (e.part is None or e.part in sel):
                    ids.append(stu.id)
        members[e.id] = ids
        wanted.update(ids)
    rows: dict[str, list[StudentSupport]] = {}
    if wanted:
        for r in db.scalars(select(StudentSupport).where(StudentSupport.student_id.in_(wanted))):
            if _teacher_visible(r, cats.get(r.catalog_id or 0)):
                rows.setdefault(r.student_id, []).append(r)
    students = school.index("students")
    hints: dict[str, list[dict[str, Any]]] = {}
    for e, c in chosen:
        if e.part is not None and e.part < len(c.parts):
            exam_subjects = {c.parts[e.part].subject}
        else:
            exam_subjects = {p.subject for p in c.parts}
        out = []
        for sid in members[e.id]:
            items = []
            for r in rows.get(sid, []):
                if not _valid_on(r, e.date):
                    continue
                if r.subjects and not set(r.subjects) & exam_subjects:
                    continue
                items.append({"label": _label(r, cats.get(r.catalog_id or 0)), "minutes": r.minutes,
                              "subjects": list(r.subjects or []), "aids": _dec(r.aids_enc, r.aad("aids"))})
            if items:
                out.append({"student_id": sid, "name": students[sid].name, "items": items,
                            "minutes": sum(i["minutes"] or 0 for i in items), "summary": _summary(items, subjects)})
        if out:
            hints[e.id] = sorted(out, key=lambda x: x["name"])
    return {"hints": hints}


# ------------------------------------------------------------------------------------------------ Personen
@router.get("/students/{sid}/people")
def student_people(sid: str, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Eltern, Klassenleitung und Fachlehrkräfte (wer unterrichtet in welchem Fach) einer Schülerin/eines Schülers."""
    snap = snapshot()
    school = snap[1]
    st = _student_or_404(snap, sid)
    if getattr(user, "role", "") in ("schueler", "eltern", "schulbegleitung") or not has(user, "students.read") \
            or not can_see_student(user, sid, snap):
        raise HTTPException(403, "Keine Berechtigung")
    teachers = school.index("teachers")
    subjects = school.index("subjects")
    cls = school.index("classes").get(st.class_id)

    def tname(tid: Optional[str]) -> str:
        return teachers[tid].name if tid and tid in teachers else (tid or "")

    leader = cls.class_teacher if cls else None
    # Kontaktdaten der Eltern: Verwaltung und Klassenleitung; Fachlehrkräfte sehen nur die Namen
    contact = getattr(user, "role", "") in ("admin", "schulleitung", "sekretariat", "zuschauer") or \
        _is_class_teacher(user, sid, snap)
    parents = []
    for u in db.scalars(select(User).join(ParentLink, ParentLink.parent_user_id == User.id)
                        .where(ParentLink.student_id == sid, User.active.is_(True)).order_by(User.display_name)):
        parents.append({"id": u.id, "name": u.display_name or u.username, "email": (u.email or "") if contact else ""})
    by_subject: dict[str, dict[str, Any]] = {}
    courses = school.index("courses")
    for cid, idxs in student_parts(sid, snap).items():
        c = courses.get(cid)
        if c is None:
            continue
        for i in idxs:
            if i >= len(c.parts):
                continue
            part = c.parts[i]
            row = by_subject.setdefault(part.subject, {
                "subject": part.subject, "subject_name": subjects[part.subject].name if part.subject in subjects
                else part.subject, "teachers": []})
            if part.teacher and not any(t["id"] == part.teacher for t in row["teachers"]):
                row["teachers"].append({"id": part.teacher, "name": tname(part.teacher), "course": c.label or c.id})
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id},
            "class_teacher": {"id": leader, "name": tname(leader)} if leader else None, "parents": parents,
            "subject_teachers": sorted(by_subject.values(), key=lambda x: x["subject_name"]),
            "can_see_support": _mode(db, user, sid, snap) is not None}


def _file_access(db: Session, user, meta) -> bool:
    try:
        row = db.get(StudentSupport, int(meta.ref_id or 0))
    except (TypeError, ValueError):
        return False
    if row is None or meta.id not in (row.file_ids or []):
        return False
    return _mode(db, user, row.student_id, snapshot()) == "full"


files.register_access_check(REF_TYPE, _file_access)
