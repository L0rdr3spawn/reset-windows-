"""Datenbankanbindung (SQLAlchemy 2).

* SQLite (Default, WAL-Modus, Fremdschlüssel aktiv) oder PostgreSQL (psycopg 3).
* ``SessionLocal`` ist eine stabile ``sessionmaker``-Instanz; :func:`configure_engine`
  bindet sie an die aktuelle ``config.database_url`` (Tests rufen das über ``create_app()``).
* Zeitstempel werden als **naive UTC**-Datetimes gespeichert (:func:`utcnow`).
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Engine, MetaData, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from .config import config

log = logging.getLogger("schulmanager.db")


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Deklarative Basis aller Tabellen (siehe ``db_models``)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


SessionLocal: sessionmaker[Session] = sessionmaker(autoflush=False, expire_on_commit=False)
_engine: Engine | None = None
_engine_lock = threading.Lock()


def utcnow() -> datetime:
    """Aktuelle Zeit als naive UTC-Datetime (Speicherformat aller Zeitstempel)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    """Naive-UTC-Datetime → ISO-8601 mit ``Z`` (für JSON-Antworten)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat(timespec="seconds") + "Z"


def normalize_url(url: str) -> str:
    """``postgres://``/``postgresql://`` → ``postgresql+psycopg://`` (psycopg 3)."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _sqlite_pragmas(dbapi_conn, _record) -> None:  # pragma: no cover - trivial
    cur = dbapi_conn.cursor()
    try:
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA busy_timeout=30000")
    finally:
        cur.close()


def build_engine(url: str) -> Engine:
    url = normalize_url(url)
    u = make_url(url)
    if u.get_backend_name() == "sqlite":
        db = u.database
        if db and db != ":memory:" and not db.startswith("file:"):
            Path(db).expanduser().parent.mkdir(parents=True, exist_ok=True)
        # Kein Pool: eine SQLite-Verbindung kostet fast nichts. Ein begrenzter Pool (5+10) blockiert unter Last –
        # Sessions sync. Endpunkte geben ihre Verbindung erst im Aufräumschritt zurück, der selbst einen
        # Threadpool-Platz braucht; sind alle Threads mit Warten auf eine Verbindung belegt, steht alles (Lasttest
        # 2026-10-12: ab ~100 gleichzeitigen Nutzern).
        file_db = bool(db) and db != ":memory:" and "mode=memory" not in url
        eng = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30},
                            **({"poolclass": NullPool} if file_db else {"pool_pre_ping": True}))
        event.listen(eng, "connect", _sqlite_pragmas)
        return eng
    # Pool größer als der Threadpool (``config.threadpool``), sonst dieselbe Verklemmung wie oben
    size = max(10, config.db_pool_size)
    return create_engine(url, pool_pre_ping=True, pool_size=size,
                         max_overflow=max(config.threadpool + 10 - size, 10), pool_timeout=20, pool_recycle=1800)


def configure_engine(url: str | None = None) -> Engine:
    """(Neu-)Erzeugt die Engine für ``url`` (Default: ``config.database_url``) und bindet ``SessionLocal``."""
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = build_engine(url or config.database_url)
        SessionLocal.configure(bind=_engine)
        return _engine


def get_engine() -> Engine:
    """Aktuelle Engine (wird bei Bedarf erzeugt)."""
    if _engine is None:
        return configure_engine()
    return _engine


def dispose_engine() -> None:
    global _engine
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
            _engine = None


def get_db() -> Iterator[Session]:
    """FastAPI-Dependency: eine Session pro Request (Commit durch den Handler)."""
    from .runtime import ensure_started

    ensure_started()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Kontextmanager für Hintergrundcode: committet bei Erfolg, Rollback bei Fehler."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def check_db() -> bool:
    """``SELECT 1`` – für ``/healthz``."""
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def db_kind() -> str:
    return get_engine().dialect.name
