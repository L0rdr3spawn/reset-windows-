"""Nachschreibtermine – Logik ohne HTTP (Routen: ``routes/features_makeups.py``).

Ablauf
------
1. :func:`sync` legt für jede Klausur/jeden Test des Planungsdokuments und jede Person, die an dem Tag laut
   Krankmeldung (``kind=krank``) oder Klassenbuch (``kind=fehlt``) gefehlt hat, eine Zeile ``exam_makeups`` an
   (Status ``offen``) und räumt Zeilen auf, deren Klausur oder Fehlzeit weggefallen ist. Aufgerufen nach jeder
   Änderung an Fehlzeiten (SQLAlchemy-Ereignis, :func:`install_hooks`), nach Klausur-Änderungen und beim Lesen.
2. Die Lehrkraft der Klausur (``exam.edit`` für diese Klausur) legt einen Termin fest (:func:`check_date`
   prüft Schultag, Zeitraster, Raum und Lehrkraft gegen Klausuren, Termine und Stundenplan).
3. Das Attest wird nicht gespeichert, sondern aus den Dokumenten der Fehlzeit abgeleitet (:func:`attest_states`).

Sichtbarkeit (:class:`MakeupAccess`): ``full`` (Klassenleitung, Sekretariat, Schulleitung: Quelle der Fehlzeit,
Attest verwalten), ``family`` (die Person selbst bzw. Eltern – bei Volljährigen nur mit Freigabe), ``teacher``
(Lehrkraft der Klausur bzw. Planung/Leitung mit ``exam.edit``: nur „abwesend“, Termin und Attest-Status – nie Grund
oder Dokument). Technische Administration: kein Zugriff.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Any, Iterable, Optional

from sqlalchemy import event, select
from sqlalchemy.orm import Session, object_session

from .absence_access import FAMILY, FULL, AbsenceAccess, part_members
from .db import utcnow
from .db_models import StudentAbsence
from .feature_models.makeups import MAKEUP_STATUS, ExamMakeup, ExamMakeupDate
from .feature_models.student_self import StudentDocument

log = logging.getLogger("schulmanager.makeups")

MISSED_KINDS = ("krank", "fehlt")
SOURCE_LABELS = {"krank": "krank gemeldet", "fehlt": "im Klassenbuch als gefehlt eingetragen"}
ATTEST_LABELS = {"fehlt": "Attest fehlt", "eingereicht": "Attest eingereicht (wird geprüft)",
                 "genehmigt": "Attest genehmigt", "abgelehnt": "Attest abgelehnt – neues Attest nötig",
                 "nicht_noetig": "Attest nicht erforderlich"}
TEACHER = "teacher"


# ----------------------------------------------------------------------------- Teilnehmende / Fehlzeiten
def exam_students(school: Any, exam: Any) -> frozenset[str]:
    """Schüler-IDs, die die Klausur schreiben (Kursteile wie ``timetable.student_parts``)."""
    course = school.index("courses").get(exam.course_id)
    if course is None:
        return frozenset()
    members = part_members(school, course)
    if exam.part is not None and 0 <= exam.part < len(members):
        return members[exam.part]
    out: set[str] = set()
    for m in members:
        out |= m
    return frozenset(out)


def _exam_day(exam: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(exam.date)[:10])
    except ValueError:
        return None


def _span(exam: Any) -> set[int]:
    return set(range(exam.start, exam.start + max(1, exam.length or 1)))


def _covers(a: StudentAbsence, day: date, exam: Any) -> bool:
    try:
        if not (date.fromisoformat(a.date_from) <= day <= date.fromisoformat(a.date_to)):
            return False
    except ValueError:
        return False
    return not a.periods or bool(set(a.periods) & _span(exam))


def sync(db: Session, school: Any) -> int:
    """Gleicht ``exam_makeups`` mit Klausuren und Fehlzeiten ab (siehe Moduldoku). Gibt die Zahl neuer Zeilen zurück;
    committet nicht."""
    exams = {e.id: e for e in school.exams}
    existing = {(m.exam_id, m.student_id): m for m in db.scalars(select(ExamMakeup))}
    covered: dict[tuple[str, str], StudentAbsence] = {}
    by_date: dict[date, list[Any]] = defaultdict(list)
    for e in exams.values():
        d = _exam_day(e)
        if d is not None:
            by_date[d].append(e)
    created = 0
    if by_date:
        lo, hi = min(by_date).isoformat(), max(by_date).isoformat()
        members: dict[str, frozenset[str]] = {}
        rows = db.scalars(select(StudentAbsence).where(StudentAbsence.kind.in_(MISSED_KINDS),
                                                       StudentAbsence.date_from <= hi,
                                                       StudentAbsence.date_to >= lo)
                          .order_by(StudentAbsence.id)).all()
        for a in rows:
            for d, exams_on in by_date.items():
                for e in exams_on:
                    if not _covers(a, d, e):
                        continue
                    if e.id not in members:
                        members[e.id] = exam_students(school, e)
                    if a.student_id not in members[e.id]:
                        continue
                    key = (e.id, a.student_id)
                    covered.setdefault(key, a)
    for key, a in covered.items():
        exam = exams[key[0]]
        row = existing.get(key)
        if row is None:
            db.add(ExamMakeup(exam_id=exam.id, student_id=key[1], course_id=exam.course_id,
                              exam_date=str(exam.date)[:10], source=a.kind if a.kind in MISSED_KINDS else "krank",
                              absence_id=a.id, status="offen", created_at=utcnow()))
            created += 1
        else:
            row.exam_date = str(exam.date)[:10]
            row.course_id = exam.course_id
            if row.absence_id is None or (row.absence_id != a.id and row.status == "offen"):
                row.absence_id = a.id
    for key, row in existing.items():
        gone = key[0] not in exams
        stale = key not in covered and row.status == "offen"
        if gone or stale:
            db.delete(row)
    db.flush()
    # Termine ohne Teilnehmende entfernen
    used = {d for (d,) in db.execute(select(ExamMakeup.date_id).where(ExamMakeup.date_id.is_not(None)))}
    for dt in db.scalars(select(ExamMakeupDate)):
        if dt.id not in used:
            db.delete(dt)
    return created


def sync_now() -> int:
    """Eigene Sitzung: abgleichen, Live-Ereignis senden, wenn sich etwas geändert hat. Fehler werden nur geloggt."""
    try:
        from .db import session_scope
        from .routes.features_common import publish_change, snapshot

        school = snapshot()[1]
        with session_scope() as db:
            before = db.query(ExamMakeup).count()
            created = sync(db, school)
            db.flush()
            changed = created or db.query(ExamMakeup).count() != before
        if changed:
            publish_change(["makeups"])
        return created
    except Exception:  # noqa: BLE001 - Fehlzeiten/Klausuren speichern darf nie daran scheitern
        log.exception("Abgleich der Nachschreibtermine fehlgeschlagen")
        return 0


_hooks_installed = False


def install_hooks() -> None:
    """Nach jedem Commit, der Fehlzeiten ändert, die Nachschreib-Zeilen abgleichen."""
    global _hooks_installed
    if _hooks_installed:
        return
    _hooks_installed = True

    def mark(_mapper: Any, _conn: Any, target: Any) -> None:
        sess = object_session(target)
        if sess is not None:
            sess.info["makeups_dirty"] = True

    for name in ("after_insert", "after_update", "after_delete"):
        event.listen(StudentAbsence, name, mark)

    @event.listens_for(Session, "after_commit")
    def _after_commit(sess: Session) -> None:
        if sess.info.pop("makeups_dirty", False):
            sync_now()

    @event.listens_for(Session, "after_rollback")
    def _after_rollback(sess: Session) -> None:
        sess.info.pop("makeups_dirty", None)


# ----------------------------------------------------------------------------- Attest
def attest_states(db: Session, rows: Iterable[ExamMakeup]) -> dict[int, dict]:
    """Attest-Zustand je Zeile aus den Dokumenten der Fehlzeiten, die den Klausurtag abdecken."""
    rows = list(rows)
    if not rows:
        return {}
    sids = sorted({r.student_id for r in rows})
    absences: dict[str, list[StudentAbsence]] = defaultdict(list)
    for chunk in _chunks(sids):
        for a in db.scalars(select(StudentAbsence).where(StudentAbsence.student_id.in_(chunk),
                                                         StudentAbsence.kind.in_(MISSED_KINDS))):
            absences[a.student_id].append(a)
    all_ids = [a.id for lst in absences.values() for a in lst]
    docs: dict[int, list[str]] = defaultdict(list)
    for chunk in _chunks(all_ids):
        for aid, status in db.execute(select(StudentDocument.absence_id, StudentDocument.status)
                                      .where(StudentDocument.absence_id.in_(chunk),
                                             StudentDocument.category == "attest",
                                             StudentDocument.withdrawn_at.is_(None))):
            docs[aid].append(status)
    out: dict[int, dict] = {}
    for r in rows:
        ids = [a.id for a in absences.get(r.student_id, ())
               if a.date_from <= r.exam_date <= a.date_to]
        statuses = [s for aid in ids for s in docs.get(aid, ())]
        if r.attest_waived:
            state = "nicht_noetig"
        elif "geprueft" in statuses:
            state = "genehmigt"
        elif "eingegangen" in statuses:
            state = "eingereicht"
        elif "abgelehnt" in statuses:
            state = "abgelehnt"
        else:
            state = "fehlt"
        out[r.id] = {"state": state, "label": ATTEST_LABELS[state], "missing": state in ("fehlt", "abgelehnt"),
                     "absence_ids": ids}
    return out


def _chunks(seq: list, size: int = 400) -> Iterable[list]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# ----------------------------------------------------------------------------- Zugriff
class MakeupAccess:
    """Wer sieht welche Nachschreib-Zeile (siehe Moduldoku)."""

    def __init__(self, user: Any, snap: Any, db: Session):
        self.user, self.snap, self.db, self.school = user, snap, db, snap[1]
        self.abs = AbsenceAccess(user, snap, db)
        self.admin = getattr(user, "role", "") == "admin"
        self._exams = {e.id: e for e in self.school.exams}

    def exam(self, row: ExamMakeup) -> Any:
        return self._exams.get(row.exam_id)

    def teaches(self, exam: Any) -> bool:
        """Darf Termine zu dieser Klausur festlegen (``exam.edit``, bei Lehrkräften nur eigene Kurse)."""
        if self.admin or exam is None:
            return False
        from .routes.features_exams import _can_edit
        return _can_edit(self.user, self.school, exam)

    def level(self, row: ExamMakeup) -> Optional[str]:
        if self.admin:
            return None
        lvl = self.abs.level(row.student_id)
        if lvl in (FULL, FAMILY):
            return lvl
        if self.teaches(self.exam(row)):
            return TEACHER
        return None


# ----------------------------------------------------------------------------- Konflikte
def own_lessons(school: Any, exam: Any, day: date, student_ids: Iterable[str]
                ) -> dict[str, tuple[Any, frozenset[str]]]:
    """Unterrichtsblöcke am Tag, die eine Lehrkraft der Klausur selbst hält und in denen mindestens eine der
    ``student_ids`` sitzt: ``{Block-ID: (Block, betroffene Schüler/innen im Block)}`` – dort kann ohnehin gemeinsam
    geschrieben werden (die Lehrkraft ist ja im Raum)."""
    from schulmanager.exams import lessons_active_on

    courses = school.index("courses")
    course = courses.get(exam.course_id)
    wanted = frozenset(student_ids)
    if course is None or not wanted:
        return {}
    teachers = {p.teacher for i, p in enumerate(course.parts) if p.teacher and (exam.part is None or i == exam.part)}
    out: dict[str, tuple[Any, frozenset[str]]] = {}
    for les in lessons_active_on(school, day):
        lc = courses.get(les.course_id)
        if lc is None:
            continue
        members = part_members(school, lc)
        sitting: set[str] = set()
        for i, p in enumerate(lc.parts):
            if p.teacher in teachers and i < len(members):
                sitting |= wanted & members[i]
        if sitting:
            out[les.id] = (les, frozenset(sitting))
    return out


def check_date(school: Any, db: Session, exam: Any, day: date, start: int, length: int, room: Optional[str],
               ignore_date_id: Optional[int] = None, student_ids: Optional[Iterable[str]] = None) -> list[str]:
    """Konflikte eines Nachschreibtermins (leer = frei): Schultag, Zeitraster, Raum und Lehrkraft gegen Klausuren,
    andere Nachschreibtermine und den Stundenplan. Mit ``student_ids`` zählen eigene Stunden der Lehrkraft, in denen
    diese Kinder ohnehin sitzen, nicht als Konflikt (gemeinsames Schreiben im Unterricht)."""
    from schulmanager.calendar_utils import class_days, holiday_name
    from schulmanager.exams import lessons_active_on

    problems: list[str] = []
    st = school.settings
    course = school.index("courses").get(exam.course_id)
    length = max(1, length)
    span = set(range(start, start + length))
    hol = holiday_name(school, day)
    classes = list(course.classes) if course else []
    teaching = any(day.weekday() in class_days(school, c) for c in classes) if classes else day.weekday() < st.days
    if hol:
        problems.append(f"{day.strftime('%d.%m.%Y')} ist kein Schultag ({hol})")
    elif not teaching:
        problems.append(f"{day.strftime('%d.%m.%Y')}: Kein Unterrichtstag der Klasse.")
    if start < 0 or start + length > st.periods:
        problems.append("Der Termin liegt außerhalb des Zeitrasters")
    teachers = {p.teacher for i, p in enumerate(course.parts) if p.teacher
                and (exam.part is None or i == exam.part)} if course else set()
    courses = school.index("courses")
    iso = day.isoformat()
    for other in school.exams:
        if str(other.date)[:10] != iso or not span & _span(other):
            continue
        oc = courses.get(other.course_id)
        ot = {p.teacher for p in oc.parts if p.teacher} if oc else set()
        if room and other.room == room:
            problems.append(f"Raum {room} ist durch die Klausur {other.title or other.id} belegt")
        if teachers & ot:
            problems.append(f"{', '.join(sorted(teachers & ot))} schreibt zu der Zeit die Klausur "
                            f"{other.title or other.id}")
    for dt in db.scalars(select(ExamMakeupDate).where(ExamMakeupDate.date == iso)):
        if dt.id == ignore_date_id:
            continue
        if not span & set(range(dt.start, dt.start + max(1, dt.length))):
            continue
        oe = next((e for e in school.exams if e.id == dt.exam_id), None)
        oc = courses.get(oe.course_id) if oe else None
        ot = {p.teacher for p in oc.parts if p.teacher} if oc else set()
        if room and dt.room == room:
            problems.append(f"Raum {room} ist durch einen anderen Nachschreibtermin belegt")
        if teachers & ot:
            problems.append(f"{', '.join(sorted(teachers & ot))} hat zu der Zeit einen anderen Nachschreibtermin")
    mine = own_lessons(school, exam, day, student_ids) if student_ids else {}
    for les in lessons_active_on(school, day):
        if not span & set(range(les.start, les.start + max(1, les.length))) or les.id in mine:
            continue
        lc = courses.get(les.course_id)
        if lc is None:
            continue
        if room and room in [r for r in les.rooms if r]:
            problems.append(f"Raum {room} ist laut Stundenplan belegt ({lc.label or lc.id})")
        busy = teachers & {p.teacher for p in lc.parts if p.teacher}
        if busy:
            problems.append(f"{', '.join(sorted(busy))} hat laut Stundenplan Unterricht ({lc.label or lc.id})")
    seen: set[str] = set()
    return [p for p in problems if not (p in seen or seen.add(p))]


# ----------------------------------------------------------------------------- Vorschläge
SUGGEST_HORIZON = 28       # Tage nach der Klausur bzw. ab morgen, in denen Termine vorgeschlagen werden
SUGGEST_LIMIT = 12


def suggest(school: Any, db: Session, exam: Any, student_ids: Iterable[str], today: Optional[date] = None,
            horizon: int = SUGGEST_HORIZON, limit: int = SUGGEST_LIMIT) -> list[dict]:
    """Terminvorschläge für das Nachschreiben von ``student_ids``, sortiert nach Eignung.

    ``kind="unterricht"``: Stunde, die eine Lehrkraft der Klausur ohnehin hält und in der betroffene Kinder sitzen
    (``student_ids`` = diese Kinder; Raum der Stunde). ``kind="frei"``: Zeit, in der Lehrkraft, **alle** Kinder und ein
    Raum frei sind (``slot``: ``luecke`` = Freistunde zwischen zwei Stunden, ``rand`` = direkt vor der ersten bzw. nach
    der letzten Stunde der Kinder). Schulfreie Tage/Ferien, Klausuren und andere Nachschreibtermine werden
    berücksichtigt. Sortierung: Nähe zu heute, Unterricht vor freier Zeit, Lücke vor Rand; höchstens drei je Tag."""
    from datetime import timedelta

    from schulmanager.calendar_utils import class_days, holiday_name
    from schulmanager.exams import _class_unavailable, lessons_active_on

    wanted = frozenset(student_ids)
    courses = school.index("courses")
    course = courses.get(exam.course_id)
    if course is None or not wanted:
        return []
    st = school.settings
    today = today or date.today()
    first = max(today, _exam_day(exam) or today) + timedelta(days=1)
    teachers = {p.teacher for i, p in enumerate(course.parts) if p.teacher and (exam.part is None or i == exam.part)}
    students = school.index("students")
    classes_of = {students[s].class_id for s in wanted if s in students}
    length = max(1, exam.length or 1)
    rooms = [r.id for r in school.rooms]
    dated: dict[str, list[ExamMakeupDate]] = defaultdict(list)
    last = (first + timedelta(days=horizon)).isoformat()
    for dt in db.scalars(select(ExamMakeupDate).where(ExamMakeupDate.date >= first.isoformat(),
                                                      ExamMakeupDate.date <= last)):
        dated[dt.date].append(dt)
    members_cache: dict[str, list[frozenset[str]]] = {}

    def members(c: Any) -> list[frozenset[str]]:
        if c.id not in members_cache:
            members_cache[c.id] = part_members(school, c)
        return members_cache[c.id]

    out: list[dict] = []
    for offset in range(horizon):
        day = first + timedelta(days=offset)
        iso = day.isoformat()
        if holiday_name(school, day) or not all(day.weekday() in class_days(school, c) for c in classes_of):
            continue
        busy_t: set[int] = set()
        busy_room: dict[str, set[int]] = defaultdict(set)
        busy_stud: dict[str, set[int]] = defaultdict(set)
        own = own_lessons(school, exam, day, wanted)
        for les in lessons_active_on(school, day):
            span = set(range(les.start, les.start + max(1, les.length)))
            lc = courses.get(les.course_id)
            if lc is None:
                continue
            for r in les.rooms:
                if r:
                    busy_room[r] |= span
            if les.id not in own and any(p.teacher in teachers for p in lc.parts):
                busy_t |= span
            for mem in members(lc):
                for sid in mem & wanted:
                    busy_stud[sid] |= span
        for other in school.exams:
            if str(other.date)[:10] != iso:
                continue
            span = set(range(other.start, other.start + max(1, other.length)))
            oc = courses.get(other.course_id)
            if other.room:
                busy_room[other.room] |= span
            if oc is not None:
                if {p.teacher for p in oc.parts if p.teacher} & teachers:
                    busy_t |= span
                for mem in members(oc):
                    for sid in mem & wanted:
                        busy_stud[sid] |= span
        for dt in dated.get(iso, ()):
            span = set(range(dt.start, dt.start + max(1, dt.length)))
            if dt.room:
                busy_room[dt.room] |= span
            oe = next((e for e in school.exams if e.id == dt.exam_id), None)
            oc = courses.get(oe.course_id) if oe else None
            if oc is not None and {p.teacher for p in oc.parts if p.teacher} & teachers:
                busy_t |= span
        near = float(offset)
        # a) eigene Stunden der Lehrkraft, in denen betroffene Kinder sitzen
        for les, sitting in own.values():
            span = set(range(les.start, les.start + max(1, les.length)))
            if max(span) >= st.periods or any(_class_unavailable(school, cid, day, p)
                                              for cid in classes_of for p in span):
                continue
            if any(span & set(range(e.start, e.start + max(1, e.length))) and sitting & exam_students(school, e)
                   for e in school.exams if str(e.date)[:10] == iso):
                continue
            allc = sitting == wanted
            out.append({"kind": "unterricht", "date": iso, "start": les.start, "length": max(1, les.length),
                        "room": next((r for r in les.rooms if r), None), "student_ids": sorted(sitting),
                        "covers_all": allc, "score": near - (5 if allc else 3),
                        "reason": "Eigene Stunde, in der " + ("die Kinder" if allc else f"{len(sitting)} von "
                                                              f"{len(wanted)} Kindern") + " ohnehin sitzen"})
        # b) freie Zeit außerhalb des Unterrichts
        if not any(busy_stud[sid] for sid in wanted):
            continue                                        # Tag ohne Unterricht der Kinder: nicht vorschlagen
        for start in range(0, st.periods - length + 1):
            span = set(range(start, start + length))
            if span & busy_t or any(span & busy_stud[sid] for sid in wanted):
                continue
            if any(_class_unavailable(school, cid, day, p) for cid in classes_of for p in span):
                continue
            if exam.room and not span & busy_room[exam.room]:
                room: Optional[str] = exam.room
            else:
                room = next((r for r in rooms if not span & busy_room[r]), None)
            if room is None:
                continue
            slots = set()
            for sid in wanted:
                lessons = sorted(busy_stud[sid])
                if not lessons:
                    slots.add("frei")
                elif lessons[0] < start and start + length - 1 < lessons[-1]:
                    slots.add("luecke")
                elif start + length == lessons[0] or start == lessons[-1] + 1:
                    slots.add("rand")
                else:
                    slots.add("frei")
            slot = "frei" if "frei" in slots else "rand" if "rand" in slots else "luecke"
            if slot == "frei":
                continue                                    # weder Randstunde noch Freistunde: nicht sinnvoll
            label = "Freistunde der Kinder" if slot == "luecke" else "Randstunde"
            out.append({"kind": "frei", "slot": slot, "date": iso, "start": start, "length": length, "room": room,
                        "student_ids": sorted(wanted), "covers_all": True,
                        "score": near + (0.0 if slot == "luecke" else 1.0),
                        "reason": f"{label}; Lehrkraft, alle Kinder und Raum {room} sind frei"})
    out.sort(key=lambda x: (x["score"], x["date"], x["start"]))
    picked: list[dict] = []
    per_day: dict[str, int] = defaultdict(int)
    for item in out:
        if per_day[item["date"]] >= 3:
            continue
        per_day[item["date"]] += 1
        picked.append(item)
        if len(picked) >= limit:
            break
    times = st.period_times
    for item in picked:
        item["time"] = times[item["start"]] if 0 <= item["start"] < len(times) else ""
        del item["score"]
    return picked


__all__ = ["MAKEUP_STATUS", "SOURCE_LABELS", "ATTEST_LABELS", "MakeupAccess", "attest_states", "check_date",
           "exam_students", "install_hooks", "own_lessons", "suggest", "sync", "sync_now"]
