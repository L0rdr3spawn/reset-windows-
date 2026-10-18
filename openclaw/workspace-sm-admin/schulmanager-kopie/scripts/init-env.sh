#!/usr/bin/env bash
# Schulpuls – .env für den Echtbetrieb erzeugen (Geheimnisse werden zufällig erzeugt)
#
#   scripts/init-env.sh --domain plan.meine-schule.de --email it@meine-schule.de [--output .env] [--force]
#
# Kopiert .env.example nach .env, setzt Domain und Kontaktadresse und ersetzt alle Platzhalter
# ("BITTE_AENDERN…") für SM_SECRET_KEY, SM_ENCRYPTION_KEYS, POSTGRES_PASSWORD und BACKUP_GPG_PASSPHRASE
# durch zufällige Werte. Die Datei bekommt Rechte 600.
#
# WICHTIG: SM_ENCRYPTION_KEYS und BACKUP_GPG_PASSPHRASE danach GETRENNT vom Server sichern (Passwort-Tresor,
# Ausdruck im Safe). Ohne den Schlüssel sind verschlüsselte Inhalte nach einer Wiederherstellung unlesbar.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/.env"
DOMAIN=""
EMAIL=""
FORCE=0

die() { echo "Fehler: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain) DOMAIN="${2:-}"; shift 2 ;;
        --email) EMAIL="${2:-}"; shift 2 ;;
        --output) OUT="${2:-}"; shift 2 ;;
        --force) FORCE=1; shift ;;
        -h|--help) sed -n '2,13p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) die "Unbekannte Option: $1" ;;
    esac
done

[[ -n "$DOMAIN" ]] || die "--domain fehlt (z. B. plan.meine-schule.de)"
[[ -n "$EMAIL" ]] || die "--email fehlt (Kontaktadresse für Let's Encrypt)"
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "Ungültige Domain"
[[ "$EMAIL" =~ ^[^@[:space:]]+@[^@[:space:]]+$ ]] || die "Ungültige E-Mail-Adresse"
command -v openssl >/dev/null || die "openssl wird benötigt"
[[ -f "$ROOT/.env.example" ]] || die ".env.example nicht gefunden"
if [[ -e "$OUT" && "$FORCE" != 1 ]]; then
    die "$OUT existiert bereits – mit --force überschreiben (bestehende Schlüssel gehen dabei verloren!)"
fi

SECRET="$(openssl rand -hex 32)"
ENCKEY="k1:$(openssl rand -base64 32)"
PGPASS="$(openssl rand -hex 24)"
GPGPASS="$(openssl rand -base64 24)"

umask 077
# Zeilenweise ersetzen (awk statt sed: Schlüssel enthalten / + =)
awk -v domain="$DOMAIN" -v email="$EMAIL" -v secret="$SECRET" -v enckey="$ENCKEY" -v pg="$PGPASS" -v gpg="$GPGPASS" '
    /^SM_DOMAIN=/            { print "SM_DOMAIN=" domain; next }
    /^ACME_EMAIL=/           { print "ACME_EMAIL=" email; next }
    /^SM_SECRET_KEY=/        { print "SM_SECRET_KEY=" secret; next }
    /^SM_ENCRYPTION_KEYS=/   { print "SM_ENCRYPTION_KEYS=" enckey; next }
    /^POSTGRES_PASSWORD=/    { print "POSTGRES_PASSWORD=" pg; next }
    /^BACKUP_GPG_PASSPHRASE=/{ print "BACKUP_GPG_PASSPHRASE=" gpg; next }
    /^SM_REQUIRE_2FA_ROLES=/ { print "SM_REQUIRE_2FA_ROLES=admin,schulleitung,sekretariat"; next }
    { print }
' "$ROOT/.env.example" | tr -d '\r' > "$OUT"
chmod 600 "$OUT" 2>/dev/null || true

if grep -q "BITTE_AENDERN" "$OUT"; then
    echo "Hinweis: In $OUT stehen noch Platzhalter (BITTE_AENDERN) – bitte von Hand ersetzen:" >&2
    grep -n "BITTE_AENDERN" "$OUT" >&2
fi

cat <<EOF
$OUT wurde erzeugt (Rechte 600).

Jetzt sichern, GETRENNT vom Server (Passwort-Tresor, Ausdruck im Safe):
  SM_ENCRYPTION_KEYS    schützt Nachrichten, Atteste und Dateien
  BACKUP_GPG_PASSPHRASE entschlüsselt die Backups
Ohne diese beiden Werte ist eine Wiederherstellung nicht möglich.

Nächste Schritte: SMTP-Zugang in $OUT eintragen (Abschnitt E-Mail), dann
  docker compose run --rm app python -m schulmanager.server.cli check-config
  docker compose up -d
Das Einmalpasswort des Erst-Administrators steht danach im Log:
  docker compose logs app | grep ERST-ADMIN
EOF
