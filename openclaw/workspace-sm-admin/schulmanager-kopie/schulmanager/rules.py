"""Regeln und Prioritäten der Stundenplan-Optimierung als Bausteine (``docs/REGELN-UND-PRIORITAETEN.md``).

Statt zehn nackter Zahlen (``Settings.weights``) beschreibt ``Settings.rules`` die Optimierung als Katalog
verständlicher Bausteine mit einer **Wichtigkeit** (``aus`` · ``nett`` · ``wichtig`` · ``sehr_wichtig`` · ``muss``),
optionalen Parametern (z. B. „Hauptfächer spätestens bis Stunde“) und **Gültigkeiten** (Ausnahmen je Jahrgang,
Klasse, Fach oder Lehrkraft, jede Woche oder nur in bestimmten Wochen/Rhythmus)::

    settings.rules = {
        "profile": "gymnasium",          # Vorlage (Schulart), von der die Schule ausgegangen ist; "" = keine
        "advanced": False,               # alle Bausteine zeigen (auch ohne Datenbezug)
        "items": {
            "class_gap": {"level": "sehr_wichtig", "weight": None, "params": {},
                          "overrides": [{"level": "nett", "grades": [11, 12, 13], "classes": [], "subjects": [],
                                         "teachers": [], "weeks": [], "rhythm": None, "note": "Oberstufe"}]},
            ...
        },
        "templates": [ {"id": "...", "name": "...", "description": "...", "items": {...}} ]   # eigene Vorlagen
    }

Die Zahlen bleiben die Wahrheit für den Generator: ``apply_to_settings`` schreibt aus den Bausteinen die Felder
``weights``, ``core_latest_period``, ``site_travel_periods``, ``prefer_doubles``, ``double_alignment`` und
``auto_replan``; ``sync_from_numbers`` geht den umgekehrten Weg (ältere Oberflächen/APIs, die nur die Zahlen setzen).
Beide Richtungen sind verlustfrei: Ein Gewicht, das keiner Stufe entspricht, wird als ``weight`` (eigener Wert)
mitgeführt. Dokumente ohne ``rules`` werden beim Lesen aus den Zahlen abgeleitet (Vorlage „standard“).

Gültigkeiten wertet :class:`PlanWeights` für den Generator je Klasse/Lehrkraft/Kurs und Wochenvariante aus.

Außerdem hier: Klausur-Höchstzahlen mit Vererbung Schule → Jahrgang → Klasse (:func:`exam_limits_for_class`).
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

from . import weeks as wk
from .models import School, SchoolClass, Settings

# --------------------------------------------------------------------------------------------- Stufen
LEVELS = ("aus", "nett", "wichtig", "sehr_wichtig", "muss")
LEVEL_LABELS = {"aus": "Aus", "nett": "Nett", "wichtig": "Wichtig", "sehr_wichtig": "Sehr wichtig", "muss": "Muss"}
#: Faktor auf das Grundgewicht (``wichtig`` = Grundgewicht = bisheriger Standardwert)
LEVEL_FACTOR = {"aus": 0.0, "nett": 0.25, "wichtig": 1.0, "sehr_wichtig": 4.0, "muss": 20.0}
LEVEL_TEXT = {
    "aus": "wird nicht beachtet",
    "nett": "zählt wenig – andere Ziele gehen vor",
    "wichtig": "normales Gewicht (Standard)",
    "sehr_wichtig": "zählt viermal so stark wie „Wichtig“",
    "muss": "zählt zwanzigmal so stark – praktisch eine harte Regel",
}
SWITCH_LEVELS = ("aus", "an")
SCOPE_DIMS = ("grades", "classes", "subjects", "teachers")


@dataclass(frozen=True)
class ParamDef:
    key: str
    label: str
    kind: str                       # "int" | "bool" | "choice"
    settings_attr: str = ""         # Feld in ``Settings``, das den Wert trägt (Synchronisation)
    min: Optional[int] = None
    max: Optional[int] = None
    choices: tuple[tuple[str, str], ...] = ()
    help: str = ""
    #: 1-basiert anzeigen (gespeichert 0-basiert, z. B. Stunden)
    one_based: bool = False
    #: darf in einer Ausnahme (Gültigkeit) abweichen
    overridable: bool = False


@dataclass(frozen=True)
class RuleDef:
    id: str
    group: str
    title: str
    text: str
    #: ``level`` (fünf Stufen) oder ``switch`` (an/aus)
    control: str = "level"
    weight_key: str = ""            # Attribut von ``Weights``
    base: float = 0.0               # Grundgewicht = Stufe „wichtig“
    params: tuple[ParamDef, ...] = ()
    #: Dimensionen, in denen Ausnahmen möglich sind
    scope: tuple[str, ...] = ()
    #: Datenbezug: Schlüssel in ``context`` – 0/False ⇒ Baustein ohne Bezug (nur unter „Erweitert“)
    requires: str = ""
    requires_text: str = ""
    #: Kennzahl des Qualitätsberichts (``/planning/report/details?kind=…``)
    report: str = ""
    #: „Muss“ wird im Generator zu einer harten Regel
    hard: bool = False
    hard_text: str = ""
    #: nur unter „Erweitert“ (Feinsteuerung)
    advanced: bool = False
    #: Einheit, auf die der Baustein wirkt: class | teacher | course | school
    entity: str = "school"
    #: Schalter: Feld in ``Settings``
    switch_attr: str = ""


GROUPS: tuple[tuple[str, str, str], ...] = (
    ("klassen", "Für die Schülerinnen und Schüler", "Wie der Schultag der Klassen aussehen soll."),
    ("unterricht", "Unterricht und Fächer", "Wie Fächer und Blöcke über Tag und Woche verteilt werden."),
    ("lehrkraefte", "Für die Lehrkräfte", "Rücksicht auf das Kollegium – meist etwas niedriger gewichtet als die Klassen."),
    ("automatik", "Automatik", "Was nach Änderungen an den Daten automatisch passiert."),
)

RULES: tuple[RuleDef, ...] = (
    RuleDef(
        "class_gap", "klassen", "Keine Hohlstunden für Klassen",
        "Freistunden mitten im Schultag einer Klasse (Unterricht davor und danach). Für jüngere Klassen ein Muss, "
        "in der Oberstufe oft hinnehmbar – dafür gibt es Ausnahmen je Jahrgang.",
        weight_key="class_gap", base=100.0, scope=("grades", "classes"), report="class_gaps", entity="class",
    ),
    RuleDef(
        "late_start", "klassen", "Unterricht beginnt zur ersten Stunde",
        "Tage, an denen eine Klasse erst später beginnt, werden vermieden – verlässliche Anfangszeiten für Familien "
        "und Busverkehr. An Abendschulen sinnvollerweise „Aus“.",
        weight_key="late_start", base=40.0, scope=("grades", "classes"), entity="class",
    ),
    RuleDef(
        "day_balance", "klassen", "Gleichmäßig lange Schultage",
        "Ähnlich viele Stunden an jedem Tag statt sehr langer und sehr kurzer Tage.",
        weight_key="day_balance", base=6.0, scope=("grades", "classes"), entity="class",
    ),
    RuleDef(
        "core_late", "klassen", "Hauptfächer früh am Tag",
        "Fächer mit der Markierung „Hauptfach“ liegen möglichst bis zur eingestellten Stunde. Mit „Muss“ dürfen sie "
        "nie später liegen (harte Regel).",
        weight_key="core_late", base=6.0,
        params=(ParamDef("core_latest_period", "Hauptfächer spätestens bis Stunde", "int",
                         settings_attr="core_latest_period", min=0, max=15, one_based=True, overridable=True,
                         help="Letzte Stunde, in der ein Hauptfach noch liegen darf."),),
        scope=("grades", "classes", "subjects"), requires="core_subjects",
        requires_text="Es ist kein Fach als Hauptfach markiert (Stammdaten → Fächer).",
        report="core_late", hard=True, hard_text="Hauptfächer liegen nie nach der eingestellten Stunde.",
        entity="course",
    ),
    RuleDef(
        "spread", "unterricht", "Fächer über die Woche verteilen",
        "Ein Fach mit bis zu drei Wochenstunden liegt nicht an direkt aufeinanderfolgenden Tagen.",
        weight_key="spread", base=5.0, scope=("grades", "classes", "subjects"), entity="course",
    ),
    RuleDef(
        "doubles", "unterricht", "Doppelstunden als Block",
        "Gewünschte Doppelstunden bleiben zusammen statt in Einzelstunden zu zerfallen. Welche Fächer Doppelstunden "
        "bekommen, steht in der Stundentafel – oder pauschal für alle Fächer ab zwei Wochenstunden.",
        weight_key="double_split", base=3.0,
        params=(
            ParamDef("prefer_doubles", "Alle Fächer ab 2 Wochenstunden als Doppelstunden planen", "bool",
                     settings_attr="prefer_doubles"),
            ParamDef("double_alignment", "Lage von Doppelstunden", "choice", settings_attr="double_alignment",
                     choices=(("bloecke", "Nur in Pausenblöcken (1.–2., 3.–4., 5.–6. Stunde …)"),
                              ("pausen", "Nur nicht über eine Pause hinweg"),
                              ("frei", "Keine Einschränkung"))),
        ),
        scope=("grades", "classes", "subjects"), entity="course",
    ),
    RuleDef(
        "position", "unterricht", "Unterricht möglichst früh am Tag (Feinsteuerung)",
        "Allgemeine Tendenz, Stunden früh zu legen. Ein kleiner Wert genügt; „Aus“ an Abendschulen.",
        weight_key="position", base=0.6, advanced=True, scope=("grades", "classes", "subjects"), entity="course",
    ),
    RuleDef(
        "teacher_gap", "lehrkraefte", "Wenige Springstunden für Lehrkräfte",
        "Freistunden zwischen den Unterrichtsstunden einer Lehrkraft. Etwas Spielraum hilft der Vertretungsplanung.",
        weight_key="teacher_gap", base=4.0, scope=("teachers",), report="teacher_gaps", entity="teacher",
    ),
    RuleDef(
        "teacher_wish", "lehrkraefte", "Wünsche der Lehrkräfte berücksichtigen",
        "Weiche Wünsche aus dem Lehrkraft-Profil (z. B. „nicht in der 1. Stunde“, „Freitagnachmittag frei“). "
        "Harte Sperrzeiten gelten unabhängig davon immer.",
        weight_key="teacher_wish", base=5.0, scope=("teachers",), requires="teacher_wishes",
        requires_text="Keine Lehrkraft hat Wünsche eingetragen.", entity="teacher",
    ),
    RuleDef(
        "site_change", "lehrkraefte", "Standortwechsel vermeiden",
        "Wechsel einer Lehrkraft zwischen den Standorten am selben Tag. Lehrkräfte, die laut Profil nicht pendeln, "
        "wechseln ohnehin praktisch nie. Die Wegezeit wird immer eingehalten (harte Regel).",
        weight_key="site_change", base=15.0,
        params=(ParamDef("site_travel_periods", "Wegezeit zwischen Standorten (freie Stunden)", "int",
                         settings_attr="site_travel_periods", min=0, max=5,
                         help="Freie Stunden zwischen Unterricht an verschiedenen Standorten – für Lehrkräfte und "
                              "Klassen, immer eingehalten."),),
        scope=("teachers",), requires="sites", requires_text="Die Schule hat nur einen Standort.",
        report="site_changes", entity="teacher",
    ),
    RuleDef(
        "auto_replan", "automatik", "Nach Änderungen automatisch neu planen",
        "Nach Änderungen an Lehrkräften, Räumen, Klassen, Kursen oder Stundentafeln werden ungültige oder fehlende "
        "Stunden automatisch neu gelegt (nur die betroffenen Kurse). Jede automatische Änderung lässt sich unter "
        "„Verlauf & Audit“ rückgängig machen.",
        control="switch", switch_attr="auto_replan",
    ),
)
RULE_BY_ID: dict[str, RuleDef] = {r.id: r for r in RULES}

#: Harte Regeln, die immer gelten – zur Anzeige mit Datenbezug (keine Einstellung hier)
HARD_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("no_double_booking", "Keine Doppelbelegung", "Klasse, Lehrkraft und Raum sind nie zweimal gleichzeitig belegt.", ""),
    ("class_rules", "Sperrzeiten, Unterrichtstage und Höchststunden je Klasse",
     "Praxistage, Rhythmen, eigene Unterrichtstage und „max. Stunden pro Tag“ stehen bei der Klasse.", "/stammdaten/classes"),
    ("teacher_rules", "Sperrzeiten, Arbeitszeiten und Höchststunden je Lehrkraft",
     "Sperrzeiten, Arbeitszeitfenster, Deputat und „max. Stunden pro Tag“ stehen bei der Lehrkraft.", "/stammdaten/teachers"),
    ("rooms", "Fachräume", "Fächer mit Raumtyp (Sporthalle, Chemie …) bekommen nur passende Räume.", "/stammdaten/subjects"),
    ("subject_per_day", "Höchstzahl Blöcke eines Fachs pro Tag", "Steht am Fach („max. Blöcke pro Tag“).", "/stammdaten/subjects"),
    ("travel", "Wegezeit zwischen Standorten", "Siehe Baustein „Standortwechsel vermeiden“ (Parameter Wegezeit).", ""),
)


# --------------------------------------------------------------------------------------------- Vorlagen
@dataclass(frozen=True)
class Template:
    id: str
    name: str
    description: str
    #: Bausteine, die diese Schulart ohne „Erweitert“ sieht
    show: tuple[str, ...]
    items: dict[str, dict]
    builtin: bool = True


def _it(level: str, **params: Any) -> dict:
    out: dict[str, Any] = {"level": level}
    if params:
        out["params"] = params
    return out


_BASE_SHOW = ("class_gap", "late_start", "day_balance", "core_late", "spread", "doubles", "teacher_gap",
              "teacher_wish", "site_change", "auto_replan")

TEMPLATES: tuple[Template, ...] = (
    Template(
        "standard", "Allgemein (Standard)",
        "Ausgewogene Voreinstellung – entspricht den bisherigen Standardwerten. Für Schulen, die nicht in eine "
        "der anderen Schularten passen.",
        _BASE_SHOW,
        {"class_gap": _it("wichtig"), "late_start": _it("wichtig"), "day_balance": _it("wichtig"),
         "core_late": _it("wichtig", core_latest_period=5), "spread": _it("wichtig"),
         "doubles": _it("wichtig", prefer_doubles=True, double_alignment="bloecke"), "position": _it("wichtig"),
         "teacher_gap": _it("wichtig"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "grundschule", "Grundschule",
        "Kinder haben nie Lücken und beginnen verlässlich zur ersten Stunde; Hauptfächer am Vormittag; Einzelstunden "
        "sind üblich, Doppelstunden nur, wo die Stundentafel sie vorsieht.",
        ("class_gap", "late_start", "day_balance", "core_late", "spread", "doubles", "teacher_gap", "auto_replan"),
        {"class_gap": _it("muss"), "late_start": _it("sehr_wichtig"), "day_balance": _it("sehr_wichtig"),
         "core_late": _it("wichtig", core_latest_period=3), "spread": _it("wichtig"),
         "doubles": _it("nett", prefer_doubles=False, double_alignment="frei"), "position": _it("wichtig"),
         "teacher_gap": _it("nett"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "gymnasium", "Gymnasium / Oberstufe",
        "Sekundarstufe I ohne Hohlstunden, Oberstufe (Jahrgang 11–13) mit Freistunden; Hauptfächer bis zur 6. Stunde; "
        "Doppelstunden in Pausenblöcken.",
        _BASE_SHOW,
        {"class_gap": {"level": "sehr_wichtig", "overrides": [
            {"level": "nett", "grades": [11, 12, 13], "note": "Oberstufe: Freistunden sind hinnehmbar"}]},
         "late_start": {"level": "wichtig", "overrides": [{"level": "nett", "grades": [11, 12, 13], "note": "Oberstufe"}]},
         "day_balance": _it("wichtig"), "core_late": _it("wichtig", core_latest_period=5), "spread": _it("wichtig"),
         "doubles": _it("wichtig", prefer_doubles=True, double_alignment="bloecke"), "position": _it("wichtig"),
         "teacher_gap": _it("wichtig"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "gesamtschule", "Gesamtschule / Sekundarschule",
        "Lange, gleichmäßige Tage mit Ganztagsanteil; keine Hohlstunden in der Sekundarstufe I, Oberstufe lockerer; "
        "Doppelstunden als Regelfall.",
        _BASE_SHOW,
        {"class_gap": {"level": "sehr_wichtig", "overrides": [{"level": "nett", "grades": [11, 12, 13], "note": "Oberstufe"}]},
         "late_start": _it("wichtig"), "day_balance": _it("sehr_wichtig"),
         "core_late": _it("wichtig", core_latest_period=5), "spread": _it("wichtig"),
         "doubles": _it("sehr_wichtig", prefer_doubles=True, double_alignment="bloecke"), "position": _it("nett"),
         "teacher_gap": _it("wichtig"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "berufsschule", "Berufsschule / Berufskolleg (Blockunterricht)",
        "Lange Blocktage statt gleichmäßiger Verteilung; Doppelstunden sehr wichtig; keine Hauptfach-Regel; "
        "Standortwechsel vermeiden.",
        ("class_gap", "doubles", "spread", "teacher_gap", "teacher_wish", "site_change", "auto_replan"),
        {"class_gap": _it("wichtig"), "late_start": _it("nett"), "day_balance": _it("nett"),
         "core_late": _it("aus", core_latest_period=7), "spread": _it("nett"),
         "doubles": _it("sehr_wichtig", prefer_doubles=True, double_alignment="pausen"), "position": _it("nett"),
         "teacher_gap": _it("wichtig"), "teacher_wish": _it("wichtig"), "site_change": _it("sehr_wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "foerderschule", "Förderschule",
        "Fester, verlässlicher Rhythmus: nie Lücken, gleichmäßige Tage, Hauptfächer am Vormittag, Fächer über die "
        "Woche verteilt; Einzelstunden statt langer Blöcke.",
        ("class_gap", "late_start", "day_balance", "core_late", "spread", "doubles", "teacher_wish", "auto_replan"),
        {"class_gap": _it("muss"), "late_start": _it("sehr_wichtig"), "day_balance": _it("sehr_wichtig"),
         "core_late": _it("wichtig", core_latest_period=3), "spread": _it("sehr_wichtig"),
         "doubles": _it("nett", prefer_doubles=False, double_alignment="frei"), "position": _it("wichtig"),
         "teacher_gap": _it("nett"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "montessori", "Montessori / offene Konzepte",
        "Lange Arbeitsphasen (Doppelstunden frei im Tag), keine Hauptfach-Regel, wenig Zwang zur Verteilung über die "
        "Woche; Lücken für Lerngruppen vermeiden.",
        ("class_gap", "late_start", "day_balance", "doubles", "spread", "teacher_gap", "auto_replan"),
        {"class_gap": _it("sehr_wichtig"), "late_start": _it("wichtig"), "day_balance": _it("wichtig"),
         "core_late": _it("aus", core_latest_period=5), "spread": _it("nett"),
         "doubles": _it("sehr_wichtig", prefer_doubles=True, double_alignment="frei"), "position": _it("nett"),
         "teacher_gap": _it("nett"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "abendschule", "Abendschule / Kolleg",
        "Unterricht liegt planmäßig spät: keine Regeln „zur ersten Stunde“ oder „früh am Tag“; Wünsche der oft "
        "nebenberuflichen Lehrkräfte wiegen schwer.",
        ("class_gap", "day_balance", "doubles", "teacher_gap", "teacher_wish", "auto_replan"),
        {"class_gap": _it("sehr_wichtig"), "late_start": _it("aus"), "day_balance": _it("wichtig"),
         "core_late": _it("aus", core_latest_period=7), "spread": _it("wichtig"),
         "doubles": _it("wichtig", prefer_doubles=True, double_alignment="pausen"), "position": _it("aus"),
         "teacher_gap": _it("wichtig"), "teacher_wish": _it("sehr_wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
    Template(
        "ganztag", "Ganztagsschule",
        "Gleichmäßig lange Tage bis in den Nachmittag; keine Hohlstunden; Hauptfächer am Vormittag, Nachmittag für "
        "Neben- und Wahlfächer; Doppelstunden als Regelfall.",
        _BASE_SHOW,
        {"class_gap": _it("sehr_wichtig"), "late_start": _it("wichtig"), "day_balance": _it("sehr_wichtig"),
         "core_late": _it("wichtig", core_latest_period=5), "spread": _it("wichtig"),
         "doubles": _it("wichtig", prefer_doubles=True, double_alignment="bloecke"), "position": _it("nett"),
         "teacher_gap": _it("wichtig"), "teacher_wish": _it("wichtig"), "site_change": _it("wichtig", site_travel_periods=1),
         "auto_replan": _it("an")},
    ),
)
TEMPLATE_BY_ID: dict[str, Template] = {t.id: t for t in TEMPLATES}
DEFAULT_PROFILE = "standard"


# --------------------------------------------------------------------------------------------- Stufe ↔ Gewicht
def weight_for(base: float, level: str, weight: Optional[float] = None) -> float:
    """Wirksames Gewicht: eigener Wert, sonst Grundgewicht × Stufenfaktor."""
    if weight is not None:
        return max(0.0, float(weight))
    return round(base * LEVEL_FACTOR.get(level, 1.0), 6)


def level_for_weight(base: float, weight: float) -> tuple[str, bool]:
    """Stufe zu einem Gewicht und ob sie den Wert exakt trifft (sonst „eigener Wert“)."""
    w = max(0.0, float(weight))
    if w == 0:
        return "aus", True
    if base <= 0:
        return "wichtig", False
    ratio = w / base
    best, dist = "wichtig", math.inf
    for lvl in ("nett", "wichtig", "sehr_wichtig", "muss"):
        d = abs(math.log(ratio) - math.log(LEVEL_FACTOR[lvl]))
        if d < dist:
            best, dist = lvl, d
    return best, abs(ratio - LEVEL_FACTOR[best]) < 1e-6


def _param_default(p: ParamDef, settings: Settings) -> Any:
    return getattr(settings, p.settings_attr) if p.settings_attr else None


# --------------------------------------------------------------------------------------------- Normalisieren
def _ints(values: Any) -> list[int]:
    out = []
    for v in values or []:
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            continue
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return sorted(set(out))


def _strs(values: Any) -> list[str]:
    return sorted({str(v) for v in (values or []) if isinstance(v, (str, int)) and str(v).strip()})


def _norm_params(rule: RuleDef, raw: Any, settings: Optional[Settings], errors: list[str], where: str,
                 partial: bool = False) -> dict:
    """Parameter prüfen und auf gültige Werte bringen (``partial``: fehlende Werte bleiben weg – Ausnahmen)."""
    raw = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}
    for p in rule.params:
        if p.key not in raw:
            if not partial:
                dflt = _param_default(p, settings) if settings is not None else None
                if dflt is not None:
                    out[p.key] = dflt
            continue
        v = raw[p.key]
        if p.kind == "bool":
            out[p.key] = bool(v)
        elif p.kind == "int":
            try:
                iv = int(v)
            except (TypeError, ValueError):
                errors.append(f"{where}: „{p.label}“ muss eine Zahl sein")
                continue
            if p.min is not None and iv < p.min or p.max is not None and iv > p.max:
                errors.append(f"{where}: „{p.label}“ außerhalb des zulässigen Bereichs")
                continue
            out[p.key] = iv
        elif p.kind == "choice":
            keys = [k for k, _ in p.choices]
            if v not in keys:
                errors.append(f"{where}: ungültige Auswahl für „{p.label}“")
                continue
            out[p.key] = v
    for k in raw:
        if k not in {p.key for p in rule.params}:
            errors.append(f"{where}: unbekannter Parameter „{k}“")
    return out


def _norm_override(rule: RuleDef, raw: Any, settings: Optional[Settings], errors: list[str], where: str) -> Optional[dict]:
    if not isinstance(raw, dict):
        errors.append(f"{where}: Ausnahme muss ein Objekt sein")
        return None
    level = raw.get("level", "wichtig")
    if level not in LEVELS:
        errors.append(f"{where}: ungültige Stufe „{level}“")
        return None
    out: dict[str, Any] = {"level": level, "weight": None, "params": {}, "note": str(raw.get("note") or "")[:120]}
    if raw.get("weight") is not None:
        try:
            out["weight"] = max(0.0, float(raw["weight"]))
        except (TypeError, ValueError):
            errors.append(f"{where}: eigener Wert muss eine Zahl sein")
    for dim in SCOPE_DIMS:
        vals = _ints(raw.get(dim)) if dim == "grades" else _strs(raw.get(dim))
        if vals and dim not in rule.scope:
            errors.append(f"{where}: Ausnahmen nach „{dim}“ sind für diesen Baustein nicht möglich")
            vals = []
        out[dim] = vals
    weeks = wk.normalize(_ints(raw.get("weeks")))
    rhythm = wk.normalize_rhythm(raw.get("rhythm")) if raw.get("rhythm") else None
    errs = wk.spec_errors(weeks, rhythm, where)
    errors.extend(errs)
    out["weeks"], out["rhythm"] = ([] if rhythm else weeks), rhythm
    out["params"] = _norm_params(rule, raw.get("params"), settings, errors, where, partial=True)
    out["params"] = {k: v for k, v in out["params"].items()
                     if any(p.key == k and p.overridable for p in rule.params)}
    if not any(out[d] for d in SCOPE_DIMS) and not weeks and not rhythm:
        errors.append(f"{where}: Eine Ausnahme braucht eine Gültigkeit (Jahrgang, Klasse, Fach, Lehrkraft oder Wochen).")
    return out


def _norm_item(rule: RuleDef, raw: Any, settings: Optional[Settings], errors: list[str]) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    where = f"Regel „{rule.title}“"
    if rule.control == "switch":
        level = raw.get("level", "an")
        if level not in SWITCH_LEVELS:
            level = "an" if level in ("wichtig", "sehr_wichtig", "muss") else "aus"
        return {"level": level, "weight": None, "params": {}, "overrides": []}
    level = raw.get("level", "wichtig")
    if level not in LEVELS:
        errors.append(f"{where}: ungültige Stufe „{level}“")
        level = "wichtig"
    weight = None
    if raw.get("weight") is not None:
        try:
            weight = max(0.0, float(raw["weight"]))
        except (TypeError, ValueError):
            errors.append(f"{where}: eigener Wert muss eine Zahl sein")
    out = {"level": level, "weight": weight,
           "params": _norm_params(rule, raw.get("params"), settings, errors, where), "overrides": []}
    ovs = raw.get("overrides") or []
    if not isinstance(ovs, list):
        errors.append(f"{where}: Ausnahmen müssen eine Liste sein")
        ovs = []
    for i, ov in enumerate(ovs[:50]):
        n = _norm_override(rule, ov, settings, errors, f"{where}, Ausnahme {i + 1}")
        if n is not None:
            out["overrides"].append(n)
    return out


def normalize(raw: Any, settings: Optional[Settings] = None, errors: Optional[list[str]] = None) -> dict:
    """Vollständige, geprüfte Form von ``settings.rules`` (unbekannte Bausteine werden gemeldet und verworfen)."""
    errors = errors if errors is not None else []
    raw = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {
        "profile": str(raw.get("profile") or "")[:60],
        "advanced": bool(raw.get("advanced", False)),
        "items": {},
        "templates": [],
    }
    items = raw.get("items") if isinstance(raw.get("items"), dict) else {}
    for rid, item in items.items():
        rule = RULE_BY_ID.get(str(rid))
        if rule is None:
            errors.append(f"Unbekannter Baustein „{rid}“")
            continue
        out["items"][rule.id] = _norm_item(rule, item, settings, errors)
    for t in (raw.get("templates") or [])[:30]:
        if not isinstance(t, dict) or not str(t.get("name") or "").strip():
            errors.append("Eigene Vorlage ohne Namen")
            continue
        titems: dict[str, dict] = {}
        for rid, item in (t.get("items") or {}).items():
            rule = RULE_BY_ID.get(str(rid))
            if rule is not None:
                titems[rule.id] = _norm_item(rule, item, None, errors)
        tid = str(t.get("id") or "").strip()[:60] or f"eigene-{len(out['templates']) + 1}"
        out["templates"].append({"id": tid, "name": str(t["name"]).strip()[:80],
                                 "description": str(t.get("description") or "")[:300], "items": titems,
                                 "show": _strs(t.get("show")) if t.get("show") else []})
    return out


def rule_errors(raw: Any, school: Optional[School] = None) -> list[str]:
    """Fehler eines Regel-Objekts (Form, Stufen, Gültigkeiten, Verweise auf Klassen/Fächer/Lehrkräfte)."""
    errors: list[str] = []
    norm = normalize(raw, school.settings if school else None, errors)
    if school is not None:
        classes, subjects, teachers = school.index("classes"), school.index("subjects"), school.index("teachers")
        for rid, item in norm["items"].items():
            for i, ov in enumerate(item["overrides"]):
                where = f"Regel „{RULE_BY_ID[rid].title}“, Ausnahme {i + 1}"
                for c in ov["classes"]:
                    if c not in classes:
                        errors.append(f"{where}: Klasse „{c}“ existiert nicht")
                for s in ov["subjects"]:
                    if s not in subjects:
                        errors.append(f"{where}: Fach „{s}“ existiert nicht")
                for t in ov["teachers"]:
                    if t not in teachers:
                        errors.append(f"{where}: Lehrkraft „{t}“ existiert nicht")
            for p in RULE_BY_ID[rid].params:
                if p.key == "core_latest_period" and p.key in item["params"] \
                        and item["params"][p.key] >= school.settings.periods:
                    errors.append("Späteste Hauptfachstunde liegt außerhalb des Zeitrasters")
    return errors


# --------------------------------------------------------------------------------------------- Ableiten / Synchronisieren
def derive_from_numbers(settings: Settings) -> dict:
    """Bausteine aus den gespeicherten Zahlen (ältere Dokumente, alte API): verlustfrei – Werte, die keiner Stufe
    entsprechen, bleiben als eigener Wert erhalten."""
    items: dict[str, dict] = {}
    for rule in RULES:
        if rule.control == "switch":
            items[rule.id] = {"level": "an" if getattr(settings, rule.switch_attr, True) else "aus",
                              "weight": None, "params": {}, "overrides": []}
            continue
        w = float(getattr(settings.weights, rule.weight_key, rule.base) or 0.0)
        level, exact = level_for_weight(rule.base, w)
        params = {p.key: getattr(settings, p.settings_attr) for p in rule.params if p.settings_attr}
        items[rule.id] = {"level": level, "weight": None if exact else w, "params": params, "overrides": []}
    return items


def resolve(settings: Settings) -> dict:
    """Vollständige Regeln der Schule: gespeicherte Bausteine, fehlende aus den Zahlen ergänzt. ``profile`` bleibt
    leer, solange die Schule keine Vorlage gewählt hat (die Oberfläche fragt dann einmal nach der Schulart)."""
    stored = normalize(settings.rules or {}, settings)
    derived = derive_from_numbers(settings)
    for rid, item in derived.items():
        stored["items"].setdefault(rid, item)
    return stored


def effective_weight(rule: RuleDef, item: dict) -> float:
    return weight_for(rule.base, item.get("level", "wichtig"), item.get("weight"))


def apply_to_settings(settings: Settings, rules: Optional[dict] = None) -> Settings:
    """Schreibt die Bausteine (``settings.rules`` oder ``rules``) in die Zahlenfelder, die der Generator liest."""
    norm = normalize(rules if rules is not None else settings.rules, settings)
    if rules is not None:
        settings.rules = norm
    items = norm["items"]
    for rule in RULES:
        item = items.get(rule.id)
        if item is None:
            continue
        if rule.control == "switch":
            setattr(settings, rule.switch_attr, item["level"] != "aus")
            continue
        setattr(settings.weights, rule.weight_key, effective_weight(rule, item))
        for p in rule.params:
            if p.settings_attr and p.key in item["params"]:
                setattr(settings, p.settings_attr, item["params"][p.key])
    return settings


def sync_from_numbers(settings: Settings, keys: Optional[Iterable[str]] = None) -> Settings:
    """Nach einer Änderung der Zahlen (``weights``, ``core_latest_period`` …) die Bausteine angleichen; Ausnahmen
    bleiben erhalten. ``keys``: geänderte Felder (``weights.class_gap``, ``prefer_doubles`` …), leer = alle."""
    if not settings.rules:
        settings.rules = {"profile": "", "advanced": False, "items": derive_from_numbers(settings), "templates": []}
        return settings
    changed = set(keys or [])
    derived = derive_from_numbers(settings)
    norm = normalize(settings.rules, settings)
    for rule in RULES:
        touched = not changed or f"weights.{rule.weight_key}" in changed or rule.switch_attr in changed \
            or any(p.settings_attr in changed for p in rule.params)
        if not touched:
            continue
        cur = norm["items"].get(rule.id, derived[rule.id])
        new = derived[rule.id]
        if rule.control == "switch" or not changed or f"weights.{rule.weight_key}" in changed:
            cur["level"], cur["weight"] = new["level"], new["weight"]
        for p in rule.params:
            if not changed or p.settings_attr in changed:
                cur["params"][p.key] = new["params"][p.key]
        norm["items"][rule.id] = cur
    settings.rules = norm
    return settings


def template_items(template_id: str, settings: Settings) -> Optional[dict]:
    """Bausteine einer eingebauten oder eigenen Vorlage (eigene aus ``settings.rules.templates``)."""
    t = TEMPLATE_BY_ID.get(template_id)
    if t is not None:
        return copy.deepcopy(t.items)
    for own in (settings.rules or {}).get("templates") or []:
        if own.get("id") == template_id:
            return copy.deepcopy(own.get("items") or {})
    return None


def shown_ids(template_id: str, settings: Settings) -> Optional[set[str]]:
    t = TEMPLATE_BY_ID.get(template_id)
    if t is not None:
        return set(t.show)
    for own in (settings.rules or {}).get("templates") or []:
        if own.get("id") == template_id:
            return set(own.get("show") or _BASE_SHOW)
    return None


# --------------------------------------------------------------------------------------------- Gültigkeiten
def _matches_class(ov: dict, cls: Optional[SchoolClass]) -> bool:
    if cls is None:
        return not ov["classes"] and not ov["grades"]
    if ov["classes"] and cls.id not in ov["classes"]:
        return False
    if ov["grades"] and int(cls.grade) not in ov["grades"]:
        return False
    return True


def override_applies(ov: dict, *, cls: Optional[SchoolClass] = None, classes: Iterable[SchoolClass] = (),
                     subjects: Iterable[str] = (), teachers: Iterable[str] = ()) -> bool:
    """Trifft die Ausnahme (ohne Wochen) auf Klasse(n), Fächer, Lehrkräfte? Leere Dimension = keine Bedingung."""
    pool = list(classes) + ([cls] if cls is not None else [])
    if ov["classes"] or ov["grades"]:
        if not pool or not any(_matches_class(ov, c) for c in pool):
            return False
    if ov["subjects"] and not any(s in ov["subjects"] for s in subjects):
        return False
    if ov["teachers"] and not any(t in ov["teachers"] for t in teachers):
        return False
    return True


def week_specs(settings: Settings) -> list[dict]:
    """Wochenangaben aller Ausnahmen (für die Wochenvarianten des Generators)."""
    out = []
    for item in resolve(settings)["items"].values():
        for ov in item["overrides"]:
            if ov["weeks"] or ov["rhythm"]:
                out.append({"weeks": ov["weeks"], "rhythm": ov["rhythm"]})
    return out


def _resolved_for(rule: RuleDef, item: dict, ovs: list[dict], fractions: list[list[float]], V: int
                  ) -> tuple[list[float], list[dict], list[bool]]:
    """Gewicht, Parameter und „hart“ je Wochenvariante für eine Einheit (Ausnahmen in Reihenfolge, letzte gewinnt).
    Eine Ausnahme, die nur in einem Teil der Wochen einer Variante gilt, wirkt anteilig."""
    base_w = effective_weight(rule, item)
    base_p = dict(item["params"])
    weights = [base_w] * V
    params = [dict(base_p) for _ in range(V)]
    hard = [rule.hard and item["level"] == "muss"] * V
    for ov, frac in zip(ovs, fractions):
        w_ov = weight_for(rule.base, ov["level"], ov.get("weight"))
        for v in range(V):
            f = frac[v]
            if f <= 0:
                continue
            weights[v] = weights[v] * (1 - f) + w_ov * f
            if f >= 0.999:
                params[v].update(ov["params"])
                hard[v] = rule.hard and ov["level"] == "muss"
    return weights, params, hard


class PlanWeights:
    """Gewichte je Klasse/Lehrkraft/Kurs und Wochenvariante für den Generator (Gültigkeiten eingerechnet).

    ``hz``/``groups`` sind der Planungshorizont und die Wochenvarianten des Schedulers (reale Wochen je Gruppe).
    """

    def __init__(self, school: School, hz, groups: list[list[int]]):
        self.school = school
        self.rules = resolve(school.settings)["items"]
        self.V = len(groups)
        self._fractions: dict[tuple, list[float]] = {}
        self.hz, self.groups = hz, groups

    def _fraction(self, ov: dict) -> list[float]:
        key = (tuple(ov["weeks"]), tuple(sorted((ov["rhythm"] or {}).items())))
        hit = self._fractions.get(key)
        if hit is None:
            if not ov["weeks"] and not ov["rhythm"]:
                hit = [1.0] * self.V
            else:
                members = self.hz.members(ov["weeks"], ov["rhythm"])
                hit = [len(members & set(g)) / max(1, len(g)) for g in self.groups]
            self._fractions[key] = hit
        return hit

    def _for(self, rid: str, **scope) -> tuple[list[float], list[dict], list[bool]]:
        rule, item = RULE_BY_ID[rid], self.rules[rid]
        ovs = [ov for ov in item["overrides"] if override_applies(ov, **scope)]
        return _resolved_for(rule, item, ovs, [self._fraction(ov) for ov in ovs], self.V)

    def for_class(self, cls: SchoolClass) -> list[tuple[float, float, float]]:
        """je Variante: (class_gap, late_start, day_balance)"""
        a = self._for("class_gap", cls=cls)[0]
        b = self._for("late_start", cls=cls)[0]
        c = self._for("day_balance", cls=cls)[0]
        return list(zip(a, b, c))

    def for_teacher(self, teacher_id: str) -> list[tuple[float, float, float]]:
        """je Variante: (teacher_gap, site_change, teacher_wish)"""
        a = self._for("teacher_gap", teachers=[teacher_id])[0]
        b = self._for("site_change", teachers=[teacher_id])[0]
        c = self._for("teacher_wish", teachers=[teacher_id])[0]
        return list(zip(a, b, c))

    def for_course(self, classes: list[SchoolClass], subjects: list[str], teachers: list[str]
                   ) -> list[tuple[float, float, float, float, int, bool]]:
        """je Variante: (position, core_late, double_split, spread, späteste Hauptfachstunde, Hauptfach hart)"""
        scope = dict(classes=classes, subjects=subjects, teachers=teachers)
        pos = self._for("position", **scope)[0]
        core_w, core_p, core_hard = self._for("core_late", **scope)
        dbl = self._for("doubles", **scope)[0]
        spr = self._for("spread", **scope)[0]
        latest = [int(p.get("core_latest_period", self.school.settings.core_latest_period)) for p in core_p]
        return list(zip(pos, core_w, dbl, spr, latest, core_hard))


def core_latest_for(school: School) -> Callable[[Any], int]:
    """Späteste Hauptfachstunde je Kurs (Ausnahmen ohne Wochenbezug eingerechnet) – für den Qualitätsbericht."""
    item = resolve(school.settings)["items"]["core_late"]
    base = int(item["params"].get("core_latest_period", school.settings.core_latest_period))
    classes = school.index("classes")
    ovs = [ov for ov in item["overrides"] if "core_latest_period" in ov["params"] and not ov["weeks"] and not ov["rhythm"]]

    def latest(course) -> int:
        out = base
        cl = [classes[c] for c in course.classes if c in classes]
        subj = [p.subject for p in course.parts]
        teach = [p.teacher for p in course.parts if p.teacher]
        for ov in ovs:
            if override_applies(ov, classes=cl, subjects=subj, teachers=teach):
                out = int(ov["params"]["core_latest_period"])
        return out

    return latest


# --------------------------------------------------------------------------------------------- Datenbezug & Wirkung
def context(school: School) -> dict:
    """Zahlen für Datenbezug und Wirkung: Standorte, Hauptfächer, Wünsche …"""
    sites = {s.id for s in school.sites} | {c.site for c in school.classes if c.site} | {r.site for r in school.rooms if r.site}
    return {
        "sites": len(sites) if len(sites) > 1 else 0,
        "core_subjects": sum(1 for s in school.subjects if s.core),
        "teacher_wishes": sum(1 for t in school.teachers if t.wishes),
        "classes": len(school.classes),
        "teachers": len(school.teachers),
        "courses": len(school.courses),
        "grades": sorted({int(c.grade) for c in school.classes}),
        "double_courses": sum(1 for c in school.courses if c.double),
        "classes_with_rules": sum(1 for c in school.classes if c.unavailable or c.school_days),
        "teachers_with_rules": sum(1 for t in school.teachers if t.unavailable or t.time_windows or t.work_grid),
        "room_subjects": sum(1 for s in school.subjects if s.room_type),
        "subject_limits": sum(1 for s in school.subjects if s.max_per_day and s.max_per_day != 1),
    }


def _affected(rule: RuleDef, item: dict, school: School, ctx: dict) -> tuple[int, str]:
    """Wie viele Einheiten der Baustein (mit seinem Grundgewicht) betrifft."""
    if rule.entity == "class":
        n = len(school.classes)
        return n, f"{n} Klasse{'n' if n != 1 else ''}"
    if rule.entity == "teacher":
        if rule.id == "teacher_wish":
            n = ctx["teacher_wishes"]
            return n, f"{n} Lehrkr{'äfte' if n != 1 else 'aft'} mit Wünschen"
        n = len(school.teachers)
        return n, f"{n} Lehrkr{'äfte' if n != 1 else 'aft'}"
    if rule.entity == "course":
        if rule.id == "core_late":
            core = {s.id for s in school.subjects if s.core}
            n = sum(1 for c in school.courses if c.parts and c.parts[0].subject in core)
            return n, f"{n} Hauptfach-Kurs{'e' if n != 1 else ''}"
        if rule.id == "doubles":
            prefer = bool(item["params"].get("prefer_doubles"))
            n = sum(1 for c in school.courses if c.double or (prefer and c.hours >= 2))
            return n, f"{n} Kurs{'e' if n != 1 else ''} mit Doppelstunden"
        if rule.id == "spread":
            n = sum(1 for c in school.courses if 0 < c.hours <= 3)
            return n, f"{n} Kurs{'e' if n != 1 else ''} mit bis zu 3 Wochenstunden"
        n = len(school.courses)
        return n, f"{n} Kurs{'e' if n != 1 else ''}"
    return 0, ""


def violations(school: School, report_stats: Optional[dict] = None) -> dict[str, Optional[float]]:
    """Aktuelle Verstöße je Baustein im gültigen Stundenplan (Durchschnitt je Schulwoche wie der Qualitätsbericht).

    Hohl-/Springstunden, Standortwechsel und späte Hauptfächer kommen aus ``report_stats`` (``validate_school``),
    die übrigen werden hier gezählt. ``None`` = für diesen Baustein nicht zählbar."""
    st = school.settings
    stats = report_stats or {}
    out: dict[str, Optional[float]] = {
        "class_gap": stats.get("class_gaps"), "teacher_gap": stats.get("teacher_gaps"),
        "site_change": stats.get("site_changes"), "core_late": stats.get("core_late"),
        "day_balance": None, "position": None, "auto_replan": None,
    }
    if not school.lessons:
        out.update({"late_start": 0, "spread": 0, "doubles": 0, "teacher_wish": 0})
        return out
    pw = wk.PlanWeeks(school)
    V = len(pw)
    courses = school.index("courses")
    classes = school.index("classes")
    # Belegung je Klasse/Variante/Tag und Fach-Tage je Kurs/Variante
    occ: dict[tuple[str, int, int], set[int]] = {}
    course_days: dict[tuple[str, int], set[int]] = {}
    wish_hits = 0.0
    split = 0
    prefer = bool(getattr(st, "prefer_doubles", False))
    teachers = school.index("teachers")
    for les in school.lessons:
        c = courses.get(les.course_id)
        if c is None:
            continue
        groups = pw.lesson_groups(les, c)
        for g in groups:
            for cid in c.classes:
                occ.setdefault((cid, g, les.day), set()).update(range(les.start, les.start + les.length))
            course_days.setdefault((c.id, g), set()).add(les.day)
            for p in c.parts:
                t = teachers.get(p.teacher) if p.teacher else None
                if t and t.wishes:
                    real = pw.real_week(g)
                    wish_hits += pw.weight[g] * sum(
                        1 for k in range(les.length) if any(r.matches(real, les.day, les.start + k) for r in t.wishes))
        if les.length == 1 and c.hours >= 2 and (c.double or (prefer and c.hours >= 2)):
            split += 1
    late = 0.0
    for (cid, g, d), periods in occ.items():
        cls = classes.get(cid)
        first_avail = 0
        if cls is not None:
            real = pw.real_week(g)
            while first_avail < st.periods and any(r.matches(real, d, first_avail) for r in cls.unavailable):
                first_avail += 1
        if min(periods) > first_avail:
            late += pw.weight[g]
    spread = 0.0
    for (cid, g), days in course_days.items():
        c = courses.get(cid)
        if c is None or c.hours > 3:
            continue
        ds = sorted(days)
        spread += pw.weight[g] * sum(1 for a, b in zip(ds, ds[1:]) if b == a + 1)
    out.update({"late_start": _num(late), "spread": _num(spread), "doubles": split, "teacher_wish": _num(wish_hits)})
    del V
    return out


def _num(x: float):
    return int(round(x)) if abs(x - round(x)) < 1e-6 else round(x, 1)


def _is_relevant(rule: RuleDef, ctx: dict) -> bool:
    return not rule.requires or bool(ctx.get(rule.requires))


def for_api(school: School, report_stats: Optional[dict] = None) -> dict:
    """Alles für die Oberfläche: Katalog, aktuelle Bausteine, Vorlagen, Datenbezug, Wirkung, Auswahllisten."""
    st = school.settings
    rules = resolve(st)
    ctx = context(school)
    viol = violations(school, report_stats)
    shown = shown_ids(rules["profile"], st) or set(_BASE_SHOW)
    tmpl_items = template_items(rules["profile"], st) or {}
    catalog = []
    for rule in RULES:
        item = rules["items"][rule.id]
        relevant = _is_relevant(rule, ctx)
        same_as_template = _same_item(item, tmpl_items.get(rule.id), rule) if tmpl_items else True
        default_visible = rule.id in shown and not rule.advanced
        n_aff, aff_text = _affected(rule, item, school, ctx)
        catalog.append({
            "id": rule.id, "group": rule.group, "title": rule.title, "text": rule.text, "control": rule.control,
            "weight_key": rule.weight_key, "base": rule.base, "scope": list(rule.scope), "report": rule.report,
            "hard": rule.hard, "hard_text": rule.hard_text, "advanced": rule.advanced, "entity": rule.entity,
            "params": [{"key": p.key, "label": p.label, "kind": p.kind, "min": p.min, "max": p.max,
                        "choices": [list(c) for c in p.choices], "help": p.help, "one_based": p.one_based,
                        "overridable": p.overridable} for p in rule.params],
            "relevant": relevant, "requires_text": "" if relevant else rule.requires_text,
            # sichtbar ohne „Erweitert“: Vorlage zeigt ihn, oder die Schule hat ihn verändert – und Datenbezug da
            "visible": relevant and (default_visible or not same_as_template),
            "weight": effective_weight(rule, item) if rule.control == "level" else None,
            "affects": n_aff, "affects_text": aff_text,
            "violations": viol.get(rule.id),
        })
    return {
        "profile": rules["profile"], "advanced": rules["advanced"], "items": rules["items"],
        "templates": [{"id": t.id, "name": t.name, "description": t.description, "builtin": True, "show": list(t.show),
                       "items": t.items} for t in TEMPLATES]
        + [{"id": t["id"], "name": t["name"], "description": t.get("description", ""), "builtin": False,
            "show": t.get("show") or [], "items": t.get("items") or {}} for t in rules["templates"]],
        "catalog": catalog,
        "groups": [{"id": g, "title": t, "text": x} for g, t, x in GROUPS],
        "levels": [{"id": lvl, "label": LEVEL_LABELS[lvl], "factor": LEVEL_FACTOR[lvl], "text": LEVEL_TEXT[lvl]}
                   for lvl in LEVELS],
        "hard_rules": [{"id": i, "title": t, "text": x, "link": link, "count": _hard_count(i, ctx)}
                       for i, t, x, link in HARD_RULES],
        "context": ctx,
        "options": {
            "grades": ctx["grades"],
            "classes": [{"id": c.id, "name": c.name, "grade": c.grade} for c in school.classes],
            "subjects": [{"id": s.id, "name": s.name, "core": s.core} for s in school.subjects],
            "teachers": [{"id": t.id, "name": t.name} for t in school.teachers],
            "periods": st.periods,
            "year_weeks": wk.MAX_WEEKS,
        },
        "numbers": {"weights": st.weights.to_dict(), "core_latest_period": st.core_latest_period,
                    "site_travel_periods": st.site_travel_periods, "prefer_doubles": st.prefer_doubles,
                    "double_alignment": st.double_alignment, "auto_replan": st.auto_replan},
    }


def _hard_count(hid: str, ctx: dict) -> Optional[int]:
    return {"class_rules": ctx["classes_with_rules"], "teacher_rules": ctx["teachers_with_rules"],
            "rooms": ctx["room_subjects"], "subject_per_day": ctx["subject_limits"]}.get(hid)


def _same_item(item: dict, tmpl: Optional[dict], rule: RuleDef) -> bool:
    if tmpl is None:
        return item["level"] == "wichtig" and item["weight"] is None and not item["overrides"]
    t = _norm_item(rule, tmpl, None, [])
    if item["level"] != t["level"] or (item["weight"] is not None):
        return False
    if len(item["overrides"]) != len(t["overrides"]):
        return False
    for k, v in t["params"].items():
        if item["params"].get(k) != v:
            return False
    return True


# --------------------------------------------------------------------------------------------- Klausur-Höchstzahlen
def exam_limits_for_class(school: School, cls: Any) -> dict:
    """Höchstzahlen Klassenarbeiten je Woche/Tag für eine Klasse: Klasse → Jahrgang → Schule.

    Liefert ``{"per_week", "per_day", "source_week", "source_day"}`` mit Quelle ``class|grade|school``."""
    st = school.settings
    if isinstance(cls, str):
        cls = school.index("classes").get(cls)
    out = {"per_week": int(st.max_exams_per_week), "per_day": int(st.max_exams_per_day),
           "source_week": "school", "source_day": "school"}
    if cls is None:
        return out
    grade = (getattr(st, "exam_limits_by_grade", None) or {}).get(str(int(cls.grade))) or {}
    for key, src in (("per_week", "source_week"), ("per_day", "source_day")):
        if grade.get(key) is not None:
            out[key], out[src] = int(grade[key]), "grade"
    own_week = getattr(cls, "max_exams_per_week", None)
    own_day = getattr(cls, "max_exams_per_day", None)
    if own_week is not None:
        out["per_week"], out["source_week"] = int(own_week), "class"
    if own_day is not None:
        out["per_day"], out["source_day"] = int(own_day), "class"
    return out


def exam_limits_text(limits: dict) -> str:
    """„max. 3 je Woche, 1 je Tag (Jahrgang)“ – für Klassenkopf und Klausurliste."""
    src = {"school": "Schule", "grade": "Jahrgang", "class": "Klasse"}
    a, b = src[limits["source_week"]], src[limits["source_day"]]
    source = a if a == b else f"Woche: {a}, Tag: {b}"
    return f"max. {limits['per_week']} je Woche, {limits['per_day']} je Tag ({source})"


def exam_limit_errors(limits_by_grade: Any) -> list[str]:
    """Prüft ``Settings.exam_limits_by_grade`` (``{"5": {"per_week": 2, "per_day": 1}}``)."""
    errs: list[str] = []
    if not isinstance(limits_by_grade, dict):
        return ["Vorgaben je Jahrgang müssen ein Objekt sein"]
    for g, v in limits_by_grade.items():
        try:
            grade = int(g)
        except (TypeError, ValueError):
            errs.append(f"Ungültiger Jahrgang „{g}“")
            continue
        if not 1 <= grade <= 14:
            errs.append(f"Jahrgang {grade} außerhalb von 1–14")
        if not isinstance(v, dict):
            errs.append(f"Jahrgang {grade}: Werte fehlen")
            continue
        for key, hi in (("per_week", 20), ("per_day", 5)):
            x = v.get(key)
            if x is not None and (not isinstance(x, int) or isinstance(x, bool) or not 0 <= x <= hi):
                errs.append(f"Jahrgang {grade}: „{key}“ muss zwischen 0 und {hi} liegen")
    return errs


def normalize_exam_limits(limits_by_grade: Any) -> dict:
    """Leere Jahrgangseinträge entfernen, Schlüssel als Zeichenkette."""
    out: dict[str, dict] = {}
    for g, v in (limits_by_grade or {}).items():
        if not isinstance(v, dict):
            continue
        clean = {k: int(v[k]) for k in ("per_week", "per_day") if v.get(k) is not None}
        if clean:
            out[str(int(g))] = clean
    return out


__all__ = [
    "LEVELS", "LEVEL_LABELS", "LEVEL_FACTOR", "RULES", "RULE_BY_ID", "TEMPLATES", "TEMPLATE_BY_ID", "GROUPS",
    "DEFAULT_PROFILE", "PlanWeights", "apply_to_settings", "sync_from_numbers", "derive_from_numbers", "resolve",
    "normalize", "rule_errors", "template_items", "week_specs", "core_latest_for", "context", "violations",
    "for_api", "weight_for", "level_for_weight", "exam_limits_for_class", "exam_limits_text", "exam_limit_errors",
    "normalize_exam_limits",
]
