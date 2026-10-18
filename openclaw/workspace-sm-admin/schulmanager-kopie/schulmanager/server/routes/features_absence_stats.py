"""Fehlzeiten-Statistik einer Schülerin/eines Schülers (Anzahl und Prozent der Unterrichtsstunden, je Fach, je Tag/Stunde).

``GET /absence-stats?student_id=&period=year|half1|half2|custom&from=&to=`` und
``GET /absence-stats/class?class_id=`` (Klassenleitung/Verwaltung: wer ist nahe an oder über der Grenze).

* **Nenner** = tatsächlich stattgefundene Stunden laut Plan bis heute: Ferien/unterrichtsfreie Tage fallen weg, Entfall
  und „Unterricht findet nicht statt“ zählen nicht, Vertretungen und Verlegungen zählen (``effective_cells``).
* **Zähler** = Stunden, in denen die Person laut Krankmeldung/Klassenbuch fehlte (Arten ``krank``, ``fehlt``, genehmigte
  bzw. abgelehnte ``beurlaubung``): bei Meldungen ohne Stundenangabe alle Stunden des Tages, sonst die gemeldeten.
  Aufgeteilt nach ``entschuldigt`` / ``unentschuldigt`` / ``offen`` (gemeldet, teilweise entschuldigt). Überschneidungen
  zählen eine Stunde nur einmal (entschuldigt vor offen vor unentschuldigt).
* ``verspaetung`` (zu spät) und ``frueh`` (früher gegangen) zählen **nicht** als ganze Fehlstunde, sondern stehen
  getrennt (Anzahl, bei Verspätung Minuten).
* Grenze (Schul-Einstellung ``absence_limit_percent`` gesamt, ``absence_limit_unexcused_percent`` unentschuldigt; leer/0 =
  keine): je Fach Ampel ``ok`` / ``warn`` (ab 80 % der Grenze) / ``over`` und „noch X Stunden bis zur Grenze“.
* **Versäumte Unterrichtszeit** (Minuten): ganze Fehlstunde = volle Stundenlänge (``settings.period_minutes``, 45), zu spät =
  die gemeldeten Minuten in der ersten betroffenen Stunde, früher gegangen = die gemeldeten Stunden ganz (ohne Stunden
  die Minuten in der letzten Stunde des Tages); je Stunde höchstens die Stundenlänge. ``missed_percent`` = versäumte
  Minuten / Unterrichtsminuten der Gruppe. **Die Ampel (Grenze) bezieht sich auf diese Zeit**, nicht auf die Stundenzahl;
  ``hours_left`` ist der Rest in Stunden (abgerundet).
* Auswertung: je Fach, je Wochentag und Stunde (Häufung; Nenner einer Zelle = Zahl der Unterrichtsstunden genau dieses
  Wochentags und dieser Stunde im Zeitraum, also eine je Woche), Fach mit dem höchsten Anteil.

Wer was sieht: wie die Fehlzeiten-Übersicht (``/student-absences/record``) – Schüler/in selbst, Eltern (Volljährige nur
mit Freigabe „krankmeldungen“), Klassenleitung, Sekretariat, Schulleitung. Fachlehrkräfte nicht. Es werden keine
Gründe oder Vermerke ausgegeben, nur Zahlen.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from schulmanager.server.absence_access import FAMILY, FAMILY_ROLES, FULL, AbsenceAccess
from schulmanager.server.db import get_db
from schulmanager.server.deps import AuthUser, current_user

from .features_common import cached, effective_cells, has, index, own_student_ids, parse_date, snapshot

router = APIRouter(tags=["Fehlzeiten"])

ABSENT_KINDS = ("krank", "fehlt", "beurlaubung")
WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
MIN_HELD_SUBJECT = 3      # darunter wird ein Fach nicht als „Auffälligkeit“ hervorgehoben
MIN_HELD_SLOT = 3
MAX_DAYS = 400
WARN_FACTOR = 0.8         # „nahe dran“ ab 80 % der Grenze
BUCKET_RANK = {"excused": 0, "open": 1, "unexcused": 2}   # bei Überschneidung zählt der „beste“ Zustand
STATE_RANK = {"none": 0, "ok": 1, "warn": 2, "over": 3}


def _today() -> date:
    """Heute (eigene Funktion, damit Tests einen festen Tag setzen können)."""
    return date.today()


def bucket_of(kind: str, status: str) -> Optional[str]:
    """Zustand einer Meldung für die Statistik; ``None`` = zählt nicht (z. B. noch nicht genehmigte Beurlaubung)."""
    if kind == "beurlaubung" and status not in ("entschuldigt", "unentschuldigt"):
        return None
    if status == "entschuldigt":
        return "excused"
    if status == "unentschuldigt":
        return "unexcused"
    return "open"


def limits(school: Any) -> dict[str, float]:
    """Grenzen in Prozent aus den Schul-Einstellungen (0 = keine)."""
    st = getattr(school, "settings", None)

    def val(name: str) -> float:
        try:
            return max(0.0, min(100.0, float(getattr(st, name, 0) or 0)))
        except (TypeError, ValueError):
            return 0.0
    return {"total": val("absence_limit_percent"), "unexcused": val("absence_limit_unexcused_percent")}


def period_length(school: Any) -> int:
    """Dauer einer Unterrichtsstunde in Minuten (Einstellung ``period_minutes``, sonst 45)."""
    try:
        return max(1, int(getattr(getattr(school, "settings", None), "period_minutes", 45) or 45))
    except (TypeError, ValueError):
        return 45


def limit_state(group: dict[str, int], lim: dict[str, float], length: int = 45) -> dict:
    """Ampel und Restzahl einer Gruppe (Fach/Gesamt) gegen die Grenzen – gerechnet in versäumten Minuten."""
    held = group["held"] * length
    state, left = "none", None
    for name, count in (("total", group["missed_minutes"]), ("unexcused", group["missed_unexcused"])):
        pct = lim[name]
        if pct <= 0:
            continue
        allowed = pct * held / 100.0
        remaining = allowed - count
        cur = "over" if count > allowed + 1e-9 else "warn" if held and 100.0 * count / held >= WARN_FACTOR * pct else "ok"
        if STATE_RANK[cur] > STATE_RANK[state]:
            state = cur
        hours = math.floor(remaining / length + 1e-9) if remaining >= 0 else -math.ceil(-remaining / length - 1e-9)
        left = hours if left is None else min(left, hours)
    return {"limit_state": state, "hours_left": left}


def year_range(school: Any, today: date) -> tuple[date, date]:
    """Beginn und Ende des laufenden Schuljahres (Einstellungen; ohne Angabe 1. August bis 31. Juli)."""
    try:
        from schulmanager.calendar_utils import year_bounds

        first, weeks, start = year_bounds(school.settings, today)
        return start, first + timedelta(days=weeks * 7 - 1)
    except Exception:  # noqa: BLE001 - Kalender nicht lesbar: übliche Grenzen
        y = today.year if today.month >= 8 else today.year - 1
        return date(y, 8, 1), date(y + 1, 7, 31)


def resolve_period(school: Any, period: str, d_from: Optional[str], d_to: Optional[str],
                   today: date) -> tuple[str, date, date, str]:
    """``(Schlüssel, von, bis, Bezeichnung)`` des gewählten Zeitraums. Halbjahre: 1. bis 31.01., 2. ab 01.02."""
    start, end = year_range(school, today)
    split = date(start.year + 1, 1, 31)
    if period == "half1":
        return period, start, split, "1. Halbjahr"
    if period == "half2":
        return period, split + timedelta(days=1), end, "2. Halbjahr"
    if period == "custom":
        a = parse_date(d_from, start, name="from")
        b = parse_date(d_to, min(today, end), name="to")
        if b < a:
            raise HTTPException(422, "Das Ende liegt vor dem Anfang")
        if (b - a).days > MAX_DAYS:
            raise HTTPException(422, f"Zeitraum zu lang (höchstens {MAX_DAYS} Tage)")
        return period, a, b, "Eigener Zeitraum"
    return "year", start, end, "Schuljahr"


def held_lessons(snap, sid: str, class_id: str, d1: date, d2: date) -> dict[date, dict[int, Optional[str]]]:
    """Stattgefundene Stunden je Schultag: ``{tag: {stunde(0-basiert): fach}}`` (je Stunde eine, auch bei parallelen
    Kursteilen)."""
    from schulmanager.calendar_utils import is_school_day

    school = snap[1]
    cls = school.index("classes").get(class_id)
    out: dict[date, dict[int, Optional[str]]] = {}
    day = d1
    while day <= d2:
        if is_school_day(school, day, cls)[0]:
            periods: dict[int, Optional[str]] = {}
            cells = sorted(effective_cells(day, "student", sid, snap), key=lambda c: (c.get("period", 0), c.get("part") or 0))
            for cell in cells:
                period = cell.get("period")
                if (not isinstance(period, int) or cell.get("kind") == "aufsicht" or cell.get("status") == "entfall"
                        or cell.get("dropped") or period in periods):
                    continue
                periods[period] = cell.get("subject")
            if periods:
                out[day] = periods
        day += timedelta(days=1)
    return out


def _pct(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


_COUNT_KEYS = ("held", "excused", "unexcused", "open", "missed_minutes", "missed_excused", "missed_unexcused",
               "missed_open", "affected", "late_count", "late_minutes", "early_count", "early_minutes")


def _counts() -> dict[str, int]:
    return dict.fromkeys(_COUNT_KEYS, 0)


def classify(rows: list[Any], held: dict[date, dict[int, Optional[str]]], d1: date, d2: date, length: int,
             abs_kind: Optional[dict] = None, notes: Optional[dict] = None):
    """Meldungen auf Stunden verteilen: ``(ganz gefehlt, Teilversäumnisse, Verspätungen, früher gegangen)``. Optional
    ``abs_kind`` (Art der gewinnenden Meldung je Stunde) und ``notes`` (Kurztexte je Stunde) für die Wochenansicht."""
    absent_at: dict[tuple[date, int], str] = {}
    partial: dict[tuple[date, int], list[tuple[str, str, int]]] = defaultdict(list)   # (Art, Zustand, Minuten)
    late = {"count": 0, "minutes": 0, "excused": 0, "unexcused": 0, "open": 0}
    early = {"count": 0, "excused": 0, "unexcused": 0, "open": 0}
    for r in rows:
        kind = r.kind or "krank"
        bucket = bucket_of(kind, r.status)
        if bucket is None:
            continue
        a, b = max(date.fromisoformat(r.date_from), d1), min(date.fromisoformat(r.date_to), d2)
        wanted = {int(p) for p in (r.periods or [])}
        if kind in ("verspaetung", "frueh"):
            if a > b or a not in held:
                continue
            target = late if kind == "verspaetung" else early
            target["count"] += 1
            target[bucket] += 1
            slots = sorted(held[a])
            minutes = max(0, int(r.minutes or 0))
            if kind == "verspaetung":
                late["minutes"] += minutes
                hit = [p for p in slots if p in wanted] if wanted else slots
                if hit:
                    partial[(a, hit[0])].append((kind, bucket, min(minutes, length)))
                    if notes is not None:
                        notes[(a, hit[0])].append(f"{minutes} Min. zu spät")
            elif wanted:
                for p in slots:
                    if p in wanted:
                        partial[(a, p)].append((kind, bucket, length))
                        if notes is not None:
                            notes[(a, p)].append(f"ab {min(wanted) + 1}. Std. gegangen")
            elif minutes:
                partial[(a, slots[-1])].append((kind, bucket, min(minutes, length)))
                if notes is not None:
                    notes[(a, slots[-1])].append(f"{minutes} Min. früher gegangen")
            continue
        if kind not in ABSENT_KINDS:
            continue
        day = a
        while day <= b:
            for period in held.get(day, {}):
                if wanted and period not in wanted:
                    continue
                key = (day, period)
                prev = absent_at.get(key)
                if prev is None or BUCKET_RANK[bucket] < BUCKET_RANK[prev]:
                    absent_at[key] = bucket
                    if abs_kind is not None:
                        abs_kind[key] = kind
            day += timedelta(days=1)
    return absent_at, partial, late, early


def compute(school: Any, held: dict[date, dict[int, Optional[str]]], rows: list[Any], d1: date, d2: date) -> dict:
    """Reine Auswertung (ohne Datenbank): ``held`` laut :func:`held_lessons`, ``rows`` = Meldungen der Person."""
    subjects = school.index("subjects")
    lim = limits(school)
    length = period_length(school)
    absent_at, partial, late, early = classify(rows, held, d1, d2, length)
    total = _counts()
    by_subject: dict[str, dict[str, int]] = defaultdict(_counts)
    by_slot: dict[tuple[int, int], dict[str, int]] = defaultdict(_counts)
    for day, periods in held.items():
        for period, subject in periods.items():
            bucket = absent_at.get((day, period))
            events = partial.get((day, period), []) if not bucket else []
            missed = {"excused": 0, "unexcused": 0, "open": 0}
            if bucket:
                missed[bucket] = length
            else:
                room = length
                for _kind, bk, mins in events:
                    take = min(mins, room)
                    missed[bk] += take
                    room -= take
            total_missed = sum(missed.values())
            for group in (total, by_subject[subject or ""], by_slot[(day.weekday(), period)]):
                group["held"] += 1
                if bucket:
                    group[bucket] += 1
                group["missed_minutes"] += total_missed
                for bk, mins in missed.items():
                    group["missed_" + bk] += mins
                if total_missed:
                    group["affected"] += 1
                for kind, _bk, mins in events:
                    if kind == "verspaetung":
                        group["late_count"] += 1
                        group["late_minutes"] += mins
                    else:
                        group["early_count"] += 1
                        group["early_minutes"] += mins

    def finish(group: dict[str, int], with_limit: bool = False) -> dict:
        absent = group["excused"] + group["unexcused"] + group["open"]
        out = {**group, "absent": absent, "percent": _pct(absent, group["held"]),
               "held_minutes": group["held"] * length,
               "missed_percent": _pct(group["missed_minutes"], group["held"] * length)}
        if with_limit:
            out.update(limit_state(group, lim, length))
        return out

    subject_rows = []
    for sid_, group in by_subject.items():
        subj = subjects.get(sid_) if sid_ else None
        subject_rows.append({"subject": sid_ or None, "name": subj.name if subj else (sid_ or "Sonstiges"),
                             **finish(group, True)})
    subject_rows.sort(key=lambda x: x["name"].lower())
    slot_rows = [{"weekday": wd, "weekday_label": WEEKDAYS[wd], "period": p, "period_label": f"{p + 1}.", **finish(g)}
                 for (wd, p), g in sorted(by_slot.items())]
    flagged = [x for x in subject_rows if x["held"] >= MIN_HELD_SUBJECT and x["missed_minutes"] > 0]
    top_subject = max(flagged, key=lambda x: (x["missed_percent"], x["missed_minutes"]), default=None)
    hot = sorted((x for x in slot_rows if x["held"] >= MIN_HELD_SLOT and x["missed_minutes"] > 0),
                 key=lambda x: (-x["missed_percent"], -x["missed_minutes"], x["weekday"], x["period"]))[:3]
    wd_rows = []
    for wd in sorted({x["weekday"] for x in slot_rows}):
        g = _counts()
        for x in slot_rows:
            if x["weekday"] == wd:
                for k in g:
                    g[k] += x[k]
        wd_rows.append({"weekday": wd, "weekday_label": WEEKDAYS[wd], **finish(g)})
    worst = max((x["limit_state"] for x in subject_rows), key=lambda s: STATE_RANK[s], default="none")
    return {"totals": finish(total, True), "subjects": subject_rows, "slots": slot_rows, "weekdays": wd_rows,
            "late": late, "early": early, "limits": lim, "period_minutes": length, "worst_state": worst,
            "top_subject": top_subject["subject"] if top_subject else None,
            "top_subject_name": top_subject["name"] if top_subject else None,
            "hot_slots": [{k: x[k] for k in ("weekday", "weekday_label", "period", "period_label", "held", "absent",
                                             "percent", "missed_percent", "missed_minutes")} for x in hot],
            "school_days": len(held)}


def _load(db: Session, snap, sid: str, st: Any, d1: date, end: date) -> dict:
    from schulmanager.server.db_models import StudentAbsence

    rows = list(db.scalars(select(StudentAbsence).where(
        StudentAbsence.student_id == sid, StudentAbsence.date_to >= d1.isoformat(),
        StudentAbsence.date_from <= end.isoformat())))
    held = (cached("absence_held", (sid, d1.isoformat(), end.isoformat()),
                   lambda: held_lessons(snap, sid, st.class_id, d1, end), snap) if end >= d1 else {})
    return compute(snap[1], held, rows, d1, end)


@router.get("/absence-stats")
def absence_stats(student_id: Optional[str] = Query(None, max_length=40), period: str = Query("year", max_length=10),
                  date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
                  user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Fehlzeiten-Statistik (siehe Moduldoku); Standard: Schuljahr bis heute."""
    if not (has(user, "student_absence.read") or has(user, "student_absence.report")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    school = snap[1]
    sid = student_id
    if not sid:
        own = own_student_ids(user)
        if len(own) != 1:
            raise HTTPException(422, "Bitte die Schülerin/den Schüler angeben")
        sid = own[0]
    st = index("students", snap).get(sid)
    acc = AbsenceAccess(user, snap, db)
    lvl = acc.level(sid) if st is not None else None
    if st is None or lvl not in (FULL, FAMILY):
        raise HTTPException(404, "Schüler/in nicht gefunden")
    today = _today()
    key, d1, d2, label = resolve_period(school, period, date_from, date_to, today)
    end = min(d2, today)
    result = _load(db, snap, sid, st, d1, end)
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id},
            "period": {"key": key, "label": label, "from": d1.isoformat(), "to": d2.isoformat(),
                       "counted_to": end.isoformat()},
            "family": acc.role in FAMILY_ROLES, **result,
            "notes": ["Gezählt werden nur Stunden, die laut Plan bis heute stattgefunden haben (ohne Ferien und Entfall, "
                      "mit Vertretungen).", "Zu spät und früher gegangen zählen nicht als ganze Fehlstunde, gehen aber mit den versäumten Minuten in die "
                      "versäumte Zeit ein."]}


@router.get("/absence-stats/class")
def class_absence_stats(class_id: str = Query(..., max_length=40), period: str = Query("year", max_length=10),
                        date_from: Optional[str] = Query(None, alias="from"),
                        date_to: Optional[str] = Query(None, alias="to"),
                        user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Klassenübersicht für Klassenleitung/Verwaltung: je Schüler/in Anteil, Ampel (schlechtestes Fach) und das Fach."""
    if not has(user, "student_absence.read") or user.role in FAMILY_ROLES:
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    school = snap[1]
    if class_id not in index("classes", snap):
        raise HTTPException(404, "Klasse nicht gefunden")
    acc = AbsenceAccess(user, snap, db)
    students = sorted((s for s in school.students if s.class_id == class_id and acc.level(s.id) == FULL),
                      key=lambda s: s.name.lower())
    if not students:
        raise HTTPException(404, "Klasse nicht gefunden")
    key, d1, d2, label = resolve_period(school, period, date_from, date_to, _today())
    end = min(d2, _today())
    out = []
    for s in students:
        r = _load(db, snap, s.id, s, d1, end)
        worst = max(r["subjects"], key=lambda x: (STATE_RANK[x["limit_state"]], x["missed_percent"]), default=None)
        out.append({"student_id": s.id, "name": s.name, "held": r["totals"]["held"], "absent": r["totals"]["absent"],
                    "percent": r["totals"]["percent"], "missed_percent": r["totals"]["missed_percent"],
                    "unexcused": r["totals"]["unexcused"], "state": r["worst_state"],
                    "worst_subject": worst["name"] if worst and worst["missed_minutes"] else None,
                    "worst_percent": worst["missed_percent"] if worst else 0.0})
    out.sort(key=lambda x: (-STATE_RANK[x["state"]], -x["missed_percent"], x["name"].lower()))
    return {"class_id": class_id, "period": {"key": key, "label": label, "from": d1.isoformat(), "to": d2.isoformat()},
            "limits": limits(school), "students": out}


KIND_WORD = {"krank": "krank", "fehlt": "gefehlt", "beurlaubung": "beurlaubt"}
BUCKET_WORD = {"excused": "entschuldigt", "unexcused": "unentschuldigt", "open": "offen"}


def week_view(school: Any, snap, sid: str, class_id: str, rows: list[Any], monday: date, today: date) -> dict:
    """Wochenansicht: je tatsächlicher Unterrichtsstunde der Woche die **Anwesenheit in Prozent** (100 = ganze Stunde da,
    0 = gefehlt, dazwischen z. B. 89 bei 5 Minuten zu spät von 45) mit Kennzeichen (krank / gefehlt / beurlaubt, zu spät,
    früher gegangen; entschuldigt / unentschuldigt / offen). Entfall und Ferientage sind gekennzeichnet, künftige Stunden
    noch ohne Wert."""
    from schulmanager.calendar_utils import is_school_day

    length = period_length(school)
    cls = school.index("classes").get(class_id)
    subjects = school.index("subjects")
    times = list(getattr(school.settings, "period_times", None) or [])
    days: list[dict] = []
    raw: dict[date, dict[int, tuple[Optional[str], bool]]] = {}
    held: dict[date, dict[int, Optional[str]]] = {}
    for i in range(7):
        day = monday + timedelta(days=i)
        ok, reason = is_school_day(school, day, cls)
        periods: dict[int, tuple[Optional[str], bool]] = {}
        if ok:
            cells = sorted(effective_cells(day, "student", sid, snap), key=lambda c: (c.get("period", 0), c.get("part") or 0))
            for cell in cells:
                period = cell.get("period")
                if not isinstance(period, int) or cell.get("kind") == "aufsicht" or period in periods:
                    continue
                periods[period] = (cell.get("subject"), cell.get("status") == "entfall" or bool(cell.get("dropped")))
        if i >= 5 and not periods:
            continue
        days.append({"date": day.isoformat(), "weekday": day.weekday(), "weekday_label": WEEKDAYS[day.weekday()],
                     "school_day": ok, "reason": reason or ("" if periods else "kein Unterricht")})
        raw[day] = periods
        if day <= today:
            h = {p: subj for p, (subj, gone) in periods.items() if not gone}
            if h:
                held[day] = h
    abs_kind: dict = {}
    notes: dict = defaultdict(list)
    absent_at, partial, _late, _early = classify(rows, held, monday, monday + timedelta(days=6), length, abs_kind, notes)
    cells_out: list[dict] = []
    for day, periods in raw.items():
        for period, (subject, gone) in sorted(periods.items()):
            subj = subjects.get(subject) if subject else None
            cell = {"date": day.isoformat(), "period": period, "period_label": f"{period + 1}.", "subject": subject or None,
                    "subject_name": subj.name if subj else (subject or "Unterricht"), "length": length}
            if gone:
                cells_out.append({**cell, "status": "cancelled", "state": "none", "present_percent": None, "missed_minutes": 0,
                                  "labels": ["Entfall"], "bucket": None, "bucket_label": ""})
                continue
            if day > today:
                cells_out.append({**cell, "status": "upcoming", "state": "none", "present_percent": None, "missed_minutes": 0,
                                  "labels": [], "bucket": None, "bucket_label": ""})
                continue
            bucket = absent_at.get((day, period))
            events = partial.get((day, period), []) if not bucket else []
            missed = length if bucket else 0
            if not bucket:
                room = length
                for _kind, _bk, mins in events:
                    take = min(mins, room)
                    missed += take
                    room -= take
            labels = ([KIND_WORD.get(abs_kind.get((day, period), ""), "gefehlt")] if bucket else []) + notes.get((day, period), [])
            if not bucket and events:
                bucket = max(events, key=lambda e: e[2])[1]
            percent = round(100.0 * (length - missed) / length)
            cells_out.append({**cell, "status": "held", "state": "present" if not missed else ("absent" if missed >= length else "partial"),
                              "present_percent": percent, "missed_minutes": missed, "labels": labels,
                              "bucket": bucket if missed else None, "bucket_label": BUCKET_WORD.get(bucket or "", "") if missed else ""})
    iso = monday.isocalendar()
    max_period = max((p for ps in raw.values() for p in ps), default=-1)
    return {"monday": monday.isoformat(), "sunday": (monday + timedelta(days=6)).isoformat(), "iso_week": iso[1],
            "iso_year": iso[0], "prev": (monday - timedelta(days=7)).isoformat(),
            "next": (monday + timedelta(days=7)).isoformat(), "is_current": monday <= today <= monday + timedelta(days=6),
            "today": today.isoformat(), "days": days, "periods": [{"period": p, "label": f"{p + 1}.",
                                                                    "time": times[p] if p < len(times) else ""}
                                                                   for p in range(max_period + 1)],
            "cells": cells_out, "period_minutes": length}


@router.get("/absence-stats/week")
def absence_stats_week(student_id: Optional[str] = Query(None, max_length=40), week: Optional[str] = Query(None, max_length=10),
                       user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Anwesenheit je tatsächlicher Stunde einer Woche (``week`` = beliebiger Tag der Woche, Standard: heute); gleiche
    Rechte wie ``/absence-stats``. Siehe :func:`week_view`."""
    from schulmanager.server.db_models import StudentAbsence

    if not (has(user, "student_absence.read") or has(user, "student_absence.report")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    sid = student_id
    if not sid:
        own = own_student_ids(user)
        if len(own) != 1:
            raise HTTPException(422, "Bitte die Schülerin/den Schüler angeben")
        sid = own[0]
    st = index("students", snap).get(sid)
    acc = AbsenceAccess(user, snap, db)
    lvl = acc.level(sid) if st is not None else None
    if st is None or lvl not in (FULL, FAMILY):
        raise HTTPException(404, "Schüler/in nicht gefunden")
    today = _today()
    ref = parse_date(week, today, name="week")
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    rows = list(db.scalars(select(StudentAbsence).where(
        StudentAbsence.student_id == sid, StudentAbsence.date_to >= monday.isoformat(),
        StudentAbsence.date_from <= sunday.isoformat())))
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id},
            **week_view(snap[1], snap, sid, st.class_id, rows, monday, today)}
