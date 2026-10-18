#!/usr/bin/env bash
# Schulmanager – Admin-Konto anlegen oder Passwort zurücksetzen (über die Backend-CLI)
#
# Nutzung:
#   scripts/create-admin.sh                       Admin "admin" anlegen, Passwort interaktiv
#   scripts/create-admin.sh -u schulleitung       anderer Benutzername
#   scripts/create-admin.sh --update -u admin     vorhandenes Konto wieder zum Admin machen + neues Passwort
#   scripts/create-admin.sh --temp -u admin       ohne Passwort: Startpasswort wird erzeugt und ausgegeben
#                                                 (muss beim ersten Login geändert werden)
#   scripts/create-admin.sh --compose …           im laufenden Docker-Container "app" ausführen
#   SM_NEW_ADMIN_PASSWORD='…' scripts/create-admin.sh --yes   nicht interaktiv (z. B. Ansible)
#
# Entspricht: python -m schulmanager.server.cli create-admin --username U --password-stdin [--update]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

username="admin"
update=0
compose=0
temp=0
display=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--username) username="${2:?Benutzername fehlt}"; shift ;;
        -n|--display-name) display="${2:?Anzeigename fehlt}"; shift ;;
        --update) update=1 ;;
        --compose) compose=1 ;;
        --temp) temp=1 ;;
        --yes) ;;  # Kompatibilität: Passwort kommt dann aus SM_NEW_ADMIN_PASSWORD
        -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
        *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
    esac
    shift
done

args=(create-admin --username "$username")
[[ -n "$display" ]] && args+=(--display-name "$display")
[[ $update -eq 1 ]] && args+=(--update)

password=""
if [[ $temp -eq 0 ]]; then
    password="${SM_NEW_ADMIN_PASSWORD:-}"
    if [[ -z "$password" ]]; then
        [[ -t 0 ]] || { echo "Kein Terminal: Passwort über SM_NEW_ADMIN_PASSWORD übergeben oder --temp nutzen." >&2; exit 1; }
        echo "Passwort für '$username' (mindestens 10 Zeichen, darf den Benutzernamen nicht enthalten):" >&2
        read -r -s -p "Passwort: " password; echo >&2
        read -r -s -p "Wiederholen: " password2; echo >&2
        [[ "$password" == "$password2" ]] || { echo "Die Passwörter stimmen nicht überein." >&2; exit 1; }
    fi
    args+=(--password-stdin)
fi

run() {
    if [[ $compose -eq 1 ]]; then
        docker compose exec -T app python -m schulmanager.server.cli "$@"
    else
        local py="${PYTHON:-}"
        if [[ -z "$py" ]]; then
            if [[ -x "$ROOT/.venv/bin/python" ]]; then py="$ROOT/.venv/bin/python"; else py="$(command -v python3)"; fi
        fi
        # .env laden, falls vorhanden und SM_DATABASE_URL noch nicht gesetzt (Installation ohne Docker)
        if [[ -z "${SM_DATABASE_URL:-}" && -f "${SM_ENV_FILE:-/etc/schulmanager/schulmanager.env}" ]]; then
            set -a
            # shellcheck disable=SC1090
            . "${SM_ENV_FILE:-/etc/schulmanager/schulmanager.env}"
            set +a
        fi
        "$py" -m schulmanager.server.cli "$@"
    fi
}

if [[ -n "$password" ]]; then
    printf '%s\n' "$password" | run "${args[@]}"
else
    run "${args[@]}" </dev/null
fi
