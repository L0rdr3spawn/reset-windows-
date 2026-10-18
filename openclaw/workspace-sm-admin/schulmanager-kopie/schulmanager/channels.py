"""Kursräume (ARCHITECTURE.md §9.4) – reine Logik über dem Planungsdokument (ohne Datenbank, ohne Server).

Kanäle
------
* **Kurs-Kanal je Kursteil**: ``kind="course"``, ``ref="<kurs>#<teil>"`` (Schreibweise wie ``Student.courses``),
  auch bei Ein-Teil-Kursen (``"5a-M#0"``). Kopplungen/Schienen (Religion ev/kath/PP, Q1-LK1 mit M-LK1, E-LK1 …)
  sind getrennte Lerngruppen mit eigener Lehrkraft – deshalb ein Kanal je Teil.
  Lehrende: Lehrkraft des Kursteils. Teilnehmende: Schüler der Kursklassen, die laut
  :func:`schulmanager.timetable.student_parts` diesen Teil besuchen (ohne Wahl → alle Teile, wie in der Anzeige).
* **Klassen-Kanal**: ``kind="class"``, ``ref=<klasse>``. Lehrende: Klassenleitung + alle Lehrkräfte mit Unterricht
  in der Klasse (bei Kopplungen über mehrere Klassen nur in den Klassen, aus denen Schüler/innen ihren Kursteil
  besuchen); Teilnehmende: alle Schüler der Klasse. Fremdes Material schützt der Server (nur Ersteller/in,
  Klassenleitung, Kursraum-Verwaltung).
* Rollen werden bei jedem Zugriff **dynamisch** aus dem Planungsdokument bestimmt (siehe ``server/routes/
  features_channels.py`` für Konten, Zusatzmitglieder und Rechte).

Sichtbarkeit von Material
-------------------------
``visible`` (sofort), ``hidden`` (nie für Schüler), ``scheduled`` (ab ``visible_from``), ``lesson`` (ab Beginn der
gebundenen Unterrichtsstunde laut ``settings.period_times``; wird die Stunde am selben Tag verlegt, gilt der neue
Beginn; entfällt sie oder ist schulfrei, gilt die nächste stattfindende Stunde desselben Kurses –
:func:`next_held_lesson`). Ordner haben dieselben Freigaben; ein nicht freigegebener Ordner verbirgt alles darin
(:func:`folder_states`). Zeitpunkte sind naive **UTC**-Datetimes (DB-Konvention);
Stundenzeiten sind Ortszeit des Servers (``TZ``, z. B. Europe/Berlin) und werden umgerechnet.

Kommende Stunden
----------------
:func:`upcoming_lessons` liefert die Unterrichtsblöcke eines Kanals in den nächsten Wochen aus dem Stundenplan
(Wochentag und laufende Woche, zentrale Aktiv-Logik ``weeks.lesson_active_in``), überspringt Ferien/Feiertage
(als ``skipped`` gemeldet) und markiert Änderungen aus dem Vertretungsplan (Entfall, Verlegung, Vertretung,
Raumänderung, Klausur). Der Tagesplan wird über eine übergebene Funktion geholt (Server: gecachter ``day_plan``)
und nur an Tagen mit möglichen Änderungen (Abwesenheiten, Overrides, Klausuren, Sperrzeit-Konflikten) berechnet.
"""
from __future__ import annotations

import re
import threading
import weakref
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Optional
from urllib.parse import urlsplit

from .calendar_utils import is_school_day, period_label, period_time
from .models import Course, Lesson, School, Student

COURSE = "course"
CLASS = "class"
CUSTOM = "custom"
KINDS = (COURSE, CLASS, CUSTOM)
MAX_UPCOMING_DAYS = 8 * 7
DEFAULT_UPCOMING_DAYS = 4 * 7
WEEKDAYS_SHORT = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")

_CANCEL_KINDS = frozenset({"entfall", "klasse_abwesend"})
_SUB_KINDS = frozenset({"vertretung", "betreuung", "mitbetreuung"})


# =========================================================================== Zeit
def now_utc() -> datetime:
    """Aktuelle Zeit (naive UTC). In Tests per ``monkeypatch.setattr(channels, "now_utc", …)`` ersetzbar."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_to_utc(dt: datetime) -> datetime:
    """Naive Ortszeit (Server-``TZ``) → naive UTC (zeitzonenbehaftete Werte werden direkt umgerechnet)."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def utc_to_local(dt: datetime) -> datetime:
    """Naive UTC → naive Ortszeit (Server-``TZ``)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().replace(tzinfo=None)


def local_today(now: Optional[datetime] = None) -> date:
    """Heutiges Datum in Ortszeit (aus :func:`now_utc`)."""
    return utc_to_local(now or now_utc()).date()


def parse_hhmm(value: str) -> Optional[tuple[int, int]]:
    try:
        h, m = (int(x) for x in str(value).split(":")[:2])
    except (TypeError, ValueError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return h, m


def period_start_local(settings, day: date, period: int) -> Optional[datetime]:
    """Beginn der Stunde ``period`` (0-basiert) am ``day`` in Ortszeit (``None`` ohne Zeitangabe)."""
    hm = parse_hhmm(period_time(settings, period))
    if hm is None:
        return None
    return datetime(day.year, day.month, day.day, hm[0], hm[1])


def period_end_hhmm(settings, period: int) -> str:
    """Ende der Stunde ``period`` als ``HH:MM`` (Beginn + ``period_minutes``)."""
    hm = parse_hhmm(period_time(settings, period))
    if hm is None:
        return ""
    total = hm[0] * 60 + hm[1] + int(getattr(settings, "period_minutes", 45) or 45)
    total = min(total, 23 * 60 + 59)
    return f"{total // 60:02d}:{total % 60:02d}"


def lesson_release_utc(settings, day: date, period: int) -> Optional[datetime]:
    """Freigabezeitpunkt (UTC) für Material „zur Stunde“: Beginn der Stunde in Ortszeit."""
    start = period_start_local(settings, day, period)
    return local_to_utc(start) if start else None


# =========================================================================== Kanal-Beschreibung
def course_ref(course_id: str, part: int) -> str:
    return f"{course_id}#{int(part)}"


def parse_course_ref(ref: str) -> Optional[tuple[str, int]]:
    """``"<kurs>#<teil>"`` → ``(kurs, teil)``; ``None`` bei ungültiger Schreibweise."""
    if not isinstance(ref, str) or "#" not in ref:
        return None
    cid, _, idx = ref.rpartition("#")
    if not cid or not idx.isdigit() or len(idx) > 3:
        return None
    return cid, int(idx)


@dataclass(frozen=True)
class ChannelSpec:
    """Beschreibung eines automatischen Kanals (aus dem Planungsdokument berechnet)."""
    kind: str
    ref: str
    title: str
    subtitle: str = ""
    course_id: Optional[str] = None
    part: Optional[int] = None
    class_ids: tuple[str, ...] = ()
    subject: Optional[str] = None
    subject_name: Optional[str] = None
    teacher_ids: tuple[str, ...] = ()
    class_teacher: Optional[str] = None
    grade: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "title": self.title, "subtitle": self.subtitle,
                "course_id": self.course_id, "part": self.part, "classes": list(self.class_ids),
                "subject": self.subject, "subject_name": self.subject_name, "teacher_ids": list(self.teacher_ids),
                "class_teacher": self.class_teacher, "grade": self.grade}


def _natural(s: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s or ""))


class SchoolIndex:
    """Abgeleitete Nachschlagetabellen eines Planungsdokuments (je ``School``-Objekt einmal berechnet)."""

    def __init__(self, school: School) -> None:
        self.school = school
        self.subjects = school.index("subjects")
        self.classes = school.index("classes")
        self.teachers = school.index("teachers")
        self.courses = school.index("courses")
        self.students = school.index("students")
        self.lessons = school.index("lessons")
        self.students_by_class: dict[str, list[Student]] = defaultdict(list)
        for st in school.students:
            self.students_by_class[st.class_id].append(st)
        self.lessons_by_course: dict[str, list[Lesson]] = defaultdict(list)
        for les in school.lessons:
            self.lessons_by_course[les.course_id].append(les)
        for lst in self.lessons_by_course.values():
            lst.sort(key=lambda le: (le.day, le.start, le.id))
        self.courses_by_class: dict[str, list[Course]] = defaultdict(list)
        self.parts_by_teacher: dict[str, list[tuple[str, int]]] = defaultdict(list)
        self.classes_by_teacher: dict[str, set[str]] = defaultdict(set)
        self.teachers_by_class: dict[str, set[str]] = defaultdict(set)
        for c in school.courses:
            for cid in c.classes:
                self.courses_by_class[cid].append(c)
            coupled = len(c.parts) > 1 and len(c.classes) > 1
            for i, p in enumerate(c.parts):
                if p.teacher:
                    self.parts_by_teacher[p.teacher].append((c.id, i))
                    for cid in c.classes:
                        if coupled and not self._class_attends(c, i, cid):
                            continue
                        self.classes_by_teacher[p.teacher].add(cid)
                        self.teachers_by_class[cid].add(p.teacher)
        for cls in school.classes:
            if cls.class_teacher:
                self.classes_by_teacher[cls.class_teacher].add(cls.id)

    def _class_attends(self, course: Course, part: int, class_id: str) -> bool:
        """Besucht mindestens ein/e Schüler/in der Klasse den Kursteil (Klasse ohne Schüler/innen: ja)?"""
        students = self.students_by_class.get(class_id, ())
        return not students or any(part in student_course_parts(st, course) for st in students)

    def class_name(self, class_id: str) -> str:
        cls = self.classes.get(class_id)
        return cls.name if cls and cls.name else class_id

    def subject_name(self, subject: Optional[str]) -> str:
        if not subject:
            return ""
        sub = self.subjects.get(subject)
        return sub.name if sub and sub.name else subject

    def teacher_name(self, teacher_id: Optional[str]) -> str:
        if not teacher_id:
            return ""
        t = self.teachers.get(teacher_id)
        return t.name if t and t.name else teacher_id


_index_lock = threading.Lock()
_index_slot: tuple[Any, SchoolIndex] | None = None


def index_for(school: School) -> SchoolIndex:
    """:class:`SchoolIndex` des Dokuments (Ein-Platz-Cache – der Store ersetzt das Dokument bei jeder Änderung)."""
    global _index_slot
    slot = _index_slot
    if slot is not None and slot[0]() is school:
        return slot[1]
    idx = SchoolIndex(school)
    with _index_lock:
        _index_slot = (weakref.ref(school), idx)
    return idx


def _class_title(name: str, class_id: str) -> str:
    label = name or class_id
    return f"Klasse {label}" if len(label) <= 6 else label


def _class_list(classes: Iterable[str], sep: str = "/") -> str:
    """Kurze Klassenliste für Titel: ``5a/5b``; bei mehr als drei Klassen ``Q1-1 … Q1-5``."""
    ids = list(classes)
    if len(ids) > 3:
        return f"{ids[0]} … {ids[-1]}"
    return sep.join(ids)


def course_part_spec(idx: SchoolIndex, course: Course, part: int) -> Optional[ChannelSpec]:
    """Kanal eines Kursteils, Titel z. B. „Deutsch 5a“, „Kath. Religion · Religion/PP 5a+5b“ oder
    „Mathematik M-LK1 · Q1 LK-Schiene 1“ (Teilbezeichnung nur, wenn sie mehr sagt als das Fach)."""
    if not 0 <= part < len(course.parts):
        return None
    p = course.parts[part]
    classes = tuple(sorted(course.classes, key=_natural))
    class_names = ", ".join(idx.class_name(c) for c in classes)
    subject_name = idx.subject_name(p.subject) or p.subject or course.id
    if len(course.parts) > 1:
        head = subject_name
        label = (p.label or "").strip()
        if label and len(label) > 4 and label.lower() not in head.lower():
            head = f"{head} {label}"
        title = f"{head} · {course.label}" if course.label else f"{head} {_class_list(classes)}"
    else:
        title = course.label or f"{subject_name} {_class_list(classes)}"
    teacher = idx.teacher_name(p.teacher)
    extra = p.label if len(course.parts) > 1 and p.label else ""
    subtitle = " · ".join(x for x in (extra, teacher, class_names) if x)
    grades = [idx.classes[c].grade for c in classes if c in idx.classes]
    return ChannelSpec(kind=COURSE, ref=course_ref(course.id, part), title=title[:200], subtitle=subtitle[:300],
                       course_id=course.id, part=part, class_ids=classes, subject=p.subject,
                       subject_name=subject_name or None, teacher_ids=(p.teacher,) if p.teacher else (),
                       grade=min(grades) if grades else None)


def class_spec(idx: SchoolIndex, class_id: str) -> Optional[ChannelSpec]:
    cls = idx.classes.get(class_id)
    if cls is None:
        return None
    teachers = set(idx.teachers_by_class.get(class_id, set()))
    if cls.class_teacher:
        teachers.add(cls.class_teacher)
    ordered = tuple(sorted(teachers, key=lambda t: (t != cls.class_teacher, _natural(t))))
    lead = idx.teacher_name(cls.class_teacher)
    n = len(idx.students_by_class.get(class_id, ()))
    parts = [f"Klassenleitung {lead}" if lead else "", f"{n} Schüler/innen" if n else ""]
    return ChannelSpec(kind=CLASS, ref=class_id, title=_class_title(cls.name, cls.id)[:200],
                       subtitle=" · ".join(x for x in parts if x), class_ids=(class_id,), teacher_ids=ordered,
                       class_teacher=cls.class_teacher, grade=cls.grade)


def channel_spec(school: School, kind: str, ref: str) -> Optional[ChannelSpec]:
    """Beschreibung eines Kurs-/Klassenkanals oder ``None`` (Kurs/Teil/Klasse existiert nicht mehr)."""
    idx = index_for(school)
    if kind == COURSE:
        parsed = parse_course_ref(ref)
        if parsed is None:
            return None
        course = idx.courses.get(parsed[0])
        return course_part_spec(idx, course, parsed[1]) if course else None
    if kind == CLASS:
        return class_spec(idx, ref)
    return None


def all_specs(school: School) -> list[ChannelSpec]:
    """Alle automatischen Kanäle: Kursteile (aller Kurse mit Teilen) und Klassen."""
    idx = index_for(school)
    out: list[ChannelSpec] = []
    for c in school.courses:
        for i in range(len(c.parts)):
            spec = course_part_spec(idx, c, i)
            if spec:
                out.append(spec)
    for cls in school.classes:
        spec = class_spec(idx, cls.id)
        if spec:
            out.append(spec)
    return out


# =========================================================================== Mitgliedschaft
def student_course_parts(student: Student, course: Course) -> list[int]:
    """Besuchte Teile eines Kurses (wie ``timetable.student_parts`` für genau einen Kurs, leer = nicht im Kurs)."""
    if student.class_id not in course.classes or not course.parts:
        return []
    if len(course.parts) <= 1:
        return [0]
    sel: set[int] = set()
    prefix = f"{course.id}#"
    for ref in student.courses:
        if ref.startswith(prefix):
            idx = ref[len(prefix):]
            if idx.isdigit():
                sel.add(int(idx))
    for i, p in enumerate(course.parts):
        if p.students and student.id in p.students:
            sel.add(i)
    sel = {i for i in sel if 0 <= i < len(course.parts)}
    return sorted(sel) if sel else list(range(len(course.parts)))


def channel_teacher_ids(school: School, kind: str, ref: str) -> list[str]:
    spec = channel_spec(school, kind, ref)
    return list(spec.teacher_ids) if spec else []


def channel_student_ids(school: School, kind: str, ref: str) -> list[str]:
    """Schüler-IDs (Planungsdokument) eines Kurs-/Klassenkanals."""
    idx = index_for(school)
    if kind == CLASS:
        return [s.id for s in idx.students_by_class.get(ref, ())]
    if kind != COURSE:
        return []
    parsed = parse_course_ref(ref)
    if parsed is None:
        return []
    course = idx.courses.get(parsed[0])
    if course is None or not 0 <= parsed[1] < len(course.parts):
        return []
    out: list[str] = []
    for cid in course.classes:
        for st in idx.students_by_class.get(cid, ()):
            if parsed[1] in student_course_parts(st, course):
                out.append(st.id)
    return out


def is_channel_teacher(school: School, kind: str, ref: str, teacher_id: Optional[str]) -> bool:
    return bool(teacher_id) and teacher_id in channel_teacher_ids(school, kind, ref)


def is_channel_student(school: School, kind: str, ref: str, student_id: Optional[str]) -> bool:
    if not student_id:
        return False
    idx = index_for(school)
    st = idx.students.get(student_id)
    if st is None:
        return False
    if kind == CLASS:
        return st.class_id == ref
    parsed = parse_course_ref(ref) if kind == COURSE else None
    if parsed is None:
        return False
    course = idx.courses.get(parsed[0])
    return course is not None and parsed[1] in student_course_parts(st, course)


def teacher_specs(school: School, teacher_id: Optional[str]) -> list[ChannelSpec]:
    """Kanäle, in denen die Lehrkraft lehrt: ihre Kursteile und ihre Klassen (Unterricht oder Klassenleitung)."""
    if not teacher_id:
        return []
    idx = index_for(school)
    out: list[ChannelSpec] = []
    for cid, part in idx.parts_by_teacher.get(teacher_id, ()):
        course = idx.courses.get(cid)
        spec = course_part_spec(idx, course, part) if course else None
        if spec:
            out.append(spec)
    for class_id in sorted(idx.classes_by_teacher.get(teacher_id, ()), key=_natural):
        spec = class_spec(idx, class_id)
        if spec:
            out.append(spec)
    return out


def student_specs(school: School, student_id: Optional[str]) -> list[ChannelSpec]:
    """Kanäle einer Schülerin/eines Schülers: besuchte Kursteile und die eigene Klasse."""
    if not student_id:
        return []
    idx = index_for(school)
    st = idx.students.get(student_id)
    if st is None:
        return []
    out: list[ChannelSpec] = []
    for course in idx.courses_by_class.get(st.class_id, ()):
        for part in student_course_parts(st, course):
            spec = course_part_spec(idx, course, part)
            if spec:
                out.append(spec)
    spec = class_spec(idx, st.class_id)
    if spec:
        out.append(spec)
    return out


# =========================================================================== Sichtbarkeit
@dataclass(frozen=True)
class Visibility:
    """Sichtbarkeit eines Materials für Teilnehmende zum Zeitpunkt ``now``.

    ``code``: ``visible`` (freigegeben), ``hidden`` (verborgen), ``folder_hidden`` (Ordner verborgen),
    ``scheduled`` (geplant, noch nicht sichtbar), ``lesson`` (zur Stunde, noch nicht sichtbar).
    ``release_at``: Freigabezeitpunkt (UTC) bei geplanten/stundengebundenen Inhalten.
    """
    visible: bool
    code: str
    release_at: Optional[datetime] = None


def item_visibility(visibility: str, visible_from: Optional[datetime], *, now: datetime,
                    folder_hidden: bool = False, release_override: Optional[datetime] = None,
                    folder: Optional[Visibility] = None) -> Visibility:
    """Sichtbarkeit für Teilnehmende. ``release_override`` = abweichender Stundenbeginn (Verlegung am Tag);
    ``folder`` = Zustand des Ordners (aus :func:`folder_states`; nicht sichtbar → ``folder_hidden`` mit dem
    spätesten Freigabezeitpunkt von Ordner und Material bzw. ohne Zeitpunkt, wenn einer davon verborgen ist)."""
    release = release_override or visible_from
    if visibility == "hidden":
        return Visibility(False, "hidden")
    if folder is not None and not folder.visible:
        own = item_visibility(visibility, visible_from, now=now, release_override=release_override)
        when = _later(folder.release_at, own.release_at if not own.visible else None,
                      unknown=own.code in ("scheduled", "lesson") and own.release_at is None)
        return Visibility(False, "folder_hidden", when)
    if folder_hidden:
        return Visibility(False, "folder_hidden", release if visibility in ("scheduled", "lesson") else None)
    if visibility in ("scheduled", "lesson"):
        if release is None:  # ohne Zeitpunkt (z. B. Stunde ohne Uhrzeit) nicht freigeben
            return Visibility(False, visibility)
        if release <= now:
            return Visibility(True, "visible", release)
        return Visibility(False, visibility, release)
    return Visibility(True, "visible")


def _later(a: Optional[datetime], b: Optional[datetime], *, unknown: bool = False) -> Optional[datetime]:
    """Späterer von zwei Freigabezeitpunkten (``a`` ``None`` = nie bzw. ``unknown`` = ohne Zeitpunkt)."""
    if a is None or unknown:
        return None
    return max(a, b) if b is not None else a


def folder_states(folders: Iterable[Any], *, now: datetime,
                  release_of: Optional[Callable[[Any], Optional[datetime]]] = None) -> dict[int, Visibility]:
    """Wirksamer Zustand je Ordner für Teilnehmende (eigene Freigabe + alle übergeordneten Ordner).

    ``folder.visibility`` (``NULL`` = nur ``hidden``) wie beim Material; ``release_of(folder)`` liefert den
    Freigabezeitpunkt geplanter/stundengebundener Ordner (Standard: ``visible_from``). Zyklen-/Tiefenschutz 64.
    """
    by_id = {f.id: f for f in folders}
    memo: dict[int, Visibility] = {}

    def own(f: Any) -> Visibility:
        vis = "hidden" if getattr(f, "hidden", False) else (getattr(f, "visibility", None) or "visible")
        rel = release_of(f) if release_of is not None and vis in ("scheduled", "lesson") else \
            getattr(f, "visible_from", None)
        return item_visibility(vis, rel, now=now)

    def state(fid: int, depth: int = 0) -> Visibility:
        if fid in memo:
            return memo[fid]
        f = by_id[fid]
        mine = own(f)
        parent = by_id.get(f.parent_id) if f.parent_id is not None and depth < 64 else None
        if parent is not None:
            up = state(parent.id, depth + 1)
            if not up.visible:
                mine = Visibility(False, mine.code if not mine.visible else "folder_hidden",
                                  _later(up.release_at, mine.release_at if not mine.visible else None,
                                         unknown=not mine.visible and mine.release_at is None))
        memo[fid] = mine
        return mine

    return {fid: state(fid) for fid in by_id}


def hidden_folder_ids(folders: Iterable[Any]) -> set[int]:
    """IDs aller Ordner, die selbst oder über einen übergeordneten Ordner verborgen sind."""
    by_id = {f.id: f for f in folders}
    memo: dict[int, bool] = {}

    def hidden(fid: Optional[int], depth: int = 0) -> bool:
        if fid is None or fid not in by_id or depth > 64:
            return False
        if fid in memo:
            return memo[fid]
        f = by_id[fid]
        memo[fid] = bool(f.hidden) or hidden(f.parent_id, depth + 1)
        return memo[fid]

    return {fid for fid in by_id if hidden(fid)}


def folder_path_ids(folders: Iterable[Any], folder_id: Optional[int]) -> list[int]:
    """Pfad (Wurzel → Ordner) als ID-Liste; leer für die Wurzel/unbekannte Ordner."""
    by_id = {f.id: f for f in folders}
    out: list[int] = []
    cur = folder_id
    while cur is not None and cur in by_id and cur not in out and len(out) < 64:
        out.append(cur)
        cur = by_id[cur].parent_id
    return list(reversed(out))


def descendant_folder_ids(folders: Iterable[Any], folder_id: int) -> set[int]:
    """Alle Unterordner (rekursiv, ohne den Ordner selbst)."""
    children: dict[Optional[int], list[int]] = defaultdict(list)
    for f in folders:
        children[f.parent_id].append(f.id)
    out: set[int] = set()
    stack = list(children.get(folder_id, ()))
    while stack:
        fid = stack.pop()
        if fid in out:
            continue
        out.add(fid)
        stack.extend(children.get(fid, ()))
    return out


# =========================================================================== Unterrichtsstunden
def lesson_active_on(school: School, lesson: Lesson, course: Course, day: date, _idx: Any = None) -> bool:
    """Findet der Block am ``day`` statt (Wochentag + laufende Woche, ohne Ferien/Vertretungsplan)?"""
    from .weeks import lesson_active_on as active
    return active(school, lesson, course, day, _idx)


def channel_class(school: School, kind: str, ref: str) -> Optional[str]:
    """Bezugsklasse eines Kursraums für Unterrichtstage: Klassen-Kanal → die Klasse, Kurs-Kanal → erste Klasse des
    Kurses (gekoppelte Kurse liegen nur an gemeinsamen Tagen), sonst ``None`` (Schulöffnungstage)."""
    if kind == "class":
        return ref or None
    if kind == "course":
        course = school.index("courses").get((ref or "").partition("#")[0])
        return course.classes[0] if course and course.classes else None
    return None


def day_has_changes(school: School, day: date) -> bool:
    """Kann der Vertretungsplan an ``day`` Einträge haben (Abwesenheiten, Overrides, Klausuren)?"""
    iso = day.isoformat()
    for a in school.absences:
        if str(a.date_from)[:10] <= iso <= str(a.date_to)[:10]:
            return True
    for o in school.overrides:
        if str(o.date)[:10] == iso:
            return True
    for ex in school.exams:
        if str(ex.date)[:10] == iso:
            return True
    return False


def _rule_conflict(idx: SchoolIndex, course: Course, lesson: Lesson, day: date) -> bool:
    """Liegt der Block in einer Sperrzeit einer Kursklasse (z. B. Praxistag nach manueller Verschiebung)?"""
    from .weeks import real_week
    real = real_week(idx.school, day)
    for cid in course.classes:
        cls = idx.classes.get(cid)
        if cls is None:
            continue
        for rule in cls.unavailable:
            for p in range(lesson.start, lesson.start + max(1, lesson.length)):
                if rule.matches(real, day.weekday(), p):
                    return True
    return False


def channel_lessons(school: School, kind: str, ref: str, teacher_id: Optional[str] = None
                    ) -> list[tuple[Lesson, Course, tuple[int, ...]]]:
    """Unterrichtsblöcke eines Kanals mit den relevanten Kursteilen.

    Kurs-Kanal: Blöcke des Kurses (Teil des Kanals). Klassen-Kanal: Blöcke aller Kurse der Klasse
    (mit ``teacher_id`` nur die Kurse/Teile dieser Lehrkraft).
    """
    idx = index_for(school)
    out: list[tuple[Lesson, Course, tuple[int, ...]]] = []
    if kind == COURSE:
        parsed = parse_course_ref(ref)
        course = idx.courses.get(parsed[0]) if parsed else None
        if course is None or not 0 <= parsed[1] < len(course.parts):
            return []
        for les in idx.lessons_by_course.get(course.id, ()):
            out.append((les, course, (parsed[1],)))
        return out
    if kind == CLASS:
        for course in idx.courses_by_class.get(ref, ()):
            parts = tuple(i for i, p in enumerate(course.parts) if not teacher_id or p.teacher == teacher_id)
            if not parts:
                continue
            for les in idx.lessons_by_course.get(course.id, ()):
                out.append((les, course, parts))
    return out


def moved_period(plan: Optional[dict], lesson_id: str, period: int, part: Optional[int] = None) -> Optional[int]:
    """Neue Stunde, wenn der Block ``lesson_id`` (ab ``period``) laut Tagesplan verlegt wurde."""
    for e in (plan or {}).get("entries") or ():
        if (e.get("kind") == "verlegung" and e.get("lesson_id") == lesson_id and e.get("moved_from") == period
                and (part is None or e.get("part", 0) == part)):
            return int(e["period"])
    return None


def _lesson_changes(plan: Optional[dict], lesson: Lesson, course: Course, parts: tuple[int, ...],
                    idx: SchoolIndex) -> dict[str, Any]:
    """Änderungen eines Blocks laut Tagesplan (Entfall/Verlegung/Vertretung/Raum/Klausur)."""
    periods = list(range(lesson.start, lesson.start + max(1, lesson.length)))
    units = {(p, part) for p in periods for part in parts}
    cancelled: set[tuple[int, int]] = set()
    moved: dict[tuple[int, int], int] = {}
    subs: list[str] = []
    rooms: list[str] = []
    notes: list[str] = []
    exams: list[str] = []
    for e in (plan or {}).get("entries") or ():
        kind = e.get("kind")
        part = int(e.get("part") or 0)
        if kind == "klausur":
            if e.get("course_id") == course.id and e.get("period") in periods and (
                    e.get("exam_part") is None or e.get("exam_part") in parts):
                exams.append(str(e.get("title") or "Klausur"))
            continue
        if e.get("lesson_id") != lesson.id or part not in parts:
            continue
        if kind == "verlegung":
            src = e.get("moved_from")
            if src in periods:
                moved[(int(src), part)] = int(e["period"])
            continue
        p = e.get("period")
        if (p, part) not in units:
            continue
        if kind in _CANCEL_KINDS:
            cancelled.add((p, part))
            if e.get("note"):
                notes.append(str(e["note"]))
        elif kind in _SUB_KINDS:
            if e.get("substitute"):
                subs.append(str(e["substitute"]))
            if e.get("new_room"):
                rooms.append(str(e["new_room"]))
        elif kind == "raumaenderung" and e.get("new_room"):
            rooms.append(str(e["new_room"]))
    gone = cancelled | set(moved)
    if moved and set(moved) >= units:
        status = "verlegt"
    elif units and gone >= units:
        status = "entfall"
    elif gone or subs or rooms:
        status = "geaendert"
    else:
        status = "normal"
    labels: list[str] = []
    if status == "verlegt":
        new = sorted(set(moved.values()))
        labels.append("verlegt in die " + ", ".join(f"{p + 1}." for p in new) + " Stunde")
    elif status == "entfall":
        labels.append("Entfall")
    else:
        if cancelled:
            labels.append("Entfall " + ", ".join(sorted({f"{p + 1}." for p, _ in cancelled})) + " Std.")
        if moved:
            labels.append("teilweise verlegt")
    if subs:
        names = sorted(set(subs))
        labels.append("Vertretung: " + ", ".join(names))
    if rooms:
        labels.append("Raum → " + ", ".join(sorted(set(rooms))))
    if exams:
        labels.append("Klausur: " + ", ".join(dict.fromkeys(exams)))
    moved_to = min(moved.values()) if status == "verlegt" else None
    return {"status": status, "labels": labels, "moved_to": moved_to, "substitutes": sorted(set(subs)),
            "new_rooms": sorted(set(rooms)), "exam": exams[0] if exams else None,
            "notes": list(dict.fromkeys(notes))[:3]}


def lesson_key(day: date | str, lesson_id: str, period: int) -> str:
    return f"{day if isinstance(day, str) else day.isoformat()}:{lesson_id}:{int(period)}"


def _lesson_entry(idx: SchoolIndex, day: date, lesson: Lesson, course: Course, parts: tuple[int, ...],
                  plan: Optional[dict], now: datetime) -> dict[str, Any]:
    st = idx.school.settings
    ch = _lesson_changes(plan, lesson, course, parts, idx)
    length = max(1, lesson.length)
    last = lesson.start + length - 1
    effective = ch["moved_to"] if ch["moved_to"] is not None else lesson.start
    release = lesson_release_utc(st, day, effective)
    from .weeks import real_week
    week_no = real_week(idx.school, day)
    subjects = [course.parts[i].subject for i in parts if i < len(course.parts)]
    teachers = [course.parts[i].teacher for i in parts if i < len(course.parts) and course.parts[i].teacher]
    rooms = [lesson.rooms[i] for i in parts if i < len(lesson.rooms) and lesson.rooms[i]]
    plabel = period_label(lesson.start) if length == 1 else f"{lesson.start + 1}.–{last + 1}."
    time = period_time(st, effective)
    end = period_end_hhmm(st, last if ch["moved_to"] is None else ch["moved_to"] + length - 1)
    label = f"{WEEKDAYS_SHORT[day.weekday()]}, {day.strftime('%d.%m.')} · {plabel} Std."
    if time:
        label += f" · {time}"
    return {
        "key": lesson_key(day, lesson.id, lesson.start), "date": day.isoformat(), "weekday": day.weekday(),
        "week_no": week_no, "lesson_id": lesson.id,
        "course_id": course.id,
        "parts": list(parts), "period": lesson.start, "length": length, "period_label": plabel,
        "effective_period": effective, "time": time, "end_time": end, "label": label,
        "subject": subjects[0] if len(set(subjects)) == 1 else "/".join(dict.fromkeys(subjects)),
        "subject_name": idx.subject_name(subjects[0]) if len(set(subjects)) == 1 else "",
        "teachers": list(dict.fromkeys(teachers)), "rooms": list(dict.fromkeys(rooms)),
        "classes": list(course.classes), "status": ch["status"], "changes": ch["labels"],
        "moved_to": ch["moved_to"], "substitutes": ch["substitutes"], "new_rooms": ch["new_rooms"],
        "exam": ch["exam"], "release_at": release, "started": bool(release and release <= now),
    }


def upcoming_lessons(school: School, kind: str, ref: str, start: date, days: int = DEFAULT_UPCOMING_DAYS, *,
                     plan_for: Optional[Callable[[date], Optional[dict]]] = None, teacher_id: Optional[str] = None,
                     now: Optional[datetime] = None, limit: int = 300) -> dict[str, Any]:
    """Kommende Unterrichtsblöcke eines Kanals ab ``start`` (einschließlich) für ``days`` Tage.

    Rückgabe ``{"from", "to", "lessons": [...], "skipped": [{"date","reason","count"}]}``; je Block ``key``
    (``"<datum>:<lesson_id>:<stunde>"``), ``date``, ``period`` (geplanter Beginn, 0-basiert), ``length``,
    ``effective_period`` (bei Verlegung die neue Stunde), ``time``/``end_time`` (Ortszeit), ``label``,
    ``status`` (``normal|geaendert|entfall|verlegt``), ``changes`` (deutsche Hinweise), ``release_at`` (UTC-
    Datetime des Stundenbeginns = Freigabezeitpunkt), ``started``. ``plan_for(day)`` liefert den Tagesplan
    (``DayPlan.to_dict()``) – nur an Tagen mit möglichen Änderungen aufgerufen.
    """
    days = max(1, min(int(days), MAX_UPCOMING_DAYS))
    now = now or now_utc()
    idx = index_for(school)
    blocks = channel_lessons(school, kind, ref, teacher_id)
    end = start + timedelta(days=days - 1)
    out: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    if blocks:
        from .weeks import ActiveIndex
        aidx = ActiveIndex(school)
        day = start
        while day <= end and len(out) < limit:
            todays = [(les, c, p) for les, c, p in blocks if lesson_active_on(school, les, c, day, aidx)]
            if todays:
                ok, reason = is_school_day(school, day)
                if not ok:
                    skipped.append({"date": day.isoformat(), "reason": reason or "schulfrei", "count": len(todays)})
                else:
                    plan = None
                    if plan_for is not None and (day_has_changes(school, day)
                                                 or any(_rule_conflict(idx, c, les, day) for les, c, _ in todays)):
                        plan = plan_for(day)
                    for les, course, parts in sorted(todays, key=lambda x: (x[0].start, x[1].id, x[0].id)):
                        out.append(_lesson_entry(idx, day, les, course, parts, plan, now))
            day += timedelta(days=1)
    return {"from": start.isoformat(), "to": end.isoformat(), "lessons": out[:limit], "skipped": skipped}


def next_held_lesson(school: School, kind: str, ref: str, after: date, after_period: int = -1, *,
                     course_id: Optional[str] = None, teacher_id: Optional[str] = None,
                     plan_for: Optional[Callable[[date], Optional[dict]]] = None, now: Optional[datetime] = None,
                     days: int = MAX_UPCOMING_DAYS, not_started: bool = False) -> Optional[dict[str, Any]]:
    """Erste Stunde des Kanals nach (``after``, ``after_period``), die stattfindet (nicht Entfall/schulfrei),
    optional nur desselben Kurses (``course_id``) bzw. der Lehrkraft; ``not_started`` = noch nicht begonnen."""
    now = now or now_utc()
    res = upcoming_lessons(school, kind, ref, after, days, plan_for=plan_for, teacher_id=teacher_id, now=now)
    for les in res["lessons"]:
        if les["date"] == after.isoformat() and les["period"] <= after_period:
            continue
        if course_id and les["course_id"] != course_id:
            continue
        if les["status"] == "entfall" or (not_started and les["started"]):
            continue
        return les
    return None


def find_lesson(school: School, kind: str, ref: str, day: date, lesson_id: str, period: int, *,
                plan: Optional[dict] = None, now: Optional[datetime] = None) -> Optional[dict[str, Any]]:
    """Einen Block (Datum, Lesson, geplanter Beginn) eines Kanals prüfen und beschreiben (``None`` = gibt es nicht)."""
    idx = index_for(school)
    for les, course, parts in channel_lessons(school, kind, ref):
        if les.id != lesson_id or les.start != period:
            continue
        if not lesson_active_on(school, les, course, day):
            return None
        return _lesson_entry(idx, day, les, course, parts, plan, now or now_utc())
    return None


# =========================================================================== Eingaben prüfen
_URL_BAD = re.compile(r"[\s\x00-\x1f\x7f<>\"\\^`{|}]")


def clean_url(value: str) -> Optional[str]:
    """Nur ``http``/``https``-Adressen mit Host (keine ``javascript:``/``data:``-Links); ``None`` = ungültig."""
    url = (value or "").strip()
    if not url or len(url) > 2000 or _URL_BAD.search(url):
        return None
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc or parts.username or parts.password:
        return None
    return url


def clean_text(value: Optional[str], max_length: int) -> str:
    """Text säubern: Steuerzeichen (außer Zeilenumbruch/Tab) entfernen, Zeilenenden vereinheitlichen, kürzen."""
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    return text.strip()[:max_length]


def clean_name(value: Optional[str], max_length: int = 120) -> str:
    """Einzeiliger Name (Ordner, Titel): Steuerzeichen/Zeilenumbrüche entfernen, Leerraum zusammenfassen."""
    text = "".join(ch if ord(ch) >= 32 else " " for ch in (value or ""))
    return re.sub(r"\s+", " ", text).strip()[:max_length]


# =========================================================================== Anzeige-Helfer
def lesson_label(settings, day: date, period: int, length: int = 1) -> str:
    """Kurzbeschreibung einer Unterrichtsstunde, z. B. ``Di, 06.10. · 3. Std. · 09:50``."""
    length = max(1, int(length or 1))
    plabel = period_label(period) if length == 1 else f"{period + 1}.–{period + length}."
    label = f"{WEEKDAYS_SHORT[day.weekday()]}, {day.strftime('%d.%m.')} · {plabel} Std."
    time = period_time(settings, period)
    return f"{label} · {time}" if time else label


# =========================================================================== Aufgaben
SUBMISSION_LABELS = {
    "offen": "offen", "ueberfaellig": "Frist verpasst", "abgegeben": "abgegeben", "verspaetet": "verspätet abgegeben",
    "bewertet": "bewertet", "zurueckgegeben": "zur Überarbeitung zurückgegeben",
}


def submission_status(due_at: Optional[datetime], submitted_at: Optional[datetime], stored: Optional[str],
                      now: datetime) -> str:
    """Status einer Abgabe aus Sicht der Schülerin/des Schülers.

    Ohne Abgabe: ``offen`` bzw. ``ueberfaellig`` (Frist vorbei); sonst der gespeicherte Status
    (``abgegeben|verspaetet|bewertet|zurueckgegeben``).
    """
    if submitted_at is None or not stored:
        return "ueberfaellig" if due_at is not None and due_at < now else "offen"
    return stored


def submit_status(due_at: Optional[datetime], now: datetime) -> str:
    """Status beim (erneuten) Abgeben: ``abgegeben`` oder nach Fristende ``verspaetet``."""
    return "verspaetet" if due_at is not None and now > due_at else "abgegeben"


# =========================================================================== ZIP-Export
_ZIP_BAD = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')


def zip_safe_name(name: Optional[str], fallback: str = "Datei", max_length: int = 120) -> str:
    """Datei-/Ordnername für ZIP-Archive: keine Pfadtrenner, Steuer- oder Windows-Sonderzeichen, kein ``..``."""
    text = _ZIP_BAD.sub("_", clean_name(name, 400))
    text = text.strip(" .")
    if not text or set(text) <= {"_"}:
        text = fallback
    if len(text) > max_length:
        stem, dot, ext = text.rpartition(".")
        if dot and 1 <= len(ext) <= 10:
            text = stem[: max_length - len(ext) - 1].rstrip(" .") + "." + ext
        else:
            text = text[:max_length].rstrip(" .")
    return text or fallback


def unique_name(name: str, taken: set[str]) -> str:
    """``name`` oder ``name (2).ext`` usw., falls schon vergeben (Vergleich ohne Groß-/Kleinschreibung)."""
    if name.lower() not in taken:
        taken.add(name.lower())
        return name
    stem, dot, ext = name.rpartition(".")
    if not dot or not 1 <= len(ext) <= 10:
        stem, ext = name, ""
    n = 2
    while True:
        candidate = f"{stem} ({n}).{ext}" if ext else f"{stem} ({n})"
        if candidate.lower() not in taken:
            taken.add(candidate.lower())
            return candidate
        n += 1
