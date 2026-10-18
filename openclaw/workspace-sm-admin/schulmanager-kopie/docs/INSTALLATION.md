# Schulpuls installieren – Anleitung für Schul-IT und Schulträger

Diese Anleitung bringt eine **eigene Instanz für eine Schule** in Betrieb (Echtbetrieb, Betriebsmodus `production`). Eine Instanz gehört genau einer Schule; mehrere Schulen bekommen mehrere Instanzen. Die ausführlichen Nachschlagewerke sind das [Betriebshandbuch](BETRIEB.md) und das [Sicherheitskonzept](SICHERHEIT.md); diese Anleitung ist der kurze Weg von „leerer Server“ bis „Schule kann arbeiten“.

Vorgefertigte Datenschutz-Unterlagen: [`datenschutz/`](datenschutz/). Kurzanleitungen für die Nutzergruppen stehen in der App unter *Hilfe* (Quelle: [`hilfe/`](hilfe/)).

## 1. Voraussetzungen

| Was | Wert |
|---|---|
| Server | Linux (Debian/Ubuntu), 2 CPU-Kerne, 4 GB RAM, 40 GB Platz (bis ca. 1000 Schüler/innen; Richtwerte für 2500: BETRIEB.md §2) |
| Software | Docker Engine ab 24 mit Compose-Plugin, `git`, `openssl` |
| Netz | feste öffentliche Adresse; DNS-Eintrag (A/AAAA) auf den Server; Ports 80 und 443 (TCP) sowie 443 (UDP) erreichbar |
| Adresse | z. B. `plan.meine-schule.de` (HTTPS-Zertifikat holt der Server selbst bei Let's Encrypt) |
| Mailserver | SMTP-Zugang (Host, Port, Benutzer, Passwort, Absenderadresse) für „Passwort vergessen“ und Benachrichtigungen |
| Verträge | Auftragsverarbeitung mit dem Hoster (siehe `datenschutz/`) |
| Aufbewahrung | Passwort-Tresor für Schlüssel und Passphrasen (siehe Schritt 3) |

## 2. Dateien holen

```bash
sudo mkdir -p /opt/schulpuls && sudo chown $USER /opt/schulpuls
git clone <Adresse-des-Repositorys> /opt/schulpuls
cd /opt/schulpuls
```

## 3. Konfiguration erzeugen

```bash
scripts/init-env.sh --domain plan.meine-schule.de --email it@meine-schule.de
```

Das Skript legt `.env` an (Rechte 600) und erzeugt zufällige Werte für `SM_SECRET_KEY`, `SM_ENCRYPTION_KEYS`, `POSTGRES_PASSWORD` und `BACKUP_GPG_PASSPHRASE`. Es setzt außerdem `SM_REQUIRE_2FA_ROLES`, damit Administration, Schulleitung und Sekretariat einen zweiten Faktor einrichten müssen.

**Sofort sichern, getrennt vom Server (Passwort-Tresor, Ausdruck im Safe):**

- `SM_ENCRYPTION_KEYS` – schützt Nachrichten, Atteste und hochgeladene Dateien. Geht der Schlüssel verloren, sind diese Inhalte **auch aus Sicherungen** nicht mehr lesbar.
- `BACKUP_GPG_PASSPHRASE` – öffnet die nächtlichen Sicherungen.
- Die ganze `.env` (verschlüsselt ablegen).

Danach in `.env` den Mailserver eintragen (`SM_SMTP_HOST`, `SM_SMTP_PORT`, `SM_SMTP_USER`, `SM_SMTP_PASSWORD`, `SM_SMTP_FROM`, `SM_SMTP_TLS`). Alle Variablen mit Erklärung stehen in [`.env.example`](../.env.example). Der Betriebsmodus ist `SM_MODE=production`.

Konfiguration prüfen, ohne zu starten:

```bash
docker compose run --rm app python -m schulmanager.server.cli check-config
```

Im Betriebsmodus `production` bricht der Start mit einer klaren Liste ab, wenn Pflichtwerte fehlen oder unsicher sind: fehlendes oder zu kurzes Secret, fehlender Verschlüsselungsschlüssel, Beispielwerte aus `.env.example` (`BITTE_AENDERN…`), Adresse ohne `https://`, bekannte Entwicklungspasswörter, eingeschaltete Demo-Funktionen. „Hinweise“ (z. B. kein Mailserver) verhindern den Start nicht.

## 4. Starten

```bash
docker compose up -d --build
docker compose ps                       # alle Dienste „healthy“
docker compose logs app | grep ERST-ADMIN
```

Beim ersten Start entstehen die Datenbank, das leere Planungsdokument und der Erst-Administrator `admin`. Sein **Einmalpasswort** steht im Log (Zeile `ERST-ADMIN`). Alternativ legen Sie vor dem Start `SM_ADMIN_PASSWORD` fest (mindestens 10 Zeichen, kein Beispielpasswort) und leeren die Variable danach wieder. Es werden **keine Demo-Daten und keine Entwicklungspasswörter** angelegt.

## 5. Erste Anmeldung und Einrichtung

1. `https://plan.meine-schule.de` öffnen, als `admin` anmelden. Die App verlangt sofort ein eigenes Passwort. In einer frischen Instanz erscheint danach die Willkommensseite „Lizenzschlüssel eingeben, um fortzufahren“; nach dem Schlüssel geht es direkt in den Einrichtungsassistenten.
2. Zwei-Faktor-Anmeldung einrichten (Profil). Das ist für Administration, Schulleitung und Sekretariat Pflicht.
3. Der **Einrichtungsassistent** (Menü *Schule einrichten*) führt weiter:

| Schritt | Inhalt |
|---|---|
| Administration sichern | Zwei-Faktor einrichten |
| Lizenz | Lizenzschlüssel (`SPUL-XXXX-XXXX-XXXX-XXXX`) eintragen; ohne gültige Lizenz ist die Instanz gesperrt |
| Schuldaten | Name, Schulform, Bundesland, Adresse, Logo, Standorte |
| Schuljahr und Ferien | Ferien und Feiertage des Bundeslandes übernehmen |
| Zeitraster | Anfangszeiten, Stundenlänge, Pausen |
| Lehrkräfte, Klassen, Fächer, Räume | Import aus SchILD-NRW, ASV, LUSD, Untis (GPU) oder CSV – erst „Probelauf“ |
| Schüler/innen | Import aus denselben Quellen; Klassen müssen vorher existieren |
| Stundentafeln und Kurse | Stunden je Fach und Jahrgang, Lehrkräfte zuweisen |
| Stundenplan | Generator oder Untis-Plan übernehmen |
| Konten und Zugangsbriefe | Konten für alle anlegen, Briefe als PDF drucken |
| Rollen und Rechte | Standard prüfen |
| E-Mail-Versand | Testmail senden |
| Schulkonto-Anmeldung | optional (Microsoft, Google, Apple oder eigener Dienst) |

Der Fortschritt wird gespeichert; Schritte lassen sich überspringen und später nachholen. Am Ende *Einrichtung abschließen*.

Eine ausführliche Beschreibung der Datenübernahme mit Beispiel steht in [SCHULE-EINRICHTEN.md](SCHULE-EINRICHTEN.md).

## 6. Sicherung einrichten und prüfen

Der Dienst `backup` sichert ab dem Start täglich um 02:30 Uhr die Datenbank (`pg_dump`) und das Datenverzeichnis (Dateien), verschlüsselt mit der Passphrase, rotiert 14 Tage / 8 Wochen / 12 Monate und legt alles unter `./backups` ab.

1. **Offsite-Kopie** einrichten (3-2-1-Regel): `BACKUP_RCLONE_REMOTE` und die `RCLONE_CONFIG_OFFSITE_*`-Werte in `.env` (Anleitung: BETRIEB.md §7).
2. In der App unter *Betrieb* sehen Sie Alter und Größe der Sicherungen. Mit **Prüfen** spielt die App eine App-Sicherung in eine Wegwerf-Kopie ein und kontrolliert sie.
3. **Test-Restore der Datenbank-Sicherung** (monatlich, Pflicht):

```bash
make restore-test FILE=backups/monthly/<datei>.dump
```

4. **Wiederherstellung** im Ernstfall: `make restore FILE=backups/daily/<datei>.dump` (stoppt die App, sichert den aktuellen Stand, spielt zurück, startet neu). Dateien (`schulmanager_files_*.tar.gz`) und der **Schlüssel `SM_ENCRYPTION_KEYS`** gehören dazu – ohne den Schlüssel bleiben verschlüsselte Inhalte unlesbar. Ablauf bei einem neuen Server: BETRIEB.md §7 „Disaster Recovery“.

## 7. Updates und Rollback

```bash
cd /opt/schulpuls
make update
```

`make update` erstellt eine Sicherung mit dem Namen „vor-update“, holt die neue Version, baut neu, startet neu und prüft den Zustand. Die **Datenbank-Migrationen** laufen beim Start automatisch (`SM_AUTO_MIGRATE=1`) und sind wiederholbar. Schlägt eine Migration fehl, startet die App nicht und schreibt die Ursache ins Log (`docker compose logs app`).

**Rollback:**

1. `git checkout <vorherige-Version>` (oder das vorherige Image-Tag in `.env`) und `make up`.
2. Wurde die Datenbank bereits migriert, zusätzlich die Sicherung „vor-update“ zurückspielen: `make restore FILE=backups/manual/<…>_vor-update.dump`.

Updates am besten nachmittags oder abends; die Unterbrechung dauert meist unter einer Minute. Zeitpunkte und Details: BETRIEB.md §6.

## 8. Betrieb im Alltag

- **Status**: Menü *Betrieb* (Administration) zeigt Version, Datenbankstand, freien Speicher, Mail, letzte Sicherung, Wartungslauf und das Fehlerprotokoll. Ein gelber Hinweis ist eine Empfehlung, ein roter Punkt braucht Handeln.
- **Gesundheitsabfrage von außen**: `https://<adresse>/healthz` (für Uptime-Kuma o. Ä.).
- **Monatlicher Patchtag**: `docker compose build --pull && docker compose up -d`, Betriebssystem-Updates.
- **Schuljahreswechsel**: Menü *Schuljahreswechsel* (Schulleitung oder Administration) mit Vorschau und Rückgängig.
- **Konten sperren/entsperren, Passwörter zurücksetzen**: in der App unter *Benutzer* oder per `docker compose exec app schulmanager-admin …`.
- **Hilfe für Nutzer**: Menü *Hilfe* in der App.

## 9. Checkliste vor dem Livegang

- [ ] `check-config` meldet „in Ordnung“, keine offenen Platzhalter in `.env`
- [ ] `https://` mit gültigem Zertifikat, Adresse stimmt mit `SM_BASE_URL`
- [ ] Erst-Administrator hat eigenes Passwort und Zwei-Faktor; `SM_ADMIN_PASSWORD` ist in `.env` leer
- [ ] `SM_ENCRYPTION_KEYS`, `BACKUP_GPG_PASSPHRASE` und `.env` liegen getrennt vom Server im Tresor
- [ ] Offsite-Sicherung läuft; ein Test-Restore wurde erfolgreich durchgeführt und notiert
- [ ] Testmail kommt an; „Passwort vergessen“ geprüft
- [ ] Lizenzschlüssel eingetragen (`/lizenz`: „Status beim Anbieter: aktiv“, „Letzte Prüfung“ gesetzt); ein Server pro Schlüssel
- [ ] Datenschutz: Verzeichnis der Verarbeitungstätigkeiten ausgefüllt, AV-Verträge liegen vor, Datenschutzhinweise verteilt, Datenschutz-Folgenabschätzung geprüft (Vorlagen: `datenschutz/`)
- [ ] Zugangsbriefe verteilt; Hinweis an Nutzer: Passwort sofort ändern
- [ ] Firewall: nur 22 (eingeschränkt), 80, 443 offen; kein Datenbankport veröffentlicht

## 10. Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| Start bricht mit „Konfiguration … unvollständig“ ab | Liste in der Meldung abarbeiten; `check-config` wiederholen |
| Kein Zertifikat | DNS zeigt noch nicht auf den Server, Ports 80/443 gesperrt; `docker compose logs caddy` |
| Einmalpasswort verloren | `docker compose exec app schulmanager-admin reset-password --username admin` gibt ein neues aus |
| Mails kommen nicht an | *Betrieb* → E-Mail, Einrichtungsassistent → Testmail; SMTP-Werte, Port und `SM_SMTP_TLS` prüfen |
| Seite zeigt Fehler mit Nummer | Nummer im *Betrieb* → Fehlerprotokoll nachschlagen |
| Datenbank nicht aktuell | `docker compose run --rm app python -m schulmanager.server.migrate` |

Weitere Fehlerbilder: BETRIEB.md §12.

## 11. Installation ohne Docker

Möglich mit systemd, PostgreSQL und nginx (Dateien unter `deploy/systemd`, `deploy/nginx`). Schritte: BETRIEB.md §4. `SM_MODE=production` und `check-config` gelten dort genauso (`/opt/schulmanager/.venv/bin/python -m schulmanager.server.cli check-config`).
