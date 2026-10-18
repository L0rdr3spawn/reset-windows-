"""Planzeiträume: je Zeitraum (z. B. 1./2. Halbjahr) ein eigener Stundenplan.

Modell (bewusst klein, ohne neue Tabelle):

* ``Settings.plan_periods`` = Liste ``{"id", "name", "date_from", "date_to", "from_week", "to_week"}``. Maßgeblich
  sind die Daten; die laufenden Wochen (``from_week``/``to_week``, ganze Wochen Mo–So des Schuljahres) werden beim
  Speichern berechnet (:func:`normalize`). Leer = ein Plan für das ganze Schuljahr (ältere Dokumente, keine Migration).
* Jede ``Lesson`` trägt ``period`` (Kennung) und die daraus abgeleiteten ``from_week``/``to_week``. Die zentrale
  Aktiv-Logik (``weeks.lesson_active_in``, ``Horizon.lesson_members``) beachtet den Bereich; Ansichten, Vertretung,
  Monitor, Bericht, iCal … folgen dadurch ohne eigene Änderung. Stunden mit ``period == ""`` gelten in jedem Zeitraum.
* Ein Zeitraum „hat einen Plan“, wenn mindestens eine Stunde zu ihm gehört (:func:`has_plan`). Wochen in einem Zeitraum
  ohne Plan oder außerhalb aller Zeiträume haben den Zustand ``missing`` bzw. ``none`` (:func:`state_for_week`); sie
  fließen nicht in Plan-Prüfung und Qualitätsbericht ein (``weeks.PlanWeeks``).
* Generator je Zeitraum: :func:`prepare_generation` begrenzt die Kurse auf die Wochen des Zeitraums und liefert nur dessen
  Stunden (bzw. die Stunden eines Quellzeitraums als fixierten Start); :func:`merge_generated` ersetzt beim Übernehmen
  nur den Plan dieses Zeitraums.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, Optional

from . import weeks as wk
from .calendar_utils import as_date, monday_of, plan_week, year_bounds
from .models import Lesson, School, lesson_in_range, spec_active

MAX_PERIODS = 12
KEYS = ("id", "name", "date_from", "date_to", "from_week", "to_week")


# ===================================================================== Zugriff
def periods(school: School) -> list[dict]:
    """Zeiträume nach Beginn sortiert (leer, wenn nicht eingerichtet)."""
    raw = [p for p in (getattr(school.settings, "plan_periods", None) or []) if isinstance(p, dict)]
    return sorted(raw, key=lambda p: (int(p.get("from_week") or 0), str(p.get("date_from") or "")))


def active(school: School) -> bool:
    return bool(periods(school))


def get(school: School, period_id: str) -> Optional[dict]:
    return next((p for p in periods(school) if p.get("id") == period_id), None)


def period_for_week(school: School, week: Optional[int]) -> Optional[dict]:
    if week is None:
        return None
    for p in periods(school):
        if int(p["from_week"]) <= week <= int(p["to_week"]):
            return p
    return None


def period_for_date(school: School, d: date | str) -> Optional[dict]:
    return period_for_week(school, plan_week(school.settings, as_date(d)))


def lessons_of(school: School, period_id: str) -> list[Lesson]:
    return [le for le in school.lessons if le.period == period_id]


def has_plan(school: School, period_id: str) -> bool:
    """Gehört mindestens eine Stunde zum Zeitraum (oder gilt ein älterer Plan ohne Zeitraum)?"""
    return any(le.period in (period_id, "") for le in school.lessons)


def public(school: School, p: dict) -> dict:
    """Zeitraum für die Antwort: Felder und ``has_plan``/``lessons``."""
    out = {k: p.get(k) for k in KEYS}
    own = sum(1 for le in school.lessons if le.period == p.get("id"))
    out["lessons"] = own
    out["has_plan"] = own > 0 or any(le.period == "" for le in school.lessons)
    return out


def state_for_week(school: School, week: Optional[int]) -> dict:
    """Plan-Zustand einer laufenden Woche: ``{"active", "state": ok|missing|none, "period"}``.

    ``missing`` = Zeitraum ohne Plan, ``none`` = Woche liegt in keinem Zeitraum. Ohne eingerichtete Zeiträume immer ``ok``."""
    ps = periods(school)
    if not ps:
        return {"active": False, "state": "ok", "period": None}
    p = period_for_week(school, week)
    if p is None:
        return {"active": True, "state": "none", "period": None}
    info = {k: p.get(k) for k in ("id", "name", "date_from", "date_to", "from_week", "to_week")}
    return {"active": True, "state": "ok" if has_plan(school, p["id"]) else "missing", "period": info}


def state_for_date(school: School, d: date | str) -> dict:
    if not getattr(school.settings, "plan_periods", None):
        return {"active": False, "state": "ok", "period": None}
    return state_for_week(school, plan_week(school.settings, as_date(d)))


def unplanned_weeks(school: School, count: int = 53) -> set[int]:
    """Laufende Wochen 1 … ``count`` ohne gültigen Plan (leer, wenn keine Zeiträume eingerichtet sind)."""
    if not active(school):
        return set()
    return {w for w in range(1, count + 1) if state_for_week(school, w)["state"] != "ok"}


# ===================================================================== Vorgaben und Prüfung
def default_periods(school: School, today: Optional[date] = None) -> list[dict]:
    """1. und 2. Halbjahr des Schuljahres von ``today``: das erste endet mit der Woche des 31. Januars."""
    st = school.settings
    today = today or date.today()
    first, y, start = year_bounds(st, today)
    end_year = first + timedelta(days=7 * y - 1)
    jan = date(start.year + (1 if start.month >= 6 else 0), 1, 31)
    cut = (monday_of(jan) - first).days // 7 + 1          # Woche des 31. Januars
    cut = max(1, min(y - 1, cut)) if y > 1 else 1
    h1_end = first + timedelta(days=7 * cut - 1)
    out = [{"id": "hj1", "name": "1. Halbjahr", "date_from": start.isoformat(), "date_to": h1_end.isoformat()}]
    if y > 1:
        out.append({"id": "hj2", "name": "2. Halbjahr", "date_from": (h1_end + timedelta(days=1)).isoformat(),
                    "date_to": end_year.isoformat()})
    else:
        out[0]["date_to"] = end_year.isoformat()
    return normalize(school, out)[0]


def normalize(school: School, raw: Iterable[Any]) -> tuple[list[dict], list[str]]:
    """Prüft Zeiträume und berechnet ``from_week``/``to_week``. Liefert ``(Zeiträume, Fehlertexte)``."""
    st = school.settings
    errs: list[str] = []
    out: list[dict] = []
    ids: set[str] = set()
    raw = list(raw)
    if len(raw) > MAX_PERIODS:
        errs.append(f"Höchstens {MAX_PERIODS} Zeiträume möglich.")
        raw = raw[:MAX_PERIODS]
    year = None
    for i, r in enumerate(raw, 1):
        r = r if isinstance(r, dict) else {}
        name = str(r.get("name") or "").strip()[:60]
        label = name or f"Zeitraum {i}"
        try:
            d1, d2 = date.fromisoformat(str(r.get("date_from"))[:10]), date.fromisoformat(str(r.get("date_to"))[:10])
        except ValueError:
            errs.append(f"{label}: Bitte Beginn und Ende angeben.")
            continue
        if not name:
            errs.append(f"{label}: Bitte einen Namen angeben.")
            continue
        if d2 < d1:
            errs.append(f"{label}: Das Ende liegt vor dem Beginn.")
            continue
        f1, y1, _ = year_bounds(st, d1)
        f2, _, _ = year_bounds(st, d2)
        if f1 != f2:
            errs.append(f"{label}: Beginn und Ende müssen im selben Schuljahr liegen.")
            continue
        if year is not None and f1 != year:
            errs.append(f"{label}: Alle Zeiträume müssen im selben Schuljahr liegen.")
            continue
        year = f1
        pid = str(r.get("id") or "").strip()[:20]
        if not pid or pid in ids:
            n = 1
            while f"z{n}" in ids or any(f"z{n}" == str(x.get("id") or "") for x in raw):
                n += 1
            pid = f"z{n}"
        ids.add(pid)
        out.append({"id": pid, "name": name, "date_from": d1.isoformat(), "date_to": d2.isoformat(),
                    "from_week": plan_week(st, d1), "to_week": plan_week(st, d2)})
    out.sort(key=lambda p: (p["from_week"], p["date_from"]))
    for a, b in zip(out, out[1:]):
        if b["from_week"] <= a["to_week"]:
            errs.append(f"{a['name']} und {b['name']} überschneiden sich (Zeiträume umfassen ganze Wochen).")
    return out, errs


def restamp(school: School) -> int:
    """Setzt ``from_week``/``to_week`` der Stunden aus ihrem Zeitraum (nach Änderung der Zeiträume). Stunden eines
    unbekannten Zeitraums gelten danach wieder ohne Zeitraum. Liefert die Zahl geänderter Stunden."""
    by_id = {p["id"]: p for p in periods(school)}
    n = 0
    for le in school.lessons:
        if not le.period:
            continue
        p = by_id.get(le.period)
        lo, hi, pid = (int(p["from_week"]), int(p["to_week"]), le.period) if p else (0, 0, "")
        if (le.from_week, le.to_week, le.period) != (lo, hi, pid):
            le.from_week, le.to_week, le.period = lo, hi, pid
            n += 1
    return n


def refresh(school: School) -> None:
    """Berechnet die Wochen der Zeiträume aus den Daten neu (z. B. nach verschobenem Schuljahresbeginn)."""
    if not active(school):
        return
    fresh, errs = normalize(school, periods(school))
    if not errs:
        school.settings.plan_periods = fresh
    restamp(school)


def shift_dates(school: School, days: int) -> None:
    """Verschiebt alle Zeiträume um ``days`` Tage (Schuljahreswechsel) und berechnet die Wochen neu."""
    if not days or not active(school):
        return
    moved = []
    for p in periods(school):
        q = dict(p)
        for k in ("date_from", "date_to"):
            q[k] = (date.fromisoformat(p[k]) + timedelta(days=days)).isoformat()
        moved.append(q)
    fresh, errs = normalize(school, moved)
    if not errs:
        school.settings.plan_periods = fresh
    restamp(school)


# ===================================================================== Einrichten und Ändern
def _next_lesson_id(school: School, extra: Iterable[Lesson] = ()) -> "callable":
    used = {le.id for le in school.lessons} | {le.id for le in extra}
    top = 0
    for i in used:
        if i[:1] == "L" and i[1:].isdigit():
            top = max(top, int(i[1:]))
    state = {"n": top}

    def new() -> str:
        state["n"] += 1
        return f"L{state['n']}"

    return new


def span_weeks(p: dict) -> range:
    return range(int(p["from_week"]), int(p["to_week"]) + 1)


def restrict_spec(weeks: Optional[list], rhythm: Optional[dict], lo: int, hi: int) -> tuple[list[int], Optional[dict]]:
    """Wochenangabe auf die Wochen ``lo … hi`` begrenzen: ``(weeks, rhythm)``."""
    act = [w for w in range(lo, hi + 1) if spec_active(weeks, rhythm, w)]
    if len(act) == hi - lo + 1:
        return [], {"every": 1, "from_week": lo, "to_week": hi}
    if not act:
        return [99], None       # gilt in keiner Woche des Zeitraums: der Generator plant dafür nichts
    return wk.spec_from_weeks(act, total=wk.MAX_WEEKS + 1, last=hi)


def _widen(le: Lesson, lo: int, hi: int, course_weeks: set[int]) -> None:
    """Nach dem Generieren: deckt die Stunde alle Kurswochen des Zeitraums ab, folgt sie wieder dem Kurs."""
    mine = {w for w in range(lo, hi + 1) if spec_active(le.weeks, le.rhythm, w)}
    if mine >= course_weeks:
        le.weeks, le.rhythm = [], None


def _stamp(le: Lesson, p: dict) -> None:
    le.period, le.from_week, le.to_week = p["id"], int(p["from_week"]), int(p["to_week"])


def setup(school: School, raw: Iterable[Any], adopt: str = "all", today: Optional[date] = None) -> list[str]:
    """Speichert die Zeiträume (``school.settings.plan_periods``) und stempelt die Stunden neu.

    Erstes Einrichten (bisher ohne Zeiträume) übernimmt den vorhandenen Plan: ``adopt="all"`` kopiert ihn in jeden Zeitraum
    (Standard, nichts geht verloren), eine Kennung weist ihn nur diesem Zeitraum zu, ``"none"`` verwirft ihn nicht,
    sondern lässt ihn ohne Zeitraum (gilt weiter überall). Liefert Fehlertexte (dann bleibt alles unverändert)."""
    new, errs = normalize(school, raw)
    if errs:
        return errs
    if not new:
        return ["Mindestens ein Zeitraum ist nötig."]
    first_time = not active(school)
    if first_time and adopt not in ("all", "none") and adopt not in {p["id"] for p in new}:
        return ["Unbekannter Zeitraum für den bisherigen Plan."]
    old_ids = {p["id"] for p in periods(school)}
    school.settings.plan_periods = new
    new_ids = {p["id"] for p in new}
    if first_time:
        legacy = [le for le in school.lessons if not le.period]
        if legacy and adopt != "none":
            if adopt == "all":
                make_id = _next_lesson_id(school)
                today = today or date.today()
                home = period_for_date(school, today) or new[0]
                copies: list[Lesson] = []
                for p in new:
                    if p["id"] == home["id"]:
                        continue
                    copies += _copy_lessons(legacy, p, make_id, school)
                for le in legacy:
                    _stamp(le, home)
                school.lessons += copies
            else:
                target = next(p for p in new if p["id"] == adopt)
                for le in legacy:
                    _stamp(le, target)
    else:
        gone = old_ids - new_ids
        if gone:       # Stunden gelöschter Zeiträume entfallen (die Oberfläche hat das bestätigen lassen)
            dropped = {le.id for le in school.lessons if le.period in gone}
            school.lessons = [le for le in school.lessons if le.period not in gone]
            school.overrides = [o for o in school.overrides if o.lesson_id not in dropped]
    restamp(school)
    return []


def _copy_lessons(src: Iterable[Lesson], dst: dict, make_id, school: School) -> list[Lesson]:
    """Kopien von Stunden für den Zeitraum ``dst`` (neue Kennungen, nicht fixiert). Stunden, die in dessen Wochen nie
    stattfänden, entfallen."""
    out: list[Lesson] = []
    lo, hi = int(dst["from_week"]), int(dst["to_week"])
    courses = school.index("courses")
    for le in src:
        c = Lesson.from_dict(le.to_dict())
        c.id, c.locked = make_id(), False
        if c.rhythm and not c.weeks:
            c.rhythm = dict(c.rhythm, to_week=0)          # gleiche Taktung weiterführen (Phase bleibt)
        _stamp(c, dst)
        co = courses.get(c.course_id)
        if not any(spec_active(c.weeks, c.rhythm, w) and (co is None or spec_active(co.weeks, co.rhythm, w))
                   for w in range(lo, hi + 1)):
            continue
        out.append(c)
    return out


def copy_period(school: School, src_id: str, dst_id: str, replace: bool = False) -> dict:
    """Plan aus Zeitraum ``src_id`` in ``dst_id`` kopieren. Ohne ``replace`` nur, wenn dieser noch leer ist."""
    src, dst = get(school, src_id), get(school, dst_id)
    if src is None or dst is None:
        raise ValueError("Zeitraum unbekannt.")
    if src_id == dst_id:
        raise ValueError("Quelle und Ziel sind derselbe Zeitraum.")
    mine = lessons_of(school, dst_id)
    if mine and not replace:
        raise ValueError("Der Zeitraum hat bereits einen Plan.")
    if mine:
        gone = {le.id for le in mine}
        school.lessons = [le for le in school.lessons if le.id not in gone]
        school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
    source = lessons_of(school, src_id)
    copies = _copy_lessons(source, dst, _next_lesson_id(school), school)
    school.lessons += copies
    return {"copied": len(copies), "skipped": len(source) - len(copies)}


def clear_period(school: School, period_id: str) -> int:
    """Entfernt den Plan eines Zeitraums. Liefert die Zahl entfernter Stunden."""
    gone = {le.id for le in school.lessons if le.period == period_id}
    school.lessons = [le for le in school.lessons if le.id not in gone]
    school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
    return len(gone)


# ===================================================================== Generator
def prepare_generation(work: School, period_id: str, copy_from: str = "") -> dict:
    """Bereitet eine **Kopie** des Dokuments für den Generator vor (verändert ``work``).

    Die Kurse gelten nur noch in den Wochen des Zeitraums; Stunden sind nur die des Zeitraums (fixierte bleiben) bzw.,
    mit ``copy_from``, die Stunden des Quellzeitraums als fixierter Start. Liefert ``{"keep": [[Kurs, Tag, Beginn,
    Länge], …]}`` der Stunden, die auch im Ergebnis fixiert bleiben sollen."""
    p = get(work, period_id)
    if p is None:
        raise ValueError("Zeitraum unbekannt.")
    lo, hi = int(p["from_week"]), int(p["to_week"])
    keep_locked = [[le.course_id, le.day, le.start, le.length] for le in lessons_of(work, period_id) if le.locked]
    for c in work.courses:
        w, r = restrict_spec(c.weeks, c.rhythm, lo, hi)
        c.weeks, c.rhythm = w, r
    if copy_from:
        if get(work, copy_from) is None:
            raise ValueError("Quellzeitraum unbekannt.")
        start = _copy_lessons(lessons_of(work, copy_from), p, _next_lesson_id(work), work)
        for le in start:
            le.locked = True
        work.lessons = start
    else:
        work.lessons = lessons_of(work, period_id)
    work.overrides = []
    return {"keep": keep_locked}


def finalize(school: School, lessons: list[Lesson], period_id: str) -> list[Lesson]:
    """Macht Generator-Stunden zu Stunden des Zeitraums (verändert ``lessons``): Zeitraum und Wochenbereich setzen,
    Wochenangabe wieder dem Kurs folgen lassen, wenn die Stunde alle seine Wochen im Zeitraum abdeckt, Räume je
    Kursteil. Stunden zu unbekannten Kursen entfallen. Der Generator-Job ruft das schon vor der Auswertung auf, damit
    Vorher/Nachher denselben Plan vergleichen wie später das Übernehmen."""
    p = get(school, period_id)
    if p is None:
        raise ValueError("Zeitraum unbekannt.")
    lo, hi = int(p["from_week"]), int(p["to_week"])
    courses = school.index("courses")
    out: list[Lesson] = []
    for le in lessons:
        c = courses.get(le.course_id)
        if c is None:
            continue
        cw = {w for w in range(lo, hi + 1) if spec_active(c.weeks, c.rhythm, w)}
        _widen(le, lo, hi, cw)
        _stamp(le, p)
        n = len(c.parts)
        le.rooms = (list(le.rooms) + [None] * n)[:n]
        out.append(le)
    return out


def merge_generated(school: School, new: list[Lesson], period_id: str, keep: Iterable[Iterable[Any]] = ()) -> dict:
    """Übernimmt das Generator-Ergebnis als Plan des Zeitraums (verändert ``school``): die bisherigen Stunden des
    Zeitraums werden ersetzt, alle anderen bleiben unberührt. ``keep`` = Stunden (Kurs, Tag, Beginn, Länge), die
    fixiert bleiben; alle übrigen Stunden des Ergebnisses sind frei (auch die eines Start-Plans)."""
    if get(school, period_id) is None:
        raise ValueError("Zeitraum unbekannt.")
    keep_keys = {tuple(k) for k in keep}
    gone = {le.id for le in school.lessons if le.period == period_id}
    rest = [le for le in school.lessons if le.id not in gone]
    make_id = _next_lesson_id(school)
    out = finalize(school, new, period_id)
    for le in out:
        le.id = make_id()
        le.locked = le.locked and (le.course_id, le.day, le.start, le.length) in keep_keys
    school.lessons = rest + out
    if gone:
        school.overrides = [o for o in school.overrides if o.lesson_id not in gone]
    return {"lessons": len(out), "replaced": len(gone)}


def default_target(school: School, today: Optional[date] = None) -> Optional[str]:
    """Voreinstellung im Generator: der laufende oder der nächste Zeitraum ohne eigenen Plan, sonst der laufende."""
    ps = periods(school)
    if not ps:
        return None
    today = today or date.today()
    w = plan_week(school.settings, today)
    own = {le.period for le in school.lessons}
    for p in ps:
        if int(p["to_week"]) >= w and p["id"] not in own:
            return p["id"]
    cur = period_for_week(school, w)
    return (cur or ps[-1])["id"]


def in_range(le: Lesson, week: int) -> bool:
    return lesson_in_range(le, week)
