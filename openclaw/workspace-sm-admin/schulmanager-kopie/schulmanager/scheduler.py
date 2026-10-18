"""Stundenplan-Generator.

Ablauf
------
0. Wochenvarianten: Die laufenden Wochen 1 … Y des Schuljahres werden nach ihren Bedingungen (Sperren, Wünsche,
   Wochenangaben von Kursen und fixierten Stunden: ausgewählte Wochen oder Rhythmus) zu Varianten zusammengefasst.
   Geplant wird je Variante (Gitter Variante × 7 Tage × Stunden); die Kosten zählen mit dem Gewicht m_v · V / Y.
   Bei Regeln nur in den Wochen 1 und 2 sind das 3 Varianten statt 52 Wochen.
1. Aus den Kursen werden Blöcke (Einzel-/Doppelstunden) erzeugt. Ein Block
   gilt zunächst für alle Wochenvarianten seines Kurses (gleicher Platz in jeder Woche).
2. Konstruktion: Blöcke werden nach Schwierigkeit sortiert (Kopplungen,
   Fachräume, wenig verfügbare Lehrer zuerst) und gierig in den besten
   gültigen Slot gesetzt.
3. Reparatur: Nicht platzierbare Blöcke verdrängen einen einzelnen anderen
   Block, der woanders hin ausweicht. Klappt das nicht, wird der Block auf
   einzelne Wochenvarianten seines Kurses aufgeteilt und
   Doppelstunden notfalls in Einzelstunden zerlegt.
4. Optimierung: Simulated Annealing (Verschieben/Tauschen) minimiert
   Hohlstunden, Springstunden, späte Hauptfächer, Standortwechsel usw.

Harte Bedingungen: keine Doppelbelegung von Klasse/Lehrer/Raum, Sperrzeiten
von Klassen und Lehrern, Unterrichtstage der Klassen (Mo–So), max. Stunden pro Tag, max. Blöcke eines Fachs pro
Tag, Wegezeit zwischen Standorten.

Reproduzierbar (V1): Mit ``iterations`` endet die Optimierung nach genau so vielen Schritten (Temperatur folgt
it/iterations), gleiche Seeds ergeben dann gleiche Pläne.
"""
from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from . import commute
from . import rules as rl
from . import weeks as wk
from .calendar_utils import class_days
from .models import Lesson, School

FREE = -1
NO_COMMUTE_FACTOR = 40.0     # Standortwechsel einer Lehrkraft, die nicht pendelt (fast harte Regel)


@dataclass
class Block:
    id: int
    course: int                          # Index in Scheduler.courses
    length: int
    weeks: tuple[int, ...]               # Wochenvarianten, in denen der Block liegt
    day: int = -1
    start: int = -1
    rooms: list = field(default_factory=list)
    site: str = ""
    locked: bool = False

    @property
    def placed(self) -> bool:
        return self.day >= 0


@dataclass
class _CourseInfo:
    id: str
    classes: list[int]
    teachers: list[int]                  # je Kursteil (-1 = keiner)
    room_reqs: list[tuple]               # je Kursteil
    weeks: tuple[int, ...]               # Wochenvarianten des Kurses
    hours: int
    double: bool
    core: bool
    max_per_day: int
    site: str
    days: tuple[int, ...] = tuple(range(7))      # Tage, an denen alle Klassen des Kurses Unterricht haben


@dataclass
class ScheduleResult:
    lessons: list[Lesson]
    unplaced: list[dict]
    stats: dict
    warnings: list[str]
    #: Verlauf der Optimierung: ``[Sekunden, Schritte, Kosten]`` (höchstens ~60 Punkte)
    trace: list = field(default_factory=list)
    #: bei ``generate_best_of``: ein Eintrag je Lauf (Startwert, Kosten, unverplant, Verlauf)
    runs: list = field(default_factory=list)


TRACE_POINTS = 60


class Scheduler:
    def __init__(self, school: School, seed: int = 1,
                 progress: Optional[Callable[[str, float], None]] = None, today: Optional[date] = None):
        self.school = school
        self.st = school.settings
        self.w = school.settings.weights
        self.rng = random.Random(seed)
        self.progress = progress or (lambda msg, frac: None)
        self.warnings: list[str] = []
        self._variants(today)
        self.D, self.P, self.W = 7, self.st.periods, len(self.groups)
        self.S = self.W * self.D * self.P
        self.T = max(0, self.st.site_travel_periods)
        self._build()

    # --------------------------------------------------------------- variants
    def _variants(self, today: Optional[date]) -> None:
        """Wochenvarianten (W5): Gruppen realer Wochen mit gleicher Signatur."""
        sc = self.school
        self.hz = hz = wk.Horizon(sc, today)
        sets: list[frozenset[int]] = []
        for c in sc.classes:
            for r in c.unavailable:
                if r.weeks or r.rhythm or r.valid_week:
                    sets.append(hz.spec_members(r))
        for t in sc.teachers:
            for r in list(t.unavailable) + list(t.wishes):
                if r.weeks or r.rhythm or r.valid_week:
                    sets.append(hz.spec_members(r))
        courses = sc.index("courses")
        for c in sc.courses:
            if c.weeks or c.rhythm:
                sets.append(hz.spec_members(c))
        for les in sc.lessons:
            if les.locked and (les.weeks or les.rhythm):
                sets.append(hz.lesson_members(les, courses.get(les.course_id)))
        for spec in rl.week_specs(sc.settings):       # Ausnahmen der Regeln, die nur in manchen Wochen gelten
            sets.append(hz.members(spec["weeks"], spec["rhythm"]))
        self.groups = wk.group_weeks(len(hz), sets) or [list(range(len(hz)))]
        self.of_index = [0] * len(hz)
        for g, members in enumerate(self.groups):
            for i in members:
                self.of_index[i] = g
        V, H = len(self.groups), max(1, len(hz))
        self.weight = [len(g) * V / H for g in self.groups]
        self.variants = [{"weeks": [hz.real[i] for i in g], "weight": round(self.weight[v], 6)}
                         for v, g in enumerate(self.groups)]
        if V > 8:
            self.warnings.append(f"Viele unterschiedliche Wochen ({V}). Erhöhen Sie die Rechenzeit oder tragen Sie "
                                 "Blockphasen als Abwesenheit ein.")

    def variants_of_members(self, members) -> tuple[int, ...]:
        """Varianten, in denen die realen Wochen (Indizes) ``members`` liegen."""
        return tuple(sorted({self.of_index[i] for i in members}))

    # ------------------------------------------------------------------ setup
    def _build(self) -> None:
        sc = self.school
        self.class_ids = [c.id for c in sc.classes]
        self.cidx = {c: i for i, c in enumerate(self.class_ids)}
        self.teacher_ids = [t.id for t in sc.teachers]
        self.tidx = {t: i for i, t in enumerate(self.teacher_ids)}
        self.room_ids = [r.id for r in sc.rooms]
        self.ridx = {r: i for i, r in enumerate(self.room_ids)}
        self.room_site = [r.site for r in sc.rooms]
        self.rooms_by_type: dict[str, list[int]] = defaultdict(list)
        for i, r in enumerate(sc.rooms):
            self.rooms_by_type[r.type].append(i)
        subjects = sc.index("subjects")
        classes = sc.index("classes")

        D, P, W = self.D, self.P, self.W
        hz = self.hz
        rep = [g[0] for g in self.groups]
        # Doppelstunden nur in Pausenblöcken (Settings.double_alignment)
        self.block_ok = [sc.settings.block_start_ok(s, 2, self.P) for s in range(self.P)]

        # Gewichte je Klasse/Lehrkraft/Kurs und Wochenvariante (Regeln mit Gültigkeiten, ``rules.PlanWeights``)
        pw = rl.PlanWeights(sc, hz, self.groups)
        self.class_w: list[list[tuple[float, float, float]]] = [pw.for_class(c) for c in sc.classes]
        self.teacher_w: list[list[tuple[float, float, float]]] = [pw.for_teacher(t.id) for t in sc.teachers]
        self.course_w: list[list[tuple[float, float, float, float, int, bool]]] = []

        # Sperrzeiten (je Variante an ihrer ersten realen Woche; Tage ohne Unterricht der Klasse sind gesperrt)
        self.class_blocked = [bytearray(self.S) for _ in self.class_ids]
        self.class_max = []
        self.class_days = []
        for i, c in enumerate(sc.classes):
            self.class_max.append(min(P, c.max_periods_per_day))
            days = set(class_days(sc, c))
            self.class_days.append(days)
            for w in range(W):
                real = hz.real[rep[w]]
                for d in range(D):
                    for p in range(P):
                        if (d not in days or p >= c.max_periods_per_day
                                or any(r.matches(real, d, p) for r in c.unavailable)):
                            self.class_blocked[i][self.slot(w, d, p)] = 1
        self.teacher_blocked = [bytearray(self.S) for _ in self.teacher_ids]
        self.teacher_wish = [bytearray(self.S) for _ in self.teacher_ids]
        self.teacher_maxday = []
        self.teacher_sites = []
        self.teacher_no_commute = []
        self.teacher_once = []
        self.commute_special = commute.special(self.st, sc.teachers)    # Wegezeiten je Standortpaar / Mindestpausen
        for i, t in enumerate(sc.teachers):
            self.teacher_maxday.append(t.max_per_day)
            self.teacher_sites.append(set(t.sites))
            self.teacher_no_commute.append(commute.teacher_mode(t) == "never")
            self.teacher_once.append(commute.teacher_mode(t) == "once")
            for target, rules in ((self.teacher_blocked, t.unavailable), (self.teacher_wish, t.wishes)):
                for rule in rules:
                    for w in range(W):
                        real = hz.real[rep[w]]
                        for d in range(D):
                            for p in range(P):
                                if rule.matches(real, d, p):
                                    target[i][self.slot(w, d, p)] = 1

        # Kurse (Doppelstunden: markierte Kurse bzw. – mit ``prefer_doubles`` – alle ab 2 Wochenstunden)
        prefer_doubles = bool(getattr(sc.settings, "prefer_doubles", False))
        self.courses: list[_CourseInfo] = []
        for c in sc.courses:
            cl = [self.cidx[x] for x in c.classes if x in self.cidx]
            if not cl or c.hours <= 0:
                continue
            teachers, reqs = [], []
            for part in c.parts:
                teachers.append(self.tidx.get(part.teacher, -1) if part.teacher else -1)
                subj = subjects.get(part.subject)
                rtype = part.room_type or (subj.room_type if subj else None)
                if part.room and part.room in self.ridx:
                    reqs.append(("fixed", self.ridx[part.room]))
                elif rtype:
                    reqs.append(("type", rtype))
                elif len(c.parts) == 1 and len(cl) == 1 and classes[c.classes[0]].home_room in self.ridx:
                    reqs.append(("fixed", self.ridx[classes[c.classes[0]].home_room]))
                else:
                    pool = [self.ridx[classes[self.class_ids[ci]].home_room] for ci in cl
                            if classes[self.class_ids[ci]].home_room in self.ridx]
                    pool += self.rooms_by_type.get("Kursraum", [])
                    reqs.append(("pool", pool))
            subj0 = subjects.get(c.parts[0].subject) if c.parts else None
            weeks_c = self.variants_of_members(hz.spec_members(c))
            if not weeks_c:
                self.warnings.append(f"{c.id}: liegt in keiner Woche dieses Schuljahres")
                continue
            days_c = set(range(D))
            for ci in cl:
                days_c &= self.class_days[ci]
            # Tage, an denen alle Beteiligten überhaupt verfügbar sind -> ggf. 2 Blöcke/Tag erlauben
            avail_days = D
            for w in weeks_c:
                n_ok = 0
                for d in sorted(days_c):
                    rng_slots = range(self.slot(w, d, 0), self.slot(w, d, 0) + P)
                    if (all(any(not self.class_blocked[ci][x] for x in rng_slots) for ci in cl)
                            and all(any(not self.teacher_blocked[ti][x] for x in rng_slots)
                                    for ti in teachers if ti >= 0)):
                        n_ok += 1
                avail_days = min(avail_days, n_ok)
            double = bool(c.double or (prefer_doubles and c.hours >= 2))
            blocks_needed = (c.hours + 1) // 2 if double else c.hours
            max_pd = max(1, subj0.max_per_day if subj0 else 1, -(-blocks_needed // max(1, avail_days)))
            self.course_w.append(pw.for_course([classes[self.class_ids[ci]] for ci in cl],
                                               [p.subject for p in c.parts], [p.teacher for p in c.parts if p.teacher]))
            self.courses.append(_CourseInfo(
                id=c.id, classes=cl, teachers=teachers, room_reqs=reqs,
                weeks=weeks_c,
                hours=c.hours, double=double,
                core=bool(subj0 and subj0.core),
                max_per_day=max_pd,
                site=classes[self.class_ids[cl[0]]].site,
                days=tuple(sorted(days_c)),
            ))
        self.course_by_id = {c.id: i for i, c in enumerate(self.courses)}

        # Zielstunden pro Klasse und Woche (für gleichmäßige Tage)
        self.class_target = [[0.0] * W for _ in self.class_ids]
        hours = [[0] * W for _ in self.class_ids]
        for c in self.courses:
            for ci in c.classes:
                for w in c.weeks:
                    hours[ci][w] += c.hours
        self.class_avail_day = [[False] * (W * D) for _ in self.class_ids]
        for ci in range(len(self.class_ids)):
            for w in range(W):
                days = 0
                for d in range(D):
                    base = self.slot(w, d, 0)
                    if any(not self.class_blocked[ci][base + p] for p in range(P)):
                        self.class_avail_day[ci][w * D + d] = True
                        days += 1
                self.class_target[ci][w] = hours[ci][w] / max(1, days)

        # Belegung
        self.class_grid = [[FREE] * self.S for _ in self.class_ids]
        self.teacher_grid = [[FREE] * self.S for _ in self.teacher_ids]
        self.room_grid = [[FREE] * self.S for _ in self.room_ids]
        self.course_day = [[0] * (W * D) for _ in self.courses]
        self.blocks: list[Block] = []

    def slot(self, w: int, d: int, p: int) -> int:
        return ((w * self.D) + d) * self.P + p

    # ------------------------------------------------------------- blocks
    def _make_blocks(self, ci: int, need: dict[int, int], double: bool) -> list[Block]:
        """Erzeugt Blöcke, die je Wochenvariante des Kurses ``need[v]`` Stunden abdecken (gemeinsame zuerst)."""
        out = []
        weeks = sorted(w for w, n in need.items() if n > 0)
        if not weeks:
            return out
        common = min(need[w] for w in weeks)
        full_weeks = tuple(weeks)

        def emit(n: int, vw: tuple[int, ...]):
            if double and n >= 2:
                for _ in range(n // 2):
                    out.append(Block(len(self.blocks) + len(out), ci, 2, vw))
                n %= 2
            for _ in range(n):
                out.append(Block(len(self.blocks) + len(out), ci, 1, vw))

        emit(common, full_weeks)
        for w in weeks:
            emit(need[w] - common, (w,))
        return out

    def _add_blocks(self, blocks: list[Block]) -> None:
        for b in blocks:
            b.id = len(self.blocks)
            self.blocks.append(b)

    # ------------------------------------------------------- feasibility
    def _slots(self, b: Block, d: int, s: int):
        D, P = self.D, self.P
        for w in b.weeks:
            base = (w * D + d) * P + s
            for k in range(b.length):
                yield base + k

    def check(self, b: Block, d: int, s: int, preferred_rooms: Optional[list] = None) -> Optional[tuple[list, str]]:
        """Liefert (Räume, Standort), wenn Block ``b`` bei (d, s) liegen darf.

        ``preferred_rooms`` (Raum-Indizes je Kursteil, ``None`` erlaubt) werden zuerst versucht – so behalten
        fixierte Stunden ihre bisherigen Räume und wechseln nicht ungewollt den Standort.
        """
        if s < 0 or s + b.length > self.P:
            return None
        if b.length > 1 and not self.block_ok[s]:
            return None
        c = self.courses[b.course]
        D = self.D
        cw = self.course_w[b.course]
        for w in b.weeks:
            if self.course_day[b.course][w * D + d] >= c.max_per_day:
                return None
            # „Muss“ bei „Hauptfächer früh am Tag“: nie nach der spätesten Hauptfachstunde (harte Regel)
            if c.core and cw[w][5] and s + b.length - 1 > cw[w][4]:
                return None
        slots = list(self._slots(b, d, s))
        for ci in c.classes:
            g, bl = self.class_grid[ci], self.class_blocked[ci]
            for x in slots:
                if g[x] != FREE or bl[x]:
                    return None
        for ti in c.teachers:
            if ti < 0:
                continue
            g, bl = self.teacher_grid[ti], self.teacher_blocked[ti]
            for x in slots:
                if g[x] != FREE or bl[x]:
                    return None
        # Teacher daily max
        for ti in c.teachers:
            if ti < 0:
                continue
            g = self.teacher_grid[ti]
            for w in b.weeks:
                base = (w * D + d) * self.P
                if sum(1 for p in range(self.P) if g[base + p] != FREE) + b.length > self.teacher_maxday[ti]:
                    return None
        rooms = self._assign_rooms(c, slots, preferred_rooms)
        if rooms is None:
            return None
        site = c.site
        for r in rooms:
            if r is not None and self.room_site[r]:
                site = self.room_site[r]
                break
        for ti in c.teachers:
            if ti >= 0 and self.teacher_sites[ti] and site and site not in self.teacher_sites[ti]:
                return None
        if (self.T or self.commute_special) and site and not self._travel_ok(c, b, d, s, site):
            return None
        return rooms, site

    def _assign_rooms(self, c: _CourseInfo, slots: list[int], preferred: Optional[list] = None) -> Optional[list]:
        rooms: list = []
        used: set[int] = set()

        def free(r: int) -> bool:
            g = self.room_grid[r]
            return r not in used and all(g[x] == FREE for x in slots)

        for i, (kind, val) in enumerate(c.room_reqs):
            want = preferred[i] if preferred and i < len(preferred) else None
            if want is not None and free(want) and (
                    (kind == "fixed" and want == val)
                    or (kind == "type" and want in self.rooms_by_type.get(val, ()))
                    or (kind == "pool" and want in val)):
                used.add(want)
                rooms.append(want)
                continue
            if kind == "fixed":
                if not free(val):
                    return None
                chosen = val
            else:
                cands = self.rooms_by_type.get(val, []) if kind == "type" else val
                chosen = None
                # Räume am Standort der Klasse bevorzugen
                for pref in (True, False):
                    for r in cands:
                        if (self.room_site[r] == c.site) == pref and free(r):
                            chosen = r
                            break
                    if chosen is not None:
                        break
                if chosen is None:
                    return None
            used.add(chosen)
            rooms.append(chosen)
        return rooms

    def _site_at(self, unit: int) -> str:
        return self.blocks[unit].site

    def _travel_ok(self, c: _CourseInfo, b: Block, d: int, s: int, site: str) -> bool:
        T, P, D = self.T, self.P, self.D
        lo, hi = max(0, s - T), min(P, s + b.length + T)
        grids = [self.class_grid[ci] for ci in c.classes]
        if not self.commute_special:
            grids += [self.teacher_grid[ti] for ti in c.teachers if ti >= 0]
        for w in b.weeks:
            base = (w * D + d) * P
            for g in grids:
                for p in range(lo, hi):
                    if s <= p < s + b.length:
                        continue
                    u = g[base + p]
                    if u != FREE and self.blocks[u].site and self.blocks[u].site != site:
                        return False
        if self.commute_special:
            # Lehrkräfte: Wegezeit je Standortpaar und Mindestpause der Lehrkraft (commute.py)
            last = s + b.length - 1
            for ti in c.teachers:
                if ti < 0:
                    continue
                teacher = self.school.teachers[ti]
                g = self.teacher_grid[ti]
                for w in b.weeks:
                    base = (w * D + d) * P
                    for p in range(P):
                        if s <= p <= last:
                            continue
                        u = g[base + p]
                        other = self.blocks[u].site if u != FREE else None
                        if not other or other == site:
                            continue
                        if self.teacher_no_commute[ti]:     # weiche Regel (Kosten); hart nur die feste Wegezeit
                            if lo <= p < hi:
                                return False
                            continue
                        ok = (commute.change_ok(self.st, teacher, other, p, site, s) if p < s
                              else commute.change_ok(self.st, teacher, site, last, other, p))
                        if not ok:
                            return False
        return True

    # ------------------------------------------------------- place/remove
    def place(self, b: Block, d: int, s: int, rooms: list, site: str) -> None:
        c = self.courses[b.course]
        b.day, b.start, b.rooms, b.site = d, s, rooms, site
        for x in self._slots(b, d, s):
            for ci in c.classes:
                self.class_grid[ci][x] = b.id
            for ti in c.teachers:
                if ti >= 0:
                    self.teacher_grid[ti][x] = b.id
            for r in rooms:
                if r is not None:
                    self.room_grid[r][x] = b.id
        for w in b.weeks:
            self.course_day[b.course][w * self.D + d] += 1

    def remove(self, b: Block) -> tuple[int, int, list, str]:
        c = self.courses[b.course]
        old = (b.day, b.start, b.rooms, b.site)
        for x in self._slots(b, b.day, b.start):
            for ci in c.classes:
                self.class_grid[ci][x] = FREE
            for ti in c.teachers:
                if ti >= 0:
                    self.teacher_grid[ti][x] = FREE
            for r in b.rooms:
                if r is not None:
                    self.room_grid[r][x] = FREE
        for w in b.weeks:
            self.course_day[b.course][w * self.D + b.day] -= 1
        b.day, b.start, b.rooms = -1, -1, []
        return old

    # --------------------------------------------------------------- cost
    def class_day_cost(self, ci: int, wd: int) -> float:
        if not self.class_avail_day[ci][wd]:
            return 0.0
        P = self.P
        base = wd * P
        g, bl = self.class_grid[ci], self.class_blocked[ci]
        first = last = -1
        count = 0
        first_avail = -1
        for p in range(P):
            if first_avail < 0 and not bl[base + p]:
                first_avail = p
            if g[base + p] != FREE:
                if first < 0:
                    first = p
                last = p
                count += 1
        w = wd // self.D
        target = self.class_target[ci][w]
        weight = self.weight[w]
        w_gap, w_late, w_balance = self.class_w[ci][w]
        cost = w_balance * 0.5 * (count - target) ** 2
        if count == 0:
            return cost * weight
        gaps = 0
        for p in range(first, last + 1):
            if g[base + p] == FREE and not bl[base + p]:
                gaps += 1
        cost += w_gap * gaps
        cost += w_late * max(0, first - first_avail)
        return cost * weight

    def teacher_day_cost(self, ti: int, wd: int) -> float:
        P = self.P
        base = wd * P
        g = self.teacher_grid[ti]
        wish = self.teacher_wish[ti]
        first = last = -1
        count = 0
        changes = 0
        wished = 0
        prev_site = None
        for p in range(P):
            u = g[base + p]
            if u != FREE:
                wished += wish[base + p]
                if first < 0:
                    first = p
                last = p
                count += 1
                site = self.blocks[u].site
                if prev_site is not None and site != prev_site:
                    changes += 1
                prev_site = site
        if count == 0:
            return 0.0
        gaps = (last - first + 1) - count
        w = wd // self.D
        w_gap, w_site, w_wish = self.teacher_w[ti][w]
        site_w = w_site * (NO_COMMUTE_FACTOR if self.teacher_no_commute[ti] else 1.0)
        if self.teacher_once[ti] and changes > 1:       # „höchstens 1× am Tag“: jeder weitere Wechsel fast verboten
            changes += (changes - 1) * (NO_COMMUTE_FACTOR - 1.0)
        return (w_gap * gaps + site_w * changes + w_wish * wished) * self.weight[w]

    def block_cost(self, b: Block) -> float:
        if not b.placed:
            return 0.0
        c = self.courses[b.course]
        cw = self.course_w[b.course]
        split = c.double and b.length == 1 and c.hours >= 2
        end = b.start + b.length - 1
        mid = b.start + (b.length - 1) * 0.5
        cost = 0.0
        for v in b.weeks:
            w_pos, w_core, w_split, _, latest, _ = cw[v]
            nv = self.weight[v]
            cost += w_pos * mid * nv
            if c.core and end > latest:
                cost += w_core * (end - latest) * nv
            if split:
                cost += w_split * nv
        return cost

    def course_cost(self, k: int) -> float:
        c = self.courses[k]
        if c.hours > 3:
            return 0.0
        cd, D = self.course_day[k], self.D
        cw = self.course_w[k]
        cost = 0.0
        for w in range(self.W):
            row = cd[w * D:(w + 1) * D]
            for d in range(D - 1):
                if row[d] and row[d + 1]:
                    cost += cw[w][3] * self.weight[w]
        return cost

    def _terms(self, b: Block, days: set[int]):
        c = self.courses[b.course]
        cds = set()
        tds = set()
        for d in days:
            for w in b.weeks:
                wd = w * self.D + d
                for ci in c.classes:
                    cds.add((ci, wd))
                for ti in c.teachers:
                    if ti >= 0:
                        tds.add((ti, wd))
        return cds, tds

    def _terms_cost(self, cds, tds, courses, blocks) -> float:
        return (sum(self.class_day_cost(ci, wd) for ci, wd in cds)
                + sum(self.teacher_day_cost(ti, wd) for ti, wd in tds)
                + sum(self.course_cost(k) for k in courses)
                + sum(self.block_cost(b) for b in blocks))

    def total_cost(self) -> float:
        WD = self.W * self.D
        cost = sum(self.class_day_cost(ci, wd) for ci in range(len(self.class_ids)) for wd in range(WD))
        cost += sum(self.teacher_day_cost(ti, wd) for ti in range(len(self.teacher_ids)) for wd in range(WD))
        cost += sum(self.course_cost(k) for k in range(len(self.courses)))
        cost += sum(self.block_cost(b) for b in self.blocks)
        cost += 1000.0 * sum(b.length * sum(self.weight[v] for v in b.weeks) for b in self.blocks if not b.placed)
        return cost

    def cost_parts(self, top: int = 5) -> list[dict]:
        """Strafpunkte je Baustein aus „Prioritäten & Regeln“ – genau die Summanden von :meth:`total_cost`.

        Nur für die Auswertung (einmal je Plan), nie in der Optimierungsschleife. Je Baustein: ``count`` = gewichtete
        Zahl der Verstöße (Wochenmuster eingerechnet), ``points`` = Strafpunkte (Anzahl × Gewicht, Ausnahmen je Klasse
        bzw. Lehrkraft eingerechnet), ``weight`` = daraus der mittlere Gewichtswert, ``top`` = die größten Verursacher.
        Die Summe aller ``points`` ist ``total_cost()``."""
        acc: dict[str, list] = {}

        def add(rid: str, who: str, count: float, points: float) -> None:
            if not points and not count:
                return
            row = acc.setdefault(rid, [0.0, 0.0, defaultdict(float)])
            row[0] += count
            row[1] += points
            row[2][who] += points

        P, D, WD = self.P, self.D, self.W * self.D
        for ci in range(len(self.class_ids)):
            name = self.school.classes[ci].name or self.class_ids[ci]
            g, bl = self.class_grid[ci], self.class_blocked[ci]
            for wd in range(WD):
                if not self.class_avail_day[ci][wd]:
                    continue
                base = wd * P
                first = last = first_avail = -1
                count = 0
                for p in range(P):
                    if first_avail < 0 and not bl[base + p]:
                        first_avail = p
                    if g[base + p] != FREE:
                        if first < 0:
                            first = p
                        last = p
                        count += 1
                w = wd // D
                nv = self.weight[w]
                w_gap, w_late, w_balance = self.class_w[ci][w]
                units = 0.5 * (count - self.class_target[ci][w]) ** 2 * nv
                add("day_balance", name, units, w_balance * units)
                if count == 0:
                    continue
                gaps = sum(1 for p in range(first, last + 1) if g[base + p] == FREE and not bl[base + p]) * nv
                add("class_gap", name, gaps, w_gap * gaps)
                late = max(0, first - first_avail) * nv
                add("late_start", name, late, w_late * late)
        for ti in range(len(self.teacher_ids)):
            name = self.school.teachers[ti].name or self.teacher_ids[ti]
            g, wish = self.teacher_grid[ti], self.teacher_wish[ti]
            for wd in range(WD):
                base = wd * P
                first = last = -1
                count = changes = wished = 0
                prev_site = None
                for p in range(P):
                    u = g[base + p]
                    if u == FREE:
                        continue
                    wished += wish[base + p]
                    if first < 0:
                        first = p
                    last = p
                    count += 1
                    site = self.blocks[u].site
                    if prev_site is not None and site != prev_site:
                        changes += 1
                    prev_site = site
                if count == 0:
                    continue
                w = wd // D
                nv = self.weight[w]
                w_gap, w_site, w_wish = self.teacher_w[ti][w]
                gaps = ((last - first + 1) - count) * nv
                add("teacher_gap", name, gaps, w_gap * gaps)
                site_w = w_site * (NO_COMMUTE_FACTOR if self.teacher_no_commute[ti] else 1.0)
                eff = changes
                if self.teacher_once[ti] and changes > 1:
                    eff += (changes - 1) * (NO_COMMUTE_FACTOR - 1.0)
                add("site_change", name, changes * nv, site_w * eff * nv)
                add("teacher_wish", name, wished * nv, w_wish * wished * nv)
        for k, c in enumerate(self.courses):
            if c.hours > 3:
                continue
            label = self.school.index("courses").get(c.id)
            label = (label.label if label and label.label else c.id)
            cd, cw = self.course_day[k], self.course_w[k]
            for w in range(self.W):
                row = cd[w * D:(w + 1) * D]
                pairs = sum(1 for d in range(D - 1) if row[d] and row[d + 1]) * self.weight[w]
                add("spread", label, pairs, cw[w][3] * pairs)
        courses = self.school.index("courses")
        for b in self.blocks:
            c = self.courses[b.course]
            label = courses[c.id].label if courses.get(c.id) and courses[c.id].label else c.id
            if not b.placed:
                n = b.length * sum(self.weight[v] for v in b.weeks)
                add("unplaced", label, n, 1000.0 * n)
                continue
            cw = self.course_w[b.course]
            split = c.double and b.length == 1 and c.hours >= 2
            end = b.start + b.length - 1
            mid = b.start + (b.length - 1) * 0.5
            for v in b.weeks:
                w_pos, w_core, w_split, _, latest, _ = cw[v]
                nv = self.weight[v]
                add("position", label, mid * nv, w_pos * mid * nv)
                if c.core and end > latest:
                    add("core_late", label, (end - latest) * nv, w_core * (end - latest) * nv)
                if split:
                    add("doubles", label, nv, w_split * nv)
        out = []
        for rid, (count, points, who) in acc.items():
            if rid == "unplaced":
                title, weight_unit = "Unverplante Stunden", "Stunden"
            else:
                title, weight_unit = rl.RULE_BY_ID[rid].title, ""
            out.append({
                "id": rid, "title": title, "count": round(count, 2), "points": round(points, 2),
                "weight": round(points / count, 3) if count else 0.0, "unit": weight_unit,
                "top": [{"name": n, "points": round(v, 1)}
                        for n, v in sorted(who.items(), key=lambda kv: -kv[1])[:top] if v > 0],
            })
        out.sort(key=lambda r: -r["points"])
        return out

    def move_delta(self, b: Block, d: int, s: int, rooms, site) -> float:
        """Kostendifferenz, wenn ``b`` (platziert oder nicht) nach (d, s) geht."""
        days = {d}
        if b.placed:
            days.add(b.day)
        cds, tds = self._terms(b, days)
        before = self._terms_cost(cds, tds, (b.course,), (b,))
        old = self.remove(b) if b.placed else None
        self.place(b, d, s, rooms, site)
        after = self._terms_cost(cds, tds, (b.course,), (b,))
        self.remove(b)
        if old is not None:
            self.place(b, *old)
        return after - before

    # ----------------------------------------------------------- construct
    def _difficulty(self, b: Block) -> float:
        c = self.courses[b.course]
        score = 30 * (len(c.classes) - 1) + 10 * (len(c.teachers) - 1)
        score += 15 * sum(1 for k, _ in c.room_reqs if k != "fixed")
        score += 20 * b.length
        for ti in c.teachers:
            if ti >= 0:
                score += 20 * sum(self.teacher_blocked[ti]) / self.S
        for ci in c.classes:
            score += 40 * sum(self.class_blocked[ci]) / self.S
        score += 5 * (self.W - len(b.weeks))
        return score + self.rng.random()

    def best_slot(self, b: Block, rand: float = 0.0):
        best = None
        for d in self.courses[b.course].days:
            for s in range(self.P - b.length + 1):
                res = self.check(b, d, s)
                if res is None:
                    continue
                delta = self.move_delta(b, d, s, *res)
                if rand:
                    delta += self.rng.random() * rand
                if best is None or delta < best[0]:
                    best = (delta, d, s, res)
        return best

    def _place_best(self, b: Block) -> bool:
        best = self.best_slot(b, rand=0.01)
        if best is None:
            return False
        _, d, s, (rooms, site) = best
        self.place(b, d, s, rooms, site)
        return True

    def _blockers(self, b: Block, d: int, s: int) -> Optional[set[int]]:
        if s + b.length > self.P:
            return None
        c = self.courses[b.course]
        out: set[int] = set()
        for x in self._slots(b, d, s):
            for ci in c.classes:
                if self.class_blocked[ci][x]:
                    return None
                if self.class_grid[ci][x] != FREE:
                    out.add(self.class_grid[ci][x])
            for ti in c.teachers:
                if ti < 0:
                    continue
                if self.teacher_blocked[ti][x]:
                    return None
                if self.teacher_grid[ti][x] != FREE:
                    out.add(self.teacher_grid[ti][x])
        return out

    def _repair(self, b: Block, tries: int = 60) -> bool:
        """Verdrängt bis zu zwei Blöcke, um ``b`` unterzubringen."""
        cands = [(d, s) for d in self.courses[b.course].days for s in range(self.P - b.length + 1)]
        self.rng.shuffle(cands)
        attempts = 0
        for d, s in cands:
            blk = self._blockers(b, d, s)
            if blk is None or len(blk) > 2 or any(self.blocks[x].locked for x in blk):
                continue
            attempts += 1
            if attempts > tries:
                break
            victims = [self.blocks[x] for x in blk]
            olds = [self.remove(v) for v in victims]
            res = self.check(b, d, s)
            if res is not None:
                self.place(b, d, s, *res)
                ok = True
                for v in victims:
                    if not self._place_best(v):
                        ok = False
                        break
                if ok:
                    return True
                for v in victims:
                    if v.placed:
                        self.remove(v)
                self.remove(b)
            for v, old in zip(victims, olds):
                res2 = self.check(v, old[0], old[1])
                if res2 is not None:
                    self.place(v, old[0], old[1], *res2)
                else:  # sollte nicht passieren – zur Sicherheit neu platzieren
                    self._place_best(v) or self._repair(v, tries=10)
        return False

    def _split(self, b: Block) -> list[Block]:
        """Teilt einen Block in je einen Block pro Wochenvariante seines Kurses bzw. in Einzelstunden auf."""
        if len(b.weeks) > 1:
            parts = [Block(0, b.course, b.length, (v,)) for v in b.weeks]
        elif b.length > 1:
            parts = [Block(0, b.course, 1, b.weeks) for _ in range(b.length)]
        else:
            return []
        b.length = 0  # markiert als ersetzt
        self._add_blocks(parts)
        return parts

    def _preplace_locked(self, keep: list[Lesson]) -> dict[tuple[int, int], int]:
        """Übernimmt fixierte Stunden; liefert bereits abgedeckte Stunden je (Kurs, Wochenvariante)."""
        covered: dict[tuple[int, int], int] = defaultdict(int)
        courses = self.school.index("courses")
        for les in keep:
            k = self.course_by_id.get(les.course_id)
            if k is None:
                continue
            c = self.courses[k]
            weeks = tuple(v for v in self.variants_of_members(self.hz.lesson_members(les, courses.get(les.course_id)))
                          if v in c.weeks)
            if not weeks:
                continue
            b = Block(len(self.blocks), k, les.length, weeks, locked=True)
            stored = [self.ridx.get(r) if r else None for r in (les.rooms or [])]
            res = self.check(b, les.day, les.start, stored)
            if res is None:
                self.warnings.append(f"Fixierte Stunde {les.id} ({self.courses[k].id}) kollidiert und wurde verworfen")
                continue
            self.blocks.append(b)
            self.place(b, les.day, les.start, *res)
            for w in weeks:
                covered[(k, w)] += les.length
        return covered

    def generate(self, time_limit: float = 20.0, keep_locked: bool = True,
                 iterations: Optional[int] = None) -> ScheduleResult:
        """Plan erzeugen. Mit ``iterations`` läuft die Optimierung genau so viele Schritte (reproduzierbar, V1)."""
        t0 = time.time()
        keep = [les for les in self.school.lessons if les.locked] if keep_locked else []
        covered = self._preplace_locked(keep)
        new_blocks: list[Block] = []
        for k, c in enumerate(self.courses):
            need = {w: c.hours - covered[(k, w)] for w in c.weeks}
            new_blocks += self._make_blocks(k, need, c.double)
        self._add_blocks(new_blocks)
        todo = sorted(new_blocks, key=self._difficulty, reverse=True)
        self.progress("Konstruktion", 0.0)
        failed: list[Block] = []
        for i, b in enumerate(todo):
            if not self._place_best(b):
                failed.append(b)
            if i % 100 == 0:
                self.progress("Konstruktion", 0.4 * i / max(1, len(todo)))

        self.progress("Reparatur", 0.4)
        queue = failed
        for _ in range(4):
            if not queue:
                break
            nxt = []
            for b in queue:
                if b.length == 0 or b.placed:
                    continue
                if self._place_best(b) or self._repair(b):
                    continue
                parts = self._split(b)
                if not parts:
                    nxt.append(b)
                    continue
                for p in parts:
                    if not (self._place_best(p) or self._repair(p)):
                        nxt.append(p)
            queue = nxt
        # Letzter Ausweg: Fach darf an einem Tag einmal öfter liegen
        for b in queue:
            if b.placed or b.length == 0:
                continue
            c = self.courses[b.course]
            c.max_per_day += 1
            if self._place_best(b) or self._repair(b):
                self.warnings.append(f"{c.id}: musste {c.max_per_day}× an einem Tag gelegt werden")
            else:
                c.max_per_day -= 1

        self.progress("Optimierung", 0.5)
        remaining = max(1.0, time_limit - (time.time() - t0))
        self.optimize(remaining, iterations)
        self.progress("Fertig", 1.0)
        return self.result()

    # ------------------------------------------------------------- optimise
    def _bad_class_days(self) -> list[tuple[int, int]]:
        out = []
        P = self.P
        for ci in range(len(self.class_ids)):
            g, bl = self.class_grid[ci], self.class_blocked[ci]
            for wd in range(self.W * self.D):
                base = wd * P
                occ = [p for p in range(P) if g[base + p] != FREE]
                if occ and any(g[base + p] == FREE and not bl[base + p]
                               for p in range(occ[0], occ[-1] + 1)):
                    out.append((ci, wd))
        return out

    def optimize(self, seconds: float, iterations: Optional[int] = None) -> None:
        """Simulated Annealing nach Zeit oder – mit ``iterations`` – nach genau so vielen Schritten."""
        movable = [b for b in self.blocks if b.placed and not b.locked and b.length > 0]
        if not movable:
            return
        t_end = time.time() + seconds
        temp0, temp = 3.0, 3.0
        it = 0
        bad: list[tuple[int, int]] = []
        start = time.time()
        self.trace = [[0.0, 0, round(self.total_cost(), 1)]]
        next_sample = 1.0 / TRACE_POINTS     # Anteil der Rechenzeit bzw. Schritte
        while True:
            if iterations is not None and it >= iterations:
                break
            it += 1
            if it % 200 == 0:
                if iterations is not None:
                    frac = it / max(1, iterations)
                else:
                    now = time.time()
                    if now >= t_end:
                        break
                    frac = (now - start) / max(1e-6, seconds)
                temp = temp0 * (1 - frac) + 0.01
                if frac >= next_sample:     # Zwischenstand für die Auswertung (höchstens ~60 Mal, kaum Mehraufwand)
                    next_sample = frac + 1.0 / TRACE_POINTS
                    self.trace.append([round(time.time() - start, 2), it, round(self.total_cost(), 1)])
                if it % 2000 == 0:
                    bad = self._bad_class_days()
                    self.progress("Optimierung", 0.5 + 0.5 * frac)
            r = self.rng.random()
            if bad and r < 0.4:
                self._fix_gap_move(self.rng.choice(bad), temp)
            elif r < 0.75:
                self._random_move(self.rng.choice(movable), temp)
            else:
                self._random_swap(self.rng.choice(movable), temp)
        self.iterations = it
        self.trace.append([round(time.time() - start, 2), it, round(self.total_cost(), 1)])

    def _accept(self, delta: float, temp: float) -> bool:
        return delta <= 0 or self.rng.random() < math.exp(-delta / max(temp, 1e-6))

    def _random_move(self, b: Block, temp: float) -> None:
        if not b.placed:
            return
        d = self.rng.choice(self.courses[b.course].days)
        s = self.rng.randrange(self.P - b.length + 1)
        if (d, s) == (b.day, b.start):
            return
        old = self.remove(b)
        res = self.check(b, d, s)
        self.place(b, *old)
        if res is None:
            return
        delta = self.move_delta(b, d, s, *res)
        if self._accept(delta, temp):
            self.remove(b)
            self.place(b, d, s, *res)

    def _fix_gap_move(self, cd: tuple[int, int], temp: float) -> None:
        ci, wd = cd
        P = self.P
        base = wd * P
        g, bl = self.class_grid[ci], self.class_blocked[ci]
        occ = [p for p in range(P) if g[base + p] != FREE]
        if not occ:
            return
        gaps = [p for p in range(occ[0], occ[-1] + 1) if g[base + p] == FREE and not bl[base + p]]
        if not gaps:
            return
        target = self.rng.choice(gaps)
        # Kandidaten: Stunden dieser Klasse (gleicher Tag zuerst: Rand -> Lücke)
        cand = {g[base + occ[0]], g[base + occ[-1]]}
        cand |= {u for u in g if u != FREE}
        cand = [self.blocks[u] for u in cand if not self.blocks[u].locked]
        self.rng.shuffle(cand)
        d = wd % self.D
        for b in cand[:12]:
            for s in (target, target - b.length + 1):
                if s < 0:
                    continue
                old = self.remove(b)
                res = self.check(b, d, s)
                self.place(b, *old)
                if res is None:
                    continue
                delta = self.move_delta(b, d, s, *res)
                if self._accept(delta, temp):
                    self.remove(b)
                    self.place(b, d, s, *res)
                    return
        # Kein direkter Zug möglich: Stunde in die Lücke holen und Kollisionen verdrängen
        for b in cand[:4]:
            if b.length == 1 and self._eject_move(b, d, target, temp):
                return
        # Oder die kürzere Seite der Lücke auf einen anderen Platz verlegen
        before = [p for p in occ if p < target]
        after = [p for p in occ if p > target]
        side = before if len(before) <= len(after) else after
        units = {g[base + p] for p in side}
        if len(units) == 1:
            b = self.blocks[units.pop()]
            if not b.locked:
                old = self.remove(b)
                self.place(b, *old)
                best = self.best_slot(b)
                if best is not None and (best[1], best[2]) != (b.day, b.start) and self._accept(best[0], temp):
                    self.remove(b)
                    self.place(b, best[1], best[2], *best[3])

    def _eject_move(self, b: Block, d: int, s: int, temp: float) -> bool:
        """Setzt ``b`` nach (d, s) und verdrängt dort kollidierende Blöcke (max. 2)."""
        blk = self._blockers(b, d, s)
        if blk is None:
            return False
        blk.discard(b.id)
        if len(blk) > 2 or any(self.blocks[x].locked for x in blk):
            return False
        victims = [self.blocks[x] for x in blk]
        all_days = set(range(self.D))
        cds, tds = self._terms(b, {d, b.day})
        courses = {b.course}
        for v in victims:
            c2, t2 = self._terms(v, all_days)
            cds |= c2
            tds |= t2
            courses.add(v.course)
        moved = [b] + victims
        before = self._terms_cost(cds, tds, courses, moved)
        old_b = self.remove(b)
        olds = [self.remove(v) for v in victims]
        res = self.check(b, d, s)
        ok = res is not None
        if ok:
            self.place(b, d, s, *res)
            for v in victims:
                if not self._place_best(v):
                    ok = False
                    break
        if ok:
            after = self._terms_cost(cds, tds, courses, moved)
            if self._accept(after - before, temp):
                return True
        for v in victims:
            if v.placed:
                self.remove(v)
        if b.placed:
            self.remove(b)
        self.place(b, *old_b)
        for v, o in zip(victims, olds):
            self.place(v, *o)
        return False

    def _random_swap(self, a: Block, temp: float) -> None:
        if not a.placed:
            return
        c = self.courses[a.course]
        ci = self.rng.choice(c.classes)
        wd = self.rng.choice(a.weeks) * self.D + self.rng.choice(c.days)
        p = self.rng.randrange(self.P)
        u = self.class_grid[ci][wd * self.P + p]
        if u == FREE or u == a.id:
            return
        b = self.blocks[u]
        if b.locked or b.length != a.length or b.weeks != a.weeks:
            return
        days = {a.day, b.day}
        cds1, tds1 = self._terms(a, days)
        cds2, tds2 = self._terms(b, days)
        cds, tds = cds1 | cds2, tds1 | tds2
        courses = {a.course, b.course}
        before = self._terms_cost(cds, tds, courses, (a, b))
        oa, ob = self.remove(a), self.remove(b)
        ra = self.check(a, ob[0], ob[1])
        if ra is not None:
            self.place(a, ob[0], ob[1], *ra)
            rb = self.check(b, oa[0], oa[1])
            if rb is not None:
                self.place(b, oa[0], oa[1], *rb)
                after = self._terms_cost(cds, tds, courses, (a, b))
                if self._accept(after - before, temp):
                    return
                self.remove(b)
            self.remove(a)
        self.place(a, *oa)
        self.place(b, *ob)

    # --------------------------------------------------------------- output
    def _block_spec(self, b: Block, c: _CourseInfo) -> tuple[list[int], Optional[dict]]:
        """Wochenangabe eines Blocks: leer, wenn er alle Wochenvarianten seines Kurses abdeckt, sonst die laufenden
        Wochen seiner Varianten (Rhythmus bei regelmäßigem Abstand)."""
        if set(b.weeks) >= set(c.weeks):
            return [], None
        return self.hz.to_spec(i for v in b.weeks for i in self.groups[v])

    def result(self) -> ScheduleResult:
        lessons: list[Lesson] = []
        unplaced = []
        n = 0
        for b in self.blocks:
            if b.length == 0:
                continue
            c = self.courses[b.course]
            weeks, rhythm = self._block_spec(b, c)
            if not b.placed:
                unplaced.append({"course": c.id, "length": b.length, "weeks": weeks, "rhythm": rhythm,
                                 "weeks_text": wk.describe_spec(weeks, rhythm, self.hz.lab)})
                continue
            n += 1
            lessons.append(Lesson(
                id=f"L{n}", course_id=c.id, day=b.day, start=b.start, length=b.length,
                weeks=weeks, rhythm=rhythm,
                rooms=[self.room_ids[r] if r is not None else None for r in b.rooms],
                locked=b.locked,
            ))
        stats = self.stats()
        stats["unplaced"] = len(unplaced)
        return ScheduleResult(lessons, unplaced, stats, self.warnings, list(getattr(self, "trace", [])))

    def stats(self) -> dict:
        P = self.P
        V = max(1, self.W)
        class_gaps = teacher_gaps = site_changes = 0.0
        core_late = 0
        for ci in range(len(self.class_ids)):
            g, bl = self.class_grid[ci], self.class_blocked[ci]
            for wd in range(self.W * self.D):
                base = wd * P
                occ = [p for p in range(P) if g[base + p] != FREE]
                if occ:
                    class_gaps += self.weight[wd // self.D] * sum(1 for p in range(occ[0], occ[-1] + 1)
                                                                  if g[base + p] == FREE and not bl[base + p])
        for ti in range(len(self.teacher_ids)):
            g = self.teacher_grid[ti]
            for wd in range(self.W * self.D):
                base = wd * P
                occ = [p for p in range(P) if g[base + p] != FREE]
                if occ:
                    wt = self.weight[wd // self.D]
                    teacher_gaps += wt * ((occ[-1] - occ[0] + 1) - len(occ))
                    sites = [self.blocks[g[base + p]].site for p in occ]
                    site_changes += wt * sum(1 for a, b in zip(sites, sites[1:]) if a != b)
        for b in self.blocks:
            if b.placed and b.length and self.courses[b.course].core:
                cw = self.course_w[b.course]
                if any(b.start + b.length - 1 > cw[v][4] for v in b.weeks):
                    core_late += 1
        def num(x: float):
            return int(round(x)) if abs(x - round(x)) < 1e-6 else round(x, 1)

        return {
            "lessons": sum(1 for b in self.blocks if b.placed and b.length),
            "hours_per_week": num(sum(b.length * sum(len(self.groups[v]) for v in b.weeks)
                                      for b in self.blocks if b.placed) / max(1, len(self.hz))),
            # Durchschnitt je Schulwoche wie ``timetable.validate_school`` (die Gewichte summieren sich zur Zahl der
            # Wochenmuster, deshalb durch V teilen)
            "class_gaps": num(class_gaps / V),
            "teacher_gaps": num(teacher_gaps / V),
            "site_changes": num(site_changes / V),
            "core_late": core_late,
            "cost": round(self.total_cost(), 1),
            "iterations": getattr(self, "iterations", 0),
            "variants": self.W,
        }


def generate(school: School, time_limit: float = 20.0, seed: int = 1,
             keep_locked: bool = True, progress=None, iterations: Optional[int] = None) -> ScheduleResult:
    """Plan erzeugen (``iterations`` = feste Zahl an Optimierungsschritten, reproduzierbar)."""
    return Scheduler(school, seed=seed, progress=progress).generate(time_limit, keep_locked, iterations)


def _generate_worker(data: dict, time_limit: float, seed: int, keep_locked: bool,
                     iterations: Optional[int] = None) -> dict:
    school = School.from_dict(data)
    res = Scheduler(school, seed=seed).generate(time_limit, keep_locked, iterations)
    return {"lessons": [les.to_dict() for les in res.lessons], "unplaced": res.unplaced,
            "stats": res.stats, "warnings": res.warnings, "seed": seed, "trace": res.trace}


def generate_best_of(school: School, time_limit: float = 30.0, workers: int = 0, seed: int = 1,
                     keep_locked: bool = True, progress=None, iterations: Optional[int] = None) -> ScheduleResult:
    """Startet mehrere Generatorläufe mit verschiedenen Seeds parallel (je CPU-Kern einen)
    und liefert den besten Plan (wenigste unverplante Stunden, dann geringste Kosten)."""
    import multiprocessing as mp
    import os
    from concurrent.futures import ProcessPoolExecutor, wait

    workers = workers or max(1, min(4, (os.cpu_count() or 1)))
    if workers == 1:
        res = generate(school, time_limit, seed, keep_locked, progress, iterations)
        res.stats["seed"] = seed
        res.stats["runs"] = 1
        res.runs = [_run_info(seed, res.stats, res.trace, 0, True)]
        return res
    progress = progress or (lambda msg, frac: None)
    data = school.to_dict()
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as ex:
        futs = [ex.submit(_generate_worker, data, time_limit, seed + i, keep_locked, iterations)
                for i in range(workers)]
        while True:
            done, _ = wait(futs, timeout=1.0)
            if len(done) == len(futs):
                break
            progress(f"{workers} parallele Läufe", min(0.99, (time.time() - t0) / max(1.0, time_limit + 5)))
        results = [f.result() for f in futs]
    best = min(results, key=lambda r: (r["stats"].get("unplaced", 0), r["stats"].get("cost", 0)))
    progress("Fertig", 1.0)
    # Startwert = der eingestellte; der Startwert des besten Laufs steht in ``best_seed``/``runs``
    best["stats"]["seed"] = seed
    best["stats"]["best_seed"] = best["seed"]
    best["stats"]["runs"] = workers
    runs = [_run_info(r["seed"], r["stats"], r.get("trace", []), i, r is best) for i, r in enumerate(results)]
    return ScheduleResult([Lesson.from_dict(x) for x in best["lessons"]], best["unplaced"],
                          best["stats"], best["warnings"], best.get("trace", []), runs)


def _run_info(seed: int, stats: dict, trace: list, index: int, best: bool) -> dict:
    return {"index": index, "seed": seed, "cost": stats.get("cost"), "unplaced": stats.get("unplaced", 0),
            "iterations": stats.get("iterations", 0), "best": best, "trace": trace}
