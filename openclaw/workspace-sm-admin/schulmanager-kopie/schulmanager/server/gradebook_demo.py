"""Demo-Daten für das Notenbuch: erfundene, aber realistische Noten für einige Demoklassen.

Je Demoklasse (5a, 9P bzw. 9a, Q1-1 bzw. Q2-1 und 7a) und Kursteil mit Lehrkraft entstehen zwei Notenbücher:

* **Vorheriges Halbjahr** – fertig: Endnoten festgelegt (einzelne vom Vorschlag abweichend), gesperrt. Damit zeigen
  die Klassenübersicht, die Versetzungswarnung, die Notenkonferenz-Liste und der Export Inhalte.
* **Laufendes Halbjahr** – in Arbeit: Klausur nach Punkten mit Notenschlüssel, Tests, mündliche Note, ein
  entschuldigtes Fehlen mit Nachschreibtermin; die meisten Leistungen sind für Schüler/innen freigegeben.

Die Noten entstehen deterministisch aus der Schüler-ID (gleiche Demo → gleiche Noten); einzelne Schüler/innen haben
bewusst schwächere Leistungen (Defizite). Aufruf: :func:`seed_demo` (von ``demo_loader.load_demo``).
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select

from .. import gradebook as gb
from . import gradebook_store as st
from .db import session_scope, utcnow
from .feature_models.gradebook import GradeBook, GradeEntry, GradeFinal, GradeItem

DEMO_CLASS_PREFERENCES = (["5a"], ["7a"], ["9P", "9a"], ["Q1-1", "Q2-1"])
REMARKS = ("Gut vorbereitet.", "Bitte die Aufgabenstellung genauer lesen.", "Deutlich verbessert.",
           "Sehr sorgfältig gearbeitet.", "Rechenweg fehlt teilweise.")


def _classes(school) -> list[str]:
    have = {c.id for c in school.classes}
    out = []
    for prefs in DEMO_CLASS_PREFERENCES:
        pick = next((p for p in prefs if p in have), None)
        if pick:
            out.append(pick)
    return out


def _label(scale: gb.Scale, value: float) -> str:
    """Zahl auf der 1–6-Skala (bzw. Punkteskala) → Eintrag."""
    value = min(6.0, max(1.0, value))
    if scale.kind == "punkte15":
        return str(min(15, max(0, round(17 - 3 * value))))
    return gb.label_for(scale, gb.D(str(round(value, 2))), "tendenz")


def _points(value: float, max_points: int) -> str:
    pct = max(6.0, min(100.0, 108 - 19 * value))
    return format(round(max_points * pct / 100 * 2) / 2, "g")


def seed_demo(school) -> dict[str, Any]:
    """Legt Demo-Notenbücher an, wenn es noch keine gibt. Gibt Zähler zurück (für das Protokoll)."""
    stats = {"books": 0, "entries": 0, "locked": 0}
    with session_scope() as db:
        if db.scalar(select(GradeBook.id).limit(1)) is not None:
            return {**stats, "skipped": True}
        settings = st.load_settings(db)
        if not settings.get("scale_by_grade"):
            settings["scale_by_grade"] = {"11": "punkte15", "12": "punkte15", "13": "punkte15"}
            st.save_settings(db, settings)
        cur = st.term_of(school, None, settings)
        prev = st.neighbour_terms(cur)[0]
        classes = set(_classes(school))
        subjects = school.index("subjects")
        by_student = {s.id: s for s in school.students}
        for course in school.courses:
            if not (set(course.classes) & classes):
                continue
            for part, p in enumerate(course.parts):
                if not p.teacher:
                    continue
                members = [m for m in st.sorted_roster(school, course.id, part) if m in by_student]
                if not members:
                    continue
                scale_id = st.default_scale_for(settings, school, course)
                for term in (prev, cur):
                    _seed_book(db, school, settings, course, part, term, scale_id, members, locked=term == prev,
                               subject_seed=p.subject if p.subject in subjects else course.id, stats=stats)
    return stats


def _seed_book(db, school, settings, course, part, term, scale_id, members, *, locked, subject_seed, stats) -> None:
    rng = random.Random(f"{course.id}|{part}|{term}")
    scale = st.scales_of(settings)[scale_id]
    book = GradeBook(course_id=course.id, part=part, term=term, scale_id=scale_id, key_id="",
                     rounding="tendenz" if scale.kind == "note6" and rng.random() < 0.35 else "ganz",
                     decimals=2, created_at=utcnow(), locked_by_name="")
    db.add(book)
    db.flush()
    subject = st.part_info(school, course.id, part)["subject"]
    st.create_categories(db, book.id, st.template_for(settings, subject))
    cats = {c.name: c.id for c in st.load_bundle(db, book, settings).categories}
    year = int(term[:4])
    start = date(year, 8, 20) if term.endswith("1") else date(year + 1, 2, 5)
    plan = [("Klausur 1", cats.get("Schriftlich / Klausuren"), 2.0, 50, 0), ("Klausur 2", cats.get(
        "Schriftlich / Klausuren"), 2.0, None, 1), ("Test 1", cats.get("Tests"), 1.0, None, 2),
        ("Mündliche Mitarbeit", cats.get("Mündlich"), 1.0, None, 3), ("Hausaufgaben", cats.get("Hausaufgaben"), 1.0,
                                                                      None, 4)]
    if scale.kind == "punkte15":
        plan = plan[:4]
    items: list[GradeItem] = []
    for pos, (title, cat, weight, maxp, offset) in enumerate(plan):
        d = start + timedelta(days=21 + offset * 18)
        it = GradeItem(book_id=book.id, category_id=cat, title=title, date=d.isoformat(), weight=weight,
                       max_points=float(maxp) if maxp and scale.kind == "note6" else None, key_id="", position=pos,
                       released=locked or pos < len(plan) - 1, makeup_date="", source_type="", source_id="",
                       created_at=utcnow())
        db.add(it)
        items.append(it)
    db.flush()
    cur_open = not locked
    makeup_for = rng.choice(members) if cur_open and len(members) > 3 else None
    entries: list[GradeEntry] = []
    for sid in members:
        srng = random.Random(f"{sid}|{subject_seed}")
        weak = random.Random(sid).random() < 0.06
        base = random.Random(sid).gauss(2.7, 0.8) + srng.gauss(0, 0.45) + (2.0 if weak else 0)
        for i, it in enumerate(items):
            if cur_open and it is items[-1] and rng.random() < 0.55:
                continue                                    # noch nicht alles bewertet
            value = base + rng.gauss(0, 0.55)
            e = GradeEntry(item_id=it.id, student_id=sid, value_enc="", note_enc="", status="", makeup_date="",
                           from_source=False, entered_by=None, entered_by_name="Demo", entered_at=utcnow())
            if it.max_points:
                e._value = _points(value, int(it.max_points))        # type: ignore[attr-defined]
            else:
                e._value = _label(scale, value)                      # type: ignore[attr-defined]
            e._note = rng.choice(REMARKS) if rng.random() < 0.08 else ""   # type: ignore[attr-defined]
            if makeup_for == sid and i == 1:
                e._value, e.status = "", "nachschreiben"             # type: ignore[attr-defined]
                e.makeup_date = (date.today() + timedelta(days=12)).isoformat()
            db.add(e)
            entries.append(e)
    db.flush()
    for e in entries:
        st.set_enc(e, "value_enc", "value", e._value)               # type: ignore[attr-defined]
        st.set_enc(e, "note_enc", "note", e._note)                  # type: ignore[attr-defined]
    stats["books"] += 1
    stats["entries"] += len(entries)
    if not locked:
        return
    db.flush()
    b = st.load_bundle(db, book, settings)
    for sid in members:
        proposal = st.student_result(b, sid)["proposal"]
        if not proposal:
            continue
        final = proposal
        if scale.kind == "note6" and rng.random() < 0.12:           # Lehrkraft weicht begründet ab
            v = gb.parse_value(scale, proposal) or gb.D(3)
            final = gb.label_for(scale, max(gb.D(1), v - gb.D("0.6")), "ganz")
        f = GradeFinal(book_id=book.id, student_id=sid, value_enc="", note_enc="", set_by=None,
                       set_by_name="Demo", set_at=utcnow())
        db.add(f)
        db.flush()
        st.set_enc(f, "value_enc", "value", final)
    book.locked_at, book.locked_by_name = utcnow(), "Demo"
    stats["locked"] += 1
