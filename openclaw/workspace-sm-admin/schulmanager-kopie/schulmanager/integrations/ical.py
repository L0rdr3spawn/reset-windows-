"""iCalendar-Export (RFC 5545) für Klassen, Lehrkräfte, Räume und Schüler.

* CRLF-Zeilenenden, Zeilenfaltung nach spätestens 75 Oktetten (UTF-8, ohne
  Zeichen zu zerteilen), Escaping von ``\\ ; , Zeilenumbruch`` in TEXT-Werten.
* Zeiten lokal mit ``TZID=Europe/Berlin`` + eingebetteter ``VTIMEZONE``.
* Stabile UIDs (Hash aus Ansicht, Kurs, Datum, Stunde, Kursteilen) – Kalender-Apps
  aktualisieren Termine beim erneuten Abruf statt sie zu duplizieren; geänderte
  Termine bekommen ``SEQUENCE:1``.
* Berücksichtigt Unterrichtstage (Mo–So je Klasse bzw. Schulöffnungstage), Ferien/Feiertage (``school.holidays``
  als ganztägige Termine), die laufende Woche (zentrale Aktiv-Logik ``weeks.lesson_active_in``), Unterrichtszeiten
  (``settings.period_times``, Stundendauer ``settings.period_minutes`` bzw. 45 min),
  Klausuren (``school.exams``) und Vertretungen aus ``plans`` (``{Datum: DayPlan-Dict}``):
  Entfall/Verlegung (alter Platz)/Klasse abwesend → ``STATUS:CANCELLED``,
  Vertretung/Betreuung/Raumänderung → geänderte ``SUMMARY``/``LOCATION``,
  Verlegung → neuer Termin. Lehrkräfte sehen zusätzlich übernommene Vertretungen
  und ihre Pausenaufsichten.
* Schüler-Ansicht: nur die gewählten Kursteile (``Student.courses`` = ``"kurs#teil"``),
  ohne Wahl alle Teile einer Kopplung.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from .. import weeks as wk
from ..calendar_utils import class_days, open_days
from ..models import Course, Lesson, School
from ._common import as_date, holiday_on, period_bounds, plans_by_date

__all__ = ["calendar", "fold_line", "escape_text", "KINDS"]

KINDS = ("class", "teacher", "room", "student")
TZID = "Europe/Berlin"
MAX_DAYS = 800

VTIMEZONE_BERLIN = [
    "BEGIN:VTIMEZONE", "TZID:Europe/Berlin", "X-LIC-LOCATION:Europe/Berlin",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200", "TZNAME:CEST",
    "DTSTART:19700329T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET",
    "DTSTART:19701025T030000", "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD",
    "END:VTIMEZONE",
]

_KIND_LABEL = {"vertretung": "Vertretung", "betreuung": "Betreuung", "mitbetreuung": "Mitbetreuung",
               "raumaenderung": "Raumänderung", "entfall": "Entfall", "klasse_abwesend": "Klasse abwesend",
               "verlegung": "Verlegt"}


# ===================================================================== Format
def escape_text(value: Any) -> str:
    """TEXT-Escaping nach RFC 5545 §3.3.11."""
    s = str(value if value is not None else "")
    s = s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return s.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def fold_line(line: str, limit: int = 75) -> str:
    """Faltet eine Inhaltszeile: max. ``limit`` Oktette je physischer Zeile (Fortsetzung mit Leerzeichen)."""
    out: list[str] = []
    cur, size = "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > limit:
            out.append(cur)
            cur, size = " " + ch, 1 + n
        else:
            cur += ch
            size += n
    out.append(cur)
    return "\r\n".join(out)


def _dt(day: date, minutes: int) -> str:
    return f"{day:%Y%m%d}T{minutes // 60:02d}{minutes % 60:02d}00"


def _uid(*parts: Any, domain: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return f"sm-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:24]}@{domain}"


# ===================================================================== Modell
@dataclass
class _Occ:
    """Ein Kursteil in einer Stunde an einem Tag (inkl. Änderungen)."""
    lesson: Lesson
    course: Course
    part: int
    period: int
    teacher: Optional[str]
    room: Optional[str]
    teacher_now: Optional[str] = None
    room_now: Optional[str] = None
    status: str = "normal"            # normal | cancelled | changed | moved_in
    change: str = ""                  # Entry-Art
    note: str = ""
    exam: str = ""
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.teacher_now = self.teacher
        self.room_now = self.room


@dataclass
class _Event:
    uid: str
    day: date
    start: int
    end: int
    summary: str
    location: str = ""
    description: str = ""
    status: str = "CONFIRMED"
    categories: str = "Unterricht"
    sequence: int = 0
    transparent: bool = False
    all_day_end: Optional[date] = None


# ===================================================================== Ansicht
class _View:
    def __init__(self, school: School, kind: str, ref: str):
        self.school, self.kind, self.ref = school, kind, ref
        self.class_id: Optional[str] = None
        self.parts_sel: dict[str, list[int]] = {}
        if kind == "student":
            st = school.index("students").get(ref)
            self.class_id = st.class_id if st else None
            self.parts_sel = _student_parts(school, ref)

    def base_parts(self, course: Course) -> list[int]:
        """Kursteile, die für die Ansicht grundsätzlich in Frage kommen."""
        if self.kind == "class":
            return list(range(len(course.parts))) if self.ref in course.classes else []
        if self.kind == "student":
            if self.class_id not in course.classes:
                return []
            return self.parts_sel.get(course.id, list(range(len(course.parts))))
        return list(range(len(course.parts)))

    def visible(self, o: _Occ) -> Optional[str]:
        """``None`` = nicht sichtbar, sonst Status für diese Ansicht."""
        if self.kind in ("class", "student"):
            return "cancelled" if o.status == "cancelled" else o.status
        attr_now, attr_orig = ("teacher_now", "teacher") if self.kind == "teacher" else ("room_now", "room")
        now, orig = getattr(o, attr_now) == self.ref, getattr(o, attr_orig) == self.ref
        if o.status == "cancelled":
            return "cancelled" if (now or orig) else None
        if now:
            return o.status
        if orig:   # Lehrkraft vertreten / Raum gewechselt → für diese Ansicht entfällt der Termin
            if self.kind == "teacher":
                o.note = (o.note + " – " if o.note else "") + f"übernimmt {o.teacher_now or '–'}"
            else:
                o.note = (o.note + " – " if o.note else "") + f"Raumänderung → {o.room_now or '–'}"
            return "cancelled"
        return None


def _student_parts(school: School, student_id: str) -> dict[str, list[int]]:
    try:
        from ..timetable import student_parts
        return student_parts(school, student_id)
    except ImportError:  # pragma: no cover - Fallback ohne timetable.py
        st = school.index("students").get(student_id)
        out: dict[str, list[int]] = defaultdict(list)
        for ref in (st.courses if st else []):
            cid, _, idx = ref.rpartition("#")
            if idx.isdigit():
                out[cid].append(int(idx))
        return dict(out)


def _apply_entry(o: _Occ, e: dict) -> None:
    k = e.get("kind") or ""
    note = e.get("note") or ""
    if k in ("entfall", "klasse_abwesend"):
        o.status, o.change = "cancelled", k
        o.note = note or _KIND_LABEL[k]
    elif k in ("vertretung", "betreuung", "mitbetreuung"):
        o.status, o.change, o.note = "changed", k, note
        if e.get("substitute"):
            o.teacher_now = e["substitute"]
        if e.get("new_room"):
            o.room_now = e["new_room"]
    elif k == "raumaenderung":
        o.status, o.change, o.note = "changed", k, note
        o.room_now = e.get("new_room") or o.room
    elif k and k not in ("verlegung", "aufsicht", "klausur"):
        o.status, o.change, o.note = "changed", k, note


# ===================================================================== Kalender
def calendar(school: School, kind: str, ref: str, date_from: date | str, date_to: date | str,
             plans: dict[str, dict] | None = None, *, name: Optional[str] = None,
             now: Optional[datetime] = None, uid_domain: str = "schulmanager",
             include_holidays: bool = True, include_duties: bool = True) -> str:
    """Erzeugt einen iCalendar-Text (``text/calendar; charset=utf-8``).

    ``kind`` ∈ ``class|teacher|room|student``, ``ref`` = ID/Kürzel. ``plans`` = Vertretungspläne
    als ``{ISO-Datum: DayPlan-Dict}`` (auch Liste möglich). ValueError bei unbekannter Ansicht/Referenz.
    """
    if kind not in KINDS:
        raise ValueError(f"Unbekannte Ansicht {kind!r} (erlaubt: {', '.join(KINDS)})")
    collection = {"class": "classes", "teacher": "teachers", "room": "rooms", "student": "students"}[kind]
    obj = school.index(collection).get(ref)
    if obj is None:
        raise ValueError(f"{ref!r} nicht gefunden ({collection})")
    d0, d1 = as_date(date_from), as_date(date_to)
    if d1 < d0:
        raise ValueError("date_to liegt vor date_from")
    if (d1 - d0).days > MAX_DAYS:
        raise ValueError(f"Zeitraum zu lang (max. {MAX_DAYS} Tage)")
    plans_d = plans_by_date(plans)
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    view = _View(school, kind, ref)
    events: list[_Event] = []
    courses = school.index("courses")
    lessons_idx = school.index("lessons")
    by_day: dict[int, list[Lesson]] = defaultdict(list)
    for les in school.lessons:
        by_day[les.day].append(les)
    exams_by_date: dict[str, list] = defaultdict(list)
    for ex in school.exams:
        exams_by_date[str(ex.date)[:10]].append(ex)

    if kind == "class":
        teaching = set(class_days(school, obj))
    elif kind == "student":
        teaching = set(class_days(school, school.index("classes").get(obj.class_id)))
    else:
        teaching = set(open_days(school))
    day = d0
    while day <= d1:
        iso = day.isoformat()
        plan = plans_d.get(iso) or {}
        if day.weekday() in teaching and not holiday_on(school, day) and not plan.get("holiday"):
            events += _day_events(school, view, day, plan, courses, lessons_idx, by_day[day.weekday()],
                                  exams_by_date.get(iso, []), uid_domain)
            if kind == "teacher" and include_duties:
                events += _duty_events(school, ref, day, plan, uid_domain)
        day += timedelta(days=1)

    if include_holidays:
        for h in school.holidays:
            try:
                hf, ht = as_date(h.date_from), as_date(h.date_to)
            except ValueError:
                continue
            if ht < d0 or hf > d1:
                continue
            events.append(_Event(_uid("holiday", h.id, h.date_from, h.date_to, domain=uid_domain), hf, 0, 0,
                                 h.name or "Ferien", categories="Ferien", transparent=True,
                                 all_day_end=ht + timedelta(days=1)))

    title = name or _title(school, kind, obj)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Schulmanager//Stundenplan//DE", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{escape_text(title)}", f"X-WR-TIMEZONE:{TZID}",
             "REFRESH-INTERVAL;VALUE=DURATION:PT1H", "X-PUBLISHED-TTL:PT1H", *VTIMEZONE_BERLIN]
    for ev in sorted(events, key=lambda e: (e.day, e.start, e.uid)):
        lines += _vevent(ev, stamp)
    lines.append("END:VCALENDAR")
    return "".join(fold_line(line) + "\r\n" for line in lines)


def _title(school: School, kind: str, obj: Any) -> str:
    label = {"class": f"Klasse {obj.name}", "teacher": f"Lehrkraft {obj.id}",
             "room": f"Raum {obj.name}", "student": f"{obj.name}"}[kind]
    return f"Stundenplan {label} – {school.settings.school_name}"


def _vevent(ev: _Event, stamp: str) -> list[str]:
    out = ["BEGIN:VEVENT", f"UID:{ev.uid}", f"DTSTAMP:{stamp}"]
    if ev.all_day_end is not None:
        out += [f"DTSTART;VALUE=DATE:{ev.day:%Y%m%d}", f"DTEND;VALUE=DATE:{ev.all_day_end:%Y%m%d}"]
    else:
        out += [f"DTSTART;TZID={TZID}:{_dt(ev.day, ev.start)}", f"DTEND;TZID={TZID}:{_dt(ev.day, ev.end)}"]
    out.append(f"SUMMARY:{escape_text(ev.summary)}")
    if ev.location:
        out.append(f"LOCATION:{escape_text(ev.location)}")
    if ev.description:
        out.append(f"DESCRIPTION:{escape_text(ev.description)}")
    out += [f"STATUS:{ev.status}", f"CATEGORIES:{escape_text(ev.categories)}",
            f"TRANSP:{'TRANSPARENT' if ev.transparent else 'OPAQUE'}", f"SEQUENCE:{ev.sequence}", "END:VEVENT"]
    return out


def _subject_name(school: School, sid: str) -> str:
    s = school.index("subjects").get(sid)
    return s.name if s else sid


def _day_events(school: School, view: _View, day: date, plan: dict, courses: dict, lessons_idx: dict,
                lessons: list[Lesson], exams: list, domain: str) -> list[_Event]:
    aidx = wk.ActiveIndex(school)
    entries = plan.get("entries") or []
    by_key: dict[tuple, dict] = {}
    moved: dict[tuple, dict] = {}
    for e in entries:
        if not e.get("lesson_id") or e.get("kind") in ("aufsicht", "klausur"):
            continue
        key = (e["lesson_id"], int(e.get("period", 0)), int(e.get("part", 0) or 0))
        by_key[key] = e
        mf = e.get("moved_from")
        if e.get("kind") == "verlegung" and mf is not None and str(mf).lstrip("-").isdigit():
            moved[(e["lesson_id"], int(mf), int(e.get("part", 0) or 0))] = e
    exam_at: dict[tuple[str, int], list] = defaultdict(list)
    for ex in exams:
        for p in range(ex.start, ex.start + max(1, ex.length)):
            exam_at[(ex.course_id, p)].append(ex)

    cells: dict[tuple[str, int], list[tuple[_Occ, str]]] = defaultdict(list)
    meta: dict[str, tuple[Lesson, Course]] = {}

    def add(o: _Occ, group: str) -> None:
        status = view.visible(o)
        if status is None:
            return
        for ex in exam_at.get((o.course.id, o.period), []):
            if ex.part is None or ex.part == o.part:
                o.exam = ex.title or "Klausur"
        cells[(group, o.period)].append((o, status))
        meta[group] = (o.lesson, o.course)

    for les in lessons:
        course = courses.get(les.course_id)
        if course is None or not aidx.in_week(les, course, day):
            continue
        parts = view.base_parts(course)
        if not parts:
            continue
        for p in range(les.start, les.start + max(1, les.length)):
            for i in parts:
                if i >= len(course.parts):
                    continue
                part = course.parts[i]
                o = _Occ(les, course, i, p, part.teacher, les.rooms[i] if i < len(les.rooms) else None)
                mv = moved.get((les.id, p, i))
                if mv is not None:
                    o.status, o.change = "cancelled", "verlegung"
                    o.note = f"verlegt in die {int(mv['period']) + 1}. Stunde"
                else:
                    e = by_key.get((les.id, p, i))
                    if e is not None and e.get("kind") != "verlegung":
                        _apply_entry(o, e)
                add(o, les.id)
    # Verlegte Stunden am neuen Platz
    for e in entries:
        if e.get("kind") != "verlegung" or not e.get("lesson_id"):
            continue
        les = lessons_idx.get(e["lesson_id"])
        course = courses.get(les.course_id) if les else None
        if les is None or course is None:
            continue
        i = int(e.get("part", 0) or 0)
        if i not in view.base_parts(course) or i >= len(course.parts):
            continue
        o = _Occ(les, course, i, int(e["period"]), course.parts[i].teacher,
                 e.get("room") or (les.rooms[i] if i < len(les.rooms) else None))
        o.status, o.change = "moved_in", "verlegung"
        o.teacher_now = e.get("substitute") or o.teacher
        o.room_now = e.get("new_room") or o.room
        mf = e.get("moved_from")
        o.note = e.get("note") or (f"verlegt aus der {int(mf) + 1}. Stunde" if str(mf).lstrip("-").isdigit() else "")
        add(o, f"{les.id}>in")

    events: list[_Event] = []
    groups: dict[str, list[int]] = defaultdict(list)
    for group, p in cells:
        groups[group].append(p)
    for group, periods in groups.items():
        les, course = meta[group]
        run: list[int] = []
        for p in sorted(periods) + [-99]:
            if run and (p != run[-1] + 1 or _signature(cells[(group, p)] if p >= 0 else [])
                        != _signature(cells[(group, run[0])])):
                events.append(_make_event(school, view, day, les, course, run,
                                          [cells[(group, q)] for q in run], group.endswith(">in"), domain))
                run = []
            if p >= 0:
                run.append(p)
    return events


def _signature(cell: list[tuple[_Occ, str]]) -> tuple:
    return tuple(sorted((o.part, status, o.teacher_now or "", o.room_now or "", o.note, o.change, o.exam)
                        for o, status in cell))


def _make_event(school: School, view: _View, day: date, les: Lesson, course: Course,
                run: list[int], cells: list[list[tuple[_Occ, str]]], moved_in: bool, domain: str) -> _Event:
    st = school.settings
    first = cells[0]
    occs = [o for o, _ in first]
    statuses = {s for _, s in first}
    cancelled = statuses == {"cancelled"}
    begin, _ = period_bounds(st, run[0])
    _, end = period_bounds(st, run[-1])
    subjects = list(dict.fromkeys(o.course.parts[o.part].subject for o in occs))
    classes = "/".join(course.classes)
    if len(subjects) == 1:
        what = _subject_name(school, subjects[0]) if view.kind in ("class", "student") else subjects[0]
    else:
        what = course.label or "/".join(subjects)
    if view.kind == "teacher":
        base = f"{what} {classes}".strip()
    elif view.kind == "room":
        teachers = "/".join(dict.fromkeys(o.teacher_now or "–" for o in occs))
        base = f"{what} {classes} ({teachers})".strip()
    else:
        base = what
    changes = [o.change for o in occs if o.change]
    if moved_in:
        prefix = "Verlegt"
    elif cancelled:
        first_change = changes[0] if changes else ""
        prefix = {"verlegung": "Verlegt", "klasse_abwesend": "Klasse abwesend", "vertretung": "Vertreten",
                  "betreuung": "Vertreten", "mitbetreuung": "Vertreten",
                  "raumaenderung": "Raumwechsel"}.get(first_change, "Entfall")
    elif changes:
        prefix = _KIND_LABEL.get(changes[0], "Änderung")
    else:
        prefix = ""
    exam = next((o.exam for o in occs if o.exam), "")
    summary = f"{prefix}: {base}" if prefix else base
    if exam:
        summary = f"Klausur ({exam}): {summary}"
    active = [o for o, s in first if s != "cancelled"] or occs
    rooms = list(dict.fromkeys(o.room_now for o in active if o.room_now))
    desc: list[str] = []
    for o in occs:
        part = o.course.parts[o.part]
        line = f"{_subject_name(school, part.subject)}"
        if part.label:
            line += f" ({part.label})"
        line += f": {o.teacher_now or '–'}"
        if o.teacher_now != o.teacher and o.teacher:
            line += f" statt {o.teacher}"
        if o.room_now:
            line += f", Raum {o.room_now}"
        if o.room_now != o.room and o.room:
            line += f" statt {o.room}"
        desc.append(line)
    if course.classes:
        desc.append(f"Klassen: {', '.join(course.classes)}")
    desc.append(f"{run[0] + 1}." + (f"–{run[-1] + 1}." if len(run) > 1 else "") + f" Stunde, Woche {wk.real_week(school, day)}")
    notes = list(dict.fromkeys(o.note for o in occs if o.note))
    desc += notes
    if exam:
        desc.append(f"Klausur: {exam}")
    parts_key = ",".join(str(o.part) for o in sorted(occs, key=lambda x: x.part))
    uid = _uid(view.kind, view.ref, course.id, day.isoformat(), run[0], parts_key, "in" if moved_in else "",
               domain=domain)
    categories = "Klausur" if exam else ("Entfall" if cancelled else ("Vertretung" if changes else "Unterricht"))
    return _Event(uid, day, begin, end, summary, ", ".join(rooms), "\n".join(desc),
                  "CANCELLED" if cancelled else "CONFIRMED", categories,
                  1 if (changes or moved_in) else 0, cancelled)


def _duty_events(school: School, ref: str, day: date, plan: dict, domain: str) -> list[_Event]:
    st = school.settings
    areas = school.index("areas")
    replaced = {e.get("duty_id"): e for e in plan.get("entries") or [] if e.get("kind") == "aufsicht"}
    out: list[_Event] = []
    for d in school.duties:
        if not wk.duty_active_on(school, d, day) or not 0 <= d.break_index < len(st.breaks):
            continue
        rep = replaced.get(d.id)
        mine = d.teacher == ref
        takes_over = rep is not None and rep.get("substitute") == ref and not mine
        if not mine and not takes_over:
            continue
        brk = st.breaks[d.break_index]
        nxt, _ = period_bounds(st, int(brk.get("after", 0)) + 1)
        minutes = int(brk.get("minutes", 15) or 15)
        area = areas.get(d.area)
        where = area.name if area else d.area
        cancelled = mine and rep is not None and rep.get("substitute") != ref
        if cancelled:
            summary = f"Entfall: Pausenaufsicht {where}"
            desc = f"{brk.get('name', 'Pause')} – Aufsicht übernimmt {rep.get('substitute') or '–'}"
        elif takes_over:
            summary = f"Vertretung: Pausenaufsicht {where}"
            desc = f"{brk.get('name', 'Pause')} – statt {d.teacher or '–'}"
        else:
            summary = f"Pausenaufsicht {where}"
            desc = brk.get("name", "Pause")
        out.append(_Event(_uid("duty", ref, d.id, day.isoformat(), domain=domain), day, nxt - minutes, nxt,
                          summary, where, desc, "CANCELLED" if cancelled else "CONFIRMED", "Aufsicht",
                          1 if (cancelled or takes_over) else 0, cancelled))
    return out


def unfold(text: str) -> list[str]:
    """Hilfsfunktion (Tests/Debug): entfaltet einen iCalendar-Text zu logischen Zeilen."""
    return re.sub(r"\r\n[ \t]", "", text).split("\r\n")
