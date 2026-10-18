"""Import aus Fremdsystemen (Moodle, OneRoster, WebUntis, SchILD/ASV/IServ-Listen): Vorschau, Import, Protokoll, Rückgängig.

Rechte: ``masterdata.edit`` **und** ``channels.manage`` (ohne Einschränkung auf eigene Kurse) – der Import legt Personen,
Kursräume und Aufgaben an. Lehrkräfte (``channels.manage`` nur für eigene Kurse) und Sekretariat (kein Kursraum-Recht)
dürfen nicht importieren.

* ``GET  /import/fremd/systems`` – unterstützte Systeme und Datenarten (für Assistenten/Dialoge)
* ``POST /import/fremd/preview`` – Trockenlauf (Datei(en) als ``files``; ``system`` = ``auto`` oder Kennung; ``options`` = JSON)
* ``POST /import/fremd/run`` – echter Lauf (gleiche Parameter), Antwort = Bericht mit ``run_id``
* ``GET  /import/fremd/runs`` / ``GET /import/fremd/runs/{id}`` – Importprotokoll
* ``POST /import/fremd/runs/{id}/undo`` – Rückgängig
* ``GET  /export/oneroster.zip`` – Stammdaten als OneRoster-1.2-CSV

Doku für den Einrichtungsassistenten: ``docs/IMPORT-FREMDSYSTEME.md`` §2.
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from schulmanager.integrations.fremd import registry
from schulmanager.server import import_fremd as imp
from schulmanager.server.db import SessionLocal
from schulmanager.server.deps import AuthUser, current_user

from .features_common import has, perm_scope, snapshot
from .features_exchange import _download, _read_upload, _stamp

router = APIRouter(tags=["Import/Export"])

SYSTEM_INFO = [
    {"id": "moodle-db", "label": registry.SYSTEMS["moodle-db"], "accepts": [".sqlite", ".db"],
     "kinds": ["personen", "kursraeume", "gruppen", "aufgaben", "noten", "fragen", "kompetenzen", "abzeichen", "forum", "dateien"]},
    {"id": "moodle-mbz", "label": registry.SYSTEMS["moodle-mbz"], "accepts": [".mbz"],
     "kinds": ["personen", "kursraeume", "gruppen", "aufgaben", "dateien"]},
    {"id": "oneroster", "label": registry.SYSTEMS["oneroster"], "accepts": [".zip", ".csv"],
     "kinds": ["personen", "kursraeume", "noten"]},
    {"id": "webuntis", "label": registry.SYSTEMS["webuntis"], "accepts": [".json"], "kinds": ["personen"]},
    {"id": "csv", "label": registry.SYSTEMS["csv"], "accepts": [".csv", ".txt"], "kinds": ["personen"],
     "presets": ["schild-nrw", "asv", "lusd", "magellan"]},
]


def _need_import(user: AuthUser) -> None:
    if getattr(user, "role", "") == "zuschauer":        # Ansichtskonto: ändert nie, sieht keine Importprotokolle (Namen)
        raise HTTPException(403, "Keine Berechtigung")
    if not (has(user, "masterdata.edit") and has(user, "channels.manage")) or perm_scope(user, "channels.manage") is not None:
        raise HTTPException(403, "Keine Berechtigung")


def _import_user(user: AuthUser = Depends(current_user)) -> AuthUser:
    _need_import(user)
    return user


def _json(raw: Optional[str], what: str) -> Optional[dict]:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(422, f"{what} ist kein gültiges JSON") from None
    if not isinstance(data, dict):
        raise HTTPException(422, f"{what} muss ein JSON-Objekt sein")
    return data


async def _collect(files: list[UploadFile]) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for f in files:
        out[(f.filename or "upload").replace("\\", "/").rsplit("/", 1)[-1]] = await _read_upload(f)
    if not out:
        raise HTTPException(422, "Keine Datei erhalten")
    return out


def _work(user: AuthUser, files: dict[str, bytes], system: str, options: Optional[dict], mapping: Optional[dict],
          preset: str, prefix: str, dry_run: bool, request_ip: str) -> dict:
    opts = imp.Options.from_dict(options)
    try:
        bundle, detected = registry.read_bundle(files, system, instance=opts.instance, mapping=mapping, preset=preset,
                                                prefix=prefix or "mdl_")
    except StopIteration:
        raise HTTPException(422, "Keine passende Datei für dieses System gefunden") from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    import hashlib
    h = hashlib.sha256()
    for name in sorted(files):
        h.update(name.encode("utf-8"))
        h.update(files[name])
    db = SessionLocal()
    try:
        rep = imp.run_import(db, user, bundle, opts, dry_run=dry_run, source_name=", ".join(sorted(files))[:200],
                             source_hash=h.hexdigest())
        if not dry_run:
            db.commit()
        rep["detected"] = detected
        return rep
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/import/fremd/systems")
def fremd_systems(user: AuthUser = Depends(_import_user)) -> dict:
    """Unterstützte Quellsysteme, Dateiendungen und Datenarten (``parts`` der Optionen)."""
    return {"systems": SYSTEM_INFO, "parts": list(imp.PARTS),
            "options": ["instance", "create_missing_students", "create_missing_teachers", "default_class", "course_map",
                        "person_map", "include_hidden_courses", "publish", "parts", "only_courses", "update_existing"]}


@router.post("/import/fremd/preview")
async def fremd_preview(files: list[UploadFile] = File(...), system: str = Form("auto"), options: Optional[str] = Form(None),
                        mapping: Optional[str] = Form(None), preset: str = Form(""), prefix: str = Form("mdl_"),
                        user: AuthUser = Depends(_import_user)) -> dict:
    """Trockenlauf: zeigt, was angelegt/geändert würde und was unklar ist. Schreibt nichts."""
    data = await _collect(files)
    return await run_in_threadpool(_work, user, data, system, _json(options, "options"), _json(mapping, "mapping"),
                                   preset, prefix, True, "")


@router.post("/import/fremd/run")
async def fremd_run(request: Request, files: list[UploadFile] = File(...), system: str = Form("auto"),
                    options: Optional[str] = Form(None), mapping: Optional[str] = Form(None), preset: str = Form(""),
                    prefix: str = Form("mdl_"), user: AuthUser = Depends(_import_user)) -> dict:
    """Import ausführen. Antwort: Bericht mit ``run_id`` (für Protokoll und Rückgängig)."""
    data = await _collect(files)
    return await run_in_threadpool(_work, user, data, system, _json(options, "options"), _json(mapping, "mapping"),
                                   preset, prefix, False, "")


@router.get("/import/fremd/runs")
def fremd_runs(limit: int = 50, user: AuthUser = Depends(_import_user)) -> dict:
    db = SessionLocal()
    try:
        return {"runs": imp.list_runs(db, limit)}
    finally:
        db.close()


@router.get("/import/fremd/runs/{run_id}")
def fremd_run_detail(run_id: int, user: AuthUser = Depends(_import_user)) -> dict:
    from schulmanager.server.feature_models.import_fremd import ImportRun
    db = SessionLocal()
    try:
        row = db.get(ImportRun, run_id)
        if row is None:
            raise HTTPException(404, "Importlauf nicht gefunden")
        return imp.run_dict(row, with_report=True)
    finally:
        db.close()


@router.post("/import/fremd/runs/{run_id}/undo")
async def fremd_undo(run_id: int, user: AuthUser = Depends(_import_user)) -> dict:
    """Alles entfernen, was dieser Lauf neu angelegt hat (geänderte Daten bleiben)."""
    def work() -> dict:
        db = SessionLocal()
        try:
            res = imp.undo_run(db, user, run_id)
            db.commit()
            return res
        except imp.ImportError_ as exc:
            db.rollback()
            raise HTTPException(404 if "nicht gefunden" in str(exc) else 409, str(exc)) from None
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return await run_in_threadpool(work)


@router.get("/export/oneroster.zip")
def export_oneroster(user: AuthUser = Depends(current_user)):
    """Stammdaten (Schule, Klassen, Kurse, Personen, Einschreibungen, Geburtsdaten) als OneRoster-1.2-CSV-ZIP."""
    if not has(user, "students.read") or perm_scope(user, "students.read") is not None:
        raise HTTPException(403, "Keine Berechtigung")
    from schulmanager.integrations.fremd import oneroster
    from schulmanager.branding import PRODUCT_NAME
    snap = snapshot()
    data = oneroster.export_zip(snap[1], school_name=PRODUCT_NAME)
    return _download(data, f"oneroster-{_stamp()}.zip", "application/zip")
