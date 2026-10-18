"""Personenlisten als CSV (SchILD-NRW, ASV-BW/BY, LUSD, Magellan, IServ-artige Listen, eigene Exporte) → Bundle.

Nutzt die Spaltenerkennung und Presets von :mod:`schulmanager.integrations.csv_io` (Umlaute/Satzzeichen egal, ``;``/``,``/Tab,
UTF-8 mit/ohne BOM, Windows-1252). Dadurch laufen auch diese Listen durch Zuordnung, Trockenlauf, Idempotenz und Rückgängig.

Welche Datei Schüler/innen oder Lehrkräfte enthält, entscheidet der Dateiname (``lehrer``, ``lehrkr``, ``teacher``,
``kollegium``, ``personal`` → Lehrkräfte; sonst Schüler/innen). Fehlende Klasse bei Schüler/innen → Hinweis in
``class_hint`` bleibt leer (die Anwendung fragt nach der Standardklasse).
"""
from __future__ import annotations

import csv
import io
import re

from .. import csv_io
from .._common import decode_bytes, grade_from_name
from .model import Bundle, FPerson
from .text import clean, fold, parse_date

TEACHER_NAMES = re.compile(r"lehrer|lehrkr|teacher|kollegium|personal|staff", re.I)


def read_csv_persons(files: dict[str, bytes], *, instance: str = "standard", mapping=None, preset: str = "") -> Bundle:
    b = Bundle(system="csv", source=", ".join(sorted(files))[:200], instance=instance)
    seen_classes: dict[str, int] = {}
    for name, data in sorted(files.items()):
        if not name.lower().endswith((".csv", ".txt")):
            continue
        what = "teachers" if TEACHER_NAMES.search(name) else "students"
        text, enc = decode_bytes(data)
        if not text.strip():
            b.problem("format", name, "Datei ist leer")
            continue
        delim = csv_io._sniff(text)
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
        start = next((i for i, r in enumerate(rows) if any(c.strip() for c in r)), None)
        if start is None:
            b.problem("format", name, "Keine Kopfzeile gefunden")
            continue
        mp = dict(mapping or {})
        if preset:
            mp["preset"] = preset
        rep: dict = {"errors": [], "warnings": [], "columns": {}, "ignored_columns": []}
        cols = csv_io._resolve_columns(what, rows[start], mp or None, rep)
        for e in rep["errors"]:
            b.problem("format", name, e)
        if not cols:
            b.problem("format", name, "Keine bekannte Spalte – bitte Spalten zuordnen (Mapping)")
            continue
        b.info.setdefault("files", {})[name] = {"what": what, "encoding": enc, "delimiter": delim,
                                                "columns": rep["columns"], "ignored": rep["ignored_columns"]}
        for line, row in enumerate(rows[start + 1:], start=start + 2):
            if not any(c.strip() for c in row):
                continue
            rec = {f: clean(row[i]) for i, f in cols.items() if i < len(row)}
            first, last, full = rec.get("first_name", ""), rec.get("last_name", ""), rec.get("name", "")
            if full and first and not last:
                last = full
            elif full and not (first or last):
                first, _, last = full.rpartition(" ")
            if not (first or last):
                b.problem("zeile", f"{name}:{line}", "Name fehlt – Zeile übersprungen")
                continue
            cls = rec.get("class_id", "")
            ident = rec.get("id", "")
            key = f"{what[0]}:{ident}" if ident else f"{what[0]}:{fold(first + last)}:{parse_date(rec.get('birthdate', ''))}"
            if key in b.persons:
                b.problem("zeile", f"{name}:{line}", f"Doppelter Eintrag ({first} {last}) – übersprungen")
                continue
            p = FPerson(src_id=key[:120], first=first, last=last, role="teacher" if what == "teachers" else "student",
                        email=rec.get("email", "").lower(), ident=ident, birth=parse_date(rec.get("birthdate", "")),
                        class_hint=cls, extra={"line": line, "file": name})
            if rec.get("birthdate") and not p.birth:
                b.problem("zeile", f"{name}:{line}", f"Geburtsdatum {rec['birthdate']!r} nicht lesbar")
            b.persons[p.src_id] = p
            if cls and what == "students":
                seen_classes.setdefault(cls, int(rec.get("grade") or 0) if str(rec.get("grade", "")).isdigit() else 0)
    for c, g in seen_classes.items():
        grade = g or grade_from_name(c)
        if grade is not None:
            b.classes.append({"id": c, "name": c, "grade": grade})
    return b
