"""Sicherungen nach ``config.backup_dir`` (Default ``data/backups``).

* SQLite: konsistente Kopie über die SQLite-Backup-API → ``schulmanager-YYYYmmdd-HHMMSS.db``
* sonst (PostgreSQL): JSON-Export aller Tabellen + aktuelles Planungsdokument →
  ``schulmanager-YYYYmmdd-HHMMSS.json.gz`` (für vollständige PG-Sicherungen zusätzlich ``pg_dump``,
  siehe Infrastruktur-Sidecar).
Rotation: ``SM_BACKUP_KEEP`` (Default 30) neueste Dateien bleiben erhalten.
"""
from __future__ import annotations

import base64
import gzip
import json
import logging
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import make_url

from .config import config
from .db import Base, get_engine, normalize_url, session_scope

log = logging.getLogger("schulmanager.backups")

NAME_RE = re.compile(r"^schulmanager-(\d{8}-\d{6})(?:-(\d+))?\.(?:db|json\.gz)$")


def _sort_key(name: str) -> tuple[str, int]:
    m = NAME_RE.match(name)
    return (m.group(1), int(m.group(2) or 1)) if m else ("", 0)
_lock = threading.Lock()


def backup_dir() -> Path:
    path = Path(config.backup_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_backups() -> list[dict[str, Any]]:
    path = Path(config.backup_dir)
    if not path.exists():
        return []
    out = []
    for f in path.iterdir():
        if f.is_file() and NAME_RE.match(f.name):
            st = f.stat()
            out.append({"name": f.name, "size": st.st_size,
                        "created_at": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds")
                        .replace("+00:00", "Z"),
                        "kind": "sqlite" if f.name.endswith(".db") else "json"})
    out.sort(key=lambda b: _sort_key(b["name"]), reverse=True)
    return out


def backup_path(name: str) -> Path | None:
    """Pfad einer Sicherung oder ``None`` (Name wird streng geprüft → kein Path-Traversal)."""
    if not NAME_RE.match(name):
        return None
    path = Path(config.backup_dir) / name
    return path if path.is_file() else None


def _target(ext: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    directory = backup_dir()
    path = directory / f"schulmanager-{stamp}.{ext}"
    n = 1
    while path.exists():
        n += 1
        path = directory / f"schulmanager-{stamp}-{n}.{ext}"
    return path


def _sqlite_file() -> str | None:
    url = make_url(normalize_url(config.database_url))
    if url.get_backend_name() != "sqlite":
        return None
    return url.database or None


def _jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"$b64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def export_tables() -> dict[str, Any]:
    """Alle Tabellen als JSON-kompatibles Dict (Planversionen ohne Binärdaten außer der aktuellen)."""
    from .store import get_store

    out: dict[str, Any] = {"format": "schulmanager-backup", "version": 1,
                           "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tables": {}}
    with get_engine().connect() as conn:
        for table in Base.metadata.sorted_tables:
            rows = []
            for row in conn.execute(select(table)).mappings():
                item = {k: _jsonable(v) for k, v in row.items()}
                if table.name == "school_versions":
                    item.pop("data", None)
                rows.append(item)
            out["tables"][table.name] = rows
    store = get_store()
    out["school"] = {"version": store.version, "data": store.school.to_dict()}
    return out


def create_backup(user: Any = None, ip: str | None = None) -> dict[str, Any]:
    """Erstellt eine Sicherung und rotiert alte. Gibt ``{name, size, kind}`` zurück."""
    with _lock:
        src = _sqlite_file()
        if src and src != ":memory:":
            target = _target("db")
            source = sqlite3.connect(src, timeout=30)
            dest = sqlite3.connect(str(target))
            try:
                source.backup(dest)
            finally:
                dest.close()
                source.close()
            kind = "sqlite"
        else:
            target = _target("json.gz")
            data = json.dumps(export_tables(), ensure_ascii=False, default=str).encode("utf-8")
            with gzip.open(target, "wb") as fh:
                fh.write(data)
            kind = "json"
        try:
            target.chmod(0o600)
        except OSError:
            pass
        size = target.stat().st_size
        rotate()
    log.info("Sicherung erstellt: %s (%d Bytes)", target.name, size)
    with session_scope() as db:
        from .audit import audit

        audit(db, user, "system.backup", target.name, {"size": size, "kind": kind}, ip=ip)
    return {"name": target.name, "size": size, "kind": kind}


def rotate(keep: int | None = None) -> list[str]:
    keep = config.backup_keep if keep is None else keep
    removed = []
    if keep <= 0:
        return removed
    for item in list_backups()[keep:]:
        try:
            (Path(config.backup_dir) / item["name"]).unlink()
            removed.append(item["name"])
        except OSError:
            log.warning("Alte Sicherung %s konnte nicht gelöscht werden", item["name"])
    return removed


def delete_backup(name: str) -> bool:
    path = backup_path(name)
    if path is None:
        return False
    path.unlink()
    return True
