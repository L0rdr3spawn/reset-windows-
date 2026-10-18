"""Formaterkennung und Einstieg für alle Fremdsystem-Leser.

``detect(files)`` rät das Format aus Dateinamen und Inhalt, ``read_bundle(files, system)`` ruft den passenden Leser auf.
``files`` ist ein Dict ``{Dateiname: Bytes}`` (ein ZIP wird vorher entpackt, siehe :func:`expand_zip`).
"""
from __future__ import annotations

import io
import json
import os
import tempfile
import zipfile
from typing import Optional

from .model import Bundle

SYSTEMS = {
    "moodle-db": "Moodle – Datenbank (SQLite-Abzug)",
    "moodle-mbz": "Moodle – Kurssicherung (.mbz)",
    "oneroster": "OneRoster 1.2 – CSV (ZIP oder Einzeldateien)",
    "webuntis": "WebUntis – JSON (REST/JSON-RPC-Antworten)",
    "csv": "Personenlisten (SchILD-NRW, ASV-BW/BY, LUSD, IServ, Magellan, eigenes Mapping)",
}
MAX_ZIP_FILES = 500
MAX_ZIP_BYTES = 400 * 1024 * 1024
ONEROSTER_FILES = {"manifest.csv", "orgs.csv", "users.csv", "classes.csv", "courses.csv", "enrollments.csv",
                   "academicsessions.csv", "demographics.csv", "lineitems.csv", "results.csv", "categories.csv",
                   "resources.csv", "classresources.csv", "coursesresources.csv"}


def expand_zip(name: str, data: bytes, *, max_files: int = MAX_ZIP_FILES, max_bytes: int = MAX_ZIP_BYTES) -> dict[str, bytes]:
    """ZIP → ``{Pfad: Bytes}`` mit Grenzen (ZIP-Bomben, Pfade mit ``..`` werden abgelehnt)."""
    out: dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if len(infos) > max_files:
            raise ValueError("Zu viele Dateien im ZIP")
        for i in infos:
            n = i.filename.replace("\\", "/")
            if n.startswith("/") or ".." in n.split("/"):
                raise ValueError(f"Unzulässiger Pfad im ZIP: {n}")
            total += i.file_size
            if total > max_bytes:
                raise ValueError("ZIP-Inhalt zu groß")
            out[n] = zf.read(i)
    return out


def detect(files: dict[str, bytes]) -> str:
    names = {n.rsplit("/", 1)[-1].lower(): n for n in files}
    for n, data in files.items():
        if data[:16].startswith(b"SQLite format 3"):
            return "moodle-db"
        if n.lower().endswith(".mbz") or (data[:2] == b"\x1f\x8b" and n.lower().endswith((".tar.gz", ".gz"))):
            return "moodle-mbz"
    if "moodle_backup.xml" in names:
        return "moodle-mbz"
    if ONEROSTER_FILES & set(names) and ("users.csv" in names or "manifest.csv" in names):
        return "oneroster"
    for n, data in files.items():
        if n.lower().endswith(".json"):
            try:
                doc = json.loads(data.decode("utf-8-sig"))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(doc, dict) and ("webuntis" in json.dumps(list(doc)[:20]).lower() or "result" in doc
                                          or any(k in doc for k in ("teachers", "klassen", "students", "subjects"))):
                return "webuntis"
            if isinstance(doc, list) and doc and isinstance(doc[0], dict) and "longName" in doc[0]:
                return "webuntis"
    if any(n.lower().endswith((".csv", ".txt")) for n in files):
        return "csv"
    return ""


def read_bundle(files: dict[str, bytes], system: str = "auto", *, instance: str = "standard",
                mapping: Optional[dict] = None, preset: str = "", prefix: str = "mdl_") -> tuple[Bundle, str]:
    """Liest ``files`` und gibt ``(Bundle, erkanntes System)`` zurück. Wirft ``ValueError`` bei unbekanntem Format."""
    # ZIPs auspacken (außer .mbz, das selbst ein Archiv ist)
    flat: dict[str, bytes] = {}
    for n, d in files.items():
        if d[:4] == b"PK\x03\x04" and not n.lower().endswith(".mbz") and not n.lower().endswith(".docx"):
            try:
                flat.update(expand_zip(n, d))
            except (zipfile.BadZipFile, ValueError) as exc:
                raise ValueError(f"ZIP nicht lesbar: {exc}") from None
        else:
            flat[n] = d
    files = flat
    chosen = detect(files) if system in ("", "auto") else system
    if chosen == "moodle-db":
        from .moodle_db import read_moodle_db
        name, data = next((n, d) for n, d in files.items() if d[:16].startswith(b"SQLite format 3"))
        fd, path = tempfile.mkstemp(suffix=".sqlite")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            b = read_moodle_db(path, prefix=prefix, instance=instance)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        b.source = name.rsplit("/", 1)[-1]
        return b, chosen
    if chosen == "moodle-mbz":
        from .moodle_mbz import read_moodle_mbz
        name, data = next(((n, d) for n, d in files.items() if n.lower().endswith((".mbz", ".gz", ".tgz"))),
                          next(iter(files.items())))
        return read_moodle_mbz(data, name=name, instance=instance), chosen
    if chosen == "oneroster":
        from .oneroster import read_oneroster
        return read_oneroster(files, instance=instance), chosen
    if chosen == "webuntis":
        from .webuntis import read_webuntis
        return read_webuntis(files, instance=instance), chosen
    if chosen == "csv":
        from .csv_persons import read_csv_persons
        return read_csv_persons(files, instance=instance, mapping=mapping, preset=preset), chosen
    raise ValueError("Format nicht erkannt – bitte das System auswählen")
