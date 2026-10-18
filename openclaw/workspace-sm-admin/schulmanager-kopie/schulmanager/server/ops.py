"""Betrieb für die Administration (``docs/PRODUKTREIFE.md``, ``docs/BETRIEB.md``).

* Zustandsspeicher: :func:`get_state` / :func:`set_state` (Tabelle ``system_state``).
* Fehlerprotokoll: :func:`install_error_log` hängt einen Logging-Handler an, der ``ERROR``/``CRITICAL`` über eine
  Warteschlange und einen Hintergrund-Thread in ``error_log`` schreibt (der Handler blockiert nie – auch nicht, wenn die
  auslösende Anfrage selbst gerade eine Datenbanksperre hält). :func:`prune_error_log` räumt auf.
* Statusseite: :func:`status_report` (Version, Datenbankstand, Speicher, Mail, letzte Sicherung, Wartungslauf,
  Prüfliste) und :func:`verify_backup` (Test-Restore einer SQLite-Sicherung in eine Wegwerf-Kopie).
"""
from __future__ import annotations

import logging
import os
import queue
import shutil
import sqlite3
import tempfile
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select

from . import runtime
from .config import APP_VERSION, config
from .db import iso, session_scope, utcnow
from .feature_models.ops import ErrorLogEntry, SystemState
from .logging_setup import request_id_var

log = logging.getLogger("schulmanager.ops")

ERROR_LOG_KEEP_DAYS = 30
ERROR_LOG_KEEP_ROWS = 1000
_MESSAGE_MAX = 2000
_TRACE_MAX = 8000


# ---------------------------------------------------------------------------
# Zustandsspeicher
# ---------------------------------------------------------------------------
def get_state(key: str, default: Any = None) -> Any:
    with session_scope() as db:
        row = db.get(SystemState, key)
        return default if row is None or row.value is None else row.value


def set_state(key: str, value: Any, by: str | None = None) -> None:
    with session_scope() as db:
        row = db.get(SystemState, key)
        if row is None:
            db.add(SystemState(key=key, value=value, updated_at=utcnow(), updated_by=(by or "")[:80] or None))
        else:
            row.value = value
            row.updated_at = utcnow()
            row.updated_by = (by or "")[:80] or None


# ---------------------------------------------------------------------------
# Fehlerprotokoll
# ---------------------------------------------------------------------------
_queue: "queue.Queue[dict | None]" = queue.Queue(maxsize=500)
_worker: threading.Thread | None = None
_handler: logging.Handler | None = None


class ErrorLogHandler(logging.Handler):
    """Schreibt Fehler (ab ``ERROR``) ins Fehlerprotokoll – asynchron, nie blockierend, nie mit Folgefehlern."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)

    def emit(self, record: logging.LogRecord) -> None:
        if record.name.startswith(("schulmanager.ops", "sqlalchemy")):
            return  # keine Rückkopplung
        try:
            trace = None
            if record.exc_info:
                trace = "".join(traceback.format_exception(*record.exc_info))[-_TRACE_MAX:]
            item = {"level": record.levelname, "logger": record.name[:120],
                    "message": record.getMessage()[:_MESSAGE_MAX], "request_id": request_id_var.get(),
                    "trace": trace, "created_at": utcnow()}
            _queue.put_nowait(item)
        except Exception:  # noqa: BLE001 - Protokollierung darf nie selbst Fehler auslösen
            pass


def _write_item(item: dict) -> None:
    with session_scope() as db:
        db.add(ErrorLogEntry(level=item["level"], logger=item["logger"], message=item["message"],
                             request_id=(item.get("request_id") or None), trace=item.get("trace"),
                             created_at=item["created_at"]))


def _worker_loop() -> None:
    while True:
        item = _queue.get()
        if item is None:
            return
        try:
            _write_item(item)
        except Exception:  # noqa: BLE001 - Datenbank nicht erreichbar o. ä.: Eintrag verwerfen
            pass


def install_error_log() -> None:
    """Idempotent: Handler am Root-Logger und Schreib-Thread starten."""
    global _worker, _handler
    if _handler is None:
        _handler = ErrorLogHandler()
        logging.getLogger().addHandler(_handler)
    if _worker is None or not _worker.is_alive():
        _worker = threading.Thread(target=_worker_loop, name="sm-errorlog", daemon=True)
        _worker.start()


def flush_error_log(timeout: float = 3.0) -> None:
    """Wartet, bis die Warteschlange abgearbeitet ist (Tests, Herunterfahren)."""
    end = time.monotonic() + timeout
    while not _queue.empty() and time.monotonic() < end:
        time.sleep(0.02)
    time.sleep(0.05)


def record_error(message: str, *, logger: str = "schulmanager.manual", trace: str | None = None,
                 level: str = "ERROR") -> None:
    """Direkter Eintrag ins Fehlerprotokoll (synchron)."""
    _write_item({"level": level, "logger": logger[:120], "message": message[:_MESSAGE_MAX],
                 "request_id": request_id_var.get(), "trace": trace, "created_at": utcnow()})


def prune_error_log(now: datetime | None = None) -> int:
    """Einträge älter als 30 Tage und alles über 1000 Zeilen entfernen."""
    now = now or utcnow()
    with session_scope() as db:
        removed = db.execute(delete(ErrorLogEntry).where(
            ErrorLogEntry.created_at < now - timedelta(days=ERROR_LOG_KEEP_DAYS))).rowcount or 0
        total = db.scalar(select(func.count(ErrorLogEntry.id))) or 0
        if total > ERROR_LOG_KEEP_ROWS:
            cutoff = db.scalar(select(ErrorLogEntry.id).order_by(ErrorLogEntry.id.desc())
                               .offset(ERROR_LOG_KEEP_ROWS).limit(1))
            if cutoff is not None:
                removed += db.execute(delete(ErrorLogEntry).where(ErrorLogEntry.id <= cutoff)).rowcount or 0
    return removed


def list_errors(limit: int = 100, offset: int = 0, level: str | None = None) -> dict[str, Any]:
    with session_scope() as db:
        q = select(ErrorLogEntry)
        cq = select(func.count(ErrorLogEntry.id))
        if level:
            q, cq = q.where(ErrorLogEntry.level == level.upper()), cq.where(ErrorLogEntry.level == level.upper())
        rows = db.scalars(q.order_by(ErrorLogEntry.id.desc()).offset(offset).limit(limit)).all()
        total = db.scalar(cq) or 0
        return {"total": total, "items": [
            {"id": r.id, "created_at": iso(r.created_at), "level": r.level, "logger": r.logger,
             "message": r.message, "request_id": r.request_id, "trace": r.trace} for r in rows]}


def clear_errors() -> int:
    with session_scope() as db:
        return db.execute(delete(ErrorLogEntry)).rowcount or 0


# ---------------------------------------------------------------------------
# Wartungslauf merken
# ---------------------------------------------------------------------------
def record_maintenance(result: dict[str, int]) -> None:
    try:
        set_state("maintenance", {"at": iso(utcnow()), "deleted": int(sum(v for v in result.values()
                                                                          if isinstance(v, int)))})
    except Exception:  # noqa: BLE001
        log.debug("Wartungslauf konnte nicht vermerkt werden", exc_info=True)


# ---------------------------------------------------------------------------
# Statusseite
# ---------------------------------------------------------------------------
_size_cache: dict[str, tuple[float, int]] = {}


def dir_size(path: Path, ttl: float = 60.0) -> int:
    """Gesamtgröße eines Verzeichnisses in Bytes (kurz zwischengespeichert, Fehler → 0)."""
    key = str(path)
    hit = _size_cache.get(key)
    if hit and time.monotonic() - hit[0] < ttl:
        return hit[1]
    total = 0
    try:
        for root, _dirs, files in os.walk(path):
            for name in files:
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
    except OSError:
        total = 0
    _size_cache[key] = (time.monotonic(), total)
    return total


def _check(key: str, label: str, level: str, detail: str) -> dict[str, str]:
    return {"key": key, "label": label, "level": level, "detail": detail}


def status_report() -> dict[str, Any]:
    """Alles für die Statusseite der Administration. Keine Geheimnisse (nur Schlüssel-IDs/Fingerabdrücke)."""
    from . import crypto, licensing, migrate
    from .backups import list_backups
    from .db_models import NotificationOutbox, User
    from .store import get_store

    now = utcnow()
    try:
        current, head = migrate.current_revision(), migrate.head_revision()
        db_ok = True
    except Exception:  # noqa: BLE001
        log.exception("Statusseite: Datenbankstand nicht lesbar")
        current = head = None
        db_ok = False
    migrated = db_ok and migrate.check_up_to_date()

    data_dir = Path(config.data_dir)
    probe = data_dir if data_dir.exists() else Path(".")
    try:
        usage = shutil.disk_usage(probe)
        disk = {"total": usage.total, "used": usage.used, "free": usage.free,
                "free_percent": round(usage.free * 100 / usage.total, 1) if usage.total else None}
    except OSError:
        disk = {"total": None, "used": None, "free": None, "free_percent": None}
    db_file = None
    if config.db_kind == "sqlite":
        from .backups import _sqlite_file  # noqa: PLC0415

        path = _sqlite_file()
        if path and path != ":memory:" and os.path.exists(path):
            db_file = os.path.getsize(path)
    files_bytes = dir_size(Path(config.files_dir))
    backups = list_backups()
    last_backup = backups[0] if backups else None

    with session_scope() as db:
        pending = db.scalar(select(func.count(NotificationOutbox.id)).where(
            NotificationOutbox.kind == "email", NotificationOutbox.status.in_(("pending", "sending")))) or 0
        failed = db.scalar(select(func.count(NotificationOutbox.id)).where(
            NotificationOutbox.kind == "email", NotificationOutbox.status == "failed")) or 0
        last_sent = db.scalar(select(func.max(NotificationOutbox.sent_at)).where(
            NotificationOutbox.kind == "email", NotificationOutbox.status == "sent"))
        admins = db.scalar(select(func.count(User.id)).where(User.role == "admin", User.active.is_(True))) or 0
        errors_24h = db.scalar(select(func.count(ErrorLogEntry.id)).where(
            ErrorLogEntry.created_at > now - timedelta(hours=24))) or 0
        errors_total = db.scalar(select(func.count(ErrorLogEntry.id))) or 0
    maintenance = get_state("maintenance") or {}
    lic = licensing.status()
    ring = crypto.describe()
    school = get_store().school

    checks: list[dict[str, str]] = []
    checks.append(_check("db", "Datenbank", "ok" if db_ok else "error",
                         "erreichbar" if db_ok else "nicht erreichbar – siehe Fehlerprotokoll"))
    checks.append(_check("migration", "Datenbankstand", "ok" if migrated else "warn",
                         "aktuell" if migrated else
                         f"Schema nicht aktuell ({current or 'leer'} → {head}); `scripts/migrate.sh` ausführen"))
    if disk["free_percent"] is not None:
        lvl = "ok" if disk["free_percent"] >= 15 else ("warn" if disk["free_percent"] >= 5 else "error")
        checks.append(_check("disk", "Speicherplatz", lvl, f"{disk['free_percent']} % frei"))
    if last_backup is None:
        checks.append(_check("backup", "Sicherung", "warn" if config.is_production_mode else "ok",
                             "Noch keine App-Sicherung vorhanden – täglichen Backup-Lauf einrichten"))
    else:
        age_h = (now - datetime.fromisoformat(last_backup["created_at"].replace("Z", ""))).total_seconds() / 3600
        checks.append(_check("backup", "Sicherung", "ok" if age_h <= 48 else "warn",
                             f"letzte vor {int(age_h)} Stunden ({last_backup['name']})"))
    if config.dev_outbox:
        checks.append(_check("mail", "E-Mail-Versand", "warn", "Test-Postausgang aktiv – Mails werden nicht zugestellt"))
    elif not config.smtp_enabled:
        checks.append(_check("mail", "E-Mail-Versand", "warn", "nicht eingerichtet (SM_SMTP_HOST/SM_SMTP_FROM)"))
    elif failed:
        checks.append(_check("mail", "E-Mail-Versand", "warn", f"{failed} Mails nicht zustellbar"))
    else:
        checks.append(_check("mail", "E-Mail-Versand", "ok", "eingerichtet"))
    checks.append(_check("encryption", "Verschlüsselung", "ok" if ring["source"] != "derived" else "warn",
                         "Schlüssel aus SM_ENCRYPTION_KEYS" if ring["source"] != "derived"
                         else "abgeleiteter Entwicklungsschlüssel – für echte Daten SM_ENCRYPTION_KEYS setzen"))
    checks.append(_check("license", "Lizenz", "ok" if (lic.get("state") in ("valid", "grace") or not lic.get("enforced"))
                         else "error", str(lic.get("message") or lic.get("state") or "")))
    checks.append(_check("maintenance", "Wartungslauf", "ok" if maintenance.get("at") else "warn",
                         f"letzter Lauf {maintenance['at']}" if maintenance.get("at") else "noch nicht gelaufen"))
    checks.append(_check("errors", "Fehlerprotokoll", "ok" if errors_24h == 0 else "warn",
                         "keine Fehler in den letzten 24 Stunden" if errors_24h == 0
                         else f"{errors_24h} Fehler in den letzten 24 Stunden"))
    checks.append(_check("https", "HTTPS", "ok" if config.base_url.startswith("https://") and config.cookie_secure
                         else "warn", "Adresse und Cookie gesichert" if config.base_url.startswith("https://")
                         else "SM_BASE_URL ohne https://"))
    if config.is_production_mode and not config.require_2fa_roles:
        checks.append(_check("2fa", "Zwei-Faktor", "warn", "für Administration/Schulleitung nicht erzwungen "
                                                          "(SM_REQUIRE_2FA_ROLES)"))
    if admins == 0:
        checks.append(_check("admin", "Administration", "error", "kein aktives Administrationskonto"))

    return {
        "version": APP_VERSION, "mode": config.mode, "env": config.env, "school_name": school.settings.school_name,
        "uptime_seconds": round(time.time() - runtime.started_at, 1), "generated_at": iso(now),
        "database": {"kind": config.db_kind, "revision": current, "head": head, "up_to_date": migrated,
                     "file_bytes": db_file},
        "storage": {"disk": disk, "files_bytes": files_bytes, "backups_bytes": dir_size(Path(config.backup_dir)),
                    "data_dir": str(config.data_dir)},
        "mail": {"smtp": config.smtp_enabled, "dev_outbox": config.dev_outbox, "pending": pending, "failed": failed,
                 "last_sent": iso(last_sent)},
        "backup": {"count": len(backups), "last": last_backup, "auto_hours": config.auto_backup_hours,
                   "keep": config.backup_keep},
        "maintenance": {"last": maintenance.get("at"), "interval_seconds": config.maintenance_interval},
        "encryption": {"source": ring["source"], "active": ring["active"], "keys": [
            {"id": kid, "fingerprint": ring["fingerprints"].get(kid)} for kid in ring["key_ids"]]},
        "license": {k: lic.get(k) for k in ("state", "enforced", "message", "read_only")},
        "errors": {"last_24h": errors_24h, "total": errors_total},
        "checks": checks,
        "ok": all(c["level"] != "error" for c in checks),
    }


# ---------------------------------------------------------------------------
# Test-Restore
# ---------------------------------------------------------------------------
def verify_backup(name: str) -> dict[str, Any]:
    """Prüft eine App-Sicherung, ohne die Live-Daten anzufassen: SQLite-Datei in eine temporäre Kopie, ``PRAGMA
    integrity_check``, Tabellen- und Zeilenzahlen, Planversionen, Datenbank-Revision. JSON-Sicherungen werden
    entpackt und auf Format/Tabellen geprüft."""
    import gzip
    import json

    from .backups import backup_path

    path = backup_path(name)
    if path is None:
        raise FileNotFoundError(name)
    started = time.monotonic()
    result: dict[str, Any] = {"name": name, "size": path.stat().st_size, "ok": False, "tables": {}}
    if name.endswith(".db"):
        with tempfile.TemporaryDirectory(prefix="sm-restore-test-") as tmp:
            copy = Path(tmp) / "restore.db"
            shutil.copyfile(path, copy)
            conn = sqlite3.connect(str(copy))
            try:
                check = conn.execute("PRAGMA integrity_check").fetchone()
                result["integrity"] = check[0] if check else "unbekannt"
                tables = [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                for t in tables:
                    result["tables"][t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]  # noqa: S608
                rev = None
                if "alembic_version" in tables:
                    rev = ",".join(sorted(r[0] for r in conn.execute("SELECT version_num FROM alembic_version")))
                result["revision"] = rev
            finally:
                conn.close()
        result["ok"] = (result.get("integrity") == "ok" and result["tables"].get("users", 0) > 0
                        and result["tables"].get("school_versions", 0) > 0)
    else:
        try:
            with gzip.open(path, "rb") as fh:
                data = json.loads(fh.read().decode("utf-8"))
        except (OSError, ValueError) as exc:
            result["integrity"] = f"nicht lesbar: {exc}"
            return result
        result["integrity"] = "ok" if data.get("format") == "schulmanager-backup" else "unbekanntes Format"
        result["tables"] = {t: len(rows) for t, rows in (data.get("tables") or {}).items()}
        result["ok"] = (result["integrity"] == "ok" and result["tables"].get("users", 0) > 0
                        and bool((data.get("school") or {}).get("data")))
        result["revision"] = None
    result["seconds"] = round(time.monotonic() - started, 2)
    result["users"] = result["tables"].get("users")
    result["plan_versions"] = result["tables"].get("school_versions")
    return result
