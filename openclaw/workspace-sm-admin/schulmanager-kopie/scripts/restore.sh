#!/usr/bin/env bash
# Schulmanager – Backup wiederherstellen (PostgreSQL, SQLite, Datenverzeichnis)
#
# ACHTUNG: Überschreibt den aktuellen Datenbestand! Vorher wird automatisch ein
# Sicherheits-Backup in BACKUP_DIR/manual/ angelegt (abschaltbar mit --no-safety-backup).
# Die App hält die Planungsdaten im Speicher → sie muss während des Restores gestoppt sein
# und wird danach neu gestartet (im Compose-Modus automatisch).
#
# Nutzung:
#   scripts/restore.sh --compose backups/daily/schulmanager_pg_2026-10-05_023000.dump
#        Docker-Compose-Betrieb: kopiert die Datei in den backup-Container, stoppt "app",
#        stellt wieder her und startet "app" neu (empfohlen).
#   scripts/restore.sh [--yes] DATEI
#        Direkt (systemd-Installation, Entwicklung, im backup-Container). App vorher stoppen,
#        z. B. "systemctl stop schulmanager", oder --stop-cmd/--start-cmd angeben.
#   scripts/restore.sh --test DATEI
#        Test-Restore: nur entschlüsseln/entpacken und prüfen (PostgreSQL: zusätzlich in eine
#        temporäre Datenbank einspielen, wenn erlaubt) – ändert den Live-Bestand NICHT.
#
# Optionen:
#   --yes                 keine Sicherheitsabfrage (für Automatisierung)
#   --no-safety-backup    vorher kein Sicherheits-Backup anlegen
#   --stop-cmd "CMD"      Befehl zum Stoppen der App vor dem Restore
#   --start-cmd "CMD"     Befehl zum Starten der App danach
#   --compose             siehe oben (COMPOSE="docker compose -f …" überschreibbar)
#
# Dateitypen: *.dump (pg_dump -Fc), *.sql / *.sql.gz (SQL), *.db / *.db.gz / *.sqlite (SQLite),
#             schulmanager_files_*.tar.gz (Datenverzeichnis) – jeweils optional *.gpg (verschlüsselt,
#             Passphrase aus BACKUP_GPG_PASSPHRASE oder interaktiv).
# Datenbank-Ziel: wie scripts/backup.sh (SM_DATABASE_URL, PG*-Variablen, BACKUP_SQLITE_PATH).
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${SM_APP_DIR:-$ROOT}"
BACKUP_SCRIPT="$(dirname "${BASH_SOURCE[0]}")/backup.sh"
[[ -x "$BACKUP_SCRIPT" ]] || BACKUP_SCRIPT="$(command -v backup.sh || true)"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
CONFIRM_WORD="WIEDERHERSTELLEN"

yes=0
safety=1
compose=0
test_only=0
stop_cmd=""
start_cmd=""
file=""
WORK=""

log() { printf '%s [restore] %s\n' "$(date -Iseconds)" "$*" >&2; }
die() { log "FEHLER: $*"; exit 1; }
cleanup() { [[ -n "$WORK" && -d "$WORK" ]] && rm -rf "$WORK"; return 0; }
trap cleanup EXIT

usage() { sed -n '2,32p' "$0"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes) yes=1 ;;
        --no-safety-backup) safety=0 ;;
        --compose) compose=1 ;;
        --test) test_only=1 ;;
        --stop-cmd) stop_cmd="${2:?}"; shift ;;
        --start-cmd) start_cmd="${2:?}"; shift ;;
        -h|--help) usage; exit 0 ;;
        -*) die "Unbekannte Option: $1" ;;
        *) file="$1" ;;
    esac
    shift
done
[[ -n "$file" ]] || { usage; exit 1; }
[[ -f "$file" ]] || die "Datei nicht gefunden: $file"

# ---------------------------------------------------------------------------
# Hilfsfunktionen (gleiche Logik wie backup.sh)
# ---------------------------------------------------------------------------
pg_dsn() {
    local url="${SM_DATABASE_URL:-}"
    if [[ "$url" == postgres* ]]; then
        printf '%s' "$url" | sed -E 's#^postgres(ql)?(\+[A-Za-z0-9_]+)?://#postgresql://#'
    fi
}

sqlite_path() {
    local p
    if [[ -n "${BACKUP_SQLITE_PATH:-}" ]]; then
        p="$BACKUP_SQLITE_PATH"
    else
        local url="${SM_DATABASE_URL:-sqlite:///./data/schulmanager.db}"
        p="${url#sqlite:///}"
        p="${p%%\?*}"
    fi
    [[ "$p" == /* ]] || p="$APP_DIR/${p#./}"
    printf '%s' "$p"
}

masked_target() {
    local dsn
    dsn="$(pg_dsn)"
    if [[ -n "$dsn" ]]; then
        printf '%s' "$dsn" | sed -E 's#://([^:/@]+):[^@]*@#://\1:***@#'
    else
        printf 'postgresql://%s@%s:%s/%s' "${PGUSER:-?}" "${PGHOST:-localhost}" "${PGPORT:-5432}" "${PGDATABASE:-?}"
    fi
}

kind_of() {         # Art anhand des Dateinamens (ohne .gpg)
    local n
    n="$(basename "${1%.gpg}")"
    case "$n" in
        schulmanager_files_*.tar.gz|*.tar.gz) echo files ;;
        *.dump) echo pg_dump ;;
        *.sql|*.sql.gz) echo pg_sql ;;
        *.db|*.db.gz|*.sqlite|*.sqlite.gz|*.sqlite3) echo sqlite ;;
        *) echo unknown ;;
    esac
}

confirm() {         # confirm "Beschreibung"
    [[ $yes -eq 1 ]] && return 0
    if [[ ! -t 0 ]]; then
        die "Keine interaktive Eingabe möglich – mit --yes bestätigen (Vorsicht!)"
    fi
    printf '\n\033[1;31m!!! ACHTUNG – WIEDERHERSTELLUNG !!!\033[0m\n%s\n\n' "$1" >&2
    printf 'Zum Fortfahren "%s" eingeben: ' "$CONFIRM_WORD" >&2
    local answer
    read -r answer
    [[ "$answer" == "$CONFIRM_WORD" ]] || die "Abgebrochen."
}

verify_checksum() {
    if [[ -f "$1.sha256" ]]; then
        ( cd "$(dirname "$1")" && sha256sum -c "$(basename "$1").sha256" >/dev/null 2>&1 ) \
            || die "Prüfsumme stimmt nicht – Datei beschädigt? ($1)"
        log "Prüfsumme OK"
    fi
}

decrypt_if_needed() {   # gibt Pfad der entschlüsselten Datei aus
    local f="$1"
    if [[ "$f" == *.gpg ]]; then
        command -v gpg >/dev/null 2>&1 || die "gpg wird zum Entschlüsseln benötigt"
        local pass="${BACKUP_GPG_PASSPHRASE:-}"
        if [[ -z "$pass" ]]; then
            [[ -t 0 ]] || die "Verschlüsseltes Backup: BACKUP_GPG_PASSPHRASE setzen"
            read -r -s -p "GPG-Passphrase: " pass; echo >&2
        fi
        local out
        out="$WORK/$(basename "${f%.gpg}")"
        gpg --batch --yes --quiet --pinentry-mode loopback --passphrase-fd 3 -d -o "$out" "$f" 3<<<"$pass" \
            || die "Entschlüsseln fehlgeschlagen (falsche Passphrase?)"
        f="$out"
    fi
    printf '%s' "$f"
}

sqlite_check() {
    local res
    if command -v sqlite3 >/dev/null 2>&1; then
        res="$(sqlite3 "$1" 'PRAGMA integrity_check;' | head -n1)"
    else
        res="$(python3 -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("PRAGMA integrity_check").fetchone()[0])' "$1")"
    fi
    [[ "$res" == "ok" ]]
}

pg_run() {          # psql mit Ziel-DB
    local dsn
    dsn="$(pg_dsn)"
    if [[ -n "$dsn" ]]; then
        psql --no-psqlrc -v ON_ERROR_STOP=1 --quiet --dbname="$dsn" "$@"
    else
        psql --no-psqlrc -v ON_ERROR_STOP=1 --quiet "$@"
    fi
}

# PostgreSQL-Dump → SQL-Datei (vollständig, bevor irgendetwas geändert wird)
pg_to_sql() {       # pg_to_sql DATEI ART → Pfad der SQL-Datei
    local f="$1" k="$2" sql="$WORK/restore.sql"
    case "$k" in
        pg_dump)
            command -v pg_restore >/dev/null 2>&1 || die "pg_restore nicht gefunden (backup-Container oder --compose nutzen)"
            pg_restore --no-owner --no-privileges --file="$sql" "$f" || die "Dump nicht lesbar: $f"
            ;;
        pg_sql)
            if [[ "$f" == *.gz ]]; then gzip -dc "$f" > "$sql"; else cp "$f" "$sql"; fi
            ;;
    esac
    printf '%s' "$sql"
}

# ---------------------------------------------------------------------------
# Compose-Modus: Wrapper auf dem Host
# ---------------------------------------------------------------------------
compose_restore() {
    local compose="${COMPOSE:-docker compose}"
    # shellcheck disable=SC2206
    local dc=($compose)
    cd "$ROOT"
    "${dc[@]}" ps --status running --services 2>/dev/null | grep -qx backup \
        || die "Der backup-Container läuft nicht (docker compose up -d backup)"

    confirm "Backup:  $file
Ziel:    Datenbank des Docker-Compose-Projekts in $ROOT
Ablauf:  app stoppen → Sicherheits-Backup → Restore → app starten
Alle Änderungen seit dem Backup gehen verloren."

    local name dest
    name="$(basename "$file")"
    dest="/tmp/restore-$STAMP-$name"
    log "Kopiere Backup in den backup-Container …"
    "${dc[@]}" cp "$file" "backup:$dest"
    [[ -f "$file.sha256" ]] && "${dc[@]}" cp "$file.sha256" "backup:$dest.sha256.orig"

    log "Stoppe app …"
    "${dc[@]}" stop app
    local rc=0
    local inner=(restore.sh --yes "$dest")
    [[ $safety -eq 0 ]] && inner+=(--no-safety-backup)
    if [[ -f "$file.sha256" ]]; then
        "${dc[@]}" exec -T backup sh -c "sed 's#  .*#  $(basename "$dest")#' '$dest.sha256.orig' > '$dest.sha256'"
    fi
    "${dc[@]}" exec -T backup "${inner[@]}" || rc=$?
    "${dc[@]}" exec -T backup rm -f "$dest" "$dest.sha256" "$dest.sha256.orig" || true

    log "Starte app …"
    "${dc[@]}" start app
    if "${dc[@]}" exec -T app /app/scripts/healthcheck.sh --quiet --wait 240; then
        log "App ist wieder gesund."
    else
        log "WARNUNG: App meldet sich nicht gesund – Logs prüfen: docker compose logs app"
    fi
    (( rc == 0 )) || die "Restore fehlgeschlagen (Exit-Code $rc). Datenbank unverändert (Transaktion) – siehe Ausgabe oben."
    log "Wiederherstellung abgeschlossen."
}

# ---------------------------------------------------------------------------
# Direkter Restore
# ---------------------------------------------------------------------------
restore_postgres() {
    local f="$1" k="$2" sql
    command -v psql >/dev/null 2>&1 || die "psql nicht gefunden (backup-Container oder --compose nutzen)"
    sql="$(pg_to_sql "$f" "$k")"
    [[ -s "$sql" ]] || die "Leeres SQL – Backup unbrauchbar"

    if [[ $test_only -eq 1 ]]; then
        log "Test-Restore: SQL erzeugt ($(du -h "$sql" | cut -f1)), $(grep -c '^COPY ' "$sql" || true) Tabellen mit Daten."
        if [[ "${RESTORE_TEST_DB:-}" != "" ]]; then
            log "Spiele zusätzlich in Test-Datenbank '$RESTORE_TEST_DB' ein …"
            pg_run -c "DROP DATABASE IF EXISTS \"$RESTORE_TEST_DB\"" -c "CREATE DATABASE \"$RESTORE_TEST_DB\""
            local dsn
            dsn="$(pg_dsn)"
            if [[ -n "$dsn" ]]; then
                dsn="$(printf '%s' "$dsn" | sed -E "s#/[^/?]+(\?|$)#/$RESTORE_TEST_DB\1#")"
                psql --no-psqlrc -v ON_ERROR_STOP=1 --quiet --single-transaction --dbname="$dsn" -f "$sql" >/dev/null
                psql --no-psqlrc --dbname="$dsn" -c "SELECT count(*) AS versionen FROM school_versions" || true
            else
                PGDATABASE="$RESTORE_TEST_DB" psql --no-psqlrc -v ON_ERROR_STOP=1 --quiet --single-transaction -f "$sql" >/dev/null
                PGDATABASE="$RESTORE_TEST_DB" psql --no-psqlrc -c "SELECT count(*) AS versionen FROM school_versions" || true
            fi
            pg_run -c "DROP DATABASE \"$RESTORE_TEST_DB\""
            log "Test-Restore in temporäre Datenbank erfolgreich."
        fi
        return 0
    fi

    confirm "Backup:  $file
Ziel:    $(masked_target)
Das Schema 'public' wird vollständig ersetzt. Alle Änderungen seit dem Backup gehen verloren.
Die App MUSS gestoppt sein (sie hält Daten im Speicher)."

    [[ -n "$stop_cmd" ]] && { log "Stoppe App: $stop_cmd"; bash -c "$stop_cmd"; }
    if [[ $safety -eq 1 && -n "$BACKUP_SCRIPT" ]]; then
        log "Sicherheits-Backup des aktuellen Stands …"
        BACKUP_DATA_DIR="" "$BACKUP_SCRIPT" --label vor-restore || die "Sicherheits-Backup fehlgeschlagen – Abbruch"
    fi

    log "Spiele Backup ein (eine Transaktion – bei Fehler bleibt alles unverändert) …"
    {
        echo "SET client_min_messages = warning;"
        echo "DROP SCHEMA IF EXISTS public CASCADE;"
        echo "CREATE SCHEMA public;"
        cat "$sql"
    } | pg_run --single-transaction >/dev/null
    pg_run -c "ANALYZE" >/dev/null || true
    log "PostgreSQL-Restore erfolgreich."
    [[ -n "$start_cmd" ]] && { log "Starte App: $start_cmd"; bash -c "$start_cmd"; }
    return 0
}

restore_sqlite() {
    local f="$1" target tmp
    target="$(sqlite_path)"
    tmp="$WORK/restore.db"
    if [[ "$f" == *.gz ]]; then gzip -dc "$f" > "$tmp"; else cp "$f" "$tmp"; fi
    sqlite_check "$tmp" || die "Backup-Datenbank ist beschädigt (integrity_check)"
    log "Integritätsprüfung OK"

    if [[ $test_only -eq 1 ]]; then
        log "Test-Restore OK: $(du -h "$tmp" | cut -f1) SQLite-Datenbank, integrity_check = ok"
        return 0
    fi

    confirm "Backup:  $file
Ziel:    $target
Die aktuelle Datei wird nach $target.vor-restore-$STAMP verschoben.
Die App MUSS gestoppt sein (sie hält Daten im Speicher)."

    [[ -n "$stop_cmd" ]] && { log "Stoppe App: $stop_cmd"; bash -c "$stop_cmd"; }
    if [[ $safety -eq 1 && -n "$BACKUP_SCRIPT" && -f "$target" ]]; then
        log "Sicherheits-Backup des aktuellen Stands …"
        BACKUP_DATA_DIR="" "$BACKUP_SCRIPT" --label vor-restore || die "Sicherheits-Backup fehlgeschlagen – Abbruch"
    fi

    local dir owner
    dir="$(dirname "$target")"
    mkdir -p "$dir"
    owner="$(stat -c '%u:%g' "$dir" 2>/dev/null || true)"
    if [[ -f "$target" ]]; then
        mv -f "$target" "$target.vor-restore-$STAMP"
        # WAL gehört zur alten Datei → mit umbenennen, damit die Kopie konsistent bleibt
        [[ -f "$target-wal" ]] && mv -f "$target-wal" "$target.vor-restore-$STAMP-wal"
        log "Alte Datenbank gesichert: $target.vor-restore-$STAMP"
    fi
    rm -f "$target-wal" "$target-shm"
    cp "$tmp" "$target.tmp-restore"
    mv -f "$target.tmp-restore" "$target"
    if [[ -n "$owner" && "$(id -u)" == "0" ]]; then
        chown "$owner" "$target" || true
    fi
    chmod 0640 "$target" || true
    log "SQLite-Restore erfolgreich: $target"
    [[ -n "$start_cmd" ]] && { log "Starte App: $start_cmd"; bash -c "$start_cmd"; }
    return 0
}

restore_files() {
    local f="$1" target="${BACKUP_DATA_DIR:-$APP_DIR/data}"
    tar -tzf "$f" >/dev/null || die "Archiv beschädigt"
    if [[ $test_only -eq 1 ]]; then
        log "Test-Restore OK: Archiv enthält $(tar -tzf "$f" | wc -l) Einträge"
        return 0
    fi
    confirm "Backup:  $file
Ziel:    $target (Dateien werden überschrieben, Datenbankdateien bleiben unberührt)"
    local owner
    owner="$(stat -c '%u:%g' "$target" 2>/dev/null || true)"
    tar -xzf "$f" -C "$target" --no-same-owner
    if [[ -n "$owner" && "$(id -u)" == "0" ]]; then
        chown -R "$owner" "$target" || true
    fi
    log "Datenverzeichnis wiederhergestellt: $target"
}

# ---------------------------------------------------------------------------
main() {
    if [[ $compose -eq 1 ]]; then
        [[ $test_only -eq 0 ]] || die "--test bitte direkt im Container: docker compose exec backup restore.sh --test …"
        compose_restore
        return
    fi

    WORK="$(mktemp -d "${TMPDIR:-/tmp}/sm-restore.XXXXXX")"
    verify_checksum "$file"
    local k plain
    k="$(kind_of "$file")"
    [[ "$k" != unknown ]] || die "Unbekannter Dateityp: $file"
    plain="$(decrypt_if_needed "$file")"
    log "Backup-Art: $k ($(basename "$file"))"

    case "$k" in
        pg_dump|pg_sql) restore_postgres "$plain" "$k" ;;
        sqlite) restore_sqlite "$plain" ;;
        files) restore_files "$plain" ;;
    esac
    if [[ $test_only -eq 0 && -z "$start_cmd" && "$k" != files ]]; then
        log "Hinweis: App jetzt (neu) starten, damit sie den wiederhergestellten Stand lädt."
    fi
}

main
