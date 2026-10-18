#!/usr/bin/env bash
# Schulmanager – Container-Entrypoint
#
# Befehle:
#   serve            (Standard) Migrationen ausführen, dann uvicorn starten
#   migrate          nur Datenbank-Migrationen ausführen
#   create-admin …   Admin-Konto anlegen/zurücksetzen (siehe scripts/create-admin.sh)
#   cli …            Backend-CLI: python -m schulmanager.server.cli …
#   shell            Python-Shell im App-Kontext
#   <beliebig>       wird unverändert ausgeführt (z. B. "bash")
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
cd "$APP_DIR"

log() { printf '%s [entrypoint] %s\n' "$(date -Iseconds)" "$*" >&2; }

preflight() {
    local env="${SM_ENV:-production}"
    if [[ "$env" == "production" ]]; then
        if [[ -z "${SM_SECRET_KEY:-}" ]]; then
            log "WARNUNG: SM_SECRET_KEY ist nicht gesetzt. Sitzungen/Tokens sind nach einem Neustart ungültig"
            log "         bzw. die App erzeugt einen eigenen Schlüssel. Erzeugen mit: openssl rand -hex 32"
        elif [[ ${#SM_SECRET_KEY} -lt 32 ]]; then
            log "WARNUNG: SM_SECRET_KEY ist kürzer als 32 Zeichen – bitte 'openssl rand -hex 32' verwenden."
        fi
        if [[ "${SM_COOKIE_SECURE:-1}" != "1" ]]; then
            log "WARNUNG: SM_COOKIE_SECURE != 1 in Produktion – Session-Cookies werden auch über HTTP gesendet."
        fi
    fi

    # Reverse-Proxy-Vertrauen (S-10): X-Forwarded-* nur von SM_TRUSTED_PROXIES (Standard: nur Loopback)
    local proxies="${SM_TRUSTED_PROXIES:-${SM_FORWARDED_ALLOW_IPS:-}}"
    if [[ "${SM_TRUST_PROXY:-0}" == "1" ]]; then
        if [[ -z "$proxies" ]]; then
            log "WARNUNG: SM_TRUST_PROXY=1, aber SM_TRUSTED_PROXIES ist leer – es wird nur Loopback vertraut."
            log "         Hinter Caddy/nginx im Docker-Netz das Netz eintragen (siehe docs/BETRIEB.md, Abschnitt Reverse Proxy)."
        elif [[ "$proxies" == *"*"* ]]; then
            log "WARNUNG: SM_TRUSTED_PROXIES enthält '*' – jede Adresse darf ihre Client-IP fälschen. Nur verwenden,"
            log "         wenn die App garantiert nicht direkt erreichbar ist."
        fi
    elif [[ -n "$proxies" ]]; then
        log "HINWEIS: SM_TRUSTED_PROXIES ist gesetzt, aber SM_TRUST_PROXY ist nicht 1 – Proxy-Köpfe werden ignoriert."
    fi

    # SQLite: Verzeichnis muss existieren und beschreibbar sein
    local url="${SM_DATABASE_URL:-}"
    if [[ "$url" == sqlite:* ]]; then
        local path="${url#sqlite:///}"
        path="${path%%\?*}"
        local dir
        dir="$(dirname "$path")"
        mkdir -p "$dir" 2>/dev/null || true
        if [[ ! -w "$dir" ]]; then
            log "FEHLER: Datenverzeichnis '$dir' ist für $(id -un) (uid $(id -u)) nicht beschreibbar."
            log "        Volume-Rechte prüfen: chown -R 10001:10001 <volume-pfad>"
            exit 1
        fi
    fi
}

serve() {
    preflight

    if [[ "${SM_MIGRATE_ON_START:-1}" == "1" ]]; then
        "$APP_DIR/scripts/migrate.sh"
    else
        log "SM_MIGRATE_ON_START=0 – Migrationen werden übersprungen."
    fi

    local workers="${SM_WORKERS:-1}"
    if [[ "$workers" =~ ^[0-9]+$ ]] && (( workers > 1 )); then
        log "WARNUNG: SM_WORKERS=$workers. Der Schulmanager hält die Planungsdaten im Speicher und verteilt"
        log "         Live-Updates (SSE) prozesslokal. Mehrere Worker sehen sich gegenseitig NICHT – Änderungen"
        log "         und Live-Events gehen verloren. Empfohlen: SM_WORKERS=1 (vertikal skalieren)."
    fi

    local log_level
    log_level="$(printf '%s' "${SM_LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"
    case "$log_level" in
        critical|error|warning|info|debug|trace) ;;
        warn) log_level=warning ;;
        *) log_level=info ;;
    esac

    local args=(
        schulmanager.server.app:app
        --host "${SM_HOST:-0.0.0.0}"
        --port "${SM_PORT:-8000}"
        # X-Forwarded-* wertet die App selbst aus (schulmanager/server/proxy.py, nur von SM_TRUSTED_PROXIES)
        --no-proxy-headers
        --workers "$workers"
        --timeout-graceful-shutdown "${SM_GRACEFUL_TIMEOUT:-15}"
        --timeout-keep-alive "${SM_KEEPALIVE_TIMEOUT:-75}"
        --log-level "$log_level"
        --no-server-header
        # Access-Log schreibt die App selbst (Logger schulmanager.access, SM_ACCESS_LOG)
        --no-access-log
    )

    log "Starte Schulmanager ${SM_APP_VERSION:-} (Umgebung ${SM_ENV:-production}, Worker $workers, Port ${SM_PORT:-8000})"
    exec uvicorn "${args[@]}"
}

cmd="${1:-serve}"
case "$cmd" in
    serve)
        serve
        ;;
    migrate)
        exec "$APP_DIR/scripts/migrate.sh"
        ;;
    create-admin)
        shift
        exec python -m schulmanager.server.cli create-admin "$@"
        ;;
    cli)
        shift
        exec python -m schulmanager.server.cli "$@"
        ;;
    shell)
        exec python
        ;;
    *)
        exec "$@"
        ;;
esac
