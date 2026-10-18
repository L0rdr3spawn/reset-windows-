"""Jahrgänge (Stammdaten → Jahrgänge) und Klassenstufen.

**Jahrgänge** (``GradeProfile``, Logik in ``schulmanager/grade_profiles.py``) sind frei definierbar – „5“,
„5 Informatik“, „Montessori“, „GIF 26“ – mit eigener oder abgeleiteter Stundentafel; Klassen werden einem Jahrgang
zugeordnet. Ändern dürfen ``masterdata.edit`` oder ``timetable.edit``; alles läuft über ``mutate`` (Verlauf, Undo,
Audit).

* ``GET    /grade-profiles`` – Jahrgänge mit Klassen und Zahlen, nicht zugeordnete Klassen je Stufe, Stundentafeln,
  ausstehende Umstellung alter Dokumente
* ``GET    /grade-profiles/matrix`` – Stundentafeln als Matrix Fächer × Tafeln (wirksame Zeilen, Soll/Ist)
* ``GET    /grade-profiles/migration`` / ``POST …`` – Vorschau bzw. Umstellung „Klassenstufen-Nummern → Jahrgänge“
* ``POST   /grade-profiles`` – Jahrgang anlegen (Stundentafel wählen, neu oder von einer Basis ableiten, Klassen)
* ``PUT    /grade-profiles/{id}`` – Jahrgang ändern
* ``POST   /grade-profiles/assign`` – Klassen einem Jahrgang zuordnen (``profile_id`` null = lösen)
* ``GET    /grade-profiles/{id}/impact`` – Folgen des Löschens
* ``DELETE /grade-profiles/{id}?move_to=&delete_curriculum=`` – löschen, Klassen umziehen
* ``GET    /curricula/{id}/impact``, ``GET /subjects/{id}/impact`` – Folgen des Löschens einer Tafel bzw. eines Fachs
* ``POST   /curricula/derive`` – Stundentafel von einer Basis ableiten

**Klassenstufen** (Zahl ``grade`` an den Klassen) bleiben für Klassen-Massenanlage und -Löschung:

* ``GET  /grade-levels`` – Stufen mit Klassen, Zahlen, Stundentafel und Problemen
* ``GET  /grade-levels/impact?classes=a,b`` – was an den Klassen hängt (Schüler, Kurse, Stunden …)
* ``POST /grade-levels/{grade}/classes`` – mehrere Klassen anlegen (``masterdata.edit``; ``profile`` = Jahrgang)
* ``POST /grade-levels/delete-classes`` – Klassen löschen, Schüler/innen optional verschieben (``masterdata.edit``)
* ``PUT  /grade-levels/{grade}/curriculum`` – Altbestand: Stundentafel der Stufe festlegen (``timetable.edit``)
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from schulmanager import grade_profiles as gp
from schulmanager.models import Curriculum, CurriculumEntry, GradeProfile, School, SchoolClass
from schulmanager.server.deps import AuthUser, current_user, require

from .features_common import check_id, has, mutate, need, new_id, snapshot
from .features_data import GRADE_MAX, GRADE_MIN, cascade_delete, validate_item

router = APIRouter(tags=["Klassenstufen"])

VIEW_PERMS = ("masterdata.edit", "timetable.edit", "plans.read_all")
WRITE_PERMS = ("masterdata.edit", "timetable.edit")
MAX_NEW_CLASSES = 30


def _natural(value: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", value or ""))


def _need_view(user) -> None:
    if not any(has(user, p) for p in VIEW_PERMS):
        raise HTTPException(403, "Keine Berechtigung für die Klassenstufen")


def _need_write(user) -> None:
    if not any(has(user, p) for p in WRITE_PERMS):
        raise HTTPException(403, "Jahrgänge ändern Stammdaten oder Stundenplanung")


def _hours(cur, school: School) -> int:
    from schulmanager.planning import curriculum_hours
    return curriculum_hours(school, cur)


def _impact_one(school: School, cls: SchoolClass, others: Optional[set[str]] = None) -> dict:
    """Folgen des Löschens einer Klasse. ``others`` = weitere Klassen, die gleichzeitig gelöscht werden."""
    gone_with = (others or set()) | {cls.id}
    owned = [c for c in school.courses if cls.id in c.classes and set(c.classes) <= gone_with]
    shared = [c for c in school.courses if cls.id in c.classes and not set(c.classes) <= gone_with]
    owned_ids = {c.id for c in owned}
    return {
        "id": cls.id, "name": cls.name, "grade": cls.grade,
        "students": sum(1 for s in school.students if s.class_id == cls.id),
        "courses_deleted": len(owned), "courses_shared": len(shared),
        "lessons": sum(1 for le in school.lessons if le.course_id in owned_ids),
        "curricula": [c.id for c in school.curricula if cls.id in c.classes],
        "absences": sum(1 for a in school.absences if a.kind == "class" and a.ref == cls.id),
    }


def _impact(school: School, ids: list[str]) -> dict:
    classes = school.index("classes")
    unknown = [i for i in ids if i not in classes]
    if unknown:
        raise HTTPException(404, f"Klasse „{unknown[0]}“ nicht gefunden")
    group = set(ids)
    rows = [_impact_one(school, classes[i], group) for i in ids]
    keys = ("students", "courses_deleted", "courses_shared", "lessons", "absences")
    return {"classes": rows, "totals": {k: sum(r[k] for r in rows) for k in keys}}


@router.get("/grade-levels")
def list_grade_levels(user: AuthUser = Depends(current_user)):
    """Alle Klassenstufen mit ihren Klassen. Eine Stufe ohne Klasse erscheint, wenn eine Stundentafel sie nennt."""
    _need_view(user)
    school = snapshot()[1]
    from schulmanager.planning import resolve_curricula

    res = resolve_curricula(school)
    curricula = {c.id: c for c in school.curricula}
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
    by_grade: dict[int, list[SchoolClass]] = defaultdict(list)
    for cls in school.classes:
        by_grade[cls.grade].append(cls)
    for cur in school.curricula:
        if not cur.classes:
            for g in cur.grades:
                by_grade.setdefault(g, [])
    levels = []
    for grade in sorted(by_grade):
        rows = []
        for cls in sorted(by_grade[grade], key=lambda c: _natural(c.name or c.id)):
            r = res.get(cls.id, {})
            cur = curricula.get(r.get("curriculum") or "")
            t = teachers.get(cls.class_teacher) if cls.class_teacher else None
            site = sites.get(cls.site)
            rows.append({
                "id": cls.id, "name": cls.name, "site": cls.site, "site_name": site.name if site else "",
                "students": n_students.get(cls.id) or int(cls.students or 0),
                "students_listed": n_students.get(cls.id, 0),
                "class_teacher": {"id": t.id, "name": t.name} if t else None,
                "curriculum_id": cur.id if cur else None, "curriculum_name": cur.name if cur else None,
                "curriculum_source": r.get("source"), "curriculum_conflict": bool(r.get("conflict")),
                "courses": n_courses.get(cls.id, 0), "open_courses": open_courses.get(cls.id, 0),
            })
        shared = [c for c in school.curricula if not c.classes and grade in c.grades]
        levels.append({
            "grade": grade, "classes": rows,
            "students": sum(r["students"] for r in rows),
            "courses": sum(r["courses"] for r in rows), "open_courses": sum(r["open_courses"] for r in rows),
            "curriculum": ({"id": shared[0].id, "name": shared[0].name, "hours": _hours(shared[0], school)}
                           if len(shared) == 1 else None),
            "curriculum_conflict": [c.id for c in shared] if len(shared) > 1 else [],
            "without_curriculum": [r["id"] for r in rows if not r["curriculum_id"] and not r["curriculum_conflict"]],
        })
    return {
        "grade_min": GRADE_MIN, "grade_max": GRADE_MAX, "levels": levels,
        "curricula": [{"id": c.id, "name": c.name, "hours": _hours(c, school), "for_classes": bool(c.classes)}
                      for c in sorted(school.curricula, key=lambda c: _natural(c.name))],
        "can_edit": has(user, "masterdata.edit"), "can_plan": has(user, "timetable.edit"),
    }


@router.get("/grade-levels/impact")
def classes_impact(classes: str = Query(..., min_length=1, max_length=2000),
                   user: AuthUser = Depends(current_user)):
    """Folgen des Löschens: je Klasse Schüler/innen, Kurse (mit der Klasse gelöscht bzw. nur gekürzt), Stunden."""
    _need_view(user)
    ids = [x for x in dict.fromkeys(i.strip() for i in classes.split(",")) if x]
    return _impact(snapshot()[1], ids)


class NewClassesIn(BaseModel):
    names: list[str] = Field(min_length=1, max_length=MAX_NEW_CLASSES)
    copy_from: Optional[str] = Field(None, max_length=64)
    students: int = Field(25, ge=0, le=60)
    create_courses: bool = True
    #: Jahrgang, dem die neuen Klassen gehören (bestimmt ihre Stundentafel)
    profile: Optional[str] = Field(None, max_length=64)


@router.post("/grade-levels/{grade}/classes", status_code=201)
def create_classes(grade: int, body: NewClassesIn, user: AuthUser = Depends(require("masterdata.edit"))):
    """Mehrere Klassen einer Stufe in einem Rutsch anlegen (Kürzel = Name, z. B. „5a“). Standort, Stunden pro Tag
    und Unterrichtstage kommen von ``copy_from`` bzw. der ersten Klasse der Stufe. Gilt für die Stufe eine
    Stundentafel, entstehen die Kurse der neuen Klassen gleich mit."""
    if not GRADE_MIN <= grade <= GRADE_MAX:
        raise HTTPException(422, f"Klassenstufe muss zwischen {GRADE_MIN} und {GRADE_MAX} liegen")
    names = [check_id(n) for n in body.names]
    if len(set(n.lower() for n in names)) != len(names):
        raise HTTPException(422, "Ein Kürzel steht doppelt in der Liste")

    def fn(school: School):
        from schulmanager.planning import rebuild_class_courses

        classes = school.index("classes")
        clash = [n for n in names if n in classes]
        if clash:
            raise HTTPException(409, f"Klasse „{clash[0]}“ existiert bereits")
        ref = classes.get(body.copy_from) if body.copy_from else None
        if body.copy_from and ref is None:
            raise HTTPException(422, f"Klasse „{body.copy_from}“ existiert nicht")
        profile = (body.profile or "").strip() or None
        if profile and profile not in school.index("grade_profiles"):
            raise HTTPException(422, f"Jahrgang „{profile}“ existiert nicht")
        if ref is None and profile:
            ref = next((c for c in school.classes if c.profile == profile), None)
        if ref is None:
            ref = next((c for c in school.classes if c.grade == grade), None)
        created, warnings, open_parts = [], [], []
        for n in names:
            cls = SchoolClass(n, n, grade, students=body.students,
                              site=ref.site if ref else (school.sites[0].id if len(school.sites) == 1 else ""),
                              max_periods_per_day=ref.max_periods_per_day if ref else min(8, school.settings.periods),
                              school_days=list(ref.school_days) if ref else [], profile=profile)
            errs = validate_item(school, "classes", cls)
            if errs:
                raise HTTPException(422, f"Klasse {n}: " + "; ".join(errs))
            school.classes.append(cls)
            created.append(n)
        if body.create_courses:
            for n in created:
                r = rebuild_class_courses(school, n)
                warnings += [w for w in r.get("warnings", []) if "keine Stundentafel" not in w]
                open_parts += r.get("open_parts", [])
        return {"created": created, "warnings": warnings, "open_parts": open_parts}

    return mutate(user, f"Klassenstufe {grade}: {len(names)} Klasse(n) angelegt ({', '.join(names)})", fn,
                  scope=["classes", "courses", "timetable", "grade_profiles"])


class DeleteClassesIn(BaseModel):
    class_ids: list[str] = Field(min_length=1, max_length=MAX_NEW_CLASSES * 3)
    #: Schüler/innen vorher in diese Klasse verschieben (statt sie mit der Klasse zu löschen)
    move_students_to: Optional[str] = Field(None, max_length=64)


@router.post("/grade-levels/delete-classes")
def delete_classes(body: DeleteClassesIn, user: AuthUser = Depends(require("masterdata.edit"))):
    """Klassen endgültig löschen: Kurse nur dieser Klassen mit ihren Stunden, Abwesenheiten und eigene Klassen-
    Stundentafeln gehen mit. Schüler/innen werden verschoben (``move_students_to``) oder ebenfalls gelöscht."""
    ids = list(dict.fromkeys(body.class_ids))
    target = body.move_students_to or None
    if target and target in ids:
        raise HTTPException(422, "Die Zielklasse für die Schüler/innen wird selbst gelöscht")

    def fn(school: School):
        classes = school.index("classes")
        unknown = [i for i in ids if i not in classes]
        if unknown:
            raise HTTPException(404, f"Klasse „{unknown[0]}“ nicht gefunden")
        if target and target not in classes:
            raise HTTPException(422, f"Zielklasse „{target}“ existiert nicht")
        impact = _impact(school, ids)
        moved = 0
        if target:
            courses = {c.id: c for c in school.courses}
            for s in school.students:
                if s.class_id in ids:
                    s.class_id = target
                    # Kurswahlen nur behalten, wenn der Kurs auch die Zielklasse hat
                    s.courses = [r for r in s.courses
                                 if (c := courses.get(r.rpartition("#")[0])) is not None and target in c.classes]
                    moved += 1
        own = {c.id for c in school.curricula if set(c.classes) & set(ids)}
        for cid in ids:
            cascade_delete(school, "classes", cid)
        school.classes = [c for c in school.classes if c.id not in ids]
        # Tafeln, die nur für die gelöschten Klassen galten (eigene Klassen-Tafeln), mit entfernen
        school.curricula = [c for c in school.curricula if not (c.id in own and not c.classes and not c.grades)]
        return {"deleted": ids, "moved_students": moved, "impact": impact["totals"]}

    return mutate(user, f"Klasse(n) {', '.join(ids)} gelöscht" + (f" (Schüler/innen → {target})" if target else ""),
                  fn, scope=["classes", "students", "courses", "curricula", "timetable"])


class GradeCurriculumIn(BaseModel):
    curriculum_id: Optional[str] = Field(None, max_length=64)


@router.put("/grade-levels/{grade}/curriculum")
def set_grade_curriculum(grade: int, body: GradeCurriculumIn, user: AuthUser = Depends(require("timetable.edit"))):
    """Stundentafel der Klassenstufe festlegen (``None`` = keine). Klassen mit eigener Klassen-Tafel behalten diese.
    Die Kurse ändern sich erst mit „Kurse erzeugen“."""
    if not GRADE_MIN <= grade <= GRADE_MAX:
        raise HTTPException(422, f"Klassenstufe muss zwischen {GRADE_MIN} und {GRADE_MAX} liegen")
    need(user, "timetable.edit")

    def fn(school: School):
        target = None
        if body.curriculum_id:
            target = school.index("curricula").get(body.curriculum_id)
            if target is None:
                raise HTTPException(404, f"Stundentafel „{body.curriculum_id}“ nicht gefunden")
            if target.classes:
                raise HTTPException(422, "Diese Stundentafel gilt für einzelne Klassen – bitte in der Stundentafel "
                                         "auf „ganze Klassenstufe“ umstellen")
        for cur in school.curricula:
            if not cur.classes and grade in cur.grades and cur is not target:
                cur.grades = [g for g in cur.grades if g != grade]
        if target is not None and grade not in target.grades:
            target.grades = sorted([*target.grades, grade])
        return {"grade": grade, "curriculum_id": target.id if target else None}

    what = f"Stundentafel „{body.curriculum_id}“" if body.curriculum_id else "keine Stundentafel"
    return mutate(user, f"Klassenstufe {grade}: {what}", fn, scope=["curricula", "courses"])


# =================================================================== Jahrgänge
def _profile_or_404(school: School, profile_id: str) -> GradeProfile:
    prof = school.index("grade_profiles").get(profile_id)
    if prof is None:
        raise HTTPException(404, f"Jahrgang „{profile_id}“ nicht gefunden")
    return prof


def _curriculum_or_404(school: School, curriculum_id: str) -> Curriculum:
    cur = school.index("curricula").get(curriculum_id)
    if cur is None:
        raise HTTPException(404, f"Stundentafel „{curriculum_id}“ nicht gefunden")
    return cur


def _profiles_out(school: School, user) -> dict:
    from schulmanager.legacy import grade_profiles_preview
    rows = gp.profile_rows(school)
    migration = grade_profiles_preview(school)
    return {
        "grade_min": GRADE_MIN, "grade_max": GRADE_MAX,
        "profiles": [r for r in rows if "_unassigned" not in r],
        "unassigned": [{"grade": r["_unassigned"], "classes": r["classes"]} for r in rows if "_unassigned" in r],
        "curricula": [{"id": c.id, "name": c.name, "hours": _hours(c, school), "for_classes": bool(c.classes),
                       "base": c.base, "grades": list(c.grades)}
                      for c in sorted(school.curricula, key=lambda c: gp.natural_key(c.name))],
        "migration": {"pending": migration["pending"],
                      "profiles": len([p for p in migration["profiles"] if not p["exists"]]),
                      "classes": migration["classes"]},
        "can_edit": has(user, "masterdata.edit"), "can_plan": has(user, "timetable.edit"),
        "can_write": any(has(user, p) for p in WRITE_PERMS),
    }


@router.get("/grade-profiles")
def list_profiles(user: AuthUser = Depends(current_user)):
    """Alle Jahrgänge mit Klassen und Zahlen; Klassen ohne Jahrgang je Klassenstufe; alle Stundentafeln."""
    _need_view(user)
    return _profiles_out(snapshot()[1], user)


@router.get("/grade-profiles/matrix")
def curricula_matrix(user: AuthUser = Depends(current_user)):
    """Stundentafeln als Matrix: je Tafel die wirksamen Zeilen (auch abgeleitete), Jahrgänge, Klassen, Soll/Ist."""
    _need_view(user)
    school = snapshot()[1]
    return {"curricula": gp.curriculum_rows(school),
            "profiles": [p.to_dict() for p in sorted(school.grade_profiles, key=gp.profile_sort_key)],
            "class_names": {c.id: c.name for c in school.classes},
            "subjects": [s.to_dict() for s in school.subjects]}


@router.get("/grade-profiles/migration")
def migration_preview(user: AuthUser = Depends(current_user)):
    """Vorschau: welche Jahrgänge aus den Klassenstufen-Nummern entstehen und welche Klassen zugeordnet würden."""
    _need_view(user)
    from schulmanager.legacy import grade_profiles_preview
    return grade_profiles_preview(snapshot()[1])


@router.post("/grade-profiles/migration")
def migration_apply(user: AuthUser = Depends(current_user)):
    """Umstellung ausführen (rückgängig über den Planverlauf)."""
    _need_write(user)
    from schulmanager.legacy import migrate_grade_profiles

    def fn(school: School):
        return migrate_grade_profiles(school)

    return mutate(user, "Jahrgänge aus Klassenstufen übernommen", fn,
                  scope=["grade_profiles", "classes", "curricula"])


class CurriculumChoiceIn(BaseModel):
    """Stundentafel eines Jahrgangs: vorhandene (``id``), neue leere (``new``) oder von ``base`` abgeleitet."""
    id: Optional[str] = Field(None, max_length=64)
    new: bool = False
    base: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=120)


class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    short: str = Field("", max_length=20)
    grade: Optional[int] = Field(None, ge=GRADE_MIN, le=GRADE_MAX)
    color: str = Field("", max_length=7)
    description: str = Field("", max_length=500)
    department: str = Field("", max_length=80)
    curriculum: Optional[CurriculumChoiceIn] = None
    class_ids: Optional[list[str]] = Field(None, max_length=200)


def _resolve_curriculum(school: School, choice: Optional[CurriculumChoiceIn], prof_name: str) -> Optional[str]:
    """Wunsch der Oberfläche → Stundentafel-ID (legt bei ``new``/``base`` eine neue Tafel an)."""
    if choice is None:
        return None
    if choice.new or choice.base:
        name = (choice.name or "").strip() or f"Stundentafel {prof_name}"
        cid = new_id([c.id for c in school.curricula], "ST")
        if choice.base:
            _curriculum_or_404(school, choice.base)
            gp.derive_curriculum(school, cid, name, choice.base)
        else:
            school.curricula.append(Curriculum(id=cid, name=name))
        return cid
    if choice.id:
        return _curriculum_or_404(school, choice.id).id
    return None


def _apply_profile_fields(prof: GradeProfile, body: ProfileIn) -> None:
    prof.name = body.name.strip()
    prof.short = body.short.strip()
    prof.grade = body.grade
    prof.color = body.color.strip()
    prof.description = body.description.strip()
    prof.department = body.department.strip()


def _check_profile(school: School, prof: GradeProfile) -> None:
    errs = validate_item(school, "grade_profiles", prof)
    if errs:
        raise HTTPException(422, "; ".join(errs))


@router.post("/grade-profiles", status_code=201)
def create_profile(body: ProfileIn, user: AuthUser = Depends(current_user)):
    """Jahrgang anlegen – mit vorhandener, neuer oder abgeleiteter Stundentafel und optional gleich den Klassen."""
    _need_write(user)

    def fn(school: School):
        wish = (body.short or body.name).strip()
        existing = {p.id for p in school.grade_profiles}
        try:
            pid = check_id(wish)                 # Kurzname bzw. Name als sprechende ID („5IF“), sonst JGn
        except HTTPException:
            pid = ""
        if not pid or pid in existing:
            pid = new_id(existing, "JG")
        prof = GradeProfile(id=pid, name=body.name.strip())
        _apply_profile_fields(prof, body)
        prof.curriculum = _resolve_curriculum(school, body.curriculum, prof.name)
        _check_profile(school, prof)
        school.grade_profiles.append(prof)
        if body.class_ids:
            unknown = [c for c in body.class_ids if c not in school.index("classes")]
            if unknown:
                raise HTTPException(422, f"Klasse „{unknown[0]}“ existiert nicht")
            gp.assign_classes(school, body.class_ids, pid)
        return {**prof.to_dict(), "classes": body.class_ids or []}

    return mutate(user, f"Jahrgang „{body.name.strip()}“ angelegt", fn,
                  scope=["grade_profiles", "classes", "curricula"])


@router.put("/grade-profiles/{profile_id}")
def update_profile(profile_id: str, body: ProfileIn, user: AuthUser = Depends(current_user)):
    """Jahrgang ändern (Name, Kurzname, Stufe, Farbe, Beschreibung, Abteilung, Stundentafel)."""
    _need_write(user)

    def fn(school: School):
        prof = _profile_or_404(school, profile_id)
        _apply_profile_fields(prof, body)
        if body.curriculum is not None:
            prof.curriculum = _resolve_curriculum(school, body.curriculum, prof.name)
        _check_profile(school, prof)
        return prof.to_dict()

    return mutate(user, f"Jahrgang {profile_id} geändert", fn, scope=["grade_profiles", "curricula", "courses"])


class AssignIn(BaseModel):
    class_ids: list[str] = Field(min_length=1, max_length=200)
    profile_id: Optional[str] = Field(None, max_length=64)


@router.post("/grade-profiles/assign")
def assign_classes(body: AssignIn, user: AuthUser = Depends(current_user)):
    """Klassen einem Jahrgang zuordnen (auch nachträglich, auch aus einem anderen Jahrgang); ``profile_id`` null
    löst die Zuordnung. Die Kurse ändern sich erst mit „Kurse erzeugen“."""
    _need_write(user)

    def fn(school: School):
        if body.profile_id:
            _profile_or_404(school, body.profile_id)
        unknown = [c for c in body.class_ids if c not in school.index("classes")]
        if unknown:
            raise HTTPException(404, f"Klasse „{unknown[0]}“ nicht gefunden")
        changed = gp.assign_classes(school, body.class_ids, body.profile_id)
        return {"changed": changed, "profile_id": body.profile_id}

    what = f"Jahrgang {body.profile_id}" if body.profile_id else "kein Jahrgang"
    return mutate(user, f"Klasse(n) {', '.join(body.class_ids)} → {what}", fn,
                  scope=["grade_profiles", "classes", "curricula", "courses"])


@router.get("/grade-profiles/{profile_id}/impact")
def profile_impact(profile_id: str, user: AuthUser = Depends(current_user)):
    """Folgen des Löschens: Klassen, Stundentafel-Kurse und Stunden, Stundentafel, andere Jahrgänge als Ziel."""
    _need_view(user)
    school = snapshot()[1]
    _profile_or_404(school, profile_id)
    return gp.profile_impact(school, profile_id)


@router.delete("/grade-profiles/{profile_id}")
def delete_profile(profile_id: str, move_to: Optional[str] = Query(None, max_length=64),
                   delete_curriculum: bool = Query(False), user: AuthUser = Depends(current_user)):
    """Jahrgang löschen; Klassen wandern nach ``move_to`` oder verlieren die Zuordnung. ``delete_curriculum``
    entfernt die nur hier verwendete Stundentafel mit (abgeleitete Tafeln werden eigenständig)."""
    _need_write(user)
    if move_to and move_to == profile_id:
        raise HTTPException(422, "Der Ziel-Jahrgang wird selbst gelöscht")

    def fn(school: School):
        prof = _profile_or_404(school, profile_id)
        if move_to:
            _profile_or_404(school, move_to)
        res = gp.delete_profile(school, profile_id, move_to or None, delete_curriculum)
        res["name"] = prof.name
        return res

    return mutate(user, f"Jahrgang {profile_id} gelöscht" + (f" (Klassen → {move_to})" if move_to else ""), fn,
                  scope=["grade_profiles", "classes", "curricula", "courses"])


# =================================================================== Stundentafeln und Fächer: Folgen, Ableitung
@router.get("/curricula/{curriculum_id}/impact")
def curriculum_impact(curriculum_id: str, user: AuthUser = Depends(current_user)):
    """Folgen des Löschens einer Stundentafel: Jahrgänge, Klassen, Kurse, Stunden, abgeleitete Tafeln."""
    _need_view(user)
    school = snapshot()[1]
    _curriculum_or_404(school, curriculum_id)
    return gp.curriculum_impact(school, curriculum_id)


@router.get("/subjects/{subject_id}/impact")
def subject_impact(subject_id: str, user: AuthUser = Depends(current_user)):
    """Folgen des Löschens eines Fachs: Stundentafeln, Kurse, Stunden, Lehrkräfte, Klausuren."""
    _need_view(user)
    school = snapshot()[1]
    if subject_id not in school.index("subjects"):
        raise HTTPException(404, f"Fach „{subject_id}“ nicht gefunden")
    return gp.subject_impact(school, subject_id)


class DeriveIn(BaseModel):
    base: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    #: gewünschte wirksame Zeilen (None = genau wie die Basis)
    entries: Optional[list[dict]] = None
    profile_id: Optional[str] = Field(None, max_length=64)


@router.post("/curricula/derive", status_code=201)
def derive_curriculum(body: DeriveIn, user: AuthUser = Depends(require("timetable.edit"))):
    """Stundentafel „wie Basis, plus Abweichungen“ anlegen; optional gleich einem Jahrgang zuordnen."""
    def fn(school: School):
        _curriculum_or_404(school, body.base)
        target = None
        if body.entries is not None:
            target = []
            for e in body.entries:
                subj = str(e.get("subject") or "")
                if subj not in school.index("subjects"):
                    raise HTTPException(422, f"Fach „{subj}“ existiert nicht")
                target.append(CurriculumEntry(subj, int(e.get("hours") or 0), bool(e.get("double"))))
        cid = new_id([c.id for c in school.curricula], "ST")
        cur = gp.derive_curriculum(school, cid, body.name.strip(), body.base, target)
        errs = validate_item(school, "curricula", cur)
        if errs:
            raise HTTPException(422, "; ".join(errs))
        if body.profile_id:
            _profile_or_404(school, body.profile_id).curriculum = cid
        return cur.to_dict()

    return mutate(user, f"Stundentafel „{body.name.strip()}“ von {body.base} abgeleitet", fn,
                  scope=["curricula", "grade_profiles"])
