"""Kompetenzraster: reine Fachlogik ohne Datenbank und HTTP (Moodle-Lücke M5, ``docs/KOMPETENZEN.md``).

* Rahmen-Vorlagen (JSON/CSV) lesen, prüfen und ausgeben: :func:`normalize_template`, :func:`parse_json`,
  :func:`parse_csv`, :func:`to_csv`.
* Lernstand: :func:`latest`, :func:`needs_support`, :func:`progress`, :func:`week_start`.
* Abzeichen-Kriterien: :func:`validate_criteria`, :func:`criteria_met`.
* Eingebaute Beispielrahmen: :data:`TEMPLATES` (Grundschule Mathe/Deutsch, Montessori-Materialien).

Stufen sind 1…n (n = ``len(levels)``). „Nicht eingeschätzt“ ist kein Wert, sondern das Fehlen eines Eintrags.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date, timedelta
from typing import Any, Iterable, Mapping, Optional, Sequence

MIN_LEVELS = 2
MAX_LEVELS = 6
MAX_AREAS = 40
MAX_COMPETENCIES = 600
DEFAULT_LEVELS = ["Ich fange an", "Ich kann es mit Hilfe", "Ich kann es allein", "Ich kann es erklären"]

BADGE_ICONS = ("star", "medal", "trophy", "flag", "book", "calculator", "pencil", "puzzle", "bulb", "heart", "leaf",
               "rocket")
BADGE_COLORS = ("gold", "silver", "bronze", "blue", "green", "red", "purple")
PLAN_STATUS = ("offen", "in_arbeit", "erledigt")
EVIDENCE_TYPES = ("", "note", "link", "assignment", "material")


class TemplateError(ValueError):
    """Fehler in einer Rahmen-Vorlage (Text auf Deutsch, für die Oberfläche bestimmt)."""


# ------------------------------------------------------------------------------------------ Rahmen-Vorlagen
def _text(value: Any, limit: int, what: str, required: bool = False) -> str:
    s = "" if value is None else str(value).strip()
    if required and not s:
        raise TemplateError(f"{what} fehlt")
    if len(s) > limit:
        raise TemplateError(f"{what} ist zu lang (höchstens {limit} Zeichen)")
    return s


def check_levels(levels: Any) -> list[str]:
    """Beschriftungen der Niveaustufen prüfen (2 bis 6, jede nicht leer)."""
    if not isinstance(levels, (list, tuple)):
        raise TemplateError("Die Niveaustufen müssen eine Liste sein")
    out = [_text(x, 80, "Beschriftung der Stufe") for x in levels]
    if not (MIN_LEVELS <= len(out) <= MAX_LEVELS):
        raise TemplateError(f"Es braucht {MIN_LEVELS} bis {MAX_LEVELS} Niveaustufen")
    if any(not x for x in out):
        raise TemplateError("Jede Niveaustufe braucht eine Beschriftung")
    return out


def normalize_template(data: Any) -> dict:
    """Prüft eine Vorlage und gibt sie in fester Form zurück::

        {"name", "subject", "description", "levels": [...], "support_level": 1,
         "areas": [{"name", "competencies": [{"code", "title", "descriptors": [...]}]}]}

    Fehler → :class:`TemplateError`."""
    if not isinstance(data, Mapping):
        raise TemplateError("Die Vorlage muss ein Objekt mit Name, Stufen und Bereichen sein")
    levels = check_levels(data.get("levels") or DEFAULT_LEVELS)
    support = data.get("support_level", 1)
    if not isinstance(support, int) or isinstance(support, bool) or not (0 <= support < len(levels)):
        raise TemplateError("Die Stufe für „braucht Unterstützung“ liegt außerhalb der Niveaustufen")
    areas_in = data.get("areas")
    if not isinstance(areas_in, list) or not areas_in:
        raise TemplateError("Die Vorlage braucht mindestens einen Bereich")
    if len(areas_in) > MAX_AREAS:
        raise TemplateError(f"Höchstens {MAX_AREAS} Bereiche")
    areas: list[dict] = []
    total = 0
    for a in areas_in:
        if not isinstance(a, Mapping):
            raise TemplateError("Ein Bereich muss ein Objekt mit Name und Kompetenzen sein")
        name = _text(a.get("name"), 200, "Name des Bereichs", required=True)
        comps_in = a.get("competencies") or []
        if not isinstance(comps_in, list):
            raise TemplateError(f"Bereich „{name}“: die Kompetenzen müssen eine Liste sein")
        comps: list[dict] = []
        for c in comps_in:
            if isinstance(c, str):
                c = {"title": c}
            if not isinstance(c, Mapping):
                raise TemplateError(f"Bereich „{name}“: eine Kompetenz muss ein Text oder Objekt sein")
            desc_in = c.get("descriptors") or []
            if not isinstance(desc_in, list) or len(desc_in) > len(levels):
                raise TemplateError(f"Bereich „{name}“: höchstens ein Text je Niveaustufe")
            comps.append({"code": _text(c.get("code"), 20, "Kürzel der Kompetenz"),
                          "title": _text(c.get("title"), 300, "Text der Kompetenz", required=True),
                          "descriptors": [_text(d, 300, "Beschreibung der Stufe") for d in desc_in]})
        total += len(comps)
        areas.append({"name": name, "competencies": comps})
    if total > MAX_COMPETENCIES:
        raise TemplateError(f"Höchstens {MAX_COMPETENCIES} Kompetenzen je Rahmen")
    if not total:
        raise TemplateError("Die Vorlage braucht mindestens eine Kompetenz")
    return {"name": _text(data.get("name"), 200, "Name des Rahmens", required=True),
            "subject": _text(data.get("subject"), 40, "Fach"),
            "description": _text(data.get("description"), 500, "Beschreibung"),
            "levels": levels, "support_level": support, "areas": areas}


def parse_json(text: str) -> dict:
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise TemplateError("Die Datei ist kein gültiges JSON") from exc
    return normalize_template(data)


CSV_HEAD = ("bereich", "kompetenz")


def parse_csv(text: str, *, name: str, levels: Optional[Sequence[str]] = None, subject: str = "",
              description: str = "") -> dict:
    """CSV mit den Spalten ``Bereich;Kompetenz[;Kürzel][;Stufe 1][;Stufe 2]…`` (Trenner ``;``, ``,`` oder Tabulator).

    Spalten ab der dritten: eine mit der Überschrift „Kürzel“/„Code“, danach beliebig viele Beschreibungen je Stufe.
    ``levels`` = Beschriftungen der Stufen (Standard: :data:`DEFAULT_LEVELS`)."""
    text = text.lstrip("﻿")
    first = text.splitlines()[0] if text.strip() else ""
    delimiter = max(";,\t", key=first.count) if first else ";"
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise TemplateError("Die CSV braucht eine Kopfzeile und mindestens eine Kompetenz")
    head = [h.strip().lower() for h in rows[0]]
    if len(head) < 2 or tuple(head[:2]) != CSV_HEAD:
        raise TemplateError("Die CSV muss mit den Spalten „Bereich“ und „Kompetenz“ beginnen")
    code_col = next((i for i, h in enumerate(head) if h in ("kürzel", "kuerzel", "code")), None)
    desc_cols = [i for i in range(2, len(head)) if i != code_col]
    areas: list[dict] = []
    by_name: dict[str, dict] = {}
    for r in rows[1:]:
        r = [c.strip() for c in r] + [""] * (len(head) - len(r))
        area_name = r[0] or (areas[-1]["name"] if areas else "")
        if not area_name or not r[1]:
            raise TemplateError("Jede Zeile braucht einen Bereich und eine Kompetenz")
        area = by_name.get(area_name)
        if area is None:
            area = by_name[area_name] = {"name": area_name, "competencies": []}
            areas.append(area)
        descriptors = [r[i] for i in desc_cols]
        while descriptors and not descriptors[-1]:
            descriptors.pop()
        area["competencies"].append({"code": r[code_col] if code_col is not None else "", "title": r[1],
                                     "descriptors": descriptors})
    return normalize_template({"name": name, "subject": subject, "description": description,
                               "levels": list(levels) if levels else DEFAULT_LEVELS, "areas": areas})


def to_csv(template: Mapping) -> str:
    """Rahmen als CSV (``;``): Bereich, Kompetenz, Kürzel, Beschreibungen je Stufe."""
    levels = template.get("levels") or []
    out = io.StringIO()
    w = csv.writer(out, delimiter=";", lineterminator="\n")
    w.writerow(["Bereich", "Kompetenz", "Kürzel", *[f"Stufe {i + 1}: {lv}" for i, lv in enumerate(levels)]])
    for area in template.get("areas") or []:
        for c in area.get("competencies") or []:
            desc = list(c.get("descriptors") or [])
            desc += [""] * (len(levels) - len(desc))
            w.writerow([area["name"], c["title"], c.get("code", ""), *desc])
    return out.getvalue()


# --------------------------------------------------------------------------------------------- Lernstand
def latest(rows: Iterable[Mapping]) -> Optional[Mapping]:
    """Jüngster Eintrag (Datum, dann ID) aus Einträgen mit ``assessed_on`` und ``id``."""
    best = None
    for r in rows:
        if best is None or (r["assessed_on"], r["id"]) > (best["assessed_on"], best["id"]):
            best = r
    return best


def needs_support(teacher: Optional[int], own: Optional[int], support_level: int = 1) -> bool:
    """„Braucht Unterstützung“: Einschätzung der Lehrkraft höchstens ``support_level``; ohne Einschätzung der Lehrkraft
    zählt die Selbsteinschätzung."""
    if support_level < 1:
        return False
    if teacher is not None:
        return teacher <= support_level
    return own is not None and own <= support_level


def progress(levels: Mapping[int, int], competency_ids: Sequence[int], max_level: int) -> float:
    """Fortschritt 0…1: Mittel aus Stufe/Höchststufe über alle Kompetenzen (ohne Eintrag = 0)."""
    if not competency_ids or max_level < 1:
        return 0.0
    return sum(min(levels.get(c, 0), max_level) for c in competency_ids) / (max_level * len(competency_ids))


def week_start(day: date) -> date:
    """Montag der Woche."""
    return day - timedelta(days=day.weekday())


def parse_day(value: Any, name: str = "Datum") -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValueError(f"{name} ist kein gültiges Datum") from exc


# ------------------------------------------------------------------------------------ Abzeichen-Kriterien
def validate_criteria(criteria: Any, max_levels: Mapping[str, int] | None = None) -> Optional[dict]:
    """Kriterien einer Abzeichen-Vergabe prüfen. ``None`` = nur manuell.

    * ``{"type": "competencies", "competency_ids": [..], "min_level": n}`` – alle genannten Kompetenzen erreicht
    * ``{"type": "area", "area_id": n, "min_level": n, "share": 0.8}`` – Anteil der Kompetenzen eines Bereichs
    * ``{"type": "framework", "framework_id": n, "min_level": n, "share": 1.0}`` – Anteil eines ganzen Rahmens"""
    if criteria in (None, {}):
        return None
    if not isinstance(criteria, Mapping):
        raise ValueError("Die Vergabekriterien sind ungültig")
    kind = criteria.get("type")
    min_level = criteria.get("min_level")
    if not isinstance(min_level, int) or isinstance(min_level, bool) or not (1 <= min_level <= MAX_LEVELS):
        raise ValueError("Die Mindeststufe ist ungültig")
    if kind == "competencies":
        ids = criteria.get("competency_ids")
        if (not isinstance(ids, list) or not ids or len(ids) > 100
                or any(not isinstance(i, int) or isinstance(i, bool) for i in ids)):
            raise ValueError("Bitte mindestens eine Kompetenz wählen")
        return {"type": kind, "competency_ids": sorted(set(ids)), "min_level": min_level}
    if kind in ("area", "framework"):
        key = "area_id" if kind == "area" else "framework_id"
        ref = criteria.get(key)
        share = criteria.get("share", 1.0)
        if not isinstance(ref, int) or isinstance(ref, bool):
            raise ValueError("Bereich bzw. Rahmen fehlt")
        if not isinstance(share, (int, float)) or isinstance(share, bool) or not (0 < share <= 1):
            raise ValueError("Der Anteil muss zwischen 1 % und 100 % liegen")
        return {"type": kind, key: ref, "min_level": min_level, "share": float(share)}
    raise ValueError("Unbekannte Vergabeart")


def criteria_met(criteria: Optional[Mapping], teacher_levels: Mapping[int, int], areas: Mapping[int, Sequence[int]],
                 frameworks: Mapping[int, Sequence[int]]) -> bool:
    """Erfüllt die Lernstand-Lage einer Person die Kriterien? ``teacher_levels``: Kompetenz-ID → aktuelle Stufe der
    Lehrkraft; ``areas``/``frameworks``: ID → Kompetenz-IDs. Manuelle Abzeichen (``None``) sind nie automatisch erfüllt."""
    if not criteria:
        return False
    need = criteria["min_level"]
    kind = criteria["type"]
    if kind == "competencies":
        ids = criteria["competency_ids"]
        return bool(ids) and all(teacher_levels.get(i, 0) >= need for i in ids)
    ids = list((areas if kind == "area" else frameworks).get(criteria["area_id" if kind == "area" else "framework_id"], []))
    if not ids:
        return False
    reached = sum(1 for i in ids if teacher_levels.get(i, 0) >= need)
    return reached / len(ids) + 1e-9 >= criteria["share"]


# ---------------------------------------------------------------------------------------- Beispielrahmen
_GS_LEVELS = ["Ich fange an", "Ich kann es mit Hilfe", "Ich kann es allein", "Ich kann es erklären"]
_MONTESSORI_LEVELS = ["Eingeführt", "Übt mit dem Material", "Arbeitet sicher", "Kann es weitergeben"]


def _comps(prefix: str, titles: Sequence[str]) -> list[dict]:
    return [{"code": f"{prefix}{i + 1}", "title": t, "descriptors": []} for i, t in enumerate(titles)]


TEMPLATES: dict[str, dict] = {
    "grundschule-mathe-deutsch": {
        "name": "Grundschule Mathe und Deutsch",
        "subject": "",
        "description": "Beispielrahmen für die Klassen 1 und 2 mit „Ich kann …“-Aussagen.",
        "levels": _GS_LEVELS,
        "support_level": 1,
        "areas": [
            {"name": "Mathe: Zahlen und Rechnen", "competencies": _comps("MZ", [
                "Ich kann bis 20 sicher zählen und Mengen erfassen.",
                "Ich kann Zahlen bis 100 lesen, schreiben und ordnen.",
                "Ich kann Plus- und Minusaufgaben im Zahlenraum bis 20 lösen.",
                "Ich kann Plus- und Minusaufgaben im Zahlenraum bis 100 lösen.",
                "Ich kann das kleine Einmaleins an Beispielen erklären."])},
            {"name": "Mathe: Formen und Größen", "competencies": _comps("MF", [
                "Ich kann Dreieck, Viereck und Kreis erkennen und benennen.",
                "Ich kann Längen mit Lineal und Zentimetern messen.",
                "Ich kann die Uhrzeit auf der Uhr ablesen.",
                "Ich kann mit Euro und Cent rechnen."])},
            {"name": "Deutsch: Sprechen und Zuhören", "competencies": _comps("DS", [
                "Ich kann anderen zuhören und beim Thema bleiben.",
                "Ich kann in ganzen Sätzen von etwas erzählen.",
                "Ich kann einen kurzen Text in eigenen Worten wiedergeben."])},
            {"name": "Deutsch: Lesen", "competencies": _comps("DL", [
                "Ich kann alle Buchstaben und Lautverbindungen lesen.",
                "Ich kann kurze Texte flüssig lesen.",
                "Ich kann Fragen zu einem Text beantworten.",
                "Ich kann einen Text finden, der zu meiner Frage passt."])},
            {"name": "Deutsch: Schreiben", "competencies": _comps("DW", [
                "Ich kann Buchstaben und Wörter in lesbarer Schrift schreiben.",
                "Ich kann lautgetreue Wörter richtig aufschreiben.",
                "Ich kann einen Satz mit Großbuchstabe am Anfang und Punkt am Ende schreiben.",
                "Ich kann eine kleine Geschichte mit Anfang, Mitte und Schluss schreiben.",
                "Ich kann meinen Text mit Wörterliste und Hilfen überprüfen."])},
        ],
    },
    "montessori-materialien": {
        "name": "Montessori-Materialien",
        "subject": "",
        "description": "Beispielrahmen nach dem Dreierschritt: eingeführt, geübt, sicher – für die Freiarbeit.",
        "levels": _MONTESSORI_LEVELS,
        "support_level": 1,
        "areas": [
            {"name": "Übungen des täglichen Lebens", "competencies": _comps("PL", [
                "Ich kann mit der Zange und dem Löffel umfüllen, ohne etwas zu verschütten.",
                "Ich kann Blumen schneiden und in eine Vase stellen.",
                "Ich kann Schuhe putzen und Tisch decken.",
                "Ich kann eine Schleife binden."])},
            {"name": "Sinnesmaterial", "competencies": _comps("SI", [
                "Ich kann die Zylinderblöcke nach Größe ordnen.",
                "Ich kann den Rosa Turm und die Braune Treppe bauen.",
                "Ich kann die Farbtäfelchen nach Farbstufen sortieren.",
                "Ich kann die Geometrische Kommode mit den Formen benennen."])},
            {"name": "Sprache", "competencies": _comps("SP", [
                "Ich kann Sandpapierbuchstaben nachspuren und den Laut sagen.",
                "Ich kann Wörter mit dem Beweglichen Alphabet legen.",
                "Ich kann Wortarten mit den Symbolen der Grammatik zuordnen.",
                "Ich kann Lesekarten zu einem Thema lesen und ordnen."])},
            {"name": "Mathematik", "competencies": _comps("MA", [
                "Ich kann mit den Rechenstäben bis 10 zählen und ordnen.",
                "Ich kann mit dem Goldenen Perlenmaterial Einer, Zehner, Hunderter und Tausender legen.",
                "Ich kann am Markenspiel Plus- und Minusaufgaben mit Übertrag lösen.",
                "Ich kann am Streifenbrett die Einmaleins-Reihen legen.",
                "Ich kann mit dem Bruchrechenmaterial Teile vergleichen."])},
            {"name": "Kosmische Erziehung", "competencies": _comps("KO", [
                "Ich kann einen Zeitstrahl des Lebens auf der Erde legen und erzählen.",
                "Ich kann die Kontinente auf der Landkarte benennen.",
                "Ich kann ein Thema recherchieren und anderen vorstellen."])},
        ],
    },
}
