"""Umrechnung älterer Planungsdokumente auf das 52-Wochen-System.

Ältere Dokumente kennen einen Schul-Wochenzyklus (Felder ``cycle_weeks``, ``cycle_start_week``, ``cycle_shifts`` in
den Einstellungen, ``cycle_weeks``/``cycle_start_week`` je Klasse) und speichern ``weeks``-Listen als 0-basierte
Zykluswochen. Das Zielmodell kennt nur laufende Wochen 1 … 52 (53): jede Woche, ausgewählte Wochen oder einen
Rhythmus (``weeks`` bzw. ``rhythm``). ``migrate_document`` rechnet ein Wörterbuch (``School.to_dict``-Form) dafür
verlustfrei um:

* Zykluswoche *i* im Zyklus *n* mit Start *s* → ``rhythm = {"every": n, "from_week": ((s + i − 1) mod n) + 1}``;
* mehrere Zykluswochen (oder Verschiebungen) → die ausgewählten laufenden Wochen als Liste;
* alle Zykluswochen → leer (= jede Woche).

Die Funktion ist idempotent: ohne die alten Felder ändert sie nichts. Alte Anfrage-Felder (``cycle_weeks`` usw.) nimmt
``strip_legacy_fields`` für die Server-Routen tolerant entgegen.
"""
from __future__ import annotations

import copy
from datetime import date, timedelta
from typing import Any, Callable, Iterable, Optional

MAX_WEEK = 53
LEGACY_SETTINGS = ("cycle_weeks", "cycle_start_week", "cycle_shifts")
LEGACY_CLASS = ("cycle_weeks", "cycle_start_week")
#: Felder, die ältere Clients noch senden dürfen und die ohne Wirkung ignoriert werden
LEGACY_REQUEST_FIELDS = ("cycle_weeks", "cycle_start_week", "cycle_shifts", "cycle_own", "week_label", "week_labels")


def strip_legacy_fields(data: dict) -> dict:
    """Entfernt veraltete Zyklusfelder aus einem Request-Wörterbuch (in place) und liefert es zurück."""
    if isinstance(data, dict):
        for k in LEGACY_REQUEST_FIELDS:
            data.pop(k, None)
    return data


def _parse(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


# ------------------------------------------------------------------ alte Zykluswoche je laufender Woche
def _old_phase(st: dict, first: date, n: int, start: int, shifts: Optional[list], iso: bool) -> Callable[[int], int]:
    """``k(L)`` = alte Zykluswoche (0-basiert) der laufenden Woche ``L`` (1-basiert) im Schuljahr ab ``first``."""
    def ref(monday: date, no: int) -> int:
        return monday.isocalendar()[1] if iso else no

    shift_pts: list[tuple[date, int]] = []
    for sh in shifts or []:
        if not isinstance(sh, dict):
            continue
        sd = _parse(sh.get("date"))
        try:
            k = int(sh.get("cycle_week") or 1)
        except (TypeError, ValueError):
            continue
        if sd is not None:
            shift_pts.append((_monday(sd), k))

    def phase(no: int) -> int:
        if n <= 1:
            return 0
        monday = first + timedelta(days=7 * (no - 1))
        s_eff = start
        best: Optional[tuple[date, int]] = None
        for sm, k in shift_pts:
            if sm <= monday and (best is None or sm >= best[0]):
                best = (sm, k)
        if best is not None:
            no_s = (best[0] - first).days // 7 + 1
            s_eff = ref(best[0], no_s) - (best[1] - 1)
        return (ref(monday, no) - s_eff) % n

    return phase


def weeks_to_spec(weeks: Iterable[int], n: int, phase: Callable[[int], int]) -> tuple[list[int], Optional[dict]]:
    """Wochenliste im Zyklus ``n`` (0-basiert, Phase ``phase``) → ``(weeks, rhythm)`` in laufenden Wochen."""
    ws = {int(w) for w in weeks if isinstance(w, int) and not isinstance(w, bool) and 0 <= w < n}
    if not ws or len(ws) >= n:
        return [], None
    running = [no for no in range(1, MAX_WEEK + 1) if phase(no) in ws]
    if not running:
        return [], None
    if len(ws) == 1 and n > 1 and running == list(range(running[0], MAX_WEEK + 1, n)):
        return [], {"every": n, "from_week": running[0], "to_week": 0}
    return running, None


# ------------------------------------------------------------------ Dokument
def is_legacy(data: dict) -> bool:
    st = data.get("settings") if isinstance(data, dict) else None
    return isinstance(st, dict) and any(k in st for k in LEGACY_SETTINGS)


def migrate_document(data: dict) -> dict:
    """Altes Dokument (Zykluswochen) → neues Dokument (laufende Wochen). Liefert eine umgerechnete Kopie; Dokumente
    ohne die alten Felder kommen unverändert zurück."""
    if not is_legacy(data):
        return data
    from .calendar_utils import year_bounds
    from .models import Settings

    data = copy.deepcopy(data)
    st_raw = data["settings"]
    st = Settings.from_dict({k: v for k, v in st_raw.items() if k not in LEGACY_SETTINGS})
    n_school = max(1, int(st_raw.get("cycle_weeks") or 1))
    s_school = int(st_raw.get("cycle_start_week") or 1)
    shifts = st_raw.get("cycle_shifts") or []
    iso = st_raw.get("week_numbering", "school_year") == "iso"
    base = _parse(st_raw.get("school_year_start")) or _parse(st_raw.get("cycle_start")) or date(2026, 8, 31)
    first, _, _ = year_bounds(st, base)

    school_phase = _old_phase(st_raw, first, n_school, s_school, shifts, iso)
    classes = {c.get("id"): c for c in data.get("classes") or [] if isinstance(c, dict)}

    def class_cycle(cid: Any) -> tuple[int, int, bool]:
        c = classes.get(cid) or {}
        n = int(c.get("cycle_weeks") or 0)
        if n > 0:
            return n, int(c.get("cycle_start_week") or 1), True
        return n_school, s_school, False

    def class_phase(cid: Any) -> tuple[int, Callable[[int], int]]:
        n, s, own = class_cycle(cid)
        if not own:
            return n_school, school_phase
        return n, _old_phase(st_raw, first, n, s, None, iso)

    def course_phase(course: Optional[dict]) -> tuple[int, Callable[[int], int]]:
        cycles = {class_cycle(cid) for cid in (course or {}).get("classes") or []}
        if len(cycles) == 1:
            cid = next(iter((course or {}).get("classes")))
            return class_phase(cid)
        return n_school, school_phase

    def convert(obj: dict, n: int, phase: Callable[[int], int]) -> None:
        if not isinstance(obj, dict):
            return
        if obj.get("rhythm"):
            obj["weeks"] = []
            return
        weeks, rhythm = weeks_to_spec(obj.get("weeks") or [], n, phase)
        obj["weeks"] = weeks
        if rhythm:
            obj["rhythm"] = rhythm

    for c in data.get("classes") or []:
        n, ph = class_phase(c.get("id"))
        for r in c.get("unavailable") or []:
            convert(r, n, ph)
    for t in data.get("teachers") or []:
        for key in ("unavailable", "wishes", "time_windows"):
            for r in t.get(key) or []:
                convert(r, n_school, school_phase)
    courses = {c.get("id"): c for c in data.get("courses") or [] if isinstance(c, dict)}
    for c in data.get("courses") or []:
        n, ph = course_phase(c)
        convert(c, n, ph)
    for les in data.get("lessons") or []:
        n, ph = course_phase(courses.get(les.get("course_id")))
        convert(les, n, ph)
    for d in data.get("duties") or []:
        convert(d, n_school, school_phase)
    for c in data.get("classes") or []:
        for k in LEGACY_CLASS:
            c.pop(k, None)
    for k in LEGACY_SETTINGS:
        st_raw.pop(k, None)
    return data


# ------------------------------------------------------------------ Klassenstufen-Nummern → Jahrgänge
def grade_profiles_preview(school) -> dict:
    """Vorschau der Umstellung „Stundentafel je Klassenstufen-Nummer“ → Jahrgänge (``GradeProfile``):
    je Stufe, die eine Tafel über ``grades`` nennt oder die Klassen ohne Jahrgang hat, ein Jahrgang. Liefert
    ``{"pending": bool, "profiles": [{id, name, grade, curriculum, curriculum_name, classes, conflict}],
    "classes": n}``. Nichts wird geändert."""
    existing_ids = {p.id for p in school.grade_profiles}
    by_grade_profile = {p.grade: p for p in school.grade_profiles if p.grade is not None}
    cur_by_grade: dict[int, list] = {}
    for cur in school.curricula:
        if cur.classes:
            continue
        for g in cur.grades:
            cur_by_grade.setdefault(g, []).append(cur)
    classes_by_grade: dict[int, list[str]] = {}
    for cls in school.classes:
        if not cls.profile:
            classes_by_grade.setdefault(cls.grade, []).append(cls.id)
    out = []
    n_classes = 0
    for g in sorted(set(cur_by_grade) | set(classes_by_grade)):
        curs = cur_by_grade.get(g, [])
        cls_ids = classes_by_grade.get(g, [])
        if g in by_grade_profile:
            # Jahrgang mit dieser Stufe existiert schon: nur noch Klassen ohne Jahrgang dort einsortieren
            if not cls_ids:
                continue
            p = by_grade_profile[g]
            out.append({"id": p.id, "name": p.name, "grade": g, "curriculum": p.curriculum, "exists": True,
                        "curriculum_name": next((c.name for c in school.curricula if c.id == p.curriculum), None),
                        "classes": cls_ids, "conflict": False, "candidates": []})
            n_classes += len(cls_ids)
            continue
        if not curs and not cls_ids:
            continue
        pid = f"JG{g}"
        k = 2
        while pid in existing_ids:
            pid = f"JG{g}-{k}"
            k += 1
        cur = curs[0] if len(curs) == 1 else None
        out.append({"id": pid, "name": f"Jahrgang {g}", "grade": g,
                    "curriculum": cur.id if cur else None, "curriculum_name": cur.name if cur else None,
                    "classes": cls_ids, "conflict": len(curs) > 1, "exists": False,
                    "candidates": [c.id for c in curs]})
        n_classes += len(cls_ids)
    pending = any(not p["exists"] for p in out) or n_classes > 0
    return {"pending": pending, "profiles": out, "classes": n_classes}


def migrate_grade_profiles(school) -> dict:
    """Führt :func:`grade_profiles_preview` aus: legt die Jahrgänge an, ordnet die Klassen zu und leert die
    ``grades``-Listen der Stundentafeln (bei Konflikt – mehrere Tafeln je Stufe – bleibt die Stufe unverändert
    und der Jahrgang bekommt keine Tafel). Mutiert ``school``; liefert die Vorschau mit ``applied=True``."""
    from .models import GradeProfile
    preview = grade_profiles_preview(school)
    index = {p.id: p for p in school.grade_profiles}
    for row in preview["profiles"]:
        if row["exists"]:
            prof = index[row["id"]]
        else:
            prof = GradeProfile(id=row["id"], name=row["name"], short=str(row["grade"]), grade=row["grade"],
                                curriculum=row["curriculum"])
            school.grade_profiles.append(prof)
            index[prof.id] = prof
        for cid in row["classes"]:
            for cls in school.classes:
                if cls.id == cid:
                    cls.profile = prof.id
        if not row["conflict"]:
            for cur in school.curricula:
                if not cur.classes and row["grade"] in cur.grades:
                    cur.grades = [g for g in cur.grades if g != row["grade"]]
    preview["applied"] = True
    return preview


def migrate_profile_payload(payload: dict) -> dict:
    """Offener Profilantrag aus der Zeit des Wochenzyklus (Feld ``cycle_weeks`` im Antrag) → laufende Wochen.

    Die Wochen der Zeitfenster und Wünsche zählten im Zyklus der Schule zum Zeitpunkt des Einreichens; sie werden mit
    Zykluswoche 1 = Schulwoche 1 umgerechnet (Zykluswoche *i* → „jede *n*. Woche ab Woche *i*+1“)."""
    if not isinstance(payload, dict) or "cycle_weeks" not in payload:
        return payload
    n = max(1, int(payload.get("cycle_weeks") or 1))
    out = {k: v for k, v in payload.items() if k != "cycle_weeks"}
    for key in ("time_windows", "wishes"):
        items = []
        for item in payload.get(key) or []:
            if not isinstance(item, dict) or item.get("rhythm") or not item.get("weeks"):
                items.append(item)
                continue
            weeks, rhythm = weeks_to_spec(item["weeks"], n, lambda L, n=n: (L - 1) % n)
            new = {**item, "weeks": weeks}
            if rhythm:
                new["rhythm"] = rhythm
            items.append(new)
        out[key] = items
    return out
