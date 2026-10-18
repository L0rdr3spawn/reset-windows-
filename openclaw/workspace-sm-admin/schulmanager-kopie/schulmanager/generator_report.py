"""Auswertung eines Generator-Laufs (reine Logik, ohne Datenbank und ohne Hintergrundprozesse).

``evaluate(before, after)`` vergleicht den aktuellen Plan (``before``) mit einem Entwurf (``after``) und liefert alles,
was die Oberfläche (Planung › Generator › Ergebnis) in Kacheln und Diagrammen zeigt:

* ``kpis`` – Kennzahlen vorher/nachher. Sie kommen aus **derselben Funktion wie der Qualitätsbericht**
  (``timetable.validate_school``, Durchschnitt je Schulwoche); die Kennzahlen des Generators selbst werden nicht
  verwendet, damit beide nie auseinanderlaufen.
* ``entities`` – je Klasse und je Lehrkraft die größten Verbesserungen und Verschlechterungen.
* ``moves`` – wie viele Blöcke sich verschoben haben (Tag, Stunde, Raum) samt Liste.
* ``distribution`` – Verteilung der Unterrichtsstunden je Wochentag und Stunde, vorher/nachher.
* ``rules`` – weiche Ziele mit Gewicht (aus „Prioritäten & Regeln“) und ihre Verstöße vorher/nachher.
* ``hints`` – Hinweise des Generators in lesbarem Deutsch.

Dieselbe Auswertung dient dem Vergleich eines gespeicherten Plan-Stands mit dem aktuellen Plan.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Optional

from . import rules as rl
from .models import School
from .timetable import validate_school

#: Kennzahlen in Anzeigereihenfolge: (Schlüssel, Beschriftung, Einheit); kleiner = besser
KPI_DEFS: tuple[tuple[str, str, str], ...] = (
    ("class_gaps", "Hohlstunden Klassen", "Ø je Woche"),
    ("teacher_gaps", "Springstunden Lehrkräfte", "Ø je Woche"),
    ("site_changes", "Standortwechsel", "Ø je Woche"),
    ("core_late", "Hauptfächer spät", "Blöcke"),
    ("unplaced_hours", "Unverplante Stunden", "Stunden"),
    ("conflicts", "Konflikte", "Stück"),
    ("cost", "Strafpunkte", "Punkte"),
)
MAX_MOVES = 400
TOP = 8
DAY_NAMES = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


def _num(x: float):
    return int(round(x)) if abs(x - round(x)) < 1e-6 else round(x, 1)


def plan_cost_info(school: School) -> tuple[Optional[float], list[dict]]:
    """Kosten eines vorhandenen Plans nach der Zielfunktion des Generators (alle Stunden fixiert, keine Optimierung)
    und ihre Aufschlüsselung je Baustein (``Scheduler.cost_parts``, Summe = Kosten).

    ``(None, [])``, wenn die Berechnung scheitert (die Auswertung bleibt dann ohne Kosten vorher/nachher)."""
    from .scheduler import Scheduler
    try:
        work = School.from_dict(school.to_dict())
        for le in work.lessons:
            le.locked = True
        sch = Scheduler(work, seed=1)
        covered = sch._preplace_locked(list(work.lessons))      # noqa: SLF001 - wie ``Scheduler.generate``
        missing = []
        for k, c in enumerate(sch.courses):
            need = {w: c.hours - covered[(k, w)] for w in c.weeks}
            missing += sch._make_blocks(k, need, c.double)      # noqa: SLF001 - fehlende Stunden zählen als unverplant
        sch._add_blocks(missing)                                # noqa: SLF001
        return round(sch.total_cost(), 1), sch.cost_parts()
    except Exception:  # noqa: BLE001 - Kosten sind eine Zugabe
        return None, []


def plan_cost(school: School) -> Optional[float]:
    """Nur die Gesamtkosten von :func:`plan_cost_info`."""
    return plan_cost_info(school)[0]


def cost_parts_table(parts_before: list[dict], parts_after: list[dict], cost_before: Optional[float],
                     cost_after: Optional[float]) -> list[dict]:
    """Strafpunkte je Baustein vorher/nachher. Nur echte Kleinstbeträge (zusammen höchstens 2 % der Gesamtsumme, die
    kleinsten zuerst) werden zu „Übrige“ zusammengefasst; unverplante Stunden bleiben immer einzeln."""
    ids = list(dict.fromkeys([p["id"] for p in parts_after] + [p["id"] for p in parts_before]))
    b = {p["id"]: p for p in parts_before}
    a = {p["id"]: p for p in parts_after}
    rows: list[dict] = []
    for pid in ids:
        pb, pa = b.get(pid), a.get(pid)
        ref = pa or pb
        rows.append({"id": pid, "title": ref["title"], "weight": ref["weight"],
                     "count_before": pb["count"] if pb else 0, "count_after": pa["count"] if pa else 0,
                     "points_before": pb["points"] if pb else 0, "points_after": pa["points"] if pa else 0,
                     "weight_before": pb["weight"] if pb else 0, "weight_after": pa["weight"] if pa else 0,
                     "top": (pa or {"top": []})["top"]})
    budget = 0.02 * max(cost_after or 0.0, cost_before or 0.0)
    rest = {"before": 0.0, "after": 0.0}
    kept = list(rows)
    for r in sorted(rows, key=lambda r: max(r["points_after"], r["points_before"])):
        if r["id"] == "unplaced":
            continue
        if max(rest["before"] + r["points_before"], rest["after"] + r["points_after"]) > budget:
            break
        rest["before"] += r["points_before"]
        rest["after"] += r["points_after"]
        kept.remove(r)
    kept.sort(key=lambda r: -max(r["points_after"], r["points_before"]))
    if rest["before"] or rest["after"]:
        kept.append({"id": "rest", "title": "Übrige (Kleinstbeträge)", "weight": 0, "count_before": 0, "count_after": 0,
                     "points_before": round(rest["before"], 2), "points_after": round(rest["after"], 2),
                     "weight_before": 0, "weight_after": 0, "top": []})
    return kept


def _stats(school: School) -> tuple[dict, dict]:
    """(``stats``, Werte je Klasse/Lehrkraft) aus ``validate_school`` – genau die Rechnung des Qualitätsberichts."""
    rep = validate_school(school, details=True)
    return rep["stats"], rep.get("per_entity", {})


# --------------------------------------------------------------------------- Kennzahlen
def kpis(before: dict, after: dict, cost_before: Optional[float], cost_after: Optional[float]) -> list[dict]:
    out = []
    for key, label, unit in KPI_DEFS:
        if key == "cost":
            b, a = cost_before, cost_after
        else:
            b, a = before.get(key, 0), after.get(key, 0)
        delta = None if b is None or a is None else _num(a - b)
        out.append({"key": key, "label": label, "unit": unit, "before": b, "after": a, "delta": delta,
                    "better": None if not delta else delta < 0})
    return out


# --------------------------------------------------------------------------- Klassen und Lehrkräfte
def _entity_rows(ids: dict[str, str], before: dict, after: dict) -> dict:
    """Je Klasse bzw. Lehrkraft: Wert vorher/nachher; die größten Verbesserungen und Verschlechterungen."""
    rows = []
    for ident, name in ids.items():
        b, a = before.get(ident, 0), after.get(ident, 0)
        rows.append({"id": ident, "name": name, "before": _num(b), "after": _num(a), "delta": _num(a - b)})
    better = sorted((r for r in rows if r["delta"] < 0), key=lambda r: (r["delta"], r["name"]))[:TOP]
    worse = sorted((r for r in rows if r["delta"] > 0), key=lambda r: (-r["delta"], r["name"]))[:TOP]
    highest = sorted((r for r in rows if r["after"] > 0), key=lambda r: (-r["after"], r["name"]))[:TOP]
    return {"better": better, "worse": worse, "highest": highest, "changed": sum(1 for r in rows if r["delta"]),
            "better_count": sum(1 for r in rows if r["delta"] < 0),
            "worse_count": sum(1 for r in rows if r["delta"] > 0), "total": len(rows)}


# --------------------------------------------------------------------------- Verschiebungen
def _week_key(le) -> tuple:
    return (tuple(le.weeks or ()), tuple(sorted((le.rhythm or {}).items())) if isinstance(le.rhythm, dict) else
            (le.rhythm or ""))


def moves(before: School, after: School) -> dict:
    """Vergleicht die Blöcke je Kurs. Gleiche Blöcke (Tag, Beginn, Länge, Wochen) gelten als unverändert (bzw. nur
    Raum geändert), übrige werden der Reihe nach als verschoben gepaart, der Rest ist neu oder entfallen."""
    courses = after.index("courses")
    courses.update({k: v for k, v in before.index("courses").items() if k not in courses})
    by_b: dict[str, list] = defaultdict(list)
    by_a: dict[str, list] = defaultdict(list)
    for le in before.lessons:
        by_b[le.course_id].append(le)
    for le in after.lessons:
        by_a[le.course_id].append(le)
    items: list[dict] = []
    counts = {"unchanged": 0, "moved": 0, "room": 0, "added": 0, "removed": 0, "day": 0, "period": 0}

    def info(c, cid):
        return {"course": cid, "label": (c.label or cid) if c else cid, "classes": list(c.classes) if c else [],
                "teachers": [p.teacher for p in c.parts if p.teacher] if c else []}

    def where(le) -> dict:
        return {"day": le.day, "start": le.start + 1, "length": le.length, "rooms": [r for r in le.rooms if r]}

    for cid in sorted(set(by_b) | set(by_a)):
        c = courses.get(cid)
        olds, news = list(by_b.get(cid, [])), list(by_a.get(cid, []))
        rest_new = []
        for n in news:
            key = (n.day, n.start, n.length, _week_key(n))
            match = next((o for o in olds if (o.day, o.start, o.length, _week_key(o)) == key), None)
            if match is None:
                rest_new.append(n)
                continue
            olds.remove(match)
            if sorted(r for r in match.rooms if r) != sorted(r for r in n.rooms if r):
                counts["room"] += 1
                items.append({**info(c, cid), "kind": "room", "changes": ["Raum"], "from": where(match), "to": where(n)})
            else:
                counts["unchanged"] += 1
        olds.sort(key=lambda x: (x.day, x.start))
        rest_new.sort(key=lambda x: (x.day, x.start))
        for o, n in zip(olds, rest_new):
            ch = []
            if o.day != n.day:
                ch.append("Tag")
                counts["day"] += 1
            if o.start != n.start or o.length != n.length:
                ch.append("Stunde")
                counts["period"] += 1
            if sorted(r for r in o.rooms if r) != sorted(r for r in n.rooms if r):
                ch.append("Raum")
            counts["moved"] += 1
            items.append({**info(c, cid), "kind": "moved", "changes": ch, "from": where(o), "to": where(n)})
        for n in rest_new[len(olds):]:
            counts["added"] += 1
            items.append({**info(c, cid), "kind": "added", "changes": [], "from": None, "to": where(n)})
        for o in olds[len(rest_new):]:
            counts["removed"] += 1
            items.append({**info(c, cid), "kind": "removed", "changes": [], "from": where(o), "to": None})
    counts["total_before"] = len(before.lessons)
    counts["total_after"] = len(after.lessons)
    order = {"moved": 0, "added": 1, "removed": 2, "room": 3}
    items.sort(key=lambda r: (order[r["kind"]], r["label"]))
    return {"counts": counts, "items": items[:MAX_MOVES], "truncated": len(items) > MAX_MOVES}


# --------------------------------------------------------------------------- Verteilung
def distribution(before: School, after: School) -> dict:
    """Unterrichtsstunden (Blocklänge) je Wochentag und je Stunde, vorher/nachher; dazu Hauptfach-Stunden je Stunde."""
    periods = max(before.settings.periods, after.settings.periods)

    def count(school: School) -> tuple[list[int], list[int], list[int]]:
        days = [0] * 7
        per = [0] * periods
        core = [0] * periods
        courses = school.index("courses")
        subjects = school.index("subjects")
        for le in school.lessons:
            c = courses.get(le.course_id)
            is_core = bool(c and c.parts and subjects.get(c.parts[0].subject) and subjects[c.parts[0].subject].core)
            days[le.day] += le.length
            for k in range(le.length):
                p = le.start + k
                if p < periods:
                    per[p] += 1
                    core[p] += 1 if is_core else 0
        return days, per, core

    db, pb, cb = count(before)
    da, pa, ca = count(after)
    used = [d for d in range(7) if db[d] or da[d]] or list(range(5))
    return {
        "days": [{"day": d, "label": DAY_NAMES[d], "before": db[d], "after": da[d]} for d in used],
        "periods": [{"period": p + 1, "before": pb[p], "after": pa[p]} for p in range(periods) if pb[p] or pa[p]],
        "core_periods": [{"period": p + 1, "before": cb[p], "after": ca[p]} for p in range(periods) if cb[p] or ca[p]],
    }


# --------------------------------------------------------------------------- Regeln
def rule_rows(school: School, stats_before: dict, stats_after: dict, before: School) -> list[dict]:
    """Weiche Ziele mit Gewicht und Verstößen vorher/nachher (Einstellungen des Entwurfs gelten)."""
    resolved = rl.resolve(school.settings)
    ctx = rl.context(school)
    vb = rl.violations(before, stats_before)
    va = rl.violations(school, stats_after)
    labels = rl.LEVEL_LABELS
    rows = []
    for rule in rl.RULES:
        if not rl._is_relevant(rule, ctx):    # noqa: SLF001 - gleiche Auswahl wie die Regelseite
            continue
        item = resolved["items"][rule.id]
        level = item.get("level")
        b, a = vb.get(rule.id), va.get(rule.id)
        if level == "aus" or (b is None and a is None):
            continue
        weight = rl.effective_weight(rule, item) if rule.control == "level" else None
        rows.append({"id": rule.id, "title": rule.title, "group": rule.group, "level": level,
                     "level_label": labels.get(level, str(level)) if rule.control == "level" else "an",
                     "weight": None if weight is None else _num(weight),
                     "before": None if b is None else _num(b), "after": None if a is None else _num(a),
                     "delta": None if b is None or a is None else _num(a - b), "hard": bool(rule.hard and level == "muss")})
    rows.sort(key=lambda r: (-(r["weight"] or 0), r["title"]))
    return rows


# --------------------------------------------------------------------------- Hinweise
_MAX_PER_DAY = re.compile(r"^(?P<c>.+): musste (?P<n>\d+)× an einem Tag gelegt werden$")
_DROPPED = re.compile(r"^Fixierte Stunde (?P<l>\S+) \((?P<c>.+)\) kollidiert und wurde verworfen$")
_NO_WEEK = re.compile(r"^(?P<c>.+): liegt in keiner Woche dieses Schuljahres$")


def clean_warnings(school: School, warnings: list[str]) -> list[dict]:
    """Hinweise des Generators in lesbarem Deutsch: ``[{kind, text, course}]`` (gleiche Hinweise werden zusammengefasst)."""
    courses = school.index("courses")

    def label(cid: str) -> str:
        c = courses.get(cid)
        return (c.label or cid) if c else cid

    out: list[dict] = []
    seen: set[str] = set()
    for w in warnings:
        text, kind, course = w, "info", None
        if m := _MAX_PER_DAY.match(w):
            course, kind = m["c"], "per_day"
            text = f"{label(course)}: Das Fach liegt an einem Tag {m['n']}× – anders ließ es sich nicht verplanen."
        elif m := _DROPPED.match(w):
            course, kind = m["c"], "locked"
            text = f"{label(course)}: Eine fixierte Stunde kollidierte mit anderen Stunden und wurde nicht übernommen."
        elif m := _NO_WEEK.match(w):
            course, kind = m["c"], "weeks"
            text = f"{label(course)}: Der Kurs liegt in keiner Woche dieses Schuljahres und wird nicht verplant."
        if text in seen:
            continue
        seen.add(text)
        out.append({"kind": kind, "text": text, "course": course})
    return out


# --------------------------------------------------------------------------- Gesamt
def evaluate(before: School, after: School, *, warnings: Optional[list[str]] = None,
             with_cost: bool = True, cost_before: Optional[float] = None,
             parts_before: Optional[list[dict]] = None) -> dict:
    """Vollständige Auswertung (siehe Moduldoku). ``after`` ist der Entwurf bzw. der gespeicherte Stand."""
    sb, pb = _stats(before)
    sa, pa = _stats(after)
    pb_parts = parts_before or []
    if cost_before is not None:
        cb = cost_before
    elif with_cost:
        cb, pb_parts = plan_cost_info(before)
    else:
        cb = None
    ca, pa_parts = plan_cost_info(after) if with_cost else (None, [])
    classes = {c.id: c.name or c.id for c in after.classes}
    teachers = {t.id: t.name or t.id for t in after.teachers}
    return {
        "kpis": kpis(sb, sa, cb, ca),
        "stats_before": {k: v for k, v in sb.items() if isinstance(v, (int, float))},
        "stats_after": {k: v for k, v in sa.items() if isinstance(v, (int, float))},
        "week_variants": sa.get("week_variants", 1),
        "entities": {
            "classes": _entity_rows(classes, pb.get("class_gaps", {}), pa.get("class_gaps", {})),
            "teachers": _entity_rows(teachers, pb.get("teacher_gaps", {}), pa.get("teacher_gaps", {})),
            "teachers_sites": _entity_rows(teachers, pb.get("site_changes", {}), pa.get("site_changes", {})),
        },
        "moves": moves(before, after),
        "distribution": distribution(before, after),
        "rules": rule_rows(after, sb, sa, before),
        "hints": clean_warnings(after, warnings or []),
        "cost_before": cb,
        "cost_parts": cost_parts_table(pb_parts, pa_parts, cb, ca),
    }


def rank_key(ev: dict) -> tuple:
    """Sortierschlüssel für „beste Variante“: erst Konflikte, dann unverplante Stunden, dann Kosten (kleiner = besser)."""
    after = ev.get("stats_after", {})
    cost = next((k["after"] for k in ev.get("kpis", []) if k["key"] == "cost"), None)
    return (after.get("conflicts", 0), after.get("unplaced_hours", 0), cost if cost is not None else 0)


__all__: list[Any] = ["evaluate", "plan_cost", "plan_cost_info", "cost_parts_table", "rank_key", "kpis", "moves", "distribution", "clean_warnings", "KPI_DEFS"]
