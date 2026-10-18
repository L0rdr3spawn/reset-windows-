# Produktreife – von der Demo zur Software, die eine Schule selbst betreibt

Stand: 16.10.2026 (Runde 3, Paket P). Ziel: eine echte Schule kann Schulpuls selbst **installieren, einrichten, mit echten Daten befüllen und dauerhaft betreiben**. Zuordnung der Werkzeuge: Installation [`INSTALLATION.md`](INSTALLATION.md), Betrieb [`BETRIEB.md`](BETRIEB.md), Einrichtung [`SCHULE-EINRICHTEN.md`](SCHULE-EINRICHTEN.md), Sicherheit [`SICHERHEIT.md`](SICHERHEIT.md), Datenschutz [`datenschutz/`](datenschutz/), Löschkonzept [`DATENSCHUTZ-LOESCHKONZEPT.md`](DATENSCHUTZ-LOESCHKONZEPT.md).

Legende: ✔ fertig · ◐ teilweise · ✘ offen. Aufwand: S = Stunden bis 1 Tag, M = wenige Tage, L = Wochen.

## 1. Bestandsaufnahme (vor dieser Runde)

**Was nur in der Demo funktionierte:** Demo-Schule laden (`/admin/demo`, `cli load-demo`, `SM_LOAD_DEMO`), Demo-Zugänge für Vorführungen (`/demo-access`, nur mit `SM_DEMO_PUBLIC`), Demo-Konten mit festen Passwörtern (`demo_loader.py`, `demo123456`), Schutz der Demo-Konten (`deps._guard_demo`), Entwicklungs-Erstpasswort `admin12345` und `SM_ADMIN_PASSWORD`-Voreinstellungen in `scripts/dev.sh`, `preview.sh` und den Dev-Compose-Dateien, Test-Postausgang und Test-Anmeldedienst (nur in Entwicklung erlaubt).

**Was hart auf Beispieldaten setzte:** Platzhalter-Schulname „Meine Schule“, Beispielwerte in `.env.example` (`plan.meine-schule.de`, `BITTE_AENDERN…`), Demo-Generator (`schulmanager/demo.py`) mit erfundenen Klassen/Namen (bleibt, nur für Demo und Tests), die Einrichtungsseite prüfte nur Zähler und kannte weder Schuldaten noch Fortschritt.

**Was für den Echtbetrieb fehlte:** ein einheitlicher Betriebsmodus mit Abbruch bei fehlenden Pflichtwerten, ein Einrichtungsassistent mit gespeichertem Fortschritt und Schuldaten, ein Schuljahreswechsel, eine Statusseite mit Fehlerprotokoll, ein prüfbarer Test-Restore in der Oberfläche, eine Installationsanleitung mit Prüfschritten, Datenschutz-Vorlagen und eine Hilfe in der App.

## 2. Checkliste mit Status

### A. Betriebsmodus und sichere Voreinstellungen

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| `SM_MODE=production\|demo\|development`, alte Variablen (`SM_ENV`, `SM_DEMO_PUBLIC`, `SM_LOAD_DEMO`) bleiben kompatibel | ✔ | – | `config.py` (`_resolve_mode`), `tests/test_produktreife_betrieb.py` |
| Echtbetrieb bricht beim Start mit klarer Liste ab (Secret, Verschlüsselungsschlüssel, https-Adresse, Beispielpasswörter, Platzhalter, Demo-Schalter) | ✔ | – | `config.mode_problems`, `cli check-config` |
| Demo-Funktionen im Echtbetrieb aus (Demo laden, CLI, Erststart-Demo, Demo-Zugänge, Rollen-Knöpfe, Admin-Demo-Block) | ✔ | – | `routes/admin.py`, `cli.py`, `bootstrap.py`, `AdminPage.tsx` |
| Sichere Voreinstellungen: Test-Postausgang, Test-SSO, OpenAPI-Doku aus | ✔ | – | `config.py` |
| Erst-Administrator: Einmalpasswort statt Entwicklungspasswort, Passwortwechsel erzwungen | ✔ | – | `bootstrap.ensure_admin` |
| Einmalpasswort wird im Container-Log ausgegeben | ◐ | S | Besser: einmaliger Einrichtungslink oder Datei im Datenverzeichnis (Entscheidung E7) |
| Altinstanzen mit `SM_ENV=production` ohne `SM_MODE` laufen unverändert weiter (neue Prüfungen nur als Warnung) | ✔ | – | Test `test_legacy_variables_stay_compatible` |

### B. Einrichtung einer leeren Instanz

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| Assistent mit 13 Schritten, Fortschritt gespeichert, überspringen, später fortsetzen, abschließen | ✔ | – | `routes/setup.py`, `pages/SetupPage.tsx` |
| Hinweisband für die Administration, bis die Einrichtung abgeschlossen ist | ✔ | – | `Layout.tsx` (`SetupHint`) |
| Schuldaten: Name, Schulform, Bundesland, Adresse, Kontakt, Logo | ✔ | – | `PUT /setup/profile`, `GET /school-logo` |
| Logo auf Anmeldeseite, Briefen und PDFs verwenden | ✘ | S | Logo ist gespeichert und abrufbar, aber noch nicht eingebunden |
| Schuljahr und Ferien/Feiertage (Bundesland aus Schuldaten) | ✔ | – | `POST /setup/holidays` (nutzt Ferien-Import) |
| Zeitraster | ◐ | M | Verlinkt auf die Planungsseite; Vorlagen je Schulform fehlen (z. B. „Gymnasium 45 Min.“) |
| Import Lehrkräfte, Klassen, Schüler, Fächer, Räume: CSV mit Vorlagen SchILD-NRW, ASV, LUSD, Magellan; Untis GPU; JSON | ✔ | – | `integrations/*`, Importseite mit Probelauf |
| Direktimport im Original-Exportformat (SchILD-XML/SVWS-Schnittstelle, ASV-XML, LUSD-Datei, OneRoster) | ✘ | L | heute CSV-Export aus dem System nötig |
| Stundentafeln | ◐ | M | Anlage von Hand/Import; Vorlagen je Bundesland und Schulform fehlen |
| Rollen und Rechte | ✔ | – | Standardrechte, Seite *Rollen & Rechte* |
| Zugangsbriefe (PDF, QR-Code, Startpasswort) | ✔ | – | |
| Einmal-Anmeldelink statt Startpasswort im Brief | ✘ | M | Werkzeug W-17 in `MONTESSORI-UND-WERKZEUGE.md` |
| Mail-Versand: Status und Testmail | ✔ | – | `POST /setup/test-mail` |
| SMTP-Zugang in der Oberfläche eintragen | ✘ | M | bewusst nur in der Konfiguration (Geheimnisse gehören nicht in die Datenbank) |
| Optionales SSO | ✔ | – | Seite *Anmeldedienste* |

### C. Schuljahreswechsel

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| Klassen hochstufen (Jahrgang +1, Klassenname mit Zahl), Ausnahmen je Klasse | ✔ | – | `year_change.py` |
| Abgänger austragen (Abschlussjahrgang, Einzelne), Konten sperren, Eltern nur ohne weiteres Kind | ✔ | – | |
| Anbindung an das Löschkonzept | ◐ | S | Schnittstelle `year_change.register_leaver_handler`; Agent S-A hängt die Warteliste „ausgetreten“ ein. Bis dahin: Konten bleiben gesperrt. |
| Neue Klassen anlegen (Schüler danach per CSV) | ✔ | – | |
| Kursräume archivieren, Notenbücher abschließen | ✔ | – | |
| Neues Schuljahr: Beginn setzen, alter Beginn im Verlauf; optional Stundenplan leeren | ✔ | – | |
| Vorschau vor dem Ausführen, Bindung an die Vorschau, Rückgängig | ✔ | – | Rückgängig nur, solange der Plan unverändert ist |
| Kurse und Stundentafel für das neue Jahr automatisch fortschreiben, Oberstufen-Kursphasen | ✘ | M | heute: nach dem Wechsel „Kurse aus Stundentafeln“ und Generator von Hand |
| Zeugnisdaten/Abschlussnoten der Abgänger archivieren (Export) | ✘ | M | vor dem Wechsel Notenbuch exportieren |

### D. Betrieb

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| Backup aus der Oberfläche und per Skript, verschlüsselt (GPG), Rotation, Offsite | ✔ | – | `backups.py`, `scripts/backup.sh`, Backup-Dienst |
| Test-Restore (Skript und Oberfläche „Prüfen“) | ✔ | – | `make restore-test`, `ops.verify_backup` |
| Wiederherstellung per Klick in der Oberfläche | ✘ | M | bewusst nicht: Restore stoppt die App und braucht Schlüssel; per `make restore` |
| Schlüssel-Hinweise (Verlust = Datenverlust, getrennt aufbewahren) | ✔ | – | Statusseite, `INSTALLATION.md`, `datenschutz/toms.md` |
| Update mit Migration und Rollback dokumentiert | ✔ | – | `INSTALLATION.md` §7, `BETRIEB.md` §6 |
| Statusseite (Version, Datenbank, Speicher, Mail, Sicherung, Wartung, Lizenz, Prüfliste) | ✔ | – | `GET /admin/status`, Seite *Betrieb* |
| Fehlerprotokoll einsehbar (30 Tage/1000 Einträge), Fehlernummer in Meldungen | ✔ | – | `GET /admin/errors` |
| Alarm bei Fehlern/ausbleibender Sicherung per E-Mail | ✘ | M | Prometheus-Regeln vorhanden (`deploy/prometheus`), kein Versand aus der App |
| Externe Sicherung (Backup-Dienst) auf der Statusseite sichtbar | ✘ | S | Status zeigt nur App-Sicherungen; Healthcheck des Dienstes liegt in Docker |
| Mehrere Instanzen/Mandanten zentral verwalten | ✘ | L | heute eine Instanz je Schule (gewollt) |

### E. Installation

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| Docker-Compose für Schulen: App, PostgreSQL, Caddy mit HTTPS, Backup-Dienst, Volumes | ✔ | – | `docker-compose.yml` (Beispiel für SQLite: `docker-compose.sqlite.yml`) |
| `.env.example` mit allen Variablen und Erklärung | ✔ | – | um `SM_MODE` und weitere Variablen ergänzt |
| `.env` mit Zufallsgeheimnissen erzeugen | ✔ | – | `scripts/init-env.sh` |
| Installationsanleitung für Schul-IT/Schulträger | ✔ | – | `INSTALLATION.md` |
| Fertige Images aus einer Registry und signierte Releases | ◐ | M | CI baut Images; Veröffentlichungsprozess und Versionsnummern (`0.1.0`) festlegen |
| Code-Schutz der Auslieferung (nur Container, kompiliertes Python) | ✘ | M | Wunsch in `OFFENE-WUENSCHE.md` |
| Installation unter Windows Server / ohne Linux-Kenntnisse | ✘ | L | |

### F. Rechtliches und Datenschutz

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| Verzeichnis der Verarbeitungstätigkeiten (Vorlage) | ✔ | – | `datenschutz/vvt-vorlage.md` |
| TOMs aus dem Code abgeleitet | ✔ | – | `datenschutz/toms.md` |
| Datenschutzhinweise für Eltern, Schüler/innen, Lehrkräfte (Muster) | ✔ | – | `datenschutz/datenschutzhinweise-*.md` |
| Hinweis AV-Vertrag und DSFA | ✔ | – | `datenschutz/README.md` |
| Löschkonzept in der Software | ◐ | – | Agent S-A (`DATENSCHUTZ-LOESCHKONZEPT.md`) |
| **Juristische Prüfung der Vorlagen** (Landesrecht, Schulträger) | ✘ | M | durch Datenschutzbeauftragte/n bzw. Anwalt; die Vorlagen sind nur Entwürfe |
| Lizenzvertrag/EULA, AV-Vertragsmuster des Anbieters, Support-Vereinbarung | ✘ | M | Entscheidung E2–E5 |

### G. Hilfe und Aufräumen

| Punkt | Status | Aufwand | Nachweis / offen |
|---|---|---|---|
| Handbuch in der App: Kurzanleitungen für Administration, Schulleitung, Lehrkräfte, Eltern, Schüler/innen (Sie-Form) | ✔ | – | `docs/hilfe/*.md`, Menü *Hilfe*, `GET /manual` |
| Screenshots und Schritt-für-Schritt-Bilder in der Hilfe | ✘ | M | |
| Hilfe auf Englisch/weitere Sprachen | ✘ | M | |
| Demo-/Testtexte im Echtbetrieb ausgeblendet | ✔ | – | Demo-Block, Demo-Zugang, Demo-Hinweisband nur bei Modus demo bzw. `user.demo`; Test-Postausgang nur mit `SM_DEV_OUTBOX` |
| Platzhalter-Schulname „Meine Schule“ | ◐ | S | Assistent erkennt ihn als „nicht eingerichtet“; Standardwert im Modell bleibt (Kompatibilität) |
| Entwicklungsskripte (`dev.sh`, `preview.sh`, `docker-compose.dev.yml`) mit Beispielpasswörtern | ◐ | S | nur lokal; `SM_MODE=production` weist diese Passwörter zurück |

## 3. Entscheidungen (brauchen den Nutzer)

| Nr. | Frage | Empfehlung |
|---|---|---|
| E1 | Soll die **Hauptinstanz** auf echten Betrieb umgestellt werden? | **Nein.** Die Hauptinstanz bleibt Vorführung (`SM_MODE=demo`, ändert nichts am Verhalten). Für die erste echte Schule eine **eigene Instanz** mit `SM_MODE=production` aufsetzen. So vermischen sich Demo-Daten und echte Daten nie, und die Demo darf jede Nacht zurückgesetzt werden. Umstellen heißt nur `SM_MODE` setzen und neu starten – das habe ich nicht getan. |
| E2 | **Lizenzmodell** (Jahreslizenz je Schule, Staffel nach Konten, Einmalkauf, Abo) | Jahreslizenz je Schule, gestaffelt nach Zahl der Schüler/innen; Testbetrieb mit 25 Konten bleibt als Probierversion. Die Lizenztechnik (Lizenzschlüssel je Server unter einer Schule, tägliche signierte Prüfung beim Lizenzserver, Sofortsperre, Kulanzzeit nur lesen, danach gesperrt) trägt jedes dieser Modelle; Preise legt der Nutzer fest. Ein Testbetrieb ohne Lizenz entfällt in Produktion. |
| E3 | **Hosting-Angebot** (Schule betreibt selbst / Anbieter hostet) | Für die ersten Schulen **gehostet durch den Anbieter** (weniger Supportaufwand, einheitliche Updates), danach Selbstbetrieb für Schulen mit eigener IT anbieten. Gehosteter Betrieb braucht AV-Vertrag, Rechenzentrum in Deutschland und ein Update-/Wartungsfenster. |
| E4 | **Support** (Kanäle, Zeiten, Reaktionszeit, Wartungsfenster, Verantwortlicher) | E-Mail-Support werktags, Reaktion innerhalb eines Werktags, Fehler mit Fehlernummer aus dem Fehlerprotokoll; Wartungsfenster nachmittags; Notfallkontakt für Ausfälle am Schultag früh. Entscheidung über Telefon- oder Bereitschaftsdienst offen. |
| E5 | **Verträge**: Lizenzvertrag/EULA, AV-Vertragsmuster, Haftung, Datenschutzvereinbarung mit dem Lizenzserver | Von einer Anwältin bzw. einem Anwalt mit Schulrecht-Erfahrung prüfen lassen; die Vorlagen unter `datenschutz/` sind nur Entwürfe. |
| E6 | **Datenbank** für neue Schulen | PostgreSQL ab ca. 500 Konten oder wenn Hochverfügbarkeit zählt; SQLite nur für kleine Schulen (ein Prozess, einfache Sicherung). Die Compose-Vorlage nutzt PostgreSQL. |
| E7 | **Erst-Admin-Übergabe**: Einmalpasswort im Log (heute) oder einmaliger Einrichtungslink | Einrichtungslink mit Ablauf, der beim ersten Aufruf das Passwort setzen lässt (S). Das Log-Passwort ist akzeptabel, solange nur Schul-IT Zugriff auf die Container-Logs hat. |
| E8 | **Pilotschule**: Wer, wann, mit welchem Funktionsumfang? | Eine kleine Schule (≤ 500 Schüler/innen) mit Untis- oder SchILD-Export, Start zu einem Halbjahreswechsel; Abnahmeliste = Kapitel *Checkliste vor dem Livegang* in `INSTALLATION.md`. |
| E9 | **Weißlabel**: Soll die Schule den Produktnamen „Schulpuls“ ersetzen dürfen (`SM_APP_NAME`)? | Technisch möglich (`SM_APP_NAME`); als Lizenzfrage entscheiden. |
| E10 | **Direktimporte** (SchILD-XML, ASV-XML, LUSD, OneRoster): Priorität? | Nach Pilotschule entscheiden: Der Bedarf hängt vom Bundesland der ersten Kunden ab. Die CSV-Wege decken bis dahin alle ab. |

## 4. Nächste Schritte (Empfehlung, in dieser Reihenfolge)

1. E1/E3/E8 klären; Pilotinstanz mit `scripts/init-env.sh` aufsetzen und `INSTALLATION.md` einmal komplett durchspielen (Zeit messen, Stolperstellen eintragen).
2. Löschkonzept (Agent S-A) an den Schuljahreswechsel anschließen (`register_leaver_handler`), Test mit echter Warteliste.
3. Logo in Anmeldeseite und Briefe einbinden, Einrichtungslink statt Log-Passwort (je S).
4. Zeitraster- und Stundentafel-Vorlagen je Schulform und Bundesland (M); danach Direktimporte nach Bedarf.
5. Juristische Prüfung der Datenschutz-Vorlagen und der Verträge (E5).
6. Alarmierung per E-Mail bei fehlender Sicherung oder Fehlerhäufung (M).
