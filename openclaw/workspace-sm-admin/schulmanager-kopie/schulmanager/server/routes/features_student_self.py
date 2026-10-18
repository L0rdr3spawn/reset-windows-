"""Schüler-Selbstbedienung, Atteste & Dokumente (ARCHITECTURE.md §9.6).

Endpunkte
---------
* ``GET  /me/student-overview?student_id=`` – „Meine Übersicht“ (Schüler/in bzw. Eltern je Kind): Stammdaten,
  ob eine eigene Krankmeldung erlaubt ist (sonst Hinweis), eigene Krankmeldungen mit Attest-Zustand, Dokumente,
  Klausuren der nächsten 3 Wochen, Klassenleitung, nächster Schultag. Pläne/Aufgaben/Nachrichten holt das
  Frontend über ``/me/today``, ``/channels/overview`` und ``/messages/unread``.
* ``GET    /student-documents`` (``?student_id=&status=&category=&absence_id=``) – sichtbare Dokumente.
* ``POST   /student-documents`` – einreichen (Datei vorher über ``POST /files?purpose=student_document``).
  Schulpersonal darf ohne Datei vermerken, dass ein Papier-Attest vorliegt (Status direkt „geprüft“).
* ``PATCH  /student-documents/{id}`` – Status ``eingegangen|geprueft|abgelehnt`` + Vermerk (Schulpersonal).
* ``DELETE /student-documents/{id}`` – Zurückziehen (archivieren, nichts wird vernichtet): Einreichende (solange
  „eingegangen“) bzw. Sekretariat/Schulleitung; endgültig löscht nur die Aufbewahrungsfrist.
* ``GET    /student-documents/summary`` – Zähler für Menü/Kachel: ``{open, attest_missing}``.

Sichtbarkeit (Gesundheitsdaten, Art. 9 DSGVO): Einreichende; Eltern (nicht bei volljährigen Kindern – außer
eigene Einreichungen); volljährige Schüler/innen für sich; Sekretariat und Schulleitung; die **Klassenleitung**
(Scope ``class_teacher``). Fachlehrkräfte und die technische Administration sehen keine Dokumente.
Titel und Vermerke liegen nur verschlüsselt in der Datenbank, Dateien verschlüsselt in der Dateiablage.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager import student_self as logic
from schulmanager.server import absence_log as alog
from schulmanager.server import crypto, files
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user

from .features_common import cached, has, index, own_student_ids, perm_scope, publish_change, snapshot, write_audit

router = APIRouter(tags=["Schüler-Selbstbedienung"])

PURPOSE = "student_document"
REF_TYPE = "student_document"
READ = "student_documents.read"
FAMILY_ROLES = {"schueler", "eltern"}
OVERVIEW_ABSENCE_DAYS = 60
EXAM_DAYS = 21

files.register_purpose(PURPOSE, kinds=["pdf", "image"], max_mb=15)


class DocumentIn(BaseModel):
    student_id: Optional[str] = Field(None, max_length=40)
    absence_id: Optional[int] = Field(None, ge=1)
    category: Literal["attest", "entschuldigung", "beurlaubung", "einverstaendnis", "sonstiges"] = "attest"
    title: str = Field("", max_length=200)
    file_id: Optional[str] = Field(None, max_length=36)
    note: str = Field("", max_length=1000)


class DocumentPatch(BaseModel):
    status: Optional[Literal["eingegangen", "geprueft", "abgelehnt"]] = None
    note: Optional[str] = Field(None, max_length=1000)


# =========================================================================== Verschlüsselung
def enc(value: str, table: str, col: str, ident: Any) -> str:
    return crypto.encrypt_text(value, f"{table}.{col}:{ident}") if value else ""


def dec(value: Optional[str], table: str, col: str, ident: Any) -> str:
    """Entschlüsselt ``SM1.``-Tokens; Altbestand im Klartext bleibt lesbar. Manipulierte Tokens → Platzhalter."""
    if not value:
        return ""
    if not crypto.is_token(value):
        return value
    try:
        return crypto.decrypt_text(value, f"{table}.{col}:{ident}")
    except Exception:  # noqa: BLE001 - nie mit 500 abbrechen, nie Fremdinhalt zeigen
        return "[nicht lesbar]"


# =========================================================================== Rechte
def _class_teacher_students(teacher_id: Optional[str], snap) -> frozenset[str]:
    if not teacher_id:
        return frozenset()

    def compute():
        classes = {c.id for c in snap[1].classes if c.class_teacher == teacher_id}
        return frozenset(s.id for s in snap[1].students if s.class_id in classes)

    return cached("class_teacher_students", (teacher_id,), compute, snap)


def doc_scope(user, snap) -> Optional[frozenset[str]]:
    """Schüler-IDs, deren Dokumente ``user`` sieht (``None`` = alle, leer = keine – eigene Einreichungen
    sind davon unabhängig immer sichtbar)."""
    if not has(user, READ):
        return frozenset()
    scope = perm_scope(user, READ)
    if scope is None:
        return None
    if scope == "class_teacher":
        return _class_teacher_students(getattr(user, "teacher_id", None), snap)
    if scope in ("own", "own_children"):
        return frozenset(own_student_ids(user))
    return frozenset()


def adult_student_ids(db: Session, student_ids: Iterable[str]) -> set[str]:
    """Schüler-IDs, die volljährig sind (Geburtsdatum, sonst Konto-Merkmal)."""
    from schulmanager.server import parent_access as pa

    ids = sorted(set(student_ids))
    return {sid for sid in ids if pa.is_adult(db, sid)} if ids else set()


def blocked_for_parents(db: Session, student_ids: Iterable[str]) -> set[str]:
    """Volljährige Schüler/innen, deren Eltern Dokumente und Atteste **nicht** sehen dürfen (keine Freigabe im
    Bereich ``dokumente``); Minderjährige sind nie dabei."""
    from schulmanager.server import parent_access as pa

    return {sid for sid in adult_student_ids(db, student_ids) if not pa.parent_may_see(db, sid, pa.AREA_DOCUMENTS)}


def _in(scope: Optional[frozenset[str]], sid: str) -> bool:
    return scope is None or sid in scope


def _family_blocked(user, sid: str, adults: set[str]) -> bool:
    """Eltern volljähriger Kinder ohne Freigabe „dokumente“ sehen deren Dokumente nicht (nur eigene Einreichungen);
    ``adults`` ist hier die Menge aus :func:`blocked_for_parents`."""
    return getattr(user, "role", "") == "eltern" and sid in adults


def can_view(user, doc, snap, adults: set[str]) -> bool:
    if doc.uploaded_by is not None and doc.uploaded_by == getattr(user, "id", None):
        return True
    return _in(doc_scope(user, snap), doc.student_id) and not _family_blocked(user, doc.student_id, adults)


def can_handle(user, sid: str, snap) -> bool:
    """Status/Vermerk setzen: Schulpersonal mit Dokument-Recht für die Schülerin/den Schüler."""
    return getattr(user, "role", "") not in FAMILY_ROLES and _in(doc_scope(user, snap), sid) and has(user, READ)


def _can_delete(user, doc, snap) -> bool:
    if doc.uploaded_by is not None and doc.uploaded_by == getattr(user, "id", None) and doc.status == "eingegangen":
        return True
    return can_handle(user, doc.student_id, snap) and doc_scope(user, snap) is None


def _file_access(db: Session, user, meta) -> bool:
    from schulmanager.server.feature_models.student_self import StudentDocument

    try:
        doc = db.get(StudentDocument, int(meta.ref_id or 0))
    except (TypeError, ValueError):
        return False
    if doc is None or doc.file_id != meta.id:
        return False
    snap = snapshot()
    if doc.withdrawn_at is not None and not can_handle(user, doc.student_id, snap):
        return False                       # archiviert: nur Schulpersonal
    return can_view(user, doc, snap, blocked_for_parents(db, [doc.student_id]))


files.register_access_check(REF_TYPE, _file_access)


# =========================================================================== Ausgabe
def doc_out(doc, user, snap, db: Session) -> dict:
    st = index("students", snap).get(doc.student_id)
    file_info = None
    if doc.file_id:
        meta = files.get_file(db, doc.file_id)
        if meta is not None:
            file_info = {"id": meta.id, "filename": meta.filename, "size": meta.size,
                         "content_type": meta.content_type, "inline": bool(files.file_info(meta).get("inline"))}
    return {"id": doc.id, "student_id": doc.student_id, "student_name": st.name if st else doc.student_id,
            "class_id": st.class_id if st else None, "absence_id": doc.absence_id, "category": doc.category,
            "category_label": logic.CATEGORIES.get(doc.category, doc.category),
            "title": dec(doc.title_enc, "student_documents", "title", doc.id), "file": file_info,
            "paper": doc.file_id is None, "status": doc.status,
            "status_label": logic.DOC_STATUSES.get(doc.status, doc.status),
            "note": dec(doc.note_enc, "student_documents", "note", doc.id),
            "uploaded_by_name": doc.uploaded_by_name, "own": doc.uploaded_by == getattr(user, "id", None),
            "handled_by_name": doc.handled_by_name, "handled_at": iso(doc.handled_at),
            "created_at": iso(doc.created_at), "can_handle": can_handle(user, doc.student_id, snap),
            "can_delete": _can_delete(user, doc, snap)}


def attest_map(db: Session, school, rows: list, today: Optional[date] = None) -> dict[int, dict]:
    """Attest-Zustand je Krankmeldung (für Listen der Krankmeldungen)."""
    from schulmanager.server.feature_models.student_self import StudentDocument

    ids = [r.id for r in rows]
    statuses: dict[int, list[str]] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for aid, status in db.execute(select(StudentDocument.absence_id, StudentDocument.status)
                                      .where(StudentDocument.absence_id.in_(chunk),
                                             StudentDocument.category == "attest",
                                             StudentDocument.withdrawn_at.is_(None))):
            statuses.setdefault(aid, []).append(status)
    students = school.index("students")
    return {r.id: logic.attest_info(school, r.date_from, r.date_to, statuses.get(r.id, ()), today,
                                    cls=getattr(students.get(r.student_id), "class_id", None)).to_dict()
            for r in rows}


def _get_doc(db: Session, doc_id: int):
    from schulmanager.server.feature_models.student_self import StudentDocument

    doc = db.get(StudentDocument, doc_id)
    if doc is None:
        raise HTTPException(404, "Dokument nicht gefunden")
    return doc


# =========================================================================== Dokumente
@router.get("/student-documents")
def list_documents(student_id: Optional[str] = Query(None, max_length=40),
                   status: Optional[Literal["eingegangen", "geprueft", "abgelehnt"]] = None,
                   category: Optional[Literal["attest", "entschuldigung", "beurlaubung", "einverstaendnis", "sonstiges"]] = None,
                   absence_id: Optional[int] = Query(None, ge=1), limit: int = Query(200, ge=1, le=1000),
                   user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Dokumente, die der Benutzer sehen darf (neueste zuerst)."""
    from sqlalchemy import or_

    from schulmanager.server.feature_models.student_self import StudentDocument

    snap = snapshot()
    scope = doc_scope(user, snap)
    q = select(StudentDocument).where(StudentDocument.withdrawn_at.is_(None))
    own = StudentDocument.uploaded_by == user.id
    if scope is not None:
        q = q.where(or_(own, StudentDocument.student_id.in_(sorted(scope))) if scope else own)
    if student_id:
        q = q.where(StudentDocument.student_id == student_id)
    if status:
        q = q.where(StudentDocument.status == status)
    if category:
        q = q.where(StudentDocument.category == category)
    if absence_id:
        q = q.where(StudentDocument.absence_id == absence_id)
    rows = db.scalars(q.order_by(StudentDocument.created_at.desc(), StudentDocument.id.desc()).limit(limit)).all()
    adults = blocked_for_parents(db, {r.student_id for r in rows}) if user.role == "eltern" else set()
    return [doc_out(r, user, snap, db) for r in rows if can_view(user, r, snap, adults)]


@router.post("/student-documents", status_code=201)
def submit_document(body: DocumentIn, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Dokument/Attest einreichen: Eltern für ihre (nicht volljährigen) Kinder, volljährige Schüler/innen für sich,
    Sekretariat/Schulleitung/Klassenleitung für ihre Schüler/innen."""
    from schulmanager.server.db_models import StudentAbsence
    from schulmanager.server.feature_models.student_self import StudentDocument

    snap = snapshot()
    if not has(user, READ):
        raise HTTPException(403, logic.self_report_hint(user.role, user.adult) or "Keine Berechtigung")
    sid = body.student_id
    if not sid:
        own = own_student_ids(user)
        if len(own) != 1:
            raise HTTPException(422, "Bitte die Schülerin/den Schüler angeben")
        sid = own[0]
    if sid not in index("students", snap):
        raise HTTPException(404, "Schüler/in nicht gefunden")
    if not _in(doc_scope(user, snap), sid):
        raise HTTPException(403, "Keine Berechtigung für diese Schülerin/diesen Schüler")
    if user.role == "eltern" and sid in adult_student_ids(db, [sid]):
        raise HTTPException(403, "Ihr Kind ist volljährig und reicht Dokumente selbst ein.")
    if body.absence_id is not None:
        absence = db.get(StudentAbsence, body.absence_id)
        if absence is None or absence.student_id != sid:
            raise HTTPException(422, "Die Krankmeldung gehört nicht zu dieser Schülerin/diesem Schüler")
    staff = user.role not in FAMILY_ROLES
    if not body.file_id and not staff:
        raise HTTPException(422, "Bitte eine Datei (PDF oder Foto) anhängen")
    doc = StudentDocument(student_id=sid, absence_id=body.absence_id, category=body.category, title_enc="",
                          file_id=None, uploaded_by=user.id or None,
                          uploaded_by_name=user.display_name or user.username, status="eingegangen",
                          handled_by_name="", note_enc="", created_at=utcnow())
    db.add(doc)
    db.flush()
    if body.file_id:
        files.attach(db, body.file_id, user, REF_TYPE, doc.id)
        doc.file_id = body.file_id
    else:  # Papiervorlage im Sekretariat vermerkt → gilt als geprüft
        doc.status, doc.handled_by, doc.handled_by_name, doc.handled_at = (
            "geprueft", user.id or None, user.display_name or user.username, utcnow())
    doc.title_enc = enc(logic.clean_title(body.title, body.category), "student_documents", "title", doc.id)
    note = body.note.strip()
    if note:
        doc.note_enc = enc(note, "student_documents", "note", doc.id)
    write_audit(db, user, "student_document.create", f"student_document:{doc.id}",
                {"student_id": sid, "category": body.category, "absence_id": body.absence_id,
                 "paper": body.file_id is None})
    if doc.absence_id:
        paper = body.file_id is None
        alog.record(db, doc.absence_id, sid, "dokument_eingereicht", user,
                    channel="schriftlich" if paper else "online", detail={"category": body.category, "paper": paper})
        if paper:
            alog.record(db, doc.absence_id, sid, "dokument_geprueft", user, channel="schriftlich",
                        detail={"category": body.category, "paper": True})
    db.commit()
    publish_change(["student_documents", "student_absences"])
    return doc_out(doc, user, snap, db)


@router.patch("/student-documents/{doc_id}")
def handle_document(doc_id: int, body: DocumentPatch, user: AuthUser = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    """Prüfen/ablehnen (mit Vermerk) – Sekretariat, Schulleitung, Klassenleitung."""
    doc = _get_doc(db, doc_id)
    snap = snapshot()
    adults = blocked_for_parents(db, [doc.student_id])
    if not can_view(user, doc, snap, adults):
        raise HTTPException(404, "Dokument nicht gefunden")
    if not can_handle(user, doc.student_id, snap):
        raise HTTPException(403, "Keine Berechtigung")
    changes: dict[str, Any] = {}
    if body.status == "abgelehnt" and not ((body.note or "").strip() or dec(doc.note_enc, "student_documents",
                                                                           "note", doc.id)):
        raise HTTPException(422, "Bitte einen Grund für die Ablehnung angeben")
    if body.status is not None and body.status != doc.status:
        changes["status"] = [doc.status, body.status]
        doc.status = body.status
        doc.handled_by, doc.handled_by_name, doc.handled_at = (user.id or None,
                                                               user.display_name or user.username, utcnow())
    if body.note is not None:
        note = body.note.strip()
        if note != dec(doc.note_enc, "student_documents", "note", doc.id):
            changes["note"] = True
            doc.note_enc = enc(note, "student_documents", "note", doc.id)
    if changes.get("status") and doc.status == "geprueft" and doc.absence_id and doc.category in (
            "attest", "entschuldigung"):
        # Geprüfte Entschuldigung bzw. geprüftes Attest → zugehörige Fehlzeit gilt als entschuldigt
        from schulmanager.server.db_models import StudentAbsence
        absence = db.get(StudentAbsence, doc.absence_id)
        if absence is not None and absence.status != "entschuldigt":
            prev_status = absence.status
            absence.status = "entschuldigt"
            absence.excused_by, absence.excused_by_name, absence.excused_at = (
                user.id or None, user.display_name or user.username, utcnow())
            absence.updated_at = utcnow()
            changes["absence_excused"] = absence.id
            alog.record(db, absence.id, absence.student_id, "aenderung", user, changes={"status": [prev_status, "entschuldigt"]},
                        detail={"kind": absence.kind or "krank", "via_document": doc.id})
    if changes.get("status") and doc.absence_id and doc.status in ("geprueft", "abgelehnt"):
        alog.record(db, doc.absence_id, doc.student_id,
                    "dokument_geprueft" if doc.status == "geprueft" else "dokument_abgelehnt", user,
                    detail={"category": doc.category})
    if changes:
        write_audit(db, user, "student_document.update", f"student_document:{doc.id}",
                    {"student_id": doc.student_id, **changes})
        db.commit()
        publish_change(["student_documents", "student_absences"])
    return doc_out(doc, user, snap, db)


@router.delete("/student-documents/{doc_id}")
def delete_document(doc_id: int, user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    doc = _get_doc(db, doc_id)
    snap = snapshot()
    if not can_view(user, doc, snap, blocked_for_parents(db, [doc.student_id])):
        raise HTTPException(404, "Dokument nicht gefunden")
    if not _can_delete(user, doc, snap):
        raise HTTPException(403, "Bereits bearbeitete Dokumente kann nur das Sekretariat löschen.")
    # Dokumente werden nie sofort vernichtet: zurückgezogen = archiviert (Datei bleibt verschlüsselt erhalten,
    # nur noch für Schulpersonal abrufbar); endgültig löscht sie die Aufbewahrungsfrist (``run_retention``)
    doc.withdrawn_at, doc.withdrawn_by_name = utcnow(), user.display_name or user.username
    write_audit(db, user, "student_document.delete", f"student_document:{doc.id}",
                {"student_id": doc.student_id, "archived": True})
    if doc.absence_id:
        alog.record(db, doc.absence_id, doc.student_id, "dokument_zurueckgezogen", user,
                    detail={"category": doc.category})
    db.commit()
    publish_change(["student_documents", "student_absences"])
    return {"deleted": doc_id}


def _missing_attests(db: Session, user, snap, scope: Optional[frozenset[str]]) -> list:
    """Krankmeldungen (letzte 60 Tage) im Scope, bei denen das Attest fehlt."""
    from schulmanager.server.db_models import StudentAbsence

    if scope is not None and not scope:
        return []
    limit = int(getattr(snap[1].settings, "sick_note_after_days", 0) or 0)
    if limit <= 0:
        return []
    since = (date.today() - timedelta(days=OVERVIEW_ABSENCE_DAYS)).isoformat()
    q = select(StudentAbsence).where(StudentAbsence.date_to >= since,
                                     StudentAbsence.date_from <= date.today().isoformat())
    if scope is not None:
        q = q.where(StudentAbsence.student_id.in_(sorted(scope)))
    rows = db.scalars(q.limit(5000)).all()
    info = attest_map(db, snap[1], rows)
    return [r for r in rows if info[r.id]["missing"]]


@router.get("/student-documents/summary")
def documents_summary(user: AuthUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Zähler: offene (eingegangene) Dokumente zur Prüfung, Krankmeldungen mit fehlendem Attest."""
    from schulmanager.server.feature_models.student_self import StudentDocument

    snap = snapshot()
    scope = doc_scope(user, snap)
    if not has(user, READ):
        return {"open": 0, "attest_missing": 0}
    open_count = 0
    if user.role not in FAMILY_ROLES and (scope is None or scope):
        q = select(func.count(StudentDocument.id)).where(StudentDocument.status == "eingegangen",
                                                         StudentDocument.withdrawn_at.is_(None))
        if scope is not None:
            q = q.where(StudentDocument.student_id.in_(sorted(scope)))
        open_count = int(db.scalar(q) or 0)
    if user.role == "eltern":  # Krankmeldungen volljähriger Kinder nur mit Freigabe (B-06/U-103), wie die Liste
        from schulmanager.server.absence_access import AbsenceAccess
        scope = AbsenceAccess(user, snap, db).family_ids & (scope or frozenset())
    out = {"open": open_count, "attest_missing": len(_missing_attests(db, user, snap, scope))}
    if perm_scope(user, READ) == "class_teacher":  # für Kachel/Menü: Klassenleitung welcher Klassen?
        tid = getattr(user, "teacher_id", None)
        out["class_teacher_of"] = sorted(c.id for c in snap[1].classes if tid and c.class_teacher == tid)
    return out


# =========================================================================== Meine Übersicht
def _next_school_day(school, day: date, cls=None) -> Optional[date]:
    from schulmanager.calendar_utils import is_school_day

    d = day
    for _ in range(30):
        d += timedelta(days=1)
        if is_school_day(school, d, cls)[0]:     # Unterrichtstage der Klasse (R3)
            return d
    return None


@router.get("/me/student-overview")
def student_overview(student_id: Optional[str] = Query(None, max_length=40), user: AuthUser = Depends(current_user),
                     db: Session = Depends(get_db)) -> dict:
    from schulmanager.calendar_utils import is_school_day
    from schulmanager.server.db_models import StudentAbsence
    from schulmanager.server.feature_models.student_self import StudentDocument

    from schulmanager.server.absence_access import FAMILY, AbsenceAccess

    from .features_student_absences import absence_out
    from .features_substitutions import _exam_rows, _student_exam_filter

    sids = own_student_ids(user)
    if user.role not in FAMILY_ROLES or not sids:
        raise HTTPException(403, "„Meine Übersicht“ gibt es für Schüler/innen und Eltern.")
    sid = student_id or sids[0]
    if sid not in sids:
        raise HTTPException(403, "Keine Berechtigung für diese Schülerin/diesen Schüler")
    snap = snapshot()
    school = snap[1]
    students = index("students", snap)
    st = students.get(sid)
    if st is None:
        raise HTTPException(404, "Schüler/in nicht gefunden")
    cls = index("classes", snap).get(st.class_id)
    teachers = index("teachers", snap)
    adults = adult_student_ids(db, sids)
    today = date.today()
    # Krankmelden/Krankmeldungen (Eltern volljähriger Kinder nur mit Freigabe „krankmeldungen“, B-06/U-103)
    acc = AbsenceAccess(user, snap, db)
    absences_visible = acc.level(sid) == FAMILY
    can_report = acc.can_report and absences_visible  # auch volljährig nach Geburtsdatum ohne Konto-Merkmal
    if can_report:
        hint = None
    elif acc.linked_but_hidden(sid):
        hint = "Ihr Kind ist volljährig und meldet sich selbst krank."
    else:
        hint = logic.self_report_hint(user.role, bool(user.adult)) or "Keine Berechtigung"
    # Dokumente (Eltern volljähriger Kinder: nur eigene Einreichungen)
    docs_visible = has(user, READ) and not _family_blocked(user, sid, blocked_for_parents(db, [sid]))
    can_submit = docs_visible
    docs_q = select(StudentDocument).where(StudentDocument.student_id == sid,
                                           StudentDocument.withdrawn_at.is_(None))
    if not docs_visible:
        docs_q = docs_q.where(StudentDocument.uploaded_by == user.id)
    docs = db.scalars(docs_q.order_by(StudentDocument.created_at.desc()).limit(20)).all()
    # Krankmeldungen
    since = (today - timedelta(days=OVERVIEW_ABSENCE_DAYS)).isoformat()
    rows = db.scalars(select(StudentAbsence).where(StudentAbsence.student_id == sid, StudentAbsence.date_to >= since)
                      .order_by(StudentAbsence.date_from.desc(), StudentAbsence.id.desc())
                      .limit(100)).all() if absences_visible else []
    attest = attest_map(db, school, rows, today)
    absences = [absence_out(r, snap, user, attest.get(r.id), acc=acc) for r in rows]
    asked = {aid for aid, evs in alog.events_by_absence(db, [r.id for r in rows]).items()
             if any(e.event == "ruecknahme_angefragt" for e in evs)} if rows else set()
    for item in absences:
        item["withdrawal_requested"] = item["id"] in asked
    # Klausuren
    end = (today + timedelta(days=EXAM_DAYS)).isoformat()
    upcoming = sorted((e for e in school.exams if today.isoformat() <= e.date <= end), key=lambda e: (e.date, e.start))
    exams = _exam_rows(school, upcoming, _student_exam_filter(snap, sid))
    ct = teachers.get(cls.class_teacher) if cls and cls.class_teacher else None
    school_day, why_not = is_school_day(school, today, st.class_id)
    nxt = _next_school_day(school, today, st.class_id)
    return {
        "student": {"id": st.id, "name": st.name, "class_id": st.class_id, "class_name": cls.name if cls else st.class_id,
                    "adult": sid in adults},
        "children": [{"id": s, "name": students[s].name, "class_id": students[s].class_id, "adult": s in adults}
                     for s in sids if s in students] if user.role == "eltern" else [],
        "role": user.role,
        "today": today.isoformat(), "today_is_school_day": school_day, "today_note": why_not,
        "next_school_day": nxt.isoformat() if nxt else None,
        "can_report": can_report, "report_hint": hint, "absences_hidden": not absences_visible,
        "can_submit_documents": can_submit, "documents_hidden": not docs_visible and user.role == "eltern",
        "sick_note_after_days": int(getattr(school.settings, "sick_note_after_days", 0) or 0),
        "absences": absences,
        "attest_missing": sum(1 for a in absences if (a.get("attest") or {}).get("missing")),
        "documents": [doc_out(d, user, snap, db) for d in docs],
        "exams": exams,
        "class_teacher": {"id": ct.id, "name": ct.name} if ct else None,
        "periods": school.settings.periods,
    }


# =========================================================================== Export (DSGVO)
def export_documents(db: Session, user, student_ids: list[str]) -> list[dict]:
    """Metadaten eigener bzw. eigene Kinder betreffender Dokumente (Titel/Vermerk entschlüsselt) – nur, was die
    Liste und der Dateizugriff dem Konto zeigen (:func:`can_view`; Eltern volljähriger Kinder nur eigene
    Einreichungen, U-03)."""
    from sqlalchemy import or_

    from schulmanager.server.feature_models.student_self import StudentDocument

    conds = [StudentDocument.uploaded_by == user.id]
    if student_ids:
        conds.append(StudentDocument.student_id.in_(student_ids))
    rows = db.scalars(select(StudentDocument).where(or_(*conds)).order_by(StudentDocument.id)).all()
    snap = snapshot()
    adults = blocked_for_parents(db, {d.student_id for d in rows}) if user.role == "eltern" else set()
    out = []
    for d in (r for r in rows if can_view(user, r, snap, adults)):
        out.append({"id": d.id, "student_id": d.student_id, "absence_id": d.absence_id, "category": d.category,
                    "title": dec(d.title_enc, "student_documents", "title", d.id), "file_id": d.file_id,
                    "status": d.status, "note": dec(d.note_enc, "student_documents", "note", d.id),
                    "uploaded_by_name": d.uploaded_by_name, "handled_by_name": d.handled_by_name,
                    "handled_at": iso(d.handled_at), "created_at": iso(d.created_at)})
    return out


def run_retention(days: int) -> int:
    """Wartung: Dokumente älter als ``days`` Tage (samt Datei) löschen; 0 = aus."""
    from schulmanager.server.db import session_scope
    from schulmanager.server.feature_models.student_self import StudentDocument

    if days <= 0:
        return 0
    cutoff = utcnow() - timedelta(days=days)
    n = 0
    with session_scope() as db:
        for doc in db.scalars(select(StudentDocument).where(StudentDocument.created_at < cutoff).limit(5000)).all():
            if doc.file_id:
                files.delete(db, doc.file_id, None, hard=True)
            db.delete(doc)
            n += 1
    return n
