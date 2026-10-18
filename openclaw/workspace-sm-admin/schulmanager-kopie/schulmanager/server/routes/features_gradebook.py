"""Notenbuch (B-52, ``docs/NOTENBUCH.md``).

* ``GET /gradebook/meta`` – Skalen, Notenschlüssel, Halbjahre, Einstellungen, eigene Rechte, sichtbare Klassen
* ``PUT /gradebook/settings`` – Schuleinstellungen (``gradebook.manage``)
* ``GET /gradebook/courses`` · ``GET|POST /gradebook/books`` · ``GET|PATCH|DELETE /gradebook/books/{id}`` –
  Notenbücher je Kursteil und Halbjahr; ``GET`` liefert die ganze Notentabelle samt Schnitten und Vorschlägen
* Kategorien ``/gradebook/books/{id}/categories``, ``/gradebook/categories/{id}``; Leistungen
  ``/gradebook/books/{id}/items``, ``/gradebook/items/{id}``; Eintragen ``PUT /gradebook/items/{id}/entries``
* Halbjahresnoten ``PUT /gradebook/books/{id}/finals``, ``POST …/finals/apply-proposals``; Sperren ``POST …/lock``,
  Öffnen ``POST …/unlock`` (Schulleitung); Protokoll ``GET …/log``
* Übernahme ``GET|POST /gradebook/books/{id}/sources[/adopt|dismiss|restore|sync]``
* Sichten: ``GET /gradebook/my`` (Schüler/in, Eltern), ``GET /gradebook/class/{id}`` (+ ``/conference.pdf``),
  ``GET /gradebook/export`` (CSV für SchILD/ASV/LUSD)

Rechte: Fachlehrkraft für eigene Kursteile (``gradebook.use``), Klassenleitung lesend (``gradebook.read_class``),
Schulleitung alles (``gradebook.manage``), Export (``gradebook.export``). Fremde Notenbücher → 404. Jede Änderung
steht im Audit-Protokoll und – mit alten und neuen Werten, verschlüsselt – im Notenbuch-Protokoll.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from schulmanager import gradebook as gb
from schulmanager.integrations import grades_export
from schulmanager.server import gradebook_reports as rep
from schulmanager.server import gradebook_sources as src
from schulmanager.server import gradebook_store as st
from schulmanager.server.db import get_db, utcnow
from schulmanager.server.deps import AuthUser, current_user
from schulmanager.server.feature_models.gradebook import (GradeBook, GradeCategory, GradeEntry, GradeFinal,
                                                          GradeItem, GradeSourceLink)

from .features_common import has, own_student_ids, publish_change, snapshot, write_audit

router = APIRouter(tags=["Notenbuch"])
SCOPE = ["gradebook"]


# ----------------------------------------------------------------------------------------------- Hilfen
def _any_right(user) -> bool:
    return any(has(user, p) for p in ("gradebook.use", "gradebook.read_class", "gradebook.manage", "gradebook.export"))


def _need_staff(user) -> None:
    if getattr(user, "role", "") == "admin" or not _any_right(user):
        raise HTTPException(403, "Keine Berechtigung")


def _iso_date(value: Optional[str], what: str = "Datum") -> str:
    v = (value or "").strip()
    if not v:
        return ""
    try:
        date.fromisoformat(v)
    except ValueError:
        raise HTTPException(422, f"{what} ist ungültig") from None
    return v[:10]


def _book(db: Session, user, book_id: int, *, edit: bool = False) -> tuple[GradeBook, Any, str]:
    _need_staff(user)
    book = db.get(GradeBook, book_id)
    school = snapshot()[1]
    access = st.book_access(user, school, book) if book else None
    if book is None or access is None:
        raise HTTPException(404, "Notenbuch nicht gefunden")
    if edit and access != "edit":
        raise HTTPException(403, "Dieses Notenbuch dürfen Sie nur lesen")
    return book, school, access


def _open_book(db: Session, user, book_id: int) -> tuple[GradeBook, Any]:
    book, school, _ = _book(db, user, book_id, edit=True)
    st.ensure_open(book)
    return book, school


def _item(db: Session, user, item_id: int, *, open_: bool = True) -> tuple[GradeItem, GradeBook, Any]:
    item = db.get(GradeItem, item_id)
    if item is None:
        raise HTTPException(404, "Leistung nicht gefunden")
    book, school, _ = _book(db, user, item.book_id, edit=True)
    if open_:
        st.ensure_open(book)
    return item, book, school


def _audit(db: Session, user, action: str, book_id: int, details: Optional[dict] = None) -> None:
    write_audit(db, user, f"gradebook.{action}", f"book:{book_id}", details or {})


def _nta_flags(db: Session, user, sids: list[str]) -> set[str]:
    """Schüler/innen mit Nachteilsausgleich (nur Hinweis, keine Einzelheiten) – nur mit ``support.*``."""
    if getattr(user, "role", "") == "admin" or not (has(user, "support.hints") or has(user, "support.read")):
        return set()
    from schulmanager.server.feature_models.support import StudentSupport, SupportCatalog
    if not sids:
        return set()
    cats = {c.id: c for c in db.scalars(select(SupportCatalog))}
    today = date.today().isoformat()
    out: set[str] = set()
    for r in db.scalars(select(StudentSupport).where(StudentSupport.student_id.in_(sids))):
        cat = cats.get(r.catalog_id or 0)
        kind = cat.kind if cat is not None else r.kind
        visible = cat.teacher_visible if cat is not None else r.kind == "nachteilsausgleich"
        valid = not ((r.valid_from and r.valid_from > today) or (r.valid_to and r.valid_to < today))
        if kind == "nachteilsausgleich" and visible and valid:
            out.add(r.student_id)
    return out


def _table(db: Session, user, book: GradeBook, school, access: str, settings: dict, only: Optional[set[str]] = None
           ) -> dict[str, Any]:
    b = st.load_bundle(db, book, settings)
    students = school.index("students")
    sids = st.sorted_roster(school, book.course_id, book.part)
    flags = _nta_flags(db, user, sids)
    rows = []
    for sid in sids:
        if only is not None and sid not in only:
            continue
        s = students.get(sid)
        row = st.student_row(b, sid, s.name if s else sid, s.class_id if s else None)
        row["support"] = sid in flags
        rows.append(row)
    labels = src.source_labels()
    cands = _candidates(db, school, book) if access == "edit" and book.locked_at is None and only is None else []
    return {"book": st.book_out(school, book, b, access, settings, user), "categories": st.category_out(b),
            "items": [st.item_out(i, labels) for i in b.items], "students": rows,
            "pending_sources": sum(1 for c in cands if c["state"] == "open"),
            "visibility": settings.get("visibility", "sofort")}


def _candidates(db: Session, school, book: GradeBook) -> list[dict[str, Any]]:
    labels = src.source_labels()
    links = {(lk.source_type, lk.source_id): lk for lk in db.scalars(select(GradeSourceLink).where(
        GradeSourceLink.book_id == book.id))}
    members = set(st.roster(school, book.course_id, book.part))
    out = []
    for bundle in src.fetch_bundles(db, school, book.course_id, book.part):
        link = links.get((bundle.source_type, bundle.source_id))
        count = sum(1 for sid in bundle.results if sid in members)
        if not count:
            continue
        out.append({"source_type": bundle.source_type, "source_label": labels.get(bundle.source_type,
                                                                                   bundle.source_type),
                    "source_id": bundle.source_id, "title": bundle.title, "date": bundle.date,
                    "max_points": bundle.max_points, "count": count,
                    "kind": "punkte" if bundle.max_points else "note",
                    "state": link.state if link else "open", "item_id": link.item_id if link else None})
    out.sort(key=lambda c: (c["date"] or "", c["title"]), reverse=True)
    return out


# ------------------------------------------------------------------------------------------------- Meta
@router.get("/gradebook/meta")
def meta(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_staff(user)
    school = snapshot()[1]
    settings = st.load_settings(db)
    manage = has(user, "gradebook.manage")
    export = has(user, "gradebook.export") or manage
    visible = [{"id": c.id, "name": c.name, "grade": c.grade} for c in school.classes
               if export or st.class_visible(user, school, [c.id])]
    out_settings = {k: v for k, v in settings.items() if manage or k in ("visibility", "show_averages", "rounding",
                                                                            "decimals", "risk")}
    return {
        "scales": [s.as_dict() for s in st.scales_of(settings).values()],
        "keys": [k.as_dict() for k in st.keys_of(settings).values()],
        "term": st.term_of(school, None, settings), "terms": st.term_options(school, settings),
        "settings": out_settings, "visibility_options": [{"id": k, "label": v} for k, v in st.VISIBILITY.items()],
        "statuses": [{"id": k, "label": v} for k, v in gb.STATUS_LABELS.items() if k],
        "can": {"use": has(user, "gradebook.use"), "read_class": has(user, "gradebook.read_class"),
                "manage": manage, "export": has(user, "gradebook.export") or manage},
        "classes": visible, "default_template": st.DEFAULT_TEMPLATE,
        "export_formats": [{"id": k, "label": v} for k, v in grades_export.FORMAT_LABELS.items()],
        "grades": sorted({c.grade for c in school.classes}),
        "subjects": [{"id": s.id, "name": s.name, "core": bool(s.core)} for s in school.subjects] if manage else [],
    }


class LabelIn(BaseModel):
    label: str = Field(min_length=1, max_length=30)
    value: float


class ScaleIn(BaseModel):
    id: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=60)
    higher_better: bool = False
    labels: list[LabelIn] = Field(min_length=2, max_length=30)


class StepIn(BaseModel):
    min_percent: float = Field(ge=0, le=100)
    label: str = Field(min_length=1, max_length=30)


class KeyIn(BaseModel):
    id: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=60)
    scale_id: str = Field(min_length=1, max_length=40)
    steps: list[StepIn] = Field(min_length=2, max_length=40)


class RiskIn(BaseModel):
    enabled: bool = True
    min_grade: int = Field(5, ge=2, le=6)
    max_points: int = Field(4, ge=0, le=14)
    core_count: int = Field(1, ge=0, le=10)
    any_count: int = Field(2, ge=0, le=20)


class TemplateNode(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    weight: float = Field(1, ge=0, le=1000)
    children: list["TemplateNode"] = Field(default_factory=list, max_length=20)


class SettingsIn(BaseModel):
    model_config = {"extra": "forbid"}
    default_scale: Optional[str] = Field(None, max_length=40)
    scale_by_grade: Optional[dict[str, str]] = None
    scale_by_course: Optional[dict[str, str]] = None
    keys_default: Optional[dict[str, str]] = None
    visibility: Optional[Literal["aus", "sofort", "freigabe", "endnote"]] = None
    show_averages: Optional[bool] = None
    rounding: Optional[Literal["ganz", "tendenz"]] = None
    decimals: Optional[int] = Field(None, ge=0, le=3)
    custom_scales: Optional[list[ScaleIn]] = Field(None, max_length=20)
    custom_keys: Optional[list[KeyIn]] = Field(None, max_length=20)
    risk: Optional[RiskIn] = None
    halfyear_split: Optional[str] = Field(None, pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
    templates: Optional[dict[str, list[TemplateNode]]] = None


@router.put("/gradebook/settings")
def put_settings(body: SettingsIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if getattr(user, "role", "") == "admin" or not has(user, "gradebook.manage"):
        raise HTTPException(403, "Keine Berechtigung")
    settings = st.load_settings(db)
    patch = body.model_dump(exclude_none=True)
    for key, val in patch.items():
        settings[key] = val
    errors = _settings_errors(settings)
    if errors:
        raise HTTPException(422, errors[0])
    st.save_settings(db, settings)
    write_audit(db, user, "gradebook.settings", "gradebook", {"fields": sorted(patch)})
    db.commit()
    publish_change(SCOPE)
    return meta(user, db)


def _settings_errors(s: dict[str, Any]) -> list[str]:
    scales = st.scales_of(s)
    keys = st.keys_of(s)
    errs = []
    ids = [c["id"] for c in s.get("custom_scales", [])]
    if len(set(ids)) != len(ids) or any(i in gb.BUILTIN_SCALES for i in ids):
        errs.append("Skalen-Kennungen müssen eindeutig sein und dürfen nicht eingebaute Skalen überschreiben")
    kids = [c["id"] for c in s.get("custom_keys", [])]
    if len(set(kids)) != len(kids) or any(i in gb.BUILTIN_KEYS for i in kids):
        errs.append("Notenschlüssel-Kennungen müssen eindeutig sein und dürfen nicht eingebaute überschreiben")
    for k in s.get("custom_keys", []):
        sc = scales.get(k["scale_id"])
        if sc is None or not sc.numeric:
            errs.append(f"Notenschlüssel „{k['name']}“: Skala unbekannt oder ohne Zahlenwerte")
        else:
            labels = {gb._norm_label(label) for label, _ in sc.labels}
            if sc.kind != "prozent" and any(gb._norm_label(x["label"]) not in labels for x in k["steps"]):
                errs.append(f"Notenschlüssel „{k['name']}“: Noten passen nicht zur Skala")
            if not any(float(x["min_percent"]) == 0 for x in k["steps"]):
                errs.append(f"Notenschlüssel „{k['name']}“: Die unterste Stufe muss bei 0 % beginnen")
    for name in ("default_scale",):
        if s.get(name) not in scales:
            errs.append("Die Standardskala ist unbekannt")
    for mapping in ("scale_by_grade", "scale_by_course"):
        for sid in (s.get(mapping) or {}).values():
            if sid not in scales:
                errs.append(f"Unbekannte Skala „{sid}“")
    for sid, kid in (s.get("keys_default") or {}).items():
        if sid not in scales or kid not in keys or keys[kid].scale_id != sid:
            errs.append(f"Notenschlüssel „{kid}“ passt nicht zur Skala „{sid}“")
    return errs


# ------------------------------------------------------------------------------------------ Notenbücher
@router.get("/gradebook/courses")
def list_courses(term: Optional[str] = Query(None, max_length=10), class_id: Optional[str] = Query(None, max_length=40),
                 user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Kursteile, für die die Person ein Notenbuch führen darf, mit vorhandenem Notenbuch des Halbjahres."""
    _need_staff(user)
    school = snapshot()[1]
    settings = st.load_settings(db)
    term = term or st.term_of(school, None, settings)
    if not st.valid_term(term):
        raise HTTPException(422, "Halbjahr ungültig")
    books = {(b.course_id, b.part): b for b in db.scalars(select(GradeBook).where(GradeBook.term == term))}
    out = []
    for c in school.courses:
        if class_id and class_id not in c.classes:
            continue
        for i, _p in enumerate(c.parts):
            probe = GradeBook(course_id=c.id, part=i, term=term)
            access = st.book_access(user, school, probe)
            if access is None:
                continue
            info = st.part_info(school, c.id, i)
            b = books.get((c.id, i))
            out.append({"course_id": c.id, "part": i, "title": st.book_title(school, probe),
                        "subject": info["subject"], "subject_name": info["subject_name"], "classes": info["classes"],
                        "teacher_name": info["teacher_name"], "access": access, "book_id": b.id if b else None,
                        "locked": bool(b and b.locked_at), "scale_id": st.default_scale_for(settings, school, c)})
            if len(out) >= 400:
                break
    out.sort(key=lambda x: (x["book_id"] is None, x["title"].lower()))
    return {"term": term, "term_label": st.term_label(term), "courses": out}


@router.get("/gradebook/books")
def list_books(term: Optional[str] = Query(None, max_length=10), user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    _need_staff(user)
    school = snapshot()[1]
    settings = st.load_settings(db)
    term = term or st.term_of(school, None, settings)
    if not st.valid_term(term):
        raise HTTPException(422, "Halbjahr ungültig")
    out = []
    for book in db.scalars(select(GradeBook).where(GradeBook.term == term).order_by(GradeBook.id)):
        access = st.book_access(user, school, book)
        if access is None:
            continue
        info = st.part_info(school, book.course_id, book.part)
        out.append({**st.book_out(school, book, None, access, settings, user), "students": len(
            st.roster(school, book.course_id, book.part)), "teacher_name": info["teacher_name"]})
    out.sort(key=lambda x: x["title"].lower())
    return {"term": term, "term_label": st.term_label(term), "books": out}


class BookIn(BaseModel):
    course_id: str = Field(min_length=1, max_length=64)
    part: int = Field(0, ge=0, le=20)
    term: str = Field(min_length=6, max_length=6)
    scale_id: Optional[str] = Field(None, max_length=40)
    copy_from: Optional[int] = None


@router.post("/gradebook/books", status_code=201)
def create_book(body: BookIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_staff(user)
    school = snapshot()[1]
    settings = st.load_settings(db)
    if not st.valid_term(body.term):
        raise HTTPException(422, "Halbjahr ungültig")
    course = school.index("courses").get(body.course_id)
    if course is None or body.part >= len(course.parts):
        raise HTTPException(404, "Kurs nicht gefunden")
    probe = GradeBook(course_id=body.course_id, part=body.part, term=body.term)
    if st.book_access(user, school, probe) != "edit":
        raise HTTPException(403, "Ein Notenbuch führen nur die Lehrkraft des Kurses und die Schulleitung")
    exists = db.scalar(select(GradeBook).where(GradeBook.course_id == body.course_id, GradeBook.part == body.part,
                                               GradeBook.term == body.term))
    if exists is not None:
        raise HTTPException(409, "Für diesen Kurs gibt es in diesem Halbjahr schon ein Notenbuch")
    scales = st.scales_of(settings)
    scale_id = body.scale_id or st.default_scale_for(settings, school, course)
    if scale_id not in scales:
        raise HTTPException(422, "Unbekannte Notenskala")
    book = GradeBook(course_id=body.course_id, part=body.part, term=body.term, scale_id=scale_id, key_id="",
                     rounding=settings.get("rounding", "ganz"), decimals=int(settings.get("decimals", 2)),
                     created_by=user.id or None, created_at=utcnow(), locked_by_name="")
    db.add(book)
    db.flush()
    if body.copy_from:
        other = db.get(GradeBook, body.copy_from)
        if other is None or st.book_access(user, school, other) is None:
            raise HTTPException(404, "Das Notenbuch zum Kopieren gibt es nicht")
        st.copy_structure(db, other, book)
        if other.scale_id == scale_id:
            book.key_id, book.rounding, book.decimals = other.key_id, other.rounding, other.decimals
    else:
        subject = st.part_info(school, body.course_id, body.part)["subject"]
        st.create_categories(db, book.id, st.template_for(settings, subject))
    st.log(db, user, book.id, "book", detail={"term": body.term, "scale": scale_id})
    _audit(db, user, "book.create", book.id, {"course": body.course_id, "part": body.part, "term": body.term})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", settings)


@router.get("/gradebook/books/{book_id}")
def get_book(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    book, school, access = _book(db, user, book_id)
    return _table(db, user, book, school, access, st.load_settings(db))


class BookPatch(BaseModel):
    model_config = {"extra": "forbid"}
    scale_id: Optional[str] = Field(None, max_length=40)
    key_id: Optional[str] = Field(None, max_length=40)
    rounding: Optional[Literal["ganz", "tendenz"]] = None
    decimals: Optional[int] = Field(None, ge=0, le=3)


@router.patch("/gradebook/books/{book_id}")
def patch_book(book_id: int, body: BookPatch, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    book, school = _open_book(db, user, book_id)
    settings = st.load_settings(db)
    scales, keys = st.scales_of(settings), st.keys_of(settings)
    patch = body.model_dump(exclude_none=True)
    if "scale_id" in patch and patch["scale_id"] != book.scale_id:
        if patch["scale_id"] not in scales:
            raise HTTPException(422, "Unbekannte Notenskala")
        used = db.scalar(select(GradeEntry.id).join(GradeItem, GradeItem.id == GradeEntry.item_id)
                         .where(GradeItem.book_id == book.id).limit(1))
        has_final = db.scalar(select(GradeFinal.id).where(GradeFinal.book_id == book.id).limit(1))
        if used or has_final:
            raise HTTPException(409, "Die Skala lässt sich nur ändern, solange noch keine Noten eingetragen sind")
        book.scale_id, book.key_id = patch["scale_id"], ""
    if "key_id" in patch:
        kid = patch["key_id"]
        if kid and (kid not in keys or keys[kid].scale_id != book.scale_id):
            raise HTTPException(422, "Der Notenschlüssel passt nicht zur Skala")
        book.key_id = kid
    if "rounding" in patch:
        book.rounding = patch["rounding"]
    if "decimals" in patch:
        book.decimals = patch["decimals"]
    st.log(db, user, book.id, "settings", detail=patch)
    _audit(db, user, "book.update", book.id, {"fields": sorted(patch)})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", settings)


@router.delete("/gradebook/books/{book_id}")
def delete_book(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    book, _ = _open_book(db, user, book_id)
    used = db.scalar(select(GradeEntry.id).join(GradeItem, GradeItem.id == GradeEntry.item_id)
                     .where(GradeItem.book_id == book.id).limit(1))
    has_final = db.scalar(select(GradeFinal.id).where(GradeFinal.book_id == book.id).limit(1))
    if used or has_final:
        raise HTTPException(409, "Ein Notenbuch mit Noten lässt sich nicht löschen")
    _audit(db, user, "book.delete", book.id, {"course": book.course_id, "term": book.term})
    st.delete_book_data(db, book)
    db.commit()
    publish_change(SCOPE)
    return {"ok": True}


# ------------------------------------------------------------------------------------------- Kategorien
class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    weight: float = Field(1, ge=0, le=1000)
    parent_id: Optional[int] = None


class CategoryPatch(BaseModel):
    model_config = {"extra": "forbid"}
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    weight: Optional[float] = Field(None, ge=0, le=1000)
    parent_id: Optional[int] = None
    position: Optional[int] = Field(None, ge=0, le=1000)
    move_to_root: bool = False


def _cat_depth(cats: dict[int, GradeCategory], cid: Optional[int]) -> int:
    d, seen = 0, set()
    while cid is not None and cid in cats and cid not in seen:
        seen.add(cid)
        cid = cats[cid].parent_id
        d += 1
    return d


@router.post("/gradebook/books/{book_id}/categories", status_code=201)
def add_category(book_id: int, body: CategoryIn, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    book, school = _open_book(db, user, book_id)
    cats = {c.id: c for c in db.scalars(select(GradeCategory).where(GradeCategory.book_id == book.id))}
    if len(cats) >= st.MAX_CATEGORIES:
        raise HTTPException(409, "Mehr Leistungsarten sind nicht möglich")
    if body.parent_id is not None and body.parent_id not in cats:
        raise HTTPException(404, "Übergeordnete Leistungsart nicht gefunden")
    if _cat_depth(cats, body.parent_id) >= gb.MAX_DEPTH - 1:
        raise HTTPException(422, f"Höchstens {gb.MAX_DEPTH} Ebenen sind möglich")
    pos = max([c.position for c in cats.values() if c.parent_id == body.parent_id], default=-1) + 1
    row = GradeCategory(book_id=book.id, parent_id=body.parent_id, name=body.name.strip(), weight=body.weight,
                        position=pos)
    db.add(row)
    db.flush()
    st.log(db, user, book.id, "category", detail={"add": row.name, "weight": row.weight})
    _audit(db, user, "category.add", book.id, {"category": row.id})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", st.load_settings(db))


def _category(db: Session, user, cid: int) -> tuple[GradeCategory, GradeBook, Any]:
    cat = db.get(GradeCategory, cid)
    if cat is None:
        raise HTTPException(404, "Leistungsart nicht gefunden")
    book, school, _ = _book(db, user, cat.book_id, edit=True)
    st.ensure_open(book)
    return cat, book, school


@router.patch("/gradebook/categories/{cid}")
def patch_category(cid: int, body: CategoryPatch, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    cat, book, school = _category(db, user, cid)
    cats = {c.id: c for c in db.scalars(select(GradeCategory).where(GradeCategory.book_id == book.id))}
    patch = body.model_dump(exclude_none=True, exclude={"move_to_root"})
    if "name" in patch:
        cat.name = patch["name"].strip()
    if "weight" in patch:
        cat.weight = patch["weight"]
    if "position" in patch:
        cat.position = patch["position"]
    if body.move_to_root:
        cat.parent_id = None
    elif "parent_id" in patch:
        pid = patch["parent_id"]
        if pid not in cats or pid == cat.id:
            raise HTTPException(404, "Übergeordnete Leistungsart nicht gefunden")
        cur, seen = pid, set()
        while cur is not None and cur not in seen:           # kein Zyklus
            if cur == cat.id:
                raise HTTPException(422, "Eine Leistungsart kann nicht in sich selbst liegen")
            seen.add(cur)
            cur = cats[cur].parent_id if cur in cats else None
        if _cat_depth(cats, pid) >= gb.MAX_DEPTH - 1:
            raise HTTPException(422, f"Höchstens {gb.MAX_DEPTH} Ebenen sind möglich")
        cat.parent_id = pid
    st.log(db, user, book.id, "category", detail={"update": cat.id, **{k: v for k, v in patch.items()}})
    _audit(db, user, "category.update", book.id, {"category": cat.id, "fields": sorted(patch)})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", st.load_settings(db))


@router.delete("/gradebook/categories/{cid}")
def delete_category(cid: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    cat, book, school = _category(db, user, cid)
    if db.scalar(select(GradeItem.id).where(GradeItem.category_id == cat.id).limit(1)) or db.scalar(
            select(GradeCategory.id).where(GradeCategory.parent_id == cat.id).limit(1)):
        raise HTTPException(409, "Die Leistungsart ist nicht leer: erst Leistungen verschieben oder entfernen")
    name = cat.name
    db.delete(cat)
    st.log(db, user, book.id, "category", detail={"remove": name})
    _audit(db, user, "category.delete", book.id, {"category": cid})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", st.load_settings(db))


# --------------------------------------------------------------------------------------------- Leistungen
class ItemIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    category_id: Optional[int] = None
    date: str = Field("", max_length=10)
    weight: float = Field(1, ge=0, le=1000)
    max_points: Optional[float] = Field(None, gt=0, le=100000)
    key_id: str = Field("", max_length=40)
    makeup_date: str = Field("", max_length=10)


class ItemPatch(BaseModel):
    model_config = {"extra": "forbid"}
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    category_id: Optional[int] = None
    date: Optional[str] = Field(None, max_length=10)
    weight: Optional[float] = Field(None, ge=0, le=1000)
    max_points: Optional[float] = Field(None, gt=0, le=100000)
    key_id: Optional[str] = Field(None, max_length=40)
    makeup_date: Optional[str] = Field(None, max_length=10)
    released: Optional[bool] = None
    clear_points: bool = False
    clear_category: bool = False


def _check_category(db: Session, book: GradeBook, cid: Optional[int]) -> None:
    if cid is not None and (db.get(GradeCategory, cid) is None or db.get(GradeCategory, cid).book_id != book.id):
        raise HTTPException(404, "Leistungsart nicht gefunden")


def _check_key(settings: dict, book: GradeBook, kid: str) -> None:
    keys = st.keys_of(settings)
    if kid and (kid not in keys or keys[kid].scale_id != book.scale_id):
        raise HTTPException(422, "Der Notenschlüssel passt nicht zur Skala")


@router.post("/gradebook/books/{book_id}/items", status_code=201)
def add_item(book_id: int, body: ItemIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    book, school = _open_book(db, user, book_id)
    settings = st.load_settings(db)
    _check_category(db, book, body.category_id)
    _check_key(settings, book, body.key_id)
    count = len(list(db.scalars(select(GradeItem.id).where(GradeItem.book_id == book.id))))
    if count >= st.MAX_ITEMS:
        raise HTTPException(409, "Mehr Leistungen sind in einem Notenbuch nicht möglich")
    row = GradeItem(book_id=book.id, category_id=body.category_id, title=body.title.strip(),
                    date=_iso_date(body.date), weight=body.weight, max_points=body.max_points, key_id=body.key_id,
                    position=count, released=False, makeup_date=_iso_date(body.makeup_date, "Nachschreibtermin"),
                    source_type="", source_id="", created_at=utcnow())
    db.add(row)
    db.flush()
    st.log(db, user, book.id, "item", item_id=row.id, detail={"add": row.title})
    _audit(db, user, "item.add", book.id, {"item": row.id})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", settings)


@router.patch("/gradebook/items/{item_id}")
def patch_item(item_id: int, body: ItemPatch, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    item, book, school = _item(db, user, item_id, open_=False)
    patch = body.model_dump(exclude_none=True, exclude={"clear_points", "clear_category"})
    if book.locked_at is not None and set(patch) - {"released"}:
        st.ensure_open(book)
    settings = st.load_settings(db)
    if "category_id" in patch:
        _check_category(db, book, patch["category_id"])
        item.category_id = patch["category_id"]
    if body.clear_category:
        item.category_id = None
    if "title" in patch:
        item.title = patch["title"].strip()
    if "date" in patch:
        item.date = _iso_date(patch["date"])
    if "weight" in patch:
        item.weight = patch["weight"]
    if "max_points" in patch:
        item.max_points = patch["max_points"]
    if body.clear_points:
        item.max_points = None
    if "key_id" in patch:
        _check_key(settings, book, patch["key_id"])
        item.key_id = patch["key_id"]
    if "makeup_date" in patch:
        item.makeup_date = _iso_date(patch["makeup_date"], "Nachschreibtermin")
    if "released" in patch:
        item.released = bool(patch["released"])
    st.log(db, user, book.id, "item", item_id=item.id, detail={"update": sorted(patch) + (
        ["max_points"] if body.clear_points else [])})
    _audit(db, user, "item.update", book.id, {"item": item.id, "fields": sorted(patch)})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", settings)


@router.delete("/gradebook/items/{item_id}")
def delete_item(item_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    item, book, school = _item(db, user, item_id)
    removed = len(list(db.scalars(select(GradeEntry.id).where(GradeEntry.item_id == item.id))))
    if item.source_type:
        link = db.scalar(select(GradeSourceLink).where(
            GradeSourceLink.book_id == book.id, GradeSourceLink.source_type == item.source_type,
            GradeSourceLink.source_id == item.source_id))
        if link is not None:
            link.state, link.item_id = "dismissed", None
    db.execute(delete(GradeEntry).where(GradeEntry.item_id == item.id))
    title = item.title
    db.delete(item)
    st.log(db, user, book.id, "item", detail={"remove": title, "entries": removed})
    _audit(db, user, "item.delete", book.id, {"item": item_id, "entries": removed})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", st.load_settings(db))


# ---------------------------------------------------------------------------------------- Eintragungen
class EntryIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=40)
    value: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = Field(None, max_length=500)
    makeup_date: Optional[str] = Field(None, max_length=10)


class EntriesIn(BaseModel):
    entries: list[EntryIn] = Field(max_length=400)


@router.put("/gradebook/items/{item_id}/entries")
def put_entries(item_id: int, body: EntriesIn, user: AuthUser = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    """Noten einer Leistung eintragen. Felder, die fehlen, bleiben unverändert; ``""`` leert. Ohne Wert, Status,
    Bemerkung und Nachschreibtermin wird die Eintragung gelöscht. Antwort: neu berechnete Zeilen der Betroffenen."""
    try:
        return _put_entries(item_id, body, user, db)
    except IntegrityError:        # zwei gleichzeitige Eingaben für dieselbe Zelle: zweiter Versuch sieht die erste
        db.rollback()
        return _put_entries(item_id, body, user, db)


def _put_entries(item_id: int, body: EntriesIn, user: AuthUser, db: Session) -> dict:
    item, book, school = _item(db, user, item_id)
    settings = st.load_settings(db)
    b = st.load_bundle(db, book, settings)
    members = set(st.roster(school, book.course_id, book.part))
    maxp = st.item_max(item)
    existing = {e.student_id: e for e in db.scalars(select(GradeEntry).where(GradeEntry.item_id == item.id))}
    name = (user.display_name or user.username)[:200]
    changed: list[str] = []
    for ent in body.entries:
        if ent.student_id not in members:
            raise HTTPException(422, f"{ent.student_id} gehört nicht zu diesem Kurs")
        row = existing.get(ent.student_id)
        old_value = st.dec(row.value_enc, row.aad("value")) if row else ""
        old_note = st.dec(row.note_enc, row.aad("note")) if row else ""
        old_status = row.status if row else ""
        old_makeup = row.makeup_date if row else ""
        value = old_value if ent.value is None else ent.value
        status = old_status if ent.status is None else ent.status.strip()
        note = old_note if ent.note is None else ent.note.strip()
        makeup = old_makeup if ent.makeup_date is None else _iso_date(ent.makeup_date, "Nachschreibtermin")
        if status not in gb.STATUS_LABELS:
            raise HTTPException(422, "Unbekannter Status")
        try:
            value = st.canonical_value(b.scale, maxp, value)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        if value and status == "nachschreiben":
            status = ""
        if status != "nachschreiben" and ent.makeup_date is None and old_status == "nachschreiben":
            makeup = ""
        if not value and not status and not note and not makeup:
            if row is not None:
                st.log(db, user, book.id, "entry", item_id=item.id, student_id=ent.student_id,
                       detail={"from": old_value, "to": "", "status": old_status, "removed": True})
                db.delete(row)
                changed.append(ent.student_id)
            continue
        if row is not None and (old_value, old_status, old_note, old_makeup) == (value, status, note, makeup):
            continue
        if row is None:
            row = GradeEntry(item_id=item.id, student_id=ent.student_id, value_enc="", note_enc="", status="",
                             makeup_date="", from_source=False)
            db.add(row)
            db.flush()
        row.status, row.makeup_date, row.from_source = status, makeup, False
        row.entered_by, row.entered_by_name, row.entered_at = user.id or None, name, utcnow()
        st.set_enc(row, "value_enc", "value", value)
        st.set_enc(row, "note_enc", "note", note)
        st.log(db, user, book.id, "entry", item_id=item.id, student_id=ent.student_id,
               detail={"from": old_value, "to": value, "status_from": old_status, "status_to": status})
        changed.append(ent.student_id)
    if changed:
        _audit(db, user, "entries", book.id, {"item": item.id, "students": changed[:60], "count": len(changed)})
        db.commit()
        publish_change(SCOPE)
    return {"changed": len(changed), **_table(db, user, book, school, "edit", settings, only=set(changed) or set())}


# ---------------------------------------------------------------------------------------- Endnoten, Sperre
class FinalIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=40)
    value: Optional[str] = Field(None, max_length=500)
    note: Optional[str] = Field(None, max_length=500)


class FinalsIn(BaseModel):
    finals: list[FinalIn] = Field(max_length=400)


def _set_final(db: Session, user, book: GradeBook, scale: gb.Scale, sid: str, value: Optional[str],
               note: Optional[str], existing: dict[str, GradeFinal]) -> bool:
    row = existing.get(sid)
    old_v = st.dec(row.value_enc, row.aad("value")) if row else ""
    old_n = st.dec(row.note_enc, row.aad("note")) if row else ""
    new_v = old_v if value is None else value
    new_n = old_n if note is None else note.strip()
    try:
        new_v = st.canonical_value(scale, None, new_v)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    if not new_v and not new_n:
        if row is None:
            return False
        db.delete(row)
        st.log(db, user, book.id, "final", student_id=sid, detail={"from": old_v, "to": "", "removed": True})
        return True
    if row is not None and (old_v, old_n) == (new_v, new_n):
        return False
    if row is None:
        row = GradeFinal(book_id=book.id, student_id=sid, value_enc="", note_enc="")
        db.add(row)
        db.flush()
        existing[sid] = row
    row.set_by, row.set_by_name, row.set_at = user.id or None, (user.display_name or user.username)[:200], utcnow()
    st.set_enc(row, "value_enc", "value", new_v)
    st.set_enc(row, "note_enc", "note", new_n)
    st.log(db, user, book.id, "final", student_id=sid, detail={"from": old_v, "to": new_v})
    return True


@router.put("/gradebook/books/{book_id}/finals")
def put_finals(book_id: int, body: FinalsIn, user: AuthUser = Depends(current_user),
               db: Session = Depends(get_db)) -> dict:
    """Halbjahres-/Zeugnisnoten festlegen (leer = zurücknehmen)."""
    try:
        return _put_finals(book_id, body, user, db)
    except IntegrityError:
        db.rollback()
        return _put_finals(book_id, body, user, db)


def _put_finals(book_id: int, body: FinalsIn, user: AuthUser, db: Session) -> dict:
    book, school = _open_book(db, user, book_id)
    settings = st.load_settings(db)
    scale = st.scales_of(settings).get(book.scale_id) or gb.BUILTIN_SCALES["note6"]
    members = set(st.roster(school, book.course_id, book.part))
    existing = {f.student_id: f for f in db.scalars(select(GradeFinal).where(GradeFinal.book_id == book.id))}
    changed = []
    for f in body.finals:
        if f.student_id not in members:
            raise HTTPException(422, f"{f.student_id} gehört nicht zu diesem Kurs")
        if _set_final(db, user, book, scale, f.student_id, f.value, f.note, existing):
            changed.append(f.student_id)
    if changed:
        _audit(db, user, "finals", book.id, {"students": changed[:60], "count": len(changed)})
        db.commit()
        publish_change(SCOPE)
    return {"changed": len(changed), **_table(db, user, book, school, "edit", settings, only=set(changed) or set())}


class ApplyIn(BaseModel):
    student_ids: Optional[list[str]] = Field(None, max_length=400)
    overwrite: bool = False


@router.post("/gradebook/books/{book_id}/finals/apply-proposals")
def apply_proposals(book_id: int, body: ApplyIn, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    """Vorschlagsnoten als festgelegte Noten übernehmen (ohne ``overwrite`` nur, wo noch nichts festgelegt ist)."""
    book, school = _open_book(db, user, book_id)
    settings = st.load_settings(db)
    b = st.load_bundle(db, book, settings)
    members = st.roster(school, book.course_id, book.part)
    existing = {f.student_id: f for f in db.scalars(select(GradeFinal).where(GradeFinal.book_id == book.id))}
    changed = []
    for sid in members:
        if body.student_ids is not None and sid not in body.student_ids:
            continue
        r = st.student_result(b, sid)
        if not r["proposal"]:
            continue
        if sid in existing and not body.overwrite and b.finals.get(sid, {}).get("value"):
            continue
        if _set_final(db, user, book, b.scale, sid, r["proposal"], None, existing):
            changed.append(sid)
    if changed:
        _audit(db, user, "finals", book.id, {"students": changed[:60], "count": len(changed), "proposals": True})
        db.commit()
        publish_change(SCOPE)
    return {"changed": len(changed), **_table(db, user, book, school, "edit", settings)}


@router.post("/gradebook/books/{book_id}/lock")
def lock_book(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Halbjahresnoten sperren: danach ändert sich nichts mehr, bis die Schulleitung das Notenbuch wieder öffnet."""
    book, school = _open_book(db, user, book_id)
    book.locked_at, book.locked_by = utcnow(), user.id or None
    book.locked_by_name = (user.display_name or user.username)[:200]
    members = st.roster(school, book.course_id, book.part)
    have = set(db.scalars(select(GradeFinal.student_id).where(GradeFinal.book_id == book.id)))
    missing = len([s for s in members if s not in have])
    st.log(db, user, book.id, "lock", detail={"missing_finals": missing})
    _audit(db, user, "lock", book.id, {"missing_finals": missing})
    db.commit()
    _notify_final(db, school, book, members, st.load_settings(db))
    publish_change(SCOPE)
    return {"missing_finals": missing, **_table(db, user, book, school, "edit", st.load_settings(db))}


def _notify_final(db: Session, school, book: GradeBook, members: list[str], settings: dict) -> None:
    """Benachrichtigung „Halbjahresnoten liegen vor“ an Schüler/innen (Art ``gradebook``, ohne Notenwerte)."""
    if settings.get("visibility") == "aus":
        return
    try:
        from schulmanager.server.db_models import User
        from schulmanager.server.notifications import notify
        uids = list(db.scalars(select(User.id).where(User.student_id.in_(members), User.role == "schueler",
                                                     User.active.is_(True))))
        subject = st.part_info(school, book.course_id, book.part)["subject_name"]
        notify(uids, "gradebook", f"Halbjahresnote {subject} liegt vor", "/noten", ref=f"gb:{book.id}",
               dedupe=f"gb-lock:{book.id}:{book.locked_at}")
    except Exception:  # noqa: BLE001 - eine Benachrichtigung darf das Sperren nie verhindern
        pass


@router.post("/gradebook/books/{book_id}/unlock")
def unlock_book(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    _need_staff(user)
    if not has(user, "gradebook.manage"):
        raise HTTPException(403, "Nur die Schulleitung öffnet ein gesperrtes Notenbuch")
    book, school, _ = _book(db, user, book_id, edit=True)
    if book.locked_at is None:
        raise HTTPException(409, "Das Notenbuch ist nicht gesperrt")
    book.locked_at, book.locked_by, book.locked_by_name = None, None, ""
    st.log(db, user, book.id, "unlock")
    _audit(db, user, "unlock", book.id)
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", st.load_settings(db))


@router.get("/gradebook/books/{book_id}/log")
def book_log(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    book, school, _ = _book(db, user, book_id)
    students = school.index("students")
    items = {i.id: i.title for i in db.scalars(select(GradeItem).where(GradeItem.book_id == book.id))}
    out = st.log_out(db, book.id)
    for row in out:
        s = students.get(row["student_id"])
        row["student"] = s.name if s else row["student_id"]
        row["item"] = items.get(row["item_id"], "")
    return {"log": out}


# ---------------------------------------------------------------------------------------- Übernahme
@router.get("/gradebook/books/{book_id}/sources")
def list_sources(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    book, school, _ = _book(db, user, book_id)
    return {"sources": _candidates(db, school, book)}


class SourceRef(BaseModel):
    source_type: str = Field(min_length=1, max_length=30)
    source_id: str = Field(min_length=1, max_length=80)
    category_id: Optional[int] = None
    weight: float = Field(1, ge=0, le=1000)


def _link(db: Session, book: GradeBook, ref: SourceRef) -> Optional[GradeSourceLink]:
    return db.scalar(select(GradeSourceLink).where(
        GradeSourceLink.book_id == book.id, GradeSourceLink.source_type == ref.source_type,
        GradeSourceLink.source_id == ref.source_id))


@router.post("/gradebook/books/{book_id}/sources/adopt")
def adopt_source(book_id: int, body: SourceRef, user: AuthUser = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    book, school = _open_book(db, user, book_id)
    settings = st.load_settings(db)
    bundle = src.find_bundle(db, school, book.course_id, book.part, body.source_type, body.source_id)
    if bundle is None:
        raise HTTPException(404, "Diese Quelle hat für den Kurs keine Ergebnisse")
    link = _link(db, book, body)
    if link is not None and link.state == "adopted" and link.item_id and db.get(GradeItem, link.item_id):
        raise HTTPException(409, "Die Leistung ist schon übernommen")
    _check_category(db, book, body.category_id)
    count = len(list(db.scalars(select(GradeItem.id).where(GradeItem.book_id == book.id))))
    if count >= st.MAX_ITEMS:
        raise HTTPException(409, "Mehr Leistungen sind in einem Notenbuch nicht möglich")
    item = GradeItem(book_id=book.id, category_id=body.category_id, title=(bundle.title or "Leistung")[:120],
                     date=(bundle.date or "")[:10], weight=body.weight, max_points=bundle.max_points or None,
                     key_id="", position=count, released=False, makeup_date="", source_type=body.source_type,
                     source_id=body.source_id, created_at=utcnow())
    db.add(item)
    db.flush()
    if link is None:
        link = GradeSourceLink(book_id=book.id, source_type=body.source_type, source_id=body.source_id)
        db.add(link)
    link.state, link.item_id = "adopted", item.id
    n = src.apply_bundle(db, user, book, item, bundle, st.roster(school, book.course_id, book.part))
    st.log(db, user, book.id, "source", item_id=item.id, detail={"adopt": body.source_type, "entries": n})
    _audit(db, user, "source.adopt", book.id, {"source": f"{body.source_type}:{body.source_id}", "entries": n})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", settings)


@router.post("/gradebook/books/{book_id}/sources/dismiss")
def dismiss_source(book_id: int, body: SourceRef, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    """Quelle abwählen: eine schon übernommene Leistung samt Eintragungen wird aus dem Notenbuch entfernt."""
    book, school = _open_book(db, user, book_id)
    link = _link(db, book, body)
    removed = 0
    if link is None:
        link = GradeSourceLink(book_id=book.id, source_type=body.source_type, source_id=body.source_id)
        db.add(link)
    if link.item_id:
        item = db.get(GradeItem, link.item_id)
        if item is not None and item.book_id == book.id:
            removed = len(list(db.scalars(select(GradeEntry.id).where(GradeEntry.item_id == item.id))))
            db.execute(delete(GradeEntry).where(GradeEntry.item_id == item.id))
            db.delete(item)
    link.state, link.item_id = "dismissed", None
    st.log(db, user, book.id, "source", detail={"dismiss": body.source_type, "entries": removed})
    _audit(db, user, "source.dismiss", book.id, {"source": f"{body.source_type}:{body.source_id}", "entries": removed})
    db.commit()
    publish_change(SCOPE)
    return _table(db, user, book, school, "edit", st.load_settings(db))


@router.post("/gradebook/books/{book_id}/sources/restore")
def restore_source(book_id: int, body: SourceRef, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)) -> dict:
    book, school = _open_book(db, user, book_id)
    link = _link(db, book, body)
    if link is not None and link.state == "dismissed":
        db.delete(link)
        _audit(db, user, "source.restore", book.id, {"source": f"{body.source_type}:{body.source_id}"})
        db.commit()
        publish_change(SCOPE)
    return {"sources": _candidates(db, school, book)}


@router.post("/gradebook/books/{book_id}/sources/sync")
def sync_sources(book_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Übernommene Leistungen auffrischen (neue Ergebnisse der Quelle; von Hand geänderte Noten bleiben)."""
    book, school = _open_book(db, user, book_id)
    total = 0
    for link in db.scalars(select(GradeSourceLink).where(GradeSourceLink.book_id == book.id,
                                                         GradeSourceLink.state == "adopted")):
        item = db.get(GradeItem, link.item_id) if link.item_id else None
        bundle = src.find_bundle(db, school, book.course_id, book.part, link.source_type, link.source_id)
        if item is not None and bundle is not None:
            total += src.apply_bundle(db, user, book, item, bundle, st.roster(school, book.course_id, book.part))
    if total:
        _audit(db, user, "source.sync", book.id, {"entries": total})
        db.commit()
        publish_change(SCOPE)
    return {"changed": total, **_table(db, user, book, school, "edit", st.load_settings(db))}


# --------------------------------------------------------------------------------------------- Sichten
@router.get("/gradebook/my")
def my_grades(student_id: Optional[str] = Query(None, max_length=40), term: Optional[str] = Query(None, max_length=10),
              user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Noten für Schüler/in bzw. Eltern: je Fach Einzelnoten, Schnitte und Endnote – nach der Einsichtsregel der Schule
    (``visibility``). Eltern volljähriger Kinder brauchen deren Freigabe (Elternzugriff, Bereich „noten“)."""
    from schulmanager.server import parent_access as pa
    snap = snapshot()
    school = snap[1]
    role = getattr(user, "role", "")
    if role not in ("schueler", "eltern"):
        raise HTTPException(403, "Keine Berechtigung")
    own = own_student_ids(user)
    if not student_id:
        if len(own) != 1:
            raise HTTPException(422, "Bitte die Schülerin/den Schüler angeben")
        student_id = own[0]
    if student_id not in own or school.index("students").get(student_id) is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    if role == "eltern" and not pa.parent_may_see(db, student_id, pa.AREA_GRADES, school=school):
        raise HTTPException(403, "Die Noten sind für die Eltern nicht freigegeben")
    settings = st.load_settings(db)
    term = term or st.term_of(school, None, settings)
    if not st.valid_term(term):
        raise HTTPException(422, "Halbjahr ungültig")
    data = rep.my_view(db, school, student_id, term, settings)
    data["terms"] = st.term_options(school, settings)
    return data


@router.get("/gradebook/class/{class_id}")
def class_overview(class_id: str, term: Optional[str] = Query(None, max_length=10),
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Klasse × Fächer mit Halbjahres- bzw. Vorschlagsnoten und Warnung bei gefährdeter Versetzung."""
    _need_staff(user)
    school = snapshot()[1]
    if school.index("classes").get(class_id) is None or not st.class_visible(user, school, [class_id]):
        raise HTTPException(404, "Klasse nicht gefunden")
    settings = st.load_settings(db)
    term = term or st.term_of(school, None, settings)
    if not st.valid_term(term):
        raise HTTPException(422, "Halbjahr ungültig")
    return rep.class_overview(db, school, class_id, term, settings)


@router.get("/gradebook/class/{class_id}/conference.pdf")
def conference_pdf(class_id: str, term: Optional[str] = Query(None, max_length=10),
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Notenkonferenz-Liste der Klasse als PDF."""
    from schulmanager.server.files import content_disposition
    data = class_overview(class_id, term, user, db)
    school = snapshot()[1]
    pdf = rep.conference_pdf(school, data, st.load_settings(db))
    write_audit(db, user, "gradebook.conference", f"class:{class_id}", {"term": data["term"]})
    db.commit()
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": content_disposition(
                        f"Notenkonferenz-{class_id}-{data['term']}.pdf"), "Cache-Control": "no-store"})


@router.get("/gradebook/export")
def export_grades(term: Optional[str] = Query(None, max_length=10), format: str = Query("schild", max_length=10),
                  class_id: Optional[str] = Query(None, max_length=40), include_open: bool = False,
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Festgelegte Halbjahresnoten gesperrter Notenbücher als CSV (``format``: schild, asv, lusd)."""
    from schulmanager.server.files import content_disposition
    if getattr(user, "role", "") == "admin" or not (has(user, "gradebook.export") or has(user, "gradebook.manage")):
        raise HTTPException(403, "Keine Berechtigung")
    if format not in grades_export.FORMATS:
        raise HTTPException(422, "Unbekanntes Format")
    school = snapshot()[1]
    settings = st.load_settings(db)
    term = term or st.term_of(school, None, settings)
    if not st.valid_term(term):
        raise HTTPException(422, "Halbjahr ungültig")
    if include_open and not has(user, "gradebook.manage"):
        raise HTTPException(403, "Noch nicht gesperrte Notenbücher exportiert nur die Schulleitung")
    rows = rep.export_rows(db, school, term, settings, class_id=class_id, include_open=include_open)
    text = grades_export.export_grades(rows, format)
    write_audit(db, user, "gradebook.export", f"term:{term}", {"format": format, "rows": len(rows),
                                                                "class": class_id or ""})
    db.commit()
    return Response(text.encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": content_disposition(f"Noten-{format}-{term}.csv"),
                             "Cache-Control": "no-store", "X-Row-Count": str(len(rows))})

