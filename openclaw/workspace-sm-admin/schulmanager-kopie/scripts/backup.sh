#!/usr/bin/env bash
# Schulmanager – Datenbank-Backup mit Rotation und optionaler Offsite-Kopie
#
# Unterstützt PostgreSQL (pg_dump, Custom-Format) und SQLite (Online-Backup-API, gzip).
# Läuft im backup-Container (docker-compose.yml) oder direkt auf dem Host (systemd-Timer, Cron, make).
#
# Nutzung:
#   scripts/backup.sh                    Backup erstellen, rotieren, ggf. offsite kopieren
#   scripts/backup.sh --label vor-update zusätzliches Backup in manual/ (wird nicht täglich rotiert)
#   scripts/backup.sh --list             vorhandene Backups anzeigen
#   scripts/backup.sh --prune            nur Rotation anwenden
#   scripts/backup.sh --verify DATEI     Prüfsumme und Format einer Backup-Datei prüfen
#
# Ablage (BACKUP_DIR):
#   daily/   schulmanager_<art>_<JJJJ-MM-TT_hhmmss>.<ext>   (letzte BACKUP_KEEP_DAILY Tage)
#   weekly/  schulmanager_<art>_<JJJJ-Www>.<ext>            (erstes Backup je ISO-Woche)
#   monthly/ schulmanager_<art>_<JJJJ-MM>.<ext>             (erstes Backup je Monat)
#   manual/  schulmanager_<art>_<Zeit>_<label>.<ext>        (z. B. vor Updates/Restores)
#   <art> = pg | sqlite | files ;  <ext> = dump | db.gz | tar.gz  (+ .gpg bei Verschlüsselung)
#
# Umgebungsvariablen:
#   SM_DATABASE_URL        sqlite:///… oder postgresql+psycopg://user:pw@host:5432/db
#   PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE   alternativ zur URL (backup-Container)
#   BACKUP_DB_TYPE         auto | postgres | sqlite                       (Default auto)
#   BACKUP_SQLITE_PATH     Pfad der SQLite-Datei (überschreibt die URL)
#   BACKUP_DIR             Zielverzeichnis                                (Default ./backups)
#   BACKUP_KEEP_DAILY=14  BACKUP_KEEP_WEEKLY=8  BACKUP_KEEP_MONTHLY=12  BACKUP_KEEP_MANUAL=10
#   BACKUP_DATA_DIR        zusätzlich dieses Verzeichnis als tar.gz sichern (ohne DB-Dateien, ./backups und
#                          ohne BACKUP_DIR, falls es darin liegt)
#   BACKUP_GPG_PASSPHRASE  gesetzt → alle Backups symmetrisch mit GPG (AES256) verschlüsseln
#   BACKUP_RCLONE_REMOTE   z. B. "offsite:schulmanager" → nach jedem Lauf rclone sync/copy
#   BACKUP_RCLONE_MODE     sync (Default, spiegelt die Rotation) | copy (löscht offsite nie)
#   BACKUP_RCLONE_FLAGS    zusätzliche rclone-Optionen
#   BACKUP_PING_URL        bei Erfolg aufrufen (Healthchecks.io, Uptime-Kuma-Push …)
#   BACKUP_PING_URL_FAIL   bei Fehler aufrufen
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${SM_APP_DIR:-$ROOT}"
PY="${PYTHON:-python3}"          # Python für die SQLite-Kopie ohne sqlite3-Programm

BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
KEEP_DAILY="${BACKUP_KEEP_DAILY:-14}"
KEEP_WEEKLY="${BACKUP_KEEP_WEEKLY:-8}"
KEEP_MONTHLY="${BACKUP_KEEP_MONTHLY:-12}"
KEEP_MANUAL="${BACKUP_KEEP_MANUAL:-10}"

STAMP="$(date +%Y-%m-%d_%H%M%S)"
WEEK="$(date +%G-W%V)"
MONTH="$(date +%Y-%m)"

MODE=""          # "backup" während eines Backup-Laufs (für Fehler-Ping)
CURRENT_TMP=""   # halbfertige Datei, die bei Abbruch entfernt wird

log() { printf '%s [backup] %s\n' "$(date -Iseconds)" "$*" >&2; }
die() { log "FEHLER: $*"; exit 1; }

# ---------------------------------------------------------------------------
# Datenbank erkennen
# ---------------------------------------------------------------------------
db_type() {
    local t="${BACKUP_DB_TYPE:-auto}" url="${SM_DATABASE_URL:-}"
    if [[ "$t" != "auto" ]]; then
        echo "$t"
    elif [[ "$url" == postgres* ]]; then
        echo postgres
    elif [[ "$url" == sqlite* ]]; then
        echo sqlite
    elif [[ -n "${PGHOST:-}${PGDATABASE:-}" ]]; then
        echo postgres
    else
        echo sqlite
    fi
}

# libpq-kompatible URL (ohne SQLAlchemy-Treiberzusatz wie +psycopg); leer → PG*-Variablen
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
    # absolut: /… (Linux) oder Laufwerksbuchstabe C:\… / C:/… (Git-Bash unter Windows)
    [[ "$p" == /* || "$p" == [A-Za-z]:/* || "$p" == [A-Za-z]:\\* ]] || p="$APP_DIR/${p#./}"
    printf '%s' "$p"
}

pg_args() {
    local dsn
    dsn="$(pg_dsn)"
    if [[ -n "$dsn" ]]; then
        printf '%s\n' "--dbname=$dsn"
    fi
}

# ---------------------------------------------------------------------------
# Einzelschritte
# ---------------------------------------------------------------------------
sqlite_backup() {   # sqlite_backup SRC DEST  – konsistente Online-Kopie
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "$1" ".timeout 30000" ".backup '${2//\'/\'\'}'"
    else
        "$PY" - "$1" "$2" <<'PY'
import sqlite3, sys
src = sqlite3.connect(sys.argv[1], timeout=30)
dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
dst.close()
src.close()
PY
    fi
}

sqlite_check() {    # sqlite_check DATEI → "ok"?
    local res
    if command -v sqlite3 >/dev/null 2>&1; then
        res="$(sqlite3 "$1" 'PRAGMA integrity_check;' | head -n1)"
    else
        res="$("$PY" -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("PRAGMA integrity_check").fetchone()[0])' "$1")"
    fi
    [[ "$res" == "ok" ]]
}

dump_postgres() {   # dump_postgres ZIEL
    command -v pg_dump >/dev/null 2>&1 || die "pg_dump nicht gefunden (postgresql-client installieren oder backup-Container nutzen)"
    local args=()
    mapfile -t args < <(pg_args)
    pg_dump --format=custom --compress=6 --no-password "${args[@]}" --file="$1"
    pg_restore --list "$1" >/dev/null || die "Dump ist nicht lesbar: $1"
}

dump_sqlite() {     # dump_sqlite ZIEL(.db.gz)
    local src tmp
    src="$(sqlite_path)"
    [[ -f "$src" ]] || die "SQLite-Datenbank nicht gefunden: $src"
    tmp="${1%.gz}.tmp"
    rm -f "$tmp"
    sqlite_backup "$src" "$tmp"
    sqlite_check "$tmp" || { rm -f "$tmp"; die "Integritätsprüfung der Kopie fehlgeschlagen"; }
    gzip -6 -c "$tmp" > "$1"
    rm -f "$tmp"
    gzip -t "$1"
}

dump_files() {      # dump_files ZIEL(.tar.gz)
    local data target excl=()
    data="$(cd "$BACKUP_DATA_DIR" && pwd -P)"
    target="$(cd "$BACKUP_DIR" && pwd -P)"
    # Liegt das Zielverzeichnis im gesicherten Ordner (systemd: /var/lib/schulmanager/backups-db), wird es
    # ausgeschlossen – sonst enthält jedes Datei-Archiv alle früheren Sicherungen und verdoppelt sich je Lauf.
    if [[ "$target" == "$data" ]]; then
        die "BACKUP_DIR darf nicht gleich BACKUP_DATA_DIR sein ($data)"
    elif [[ "$target" == "$data"/* ]]; then
        excl+=("--exclude=./${target#"$data"/}")
    fi
    # GNU tar hält „C:\…“ sonst für einen Netzwerk-Host (Windows/Git-Bash); unter Linux ohne Wirkung
    [[ "$1" == *:* ]] && tar --help 2>/dev/null | grep -q -- '--force-local' && excl+=("--force-local")
    tar -czf "$1" -C "$data" "${excl[@]}" \
        --exclude='./backups' --exclude='*.db' --exclude='*.db-wal' --exclude='*.db-shm' \
        --exclude='*.sqlite' --exclude='*.sqlite3' --exclude='*.tmp' --exclude='*.partial' .
    gzip -t "$1"
}

encrypt() {         # encrypt DATEI → gibt neuen Namen aus
    local f="$1"
    if [[ -n "${BACKUP_GPG_PASSPHRASE:-}" ]]; then
        command -v gpg >/dev/null 2>&1 || die "BACKUP_GPG_PASSPHRASE gesetzt, aber gpg fehlt"
        gpg --batch --yes --quiet --pinentry-mode loopback --passphrase-fd 3 \
            --symmetric --cipher-algo AES256 --compress-algo none -o "$f.gpg" "$f" 3<<<"$BACKUP_GPG_PASSPHRASE"
        rm -f "$f"
        f="$f.gpg"
    fi
    printf '%s' "$f"
}

checksum() {        # checksum DATEI → DATEI.sha256
    ( cd "$(dirname "$1")" && sha256sum "$(basename "$1")" > "$(basename "$1").sha256" )
}

link_or_copy() {    # Hardlink spart Platz; über Dateisystemgrenzen hinweg kopieren
    ln -f "$1" "$2" 2>/dev/null || cp -f "$1" "$2"
    [[ -f "$1.sha256" ]] && sed "s#  .*#  $(basename "$2")#" "$1.sha256" > "$2.sha256"
    return 0
}

# ---------------------------------------------------------------------------
# Rotation
# ---------------------------------------------------------------------------
list_kind() {       # list_kind VERZ ART → Dateien (ohne .sha256), chronologisch
    find "$1" -maxdepth 1 -type f -name "schulmanager_${2}_*" ! -name '*.sha256' ! -name '*.partial' 2>/dev/null | sort
}

prune_daily() {     # behält alle Dateien der letzten N Kalendertage (mehrere Backups/Tag möglich)
    local dir="$1" keep="$2" kind f d
    for kind in pg sqlite files; do
        local files=() dates=()
        mapfile -t files < <(list_kind "$dir" "$kind")
        (( ${#files[@]} )) || continue
        mapfile -t dates < <(for f in "${files[@]}"; do basename "$f"; done \
            | sed -E "s/^schulmanager_${kind}_([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/" | sort -u -r)
        local keep_dates=" ${dates[*]:0:$keep} "
        for f in "${files[@]}"; do
            d="$(basename "$f" | sed -E "s/^schulmanager_${kind}_([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/")"
            if [[ "$keep_dates" != *" $d "* ]]; then
                log "Rotation: entferne $(basename "$f")"
                rm -f "$f" "$f.sha256"
            fi
        done
    done
}

prune_count() {     # behält die neuesten N Dateien je Art
    local dir="$1" keep="$2" kind i
    for kind in pg sqlite files; do
        local files=()
        mapfile -t files < <(list_kind "$dir" "$kind")
        local n=${#files[@]}
        for (( i = 0; i < n - keep; i++ )); do
            log "Rotation: entferne ${files[$i]#"$BACKUP_DIR"/}"
            rm -f "${files[$i]}" "${files[$i]}.sha256"
        done
    done
}

prune_all() {
    prune_daily "$BACKUP_DIR/daily" "$KEEP_DAILY"
    prune_count "$BACKUP_DIR/weekly" "$KEEP_WEEKLY"
    prune_count "$BACKUP_DIR/monthly" "$KEEP_MONTHLY"
    prune_count "$BACKUP_DIR/manual" "$KEEP_MANUAL"
}

# ---------------------------------------------------------------------------
# Offsite & Benachrichtigung
# ---------------------------------------------------------------------------
offsite() {
    [[ -n "${BACKUP_RCLONE_REMOTE:-}" ]] || return 0
    command -v rclone >/dev/null 2>&1 || die "BACKUP_RCLONE_REMOTE gesetzt, aber rclone fehlt"
    local mode="${BACKUP_RCLONE_MODE:-sync}" extra=()
    [[ "$mode" == "sync" || "$mode" == "copy" ]] || die "BACKUP_RCLONE_MODE muss sync oder copy sein"
    # shellcheck disable=SC2206 # bewusstes Wort-Splitting der Zusatzflags
    extra=(${BACKUP_RCLONE_FLAGS:-})
    log "Offsite: rclone $mode → $BACKUP_RCLONE_REMOTE"
    rclone "$mode" "$BACKUP_DIR" "$BACKUP_RCLONE_REMOTE" \
        --exclude '.last_*' --exclude '*.partial' --exclude '*.tmp' --exclude '.lock' \
        --transfers 2 --retries 5 --low-level-retries 10 "${extra[@]}"
}

ping() {            # ping URL [Nachricht]
    [[ -n "${1:-}" ]] || return 0
    if command -v curl >/dev/null 2>&1; then
        curl -fsS -m 15 --retry 3 --data-raw "${2:-}" "$1" >/dev/null || log "Ping an Monitoring fehlgeschlagen"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -T 15 -O /dev/null --post-data="${2:-}" "$1" || log "Ping an Monitoring fehlgeschlagen"
    fi
}

# ---------------------------------------------------------------------------
# Befehle
# ---------------------------------------------------------------------------
cmd_list() {
    local sub
    for sub in daily weekly monthly manual; do
        [[ -d "$BACKUP_DIR/$sub" ]] || continue
        echo "== $sub =="
        find "$BACKUP_DIR/$sub" -maxdepth 1 -type f ! -name '*.sha256' -exec ls -lh {} + 2>/dev/null \
            | awk '{print "  " $5 "\t" $NF}' | sed "s#$BACKUP_DIR/$sub/##" | sort -k2
    done
    if [[ -f "$BACKUP_DIR/.last_success" ]]; then
        echo "Letztes erfolgreiches Backup: $(date -d "@$(cat "$BACKUP_DIR/.last_success")" 2>/dev/null || cat "$BACKUP_DIR/.last_success")"
    fi
}

cmd_verify() {
    local f="${1:?Datei fehlt}"
    [[ -f "$f" ]] || die "Datei nicht gefunden: $f"
    if [[ -f "$f.sha256" ]]; then
        ( cd "$(dirname "$f")" && sha256sum -c "$(basename "$f").sha256" ) || die "Prüfsumme stimmt nicht: $f"
    else
        log "Keine .sha256-Datei – überspringe Prüfsummenvergleich"
    fi
    case "$f" in
        *.gpg) log "Verschlüsselt – Inhalt wird beim Restore geprüft" ;;
        *.dump) pg_restore --list "$f" >/dev/null && log "pg_restore kann den Dump lesen" ;;
        *.gz) gzip -t "$f" && log "gzip-Archiv ist intakt" ;;
        *) log "Unbekanntes Format – nur Prüfsumme geprüft" ;;
    esac
    log "OK: $f"
}

cmd_backup() {
    local label="${1:-}" type kind ext dest_dir name tmp final created=()
    type="$(db_type)"
    case "$type" in
        postgres) kind=pg; ext=dump ;;
        sqlite) kind=sqlite; ext=db.gz ;;
        *) die "Unbekannter Datenbanktyp: $type" ;;
    esac

    if [[ -n "$label" ]]; then
        label="$(printf '%s' "$label" | tr -c 'A-Za-z0-9_-' '-')"
        dest_dir="$BACKUP_DIR/manual"
    else
        dest_dir="$BACKUP_DIR/daily"
    fi
    mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly,manual}

    # Paralleles Ausführen (Zeitplan + manuell) verhindern
    if command -v flock >/dev/null 2>&1; then
        exec 9>"$BACKUP_DIR/.lock"
        local lock_opts=(-n)   # BusyBox-flock kennt kein -w
        flock --help 2>&1 | grep -q -- '-w' && lock_opts=(-w 600)
        flock "${lock_opts[@]}" 9 || die "Ein anderes Backup läuft noch (Sperre $BACKUP_DIR/.lock)"
    fi

    local parts=("$kind:$ext")
    if [[ -n "${BACKUP_DATA_DIR:-}" && -d "${BACKUP_DATA_DIR:-}" ]]; then
        parts+=("files:tar.gz")
    fi

    local start=$SECONDS part k e
    for part in "${parts[@]}"; do
        k="${part%%:*}"
        e="${part#*:}"
        name="schulmanager_${k}_${STAMP}${label:+_$label}.$e"
        tmp="$dest_dir/$name.partial"
        CURRENT_TMP="$tmp"
        log "Erstelle $k-Backup → ${dest_dir#"$BACKUP_DIR"/}/$name"
        case "$k" in
            pg) dump_postgres "$tmp" ;;
            sqlite) dump_sqlite "$tmp" ;;
            files) dump_files "$tmp" ;;
        esac
        mv -f "$tmp" "$dest_dir/$name"
        CURRENT_TMP=""
        final="$(encrypt "$dest_dir/$name")"
        checksum "$final"
        created+=("$final")
        log "Fertig: $(basename "$final") ($(du -h "$final" | cut -f1))"

        # Wochen-/Monatsstände: erstes Backup der Periode übernehmen
        if [[ -z "$label" ]]; then
            local suffix="${final#"$dest_dir/schulmanager_${k}_${STAMP}"}"
            if ! compgen -G "$BACKUP_DIR/weekly/schulmanager_${k}_${WEEK}.*" >/dev/null; then
                link_or_copy "$final" "$BACKUP_DIR/weekly/schulmanager_${k}_${WEEK}${suffix}"
                log "Wochenstand $WEEK angelegt"
            fi
            if ! compgen -G "$BACKUP_DIR/monthly/schulmanager_${k}_${MONTH}.*" >/dev/null; then
                link_or_copy "$final" "$BACKUP_DIR/monthly/schulmanager_${k}_${MONTH}${suffix}"
                log "Monatsstand $MONTH angelegt"
            fi
        fi
    done

    prune_all
    offsite

    date +%s > "$BACKUP_DIR/.last_success"
    printf '%s\n' "${created[@]}" > "$BACKUP_DIR/.last_success_files"
    log "Backup erfolgreich in $((SECONDS - start)) s"
    ping "${BACKUP_PING_URL:-}" "OK: ${created[*]##*/}"
}

on_exit() {
    local rc=$?
    [[ -n "$CURRENT_TMP" ]] && rm -f "$CURRENT_TMP" "${CURRENT_TMP%.gz}.tmp"
    if (( rc != 0 )) && [[ "$MODE" == "backup" ]]; then
        log "Backup FEHLGESCHLAGEN (Exit-Code $rc)"
        ping "${BACKUP_PING_URL_FAIL:-}" "Backup fehlgeschlagen auf $(hostname) (rc=$rc)"
    fi
    exit "$rc"
}
trap on_exit EXIT

main() {
    case "${1:-}" in
        -h|--help) sed -n '2,36p' "$0" ;;
        --list) cmd_list ;;
        --prune) prune_all ;;
        --verify) shift; cmd_verify "${1:-}" ;;
        --label) shift; MODE=backup; cmd_backup "${1:?Label fehlt}" ;;
        "") MODE=backup; cmd_backup "" ;;
        *) die "Unbekannte Option: $1 (siehe --help)" ;;
    esac
}

main "$@"
