"""Vorbereitung der Planung: Stundentafel -> Kurse, Lehrerzuweisung.

Zuordnung Stundentafel → Klasse (``resolve_curricula``), in dieser Reihenfolge:

1. eine Tafel, die die Klasse unter ``classes`` nennt (eigene Klassen-Tafel);
2. die Tafel des Jahrgangs der Klasse (``SchoolClass.profile`` → ``GradeProfile.curriculum``);
3. Altbestand: eine Tafel **ohne** ``classes``, deren ``grades`` die Klassenstufen-Nummer enthält
   (``legacy.migrate_grade_profiles`` macht daraus Jahrgänge).

Gelten auf derselben Stufe mehrere Tafeln, ist das ein **Konflikt** – die Kurse der Klasse bleiben dann unverändert.
Abgeleitete Tafeln (``Curriculum.base`` + ``deltas``) werden über ``effective_entries`` aufgelöst.
"""
from __future__ import annotations

import copy
from collections import defaultdict

from .models import Course, CoursePart, Curriculum, CurriculumEntry, School

#: Felder eines Stundentafel-Kurses, die nach einer manuellen Änderung erhalten bleiben (``Course.pinned``)
PINNABLE = ("hours", "double", "weeks", "label", "parts")
PIN_LABELS = {"hours": "Wochenstunden", "double": "Doppelstunde", "weeks": "Wochen", "label": "Bezeichnung",
              "parts": "Kursteile/Räume"}


def effective_entries(school: School, cur: Curriculum | None,
                      _seen: frozenset[str] = frozenset()) -> list[CurriculumEntry]:
    """Wirksame Zeilen einer Stundentafel: eigene ``entries`` – oder, mit ``base``, die wirksamen Zeilen der Basis
    plus ``deltas`` (Stunden addiert, Fächer mit ≤ 0 Stunden fallen weg, neue Fächer kommen hinzu, ``double`` ist der
    Zielwert). Fehlt die Basis oder bildet sie einen Kreis, zählen die eigenen ``entries``."""
    if cur is None:
        return []
    if not cur.base or cur.id in _seen:
        return list(cur.entries)
    base = school.index("curricula").get(cur.base)
    if base is None:
        return list(cur.entries)
    merged: dict[str, CurriculumEntry] = {}
    for e in effective_entries(school, base, _seen | {cur.id}):
        if e.subject:
            merged[e.subject] = CurriculumEntry(e.subject, e.hours, e.double)
    for d in cur.deltas:
        if not d.subject:
            continue
        prev = merged.get(d.subject)
        hours = (prev.hours if prev else 0) + d.hours
        if hours <= 0:
            merged.pop(d.subject, None)
        else:
            merged[d.subject] = CurriculumEntry(d.subject, hours, d.double)
    return list(merged.values())


def curriculum_hours(school: School, cur: Curriculum | None) -> int:
    return sum(e.hours for e in effective_entries(school, cur))


def deltas_for(base_entries: list[CurriculumEntry], target: list[CurriculumEntry]) -> list[CurriculumEntry]:
    """Abweichungen, die aus ``base_entries`` genau ``target`` machen (Editor: Zielwerte → ``deltas``)."""
    base = {e.subject: e for e in base_entries if e.subject}
    out: list[CurriculumEntry] = []
    for t in target:
        if not t.subject:
            continue
        b = base.get(t.subject)
        if b is None:
            out.append(CurriculumEntry(t.subject, t.hours, t.double))
        elif (b.hours, b.double) != (t.hours, t.double):
            out.append(CurriculumEntry(t.subject, t.hours - b.hours, t.double))
    wanted = {t.subject for t in target}
    for subj, b in base.items():
        if subj not in wanted:
            out.append(CurriculumEntry(subj, -b.hours, b.double))
    return out


def _candidates(school: School, cls) -> tuple[list[Curriculum], str | None]:
    by_class = [cur for cur in school.curricula if cls.id in cur.classes]
    if by_class:
        return by_class, "class"
    if cls.profile:
        prof = school.index("grade_profiles").get(cls.profile)
        if prof is not None and prof.curriculum:
            cur = school.index("curricula").get(prof.curriculum)
            if cur is not None:
                return [cur], "profile"
    by_grade = [cur for cur in school.curricula if not cur.classes and cls.grade in cur.grades]
    return by_grade, ("grade" if by_grade else None)


def curriculum_for_class(school: School, class_id: str) -> Curriculum | None:
    """Gültige Stundentafel der Klasse (Klasse vor Jahrgang). Bei einem Konflikt die erste – Aufrufer, die
    Konflikte melden müssen, nutzen ``resolve_curricula``. KeyError bei unbekannter Klasse."""
    cls = school.index("classes")[class_id]
    found, _ = _candidates(school, cls)
    return found[0] if found else None


def resolve_curricula(school: School) -> dict[str, dict]:
    """Je Klasse ``{"curriculum": id|None, "source": "class"|"profile"|"grade"|None, "candidates": [ids],
    "conflict": bool}`` – bei ``conflict`` ist ``curriculum`` None."""
    out: dict[str, dict] = {}
    for cls in school.classes:
        found, source = _candidates(school, cls)
        ids = [c.id for c in found]
        out[cls.id] = {"curriculum": ids[0] if len(ids) == 1 else None, "source": source, "candidates": ids,
                       "conflict": len(ids) > 1}
    return out


def curriculum_conflicts(school: School, only: str | None = None) -> list[dict]:
    """Überschneidungen gruppiert: ``[{"curricula": [ids], "classes": [ids], "source"}]`` (optional nur
    Gruppen, an denen die Tafel ``only`` beteiligt ist)."""
    groups: dict[tuple, list[str]] = defaultdict(list)
    for cid, info in resolve_curricula(school).items():
        if info["conflict"] and (only is None or only in info["candidates"]):
            groups[(tuple(info["candidates"]), info["source"])].append(cid)
    return [{"curricula": list(k[0]), "source": k[1], "classes": v} for k, v in groups.items()]


def curriculum_overview(school: School) -> dict:
    """Für den Editor: je Tafel die Klassen, für die sie gilt (bzw. im Konflikt steht), und Klassen ohne Tafel."""
    names = {c.id: c.name for c in school.classes}
    res = resolve_curricula(school)
    per: dict[str, dict] = {c.id: {"classes": [], "conflicts": [], "via_grade": [], "via_profile": [],
                                   "shadowed": [], "profiles": []} for c in school.curricula}
    for p in school.grade_profiles:
        if p.curriculum in per:
            per[p.curriculum]["profiles"].append(p.id)
    for cid, info in res.items():
        for cur_id in info["candidates"]:
            entry = per[cur_id]
            (entry["conflicts"] if info["conflict"] else entry["classes"]).append(cid)
            if info["source"] == "grade":
                entry["via_grade"].append(cid)
            elif info["source"] == "profile":
                entry["via_profile"].append(cid)
    # Jahrgangs-/Stufen-Tafeln, die für eine Klasse wegen einer Klassen-Tafel nicht gelten (nur Info)
    profiles = school.index("grade_profiles")
    for cls in school.classes:
        if res[cls.id]["source"] == "class":
            prof = profiles.get(cls.profile) if cls.profile else None
            for cur in school.curricula:
                if (prof is not None and prof.curriculum == cur.id) or (not cur.classes and cls.grade in cur.grades):
                    per[cur.id]["shadowed"].append(cls.id)
    return {"curricula": per, "classes": res, "class_names": names,
            "without": [cid for cid, info in res.items() if info["source"] is None],
            "conflicts": curriculum_conflicts(school)}


def _part_key(parts: list[CoursePart]) -> list[dict]:
    """Kursteile ohne Lehrkraft (die Lehrkraft bleibt ohnehin erhalten) – für den Vergleich."""
    return [{k: v for k, v in p.to_dict().items() if k != "teacher"} for p in parts]


def changed_fields(old: Course, new: Course) -> list[str]:
    """Welche ``PINNABLE``-Felder unterscheiden sich (Kurs-Editor → ``Course.pinned``)."""
    out = []
    for f in PINNABLE:
        if f == "parts":
            if _part_key(old.parts) != _part_key(new.parts):
                out.append(f)
        elif getattr(old, f) != getattr(new, f):
            out.append(f)
    return out


def _names(school: School, ids) -> str:
    idx = school.index("classes")
    return ", ".join(idx[i].name if i in idx else i for i in ids)


def rebuild_courses(school: School, reset_manual: bool = False) -> dict:
    """Erzeugt für jede Klasse Kurse aus ihrer Stundentafel und liefert einen Bericht.

    * Vorhandene manuelle/Untis-Kurse derselben Klasse und desselben Fachs werden angerechnet (kein
      Doppelunterricht).
    * Kurse aus einem früheren Lauf (``origin == "curriculum"``) werden neu erzeugt; die Lehrkraft von Teil 0
      bleibt, im Kurs-Editor geänderte Felder (``Course.pinned``) bleiben erhalten – außer ``reset_manual``.
    * Klassen mit mehreren gleichrangigen Tafeln (Konflikt) behalten ihre bisherigen Kurse unverändert.
    * Gleiches Fach mehrfach in einer Tafel (Altbestand) wird zusammengefasst; Kurs-IDs sind eindeutig.

    Bericht: ``warnings``, ``conflicts`` (wie ``curriculum_conflicts``), ``created``/``removed`` (IDs),
    ``changed`` (``[{id,label,fields}]``), ``kept`` (``[{id,label,fields,labels}]`` = eigene Anpassungen),
    ``replan_needed``. Mutiert ``school.courses``.
    """
    warnings: list[str] = []
    previous = {c.id: c for c in school.courses if c.origin == "curriculum"}
    manual = [c for c in school.courses if c.origin != "curriculum"]
    taken = {c.id for c in manual}
    subjects = school.index("subjects")
    covered: dict[tuple[str, str], float] = defaultdict(float)
    has_manual: set[str] = set()
    from .weeks import Horizon
    hz = Horizon(school) if any(c.weeks or c.rhythm for c in manual) else None
    for c in manual:
        # U-52: ein Kurs nur in einigen Wochen des Schuljahres zählt anteilig (jede 2. Woche = halbe Stunden)
        share = (len(hz.spec_members(c)) / max(1, len(hz))) if hz is not None and (c.weeks or c.rhythm) else 1.0
        for cid in c.classes:
            has_manual.add(cid)
            for subj in {p.subject for p in c.parts}:
                covered[(cid, subj)] += c.hours * share
    resolved = resolve_curricula(school)
    curricula = school.index("curricula")
    new_courses: list[Course] = []
    kept: list[dict] = []
    without: list[str] = []
    empty: dict[str, list[str]] = defaultdict(list)
    unknown: dict[str, set[str]] = defaultdict(set)
    doubled: dict[str, set[str]] = defaultdict(set)
    conflict_classes: set[str] = set()
    for cls in school.classes:
        info = resolved[cls.id]
        if info["conflict"]:
            conflict_classes.add(cls.id)
            continue
        cur = curricula.get(info["curriculum"]) if info["curriculum"] else None
        if cur is None:
            without.append(cls.id)
            continue
        entries: dict[str, list] = {}
        for e in effective_entries(school, cur):
            if not e.subject:
                continue
            if e.subject not in subjects:
                unknown[cur.id].add(e.subject)
                continue
            if e.subject in entries:
                doubled[cur.id].add(e.subject)
                entries[e.subject][0] += e.hours
                entries[e.subject][1] = entries[e.subject][1] or e.double
            else:
                entries[e.subject] = [e.hours, e.double]
        made = 0
        for subj, (total, double) in entries.items():
            hours = int(total - covered[(cls.id, subj)] + 0.5)
            if hours <= 0:
                continue
            cid = f"{cls.id}-{subj}"
            if cid in taken:                 # gleiche ID wie ein manueller Kurs → eindeutige Variante
                n = 2
                while f"{cid}-{n}" in taken:
                    n += 1
                cid = f"{cid}-{n}"
            taken.add(cid)
            old = previous.get(cid)
            course = Course(id=cid, classes=[cls.id], hours=hours, double=double,
                            parts=[CoursePart(subject=subj, teacher=old.parts[0].teacher if old and old.parts
                                              else None)],
                            label=f"{subj} {cls.name}", origin="curriculum")
            pins = [] if reset_manual or old is None else [f for f in getattr(old, "pinned", []) if f in PINNABLE]
            for f in pins:
                setattr(course, f, copy.deepcopy(getattr(old, f)))
            if "weeks" in pins:
                course.rhythm = copy.deepcopy(old.rhythm)
            course.pinned = pins
            if pins:
                kept.append({"id": cid, "label": course.label or cid, "fields": pins,
                             "labels": [PIN_LABELS[f] for f in pins], "curriculum_hours": hours})
            new_courses.append(course)
            made += 1
        if not made and cls.id not in has_manual:
            empty[cur.id].append(cls.id)
    # Konfliktklassen: bisherige Stundentafel-Kurse unverändert übernehmen
    for c in previous.values():
        if c.classes and all(x in conflict_classes for x in c.classes) and c.id not in taken:
            taken.add(c.id)
            new_courses.append(c)
    conflicts = curriculum_conflicts(school)
    for g in conflicts:
        names = ", ".join(curricula[i].name for i in g["curricula"] if i in curricula)
        warnings.append(f"Konflikt: für {_names(school, g['classes'])} gelten mehrere Stundentafeln ({names}) – "
                        "Kurse dieser Klassen wurden nicht geändert")
    if without:
        warnings.append(f"Ohne Stundentafel (keine Kurse erzeugt): {_names(school, without)}")
    for cur_id, cls_ids in empty.items():
        warnings.append(f"Stundentafel „{curricula[cur_id].name}“ enthält keine Fächer mit Wochenstunden – "
                        f"keine Kurse für {_names(school, cls_ids)}")
    for cur_id, subj in unknown.items():
        warnings.append(f"Stundentafel „{curricula[cur_id].name}“: Fach {', '.join(sorted(subj))} existiert "
                        "nicht (übersprungen)")
    for cur_id, subj in doubled.items():
        warnings.append(f"Stundentafel „{curricula[cur_id].name}“: Fach {', '.join(sorted(subj))} mehrfach "
                        "eingetragen – Stunden zusammengefasst")
    school.courses = manual + new_courses
    new_ids = {c.id for c in new_courses}
    changed = []
    for c in new_courses:
        old = previous.get(c.id)
        if old is None or old is c:
            continue
        fields = [f for f in ("hours", "double", "weeks", "rhythm", "label") if getattr(old, f) != getattr(c, f)]
        if [p.to_dict() for p in old.parts] != [p.to_dict() for p in c.parts]:
            fields.append("parts")
        if fields:
            changed.append({"id": c.id, "label": c.label or c.id, "fields": fields})
    created = [c.id for c in new_courses if c.id not in previous]
    removed = [cid for cid in previous if cid not in new_ids]
    return {"warnings": warnings, "conflicts": conflicts, "created": created, "removed": removed,
            "changed": changed, "kept": kept,
            "replan_needed": bool(created or removed or any(set(x["fields"]) - {"label"} for x in changed))}


def build_courses_from_curricula(school: School, reset_manual: bool = False) -> list[str]:
    """Kurse aus den Stundentafeln erzeugen (siehe ``rebuild_courses``); gibt nur die Warnungen zurück."""
    return rebuild_courses(school, reset_manual)["warnings"]


def _class_slots(school: School, class_ids: list[str], classes: dict, real_week: int) -> frozenset[tuple[int, int]]:
    """Die ``(Tag, Stunde)``, an denen alle Klassen eines Kurses in der laufenden Woche ``real_week`` Unterricht haben
    können (Unterrichtstage der Klassen, Sperren)."""
    from .calendar_utils import class_days
    st = school.settings
    days = set(range(7))
    for cid in class_ids:
        days &= set(class_days(school, classes.get(cid)))
    slots = set()
    for d in sorted(days):
        for p in range(st.periods):
            ok = True
            for cid in class_ids:
                cls = classes.get(cid)
                if cls is None:
                    continue
                if p >= cls.max_periods_per_day or any(r.matches(real_week, d, p) for r in cls.unavailable):
                    ok = False
                    break
            if ok:
                slots.add((d, p))
    return frozenset(slots)


def teacher_course_capacity(school: School, course, teacher, classes: dict | None = None,
                            _cache: dict | None = None) -> int:
    """Kleinste Anzahl gemeinsamer freier Stunden (Klassen des Kurses ∩ Verfügbarkeit der Lehrkraft) je
    Wochenvariante des Kurses. Ist sie kleiner als ``course.hours``, kann die Lehrkraft den Kurs nicht halten
    (Zeitfenster/Sperrzeiten)."""
    from .weeks import PlanWeeks
    classes = classes or school.index("classes")
    key = tuple(course.classes)
    cache = _cache if _cache is not None else {}
    if "pw" not in cache:
        cache["pw"] = PlanWeeks(school)
    pw = cache["pw"]
    groups = tuple(pw.spec_groups(course)) or (0,)
    rkey = ("r", key, teacher.id, groups)
    if rkey in cache:
        return cache[rkey]
    best = None
    for g in groups:
        real = pw.real_week(g)
        if ("c", key, g) not in cache:
            cache[("c", key, g)] = _class_slots(school, list(course.classes), classes, real)
        cslots = cache[("c", key, g)]
        if not teacher.unavailable:
            cnt = len(cslots)
        else:
            cnt = sum(1 for (d, p) in cslots if not any(r.matches(real, d, p) for r in teacher.unavailable))
        best = cnt if best is None else min(best, cnt)
    cache[rkey] = best or 0
    return cache[rkey]


def assign_teachers(school: School) -> list[str]:
    """Weist Kursteilen ohne Lehrer eine qualifizierte Lehrkraft zu.

    Bevorzugt Lehrkräfte, die die Klasse bereits unterrichten (weniger
    Lehrer pro Klasse) oder sie als Wunschklasse angegeben haben (``preferred_classes``),
    und verteilt das Deputat gleichmäßig. Lehrkräfte, deren Zeitfenster/Sperrzeiten zu wenige
    gemeinsame Stunden mit den Klassen des Kurses lassen, bekommen den Kurs nicht.
    """
    warnings: list[str] = []
    teachers = school.index("teachers")
    classes = school.index("classes")
    load: dict[str, int] = defaultdict(int)
    in_class: dict[tuple[str, str], int] = defaultdict(int)
    site_load: dict[tuple[str, str], int] = defaultdict(int)
    open_parts = []
    cap_cache: dict = {}

    def course_site(c) -> str:
        return next((classes[x].site for x in c.classes if x in classes), "")

    for c in school.courses:
        for p in c.parts:
            if p.teacher and p.teacher in teachers:
                load[p.teacher] += c.hours
                site_load[(p.teacher, course_site(c))] += c.hours
                for cid in c.classes:
                    in_class[(p.teacher, cid)] += 1
            else:
                p.teacher = None
                open_parts.append((c, p))
    qualified: dict[str, list[str]] = defaultdict(list)
    for t in teachers.values():
        for s in t.subjects:
            qualified[s].append(t.id)
    # Knappe Fächer zuerst, dann große Kurse
    open_parts.sort(key=lambda cp: (len(qualified[cp[1].subject]), -cp[0].hours))
    for c, p in open_parts:
        sites = {classes[cid].site for cid in c.classes if cid in classes}
        best, best_score = None, None
        blocked: dict[str, int] = defaultdict(int)   # Grund → Anzahl ausgeschlossener Lehrkräfte
        in_course = {q.teacher for q in c.parts if q.teacher}
        for tid in qualified[p.subject]:
            t = teachers[tid]
            if tid in in_course:  # parallele Kursteile brauchen verschiedene Lehrkräfte
                blocked["parallel"] += 1
                continue
            if load[tid] + c.hours > t.max_hours:
                blocked["deputat"] += 1
                continue
            if t.sites and sites and not sites & set(t.sites):
                blocked["site"] += 1
                continue
            # Zeitfenster/Sperrzeiten: genug gemeinsame Stunden mit den Klassen des Kurses?
            capacity = teacher_course_capacity(school, c, t, classes, cap_cache)
            if capacity < c.hours:
                blocked["time"] += 1
                continue
            score = (load[tid] / max(1, t.max_hours)) * 10
            score -= 4 * sum(in_class[(tid, cid)] for cid in c.classes)
            # Wunschklassen der Lehrkraft (Selbstauskunft)
            if t.preferred_classes and set(c.classes) & set(t.preferred_classes):
                score -= 6
            # knappe Verfügbarkeit (z. B. nur Abendstunden) → lieber Lehrkräfte mit mehr Spielraum
            if capacity < 2 * c.hours:
                score += 4 * c.hours / max(1, capacity)
            # Standorttreue: Lehrkräfte möglichst an einem Standort einsetzen (weniger Wegezeiten)
            other = sum(v for (tt, site), v in site_load.items() if tt == tid and site not in sites)
            score += 8 * other / max(1, t.max_hours)
            if best_score is None or score < best_score:
                best, best_score = tid, score
        if best is None:
            warnings.append(_no_teacher_reason(school, p.subject, c, blocked))
            continue
        p.teacher = best
        load[best] += c.hours
        site_load[(best, course_site(c))] += c.hours
        for cid in c.classes:
            in_class[(best, cid)] += 1
    return warnings


def _no_teacher_reason(school: School, subject: str, course, blocked: dict[str, int]) -> str:
    """Verständliche Meldung, warum ein Kursteil keine Lehrkraft bekommt."""
    where = course.label or course.id
    subj = school.index("subjects").get(subject)
    name = f"{subject} ({subj.name})" if subj and subj.name and subj.name != subject else subject
    if not blocked:
        return (f"Keine Lehrkraft mit dem Fach {name} – {where} bleibt offen (Fach bei Lehrkräften eintragen "
                "oder Lehrkraft im Kurs wählen)")
    reasons = {"deputat": "Deputat ausgeschöpft", "time": "Zeitfenster/Sperrzeiten passen nicht",
               "site": "anderer Standort", "parallel": "unterrichtet schon einen Parallelteil"}
    parts = [f"{reasons[k]}: {n}" for k, n in blocked.items() if n]
    return f"Keine freie Lehrkraft für {name} in {where} ({'; '.join(parts)})"


def capacity_warnings(school: School) -> list[str]:
    """Prüft, ob Klassen genug verfügbare Stunden für ihre Kurse haben."""
    from .calendar_utils import class_days
    from .weeks import PlanWeeks
    st = school.settings
    pw = PlanWeeks(school)
    course_groups = {c.id: set(pw.spec_groups(c)) for c in school.courses}
    out = []
    for cls in school.classes:
        days = class_days(school, cls)
        for g in range(len(pw)):
            real = pw.real_week(g)
            hours = sum(c.hours for c in school.courses if cls.id in c.classes and g in course_groups[c.id])
            free = 0
            for d in days:
                for p in range(min(st.periods, cls.max_periods_per_day)):
                    if not any(r.matches(real, d, p) for r in cls.unavailable):
                        free += 1
            if hours > free:
                wl = f" ({pw.hz.describe(pw.groups[g])})" if len(pw) > 1 else ""
                out.append(f"Klasse {cls.name}{wl}: {hours} Wochenstunden, aber nur {free} verfügbare Stunden")
    return out


def assign_class_teachers(school: School, prefer: list[str] | None = None) -> list[str]:
    """Setzt für Klassen ohne Klassenleitung eine Lehrkraft, die dort die meisten Stunden unterrichtet.

    Jede Lehrkraft leitet höchstens eine Klasse; Lehrkräfte aus ``prefer`` (z. B. Demo-Konten) werden bevorzugt.
    Nur Lehrkräfte, die die Klasse ohnehin unterrichten – so ändert sich deren Sichtbarkeit (Lehrer-Scope) nicht.
    Gibt die IDs der neu besetzten Klassen zurück.
    """
    prefer = [p for p in (prefer or []) if p]
    taken = {c.class_teacher for c in school.classes if c.class_teacher}
    hours: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for course in school.courses:
        for part in course.parts:
            if part.teacher:
                for cid in course.classes:
                    hours[cid][part.teacher] += course.hours
    changed: list[str] = []
    # Bevorzugte Lehrkräfte zuerst ihrer stärksten Klasse zuordnen
    for tid in prefer:
        if tid in taken:
            continue
        best = max((c for c in school.classes if not c.class_teacher and hours[c.id].get(tid)),
                   key=lambda c: (hours[c.id][tid], c.id), default=None)
        if best is not None:
            best.class_teacher = tid
            taken.add(tid)
            changed.append(best.id)
    for cls in school.classes:
        if cls.class_teacher:
            continue
        ranked = sorted(hours[cls.id].items(), key=lambda kv: (-kv[1], kv[0]))
        tid = next((t for t, _ in ranked if t not in taken), None)
        if tid:
            cls.class_teacher = tid
            taken.add(tid)
            changed.append(cls.id)
    return changed


# ------------------------------------------------------------------ Stundentafel einer Klasse
def class_curriculum_id(class_id: str) -> str:
    return f"KL-{class_id}"


def set_class_curriculum(school: School, class_id: str, entries: list[CurriculumEntry]) -> dict:
    """Legt die eigene Stundentafel einer Klasse fest (Vorrang vor der Jahrgangs-Stundentafel) und erzeugt die
    Kurse **nur dieser Klasse** neu (:func:`rebuild_class_courses`). ``entries`` leer = eigene Tafel entfernen,
    danach gilt wieder die Jahrgangs-Stundentafel."""
    cls = school.index("classes")[class_id]
    cid = class_curriculum_id(class_id)
    # Klasse aus anderen klassenbezogenen Tafeln lösen (eine Klasse hat genau eine eigene Tafel)
    emptied = set()
    for cur in school.curricula:
        if cur.id != cid and class_id in cur.classes:
            cur.classes = [c for c in cur.classes if c != class_id]
            if not cur.classes and not cur.grades:
                emptied.add(cur.id)        # galt nur für diese Klasse → durch die eigene Tafel ersetzt
    school.curricula = [c for c in school.curricula if c.id != cid and c.id not in emptied]
    if entries:
        school.curricula.append(Curriculum(id=cid, name=f"Stundentafel {cls.name}", grades=[], classes=[class_id],
                                           entries=list(entries)))
    return rebuild_class_courses(school, class_id)


def rebuild_class_courses(school: School, class_id: str) -> dict:
    """Erzeugt die Stundentafel-Kurse einer Klasse neu (wie :func:`build_courses_from_curricula`, aber nur für diese
    Klasse): Lehrkräfte bestehender Kurse bleiben, gekoppelte/manuelle Kurse werden angerechnet, Stunden entfernter
    Kurse fallen aus dem Plan. Offene Kursteile bekommen eine Lehrkraft (:func:`assign_teachers`).

    Liefert ``{"added", "removed", "changed", "unchanged", "warnings", "open_parts"}``."""
    cls = school.index("classes")[class_id]
    mine = {c.id: c for c in school.courses if c.origin == "curriculum" and c.classes == [class_id]}
    covered: dict[str, int] = defaultdict(int)
    for c in school.courses:
        if c.id in mine or class_id not in c.classes:
            continue
        for subj in {p.subject for p in c.parts}:
            covered[subj] += c.hours
    cur = curriculum_for_class(school, class_id)
    warnings: list[str] = []
    if cur is None:
        warnings.append(f"Klasse {cls.name}: keine Stundentafel zugeordnet")
    new: dict[str, Course] = {}
    subjects = school.index("subjects")
    for e in effective_entries(school, cur):
        if e.subject not in subjects:
            warnings.append(f"Fach {e.subject} gibt es nicht")
            continue
        hours = e.hours - covered[e.subject]
        if hours <= 0:
            continue
        cid = f"{class_id}-{e.subject}"
        old = mine.get(cid)
        teacher = old.parts[0].teacher if old and old.parts else None
        new[cid] = Course(id=cid, classes=[class_id], hours=hours, double=e.double,
                          parts=[CoursePart(subject=e.subject, teacher=teacher)],
                          label=f"{e.subject} {cls.name}", origin="curriculum",
                          weeks=list(old.weeks) if old else [], rhythm=copy.deepcopy(old.rhythm) if old else None)
    added = sorted(set(new) - set(mine))
    removed = sorted(set(mine) - set(new))
    changed = sorted(c for c in set(new) & set(mine)
                     if (new[c].hours, new[c].double) != (mine[c].hours, mine[c].double))
    school.courses = [c for c in school.courses if c.id not in mine] + list(new.values())
    if removed:
        gone = set(removed)
        school.lessons = [le for le in school.lessons if le.course_id not in gone]
    if added:
        warnings += [w for w in assign_teachers(school) if class_id in w or cls.name in w]
    open_parts = [c.id for c in new.values() if any(not p.teacher for p in c.parts)]
    return {"added": added, "removed": removed, "changed": changed,
            "unchanged": sorted(set(new) - set(added) - set(changed)), "warnings": warnings, "open_parts": open_parts}
