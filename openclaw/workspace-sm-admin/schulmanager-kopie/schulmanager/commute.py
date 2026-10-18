"""Pendeln von Lehrkräften zwischen Standorten (reine Logik, ohne Abhängigkeit vom Planer).

Regeln
------
* **Pendelart** je Lehrkraft (``Teacher.commute_mode``): ``never`` = nie am selben Tag an zwei Standorten,
  ``once`` = höchstens ein Standortwechsel am Tag, ``free`` = beliebig. Ist nichts gewählt, entscheidet das alte Feld
  ``Teacher.commutes`` (``False`` = ``never``, sonst ``free``).
* **Wegezeit** zwischen zwei Standorten: ``Settings.site_travel`` (Minuten je Standortpaar, beide Richtungen). Fehlt ein
  Paar, gilt ``Settings.site_travel_periods`` (freie Stunden dazwischen).
* **Mindestpause** der Lehrkraft (``Teacher.commute_gap``, Minuten): zwischen dem Ende der einen und dem Beginn der
  anderen Stunde beim Standortwechsel – wirksam ist der größere Wert aus Wegezeit und Mindestpause.

Die Pause zwischen zwei Stunden ergibt sich aus dem Zeitraster (``period_times``, ``period_minutes``): Dauer von Ende
der Stunde *p* bis Beginn der Stunde *q* (inklusive der Pausen und freien Stunden dazwischen).
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

MODES = ("never", "once", "free")
MODE_LABELS = {"never": "nie pendeln", "once": "höchstens 1× am Tag", "free": "beliebig"}


def teacher_mode(teacher: Any) -> str:
    """Wirksame Pendelart (``never`` | ``once`` | ``free``)."""
    mode = getattr(teacher, "commute_mode", "") or ""
    if mode in MODES:
        return mode
    return "free" if getattr(teacher, "commutes", True) else "never"


def travel_minutes(settings: Any, a: Optional[str], b: Optional[str]) -> Optional[int]:
    """Wegezeit zwischen zwei Standorten in Minuten; ``None``, wenn für das Paar nichts eingetragen ist."""
    if not a or not b or a == b:
        return 0 if a == b else None
    for row in getattr(settings, "site_travel", None) or []:
        if not isinstance(row, dict):
            continue
        if {row.get("a"), row.get("b")} == {a, b}:
            try:
                return max(0, int(row.get("minutes") or 0))
            except (TypeError, ValueError):
                return None
    return None


def _minutes(value: str) -> Optional[int]:
    try:
        h, m = str(value).split(":")
        return int(h) * 60 + int(m)
    except (TypeError, ValueError):
        return None


def gap_minutes(settings: Any, p: int, q: int) -> Optional[int]:
    """Minuten vom Ende der Stunde ``p`` bis zum Beginn der späteren Stunde ``q`` (``None`` ohne Uhrzeiten)."""
    if q <= p:
        return 0
    times = list(getattr(settings, "period_times", None) or [])
    if q >= len(times) or p >= len(times):
        return None
    start_q, start_p = _minutes(times[q]), _minutes(times[p])
    if start_q is None or start_p is None:
        return None
    length = int(getattr(settings, "period_minutes", 45) or 45)
    return max(0, start_q - (start_p + length))


def special(settings: Any, teachers: Iterable[Any]) -> bool:
    """Gibt es Wegezeiten oder Mindestpausen, die über ``site_travel_periods`` hinausgehen?"""
    if getattr(settings, "site_travel", None):
        return True
    return any(int(getattr(t, "commute_gap", 0) or 0) > 0 for t in teachers)


def change_ok(settings: Any, teacher: Any, site_a: Optional[str], p: int, site_b: Optional[str], q: int) -> bool:
    """Darf die Lehrkraft in Stunde ``p`` (Standort A) und in der späteren Stunde ``q`` (Standort B) unterrichten?

    Gleicher Standort oder unbekannter Standort: immer. Sonst Pendelart ``never`` → nein; sonst muss die Pause
    mindestens der Wegezeit des Standortpaars bzw. der Mindestpause der Lehrkraft entsprechen. Ohne eingetragene
    Wegezeit gilt ``site_travel_periods`` (freie Stunden dazwischen)."""
    if not site_a or not site_b or site_a == site_b:
        return True
    if q < p:
        p, q, site_a, site_b = q, p, site_b, site_a
    if teacher_mode(teacher) == "never":
        return False
    gap = gap_minutes(settings, p, q)
    need = travel_minutes(settings, site_a, site_b)
    if need is None:
        free = q - p - 1
        if free < max(0, int(getattr(settings, "site_travel_periods", 0) or 0)):
            return False
        need = 0
    own = int(getattr(teacher, "commute_gap", 0) or 0)
    if gap is None:        # ohne Uhrzeiten nur nach freien Stunden
        return True
    return gap >= max(need, own)


def day_changes(sites_by_period: dict[int, Optional[str]]) -> list[tuple[int, int]]:
    """Standortwechsel eines Tages: Paare ``(p, q)`` aufeinanderfolgender Stunden (nach Stunde sortiert) mit
    unterschiedlichem, bekanntem Standort."""
    seq = [(p, s) for p, s in sorted(sites_by_period.items()) if s]
    return [(a[0], b[0]) for a, b in zip(seq, seq[1:]) if a[1] != b[1]]


def violations(settings: Any, teacher: Any, sites_by_period: dict[int, Optional[str]]) -> list[str]:
    """Verstöße eines Tages gegen die Pendelregeln der Lehrkraft (Texte für Bericht und Hinweise)."""
    out: list[str] = []
    seq = [(p, s) for p, s in sorted(sites_by_period.items()) if s]
    changes = [(a, b) for a, b in zip(seq, seq[1:]) if a[1] != b[1]]
    mode = teacher_mode(teacher)
    if changes and mode == "never":
        out.append("pendelt nicht, wechselt aber den Standort")
    elif len(changes) > 1 and mode == "once":
        out.append(f"{len(changes)} Standortwechsel an einem Tag (erlaubt: 1)")
    for (pa, sa), (pb, sb) in changes:
        if mode != "never" and not change_ok(settings, teacher, sa, pa, sb, pb):
            gap = gap_minutes(settings, pa, pb)
            out.append(f"zu kurze Pause beim Wechsel {sa} → {sb} ({pa + 1}. → {pb + 1}. Stunde"
                       + (f", {gap} Min." if gap is not None else "") + ")")
    return out
