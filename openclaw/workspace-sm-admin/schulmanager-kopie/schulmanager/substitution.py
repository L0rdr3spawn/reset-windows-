"""Vertretungsplan-Engine (Live-Umplanung bei Abwesenheiten).

Grundidee
---------
Für einen Tag wird der reguläre Stundenplan in *Einheiten* zerlegt:
``(Lesson, Stunde, Kursteil)``. Doppelstunden werden also stundenweise
betrachtet und können teilweise betroffen sein. Danach wird in Phasen
entschieden:

1. Manuelle Entscheidungen (``school.overrides``) – haben immer Vorrang.
2. Klausuren markieren (dürfen nie still entfallen).
3. Klassenstufe ≥ ``policy.cancel_min_grade``: betroffene **Randstunden**
   entfallen iterativ von außen nach innen (``edge_strategy="cancel"``);
   Lücken in der Mitte werden – bei ``middle_strategy="shift_first"`` –
   durch **Verlegung** einer nicht betroffenen Rand-Einzelstunde der Klasse
   geschlossen, so wandert der Ausfall an den Rand.
4. Klausuren und jüngere Klassen: immer Vertretung / Betreuung.
5. Übrige Einheiten: Vertretung (qualifiziert) → Mitbetreuung (Kopplung) →
   Betreuung (fachfremd) → Entfall (am Rand ohne, in der Mitte mit Warnung).
6. Pausenaufsichten abwesender Lehrkräfte (``duties.duty_replacements``),
   Raumsperren und durch Klausuren belegte Räume (``raumaenderung``): Ersatzraum gleichen Typs; ist keiner frei
   (z. B. der einzige IT-Raum), wird die Stunde mit einer anderen Stunde der Klasse **getauscht**, zu der ein
   passender Raum frei ist (beide Einträge ``verlegung``); sonst Ausweichraum mit Warnung. Klausur-Infos.

„Unterricht findet nicht statt“ (``Absence(kind="lesson", ref="<kurs>[#<teil>]")``): die
betroffenen Einheiten werden wie bei fehlender Lehrkraft entschieden (Rand → Entfall, Mitte →
Verlegung …, jüngere Klassen → Betreuung), die Lehrkraft ist dabei aber **frei** und kann
anderswo vertreten. Einträge tragen ``"dropped": true``.

Das Ergebnis hängt nur von den Eingaben ab (``school``, Datum, Historie).
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Iterable, Optional

from . import commute
from . import weeks as wk
from .calendar_utils import (as_date, break_time, class_days, day_kind, is_school_day, monday_of, period_label,
                             period_time, week_info)
from .models import Course, Lesson, School, Teacher

KINDS = ("vertretung", "betreuung", "mitbetreuung", "entfall", "verlegung", "raumaenderung",
         "klasse_abwesend", "aufsicht", "klausur")
SUB_KINDS = ("vertretung", "betreuung")          # zählen als Vertretung (Limits, Fairness)
# Einträge, die als „Vertretungsfall“ der (ursprünglichen) Lehrkraft zählen (``absent_teacher_details.cases``)
CASE_KINDS = ("vertretung", "betreuung", "mitbetreuung", "entfall", "aufsicht")

# Status einer Einheit
_NORMAL = "normal"            # findet wie geplant statt (ggf. Raumänderung)
_AFFECTED = "affected"        # Lehrkraft fehlt, noch nicht entschieden
_SUB = "sub"                  # vertreten / betreut / mitbetreut
_CANCELLED = "cancelled"      # entfällt
_CLASS_ABSENT = "class_absent"  # alle Klassen abwesend
_MOVED = "moved"              # an eine andere Stunde verlegt (alte Position)
_SHIFTED = "shifted"          # verlegte Stunde an neuer Position
_FREE = frozenset({_CLASS_ABSENT, _CANCELLED, _MOVED})   # Klasse hat in dieser Einheit nichts
_ACTIVE = frozenset({_NORMAL, _SUB, _SHIFTED, _AFFECTED})  # Raum belegt


def _natural(s: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s or ""))


def split_lesson_ref(ref: str) -> tuple[str, Optional[int]]:
    """Referenz einer ``lesson``-Abwesenheit → ``(course_id, part)``.

    ``"<course_id>"`` = ganzer Kurs (``part=None``), ``"<course_id>#<part>"`` = nur dieser Kursteil
    (0-basiert). ``ValueError`` bei ungültiger Teilangabe (z. B. ``"K1#x"``).
    """
    cid, sep, part = (ref or "").partition("#")
    cid, part = cid.strip(), part.strip()
    if not sep:
        return cid, None
    if not part.isdigit():
        raise ValueError(f"Ungültiger Kursteil „{part}“")
    return cid, int(part)


# --------------------------------------------------------------------- DayPlan
@dataclass
class DayPlan:
    """Vertretungsplan eines Tages (Format siehe ARCHITECTURE.md §4)."""
    date: date
    weekday: int
    week_no: int
    holiday: Optional[str] = None
    entries: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    absent_teachers: list[str] = field(default_factory=list)
    absent_classes: list[str] = field(default_factory=list)
    # je abwesender Lehrkraft: {teacher, name, full_day, periods (leer bei ganztägig), cases} – nie ein Grund
    absent_teacher_details: list[dict] = field(default_factory=list)
    # je Klasse in ``absent_classes``: {class, name, source: absence|rhythm, full_day, periods, reason}
    absent_class_details: list[dict] = field(default_factory=list)
    # R3: Woche (WeekInfo der Schule) und Art des Tages (unterricht | kein_unterrichtstag | ferien | feiertag)
    week_info: dict = field(default_factory=dict)
    day_kind: str = "unterricht"

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(), "weekday": self.weekday, "week_no": self.week_no,
            "holiday": self.holiday,
            "week_info": dict(self.week_info), "day_kind": self.day_kind,
            "entries": [dict(e) for e in self.entries], "warnings": list(self.warnings),
            "stats": dict(self.stats), "absent_teachers": list(self.absent_teachers),
            "absent_classes": list(self.absent_classes),
            "absent_teacher_details": [dict(d) for d in self.absent_teacher_details],
            "absent_class_details": [dict(d) for d in self.absent_class_details],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DayPlan":
        return cls(date=as_date(data["date"]), weekday=int(data.get("weekday", 0)),
                   week_no=int(data.get("week_no", 0)),
                   holiday=data.get("holiday"), entries=list(data.get("entries", [])),
                   warnings=list(data.get("warnings", [])), stats=dict(data.get("stats", {})),
                   absent_teachers=list(data.get("absent_teachers", [])),
                   absent_classes=list(data.get("absent_classes", [])),
                   absent_teacher_details=[dict(d) for d in data.get("absent_teacher_details") or []],
                   absent_class_details=[dict(d) for d in data.get("absent_class_details") or []],
                   week_info=dict(data.get("week_info") or {}), day_kind=data.get("day_kind") or "unterricht")

    def substitution_counts(self) -> dict[str, int]:
        """Vertretungen (vertretung + betreuung) je Lehrkraft an diesem Tag."""
        out: Counter = Counter()
        for e in self.entries:
            if e.get("kind") in SUB_KINDS and e.get("substitute"):
                out[e["substitute"]] += 1
        return dict(out)


#: Einträge, die im Bestätigungsmodus (``settings.substitution_confirm``) erst nach Freigabe gelten: automatisch
#: berechnete Vertretungen/Betreuungen (nicht von Hand entschiedene)
PROPOSAL_KINDS = ("vertretung", "betreuung")


def is_proposal(entry: dict) -> bool:
    """Automatisch berechneter Vertretungsvorschlag (noch keine Entscheidung der Vertretungsplanung)?"""
    return entry.get("kind") in PROPOSAL_KINDS and bool(entry.get("substitute")) and not entry.get("manual")


def strip_proposals(plan: "DayPlan") -> "DayPlan":
    """Plan ohne die noch nicht freigegebenen Vorschläge (Sicht für alle außer der Vertretungsplanung)."""
    import dataclasses
    entries = [e for e in plan.entries if not is_proposal(e)]
    if len(entries) == len(plan.entries):
        return plan
    stats = _empty_stats()
    for e in entries:
        if e.get("kind") in stats:
            stats[e["kind"]] += 1
    stats["warnungen"] = plan.stats.get("warnungen", 0)
    if "entfall_mitte" in plan.stats:
        stats["entfall_mitte"] = plan.stats["entfall_mitte"]
    return dataclasses.replace(plan, entries=entries, stats=stats)


def mark_proposals(plan: dict) -> dict:
    """Kopie des Plan-Dicts, bei der Vorschläge ``"proposed": true`` tragen (Sicht der Vertretungsplanung)."""
    out = dict(plan)
    out["entries"] = [{**e, "proposed": True} if is_proposal(e) else e for e in plan.get("entries") or []]
    out["proposals"] = sum(1 for e in out["entries"] if e.get("proposed"))
    return out


def absence_cases(entries: Iterable[dict]) -> Counter:
    """Vertretungsfälle je ursprünglicher Lehrkraft: vertretene, betreute oder entfallene eigene Stunden und
    vertretene Aufsichten (ohne Unterricht, der ohnehin nicht stattfindet, ``dropped``)."""
    out: Counter = Counter()
    for e in entries:
        if e.get("kind") in CASE_KINDS and e.get("teacher") and not e.get("dropped"):
            out[e["teacher"]] += 1
    return out


def _empty_stats() -> dict:
    out = {k: 0 for k in KINDS}
    out["entfall_mitte"] = 0
    out["warnungen"] = 0
    return out


# ----------------------------------------------------------------------- Items
class _Item:
    """Eine Planungseinheit (Lesson, Stunde, Kursteil)."""
    __slots__ = ("lesson", "course", "period", "part", "teacher", "room", "site", "classes", "subject",
                 "grade", "status", "kind", "sub", "new_room", "note", "warning", "manual", "exam",
                 "moved_from", "origin", "reason", "dropped")

    def __init__(self, lesson: Lesson, course: Course, period: int, part: int, teacher: Optional[str],
                 room: Optional[str], site: str, classes: list[str], subject: str, grade: int):
        self.lesson = lesson
        self.course = course
        self.period = period
        self.part = part
        self.teacher = teacher
        self.room = room
        self.site = site
        self.classes = classes
        self.subject = subject
        self.grade = grade
        self.status = _NORMAL
        self.kind: Optional[str] = None
        self.sub: Optional[str] = None
        self.new_room: Optional[str] = None
        self.note = ""
        self.warning = False
        self.manual = False
        self.exam = None
        self.moved_from: Optional[int] = None
        self.origin: Optional[_Item] = None
        self.reason = ""
        self.dropped = False          # Unterricht findet laut ``lesson``-Abwesenheit nicht statt

    @property
    def key(self) -> tuple[str, int, int]:
        return (self.lesson.id, self.period, self.part)

    @property
    def eff_room(self) -> Optional[str]:
        return self.new_room or self.room

    @property
    def coupled(self) -> bool:
        return len(self.course.parts) > 1

    def label(self) -> str:
        cls = "/".join(self.classes) or "?"
        return f"{cls} {self.period + 1}. Std. ({self.subject}, {self.teacher or '–'})"


@dataclass
class _Cand:
    score: float
    teacher: Teacher
    reasons: list[str]
    qualified: bool


# ----------------------------------------------------------------------- Engine
class _Engine:
    def __init__(self, school: School, day: date, history: Optional[dict[str, int]] = None):
        self.school = school
        self.st = school.settings
        self.policy = school.settings.policy
        self.day = day
        self.iso = day.isoformat()
        self.wd = day.weekday()
        self.real_week = wk.real_week(school, day)   # laufende Woche (Grundlage aller Wochenangaben)
        self.aidx = wk.ActiveIndex(school)
        self.P = max(1, self.st.periods)
        self.T = max(0, int(self.st.site_travel_periods or 0))
        self.commute_special = commute.special(self.st, school.teachers)
        self.history = dict(history or {})
        self.teachers = school.index("teachers")
        self.teacher_list = sorted(school.teachers, key=lambda t: t.id)
        self.classes = school.index("classes")
        self.rooms = school.index("rooms")
        self.subjects = school.index("subjects")
        self.courses = school.index("courses")
        self.warnings: list[str] = []
        self.items: list[_Item] = []
        self.by_key: dict[tuple[str, int, int], _Item] = {}
        self.lesson_items: dict[str, list[_Item]] = {}
        self.course_items: dict[tuple[str, int], list[_Item]] = {}
        self.class_items: dict[str, list[list[_Item]]] = {}
        self.t_busy: dict[str, dict[int, list[_Item]]] = {}
        self.t_freed: dict[str, dict[int, str]] = {}
        self.t_absent: dict[str, tuple[set[int], str]] = {}
        self.t_blocked_cache: dict[str, set[int]] = {}
        self._probing = False
        self.t_wish_cache: dict[str, set[int]] = {}
        self.t_classes: dict[str, set[str]] = {}
        self.t_subjects = {t.id: set(t.subjects) for t in school.teachers}
        self.t_duty: dict[str, dict[int, str]] = {}
        self.c_absent: dict[str, dict[int, str]] = {}
        # Klassen, die heute als „nicht im Haus“ gelten: gemeldete Abwesenheit oder ganztägig laut Rhythmus
        # (Teilsperren wie „Abendklasse erst ab 16:00“ zählen nicht)
        self.c_absent_day: set[str] = set()
        # Herkunft für ``absent_class_details``: gemeldete Abwesenheit (Stunden, Gründe) bzw. ganztägiger Rhythmus
        self.c_reported: dict[str, tuple[set[int], list[str]]] = {}
        self.c_rhythm: dict[str, list[str]] = {}
        # entfallender Unterricht (``lesson``-Abwesenheiten): Kurs → [(Kursteil | None = alle, Stunden, Grund)]
        self.l_dropped: dict[str, list[tuple[Optional[int], set[int], str]]] = {}
        self.r_absent: dict[str, set[int]] = {}
        self.r_exam: dict[str, dict[int, str]] = {}   # Raum → Stunde → Kurs der Klausur, die ihn belegt
        self.room_use: Counter = Counter()
        self.subs_today: Counter = Counter()
        self.cosup: set[tuple[str, int]] = set()
        self.duty_overrides: dict[str, Any] = {}

    # ------------------------------------------------------------- building
    def build(self) -> None:
        self._load_absences()
        self._load_lessons()
        for c in self.school.courses:
            for part in c.parts:
                if part.teacher:
                    self.t_classes.setdefault(part.teacher, set()).update(c.classes)
        self._load_duties()

    def _load_absences(self) -> None:
        P, day = self.P, self.day
        all_p = set(range(P))
        for a in self.school.absences:
            try:
                if not (date.fromisoformat(a.date_from) <= day <= date.fromisoformat(a.date_to)):
                    continue
            except (TypeError, ValueError):
                continue
            periods = {p for p in a.periods if 0 <= p < P} if a.periods else set(all_p)
            if not periods:
                continue
            reason = a.reason or ""
            if a.kind == "teacher":
                old = self.t_absent.get(a.ref)
                if old:
                    self.t_absent[a.ref] = (old[0] | periods, old[1] or reason)
                else:
                    self.t_absent[a.ref] = (periods, reason)
            elif a.kind == "class":
                if self.wd not in class_days(self.school, self.classes.get(a.ref)):
                    continue        # kein Unterrichtstag der Klasse
                self.c_absent_day.add(a.ref)
                slot = self.c_absent.setdefault(a.ref, {})
                for p in periods:
                    slot.setdefault(p, reason or "Klasse abwesend")
                rep = self.c_reported.setdefault(a.ref, (set(), []))
                rep[0].update(periods)
                if reason and reason not in rep[1]:
                    rep[1].append(reason)
            elif a.kind == "room":
                self.r_absent.setdefault(a.ref, set()).update(periods)
            elif a.kind == "lesson":
                # leere ``periods`` = alle Stunden des Kurses an dem Tag (= alle Stunden des Tages)
                try:
                    cid, part = split_lesson_ref(a.ref)
                except ValueError:
                    continue
                if cid:
                    self.l_dropped.setdefault(cid, []).append((part, periods, reason))
        self._load_event_absences()
        for c in self.school.classes:
            if not c.unavailable or self.wd not in class_days(self.school, c):
                continue
            blocked = 0
            notes: list[str] = []
            for p in range(P):
                for r in c.unavailable:
                    if r.matches(self.real_week, self.wd, p):
                        note = r.note or "Klasse laut Rhythmus nicht da"
                        self.c_absent.setdefault(c.id, {}).setdefault(p, note)
                        blocked += p < c.max_periods_per_day
                        if note not in notes:
                            notes.append(note)
                        break
            if blocked and blocked >= min(P, c.max_periods_per_day):
                self.c_absent_day.add(c.id)
                self.c_rhythm[c.id] = notes

    def _load_event_absences(self) -> None:
        """Termine mit Lehrkräften (Fortbildung, Exkursion …) → die Lehrkräfte fehlen in den Stunden des Termins."""
        from .teacher_profile import period_spans, to_minutes
        spans = None
        for ev in self.school.events:
            if not ev.teachers or ev.kind == "pflicht" or not ev.covers(self.day):
                continue
            periods = set(range(self.P))
            if ev.time_from:
                if spans is None:
                    spans = period_spans(self.st)
                try:
                    t0 = to_minutes(ev.time_from)
                    t1 = to_minutes(ev.time_to, allow_24=True) if ev.time_to else 24 * 60
                except ValueError:
                    t0, t1 = 0, 24 * 60
                first, last = ev.date_from, ev.date_to or ev.date_from
                if self.iso != first:
                    t0 = 0              # Folgetage eines mehrtägigen Termins: ab Tagesbeginn …
                if self.iso != last:
                    t1 = 24 * 60        # … bis Tagesende
                periods = {p for p in range(self.P) if p < len(spans) and spans[p] and spans[p][0] < t1 and spans[p][1] > t0}
            if not periods:
                continue
            reason = f"Termin: {ev.title}"
            for tid in ev.teachers:
                old = self.t_absent.get(tid)
                self.t_absent[tid] = (old[0] | periods, old[1] or reason) if old else (set(periods), reason)

    def _lesson_active(self, les: Lesson, course: Course) -> bool:
        """Zentrale Aktiv-Logik (``weeks.lesson_active_in``, laufende Woche); an Tagen ohne Unterricht aller Klassen des
        Kurses findet der Block nicht statt."""
        if not self.aidx.active_on(les, course, self.day):
            return False
        return any(self.wd in class_days(self.school, self.classes.get(c)) for c in course.classes) \
            or not course.classes

    def _load_lessons(self) -> None:
        P = self.P
        rooms, classes = self.rooms, self.classes
        for les in self.school.lessons:
            if les.day != self.wd:
                continue
            course = self.courses.get(les.course_id)
            if course is None or not course.parts or not self._lesson_active(les, course):
                continue
            cls = list(course.classes)
            grades = [classes[c].grade for c in cls if c in classes]
            grade = min(grades) if grades else 0
            base_site = ""
            for r in les.rooms:
                if r and r in rooms and rooms[r].site:
                    base_site = rooms[r].site
                    break
            if not base_site:
                for c in cls:
                    if c in classes and classes[c].site:
                        base_site = classes[c].site
                        break
            litems = self.lesson_items.setdefault(les.id, [])
            for p in range(max(0, les.start), min(P, les.start + max(1, les.length))):
                for i, part in enumerate(course.parts):
                    room = les.rooms[i] if i < len(les.rooms) else None
                    site = rooms[room].site if room in rooms and rooms[room].site else base_site
                    it = _Item(les, course, p, i, part.teacher, room, site, cls, part.subject, grade)
                    self._classify(it)
                    self.items.append(it)
                    self.by_key[it.key] = it
                    litems.append(it)
                    self.course_items.setdefault((course.id, p), []).append(it)
                    for c in cls:
                        rows = self.class_items.get(c)
                        if rows is None:
                            rows = self.class_items[c] = [[] for _ in range(P)]
                        rows[p].append(it)

    def _classify(self, it: _Item) -> None:
        p = it.period
        reasons = [self.c_absent.get(c, {}).get(p) for c in it.classes]
        if it.classes and all(reasons):
            it.status = _CLASS_ABSENT
            it.reason = reasons[0] or "Klasse abwesend"
            if it.teacher and not self.absent(it.teacher, p):
                self.t_freed.setdefault(it.teacher, {})[p] = f"Klasse {'/'.join(it.classes)} abwesend"
            return
        self._room_take(it.room, p)
        drop = self._drop_reason(it) if self.l_dropped else None
        if drop is not None:
            # Unterricht findet nicht statt: wie eine fehlende Lehrkraft entscheiden (Rand/Mitte/Betreuung),
            # die Lehrkraft ist aber nicht abwesend, sondern frei und steht für Vertretungen zur Verfügung
            it.status = _AFFECTED
            it.dropped = True
            it.reason = drop
            if it.teacher and not self.absent(it.teacher, p):
                self.t_freed.setdefault(it.teacher, {})[p] = "Unterricht entfällt"
            return
        if it.teacher and self.absent(it.teacher, p):
            it.status = _AFFECTED
            return
        if it.teacher:
            self._engage(it.teacher, p, it)

    def _drop_reason(self, it: _Item) -> Optional[str]:
        """Grund (ggf. ``""``), wenn die Einheit laut ``lesson``-Abwesenheit entfällt, sonst ``None``."""
        for part, periods, reason in self.l_dropped.get(it.course.id, ()):
            if (part is None or part == it.part) and it.period in periods:
                return reason
        return None

    @staticmethod
    def drop_note(X: _Item, text: str) -> str:
        """Hinweis einer entfallenden Einheit: „Unterricht entfällt (Grund) – …“ (sonst ``text`` unverändert)."""
        if not X.dropped:
            return text
        head = "Unterricht entfällt" + (f" ({X.reason})" if X.reason else "")
        return f"{head} – {text}" if text else head

    def _load_duties(self) -> None:
        breaks = self.st.breaks
        areas = self.school.index("areas")
        for d in self.school.duties:
            if d.day != self.wd or not d.teacher:
                continue
            if not wk.duty_active_on(self.school, d, self.day):
                continue
            if not 0 <= d.break_index < len(breaks):
                continue
            a = int(breaks[d.break_index].get("after", -1))
            if self.absent(d.teacher, a) or self.absent(d.teacher, a + 1):
                continue
            area = areas.get(d.area)
            self.t_duty.setdefault(d.teacher, {})[d.break_index] = area.site if area else ""

    # ------------------------------------------------------------ primitives
    def absent(self, tid: str, p: int) -> bool:
        a = self.t_absent.get(tid)
        return bool(a and p in a[0])

    def blocked(self, tid: str) -> set[int]:
        out = self.t_blocked_cache.get(tid)
        if out is None:
            t = self.teachers.get(tid)
            out = set()
            if t and t.unavailable:
                out = {p for p in range(self.P)
                       if any(r.matches(self.real_week, self.wd, p) for r in t.unavailable)}
            self.t_blocked_cache[tid] = out
        return out

    def wish_free(self, tid: str) -> set[int]:
        out = self.t_wish_cache.get(tid)
        if out is None:
            t = self.teachers.get(tid)
            wishes = getattr(t, "wishes", None) or []
            out = {p for p in range(self.P) if any(r.matches(self.real_week, self.wd, p) for r in wishes)}
            self.t_wish_cache[tid] = out
        return out

    def _engage(self, tid: str, p: int, it: _Item) -> None:
        self.t_busy.setdefault(tid, {}).setdefault(p, []).append(it)

    def _release(self, tid: Optional[str], p: int, it: _Item) -> None:
        if not tid:
            return
        lst = self.t_busy.get(tid, {}).get(p)
        if lst and it in lst:
            lst.remove(it)
            if not lst:
                del self.t_busy[tid][p]

    def busy_at(self, tid: str, p: int) -> list[_Item]:
        return self.t_busy.get(tid, {}).get(p) or []

    def _room_take(self, room: Optional[str], p: int) -> None:
        if room:
            self.room_use[(room, p)] += 1

    def _room_free(self, room: Optional[str], p: int) -> None:
        if room and self.room_use[(room, p)] > 0:
            self.room_use[(room, p)] -= 1

    def room_free_at(self, room: Optional[str], p: int, ignore: Optional[_Item] = None) -> bool:
        if not room or p in self.r_absent.get(room, ()) or p in self.r_exam.get(room, ()):
            return False
        use = self.room_use.get((room, p), 0)
        if ignore is not None and ignore.eff_room == room and ignore.status in _ACTIVE:
            use -= 1
        return use <= 0

    def room_site(self, room: Optional[str]) -> str:
        r = self.rooms.get(room) if room else None
        return r.site if r else ""

    def presence(self, tid: str) -> set[int]:
        """Stunden, in denen die Lehrkraft ohnehin im Haus ist (Einsätze + freigesetzte Stunden)."""
        out = {q for q, lst in self.t_busy.get(tid, {}).items() if lst}
        out.update(self.t_freed.get(tid, {}))
        return out

    def _breaks_near(self, p: int, span: int) -> list[int]:
        out = []
        for b, brk in enumerate(self.st.breaks):
            a = int(brk.get("after", -99))
            if p - span <= a <= p + span - 1:
                out.append(b)
        return out

    def travel_ok(self, tid: str, p: int, site: str, ignore: Optional[_Item] = None) -> bool:
        T = self.T
        if not site or not (T or self.commute_special):
            return True
        busy = self.t_busy.get(tid, {})
        teacher = self.teachers.get(tid)
        if self.commute_special and teacher is not None:
            # Wegezeit je Standortpaar und Mindestpause der Lehrkraft (commute.py)
            for q, items in busy.items():
                if q == p:
                    continue
                for it in items:
                    if it is ignore or (ignore is not None and it.origin is ignore):
                        continue
                    if it.site and it.site != site and not (
                            commute.change_ok(self.st, teacher, it.site, q, site, p) if q < p
                            else commute.change_ok(self.st, teacher, site, p, it.site, q)):
                        return False
        for q in (range(p - T, p + T + 1) if not (self.commute_special and teacher is not None) else ()):
            if q == p:
                continue
            for it in busy.get(q, ()):
                if it is ignore or (ignore is not None and it.origin is ignore):
                    continue
                if it.site and it.site != site:
                    return False
        duties = self.t_duty.get(tid)
        if duties:
            for b in self._breaks_near(p, T):
                s = duties.get(b)
                if s and s != site:
                    return False
        return True

    # ----------------------------------------------------------- candidates
    def describe_busy(self, items: list[_Item]) -> str:
        it = items[0]
        what = "Vertretung" if it.status == _SUB else "Verlegung" if it.status == _SHIFTED else "Unterricht"
        return f"{what} {it.subject} {'/'.join(it.classes)}"

    def evaluate(self, t: Teacher, X: _Item, relax: bool = False, full: bool = False
                 ) -> tuple[bool, float, list[str], bool]:
        """Prüft Lehrkraft ``t`` als Vertretung für ``X``: (frei, Score, Gründe, qualifiziert)."""
        tid, p = t.id, X.period
        qualified = X.subject in self.t_subjects.get(tid, ())
        problems: list[str] = []
        if self.absent(tid, p):
            problems.append("abwesend")
        elif p in self.blocked(tid):
            problems.append("Sperrzeit")
        busy = self.busy_at(tid, p)
        if busy:
            problems.append("belegt: " + self.describe_busy(busy))
        if t.sites and X.site and X.site not in t.sites:
            problems.append(f"nicht am Standort {X.site} eingesetzt")
        if X.site:
            mode = commute.teacher_mode(t)
            if mode == "never":
                other = {it.site for q, lst in self.t_busy.get(tid, {}).items() for it in lst if it.site} - {X.site}
                if other:
                    problems.append("pendelt nicht zwischen Standorten")
            elif mode == "once":
                sites = {q: lst[0].site for q, lst in self.t_busy.get(tid, {}).items() if lst}
                sites[p] = X.site
                if len(commute.day_changes(sites)) > 1:
                    problems.append("würde mehr als einmal am Tag den Standort wechseln")
        if problems and not full:
            return False, 0.0, problems, qualified
        if not problems and not self.travel_ok(tid, p, X.site):
            problems.append("Wegezeit zwischen Standorten reicht nicht")
        today = self.subs_today.get(tid, 0)
        week = self.history.get(tid, 0) + today
        engaged = [q for q, lst in self.t_busy.get(tid, {}).items() if lst]
        if not relax:
            if today >= self.policy.max_subs_per_day:
                problems.append("Tageslimit Vertretungen erreicht")
            if week >= t.max_subs_per_week:
                problems.append("Wochenlimit Vertretungen erreicht")
            if len(engaged) >= t.max_per_day:
                problems.append("Tageshöchststunden erreicht")
        if problems and not full:
            return False, 0.0, problems, qualified
        score, reasons = self._score(t, X, qualified, week, today)
        return not problems, score, problems + reasons, qualified

    def _score(self, t: Teacher, X: _Item, qualified: bool, week: int, today: int) -> tuple[float, list[str]]:
        tid, p = t.id, X.period
        s = 0.0
        reasons: list[str] = []
        if qualified:
            s += 40
            reasons.append(f"Fach {X.subject}")
        known = self.t_classes.get(tid, set()).intersection(X.classes)
        if known:
            s += 15
            reasons.append("kennt " + ", ".join(sorted(known, key=_natural)))
        if any(self.classes[c].class_teacher == tid for c in X.classes if c in self.classes):
            s += 5
            reasons.append("Klassenleitung")
        freed = self.t_freed.get(tid, {})
        present = self.presence(tid)
        if p in freed:
            s += 30
            reasons.append(f"freigesetzt ({freed[p]})")
        if not present:
            s -= 40
            reasons.append("müsste extra kommen")
        elif p not in freed:
            lo, hi = min(present), max(present)
            if lo < p < hi:
                s += 20
                reasons.append("Springstunde (ohnehin im Haus)")
            elif p < lo:
                s -= 4 + 6 * (lo - p - 1)
                reasons.append("müsste früher kommen")
            elif p > hi:
                s -= 4 + 6 * (p - hi - 1)
                reasons.append("müsste länger bleiben")
        if present and X.site:
            sites = {it.site for q in present for it in self.busy_at(tid, q) if it.site}
            if X.site in sites:
                s += 5
                reasons.append("gleicher Standort")
            elif sites:
                s -= 10
                reasons.append("anderer Standort")
        if week:
            s -= 6 * week * 25 / max(5, t.max_hours or 25)
            reasons.append(f"{week} Vertretung(en) diese Woche")
        if today:
            s -= 8 * today
        if p in self.wish_free(tid):
            s -= 8
            reasons.append("Wunsch: frei")
        bonus, why = (0.0, "") if self._probing else self._block_bonus(t, X, week, today)
        if bonus:
            s += bonus
            reasons.append(why)
        return s, reasons

    def _block_neighbours(self, X: _Item) -> list[_Item]:
        """Nachbarstunden desselben Blocks (gleiche Lehrveranstaltung und Kursteil, Stunde davor/danach)."""
        return [Y for Y in self.lesson_items.get(X.lesson.id, ())
                if Y is not X and Y.part == X.part and abs(Y.period - X.period) == 1]

    def _block_bonus(self, t: Teacher, X: _Item, week: int, today: int) -> tuple[float, str]:
        """Bonus für die Vertretung des ganzen Blocks (Doppelstunde): Die Lehrkraft vertritt die Nachbarstunde bereits
        oder wäre dort ebenfalls frei. Ohne Bonus bei Fairness-Grenzen, damit niemand darüber hinaus belastet wird."""
        tid = t.id
        bonus, why = 0.0, ""
        for Y in self._block_neighbours(X):
            if Y.status == _SUB and Y.sub == tid and Y.kind != "mitbetreuung":
                return 40.0, "übernimmt auch die Nachbarstunde (ganzer Block)"
            if Y.status != _AFFECTED or bonus:
                continue
            engaged = sum(1 for lst in self.t_busy.get(tid, {}).values() if lst)
            if (today + 1 >= self.policy.max_subs_per_day or week + 1 >= t.max_subs_per_week
                    or engaged + 1 >= t.max_per_day):
                continue
            self._probing = True          # Nachbarprüfung ohne eigenen Blockbonus (sonst Endlosschleife)
            try:
                free = self.evaluate(t, Y)[0]
            finally:
                self._probing = False
            if not free:
                continue
            bonus, why = 30.0, "wäre auch in der Nachbarstunde frei (ganzer Block)"
        return bonus, why

    def inhouse_free(self, tid: str, p: int) -> bool:
        """Lehrkraft ist zu ``p`` ohnehin im Haus (Springstunde oder freigesetzt)."""
        if p in self.t_freed.get(tid, {}):
            return True
        present = self.presence(tid)
        return bool(present) and min(present) < p < max(present)

    def best(self, X: _Item, *, qualified_only: bool = False, inhouse_only: bool = False,
             relax: bool = False) -> Optional[_Cand]:
        best: Optional[_Cand] = None
        for t in self.teacher_list:
            if t.id == X.teacher:
                continue
            ok, score, reasons, q = self.evaluate(t, X, relax=relax)
            if not ok or (qualified_only and not q):
                continue
            if inhouse_only and not self.inhouse_free(t.id, X.period):
                continue
            if best is None or score > best.score:
                best = _Cand(score, t, reasons, q)
        return best

    # --------------------------------------------------------------- actions
    def assign(self, X: _Item, cand: _Cand, note: str = "") -> None:
        tid = cand.teacher.id
        X.status = _SUB
        X.kind = "vertretung" if cand.qualified else "betreuung"
        X.sub = tid
        self._engage(tid, X.period, X)
        self.subs_today[tid] += 1
        orig = self.teachers.get(X.teacher)
        # bei entfallendem Unterricht fehlt die Lehrkraft nicht → kein „Vertretung für …“
        who = "" if X.dropped else orig.name if orig else (X.teacher or "")
        if X.kind == "vertretung":
            X.note = note or self.drop_note(X, f"Vertretung für {who}" if who else "Vertretung")
        else:
            X.note = note or self.drop_note(X, "Betreuung (fachfremd)")
            self._betreuung_room(X)
        if X.exam is not None:
            X.note += " – Klausuraufsicht"
        self._note_split(X, tid)

    def _extend_block(self, X: _Item, min_grade: int) -> None:
        """Übernimmt die Lehrkraft eine Stunde, die immer gedeckt werden muss (Klausur, jüngere Klasse), bekommt sie
        die noch offene Nachbarstunde desselben Blocks gleich mit, sofern sie dort frei ist – sonst nähme eine
        Stunde einer anderen Klasse sie dazwischen weg."""
        if X.status != _SUB or X.kind not in ("vertretung", "betreuung") or not X.sub:
            return
        t = self.teachers.get(X.sub)
        if t is None:
            return
        for Y in self._block_neighbours(X):
            if Y.status != _AFFECTED or not (Y.exam is not None or Y.grade < min_grade):
                continue
            ok, score, reasons, qualified = self.evaluate(t, Y)
            if ok:
                self.assign(Y, _Cand(score, t, reasons, qualified))

    def _note_split(self, X: _Item, tid: str) -> None:
        """Wird ein Block auf zwei Lehrkräfte verteilt, steht der Grund im Hinweis beider Stunden."""
        for Y in self._block_neighbours(X):
            if Y.status == _SUB and Y.kind in ("vertretung", "betreuung") and Y.sub and Y.sub != tid:
                text = " – Block geteilt: keine Lehrkraft für beide Stunden frei"
                for Z in (X, Y):
                    if text not in Z.note:
                        Z.note += text

    def _betreuung_room(self, X: _Item) -> None:
        """Fachfremde Betreuung im Fachraum (z. B. Sporthalle) → möglichst in den Klassenraum."""
        room = self.rooms.get(X.room) if X.room else None
        if room is None or room.type in ("Klassenraum", "Kursraum") or len(X.classes) != 1:
            return
        cls = self.classes.get(X.classes[0])
        home = cls.home_room if cls else None
        if home and home != X.room and self.room_free_at(home, X.period) and self.room_site(home) in ("", X.site):
            self._room_free(X.eff_room, X.period)
            X.new_room = home
            self._room_take(home, X.period)

    def cancel(self, X: _Item, note: str, warning: bool = False, manual: bool = False) -> None:
        was_active = X.status in _ACTIVE
        if X.status in (_NORMAL, _SHIFTED) and X.teacher and not self.absent(X.teacher, X.period):
            self._release(X.teacher, X.period, X)
            self.t_freed.setdefault(X.teacher, {})[X.period] = "Unterricht entfällt"
        if X.status == _SUB and X.sub:
            self._release(X.sub, X.period, X)
        if was_active:
            self._room_free(X.eff_room, X.period)
        if not manual:
            note = self.drop_note(X, note)
        X.status = _CANCELLED
        X.kind = "entfall"
        X.sub = None
        X.note = note
        X.manual = X.manual or manual
        X.warning = warning
        if warning:
            self.warnings.append(f"{X.label()}: {note}")

    def try_cover(self, X: _Item, *, unqualified: bool, relax: bool) -> bool:
        """Vertretung (beste Lehrkraft, Fach zählt im Score) → Mitbetreuung → Betreuung (fachfremd).

        ``unqualified=False``: nur fachlich qualifizierte Lehrkräfte. ``relax``: als letzter Ausweg
        Vertretungs-/Tageslimits ignorieren (harte Bedingungen bleiben).
        """
        cand = self.best(X, qualified_only=not unqualified)
        if cand is not None and cand.qualified:
            self.assign(X, cand)
            return True
        if X.coupled and self.try_cosupervise(X):
            return True
        if cand is not None:
            self.assign(X, cand)
            return True
        if relax:
            cand = self.best(X, qualified_only=not unqualified, relax=True)
            if cand is not None:
                self.assign(X, cand)
                X.note += " (über Vertretungslimit)"
                self.warnings.append(f"{X.label()}: {cand.teacher.id} über Vertretungslimit eingesetzt")
                return True
        return False

    def try_cosupervise(self, X: _Item) -> bool:
        p = X.period
        options = []
        for Y in self.lesson_items.get(X.lesson.id, ()):
            if Y.period != p or Y.part == X.part or Y.status != _NORMAL or not Y.teacher:
                continue
            if (Y.teacher, p) in self.cosup or self.absent(Y.teacher, p):
                continue
            options.append((0 if Y.subject == X.subject else 1, Y.part, Y))
        if not options:
            return False
        options.sort(key=lambda o: (o[0], o[1]))
        Y = options[0][2]
        X.status = _SUB
        X.kind = "mitbetreuung"
        X.sub = Y.teacher
        self.cosup.add((Y.teacher, p))
        if Y.eff_room and Y.eff_room != X.eff_room:
            self._room_free(X.eff_room, p)
            X.new_room = Y.eff_room
            self._room_take(X.new_room, p)
        part = X.course.parts[Y.part]
        X.note = self.drop_note(X, f"Mitbetreuung durch {Y.teacher} ({part.label or part.subject})")
        if X.exam is not None:
            X.note += " – Klausuraufsicht"
        return True

    # ------------------------------------------------------------ edge logic
    def _free_for(self, items: list[_Item], X: _Item) -> bool:
        for it in items:
            if it is X or it.status in _FREE:
                continue
            if it.course is X.course and it.part != X.part and X.coupled:
                continue  # paralleler Kursteil = andere Schülergruppe
            return False
        return True

    def edge(self, X: _Item) -> Optional[str]:
        """``"start"``/``"end"``/``"rand"``, wenn ``X`` für alle beteiligten Klassen am Tagesrand liegt."""
        p, P = X.period, self.P
        sides = set()
        for c in X.classes:
            if p in self.c_absent.get(c, {}):
                continue
            rows = self.class_items.get(c)
            if rows is None:
                continue
            before = all(self._free_for(rows[q], X) for q in range(p))
            if before:
                sides.add("start")
                continue
            after = all(self._free_for(rows[q], X) for q in range(p + 1, P))
            if not after:
                return None
            sides.add("end")
        if sides == {"end"}:
            return "end"
        if sides == {"start"} or not sides:
            return "start"
        return "rand"

    @staticmethod
    def edge_note(side: str, short: bool = False) -> str:
        """Hinweis zum Randentfall; ``short`` ohne „Entfall …“ (für „Unterricht entfällt (Grund) – …“)."""
        if side == "start":
            return "Unterricht beginnt später" if short else "Entfall am Tagesanfang – Unterricht beginnt später"
        if side == "end":
            return "Unterricht endet früher" if short else "Entfall am Tagesende – Unterricht endet früher"
        return "Randstunde des Schultags" if short else "Entfall am Rand des Schultags"

    def resolve_edge(self, X: _Item, side: str, final: bool) -> bool:
        strategy = self.policy.edge_strategy
        note = self.edge_note(side, short=X.dropped)
        if strategy == "cancel":
            self.cancel(X, note)
            return True
        if not final:
            return False
        if strategy == "substitute_if_qualified":
            cand = self.best(X, qualified_only=True, inhouse_only=True)
            if cand is not None:
                self.assign(X, cand)
            else:
                self.cancel(X, note)
            return True
        if not self.try_cover(X, unqualified=self.policy.allow_unqualified, relax=False):
            self.cancel(X, note)
        return True

    def edge_pass(self, pending: list[_Item], final: bool) -> None:
        changed = True
        while changed:
            changed = False
            for X in pending:
                if X.status != _AFFECTED:
                    continue
                side = self.edge(X)
                if side and self.resolve_edge(X, side, final):
                    changed = True

    def resolve_middle(self, X: _Item, final: bool) -> bool:
        shift_first = self.policy.middle_strategy != "substitute_first"
        if shift_first and self.try_shift(X):
            return True
        if not final:
            return False
        if self.try_cover(X, unqualified=self.policy.allow_unqualified, relax=False):
            return True
        if not shift_first and self.try_shift(X):
            return True
        if self.try_cover(X, unqualified=self.policy.allow_unqualified, relax=True):
            return True
        self.cancel(X, "Entfall in der Tagesmitte – keine Vertretung gefunden", warning=True)
        return True

    def older_loop(self, pending: list[_Item], final: bool) -> None:
        pending = sorted(pending, key=lambda x: (_natural(x.classes[0] if x.classes else ""), x.period, x.part))
        while True:
            self.edge_pass(pending, final)
            progressed = False
            for X in pending:
                if X.status != _AFFECTED or self.edge(X):
                    continue
                if self.resolve_middle(X, final):
                    progressed = True
                    break
            if not progressed:
                return

    # ----------------------------------------------------------------- shift
    def try_shift(self, X: _Item) -> bool:
        """Verlegt eine nicht betroffene Rand-Einzelstunde der Klasse in die Lücke ``X``."""
        if len(X.classes) != 1 or X.coupled or X.exam is not None or X.manual:
            return False
        c, p = X.classes[0], X.period
        rows = self.class_items.get(c)
        if rows is None or any(it is not X and it.status not in _FREE for it in rows[p]):
            return False
        occupied = [q for q in range(self.P) if q != p and any(it.status not in _FREE for it in rows[q])]
        if not occupied or not (occupied[0] < p < occupied[-1]):
            return False
        for e in (occupied[-1], occupied[0]):
            cands = [it for it in rows[e] if it.status not in _FREE]
            if len(cands) != 1:
                continue
            M = cands[0]
            if not self._movable(M, X):
                continue
            room = self._shift_room(M, X)
            if room is False:
                continue
            self._do_shift(X, M, room)
            return True
        return False

    def _movable(self, M: _Item, X: _Item) -> bool:
        if M.status != _NORMAL or M.manual or M.exam is not None or M.lesson is X.lesson:
            return False
        if X.dropped and M.course is X.course:
            return False  # entfallenden Kurs nicht über eine andere Stunde in die Lücke zurückholen
        if M.lesson.length != 1 or len(M.course.classes) != 1 or M.coupled:
            return False
        t = self.teachers.get(M.teacher) if M.teacher else None
        if t is None:
            return False
        p = X.period
        if self.absent(t.id, p) or p in self.blocked(t.id) or self.busy_at(t.id, p):
            return False
        if t.sites and X.site and X.site not in t.sites:
            return False
        return self.travel_ok(t.id, p, X.site, ignore=M)

    def _shift_room(self, M: _Item, X: _Item):
        p = X.period
        part = M.course.parts[M.part]
        subj = self.subjects.get(M.subject)
        rtype = part.room_type or (subj.room_type if subj else None)

        def ok(r: Optional[str]) -> bool:
            return bool(r) and self.room_free_at(r, p, ignore=X) and self.room_site(r) in ("", X.site or self.room_site(r))

        if rtype:
            pool = [M.room] + sorted(r.id for r in self.school.rooms
                                     if r.type == rtype and (not X.site or r.site == X.site))
            for r in pool:
                if ok(r):
                    return r
            return False
        cls = self.classes.get(X.classes[0])
        own_type = self.rooms[M.room].type if M.room in self.rooms else "Klassenraum"
        allowed = {"Klassenraum", "Kursraum", own_type}
        pool = [X.eff_room, cls.home_room if cls else None, M.room]
        for r in pool:
            if ok(r) and r in self.rooms and self.rooms[r].type in allowed:
                return r
        if not M.room and not X.eff_room:
            return None
        return False

    def _do_shift(self, X: _Item, M: _Item, room: Optional[str]) -> None:
        e, p = M.period, X.period
        c = X.classes[0]
        mt = self.teachers.get(M.teacher)
        when = "vorgezogen" if e > p else "nach hinten verlegt"
        instead = f"dafür {M.subject} ({M.teacher}) aus der {e + 1}. Stunde {when}"
        self.cancel(X, instead if X.dropped else f"Entfall – {instead}")
        M.status = _MOVED
        M.note = f"verlegt in die {p + 1}. Stunde"
        self._release(M.teacher, e, M)
        self._room_free(M.eff_room, e)
        N = _Item(M.lesson, M.course, p, M.part, M.teacher, M.room, self.room_site(room) or X.site,
                  M.classes, M.subject, M.grade)
        N.status = _SHIFTED
        N.kind = "verlegung"
        N.moved_from = e
        N.origin = M
        N.new_room = room if room != M.room else None
        N.note = f"{M.subject} ({mt.name if mt else M.teacher}) aus der {e + 1}. Stunde {when}"
        self.items.append(N)
        self.by_key[N.key] = N
        self.lesson_items.setdefault(N.lesson.id, []).append(N)
        self.class_items[c][p].append(N)
        self._engage(M.teacher, p, N)
        self._room_take(N.eff_room, p)

    # ------------------------------------------------------------- overrides
    def apply_overrides(self) -> None:
        latest: dict[tuple[str, int, int], Any] = {}
        for ov in self.school.overrides:
            if str(ov.date)[:10] != self.iso:
                continue
            latest[(ov.lesson_id, ov.period, ov.part)] = ov
        for key, ov in latest.items():
            X = self.by_key.get(key)
            if X is None:
                if any(d.id == ov.lesson_id for d in self.school.duties):
                    self.duty_overrides[ov.lesson_id] = ov
                else:
                    self.warnings.append(f"Manuelle Änderung {ov.id}: Stunde {ov.lesson_id} "
                                         f"({ov.period + 1}. Std., Teil {ov.part}) findet an diesem Tag nicht statt")
                continue
            self._apply_override(X, ov)

    def _apply_override(self, X: _Item, ov) -> None:
        p = X.period
        action = ov.action or "substitute"
        X.manual = True
        if action == "cancel":
            note = ov.note or self.drop_note(X, "Entfall (manuelle Entscheidung)")
            if X.exam is not None:
                self.warnings.append(f"{X.label()}: Klausur entfällt durch manuelle Entscheidung")
            self.cancel(X, note, warning=X.exam is not None, manual=True)
            return
        if action == "keep":
            if X.status in (_AFFECTED, _CLASS_ABSENT):
                if X.status == _CLASS_ABSENT:
                    self._room_take(X.room, p)
                if X.teacher and (X.status == _CLASS_ABSENT or X.dropped):
                    # Unterricht findet doch statt → Lehrkraft ist nicht mehr frei
                    self.t_freed.get(X.teacher, {}).pop(p, None)
                X.status = _NORMAL
                X.dropped = False
                X.reason = ""
                if X.teacher:
                    self._engage(X.teacher, p, X)
            if ov.room:
                self._set_room(X, ov.room)
                X.note = ov.note or "Raumänderung (manuell)"
            return
        if action == "room":
            if ov.room:
                self._set_room(X, ov.room)
                X.note = ov.note or "Raumänderung (manuell)"
            return
        # substitute
        tid = ov.teacher
        if not tid:
            self.warnings.append(f"Manuelle Vertretung {ov.id} ohne Lehrkraft – automatisch geplant")
            X.manual = False
            return
        t = self.teachers.get(tid)
        if t is None:
            self.warnings.append(f"Manuelle Vertretung {ov.id}: Lehrkraft {tid} unbekannt")
            X.manual = False
            return
        if tid == X.teacher:  # eigene Lehrkraft eingetragen = Unterricht findet statt
            self._apply_override(X, type(ov)(**{**ov.to_dict(), "action": "keep"}))
            return
        if self.absent(tid, p):
            self.warnings.append(f"{X.label()}: manuell eingeteilte Lehrkraft {tid} ist abwesend")
        elif self.busy_at(tid, p):
            self.warnings.append(f"{X.label()}: manuell eingeteilte Lehrkraft {tid} ist bereits belegt "
                                 f"({self.describe_busy(self.busy_at(tid, p))})")
        if X.status == _CLASS_ABSENT:
            self.warnings.append(f"{X.label()}: Vertretung eingetragen, obwohl die Klasse abwesend ist")
            self._room_take(X.room, p)
        elif X.status == _NORMAL and X.teacher and X.teacher != tid:
            self._release(X.teacher, p, X)
            self.t_freed.setdefault(X.teacher, {})[p] = "durch manuelle Vertretung ersetzt"
        elif X.status == _NORMAL and X.teacher == tid:
            if ov.room:
                self._set_room(X, ov.room)
            return
        X.status = _SUB
        X.sub = tid
        X.kind = "vertretung" if X.subject in self.t_subjects.get(tid, ()) else "betreuung"
        self._engage(tid, p, X)
        self.subs_today[tid] += 1
        X.note = ov.note or self.drop_note(X, "Vertretung (manuell)" if X.kind == "vertretung"
                                           else "Betreuung (manuell)")
        if ov.room:
            self._set_room(X, ov.room)

    def _set_room(self, X: _Item, room: str) -> None:
        if X.status in _ACTIVE:
            self._room_free(X.eff_room, X.period)
            self._room_take(room, X.period)
        X.new_room = room if room != X.room else None

    # ------------------------------------------------------------------ exams
    def mark_exams(self) -> list[Any]:
        todays = []
        for ex in self.school.exams:
            if str(ex.date)[:10] != self.iso:
                continue
            todays.append(ex)
            if ex.room:
                for p in range(ex.start, ex.start + max(1, ex.length)):
                    self.r_exam.setdefault(ex.room, {})[p] = ex.course_id
            for p in range(ex.start, ex.start + max(1, ex.length)):
                for it in self.course_items.get((ex.course_id, p), ()):
                    if ex.part is None or it.part == ex.part:
                        it.exam = ex
        return todays

    # ------------------------------------------------------------- rooms
    def room_changes(self) -> None:
        if not self.r_absent and not self.r_exam:
            return
        for X in list(self.items):
            if X.status not in (_NORMAL, _SUB, _SHIFTED):
                continue
            r = X.eff_room
            why = self._room_unavailable(X, r) if r else None
            if why is None:
                continue
            new = self._replacement_room(X, r)
            if new is None and self._swap_for_room(X, r, why):
                continue
            self._room_free(r, X.period)
            if new:
                X.new_room = new if new != X.room else None
                self._room_take(new, X.period)
                if X.status == _NORMAL:
                    X.note = X.note or f"{why} – Ersatzraum {new}"
            else:
                fallback = self._fallback_room(X, r)
                X.warning = True
                X.new_room = fallback if fallback and fallback != X.room else None
                if fallback:
                    self._room_take(fallback, X.period)
                    text = f"{why} – kein gleichwertiger Raum frei, Ausweichraum {fallback} (bitte prüfen)"
                else:
                    text = f"{why} – kein Ersatzraum frei"
                X.note = (X.note + "; " if X.note else "") + text
                self.warnings.append(f"{X.label()}: {text}")
            if X.status == _NORMAL:
                X.kind = "raumaenderung"

    def _room_unavailable(self, X: _Item, r: str, p: Optional[int] = None) -> Optional[str]:
        """Grund, warum Raum ``r`` für ``X`` zur Stunde ``p`` (Standard: Stunde von ``X``) nicht nutzbar ist."""
        p = X.period if p is None else p
        if p in self.r_absent.get(r, ()):
            return f"Raum {r} gesperrt"
        exam_course = self.r_exam.get(r, {}).get(p)
        if exam_course is not None and exam_course != X.course.id:
            return f"Raum {r} durch Klausur belegt"
        return None

    def _fallback_room(self, X: _Item, r: str) -> Optional[str]:
        """Letzter Ausweg bei gesperrtem Fachraum: Klassenraum der Klasse oder ein freier Klassen-/Kursraum."""
        room = self.rooms.get(r)
        if room is None or room.type in ("Klassenraum", "Kursraum"):
            return None
        site = room.site or X.site
        pool: list[str] = [self.classes[c].home_room for c in X.classes
                           if c in self.classes and self.classes[c].home_room]
        homes = {c.home_room for c in self.school.classes if c.home_room}
        pool += sorted((x.id for x in self.school.rooms if x.type in ("Klassenraum", "Kursraum")
                        and (not site or x.site == site)), key=lambda rid: (rid in homes, _natural(rid)))
        return next((cand for cand in pool if self.room_free_at(cand, X.period)), None)

    def _teacher_free(self, tid: Optional[str], p: int, site: str, partner: _Item) -> bool:
        """Lehrkraft ``tid`` kann zur Stunde ``p`` unterrichten, wenn ``partner`` von dort weggetauscht wird."""
        if not tid:
            return True
        if self.absent(tid, p) or p in self.blocked(tid):
            return False
        if any(it is not partner for it in self.busy_at(tid, p)):
            return False
        t = self.teachers.get(tid)
        if t is not None and t.sites and site and site not in t.sites:
            return False
        return self.travel_ok(tid, p, site, ignore=partner)

    def _swap_for_room(self, X: _Item, r: str, why: str) -> bool:
        """Gesperrter Fachraum ohne Ersatz: Stunde ``X`` mit einer anderen Einzelstunde ``Y`` derselben Klasse am
        selben Tag tauschen, wenn zu deren Zeit ein Raum des benötigten Typs frei ist (nächstgelegene Stunde zuerst).
        Beide Lehrkräfte müssen zur neuen Zeit können; ``Y`` braucht zur alten Zeit von ``X`` einen passenden Raum."""
        if (X.status != _NORMAL or X.manual or X.exam is not None or len(X.classes) != 1 or X.coupled
                or X.lesson.length != 1):
            return False
        room = self.rooms.get(r)
        if room is None or room.type in ("Klassenraum", "Kursraum"):
            return False
        rtype, site = room.type, room.site or X.site
        same_type = sorted((x.id for x in self.school.rooms if x.type == rtype and (not site or x.site == site)),
                           key=lambda rid: (rid != r, _natural(rid)))
        c, p = X.classes[0], X.period
        rows = self.class_items.get(c)
        if rows is None:
            return False
        for q in sorted(range(self.P), key=lambda q: (abs(q - p), q)):
            if q == p or q in self.c_absent.get(c, {}):
                continue
            others = [it for it in rows[q] if it.status not in _FREE]
            if len(others) != 1:
                continue
            Y = others[0]
            if (Y.status != _NORMAL or Y.manual or Y.exam is not None or Y.coupled or Y.lesson.length != 1
                    or len(Y.course.classes) != 1 or Y.lesson is X.lesson):
                continue
            room_x = next((cand for cand in same_type if self.room_free_at(cand, q, ignore=Y)
                           and self._room_unavailable(X, cand, q) is None), None)
            if room_x is None:
                continue
            if not (self._teacher_free(X.teacher, q, self.room_site(room_x) or X.site, Y)
                    and self._teacher_free(Y.teacher, p, Y.site, X)):
                continue
            room_y = self._swap_room_for(Y, p, exclude=room_x)
            if room_y is False:
                continue
            self._do_swap(X, Y, room_x, room_y, why)
            return True
        return False

    def _swap_room_for(self, Y: _Item, p: int, exclude: str):
        """Raum für ``Y`` zur Stunde ``p``: eigener Raum, sonst gleicher Typ bzw. Klassenraum (``False`` = keiner)."""
        own = Y.eff_room
        if not own:
            return None
        cands = [own]
        room = self.rooms.get(own)
        rtype = room.type if room else "Klassenraum"
        if rtype in ("Klassenraum", "Kursraum"):
            cands += [self.classes[c].home_room for c in Y.classes
                      if c in self.classes and self.classes[c].home_room]
        cands += sorted((x.id for x in self.school.rooms if x.type == rtype and (not Y.site or x.site == Y.site)),
                        key=_natural)
        for cand in cands:
            if cand and cand != exclude and self.room_free_at(cand, p) and self._room_unavailable(Y, cand, p) is None:
                return cand
        return False

    def _do_swap(self, X: _Item, Y: _Item, room_x: str, room_y: Optional[str], why: str) -> None:
        p, q = X.period, Y.period
        tx, ty = self.teachers.get(X.teacher), self.teachers.get(Y.teacher)
        for it, at in ((X, p), (Y, q)):
            self._release(it.teacher, at, it)
            self._room_free(it.eff_room, at)
            it.status = _MOVED
        X.note = f"getauscht in die {q + 1}. Stunde ({why})"
        Y.note = f"getauscht in die {p + 1}. Stunde"
        new_x = self._place_shifted(X, q, room_x)
        new_x.note = (f"{X.subject} ({tx.name if tx else X.teacher}) aus der {p + 1}. Stunde – getauscht mit "
                      f"{Y.subject}, weil {why}")
        new_y = self._place_shifted(Y, p, room_y)
        new_y.note = (f"{Y.subject} ({ty.name if ty else Y.teacher}) aus der {q + 1}. Stunde – getauscht mit "
                      f"{X.subject} ({why})")

    def _place_shifted(self, M: _Item, p: int, room: Optional[str]) -> _Item:
        N = _Item(M.lesson, M.course, p, M.part, M.teacher, M.room, self.room_site(room) or M.site,
                  M.classes, M.subject, M.grade)
        N.status = _SHIFTED
        N.kind = "verlegung"
        N.moved_from = M.period
        N.origin = M
        N.new_room = room if room and room != M.room else None
        self.items.append(N)
        self.by_key[N.key] = N
        self.lesson_items.setdefault(N.lesson.id, []).append(N)
        for c in N.classes:
            if c in self.class_items:
                self.class_items[c][p].append(N)
        if M.teacher:
            self._engage(M.teacher, p, N)
        self._room_take(N.eff_room, p)
        return N

    def _replacement_room(self, X: _Item, r: str) -> Optional[str]:
        room = self.rooms.get(r)
        rtype = room.type if room else "Klassenraum"
        site = room.site if room else X.site
        pool: list[str] = []
        if rtype == "Klassenraum":
            pool += [self.classes[c].home_room for c in X.classes if c in self.classes and self.classes[c].home_room]
        homes = {c.home_room for c in self.school.classes if c.home_room}
        # Räume, die nicht Klassenraum einer anderen Klasse sind, zuerst
        pool += sorted((x.id for x in self.school.rooms if x.type == rtype and (not site or x.site == site)),
                       key=lambda rid: (rid in homes, _natural(rid)))
        for cand in pool:
            if cand != r and self.room_free_at(cand, X.period):
                return cand
        return None

    # ----------------------------------------------------------------- duties
    def duty_entries(self) -> list[dict]:
        if not self.school.duties:
            return []
        from .duties import duty_replacements
        busy = {tid: {q: lst[0].site for q, lst in per.items() if lst} for tid, per in self.t_busy.items()}
        presence = {tid: sorted(self.presence(tid)) for tid in set(self.t_busy) | set(self.t_freed)}
        plan_busy = {
            "weekday": self.wd,
            "busy": busy, "presence": presence,
            "absent": {tid: sorted(v[0]) for tid, v in self.t_absent.items()},
            "history": self.history, "subs_today": dict(self.subs_today),
            "overrides": self.duty_overrides,
        }
        entries = duty_replacements(self.school, self.day, plan_busy)
        for e in entries:
            if e.get("warning"):
                self.warnings.append(f"Pausenaufsicht {e.get('area_name') or e.get('area')} ({e.get('period_label')}): "
                                     f"{e.get('note')}")
        return entries

    # ---------------------------------------------------------------- output
    def entry(self, X: _Item, kind: str) -> dict:
        p = X.period
        part = X.course.parts[X.part] if X.part < len(X.course.parts) else None
        out = {
            "id": f"{self.iso}:{X.lesson.id}:{p}:{X.part}",
            "date": self.iso, "period": p, "period_label": period_label(p), "time": period_time(self.st, p),
            "kind": kind, "classes": list(X.classes), "subject": X.subject, "teacher": X.teacher,
            "substitute": X.sub, "room": X.room,
            "new_room": X.new_room if X.new_room and X.new_room != X.room else None,
            "moved_from": X.moved_from, "lesson_id": X.lesson.id, "part": X.part,
            "note": X.note, "warning": bool(X.warning), "manual": bool(X.manual), "site": X.site,
            "course_id": X.course.id, "part_label": part.label if part else "",
        }
        if X.dropped:
            out["dropped"] = True     # Unterricht findet laut ``lesson``-Abwesenheit nicht statt
        return out

    def exam_entry(self, ex) -> dict:
        course = self.courses.get(ex.course_id)
        p = ex.start
        parts = [ex.part] if ex.part is not None else list(range(len(course.parts))) if course else []
        covering = [it for q in range(ex.start, ex.start + max(1, ex.length))
                    for it in self.course_items.get((ex.course_id, q), ()) if ex.part is None or it.part == ex.part]
        first = next((it for it in covering if it.period == p), covering[0] if covering else None)
        teacher = None
        subject = None
        if course and parts and 0 <= parts[0] < len(course.parts):
            teacher = course.parts[parts[0]].teacher
            subject = course.parts[parts[0]].subject
        notes, warning = [], False
        if not covering:
            notes.append("Kurs hat zu dieser Zeit laut Plan keinen Unterricht")
            warning = True
        subs = sorted({it.sub for it in covering if it.status == _SUB and it.sub})
        if any(it.status in (_CANCELLED, _MOVED) for it in covering):
            notes.append("Unterricht zur Klausurzeit entfällt – bitte klären")
            warning = True
        if any(it.status == _CLASS_ABSENT for it in covering):
            notes.append("Klasse abwesend – Klausur verschieben")
            warning = True
        if subs:
            notes.append("Aufsicht: " + ", ".join(subs))
        title = ex.title or "Klausur"
        if warning:
            self.warnings.append(f"Klausur {title} ({course.label if course else ex.course_id}): " + "; ".join(notes))
        return {
            "id": f"{self.iso}:{ex.id}:{p}:{ex.part or 0}",
            "date": self.iso, "period": p, "period_label": period_label(p), "time": period_time(self.st, p),
            "kind": "klausur", "classes": list(course.classes) if course else [], "subject": subject,
            "teacher": teacher, "substitute": subs[0] if subs else None,
            "room": ex.room or (first.eff_room if first else None), "new_room": None, "moved_from": None,
            "lesson_id": first.lesson.id if first else None, "part": ex.part or 0,
            "note": f"{title} ({ex.length} Std.)" + (" – " + "; ".join(notes) if notes else ""),
            "warning": warning, "manual": False, "site": first.site if first else "",
            "course_id": ex.course_id, "exam_id": ex.id, "exam_part": ex.part, "length": ex.length,
            "title": title,
        }

    # -------------------------------------------------------------------- run
    def run(self) -> DayPlan:
        self.build()
        exams = self.mark_exams()
        self.apply_overrides()
        min_grade = self.policy.cancel_min_grade
        affected = [x for x in self.items if x.status == _AFFECTED]
        must = [x for x in affected if x.exam is not None or x.grade < min_grade]
        older = [x for x in affected if x.exam is None and x.grade >= min_grade]
        # Phase 1: Ränder streichen / Lücken durch Verlegung schließen (verbraucht keine Vertretungen)
        self.older_loop(older, final=False)
        # Phase 2: Klausuren und jüngere Klassen – immer Vertretung/Betreuung
        must.sort(key=lambda x: (x.exam is None, x.period, _natural(x.classes[0] if x.classes else ""), x.part))
        for X in must:
            if X.status != _AFFECTED:
                continue
            if not self.try_cover(X, unqualified=True, relax=True):
                why = "Klausur ohne Aufsicht" if X.exam is not None else "Unterstufe ohne Betreuung"
                self.cancel(X, f"Keine Lehrkraft frei – {why}, bitte manuell regeln", warning=True)
            else:
                self._extend_block(X, min_grade)
        # Phase 3: Rest der älteren Klassen
        self.older_loop([x for x in older if x.status == _AFFECTED], final=True)
        # Phase 4: Räume, Aufsichten, Klausuren
        self.room_changes()
        entries: list[dict] = []
        for X in self.items:
            if X.status == _CLASS_ABSENT:
                X.kind = "klasse_abwesend"
                X.note = X.note or f"Klasse abwesend: {X.reason}"
                e = self.entry(X, "klasse_abwesend")
                # gemeldet (Wandertag …) oder regulärer Rhythmus (Praxis-/Berufsschultag)
                reported = any(X.period in self.c_reported.get(c, ((), []))[0] for c in X.classes)
                e["source"] = "absence" if reported else "rhythm"
                entries.append(e)
            elif X.status in (_SUB, _CANCELLED, _SHIFTED):
                entries.append(self.entry(X, X.kind or "entfall"))
            elif X.status == _AFFECTED:  # sollte nicht vorkommen
                self.cancel(X, "Entfall – nicht entschieden", warning=True)
                entries.append(self.entry(X, "entfall"))
            elif X.status == _NORMAL and (X.new_room or X.kind == "raumaenderung"):
                entries.append(self.entry(X, "raumaenderung"))
        entries += self.duty_entries()
        for ex in exams:
            entries.append(self.exam_entry(ex))
        entries.sort(key=lambda e: (e["period"], _natural(e["classes"][0] if e["classes"] else "~"),
                                    e.get("lesson_id") or e["id"], e["part"], e["kind"]))
        stats = _empty_stats()
        for e in entries:
            stats[e["kind"]] = stats.get(e["kind"], 0) + 1
            if e["kind"] == "entfall" and e["warning"]:
                stats["entfall_mitte"] += 1
        stats["warnungen"] = len(self.warnings)
        absent_classes = sorted({c for c in self.c_absent_day if self.c_absent.get(c)}, key=_natural)
        return DayPlan(date=self.day, weekday=self.wd, week_no=self.real_week,
                       holiday=None, entries=entries, warnings=list(dict.fromkeys(self.warnings)), stats=stats,
                       absent_teachers=sorted(self.t_absent), absent_classes=absent_classes,
                       absent_teacher_details=self.teacher_details(entries),
                       absent_class_details=self.class_details(absent_classes),
                       week_info=week_info(self.school, self.day), day_kind="unterricht")

    def teacher_details(self, entries: list[dict]) -> list[dict]:
        """Eine Zeile je abwesender Lehrkraft (ohne Grund): Stunden bzw. ganztägig und Zahl der Vertretungsfälle."""
        cases = absence_cases(entries)
        all_p = set(range(self.P))
        out = []
        for tid in sorted(self.t_absent):
            periods = self.t_absent[tid][0]
            t = self.teachers.get(tid)
            full = periods >= all_p
            out.append({"teacher": tid, "name": t.name if t else "", "full_day": full,
                        "periods": [] if full else sorted(periods), "cases": cases.get(tid, 0)})
        return out

    def class_details(self, absent_classes: list[str]) -> list[dict]:
        """Eine Zeile je Klasse und Herkunft: gemeldete Abwesenheit (``absence``, z. B. Wandertag) bzw.
        ganztägiger Rhythmus (``rhythm``, Praxis-/Berufsschultag – regulär, kein Grund zur Anzeige)."""
        all_p = set(range(self.P))
        out = []
        for cid in absent_classes:
            cls = self.classes.get(cid)
            name = cls.name if cls and cls.name else cid
            rep = self.c_reported.get(cid)
            if rep and rep[0]:
                full = rep[0] >= all_p
                out.append({"class": cid, "name": name, "source": "absence", "full_day": full,
                            "periods": [] if full else sorted(rep[0]), "reason": "; ".join(rep[1])})
            if cid in self.c_rhythm:
                out.append({"class": cid, "name": name, "source": "rhythm", "full_day": True, "periods": [],
                            "reason": "; ".join(self.c_rhythm[cid])})
        return out


# ------------------------------------------------------------------ public API
def _holiday_plan(school: School, d: date, reason: str) -> DayPlan:
    return DayPlan(date=d, weekday=d.weekday(), week_no=wk.real_week(school, d), holiday=reason,
                   stats=_empty_stats(), week_info=week_info(school, d), day_kind=day_kind(school, d))


def compute_day_plan(school: School, day: date | str, history: dict[str, int] | None = None) -> DayPlan:
    """Vertretungsplan für ``day``.

    ``history``: Vertretungen je Lehrkraft an den Vortagen derselben Woche
    (für ``max_subs_per_week`` und faire Verteilung); ``None`` = keine.
    """
    d = as_date(day)
    ok, reason = is_school_day(school, d)
    if not ok:
        return _holiday_plan(school, d, reason or "schulfrei")
    return _Engine(school, d, history).run()


def _add_counts(hist: dict[str, int], plan: DayPlan) -> None:
    for tid, n in plan.substitution_counts().items():
        hist[tid] = hist.get(tid, 0) + n


def week_history(school: School, day: date | str) -> dict[str, int]:
    """Vertretungszählung Montag..Vortag der Woche von ``day`` (faire Historie für Einzeltage)."""
    d = as_date(day)
    hist: dict[str, int] = {}
    cur = monday_of(d)
    while cur < d:
        if is_school_day(school, cur)[0]:
            _add_counts(hist, compute_day_plan(school, cur, hist))
        cur += timedelta(days=1)
    return hist


def compute_range(school: School, date_from: date | str, date_to: date | str) -> list[DayPlan]:
    """Pläne für alle Tage (Mo–So) im Bereich, inkl. Ferientage und Tage ohne Unterricht (``holiday`` gesetzt,
    ``day_kind``).

    Die Vertretungszählung der Vortage derselben Woche fließt ein (auch für Tage
    vor ``date_from`` in der ersten Woche), d. h. jeder Tag ist identisch mit
    ``compute_day_plan(school, d, week_history(school, d))``.
    """
    d0, d1 = as_date(date_from), as_date(date_to)
    if d1 < d0:
        return []
    if (d1 - d0).days > 400:
        raise ValueError("Zeitraum zu lang (maximal 400 Tage)")
    out: list[DayPlan] = []
    hist: dict[str, int] = {}
    week_start = None
    cur = monday_of(d0)
    while cur <= d1:
        if monday_of(cur) != week_start:
            week_start = monday_of(cur)
            hist = {}
        if cur < d0:
            if is_school_day(school, cur)[0]:
                _add_counts(hist, compute_day_plan(school, cur, hist))
        else:
            plan = compute_day_plan(school, cur, hist)
            _add_counts(hist, plan)
            out.append(plan)
        cur += timedelta(days=1)
    return out


def rank_candidates(school: School, day: date | str, lesson_id: str, period: int, part: int = 0,
                    history: dict[str, int] | None = None) -> list[dict]:
    """Kandidaten für eine Vertretung, beste zuerst.

    ``[{"teacher","name","score","reasons","qualified","free","current"}]`` – berücksichtigt alle
    übrigen Entscheidungen des Tagesplans (wer schon vertritt, ist belegt).
    """
    d = as_date(day)
    if not is_school_day(school, d)[0]:
        return []
    eng = _Engine(school, d, history)
    eng.run()
    X = eng.by_key.get((lesson_id, int(period), int(part)))
    if X is None:
        return []
    current = X.sub if X.status == _SUB and X.kind in SUB_KINDS else None
    if current:
        eng._release(current, X.period, X)
        eng.subs_today[current] -= 1
    out = []
    for t in eng.teacher_list:
        if t.id == X.teacher:
            continue
        ok, score, reasons, q = eng.evaluate(t, X, full=True)
        out.append({"teacher": t.id, "name": t.name, "score": round(score, 1), "reasons": reasons,
                    "qualified": q, "free": ok, "current": t.id == current})
    out.sort(key=lambda r: (not r["free"], -r["score"], r["teacher"]))
    return out


# --------------------------------------------------------------- effective day
_STATUS_BY_KIND = {
    "vertretung": "geaendert", "betreuung": "geaendert", "mitbetreuung": "geaendert",
    "raumaenderung": "geaendert", "entfall": "entfall", "klasse_abwesend": "entfall",
}


def effective_day(school: School, plan: DayPlan | dict, kind: str, ref: str) -> list[dict]:
    """Tagesansicht (Klasse/Lehrkraft/Raum/Schüler) inkl. aller Änderungen des Plans.

    Zelle: ``{"period","period_label","time","subject","teacher","room","classes","status","note",
    "lesson_id","part","kind","course_id","original_teacher","original_room","entry_id","exam","dropped"}``;
    ``status`` ∈ ``normal | geaendert | entfall | neu``, ``kind`` = Entry-Art bzw. ``unterricht``/``aufsicht``,
    ``dropped`` = Unterricht findet laut ``lesson``-Abwesenheit nicht statt (Eintrag mit ``"dropped": true``).
    """
    if isinstance(plan, dict):
        plan = DayPlan.from_dict(plan)
    if plan.holiday:
        return []
    if kind not in ("class", "teacher", "room", "student"):
        raise ValueError(f"Unbekannte Ansicht {kind}")
    eng = _Engine(school, plan.date)
    eng._load_lessons()
    st = school.settings

    parts_sel: dict[str, list[int]] = {}
    student_class = None
    if kind == "student":
        stud = school.index("students").get(ref)
        if stud is None:
            return []
        student_class = stud.class_id
        try:
            from .timetable import student_parts
            parts_sel = student_parts(school, ref)
        except ImportError:  # pragma: no cover - timetable fehlt
            parts_sel = {}

    def base_match(it: _Item) -> bool:
        if kind == "class":
            return ref in it.classes
        if kind == "teacher":
            return it.teacher == ref
        if kind == "room":
            return it.room == ref
        if student_class not in it.classes:
            return False
        sel = parts_sel.get(it.course.id)
        return sel is None or it.part in sel

    def entry_match(e: dict) -> bool:
        if kind == "class":
            return ref in e.get("classes", [])
        if kind == "teacher":
            return e.get("teacher") == ref
        if kind == "room":
            return (e.get("new_room") or e.get("room")) == ref
        if student_class not in e.get("classes", []):
            return False
        sel = parts_sel.get(e.get("course_id") or "")
        return sel is None or e.get("part", 0) in sel

    by_key: dict[tuple, dict] = {}
    moved: dict[tuple, dict] = {}
    for e in plan.entries:
        if e.get("kind") in ("aufsicht", "klausur") or not e.get("lesson_id"):
            continue
        by_key[(e["lesson_id"], e["period"], e.get("part", 0))] = e
        if e.get("kind") == "verlegung" and e.get("moved_from") is not None:
            moved[(e["lesson_id"], e["moved_from"], e.get("part", 0))] = e

    def cell(period: int, subject, teacher, room, classes, status, note, lesson_id, part, k, course_id=None,
             original_teacher=None, original_room=None, entry_id=None, dropped=False) -> dict:
        return {"period": period, "period_label": period_label(period), "time": period_time(st, period),
                "subject": subject, "teacher": teacher, "room": room, "classes": list(classes or []),
                "status": status, "note": note or "", "lesson_id": lesson_id, "part": part, "kind": k,
                "course_id": course_id, "original_teacher": original_teacher, "original_room": original_room,
                "entry_id": entry_id, "exam": None, "dropped": bool(dropped)}

    cells: list[dict] = []
    for it in eng.items:
        if not base_match(it):
            continue
        args = dict(course_id=it.course.id)
        mv = moved.get(it.key)
        if mv is not None:
            cells.append(cell(it.period, it.subject, it.teacher, it.room, it.classes, "entfall",
                              f"verlegt in die {mv['period'] + 1}. Stunde", it.lesson.id, it.part, "verlegung",
                              entry_id=mv["id"], **args))
            continue
        e = by_key.get(it.key)
        if e is None or e.get("kind") == "verlegung":
            cells.append(cell(it.period, it.subject, it.teacher, it.room, it.classes, "normal", "",
                              it.lesson.id, it.part, "unterricht", **args))
            continue
        k = e["kind"]
        status = _STATUS_BY_KIND.get(k, "geaendert")
        teacher, room = it.teacher, e.get("new_room") or it.room
        note = e.get("note", "")
        if k in ("vertretung", "betreuung", "mitbetreuung") and e.get("substitute"):
            teacher = e["substitute"]
        if kind == "teacher" and k in ("vertretung", "betreuung", "mitbetreuung"):
            status = "entfall"
            note = f"{note} – übernimmt {e.get('substitute')}" if e.get("substitute") else note
            teacher = it.teacher
        if kind == "room" and e.get("new_room") and e["new_room"] != ref:
            status = "entfall"
            note = f"Raumänderung → {e['new_room']}"
        cells.append(cell(it.period, it.subject, teacher, room, it.classes, status, note, it.lesson.id, it.part,
                          k, original_teacher=it.teacher if teacher != it.teacher else None,
                          original_room=it.room if room != it.room else None, entry_id=e["id"],
                          dropped=e.get("dropped", False), **args))

    for e in plan.entries:
        k = e.get("kind")
        if k == "verlegung" and entry_match(e):
            cells.append(cell(e["period"], e.get("subject"), e.get("teacher"), e.get("new_room") or e.get("room"),
                              e.get("classes"), "neu", e.get("note"), e.get("lesson_id"), e.get("part", 0), k,
                              course_id=e.get("course_id"), entry_id=e["id"]))
        elif kind == "teacher" and k in ("vertretung", "betreuung", "mitbetreuung") and e.get("substitute") == ref:
            cells.append(cell(e["period"], e.get("subject"), ref, e.get("new_room") or e.get("room"),
                              e.get("classes"), "neu", e.get("note"), e.get("lesson_id"), e.get("part", 0), k,
                              course_id=e.get("course_id"), original_teacher=e.get("teacher"), entry_id=e["id"]))
        elif (kind == "room" and k in ("vertretung", "betreuung", "mitbetreuung", "raumaenderung")
              and e.get("new_room") == ref):
            cells.append(cell(e["period"], e.get("subject"), e.get("substitute") or e.get("teacher"), ref,
                              e.get("classes"), "neu", e.get("note"), e.get("lesson_id"), e.get("part", 0), k,
                              course_id=e.get("course_id"), original_room=e.get("room"), entry_id=e["id"]))

    if kind == "teacher":
        cells += _teacher_duty_cells(school, plan, ref)

    # Ansicht einer Klasse/eines Schülers: Ist die eigene Klasse laut Abwesenheit nicht da (z. B. Ausflug), gilt das auch
    # für gekoppelte Stunden, die für die übrigen Klassen stattfinden (die Engine wertet sie nur als ausgefallen, wenn
    # ALLE Klassen fehlen).
    own_class = ref if kind == "class" else student_class
    if own_class:
        away: dict[int, str] = {}
        for a in school.absences:
            if a.kind != "class" or a.ref != own_class:
                continue
            for c in cells:
                if c["period"] not in away and a.covers(plan.date, c["period"]):
                    away[c["period"]] = a.reason.strip()
        for c in cells:
            if c["period"] in away and c["kind"] not in ("klasse_abwesend", "aufsicht") and c["status"] != "entfall":
                why = away[c["period"]]
                c.update(status="entfall", kind="klasse_abwesend", original_teacher=None, original_room=None,
                         note=f"Klasse abwesend: {why}" if why else "Klasse abwesend")

    for e in plan.entries:
        if e.get("kind") != "klausur":
            continue
        span = range(e["period"], e["period"] + int(e.get("length", 1) or 1))
        exam_part = e.get("exam_part")
        for c in cells:
            if c["course_id"] != e.get("course_id") or c["period"] not in span or c["kind"] == "aufsicht":
                continue
            if exam_part is None or c["part"] == exam_part:
                c["exam"] = e.get("title") or "Klausur"
    order = {"aufsicht": 1}
    cells.sort(key=lambda c: (c["period"], order.get(c["kind"], 0), c["status"] == "entfall",
                              c["lesson_id"] or "", c["part"]))
    return cells


def _teacher_duty_cells(school: School, plan: DayPlan, ref: str) -> list[dict]:
    st = school.settings
    areas = school.index("areas")
    replaced = {e.get("duty_id"): e for e in plan.entries if e.get("kind") == "aufsicht"}
    out = []
    for d in school.duties:
        if not wk.duty_active_on(school, d, plan.date):
            continue
        if not 0 <= d.break_index < len(st.breaks):
            continue
        brk = st.breaks[d.break_index]
        rep = replaced.get(d.id)
        area = areas.get(d.area)
        base = {"period": int(brk.get("after", 0)), "period_label": brk.get("name", "Pause"),
                "time": break_time(st, brk), "subject": None, "room": area.name if area else d.area,
                "classes": [], "lesson_id": None, "part": 0, "kind": "aufsicht", "course_id": None,
                "original_room": None, "entry_id": rep["id"] if rep else None, "exam": None, "dropped": False,
                "duty_id": d.id, "break_name": brk.get("name", "")}
        if d.teacher == ref:
            if rep and rep.get("substitute") != ref:
                out.append({**base, "teacher": ref, "status": "entfall",
                            "note": f"Aufsicht übernimmt {rep.get('substitute') or '–'}", "original_teacher": None})
            else:
                out.append({**base, "teacher": ref, "status": "normal", "note": "", "original_teacher": None})
        elif rep and rep.get("substitute") == ref:
            out.append({**base, "teacher": ref, "status": "neu", "note": rep.get("note", ""),
                        "original_teacher": d.teacher})
    return out


# ---------------------------------------------------------------- statistics
def _teacher_absent(school: School, tid: Optional[str], d: date, period: int) -> bool:
    for a in school.absences:
        if a.kind != "teacher" or a.ref != tid:
            continue
        try:
            if a.covers(d, period):
                return True
        except (TypeError, ValueError):
            continue
    return False


def teacher_stats(school: School, date_from: date | str, date_to: date | str,
                  plans: Optional[Iterable[DayPlan]] = None) -> list[dict]:
    """Vertretungs-/Entfall-/Aufsichtsstatistik je Lehrkraft im Zeitraum.

    ``[{"teacher","name","substitutions","cancelled_own","duties","supervisions",
    "vertretung","betreuung","mitbetreuung","freed","moved","absent_periods"}]``
    (``substitutions`` = vertretung + betreuung + mitbetreuung, ``duties`` = gehaltene reguläre
    Pausenaufsichten, ``supervisions`` = übernommene Aufsichtsvertretungen, ``freed`` = durch abwesende
    Klassen oder entfallenden Unterricht (``dropped``) freigesetzte Stunden – zählen nicht als Abwesenheit).
    """
    if plans is None:
        plans = compute_range(school, date_from, date_to)
    d0, d1 = as_date(date_from), as_date(date_to)
    rows: dict[str, dict] = {}
    for t in school.teachers:
        rows[t.id] = {"teacher": t.id, "name": t.name, "substitutions": 0, "cancelled_own": 0, "duties": 0,
                      "supervisions": 0, "vertretung": 0, "betreuung": 0, "mitbetreuung": 0, "freed": 0,
                      "moved": 0, "absent_periods": 0}

    def row(tid: Optional[str]) -> Optional[dict]:
        return rows.get(tid) if tid else None

    for plan in plans:
        if plan.holiday or not (d0 <= plan.date <= d1):
            continue
        replaced_duties = set()
        for e in plan.entries:
            k = e.get("kind")
            # Unterricht entfällt (``lesson``-Abwesenheit): die Lehrkraft ist frei, nicht abwesend
            freed = bool(e.get("dropped")) and not _teacher_absent(school, e.get("teacher"), plan.date,
                                                                   e.get("period", 0))
            if k in ("vertretung", "betreuung", "mitbetreuung"):
                r = row(e.get("substitute"))
                if r:
                    r["substitutions"] += 1
                    r[k] += 1
                r = row(e.get("teacher"))
                if r:
                    r["freed" if freed else "absent_periods"] += 1
            elif k == "entfall":
                r = row(e.get("teacher"))
                if r:
                    r["freed" if freed else "cancelled_own"] += 1
            elif k == "klasse_abwesend":
                r = row(e.get("teacher"))
                if r:
                    r["freed"] += 1
            elif k == "verlegung":
                r = row(e.get("teacher"))
                if r:
                    r["moved"] += 1
            elif k == "aufsicht":
                replaced_duties.add(e.get("duty_id"))
                r = row(e.get("substitute"))
                if r:
                    r["supervisions"] += 1
        for d in school.duties:
            if not wk.duty_active_on(school, d, plan.date) or d.id in replaced_duties:
                continue
            r = row(d.teacher)
            if r:
                r["duties"] += 1
    return sorted(rows.values(), key=lambda r: (-r["substitutions"], -r["supervisions"], r["teacher"]))


__all__ = ["DayPlan", "KINDS", "compute_day_plan", "compute_range", "rank_candidates", "effective_day",
           "split_lesson_ref", "teacher_stats", "week_history"]
