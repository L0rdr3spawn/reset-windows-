"""Alembic-Umgebung des Schulmanagers.

URL: ``sqlalchemy.url`` aus der Alembic-Konfiguration (programmatisch gesetzt) oder
``SM_DATABASE_URL`` (Kommandozeile ``alembic upgrade head``). Eine bereits offene Verbindung
kann über ``config.attributes["connection"]`` übergeben werden.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context

from schulmanager.server import db_models  # noqa: F401 - registriert alle Tabellen
from schulmanager.server.config import config as sm_config
from schulmanager.server.db import Base, build_engine, normalize_url

alembic_cfg = context.config

if alembic_cfg.config_file_name is not None and alembic_cfg.attributes.get("configure_logging", True):
    fileConfig(alembic_cfg.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    if not url or url.startswith("driver://") or "%(SM_DATABASE_URL)" in url:
        url = sm_config.database_url
    return normalize_url(url)


def run_migrations_offline() -> None:
    url = _url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"}, render_as_batch=url.startswith("sqlite"))
    with context.begin_transaction():
        context.run_migrations()


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata,
                      render_as_batch=connection.dialect.name == "sqlite", compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = alembic_cfg.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    engine = build_engine(_url())
    with engine.connect() as conn:
        _run(conn)
        conn.commit()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
