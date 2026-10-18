"""Kalender-Hilfen: Schuljahr, laufende Woche, Unterrichtstage, Ferien, Zeitraster.

Alle Funktionen sind reine Funktionen über dem Planungsdokument (``School``) bzw. den ``Settings``.

Wochen (Entwurf KALENDER-ZEITRASTER §2, §14.1, §15.3)
-----------------------------------------------------
* **Laufende Woche** (``week_no``, Zeichen L): Position 1 … Y im Schuljahr, immer Mo–So, Ferien zählen mit. Woche 1 ist die
  Woche (Mo–So), in der der Schuljahresbeginn liegt (``school_year_start``, leer = ``cycle_start``). Das Schuljahr
  endet am Sonntag vor der Woche des nächsten Beginns (nächster Eintrag bzw. Beginn + 1 Jahr); Y = 52 oder 53.
  Mit gesetztem ``school_year_start`` beginnt danach automatisch das nächste Schuljahr mit Woche 1; ohne
  (Altdokument) zählt L weiter. Frühere Schuljahre stehen in ``school_year_history``.
* **Wochenangaben** (Kurse, Stunden, Sperrzeiten, Aufsichten …) beziehen sich immer auf die laufende Woche
  (``plan_week``): jede Woche, ausgewählte Wochen oder ein Rhythmus (siehe ``weeks``).
* **Unterrichtstage**: 0 = Mo … 6 = So; Schulvorgabe ``Settings.school_days`` (leer = ``range(days)``), je Klasse
  ``SchoolClass.school_days`` (leer = Schulvorgabe). Schulöffnungstag = Unterrichtstag mindestens einer Klasse.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Optional

from .models import WEEKDAYS, Holiday, School, Settings

ISO_MODE = "iso"


def as_date(value: date | str) -> date:
    """Akzeptiert ``date``, ``datetime`` oder ISO-String."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _parse(value: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _plus_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # 29.02.
        return d.replace(year=d.year + 1, day=28)


# ------------------------------------------------------------------ Schuljahr
def base_start(st: Settings) -> date:
    """Beginn des (aktuellen) Schuljahres laut Einstellungen: ``school_year_start``, sonst ``cycle_start``."""
    return _parse(getattr(st, "school_year_start", "")) or _parse(st.cycle_start) or date(2026, 8, 31)


def year_starts(st: Settings, until: Optional[date] = None) -> list[date]:
    """Beginndaten der Schuljahre (aufsteigend): Verlauf + aktueller Beginn, Lücken > 400 Tage und die Zeit bis
    ``until`` mit „Beginn + 1 Jahr“ aufgefüllt. Ohne ``school_year_start`` (Altdokument) nur ``cycle_start``."""
    if not getattr(st, "school_year_start", ""):
        return [base_start(st)]
    starts = sorted({d for d in (_parse(x) for x in getattr(st, "school_year_history", []) or []) if d}
                    | {base_start(st)})
    out: list[date] = []
    for i, s in enumerate(starts):
        out.append(s)
        nxt = starts[i + 1] if i + 1 < len(starts) else None
        if nxt is not None:
            cur = s
            while (nxt - cur).days > 400:
                cur = _plus_year(cur)
                if (nxt - cur).days < 300:
                    break
                out.append(cur)
    if until is not None:
        guard = 0
        while monday_of(_plus_year(out[-1])) <= monday_of(until) and guard < 500:
            out.append(_plus_year(out[-1]))
            guard += 1
    return out


def year_bounds(st: Settings, d: date) -> tuple[date, int, date]:
    """``(Montag der Woche 1, Wochen Y, Beginndatum)`` des Schuljahres, zu dem ``d`` gehört.

    Vor dem ersten Schuljahr gilt das erste (die Woche zählt dann rückwärts, L ≤ 0); beim Altdokument immer das
    Schuljahr ab ``cycle_start`` (L zählt nach Y weiter)."""
    m = monday_of(d)
    starts = year_starts(st, until=d)
    idx = 0
    for i, s in enumerate(starts):
        if monday_of(s) <= m:
            idx = i
    start = starts[idx]
    nxt = starts[idx + 1] if idx + 1 < len(starts) else _plus_year(start)
    first = monday_of(start)
    return first, max(1, (monday_of(nxt) - first).days // 7), start


def school_year(st: Settings, d: date | str) -> tuple[date, int]:
    """``(Montag der Woche 1, Zahl der Wochen Y)`` des Schuljahres von ``d``."""
    first, y, _ = year_bounds(st, as_date(d))
    return first, y


def week_no(st: Settings, d: date | str) -> int:
    """Laufende Woche (Position im Schuljahr; vor Beginn ≤ 0, beim Altdokument nach Y weiter > Y)."""
    d = as_date(d)
    first, _, _ = year_bounds(st, d)
    return (monday_of(d) - first).days // 7 + 1


def plan_week(st: Settings, d: date | str) -> int:
    """Laufende Woche für Wochenangaben (``weeks``/``rhythm``): wie ``week_no``; beim Altdokument ohne
    ``school_year_start`` außerhalb des ersten Schuljahres periodisch fortgesetzt (Block von Y Wochen)."""
    d = as_date(d)
    no = week_no(st, d)
    if not getattr(st, "school_year_start", ""):
        _, y, _ = year_bounds(st, d)
        if no > y or no < 1:
            no = (no - 1) % y + 1
    return no


# ------------------------------------------------------------------ Tage
def default_days(st: Settings) -> list[int]:
    """Unterrichtstage der Schulvorgabe (0–6)."""
    days = sorted({int(x) for x in getattr(st, "school_days", None) or [] if 0 <= int(x) <= 6})
    return days or list(range(max(1, min(7, int(st.days or 5)))))


def class_days(school: School, cls: Any) -> list[int]:
    """Unterrichtstage einer Klasse (eigene, sonst Schulvorgabe)."""
    if isinstance(cls, str):
        cls = school.index("classes").get(cls)
    own = getattr(cls, "school_days", None) if cls is not None else None
    if own:
        days = sorted({int(x) for x in own if 0 <= int(x) <= 6})
        if days:
            return days
    return default_days(school.settings)


def open_days(school: School) -> list[int]:
    """Schulöffnungstage: Unterrichtstage mindestens einer Klasse (ohne Klassen: Schulvorgabe)."""
    base = default_days(school.settings)
    if not school.classes:
        return base
    out: set[int] = set()
    plain = False
    for c in school.classes:
        if c.school_days:
            out.update(class_days(school, c))
        else:
            plain = True
    if plain:
        out.update(base)
    return sorted(out)


def holiday_of(school: School, day: date) -> Optional[Holiday]:
    """Ferien/Feiertag an ``day`` (erster Treffer) oder ``None``."""
    for h in school.holidays:
        try:
            if h.covers(day):
                return h
        except ValueError:  # kaputtes Datum in den Stammdaten -> ignorieren
            continue
    return None


def holiday_name(school: School, day: date) -> Optional[str]:
    """Name der Ferien/des Feiertags an ``day`` oder ``None``."""
    h = holiday_of(school, day)
    return (h.name or "Ferien") if h is not None else None


def _not_teaching_reason(d: date) -> str:
    return "Wochenende" if d.weekday() >= 5 else "Kein Unterrichtstag"


def is_school_day(school: School, day: date | str, cls: Any = None) -> tuple[bool, Optional[str]]:
    """``(True, None)`` an Schultagen, sonst ``(False, Grund)`` („Wochenende“, „Kein Unterrichtstag“ bzw. Ferienname).

    Mit ``cls`` entscheiden die Unterrichtstage der Klasse, sonst die Schulöffnungstage."""
    d = as_date(day)
    days = class_days(school, cls) if cls is not None else open_days(school)
    if d.weekday() not in days:
        return False, _not_teaching_reason(d)
    name = holiday_name(school, d)
    if name:
        return False, name
    return True, None


def day_kind(school: School, day: date | str, cls: Any = None) -> str:
    """``unterricht`` | ``kein_unterrichtstag`` | ``ferien`` | ``feiertag`` (Ferienart ``ferien`` → ferien, sonst
    feiertag)."""
    d = as_date(day)
    days = class_days(school, cls) if cls is not None else open_days(school)
    if d.weekday() not in days:
        return "kein_unterrichtstag"
    h = holiday_of(school, d)
    if h is not None:
        return "ferien" if getattr(h, "kind", "ferien") == "ferien" else "feiertag"
    return "unterricht"


def school_days(school: School, date_from: date | str, date_to: date | str, cls: Any = None) -> list[date]:
    """Alle Schultage im Bereich ``[date_from, date_to]`` (inklusive), mit ``cls`` die der Klasse."""
    d, end = as_date(date_from), as_date(date_to)
    out: list[date] = []
    while d <= end:
        if is_school_day(school, d, cls)[0]:
            out.append(d)
        d += timedelta(days=1)
    return out


# ------------------------------------------------------------------ Wochen-Info
def _week_text(st: Settings, no: int, iso_week: int) -> str:
    """„Woche 12 · KW 45“; Modus ``iso`` bzw. außerhalb des Schuljahres nur die KW."""
    show_no = getattr(st, "week_numbering", "iso") != ISO_MODE and no >= 1
    return f"Woche {no} · KW {iso_week}" if show_no else f"KW {iso_week}"


def holiday_week(school: School, monday: date, cls: Any = None) -> tuple[bool, Optional[str]]:
    """``(Ferienwoche, Name)``: alle Unterrichtstage (Klasse bzw. Schulöffnungstage) der Woche sind frei."""
    days = class_days(school, cls) if cls is not None else open_days(school)
    names: list[str] = []
    for i in days:
        if (date.max - monday).days < i:    # letzte Woche des Kalenders (9999-12-27 …)
            break
        h = holiday_of(school, monday + timedelta(days=i))
        if h is None:
            return False, None
        names.append(h.name or "Ferien")
    if not names:
        return False, None
    return True, max(dict.fromkeys(names), key=names.count)


def week_info(school: School, d: date | str, cls: Any = None) -> dict:
    """WeekInfo (Vertrag §15.3) der Woche von ``d``; Bezug Klasse (Unterrichtstage) bzw. Schule."""
    d = as_date(d)
    st = school.settings
    m = monday_of(d)
    first, y, _ = year_bounds(st, d)
    no = (m - first).days // 7 + 1
    iso_year, iso_week, _ = m.isocalendar()
    hol, hname = holiday_week(school, m, cls)
    from .plan_periods import active, state_for_week
    out = {"week_no": no if no >= 1 else None, "iso_week": iso_week, "iso_year": iso_year,
            "week_start": m.isoformat(), "week_end": (m + timedelta(days=min(6, (date.max - m).days))).isoformat(),
            "week_text": _week_text(st, no, iso_week),
            "holiday_week": hol, "holiday_name": hname, "in_school_year": 1 <= no <= y}
    if active(school):            # nur mit Planzeiträumen: Zustand des Plans dieser Woche (ok | missing | none)
        out["plan"] = state_for_week(school, plan_week(st, m))
    return out


def day_info(school: School, d: date, cls: Any = None) -> dict:
    """Spaltenkopf eines Tages (``DayInfo``)."""
    kind = day_kind(school, d, cls)
    return {"index": d.weekday(), "name": WEEKDAYS[d.weekday()], "date": d.isoformat(),
            "teaching": kind == "unterricht", "day_kind": kind, "holiday": holiday_name(school, d)}


def monday_of_week_no(st: Settings, no: int, today: Optional[date] = None) -> date:
    """Montag der laufenden Woche ``no`` im Schuljahr von ``today`` (Standard: heute)."""
    first, _, _ = year_bounds(st, today or date.today())
    return first + timedelta(days=7 * (int(no) - 1))


def school_year_info(school: School, d: Optional[date | str] = None, cls: Any = None) -> dict:
    """``GET /calendar/school-year``: alle Wochen 1 … Y des Schuljahres von ``d`` (Standard: heute)."""
    st = school.settings
    d = as_date(d) if d else date.today()
    first, y, start = year_bounds(st, d)
    nxt = first + timedelta(days=7 * y)
    from .plan_periods import periods as plan_periods, public as plan_public, state_for_week
    plans = bool(plan_periods(school))
    weeks = []
    for i in range(y):
        m = first + timedelta(days=7 * i)
        hol, _ = holiday_week(school, m, cls)
        names = []
        for k in range(7):
            n = holiday_name(school, m + timedelta(days=k))
            if n and n not in names:
                names.append(n)
        row = {"week_no": i + 1, "iso_week": m.isocalendar()[1], "week_start": m.isoformat(),
               "week_end": (m + timedelta(days=6)).isoformat(), "holiday_week": hol, "holidays": names}
        if plans:
            pl = state_for_week(school, i + 1)
            row.update(plan_state=pl["state"], plan_period=(pl["period"] or {}).get("id"))
        weeks.append(row)
    return {"start": start.isoformat(), "first_monday": first.isoformat(),
            "end": (nxt - timedelta(days=1)).isoformat(),
            "numbering": getattr(st, "week_numbering", "iso"), "weeks_in_year": y,
            "year_start_mode": getattr(st, "year_start_mode", "auto"),
            "detected_start": next(iter(reversed([x.isoformat() for x in detect_year_starts(school) if x <= (as_date(d) if d else date.today())])), None),
            "open_days": class_days(school, cls) if cls is not None else open_days(school),
            "warnings": year_warnings(school, d, cls), "weeks": weeks,
            "plan_periods": [plan_public(school, p) for p in plan_periods(school)]}


def year_warnings(school: School, d: Optional[date] = None, cls: Any = None) -> list[str]:
    """Hinweise zur Wochenzählung (Texte §15.5)."""
    st = school.settings
    d = d or date.today()
    _, y, _ = year_bounds(st, d)
    out: list[str] = []
    if not getattr(st, "school_year_start", "") and week_no(st, d) > y:
        out.append("Schuljahr abgelaufen. Tragen Sie den Beginn des neuen Schuljahres ein.")
    return out


# ------------------------------------------------------------------ Uhrzeiten
def period_time(settings: Settings, period: int) -> str:
    """Beginn der Stunde ``period`` (0-basiert) als ``HH:MM`` oder ``""``."""
    if 0 <= period < len(settings.period_times):
        return settings.period_times[period]
    return ""


def period_label(period: int) -> str:
    """Anzeige-Label einer Stunde: 0 -> ``"1."``."""
    return f"{period + 1}."


def break_time(settings: Settings, brk: dict) -> str:
    """Beginn einer Pause (``HH:MM``), abgeleitet aus dem Beginn der Folgestunde minus Pausenlänge."""
    nxt = period_time(settings, int(brk.get("after", 0)) + 1)
    if not nxt:
        return ""
    try:
        h, m = (int(x) for x in nxt.split(":"))
    except ValueError:
        return ""
    total = h * 60 + m - int(brk.get("minutes", 0) or 0)
    total = max(0, total)
    return f"{total // 60:02d}:{total % 60:02d}"


# ------------------------------------------------------------------ Schuljahresbeginn aus den Sommerferien
def _next_weekday(d: date) -> date:
    """Erster Tag Mo–Fr nach ``d`` (erster Schultag nach Ferienende)."""
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def detect_year_starts(school: School) -> list[date]:
    """Schuljahresbeginne aus den Sommerferien: der erste Werktag nach dem Ende der Sommerferien (Ferien mit „Sommer“
    im Namen, sonst die Ferien ab 21 Tagen, die zwischen Mitte Juni und Mitte September enden). Aufsteigend."""
    out: set[date] = set()
    cand: dict[int, list] = {}
    for h in school.holidays:
        if getattr(h, "kind", "ferien") != "ferien":
            continue
        a, b = _parse(h.date_from), _parse(h.date_to)
        if not a or not b or b < a:
            continue
        summer = "sommer" in (h.name or "").lower() and 6 <= b.month <= 9
        long_break = (b - a).days >= 20 and (b.month, b.day) >= (6, 15) and (b.month, b.day) <= (9, 15)
        if summer or long_break:
            cand.setdefault(b.year, []).append((summer, b))
    for items in cand.values():
        named = [b for s, b in items if s]
        out.add(_next_weekday(max(named) if named else max(b for _, b in items)))
    return sorted(out)


def apply_auto_year_start(school: School, today: Optional[date] = None) -> Optional[dict]:
    """Setzt bei ``year_start_mode == "auto"`` den Schuljahresbeginn aus den Sommerferien (am Dokument, in ``mutate``).

    * aktueller Beginn = letzter erkannter Beginn bis heute; der nächste erkannte Beginn kommt in den Verlauf
      (``school_year_history``), damit das Ende des laufenden Schuljahres stimmt;
    * liegt der neue Beginn weniger als 300 Tage vom alten entfernt (dasselbe Schuljahr, z. B. Korrektur von
      31.8. auf 24.8.), werden gespeicherte Wochenangaben so verschoben, dass sie dieselben Kalenderwochen behalten;
    * beim Wechsel in ein neues Schuljahr bleibt der alte Beginn im Verlauf und die Zählung beginnt neu.

    Liefert ``{"old", "new", "shifted_weeks"}`` bei einer Änderung, sonst ``None`` (nichts erkannt/nichts zu tun)."""
    st = school.settings
    if getattr(st, "year_start_mode", "auto") != "auto":
        return None
    today = today or date.today()
    starts = detect_year_starts(school)
    past = [s for s in starts if s <= today]
    if not past:
        return None
    new = past[-1]
    upcoming = [s for s in starts if s > today][:1]
    old = base_start(st) if (st.school_year_start or st.cycle_start) else None
    result: Optional[dict] = None
    if old is None or new != old:
        shifted = 0
        if old is not None and abs((new - old).days) < 300:
            delta = (monday_of(new) - monday_of(old)).days // 7
            if delta:
                from .weeks import shift_week_specs
                shifted = shift_week_specs(school, delta)
        if old is not None and (new - old).days >= 300:
            st.school_year_history = sorted(set(st.school_year_history) | {old.isoformat()})[-20:]
        st.school_year_start = new.isoformat()
        if old is not None:        # Planzeiträume (plan_periods.py) ziehen mit dem Schuljahr mit
            from .plan_periods import refresh, shift_dates
            if (new - old).days >= 300:
                shift_dates(school, (monday_of(new) - monday_of(old)).days)
            else:
                refresh(school)
        result = {"old": old.isoformat() if old else "", "new": new.isoformat(), "shifted_weeks": shifted}
    keep = [x for x in st.school_year_history if (_parse(x) or date.min) <= today and _parse(x) != new]
    hist = sorted(set(keep) | {u.isoformat() for u in upcoming
                                 if 300 <= (u - new).days and (monday_of(u) - monday_of(new)).days // 7 <= 53})
    if hist != list(st.school_year_history):
        st.school_year_history = hist[-20:]
        result = result or {"old": old.isoformat() if old else "", "new": new.isoformat(), "shifted_weeks": 0}
    return result
