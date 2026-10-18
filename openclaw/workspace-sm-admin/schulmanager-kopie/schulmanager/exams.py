"""Klassenarbeiten / Klausuren: Konfliktprüfung und Abfragen.

Klausuren werden in regulären Unterrichtsstunden des Kurses geschrieben. Im
Vertretungsplan erscheinen sie als Info-Entries (``kind: "klausur"``); fällt die
Lehrkraft aus, wird zwingend eine Aufsicht (Vertretung) eingeplant.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from . import weeks as wk
from .calendar_utils import as_date, class_days, holiday_name, is_school_day, period_label, period_time, week_info
from .models import WEEKDAYS, Course, Exam, School


def _exam_date(exam: Exam) -> Optional[date]:
    try:
        return as_date(exam.date)
    except (TypeError, ValueError):
        return None


def _course_lessons_on(school: School, course: Course, day: date) -> list:
    """Blöcke des Kurses am Datum (zentrale Aktiv-Logik, laufende Woche)."""
    idx = wk.ActiveIndex(school)
    return [les for les in school.lessons if les.course_id == course.id and idx.active_on(les, course, day)]


def lessons_active_on(school: School, day: date) -> list:
    """Alle Blöcke, die am Datum stattfinden (zentrale Aktiv-Logik) – für Belegungsprüfungen (Nachschreibtermine)."""
    idx = wk.ActiveIndex(school)
    courses = school.index("courses")
    return [les for les in school.lessons if idx.active_on(les, courses.get(les.course_id), day)]


def _class_unavailable(school: School, class_id: str, day: date, period: int) -> Optional[str]:
    """Grund, warum die Klasse zu ``period`` nicht da ist (Abwesenheit/Rhythmus), sonst ``None``."""
    st = school.settings
    for a in school.absences:
        if a.kind != "class" or a.ref != class_id:
            continue
        try:
            if a.covers(day, period):
                return a.reason or "Klasse abwesend"
        except ValueError:
            continue
    cls = school.index("classes").get(class_id)
    if cls:
        real = wk.real_week(school, day)
        for r in cls.unavailable:
            if r.matches(real, day.weekday(), period):
                return r.note or "Klasse laut Rhythmus nicht da"
    del st
    return None


def check_exam(school: School, exam: Exam) -> list[str]:
    """Prüft eine (neue oder geänderte) Klausur. Leere Liste = in Ordnung.

    Geprüft werden: Kurs/Kursteil existiert, Schultag (Ferien/Wochenende), Zeitraster,
    Kurs hat zu der Zeit laut Plan Unterricht, Klasse nicht abwesend/laut Rhythmus da,
    Höchstzahlen je Klasse und Tag/Woche (``rules.exam_limits_for_class``: Klasse → Jahrgang → Schule;
    andere Teile desselben Kurses am selben Tag zählen als eine Klausur), Raum nicht doppelt belegt.
    """
    from .rules import exam_limits_for_class
    st = school.settings
    problems: list[str] = []
    courses = school.index("courses")
    course = courses.get(exam.course_id)
    if course is None:
        return [f"Kurs {exam.course_id} existiert nicht"]
    # Angekündigte Tests zählen nicht zu den Höchstzahlen für Klassenarbeiten/Klausuren
    import dataclasses
    school = dataclasses.replace(school, exams=[x for x in school.exams if getattr(x, "kind", "klausur") != "test"])
    is_test = getattr(exam, "kind", "klausur") == "test"
    day = _exam_date(exam)
    if day is None:
        return [f"Ungültiges Datum: {exam.date!r}"]
    label = course.label or course.id
    length = max(1, exam.length or 1)
    if exam.part is not None and not 0 <= exam.part < len(course.parts):
        problems.append(f"Kursteil {exam.part} existiert in {label} nicht")
    # Sa/So sind erlaubt, wenn der Tag ein Unterrichtstag einer Klasse des Kurses ist (§5)
    teaching = any(day.weekday() in class_days(school, c) for c in course.classes) if course.classes else \
        is_school_day(school, day)[0] or bool(holiday_name(school, day))
    hol = holiday_name(school, day)
    ok = teaching and not hol
    if not teaching:
        problems.append(f"{day.strftime('%d.%m.%Y')}: Kein Unterrichtstag der Klasse.")
    elif hol:
        problems.append(f"{day.strftime('%d.%m.%Y')} ist kein Schultag ({hol})")
    if exam.start < 0 or exam.start + length > st.periods:
        problems.append("Klausur liegt außerhalb des Zeitrasters")
    wd_name = WEEKDAYS[day.weekday()]
    if ok:
        covered: set[int] = set()
        for les in _course_lessons_on(school, course, day):
            covered.update(range(les.start, les.start + max(1, les.length)))
        missing = [p for p in range(exam.start, exam.start + length) if p not in covered]
        if missing:
            hours = ", ".join(f"{p + 1}." for p in missing)
            problems.append(f"{label} hat am {wd_name}, {day.strftime('%d.%m.%Y')} in der {hours} Stunde "
                            f"laut Stundenplan keinen Unterricht")
        for cid in course.classes:
            for p in range(exam.start, exam.start + length):
                why = _class_unavailable(school, cid, day, p)
                if why:
                    problems.append(f"Klasse {cid} ist in der {p + 1}. Stunde nicht da ({why})")
                    break

    monday = day - timedelta(days=day.weekday())
    sunday = monday + timedelta(days=6)
    for cid in course.classes:
        limits = exam_limits_for_class(school, cid)
        same_day: set[str] = set()
        same_week: set[tuple[str, date]] = set()
        for other in school.exams:
            if other.id == exam.id:
                continue
            oc = courses.get(other.course_id)
            od = _exam_date(other)
            if oc is None or od is None or cid not in oc.classes:
                continue
            if other.course_id == exam.course_id and od == day:
                continue  # anderer Teil desselben Kurses am selben Tag = dieselbe Klausur
            if od == day:
                same_day.add(other.course_id)
            if monday <= od <= sunday:
                same_week.add((other.course_id, od))
        if not is_test and len(same_day) >= max(1, limits["per_day"]):
            problems.append(f"Klasse {cid}: am {day.strftime('%d.%m.%Y')} bereits {len(same_day)} Klausur(en) "
                            f"(max. {limits['per_day']} pro Tag)")
        if not is_test and len(same_week) >= max(1, limits["per_week"]):
            problems.append(f"Klasse {cid}: in dieser Woche bereits {len(same_week)} Klausur(en) "
                            f"(max. {limits['per_week']} pro Woche)")
    if exam.room:
        span = set(range(exam.start, exam.start + length))
        for other in school.exams:
            if other.id == exam.id or other.room != exam.room or _exam_date(other) != day:
                continue
            if span & set(range(other.start, other.start + max(1, other.length))):
                problems.append(f"Raum {exam.room} ist bereits durch Klausur {other.title or other.id} belegt")
    return problems


def _exam_dict(school: School, ex: Exam, course: Optional[Course]) -> dict:
    st = school.settings
    day = _exam_date(ex)
    parts = ([ex.part] if ex.part is not None else list(range(len(course.parts)))) if course else []
    parts = [i for i in parts if course and 0 <= i < len(course.parts)]
    teachers = [course.parts[i].teacher for i in parts if course.parts[i].teacher] if course else []
    subjects = [course.parts[i].subject for i in parts] if course else []
    return {
        "id": ex.id, "course_id": ex.course_id, "date": day.isoformat() if day else ex.date,
        "weekday": day.weekday() if day else None,
        "week_text": week_info(school, day)["week_text"] if day else "",
        "start": ex.start, "length": ex.length, "period_label": period_label(ex.start),
        "time": period_time(st, ex.start), "title": ex.title or "Klausur", "part": ex.part, "room": ex.room,
        "classes": list(course.classes) if course else [], "subject": subjects[0] if subjects else None,
        "subjects": subjects, "teacher": teachers[0] if teachers else None, "teachers": teachers,
        "label": (course.label or course.id) if course else ex.course_id,
    }


def exams_for(school: School, kind: str, ref: str, date_from: date | str, date_to: date | str) -> list[dict]:
    """Klausuren im Zeitraum für ``kind`` ∈ ``class|teacher|room|student|course|all``.

    Liefert ``[{"id","course_id","date","weekday","start","length","period_label","time","title",
    "part","room","classes","subject","subjects","teacher","teachers","label","week_text"}]``.
    """
    d0, d1 = as_date(date_from), as_date(date_to)
    courses = school.index("courses")
    sel: dict[str, list[int]] = {}
    student_class = None
    if kind == "student":
        stud = school.index("students").get(ref)
        if stud is None:
            return []
        student_class = stud.class_id
        from .timetable import student_parts
        sel = student_parts(school, ref)
    elif kind not in ("class", "teacher", "room", "course", "all"):
        raise ValueError(f"Unbekannte Ansicht {kind}")
    out = []
    for ex in school.exams:
        day = _exam_date(ex)
        if day is None or not d0 <= day <= d1:
            continue
        c = courses.get(ex.course_id)
        parts = ([ex.part] if ex.part is not None else list(range(len(c.parts)))) if c else []
        if kind == "class":
            if c is None or ref not in c.classes:
                continue
        elif kind == "teacher":
            if c is None or not any(0 <= i < len(c.parts) and c.parts[i].teacher == ref for i in parts):
                continue
        elif kind == "room":
            if ex.room != ref:
                continue
        elif kind == "course":
            if ex.course_id != ref:
                continue
        elif kind == "student":
            if c is None or student_class not in c.classes or c.id not in sel:
                continue
            if ex.part is not None and ex.part not in sel[c.id]:
                continue
        out.append(_exam_dict(school, ex, c))
    out.sort(key=lambda e: (e["date"], e["start"], e["id"]))
    return out
