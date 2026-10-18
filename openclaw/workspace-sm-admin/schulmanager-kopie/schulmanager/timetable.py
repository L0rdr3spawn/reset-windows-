"""Stundenplan-Ansichten, manuelles Verschieben und Qualitätsbericht.

Arbeitet direkt auf dem Planungsdokument (``School``). Alle Zeiten 0-basiert, Tage 0 = Mo … 6 = So.
Wochen: Ansichten gelten für eine reale Woche (Datum bzw. laufende Woche); Belegung und Bericht rechnen über
die Wochenvarianten des Schuljahres (``weeks.PlanWeeks``); aktiv ist ein Block nach ``weeks.lesson_active_in``.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable, Optional

from . import commute
from . import weeks as wk
from .calendar_utils import class_days, day_info, monday_of, monday_of_week_no, open_days, week_info
from .models import WEEKDAYS, Lesson, School


# --------------------------------------------------------------------- helpers
def weeks_text(lesson: Optional[Lesson], course=None, lab: Optional[wk.WeekLabels] = None) -> str:
    """Wochentext eines Blocks: Wochenangabe der Stunde und/oder des Kurses, sonst „jede Woche“ (``lab``: als KW)."""
    parts = [wk.describe_rule_weeks(x, lab) for x in (lesson, course) if x is not None and wk.spec_of(x) != ([], None)]
    return " und ".join(dict.fromkeys(parts)) if parts else "jede Woche"


def course_days(school: School, course, classes: Optional[dict] = None) -> list[int]:
    """Tage, an denen alle Klassen des Kurses Unterricht haben."""
    classes = classes if classes is not None else school.index("classes")
    days = set(range(7))
    for cid in course.classes:
        days &= set(class_days(school, classes.get(cid)))
    return sorted(days) if course.classes else open_days(school)


def lesson_site(school: School, lesson: Lesson, rooms=None, classes=None, courses=None) -> str:
    rooms = rooms or school.index("rooms")
    for r in lesson.rooms:
        if r and r in rooms and rooms[r].site:
            return rooms[r].site
    courses = courses or school.index("courses")
    classes = classes or school.index("classes")
    c = courses.get(lesson.course_id)
    if c and c.classes and c.classes[0] in classes:
        return classes[c.classes[0]].site
    return ""


def student_parts(school: School, student_id: str) -> dict[str, list[int]]:
    """Welche Kursteile besucht ein Schüler? ``{course_id: [part_index, ...]}``.

    Ein-Teil-Kurse der Klasse → Teil 0. Bei mehreren Teilen zählen die Wahlen in
    ``Student.courses`` (``"kurs#teil"``) bzw. ``CoursePart.students``; ohne Wahl
    alle Teile.
    """
    st = school.index("students").get(student_id)
    if st is None:
        return {}
    chosen: dict[str, set[int]] = defaultdict(set)
    for ref in st.courses:
        if "#" in ref:
            cid, _, idx = ref.rpartition("#")
            if idx.isdigit():
                chosen[cid].add(int(idx))
    out: dict[str, list[int]] = {}
    for c in school.courses:
        if st.class_id not in c.classes:
            continue
        if len(c.parts) <= 1:
            out[c.id] = [0]
            continue
        sel = set(chosen.get(c.id, set()))
        for i, p in enumerate(c.parts):
            if p.students and student_id in p.students:
                sel.add(i)
        out[c.id] = sorted(sel) if sel else list(range(len(c.parts)))
    return out


def lesson_info(school: School, lesson: Lesson, parts: Optional[list[int]] = None, _idx=None) -> dict:
    """Zelle für Ansichten (Format siehe ARCHITECTURE.md §3)."""
    idx = _idx or _Index(school)
    c = idx.courses.get(lesson.course_id)
    if c is None:
        return {"lesson_id": lesson.id, "course_id": lesson.course_id, "day": lesson.day,
                "start": lesson.start, "length": lesson.length, "weeks": lesson.weeks, "rhythm": lesson.rhythm,
                "subject": "?", "subject_name": "Unbekannter Kurs", "color": "#999",
                "teachers": [], "rooms": [], "classes": [], "label": lesson.course_id,
                "locked": lesson.locked, "parts": []}
    sel = parts if parts is not None else list(range(len(c.parts)))
    part_rows = []
    for i in sel:
        if i >= len(c.parts):
            continue
        p = c.parts[i]
        part_rows.append({
            "index": i, "subject": p.subject, "teacher": p.teacher,
            "room": lesson.rooms[i] if i < len(lesson.rooms) else None,
            "label": p.label or p.subject,
        })
    subjects = [r["subject"] for r in part_rows]
    main = subjects[0] if len(set(subjects)) == 1 else (c.label or "Kopplung")
    subj = idx.subjects.get(subjects[0]) if subjects else None
    return {
        "lesson_id": lesson.id, "course_id": c.id, "day": lesson.day, "start": lesson.start,
        "length": lesson.length, "weeks": lesson.weeks, "rhythm": lesson.rhythm,
        "subject": main, "subject_name": subj.name if subj and len(set(subjects)) == 1 else (c.label or main),
        "color": subj.color if subj and subj.color else "#90a4ae",
        "teachers": [r["teacher"] for r in part_rows if r["teacher"]],
        "rooms": [r["room"] for r in part_rows if r["room"]],
        "classes": list(c.classes), "label": c.label or c.id, "locked": lesson.locked,
        "parts": part_rows,
    }


class _Index:
    def __init__(self, school: School):
        self.courses = school.index("courses")
        self.subjects = school.index("subjects")
        self.classes = school.index("classes")
        self.teachers = school.index("teachers")
        self.rooms = school.index("rooms")
        self.students = school.index("students")


# ----------------------------------------------------------------------- views
def _week_monday(school: School, week: int, today: Optional[date] = None) -> date:
    """Montag der laufenden Woche ``week`` (1-basiert; kleiner als 1 = Woche 1) im Schuljahr von ``today``."""
    return monday_of_week_no(school.settings, max(1, int(week or 1)), today)


def visible_days(school: School, cells: Iterable[dict], teaching: Iterable[int] = (), all_days: bool = True,
                 extra: Iterable[int] = ()) -> int:
    """Spaltenzahl ab Montag (V10/E2): 7 bzw. 1 + max({4} ∪ Unterrichtstage ∪ Tage mit Zellen/Klausuren)."""
    if all_days:
        return 7
    used = {4} | set(teaching) | {int(c["day"]) for c in cells} | set(extra)
    return min(7, max(used) + 1)


def timetable_view(school: School, kind: str, ref: str, week: int = 0, *, when: Optional[date] = None,
                   all_days: bool = True, today: Optional[date] = None) -> dict:
    """Wochenraster für Klasse, Lehrer, Raum oder Schüler.

    Die Woche ist ``when`` (ein Datum darin) oder – ohne Datum – die laufende Woche ``week`` (1 … Y) des Schuljahres.
    Die Antwort enthält nur die in dieser Woche aktiven Zellen (jede mit ``weeks_text``), ``week_info``, ``day_info``
    und als ``days`` die Namen der sichtbaren Spalten ab Montag (``all_days``: alle 7)."""
    st = school.settings
    idx = _Index(school)
    labels = wk.WeekLabels(st, today=today)
    title = ref
    blocked: list[dict] = []
    student_sel: dict[str, list[int]] = {}
    ref_class = None
    if kind == "class":
        obj = idx.classes.get(ref)
        if obj is None:
            raise KeyError(f"Klasse {ref} unbekannt")
        title = obj.name
        rules = obj.unavailable
        ref_class = obj
    elif kind == "teacher":
        obj = idx.teachers.get(ref)
        if obj is None:
            raise KeyError(f"Lehrkraft {ref} unbekannt")
        title = obj.name
        rules = obj.unavailable
    elif kind == "room":
        obj = idx.rooms.get(ref)
        if obj is None:
            raise KeyError(f"Raum {ref} unbekannt")
        title = obj.name
        rules = []
    elif kind == "student":
        obj = idx.students.get(ref)
        if obj is None:
            raise KeyError(f"Schüler {ref} unbekannt")
        title = obj.name
        student_sel = student_parts(school, ref)
        ref_class = idx.classes.get(obj.class_id)
        rules = ref_class.unavailable if ref_class else []
    else:
        raise ValueError(f"Unbekannte Ansicht {kind}")
    monday = monday_of(when) if when is not None else _week_monday(school, week, today)
    real = wk.real_week(school, monday)
    teaching = class_days(school, ref_class) if ref_class is not None else open_days(school)
    for d in teaching:
        for p in range(st.periods):
            for r in rules:
                if r.matches(real, d, p):
                    blocked.append({"day": d, "period": p, "note": r.note or "nicht verfügbar"})
                    break

    aidx = wk.ActiveIndex(school)
    cells = []
    course_ids: set[str] = set()
    for les in school.lessons:
        c = idx.courses.get(les.course_id)
        if c is None or not aidx.in_week(les, c, monday):
            continue
        parts: Optional[list[int]] = None
        if kind == "class":
            if ref not in c.classes:
                continue
        elif kind == "teacher":
            parts = [i for i, p in enumerate(c.parts) if p.teacher == ref]
            if not parts:
                continue
        elif kind == "room":
            parts = [i for i, r in enumerate(les.rooms) if r == ref]
            if not parts:
                continue
        elif kind == "student":
            if c.id not in student_sel:
                continue
            parts = student_sel[c.id]
        cell = lesson_info(school, les, parts, idx)
        cell["weeks_text"] = weeks_text(les, c, labels)
        cells.append(cell)
        course_ids.add(c.id)
    cells.sort(key=lambda x: (x["day"], x["start"]))
    sunday = monday + timedelta(days=6)
    exam_days = set()
    for ex in school.exams:
        try:
            ed = date.fromisoformat(str(ex.date)[:10])
        except ValueError:
            continue
        if monday <= ed <= sunday and ex.course_id in course_ids:
            exam_days.add(ed.weekday())
    n_days = visible_days(school, cells, teaching if ref_class is not None else (), all_days, exam_days)
    return {
        "kind": kind, "ref": ref, "title": title, "week_no": real,
        "days": WEEKDAYS[:n_days],
        "day_info": [day_info(school, monday + timedelta(days=i), ref_class) for i in range(n_days)],
        "week_info": week_info(school, monday, ref_class),
        "periods": [{"index": i, "label": f"{i + 1}.",
                     "time": st.period_times[i] if i < len(st.period_times) else ""}
                    for i in range(st.periods)],
        "breaks": st.breaks,
        "blocked": blocked,
        "cells": cells,
    }


# ------------------------------------------------------------------ occupancy
class _Occupancy:
    """Belegung (Wochenvariante, Tag, Stunde) für Klassen, Lehrer und Räume (``weeks.PlanWeeks``)."""

    def __init__(self, school: School, exclude: Optional[str] = None):
        self.school = school
        self.idx = _Index(school)
        self.pw = wk.PlanWeeks(school)
        self.cls: dict[tuple, str] = {}
        self.tch: dict[tuple, str] = {}
        self.room: dict[tuple, str] = {}
        self.site_t: dict[tuple, str] = {}
        self.site_c: dict[tuple, str] = {}
        self.course_day: dict[tuple, int] = defaultdict(int)
        for les in school.lessons:
            if les.id == exclude:
                continue
            c = self.idx.courses.get(les.course_id)
            if c is None:
                continue
            site = lesson_site(school, les, self.idx.rooms, self.idx.classes, self.idx.courses)
            for w in self.pw.lesson_groups(les, c):
                self.course_day[(c.id, w, les.day)] += 1
                for k in range(les.length):
                    key = (w, les.day, les.start + k)
                    for cid in c.classes:
                        self.cls[(cid,) + key] = les.id
                        self.site_c[(cid,) + key] = site
                    for p in c.parts:
                        if p.teacher:
                            self.tch[(p.teacher,) + key] = les.id
                            self.site_t[(p.teacher,) + key] = site
                    for r in les.rooms:
                        if r:
                            self.room[(r,) + key] = les.id


def _free_room(occ: _Occupancy, school: School, current: Optional[str], keys: list[tuple],
               taken: set[str], site: str) -> Optional[str]:
    rooms = occ.idx.rooms
    if current is None:
        return None
    cur = rooms.get(current)
    cands = [current] + sorted(
        (r.id for r in rooms.values() if cur and r.type == cur.type and r.id != current),
        key=lambda rid: (rooms[rid].site != site, rid))
    for rid in cands:
        if rid in taken:
            continue
        if all((rid,) + k not in occ.room for k in keys):
            return rid
    return "__none__"


def _evaluate(school: School, occ: _Occupancy, les: Lesson, day: int, start: int):
    """Liefert (Konflikte, neue Räume)."""
    st = school.settings
    idx = occ.idx
    conflicts: list[str] = []
    c = idx.courses.get(les.course_id)
    if c is None:
        return [f"Kurs {les.course_id} unbekannt"], les.rooms
    if start < 0 or start + les.length > st.periods or not 0 <= day <= 6:
        return ["Außerhalb des Zeitrasters"], les.rooms
    if day not in course_days(school, c, idx.classes):
        return ["Kein Unterrichtstag der Klasse."], les.rooms
    pw = occ.pw
    weeks = pw.lesson_groups(les, c)
    keys = [(w, day, start + k) for w in weeks for k in range(les.length)]

    def wl(w: int) -> str:
        return pw.label(w)
    for cid in c.classes:
        cls = idx.classes.get(cid)
        if cls is None:
            continue
        for (w, d, p) in keys:
            if p >= cls.max_periods_per_day:
                conflicts.append(f"Klasse {cls.name}: max. {cls.max_periods_per_day} Stunden pro Tag")
                break
            rule = next((r for r in cls.unavailable if r.matches(pw.real_week(w), d, p)), None)
            if rule:
                conflicts.append(f"Klasse {cls.name} ist nicht da{wl(w)}: {rule.note or 'gesperrt'}")
                break
            other = occ.cls.get((cid, w, d, p))
            if other:
                conflicts.append(f"Klasse {cls.name} hat bereits Unterricht ({other}) in der {p + 1}. Stunde{wl(w)}")
                break
    for part in c.parts:
        if not part.teacher:
            continue
        t = idx.teachers.get(part.teacher)
        for (w, d, p) in keys:
            if t:
                rule = next((r for r in t.unavailable if r.matches(pw.real_week(w), d, p)), None)
                if rule:
                    conflicts.append(f"Lehrkraft {t.id} ist nicht verfügbar{wl(w)}: {rule.note or 'gesperrt'}")
                    break
            other = occ.tch.get((part.teacher, w, d, p))
            if other:
                conflicts.append(f"Lehrkraft {part.teacher} unterrichtet bereits ({other}) in der {p + 1}. Stunde{wl(w)}")
                break
    # Fach max pro Tag
    subj = idx.subjects.get(c.parts[0].subject) if c.parts else None
    max_pd = max(1, subj.max_per_day if subj else 1)
    n_days = max(1, len(course_days(school, c, idx.classes)))     # U-51: dieselben Tage wie der Generator
    if c.hours > n_days:
        max_pd = max(max_pd, -(-c.hours // n_days))
    for w in weeks:
        if occ.course_day[(c.id, w, day)] >= max_pd:
            conflicts.append(f"{c.label or c.id} liegt an diesem Tag bereits {occ.course_day[(c.id, w, day)]}×")
            break
    # Räume
    site = lesson_site(school, les, idx.rooms, idx.classes, idx.courses)
    new_rooms: list[Optional[str]] = []
    taken: set[str] = set()
    for r in les.rooms:
        nr = _free_room(occ, school, r, keys, taken, site)
        if nr == "__none__":
            conflicts.append(f"Kein freier Raum vom Typ wie {r}")
            nr = r
        if nr:
            taken.add(nr)
        new_rooms.append(nr)
    # Wegezeit zwischen Standorten
    T = st.site_travel_periods
    teachers = school.index("teachers")
    special = commute.special(st, school.teachers)        # Wegezeiten je Standortpaar / Mindestpausen
    if (T or special) and site:
        for (w, d, p0) in {(w, day, start) for w in weeks}:
            if special:
                last = start + les.length - 1
                for part in c.parts:
                    teacher = teachers.get(part.teacher) if part.teacher else None
                    if teacher is None:
                        continue
                    for p in range(st.periods):
                        s2 = occ.site_t.get((part.teacher, w, d, p)) if not start <= p <= last else None
                        if s2 and s2 != site and not (
                                commute.change_ok(st, teacher, s2, p, site, start) if p < start
                                else commute.change_ok(st, teacher, site, last, s2, p)):
                            conflicts.append(f"Lehrkraft {part.teacher}: Standortwechsel ohne ausreichende Pause "
                                             f"({p + 1}. Stunde)")
            lo, hi = max(0, start - T), min(st.periods, start + les.length + T)
            for p in range(lo, hi):
                if start <= p < start + les.length:
                    continue
                for part in c.parts:
                    s2 = occ.site_t.get((part.teacher, w, d, p)) if part.teacher and not special else None
                    if s2 and s2 != site:
                        conflicts.append(f"Lehrkraft {part.teacher}: Standortwechsel ohne Wegezeit ({p + 1}. Stunde)")
                for cid in c.classes:
                    s2 = occ.site_c.get((cid, w, d, p))
                    if s2 and s2 != site:
                        conflicts.append(f"Klasse {cid}: Standortwechsel ohne Wegezeit ({p + 1}. Stunde)")
    # Duplikate entfernen, Reihenfolge erhalten
    seen = set()
    conflicts = [x for x in conflicts if not (x in seen or seen.add(x))]
    return conflicts, new_rooms


def _find(school: School, lesson_id: str) -> Lesson:
    for les in school.lessons:
        if les.id == lesson_id:
            return les
    raise KeyError(f"Stunde {lesson_id} unbekannt")


def check_move(school: School, lesson_id: str, day: int, start: int) -> list[str]:
    les = _find(school, lesson_id)
    occ = _Occupancy(school, exclude=lesson_id)
    return _block_conflict(school, les, start) + _evaluate(school, occ, les, day, start)[0]


def _block_conflict(school: School, les: Lesson, start: int) -> list[str]:
    if school.settings.block_start_ok(start, les.length, school.settings.periods):
        return []
    return [f"Doppelstunde {start + 1}.–{start + les.length}. Stunde liegt über einer Pause bzw. nicht im Pausenblock"]


def move_lesson(school: School, lesson_id: str, day: int, start: int) -> Lesson:
    """Verschiebt eine Stunde (Räume werden bei Bedarf getauscht). ValueError bei Konflikten."""
    les = _find(school, lesson_id)
    occ = _Occupancy(school, exclude=lesson_id)
    conflicts, rooms = _evaluate(school, occ, les, day, start)
    conflicts = _block_conflict(school, les, start) + conflicts
    if conflicts:
        raise ValueError(conflicts)
    les.day, les.start, les.rooms = day, start, rooms
    return les


def move_options(school: School, lesson_id: str) -> list[dict]:
    les = _find(school, lesson_id)
    occ = _Occupancy(school, exclude=lesson_id)
    st = school.settings
    out = []
    course = occ.idx.courses.get(les.course_id)
    days = course_days(school, course, occ.idx.classes) if course else open_days(school)
    for d in days:
        for s in range(st.periods - les.length + 1):
            conflicts = _block_conflict(school, les, s) + _evaluate(school, occ, les, d, s)[0]
            out.append({"day": d, "start": s, "ok": not conflicts, "conflicts": conflicts})
    return out


# --------------------------------------------------------------------- report
def validate_school(school: School, today: Optional[date] = None, details: bool = False) -> dict:
    """Qualitätsbericht: fehlende Stunden, Doppelbelegungen, Hohl-/Springstunden …

    Rechnet über die Wochenvarianten des Schuljahres („Wochenmuster“: Wochen mit gleichen Regeln); Hohl-/Springstunden
    und Standortwechsel in ``stats`` sind der Durchschnitt je Schulwoche (gewichtet nach Anteil der Wochen) und deshalb
    bei mehreren Wochenmustern auch halbe Werte. ``ranges`` nennt die Spanne je Woche (kleinster/größter Wert eines
    Wochenmusters). Fehlende/zu viele Stunden zählen je Wochenmuster des Kurses.

    ``details=True`` liefert zusätzlich ``details`` mit den einzelnen Fundstellen (Tag, Stunde, Wochen) für die
    Einzelansichten der Kennzahlen."""
    st = school.settings
    idx = _Index(school)
    pw = wk.PlanWeeks(school, today)
    V = len(pw)
    warnings: list[str] = []
    conflicts: list[str] = []
    placed: dict[tuple[str, int], int] = defaultdict(int)
    occ_cls: dict[tuple, list[str]] = defaultdict(list)
    occ_t: dict[tuple, list[str]] = defaultdict(list)
    occ_r: dict[tuple, list[str]] = defaultdict(list)
    site_t: dict[tuple, str] = {}
    core_late = 0
    core_late_items: list[dict] = []
    never: list[str] = []
    from .rules import core_latest_for
    core_latest = core_latest_for(school)      # je Kurs (Ausnahmen der Regel „Hauptfächer früh am Tag“)
    for les in school.lessons:
        c = idx.courses.get(les.course_id)
        if c is None:
            warnings.append(f"Stunde {les.id}: Kurs {les.course_id} existiert nicht mehr")
            continue
        subj = idx.subjects.get(c.parts[0].subject) if c.parts else None
        if subj and subj.core and les.start + les.length - 1 > core_latest(c):
            core_late += 1
            core_late_items.append({"lesson": les.id, "course": c.id, "label": c.label or c.id, "classes": list(c.classes),
                                    "teachers": [p.teacher for p in c.parts if p.teacher], "day": les.day,
                                    "period": les.start + les.length})
        site = lesson_site(school, les, idx.rooms, idx.classes, idx.courses)
        groups = pw.lesson_groups(les, c)
        if not groups:
            never.append(c.label or c.id)
        for g in groups:
            placed[(c.id, g)] += les.length
            for k in range(les.length):
                key = (g, les.day, les.start + k)
                for cid in c.classes:
                    occ_cls[(cid,) + key].append(les.id)
                for p in c.parts:
                    if p.teacher:
                        occ_t[(p.teacher,) + key].append(les.id)
                        site_t[(p.teacher,) + key] = site
                for r in les.rooms:
                    if r:
                        occ_r[(r,) + key].append(les.id)
    for name in dict.fromkeys(never):
        warnings.append(f"Kurs {name}: Eine Stunde liegt in keiner Woche des Schuljahres.")
    times = st.period_times
    conflict_items: list[dict] = []
    for name, kind, occ in (("Klasse", "class", occ_cls), ("Lehrkraft", "teacher", occ_t), ("Raum", "room", occ_r)):
        for key, ids in occ.items():
            if len(ids) > 1:
                g, d, p = key[1], key[2], key[3]
                t = f" {times[p]}" if p < len(times) else ""
                when = pw.hz.describe(pw.groups[g]) if V > 1 else "jede Woche"
                text = f"{name} {key[0]} doppelt belegt: {WEEKDAYS[d][:2]} {p + 1}. Stunde{t}, {when}: {', '.join(ids)}"
                conflicts.append(text)
                conflict_items.append({"text": text, "kind": kind, "id": key[0], "day": d, "period": p + 1,
                                       "weeks_text": when, "lessons": list(ids)})
    unplaced = []
    overplaced = []
    for c in school.courses:
        for g in pw.spec_groups(c):
            if not pw.planned[g]:
                continue
            text = pw.hz.describe(pw.groups[g]) if V > 1 else "jede Woche"
            missing = c.hours - placed[(c.id, g)]
            if missing > 0:
                if any(not p.teacher for p in c.parts):
                    reason = "Kursteil ohne Lehrkraft"
                elif placed[(c.id, g)] == 0:
                    reason = "noch keine Stunde gelegt"
                else:
                    reason = f"erst {placed[(c.id, g)]} von {c.hours} Stunden gelegt"
                unplaced.append({"course": c.id, "label": c.label or c.id, "weeks_text": text, "missing": missing,
                                 "hours": c.hours, "placed": placed[(c.id, g)], "reason": reason})
            elif missing < 0:
                overplaced.append({"course": c.id, "label": c.label or c.id, "weeks_text": text,
                                   "extra": -missing, "hours": c.hours, "placed": placed[(c.id, g)]})
    if unplaced:
        warnings.append(f"{sum(u['missing'] for u in unplaced)} Unterrichtsstunden sind nicht verplant")
    if overplaced:
        names = ", ".join(dict.fromkeys(o["label"] for o in overplaced))
        warnings.append(f"{sum(o['extra'] for o in overplaced)} Unterrichtsstunden zu viel verplant "
                        f"(mehr als die Wochenstunden des Kurses): {names[:300]} – Stundenplan im Generator prüfen")

    days_all = list(range(7))

    def gaps(occ, ids, blocked_fn):
        """Summe (Durchschnitt je Schulwoche), je Kennung, Summe je Wochenmuster und die einzelnen Lücken."""
        total = 0.0
        per: dict[str, float] = {}
        per_group = [0.0] * V
        cells: dict[tuple, set] = defaultdict(set)
        for ident in ids:
            n = 0.0
            for g in range(V):
                for d in days_all:
                    ps = [p for p in range(st.periods) if (ident, g, d, p) in occ]
                    if ps:
                        for p in range(ps[0], ps[-1] + 1):
                            if (ident, g, d, p) not in occ and not blocked_fn(ident, g, d, p):
                                n += pw.weight[g]
                                per_group[g] += 1
                                cells[(ident, d, p)].add(g)
            n = round(n, 6)
            if n:
                per[ident] = _num(n)
            total += n
        return _num(round(total, 6)), per, per_group, cells

    def cls_blocked(cid, g, d, p):
        cl = idx.classes.get(cid)
        if not cl:
            return False
        return any(r.matches(pw.real_week(g), d, p) for r in cl.unavailable)

    def weeks_of(groups: set) -> str:
        if len(groups) >= V:
            return "jede Woche"
        return pw.hz.describe(i for g in sorted(groups) for i in pw.groups[g])

    def gap_rows(kind: str, cells: dict) -> list[dict]:
        return [{"kind": kind, "id": ident, "day": d, "period": p + 1, "weeks_text": weeks_of(gs)}
                for (ident, d, p), gs in sorted(cells.items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2]))]

    class_gaps, class_gap_detail, class_pg, class_cells = gaps(occ_cls, idx.classes.keys(), cls_blocked)
    teacher_gaps, teacher_gap_detail, teacher_pg, teacher_cells = gaps(occ_t, idx.teachers.keys(), lambda *a: False)
    site_changes = 0.0
    site_per: dict[str, float] = defaultdict(float)
    site_pg = [0.0] * V
    site_cells: dict[tuple, set] = defaultdict(set)
    commute_viol = 0.0
    commute_rows: dict[tuple, set] = defaultdict(set)
    for t in idx.teachers:
        for g in range(V):
            for d in days_all:
                seq = [(p, site_t[(t, g, d, p)]) for p in range(st.periods) if (t, g, d, p) in site_t]
                for text in commute.violations(st, idx.teachers[t], dict(seq)):   # Pendelregeln der Lehrkraft
                    commute_viol += pw.weight[g]
                    commute_rows[(t, d, text)].add(g)
                for (_, a), (p2, b) in zip(seq, seq[1:]):
                    if a != b:
                        site_changes += pw.weight[g]
                        site_per[t] += pw.weight[g]
                        site_pg[g] += 1
                        site_cells[(t, d, p2, a, b)].add(g)
    site_changes = _num(round(site_changes, 6))
    commute_viol = _num(round(commute_viol, 6))
    if commute_rows:
        names = sorted({t for t, _, _ in commute_rows})
        warnings.append(f"Pendelregeln verletzt bei {len(names)} Lehrkraft/Lehrkräften: " + ", ".join(names[:15]))
    if class_gaps:
        warnings.append(f"{class_gaps} Hohlstunden bei Klassen: "
                        + ", ".join(f"{k} ({v})" for k, v in sorted(class_gap_detail.items())[:15]))
    load: dict[str, int] = defaultdict(int)
    for c in school.courses:
        for p in c.parts:
            if p.teacher:
                load[p.teacher] += c.hours
    overloaded = []
    for t in idx.teachers.values():
        if load[t.id] > t.max_hours:
            warnings.append(f"Lehrkraft {t.id}: {load[t.id]} Stunden > Deputat {t.max_hours}")
            overloaded.append(t.id)

    def spread(per_group: list[float]) -> dict:
        """Kleinster/größter Wert je Wochenmuster und Durchschnitt je Schulwoche."""
        avg = sum(w * x for w, x in zip(pw.weight, per_group))
        used = [x for x, ok in zip(per_group, pw.planned) if ok] or per_group     # ohne Wochen ohne Plan
        return {"min": _num(min(used)), "max": _num(max(used)), "avg": _num(round(avg, 6))}

    out = {
        "stats": {
            "lessons": len(school.lessons),
            "courses": len(school.courses),
            "classes": len(school.classes),
            "teachers": len(school.teachers),
            "students": len(school.students),
            "class_gaps": class_gaps,
            "teacher_gaps": teacher_gaps,
            "site_changes": site_changes,
            "commute_violations": commute_viol,
            "core_late": core_late,
            "conflicts": len(conflicts),
            "unplaced_hours": sum(u["missing"] for u in unplaced),
            "overplaced_hours": sum(o["extra"] for o in overplaced),
            "overloaded_teachers": len(overloaded),
            "week_variants": V,
        },
        "ranges": {"class_gaps": spread(class_pg), "teacher_gaps": spread(teacher_pg), "site_changes": spread(site_pg)},
        "warnings": warnings,
        "conflicts": conflicts[:200],
        "unplaced_hours": unplaced,
        "overplaced_hours": overplaced,
        "class_gaps": class_gap_detail,
    }
    if details:
        site_sorted = sorted(site_cells.items(), key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2]))
        out["per_entity"] = {   # Werte je Klasse bzw. Lehrkraft (Durchschnitt je Schulwoche), ohne Kappung
            "class_gaps": dict(class_gap_detail), "teacher_gaps": dict(teacher_gap_detail),
            "site_changes": {t: _num(round(v, 6)) for t, v in site_per.items() if v},
        }
        out["details"] = {
            "class_gaps": gap_rows("class", class_cells)[:_DETAIL_CAP],
            "teacher_gaps": gap_rows("teacher", teacher_cells)[:_DETAIL_CAP],
            "site_changes": [{"kind": "teacher", "id": t, "day": d, "period": p + 1, "weeks_text": weeks_of(gs),
                              "from_site": a, "to_site": b} for (t, d, p, a, b), gs in site_sorted][:_DETAIL_CAP],
            "commute": [{"kind": "teacher", "id": t, "day": d, "weeks_text": weeks_of(gs), "text": text}
                        for (t, d, text), gs in sorted(commute_rows.items(),
                                                       key=lambda kv: (str(kv[0][0]), kv[0][1], kv[0][2]))][:_DETAIL_CAP],
            "conflicts": conflict_items[:_DETAIL_CAP],
            "core_late": core_late_items[:_DETAIL_CAP],
            "unplaced": unplaced[:_DETAIL_CAP],
            "overplaced": overplaced[:_DETAIL_CAP],
            "teachers": sorted(
                ({"id": t.id, "name": t.name, "max_hours": t.max_hours, "load": load[t.id],
                  "over": max(0, load[t.id] - t.max_hours)} for t in idx.teachers.values()),
                key=lambda r: (-r["over"], r["name"])),
            "weeks": [{"weeks_text": pw.hz.describe(pw.groups[g]) if V > 1 else "jede Woche",
                       "week_count": len(pw.groups[g]), "class_gaps": _num(class_pg[g]),
                       "teacher_gaps": _num(teacher_pg[g]), "site_changes": _num(site_pg[g])} for g in range(V)],
        }
    return out


_DETAIL_CAP = 400


def _num(x: float):
    """Ganze Zahl, wenn möglich (Zählwerte über Wochenvarianten), sonst auf eine Stelle gerundet."""
    return int(round(x)) if abs(x - round(x)) < 1e-6 else round(x, 1)
