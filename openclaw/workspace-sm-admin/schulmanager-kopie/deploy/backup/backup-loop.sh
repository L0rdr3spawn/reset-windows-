#!/usr/bin/env bash
# Schulmanager – Zeitsteuerung des Backup-Sidecars
#
#   backup-loop.sh            Dauerschleife: Backup zu den Zeiten in BACKUP_TIMES (lokale Zeit, TZ)
#   backup-loop.sh --check    Healthcheck: letztes erfolgreiches Backup jünger als BACKUP_MAX_AGE_HOURS?
#   backup-loop.sh --once     ein Backup sofort ausführen und beenden
#
# Umgebungsvariablen:
#   BACKUP_TIMES          Uhrzeiten HH:MM, durch Leerzeichen getrennt (Default "02:30";
#                         Beispiel "02:30 12:45" → zusätzlich mittags nach dem Vertretungsplan-Stress)
#   BACKUP_ON_START       1 = beim Containerstart sofort ein Backup erstellen (Default 1)
#   BACKUP_MAX_AGE_HOURS  Grenze für den Healthcheck (Default 26)
#   weitere: siehe backup.sh
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_TIMES="${BACKUP_TIMES:-02:30}"
MAX_AGE_H="${BACKUP_MAX_AGE_HOURS:-26}"
STARTED_FILE="/tmp/backup-loop.started"

log() { printf '%s [backup-loop] %s\n' "$(date -Iseconds)" "$*" >&2; }

check() {
    local now last started
    now="$(date +%s)"
    if [[ -f "$BACKUP_DIR/.last_success" ]]; then
        last="$(cat "$BACKUP_DIR/.last_success")"
        if (( now - last <= MAX_AGE_H * 3600 )); then
            echo "OK: letztes Backup vor $(( (now - last) / 60 )) min"
            exit 0
        fi
        echo "FEHLER: letztes erfolgreiches Backup vor $(( (now - last) / 3600 )) h"
        exit 1
    fi
    # Noch nie ein Backup: gesund, solange der Container jünger als die Höchstdauer ist
    started="$(cat "$STARTED_FILE" 2>/dev/null || echo "$now")"
    if (( now - started <= MAX_AGE_H * 3600 )); then
        echo "OK: noch kein Backup (Container läuft seit $(( (now - started) / 60 )) min)"
        exit 0
    fi
    echo "FEHLER: noch nie ein erfolgreiches Backup"
    exit 1
}

run_backup() {
    if backup.sh; then
        return 0
    fi
    log "Backup fehlgeschlagen – nächster Versuch zur nächsten geplanten Zeit (Details oben)."
    return 0
}

case "${1:-}" in
    --check) check ;;
    --once) exec backup.sh ;;
    "") ;;
    *) exec "$@" ;;
esac

for t in $BACKUP_TIMES; do
    [[ "$t" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]] || { log "Ungültige Zeit in BACKUP_TIMES: '$t' (Format HH:MM)"; exit 2; }
done

date +%s > "$STARTED_FILE"
trap 'log "Beende Backup-Dienst."; exit 0' TERM INT

log "Backup-Dienst aktiv. Zeiten: $BACKUP_TIMES (TZ=${TZ:-UTC}); Rotation täglich ${BACKUP_KEEP_DAILY:-14}," \
    "wöchentlich ${BACKUP_KEEP_WEEKLY:-8}, monatlich ${BACKUP_KEEP_MONTHLY:-12};" \
    "Offsite: ${BACKUP_RCLONE_REMOTE:-aus}; Verschlüsselung: $([[ -n "${BACKUP_GPG_PASSPHRASE:-}" ]] && echo an || echo aus)"

if [[ "${BACKUP_ON_START:-1}" == "1" ]]; then
    log "Start-Backup …"
    run_backup
fi

declare -A done_today=()
while true; do
    now="$(date +%H:%M)"
    today="$(date +%F)"
    for t in $BACKUP_TIMES; do
        if [[ "$now" == "$t" && "${done_today[$t]:-}" != "$today" ]]; then
            done_today[$t]="$today"
            log "Geplantes Backup ($t) …"
            run_backup
        fi
    done
    sleep 20 &
    wait $! || true
done
