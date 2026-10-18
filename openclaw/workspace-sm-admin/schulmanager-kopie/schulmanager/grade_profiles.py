"""Jahrgänge/Profile (``GradeProfile``) – reine Logik ohne Datenbank: Kennzahlen, Folgen des Löschens (Jahrgang,
Stundentafel, Fach), Löschen mit Umzug, Zuordnung von Klassen.

Ein Jahrgang ist frei definierbar („5“, „5 Informatik“, „Montessori“, „GIF 26“). Klassen gehören zu genau einem
Jahrgang (``SchoolClass.profile``); der Jahrgang zeigt auf eine Stundentafel (``GradeProfile.curriculum``), die
selbst eigenständig oder von einer Basis abgeleitet sein kann (``Curriculum.base`` + ``deltas``, siehe
``planning.effective_entries``). Nichts davon ist fest verdrahtet: keine festen Stufen, keine festen Fächer.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from .models import Curriculum, CurriculumEntry, GradeProfile, School
from .planning import curriculum_hours, effective_entries, resolve_curricula

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def natural_key(value: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", value or ""))


def profile_sort_key(p: GradeProfile) -> tuple:
    return (p.grade if p.grade is not None else 999, natural_key(p.name))


def classes_of(school: School, profile_id: str) -> list:
    return [c for c in school.classes if c.profile == profile_id]


# ------------------------------------------------------------------ Kennzahlen
def profile_rows(school: School) -> list[dict]:
    """Je Jahrgang die Klassen und Zahlen (Schüler/innen, Kurse, offene Kursteile, Stundentafel mit Summe)."""
    res = resolve_curricula(school)
    curricula = school.index("curricula")
    teachers, sites = school.index("teachers"), school.index("sites")
    n_students = Counter(s.class_id for s in school.students)
    n_courses: Counter = Counter()
    open_courses: Counter = Counter()
    for c in school.courses:
        open_ = any(not p.teacher for p in c.parts)
        for cid in set(c.classes):
            n_courses[cid] += 1
            if open_:
                open_courses[cid] += 1

    def class_row(cls) -> dict:
        r = res.get(cls.id, {})
        cur = curricula.get(r.get("curriculum") or "")
        t = teachers.get(cls.class_teacher) if cls.class_teacher else None
        site = sites.get(cls.site)
        return {
            "id": cls.id, "name": cls.name, "grade": cls.grade, "profile": cls.profile,
            "site": cls.site, "site_name": site.name if site else "",
            "students": n_students.get(cls.id) or int(cls.students or 0),
            "students_listed": n_students.get(cls.id, 0),
            "class_teacher": {"id": t.id, "name": t.name} if t else None,
            "curriculum_id": cur.id if cur else None, "curriculum_name": cur.name if cur else None,
            "curriculum_source": r.get("source"), "curriculum_conflict": bool(r.get("conflict")),
            "courses": n_courses.get(cls.id, 0), "open_courses": open_courses.get(cls.id, 0),
        }

    rows = []
    for p in sorted(school.grade_profiles, key=profile_sort_key):
        cls_rows = [class_row(c) for c in sorted(classes_of(school, p.id), key=lambda c: natural_key(c.name or c.id))]
        cur = curricula.get(p.curriculum or "")
        rows.append({
            **p.to_dict(),
            "classes": cls_rows,
            "students": sum(r["students"] for r in cls_rows),
            "courses": sum(r["courses"] for r in cls_rows),
            "open_courses": sum(r["open_courses"] for r in cls_rows),
            "curriculum_info": ({"id": cur.id, "name": cur.name, "hours": curriculum_hours(school, cur),
                                 "base": cur.base, "subjects": len(effective_entries(school, cur))}
                                if cur else None),
            "curriculum_missing": bool(p.curriculum) and cur is None,
        })
    unassigned = {}
    for cls in school.classes:
        if cls.profile and cls.profile in school.index("grade_profiles"):
            continue
        unassigned.setdefault(cls.grade, []).append(class_row(cls))
    return [*rows, *[{"_unassigned": g, "classes": sorted(v, key=lambda r: natural_key(r["name"]))}
                     for g, v in sorted(unassigned.items())]]


def curriculum_rows(school: School) -> list[dict]:
    """Je Stundentafel: wirksame Zeilen, Basis, Jahrgänge, Klassen, Ist-Stunden aus den Kursen je Fach (Mittel über
    die Klassen, für den Soll/Ist-Abgleich) – Grundlage der Matrix „Fächer × Jahrgänge“."""
    res = resolve_curricula(school)
    applies: dict[str, list[str]] = {c.id: [] for c in school.curricula}
    conflicts: dict[str, list[str]] = {c.id: [] for c in school.curricula}
    for cid, info in res.items():
        for cur_id in info["candidates"]:
            (conflicts if info["conflict"] else applies)[cur_id].append(cid)
    # Ist: Stunden der Stundentafel-Kurse je Klasse und Fach (manuelle Kurse/Kopplungen zählen nicht)
    actual: dict[str, Counter] = {}
    for c in school.courses:
        if c.origin != "curriculum":
            continue
        subjects = {p.subject for p in c.parts}
        for cid in set(c.classes):
            cnt = actual.setdefault(cid, Counter())
            for subj in subjects:
                cnt[subj] += c.hours
    out = []
    for cur in sorted(school.curricula, key=lambda c: natural_key(c.name)):
        cls_ids = applies[cur.id]
        ist: dict[str, float] = {}
        if cls_ids:
            total: Counter = Counter()
            for cid in cls_ids:
                total.update(actual.get(cid, Counter()))
            ist = {s: round(h / len(cls_ids), 1) for s, h in total.items()}
        eff = effective_entries(school, cur)
        out.append({
            "id": cur.id, "name": cur.name, "base": cur.base, "classes_only": list(cur.classes),
            "grades": list(cur.grades),
            "profiles": [p.id for p in school.grade_profiles if p.curriculum == cur.id],
            "derived": [c.id for c in school.curricula if c.base == cur.id],
            "applies": cls_ids, "conflicts": conflicts[cur.id],
            "effective": [e.to_dict() for e in eff], "hours": sum(e.hours for e in eff),
            "actual": ist, "actual_hours": round(sum(ist.values()), 1),
        })
    return out


# ------------------------------------------------------------------ Folgen des Löschens
def _courses_of_classes(school: School, class_ids: set[str], only_curriculum: bool = False) -> list:
    return [c for c in school.courses if set(c.classes) & class_ids
            and (not only_curriculum or c.origin == "curriculum")]


def _lessons_of(school: School, course_ids: set[str]) -> int:
    return sum(1 for le in school.lessons if le.course_id in course_ids)


def profile_impact(school: School, profile_id: str) -> dict:
    """Was am Jahrgang hängt: Klassen (bleiben, verlieren nur die Zuordnung), deren Stundentafel-Kurse und Stunden
    (entfallen beim nächsten „Kurse erzeugen“), die Stundentafel (nur hier verwendet?), andere Jahrgänge als Ziel."""
    prof = school.index("grade_profiles").get(profile_id)
    if prof is None:
        raise KeyError(profile_id)
    classes = classes_of(school, profile_id)
    ids = {c.id for c in classes}
    courses = _courses_of_classes(school, ids, only_curriculum=True)
    cur = school.index("curricula").get(prof.curriculum or "")
    others = [p for p in school.grade_profiles if p.id != profile_id and p.curriculum == prof.curriculum]
    derived = [c.id for c in school.curricula if cur is not None and c.base == cur.id]
    return {
        "id": prof.id, "name": prof.name,
        "classes": [{"id": c.id, "name": c.name} for c in classes],
        "courses": len(courses), "lessons": _lessons_of(school, {c.id for c in courses}),
        "curriculum": ({"id": cur.id, "name": cur.name, "shared": bool(others) or bool(cur.classes),
                        "derived": derived} if cur else None),
        "alternatives": [{"id": p.id, "name": p.name, "grade": p.grade, "color": p.color}
                         for p in sorted(school.grade_profiles, key=profile_sort_key) if p.id != profile_id],
    }


def curriculum_impact(school: School, curriculum_id: str) -> dict:
    """Was an der Stundentafel hängt: Jahrgänge und Klassen, für die sie gilt, deren Kurse/Stunden, abgeleitete
    Tafeln (werden eigenständig)."""
    cur = school.index("curricula").get(curriculum_id)
    if cur is None:
        raise KeyError(curriculum_id)
    res = resolve_curricula(school)
    cls_ids = {cid for cid, info in res.items() if curriculum_id in info["candidates"]}
    names = school.index("classes")
    courses = _courses_of_classes(school, cls_ids, only_curriculum=True)
    return {
        "id": cur.id, "name": cur.name,
        "profiles": [{"id": p.id, "name": p.name} for p in school.grade_profiles if p.curriculum == curriculum_id],
        "classes": [{"id": c, "name": names[c].name} for c in sorted(cls_ids, key=natural_key) if c in names],
        "courses": len(courses), "lessons": _lessons_of(school, {c.id for c in courses}),
        "derived": [{"id": c.id, "name": c.name} for c in school.curricula if c.base == curriculum_id],
        "alternatives": [{"id": c.id, "name": c.name} for c in sorted(school.curricula, key=lambda c: natural_key(c.name))
                         if c.id != curriculum_id],
    }


def subject_impact(school: School, subject_id: str) -> dict:
    """Was am Fach hängt: Stundentafeln (Zeilen), Kurse mit Stunden, Lehrkräfte mit dem Fach."""
    if subject_id not in school.index("subjects"):
        raise KeyError(subject_id)
    courses = [c for c in school.courses if any(p.subject == subject_id for p in c.parts)]
    curricula = [c for c in school.curricula
                 if any(e.subject == subject_id for e in c.entries) or any(e.subject == subject_id for e in c.deltas)]
    return {
        "id": subject_id,
        "curricula": [{"id": c.id, "name": c.name} for c in curricula],
        "courses": len(courses), "lessons": _lessons_of(school, {c.id for c in courses}),
        "teachers": sum(1 for t in school.teachers if subject_id in t.subjects),
        "exams": sum(1 for e in school.exams if e.course_id in {c.id for c in courses}),
    }


# ------------------------------------------------------------------ Änderungen (mutieren ``school``)
def assign_classes(school: School, class_ids: list[str], profile_id: Optional[str]) -> list[str]:
    """Klassen einem Jahrgang zuordnen (``None`` = Zuordnung aufheben). Liefert die geänderten Klassen-IDs."""
    if profile_id and profile_id not in school.index("grade_profiles"):
        raise KeyError(profile_id)
    wanted = set(class_ids)
    changed = []
    for cls in school.classes:
        if cls.id in wanted and (cls.profile or None) != (profile_id or None):
            cls.profile = profile_id or None
            changed.append(cls.id)
    return changed


def delete_profile(school: School, profile_id: str, move_to: Optional[str] = None,
                   delete_curriculum: bool = False) -> dict:
    """Jahrgang löschen: Klassen wandern nach ``move_to`` (oder verlieren die Zuordnung). Mit ``delete_curriculum``
    geht die nur hier verwendete Stundentafel mit (abgeleitete Tafeln werden eigenständig). Kurse bleiben – sie
    ändern sich erst mit „Kurse erzeugen“."""
    prof = school.index("grade_profiles").get(profile_id)
    if prof is None:
        raise KeyError(profile_id)
    if move_to and (move_to == profile_id or move_to not in school.index("grade_profiles")):
        raise ValueError(move_to)
    impact = profile_impact(school, profile_id)
    moved = assign_classes(school, [c["id"] for c in impact["classes"]], move_to)
    school.grade_profiles = [p for p in school.grade_profiles if p.id != profile_id]
    removed_curriculum = None
    if delete_curriculum and impact["curriculum"] and not impact["curriculum"]["shared"]:
        delete_curriculum_keep_derived(school, impact["curriculum"]["id"])
        removed_curriculum = impact["curriculum"]["id"]
    return {"deleted": profile_id, "moved_classes": moved, "moved_to": move_to,
            "removed_curriculum": removed_curriculum, "impact": impact}


def materialize(school: School, cur: Curriculum) -> None:
    """Abgeleitete Tafel eigenständig machen: wirksame Zeilen werden eigene ``entries``."""
    cur.entries = [CurriculumEntry(e.subject, e.hours, e.double) for e in effective_entries(school, cur)]
    cur.base, cur.deltas = None, []


def delete_curriculum_keep_derived(school: School, curriculum_id: str) -> None:
    """Stundentafel entfernen: Jahrgänge verlieren den Verweis, abgeleitete Tafeln werden eigenständig."""
    for c in school.curricula:
        if c.base == curriculum_id:
            materialize(school, c)
    for p in school.grade_profiles:
        if p.curriculum == curriculum_id:
            p.curriculum = None
    school.curricula = [c for c in school.curricula if c.id != curriculum_id]


def derive_curriculum(school: School, new_id: str, name: str, base_id: str,
                      target: Optional[list[CurriculumEntry]] = None) -> Curriculum:
    """Neue Stundentafel „wie ``base`` plus Abweichungen“ anlegen. ``target`` = gewünschte wirksame Zeilen (sonst
    gleich der Basis, ohne Abweichung)."""
    from .planning import deltas_for
    base = school.index("curricula")[base_id]
    cur = Curriculum(id=new_id, name=name, base=base_id)
    if target is not None:
        cur.deltas = deltas_for(effective_entries(school, base), target)
    school.curricula.append(cur)
    return cur


def validate_profile(school: School, item: GradeProfile, grade_min: int, grade_max: int) -> list[str]:
    errs = []
    if not (item.name or "").strip():
        errs.append("Name des Jahrgangs fehlt")
    if item.grade is not None and not grade_min <= item.grade <= grade_max:
        errs.append(f"Klassenstufe muss zwischen {grade_min} und {grade_max} liegen oder leer sein")
    if item.color and not HEX_COLOR.match(item.color):
        errs.append("Farbe bitte als #rrggbb angeben")
    if item.curriculum and item.curriculum not in school.index("curricula"):
        errs.append(f"Stundentafel „{item.curriculum}“ existiert nicht")
    for key, limit in (("name", 120), ("short", 20), ("description", 500), ("department", 80)):
        if len(getattr(item, key) or "") > limit:
            errs.append(f"{key}: höchstens {limit} Zeichen")
    return errs


def curriculum_base_errors(school: School, item: Curriculum) -> list[str]:
    """Basis muss existieren, darf nicht die Tafel selbst sein und keinen Kreis bilden."""
    if not item.base:
        return []
    if item.base == item.id:
        return ["Eine Stundentafel kann nicht von sich selbst abgeleitet sein"]
    idx = {c.id: c for c in school.curricula}
    if item.base not in idx:
        return [f"Basis-Stundentafel „{item.base}“ existiert nicht"]
    seen = {item.id}
    nxt: Optional[str] = item.base
    while nxt:
        if nxt in seen:
            return ["Die Ableitung bildet einen Kreis"]
        seen.add(nxt)
        cur = idx.get(nxt)
        nxt = cur.base if cur is not None else None
    return []
