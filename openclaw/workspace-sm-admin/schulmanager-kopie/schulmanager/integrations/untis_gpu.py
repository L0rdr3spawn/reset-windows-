"""Untis-Datenaustausch über die GPU-/DIF-Textdateien.

Untis (Gruber & Petters) exportiert und importiert seine Daten als „DIF-Dateien“
``GPUxxx.TXT``: CSV ohne Kopfzeile, Feldtrenner Komma (in Untis einstellbar, der
Import erkennt auch ``;`` und Tab), Texte in doppelten Anführungszeichen, Zahlen
ohne, Datumswerte ``JJJJMMTT``, Zeilenende CRLF. Kodierung ist bei Untis
standardmäßig **Windows-1252 (ANSI)**; neuere Versionen können UTF-8 schreiben.
:func:`import_files` erkennt die Kodierung automatisch (BOM → UTF-8 → Windows-1252),
:func:`export_zip` schreibt Windows-1252 (``encoding="utf-8"`` möglich).

Untis zählt **Tage 1–6 (1 = Montag) und Stunden ab 1**, der Schulmanager intern
ab 0 – die Umrechnung passiert ausschließlich in diesem Modul.

Quellen der Spaltenbelegung: Untis-Handbuch „Allgemeine Schnittstellen / Export
… (GPU0xx.TXT)“ (untis.at/manual, aus der Build-Umgebung nicht erreichbar) und die
MIT-lizenzierte Bibliothek *enbrea.untis.gpu* (Stüber Systems), deren Feldindizes
und Beispielzeilen hier abgeglichen wurden. Feldnummern unten sind **1-basiert**
wie im Untis-Handbuch. Legende: ``[s]`` = sicher (Handbuch + Referenzimplementierung
+ Beispielzeilen), ``[u]`` = unsicher (aus dem Gedächtnis / plausibel) – **vor einem
Produktivimport mit der eigenen Untis-Version prüfen** (Testexport in Untis
erzeugen und Spalten vergleichen). Nicht genannte Felder bleiben leer.

GPU001 Stundenplan (9 Felder) – eine Zeile je Stunde × Kopplungszeile × Klasse
    1 Unterrichtsnummer [s] · 2 Klasse [s] · 3 Lehrer [s] · 4 Fach [s] · 5 Raum [s]
    · 6 Tag 1–6 [s] · 7 Stunde ab 1 [s] · 8 Stundenlänge (hh:mm/mm, leer) [u] · 9 leer [u]
    Doppelstunden = zwei Zeilen mit aufeinanderfolgenden Stunden. Keine Wochenangabe!

GPU002 Unterricht (47 Felder) – eine Zeile je Kopplungszeile × Klasse
    1 Unt-Nr [s] · 2 Wochenstunden [s] · 3 Wst. Klasse (nur 1. Zeile je Klasse) [s]
    · 4 Wst. Lehrer (nur 1. Zeile je Lehrer) [s] · 5 Klasse [s] · 6 Lehrer [s] · 7 Fach [s]
    · 8 Fachraum (``~``-getrennt) [s] · 12 Unterrichtsgruppe [s] · 13 Zeilentext 1 [u]
    · 15/16 Datum von/bis [s] · 18 Text [u] · 20 Stammraum(``~``) [s] · 21 Beschreibung [s]
    · 22/23 Vorder-/Hintergrundfarbe [s] · 24 Kennzeichen [s] · 28/29 Doppelstunden
    min/max [u] · 39 Zeilentext 2 [u]
    Kopplung = mehrere Zeilen mit derselben Unt-Nr; jede Kopplungszeile wird zu
    einem ``CoursePart``, die Klassen aller Zeilen zu ``Course.classes``.

GPU003 Klassen (33 Felder)
    1 Name [s] · 2 Langname [s] · 4 Raum (Stammraum) [s] · 15 Abteilung [s]
    · 20/21 Unterrichtsbeginn/-ende [s] · 23 Beschreibung [s] · 24/25 Farben [s] · 29 Alias [s]

GPU004 Lehrer (45 Felder)
    1 Name/Kürzel [s] · 2 Langname (Nachname) [s] · 15 Wochen-Soll (Deputat) [u]
    · 17 Abteilung [s] · 24 Beschreibung [s] · 25/26 Farben [s] · 29 Vorname [s]
    · 31 Geschlecht 1=w/2=m/3=d [s] · 33 E-Mail [s] · 36 Alias [s]

GPU005 Räume (18 Felder)
    1 Name [s] · 2 Langname [s] · 3 Ausweichraum [s] · 7 Gewicht [s] · 8 Kapazität [s]
    · 9 Abteilung (→ Standort) [s] · 13 Beschreibung (hier: Raumtyp) [s] · 14/15 Farben [s]

GPU006 Fächer (23 Felder)
    1 Name [s] · 2 Langname [s] · 4 Fachraum [s] · 13 Fachgruppe [s] · 16 Text [s]
    · 17 Beschreibung [s] · 18/19 Vorder-/Hintergrundfarbe (Win32-COLORREF) [s] · 21 Alias [s]

GPU010 Schüler (15 Felder)
    1 Kurzname [s] · 2 Langname (Nachname) [s] · 3 Text · 4 Beschreibung · 5/6 Statistik
    · 7 Kennzeichen · 8 Vorname [s] · 9 Schülernummer [s] · 10 Klasse [s] · 11 Geschlecht [s]
    · 13 Geburtsdatum JJJJMMTT [s] · 14 E-Mail [s] · 15 Fremdschlüssel [s]

GPU014 Vertretungen (22 Felder)
    1 Vertretungsnummer [s] · 2 Datum JJJJMMTT [s] · 3 Stunde ab 1 [s] · 4 Absenznummer [s]
    · 5 Unt-Nr [s] · 6 abwesender Lehrer [s] · 7 vertretender Lehrer [s] · 8 Fach [s]
    · 9 Statistik Fach · 10 Vertretungsfach [s] · 11 Statistik Vertretungsfach · 12 Raum(``~``) [s]
    · 13 Vertretungsraum(``~``) [s] · 14 Statistik-Kennzeichen · 15 Klassen(``~``) [s]
    · 16 Absenzgrund [s] · 17 Text zur Vertretung [s] · 18 Art (Bitfeld) [u: Bitzählung]
    · 19 Vertretungsklassen(``~``) [s] · 20 Vertretungsart (Buchstabe) [s]
    · 21 letzte Änderung JJJJMMTTHHMM [s] · 22 (Zählkennzeichen, leer) [u]
    Art-Bits (Bit n = Wert 2^n): 0 Entfall, 1 Betreuung, 2 Sondereinsatz, 3 Wegverlegung,
    4 Freisetzung, 5 Plus als Vertreter, 6 Teilvertretung, 7 Hinverlegung,
    16 Raumvertretung, 17 Pausenaufsichtsvertretung, 18 unterrichtsfrei, 20 nicht drucken,
    21 neu. Vertretungsart: T verlegt, F verlegt von, W Tausch, S Betreuung, A Sondereinsatz,
    C Entfall, L Freisetzung, P Teilvertretung, R Raumvertretung, B Pausenaufsichtsvertretung,
    ~ Lehrertausch, E Klausur, leer = Vertretung.

GPU015 Kurswahlen (14 Felder, zusätzlich – für Schüler-Kursteile)
    1 Schüler-Kurzname [s] · 2 Unt-Nr [s] · 3 Fach [s] · 4 Unterrichts-Alias [s] · 5 Klasse [s]
    · 6 Statistik [s] · 7 Schülernummer [s] · 10/11/13 Alternativkurse [s]

Wochen
------
DIF-Dateien kennen keine Wochenperiodizität. Der Export legt Blöcke, die nur in
ausgewählten Wochen oder im Rhythmus liegen, daher als **eigene Unterrichtsnummer** an
(Wochenstunden anteilig, z. B. 0.5; Text „… (Woche 1)“ bzw. „… (Woche 1, 3)“, laufende Wochen des Schuljahres).
Beim Import aus echten Untis-Daten wird ein Wochenmuster erkannt, wenn Text/Zeilentext „Woche 1“ … „Woche 53“ oder
eine Liste („Woche 1, 3“) enthält; Woche *i* eines Musters aus *n* Wochen wird zu „jede *n*. Woche ab Woche *i*“.
Fehlt die Angabe, gilt der Unterricht für alle Wochen (mit Warnung bei gebrochenen Wochenstunden).
Tage: Mo = 1 … So = 7 (Sa/So [u]).

Schulmanager-Metadaten
----------------------
Damit Export → Import verlustfrei ist (Kurs-IDs, Kursteil-Index, Wochen,
Doppelstunden, Raumtyp), schreibt der Export eine Kennung ``sm1;k=v;…`` in
GPU002 Feld 39 (Zeilentext 2) und GPU006 Feld 16 (Text). Untis ignoriert das
inhaltlich; mit ``include_meta=False`` entfällt sie. Fehlt sie beim Import, wird
heuristisch gearbeitet (Kurs-ID ``U<Unt-Nr>`` bzw. Abgleich mit vorhandenen
Kursen über Klassen + Fächer).
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from urllib.parse import quote, unquote

from ..models import (Absence, Course, CoursePart, Lesson, Override, Room, School, SchoolClass,
                      Site, Student, Subject, Teacher)
from ._common import (as_date, color_to_win32, decode_bytes, encode_lossy,
                      grade_from_name, parse_float, parse_int, plans_by_date, split_name,
                      win32_to_color)

__all__ = ["export_zip", "export_files", "import_files", "unit_numbers", "GPU_FILES",
           "ART_ENTFALL", "ART_BETREUUNG", "ART_WEGVERLEGUNG", "ART_FREISETZUNG",
           "ART_HINVERLEGUNG", "ART_RAUMVERTRETUNG", "ART_PAUSENAUFSICHT"]

GPU_FILES = {
    "GPU001": "Stundenplan", "GPU002": "Unterricht", "GPU003": "Klassen", "GPU004": "Lehrer",
    "GPU005": "Räume", "GPU006": "Fächer", "GPU010": "Schüler", "GPU014": "Vertretungen",
    "GPU015": "Kurswahlen",
}
FIELD_COUNT = {"GPU001": 9, "GPU002": 47, "GPU003": 33, "GPU004": 45, "GPU005": 18, "GPU006": 23,
               "GPU010": 15, "GPU014": 22, "GPU015": 14}

# GPU014 Feld 18 „Art“ (Bitfeld, Bit n = 2**n)
ART_ENTFALL = 1 << 0
ART_BETREUUNG = 1 << 1
ART_SONDEREINSATZ = 1 << 2
ART_WEGVERLEGUNG = 1 << 3
ART_FREISETZUNG = 1 << 4
ART_PLUS = 1 << 5
ART_TEILVERTRETUNG = 1 << 6
ART_HINVERLEGUNG = 1 << 7
ART_RAUMVERTRETUNG = 1 << 16
ART_PAUSENAUFSICHT = 1 << 17
ART_UNTERRICHTSFREI = 1 << 18

# DayPlan-Entry-Art → (Art-Bits, Vertretungsart)
_KIND_EXPORT: dict[str, tuple[int, str]] = {
    "vertretung": (0, ""),
    "betreuung": (ART_BETREUUNG, "S"),
    "mitbetreuung": (ART_BETREUUNG, "S"),
    "entfall": (ART_ENTFALL, "C"),
    "verlegung": (ART_HINVERLEGUNG, "T"),
    "raumaenderung": (ART_RAUMVERTRETUNG, "R"),
    "klasse_abwesend": (ART_FREISETZUNG, "L"),
    "aufsicht": (ART_PAUSENAUFSICHT, "B"),
    "klausur": (0, "E"),
}
_VART_IMPORT = {"T": "verlegung", "F": "verlegung_weg", "W": "vertretung", "S": "betreuung",
                "A": "vertretung", "C": "entfall", "L": "freisetzung", "P": "vertretung",
                "R": "raumaenderung", "B": "aufsicht", "~": "vertretung", "E": "klausur"}

# „Woche 1“ … „Woche 53“, Listen „Woche 1, 3“ / „Woche 1/3“ (Wochenmuster einer Untis-Datei)
_WEEK_RE = re.compile(r"\bWoche\s*(\d{1,2}(?:\s*[,/]\s*\d{1,2})*)\b", re.IGNORECASE)
_META_PREFIX = "sm1"


# ===================================================================== Format
def _q(value: Any) -> str:
    """Textfeld: in Anführungszeichen, leere Werte bleiben leer."""
    if value is None:
        return ""
    s = str(value).replace('"', "'").replace("\r", " ").replace("\n", " ")
    return f'"{s}"' if s else ""


def _n(value: Any) -> str:
    """Zahlfeld ohne Anführungszeichen (Dezimalpunkt)."""
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.5f}".rstrip("0").rstrip(".")
    return str(value)


def _line(key: str, values: dict[int, str]) -> str:
    """Zeile aus 0-basierten Feldindizes → formatiertem Wert."""
    cells = [""] * FIELD_COUNT[key]
    for i, v in values.items():
        cells[i] = v
    return ",".join(cells)


def _meta(**kw: Any) -> str:
    parts = [_META_PREFIX]
    for k, v in kw.items():
        if v is None or v == "" or v is False or (isinstance(v, (list, tuple)) and not v):
            continue
        if isinstance(v, (list, tuple)):
            v = ",".join(str(x) for x in v)
        elif v is True:
            v = 1
        parts.append(f"{k}={quote(str(v), safe='')}")
    return ";".join(parts)


def _parse_meta(text: str) -> dict[str, str]:
    t = (text or "").strip()
    if not t.lower().startswith(_META_PREFIX + ";") and t.lower() != _META_PREFIX:
        return {}
    out: dict[str, str] = {}
    for part in t.split(";")[1:]:
        k, _, v = part.partition("=")
        if k.strip():
            out[k.strip()] = unquote(v.strip())
    return out


def _int_list(text: str) -> list[int]:
    return [int(x) for x in re.split(r"[,\s]+", text or "") if x.strip().isdigit()]


def _extend_period_times(st: Any, pause_minutes: int = 5) -> bool:
    """Fehlende Unterrichtszeiten fortschreiben (GPU kennt keine Uhrzeiten, z. B. Abendstunden einer neuen
    Schule): jede weitere Stunde beginnt ``period_minutes`` + ``pause_minutes`` nach der vorigen.
    ``False``, wenn sich keine gültige Zeit ableiten lässt (dann bleibt die Warnung)."""
    times = [str(t) for t in st.period_times[:st.periods]]
    step = int(getattr(st, "period_minutes", 45) or 45) + pause_minutes
    while len(times) < st.periods:
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", times[-1] if times else "07:55")
        if not m:
            return False
        nxt = int(m.group(1)) * 60 + int(m.group(2)) + (step if times else 0)
        if nxt >= 24 * 60:
            return False
        times.append(f"{nxt // 60:02d}:{nxt % 60:02d}")
    st.period_times = times
    return True


def _split_tilde(text: str) -> list[str]:
    return [x.strip() for x in (text or "").split("~") if x.strip()]


def _split_person(name: str) -> tuple[str, str, str]:
    """``"Frau Dr. Anna Müller"`` → (Geschlecht ``"1"``, Vorname ``"Dr. Anna"``, Nachname ``"Müller"``)."""
    tokens = (name or "").split()
    gender = ""
    if tokens and tokens[0].rstrip(".").lower() in {"frau", "fr"}:
        gender, tokens = "1", tokens[1:]
    elif tokens and tokens[0].rstrip(".").lower() in {"herr", "hr"}:
        gender, tokens = "2", tokens[1:]
    first, last = split_name(" ".join(tokens))
    return gender, first, last


# ===================================================================== Export
@dataclass
class _Numbers:
    """Vergabe der Untis-Unterrichtsnummern (stabil für dieselbe Schule)."""
    unit: dict[tuple[str, tuple[int, ...]], int] = field(default_factory=dict)
    lesson: dict[str, int] = field(default_factory=dict)
    units_of_course: dict[str, list[tuple[int, tuple[int, ...]]]] = field(default_factory=dict)

    def course_nr(self, course_id: str) -> Optional[int]:
        units = self.units_of_course.get(course_id)
        return units[0][0] if units else None


def _active_weeks(weeks: list, rhythm: Optional[dict], course: Optional[Course] = None,
                  lesson: Optional[Lesson] = None) -> tuple[int, ...]:
    """Laufende Wochen 1 … 53, in denen die Wochenangabe (und ggf. Stunde ∩ Kurs) gilt; ``()`` = jede Woche."""
    from ..weeks import lesson_active_in
    if lesson is None:
        from ..models import spec_active
        out = tuple(w for w in range(1, 54) if spec_active(weeks, rhythm, w))
    else:
        out = tuple(w for w in range(1, 54) if lesson_active_in(lesson, course, w))
    return () if len(out) >= 53 else out


def _week_key(school: School, lesson: Lesson, course: Course) -> tuple[int, ...]:
    return _active_weeks(lesson.weeks, lesson.rhythm, course, lesson)


def _rhythm_text(rhythm: Optional[dict]) -> str:
    return "" if not rhythm else f"{rhythm.get('every')}:{rhythm.get('from_week')}:{rhythm.get('to_week') or 0}"


def _rhythm_parse(text: Optional[str]) -> Optional[dict]:
    m = re.fullmatch(r"(\d{1,2}):(\d{1,2}):(\d{1,2})", (text or "").strip())
    return {"every": int(m.group(1)), "from_week": int(m.group(2)), "to_week": int(m.group(3))} if m else None


def _pattern_spec(pattern, n: int) -> tuple[list[int], Optional[dict]]:
    """Wochenmuster einer Untis-Datei (0-basierte Position im Muster aus ``n`` Wochen, beginnend mit Schulwoche 1)
    → ``(weeks, rhythm)`` in laufenden Wochen."""
    from ..legacy import weeks_to_spec
    n = max(1, int(n))
    return weeks_to_spec(pattern, n, lambda L: (L - 1) % n)


def _numbering(school: School) -> _Numbers:
    nums = _Numbers()
    courses = school.index("courses")
    order = {c.id: i for i, c in enumerate(school.courses)}
    keys_by_course: dict[str, set[tuple[int, ...]]] = defaultdict(set)
    for les in school.lessons:
        c = courses.get(les.course_id)
        if c is not None:
            keys_by_course[c.id].add(_week_key(school, les, c))
    nxt = len(school.courses) + 1
    for i, c in enumerate(school.courses):
        keys = keys_by_course.get(c.id, set())
        units: list[tuple[int, tuple[int, ...]]] = []
        if () in keys or not keys:
            units.append((i + 1, ()))
        nums.units_of_course[c.id] = units
    for c in sorted(school.courses, key=lambda x: order[x.id]):
        for key in sorted(k for k in keys_by_course.get(c.id, set()) if k):
            nums.units_of_course[c.id].append((nxt, key))
            nxt += 1
    for cid, units in nums.units_of_course.items():
        for nr, key in units:
            nums.unit[(cid, key)] = nr
    for les in school.lessons:
        c = courses.get(les.course_id)
        if c is not None:
            nums.lesson[les.id] = nums.unit[(c.id, _week_key(school, les, c))]
    return nums


def unit_numbers(school: School) -> dict[str, int]:
    """Kurs-ID → (erste) Untis-Unterrichtsnummer, wie sie :func:`export_zip` vergibt."""
    nums = _numbering(school)
    return {cid: units[0][0] for cid, units in nums.units_of_course.items() if units}


def _gpu001(school: School, nums: _Numbers) -> list[str]:
    courses = school.index("courses")
    order = {c.id: i for i, c in enumerate(school.courses)}
    out: list[str] = []
    lessons = sorted((les for les in school.lessons if les.course_id in courses),
                     key=lambda x: (x.day, x.start, order[x.course_id], x.id))
    for les in lessons:
        c = courses[les.course_id]
        nr = nums.lesson[les.id]
        for k in range(max(1, les.length)):
            for pi, part in enumerate(c.parts):
                room = les.rooms[pi] if pi < len(les.rooms) else None
                for cls in c.classes or [""]:
                    out.append(_line("GPU001", {
                        0: _n(nr), 1: _q(cls), 2: _q(part.teacher), 3: _q(part.subject), 4: _q(room),
                        5: _n(les.day + 1), 6: _n(les.start + k + 1)}))
    return out


def _gpu002(school: School, nums: _Numbers, include_meta: bool) -> list[str]:
    from ..weeks import describe
    classes = school.index("classes")
    courses = school.index("courses")
    hours_of_unit: dict[int, float] = defaultdict(float)

    def share(key: tuple[int, ...]) -> float:
        return len([w for w in key if w <= 52]) / 52 if key else 1.0

    for les in school.lessons:
        c = courses.get(les.course_id)
        if c is None:
            continue
        hours_of_unit[nums.lesson[les.id]] += les.length * share(_week_key(school, les, c))
    out: list[str] = []
    for c in school.courses:
        course_weeks = list(_active_weeks(c.weeks, c.rhythm)) if (c.weeks or c.rhythm) else []
        for nr, key in nums.units_of_course.get(c.id, []):
            if nr in hours_of_unit:
                wst = round(hours_of_unit[nr], 5)
            else:  # (noch) nicht verplant → Soll aus dem Kurs
                wst = round(c.hours * share(tuple(course_weeks)), 5)
            week_txt = ""
            if key:
                week_txt = f" ({describe(key)})"
            text = (c.label or c.id) + week_txt
            dbl = c.hours // 2 if c.double else None
            seen_class: set[str] = set()
            seen_teacher: set[str] = set()
            for pi, part in enumerate(c.parts):
                meta = _meta(c=c.id, p=pi, h=c.hours, d=c.double, cw=course_weeks, cr=_rhythm_text(c.rhythm), lw=list(key),
                             o=c.origin if c.origin != "manual" else None) if include_meta else ""
                for cls in c.classes or [""]:
                    wk = wst if cls and cls not in seen_class else None
                    wl = wst if part.teacher and part.teacher not in seen_teacher else None
                    seen_class.add(cls)
                    if part.teacher:
                        seen_teacher.add(part.teacher)
                    home = classes[cls].home_room if cls in classes else None
                    out.append(_line("GPU002", {
                        0: _n(nr), 1: _n(float(wst)), 2: _n(None if wk is None else float(wk)),
                        3: _n(None if wl is None else float(wl)), 4: _q(cls), 5: _q(part.teacher),
                        6: _q(part.subject), 7: _q(part.room), 12: _q(part.label), 17: _q(text),
                        19: _q(home), 27: _n(dbl), 28: _n(dbl), 38: _q(meta)}))
    return out


def _gpu003(school: School) -> list[str]:
    return [_line("GPU003", {0: _q(c.id), 1: _q(c.name), 3: _q(c.home_room), 14: _q(c.site)})
            for c in school.classes]


def _gpu004(school: School) -> list[str]:
    out = []
    for t in school.teachers:
        gender, first, last = _split_person(t.name)
        out.append(_line("GPU004", {0: _q(t.id), 1: _q(last or t.id), 14: _n(t.max_hours),
                                    28: _q(first), 30: _q(gender), 32: _q(getattr(t, "email", ""))}))
    return out


def _gpu005(school: School) -> list[str]:
    return [_line("GPU005", {0: _q(r.id), 1: _q(r.name), 7: _n(r.capacity), 8: _q(r.site), 12: _q(r.type)})
            for r in school.rooms]


def _gpu006(school: School, include_meta: bool) -> list[str]:
    out = []
    for s in school.subjects:
        meta = _meta(rt=s.room_type, core=s.core, mpd=s.max_per_day) if include_meta else ""
        out.append(_line("GPU006", {0: _q(s.id), 1: _q(s.name), 15: _q(meta),
                                    18: _n(color_to_win32(s.color))}))
    return out


def _gpu010(school: School) -> list[str]:
    out = []
    for st in school.students:
        first, last = split_name(st.name)
        out.append(_line("GPU010", {0: _q(st.id), 1: _q(last), 7: _q(first), 8: _q(st.id),
                                    9: _q(st.class_id), 14: _q(st.id)}))
    return out


def _gpu015(school: School, nums: _Numbers) -> list[str]:
    courses = school.index("courses")
    out = []
    for st in school.students:
        for ref in st.courses:
            cid, _, idx = ref.rpartition("#")
            c = courses.get(cid)
            if c is None or not idx.isdigit() or int(idx) >= len(c.parts):
                continue
            nr = nums.course_nr(cid)
            if nr is None:
                continue
            pi = int(idx)
            part = c.parts[pi]
            alias = part.label
            if sum(1 for p in c.parts if (p.subject, p.label) == (part.subject, part.label)) > 1:
                alias = f"{part.label or part.subject}#{pi}"   # gleiche Fächer/Labels unterscheidbar machen
            out.append(_line("GPU015", {0: _q(st.id), 1: _n(nr), 2: _q(part.subject), 3: _q(alias),
                                        4: _q(st.class_id), 6: _q(st.id)}))
    return out


def _gpu014(school: School, plans: Any, nums: _Numbers, include_reasons: bool = False) -> list[str]:
    plans_d = plans_by_date(plans)
    lessons = school.index("lessons")
    stamp = datetime.now().strftime("%Y%m%d%H%M")
    out: list[str] = []
    n = 0

    def reason(teacher: str, iso: str) -> str:
        if not include_reasons:      # Datenschutz: Gründe von Lehrkräften standardmäßig nie exportieren
            return ""
        for a in school.absences:
            if a.kind == "teacher" and a.ref == teacher and a.date_from <= iso <= a.date_to:
                return a.reason
        return ""

    for iso in sorted(plans_d):
        datum = iso.replace("-", "")
        for e in plans_d[iso].get("entries") or []:
            kind = e.get("kind") or "vertretung"
            if kind not in _KIND_EXPORT:
                continue
            art, vart = _KIND_EXPORT[kind]
            les = lessons.get(e.get("lesson_id") or "")
            nr = nums.lesson.get(les.id, 0) if les else 0
            if not nr and e.get("course_id"):
                nr = nums.course_nr(e["course_id"]) or 0
            period = parse_int(e.get("period"), 0) or 0
            hour = period + 2 if kind == "aufsicht" else period + 1   # Aufsicht: „vor der Stunde“
            absent = e.get("teacher") or ""
            sub = e.get("substitute") or ""
            subject = e.get("subject") or ""
            room = e.get("room") or e.get("area") or ""
            new_room = e.get("new_room") or ""
            if kind == "entfall":
                sub_room, sub_subject = "", ""
            else:
                sub_room, sub_subject = new_room or room, subject
            classes = "~".join(e.get("classes") or [])
            n += 1
            out.append(_line("GPU014", {
                0: _n(n), 1: _q(datum), 2: _n(hour), 4: _n(nr), 5: _q(absent), 6: _q(sub), 7: _q(subject),
                9: _q(sub_subject), 11: _q(room), 12: _q(sub_room), 14: _q(classes),
                15: _q(reason(absent, iso) if absent and kind != "aufsicht" else ""),
                16: _q(e.get("note") or ""), 17: _n(art), 18: _q(classes), 19: _q(vart), 20: _n(stamp)}))
            moved = e.get("moved_from")
            if kind == "verlegung" and moved is not None and str(moved).strip().lstrip("-").isdigit():
                n += 1
                out.append(_line("GPU014", {
                    0: _n(n), 1: _q(datum), 2: _n(int(moved) + 1), 4: _n(nr), 5: _q(absent), 6: _q(sub),
                    7: _q(subject), 9: _q(subject), 11: _q(room), 14: _q(classes),
                    16: _q(f"verlegt in die {period + 1}. Stunde"), 17: _n(ART_WEGVERLEGUNG),
                    18: _q(classes), 19: _q("F"), 20: _n(stamp)}))
    return out


def export_files(school: School, plans: Any = None, *, encoding: str = "cp1252",
                 include_meta: bool = True, include_reasons: bool = False) -> dict[str, bytes]:
    """Alle GPU-Dateien als ``{"GPU001.TXT": bytes, ...}`` (CRLF, Standard Windows-1252).

    ``include_reasons=True`` schreibt Abwesenheitsgründe von Lehrkräften in GPU014 Feld 16
    (Standard: aus – GPU014 landet oft in Schüler-Apps; Gründe sind Gesundheitsdaten).
    """
    nums = _numbering(school)
    texts = {
        "GPU001": _gpu001(school, nums),
        "GPU002": _gpu002(school, nums, include_meta),
        "GPU003": _gpu003(school),
        "GPU004": _gpu004(school),
        "GPU005": _gpu005(school),
        "GPU006": _gpu006(school, include_meta),
        "GPU010": _gpu010(school),
        "GPU014": _gpu014(school, plans, nums, include_reasons),
        "GPU015": _gpu015(school, nums),
    }
    out: dict[str, bytes] = {}
    for key, lines in texts.items():
        text = "".join(line + "\r\n" for line in lines)
        out[f"{key}.TXT"] = encode_lossy(text, encoding)
    return out


def export_zip(school: School, plans: list[dict] | None = None, *, encoding: str = "cp1252",
               include_meta: bool = True, include_reasons: bool = False) -> bytes:
    """ZIP mit GPU001–006, GPU010, GPU014 (aus ``plans``: Liste/Dict von DayPlan-Dicts) und GPU015."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in export_files(school, plans, encoding=encoding, include_meta=include_meta,
                                       include_reasons=include_reasons).items():
            zf.writestr(name, data)
    return buf.getvalue()


# ===================================================================== Import
def _collect(files: dict[str, bytes], warnings: list[str]) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for name, data in (files or {}).items():
        base = re.split(r"[\\/]", str(name))[-1]
        if base.lower().endswith(".zip") or (isinstance(data, bytes) and data[:4] == b"PK\x03\x04"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    inner = {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}
            except zipfile.BadZipFile:
                warnings.append(f"{base}: kein gültiges ZIP-Archiv")
                continue
            out.update(_collect(inner, warnings))
            continue
        m = re.match(r"^(GPU\d{3})", base.upper())
        if not m:
            warnings.append(f"{base}: keine GPU-Datei – ignoriert")
            continue
        if m.group(1) not in GPU_FILES:
            warnings.append(f"{base}: {m.group(1)} wird nicht unterstützt – ignoriert")
            continue
        out[m.group(1)] = data if isinstance(data, bytes) else str(data).encode("utf-8")
    return out


def _detect_delimiter(text: str) -> str:
    for line in text.splitlines():
        if not line.strip():
            continue
        counts = {d: 0 for d in ",;\t"}
        quoted = False
        for ch in line:
            if ch == '"':
                quoted = not quoted
            elif not quoted and ch in counts:
                counts[ch] += 1
        best = max(counts, key=lambda d: counts[d])
        return best if counts[best] else ","
    return ","


def _rows(text: str) -> list[list[str]]:
    delim = _detect_delimiter(text)
    out = []
    for row in csv.reader(io.StringIO(text), delimiter=delim, quotechar='"'):
        cells = [c.strip() for c in row]
        if any(cells):
            out.append(cells)
    return out


def _c(row: list[str], i: int) -> str:
    return row[i].strip() if i < len(row) else ""


@dataclass
class _Line:
    teacher: str
    subject: str
    label: str = ""
    room: str = ""
    classes: list[str] = field(default_factory=list)


@dataclass
class _Unit:
    nr: str
    course_id: str = ""
    weeks: tuple[int, ...] = ()          # laufende Wochen (1-basiert)
    rhythm: Optional[dict] = None        # Rhythmus in laufenden Wochen
    pattern: tuple[int, ...] = ()        # Wochenmuster der Untis-Datei (0-basiert), noch nicht umgerechnet
    lines: list[_Line] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    wst: float = 0.0
    text: str = ""
    meta: dict[str, str] = field(default_factory=dict)
    double: Optional[bool] = None

    @property
    def restricted(self) -> bool:
        return bool(self.pattern or self.weeks or self.rhythm)

    def part_index(self, teacher: str, subject: str) -> Optional[int]:
        for pred in (lambda ln: ln.teacher == teacher and ln.subject == subject,
                     lambda ln: ln.subject == subject and subject,
                     lambda ln: ln.teacher == teacher and teacher):
            for i, ln in enumerate(self.lines):
                if pred(ln):
                    return i
        return None


class _Importer:
    def __init__(self, school: Optional[School], warnings: list[str], lock: bool):
        self.new = school is None
        self.sc = school if school is not None else School()
        self.w = warnings
        self.lock = lock
        self.max_day = 0
        self.max_period = 0
        self.stats: dict[str, int] = defaultdict(int)
        self._ids: dict[str, set[str]] = {}
        self.missing: dict[str, list[str]] = defaultdict(list)

    # ------------------------------------------------------------ helpers
    def idx(self, name: str) -> dict[str, Any]:
        return self.sc.index(name)

    def has(self, name: str, key: str) -> bool:
        ids = self._ids.get(name)
        if ids is None or len(ids) != len(getattr(self.sc, name)):
            ids = self._ids[name] = {x.id for x in getattr(self.sc, name)}
        return key in ids

    def site(self, value: str) -> str:
        v = (value or "").strip()
        if not v:
            return ""
        for s in self.sc.sites:
            if v.lower() in (s.id.lower(), s.name.lower()):
                return s.id
        if self.new:
            self.sc.sites.append(Site(v, v))
            return v
        self.w.append(f"Abteilung/Standort „{v}“ unbekannt – ignoriert")
        return ""

    def ensure_subject(self, sid: str) -> None:
        if sid and not self.has("subjects", sid):
            self.sc.subjects.append(Subject(sid, sid))
            if not self.new or self.stats["gpu006"]:
                self.missing["Fächer"].append(sid)

    def ensure_teacher(self, tid: str) -> None:
        if tid and not self.has("teachers", tid):
            self.sc.teachers.append(Teacher(tid, tid))
            self.missing["Lehrkräfte"].append(tid)

    def ensure_room(self, rid: str, site: str = "") -> None:
        if rid and not self.has("rooms", rid):
            self.sc.rooms.append(Room(rid, rid, "Klassenraum", site))
            if self.stats["gpu005"] or not self.new:
                self.missing["Räume"].append(rid)

    def ensure_class(self, cid: str) -> None:
        if cid and not self.has("classes", cid):
            grade = grade_from_name(cid)
            self.sc.classes.append(SchoolClass(cid, cid, grade or 0))
            self.missing["Klassen"].append(cid)
            if not grade:
                self.missing["Klassen ohne erkennbaren Jahrgang (bitte nachtragen)"].append(cid)

    def finish(self) -> None:
        """Fehlende Stammdaten als je eine Sammelwarnung melden."""
        for what, ids in self.missing.items():
            shown = ", ".join(ids[:15]) + (f" … (+{len(ids) - 15})" if len(ids) > 15 else "")
            if what.startswith("Klassen ohne"):
                self.w.append(f"{what}: {shown}")
            else:
                self.w.append(f"{what} ohne Stammdaten angelegt ({len(ids)}): {shown}")

    # ------------------------------------------------------- master data
    def subjects(self, rows: list[list[str]]) -> None:
        self.stats["gpu006"] = len(rows)
        idx = self.idx("subjects")
        for r in rows:
            sid = _c(r, 0)
            if not sid:
                continue
            meta = _parse_meta(_c(r, 15))
            color = win32_to_color(_c(r, 18))
            s = idx.get(sid)
            if s is None:
                s = Subject(sid, _c(r, 1) or sid)
                self.sc.subjects.append(s)
                idx[sid] = s
            elif _c(r, 1):
                s.name = _c(r, 1)
            if color:
                s.color = color
            if meta:
                s.room_type = meta.get("rt") or None
                s.core = meta.get("core") == "1"
                s.max_per_day = parse_int(meta.get("mpd"), s.max_per_day) or 1

    def rooms(self, rows: list[list[str]]) -> None:
        self.stats["gpu005"] = len(rows)
        idx = self.idx("rooms")
        for r in rows:
            rid = _c(r, 0)
            if not rid:
                continue
            site = self.site(_c(r, 8))
            cap = parse_int(_c(r, 7))
            typ = _c(r, 12)
            room = idx.get(rid)
            if room is None:
                room = Room(rid, _c(r, 1) or rid, typ or "Klassenraum", site, cap or 30)
                self.sc.rooms.append(room)
                idx[rid] = room
                continue
            if _c(r, 1):
                room.name = _c(r, 1)
            if typ:
                room.type = typ
            if site:
                room.site = site
            if cap:
                room.capacity = cap

    def teachers(self, rows: list[list[str]]) -> None:
        idx = self.idx("teachers")
        for r in rows:
            tid = _c(r, 0)
            if not tid:
                continue
            last, first, gender = _c(r, 1), _c(r, 28), _c(r, 30)
            if first:
                name = f"{first} {last}".strip()
            elif last:
                name = {"1": "Frau ", "2": "Herr "}.get(gender, "") + last
            else:
                name = tid
            hours = parse_float(_c(r, 14))
            t = idx.get(tid)
            if t is None:
                t = Teacher(tid, name)
                self.sc.teachers.append(t)
                idx[tid] = t
            elif last or first:
                t.name = name
            if hours and hours > 0:
                t.max_hours = int(round(hours))
            if _c(r, 32) and hasattr(t, "email"):
                t.email = _c(r, 32)

    def classes(self, rows: list[list[str]]) -> None:
        idx = self.idx("classes")
        for r in rows:
            cid = _c(r, 0)
            if not cid:
                continue
            site = self.site(_c(r, 14))
            room = _c(r, 3) or None
            if room:
                self.ensure_room(room, site)
            c = idx.get(cid)
            if c is None:
                grade = grade_from_name(cid) or grade_from_name(_c(r, 1))
                if grade is None:
                    self.w.append(f"Klasse {cid}: Jahrgang nicht erkennbar – bitte nachtragen")
                c = SchoolClass(cid, _c(r, 1) or cid, grade or 0, home_room=room, site=site)
                self.sc.classes.append(c)
                idx[cid] = c
                continue
            if _c(r, 1):
                c.name = _c(r, 1)
            if room:
                c.home_room = room
            if site:
                c.site = site

    # ----------------------------------------------------------- lessons
    def units_from_gpu002(self, rows: list[list[str]]) -> dict[str, _Unit]:
        grouped: dict[str, list[list[str]]] = {}
        for r in rows:
            nr = _c(r, 0)
            if not nr.isdigit():
                self.w.append(f"GPU002: Zeile ohne gültige Unterrichtsnummer übersprungen ({nr!r})")
                continue
            grouped.setdefault(nr, []).append(r)
        units: dict[str, _Unit] = {}
        for nr, urows in grouped.items():
            u = _Unit(nr)
            by_p: dict[int, _Line] = {}
            for r in urows:
                cls_list = _split_tilde(_c(r, 4))
                teacher, subject = _c(r, 5), _c(r, 6)
                room = (_split_tilde(_c(r, 7)) or [""])[0]
                label = _c(r, 12)
                meta = _parse_meta(_c(r, 38))
                if meta and not u.meta:
                    u.meta = meta
                u.wst = max(u.wst, parse_float(_c(r, 1), 0.0) or 0.0)
                u.text = u.text or _c(r, 17)
                dmax = parse_int(_c(r, 28))
                if dmax is not None:
                    u.double = (u.double or False) or dmax > 0
                if meta and "p" in meta and meta["p"].isdigit():
                    line = by_p.get(int(meta["p"]))
                    if line is None:
                        line = by_p[int(meta["p"])] = _Line(teacher, subject, label, room)
                else:
                    line = None
                    for ln in u.lines:
                        if (ln.teacher, ln.subject, ln.label) == (teacher, subject, label) \
                                and not set(cls_list) & set(ln.classes):
                            line = ln
                            break
                    if line is None:
                        line = _Line(teacher, subject, label, room)
                        u.lines.append(line)
                for cl in cls_list:
                    if cl not in line.classes:
                        line.classes.append(cl)
                    if cl not in u.classes:
                        u.classes.append(cl)
            if by_p:
                u.lines = [by_p[k] for k in sorted(by_p)]
            if u.meta:
                u.course_id = u.meta.get("c") or f"U{nr}"
                lw = _int_list(u.meta.get("lw", ""))
                n_old = parse_int(u.meta.get("cy"), 0) or 0
                if n_old:       # älteres Exportformat: 0-basierte Wochen eines Wochenmusters mit n_old Wochen
                    weeks, u.rhythm = _pattern_spec(lw, n_old)
                    u.weeks = tuple(weeks)
                else:
                    u.weeks = tuple(lw)
                    u.rhythm = _rhythm_parse(u.meta.get("lr"))
                u.double = u.meta.get("d") == "1"      # Kennung ist maßgeblich (fehlt = keine Doppelstunde)
            else:
                u.pattern = self._weeks_from_text(u.text, *(ln.label for ln in u.lines))
            units[nr] = u
        return units

    def _weeks_from_text(self, *texts: str) -> tuple[int, ...]:
        found: set[int] = set()
        for t in texts:
            for m in _WEEK_RE.finditer(t or ""):
                found.update(int(x) - 1 for x in re.split(r"\s*[,/]\s*", m.group(1)) if x.isdigit()
                             and 1 <= int(x) <= 53)
        return tuple(sorted(found))

    def units_from_gpu001(self, rows: list[list[str]], known: dict[str, _Unit]) -> None:
        """Ergänzt Unterrichte, die nur in GPU001 vorkommen (z. B. Import ohne GPU002)."""
        slots: dict[str, set[tuple[str, str]]] = defaultdict(set)
        added: set[str] = set()
        for r in rows:
            nr = _c(r, 0)
            if not nr.isdigit() or (nr in known and nr not in added):
                continue
            u = known.get(nr)
            if u is None:
                u = known[nr] = _Unit(nr)
                added.add(nr)
            teacher, subject, cls = _c(r, 2), _c(r, 3), _c(r, 1)
            line = next((ln for ln in u.lines if (ln.teacher, ln.subject) == (teacher, subject)), None)
            if line is None:
                line = _Line(teacher, subject)
                u.lines.append(line)
            if cls and cls not in line.classes:
                line.classes.append(cls)
            if cls and cls not in u.classes:
                u.classes.append(cls)
            slots[nr].add((_c(r, 5), _c(r, 6)))
        for nr, s in slots.items():
            known[nr].wst = float(len(s))

    def courses(self, units: dict[str, _Unit]) -> None:
        """Unterrichte → Kurse (Upsert).

        Mehrere Unterrichtsnummern eines Kurses werden zusammengeführt: mit Metadaten über
        die Kurs-ID, ohne über gleiche Klassen + Lehrer/Fächer (Wochen-Unterrichte „Woche 1“/„Woche 2“
        hängen sich an den wöchentlichen Unterricht). Externe Unterrichte werden – wenn
        möglich – vorhandenen Kursen mit gleichen Klassen und Fächern zugeordnet.
        """
        idx = self.idx("courses")
        # Wochenmuster der Datei (Länge = größte Wochennummer) auf laufende Wochen abbilden: Woche i → „jede n. Woche
        # ab Woche i“
        cyc_target = max([1] + [w + 1 for u in units.values() for w in u.pattern])
        for u in units.values():
            if u.pattern and not (u.weeks or u.rhythm):
                weeks, u.rhythm = _pattern_spec(u.pattern, cyc_target)
                u.weeks = tuple(weeks)
        signature: dict[tuple, list[Course]] = defaultdict(list)
        for c in self.sc.courses:
            signature[(frozenset(c.classes), tuple(sorted(p.subject for p in c.parts)))].append(c)
        used: set[str] = set()

        def assign_external(u: _Unit) -> str:
            sig = (frozenset(u.classes), tuple(sorted(ln.subject for ln in u.lines)))
            cands = [c for c in signature.get(sig, []) if c.id not in used]
            teachers = [ln.teacher for ln in u.lines]
            cands.sort(key=lambda c: -sum(1 for p, t in zip(c.parts, teachers) if p.teacher == t))
            if cands and f"U{u.nr}" not in idx:
                used.add(cands[0].id)
                return cands[0].id
            return f"U{u.nr}"

        def line_key(u: _Unit) -> tuple:
            return frozenset(u.classes), tuple((ln.teacher, ln.subject) for ln in u.lines)

        external = [u for u in units.values() if not u.course_id]
        by_key: dict[tuple, str] = {}
        for u in sorted(external, key=lambda x: (x.restricted, int(x.nr))):
            if u.restricted and line_key(u) in by_key:
                u.course_id = by_key[line_key(u)]
            else:
                u.course_id = assign_external(u)
                by_key.setdefault(line_key(u), u.course_id)
        by_course: dict[str, list[_Unit]] = {}
        for u in units.values():
            by_course.setdefault(u.course_id, []).append(u)
        for cid, ulist in by_course.items():
            main = next((u for u in ulist if not u.restricted), ulist[0])
            meta = main.meta or ulist[0].meta
            for u in ulist:
                for ln in u.lines:
                    self.ensure_subject(ln.subject)
                    self.ensure_teacher(ln.teacher)
                    if ln.room:
                        self.ensure_room(ln.room)
                for cl in u.classes:
                    self.ensure_class(cl)
            label = re.sub(r"\s*\([^()]*Woche[^()]*\)\s*$", "", main.text or "")
            if meta:
                hours = parse_int(meta.get("h"), None)
                if hours is None:
                    hours = int(round(sum(u.wst * self._factor(u, cyc_target) for u in ulist)))
                double = meta.get("d") == "1"
                if parse_int(meta.get("cy"), 0):      # älteres Exportformat
                    cweeks, crhythm = _pattern_spec(_int_list(meta.get("cw", "")), parse_int(meta.get("cy"), 1))
                else:
                    cweeks, crhythm = _int_list(meta.get("cw", "")), _rhythm_parse(meta.get("cr"))
                origin = meta.get("o") or "manual"
            else:
                weeks_union = sorted({w for u in ulist for w in u.pattern})
                total = sum(u.wst for u in ulist)
                if any(not u.pattern for u in ulist) or len(weeks_union) >= cyc_target:
                    cweeks, crhythm = [], None
                    if total and not float(total).is_integer():
                        self.w.append(f"Unterricht {main.nr}: {total:g} Wochenstunden (periodisch?) – "
                                      "ohne Wochenangabe als wöchentlich importiert")
                    hours = max(1, int(round(total or 1)))
                else:
                    cweeks, crhythm = _pattern_spec(weeks_union, cyc_target)
                    hours = max(1, int(round(total * cyc_target / len(weeks_union))))
                double = any(bool(u.double) for u in ulist)
                origin = "untis"
                label = label or f"{'/'.join(ln.subject for ln in main.lines)} {'+'.join(main.classes)}".strip()
            classes = []
            for u in ulist:
                for cl in u.classes:
                    if cl not in classes:
                        classes.append(cl)
            new_parts = [CoursePart(ln.subject, ln.teacher or None, ln.room or None, label=ln.label)
                         for ln in main.lines]
            course = idx.get(cid)
            if course is None:
                course = Course(cid, classes, new_parts, hours, double, label, cweeks, origin, rhythm=crhythm)
                self.sc.courses.append(course)
                idx[cid] = course
            else:
                for i, p in enumerate(new_parts):
                    if i < len(course.parts) and course.parts[i].subject == p.subject:
                        old = course.parts[i]
                        p.room_type, p.students = old.room_type, old.students
                        p.room = p.room or old.room
                        p.label = p.label or old.label
                course.classes, course.parts, course.hours = classes, new_parts, hours
                course.double = double if meta else (double or course.double)
                course.label = label or course.label
                if meta or cweeks or crhythm:
                    course.weeks, course.rhythm = cweeks, crhythm
                if meta:
                    course.origin = origin
            teachers = self.idx("teachers")
            for p in course.parts:
                t = teachers.get(p.teacher or "")
                if t is not None and p.subject not in t.subjects:
                    t.subjects.append(p.subject)

    @staticmethod
    def _factor(u: "_Unit", n: int) -> float:
        """Wochen je Muster: Faktor von Wochenstunden (Durchschnitt) auf Stunden in den aktiven Wochen."""
        if u.pattern:
            return n / len(u.pattern)
        if u.rhythm:
            return float(u.rhythm.get("every") or 1)
        if u.weeks:
            return 52 / max(1, len(u.weeks))
        return 1.0

    def timetable(self, rows: list[list[str]], units: dict[str, _Unit], replace: bool) -> None:
        st = self.sc.settings
        courses = self.idx("courses")
        slots: dict[tuple[str, int], dict[int, list[list[str]]]] = defaultdict(lambda: defaultdict(list))
        bad = 0
        for r in rows:
            nr = _c(r, 0)
            day, hour = parse_int(_c(r, 5)), parse_int(_c(r, 6))
            if not nr.isdigit() or not day or not hour or day < 1 or day > 7 or hour < 1:
                bad += 1
                continue
            slots[(nr, day)][hour].append(r)
            if _c(r, 4):
                self.ensure_room(_c(r, 4))
        if bad:
            self.w.append(f"GPU001: {bad} Zeile(n) ohne gültige Unt-Nr/Tag/Stunde übersprungen")
        unmatched: set[str] = set()
        new_lessons: list[Lesson] = []
        for (nr, day), hours in sorted(slots.items(), key=lambda kv: (kv[0][1], int(kv[0][0]))):
            u = units.get(nr)
            course = courses.get(u.course_id) if u else None
            if u is None or course is None:
                unmatched.add(nr)
                continue
            self.max_day = max(self.max_day, day)
            per_hour: list[tuple[int, tuple]] = []
            for hour in sorted(hours):
                rooms: list[Optional[str]] = [None] * len(course.parts)
                for r in hours[hour]:
                    pi = u.part_index(_c(r, 2), _c(r, 3))
                    if pi is None or pi >= len(rooms):
                        self.w.append(f"GPU001: Unt-Nr {nr} {_c(r, 3)}/{_c(r, 2)} passt zu keiner "
                                      "Kopplungszeile – Zeile ignoriert")
                        continue
                    if rooms[pi] is None and _c(r, 4):
                        rooms[pi] = _c(r, 4)
                per_hour.append((hour, tuple(rooms)))
            # Doppelstunden: markierter Kurs, unbekannt (fremdes Untis) oder „Doppelstunden bevorzugen“ ab 2 Std.
            prefer = bool(getattr(st, "prefer_doubles", False)) and course.hours >= 2
            max_len = 2 if (course.double or u.double is None or prefer) else 1
            block: list[tuple[int, tuple]] = []
            for hour, rooms in per_hour + [(-99, ())]:
                if block and (hour != block[-1][0] + 1 or rooms != block[0][1] or len(block) >= max_len):
                    start = block[0][0] - 1
                    self.max_period = max(self.max_period, start + len(block))
                    new_lessons.append(Lesson(
                        f"L{len(new_lessons) + 1}", course.id, day - 1, start, len(block),
                        list(u.weeks), list(block[0][1]), self.lock, u.rhythm))
                    if len(block) > 1 and u.double is None and course.origin == "untis":
                        course.double = True
                    block = []
                if hour > 0:
                    block.append((hour, rooms))
        if unmatched:
            self.w.append("GPU001: Unterrichtsnummern ohne Unterricht übersprungen: "
                          + ", ".join(sorted(unmatched, key=int)[:20]) + (" …" if len(unmatched) > 20 else ""))
        # Raster der Schule anpassen bzw. prüfen
        from ..calendar_utils import open_days
        if self.max_day > max(open_days(self.sc)) + 1:
            if self.new:
                st.days = self.max_day
                st.school_days = list(range(self.max_day))       # Z6c: Unterrichtstage mit übernehmen
            else:
                self.w.append(f"Stundenplan nutzt {self.max_day} Tage, eingestellt sind {st.days}")
        if self.max_period > st.periods:
            if self.new:
                st.periods = self.max_period
            else:
                self.w.append(f"Stundenplan nutzt {self.max_period} Stunden, eingestellt sind {st.periods}")
        if len(st.period_times) < st.periods and not (self.new and _extend_period_times(st)):
            self.w.append("Unterrichtszeiten (period_times) unvollständig – bitte in den Einstellungen ergänzen")
        if replace:
            self.sc.lessons = new_lessons
        else:
            touched = {les.course_id for les in new_lessons}
            keep = [les for les in self.sc.lessons if les.course_id not in touched]
            used = {les.id for les in keep}
            n = 0
            for les in new_lessons:
                n += 1
                while f"L{n}" in used:
                    n += 1
                les.id = f"L{n}"
            self.sc.lessons = keep + new_lessons
        self.stats["lessons"] = len(new_lessons)

    # ---------------------------------------------------------- students
    def students(self, rows: list[list[str]]) -> dict[str, str]:
        """Liefert Untis-Kurzname → Schüler-ID."""
        idx = self.idx("students")
        short_to_id: dict[str, str] = {}
        by_name_class = {(s.name.lower(), s.class_id): s for s in self.sc.students}
        touched_classes: set[str] = set()
        for r in rows:
            short, last, first = _c(r, 0), _c(r, 1), _c(r, 7)
            number, cls, foreign = _c(r, 8), _c(r, 9), _c(r, 14)
            name = f"{first} {last}".strip() or short
            if not (short or number or foreign):
                continue
            st = next((idx[k] for k in (foreign, number, short) if k and k in idx), None)
            if st is None:
                st = by_name_class.get((name.lower(), cls))
            if cls:
                self.ensure_class(cls)
                touched_classes.add(cls)
            if st is None:
                st = Student(foreign or number or short, name, cls)
                self.sc.students.append(st)
                idx[st.id] = st
            else:
                st.name = name
                if cls:
                    st.class_id = cls
            short_to_id[short or st.id] = st.id
        counts: dict[str, int] = defaultdict(int)
        for s in self.sc.students:
            counts[s.class_id] += 1
        for c in self.sc.classes:
            if c.id in touched_classes and counts[c.id]:
                c.students = counts[c.id]
        return short_to_id

    def choices(self, rows: list[list[str]], units: dict[str, _Unit], short_to_id: dict[str, str]) -> None:
        courses = self.idx("courses")
        students = self.idx("students")
        chosen: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
        missing = 0
        for r in rows:
            sid = short_to_id.get(_c(r, 0)) or (_c(r, 0) if _c(r, 0) in students else None) \
                or (_c(r, 6) if _c(r, 6) in students else None)
            u = units.get(_c(r, 1))
            course = courses.get(u.course_id) if u else courses.get(f"U{_c(r, 1)}")
            if sid is None or course is None:
                missing += 1
                continue
            subject, label = _c(r, 2), _c(r, 3)
            cands = [i for i, p in enumerate(course.parts) if p.subject == subject]
            if len(cands) > 1 and label:
                m = re.match(r"^(.*)#(\d+)$", label)
                if m and int(m.group(2)) in cands:
                    cands = [int(m.group(2))]
                else:
                    cands = [i for i in cands if course.parts[i].label == label] or cands
            if not cands:
                missing += 1
                continue
            chosen[sid][course.id].add(cands[0])
        for sid, per_course in chosen.items():
            st = students[sid]
            keep = [ref for ref in st.courses if ref.rpartition("#")[0] not in per_course]
            for cid, parts in per_course.items():
                if len(courses[cid].parts) > 1:
                    keep += [f"{cid}#{i}" for i in sorted(parts)]
            st.courses = keep
        if missing:
            self.w.append(f"GPU015: {missing} Kurswahl(en) ohne passenden Schüler/Unterricht übersprungen")

    # ----------------------------------------------------- substitutions
    def substitutions(self, rows: list[list[str]], units: dict[str, _Unit]) -> None:
        sc = self.sc
        courses = self.idx("courses")
        inverse = {nr: (cid, key) for (cid, key), nr in _numbering(sc).unit.items()}
        lessons_of: dict[str, list[Lesson]] = defaultdict(list)
        for les in sc.lessons:
            lessons_of[les.course_id].append(les)
        dates: set[str] = set()
        overrides: dict[str, Override] = {}
        teacher_abs: dict[tuple[str, str], set[int]] = defaultdict(set)
        class_abs: dict[tuple[str, str], set[int]] = defaultdict(set)
        reasons: dict[tuple[str, str], str] = {}
        skipped: dict[str, int] = defaultdict(int)
        for r in rows:
            try:
                day = as_date(_c(r, 1))
            except ValueError:
                skipped["ungültiges Datum"] += 1
                continue
            iso = day.isoformat()
            dates.add(iso)
            hour = parse_int(_c(r, 2))
            if not hour:
                skipped["ohne Stunde"] += 1
                continue
            period = hour - 1
            nr = _c(r, 4)
            absent, sub, subject = _c(r, 5), _c(r, 6), _c(r, 7)
            room = (_split_tilde(_c(r, 11)) or [""])[0]
            new_room = (_split_tilde(_c(r, 12)) or [""])[0]
            classes = _split_tilde(_c(r, 14))
            art = parse_int(_c(r, 17), 0) or 0
            vart = _c(r, 19).strip()
            kind = _VART_IMPORT.get(vart)
            if kind is None:
                if art & ART_ENTFALL:
                    kind = "entfall"
                elif art & ART_BETREUUNG:
                    kind = "betreuung"
                elif art & ART_WEGVERLEGUNG:
                    kind = "verlegung_weg"
                elif art & ART_HINVERLEGUNG:
                    kind = "verlegung"
                elif art & ART_FREISETZUNG:
                    kind = "freisetzung"
                elif art & ART_PAUSENAUFSICHT:
                    kind = "aufsicht"
                elif art & ART_RAUMVERTRETUNG:
                    kind = "raumaenderung"
                elif sub and sub != absent:
                    kind = "vertretung"
                elif new_room and new_room != room:
                    kind = "raumaenderung"
                elif absent and not sub:
                    kind = "entfall"
                else:
                    kind = "vertretung"
            if kind in ("aufsicht", "klausur"):
                skipped[{"aufsicht": "Pausenaufsicht", "klausur": "Klausur"}[kind]] += 1
                continue
            if kind == "freisetzung":
                for cl in classes:
                    class_abs[(cl, iso)].add(period)
                continue
            if kind in ("verlegung", "verlegung_weg"):
                skipped["Verlegung (nicht als Override abbildbar)"] += 1
                continue
            # Unterrichtsstunde finden
            cid, key = None, None
            if nr in units:
                cid, key = units[nr].course_id, units[nr].weeks
            elif nr.isdigit() and int(nr) in inverse:
                cid, key = inverse[int(nr)]
            elif f"U{nr}" in courses:
                cid = f"U{nr}"
            course = courses.get(cid or "")
            les = None
            if course is not None:
                from ..weeks import lesson_active_in, real_week
                week = real_week(sc, day)
                for cand in lessons_of.get(course.id, []):
                    if cand.day == day.weekday() \
                            and cand.start <= period < cand.start + cand.length \
                            and lesson_active_in(cand, course, week):
                        les = cand
                        break
            if les is None or course is None:
                skipped["ohne passende Unterrichtsstunde"] += 1
                continue
            part = next((i for i, p in enumerate(course.parts) if absent and p.teacher == absent), None)
            if part is None:
                part = next((i for i, p in enumerate(course.parts) if p.subject == subject), 0)
            note = _c(r, 16)
            oid = f"untis-{iso}-{les.id}-{period}-{part}"
            if kind == "entfall":
                overrides[oid] = Override(oid, iso, les.id, period, part, "cancel", note=note)
            elif kind == "raumaenderung":
                overrides[oid] = Override(oid, iso, les.id, period, part, "room", room=new_room or None, note=note)
            elif sub:
                overrides[oid] = Override(oid, iso, les.id, period, part, "substitute", teacher=sub,
                                          room=new_room if new_room and new_room != room else None, note=note)
            else:
                skipped["ohne vertretende Lehrkraft"] += 1
                continue
            if absent and absent != sub and kind in ("entfall", "vertretung", "betreuung"):
                teacher_abs[(absent, iso)].add(period)
                if _c(r, 15):
                    reasons[(absent, iso)] = _c(r, 15)
        # frühere Untis-Importe derselben Tage ersetzen
        sc.overrides = [o for o in sc.overrides if not (o.id.startswith("untis-") and o.date in dates)]
        sc.absences = [a for a in sc.absences
                       if not (a.id.startswith("untis-") and a.date_from in dates and a.date_to in dates)]
        sc.overrides += list(overrides.values())
        teachers = self.idx("teachers")
        for (tid, iso), periods in sorted(teacher_abs.items()):
            if tid not in teachers:
                self.ensure_teacher(tid)
            sc.absences.append(Absence(f"untis-L-{tid}-{iso}", "teacher", tid, iso, iso, sorted(periods),
                                       reasons.get((tid, iso), "Untis-Import")))
        for (cl, iso), periods in sorted(class_abs.items()):
            if cl in self.idx("classes"):
                sc.absences.append(Absence(f"untis-K-{cl}-{iso}", "class", cl, iso, iso, sorted(periods),
                                           "Untis-Import (Freisetzung)"))
        self.stats["overrides"] = len(overrides)
        for why, n in skipped.items():
            self.w.append(f"GPU014: {n} Zeile(n) übersprungen – {why}")


def import_files(files: dict[str, bytes], school: School | None = None, *, encoding: str | None = None,
                 lock: bool = False, replace_lessons: bool = True) -> tuple[School, list[str]]:
    """Importiert Untis-GPU-Dateien.

    ``files``: ``{Dateiname: Inhalt}`` – Namen wie ``GPU001.TXT`` (Groß-/Kleinschreibung
    und Pfade egal) oder ein ZIP-Archiv. ``school=None`` → neue Schule, sonst wird in
    die übergebene Schule **gemergt** (Upsert nach Kürzel/ID; die Schule wird verändert
    und zurückgegeben). Mit GPU001 wird der Stundenplan ersetzt (``replace_lessons=False``:
    nur Stunden der importierten Kurse). GPU014 wird zu Abwesenheiten + Overrides (IDs
    ``untis-…``). Rückgabe ``(school, warnings)``.
    """
    warnings: list[str] = []
    raw = _collect(files, warnings)
    if not raw:
        raise ValueError("Keine Untis-GPU-Dateien gefunden (erwartet z. B. GPU001.TXT, GPU002.TXT)")
    tables: dict[str, list[list[str]]] = {}
    for key, data in raw.items():
        text, _enc = decode_bytes(data, encoding)
        tables[key] = _rows(text)
    imp = _Importer(school, warnings, lock)
    imp.subjects(tables.get("GPU006", []))
    imp.rooms(tables.get("GPU005", []))
    imp.teachers(tables.get("GPU004", []))
    imp.classes(tables.get("GPU003", []))
    units: dict[str, _Unit] = {}
    if "GPU002" in tables:
        units = imp.units_from_gpu002(tables["GPU002"])
    if "GPU001" in tables:
        imp.units_from_gpu001(tables["GPU001"], units)
    if units:
        imp.courses(units)
    if "GPU001" in tables:
        imp.timetable(tables["GPU001"], units, replace_lessons)
    short_to_id: dict[str, str] = {}
    if "GPU010" in tables:
        short_to_id = imp.students(tables["GPU010"])
    if "GPU015" in tables:
        imp.choices(tables["GPU015"], units, short_to_id)
    if "GPU014" in tables:
        imp.substitutions(tables["GPU014"], units)
    imp.finish()
    return imp.sc, warnings
