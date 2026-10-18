"""Notenbuch: Sichten und Auswertungen (Klassenübersicht, Notenkonferenz-PDF, Export, Schüler-/Elternsicht).

Alles liest nur; die Rechtsprüfung macht die Route (``routes/features_gradebook.py``).
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import gradebook as gb
from ..branding import PRODUCT_NAME
from . import gradebook_store as gs
from .feature_models.gradebook import GradeBook


def books_for_class(db: Session, school, class_id: str, term: str) -> list[GradeBook]:
    course_ids = {c.id for c in school.courses if class_id in c.classes}
    if not course_ids:
        return []
    return [b for b in db.scalars(select(GradeBook).where(GradeBook.term == term, GradeBook.course_id.in_(course_ids))
                                  .order_by(GradeBook.id))]


def class_overview(db: Session, school, class_id: str, term: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Klasse × Fächer: je Zelle Endnote (festgelegt) oder Vorschlag (vorläufig)."""
    students = [s for s in school.students if s.class_id == class_id]
    students.sort(key=lambda s: s.name.lower())
    sids = {s.id for s in students}
    subjects_idx = school.index("subjects")
    cfg = gb.risk_config(settings.get("risk"))
    columns: dict[str, dict[str, Any]] = {}
    for c in school.courses:
        if class_id not in c.classes:
            continue
        for i, p in enumerate(c.parts):
            sub = subjects_idx.get(p.subject)
            columns.setdefault(p.subject, {"id": p.subject, "name": sub.name if sub else p.subject,
                                           "core": bool(sub and sub.core)})
    books = books_for_class(db, school, class_id, term)
    cells: dict[str, dict[str, dict[str, Any]]] = {s.id: {} for s in students}
    book_states: dict[int, dict[str, Any]] = {}
    for book in books:
        b = gs.load_bundle(db, book, settings)
        info = gs.part_info(school, book.course_id, book.part)
        sub_id = info["subject"]
        if sub_id not in columns:
            columns[sub_id] = {"id": sub_id, "name": info["subject_name"], "core": info["core"]}
        member = set(gs.roster(school, book.course_id, book.part)) & sids
        for sid in member:
            if sub_id in cells[sid]:
                continue
            r = gs.student_result(b, sid)
            fin = b.finals.get(sid, {}).get("value", "")
            value = fin or r["proposal"]
            if not value:
                continue
            core = columns[sub_id]["core"]
            deficit = gb.is_deficit(b.scale, value, cfg)
            cells[sid][sub_id] = {"value": value, "final": bool(fin), "locked": book.locked_at is not None,
                                  "overridden": gb.is_overridden(r["proposal"], fin), "deficit": deficit,
                                  "core": core, "average": r["average"], "book_id": book.id,
                                  "scale": b.scale.kind}
        book_states[book.id] = {"book_id": book.id, "subject": sub_id, "locked": book.locked_at is not None,
                                "title": gs.book_title(school, book)}
    rows = []
    for s in students:
        defs = [(columns[sub]["core"], True) for sub, cell in cells[s.id].items() if cell["deficit"]]
        reasons = gb.risk_for(defs, cfg)
        rows.append({"student_id": s.id, "name": s.name, "cells": cells[s.id], "warnings": reasons,
                     "deficits": len(defs)})
    cols = sorted(columns.values(), key=lambda c: (not c["core"], c["name"].lower()))
    return {"class_id": class_id, "term": term, "term_label": gs.term_label(term), "subjects": cols, "students": rows,
            "books": list(book_states.values()), "risk": cfg,
            "locked_all": bool(books) and all(x["locked"] for x in book_states.values()),
            "warning_count": sum(1 for r in rows if r["warnings"])}


def conference_pdf(school, data: dict[str, Any], settings: dict[str, Any]) -> bytes:
    """Notenkonferenz-Liste einer Klasse: Schüler/innen × Fächer, Defizite markiert, Warnungen am Ende."""
    from .pdf_simple import A4, MARGIN, Page, render

    title = f"Notenkonferenz {data['class_id']} – {data['term_label']}"
    subjects = data["subjects"]
    width = A4[0] - 2 * MARGIN
    name_w = 120.0
    col_w = min(34.0, (width - name_w - 70) / max(1, len(subjects))) if subjects else 34.0
    pages: list[Page] = []
    page: Optional[Page] = None
    row_h = 15.0

    def header(p: Page) -> None:
        p.text(MARGIN, p.y, school.settings.school_name or PRODUCT_NAME, 11, bold=True)
        p.y -= 16
        p.text(MARGIN, p.y, title, 10, bold=True)
        p.y -= 6
        p.text(A4[0] - MARGIN - 70, p.y + 6, "Vertraulich", 8, gray=0.4)
        p.y -= 14
        p.text(MARGIN, p.y, "Name", 7.5, bold=True)
        x = MARGIN + name_w
        for s in subjects:
            p.text(x, p.y, (s["id"] or s["name"])[:5], 7.5, bold=True)
            x += col_w
        p.text(x, p.y, "Hinweis", 7.5, bold=True)
        p.y -= 4
        p.line(MARGIN, p.y, A4[0] - MARGIN, p.y, 0.6)
        p.y -= row_h - 4

    for row in data["students"]:
        if page is None or page.y < MARGIN + 40:
            page = Page()
            pages.append(page)
            header(page)
        page.text(MARGIN, page.y, row["name"][:26], 8)
        x = MARGIN + name_w
        for s in subjects:
            cell = row["cells"].get(s["id"])
            if cell:
                txt = cell["value"] + ("" if cell["final"] else "*")
                page.text(x, page.y, txt, 8, bold=cell["deficit"], gray=0.0 if cell["final"] else 0.35)
                if cell["deficit"]:
                    page.box(x - 2, page.y - 3, col_w - 6, 11, 0.5)
            x += col_w
        if row["warnings"]:
            page.text(x, page.y, "Versetzung gefährdet", 7.5, bold=True)
        page.y -= row_h
    if page is None:
        page = Page()
        pages.append(page)
        header(page)
        page.text(MARGIN, page.y, "Keine Schüler/innen in dieser Klasse.", 9)
    foot = ("* = Vorschlag, noch nicht festgelegt. Umrahmt = Defizit. "
            f"Warnung: {data['warning_count']} Schüler/innen.")
    page.y -= 6
    page.text(MARGIN, page.y, foot, 7.5, gray=0.35)
    return render(pages, title)


def export_rows(db: Session, school, term: str, settings: dict[str, Any], *, class_id: Optional[str] = None,
                include_open: bool = False) -> list[dict[str, Any]]:
    """Endnoten für die CSV-Ausgabe: nur gesperrte Notenbücher (``include_open``: alle) und nur festgelegte Noten."""
    q = select(GradeBook).where(GradeBook.term == term).order_by(GradeBook.course_id, GradeBook.part)
    students = school.index("students")
    classes = school.index("classes")
    year = f"{term[:4]}/{str(int(term[:4]) + 1)[2:]}"
    out = []
    for book in db.scalars(q):
        if book.locked_at is None and not include_open:
            continue
        info = gs.part_info(school, book.course_id, book.part)
        b = gs.load_bundle(db, book, settings)
        for sid in gs.sorted_roster(school, book.course_id, book.part):
            fin = b.finals.get(sid, {}).get("value", "")
            st = students.get(sid)
            if not fin or st is None or (class_id and st.class_id != class_id):
                continue
            name = st.name.strip()
            first, _, last = name.rpartition(" ")
            if not first:
                first, last = "", name
            out.append({"student_id": sid, "last_name": last, "first_name": first,
                        "birth_date": getattr(st, "birth_date", "") or "", "class_id": st.class_id,
                        "class_name": classes[st.class_id].name if st.class_id in classes else st.class_id,
                        "year": year, "term_no": int(term[5]), "subject_id": info["subject"],
                        "subject_name": info["subject_name"], "course_id": book.course_id,
                        "teacher": info["teacher_name"], "grade": fin, "remark": ""})
    out.sort(key=lambda r: (r["class_id"], r["last_name"].lower(), r["first_name"].lower(), r["subject_name"]))
    return out


def my_view(db: Session, school, student_id: str, term: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Noten einer Schülerin/eines Schülers für Schüler/in und Eltern – nach Einsichtsregel der Schule."""
    mode = settings.get("visibility", "sofort")
    show_avg = bool(settings.get("show_averages", True))
    out_subjects: list[dict[str, Any]] = []
    st = school.index("students").get(student_id)
    if st is None:
        return {"term": term, "term_label": gs.term_label(term), "visibility": mode, "subjects": []}
    course_ids = {c.id for c in school.courses}
    books = [b for b in db.scalars(select(GradeBook).where(GradeBook.term == term).order_by(GradeBook.id))
             if b.course_id in course_ids and student_id in gs.roster(school, b.course_id, b.part)]
    for book in books:
        b = gs.load_bundle(db, book, settings)
        info = gs.part_info(school, book.course_id, book.part)
        locked = book.locked_at is not None
        fin = b.finals.get(student_id, {})
        final = fin.get("value", "") if (locked and mode != "aus") else ""
        visible_ids: set[int] = set()
        if mode == "sofort":
            visible_ids = {i.id for i in b.items}
        elif mode == "freigabe":
            visible_ids = {i.id for i in b.items if i.released}
        items = []
        for it in b.items:
            if it.id not in visible_ids:
                continue
            e = b.entries.get((it.id, student_id))
            if e is None or not (e["value"] or e["status"]):
                continue
            eo = gs.entry_out(b, it, e, include_meta=False)
            items.append({"item_id": it.id, "title": it.title, "date": it.date, "category_id": it.category_id,
                          "max_points": it.max_points, "makeup_date": e["makeup_date"] or it.makeup_date,
                          "value": eo["value"], "label": eo["label"], "status": eo["status"], "note": eo["note"]})
        res = gs.student_result(b, student_id, only_items={i["item_id"] for i in items}) if items else None
        cats = []
        if show_avg and res is not None:
            names = {c["id"]: c for c in gs.category_out(b)}
            cats = [{"id": cid, "name": names[cid]["name"], "parent_id": names[cid]["parent_id"], "average": avg}
                    for cid, avg in res["categories"].items() if avg is not None and cid in names]
        if not items and not final:
            continue
        out_subjects.append({
            "book_id": book.id, "subject": info["subject"], "subject_name": info["subject_name"],
            "teacher_name": info["teacher_name"], "scale": b.scale.as_dict(), "final": final,
            "final_note": fin.get("note", "") if final else "", "locked": locked,
            "average": res["average"] if (show_avg and res is not None) else None, "categories": cats,
            "items": items})
    out_subjects.sort(key=lambda s: s["subject_name"].lower())
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id}, "term": term,
            "term_label": gs.term_label(term), "visibility": mode, "show_averages": show_avg,
            "subjects": out_subjects}
