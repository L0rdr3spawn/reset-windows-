"""Lehrer-Selbstverwaltung: Zeitfenster → Sperrzeiten, Profiländerungen und Konflikte (reine Logik).

Begriffe
--------
* **Zeitfenster** (``Teacher.time_windows``) beschreiben, *wann* eine Lehrkraft arbeiten kann::

      [{"days": [0, 1, 2, 3, 4], "start": "10:00", "end": "18:30", "weeks": []}]   # erst ab 10:00
      [{"days": [0, 1, 2, 3], "start": "16:00", "end": "21:00", "weeks": []}]      # nur Abendunterricht

  ``weeks`` = ausgewählte laufende Wochen (leer = jede Woche), alternativ ``rhythm`` = ``{"every", "from_week",
  "to_week"}`` (alle k Wochen ab Woche s, optional bis Woche e); nie beides in einem Fenster.
  Ist die Liste leer, gilt die Lehrkraft als ganztägig verfügbar.
  Sonst ist sie **nur** innerhalb der Fenster verfügbar – Tage ohne Fenster gelten als nicht verfügbar.
* Eine Unterrichtsstunde zählt als verfügbar, wenn sie **komplett** im Fenster liegt
  (Beginn laut ``settings.period_times``, Dauer ``settings.period_minutes``).
* Beim Übernehmen werden die Fenster in harte Sperrzeiten (``Teacher.unavailable``) umgerechnet. Diese Regeln tragen
  eine Notiz, die mit ``"Zeitfenster"`` beginnt; alte Zeitfenster-Regeln werden ersetzt, andere Sperrzeiten bleiben.
  Damit gelten die Fenster automatisch im Generator, in der Vertretungsplanung und beim Verschieben.

Neu (eine Bedienung für Arbeitszeiten, Sperrzeiten und Wünsche): Das Profil führt die **Sperrzeiten**
(``unavailable``, hart) und **Wünsche** (``wishes``, weich) als ``TimeRule``-Listen – je Regel Tage × Stunden,
Rhythmus (``rhythm`` / ``weeks``) und optional ``valid_from`` („gilt ab Datum“; mitten im Jahr). Zeitfenster und
Arbeitszeiten-Raster sind nur noch Altformate: Eingaben damit werden beim Validieren in Regeln umgerechnet (ohne
Verlust), ``teacher_profile()`` liefert sie nicht mehr (``time_windows`` = ``[]``, ``work_grid`` = ``{}``).

Profil = ``{"subjects", "preferred_classes", "max_hours", "unavailable", "wishes"}`` (Regeln als
``TimeRule``-Dicts), optional ``"new_subjects": [{"id", "name", "room_type"}]`` = von der Lehrkraft vorgeschlagene,
noch nicht vorhandene Fächer (werden erst bei der Genehmigung angelegt, ``apply_profile``). Alle Funktionen arbeiten auf dem Planungsmodell und verändern es nur, wo es ausdrücklich steht.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable, Optional

from . import weeks as wk
from .calendar_utils import as_date, plan_week
from .models import WEEKDAYS, School, Settings, Subject, Teacher, TimeRule, spec_active

WINDOW_NOTE = "Zeitfenster"
PROFILE_FIELDS = ("subjects", "preferred_classes", "max_hours", "unavailable", "time_windows", "work_grid", "wishes")
FIELD_LABELS = {
    "subjects": "Fächer (Lehrbefähigung)",
    "preferred_classes": "Klassen, die ich hauptsächlich unterrichte",
    "max_hours": "Deputat (Wochenstunden)",
    "unavailable": "Sperrzeiten (hart)",
    "time_windows": "Arbeitszeitfenster",
    "work_grid": "Arbeitszeiten",
    "wishes": "Wünsche (weich)",
    "new_subjects": "Neue Fächer (Vorschlag)",
}
MAX_NEW_SUBJECTS = 5
_SUBJECT_ID_BAD = re.compile(r"[/#?\\,;|\x00-\x1f]")
MAX_WINDOWS = 30
MAX_GRID_WEEKS = 52
GRID_NOTE = f"{WINDOW_NOTE}: Arbeitszeiten – gesperrt"
MAX_WISHES = 30
MAX_RULES = 60
MAX_HOURS = 40
MAX_NOTE = 200
_TIME = re.compile(r"^(\d{1,2}):(\d{2})$")
DAY_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


class ProfileError(ValueError):
    """Ungültige Profilangaben; ``errors`` enthält deutsche Meldungen."""

    def __init__(self, errors: Iterable[str]):
        self.errors = list(dict.fromkeys(errors))
        super().__init__("; ".join(self.errors))


# ----------------------------------------------------------------- Uhrzeiten
def to_minutes(value: Any, *, allow_24: bool = False) -> int:
    """``"HH:MM"`` → Minuten seit Mitternacht (``"24:00"`` nur mit ``allow_24``). ValueError bei Unsinn."""
    m = _TIME.match(str(value or "").strip())
    if not m:
        raise ValueError(f"Ungültige Uhrzeit „{value}“ (Format HH:MM)")
    h, mi = int(m.group(1)), int(m.group(2))
    if mi > 59 or h > 24 or (h == 24 and (mi or not allow_24)):
        raise ValueError(f"Ungültige Uhrzeit „{value}“")
    return h * 60 + mi


def fmt_minutes(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def period_minutes(settings: Settings) -> int:
    try:
        return max(1, int(getattr(settings, "period_minutes", 45) or 45))
    except (TypeError, ValueError):
        return 45


def period_spans(settings: Settings) -> list[Optional[tuple[int, int]]]:
    """``[(beginn, ende)]`` in Minuten je Stunde des Rasters (``None`` bei fehlender/ungültiger Zeit)."""
    length = period_minutes(settings)
    out: list[Optional[tuple[int, int]]] = []
    for i in range(max(0, settings.periods)):
        raw = settings.period_times[i] if i < len(settings.period_times) else ""
        try:
            start = to_minutes(raw)
        except ValueError:
            out.append(None)
            continue
        out.append((start, start + length))
    return out


def period_label(settings: Settings, p: int) -> str:
    t = settings.period_times[p] if 0 <= p < len(settings.period_times) else ""
    return f"{p + 1}. Std." + (f" ({t})" if t else "")


# ----------------------------------------------------------------- Zeitfenster
def _int_list(value: Any, what: str, errors: list[str]) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        errors.append(f"{what}: Liste erwartet")
        return []
    out = []
    for x in value:
        if isinstance(x, bool) or not isinstance(x, int):
            try:
                x = int(x)
            except (TypeError, ValueError):
                errors.append(f"{what}: ungültiger Wert „{x}“")
                continue
        out.append(x)
    return sorted(set(out))


def normalize_windows(windows: Any, settings: Settings) -> list[dict]:
    """Prüft und normalisiert Zeitfenster → ``[{"days","start","end","weeks"}]`` (ProfileError bei Fehlern)."""
    if windows is None:
        return []
    if not isinstance(windows, list):
        raise ProfileError(["Zeitfenster: Liste erwartet"])
    if len(windows) > MAX_WINDOWS:
        raise ProfileError([f"Zeitfenster: höchstens {MAX_WINDOWS} Einträge"])
    errors: list[str] = []
    out: list[dict] = []
    for i, w in enumerate(windows, 1):
        what = f"Zeitfenster {i}"
        if not isinstance(w, dict):
            errors.append(f"{what}: Objekt erwartet")
            continue
        unknown = set(w) - {"days", "start", "end", "weeks", "rhythm", "week_pattern"}
        if unknown:
            errors.append(f"{what}: unbekannte Felder {', '.join(sorted(unknown))}")
        w = dict(w)
        errors += [f"{what}: {e}" for e in wk.parse_weeks_input(w)]
        days = _int_list(w.get("days"), what, errors)
        weeks = _int_list(w.get("weeks"), what, errors)
        rhythm = w.get("rhythm") or None
        if not days:
            errors.append(f"{what}: mindestens ein Wochentag nötig")
        if any(not 0 <= d <= 6 for d in days):
            errors.append(f"{what}: Wochentag außerhalb der Woche")
        if rhythm is not None and weeks:
            errors.append(f"{what}: Bitte entweder Wochen oder einen Rhythmus angeben.")
        elif rhythm is not None:
            errors += [f"{what}: {e}" for e in wk.rhythm_errors(rhythm)]
        else:
            errors += [f"{what}: {e}" for e in wk.errors(weeks)]
        try:
            start = to_minutes(w.get("start"))
            end = to_minutes(w.get("end"), allow_24=True)
        except ValueError as exc:
            errors.append(f"{what}: {exc}")
            continue
        if end <= start:
            errors.append(f"{what}: Ende ({fmt_minutes(end)}) muss nach dem Beginn ({fmt_minutes(start)}) liegen")
            continue
        item = {"days": days, "start": fmt_minutes(start), "end": fmt_minutes(end), "weeks": wk.normalize(weeks)}
        if rhythm is not None:
            item["rhythm"] = wk.normalize_rhythm(rhythm)
        out.append(item)
    if errors:
        raise ProfileError(errors)
    return out


def window_applies(window: dict, week: Optional[int], day: int) -> bool:
    """Gilt das Fenster am (laufende Woche, Tag)? Unbekannte Woche (``None``) = ja."""
    if day not in (window.get("days") or []):
        return False
    return spec_active(window.get("weeks"), window.get("rhythm"), week)


def available_periods(windows: list[dict], settings: Settings, week: Optional[int], day: int,
                      spans: Optional[list] = None) -> set[int]:
    """Stunden, die am (laufende Woche, Tag) komplett in einem Zeitfenster liegen (leere Fensterliste = alle)."""
    if not windows:
        return set(range(settings.periods))
    spans = spans if spans is not None else period_spans(settings)
    out: set[int] = set()
    for w in windows:
        if not window_applies(w, week, day):
            continue
        try:
            start, end = to_minutes(w["start"]), to_minutes(w["end"], allow_24=True)
        except (KeyError, ValueError):
            continue
        for p, span in enumerate(spans):
            if span and span[0] >= start and span[1] <= end:
                out.add(p)
    return out


def _week_classes(windows: list[dict]) -> list[list[int]]:
    """Laufende Wochen 1 … 53, gruppiert nach den Fenstern, die in ihnen gelten (jede Gruppe: gleiche Verfügbarkeit)."""
    groups: dict[tuple, list[int]] = {}
    for L in range(1, wk.MAX_WEEKS + 1):
        key = tuple(spec_active(w.get("weeks"), w.get("rhythm"), L) for w in windows)
        groups.setdefault(key, []).append(L)
    return list(groups.values())


def availability(windows: list[dict], settings: Settings, days: Optional[Iterable[int]] = None) -> list[dict]:
    """Vorschau je Tag und Gruppe gleicher Wochen: ``[{"weeks","rhythm","weeks_text","day","day_name",
    "periods"}]`` (``weeks``/``rhythm`` = laufende Wochen der Gruppe, beide leer = jede Woche)."""
    from .calendar_utils import default_days
    spans = period_spans(settings)
    classes = _week_classes(windows or [])
    lab = wk.WeekLabels(settings)
    out = []
    for d in sorted(set(days) if days is not None else set(default_days(settings))):
        groups: dict[tuple[int, ...], list[int]] = {}
        for ls in classes:
            groups.setdefault(tuple(sorted(available_periods(windows, settings, ls[0], d, spans))), []).extend(ls)
        for periods, ws in groups.items():
            weeks, rhythm = wk.spec_from_weeks(ws)
            out.append({"weeks": weeks, "rhythm": rhythm, "weeks_text": wk.describe_spec(weeks, rhythm, lab),
                        "day": d, "day_name": WEEKDAYS[d], "periods": list(periods)})
    return out


def availability_from_rules(rules: Iterable[TimeRule], settings: Settings,
                            days: Optional[Iterable[int]] = None) -> list[dict]:
    """Wie ``availability``, aber aus harten Sperrzeiten: frei sind die Stunden, die keine Regel sperrt."""
    from .calendar_utils import default_days
    rules = list(rules)
    P = settings.periods
    groups_w: dict[tuple, list[int]] = {}
    for L in range(1, wk.MAX_WEEKS + 1):
        key = tuple((spec_active(r.weeks, r.rhythm, L) and L >= (r.valid_week or 0)) for r in rules)
        groups_w.setdefault(key, []).append(L)
    lab = wk.WeekLabels(settings)
    out = []
    for d in sorted(set(days) if days is not None else set(default_days(settings))):
        groups: dict[tuple[int, ...], list[int]] = {}
        for ls in groups_w.values():
            free = tuple(p for p in range(P) if not any(r.matches(ls[0], d, p) for r in rules))
            groups.setdefault(free, []).extend(ls)
        for periods, ws in groups.items():
            weeks, rhythm = wk.spec_from_weeks(sorted(ws))
            out.append({"weeks": weeks, "rhythm": rhythm, "weeks_text": wk.describe_spec(weeks, rhythm, lab),
                        "day": d, "day_name": WEEKDAYS[d], "periods": list(periods)})
    return out


def _ranges_text(windows: list[dict], week: Optional[int], day: int) -> str:
    ranges = sorted({(w["start"], w["end"]) for w in windows if window_applies(w, week, day)})
    return ", ".join(f"{a}–{b}" for a, b in ranges)


def windows_to_rules(windows: list[dict], settings: Settings) -> list[TimeRule]:
    """Rechnet Zeitfenster in harte Sperrzeiten um (kompakt: gleiche Sperren werden über Tage/Wochen gebündelt).

    Alle 7 Wochentage zählen: ein Tag ohne Fenster ist gesperrt. Wochen mit gleicher Fensterlage bilden eine Gruppe;
    gilt eine Sperre nur in einigen Wochen, bekommt die Regel diese Wochen (Liste oder Rhythmus)."""
    if not windows:
        return []
    D, P = 7, settings.periods
    spans = period_spans(settings)
    classes = _week_classes(windows)
    blocked: dict[tuple[int, int], tuple[int, ...]] = {}
    texts: dict[tuple[int, int], str] = {}
    for g, ls in enumerate(classes):
        for d in range(D):
            avail = available_periods(windows, settings, ls[0], d, spans)
            blocked[(g, d)] = tuple(p for p in range(P) if p not in avail)
            texts[(g, d)] = _ranges_text(windows, ls[0], d)
    groups: dict[tuple[tuple[int, ...], tuple[int, ...], str], list[int]] = defaultdict(list)
    spec_of_weeks: dict[tuple[int, ...], tuple[list[int], Optional[dict]]] = {}
    for d in range(D):
        per_class = [(blocked[(g, d)], texts[(g, d)]) for g in range(len(classes))]
        if all(x == per_class[0] for x in per_class):
            if per_class[0][0]:
                groups[((), per_class[0][0], per_class[0][1])].append(d)
            continue
        by_block: dict[tuple[tuple[int, ...], str], list[int]] = defaultdict(list)
        for g, (b, text) in enumerate(per_class):
            if b:
                by_block[(b, text)].extend(classes[g])
        for (b, text), weeks in by_block.items():
            key = tuple(sorted(weeks))
            spec_of_weeks[key] = wk.spec_from_weeks(key)
            groups[(key, b, text)].append(d)
    rules: list[TimeRule] = []
    for (weeks, periods, text), days in sorted(groups.items(), key=lambda kv: (kv[1][0], kv[0][0], kv[0][1])):
        full = len(periods) >= P
        note = f"{WINDOW_NOTE}: nicht verfügbar" if full or not text else f"{WINDOW_NOTE}: verfügbar {text}"
        wlist, rhythm = spec_of_weeks.get(weeks, ([], None))
        rules.append(TimeRule(weeks=wlist, days=sorted(days), periods=[] if full else list(periods), note=note,
                              rhythm=rhythm))
    return rules


# ----------------------------------------------------------------- Arbeitszeiten-Raster
def normalize_work_grid(grid: Any, settings: Settings) -> dict:
    """Prüft das Arbeitszeiten-Raster → ``{"weeks": N, "blocked": [{"week","day","periods"}]}`` bzw. ``{}`` (keine
    Einschränkung). ProfileError bei Fehlern."""
    if not grid:
        return {}
    if not isinstance(grid, dict) or set(grid) - {"weeks", "blocked"}:
        raise ProfileError(["Arbeitszeiten: ungültiges Format"])
    errors: list[str] = []
    try:
        n = int(grid.get("weeks") or 1)
    except (TypeError, ValueError):
        n = 0
    if not 1 <= n <= MAX_GRID_WEEKS:
        raise ProfileError([f"Arbeitszeiten: Rhythmus von 1 bis {MAX_GRID_WEEKS} Wochen"])
    raw = grid.get("blocked") or []
    if not isinstance(raw, list) or len(raw) > n * 7:
        raise ProfileError(["Arbeitszeiten: ungültige Sperrliste"])
    cells: dict[tuple[int, int], set[int]] = defaultdict(set)
    for item in raw:
        if not isinstance(item, dict):
            errors.append("Arbeitszeiten: ungültiger Eintrag")
            continue
        try:
            k, d = int(item.get("week") or 0), int(item.get("day"))
        except (TypeError, ValueError):
            errors.append("Arbeitszeiten: ungültiger Eintrag")
            continue
        periods = _int_list(item.get("periods"), "Arbeitszeiten", errors)
        if not 0 <= k < n:
            errors.append(f"Arbeitszeiten: Woche {k + 1} liegt außerhalb des Rasters ({n} Wochen)")
        elif not 0 <= d <= 6:
            errors.append("Arbeitszeiten: Wochentag außerhalb der Woche")
        elif any(not 0 <= p < settings.periods for p in periods):
            errors.append(f"Arbeitszeiten: Stunde außerhalb des Rasters (1–{settings.periods})")
        else:
            cells[(k, d)].update(periods)
    if errors:
        raise ProfileError(errors)
    blocked = [{"week": k, "day": d, "periods": sorted(ps)} for (k, d), ps in sorted(cells.items()) if ps]
    if not blocked and n == 1:
        return {}
    return {"weeks": n, "blocked": blocked}


def grid_to_rules(grid: Optional[dict], settings: Settings) -> list[TimeRule]:
    """Raster → harte Sperrzeiten: in allen Rasterwochen gleich gesperrte Stunden ohne Rhythmus, sonst je Rasterwoche
    ein Rhythmus „alle N Wochen ab Woche k+1“. Gleiche Sperren an mehreren Tagen werden gebündelt."""
    if not grid or not grid.get("blocked"):
        return []
    n = max(1, int(grid.get("weeks") or 1))
    P = settings.periods
    weeks_of: dict[tuple[int, tuple[int, ...]], set[int]] = defaultdict(set)
    for b in grid["blocked"]:
        weeks_of[(b["day"], tuple(b["periods"]))].add(b["week"])
    by_rule: dict[tuple[Optional[int], tuple[int, ...]], list[int]] = defaultdict(list)
    for (d, periods), ks in weeks_of.items():
        for k in ([None] if len(ks) >= n else sorted(ks)):
            by_rule[(k, periods)].append(d)
    rules = []
    for (k, periods), days in sorted(by_rule.items(), key=lambda kv: (-1 if kv[0][0] is None else kv[0][0], kv[0][1])):
        rhythm = None if k is None else {"every": n, "from_week": k + 1, "to_week": 0}
        rules.append(TimeRule(days=sorted(days), periods=[] if len(periods) >= P else list(periods), note=GRID_NOTE,
                              rhythm=rhythm))
    return rules


def describe_grid(grid: Optional[dict]) -> str:
    if not grid or not grid.get("blocked"):
        return "keine Einschränkung"
    n = int(grid.get("weeks") or 1)
    count = sum(len(b["periods"]) for b in grid["blocked"])
    rhythm = "jede Woche" if n == 1 else f"Raster über {n} Wochen"
    return f"{rhythm}, {count} Stunde{'' if count == 1 else 'n'} gesperrt"


def is_window_rule(rule: TimeRule) -> bool:
    return (rule.note or "").startswith(WINDOW_NOTE)


def strip_window_rules(rules: Iterable[TimeRule]) -> list[TimeRule]:
    """Sperrzeiten ohne die aus Zeitfenstern erzeugten Regeln."""
    return [r for r in rules if not is_window_rule(r)]


def detach_note(note: str) -> str:
    """Notiz einer aus Zeitfenstern/Raster erzeugten Regel → normale Notiz („Zeitfenster: verfügbar 10:00–18:30“ →
    „Arbeitszeit: verfügbar 10:00–18:30“), damit die Regel eine ganz normale, frei bearbeitbare Sperrzeit wird."""
    text = (note or "").strip()
    if not text.startswith(WINDOW_NOTE):
        return text
    rest = text[len(WINDOW_NOTE):].lstrip(": ").replace("Arbeitszeiten – ", "")
    return f"Arbeitszeit: {rest}".strip(": ")


def detached(rules: Iterable[TimeRule]) -> list[TimeRule]:
    """Kopien der Regeln, bei denen Zeitfenster-Notizen durch normale ersetzt sind."""
    out = []
    for r in rules:
        c = TimeRule.from_dict(r.to_dict())
        c.note = detach_note(c.note)
        out.append(c)
    return out


def legacy_rules(windows: Any, grid: Any, settings: Settings) -> list[TimeRule]:
    """Altformate (Zeitfenster, Raster) als normale Sperrzeiten (ohne reservierte Notiz)."""
    return detached(windows_to_rules(windows or [], settings) + grid_to_rules(grid or {}, settings))


def valid_week_of(valid_from: str, settings: Settings) -> int:
    """Laufende Woche, ab der eine Regel mit ``valid_from`` gilt (0 = von Schuljahresbeginn an / ungültig)."""
    if not valid_from:
        return 0
    try:
        no = plan_week(settings, as_date(valid_from))
    except (TypeError, ValueError):
        return 0
    return max(0, int(no))


def stamp_valid_weeks(rules: Iterable[TimeRule], settings: Settings) -> None:
    """Berechnet ``valid_week`` aller Regeln aus ``valid_from`` (nach Änderung von Schuljahr/Wochenzählung neu)."""
    for r in rules:
        r.valid_week = valid_week_of(getattr(r, "valid_from", "") or "", settings)


def rules_from(raw: Iterable[Any], settings: Settings) -> list[TimeRule]:
    """Regel-Dicts → ``TimeRule`` mit berechneter Gültigkeitswoche."""
    rules = [r if isinstance(r, TimeRule) else TimeRule.from_dict(r) for r in raw or []]
    stamp_valid_weeks(rules, settings)
    return rules


def apply_windows(teacher: Teacher, settings: Settings) -> None:
    """Ersetzt die Zeitfenster-Sperrzeiten der Lehrkraft (andere Sperrzeiten bleiben unangetastet) und berechnet die
    Gültigkeitswochen aller Regeln (``valid_from``)."""
    teacher.unavailable = (strip_window_rules(teacher.unavailable) + windows_to_rules(teacher.time_windows or [], settings)
                           + grid_to_rules(getattr(teacher, "work_grid", None) or {}, settings))
    stamp_valid_weeks(list(teacher.unavailable) + list(teacher.wishes), settings)


def refresh_all_windows(school: School) -> int:
    """Nach Änderungen am Zeitraster: Zeitfenster-Sperrzeiten aller Lehrkräfte neu berechnen. Gibt die Anzahl
    geänderter Lehrkräfte zurück."""
    changed = 0
    for t in school.teachers:
        if (not t.time_windows and not t.work_grid and not any(is_window_rule(r) for r in t.unavailable)
                and not any(r.valid_from or r.valid_week for r in list(t.unavailable) + list(t.wishes))):
            continue
        before = [r.to_dict() for r in t.unavailable]
        try:
            t.time_windows = normalize_windows(t.time_windows, school.settings)
        except ProfileError:
            # Fenster passen nicht mehr zum Raster (z. B. weniger Schultage): nur gültige Tage behalten
            t.time_windows = _salvage_windows(t.time_windows, school.settings)
        try:
            t.work_grid = normalize_work_grid(t.work_grid, school.settings)
        except ProfileError:
            # Raster passt nicht mehr (z. B. weniger Stunden): nur vorhandene Stunden behalten
            g = t.work_grid if isinstance(t.work_grid, dict) else {}
            keep = [{**b, "periods": [p for p in b.get("periods") or [] if 0 <= p < school.settings.periods]}
                    for b in g.get("blocked") or [] if isinstance(b, dict) and 0 <= int(b.get("day") or 0) <= 6]
            try:
                t.work_grid = normalize_work_grid({"weeks": g.get("weeks") or 1, "blocked": keep}, school.settings)
            except ProfileError:
                t.work_grid = {}
        apply_windows(t, school.settings)
        if [r.to_dict() for r in t.unavailable] != before:
            changed += 1
    return changed


def _salvage_windows(windows: Any, settings: Settings) -> list[dict]:
    out = []
    for w in windows or []:
        if not isinstance(w, dict):
            continue
        days = [d for d in w.get("days") or [] if isinstance(d, int) and 0 <= d <= 6]
        weeks = [x for x in w.get("weeks") or [] if isinstance(x, int) and 1 <= x <= wk.MAX_WEEKS]
        if not days:
            continue
        item = {"days": days, "start": w.get("start"), "end": w.get("end"), "weeks": weeks}
        if w.get("rhythm"):
            item = {**item, "weeks": [], "rhythm": w["rhythm"]}
        try:
            out += normalize_windows([item], settings)
        except ProfileError:
            continue
    return out


def describe_windows(windows: list[dict], settings: Settings) -> str:
    """Kurzbeschreibung, z. B. „Mo–Fr 10:00–18:30; Woche 2: Fr 08:00–12:00“."""
    if not windows:
        return "ganztägig verfügbar"
    parts = []
    lab = wk.WeekLabels(settings)
    for w in windows:
        days = w.get("days") or []
        if days and days == list(range(days[0], days[-1] + 1)) and len(days) > 2:
            dtext = f"{DAY_SHORT[days[0]]}–{DAY_SHORT[days[-1]]}"
        else:
            dtext = ", ".join(DAY_SHORT[d] if d < len(DAY_SHORT) else str(d + 1) for d in days)
        weeks = w.get("weeks") or []
        if w.get("rhythm"):
            wtext = wk.describe_rhythm(w["rhythm"], lab) + ": "
        else:
            wtext = f"{wk.describe(weeks, lab)}: " if weeks else ""
        parts.append(f"{wtext}{dtext} {w.get('start')}–{w.get('end')}")
    return "; ".join(parts)


# ----------------------------------------------------------------- Profil
def teacher_profile(teacher: Teacher) -> dict:
    """Aktuelle Selbstauskunft einer Lehrkraft (Profilfelder als JSON-Dict).

    Zeitfenster und Raster erscheinen nur als normale Sperrzeiten (``unavailable``); ``time_windows``/``work_grid``
    sind immer leer. So bedient die Oberfläche eine einzige Liste, und gespeichert wird verlustfrei."""
    rules = detached(teacher.unavailable)
    return {"subjects": list(teacher.subjects), "preferred_classes": list(teacher.preferred_classes),
            "max_hours": int(teacher.max_hours), "unavailable": [_rule_out(r) for r in rules],
            "time_windows": [], "work_grid": {}, "wishes": [_rule_out(r) for r in teacher.wishes]}


def _rule_out(rule: TimeRule) -> dict:
    """Regel für Profil/Antrag (ohne die abgeleitete ``valid_week``)."""
    d = rule.to_dict()
    d.pop("valid_week", None)
    if not d.get("valid_from"):
        d.pop("valid_from", None)
    return d


def describe_availability(profile: dict) -> str:
    """Kurztext für Kopfzeilen: „3 Sperrzeiten, 1 Wunsch“."""
    n, w = len(profile.get("unavailable") or []), len(profile.get("wishes") or [])
    legacy = describe_windows(profile.get("time_windows") or [], Settings()) if profile.get("time_windows") else ""
    if legacy:
        return legacy
    if not n and not w:
        return "keine Einschränkung"
    parts = []
    if n:
        parts.append(f"{n} Sperrzeit" + ("" if n == 1 else "en"))
    if w:
        parts.append(f"{w} Wunsch" + ("" if w == 1 else "e"))
    return ", ".join(parts)


def describe_rule(rule: TimeRule) -> str:
    """„jede 2. Woche ab Woche 3 · Mi · 1.–2. Std. (ab 15.10.2026)“"""
    parts = []
    spec = wk.describe_spec(rule.weeks, rule.rhythm) if (rule.weeks or rule.rhythm) else ""
    if spec and spec != "jede Woche":
        parts.append(spec)
    days = sorted(rule.days)
    if not days:
        parts.append("jeder Tag")
    elif len(days) > 2 and days == list(range(days[0], days[-1] + 1)):
        parts.append(f"{DAY_SHORT[days[0]]}–{DAY_SHORT[days[-1]]}")
    else:
        parts.append(", ".join(DAY_SHORT[d] if d < len(DAY_SHORT) else str(d + 1) for d in days))
    if rule.periods:
        ps = sorted(rule.periods)
        runs, i = [], 0
        while i < len(ps):
            j = i
            while j + 1 < len(ps) and ps[j + 1] == ps[j] + 1:
                j += 1
            runs.append(f"{ps[i] + 1}." if i == j else f"{ps[i] + 1}.–{ps[j] + 1}.")
            i = j + 1
        parts.append(", ".join(runs) + " Std.")
    else:
        parts.append("ganztägig")
    text = " · ".join(parts)
    if rule.valid_from:
        try:
            text += f" (ab {as_date(rule.valid_from).strftime('%d.%m.%Y')})"
        except (TypeError, ValueError):
            pass
    return text


def _check_date(value: Any, what: str, errors: list[str]) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return as_date(text).isoformat()
    except (TypeError, ValueError):
        errors.append(f"{what}: „Gilt ab“ bitte als Datum angeben")
        return ""


def parse_rules(raw: Any, what: str, limit: int, errors: list[str], *, detach: bool = False) -> list[TimeRule]:
    """Regel-Dicts (Sperrzeiten/Wünsche) → ``TimeRule`` prüfen; Fehler landen in ``errors``. Mit ``detach`` verlieren
    Regeln mit reservierter Zeitfenster-Notiz diese Kennzeichnung (sie sind dann normale, bearbeitbare Regeln)."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append(f"{what}: Liste erwartet")
        return []
    if len(raw) > limit:
        errors.append(f"Höchstens {limit} {what}-Regeln")
        return []
    out: list[TimeRule] = []
    for i, r in enumerate(raw, 1):
        if isinstance(r, TimeRule):
            r = r.to_dict()
        if not isinstance(r, dict) or set(r) - {"weeks", "days", "periods", "note", "rhythm", "week_pattern",
                                                  "valid_from", "valid_week"}:
            errors.append(f"{what} {i}: ungültiges Format")
            continue
        e: list[str] = []
        r = dict(r)
        e += [f"{what} {i}: {x}" for x in wk.parse_weeks_input(r)]
        rhythm = r.get("rhythm") or None
        if rhythm is not None and not wk.rhythm_errors(rhythm):
            rhythm = wk.normalize_rhythm(rhythm)
        note = str(r.get("note") or "").strip()
        if detach:
            note = detach_note(note)
        out.append(TimeRule(weeks=_int_list(r.get("weeks"), f"{what} {i}", e),
                            days=_int_list(r.get("days"), f"{what} {i}", e),
                            periods=_int_list(r.get("periods"), f"{what} {i}", e),
                            note=note, rhythm=rhythm, valid_from=_check_date(r.get("valid_from"), f"{what} {i}", e)))
        errors += e
    return out


def _rule_errors(rules: list[TimeRule], settings: Settings, what: str) -> list[str]:
    out = []
    for r in rules:
        out += wk.rule_errors(r, settings.periods, what)
        if len(r.note or "") > MAX_NOTE:
            out.append(f"{what}: Notiz zu lang (max. {MAX_NOTE} Zeichen)")
        if is_window_rule(r):
            out.append(f"{what}: Notizen dürfen nicht mit „{WINDOW_NOTE}“ beginnen (reserviert)")
    return out


def validate_profile(school: School, data: dict, current: Optional[dict] = None) -> dict:
    """Prüft eine Profiländerung und liefert das vollständige, normalisierte Profil.

    Fehlende Felder werden aus ``current`` übernommen. ProfileError mit allen Fehlermeldungen.
    """
    current = current or {}
    errors: list[str] = []
    st = school.settings
    out: dict = {}
    subjects_known = school.index("subjects")
    classes_known = school.index("classes")

    def pick(key: str, default: Any) -> Any:
        v = data.get(key)
        return current.get(key, default) if v is None else v

    subjects = pick("subjects", [])
    if not isinstance(subjects, list) or not all(isinstance(s, str) for s in subjects):
        errors.append("Fächer: Liste von Fach-Kürzeln erwartet")
        subjects = []
    subjects = list(dict.fromkeys(s.strip() for s in subjects if s.strip()))
    new_subjects = _new_subjects(data.get("new_subjects"), subjects_known, errors)
    new_ids = [n["id"] for n in new_subjects]
    subjects += [i for i in new_ids if i not in subjects]
    unknown = [s for s in subjects if s not in subjects_known and s not in new_ids]
    if unknown:
        errors.append(f"Unbekannte Fächer: {', '.join(unknown)}")
    if len(subjects) > 20:
        errors.append("Höchstens 20 Fächer")
    out["subjects"] = subjects
    if new_subjects:
        out["new_subjects"] = new_subjects

    classes = pick("preferred_classes", [])
    if not isinstance(classes, list) or not all(isinstance(c, str) for c in classes):
        errors.append("Wunschklassen: Liste von Klassen-Kürzeln erwartet")
        classes = []
    classes = list(dict.fromkeys(c.strip() for c in classes if c.strip()))
    unknown = [c for c in classes if c not in classes_known]
    if unknown:
        errors.append(f"Unbekannte Klassen: {', '.join(unknown)}")
    if len(classes) > 30:
        errors.append("Höchstens 30 Wunschklassen")
    out["preferred_classes"] = classes

    hours = pick("max_hours", 25)
    try:
        if isinstance(hours, bool):
            raise ValueError
        hours = int(hours)
        if not 0 <= hours <= MAX_HOURS:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(f"Deputat muss eine ganze Zahl zwischen 0 und {MAX_HOURS} sein")
        hours = 0
    out["max_hours"] = hours

    try:
        out["time_windows"] = normalize_windows(data.get("time_windows") or [], st)
    except ProfileError as exc:
        errors += exc.errors
        out["time_windows"] = []
    try:
        out["work_grid"] = normalize_work_grid(data.get("work_grid") or {}, st)
    except ProfileError as exc:
        errors += exc.errors
        out["work_grid"] = {}

    wishes = parse_rules(pick("wishes", []), "Wunsch", MAX_WISHES, errors)
    errors += _rule_errors(wishes, st, "Wunsch")

    # Sperrzeiten: neue Liste (oder bisherige); Altformate (Zeitfenster, Raster) werden zu Regeln
    legacy_sent = data.get("time_windows") is not None or data.get("work_grid") is not None
    base_raw = data.get("unavailable")
    if base_raw is None:
        cur = [TimeRule.from_dict(x) if isinstance(x, dict) else x for x in current.get("unavailable") or []]
        # alter Client mit Zeitfenstern/Raster: deren (umbenannte) Regeln werden durch die neuen ersetzt
        base_raw = [r.to_dict() for r in cur if not (legacy_sent and (r.note or "").startswith("Arbeitszeit:"))]
    unavailable = parse_rules(base_raw, "Sperrzeit", MAX_RULES, errors, detach=True)
    errors += _rule_errors(unavailable, st, "Sperrzeit")
    if legacy_sent:
        unavailable += legacy_rules(out["time_windows"], out["work_grid"], st)
    out["time_windows"], out["work_grid"] = [], {}
    stamp_valid_weeks(unavailable + wishes, st)
    out["unavailable"] = [_rule_out(r) for r in unavailable]
    out["wishes"] = [_rule_out(w) for w in wishes]
    if errors:
        raise ProfileError(errors)
    return out


def _new_subjects(raw: Any, known: dict, errors: list[str]) -> list[dict]:
    """Vorgeschlagene neue Fächer prüfen/normalisieren; bereits vorhandene Kürzel fallen heraus (gelten als
    normale Fächer)."""
    if raw in (None, []):
        return []
    if not isinstance(raw, list):
        errors.append("Neue Fächer: Liste erwartet")
        return []
    if len(raw) > MAX_NEW_SUBJECTS:
        errors.append(f"Höchstens {MAX_NEW_SUBJECTS} neue Fächer je Antrag")
    out: list[dict] = []
    for item in raw[:MAX_NEW_SUBJECTS]:
        if not isinstance(item, dict):
            errors.append("Neue Fächer: ungültiges Format")
            continue
        sid = " ".join(str(item.get("id") or "").split())
        name = " ".join(str(item.get("name") or "").split())
        room_type = " ".join(str(item.get("room_type") or "").split()) or None
        if not sid or len(sid) > 20 or _SUBJECT_ID_BAD.search(sid):
            errors.append(f"Neues Fach: Kürzel „{sid}“ ungültig (1–20 Zeichen, keine / # ? \\ , ; |)")
            continue
        if not name or len(name) > 80:
            errors.append(f"Neues Fach {sid}: Name fehlt oder ist zu lang (max. 80 Zeichen)")
            continue
        if room_type and len(room_type) > 40:
            errors.append(f"Neues Fach {sid}: Fachraum-Typ zu lang")
            continue
        if sid in known or any(o["id"] == sid for o in out):
            continue
        out.append({"id": sid, "name": name, "room_type": room_type})
    return out


def apply_profile(school: School, teacher_id: str, profile: dict) -> Teacher:
    """Übernimmt ein (validiertes) Profil in ``school`` (Zeitfenster → Sperrzeiten). KeyError, wenn unbekannt.
    Vorgeschlagene neue Fächer (``new_subjects``) werden dabei angelegt, sofern es das Kürzel noch nicht gibt."""
    teacher = school.index("teachers").get(teacher_id)
    if teacher is None:
        raise KeyError(f"Lehrkraft {teacher_id} existiert nicht")
    known = {s.id for s in school.subjects}
    for ns in profile.get("new_subjects") or []:
        if ns.get("id") and ns["id"] not in known:
            school.subjects.append(Subject(ns["id"], ns.get("name") or ns["id"], ns.get("room_type") or None))
            known.add(ns["id"])
    teacher.subjects = list(profile.get("subjects", teacher.subjects))
    teacher.preferred_classes = list(profile.get("preferred_classes", teacher.preferred_classes))
    teacher.max_hours = int(profile.get("max_hours", teacher.max_hours))
    teacher.time_windows = [dict(w) for w in profile.get("time_windows", teacher.time_windows) or []]
    teacher.work_grid = dict(profile.get("work_grid", teacher.work_grid) or {})
    teacher.wishes = [r if isinstance(r, TimeRule) else TimeRule.from_dict(r)
                      for r in profile.get("wishes", [w.to_dict() for w in teacher.wishes])]
    if "unavailable" in profile:
        # die Liste enthält bereits alles (auch frühere Zeitfenster/Raster-Regeln als normale Sperrzeiten)
        teacher.unavailable = [r if isinstance(r, TimeRule) else TimeRule.from_dict(r) for r in profile["unavailable"]]
        if "time_windows" not in profile:
            teacher.time_windows = []
        if "work_grid" not in profile:
            teacher.work_grid = {}
    apply_windows(teacher, school.settings)
    return teacher


def diff_profile(before: Optional[dict], after: dict, settings: Optional[Settings] = None) -> list[dict]:
    """Vergleich alt/neu: ``[{"field","label","old","new","old_text","new_text"}]`` (nur geänderte Felder)."""
    before = before or {}
    out = []
    for key in PROFILE_FIELDS:
        old, new = before.get(key), after.get(key)
        if old == new or (key == "work_grid" and not old and not new):
            continue
        if key == "unavailable" and "unavailable" not in after:
            continue
        if key in ("time_windows", "work_grid") and "unavailable" in after and not new:
            continue        # Altformat ist in den Sperrzeiten aufgegangen
        out.append({"field": key, "label": FIELD_LABELS[key], "old": old, "new": new,
                    "old_text": _field_text(key, old, settings), "new_text": _field_text(key, new, settings)})
    if after.get("new_subjects"):
        new = after["new_subjects"]
        out.append({"field": "new_subjects", "label": FIELD_LABELS["new_subjects"], "old": None, "new": new,
                    "old_text": "–", "new_text": ", ".join(
                        f"{n['id']} – {n['name']}" + (f" ({n['room_type']})" if n.get("room_type") else "")
                        for n in new)})
    return out


def _field_text(key: str, value: Any, settings: Optional[Settings]) -> str:
    if value is None:
        return "–"
    if key in ("subjects", "preferred_classes"):
        return ", ".join(value) or "–"
    if key == "max_hours":
        return f"{value} Std."
    if key == "time_windows":
        return describe_windows(value, settings or Settings())
    if key == "work_grid":
        return describe_grid(value)
    if key in ("wishes", "unavailable"):
        if not value:
            return "keine"
        rules = [TimeRule.from_dict(x) if isinstance(x, dict) else x for x in value]
        return "; ".join(describe_rule(r) for r in rules)
    return str(value)


# ----------------------------------------------------------------- Unterricht & Konflikte
def teacher_courses(school: School, teacher_id: str) -> list[tuple[Any, list[int]]]:
    """``[(Kurs, [Teil-Indizes der Lehrkraft])]``."""
    out = []
    for c in school.courses:
        parts = [i for i, p in enumerate(c.parts) if p.teacher == teacher_id]
        if parts:
            out.append((c, parts))
    return out


def current_load(school: School, teacher_id: str) -> dict:
    """Ist-Deputat aus den zugewiesenen Kursteilen (wie ``timetable.validate_school``)."""
    courses = []
    hours = 0
    for c, parts in teacher_courses(school, teacher_id):
        hours += c.hours
        courses.append({"id": c.id, "label": c.label or c.id, "classes": list(c.classes),
                        "subjects": sorted({c.parts[i].subject for i in parts}), "hours": c.hours,
                        "weeks": list(c.weeks), "rhythm": c.rhythm})
    courses.sort(key=lambda x: (x["classes"], x["label"]))
    return {"hours": hours, "courses": courses}


def lesson_conflicts(school: School, teacher_id: str, rules: list[TimeRule]) -> list[dict]:
    """Stunden der Lehrkraft, die in den Sperrzeiten ``rules`` lägen."""
    courses = {c.id: (c, parts) for c, parts in teacher_courses(school, teacher_id)}
    if not courses or not rules:
        return []
    hz = wk.Horizon(school)
    out = []
    for les in school.lessons:
        if les.course_id not in courses:
            continue
        c, _parts = courses[les.course_id]
        members = sorted(hz.real[i] for i in hz.lesson_members(les, c))
        hits: dict[int, list[int]] = defaultdict(list)
        notes: list[str] = []
        for w in members:
            for k in range(les.length):
                p = les.start + k
                rule = next((r for r in rules if r.matches(w, les.day, p)), None)
                if rule:
                    hits[p].append(w)
                    if rule.note and rule.note not in notes:
                        notes.append(rule.note)
        if not hits:
            continue
        periods = sorted(hits)
        weeks = sorted({w for ws in hits.values() for w in ws})
        day = WEEKDAYS[les.day] if les.day < len(WEEKDAYS) else f"Tag {les.day + 1}"
        prange = f"{periods[0] + 1}." + (f"–{periods[-1] + 1}." if len(periods) > 1 else "")
        wtext = f", {wk.describe(weeks, hz.lab)}" if len(weeks) < len(members) else ""
        label = c.label or c.id
        out.append({"lesson_id": les.id, "course_id": c.id, "label": label, "classes": list(c.classes),
                    "day": les.day, "start": les.start, "length": les.length, "weeks": weeks, "periods": periods,
                    "reason": notes[0] if notes else "Sperrzeit",
                    "text": f"{day} {prange} Std. ({label}{wtext}) liegt außerhalb der verfügbaren Zeit"})
    out.sort(key=lambda x: (x["day"], x["start"], x["label"]))
    return out


def profile_rules(teacher: Teacher, profile: dict, settings: Settings) -> list[TimeRule]:
    """Harte Sperrzeiten, die gelten würden, wenn ``profile`` übernommen wird (neue Liste ``unavailable`` bzw. – bei
    alten Anträgen – bisherige Regeln plus Zeitfenster/Raster)."""
    if "unavailable" in profile:
        rules = [TimeRule.from_dict(x) if isinstance(x, dict) else x for x in profile.get("unavailable") or []]
        rules += legacy_rules(profile.get("time_windows"), profile.get("work_grid"), settings)
    else:
        rules = (strip_window_rules(teacher.unavailable)
                 + windows_to_rules(profile.get("time_windows", teacher.time_windows) or [], settings)
                 + grid_to_rules(profile.get("work_grid", teacher.work_grid) or {}, settings))
    stamp_valid_weeks(rules, settings)
    return rules


def conflicts(school: School, teacher_id: str, profile: dict) -> dict:
    """Konflikte einer (geplanten) Profiländerung gegenüber dem aktuellen Stundenplan.

    * ``outside_windows`` – Stunden, die nach der Änderung in Sperrzeiten/außerhalb der Zeitfenster lägen
    * ``dropped_subjects`` – Fächer, die die Lehrkraft nicht mehr angibt, aber noch unterrichtet
    * ``hours`` – Ist-Deputat gegenüber neuem Soll (``status``: ``ok``/``ueber``/``unter``)
    * ``preferred_new`` – Wunschklassen, in denen die Lehrkraft derzeit nicht unterrichtet (Hinweis)
    * ``messages`` (deutsch) und ``count`` (Anzahl harter Konflikte)
    """
    teacher = school.index("teachers").get(teacher_id)
    if teacher is None:
        raise KeyError(f"Lehrkraft {teacher_id} existiert nicht")
    st = school.settings
    rules = profile_rules(teacher, profile, st)
    outside = lesson_conflicts(school, teacher_id, rules)

    old_subjects = set(teacher.subjects)
    new_subjects = set(profile.get("subjects", teacher.subjects))
    dropped = []
    for subj in sorted(old_subjects - new_subjects):
        hit = [(c, i) for c, parts in teacher_courses(school, teacher_id) for i in parts if c.parts[i].subject == subj]
        if hit:
            dropped.append({"subject": subj, "hours": sum(c.hours for c, _ in hit),
                            "courses": [{"id": c.id, "label": c.label or c.id, "hours": c.hours} for c, _ in hit]})

    load = current_load(school, teacher_id)
    max_hours = int(profile.get("max_hours", teacher.max_hours))
    diff = load["hours"] - max_hours
    status = "ueber" if diff > 0 else "unter" if diff < 0 else "ok"

    taught = set()
    for c, _ in teacher_courses(school, teacher_id):
        taught.update(c.classes)
    preferred_new = [c for c in profile.get("preferred_classes", teacher.preferred_classes) if c not in taught]

    messages: list[str] = []
    if outside:
        messages.append(f"{len(outside)} Unterrichtsblöcke liegen außerhalb der neuen Sperrzeiten – "
                        "der Stundenplan muss für diese Lehrkraft neu geplant werden.")
    for d in dropped:
        messages.append(f"Fach {d['subject']} wird noch in {len(d['courses'])} Kurs(en) mit {d['hours']} Std. "
                        "unterrichtet – dafür ist eine neue Lehrkraft nötig.")
    if status == "ueber":
        messages.append(f"Ist-Deputat {load['hours']} Std. liegt {diff} Std. über dem neuen Deputat ({max_hours} Std.).")
    elif status == "unter":
        messages.append(f"Ist-Deputat {load['hours']} Std. liegt {-diff} Std. unter dem neuen Deputat "
                        f"({max_hours} Std.) – freie Kapazität.")
    if preferred_new:
        messages.append(f"Wunschklassen ohne bisherigen Unterricht: {', '.join(preferred_new)} "
                        "(wird bei der nächsten Lehrkräfte-Zuweisung bevorzugt).")
    suggestions = _suggestions(school, teacher, outside, rules)
    return {"outside_windows": outside, "dropped_subjects": dropped, "suggestions": suggestions,
            "hours": {"current": load["hours"], "max_hours": max_hours, "previous_max": int(teacher.max_hours),
                      "diff": diff, "status": status},
            "preferred_new": preferred_new, "messages": messages,
            "count": len(outside) + len(dropped) + (1 if status == "ueber" else 0)}


def _suggestions(school: School, teacher: Teacher, outside: list[dict], rules: list[TimeRule]) -> list[dict]:
    """Lösungsvorschläge für Unterricht in neuen Sperrzeiten (nichts davon geschieht automatisch):
    Teil-Neuplanung, Verschieben, anderer Beginn der Sperrzeit und – je Block – Lehrkräfte mit gleichem Fach, die
    zu der Zeit frei sind. Hinweise sind nur Vorschläge für die Planung."""
    if not outside:
        return []
    tid = teacher.id
    out = [
        {"kind": "replan", "text": "Stundenplan dieser Lehrkraft teilweise neu planen: nur die betroffenen Kurse werden "
                                   "neu gelegt, alles andere bleibt. Das Ergebnis wird erst nach Prüfung übernommen.",
         "link": f"/planung/antraege?lehrkraft={tid}"},
        {"kind": "move", "text": "Einzelne Stunden von Hand in andere freie Zeiten verschieben.",
         "link": f"/stundenplan/teacher/{tid}"},
    ]
    dated = [r for r in rules if r.valid_from]
    if dated:
        out.append({"kind": "later", "text": "Die Sperrzeit erst später gelten lassen (Datum „Gilt ab“ nach hinten "
                                             "setzen, z. B. zum Halbjahr) – bis dahin bleibt der Plan unverändert."})
    else:
        out.append({"kind": "later", "text": "Bei „Gilt ab“ ein Datum setzen, damit die Sperrzeit erst ab dann gilt und "
                                             "der bisherige Plan bis dahin unverändert bleibt."})
    # Kurse mit freien Vertretungslehrkräften
    courses = school.index("courses")
    busy: dict[str, set[tuple[int, int]]] = defaultdict(set)
    for les in school.lessons:
        c = courses.get(les.course_id)
        if c is None:
            continue
        for part in c.parts:
            if part.teacher:
                for k in range(les.length):
                    busy[part.teacher].add((les.day, les.start + k))
    lessons = {les.id: les for les in school.lessons}
    shown = 0
    for item in outside:
        les, c = lessons.get(item["lesson_id"]), courses.get(item["course_id"])
        if les is None or c is None or shown >= 5:
            continue
        subjects = {p.subject for p in c.parts if p.teacher == tid}
        free = []
        for t in school.teachers:
            if t.id == tid or not (subjects & set(t.subjects)):
                continue
            slots = [(les.day, les.start + k) for k in range(les.length)]
            if any(sl in busy[t.id] for sl in slots):
                continue
            weeks = item.get("weeks") or [None]
            if any(r.matches(w, d, p) for r in t.unavailable for w in weeks for d, p in slots):
                continue
            free.append(t)
        if free:
            shown += 1
            names = ", ".join(f"{t.name} ({t.id})" for t in free[:3])
            out.append({"kind": "teacher", "lesson_id": item["lesson_id"], "teachers": [t.id for t in free[:3]],
                        "text": f"{item['label']}: zu der Zeit frei und mit passendem Fach: {names}."})
    return out


# ----------------------------------------------------------------- einmalige Ausnahme (Antrag)
MAX_EXCEPTION_DAYS = 14


def validate_exception(school: School, raw: dict, today: Optional[Any] = None) -> dict:
    """Prüft eine einmalige Ausnahme ``{"date", "date_to", "periods", "reason"}`` → normalisiert
    (``periods`` leer = ganzer Tag). ProfileError mit deutschen Meldungen."""
    from datetime import date as _date
    errors: list[str] = []
    today = as_date(today) if today else _date.today()
    try:
        d1 = as_date(raw.get("date"))
        d2 = as_date(raw.get("date_to") or raw.get("date"))
    except (TypeError, ValueError):
        raise ProfileError(["Bitte ein Datum angeben"]) from None
    if d1 < today:
        errors.append("Das Datum liegt in der Vergangenheit")
    if d2 < d1:
        errors.append("Das Ende liegt vor dem Beginn")
    if (d2 - d1).days >= MAX_EXCEPTION_DAYS:
        errors.append(f"Höchstens {MAX_EXCEPTION_DAYS} Tage – für längere Zeiträume bitte die Sperrzeiten ändern")
    periods = _int_list(raw.get("periods"), "Stunden", errors)
    if any(not 0 <= p < school.settings.periods for p in periods):
        errors.append(f"Stunden von 1 bis {school.settings.periods}")
    reason = " ".join(str(raw.get("reason") or "").split())[:MAX_NOTE]
    if errors:
        raise ProfileError(errors)
    return {"date": d1.isoformat(), "date_to": d2.isoformat(), "periods": periods, "reason": reason}


def describe_exception(ex: dict, settings: Optional[Settings] = None) -> str:
    """„Do 15.10.2026, ab der 5. Stunde“ / „15.10.–16.10.2026, ganztägig“"""
    try:
        d1, d2 = as_date(ex["date"]), as_date(ex.get("date_to") or ex["date"])
    except (KeyError, TypeError, ValueError):
        return "–"
    day = f"{DAY_SHORT[d1.weekday()]} {d1.strftime('%d.%m.%Y')}" if d1 == d2 else         f"{d1.strftime('%d.%m.')}–{d2.strftime('%d.%m.%Y')}"
    ps = sorted(ex.get("periods") or [])
    if not ps:
        when = "ganztägig"
    else:
        last = (settings.periods - 1) if settings else None
        if last is not None and ps == list(range(ps[0], last + 1)) and ps[0] > 0:
            when = f"ab der {ps[0] + 1}. Stunde"
        elif ps == list(range(ps[0], ps[-1] + 1)) and len(ps) > 1:
            when = f"{ps[0] + 1}.–{ps[-1] + 1}. Stunde"
        else:
            when = ", ".join(f"{p + 1}." for p in ps) + " Stunde"
    return f"{day}, {when}"


def exception_impact(school: School, teacher_id: str, ex: dict) -> dict:
    """Unterricht der Lehrkraft, der durch die Ausnahme ausfällt bzw. vertreten werden muss:
    ``{"lessons": [{date, day, period, label, classes}], "count": n, "text": ...}``."""
    from datetime import timedelta
    d1, d2 = as_date(ex["date"]), as_date(ex.get("date_to") or ex["date"])
    picked = set(ex.get("periods") or [])
    courses = school.index("courses")
    own = {c.id: c for c, _parts in teacher_courses(school, teacher_id)}
    idx = wk.ActiveIndex(school)
    items: list[dict] = []
    day = d1
    while day <= d2:
        for les in school.lessons:
            c = own.get(les.course_id)
            if c is None or les.day != day.weekday() or not idx.active_on(les, courses.get(les.course_id), day):
                continue
            for k in range(les.length):
                p = les.start + k
                if not picked or p in picked:
                    items.append({"date": day.isoformat(), "day": les.day, "period": p, "label": c.label or c.id,
                                  "classes": list(c.classes)})
        day += timedelta(days=1)
    items.sort(key=lambda x: (x["date"], x["period"]))
    n = len(items)
    text = ("Kein Unterricht betroffen." if not n
            else f"{n} Unterrichtsstunde{'' if n == 1 else 'n'} betroffen – nach der Genehmigung als Abwesenheit "
                 "im Vertretungsplan.")
    return {"lessons": items[:60], "count": n, "text": text}
