#!/usr/bin/env bash
# Schulmanager – Datenbank-Migrationen ausführen
#
# Zentrale Stelle für "wie wird migriert" (genutzt von Docker-Entrypoint, systemd, Makefile, CI).
# Reihenfolge:
#   1. python -m schulmanager.server.cli migrate    (Backend-CLI: prüft Konfiguration, Alembic upgrade head)
#   2. schulmanager.server.migrate.upgrade_head()   (Fallback ohne CLI)
#   3. alembic upgrade head                         (falls alembic.ini im Projekt-Root liegt)
#   4. sonst: nichts tun – die App migriert beim Start selbst (SM_AUTO_MIGRATE=1, Default)
#
# Datenbank: SM_DATABASE_URL (Default sqlite:///./data/schulmanager.db)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log() { printf '%s [migrate] %s\n' "$(date -Iseconds)" "$*" >&2; }

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
    if [[ -x "$ROOT/.venv/bin/python" ]]; then
        PYTHON="$ROOT/.venv/bin/python"
    else
        PYTHON="$(command -v python3 || command -v python)"
    fi
fi

url="${SM_DATABASE_URL:-sqlite:///./data/schulmanager.db}"
if [[ "$url" == sqlite:* ]]; then
    path="${url#sqlite:///}"
    path="${path%%\?*}"
    mkdir -p "$(dirname "$path")"
fi

has_module() {
    "$PYTHON" - "$1" <<'PY' >/dev/null 2>&1
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)
PY
}

if has_module schulmanager.server.cli; then
    log "Führe 'python -m schulmanager.server.cli migrate' aus …"
    exec "$PYTHON" -m schulmanager.server.cli migrate
elif has_module schulmanager.server.migrate; then
    log "Bringe Datenbank auf den neuesten Stand (schulmanager.server.migrate.upgrade_head) …"
    exec "$PYTHON" - <<'PY'
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [migrate] %(message)s")
from schulmanager.server.config import config
from schulmanager.server import migrate

try:
    migrate.upgrade_head()
    rev = migrate.current_revision()
except Exception as exc:  # noqa: BLE001 - Klartext-Fehler für Betreiber
    logging.error("Migration fehlgeschlagen: %s", exc)
    sys.exit(1)
logging.info("Datenbank aktuell (Revision %s, %s)", rev, config.db_kind)
PY
elif [[ -f "$ROOT/alembic.ini" ]]; then
    log "Führe 'alembic upgrade head' aus …"
    exec "$PYTHON" -m alembic -c "$ROOT/alembic.ini" upgrade head
else
    log "Keine separate Migrationskonfiguration gefunden – die App migriert beim Start selbst."
fi
