"""Notenbuch – Datenzugriff und Berechnung auf Datenbankebene (B-52, ``docs/NOTENBUCH.md``).

Die reine Rechnung steht in :mod:`schulmanager.gradebook`; die Routen (``routes/features_gradebook.py``) rufen nur
diese Funktionen. Alles mit Personenbezug (Noten, Bemerkungen, Protokolleinzelheiten) liegt verschlüsselt in der
Datenbank (``crypto.encrypt_text`` nach ``flush``). Schreibende Funktionen committen nicht – das macht der Aufrufer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import gradebook as gb
from . import crypto
from .db import iso, utcnow
from .feature_models.gradebook import (GradeBook, GradeCategory, GradeEntry, GradeFinal, GradeItem, GradeLog,
                                       GradebookConfig)

TERM_RE_LEN = 6
MAX_CATEGORIES = 40
MAX_ITEMS = 120

DEFAULT_TEMPLATE: list[dict[str, Any]] = [
    {"name": "Schriftlich / Klausuren", "weight": 50, "children": []},
    {"name": "Sonstige Mitarbeit", "weight": 50, "children": [
        {"name": "Tests", "weight": 1}, {"name": "Mündlich", "weight": 1},
        {"name": "Hausaufgaben", "weight": 1}, {"name": "Referate", "weight": 1}]},
]

VISIBILITY = {"aus": "Keine Einsicht", "sofort": "Sofort sichtbar", "freigabe": "Nach Freigabe durch die Lehrkraft",
              "endnote": "Nur die Endnote"}

DEFAULT_SETTINGS: dict[str, Any] = {
    "default_scale": "note6",
    "scale_by_grade": {},          # {"11": "punkte15"}
    "scale_by_course": {},         # {"<kurs>": "punkte15"}
    "keys_default": {},            # {"note6": "tendenz6"} – Schulstandard je Skala
    "visibility": "sofort",
    "show_averages": True,
    "rounding": "ganz",
    "decimals": 2,
    "custom_scales": [],
    "custom_keys": [],
    "risk": dict(gb.DEFAULT_RISK),
    "halfyear_split": "02-01",
    "templates": {},               # {"<fach>" | "*": [{name, weight, children:[…]}]}
}


# ------------------------------------------------------------------------------------------ Einstellungen
def load_settings(db: Session) -> dict[str, Any]:
    row = db.get(GradebookConfig, "settings")
    out = json.loads(json.dumps(DEFAULT_SETTINGS))
    if row is not None and isinstance(row.value, dict):
        for k, v in row.value.items():
            if k in out:
                out[k] = v
    out["risk"] = gb.risk_config(out.get("risk"))
    return out


def save_settings(db: Session, settings: dict[str, Any]) -> None:
    row = db.get(GradebookConfig, "settings")
    if row is None:
        row = GradebookConfig(key="settings")
        db.add(row)
    row.value = {k: settings[k] for k in DEFAULT_SETTINGS if k in settings}
    row.updated_at = utcnow()


def scales_of(settings: dict[str, Any]) -> dict[str, gb.Scale]:
    return gb.scale_table(settings.get("custom_scales"))


def keys_of(settings: dict[str, Any]) -> dict[str, gb.Key]:
    return gb.key_table(settings.get("custom_keys"))


# ------------------------------------------------------------------------------------------------ Halbjahre
def term_of(school, day: Optional[date] = None, settings: Optional[dict] = None) -> str:
    """Halbjahr (``"2026-1"``) zum Datum: Schuljahr nach Planungsdokument, Wechsel zum 2. Halbjahr am Stichtag
    ``halfyear_split`` (Standard 1. Februar)."""
    from schulmanager.calendar_utils import year_bounds
    day = day or date.today()
    try:
        _, _, start = year_bounds(school.settings, day)
    except Exception:  # noqa: BLE001
        start = date(day.year if day.month >= 6 else day.year - 1, 8, 1)
    year = start.year if start.month >= 6 else start.year - 1
    split = (settings or DEFAULT_SETTINGS).get("halfyear_split", "02-01")
    try:
        month, dom = (int(x) for x in str(split).split("-"))
        boundary = date(year + 1, month, dom)
    except (ValueError, TypeError):
        boundary = date(year + 1, 2, 1)
    return f"{year}-{1 if day < boundary else 2}"


def valid_term(term: str) -> bool:
    return len(term) == TERM_RE_LEN and term[:4].isdigit() and term[4] == "-" and term[5] in "12"


def term_label(term: str) -> str:
    if not valid_term(term):
        return term
    y = int(term[:4])
    return f"{y}/{str(y + 1)[2:]}, {term[5]}. Halbjahr"


def neighbour_terms(term: str) -> list[str]:
    y, h = int(term[:4]), int(term[5])
    prev = f"{y}-1" if h == 2 else f"{y - 1}-2"
    nxt = f"{y}-2" if h == 1 else f"{y + 1}-1"
    return [prev, term, nxt]


def term_options(school, settings: dict, today: Optional[date] = None) -> list[dict[str, str]]:
    cur = term_of(school, today, settings)
    y, h = int(cur[:4]), int(cur[5])
    out = []
    for _ in range(4):                              # zwei Schuljahre zurück
        out.append(f"{y}-{h}")
        y, h = (y, 1) if h == 2 else (y - 1, 2)
    out.reverse()
    nxt = neighbour_terms(cur)[2]
    out.append(nxt)
    return [{"id": t, "label": term_label(t)} for t in out]


# --------------------------------------------------------------------------------------- Kurse und Schüler
def course_grade(school, course) -> Optional[int]:
    classes = school.index("classes")
    grades = [classes[c].grade for c in course.classes if c in classes]
    return max(grades) if grades else None


def default_scale_for(settings: dict, school, course) -> str:
    by_course = settings.get("scale_by_course") or {}
    if course.id in by_course and by_course[course.id] in scales_of(settings):
        return by_course[course.id]
    g = course_grade(school, course)
    by_grade = settings.get("scale_by_grade") or {}
    if g is not None and str(g) in by_grade and by_grade[str(g)] in scales_of(settings):
        return by_grade[str(g)]
    sid = settings.get("default_scale") or gb.DEFAULT_SCALE
    return sid if sid in scales_of(settings) else gb.DEFAULT_SCALE


def roster(school, course_id: str, part: int) -> list[str]:
    """Schüler-IDs des Kursteils."""
    from schulmanager import channels as logic
    return list(logic.channel_student_ids(school, logic.COURSE, logic.course_ref(course_id, part)))


def sorted_roster(school, course_id: str, part: int) -> list[str]:
    students = school.index("students")
    return sorted(roster(school, course_id, part),
                  key=lambda s: ((students[s].class_id, students[s].name.lower()) if s in students else ("~", s)))


def part_info(school, course_id: str, part: int) -> dict[str, Any]:
    course = school.index("courses").get(course_id)
    if course is None or not 0 <= part < len(course.parts):
        return {"subject": "", "subject_name": "Kurs entfernt", "teacher": None, "teacher_name": "", "classes": [],
                "label": course_id, "core": False}
    p = course.parts[part]
    subjects, teachers = school.index("subjects"), school.index("teachers")
    sub = subjects.get(p.subject)
    label = (p.label or course.label or "").strip()
    return {"subject": p.subject, "subject_name": sub.name if sub else p.subject,
            "core": bool(sub and sub.core), "teacher": p.teacher,
            "teacher_name": teachers[p.teacher].name if p.teacher in teachers else "",
            "classes": list(course.classes), "label": label}


def book_title(school, book: GradeBook) -> str:
    info = part_info(school, book.course_id, book.part)
    classes = ", ".join(info["classes"])
    extra = f" ({info['label']})" if info["label"] and info["label"] != info["subject_name"] else ""
    return f"{info['subject_name']}{extra} · {classes}".strip(" ·")


# ------------------------------------------------------------------------------------------------- Rechte
def book_access(user, school, book: GradeBook) -> Optional[str]:
    """``"edit"`` (Fachlehrkraft des Kursteils, Schulleitung), ``"read"`` (Klassenleitung) oder ``None``."""
    from .routes.features_common import has, perm_scope
    if has(user, "gradebook.manage"):
        return "edit"
    course = school.index("courses").get(book.course_id)
    tid = getattr(user, "teacher_id", None)
    if has(user, "gradebook.use"):
        if perm_scope(user, "gradebook.use") is None:
            return "edit"
        if course is not None and tid and 0 <= book.part < len(course.parts) and course.parts[book.part].teacher == tid:
            return "edit"
    if has(user, "gradebook.read_class") and course is not None:
        return "read" if class_visible(user, school, course.classes) else None
    return None


def class_visible(user, school, class_ids) -> bool:
    """Darf die Person (lesend) die Noten mindestens einer dieser Klassen sehen (Klassenleitung, Schulleitung)?"""
    from .routes.features_common import has, perm_scope
    if has(user, "gradebook.manage"):
        return True
    if not has(user, "gradebook.read_class"):
        return False
    scope = perm_scope(user, "gradebook.read_class")
    if scope is None:
        return True
    classes = school.index("classes")
    if scope == "class_teacher":
        tid = getattr(user, "teacher_id", None)
        return bool(tid) and any(c in classes and classes[c].class_teacher == tid for c in class_ids)
    if scope == "own_branch":
        from .permissions import branch_class_ids
        mine = branch_class_ids(school, getattr(user, "branches", None)) | {
            c.id for c in school.classes if c.class_teacher == getattr(user, "teacher_id", None)}
        return bool(mine & set(class_ids))
    return False


def class_ids_visible(user, school) -> list[str]:
    return [c.id for c in school.classes if class_visible(user, school, [c.id])]


# ------------------------------------------------------------------------------------------- Entschlüsseln
def dec(token: str, aad: str) -> str:
    if not token:
        return ""
    try:
        return crypto.decrypt_text(token, aad)
    except Exception:  # noqa: BLE001
        return ""


def set_enc(row: Any, attr: str, field: str, text: str) -> None:
    """Verschlüsselt ``text`` in ``row.<attr>`` (Zeile muss schon eine ID haben)."""
    setattr(row, attr, crypto.encrypt_text(text, row.aad(field)) if text else "")


# ---------------------------------------------------------------------------------------------- Bündel
@dataclass
class Bundle:
    book: GradeBook
    scale: gb.Scale
    keys: dict[str, gb.Key]
    key_defaults: dict[str, str]
    categories: list[GradeCategory] = field(default_factory=list)
    items: list[GradeItem] = field(default_factory=list)
    entries: dict[tuple[int, str], dict[str, Any]] = field(default_factory=dict)
    finals: dict[str, dict[str, Any]] = field(default_factory=dict)
    item_keys: dict[int, Optional[gb.Key]] = field(default_factory=dict)

    @property
    def decimals(self) -> int:
        return int(self.book.decimals if self.book.decimals in (0, 1, 2, 3) else 2)


def load_bundle(db: Session, book: GradeBook, settings: dict[str, Any]) -> Bundle:
    scales, keys = scales_of(settings), keys_of(settings)
    scale = scales.get(book.scale_id) or gb.BUILTIN_SCALES[gb.DEFAULT_SCALE]
    b = Bundle(book=book, scale=scale, keys=keys, key_defaults=dict(settings.get("keys_default") or {}))
    b.categories = list(db.scalars(select(GradeCategory).where(GradeCategory.book_id == book.id)
                                   .order_by(GradeCategory.position, GradeCategory.id)))
    b.items = list(db.scalars(select(GradeItem).where(GradeItem.book_id == book.id)
                              .order_by(GradeItem.position, GradeItem.date, GradeItem.id)))
    ids = [i.id for i in b.items]
    if ids:
        for e in db.scalars(select(GradeEntry).where(GradeEntry.item_id.in_(ids))):
            b.entries[(e.item_id, e.student_id)] = {
                "id": e.id, "value": dec(e.value_enc, e.aad("value")), "note": dec(e.note_enc, e.aad("note")),
                "status": e.status or "", "makeup_date": e.makeup_date or "", "from_source": bool(e.from_source),
                "by": e.entered_by_name, "at": iso(e.entered_at)}
    for f in db.scalars(select(GradeFinal).where(GradeFinal.book_id == book.id)):
        b.finals[f.student_id] = {"value": dec(f.value_enc, f.aad("value")), "note": dec(f.note_enc, f.aad("note")),
                                  "by": f.set_by_name, "at": iso(f.set_at)}
    for it in b.items:
        b.item_keys[it.id] = gb.key_for(scale, it.key_id or book.key_id, keys, b.key_defaults)
    return b


def _fl(value: Optional[Decimal], places: int) -> Optional[float]:
    return None if value is None else float(gb.quantize(value, places))


def item_max(item: GradeItem) -> Optional[Decimal]:
    return gb.dec(item.max_points) if item.max_points else None


def is_entry_invalid(b: Bundle, item: GradeItem, entry: dict[str, Any]) -> bool:
    value = (entry.get("value") or "").strip()
    if not value or entry.get("status") in gb.NOT_COUNTED or entry.get("status") == "unentschuldigt":
        return False
    if item_max(item) is not None:
        v = gb.dec(value)
        return v is None or v < 0
    return not gb.is_valid(b.scale, value)


def cat_nodes(b: Bundle) -> list[gb.CatNode]:
    return [gb.CatNode(c.id, c.parent_id, gb.dec(c.weight) or gb.ZERO) for c in b.categories]


def item_nodes(b: Bundle, only: Optional[set[int]] = None) -> list[gb.ItemNode]:
    return [gb.ItemNode(i.id, i.category_id, gb.dec(i.weight) or gb.ZERO) for i in b.items
            if only is None or i.id in only]


def number_of(b: Bundle, item: GradeItem, entry: Optional[dict[str, Any]]) -> Optional[Decimal]:
    if entry is None:
        return None
    return gb.entry_number(b.scale, b.item_keys.get(item.id), item_max(item), entry["status"], entry["value"])


def entry_out(b: Bundle, item: GradeItem, entry: Optional[dict[str, Any]], *, include_meta: bool = True
              ) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    out = {"value": entry["value"], "label": gb.entry_label(b.scale, b.item_keys.get(item.id), item_max(item),
                                                              entry["status"], entry["value"]),
           "status": entry["status"], "note": entry["note"], "makeup_date": entry["makeup_date"],
           "invalid": is_entry_invalid(b, item, entry)}
    if include_meta:
        out["from_source"] = entry["from_source"]
    return out


def student_result(b: Bundle, sid: str, *, only_items: Optional[set[int]] = None) -> dict[str, Any]:
    """Schnitte und Vorschlag einer Person (``only_items``: nur diese Leistungen zählen, z. B. freigegebene)."""
    numbers: dict[int, Optional[Decimal]] = {}
    for it in b.items:
        if only_items is not None and it.id not in only_items:
            continue
        numbers[it.id] = number_of(b, it, b.entries.get((it.id, sid)))
    res = gb.compute_student(cat_nodes(b), item_nodes(b, only_items), numbers)
    avg, proposal = gb.suggest(b.scale, res.overall, b.book.rounding, b.decimals)
    return {"categories": {cid: _fl(v, b.decimals) for cid, v in res.categories.items()},
            "average": _fl(avg, b.decimals), "proposal": proposal, "counted": res.counted}


def student_row(b: Bundle, sid: str, name: str, class_id: Optional[str]) -> dict[str, Any]:
    entries = {}
    for it in b.items:
        e = entry_out(b, it, b.entries.get((it.id, sid)))
        if e is not None:
            entries[str(it.id)] = e
    r = student_result(b, sid)
    fin = b.finals.get(sid)
    final = fin["value"] if fin else ""
    return {"student_id": sid, "name": name, "class_id": class_id, "entries": entries,
            "categories": {str(k): v for k, v in r["categories"].items()}, "average": r["average"],
            "proposal": r["proposal"], "counted": r["counted"], "final": final,
            "final_note": fin["note"] if fin else "", "final_by": fin["by"] if fin else "",
            "final_at": fin["at"] if fin else None,
            "overridden": gb.is_overridden(r["proposal"], final)}


def category_out(b: Bundle) -> list[dict[str, Any]]:
    """Kategorien in Baumreihenfolge (Elternknoten vor ihren Kindern) mit Tiefe."""
    by_id = {c.id: c for c in b.categories}
    kids: dict[Optional[int], list[GradeCategory]] = {}
    for c in b.categories:
        kids.setdefault(c.parent_id if c.parent_id in by_id else None, []).append(c)
    out: list[dict[str, Any]] = []

    def walk(pid: Optional[int], depth: int) -> None:
        for c in sorted(kids.get(pid, []), key=lambda x: (x.position, x.id)):
            if depth >= gb.MAX_DEPTH:
                continue
            out.append({"id": c.id, "parent_id": pid, "name": c.name, "weight": c.weight, "position": c.position,
                        "depth": depth})
            walk(c.id, depth + 1)

    walk(None, 0)
    return out


def item_out(i: GradeItem, source_labels: dict[str, str]) -> dict[str, Any]:
    return {"id": i.id, "category_id": i.category_id, "title": i.title, "date": i.date, "weight": i.weight,
            "max_points": i.max_points, "key_id": i.key_id, "position": i.position, "released": bool(i.released),
            "makeup_date": i.makeup_date, "source_type": i.source_type, "source_id": i.source_id,
            "source_label": source_labels.get(i.source_type, i.source_type) if i.source_type else ""}


def book_out(school, book: GradeBook, b: Optional[Bundle], access: Optional[str], settings: dict, user=None
             ) -> dict[str, Any]:
    from .routes.features_common import has
    info = part_info(school, book.course_id, book.part)
    scale = b.scale if b else scales_of(settings).get(book.scale_id)
    key = None
    if b is not None:
        key = gb.key_for(b.scale, book.key_id, b.keys, b.key_defaults)
    return {"id": book.id, "course_id": book.course_id, "part": book.part, "term": book.term,
            "term_label": term_label(book.term), "title": book_title(school, book), "subject": info["subject"],
            "subject_name": info["subject_name"], "classes": info["classes"], "teacher_name": info["teacher_name"],
            "scale": scale.as_dict() if scale else None, "scale_id": book.scale_id, "key_id": book.key_id,
            "key": key.as_dict() if key else None, "rounding": book.rounding, "decimals": book.decimals,
            "locked": book.locked_at is not None, "locked_at": iso(book.locked_at),
            "locked_by": book.locked_by_name, "can_edit": access == "edit" and book.locked_at is None,
            "can_unlock": bool(user is not None and has(user, "gradebook.manage") and book.locked_at is not None),
            "can_lock": bool(access == "edit" and book.locked_at is None), "access": access}


def ensure_open(book: GradeBook) -> None:
    if book.locked_at is not None:
        raise HTTPException(409, "Das Notenbuch ist gesperrt. Die Schulleitung kann es wieder öffnen.")


# ----------------------------------------------------------------------------------- Protokoll (Änderungen)
def log(db: Session, user, book_id: int, action: str, *, item_id: Optional[int] = None, student_id: str = "",
        detail: Optional[dict[str, Any]] = None) -> None:
    row = GradeLog(book_id=book_id, at=utcnow(), actor_id=getattr(user, "id", None) or None,
                   actor_name=(getattr(user, "display_name", "") or getattr(user, "username", "") or "System")[:200],
                   action=action, item_id=item_id, student_id=student_id, detail_enc="")
    db.add(row)
    db.flush()
    if detail:
        row.detail_enc = crypto.encrypt_text(json.dumps(detail, ensure_ascii=False), row.aad("detail"))


def log_out(db: Session, book_id: int, limit: int = 200) -> list[dict[str, Any]]:
    rows = db.scalars(select(GradeLog).where(GradeLog.book_id == book_id).order_by(GradeLog.id.desc()).limit(limit))
    out = []
    for r in rows:
        try:
            detail = json.loads(dec(r.detail_enc, r.aad("detail")) or "{}")
        except ValueError:
            detail = {}
        out.append({"id": r.id, "at": iso(r.at), "actor": r.actor_name, "action": r.action, "item_id": r.item_id,
                    "student_id": r.student_id, "detail": detail})
    return out


# ------------------------------------------------------------------------------------- Eingaben prüfen
def canonical_value(scale: gb.Scale, max_points: Optional[Decimal], raw: str) -> str:
    """Normalisierte Schreibweise einer Eingabe; ``ValueError`` mit verständlichem Text, wenn sie nicht passt."""
    text = (raw or "").strip()
    if not text:
        return ""
    if max_points is not None and max_points > 0:
        v = gb.dec(text)
        if v is None or v < 0 or v > 100000:
            raise ValueError(f"„{text}“ ist keine gültige Punktzahl")
        return format(v.normalize(), "f")
    if scale.kind == "verbal":
        return text[:500]
    v = gb.parse_value(scale, text)
    if v is None:
        raise ValueError(f"„{text}“ passt nicht zur Skala „{scale.name}“")
    if scale.kind == "note6":
        return gb._norm_label(text) if gb._norm_label(text) != "1+" else "1+"
    if scale.kind in ("punkte15", "prozent"):
        return format(v.normalize(), "f")
    if scale.kind == "bestanden":
        return "bestanden" if v == gb.ONE else "nicht bestanden"
    for label, val in scale.labels:
        if gb._norm_label(label) == gb._norm_label(text):
            return label
    return text


# ----------------------------------------------------------------------------------- Vorlagen, Anlegen
def template_for(settings: dict, subject_id: str) -> list[dict[str, Any]]:
    t = settings.get("templates") or {}
    return t.get(subject_id) or t.get("*") or DEFAULT_TEMPLATE


def create_categories(db: Session, book_id: int, nodes: list[dict[str, Any]], parent: Optional[int] = None,
                      depth: int = 0) -> int:
    n = 0
    for pos, node in enumerate(nodes):
        name = str(node.get("name", "")).strip()[:120]
        if not name or depth >= gb.MAX_DEPTH:
            continue
        weight = float(node.get("weight", 1) or 0)
        row = GradeCategory(book_id=book_id, parent_id=parent, name=name, weight=max(0.0, weight), position=pos)
        db.add(row)
        db.flush()
        n += 1
        n += create_categories(db, book_id, node.get("children") or [], row.id, depth + 1)
    return n


def copy_structure(db: Session, src: GradeBook, dst: GradeBook) -> None:
    """Kategorien (mit Gewichten) eines anderen Notenbuchs übernehmen – ohne Leistungen und Noten."""
    old = list(db.scalars(select(GradeCategory).where(GradeCategory.book_id == src.id)
                          .order_by(GradeCategory.position, GradeCategory.id)))
    mapping: dict[int, int] = {}
    pending = list(old)
    for _ in range(gb.MAX_DEPTH + 1):
        rest = []
        for c in pending:
            if c.parent_id is None or c.parent_id in mapping:
                row = GradeCategory(book_id=dst.id, parent_id=mapping.get(c.parent_id), name=c.name, weight=c.weight,
                                    position=c.position)
                db.add(row)
                db.flush()
                mapping[c.id] = row.id
            else:
                rest.append(c)
        pending = rest
        if not pending:
            break


def tree_template(db: Session, book_id: int) -> list[dict[str, Any]]:
    cats = list(db.scalars(select(GradeCategory).where(GradeCategory.book_id == book_id)
                           .order_by(GradeCategory.position, GradeCategory.id)))
    kids: dict[Optional[int], list[GradeCategory]] = {}
    for c in cats:
        kids.setdefault(c.parent_id, []).append(c)

    def build(pid: Optional[int]) -> list[dict[str, Any]]:
        return [{"name": c.name, "weight": c.weight, "children": build(c.id)} for c in kids.get(pid, [])]
    return build(None)


def delete_book_data(db: Session, book: GradeBook) -> None:
    ids = list(db.scalars(select(GradeItem.id).where(GradeItem.book_id == book.id)))
    if ids:
        db.execute(delete(GradeEntry).where(GradeEntry.item_id.in_(ids)))
    db.execute(delete(GradeItem).where(GradeItem.book_id == book.id))
    db.execute(delete(GradeCategory).where(GradeCategory.book_id == book.id))
    db.execute(delete(GradeFinal).where(GradeFinal.book_id == book.id))
    db.delete(book)


def now_iso_date() -> str:
    return datetime.now().date().isoformat()
