# Schulmanager – Betriebshandbuch

Dieses Handbuch richtet sich an die IT-Betreuung der Schule bzw. des Schulträgers. Es beschreibt
Installation, Updates, Datensicherung, Überwachung und Fehlersuche. Datenschutz und Härtung stehen in
[`SICHERHEIT.md`](SICHERHEIT.md).

**Inhalt**

1. [Überblick](#1-überblick)
2. [Systemvoraussetzungen](#2-systemvoraussetzungen)
3. [Installation mit Docker in 10 Schritten](#3-installation-mit-docker-in-10-schritten)
4. [Installation ohne Docker (systemd + nginx)](#4-installation-ohne-docker-systemd--nginx)
5. [Erststart: Admin, Demo, Daten](#5-erststart-admin-demo-daten)
6. [Updates](#6-updates)
7. [Backup & Restore](#7-backup--restore)
8. [Monitoring & Alarme](#8-monitoring--alarme)
9. [Logs](#9-logs)
10. [Skalierung & Grenzen](#10-skalierung--grenzen)
11. [Hochverfügbarkeit](#11-hochverfügbarkeit)
12. [Troubleshooting](#12-troubleshooting)
13. [Referenz: Dateien, Befehle, Variablen](#13-referenz-dateien-befehle-variablen)

---

## 1. Überblick

```
                Internet (HTTPS 443 TCP/UDP, HTTP 80 → Weiterleitung)
                                   │
                         ┌─────────▼─────────┐
   Netz "web"            │ caddy             │  Let's Encrypt, HSTS, Security-Header,
                         │ (Reverse Proxy)   │  zstd/gzip, SSE ungepuffert, /metrics gesperrt
                         └─────────┬─────────┘
                                   │ http://app:8000
                         ┌─────────▼─────────┐
                         │ app               │  FastAPI + React-SPA, 1 Prozess/1 Worker,
                         │ (uvicorn)         │  Planungsdaten im Speicher, Live-Updates (SSE)
                         └───┬───────────┬───┘
   Netz "backend"            │           │            Netz "monitoring"
   (intern, kein Internet)   │           └──────────► prometheus ──► grafana   (Profil monitoring)
                    ┌────────▼───────┐
                    │ db             │◄──── backup (pg_dump nachts, Rotation 14/8/12,
                    │ PostgreSQL 16  │       optional GPG + Offsite via rclone)
                    └────────────────┘
```

| Dienst | Image | Aufgabe | von außen erreichbar |
|---|---|---|---|
| `app` | `schulmanager` (eigener Build oder GHCR) | Anwendung + Weboberfläche | nein (nur über Caddy) |
| `db` | `postgres:16-alpine` | Datenbank | nein (internes Netz) |
| `caddy` | `caddy:2.11-alpine` | HTTPS, Zertifikate, Header | ja: 80, 443 (TCP+UDP) |
| `backup` | `schulmanager-backup` (eigener Build) | Datenbank-Backups | nein |
| `prometheus`, `grafana` | Profil `monitoring` | Metriken, Dashboard, Alarme | nur `127.0.0.1` |
| `uptime-kuma` | Profil `uptime` | Erreichbarkeit, Benachrichtigungen | nur `127.0.0.1` |

Daten liegen in Docker-Volumes (`pgdata`, `app_data`, `caddy_data`, …) und die Backups in `./backups`
(bzw. `BACKUP_HOST_DIR`).

---

## 2. Systemvoraussetzungen

### Größenordnung (≈ 2500 Schüler, ≈ 200 Lehrkräfte, 2 Standorte)

| Ressource | Minimum | Empfohlen | Bemerkung |
|---|---|---|---|
| vCPU | 2 | 4 | Normalbetrieb braucht wenig CPU. Der **Stundenplan-Generator** rechnet `SM_GENERATE_TIME_LIMIT` Sekunden (Default 30, sinnvoll bis 300) und nutzt dabei mehrere Kerne (mehrere Läufe parallel, bester gewinnt). Mehr Kerne = bessere Pläne in gleicher Zeit. |
| RAM | 4 GB | 4–8 GB | App ≈ 0,3–1 GB (Planungsdokument + Caches im Speicher), PostgreSQL ≈ 0,5–1 GB, Caddy/Backup < 0,3 GB. Monitoring-Profil zusätzlich ≈ 1 GB. |
| Platte | 20 GB SSD | 40 GB SSD | Datenbank wenige 100 MB (Versionen des Planungsdokuments, Audit-Log), Backups: 14 + 8 + 12 Stände, Docker-Images ≈ 2 GB. |
| Netz | – | – | Feste öffentliche IPv4 (und gern IPv6), DNS-Eintrag, Ports 80/443 eingehend; ausgehend: Let's Encrypt, SMTP, ggf. Offsite-Speicher. |

**Kurz: 2 vCPU / 4 GB RAM reichen für den Betrieb einer Schule dieser Größe.** Wer häufig neue
Stundenpläne mit langen Laufzeiten erzeugt, gönnt der VM 4 vCPU – während der Generator läuft, bleibt die
Weboberfläche bedienbar, da er in eigenen Prozessen rechnet.

### Software

* Linux-Server (Debian 12/13, Ubuntu 22.04/24.04 LTS oder vergleichbar), 64 Bit (amd64 oder arm64)
* Docker Engine ≥ 24 mit Compose-Plugin **≥ 2.24** (`docker compose version`)
* Für die Installation ohne Docker: Python 3.11/3.12, Node.js 22 (nur zum Bauen), PostgreSQL 16, nginx, certbot
* Hosting möglichst in Deutschland/EU mit Auftragsverarbeitungsvertrag (siehe [`SICHERHEIT.md`](SICHERHEIT.md))

---

## 3. Installation mit Docker in 10 Schritten

1. **Server vorbereiten** – Updates einspielen, Zeitsynchronisation prüfen (`timedatectl` → *synchronized: yes*,
   wichtig für 2FA-Codes), Firewall öffnen für 22 (nur Admin-Netze), 80/tcp, 443/tcp, 443/udp:
   ```bash
   apt update && apt full-upgrade -y && apt install -y git make ufw unattended-upgrades
   ufw allow from <admin-netz> to any port 22 proto tcp
   ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp && ufw enable
   ```
2. **Docker installieren** (offizielles Repository, siehe docs.docker.com) und prüfen:
   ```bash
   docker version && docker compose version   # Compose ≥ 2.24
   ```
3. **DNS einrichten** – A-Record (und AAAA, falls IPv6) für z. B. `plan.meine-schule.de` auf die Server-IP.
   Prüfen: `dig +short plan.meine-schule.de`.
4. **Code holen**:
   ```bash
   git clone https://github.com/<organisation>/<repository>.git /opt/schulmanager
   cd /opt/schulmanager
   ```
5. **Konfiguration anlegen**:
   ```bash
   cp .env.example .env && chmod 600 .env
   sed -i "s|^SM_SECRET_KEY=.*|SM_SECRET_KEY=$(openssl rand -hex 32)|" .env
   sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')|" .env
   nano .env   # SM_DOMAIN, ACME_EMAIL, SM_ADMIN_PASSWORD, SMTP, Backup-Verschlüsselung …
   ```
   Pflicht: `SM_DOMAIN`, `ACME_EMAIL`, `SM_SECRET_KEY`, `POSTGRES_PASSWORD`, für den Erststart
   `SM_ADMIN_PASSWORD` (≥ 10 Zeichen). Dringend empfohlen: `BACKUP_GPG_PASSPHRASE`.
6. **Konfiguration prüfen**: `make config` (bzw. `docker compose config`) – zeigt fehlende Pflichtwerte an.
7. **Starten** (baut die Images beim ersten Mal, 3–8 Minuten):
   ```bash
   make up            # = docker compose up -d --build
   ```
   Alternativ fertige Images aus der GitHub Container Registry: in `.env`
   `SM_IMAGE=ghcr.io/<org>/<repo>:<version>` und `SM_BACKUP_IMAGE=ghcr.io/<org>/<repo>-backup:<version>`,
   dann `docker compose pull && docker compose up -d`.
8. **Status prüfen** – alle Dienste `healthy`, Zertifikat ausgestellt:
   ```bash
   make ps
   make logs SERVICE=caddy        # "certificate obtained successfully"
   scripts/healthcheck.sh https://plan.meine-schule.de
   ```
9. **Anmelden** unter `https://plan.meine-schule.de` mit `SM_ADMIN_USER`/`SM_ADMIN_PASSWORD`, sofort
   **2FA einrichten** (Profil → Zwei-Faktor) und danach `SM_ADMIN_PASSWORD` in `.env` wieder leeren.
10. **Datensicherung verifizieren** – der Backup-Dienst sichert beim Start und täglich um 02:30:
    ```bash
    make backup-list
    make restore-test FILE=backups/daily/<neueste-datei>.dump
    ```
    Optional Monitoring starten: `GRAFANA_ADMIN_PASSWORD` setzen, `make monitoring-up` (Abschnitt 8).

> **Testinstallation ohne Domain:** `SM_DOMAIN=localhost` – Caddy erzeugt ein selbstsigniertes Zertifikat.
> Für eine schlanke Variante ohne PostgreSQL (Schulung/Demo): `docker compose -f docker-compose.sqlite.yml up -d`.

---

## 4. Installation ohne Docker (systemd + nginx)

Für Umgebungen, in denen Docker nicht erlaubt ist. Beispiel Debian 12/Ubuntu 24.04.

```bash
# 1. Pakete (PostgreSQL 16 ggf. aus apt.postgresql.org, Node.js 22 aus nodesource o. ä.)
apt install -y python3 python3-venv postgresql-16 postgresql-client-16 nginx certbot python3-certbot-nginx git make
# Node.js 22 nur zum Bauen des Frontends nötig

# 2. Systembenutzer und Verzeichnisse
useradd --system --home /opt/schulmanager --shell /usr/sbin/nologin schulmanager
git clone https://github.com/<organisation>/<repository>.git /opt/schulmanager
install -d -o schulmanager -g schulmanager -m 0750 /var/lib/schulmanager /var/lib/schulmanager/backups-db

# 3. Python-Umgebung und Frontend
cd /opt/schulmanager
python3 -m venv .venv && .venv/bin/pip install --upgrade pip \n  && .venv/bin/pip install --require-hashes --no-deps -r requirements.lock && .venv/bin/pip install --no-deps .
(cd frontend && npm ci && npm run build)

# 4. Datenbank
sudo -u postgres createuser --pwprompt schulmanager
sudo -u postgres createdb --owner schulmanager --encoding UTF8 schulmanager

# 5. Konfiguration
install -D -m 0640 -o root -g schulmanager .env.example /etc/schulmanager/schulmanager.env
nano /etc/schulmanager/schulmanager.env
#   SM_DATABASE_URL=postgresql+psycopg://schulmanager:<pw>@127.0.0.1:5432/schulmanager
#   SM_SECRET_KEY=<openssl rand -hex 32>, SM_BASE_URL=https://plan.meine-schule.de, SM_ADMIN_PASSWORD=…
#   (Abschnitte 6, 10–12 der Datei werden ohne Docker nicht benötigt)
#   systemd liest Kommentare nur am Zeilenanfang – nie „WERT   # Kommentar“ schreiben

# 6. Dienst
cp deploy/systemd/schulmanager.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now schulmanager
journalctl -u schulmanager -f          # "Uvicorn running on http://127.0.0.1:8000"

# 7. Reverse Proxy + Zertifikat
cp deploy/nginx/schulmanager.conf /etc/nginx/sites-available/schulmanager.conf
sed -i 's/plan.example.org/plan.meine-schule.de/g' /etc/nginx/sites-available/schulmanager.conf
certbot certonly --nginx -d plan.meine-schule.de
ln -s /etc/nginx/sites-available/schulmanager.conf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 8. Backups (Timer täglich 02:30)
cp deploy/systemd/schulmanager-backup.{service,timer} /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now schulmanager-backup.timer
systemctl start schulmanager-backup.service && ls -R /var/lib/schulmanager/backups-db
```

Hinweise:

* Die nginx-Vorlage enthält bereits SSE-Einstellungen (`proxy_buffering off`, lange `proxy_read_timeout`),
  ein Login-Rate-Limit (`limit_req`), Security-Header, ein Access-Log ohne iCal-Tokens und liefert
  `/assets/` direkt von der Platte aus (Pfad in der Vorlage an `SM_FRONTEND_DIST` anpassen).
* `X-Forwarded-For` wird von nginx **überschrieben** (`$remote_addr`), damit Clients ihre IP nicht fälschen
  können; die App läuft mit `SM_TRUST_PROXY=1`.
* `pg_dump` muss zur Server-Version passen (16). Für Offsite-Kopien `rclone` und für Verschlüsselung `gpg`
  installieren; Konfiguration wie im Docker-Betrieb über die `BACKUP_*`-Variablen in der Env-Datei.
* Update: `git pull`, `.venv/bin/pip install --require-hashes --no-deps -r requirements.lock && .venv/bin/pip install --no-deps .`, Frontend neu bauen, `systemctl restart schulmanager`
  (Migrationen laufen per `ExecStartPre`).

---

## 5. Erststart: Admin, Demo, Daten

### Admin-Konto

* Automatisch beim ersten Start aus `SM_ADMIN_USER`/`SM_ADMIN_PASSWORD` (nur, wenn noch kein Admin existiert).
* Jederzeit über die CLI (auch zum Zurücksetzen vergessener Passwörter):
  ```bash
  make create-admin ADMIN=schulleitung              # Passwort wird abgefragt
  scripts/create-admin.sh --compose --update -u admin   # vorhandenes Konto wieder zum Admin machen
  scripts/create-admin.sh --compose --temp -u admin     # Startpasswort erzeugen (Wechsel erzwungen)
  docker compose exec app schulmanager-admin list-users # Konten mit Flags (2fa, inaktiv, pw-wechsel)
  docker compose exec app schulmanager-admin unlock --username <name>       # Login-Sperre aufheben
  docker compose exec app schulmanager-admin disable-2fa --username <name>  # verlorenes 2FA-Gerät
  ```
  Ohne Docker: dieselben Befehle mit `/opt/schulmanager/.venv/bin/schulmanager-admin …` als Benutzer
  `schulmanager` und geladener Env-Datei (`scripts/create-admin.sh` erledigt das automatisch).

### Betriebsmodus `SM_MODE`

`SM_MODE=production` (Echtbetrieb), `demo` (Vorführung) oder `development` (lokal). Im Echtbetrieb sind alle Demo-Funktionen aus
(*Demo laden*, `cli load-demo`, `SM_LOAD_DEMO`, Demo-Zugänge) und der Start bricht mit einer Liste ab, wenn Pflichtwerte fehlen oder
Beispielwerte stehen (`python -m schulmanager.server.cli check-config` prüft ohne Start). Ohne `SM_MODE` gilt wie bisher `SM_ENV`.
Komplette Anleitung: [`INSTALLATION.md`](INSTALLATION.md); Status und Fehlerprotokoll: Menü *Betrieb*.

### Demo-Schule (nur Test/Schulung, nicht im Echtbetrieb)

* `SM_LOAD_DEMO=1` beim allerersten Start → Demo (≈ 2600 Schüler, 98 Klassen, 2 Standorte) wird im
  Hintergrund erzeugt, die Oberfläche ist sofort erreichbar.
* In einen laufenden Stack: `make demo-docker` (überschreibt die Planungsdaten, startet die App neu) oder
  in der Oberfläche *Administration → System → Demo laden*.
* Demo-Konten (Passwort `demo123456`): `schulleitung`, `planer`, `sekretariat`, `lehrer1`–`lehrer3`,
  `schueler1`–`schueler3`, `eltern1`, `monitor`. **Niemals in einer Produktivinstanz verwenden.**
* Lokale Entwicklung: `make demo` (frische SQLite-Datenbank mit Demo, Backend :8000, Frontend :5173).

### Echte Daten

Empfohlene Reihenfolge: Einstellungen (Zeitraster, Schuljahr, Unterrichtstage, Standorte, Wegezeiten) → Stammdaten per
Import (Untis GPU, CSV aus SchILD-NRW/ASV/LUSD/Magellan) → Stundentafeln → Kurse/Kopplungen → Lehrkräfte
zuordnen → Generator → Konten per Massenanlage (Zugangsbriefe drucken) → Monitore einrichten.

---

## 6. Updates

### Docker (Quellcode-Checkout)

```bash
cd /opt/schulmanager
make update
#  = Backup mit Label "vor-update" → git pull --ff-only → Images neu bauen
#    → Container neu starten (Migrationen laufen automatisch) → Healthcheck
```

### Docker (Images aus GHCR)

```bash
docker compose exec -T backup backup.sh --label vor-update
sed -i 's|^SM_IMAGE=.*|SM_IMAGE=ghcr.io/<org>/<repo>:1.3.0|' .env      # neue Version
sed -i 's|^SM_BACKUP_IMAGE=.*|SM_BACKUP_IMAGE=ghcr.io/<org>/<repo>-backup:1.3.0|' .env
git pull --ff-only          # Compose-/Caddy-/Prometheus-Dateien der neuen Version
docker compose pull && docker compose up -d --remove-orphans
docker compose exec -T app /app/scripts/healthcheck.sh --wait 240
```

### Ablauf und Hinweise

* **Zeitpunkt:** außerhalb der Unterrichtszeit (Vertretungsplan wird morgens intensiv genutzt), ideal
  nachmittags/abends. Die Unterbrechung dauert typischerweise 10–30 Sekunden; Caddy hält Anfragen bis
  15 s zurück und zeigt sonst eine Wartungsseite mit automatischem Neuladen.
* **Migrationen** laufen beim Start (`scripts/migrate.sh`, idempotent). Schlägt eine Migration fehl,
  startet die App nicht – Logs prüfen (`make logs SERVICE=app`).
* **Rollback:** vorheriges Image-Tag in `.env` eintragen (bzw. `git checkout <tag>` + `make up`). Wurde die
  Datenbank bereits migriert, zusätzlich das Backup `manual/…_vor-update.dump` zurückspielen (Abschnitt 7).
* **Basis-Images** (Python, Node, PostgreSQL-Minor, Caddy) erhalten Sicherheitsupdates über regelmäßige
  Neu-Builds: monatlich `docker compose build --pull && docker compose up -d`.
* **PostgreSQL-Major-Wechsel** (z. B. 16 → 17) nie durch einfaches Ändern des Tags: Backup erstellen, Stack
  stoppen, Volume `pgdata` umbenennen/sichern, `POSTGRES_VERSION=17` setzen, Stack starten, Backup einspielen.
* Docker selbst und das Betriebssystem: `unattended-upgrades` für Sicherheitsupdates, Neustarts planen.
* **Umgebungsvariablen (ab Runde 2):** `docker-compose.yml` reicht jetzt **alle** in `.env.example` dokumentierten
  `SM_*`-Variablen aus `.env` an die App weiter (u. a. `SM_REQUIRE_2FA_ROLES`, `SM_SMS_*`, `SM_SSO_*`,
  `SM_AUTH_CODE_MINUTES`, `SM_LETTER_BATCH_MINUTES`). Wer diese Werte bisher in `app.env` stehen hatte: in `.env`
  übernehmen – die Einträge unter `environment:` haben Vorrang vor `app.env`. Prüfen mit
  `docker compose config | grep -E 'SM_(REQUIRE_2FA|SMS|SSO)'`.

---

## 7. Backup & Restore

### Was wird gesichert?

| Art | Inhalt | Werkzeug | Datei |
|---|---|---|---|
| `pg` | komplette PostgreSQL-Datenbank (Planungsdokument mit Versionen, Konten, Audit-Log, Mitteilungen, Krankmeldungen, Outbox) | `pg_dump -Fc` | `schulmanager_pg_<Zeit>.dump` |
| `sqlite` | SQLite-Datenbank (SQLite-Variante) | Online-Backup-API + Integritätsprüfung | `schulmanager_sqlite_<Zeit>.db.gz` |
| `files` | Datenverzeichnis der App ohne Datenbankdateien, App-Backups und ohne das Zielverzeichnis der Sicherung (`BACKUP_DIR`, falls es im Datenverzeichnis liegt – z. B. systemd `/var/lib/schulmanager/backups-db`) | `tar` | `schulmanager_files_<Zeit>.tar.gz` |

Zu jeder Datei gehört eine `.sha256`-Prüfsumme. Mit `BACKUP_GPG_PASSPHRASE` werden alle Dateien mit
GPG (AES-256) verschlüsselt (`*.gpg`). **Ohne Passphrase ist kein Restore möglich – getrennt vom Server
aufbewahren (Tresor, Passwortmanager der Schulleitung).**

Nicht gesichert werden müssen: Docker-Images (reproduzierbar), Caddy-Zertifikate (werden neu ausgestellt),
Prometheus-/Grafana-Daten (optional). Die `.env` sichern Sie **getrennt und verschlüsselt** (enthält
Zugangsdaten).

### Zeitplan und Rotation

* Täglich um `BACKUP_TIMES` (Default `02:30`, mehrere Zeiten möglich, z. B. `"02:30 12:45"`) und beim
  Start des Backup-Containers.
* Aufbewahrung: **14 Tage** (`daily/`), **8 Wochen** (`weekly/`, erstes Backup je ISO-Woche),
  **12 Monate** (`monthly/`, erstes Backup je Monat); `manual/` (vor Updates/Restores) die letzten 10.
* Wochen-/Monatsstände sind Hardlinks – sie belegen keinen zusätzlichen Platz.
* Gesundheitszustand: Der Container `backup` wird *unhealthy*, wenn das letzte erfolgreiche Backup älter
  als `BACKUP_MAX_AGE_HOURS` (26 h) ist. Zusätzlich können `BACKUP_PING_URL`/`BACKUP_PING_URL_FAIL`
  (Uptime-Kuma *Push*-Monitor, Healthchecks.io) aufgerufen werden.

### Offsite-Kopie (3-2-1-Regel)

`BACKUP_RCLONE_REMOTE=offsite:<bucket>/<pfad>` plus `RCLONE_CONFIG_OFFSITE_*` (Beispiele für S3, SFTP,
WebDAV/Nextcloud in `.env.example`). Nach jedem Backup spiegelt `rclone sync` die Ablage (`BACKUP_RCLONE_MODE=copy`
löscht offsite nie). Empfehlungen: Anbieter in DE/EU mit AV-Vertrag, Verschlüsselung aktivieren, Bucket mit
**Versionierung/Object Lock** (Schutz vor Ransomware, die auch die Offsite-Kopie löschen will), eigener
Zugangsschlüssel nur mit Schreibrecht auf diesen Bucket.

### Manuelles Backup

```bash
make backup                                   # → backups/manual/…_manuell.dump
make backup-list
make backup-verify FILE=backups/daily/schulmanager_pg_2026-10-05_023000.dump
```

Die App bietet zusätzlich eigene Sicherungen (*Administration → System → Backups*, JSON bzw. SQLite-Datei,
`SM_BACKUP_DIR`, optional automatisch mit `SM_AUTO_BACKUP_HOURS`). Sie sind praktisch zum Herunterladen,
ersetzen aber nicht die Datenbank-Backups des Sidecars.

### Restore (Docker)

```bash
make restore FILE=backups/daily/schulmanager_pg_2026-10-05_023000.dump
```

Ablauf (`scripts/restore.sh --compose`): Sicherheitsabfrage (Eingabe `WIEDERHERSTELLEN`) → Datei in den
Backup-Container kopieren → **App stoppen** (sie hält die Planungsdaten im Speicher) → Sicherheits-Backup
des aktuellen Stands (`manual/…_vor-restore.dump`) → Prüfsumme prüfen, ggf. entschlüsseln → das Schema
wird in **einer Transaktion** ersetzt (bei Fehlern bleibt alles unverändert) → App starten → Healthcheck.
Danach migriert die App ein älteres Backup automatisch auf den aktuellen Stand.

SQLite-Variante: identisch (`COMPOSE="docker compose -f docker-compose.sqlite.yml" make restore FILE=…`);
die alte Datei bleibt als `schulmanager.db.vor-restore-<Zeit>` liegen.

Datenverzeichnis (`schulmanager_files_*.tar.gz`): `docker compose cp <datei> backup:/tmp/` und
`docker compose exec backup restore.sh /tmp/<datei>`.

### Restore ohne Docker

```bash
systemctl stop schulmanager
sudo -u schulmanager bash -c 'set -a; . /etc/schulmanager/schulmanager.env; set +a; \
  BACKUP_DIR=/var/lib/schulmanager/backups-db /opt/schulmanager/scripts/restore.sh <datei>'
systemctl start schulmanager
# oder in einem Schritt: … restore.sh --stop-cmd "systemctl stop schulmanager" --start-cmd "systemctl start schulmanager" <datei>
```

### Test-Restore (monatlich, Pflicht!)

Ein Backup ist erst etwas wert, wenn die Wiederherstellung geprobt ist.

```bash
make restore-test FILE=backups/monthly/schulmanager_pg_2026-10.dump
# Docker: spielt den Dump in eine temporäre Datenbank "schulmanager_restore_test" ein,
#         zählt die Planversionen und löscht die Test-Datenbank wieder. Live-Daten bleiben unberührt.
```

Zusätzlich halbjährlich einen **vollständigen Probe-Restore** auf einer separaten VM durchführen
(Installation nach Abschnitt 3, Backup einspielen, Anmeldung und Vertretungsplan prüfen) und das Ergebnis
dokumentieren (Datum, Backup-Datei, Dauer, Ergebnis, Name) – das ist Teil der TOMs.

### Wiederherstellung auf neuem Server (Disaster Recovery)

1. Neuen Server nach Abschnitt 3, Schritte 1–6 vorbereiten, **dieselbe `.env`** verwenden (aus der getrennten
   Sicherung; insbesondere `SM_SECRET_KEY`, sonst sind Sitzungen/API-Tokens ungültig – unkritisch).
2. Backups aus der Offsite-Kopie holen: `rclone copy offsite:<pfad> ./backups`.
3. `docker compose up -d db backup` und `make restore FILE=backups/daily/<neueste>.dump` (die App wird
   dabei gestartet).
4. DNS auf die neue IP umstellen; Caddy holt neue Zertifikate.

Richtwerte: **RPO** (max. Datenverlust) = Abstand der Backups (Standard 24 h, mit zwei Zeiten ≈ 12 h);
**RTO** (Wiederanlauf) ≈ 1 h mit vorbereitetem Server.

---

## 8. Monitoring & Alarme

### Bordmittel (immer aktiv)

* **`/healthz`** (ohne Anmeldung): `{"status":"ok","db":"ok","version":…,"plan_version":…}`, HTTP 503 bei
  Datenbankproblemen. Prüfen: `scripts/healthcheck.sh https://plan.meine-schule.de`.
* **Docker-Healthchecks** für `app`, `db`, `caddy`, `backup` – `make ps` zeigt `healthy/unhealthy`;
  `restart: unless-stopped` startet abgestürzte Container neu.
* **Backup-Überwachung** über den Healthcheck des Backup-Containers und optionale Ping-URLs.

### Prometheus + Grafana (Profil `monitoring`)

```bash
# .env: GRAFANA_ADMIN_PASSWORD=…, ALERT_EMAIL=…, optional GRAFANA_SMTP_ENABLED=true + GRAFANA_SMTP_HOST=host:587
make monitoring-up
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 admin@server   # vom Admin-PC
# → http://localhost:3000  (Grafana)   http://localhost:9090  (Prometheus)
```

Prometheus scrapt `app:8000/metrics` im internen Netz (von außen sperrt Caddy `/metrics`). Das Dashboard
**„Schulmanager – Überblick“** wird automatisch provisioniert:

| Bereich | Inhalt |
|---|---|
| Überblick | Status, Anfragen/s, Fehlerquote 5xx, Latenz p95, Live-Clients (SSE), laufende Jobs, Planversion |
| HTTP | Anfragen nach Status, Latenz p50/p95/p99, langsamste und meistgenutzte Routen |
| Live-Betrieb & Sicherheit | SSE-Verbindungen (Vertretungsplan-Seiten, Monitore), Fehlanmeldungen, Jobs |
| Konten & Prozess | aktive Sitzungen, Konten je Rolle, Speicher (RSS), CPU, offene Dateien |

**Alarme** (Grafana, E-Mail an `ALERT_EMAIL`, Kontaktpunkt `schulmanager-admins`): *nicht erreichbar*
(2 min), *Fehlerquote > 5 %* (10 min), *p95 > 2 s* (15 min). Dieselben Regeln plus *Speicher > 2,5 GB* und
*viele Fehlanmeldungen* stehen in `deploy/prometheus/alerts.yml` (sichtbar in Prometheus unter *Alerts*).
Weitere Kanäle (Matrix, Teams, Telegram, Signal-Gateway) in Grafana unter *Alerting → Contact points*.

Wichtige Metriken: `schulmanager_http_requests_total{method,route,status}`,
`schulmanager_http_request_duration_seconds` (Histogramm), `schulmanager_sse_clients`,
`schulmanager_jobs_running`, `schulmanager_school_version`, `schulmanager_login_failures_total`,
`schulmanager_sessions_active`, `schulmanager_users{role,active}`, `process_resident_memory_bytes`.
Optional schützt `SM_METRICS_TOKEN` den Endpunkt zusätzlich (dann in `prometheus.yml` `authorization`
mit `credentials_file` ergänzen).

### Uptime-Kuma (Profil `uptime`) – Sicht von außen

```bash
make uptime-up && ssh -L 3001:127.0.0.1:3001 admin@server   # → http://localhost:3001
```

Empfohlene Monitore:

1. **HTTP(s) – Keyword** auf `https://plan.meine-schule.de/healthz`, Keyword `"status":"ok"`, Intervall 60 s.
2. **Zertifikatsablauf** (Option im HTTP-Monitor, Warnung 14 Tage vorher).
3. **Push-Monitor „Backup“**, Intervall 25 h → URL als `BACKUP_PING_URL` eintragen.
4. Benachrichtigung per E-Mail/Matrix/Telegram an IT-Betreuung **und** Schulleitung (Vertretungsplan ist
   morgens geschäftskritisch).

Besser noch: Uptime-Kuma bzw. ein externer Dienst auf einem **anderen** Server, damit ein Totalausfall
überhaupt gemeldet werden kann.

---

## 9. Logs

```bash
make logs                    # alle Dienste
make logs SERVICE=app        # nur die App
docker compose logs --since 2h app | jq -r 'select(.level=="ERROR")'   # Fehler der letzten 2 h
```

* **App**: JSON-Zeilen (`SM_LOG_FORMAT=json`) mit `ts`, `level`, `logger`, `msg`, `request_id`; das
  Zugriffsprotokoll (`schulmanager.access`) enthält Methode, Pfad, Status, Dauer und die **gekürzte** Client-IP
  (IPv4 /24, IPv6 /48; iCal-Tokens maskiert). Jede Antwort trägt einen `X-Request-ID`-Header – damit lassen sich
  Fehlermeldungen von Nutzern im Log finden.
* **Caddy**: JSON-Access-Log; Cookies/Authorization automatisch geschwärzt, iCal-Tokens maskiert,
  **IP-Adressen gekürzt** (IPv4 /24, IPv6 /48).
* **Rotation**: Docker `json-file` mit `LOG_MAX_SIZE` × `LOG_MAX_FILES` (Default 10 MB × 5, komprimiert)
  je Container – damit ist auch die Aufbewahrungsdauer begrenzt (DSGVO: Logs mit IP-Adressen nur so lange
  wie nötig, i. d. R. ≤ 14 Tage). Die Rotation ist nur größenbasiert; wer die 14 Tage nachweisen muss, setzt
  `LOG_MAX_SIZE`/`LOG_MAX_FILES` passend zum Verkehr oder nutzt journald (`MaxRetentionSec=14d`).
* **Audit-Log** (fachlich: wer hat was geändert) in der Datenbank: *Administration → Audit* bzw.
  `GET /api/v1/audit`.
* Ohne Docker: `journalctl -u schulmanager` (Aufbewahrung über `journald.conf`, z. B. `MaxRetentionSec=14d`),
  nginx unter `/var/log/nginx/schulmanager.*.log` (logrotate).
* Zentrales Logging (Loki, Graylog, …): Docker-Logging-Treiber in `x-logging` von `docker-compose.yml` anpassen.

---

## 10. Skalierung & Grenzen

### Warum genau ein Prozess?

Der Schulmanager hält das komplette Planungsdokument (Stammdaten, Stundenplan, Abwesenheiten) **im Speicher**
eines Prozesses (`SchoolStore`) und verteilt Live-Änderungen über **Server-Sent Events** aus diesem Prozess.
Mehrere uvicorn-Worker oder mehrere Container hätten jeweils eigene Kopien und eigene Event-Busse: Eine
Änderung in Worker A würde bei Clients, die an Worker B hängen, nicht live ankommen. Deshalb:

* `SM_WORKERS=1` (Image, Compose und systemd setzen das; der Entrypoint warnt bei größeren Werten),
* **keine** horizontale Skalierung hinter einem Load-Balancer,
* stattdessen **vertikal skalieren**: mehr CPU (Generator) bzw. RAM (große Schulen, viele Versionen).

Das ist für eine Schule kein Engpass: Lesezugriffe werden aus dem Speicher bzw. aus Caches beantwortet
(z. B. `/me/today` in wenigen Millisekunden), uvicorn arbeitet asynchron und hält tausende gleichzeitige
SSE-Verbindungen (Monitore, geöffnete Vertretungspläne). Der Generator läuft in eigenen Prozessen und
blockiert die Oberfläche nicht.

### Stellschrauben

| Engpass | Maßnahme |
|---|---|
| Generator dauert lange / Plan zu viele Hohlstunden | mehr vCPU, `SM_GENERATE_TIME_LIMIT` (bzw. Laufzeit in der Oberfläche) erhöhen |
| Speicher | `APP_MEMORY` (Container-Limit, Default 3 GB), `SM_KEEP_VERSIONS` verringern |
| Datenbank | `PG_SHARED_BUFFERS` (≈ 25 % RAM), `PG_EFFECTIVE_CACHE_SIZE` (≈ 75 % RAM) |
| Viele Clients morgens | Caddy/uvicorn skalieren problemlos; ggf. `ulimit`/`LimitNOFILE` prüfen |
| Mehrere Schulen | **eine Instanz je Schule** (eigenes Verzeichnis + `COMPOSE_PROJECT_NAME`, eigene Domain) – auch aus Datenschutzgründen (Trennungsgebot) |

---

## 11. Hochverfügbarkeit

Ein aktiver Zweitbetrieb (Active/Active) ist wegen des In-Memory-Designs nicht vorgesehen. Bewährte Optionen:

| Stufe | Aufbau | RTO | RPO | Aufwand |
|---|---|---|---|---|
| 0 – Standard | 1 VM, nächtliche Backups + Offsite | ≈ 1–4 h | ≤ 24 h | gering |
| 1 – Häufigere Backups | `BACKUP_TIMES="02:30 07:15 12:45 16:00"`, Hoster-Snapshots der VM | ≈ 1 h | ≤ 4–5 h | gering |
| 2 – Cold Standby | Zweite VM (anderes Rechenzentrum) mit identischer Installation, gestoppt; Offsite-Backups werden regelmäßig dort eingespielt (Test-Restore!), DNS-Umschaltung manuell (kurze TTL) | ≈ 15–30 min | ≤ Backup-Intervall | mittel |
| 3 – Warm Standby | PostgreSQL-Streaming-Replikation auf Zweit-VM (eigener Compose-Stack mit Replica), App dort gestoppt; im Fehlerfall Replica *promoten*, App starten, DNS/Floating-IP umschalten | ≈ 5–15 min | Sekunden | hoch |

Ergänzend: Floating IP/Failover-IP des Hosters statt DNS-Umschaltung, Monitoring von außen (Abschnitt 8),
dokumentiertes Notfallhandbuch inkl. Kontaktliste. Für die Unterrichtsorganisation hilft zusätzlich ein
**Notfallausdruck**: Vertretungsplan des Tages und Stundenpläne als PDF (Druckansichten) morgens ablegen.

---

## 12. Troubleshooting

| Symptom | Ursache / Prüfung | Lösung |
|---|---|---|
| Kein Zertifikat, Browser-Warnung | `make logs SERVICE=caddy` → ACME-Fehler; DNS zeigt nicht auf Server, Port 80/443 zu, Let's-Encrypt-Rate-Limit | DNS/Firewall korrigieren, `docker compose restart caddy`; zum Testen `ACME_CA` auf Staging |
| `502`/Wartungsseite | App startet nicht: `make logs SERVICE=app` | Fehler beheben (siehe folgende Zeilen), `make restart` |
| `SM_SECRET_KEY muss in Produktion gesetzt sein` / `zu kurz` | `.env` | `openssl rand -hex 32` eintragen, `make up` |
| `Datenverzeichnis … nicht beschreibbar` | Volume-Rechte (z. B. nach manuellem Kopieren) | `docker compose run --rm --no-deps --user root --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER app chown -R 10001:10001 /app/data` |
| App `unhealthy`, `db: error` | PostgreSQL down/voll: `make logs SERVICE=db`, `df -h` | Platz schaffen, `docker compose restart db` |
| `POSTGRES_PASSWORD … not specified` | Passwort fehlt in `.env` | setzen; bei bereits initialisiertem Volume muss es zum bestehenden Passwort passen |
| Passwort der DB geändert, App verbindet nicht | PostgreSQL übernimmt `POSTGRES_PASSWORD` nur bei der Erstinitialisierung | `docker compose exec db psql -U schulmanager -c "ALTER USER schulmanager PASSWORD '…'"` |
| Login: „zu viele Versuche“ (429) | Kontosperre/IP-Sperre | warten (`SM_LOGIN_LOCK_MINUTES`) oder `schulmanager-admin unlock --username …` |
| Admin-Passwort vergessen / 2FA-Gerät verloren | – | `scripts/create-admin.sh --compose --update -u admin` bzw. `schulmanager-admin disable-2fa --username …` |
| 2FA-Codes werden abgelehnt | Serverzeit falsch | `timedatectl`, NTP aktivieren |
| Vertretungsplan aktualisiert sich nicht live | SSE wird gepuffert (zusätzlicher Proxy/Firewall mit TLS-Inspektion) | Puffern für `/api/v1/events` abschalten (nginx: `proxy_buffering off`), Proxy-Timeouts ≥ 60 s |
| Hinter weiterem Proxy falsche Client-IPs/Sperren aller Nutzer | Caddy sieht nur die Proxy-IP | im Caddyfile `trusted_proxies` setzen |
| Generator-Job bricht ab / langsam | CPU-/RAM-Limit (`APP_CPUS`, `APP_MEMORY`), `docker stats` | Limits erhöhen, Laufzeit anpassen |
| Backup-Container `unhealthy` | `make logs SERVICE=backup` (Passwort, Platz, Offsite-Zugang) | Ursache beheben, `make backup` |
| `pg_dump: server version mismatch` | `POSTGRES_VERSION` von db und backup unterschiedlich | gleiche Major-Version, `docker compose build backup` |
| Platte voll | `docker system df`, `du -sh backups` | alte Images: `docker image prune`; Rotation verkleinern; Platte vergrößern |
| Falsche Uhrzeiten | `TZ` | `TZ=Europe/Berlin` (Default); Datenbank speichert UTC |
| Restore abgebrochen | Ausgabe prüfen; Datenbank ist unverändert (eine Transaktion) | Ursache beheben, erneut ausführen; App ggf. `make restart` |

Weitere Diagnose: `make shell` (Shell im App-Container), `docker compose exec app schulmanager-admin …`,
`docker compose exec db psql -U schulmanager`, `GET /api/v1/admin/system` (als Admin, Systeminfo).

---

## 13. Referenz: Dateien, Befehle, Variablen

| Datei | Zweck |
|---|---|
| `Dockerfile` | mehrstufig: Frontend-Build (Node 22) → Python 3.12, non-root (UID 10001), Healthcheck, Entrypoint |
| `docker-compose.yml` | Produktion: app, db, caddy, backup; Profile `monitoring`, `uptime` |
| `docker-compose.sqlite.yml` | schlanke Variante ohne PostgreSQL |
| `docker-compose.dev.yml` | Entwicklung: uvicorn `--reload`, Vite-Dev-Server; Profile `postgres`, `mail` (Mailpit) |
| `deploy/Caddyfile`, `deploy/caddy/` | Reverse Proxy; `conf.d/*.caddy` für Ergänzungen; optional Rate-Limit-Plugin |
| `deploy/nginx/schulmanager.conf` | Alternative zu Caddy (ohne Docker) |
| `deploy/systemd/` | `schulmanager.service`, `schulmanager-backup.{service,timer}` |
| `deploy/backup/` | Backup-Sidecar (Image + Zeitsteuerung) |
| `deploy/prometheus/`, `deploy/grafana/` | Scrape-Konfiguration, Alarmregeln, Datenquelle, Dashboard, Grafana-Alarme |
| `scripts/` | `backup.sh`, `restore.sh`, `migrate.sh`, `create-admin.sh`, `healthcheck.sh`, `dev.sh` |
| `.env.example` | alle Variablen mit Erklärung |
| `.github/` | CI (Tests, Lint, Docker-Build), CodeQL, Release nach GHCR, Dependabot |

`make help` listet alle Make-Ziele. Container-Befehle des App-Images:
`schulmanager-entrypoint serve|migrate|create-admin …|cli …|shell` sowie `schulmanager-admin <befehl>`.

---

## 14. Verschlüsselung & Schlüsselverwaltung

Nachrichten, hochgeladene Dateien (inkl. Dateinamen), Atteste und Freitexte werden mit AES-256-GCM verschlüsselt
gespeichert (Hintergrund und Grenzen: `docs/SICHERHEIT.md`, Abschnitt 4.6). Der Master-Schlüssel steht in
`SM_ENCRYPTION_KEYS` – **Pflicht in Produktion**, sonst bricht der Start mit
`SM_ENCRYPTION_KEYS muss in Produktion gesetzt sein` ab (auch `docker compose` verweigert den Start ohne Eintrag).

> **Schlüssel GETRENNT vom Backup sichern!** Backups enthalten die Inhalte nur verschlüsselt. Geht der Schlüssel
> verloren, sind Nachrichten, Dateien und Atteste unwiederbringlich verloren – auch aus allen Backups. Aufbewahrung:
> Passwort-Tresor der Schulleitung **und** versiegelter Ausdruck im Safe; nicht im Backup-Speicher, nicht per E-Mail.

### Ersteinrichtung

```bash
# Schlüssel erzeugen (eine der beiden Varianten)
echo "k1:$(openssl rand -base64 32)"
docker compose run --rm --no-deps app schulmanager-admin gen-key --kid k1   # braucht schon irgendeinen Wert in .env

# in .env eintragen (chmod 600), danach starten
SM_ENCRYPTION_KEYS=k1:<Ausgabe>
make up
docker compose exec app schulmanager-admin crypto-status    # aktive ID + Fingerabdruck (ohne Geheimnis)
```

Den Fingerabdruck aus `crypto-status` mit im Tresor notieren – so lässt sich später ohne Offenlegung prüfen, ob der
richtige Schlüssel eingetragen ist. Ohne Docker: `schulmanager-admin …` bzw. `python -m schulmanager.server.cli …`
mit derselben Umgebung wie der Dienst.

### Schlüsselrotation (z. B. jährlich, bei Personalwechsel, nach Verdacht auf Offenlegung)

1. Vorher ein Backup erstellen (`make backup`).
2. Neuen Schlüssel erzeugen: `docker compose run --rm --no-deps app schulmanager-admin gen-key --kid k2`.
3. In `.env` **vorn** eintragen, den alten dahinter lassen: `SM_ENCRYPTION_KEYS=k2:<neu>,k1:<alt>` – der erste
   verschlüsselt neue Daten, alle weiteren werden nur noch zum Lesen genutzt.
4. Neu starten: `docker compose up -d app`.
5. Alle Datenschlüssel neu wrappen: `docker compose exec app schulmanager-admin rotate-keys`
   (je Bereich, z. B. `stored_files`, Nachrichten, wird die Anzahl ausgegeben; einzeln mit `--only NAME`).
   Die Nutzdaten werden dabei nicht neu geschrieben – das geht auch bei vielen GB Dateien schnell.
6. Prüfen: `schulmanager-admin crypto-status` und `schulmanager-admin verify-files`.
7. Den alten Schlüssel **erst entfernen, wenn alle Backups von vor der Rotation abgelaufen sind** (Backup-Rotation:
   bis 12 Monate → Kalendereintrag). Bis dahin bleibt er im Tresor **und** in `SM_ENCRYPTION_KEYS`.

### Restore, Umzug, Prüfung

* Für ein Restore werden **Datenbank-Backup, Datei-Archiv (`files`) vom selben Zeitpunkt und der Schlüssel** benötigt.
  Der Backup-Sidecar sichert die Dateiablage (`/app/data/files`, verschlüsselt) im `files`-Archiv mit; die App-interne
  Sicherung (Seite *System*, `schulmanager-admin backup`) enthält **nur die Datenbank**.
* Nach Restore oder Umzug: `schulmanager-admin verify-files` entschlüsselt alle Dateien und vergleicht die Prüfsummen
  (Exit-Code 1 bei fehlenden oder beschädigten Dateien; IDs werden ausgegeben).

### Fehlerbilder

| Meldung | Ursache | Lösung |
|---|---|---|
| `SM_ENCRYPTION_KEYS muss in Produktion gesetzt sein` | Eintrag fehlt in `.env` | Schlüssel aus dem Tresor eintragen (Neuanlage nur bei ganz neuer Installation!) |
| `SM_ENCRYPTION_KEYS: Schlüssel 'k1' muss genau 32 Byte lang sein` / `kein gültiges Base64` | Tippfehler, abgeschnittener Eintrag | mit Tresor-Eintrag vergleichen (Fingerabdruck), ggf. Anführungszeichen prüfen |
| `Schlüssel 'k0' ist nicht in SM_ENCRYPTION_KEYS` (Log) | alter Schlüssel zu früh entfernt bzw. Restore eines alten Backups | alten Schlüssel wieder hinten anhängen, Neustart, `rotate-keys` |
| Download liefert `500 – Die Datei ist beschädigt oder der Schlüssel fehlt` | Inhalt fehlt/beschädigt oder falscher Schlüssel | `verify-files`, `crypto-status` (Fingerabdruck), Datei-Archiv aus Backup zurückspielen |

---

## 15. Datei-Uploads & Virenscan

Hochgeladene Dateien liegen verschlüsselt unter `SM_FILES_DIR` (Standard `<SM_DATA_DIR>/files`, Docker:
`/app/data/files` im Volume `app_data`). Sicherheitsregeln (Allowlist, blockierte Typen, Download-Header):
`docs/SICHERHEIT.md`, Abschnitt 4.7.

| Variable | Standard | Bedeutung |
|---|---|---|
| `SM_UPLOAD_MAX_MB` | `25` | Höchstgröße je Datei; über ~49 MB auch `max_size` in `deploy/Caddyfile` bzw. `client_max_body_size` (nginx) erhöhen |
| `SM_QUOTA_MB_STAFF` | `2000` | Speicherkontingent je Personal-Konto (`0` = unbegrenzt) |
| `SM_QUOTA_MB_STUDENT` | `200` | Kontingent je Schüler- und Eltern-Konto |
| `SM_FILES_DIR` | `<SM_DATA_DIR>/files` | Ablageort (eigener Datenträger möglich; im Backup mitsichern!) |
| `SM_CLAMAV_HOST` / `SM_CLAMAV_PORT` | leer / `3310` | ClamAV-Daemon (clamd, TCP) für den Virenscan; leer = aus |
| `SM_CLAMAV_REQUIRED` | `0` | `1` = Uploads ablehnen, solange der Scanner nicht erreichbar ist (HTTP 503) |
| `SM_CLAMAV_TIMEOUT` | `30` | Sekunden je Scan-Verbindung |
| `SM_STUDENT_DOCS_RETENTION_DAYS` | `400` | Atteste/Dokumente von Schüler/innen nach so vielen Tagen samt Datei löschen (Wartungslauf); `0` = nie |

**Speicherbedarf:** Unterrichtsmaterial und Anhänge wachsen über das Schuljahr; als Richtwert 20–50 GB für eine Schule
dieser Größe einplanen und den Plattenplatz überwachen (`docker system df -v`, `du -sh` im Volume, Monitoring des
Hosters bzw. node_exporter). Die Wartung (stündlich) löscht nicht verwendete Uploads nach 24 h und gelöschte Dateien nach 30 Tagen;
manuell: `schulmanager-admin maintenance`.

### Virenscan mit ClamAV aktivieren (Docker)

```bash
# .env
SM_CLAMAV_HOST=clamav
SM_CLAMAV_REQUIRED=1        # empfohlen, sobald der Scanner stabil läuft

docker compose --profile antivirus up -d
docker compose ps clamav    # erster Start lädt Signaturen (einige Minuten bis "healthy"), braucht 1,5–3 GB RAM
```

Signaturen aktualisiert `freshclam` im Container selbst (Netz `egress`). Test: eine Textdatei mit der
EICAR-Testzeichenkette hochladen – erwartet wird „Die Datei wurde vom Virenscanner als gefährlich erkannt und
abgelehnt“ und ein Audit-Eintrag `file.virus`. Ohne Docker: `clamav-daemon` installieren, `TCPSocket 3310` +
`TCPAddr 127.0.0.1` in `clamd.conf`, `SM_CLAMAV_HOST=127.0.0.1`.

Im Log beobachten: `Virenscan fehlgeschlagen … ungeprüft angenommen` (Scanner nicht erreichbar, bei
`SM_CLAMAV_REQUIRED=0`) und `Upload blockiert` (Audit `file.blocked`).

## 16. Konten & Anmeldung (E-Mail/SMS, Anmeldedienste, Zugangsbriefe)

* **E-Mail** für Bestätigungscodes, „Passwort vergessen“ und Zugangsbriefe läuft über die vorhandene SMTP-Einstellung
  (`SM_SMTP_*`). Inhalte liegen bis zur Zustellung nur verschlüsselt in der Outbox.
* **SMS** (optional): `SM_SMS_PROVIDER=webhook|twilio|seven` + Zugangsdaten (siehe `.env.example`). `log` schreibt nur ins
  Protokoll. Ohne SMS-Anbieter bietet „Passwort vergessen“ nur E-Mail an.
* **„Passwort vergessen“ wirklich einschalten (Checkliste):**
  1. E-Mail: `SM_SMTP_HOST`, `SM_SMTP_PORT`, `SM_SMTP_USER`, `SM_SMTP_PASSWORD`, `SM_SMTP_FROM`, `SM_SMTP_TLS` setzen;
     **`SM_NOTIFY_DISPATCHER` darf nicht `0` sein** (sonst bleibt alles in der Outbox). Ohne SMTP zeigt die Seite
     „Kein Versand eingerichtet“.
  2. SMS (optional): `SM_SMS_PROVIDER=seven` + `SM_SMS_TOKEN` (+ `SM_SMS_FROM`) oder `twilio` (+ `SM_SMS_ACCOUNT_SID`,
     `SM_SMS_TOKEN`, `SM_SMS_FROM`) oder `webhook` (+ `SM_SMS_URL`). Kosten grob 7–10 ct je SMS in Deutschland (seven,
     Twilio), also wenige Euro pro Monat; E-Mail ist bei vorhandenem Postfach kostenlos.
  3. `SM_DEV_OUTBOX` im Echtbetrieb aus lassen; `SM_BASE_URL` muss die öffentliche Adresse sein (Link in der E-Mail).
  4. Nutzer/innen hinterlegen und bestätigen ihre Angaben unter *Profil → E-Mail & Handynummer* (Code per E-Mail/SMS);
     das Sekretariat kann sie unter *Benutzer → Kontakt* pflegen oder bestätigen. Erst bestätigte Angaben werden
     verwendet. Die Anmelde-Richtlinie des Kontos muss „Passwort“ und den Kanal erlauben.
  5. Prüfen: `docker exec schulmanager sh -c 'env | cut -d= -f1 | grep -E "SMTP|SMS|NOTIFY"'` (nur Namen, keine Werte).
* **Microsoft / Google / Apple / Schulkonto**: als Admin unter *Verwaltung → Anmeldedienste* einrichten (Client-ID,
  Geheimnis, bei Apple Team-ID, Key-ID und `.p8`-Schlüssel) oder per `SM_SSO_*`. Die anzuzeigende Weiterleitungs-URI
  steht auf der Seite. Wer sich wie anmelden darf (z. B. „Schüler/innen nur Microsoft + Apple, beide Pflicht“), legt
  *Verwaltung → Anmelde-Richtlinien* fest.
* **Zugangsbriefe** (PDF, einzeln/ZIP/E-Mail) entstehen beim Anlegen von Klassen und Konten; der Stapel mit den
  Startpasswörtern wird nach `SM_LETTER_BATCH_MINUTES` gelöscht. Das zuletzt erzeugte Startpasswort bleibt verschlüsselt
  am Konto, damit Verwaltung und Klassenleitung „Auf Startpasswort zurücksetzen“ können.
* **Nur Entwicklung/Vorschau**: `SM_DEV_OUTBOX=1` (Seite `/test-postausgang` zeigt Codes und Briefe) und
  `SM_SSO_DEV_MOCK=1` (Test-Anbieter). `SM_DEV_OUTBOX` ist in der Entwicklung standardmäßig an, `SM_SSO_DEV_MOCK` nur auf ausdrücklichen Wunsch (Standard aus); beide sind in Produktion verboten, der Test-Anbieter auch in der Demo – der
  Server startet dann nicht.

## 17. Auto-Planer, E-Mail-Konten und Fehlzeiten (Erweiterung 5)

### Auto-Planer (`server/autoplan.py`, `schulmanager/autoplan.py`)
Nach jeder planungsrelevanten Änderung (Lehrkräfte, Räume, Klassen, Kurse, Stundentafeln, Einstellungen, Stundenplan,
Import) prüft der Server nach `SM_AUTOPLAN_DELAY` Sekunden den regulären Stundenplan auf harte Verstöße (Sperrzeiten,
Klasse nicht da, Doppelbelegung, falscher/fehlender Fachraum, Stunden außerhalb des Rasters) sowie fehlende/überzählige
Wochenstunden. Zuerst werden Räume zur selben Zeit getauscht; bleibt etwas offen, plant der Generator nur die
betroffenen Kurse neu (Stufe 2: alle Kurse der beteiligten Klassen/Lehrkräfte). Übernommen wird nur, wenn der Plan
besser wird – als normale Version „Automatische Neuplanung …“ (Verlauf & Audit → Rückgängig). Status: Planung →
Generator → „Automatische Neuplanung“ bzw. `GET /api/v1/planning/autoplan`. Abschalten: Einstellungen → „Automatische
Neuplanung“ (je Schule) oder `SM_AUTOPLAN=0` (Server). Der Tagesplan (Vertretungen) tauscht bei gesperrtem Fachraum ohne
Ersatz die Stunde mit einer anderen Stunde der Klasse; durch eine Klausur belegte Räume zählen als belegt.

### E-Mail-Konten im Postfach (`server/mailbridge.py`, `routes/features_mail.py`)
Jede Person kann unter Postfach → Einstellungen eigene E-Mail-Konten verbinden (IMAP/SMTP mit App-Passwort; Google,
Apple/iCloud, GMX, WEB.DE, T-Online, Yahoo, eigener Server). Darüber gehen Nachrichten an Adressen außerhalb der Schule
hinaus; eingehende E-Mails ruft der Server alle `SM_MAIL_SYNC_MINUTES` Minuten ab (nur lesend, beim Anbieter ändert sich
nichts) und legt sie verschlüsselt ins Postfach. Antworten werden über `Message-ID`/`In-Reply-To` der Unterhaltung
zugeordnet. Zugangsdaten liegen nur verschlüsselt in `mail_accounts.secret_enc` (Schlüsselrotation über
`cli rotate-keys`). Der Server braucht ausgehende Verbindungen zu den IMAP-/SMTP-Servern (Ports 993, 465/587).

**Microsoft (Outlook/Hotmail/365) erlaubt IMAP/SMTP nur mit OAuth.** Dafür einmalig eine App registrieren:
* Microsoft Entra ID → App-Registrierungen → Neu; Kontotypen „beliebiges Verzeichnis und persönliche Microsoft-Konten“;
  Umleitungs-URI (Web): `<SM_BASE_URL>/api/v1/mail/oauth/callback`; API-Berechtigungen (delegiert):
  `IMAP.AccessAsUser.All`, `SMTP.Send`, `offline_access`, `openid`, `email`; Geheimen Clientschlüssel erzeugen →
  `SM_OAUTH_MICROSOFT_CLIENT_ID`, `SM_OAUTH_MICROSOFT_CLIENT_SECRET` (optional `SM_OAUTH_MICROSOFT_TENANT`).
* Google (optional, sonst App-Passwort): Google Cloud Console → OAuth-Client (Webanwendung), Weiterleitungs-URI wie
  oben, Bereich `https://mail.google.com/` (eingeschränkter Bereich: ohne Google-Prüfung nur für eingetragene Testnutzer)
  → `SM_OAUTH_GOOGLE_CLIENT_ID`, `SM_OAUTH_GOOGLE_CLIENT_SECRET`.
`SM_BASE_URL` muss die Adresse sein, unter der Browser den Schulmanager erreichen (Weiterleitung nach der Anmeldung).

### Fehlzeiten
`student_absences` kennt Art (`krank`, `verspaetung` mit Minuten, `frueh`, `fehlt`), Herkunft (online, Telefon,
schriftlich, Lehrkraft) und den Status `teilweise` (telefonisch gemeldet, schriftliche Entschuldigung fehlt). Übersicht je
Kind: `/fehlzeiten/<Schüler-ID>`; Formular zum Ausdrucken: `GET /api/v1/student-absences/form.pdf`. Wird eine
Entschuldigung/ein Attest zu einem Eintrag als „geprüft“ markiert, gilt der Eintrag als entschuldigt. Telefonnummer und
Zeiten für Krankmeldungen: Einstellungen → „Krankmeldungen & Atteste“.

### Ferien und Feiertage automatisch (`server/holiday_import.py`)
Planung → „Zeitraster & Schuljahr“ → „Ferien & Feiertage automatisch“: Land und Bundesland wählen, „Jedes Schuljahr
automatisch übernehmen“ einschalten oder per „Vorschau“ / „Jetzt übernehmen“ von Hand holen (Recht
`masterdata.edit`). Quelle: OpenHolidays API (`openholidaysapi.org`, Feiertage + Schulferien), für Länder ohne Eintrag dort
Nager.Date (`date.nager.at`, nur Feiertage); beide ohne Schlüssel. Der Server ruft sie ab (Timeout 10 s, Listen 24 h
gecacht) – er braucht ausgehenden HTTPS-Zugriff. Die Automatik prüft 30 s nach dem Start und danach täglich das laufende
und das nächste Schuljahr; bei Fehlern (z. B. offline) wird nur protokolliert und nach einer Stunde neu versucht.
Importierte Einträge werden aktualisiert, nie doppelt angelegt; von Hand angelegte oder später geänderte Einträge und von
Hand gelöschte Einträge bleiben unangetastet, es wird nichts gelöscht. `SM_HOLIDAY_IMPORT=0` schaltet den Dienst ganz ab
(Standard: an, aber je Schule erst aktiv, wenn die Automatik eingeschaltet ist).

---

## 18. Reverse Proxy, API-Doku, Chat-Kontingent, Abhängigkeiten (Sicherheitsprüfung Runde 3)

### Reverse Proxy und vertrauenswürdige Adressen (S-10)

**Die App wird nie direkt veröffentlicht** (kein `-p 8000:8000` ins Internet, kein offener Port am Router): Davor steht immer
Caddy (Compose) oder nginx (systemd). Nur der Proxy darf die Client-IP und das Schema (`X-Forwarded-For`/`-Proto`)
melden – sonst könnte jeder Besucher seine Adresse frei wählen und damit die Login-Sperre je IP, die IP-Listen der
API-Zugänge und die Audit-IP aushebeln.

| Variable | Bedeutung |
|---|---|
| `SM_TRUST_PROXY=1` | `X-Forwarded-*` überhaupt auswerten (Compose/systemd setzen es). Ohne: immer die echte Adresse der Verbindung. |
| `SM_TRUSTED_PROXIES` | Adressen/Netze, kommagetrennt, deren Köpfen geglaubt wird. Leer = nur `127.0.0.1`/`::1`. Alter Name `SM_FORWARDED_ALLOW_IPS` gilt als Rückfall. `*` nur, wenn die App garantiert nicht direkt erreichbar ist (Warnung beim Start). |
| `SM_PROXY_COUNT` | Wie viele Proxys hintereinander (Standard 1). |
| `SM_WEB_SUBNET` | Compose: festes Netz `web` (Standard `172.29.40.0/24`); `SM_TRUSTED_PROXIES` übernimmt es automatisch. Bei Adresskonflikt mit dem Heimnetz ändern. |

* **Docker/Compose:** `docker-compose.yml` vergibt das Netz `web` fest und setzt `SM_TRUSTED_PROXIES` darauf. Weitere
  Container im Netz `web` (Uptime-Kuma) könnten Köpfe fälschen, sie haben aber keinen Zugriff von außen.
* **systemd/nginx:** Die Unit setzt `SM_TRUSTED_PROXIES=127.0.0.1,::1` und startet uvicorn mit `--no-proxy-headers`; nginx
  überschreibt `X-Forwarded-For` mit `$remote_addr`.
* **Entrypoint:** warnt beim Start, wenn `SM_TRUST_PROXY=1` ohne `SM_TRUSTED_PROXIES` läuft oder `*` enthält.
* **Prüfen:** `curl -H 'X-Forwarded-For: 1.2.3.4' https://<Schule>/api/v1/auth/me` darf im Audit/Login-Protokoll nie `1.2.3.4`
  erzeugen (Caddy/nginx überschreiben den Kopf; direkter Zugriff auf Port 8000 ist von außen gesperrt).

### API-Dokumentation (S-15)

`SM_ENABLE_DOCS=0` (Voreinstellung in Produktion und in `docker-compose.yml`) schaltet `/api/docs` und `/api/openapi.json`
ab; `admin` erlaubt sie nur angemeldeten Administratoren (Browser mit Sitzung oder Admin-API-Token); `1` öffnet sie für alle
(nur im Schulnetz). Die Oberfläche (Swagger-UI) liegt im Image – es werden keine Skripte von Drittanbietern geladen. Für API-Zugänge
bleiben `/llms.txt` und `/api/v1/meta/openapi.json` unverändert erreichbar.

### Chat-Bilder: Kontingent (S-13)

Bilder in Chats liegen verschlüsselt als Blobs in der Datenbank und zählen **nicht** in das Dateikontingent
(`SM_QUOTA_MB_*`), sondern in ein eigenes: `SM_CHAT_QUOTA_MB_STAFF` (500), `SM_CHAT_QUOTA_MB_STUDENT` (100, auch Eltern),
`SM_CHAT_QUOTA_MB_CHAT` (1000 je Chat, alle Mitglieder zusammen), `SM_CHAT_UPLOADS_PER_10MIN` (30). `0` = unbegrenzt. Wer voll ist, sieht „Ihr
Platz für Chat-Bilder ist voll …“; Platz entsteht durch Löschen der Nachricht. Obergrenze für die Datenbank bei 2500 Schülern:
Σ Kontingente ≈ 350 GB im ungünstigsten Fall (ohne Eltern-Konten), praktisch weit darunter (siehe `SPEICHER-KALKULATION.md`, Abschnitt 2.6).

### Python-Abhängigkeiten sperren und prüfen (S-14)

* `requirements.lock` (Laufzeit) und `requirements-dev.lock` (mit Test-Werkzeugen) enthalten alle Pakete **mit Hashes**;
  Dockerfile (`--require-hashes`), CI und `make install` installieren daraus. Aktualisieren: `make lock` (braucht `uv`), prüfen,
  committen. Dependabot schlägt Änderungen an `pyproject.toml` vor; danach `make lock` ausführen.
* Schwachstellen-Scan: `make audit` (pip-audit gegen das Lockfile); in CI als Job „Abhängigkeits-Audit“ (zusätzlich `npm audit --omit=dev`).

### Beim nächsten Deploy zu setzen / zu tun

1. Neue `.env`/Compose-Datei übernehmen: `SM_ENABLE_DOCS` (Standard jetzt `0`), optional `SM_WEB_SUBNET`, die Chat-Kontingente.
2. `docker compose up -d --build`: Das Netz `web` bekommt das feste Subnetz (kurze Unterbrechung; bei Konflikt `SM_WEB_SUBNET` ändern).
   Prüfen, dass `SM_FORWARDED_ALLOW_IPS="*"` nirgends mehr in `.env`/`app.env` steht (wird sonst als Rückfall für
   `SM_TRUSTED_PROXIES` benutzt).
3. Migration `0045_secrets_at_rest` läuft automatisch (`SM_AUTO_MIGRATE=1`); vorher ein Backup (`make backup`). Danach funktionieren
   bestehende Kalender-Links weiter, werden aber im Profil nicht mehr angezeigt (neu erzeugen, wenn ein Link verloren ging).
   Ein Zurückrollen der Migration setzt die iCal-Links zurück.
4. Nach Schlüsselrotation (`schulmanager-admin rotate-keys`) werden auch die TOTP-Geheimnisse neu verpackt.


## 19. Lizenz (Lizenzschlüssel und Lizenzserver)

Jede Schul-Instanz braucht einen **Lizenzschlüssel** (`SPUL-XXXX-XXXX-XXXX-XXXX`, ein Schlüssel je Server; eine Schule mit mehreren
Servern bekommt mehrere Schlüssel). Der Anbieter verwaltet sie auf seinem Lizenzserver (`lizenzserver/`, Bedienung dort im README).

* **Eintragen:** `/lizenz` (Recht `license.manage`: Administration, Schulleitung) bzw. auf der Willkommensseite einer frischen Instanz.
  Die Instanz bindet den Schlüssel dabei an sich; ein zweiter Server mit demselben Schlüssel wird abgelehnt (Serverumzug: Anbieter löst die Bindung).
* **Prüfung:** beim Start und mindestens alle 24 Stunden (`SM_LICENSE_CHECK_HOURS`) fragt die Instanz beim Anbieter nach, zusätzlich
  alle 15 Minuten kurz (`SM_LICENSE_PING_MINUTES`, `0` = aus; kein Datenbankzugriff, winzige Anfrage), damit eine Sofortsperre zeitnah wirkt.
  Die Antwort ist mit dem Schlüssel des Anbieters signiert (`VENDOR_PUBKEY`) und gilt als Bestätigung bis `confirmed_until` (Standard 7 Tage).
* **Stufen:** gültig (Vorwarnung 30/14/7/1 Tag vor „Abo aktiv bis“, Banner und Glocke für Administration/Schulleitung) → **Kulanzzeit**
  (`SM_LICENSE_GRACE_DAYS`, 14 Tage, für alle nur lesen) → **gesperrt** (API und Oberfläche für alle zu; nur Anmeldung/Abmeldung und `/lizenz` für
  `license.manage`). Gründe: Abo abgelaufen und Pausieren (mit Kulanz), Anbieter nicht erreichbar länger als die Bestätigung gilt (mit Kulanz),
  Kündigung, unbekannter Schlüssel, Bindung gelöst und **Sofortsperre** des Anbieters (sofort, ohne Kulanz, eigener Text).
* **Produktion:** `SM_MODE=production` erzwingt die Prüfung (`SM_LICENSE_ENFORCE` wirkt dort nicht); öffentlicher Schlüssel und Serveradresse sind
  fest eingebaut (`licensing.VENDOR_PUBKEY`, `VENDOR_SERVER`). Entwicklung/Demo: frei, Prüfung per `SM_LICENSE_ENFORCE=1`, Test-Schlüssel per
  `SM_LICENSE_PUBKEY`, Test-Server per `SM_LICENSE_SERVER` (ausgehende Verbindung zu lokalen Adressen: `SM_OUTBOUND_ALLOW`).
* **Dateien:** `<data_dir>/license.json` (nur der Schlüssel), `<data_dir>/license_state.json` (Instanz-ID, Sperr-Schlüssel, letztes Token). Nicht löschen:
  ohne Zustandsdatei bekommt die Instanz eine neue ID und der Schlüssel gilt als an einen anderen Server gebunden, bis der Anbieter die Bindung löst.

## Updates und mehrere Server

Der Anbieter kann Updates automatisch zu einem vereinbarten Termin einspielen (Sicherung, Gesundheitsprüfung, Rückfall). Dafür läuft
neben der App der **Update-Agent** (Compose-Profil `updater`, `scripts/compose.sh --profile updater up -d updater`); Termin, Verschieben
und „Jetzt installieren“ sehen Sie unter `/betrieb`. Mit `SM_NODE_ID`/`SM_HA` lassen sich mehrere App-Knoten mit gemeinsamer
PostgreSQL-Datenbank betreiben (Leader-Sperre für Hintergrundjobs, `/healthz/ready` für den Lastverteiler). Vollständige Beschreibung,
Sicherheit (Docker-Socket), Checkliste und die ehrliche Abgrenzung von Gebautem und Konzept: `docs/UPDATES-UND-HOCHVERFUEGBARKEIT.md`.
Nach dem ersten Update bitte immer `scripts/compose.sh` statt `docker compose` verwenden (liest `update.env`).
