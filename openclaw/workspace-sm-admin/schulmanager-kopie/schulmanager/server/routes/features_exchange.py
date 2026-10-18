"""Import/Export (Untis GPU, Schulmanager-Online-Paket, CSV, JSON), iCal-Feed und
Benachrichtigungs-Outbox.

* Exporte: ``timetable.edit`` oder ``masterdata.edit`` (enthalten Schülerdaten)
* Importe laufen über ``store.mutate`` (neue Version, Undo möglich); ``?dry_run=1`` prüft nur.
* ``public_router``: ``GET /ical/{token}.ics`` (ohne ``/api/v1``, Token aus ``GET /me/ical-url``)
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import date, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schulmanager.branding import PRODUCT_NAME
from schulmanager.models import COLLECTIONS, School
from schulmanager.server.db import get_db, iso, utcnow
from schulmanager.server.deps import AuthUser, current_user, require, user_from_ical_token

from .features_common import (check_range, day_plan, filter_plan, has, mutate, need, own_student_ids, parse_date,
                              perm_scope, range_plans, reads_all_plans, snapshot)

router = APIRouter(tags=["Import/Export"])
public_router = APIRouter(tags=["Kalender"])

CSV_WHAT = ("teachers", "classes", "rooms", "subjects", "students", "lessons", "curricula")
CsvWhat = Literal["teachers", "classes", "rooms", "subjects", "students", "lessons", "curricula"]
MAX_UPLOAD = 50 * 1024 * 1024
MAX_ZIP_FILES = 300


def _export_user(user) -> None:
    need(user, "timetable.edit", "masterdata.edit")


def _download(content: bytes | str, filename: str, media_type: str) -> Response:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"',
                             "Cache-Control": "no-store"})


def _plans(date_from: Optional[str], date_to: Optional[str], snap) -> list[dict]:
    d1 = parse_date(date_from, date.today(), name="from")
    d2 = parse_date(date_to, d1 + timedelta(days=6), name="to")
    check_range(d1, d2, 31)
    return range_plans(d1, d2, snap)


def _stamp() -> str:
    return date.today().strftime("%Y%m%d")


def _replace_all(target: School, source: School) -> None:
    target.settings = source.settings
    for name in COLLECTIONS:
        setattr(target, name, getattr(source, name))


def _counts(school: School) -> dict[str, int]:
    return {name: len(getattr(school, name)) for name in COLLECTIONS}


# ===================================================================== Export
@router.get("/export/untis.zip")
def export_untis(date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
                 user: AuthUser = Depends(current_user)):
    """Untis-GPU-Dateien (GPU001–006, 010, 014) als ZIP; Vertretungen für ``from``–``to`` (Standard 7 Tage)."""
    _export_user(user)
    from schulmanager.integrations.untis_gpu import export_zip
    snap = snapshot()
    data = export_zip(snap[1], _plans(date_from, date_to, snap))
    return _download(data, f"untis-gpu-{_stamp()}.zip", "application/zip")


@router.get("/export/schulmanager-online.zip")
def export_smo(date_from: Optional[str] = Query(None, alias="from"), date_to: Optional[str] = Query(None, alias="to"),
               students: bool = Query(True, description="Schülerdaten mitliefern"),
               user: AuthUser = Depends(current_user)):
    """Importpaket für Schulmanager Online (Untis-Dateien + CSV + Anleitung)."""
    _export_user(user)
    from schulmanager.integrations.schulmanager_online import export_package
    snap = snapshot()
    data = export_package(snap[1], _plans(date_from, date_to, snap), include_students=students)
    return _download(data, f"schulmanager-online-{_stamp()}.zip", "application/zip")


@router.get("/export/csv/{what}")
def export_csv(what: CsvWhat, user: AuthUser = Depends(current_user)):
    """CSV (``;``, UTF-8 mit BOM für Excel)."""
    if what == "students":
        if not has(user, "students.read") or perm_scope(user, "students.read") is not None:
            raise HTTPException(403, "Keine Berechtigung")
    elif not (reads_all_plans(user) or has(user, "masterdata.edit") or has(user, "timetable.edit")):
        # Lehrkräfte (plans.read_all nur für eigene Klassen) exportieren keine schulweiten Daten
        raise HTTPException(403, "Keine Berechtigung")
    from schulmanager.integrations.csv_io import export_csv as _export
    text = _export(snapshot()[1], what)
    if not text.startswith("﻿"):
        text = "﻿" + text
    return _download(text, f"{what}-{_stamp()}.csv", "text/csv; charset=utf-8")


@router.get("/export/json")
def export_json(user: AuthUser = Depends(current_user)):
    """Komplettes Planungsdokument als JSON (wieder importierbar über ``POST /import/json``)."""
    _export_user(user)
    ver, school = snapshot()
    doc = {"format": "schulmanager", "format_version": 1, "version": ver, "exported_at": iso(utcnow()),
           "school": school.to_dict()}
    return _download(json.dumps(doc, ensure_ascii=False, indent=1), f"schulmanager-{_stamp()}.json",
                     "application/json")


# ===================================================================== Import
async def _read_upload(f: UploadFile) -> bytes:
    data = await f.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Datei zu groß (maximal 50 MB)")
    return data


def _unzip(data: bytes) -> dict[str, bytes]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(422, "Ungültige ZIP-Datei") from None
    out: dict[str, bytes] = {}
    total = 0
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if len(infos) > MAX_ZIP_FILES:
        raise HTTPException(422, "Zu viele Dateien im ZIP")
    for info in infos:
        total += info.file_size
        if total > 4 * MAX_UPLOAD:
            raise HTTPException(413, "ZIP-Inhalt zu groß")
        name = info.filename.replace("\\", "/").rsplit("/", 1)[-1]
        if name and not name.startswith("."):
            out[name] = zf.read(info)
    return out


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


@router.post("/import/untis")
async def import_untis(files: list[UploadFile] = File(...), mode: Literal["merge", "replace"] = Form("merge"),
                       dry_run: bool = Query(False), user: AuthUser = Depends(require("timetable.edit"))):
    """Untis-GPU-Import (einzelne GPU-Dateien oder ein ZIP). ``mode=merge`` ergänzt/aktualisiert,
    ``mode=replace`` ersetzt das Planungsdokument."""
    collected: dict[str, bytes] = {}
    for f in files:
        data = await _read_upload(f)
        name = (f.filename or "upload").rsplit("/", 1)[-1]
        if name.lower().endswith(".zip") or data[:4] == b"PK\x03\x04":
            collected.update(_unzip(data))
        else:
            collected[name] = data
    if not collected:
        raise HTTPException(422, "Keine Dateien erhalten")
    return await run_in_threadpool(_do_import_untis, user, collected, mode, dry_run)


def _do_import_untis(user, files: dict[str, bytes], mode: str, dry_run: bool) -> dict:
    from schulmanager.integrations.untis_gpu import import_files
    from schulmanager.server.store import copy_school

    def run(school: School) -> dict:
        base = school if mode == "merge" else None
        webhooks = list(school.settings.webhooks)
        try:
            new, warnings = import_files(files, base)
        except (ValueError, KeyError) as exc:
            raise HTTPException(422, f"Untis-Import fehlgeschlagen: {exc}") from None
        if new is not school:
            _replace_all(school, new)
            if not school.settings.webhooks:
                school.settings.webhooks = webhooks  # Konfiguration nicht durch Import verlieren
        return {"warnings": list(warnings), "counts": _counts(school), "files": sorted(files), "mode": mode,
                "dry_run": dry_run}

    if dry_run:
        return run(copy_school(snapshot()[1]))
    return mutate(user, f"Untis-Import ({mode}, {len(files)} Dateien)", run, scope=["all", "import"])


@router.get("/import/csv/{what}/fields")
def import_csv_fields(what: CsvWhat, user: AuthUser = Depends(current_user)):
    """Zielfelder, erkannte Spaltennamen und Presets (SchILD-NRW, ASV, …) für den Mapping-Dialog."""
    need(user, "timetable.edit" if what in ("lessons", "curricula") else "masterdata.edit")
    from schulmanager.integrations.csv_io import describe
    return describe(what)


@router.post("/import/csv/{what}")
async def import_csv(what: CsvWhat, file: UploadFile = File(...), mapping: Optional[str] = Form(None),
                     dry_run: bool = Query(False), user: AuthUser = Depends(current_user)):
    """CSV-Import (z. B. aus SchILD-NRW/ASV). ``mapping`` = JSON ``{"Spalte in Datei": "feld"}``."""
    if what in ("lessons", "curricula"):
        need(user, "timetable.edit")
    else:
        need(user, "masterdata.edit")
    text = _decode(await _read_upload(file))
    mp: Optional[dict] = None
    if mapping:
        try:
            mp = json.loads(mapping)
        except json.JSONDecodeError:
            raise HTTPException(422, "mapping ist kein gültiges JSON") from None
        if not isinstance(mp, dict):
            raise HTTPException(422, "mapping muss ein JSON-Objekt sein")
    return await run_in_threadpool(_do_import_csv, user, what, text, mp, dry_run)


def curriculum_conflict_warnings(school: School, before: Optional[list[dict]] = None) -> list[str]:
    """Überschneidende Stundentafeln (``planning.curriculum_conflicts``) als Hinweise mit Klassenliste – mit
    ``before`` nur Überschneidungen, die es vorher nicht gab (Import soll sie melden, nicht still übernehmen)."""
    from schulmanager.planning import curriculum_conflicts
    known = {(tuple(g["curricula"]), tuple(g["classes"])) for g in before or []}
    names = {c.id: c.name for c in school.curricula}
    cls = {c.id: c.name for c in school.classes}
    return [f"Konflikt: für {', '.join(cls.get(x, x) for x in g['classes'])} gelten mehrere Stundentafeln "
            f"({' / '.join(names.get(i, i) for i in g['curricula'])}) – beim Kurse-Erzeugen bleiben ihre Kurse "
            "unverändert" for g in curriculum_conflicts(school)
            if (tuple(g["curricula"]), tuple(g["classes"])) not in known]


def _plan_tuple(cls) -> tuple:
    from .features_data import CLASS_PLAN_FIELDS
    return tuple(repr(getattr(cls, f)) for f in CLASS_PLAN_FIELDS)


def _class_plan_fields(school: School) -> dict[str, tuple]:
    """Planungsfelder je Klasse (``features_data.CLASS_PLAN_FIELDS``) für den Vergleich vor/nach einem Import."""
    return {c.id: _plan_tuple(c) for c in school.classes}


def _do_import_csv(user, what: str, text: str, mapping: Optional[dict], dry_run: bool) -> dict:
    from schulmanager.integrations.csv_io import import_csv as _import
    from schulmanager.planning import curriculum_conflicts
    from schulmanager.server.store import copy_school

    def run(school: School) -> dict:
        from .features_data import validate_item
        cache: dict = {}

        def validate(kind: str, obj) -> list[str]:   # gleiche Regeln wie die Oberfläche (POST/PUT /data)
            return validate_item(school, kind, obj, cache) if kind != "lessons" else []

        before = curriculum_conflicts(school)
        plan_before = _class_plan_fields(school)
        try:
            report = _import(school, what, text, mapping, validate)
        except (ValueError, KeyError) as exc:
            raise HTTPException(422, f"CSV-Import fehlgeschlagen: {exc}") from None
        if what == "classes" and not has(user, "timetable.edit"):   # R1: Planungsfelder nur mit timetable.edit
            from .features_data import PLAN_FIELDS_403
            default = _plan_tuple(COLLECTIONS["classes"]("", "", 0))
            if any(v != plan_before.get(k, default) for k, v in _class_plan_fields(school).items()):
                raise HTTPException(403, PLAN_FIELDS_403)
        report = dict(report or {})
        report["warnings"] = list(report.get("warnings") or []) + curriculum_conflict_warnings(school, before)
        report.setdefault("what", what)
        report["dry_run"] = dry_run
        return report

    if dry_run:
        return run(copy_school(snapshot()[1]))
    scope = ["timetable"] if what == "lessons" else [what]
    return mutate(user, f"CSV-Import {what}", run, scope=scope + ["import"])


@router.post("/import/json")
async def import_json(request: Request, dry_run: bool = Query(False),
                      user: AuthUser = Depends(require("timetable.edit", "masterdata.edit"))):
    """Komplettimport eines Planungsdokuments (JSON-Body oder Datei-Upload ``file``) – ersetzt alles."""
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/"):
        form = await request.form()
        f = form.get("file")
        if f is None or isinstance(f, str):
            raise HTTPException(422, "Datei „file“ fehlt")
        raw = await _read_upload(f)
    else:
        raw = await request.body()
        if len(raw) > MAX_UPLOAD:
            raise HTTPException(413, "Daten zu groß (maximal 50 MB)")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(422, "Ungültiges JSON") from None
    return await run_in_threadpool(_do_import_json, user, data, dry_run)


def json_integrity(school: School) -> list[str]:
    """Kurzprüfung eines importierten Dokuments (fehlende Referenzen)."""
    warnings = []
    ids = {name: {x.id for x in getattr(school, name)} for name in COLLECTIONS}
    for name in COLLECTIONS:
        seen: set = set()
        for x in getattr(school, name):
            if x.id in seen:
                warnings.append(f"{name}: doppelte ID {x.id}")
            seen.add(x.id)
    for s in school.students:
        if s.class_id not in ids["classes"]:
            warnings.append(f"Schüler/in {s.id}: Klasse {s.class_id} fehlt")
    for c in school.courses:
        for cid in c.classes:
            if cid not in ids["classes"]:
                warnings.append(f"Kurs {c.id}: Klasse {cid} fehlt")
        for p in c.parts:
            if p.teacher and p.teacher not in ids["teachers"]:
                warnings.append(f"Kurs {c.id}: Lehrkraft {p.teacher} fehlt")
            if p.subject not in ids["subjects"]:
                warnings.append(f"Kurs {c.id}: Fach {p.subject} fehlt")
    for le in school.lessons:
        if le.course_id not in ids["courses"]:
            warnings.append(f"Stunde {le.id}: Kurs {le.course_id} fehlt")
    return warnings[:200]


def _do_import_json(user, data: Any, dry_run: bool) -> dict:
    if isinstance(data, dict) and isinstance(data.get("school"), dict):
        data = data["school"]
    if not isinstance(data, dict) or not any(k in data for k in ("settings", *COLLECTIONS)):
        raise HTTPException(422, f"Kein {PRODUCT_NAME}-Planungsdokument")
    try:
        from pydantic import TypeAdapter
        new = TypeAdapter(School).validate_python(data)
        new = School.from_dict(new.to_dict())
    except (ValidationError, TypeError, ValueError, KeyError) as exc:
        raise HTTPException(422, f"Ungültiges Planungsdokument: {str(exc)[:500]}") from None
    warnings = json_integrity(new) + curriculum_conflict_warnings(new)
    current = snapshot()[1]
    labels = {"sites": "Standorte", "subjects": "Fächer", "teachers": "Lehrkräfte", "rooms": "Räume",
              "classes": "Klassen", "students": "Schüler/innen", "curricula": "Stundentafeln", "courses": "Kurse",
              "lessons": "Stunden", "absences": "Abwesenheiten", "overrides": "Vertretungen", "holidays": "Ferien",
              "areas": "Aufsichtsbereiche", "duties": "Aufsichten", "exams": "Klausuren"}
    missing = [name for name in COLLECTIONS if name not in data and getattr(current, name)]
    would_delete = {name: len(getattr(current, name)) for name in missing}
    danger = []
    if missing:
        danger.append("Die Datei enthält nur einen Teil des Planungsdokuments. Beim Import würden gelöscht: "
                      + ", ".join(f"{n} {labels.get(k, k)}" for k, n in would_delete.items()))
    if "settings" not in data:
        danger.append("Die Datei enthält keine Einstellungen – Zeitraster, Pausen und Regeln würden auf "
                      "Standardwerte zurückgesetzt")
    result = {"counts": _counts(new), "warnings": warnings, "dry_run": dry_run, "partial": bool(danger),
              "would_delete": would_delete, "danger": danger}
    if dry_run:
        return result

    def run(school: School) -> dict:
        _replace_all(school, new)
        return result

    return mutate(user, "JSON-Import (Planungsdokument ersetzt)", run, scope=["all", "import"])


# ===================================================================== iCal
def _ical_target(user, school: School, student: Optional[str]) -> tuple[str, str]:
    tid = getattr(user, "teacher_id", None)
    if tid and tid in school.index("teachers"):
        return "teacher", tid
    sids = own_student_ids(user)
    if sids:
        sid = student if student in sids else sids[0]
        if sid in school.index("students"):
            return "student", sid
    raise HTTPException(404, "Für dieses Konto gibt es keinen persönlichen Stundenplan")


@public_router.get("/ical/{token}.ics", include_in_schema=False)
def ical_feed(token: str, student: Optional[str] = None, days: int = Query(21, ge=1, le=62),
              db: Session = Depends(get_db)):
    """Persönlicher Kalender-Feed (Stundenplan inkl. Vertretungen) – Authentifizierung über geheimes Token."""
    from schulmanager.calendar_utils import school_days
    from schulmanager.integrations.ical import calendar

    user = user_from_ical_token(db, token)
    if user is None:
        raise HTTPException(404, "Kalender nicht gefunden")
    snap = snapshot()
    school = snap[1]
    kind, ref = _ical_target(user, school, student)
    d1 = date.today() - timedelta(days=7)
    d2 = date.today() + timedelta(days=days)
    plans = {}
    for d in school_days(school, d1, d2):
        _, plan = day_plan(d, snap)
        plans[d.isoformat()] = filter_plan(user, plan, snap)
    try:
        text = calendar(school, kind, ref, d1, d2, plans, name=f"{school.settings.school_name} – Stundenplan")
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from None
    return Response(content=text.encode("utf-8"), media_type="text/calendar; charset=utf-8",
                    headers={"Cache-Control": "private, max-age=300",
                             "Content-Disposition": f'inline; filename="stundenplan-{ref}.ics"'})


# ===================================================================== Outbox
@router.get("/notifications/outbox")
def outbox(status: Optional[Literal["pending", "sending", "sent", "failed"]] = None,
           limit: int = Query(100, ge=1, le=1000),
           user: AuthUser = Depends(require("settings.edit", "system.admin", any_of=True)),
           db: Session = Depends(get_db)):
    """Ausgehende Benachrichtigungen (Webhooks/E-Mails) mit Zustellstatus."""
    from schulmanager.server.db_models import NotificationOutbox as O
    q = select(O).order_by(O.id.desc()).limit(limit)
    if status:
        q = q.where(O.status == status)
    rows = db.scalars(q).all()
    counts = dict(db.execute(select(O.status, func.count(O.id)).group_by(O.status)).all())
    return {"counts": counts, "items": [
        {"id": r.id, "kind": r.kind, "target": r.target, "subject": r.subject, "status": r.status,
         "attempts": r.attempts, "next_attempt_at": iso(r.next_attempt_at), "last_error": r.last_error,
         "created_at": iso(r.created_at), "sent_at": iso(r.sent_at)} for r in rows]}


@router.post("/notifications/outbox/{item_id}/retry")
def outbox_retry(item_id: int, user: AuthUser = Depends(require("settings.edit", "system.admin", any_of=True)),
                 db: Session = Depends(get_db)):
    """Fehlgeschlagene Benachrichtigung erneut einplanen."""
    from schulmanager.server import notify
    from schulmanager.server.db_models import NotificationOutbox as O
    row = db.get(O, item_id)
    if row is None:
        raise HTTPException(404, "Eintrag nicht gefunden")
    if row.status == "sent":
        raise HTTPException(409, "Bereits zugestellt")
    row.status, row.next_attempt_at, row.attempts = "pending", utcnow(), 0
    db.commit()
    notify.kick()
    return {"id": row.id, "status": row.status}
