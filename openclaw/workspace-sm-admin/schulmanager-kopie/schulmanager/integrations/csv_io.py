"""CSV-Import/-Export der Stammdaten (Excel-tauglich, deutsche Spaltennamen).

Export: Trennzeichen ``;``, UTF-8 **mit BOM** (Excel erkennt Umlaute), CRLF,
Listen in einer Zelle mit ``", "`` getrennt, Wahrheitswerte ``ja``/``nein``,
Stunden/Tage 1-basiert („Stunde 1“ = 1. Stunde, Tag ``Montag``).

Import: Trennzeichen ``;``/``,``/Tab und Kodierung (UTF-8 mit/ohne BOM,
Windows-1252) werden erkannt; Spaltennamen werden tolerant zugeordnet
(Groß-/Kleinschreibung, Umlaute, Satzzeichen egal) – inklusive typischer
Spalten aus **SchILD-NRW**, **ASV-BW/ASV-BY**, **Magellan** und **LUSD**.
Abweichende Spalten lassen sich über ``mapping`` zuordnen::

    import_csv(school, "students", text, {"Familienname": "last_name", "Rufname": "first_name"})
    import_csv(school, "students", text, {"preset": "asv"})       # Preset + eigene Ergänzungen

Der Import ändert die übergebene ``School`` (Upsert nach ID/Kürzel). **Leere
Zellen lassen vorhandene Werte unverändert.** Schüler ohne ID werden über
Name + Klasse wiedererkannt, sonst mit stabiler ID (Hash aus Name/Geburtsdatum)
angelegt. Eine Spalte Konfession/Bekenntnis/Religionsunterricht ordnet Schüler
dem passenden Teil einer Religions-Kopplung ihrer Klasse zu (ER/KR/Ethik bzw.
Praktische Philosophie, Werte und Normen …) → ``Student.courses`` = ``"kurs#teil"``.

Rückgabe von :func:`import_csv`: ``{"what", "rows", "created", "updated", "skipped",
"errors": [...], "warnings": [...], "columns": {Spalte: Feld}, "ignored_columns": [...],
"delimiter", "encoding"}``.

Jede Zeile wird **ganz oder gar nicht** übernommen: Fehler (auch aus ``validate``, z. B. der Server-Prüfung
``features_data.validate_item``) machen alle Änderungen der Zeile rückgängig. Listen-Zellen werden an
``,``/``;``/``|`` getrennt; Leerzeichen trennen nur, wenn die Zelle als Ganzes kein bekanntes Kürzel ist
(Kürzel mit Leerzeichen überstehen so den Rundlauf).
"""
from __future__ import annotations

import copy
import csv
import dataclasses
import hashlib
import io
import re
from typing import Any, Callable, Optional

from ..models import (Curriculum, CurriculumEntry, Lesson, Room, School, SchoolClass, Student, Subject,
                      Teacher, TimeRule)
from ._common import (DAY_NAMES, DAY_SHORT, decode_bytes, grade_from_name, norm_key, parse_bool, parse_int,
                      parse_week_list, split_name, week_ranges)

__all__ = ["export_csv", "import_csv", "describe", "WHATS", "PRESETS", "format_rules", "parse_rules",
           "format_windows", "parse_windows", "religion_category", "assign_religion"]

SEP = ";"
WHATS = ("teachers", "classes", "rooms", "subjects", "students", "lessons", "curricula")

# Export-Spalten: (Überschrift, Feld)
COLUMNS: dict[str, list[tuple[str, str]]] = {
    "teachers": [("Kürzel", "id"), ("Name", "name"), ("Fächer", "subjects"), ("Deputat", "max_hours"),
                 ("Max. Stunden pro Tag", "max_per_day"), ("Max. Vertretungen pro Woche", "max_subs_per_week"),
                 ("Standorte", "sites"), ("E-Mail", "email"), ("Sperrzeiten", "unavailable"),
                 ("Wünsche", "wishes"), ("Wunschklassen", "preferred_classes"), ("Zeitfenster", "time_windows")],
    "classes": [("Kürzel", "id"), ("Name", "name"), ("Jahrgang", "grade"), ("Schülerzahl", "students"),
                ("Klassenraum", "home_room"), ("Standort", "site"), ("Max. Stunden pro Tag", "max_periods_per_day"),
                ("Klassenleitung", "class_teacher"), ("Sperrzeiten", "unavailable"),
                ("Unterrichtstage", "school_days"), ("Jahrgang (Profil)", "profile")],
    "rooms": [("Kürzel", "id"), ("Name", "name"), ("Raumtyp", "type"), ("Standort", "site"),
              ("Kapazität", "capacity")],
    "subjects": [("Kürzel", "id"), ("Name", "name"), ("Raumtyp", "room_type"), ("Hauptfach", "core"),
                 ("Max. pro Tag", "max_per_day"), ("Farbe", "color")],
    "students": [("ID", "id"), ("Nachname", "last_name"), ("Vorname", "first_name"), ("Klasse", "class_id"),
                 ("Kurse", "courses")],
    "lessons": [("ID", "id"), ("Kurs", "course_id"), ("Bezeichnung", "label"), ("Klassen", "classes"),
                ("Fächer", "subjects"), ("Lehrkräfte", "teachers"), ("Tag", "day"), ("Stunde", "start"),
                ("Länge", "length"), ("Wochen", "weeks"), ("Räume", "rooms"), ("Fixiert", "locked"),
                ("Beginn", "begin"), ("Ende", "end")],
    "curricula": [("Stundentafel", "id"), ("Name", "name"), ("Jahrgänge", "grades"), ("Klassen", "classes"),
                  ("Fach", "subject"), ("Wochenstunden", "hours"), ("Doppelstunde", "double")],
}

# Zusätzliche Spaltennamen (normalisiert, siehe norm_key) je Feld
ALIASES: dict[str, dict[str, list[str]]] = {
    "teachers": {
        "id": ["kuerzel", "kurzzeichen", "lehrerkuerzel", "kurzname", "id", "lehrerid", "kuerzellehrer", "lkz"],
        "name": ["name", "anzeigename", "vollername"],
        "last_name": ["nachname", "familienname"],
        "first_name": ["vorname", "rufname", "vornamen"],
        "title": ["anrede"],
        "subjects": ["faecher", "fach", "lehrbefaehigung", "lehrbefaehigungen", "unterrichtsfaecher", "fakultas",
                     "fakultaeten", "lehramtsfaecher"],
        "max_hours": ["deputat", "pflichtstunden", "pflichtstundensoll", "sollstunden", "wochenstunden",
                      "stundendeputat", "soll", "unterrichtsverpflichtung", "regelstunden"],
        "max_per_day": ["maxstundenprotag", "maxprotag"],
        "max_subs_per_week": ["maxvertretungenprowoche", "vertretungenprowoche"],
        "sites": ["standorte", "standort"],
        "email": ["email", "mail", "emailadresse", "dienstlicheemail"],
        "unavailable": ["sperrzeiten", "nichtverfuegbar", "sperren"],
        "wishes": ["wuensche", "zeitwuensche", "moeglichstfrei"],
        "preferred_classes": ["wunschklassen", "bevorzugteklassen", "hauptklassen", "stammklassen"],
        "time_windows": ["zeitfenster", "arbeitszeiten", "arbeitszeit", "verfuegbarkeit", "unterrichtszeiten"],
    },
    "classes": {
        "id": ["kuerzel", "klasse", "id", "klassenkuerzel", "kurzbezeichnung", "klassenkurzbezeichnung"],
        "name": ["name", "bezeichnung", "langname", "klassenbezeichnung", "langbezeichnung"],
        "grade": ["jahrgang", "stufe", "jahrgangsstufe", "klassenstufe"],
        "students": ["schuelerzahl", "anzahlschueler", "schueler", "anzahl", "schuelerinnen"],
        "home_room": ["klassenraum", "raum", "stammraum"],
        "site": ["standort", "gebaeude"],
        "max_periods_per_day": ["maxstundenprotag"],
        "class_teacher": ["klassenleitung", "klassenlehrer", "klassenlehrerin", "klassenlehrerkuerzel", "kl"],
        "unavailable": ["sperrzeiten", "rhythmus", "abwesenheiten"],
        "school_days": ["unterrichtstage", "schultage", "tage"],
        "profile": ["jahrgangprofil", "profil", "jahrgangsprofil", "bildungsgang"],
    },
    "rooms": {
        "id": ["kuerzel", "raum", "id", "raumnummer", "raumkuerzel", "nummer"],
        "name": ["name", "bezeichnung", "langname", "raumbezeichnung"],
        "type": ["raumtyp", "typ", "art", "raumart", "fachraum"],
        "site": ["standort", "gebaeude"],
        "capacity": ["kapazitaet", "plaetze", "sitzplaetze", "groesse"],
    },
    "subjects": {
        "id": ["kuerzel", "fach", "id", "fachkuerzel", "kurzbezeichnung", "fachkurzbezeichnung"],
        "name": ["name", "bezeichnung", "langname", "fachbezeichnung", "langbezeichnung"],
        "room_type": ["raumtyp", "fachraum", "fachraumtyp"],
        "core": ["hauptfach", "kernfach"],
        "max_per_day": ["maxprotag", "maxbloeckeprotag"],
        "color": ["farbe"],
    },
    "students": {
        "id": ["id", "schuelerid", "schuelernummer", "schuelernr", "internidnummer", "interneidnummer",
               "interneid", "idnummer", "lokaleid", "asvid", "schuelerkennung", "identnummer", "guid",
               "schuelerguid", "nr"],
        "name": ["name", "vollername", "anzeigename"],
        "last_name": ["nachname", "familienname", "zuname"],
        "first_name": ["vorname", "rufname", "vornamen"],
        "class_id": ["klasse", "klassenbezeichnung", "klassegruppe", "stammklasse", "klassenname",
                     "klassekuerzel", "klassenkuerzel", "lerngruppe"],
        "grade": ["jahrgang", "jahrgangsstufe", "stufe", "klassenstufe"],
        "birthdate": ["geburtsdatum", "gebdatum", "geboren", "geburtstag", "gebam"],
        "gender": ["geschlecht"],
        "courses": ["kurse", "kurswahlen", "kursteile"],
        "religion": ["konfession", "bekenntnis", "religion", "religionszugehoerigkeit", "religionsbekenntnis",
                     "glaubensrichtung", "glaubensbekenntnis"],
        "religion_class": ["religionsunterricht", "teilnahmereligionsunterricht", "reliunterricht",
                           "relunterricht", "religionethik", "religionsunterrichtethik", "ethikreligion",
                           "reliethik", "religionsunterrichtteilnahme", "teilnahmeamreligionsunterricht"],
        "religion_opt_out": ["religionsabmeldung", "abmeldungreligion", "abgemeldetvonreligion",
                             "reliabmeldung", "abmeldungreligionsunterricht"],
    },
    "lessons": {
        "id": ["id"], "course_id": ["kurs", "kursid"], "label": ["bezeichnung"], "classes": ["klassen"],
        "subjects": ["faecher"], "teachers": ["lehrkraefte", "lehrer"], "day": ["tag", "wochentag"],
        "start": ["stunde", "beginn"], "length": ["laenge", "dauer"], "weeks": ["wochen", "woche"],
        "rooms": ["raeume", "raum"], "locked": ["fixiert", "gesperrt"],
    },
    "curricula": {
        "id": ["stundentafel", "stundentafelid", "id"], "name": ["name", "bezeichnung"],
        "grades": ["jahrgaenge", "jahrgang"], "classes": ["klassen", "klasse"], "subject": ["fach"],
        "hours": ["wochenstunden", "stunden"], "double": ["doppelstunde", "doppelstunden"],
    },
}
_EXPORT_ONLY = {"lessons": {"label", "classes", "subjects", "teachers"}}

# Beschriftungen der Zielfelder, die nicht als Export-Spalte vorkommen (für Mapping-Dialoge)
_EXTRA_LABELS = {"last_name": "Nachname", "first_name": "Vorname", "title": "Anrede", "grade": "Jahrgang",
                 "birthdate": "Geburtsdatum", "gender": "Geschlecht (ignoriert)",
                 "religion": "Konfession/Bekenntnis", "religion_class": "Religionsunterricht (ER/KR/Ethik …)",
                 "religion_opt_out": "Abmeldung vom Religionsunterricht", "name": "Name (vollständig)"}

# Mapping-Presets: Original-Spaltenname → Feld (je Art). Ergänzen die automatische Erkennung.
PRESETS: dict[str, dict[str, dict[str, str]]] = {
    "schild-nrw": {
        "students": {"Interne ID-Nummer": "id", "Nachname": "last_name", "Vorname": "first_name",
                     "Klasse": "class_id", "Jahrgang": "grade", "Geburtsdatum": "birthdate",
                     "Geschlecht": "gender", "Konfession": "religion", "Religionsabmeldung": "religion_opt_out"},
        "teachers": {"Kürzel": "id", "Nachname": "last_name", "Vorname": "first_name",
                     "Lehrbefähigungen": "subjects", "Pflichtstundensoll": "max_hours", "E-Mail": "email"},
        "classes": {"Klasse": "id", "Klassenbezeichnung": "name", "Jahrgang": "grade",
                    "Klassenlehrer": "class_teacher"},
    },
    "asv": {   # ASV-BW und ASV-BY (Schülerexport)
        "students": {"Schüler-ID": "id", "Lokale ID": "id", "Familienname": "last_name", "Nachname": "last_name",
                     "Rufname": "first_name", "Vorname": "first_name", "Klasse": "class_id",
                     "Klasse/Gruppe": "class_id", "Jahrgangsstufe": "grade", "Geburtsdatum": "birthdate",
                     "Bekenntnis": "religion", "Konfession": "religion", "Religionsunterricht": "religion_class"},
        "teachers": {"Kürzel": "id", "Lehrerkürzel": "id", "Familienname": "last_name", "Rufname": "first_name",
                     "Unterrichtspflichtzeit": "max_hours"},
        "classes": {"Klasse": "id", "Klassenbezeichnung": "name", "Jahrgangsstufe": "grade",
                    "Klassenleitung": "class_teacher"},
    },
    "magellan": {
        "students": {"Name": "last_name", "Vorname": "first_name", "Klasse": "class_id", "Geb.-Datum": "birthdate",
                     "Geburtsdatum": "birthdate", "Konfession": "religion", "Religionsunterricht": "religion_class"},
        "teachers": {"Kürzel": "id", "Name": "last_name", "Vorname": "first_name"},
        "classes": {"Klasse": "id", "Jahrgangsstufe": "grade", "Klassenlehrer": "class_teacher"},
    },
    "lusd": {
        "students": {"Schüler-ID": "id", "Nachname": "last_name", "Vorname": "first_name", "Klasse": "class_id",
                     "Geburtsdatum": "birthdate", "Bekenntnis": "religion",
                     "Teilnahme Religionsunterricht": "religion_class"},
        "teachers": {"Kürzel": "id", "Nachname": "last_name", "Vorname": "first_name"},
        "classes": {"Klasse": "id", "Jahrgangsstufe": "grade", "Klassenleitung": "class_teacher"},
    },
}
PRESETS["schild"] = PRESETS["schild-nrw"]
PRESETS["asv-bw"] = PRESETS["asv"]
PRESETS["asv-by"] = PRESETS["asv"]


def describe(what: str) -> dict:
    """Zielfelder (mit Beschriftung und erkannten Spaltennamen) und Presets – für Mapping-Dialoge."""
    if what not in COLUMNS:
        raise ValueError(f"Unbekannte Art {what!r} (erlaubt: {', '.join(WHATS)})")
    labels = {f: h for h, f in COLUMNS[what]}
    fields = []
    for f in dict.fromkeys([f for _, f in COLUMNS[what]] + list(ALIASES[what])):
        if f in _EXPORT_ONLY.get(what, set()):
            continue
        fields.append({"field": f, "label": labels.get(f) or _EXTRA_LABELS.get(f, f),
                       "aliases": ALIASES[what].get(f, [])})
    presets = sorted(k for k, v in PRESETS.items() if what in v and k not in ("schild", "asv-bw", "asv-by"))
    return {"what": what, "fields": fields, "presets": presets,
            "columns": [h for h, f in COLUMNS[what]]}


# ===================================================================== Sperrzeiten
def _rhythm_text(rhythm: dict) -> str:
    """``{"every": 3, "from_week": 10, "to_week": 30}`` → ``"jede 3. Woche ab Woche 10 bis Woche 30"``."""
    k, a, e = int(rhythm.get("every") or 1), int(rhythm.get("from_week") or 1), int(rhythm.get("to_week") or 0)
    return f"jede {k}. Woche ab Woche {a}" + (f" bis Woche {e}" if e else "")


def format_week_spec(weeks: list, rhythm: Optional[dict]) -> str:
    """Wochenangabe für Tabellen: Rhythmus als Text, Wochenliste als ``"1-4,9"``, sonst leer (= jede Woche)."""
    if rhythm:
        return _rhythm_text(rhythm)
    return week_ranges(weeks) if weeks else ""


def parse_week_spec(text: str) -> tuple[list[int], Optional[dict]]:
    """Gegenstück zu :func:`format_week_spec`: ``"1-4,9"`` oder ``"jede 3. Woche ab Woche 10 [bis Woche 30]"``."""
    t = (text or "").strip()
    m = _RHYTHM_RE.match(t + ":")
    if m:
        return [], {"every": int(m.group("k")), "from_week": int(m.group("a")), "to_week": int(m.group("e") or 0)}
    return parse_week_list(t), None


_RHYTHM_RE = re.compile(r"^\s*jede\s+(?P<k>\d{1,2})\.\s*Woche\s+ab\s+Woche\s+(?P<a>\d{1,2})"
                        r"(?:\s+bis\s+Woche\s+(?P<e>\d{1,2}))?\s*:\s*(?P<rest>.*)$", re.IGNORECASE)


def _split_rhythm(chunk: str) -> tuple[Optional[dict], str]:
    m = _RHYTHM_RE.match(chunk)
    if not m:
        return None, chunk
    return ({"every": int(m.group("k")), "from_week": int(m.group("a")), "to_week": int(m.group("e") or 0)},
            m.group("rest"))


def format_rules(rules: list[TimeRule], settings=None) -> str:
    """TimeRules → ``"Woche 1: Mi (Praxistag) | Fr Std. 6-8 | Woche 1-4,9: Di"`` (Wochen und Stunden 1-basiert;
    Rhythmus als ``"jede 3. Woche ab Woche 10: Fr"``)."""
    del settings
    out = []
    for r in rules:
        s = ""
        if getattr(r, "rhythm", None):
            s += _rhythm_text(r.rhythm) + ": "
        elif r.weeks:
            s += "Woche " + week_ranges(r.weeks) + ": "
        s += ",".join(DAY_SHORT[d] for d in sorted(r.days) if 0 <= d < 7) if r.days else "täglich"
        if r.periods:
            s += " Std. " + _ranges([p + 1 for p in sorted(r.periods)])
        if r.note:
            s += f" ({r.note})"
        out.append(s)
    return " | ".join(out)


def _ranges(nums: list[int]) -> str:
    """``[1, 2, 3, 5]`` → ``"1-3,5"``."""
    spans: list[list[int]] = []
    for n in nums:
        if spans and n == spans[-1][1] + 1:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    return ",".join(f"{a}-{b}" if a != b else str(a) for a, b in spans)


_RULE_RE = re.compile(
    r"^\s*(?:Woche\s+(?P<weeks>[A-Za-z0-9]{1,2}(?:\s*-\s*\d{1,2})?(?:\s*,\s*[A-Za-z0-9]{1,2}(?:\s*-\s*\d{1,2})?)*)"
    r"\s*:\s*)?"
    r"(?P<days>[^()]*?)\s*(?:Std\.?\s*(?P<periods>[\d,\-\s]+?))?\s*(?:\((?P<note>.*)\))?\s*$")


def _day_index(token: str) -> Optional[int]:
    t = norm_key(token)
    if not t:
        return None
    if t.isdigit():
        return int(t) - 1 if 1 <= int(t) <= 7 else None
    for i, name in enumerate(DAY_NAMES):
        if len(t) >= 2 and norm_key(name).startswith(t):
            return i
    return None


def parse_rules(text: str) -> list[TimeRule]:
    """Gegenstück zu :func:`format_rules` (ValueError bei unlesbaren Angaben)."""
    rules = []
    for chunk in (text or "").split("|"):
        if not chunk.strip():
            continue
        rhythm, chunk = _split_rhythm(chunk)
        m = _RULE_RE.match(chunk)
        if not m:
            raise ValueError(f"Sperrzeit nicht lesbar: {chunk.strip()!r}")
        days: list[int] = []
        for tok in re.split(r"[,\s+/]+", m.group("days") or ""):
            if not tok or norm_key(tok) in {"taeglich", "alle", "jedentag"}:
                continue
            d = _day_index(tok)
            if d is None:
                raise ValueError(f"Wochentag nicht erkannt: {tok!r}")
            days.append(d)
        periods: list[int] = []
        for rng in re.split(r"[,\s]+", m.group("periods") or ""):
            if not rng:
                continue
            a, _, b = rng.partition("-")
            if not a.isdigit() or (b and not b.isdigit()):
                raise ValueError(f"Stunden nicht erkannt: {rng!r}")
            periods += list(range(int(a) - 1, int(b or a)))
        rules.append(TimeRule(weeks=[] if rhythm else parse_week_list(m.group("weeks") or ""),
                              days=sorted(set(days)), periods=sorted(set(periods)),
                              note=(m.group("note") or "").strip(), rhythm=rhythm))
    return rules


# ===================================================================== Zeitfenster (Lehrkräfte)
def _day_ranges(days: list[int]) -> str:
    """``[0, 1, 2, 3, 4]`` → ``"Mo-Fr"``, ``[0, 2, 4]`` → ``"Mo,Mi,Fr"`` (Läufe ab drei Tagen als Bereich)."""
    spans: list[list[int]] = []
    for d in sorted(set(days)):
        if spans and d == spans[-1][1] + 1:
            spans[-1][1] = d
        else:
            spans.append([d, d])
    out: list[str] = []
    for a, b in spans:
        if b - a >= 2:
            out.append(f"{DAY_SHORT[a]}-{DAY_SHORT[b]}")
        else:
            out += [DAY_SHORT[x] for x in range(a, b + 1)]
    return ",".join(out)


def format_windows(windows: list[dict], settings=None) -> str:
    """Arbeitszeitfenster → ``"Mo-Fr 10:00-18:30 | Woche 2: Mo,Mi 16:00-21:00"`` (leer = ganztägig verfügbar)."""
    del settings
    out = []
    for w in windows or []:
        days = [int(d) for d in w.get("days") or [] if 0 <= int(d) < 7]
        weeks = sorted({int(x) for x in w.get("weeks") or []})
        s = ""
        if w.get("rhythm"):
            s += _rhythm_text(w["rhythm"]) + ": "
        elif weeks:
            s += "Woche " + week_ranges(weeks) + ": "
        out.append(f"{s}{_day_ranges(days)} {w.get('start', '')}-{w.get('end', '')}")
    return " | ".join(out)


_WINDOW_RE = re.compile(
    r"^\s*(?:Woche\s+(?P<weeks>\d{1,2}(?:\s*-\s*\d{1,2})?(?:\s*[,/+]\s*\d{1,2}"
    r"(?:\s*-\s*\d{1,2})?)*)\s*:\s*)?(?P<days>.*?)\s*"
    r"(?P<start>\d{1,2}[:.]\d{2})\s*(?:Uhr\s*)?(?:-|–|—|bis)\s*(?P<end>\d{1,2}[:.]\d{2})\s*(?:Uhr)?\s*$",
    re.IGNORECASE)
_ALL_DAYS = {"taeglich", "alle", "jedentag", "montagbisfreitag"}
_NO_WINDOWS = {"ganztaegig", "ganztags", "keine", "ohne", "immer", "uneingeschraenkt"}


def _window_days(text: str, days_per_week: int) -> list[int]:
    days: list[int] = []
    for tok in re.split(r"[,\s+/]+", re.sub(r"\s*[-–—]\s*", "-", text or "")):
        if not tok:
            continue
        if norm_key(tok) in _ALL_DAYS:
            days += list(range(days_per_week))
            continue
        a, _, b = tok.replace("–", "-").replace("—", "-").partition("-")
        first = _day_index(a)
        last = _day_index(b) if b else first
        if first is None or last is None or last < first:
            raise ValueError(f"Wochentag nicht erkannt: {tok!r}")
        days += list(range(first, last + 1))
    return sorted(set(days))


def parse_windows(text: str, days_per_week: int = 5) -> list[dict]:
    """Gegenstück zu :func:`format_windows`; versteht auch „Mo–Fr 10:00–18:30; Woche 2: …“, Rhythmus „jede 3. Woche ab Woche 10: …“ und „ganztägig“
    (= keine Fenster). ValueError bei unlesbaren Angaben."""
    if norm_key(text) in _NO_WINDOWS:
        return []
    out = []
    for chunk in re.split(r"[|;]", text or ""):
        if not chunk.strip():
            continue
        rhythm, chunk = _split_rhythm(chunk)
        m = _WINDOW_RE.match(chunk)
        if not m:
            raise ValueError(f"Zeitfenster nicht lesbar: {chunk.strip()!r} (Beispiel: „Mo-Fr 10:00-18:30“)")
        days = _window_days(m.group("days"), days_per_week) if m.group("days").strip() else \
            list(range(days_per_week))
        item = {"days": days, "start": m.group("start").replace(".", ":"),
                "end": m.group("end").replace(".", ":"),
                "weeks": [] if rhythm else parse_week_list(m.group("weeks") or "")}
        if rhythm:
            item["rhythm"] = rhythm
        out.append(item)
    return out


# ===================================================================== Religion
_REL_STRICT = {
    "ev": {"er", "ev", "evr", "rev", "eva", "evrel", "reev", "evang", "evangelisch", "evreligion",
           "religionev", "evangelischereligion"},
    "kath": {"kr", "rk", "rkr", "ka", "kat", "kath", "katholisch", "roemischkatholisch", "rkath",
             "kathreligion", "katholischereligion", "religionkath"},
    "islam": {"ir", "isl", "islr", "iru", "islam", "islamisch", "islamischereligion", "is"},
    "orth": {"or", "orth", "orthodox"},
    "jued": {"jr", "jued", "juedisch", "jd"},
    "ethik": {"pp", "pl", "et", "eth", "ethik", "phil", "ler", "wn", "pphil", "philosophie",
              "praktischephilosophie", "werteundnormen", "ethikunterricht"},
}
_NONE_WORDS = ("ohne", "keine", "kein", "konfessionslos", "abgemeldet", "atheist", "sonstig", "andere",
               "religionsfrei", "freireligioes")


def religion_category(value: str) -> Optional[str]:
    """Konfession/Religionsunterricht → ``ev | kath | islam | orth | jued | ethik`` (``None`` = leer)."""
    k = norm_key(value)
    if not k:
        return None
    for cat, codes in _REL_STRICT.items():
        if k in codes:
            return cat
    if k in {"ob", "oh", "oeb", "ok", "so", "sonst", "x", "nein"}:
        return "ethik"
    if "evang" in k or "protest" in k or "luther" in k or "reformiert" in k or k.startswith("ev"):
        return "ev"
    if "kath" in k:
        return "kath"
    if "islam" in k or "alevit" in k or "muslim" in k:
        return "islam"
    if "orthodox" in k:
        return "orth"
    if "jued" in k:
        return "jued"
    if "ethik" in k or "philosoph" in k or "werte" in k or any(w in k for w in _NONE_WORDS):
        return "ethik"
    return "ethik"   # andere Bekenntnisse besuchen in der Regel Ethik/PP


def _part_category(part, subjects: dict[str, Subject]) -> Optional[str]:
    k = norm_key(part.subject)
    for cat, codes in _REL_STRICT.items():
        if k in codes and len(k) <= 5:
            return cat
    subj = subjects.get(part.subject)
    name = norm_key(subj.name) if subj else ""
    if "relig" in name:
        if "kath" in name:
            return "kath"
        if "ev" in name or "protest" in name:
            return "ev"
        if "islam" in name:
            return "islam"
        if "orthodox" in name:
            return "orth"
        if "jued" in name:
            return "jued"
    if any(w in name for w in ("ethik", "philosoph", "werteundnormen", "lebensgestaltung")):
        return "ethik"
    lab = norm_key(part.label)
    for cat, codes in _REL_STRICT.items():
        if lab in codes:
            return cat
    return None


def assign_religion(school: School, student: Student, value: str) -> Optional[str]:
    """Ordnet ``student`` dem passenden Teil der Religions-Kopplung seiner Klasse zu.

    Liefert die gesetzte Referenz ``"kurs#teil"`` oder ``None`` (keine passende Kopplung).
    """
    cat = religion_category(value)
    if cat is None:
        return None
    subjects = school.index("subjects")
    for c in school.courses:
        if student.class_id not in c.classes or len(c.parts) < 2:
            continue
        cats = [_part_category(p, subjects) for p in c.parts]
        if sum(1 for x in cats if x) < 2:
            continue
        target = cat if cat in cats else ("ethik" if "ethik" in cats else None)
        if target is None:
            continue
        idx = cats.index(target)
        ref = f"{c.id}#{idx}"
        student.courses = [r for r in student.courses if r.rpartition("#")[0] != c.id] + [ref]
        return ref
    return None


# ===================================================================== Export
def _has_field(cls, name: str) -> bool:
    return name in {f.name for f in dataclasses.fields(cls)}


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _export_rows(school: School, what: str) -> tuple[list[str], list[list[Any]]]:
    cols = COLUMNS[what]
    if what == "teachers":   # optionale Felder je nach Modellstand
        cols = [c for c in cols if c[1] not in ("email", "wishes", "preferred_classes", "time_windows")
                or _has_field(Teacher, c[1])]
    header = [h for h, _ in cols]
    st = school.settings
    rows: list[list[Any]] = []
    if what == "teachers":
        for t in school.teachers:
            values = {"id": t.id, "name": t.name, "subjects": t.subjects, "max_hours": t.max_hours,
                      "max_per_day": t.max_per_day, "max_subs_per_week": t.max_subs_per_week, "sites": t.sites,
                      "email": getattr(t, "email", ""), "unavailable": format_rules(t.unavailable, st),
                      "wishes": format_rules(getattr(t, "wishes", []), st),
                      "preferred_classes": getattr(t, "preferred_classes", []),
                      "time_windows": format_windows(getattr(t, "time_windows", []), st)}
            rows.append([values[f] for _, f in cols])
    elif what == "classes":
        for c in school.classes:
            rows.append([c.id, c.name, c.grade, c.students, c.home_room, c.site, c.max_periods_per_day,
                         c.class_teacher, format_rules(c.unavailable, st), _days_text(c.school_days),
                         getattr(c, "profile", None) or ""])
    elif what == "rooms":
        rows = [[r.id, r.name, r.type, r.site, r.capacity] for r in school.rooms]
    elif what == "subjects":
        rows = [[s.id, s.name, s.room_type, s.core, s.max_per_day, s.color] for s in school.subjects]
    elif what == "students":
        for s in school.students:
            first, last = split_name(s.name)
            rows.append([s.id, last, first, s.class_id, s.courses])
    elif what == "lessons":
        courses = school.index("courses")
        from ._common import period_bounds
        for les in sorted(school.lessons, key=lambda x: (x.day, x.start, x.course_id, x.id)):
            c = courses.get(les.course_id)
            parts = c.parts if c else []
            begin, _ = period_bounds(st, les.start)
            _, end = period_bounds(st, les.start + max(1, les.length) - 1)
            rows.append([les.id, les.course_id, c.label if c else "", c.classes if c else [],
                         "/".join(p.subject for p in parts), "/".join(p.teacher or "-" for p in parts),
                         DAY_NAMES[les.day] if 0 <= les.day < 7 else les.day + 1, les.start + 1, les.length,
                         format_week_spec(les.weeks, les.rhythm),
                         ", ".join(r or "-" for r in les.rooms), les.locked,
                         f"{begin // 60:02d}:{begin % 60:02d}", f"{end // 60:02d}:{end % 60:02d}"])
    elif what == "curricula":
        for cur in school.curricula:
            if not cur.entries:
                rows.append([cur.id, cur.name, cur.grades, cur.classes, "", "", ""])
            for e in cur.entries:
                rows.append([cur.id, cur.name, cur.grades, cur.classes, e.subject, e.hours, e.double])
    return header, rows


def export_csv(school: School, what: str) -> str:
    """CSV (``;``, CRLF) mit führender UTF-8-BOM (``"\\ufeff"``) – als UTF-8 speichern/ausliefern."""
    if what not in COLUMNS:
        raise ValueError(f"Unbekannte Art {what!r} (erlaubt: {', '.join(WHATS)})")
    header, rows = _export_rows(school, what)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=SEP, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerow(header)
    for r in rows:
        w.writerow([_cell(v) for v in r])
    return "﻿" + buf.getvalue()


# ===================================================================== Import
def _sniff(text: str) -> str:
    """Trennzeichen aus der Kopfzeile bestimmen (``;`` gewinnt bei Gleichstand)."""
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    counts = {d: len(next(csv.reader([first], delimiter=d), [])) for d in (";", ",", "\t", "|")}
    best = max(counts, key=lambda d: (counts[d], d == ";"))
    return best if counts[best] > 1 else ";"


def _codes(text: str, known: Optional[dict | set] = None) -> list[str]:
    """Kürzel-Liste aus einer Zelle. Mit ``known``: Teile mit Leerzeichen bleiben zusammen, wenn sie als Ganzes
    bekannt sind (oder keiner der Einzelteile bekannt ist) – sonst wird an Leerzeichen getrennt („M D E“)."""
    out: list[str] = []
    for tok in re.split(r"[,;|/+]+", text or ""):
        tok = tok.strip()
        if not tok:
            continue
        words = tok.split()
        if len(words) > 1 and known is not None and (tok in known or not any(w in known for w in words)):
            out.append(" ".join(words))
        else:
            out += words
    return out


def _items(text: str) -> list[str]:
    return [t.strip() for t in re.split(r"[,;|]", text or "") if t.strip()]


def _resolve_columns(what: str, header: list[str], mapping: Any, report: dict) -> dict[int, str]:
    valid = set(ALIASES[what]) | {f for _, f in COLUMNS[what]}
    explicit: dict[str, Optional[str]] = {}
    if isinstance(mapping, str):
        mapping = {"preset": mapping}
    if mapping:
        preset = mapping.get("preset")
        if preset:
            pdef = PRESETS.get(str(preset).lower())
            if pdef is None:
                report["errors"].append(f"Unbekanntes Preset {preset!r} (verfügbar: {', '.join(sorted(PRESETS))})")
            else:
                explicit.update({norm_key(k): v for k, v in pdef.get(what, {}).items()})
        for k, v in mapping.items():
            if k == "preset":
                continue
            if v and v not in valid:
                report["errors"].append(f"Mapping: unbekanntes Zielfeld {v!r} für Spalte {k!r}")
                continue
            explicit[norm_key(k)] = v or None
    auto: dict[str, str] = {}
    for h, f in COLUMNS[what]:
        auto.setdefault(norm_key(h), f)
    for f, names in ALIASES[what].items():
        for n in names:
            auto.setdefault(n, f)
    out: dict[int, str] = {}
    taken: set[str] = set()
    for i, h in enumerate(header):
        k = norm_key(h)
        if not k:
            continue
        f = explicit[k] if k in explicit else auto.get(k)
        if f is None or f in _EXPORT_ONLY.get(what, set()):
            if f is None:
                report["ignored_columns"].append(h)
            continue
        if f in taken:
            report["warnings"].append(f"Spalte {h!r}: Feld {f!r} ist bereits zugeordnet – ignoriert")
            continue
        taken.add(f)
        out[i] = f
        report["columns"][h] = f
    return out


class _Ctx:
    """Import-Zustand. Jede Zeile läuft als kleine Transaktion: ``touch`` merkt geänderte/neue Objekte,
    ``rollback`` stellt sie bei einem Fehler wieder her, ``commit`` übernimmt Zähler und Hinweise."""

    def __init__(self, school: School, report: dict, validate: Optional[Callable[[str, Any], list[str]]] = None):
        self.sc = school
        self.report = report
        self.validate = validate
        self.reset_curricula: set[str] = set()
        self.no_religion = 0
        self.idx_cache: dict[str, dict] = {}
        self._begin()

    def _begin(self) -> None:
        self.touched: list[tuple[str, Any, Optional[dict]]] = []
        self.pending = {"created": 0, "updated": 0, "no_religion": 0}
        self.row_warnings: list[str] = []
        self.row_resets: set[str] = set()

    def idx(self, name: str) -> dict:
        cache = self.idx_cache.get(name)
        if cache is None or len(cache) != len(getattr(self.sc, name)):
            cache = self.idx_cache[name] = self.sc.index(name)
        return cache

    def touch(self, kind: str, obj: Any, created: bool = False) -> None:
        if any(o is obj for _, o, _ in self.touched):
            return
        self.touched.append((kind, obj, None if created else copy.deepcopy(obj.__dict__)))

    def add(self, kind: str, obj: Any) -> None:
        cache = self.idx(kind)
        getattr(self.sc, kind).append(obj)
        cache[obj.id] = obj
        self.touch(kind, obj, created=True)

    def created(self) -> None:
        self.pending["created"] += 1

    def updated(self) -> None:
        self.pending["updated"] += 1

    def warn(self, msg: str) -> None:
        self.row_warnings.append(msg)

    def check(self) -> list[str]:
        """Prüft alle in dieser Zeile geänderten Objekte mit ``validate`` (Server-Regeln)."""
        if self.validate is None:
            return []
        errs: list[str] = []
        for kind, obj, _ in self.touched:
            errs += self.validate(kind, obj)
        return list(dict.fromkeys(errs))

    def commit(self) -> None:
        self.report["created"] += self.pending["created"]
        self.report["updated"] += self.pending["updated"]
        self.no_religion += self.pending["no_religion"]
        self.report["warnings"] += self.row_warnings
        self.reset_curricula |= self.row_resets
        self._begin()

    def rollback(self) -> None:
        for kind, obj, saved in reversed(self.touched):
            if saved is None:
                items = getattr(self.sc, kind)
                setattr(self.sc, kind, [x for x in items if x is not obj])
                self.idx_cache.pop(kind, None)
            else:
                obj.__dict__.clear()
                obj.__dict__.update(saved)
        self._begin()


def _int_field(rec: dict, key: str, line: int, minimum: int = 0) -> Optional[int]:
    raw = rec.get(key, "")
    if not raw:
        return None
    v = parse_int(raw)
    if v is None or v < minimum:
        raise ValueError(f"{key}: ungültige Zahl {raw!r}")
    return v


def _check_refs(ctx: _Ctx, line: int, kind: str, ids: list[str], label: str) -> None:
    if ctx.validate is not None:      # Server-Prüfung meldet unbekannte Verweise als Fehler
        return
    known = ctx.idx(kind)
    for x in ids:
        if x and x not in known:
            ctx.warn(f"Zeile {line}: {label} {x!r} unbekannt")


def _imp_teacher(ctx: _Ctx, rec: dict, line: int) -> None:
    tid = rec.get("id", "")
    if not tid:
        raise ValueError("Kürzel fehlt")
    windows = None
    if rec.get("time_windows") and _has_field(Teacher, "time_windows"):  # vor jeder Änderung prüfen
        from ..teacher_profile import ProfileError, normalize_windows
        try:
            windows = normalize_windows(parse_windows(rec["time_windows"], ctx.sc.settings.days), ctx.sc.settings)
        except ProfileError as exc:
            raise ValueError("; ".join(exc.errors)) from None
    name = rec.get("name", "")
    if not name and (rec.get("first_name") or rec.get("last_name")):
        name = " ".join(x for x in (rec.get("first_name"), rec.get("last_name")) if x)
        if not rec.get("first_name") and rec.get("title"):
            name = f"{rec['title']} {rec['last_name']}"
    idx = ctx.idx("teachers")
    t = idx.get(tid)
    if t is None:
        t = Teacher(tid, name or tid)
        ctx.add("teachers", t)
        ctx.created()
    else:
        ctx.touch("teachers", t)
        if name:
            t.name = name
        ctx.updated()
    if rec.get("subjects"):
        t.subjects = _codes(rec["subjects"], ctx.idx("subjects"))
        _check_refs(ctx, line, "subjects", t.subjects, "Fach")
    for key in ("max_hours", "max_per_day", "max_subs_per_week"):
        v = _int_field(rec, key, line)
        if v is not None:
            setattr(t, key, v)
    if rec.get("sites"):
        t.sites = _codes(rec["sites"], ctx.idx("sites"))
        _check_refs(ctx, line, "sites", t.sites, "Standort")
    if rec.get("email") and _has_field(Teacher, "email"):
        t.email = rec["email"]
    if rec.get("unavailable"):
        t.unavailable = parse_rules(rec["unavailable"])
    if rec.get("wishes") and _has_field(Teacher, "wishes"):
        t.wishes = parse_rules(rec["wishes"])
    if rec.get("preferred_classes") and _has_field(Teacher, "preferred_classes"):
        t.preferred_classes = list(dict.fromkeys(_codes(rec["preferred_classes"], ctx.idx("classes"))))
        _check_refs(ctx, line, "classes", t.preferred_classes, "Wunschklasse")
    if windows is not None:
        t.time_windows = windows
    if windows is not None or getattr(t, "time_windows", None):
        # Zeitfenster → harte Sperrzeiten (ersetzt „Zeitfenster …“-Regeln, andere Sperrzeiten bleiben)
        from ..teacher_profile import apply_windows
        apply_windows(t, ctx.sc.settings)


def _imp_class(ctx: _Ctx, rec: dict, line: int) -> None:
    cid = rec.get("id", "")
    if not cid:
        raise ValueError("Klassen-Kürzel fehlt")
    idx = ctx.idx("classes")
    c = idx.get(cid)
    grade = _int_field(rec, "grade", line)
    if c is None:
        if grade is None:
            grade = grade_from_name(cid) or grade_from_name(rec.get("name", ""))
        if grade is None:
            raise ValueError(f"Jahrgang für Klasse {cid!r} fehlt")
        c = SchoolClass(cid, rec.get("name") or cid, grade)
        ctx.add("classes", c)
        ctx.created()
    else:
        ctx.touch("classes", c)
        if rec.get("name"):
            c.name = rec["name"]
        if grade is not None:
            c.grade = grade
        ctx.updated()
    for key in ("students", "max_periods_per_day"):
        v = _int_field(rec, key, line)
        if v is not None:
            setattr(c, key, v)
    if rec.get("home_room"):
        c.home_room = rec["home_room"]
        _check_refs(ctx, line, "rooms", [c.home_room], "Raum")
    if rec.get("site"):
        c.site = rec["site"]
        _check_refs(ctx, line, "sites", [c.site], "Standort")
    if rec.get("class_teacher"):
        c.class_teacher = rec["class_teacher"]
        _check_refs(ctx, line, "teachers", [c.class_teacher], "Lehrkraft")
    if rec.get("profile"):
        c.profile = rec["profile"]
        _check_refs(ctx, line, "grade_profiles", [c.profile], "Jahrgang (Profil)")
    if rec.get("unavailable"):
        c.unavailable = parse_rules(rec["unavailable"])
    if rec.get("school_days"):
        days = _days_parse(rec["school_days"])
        if not days:
            raise ValueError(f"Unterrichtstage {rec['school_days']!r} nicht erkannt")
        c.school_days = days


def _days_text(days: list[int]) -> str:
    """Unterrichtstage → ``"Mo-Fr"`` / ``"Mo,Di,Sa"`` (leer = Schulvorgabe)."""
    return _day_ranges(days) if days else ""


def _days_parse(text: str) -> list[int]:
    return sorted(set(_window_days(text, 7)))


def _imp_room(ctx: _Ctx, rec: dict, line: int) -> None:
    rid = rec.get("id", "")
    if not rid:
        raise ValueError("Raum-Kürzel fehlt")
    idx = ctx.idx("rooms")
    r = idx.get(rid)
    if r is None:
        r = Room(rid, rec.get("name") or rid)
        ctx.add("rooms", r)
        ctx.created()
    else:
        ctx.touch("rooms", r)
        if rec.get("name"):
            r.name = rec["name"]
        ctx.updated()
    if rec.get("type"):
        r.type = rec["type"]
    if rec.get("site"):
        r.site = rec["site"]
        _check_refs(ctx, line, "sites", [r.site], "Standort")
    cap = _int_field(rec, "capacity", line)
    if cap is not None:
        r.capacity = cap


def _imp_subject(ctx: _Ctx, rec: dict, line: int) -> None:
    sid = rec.get("id", "")
    if not sid:
        raise ValueError("Fach-Kürzel fehlt")
    idx = ctx.idx("subjects")
    s = idx.get(sid)
    if s is None:
        s = Subject(sid, rec.get("name") or sid)
        ctx.add("subjects", s)
        ctx.created()
    else:
        ctx.touch("subjects", s)
        if rec.get("name"):
            s.name = rec["name"]
        ctx.updated()
    if rec.get("room_type"):
        s.room_type = None if norm_key(rec["room_type"]) in {"klassenraum", "keiner", "nein"} else rec["room_type"]
    if rec.get("core"):
        b = parse_bool(rec["core"])
        if b is None:
            raise ValueError(f"Hauptfach: ja/nein erwartet, nicht {rec['core']!r}")
        s.core = b
    v = _int_field(rec, "max_per_day", line, 1)
    if v is not None:
        s.max_per_day = v
    if rec.get("color"):
        col = rec["color"].strip()
        if not re.fullmatch(r"#?[0-9a-fA-F]{6}", col):
            raise ValueError(f"Farbe {col!r} ist kein #rrggbb-Wert")
        s.color = col if col.startswith("#") else f"#{col}"


def _student_id(rec: dict) -> str:
    raw = "|".join(norm_key(rec.get(k, "")) for k in ("last_name", "first_name", "name", "birthdate"))
    return "S-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8].upper()


def _imp_student(ctx: _Ctx, rec: dict, line: int) -> None:
    first, last, name = rec.get("first_name", ""), rec.get("last_name", ""), rec.get("name", "")
    if name and first and not last:      # „Name“ + „Vorname“ (Magellan u. a.) → Name = Nachname
        name = f"{first} {name}"
    elif not name:
        name = " ".join(x for x in (first, last) if x)
    cls = rec.get("class_id", "")
    if cls and cls not in ctx.idx("classes"):
        grade = _int_field(rec, "grade", line) or grade_from_name(cls)
        if grade is None:
            raise ValueError(f"Klasse {cls!r} unbekannt und Jahrgang nicht erkennbar")
        ctx.add("classes", SchoolClass(cls, cls, grade))
        ctx.warn(f"Zeile {line}: Klasse {cls!r} angelegt (Jahrgang {grade})")
    idx = ctx.idx("students")
    sid = rec.get("id", "")
    st = idx.get(sid) if sid else None
    if st is None and not sid:
        if not name:
            raise ValueError("Name und ID fehlen")
        same = [s for s in ctx.sc.students if s.name.lower() == name.lower()]
        if cls:
            same = [s for s in same if s.class_id == cls] or ([] if len(same) != 1 else same)
        st = same[0] if len(same) == 1 else None
        if st is None:
            sid = _student_id(rec)
            st = idx.get(sid)
    if st is None:
        if not cls:
            raise ValueError("Klasse fehlt")
        st = Student(sid, name or sid, cls)
        ctx.add("students", st)
        ctx.created()
    else:
        ctx.touch("students", st)
        if name:
            st.name = name
        if cls:
            st.class_id = cls
        ctx.updated()
    if rec.get("birthdate") and not st.birth_date:           # Geburtsdatum nur ergänzen, nie überschreiben
        from .fremd.text import parse_date
        iso = parse_date(rec["birthdate"])
        if iso:
            st.birth_date = iso
        else:
            ctx.warn(f"Zeile {line}: Geburtsdatum {rec['birthdate']!r} nicht lesbar")
    if rec.get("courses"):
        courses = ctx.idx("courses")
        st.courses = []
        for tok in (t.strip() for t in re.split(r"[,;]+", rec["courses"])):
            words = tok.split()
            # Kurs-IDs dürfen Leerzeichen enthalten („5a-Netz Tech#0“); sonst trennt ein Leerzeichen
            if len(words) > 1 and tok.rpartition("#")[0] in courses:
                st.courses.append(tok)
            else:
                st.courses += words
        for ref in st.courses:
            cid, _, part = ref.rpartition("#")
            if cid not in courses or not part.isdigit() or int(part) >= len(courses[cid].parts):
                ctx.warn(f"Zeile {line}: Kursteil {ref!r} unbekannt")
    rel = rec.get("religion_class") or ("ethik" if rec.get("religion_opt_out") else "") or rec.get("religion")
    if rel:
        if assign_religion(ctx.sc, st, rel) is None:
            ctx.pending["no_religion"] += 1


def _imp_lesson(ctx: _Ctx, rec: dict, line: int) -> None:
    sc = ctx.sc
    st = sc.settings
    courses = ctx.idx("courses")
    cid = rec.get("course_id", "")
    if cid not in courses:
        raise ValueError(f"Kurs {cid!r} unbekannt")
    course = courses[cid]
    day_raw = rec.get("day", "")
    day = _day_index(day_raw) if day_raw else None
    if day is None or not 0 <= day <= 6:
        raise ValueError(f"Tag {day_raw!r} ungültig")
    start = _int_field(rec, "start", line, 1)
    if start is None:
        raise ValueError("Stunde fehlt")
    start -= 1
    length = _int_field(rec, "length", line, 1) or 1
    if start + length > st.periods:
        raise ValueError(f"Stunde {start + 1} (+{length}) liegt außerhalb des Rasters ({st.periods} Stunden)")
    weeks, rhythm = parse_week_spec(rec.get("weeks", ""))
    from ..weeks import spec_errors
    errs = spec_errors(weeks, rhythm)
    if errs:
        raise ValueError(f"Woche {rec.get('weeks')!r}: {errs[0]}")
    rooms: list[Optional[str]] = [None if r in ("-", "") else r for r in _items(rec.get("rooms", ""))]
    rooms = (rooms + [None] * len(course.parts))[:len(course.parts)]
    _check_refs(ctx, line, "rooms", [r for r in rooms if r], "Raum")
    idx = ctx.idx("lessons")
    lid = rec.get("id", "")
    les = idx.get(lid) if lid else None
    if les is None:
        if not lid:
            n = len(sc.lessons) + 1
            while f"L{n}" in idx:
                n += 1
            lid = f"L{n}"
        les = Lesson(lid, cid, day, start, length, weeks, rooms, rhythm=rhythm)
        ctx.add("lessons", les)
        ctx.created()
    else:
        ctx.touch("lessons", les)
        les.course_id, les.day, les.start, les.length, les.weeks = cid, day, start, length, weeks
        les.rhythm = rhythm
        if rec.get("rooms"):
            les.rooms = rooms
        ctx.updated()
    if rec.get("locked"):
        les.locked = bool(parse_bool(rec["locked"]))


def _imp_curriculum(ctx: _Ctx, rec: dict, line: int) -> None:
    cid = rec.get("id", "")
    if not cid:
        raise ValueError("Stundentafel-ID fehlt")
    idx = ctx.idx("curricula")
    cur = idx.get(cid)
    if cur is None:
        cur = Curriculum(cid, rec.get("name") or cid)
        ctx.add("curricula", cur)
        ctx.row_resets.add(cid)
        ctx.created()
    else:
        ctx.touch("curricula", cur)
        if cid not in ctx.reset_curricula:
            cur.entries = []          # Einträge werden durch die Datei ersetzt
            ctx.row_resets.add(cid)
            ctx.updated()
    if rec.get("name"):
        cur.name = rec["name"]
    if rec.get("grades"):
        grades = [parse_int(g) for g in _codes(rec["grades"])]
        if any(g is None for g in grades):
            raise ValueError(f"Jahrgänge {rec['grades']!r} ungültig")
        cur.grades = [g for g in grades if g is not None]
    if rec.get("classes"):
        cur.classes = _codes(rec["classes"], ctx.idx("classes"))
        _check_refs(ctx, line, "classes", cur.classes, "Klasse")
    if rec.get("subject"):
        hours = _int_field(rec, "hours", line, 0)
        if hours is None:
            raise ValueError("Wochenstunden fehlen")
        if rec["subject"] not in ctx.idx("subjects") and ctx.validate is None:
            ctx.warn(f"Zeile {line}: Fach {rec['subject']!r} unbekannt")
        cur.entries.append(CurriculumEntry(rec["subject"], hours, bool(parse_bool(rec.get("double", "")))))


_HANDLERS: dict[str, Callable[[_Ctx, dict, int], None]] = {
    "teachers": _imp_teacher, "classes": _imp_class, "rooms": _imp_room, "subjects": _imp_subject,
    "students": _imp_student, "lessons": _imp_lesson, "curricula": _imp_curriculum,
}


def import_csv(school: School, what: str, text: str | bytes, mapping: dict | None = None,
               validate: Optional[Callable[[str, Any], list[str]]] = None) -> dict:
    """Importiert eine CSV-Datei in ``school`` (Upsert). Siehe Modul-Doku für Format und Report.

    ``validate(kind, obj) -> [Fehler]`` prüft jedes in einer Zeile angelegte/geänderte Objekt; bei Fehlern wird
    die Zeile nicht übernommen (Server: ``features_data.validate_item``)."""
    if what not in _HANDLERS:
        raise ValueError(f"Unbekannte Art {what!r} (erlaubt: {', '.join(WHATS)})")
    text, enc = decode_bytes(text) if isinstance(text, bytes) else (text.lstrip("﻿"), "str")
    report: dict[str, Any] = {"what": what, "rows": 0, "created": 0, "updated": 0, "skipped": 0,
                              "errors": [], "warnings": [], "columns": {}, "ignored_columns": [],
                              "delimiter": ";", "encoding": enc}
    if not text.strip():
        report["errors"].append("Datei ist leer")
        return report
    delim = _sniff(text)
    report["delimiter"] = delim
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    start = next((i for i, r in enumerate(rows) if any(c.strip() for c in r)), None)
    if start is None:
        report["errors"].append("Keine Kopfzeile gefunden")
        return report
    header = rows[start]
    colmap = _resolve_columns(what, header, mapping, report)
    if not colmap:
        report["errors"].append("Keine bekannte Spalte gefunden – bitte Spalten-Mapping angeben")
        return report
    ctx = _Ctx(school, report, validate)
    handler = _HANDLERS[what]
    for line, row in enumerate(rows[start + 1:], start=start + 2):
        if not any(c.strip() for c in row):
            continue
        report["rows"] += 1
        rec = {f: row[i].strip() for i, f in colmap.items() if i < len(row)}
        try:
            handler(ctx, rec, line)
            errs = ctx.check()
            if errs:
                raise ValueError("; ".join(errs))
        except ValueError as ex:
            ctx.rollback()
            report["skipped"] += 1
            report["errors"].append(f"Zeile {line}: {ex}")
        else:
            ctx.commit()
    if ctx.no_religion:
        report["warnings"].append(f"{ctx.no_religion} Schüler: keine passende Religions-/Ethik-Kopplung "
                                  "in der Klasse gefunden")
    return report
