#!/usr/bin/env bash
# Schulmanager – Vorschau zum Ausprobieren (GitHub Codespaces oder lokal): App mit Demo-Schule auf einem Port
#
# Nutzung:
#   scripts/preview.sh               im Vordergrund starten (Strg+C beendet)
#   scripts/preview.sh --background  im Hintergrund starten, warten bis die Demo-Schule geladen ist (Codespaces)
#   scripts/preview.sh --reset       Vorschau-Datenbank löschen und frisch mit Demo-Schule starten
#   scripts/preview.sh --stop        laufende Vorschau beenden
#
# Voraussetzung: pip install -e . und gebaute Oberfläche (npm --prefix frontend ci && npm --prefix frontend run build).
# Nur zum Testen – nicht für echte Schuldaten (Entwicklungsmodus, Schlüssel aus SM_SECRET_KEY abgeleitet).
# Anmeldung: Demo-Konten mit Passwort demo123456, Admin: admin / Schulmanager-Vorschau-2026 (siehe docs/VORSCHAU.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${PREVIEW_PORT:-8000}"
DIR="$ROOT/data/preview"
LOG="$DIR/server.log"
PIDFILE="$DIR/server.pid"
mode=foreground

while [[ $# -gt 0 ]]; do
    case "$1" in
        --background) mode=background ;;
        --reset) mode=reset ;;
        --stop) mode=stop ;;
        -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
        *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
    esac
    shift
done

# PID der laufenden Vorschau (nur wenn der Prozess wirklich unser uvicorn ist – nach einem Neustart des
# Containers kann die alte PID zu einem anderen Prozess gehören)
running_pid() {
    local pid
    [[ -f "$PIDFILE" ]] || return 1
    pid="$(cat "$PIDFILE")"
    [[ -r "/proc/$pid/cmdline" ]] && tr '\0' ' ' <"/proc/$pid/cmdline" | grep -q "schulmanager.server.app" || return 1
    echo "$pid"
}

stop() {
    local pid
    if pid="$(running_pid)"; then
        kill "$pid" || true
        for _ in $(seq 1 20); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.5
        done
        echo "Vorschau beendet."
    fi
    rm -f "$PIDFILE"
}

case "$mode" in
    stop) stop; exit 0 ;;
    reset)
        stop
        rm -f "$DIR"/schulmanager.db "$DIR"/schulmanager.db-wal "$DIR"/schulmanager.db-shm
        rm -rf "$DIR/files"
        echo "Vorschau-Datenbank gelöscht – starte frisch mit Demo-Schule."
        mode=background
        ;;
esac

if ! python -c 'import schulmanager, uvicorn, fastapi, sqlalchemy' 2>/dev/null; then
    echo "Python-Pakete fehlen – installiere …"
    pip install --no-cache-dir -e "$ROOT"
fi

if [[ ! -f "$ROOT/frontend/dist/index.html" ]]; then
    echo "Oberfläche fehlt – baue frontend/dist …"
    npm --prefix frontend ci
    npm --prefix frontend run build
fi

mkdir -p "$DIR"

# Öffentliche Adresse: in Codespaces die weitergeleitete Port-URL, sonst localhost
if [[ -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
    url="https://${CODESPACE_NAME}-${PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
else
    url="http://localhost:${PORT}"
fi

export TZ="${TZ:-Europe/Berlin}"     # Stundenzeiten (z. B. Freigabe „zur Stunde“) gelten in Schulzeit
export SM_ENV=development
export SM_DATA_DIR="$DIR"
export SM_DATABASE_URL="sqlite:///$DIR/schulmanager.db"
export SM_BASE_URL="$url"
export SM_COOKIE_SECURE=0
export SM_TRUST_PROXY=1
export SM_TRUSTED_PROXIES="${PREVIEW_TRUSTED_PROXIES:-127.0.0.1,::1}"   # Vorschau-Proxy läuft lokal; nie "*"
export SM_ADMIN_USER=admin
export SM_ADMIN_PASSWORD="${PREVIEW_ADMIN_PASSWORD:-Schulmanager-Vorschau-2026}"
export SM_LOAD_DEMO=1
export SM_DEMO_BACKGROUND=0          # Server lauscht erst, wenn die Demo-Schule fertig ist
export SM_DEMO_CLASSES_PER_GRADE="${PREVIEW_CLASSES_PER_GRADE:-14}"
export SM_GENERATE_TIME_LIMIT="${PREVIEW_GENERATE_SECONDS:-20}"
export SM_FRONTEND_DIST="$ROOT/frontend/dist"
export SM_NOTIFY_DISPATCHER=0
export SM_LOG_FORMAT=text
export SM_LOG_LEVEL=INFO

cmd=(python -m uvicorn schulmanager.server.app:app --host 0.0.0.0 --port "$PORT" --no-proxy-headers)

if [[ "$mode" == foreground ]]; then
    echo "Schulmanager-Vorschau: $url  (erster Start: Demo-Schule wird ca. 1 Minute erzeugt)"
    exec "${cmd[@]}"
fi

stop
echo "Starte Schulmanager-Vorschau im Hintergrund (Protokoll: $LOG) …"
setsid nohup "${cmd[@]}" >>"$LOG" 2>&1 </dev/null &
echo $! >"$PIDFILE"

for _ in $(seq 1 150); do
    if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
        echo
        echo "Vorschau läuft: $url"
        echo "Anmelden z. B. als eltern1, schueler1, lehrer1, sekretariat (Passwort demo123456) – siehe docs/VORSCHAU.md"
        exit 0
    fi
    if ! running_pid >/dev/null; then
        echo "Vorschau ist beim Start abgebrochen – letzte Zeilen aus $LOG:" >&2
        tail -n 30 "$LOG" >&2
        exit 1
    fi
    sleep 2
done
echo "Vorschau startet noch (Demo-Schule wird erzeugt) – Protokoll: $LOG" >&2
