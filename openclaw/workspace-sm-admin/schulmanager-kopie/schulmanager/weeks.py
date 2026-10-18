"""Wochenangaben im 52-Wochen-System und die zentrale Aktiv-Logik.

* **Laufende Wochen**: Das Schuljahr hat die Wochen 1 … 52 (53), Mo–So, Ferien zählen mit (``calendar_utils.plan_week``).
* **Wochenangabe** eines Eigentümers (Kurs, Stunde, Sperrzeit, Wunsch, Zeitfenster, Aufsicht, Vertretungsregel …):

  - **jede Woche** (Standard): ``weeks`` leer, ``rhythm`` leer;
  - **ausgewählte Wochen**: ``weeks`` = Liste laufender Wochen (1-basiert, sortiert, eindeutig);
  - **Rhythmus**: ``rhythm = {"every": k, "from_week": s, "to_week": e}`` – alle *k* Wochen ab Woche *s*, optional bis
    Woche *e* (``to_week`` 0 = offen), *k* beliebig 1 … 52.

  Beides zugleich ist nicht erlaubt. Es gibt keine Wochenbuchstaben.
* **Aktiv-Logik** (eine Stelle für Ansicht, Engine, Kursräume, Klausuren, Aufsichten, Klassen-Seite, iCal, Jobs):
  ein Block ist in einer Woche aktiv, wenn die Wochenangaben von Stunde **und** Kurs sie enthalten.
* **Planungshorizont**: ``Horizon`` = die realen Wochen 1 … Y eines Schuljahres; ``group_weeks`` fasst Wochen mit
  gleicher Signatur zu Varianten zusammen (Generator, Bericht, Aufsichten).

* **Anzeige als Kalenderwoche** (``Settings.week_numbering == "iso"``, Standard): Gespeichert wird immer die laufende
  Woche (Position im Schuljahr, fortlaufend über Neujahr, ohne Sprung bei KW 52/53 → 1). Nur Anzeige und Eingabe
  rechnen über :class:`WeekLabels` in ISO-Kalenderwochen um. Gespeicherte Daten bleiben dadurch unverändert (verlustfrei);
  Rhythmen laufen über den Jahreswechsel, ohne dass KW 53 eine Sonderrolle spielt.

Texte (``describe_spec``, Fehler) sind deutsch.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, Optional, Sequence

from .calendar_utils import as_date, monday_of, plan_week, week_no, year_bounds
from .models import Course, Lesson, School, lesson_in_range, spec_active

MAX_WEEKS = 53
KEYS_RHYTHM = {"every", "from_week", "to_week", "invert"}


# ===================================================================== Wochenlisten
def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def errors(weeks: Any) -> list[str]:
    """Prüft eine Wochenliste: nur ganze Zahlen 1 … 53 (laufende Wochen), höchstens 53 Einträge."""
    if weeks is None:
        return []
    if not isinstance(weeks, (list, tuple)):
        return [f"Wochen: nur 1 bis {MAX_WEEKS} möglich."]
    if len(weeks) > MAX_WEEKS or any(not _is_int(w) or not 1 <= w <= MAX_WEEKS for w in weeks):
        return [f"Wochen: nur 1 bis {MAX_WEEKS} möglich."]
    return []


def normalize(weeks: Iterable[int]) -> list[int]:
    """Sortiert, eindeutig, nur 1 … 53; alle Wochen → ``[]``."""
    out = sorted({int(w) for w in weeks if _is_int(w) and 1 <= w <= MAX_WEEKS})
    return [] if len(out) >= MAX_WEEKS else out


# ===================================================================== Anzeige als Kalenderwoche
class WeekLabels:
    """Umrechnung laufende Woche <-> ISO-Kalenderwoche für Anzeige und Eingabe.

    ``iso`` = False: unverändert („Woche 5“). ``iso`` = True: „KW 38“; die laufende Woche ``L`` ist die Woche
    Montag ``first + 7·(L−1)``. In einem Schuljahr mit 53 Wochen kommt die KW des Beginns zweimal vor (Beginn und Ende);
    beim Umrechnen KW → Woche gilt für „ab“ das erste, für „bis“ das letzte Vorkommen."""

    def __init__(self, st: Any, today: Optional[date] = None, first: Optional[date] = None):
        self.iso = getattr(st, "week_numbering", "iso") == "iso"
        if first is None:
            first, y, _ = year_bounds(st, today or date.today())
        else:
            y = year_bounds(st, first)[1]
        self.first, self.year_weeks = first, y

    @property
    def word(self) -> str:
        return "KW" if self.iso else "Woche"

    def of(self, week: int) -> int:
        """Anzeigenummer der laufenden Woche ``week`` (KW bzw. die Woche selbst)."""
        if not self.iso:
            return week
        return (self.first + timedelta(days=7 * (week - 1))).isocalendar()[1]

    def follows(self, a: int, b: int) -> bool:
        """Folgt die Anzeige von ``b`` unmittelbar auf ``a`` (an der Jahresgrenze 52/53 -> 1 nicht)?"""
        return b == a + 1 and self.of(b) == self.of(a) + 1

    def to_week(self, number: int, last: bool = False) -> Optional[int]:
        """Laufende Woche zur Anzeigenummer (KW) im Schuljahr; ``None``, wenn es sie dort nicht gibt (z. B. KW 53)."""
        if not self.iso:
            return number if 1 <= number <= self.year_weeks else None
        hits = [w for w in range(1, self.year_weeks + 1) if self.of(w) == number]
        return (hits[-1] if last else hits[0]) if hits else None


# ===================================================================== Rhythmus
def rhythm_errors(rhythm: Any) -> list[str]:
    """Prüft ``{"every": 1…53, "from_week": 1…53, "to_week": 0…53}`` (``to_week`` 0 = offen)."""
    if not isinstance(rhythm, dict):
        return ["Bitte entweder Wochen oder einen Rhythmus angeben."]
    every, start, end = rhythm.get("every"), rhythm.get("from_week"), rhythm.get("to_week", 0)
    end = 0 if end is None else end
    out = []
    if not _is_int(every) or not 1 <= every <= MAX_WEEKS:
        out.append(f"Rhythmus: Abstand 1 bis {MAX_WEEKS}.")
    if (not _is_int(start) or not 1 <= start <= MAX_WEEKS or not _is_int(end) or not 0 <= end <= MAX_WEEKS):
        out.append(f"Wochen: nur 1 bis {MAX_WEEKS} möglich.")
    elif end and end < start:
        out.append("„Bis Woche“ liegt vor „Ab Woche“.")
    unknown = set(rhythm) - KEYS_RHYTHM
    if unknown:
        out.append(f"Rhythmus: unbekannte Felder {', '.join(sorted(unknown))}")
    return out


def normalize_rhythm(rhythm: Optional[dict]) -> Optional[dict]:
    """Gespeicherte Form ``{"every", "from_week", "to_week"}`` (``None`` bleibt ``None``)."""
    if not rhythm:
        return None
    out = {"every": int(rhythm["every"]), "from_week": int(rhythm["from_week"]),
           "to_week": int(rhythm.get("to_week") or 0)}
    if rhythm.get("invert"):
        out["invert"] = True
    return out


def describe_rhythm(rhythm: Optional[dict], lab: Optional[WeekLabels] = None) -> str:
    """„jede 2. Woche ab Woche 10“, „… bis Woche 30“, „jede Woche ab Woche 5“ (mit ``lab`` in KW: „ab KW 38“)."""
    if not rhythm:
        return "jede Woche"
    every, start, end = int(rhythm.get("every") or 1), int(rhythm.get("from_week") or 1), int(rhythm.get("to_week") or 0)
    word = lab.word if lab else "Woche"
    num = lab.of if lab else (lambda w: w)
    head = "jede Woche" if every == 1 else f"jede {every}. Woche"
    text = head if every == 1 and start <= 1 and not end else f"{head} ab {word} {num(start)}"
    if end:
        text += f" bis {word} {num(end)}"
    if rhythm.get("invert"):
        text = f"außer {text}"
    return text


def _runs(weeks: Sequence[int], lab: Optional[WeekLabels] = None) -> str:
    """„1–4, 9“ (Läufe ab 3 Wochen als Bereich; in KW läuft ein Bereich nicht über den Jahreswechsel)."""
    follows = lab.follows if lab else (lambda a, b: b == a + 1)
    num = lab.of if lab else (lambda w: w)
    parts: list[str] = []
    i = 0
    ws = list(weeks)
    while i < len(ws):
        j = i
        while j + 1 < len(ws) and follows(ws[j], ws[j + 1]):
            j += 1
        if j - i >= 2:
            parts.append(f"{num(ws[i])}–{num(ws[j])}")
        else:
            parts.extend(str(num(w)) for w in ws[i:j + 1])
        i = j + 1
    return ", ".join(parts)


def describe(weeks: Iterable[int], lab: Optional[WeekLabels] = None) -> str:
    """Kürzester Text einer Wochenliste: „jede Woche“, „Woche 1–4, 9“, „jede 3. Woche ab Woche 2“, „… bis Woche 29“
    (mit ``lab`` als KW)."""
    ws = normalize(weeks)
    if not ws:
        return "jede Woche"
    word = lab.word if lab else "Woche"
    num = lab.of if lab else (lambda w: w)
    texts = [f"{word} " + _runs(ws, lab)]
    if len(ws) >= 4:
        step = ws[1] - ws[0]
        if step >= 2 and all(b - a == step for a, b in zip(ws, ws[1:])):
            head = f"jede {step}. Woche ab {word} {num(ws[0])}"
            texts.append(head if ws[-1] + step > MAX_WEEKS else f"{head} bis {word} {num(ws[-1])}")
    return min(texts, key=len)


def spec_from_weeks(weeks: Iterable[int], total: int = MAX_WEEKS, last: int = MAX_WEEKS
                    ) -> tuple[list[int], Optional[dict]]:
    """Laufende Wochen → ``(weeks, rhythm)``: alle ``total`` Wochen → leer; mindestens drei Wochen mit gleichem Abstand
    ab 2 → Rhythmus (``to_week`` 0, wenn er bis zur letzten Woche ``last`` reicht), sonst die Wochenliste."""
    ls = sorted({int(w) for w in weeks if _is_int(w) and 1 <= w <= MAX_WEEKS})
    if len(ls) >= total:
        return [], None
    if len(ls) >= 3:
        step = ls[1] - ls[0]
        if step >= 2 and all(b - a == step for a, b in zip(ls, ls[1:])):
            return [], {"every": step, "from_week": ls[0], "to_week": 0 if ls[-1] + step > last else ls[-1]}
    return ls, None


def describe_spec(weeks: Optional[Iterable[int]] = None, rhythm: Optional[dict] = None,
                  lab: Optional[WeekLabels] = None) -> str:
    """Text einer Wochenangabe (Rhythmus hat Vorrang, sonst Wochenliste)."""
    if rhythm:
        return describe_rhythm(rhythm, lab)
    return describe(weeks or [], lab)


def spec_of(obj: Any) -> tuple[list[int], Optional[dict]]:
    """``(weeks, rhythm)`` eines Objekts oder Wörterbuchs."""
    if isinstance(obj, dict):
        return list(obj.get("weeks") or []), obj.get("rhythm") or None
    return list(getattr(obj, "weeks", None) or []), getattr(obj, "rhythm", None) or None


def describe_rule_weeks(rule: Any, lab: Optional[WeekLabels] = None) -> str:
    """Wochentext einer Regel/Aufsicht/eines Kurses (Rhythmus oder Wochenliste)."""
    weeks, rhythm = spec_of(rule)
    return describe_spec(weeks, rhythm, lab)


def spec_errors(weeks: Any, rhythm: Any, what: str = "") -> list[str]:
    """Prüft eine Wochenangabe: Liste 1 … 53 oder Rhythmus (nie beides)."""
    pre = f"{what}: " if what else ""
    if rhythm and weeks:
        return [f"{pre}Bitte entweder Wochen oder einen Rhythmus angeben."]
    if rhythm:
        return [f"{pre}{e}" for e in rhythm_errors(rhythm)]
    return [f"{pre}{e}" for e in errors(weeks)]


def parse_weeks_input(data: dict) -> list[str]:
    """Ältere Anfrage-Felder in einem Request-Dict auf ``weeks``/``rhythm`` abbilden (in place). Liefert Fehlertexte.

    ``week_pattern`` (alt: ``{"every", "from", "to"}``) wird zu ``rhythm`` ``{"every", "from_week", "to_week"}``."""
    if not isinstance(data, dict) or "week_pattern" not in data:
        return []
    pattern = data.pop("week_pattern")
    if pattern is None:
        return []
    if data.get("weeks") or data.get("rhythm") or not isinstance(pattern, dict):
        return ["Bitte entweder Wochen oder einen Rhythmus angeben."]
    rhythm = {"every": pattern.get("every"), "from_week": pattern.get("from_week", pattern.get("from")),
              "to_week": pattern.get("to_week", pattern.get("to")) or 0}
    errs = rhythm_errors(rhythm)
    if errs:
        return errs
    data["rhythm"] = rhythm
    return []


# ===================================================================== Aktiv-Logik
def real_week(school: School, d: date | str) -> int:
    """Laufende Woche am Datum ``d`` (Grundlage aller Wochenangaben)."""
    return plan_week(school.settings, as_date(d))


def lesson_active_in(lesson: Lesson, course: Optional[Course], week: Optional[int]) -> bool:
    """Liegt der Block in der laufenden Woche ``week``? (Stunde ∩ Kurs; unbekannte Woche = ja)"""
    if not spec_active(lesson.weeks, lesson.rhythm, week) or not lesson_in_range(lesson, week):
        return False
    return course is None or spec_active(course.weeks, course.rhythm, week)


class ActiveIndex:
    """Zwischenspeicher für viele Aktiv-Abfragen auf einem Dokument (laufende Woche je Montag)."""

    def __init__(self, school: School):
        self.school = school
        self.classes = school.index("classes")
        self.courses = school.index("courses")
        self._real: dict[date, int] = {}

    def real(self, d: date) -> int:
        m = monday_of(d)
        hit = self._real.get(m)
        if hit is None:
            hit = self._real[m] = plan_week(self.school.settings, m)
        return hit

    def active_on(self, lesson: Lesson, course: Optional[Course], d: date) -> bool:
        if lesson.day != d.weekday():
            return False
        return lesson_active_in(lesson, course, self.real(d))

    def in_week(self, lesson: Lesson, course: Optional[Course], d: date) -> bool:
        """Liegt der Block in der Woche von ``d`` (unabhängig vom Wochentag)?"""
        return lesson_active_in(lesson, course, self.real(d))


def lesson_active_on(school: School, lesson: Lesson, course: Optional[Course], d: date | str,
                     _idx: Optional[ActiveIndex] = None) -> bool:
    """Findet der Block am Datum ``d`` statt (Wochentag und laufende Woche)?"""
    idx = _idx or ActiveIndex(school)
    return idx.active_on(lesson, course, as_date(d))


def rule_active_on(school: School, rule: Any, d: date | str) -> bool:
    """Gilt die Regel/Aufsicht (Wochen bzw. Rhythmus und Tage) am Datum ``d``?"""
    d = as_date(d)
    days = getattr(rule, "days", None)
    if days and d.weekday() not in days:
        return False
    if getattr(rule, "day", None) is not None and getattr(rule, "day") != d.weekday():
        return False
    return spec_active(getattr(rule, "weeks", None), getattr(rule, "rhythm", None), real_week(school, d))


def duty_active_on(school: School, duty: Any, d: date | str) -> bool:
    """Findet die Aufsicht am Datum ``d`` statt (Wochentag, Wochen bzw. Rhythmus)?"""
    d = as_date(d)
    if duty.day != d.weekday():
        return False
    return spec_active(duty.weeks, duty.rhythm, real_week(school, d))


# ===================================================================== Planungshorizont und Varianten
class Horizon:
    """Reale Wochen 1 … Y des Schuljahres von ``today``.

    Beim Altdokument nach Ablauf des ersten Schuljahres der Block von Y Wochen, der ``today`` enthält."""

    def __init__(self, school: School, today: Optional[date] = None):
        self.school = school
        st = school.settings
        today = today or date.today()
        first, y, _ = year_bounds(st, today)
        if not getattr(st, "school_year_start", ""):
            no = week_no(st, today)
            if no > y:
                first += timedelta(days=7 * y * ((no - 1) // y))
        self.first, self.Y = first, y
        self.lab = WeekLabels(st, first=first)
        self.mondays = [first + timedelta(days=7 * i) for i in range(y)]
        self.real = [plan_week(st, m) for m in self.mondays]

    def __len__(self) -> int:
        return self.Y

    def members(self, weeks: Optional[Iterable[int]] = None, rhythm: Optional[dict] = None) -> frozenset[int]:
        """Indizes der realen Wochen, in denen die Wochenangabe gilt (leer = alle)."""
        ws = [w for w in (weeks or []) if _is_int(w)]
        if not ws and not rhythm:
            return frozenset(range(self.Y))
        return frozenset(i for i, L in enumerate(self.real) if spec_active(ws, rhythm, L))

    def spec_members(self, obj: Any) -> frozenset[int]:
        """Reale Wochen, in denen die Wochenangabe von ``obj`` (Regel, Kurs, Stunde, Aufsicht …) gilt."""
        weeks, rhythm = spec_of(obj)
        members = self.members(weeks, rhythm)
        start = getattr(obj, "valid_week", 0) or 0     # Regeln „gültig ab Datum“
        if start:
            members = frozenset(i for i in members if self.real[i] >= start)
        return members

    def lesson_members(self, lesson: Lesson, course: Optional[Course]) -> frozenset[int]:
        """Reale Wochen, in denen der Block liegt (Stunde ∩ Kurs)."""
        mem = self.spec_members(lesson)
        lo, hi = lesson.from_week or 0, lesson.to_week or 0
        if lo or hi:
            mem = frozenset(i for i in mem if (not lo or self.real[i] >= lo) and (not hi or self.real[i] <= hi))
        if course is not None:
            mem = mem & self.spec_members(course)
        return mem

    def describe(self, indices: Iterable[int]) -> str:
        """„Woche 1“, „Woche 1 und jede 6. Woche“, „Woche 3, 9, 15“, „jede Woche“ (reale Wochen; im KW-Modus „KW 38“)."""
        ls = sorted(self.real[i] for i in indices)
        word, num = self.lab.word, self.lab.of
        if not ls:
            return ""
        if len(ls) == 1:
            return f"{word} {num(ls[0])}"
        step = ls[1] - ls[0]
        if all(b - a == step for a, b in zip(ls, ls[1:])):
            if step == 1:
                if len(ls) >= self.Y:
                    return "jede Woche"
                return f"{word} " + _runs(ls, self.lab) if self.lab.iso else f"{word} {ls[0]}–{ls[-1]}"
            return f"{word} {num(ls[0])} und jede {step}. Woche"
        head = ", ".join(str(num(x)) for x in ls[:6])
        return f"{word} {head}" + (" …" if len(ls) > 6 else "")

    def to_spec(self, indices: Iterable[int]) -> tuple[list[int], Optional[dict]]:
        """Reale Wochen (Indizes) → ``(weeks, rhythm)`` (siehe :func:`spec_from_weeks`)."""
        return spec_from_weeks((self.real[i] for i in indices), self.Y, max(self.real))


def group_weeks(size: int, sets: Iterable[frozenset[int]] = ()) -> list[list[int]]:
    """Fasst Wochen 0 … size−1 mit gleicher Signatur (Zugehörigkeit zu jeder Menge) zusammen.
    Reihenfolge der Gruppen nach ihrer ersten Woche."""
    sets = [s for s in dict.fromkeys(sets) if 0 < len(s) < size]
    groups: dict[tuple, list[int]] = {}
    for i in range(size):
        sig = tuple(i in s for s in sets)
        groups.setdefault(sig, []).append(i)
    return list(groups.values())


# ===================================================================== Regeln prüfen
def rule_errors(rule: Any, periods: int, what: str) -> list[str]:
    """Prüft eine Sperr-/Wunschregel: Wochen oder Rhythmus (nie beides), Tage 0–6, Stunden im Raster, nicht
    leer (U-15)."""
    weeks_, rhythm = spec_of(rule)
    out = spec_errors(weeks_, rhythm, what)
    days = getattr(rule, "days", None) or []
    if any(not _is_int(d) or not 0 <= d <= 6 for d in days):
        out.append(f"{what}: ungültiger Wochentag")
    pers = getattr(rule, "periods", None) or []
    if any(not _is_int(p) or not 0 <= p < periods for p in pers):
        out.append(f"{what}: ungültige Stunde")
    if not weeks_ and not rhythm and not days and not pers:
        out.append(f"{what}: Bitte mindestens einen Tag oder eine Stunde wählen.")
    return out


class PlanWeeks:
    """Wochenvarianten eines Dokuments für Belegung, Verschieben und Bericht.

    Gruppen realer Wochen 1 … Y mit gleicher Signatur aus Klassen- und Lehrkraft-Regeln und den Wochenangaben aller
    Stunden und Kurse. Jede Gruppe hat eine erste reale Woche (``rep``) und ein Gewicht ``weight`` (Anteil der
    Schulwochen; Summe = 1)."""

    def __init__(self, school: School, today: Optional[date] = None):
        self.school = school
        self.hz = hz = Horizon(school, today)
        self.idx = ActiveIndex(school)
        courses = school.index("courses")
        sets: list[frozenset[int]] = []
        for c in school.classes:
            for r in c.unavailable:
                if r.weeks or r.rhythm or r.valid_week:
                    sets.append(hz.spec_members(r))
        for t in school.teachers:
            for r in list(t.unavailable) + list(t.wishes):
                if r.weeks or r.rhythm or r.valid_week:
                    sets.append(hz.spec_members(r))
        for c in school.courses:
            if c.weeks or c.rhythm:
                sets.append(hz.spec_members(c))
        # Wochen ohne gültigen Plan (Planzeiträume) bilden eigene Gruppen und zählen weder für fehlende Stunden noch
        # für die Durchschnitte (``planned``, ``weight``)
        from .plan_periods import unplanned_weeks
        bad = unplanned_weeks(school)
        unplanned = frozenset(i for i, L in enumerate(hz.real) if L in bad)
        if unplanned:
            sets.append(frozenset(range(len(hz))) - unplanned)
        self._lesson_sets: dict[str, frozenset[int]] = {}
        for les in school.lessons:
            members = self.lesson_members(les, courses.get(les.course_id))
            if len(members) < len(hz):
                sets.append(members)
        self.groups = group_weeks(len(hz), sets) or [list(range(len(hz)))]
        self.of_index = [0] * len(hz)
        for g, members in enumerate(self.groups):
            for i in members:
                self.of_index[i] = g
        self.rep = [members[0] for members in self.groups]
        self.planned = [not (set(members) & unplanned) for members in self.groups]
        total = sum(len(m) for m, ok in zip(self.groups, self.planned) if ok) or len(hz)
        self.weight = [len(members) / max(1, total) if ok else 0.0
                       for members, ok in zip(self.groups, self.planned)]
        self._lesson_groups: dict[frozenset, list[int]] = {}

    def __len__(self) -> int:
        return len(self.groups)

    def lesson_members(self, lesson: Lesson, course: Optional[Course]) -> frozenset[int]:
        hit = self._lesson_sets.get(lesson.id)
        if hit is None:
            hit = self._lesson_sets[lesson.id] = self.hz.lesson_members(lesson, course)
        return hit

    def lesson_groups(self, lesson: Lesson, course: Optional[Course]) -> list[int]:
        """Gruppen, in denen der Block liegt."""
        members = self.lesson_members(lesson, course)
        hit = self._lesson_groups.get(members)
        if hit is None:
            hit = self._lesson_groups[members] = sorted({self.of_index[i] for i in members})
        return hit

    def spec_groups(self, obj: Any) -> list[int]:
        """Gruppen, in denen die Wochenangabe von ``obj`` (z. B. Kurs) gilt."""
        return sorted({self.of_index[i] for i in self.hz.spec_members(obj)})

    def real_week(self, g: int) -> int:
        return self.hz.real[self.rep[g]]

    def label(self, g: int) -> str:
        """„ (Woche 1)“ bzw. „ (Woche 3 und jede 6. Woche)“; leer, wenn es nur eine Gruppe gibt."""
        if len(self.groups) <= 1:
            return ""
        return f" ({self.hz.describe(self.groups[g])})"


# ===================================================================== Beginn des Schuljahres verschoben
def _shift_list(weeks: Iterable[int], delta: int) -> list[int]:
    """Wochenliste um ``delta`` Wochen zurück (Beginn später = kleinere laufende Wochen); an den Rändern 1 … 53 begrenzt."""
    return sorted({min(MAX_WEEKS, max(1, int(w) - delta)) for w in weeks if _is_int(w)})


def _shift_rhythm(rhythm: dict, delta: int) -> dict:
    """Rhythmus um ``delta`` Wochen zurück. Fällt der Anfang vor Woche 1, rückt er um ganze Abstände nach hinten, damit
    dieselben Kalenderwochen getroffen werden."""
    every = max(1, int(rhythm.get("every") or 1))
    start = int(rhythm.get("from_week") or 1) - delta
    end = int(rhythm.get("to_week") or 0)
    end = end - delta if end else 0
    if start < 1:
        start += every * (-(-(1 - start) // every))
    out = dict(rhythm)
    out["from_week"] = min(MAX_WEEKS, start)
    out["to_week"] = max(out["from_week"], min(MAX_WEEKS, end)) if end else 0
    return out


def _shift_obj(obj: Any, delta: int) -> int:
    """Verschiebt ``weeks``/``rhythm`` eines Objekts oder Wörterbuchs; Anzahl geänderter Angaben (0/1)."""
    if isinstance(obj, dict):
        weeks, rhythm = obj.get("weeks"), obj.get("rhythm")
    else:
        weeks, rhythm = getattr(obj, "weeks", None), getattr(obj, "rhythm", None)
    if rhythm:
        new_r, new_w = _shift_rhythm(rhythm, delta), weeks
    elif weeks:
        new_r, new_w = rhythm, _shift_list(weeks, delta)
    else:
        return 0
    if isinstance(obj, dict):
        obj["rhythm"], obj["weeks"] = new_r, new_w
    else:
        obj.rhythm, obj.weeks = new_r, new_w
    return 1


def shift_week_specs(school: School, delta: int) -> int:
    """Rechnet alle gespeicherten Wochenangaben (Sperrzeiten, Wünsche, Zeitfenster, Kurse, Stunden, Aufsichten) um, wenn
    sich der Beginn des Schuljahres um ``delta`` Wochen nach hinten verschiebt (laufende Wochen werden kleiner), sodass
    jede Angabe dieselben Kalenderwochen trifft. Liefert die Zahl geänderter Angaben."""
    n = 0
    for c in school.classes:
        n += sum(_shift_obj(r, delta) for r in c.unavailable)
    for t in school.teachers:
        n += sum(_shift_obj(r, delta) for r in list(t.unavailable) + list(t.wishes))
        n += sum(_shift_obj(w, delta) for w in t.time_windows)
    n += sum(_shift_obj(c, delta) for c in school.courses)
    n += sum(_shift_obj(x, delta) for x in school.lessons)
    n += sum(_shift_obj(d, delta) for d in school.duties)
    return n
