"""Bewertungsraster, Notenschlüssel und Gruppeneinteilung für Aufgaben im Kursraum (reine Logik, ohne Datenbank).

Bewertungsraster
----------------
* ``kind="rubric"`` (Raster): Kriterien mit Stufen; jede Stufe hat Punkte. Beim Bewerten wird je Kriterium eine Stufe
  angeklickt, die Summe ergibt sich aus den Stufen. Höchstpunktzahl = Summe der besten Stufen.
* ``kind="guide"`` (Bewertungsleitfaden): Kriterien mit Freitext (Erwartung) und Höchstpunkten; beim Bewerten werden je
  Kriterium Punkte vergeben (0 … Höchstpunkte).
* Ausfüllung (``fill``): ``{"<kriterium>": {"level": "<stufe>", "points": 3.5, "comment": "…"}}`` – bei Raster zählt
  ``level``, beim Leitfaden ``points``; ``comment`` ist optional.

Notenschlüssel
--------------
``{"preset": "noten"}`` (Standard: 1 ab 92 %, 2 ab 81 %, 3 ab 67 %, 4 ab 50 %, 5 ab 30 %, sonst 6),
``{"preset": "punkte"}`` (Oberstufe 15 … 0 Punkte) oder ``{"steps": [{"min": 87.5, "label": "1"}, …]}`` (eigene
Prozentgrenzen, absteigend; die unterste Stufe gilt ab 0 %).
"""
from __future__ import annotations

import math
import random
import re
from typing import Any, Optional

MAX_CRITERIA = 30
MAX_LEVELS = 10
MAX_POINTS = 1000.0
MAX_TEXT = 2000
RUBRIC, GUIDE = "rubric", "guide"
KINDS = (RUBRIC, GUIDE)
KIND_LABELS = {RUBRIC: "Bewertungsraster", GUIDE: "Bewertungsleitfaden"}

GRADE_PRESETS: dict[str, list[tuple[float, str]]] = {
    "noten": [(92, "1"), (81, "2"), (67, "3"), (50, "4"), (30, "5"), (0, "6")],
    "punkte": [(95, "15"), (90, "14"), (85, "13"), (80, "12"), (75, "11"), (70, "10"), (65, "9"), (60, "8"),
               (55, "7"), (50, "6"), (45, "5"), (40, "4"), (33, "3"), (27, "2"), (20, "1"), (0, "0")],
}
PRESET_LABELS = {"noten": "Noten 1–6 (92/81/67/50/30 %)", "punkte": "Punkte 15–0 (Oberstufe)"}
DEFAULT_SCALE: dict[str, Any] = {"preset": "noten"}


def _clean(value: Any, limit: int) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(value or "")).strip()
    return text[:limit]


def _points(value: Any, what: str) -> float:
    try:
        num = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError(f"Ungültige Punktzahl bei {what}") from None
    if not math.isfinite(num) or num < 0 or num > MAX_POINTS:
        raise ValueError(f"Punkte bei {what} müssen zwischen 0 und {int(MAX_POINTS)} liegen")
    return round(num, 2)


def fmt_points(value: Optional[float]) -> str:
    """Punkte ohne überflüssige Nachkommastellen (``4.0`` → ``4``)."""
    if value is None:
        return ""
    return f"{value:g}"


# =========================================================================== Raster
def normalize_rubric(data: Any) -> dict[str, Any]:
    """Prüft und bereinigt ein Raster/einen Leitfaden (Kriterien-IDs ``c1…``, Stufen-IDs ``l1…`` werden ergänzt)."""
    if not isinstance(data, dict):
        raise ValueError("Ungültiges Bewertungsraster")
    kind = data.get("kind")
    if kind not in KINDS:
        raise ValueError("Bitte Raster oder Leitfaden wählen")
    raw = data.get("criteria")
    if not isinstance(raw, list) or not raw:
        raise ValueError("Mindestens ein Kriterium angeben")
    if len(raw) > MAX_CRITERIA:
        raise ValueError(f"Höchstens {MAX_CRITERIA} Kriterien")
    criteria: list[dict[str, Any]] = []
    seen: set[str] = set()
    for n, c in enumerate(raw, 1):
        if not isinstance(c, dict):
            raise ValueError("Ungültiges Kriterium")
        title = _clean(c.get("title"), 200)
        if not title:
            raise ValueError(f"Kriterium {n}: bitte einen Namen angeben")
        cid = _clean(c.get("id"), 20) or f"c{n}"
        if cid in seen:
            cid = f"c{n}"
        while cid in seen:
            cid += "x"
        seen.add(cid)
        entry: dict[str, Any] = {"id": cid, "title": title, "description": _clean(c.get("description"), MAX_TEXT)}
        if kind == GUIDE:
            top = _points(c.get("max_points"), f"„{title}“")
            if top <= 0:
                raise ValueError(f"„{title}“: Höchstpunkte müssen größer als 0 sein")
            entry["max_points"] = top
        else:
            lv_raw = c.get("levels")
            if not isinstance(lv_raw, list) or len(lv_raw) < 2:
                raise ValueError(f"„{title}“: mindestens zwei Stufen angeben")
            if len(lv_raw) > MAX_LEVELS:
                raise ValueError(f"„{title}“: höchstens {MAX_LEVELS} Stufen")
            levels, lseen = [], set()
            for m, lv in enumerate(lv_raw, 1):
                if not isinstance(lv, dict):
                    raise ValueError(f"„{title}“: ungültige Stufe")
                ltitle = _clean(lv.get("title"), 200)
                if not ltitle:
                    raise ValueError(f"„{title}“: Stufe {m} braucht einen Namen")
                lid = _clean(lv.get("id"), 20) or f"l{m}"
                while lid in lseen:
                    lid += "x"
                lseen.add(lid)
                levels.append({"id": lid, "title": ltitle, "description": _clean(lv.get("description"), MAX_TEXT),
                               "points": _points(lv.get("points"), f"„{title}“ / {ltitle}")})
            entry["levels"] = levels
        criteria.append(entry)
    out = {"kind": kind, "criteria": criteria}
    if max_points(out) <= 0:
        raise ValueError("Die Gesamtpunktzahl muss größer als 0 sein")
    return out


def criterion_max(kind: str, criterion: dict[str, Any]) -> float:
    if kind == GUIDE:
        return float(criterion.get("max_points") or 0)
    return max((float(lv.get("points") or 0) for lv in criterion.get("levels") or []), default=0.0)


def max_points(rubric: dict[str, Any]) -> float:
    """Höchstpunktzahl: Summe der besten Stufen bzw. der Höchstpunkte der Kriterien."""
    kind = rubric.get("kind", "")
    return round(sum(criterion_max(kind, c) for c in rubric.get("criteria") or []), 2)


def score_fill(rubric: dict[str, Any], fill: Any) -> tuple[float, dict[str, Any], bool]:
    """Summe und bereinigte Ausfüllung. ``complete`` = jedes Kriterium ist bewertet.

    Wirft ``ValueError`` bei unbekannten Stufen/Kriterien oder Punkten außerhalb 0 … Höchstpunkte."""
    if fill is None:
        fill = {}
    if not isinstance(fill, dict):
        raise ValueError("Ungültige Bewertung des Rasters")
    kind = rubric.get("kind", "")
    by_id = {c["id"]: c for c in rubric.get("criteria") or []}
    unknown = set(fill) - set(by_id)
    if unknown:
        raise ValueError("Die Bewertung passt nicht zum Raster")
    clean: dict[str, Any] = {}
    total = 0.0
    complete = True
    for cid, crit in by_id.items():
        raw = fill.get(cid)
        if not isinstance(raw, dict):
            complete = False
            continue
        entry: dict[str, Any] = {}
        comment = _clean(raw.get("comment"), MAX_TEXT)
        if comment:
            entry["comment"] = comment
        if kind == RUBRIC:
            lid = raw.get("level")
            if lid in (None, ""):
                complete = False
            else:
                level = next((lv for lv in crit["levels"] if lv["id"] == lid), None)
                if level is None:
                    raise ValueError(f"„{crit['title']}“: unbekannte Stufe")
                entry["level"] = level["id"]
                entry["points"] = float(level["points"])
                total += float(level["points"])
        else:
            if raw.get("points") in (None, ""):
                complete = False
            else:
                pts = _points(raw.get("points"), f"„{crit['title']}“")
                if pts > float(crit["max_points"]) + 1e-9:
                    raise ValueError(f"„{crit['title']}“: höchstens {fmt_points(float(crit['max_points']))} Punkte")
                entry["points"] = pts
                total += pts
        if entry:
            clean[cid] = entry
    return round(total, 2), clean, complete


# =========================================================================== Notenschlüssel
def normalize_scale(data: Any) -> dict[str, Any]:
    """Prüft einen Notenschlüssel (``None`` → Standard)."""
    if not data:
        return dict(DEFAULT_SCALE)
    if not isinstance(data, dict):
        raise ValueError("Ungültiger Notenschlüssel")
    preset = data.get("preset")
    if preset:
        if preset not in GRADE_PRESETS:
            raise ValueError("Unbekannter Notenschlüssel")
        return {"preset": preset}
    steps_raw = data.get("steps")
    if not isinstance(steps_raw, list) or not 2 <= len(steps_raw) <= 20:
        raise ValueError("Der Notenschlüssel braucht zwei bis 20 Stufen")
    steps = []
    for st in steps_raw:
        if not isinstance(st, dict):
            raise ValueError("Ungültige Stufe im Notenschlüssel")
        label = _clean(st.get("label"), 20)
        try:
            low = float(str(st.get("min")).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError("Ungültige Prozentgrenze im Notenschlüssel") from None
        if not label or not 0 <= low <= 100:
            raise ValueError("Jede Stufe braucht eine Note und eine Grenze von 0 bis 100 %")
        steps.append({"min": round(low, 2), "label": label})
    steps.sort(key=lambda s: -s["min"])
    if len({s["min"] for s in steps}) != len(steps):
        raise ValueError("Prozentgrenzen dürfen sich nicht wiederholen")
    steps[-1]["min"] = 0.0
    return {"steps": steps}


def scale_steps(scale: Optional[dict[str, Any]]) -> list[tuple[float, str]]:
    scale = scale or DEFAULT_SCALE
    if scale.get("steps"):
        return [(float(s["min"]), str(s["label"])) for s in sorted(scale["steps"], key=lambda s: -float(s["min"]))]
    return GRADE_PRESETS.get(scale.get("preset") or "noten", GRADE_PRESETS["noten"])


def percent(points: Optional[float], top: Optional[float]) -> Optional[float]:
    if points is None or not top or top <= 0:
        return None
    return round(100.0 * points / top, 2)


def grade_for(points: Optional[float], top: Optional[float], scale: Optional[dict[str, Any]] = None) -> Optional[str]:
    """Note zu ``points`` von ``top`` Punkten nach Notenschlüssel (``None`` ohne Punkte)."""
    pct = percent(points, top)
    if pct is None:
        return None
    steps = scale_steps(scale)
    for low, label in steps:
        if pct + 1e-9 >= low:
            return label
    return steps[-1][1]


_GRADE_RE = re.compile(r"^\s*([1-6])\s*([+-])?\s*$|^\s*([0-9]+[.,][0-9]+)\s*$")


def grade_number(label: Optional[str]) -> Optional[float]:
    """Zahlenwert einer Note (``"2+"`` → 1.7, ``"2-"`` → 2.3, ``"2,5"`` → 2.5); sonst ``None`` (z. B. Punkte-Noten)."""
    m = _GRADE_RE.match(label or "")
    if not m:
        return None
    if m.group(3):
        return float(m.group(3).replace(",", "."))
    base = float(m.group(1))
    return round(base - 0.3 if m.group(2) == "+" else base + 0.3 if m.group(2) == "-" else base, 1)


# =========================================================================== Gruppen
def auto_divide(user_ids: list[int], *, count: Optional[int] = None, size: Optional[int] = None,
                shuffle: bool = True, rng: Optional[random.Random] = None) -> list[list[int]]:
    """Teilt ``user_ids`` auf Gruppen auf: ``count`` Gruppen oder Gruppen der Größe ``size`` (gleichmäßig verteilt,
    Größen unterscheiden sich höchstens um 1). ``shuffle=False`` behält die Reihenfolge (z. B. alphabetisch) bei."""
    ids = list(dict.fromkeys(user_ids))
    if not ids:
        return []
    if (count is None) == (size is None):
        raise ValueError("Bitte Gruppenzahl oder Gruppengröße angeben")
    n_groups = count if count is not None else math.ceil(len(ids) / max(1, size or 1))
    n_groups = max(1, min(int(n_groups), len(ids)))
    if shuffle:
        (rng or random).shuffle(ids)
    groups: list[list[int]] = [[] for _ in range(n_groups)]
    if shuffle:
        for i, uid in enumerate(ids):
            groups[i % n_groups].append(uid)
    else:      # nacheinander füllen: Gruppen bleiben "alphabetisch zusammenhängend"
        base, extra = divmod(len(ids), n_groups)
        pos = 0
        for g in range(n_groups):
            take = base + (1 if g < extra else 0)
            groups[g] = ids[pos:pos + take]
            pos += take
    return groups
