"""Start/Stopp der Laufzeit: Migration, Bootstrap, Hintergrundaufgaben.

``ensure_started()`` ist idempotent und wird vom Lifespan sowie lazily von ``get_db``/``get_store``
aufgerufen (damit funktionieren auch ``TestClient(app)`` ohne Kontextmanager).
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import threading
import time

from .config import config

log = logging.getLogger("schulmanager.runtime")

_lock = threading.RLock()
_started = False
_starting_thread: int | None = None
started_at: float = time.time()
_maintenance_task: asyncio.Task | None = None
_optional_hooks_started = False


def ensure_started() -> None:
    """Migration + Bootstrap (Erst-Admin, Planungsdokument, ggf. Demo). Idempotent und thread-sicher."""
    global _started, _starting_thread, started_at
    if _started:
        return
    with _lock:
        if _started or _starting_thread == threading.get_ident():
            return
        _starting_thread = threading.get_ident()
        try:
            from . import bootstrap, migrate
            from .db import get_engine

            config.validate()
            get_engine()
            if config.auto_migrate:
                migrate.upgrade_head()
            elif not migrate.check_up_to_date():
                log.error("Datenbankschema ist nicht aktuell – bitte `alembic upgrade head` ausführen "
                          "(SM_AUTO_MIGRATE=0)")
            bootstrap.run()
            from . import chat_migration

            chat_migration.run_startup()      # alte Postfach-Gruppen/-Chats → „Chats & Gruppen“ (idempotent)
            started_at = time.time()
            _started = True
        finally:
            _starting_thread = None


def is_started() -> bool:
    return _started


def reset() -> None:
    """Setzt den Laufzeitzustand zurück (neue App-Instanz / Tests)."""
    global _started
    from .events import bus
    from .store import reset_store

    with _lock:
        _started = False
        reset_store()
        bus.clear()


def optional_module(name: str):
    """Importiert ``schulmanager.server.<name>``, falls vorhanden (sonst ``None``)."""
    try:
        return importlib.import_module(f"schulmanager.server.{name}")
    except ModuleNotFoundError as exc:
        if exc.name == f"schulmanager.server.{name}":
            return None
        log.exception("Modul %s konnte nicht geladen werden", name)
    except Exception:  # noqa: BLE001
        log.exception("Modul %s konnte nicht geladen werden", name)
    return None


def _call_hook(module_name: str, func: str) -> None:
    mod = optional_module(module_name)
    fn = getattr(mod, func, None) if mod else None
    if callable(fn):
        try:
            fn()
        except Exception:  # noqa: BLE001
            log.exception("%s.%s() fehlgeschlagen", module_name, func)


async def startup() -> None:
    """Lifespan-Start: Initialisierung im Thread (blockiert den Loop nicht), dann Hintergrundaufgaben."""
    global _maintenance_task, _optional_hooks_started
    await asyncio.to_thread(ensure_started)
    try:  # Threadpool der synchronen Endpunkte (passend zum Datenbank-Pool, siehe db.build_engine)
        import anyio.to_thread
        anyio.to_thread.current_default_thread_limiter().total_tokens = config.threadpool
    except Exception:  # noqa: BLE001
        log.warning("Threadpool-Größe konnte nicht gesetzt werden")
    _call_hook("ops", "install_error_log")       # Fehlerprotokoll für die Administration (/admin/errors)
    _call_hook("licensing", "start")
    _call_hook("update_state", "record_startup")   # UPDATES-HA: Versionswechsel ins Audit-Protokoll
    optional_module("routes.features_mail")      # setzt mailbridge.sync_hook
    _optional_hooks_started = True
    # >>> UPDATES-HA: bei SM_HA=1 laufen die folgenden Jobs nur auf dem Leader-Knoten (leader.py), sonst wie bisher
    if config.ha:
        from . import leader

        leader.start(start_leader_jobs, stop_leader_jobs)
        if config.maintenance_interval > 0:
            _maintenance_task = asyncio.create_task(_ha_maintenance(), name="sm-maintenance-ha")
    else:
        start_leader_jobs()
        if config.maintenance_interval > 0:
            from .maintenance import maintenance_loop

            _maintenance_task = asyncio.create_task(maintenance_loop(), name="sm-maintenance")
    # <<< UPDATES-HA


# >>> UPDATES-HA
_LEADER_JOBS = (("notify", "start_dispatcher", "stop_dispatcher"), ("autoplan", "start", "stop"),
                ("mailbridge", "start", "stop"), ("holiday_import", "start", "stop"))


def start_leader_jobs() -> None:
    """Hintergrundjobs, die nur auf einem Knoten laufen dürfen."""
    for module, start, _stop in _LEADER_JOBS:
        _call_hook(module, start)


def stop_leader_jobs() -> None:
    for module, _start, stop in _LEADER_JOBS:
        _call_hook(module, stop)


async def _ha_maintenance() -> None:
    """Wartungsschleife nur, solange dieser Knoten Leader ist."""
    from . import leader
    from .maintenance import maintenance_loop

    task: asyncio.Task | None = None
    try:
        while True:
            if leader.is_leader() and task is None:
                task = asyncio.create_task(maintenance_loop(), name="sm-maintenance")
            elif not leader.is_leader() and task is not None:
                task.cancel()
                task = None
            await asyncio.sleep(5)
    finally:
        if task is not None:
            task.cancel()
# <<< UPDATES-HA


async def shutdown() -> None:
    global _maintenance_task, _optional_hooks_started
    from .events import bus

    if _maintenance_task is not None:
        _maintenance_task.cancel()
        try:
            await _maintenance_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        _maintenance_task = None
    if _optional_hooks_started:
        if config.ha:                                    # UPDATES-HA: Pacht freigeben, Jobs stoppen
            from . import leader

            await asyncio.to_thread(leader.stop)
        await asyncio.to_thread(stop_leader_jobs)
        await asyncio.to_thread(_call_hook, "jobs", "shutdown")
        _optional_hooks_started = False
    bus.clear()
