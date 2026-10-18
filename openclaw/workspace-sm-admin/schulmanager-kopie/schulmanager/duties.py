"""Pausenaufsichten: faire Planung und Vertretung bei Abwesenheit.

* ``generate_duties(school)`` verteilt die benötigten Aufsichten (``school.areas`` ×
  ``settings.breaks`` × Schulöffnungstage × Wochenvarianten) gleichmäßig nach Deputat. Bevorzugt
  werden Lehrkräfte, die direkt vor oder nach der Pause am Standort des Bereichs
  unterrichten; Lehrkräfte, die direkt angrenzend am anderen Standort sind, nie.
* ``duty_replacements(school, day, plan_busy)`` liefert Vertretungs-Entries
  (``kind: "aufsicht"``) für Aufsichten abwesender Lehrkräfte; wird von
  ``substitution.compute_day_plan`` aufgerufen.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Optional

from . import weeks as wk
from .calendar_utils import as_date, break_time
from .models import Duty, School, Teacher


def _occupancy_at(school: School, idx: wk.ActiveIndex, monday: date) -> dict[tuple[str, int], dict[int, str]]:
    """Belegung je (Lehrkraft, Tag) in der Woche von ``monday``: ``{stunde: standort}`` (zentrale Aktiv-Logik)."""
    courses = school.index("courses")
    rooms = school.index("rooms")
    classes = school.index("classes")
    occ: dict[tuple[str, int], dict[int, str]] = defaultdict(dict)
    for les in school.lessons:
        c = courses.get(les.course_id)
        if c is None or not idx.in_week(les, c, monday):
            continue
        class_site = next((classes[x].site for x in c.classes if x in classes and classes[x].site), "")
        for i, part in enumerate(c.parts):
            if not part.teacher:
                continue
            room = les.rooms[i] if i < len(les.rooms) else None
            site = rooms[room].site if room in rooms and rooms[room].site else class_site
            slot = occ[(part.teacher, les.day)]
            for p in range(les.start, les.start + max(1, les.length)):
                slot[p] = site
    return occ


def _blocked(t: Teacher, d: int, p: int, real_week: Optional[int] = None) -> bool:
    return any(r.matches(real_week, d, p) for r in t.unavailable)


def duty_variants(school: School, today: Optional[date] = None) -> tuple[wk.Horizon, list[list[int]]]:
    """Gruppen realer Wochen mit gleichen Bedingungen für Aufsichten (Wochenvarianten): Wochen mit denselben
    Sperrzeiten der Lehrkräfte und denselben Unterrichtsblöcken bilden eine Gruppe."""
    hz = wk.Horizon(school, today)
    sets: list[frozenset[int]] = []
    for t in school.teachers:
        for r in t.unavailable:
            if r.weeks or r.rhythm or r.valid_week:
                sets.append(hz.spec_members(r))
    courses = school.index("courses")
    for les in school.lessons:
        members = hz.lesson_members(les, courses.get(les.course_id))
        if len(members) < len(hz):
            sets.append(members)
    return hz, wk.group_weeks(len(hz), sets)


MAX_PER_WEEK = 3                     # Richtwert: höchstens so viele Pausenaufsichten je Lehrkraft und Woche


def generate_duties(school: School, today: Optional[date] = None) -> list[Duty]:
    """Erzeugt einen fairen Aufsichtsplan (ersetzt ``school.duties`` NICHT – Aufrufer setzt ihn).

    Je Bereich, Pause und Schulöffnungstag werden ``area.needed`` Lehrkräfte eingeteilt, und zwar je Wochenvariante
    (Gruppe realer Wochen mit gleichen Bedingungen). Kriterien (in dieser Reihenfolge):
    höchstens eine Aufsicht pro Tag, gleichmäßige Last relativ zum Deputat, Unterricht direkt vor/nach der Pause am
    Standort, Stabilität zwischen den Varianten. Nicht besetzbare Aufsichten erscheinen mit ``teacher=None``.
    ``Duty.weeks``/``Duty.rhythm`` nennen die laufenden Wochen der Variante (leer = jede Woche).
    """
    from .calendar_utils import open_days
    st = school.settings
    P = max(1, st.periods)
    teachers = sorted(school.teachers, key=lambda t: t.id)
    hz, variants = duty_variants(school, today)
    idx = wk.ActiveIndex(school)
    V = len(variants)
    reps = [v[0] for v in variants]
    occs = [_occupancy_at(school, idx, hz.mondays[i]) for i in reps]
    sps = [site_periods_at(school, idx, hz.mondays[i], occs[k]) for k, i in enumerate(reps)]
    mult = [len(v) / max(1, len(hz)) * V for v in variants]
    weight = {t.id: max(1, t.max_hours or 25) / 25 for t in teachers}
    load: dict[str, float] = defaultdict(float)
    per_day: dict[tuple[str, int, int], int] = defaultdict(int)
    chosen: dict[tuple[int, int, int, str], list[Optional[str]]] = {}
    areas = sorted(school.areas, key=lambda a: (-a.needed, a.id))
    days = open_days(school)

    for v in range(V):
        rep = reps[v]
        real = hz.real[rep]
        for d in days:
            for b, brk in enumerate(st.breaks):
                a = int(brk.get("after", -1))
                if a < 0 or a + 1 >= P:
                    continue
                taken: set[str] = set()
                for area in areas:
                    prev = set(chosen.get((0, d, b, area.id), [])) if v > 0 else set()
                    picks: list[Optional[str]] = []
                    if not break_relevant(sps[v], d, area.site, a):
                        chosen[(v, d, b, area.id)] = []     # keine Pause an dem Standort (z. B. kein Abendunterricht)
                        continue
                    for _ in range(max(0, area.needed)):
                        best: Optional[tuple[float, str]] = None
                        for t in teachers:
                            if t.id in taken:
                                continue
                            if t.sites and area.site and area.site not in t.sites:
                                continue
                            if _blocked(t, d, a, real) or _blocked(t, d, a + 1, real):
                                continue
                            o = occs[v].get((t.id, d))
                            if not o:
                                continue  # an dem Tag nicht im Haus
                            before, after = o.get(a), o.get(a + 1)
                            if area.site and ((before and before != area.site) or (after and after != area.site)):
                                continue  # direkt angrenzend am anderen Standort
                            sites_today = set(o.values())
                            if area.site and area.site not in sites_today:
                                continue
                            if before or after:
                                adj = 0
                            elif min(o) <= a < max(o):
                                adj = 1
                            else:
                                adj = 2
                            score = (40 * per_day[(t.id, v, d)] + 10 * load[t.id] / weight[t.id] + 4 * adj
                                     - (3 if t.id in prev else 0))
                            # mehr als MAX_PER_WEEK Aufsichten pro Woche nur, wenn sonst niemand kann
                            if (load[t.id] + mult[v]) / max(1, V) > MAX_PER_WEEK:
                                score += 1000
                            if best is None or (score, t.id) < best:
                                best = (score, t.id)
                        if best is None:
                            picks.append(None)
                            continue
                        tid = best[1]
                        taken.add(tid)
                        load[tid] += mult[v]
                        per_day[(tid, v, d)] += 1
                        picks.append(tid)
                    chosen[(v, d, b, area.id)] = picks

    duties: list[Duty] = []
    for d in days:
        for b in range(len(st.breaks)):
            for area in sorted(school.areas, key=lambda a: a.id):
                lists = [chosen.get((v, d, b, area.id)) for v in range(V)]
                if any(x is None for x in lists):
                    continue
                n = 0

                def add(tid: Optional[str], variant: Optional[int]) -> None:
                    nonlocal n
                    n += 1
                    weeks, rhythm = hz.to_spec(variants[variant]) if variant is not None else ([], None)
                    duties.append(Duty(id=f"AU-{area.id}-{d}-{b}-{n}", area=area.id, day=d, break_index=b,
                                       teacher=tid, weeks=weeks, rhythm=rhythm))

                if V == 1:
                    for tid in lists[0]:
                        add(tid, None)
                    continue
                common = set.intersection(*[{x for x in lst if x} for lst in lists])
                for tid in sorted(common):
                    add(tid, None)
                for v, lst in enumerate(lists):
                    for tid in lst:
                        if tid not in common:
                            add(tid, v)
    return duties


def duty_load(school: School, today: Optional[date] = None) -> dict[str, float]:
    """Aufsichten je Lehrkraft pro Woche (über die Wochen des Schuljahres gemittelt)."""
    out: dict[str, float] = defaultdict(float)
    hz: Optional[wk.Horizon] = None
    for d in school.duties:
        if not d.teacher:
            continue
        if d.weeks or d.rhythm:
            hz = hz or wk.Horizon(school, today)
            out[d.teacher] += len(hz.spec_members(d)) / max(1, len(hz))
        else:
            out[d.teacher] += 1.0
    return dict(out)


def active_duties(school: School, day: date | str) -> list[Duty]:
    """Aufsichten, die am Datum ``day`` stattfinden (Wochentag, Wochen bzw. Rhythmus)."""
    d0 = as_date(day)
    return [d for d in school.duties if wk.duty_active_on(school, d, d0)]


def duty_conflict(site: str, a: int, busy_t: dict[int, str], presence_t: list[int], absent_t: set[int]) -> Optional[str]:
    """Warum die Lehrkraft die Aufsicht (nach Stunde ``a`` am Standort ``site``) so nicht übernehmen kann – oder ``None``.
    (Hat sie an dem Tag gar keinen Unterricht, gilt das nicht als Konflikt: sie kommt dann eigens – die Übersicht
    weist darauf hin.)

    ``busy_t`` = ``{stunde: standort}`` ihrer Einsätze an dem Tag, ``presence_t`` = Stunden im Haus (inkl. freigesetzter),
    ``absent_t`` = Stunden, in denen sie fehlt."""
    if a in absent_t or a + 1 in absent_t:
        return "abwesend"
    if site and (presence_t or busy_t):
        before, after = busy_t.get(a), busy_t.get(a + 1)
        if (before and before != site) or (after and after != site):
            return "wechselt direkt vor/nach der Pause den Standort"
        sites = {x for x in busy_t.values() if x}
        if sites and site not in sites:
            return "an dem Tag nicht am Standort der Aufsicht"
    return None


def break_relevant(site_periods: dict[tuple[int, str], set[int]], day: int, site: str, a: int) -> bool:
    """Gibt es zur Pause nach Stunde ``a`` am Standort ``site`` überhaupt jemanden zu beaufsichtigen?

    Ja, wenn am Standort (``site`` leer = irgendwo) in Stunde ``a`` oder ``a + 1`` Unterricht ist – also keine
    Abendpause ohne Abendunterricht und keine Pause an einem Standort, an dem zu der Zeit niemand ist."""
    if site:
        ps = site_periods.get((day, site), set())
    else:
        ps = set().union(*[v for (dd, _), v in site_periods.items() if dd == day]) if site_periods else set()
    return a in ps or a + 1 in ps


def site_periods_at(school: School, idx: wk.ActiveIndex, monday: date,
                    occ: Optional[dict[tuple[str, int], dict[int, str]]] = None) -> dict[tuple[int, str], set[int]]:
    """``{(tag, standort): {stunden mit Unterricht}}`` der Woche von ``monday``."""
    occ = occ if occ is not None else _occupancy_at(school, idx, monday)
    out: dict[tuple[int, str], set[int]] = defaultdict(set)
    for (_tid, day), per in occ.items():
        for p, site in per.items():
            out[(day, site or "")].add(p)
    return out


def duty_replacements(school: School, day: date | str, plan_busy: dict[str, Any]) -> list[dict]:
    """Ersatz für Pausenaufsichten abwesender (oder nicht eingeteilter) Lehrkräfte.

    ``plan_busy`` (von der Vertretungs-Engine):
      ``weekday`` – Wochentag,
      ``busy`` – ``{lehrer: {stunde: standort}}`` Einsätze nach der Vertretungsplanung,
      ``presence`` – ``{lehrer: [stunden]}`` Stunden im Haus (inkl. freigesetzter),
      ``absent`` – ``{lehrer: [stunden]}`` abwesende Stunden,
      optional ``subs_today``/``history`` – Vertretungszählung, ``overrides`` – ``{duty_id: Override}``.
    Liefert Entries ``kind: "aufsicht"`` (Format wie Vertretungs-Entries, Zusatzfelder
    ``duty_id``, ``area``, ``area_name``, ``break_index``, ``break_name``).
    """
    d0 = as_date(day)
    st = school.settings
    wd = int(plan_busy.get("weekday", d0.weekday()))
    real = wk.real_week(school, d0)
    busy: dict[str, dict[int, str]] = plan_busy.get("busy") or {}
    presence: dict[str, list[int]] = plan_busy.get("presence") or {}
    absent = {k: set(v) for k, v in (plan_busy.get("absent") or {}).items()}
    subs_today: dict[str, int] = plan_busy.get("subs_today") or {}
    overrides: dict[str, Any] = plan_busy.get("overrides") or {}
    teachers = school.index("teachers")
    areas = school.index("areas")
    load = duty_load(school)
    iso = d0.isoformat()

    todays = sorted(active_duties(school, d0), key=lambda d: (d.break_index, d.area, d.id))
    taken: set[tuple[str, int]] = set()

    def is_absent(tid: str, a: int) -> bool:
        s = absent.get(tid)
        return bool(s) and (a in s or a + 1 in s)

    def conflict_of(d: Duty, a: int) -> Optional[str]:
        """Konflikt der eingeteilten Lehrkraft (abwesend, anderer Standort, nicht im Haus …) – ``None`` = alles gut."""
        if not d.teacher or d.teacher not in teachers:
            return None
        area = areas.get(d.area)
        pres = presence.get(d.teacher) or []
        tb = busy.get(d.teacher, {})
        if "busy" not in plan_busy and "presence" not in plan_busy:
            return "abwesend" if is_absent(d.teacher, a) else None       # ohne Einsatzdaten nur Abwesenheit prüfen
        return duty_conflict(area.site if area else "", a, tb, pres, absent.get(d.teacher, set()))

    for d in todays:
        if d.teacher and d.teacher in teachers and 0 <= d.break_index < len(st.breaks):
            a = int(st.breaks[d.break_index].get("after", -1))
            if conflict_of(d, a) is None and d.id not in overrides:
                taken.add((d.teacher, d.break_index))

    replaced_today: dict[str, int] = defaultdict(int)
    entries: list[dict] = []
    for d in todays:
        if not 0 <= d.break_index < len(st.breaks):
            continue
        brk = st.breaks[d.break_index]
        a = int(brk.get("after", -1))
        area = areas.get(d.area)
        site = area.site if area else ""
        ov = overrides.get(d.id)
        conflict = conflict_of(d, a)
        missing = not d.teacher or d.teacher not in teachers or conflict is not None
        if not missing and ov is None:
            continue
        base = {
            "id": f"{iso}:{d.id}:{a}:0", "date": iso, "period": a,
            "period_label": brk.get("name") or f"Pause nach der {a + 1}. Stunde",
            "time": break_time(st, brk), "kind": "aufsicht", "classes": [], "subject": None,
            "teacher": d.teacher, "substitute": None, "room": area.name if area else d.area, "new_room": None,
            "moved_from": None, "lesson_id": None, "part": 0, "note": "", "warning": False, "manual": False,
            "site": site, "course_id": None, "duty_id": d.id, "area": d.area, "area_name": area.name if area else d.area,
            "break_index": d.break_index, "break_name": brk.get("name", ""),
        }
        if ov is not None:
            action = getattr(ov, "action", "substitute")
            if action == "keep" and not missing:
                continue
            if action == "cancel":
                entries.append({**base, "manual": True, "note": ov.note or "Aufsicht entfällt (manuell)"})
                continue
            if action == "substitute" and ov.teacher:
                taken.add((ov.teacher, d.break_index))
                entries.append({**base, "manual": True, "substitute": ov.teacher,
                                "note": ov.note or "Aufsichtsvertretung (manuell)"})
                continue
        best: Optional[tuple[float, str, str]] = None
        for t in sorted(teachers.values(), key=lambda t: t.id):
            tid = t.id
            if tid == d.teacher or (tid, d.break_index) in taken or is_absent(tid, a):
                continue
            if any(r.matches(real, wd, a) and r.matches(real, wd, a + 1) for r in t.unavailable):
                continue
            if t.sites and site and site not in t.sites:
                continue
            tb = busy.get(tid, {})
            before, after = tb.get(a), tb.get(a + 1)
            if site and ((before and before != site) or (after and after != site)):
                continue
            pres = presence.get(tid) or sorted(tb)
            if before or after:
                rank, why = 0, "Unterricht direkt vor/nach der Pause"
            elif pres and min(pres) <= a < max(pres):
                rank, why = 1, "ohnehin im Haus"
            elif pres:
                rank, why = 3, "müsste früher kommen/länger bleiben"
            else:
                rank, why = 6, "müsste extra kommen"
            score = (rank * 10 + 25 * replaced_today[tid] + 4 * subs_today.get(tid, 0)
                     + 6 * load.get(tid, 0.0) * 25 / max(5, t.max_hours or 25))
            if best is None or (score, tid) < (best[0], best[1]):
                best = (score, tid, why)
        why_missing = conflict if d.teacher in teachers else "unbesetzt"
        if best is None:
            entries.append({**base, "warning": True, "conflict": why_missing,
                            "note": "Keine Lehrkraft für die Aufsicht frei – bitte manuell regeln"
                                    + (f" ({why_missing})" if why_missing else "")})
            continue
        tid = best[1]
        taken.add((tid, d.break_index))
        replaced_today[tid] += 1
        who = teachers[d.teacher].name if d.teacher in teachers else "unbesetzt"
        entries.append({**base, "substitute": tid, "conflict": why_missing, "reason": best[2],
                        "note": f"Aufsicht für {who} ({best[2]})"
                                + (f" – {why_missing}" if why_missing and why_missing != "abwesend" else "")})
    return entries


# ===================================================================== Übersicht (Wochenansicht der Aufsichten)
def duty_overview(school: School, day: date | str, history: Optional[dict[str, int]] = None) -> dict[str, Any]:
    """Aufsichtsplan der Woche, lesbar aufbereitet: Tag × Pause × Bereich mit Namen, Standort der Lehrkraft und Konflikten.

    ``day`` = beliebiger Tag der Woche. Ergebnis::

        {"week_start", "sites": [{id, name}], "days": [{
            "date", "weekday", "open": bool, "reason": str|None,
            "breaks": [{"index", "name", "time", "after", "cells": [{
                "area", "area_name", "site", "needed",
                "duties": [{"duty_id", "teacher", "teacher_name", "status": ok|konflikt|vertreten|offen,
                            "sites_today": [standort-ids], "first_site", "note", "substitute", "substitute_name",
                            "substitute_reason"}],
                "missing": int}]}]}]}

    Nur Pausen, die es am Standort des Bereichs wirklich gibt (Unterricht direkt vor oder nach der Pause am Standort); bestehende
    Einteilungen in anderen Pausen bleiben sichtbar. Konflikte und Ersatz entsprechen exakt der Vertretungsplanung
    (``duty_replacements``): abwesende Lehrkraft, Standortwechsel direkt um die Pause, an dem Tag nicht am Standort,
    nicht im Haus.
    """
    from . import substitution as sub
    from .calendar_utils import is_school_day, monday_of, open_days
    d0 = as_date(day)
    monday = monday_of(d0)
    st = school.settings
    teachers = school.index("teachers")
    areas = sorted(school.areas, key=lambda a: (a.site, a.name, a.id))
    idx = wk.ActiveIndex(school)
    occ = _occupancy_at(school, idx, monday)
    sp = site_periods_at(school, idx, monday, occ)
    days_out: list[dict] = []
    hist = dict(history or {})
    for wd in sorted(set(open_days(school))):
        dd = monday + timedelta(days=wd)
        ok, reason = is_school_day(school, dd)
        info: dict[str, Any] = {"date": dd.isoformat(), "weekday": wd, "open": bool(ok), "reason": None if ok else reason,
                                "breaks": []}
        days_out.append(info)
        if not ok:
            continue
        plan = sub.compute_day_plan(school, dd, hist)
        sub._add_counts(hist, plan)
        repl = {e.get("duty_id"): e for e in plan.entries if e.get("kind") == "aufsicht"}
        absent_periods: dict[str, set[int]] = {}
        for det in plan.absent_teacher_details:
            absent_periods[det["teacher"]] = set(range(st.periods)) if det.get("full_day") or not det.get("periods") \
                else set(det["periods"])
        active = active_duties(school, dd)
        by_cell: dict[tuple[str, int], list[Duty]] = defaultdict(list)
        for d in active:
            by_cell[(d.area, d.break_index)].append(d)
        for b, brk in enumerate(st.breaks):
            a = int(brk.get("after", -1))
            cells: list[dict] = []
            for area in areas:
                duties = sorted(by_cell.get((area.id, b), []), key=lambda x: x.id)
                if not duties and not break_relevant(sp, wd, area.site, a):
                    continue
                rows = []
                for d in duties:
                    t = teachers.get(d.teacher) if d.teacher else None
                    e = repl.get(d.id)
                    per = occ.get((d.teacher, wd), {}) if d.teacher else {}
                    sites_today = sorted({x for x in per.values() if x})
                    first_site = per[min(per)] if per else ""
                    row: dict[str, Any] = {
                        "duty_id": d.id, "teacher": d.teacher if t else None, "teacher_name": t.name if t else "",
                        "sites_today": sites_today, "first_site": first_site or "", "substitute": None,
                        "substitute_name": "", "substitute_reason": "", "note": "", "status": "ok"}
                    if not t:
                        row["status"] = "offen"
                    elif a in absent_periods.get(d.teacher, set()) or a + 1 in absent_periods.get(d.teacher, set()):
                        row["status"] = "vertreten" if e and e.get("substitute") else "konflikt"
                        row["note"] = "abwesend"
                    elif e is not None:
                        row["status"] = "vertreten" if e.get("substitute") else "konflikt"
                        row["note"] = e.get("conflict") or e.get("note") or ""
                    elif not per:
                        row["status"], row["note"] = "hinweis", "kein Unterricht an dem Tag – kommt eigens"
                    if e is not None:
                        sid = e.get("substitute")
                        if sid:
                            row["substitute"] = sid
                            row["substitute_name"] = teachers[sid].name if sid in teachers else sid
                            row["substitute_reason"] = e.get("reason") or ""
                        if e.get("manual"):
                            row["note"] = e.get("note") or row["note"]
                    rows.append(row)
                n_ok = sum(1 for r in rows if r["teacher"] and r["status"] in ("ok", "vertreten"))
                cells.append({"area": area.id, "area_name": area.name, "site": area.site, "needed": area.needed,
                              "duties": rows, "missing": max(0, area.needed - n_ok)})
            if cells:
                info["breaks"].append({"index": b, "name": brk.get("name") or f"Pause {b + 1}", "after": a,
                                       "time": break_time(st, brk), "cells": cells})
    return {"week_start": monday.isoformat(), "sites": [{"id": s.id, "name": s.name} for s in school.sites],
            "days": days_out}
