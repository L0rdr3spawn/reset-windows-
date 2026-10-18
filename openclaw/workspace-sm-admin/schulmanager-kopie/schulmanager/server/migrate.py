"""Alembic-Integration: Migrationen programmatisch ausführen (Auto-Upgrade beim Start).

Kommandozeile (im Repo-Root): ``alembic upgrade head`` (nutzt ``alembic.ini`` → ``SM_DATABASE_URL``).
"""
from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from .config import config
from .db import get_engine, normalize_url

log = logging.getLogger("schulmanager.migrate")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def alembic_config(url: str | None = None) -> AlembicConfig:
    cfg = AlembicConfig()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", normalize_url(url or config.database_url).replace("%", "%%"))
    cfg.attributes["configure_logging"] = False
    return cfg


def head_revisions() -> set[str]:
    """Alle Köpfe (Feature-Migrationen dürfen parallel von ``0001``/``0002`` abzweigen)."""
    return set(ScriptDirectory.from_config(alembic_config()).get_heads())


def head_revision() -> str | None:
    heads = sorted(head_revisions())
    return ",".join(heads) if heads else None


def current_revisions() -> set[str]:
    with get_engine().connect() as conn:
        return set(MigrationContext.configure(conn).get_current_heads())


def current_revision() -> str | None:
    cur = sorted(current_revisions())
    return ",".join(cur) if cur else None


def upgrade_head() -> None:
    """Bringt die Datenbank auf den neuesten Stand (idempotent, auch bei mehreren Köpfen)."""
    cur, heads = current_revisions(), head_revisions()
    if cur == heads:
        return
    log.info("Datenbank-Migration %s → %s", ",".join(sorted(cur)) or "(leer)", ",".join(sorted(heads)))
    cfg = alembic_config()
    with get_engine().begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "heads")


def check_up_to_date() -> bool:
    return current_revisions() == head_revisions()


def main() -> None:
    """``python -m schulmanager.server.migrate`` – Datenbank auf den neuesten Stand bringen."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    config.validate()
    before = current_revision()
    upgrade_head()
    print(f"Datenbank: {config.db_kind}, Revision {before or '(leer)'} → {current_revision()}")


if __name__ == "__main__":
    main()
