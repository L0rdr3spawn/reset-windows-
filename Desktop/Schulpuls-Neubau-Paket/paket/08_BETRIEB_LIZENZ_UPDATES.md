# 08 · Betrieb, Lizenz, Updates, Zahlungen, Demo (Kürzel BET)

Betriebs-Spezifikation für den Neubau. Quellen: Betriebs-, Installations-, Einrichtungs- und Vorschau-Unterlagen, Lizenz-/Update-/Zahlungswerte, Konfigurationswerte, Wartungs- und Sicherungswerte, Gesprächsstand bis 17.10.2026 (neuester Stand zählt). Alle Werte stammen aus dem Ist-Zustand oder aus ausdrücklichen Wünschen des Betreibers; nichts ist erfunden, Unklares steht als `[unklar: …]`.

## 0. Geltung, Begriffe, Legende

**Geltungsbereich.** Dieses Dokument beschreibt drei Software-Teile:

1. **Schul-Instanz**: die Anwendung samt Datenbank, Dateiablage, Hintergrundjobs, Wartung, Lizenzprüfung und Statusseite. Läuft je Schule (Kap. 1).
2. **Anbieter-Lizenzserver mit Anbieter-Portal**: läuft beim Anbieter; verwaltet Schulen, Server-Lizenzen, Zahlungen, Tarife und Update-Freigaben (Kap. 12 bis 15).
3. **Update-Agent**: Begleitdienst bei der Schule, der freigegebene Versionen installiert (Kap. 15).

Fachliche Details anderer Bereiche stehen dort: Anmeldung, Sitzungen, Passwortregeln, Zwei-Faktor (ANM); Löschfristen, Verschlüsselungsverfahren, Audit-Inhalte (DAT); API-Zugänge und Importe (INT); Einrichtungsassistent im Detail (STA); Arbeitsweise und Freigaben für Server-Eingriffe (PRI). Hier stehen die Betriebsanforderungen, die diese Bereiche voraussetzen.

**Begriffe.**

| Begriff | Bedeutung |
|---|---|
| Betreiber | Wer eine Schul-Instanz technisch betreibt (Schul-IT, Schulträger oder der Anbieter bei gehostetem Betrieb). Hat Serverzugang. |
| Anbieter | Software-Inhaber; betreibt Lizenzserver, Portal, Demo; stellt Lizenzen aus. |
| Administration | Rolle `admin` der Schul-Instanz (technische Verwaltung); Recht `system.admin`. |
| Knoten | Ein Server, der dieselbe Instanz bedient (Kap. 15.5). Standard: ein Knoten. |
| Instanz-ID | Zufällige Kennung (24 Hexzeichen), die eine Installation gegenüber dem Lizenzserver ausweist. |
| Gruppen-Kennung | Öffentliche Kennung einer Schule beim Anbieter, Format `G-` plus 8 Hexzeichen (Großbuchstaben). |
| Kulanz | Stufe „nur lesen“ vor der Sperre. |

**Priorität.** P0 Pflicht/Sicherheit/Recht, P1 Kernfunktion, P2 wichtig, P3 Wunsch. **Status.** `Status: Ist` = im Altbestand gebaut (Verhalten ist Mindestumfang des Neubaus); `Status: offen` = gewünscht, vorgeschlagen oder Lücke, noch nicht gebaut.

**Verbindliche Gestaltungsregeln für alle Betriebs- und Portalseiten.** Anrede „Sie“; Erklärungen nur über Hilfe-Symbol bzw. Hilfetext, keine Erklär-Absätze; eigene App-Dialoge statt Browser-Popups (auch für Bestätigungen im Anbieter-Portal); Anbieter-Portal in derselben Gestaltung wie die Schul-Oberfläche (Farben, Schrift, Karten, Tabellen, hell/dunkel/automatisch, am Handy nutzbar); fremde Daten und unberechtigt angefragte Betreiber-Inhalte liefern 404; jede schreibende Aktion wird protokolliert, ohne Inhalte und ohne Geheimnisse; der Produktname steht nur an einer Stelle der Konfiguration (technische Kennungen wie Metrik-Präfix, Cookie-Name, Image-Name und Manifest-Produktkennung sind davon getrennte feste Konstanten, je eine Stelle).

---

## 1. Betriebsmodell und Instanzen (Mehrinstanz)

**BET-001** · P0 · Status: Ist · Eine Instanz je Schule
Jede Schule läuft als eigene Instanz mit eigener Datenbank, eigener Dateiablage, eigenem `SM_SECRET_KEY` und eigenem `SM_ENCRYPTION_KEYS`. Schlüssel, Datenvolumen oder Datenbanken werden nie zwischen Schulen geteilt. Mehrere Schulen in einer Instanz (Multi-Mandant) sind bewusst nicht vorgesehen (Mandantentrennung). Mehrere Server derselben Schule sind Knoten derselben Instanz (Kap. 15.5).
Abnahme: Zwei Instanzen A und B mit getrennten Volumes: Sitzungs-Cookie oder API-Zugangs-Token aus A gegen B → 401; eine Zeile aus A in die Datenbank von B kopiert → verschlüsselte Felder sind nicht lesbar (Fehler „ungültig“ bzw. „nicht lesbar“, nie Klartext); die Installationsanleitung enthält die Pflicht „eigener zufälliger Geheimschlüssel (32 Byte, hex) je Schule“.

**BET-002** · P1 · Status: Ist · Instanzrollen beim Anbieter
Der Anbieter betreibt: Hauptinstanz (HTTPS), Demo-Instanz (Modus `demo`, nächtlicher Reset, Kap. 16), Test-Instanz „neu“ (leer: nur ein Admin-Konto und der Einrichtungsassistent; bildet eine Kundenschule nach) und den Lizenzserver (eigener Container, Portal unter `/admin`). Jede Instanz hat eigene Datenbank, eigene Dateiablage und eigenes Geheimnis; es gibt keine gemeinsamen Daten oder Schlüssel.
Abnahme: Alle vier Dienste melden ihren Gesundheitsstatus „ok“ (`/healthz` bzw. Lizenzserver-Gesundheitsabfrage); Löschen der Demo-Datenbank ändert Hauptinstanz und Test-Instanz nicht; im Betriebsplan sind keine gemeinsamen Volumes oder Schlüssel eingetragen.

**BET-003** · P0 · Status: offen · Kundeninstanzen nur im Produktivmodus
Jede Instanz mit echten Schüler-/Schuldaten und die Test-Instanz „neu“ (die eine Kundenschule nachstellen soll) laufen im Modus `production`. Stand 17.10.2026: alle drei Schulinstanzen inklusive Hauptserver liefen noch im Entwicklungsmodus (Schutzmechanismen aus, Demo-Sperre ungeprüft); die Frage „Soll ich zumindest die Test-Instanz umstellen?“ ist unbeantwortet. Empfehlung E1 des Berichts (nicht entschieden): Hauptinstanz bleibt Vorführung (`demo`), die erste echte Schule bekommt eine eigene Instanz im Modus `production`; Umstellen = `SM_MODE` setzen und neu starten.
Abnahme: Die Statusseite `/betrieb` zeigt den Modus; eine Instanz im Modus `development` zeigt dort eine rote Zeile „Entwicklungsmodus: Schutzmechanismen sind abgeschaltet“; nach Umstellung auf `production` und Neustart ist die Zeile grün und die Demo-Funktionen sind verweigert (BET-011).

**BET-004** · P3 · Status: offen · Eigene Subdomain je Schule und zentraler Anmeldepunkt
Wunsch des Betreibers: pro Schule eine Subdomain, auf der sich nur deren Leute anmelden; eigene Schul-Domain nur als Option (Schulen haben ihre Domain schwer zugänglich). Empfehlung: Instanz je Schule mit eigener Datenbank unter Subdomain; ein zentraler Anmeldepunkt (Platzhalter `<anbieter-login-adresse>`) erst, sobald eine zweite Schule kommt. `[unklar: Entscheidung offen]`
Abnahme: Zwei Instanzen unter zwei Subdomains sind gleichzeitig erreichbar; ein Sitzungs-Cookie der einen gilt nicht auf der anderen; die Entscheidung über den zentralen Anmeldepunkt ist schriftlich dokumentiert, bevor die zweite Schule startet.

**BET-005** · P3 · Status: offen · Mehrere Schulen je Konto
Wunsch (12.10.): Eltern mit Kindern an zwei Schulen wechseln die Schule im selben Konto. Das widerspricht „eine Instanz je Schule“ und setzt einen zentralen Anmeldepunkt (BET-004) voraus; zurückgestellt („später“).
Abnahme: Entscheidungsvorlage vorhanden, die zeigt, wie ein Konto zwei Instanzen erreicht, ohne Daten zwischen Instanzen zu teilen; bis dahin meldet sich ein Konto nur an der Instanz seiner Schule an.

---

## 2. Betriebsmodi und Pflichtprüfungen beim Start

**BET-006** · P0 · Status: Ist · Drei Betriebsmodi
Der Modus wird über `SM_MODE` gewählt: `production`, `demo`, `development`.

| Modus | Wirkung |
|---|---|
| `production` (Echtbetrieb einer Schule) | Demo-Funktionen vollständig aus: Demo laden (Oberfläche, Kommandozeile, Erststart), Demo-Zugang ausgeben, Rollen-Schnellknöpfe, Demo-Block der Administration, Demo-Hinweisband, Demo-Konten. Lizenzprüfung immer aktiv (`SM_LICENSE_ENFORCE`, `SM_LICENSE_PUBKEY`, `SM_LICENSE_SERVER` ohne Wirkung; Lizenzserver-Adresse und Prüfschlüssel fest eingebaut). Test-Postausgang, Test-Anmeldedienst und API-Dokumentation aus (`SM_ENABLE_DOCS` Standard `off`). Cookies mit Secure. Log-Format `json`. Ersatz-Passwörter und Ersatz-Schlüssel gesperrt. |
| `demo` (Vorführung) | Demo laden und Demo-Konten erlaubt; Demo-Zugänge nur mit `SM_DEMO_PUBLIC` (im Modus `demo` Standard 1); Demo-Hinweisband sichtbar; Test-Anmeldedienst verboten (Start bricht ab); Test-Postausgang nur mit `SM_DEV_OUTBOX`; die Instanz darf jede Nacht zurückgesetzt werden; Lizenzprüfung frei. |
| `development` (lokale Entwicklung) | Test-Postausgang standardmäßig an, wenn die Basisadresse lokal ist; Test-Anmeldedienst nur mit `SM_SSO_DEV_MOCK=1` (Standard aus); Lizenzprüfung frei (mit `SM_LICENSE_ENFORCE=1` erzwingbar); Testschlüssel und Testserver konfigurierbar; lokaler Start mit frischer SQLite-Datenbank und Demo (Backend Port 8000, Frontend Port 5173); Entwicklungs-Erstpasswort für den Erst-Admin. |

Abnahme: Je Modus ein Startversuch: `production` + `SM_LOAD_DEMO=1` → Start bricht ab; `production` → `POST /api/v1/admin/demo` liefert 403 und die Oberfläche zeigt keinen Demo-Knopf; `demo` + `SM_SSO_DEV_MOCK=1` → Start bricht ab; `demo` zeigt das Hinweisband; `development` auf localhost erlaubt Test-Postausgang unter `/test-postausgang`; in `production` ist `/test-postausgang` nicht vorhanden (404).

**BET-007** · P0 · Status: offen · Kein stiller Entwicklungsmodus
Ist-Befund: Ohne `SM_MODE` und ohne `SM_ENV=production` gilt der Entwicklungsmodus; der Erst-Admin bekommt dann ein bekanntes Entwicklungs-Passwort. Im Neubau gilt ohne `SM_MODE` der Modus `production` (Start prüft streng, BET-008). Der Entwicklungsmodus gilt nur bei ausdrücklichem `SM_MODE=development`. `SM_ENV` bleibt nur als Rückfall-Name für übernommene Altinstanzen (`production` aus `SM_ENV` zählt wie `SM_MODE=production`); widersprüchliche Angaben (`SM_MODE=production` bei `SM_ENV=development` und umgekehrt) lassen den Start abbrechen. `[unklar: ob Altinstanzen übernommen werden müssen; sonst entfällt SM_ENV]`
Abnahme: Start ohne jede Modus-Variable und ohne Pflichtwerte → bricht mit der Fehlerliste von BET-008 ab (kein Entwicklungs-Erstpasswort); Start mit `SM_MODE=development` → startet lokal; `SM_MODE=production` + `SM_ENV=development` → Abbruch mit Meldung zum Widerspruch; ungültiger Wert für `SM_MODE` → Abbruch.

**BET-008** · P0 · Status: Ist · Pflichtprüfungen beim Start (Produktion)
Im Modus `production` bricht der Start mit einer vollständigen Fehlerliste ab (alle Fehler auf einmal, Meldung nennt Variable und Grund, nie Schlüsselwerte). Hinweise (BET-009) blockieren den Start nicht.

| Prüfung | Bedingung → Abbruch |
|---|---|
| `SM_SECRET_KEY` | fehlt, kürzer als 32 Zeichen, beginnt mit `BITTE_AENDERN` oder enthält `CHANGE_ME` |
| `SM_ENCRYPTION_KEYS` | fehlt oder Format ungültig (je Eintrag `Kennung:Base64`, 32 Byte; Kennung 1 bis 32 Zeichen aus A–Z a–z 0–9 `_` `-`; doppelte Kennung; `dev` reserviert) |
| `SM_BASE_URL` | fehlt oder beginnt nicht mit `https://` (Ausnahme: lokale Adresse localhost, 127.0.0.1, [::1]) |
| `SM_COOKIE_SECURE` | auf 0 gesetzt |
| Beispiel-/Platzhalterwerte | Werte der Vorlage (`BITTE_AENDERN…`) noch gesetzt |
| `SM_ADMIN_PASSWORD` | gleich einem bekannten Entwicklungs-Passwort oder Platzhalter |
| Demo-Schalter | `SM_LOAD_DEMO=1` oder `SM_DEMO_PUBLIC=1` |
| Test-Schalter | `SM_DEV_OUTBOX=1` oder `SM_SSO_DEV_MOCK=1` |
| `SM_SCRYPT_N` | keine Zweierpotenz, kleiner 2, oder kleiner 16384 |
| `SM_AUTH_CODE_MINUTES` | kleiner 1 oder größer 1440 |
| `SM_SMS_PROVIDER` | nicht leer/`log`/`webhook`/`twilio`/`seven`; `webhook` ohne http(s)-Adresse; `twilio` ohne Konto-Kennung, Token oder Absender; `seven` ohne Token; `SM_SMS_TIMEOUT` ≤ 0 |
| Datei-Grenzen | `SM_UPLOAD_MAX_MB` nicht größer 0 oder größer 10240; Datei- oder Chat-Kontingent kleiner 0; Upload-Rate kleiner 0 |
| Virenscan | `SM_CLAMAV_PORT` nicht 1 bis 65535; `SM_CLAMAV_TIMEOUT` ≤ 0; `SM_CLAMAV_REQUIRED=1` ohne `SM_CLAMAV_HOST` |
| Zahlenwerte | Variable mit Zahlenwert enthält Text (Meldung nennt die Variable) |
| Unvollständige Anmeldedienste | Anbieter-Einstellungen unvollständig (Pflichtfelder fehlen) |

Abnahme: Für jede Tabellenzeile ein Startversuch mit genau diesem Fehler: Start bricht ab, die Meldung nennt die betroffene Variable, im Log steht kein Schlüssel- oder Passwortwert; sind mehrere Fehler gesetzt, erscheinen alle in einer Liste; eine vollständig gültige Konfiguration startet.

**BET-009** · P1 · Status: Ist · Startwarnungen (blockieren nicht)
Warnungen im Log und auf der Statusseite: SQLite bei etwa 500 oder mehr Konten (PostgreSQL empfohlen); kein E-Mail-Versand (`SM_SMTP_HOST` oder `SM_SMTP_FROM` fehlt: Passwort-Zurücksetzen per E-Mail, Benachrichtigungen und Briefe per E-Mail gehen nicht); `SM_REQUIRE_2FA_ROLES` leer (Empfehlung `admin`, `schulleitung`, `sekretariat`); `SM_AUTO_BACKUP_HOURS` = 0; `SM_TRUST_PROXY` nicht gesetzt (hinter Proxy sieht die Drosselung je Adresse nur die Proxy-Adresse); `SM_SMS_PROVIDER=log` in Produktion (SMS werden nur protokolliert); `SM_DEV_OUTBOX=1` parallel zu SMTP/SMS; `SM_TRUST_PROXY=1` ohne `SM_TRUSTED_PROXIES` oder mit `*`.
Abnahme: Je Bedingung ein Start: Instanz startet, die Warnung steht im Log und als gelber Punkt auf `/betrieb`; Beseitigung der Ursache entfernt die Warnung.

**BET-010** · P1 · Status: Ist · Konfigurationsprüfung ohne Start
Der Befehl `check-config` (im Container über den App-Container) prüft die Konfiguration ohne Start und gibt „in Ordnung“ oder die Problemliste aus (Fehler wie BET-008, Warnungen wie BET-009).
Abnahme: Mit gültiger Konfiguration → Ausgabe „in Ordnung“; mit fehlendem `SM_SECRET_KEY` → Problemliste mit diesem Eintrag; der Befehl startet keinen Server und ändert keine Daten.

**BET-011** · P0 · Status: Ist · Demo-Funktionen im Echtbetrieb serverseitig verweigert
„Demo laden“ und „Demo-Zugang ausgeben“ werden im Modus `production` vom Server verweigert, unabhängig vom Weg (Oberfläche, Programmierschnittstelle, Kommandozeile `load-demo`, Start-Schalter `SM_LOAD_DEMO`). Die Oberfläche zeigt die Knöpfe nur, wenn der Server sie erlaubt. Eine Verweigerung verändert keine Daten. Das Demo-Passwort steht nie im Log.
Abnahme: In `production`: `POST /api/v1/admin/demo` → 403; `load-demo` → Fehlermeldung ohne Datenänderung (Zeilenzahlen vor/nach gleich); Administration → System zeigt keinen Demo-Knopf; Log nach einem Demo-Start (Modus `demo`) enthält keinen Passwortwert.

**BET-012** · P0 · Status: Ist · Entwicklungs-Passwörter und Ersatzschlüssel nur in der Entwicklung
Bekannte Entwicklungs-Passwörter, Entwicklungsschlüssel (`dev`, abgeleitet aus `SM_SECRET_KEY`) und Ersatz-Prüfschlüssel/unsichere Verbindungen des Update-Agenten gibt es nur im Modus `development`; in `production` sind sie gesperrt (Start-Abbruch bzw. Agent hält an). Ohne `SM_ENCRYPTION_KEYS` verwendet die Entwicklung den abgeleiteten Schlüssel `dev` mit Warnung im Log; mit gesetzter Variable bleibt `dev` nur als Entschlüsselungs-Rückfall.
Abnahme: In `production` führen `UPDATER_PUBKEY` (Ersatz-Schlüssel) und `UPDATER_ALLOW_INSECURE=1` dazu, dass der Agent nicht arbeitet; in `development` ohne `SM_ENCRYPTION_KEYS` erscheint die Warnung „abgeleiteter Entwicklungsschlüssel“ auf `/betrieb`, in `production` ist dieser Zustand gar nicht erreichbar.

**BET-013** · P0 · Status: offen · Konten mit Demo-Passwort in Produktion sperren
Backlog-Anforderung (offen): In Produktion werden Konten, die das Demo-Passwort tragen, beim Start gesperrt und im Systembereich gemeldet, als Netz unter BET-011. Hintergrund: Standard-Demo-Konten mit öffentlich bekanntem Passwort waren aus dem Internet erreichbar (Warnung 12.10., Sperre 12.10. 15:43).
Abnahme: Datenbank mit einem Konto, dessen Passwort dem Demo-Passwort entspricht, wird in `production` gestartet → das Konto ist gesperrt, `/betrieb` listet es, eine Anmeldung damit → 403 bzw. Fehlermeldung „Konto gesperrt“.

---

## 3. Konfigurationsvariablen

**BET-014** · P0 · Status: Ist · Konfiguration nur über Umgebungsvariablen
Alle Einstellungen der Schul-Instanz kommen aus Umgebungsvariablen mit Präfix `SM_` (Compose-Variablen ohne Präfix siehe unten). Geheimnisse liegen nur in der Konfiguration (Datei mit Rechten 600), nie in der Datenbank, nie im Log, nie im Image; SMTP-Zugang wird bewusst nur in der Konfiguration eingetragen, nicht in der Oberfläche. Jede neue Variable wird an vier Stellen geführt: Konfiguration der Anwendung, Beispiel-Umgebungsdatei (nur Platzhalter), Container-Konfiguration (sonst wirkt sie im Container nicht) und Betriebsdokumentation. Die Container-Konfiguration reicht alle dokumentierten `SM_*`-Variablen aus der `.env` an die App durch. Standardwerte stehen in den Tabellen unten; „—“ = leer/nicht gesetzt.
Abnahme: Ein automatischer Test vergleicht die Variablen der Anwendung mit Beispiel-Umgebungsdatei, Container-Konfigurationsausgabe und Betriebsdokumentation und schlägt bei einer Abweichung an; in einer Container-Konfigurationsausgabe sind z. B. `SM_REQUIRE_2FA_ROLES`, `SM_SMS_PROVIDER` und `SM_SSO_*` sichtbar; kein Geheimniswert erscheint in `/api/v1/admin/system`.

**BET-015** · P0 · Status: Ist · Tabellen der Konfigurationsvariablen (Mindestumfang)
Die folgenden Tabellen sind der verbindliche Umfang (Name | Standard | Bedeutung). Zeiten in Sekunden, wenn nicht anders angegeben.

*A. Betrieb, Start, Prozess*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_MODE` | Neubau: `production` (Ist: abgeleitet) | `production`, `demo`, `development` (BET-006, BET-007) |
| `SM_ENV` | `development` (nur Altinstanzen) | Alt-Name des Modus; wirkt nur ohne `SM_MODE` |
| `SM_APP_VERSION` | `0.1.0` (Build-Argument) | Versionsanzeige; im Neubau aus dem Release (BET-160) |
| `SM_APP_NAME` | Produktname aus der Branding-Konstante | Name in Oberfläche, Briefen, Mails (Weißlabel technisch möglich; Lizenzfrage E9 offen) |
| `SM_BASE_URL` | lokale Adresse Port 8000 (ohne Schluss-`/`) | Öffentliche Adresse für Links (Codes, Briefe, Abmelde-Mails, OAuth-Rückkehr); Produktion `https://` |
| `SM_PORT` | `8000` | Lauschport der App im Container |
| `SM_DATA_DIR` | `./data` (Container: Volume `/app/data`) | Datenverzeichnis: Geheimschlüssel-Datei (nur Entwicklung), Sicherungen, Erst-Admin-Datei, Lizenz-Dateien, Agent-Austausch |
| `SM_FILES_DIR` | `<SM_DATA_DIR>/files` | Dateiablage (eigener Datenträger möglich, dann im Backup mitsichern; bei Mehrknoten gemeinsames Laufwerk) |
| `SM_FRONTEND_DIST` | Auslieferungsordner der Oberfläche | Ordner der gebauten Oberfläche (bei Betrieb ohne Container anpassen) |
| `SM_WORKERS` | `1` (fest) | Anzahl Prozesse; größere Werte werden beim Start gewarnt (Kap. 17, BET-195) |
| `SM_THREADPOOL` | `40` (min. 8) | Threads für synchrone Endpunkte |
| `SM_DB_POOL_SIZE` | `20` (min. 5) | Datenbank-Pool; soll größer sein als die Threads |
| `SM_LOG_LEVEL` | `INFO` | Protokollstufe |
| `SM_LOG_FORMAT` | `json` in Produktion, sonst `text` | Log-Format |
| `SM_ACCESS_LOG` | `1` | Zugriffsprotokoll an |
| `SM_SSE_PING_SECONDS` | `20` | Keep-alive des Live-Stroms |
| `SM_MAINTENANCE_INTERVAL` | `3600` (min. 5; Neubau: 0 = aus) | Abstand der Wartungsläufe (Kap. 10) |
| `SM_ENABLE_DOCS` | `off` in Produktion, sonst `admin` | API-Dokumentation: `off`/`0`, `admin` (nur angemeldete Administration oder Admin-API-Token), `public`/`1` (nur im Schulnetz) |
| `SM_METRICS_TOKEN` | — | Bearer-Token für `/metrics`; ohne Token ist `/metrics` gesperrt (401) |
| `SM_TZ`/`TZ` | `Europe/Berlin` | Zeitzone der Anzeige; Datenbank und Protokolle speichern UTC |

*B. Schlüssel und Geheimnisse*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_SECRET_KEY` | Entwicklung: automatisch erzeugt; Produktion: Pflicht | Geheimnis (≥ 32 Zeichen) für HMAC von Sitzungen, API-Token, Codes, SSO-Status; Wechsel macht alle Sitzungen, API-Token und offenen Codes ungültig |
| `SM_ENCRYPTION_KEYS` | Produktion: Pflicht | Schlüsselring `Kennung:Base64(32 Byte)`, Trenner Komma/Semikolon/Leerzeichen/Zeilenumbruch; der erste Eintrag ist aktiv (BET-054) |
| `SM_SCRYPT_N` | `32768` | Kostenfaktor des Passwort-Hashs; Zweierpotenz; Produktion mindestens 16384 |

*C. Datenbank, Migration*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_DATABASE_URL` | SQLite-Datei im Datenverzeichnis | Datenbank; PostgreSQL 16 ab etwa 500 Konten (BET-036) |
| `SM_AUTO_MIGRATE` | `1` | Datenbank beim Start migrieren |
| `SM_MIGRATE_ON_START` | `1` (Container) | Migrationsschritt im Start-Skript; bei Betriebs-Benutzer `0` |
| `SM_MIGRATE_DATABASE_URL` | — (geplant) | Eigentümer-Verbindung nur für Migrationen (BET-038, offen) |

*D. Adressen, Proxy, Cookies, Begrenzung*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_TRUST_PROXY` | `0` im Programm; `1` in Compose- und systemd-Vorlage | Weiterleitungs-Kopfzeilen (Client-IP, Schema, Host) nur von vertrauten Proxys auswerten |
| `SM_TRUSTED_PROXIES` | leer = nur 127.0.0.1 und ::1 (Compose: festes Netz `web`) | Vertraute Proxy-Adressen/Netze; Alt-Name `SM_FORWARDED_ALLOW_IPS`; `*` nur wenn die App garantiert nicht direkt erreichbar ist, mit Startwarnung |
| `SM_PROXY_COUNT` | `1` (min. 1) | Anzahl hintereinander geschalteter Proxys |
| `SM_WEB_SUBNET` (Compose) | `172.29.40.0/24` | Festes Proxy-Netz; bei Konflikt mit dem Heimnetz ändern |
| `SM_COOKIE_SECURE` | `1` in Produktion, sonst `0` | Secure-Attribut; zusätzlich automatisch bei HTTPS-Anfragen |
| `SM_RATE_LIMIT` | `1` | Allgemeine Anfrage-Begrenzung an |
| `SM_RATE_IP_PER_MIN` | `6000` | Anfragen je Minute und IP (zugleich Burst) |
| `SM_RATE_ACCOUNT_PER_MIN` | `1200` | Anfragen je Minute und Konto |
| `SM_OUTBOUND_ALLOW` | — | Ausnahmen vom Schutz gegen Zugriffe auf interne Ziele (Hosts, IPs, Netze, kommagetrennt) |

*E. Anmeldung, Sitzung (Details in ANM)*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_SESSION_IDLE_MINUTES` | `10080` (7 Tage) | Leerlauf-Abmeldung Schüler/innen und Eltern; Obergrenze für Personal (Personal-Standard 720 Minuten per Schuleinstellung) |
| `SM_SESSION_MAX_DAYS` | `30` | Absolute Sitzungsdauer, zugleich Cookie-Laufzeit |
| `SM_LOGIN_MAX_FAILURES` | `5` | Fehlversuche Konto+IP bis Wartezeit |
| `SM_LOGIN_MAX_FAILURES_IP` | `30` | Grundschwelle je IP |
| `SM_LOGIN_LOCK_MINUTES` | `15` | Zählfenster der Fehlversuche und Deckel der Wartezeit |
| `SM_REQUIRE_2FA_ROLES` | leer (Einrichtungsskript setzt `admin,schulleitung,sekretariat`) | Rollen mit Zwei-Faktor-Pflicht |
| `SM_AUTH_CODE_MINUTES` | `15` (1 bis 1440) | Gültigkeit von Bestätigungscodes, Links, Reset-Codes |
| `SM_LETTER_BATCH_MINUTES` | `60` (1 bis 1440) | Lebensdauer eines Zugangsbrief-Stapels |
| `SM_HIBP_CHECK` | `0` | Leak-Prüfung neuer Passwörter (ausgehende Abfrage mit Hash-Präfix) |
| `SM_ADMIN_USER` | `admin` | Name des Erst-Admins |
| `SM_ADMIN_PASSWORD` | leer | Optionales Erst-Admin-Passwort (BET-044); nach dem Erststart leeren |
| `SM_OIDC_ISSUER`, `SM_OIDC_CLIENT_ID`, `SM_OIDC_CLIENT_SECRET` | — | Allgemeines Schulkonto (OpenID Connect); aktiv nur mit Issuer und Client-ID |
| `SM_OIDC_SCOPES` | `openid profile email` | Scopes |
| `SM_OIDC_USERNAME_CLAIM` | `preferred_username` | Claim für den Benutzernamen |
| `SM_OIDC_AUTO_CREATE` | `0` | Konto beim ersten Login automatisch anlegen |
| `SM_OIDC_DEFAULT_ROLE` | `lehrer` | Rolle für automatisch angelegte Konten |
| `SM_OIDC_LABEL` | `Single Sign-on` | Beschriftung des Knopfs |
| `SM_SSO_MICROSOFT_CLIENT_ID`/`_CLIENT_SECRET`/`_TENANT` | — | Anmeldedienst Microsoft (Tenant-Kommentar `organizations`) |
| `SM_SSO_GOOGLE_CLIENT_ID`/`_CLIENT_SECRET`/`_HD` | — | Anmeldedienst Google (`_HD` = nur Konten dieser Domain) |
| `SM_SSO_APPLE_CLIENT_ID`/`_TEAM_ID`/`_KEY_ID`/`_PRIVATE_KEY` | — | Anmeldedienst Apple (Services-ID, Team, Schlüssel-ID, privater Schlüssel als Inhalt oder Pfad) |
| `SM_SSO_DEV_MOCK` | `0` | Test-Anmeldedienst; nur Entwicklung, sonst Startabbruch |

*F. Konto-Post: E-Mail, SMS, Postfach-Abruf*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_SMTP_HOST` / `SM_SMTP_USER` / `SM_SMTP_PASSWORD` / `SM_SMTP_FROM` | — | SMTP-Zugang; E-Mail nur mit Host und Absender |
| `SM_SMTP_PORT` | `587` | SMTP-Port |
| `SM_SMTP_TLS` | `starttls` | `starttls`, `ssl`, `none` |
| `SM_NOTIFY_DISPATCHER` | `1` | Zustellung der Outbox; `0` = E-Mail gilt als nicht verfügbar (alles bleibt in der Outbox) |
| `SM_WEBHOOK_SECRET` | — | Webhook-Geheimnis (Signatur ausgehender Webhooks) |
| `SM_SMS_PROVIDER` | leer (nur E-Mail) | `webhook`, `twilio`, `seven` oder `log` (nur protokollieren) |
| `SM_SMS_URL` / `SM_SMS_TOKEN` / `SM_SMS_ACCOUNT_SID` / `SM_SMS_FROM` | — | Webhook-Ziel; Token (Webhook, twilio, seven); Konto-Kennung (twilio); Absender (Pflicht twilio, optional seven) |
| `SM_SMS_TIMEOUT` | `10` | Zeitlimit SMS-Versand (> 0) |
| `SM_DEV_OUTBOX` | `1`, wenn nicht Produktion und Basis-Adresse lokal; sonst `0` | Test-Postausgang (nur Entwicklung; Produktion verboten) |
| `SM_MAIL_SYNC` | `1` | Abruf verbundener Postfächer an |
| `SM_MAIL_SYNC_MINUTES` | `5` | Abrufintervall (nur lesend) |
| `SM_OAUTH_GOOGLE_CLIENT_ID`/`_CLIENT_SECRET` | — | Postfach-Verbindung Google (Bereich Mail-Vollzugriff; ohne Google-Prüfung nur für eingetragene Testnutzer) |
| `SM_OAUTH_MICROSOFT_CLIENT_ID`/`_CLIENT_SECRET` | — | Postfach-Verbindung Microsoft (Weiterleitungsadresse `<SM_BASE_URL>/api/v1/mail/oauth/callback`) |
| `SM_OAUTH_MICROSOFT_TENANT` | `common` | Mandant |

*G. Dateien, Virenscan, Kontingente, Aufbewahrung*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_UPLOAD_MAX_MB` | `25` (> 0, höchstens 10240) | Maximale Dateigröße; über etwa 49 MB auch die Größengrenze des Proxys anheben |
| `SM_QUOTA_MB_STAFF` | `2000` (0 = unbegrenzt) | Dateikontingent Personal |
| `SM_QUOTA_MB_STUDENT` | `200` | Dateikontingent Schüler/innen |
| `SM_CHAT_QUOTA_MB_STAFF` | `500` (0 = unbegrenzt) | Chat-Bilder je Konto, Personal |
| `SM_CHAT_QUOTA_MB_STUDENT` | `100` (auch Eltern) | Chat-Bilder je Konto, Schüler/innen und Eltern |
| `SM_CHAT_QUOTA_MB_CHAT` | `1000` | Chat-Bilder je Chat, alle Mitglieder zusammen |
| `SM_CHAT_UPLOADS_PER_10MIN` | `30` | Upload-Rate Chat-Anhänge |
| `SM_CLAMAV_HOST` | leer (Virenscan aus) | Dienstname/Host des Virenscanners |
| `SM_CLAMAV_PORT` | `3310` | Port (1 bis 65535) |
| `SM_CLAMAV_REQUIRED` | `0` | `1` = Uploads mit 503 ablehnen, solange der Scanner nicht erreichbar ist |
| `SM_CLAMAV_TIMEOUT` | `30` | Zeitlimit je Scan (> 0) |
| `SM_STUDENT_DOCS_RETENTION_DAYS` | `400` (0 = nie) | Atteste/Dokumente samt Datei löschen |
| `SM_AUDIT_RETENTION_DAYS` | `365` | Startwert der Audit-Frist (0 = nie löschen) |

*H. Sicherung, Planung, Ferien*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_BACKUP_DIR` | `<SM_DATA_DIR>/backups` | Ablage der App-Sicherungen |
| `SM_BACKUP_KEEP` | `30` (0 = keine Rotation) | Anzahl aufbewahrter App-Sicherungen |
| `SM_AUTO_BACKUP_HOURS` | `0` (aus) | Automatische App-Sicherung im Wartungslauf |
| `SM_GENERATE_TIME_LIMIT` | `30` (sinnvoll bis 300) | Rechenzeit des Stundenplan-Generators |
| `SM_AUTOPLAN` | `1` | Auto-Planer an (`0` = serverweit aus) |
| `SM_AUTOPLAN_DELAY` | `3` | Ruhezeit nach der letzten Änderung bis zur Prüfung |
| `SM_AUTOPLAN_TIME_LIMIT` | `15` | Rechenzeit des Auto-Planers |
| `SM_KEEP_VERSIONS` | `300` (min. 2) | Aufbewahrte Planversionen |
| `SM_HOLIDAY_IMPORT` | `1` | Ferien-/Feiertagsdienst; `0` schaltet ihn ganz ab (je Schule nur aktiv, wenn die Automatik eingeschaltet ist) |

*I. Lizenz (Schul-Instanz)*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_LICENSE_ENFORCE` | `0`; in Produktion immer wirksam | Lizenz durchsetzen (Entwicklung/Demo) |
| `SM_LICENSE_CHECK_HOURS` | `24` (min. 1) | Abstand der ausführlichen Prüfung |
| `SM_LICENSE_PING_MINUTES` | `15` (0 = aus) | Kurze Statusabfrage |
| `SM_LICENSE_GRACE_DAYS` | `14` (min. 0) | Kulanz, falls die Antwort keine nennt |
| `SM_LICENSE_PUBKEY`, `SM_LICENSE_SERVER` | — | Nur Test (nicht in Produktion) |

*J. Mehrknoten, Demo*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_NODE_ID` | `main` (1 bis 40 Zeichen) | Knotenname (Leader-Sperre, Drain, Anzeige) |
| `SM_HA` | `0` | `1` = Mehrknoten-Betrieb: Hintergrundjobs nur auf dem Leader, optimistische Sperre beim Planungsdokument |
| `SM_LOAD_DEMO` | `0` | Demo-Schule beim allerersten Start erzeugen (in Produktion verboten) |
| `SM_DEMO_BACKGROUND` | `1` | Demo im Hintergrund erzeugen (`0` = blockierend) |
| `SM_DEMO_CLASSES_PER_GRADE` | `14` (1 bis 23) | Umfang der Demo |
| `SM_DEMO_PUBLIC` | `1` im Modus `demo`, sonst `0` | Öffentliche Vorführ-Instanz mit Demo-Zugängen (in Produktion verboten) |
| `SM_DEMO_ALL_ACCOUNTS` | `1` | Demo: je ein Konto je Lehrkraft, Schüler/in und Elternhaus |
| `SM_DEMO_PASSWORD` | Demo-Standard (nicht übernommen) | Passwort der Demo-Konten; auch vom Lasttest gelesen; nie ausgegeben |
| `SM_HELP_DIR`, `SM_OPS_DOCS_DIR` | Ordner der Hilfe- bzw. Betreiber-Dokumente im Programm | Ort der Handbuch-Texte |

*K. Compose-Variablen (ohne Präfix `SM_`)*

| Name | Standard | Bedeutung |
|---|---|---|
| `SM_DOMAIN` | Pflicht (Test: `localhost`) | Adresse für Proxy und Zertifikat (`localhost` → selbst signiertes Zertifikat) |
| `ACME_EMAIL` | Pflicht | Kontakt für Let's-Encrypt-Zertifikate |
| `ACME_CA` | produktiv | Zertifikatsstelle (Testumgebung möglich) |
| `SM_IMAGE`, `SM_BACKUP_IMAGE` | — | Versions-Tags der fertigen Images (App, Backup) |
| `POSTGRES_USER`, `POSTGRES_PASSWORD` | Passwort Pflicht | Datenbank-Benutzer/-Passwort (nur bei Erst-Initialisierung wirksam) |
| `POSTGRES_VERSION` | `16` | Hauptversion; nie durch bloßes Ändern des Tags wechseln (BET-036) |
| `PG_SHARED_BUFFERS`, `PG_EFFECTIVE_CACHE_SIZE` | ca. 25 % bzw. 75 % des RAM | Datenbank-Speichereinstellungen |
| `APP_CPUS`, `APP_MEMORY` | `APP_MEMORY` 3 GB | Ressourcenlimits des App-Containers |
| `LOG_MAX_SIZE`, `LOG_MAX_FILES` | 10 MB, 5 | Container-Log-Rotation je Container |
| `BACKUP_TIMES` | `02:30` (mehrere: `02:30 12:45`) | Sicherungszeiten |
| `BACKUP_MAX_AGE_HOURS` | `26` | Backup-Container wird „unhealthy“, wenn das letzte erfolgreiche Backup älter ist |
| `BACKUP_PING_URL`, `BACKUP_PING_URL_FAIL` | — | Push-Monitor bei Erfolg/Fehler |
| `BACKUP_HOST_DIR` | `./backups` | Ablage der Sicherungen auf dem Host |
| `BACKUP_GPG_PASSPHRASE` | — (dringend empfohlen) | GPG-Passphrase; ohne sie ist kein Restore verschlüsselter Dateien möglich |
| `BACKUP_RCLONE_REMOTE`, `BACKUP_RCLONE_MODE`, `RCLONE_CONFIG_OFFSITE_*` | Modus `copy` | Offsite-Kopie (BET-049) |
| `GRAFANA_ADMIN_PASSWORD` (Pflicht für Monitoring), `ALERT_EMAIL`, `GRAFANA_SMTP_ENABLED`, `GRAFANA_SMTP_HOST` | — | Monitoring-Profil |

*L. Update-Agent (Kap. 15) und Lizenzserver (Kap. 13)*: siehe BET-155 und BET-104 (eigene Tabellen).

Abnahme: Für jede Variable der Tabellen existiert ein Test oder eine Konfigurationsprüfung, der den Standardwert bestätigt (Variable nicht gesetzt → dokumentierter Wert wirksam); ungültige Werte der Bereichsvariablen (z. B. `SM_UPLOAD_MAX_MB=0`, `SM_AUTH_CODE_MINUTES=2000`) brechen den Start ab; `SM_WORKERS` größer 1 erzeugt beim Start eine Warnung.

**BET-016** · P2 · Status: Ist · Betrieb hinter Nicht-Standard-Port
Die Instanz funktioniert hinter einem HTTPS-Port ungleich 443 (Betreiber-Umgebung: Provider erlaubt eingehend nur einen schmalen Portbereich): `SM_BASE_URL` darf einen Port enthalten; Links in Mails, Zugangsbriefen (QR-Code), Abmelde-Mails und OAuth-Rückkehr tragen den Port; Cookies gelten je Host/Port ohne Vermischung mehrerer Instanzen desselben Hosts mit verschiedenen Ports. Die Erreichbarkeit einer neuen Adresse wird von außen getestet, bevor sie gemeldet wird.
Abnahme: Instanz mit `SM_BASE_URL=https://schule.example.org:<port>` → ein Zugangsbrief-QR-Code und ein Passwort-vergessen-Link führen auf diese Adresse mit Port; zwei Instanzen unter verschiedenen Ports desselben Hosts melden sich unabhängig an und ab.

---

## 4. Installation, Container, Reverse-Proxy

**BET-017** · P1 · Status: Ist · Systemvoraussetzungen
Betriebssystem Linux 64 Bit (Debian 12/13, Ubuntu 22.04/24.04 LTS oder vergleichbar; amd64 oder arm64). Container-Variante: Docker Engine ab 24, Compose-Plugin ab 2.24. Variante ohne Container: Python 3.11 oder 3.12, Node.js 22 (nur zum Bauen der Oberfläche), PostgreSQL 16 (Datenbank-Client passend zur Serverversion), nginx, certbot; optional rclone und gpg. Netz: feste öffentliche Adresse (IPv4, IPv6 gern), DNS-Eintrag (A, bei IPv6 AAAA), eingehend 80 und 443 (TCP) sowie 443 (UDP); ausgehend nötig für Let's Encrypt, SMTP, Offsite-Speicher, Lizenzserver des Anbieters, Ferien-/Feiertags-Dienste, IMAP/SMTP der Mail-Konten (Ports 993, 465/587), OAuth-Anbieter (Microsoft, Google) und optional die Passwort-Leak-Prüfung. Hosting möglichst in Deutschland/EU mit Auftragsverarbeitungsvertrag. Ressourcen je Schulgröße: Kap. 17 (BET-196). Untere Grenze laut Betriebshandbuch: 2 vCPU, 4 GB RAM, 20 GB SSD (empfohlen 4 vCPU, 4 bis 8 GB, 40 GB); Richtwerte RAM: App 0,3 bis 1 GB, PostgreSQL 0,5 bis 1 GB, Proxy und Backup zusammen unter 0,3 GB, Monitoring-Profil +1 GB, Virenscanner +1,5 bis 3 GB.
Abnahme: Die Installationsanleitung enthält genau diese Voraussetzungen; eine Installation auf Debian 12 und auf Ubuntu 24.04 (je amd64) mit Docker 24 / Compose 2.24 endet mit allen Diensten „healthy“; die Demo-Schule (ca. 2.600 Schüler/innen) läuft auf 2 vCPU / 4 GB mit `/healthz` „ok“.

**BET-018** · P1 · Status: Ist · Container-Stack
Dienste: `app` (genau ein Prozess; von außen nicht erreichbar), `db` (PostgreSQL 16; nur im internen Netz, kein Internetzugang, kein veröffentlichter Port), `proxy` (Caddy 2.x, Kap. BET-020), `backup` (eigener Container, BET-042). Profile: `monitoring` (Prometheus und Grafana, nur localhost), `uptime` (Uptime-Kuma, nur localhost), `antivirus` (ClamAV-Daemon), `updater` (Update-Agent, Kap. 15). Netze: `web` (Proxy, festes Subnetz), `backend` (intern, kein Internet), `monitoring`, `egress` (ausgehend, z. B. Signaturupdates des Virenscanners). Volumes: Datenbank, App-Daten (inklusive Dateiablage), Proxy-Zertifikate; Sicherungen unter `./backups` bzw. `BACKUP_HOST_DIR`. Zusätzlich eine schlanke SQLite-Variante der Compose-Konfiguration (Schulung, Demo, Kleinbetrieb) und eine Entwicklungs-Variante. Alle Dienste mit Gesundheitsprüfung und Neustart-Richtlinie `unless-stopped`; Speicherlimit der App `APP_MEMORY` (Standard 3 GB). Nach außen nur Proxy-Ports 80, 443/tcp, 443/udp. Der Image-Bau ist mehrstufig (Oberfläche bauen, dann Laufzeit-Image).
Abnahme: Alle Dienste zeigen „healthy“; die Container-Konfigurationsausgabe enthält keine veröffentlichten Ports außer 80/443; ein Portscan von außen findet weder Datenbank- noch App-Port (8000); nach `kill` des App-Containers startet er neu und wird wieder „healthy“; SQLite-Variante startet ohne `db`-Dienst.

**BET-019** · P0 · Status: Ist · Container-Härtung
Die App läuft als Nicht-Root-Benutzer, mit schreibgeschütztem Dateisystem (beschreibbar nur ein tmpfs für `/tmp` und das Daten-Volume) und ohne zusätzliche Linux-Capabilities. Datenbank nur im internen Netz; Metriken nur lokal; Zugriff auf Container-Protokolle nur für die Schul-IT. `.env` liegt nie im Repository oder Image (`.env.example` nur mit Platzhaltern); Backups sind aus Repository und Image ausgeschlossen; Geheimnisse nur über Umgebungsvariablen oder Secret-Store.
Abnahme: Im laufenden App-Container ist der Benutzer nicht root, ein Schreibversuch außerhalb von `/tmp` und Daten-Volume scheitert, die Container-Inspektion zeigt keine zusätzlichen Capabilities; eine Suche im gebauten Image findet keine `.env`, keine Datenbank, keinen Schlüssel.

**BET-020** · P0 · Status: Ist · Reverse-Proxy: fachliche Anforderungen
Vor der App steht immer ein Reverse-Proxy (Caddy im Container, nginx ohne Container; die App wird nie direkt veröffentlicht, kein Router-Weiterleiten auf die App). Anforderungen: (1) HTTPS mit automatischen Let's-Encrypt-Zertifikaten (`ACME_EMAIL`), TLS 1.2 und 1.3, Port 80 leitet auf HTTPS weiter, 443 auch per UDP; (2) HSTS und Sicherheits-Header (`X-Content-Type-Options: nosniff`, `X-Frame-Options`, Referrer-Policy, Permissions-Policy, Content-Security-Policy); die App setzt ihre Header nur, wenn der Proxy sie nicht schon setzt (keine doppelten Header); (3) Komprimierung zstd/gzip; (4) Server-Sent Events ungepuffert, Proxy-Timeouts mindestens 60 Sekunden; (5) Pfad der Metriken von außen gesperrt; (6) Wartungsseite: bei einem Neustart hält der Proxy Anfragen bis zu 15 Sekunden zurück, danach zeigt er eine Wartungsseite mit automatischem Neuladen; (7) Zugriffsprotokoll (JSON): Cookies und Autorisierungsdaten geschwärzt, iCal-Tokens maskiert, Client-Adressen gekürzt (IPv4 auf /24, IPv6 auf /48); (8) Größenbegrenzung für Uploads nicht kleiner als `SM_UPLOAD_MAX_MB` (über etwa 49 MB den Proxy-Wert anheben); (9) Begrenzung der Anmeldeversuche am Proxy zusätzlich zur App möglich (nginx-Vorlage: Anfragebegrenzung mit 429); (10) der Proxy überschreibt `X-Forwarded-For` mit der echten Client-Adresse; (11) Testinstallation mit `SM_DOMAIN=localhost` erzeugt ein selbst signiertes Zertifikat.
Abnahme: Prüfung per Kopfzeilen-Abruf zeigt HSTS und alle genannten Header genau einmal; Port 80 → 301/308 auf HTTPS; `/metrics` von außen → 403 oder 404; Live-Änderung am Vertretungsplan erscheint am Monitor innerhalb von etwa 1 Sekunde (kein Puffern); App-Neustart während einer Anfrage → Antwort nach höchstens 15 Sekunden oder Wartungsseite mit Auto-Neuladen; Proxy-Log enthält keine Cookie-/Authorization-Werte und IPs nur gekürzt.

**BET-021** · P0 · Status: Ist · Proxy-Vertrauen und Client-Adresse
Nur der Proxy darf Client-Adresse und Schema melden; sonst könnte jeder Besucher seine Adresse frei wählen und Anmeldesperren je Adresse, Adresslisten der API-Zugänge und die Adresse im Audit aushebeln. `SM_TRUST_PROXY=1` wertet die Weiterleitungs-Kopfzeilen aus, aber nur von Adressen in `SM_TRUSTED_PROXIES`; die App-Server-Schicht verarbeitet die Standard-Weiterleitungs-Kopfzeilen nicht selbst. Compose: festes Netz `web` (`SM_WEB_SUBNET`) wird automatisch in `SM_TRUSTED_PROXIES` übernommen. Ohne Container: `SM_TRUSTED_PROXIES=127.0.0.1,::1`. Die Client-Adresse wird für IPv4 und IPv6 korrekt weitergereicht. Beim Start warnt die Prüfung, wenn `SM_TRUST_PROXY=1` ohne `SM_TRUSTED_PROXIES` oder mit `*` läuft.
Abnahme: Anfrage mit gefälschtem `X-Forwarded-For` direkt an die App → Audit und Anmelde-Protokoll zeigen die echte Verbindungsadresse, nie die gefälschte; Anfrage über den Proxy → die echte Client-Adresse (IPv4 und IPv6); 6 Fehlanmeldungen aus einer Adresse sperren nur diese Adresse, nicht alle Nutzer hinter dem Proxy.

**BET-022** · P1 · Status: Ist · Installationsablauf (fachlich)
Reihenfolge: (1) Server vorbereiten: Updates, Zeitsynchronisation muss „synchronisiert“ melden (sonst werden Zwei-Faktor-Codes abgelehnt), Firewall (SSH nur aus Admin-Netzen, 80/tcp, 443/tcp, 443/udp), automatische Sicherheitsupdates; (2) Docker und Compose in Mindestversion; (3) DNS-Eintrag; (4) Dateien holen; (5) Konfiguration erzeugen: ein Skript erzeugt `.env` (Rechte 600) mit Zufallswerten für `SM_SECRET_KEY`, `SM_ENCRYPTION_KEYS`, `POSTGRES_PASSWORD`, `BACKUP_GPG_PASSPHRASE`, setzt `SM_REQUIRE_2FA_ROLES` (Administration, Schulleitung, Sekretariat) und `SM_MODE=production`; danach SMTP eintragen; sofort getrennt vom Server sichern: `SM_ENCRYPTION_KEYS`, `BACKUP_GPG_PASSPHRASE`, die ganze `.env` verschlüsselt; (6) `check-config`; (7) Start (Images bauen 3 bis 8 Minuten oder fertige Images über `SM_IMAGE`/`SM_BACKUP_IMAGE`); (8) Status: alle Dienste „healthy“, im Proxy-Log „certificate obtained successfully“, Erreichbarkeitsprüfung gegen die Adresse; (9) Anmeldung als Administrator, sofort Zwei-Faktor einrichten, danach `SM_ADMIN_PASSWORD` in `.env` leeren; (10) Sicherung verifizieren (Liste, Test-Restore einer Datenbank-Sicherung in eine Wegwerf-Datenbank), optional Monitoring starten.
Abnahme: Ein protokollierter Durchlauf auf einem frischen Server (Zeit gemessen, Stolperstellen notiert) endet mit allen Diensten „healthy“, gültigem Zertifikat, Admin-Anmeldung mit erzwungenem Passwortwechsel und Zwei-Faktor, leerem `SM_ADMIN_PASSWORD` und erfolgreichem Test-Restore.

**BET-023** · P1 · Status: Ist · Checkliste vor dem Livegang
Zehn Punkte, alle abzuhaken: (1) `check-config` ohne Meldung; (2) HTTPS gültig und Adresse gleich `SM_BASE_URL`; (3) Erst-Administrator hat eigenes Passwort und Zwei-Faktor; (4) `SM_ADMIN_PASSWORD` in `.env` leer; (5) Schlüssel, Passphrase und `.env` getrennt im Tresor; (6) Offsite-Sicherung läuft, Test-Restore erfolgreich und notiert; (7) Testmail kommt an, „Passwort vergessen“ geprüft; (8) Lizenzschlüssel eingetragen (Lizenzseite: Status beim Anbieter aktiv, letzte Prüfung gesetzt, ein Server pro Schlüssel); (9) Datenschutz: Verzeichnis der Verarbeitungstätigkeiten ausgefüllt, AV-Verträge liegen vor, Datenschutzhinweise verteilt, Datenschutz-Folgenabschätzung geprüft; Zugangsbriefe verteilt mit Hinweis, das Passwort sofort zu ändern; (10) Firewall: nur SSH eingeschränkt, 80 und 443 offen, kein Datenbankport veröffentlicht. Die Checkliste ist die Abnahmeliste einer Pilotschule (Entscheidung E8).
Abnahme: Die Checkliste steht im Betreiber-Paket (BET-214); jeder Punkt ist ohne Interpretation prüfbar; eine Pilot-Installation hakt alle zehn Punkte nachweislich ab.

**BET-024** · P2 · Status: Ist · Betrieb ohne Container
Alternative mit systemd, nginx, PostgreSQL 16 und certbot: Systembenutzer ohne Login-Shell; Datenverzeichnis (Rechte 0750) und Verzeichnis für Datenbank-Sicherungen; Python-Umgebung aus der gesperrten Abhängigkeitsliste mit Hash-Prüfung (ohne Abhängigkeiten nachzuladen); Oberfläche bauen; PostgreSQL-Benutzer mit Passwortabfrage und Datenbank in UTF-8 mit diesem Benutzer als Eigentümer; Umgebungsdatei unter `/etc` (Rechte 0640, Gruppe des Dienstbenutzers; Kommentare nur am Zeilenanfang, nie `WERT # Kommentar`); Dienst-Unit; nginx-Vorlage (SSE ohne Puffer, lange Lesezeitüberschreitung, Anmelde-Begrenzung, Sicherheits-Header, Zugriffsprotokoll ohne iCal-Tokens, Auslieferung der Oberflächen-Dateien von der Platte); Backup als systemd-Timer täglich 02:30; `SM_TRUST_PROXY=1` mit `SM_TRUSTED_PROXIES=127.0.0.1,::1`; Update: neue Version holen, Python-Umgebung aus der Sperrliste neu, Oberfläche neu bauen, Dienst neu starten (Migrationen im Start-Schritt).
Abnahme: Auf einem frischen Debian läuft der Dienst, `/healthz` meldet ok, der Backup-Timer ist aktiv, `check-config` verhält sich wie im Container; eine Umgebungsdatei mit Zeilenende-Kommentar wird im Betreiber-Paket als Fehlerquelle genannt.

**BET-025** · P2 · Status: Ist · Zeit und Zeitzone
Zeitzone der Anzeige `Europe/Berlin` (Variable `TZ`); die Datenbank speichert UTC; Protokolle, Audit und Anmeldeversuche tragen UTC-Zeitstempel. Die Serverzeit muss synchronisiert sein (sonst werden Zwei-Faktor-Codes abgelehnt).
Abnahme: Ein Datenbankeintrag um 12:00 Uhr Sommerzeit hat Zeitstempel 10:00 UTC und wird in der Oberfläche als 12:00 angezeigt; bei Serverzeit-Abweichung über 60 Sekunden verweist das Betreiber-Paket auf die Zeitsynchronisation als Ursache abgelehnter Zwei-Faktor-Codes.

**BET-026** · P1 · Status: Ist · Aktualisierung durch den Betreiber (ohne Anbieter-Automatik) und Patch-Pflege
Zeitpunkt außerhalb der Unterrichtszeit (nachmittags/abends); Unterbrechung typisch 10 bis 30 Sekunden (Installationsanleitung: unter einer Minute). Ablauf: Sicherung mit Kennzeichen `vor-update` (BET-043) → neue Version (bei fertigen Images die Tags `SM_IMAGE`/`SM_BACKUP_IMAGE` setzen und die Compose-, Proxy- und Monitoring-Dateien der neuen Version holen) → Container neu starten → Migrationen laufen automatisch → Gesundheitsprüfung mit Wartezeit bis 240 Sekunden. Schlägt eine Migration fehl, startet die App nicht; die Ursache steht im App-Protokoll. Rollback: vorheriges Image-Tag eintragen und starten; war die Datenbank bereits migriert, zusätzlich die Sicherung `vor-update` zurückspielen. Nach dem ersten Update durch die Anbieter-Automatik immer das Hilfsskript verwenden (es liest die Update-Umgebung), nicht den direkten Compose-Befehl. Monatlich: Basis-Images neu bauen und neu starten (Sicherheitsupdates von Python, Node, PostgreSQL-Minor, Proxy); Betriebssystem und Docker mit automatischen Sicherheitsupdates, Neustarts planen.
Abnahme: Ein Update auf eine Testversion mit absichtlich fehlschlagender Migration → App startet nicht, Fehler im Log, Rollback auf das alte Image-Tag plus Sicherung `vor-update` stellt den alten Stand wieder her; ein Update mit gültiger Migration → `/healthz` meldet die neue Version innerhalb von 240 Sekunden.

**BET-027** · P1 · Status: Ist · Deploy-Ablauf des Anbieters für die eigenen Instanzen
Für Hauptinstanz, Demo, Test-Instanz „neu“ und Lizenzserver gilt vor jedem Aufspielen: automatische Sicherung aller Datenbanken und des alten Images (Tag `vor-update-<JJJJMMTT-HHMM>`); Migrationen vorher an Kopien der echten Datenbanken geprüft und Probelauf mit diesen Kopien ohne Fehler; Rücksetzweg = Image-Tag zurück plus Datenbank-Kopien (Anleitung am Ende des Deploy-Skripts); nach dem Deploy Demo-Reset, Demo-Zugänge und bestehende Lizenzen bleiben erhalten. Technische Fallen: Image-Bau auf dem Server braucht Internet (Deploy nur bei stabiler Verbindung); Shell-Skripte mit LF-Zeilenenden und erhaltenem Ausführungsrecht (sonst startet der Container nicht); Paket-Sperrdateien müssen für den Build vorliegen. Eine neue Adresse wird erst von außen getestet, dann gemeldet. Deploy-Ziel ist immer der Server, nie der Entwicklungs-PC (Arbeitsregeln: PRI).
Abnahme: Ein Deploy-Trockenlauf erzeugt Datenbank-Sicherungen und das Image-Tag `vor-update-…`, der Probelauf auf Kopien endet fehlerfrei, danach melden alle Instanzen `/healthz` „ok“ aus dem Internet; der Rücksetztest (Tag zurück + Kopie) startet den alten Stand mit den alten Daten.

**BET-028** · P3 · Status: offen · Installation unter Windows Server oder ohne Linux-Kenntnisse
Lücke laut Produktreife: nicht unterstützt. Weg für Schulen ohne IT-Kenntnis ist das gehostete Angebot des Anbieters (Entscheidung E3 offen, BET-206).
Abnahme: Entscheidung dokumentiert (unterstützt/nicht unterstützt); falls unterstützt, gelingt eine Installation auf Windows Server nach der Anleitung bis zur Checkliste BET-023.

---

## 5. Datenbank und Migrationen

**BET-029** · P1 · Status: Ist · Unterstützte Datenbanken
SQLite (Standard: eine Datei im Datenverzeichnis, ein Prozess; für Schulung, Demo, Kleinbetrieb; im Speicher nur in Tests) und PostgreSQL 16 (Standard der Compose-Konfiguration). Typisierte Spalten; Schemaänderungen ausschließlich über versionierte Migrationen. Die Datenbank-Art wird beim Start erkannt; die Statusseite prüft Erreichbarkeit und Schema-Stand. Beide Arten werden automatisch getestet.
Abnahme: Dieselbe Funktionstestsuite läuft grün auf SQLite und auf PostgreSQL 16; `/healthz` liefert 503, wenn die Datenbank nicht erreichbar ist; die Statusseite zeigt „Datenbankstand: aktuell“ oder einen Migrationshinweis.

**BET-030** · P1 · Status: Ist · Wahl SQLite oder PostgreSQL
Entscheidungsregel (E6): PostgreSQL ab etwa 500 Konten, bei Hochverfügbarkeit (Kap. 15.5), sobald die Datenbank über etwa 5 GB wächst, bei Chat-Bildern in der Datenbank oder vielen parallelen Schreibvorgängen; bei Schulen mit bis zu 5.000 Schüler/innen ist PostgreSQL zwingend (Kap. 17, BET-196). SQLite nur für kleine Schulen. Der Start warnt bei SQLite mit etwa 500 oder mehr Konten (BET-009).
Abnahme: Eine SQLite-Instanz mit 500 oder mehr Konten zeigt die Warnung „PostgreSQL empfohlen“; die Betriebsdokumentation nennt die Schwellen.

**BET-031** · P2 · Status: offen · Umstieg SQLite zu PostgreSQL
Der Umstieg ist für wachsende Schulen nötig, wurde aber nicht geprüft (Lasttest/Kompression der Chat-Daten ebenfalls offen). Der JSON-Export (Sicherung) existiert; ein geprüfter Umstiegsweg fehlt.
Abnahme: Die Daten einer SQLite-Instanz (ab 1.000 Konten, mit Dateien, Chats, Atteste) werden in eine leere PostgreSQL-Instanz übernommen; Zeilenzahlen je Tabelle stimmen, Anmeldung klappt, `verify-files` meldet Exit 0, Entschlüsselung ist möglich.

**BET-032** · P2 · Status: Ist · PostgreSQL-Betriebsregeln
(1) Wechsel der Hauptversion (z. B. 16 auf 17) nie durch bloßes Ändern des Tags: Sicherung, Stack stoppen, Datenbank-Volume sichern bzw. umbenennen, `POSTGRES_VERSION` setzen, starten, Sicherung einspielen. (2) `POSTGRES_PASSWORD` gilt nur bei der Erst-Initialisierung; geänderte Passwörter in der Datenbank per `ALTER USER` nachziehen. (3) Dump-Werkzeug und Datenbankserver haben dieselbe Hauptversion (Sidecar baut mit gleicher Version); die App enthält kein Dump-Werkzeug. (4) `PG_SHARED_BUFFERS` etwa 25 % und `PG_EFFECTIVE_CACHE_SIZE` etwa 75 % des RAM.
Abnahme: Ein dokumentierter Probelauf 16 → 17 auf einer Kopie behält alle Konten; ein App-Start nach geändertem `POSTGRES_PASSWORD` ohne `ALTER USER` zeigt „App unhealthy“, mit `ALTER USER` „healthy“.

**BET-033** · P0 · Status: Ist · Migrationen beim Start
Migrationen sind nummeriert, lückenlos und wiederholbar. Sie laufen beim Start automatisch (`SM_AUTO_MIGRATE=1`, im Container zusätzlich als Start-Schritt `SM_MIGRATE_ON_START=1`) und manuell per Befehl `migrate`. Schlägt eine Migration fehl, startet die App nicht; die Ursache steht im App-Protokoll. Die Datenbank hebt sich beim Start selbst auf den aktuellen Stand; ein älteres Backup wird nach dem Restore automatisch auf den aktuellen Stand gebracht. Ein Test vergleicht Modelle und Schema; jede Schemaänderung ist genau eine Revision; Mehrfach-Köpfe werden vor dem Release zusammengeführt. Tests laufen auf SQLite und PostgreSQL 16 sowie mit gespeicherten Altversionen (Aufwärts und Abwärts). Planungsdaten müssen mit Standardwerten auskommen. Beim Mehrknoten-Betrieb migriert nur ein Knoten (Kap. 15.5, BET-164).
Abnahme: Frische Datenbank → alle Migrationen laufen ohne Fehler; zweiter Start ändert nichts; absichtlich fehlerhafte Migration → App startet nicht, Log nennt die Revision; Modell/Schema-Abgleichstest schlägt bei einer Modelländerung ohne Migration an; ein Backup aus der Vorversion lässt sich einspielen und migrieren.

**BET-034** · P0 · Status: Ist · Expand-Regel für Migrationen
Verbindlich für rollend ausgelieferte Releases: Eine Migration darf nur erweitern. Erlaubt: neue Tabelle; neue Spalte mit NULL oder Standardwert; neuer Index; Daten ergänzen. Verboten in einem Schritt: Spalte oder Tabelle löschen oder umbenennen; Typ ändern; Spalte auf NOT NULL setzen; neue NOT-NULL-Spalte ohne Standardwert; vorhandene Werte so umschreiben, dass der alte Code sie nicht mehr versteht. Aufteilung in zwei Releases: Release n fügt die neue Spalte hinzu und schreibt in beide, Release n+1 löscht die alte. Ausnahmen werden bewusst als nicht abwärtskompatibel („breaking“) freigegeben (dann Wartungsfenster, BET-149). Datenmigrationen, die Werte umschreiben, werden immer von Hand geprüft.
Abnahme: Eine Testmigration „Spalte löschen“ wird vom Prüfskript (BET-035) als Verstoß gemeldet; „neue Spalte mit Standardwert“ nicht; beim Betrieb von Version n und n+1 gleichzeitig auf demselben Schema (zwei Knoten) funktionieren beide.

**BET-035** · P0 · Status: Ist · Verträglichkeits-Prüfskript vor jedem Release
Ein Skript prüft vor jeder Freigabe, ob die Migrationen die Expand-Regel einhalten; es erkennt offensichtliche Fälle (Löschen, Umbenennen, Typänderung, NOT NULL), aber keine umschreibenden Datenmigrationen. Das Ergebnis geht als Kennzeichen „abwärtskompatibel“ in das Release-Manifest (BET-137). Bestand (Stand 16.10.2026): von 51 bisherigen Änderungen ist eine nicht verträglich (Passwort-Feld entfernt, Ablaufzeit Pflichtfeld); eine Datenmigration (Hash der Kalender-Tokens) wird vom Skript nicht erkannt.
Abnahme: Das Release-Anlegen ohne gesetztes Kennzeichen wird verweigert; das Skript schlägt bei einer Testmigration „Typ ändern“ an; ein sauberer Lauf ist Voraussetzung für die Freigabe.

**BET-036** · P0 · Status: Ist · Umbau von Tabellen mit kaskadierenden Fremdschlüsseln
Tabellenumbauten (SQLite-Umbau durch Neuanlegen und Kopieren) an Tabellen mit kaskadierenden Fremdschlüsseln (Konten, Kursraum-Ordner) können Daten löschen. Solche Änderungen brauchen einen gesonderten Prüfplan: Zeilenzahlen aller abhängigen Tabellen vor und nach der Migration vergleichen, vorher Probelauf an einer Kopie. Bekannter Fall: eine Migration der Cloud-Version konnte beim Upgrade Materialien in Bestandsordnern löschen (Behebung im Merge unbestätigt).
Abnahme: Ein Migrationstest auf gefüllter Datenbank (Konten mit Kursraum-Ordnern und Materialien) liefert nach der Migration identische Zeilenzahlen in allen abhängigen Tabellen.

**BET-037** · P1 · Status: offen · Getrennte Datenbank-Benutzer für Migration und Betrieb (PostgreSQL)
Heute gibt es eine Verbindung (`SM_DATABASE_URL`) mit Eigentümerrechten; die App braucht daher DDL-Rechte. Ziel: Eigentümer-Rolle nur für Migrationen und Betriebsrolle nur mit SELECT, INSERT, UPDATE, DELETE (ohne CREATE, ALTER, DROP); Schema-Rechte für alle anderen entziehen (PostgreSQL ab 15); Standardrechte für künftige Tabellen und Sequenzen; für anhängende Tabellen (z. B. Audit-Protokoll) nur SELECT und INSERT, wenn die App dort nie UPDATE/DELETE ausführt. Neue Variable `SM_MIGRATE_DATABASE_URL` (Migrationsskript bevorzugt sie, sonst `SM_DATABASE_URL`); die laufende App läuft mit Betriebs-URL und `SM_AUTO_MIGRATE=0`, `SM_MIGRATE_ON_START=0`. Die Laufzeit darf kein DDL ausführen (Startpfade prüfen). Bei bestehenden Installationen gehören die Tabellen dem bisherigen Benutzer (Sicherung, dann Umhängen der Objekte). Das Initialisierungsskript der Datenbank läuft nur bei leerem Datenverzeichnis. Aufwand etwa 1 Tag; bisher nur Dokumentation. SQLite nicht betroffen.
Abnahme: Mit der Betriebsrolle laufen alle Funktionstests grün; `CREATE TABLE` mit der Betriebsrolle wird verweigert; die Migration mit `SM_MIGRATE_DATABASE_URL` gelingt; UPDATE/DELETE auf das Audit-Protokoll mit der Betriebsrolle wird verweigert.

---

## 6. Erststart, Notfall-Befehle, Einrichtung

**BET-038** · P0 · Status: Ist · Erst-Administrator
Der Start legt einen Erst-Administrator nur an, wenn noch keiner existiert; Benutzername `SM_ADMIN_USER` (Standard `admin`). Fälle: (a) `SM_ADMIN_PASSWORD` gesetzt (mindestens 10 Zeichen, kein Beispielwert): dieses Passwort, kein Pflichtwechsel; (b) leer in `production`/`demo`: zufälliges Startpasswort (4 Gruppen zu 4 Zeichen) mit Pflichtwechsel, geschrieben in die Datei `ERST-ADMIN.txt` im Datenverzeichnis (Rechte 600); im Log steht nur ein Hinweis (Zeile `ERST-ADMIN`), nie das Passwort; die Datei wird nach dem ersten Passwortwechsel eines Administrators gelöscht (auch beim Start, wenn kein Administrator mehr einen Pflichtwechsel hat); (c) `development`: Entwicklungs-Passwort mit Pflichtwechsel. Kann die Datei nicht geschrieben werden: Fehlermeldung ohne Passwort, Zurücksetzen per Befehl `reset-password`. Im Echtbetrieb gibt es beim Erststart keine Demo-Daten und keine Entwicklungspasswörter. Entscheidung bei Widerspruch: Das Betriebshandbuch verlangt `SM_ADMIN_PASSWORD` als Pflicht, die neuere Installationsanleitung und die Produktreife beschreiben die Einmalpasswort-Datei; gilt die Datei, `SM_ADMIN_PASSWORD` ist optional.
Abnahme: Frischer Start im Modus `production` ohne `SM_ADMIN_PASSWORD` → Datei `ERST-ADMIN.txt` mit Rechten 600 vorhanden, Log enthält die Zeile `ERST-ADMIN` ohne Passwort; Anmeldung mit dem Passwort aus der Datei → Pflicht zum Passwortwechsel; nach dem Wechsel ist die Datei gelöscht; zweiter Start legt keinen weiteren Administrator an; keine Demo-Daten vorhanden.

**BET-039** · P1 · Status: offen · Erst-Admin-Übergabe verbessern
(1) Entscheidung E7: einmaliger Einrichtungslink mit Ablauf statt Passwort-Datei (Aufwand S); bis dahin sind Datei bzw. Log-Hinweis akzeptabel, solange nur die Schul-IT Container-Logs und das Datenverzeichnis sieht. (2) Ein gesetztes `SM_ADMIN_PASSWORD` unterliegt den Passwortregeln: Verstoß (kürzer als 10 Zeichen, Beispielwert, Eintrag der Entwicklungsliste) lässt den Start im Modus `production` abbrechen (Ist: nur Warnung im Protokoll, Passwort wird trotzdem verwendet).
Abnahme: `SM_ADMIN_PASSWORD` mit 9 Zeichen im Modus `production` → Start bricht ab; bei umgesetztem Einrichtungslink erlaubt der Link genau eine Einlösung und läuft nach der festgelegten Frist ab (zweite Einlösung → Fehler).

**BET-040** · P1 · Status: Ist · Erste Anmeldung und Einrichtungsassistent
Reihenfolge nach der Installation: Anmeldung als Erst-Administrator, sofort eigenes Passwort, danach die Willkommensseite „Lizenzschlüssel eingeben, um fortzufahren“ (vor allem anderen; ohne gültige Lizenz sonst nur Administration erreichbar), nach gültiger Bindung der Einrichtungsassistent unter `/einrichtung`. Zwei-Faktor ist für Administration, Schulleitung und Sekretariat Pflicht. Der Assistent speichert Fortschritt serverseitig je Schritt, Schritte sind überspringbar und später fortsetzbar; ein Hinweisband erscheint bis zum „Einrichtung abschließen“; danach bleibt der Assistent über die Verwaltung („Einrichtung fortsetzen“) erreichbar. Rechte: Schritte lesen/bearbeiten, abschließen und wieder öffnen verlangen `settings.edit` und `users.manage`. Inhalt und Reihenfolge der Schritte stehen im Bereich STA; Test-E-Mail, Schuldaten, Ferien-Import und Importe sind dort beschrieben. Der Entwurf einer Eingabe wird nur im Browser gehalten.
Abnahme: Frische Instanz ohne Lizenz: nach dem Passwortwechsel erscheint die Willkommensseite; mit gültigem Schlüssel führt „Weiter“ in `/einrichtung`; ein Schritt „überspringen“ und später fortsetzen behält den Stand nach Neustart; ein Konto ohne `settings.edit` erhält 403 auf `PUT /api/v1/setup/steps/{key}`.

**BET-041** · P0 · Status: Ist · Notfall- und Betriebsbefehle (Kommandozeile)
Die Befehle sind nur für Betreiber mit Serverzugang (im Container Aufruf `schulmanager-admin`).

| Befehl | Wirkung |
|---|---|
| `check-config` | Konfiguration prüfen (BET-010) |
| `migrate` | Datenbank-Migrationen ausführen |
| `create-admin --username U` | Administrator anlegen; ohne Passwort: Startpasswort (4 Gruppen zu 4 Zeichen) mit Pflichtwechsel; Passwort per Standardeingabe: Passwortregeln geprüft, kein Pflichtwechsel; `--update` macht ein bestehendes Konto zum Administrator; `--temp` erzeugt ein Startpasswort mit Wechselzwang |
| `reset-password --username U` | neues Einmalpasswort (3 Gruppen zu 4 Zeichen) mit Pflichtwechsel; alle Sitzungen des Kontos beendet |
| `unlock --username U` | Anmeldesperre aufheben |
| `disable-2fa --username U` | Zwei-Faktor eines Kontos abschalten (verlorenes Gerät) |
| `list-users [--role R]` | Konten mit Kennzeichen (Zwei-Faktor, inaktiv, Passwortwechsel offen) |
| `load-demo [--time-limit S] [--classes-per-grade N] [--no-accounts]` | Demo-Schule laden; in `production` verweigert (BET-011) |
| `backup`, `maintenance` | App-Sicherung (BET-045) bzw. Wartungslauf (BET-069) auslösen |
| `gen-key`, `rotate-keys [--only BEREICH]`, `crypto-status`, `verify-files` | Schlüsselverwaltung (BET-052 bis BET-054) |
| `restore`, `restore-test`, `backup-list`, `backup-verify` | Sicherungsverwaltung des Backup-Dienstes (BET-042 bis BET-049) |
| `logs [Dienst]` | Protokolle der Dienste |

Abnahme: Je Befehl ein Aufruf mit Soll-Ausgabe; `reset-password` für ein unbekanntes Konto → Fehlermeldung ohne Seiteneffekt; nach `unlock` ist eine zuvor mit „zu viele Versuche“ (429) gesperrte Anmeldung wieder möglich; ein Aufruf durch eine Webanfrage ist nicht möglich (nur Serverzugang).

---

## 7. Sicherung, Wiederherstellung, Übungspflicht

**BET-042** · P0 · Status: Ist · Backup-Dienst (System-Sicherung)
Ein eigener Dienst (Sidecar-Container) sichert täglich zu `BACKUP_TIMES` (Standard 02:30; mehrere Zeiten, z. B. `02:30 12:45`) und beim Start des Backup-Containers: (1) Datenbank: PostgreSQL als komprimierter Dump `schulmanager_pg_<Zeit>.dump`; SQLite als Online-Sicherung mit Integritätsprüfung `schulmanager_sqlite_<Zeit>.db.gz`; (2) Dateien: Datenverzeichnis der App ohne Datenbankdateien, ohne App-Sicherungen und ohne das Zielverzeichnis, als `schulmanager_files_<Zeit>.tar.gz` (enthält auch die Lizenz-Zustandsdateien, BET-072). Zu jeder Datei eine `.sha256`-Prüfsumme; mit `BACKUP_GPG_PASSPHRASE` alle Dateien GPG-verschlüsselt (AES-256, Endung `.gpg`); ohne Passphrase ist kein Restore verschlüsselter Dateien möglich. Nicht gesichert werden müssen Container-Images, Proxy-Zertifikate (werden neu ausgestellt) und Prometheus-/Grafana-Daten; die `.env` wird getrennt und verschlüsselt aufbewahrt. Die Sicherungen enthalten keine Schlüssel des Schlüsselrings.
Abnahme: Nach dem Lauf zu `BACKUP_TIMES` liegen Datenbank- und Datei-Archiv samt `.sha256` vor (mit Endung `.gpg`, wenn die Passphrase gesetzt ist); die Prüfsummen stimmen; der Wert aus `SM_ENCRYPTION_KEYS` kommt in keiner Sicherung vor; manuelle Auslösung (`make backup` bzw. `backup`) erzeugt dieselben Dateien unter `manual` mit Kennzeichen „manuell“.

**BET-043** · P0 · Status: Ist · Aufbewahrung und Gesundheit der Sicherungen
Rotation: `daily` 14 Tage; `weekly` 8 Wochen (erstes Backup je ISO-Woche); `monthly` 12 Monate (erstes Backup je Monat); `manual` (vor Updates und Restores, Kennzeichen `vor-update`, `vor-restore`) die letzten 10. Wochen- und Monatsstände sind Hardlinks und belegen keinen zusätzlichen Platz. Der Backup-Container wird „unhealthy“, wenn das letzte erfolgreiche Backup älter ist als `BACKUP_MAX_AGE_HOURS` (26 Stunden); optional ruft er `BACKUP_PING_URL` (Erfolg) bzw. `BACKUP_PING_URL_FAIL` (Fehler) auf.
Abnahme: Simulierte Tagesläufe über 400 Tage ergeben höchstens 14 Tages-, 8 Wochen-, 12 Monats- und 10 manuelle Stände; nach 27 Stunden ohne erfolgreiches Backup ist der Backup-Container „unhealthy“ und `BACKUP_PING_URL_FAIL` wird aufgerufen.

**BET-044** · P0 · Status: Ist · Offsite-Kopie (3-2-1)
`BACKUP_RCLONE_REMOTE` (Ziel mit Bucket und Pfad) plus `RCLONE_CONFIG_OFFSITE_*` (Vorlagen für S3, SFTP, WebDAV/Nextcloud). Nach jedem Backup spiegelt rclone die Ablage; `BACKUP_RCLONE_MODE=copy` (Standard) löscht am Ziel nie. Empfehlungen: Anbieter in Deutschland/EU mit AV-Vertrag, Verschlüsselung, Versionierung oder Object Lock am Bucket (Schutz vor Ransomware), eigener Zugang mit Schreibrecht nur auf diesen Bucket.
Abnahme: Nach einem Backup liegen die Dateien am Ziel; das Löschen einer lokalen Sicherung entfernt die Datei am Ziel nicht (`copy`); der Offsite-Zugang kann in keinen anderen Bucket schreiben.

**BET-045** · P1 · Status: Ist · App-eigene Sicherung (Oberfläche, Administration)
Administration → System bzw. Statusseite: Sicherung anlegen, auflisten, herunterladen, löschen und prüfen (Recht `system.admin`; Schnittstellen `GET/POST /api/v1/admin/backups`, `GET/DELETE /api/v1/admin/backups/{name}`, `POST …/{name}/verify`). Dateinamen `schulmanager-JJJJMMTT-HHMMSS.db` (SQLite: konsistente Kopie über die Datenbank-Sicherungsfunktion, Zeitlimit der Quelle 30 Sekunden) bzw. `.json.gz` (PostgreSQL: JSON-Export aller Tabellen; verschlüsselte Spalten bleiben als Token; Planversionen ohne Binärdaten; das aktuelle Planungsdokument verschlüsselt mit Bindung an die Version), bei Namensgleichheit `-n` angehängt; nur dieses Muster wird gelistet und ist abrufbar (kein Pfadzugriff). Ablage `SM_BACKUP_DIR`; Rotation `SM_BACKUP_KEEP` (30, 0 = keine; Rotation nur beim Anlegen); optional automatisch alle `SM_AUTO_BACKUP_HOURS` im Wartungslauf (Standard 0 = aus); Dateirechte 0600; Audit-Eintrag `system.backup` (Name, Größe, Art). Diese Sicherung enthält nur die Datenbank, keine Dateien, und ersetzt nicht den Backup-Dienst (BET-042). Ein älteres Sicherungsformat wird beim Prüfen akzeptiert.
Abnahme: Anlegen → Datei im Sicherungsverzeichnis und Audit-Eintrag `system.backup`; Download als Administration → 200, als Schulleitung → 403; Abruf mit Name `../x` → 404; die 31. Sicherung entfernt die älteste; „Prüfen“ liefert ein Ergebnis als Text (BET-049).

**BET-046** · P1 · Status: offen · Sicherung in der Oberfläche mit Dateien
Backlog-Anforderung (B-05, offen): „Sicherung erstellen“ erzeugt ein Archiv aus Datenbank und Dateien (Atteste, Kursraum-Dateien, Anhänge); Schlüssel werden nicht im Klartext mitgesichert; ohne passenden Schlüssel bricht die Wiederherstellung mit klarer Meldung ab. „Herunterladen“ und „Wiederherstellen“ sind getrennte Vorgänge (BET-047). Ist-Lücke: die App-Sicherung enthält keine Dateien (Ablageort der Dateien und Verhältnis zur Schlüsselrotation in den Quellen offen).
Abnahme: Rundlauf: Sicherung in der Oberfläche erstellen → leere Instanz → Wiederherstellen (Befehl) → Atteste und Kursraum-Dateien lesbar; Wiederherstellen ohne passenden Schlüssel → Abbruch mit klarer Meldung und unveränderter Datenbank.

**BET-047** · P0 · Status: Ist · Wiederherstellung (Restore) nur per Befehl
Wiederherstellung per Klick in der Oberfläche ist bewusst nicht gebaut (spätere Festlegung 16.10. überstimmt die Backlog-Forderung vom 10.10., die einen Knopf „Wiederherstellen“ vorsah; `[unklar: die Vorschau-Anleitung nennt noch „Laden einer Sicherung“ in Administration → System]`). Befehl `restore` (Container: `make restore FILE=<Datei>`): (1) Sicherheitsabfrage, Eingabe des Wortes `WIEDERHERSTELLEN`; (2) Datei in den Backup-Container; (3) App stoppen (sie hält die Planungsdaten im Speicher); (4) Sicherheitssicherung des aktuellen Stands (`manual`, Kennzeichen `vor-restore`); (5) Prüfsumme prüfen, ggf. entschlüsseln; (6) Schema in einer Transaktion ersetzen (bei Fehler bleibt alles unverändert); (7) App starten; (8) Gesundheitsprüfung. SQLite: gleicher Ablauf, die alte Datei bleibt als `schulmanager.db.vor-restore-<Zeit>` liegen. Das Datei-Archiv wird getrennt in den Backup-Container kopiert und eingespielt. Ohne Container: Dienst stoppen, Restore-Skript als Dienstbenutzer mit geladener Umgebungsdatei ausführen, Dienst starten. Ein älteres Backup wird danach automatisch migriert.
Abnahme: Restore einer beschädigten Datei → Datenbank unverändert, klare Fehlermeldung; Restore ohne Eingabe von `WIEDERHERSTELLEN` → Abbruch; nach dem Restore existiert ein `vor-restore`-Stand; die Oberfläche zeigt keinen Wiederherstellen-Knopf; eine gültige Sicherung stellt Stundenplan-Stand und Konten wieder her (Konten-Zahl gleich).

**BET-048** · P0 · Status: Ist · Wiederanlauf auf neuem Server und Richtwerte
Disaster Recovery: neuen Server nach den Installationsschritten 1 bis 6 vorbereiten; dieselbe `.env` verwenden (aus der getrennten Sicherung; `SM_SECRET_KEY` muss gleich bleiben, sonst werden Sitzungen und API-Tokens ungültig); Offsite-Sicherungen holen; Datenbank- und Backup-Dienst starten; Restore mit der neuesten Datei; DNS auf die neue Adresse umstellen (der Proxy holt neue Zertifikate). Benötigt werden: Datenbank-Sicherung, Datei-Archiv vom selben Zeitpunkt und der Verschlüsselungsschlüssel. Richtwerte: RPO (maximaler Datenverlust) = Backup-Abstand (Standard 24 Stunden, mit zwei Zeiten etwa 12 Stunden); RTO (Wiederanlauf) etwa 1 Stunde mit vorbereitetem Server.
Abnahme: Übung auf einer frischen VM mit Offsite-Sicherung: Gesamtdauer bis zur funktionierenden Anmeldung und zum Vertretungsplan gemessen und protokolliert (Soll etwa 1 Stunde); danach melden sich bisherige Nutzer mit ihren Passwörtern an (Sitzungen bleiben mit gleichem `SM_SECRET_KEY` gültig).

**BET-049** · P0 · Status: Ist · Übungspflicht für Wiederherstellung
(1) Monatlich Pflicht: Test-Restore (`restore-test` mit einer `monthly`-Datei): spielt den Dump in eine temporäre Datenbank, zählt die Planversionen und löscht die Test-Datenbank wieder; Live-Daten bleiben unberührt. (2) Halbjährlich ein vollständiger Probe-Restore auf einer separaten VM (Installation, Backup einspielen, Anmeldung und Vertretungsplan prüfen); das Ergebnis wird dokumentiert (Datum, Backup-Datei, Dauer, Ergebnis, Name) und ist Teil der technisch-organisatorischen Maßnahmen. (3) In der Oberfläche „Prüfen“: spielt eine App-Sicherung in eine Wegwerf-Kopie ein; SQLite: Integritätsprüfung „ok“, Zeilen je Tabelle, Konten größer 0 und Planversionen größer 0 = bestanden; JSON: Format „schulmanager-backup“ und Planungsdokument vorhanden = bestanden; die Kopie wird danach gelöscht. (4) Die Statusseite warnt, wenn die letzte Sicherung älter als 48 Stunden ist (BET-061).
Abnahme: `restore-test` auf eine `monthly`-Datei meldet die Zahl der Planversionen und lässt die Live-Datenbank unverändert; „Prüfen“ einer absichtlich beschädigten App-Sicherung → „nicht bestanden“; im Betreiber-Paket existiert eine Vorlage für das Protokoll des halbjährlichen Probe-Restores.

**BET-050** · P1 · Status: offen · Vollständiger Restore-Rundlauf mit echter Sicherung
Der Restore-Test vom 17.10.2026 (Sicherung des Hauptservers in einem Container ohne Netz, gleicher Programmstand) ergab: Datenbank gesund, Stundenplan im richtigen Stand, alle 5.464 Konten lesbar; die Dateiprüfung umfasste nur 5 Dateien, weil die Sicherung nicht mehr enthielt. Die Aussage „funktioniert“ gilt nur für Datenbank und Konten. Nutzer-Vorgabe: einmal echt, vollständig. Wiederholung: Sicherung mit Dateien, leere Instanz, Restore, `verify-files`.
Abnahme: Rundlauf mit einer Sicherung, die Datenbank und Dateien enthält (mindestens Atteste, Kursraum-Dateien, Nachrichten-Anhänge): `verify-files` meldet Exit-Code 0 und die Dateizahl entspricht der Quell-Instanz; ein Attest und eine Nachricht sind in der Oberfläche lesbar; das Ergebnis ist protokolliert.

**BET-051** · P0 · Status: Ist · Sicherungen sind personenbezogene Daten
Sicherungen enthalten Schul- und Personendaten (verschlüsselt, ohne Schlüssel) und haben hohen Schutzbedarf: Zugriff nur Administration bzw. Betreiber; Offsite verschlüsselt; Aufbewahrung begrenzt (Rotation). Personenlöschungen nach dem Löschkonzept (DAT) wirken nicht rückwirkend in Sicherungen; der Rückhalt ergibt sich aus der Rotation (bis 12 Monate bei Monatsständen, App-Sicherungen etwa 30 Stände). `[unklar: Folgeregel, ob nach einem Restore bereits gelöschte Personen erneut gelöscht werden müssen]`
Abnahme: Ein Download der App-Sicherung durch ein Konto ohne `system.admin` → 403; der Betreiber-Hinweis zum Löschkonzept nennt die Rückhaltefristen der Sicherungen; die Datenschutz-Unterlagen führen Sicherungen als Verarbeitung.

---

## 8. Schlüsselverwaltung und Rotation

**BET-052** · P0 · Status: Ist · Schlüsselring `SM_ENCRYPTION_KEYS`
Nachrichten, hochgeladene Dateien (inklusive Dateinamen), Atteste und Freitexte werden mit AES-256-GCM gespeichert (Verfahren und Feldliste: DAT). Der Master-Schlüsselring steht in `SM_ENCRYPTION_KEYS`: Einträge `Kennung:Schlüssel` (Schlüssel 32 Byte Base64), getrennt durch Komma, Semikolon, Leerzeichen oder Zeilenumbruch; Kennung 1 bis 32 Zeichen (A–Z, a–z, 0–9, `_`, `-`), doppelte Kennungen sind ein Fehler, `dev` ist reserviert. Der erste Eintrag verschlüsselt neue Daten, alle weiteren dienen nur zum Lesen. In Produktion Pflicht: ohne Eintrag bricht der Start ab (auch der Container-Start). Erzeugen: Befehl `gen-key` (Standard-Kennung `k` plus Datum JJJJMMTT oder frei, z. B. `k1`; alternativ 32 Byte Base64); Eintrag in `.env` (Rechte 600). `crypto-status` zeigt aktive Kennung und Fingerabdruck (12 Hexzeichen, nicht umkehrbar, kein Geheimnis); der Fingerabdruck steht auch auf der Statusseite zum Abgleich. Fehlermeldungen enthalten nie Schlüsselmaterial.
Abnahme: Start ohne `SM_ENCRYPTION_KEYS` in `production` → Abbruch; Schlüssel mit 31 Byte oder ungültigem Base64 → Abbruch mit Hinweis auf Tippfehler/abgeschnittenen Eintrag/Anführungszeichen; `crypto-status` gibt Kennung und 12-stelligen Fingerabdruck aus, aber nie den Schlüssel; zwei Einträge mit gleicher Kennung → Fehler.

**BET-053** · P0 · Status: Ist · Schlüssel sichern und aufbewahren
Der Schlüsselring wird getrennt vom Backup gesichert: Passwort-Tresor der Schulleitung und versiegelter Ausdruck im Safe; nicht im Backup-Speicher und nicht per E-Mail. Ohne Schlüssel sind Nachrichten, Dateien und Atteste auch aus allen Sicherungen unwiederbringlich verloren. Die Statusseite zeigt den Hinweis „Schlüsselverlust bedeutet Datenverlust“ und den Fingerabdruck. Für Restore und Umzug werden Datenbank-Sicherung, Datei-Archiv vom selben Zeitpunkt und der Schlüssel benötigt.
Abnahme: Ein Restore in eine Instanz mit anderem Schlüsselring → verschlüsselte Inhalte nicht lesbar und klare Fehlermeldung „Datei beschädigt oder Schlüssel fehlt“ (kein Absturz); Betreiber-Paket enthält die Aufbewahrungsregel; die Statusseite zeigt den Hinweis.

**BET-054** · P0 · Status: Ist · Schlüsselrotation
Anlass: jährlich, bei Personalwechsel, bei Verdacht auf Offenlegung. Ablauf: (1) Sicherung erstellen; (2) neuen Schlüssel erzeugen (neue Kennung, z. B. `k2`); (3) in `.env` vorn eintragen, den alten dahinter lassen; (4) App neu starten; (5) alle Datenschlüssel neu verpacken: Befehl `rotate-keys`, je Bereich einzeln mit `--only` (u. a. Dateiablage, Nachrichten, Planungsdokument samt Verlauf), Anzahl wird ausgegeben; Nutzdaten werden nicht neu geschrieben (bei Dateien nur der Kopf, Blöcke werden kopiert, atomar ersetzt), auch bei vielen GB schnell; (6) prüfen: `crypto-status` und `verify-files` (entschlüsselt alle Dateien und vergleicht Prüfsummen; Exit-Code 1 bei fehlenden oder beschädigten Dateien, IDs werden ausgegeben); (7) den alten Schlüssel erst entfernen, wenn alle Sicherungen von vor der Rotation abgelaufen sind (bis zu 12 Monate; Kalendereintrag), bis dahin im Tresor und in der Schlüsselliste behalten. Nach der Rotation werden auch TOTP-Geheimnisse (Zwei-Faktor) und verschlüsselte Zugangsdaten der Mail-Konten neu verpackt. Werte, die innerhalb des Planungsdokuments zusätzlich verschlüsselt sind (z. B. Abwesenheitsgründe aus Lehrkraft-Anträgen), behalten ihren alten Schlüssel; deshalb bleibt der alte Schlüssel im Ring. Planversionen im reinen Komprimierformat (Altbestand) werden beim Start bzw. durch `rotate-keys` umgeschlüsselt.
Abnahme: Nach Rotation `k1`→`k2`: `crypto-status` zeigt `k2` aktiv; neu angelegte Daten sind mit `k2` verschlüsselt, alte bleiben lesbar; wird `k1` aus dem Ring entfernt, meldet `verify-files` Exit 1 mit den betroffenen IDs und das Log „Schlüssel nicht in SM_ENCRYPTION_KEYS“; nach erneutem Anhängen von `k1` und Neustart verschwindet der Fehler; ein Zwei-Faktor-Konto und ein verbundenes Mail-Konto funktionieren nach der Rotation.

**BET-055** · P1 · Status: offen · Notfall-Neuverschlüsselung bei Kompromittierung
Bei Kompromittierung eines Master-Schlüssels genügt das Neu-Verpacken der Datenschlüssel nicht; vorgesehen ist eine vollständige Neuverschlüsselung (neuer Datenschlüssel je Wert, je Datei). `[unklar: Aufrufweg im Altbestand nicht belegt]`
Abnahme: Befehl/Verfahren dokumentiert und getestet: nach der Ausführung ist der kompromittierte Schlüssel aus dem Ring entfernbar, ohne dass eine Zeile oder Datei unlesbar wird (`verify-files` Exit 0, Stichprobe Nachricht/Attest lesbar).

**BET-056** · P0 · Status: Ist · Geheimnis `SM_SECRET_KEY`
Pflicht in Produktion, mindestens 32 Zeichen, erzeugt mit 32 Byte Zufall (hex). Es wirkt als HMAC-Schlüssel für Sitzungs-Hashes, API-Token, Codes, SSO-Status, Teilnahmekennungen im Lernbereich und den OAuth-Status des Postfachs. Ein Wechsel macht alle Sitzungen, API-Token und offenen Codes ungültig (bei Rotation, Restore und Umzug beachten; für Restore/Umzug gleich lassen). In der Entwicklung: einmal erzeugt in einer Datei im Datenverzeichnis (Rechte 600) und wiederverwendet; ist das Verzeichnis nicht schreibbar, entsteht je Start ein zufälliger Schlüssel (Sitzungen gehen beim Neustart verloren).
Abnahme: Wechsel des Werts + Neustart → alle bestehenden Sitzungen und API-Zugangs-Token liefern 401; Verbleib desselben Werts nach Restore → Sitzungen gültig; in `production` startet die Instanz mit 31 Zeichen nicht.

**BET-057** · P1 · Status: Ist · Fehlerbilder der Schlüsselverwaltung
Die Betreiber-Dokumentation beschreibt und die Meldungen unterscheiden: (a) „Schlüssel muss in Produktion gesetzt sein“ (Eintrag fehlt; nur bei ganz neuer Installation neu anlegen); (b) Schlüssel nicht 32 Byte oder kein gültiges Base64 (Tippfehler, abgeschnittener Eintrag, Anführungszeichen); (c) Log „Schlüssel nicht in SM_ENCRYPTION_KEYS“ (alter Schlüssel zu früh entfernt oder altes Backup eingespielt: Schlüssel hinten anhängen, Neustart, `rotate-keys`); (d) Download liefert „Datei beschädigt oder Schlüssel fehlt“ (`verify-files`, `crypto-status`, Datei-Archiv aus dem Backup zurückspielen). Manipulation, falsches Zusatzdatum oder falscher Schlüssel führt zu „ungültig“, eine unbekannte Schlüssel-Kennung zu „nicht lesbar“; Klartext wird nie zurückgegeben.
Abnahme: Je Fehlerbild ein Test mit der erwarteten Meldung; ein manipulierter Chiffretext liefert „ungültig“, kein Klartext.

---

## 9. Überwachung, Betriebsstatus, Protokolle

**BET-058** · P0 · Status: Ist · Gesundheits- und Bereitschaftsprüfung
`GET /healthz` (ohne Anmeldung; auch `HEAD`): 200 mit `{"status":"ok","db":"ok","version","started","plan_version"}`; 503 bei Datenbankproblemen. `GET /healthz/ready` (Bereitschaft für Lastverteiler): 503, solange eine Drain-Markierung gesetzt ist (Update-Installation, BET-167). `GET /api/v1/version` ohne Anmeldung. Diese Endpunkte bleiben auch bei Lizenzsperre erreichbar und sind von der Anfrage-Begrenzung ausgenommen. Docker-Gesundheitsprüfungen für App, Datenbank, Proxy und Backup; ein Prüfskript fragt `/healthz` gegen die Adresse ab.
Abnahme: `/healthz` ohne Anmeldung → 200 und die vier Felder; Datenbank gestoppt → 503; Drain-Markierung gesetzt → `/healthz/ready` 503, `/healthz` weiter 200; bei Lizenzsperre bleiben beide erreichbar.

**BET-059** · P1 · Status: Ist · Metriken
`GET /metrics` im Prometheus-Textformat, Zugang nur mit Bearer-Token (`SM_METRICS_TOKEN`); ohne Token 401 mit Fehlerkennung `metrics_token_required`; von außen am Proxy zusätzlich gesperrt; von Anfrage-Begrenzung ausgenommen. Alle Namen tragen das Präfix `schulmanager_` (technische Konstante): `schulmanager_http_requests_total{method,route,status}`, `schulmanager_http_request_duration_seconds{method,route}` (Route als Vorlage, ungematcht `<unmatched>`), `schulmanager_http_requests_in_flight`, `schulmanager_sse_clients`, `schulmanager_jobs_running`, `schulmanager_school_version`, `schulmanager_login_failures_total`, `schulmanager_logins_total{result}`, `schulmanager_users{role,active}`, `schulmanager_sessions_active`, `schulmanager_school_versions_stored`, `schulmanager_uptime_seconds`, `schulmanager_info{version,env,db}`; dazu Prozessmetriken (Speicher, CPU-Zeit, offene Dateien). Für Prometheus ein Token erzeugen (24 Byte Zufall, hex) und in die Token-Datei des Prometheus-Verzeichnisses legen. Eine neue Metrik braucht das Präfix, ein Test sichert den Namen ab.
Abnahme: `GET /metrics` ohne Token → 401 `metrics_token_required`; mit Token → 200 und alle genannten Namen; über den Proxy von außen → 403/404; ein Test schlägt an, wenn eine Metrik ohne Präfix registriert wird.

**BET-060** · P1 · Status: Ist · Statusseite `/betrieb`
Nur Administration (`system.admin`). Inhalt: Prüfliste mit Stufen je Punkt (gelb = Empfehlung, roter Punkt = Handeln, BET-061); Kennzahlen (Version, Laufzeit seit Start, Datenbankstand, freier Speicher, Mail, letzte Sicherung, Wartungslauf, Lizenz); Liste der Sicherungen mit Alter, Größe und Prüfergebnis (BET-045); Fehlerprotokoll mit Fehlernummer (BET-062); Karte „Updates“ (BET-159); Hinweis zu Impressum und Datenschutztext (warnt, wenn der Text fehlt oder noch Platzhalter in eckigen Klammern enthält); Betriebsmodus (BET-003); Schlüssel-Fingerabdruck (BET-053). Schnittstellen: `GET /api/v1/admin/status`, `GET /api/v1/admin/system` (Systemangaben), `POST /api/v1/admin/maintenance` (Wartung jetzt), `GET/DELETE /api/v1/admin/errors`. Kein Wert eines Geheimnisses wird angezeigt.
Abnahme: Als Administration alle genannten Blöcke sichtbar; als Schulleitung/Lehrkraft → 403 bzw. Seite nicht im Menü; `GET /api/v1/admin/system` enthält keinen Schlüssel-, Passwort- oder Token-Wert.

**BET-061** · P1 · Status: Ist · Prüfpunkte und Schwellen der Statusseite

| Prüfung | Schwelle → Ergebnis |
|---|---|
| Datenbank | erreichbar, Schema-Stand aktuell (sonst Migrationshinweis) |
| Speicherplatz frei | ≥ 15 % ok; 5 bis 15 % Warnung; < 5 % Fehler |
| Sicherung (Alter der letzten) | ≤ 48 Stunden ok, sonst Warnung; keine Sicherung: Warnung in Produktion, sonst ok |
| Fehlerprotokoll | 0 Fehler in 24 Stunden ok, sonst Warnung |
| E-Mail | nicht eingerichtet: Warnung; Test-Postausgang aktiv: Warnung; nicht zustellbare Mails: Warnung |
| Verschlüsselung | Schlüssel aus Konfiguration ok; abgeleiteter Entwicklungsschlüssel Warnung |
| Zwei-Faktor | in Produktion und nicht für Administration/Schulleitung erzwungen: Warnung |
| Administration | kein aktives Administrator-Konto: Fehler |
| HTTPS | Adresse mit `https` und sicheres Cookie ok; sonst Warnung |
| Wartungslauf | letzter Lauf vorhanden ok; sonst Warnung |
| Lizenz, Impressum, Datenschutztexte | laut Lizenzstufe bzw. Textstand |

Abnahme: Je Zeile ein Zustand: z. B. freier Platz 10 % → Warnung, 3 % → Fehler; letzte Sicherung 49 Stunden alt → Warnung; keinen aktiven Administrator → Fehler; Wartungslauf nie gelaufen → Warnung.

**BET-062** · P1 · Status: Ist · Fehlerprotokoll
Gespeichert werden nur Meldungen der Stufen ERROR und CRITICAL: Zeit, Stufe, meldende Stelle, Meldungstext (gekürzt auf 2000 Zeichen), Anfrage-Kennung, Anfragepfad ohne Abfrageteil (Kennungen maskiert), technische Ablaufverfolgung (höchstens 8000 Zeichen, das Ende der Ausgabe). Aufbewahrung 30 Tage, höchstens 1000 Zeilen (Wartung). Schreibweise asynchron über eine Warteschlange (500 Einträge) mit Hintergrund-Schreiber: blockiert nie die auslösende Anfrage, eigene Protokollierung wird nicht zurückgekoppelt. Nutzer sehen bei unerwarteten Fehlern „Das hat nicht geklappt“ mit einer Fehlernummer (Anfrage-Kennung), die im Fehlerprotokoll nachgeschlagen wird. Ansehen und Leeren: `system.admin`. Tabelle `error_log` (`created_at`, `level`, `logger`, `message`, `request_id`, `path`, `trace`).
Abnahme: Ein ausgelöster Serverfehler erscheint in der Fehlerliste mit Fehlernummer; die 1001. Zeile verdrängt die älteste; Einträge älter als 30 Tage sind nach dem Wartungslauf weg; eine Meldung mit 5000 Zeichen wird auf 2000 gekürzt; Fehler beim Schreiben des Fehlerprotokolls blockieren die Anfrage nicht.

**BET-063** · P0 · Status: Ist · Protokolle (Logs)
App-Protokoll im Modus `production` strukturiert (JSON) mit Zeitstempel, Stufe, Logger, Meldung und Anfrage-Kennung; jede Antwort trägt den Kopf `X-Request-ID`. Zugriffsprotokoll je Anfrage: Methode, Pfad, Status, Dauer, gekürzte Client-Adresse (IPv4 auf /24, IPv6 auf /48), iCal-Tokens maskiert. Keine Passwörter, Codes, Telefonnummern oder Geheimnisse im Log; Demo-Passwörter nie. Container-Rotation `LOG_MAX_SIZE` (10 MB) mal `LOG_MAX_FILES` (5), komprimiert, je Container; ohne Container Journal (Aufbewahrung 14 Tage) und nginx-Protokolle mit logrotate. Aufbewahrung von Protokollen mit IP-Adressen so kurz wie nötig, in der Regel höchstens 14 Tage. Zentrales Logging (Loki, Graylog u. a.) über den Log-Treiber der Compose-Konfiguration möglich. Das fachliche Audit-Protokoll (wer hat was geändert) liegt in der Datenbank (Administration → Audit, `GET /api/v1/audit`; Inhalte: DAT).
Abnahme: Eine Anfrage erzeugt eine Log-Zeile mit gekürzter IP und `X-Request-ID`, die im Fehlerfall dieselbe Kennung trägt; ein Anmeldeversuch hinterlässt kein Passwort im Log; ein Abruf des iCal-Feeds erscheint mit maskiertem Token.

**BET-064** · P1 · Status: Ist · Monitoring-Profil und Alarme
Profil `monitoring`: Prometheus und Grafana, nur über localhost (Tunnel per SSH); Prometheus holt die Metriken im internen Netz; Dashboard „Schulmanager – Überblick“ wird automatisch bereitgestellt (Bereiche Überblick: Status, Anfragen pro Sekunde, Fehlerquote 5xx, Latenz p95, Live-Clients, laufende Jobs, Planversion; HTTP: Anfragen nach Status, Latenz p50/p95/p99, langsamste und meistgenutzte Routen; Live-Betrieb und Sicherheit: SSE-Verbindungen, Fehlanmeldungen, Jobs; Konten und Prozess: aktive Sitzungen, Konten je Rolle, Speicher, CPU, offene Dateien). Alarme (Grafana, E-Mail an `ALERT_EMAIL`, Kontaktpunkt „schulmanager-admins“): nicht erreichbar (2 Minuten); Fehlerquote über 5 % (10 Minuten); p95-Latenz über 2 Sekunden (15 Minuten). Dieselben Regeln plus Speicher über 2,5 GB und viele Fehlanmeldungen stehen in den Prometheus-Regeln. Weitere Kanäle (Matrix, Teams, Telegram, Signal-Gateway) in Grafana einrichtbar. Profil `uptime` (Uptime-Kuma, nur localhost): empfohlene Monitore: HTTP-Stichwortprüfung auf `/healthz` (Stichwort `status` mit Wert `ok`, Intervall 60 Sekunden), Zertifikatsablauf mit Warnung 14 Tage vorher, Push-Monitor „Backup“ mit 25 Stunden Intervall (Adresse als `BACKUP_PING_URL`); Benachrichtigung an IT-Betreuung und Schulleitung; besser auf einem anderen Server, damit ein Totalausfall gemeldet werden kann. Prometheus-Daten 15 Tage.
Abnahme: Mit gestartetem Profil ist `up=1` für die App; App stoppen → nach 2 Minuten Alarm per E-Mail an `ALERT_EMAIL`; das Dashboard zeigt alle vier Bereiche; Grafana ist von außen nicht erreichbar.

**BET-065** · P1 · Status: offen · E-Mail-Alarm aus der App
Alarmregeln existieren nur in Prometheus/Grafana. Fehlt: Versand einer E-Mail durch die App selbst an die Administration bei fehlender Sicherung (älter als 48 Stunden) oder Fehlerhäufung.
Abnahme: Sicherung älter als 48 Stunden → die Administration erhält eine E-Mail (und eine Benachrichtigung in der App); ohne Mailversand erscheint stattdessen der rote Punkt auf `/betrieb`.

**BET-066** · P2 · Status: offen · Externe Sicherung auf der Statusseite
Die Statusseite zeigt nur App-Sicherungen, nicht die des Backup-Dienstes und nicht die Offsite-Kopie.
Abnahme: Die Statusseite zeigt Alter und Größe der letzten Sicherung des Backup-Dienstes und der letzten Offsite-Kopie; ist eine der beiden älter als `BACKUP_MAX_AGE_HOURS`, erscheint eine Warnung.

**BET-067** · P2 · Status: offen · Öffentliche Statusseite und Wartungshinweis
Backlog (B-58): öffentliche Statusseite und Wartungshinweis; Wartung außerhalb der Unterrichtszeit planbar; Ergebnisse der Lasttests (Kap. 17, BET-197) und Betriebsempfehlung in der Betriebsdokumentation.
Abnahme: Eine ohne Anmeldung erreichbare Seite zeigt „in Betrieb“ bzw. einen geplanten Wartungszeitraum; ein eingetragener Wartungshinweis erscheint auf der Anmeldeseite.

---

## 10. Wartungsjobs

**BET-068** · P0 · Status: Ist · Wartungslauf
Ein Hauptlauf startet sofort nach dem Serverstart und danach alle `SM_MAINTENANCE_INTERVAL` Sekunden (Standard 3600; Untergrenze 5). Reihenfolge der Stufen: Sitzungen, Tokens, Anmeldeversuche, Dateiablage, Dokumente, Formulare, Kontakt-Codes, Zugangsbriefe, Benachrichtigungen, Kursraum-Papierkorb, Fehlerprotokoll, Löschkonzept. Jede Stufe hat eine eigene Fehlerbehandlung; ein Fehler stoppt die übrigen Stufen nicht. Der letzte Lauf (Zeit, Summe gelöschter Einträge) wird im Zustandsspeicher (`system_state`, Schlüssel `maintenance`) vermerkt und auf der Statusseite gezeigt. Manuell auslösbar: Befehl `maintenance`, Schaltfläche „Wartung jetzt ausführen“ (Administration → System), `POST /api/v1/admin/maintenance`. Im Mehrknoten-Betrieb läuft die Wartung nur auf dem Leader (BET-165). `SM_MAINTENANCE_INTERVAL=0` bedeutet im Neubau eindeutig „aus“ (Ist: die Schleife läuft trotzdem mindestens alle 5 Sekunden).
Abnahme: Nach dem Start läuft der erste Lauf sofort (Zeitstempel in `system_state`); ein absichtlich fehlschlagender Job in Stufe 4 verhindert die Stufen 5 bis 12 nicht; `SM_MAINTENANCE_INTERVAL=0` → kein automatischer Lauf, manueller Lauf funktioniert.

**BET-069** · P0 · Status: Ist · Wartungsjobs und Fristen

| Job | Intervall | Wirkung |
|---|---|---|
| Abgelaufene Anmeldesitzungen | jeder Lauf | löscht Sitzungen mit Ablauf in der Vergangenheit |
| Persönliche Tokens (ohne Umfang) | jeder Lauf | löscht nach Ablauf sofort |
| API-Zugänge mit Umfang | jeder Lauf | löscht 30 Tage nach Ablauf |
| Anmeldeversuche | jeder Lauf | löscht Einträge älter als 30 Tage |
| Dateiablage | jeder Lauf; Abgleich Platte/Datenbank höchstens alle 12 Stunden; Temp-Reste älter als 6 Stunden | löscht Uploads ohne Anhang nach 24 Stunden und weich gelöschte Dateien nach 30 Tagen endgültig |
| Schüler-Dokumente | jeder Lauf | löscht Dokumente älter als `SM_STUDENT_DOCS_RETENTION_DAYS` (400 Tage) samt Datei; höchstens 5000 je Lauf; 0 = aus |
| Formular-Erinnerungen | jeder Lauf | erinnert Prüfende an offene Einreichungen, wenn die Vorlage eine Erinnerungsfrist (Tage) hat; danach erneut nach derselben Zeit |
| Formular-Aufbewahrung | jeder Lauf | löscht abgeschlossene Einreichungen älter als die Alters-Frist (400 Tage); höchstens 5000 je Lauf |
| Kontakt-Codes und Rate-Zeilen | jeder Lauf | löscht 1 Stunde nach Ablauf |
| Test-Postausgang | jeder Lauf | löscht Einträge älter als 24 Stunden |
| Zugangsbrief-Stapel | jeder Lauf | löscht abgelaufene Stapel (Standard 60 Minuten) |
| Doppelsende-Schutz (`send_idempotency`) | jeder Lauf | löscht Zeilen älter als 24 Stunden |
| Benachrichtigungen: Erinnerungen | jeder Lauf | Fristerinnerungen und Attest-Erinnerungen |
| Benachrichtigungen: zurückgestellte Mails | jeder Lauf | versendet nach Ende der Ruhezeit |
| Benachrichtigungen: Tageszusammenfassung | einmal pro Tag, frühestens 7:00 Uhr Ortszeit | fasst ungelesene Benachrichtigungen zusammen |
| Benachrichtigungen: Aufräumen | jeder Lauf | löscht Benachrichtigungen älter als die Aufbewahrung (Standard 90 Tage; 7 bis 730) |
| Kursraum-Papierkorb | jeder Lauf | löscht endgültig nach `trash_retention_days` (Standard 30 Tage) |
| Fehlerprotokoll | jeder Lauf | löscht älter als 30 Tage und alles über 1000 Zeilen |
| Löschkonzept | jeder Lauf | Abgleich der Warteliste, Fristlöschung (nur bei `auto_purge` = 1), Alters-Fristen, Audit-Frist (365 Tage), Löschprotokoll-Frist (1095 Tage); Einzelheiten DAT |
| Automatische App-Sicherung | alle `SM_AUTO_BACKUP_HOURS` (0 = aus) | Sicherung und Rotation auf `SM_BACKUP_KEEP` |
| Zeitgesteuert: Ferien-Automatik | 30 Sekunden nach Start, dann täglich | prüft das laufende und das nächste Schuljahr; bei Fehlern nur Protokoll, Neuversuch nach einer Stunde; Details STA |
| Auto-Planer | nach `SM_AUTOPLAN_DELAY` Sekunden Ruhe | siehe STP |
| Postfach-Abruf | alle `SM_MAIL_SYNC_MINUTES` (5) | siehe NAC |
| Lizenzprüfung | Start, `SM_LICENSE_CHECK_HOURS`, Ping | siehe Kap. 12 |

Abnahme: Je Zeile ein Test mit Zeitmanipulation: z. B. Anmeldeversuch von 31 Tagen → nach dem Lauf weg, 29 Tage → bleibt; hochgeladene Datei ohne Anhang nach 25 Stunden → gelöscht; weich gelöschte Datei nach 31 Tagen → endgültig weg, nach 29 Tagen nicht; 5001 Schüler-Dokumente über Frist → nach einem Lauf 5000 gelöscht.

**BET-070** · P2 · Status: offen · Postfach-Aufbewahrung als eigene Wartungsstufe
Ist-Befund: Die Aufbewahrungsfrist des Postfachs (Nachrichten älter als `messaging_retention_days`, Standard 365 Tage, 0 = nie, ausgenommen offen gemeldete; danach leere Unterhaltungen, Entwürfe und abgeschlossene Meldungen älter als die Frist; Ende abgelaufener Postfach-Sperren) läuft nicht im Hauptlauf, sondern als Notbehelf beim Abruf des Ungelesen-Zählers, höchstens alle 6 Stunden. Neubau: eigene Stufe im Hauptlauf.
Abnahme: Eine Nachricht von 366 Tagen ist nach dem nächsten Wartungslauf gelöscht, ohne dass ein Nutzer den Ungelesen-Zähler abruft; eine offen gemeldete Nachricht bleibt.

---

## 11. Dateien, Virenscan, Kontingente (Betriebsseite)

**BET-071** · P1 · Status: Ist · Virenscan der Uploads
Optionaler ClamAV-Daemon (Profil `antivirus`): `SM_CLAMAV_HOST` auf den Dienstnamen des Scanners, `SM_CLAMAV_REQUIRED=1` empfohlen, sobald der Scanner stabil läuft (dann HTTP 503 für Uploads, solange der Scanner nicht erreichbar ist; bei 0 werden Dateien „ungeprüft angenommen“ und ein Protokollhinweis „Virenscan fehlgeschlagen“ geschrieben). Der erste Start lädt Signaturen (einige Minuten bis „healthy“), braucht 1,5 bis 3 GB RAM; Signaturen aktualisiert der Scanner selbst über das Netz `egress`. Zeitlimit je Scan `SM_CLAMAV_TIMEOUT` (30 Sekunden); Scan-Durchsatz etwa 20 bis 60 MB/s. Ohne Container: Scanner-Daemon mit TCP-Port 3310 auf 127.0.0.1. Test: Datei mit der EICAR-Testzeichenkette hochladen → Meldung „Die Datei wurde vom Virenscanner als gefährlich erkannt und abgelehnt“ und Audit-Eintrag `file.virus`; blockierte Uploads erzeugen `file.blocked`.
Abnahme: EICAR-Upload → abgelehnt mit genau dieser Meldung und Audit-Eintrag `file.virus`; Scanner gestoppt + `SM_CLAMAV_REQUIRED=1` → Upload 503; mit `0` → Upload angenommen und Log „ungeprüft angenommen“.

**BET-072** · P1 · Status: Ist · Upload-Grenzen und Kontingente im Betrieb
Hochgeladene Dateien liegen verschlüsselt unter `SM_FILES_DIR` (eigener Datenträger möglich; dann im Backup mitsichern). Grenzen: `SM_UPLOAD_MAX_MB` 25; Kontingente `SM_QUOTA_MB_STAFF` 2000 (0 = unbegrenzt), `SM_QUOTA_MB_STUDENT` 200; Chat-Bilder (verschlüsselte Blobs in der Datenbank, nicht im Dateikontingent) `SM_CHAT_QUOTA_MB_STAFF` 500, `SM_CHAT_QUOTA_MB_STUDENT` 100 (auch Eltern), `SM_CHAT_QUOTA_MB_CHAT` 1000 je Chat (alle Mitglieder zusammen), `SM_CHAT_UPLOADS_PER_10MIN` 30. Wer voll ist, sieht „Ihr Platz für Chat-Bilder ist voll …“; Platz entsteht durch Löschen der Nachricht. Obergrenze der Datenbank bei 2.500 Schüler/innen: Summe der Chat-Kontingente etwa 350 GB im ungünstigsten Fall (ohne Eltern-Konten), praktisch weit darunter. Dateien: Allowlist und Magic-Byte-Prüfung, aktive Inhalte blockiert; Verfahren in DAT/SIC.
Abnahme: Upload über `SM_UPLOAD_MAX_MB` → abgelehnt; Konto mit vollem Dateikontingent → Upload abgelehnt, nach dem Löschen einer Datei wieder möglich; 31. Chat-Bild-Upload innerhalb von 10 Minuten → abgelehnt; Variable auf 0 → unbegrenzt.

---

## 12. Lizenzmodell (Schul-Instanz und Protokoll mit dem Anbieter)

Kap. 12 beschreibt die Seite der Schul-Instanz und das Protokoll zum Anbieter. Die Anbieter-Seite (Lizenzserver, Portal, Schlüsselverwaltung) steht in Kap. 13, Zahlungen und Tarife in Kap. 14, Updates in Kap. 15. Konfigurationsvariablen der Instanz: Kap. 3 (`SM_LICENSE_*`). Rechte-Name: `license.manage` (Administration und Schulleitung).

**BET-073** · P0 · Status: Ist · Lizenzpflicht und Abo-Modell
Im Echtbetrieb läuft jede Instanz nur mit gültiger Lizenz des Anbieters. Wunsch des Betreibers (12.10.2026): die Software läuft auf Schul-Servern nur mit Lizenz, „damit ich auch wirklich Geld dafür verlangen kann“. Entscheidung vom 16.10.2026 (überstimmt die frühere Lizenzdatei): Abo-Modell. „wenn die Lizenz nicht mehr auf meinem Server registriert wurde, nicht mehr anerkannt wird, dann sperrt der Server“; die Lizenz als Datei mit Ablaufdatum war falsch („die lizens ist nicht das was ich meinte“) und ist verworfen (ebenso die frühere Fassung „Schreibsperre ohne Lizenz, Kontenzahl nach Lizenz“). Folgen:
- Es gibt kein Ablaufdatum im Schlüssel und keines in der Instanz. Status, „Abo aktiv bis“, Grenzen und Sperren steuert ausschließlich der Lizenzserver des Anbieters.
- Ein Schlüssel je Server; eine Schule kann mehrere Server haben (BET-091).
- Eine frische Instanz ohne Schlüssel zeigt vor allem anderen die Seite „Lizenz eingeben, um fortzufahren“ (Begrüßungsseite).
- Kaufablauf (Wortlaut): „wenn die jetzt das Abo kaufen schicke ich denen eine Lizenz und einen Admin Zugang mit einem einmaligen Key also mit einem einmaligen Passwort“. Die Schule erhält Schlüssel, Administrationszugang mit Einmalpasswort (Passwortwechsel beim ersten Anmelden, BET-038) und eine Schulanleitung (Lizenzpaket, BET-111).
- Im Modus `production` ist die Lizenzprüfung nicht abschaltbar (BET-082).
Abnahme: Instanz im Modus `production` ohne Schlüssel → jede Seite außer Begrüßungsseite und Anmeldung zeigt die Lizenz-Eingabe; nach Eintrag eines gültigen Schlüssels ist die Instanz ohne Neustart voll nutzbar; in der Instanz gibt es kein Eingabefeld und keine Datei mit einem Ablaufdatum, das Abo-Ende kommt nur aus der signierten Anbieter-Antwort.

**BET-074** · P0 · Status: Ist · Schlüsselformat und Eingabeprüfung
Ein Lizenzschlüssel hat das Format `SPUL-XXXX-XXXX-XXXX-XXXX` (Präfix `SPUL` ist eine feste technische Konstante, getrennt vom konfigurierbaren Produktnamen).

| Bestandteil | Wert |
|---|---|
| Nutzzeichen | 16 (15 zufällig + 1 Prüfziffer), dargestellt in vier Gruppen zu 4 Zeichen mit Bindestrich |
| Alphabet | 31 Zeichen: Ziffern 2 bis 9, Buchstaben A bis Z ohne I, L, O (ohne 0 und 1, verwechslungsarm) |
| Prüfziffer | Summe aus (Position + 1) × Wert des Zeichens über die 15 Zufallszeichen, Rest modulo 31, auf das Alphabet abgebildet; erkennt Tippfehler |
| Eingabe | Groß-/Kleinschreibung, Leerzeichen und Striche werden ignoriert |
| Entropie | 15 × log2(31) ≈ 74 Bit (berechnet) |

Ein Schlüssel ohne gültiges Präfix, ohne 16 Nutzzeichen oder mit falscher Prüfziffer wird sofort abgewiesen, ohne Netzaufruf, mit der Meldung „Der Lizenzschlüssel ist nicht korrekt. Bitte prüfen Sie die Eingabe auf Tippfehler (Aufbau: SPUL-XXXX-XXXX-XXXX-XXXX).“ Echte Schlüssel stehen nie in Dokumenten, Protokollen oder Tests.
Abnahme: 1.000 erzeugte Schlüssel enthalten nie die Zeichen 0, 1, I, L, O und bestehen die Prüfziffer; ein Schlüssel mit einem getauschten Zeichen → Meldung wie oben, im Netzmitschnitt keine Anfrage; Eingabe in Kleinbuchstaben mit Leerzeichen statt Strichen wird akzeptiert.

**BET-075** · P0 · Status: Ist · Schlüssel eintragen (Aktivierung)
Wege: Seite `/lizenz` (Recht `license.manage`), Begrüßungsseite einer frischen Instanz, Schnittstellen `GET /api/v1/license` (Stand), `PUT /api/v1/license` (Schlüssel hinterlegen), `POST /api/v1/license/check` (jetzt beim Anbieter prüfen); alle verlangen `license.manage`. Im gesperrten Zustand bleibt `/lizenz` für Konten mit `license.manage` offen (Wortlaut: „eine option als admin also der oberste account der die schule leiter die lizens wieder irgendwo eingeben kann“).

| Schritt | Regel | Fehlerfall |
|---|---|---|
| 1 | Eingabe normalisieren und prüfen (BET-074) | Meldung ohne Netzaufruf |
| 2 | Der Prüfschlüssel des Anbieters muss eingebaut sein | „In dieser Installation ist kein Prüfschlüssel des Anbieters eingerichtet.“ |
| 3 | Aktivierung beim Anbieter: Schlüssel, Instanz-ID, eigene Adresse (max. 300 Zeichen), Version (max. 40 Zeichen), Anzahl Schüler/innen und aktive Konten, Nonce (32 Hexzeichen); Zeitlimit 15 Sekunden | „Der Lizenzserver ist nicht erreichbar“ |
| 4 | Antwort prüfen: Signatur, Nonce, Instanz-ID, letzte 4 Zeichen des Schlüssels | „nicht korrekt signiert“ bzw. „passt nicht zur Anfrage“ |
| 5 | Antwort-Status `unknown`, `cancelled` oder `bound_elsewhere` | Meldung aus BET-089; Schlüssel wird nicht gespeichert |
| 6 | Schlüssel und Aktivierungszeit speichern; Sperrgeheimnis übernehmen; vorhandene Sperre aufheben und mitgelieferten Sperrbefehl anwenden; Token, Zeitpunkte speichern | – |
| 7 | Benachrichtigungen prüfen, Stand neu anzeigen | – |

Eine pausierte oder abgelaufene Schule wird beim Eintragen angenommen; die Stufe zeigt dann Kulanz oder Sperre.
Abnahme: Gültiger Schlüssel → Stufe `valid` und Eintrag im Datenordner; Lizenzserver ausgeschaltet → Meldung nach höchstens 15 Sekunden, nichts gespeichert; Antwort mit verändertem Zeichen → „nicht korrekt signiert“, nichts gespeichert; Schlüssel einer gekündigten oder an eine andere Instanz gebundenen Schule → Meldung, nichts gespeichert; Lehrkraft ruft `PUT /api/v1/license` → 403; Administration trägt im Zustand `locked` einen gültigen Schlüssel ein → sofort frei.

**BET-076** · P0 · Status: Ist · Bindung an eine Instanz, Instanz-ID, Zustandsdateien
Die erste Aktivierung bindet den Schlüssel an die Instanz („Erstbindung durch Admin-Eingabe“). Ein zweiter Server mit demselben Schlüssel wird abgelehnt (`bound_elsewhere`). Die Instanz-ID (24 Hexzeichen) wird lokal zufällig erzeugt. Im Datenordner der Instanz liegen zwei Dateien, die nicht gelöscht werden dürfen:

| Datei | Inhalt | Übertragung |
|---|---|---|
| Schlüssel-Datei | eingetragener Schlüssel, Aktivierungszeit | Schlüssel bei jeder Anfrage |
| Zustandsdatei | Instanz-ID, letztes signiertes Ergebnis (Token), Sperrgeheimnis, Sperrbefehl (`hard_lock`), letzter Fehler, Zeitpunkte des letzten Versuchs und der letzten ausführlichen Prüfung | Instanz-ID bei jeder Anfrage; Sperrgeheimnis nie; Token nie |

Serverumzug: der Anbieter löst die Bindung („Bindung lösen“), der neue Server trägt den Schlüssel ein (oder die Zustandsdatei wird mit Instanz-ID übernommen). Neu ausstellen macht den alten Schlüssel sofort ungültig; die Instanz muss den neuen eintragen. Verlust der Zustandsdatei erzeugt eine neue Instanz-ID; der Schlüssel gilt dann als an eine andere Installation gebunden, bis der Anbieter die Bindung löst. Bei mehreren Knoten hat jeder Knoten eigenen Schlüssel, eigene Instanz-ID und eigenen Datenordner (BET-164).
Abnahme: Zwei Instanzen, derselbe Schlüssel → die zweite zeigt „Der Schlüssel ist an eine andere Installation gebunden“ (beim Eintragen mit Hinweis auf die Lösung der Bindung durch den Anbieter); Zustandsdatei löschen und neu starten → neue Instanz-ID, Stufe `locked`; nach „Bindung lösen“ im Portal und erneutem Eintragen → wieder `valid`; die Datenordner-Anleitung nennt beide Dateien als „nicht löschen“.

**BET-077** · P0 · Status: offen · Sperrzustand manipulationssicher speichern, Wiederanlauf
Ist-Befund: Der Sperrbefehl liegt ungeschützt in der Zustandsdatei; wird er dort entfernt, gilt die Instanz bis zum nächsten Kontakt (höchstens 15 Minuten) als frei. Das Sperrgeheimnis wird nur bei der Aktivierung ausgeliefert und lässt sich nicht erneut abholen. Neubau:
- Sperrzustand, Token und Instanz-Bindung werden signiert oder mit einem an die Instanz gebundenen Schlüssel gesichert gespeichert; eine veränderte oder gelöschte Zustandsdatei führt zur Stufe `locked` (Grund `unconfirmed`), nie zu „frei“.
- Ein verlorenes Sperrgeheimnis wird durch „Bindung lösen“ und erneutes Eintragen ersetzt (neues Geheimnis); der Ablauf steht in der Betreiber-Anleitung.
Abnahme: Test: Sperrbefehl gespeichert, dann Sperrbefehl in der Zustandsdatei entfernt und Instanz neu gestartet → die Instanz bleibt gesperrt (kein freies Zeitfenster, auch nicht bis zum nächsten Ping); veränderte Zustandsdatei → `locked` mit Grund `unconfirmed` und Protokollzeile „Zustandsdatei beschädigt“.

**BET-078** · P0 · Status: Ist · Prüfrhythmus und übertragene Angaben
Die Instanz prüft beim Start, danach alle 24 Stunden (`SM_LICENSE_CHECK_HOURS`, Mindestwert 1) ausführlich (`check`), nach Fehlern stündlich, zusätzlich alle 15 Minuten kurz (`ping`, `SM_LICENSE_PING_MINUTES`, 0 = aus; ohne Datenbankzugriff), damit eine Sofortsperre zeitnah wirkt. Zeitlimit je Anfrage 15 Sekunden. Die berechnete Stufe wird 30 Sekunden zwischengespeichert und neu berechnet, wenn sich Dateien, Tag oder Prüfschlüssel ändern.

| Angabe | Wann | Hinweis |
|---|---|---|
| Schlüssel, Instanz-ID | jede Anfrage | |
| Adresse der Instanz (max. 300 Zeichen), Version (max. 40 Zeichen) | jede Anfrage | Anbieter speichert beides |
| Nonce (32 Hexzeichen, zufällig) | jede Anfrage | Antwort muss dasselbe Nonce tragen |
| Anzahl Schüler/innen, Anzahl aktiver Konten | Eintragen und ausführliche Prüfung | beim Ping nicht; der Anbieter behält den letzten Wert (bis 24 Stunden alt) |

Es werden nie Namen oder Inhalte übertragen. Neubau: Schlägt die Zählung fehl, werden nicht still leere Werte gesendet; die Statusseite `/betrieb` zeigt „Zählung der Lizenzangaben fehlgeschlagen“ als Warnung.
Abnahme: Start mit erreichbarem Lizenzserver → im Verlauf des Anbieters ein `check`-Eintrag mit Version und Zählern, danach `ping`-Anfragen ohne Verlaufseintrag; Netz getrennt → nächster Versuch nach 1 Stunde; bei fehlgeschlagener Zählung erscheint die Warnung auf `/betrieb`, die Anfrage trägt keine Namen.

**BET-079** · P0 · Status: Ist · Signierte Antworten und Echtheitsprüfung
Alle Antworten des Anbieters sind HTTP 200 der Form `{"result": …, "signature": …}`; Fehler stehen im Ergebnis, nicht im Statuscode. Signatur: Ed25519 über die kanonische Form des Ergebnisses (JSON mit sortierten Schlüsseln, ohne Leerzeichen, UTF-8, Zeichen nicht maskiert), Base64. Der öffentliche Prüfschlüssel des Anbieters ist fest in die Instanz eingebaut (im Modus `production` nicht überschreibbar); der private Schlüssel verlässt den Anbieter-Server nie. Die Instanz akzeptiert eine Antwort nur, wenn Signatur, Nonce (Echo der Anfrage), Instanz-ID und letzte 4 Zeichen des Schlüssels passen. Gefälschte, unsignierte oder falsch gebundene Antworten zählen wie „Anbieter nicht erreichbar“; ein gespeichertes Token ist nur mit passender Signatur, Instanz-ID und Schlüsselendung gültig. Ein Wiedereinspielen einer früheren Antwort wirkt nicht (andere Nonce). Feldliste der Antwort: BET-099.
Abnahme: Antwort mit einem veränderten Zeichen → verworfen, Fehler gemerkt, Stufe unverändert; Antwort mit fremdem Nonce oder fremder Instanz-ID → verworfen; eine Instanz in `production` lässt sich nicht auf einen fremden Prüfschlüssel oder eine fremde Lizenzserver-Adresse umstellen.

**BET-080** · P0 · Status: Ist · Ausgehende Verbindung zum Lizenzserver
Die Instanz verbindet sich nur mit der eingebauten Lizenzserver-Adresse (`<anbieter-adresse>`; in Entwicklung/Demo/Test per `SM_LICENSE_SERVER`, lokale Ziele nur mit `SM_OUTBOUND_ALLOW`). Der Schutz ausgehender Ziele gilt auch hier: nur öffentliche Adressen nach Auflösung aller DNS-Einträge (Loopback, Link-Local, private Bereiche, Multicast und eigene Container-Namen abgewiesen), Verbindung an die geprüfte Adresse gebunden, keine Weiterleitungen, Antwortinhalte nie in Fehlertexten, Port fest. Die Anbieter-Adresse steht nur an einer Stelle der Software und ist dort überschreibbar; ohne Überschreibung gilt der Platzhalter `example.org`.
Abnahme: Test mit einer Lizenzserver-Adresse, die auf eine private IP auflöst → Verbindung abgewiesen; Weiterleitung (301) der Antwort → nicht verfolgt; eine Suche im Quelltext findet die echte Anbieter-Adresse an genau einer Stelle (Test bei jedem Lauf).

**BET-081** · P0 · Status: offen · Lizenzserver in den Datenschutzunterlagen
Die Datenschutzvorlagen (Verzeichnis der Verarbeitungstätigkeiten, Datenschutzhinweise, technisch-organisatorische Maßnahmen) nennen den Lizenzserver als Empfänger und beschreiben die übertragenen Angaben (BET-078). Befund der Sicherheitsprüfung (P4): „Lizenzserver fehlt in Vorlage“.
Abnahme: Die ausgelieferten Vorlagen enthalten einen Absatz „Lizenzserver des Anbieters“ mit Zweck, Datenkategorien (Schlüssel, Instanz-ID, Adresse, Version, Zähler) und Speicherdauer beim Anbieter (BET-106); ein Dokumententest findet das Stichwort in allen drei Vorlagen.

**BET-082** · P0 · Status: Ist · Stufen, Durchsetzung und Wirkung
Durchsetzung: im Modus `production` immer; sonst nur mit `SM_LICENSE_ENFORCE=1` (Standard aus). Ohne Durchsetzung werden Stufe und Grund berechnet und angezeigt, aber nicht erzwungen.

| Stufe | Bedeutung | Wirkung (mit Durchsetzung) |
|---|---|---|
| `valid` | Lizenz gültig | alles möglich |
| `warning` | Unterstufe von `valid`: Abo endet in 0 bis 30 Tagen, oder Lizenzserver nicht erreichbar bei noch gültiger Bestätigung | Banner; keine Einschränkung |
| `grace` | Kulanzzeit | nur lesen (`read_only`): lesende Anfragen 200, schreibende 403 |
| `locked` | gesperrt | API und Oberfläche für alle gesperrt (403, Kennung `license_locked`); offen bleiben Anmeldung, Abmeldung und die Lizenzseite für Konten mit `license.manage` sowie `/healthz`, `/healthz/ready`, `/api/v1/version` |

Die strengste Ursache gewinnt („locked“ schlägt „grace“).
Abnahme: Mit `SM_MODE=production` und `SM_LICENSE_ENFORCE=0` → Durchsetzung bleibt wirksam; in `development` ohne Durchsetzung erscheint bei Stufe `locked` nur die Anzeige, Schreiben funktioniert; Stufe `grace`: `GET /api/v1/me/week` 200, `POST` auf eine beliebige Schreib-Route 403; Stufe `locked`: dieselben Routen 403 `license_locked`, `/healthz` 200.

**BET-083** · P0 · Status: Ist · Gründe und Fristen
Fristen kommen aus der Antwort des Anbieters (Feld `grace_days`), sonst aus `SM_LICENSE_GRACE_DAYS` (Standard 14 Tage).

| Grund | Auslöser | Stufe | Kulanz (nur lesen) | danach |
|---|---|---|---|---|
| `missing` | kein Schlüssel eingetragen | `locked` | – | – |
| `unconfirmed` | kein gültiges signiertes Token (noch nicht bestätigt; Signatur, Instanz oder Schlüsselendung passen nicht) | `locked` | – | – |
| `blocked` | gültiger Sperrbefehl gespeichert (Sofortsperre) | `locked` | keine | aufgehoben durch `unlock` beim nächsten Kontakt |
| `cancelled` | Schule gekündigt | `locked` | keine | – |
| `unknown` | Schlüssel dem Anbieter unbekannt (z. B. nach Neuausstellung) | `locked` | keine | – |
| `unbound` | Bindung gelöst (Serverumzug, Abbau) | `locked` | keine | Schlüssel neu eintragen |
| `bound` | Schlüssel an andere Installation gebunden | `locked` | keine | – |
| `paused` | Schule pausiert | `grace` | `grace_days` ab Beginn der Pause | dann `locked` |
| `expired` | „Abo aktiv bis“ überschritten | `grace` | `grace_days` ab dem Tag nach Abo-Ende | dann `locked` (ab Tag 15 nach Abo-Ende) |
| `offline` | Bestätigungsfrist überschritten (BET-085) | `grace` | `grace_days` ab Ende der Bestätigungsfrist | dann `locked` |

`expired` und `offline` laufen unabhängig; die strengere Stufe gilt. Zuordnung Anbieter-Status zu Grund: `paused`→`paused`, `cancelled`→`cancelled`, `unknown`→`unknown`, `unbound`→`unbound`, `bound_elsewhere`→`bound`, alles andere→`unknown`.
Abnahme: Je Zeile ein Test mit Zeitmanipulation: Abo-Ende gestern → `grace`, Grund `expired`, Ende der Kulanz in 14 Tagen minus 1; Abo-Ende vor 15 Tagen → `locked`; Pause vor 10 Tagen → `grace`, vor 15 Tagen → `locked`; Kündigung → sofort `locked` ohne Kulanz; `grace_days` 3 in der Antwort → Kulanz 3 Tage.

**BET-084** · P0 · Status: Ist · Entscheidungsfolge der Stufe
Die Stufe wird in dieser Reihenfolge ermittelt, die erste zutreffende Zeile entscheidet:

| Nr. | Prüfung | Ergebnis |
|---|---|---|
| 1 | kein Schlüssel | `locked`, `missing` |
| 2 | kein gültiges Token für Schlüssel und Instanz | `locked`, `unconfirmed` |
| 3 | Sperrbefehl gespeichert | `locked`, `blocked`, Text des Anbieters |
| 4 | Anbieter-Status `paused` | `grace` bis Pausenbeginn + `grace_days`, danach `locked` |
| 5 | Anbieter-Status weder `active` noch `expired` | `locked`, Grund nach BET-083 |
| 6 | Abo-Ende überschritten | `grace` (`expired`) bis Abo-Ende + `grace_days`, danach `locked` |
| 7 | Bestätigungsfrist überschritten | `grace` (`offline`) bis Ende der Frist + `grace_days`, danach `locked` |
| 8 | Bestätigungsfrist gültig, aber letzter Fehler gespeichert | `valid` mit Warnung „Lizenzserver nicht erreichbar, letzte Bestätigung gilt noch N Tage“ |
| 9 | Abo endet in 0 bis 30 Tagen | `warning`, Warnstufe 30, 14, 7 oder 1 |
| 10 | sonst | `valid` |

Übergänge: Eintragen → `valid`; `valid`/`warning` → `grace` bei Abo-Ende, abgelaufener Bestätigungsfrist oder Pause; `grace` → `valid` bei neuer gültiger Bestätigung (Verlängerung, Fortsetzen, Netz wieder da); `grace` → `locked` am Ende der Kulanz; jede Stufe → `locked` sofort bei Sofortsperre, Kündigung, unbekanntem Schlüssel, gelöster oder fremder Bindung; `locked` → `valid` durch Entsperren oder gültige Bestätigung nach Verlängerung/Neubindung.
Abnahme: Je Nummer ein Test; Kombination „Abo abgelaufen und offline“ ergibt die strengere der beiden; Verlängerung beim Anbieter → beim nächsten Ping (≤ 15 Minuten) wechselt die Instanz von `grace` nach `valid`.

**BET-085** · P0 · Status: Ist · Offline-Regel (Anbieter nicht erreichbar)
Entscheidung des Betreibers (16.10.2026 14:38): „wenn der Server keine Verbindung mehr hat, dann soll er nach sieben Tagen offline gehen“. Die frühere Aussage „30 Tage“ ist überstimmt. Jede gültige Antwort setzt `confirmed_until` = Antwortzeit + 7 Tage (Anbieter-Variable `LZ_CONFIRM_DAYS`, Standard 7). Bis dahin läuft die Instanz normal, mit Warnung „Der Lizenzserver ist nicht erreichbar. Die letzte Bestätigung gilt noch N Tag(e).“ Danach `grace` (Grund `offline`) 14 Tage nur lesen mit Banner, danach `locked`; bei Standardwerten rund 21 Tage ohne Kontakt. Das Fenster fängt Strom- oder Internetausfälle des Anbieters ab (der Anbieter-Server ist ein Ausfallpunkt, BET-210).
Abnahme: Zeitmanipulation: letzter Kontakt vor 6 Tagen → `valid` mit Warnung (N = 1); vor 8 Tagen → `grace`, schreibende Anfrage 403; vor 22 Tagen → `locked`; Netz kommt zurück → beim nächsten Versuch wieder `valid`.

**BET-086** · P0 · Status: Ist · Sofortsperre auf der Instanz
Wunsch (16.10.2026): „wenn zum Beispiel die Schule sagt, wir zahlen nicht mehr … muss ich den sofort sperren“; „es gibt einen bestimmten Lizenzkey und der blockiert sofort“. Ablauf: Der Anbieter sperrt eine Schule (alle Server) oder einen einzelnen Server mit Text; die Instanz erhält den Sperrbefehl beim nächsten Kontakt, spätestens nach 15 Minuten (Ping). Der Befehl wird nur an die gebundene Instanz geliefert und trägt einen Prüfcode (HMAC-SHA256 mit dem Sperrgeheimnis über Befehl, Text, Zeitpunkt, Nonce der Anfrage, Instanz-ID und letzte 4 Zeichen des Schlüssels; Vergleich in konstanter Zeit). Ein Befehl einer anderen Schule oder Instanz, ein wiederholter Befehl (andere Nonce) oder ein Befehl mit ungültigem Prüfcode wirkt nicht und erzeugt eine Warnung im Protokoll. Ohne Sperrgeheimnis werden Sperrbefehle nicht geprüft (keine Sperre aus dem Anbieter möglich). Wirkung: `hard_lock` mit Text (max. 300 Zeichen), Stufe `locked`, Grund `blocked`, ohne Kulanz; Standardtext „Die Lizenz wurde vom Anbieter gesperrt.“ Aufheben: Befehl `unlock`, bei jedem Kontakt für nicht gesperrte Schulen mitgeliefert.
Abnahme: Sperre im Portal → Instanz zeigt innerhalb von 15 Minuten die Sperrseite mit dem Text; derselbe Befehl mit verändertem Text oder von einer zweiten Schule signiert → keine Wirkung, Warnung im Log; „Sperre aufheben“ im Portal → Instanz innerhalb von 15 Minuten wieder frei; Einzelsperre von Server 2 → Server 1 bleibt `valid`.

**BET-087** · P0 · Status: Ist · Sperre wirkt auf alle Schnittstellen, Wiedereintragen
Im Zustand `locked` liefern alle Seiten und alle Schnittstellen (Test über rund 500 Routen) für Konten ohne `license.manage` die Sperrseite bzw. 403 `license_locked`: „Die Lizenz dieser Schule ist abgelaufen – bitte wenden Sie sich an die Schulleitung“ (bei Sofortsperre: der Text des Anbieters). API-Zugänge (Token), Kalender-Abos und Live-Strom sind eingeschlossen. Ausnahmen (Zulassungsliste): Anmeldung, Abmeldung, Lizenzseite und Lizenz-Schnittstellen für `license.manage`, `/healthz`, `/healthz/ready`, `/api/v1/version`. Administration und Schulleitung können sich trotz Sperre anmelden und einen neuen Schlüssel eintragen; danach ist „alles sofort wieder frei“. Im Zustand `grace` zeigt eine Hinweisleiste allen Konten den Stand (Ende der Kulanz), die Vorwarnung betrifft nur Konten mit `license.manage` (BET-088).
Abnahme: Ein automatischer Test ruft alle im Routenverzeichnis geführten Routen im Zustand `locked` mit einem Lehrkraft-Konto auf: außer der Zulassungsliste alle 403 `license_locked`; mit Administrationskonto sind `/lizenz` und `PUT /api/v1/license` erreichbar, alle anderen Fachrouten 403; Eintrag eines gültigen Schlüssels → sofort alle Routen wieder 200; ein API-Zugangs-Token erhält in `locked` ebenfalls 403.

**BET-088** · P1 · Status: Ist · Vorwarnungen und Hinweise
Vorwarnung 30, 14, 7 und 1 Tag vor „Abo aktiv bis“ als Banner und Glocke für Konten mit `license.manage` (Administration, Schulleitung). Die Hinweisleiste der Kulanzzeit sehen alle Konten, die Vorwarnung nur Konten mit `license.manage`.

| Auslöser | Duplikat-Schlüssel | Titel (fester Text) |
|---|---|---|
| Restlaufzeit ≤ 30 Tage (Stufe 30), ≤ 14 (Stufe 14), ≤ 7 (Stufe 7), ≤ 1 (Stufe 1) | `warn:30`, `warn:14`, `warn:7`, `warn:1` | „Das Abo läuft in N Tag(en) ab“ |
| Abo endet heute | `warn:1` (Restlaufzeit 0) | „Das Abo läuft heute ab“ |
| Kulanzzeit beginnt | `grace:Grund:Ende` | „Lizenz nicht bestätigt – Daten nur noch lesbar“ |
| Sperre | `locked:Grund` | „Die Lizenz ist nicht mehr gültig – die Anwendung ist gesperrt“ |

Je Schlüssel und Stufe genau eine Meldung (Duplikat-Schutz über Schlüsselendung und Stufe); Link der Meldung ist die Lizenzseite; Empfänger sind alle Konten mit `license.manage`; Meldungen nur mit Durchsetzung und nicht bei fehlendem Schlüssel oder fehlender Bestätigung. Die Prüfschleife läuft alle 15 Minuten (oder im Ping-Intervall, mindestens alle 60 Sekunden).
Abnahme: Abo-Ende in 29 Tagen → eine Meldung `warn:30`, nach erneutem Prüflauf keine zweite; in 13 Tagen → zusätzlich `warn:14`; Abo-Ende heute → Titel „Das Abo läuft heute ab“; Konto ohne `license.manage` sieht keine Vorwarnung, in der Kulanzzeit aber die Hinweisleiste; ohne Durchsetzung (Entwicklung) keine Meldung.

**BET-089** · P1 · Status: Ist · Feste Meldungen der Lizenz
Texte (Anrede „Sie“, Datumsformat TT.MM.JJJJ):

| Lage | Text |
|---|---|
| kein Schlüssel | „Es ist noch kein Lizenzschlüssel eingetragen.“ |
| nicht bestätigt | „Die Lizenz wurde noch nicht vom Anbieter bestätigt.“ |
| pausiert | „Lizenz pausiert – bitte Anbieter kontaktieren.“ (mit Kulanz: „Bis zum TT.MM.JJJJ können Sie die Daten nur noch lesen.“) |
| gekündigt | „Die Lizenz wurde gekündigt.“ |
| unbekannt | „Der Lizenzschlüssel ist dem Anbieter nicht bekannt.“ |
| nicht gebunden | „Der Schlüssel ist nicht mehr an diese Installation gebunden – bitte tragen Sie ihn neu ein.“ |
| anderswo gebunden | „Der Schlüssel ist an eine andere Installation gebunden.“, beim Eintragen mit dem Zusatz, dass der Anbieter bei einem Serverumzug die Bindung löst |
| Abo abgelaufen | „Das Abo ist am TT.MM.JJJJ abgelaufen.“ (mit Kulanz: „… Bis zum TT.MM.JJJJ können Sie die Daten nur noch lesen; danach ist die Anwendung gesperrt.“) |
| offline | „Die Lizenz konnte seit N Tag(en) nicht bestätigt werden.“ (mit Kulanz-Ende) |
| Server nicht erreichbar, noch gültig | „Der Lizenzserver ist nicht erreichbar. Die letzte Bestätigung gilt noch N Tag(e).“ |
| Schüler/innen über Grenze | „Mehr Schüler/innen (N) als lizenziert (M).“ (nur Warnung) |
| Sofortsperre | Text des Anbieters, Standard „Die Lizenz wurde vom Anbieter gesperrt.“ |

Abnahme: Je Zeile ein Zustand; die Texte erscheinen wörtlich auf der Lizenzseite und (bei Sperre) auf der Sperrseite; ein Test vergleicht die Texte mit dieser Tabelle.

**BET-090** · P1 · Status: offen · Grenzen für Konten und Schüler/innen
Der Anbieter liefert `max_users` (aktive Konten) und `max_students` (Schüler/innen); leer bedeutet unbegrenzt. Ist-Befund: Die Schülergrenze ist nur eine Warnung (Meldung aus BET-089, keine Sperre). Für die Kontengrenze ist die Durchsetzung im Altbestand nicht nachgewiesen (`[unklar: ob das Anlegen von Konten über der Grenze verhindert wird]`); die frühe Fassung (12.10.2026) sah vor, dass sich die Kontenzahl nach der Lizenz richtet. Neubau: Das Anlegen oder Aktivieren eines Kontos über `max_users` hinaus wird abgelehnt (Meldung mit Grenze und aktueller Zahl); die Schülergrenze bleibt Warnung; die Lizenzseite zeigt Ist-Zahl und Grenze. `[unklar: Betreiber bestätigt, ob die Kontengrenze hart oder nur Warnung ist]`
Abnahme: `max_users` = 100 bei 100 aktiven Konten → Anlegen eines 101. Kontos wird mit Meldung abgelehnt (409), Deaktivieren eines Kontos macht einen Platz frei; `max_students` = 50 bei 51 Schüler/innen → Warnung „Mehr Schüler/innen (51) als lizenziert (50).“, kein Sperrzustand; leere Grenze → keine Prüfung.

**BET-091** · P1 · Status: Ist · Mehrere Server je Schule
Wunsch (16.10.2026): „es kann auch sein, dass die 2 Server haben oder 5 oder 100“; die Schule meldet die Serverzahl, der Anbieter legt die Lizenzen fest („am besten die kriegen dann zwei Lizenzen für jeden Server“), der Anbieter erkennt die Server einer Schule an derselben Gruppen-Kennung (`G-` plus 8 Hexzeichen). Die Schule hat eine gebuchte Serverzahl (1 bis 1000), jeder Server einen eigenen Schlüssel mit Bezeichnung (z. B. „Server Haus A“, max. 100 Zeichen). Die Antwort enthält die Liste aller Server der Schule (Bezeichnung, letzte 4 Zeichen, Zustand, Adresse, Version, letzte Prüfung, Markierung „dieser Server“), nie Instanz-ID oder Geheimnisse. Pause, Kündigung, Sofortsperre, Abo-Ende und Grenzen gelten schulweit für alle Server; zusätzlich lässt sich ein einzelner Server sperren, lösen oder umbenennen (gestohlener oder abgebauter Server). Mehr Schlüssel als gebucht nur nach ausdrücklicher Bestätigung (BET-101).
Abnahme: Schule mit 3 Servern → die Lizenzseite jedes Servers listet alle 3 mit eigenem Zustand und markiert den eigenen; Pause der Schule → alle 3 wechseln nach `grace`; Einzelsperre von Server 2 → nur Server 2 `locked`; die Antwort enthält keine Instanz-ID anderer Server.

**BET-092** · P1 · Status: Ist · Lizenzseite `/lizenz`
Recht `license.manage`. Inhalt: Schlüssel maskiert (`SPUL-••••-••••-••••-XXXX`, nur letzte 4 Zeichen), Stufe und Grund mit Meldung (BET-089), „Abo aktiv bis“, Ende der Kulanz, Zeitpunkt der letzten Prüfung und Bestätigung („gilt bis“), Schulname und Gruppen-Kennung, Liste der Server der Schule (BET-091), Grenzen mit Ist-Zahlen, Hinweis auf ein freigegebenes Update. Aktionen: Schlüssel eintragen oder ersetzen, „Jetzt prüfen“. Erklärungen nur über Hilfe-Symbole, Anrede „Sie“. Im Altbestand prüften die Lizenzseiten noch das Recht `system.admin`; im Neubau gilt `license.manage` (Katalog). `[unklar: Feldliste der Seite im Altbestand nur teilweise belegt]`
Abnahme: Schulleitung und Administration sehen die Seite, Lehrkraft, Sekretariat und Planung erhalten 403 und sehen den Menüeintrag nicht; der Schlüssel erscheint nie im Klartext; „Jetzt prüfen“ aktualisiert „letzte Prüfung“ und zeigt bei Fehlern die Meldung aus BET-089.

**BET-093** · P1 · Status: offen · Audit der Lizenzereignisse
Backlog (W1-05): Die Lizenzprüfung fehlt im Audit. Zu protokollieren sind ohne Inhalte und ohne Schlüssel (nur letzte 4 Zeichen): Schlüssel eingetragen oder ersetzt (Konto), Stufenwechsel (z. B. `valid`→`grace`), Sofortsperre angewendet und aufgehoben, Bindung verloren, mehrere Prüfungen hintereinander fehlgeschlagen. Ereignisnamen legt der Neubau fest `[unklar]`.
Abnahme: Eintragen eines Schlüssels erzeugt eine Audit-Zeile mit Konto, Zeit und letzten 4 Zeichen, ohne vollständigen Schlüssel; der Wechsel `grace`→`locked` erzeugt eine Systemzeile ohne Konto; ein Audit-Export enthält nirgends einen vollständigen Schlüssel.

**BET-094** · P2 · Status: Ist · Entwicklungs- und Testbetrieb der Lizenz
Entwicklung und Demo sind lizenzfrei; die Prüfung wird mit `SM_LICENSE_ENFORCE=1` erzwungen, Testschlüsselpaar mit `SM_LICENSE_PUBKEY`, Testserver mit `SM_LICENSE_SERVER` (lokale Ziele zusätzlich über `SM_OUTBOUND_ALLOW`); in `production` wirken diese drei Variablen nicht (BET-006). Pflicht-Testmatrix mit lokalem Test-Lizenzserver und Testschlüsseln: Vorwarnung (30/14/7/1), Kulanzzeit, Sperre, Neueingabe, Sofortsperre und `unlock`, Offline 7/21 Tage, Bindung (zweiter Server), falscher Prüfschlüssel, gefälschte Antwort, Wartung ohne Netz. Stand Altbestand: 31 Tests in der Schul-App, 89 im Lizenzserver. Live-Test auf der Test-Instanz „neu“ (Schlüssel eintragen, Widerruf, Sperre prüfen, wieder freigeben; Sofortsperre im Portal innerhalb von 15 Minuten, Entsperren) steht aus.
Abnahme: Die Testmatrix läuft automatisch grün; der Live-Test ist mit Datum und Ergebnis dokumentiert (Sperre ≤ 15 Minuten nach Auslösung, Entsperren ≤ 15 Minuten); ein Test beweist, dass `SM_LICENSE_PUBKEY` in `production` ignoriert wird.

**BET-095** · P3 · Status: offen · Modulare Lizenz (Module ein- und ausschalten)
Backlog B-56 (Herkunft Marktvergleich „modulare Lizenz“): „Die Schule bezahlt und sieht nur die Module, die sie nutzt.“ Die Administration schaltet Module ein und aus (z. B. Kursräume, Postfach, Klassenbuch, Elternbriefe, Sprechtag, Noten, Buchung, Monitor); nicht gebuchte Module verschwinden aus Menü, Startseite und API (404); Ausschalten löscht keine Daten, Wiedereinschalten stellt sie wieder her; ein zentrales Modulverzeichnis liest den Modulstatus; die gebuchten Module liefert der Lizenzserver in der signierten Antwort `[Vorschlag, nicht bestätigt]`. Das Preismodell ist offen (BET-135).
Abnahme: Modul „Noten“ ausgeschaltet → Menü und Startseite ohne Noten, `GET` auf Noten-Routen 404, nach Wiedereinschalten sind die Daten wieder da; Lizenz ohne Modul „Postfach“ → Postfach-Routen 404 für alle Rollen, Daten unverändert.

---

## 13. Anbieter-Lizenzserver und Anbieter-Portal

Der Lizenzserver ist ein eigenständiger Dienst des Anbieters (eigener Container, eigene Datenbank, eigener Datenordner). Er bestätigt den Schul-Servern die Lizenz, verwaltet Schulen (Kunden), Server-Lizenzen, Tarife, Zahlungen und Update-Freigaben und enthält das Anbieter-Portal unter `/admin`. Kein Anbieter-Wert (Domain, Schlüssel, Zugangsdaten, Namen) steht in diesem Dokument; Platzhalter `<anbieter-adresse>`.

### 13.1 Lizenzserver

**BET-096** · P0 · Status: Ist · Lizenzserver als eigener Dienst, Schnittstellen
Eigener Container mit eigenem Datenvolumen (Standardport 8200, hinter Proxy mit `LZ_TRUST_PROXY=1`). Er teilt keine Daten oder Schlüssel mit einer Schul-Instanz.

| Pfad | Methode | Aufrufer | Zweck |
|---|---|---|---|
| `/api/v1/health` | GET | Überwachung | Lebenszeichen `{"ok": true}` |
| `/api/v1/activate` | POST | Schul-Instanz | Aktivierung und Bindung; einziger Ort des Sperrgeheimnisses |
| `/api/v1/check` | POST | Schul-Instanz (Start, alle 24 Stunden, nach Fehlern stündlich) | ausführliche Prüfung mit Zählern und Verlauf |
| `/api/v1/ping` | POST | Schul-Instanz (alle 15 Minuten) | leichte Statusabfrage ohne Verlauf und Zähler |
| `/api/v1/payments/webhook/{Anbieter}` | POST | Zahlungsanbieter | Zahlungseingang und Fehlschläge (Kap. 14) |
| `/api/v1/updates/poll` | POST | Update-Agent | Angebot oder Auftrag (Kap. 15) |
| `/api/v1/updates/download/{Version}` | GET | Update-Agent | Abbild-Datei |
| `/admin`, `/admin/login`, `/admin/schools`, `/admin/payments`, `/admin/payments/plans`, `/admin/payments/export.csv`, `/admin/updates` | GET/POST | Anbieter-Portal | Verwaltung (BET-107 ff.) |

Fehlercodes: 422 bei ungültigen Eingaben, 429 bei Überschreiten der Grenzen (BET-097), 400 bei ungültiger Webhook-Signatur oder unlesbarer Nachricht, 503 bei Webhook ohne eingerichtetes Geheimnis, 404 bei unbekanntem Zahlungsanbieter, 403 beim Download ohne gültige Lizenz. Die Datenbank wird beim Start ohne Datenverlust um Spalten ergänzt.
Abnahme: `GET /api/v1/health` → 200 `{"ok": true}`; `POST /api/v1/check` mit unbekanntem Schlüssel → HTTP 200 mit signiertem Ergebnis `unknown`; Webhook ohne Geheimnis → 503; Download ohne Lizenz → 403; ein Portscan zeigt außer dem Proxy keine offenen Ports des Lizenzservers.

**BET-097** · P0 · Status: Ist · Eingabegrenzen und Anfragebegrenzung

| Feld | Grenze |
|---|---|
| Schlüssel (Anfrage) | 10 bis 64 Zeichen |
| Instanz-ID | 1 bis 64 Zeichen |
| Adresse der Instanz | max. 300 Zeichen (gekürzt) |
| Version | max. 40 Zeichen |
| Schüler/innen, Konten | ganzzahlig, ≥ 0 |
| Nonce | 16 bis 64 Zeichen |
| Lizenz-API (`activate`, `check`, `ping` gemeinsam) | 60 Anfragen je 10 Minuten je Adresse, sonst 429 „Zu viele Anfragen“ |
| Update-API (`poll`, `download` gemeinsam) | 120 Anfragen je 10 Minuten je Adresse, sonst 429 |
| Adresse hinter Proxy | mit `LZ_TRUST_PROXY=1` die erste Adresse der Weiterleitungs-Kopfzeile, sonst die Verbindungsadresse |

Ungültige Eingaben liefern 422. Die Grenzen müssen auch mehrere Server hinter einer gemeinsamen Adresse (NAT) tragen: Ein Server erzeugt im Normalbetrieb weniger als 1 Lizenz-Anfrage je 10 Minuten (Ping alle 15 Minuten), bei offenem Update-Angebot bis zu 10 Update-Anfragen je 10 Minuten (Abfrage alle 60 Sekunden, BET-158).
Abnahme: 61 Anfragen in 10 Minuten von einer Adresse → die 61. liefert 429; Schlüssel mit 9 Zeichen → 422; Anfrage mit gefälschter Weiterleitungs-Kopfzeile bei `LZ_TRUST_PROXY=0` zählt auf die Verbindungsadresse.

**BET-098** · P0 · Status: Ist · Datenmodell des Lizenzservers
Datenbank: eine Datei im Datenordner (`LZ_DATA_DIR`, Standard `data`). Tabellen und Felder:

| Tabelle | Felder (Typ/Standard) |
|---|---|
| `schools` (Schule = Kunde) | `id`; `name` (200, Pflicht); `group_id` (24, eindeutig, `G-` + 8 Hex); `status` (12; `active`, `paused`, `cancelled`; Standard `active`); `status_changed_at`; `valid_until` (Datum, leer = unbegrenzt); `max_users`, `max_students` (leer = unbegrenzt); `servers_booked` (Standard 1); `blocked` (Standard nein), `block_text` (max. 300), `blocked_at`; `note` (500); `created_at` |
| `license_keys` (Server-Lizenz) | `id`; `school_id`; `key_hash` (64, eindeutig, SHA-256); `last4`; `key_enc` (verschlüsselter Klartext zur Anzeige, leer im Altbestand); `label` (100, Standard „Server N“); `note`; `created_at`; `bound_instance` (64), `bound_url` (300), `bound_at`; `lock_secret` (64 Hex); `blocked`, `block_text`, `blocked_at` (Einzelsperre); `last_check_at`, `last_ip` (64), `last_version` (40), `last_users`, `last_students` |
| `key_events` (Verlauf) | `id`; `school_id`; `key_id` (leer = Schulebene); `kind` (16: `check`, `activate`, `admin`, `payment`); `status` (20: Status oder Aktion, z. B. `active`, `paused`, `pause`, `block`, `key_issued`, `key_reissued`, `key_shown`, `invoiced`, `paid`, `failed`, `auto_paused`); `text` (500); `instance_id`, `url`, `ip`, `version`, `users` (nicht bei Ping); `created_at` |
| `plans`, `school_billing`, `payments` | Kap. 14 |
| `upd_releases`, `upd_school_settings`, `upd_rollouts`, `upd_appointments`, `upd_nodes`, `upd_events` | Kap. 15 |

Altbestand-Tabellen für Lizenzen (`licenses`, `checks`) werden nur noch gelesen (BET-117).
Abnahme: Eine frische Datenbank enthält alle Tabellen mit den genannten Standardwerten; `key_hash` ist eindeutig (zweiter gleicher Hash → Fehler); die Datenbank einer älteren Version wird beim Start ohne Datenverlust ergänzt (Test mit gespeichertem Altstand).

**BET-099** · P0 · Status: Ist · Status der Schule und signierte Antwort
Statusermittlung des Anbieters (erste zutreffende Zeile): 1 Schlüssel unbekannt → `unknown`; 2 Schule gekündigt → `cancelled`; 3 Schule pausiert → `paused`; 4 Instanz-ID angegeben und Schlüssel nicht gebunden → `unbound`; 5 an andere Instanz gebunden → `bound_elsewhere`; 6 heute nach „Abo aktiv bis“ → `expired`; 7 sonst `active`. Die Sofortsperre ist kein Status, sondern ein Kennzeichen (Sperrbefehl in der Antwort). Zustand eines Servers in der Übersicht (Reihenfolge): `blocked` (Server oder Schule gesperrt) → `unbound` → `paused`/`cancelled`/`expired` (Schulstatus) → `silent` (gebunden, aber über 2 Tage ohne Kontakt) → `active`. „Letzter Kontakt“ wird bei Antworten mit Status `active`, `expired`, `paused`, `cancelled` oder `unbound` für die gebundene Instanz gesetzt (auch bei Ping).

| Feld der Antwort | Inhalt | Nur an gebundene Instanz |
|---|---|---|
| `status`, `message`, `nonce`, `instance_id`, `checked_at`, `key_last4` | Status, fester Text, Echos, Serverzeit, letzte 4 Zeichen (bei unbekanntem Schlüssel leer) | nein |
| `licensee`, `group_id`, `server_label`, `valid_until`, `max_users`, `max_students`, `servers_booked`, `servers` | Schulname, Gruppen-Kennung, Server-Bezeichnung, Abo-Ende, Grenzen (leer = unbegrenzt), gebuchte Server, alle Server der Schule | ja |
| `grace_days` | Kulanztage (Standard 14) | nein |
| `since` | Beginn der Pause (nur bei `paused`) | nein |
| `confirmed_until` | Antwortzeit + 7 Tage (nur bei `active`, `expired`) | nein |
| `update` | Hinweis auf ein freigegebenes Update (nur bei `active`, `expired`) | nein |
| `lock` | Sperrbefehl (`lock`/`unlock`, Text, Zeitpunkt, Prüfcode); nur wenn ein Sperrgeheimnis existiert | ja |
| `lock_secret` | Sperrgeheimnis (64 Hex) | nur bei Aktivierung, nie bei Prüfung |

Abnahme: Je Statuszeile ein Test (z. B. Schule pausiert und Schlüssel nicht gebunden → `paused`); Antwort an eine fremde Instanz enthält weder `licensee` noch `servers` noch `lock`; `lock_secret` erscheint ausschließlich in der Antwort auf `activate`; der Servers-Zustand `silent` erscheint nach 3 Tagen ohne Kontakt, nicht nach 1 Tag.

**BET-100** · P0 · Status: Ist · Schlüsselerzeugung und -speicherung auf dem Lizenzserver
Schlüssel werden zufällig im Format von BET-074 erzeugt. Gespeichert werden der SHA-256-Hash (Grundlage der Prüfung, eindeutig) und die letzten 4 Zeichen; zusätzlich der Klartext verschlüsselt (Fernet: AES-128-CBC mit HMAC) ausschließlich zur Anzeige im Portal, die Anzeige erfolgt nur, wenn Entschlüsselung und Hash zusammenpassen. Der Datenschlüssel stammt aus `LZ_KEY_STORE_KEY`, sonst aus einer Datei im Datenordner (Rechte 0600, beim ersten Bedarf erzeugt); sein Verlust macht den Klartext unlesbar (Schlüssel bleiben gültig, Neuausstellung nötig). Anzeige-Maske: `SPUL-••••-••••-••••-XXXX`. Ursprung der Regel: Schlüssel waren zuerst nur als Hash gespeichert; auf Wunsch des Betreibers (16.10.2026 15:43) sind sie im Portal jederzeit anzeigbar und kopierbar (BET-114). Wer Datenbank und Datenschlüssel lesen kann, kann alle Schlüssel lesen: beide wie Geheimnisse behandeln und gemeinsam sichern (BET-105).
Abnahme: In der Datenbank steht kein Klartext-Schlüssel (Suche nach dem bekannten Testschlüssel → nur `key_enc`-Chiffretext und Hash); Datenschlüssel entfernt → Anzeige zeigt „Nicht gespeichert – neu ausstellen“, Prüfung der Schlüssel funktioniert weiter; Datenschlüssel-Datei hat Rechte 0600.

**BET-101** · P0 · Status: Ist · Lebenszyklus eines Server-Schlüssels

| Vorgang | Auslöser | Wirkung |
|---|---|---|
| Schule anlegen | Portal-Assistent oder `create-school` | Schule mit gebuchten Servern (Standard 1; 1 bis 1000); je Server ein Schlüssel „Server 1“, „Server 2“ …; Klartext wird bei der Anlage einmalig als frische Meldung angezeigt |
| Server ergänzen | `add-server` | nur bis zur gebuchten Anzahl; darüber nur mit `--force` bzw. Bestätigung im Portal |
| Aktivierung und Bindung | erstes `activate` | Instanz-ID und Adresse gebunden; neues Sperrgeheimnis (64 Hex) erzeugt und einmalig mitgeliefert |
| Adresse nachführen | `check`/`activate` mit geänderter Adresse | Adresse aktualisiert |
| Bindung lösen | `unbind` oder Portal | Bindung, Adresse und Sperrgeheimnis entfernt; Zustand `unbound` |
| Neu ausstellen | `reissue --yes` oder Portal (mit Bestätigung) | alter Schlüssel ungültig (Hash ersetzt), Bindung und Geheimnis entfernt; neuer Klartext angezeigt; die Instanz muss neu eintragen |
| Klartext anzeigen | `show-key` oder Portal | nur bei gespeichertem Klartext; Verlaufseintrag `key_shown` |
| Einzelsperre / aufheben | `server-block --text` / `server-unblock` | nur dieser Server; Sperrtext max. 300 Zeichen |
| Umbenennen | `label` | Bezeichnung max. 100 Zeichen |
| Verlauf | jede Änderung | Ereignis der Schule mit Aktion und Text (max. 500 Zeichen) |

Server werden in der Kommandozeile bei `server-block`, `server-unblock`, `unbind`, `label` über die Server-Nummer aus `show` oder den vollständigen Schlüssel angesprochen, bei `show-key` und `reissue` über den Platz in der Schule (1 = erster Server).
Abnahme: Je Zeile ein Test: Neuausstellung → alter Schlüssel liefert `unknown`, neuer ist `unbound`; Bindung lösen → Instanz zeigt beim nächsten Kontakt `unbound`; fünfter Schlüssel bei 4 gebuchten Servern ohne Bestätigung → abgewiesen, mit `--force` bzw. Bestätigung angelegt; jede Aktion erzeugt einen Verlaufseintrag.

**BET-102** · P0 · Status: Ist · Aktionen auf Schulebene (Portal und Kommandozeile)

| Aktion | Befehl | Wirkung | Kulanz auf der Instanz |
|---|---|---|---|
| pausieren | `pause` | Status `paused` für alle Server | nur lesen, `grace_days` (Standard 14), dann gesperrt |
| fortsetzen | `resume` | Status `active` | – |
| kündigen | `cancel` | Status `cancelled` | sofort gesperrt, keine Kulanz; im Portal Bestätigung mit Schulnamen |
| Abo aktiv bis | `extend --until JJJJ-MM-TT` | Abo-Ende setzen, leer = unbegrenzt | – |
| Grenzen | `set-limits` | `max_users`, `max_students` (leer = unbegrenzt) | – |
| gebuchte Server | `set-servers` (1 bis 1000) | Zahl der gebuchten Server | – |
| Sofortsperre Schule | `block [--text]` | Sperrbefehl an alle Server beim nächsten Kontakt | keine; Standardtext „Die Lizenz wurde vom Anbieter gesperrt.“ |
| Sperre aufheben | `unblock` | `unlock` beim nächsten Kontakt | – |
| umbenennen | Portal | Schulname max. 200 Zeichen, nicht leer | – |
| Notiz | Portal | max. 500 Zeichen | – |
| Server sperren / entsperren | `server-block` / `server-unblock` | nur dieser Server | keine |
| Bindung lösen | `unbind` | Bindung und Geheimnis entfernt (Serverumzug) | – |

Abnahme: `pause` → Instanz geht nach spätestens 15 Minuten in `grace` mit Grund `paused`; `cancel` → sofort `locked`; `extend` auf ein künftiges Datum → Instanz wechselt zurück nach `valid`/`warning`; `set-servers 0` → Fehlermeldung; Kündigen im Portal ohne korrekt eingegebenen Schulnamen wird auch serverseitig abgewiesen.

**BET-103** · P0 · Status: Ist · Sicherheitsmerkmale des Lizenzservers
Signaturschlüssel: ein Ed25519-Schlüsselpaar, der private Schlüssel entsteht auf dem Anbieter-Server (`keygen`), verlässt ihn nie und wird offline gesichert; nur der öffentliche Teil geht in die Schul-Software. Nonce je Anfrage, Antwort spiegelt sie (BET-079). Sperrgeheimnis je Server-Lizenz (64 Hex, nur bei Aktivierung ausgeliefert) bindet Sperrbefehle an die Schule und die Instanz (BET-086). Webhook-Signaturen (Kap. 14). Anfragebegrenzung je Adresse (BET-097). Verwaltung: Anmeldung gegen Durchprobieren geschützt, CSRF, Herkunftsprüfung, Sitzung 8 Stunden (BET-107). Antwort-Kopfzeilen: Content-Security-Policy (nur eigene Dateien, keine Inline-Skripte, kein Fremdinhalt), `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`. Exporte (CSV, PDF) mit Anhang-Kopfzeile und `no-store`. Hinter einem Proxy: `Host`-Kopf passend zur Portal-Adresse; das Portal zusätzlich per Proxy auf bekannte Adressen einschränken (Empfehlung). Das Antwortverhalten gegen fremde Schulen ist in BET-099 festgelegt (fremde Daten nicht lieferbar). Ein Schlüsselpaar signiert Lizenzantworten, Update-Antworten und Release-Manifeste; die Trennung ist offen (BET-138).
Abnahme: Ein Header-Test des Portals zeigt alle fünf Kopfzeilen; eine Suche im ausgelieferten Anbieter-Image findet weder privaten Schlüssel noch Datenbank noch Datenschlüssel; Portal-Seiten laden ohne Inline-Skripte (CSP-Verstöße = 0).

**BET-104** · P1 · Status: Ist · Konfigurationsvariablen des Lizenzservers

| Variable | Standard | Wirkung |
|---|---|---|
| `LZ_DATA_DIR` | `data` | Datenordner (Datenbank, Datenschlüssel, Passwort-Hash, Release-Bestand, Signaturschlüssel) |
| `LZ_ADMIN_PASSWORD_HASH` | — | Hash des Portal-Passworts (Vorrang); sonst Hash-Datei im Datenordner; sonst `LZ_ADMIN_PASSWORD` (Klartext, schwächer) |
| `LZ_TRUST_PROXY` | `0` | `1` = erste Adresse der Weiterleitungs-Kopfzeile zählt (hinter Proxy) |
| `LZ_COOKIE_SECURE` | `1` | `0` schaltet das Secure-Attribut ab (nur lokal) |
| `LZ_CONFIRM_DAYS` | `7` | Bestätigungszeitraum der Instanzen in Tagen (BET-085) |
| `LZ_KEY_STORE_KEY` | Datei im Datenordner | Datenschlüssel der Schlüsselanzeige (BET-100) |
| `LZ_RELEASE_DIR` | Datenordner/`releases` | Release-Bestand für Abbild-Dateien (Kap. 15) |
| `LZ_VENDOR_NAME`, `LZ_VENDOR_ADDRESS` | „Anbieter“, leer | Absender auf Rechnungen und Quittungen |
| `LZ_INVOICE_LEAD_DAYS` | `14` | Vorlauf des Rechnungslaufs in Tagen |
| `LZ_BILLING_AUTORUN` | `0` | `1` = Rechnungslauf im Hintergrund alle 6 Stunden |
| `LZ_AUTO_PAUSE` | `0` | Voreinstellung „Pausieren bei Verzug“ (je Schule übersteuerbar) |
| `LZ_STRIPE_WEBHOOK_SECRET`, `LZ_GOCARDLESS_WEBHOOK_SECRET` | — | Webhook-Geheimnisse; ohne sie antwortet der Endpunkt 503 |

Geheimnisse trägt nur der Anbieter ein, nie ein Assistent oder ein Dokument.
Abnahme: Ohne gesetzte Variablen läuft der Dienst mit den Standardwerten (Test); ohne Passwort-Quelle zeigt `/admin/login` Status 503 „Verwaltung nicht eingerichtet“; `LZ_CONFIRM_DAYS=3` → `confirmed_until` = Antwortzeit + 3 Tage.

**BET-105** · P0 · Status: Ist · Sicherung, Wiederherstellung und Image-Hygiene des Lizenzservers
Zu sichern (verschlüsselt, getrennt vom Dienst): Datenbank, Datenschlüssel (zusammen mit der Datenbank, sonst sind gespeicherte Schlüssel nach einer Wiederherstellung unlesbar), Passwort-Hash, Release-Bestand, privater Signaturschlüssel (zusätzlich offline). Sicherungen und Datenvolumen sind wie Geheimnisse zu behandeln. Das Image des Lizenzservers hat eine eigene Ausschlussliste: Schlüssel, Datenbank und Datenschlüssel landen nie im Image; das Schul-Image enthält weder Lizenzserver noch Tests, Entwicklerskripte, interne Dokumentation oder Updater-Entwicklungscode; keine Betreiber-Daten (Heimserver, Domain, Personen) in Kundentexten, ein Test prüft das bei jedem Lauf. Vor jedem Aufspielen: Sicherung, bestehende Test-Lizenz bleibt erhalten (BET-027).
Abnahme: Wiederherstellung auf einem frischen Lizenzserver → Schlüsselanzeige und alle Bindungen wie vorher; die Image-Inhaltsprüfung (Test) findet keinen Treffer für `*.key`, Datenbank-Datei und Passwort-Hash; der Test „keine Betreiber-Daten in Kundentexten“ läuft grün.

**BET-106** · P0 · Status: offen · Aufbewahrungsfristen auf dem Lizenzserver
Das Dokument des Altbestands nennt keine Fristen. Personenbezogene und sensible Daten dort: IP-Adressen der letzten Prüfung und des Verlaufs, Kontaktdaten der Schule, Zahlungsreferenzen, Mandatsnummern, Kundennummern beim Zahlungsanbieter. Neubau: Fristen je Datenart festlegen und dokumentieren (Prüfverlauf `check`/`activate` mit IP-Adresse; Verlauf `admin`; Zahlungen mit den gesetzlichen Aufbewahrungspflichten für Rechnungen) und automatisch durchsetzen; die Fristen stehen in der Datenschutzunterlage (BET-081). `[unklar: Fristen legt der Betreiber mit Steuer- und Datenschutzberatung fest]`
Abnahme: Für jede Datenart ist eine Frist in der Betreiber-Dokumentation eingetragen; ein Lauf mit Zeitmanipulation löscht IP-Adressen und Prüfverlaufszeilen älter als die Frist und lässt Rechnungen innerhalb der gesetzlichen Frist unangetastet.

### 13.2 Anbieter-Portal (`/admin`)

**BET-107** · P0 · Status: Ist · Anmeldung am Portal

| Regel | Wert |
|---|---|
| Passwort-Speicherung | PBKDF2-SHA256, 600 000 Durchläufe, 16 Byte Salz; nur Hash gespeichert |
| Mindestlänge (Kommandozeile `set-admin-password`, verdeckte Eingabe) | 12 Zeichen |
| Quellen (Reihenfolge) | `LZ_ADMIN_PASSWORD_HASH`, Hash-Datei im Datenordner, `LZ_ADMIN_PASSWORD` |
| Kein Passwort gesetzt | Portal aus: Anmeldeseite mit Status 503 „Verwaltung nicht eingerichtet“ |
| Fehlversuche | 5 je Adresse in 10 Minuten, danach 429, bis der älteste Fehlversuch 10 Minuten alt ist |
| Sitzung | 8 Stunden (Cookie und Serverzeit), nur im Arbeitsspeicher (Neustart meldet ab) |
| Cookie | HttpOnly, SameSite=Strict, Secure (Standard an), Name fest und getrennt vom Schul-Cookie |
| CSRF | Formular-Token je Sitzung; Änderungen nur bei gleicher Herkunft (Origin oder Referer passt zum Host), sonst „Anfrage abgelehnt“ (403) |

Abnahme: 5 falsche Passwörter von einer Adresse → die 6. Anmeldung 429 auch mit richtigem Passwort; POST ohne CSRF-Token oder mit fremdem Origin → 403; Sitzung nach 8 Stunden ungültig; ohne gesetztes Passwort → 503; das Passwort steht nirgends im Log.

**BET-108** · P1 · Status: offen · Konten und Rollen im Portal
Ist: ein gemeinsames Verwaltungs-Passwort, keine Konten und keine Rollen; Sitzungen nur im Arbeitsspeicher. Der Betreiber mit Serverzugang nutzt zusätzlich die Kommandozeile (alle Befehle). Neubau-Vorschlag: persönliche Portal-Konten mit Rollen (`[unklar: Rollennamen entscheidet der Betreiber]`; Vorschlag: Verwaltung (alles), Support (Schulen und Server lesen, Verlauf, Entsperren ohne Zahlungen), Buchhaltung (Zahlungen, Tarife, Rechnungen), Lesen), Zwei-Faktor-Anmeldung, Protokoll jeder Aktion mit Konto, sperrbare Konten; gefährliche Aktionen (BET-113) nur Verwaltung.
Abnahme: Konto „Support“ sieht keine Zahlungsseiten (404) und kann keine Schule kündigen (403); jede Aktion trägt im Verlauf das handelnde Konto; Anmeldung ohne zweiten Faktor ist für Verwaltungs-Konten nicht möglich.

**BET-109** · P1 · Status: Ist · Start der Portal-Oberfläche
Seitenleiste: Start, Schulen, Zahlungen, Tarife, Updates. Startseite: Kennzahlen (Schulen aktiv, pausiert, gesperrt; Server online oder still; Einnahmen des Monats; überfällige Zahlungen; Abo-Ende in 30 Tagen), Liste „Braucht Aufmerksamkeit“, letzte Aktionen, Schaltflächen „Schule anlegen“ und „Rechnungslauf“. Wunsch (16.10.2026): „eine Übersicht für die Firma, wo ich quasi die Schulen sehe und deren Lizenzen sehe“.
Abnahme: Testdaten mit 2 aktiven, 1 pausierten, 1 gesperrten Schule, einem Server ohne Kontakt seit 3 Tagen, einer überfälligen Zahlung → die Kennzahlen zeigen genau diese Zahlen; der Server erscheint unter „Braucht Aufmerksamkeit“.

**BET-110** · P1 · Status: Ist · Schulliste
Liste mit Suche (Name, Gruppen-Kennung), Filtern (Status, Zahlung überfällig, Server ohne Kontakt, Schlüssel nicht eingetragen), Sortierung und Statuschips (z. B. „Server: 3 von 3 aktiv“, Zahlungszustand `überfällig`, `offen`, `ok`, `keiner` = kein Tarif und nie gezahlt). Die Übersicht zeigt nie einen Schlüssel.
Abnahme: Suche nach einem Namensteil findet die Schule; Filter „Server ohne Kontakt“ zeigt nur Schulen mit mindestens einem Server im Zustand `silent`; in der gerenderten Liste (Quelltext) kommt kein Schlüssel vor.

**BET-111** · P1 · Status: Ist · Schule anlegen (Assistent) und Lizenzpaket
Assistent in vier Schritten: Schule (Name), Tarif und Server (gebuchte Anzahl), Abo und Grenzen (Abo-Ende, `max_users`, `max_students`, optional erste Zahlung), Prüfen. Danach werden die Schlüssel einmalig als frische Meldung angezeigt und als Zugangsblatt zum Herunterladen angeboten (alle Schlüssel der Schule; die Quellen nennen PDF bzw. Textdatei, Neubau: PDF). Lizenzpaket für den Erstzugang (Wortlaut des Betreibers: Lizenz und Admin-Zugang mit einmaligem Passwort): Schlüssel, Administrationszugang mit Einmalpasswort und erzwungenem Passwortwechsel, Schulanleitung (Betreiber-Paket, BET-214). Anlegen ohne Tarif ist möglich; ohne Tarif entstehen keine automatischen Rechnungen.
Abnahme: Assistent mit 2 Servern → 2 Schlüssel „Server 1“, „Server 2“, Zugangsblatt enthält beide, Seite neu laden → Schlüssel nicht mehr in der Meldung, aber in der Detailseite anzeigbar; Schule ohne Abo-Ende → `valid_until` leer (unbegrenzt); Name leer → Fehlermeldung.

**BET-112** · P1 · Status: Ist · Schul-Detailseite
Reiter: Überblick (Status, Abo, Grenzen, Server-Zusammenfassung, Zahlungszustand), Server (je Server Bezeichnung, maskierter Schlüssel, Zustand, Version, letzte Prüfung, Adresse; Aktionen: anzeigen, kopieren, neu ausstellen, sperren, Bindung lösen, umbenennen, weiteren Schlüssel ausstellen), Zahlungen (BET-121), Verlauf (BET-118), Einstellungen (Name, Notiz, Abo, Grenzen, gebuchte Server, Abrechnung mit Tarif und Pausieren bei Verzug, Status und Sperren; Update-Einstellungen der Schule siehe BET-146).
Abnahme: Jeder Reiter lädt mit Testdaten; Änderung des Abo-Endes erscheint im Verlauf; Server-Reiter zeigt für einen Altbestands-Schlüssel ohne Klartext „Nicht gespeichert – neu ausstellen“.

**BET-113** · P0 · Status: Ist · Gefährliche Aktionen im Portal
Kündigen und Sofortsperre sind rot gekennzeichnet, laufen über einen eigenen App-Dialog (kein Browser-Popup) und verlangen die Eingabe des exakten Schulnamens; die Prüfung erfolgt auch auf dem Server. Dasselbe gilt für Neuausstellung eines Schlüssels (Bestätigung) und das Überschreiten der gebuchten Serverzahl.
Abnahme: Kündigen mit Schulnamen in falscher Schreibweise → Dialog verweigert; ein direkter POST mit falschem Schulnamen → serverseitig abgewiesen, Status unverändert; kein `window.confirm`/`alert` im Portal (Test auf Quelltext).

**BET-114** · P0 · Status: Ist · Schlüsselanzeige im Portal
Anzeige maskiert (`SPUL-••••-••••-••••-XXXX`); „Anzeigen“ zeigt den Klartext, schreibt einen Eintrag in den Verlauf (`key_shown`) und setzt Cache-Verbot; „Kopieren“ legt den Schlüssel in die Zwischenablage. Entscheidung des Betreibers (16.10.2026 15:43, überstimmt „genau einmal anzeigen“): Schlüssel sind im Portal jederzeit anzeigbar und kopierbar. Altbestand ohne gespeicherten Klartext: „Nicht gespeichert – neu ausstellen“.
Abnahme: „Anzeigen“ → Verlaufseintrag mit Zeit (und im Neubau handelnder Konto); Antwort-Kopfzeile `Cache-Control: no-store`; ein zweites „Anzeigen“ funktioniert; „Kopieren“ legt den vollständigen Schlüssel ab; Altbestand-Schlüssel ohne `key_enc` zeigt den Hinweis.

**BET-115** · P1 · Status: Ist · Rückmeldungen, Gestaltung und Erweiterbarkeit des Portals
Wunsch (16.10.2026): „die Oberfläche soll bitte den gleichen Style haben wie die Schuloberfläche“. Das Portal nutzt Farben, Schrift, Karten und Tabellen der Schul-Oberfläche, hell, dunkel oder automatisch (Umschalter in der Seitenleiste) und ist am Handy nutzbar. Nach jeder Änderung erscheint eine einmalige Meldung; einmalige Inhalte (frische Schlüssel) erscheinen nur einmal. Erklärungen nur über Hilfe-Symbole, Anrede „Sie“, eigene App-Dialoge. Neue Portal-Seiten lassen sich ergänzen (Navigationseintrag und Registrierung), ohne bestehende Seiten zu ändern. Barrierefreiheit: `[unklar: im Altbestand nicht beschrieben]`, Neubau gemäß OBE.
Abnahme: Portal-Screenshots in Hell und Dunkel verwenden dieselben Farbvariablen wie die Schul-Oberfläche; bei 375 Pixel Breite kein horizontales Scrollen; nach „Schule pausieren“ erscheint genau eine Meldung, nach Neuladen keine.

**BET-116** · P1 · Status: Ist · Kommandozeile des Anbieters
Alle Funktionen des Portals gibt es als Befehle (für den Betreiber mit Serverzugang). Einrichten: `keygen` (Signaturschlüsselpaar), `set-admin-password`, `serve --port`. Schulen: `create-school --name … --servers … --until … --max-users … --max-students …`, `list`, `show <Nr>`, `pause`, `resume`, `cancel`, `block <Nr> --text …`, `unblock`, `extend <Nr> --until …`, `set-limits <Nr> --max-users … [--max-students …]`, `set-servers <Nr> <Anzahl>`. Server: `add-server <Nr> --label … [--force]`, `server-block <Nr> --text …`, `server-unblock`, `unbind`, `label <Nr> "…"`, `show-key <Schule> <Server>` (nur im Terminal), `reissue <Schule> <Server> --yes`. Zahlungen: `payments run` (Rechnungslauf), `payments export [JAHR]`, `payments webhooks`. Updates: `release-add`, `rollout-add`, `rollout-start` (BET-136 ff.). Datenübernahme: `migrate-legacy [--dry-run]`.
Abnahme: Jeder Befehl hat einen automatisierten Test (Aufruf → erwartete Wirkung im Portal); `reissue` ohne `--yes` bricht ab; `show-key` schreibt einen Verlaufseintrag; die Befehlsliste in der Hilfe stimmt mit dieser Liste überein.

**BET-117** · P3 · Status: Ist · Übernahme alter Lizenzen
`migrate-legacy` mit Trockenlauf (`--dry-run`): je alter Lizenz eine Schule mit einem Server-Schlüssel; Abo-Ende, Grenzen und Widerruf werden übernommen; Datenbank vorher gesichert; alte Tabellen bleiben unangetastet; neue Schlüssel stehen nur in der Befehlsausgabe; alte Lizenzdateien werden von der Schul-Instanz nicht mehr unterstützt. Im Neubau nur nötig, wenn Lizenzen des Altbestands (zwei Test-Lizenzen) übernommen werden `[unklar: ob nötig]`.
Abnahme: Trockenlauf listet die Schulen, ohne Daten zu ändern (Zeilenzahlen vor und nach gleich); echter Lauf legt je alter Lizenz eine Schule an, Abo-Ende und Grenzen stimmen.

**BET-118** · P1 · Status: Ist · Verlauf der Schule
Jede Prüfung (`check`, `activate`), jede Anbieter-Aktion (`admin`) und jede Zahlung (`payment`) erzeugt einen Verlaufseintrag der Schule (Zeit, Art, Status/Aktion, Text max. 500 Zeichen; bei Prüfungen Instanz-ID, Adresse, IP, Version, Konten; beim Ping nichts). Der Reiter „Verlauf“ zeigt die Einträge neueste zuerst mit Filter nach Art; die IP-Adressen unterliegen der Frist aus BET-106.
Abnahme: Ein `check` erscheint mit Version und IP; ein `ping` erzeugt keinen Eintrag; „Schlüssel anzeigen“ erzeugt `key_shown`; Filter „Zahlungen“ zeigt nur Zahlungseinträge.

---

## 14. Zahlungen, Rechnungen, Tarife, Verlängerung

Zahlungen laufen ausschließlich im Lizenzserver des Anbieters (Portal unter `/admin/payments`). Beträge werden in Cent geführt, Zeitpunkte in UTC, Anzeige in Ortszeit (Europa/Berlin), Datumsformat TT.MM.JJJJ. Preise und Tarifstaffeln legt der Betreiber fest; dieses Dokument enthält keine Preise.

**BET-119** · P1 · Status: Ist · Tarife
Tabelle `plans`; Seite `/admin/payments/plans`.

| Feld | Standard | Einheit / Grenze | Wirkung |
|---|---|---|---|
| Name | – | max. 100 Zeichen | Anzeige (Beispiele: „Monatlich“, „Jährlich“) |
| Preis | 0 | Cent je Intervall | Grundbetrag |
| Währung | EUR | 3 Zeichen | |
| Intervall | `month` | `month` oder `year` | Anzeige |
| Verlängerung je Zahlung | 1 | Monate, 1 bis 120 | um so viele Monate rückt das Abo-Ende je bezahlter Zahlung vor |
| Server inklusive | 1 | 1 bis 1000 | im Preis enthaltene Server |
| Preis je weiterem Server | 0 | Cent je Intervall | Zuschlag |
| Kulanztage bei Verzug | 14 | Tage, 0 bis 365 | Schwelle der automatischen Pause (BET-125) |
| aktiv | ja | | nur aktive Tarife werden für Rechnungen verwendet |

Betrag einer Rechnung = Preis + max(0; gebuchte Server − inklusive Server) × Preis je weiterem Server.
Abnahme: Tarif mit Preis 5000 Cent, 2 Server inklusive, 1000 Cent je weiterem Server; Schule mit 4 gebuchten Servern → Rechnung 7000 Cent; Verlängerung 121 Monate → Eingabe abgewiesen; inaktiver Tarif → der Rechnungslauf erzeugt keine Rechnung.

**BET-120** · P1 · Status: Ist · Abrechnung je Schule
Tabelle `school_billing`, eine Zeile je Schule: Tarif (leer = keine automatischen Rechnungen), „Pausieren bei Verzug“ (leer = Voreinstellung `LZ_AUTO_PAUSE`, Standard aus; Automatik nur, wenn für die Schule „ein“), Kundenkennung beim Zahlungsanbieter für Kartenzahlung (max. 64 Zeichen), Mandat für Lastschrift (max. 64 Zeichen). Zu finden unter Schule → Einstellungen → Abrechnung.
Abnahme: Schule ohne Tarif → der Rechnungslauf legt nie eine Rechnung an; „Pausieren bei Verzug“ leer und `LZ_AUTO_PAUSE=0` → keine Automatik; „ein“ an der Schule bei `LZ_AUTO_PAUSE=0` → Automatik wirkt für diese Schule.

**BET-121** · P1 · Status: Ist · Zahlungen erfassen
Tabelle `payments`:

| Feld | Standard / Grenze | Bedeutung |
|---|---|---|
| Betrag | 0 Cent | |
| Währung | EUR | 3 Zeichen |
| Zeitraum von / bis | leer | von der Zahlung abgedeckter Zeitraum |
| Fällig am | leer | bei Rechnungen: bisheriges Abo-Ende |
| Bezahlt am | leer | Zeitpunkt |
| Methode | `transfer` | `transfer` (Überweisung), `sepa` (Lastschrift), `card` (Karte), `manual` (manuell), `stripe`, `gocardless` |
| Referenz | max. 120 Zeichen | |
| Status | `open` | `open` (offen), `paid` (bezahlt), `failed` (fehlgeschlagen), `refunded` (erstattet) |
| Notiz | max. 500 Zeichen | |
| Zahlungsanbieter / Anbieter-Kennung | leer; Kennung eindeutig | Dublettenschutz |
| verlängert | nein | verhindert doppelte Verlängerung |

Eine manuell erfasste Zahlung (Datum, Betrag, Zeitraum, Methode, Status, Referenz, Notiz) mit Status „bezahlt“ verlängert sofort (BET-122). Erstattung: Status „erstattet“, das Abo-Ende bleibt unverändert, ein Hinweis erscheint im Verlauf.
Abnahme: Zahlung mit Referenz von 121 Zeichen → abgewiesen; zweite Zahlung mit derselben Anbieter-Kennung → abgewiesen; „bezahlt“ erfassen → Abo-Ende rückt vor und ein Verlaufseintrag `paid` entsteht; „erstattet“ ändert das Abo-Ende nicht.

**BET-122** · P0 · Status: Ist · Verlängerung des Abos bei Zahlung
Regel (16.10.2026): „Verlängerung ab dem bisherigen Ablaufdatum, nicht ab heute“. Neues Abo-Ende = bisheriges Abo-Ende (ohne Abo-Ende: heute) + Verlängerungsmonate des Tarifs; Monatsenden werden gekappt (31.01. + 1 Monat = 28. bzw. 29.02.). Zeitraum der Zahlung (wenn nicht angegeben): Beginn = bisheriges Abo-Ende + 1 Tag (ohne Abo-Ende: heute), Ende = neues Abo-Ende. Eine Zahlung verlängert höchstens einmal (Kennzeichen „verlängert“); jede Verlängerung erzeugt einen Verlaufseintrag.
Abnahme: Abo-Ende 31.01.2027, Tarif 1 Monat, Zahlung „bezahlt“ → 28.02.2027; Abo-Ende 31.01.2028 → 29.02.2028; zweimal auf „bezahlt“ setzen → eine einzige Verlängerung; Schule ohne Abo-Ende → heute + Monate; Zeitraum der Zahlung 01.02.2027 bis 28.02.2027.

**BET-123** · P1 · Status: offen · Verlängerung bei bereits abgelaufenem Abo
Ist: Die Verlängerung rechnet auch bei einem in der Vergangenheit liegenden Abo-Ende ab diesem Datum; nach der Zahlung kann die Schule weiter abgelaufen sein. Absicht unklar. Zu entscheiden: (A) ab altem Abo-Ende (Ist), (B) ab dem Zahltag, wenn das alte Ende mehr als `[unklar: N]` Tage zurückliegt. Bis zur Entscheidung gilt A.
Abnahme: Entscheidung (A oder B) im Dokument vermerkt; Test: Abo-Ende vor 40 Tagen, Tarif 1 Monat, Zahlung bezahlt → bei A neues Ende vor 10 Tagen und Schule bleibt `expired`, bei B Ende in 1 Monat ab Zahltag und die Instanz wechselt nach `valid`.

**BET-124** · P1 · Status: Ist · Rechnungslauf
Voraussetzungen je Schule: nicht gekündigt, Tarif aktiv, Abo-Ende gesetzt, Abo-Ende − Vorlauf ≤ heute (Vorlauf 14 Tage, `LZ_INVOICE_LEAD_DAYS`), keine offene Zahlung, keine offene oder bezahlte Zahlung für denselben Beginn. Rechnungsdaten: Beginn = Abo-Ende + 1 Tag, Ende = Abo-Ende + Verlängerungsmonate, fällig = bisheriges Abo-Ende, Methode Überweisung, Status offen, Betrag nach BET-119. Schritte: (1) Rechnungen anlegen, (2) Verzugspausen (BET-125), (3) überfällige zählen (offen und Fälligkeit vor heute → Anzeige „überfällig“ und Verlaufseintrag). Auslöser: Schaltfläche „Rechnungslauf“, Befehl `payments run` für Cron (Ausgabe „Rechnungslauf: N Rechnungen angelegt, M Schulen pausiert, K überfällig.“), `LZ_BILLING_AUTORUN=1` (Hintergrundlauf alle 6 Stunden = 21 600 Sekunden ab Dienststart; Fehler werden protokolliert, der Dienst läuft weiter). Ist-Befund: Nach einer fehlgeschlagenen Zahlung legt der Lauf erneut eine offene Rechnung für denselben Zeitraum an, weil fehlgeschlagene Zahlungen nicht als vorhanden zählen `[unklar: ob gewollt]`.
Abnahme: Schule mit Abo-Ende in 10 Tagen und aktivem Tarif → nach dem Lauf genau eine offene Rechnung, zweiter Lauf legt keine zweite an; Abo-Ende in 20 Tagen → keine; gekündigte Schule → keine; die CLI-Ausgabe entspricht dem Satzmuster; bei ausgefallener Zahlungsanbieter-Verbindung läuft der Lauf trotzdem.

**BET-125** · P1 · Status: Ist · Automatische Pause bei Zahlungsverzug
Standard aus (`LZ_AUTO_PAUSE`), je Schule übersteuerbar. Ist eine offene Zahlung länger als Fälligkeit + Kulanztage des Tarifs (Standard 14) überfällig, wird die Schule pausiert (Verlaufseintrag `auto_paused`, „Automatisch pausiert“); danach sind die Server 14 Tage nur lesbar (Kulanz der Anwendung, BET-083), dann gesperrt. Es gibt zwei Kulanzbegriffe (Tarif-Kulanz für die Pause, Anwendungs-Kulanz nach Pause); die Vereinheitlichung ist zu entscheiden (BET-218). Ob ein späterer Zahlungseingang eine automatisch pausierte Schule fortsetzt, ist im Altbestand nicht geregelt `[unklar]`; Neubau-Vorschlag: nur durch die Automatik ausgelöste Pausen werden bei vollständiger Zahlung automatisch aufgehoben, manuelle Pausen nie.
Abnahme: Automatik an, Rechnung seit 15 Tagen überfällig, Tarif-Kulanz 14 → Lauf pausiert die Schule und die Instanz geht innerhalb von 15 Minuten in `grace`; seit 10 Tagen überfällig → keine Pause; Automatik aus → nie; Zahlung nach Auto-Pause → Verhalten wie entschieden (dokumentiert) und im Verlauf sichtbar.

**BET-126** · P0 · Status: Ist · Zahlungsanbieter-Webhook Stripe
Endpunkt `POST /api/v1/payments/webhook/stripe`. Prüfung: Kopfzeile `Stripe-Signature` mit `t=` (Zeit) und `v1=` (Signatur, mehrere zulässig); HMAC-SHA256 über „Zeit.Körper“ mit dem Webhook-Geheimnis; Abweichung zur Serverzeit höchstens 300 Sekunden. Ereignisse „bezahlt“: `invoice.paid`, `invoice.payment_succeeded`, `checkout.session.completed` (nur wenn bezahlt), `payment_intent.succeeded`; „fehlgeschlagen“: `invoice.payment_failed`, `payment_intent.payment_failed`. Buchungskennung: Ereignis-ID des Anbieters. Zuordnung der Schule über die Gruppen-Kennung (Metadatum `school` oder `client_reference_id`) oder die Kundenkennung (`cus_…`) aus der Abrechnung. Körper höchstens 512 000 Byte; Währung wird groß geschrieben (Standard EUR). Ohne eingerichtetes Geheimnis 503, bei falscher Signatur oder unlesbarem Körper 400.
Abnahme (nur mit erfundenen Test-Geheimnissen): gültig signiertes Ereignis `invoice.paid` → die älteste offene Zahlung der Schule ist bezahlt; Signatur mit 301 Sekunden Abweichung → 400; veränderter Körper → 400; ohne Geheimnis → 503; dasselbe Ereignis zweimal → zweite Antwort `duplicate`, keine zweite Buchung.

**BET-127** · P0 · Status: Ist · Zahlungsanbieter-Webhook GoCardless (SEPA-Lastschrift)
Endpunkt `POST /api/v1/payments/webhook/gocardless`. Prüfung: Kopfzeile `Webhook-Signature` (HMAC-SHA256, hexadezimal) über den Rohtext; kein Zeitfenster. Ereignisse: Ressource `payments` mit Aktion `confirmed` (bezahlt) sowie `failed`, `charged_back`, `late_failure_settled` (fehlgeschlagen); `paid_out` wird ignoriert. Der Betrag steht nicht im Ereignis: es gilt die offene Rechnung oder der Tarifbetrag. Buchungskennung `gc:<Zahlung>:<Aktion>`. Zuordnung über das Mandat (`MD…`) aus der Abrechnung oder das Metadatum `school`. Schutz gegen Wiedereinspielen besteht im Altbestand nur über die eindeutige Kennung; Neubau: zusätzlich Ereigniszeit prüfen, soweit der Anbieter sie liefert `[Vorschlag]`.
Abnahme (Test-Geheimnisse): `confirmed` für ein bekanntes Mandat → Zahlung bezahlt, Abo verlängert; `failed` → Zahlung „fehlgeschlagen“ mit Notiz; `paid_out` → Ergebnis ignoriert, keine Buchung; unbekanntes Mandat → Ergebnis `unknown_school`, keine Buchung; wiederholte Nachricht → `duplicate`.

**BET-128** · P0 · Status: Ist · Verarbeitung eines Zahlungseingangs
Antwort immer `{"ok": true, "results": […]}` (je Ereignis ein Ergebnis). Zuordnung: Gruppen-Kennung oder Kundenkennung/Mandat; ohne Treffer `unknown_school`, keine Buchung. „Bezahlt“: die älteste offene Zahlung der Schule wird bezahlt (Betrag übernommen, falls angegeben), sonst entsteht eine neue Zahlung; danach Verlängerung (BET-122). „Fehlgeschlagen“: die älteste offene Zahlung wird „fehlgeschlagen“ (oder es entsteht eine neue fehlgeschlagene Zahlung) mit Notiz und Verlaufseintrag `failed`. Dublette (Anbieter-Kennung bereits verbucht): `duplicate`, keine Buchung. Anzeige des Einrichtungsstands auf der Seite „Zahlungen“ und per `payments webhooks` („eingerichtet“ bzw. „nicht eingerichtet (… fehlt)“).
Abnahme: Je Ergebnis (`unknown_school`, `duplicate`, bezahlt, fehlgeschlagen) ein Test; Nachricht ohne offene Rechnung → neue Zahlung über den Tarifbetrag; zwei gleichzeitige gleiche Nachrichten → genau eine Buchung.

**BET-129** · P1 · Status: offen · Zahlungsanbieter in Betrieb nehmen
Stripe (Karte) und GoCardless (SEPA-Lastschrift) sind vorbereitet, aber inaktiv: Konten und Schlüssel müssen vom Betreiber angelegt werden; Webhook-Geheimnisse nur über Umgebungsvariablen. Offen ist ein Test mit den Testmodi der Anbieter (nicht nur mit erfundenen Geheimnissen). Eine Prüfliste des Altbestands hält Stripe-Abo-Punkte für nicht zutreffend, die Zahlungsanbindung nutzt aber Stripe und GoCardless; abzugleichen.
Abnahme: `payments webhooks` meldet beide Anbieter „eingerichtet“; je eine Testzahlung im Testmodus (Stripe-Rechnung bezahlt, GoCardless-Zahlung bestätigt) verlängert eine Testschule und erscheint im Verlauf; das Ergebnis ist mit Datum dokumentiert.

**BET-130** · P1 · Status: Ist · Rechnung und Quittung als PDF
Je Zahlung ein PDF (eine Seite A4): Titel „Rechnung Nr. N“ (offen) bzw. „Quittung“ (bezahlt); Absender aus `LZ_VENDOR_NAME` (Standard „Anbieter“) und `LZ_VENDOR_ADDRESS`; Schule, Zeitraum, Betrag, Fälligkeit, Referenz. Abruf im Portal je Zahlung, Antwort als Anhang mit `no-store`. Ist-Befund: Die Rechnungsnummer ist die interne Zahlungs-ID, das PDF enthält keinen Steuerausweis, nur den Verweis „siehe gesetzliche Angaben des Anbieters“; fest eingetippte Produktnamen in Rechnungstexten sind zu vermeiden (Produktname nur an einer Stelle).
Abnahme: PDF einer offenen Zahlung trägt „Rechnung Nr.“, einer bezahlten „Quittung“; Absender stammt aus den Variablen; die Antwort hat `Content-Disposition: attachment` und `Cache-Control: no-store`.

**BET-131** · P0 · Status: offen · Rechtlich vollständige Rechnungen
Neubau: eigener fortlaufender, lückenloser Nummernkreis (nicht die interne ID); Pflichtangaben nach Umsatzsteuerrecht (Name und Anschrift von Anbieter und Schule, Steuernummer oder USt-IdNr., Ausstellungsdatum, Leistungszeitraum, Leistungsbeschreibung, Entgelt, Steuersatz und Steuerbetrag oder Hinweis auf Steuerbefreiung); Stornobeleg oder Gutschrift bei Erstattung mit Bezug auf die ursprüngliche Nummer; Aufbewahrung nach gesetzlichen Fristen (BET-106). Schulen und Schulträger sind öffentliche Auftraggeber: Pflicht zur elektronischen Rechnung (XRechnung/ZUGFeRD) prüfen `[unklar: Prüfung durch Steuerberatung]`.
Abnahme: Die Pflichtangaben-Checkliste ist auf einem Muster-PDF vollständig abgehakt; 100 parallel erzeugte Rechnungen erhalten lückenlos aufsteigende Nummern ohne Dublette; eine Erstattung erzeugt einen Stornobeleg mit Bezug auf die Ursprungsnummer.

**BET-132** · P2 · Status: Ist · Zahlungsseite, Einnahmen, CSV-Export
Seite `/admin/payments`: offene und überfällige Zahlungen, Einnahmen je Monat (bezahlte Zahlungen nach Zahldatum, letzte 12 Monate) als Diagramm, Zahlungszustand je Schule (`überfällig`, `offen`, `ok`, `keiner`). Export `/admin/payments/export.csv` und `payments export [JAHR]`: Trennzeichen Semikolon, UTF-8 mit Byte-Order-Mark, Zeilenende CRLF, Betrag mit Komma, Jahresfilter; Spalten: Nr, Schule, Gruppe, Status, Betrag, Währung, Zeitraum von, Zeitraum bis, Fällig, Bezahlt am, Methode, Referenz, Anbieter, Notiz. Neubau: Zellen, die mit `=`, `+`, `-` oder `@` beginnen, werden im Export entschärft (Befund: CSV-Exporte ohne Formel-Schutz).
Abnahme: CSV öffnet in einer Tabellenkalkulation mit korrekten Umlauten und Kommabeträgen; eine Referenz `=1+1` erscheint als Text; die Summe der Monatswerte entspricht der Summe der bezahlten Zahlungen der letzten 12 Monate.

**BET-133** · P1 · Status: Ist · Erste Zahlung beim Anlegen einer Schule
Mit Tarif und „Beginn“ legt der Assistent (BET-111) das Abo-Ende fest: ohne erste Zahlung gilt Abo-Ende = Beginn + Verlängerungsmonate − 1 Tag (wenn kein Abo-Ende angegeben); mit erster Zahlung wird zuerst Abo-Ende = Beginn − 1 Tag gesetzt, dann eine bezahlte Zahlung (Betrag nach Tarif) mit Notiz „Erste Zahlung (beim Anlegen erfasst)“ angelegt und verlängert.
Abnahme: Beginn 01.08.2027, Tarif 12 Monate: mit erster Zahlung → Abo-Ende 31.07.2028 und eine bezahlte Zahlung; ohne → Abo-Ende 31.07.2028 und keine Zahlung.

**BET-134** · P0 · Status: Ist · Zahlungsdaten bleiben beim Anbieter
Zahlungen laufen nur im Lizenzserver, nie in der Schul-Instanz; die Schule erhält Rechnungen vom Anbieter. Im Lizenzserver stehen keine Karten- oder Kontodaten (sie liegen beim Zahlungsanbieter); gespeichert werden nur Referenz, Kundenkennung, Mandatskennung und Anbieter-Kennung. Die Zahlungsanbieter sind in der Datenschutzunterlage des Anbieters als Empfänger zu nennen. Webhook-Geheimnisse nur über Umgebungsvariablen; Tests mit erfundenen Geheimnissen.
Abnahme: Ein Datenbankabzug des Lizenzservers enthält kein Muster einer Kartennummer oder IBAN; die Schul-Instanz hat weder Tabelle noch Route für Zahlungen.

**BET-135** · P1 · Status: offen · Preis- und Lizenzmodell
Empfehlung E2 des Berichts (nicht entschieden): Jahreslizenz je Schule, gestaffelt nach Schülerzahl; Testbetrieb mit 25 Konten als Probierversion; Preise legt der Betreiber fest; kein Testbetrieb ohne Lizenz in Produktion. Marktvergleich (Belege, keine Listenpreise): Schulmanager Online 89 bis 239 Euro je Schuljahr und Modul, bis 30 % Rabatt bei mehreren Modulen; schul.cloud 30 Tage Test, Laufzeit 1 oder 12 Monate; Lizenzmodelle der Wettbewerber je Nutzer, je Schüler, je Schule oder je Träger. Widerspruch der Quellen: „kein Lizenzmodul je Funktion“ gegen „Ein Preis ohne Modul-Staffel“ gegen Backlog B-56 „Module ein-/ausschalten“ (BET-095).
Abnahme: Tarife (Preis, Staffel, Intervall, inklusive Server) sind im Portal angelegt und schriftlich beschlossen; die Probierversion ist als Tarif mit `max_users` 25 und Abo-Ende abbildbar, in Produktion lauffähig, das 26. Konto wird abgelehnt (BET-090); die Entscheidung über Modul-Staffel ja/nein ist dokumentiert.

---

## 15. Update-System

Ziel (Betreiber, 16.10.2026): „dass die Schulserver automatisch das Update machen“, der Anbieter bestimmt den Zeitpunkt („am Wochenende“), bei mehreren Servern je Schule immer mindestens einer online. Das System besteht aus der Update-Verwaltung im Lizenzserver (Releases, Rollouts, Termine, Strategien, Protokoll; Portal `/admin/updates`), dem Update-Agenten als Begleitdienst bei der Schule (15.4), der Karte „Updates“ unter `/betrieb` und den Voraussetzungen für den Betrieb mit mehreren Servern (15.5). Die Ausführung ohne Anbieter-Automatik (Betreiber aktualisiert selbst) steht in BET-026; die Migrationsregel in BET-034, das Prüfskript in BET-035.

### 15.1 Releases, Signatur, Verteilung

**BET-136** · P0 · Status: Ist · Release anlegen
Tabelle `upd_releases`; Anlegen im Portal oder per Befehl `release-add` (Version, Abbild-Datei, Mindestversion, Migrationskennzeichen, „breaking“-Schalter für nicht abwärtskompatibel, Notizen).

| Feld | Regel | Standard |
|---|---|---|
| Version (`version`) | genau drei Zahlenblöcke (Form 1.4.0), eindeutig; Versionen sind unveränderlich | – |
| Kanal (`channel`) | `stable` oder `test`; Test-Releases nur an Test-Schulen (BET-147) | `stable` |
| Mindestversion (`min_version`) | Form x.y.z, muss kleiner als die Version sein | leer |
| Enthält Migration (`has_migration`) | Ja/Nein | nein |
| Migration abwärtskompatibel (`backward_compatible`) | Ja/Nein; nein → Wartungsfenster bei mehreren Servern (BET-149); ohne Migration erzwungen „ja“ | ja |
| Verteilung | Datei oder Registry-Verweis (BET-139) | – |
| Notizen (`notes`) | Versionsnotizen als Text für die Schule, max. 4000 Zeichen | leer |
| Manifest / Signatur | BET-137 | – |
| Zurückgezogen (`withdrawn`) | BET-141 | nein |

Eine Version lässt sich nur zurückziehen, nie überschreiben.
Abnahme: Version `1.4` oder `1.4.0.1` → abgewiesen; zweite Anlage von `1.4.0` → abgewiesen; Mindestversion gleich oder größer als die Version → abgewiesen; Release ohne Migration hat `backward_compatible` = ja und lässt sich nicht auf „nein“ setzen.

**BET-137** · P0 · Status: Ist · Manifest und Signatur
Je Release ein Manifest (kanonisches JSON wie BET-079): Produktkennung (fest, Altbestand `schulpuls`), Version, Mindestversion, die zwei Migrationsangaben, bei Datei-Verteilung SHA-256-Prüfsumme und Größe, bei Registry der Digest; Ed25519-Signatur über das gesamte Manifest. Fehlende Felder oder eine andere Verteilungsart werden abgelehnt. Das Kennzeichen „abwärtskompatibel“ stammt aus dem Verträglichkeits-Prüfskript (BET-035); Neubau: `release-add` übernimmt das Prüfergebnis, ein Überschreiben auf „abwärtskompatibel“ verlangt eine Bestätigung und wird protokolliert `[Vorschlag]`. Die Antwort auf `poll` enthält Manifest und Signatur.
Abnahme: Ein Manifest mit verändertem Feld wird vom Agenten abgelehnt (BET-154); ein Manifest ohne Prüfsumme bei Datei-Verteilung lässt sich nicht erzeugen; das Prüfergebnis „nicht abwärtskompatibel“ steht im Manifest.

**BET-138** · P0 · Status: offen · Getrennte Signaturschlüssel für Lizenz und Release
Ist: Ein Ed25519-Schlüssel signiert Lizenzantworten, Update-Antworten und Release-Manifeste; wer ihn stiehlt, kann Lizenzen fälschen und über den Update-Agenten Code auf Schul-Servern ausführen (BET-161). Offene Entscheidung der Quelle (Nr. 5): Release-Schlüssel getrennt vom Lizenz-Schlüssel führen. Neubau: zwei Schlüsselpaare — der Lizenzschlüssel liegt online auf dem Lizenzserver, der Release-Schlüssel signiert nur Manifeste und liegt offline (Build-System oder Hardware-Token); der Update-Agent pinnt den Release-Prüfschlüssel (BET-154); ein bewusster Schlüsselwechsel ist dokumentiert.
Abnahme: Ein vom Lizenzschlüssel signiertes Manifest wird vom Agenten abgelehnt; ein vom Release-Schlüssel signierte Lizenzantwort wird von der Instanz abgelehnt; der private Release-Schlüssel liegt nicht auf dem Lizenzserver (Prüfung der Server-Dateien).

**BET-139** · P1 · Status: Ist · Verteilung der Abbilder
Download vom Lizenzserver (gebaut): Das Abbild liegt im Release-Bestand (`LZ_RELEASE_DIR`); die Schule lädt mit Schlüssel (Kopfzeile `X-License-Key`) und Instanz-ID (`X-Instance-Id`); Lizenz muss aktiv oder abgelaufen sein, Schule und Server nicht gesperrt (sonst 403); 404 bei unbekannter Version, zurückgezogenem Release, Test-Kanal ohne Berechtigung oder fehlender Datei; nur sichere Dateinamen; jeder Abruf wird protokolliert (Version, Schule). Größe etwa 300 bis 600 MB je Schule und Update; ein Abbruch startet den Download neu (unkritisch, weil vorab geladen). Registry (nicht gebaut, nicht erprobt, keine Registry vorhanden): Abbild nur per Digest (`Abbild@sha256:…`), nie per Tag; optional nur ein erlaubtes Präfix (`UPDATER_ALLOWED_REGISTRY`); Schichten einzeln, Wiederaufnahme bei Abbruch; Zugang je Schule oder öffentlich lesbar mit Digest-Pflicht. Empfehlung der Quelle: jetzt Download; Registry, sobald mehr als etwa 10 Schulen aktiv sind oder der Lizenzserver die Last nicht trägt (Entscheidung offen, BET-216).
Abnahme: Download mit gültigem Schlüssel → Datei, SHA-256 und Größe stimmen mit dem Manifest; ohne Lizenz/gesperrte Schule → 403; zurückgezogene Version → 404; Dateiname mit `../` → 404.

**BET-140** · P0 · Status: Ist · Mindestversion, Zwischenschritte, Downgrade-Schutz
Ein Angebot entsteht nur, wenn die laufende Version die Mindestversion des Ziels erreicht. Sonst wird der höchste Zwischenschritt angeboten (gleicher Kanal, nicht zurückgezogen, größer als laufend, kleiner als das Ziel, Mindestversion ≤ laufend); gibt es keinen, kein Angebot. Ein Downgrade wird nie angeboten: Das Ziel muss größer sein als die laufende und (im Agenten) größer als die höchste je installierte Version.
Abnahme: Releases 1.0.0, 1.1.0 (Mindestversion 1.0.0), 1.3.0 (Mindestversion 1.1.0): laufend 1.0.0 → Angebot 1.1.0, nach der Installation 1.3.0; laufend 1.3.0 → kein Angebot für 1.1.0; manuelles Zurückstellen der Datenbank-Version auf 1.0.0 → der Agent lehnt 1.1.0 ab, weil die höchste je installierte Version 1.3.0 ist.

**BET-141** · P0 · Status: Ist · Release zurückziehen
Das Kennzeichen „zurückgezogen“ verhindert neue Angebote und lässt den Download mit 404 antworten; bereits installierte Server bleiben auf der Version. Nicht beschrieben im Altbestand: eine bereits geladene, dann zurückgezogene Version. Neubau: Der Agent verwirft das geladene Abbild, wenn die nächste Abfrage kein Angebot mehr enthält, und startet nicht; eine bereits begonnene Installation läuft zu Ende `[unklar: vom Betreiber zu bestätigen]`.
Abnahme: Release zurückziehen → nächste Abfrage liefert kein Angebot, Download 404; Agent mit geladenem Abbild startet nach dem Zurückziehen keine Installation und entfernt das Abbild; Server mit der zurückgezogenen Version laufen unverändert weiter.

### 15.2 Rollouts, Wellen, Termine

**BET-142** · P1 · Status: Ist · Rollout
Tabelle `upd_rollouts`; ein Rollout verbindet ein Release mit Zielgruppe, Wellen und Terminen.

| Feld | Standard | Grenze / Wirkung |
|---|---|---|
| Name | „Rollout“ | max. 120 Zeichen |
| Release | – | Pflicht |
| Status | `draft` | `draft`, `active`, `paused`, `aborted`, `completed` |
| Zielgruppe (`target_mode`) | `all` | `all` (alle Schulen), `tests` (nur Test-Schulen), `selected` (Liste, Pflicht) |
| Test-Schulen zuerst | ja | erste Welle sind Test-Schulen |
| Anteil der übrigen je Welle | 10 % | 0 bis 100; Welle = aufgerundeter Anteil der Restschulen |
| Wartezeit nach Welle | 24 Stunden | ≥ 0; nach der letzten gesunden Schule der Vorwelle |
| Wartezeit nach Test-Schulen | 0 Stunden | ≥ 0 |
| Zeitfenster | leer | Wochentage, Beginn, Ende, Zeitzone; überschreibt das Fenster der Schule |
| frühestens ab | leer | Angebot erst ab diesem Zeitpunkt |
| dringend | nein | BET-145 |
| Start (Termin) / Startfenster | leer / 6 Stunden (min. 1) | BET-144 |
| Verpasst-Regel | `ask` | `ask`, `catch_up`, `next_window` |
| manuell freigegebene Wellen | 0 | „Nächste Welle freigeben“ zählt +1 |
| Ansage | leer | max. 1000 Zeichen, die Schul-Administration sieht sie unter `/betrieb` |
| gestartet am | leer | erster Start; Ausgangspunkt der Wellen |

Statusübergänge: `draft`→`active` (Start; Startzeitpunkt wird beim ersten Start gesetzt); `active`→`paused` (Pause mit Grund, max. 200 Zeichen, Standard „vom Anbieter pausiert“; keine neuen Angebote); `paused`→`active` (Fortsetzen); `active`/`paused`→`aborted` (endgültig, neuer Rollout nötig); `active`→`completed`: im Altbestand definiert, aber von keinem Pfad gesetzt. Neubau: `completed`, sobald alle Zielschulen gesund auf der Zielversion sind `[Vorschlag]`.
Abnahme: Rollout ohne Release → abgewiesen; Zielgruppe `selected` ohne Schulen → abgewiesen; Pause mit Grund → kein Angebot mehr bis Fortsetzen; abgebrochener Rollout lässt sich nicht fortsetzen; Rollout, dessen Zielschulen alle gesund sind, steht auf `completed`.

**BET-143** · P1 · Status: Ist · Wellen, Tor und Fehlerstopp
Wortlaut/Regel: „erst Test-Schulen, dann X Prozent, der Rest nach Y Stunden; weiter nur, wenn alle gesund sind; jede Welle von Hand freigebbar.“ Zielschulen sind gebundene, nicht gekündigte, nicht gesperrte Schulen der Zielgruppe. Wellenbildung: Welle 1 Test-Schulen (bei „Test zuerst“ und Zielgruppe ungleich `tests`), Welle 2 aufgerundeter Anteil der übrigen, Welle 3 der Rest; die Reihenfolge ist stabil (Hash aus Rollout-Nummer und Schul-Kennung). Welle 1 öffnet mit dem Start. Eine spätere Welle öffnet, wenn alle nicht ausgeschlossenen Schulen der Vorwelle gesund auf der Zielversion sind und seit deren letztem Abschluss die Wartezeit vergangen ist. Ausgeschlossen sind Schulen mit „keine automatischen Updates“ oder ohne Meldung seit 3 Tagen (die Konstante 14 Tage des Altbestands wirkt nicht; gültig 3 Tage). Gesund: alle Server der Schule auf Zielversion oder neuer, keiner in Arbeit, kein Fehlerzustand. Fehler: mindestens ein Server im Zustand `error` oder `rolled_back` für diese Zielversion. Fehlerstopp: Ist eine Schule einer Welle im Fehler, öffnet keine spätere Welle; laufende Schulen werden nicht angehalten; „Nächste Welle freigeben“ öffnet die Welle trotzdem (auch bei früheren Fehlern, bewusst). Hinweise des Altbestands: Ein Rollout pausiert bei Fehlern nicht von selbst (es öffnen nur keine weiteren Wellen); pausierte Schulen bleiben „ausstehend“ und verzögern die nächste Welle, bis sie 3 Tage nicht gemeldet haben.
Abnahme: 10 Schulen (2 Test, 8 übrige, Anteil 10 %) → Welle 1 = 2 Test-Schulen, Welle 2 = 1 Schule, Welle 3 = 7; Welle 2 öffnet erst nach beiden gesunden Test-Schulen plus Wartezeit; Fehler einer Test-Schule → Welle 2 bleibt zu; „Nächste Welle freigeben“ öffnet sie; Schule ohne Meldung seit 4 Tagen zählt nicht als Hindernis.

**BET-144** · P1 · Status: Ist · Termine, Zeitfenster, verpasste Termine
Wunsch (16.10.2026): „es soll sein am 21.05. um 0 Uhr beispielsweise“ — ein konkretes Datum mit Uhrzeit, nicht ein Wochentag. Eingabe im Portal in Ortszeit (Europa/Berlin), Speicherung in UTC (Tabelle `upd_appointments`: Rollout, Schule, Server, Termin; `key_id` 0 = ganze Schule), Anzeige TT.MM.JJJJ hh:mm; Sommer- und Winterzeit werden berücksichtigt, eine durch die Umstellung nicht existierende Uhrzeit rutscht auf die nächste gültige. Vorrang: Termin des Servers (nur Strategie `per_server`) vor Termin der Schule vor Start des Rollouts; ohne Termin gilt das wiederkehrende Zeitfenster (Voreinstellung, „automatisch, sobald ein Update da ist“: Samstag 02:00 bis 05:00 Europa/Berlin; Wochentage 0 = Montag bis 6 = Sonntag; Ende vor Beginn = über Mitternacht; Beginn gleich Ende = ganzer Tag; Rollout-Fenster geht vor Schulfenster). Ein Termin ist offen von Termin bis Termin + Startfenster (Standard 6 Stunden) und bleibt offen, wenn die Schule bereits begonnen hat. Verpasst (Schule hat nicht begonnen, z. B. Server war aus): `ask` — im Portal „verpasst“, nichts geschieht automatisch, der Anbieter entscheidet; `catch_up` — sofort nachholen; `next_window` — nächstes Zeitfenster.
Abnahme: Termin 29.03.2026 02:30 Europa/Berlin (Zeit existiert nicht) → wirksam 03:00; Fenster Samstag 22:00 bis 02:00 → Sonntag 01:00 gilt als offen, Sonntag 03:00 nicht; Fenster 06:00 bis 06:00 → ganztägig offen; Termin verpasst mit `ask` → Markierung „verpasst“ im Portal und keine Installation; mit `catch_up` → Installation sofort nach dem Start des Servers.

**BET-145** · P1 · Status: Ist · Dringend, Vertrag, Modus, „Jetzt installieren“, Verschieben

| Option | Wirkung | Grenze |
|---|---|---|
| Dringend (Rollout, Sicherheitsupdate) | umgeht Zeitfenster, Verschiebung der Schule und „Verpasst“ | nicht die Wellen, nicht „frühestens ab“, nicht den Vertrag „nur manuell“ |
| Vertrag „nur manuell“ (`auto_update` = nein) | nur Angebot (`offer`), kein automatischer Start | wird durch „Jetzt installieren“ der Schule überschritten |
| Installationsmodus der Schule „manuell“ | nur Angebot, außer dringend oder „Jetzt installieren“ | Schalter unter `/betrieb` oder `UPDATER_MODE=manual`; nicht umschaltbar, wenn vertraglich festgelegt |
| „Jetzt installieren“ der Schule | umgeht Vertrag, Modus, Verschiebung, Verpasst und Zeitfenster | nicht die Wellen, nicht „frühestens ab“, nicht den Fehler einer früheren Installation |
| Verschieben durch die Schule | einmal je Version, 1 bis 7 Tage (längere Anfragen werden auf 7 Tage begrenzt); Zustand `postponed`, keine Installation | nicht bei dringend und nach „Jetzt installieren“ |

Vorgabe des Betreibers: Die Schule darf ein Update einmal um 1 bis 7 Tage verschieben, außer es ist als dringend (Sicherheit) markiert. Offene Entscheidung: ob „Jetzt installieren“ den vertraglichen Ausschluss automatischer Updates umgehen darf (BET-217).
Abnahme: Dringendes Update im Zeitfenster-fremden Moment → Installation sofort (ohne Wellen-Umgehung); Verschieben auf 10 Tage → gespeichert als 7 Tage; zweites Verschieben derselben Version → abgewiesen; dringend → Verschieben abgewiesen; Schule mit Vertrag „nur manuell“ erhält nur das Angebot und installiert nach „Jetzt installieren“.

**BET-146** · P1 · Status: Ist · Einstellungen je Schule
Tabelle `upd_school_settings` (Schlüssel: Gruppen-Kennung). Wunsch: „Die Schule stellt ein, wie sie updaten will“ — der Anbieter setzt die Strategie, die Schule wählt nur, wenn der Anbieter es erlaubt.

| Feld | Standard | Grenze / Wirkung |
|---|---|---|
| Test-Schule | nein | bekommt Updates zuerst, Zugang zum Test-Kanal |
| Automatische Updates | ja | Vertrag; nein = nur manuell |
| Kanal | `stable` | `stable` oder `test` |
| Strategie bei mehreren Servern | `rolling` | `simultaneous`, `rolling`, `per_server` (BET-148) |
| Gleichzeitig (bei `rolling`) | 1 | Server, min. 1 |
| Wartezeit zwischen Servern | 0 | Minuten ≥ 0, nach Abschluss eines Servers |
| Rang je Server | leer → 100 + Schlüssel-Nummer | ganzzahlig, niedriger zuerst |
| Schule darf wählen | nein | Wahl zwischen gleichzeitig und nacheinander (nicht bei `per_server`) |
| Zeitfenster | Samstag 02:00 bis 05:00, Europa/Berlin | Wochentage, Beginn, Ende |

Abnahme: Neue Schule hat die Standardwerte; „Schule darf wählen“ = nein → Wahl der Schule unter `/betrieb` abgewiesen (403); = ja → Wahl wirkt und erzeugt das Audit-Ereignis `update.strategy`.

**BET-147** · P1 · Status: Ist · Update-Kanäle und Test-Schulen
Zwei Kanäle: `stable` (Standard) und `test`. Ein Test-Release geht nur an Test-Schulen oder Schulen mit Kanal `test`; der Download eines Test-Releases ohne Berechtigung liefert 404. Test-Schulen erhalten Updates zuerst (Welle 1 aus BET-143). Die Test-Instanz „neu“ des Anbieters, die eine Kundenschule nachstellt, wird als Test-Schule geführt `[Vorschlag]`.
Abnahme: Test-Release für Schule mit Kanal `stable` → kein Angebot, Download 404; dieselbe Schule auf Kanal `test` → Angebot; Rollout `tests` erreicht nur Test-Schulen.

### 15.3 Mehrere Server je Schule

**BET-148** · P1 · Status: Ist · Strategien

| Strategie | Bedeutung | Regeln |
|---|---|---|
| `simultaneous` (gleichzeitig) | alle Server im selben Zeitfenster | keine Abstimmung; kurze Ausfallzeit |
| `rolling` (nacheinander, Standard) | höchstens k Server aktualisieren sich zugleich | k = min(Gleichzeitig; Anzahl Server − 1), nie alle Server; Reihenfolge nach Rang, dann Kennung; Wartezeit nach jedem fertigen Server; der Partner muss gemeldet (Meldung höchstens 10 Minuten alt), gesund und nicht angehalten sein |
| `per_server` | jeder Server hat einen eigenen Termin (Datum und Uhrzeit) | keine Abstimmung außer Halt bei Fehlern |
| ein Server | nur im Termin bzw. Fenster | Rolle „single“ |

Wortlaut des Betreibers: „gleichzeitig oder nacheinander oder … an dem Tag und an dem Tag“; „es kann auch sein, dass die 2 Server haben oder 5 oder 100“; „zuerst auf dem Schulserver und dann auf dem …“. Der nächste Server beginnt erst, wenn der vorige wieder gesund läuft. Begründungstexte der Abstimmung (Auswahl): „Platz frei, Gegenstelle online und gesund“; „Kein anderer Server ist online und gesund – das Update würde die Schule vom Netz nehmen.“; „Wartezeit von N Minuten nach dem vorigen Server.“
Abnahme: Test mit 1, 2, 3 und 5 Servern gegen eine simulierte Laufzeit: bei `rolling` mit k = 1 sind nie zwei Server gleichzeitig in einem besetzten Zustand; bei 2 Servern und Gleichzeitig = 2 ergibt sich k = 1; ist der Partner 11 Minuten nicht gemeldet, wartet der Server mit der genannten Begründung; `per_server` startet jeden Server an seinem Termin.

**BET-149** · P0 · Status: Ist · Wartungsfenster bei nicht abwärtskompatibler Migration
Kann ein Update alte und neue Version nicht gleichzeitig betreiben (`backward_compatible` = nein) und hat die Schule mehr als einen Server, gilt unabhängig von der Strategie „gleichzeitig im Wartungsfenster“ und das Portal zeigt einen Hinweis. Ablauf: Der erste Server (Leiter, niedrigster Rang) bereitet vor (`ready`) und wartet, bis alle anderen `ready` oder `held` sind; die übrigen bereiten vor und halten an, sobald alle Server bereit sind (Entnahme aus dem Lastausgleich, Dienst gestoppt, Zustand `held`); der Leiter installiert, wenn alle anderen angehalten sind; die übrigen installieren, sobald der Leiter gesund ist. Nur der Leiter migriert die Datenbank. Die Rückkehr mit Einspielen der Sicherung ist nur bei einem Server oder im Wartungsfenster erlaubt (BET-157).
Abnahme: 3 Server, Release mit nicht kompatibler Migration → Portal zeigt „Wartungsfenster“; zu keinem Zeitpunkt läuft alte und neue Version gleichzeitig gegen dieselbe Datenbank (Protokoll der Zustände); Leiter schlägt fehl → die angehaltenen Server starten nicht mit der neuen Version.

**BET-150** · P1 · Status: Ist · Schloss, hängender Server, Fehlerhalt
Jeder Agent fragt „darf ich jetzt?“; der Anbieter vermerkt die Freigabe sofort als „belegt“, kein zweiter Server bekommt sie gleichzeitig. Besetzte Zustände: `draining`, `backing_up`, `updating`, `verifying`, `held`. Hängend: ein belegter Server (außer `held`) länger als 90 Minuten ohne Zustandswechsel oder ohne Meldung seit mehr als 90 Minuten — die Schule wird angehalten, der Anbieter entscheidet im Portal („Erneut versuchen“ oder „Abbrechen“). Fehlerhalt: Ein Server im Zustand `error` oder `rolled_back`, der die Zielversion nicht erreicht hat, hält die Schule an. Andere Schulen laufen weiter.
Abnahme: Zwei Server fragen gleichzeitig → genau einer erhält `install`; Server 91 Minuten im Zustand `updating` → Schule angehalten und im Portal markiert; Zustand `rolled_back` auf Server 1 → Server 2 erhält kein `install`.

**BET-151** · P1 · Status: Ist · Entscheidung des Anbieters auf eine Abfrage
`POST /api/v1/updates/poll` (Antwort `{"result": …, "signature": …}`, Nonce-Echo). Die Entscheidung läuft in dieser Reihenfolge:

| Nr. | Prüfung | Ergebnis (`action`) | Grund |
|---|---|---|---|
| 1 | Lizenz nicht aktiv oder abgelaufen, Schule oder Server gesperrt | `none` | `license` (Agent meldet nichts) |
| 2 | kein Angebot (kein aktiver Rollout, Schule nicht in Zielgruppe, Release zurückgezogen oder anderer Kanal, „frühestens ab“ nicht erreicht, keine passende Version) | `none` | – |
| 3 | Welle noch nicht offen | `none` | `stage_closed` (durch dringend nicht umgangen) |
| 4 | auf diesem Server ist für diese Version ein Fehler gespeichert | `none` | `failed_before` (durch dringend nicht umgangen) |
| 5 | Vertrag „nur manuell“ und nicht „Jetzt installieren“ | `offer` | „Vertrag: nur manuelle Updates“ |
| 6 | Modus der Schule „manuell“, weder „Jetzt installieren“ noch dringend | `offer` | „Die Schule installiert Updates nur manuell.“ |
| 7 | von der Schule verschoben, nicht dringend | `prepare` | „Von der Schule verschoben“ |
| 8 | Termin verpasst, nicht dringend, nicht „Jetzt installieren“ | `prepare` | Begründung des Termins |
| 9 | nicht im Zeitfenster, nicht dringend | `prepare` | „Warten auf das Zeitfenster“ |
| 10 | mehrere Server | `install`, `prepare` oder `hold` | Begründung der Abstimmung (BET-148) |
| 11 | sonst | `install` | „Zeitfenster offen“ bzw. „Auf Wunsch der Schule/dringend“ |

Das Angebot enthält Manifest und Signatur, Begründung, Zeitfenster (Beginn, Ende, innerhalb ja/nein), Strategie, Anzahl Server, Ansage, dringend, versäumt. Eingaben des Agenten: Schlüssel 10 bis 64 Zeichen; Instanz-ID 1 bis 64; Knotenname 1 bis 40 (Buchstaben, Ziffern, Punkt, Unterstrich, Bindestrich; Standard `main`); Version max. 40; Zustand max. 14 Zeichen (länger → 422; unbekannte zulässige Zustände gelten als `idle`); Detail max. 300; Zielversion max. 20; Gesundheit ja/nein (Standard ja); Modus `auto`/`manual` (Standard `auto`); „Jetzt installieren“ ja/nein; Strategie-Wunsch `simultaneous` oder `rolling` (anderes → 422); „verschoben bis“ max. 40 Zeichen; Nonce 16 bis 64. Ändern sich Zustand, Version oder Zielversion eines Servers, entsteht ein Protokolleintrag. Bei einem einzelnen Server gilt Nr. 11 (Rolle „single“) direkt.
Abnahme: Je Nummer ein Test; Abfrage mit Zustand von 15 Zeichen → 422; gesperrte Schule → `none` mit Grund `license`; Antwort mit verändertem Nonce wird vom Agenten verworfen.

**BET-152** · P1 · Status: Ist · Zustände des Servers beim Update

| Zustand | Bedeutung | Meldung gesund |
|---|---|---|
| `idle` (aktuell) | nichts zu tun; oder keine Lizenz (Detail „Keine Lizenz eingetragen“) | ja |
| `downloading` | Version wird geladen und geprüft | ja |
| `ready` | Version liegt bereit, wartet auf Zeitfenster | ja |
| `postponed` | bereit, die Schule hat verschoben | ja |
| `manual` | Angebot wartet auf Freigabe | ja |
| `held` | Wartungsfenster, Dienst gestoppt (zählt als belegt) | ja |
| `draining` | aus dem Lastausgleich genommen | ja (besetzt) |
| `backing_up` | Sicherung vor dem Update | ja (besetzt) |
| `updating` | neue oder alte Version wird gestartet | ja (besetzt) |
| `verifying` | Gesundheitsprüfung läuft | ja (besetzt) |
| `healthy` | Version läuft und ist gesund | ja |
| `rolled_back` | alte Version läuft wieder | nein („ungesund“) |
| `error` | keine laufende gesunde Version; der Server bleibt aus dem Lastausgleich | nein |
| `waiting` | im Zustandskatalog des Anbieters, vom Agenten nie gesetzt | – |

Tabelle `upd_nodes` (ein Knoten je Server-Schlüssel): Knotenname (40), Instanz-ID (64), Version (40), Zustand (14), Detail (300), Zielversion (20), Gesundheit (Standard ja), Modus (`auto`/`manual`), Zähler „Erneut versuchen“, erste/letzte Meldung, Zustand seit.
Abnahme: Jeder Zustand ist im Portal mit deutschem Namen sichtbar; ein Server ohne Meldung seit mehr als 10 Minuten zählt in `rolling` nicht als Partner; Zustand `waiting` wird vom Agenten nie gemeldet (Test).

**BET-153** · P1 · Status: Ist · Erneut versuchen, Fehlerzustand und Protokoll
Ein Fehler (max. 300 Zeichen) wird gespeichert und blockiert diese Zielversion auf diesem Server (`failed_before`), bis der Anbieter „Erneut versuchen“ auslöst (Zähler +1, Zustand `idle`, Zielversion leer; der Agent vergisst den Fehler für alle Versionen). Fehlgeschlagene Versionen werden nie von selbst wiederholt. Protokoll `upd_events`: Art `node` (Zustand eines Servers), `rollout` (Start, Pause, Abbruch, Welle, Termin), `admin` (Anbieter-Aktion); Text max. 500 Zeichen; Anzeige im Portal: Rollout-Verlauf 40 Einträge, Server-Verlauf 300. Jeder Download wird protokolliert. Aufbewahrungsfrist des Protokolls: im Altbestand nicht angegeben `[unklar]`; Neubau: Frist festlegen (BET-106).
Abnahme: Fehlgeschlagene Installation → nächste Abfrage liefert `none` mit `failed_before`; nach „Erneut versuchen“ erhält der Server das Angebot wieder; ein Zustandswechsel erzeugt genau einen `node`-Eintrag; der 301. Eintrag eines Servers verdrängt ihn nicht aus der Datenbank, nur aus der Anzeige.

### 15.4 Update-Agent und Schul-Seite

**BET-154** · P0 · Status: Ist · Update-Agent: Aufgabe, Befehlsgrenze, Prüfregeln
Der Update-Agent ist ein kleiner Begleitdienst (eigener Container, Profil `updater`) ohne Netzwerkdienst nach innen. Er führt genau einen festen Auftrag aus: „Version X installieren“ (laden, sichern, Abbild tauschen, prüfen). Befehle, Skripte oder Adressen aus Antworten führt er nie aus. Die App selbst kann keine Updates ausführen und hat keinen Zugriff auf den Container-Dienst des Hosts; App und Agent tauschen nur Dateien im Datenordner aus (BET-158).

| Prüfung | Regel | Bei Verstoß |
|---|---|---|
| Antwort des Anbieters | Signatur gültig; Nonce, Instanz-ID und Knotenname stimmen | ignoriert, letzter Fehler gemerkt; falsch signiert zählt wie „Anbieter nicht erreichbar“ |
| Signatur des Manifests | Ed25519 über das kanonische Manifest mit dem gepinnten Anbieter-Schlüssel | Angebot abgelehnt |
| Produktkennung | genau die feste Konstante des Produkts | „Fremdes Produkt“ |
| Version | Form x.y.z | ungültig |
| Downgrade-Schutz | größer als laufend und größer als höchste je installierte Version | Ablehnung |
| Mindestversion | laufende Version ≥ Mindestversion | Ablehnung |
| Verteilung Datei | SHA-256 (64 Hex), sicherer Dateiname, Größe > 0 | ungültig |
| Verteilung Registry | Abbild-Muster, Digest `sha256` (64 Hex), nur per Digest, nur Abbilder mit dem konfigurierten Präfix (falls gesetzt) | ungültig / „Registry nicht erlaubt“ |
| Migrationsangabe | zwei Wahrheitswerte | ungültig |
| bereits gescheitert | Zielversion im Fehlerspeicher | keine Aktion |
| Schlüssel-Pinning | Fingerabdruck = erste 16 Hex des SHA-256 des Prüfschlüssels, im Zustand gespeichert; Änderung → Agent hält an (bewusster Wechsel: Zustandsdatei löschen) | Stopp |
| Adresse | nur https (Ausnahme: lokal mit beiden Entwicklungsschaltern) | Fehler |
| Anbieter nicht erreichbar | Zeitlimit 20 Sekunden | keine Änderung, nächster Takt |

Im Modus `production` sind Ersatz-Prüfschlüssel (`UPDATER_PUBKEY`) und unsichere Verbindungen (`UPDATER_ALLOW_INSECURE`, `UPDATER_DEV`) gesperrt (BET-012). Ein gesperrter oder gekündigter Schulstatus führt zu keinem Update und keinem Download.
Abnahme: Je Zeile ein Test gegen einen lokalen Lizenzserver mit Test-Schlüsseln; Antwort mit fremdem Knotennamen → ignoriert; Prüfschlüssel-Wechsel → Agent hält an und meldet es; Antwort, die einen Shell-Befehl enthält, löst keine Ausführung aus (Test mit präpariertem Feld); `UPDATER_PUBKEY` in `production` → Agent arbeitet nicht.

**BET-155** · P1 · Status: Ist · Konfiguration des Update-Agenten

| Variable | Standard | Einheit / Wirkung |
|---|---|---|
| `UPDATER_VENDOR_URL` | – (Pflicht) | Anbieter-Adresse, nur https |
| `UPDATER_PUBKEY_FILE` | fester Pfad im Container (mit Ausweichpfad) | gepinnter Anbieter-Prüfschlüssel, Pflicht; wird beim Bau des Agenten-Images eingetragen |
| `UPDATER_PUBKEY` | leer | Base64-Ersatz, nur ohne Datei und nie in `production` |
| `UPDATER_NODE` | `main` | 1 bis 40 Zeichen, Name des Servers im Rollout (gleich `SM_NODE_ID`) |
| `UPDATER_MODE` | `auto` | `auto` oder `manual` (manuell setzt nur Angebote) |
| `UPDATER_POLL_SECONDS` | 900 | Sekunden, min. 30; Abfrage-Rhythmus |
| `UPDATER_DRAIN_SECONDS` | 20 | Wartezeit nach Entnahme aus dem Lastausgleich |
| `UPDATER_HEALTH_TIMEOUT` | 300 | Sekunden, Gesundheitsprüfung insgesamt |
| `UPDATER_MIN_FREE_MB` | 2048 | Megabyte, Mindestplatz für den Download |
| `UPDATER_ALLOWED_REGISTRY` | leer | Präfix; leer = alle |
| `UPDATER_DATA_DIR`, `UPDATER_STATE_DIR`, `UPDATER_COMPOSE_DIR`, `UPDATER_HEALTH_URL`, `UPDATER_HOST_DIR` | Container-Pfade bzw. interne Adresse der App (`/healthz`) | Lizenzdateien (nur lesen), Plan, Status; Zustand und Downloads; Dienst der Schule; Gesundheit; Host-Ordner |
| `COMPOSE_PROJECT_NAME` | leer | Projektname |
| `UPDATER_ALLOW_INSECURE` + `UPDATER_DEV` | beide `1` | nur lokale Adresse, nur Entwicklung |
| `UPDATER_LOG_LEVEL` | `INFO` | Protokoll |

Feste Werte (nicht konfigurierbar): Gesundheit gilt nach 3 aufeinanderfolgenden guten Prüfungen im Abstand von 5 Sekunden; Verschiebung höchstens 7 Tage; Anbieter-Anfrage 20 Sekunden; Download 600 Sekunden; Wiederholung nach Fehler im nächsten Takt.
Abnahme: Agent ohne `UPDATER_VENDOR_URL` oder ohne Prüfschlüssel startet nicht; `UPDATER_POLL_SECONDS=10` wirkt als 30; `UPDATER_VENDOR_URL` mit `http://` → Fehler in `production`; Standardwerte durch Test bestätigt.

**BET-156** · P0 · Status: Ist · Installationsablauf

| Schritt | Regel | Zeit |
|---|---|---|
| 1. Vorbereiten (`prepare`) | Angebot prüfen (BET-154); Platz mindestens max(2048 MB; 2 × Dateigröße); Download; SHA-256 und Größe müssen stimmen; Abbild laden bzw. per Digest ziehen; alte Downloads entfernen | Download-Zeitlimit 600 s |
| 2. Last wegnehmen | Drain-Markierung schreiben; `/healthz/ready` meldet 503 (BET-167) | 20 s (entfällt bei zuvor angehaltenem Server) |
| 3. Sicherung | Sicherungsdienst mit Bezeichnung `vor-update-<Version>` (Datenbank und Dateien); Fehler → Update nicht gestartet, alte Version läuft (BET-162) | |
| 4. Neue Version starten | Dienst mit neuem Abbild neu erstellen; die App migriert beim Start | Fehler → Rückkehr (BET-157) |
| 5. Gesundheitsprüfung | Status ok, Datenbank ok, Startseite erreichbar, Version gleich Zielversion; 3 gute Prüfungen hintereinander | Gesamtlimit 300 s, Abstand 5 s |
| 6. Ergebnis | ok: Zustand `healthy`, Drain-Markierung entfernt, höchste installierte Version = Zielversion, Fehlerliste dieser Version gelöscht; nicht ok: Rückkehr | |

Jeder Schritt wird dem Anbieter gemeldet und steht unter `/betrieb` (letzte 30 Einträge; im Agenten-Zustand 60). Eine unterbrochene Installation (Agent beendet, Absturz) wird beim nächsten Start geprüft: gesund → abgeschlossen, sonst Rückkehr. Halt (nur Folgeserver im Wartungsfenster, BET-149): Drain-Markierung, 20 s, Dienst stoppen, Zustand `held`; Freigabe: Dienst starten, Drain-Markierung entfernen. Zeitpunkt der Installation: vereinbarter Termin bzw. Fenster, außerhalb der Unterrichtszeit.
Abnahme: Test mit simulierter Container-Laufzeit: Reihenfolge der Zustände `downloading`→`ready`→`draining`→`backing_up`→`updating`→`verifying`→`healthy`; Prüfsumme falsch → keine Installation und Fehler gemeldet; zu wenig Platz → Abbruch vor dem Download; Agent mitten im Schritt 4 beendet → nach Neustart Abschluss oder Rückkehr; Versionsanzeige `/healthz` = Zielversion.

**BET-157** · P0 · Status: Ist · Rückkehr nach fehlgeschlagener Installation

| Bedingung | Ergebnis | Zustand |
|---|---|---|
| alte Version startet und ist gesund; keine Migration oder Migration abwärtskompatibel | `done` (Datenbank bleibt) | `rolled_back` |
| Migration nicht abwärtskompatibel oder alte Version ungesund; Einspielen erlaubt (nur ein Server oder Wartungsfenster) und Sicherung vorhanden | Datenbank aus der Sicherung einspielen, Dienst starten, prüfen | `rolled_back`, wenn alte Version gesund, sonst `error` |
| sonst | `give_up` | `error` |

Bei `error` bleibt der Server im Drain (aus dem Lastausgleich) bis zum Eingreifen. Der Fehler (max. 300 Zeichen) wird gespeichert und blockiert die Zielversion bis „Erneut versuchen“ (BET-153); die Meldung geht an den Anbieter. Einspielen der Sicherung nur, wenn kein anderer Server dieselbe Datenbank gerade benutzt.
Abnahme: Test: Release 1.2.0 mit absichtlich fehlschlagendem Start → alte Version läuft wieder, Zustand `rolled_back`, Fehler im Portal; Release mit nicht kompatibler Migration und Startfehler bei einem Server → Datenbank wird aus `vor-update-<Version>` eingespielt; bei drei Servern ohne Wartungsfenster wird nicht eingespielt (`give_up`).

**BET-158** · P1 · Status: Ist · Abfrage-Rhythmus, Verschiebung, Dateien des Agenten

| Lage | Intervall |
|---|---|
| normal | 900 Sekunden (`UPDATER_POLL_SECONDS`), min. 30 |
| Angebot offen und Zustand `ready`, `postponed`, `waiting` oder `downloading` | 60 Sekunden |
| nach Start | sofort eine Abfrage |
| Fehler bei der Anfrage | nächster Takt |

| Datei im Datenordner | Inhalt | Schreiber |
|---|---|---|
| Lizenz-Schlüssel- und Zustandsdatei | Schlüssel, Instanz-ID | nur lesen |
| Plan-Datei | Verschieben, Modus, „Jetzt installieren“ mit Kennung (nach der Installation verbraucht) | App schreibt, Agent liest |
| Status-Datei | Zustand, Angebot, Fenster, Ansage, Verschiebung, Protokoll (30 Einträge), Fehler | Agent (Anzeige unter `/betrieb`) |
| Drain-Markierung (je Knoten) | Zeitpunkt der Entnahme | Agent |
| Zustandsdatei des Agenten (Zustandsordner) | höchste Version, Zustand, Zielversion, Fehlerliste, Verschiebungen, Protokoll (60 Einträge), laufende Installation, Fingerabdruck des Prüfschlüssels | Agent |
| Download-Ordner | nur das aktuelle Abbild | Agent |

Abnahme: Offenes Angebot im Zustand `ready` → Abfragen im 60-Sekunden-Takt; kein Angebot → 900-Sekunden-Takt; Plan-Datei der App mit „Jetzt installieren“ wird nach der Installation verbraucht; der Download-Ordner enthält nach einem Update nur noch das aktuelle Abbild.

**BET-159** · P1 · Status: Ist · Karte „Updates“ unter `/betrieb`
Sichtbar für Administration (`system.admin`; die Quelle nennt den Rollennamen nicht `[unklar]`). Inhalt: installierte Version und Stand des Update-Dienstes; anstehendes Update mit Versionsnotizen; Zeitfenster oder Termin in Ortszeit; Hinweis zur Datenbank-Änderung; bei mehreren Servern Reihenfolge und Hinweis; Ansage des Anbieters; Protokoll der Schritte. Aktionen: „Jetzt installieren“; „einmal verschieben“ (1 bis 7 Tage, nicht bei dringend); Umschalten auf „nur manuell“ (nicht, wenn vertraglich festgelegt); Strategie wählen (nur wenn der Anbieter es erlaubt). Audit-Ereignisse: `update.version_changed` (Versionswechsel beim Start), `update.postpone`, `update.install_now`, `update.mode`, `update.strategy`. Anrede „Sie“, Erklärungen nur über Hilfe-Symbole. Ist der Update-Dienst nicht gestartet, zeigt die Karte „Update-Dienst nicht aktiv“ (kein Fehler).
Abnahme: Lehrkraft ruft die Karte ab → 403; Administration: „einmal verschieben“ um 3 Tage → Status `postponed`, Audit-Ereignis `update.postpone` (ohne Inhalte); zweiter Versuch → abgewiesen; „Jetzt installieren“ bei dringendem Update ist nicht nötig, bei Vertrag „nur manuell“ löst es die Installation aus; Moduswechsel bei vertraglicher Festlegung → 403.

**BET-160** · P1 · Status: offen · Versionsanzeige und Veröffentlichungsprozess
Im Altbestand ist die Versionsanzeige `SM_APP_VERSION` ein Build-Argument (Standard `0.1.0`), und der Veröffentlichungsprozess (Images in einer Registry, Versionsnummern, signierte Releases) ist offen (CI baut Images, GHCR-Push nicht validiert). Neubau: Die Version kommt aus dem Release; ein Release-Lauf erzeugt Image, Manifest und Signatur ohne manuelle Schritte und trägt die Version in `/healthz`, `/api/v1/version` und die Statusseite ein. Fertige Images ersetzen den Bau auf dem Schul-Server (BET-022).
Abnahme: Ein Release-Lauf mit Version 1.4.0 erzeugt Image, Manifest und Signatur; `/healthz` der installierten Instanz meldet `1.4.0`; es gibt keinen Pfad, in dem eine Instanz „0.1.0“ meldet.

**BET-161** · P0 · Status: offen · Zugriff des Update-Agenten auf die Container-Steuerung
Risiko (Quelle): Der Agent braucht Zugriff auf den Container-Dienst des Hosts; das ist faktisch Root-Zugriff auf den Host. Gegenmaßnahmen im Ist: kleiner Agent, kein Netzwerkdienst, schreibgeschütztes Dateisystem, keine zusätzlichen Capabilities, nur Verbindung zum Anbieter, nur signierte Aufträge. Restrisiko: Diebstahl des Anbieter-Schlüssels (BET-138). Der Update-Dienst ist auf keinem Schul-Server eingespielt; die Entscheidung je Schule bleibt offen:

| Variante | Beschreibung |
|---|---|
| (Ist) Agent mit Container-Zugriff | wie oben |
| A | Zeitgesteuerter Dienst auf dem Host, der das Release holt, die Signatur prüft und die Anwendung neu startet (kein Container mit Zugriff) |
| B | Socket-Proxy, der nur nötige Teile freigibt (Schutz geringer, als es aussieht) |
| C | rootless Container-Laufzeit für die Schul-Installation |
| D | nur manuell: Agent ohne Zugriff, nur als Melder |

Abnahme: Je Schule ist die gewählte Variante schriftlich dokumentiert; für Variante D meldet der Agent Angebote und Zustand, ohne den Container-Dienst zu berühren (Prüfung der eingebundenen Pfade und Capabilities); für die Ist-Variante besteht eine Härtungs-Checkliste (Dateisystem schreibgeschützt, keine Capabilities, kein eingehender Port), die bei Inbetriebnahme abgehakt wird.

**BET-162** · P2 · Status: offen · Zustand „nicht gestartet“
Ist: Schlägt schon die Sicherung (Schritt 3) fehl, meldet der Agent `rolled_back`, obwohl kein Update lief. Der Zustand `waiting` steht im Katalog des Anbieters, wird vom Agenten aber nie gesetzt. Neubau: eigener Zustand „nicht gestartet“ (z. B. `not_started`) für Abbruch vor dem Tausch; `waiting` wird entweder gesetzt (Warten auf Partner oder Fenster) oder entfernt.
Abnahme: Sicherung schlägt fehl → Zustand „nicht gestartet“ mit Grund, die alte Version läuft, der Fehlerhalt der Schule (BET-150) greift nicht für diesen Zustand, sehr wohl aber „Erneut versuchen“; kein Pfad meldet `rolled_back` ohne Tausch.

**BET-163** · P2 · Status: Ist · Technische Namen als Konstanten
Der Produktname steht nur an einer Stelle der Konfiguration (`SM_APP_NAME`). Technische Kennungen sind davon getrennte feste Konstanten, je eine Stelle: Metrik-Präfix (`schulmanager_`), Cookie-Name, Image-Name, Produktkennung im Manifest (Altbestand `schulpuls`), Name des Lastverteilungs-Cookies, Pfadnamen. Alte Pfade (z. B. `/opt/schulpuls`) werden als Rückfall gelesen. Der Lastverteilungs-Cookie bleibt unverändert (der Proxy kennt nur einen Namen); bei einer Umbenennung wird nach einem Update jede Anmeldung einmal neu verteilt (kein Datenverlust). Fest eingetippte Produktnamen in PDF-Metadaten, User-Agent-Texten, Mail-Kopfzeilen und Rechnungen sind zu vermeiden. `[unklar: der endgültige technische Name wird im Neubau einmal festgelegt]`
Abnahme: Ein Test ersetzt `SM_APP_NAME` und prüft, dass in Oberfläche, PDF-Texten, Mails und Rechnungen kein fest eingetippter Produktname verbleibt; je technische Kennung genau ein Vorkommen im Quelltext.

### 15.5 Betrieb mit mehreren Servern (Hochverfügbarkeit)

Stand laut Quelle: Konzept und Checkliste; ein Betrieb mit zwei oder mehr Knoten wurde nie erprobt. Wunsch des Betreibers: „bei zwei Servern ist immer einer online“; „am besten die kriegen dann zwei Lizenzen für jeden Server“. Empfehlung (nicht entschieden): Mehrere Server je Schule erst anbieten, wenn der Probelauf (BET-169) einmal durchgespielt ist.

**BET-164** · P1 · Status: offen · Voraussetzungen für mehrere Knoten

| Punkt | Anforderung |
|---|---|
| Datenbank | gemeinsame PostgreSQL-Datenbank; SQLite ist für mehrere Knoten ausgeschlossen |
| Sitzungen, Anmeldesperren | in der Datenbank, jeder Knoten bedient jede Sitzung |
| Planungsdokument | BET-170 |
| Dateiablage | gemeinsamer Datenträger als `SM_FILES_DIR` (Netzlaufwerk), Schreibrechte für den Dienstbenutzer; Chat-Bilder liegen in der Datenbank |
| Hintergrundjobs | nur einmal (Leader, BET-165) |
| Live-Ereignisse, Aufträge | BET-166 |
| Lastverteiler | BET-168 |
| Schlüssel | gleiche `SM_SECRET_KEY` und `SM_ENCRYPTION_KEYS` auf allen Knoten |
| Lizenz | je Knoten eigener Schlüssel, eigene Instanz-ID, eigener Datenordner (Lizenz, Drain-Markierung, Austausch mit dem Agenten); nur die Dateiablage ist gemeinsam |
| Kennung | `SM_NODE_ID` je Knoten (z. B. `app1`, `app2`), `SM_HA=1`, Update-Agent je Knoten mit `UPDATER_NODE` (gleicher Name) |
| Migrationen | nur ein Knoten migriert; abwärtskompatibel (BET-034), sonst Wartungsfenster (BET-149) |

Abnahme: Zwei Knoten gegen eine PostgreSQL-Datenbank und einen gemeinsamen Dateiordner: Anmeldung an Knoten 1, Sitzung gilt an Knoten 2; Knoten 1 abgeschaltet → Anmeldung, Planänderung und Datei-Download über Knoten 2 funktionieren; SQLite mit `SM_HA=1` → Start bricht ab mit Meldung.

**BET-165** · P1 · Status: Ist · Leader-Sperre für Hintergrundjobs
Im Mehrknoten-Betrieb laufen Benachrichtigungen, Auto-Planer, Mail-Abruf, Ferienimport und Wartung (BET-068) nur auf dem Leader. Die Leader-Sperre ist eine Pacht in einer Systemtabelle mit 30 Sekunden Laufzeit; fällt der Leader aus, übernimmt ein anderer Knoten nach spätestens 30 Sekunden. Die Lizenzprüfung läuft auf jedem Knoten. Stand: mit SQLite getestet, gegen echtes PostgreSQL nicht.
Abnahme: Zwei Knoten: eine Wartungsstufe wird je Lauf genau einmal ausgeführt (Zähler gelöschter Zeilen nicht doppelt); Leader-Prozess beenden → anderer Knoten führt den nächsten Lauf innerhalb von 30 Sekunden plus Laufintervall aus; der Test läuft gegen PostgreSQL 16.

**BET-166** · P1 · Status: offen · Live-Ereignisse und Hintergrund-Aufträge über Knoten
Ist: Live-Ereignisse (Server-Sent Events) sind prozesslokal; Planänderungen anderer Knoten kommen erst beim nächsten Nachladen an; der Fortschritt eines Auftrags (z. B. Stundenplan-Berechnung) kommt nur vom startenden Knoten; Nachfragen müssen auf demselben Knoten ankommen. Neubau: Ereignisse laufen über die gemeinsame Datenbank (Relay) an alle Knoten, der Auftragsstatus liegt in der Datenbank, sodass jeder Knoten ihn liefert.
Abnahme: Eine Planänderung über Knoten 1 erscheint an einem Monitor, der an Knoten 2 hängt, innerhalb von 3 Sekunden `[Zielwert: Vorschlag]`; die Statusabfrage eines auf Knoten 1 gestarteten Generator-Auftrags über Knoten 2 liefert den Fortschritt.

**BET-167** · P1 · Status: Ist · Drain-Markierung und Bereitschaft
Der Agent setzt vor der Installation die Drain-Markierung des Knotens (Datei `drain-<Knoten>.flag` im Datenordner). Solange sie besteht, antwortet `/healthz/ready` mit 503 und der Lastverteiler nimmt den Server heraus; `/healthz` bleibt 200. Nach der erfolgreichen Installation wird die Markierung entfernt; bei `error` bleibt sie bis zum Eingreifen.
Abnahme: Markierung gesetzt → `/healthz/ready` 503, `/healthz` 200, neue Anfragen des Verteilers gehen an den anderen Knoten; Markierung entfernt → 200.

**BET-168** · P1 · Status: offen · Lastverteiler
Bindung je Nutzer an einen festen Knoten über ein Cookie, Gesundheitsprüfung über `/healthz/ready`, zwei Verteiler mit gemeinsamer Adresse (der Verteiler ist selbst ein Ausfallpunkt); Beispiel-Konfiguration liegt vor. Die Anfrage-Begrenzung der App (`SM_RATE_LIMIT`) zählt je Knoten (Speicher-Zähler): den Gesamtdurchsatz einplanen oder am Verteiler zusätzlich begrenzen. Der Name des Lastverteilungs-Cookies ist fest (BET-163).
Abnahme: Ein Nutzer bleibt über 20 Anfragen am selben Knoten; Knoten mit Drain-Markierung erhält keine neuen Nutzer; Ausfall eines Verteilers → der zweite übernimmt die gemeinsame Adresse (Probelauf, BET-169).

**BET-169** · P1 · Status: offen · Probelauf und Freigabe des Mehrknoten-Betriebs
Probelauf mit einer Test-Schule (Checkliste der Quelle): (1) PostgreSQL außerhalb der beiden Knoten (eigener Host oder verwalteter Dienst) mit Sicherungen dort; (2) gemeinsame Dateiablage als `SM_FILES_DIR` einbinden; (3) je Knoten eigene Umgebungsdatei mit gleichen Geheimschlüsseln und gleicher Datenbank-Adresse, aber eigenem `SM_NODE_ID` und `SM_HA=1`; (4) je Knoten eigener Lizenzschlüssel und Datenordner; (5) Lastverteiler mit Cookie-Bindung und `/healthz/ready`; (6) je Knoten Update-Agent mit `UPDATER_NODE`; (7) im Portal Strategie „nacheinander“ und Reihenfolge; (8) Tests: Knoten 1 abschalten (Anmeldung, Planänderung, Wiederanlauf), Update mit abwärtskompatibler Migration, Absturz eines Knotens während des Updates, Wartungsfenster mit nicht kompatibler Migration. Mehrserver-Betrieb wird Kunden erst nach erfolgreichem Probelauf angeboten.
Abnahme: Ein Probelauf-Protokoll mit Datum und Ergebnis je Test (1 bis 8) liegt vor; ohne Protokoll ist die Strategie `rolling` für Schulen mit mehr als einem Server im Portal nicht auswählbar `[Vorschlag]`.

**BET-170** · P1 · Status: Ist · Schutz vor verlorenen Planänderungen
Das Planungsdokument liegt je Prozess im Speicher und wird aus der Datenbank nachgeladen (höchstens alle 2 Sekunden bei Zugriff, sofort vor jeder Änderung). Im Mehrknoten-Modus (`SM_HA=1`) schreibt ein Knoten nur, wenn kein anderer inzwischen eine neuere Version gespeichert hat; sonst Antwort 409 „bitte erneut versuchen“. Die Prüfung läuft über eine Sperre in der Datenbank. Stand: mit SQLite getestet.
Abnahme: Zwei Knoten ändern gleichzeitig denselben Plan: genau eine Änderung gelingt, die andere erhält 409 und kann nach Nachladen erneut speichern; keine Änderung geht still verloren (Test gegen PostgreSQL 16).

**BET-171** · P0 · Status: offen · Erprobung des Update-Systems vor dem ersten Kunden
Nicht automatisch erprobt: echtes Docker (die Anbindung des Agenten wurde nie ausgeführt), echte Registry, echtes PostgreSQL, echte Knoten; getestet ist nur gegen eine simulierte Laufzeit (Version 1.1.0 ging durch, 1.2.0 scheiterte absichtlich und wurde zurückgerollt; Strategien mit 1, 2, 3, 5 Servern). Vor dem ersten Kunden: Rundlauf auf einer Test-Schule mit echtem Container-Dienst: erfolgreiches Update, absichtlich scheiternder Start (Rollback), Abbruch des Agenten mitten im Update (Wiederaufnahme), Ausfall des Lizenzservers während des Updates (Agent versucht es erneut, laufende Installation läuft zu Ende `[unklar: im Altbestand nicht beschrieben]`), Zurückziehen einer geladenen Version (BET-141).
Abnahme: Ein dokumentierter Rundlauf mit Datum und Version zeigt alle fünf Fälle bestanden, auf einem echten Container-Dienst; ohne diesen Nachweis wird der Update-Dienst keiner Kundenschule eingespielt.

---

## 16. Demo-Betrieb

Die Demo-Instanz des Anbieters (Modus `demo`, BET-006) dient der Vorführung: „damit man anderen Leuten zeigen kann, was hier abgeht“. Sie enthält ausschließlich erfundene Daten, hat eigene Datenbank, eigene Dateiablage, eigenes Geheimnis und eigenes Zertifikat und teilt nichts mit der Hauptinstanz (BET-002). Demo-Funktionen sind im Modus `production` serverseitig verweigert (BET-011). Konfigurationsvariablen: Kap. 3 (`SM_LOAD_DEMO`, `SM_DEMO_BACKGROUND`, `SM_DEMO_CLASSES_PER_GRADE`, `SM_DEMO_PUBLIC`, `SM_DEMO_ALL_ACCOUNTS`, `SM_DEMO_PASSWORD`).

**BET-172** · P1 · Status: Ist · Demo-Schule: Umfang und Erzeugung
Inhalt der Demo-Schule (alles erfunden): 99 Klassen mit 18 bis 29 Kindern, 169 Lehrkräfte, 2.644 Schüler/innen, 1.554 Stunden (alle verplant), 2 Standorte, Rhythmus-Beispiele (jede zweite Woche), Praxisklasse (z. B. 9P) mit Praxistag mittwochs ohne Unterricht, Berufsschul-Kooperationsklassen, die jeden Mittwoch zur Berufsschule gehen. Erzeugung: `SM_LOAD_DEMO=1` beim allerersten Start (Hintergrund, die Oberfläche ist sofort erreichbar; `SM_DEMO_BACKGROUND=0` = blockierend), Befehl `load-demo [--time-limit S] [--classes-per-grade N] [--no-accounts]`, in einen laufenden Stack über das Make-Ziel `demo`, in der Oberfläche unter Administration → System „Demo laden“ (ersetzt alle Daten; außerhalb von `production` ist die Eingabe des Schulnamens als Bestätigung nötig); Umfang `SM_DEMO_CLASSES_PER_GRADE` (Standard 14, Bereich 1 bis 23). Demo-Konten je Rolle: Schulleitung, Planung, Sekretariat, Lehrkräfte, Schüler/innen, Eltern, Monitor (`SM_DEMO_ALL_ACCOUNTS=1`: je ein Konto je Lehrkraft, Schüler/in und Elternhaus); Demo-Passwort `SM_DEMO_PASSWORD`, nie ausgegeben. Das Demo-Hinweisband ist im Modus `demo` und an Konten mit Demo-Kennzeichen sichtbar, sonst nie. Demo-Konten werden nie in einer Produktivinstanz verwendet.
Abnahme: Frischer Start mit `SM_LOAD_DEMO=1` im Modus `demo` → Oberfläche sofort erreichbar, Demo-Schule vollständig nach 30 bis 60 Sekunden (Richtwert der Vorschau), Zahlen wie oben (Toleranz je Zufallsgenerator festlegen); `load-demo` in `production` → Fehler ohne Datenänderung; „Demo laden“ ohne Schulnamen-Bestätigung → abgewiesen.

**BET-173** · P1 · Status: Ist · Nächtliches Zurücksetzen der Demo
Wunsch (12.10.2026): Die Demo wird jede Nacht neu aufgesetzt, mit Beispielinhalten passend zur aktuellen Woche. Ablauf: Ein Nachtjob um 03:30 Ortszeit setzt die Demo-Instanz neu auf (frische Datenbank, Demo-Schule, Beispielinhalte) und fährt sie automatisch wieder hoch; dasselbe geschieht nach jedem Aufspielen einer neuen Version. Beispielinhalte der aktuellen Woche: eine Klassenarbeit, Noten, Hausaufgaben mit Abgabe, Material, eine kranke Lehrkraft mit Vertretung, die Krankmeldung einer volljährigen Schülerin, eine Mitteilung der Schulleitung, Nachrichten. Am Wochenende zeigen die Seiten den nächsten Schultag. Persistente Konten: BET-176.
Abnahme: Eine Änderung vom Vortag (neue Nachricht, verschobene Stunde) ist nach 03:30 weg; die Beispielinhalte tragen Daten der laufenden Woche; `/healthz` der Demo meldet nach dem Reset „ok“; ein Reset nach einem Deploy erzeugt dieselben Beispielinhalte. `[unklar: Dauer des Resets und Verhalten offener Sitzungen — im Altbestand nicht beschrieben]`

**BET-174** · P1 · Status: offen · Ferienfeste Beispielinhalte
Befund: Die Demo-Klassenarbeit konnte in den Herbstferien nicht angelegt werden (Wartungsbedarf der Demo-Schuldaten). Neubau: Die Beispielinhalte werden an Ferientagen, Wochenenden und Feiertagen auf den nächsten Schultag gelegt (Datumstests über echte Schultage inklusive Ferien); eine Demo-Lehrkraft ohne Unterricht am Mittwoch ist als Absicht gekennzeichnet oder behoben (Frage des 11.10.2026, unbeantwortet).
Abnahme: Ein Reset an einem Ferientag, einem Samstag und einem Feiertag erzeugt jeweils Klassenarbeit, Hausaufgaben und Vertretung am nächsten Schultag; die Datumstests laufen mit Ferien- und Feiertagsdaten des Bundeslands.

**BET-175** · P0 · Status: Ist · Demo-Zugänge ausgeben
Wunsch (12.10.2026): „Du kannst so mit Demo-Accounts erstellen, die quasi die Funktion von normalen Accounts haben“, je Rolle (Schüler, Eltern, Sekretariat, Administration, Lehrkraft u. a.), um Stundenplan, Vertretung, Eigenarbeit, Hausaufgaben, Arbeitsmaterial, Einsenden, Nachrichten zwischen Konten und Newsletter zu zeigen — „pro Account“, ohne Einfluss auf den echten Betrieb. Umsetzung: 11 Demo-Zugänge, je Rolle einer, mit Kürzel-Präfix `dz-`; „Demo-Zugang ausgeben“ in der Benutzerverwaltung, nur für den Inhaber, nur im Modus `demo`. Zugangsdaten stehen nur in einer Datei, nie im Chat oder Log; jeder Zugang hat ein eigenes, zufälliges Passwort.
Abnahme: Inhaber gibt einen Zugang aus → Konto mit Präfix `dz-` und Zufallspasswort, Anzeige einmalig; ein Konto ohne Inhaber-Eigenschaft → 403; in `production` → 403; das Log enthält kein Passwort.

**BET-176** · P0 · Status: Ist · Persistenz bestimmter Demo-Konten über das Zurücksetzen
Die Demo-Zugänge (`dz-…`, Inhaber-Zugänge sowie Beta-Test-Zugänge, BET-185) überleben die nächtliche Zurücksetzung: Konto, Rolle, Passwort, Zuordnung zur Demo-Person und die Markierung „beobachtet“ (mit Ablaufdatum) werden nach dem Reset wiederhergestellt; die eingebauten Standardkonten bleiben gesperrt. Daten, die für die Auswertung gebraucht werden — Nachrichten an die Demo-Wunschbox (BET-186) und das Beobachtungsprotokoll (BET-183) —, gehen durch den Reset nicht verloren: Sie werden vor dem Reset gesichert bzw. in einem vom Reset ausgenommenen Bereich geführt (Ist: Sammelskript jede Minute, Sicherung vor dem Reset, Protokoll-Kopie als Datei). Wiederhergestellt wird auch nach einem Aufspielen einer neuen Version (Deploy: „11 Demo-Zugänge wiederhergestellt“).
Abnahme: Ein Wegwerfkonto `dz-test` mit Beobachtung wird angelegt, der Reset läuft → Konto besteht mit gleichem Passwort, Rolle und Beobachtung; ein Beobachtungs-Eintrag und eine Wunschbox-Nachricht vom Vortag sind nach dem Reset abrufbar; ein Standard-Demo-Konto lässt sich nach dem Reset nicht anmelden (403 „Konto gesperrt“).

**BET-177** · P1 · Status: offen · Wer Demo-Zugänge ausgeben darf
Wortlaut des Betreibers (12.10.2026): „soll einfach nur die Schule Demo-Accounts rausgeben können oder der, also ich, der Software-Inhaber“. Umgesetzt ist nur der Inhaber (nicht andere Administrations-Konten). Ob auch Schulen eigene Demo-Zugänge ausgeben dürfen, ist ein Widerspruch zur Umsetzung und offen (Zusammenhang BET-189).
Abnahme: Entscheidung (nur Inhaber / auch Schule) dokumentiert; Test passend: Administration ohne Inhaber-Eigenschaft ruft „Demo-Zugang ausgeben“ → 403 (falls „nur Inhaber“) bzw. 200 im Modus `demo` und 403 in `production` (falls „auch Schule“).

**BET-178** · P1 · Status: offen · Anmeldeseite ohne Rollen-Schnellknöpfe
Wortlaut (12.10.2026 14:16): „wenn man sich einloggt bei dem Schulmanager, dass dann da den Demo-Schul ausprobieren, rollen, wählen, ding Totaler Quatsch, das soll da gar nicht da so sein“. Die Knöpfe wurden entfernt; Beschreibungen vom 16.10.2026 (nicht vom Betreiber) nennen die Demo-Instanz wieder mit „Anmeldung über Rollen-Knöpfe ohne Passwort“. Spätere Aussage des Betreibers gilt: Die Anmeldeseite jeder Instanz hat keine Rollen-Schnellknöpfe; Demo-Zugang gibt es nur über ausgegebene Konten (BET-175). `[unklar: ob eine passwortlose Rollenwahl in einer rein öffentlichen Demo ohne Echtdaten gewünscht ist; vom Betreiber zu bestätigen]`
Abnahme: Die Anmeldeseite im Modus `demo` zeigt nur Benutzername, Passwort und die Anmeldedienste; ein Test sucht in Seite und Schnittstellen nach einer passwortlosen Rollenanmeldung und findet keine.

**BET-179** · P0 · Status: Ist · Demo-Schutz: Schreibzugriffe nur nach Erlaubnisliste
Stand 12.10.2026: In der Demo sind nur Passwörter, Zwei-Faktor-Anmeldung, Systemfunktionen und E-Mail-Konten der Demo-Konten gesperrt, alles andere frei (neue Konten, Klassen, Nachrichten, Abgaben). Spätere Regel (16.10.2026, überstimmt): Alles Schreibende ist gesperrt, außer ausdrücklich Erlaubtem. Zusätzlich gesperrt: Importe, Kompetenz-Import und -Verwaltung, Webhooks, Aufbewahrungsfristen, Anzeige abwesender Lehrkräfte (außenwirksame Einstellungen). Erlaubt bleiben die Vorführaktionen des Alltags (u. a. Stundenplan ändern, Vertretung erfassen, Krankmeldung, Nachrichten, Abgaben und Bewertungen, Klassenbuch, Kursraum-Inhalte). `[unklar: die abschließende Erlaubnisliste legt der Neubau fest]` Ein Test geht alle schreibenden Routen durch (im Altbestand 330).
Abnahme: Automatischer Test ruft im Modus `demo` jede schreibende Route mit einem Administrationskonto auf: alle nicht in der Erlaubnisliste → 403; eine neu hinzugefügte Schreib-Route ohne Eintrag in der Liste lässt den Test fehlschlagen; „Import starten“, „Webhook speichern“, „Aufbewahrungsfrist ändern“ → 403.

**BET-180** · P0 · Status: Ist · Demo ohne Außenwirkung
Die Demo versendet nichts nach außen: keine E-Mails, SMS oder Webhooks an echte Empfänger (E-Mails und SMS werden höchstens im Test-Postausgang angezeigt, und dieser nur mit `SM_DEV_OUTBOX`), keine Mail-Konto-Abrufe, E-Mail-Konten gesperrt, keine Importe. Der Test-Anmeldedienst ist im Modus `demo` verboten (Start bricht ab, BET-006). Keine echten personenbezogenen Daten in der Demo.
Abnahme: „Passwort vergessen“ in der Demo erzeugt keine Mail an eine externe Adresse; `SM_SSO_DEV_MOCK=1` im Modus `demo` → Start bricht ab; ein Netzmitschnitt der Demo während eines Rundgangs zeigt keine ausgehende SMTP-, SMS- oder Webhook-Verbindung.

**BET-181** · P0 · Status: Ist · Keine öffentlichen Konten mit bekanntem Passwort
Befund (12.10.2026): Standard-Demo-Konten mit öffentlich bekanntem Passwort waren aus dem Internet erreichbar (Warnung 12:53, Sperre 15:43). Regel für den Neubau: In einer aus dem Internet erreichbaren Instanz gibt es nie Konten mit bekanntem Passwort; eingebaute Standardkonten sind dort gesperrt; Demo-Zugänge haben individuelle Zufallspasswörter. Demo-Konten dürfen ihr Passwort und ihren zweiten Faktor nicht ändern, andere Konten (auch Administration) dürfen Demo-Konten nicht ändern (403). Das Demo-Passwort steht nie im Log oder Chat; Zugangsdaten gehören nur in eine Datei. In `production` sperrt der Start Konten mit dem Demo-Passwort (BET-013).
Abnahme: In der Demo schlägt die Anmeldung mit dem Standard-Demo-Passwort an allen eingebauten Konten fehl; Passwortänderung am Demo-Konto → 403; Administration ändert ein Demo-Konto → 403.

**BET-182** · P1 · Status: Ist · Ansichtskonto (Vorführkonto)
Wunsch (12.10.2026): „ein Profil ... was wie ein Restricted Admin funktioniert ... ein Admin, der alles angucken kann, aber nichts machen darf“. Umsetzung: Ansichtskonto (nur lesen), sieht alles wie die Schulleitung; der Server verweigert jede Änderung mit 403 (nicht nur die Oberfläche); auf jeder Seite das Banner „Ansichtskonto – nur lesen“; nur ausdrücklich erteilte Rechte dürfen ändern. In den Beta-Test-Zugängen heißt die Rolle „Zuschauer“ (BET-185).
Abnahme: Ein Ansichtskonto ruft alle schreibenden Routen auf → jeweils 403; das Banner erscheint auf jeder von 10 Stichprobenseiten; lesende Seiten der Schulleitung sind erreichbar.

**BET-183** · P0 · Status: Ist · Verstärkte Beobachtung von Test- und Demo-Konten
Wortlaut des Betreibers (16./17.10.2026): „mach mir eine betatester account der admin zugang hat aber alle actionen extrem stark geloget werden“; „damit er quasi jede Änderung erhält, wenn das Passwort von anderen Leuten ändert oder wenn er Einträge macht, dass alles gelockt werden soll, alle Seiten, die er öffnet, alles, was er abruft“; „das soll alles gelockt werden, falls er Mist baut“. Umsetzung (Betriebsanforderung; Funktion im Einzelnen: DAT): Merkmal „beobachtet“ je Konto, optional mit Ablaufdatum (in der Zukunft, sonst 422), gesetzt durch `users.manage` mit `watch.read`; protokolliert wird jede Anfrage, auch lesend (Zeit, Methode, Pfad, Status, Dauer, Adresse, Gerät, Sitzungs-Hash), bei Änderungen zusätzlich gesendete Daten und Vorher/Nachher-Werte; Passwörter, Codes, Tokens, Schlüssel und Dateiinhalte geschwärzt; Inhalte verschlüsselt (Körper max. 32 000 Byte, Textwert 4 000 Zeichen, Liste 200 Einträge, Kürzungsvermerk); Aufbewahrung 180 Tage (bei Kontolöschung sofort). Der Beobachtete sieht weder Menü noch Protokoll noch Kennzeichen und kann die Beobachtung auch als Administration nicht abschalten (Einsicht → 404); ein Konto beobachtet sich nicht selbst (409). Beobachtete Konten dürfen standardmäßig keine Administrationskonten anlegen oder Administrationsrechte vergeben (403, Ereignis `user.admin_grant_denied`); nur der Inhaber schaltet das ab. Einsicht: Seite „Beobachtete Konten“ (`/beobachtete-konten`) mit Zeitleiste, Filtern, Detailansicht und CSV-Export; nach dem Wunsch des Betreibers nur der Inhaber `[unklar: der Rechte-Katalog nennt zusätzlich die Schulleitung]`. Alle `dz-`-Zugänge (Inhaber- und Beta-Test-Zugänge) sind beobachtet, die Markierung übersteht den Reset (BET-176).
Abnahme: Ein beobachtetes Konto ruft 3 Seiten auf und ändert einen Wert → 4 Protokollzeilen, die Änderung mit Vorher/Nachher; Passwort-Feld im Anfrage-Inhalt ist geschwärzt; das Konto selbst erhält für die Einsichtsseite 404; ein Admin-Anlegen durch das beobachtete Konto → 403; nach dem Reset ist die Beobachtung der `dz-`-Konten wieder aktiv.

**BET-184** · P0 · Status: offen · Datenschutz-Vorbehalt bei der Beobachtung realer Personen
Die Beobachtung eines Beta-Testers verarbeitet personenbezogene Daten einer realen Person. Vor dem Anlegen sind Rechtsgrundlage, Zweck, Information der betroffenen Person und Speicherdauer (DSGVO) zu klären; die Information der Person erfolgt vor der ersten Anmeldung (Hinweis im Zugangsblatt). Offen: Ob „jede Anfrage“ bei beobachteten Konten auch Chat-Nachrichten erfasst und damit die Audit-Ausnahme für Chat-Nachrichten aufhebt. Neubau: Chat-Inhalte werden auch bei beobachteten Konten nie protokolliert (nur Metadaten ohne Text); die Fristen (API-Protokoll 90 Tage, Beobachtung 180 Tage) stehen in der Datenschutzerklärung des Anbieters bzw. der Schule. Ein Test-/Beta-Konto, das nicht mehr gebraucht wird (Konto `betatester` auf dem Hauptserver: behalten oder löschen), wird gelöscht.
Abnahme: Das Zugangsblatt eines beobachteten Kontos enthält den Hinweis auf die Protokollierung und die Frist; eine im Chat gesendete Nachricht eines beobachteten Kontos erscheint im Protokoll nur mit Pfad und Status, nie mit Text; die Datenschutzunterlage nennt 90 und 180 Tage.

**BET-185** · P2 · Status: Ist · Beta-Test-Zugänge für alle Rollen
Wunsch (17.10.2026): „Ich will, dass du dem auch noch Konten machst für Schüler, Lehrer und so, also alle anderen Demozugänge, dass der auch sieht, wie die anderen Zugänge aussehen und die Berechtigung checken kann“. Umsetzung: zehn Rollenkonten mit Präfix `dz-` (Schulleitung, Planer, Sekretariat, Lehrkraft mit Klassenleitung, Lehrkraft ohne Klassenleitung, Schüler/in minderjährig, Schüler/in volljährig, Eltern, Monitor, Zuschauer) plus ein Administrations-Konto des Beta-Testers ohne Recht, Administrationskonten zu vergeben; alle beobachtet (BET-183); die Demo-Personen entsprechen denen der Inhaber-Zugänge. Startpasswörter nur in einer Datei. Der Beta-Tester prüft damit Oberflächen und Berechtigungen.
Abnahme: Alle elf Konten melden sich an und zeigen die rollentypische Oberfläche (Stichprobe je Rolle); das Zuschauer-Konto kann nichts ändern (403); das Beta-Admin-Konto kann kein Administrationskonto anlegen (403); alle elf sind beobachtet.

**BET-186** · P2 · Status: Ist · Rückmeldekanal der Demo (Wunschbox)
Der Beta-Tester schreibt seine Rückmeldung („was geändert werden muss, was gut ist, was schlecht ist“) in der App an den Empfänger „Entwicklung (Demo-Wunschbox)“. Ein Sammel-Skript auf dem Server liest jede Minute die Nachrichten des Beta-Kontos und sichert sie vor dem nächtlichen Reset; eine Protokoll-Kopie entsteht jede Minute als Datei. Rückmeldekanäle außerhalb der App (Chat-Dienste) sind nicht Teil des Produkts. Die Entscheidung, ob das Sammel-Skript weiterläuft, ist offen; die Wunschbox wurde noch nicht durchgespielt.
Abnahme: Eine Nachricht an die Wunschbox um 23:00 Uhr ist nach dem Reset um 03:30 Uhr als Datei beim Inhaber abrufbar; die Wunschbox-Nachricht enthält nur Inhalte des Absenders; das Sammel-Skript lässt sich mit einem dokumentierten Befehl abschalten.

**BET-187** · P2 · Status: Ist · Testtag-Szenario
Wunsch (12.10.2026): „dann kannst du mir wieder einen Testtag machen, wo alles quasi gleichzeitig ist“. Ein Skript legt in Test- und Demo-Instanzen alles Zusammenspiel auf einen Tag, markiert mit „[Testtag]“ und mit einem Befehl entfernbar: Klasse 5a mit fünf Hausaufgaben (mit Abgabe), einer Klassenarbeit (Mathematik, 3. Stunde) und einem Test (Englisch, 5. Stunde) in echten Stunden, die Krankmeldung des Kindes durch das Eltern-Testkonto am Klausurtag (Nachschreiben nötig), eine mehrtägige Meldung eines zweiten Kindes mit Attest, Nachteilsausgleich (+15 Minuten, Wörterbuch), ein „fehlt“ im Klassenbuch, Lehrkraft-Zugang für die Mathematiklehrkraft. Das Skript lief lokal (Anlegen, zweiter Lauf, Entfernen), auf dem Hauptserver nicht; die Abnahme durch den Betreiber steht aus. Neubau: Daten relativ zur aktuellen Woche statt fester Kalenderwoche.
Abnahme: Anlegen erzeugt alle genannten Elemente, jedes mit „[Testtag]“; ein zweiter Lauf erzeugt nichts doppelt; Entfernen löscht genau die markierten Elemente (Zeilenzahlen aller anderen Tabellen unverändert); das Skript verweigert den Lauf in `production`.

**BET-188** · P3 · Status: offen · Simulation aller Vorgänge in der Demo
Wunsch (12.10.2026): „Alles soll simulierbar und jederzeit erzeugbar sein“, für jede Kontoart: Nachrichten senden, Postfächer, Newsletter, neue Stundenpläne, Änderungen, neue Klasse einrichten, Klasse fällt weg, Schüler wechseln Klassen, Schüler gehen oder kommen, Schülerchats live, Sicherheit. Ist: nur nächtlicher Neuaufbau, keine laufenden Simulationen. Neubau: Befehl oder Inhaber-Oberfläche (nur Modus `demo` und `development`) löst Simulationen aus; jede Simulation wirkt sichtbar auf die Demo-Konten.
Abnahme: Je genanntem Vorgang ein Simulationsaufruf mit sichtbarem Effekt (z. B. „Schüler wechselt Klasse“ → Stundenplan und Benachrichtigung des Kontos ändern sich); in `production` → 403.

**BET-189** · P3 · Status: offen · Demo bei Schulen und Trennung von Echtdaten
Wunsch (12.10.2026): Schulen sollen Demo-Accounts oder Demo-Klassen im normalen Schul-Account haben oder eine ganze Demo-Schule auf ihrem Server hosten können. Vorschlag (Claude): Demo-Betrieb strikt von echten Daten trennen (Demo-Kennzeichnung), damit eine Lizenz-Schule keine Demo-Daten sieht. Das widerspricht BET-011 (Demo-Funktionen im Echtbetrieb aus). Neubau-Weg, falls gewünscht: eine eigene Demo-Instanz je Schule (gleiches Image, Modus `demo`, eigene Datenbank) statt Demo-Daten in der Produktivinstanz. `[unklar: Entscheidung des Betreibers]`
Abnahme: Entscheidung dokumentiert; bei „eigene Demo-Instanz“: Die Demo-Instanz der Schule hat keine Verbindung zur Produktiv-Datenbank und andere Schlüssel (Trennungstest wie BET-001); die Produktivinstanz zeigt nirgends Demo-Daten.

**BET-190** · P2 · Status: Ist · Vorschau-Umgebung (Ausprobieren ohne eigene Installation)
Anleitung für Interessierte und Tester: die komplette App mit der Demo-Schule im Entwicklungsmodus ausprobieren (Test-Postausgang `/test-postausgang`, Test-Anmeldedienste mit dem Zusatz „(Test)“, nicht für echte Daten): im Browser über einen privaten Codespace (Adresse nur mit Konto des Hosters; stoppt nach 30 Minuten Inaktivität) oder lokal auf `localhost`; Befehl `preview` mit Reset-Option und Hintergrundbetrieb (Protokoll in der Vorschau-Datei); Vorschau-Administrator-Passwort über eine Umgebungsvariable bzw. Ausgabe des Skripts. Vorschau-Konten: `admin` (technisch, sieht keine Atteste), `schulleitung`, `planer`, `sekretariat`, drei Lehrkräfte (Klassenleitung mit Oberstufenkursen), vier Schüler/innen (minderjährig in 5a — Krankmeldung nur über Eltern; Praxisklasse mittwochs im Betrieb; volljährig in der Oberstufe — meldet sich selbst krank; mit Kursen einer anderen Klasse), `eltern` (zwei Kinder in 5a und 9P), `monitor` (Flur-Bildschirm Hauptstandort). Rundgang (Beispielschritte; im Altbestand 17 von 17 automatisch durchgespielt): Stundenplan verschieben, Ausfall einer Stunde mit Vorschau, Klasse nicht da, Live-Vertretung am Monitor, Krankmeldung durch Lehrkraft, Lehrkraft-Profil und Anträge, Kursräume, Postfach und Rundschreiben, Krankmeldung und Attest, Neue Klasse mit Zugangsdaten, Passwort-Reset, Test-Anmeldedienste, Anmelde-Richtlinien, Verwaltung (Sicherung, Wartung, Verlauf), Profil. Neubau: Keine persönlichen Links oder Vorschau-Passwörter im ausgelieferten Code; die Vorschau läuft im Entwicklungsmodus, die öffentliche Demo im Modus `demo` (die Modi bleiben getrennt; der Test-Anmeldedienst gibt es nur in der Vorschau).
Abnahme: Vorschau startet lokal mit der Demo-Schule in 30 bis 60 Sekunden und zeigt die Konten der Liste; `preview` mit Reset-Option setzt die Daten zurück; der Rundgang (alle genannten Schritte) läuft als automatischer Test grün (Zuschauer-Rundgang über 274 Adressen im Altbestand); ein Test findet im ausgelieferten Paket keinen persönlichen Link und kein Vorschau-Passwort.

---

## 17. Kapazitäts- und Speicherwerte je Schulgröße

Quelle: Speicher- und Lastkalkulation vom 12.10.2026 (Rechnung mit Annahmen) plus Messungen am Testserver und Lasttests. Gemessen sind nur die aktuellen Größen (Testserver mit 5.462 Konten) und die Lasttests; alles andere sind Schätzungen. Anlass (Wortlaut des Betreibers, 12.10.2026): „wie groß der Speicher … bei einem Jahr lang Nutzung … aussehen kann … wie groß zum Beispiel die Hausaufgabendateien werden und pro Schüler, pro Tag … wie man das minimieren kann, optimieren kann und die Auslastung auch auf dem Server minimieren kann“ und „ob die ganze Infrastruktur für tausende von Schülern wirklich funktioniert“. GB = 1.000 MB; „req/s“ = Anfragen je Sekunde.

**BET-191** · P1 · Status: Ist · Größenklassen und Annahmen der Kalkulation

| | Klein | Mittel | Groß |
|---|---|---|---|
| Schüler/innen (bis) | 1.000 | 2.500 | 5.000 |
| Lehrkräfte | 80 | 200 | 400 |
| Eltern (1,5 je Kind) | 1.500 | 3.750 | 7.500 |
| Konten gesamt | 2.580 | 6.450 | 12.900 |
| Klassen (je 25) | 40 | 100 | 200 |

Schuljahr: 38 Schulwochen = 190 Schultage. Testserver: 5.462 Konten, 14 Klassen je Jahrgang (zwischen Mittel und Groß). Nutzungsannahmen je Kopf: Abgaben 1,5 je Schüler und Woche, davon 40 % mit Datei (50 % Foto 2,5 MB, Spanne 1 bis 4 MB; 50 % PDF 0,8 MB, Spanne 0,2 bis 2 MB; Ø 1,65 MB); Unterrichtsmaterial 2,5 Dateien je Lehrkraft und Woche à 1,0 MB; Atteste 4 Fehlzeiten je Schüler und Jahr, 25 % mit Scan (Foto 2,5 MB, PDF 0,3 MB); Postfach: Lehrkraft 15, Schüler/in 1, Eltern 0,7 Nachrichten je Woche, 2 % mit 0,4-MB-Anhang, Antworten +50 %; Rundschreiben je Woche 4 / 8 / 15 (Ø 300 / 800 / 1.500 Empfänger, 30 % mit 0,4-MB-Anhang); Chat: 5 Nachrichten je Schüler/in und Schultag, 60 % Zweier-Chats, 40 % Gruppen (Ø 20 Mitglieder), 1,3 Geräte je Person; Chat-Bilder 0,2 je Schüler/in und Schultag, Ø 1,5 MB (größte Unsicherheit); Klassenbuch 6 Stunden je Klasse und Tag à 800 Byte; Fehlzeiten 25 Zeilen à 450 Byte und Noten 30 Zeilen à 150 Byte je Schüler/in und Jahr; Audit 220 Byte je Zeile; aktive Nutzer je Schultag: Schüler/innen 80 %, Lehrkräfte 95 %, Eltern 25 %; Verkehr je aktivem Nutzer (gzip): Schüler/in 35 Anfragen / 100 KB, Lehrkraft 180 Anfragen / 1 MB, Eltern 12 Anfragen / 50 KB; Sicherungen täglich 14, wöchentlich 8, monatlich 12.
Abnahme: Jede Annahme ist in der Betreiber-Dokumentation als „Annahme“ gekennzeichnet; nach 4 Wochen Pilotbetrieb sind Speicherzuwachs je Schüler/in und Woche, Anfragen je aktivem Nutzer und Anteil aktiver Nutzer gemessen und neben den Annahmen eingetragen.

**BET-192** · P1 · Status: Ist · Speicherbedarf Jahr 1 und Wachstum
Varianten: A = Standard ohne Chat-Bilder; B = Standard mit Chat-Bildern; C = optimiert (BET-199 bis BET-203) plus Löschkonzept. Datenbank-Aufschlag +15 % (SQLite-Freiseiten/WAL). Summe aus Dateien und Datenbank in GB:

| Jahr | Klein A / B / C | Mittel A / B / C | Groß A / B / C |
|---|---|---|---|
| 1 | 51 / 117 / 37 | 127 / 291 / 92 | 255 / 583 / 184 |
| 2 | 99 / 231 / 48 | 249 / 576 / 120 | 497 / 1.153 / 241 |
| 3 | 148 / 344 / 52 | 369 / 861 / 130 | 739 / 1.722 / 260 |
| 4 | 196 / 458 / 56 | 490 / 1.146 / 140 | 980 / 2.291 / 280 |
| 5 | 244 / 572 / 60 | 611 / 1.430 / 149 | 1.222 / 2.861 / 299 |

Einzelposten Jahr 1 (Variante A): Datenbank 2.900 / 7.200 / 14.400 MB; Dateien 47.626 / 119.057 / 238.108 MB, davon Abgaben 37.620 / 94.050 / 188.100 MB, Material 7.600 / 19.000 / 38.000 MB, Atteste 1.400 / 3.500 / 7.000 MB, Postfach-Anhänge 1.006 / 2.507 / 5.008 MB; Chat-Bilder (B) 57.000 / 142.500 / 285.000 MB; Chat-Schlüsselzeilen 2.159 / 5.397 / 10.794 MB, Chat-Text 276 / 689 / 1.378 MB; Audit 67 / 160 / 316 MB (0,3 / 0,7 / 1,4 Mio. Zeilen). Planversionen: Standard 300 Versionen, je 35 / 70 / 130 KB (gemessen: 15 Versionen, Ø 66 KB, höchstens 72 KB). Messung Testserver (12.10.): SQLite 3,3 MB bei 5.462 Konten, Dateiablage 764 KB (5 Dateien). Dateien wachsen linear, bis das Kontingent greift (200 MB je Schüler/in nach etwa 4 bis 5 Jahren); Abschlussjahrgänge werden nicht automatisch entfernt (BET-203).
Abnahme: Die Tabelle steht unverändert in der Betreiber-Dokumentation; ein Rechenmodell (Tabellenkalkulation) reproduziert die Jahr-1-Werte aus den Annahmen von BET-191 auf ±1 GB; nach Pilotbeginn werden die Jahr-1-Werte aus dem Zuwachs hochgerechnet und verglichen.

**BET-193** · P1 · Status: Ist · Dateien: Grenzen, Kontingente, Kennzahlen je Schüler
Obergrenzen (Betriebswerte, Variablen in Kap. 3 und BET-072): Upload 25 MB (`SM_UPLOAD_MAX_MB`), Beiträge 10 MB, Schüler-Dokumente 15 MB (nur PDF und Bild); Kontingent Lehrkraft 2.000 MB, Schüler/in 200 MB (nicht gelöschte Dateien zählen); daraus die harte Obergrenze der Dateiablage (berechnet): Klein 200 GB (Schüler/innen) und 160 GB (Lehrkräfte), Mittel 500 / 400 GB, Groß 1.000 / 800 GB. Keine Komprimierung, keine Deduplizierung; gelöschte Dateien werden nach 30 Tagen endgültig entfernt. Postfach: Nachricht einmal gespeichert, je Empfänger eine Teilnehmerzeile; Text max. 20.000 Zeichen, max. 10 Anhänge, max. 20.000 Empfänger, Frist 365 Tage. Chat: je Nachricht eine Zeile plus je Empfängergerät eine Schlüsselzeile; max. 400 Mitglieder, 10 Geräte je Person, Text höchstens 120.000 Base64-Zeichen; keine Aufbewahrungsfrist. Kursräume: max. 3.000 Einträge je Kanal, Abgabetext 50.000 Zeichen, 20 Anhänge. Kennzahlen je Schüler/in und Jahr (Variante A): 47,6 MB Dateien plus 2,9 MB Datenbank (≈ 1,33 MB je Woche, ≈ 0,27 MB je Schultag); Chat-Bilder (B) zusätzlich ≈ 57 MB; Abgabe-Fotos ≈ 79 % der Dateiablage (+0,1 Abgabedatei je Woche ≈ +6,3 MB je Schüler/in und Jahr; Fotos auf 1,25 MB halbiert ≈ −30 % Dateiwert); Chat-Schlüsselzeilen ≈ 89 % des Chat-Text-Speichers. Chat je Nachricht (Speicher / Upload): Zweier-Chat 0,5 / 0,3 KB, Kleingruppe 2,0 / 1,1 KB, Klassenchat 7,4 / 4,3 KB, Jahrgangschat (400 Mitglieder, Maximum) 99 / 57 KB; eine Nachricht im 400er-Chat entspricht ≈ 340 Zweier-Nachrichten; ein Gerätewechsel (Antwort 409 `devices_changed`) verdoppelt den Upload.
Abnahme: Upload über 25 MB → abgelehnt; Konto über Kontingent → abgelehnt (BET-072); eine Abgabe-Serie von 1.000 Fotos erzeugt in der Dateiablage genau die Summe der Dateigrößen (keine versteckte Vervielfachung); Chat-Nachricht in einer Gruppe mit 30 Mitgliedern erzeugt je Empfängergerät eine Schlüsselzeile (Zähler gleich Gerätezahl).

**BET-194** · P1 · Status: Ist · Sicherungsbedarf, Laufzeit und Offsite-Übertragung
Standard-Rotation 14 täglich, 8 wöchentlich, 12 monatlich (34 Voll-Archive, `BACKUP_KEEP_*`, BET-043); verschlüsselte Dateien lassen sich nicht komprimieren. Formel: (14 + 8 × 0,97 + 12 × a) × (Dateien + 0,75 × Datenbank), a = Auslastung der Monatsstände (0,54 / 0,77 / 0,85 / 0,89 / 0,91 in Jahr 1 bis 5).

| Sicherungsbedarf gesamt in GB | Klein A | Klein B | Klein C | Mittel A | Mittel B | Mittel C | Groß A | Groß B | Groß C |
|---|---|---|---|---|---|---|---|---|---|
| Jahr 1 | 1.415 | 3.266 | 36 | 3.538 | 8.166 | 90 | 7.077 | 16.332 | 179 |
| Jahr 3 | 4.646 | 10.931 | 50 | 11.614 | 27.327 | 126 | 23.229 | 54.654 | 252 |
| Jahr 5 | 7.859 | 18.570 | 58 | 19.646 | 46.423 | 145 | 39.293 | 92.847 | 290 |

(Variante C = inkrementell.) Laufzeit: gzip −6 auf unkomprimierbaren Daten ≈ 40 bis 80 MB/s; Mittel Jahr 1 (119 GB) ≈ 25 bis 50 Minuten, Groß (238 GB) ≈ 1 bis 1,5 Stunden plus Lese-Last. Offsite: ein Voll-Archiv von 119 GB je Nacht über 20 Mbit/s dauert ≈ 13 Stunden und schafft die Nacht nicht; inkrementell (restic, borg oder rsync mit `--link-dest`) ≈ 0,2 / 0,5 / 1,0 GB je Schultag (optimiert) bzw. 0,3 / 0,7 / 1,3 GB (Standard). Variante B ist praktisch nicht betreibbar: jedes Datenbank-Backup enthält die Chat-Bilder (70 bis 290 GB, jede Nacht, 34 Generationen).
Abnahme: Rechenprobe: Größe Mittel, Variante C, inkrementelle Nacht ≈ 0,5 GB überträgt über 20 Mbit/s in unter 10 Minuten; Voll-Sicherung von 119 GB hat dokumentierte Laufzeit unter 60 Minuten auf der Mindestausstattung (BET-196); die Anleitung weist die Backup-Medium-Größe je Größenklasse aus.

**BET-195** · P1 · Status: Ist · Verkehr, Spitzenlast und Bandbreite

| | Klein | Mittel | Groß |
|---|---|---|---|
| aktive Nutzer je Schultag | 1.251 | 3.138 | 6.275 |
| Anfragen je Schultag | 46.000 | 115.000 | 231.000 |
| Ausgehend je Schultag (API-JSON / Material-Downloads / Abgabenansicht Lehrkräfte), GB | 0,18 / 0,40 / 0,20 | 0,44 / 1,0 / 0,50 | 0,87 / 2,0 / 0,99 |
| Ausgehend je Schultag ohne / mit Chat-Bildern, GB | 0,8 / 2,5 | 1,9 / 6,2 | 3,9 / 12,5 |
| Eingehend je Schultag, GB | 0,5 | 1,3 | 2,7 |
| Ausgehend je Jahr ohne / mit Chat-Bildern, TB | 0,2 / 0,6 | 0,4 / 1,4 | 0,9 / 2,9 |
| Spitze Unterrichtsbeginn 07:30 bis 07:40 (60 % der Aktiven, ≈ 12 Anfragen je Sitzung), req/s | ≈ 40 | ≈ 100 | ≈ 190 |
| Spitze Pausen, req/s | ≈ 5 | ≈ 12 | ≈ 25 |
| gleichzeitige Live-Verbindungen (SSE; 40 bis 80 KB je Verbindung) | ≈ 600 | ≈ 1.500 | ≈ 3.000 |
| Bandbreite Spitze ausgehend ohne / mit Chat-Bildern, Mbit/s | 1,0 / 2,9 | 2,5 / 7,3 | 5,0 / 14,6 |
| einmalig je Deploy (Kaltstart-Cache 0,4 MB je Gerät), GB / Mbit/s Spitze | 0,26 / +3,4 | 0,64 / +8,5 | 1,3 / +17 |
| Mindest-Upload dauerhaft (mit Reserve), Mbit/s | 10 | 25 | 50 (Glasfaser) |

CPU-Richtwert: Ein App-Prozess schafft einfache authentifizierte JSON-Abfragen mit etwa 150 bis 300 req/s auf einem schnellen Kern, schwere Endpunkte (Klassenbuch, Planansichten, verschlüsselte Listen) deutlich weniger; Klein und Mittel liegen im Rahmen, Groß (190 req/s) an der Grenze eines Prozesses (`SM_WORKERS` bleibt 1). Schreiblast Chat: Groß ≈ 4,75 Mio. Nachrichten je Jahr × 13 Zeilen ≈ 62 Mio. Einfügungen je Jahr (≈ 0,3 Mio. je Tag), Spitze ≈ 20 Nachrichten/s × 13 Zeilen; ein einzelner SQLite-Schreiber reicht im Mittel, Bild-Uploads (5 MB) in derselben Datei sind ungünstig. Eine Planänderung zwischen 07:00 und 08:00 löst ein Live-Ereignis an alle aus und damit ein Neuladen (600 / 1.500 / 3.000 Anfragen in wenigen Sekunden, BET-202). Virenscan: 20 bis 60 MB/s, zusätzlich 1,5 bis 2 GB RAM (BET-071); Dateiverschlüsselung ≈ 1 GB/s mit AES-NI (vernachlässigbar).
Abnahme: Ein Lasttest mit dem Spitzenprofil der jeweiligen Größe (BET-198) erreicht die Spitzenwerte ohne Fehler; die Anleitung nennt Mindest-Upload je Größe; die gemessene Bandbreite eines Deploy-Kaltstarts liegt unter dem Spitzenwert der Tabelle.

**BET-196** · P1 · Status: Ist · Mindestausstattung je Größenklasse

| | Klein (≤ 1.000) | Mittel (≤ 2.500) | Groß (≤ 5.000) |
|---|---|---|---|
| CPU | 2 Kerne (4 Threads) | 4 Kerne, gute Einzelkernleistung | 6 bis 8 Kerne, starke Einzelkernleistung |
| RAM | 4 GB | 8 GB | 16 GB (+2 GB mit Virenscan) |
| SSD für 5 Jahre, Variante C | 256 GB (≈ 60 GB Daten) | 500 GB bis 1 TB (≈ 150 GB) | 1 bis 2 TB NVMe (≈ 300 GB) |
| ohne Optimierung (A, 5 Jahre) | 0,5 TB | 1 TB | 2 TB |
| mit Chat-Bildern (B, 5 Jahre) | 1 TB | 2 TB | 4 TB (nicht empfohlen) |
| Backup-Medium | 500 GB HDD/NAS + Offsite | 1 TB HDD/NAS (inkrementell) | 2 bis 4 TB NAS + Offsite |
| Datenbank | SQLite möglich, PostgreSQL empfohlen | PostgreSQL | PostgreSQL (zwingend) |
| Upload dauerhaft | ≥ 10 Mbit/s | ≥ 25 Mbit/s (Kabel/Glasfaser ≥ 50) | ≥ 50, besser 100+ symmetrisch |
| Spitzenlast | ≈ 40 req/s, 600 SSE | ≈ 100 req/s, 1.500 SSE | ≈ 190 req/s, 3.000 SSE (Grenzbereich) |
| Betrieb | Mini-PC genügt | Mini-PC/Tower-Server | Rechenzentrum/Hoster statt Heimanschluss |

Datenbank-Regel (E6): SQLite nur für kleine Schulen; PostgreSQL ab etwa 500 Konten, bei Mehrknoten-Betrieb, sobald die Datenbank über etwa 5 GB wächst, bei Chat-Bildern in der Datenbank oder vielen parallelen Schreibvorgängen (konsistenter Datenbank-Dump, Verbindungs-Pool statt Einzelverbindung); bei bis zu 5.000 Schüler/innen ist PostgreSQL zwingend (BET-030). Die untere Grenze der Installationsanleitung (2 vCPU, 4 GB RAM, 20 GB SSD; empfohlen 4 vCPU, 4 bis 8 GB, 40 GB, BET-017) gilt für Demo und Klein; ihre Angaben „bis ca. 1.000“ und „ca. 2.500 Schüler/innen“ bei gleichem Minimum widersprechen sich, die Tabelle oben (spätere Kalkulation) gilt.
Abnahme: Die Installationsanleitung enthält diese Tabelle; ein Lauf der Demo-Schule (≈ 2.600 Schüler/innen) auf der Mittel-Ausstattung besteht den Lasttest von BET-198; auf der Klein-Ausstattung mit PostgreSQL besteht das Klein-Profil.

**BET-197** · P1 · Status: Ist · Lasttest-Werkzeug und bisherige Messwerte
Ein Skript (nur Standardbibliothek) meldet N Demo-Konten an (`--anzahl`, Standard 10, zyklisch verteilt; `--gleichzeitig`, `--runden`; Make-Ziel `lasttest` mit `LASTTEST_ARGS`) und ruft je Sitzung und Runde parallel den Stundenplan der Woche (`GET /api/v1/me/week`), die Vertretung für heute und die Nachrichtenübersicht (`GET /api/v1/messages/conversations`) ab; Anmeldung und Abrufe werden getrennt gezählt. Ausgabe: Abrufe, Fehlerquote, p50, p95, Maximum je Seite und insgesamt. Exit-Code 0, wenn die Fehlerquote höchstens `--max-fehlerquote` (Standard 1 %) beträgt und keine Anmeldefehler auftraten, sonst 1. Das Passwort kommt aus `SM_DEMO_PASSWORD` und wird nie ausgegeben. Sicherheitsregel: standardmäßig nur `localhost`, `127.0.0.1`, `[::1]`; jede andere Adresse nur mit `--ich-darf` und nur gegen eine eigene Testinstanz mit Demo-Daten, nie gegen Produktiv- oder echte Schulinstanzen (es erzeugt Anmeldungen, Audit-Einträge und Last); ein falsches Passwort löst die Anmeldedrosselung aus (Lauf mit Anmeldefehlern statt Lastergebnis). Bisherige Messwerte (12.10.2026): Vor der Korrektur brach der Server bei etwa 100 gleichzeitigen Nutzern zusammen (Datenbank-Verbindungen waren erschöpft); mit 60 Nutzern 50 Anfragen/s ohne Fehler, p95 beim Senden einer Nachricht 1,2 s; nach der Korrektur lokal 150 gleichzeitige Nutzer ohne Fehler, Nachrichtenversand 3 bis 5 s. Ein echter Lauf des Skripts steht aus.
Abnahme: Lauf mit `--anzahl 10` gegen die lokale Demo → Exit 0 und Ausgabe mit p50/p95/Max; Lauf gegen eine fremde Adresse ohne `--ich-darf` → Abbruch vor dem ersten Aufruf; mit falschem Passwort → Exit 1 und Meldung „Anmeldefehler“; das Passwort erscheint nie in der Ausgabe.

**BET-198** · P1 · Status: offen · Lastziel und Abnahmelauf vor dem ersten Kunden
Wunsch des Betreibers (12.10.2026): Infrastruktur für „tausende von Schülern“, die gleichzeitig schreiben; Chatdaten verschlüsselt auf dem Server, schnell abrufbar, nur für berechtigte Personen; Frage, ob das „unglaublich langsam“ wird. Das Ziel „Tausende gleichzeitige Nutzer“ ist nur mit 150 lokal getesteten Nutzern belegt. Neubau: Vor dem ersten Kunden läuft je Größenklasse ein Abnahmelauf auf der Mindestausstattung (BET-196) mit PostgreSQL und dem Spitzenprofil von BET-195 (Klein ≈ 750, Mittel ≈ 1.900, Groß ≈ 3.800 Sitzungen im 10-Minuten-Fenster = 60 % der aktiven Nutzer, berechnet) einschließlich Schreibvorgängen (Nachrichten, Abgaben, Krankmeldungen). Zielwerte: Fehlerquote höchstens 1 %; 95-%-Antwortzeit lesender Aufrufe höchstens 1 s und beim Senden einer Nachricht höchstens 2 s `[Vorschlag, nicht bestätigt; Altbestand 3 bis 5 s]`.
Abnahme: Je Größenklasse ein dokumentierter Lauf (Datum, Hardware, Datenbank, Profil) mit Fehlerquote ≤ 1 % und den Zielwerten; Ausfälle des Laufs (Verbindungs-Pool, Zeitüberschreitungen) sind behoben und der Lauf wiederholt; der Lauf wird vor jedem größeren Ausbau mit denselben Parametern wiederholt.

**BET-199** · P1 · Status: offen · Inkrementelle Sicherung
Optimierung 1 der Kalkulation: Statt nächtlicher Voll-Archive inkrementelle Sicherung (restic, borg oder rsync mit `--link-dest`) für Datenbank-Dump und Dateiablage, Offsite ebenfalls inkrementell; Aufbewahrung 14 / 8 / 12 Stände bleibt. Wirkung ≈ −97 % Sicherungsplatz (BET-194).
Abnahme: Sicherungsbedarf Größe Mittel nach 12 Monaten ≤ 100 GB bei 119 GB Nutzdaten (Rechenwert 90 GB); tägliche Übertragung ≈ 0,5 GB; Wiederherstellung eines beliebigen der 34 Stände gelingt (Test-Restore, BET-049); der Notfallweg „Voll-Archiv“ bleibt verfügbar.

**BET-200** · P2 · Status: offen · Bilder vor dem Hochladen verkleinern
Optimierung 2: Fotos (Hausaufgaben, Atteste, Chat) werden im Browser vor dem Senden verkleinert (WebP, längste Kante höchstens 2048 Pixel). Wirkung −60 bis −80 % je Bild; Rechenmodell: Foto-Durchschnitt 1,25 MB statt 2,5 MB ≈ −30 % Dateiwert. Lesbarkeit von Schrift auf Hausaufgaben-Fotos bleibt erhalten.
Abnahme: Ein Foto von 4.000 × 3.000 Pixeln (4 MB) wird als WebP mit längster Kante 2.048 Pixel hochgeladen; der Durchschnitt über 50 Test-Fotos liegt bei höchstens 1,25 MB; ein Dokument mit 10 Punkt Schrift bleibt lesbar (Sichtprüfung durch eine Lehrkraft); PDF-Dateien bleiben unverändert.

**BET-201** · P1 · Status: offen · Chat-Speicher: Bilder als Dateien, schlanke Schlüsseltabelle
Optimierung 3: Chat-Bilder liegen als verschlüsselte Dateien in der Dateiablage statt als Blobs in der Datenbank (sonst enthält jedes Datenbank-Backup 70 bis 290 GB Bilder, BET-194); die Schlüsseltabelle (≈ 89 % des Chat-Text-Speichers) wird verschlankt (≈ −50 % Chat-Datenbank). Wunsch (12.10.2026): Chats sollen vor dem Senden komprimiert und beim Empfänger entpackt werden, damit der Server wenig Datenfluss hat; Befund: Textkompression lohnt nicht, der Wunsch ist nur teilweise erfüllbar (Bilder verkleinern: BET-200). Chat-Kontingente und Upload-Grenzen bleiben (BET-072). Datenschutz: Chat-Bilder weiterhin nur für Mitglieder lesbar (andere erhalten 404).
Abnahme: Ein Datenbank-Backup enthält keine Chat-Bild-Blobs (Größenvergleich vor/nach); die Chat-Datenbank ist bei gleichem Nachrichtenbestand höchstens halb so groß wie im Ist-Stand (Messung); ein Nicht-Mitglied erhält für ein Chat-Bild 404; das Bild wird vom Server nie im Klartext gespeichert.

**BET-202** · P2 · Status: offen · Caching und gestaffeltes Nachladen
Optimierung 4: Ein Live-Ereignis „Plan geändert“ löst heute bei allen verbundenen Geräten ein vollständiges Neuladen aus (Spitze 600 / 1.500 / 3.000 Anfragen in wenigen Sekunden). Neubau: Ereignisse betreffen nur die betroffenen Klassen, Lehrkräfte und Räume; Geräte laden gestaffelt (zufällige Verzögerung) nach; Zwischenspeicher (Entity-Tags) vermeiden unveränderte Übertragungen. Erwartete Wirkung −30 bis −50 % API-Verkehr.
Abnahme: Eine Planänderung an Klasse 5a löst das Neuladen nur bei Konten mit Bezug zu 5a aus (Zähler der Anfragen höchstens gleich der Zahl dieser Konten plus 10 %); unveränderte Ressourcen werden mit 304 beantwortet; die Anfragen nach einer Planänderung verteilen sich über mindestens 5 Sekunden `[Vorschlag]`.

**BET-203** · P2 · Status: offen · Aufbewahrungsfristen und Abgänger als Speicherhebel
Optimierung 5: Das Löschkonzept (DAT) und das Entfernen von Abschlussjahrgängen halten den Speicher bei Variante C auf 60 / 149 / 299 GB nach 5 Jahren (statt 244 / 611 / 1.222 GB ohne). Im Altbestand werden Abschlussjahrgänge nicht automatisch entfernt und Dateien wachsen linear bis zum Kontingent. Betrieb: Fristen aus BET-069 (z. B. Postfach 365 Tage, Schüler-Dokumente 400 Tage, weich gelöschte Dateien 30 Tage) sind wirksam; Abgänger werden über den Schuljahreswechsel in das Löschkonzept übergeben.
Abnahme: Simulation über 5 Schuljahre mit Löschkonzept und Abgängerübergabe liegt je Größenklasse höchstens bei den Werten der Variante C; nach dem Austritt eines Jahrgangs sinkt die Dateiablage um den Anteil dieses Jahrgangs (Messung).

**BET-204** · P2 · Status: Ist · Last von Lizenz- und Update-Server (berechnet)
Lizenzprüfungen: je Server 96 Ping-Anfragen (alle 15 Minuten) plus 1 ausführliche Prüfung je Tag = 97 Anfragen; bei N Schulen mit je 2 Servern 194 × N je Tag (100 Schulen ≈ 19.400 je Tag ≈ 0,22 je Sekunde) — unkritisch für einen kleinen Server, die Last liegt in der Verfügbarkeit (BET-085). Update-Abfragen: im Normalbetrieb alle 15 Minuten, bei offenem Angebot jede Minute. Download: 300 bis 600 MB je Schule und Update, mit Wellen verteilt; für 10 Schulen gleichzeitig ≈ 3 bis 6 GB je Release; Registry statt Download ab etwa 10 aktiven Schulen (Entscheidung BET-216).
Abnahme: Ein Test mit 100 simulierten Schulen à 2 Servern über 24 Stunden Zeitraffer erzeugt keine Antwort mit 429 oder 5xx; die Download-Last einer Welle mit 10 Schulen belegt die Bandbreite des Lizenzservers nicht dauerhaft über 80 % `[Vorschlag]`.

**BET-205** · P2 · Status: Ist · Hinweise für Betrieb am Heimanschluss
Für Schulen oder Betreiber, die ohne Rechenzentrum arbeiten: unterbrechungsfreie Stromversorgung und Dateisystemprüfung nach Stromausfall, SMART-Überwachung der Datenträger, Stromverbrauch etwa 15 bis 40 W (≈ 130 bis 350 kWh je Jahr); Erreichbarkeit über feste Adresse oder dynamischen DNS; bei CGNAT oder DS-Lite ist keine Portfreigabe möglich (Tunnel oder Hoster-Proxy; dann Auftragsverarbeitung prüfen, der Verkehr läuft dauerhaft durch den Tunnel); Ausfallsicherheit „Kaltreserve“ = Offsite-Sicherung plus zweite Maschine (Wiederanlauf BET-048). Netzfreigaben im Router ändert niemand ohne ausdrückliche Zustimmung des Betreibers. Groß-Schulen (≈ 5.000 Schüler/innen) gehören in ein Rechenzentrum (Entscheidung BET-209).
Abnahme: Nach hartem Beenden des Containers (simulierter Stromausfall) startet die Instanz, die Datenbank besteht die Integritätsprüfung und die letzten bestätigten Schreibvorgänge sind vorhanden; die Betreiber-Anleitung enthält die genannten Punkte.

---

## 18. Offene Punkte und Entscheidungen des Betreibers im Bereich Betrieb

Alle Punkte dieses Kapitels haben `Status: offen`. Die Entscheidung trifft der Betreiber; Empfehlungen des Berichts vom 16.10.2026 (E1 bis E10) und der Update-Dokumentation sind keine Entscheidungen. Bis zur Entscheidung gilt der jeweils genannte Ist-Stand. Kein Punkt wird von einem Assistenten entschieden oder ausgeführt (Server-Umstellungen, Deploys und Zugriffe auf Server nur mit ausdrücklicher Freigabe des Betreibers).

**Entscheidungsübersicht**

| Nr. | Thema | Empfehlung bzw. Ist | Anforderung |
|---|---|---|---|
| E1 | Hauptinstanz bleibt Vorführung (`demo`); erste echte Schule bekommt eigene Instanz im Modus `production` | Empfehlung, nicht ausgeführt | BET-003 |
| E2 | Lizenz- und Preismodell | Jahreslizenz je Schule, nach Schülerzahl gestaffelt; Probierversion mit 25 Konten | BET-135, BET-095 |
| E3 | Hosting-Angebot | zuerst durch den Anbieter gehostet | BET-206 |
| E4 | Support | E-Mail werktags | BET-207 |
| E5 | Verträge | EULA, AV-Vertragsmuster, Haftung | BET-208 |
| E6 | Datenbank | PostgreSQL ab etwa 500 Konten | BET-030, BET-196 |
| E7 | Erst-Admin-Übergabe | Einrichtungslink mit Ablauf oder Datei | BET-039 |
| E8 | Pilotschule | kleine Schule, Untis- oder SchILD-Export | BET-211 |
| E9 | Weißlabel | technisch möglich, Lizenzfrage offen | BET-212 |
| E10 | Direktimporte | nach Pilotschule; CSV deckt bis dahin ab | Import-Kapitel (INT) |
| – | Hosting großer Schulen | Rechenzentrum statt Heimanschluss | BET-209 |
| – | Hosting des Lizenz- und Update-Servers | Heimserver vorerst; Hoster bei echten Kunden | BET-210 |
| – | Code-Schutz, EULA, Patent | Entscheidung offen | BET-213 |
| – | Update-Verteilung Download oder Registry | Download jetzt | BET-216 |
| – | Zugriff des Update-Agenten auf die Container-Steuerung | Varianten A bis D | BET-161 |
| – | Getrennte Signaturschlüssel | Empfehlung der Quelle | BET-138 |
| – | Zwei-Knoten-Betrieb als Produktmerkmal | Konzept, nie erprobt | BET-221, BET-169 |
| – | Zahlungsanbieter und automatische Pause bei Verzug | inaktiv bzw. aus | BET-129, BET-219 |
| – | Vereinheitlichung der Kulanzbegriffe | zwei Begriffe | BET-218 |
| – | Verlängerung bei abgelaufenem Abo | ab altem Ende | BET-123 |
| – | Subdomain je Schule, zentraler Anmeldepunkt, mehrere Schulen je Konto | zurückgestellt | BET-004, BET-005 |
| – | Demo: Zugangsausgabe, Rollen-Knöpfe, Demo bei Schulen | uneinheitlich | BET-177, BET-178, BET-189 |
| – | Datenschutz der Beobachtung realer Personen | zu klären | BET-184 |
| – | vollständiger Restore-Rundlauf, getrennte Datenbank-Benutzer | offen | BET-050, BET-037 |

**Zuordnung der Auffälligkeiten des Altbestands (Lizenz, Zahlungen, Updates)**

| Nr. | Befund | Anforderung |
|---|---|---|
| 1 | Verlängerung rechnet bei abgelaufenem Abo ab dem alten Ende | BET-123 |
| 2 | Sperrbefehl liegt ungeschützt in der Zustandsdatei | BET-077 |
| 3 | Verlust der Zustandsdatei: neue Instanz-ID; Sperrgeheimnis nicht erneut abholbar | BET-076, BET-077 |
| 4 | Konstante „Schule gesehen“ 14 Tage wirkt nicht, wirksam sind 3 Tage | BET-143, BET-220 |
| 5 | Rollout pausiert bei Fehlern nicht automatisch | BET-143, BET-220 |
| 6 | Manuell freigegebene Welle öffnet auch bei Fehlern früherer Wellen | BET-143, BET-220 |
| 7 | Rollout-Status `completed` wird nie gesetzt | BET-142 |
| 8 | „Jetzt installieren“ umgeht den Vertrag „nur manuell“ | BET-145, BET-217 |
| 9 | Ein Schlüssel signiert Lizenz, Update und Manifest | BET-138 |
| 10 | Pausierte Schulen bleiben „ausstehend“ und verzögern Wellen | BET-143, BET-220 |
| 11 | Rechnungslauf legt nach fehlgeschlagener Zahlung erneut eine Rechnung an | BET-124, BET-219 |
| 12 | Ping überträgt keine Zähler (Werte bis 24 Stunden alt) | BET-078 |
| 13 | GoCardless-Nachrichten ohne Zeitprüfung | BET-127 |
| 14 | Rechnungsnummer = interne ID, kein Steuerausweis | BET-130, BET-131 |
| 15 | Download-Aufbewahrung im Agenten ohne Wirkung | BET-158, BET-220 |
| 16 | Ein gemeinsames Portal-Passwort, keine Rollen | BET-108 |
| 17 | Schülergrenze nur Warnung; Durchsetzung der Kontengrenze unklar | BET-090 |
| 18 | Zustand `waiting` wird nie gesetzt | BET-162 |
| 19 | Fehlgeschlagene Sicherung meldet `rolled_back` | BET-162 |
| 20 | Zählfehler bleiben still | BET-078 |
| 21 | Zwei Kulanzbegriffe nebeneinander | BET-125, BET-218 |

**BET-206** · P1 · Status: offen · Entscheidung E3: Hosting-Angebot
Empfehlung: zunächst durch den Anbieter gehostet (weniger Support, einheitliche Updates), später Selbstbetrieb für Schulen mit eigener IT. Ein gehosteter Betrieb braucht einen Auftragsverarbeitungsvertrag, ein Rechenzentrum in Deutschland (Zertifizierung und Vertragswerk sind Aufgabe des Betreibers, die Software liefert die Beschreibung der technisch-organisatorischen Maßnahmen und Vorlagen) und ein Wartungsfenster. Gehostet heißt weiterhin: eine Instanz je Schule (BET-001), eigene Subdomain (BET-004). Schulen ohne IT-Kenntnis erreichen den Betrieb nur so (BET-028).
Abnahme: Die Entscheidung (gehostet zuerst: ja/nein) ist schriftlich dokumentiert; bei „ja“ liegen AV-Vertragsmuster, Standort des Rechenzentrums in der Datenschutzunterlage und Wartungsfenster vor, und der Trennungstest von BET-001 ist für zwei gehostete Test-Schulen bestanden.

**BET-207** · P1 · Status: offen · Entscheidung E4: Support
Empfehlung: Support per E-Mail an Werktagen mit Reaktion binnen eines Werktags; Fehler werden mit Fehlernummer gemeldet (BET-062); Wartungsfenster nachmittags; Notfallkontakt für Ausfälle am Schultag früh; Telefon oder Bereitschaft offen. Das Wartungsfenster der Update-Verwaltung (Voreinstellung Samstag 02:00 bis 05:00, BET-144) ist mit dem Support-Fenster abzustimmen.
Abnahme: Supportbedingungen (Kanal, Zeiten, Reaktionszeit, Notfallkontakt) stehen im Betreiber-Paket (BET-214); die Fehlermeldung der App nennt Fehlernummer und Supportweg; die Frage „Telefon/Bereitschaft“ ist beantwortet.

**BET-208** · P0 · Status: offen · Entscheidung E5: Verträge und Rechtsunterlagen
Zu erstellen und von einer Anwältin oder einem Anwalt mit Schulrecht zu prüfen: Lizenzvertrag/EULA, Muster eines Auftragsverarbeitungsvertrags, Haftung, Datenschutzvereinbarung mit dem Lizenzserver (BET-081), Support-Vereinbarung; juristische Prüfung der Datenschutz-Vorlagen (Verzeichnis der Verarbeitungstätigkeiten, technisch-organisatorische Maßnahmen, Datenschutzhinweise; REH).
Abnahme: Die Unterlagen liegen unterschrieben bzw. beschlossen vor; das Betreiber-Paket verlinkt sie; die Datenschutz-Vorlagen tragen den Vermerk „geprüft am …“.

**BET-209** · P1 · Status: offen · Hosting für sehr große Schulen
Empfehlung (12.10.2026): Für eine große Schule (etwa 5.000 Schüler/innen) ein Rechenzentrum oder einen Hoster statt eines Heimanschlusses (Spitzenlast ≈ 190 req/s im Grenzbereich eines Prozesses, Upload ≥ 50, besser 100 Mbit/s symmetrisch; BET-195, BET-196). Entscheidung und Anbieterwahl offen.
Abnahme: Für Größe Groß ist ein Hosting-Ziel gewählt und der Abnahmelauf von BET-198 dort bestanden.

**BET-210** · P0 · Status: offen · Hosting und Ausfallsicherheit des Lizenz- und Update-Servers
Ist: Lizenz- und Update-Server laufen vorerst auf einem einzelnen Heimserver (Ausfallpuffer der Instanzen 7 Tage Bestätigung plus 14 Tage Kulanz, BET-085); Strom- oder Internetausfall macht ihn unerreichbar; frühere Ausfälle abends hatten ihre Ursache im Router (Kindersicherung), nicht im Server. Auf demselben Rechner liefen fremde Dienste mit (Ressourcen und Angriffsfläche geteilt; inzwischen gestoppt). Für Updates ist ein Ausfall unkritisch (Agenten versuchen es erneut), für die Lizenzprüfung nur über den Puffer. Empfehlung: bei echten Kunden ein eigener kleiner Server beim Hoster in Deutschland oder der EU, ohne fremde Dienste; Überwachung (Erreichbarkeit, Zertifikat), Sicherung (BET-105), dokumentierte Wiederanlaufzeit. `[unklar: Entscheidung und Zielwert der Wiederanlaufzeit]`
Abnahme: Ausfalltest: Lizenzserver 24 Stunden abgeschaltet → alle Test-Instanzen bleiben ohne Funktionsverlust in `valid`/`warning`; Wiederanlauf aus der Sicherung auf einem neuen Server ist mit gemessener Dauer dokumentiert; auf dem Server laufen keine fremden Dienste.

**BET-211** · P1 · Status: offen · Entscheidung E8: Pilotschule und Abnahmeliste
Empfehlung: eine kleine Schule (bis 500 Schüler/innen) mit Untis- oder SchILD-Export, Start zum Halbjahreswechsel; die Abnahmeliste ist die Checkliste vor dem Livegang (BET-023). Die Installationsanleitung wird komplett durchgespielt, die Zeit gemessen und Stolperstellen werden eingetragen (BET-022).
Abnahme: Die Pilotschule ist bestimmt (Name steht nicht in diesem Dokument); das Abnahmeprotokoll hakt alle zehn Punkte von BET-023 mit Datum ab; Dauer der Installation und notierte Stolperstellen liegen vor.

**BET-212** · P2 · Status: offen · Entscheidung E9: Weißlabel
Eine Schule darf den Produktnamen ersetzen (`SM_APP_NAME` ist technisch möglich); ob das lizenzrechtlich erlaubt ist, ist offen. Technische Kennungen bleiben Konstanten (BET-163); der Produktname steht nur an einer Stelle.
Abnahme: Entscheidung dokumentiert; bei „erlaubt“ ändert ein Wechsel von `SM_APP_NAME` alle sichtbaren Texte, PDF-Briefe und Mails, aber keine technische Kennung; bei „nicht erlaubt“ ist die Variable in der Lizenzausgabe als nicht änderbar vermerkt.

**BET-213** · P2 · Status: offen · Code-Schutz, EULA, Patent
Wortlaut des Betreibers: „der Code muss ... so verschlüsselt sein, dass die den nicht entschlüsseln können“ (12.10.2026); „das die schulen die denn code laufen lassen werden nicht einfach denn code enzifern können und revers engenieren können“ (16.10.2026); „Und der muss natürlich dann auch patentiert sein“. Bewertung (nicht entschieden): Vollständige Verschlüsselung ist technisch nicht möglich, nur eine Erschwernis (Auslieferung als Container-Image mit kompiliertem Code, für Kernteile wie Generator, Vertretung und Lizenz später kompiliert; Oberfläche ohne lesbare Quellen); die Lizenzprüfung ist im Echtbetrieb nicht abschaltbar (BET-082); Kunden-Wasserzeichen; realer Schutz über Lizenzvertrag/EULA (Anwalt) und Urheberrecht; das gehostete Angebot ist der wirksamste Schutz, weil der Code nicht ausgeliefert wird (BET-206); Software ist in der EU kaum patentierbar, ein Patentanwalt ist zu fragen (keine Rechtsberatung). Schon jetzt gilt: Das ausgelieferte Image enthält nur das Produkt, keine Tests, Entwicklerskripte, Lizenzserver oder interne Dokumentation (BET-105).
Abnahme: Entscheidung dokumentiert (Maßnahmen, Kosten, Zeitpunkt); bei „kompiliert ausliefern“ enthält das Schul-Image für die Kernteile keinen lesbaren Quelltext (Prüfung des Image-Inhalts); die EULA (BET-208) enthält das Verbot der Rückübersetzung.

**BET-214** · P1 · Status: Ist · Betreiber-Paket (Dokumente für die Zuständigen)
Wunsch (17.10.2026): „Ja, für die Leute, die dafür zuständig werden, sollte das verlinkt werden.“ Die Kundenanleitungen liegen als Betreiber-Paket im Image: Installationsanleitung (BET-022), Checkliste vor dem Livegang (BET-023), Betriebshandbuch, Sicherheitskonzept, Update-Anleitung (BET-026), Wiederherstellung (BET-047 bis BET-049), Lizenz (Kap. 12), Datenschutz-Vorlagen. In der Hilfe: Bereich „Betrieb und Einrichtung“ (Installation, Betrieb, Sicherheit, Updates) nur für die Administration; „Schule einrichten“ für alle mit Einstellungsrecht; „Datenschutz-Vorlagen“ für Datenschutz-Zuständige; nicht sichtbar für Lehrkräfte, Eltern, Schüler/innen, Zuschauer, Hausmeister und Sekretariat. Die Texte enthalten keine Heimserver-, Domain- oder Personenangaben, ein Test prüft das bei jedem Lauf. Anrede „Sie“. Noch offen: Bilder und Schritt-für-Schritt-Screenshots in der Hilfe, Hilfe in weiteren Sprachen, juristische Prüfung der Vorlagen (BET-208), Barrierefreiheit der Hilfe (OBE).
Abnahme: Eine Lehrkraft sieht den Bereich „Betrieb und Einrichtung“ nicht und erhält beim Direktaufruf 404; die Administration sieht ihn; eine Suche im Betreiber-Paket findet keine echte Domain, IP-Adresse oder Person (Test); jede genannte Anleitung ist im Paket vorhanden.

**BET-215** · P0 · Status: offen · Freigabekriterien vor dem ersten echten Kunden
Eine Lizenz für eine echte Schule wird erst ausgegeben, wenn dokumentiert vorliegt: (1) die Instanz läuft im Modus `production`, `check-config` ohne Meldung (BET-003, BET-010); (2) der öffentliche Prüfschlüssel und die Lizenzserver-Adresse sind fest eingebaut, die Prüfung ist nicht abschaltbar (BET-079, BET-082); (3) der Live-Test der Lizenz ist bestanden (BET-094); (4) der Restore-Rundlauf mit echter Sicherung einschließlich Dateien ist bestanden (BET-050); (5) der Abnahmelauf unter Last ist bestanden (BET-198); (6) das Update-System ist auf einem echten Container-Dienst erprobt oder der Betrieb ist bewusst manuell (BET-171, BET-161); (7) Verträge, Support und Hosting sind entschieden (BET-206 bis BET-208); (8) die Datenschutz-Vorlagen sind juristisch geprüft; (9) die Checkliste BET-023 ist abgehakt; (10) die Demo-Sperre im Modus `production` ist getestet (BET-011, BET-013); (11) Zahlungsabwicklung und Preise sind entschieden (BET-129, BET-135).
Abnahme: Ein Freigabeprotokoll mit den elf Punkten, Datum und verantwortlicher Person liegt vor; ein Punkt ohne Nachweis sperrt die Ausgabe der Lizenz `[Vorschlag]`.

**BET-216** · P2 · Status: offen · Entscheidung: Update-Verteilung per Download oder Registry
Empfehlung der Quelle: jetzt Download vom Lizenzserver; auf eine Registry umstellen, sobald mehr als etwa 10 Schulen aktiv sind oder der Lizenzserver die Last nicht mehr trägt. Die Registry ist nicht gebaut und nicht erprobt; es gäbe nur Zugriff per Digest (BET-139).
Abnahme: Entscheidung mit Auslöser („ab N Schulen“) dokumentiert; bei Umstellung: Zugang je Schule oder öffentlich lesbar mit Digest-Pflicht, Prüfpfad des Agenten (Präfix, Digest) getestet (BET-154), Wiederaufnahme eines abgebrochenen Ladevorgangs getestet.

**BET-217** · P1 · Status: offen · Entscheidung: „Jetzt installieren“ gegen den Vertrag „nur manuell“
Ist: Die Schule kann durch „Jetzt installieren“ jederzeit sofort installieren, auch wenn vertraglich „nur manuelle Updates“ gelten; der Vertrag verhindert nur die automatische Installation (BET-145). Zu klären ist, ob der Vertrag auch diesen Weg einschränken soll (z. B. Freigabe durch den Anbieter nötig) oder ob Sicherheitsupdates trotz Vertrag erzwungen werden dürfen (heute nicht: „dringend“ umgeht den Vertrag nicht).
Abnahme: Entscheidung dokumentiert; Test passend zur Wahl (Vertrag gilt: „Jetzt installieren“ liefert 403 mit Hinweis; Vertrag gilt nicht: Installation startet).

**BET-218** · P2 · Status: offen · Entscheidung: Kulanzbegriffe vereinheitlichen
Es bestehen zwei Kulanzbegriffe: die Tarif-Kulanz (Kulanztage bei Verzug, Standard 14 Tage; Schwelle für die automatische Pause, BET-119, BET-125) und die Kulanz der Anwendung (`grace_days`, Standard 14 Tage; „nur lesen“ nach Pause, Abo-Ende und abgelaufener Bestätigung, BET-083). Zu entscheiden sind eindeutige Namen (z. B. „Zahlungsfrist“ und „Lesezeit“) und ob eine Größe genügt.
Abnahme: Die Oberfläche des Portals und die Dokumentation verwenden je Größe genau einen Namen; Tarifseite und Lizenzseite verwechseln sie nicht (Textprüfung).

**BET-219** · P1 · Status: offen · Entscheidung: Zahlungsverzug
Zu entscheiden (Betreiber, 16.10.2026: „Entscheidung, ob und nach wie vielen Tagen“): ob die automatische Pause bei Zahlungsverzug eingeschaltet wird (heute aus, je Schule einstellbar), nach wie vielen Tagen, ob eine Zahlung die automatisch pausierte Schule wieder fortsetzt (BET-125), ob der Rechnungslauf nach einer fehlgeschlagenen Zahlung erneut eine Rechnung anlegt (BET-124) und ob die Schule vor der Pause eine Zahlungserinnerung erhält `[Vorschlag]`.
Abnahme: Die fünf Fragen sind beantwortet und im Portal als Voreinstellung bzw. Tarifwert hinterlegt; Test passend je Antwort.

**BET-220** · P2 · Status: offen · Entscheidung: Verhalten der Rollouts bei Fehlern und Fristen
Zu entscheiden (Befunde aus BET-143, BET-153, BET-158): (a) soll ein Rollout bei einem Fehler automatisch pausieren (Ist: nein, es öffnen nur keine weiteren Wellen); (b) soll eine von Hand freigegebene Welle auch bei Fehlern früherer Wellen öffnen (Ist: ja); (c) sollen pausierte Schulen eine Welle bis zu 3 Tage verzögern (Ist: ja); (d) eine Frist „Schule gesehen“ (definiert 14 Tage, wirksam 3 Tage): eine Größe festlegen; (e) die wirkungslose Download-Aufbewahrungs-Einstellung des Agenten entfällt (im Download-Ordner bleibt nur das aktuelle Abbild).
Abnahme: Fünf dokumentierte Entscheidungen; je Entscheidung ein Test in der Rollout-Simulation; im Neubau gibt es genau eine Konstante für die Frist „Schule gesehen“.

**BET-221** · P2 · Status: offen · Entscheidung: Mehrserver-Betrieb als Produktmerkmal
Offene Entscheidung der Quelle: Zwei- und Mehrknoten-Betrieb erst nach einem Probelauf anbieten (BET-169); Ereignis-Relay für Live-Updates (BET-166) und gemeinsame Dateiablage sind nicht gebaut oder erprobt; Hochverfügbarkeit Stufe 2 und 3 ist Konzept. Zu entscheiden: Soll Mehrserver-Betrieb ein verkauftes Produktmerkmal werden, ab wann und zu welchem Preis (BET-135).
Abnahme: Entscheidung dokumentiert; bei „ja“ ist der Probelauf (BET-169) bestanden, bevor das Merkmal im Portal auswählbar ist.

**BET-222** · P1 · Status: offen · Datenübernahme aus dem Altbestand
Die Instanzen des Altbestands (Hauptinstanz mit 5.462 Konten, Demo, Test-Instanz „neu“) laufen mit Migrationsstand 0053 (16.10.2026), Datenbank SQLite im Datenvolumen. Der Neubau übernimmt das Konzept, nicht die Nummern. Zu entscheiden: Datenübernahme per Importweg aus der Altbestand-Datenbank (Probelauf auf einer Kopie, Zeilenzahl-Vergleich je Tabelle, danach Sicherung) oder bewusster Neustart ohne Altdaten. `[unklar: ob die Hauptinstanz echte Daten führt; Empfehlung E1 lässt sie als Vorführung]` Bekannte Fallen: Die Migration 0013 der Cloud-Version kann beim Upgrade Materialien in Bestandsordnern löschen (Behebung im Zusammenschluss unbestätigt); Umbauten von Tabellen mit kaskadierenden Fremdschlüsseln können Daten löschen (BET-036); alte A/B-Wochen werden ins 52-Wochen-Modell übernommen.
Abnahme: Entscheidung dokumentiert; bei Übernahme: Probelauf auf einer Kopie ohne Fehler, Zeilenzahlen je Tabelle vorher/nachher gleich (außer dokumentierter Abweichungen), Stundenplan (99 Klassen, 1.554 Stunden im Referenzstand) und Konten lesbar, Materialien in Bestandsordnern vollständig.

**BET-223** · P2 · Status: offen · Lieferkette und Abhängigkeiten
Python-Pakete sind mit Prüfsummen gepinnt, der Image-Bau braucht die gesperrten Paketdateien (sonst schlägt er fehl), die Python-Pakete waren am 17.10.2026 ohne bekannte Schwachstellen. Offen: Alle direkt genutzten Pakete stehen in der Paketliste (im Altbestand fehlten drei: `pydantic`, `starlette`, `anyio`); Meldungen zu angeblich ungenutzten Paketen sind zu prüfen (fünf Fehlalarme); große Versionssprünge von Build-, Test- und Laufzeit-Werkzeugen (Oberflächen-Sprache, Build-Werkzeug, Testwerkzeug, Node) nur einzeln und mit Tests; Basis-Images monatlich neu (BET-026).
Abnahme: Ein Test vergleicht alle importierten Pakete mit der Paketliste (Abweichung = Fehler); ein Versionssprung wird in einem eigenen Änderungssatz mit grünem Gesamttest eingespielt; ein Abhängigkeits-Audit ohne bekannte Schwachstellen liegt vor jedem Release vor.

**BET-224** · P3 · Status: offen · Erreichbarkeit der Anbieter-Instanzen ohne Portnummer, eigene Domain
Wunsch (12.10.2026): eine eigene Domain über das Konto des Betreibers beim Domain-Anbieter anlegen und mit dem Server verbinden (Diktat teils unklar), dafür Erlaubnis zur Anmeldung. Nicht umgesetzt; Ersatz war eine Subdomain eines dynamischen DNS-Dienstes mit Portnummer (der Internetanschluss lässt eingehend nur einen schmalen Portbereich zu, BET-016); ein Tunnel-Dienst ohne Portnummer wurde angeboten und nicht entschieden. Port-Freigaben am Router nur mit ausdrücklicher Zustimmung des Betreibers; eine neue Adresse wird erst von außen getestet, dann gemeldet.
Abnahme: Entscheidung dokumentiert; bei „eigene Domain/Tunnel“ sind Haupt- und Demo-Instanz ohne Portnummer über HTTPS mit gültigem Zertifikat erreichbar (Test von außen) und die Zertifikatserneuerung läuft automatisch.

<!--ENDE-->

