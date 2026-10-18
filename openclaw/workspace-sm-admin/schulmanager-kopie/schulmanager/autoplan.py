"""Automatische Neuplanung des regulären Stundenplans (Auto-Planer, reine Logik).

Nach jeder Änderung an Stammdaten oder Planung (Lehrkraft gesperrt, Raum gelöscht oder umgewidmet,
Stundentafel/Kurs geändert, Klasse hat neuen Praxistag …) prüft :func:`find_problems`, ob der reguläre Plan
noch gültig ist:

* **harte Verstöße** einzelner Stunden – Klasse nicht da / über Tageshöchststunden, Lehrkraft gesperrt oder
  nicht am Standort, Doppelbelegung von Klasse/Lehrkraft/Raum, Raum fehlt oder hat den falschen Typ
  (z. B. Informatik nur im IT-Raum), Stunde außerhalb des Zeitrasters;
* **Stunden ohne Kurs** (Kurs gelöscht);
* **fehlende bzw. überzählige Wochenstunden** eines Kurses (Stundentafel geändert, Kurs neu).

:func:`prepare_repair` repariert zuerst alles, was ohne Verschieben geht (Stunden ohne Kurs entfernen, freien
Raum des richtigen Typs zur selben Zeit wählen). Was dann noch übrig ist, sind die *freien Kurse* für den
Generator: Nur deren Stunden werden neu gelegt, alle anderen bleiben samt Räumen fixiert
(``server.jobs._pin_foreign_lessons``). Gesperrte Stunden (``locked``) gelten als Wunsch der Planung und werden
bei Doppelbelegungen bevorzugt behalten.

Der Server (``server/autoplan.py``) ruft das nach Änderungen automatisch auf und übernimmt das Ergebnis, wenn
der Plan dadurch besser wird.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from .models import School
from . import weeks as wk
from .timetable import lesson_site

DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
PLAIN_ROOM_TYPES = ("Klassenraum", "Kursraum")


@dataclass
class Problems:
    """Ergebnis von :func:`find_problems`."""
    lessons: dict[str, list[str]] = field(default_factory=dict)   # Stunde → Gründe (harte Verstöße)
    room_only: set[str] = field(default_factory=set)               # Stunden, bei denen nur der Raum nicht passt
    orphans: list[str] = field(default_factory=list)               # Stunden, deren Kurs nicht mehr existiert
    missing: dict[str, int] = field(default_factory=dict)          # Kurs → fehlende Stunden (über alle Wochen)
    excess: dict[str, int] = field(default_factory=dict)           # Kurs → überzählige Stunden
    lesson_course: dict[str, str] = field(default_factory=dict)    # Stunde → Kurs (für betroffene Stunden)

    @property
    def empty(self) -> bool:
        return not (self.lessons or self.orphans or self.missing or self.excess)

    def count(self) -> int:
        """Gesamtzahl der Probleme (Maß für „besser/schlechter“)."""
        return (len(self.lessons) + len(self.orphans) + sum(self.missing.values())
                + sum(self.excess.values()))

    def courses(self) -> set[str]:
        """Kurse, die für den Generator frei werden müssen (Raum-Probleme zählen mit, solange sie bestehen)."""
        out = {self.lesson_course[lid] for lid in self.lessons if lid in self.lesson_course}
        return out | set(self.missing) | set(self.excess)

    def signature(self) -> str:
        """Fingerabdruck der Problemlage – gleiche Lage = kein neuer Versuch nötig."""
        parts = sorted(f"L{lid}:{'|'.join(r)}" for lid, r in self.lessons.items())
        parts += sorted(f"O{x}" for x in self.orphans)
        parts += sorted(f"M{c}:{n}" for c, n in self.missing.items())
        parts += sorted(f"E{c}:{n}" for c, n in self.excess.items())
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]

    def summary(self, school: School, limit: int = 12) -> list[str]:
        """Lesbare Gründe (für Verlauf, Statusanzeige)."""
        courses = school.index("courses")
        out: list[str] = []
        for lid, reasons in sorted(self.lessons.items()):
            c = courses.get(self.lesson_course.get(lid, ""))
            out.append(f"{(c.label or c.id) if c else lid}: {reasons[0]}")
        if self.orphans:
            out.append(f"{len(self.orphans)} Stunde(n) ohne Kurs")
        for cid, n in sorted(self.missing.items()):
            c = courses.get(cid)
            out.append(f"{(c.label or cid) if c else cid}: {n} Stunde(n) nicht verplant")
        for cid, n in sorted(self.excess.items()):
            c = courses.get(cid)
            out.append(f"{(c.label or cid) if c else cid}: {n} Stunde(n) zu viel")
        # Duplikate entfernen (Doppelstunden liefern denselben Grund mehrfach)
        out = list(dict.fromkeys(out))
        return out[:limit] + ([f"… und {len(out) - limit} weitere"] if len(out) > limit else [])


def _needed_type(school: School, part, subjects: dict) -> Optional[str]:
    if part.room_type:
        return part.room_type
    subj = subjects.get(part.subject)
    return subj.room_type if subj and subj.room_type else None


def _where(day: int, p: int) -> str:
    return f"{DAYS[day] if 0 <= day < len(DAYS) else day} {p + 1}. Std."


def find_problems(school: School) -> Problems:
    """Prüft den regulären Stundenplan gegen die aktuellen Stammdaten (siehe Moduldoku)."""
    st = school.settings
    courses = school.index("courses")
    classes = school.index("classes")
    teachers = school.index("teachers")
    rooms = school.index("rooms")
    subjects = school.index("subjects")
    out = Problems()
    pw = wk.PlanWeeks(school)
    room_flag: dict[str, bool] = defaultdict(bool)
    other_flag: dict[str, bool] = defaultdict(bool)

    def add(les, text: str, room: bool = False) -> None:
        lst = out.lessons.setdefault(les.id, [])
        if text not in lst:
            lst.append(text)
        out.lesson_course[les.id] = les.course_id
        if room:
            room_flag[les.id] = True
        else:
            other_flag[les.id] = True

    occ_cls: dict[tuple, str] = {}
    occ_t: dict[tuple, str] = {}
    occ_r: dict[tuple, str] = {}
    placed: dict[tuple[str, int], int] = defaultdict(int)
    # Fixierte Stunden zuerst: bei Doppelbelegung bleibt die fixierte, die andere gilt als Problem
    for les in sorted(school.lessons, key=lambda x: not x.locked):
        c = courses.get(les.course_id)
        if c is None:
            out.orphans.append(les.id)
            continue
        weeks = pw.lesson_groups(les, c)
        for w in weeks:
            placed[(c.id, w)] += les.length
        if les.day < 0 or les.day >= st.days or les.start < 0 or les.start + les.length > st.periods:
            add(les, "liegt außerhalb des Zeitrasters")
            continue
        slots = [(w, les.day, les.start + k) for w in weeks for k in range(les.length)]
        site = lesson_site(school, les, rooms, classes, courses)
        # Klassen
        for cid in c.classes:
            cl = classes.get(cid)
            if cl is None:
                continue
            for (w, d, p) in slots:
                if p >= cl.max_periods_per_day:
                    add(les, f"Klasse {cl.name} hat höchstens {cl.max_periods_per_day} Stunden am Tag")
                    break
                rule = next((r for r in cl.unavailable if r.matches(pw.real_week(w), d, p)), None)
                if rule:
                    add(les, f"Klasse {cl.name} ist {_where(d, p)} nicht da ({rule.note or 'gesperrt'})")
                    break
        # Lehrkräfte
        for part in c.parts:
            t = teachers.get(part.teacher) if part.teacher else None
            if t is None:
                continue
            for (w, d, p) in slots:
                rule = next((r for r in t.unavailable if r.matches(pw.real_week(w), d, p)), None)
                if rule:
                    add(les, f"Lehrkraft {t.id} ist {_where(d, p)} gesperrt ({rule.note or 'Sperrzeit'})")
                    break
            if t.sites and site and site not in t.sites:
                add(les, f"Lehrkraft {t.id} unterrichtet nicht am Standort {site}")
        # Räume
        for i, part in enumerate(c.parts):
            r = les.rooms[i] if i < len(les.rooms) else None
            need = _needed_type(school, part, subjects)
            if part.room and r != part.room:
                add(les, f"{part.subject} gehört in den festen Raum {part.room}", room=True)
            elif r and r not in rooms:
                add(les, f"Raum {r} gibt es nicht mehr", room=True)
            elif r and need and rooms[r].type != need:
                add(les, f"{part.subject} braucht einen Raum vom Typ {need} (Raum {r} ist {rooms[r].type})",
                    room=True)
            elif not r and need:
                add(les, f"{part.subject} braucht einen Raum vom Typ {need}", room=True)
        # Belegung
        for (w, d, p) in slots:
            for cid in c.classes:
                other = occ_cls.setdefault((cid, w, d, p), les.id)
                if other != les.id:
                    add(les, f"Klasse {cid} hat {_where(d, p)} schon Unterricht ({other})")
            for part in c.parts:
                if part.teacher:
                    other = occ_t.setdefault((part.teacher, w, d, p), les.id)
                    if other != les.id:
                        add(les, f"Lehrkraft {part.teacher} unterrichtet {_where(d, p)} schon ({other})")
            for r in les.rooms:
                if r and r in rooms:
                    other = occ_r.setdefault((r, w, d, p), les.id)
                    if other != les.id:
                        add(les, f"Raum {r} ist {_where(d, p)} doppelt belegt ({other})", room=True)
    for c in school.courses:
        miss = exc = 0
        for w in pw.spec_groups(c):
            if not pw.planned[w]:
                continue
            diff = c.hours - placed[(c.id, w)]
            if diff > 0:
                miss += diff
            elif diff < 0:
                exc -= diff
        if miss:
            out.missing[c.id] = miss
        if exc:
            out.excess[c.id] = exc
    out.room_only = {lid for lid in out.lessons if room_flag[lid] and not other_flag[lid]}
    return out


# --------------------------------------------------------------------------- Räume reparieren
def repair_rooms(school: School, lesson_ids: set[str]) -> tuple[list[dict], set[str]]:
    """Wählt für die Stunden ``lesson_ids`` freie Räume des richtigen Typs zur **selben Zeit** (verändert
    ``school``). Liefert ``(änderungen, nicht_lösbar)``; ``änderungen`` = ``[{lesson, course, old, new}]``.

    Reihenfolge der Kandidaten: fester Raum des Kursteils → bisheriger Raum (falls noch passend und frei) →
    Klassenraum der Klasse (nur ohne besonderen Raumtyp) → übrige Räume des Typs, gleicher Standort zuerst.
    """
    if not lesson_ids:
        return [], set()
    courses = school.index("courses")
    classes = school.index("classes")
    rooms = school.index("rooms")
    subjects = school.index("subjects")
    used: set[tuple] = set()
    pw = wk.PlanWeeks(school)
    for les in school.lessons:
        if les.id in lesson_ids:
            continue
        for w in pw.lesson_groups(les, courses.get(les.course_id)):
            for k in range(les.length):
                for r in les.rooms:
                    if r:
                        used.add((r, w, les.day, les.start + k))
    changes: list[dict] = []
    failed: set[str] = set()
    for les in sorted((x for x in school.lessons if x.id in lesson_ids), key=lambda x: (not x.locked, x.id)):
        c = courses.get(les.course_id)
        if c is None:
            failed.add(les.id)
            continue
        keys = [(w, les.day, les.start + k) for w in pw.lesson_groups(les, c) for k in range(les.length)]
        site = lesson_site(school, les, rooms, classes, courses)
        rooms_list = (list(les.rooms) + [None] * len(c.parts))[:len(c.parts)]
        taken_here: set[str] = set()

        def free(rid: Optional[str]) -> bool:
            return bool(rid) and rid in rooms and rid not in taken_here and all((rid,) + k not in used
                                                                                for k in keys)

        ok = True
        for i, part in enumerate(c.parts):
            cur = rooms_list[i]
            need = _needed_type(school, part, subjects)
            fits = (cur in rooms and (not need or rooms[cur].type == need)
                    and (not part.room or cur == part.room)) if cur else not need and not part.room
            if fits and (not cur or free(cur)):
                if cur:
                    taken_here.add(cur)
                continue
            want = need or (rooms[cur].type if cur in rooms else None)
            cands: list[Optional[str]] = []
            if part.room:
                cands.append(part.room)
            else:
                if cur in rooms and (not want or rooms[cur].type == want):
                    cands.append(cur)
                if not need and len(c.classes) == 1 and c.classes[0] in classes:
                    cands.append(classes[c.classes[0]].home_room)
                homes = {cl.home_room for cl in school.classes if cl.home_room}
                pool = [r for r in rooms.values() if (r.type == want if want else r.type in PLAIN_ROOM_TYPES)]
                pool.sort(key=lambda r: (bool(site) and r.site != site, r.id in homes, r.id))
                cands += [r.id for r in pool]
            new = next((r for r in cands if free(r)), None)
            if new is None:
                ok = False
                continue
            if new != cur:
                changes.append({"lesson": les.id, "course": c.id, "old": cur, "new": new})
            rooms_list[i] = new
            taken_here.add(new)
        if ok:
            les.rooms = rooms_list
        else:
            failed.add(les.id)
        for r in (les.rooms if ok else [x for x in les.rooms if x in rooms]):
            if r:
                for k in keys:
                    used.add((r,) + k)
    # Änderungen nicht lösbarer Stunden zählen nicht
    changes = [ch for ch in changes if ch["lesson"] not in failed]
    return changes, failed


def expand_courses(school: School, free: set[str] | list[str]) -> list[str]:
    """Zweite Stufe, wenn die betroffenen Kurse allein nicht passen: zusätzlich alle Kurse der beteiligten Klassen
    und Lehrkräfte frei geben (mehr Spielraum, verschiebt aber auch andere Stunden dieser Klassen/Lehrkräfte)."""
    free = set(free)
    courses = school.index("courses")
    classes = {cid for c in free if c in courses for cid in courses[c].classes}
    teachers = {p.teacher for c in free if c in courses for p in courses[c].parts if p.teacher}
    out = set(free)
    for c in school.courses:
        if set(c.classes) & classes or any(p.teacher in teachers for p in c.parts if p.teacher):
            out.add(c.id)
    return sorted(out)


# --------------------------------------------------------------------------- Vorbereitung
@dataclass
class RepairPlan:
    """Ergebnis von :func:`prepare_repair`."""
    school: School                 # Arbeitskopie nach Raumreparatur / Entfernen verwaister Stunden
    before: Problems               # Probleme vor der Reparatur
    after: Problems                # Probleme nach der Raumreparatur (→ Generator)
    room_changes: list[dict]
    removed_orphans: list[str]

    @property
    def free_courses(self) -> list[str]:
        """Kurse, die der Generator neu legen soll. Mit Planzeiträumen (``plan_periods``) bleibt die Liste leer: Verschieben
        über alle Zeiträume hinweg würde deren getrennte Pläne vermischen, geplant wird dort je Zeitraum im Generator."""
        from .plan_periods import active
        return [] if active(self.school) else sorted(self.after.courses())

    @property
    def changed(self) -> bool:
        """Hat die Raumreparatur schon etwas am Plan geändert?"""
        return bool(self.room_changes or self.removed_orphans)


def prepare_repair(school: School) -> RepairPlan:
    """Arbeitskopie mit allen Reparaturen, die ohne Verschieben gehen (siehe Moduldoku)."""
    work = School.from_dict(school.to_dict())
    before = find_problems(work)
    removed: list[str] = []
    if before.orphans:
        gone = set(before.orphans)
        removed = sorted(gone)
        work.lessons = [le for le in work.lessons if le.id not in gone]
    changes: list[dict] = []
    if before.room_only:
        changes, _ = repair_rooms(work, set(before.room_only))
    after = find_problems(work) if (changes or removed) else before
    return RepairPlan(work, before, after, changes, removed)
