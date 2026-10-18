#!/usr/bin/env bash
# Schulmanager – Entwicklungsserver: Backend (uvicorn --reload) und Frontend (Vite) parallel
#
# Nutzung:
#   scripts/dev.sh                 Backend :8000 + Frontend :5173 (Demo-Schule beim ersten Start)
#   scripts/dev.sh --backend-only  nur Backend
#   scripts/dev.sh --frontend-only nur Frontend (Backend läuft woanders: SM_BACKEND=http://host:8000)
#   scripts/dev.sh --fresh         Entwicklungsdatenbank (data/dev.db) vorher löschen
#   scripts/dev.sh --no-demo       ohne Demo-Schule starten
#
# Login: admin / schulmanager-dev (überschreibbar mit SM_ADMIN_USER / SM_ADMIN_PASSWORD)
# Eigene Einstellungen: .env.dev (wird automatisch geladen, falls vorhanden)
# Strg+C beendet beide Prozesse.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

backend=1
frontend=1
fresh=0
demo=1
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend-only) frontend=0 ;;
        --frontend-only) backend=0 ;;
        --fresh) fresh=1 ;;
        --no-demo) demo=0 ;;
        -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
        *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
    esac
    shift
done

if [[ -f "$ROOT/.env.dev" ]]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT/.env.dev"
    set +a
fi

export SM_ENV="${SM_ENV:-development}"
export SM_DATABASE_URL="${SM_DATABASE_URL:-sqlite:///./data/dev.db}"
export SM_BASE_URL="${SM_BASE_URL:-http://localhost:5173}"
export SM_COOKIE_SECURE="${SM_COOKIE_SECURE:-0}"
export SM_ADMIN_USER="${SM_ADMIN_USER:-admin}"
export SM_ADMIN_PASSWORD="${SM_ADMIN_PASSWORD:-schulmanager-dev}"
export SM_LOAD_DEMO="${SM_LOAD_DEMO:-$demo}"
export SM_LOG_FORMAT="${SM_LOG_FORMAT:-text}"
export SM_LOG_LEVEL="${SM_LOG_LEVEL:-INFO}"
export SM_GENERATE_TIME_LIMIT="${SM_GENERATE_TIME_LIMIT:-20}"
API_PORT="${DEV_API_PORT:-8000}"
WEB_PORT="${DEV_WEB_PORT:-5173}"
export SM_BACKEND="${SM_BACKEND:-http://127.0.0.1:$API_PORT}"

if [[ $fresh -eq 1 ]]; then
    db="${SM_DATABASE_URL#sqlite:///}"
    if [[ "$SM_DATABASE_URL" == sqlite:* && -f "$db" ]]; then
        echo "Lösche Entwicklungsdatenbank $db"
        rm -f -- "$db" "$db-wal" "$db-shm"
    fi
fi

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
    if [[ -x "$ROOT/.venv/bin/python" ]]; then PYTHON="$ROOT/.venv/bin/python"; else PYTHON="$(command -v python3)"; fi
fi

pids=()
# Jeder Dienst läuft (falls möglich) in einer eigenen Prozessgruppe, damit beim Beenden auch
# Kindprozesse (uvicorn-Reloader, Vite unter npm) sicher mit beendet werden.
start() {
    if command -v setsid >/dev/null 2>&1; then
        setsid "$@" &
    else
        "$@" &
    fi
    pids+=($!)
}
cleanup() {
    trap - INT TERM EXIT
    local p
    for p in "${pids[@]}"; do
        kill -TERM -- "-$p" 2>/dev/null || kill -TERM "$p" 2>/dev/null || true
    done
    if (( ${#pids[@]} )); then
        wait "${pids[@]}" 2>/dev/null || true
    fi
}
trap cleanup INT TERM EXIT

if [[ $backend -eq 1 ]]; then
    if ! "$PYTHON" -c "import uvicorn, fastapi" 2>/dev/null; then
        echo "Python-Abhängigkeiten fehlen – bitte 'make install' ausführen (oder: pip install -e '.[dev]')." >&2
        exit 1
    fi
    echo "▶ Backend:  http://localhost:$API_PORT   (API-Doku: /api/docs, DB: $SM_DATABASE_URL)"
    start "$PYTHON" -m uvicorn schulmanager.server.app:app --host 127.0.0.1 --port "$API_PORT" \
        --reload --reload-dir schulmanager
fi

if [[ $frontend -eq 1 ]]; then
    command -v npm >/dev/null 2>&1 || { echo "npm fehlt – Node.js 22 installieren." >&2; exit 1; }
    if [[ ! -d frontend/node_modules ]]; then
        echo "Installiere Frontend-Abhängigkeiten …"
        if [[ -f frontend/package-lock.json ]]; then npm --prefix frontend ci; else npm --prefix frontend install; fi
    fi
    echo "▶ Frontend: http://localhost:$WEB_PORT   (Proxy /api → $SM_BACKEND)"
    start npm --prefix frontend run dev -- --host 127.0.0.1 --port "$WEB_PORT" --strictPort
fi

echo "Login: $SM_ADMIN_USER / $SM_ADMIN_PASSWORD  –  Beenden mit Strg+C"
# Sobald einer der Prozesse endet, alles beenden
wait -n "${pids[@]}"
