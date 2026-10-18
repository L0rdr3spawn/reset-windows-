"""Versioniertes Planungsdokument (``School``) mit In-Memory-Arbeitskopie.

* ``store.school`` – aktuelles Dokument, **nur lesen** (wird bei Änderungen als Ganzes ersetzt,
  Leser behalten daher immer einen konsistenten Stand).
* ``store.mutate(user, "Nachricht", fn, scope=[...], dates=[...])`` – ``fn`` bekommt eine tiefe Kopie
  und darf sie verändern; Exceptions (auch ``HTTPException``) werden unverändert weitergeworfen und
  verwerfen die Änderung. Danach: neue Version in ``school_versions``, Audit-Eintrag ``plan.change``,
  Event ``change`` ``{version, scope, dates}``. Rückgabe = Rückgabewert von ``fn``.
  Ist das Ergebnis identisch mit dem aktuellen Stand, wird keine Version angelegt.
* ``history``, ``get_version``, ``restore``, ``undo``, ``replace`` (Import/Demo).
* Aufbewahrung: ``SM_KEEP_VERSIONS`` (Default 300), die ältesten Versionen werden gelöscht.

Thread-sicher (RLock); für Sync-Handler gedacht (``def``-Endpunkte laufen im Threadpool).
Mehrere Server-Prozesse: Vor jeder Änderung und höchstens alle 2 s beim Lesen über
:func:`get_store` wird ein neuerer Stand aus der Datenbank nachgeladen (empfohlen bleibt 1 Worker).
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
import zlib
from datetime import datetime
from typing import Any, Callable, TypeVar

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..models import School
from .audit import audit
from .config import config
from .db import SessionLocal, iso, utcnow
from .db_models import SchoolVersion, User
from .events import bus

log = logging.getLogger("schulmanager.store")

T = TypeVar("T")
SYNC_INTERVAL = 2.0


def encode_school(school: School) -> tuple[bytes, str]:
    """``School`` → (zlib-JSON, SHA-256 des JSON)."""
    raw = json.dumps(school.to_dict(), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return zlib.compress(raw, 6), hashlib.sha256(raw).hexdigest()


def decode_school(data: bytes) -> School:
    return School.from_dict(json.loads(zlib.decompress(data).decode("utf-8")))


def copy_school(school: School) -> School:
    """Tiefe Kopie über das verlustfreie Dict-Format."""
    return School.from_dict(school.to_dict())


class StoreError(Exception):
    """Fehler bei Verlauf/Wiederherstellung (z. B. Version existiert nicht)."""


class SchoolStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.school: School = School()
        self.version: int = 0
        self.updated_at: datetime | None = None
        self._digest: str = ""
        self._last_sync = 0.0
        self.loaded = False

    # ------------------------------------------------------------------ Laden
    def load(self) -> None:
        """Lädt die neueste Version; legt bei leerer Tabelle ein leeres Dokument an."""
        with self._lock:
            with SessionLocal() as db:
                rows = db.scalars(select(SchoolVersion).order_by(SchoolVersion.id.desc()).limit(5)).all()
                for row in rows:
                    try:
                        school = decode_school(row.data)
                    except Exception:  # noqa: BLE001
                        log.exception("Version %s ist beschädigt – versuche ältere", row.id)
                        continue
                    self._set(school, row.id, row.created_at)
                    break
                else:
                    if rows:
                        log.error("Keine lesbare Version gefunden – starte mit leerem Dokument")
                    self._save(db, None, "Leeres Planungsdokument angelegt", School(), ["all", "init"], None,
                               "plan.init")
            self.loaded = True
            self._last_sync = time.monotonic()

    def _set(self, school: School, version: int, created_at: datetime | None) -> None:
        self.school = school
        self.version = version
        self.updated_at = created_at
        self._digest = encode_school(school)[1]

    def sync(self, force: bool = False) -> bool:
        """Lädt einen neueren Stand aus der DB (anderer Prozess). ``True`` wenn neu geladen."""
        now = time.monotonic()
        if not force and now - self._last_sync < SYNC_INTERVAL:
            return False
        with self._lock:
            self._last_sync = now
            with SessionLocal() as db:
                latest = db.scalar(select(func.max(SchoolVersion.id)))
                if latest is None or latest == self.version:
                    return False
                row = db.get(SchoolVersion, latest)
                if row is None:
                    return False
                self._set(decode_school(row.data), row.id, row.created_at)
                log.info("Planungsdokument Version %s aus der Datenbank nachgeladen", row.id)
                return True

    # ------------------------------------------------------------------ Schreiben
    def _save(self, db: Session, user: Any, message: str, school: School, scope: list[str],
              restored_from: int | None, action: str, details: dict | None = None,
              encoded: tuple[bytes, str] | None = None) -> int:
        data, digest = encoded or encode_school(school)
        uid = getattr(user, "id", None) or None
        if config.ha:        # UPDATES-HA: mehrere Knoten schreiben in dieselbe Datenbank – Verlorene Änderungen verhindern
            if db.get_bind().dialect.name == "postgresql":
                db.execute(text("SELECT pg_advisory_xact_lock(7305001)"))      # ein Schreiber zur Zeit, bis zum Commit
            latest = db.scalar(select(func.max(SchoolVersion.id)))
            if latest is not None and latest != self.version:
                raise StoreError("Der Plan wurde inzwischen auf einem anderen Server geändert. Bitte erneut versuchen.")
        row = SchoolVersion(user_id=uid, message=message[:500], scope=list(scope), data=data,
                            restored_from=restored_from, created_at=utcnow())
        db.add(row)
        db.flush()
        audit(db, user, action, f"version:{row.id}", {"message": message, "scope": list(scope), **(details or {})})
        db.commit()
        self._prune(db)
        self.school, self.version, self.updated_at, self._digest = school, row.id, row.created_at, digest
        return row.id

    def _prune(self, db: Session) -> None:
        keep = config.keep_versions
        old_ids = db.scalars(select(SchoolVersion.id).order_by(SchoolVersion.id.desc()).offset(keep)).all()
        if old_ids:
            for i in range(0, len(old_ids), 500):
                db.query(SchoolVersion).filter(SchoolVersion.id.in_(old_ids[i:i + 500])).delete(
                    synchronize_session=False)
            db.commit()

    def mutate(self, user: Any, message: str, fn: Callable[[School], T], scope: list[str] | None = None,
               dates: list[str] | None = None, *, action: str = "plan.change", details: dict | None = None) -> T:
        """Ändert das Dokument transaktional (siehe Moduldoku)."""
        scope = list(scope or ["all"])
        with self._lock:
            self.sync(force=True)
            work = copy_school(self.school)
            result = fn(work)
            encoded = encode_school(work)
            if encoded[1] == self._digest:
                return result
            with SessionLocal() as db:
                version = self._save(db, user, message, work, scope, None, action, details, encoded)
        bus.publish("change", {"version": version, "scope": scope, "dates": list(dates or [])})
        return result

    def replace(self, user: Any, message: str, school: School, scope: list[str] | None = None, *,
                action: str = "plan.replace", restored_from: int | None = None) -> int:
        """Ersetzt das gesamte Dokument (Import, Demo, Wiederherstellung). Gibt die neue Version zurück."""
        scope = list(scope or ["all"])
        with self._lock:
            self.sync(force=True)
            with SessionLocal() as db:
                version = self._save(db, user, message, copy_school(school), scope, restored_from, action)
        bus.publish("change", {"version": version, "scope": scope, "dates": []})
        return version

    # ------------------------------------------------------------------ Verlauf
    def history(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """``[{version, created_at, user, user_id, message, scope, restored_from}]`` (neueste zuerst)."""
        with SessionLocal() as db:
            rows = db.execute(
                select(SchoolVersion.id, SchoolVersion.created_at, SchoolVersion.user_id, SchoolVersion.message,
                       SchoolVersion.scope, SchoolVersion.restored_from, User.username, User.display_name)
                .outerjoin(User, User.id == SchoolVersion.user_id)
                .order_by(SchoolVersion.id.desc()).offset(max(0, offset)).limit(max(1, min(limit, 1000)))).all()
        return [{"version": r.id, "created_at": iso(r.created_at), "user": r.username or "system",
                 "user_display_name": r.display_name or ("System" if not r.username else r.username),
                 "user_id": r.user_id, "message": r.message, "scope": r.scope or [],
                 "restored_from": r.restored_from, "current": r.id == self.version} for r in rows]

    def count_versions(self) -> int:
        with SessionLocal() as db:
            return int(db.scalar(select(func.count(SchoolVersion.id))) or 0)

    def get_version(self, version: int) -> School:
        """Lädt eine ältere Version (``StoreError`` wenn nicht vorhanden)."""
        with SessionLocal() as db:
            row = db.get(SchoolVersion, version)
            if row is None:
                raise StoreError(f"Version {version} existiert nicht (mehr)")
            return decode_school(row.data)

    def restore(self, user: Any, version: int) -> int:
        """Stellt ``version`` als neue Version wieder her."""
        with self._lock:
            school = self.get_version(version)
            return self.replace(user, f"Version {version} wiederhergestellt", school, ["all", "restore"],
                                action="plan.restore", restored_from=version)

    def undo(self, user: Any) -> int:
        """Macht die letzte Änderung rückgängig (mehrfach aufrufbar: geht schrittweise zurück)."""
        with self._lock:
            self.sync(force=True)
            with SessionLocal() as db:
                cur = db.get(SchoolVersion, self.version)
                if cur is None:
                    raise StoreError("Kein aktueller Stand vorhanden")
                base = cur.id
                if "undo" in (cur.scope or []) and cur.restored_from:
                    base = cur.restored_from
                prev = db.scalar(select(SchoolVersion).where(SchoolVersion.id < base)
                                 .order_by(SchoolVersion.id.desc()).limit(1))
                if prev is None:
                    raise StoreError("Es gibt keine ältere Version, die wiederhergestellt werden kann")
                school, prev_id, prev_msg = decode_school(prev.data), prev.id, prev.message
            return self.replace(user, f"Rückgängig: zurück auf Version {prev_id} ({prev_msg})", school,
                                ["all", "undo"], action="plan.undo", restored_from=prev_id)

    @property
    def digest(self) -> str:
        """SHA-256 des aktuellen Dokuments (unterscheidet gleiche Versionsnummern verschiedener Datenbanken)."""
        return self._digest

    def info(self) -> dict:
        return {"version": self.version, "updated_at": iso(self.updated_at)}


_store: SchoolStore | None = None
_store_lock = threading.Lock()


def get_store() -> SchoolStore:
    """Globaler Store (lädt bei Bedarf; prüft höchstens alle 2 s auf neuere Versionen anderer Prozesse)."""
    global _store
    if _store is None or not _store.loaded:
        from .runtime import ensure_started

        ensure_started()
        with _store_lock:
            if _store is None:
                _store = SchoolStore()
            if not _store.loaded:
                _store.load()
    else:
        try:
            _store.sync()
        except Exception:  # noqa: BLE001 - Lesen soll nie an der Synchronisation scheitern
            log.exception("Synchronisation des Planungsdokuments fehlgeschlagen")
    return _store


def reset_store() -> None:
    """Verwirft den globalen Store (Tests / neue App-Instanz)."""
    global _store
    with _store_lock:
        _store = None
