"""Ereignisquellen der Benachrichtigungszentrale: übersetzt Ereignisse des Schulmanagers in ``notifications.notify``.

Jede Funktion hier wird von einer bestehenden Stelle **nach dem Commit** aufgerufen, fängt alle Fehler selbst ab (eine
Benachrichtigung darf die Aktion nie verhindern) und schreibt nur Titel/Texte **ohne sensible Einzelheiten**
(„Neue Krankmeldung“, keine Gründe, Diagnosen, Noten oder Kommentare). Neue Funktionen anderer Bereiche rufen
:func:`schulmanager.server.notifications.notify` direkt auf (``docs/BENACHRICHTIGUNGEN.md``).

Quellen
-------
* :func:`plan_changes` – Vertretung/Entfall/Aufsicht (aus ``notify.check_changes``): Lehrkräfte, Schüler/innen, Eltern.
* :func:`absence_received`, :func:`absence_status` – Krankmeldung eingegangen / bestätigt; :func:`reminders` – Attest fehlt.
* :func:`form_decided`, :func:`teacher_request_decided` – Anträge.
* :func:`channel_item_created`, :func:`submission_graded`, :func:`reminders` – Kursraum (neu, bewertet, fällig morgen).
* :func:`exam_changed` – Klausur angesetzt, verschoben, abgesagt.
* :func:`plan_proposal_ready` – neuer Vorschlag der Plan-Prüfung für Planende.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Optional

from sqlalchemy import select

from . import notifications as nt
from .db import session_scope, utcnow
from .db_models import StudentAbsence, User

log = logging.getLogger("schulmanager.notification_hooks")

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
AREA_TIMETABLE = "stundenplan"
AREA_SICK = "krankmeldungen"
AREA_CHANNELS = "kursraeume"
AREA_GRADES = "noten"
AREA_DOCS = "dokumente"
# Arten im Vertretungsplan, die den Unterricht einer Klasse betreffen (Schüler/Eltern erfahren davon)
STUDENT_KINDS = ("vertretung", "betreuung", "mitbetreuung", "entfall", "verlegung", "raumaenderung",
                 "klasse_abwesend")
TEACHER_KINDS = ("entfall", "verlegung", "raumaenderung", "mitbetreuung", "klasse_abwesend")


def _safe(fn):
    """Fehler abfangen und loggen – Hooks dürfen nie die Aktion stören, die sie auslöst."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:  # noqa: BLE001
            log.exception("Benachrichtigung (%s) fehlgeschlagen", fn.__name__)
            return None
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def _school():
    from .routes.features_common import snapshot
    return snapshot()[1]


def _day_text(d: date) -> str:
    return f"{WEEKDAYS[d.weekday()]} {d.strftime('%d.%m.')}"


# =========================================================================== Vertretungsplan
def _entry_line(entry: dict, removed: bool) -> str:
    from .notify import KIND_LABELS
    p = entry.get("period")
    label = entry.get("period_label") or (f"{p + 1}." if isinstance(p, int) else "")
    what = KIND_LABELS.get(entry.get("kind") or "", entry.get("kind") or "Änderung")
    if entry.get("kind") == "aufsicht":
        head = entry.get("break_name") or "Pause"
        text = f"{head}: {what}"
    else:
        subject = entry.get("subject") or ""
        text = f"{label} Stunde {subject}: {what}".replace("  ", " ")
    return f"{text} (aufgehoben)" if removed else text


def _student_matches(st, entry: dict, courses: dict) -> bool:
    from schulmanager.channels import student_course_parts
    if st.class_id not in (entry.get("classes") or []):
        return False
    course = courses.get(entry.get("course_id") or "")
    part = entry.get("part")
    if course is None or not isinstance(part, int) or len(course.parts) <= 1:
        return True
    return part in student_course_parts(st, course)


def _compose(day: date, kind: str, lines: list[str]) -> tuple[str, str]:
    lines = list(dict.fromkeys(lines))
    title = ("Pausenaufsicht geändert – " if kind == "duty" else "Vertretungsplan geändert – ") + _day_text(day)
    shown = " · ".join(lines[:3])
    if len(lines) > 3:
        shown += f" · und {len(lines) - 3} weitere"
    return title, shown


@_safe
def plan_changes(school, day: date, diff: dict[str, list], plan: Optional[dict] = None) -> int:
    """Vergleich zweier Vertretungsplan-Stände eines Tages → Benachrichtigungen. Rückgabe: Anzahl Empfänger-Meldungen."""
    from .notify import _affected
    absent = set((plan or {}).get("absent_teachers") or [])
    entries = [(e, False) for e in diff.get("added", [])] + [(e, False) for e in diff.get("changed", [])] \
        + [(e, True) for e in diff.get("removed", [])]
    if not entries:
        return 0
    courses = school.index("courses")
    students_by_class: dict[str, list] = {}
    for st in school.students:
        students_by_class.setdefault(st.class_id, []).append(st)
    teacher_lines: dict[str, dict[str, list[str]]] = {}      # Lehrkraft → Art → Zeilen
    student_lines: dict[str, list[str]] = {}                 # Schüler → Zeilen
    for entry, removed in entries:
        kind = entry.get("kind") or ""
        line = _entry_line(entry, removed)
        bucket = "duty" if kind == "aufsicht" else "substitution"
        tids = set(_affected(entry, absent))
        if kind in TEACHER_KINDS and entry.get("teacher"):
            tids.add(entry["teacher"])
        if kind == "entfall" and entry.get("teacher"):
            tids.add(entry["teacher"])           # die eigene Stunde fällt aus – auch wenn man selbst fehlt
        for tid in tids:
            teacher_lines.setdefault(tid, {}).setdefault(bucket, []).append(line)
        if kind in STUDENT_KINDS:
            for cls in entry.get("classes") or []:
                for st in students_by_class.get(cls, ()):
                    if _student_matches(st, entry, courses):
                        student_lines.setdefault(st.id, []).append(line)
    sent = 0
    link_staff = f"/vertretung?date={day.isoformat()}"
    with session_scope() as db:
        for tid, buckets in teacher_lines.items():
            uids = nt.users_of_teachers(db, [tid])
            for bucket, lines in buckets.items():
                title, body = _compose(day, bucket, lines)
                key = nt.dedupe_key("plan", day, bucket, tid, "|".join(sorted(set(lines))))
                sent += len(nt.notify(uids, bucket, title, link_staff, body=body, dedupe=key, db=db))
        parents = nt.parents_by_student(db, student_lines, AREA_TIMETABLE, school)
        own = {}
        for sid in student_lines:
            own[sid] = nt.users_of_students(db, [sid])
        for sid, lines in student_lines.items():
            title, body = _compose(day, "substitution", lines)
            key = nt.dedupe_key("plan", day, "substitution", sid, "|".join(sorted(set(lines))))
            sent += len(nt.notify(own.get(sid, []) + parents.get(sid, []), "substitution", title, "/stundenplan",
                                  body=body, student_id=sid, dedupe=key, db=db))
    return sent


# =========================================================================== Krankmeldung
def _class_teacher_users(db, school, student_id: str) -> list[int]:
    st = school.index("students").get(student_id)
    cls = school.index("classes").get(st.class_id) if st else None
    return nt.users_of_teachers(db, [cls.class_teacher]) if cls and cls.class_teacher else []


@_safe
def absence_received(absence_id: int, actor_id: Optional[int] = None) -> None:
    """Neue Krankmeldung: Klassenleitung und Sekretariat; Familie, wenn die Schule sie erfasst hat."""
    school = _school()
    with session_scope() as db:
        row = db.get(StudentAbsence, absence_id)
        if row is None:
            return
        st = school.index("students").get(row.student_id)
        cls = st.class_id if st else ""
        kind = row.kind or "krank"
        staff = _class_teacher_users(db, school, row.student_id) + list(
            db.scalars(select(User.id).where(User.role == "sekretariat", User.active.is_(True))))
        label = {"krank": "Neue Krankmeldung", "beurlaubung": "Neue Beurlaubung",
                 "verspaetung": "Neue Verspätungsmeldung", "frueh": "Neue Meldung: früher gegangen",
                 "fehlt": "Neue Fehlzeit erfasst"}.get(kind, "Neue Krankmeldung")
        family_label = {"krank": "Krankmeldung eingegangen", "beurlaubung": "Beurlaubung eingetragen",
                        "verspaetung": "Verspätung eingetragen", "frueh": "Früher gegangen eingetragen",
                        "fehlt": "Fehlzeit eingetragen"}.get(kind, "Krankmeldung eingegangen")
        nt.notify(staff, "absence", label, "/krankmeldungen", body=f"Klasse {cls}" if cls else "",
                  student_id=row.student_id, actor_id=actor_id, dedupe=f"absence:{absence_id}:new", db=db)
        # meldet die Schule (nicht die Familie), erfährt die Familie davon
        reporter = db.get(User, row.reported_by) if row.reported_by else None
        if reporter is None or reporter.role not in ("eltern", "schueler"):
            nt.notify(nt.family_of(db, row.student_id, AREA_SICK, school=school), "absence",
                      family_label, "/krankmeldungen", student_id=row.student_id, actor_id=actor_id,
                      dedupe=f"absence:{absence_id}:family", db=db)


@_safe
def absence_status(absence_id: int, actor_id: Optional[int] = None) -> None:
    """Status geändert: „bestätigt“ (entschuldigt) bzw. „nicht entschuldigt“ → Familie."""
    school = _school()
    with session_scope() as db:
        row = db.get(StudentAbsence, absence_id)
        if row is None or row.status not in ("entschuldigt", "unentschuldigt"):
            return
        title = "Krankmeldung bestätigt" if row.status == "entschuldigt" else "Fehlzeit nicht entschuldigt"
        nt.notify(nt.family_of(db, row.student_id, AREA_SICK, school=school), "absence", title, "/krankmeldungen",
                  student_id=row.student_id, actor_id=actor_id,
                  dedupe=f"absence:{absence_id}:{row.status}", db=db)


# =========================================================================== Anträge
@_safe
def form_decided(submission_id: int, actor_id: Optional[int] = None) -> None:
    """Formular genehmigt/abgelehnt/erledigt → die einreichende Person und (je Einwilligung) die Familie."""
    from .feature_models.forms import FormSubmission, FormTemplate
    school = _school()
    with session_scope() as db:
        sub = db.get(FormSubmission, submission_id)
        if sub is None or sub.status not in ("genehmigt", "abgelehnt", "erledigt"):
            return
        tpl = db.get(FormTemplate, sub.template_id)
        title = {"genehmigt": "Antrag genehmigt", "abgelehnt": "Antrag abgelehnt", "erledigt": "Antrag bearbeitet"}[
            sub.status]
        ids = [sub.submitted_by] if sub.submitted_by else []
        if sub.student_id:
            ids += nt.family_of(db, sub.student_id, AREA_DOCS, school=school)
        nt.notify(ids, "request_decided", title, "/formulare", body=(tpl.title if tpl else ""),
                  student_id=sub.student_id, actor_id=actor_id, dedupe=f"form:{submission_id}:{sub.status}", db=db)


@_safe
def teacher_request_decided(row: Any) -> None:
    """Antrag einer Lehrkraft (Profil/Ausnahme) genehmigt oder abgelehnt."""
    if row.status not in ("genehmigt", "abgelehnt"):
        return
    what = "Ausnahme" if getattr(row, "kind", "") == "ausnahme" else "Profiländerung"
    title = f"Antrag genehmigt: {what}" if row.status == "genehmigt" else f"Antrag abgelehnt: {what}"
    with session_scope() as db:
        ids = [row.user_id] if row.user_id else nt.users_of_teachers(db, [row.teacher_id])
        nt.notify(ids, "request_decided", title, "/lehrkraft/profil", actor_id=getattr(row, "reviewer_id", None),
                  dedupe=f"teacher_request:{row.id}:{row.status}", db=db)


# =========================================================================== Kursräume
def _channel_title(ctx) -> str:
    spec = getattr(ctx, "spec", None)
    return (spec.title if spec else getattr(ctx.ch, "title", "")) or "Kursraum"


def _students_and_parents(db, school, member_ids: Iterable[int], area: str) -> list[tuple[int, Optional[str]]]:
    """Schülerkonten unter den Mitgliedern und deren Eltern (je Einwilligung): ``[(Konto, Schüler-ID)]``."""
    ids = sorted(set(member_ids))
    rows = db.execute(select(User.id, User.student_id).where(User.id.in_(ids or [-1]), User.role == "schueler",
                                                             User.active.is_(True))).all()
    out: list[tuple[int, Optional[str]]] = [(uid, sid) for uid, sid in rows]
    parents = nt.parents_by_student(db, [sid for _, sid in rows if sid], area, school)
    for _, sid in rows:
        out += [(p, sid) for p in parents.get(sid, [])]
    return out


@_safe
def channel_item_created(db, ctx, items: Iterable[Any]) -> None:
    """Neue Aufgabe/neues Material, sichtbar für Teilnehmende → Schüler/innen und Eltern (nicht für die Lehrenden).
    Verborgene/zeitlich freigegebene Inhalte lösen nichts aus."""
    from .routes.features_channels import _member_user_ids
    items = [i for i in items if getattr(i, "visibility", "visible") == "visible" and not getattr(i, "info_card", False)]
    if not items:
        return
    members = _member_user_ids(db, ctx.ch, ctx.spec, ctx.school)
    recipients = _students_and_parents(db, ctx.school, members, AREA_CHANNELS)
    if not recipients:
        return
    room = _channel_title(ctx)
    link = f"/kursraeume/{ctx.ch.id}"
    tasks = [i for i in items if i.type == "assignment"]
    title = "Neue Aufgabe im Kursraum" if tasks and len(tasks) == len(items) else "Neues Material im Kursraum"
    if len(items) > 1:
        title = "Neue Inhalte im Kursraum"
    body = room if len(items) > 1 else f"{room}: {items[0].title}"
    key = "item:" + ",".join(str(i.id) for i in items)[:50]
    with session_scope() as out:       # eigene Transaktion: der Aufrufer hat seine schon abgeschlossen
        for uid, sid in recipients:
            nt.notify([uid], "course_item", title, link, body=body, student_id=sid, actor_id=ctx.user.id, dedupe=key,
                      ref=f"channel:{ctx.ch.id}", db=out)


@_safe
def submission_graded(db, ctx, item: Any, sub: Any) -> None:
    """Abgabe bewertet bzw. zur Überarbeitung zurückgegeben → Schüler/in und Eltern (Einwilligung „Noten“)."""
    ids = nt.users_of_students(db, [sub.student_id]) if sub.student_id else [sub.student_user_id]
    ids = list(dict.fromkeys(ids + [sub.student_user_id]))
    if sub.student_id:
        ids += nt.parents_by_student(db, [sub.student_id], AREA_GRADES, ctx.school).get(sub.student_id, [])
    title = "Aufgabe zur Überarbeitung zurückgegeben" if sub.status == "zurueckgegeben" else "Abgabe bewertet"
    stamp = sub.feedback_at.isoformat() if sub.feedback_at else ""
    nt.notify(ids, "task_graded", title, f"/kursraeume/{ctx.ch.id}", body=f"{_channel_title(ctx)}: {item.title}",
              student_id=sub.student_id, actor_id=ctx.user.id, dedupe=nt.dedupe_key("graded", sub.id, sub.status, stamp),
              ref=f"channel:{ctx.ch.id}")


# =========================================================================== Klausuren
@_safe
def exam_changed(exam: Any, action: str, actor_id: Optional[int] = None, old: Any = None) -> None:
    """``action``: ``created|updated|deleted``. Betroffene: Kursteilnehmende, deren Eltern, Lehrkräfte des Kurses."""
    from schulmanager.channels import student_course_parts
    school = _school()
    course = school.index("courses").get(exam.course_id)
    if course is None:
        return
    if action == "updated" and old is not None and (old.date, old.start) == (exam.date, exam.start):
        return                                   # nur Raum/Titel geändert: kein Termin-Hinweis
    kind_word = "Test" if getattr(exam, "kind", "klausur") == "test" else "Klausur"
    title = {"created": f"{kind_word} angesetzt", "updated": f"{kind_word} verschoben",
             "deleted": f"{kind_word} abgesagt"}[action]
    try:
        when = _day_text(date.fromisoformat(exam.date)) + f", {exam.start + 1}. Stunde"
    except ValueError:
        when = exam.date
    body = f"{course.label if getattr(course, 'label', '') else exam.course_id}: {when}" if action != "deleted" \
        else (course.label if getattr(course, "label", "") else exam.course_id)
    students = [s for s in school.students if s.class_id in course.classes
                and (exam.part is None or exam.part in student_course_parts(s, course))]
    teachers = {p.teacher for i, p in enumerate(course.parts) if p.teacher and (exam.part is None or exam.part == i)}
    with session_scope() as db:
        sids = [s.id for s in students]
        parents = nt.parents_by_student(db, sids, AREA_TIMETABLE, school)
        for st in students:
            uids = nt.users_of_students(db, [st.id]) + parents.get(st.id, [])
            nt.notify(uids, "exam", title, "/klausuren", body=body, student_id=st.id, actor_id=actor_id,
                      dedupe=nt.dedupe_key("exam", exam.id, action, exam.date, exam.start, st.id), db=db)
        nt.notify(nt.users_of_teachers(db, teachers), "exam", title, "/klausuren", body=body, actor_id=actor_id,
                  dedupe=nt.dedupe_key("exam", exam.id, action, exam.date, exam.start, "t"), db=db)


# =========================================================================== Plan-Prüfung
@_safe
def plan_proposal_ready(package_id: int) -> None:
    with session_scope() as db:
        ids = nt.users_with_permission(db, "timetable.generate", "timetable.edit", "settings.edit")
        nt.notify(ids, "plan_proposal", "Neuer Vorschlag für den Stundenplan", "/planung/vorschlaege",
                  dedupe=f"proposal:{package_id}", ref=f"proposal:{package_id}", db=db)


# =========================================================================== Erinnerungen (stündlich)
def reminders(now: Optional[datetime] = None) -> dict[str, int]:
    """Fristen („fällig morgen“) und fehlende Atteste. Je Aufgabe/Meldung höchstens einmal je Konto (``dedupe``)."""
    out = {"task_due": 0, "attest_missing": 0}
    out["task_due"] = _due_tomorrow(now) or 0
    out["attest_missing"] = _attest_missing(now) or 0
    return out


@_safe
def _due_tomorrow(now: Optional[datetime] = None) -> int:
    from schulmanager.channels import channel_spec, local_to_utc, utc_to_local
    from .feature_models.channels import AssignmentSubmission, Channel, ChannelItem
    from .routes.features_channels import _member_user_ids
    school = _school()
    now = now or utcnow()
    tomorrow = utc_to_local(now).date() + timedelta(days=1)
    start = local_to_utc(datetime.combine(tomorrow, datetime.min.time()).astimezone())
    end = start + timedelta(days=1)
    count = 0
    with session_scope() as db:
        items = db.scalars(select(ChannelItem).where(ChannelItem.type == "assignment", ChannelItem.due_at >= start,
                                                     ChannelItem.due_at < end, ChannelItem.visibility == "visible"))
        for item in list(items):
            ch = db.get(Channel, item.channel_id)
            if ch is None or ch.archived:
                continue
            spec = channel_spec(school, ch.kind, ch.ref) if ch.ref else None
            members = _member_user_ids(db, ch, spec, school)
            done = set(db.scalars(select(AssignmentSubmission.student_user_id)
                                  .where(AssignmentSubmission.item_id == item.id,
                                         AssignmentSubmission.submitted_at.is_not(None))))
            pending = [m for m in members if m not in done]
            room = (spec.title if spec else ch.title) or "Kursraum"
            for uid, sid in _students_and_parents(db, school, pending, AREA_CHANNELS):
                count += len(nt.notify([uid], "task_due", "Aufgabe ist morgen fällig", f"/kursraeume/{ch.id}",
                                       body=f"{room}: {item.title}", student_id=sid, dedupe=f"due:{item.id}",
                                       ref=f"channel:{ch.id}", db=db))
    return count


@_safe
def _attest_missing(now: Optional[datetime] = None) -> int:
    from .routes.features_student_self import attest_map
    school = _school()
    now = now or utcnow()
    since = (now - timedelta(days=30)).date().isoformat()
    count = 0
    with session_scope() as db:
        rows = list(db.scalars(select(StudentAbsence).where(StudentAbsence.date_to >= since,
                                                            StudentAbsence.kind == "krank")))
        if not rows:
            return 0
        info = attest_map(db, school, rows)
        for r in rows:
            if not (info.get(r.id) or {}).get("missing"):
                continue
            count += len(nt.notify(nt.family_of(db, r.student_id, AREA_SICK, school=school), "attest_missing",
                                   "Attest fehlt", "/krankmeldungen", student_id=r.student_id,
                                   dedupe=f"attest:{r.id}", db=db))
    return count
