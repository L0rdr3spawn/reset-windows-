"""CSV-Ausgabe der Halbjahres-/Zeugnisnoten für SchILD-NRW, ASV und LUSD (B-52, ``docs/NOTENBUCH.md`` §8).

Aufbau wie die übrigen Ausgaben in :mod:`schulmanager.integrations.csv_io`: Trennzeichen ``;``, UTF-8 mit BOM (Excel
erkennt Umlaute), CRLF, Datum ``TT.MM.JJJJ``. Die Spaltenköpfe folgen den Feldnamen der jeweiligen Importvorlagen
(Leistungsdaten); die Zuordnung der Spalten beim Import in der Zielsoftware ist einmalig zu prüfen. Kein Zeugnisdruck.

Eine Zeile = eine Endnote eines Faches einer Person::

    rows = [{"student_id": "S1", "last_name": "Muster", "first_name": "Mia", "birth_date": "2014-05-03",
             "class_id": "7a", "year": "2026/27", "term_no": 1, "subject_id": "M", "subject_name": "Mathematik",
             "course_id": "7a-M", "teacher": "Frau Beispiel", "grade": "2", "remark": ""}]
    text = export_grades(rows, "schild")
"""
from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any, Iterable

SEP = ";"
FORMATS = ("schild", "asv", "lusd")
FORMAT_LABELS = {"schild": "SchILD-NRW / SVWS (Leistungsdaten)", "asv": "ASV (BW/BY)",
                 "lusd": "LUSD (Hessen)"}

#: (Spaltenkopf, Feld) je Format
COLUMNS: dict[str, list[tuple[str, str]]] = {
    "schild": [("Interne ID-Nummer", "student_id"), ("Nachname", "last_name"), ("Vorname", "first_name"),
               ("Geburtsdatum", "birth_date"), ("Klasse", "class_id"), ("Schuljahr", "year"),
               ("Abschnitt", "term_no"), ("Fach", "subject_id"), ("Fachbezeichnung", "subject_name"),
               ("Kurs", "course_id"), ("Fachlehrer", "teacher"), ("Note", "grade"), ("Bemerkung", "remark")],
    "asv": [("Schülerkennung", "student_id"), ("Familienname", "last_name"), ("Rufname", "first_name"),
            ("Geburtsdatum", "birth_date"), ("Klasse", "class_id"), ("Schuljahr", "year"),
            ("Halbjahr", "term_no"), ("Fach", "subject_id"), ("Unterrichtsfach", "subject_name"),
            ("Kurs", "course_id"), ("Lehrkraft", "teacher"), ("Note", "grade")],
    "lusd": [("LUSD-ID", "student_id"), ("Nachname", "last_name"), ("Vorname", "first_name"),
             ("Geburtsdatum", "birth_date"), ("Klasse", "class_id"), ("Schuljahr", "year"),
             ("Halbjahr", "term_no"), ("Fach Kürzel", "subject_id"), ("Fach", "subject_name"),
             ("Lerngruppe", "course_id"), ("Lehrkraft", "teacher"), ("Note", "grade")],
}


def _de_date(value: Any) -> str:
    if not value:
        return ""
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return str(value)


def export_grades(rows: Iterable[dict[str, Any]], fmt: str = "schild") -> str:
    """CSV-Text (mit BOM) für das Format ``fmt``; unbekanntes Format → ``ValueError``."""
    if fmt not in COLUMNS:
        raise ValueError(f"Unbekanntes Format {fmt!r} (erlaubt: {', '.join(FORMATS)})")
    cols = COLUMNS[fmt]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=SEP, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow([h for h, _ in cols])
    for row in rows:
        out = []
        for _, key in cols:
            v = row.get(key, "")
            if key == "birth_date":
                v = _de_date(v)
            elif key == "grade" and isinstance(v, str):
                v = v.replace(".", ",")
            out.append(_safe("" if v is None else str(v)))
        w.writerow(out)
    return "﻿" + buf.getvalue()


def _safe(text: str) -> str:
    """Excel-Formelstart entschärfen (``=``, ``+``, ``-``, ``@``), außer bei Noten wie ``2+`` oder ``3-``."""
    if text[:1] in ("=", "@") or (text[:1] in ("+", "-") and not text[1:2].isdigit() and len(text) > 1):
        return "'" + text
    return text
