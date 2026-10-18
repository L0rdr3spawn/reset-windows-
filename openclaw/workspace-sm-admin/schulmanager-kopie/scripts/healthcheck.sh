#!/usr/bin/env bash
# Schulmanager – Healthcheck
#
# Prüft GET /healthz (HTTP 200 und – falls JSON – "status" == "ok").
# Nutzbar als Docker-HEALTHCHECK, in Cron/Monitoring oder nach Updates.
#
#   scripts/healthcheck.sh                       → http://127.0.0.1:${SM_PORT:-8000}/healthz
#   scripts/healthcheck.sh https://plan.schule.de  → https://plan.schule.de/healthz
#   scripts/healthcheck.sh --quiet               → keine Ausgabe, nur Exit-Code
#   scripts/healthcheck.sh --wait 120            → bis zu 120 s warten, bis die App gesund ist
#
# Exit-Codes: 0 = gesund, 1 = ungesund/nicht erreichbar
set -euo pipefail

quiet=0
wait_s=0
base=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        -q|--quiet) quiet=1 ;;
        -w|--wait) wait_s="${2:?Sekunden fehlen}"; shift ;;
        -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
        *) base="$1" ;;
    esac
    shift
done

if [[ -z "$base" ]]; then
    url="${SM_HEALTH_URL:-http://127.0.0.1:${SM_PORT:-8000}/healthz}"
elif [[ "$base" == */healthz ]]; then
    url="$base"
else
    url="${base%/}/healthz"
fi

say() { [[ $quiet -eq 1 ]] || printf '%s\n' "$*"; }

fetch() {
    # Gibt den Body aus; Exit-Code != 0 bei Netzwerkfehler oder HTTP-Status >= 400
    if command -v curl >/dev/null 2>&1; then
        curl -fsS --max-time 5 "$url"
    elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
        "$(command -v python3 || command -v python)" - "$url" <<'PY'
import sys, urllib.request
with urllib.request.urlopen(sys.argv[1], timeout=5) as r:
    sys.stdout.write(r.read().decode("utf-8", "replace"))
PY
    elif command -v wget >/dev/null 2>&1; then
        wget -q -T 5 -O - "$url"
    else
        echo "Weder curl, python noch wget gefunden." >&2
        return 2
    fi
}

check_once() {
    local body
    body="$(fetch 2>/dev/null)" || return 1
    # Wenn JSON mit "status" zurückkommt, muss es "ok" sein
    if [[ "$body" == *'"status"'* ]] && [[ "$body" != *'"status":"ok"'* ]] && [[ "$body" != *'"status": "ok"'* ]]; then
        say "UNGESUND: $url → $body"
        return 1
    fi
    say "OK: $url ${body:0:200}"
    return 0
}

deadline=$(( $(date +%s) + wait_s ))
while true; do
    if check_once; then
        exit 0
    fi
    if (( $(date +%s) >= deadline )); then
        say "FEHLER: $url nicht gesund erreichbar."
        exit 1
    fi
    sleep 2
done
