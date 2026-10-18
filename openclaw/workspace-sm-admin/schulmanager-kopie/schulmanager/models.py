"""Datenmodell des Schulmanagers.

Alle Entitäten sind einfache Dataclasses, die verlustfrei nach/aus JSON
serialisiert werden können (``to_dict`` / ``from_dict``).

Wochen (52-Wochen-System)
-------------------------
Das Schuljahr hat die laufenden Wochen 1 … 52 bzw. 53 (Mo–So, Ferien zählen mit). Alles, was nicht jede Woche gilt
(Kurse, Stunden, Sperrzeiten, Wünsche, Zeitfenster, Aufsichten …), hat die Felder ``weeks`` (ausgewählte laufende
Wochen, 1-basiert) **oder** ``rhythm`` (``{"every": k, "from_week": s, "to_week": e}``, ``to_week`` 0 = offen);
beides leer = jede Woche. Es gibt keine Wochenbuchstaben. Tag 0 = Montag … 6 = Sonntag.
Rechenregeln: ``calendar_utils`` (Wochen, Tage) und ``weeks`` (Muster, Aktiv-Logik); ältere Dokumente mit Zykluswochen
rechnet ``legacy.migrate_document`` beim Laden um.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
#: Arten von Ferien/freien Tagen (``Holiday.kind``)
HOLIDAY_KINDS = ("ferien", "feiertag", "beweglich", "schulfrei")


def _from_dict(cls, data: dict):
    names = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in names})


class Model:
    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return _from_dict(cls, data)


@dataclass
class Site(Model):
    """Schulstandort (z. B. Hauptgebäude, Außenstelle)."""
    id: str
    name: str


@dataclass
class TimeRule(Model):
    """Regel, wann eine Klasse/ein Lehrer NICHT verfügbar ist.

    ``weeks``   – ausgewählte laufende Wochen (1-basiert, 1 … 52/53), leer = jede Woche
    ``days``    – Wochentage (0 = Montag … 6 = Sonntag), leer = jeder Tag
    ``periods`` – Stunden (0-basiert), leer = ganzer Tag
    ``rhythm``  – statt ``weeks``: ``{"every": k, "from_week": s, "to_week": e}`` in laufenden Wochen des
                  Schuljahres (1-basiert, ``to_week`` 0 = offen)

    Beispiele:
      * jeden Mittwoch weg:            TimeRule(days=[2])
      * Woche 1 und 2 Mittwoch weg:    TimeRule(weeks=[1, 2], days=[2])
      * jede 2. Woche ab Woche 2 Di:   TimeRule(days=[1], rhythm={"every": 2, "from_week": 2, "to_week": 0})
      * jede 3. Woche ab Woche 10 Fr:  TimeRule(days=[4], rhythm={"every": 3, "from_week": 10, "to_week": 0})
    """
    weeks: list[int] = field(default_factory=list)
    days: list[int] = field(default_factory=list)
    periods: list[int] = field(default_factory=list)
    note: str = ""
    rhythm: Optional[dict] = None
    # Gültig ab Datum (ISO; leer = von jeher, also für das ganze Schuljahr). ``valid_week`` ist die daraus abgeleitete
    # laufende Woche (Montag der Woche, in der das Datum liegt) und wird beim Speichern berechnet
    # (``teacher_profile.stamp_valid_weeks``); 0 = keine Einschränkung. So gelten mitten im Jahr geänderte Sperrzeiten
    # erst ab dann – in Generator, Vertretung und Konfliktprüfung.
    valid_from: str = ""
    valid_week: int = 0

    def matches(self, real_week: Optional[int], day: int, period: int) -> bool:
        """Trifft die Regel (laufende Woche, Tag, Stunde)? Ist die Woche unbekannt (``None``), gilt die Regel
        vorsichtshalber in jeder Woche."""
        if self.valid_week and real_week is not None and real_week < self.valid_week:
            return False
        if not spec_active(self.weeks, self.rhythm, real_week):
            return False
        return (not self.days or day in self.days) and (not self.periods or period in self.periods)


def rhythm_active(rhythm: Optional[dict], real_week: int) -> bool:
    """Ist ein Rhythmus ``{"every", "from_week", "to_week"}`` in der laufenden Woche ``real_week`` aktiv?
    ``invert: true`` (nur intern aus Zeitfenstern) kehrt das Ergebnis um."""
    if not rhythm:
        return True
    try:
        every = max(1, int(rhythm.get("every") or 1))
        start = int(rhythm.get("from_week") or 1)
        end = int(rhythm.get("to_week") or 0)
    except (TypeError, ValueError):
        return True
    hit = start <= real_week and (end <= 0 or real_week <= end) and (real_week - start) % every == 0
    return hit != bool(rhythm.get("invert"))


def spec_active(weeks: Optional[list], rhythm: Optional[dict], real_week: Optional[int]) -> bool:
    """Gilt eine Wochenangabe (``weeks`` oder ``rhythm``; beides leer = jede Woche) in der laufenden Woche
    ``real_week``? Unbekannte Woche (``None``) gilt vorsichtshalber als „ja“."""
    if real_week is None:
        return True
    if rhythm:
        return rhythm_active(rhythm, real_week)
    if weeks:
        return real_week in weeks
    return True



@dataclass
class Subject(Model):
    id: str
    name: str
    room_type: Optional[str] = None      # z. B. "Sporthalle", "Chemie"; None = Klassenraum
    core: bool = False                   # Hauptfach -> bevorzugt früh am Tag
    max_per_day: int = 1                 # max. Blöcke pro Tag
    color: str = ""


@dataclass
class Teacher(Model):
    id: str                              # Kürzel
    name: str
    subjects: list[str] = field(default_factory=list)
    max_hours: int = 25                  # Deputat pro Woche
    max_per_day: int = 7
    unavailable: list[TimeRule] = field(default_factory=list)   # harte Sperrzeiten
    max_subs_per_week: int = 3           # Vertretungen pro Woche
    sites: list[str] = field(default_factory=list)  # leer = alle Standorte
    wishes: list[TimeRule] = field(default_factory=list)  # weiche Wünsche: dann möglichst KEIN Unterricht
    email: str = ""
    # Selbstauskunft der Lehrkraft (Lehrer-Selbstverwaltung, ggf. nach Genehmigung übernommen):
    preferred_classes: list[str] = field(default_factory=list)  # Klassen, die sie hauptsächlich unterrichtet
    # Arbeitszeitfenster, z. B. [{"days": [0,1,2,3,4], "start": "10:00", "end": "17:00", "weeks": []}]
    # oder nur Abendunterricht [{"days": [...], "start": "16:00", "end": "21:00"}]. Leer = ganztägig.
    # Wird beim Übernehmen in harte Sperrzeiten (unavailable, note beginnt mit "Zeitfenster") umgerechnet.
    time_windows: list[dict] = field(default_factory=list)
    # Arbeitszeiten als Raster (antippen = gesperrt): {"weeks": N, "blocked": [{"week": k, "day": d, "periods": [..]}]}
    # N = Länge des Rasters 1–52 Wochen (Rasterwoche k gilt in den Schulwochen k+1, k+1+N, …); leer = keine Einschränkung.
    # Wird wie die Zeitfenster in harte Sperrzeiten umgerechnet (note beginnt mit "Zeitfenster").
    work_grid: dict = field(default_factory=dict)
    # Pendelt zwischen Standorten am selben Tag (False = an einem Tag nur an einem Standort einsetzen)
    commutes: bool = True
    # Pendeln genauer (leer = nach ``commutes``): "never" = nie, "once" = höchstens einmal am Tag, "free" = beliebig.
    # ``commute_gap`` = Mindestabstand in Minuten zwischen Ende der einen und Beginn der anderen Stunde beim
    # Standortwechsel (0 = nur die Wegezeit der Schule). Siehe ``commute.py``.
    commute_mode: str = ""
    commute_gap: int = 0
    times_self: bool = False             # darf die eigenen Arbeitszeiten selbst festlegen (Freigabe durch die Schule)

    @classmethod
    def from_dict(cls, data: dict):
        t = _from_dict(cls, data)
        t.unavailable = [r if isinstance(r, TimeRule) else TimeRule.from_dict(r) for r in t.unavailable]
        t.wishes = [r if isinstance(r, TimeRule) else TimeRule.from_dict(r) for r in t.wishes]
        return t


@dataclass
class Room(Model):
    id: str
    name: str
    type: str = "Klassenraum"
    site: str = ""
    capacity: int = 30


@dataclass
class SchoolClass(Model):
    id: str
    name: str
    grade: int
    students: int = 25
    home_room: Optional[str] = None
    site: str = ""
    max_periods_per_day: int = 8
    unavailable: list[TimeRule] = field(default_factory=list)  # Praxistage, Berufsschule, ...
    class_teacher: Optional[str] = None
    # Planung je Klasse (nur mit ``timetable.edit`` änderbar): Unterrichtstage 0–6 (leer = Schulvorgabe)
    school_days: list[int] = field(default_factory=list)
    # Klassenarbeiten/Klausuren je Woche bzw. Tag: ``None`` = Vorgabe des Jahrgangs bzw. der Schule
    # (``rules.exam_limits_for_class``: Schule → Jahrgang → Klasse)
    max_exams_per_week: Optional[int] = None
    max_exams_per_day: Optional[int] = None
    # Jahrgang/Profil (``GradeProfile.id``): bestimmt die Stundentafel, sofern die Klasse keine eigene hat
    profile: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict):
        c = _from_dict(cls, data)
        c.unavailable = [r if isinstance(r, TimeRule) else TimeRule.from_dict(r) for r in c.unavailable]
        return c


@dataclass
class Student(Model):
    id: str
    name: str
    class_id: str
    courses: list[str] = field(default_factory=list)  # IDs von Kursteilen (Oberstufe/Wahlpflicht)
    birth_date: Optional[str] = None                  # ISO-Datum (YYYY-MM-DD), optional (Volljährigkeit)


@dataclass
class CurriculumEntry(Model):
    """Eine Zeile der Stundentafel: Fach X mit N Wochenstunden."""
    subject: str
    hours: int
    double: bool = False                 # bevorzugt Doppelstunden


@dataclass
class Curriculum(Model):
    """Stundentafel: gilt über Jahrgänge (``GradeProfile.curriculum``), für einzelne Klassen (``classes``) oder –
    Altbestand – über die Klassenstufen-Nummer (``grades``). Mit ``base`` ist sie von einer anderen Tafel abgeleitet:
    ``deltas`` sind Abweichungen je Fach (``hours`` = Differenz, auch negativ; ``double`` = Zielwert), die wirksamen
    Zeilen liefert ``planning.effective_entries``."""
    id: str
    name: str
    grades: list[int] = field(default_factory=list)   # Altbestand: Klassenstufen-Nummern (Fallback, s. legacy.py)
    classes: list[str] = field(default_factory=list)  # gilt nur für diese Klassen (Vorrang vor Jahrgang/Stufe)
    entries: list[CurriculumEntry] = field(default_factory=list)
    base: Optional[str] = None                        # abgeleitet von dieser Stundentafel (ID)
    deltas: list[CurriculumEntry] = field(default_factory=list)  # Abweichungen zur Basis (nur mit ``base``)

    @classmethod
    def from_dict(cls, data: dict):
        c = _from_dict(cls, data)
        c.entries = [e if isinstance(e, CurriculumEntry) else CurriculumEntry.from_dict(e) for e in c.entries]
        c.deltas = [e if isinstance(e, CurriculumEntry) else CurriculumEntry.from_dict(e) for e in c.deltas]
        return c


@dataclass
class GradeProfile(Model):
    """Jahrgang/Profil – frei definierbar („5“, „5 Informatik“, „Montessori“, „GIF 26“): Klassen gehören zu einem
    Jahrgang, der Jahrgang bestimmt ihre Stundentafel (``curriculum``). ``grade`` ist nur eine optionale Zahl
    (Klassenstufe) für Sortierung, Vorlagen und Regeln."""
    id: str
    name: str
    short: str = ""                      # Kurzname, z. B. „5 IF“
    grade: Optional[int] = None          # Klassenstufe (Zahl), optional
    color: str = ""                      # Farbe (#rrggbb), leer = automatisch
    description: str = ""
    department: str = ""                 # Schulform/Abteilung, optional
    curriculum: Optional[str] = None     # Stundentafel (``Curriculum.id``), None = keine


@dataclass
class CoursePart(Model):
    """Ein paralleler Teil einer (ggf. gekoppelten) Unterrichtseinheit."""
    subject: str
    teacher: Optional[str] = None        # None = wird automatisch zugewiesen
    room: Optional[str] = None           # fester Raum
    room_type: Optional[str] = None      # überschreibt Fach-Raumtyp
    label: str = ""
    students: Optional[list[str]] = None  # None = alle Schüler der Klassen


@dataclass
class Course(Model):
    """Unterricht, der ``hours`` Mal pro Woche stattfindet.

    Mehrere Klassen und/oder mehrere Teile = Kopplung (z. B. Religion/Ethik
    parallel, Oberstufen-Schienen). Alle Teile liegen immer gleichzeitig.
    """
    id: str
    classes: list[str]
    parts: list[CoursePart]
    hours: int
    double: bool = False
    label: str = ""
    weeks: list[int] = field(default_factory=list)  # nur in diesen laufenden Wochen (leer = alle)
    origin: str = "manual"               # "curriculum" = aus Stundentafel erzeugt
    pinned: list[str] = field(default_factory=list)  # Stundentafel-Kurs: manuell geänderte Felder (bleiben)
    rhythm: Optional[dict] = None        # statt ``weeks``: Rhythmus in laufenden Wochen (wie TimeRule)

    @classmethod
    def from_dict(cls, data: dict):
        c = _from_dict(cls, data)
        c.parts = [p if isinstance(p, CoursePart) else CoursePart.from_dict(p) for p in c.parts]
        return c


@dataclass
class Lesson(Model):
    """Ein platzierter Block im Stundenplan."""
    id: str
    course_id: str
    day: int
    start: int
    length: int = 1
    weeks: list[int] = field(default_factory=list)   # laufende Wochen, in denen der Block liegt (leer = alle)
    rooms: list[Optional[str]] = field(default_factory=list)  # je Kursteil
    locked: bool = False
    rhythm: Optional[dict] = None        # statt ``weeks``: Rhythmus in laufenden Wochen
    # Planzeitraum (``plan_periods.py``): ``period`` = Kennung des Zeitraums, zu dessen Plan der Block gehört (leer =
    # älterer Plan ohne Zeiträume, gilt in jedem Zeitraum). ``from_week``/``to_week`` = die aus dem Zeitraum
    # abgeleiteten laufenden Wochen (0 = offen); der Block liegt nur in Wochen dieses Bereichs (zusätzlich zu
    # ``weeks``/``rhythm``). Beides wird beim Speichern der Zeiträume berechnet (``plan_periods.restamp``).
    period: str = ""
    from_week: int = 0
    to_week: int = 0


def lesson_in_range(lesson: "Lesson", real_week: Optional[int]) -> bool:
    """Liegt die laufende Woche im Gültigkeitsbereich (Planzeitraum) des Blocks? Unbekannte Woche = ja."""
    if real_week is None:
        return True
    lo, hi = getattr(lesson, "from_week", 0) or 0, getattr(lesson, "to_week", 0) or 0
    return not ((lo and real_week < lo) or (hi and real_week > hi))


@dataclass
class Absence(Model):
    """Abwesenheit von Lehrer, Klasse oder Raum für einen Datumsbereich.

    ``kind="lesson"`` = „Unterricht findet nicht statt“: ``ref`` ist ``"<course_id>"`` (ganzer Kurs) oder
    ``"<course_id>#<part>"`` (nur dieser Kursteil, 0-basiert); leere ``periods`` = alle Stunden des Kurses an
    dem Tag. Die Lehrkraft ist dann nicht abwesend, sondern frei (Vertretungs-Engine, ARCHITECTURE.md §10.1).
    """
    id: str
    kind: str                            # "teacher" | "class" | "room" | "lesson"
    ref: str                             # Lehrkraft-/Klassen-/Raum-ID bzw. "<course_id>[#<part>]"
    date_from: str                       # ISO-Datum
    date_to: str
    periods: list[int] = field(default_factory=list)  # 0-basiert, leer = ganzer Tag
    reason: str = ""
    # von der Lehrkraft selbst gemeldet (``POST /absences/report-self``) – nur solche darf sie wieder löschen
    self_reported: bool = False

    def covers(self, d: date, period: int) -> bool:
        if not (date.fromisoformat(self.date_from) <= d <= date.fromisoformat(self.date_to)):
            return False
        return not self.periods or period in self.periods


@dataclass
class Override(Model):
    """Manuelle Entscheidung im Vertretungsplan für einen Tag."""
    id: str
    date: str
    lesson_id: str
    period: int
    part: int = 0
    action: str = "substitute"          # "substitute" | "cancel" | "keep" | "room"
    teacher: Optional[str] = None
    room: Optional[str] = None
    note: str = ""


@dataclass
class Holiday(Model):
    """Ferien / Feiertag / beweglicher Ferientag – an diesen Tagen kein Unterricht.

    ``kind`` ∈ ``HOLIDAY_KINDS``. Ältere Dokumente ohne ``kind``: „…ferien…“ im Namen → ``ferien``, sonst
    ``feiertag`` (Lesepfad V15)."""
    id: str
    name: str
    date_from: str
    date_to: str
    kind: str = "ferien"
    #: Quelle eines automatischen Imports (``server/holiday_import.py``); leer = von Hand angelegt
    source: str = ""
    source_sig: str = ""

    @classmethod
    def from_dict(cls, data: dict):
        h = _from_dict(cls, data)
        if "kind" not in data or h.kind not in HOLIDAY_KINDS:
            h.kind = "ferien" if "ferien" in (h.name or "").lower() else "feiertag"
        return h

    def covers(self, d: date) -> bool:
        return date.fromisoformat(self.date_from) <= d <= date.fromisoformat(self.date_to)


@dataclass
class SupervisionArea(Model):
    """Aufsichtsbereich für Pausenaufsichten (z. B. Schulhof, Mensa)."""
    id: str
    name: str
    site: str = ""
    needed: int = 1                      # benötigte Aufsichten pro Pause


@dataclass
class Duty(Model):
    """Pausenaufsicht: Lehrer ``teacher`` beaufsichtigt ``area`` in Pause ``break_index``."""
    id: str
    area: str
    day: int
    break_index: int                     # Index in Settings.breaks
    teacher: Optional[str] = None
    weeks: list[int] = field(default_factory=list)
    rhythm: Optional[dict] = None        # statt ``weeks``: Rhythmus in laufenden Wochen (wie TimeRule)


@dataclass
class Event(Model):
    """Termin im Schulkalender (erscheint im Stundenplan der Betroffenen, auch am Wochenende).

    ``kind``: ``termin`` (zur Info, z. B. Elternabend, Sportfest) oder ``pflicht`` (Anwesenheit Pflicht, z. B.
    Unterricht/Tag der offenen Tür am Samstag). ``classes``/``grades`` leer = ganze Schule.
    """
    id: str
    title: str
    date_from: str
    date_to: str = ""
    time_from: str = ""                  # "HH:MM", leer = ganztägig
    time_to: str = ""
    kind: str = "termin"                 # termin|pflicht
    classes: list[str] = field(default_factory=list)
    grades: list[int] = field(default_factory=list)
    location: str = ""
    note: str = ""
    # Lehrkräfte, die an dem Termin teilnehmen (Fortbildung, Exkursion …): sie fehlen im Unterricht, die Vertretungs-
    # Engine behandelt sie wie eine Abwesenheit (in den Stunden des Termins, ``time_from``/``time_to``; leer = ganztägig)
    teachers: list[str] = field(default_factory=list)

    def covers(self, d: date) -> bool:
        return date.fromisoformat(self.date_from) <= d <= date.fromisoformat(self.date_to or self.date_from)

    def for_class(self, class_id: Optional[str], grade: Optional[int]) -> bool:
        if not self.classes and not self.grades:
            return True
        return (class_id is not None and class_id in self.classes) or (grade is not None and grade in self.grades)


@dataclass
class Exam(Model):
    """Klassenarbeit / Klausur, die in einer Unterrichtsstunde geschrieben wird."""
    id: str
    course_id: str
    date: str
    start: int                           # 0-basierte Stunde
    length: int = 1
    title: str = ""
    part: Optional[int] = None           # nur ein Kursteil (Oberstufe)
    room: Optional[str] = None
    kind: str = "klausur"                # klausur|test (angekündigter Test) – erscheint im Stundenplan


@dataclass
class Weights(Model):
    """Gewichte der Optimierung (höher = wichtiger)."""
    class_gap: float = 100.0             # Hohlstunden Klassen
    teacher_gap: float = 4.0             # Springstunden Lehrer
    late_start: float = 40.0             # Klasse beginnt nicht zur 1. Stunde
    position: float = 0.6                # generell früh am Tag
    core_late: float = 6.0               # Hauptfach nach core_latest_period
    day_balance: float = 6.0             # gleichmäßige Tageslänge
    spread: float = 5.0                  # gleiches Fach an aufeinanderfolgenden Tagen
    site_change: float = 15.0            # Standortwechsel eines Lehrers am Tag
    double_split: float = 3.0            # gewünschte Doppelstunde nicht bekommen
    teacher_wish: float = 5.0            # Unterricht in einem Wunsch-frei-Slot einer Lehrkraft


@dataclass
class SubstitutionPolicy(Model):
    """Regeln für die Vertretungsplanung."""
    cancel_min_grade: int = 7            # ab dieser Klassenstufe darf Unterricht entfallen
    edge_strategy: str = "cancel"        # "cancel" | "substitute_if_qualified" | "substitute"
    middle_strategy: str = "shift_first"  # "shift_first" | "substitute_first"
    allow_unqualified: bool = True       # Betreuung durch fachfremde Lehrkraft
    max_subs_per_day: int = 2


@dataclass
class Settings(Model):
    school_name: str = "Meine Schule"
    days: int = 5
    periods: int = 10
    period_times: list[str] = field(default_factory=lambda: [
        "07:55", "08:45", "09:50", "10:40", "11:45", "12:35", "13:30", "14:20", "15:10", "16:00",
    ])
    cycle_start: str = "2026-08-31"      # nur gelesen: Schuljahresbeginn älterer Dokumente (Altfeld)
    # Wochen und Schuljahr (R3): Zählung ab Schuljahresbeginn oder als KW; leer = ``cycle_start``
    week_numbering: str = "iso"          # "iso" (Kalenderwochen, Standard) | "school_year" (Woche 1 = Schuljahresbeginn)
    school_year_start: str = ""
    # Schuljahresbeginn: "auto" = Ende der Sommerferien (aus den Ferien, calendar_utils.apply_auto_year_start),
    # "own" = eigener Schulstart (school_year_start von Hand)
    year_start_mode: str = "auto"
    school_year_history: list[str] = field(default_factory=list)   # Beginn früherer Schuljahre (ISO)
    school_days: list[int] = field(default_factory=list)    # Unterrichtstage 0–6, leer = range(days)
    site_travel_periods: int = 1         # freie Stunden zwischen Standortwechseln (ohne Wegezeiten-Tabelle)
    # Wegezeit je Standortpaar in Minuten: [{"a": "Haupthaus", "b": "Außenstelle", "minutes": 10}]; gilt in beide
    # Richtungen. Fehlt ein Paar, gilt ``site_travel_periods``.
    site_travel: list[dict] = field(default_factory=list)
    core_latest_period: int = 5          # Hauptfächer möglichst bis zur 6. Stunde
    weights: Weights = field(default_factory=Weights)
    policy: SubstitutionPolicy = field(default_factory=SubstitutionPolicy)
    # Abwesende Lehrkräfte in öffentlicher Sicht (Monitor, Aushang/Druck): "off" | "short" (Kürzel) | "name"
    # (Kürzel + Name); Gründe, Stunden und Fallzahlen nie (B-04)
    public_absent_teachers: str = "short"
    webhooks: list[str] = field(default_factory=list)
    # Pausen: nach welcher Stunde (0-basiert) und wie lang
    breaks: list[dict] = field(default_factory=lambda: [
        {"after": 1, "name": "Pause 1", "minutes": 20},
        {"after": 3, "name": "Pause 2", "minutes": 20},
        {"after": 5, "name": "Pause 3", "minutes": 45},
    ])
    # Klassenarbeiten pro Klasse und Woche/Tag – Vorgabe der Schule; je Jahrgang (``exam_limits_by_grade``,
    # ``{"5": {"per_week": 2, "per_day": 1}}``) und je Klasse (``SchoolClass.max_exams_per_*``) überschreibbar
    max_exams_per_week: int = 3
    max_exams_per_day: int = 1
    exam_limits_by_grade: dict = field(default_factory=dict)
    period_minutes: int = 45             # Dauer einer Unterrichtsstunde (für Zeitfenster/Kalender)
    # Lehrer-Selbstverwaltung: "approval" = Planung genehmigt Änderungen, "direct" = sofort gültig
    teacher_self_service: str = "approval"
    # Arbeitszeiten legen Schulleitung/Stundenplanung fest; Lehrkräfte nur, wenn hier erlaubt oder je Lehrkraft
    # freigegeben (Teacher.times_self)
    teacher_times_self: bool = False
    sick_note_after_days: int = 3        # ab so vielen Fehltagen ist ein Attest nötig
    # Telefonische Krankmeldung: Nummer und Zeiten (z. B. „Mo–Fr 7:15–8:00 Uhr“), wird Eltern/Schüler/innen angezeigt
    sick_phone: str = ""
    sick_phone_hours: str = ""
    messaging_students_to_students: bool = True   # Schüler dürfen Schülern schreiben
    messaging_retention_days: int = 365  # Nachrichten danach automatisch löschen (0 = nie)
    trash_retention_days: int = 30       # Kursraum-Papierkorb: gelöschte Elemente so lange wiederherstellbar (1–365)
    # Krankmeldungen für Fachlehrkräfte (B-06): "none" = nichts, "presence" = „fehlt heute in meiner Stunde“
    subject_teacher_absence_view: str = "none"
    # zulässige Fehlzeit je Fach in Prozent der stattgefundenen Stunden (0 = keine Grenze): insgesamt / unentschuldigt
    absence_limit_percent: float = 0.0
    absence_limit_unexcused_percent: float = 0.0
    # Auto-Planer: nach Änderungen an Stammdaten/Planung ungültige oder fehlende Stunden automatisch neu legen
    auto_replan: bool = True
    # Plan prüfen (``docs/PLAN-PRUEFUNG.md``): ob kleine Lösungen ohne Rückfrage übernommen werden dürfen. ``aus`` =
    # nichts ohne Zustimmung (Standard, alle Lösungen kommen als Vorschlagspaket zur Auswahl), ``raeume`` = reine
    # Raumänderungen und das Entfernen verwaister Stunden gelten sofort (Verlauf & Audit, rückgängig möglich)
    plan_auto_apply: str = "aus"
    # Vertretung: ``True`` = automatisch berechnete Vertretungsvorschläge sind erst nach Freigabe durch die
    # Vertretungsplanung im Plan sichtbar (Eltern, Schüler, Lehrkräfte, Monitor, Benachrichtigungen)
    substitution_confirm: bool = False
    # Generator: alle Fächer mit mindestens 2 Wochenstunden als Doppelstunden planen (wo möglich)
    prefer_doubles: bool = True
    # Lage von Doppelstunden: "bloecke" = nur in den Pausenblöcken (1.–2., 3.–4. … – nie über eine Pause, nie
    # versetzt), "pausen" = nur nicht über eine Pause, "frei" = keine Einschränkung
    double_alignment: str = "bloecke"
    # Regeln und Prioritäten als Bausteine (``schulmanager/rules.py``): Vorlage, Stufen, Parameter, Ausnahmen.
    # Die Zahlenfelder oben (``weights``, ``core_latest_period`` …) werden daraus abgeleitet; fehlt ``rules``
    # (ältere Dokumente), werden die Bausteine beim Lesen aus den Zahlen bestimmt.
    rules: dict = field(default_factory=dict)
    # Planzeiträume (``plan_periods.py``): je Zeitraum ein eigener Stundenplan, z. B. 1. und 2. Halbjahr.
    # ``[{"id", "name", "date_from", "date_to", "from_week", "to_week"}]`` (Wochen werden aus den Daten berechnet);
    # leer = ein Plan für das ganze Schuljahr (ältere Dokumente).
    plan_periods: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        s = _from_dict(cls, data)
        if isinstance(s.weights, dict):
            s.weights = Weights.from_dict(s.weights)
        if isinstance(s.policy, dict):
            s.policy = SubstitutionPolicy.from_dict(s.policy)
        if not isinstance(s.rules, dict):
            s.rules = {}
        if not isinstance(s.exam_limits_by_grade, dict):
            s.exam_limits_by_grade = {}
        return s

    def block_start_ok(self, start: int, length: int, periods: Optional[int] = None) -> bool:
        """Darf ein Block (Doppelstunde o. ä.) von ``length`` Stunden in Stunde ``start`` (0-basiert) beginnen?

        Einzelstunden immer. Sonst laut ``double_alignment``: keine Pause innerhalb des Blocks und (``bloecke``) Beginn
        in gerader Entfernung vom Anfang des Pausenblocks – also 1.–2., 3.–4., 5.–6. Stunde usw."""
        if length <= 1 or self.double_alignment == "frei":
            return True
        after = sorted({int(b.get("after", -1)) for b in (self.breaks or []) if isinstance(b, dict)})
        end = start + length - 1
        if any(start <= a < end for a in after):
            return False
        if self.double_alignment != "bloecke":
            return True
        seg_start = max([a + 1 for a in after if a < start] or [0])
        return (start - seg_start) % 2 == 0


COLLECTIONS: dict[str, type] = {
    "sites": Site,
    "subjects": Subject,
    "teachers": Teacher,
    "rooms": Room,
    "classes": SchoolClass,
    "students": Student,
    "curricula": Curriculum,
    "grade_profiles": GradeProfile,
    "courses": Course,
    "lessons": Lesson,
    "absences": Absence,
    "overrides": Override,
    "holidays": Holiday,
    "areas": SupervisionArea,
    "duties": Duty,
    "exams": Exam,
    "events": Event,
}


@dataclass
class School:
    settings: Settings = field(default_factory=Settings)
    sites: list[Site] = field(default_factory=list)
    subjects: list[Subject] = field(default_factory=list)
    teachers: list[Teacher] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    classes: list[SchoolClass] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    curricula: list[Curriculum] = field(default_factory=list)
    grade_profiles: list[GradeProfile] = field(default_factory=list)
    courses: list[Course] = field(default_factory=list)
    lessons: list[Lesson] = field(default_factory=list)
    absences: list[Absence] = field(default_factory=list)
    overrides: list[Override] = field(default_factory=list)
    holidays: list[Holiday] = field(default_factory=list)
    areas: list[SupervisionArea] = field(default_factory=list)
    duties: list[Duty] = field(default_factory=list)
    exams: list[Exam] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    #: Vertretungsmonitore je Standort (``""`` = alle Standorte): Tage, Laufband, Hinweise, Darstellung
    monitors: dict[str, dict] = field(default_factory=dict)
    #: Einstellungen des Ferien-/Feiertags-Imports (``server/holiday_import.py``)
    holiday_import: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"settings": self.settings.to_dict()}
        for name in COLLECTIONS:
            out[name] = [x.to_dict() for x in getattr(self, name)]
        if self.monitors:
            out["monitors"] = {k: dict(v) for k, v in self.monitors.items()}
        if self.holiday_import:
            out["holiday_import"] = dict(self.holiday_import)
        return out

    @classmethod
    def from_dict(cls, data: dict) -> "School":
        from .legacy import migrate_document     # ältere Dokumente mit Wochenzyklus → laufende Wochen
        data = migrate_document(data)
        s = cls(settings=Settings.from_dict(data.get("settings", {})))
        for name, typ in COLLECTIONS.items():
            setattr(s, name, [typ.from_dict(x) for x in data.get(name, [])])
        s.monitors = {str(k): dict(v) for k, v in (data.get("monitors") or {}).items() if isinstance(v, dict)}
        s.holiday_import = dict(data.get("holiday_import") or {})
        return s

    # Schnellzugriff -------------------------------------------------------
    def index(self, name: str) -> dict[str, Any]:
        return {x.id: x for x in getattr(self, name)}
