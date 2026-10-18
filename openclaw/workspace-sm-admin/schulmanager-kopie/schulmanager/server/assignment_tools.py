"""Hilfen für Aufgaben im Kursraum – Bewertungsraster, Fristverlängerung, Versionen, Gruppenabgabe und die
**Ergebnis-Schnittstelle für das Notenbuch** (:func:`list_results`).

Gruppenabgabe
-------------
Jedes Gruppenmitglied hat eine eigene Abgabe-Zeile (``assignment_submissions.group_id``) mit **demselben Inhalt**
(Text, Dateien, Status, Version) – so gelten alle bestehenden Abfragen je Schüler/in weiter. Ändert ein Mitglied die
Abgabe, wird sie an die Zeilen der anderen kopiert (:func:`propagate`); die gemeinsame Bewertung ebenfalls, außer bei
Zeilen mit ``individual=True`` (Einzelanpassung der Lehrkraft). Dateien hängen an der Zeile ihres Hochladers; die
anderen Mitglieder dürfen sie lesen, weil die Datei in ihrer eigenen Zeile steht (:func:`file_in_user_rows`).

Ergebnisse für das Notenbuch
----------------------------
:func:`list_results` liefert je bewerteter Abgabe: ``channel_id``, ``item_id``, ``title`` (Aufgabe),
``student_user_id``/``student_id`` (Schüler/in), ``points``/``max_points``/``percent``, ``grade`` (Text, z. B. ``"2+"``),
``grade_number`` (Zahl, wenn eindeutig lesbar), ``graded_at`` (ISO, UTC), dazu ``attempt``, ``late``, ``group_id``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from schulmanager import grading

from .channel_groups import group_of_user, members_of
from .db import iso, utcnow
from .db_models import User
from .feature_models.assignments import (AssignmentExtension, AssignmentSettings, AssignmentSubmissionVersion)
from .feature_models.channel_groups import ChannelGroup, ChannelGroupMember
from .feature_models.channels import AssignmentSubmission, ChannelItem
from .files import StoredFile

REF_SUBMISSION = "submission"
_CHUNK = 500


def _chunks(values: Iterable[Any], size: int = _CHUNK):
    vals = list(values)
    for i in range(0, len(vals), size):
        yield vals[i:i + size]


# =========================================================================== Einstellungen
def settings_for(db: Session, item_id: int) -> Optional[AssignmentSettings]:
    return db.scalar(select(AssignmentSettings).where(AssignmentSettings.item_id == item_id))


def settings_map(db: Session, item_ids: Iterable[int]) -> dict[int, AssignmentSettings]:
    out: dict[int, AssignmentSettings] = {}
    for chunk in _chunks(set(item_ids)):
        for s in db.scalars(select(AssignmentSettings).where(AssignmentSettings.item_id.in_(chunk))):
            out[s.item_id] = s
    return out


def get_or_create_settings(db: Session, item_id: int) -> AssignmentSettings:
    row = settings_for(db, item_id)
    if row is None:
        row = AssignmentSettings(item_id=item_id, group_mode=False, rubric_enc="", rubric_title="",
                                 show_parents=False)
        db.add(row)
        db.flush()
    return row


def max_points_of(settings: Optional[AssignmentSettings]) -> Optional[float]:
    """Höchstpunktzahl: aus dem Raster, sonst die frei eingetragene (``None`` = keine Punkte vorgesehen)."""
    if settings is None:
        return None
    rubric = settings.rubric()
    if rubric:
        return grading.max_points(rubric)
    return settings.max_points


def scale_of(settings: Optional[AssignmentSettings]) -> dict[str, Any]:
    return (settings.grade_scale if settings is not None and settings.grade_scale else None) or dict(
        grading.DEFAULT_SCALE)


def grade_for_points(settings: Optional[AssignmentSettings], points: Optional[float]) -> Optional[str]:
    return grading.grade_for(points, max_points_of(settings), scale_of(settings))


# =========================================================================== Fristverlängerung
def due_overrides(db: Session, item_ids: Iterable[int], user_id: Optional[int]) -> dict[int, datetime]:
    """Verlängerte Frist (UTC) je Aufgabe für ein Konto: persönlich oder über die Gruppe (die spätere gilt)."""
    ids = list(set(item_ids))
    out: dict[int, datetime] = {}
    if not ids or not user_id:
        return out
    groups = set(db.scalars(select(ChannelGroupMember.group_id).where(ChannelGroupMember.user_id == user_id)))
    cond = AssignmentExtension.user_id == user_id
    if groups:
        cond = or_(cond, AssignmentExtension.group_id.in_(groups))
    for chunk in _chunks(ids):
        for item_id, due in db.execute(select(AssignmentExtension.item_id, AssignmentExtension.due_at).where(
                AssignmentExtension.item_id.in_(chunk), cond)):
            if item_id not in out or due > out[item_id]:
                out[item_id] = due
    return out


def effective_due(base: Optional[datetime], override: Optional[datetime]) -> Optional[datetime]:
    """Frist, die für eine Person gilt: nie früher als die allgemeine Frist; ohne Frist bleibt es ohne Frist."""
    if base is None:
        return None
    return max(base, override) if override is not None else base


def extension_hint(db: Session, item_id: int, user_id: Optional[int]) -> Optional[AssignmentExtension]:
    """Die Verlängerung, die für ``user_id`` gilt (persönlich vor Gruppe, jeweils die spätere)."""
    if not user_id:
        return None
    groups = set(db.scalars(select(ChannelGroupMember.group_id).where(ChannelGroupMember.user_id == user_id)))
    cond = AssignmentExtension.user_id == user_id
    if groups:
        cond = or_(cond, AssignmentExtension.group_id.in_(groups))
    rows = list(db.scalars(select(AssignmentExtension).where(AssignmentExtension.item_id == item_id, cond)))
    return max(rows, key=lambda e: e.due_at, default=None)


# =========================================================================== Versionen
def snapshot_version(db: Session, sub: AssignmentSubmission) -> AssignmentSubmissionVersion:
    """Hält den aktuellen Stand (Abgabe + Rückmeldung) der Abgabe als abgeschlossene Version fest."""
    v = AssignmentSubmissionVersion(
        submission_id=sub.id, attempt=sub.attempt or 1, text_enc="", feedback_enc="", grade_enc="", rubric_enc="",
        file_ids=list(sub.file_ids or []) or None, submitted_at=sub.submitted_at, status=sub.status or "abgegeben",
        points=sub.points, max_points=sub.max_points, feedback_file_ids=list(sub.feedback_file_ids or []) or None,
        feedback_by=sub.feedback_by, feedback_at=sub.feedback_at, closed_at=utcnow())
    db.add(v)
    db.flush()
    v.write_text("text", sub.read_text("text"))
    v.write_text("feedback", sub.read_text("feedback"))
    v.write_text("grade", sub.read_text("grade"))
    v.write_text("rubric", sub.read_text("rubric"))
    return v


def versions_of(db: Session, sub_ids: Iterable[int]) -> dict[int, list[AssignmentSubmissionVersion]]:
    out: dict[int, list[AssignmentSubmissionVersion]] = {}
    for chunk in _chunks(set(sub_ids)):
        for v in db.scalars(select(AssignmentSubmissionVersion).where(
                AssignmentSubmissionVersion.submission_id.in_(chunk)).order_by(
                AssignmentSubmissionVersion.attempt)):
            out.setdefault(v.submission_id, []).append(v)
    return out


def versioned_file_ids(db: Session, item_id: int) -> set[str]:
    """Dateien, die eine frühere Version einer Abgabe dieser Aufgabe benutzt (dürfen nicht gelöscht werden)."""
    ids: set[str] = set()
    stmt = (select(AssignmentSubmissionVersion.file_ids, AssignmentSubmissionVersion.feedback_file_ids)
            .join(AssignmentSubmission, AssignmentSubmission.id == AssignmentSubmissionVersion.submission_id)
            .where(AssignmentSubmission.item_id == item_id))
    for files_, fb in db.execute(stmt):
        ids.update(files_ or [])
        ids.update(fb or [])
    return ids


# =========================================================================== Gruppenabgabe
def copy_content(src: AssignmentSubmission, dst: AssignmentSubmission) -> None:
    dst.write_text("text", src.read_text("text"))
    dst.file_ids = list(src.file_ids or []) or None
    dst.status = src.status
    dst.submitted_at = src.submitted_at
    dst.attempt = src.attempt
    dst.updated_at = src.updated_at


def copy_results(src: AssignmentSubmission, dst: AssignmentSubmission) -> None:
    dst.write_text("feedback", src.read_text("feedback"))
    dst.write_text("grade", src.read_text("grade"))
    dst.write_text("rubric", src.read_text("rubric"))
    dst.points = src.points
    dst.max_points = src.max_points
    dst.feedback_file_ids = list(src.feedback_file_ids or []) or None
    dst.feedback_by = src.feedback_by
    dst.feedback_at = src.feedback_at
    dst.status = src.status


def clear_results(row: AssignmentSubmission) -> None:
    """Leert Rückmeldung, Note, Punkte und Raster (nach erneuter Abgabe einer Überarbeitung)."""
    row.write_text("feedback", "")
    row.write_text("grade", "")
    row.write_text("rubric", "")
    row.points = None
    row.max_points = None
    row.feedback_file_ids = None
    row.feedback_at = None
    row.individual = False


def group_rows(db: Session, item_id: int, group_id: int) -> list[AssignmentSubmission]:
    return list(db.scalars(select(AssignmentSubmission).where(
        AssignmentSubmission.item_id == item_id, AssignmentSubmission.group_id == group_id)
        .order_by(AssignmentSubmission.id)))


def _student_ids(db: Session, user_ids: Iterable[int]) -> dict[int, Optional[str]]:
    out: dict[int, Optional[str]] = {}
    for chunk in _chunks(set(user_ids)):
        for uid, sid in db.execute(select(User.id, User.student_id).where(User.id.in_(chunk))):
            out[uid] = sid
    return out


def new_row(db: Session, item_id: int, user_id: int, student_id: Optional[str], group_id: Optional[int]
            ) -> AssignmentSubmission:
    row = AssignmentSubmission(item_id=item_id, student_user_id=user_id, student_id=student_id, group_id=group_id,
                               text_enc="", feedback_enc="", grade_enc="", rubric_enc="", attempt=1,
                               status="abgegeben", created_at=utcnow())
    db.add(row)
    db.flush()
    return row


def propagate(db: Session, src: AssignmentSubmission, *, results: bool = False, force: bool = False) -> int:
    """Überträgt Inhalt (und mit ``results`` die Bewertung) auf die Zeilen der anderen Gruppenmitglieder; legt fehlende
    Zeilen an. Zeilen mit Einzelanpassung behalten ihre Bewertung (außer mit ``force``). Gibt die Zeilenzahl zurück."""
    if not src.group_id:
        return 0
    members = members_of(db, src.group_id)
    rows = {r.student_user_id: r for r in group_rows(db, src.item_id, src.group_id)}
    sids = _student_ids(db, members)
    n = 0
    for uid in members:
        if uid == src.student_user_id:
            continue
        row = rows.get(uid)
        if row is None:
            existing = db.scalar(select(AssignmentSubmission).where(AssignmentSubmission.item_id == src.item_id,
                                                                    AssignmentSubmission.student_user_id == uid))
            row = existing or new_row(db, src.item_id, uid, sids.get(uid), src.group_id)
            row.group_id = src.group_id
        copy_content(src, row)
        if results and (force or not row.individual):
            copy_results(src, row)
            if force:
                row.individual = False
        n += 1
    return n


def normalize_item_groups(db: Session, item: ChannelItem, settings: Optional[AssignmentSettings]) -> None:
    """Gleicht die Abgabe-Zeilen einer Gruppen-Aufgabe mit der aktuellen Einteilung ab: Mitglieder, die die Gruppe
    verlassen haben, verlieren ihre Zeile (Dateien wandern zu einem verbleibenden Mitglied); neue Mitglieder erhalten
    den Stand der Gruppe."""
    if settings is None or not settings.group_mode or not settings.group_set_id:
        return
    mem = {uid: gid for uid, gid in db.execute(select(ChannelGroupMember.user_id, ChannelGroupMember.group_id)
                                               .where(ChannelGroupMember.set_id == settings.group_set_id))}
    rows = list(db.scalars(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item.id)))
    by_group: dict[int, list[AssignmentSubmission]] = {}
    for r in rows:
        if r.group_id and mem.get(r.student_user_id) == r.group_id:
            by_group.setdefault(r.group_id, []).append(r)
    for r in rows:
        if r.group_id and mem.get(r.student_user_id) != r.group_id:
            keep = by_group.get(r.group_id) or []
            if keep:
                db.query(StoredFile).filter(StoredFile.ref_type == REF_SUBMISSION,
                                            StoredFile.ref_id == str(r.id)).update(
                    {"ref_id": str(keep[0].id)}, synchronize_session=False)
            db.delete(r)
    db.flush()
    for gid, grows in by_group.items():
        fresh = max(grows, key=lambda r: (r.updated_at or r.created_at or datetime.min))
        propagate(db, fresh)
    db.flush()


def normalize_channel(db: Session, channel_id: int) -> None:
    for item in db.scalars(select(ChannelItem).where(ChannelItem.channel_id == channel_id)):
        st = settings_for(db, item.id)
        if st is not None and st.group_mode:
            normalize_item_groups(db, item, st)


def group_for_user(db: Session, settings: Optional[AssignmentSettings], user_id: Optional[int]
                   ) -> Optional[ChannelGroup]:
    if settings is None or not settings.group_mode:
        return None
    return group_of_user(db, settings.group_set_id, user_id)


def file_in_user_rows(db: Session, item_id: int, user_id: Optional[int], file_id: str) -> bool:
    """Steht die Datei in einer (Gruppen-)Abgabe-Zeile dieses Kontos? (Zugriff auf Dateien der Gruppe)"""
    if not user_id:
        return False
    for r in db.scalars(select(AssignmentSubmission).where(AssignmentSubmission.item_id == item_id,
                                                           AssignmentSubmission.student_user_id == user_id)):
        if file_id in (r.file_ids or []) or file_id in (r.feedback_file_ids or []):
            return True
    versions = db.execute(select(AssignmentSubmissionVersion.file_ids, AssignmentSubmissionVersion.feedback_file_ids)
                          .join(AssignmentSubmission, AssignmentSubmission.id == AssignmentSubmissionVersion.submission_id)
                          .where(AssignmentSubmission.item_id == item_id, AssignmentSubmission.student_user_id == user_id))
    return any(file_id in (a or []) or file_id in (b or []) for a, b in versions)


# =========================================================================== Ergebnisse (Schnittstelle Notenbuch)
def list_results(db: Session, *, channel_id: Optional[int] = None, item_ids: Optional[Iterable[int]] = None,
                 student_user_id: Optional[int] = None, student_id: Optional[str] = None,
                 since: Optional[datetime] = None) -> list[dict[str, Any]]:
    """Bewertete Abgaben als flache Ergebnisse (Schnittstelle für das Notenbuch, siehe Modul-Doku).

    Filter: Kursraum, Aufgaben, Konto oder Schüler-ID, ``since`` (Bewertung nach diesem Zeitpunkt, UTC).
    Nur Abgaben mit Status ``bewertet`` und mindestens Punkten oder Note."""
    stmt = (select(AssignmentSubmission, ChannelItem.title, ChannelItem.channel_id, ChannelItem.due_at)
            .join(ChannelItem, ChannelItem.id == AssignmentSubmission.item_id)
            .where(AssignmentSubmission.status == "bewertet"))
    if channel_id is not None:
        stmt = stmt.where(ChannelItem.channel_id == channel_id)
    if item_ids is not None:
        stmt = stmt.where(AssignmentSubmission.item_id.in_(list(item_ids) or [0]))
    if student_user_id is not None:
        stmt = stmt.where(AssignmentSubmission.student_user_id == student_user_id)
    if student_id is not None:
        stmt = stmt.where(AssignmentSubmission.student_id == student_id)
    if since is not None:
        stmt = stmt.where(AssignmentSubmission.feedback_at >= since)
    out: list[dict[str, Any]] = []
    for sub, title, cid, due in db.execute(stmt.order_by(AssignmentSubmission.feedback_at, AssignmentSubmission.id)):
        grade = sub.read_text("grade")
        if sub.points is None and not grade:
            continue
        eff = effective_due(due, due_overrides(db, [sub.item_id], sub.student_user_id).get(sub.item_id))
        out.append({
            "source": "assignment", "channel_id": cid, "item_id": sub.item_id, "title": title,
            "student_user_id": sub.student_user_id, "student_id": sub.student_id, "submission_id": sub.id,
            "points": sub.points, "max_points": sub.max_points, "percent": grading.percent(sub.points, sub.max_points),
            "grade": grade, "grade_number": grading.grade_number(grade), "graded_at": iso(sub.feedback_at),
            "attempt": sub.attempt or 1, "group_id": sub.group_id,
            "late": bool(eff is not None and sub.submitted_at is not None and sub.submitted_at > eff)})
    return out


def count_rows(db: Session, item_id: int) -> int:
    return int(db.scalar(select(func.count()).select_from(AssignmentSubmission).where(
        AssignmentSubmission.item_id == item_id)) or 0)


def publish_to_gradebook(db: Session, item: ChannelItem) -> int:
    """Bewertete Abgaben der Aufgabe dem Notenbuch anbieten (Quelle ``aufgabe`` + Element-ID, Doku: NOTENBUCH.md §6).
    Nur Kursräume eines Kursteils haben ein Notenbuch; die Lehrkraft übernimmt die Quelle dort selbst. Ohne Commit;
    Fehler werden geschluckt (Savepoint), damit das Bewerten nie daran scheitert."""
    import logging

    from . import gradebook_sources as gs
    from .feature_models.channels import Channel
    try:
        ch = db.get(Channel, item.channel_id)
        if ch is None or ch.kind != "course" or not ch.ref or "#" not in ch.ref:
            return 0
        course_id, part = ch.ref.rsplit("#", 1)
        db.flush()  # gerade gesetzte Bewertungen müssen in der Abfrage sichtbar sein
        rows = [r for r in list_results(db, item_ids=[item.id]) if r["student_id"]]
        results = [gs.SourceResult(r["student_id"], points=r["points"]) if r["points"] is not None
                   else gs.SourceResult(r["student_id"], grade=r["grade"]) for r in rows]
        top = max_points_of(settings_for(db, item.id))
        date = (item.due_at or utcnow()).date().isoformat()
        with db.begin_nested():
            return gs.publish_results(db, source_type="aufgabe", source_id=str(item.id), course_id=course_id,
                                      part=int(part), title=item.title or "Aufgabe", date=date, max_points=top,
                                      results=results)
    except Exception:  # noqa: BLE001 - das Notenbuch darf das Bewerten nie stören
        logging.getLogger("schulmanager.assignments").exception("Aufgabe %s: Übergabe ans Notenbuch fehlgeschlagen",
                                                                item.id)
        return 0


def withdraw_from_gradebook(db: Session, item_id: int) -> None:
    from . import gradebook_sources as gs
    try:
        with db.begin_nested():
            gs.withdraw_results(db, "aufgabe", str(item_id))
    except Exception:  # noqa: BLE001
        pass
