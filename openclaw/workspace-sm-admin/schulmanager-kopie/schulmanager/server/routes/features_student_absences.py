"""Krankmeldungen von Schüler/innen (Tabelle ``student_absences``, A-58/B-06).

Wer was sieht und darf, entscheidet :mod:`schulmanager.server.absence_access` (Stufen ``full``/``family``/``teacher``):

* Melden (``student_absence.report``): Sekretariat und Klassenleitung beliebig, Fachlehrkräfte nur für die eigene
  Stunde (ein Tag, nicht in der Zukunft), Eltern für ihre Kinder (Volljährige nur mit Freigabe ``krankmeldungen``),
  volljährige Schüler/innen für sich.
* Lesen (``student_absence.read``): Sekretariat/Schulleitung alle, Klassenleitung ihre Klasse, Schüler/innen eigene,
  Eltern die ihrer Kinder (Volljährige nur mit Freigabe). Fachlehrkräfte sehen nur eigene Meldungen – mit dem
  Schulschalter ``subject_teacher_absence_view = "presence"`` zusätzlich „fehlt heute in meiner Stunde“ (Name und
  Stunde, ohne Status, Attest, Grund und meldende Person).
* Status setzen (``gemeldet|entschuldigt|unentschuldigt``), Vermerk ändern, Löschen: nur Klassenleitung, Sekretariat,
  Schulleitung; die meldende Person darf ihre Meldung löschen, solange sie „gemeldet“ ist. Fremde Meldungen → 404.
* Überlappende Meldungen derselben Person: eigene, noch „gemeldete“ Meldung wird zusammengeführt (Verlängern,
  weitere Stunden desselben Tages); die noch „gemeldete“ Stunden-Meldung einer Fachlehrkraft, die in der neuen ganz
  enthalten ist, übernehmen Familie, Klassenleitung, Sekretariat und Schulleitung (danach ohne Eigentümer: die Fachlehrkraft
  sieht sie nicht mehr, löschen nur noch Klassenleitung/Sekretariat/Schulleitung); sonst 409 mit Hinweis. Zeiträume ohne Schultag
  (Wochenende, Ferien) → 422.
* Gründe und Vermerke sind Gesundheitsdaten: nur **verschlüsselt** gespeichert (AAD ``student_absences.<feld>:<id>``).
* Jede Krankmeldung trägt den Attest-Zustand (``attest``, siehe ``schulmanager.student_self``).
* Arten (``kind``): ``krank``, ``verspaetung`` (zu spät, ``minutes``), ``frueh`` (früher gegangen), ``fehlt`` (ohne
  Meldung gefehlt – erfasst das Personal, z. B. aus dem Klassenbuch), ``beurlaubung`` (vorher beantragt, mit Anlass;
  Status heißen dort beantragt/genehmigt/abgelehnt, kein Attest). Herkunft ``source``: online, telefon, schriftlich,
  lehrkraft. Status ``teilweise`` = telefonisch gemeldet, schriftliche Entschuldigung fehlt noch.
* Rückgängig/Änderung durch die Familie (und Personal mit vollem Zugriff): ``DELETE`` (zurücknehmen, solange „gemeldet“),
  ``POST /{id}/shorten`` (früher zurück), ``POST /{id}/extend`` (verlängern), ``POST /{id}/request-withdrawal``
  (Rücknahme anfragen, wenn schon bearbeitet), ``POST /{id}/return-leave`` (genehmigte Beurlaubung zurückgeben);
  jede Aktion steht im Meldungsprotokoll (``absence_log``), Klassenleitung wird live informiert. Welche Aktionen eine
  Meldung gerade bietet, steht in ``actions`` (Familien-Sicht).
* ``GET /student-absences/record?student_id=`` Fehlzeiten-Übersicht eines Kindes mit Summen;
  ``GET /student-absences/form.pdf`` Formular „Schriftliche Entschuldigung“ (vorausgefüllt mit ``student_id``/``absence_id``).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from schulmanager.branding import PRODUCT_NAME
from schulmanager.server import absence_log as alog
from schulmanager.server.absence_access import FAMILY, FAMILY_ROLES, FULL, TEACHER, AbsenceAccess
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user

from .features_common import has, index, iso_dates, own_student_ids, parse_date, publish_change, snapshot, write_audit

router = APIRouter(tags=["Krankmeldungen"])

MAX_DAYS = 60
MAX_BACKDATE_DAYS = 30
PUPIL_ROLES = FAMILY_ROLES
NOT_FOUND = "Krankmeldung nicht gefunden"


def _today() -> date:
    """Heutiges Datum (eigene Funktion, damit Tests einen festen Tag setzen können)."""
    return date.today()


STATUSES = ("gemeldet", "teilweise", "entschuldigt", "unentschuldigt")
STATUS_LABELS = {"gemeldet": "gemeldet – noch nicht entschuldigt",
                 "teilweise": "teilweise entschuldigt (Entschuldigung fehlt)",
                 "entschuldigt": "entschuldigt", "unentschuldigt": "unentschuldigt"}
KINDS = ("krank", "verspaetung", "frueh", "fehlt", "beurlaubung")
KIND_LABELS = {"krank": "krank", "verspaetung": "zu spät", "frueh": "früher gegangen", "fehlt": "gefehlt",
               "beurlaubung": "Beurlaubung"}
# Beurlaubung (vorher beantragt, z. B. Arzt- oder Behördentermin): eigene Bezeichnungen der Status
LEAVE_STATUS_LABELS = {"gemeldet": "beantragt", "teilweise": "beantragt", "entschuldigt": "genehmigt",
                       "unentschuldigt": "abgelehnt"}


def status_label(kind: str, status: str) -> str:
    if kind == "beurlaubung":
        return LEAVE_STATUS_LABELS.get(status, status)
    return STATUS_LABELS.get(status, status)


SOURCES = ("online", "telefon", "schriftlich", "lehrkraft")
SOURCE_LABELS = {"online": "online gemeldet", "telefon": "telefonisch", "schriftlich": "schriftlich",
                 "lehrkraft": "von der Lehrkraft erfasst"}
MAX_BACKDATE_STAFF = 365


class StudentAbsenceIn(BaseModel):
    student_id: Optional[str] = None
    date_from: date
    date_to: Optional[date] = None
    periods: list[int] = Field(default_factory=list)
    reason: str = Field("", max_length=1000)
    note: str = Field("", max_length=1000)
    kind: Literal["krank", "verspaetung", "frueh", "fehlt", "beurlaubung"] = "krank"
    minutes: Optional[int] = Field(None, ge=1, le=600)
    source: Optional[Literal["online", "telefon", "schriftlich", "lehrkraft"]] = None
    status: Optional[Literal["gemeldet", "teilweise", "entschuldigt", "unentschuldigt"]] = None


class StudentAbsencePatch(BaseModel):
    status: Optional[Literal["gemeldet", "teilweise", "entschuldigt", "unentschuldigt"]] = None
    note: Optional[str] = Field(None, max_length=1000)
    kind: Optional[Literal["krank", "verspaetung", "frueh", "fehlt", "beurlaubung"]] = None
    minutes: Optional[int] = Field(None, ge=0, le=600)
    source: Optional[Literal["online", "telefon", "schriftlich", "lehrkraft"]] = None


def _texts(row) -> tuple[str, str]:
    from .features_student_self import dec
    return (dec(row.reason, "student_absences", "reason", row.id), dec(row.note, "student_absences", "note", row.id))


def _fmt(d: str) -> str:
    try:
        return date.fromisoformat(d).strftime("%d.%m.%Y")
    except ValueError:
        return d


def _range_text(d1: str, d2: str, periods) -> str:
    text = _fmt(d1) if d1 == d2 else f"{_fmt(d1)} bis {_fmt(d2)}"
    if periods:
        text += f" ({', '.join(str(p + 1) for p in sorted(periods))}. Stunde)"
    return text


# ----------------------------------------------------------------------------- Ausgabe
def _view(acc: AbsenceAccess, row) -> Optional[str]:
    """``full`` | ``family`` | ``own`` (eigene Meldung einer Fachlehrkraft) | ``None``."""
    lvl = acc.visible_level(row)
    if lvl in (FULL, FAMILY):
        return lvl
    if lvl == TEACHER and acc.own(row):
        return "own"
    return None


def absence_out(row, snap, user, attest: Optional[dict] = None, *, acc: Optional[AbsenceAccess] = None,
                db: Optional[Session] = None) -> dict:
    """Krankmeldung in der Sicht des Kontos (``view``). Ohne Zugriff bleiben Grund, Vermerk, Status, Attest leer."""
    acc = acc or AbsenceAccess(user, snap, db)
    view = _view(acc, row) or "hidden"
    st = index("students", snap).get(row.student_id)
    full = view in (FULL, FAMILY)
    reason = _texts(row)[0] if full or view == "own" else ""
    note = _texts(row)[1] if full else ""
    if attest is None and full:
        from schulmanager.student_self import attest_info
        attest = attest_info(snap[1], row.date_from, row.date_to, cls=st.class_id if st else None).to_dict()
    kind = row.kind or "krank"
    if attest is not None and kind != "krank":
        attest = {**attest, "state": "nicht_noetig", "required": False}
    known = full or view == "own"
    return {"id": row.id, "student_id": row.student_id, "student_name": st.name if st else row.student_id,
            "class_id": st.class_id if st else None, "date_from": row.date_from, "date_to": row.date_to,
            "periods": list(row.periods or []), "view": view,
            "reason": reason, "reason_hidden": not known and bool(row.reason),
            "status": row.status if full else None, "note": note,
            "reported_by": row.reported_by if known else None,
            "reported_by_name": row.reported_by_name if known else None,
            "created_at": iso(row.created_at) if known else None, "updated_at": iso(row.updated_at) if known else None,
            "attest": attest if full else None,
            "status_label": status_label(kind, row.status) if full else None,
            "kind": kind, "kind_label": KIND_LABELS.get(kind, kind),
            "minutes": row.minutes if known else None,
            "source": (row.source or "online") if full else None,
            "source_label": SOURCE_LABELS.get(row.source or "online", row.source) if full else None,
            "excused_by_name": (row.excused_by_name or None) if full else None,
            "excused_at": iso(row.excused_at) if full else None,
            "can_manage": acc.can_manage(row), "can_delete": acc.can_delete(row),
            "actions": _row_actions(acc, row, _today()) if view == FAMILY else []}


def _presence_out(row, snap, day: date, periods: list[int]) -> dict:
    """„Fehlt heute in meiner Stunde“: nur Name, Klasse und die eigenen Stunden des Tages."""
    st = index("students", snap).get(row.student_id)
    return {"id": row.id, "student_id": row.student_id, "student_name": st.name if st else row.student_id,
            "class_id": st.class_id if st else None, "date_from": day.isoformat(), "date_to": day.isoformat(),
            "periods": periods, "view": "presence", "reason": "", "reason_hidden": False, "status": None,
            "note": "", "reported_by": None, "reported_by_name": None, "created_at": None, "updated_at": None,
            "attest": None, "can_manage": False, "can_delete": False}


def _presence_periods(acc: AbsenceAccess, row, day: date) -> list[int]:
    mine = acc.lesson_periods(day).get(row.student_id)
    if not mine or not (row.date_from <= day.isoformat() <= row.date_to):
        return []
    return sorted(mine & set(row.periods)) if row.periods else sorted(mine)


def export_rows(db: Session, user) -> list[dict]:
    """DSGVO-Export: eigene Meldungen und die der eigenen Person/Kinder – im selben Umfang wie die Liste
    (Eltern volljähriger Kinder nur mit Freigabe, Fachlehrkräfte ohne Status/Vermerk)."""
    from schulmanager.server.db_models import StudentAbsence

    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    conds = [StudentAbsence.reported_by == acc.uid] if acc.uid else []
    if acc.role in FAMILY_ROLES and acc.family_ids:
        conds.append(StudentAbsence.student_id.in_(sorted(acc.family_ids)))
    if not conds:
        return []
    out = []
    for row in db.scalars(select(StudentAbsence).where(or_(*conds)).order_by(StudentAbsence.id)):
        view = _view(acc, row)
        if view is None:
            continue
        data = absence_out(row, snap, user, acc=acc)
        out.append({k: data[k] for k in ("id", "student_id", "date_from", "date_to", "periods", "reason", "status",
                                         "note", "reported_by_name", "created_at", "updated_at")})
    return out


def _get(db: Session, absence_id: int):
    from schulmanager.server.db_models import StudentAbsence
    row = db.get(StudentAbsence, absence_id)
    if row is None:
        raise HTTPException(404, NOT_FOUND)
    return row


# ----------------------------------------------------------------------------- Liste
@router.get("/student-absences/access")
def student_absence_access(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Was das Konto bei Krankmeldungen darf (für die Oberfläche): ``all`` (Sekretariat/Schulleitung),
    ``class_ids`` (Klassenleitung), ``subject_view`` (Schulschalter für Fachlehrkräfte), ``family``,
    ``student_ids`` (Familie: Personen, deren Krankmeldungen das Konto sieht – volljährige Kinder nur mit Freigabe),
    Grenzen."""
    from schulmanager.server.absence_access import subject_view
    if not (has(user, "student_absence.read") or has(user, "student_absence.report")):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    tid = acc.teacher_id
    family = acc.role in FAMILY_ROLES
    return {"all": acc.staff_all, "family": family, "can_report": acc.can_report,
            "class_ids": sorted(c.id for c in snap[1].classes if tid and c.class_teacher == tid),
            "subject_view": subject_view(snap[1]),
            "student_ids": sorted(acc.family_ids) if family else [],
            "max_days": MAX_DAYS, "max_backdate_days": MAX_BACKDATE_DAYS}


@router.get("/student-absences/preview")
def report_preview(student_id: Optional[str] = Query(None, max_length=40),
                   date_from: date = Query(..., alias="from"), date_to: Optional[date] = Query(None, alias="to"),
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Vorschau beim Krankmelden: wie viele Schultage der Zeitraum hat und ob dafür ein ärztliches Attest nötig ist
    (Schul-Einstellung „Attest ab … Schultagen“ oder eine Klausur im Zeitraum) bzw. eine unterschriebene
    Entschuldigung genügt. Nur für Konten, die für die Person melden dürfen."""
    from schulmanager.student_self import attest_info

    from .features_substitutions import _exam_rows, _student_exam_filter

    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    if not acc.can_report:
        raise HTTPException(403, "Keine Berechtigung")
    sid = student_id or (own_student_ids(user) or [None])[0]
    st = index("students", snap).get(sid) if sid else None
    if st is None or acc.level(sid) != FAMILY:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    d1, d2 = date_from, date_to or date_from
    if d2 < d1 or (d2 - d1).days >= MAX_DAYS:
        raise HTTPException(422, "Ungültiger Zeitraum")
    school = snap[1]
    info = attest_info(school, d1, d2, cls=st.class_id)
    exams = [{"date": e["date"], "title": e.get("title") or e.get("label") or "Klausur", "kind": e.get("kind")}
             for e in _exam_rows(school, [x for x in school.exams if d1.isoformat() <= x.date <= d2.isoformat()],
                                 _student_exam_filter(snap, sid))
             if (e.get("kind") or "klausur") == "klausur"]
    limit = int(getattr(school.settings, "sick_note_after_days", 0) or 0)
    return {"school_days": info.school_days, "attest_after_days": limit, "attest_by_days": info.required,
            "attest_due": info.due, "exams": exams, "attest_needed": info.required or bool(exams)}


@router.get("/student-absences")
def list_student_absences(date_from: Optional[str] = Query(None, alias="from"),
                          date_to: Optional[str] = Query(None, alias="to"),
                          class_id: Optional[str] = None, student_id: Optional[str] = None,
                          status: Optional[Literal["gemeldet", "teilweise", "entschuldigt", "unentschuldigt"]] = None,
                          kind: Optional[Literal["krank", "verspaetung", "frueh", "fehlt", "beurlaubung"]] = None,
                          attest_missing: bool = False,
                          user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Krankmeldungen im Zeitraum (Standard: letzte 30 Tage bis in die Zukunft) im Umfang des Kontos
    (``attest_missing=1``: nur solche, bei denen das Attest fehlt). Filter nach Status/Attest liefern nur
    Meldungen, deren Status/Attest das Konto sehen darf."""
    from schulmanager.server.db_models import StudentAbsence
    if not has(user, "student_absence.read"):
        raise HTTPException(403, "Keine Berechtigung")
    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    today = _today()
    d1 = parse_date(date_from, today - timedelta(days=30), name="from")
    d2 = parse_date(date_to, name="to") if date_to else None
    q = select(StudentAbsence).where(StudentAbsence.date_to >= d1.isoformat())
    if d2 is not None:
        q = q.where(StudentAbsence.date_from <= d2.isoformat())
    if student_id:
        q = q.where(StudentAbsence.student_id == student_id)
    if status:
        q = q.where(StudentAbsence.status == status)
    if kind:
        q = q.where(StudentAbsence.kind == kind)
    presence: dict[str, frozenset[int]] = {}
    leave_rows: list = []
    if not acc.staff_all:
        conds = []
        if acc.role in FAMILY_ROLES:
            if acc.family_ids:
                conds.append(StudentAbsence.student_id.in_(sorted(acc.family_ids)))
        else:
            if acc.class_students:
                conds.append(StudentAbsence.student_id.in_(sorted(acc.class_students)))
            if acc.uid:
                conds.append(StudentAbsence.reported_by == acc.uid)
            if acc.presence_enabled and not status and not attest_missing and d1 <= today \
                    and (d2 is None or today <= d2):
                presence = acc.lesson_periods(today)
                if presence:
                    conds.append(and_(StudentAbsence.student_id.in_(sorted(presence)),
                                      StudentAbsence.date_from <= today.isoformat(),
                                      StudentAbsence.date_to >= today.isoformat()))
            # genehmigte Beurlaubungen der Schüler/innen aus den eigenen Kursen (ohne Anlass, ohne Status)
            if acc.can_read and acc.teacher_id and acc.taught and not status and not attest_missing                     and kind in (None, "beurlaubung"):
                leave_q = select(StudentAbsence).where(
                    StudentAbsence.kind == "beurlaubung", StudentAbsence.status == "entschuldigt",
                    StudentAbsence.date_to >= today.isoformat(), StudentAbsence.student_id.in_(sorted(acc.taught)))
                leave_rows = db.scalars(leave_q.order_by(StudentAbsence.date_from).limit(200)).all()
        if not conds and not leave_rows:
            return []
        q = q.where(or_(*conds)) if conds else q.where(StudentAbsence.id == -1)
    from .features_student_self import adult_student_ids, attest_map
    students = index("students", snap)
    rows = db.scalars(q.order_by(StudentAbsence.date_from.desc(), StudentAbsence.id.desc()).limit(5000)).all()
    if class_id:
        rows = [r for r in rows if (st := students.get(r.student_id)) is not None and st.class_id == class_id]
    views = {r.id: _view(acc, r) for r in rows}
    if status or attest_missing:  # Status/Attest nur filtern, wo das Konto sie sehen darf
        rows = [r for r in rows if views[r.id] in (FULL, FAMILY)]
    attest = attest_map(db, snap[1], [r for r in rows if views[r.id] in (FULL, FAMILY)])
    if attest_missing:
        rows = [r for r in rows if attest[r.id]["missing"]]
    # Volljährig markierte Schüler/innen (Personal mit vollem Zugriff: Kontakt an sie statt an die Eltern)
    adults = adult_student_ids(db, {r.student_id for r in rows if views[r.id] == FULL})
    out = []
    for r in rows:
        view = views[r.id]
        if view is None:
            periods = _presence_periods(acc, r, today) if presence else []
            if periods:
                out.append(_presence_out(r, snap, today, periods))
            continue
        item = absence_out(r, snap, user, attest.get(r.id), acc=acc)
        if view == FULL:
            item["student_adult"] = r.student_id in adults
        out.append(item)
    seen = {item["id"] for item in out}
    for r in leave_rows:
        if r.id not in seen:
            out.extend(_leave_info_out(acc, r, snap, today))
    return out


LEAVE_INFO_DAYS = 14


def _leave_info_out(acc: AbsenceAccess, row, snap, today: date) -> list[dict]:
    """Genehmigte Beurlaubung für Lehrkräfte der betroffenen Stunden: je Tag (die nächsten zwei Wochen) Name, Klasse
    und die eigenen Stunden mit der Person – ohne Anlass, Status und meldende Person (Datenschutz)."""
    out = []
    day = max(date.fromisoformat(row.date_from), today)
    last = min(date.fromisoformat(row.date_to), today + timedelta(days=LEAVE_INFO_DAYS))
    while day <= last:
        mine = acc.lesson_periods(day).get(row.student_id)
        if mine:
            periods = sorted(mine & set(row.periods)) if row.periods else sorted(mine)
            if periods:
                item = _presence_out(row, snap, day, periods)
                item.update(view="leave", kind="beurlaubung", kind_label=KIND_LABELS["beurlaubung"])
                out.append(item)
        day += timedelta(days=1)
    return out


# ----------------------------------------------------------------------------- Melden
def _overlaps(a_periods, b_periods) -> bool:
    return not a_periods or not b_periods or bool(set(a_periods) & set(b_periods))


def _merge_plan(a: tuple[str, str, list[int]], b: tuple[str, str, list[int]]) -> Optional[tuple[str, str, list[int]]]:
    """Zusammenführen zweier überlappender Meldungen: ganztägig + ganztägig = Vereinigung; ganztägig umfasst eine
    stundenweise Meldung; gleicher Zeitraum stundenweise = Stunden vereinigt. Sonst ``None``."""
    (a1, a2, ap), (b1, b2, bp) = a, b
    if not ap and not bp:
        return min(a1, b1), max(a2, b2), []
    if not ap and a1 <= b1 and b2 <= a2:
        return a1, a2, []
    if not bp and b1 <= a1 and a2 <= b2:
        return b1, b2, []
    if ap and bp and a1 == b1 and a2 == b2:
        return a1, a2, sorted(set(ap) | set(bp))
    return None


def _resolve_student(acc: AbsenceAccess, body: StudentAbsenceIn, user, snap) -> tuple[str, str]:
    """Schüler-ID und Stufe der Meldung; fremde Personen → 404."""
    sid = body.student_id
    if not sid:
        own = own_student_ids(user)
        if len(own) != 1:
            raise HTTPException(422, "Bitte die Schülerin/den Schüler angeben")
        sid = own[0]
    if index("students", snap).get(sid) is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    if acc.linked_but_hidden(sid):
        raise HTTPException(403, "Ihr Kind ist volljährig und meldet sich selbst krank.")
    lvl = acc.level(sid)
    if lvl is None and acc.teacher_id and acc.lesson_periods(body.date_from).get(sid):
        lvl = TEACHER  # Vertretungsstunde: die Person sitzt heute in der eigenen Stunde
    if lvl is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    return sid, lvl


def _teacher_periods(acc: AbsenceAccess, sid: str, name: str, d1: date, d2: date, periods: list[int]) -> list[int]:
    """Fachlehrkraft: ein Tag, nicht in der Zukunft, nur eigene Stunden mit der Person (leer = alle eigenen)."""
    if d2 != d1:
        raise HTTPException(422, "Fachlehrkräfte melden eine Abwesenheit nur für einen Tag (die eigene Stunde).")
    if d1 > _today():
        raise HTTPException(422, "Eine Abwesenheit in der eigenen Stunde lässt sich erst am Tag selbst melden.")
    mine = acc.lesson_periods(d1).get(sid) or frozenset()
    if not mine:
        raise HTTPException(403, f"Sie unterrichten {name} an diesem Tag nicht.")
    if not periods:
        return sorted(mine)
    extra = sorted(set(periods) - mine)
    if extra:
        raise HTTPException(403, f"Sie können nur Ihre eigenen Stunden melden ({', '.join(str(p + 1) for p in sorted(mine))}.).")
    return periods


def _lesson_report(db: Session, row, snap) -> bool:
    """Stunden-Meldung einer Fachlehrkraft: gemeldet von einem Lehrerkonto, das nicht die Klasse leitet."""
    from schulmanager.server.db_models import User

    reporter = db.get(User, row.reported_by) if row.reported_by else None
    if reporter is None or reporter.role != "lehrer" or not reporter.teacher_id:
        return False
    st = index("students", snap).get(row.student_id)
    cls = index("classes", snap).get(st.class_id) if st else None
    return not (cls is not None and cls.class_teacher == reporter.teacher_id)


@router.post("/student-absences", status_code=201)
def report_student_absence(body: StudentAbsenceIn, response: Response, user: AuthUser = Depends(current_user),
                           db: Session = Depends(get_db)):
    """Krankmeldung abgeben (Eltern für ihr Kind, volljährige Schüler/innen für sich, Klassenleitung/Sekretariat,
    Fachlehrkräfte für die eigene Stunde). Überschneidet sie eine eigene, noch „gemeldete“ Meldung – oder enthält sie
    die noch „gemeldete“ Stunden-Meldung einer Fachlehrkraft ganz (nur Familie und Stufe ``full``) –, wird diese
    erweitert bzw. übernommen (Antwort 200, ``merged: true``)."""
    from schulmanager.calendar_utils import school_days
    from schulmanager.server.db_models import StudentAbsence

    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    if not acc.can_report:  # Recht ``student_absence.report`` oder volljährig nach Geburtsdatum
        raise HTTPException(403, "Keine Berechtigung")
    sid, lvl = _resolve_student(acc, body, user, snap)
    st = index("students", snap)[sid]
    d1 = body.date_from
    d2 = body.date_to or body.date_from
    if d2 < d1:
        raise HTTPException(422, "Das Enddatum liegt vor dem Startdatum")
    if (d2 - d1).days >= MAX_DAYS:
        raise HTTPException(422, f"Zeitraum zu lang (maximal {MAX_DAYS} Tage)")
    pupil = acc.role in FAMILY_ROLES
    back = MAX_BACKDATE_STAFF if (lvl == FULL and not pupil) else MAX_BACKDATE_DAYS
    if d1 < _today() - timedelta(days=back):
        raise HTTPException(422, f"Rückwirkende Meldungen nur bis {back} Tage")
    if pupil and body.kind == "fehlt":
        raise HTTPException(422, "„Gefehlt“ erfasst die Schule")
    if body.kind == "beurlaubung":
        if not body.reason.strip():
            raise HTTPException(422, "Bitte den Anlass der Beurlaubung angeben (z. B. Arzttermin, Behördentermin)")
        if pupil and d1 < _today():
            raise HTTPException(422, "Eine Beurlaubung wird vorher beantragt – für vergangene Tage bitte krank melden")
    if body.kind in ("verspaetung", "frueh") and d2 != d1:
        raise HTTPException(422, "Zu spät bzw. früher gegangen gilt für einen Tag")
    # Status und Herkunft setzt nur Personal mit vollem Zugriff (Klassenleitung, Sekretariat, Schulleitung)
    status = body.status if (body.status and lvl == FULL and not pupil) else "gemeldet"
    source = "online" if pupil else (body.source or ("telefon" if acc.role == "sekretariat" else "lehrkraft"))
    periods = sorted(set(body.periods))
    if any(not 0 <= p < snap[1].settings.periods for p in periods):
        raise HTTPException(422, "Ungültige Stunde")
    if not school_days(snap[1], d1, d2, st.class_id):     # Unterrichtstage der Klasse (R3)
        raise HTTPException(422, "Kein Schultag (kein Unterrichtstag oder Ferien).")
    if lvl == TEACHER:
        periods = _teacher_periods(acc, sid, st.name, d1, d2, periods)
    staff_note = lvl == FULL and acc.role not in FAMILY_ROLES
    from .features_student_self import enc

    # Überschneidungen mit vorhandenen Meldungen derselben Person
    existing = [r for r in db.scalars(select(StudentAbsence).where(StudentAbsence.student_id == sid,
                                                                    StudentAbsence.date_from <= d2.isoformat(),
                                                                    StudentAbsence.date_to >= d1.isoformat()))
                if _overlaps(r.periods or [], periods) and (r.kind or "krank") == body.kind]
    if existing:
        row = existing[0]
        plan = _merge_plan((row.date_from, row.date_to, list(row.periods or [])),
                           (d1.isoformat(), d2.isoformat(), periods)) if len(existing) == 1 else None
        if plan and (date.fromisoformat(plan[1]) - date.fromisoformat(plan[0])).days >= MAX_DAYS:
            plan = None
        # Eine umfassendere Meldung der Familie bzw. von Klassenleitung/Sekretariat/Schulleitung übernimmt die noch
        # „gemeldete“ Stunden-Meldung einer Fachlehrkraft, die sie ganz enthält (sonst blockierte die Stunden-Meldung
        # die Krankmeldung der Eltern). Danach gehört sie niemandem allein: die Fachlehrkraft sieht Grund und Status
        # nicht mehr, löschen nur noch Klassenleitung, Sekretariat und Schulleitung (sonst ließe sie sich so entfernen).
        takeover = (plan is not None and not acc.own(row) and lvl in (FULL, FAMILY)
                    and (plan[0], plan[1], list(plan[2])) == (d1.isoformat(), d2.isoformat(), periods)
                    and _lesson_report(db, row, snap))
        if not (plan and (acc.own(row) or takeover) and row.status == "gemeldet"):
            seen = _view(acc, row) in (FULL, FAMILY, "own")
            where = f" ({_range_text(row.date_from, row.date_to, row.periods)})" if seen else ""
            if acc.can_delete(row):
                hint = " Bitte löschen Sie zuerst die vorhandene Meldung."
            elif seen:
                hint = " Änderungen nimmt die Klassenleitung oder das Sekretariat vor."
            else:
                hint = ""
            raise HTTPException(409, f"Für {st.name} liegt für diesen Zeitraum bereits eine Krankmeldung vor{where}."
                                     f"{hint}")
        old_reason, old_note = _texts(row)
        prev_periods = list(row.periods or [])
        new_reason = body.reason.strip()
        changes: dict = {"merged": True}
        if takeover:
            changes["taken_over_from"] = row.reported_by
            names = [n for n in (row.reported_by_name, user.display_name or user.username) if n]
            row.reported_by, row.reported_by_name = None, ", ".join(dict.fromkeys(names))[:200]
        if (row.date_from, row.date_to, list(row.periods or [])) != plan:
            changes.update({"date_from": [row.date_from, plan[0]], "date_to": [row.date_to, plan[1]]})
            row.date_from, row.date_to, row.periods = plan[0], plan[1], plan[2]
        if new_reason and new_reason != old_reason:
            row.reason = enc((f"{old_reason}; {new_reason}" if old_reason else new_reason)[:1000],
                             "student_absences", "reason", row.id)
            changes["reason"] = True
        if staff_note and body.note.strip() and body.note.strip() != old_note:
            row.note = enc(body.note.strip(), "student_absences", "note", row.id)
            changes["note"] = True
        row.updated_at = utcnow()
        write_audit(db, user, "student_absence.update", f"student_absence:{row.id}", {"student_id": sid, **changes})
        log_changes = {k: v for k, v in changes.items() if k in ("date_from", "date_to", "reason", "note")}
        if plan[2] != list(prev_periods):
            log_changes["periods"] = [prev_periods, plan[2]]
        alog.record(db, row.id, sid, "zusammengefuehrt", user, class_lead=lvl == FULL,
                    channel=alog.channel_for(user, source), changes=log_changes,
                    detail={"kind": row.kind or "krank", **({"taken_over": True} if takeover else {})})
        db.commit()
        publish_change(["student_absences"], iso_dates(date.fromisoformat(row.date_from),
                                                       date.fromisoformat(row.date_to), 62))
        _notify_class_teacher(db, sid, snap)
        response.status_code = 200
        return {**absence_out(row, snap, user, acc=acc, db=db), "merged": True}

    row = StudentAbsence(student_id=sid, date_from=d1.isoformat(), date_to=d2.isoformat(),
                         periods=periods, reason="", status=status, note="",
                         reported_by=user.id or None, reported_by_name=user.display_name or user.username,
                         created_at=utcnow(), kind=body.kind, minutes=body.minutes, source=source,
                         excused_by_name="")
    if status in ("entschuldigt", "unentschuldigt"):
        row.excused_by, row.excused_by_name, row.excused_at = (user.id or None, user.display_name or user.username,
                                                               utcnow())
    db.add(row)
    db.flush()
    row.reason = enc(body.reason.strip(), "student_absences", "reason", row.id)
    if staff_note:
        row.note = enc(body.note.strip(), "student_absences", "note", row.id)
    write_audit(db, user, "student_absence.create", f"student_absence:{row.id}",
                {"student_id": sid, "date_from": row.date_from, "date_to": row.date_to, "kind": row.kind,
                 "status": row.status, "source": row.source})
    alog.record(db, row.id, sid, "angelegt", user, class_lead=lvl == FULL and acc.role == "lehrer",
                channel=alog.channel_for(user, source),
                detail={"kind": row.kind, "date_from": row.date_from, "date_to": row.date_to,
                        "periods": list(periods), "status": row.status,
                        **({"minutes": row.minutes} if row.minutes else {})})
    db.commit()
    publish_change(["student_absences"], iso_dates(d1, d2, 62))
    _notify_class_teacher(db, sid, snap)
    from schulmanager.server import notification_hooks  # Glocke: Krankmeldung eingegangen
    notification_hooks.absence_received(row.id, user.id or None)
    return absence_out(row, snap, user, acc=acc, db=db)


# ----------------------------------------------------------------------------- Bearbeiten
def _visible_row(acc: AbsenceAccess, db: Session, absence_id: int):
    """Vorhandene Meldung, die das Konto in irgendeiner Form sieht oder deren Person es betreut – sonst 404."""
    row = _get(db, absence_id)
    if acc.visible_level(row) is None:
        raise HTTPException(404, NOT_FOUND)
    return row


@router.patch("/student-absences/{absence_id}")
def patch_student_absence(absence_id: int, body: StudentAbsencePatch, user: AuthUser = Depends(current_user),
                          db: Session = Depends(get_db)):
    """Status (``gemeldet|teilweise|entschuldigt|unentschuldigt``), Art, Minuten, Herkunft bzw. Vermerk setzen – nur
    Klassenleitung, Sekretariat, Schulleitung (Fachlehrkraft 403, ohne Bezug zur Person 404)."""
    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    row = _visible_row(acc, db, absence_id)
    if not acc.can_manage(row):
        raise HTTPException(403, "Status und Vermerk setzen nur Klassenleitung, Sekretariat und Schulleitung.")
    changes = {}
    if body.status is not None and body.status != row.status:
        changes["status"] = [row.status, body.status]
        row.status = body.status
        if body.status in ("entschuldigt", "unentschuldigt"):
            row.excused_by, row.excused_by_name, row.excused_at = (user.id or None,
                                                                   user.display_name or user.username, utcnow())
        else:
            row.excused_by, row.excused_by_name, row.excused_at = None, "", None
    for key in ("kind", "minutes", "source"):
        value = getattr(body, key)
        if value is not None and value != getattr(row, key):
            changes[key] = [getattr(row, key), value]
            setattr(row, key, value or None if key == "minutes" else value)
    if body.note is not None and body.note.strip() != _texts(row)[1]:
        from .features_student_self import enc
        changes["note"] = True
        row.note = enc(body.note.strip(), "student_absences", "note", row.id)
    if changes:
        row.updated_at = utcnow()
        write_audit(db, user, "student_absence.update", f"student_absence:{row.id}",
                    {"student_id": row.student_id, **changes})
        alog.record(db, row.id, row.student_id, "aenderung", user, class_lead=acc.role == "lehrer", changes=changes,
                    detail={"kind": row.kind or "krank"})
        db.commit()
        publish_change(["student_absences"])
        if "status" in changes:  # Glocke: bestätigt / nicht entschuldigt
            from schulmanager.server import notification_hooks
            notification_hooks.absence_status(row.id, user.id or None)
    from .features_student_self import attest_map
    return absence_out(row, snap, user, attest_map(db, snap[1], [row])[row.id], acc=acc)


@router.delete("/student-absences/{absence_id}")
def delete_student_absence(absence_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Löschen: Klassenleitung, Sekretariat, Schulleitung oder die meldende Person, solange der Status „gemeldet“
    ist."""
    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    row = _visible_row(acc, db, absence_id)
    if not acc.can_delete(row):
        raise HTTPException(403, "Löschen dürfen nur Klassenleitung, Sekretariat und Schulleitung – die meldende "
                                 "Person, solange die Meldung noch nicht bearbeitet ist.")
    write_audit(db, user, "student_absence.delete", f"student_absence:{row.id}", {"student_id": row.student_id})
    alog.record(db, row.id, row.student_id, "zurueckgenommen", user,
                class_lead=acc.role == "lehrer" and acc.level(row.student_id) == FULL,
                detail={"kind": row.kind or "krank", "date_from": row.date_from, "date_to": row.date_to,
                        "periods": list(row.periods or []), "status": row.status})
    db.delete(row)
    db.commit()
    publish_change(["student_absences"])
    return {"deleted": absence_id}


# ----------------------------------------------------------------------------- Rückgängig, verkürzen, verlängern
class ShortenIn(BaseModel):
    """Früher zurück: ``back_date`` = erster Tag, an dem die Person wieder da ist; mit ``back_lesson`` (1-basiert,
    mindestens 2) erst ab dieser Stunde dieses Tages."""
    back_date: date
    back_lesson: Optional[int] = Field(None, ge=2, le=30)


class ExtendIn(BaseModel):
    date_to: date
    reason: str = Field("", max_length=1000)


_EXTEND_BACK_DAYS = 7


def _row_actions(acc: AbsenceAccess, row, today: date) -> list[str]:
    """Aktionen, die die Familie an einer Meldung hat (Oberfläche): ``withdraw`` (Rückgängig/Zurücknehmen),
    ``request_withdrawal`` (schon bearbeitet → Klassenleitung bitten), ``shorten`` (früher zurück), ``extend``
    (verlängern), ``return_leave`` (genehmigte Beurlaubung zurückgeben)."""
    if acc.role not in FAMILY_ROLES or not acc.can_report or acc.level(row.student_id) != FAMILY:
        return []
    kind, t = row.kind or "krank", today.isoformat()
    back = (today - timedelta(days=_EXTEND_BACK_DAYS)).isoformat()
    out = []
    if kind == "krank":
        if acc.can_delete(row):
            out.append("withdraw")
        elif row.date_to >= (today - timedelta(days=MAX_BACKDATE_DAYS)).isoformat():
            out.append("request_withdrawal")
        if row.status == "gemeldet" and row.date_to >= t and (row.date_to > row.date_from
                                                              or (row.date_from <= t and not row.periods)):
            out.append("shorten")
        if not row.periods and row.date_to >= back:
            out.append("extend")
    elif kind == "beurlaubung":
        if acc.can_delete(row):
            out.append("withdraw")
        if row.date_to >= t and row.status == "entschuldigt":
            out.append("return_leave")
        if row.date_to >= t and row.status in ("gemeldet", "entschuldigt"):
            out.append("extend")
    return out


def _action_row(db: Session, absence_id: int, user, snap, *, kinds: tuple[str, ...]):
    """Meldung für eine Aktion der Familie bzw. des Personals mit vollem Zugriff (sonst 404/403)."""
    acc = AbsenceAccess(user, snap, db)
    row = _visible_row(acc, db, absence_id)
    lvl = acc.level(row.student_id)
    family = acc.role in FAMILY_ROLES
    if not ((family and lvl == FAMILY and acc.can_report) or (not family and lvl == FULL)):
        raise HTTPException(403, "Keine Berechtigung")
    if (row.kind or "krank") not in kinds:
        raise HTTPException(422, "Das geht bei dieser Art von Meldung nicht.")
    return acc, row, lvl


def _require_pending(row, lvl: str) -> None:
    if lvl == FAMILY and row.status != "gemeldet":
        raise HTTPException(409, "Die Meldung ist schon bearbeitet. Bitte die Rücknahme anfragen – die "
                                 "Klassenleitung meldet sich.")


def _finish(db: Session, sid: str, d_from: date, d_to: date, snap) -> None:
    db.commit()
    publish_change(["student_absences"], iso_dates(d_from, d_to, 62))
    _notify_class_teacher(db, sid, snap)


def _new_row(db: Session, user, src, d1: date, d2: date, periods: list[int], reason: str, kind: str):
    """Folgemeldung zu ``src`` (gleiche Person, Art und Herkunft; Status „gemeldet“)."""
    from schulmanager.server.db_models import StudentAbsence

    from .features_student_self import enc

    row = StudentAbsence(student_id=src.student_id, date_from=d1.isoformat(), date_to=d2.isoformat(), periods=periods,
                         reason="", status="gemeldet", note="", reported_by=user.id or None,
                         reported_by_name=user.display_name or user.username, created_at=utcnow(), kind=kind,
                         source=src.source or "online", excused_by_name="")
    db.add(row)
    db.flush()
    row.reason = enc(reason[:1000], "student_absences", "reason", row.id)
    return row


@router.post("/student-absences/{absence_id}/shorten")
def shorten_absence(absence_id: int, body: ShortenIn, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)):
    """„Ich komme früher zurück“: eine Krankmeldung verkürzen – ab ``back_date`` wieder da (die Meldung endet am Tag
    davor) bzw. am Tag selbst ab einer Stunde (``back_lesson``; die Meldung gilt dann nur für die Stunden davor).
    Nur ab heute; Familie nur, solange die Meldung noch „gemeldet“ ist. Attestpflicht und Nachschreibtermine rechnen
    sich aus dem neuen Zeitraum."""
    from schulmanager.calendar_utils import school_days

    snap = snapshot()
    acc, row, lvl = _action_row(db, absence_id, user, snap, kinds=("krank",))
    _require_pending(row, lvl)
    st = index("students", snap)[row.student_id]
    today, back = _today(), body.back_date
    d1, d2 = date.fromisoformat(row.date_from), date.fromisoformat(row.date_to)
    if back < today:
        raise HTTPException(422, "Früher zurück geht nur ab heute.")
    old = (row.date_from, row.date_to, list(row.periods or []))
    spawn = None
    if body.back_lesson is None:
        if back <= d1:
            raise HTTPException(422, "Dann war die Meldung nicht nötig – bitte „Rückgängig“ bzw. „Zurücknehmen“ nutzen.")
        if back > d2:
            raise HTTPException(422, "Die Meldung endet schon vor diesem Tag.")
        row.date_to = (back - timedelta(days=1)).isoformat()
    else:
        if row.periods:
            raise HTTPException(422, "Bei einzelnen Stunden bitte die Meldung zurücknehmen und neu melden.")
        if not d1 <= back <= d2:
            raise HTTPException(422, "Dieser Tag liegt nicht in der Meldung.")
        if body.back_lesson > snap[1].settings.periods:
            raise HTTPException(422, "Ungültige Stunde")
        if not school_days(snap[1], back, back, st.class_id):
            raise HTTPException(422, "Kein Schultag (kein Unterrichtstag oder Ferien).")
        absent = list(range(body.back_lesson - 1))
        if back == d1:
            row.date_to, row.periods = row.date_from, absent
        else:
            row.date_to = (back - timedelta(days=1)).isoformat()
            spawn = _new_row(db, user, row, back, back, absent, _texts(row)[0], "krank")
    row.updated_at = utcnow()
    changes: dict = {}
    if row.date_to != old[1]:
        changes["date_to"] = [old[1], row.date_to]
    if list(row.periods or []) != old[2]:
        changes["periods"] = [old[2], list(row.periods or [])]
    cl = lvl == FULL and acc.role == "lehrer"
    detail = {"kind": "krank", "back_date": back.isoformat(),
              **({"back_lesson": body.back_lesson} if body.back_lesson else {}),
              **({"new_absence_id": spawn.id} if spawn is not None else {})}
    write_audit(db, user, "student_absence.update", f"student_absence:{row.id}",
                {"student_id": row.student_id, "shortened": True, **changes})
    alog.record(db, row.id, row.student_id, "verkuerzt", user, class_lead=cl, channel=alog.channel_for(user, None),
                changes=changes, detail=detail)
    if spawn is not None:
        alog.record(db, spawn.id, row.student_id, "angelegt", user, class_lead=cl, channel=alog.channel_for(user, None),
                    detail={"kind": "krank", "date_from": spawn.date_from, "date_to": spawn.date_to,
                            "periods": list(spawn.periods or []), "status": "gemeldet", "split_from": row.id})
    _finish(db, row.student_id, d1, d2, snap)
    from .features_student_self import attest_map
    return {**absence_out(row, snap, user, attest_map(db, snap[1], [row])[row.id], acc=acc, db=db),
            "new_absence_id": spawn.id if spawn is not None else None}


@router.post("/student-absences/{absence_id}/extend")
def extend_absence(absence_id: int, body: ExtendIn, user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Verlängern: eine Krankmeldung oder einen Beurlaubungsantrag bis ``date_to`` ausdehnen. Solange die Meldung
    noch „gemeldet“ (bzw. „beantragt“) ist, wird sie selbst verlängert; sonst entsteht eine Folgemeldung für die
    zusätzlichen Tage (bei einer genehmigten Beurlaubung ein neuer Antrag – die Klassenleitung entscheidet). Die
    Attestpflicht rechnet sich aus dem neuen Zeitraum (Antwort ``attest``)."""
    from schulmanager.calendar_utils import school_days

    snap = snapshot()
    acc, row, lvl = _action_row(db, absence_id, user, snap, kinds=("krank", "beurlaubung"))
    kind = row.kind or "krank"
    st = index("students", snap)[row.student_id]
    today = _today()
    d1, d2 = date.fromisoformat(row.date_from), date.fromisoformat(row.date_to)
    if body.date_to <= d2:
        raise HTTPException(422, "Das neue Ende muss nach dem bisherigen liegen.")
    if row.periods and kind == "krank":
        raise HTTPException(422, "Bei einzelnen Stunden bitte neu melden.")
    if (body.date_to - d1).days >= MAX_DAYS:
        raise HTTPException(422, f"Zeitraum zu lang (maximal {MAX_DAYS} Tage)")
    if kind == "krank" and d2 < today - timedelta(days=_EXTEND_BACK_DAYS) and lvl == FAMILY:
        raise HTTPException(422, "Das ist schon zu lange her – bitte neu melden.")
    if kind == "beurlaubung" and (d2 < today or row.status not in ("gemeldet", "entschuldigt")):
        raise HTTPException(422, "Eine abgelaufene oder abgelehnte Beurlaubung lässt sich nicht verlängern.")
    nxt = d2 + timedelta(days=1)
    if not school_days(snap[1], nxt, body.date_to, st.class_id):
        raise HTTPException(422, "Kein Schultag (kein Unterrichtstag oder Ferien).")
    cl = lvl == FULL and acc.role == "lehrer"
    new = None
    if row.status == "gemeldet":
        row.date_to = body.date_to.isoformat()
        row.updated_at = utcnow()
        changes = {"date_to": [d2.isoformat(), row.date_to]}
        write_audit(db, user, "student_absence.update", f"student_absence:{row.id}",
                    {"student_id": row.student_id, "extended": True, **changes})
        alog.record(db, row.id, row.student_id, "verlaengert", user, class_lead=cl, channel=alog.channel_for(user, None),
                    changes=changes, detail={"kind": kind})
        target = row
    else:
        reason = body.reason.strip() or _texts(row)[0]
        if kind == "beurlaubung" and not reason:
            raise HTTPException(422, "Bitte den Anlass der Verlängerung angeben")
        new = target = _new_row(db, user, row, nxt, body.date_to, [] if kind == "krank" else list(row.periods or []),
                                reason, kind)
        write_audit(db, user, "student_absence.create", f"student_absence:{new.id}",
                    {"student_id": row.student_id, "date_from": new.date_from, "date_to": new.date_to, "kind": kind,
                     "status": "gemeldet", "extension_of": row.id})
        alog.record(db, new.id, row.student_id, "angelegt", user, class_lead=cl, channel=alog.channel_for(user, None),
                    detail={"kind": kind, "date_from": new.date_from, "date_to": new.date_to,
                            "periods": list(new.periods or []), "status": "gemeldet", "extension_of": row.id})
        alog.record(db, row.id, row.student_id, "verlaengerung_beantragt" if kind == "beurlaubung" else "verlaengert",
                    user, class_lead=cl, channel=alog.channel_for(user, None),
                    detail={"kind": kind, "date_from": new.date_from, "date_to": new.date_to, "new_absence_id": new.id})
    _finish(db, row.student_id, d1, body.date_to, snap)
    from .features_student_self import attest_map
    return {**absence_out(target, snap, user, attest_map(db, snap[1], [target])[target.id], acc=acc, db=db),
            "extended_from": row.id if new is not None else None}


@router.post("/student-absences/{absence_id}/request-withdrawal")
def request_withdrawal(absence_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """„Rücknahme anfragen“: die Familie bittet die Klassenleitung, eine schon bearbeitete Meldung zurückzunehmen.
    Wird protokolliert (ohne Freitext – Gesundheitsdaten) und der Klassenleitung live angezeigt; mehrfaches Anfragen
    zählt einmal."""
    snap = snapshot()
    acc = AbsenceAccess(user, snap, db)
    row = _visible_row(acc, db, absence_id)
    if acc.role not in FAMILY_ROLES or acc.level(row.student_id) != FAMILY or not acc.can_report:
        raise HTTPException(403, "Keine Berechtigung")
    if acc.can_delete(row):
        raise HTTPException(422, "Diese Meldung können Sie selbst zurücknehmen.")
    if any(e.event == "ruecknahme_angefragt" for e in alog.events_for(db, absence_ids=[row.id])):
        return {"requested": True, "already": True}
    write_audit(db, user, "student_absence.withdrawal_request", f"student_absence:{row.id}",
                {"student_id": row.student_id})
    alog.record(db, row.id, row.student_id, "ruecknahme_angefragt", user, channel="online",
                detail={"kind": row.kind or "krank", "date_from": row.date_from, "date_to": row.date_to,
                        "periods": list(row.periods or []), "status": row.status})
    _finish(db, row.student_id, date.fromisoformat(row.date_from), date.fromisoformat(row.date_to), snap)
    return {"requested": True, "already": False}


@router.post("/student-absences/{absence_id}/return-leave")
def return_leave(absence_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Genehmigte Beurlaubung zurückgeben („nicht mehr nötig“): die Beurlaubung entfällt, die Klassenleitung wird
    informiert; das Protokoll behält den Vorgang. Nur solange sie noch nicht vorbei ist."""
    snap = snapshot()
    acc, row, lvl = _action_row(db, absence_id, user, snap, kinds=("beurlaubung",))
    if row.status != "entschuldigt":
        raise HTTPException(422, "Nur eine genehmigte Beurlaubung lässt sich zurückgeben – einen offenen Antrag bitte "
                                 "zurückziehen.")
    if row.date_to < _today().isoformat():
        raise HTTPException(422, "Die Beurlaubung ist schon vorbei.")
    write_audit(db, user, "student_absence.delete", f"student_absence:{row.id}",
                {"student_id": row.student_id, "returned_leave": True})
    alog.record(db, row.id, row.student_id, "beurlaubung_zurueckgegeben", user,
                class_lead=lvl == FULL and acc.role == "lehrer", channel=alog.channel_for(user, None),
                detail={"kind": "beurlaubung", "date_from": row.date_from, "date_to": row.date_to,
                        "periods": list(row.periods or []), "status": row.status})
    d1, d2, sid = date.fromisoformat(row.date_from), date.fromisoformat(row.date_to), row.student_id
    db.delete(row)
    _finish(db, sid, d1, d2, snap)
    return {"returned": absence_id}


def _notify_class_teacher(db: Session, student_id: str, snap) -> None:
    """Live-Hinweis (ohne Inhalt) an das Konto der Klassenleitung – deren Kachel lädt dann neu."""
    try:
        from schulmanager.server.db_models import User
        from schulmanager.server.events import bus

        st = index("students", snap).get(student_id)
        cls = index("classes", snap).get(st.class_id) if st else None
        if not cls or not cls.class_teacher:
            return
        ids = set(db.scalars(select(User.id).where(User.teacher_id == cls.class_teacher, User.active.is_(True))))
        if ids:
            bus.publish("change", {"scope": ["student_absences", "class_absences"]}, user_ids=ids)
    except Exception:  # pragma: no cover - Hinweise dürfen die Meldung nie verhindern
        pass


# =========================================================================== Fehlzeiten-Übersicht eines Kindes
def _record_level(acc: AbsenceAccess, sid: str) -> Optional[str]:
    """Fehlzeiten-Übersicht/Formular: volle Sicht (Klassenleitung, Sekretariat, Schulleitung) oder Familie;
    Fachlehrkräfte und alle anderen nicht (→ 404)."""
    lvl = acc.level(sid)
    return lvl if lvl in (FULL, FAMILY) else None


@router.get("/student-absences/record")
def student_record(student_id: str = Query(..., max_length=40), date_from: Optional[str] = Query(None, alias="from"),
                   date_to: Optional[str] = Query(None, alias="to"), user: AuthUser = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Fehlzeiten eines Kindes: alle Einträge (krank, zu spät, früher gegangen, gefehlt) mit Status und Summen
    (Schultage/Stunden entschuldigt, unentschuldigt, offen; Verspätungen mit Minuten). Standard: aktuelles Schuljahr."""
    from schulmanager.calendar_utils import school_days
    from schulmanager.server.db_models import StudentAbsence
    snap = snapshot()
    school = snap[1]
    st = index("students", snap).get(student_id)
    acc = AbsenceAccess(user, snap, db)
    lvl = _record_level(acc, student_id) if st is not None else None
    if st is None or lvl is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    today = _today()
    start_default = date(today.year if today.month >= 8 else today.year - 1, 8, 1)
    d1 = parse_date(date_from, start_default, name="from")
    d2 = parse_date(date_to, today + timedelta(days=60), name="to")
    rows = list(db.scalars(select(StudentAbsence).where(
        StudentAbsence.student_id == student_id, StudentAbsence.date_to >= d1.isoformat(),
        StudentAbsence.date_from <= d2.isoformat()).order_by(StudentAbsence.date_from.desc(), StudentAbsence.id.desc())))
    from .features_student_self import attest_map
    attest = attest_map(db, school, rows)
    entries = []
    logs = alog.events_by_absence(db, [r.id for r in rows]) if lvl == FULL and acc.role not in FAMILY_ROLES else {}
    summary = {"days": 0, "days_excused": 0, "days_unexcused": 0, "days_open": 0, "lessons": 0,
               "lessons_excused": 0, "lessons_unexcused": 0, "late_count": 0, "late_minutes": 0, "early_count": 0,
               "open_count": 0}
    for r in rows:
        out = absence_out(r, snap, user, attest[r.id], acc=acc)
        days = school_days(school, r.date_from, r.date_to, st.class_id)
        out["school_days"] = len(days)
        kind = r.kind or "krank"
        if r.id in logs:
            first = next((e for e in logs[r.id] if e.event == "angelegt"), None)
            out["history"] = alog.timeline(logs[r.id], FULL, kind)
            out.update(alog.report_info(r, first, FULL))
        bucket = ("excused" if r.status == "entschuldigt" else "unexcused" if r.status == "unentschuldigt"
                  else "open")
        if bucket == "open":
            summary["open_count"] += 1
        if kind == "verspaetung":
            summary["late_count"] += 1
            summary["late_minutes"] += int(r.minutes or 0)
        elif kind == "frueh":
            summary["early_count"] += 1
        elif r.periods:
            n = len(r.periods) * len(days)
            summary["lessons"] += n
            if bucket != "open":
                summary[f"lessons_{bucket}"] += n
        else:
            summary["days"] += len(days)
            summary[f"days_{bucket}"] += len(days)
        entries.append(out)
    withdrawn = []
    if lvl == FULL and acc.role not in FAMILY_ROLES:  # zurückgenommene/gelöschte Meldungen bleiben im Protokoll
        by_absence: dict[int, list] = {}
        for ev in alog.events_for(db, student_ids=[student_id]):
            by_absence.setdefault(ev.absence_id, []).append(ev)
        withdrawn = [{"absence_id": aid, "history": alog.timeline(evs, FULL)}
                     for aid, evs in by_absence.items() if aid not in logs and any(e.event in ("zurueckgenommen", "beurlaubung_zurueckgegeben") for e in evs)]
    docs = []
    if getattr(user, "role", "") in PUPIL_ROLES or has(user, "student_documents.read"):
        from schulmanager.server.feature_models.student_self import StudentDocument

        from .features_student_self import blocked_for_parents, can_view, doc_out
        adults = blocked_for_parents(db, [student_id])
        for doc in db.scalars(select(StudentDocument).where(StudentDocument.student_id == student_id,
                                                            StudentDocument.withdrawn_at.is_(None))
                              .order_by(StudentDocument.created_at.desc()).limit(200)):
            if can_view(user, doc, snap, adults):
                docs.append(doc_out(doc, user, snap, db))
    st_set = school.settings
    return {"student": {"id": st.id, "name": st.name, "class_id": st.class_id},
            "from": d1.isoformat(), "to": d2.isoformat(), "entries": entries, "withdrawn": withdrawn, "documents": docs, "summary": summary,
            "can_manage": lvl == FULL and acc.role not in FAMILY_ROLES, "can_report": acc.can_report,
            "phone": {"number": getattr(st_set, "sick_phone", "") or "",
                      "hours": getattr(st_set, "sick_phone_hours", "") or ""}}


@router.get("/student-absences/form.pdf")
def excuse_form(student_id: Optional[str] = Query(None, max_length=40), absence_id: Optional[int] = Query(None),
                user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Formular „Schriftliche Entschuldigung“ als PDF zum Ausdrucken und Ausfüllen (ganzer Tag, einzelne Stunden,
    zu spät, früher gegangen). Mit ``student_id``/``absence_id`` vorausgefüllt (nur mit Leserecht für das Kind)."""
    from fastapi.responses import Response

    from schulmanager.calendar_utils import period_label
    from schulmanager.server.db_models import StudentAbsence
    from schulmanager.server.pdf_simple import MARGIN, Page, render

    snap = snapshot()
    school = snap[1]
    row = db.get(StudentAbsence, absence_id) if absence_id else None
    if row is not None:
        student_id = row.student_id
    st = index("students", snap).get(student_id) if student_id else None
    if (row is not None or student_id) and (st is None or _record_level(AbsenceAccess(user, snap, db), st.id) is None):
        raise HTTPException(404, "Schüler/in nicht gefunden")

    def de(iso_day: str) -> str:
        try:
            return date.fromisoformat(iso_day).strftime("%d.%m.%Y")
        except ValueError:
            return iso_day

    setting = school.settings
    p = Page()
    p.text(MARGIN, p.y, setting.school_name or "Schule", 9, gray=0.35)
    p.y -= 26
    p.para("Schriftliche Entschuldigung", 18, bold=True, gap=2)
    p.para(f"Bitte ausfüllen, unterschreiben und in der Schule abgeben oder als Foto/PDF im {PRODUCT_NAME} hochladen "
           "(Krankmeldungen › Offene Punkte › „Entschuldigung hochladen“).", 9, gap=12, gray=0.3)
    half = (595 - 2 * MARGIN - 16) / 2
    y0 = p.y
    p.field("Name der Schülerin / des Schülers", st.name if st else "", width=half)
    p.y = y0
    p.field("Klasse", st.class_id if st else "", width=half, x=MARGIN + half + 16)
    kind = (row.kind or "krank") if row else ""
    whole = row is not None and kind in ("krank", "fehlt") and not row.periods
    p.y -= 4
    p.para("Meine Tochter / mein Sohn bzw. ich (volljährig) konnte am Unterricht nicht teilnehmen:", 10, gap=8)
    y0 = p.y
    p.field("vom", de(row.date_from) if row else "", width=half)
    p.y = y0
    p.field("bis einschließlich", de(row.date_to) if row else "", width=half, x=MARGIN + half + 16)
    lessons = ", ".join(period_label(x) for x in (row.periods or [])) if row and row.periods else ""
    p.check("ganze Tage", checked=whole)
    p.check("nur einzelne Stunden:", checked=bool(lessons) and kind in ("krank", "fehlt"),
            after=lessons if kind in ("krank", "fehlt") else "", line_width=260)
    p.check("zu spät gekommen um", checked=kind == "verspaetung", line_width=80,
            after=f"(+{row.minutes} Min.)" if row and row.minutes and kind == "verspaetung" else "")
    p.check("früher gegangen um", checked=kind == "frueh", line_width=80)
    p.y -= 4
    p.para("Grund (freiwillig – Angaben zur Gesundheit sind nicht nötig):", 10, gap=6)
    for _ in range(3):
        p.line(MARGIN, p.y, 595 - MARGIN, p.y, 0.5)
        p.y -= 22
    p.y -= 8
    p.check("Ein ärztliches Attest liegt bei.")
    p.y -= 18
    y0 = p.y
    p.field("Ort, Datum", width=half)
    p.y = y0
    p.field("Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in", width=half,
            x=MARGIN + half + 16)
    phone = getattr(setting, "sick_phone", "") or ""
    if phone:
        hours = getattr(setting, "sick_phone_hours", "") or ""
        p.y -= 10
        p.para(f"Telefonische Krankmeldung am ersten Tag: {phone}" + (f" ({hours})" if hours else ""), 9,
               gray=0.3)
    p.y = 60
    p.para("Nur für die Schule:  [ ] eingegangen am ____________   [ ] entschuldigt   [ ] nicht entschuldigt   "
           "Kürzel ______", 8, gray=0.35)
    pdf = render([p], "Schriftliche Entschuldigung")
    name = f"Entschuldigung_{(st.name if st else 'Formular').replace(' ', '_')}.pdf"
    from schulmanager.server.files import content_disposition
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": content_disposition(name)})


@router.get("/student-absences/leave-form.pdf")
def leave_form(student_id: Optional[str] = Query(None, max_length=40), absence_id: Optional[int] = Query(None),
               user: AuthUser = Depends(current_user), db: Session = Depends(get_db)):
    """Formular „Antrag auf Beurlaubung“ als PDF zum Ausdrucken und Unterschreiben (wie die digitale Eingabe: von–bis,
    Stunden, Anlass). Mit ``student_id``/``absence_id`` vorausgefüllt (nur mit Leserecht für das Kind)."""
    from fastapi.responses import Response

    from schulmanager.calendar_utils import period_label
    from schulmanager.server.db_models import StudentAbsence
    from schulmanager.server.pdf_simple import MARGIN, Page, render

    snap = snapshot()
    school = snap[1]
    row = db.get(StudentAbsence, absence_id) if absence_id else None
    if row is not None:
        student_id = row.student_id
    st = index("students", snap).get(student_id) if student_id else None
    acc = AbsenceAccess(user, snap, db)
    if (row is not None or student_id) and (st is None or _record_level(acc, st.id) is None):
        raise HTTPException(404, "Schüler/in nicht gefunden")
    reason = _texts(row)[0] if row is not None and acc.level(row.student_id) in (FULL, FAMILY) else ""

    def de(iso_day: str) -> str:
        try:
            return date.fromisoformat(iso_day).strftime("%d.%m.%Y")
        except ValueError:
            return iso_day

    setting = school.settings
    p = Page()
    p.text(MARGIN, p.y, setting.school_name or "Schule", 9, gray=0.35)
    p.y -= 26
    p.para("Antrag auf Beurlaubung", 18, bold=True, gap=2)
    p.para("Bitte vor dem Termin ausfüllen, unterschreiben und in der Schule abgeben oder als Foto/PDF im "
           f"{PRODUCT_NAME} hochladen (Krankmeldungen › Beurlaubung beantragen). Die Klassenleitung entscheidet.",
           9, gap=12, gray=0.3)
    half = (595 - 2 * MARGIN - 16) / 2
    y0 = p.y
    p.field("Name der Schülerin / des Schülers", st.name if st else "", width=half)
    p.y = y0
    p.field("Klasse", st.class_id if st else "", width=half, x=MARGIN + half + 16)
    p.y -= 4
    p.para("Ich beantrage die Beurlaubung vom Unterricht:", 10, gap=8)
    y0 = p.y
    p.field("vom", de(row.date_from) if row else "", width=half)
    p.y = y0
    p.field("bis einschließlich", de(row.date_to) if row else "", width=half, x=MARGIN + half + 16)
    lessons = ", ".join(period_label(x) for x in (row.periods or [])) if row and row.periods else ""
    p.check("ganze Tage", checked=row is not None and not row.periods)
    p.check("nur einzelne Stunden:", checked=bool(lessons), after=lessons, line_width=260)
    p.y -= 4
    p.para("Anlass der Beurlaubung (z. B. Arzttermin, Behördentermin, Fahrprüfung):", 10, gap=6)
    for i in range(3):
        if i == 0 and reason:
            p.para(reason[:110], 10, gap=4)
        p.line(MARGIN, p.y, 595 - MARGIN, p.y, 0.5)
        p.y -= 22
    p.y -= 8
    y0 = p.y
    p.field("Ort, Datum", width=half)
    p.y = y0
    p.field("Unterschrift Erziehungsberechtigte/r bzw. volljährige/r Schüler/in", width=half, x=MARGIN + half + 16)
    p.y = 90
    p.para("Nur für die Schule:  [ ] genehmigt   [ ] abgelehnt   Datum ____________   Unterschrift Klassenleitung "
           "______________________", 8, gray=0.35)
    pdf = render([p], "Antrag auf Beurlaubung")
    name = f"Beurlaubung_{(st.name if st else 'Formular').replace(' ', '_')}.pdf"
    from schulmanager.server.files import content_disposition
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": content_disposition(name)})
