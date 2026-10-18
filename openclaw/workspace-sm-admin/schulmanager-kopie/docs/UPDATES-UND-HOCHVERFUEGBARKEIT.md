# Updates und mehrere Server je Schule

Stand 16.10.2026. Dieses Dokument beschreibt, wie der Anbieter neue Versionen **automatisch** auf die Schul-Server bringt (zu einem
vereinbarten Termin, in Wellen, mit Sicherung und Rückfall) und was nötig ist, wenn eine Schule **mehrere Server** mit denselben Daten
betreibt. Es kennzeichnet ehrlich, was gebaut und getestet ist und was nur Konzept ist (Abschnitt 1).

## 1. Was ist gebaut, was ist getestet, was ist Konzept?

| Baustein | Stand |
|---|---|
| Releases mit Kanal, Notizen, Mindestversion, „enthält Migration“, „abwärtskompatibel“; Manifest mit Ed25519 signiert (Anbieter: `lizenzserver/updates.py`, CLI `updates_cli`) | gebaut, automatisch getestet |
| Rollout-Plan: Zielgruppe, Test-Schulen zuerst, Wellen in Prozent mit Wartezeit, Pausieren/Abbrechen, Welle manuell freigeben (`rollout.py`, `updates.py`) | gebaut, automatisch getestet |
| Konkrete Termine (Datum + Uhrzeit, Europa/Berlin, in UTC gespeichert), Termin je Schule und je Server, „verpasst“-Behandlung, wiederkehrendes Wartungsfenster als Voreinstellung | gebaut, automatisch getestet (auch Sommer-/Winterzeit-Umstellung) |
| Server je Schule: gleichzeitig, nacheinander (höchstens *k* gleichzeitig, Reihenfolge, Wartezeit, Gesundheitsprüfung), Termin je Server, Wartungsfenster bei nicht abwärtskompatibler Migration, Schloss beim Anbieter mit Zeitüberschreitung | gebaut, automatisch getestet (Logik und Ablauf mit 1, 2, 3 und 5 Servern gegen eine Fake-Laufzeit) |
| Anbieter-Portal (`/admin/updates`): Releases, Rollouts, Wellen, Schulen und Server, Termine, Einstellungen, Protokoll | gebaut, automatisch getestet (Seiten und Aktionen); Bildschirmfotos siehe Abschnitt 10 |
| Update-Agent (`updater/`): Signatur und Downgrade-Schutz, Download mit Prüfsumme, Vorbereiten, Zeitfenster, Drain, Sicherung, Start, Gesundheitsprüfung, Rollback (Abbild und Datenbank), Wiederaufnahme nach Absturz | gebaut, automatisch getestet gegen einen lokalen Lizenzserver mit Test-Schlüsseln und eine **Fake**-Laufzeit |
| Docker-Anbindung des Agenten (`updater/runtime.py`, `DockerRuntime`; Compose-Dienst `updater`) | gebaut, **nicht ausgeführt**: auf diesem PC ist Docker nicht installiert, es läuft nirgends ein Test gegen echtes Docker. Erster Lauf auf dem Heimserver mit einer Test-Schule (Abschnitt 9) |
| App: Update-Ansicht unter `/betrieb` (anstehendes Update, Zeitfenster, einmal verschieben, „Jetzt installieren“, Modus, Audit), `/healthz/ready` mit Drain | gebaut, automatisch getestet (Backend und Oberfläche) |
| Leader-Sperre für Hintergrundjobs, Schutz vor verlorenen Planänderungen, Knoten-Name (`SM_NODE_ID`, `SM_HA`) | gebaut, getestet mit SQLite; der **Postgres-Advisory-Lock** ist nicht gegen echtes Postgres getestet |
| Echter Betrieb mit zwei oder mehr Knoten (gemeinsame PostgreSQL, gemeinsame Ablage, Lastverteiler) | **Konzept und Checkliste** (Abschnitt 8). Nie mit mehreren echten Knoten ausprobiert. |
| Registry-Verteilung | im Manifest und im Agenten vorgesehen (Digest-Pflicht), **nicht praktisch erprobt**; es gibt keine Registry |

## 2. Architektur

```
 Anbieter                                      Schule (je Server ein Agent)
 ┌────────────────────────────┐   HTTPS        ┌──────────────────────────────────────────────┐
 │ Lizenzserver               │◄───────────────│ updater  (Begleitdienst, Docker-Socket)      │
 │  • Releases + Manifest     │  poll (15 min) │   1. fragt: „darf ich?“ (Schlüssel + Instanz) │
 │    (Ed25519-signiert)      │  download      │   2. prüft Signatur, Downgrade, Prüfsumme     │
 │  • Rollouts, Wellen,       │                │   3. lädt vorab, wartet auf den Termin        │
 │    Termine, Schloss        │                │   4. drain → Sicherung → neue Version →       │
 │  • Portal /admin/updates   │                │      Gesundheitsprüfung → oder Rollback       │
 └────────────────────────────┘                └──────────────┬───────────────────────────────┘
                                                              │ Dateien im Datenordner
                                              ┌───────────────▼───────────────┐
                                              │ app  /betrieb: Update-Ansicht, │
                                              │ verschieben, „Jetzt installieren“, Audit │
                                              └────────────────────────────────┘
```

* **Der Agent führt nur einen Auftrag aus: „Version X installieren“.** Er führt nie Befehle, Skripte oder Adressen aus der Antwort aus.
  Alles, was er tut, ist fest einprogrammiert (laden, sichern, Abbild tauschen, prüfen).
* Die Antwort des Anbieters ist signiert und an die Anfrage gebunden (Nonce, Instanz-ID, Knotenname). Das Release selbst (das
  Manifest) ist zusätzlich signiert und enthält Version, Mindestversion, Migrationsangaben und Prüfsumme bzw. Digest.
* Die App kann keine Updates ausführen und hat keinen Zugriff auf den Docker-Socket. Sie und der Agent tauschen nur Dateien im
  Datenordner (`updater/status.json`, `updater/plan.json`).

## 3. Verteilung der Abbilder: Download oder Registry?

| | Download vom Lizenzserver (heute gebaut) | Registry des Anbieters |
|---|---|---|
| Aufwand heute | keiner: Datei in `LZ_RELEASE_DIR` legen | Registry betreiben oder mieten (GHCR, Docker Hub privat, Harbor) |
| Bandbreite | alles vom Heimserver des Anbieters (Abbild ca. 300–600 MB je Schule und Update) | Schichten werden zwischengespeichert, nur Änderungen laden; CDN des Anbieters |
| Wiederaufnahme bei Abbruch | nein (Neustart des Downloads, Datei wird vorab geladen, deshalb unkritisch) | ja, schichtweise |
| Integrität | SHA-256 und Größe im signierten Manifest | Digest im signierten Manifest (`image@sha256:…`), Docker prüft ihn |
| Zugriff | Lizenzschlüssel + Instanz-ID | Pull-Zugang je Schule oder öffentlich lesbar mit Digest-Pflicht |

**Empfehlung:** Jetzt mit dem **Download** vom Lizenzserver starten (keine neue Infrastruktur, funktioniert sofort), und sobald mehr als
etwa zehn Schulen aktiv sind oder der Heimserver die Last nicht mehr trägt (der Heimserver verliert abends zeitweise das Internet),
auf eine **Registry** umstellen. Das Manifest kennt beide Wege; der Agent akzeptiert nur Digest-Verweise, nie Tags.

## 4. Für den Anbieter: Release, Rollout, Termine

### 4.1 Release anlegen

```bash
# Abbild bauen und als Datei exportieren (auf dem Build-Rechner)
docker build --build-arg APP_VERSION=1.4.0 -t schulpuls-app:1.4.0 .
docker save schulpuls-app:1.4.0 -o schulpuls-1.4.0.tar

# Migration prüfen (Abschnitt 8.4)
python scripts/check_migration_compat.py

# Auf dem Lizenzserver (Heimserver): Datei in den Release-Ordner, Manifest signieren
python -m lizenzserver.updates_cli release-add --version 1.4.0 --image-file schulpuls-1.4.0.tar \
    --min-version 1.2.0 --migration --notes "Neue Wochenansicht"        # --breaking, wenn die Migration NICHT abwärtskompatibel ist
```

Im Portal: **Updates → Releases**. Versionen sind unveränderlich (eine Version lässt sich nur zurückziehen, nicht überschreiben).
`--min-version`: Eine Schule mit älterer Version bekommt automatisch den höchsten erreichbaren **Zwischenschritt** und danach das Ziel.

### 4.2 Rollout planen (Portal: Updates → Neuer Rollout)

* **Zielgruppe:** alle, nur Test-Schulen, ausgewählte Schulen.
* **Wellen:** Test-Schulen zuerst, dann *n* % der übrigen, der Rest nach *x* Stunden. Eine Welle öffnet erst, wenn **alle** Schulen der
  vorigen aktualisiert und gesund sind (Schulen ohne Kontakt seit 14 Tagen und vertraglich „nur manuell“ zählen nicht). Ein Fehler hält
  die späteren Wellen an; die laufenden Schulen werden nicht angehalten. „Nächste Welle jetzt freigeben“ überstimmt das Tor.
* **Termin:** ein **konkretes Datum mit Uhrzeit** (Ortszeit Europa/Berlin, gespeichert in UTC; Sommer-/Winterzeit stimmen, eine
  Uhrzeit, die es wegen der Umstellung nicht gibt, rutscht auf die nächste gültige). Der erste Server darf innerhalb von *h*
  Stunden nach dem Termin beginnen; weitere Server der Schule folgen auch danach.
* **Termin verpasst** (Server war aus): einstellbar je Rollout. Standard **„Anbieter fragen“**: die Schule wird im Portal als
  „verpasst“ markiert, nichts passiert von selbst; Alternativen: sofort nachholen oder auf das nächste Wartungsfenster warten.
* **Wiederkehrendes Wartungsfenster** (z. B. jeden Samstag 02:00–05:00) ist nur die Voreinstellung für Rollouts **ohne** konkreten
  Start („automatisch, sobald ein Update da ist“). Standard ohne Angabe: Samstag 02:00–05:00 Ortszeit.
* **Dringend:** ignoriert Zeitfenster und die Verschiebung durch die Schule. Gilt nicht für Schulen, die vertraglich „nur manuell“
  aktualisieren.
* **Ansage:** ein Text, den die Administration der Schule unter `/betrieb` sieht.

### 4.3 Strategie je Schule (Portal: Updates → Schule)

| Strategie | Verhalten |
|---|---|
| **gleichzeitig** | alle Server im selben Termin; kurze Ausfallzeit |
| **nacheinander (rollend)** | höchstens *k* Server gleichzeitig (Standard 1), nie alle; der nächste beginnt erst, wenn der vorige gesund ist; Reihenfolge einstellbar (Rang je Server); optionale Wartezeit (Minuten) zwischen den Servern |
| **eigener Termin je Server** | jeder Server hat sein eigenes Datum mit Uhrzeit, z. B. Haus A am 21.05. 00:00, Haus B am 22.05. 00:00 |
| **ein Server** | es gibt nur „im Termin“ |

Wählbar vom Anbieter; die Schule darf unter `/betrieb` nur dann zwischen „gleichzeitig“ und „nacheinander“ wählen, wenn der Anbieter
es erlaubt hat. Ist die **Migration nicht abwärtskompatibel**, gilt unabhängig davon automatisch das **Wartungsfenster**: alle Server
bereiten vor, die Folger werden angehalten, der erste migriert und startet, danach starten die anderen. Das Portal zeigt den Hinweis.

**Das Schloss (verteilte Abstimmung):** Jeder Agent fragt „darf ich jetzt?“. Der Anbieter-Server gibt die Freigabe im selben
Augenblick als „belegt“ in seiner Datenbank vermerkt (kein zweiter Server bekommt sie gleichzeitig). Meldet ein belegter Server
länger als 90 Minuten keinen Fortschritt oder bleibt stumm, gilt er als **hängend**: die Schule wird angehalten, der Anbieter
entscheidet im Portal (Erneut versuchen, Abbrechen). Ein Fehler (`Rollback`/`Fehler`) hält ebenfalls die ganze Schule an.

## 5. Ablauf auf dem Schul-Server (Agent)

1. Alle 15 Minuten (häufiger, solange ein Update bereitliegt): Anfrage mit Lizenzschlüssel, Instanz-ID, Version, Zustand.
2. Antwort prüfen: Signatur (Schlüssel fest im Agent-Image), Nonce, Instanz, Knoten. Release prüfen: Signatur, **Downgrade-Schutz**
   (nur neuer als die laufende **und** als die höchste je installierte Version), Mindestversion, Form der Verteilung.
3. **Vorab laden:** Download mit Prüfsumme (oder Registry-Pull per Digest), Image laden; zu wenig freier Speicher bricht ab.
4. **Termin abwarten.** Die Schule kann einmal bis zu 7 Tage verschieben (nicht bei „dringend“), im Modus „nur manuell“ gibt es
   „Jetzt installieren“.
5. **Installieren:** Datei `drain-<Knoten>.flag` anlegen (`/healthz/ready` → 503, der Lastverteiler nimmt den Server heraus) → warten →
   **Sicherung** (`backup.sh --label vor-update-<Version>`: Datenbank + Dateien) → neues Abbild starten (die App migriert beim Start) →
   **Gesundheitsprüfung** (`/healthz` ok und Datenbank ok, Version stimmt, Startseite erreichbar, mehrfach hintereinander) → Drain-Datei
   löschen.
6. **Rollback bei Fehler:** altes Abbild zurück. War die Migration abwärtskompatibel, bleibt die Datenbank; war sie es nicht oder
   läuft die alte Version auch dann nicht, wird die **Sicherung eingespielt** – aber nur, wenn kein anderer Server dieselbe Datenbank
   gerade benutzt. Sonst meldet der Agent „Fehler“, und der Anbieter entscheidet. Fehlgeschlagene Versionen werden **nicht von selbst
   erneut** versucht; der Anbieter drückt „Erneut versuchen“.
7. Jeder Schritt wird dem Anbieter gemeldet (Protokoll, Schloss) und steht unter `/betrieb`. Wurde der Agent mitten im Update beendet,
   führt er es beim Start zu Ende oder rollt zurück.
8. Versionswechsel schreibt die App beim Start in das Audit-Protokoll (`update.version_changed`); Wünsche der Administration
   (`update.postpone`, `update.install_now`, `update.mode`, `update.strategy`) ebenfalls.

## 6. Sicherheit

| Maßnahme | Umsetzung |
|---|---|
| Nur signierte Releases | Ed25519-Signatur über das gesamte Manifest; jede andere Verteilungsart oder fehlende Felder werden abgelehnt |
| Schlüssel-Pinning | Der öffentliche Anbieter-Schlüssel wird beim Bauen des Agent-Images fest eingetragen (`--build-arg VENDOR_PUBKEY`) und im Zustand des Agenten gemerkt; ändert er sich, hält der Agent an |
| Keine beliebigen Befehle | Der Agent kennt nur „Version X installieren“; Image-Verweis wird gegen ein enges Muster geprüft; Registry nur per Digest, optional nur ein erlaubtes Präfix |
| Downgrade-Schutz | Nur Versionen oberhalb der laufenden **und** der höchsten je installierten; zurückgezogene Releases werden nicht ausgeliefert |
| Antworten nicht wiederholbar/fälschbar | Nonce, Instanz-ID und Knotenname sind in der signierten Antwort; falsch signierte Antworten werden wie „Anbieter nicht erreichbar“ behandelt |
| Abschaltbar | Vertraglich „nur manuell“ (Anbieter-Einstellung) oder `UPDATER_MODE=manual` bzw. unter `/betrieb`; ganz aus: Agent nicht starten |
| Audit | Aktionen der Administration und Versionswechsel im Audit-Protokoll der App; Zustandswechsel im Protokoll des Anbieters |
| Sperre und Sofortsperre | Gesperrte oder gekündigte Schulen bekommen kein Update und keinen Download |

### Der Docker-Socket

Der Agent braucht Zugriff auf `/var/run/docker.sock` des Hosts, um den Dienst `app` neu zu erstellen. **Das ist faktisch Root-Zugriff
auf den Host:** wer den Agenten übernimmt, kann Container mit beliebigen Rechten starten. Gegenmaßnahmen und Abwägung:

* Der Agent ist klein, hat keinen Netzwerkdienst, läuft schreibgeschützt ohne Capabilities, spricht nur den Anbieter an und führt nur
  signierte Aufträge aus. Das Risiko ist damit auf „der Anbieter-Schlüssel wird gestohlen“ begrenzt (Schlüssel gut schützen,
  idealerweise den Release-Schlüssel getrennt vom Lizenz-Schlüssel führen).
* **Alternative A – systemd-Timer auf dem Host** (nicht gebaut): ein kleines Skript auf dem Host holt das Release, prüft die Signatur
  und ruft `scripts/compose.sh up -d app` auf. Kein Container mit Socket, dafür Installation auf dem Host.
* **Alternative B – Docker-Socket-Proxy** (z. B. `tecnativa/docker-socket-proxy`), der nur die nötigen API-Teile freigibt
  (Container, Images, `POST`). Compose braucht viele davon; der Schutz ist geringer als er aussieht.
* **Alternative C – rootless Docker** für die Schul-Installation: ein Einbruch bleibt auf den Benutzer beschränkt.
* **Alternative D – nur manuell:** der Agent läuft ohne Socket nur als Melder (`offer`), die IT der Schule installiert selbst.

Entscheiden Sie das je Schule (Abschnitt 11).

## 7. Für die Schule: `/betrieb`

Karte „Updates“: installierte Version, Stand des Update-Dienstes, anstehendes Update mit Release-Notizen, **Zeitfenster/Termin in
Ortszeit**, Hinweis zur Datenbank-Änderung und – bei mehreren Servern – zur Reihenfolge, „Jetzt installieren“, **einmal verschieben**
(1–7 Tage; nicht bei dringenden Sicherheitsupdates), Umschalten auf „nur manuell“ (außer vertraglich festgelegt), Protokoll.

## 8. Mehrere Server mit denselben Daten

### 8.1 Was die App dafür braucht (Prüfung des Ist-Stands)

| Anforderung | Stand in der App |
|---|---|
| Gemeinsame **PostgreSQL**-Datenbank | Vorhanden (Produktion nutzt Postgres). **SQLite geht nicht** für mehrere Knoten. |
| **Sitzungen in der Datenbank** | Ja (`user_sessions`, Anmeldesperren in `login_attempts`); beliebiger Knoten kann eine Sitzung bedienen. |
| **Planungsdokument** | Liegt im Speicher je Prozess und wird aus der Datenbank nachgeladen (höchstens alle 2 s bei Zugriff, vor jeder Änderung sofort). Neu: bei `SM_HA=1` schreibt ein Knoten nur, wenn kein anderer inzwischen eine neuere Version gespeichert hat (Postgres: Advisory-Lock); sonst Antwort 409 „bitte erneut versuchen“. |
| **Gemeinsame Dateiablage** | Uploads und Dateien liegen im Dateisystem (`SM_FILES_DIR`). Für mehrere Knoten muss das **gemeinsames Netzlaufwerk** sein (NFS o. ä.). **Offen:** Nicht mit mehreren echten Knoten getestet; Chat-Bilder liegen in der Datenbank. |
| **Hintergrundjobs nur einmal** | Neu: Leader-Sperre (`leader.py`, Pacht in `system_state`, 30 s). Auf dem Leader laufen Benachrichtigungen, Autoplaner, Mail-Abruf, Ferienimport und Wartung; fällt er aus, übernimmt ein anderer nach spätestens 30 s. Die Lizenzprüfung läuft auf jedem Knoten. |
| **Live-Updates (SSE)** | Der Ereignisbus ist **prozesslokal**. Planänderungen anderer Knoten kommen erst beim nächsten Nachladen an; Auftragsfortschritt (z. B. Stundenplan-Berechnung) kommt nur vom Knoten, der den Auftrag gestartet hat. **Offen:** Ein Ereignis-Relay über die Datenbank ist nicht gebaut. Darum Lastverteiler mit festem Knoten je Nutzer (Cookie) und kurzem Nachladen. |
| **Hintergrund-Aufträge im eigenen Prozess** (Stundenplan-Generator) | Status liegt im Speicher des startenden Knotens; Nachfragen müssen dort ankommen (Cookie-Bindung im Lastverteiler). |
| **Lastverteiler/Proxy** | Beispiel `deploy/ha/Caddyfile.mehrknoten.example` (Cookie-Bindung, Gesundheitsprüfung `/healthz/ready`). Der Proxy selbst ist ein einzelner Ausfallpunkt – dafür braucht es zwei Proxys mit gemeinsamer Adresse. |
| **Gleiche Schlüssel** | `SM_SECRET_KEY` und `SM_ENCRYPTION_KEYS` müssen auf allen Knoten identisch sein. |
| **Lizenz** | Jeder Server hat einen eigenen Lizenzschlüssel und eine eigene Instanz-ID (Lizenzmodell „Schule mit N Server-Lizenzen“). Bei gemeinsamem Datenordner teilen sich Knoten `license.json`/`license_state.json` und damit die Instanz-ID – dann ist der Server-Schlüssel nicht je Knoten unterscheidbar; ein Datenordner **je Knoten** für `/app/data` (Lizenz, Drain-Datei, Agent-Austausch) und nur die Dateiablage `SM_FILES_DIR` gemeinsam ist der saubere Zuschnitt. |

### 8.2 Checkliste für den ersten echten Zwei-Knoten-Betrieb (Konzept)

1. PostgreSQL außerhalb der beiden Knoten (eigener Host oder verwalteter Dienst), Sicherungen dort.
2. Gemeinsame Dateiablage einrichten und als `SM_FILES_DIR` auf beiden Knoten einbinden; Schreibrechte für UID 10001.
3. Je Knoten ein eigenes `.env` mit gleichem `SM_SECRET_KEY`, `SM_ENCRYPTION_KEYS`, `SM_DATABASE_URL`, aber `SM_NODE_ID=app1` bzw. `app2` und `SM_HA=1`.
4. Je Knoten ein eigener Lizenzschlüssel (Portal: Schule → Server), eigener Datenordner (`app_data`).
5. Lastverteiler nach `deploy/ha/Caddyfile.mehrknoten.example`; `/healthz/ready` als Prüfung.
6. Je Knoten den Update-Agenten (`UPDATER_NODE=app1|app2`, `SM_NODE_ID` gleich).
7. Im Portal bei der Schule Strategie „nacheinander“ und Reihenfolge setzen.
8. **Probelauf mit einer Test-Schule:** Knoten 1 abschalten, Anmeldung, Planänderung, Wiederanlauf; Update mit abwärtskompatibler Migration; Absturz eines Knotens während des Updates; Wartungsfenster mit nicht kompatibler Migration.

### 8.3 Rollende Updates

Knoten 1: Drain-Datei → Lastverteiler nimmt ihn heraus → Sicherung → Update → Gesundheitsprüfung → wieder rein. Erst dann Knoten 2.
Das erzwingt der Anbieter-Server (Schloss), nicht die Knoten untereinander. Voraussetzung ist, dass die **Migration abwärtskompatibel**
ist: Während Knoten 1 neu und Knoten 2 noch alt ist, laufen beide Versionen auf demselben (neuen) Schema.

### 8.4 Expand/Contract – Regel für Migrationen

Eine Migration in einem Release, das rollend ausgeliefert wird, darf **nur erweitern**:

* erlaubt: neue Tabelle, neue Spalte mit `NULL` oder `server_default`, neuer Index, Daten **ergänzen**;
* verboten (in einem Schritt): Spalte oder Tabelle löschen oder umbenennen, Typ ändern, Spalte auf `NOT NULL` setzen, neue
  `NOT NULL`-Spalte ohne `server_default`, vorhandene Werte so umschreiben, dass der alte Code sie nicht mehr versteht.

Aufteilen in zwei Releases: Release *n* fügt die neue Spalte hinzu und schreibt in beide; Release *n+1* löscht die alte. Das Skript
`scripts/check_migration_compat.py` findet die offensichtlichen Fälle, der Test `tests/test_migration_compat.py` bricht bei einer neuen
Migration mit Befund ab. **Prüfung der vorhandenen 51 Migrationen:** Nur `0044_security_hardening` ist nicht abwärtskompatibel
(löscht `password_enc`, setzt `expires_at` auf NOT NULL); sie ist längst überall eingespielt. Das Skript erkennt **keine** Daten-
migrationen, die Werte umschreiben (z. B. `0045_secrets_at_rest` hasht iCal-Token): solche immer von Hand prüfen. Release mit
Befund → `--breaking` anlegen: Mehr-Server-Schulen wechseln automatisch ins Wartungsfenster.

## 9. Einrichten auf dem Heimserver (Anbieter-Seite)

Der Heimserver ist das Ziel für alle Dienste (nie auf dem PC). Befehle (Beispiel mit Docker; Pfade und Namen anpassen):

```bash
# 1. Lizenzserver aktualisieren (enthält jetzt die Update-Verwaltung); Daten-Volume bleibt
docker build -t lizenzserver ./lizenzserver && docker rm -f lizenz && \
docker run -d --name lizenz --restart unless-stopped -p 8200:8200 -v lizenz-data:/data \
    -e LZ_ADMIN_PASSWORD_HASH="$(cat admin_password.hash)" -e LZ_TRUST_PROXY=1 lizenzserver

# 2. Erstes Release einspielen
docker cp schulpuls-1.4.0.tar lizenz:/data/releases/
docker exec lizenz python -m lizenzserver.updates_cli release-add --version 1.4.0 --image-file /data/releases/schulpuls-1.4.0.tar
docker exec lizenz python -m lizenzserver.updates_cli rollout-add --release 1.4.0 --name "Erstes Update" --tests
docker exec lizenz python -m lizenzserver.updates_cli rollout-start 1

# 3. Portal öffnen: https://<lizenzserver>/admin/updates
```

Auf der Test-Schule: `.env` um `UPDATER_HOST_DIR=/pfad/zum/projekt` ergänzen, Agent-Image bauen
(`docker build -f updater/Dockerfile --build-arg VENDOR_PUBKEY=<öffentlicher Schlüssel> -t schulpuls-updater .`), dann
`scripts/compose.sh --profile updater up -d updater`. **Wichtig:** Danach immer `scripts/compose.sh` statt `docker compose` benutzen,
sonst fällt die App auf das Abbild aus `.env` zurück (der Agent merkt sich das installierte Abbild in `update.env`).

## 10. Tests und Bildschirmfotos

* Anbieter: `python -m pytest lizenzserver/tests/test_updates.py lizenzserver/tests/test_updates_portal.py` (Zeitfenster, Sommer-/Winterzeit,
  Wellen, Schloss, Termine, verpasste Termine, Strategien für 1/2/3/5 Server, Portal).
* Agent: `python -m pytest updater/tests` (Signatur, Downgrade, Rollback-Entscheidungen, Abläufe mit Erfolg, Fehler, Migration,
  Absturz, zwei Server nacheinander, Wartungsfenster mit drei Servern).
* App: `python -m pytest tests/test_updates_ha.py tests/test_migration_compat.py`.
* Nicht automatisch getestet: echtes Docker, echte Registry, echtes Postgres, echte zwei Knoten (Abschnitt 1).

## 11. Offene Entscheidungen

1. **Registry:** beim Download bleiben oder jetzt eine Registry aufsetzen (Abschnitt 3)?
2. **Hosting des Lizenz-/Update-Servers:** Der Heimserver verliert abends zeitweise das Internet. Für Updates unkritisch (Agenten versuchen es
   erneut), für die Lizenzprüfung nicht. Ein eigener kleiner Server beim Hoster wäre robuster.
3. **Docker-Socket oder Alternative** (Abschnitt 6) je nach Schule.
4. **Zwei-Knoten-Betrieb:** erst mit Probelauf (Abschnitt 8.2) anbieten; Ereignis-Relay für Live-Updates und gemeinsame Ablage sind
   nicht gebaut/erprobt. Soll das ein Produktmerkmal werden?
5. **Release-Schlüssel getrennt vom Lizenz-Schlüssel führen** (heute derselbe Ed25519-Schlüssel signiert beides).
