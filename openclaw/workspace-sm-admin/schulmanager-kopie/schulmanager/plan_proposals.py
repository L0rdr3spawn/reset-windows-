"""Plan prüfen: Vorschlagspakete – reine Logik (ohne Datenbank, ohne Hintergrundprozesse).

Die Dauerprüfung (``server/autoplan.py``) findet Probleme im regulären Stundenplan (:func:`autoplan.find_problems`);
:mod:`server.proposals` rechnet daraus mehrere Lösungen. Dieses Modul liefert die Bausteine:

* :func:`metrics` – Kennzahlen eines Plans (Probleme, Konflikte, Hohl-/Springstunden … und die Regel-Bausteine
  aus :func:`rules.violations`), damit „vorher/nachher“ je Variante vergleichbar ist;
* :func:`state_hash` – Fingerabdruck von Stundenplan **und** Problemlage: ändert sich einer der beiden, ist ein
  Paket veraltet (andere Änderungen wie Krankmeldungen oder Mitteilungen ändern ihn nicht);
* :func:`diff_lessons` / :func:`apply_diff` – Unterschied zweier Stundenpläne und seine Anwendung auf den Plan;
* :func:`describe_changes` – lesbare Änderungsliste (Kurs: von → nach, Raumwechsel), betroffene Klassen/Lehrkräfte;
* :func:`variant_specs` – welche Lösungen berechnet werden (minimal, lokal, gründlich, ggf. Vertretung);
* :func:`valid_from_hint` – ab wann der Anlass gilt (kleinstes „gilt ab“ der beteiligten Sperrzeiten);
* :func:`substitution_cover` – Stunden, die statt einer Planänderung per Vertretung abgedeckt werden könnten.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Optional

from . import rules as rl
from . import weeks as wk
from .autoplan import Problems, expand_courses, find_problems
from .models import Lesson, School, lesson_in_range, spec_active
from .timetable import validate_school

DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
METRIC_KEYS = ("problems", "conflicts", "unplaced_hours", "class_gaps", "teacher_gaps", "site_changes",
               "core_late", "late_start", "spread", "doubles", "teacher_wish")
#: Kennzahlen, bei denen weniger besser ist (alle)
MAX_CHANGES = 200


# --------------------------------------------------------------------------- Kennzahlen
def metrics(school: School, problems: Optional[Problems] = None) -> dict[str, Any]:
    """Kennzahlen eines Plans (kleiner = besser): Probleme der Dauerprüfung, Konflikte, unverplante Stunden,
    Hohl-/Springstunden, Standortwechsel, späte Hauptfächer und die Regel-Bausteine aus ``rules.violations``."""
    pr = problems or find_problems(school)
    stats = validate_school(school)["stats"]
    viol = rl.violations(school, stats)
    out: dict[str, Any] = {
        "problems": pr.count(), "conflicts": stats["conflicts"], "unplaced_hours": stats["unplaced_hours"],
        "class_gaps": stats["class_gaps"], "teacher_gaps": stats["teacher_gaps"],
        "site_changes": stats["site_changes"], "core_late": stats["core_late"],
    }
    for key in ("late_start", "spread", "doubles", "teacher_wish"):
        out[key] = viol.get(key)
    return out


# --------------------------------------------------------------------------- Stand des Plans
def lessons_fingerprint(school: School) -> str:
    rows = sorted((le.id, le.course_id, le.day, le.start, le.length, list(le.weeks or []),
                   json.dumps(le.rhythm, sort_keys=True) if le.rhythm else "", list(le.rooms or []),
                   bool(le.locked)) for le in school.lessons)
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def state_hash(school: School, problems: Optional[Problems] = None) -> str:
    """Stundenplan + Problemlage. Unabhängig von Krankmeldungen, Vertretungsentscheidungen und Texten."""
    pr = problems or find_problems(school)
    return hashlib.sha256((lessons_fingerprint(school) + "|" + pr.signature()).encode("utf-8")).hexdigest()[:32]


# --------------------------------------------------------------------------- Unterschied zum Plan
def _lesson_json(le: Lesson) -> str:
    return json.dumps(le.to_dict(), sort_keys=True, ensure_ascii=False, default=str)


def diff_lessons(old: Iterable[Lesson], new: Iterable[Lesson]) -> dict[str, list]:
    """``{"upsert": [Stunde als Dict …], "delete": [IDs]}`` – neue oder geänderte bzw. entfernte Stunden."""
    old_by = {le.id: le for le in old}
    new_list = list(new)
    new_ids = {le.id for le in new_list}
    upsert = [le.to_dict() for le in new_list if le.id not in old_by or _lesson_json(old_by[le.id]) != _lesson_json(le)]
    delete = sorted(i for i in old_by if i not in new_ids)
    return {"upsert": upsert, "delete": delete}


def apply_diff(school: School, diff: dict) -> None:
    """Wendet ``diff`` auf ``school`` an (verändert es) und entfernt Tagesentscheidungen zu verlegten Stunden."""
    upsert = {d["id"]: d for d in diff.get("upsert", [])}
    gone = set(diff.get("delete", []))
    courses = school.index("courses")
    seen: set[str] = set()
    out: list[Lesson] = []

    def build(data: dict) -> Optional[Lesson]:
        le = Lesson.from_dict(data)
        c = courses.get(le.course_id)
        if c is None:
            return None
        n = len(c.parts)
        le.rooms = (list(le.rooms) + [None] * n)[:n]
        return le

    for le in school.lessons:
        if le.id in gone:
            continue
        if le.id in upsert:
            seen.add(le.id)
            new = build(upsert[le.id])
            if new is not None:
                out.append(new)
            continue
        out.append(le)
    for lid, data in upsert.items():
        if lid not in seen:
            new = build(data)
            if new is not None:
                out.append(new)
    replaced = {le.id for le in school.lessons} - {le.id for le in out}
    school.lessons = out
    if replaced:
        school.overrides = [o for o in school.overrides if o.lesson_id not in replaced]


def _weeks_key(school: School, le: Lesson) -> tuple:
    if le.weeks or le.rhythm or le.from_week or le.to_week:
        return tuple(w for w in range(1, 54) if spec_active(le.weeks, le.rhythm, w) and lesson_in_range(le, w))
    return ()


def _where(school: School, le: Lesson) -> str:
    span = f"{le.start + 1}." + (f"–{le.start + le.length}." if le.length > 1 else "")
    weeks = _weeks_key(school, le)
    text = f"{DAYS[le.day] if 0 <= le.day < len(DAYS) else le.day} {span}"
    return text + (f" ({wk.describe(weeks)})" if weeks else "")


def _slot(school: School, le: Lesson) -> tuple:
    return (le.day, le.start, le.length, _weeks_key(school, le))


def describe_changes(before: School, after: School) -> list[dict]:
    """Lesbare Änderungsliste je Kurs: verschobene Stunden (``from`` → ``to``) und Raumwechsel (``rooms``)."""
    courses = after.index("courses")
    courses_b = before.index("courses")
    by_b: dict[str, list[Lesson]] = {}
    by_a: dict[str, list[Lesson]] = {}
    for le in before.lessons:
        by_b.setdefault(le.course_id, []).append(le)
    for le in after.lessons:
        by_a.setdefault(le.course_id, []).append(le)
    out: list[dict] = []
    for cid in sorted(set(by_b) | set(by_a)):
        old, new = by_b.get(cid, []), by_a.get(cid, [])
        old_slots = {_slot(before, le): le for le in old}
        new_slots = {_slot(after, le): le for le in new}
        removed = [old_slots[k] for k in sorted(old_slots) if k not in new_slots]
        added = [new_slots[k] for k in sorted(new_slots) if k not in old_slots]
        room_changes = []
        for k in sorted(set(old_slots) & set(new_slots)):
            a, b = old_slots[k], new_slots[k]
            if list(a.rooms or []) != list(b.rooms or []):
                room_changes.append({"where": _where(after, b),
                                     "old": [r for r in (a.rooms or []) if r], "new": [r for r in (b.rooms or []) if r]})
        if not (removed or added or room_changes):
            continue
        c = courses.get(cid) or courses_b.get(cid)
        teachers = sorted({p.teacher for p in c.parts if p.teacher}) if c else []
        out.append({"course_id": cid, "label": (c.label or cid) if c else cid,
                    "classes": list(c.classes) if c else [], "teachers": teachers,
                    "from": [_where(before, x) for x in removed], "to": [_where(after, x) for x in added],
                    "rooms": room_changes[:20]})
    return out[:MAX_CHANGES]


def affected(changes: list[dict]) -> tuple[list[str], list[str]]:
    classes = sorted({c for ch in changes for c in ch.get("classes", [])})
    teachers = sorted({t for ch in changes for t in ch.get("teachers", [])})
    return classes, teachers


def count_moved(changes: list[dict]) -> int:
    return sum(len(ch.get("to", [])) for ch in changes)


# --------------------------------------------------------------------------- Gültigkeit
def valid_from_hint(school: School, problems: Problems) -> Optional[str]:
    """Kleinstes „gilt ab“ der Sperrzeiten, die an den Problemen beteiligt sind (Lehrkräfte/Klassen der betroffenen
    Kurse). ``None``: die Probleme gelten von jeher bzw. nicht datumsgebunden."""
    courses = school.index("courses")
    teachers = school.index("teachers")
    classes = school.index("classes")
    dates: list[str] = []
    for cid in problems.courses():
        c = courses.get(cid)
        if c is None:
            continue
        for p in c.parts:
            t = teachers.get(p.teacher) if p.teacher else None
            if t is not None:
                dates += [r.valid_from for r in t.unavailable if r.valid_from]
        for k in c.classes:
            cl = classes.get(k)
            if cl is not None:
                dates += [r.valid_from for r in cl.unavailable if getattr(r, "valid_from", "")]
    return min(dates) if dates else None


# --------------------------------------------------------------------------- Vertretung statt Planänderung
TEACHER_REASONS = ("gesperrt", "unterrichtet nicht am Standort")


def substitution_cover(school: School, problems: Problems) -> Optional[list[dict]]:
    """Stunden, die ohne Planänderung vertreten werden könnten. ``None``, wenn die Probleme nicht ausschließlich
    Stunden betreffen, bei denen eine Lehrkraft fehlt (Sperrzeit/Standort) – dann gibt es diese Variante nicht."""
    if problems.orphans or problems.missing or problems.excess or not problems.lessons:
        return None
    courses = school.index("courses")
    lessons = {le.id: le for le in school.lessons}
    out: list[dict] = []
    for lid, reasons in sorted(problems.lessons.items()):
        if not reasons or not all(any(t in r for t in TEACHER_REASONS) for r in reasons):
            return None
        le = lessons.get(lid)
        c = courses.get(le.course_id) if le else None
        if le is None or c is None:
            return None
        out.append({"lesson_id": lid, "course_id": c.id, "label": c.label or c.id, "classes": list(c.classes),
                    "teachers": sorted({p.teacher for p in c.parts if p.teacher}), "where": _where(school, le),
                    "reason": reasons[0]})
    return out


# --------------------------------------------------------------------------- Varianten
@dataclass(frozen=True)
class VariantSpec:
    key: str
    title: str
    description: str
    scope: str          # minimal | classes | wide
    seed: int
    time_factor: float


SPECS = (
    VariantSpec("minimal", "Minimal: nur betroffene Stunden verschieben",
                "Nur die Kurse mit Problemen werden neu gelegt, alles andere bleibt, wie es ist.", "minimal", 1, 1.0),
    VariantSpec("lokal", "Lokal: betroffene Lehrkräfte und Klassen neu planen",
                "Zusätzlich dürfen alle Kurse der beteiligten Klassen und Lehrkräfte wandern – mehr Spielraum, "
                "dafür mehr Änderungen.", "classes", 2, 1.5),
    VariantSpec("gruendlich", "Gründlich: größerer Teilbereich, bessere Qualität",
                "Ein größerer Teilbereich wird mit mehr Rechenzeit neu geplant – meist weniger Hohl- und "
                "Springstunden, aber die meisten Änderungen.", "wide", 3, 3.0),
)


def variant_specs() -> tuple[VariantSpec, ...]:
    return SPECS


def free_courses_for(school: School, base_free: list[str], scope: str) -> list[str]:
    free = sorted(set(base_free))
    if scope == "minimal":
        return free
    first = expand_courses(school, free)
    if scope == "classes":
        return first
    second = expand_courses(school, first)
    # nicht gleich die ganze Schule: höchstens doppelt so viele Kurse (bzw. +25) wie die lokale Variante
    return second if len(first) < len(second) <= max(2 * len(first), len(first) + 25) else first


def today_iso() -> str:
    return date.today().isoformat()
