#!/usr/bin/env bash
# Schulmanager – docker compose mit allen Umgebungsdateien
#
# Der Update-Agent legt das aktuell installierte Abbild in update.env ab (SM_IMAGE=…). Ein nacktes "docker compose up"
# würde nur .env lesen und die App auf das alte Abbild zurücksetzen. Dieses Skript liest beide Dateien:
#
#   scripts/compose.sh up -d
#   scripts/compose.sh --profile updater up -d updater
#   scripts/compose.sh logs -f app
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
args=()
[[ -f .env ]] && args+=(--env-file .env)
[[ -f update.env ]] && args+=(--env-file update.env)
exec docker compose "${args[@]}" "$@"
