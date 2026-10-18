# Schulmanager – Datenschutz & Sicherheit

Hinweise für Schulleitung, Datenschutzbeauftragte und IT-Betreuung. Sie ersetzen keine Rechtsberatung;
maßgeblich sind DSGVO, BDSG, das jeweilige Landesschul- und Landesdatenschutzgesetz sowie die
Verwaltungsvorschriften des Landes (z. B. zu IT-Verfahren in Schulen). Betrieb und Installation:
[`BETRIEB.md`](BETRIEB.md).

**Inhalt**

1. [Rollen und Verantwortung](#1-rollen-und-verantwortung)
2. [DSGVO-Hinweise](#2-dsgvo-hinweise)
3. [TOMs-Checkliste (Art. 32 DSGVO)](#3-toms-checkliste-art-32-dsgvo)
4. [Härtung](#4-härtung)
5. [Incident-Ablauf (Sicherheitsvorfall / Datenpanne)](#5-incident-ablauf-sicherheitsvorfall--datenpanne)
6. [Vorlagen](#6-vorlagen)

---

## 1. Rollen und Verantwortung

| Wer | Rolle im Datenschutz | Aufgaben |
|---|---|---|
| Schule (Schulleitung) | **Verantwortlicher** (Art. 4 Nr. 7 DSGVO) | Freigabe des Verfahrens, Verzeichnis der Verarbeitungstätigkeiten, Information der Betroffenen, Rollen- und Löschkonzept, Meldung von Datenpannen |
| Schulträger / IT-Dienstleister / Hoster | **Auftragsverarbeiter** (Art. 28) | Betrieb nach Weisung, TOMs, Unterauftragnehmer nur mit Zustimmung |
| Behördliche/r Datenschutzbeauftragte/r | Beratung, Kontrolle | DSFA-Prüfung, Schulung, Ansprechpartner für Betroffene und Aufsichtsbehörde |
| IT-Betreuung der Schule | Administration | Konten, Updates, Backups, Monitoring, Vorfallsbearbeitung |

Für jede Schule eine **eigene Instanz** (eigene Datenbank, eigene Domain) – das erfüllt das Trennungsgebot
und vereinfacht Löschung und Auskunft.

---

## 2. DSGVO-Hinweise

### 2.1 Rechtsgrundlage und Zweck

Stunden- und Vertretungsplanung, Raum- und Aufsichtsplanung sowie die Kommunikation von Planänderungen sind
Teil der Erfüllung des Bildungsauftrags: Art. 6 Abs. 1 lit. e, Abs. 3 DSGVO i. V. m. dem Landesschulgesetz
(bzw. für Lehrkräfte i. V. m. dem Beamten-/Beschäftigtendatenschutz). Freiwillige Zusatzfunktionen
(z. B. iCal-Abonnement auf private Geräte, E-Mail-Benachrichtigungen an private Adressen) nur mit
Einwilligung bzw. nach Landesvorgabe.

### 2.2 Datensparsamkeit – welche Daten werden verarbeitet?

| Kategorie | Daten | Hinweis |
|---|---|---|
| Schüler | Name, Klasse, Kurswahlen/Kursteile (z. B. Religion/Ethik), Benutzerkonto | **Keine** Adressen, Geburtsdaten, Fotos, Noten nötig – beim CSV-Import nur benötigte Spalten zuordnen. Die Religionszugehörigkeit ergibt sich mittelbar aus der Kurswahl → besondere Kategorie (Art. 9), Zugriff nur für Berechtigte. |
| Eltern | Name, Konto, Zuordnung zu Kindern, optional E-Mail | |
| Lehrkräfte | Name, Kürzel, Fächer, Deputat, Sperrzeiten, Wünsche, Standort, optional E-Mail | Wünsche/Sperrzeiten sind Beschäftigtendaten → nur Planung/Schulleitung |
| Abwesenheiten Lehrkräfte | Zeitraum, Grund | Grund **minimal** halten („krank“, „Fortbildung“) – keine Diagnosen! Gründe sehen nur Berechtigte (`substitution.edit`), Schüler/Eltern/Exporte nie. |
| Krankmeldungen Schüler | Zeitraum, Stunden, Grund, Status | Gesundheitsbezug → knapp formulieren. Die Abwesenheit sehen die Lehrkräfte der Klasse, den **Grund** nur meldende Person, Familie, Klassenleitung, Sekretariat und Schulleitung (Fachlehrkräfte: „vertraulich“). Grund und Vermerk **verschlüsselt** gespeichert. |
| Atteste & Dokumente | Datei (PDF/Foto), Art, Titel, Status, Vermerk | Gesundheitsdaten (Art. 9). Sicht nur: Einreichende, Eltern (nicht bei volljährigen Kindern), volljährige Schüler/innen selbst, Sekretariat, Schulleitung, **Klassenleitung** – **nie Fachlehrkräfte, nicht die technische Administration**. Datei, Dateiname, Titel und Vermerk verschlüsselt; Anlegen/Prüfen/Löschen im Audit-Log (ohne Inhalt). |
| Technik | Sitzungen, Login-Versuche, Audit-Log (wer hat wann was geändert), Server-Logs mit gekürzten IP-Adressen | Zweckbindung: Sicherheit und Nachvollziehbarkeit |

Die Software unterstützt Datensparsamkeit u. a. durch: rollenbasierte Sichtbarkeit (siehe 2.3), keine
Gründe von Lehrkraft-Abwesenheiten in Exporten (Untis GPU014 nur auf ausdrücklichen Wunsch), keine
Abwesenheitsgründe in iCal-Feeds, maskierte iCal-Tokens und gekürzte IP-Adressen in Logs, Monitoransicht
ohne Lehrkraft-Abwesenheiten und Gründe.

### 2.3 Rollen und Rechte (Need-to-know)

| Rolle | sieht | darf ändern |
|---|---|---|
| Admin | alles außer Atteste/Dokumente von Schüler/innen | alles inkl. Konten, Backups, System |
| Schulleitung | alles außer Systemverwaltung | Konten (keine Admins), Einstellungen, Stammdaten, Vertretungen, Mitteilungen |
| Stundenplaner | alle Pläne, Stammdaten | Stundenplan, Generator, Vertretungen, Klausuren |
| Sekretariat | alle Pläne, Schülerdaten | Stammdaten, Vertretungen/Abwesenheiten, Schüler-/Elternkonten, Krankmeldungen |
| Lehrkraft | Pläne und Schülerdaten **nur eigener Klassen/Kurse**; Gründe von Krankmeldungen und Atteste **nur als Klassenleitung** | eigene Krankmeldung, eigenes Profil (Antrag), Klausuren/Kursräume eigener Kurse, Mitteilungen an eigene Klassen, Atteste prüfen (Klassenleitung) |
| Schüler | eigener Plan, eigene Klasse/Kurse, eigene Krankmeldungen | volljährig (nur durch Sekretariat/Schulleitung/Admin setzbar): eigene Krankmeldung und Atteste |
| Eltern | Pläne/Krankmeldungen der eigenen Kinder; Atteste nur bei minderjährigen Kindern | Krankmeldung der Kinder, Atteste/Dokumente einreichen |
| Monitor | Vertretungsplan eines Standorts ohne Gründe | – |

Konten **regelmäßig prüfen** (mindestens zum Schuljahreswechsel): `schulmanager-admin list-users`,
Oberfläche *Benutzer*. Rechte nur so weit vergeben, wie es die Aufgabe erfordert; Admin-Konten personengebunden
(kein geteiltes „admin“-Konto im Alltag).

### 2.4 Löschfristen (Vorschlag – mit Landesvorgaben abgleichen)

> Seit Oktober 2026 setzt die Software das Löschkonzept selbst um (Warteliste „ausgetreten“, Fristen je Datenart, Vorschau, Löschprotokoll, Sofort-Löschen, Audit-Frist): siehe [`DATENSCHUTZ-LOESCHKONZEPT.md`](DATENSCHUTZ-LOESCHKONZEPT.md). Die Tabelle unten bleibt als Überblick.

| Daten | Frist | Umsetzung |
|---|---|---|
| Konten ausgeschiedener Schüler/Eltern/Lehrkräfte | zum Ende des Schuljahres bzw. bei Austritt deaktivieren, spätestens nach 3 Monaten löschen | *Benutzer* → deaktivieren/löschen; Massenbereinigung zum Schuljahreswechsel |
| Stammdaten ausgeschiedener Schüler | mit Abgang aus dem Planungsdokument entfernen | Import mit „ersetzen“ bzw. Löschen in *Stammdaten* |
| Abwesenheiten/Vertretungsentscheidungen | Ende des folgenden Schuljahres (Nachweis Unterrichtsausfall/Vertretungsabrechnung) | Bereinigung vergangener Einträge zum Schuljahreswechsel |
| Krankmeldungen Schüler | Ende des Schuljahres (+ Frist für Zeugnis-Fehlzeiten nach Landesrecht) | *Krankmeldungen* filtern und löschen |
| Atteste & Dokumente von Schüler/innen | automatisch nach `SM_STUDENT_DOCS_RETENTION_DAYS` (Standard 400 Tage ≈ Schuljahr + Zeugnisfrist; `0` = aus) | Wartungslauf löscht Eintrag **und** Datei; einzeln: *Atteste & Dokumente* → Löschen (Sekretariat) |
| Planversionen (Verlauf/Undo) | automatisch begrenzt auf `SM_KEEP_VERSIONS` (Default 300) | Konfiguration |
| Sitzungen, abgelaufene Tokens, Login-Versuche | automatisch (Wartungslauf, `SM_MAINTENANCE_INTERVAL`) | – |
| Audit-Log | 1 Jahr (Sicherheit, Nachvollziehbarkeit) | Bereinigung jährlich |
| Server-Logs (mit gekürzten IP-Adressen) | ≤ 14 Tage | Log-Rotation `LOG_MAX_SIZE`/`LOG_MAX_FILES` (nur größenbasiert), journald `MaxRetentionSec=14d` empfohlen, Zugriffsprotokoll kürzt IPs selbst |
| Backups | max. 12 Monate (Rotation 14 Tage / 8 Wochen / 12 Monate) | gelöschte Daten verschwinden spätestens mit dem Ablauf des letzten Backups; im Löschkonzept so dokumentieren |

### 2.5 Betroffenenrechte

* **Auskunft/Datenübertragbarkeit** (Art. 15, 20): Nutzer laden ihre Kontodaten unter *Profil → Daten
  exportieren* (`GET /api/v1/me/export`) als JSON; für vollständige Auskünfte erzeugt die Schulleitung die Auskunft zu einer Person als ZIP
  (`GET /api/v1/privacy/export`, siehe `DATENSCHUTZ-LOESCHKONZEPT.md`).
* **Berichtigung** (Art. 16): über *Stammdaten* bzw. *Benutzer*.
* **Löschung/Einschränkung** (Art. 17, 18): siehe Löschfristen; Konto deaktivieren schränkt sofort ein.
* **Information** (Art. 13/14): Datenschutzhinweise für Schüler, Eltern und Lehrkräfte bereitstellen
  (Zweck, Rechtsgrundlage, Empfänger, Speicherdauer, Rechte, Kontakt DSB).

### 2.6 Auftragsverarbeitung und Hosting in Deutschland

* **Hosting** bei einem Anbieter mit Rechenzentrum in Deutschland (oder EU/EWR) und **AV-Vertrag nach
  Art. 28 DSGVO**; ISO-27001-zertifizierte Rechenzentren bevorzugen. Kein Transfer in Drittländer (auch nicht
  über US-Konzernmütter von Backup-/Mail-/CDN-Diensten ohne geeignete Garantien).
* **Auftragsverarbeiter im Gesamtsystem** (jeweils AV-Vertrag, im VVT aufführen): Hoster/Rechenzentrum,
  ggf. IT-Dienstleister des Schulträgers, E-Mail-Versand (`SM_SMTP_*`), Offsite-Backup-Speicher
  (`BACKUP_RCLONE_*`), externer Monitoring-Dienst (falls genutzt), SSO-Identitätsanbieter.
* **Keine externen Ressourcen im Browser:** Die Oberfläche lädt keine Schriften, Skripte oder Tracker von
  Drittanbietern (CSP `default-src 'self'`). Grafana sendet keine Nutzungsstatistiken (abgeschaltet).
* **Let's Encrypt** erhält nur den Domainnamen und die Kontakt-E-Mail.
* **Offsite-Backups** immer verschlüsselt (`BACKUP_GPG_PASSPHRASE`) – der Speicheranbieter sieht dann
  keine Klartextdaten.

### 2.7 Verzeichnis, Datenschutz-Folgenabschätzung

* Eintrag im **Verzeichnis von Verarbeitungstätigkeiten** (Art. 30) – Vorlage in Abschnitt 6.
* **DSFA** (Art. 35) prüfen: Umfang (> 2500 Schüler), Minderjährige, mittelbare Art.-9-Daten
  (Religionskurse, Krankmeldungen) sprechen dafür, die Schwellwertanalyse zu dokumentieren und ggf. eine DSFA
  durchzuführen. Viele Länder stellen Muster bereit.
* **Schulung** des Personals (Rollen, Passwörter/2FA, Umgang mit Zugangsbriefen, Gründe knapp halten).

---

## 3. TOMs-Checkliste (Art. 32 DSGVO)

Abhaken, Verantwortliche/n und Datum eintragen, jährlich überprüfen.

**Vertraulichkeit**

- [ ] Zutrittskontrolle: Server in zertifiziertem Rechenzentrum (Nachweis des Hosters)
- [ ] Zugangskontrolle Server: SSH nur mit Schlüssel, kein Root-Login per Passwort, SSH nur aus Admin-Netzen
- [ ] Zugangskontrolle Anwendung: Passwortregeln aktiv (≥ 10 Zeichen, Schüler ≥ 8), **2FA für alle Personal-Konten mit erweiterten Rechten** (Admin, Schulleitung, Planung, Sekretariat), Kontosperre nach Fehlversuchen
- [ ] Zugriffskontrolle: Rollenmodell nach Need-to-know, jährliche Rechteprüfung, personengebundene Admin-Konten
- [ ] Trennungskontrolle: eigene Instanz je Schule, Test-/Demo-Instanzen ohne Echtdaten
- [ ] Pseudonymisierung/Minimierung: IP-Kürzung in Logs, keine unnötigen Stammdaten, Gründe knapp
- [ ] Verschlüsselung: TLS 1.2/1.3 mit HSTS (Caddy/nginx), Backups mit GPG/AES-256, Festplattenverschlüsselung beim Hoster (falls angeboten)
- [ ] Inhaltsverschlüsselung: Nachrichten, Dateien/Atteste und Freitexte AES-256-GCM-verschlüsselt (`SM_ENCRYPTION_KEYS`), Master-Schlüssel **getrennt vom Backup** im Tresor hinterlegt, Rotation dokumentiert (Abschnitt 4.6)

**Integrität**

- [ ] Weitergabekontrolle: Exporte (Untis, CSV, JSON) nur durch Berechtigte, Ablage nur auf dienstlichen Geräten; Webhooks signiert (`SM_WEBHOOK_SECRET`)
- [ ] Eingabekontrolle: Audit-Log aktiv, Planversionen nachvollziehbar (wer/wann/was)
- [ ] Software-Integrität: Images aus eigener CI bzw. signierter Release-Pipeline (Build-Provenienz), Abhängigkeits-Updates (Dependabot), CodeQL

**Verfügbarkeit und Belastbarkeit**

- [ ] Backups täglich, Rotation 14/8/12, **Offsite-Kopie**, Backup-Überwachung (Healthcheck/Push-Monitor)
- [ ] **Test-Restore monatlich**, vollständiger Probe-Restore halbjährlich (dokumentiert)
- [ ] Monitoring von außen mit Alarmierung (Uptime-Kuma/Grafana), Zertifikatsablauf überwacht
- [ ] Ressourcenlimits, automatischer Neustart der Container, Notfallhandbuch + Kontaktliste
- [ ] Notfall-Ausdruck des Vertretungsplans (organisatorisch)

**Verfahren zur regelmäßigen Überprüfung**

- [ ] Monatlicher Patchtag (OS, Docker, Images neu bauen, App-Updates)
- [ ] Jährliche Überprüfung von TOMs, Rollen, Löschfristen, AV-Verträgen
- [ ] Auftragskontrolle: AV-Verträge mit Hoster, Mail-, Backup-, Monitoring-Anbieter liegen vor

---

## 4. Härtung

### 4.1 Anwendung

* **2FA (TOTP)** für alle Konten mit erweiterten Rechten technisch erzwingen:
  `SM_REQUIRE_2FA_ROLES=admin,schulleitung,planer,sekretariat` – betroffene Konten werden nach der Anmeldung auf die
  Seite „Zwei-Faktor-Anmeldung einrichten“ geleitet und können bis dahin nichts anderes tun (API: `403 totp_setup_required`).
  Kontrolle über `schulmanager-admin list-users` (Spalte `2fa`). Verlorene Geräte: `disable-2fa`, danach neu
  einrichten lassen.
* **Passwortregeln** (fest in der App): mindestens 10 Zeichen (Schüler 8), keine Trivialpasswörter, nicht den
  Benutzernamen enthaltend; Hashing mit scrypt (`SM_SCRYPT_N` ≥ 16384, Default 32768). Startpasswörter aus
  der Massenanlage müssen beim ersten Login geändert werden. Empfehlung an Nutzer: Passphrasen aus 4–5
  Wörtern bzw. Passwortmanager.
* **Sitzungen:** Ablauf nach Inaktivität (`SM_SESSION_IDLE_MINUTES`) und absolut (`SM_SESSION_MAX_DAYS`);
  Cookie `HttpOnly`, `SameSite=Lax`, `Secure` (`SM_COOKIE_SECURE=1`); CSRF-Token für ändernde Anfragen.
  Für Personal kürzere Werte erwägen (z. B. 1 Tag Inaktivität).
* **Brute-Force-Schutz:** Sperre je Konto (`SM_LOGIN_MAX_FAILURES`) und je IP (`SM_LOGIN_MAX_FAILURES_IP`);
  zusätzlich Proxy-Rate-Limit (nginx-Vorlage aktiv, Caddy optional per Plugin, siehe
  `deploy/caddy/conf.d/ratelimit.caddy.example`).
* **API-Tokens** nur mit Ablaufdatum und für den konkreten Zweck; nicht benötigte Tokens löschen.
* **iCal-Links** sind geheime URLs: bei Verdacht neu erzeugen (*Profil*), Nutzer darauf hinweisen, Links
  nicht weiterzugeben. Der Server speichert nur eine Prüfsumme (HMAC); der Link wird **nur beim Erzeugen** angezeigt.
* **SSO (OIDC)** über den Landes-/Schulträger-IdP reduziert Passwörter; `SM_OIDC_AUTO_CREATE=0` lassen, wenn
  Konten nur gezielt angelegt werden sollen.
* **API-Dokumentation** (`/api/docs`, `/api/openapi.json`): Voreinstellung in Produktion **aus**, sonst nur für
  angemeldete Administratoren (`SM_ENABLE_DOCS=0|admin|1`, siehe 4.8). Swagger-UI wird lokal ausgeliefert, es wird
  nichts von einem CDN geladen. `/llms.txt` und die öffentliche API-Beschreibung für API-Zugänge
  (`docs/API-ZUGAENGE.md`) bleiben unabhängig davon erreichbar.
* **Geheimnisse in der Datenbank:** TOTP-Geheimnisse liegen mit dem Hauptschlüssel verschlüsselt in der Datenbank
  (`crypto.py`, Bindung an das Konto; Neuverpacken bei Schlüsselrotation, `rotate-keys`), iCal-Tokens nur als Hash.
  Ein Datenbank-Dump allein reicht damit nicht für Kalender-Feeds oder 2FA-Codes. Dumps bleiben trotzdem
  schützenswert (Verschlüsselung der Backups, restriktive Dateirechte; die Backup-Skripte arbeiten mit `umask 077`).

### 4.2 Server

* Minimales OS, nur benötigte Dienste; **automatische Sicherheitsupdates** (`unattended-upgrades`),
  geplante Neustarts.
* **SSH:** nur Schlüssel (`PasswordAuthentication no`, `PermitRootLogin prohibit-password` bzw. `no`),
  Zugriff nur aus Admin-Netzen/VPN, optional `fail2ban`.
* **Firewall:** eingehend nur 22 (eingeschränkt), 80/tcp, 443/tcp, 443/udp.
  *Achtung:* Von Docker veröffentlichte Ports umgehen `ufw`. Der Stack veröffentlicht deshalb nur 80/443;
  Grafana, Prometheus und Uptime-Kuma sind ausschließlich an `127.0.0.1` gebunden. Keine weiteren
  `ports:` hinzufügen (insbesondere nicht für PostgreSQL).
* **Zeit:** NTP aktiv (TOTP, Zertifikate, Protokolle).
* **Dateirechte:** `.env` `chmod 600`, Besitzer root; Backup-Verzeichnis nur root bzw. `schulmanager`.
* **Admin-Zugänge** zu Grafana/Uptime-Kuma nur per SSH-Tunnel; eigene starke Passwörter.

### 4.3 Container

Bereits umgesetzt in `Dockerfile`/`docker-compose.yml`:

* App läuft als **unprivilegierter Benutzer** (UID 10001), **schreibgeschütztes Root-Dateisystem**
  (`read_only`, nur `/tmp` als tmpfs und `/app/data` als Volume), `cap_drop: ALL`,
  `no-new-privileges`, PID-/CPU-/RAM-Limits.
* **PostgreSQL** nur im internen Netz `backend` (`internal: true`) – weder vom Internet erreichbar noch mit
  Internetzugang; kein veröffentlichter Port.
* Caddy mit minimalen Rechten (`NET_BIND_SERVICE`), schreibgeschützt; Security-Header (HSTS, CSP,
  `X-Frame-Options`, `nosniff`, Referrer-/Permissions-Policy); `/metrics` von außen gesperrt.
* Build-Kontext per Whitelist (`.dockerignore`) – keine `.env`, Datenbanken oder Backups im Image.
* Regelmäßig neu bauen (`docker compose build --pull`), optional Images scannen
  (z. B. `trivy image schulmanager:latest`).

### 4.4 Schlüssel und Geheimnisse

| Geheimnis | Ort | Rotation / Folgen |
|---|---|---|
| `SM_SECRET_KEY` | `.env` | Wechsel meldet alle Sitzungen ab und macht API-Tokens ungültig (Tokens sind als HMAC gespeichert) |
| `SM_ENCRYPTION_KEYS` | `.env` + **Tresor, getrennt vom Backup** | Rotation ohne Ausfall (Abschnitt 4.6); **Verlust = verschlüsselte Inhalte unwiederbringlich verloren**, auch aus Backups |
| `POSTGRES_PASSWORD` | `.env` | `ALTER USER … PASSWORD` + `.env` anpassen + Neustart |
| `BACKUP_GPG_PASSPHRASE` | `.env` + **Tresor** | neue Backups mit neuer Passphrase; alte Passphrase für ältere Backups aufbewahren, bis diese rotiert sind |
| `SM_WEBHOOK_SECRET` | `.env` | Empfänger informieren |
| SMTP-/S3-/OIDC-Zugangsdaten | `.env` | beim Anbieter neu erzeugen |
| Admin-Passwörter, 2FA | Konten | regelmäßig prüfen, bei Personalwechsel sofort deaktivieren |

### 4.5 Updates

* Monatlicher **Patchtag** (BETRIEB.md, Abschnitt 6) – Sicherheitsupdates sofort.
* GitHub-Releases des Projekts beobachten („Watch → Releases“); Dependabot hält Abhängigkeiten aktuell.

### 4.6 Verschlüsselung & Schlüsselverwaltung

**Was ist verschlüsselt?** Inhalte, die besonders schutzbedürftig sind, liegen in Datenbank und Dateiablage nie im
Klartext: Betreff und Text interner Nachrichten, alle hochgeladenen Dateien (Unterrichtsmaterial, Anhänge, Atteste und
andere Dokumente) **einschließlich der Dateinamen**, Titel und Vermerke von Attesten, **Gründe und Vermerke von
Krankmeldungen** (Altbestand wird bei der Migration `0006_student_self` verschlüsselt), Freitexte in Anträgen von Lehrkräften. Nicht verschlüsselt sind
Planungsdaten (Stundenplan, Vertretungen) und Konten-Stammdaten – diese schützen Rechtekonzept, Transport- und
Backup-Verschlüsselung.

**Verfahren:** Umschlagverschlüsselung mit **AES-256-GCM** (Bibliothek `cryptography`). Jedes Objekt (jede Nachricht,
jede Datei) erhält einen eigenen, zufälligen 256-Bit-Datenschlüssel; dieser wird mit dem **Master-Schlüssel** aus
`SM_ENCRYPTION_KEYS` verschlüsselt („gewrappt“) und mit dem Chiffrat gespeichert. Zusätzlich gebundene Daten (AAD:
Tabelle, Feld, Datensatz-ID) verhindern, dass verschlüsselte Werte unbemerkt in andere Datensätze kopiert werden.
Dateien werden blockweise (64 KiB) authentifiziert verschlüsselt; Manipulation, Abschneiden oder Vertauschen von Blöcken
wird beim Lesen erkannt (Fehler statt stiller Datenmüll). Token-Format versioniert (`SM1`/`SMS1`), Nonces zufällig.

**Wovor schützt das?** Vor dem Lesen von Inhalten aus gestohlenen oder versehentlich veröffentlichten Datenbank-Dumps
und Backups, aus Festplatten-/Snapshot-Kopien beim Hoster und durch Datenbank-Administration ohne Schlüssel.
**Nicht** vor jemandem mit Root-Zugriff auf den laufenden Server (der Schlüssel liegt in der Umgebung des Prozesses)
und nicht vor Missbrauch berechtigter Konten in der Anwendung – dafür gelten Rechtekonzept, 2FA und Audit-Log. Es ist
**keine Ende-zu-Ende-Verschlüsselung**: Der Server entschlüsselt, um Nachrichten anzuzeigen und Meldungen moderieren zu
können (`messages.moderate`).

**Schlüssel erzeugen und aufbewahren**

* Erzeugen: `schulmanager-admin gen-key` (bzw. `echo "k1:$(openssl rand -base64 32)"`) → Eintrag `id:Base64` in
  `.env` als `SM_ENCRYPTION_KEYS=…` (`chmod 600`). Ohne gültigen Schlüssel **startet die Anwendung in Produktion nicht**.
* **Getrennt vom Backup aufbewahren:** Passwort-Tresor der Schulleitung **und** versiegelter Ausdruck im Safe; nie im
  selben Speicher/Bucket wie die Backups, nie per E-Mail oder Chat. Ein Backup ohne Schlüssel ist für Angreifer
  wertlos – aber auch für die Schule.
* **Verlust des Schlüssels = Datenverlust:** Nachrichten, Dateien und Atteste sind dann auch aus allen Backups nicht
  mehr lesbar. Es gibt keine Hintertür und keinen Generalschlüssel des Herstellers.
* Kontrolle ohne Offenlegung: `schulmanager-admin crypto-status` zeigt aktive Schlüssel-ID und Fingerabdrücke (zum
  Abgleich mit dem Tresor-Eintrag), nie das Schlüsselmaterial.
* Entwicklung/Test: Fehlt `SM_ENCRYPTION_KEYS`, wird ein Schlüssel aus `SM_SECRET_KEY` abgeleitet (Warnung im Log).
  Solche Instanzen nie mit Echtdaten betreiben.

**Rotation** (z. B. jährlich, bei Personalwechsel in der IT, nach Verdacht auf Offenlegung): neuen Schlüssel **vorn**
eintragen (`SM_ENCRYPTION_KEYS="k2:…,k1:…"`), Neustart, `schulmanager-admin rotate-keys` wrappt alle Datenschlüssel
(Dateien inkl. Namen, Nachrichten und weitere registrierte Bereiche) mit dem neuen Master-Schlüssel neu – die Nutzdaten
selbst werden nicht angefasst, das geht auch bei vielen Dateien schnell. Den alten Schlüssel erst entfernen, wenn alle
Backups, die vor der Rotation entstanden sind, abgelaufen sind (Rotation der Backups: bis 12 Monate). Schritt-für-Schritt:
`docs/BETRIEB.md`, Abschnitt 14. Nach Verdacht auf Offenlegung zusätzlich als Vorfall behandeln (Abschnitt 5): Alte
Backups bleiben mit dem alten Schlüssel lesbar.

### 4.6a Chats: Geräte, Verlauf und Wiederherstellung

Chats sind Ende-zu-Ende-verschlüsselt (`frontend/src/features/chats/crypto.ts`, `keys.ts`). Je Nachricht gibt es einen
zufälligen Inhaltsschlüssel K (`secretbox`), den der Absender für **jedes Gerät** aller Mitglieder verpackt (`box`,
X25519). Der private Geräteschlüssel verlässt den Browser nie.

**Verlauf auf ein neues Gerät übertragen.** Das neue Gerät zeigt Code, QR-Code und Fingerabdruck. Auf einem
eingerichteten Gerät gibt man den Code ein, vergleicht den Fingerabdruck und bestätigt. Danach öffnet das alte Gerät
die Schlüssel K der bisherigen Nachrichten (in Paketen zu 200, fortsetzbar, abbrechbar) und verpackt sie neu für das
neue Gerät (`POST /chat-keys`). Der Server prüft: beide Geräte gehören dem Konto, Freigabe liegt vor (Code 15 min,
danach 2 h Übertragungsfenster), die Person war Mitglied und die Nachricht liegt nach ihrer Beitrittsgrenze. Beim
Entpacken zählt der öffentliche Schlüssel des Verpackers (`wrapper_key`). Bilder: ihr Schlüssel steht im
verschlüsselten Inhalt und ist damit automatisch lesbar.

**Wiederherstellung mit Passwort (optional).** Das Konto erhält ein Archiv-Schlüsselpaar. Der öffentliche Teil
erscheint als „Gerät“ `kind=archive`, für das alle Teilnehmer künftig mitverpacken; der bisherige Verlauf wird vom
einrichtenden Gerät dafür verpackt. Der private Teil liegt nur als Blob (`chat_key_backups`) auf dem Server,
verschlüsselt mit einem Schlüssel aus Wiederherstellungscode oder -passwort (PBKDF2-SHA-256, 1 Mio. Runden, Salt im
Blob). Empfohlen ist der erzeugte Code (125 Bit); eigene Passwörter brauchen mindestens 12 Zeichen. **Ohne Code oder
Passwort gibt es keine Wiederherstellung** – auch nicht durch Schule oder Betreiber. Passwort ändern und Backup
löschen sind möglich (Löschen entfernt den Archivschlüssel und alle für ihn verpackten Schlüssel).

**Neue Schlüssel.** „Dieses Gerät neu einrichten“ erzeugt ein neues Schlüsselpaar (auf Wunsch wandert der Verlauf
mit) und widerruft das alte. „Alle Geräte zurücksetzen“ widerruft alle Geräteschlüssel des Kontos (Backup wahlweise
behalten); Gesprächspartner verwenden automatisch die neuen Schlüssel. Deren Browser merken sich je Person die
Fingerabdrücke und zeigen „Sicherheitsschlüssel von X hat sich geändert“ (Schlüssel ersetzt) bzw. „weiteres Gerät“.
Neue eigene Geräte werden den anderen eigenen Geräten als „neu“ gemeldet (Live-Ereignis, Banner), bis ein *anderes*
Gerät sie bestätigt oder entfernt.

**Bedrohungsmodell – was der Server sieht:** Konten, Mitglieder, Zeitpunkte, Größen, öffentliche Schlüssel und
Gerätenamen, verpackte Schlüssel (wer wann für welches Gerät ergänzt wurde), Verknüpfungs-Codes (kurzlebig, nur im
eigenen Konto auffindbar, Ratenlimit) und das Backup-Blob. **Nie:** Nachrichtentexte, Bilder, Inhaltsschlüssel,
private Geräte- oder Archivschlüssel, Passwort/Code. **Grenzen:** Ein bösartiger oder kompromittierter Server könnte
beim Verknüpfen ein eigenes Gerät unterschieben – deshalb der Fingerabdruck-Vergleich auf beiden Geräten. Ein
Angreifer mit Server-Datenbank kann das Backup-Blob offline erraten; Schutz bietet nur ein starker Code/ein langes
Passwort. Wer ein entsperrtes Gerät oder den Wiederherstellungscode besitzt, liest den Verlauf. Nachrichten, die vor
der Mitgliedschaft einer Person gesendet wurden, bleiben für sie unlesbar.

### 4.7 Datei-Uploads

* **Grenzen:** höchstens `SM_UPLOAD_MAX_MB` (Standard 25 MB) je Datei – schon während der Übertragung geprüft;
  Speicherkontingent je Konto `SM_QUOTA_MB_STAFF` (Personal, 2000 MB) bzw. `SM_QUOTA_MB_STUDENT` (Schüler und Eltern,
  200 MB), `0` = unbegrenzt. Der Reverse Proxy begrenzt Anfragen zusätzlich auf 50 MB.
* **Erlaubte Dateiarten (Allowlist), am Inhalt erkannt** (Magic Bytes – Dateiendung und Browser-Angabe zählen nicht):
  PDF, Bilder (PNG, JPEG, GIF, WebP, HEIC; SVG nur als Download), Office/OpenDocument (DOCX/XLSX/PPTX/ODT/ODS/ODP,
  DOC/XLS/PPT), Text/CSV/Markdown, Audio/Video (MP3, M4A, WAV, OGG, MP4, MOV, WebM), ZIP.
  **Blockiert** (Audit `file.blocked`): Programme (EXE/DLL/MSI, ELF, Mach-O, APK, JAR …), Skripte (Shell, PowerShell,
  JavaScript, VBS …), HTML/PHP, SVG mit Skripten, Office-Dateien mit Makros/ActiveX/eingebetteten Programmen,
  passwortgeschützte Office-Dateien und Archive (nicht prüfbar), PDF mit Startbefehlen, ZIP-Archive mit ausführbaren
  Dateien oder ungültigen Pfaden. Dateinamen werden bereinigt; die Endung passt immer zum erkannten Inhalt.
* **Auslieferung:** immer als Download (`Content-Disposition` mit `filename*`); nur PDF und Bilder (außer SVG) dürfen im
  Browser angezeigt werden. Dazu `X-Content-Type-Options: nosniff`, `Content-Security-Policy: sandbox`,
  `Cross-Origin-Resource-Policy: same-origin`, `Cache-Control: no-store` – hochgeladene Inhalte können so keinen Code im
  Kontext der Anwendung ausführen.
* **Zugriff:** die hochladende Person und sonst **nur**, wer laut Fachbereich berechtigt ist (Kursmitglieder für
  Material, Gesprächsteilnehmende für Anhänge, berechtigte Stellen für Atteste). Es gibt bewusst **keinen automatischen
  Admin-Zugriff** auf Dateien. Abrufe fremder Dateien werden protokolliert (Audit `file.download`, je Konto/Datei/Tag einmal).
* **Virenscan (optional, empfohlen):** ClamAV prüft jeden Upload vor dem Speichern (Docker-Profil `antivirus`,
  `SM_CLAMAV_HOST`). Fund → Upload abgelehnt (Audit `file.virus`). Mit `SM_CLAMAV_REQUIRED=1` werden Uploads abgelehnt,
  solange der Scanner nicht erreichbar ist; sonst werden sie ungeprüft angenommen (Warnung im Log, Kennzeichnung
  „nicht virengeprüft“). Ein Virenscanner ergänzt die Allowlist, ersetzt aber keine aktuellen Endgeräte.
* **Löschfristen:** nicht verwendete Uploads werden nach 24 Stunden gelöscht, gelöschte Dateien nach 30 Tagen
  endgültig entfernt (stündliche Wartung); Fristen für Nachrichten und Dokumente regeln die Fachbereiche.

### 4.8 Härtung Runde 3 (Sicherheitsprüfung 2026-10-13: S-08 bis S-11, S-13 bis S-15)

| Fund | Maßnahme | Einstellung |
|---|---|---|
| S-08 Datensparsamkeit | `GET /data/students` liefert das **Geburtsdatum nur mit Recht „Geburtsdatum pflegen“** (`students.birth_date`, bei Klassenleitung nur für die eigene Klasse) und für die Person selbst. Die **Kurswahl** sehen vollständig nur Planung/Verwaltung und die Betroffenen; übrige Lehrkräfte sehen nur echte Wahlen in mehrteiligen Kursen (wie auf der Klassenseite). Export für Planung/Verwaltung unverändert. | Rechte siehe `ROLLEN-RECHTE.md` |
| S-09 Geheimnisse | iCal-Token nur als HMAC-Hash (Anzeige einmalig beim Erzeugen, `GET /me/ical-url` liefert nur `active`); TOTP-Geheimnis verschlüsselt in neuer Spalte `totp_secret_enc` (AAD `users.totp_secret:<id>`) und in `rotate-keys` aufgenommen. Migration `0045_secrets_at_rest` wandelt Bestandsdaten um (bestehende Kalender-Links bleiben gültig). | – |
| S-10 Proxy-Vertrauen | uvicorn läuft mit `--no-proxy-headers`; `X-Forwarded-*` wertet die App (`server/proxy.py`) nur aus, wenn `SM_TRUST_PROXY=1` **und** die direkte Gegenstelle in `SM_TRUSTED_PROXIES` liegt (leer = nur Loopback). Fremde Gegenstellen verlieren diese Köpfe – IP-Sperre, IP-Allowlists der API-Zugänge, Audit-IP und `Secure`-Cookie lassen sich nicht mehr fälschen. | `SM_TRUST_PROXY`, `SM_TRUSTED_PROXIES`, `SM_PROXY_COUNT`, Compose: `SM_WEB_SUBNET` |
| S-11 Zugriffsprotokoll | Das App-Zugriffsprotokoll kürzt die Client-IP (IPv4 /24, IPv6 /48); nginx-Vorlage kürzt ebenfalls. Login-Versuche (30 Tage) und Audit-Log behalten die volle IP – sie dienen der Sperre bzw. Nachvollziehbarkeit. | `SM_ACCESS_LOG=0` schaltet das Protokoll ganz ab |
| S-13 Chat-Bilder | Kontingent für Chat-Bilder je Konto (Personal 500 MB, Schüler/Eltern 100 MB) und je Chat (1000 MB) sowie höchstens 30 Uploads je 10 Minuten; verständliche Fehlermeldung, Platz wird durch Löschen der Nachricht frei. | `SM_CHAT_QUOTA_MB_STAFF`, `SM_CHAT_QUOTA_MB_STUDENT`, `SM_CHAT_QUOTA_MB_CHAT`, `SM_CHAT_UPLOADS_PER_10MIN` (0 = unbegrenzt) |
| S-14 Lieferkette | `requirements.lock`/`requirements-dev.lock` mit Hashes (`make lock`), Dockerfile und CI installieren daraus mit `--require-hashes`; CI-Job „Abhängigkeits-Audit“ (`pip-audit`, `npm audit`); lokal `make audit`. | – |
| S-15 API-Doku | `/api/docs` und `/api/openapi.json` nur für angemeldete Administratoren (oder aus); Swagger-UI lokal (`server/static/swagger`, swagger-ui-dist 5.33.1, Apache-2.0), CSP ohne CDN und ohne `unsafe-inline` für Skripte. | `SM_ENABLE_DOCS=0\|admin\|1` |

Hinweis zu S-10: Läuft die App **direkt** erreichbar (`docker run -p 8000:8000`), setzt man `SM_TRUST_PROXY` nicht
(oder lässt `SM_TRUSTED_PROXIES` leer) – dann gilt immer die echte Adresse der Verbindung. Der Wert `*` ist nur zulässig,
wenn die App garantiert nur hinter dem Proxy erreichbar ist (die App warnt beim Start).

---

## 5. Incident-Ablauf (Sicherheitsvorfall / Datenpanne)

Beispiele: Verdacht auf fremden Zugriff, kompromittiertes Konto, verlorenes Gerät mit Admin-Sitzung,
Zugangsbriefe falsch verteilt, Ransomware auf dem Server, Backup-Datei öffentlich zugänglich.

**Grundsatz:** Ruhe bewahren, nichts vorschnell löschen, alles mit Uhrzeit protokollieren. Die Frist für
die Meldung an die Aufsichtsbehörde beträgt **72 Stunden ab Kenntnis** (Art. 33 DSGVO).

| Schritt | Was | Wer | Wie (technisch) |
|---|---|---|---|
| 1. Erkennen & melden | Vorfall sofort an IT-Betreuung **und** Schulleitung melden; DSB informieren | alle | Kontaktliste (Abschnitt 6) |
| 2. Eindämmen | betroffene Konten sperren, Sitzungen beenden, Zugänge ändern; bei Server-Kompromittierung Netz trennen | IT | *Benutzer* → deaktivieren / „alle Sitzungen beenden“; `schulmanager-admin reset-password --username …`; bei breitem Verdacht `SM_SECRET_KEY` neu setzen (meldet **alle** ab, API-Tokens ungültig) und `make up`; iCal-Links betroffener Nutzer neu erzeugen; `docker compose stop caddy` (Dienst offline) |
| 3. Beweise sichern | Logs, Audit-Log, Datenbankstand sichern, **bevor** etwas bereinigt wird | IT | `docker compose logs --no-color > vorfall-<datum>.log`; `make backup` (Label); Audit-Export (*Audit*); Hoster-Snapshot der VM |
| 4. Bewerten | Welche Daten, wie viele Personen, welches Risiko (Minderjährige, Art.-9-Daten)? | Schulleitung + DSB + IT | Audit-Log (`GET /api/v1/audit?since=…`), Zugriffslogs (Request-IDs), Konten-Liste |
| 5. Melden | Aufsichtsbehörde binnen 72 h (außer „voraussichtlich kein Risiko“ – Begründung dokumentieren); bei hohem Risiko Betroffene benachrichtigen (Art. 34); Schulaufsicht/Schulträger nach Landesvorgabe | Schulleitung (Verantwortlicher) mit DSB | Meldeformular der Landesdatenschutzbehörde |
| 6. Wiederherstellen | Ursache beseitigen (Update, Konfiguration, Passwort), ggf. sauberes System neu aufsetzen und **Backup von vor dem Vorfall** einspielen | IT | BETRIEB.md Abschnitt 7 (Disaster Recovery); alle Geheimnisse (Abschnitt 4.4) rotieren |
| 7. Nachbereiten | Ursachenanalyse, Maßnahmen, TOMs anpassen, Dokumentation (Art. 33 Abs. 5: jede Panne dokumentieren, auch nicht meldepflichtige) | Schulleitung + IT + DSB | Vorfallsbericht (Vorlage unten) |

Sonderfälle:

* **Ransomware/Server kompromittiert:** Server nicht weiterverwenden. Neu aufsetzen (frisches OS, neue
  Geheimnisse), Backup aus der (versionierten) Offsite-Kopie von vor dem Befall einspielen, vorher
  im Test-Restore prüfen.
* **Zugangsbriefe falsch verteilt:** betroffene Konten zurücksetzen (`POST /users/{id}/reset-password` bzw.
  *Benutzer*), neue Briefe ausgeben; i. d. R. Dokumentation, Meldung nach Risikobewertung.
* **Gerät mit aktiver Sitzung verloren:** Sitzungen des Kontos beenden (*Benutzer → Sitzungen*), Passwort
  ändern, ggf. 2FA neu einrichten.

---

## 6. Vorlagen

### Kontaktliste (ausfüllen, ausdrucken, offline aufbewahren)

| Funktion | Name | Telefon | E-Mail | Vertretung |
|---|---|---|---|---|
| Schulleitung (Verantwortlicher) | | | | |
| IT-Betreuung / Administration | | | | |
| Datenschutzbeauftragte/r | | | | |
| Hoster / Rechenzentrum (Support, Vertragsnr.) | | | | |
| Schulträger IT | | | | |
| Aufsichtsbehörde (Landesdatenschutz) | | | | |

### Eintrag im Verzeichnis von Verarbeitungstätigkeiten (Stichpunkte)

* **Bezeichnung:** Stunden- und Vertretungsplanung „Schulmanager“
* **Zwecke:** Erstellung von Stundenplänen, Vertretungsplanung, Raum-/Aufsichts-/Klausurplanung,
  Information über Planänderungen, Krankmeldungen
* **Rechtsgrundlage:** Art. 6 Abs. 1 lit. e DSGVO i. V. m. Landesschulgesetz; Beschäftigtendatenschutz
* **Betroffene:** Schüler, Erziehungsberechtigte, Lehrkräfte, sonstiges Personal
* **Datenkategorien:** siehe Abschnitt 2.2
* **Empfänger:** Schulpersonal nach Rollen; Auftragsverarbeiter (Abschnitt 2.6); ggf. Schnittstellen
  (Untis, Schulmanager Online) nach Freigabe
* **Drittlandübermittlung:** keine
* **Löschfristen:** Abschnitt 2.4
* **TOMs:** Abschnitt 3 und 4

### Vorfallsbericht (Kurzform)

```
Datum/Uhrzeit Kenntnis: ……………   Gemeldet von: ……………
Beschreibung: ………………………………………………………………………
Betroffene Daten/Personen (Anzahl, Kategorien): ……………………
Sofortmaßnahmen (mit Uhrzeit): ……………………………………………
Risikobewertung (gering/mittel/hoch, Begründung): ………………
Meldung Aufsichtsbehörde: ja/nein, am ……… (Aktenzeichen ………)
Benachrichtigung Betroffener: ja/nein, am ………
Ursache: ……………………………   Dauerhafte Maßnahmen: ……………………
Abgeschlossen am: ………   Unterschrift Schulleitung: ………
```


## Anmelde-Härtung, SSRF-Schutz und Demo-Schutz (Prüfbericht 13.10.2026, S-02 bis S-06, S-16, S-17)

### Ausgehende Verbindungen (`server/net_guard.py`)
Alles, was Nutzer oder Administration konfigurieren können, läuft über eine zentrale Zielprüfung: Postfach-Server (IMAP
993, SMTP 465/587/25), Webhooks, OIDC/SSO-Discovery und JWKS (443/8443), SMS-Webhook, Ferien-Dienst, Lizenzserver.
* Der Hostname wird bei **jeder** Verbindung aufgelöst; **alle** Adressen müssen öffentlich sein (nicht loopback, privat,
  link-local, Metadaten, CGNAT, Multicast; IPv6 inkl. eingebetteter IPv4). Verbunden wird mit der geprüften Adresse
  (kein DNS-Rebinding), TLS prüft weiter gegen den Namen. Keine Weiterleitungen; Antwortinhalte stehen nie in Meldungen.
* **Ausnahmen für schulinterne Ziele** (Mailserver, Keycloak …): Umgebungsvariable `SM_OUTBOUND_ALLOW`, kommagetrennt,
  Hostname, IP oder Netz, optional `:port` – z. B. `SM_OUTBOUND_ALLOW=mail.schule.lokal,10.20.0.0/24,keycloak.schule.lokal:8443`.
  Die Ausnahme hebt nur die Adressprüfung auf, die Ports des Dienstes bleiben. Der Server-eigene SMTP-Relay
  (`SM_SMTP_HOST`) und Datenbank/ClamAV sind Betreiber-Konfiguration und nicht betroffen.
* **Postfach – wer darf eigene Server eintragen?** Die bekannten Anbieter (Google, GMX, Web.de, T-Online, Yahoo, Apple,
  Microsoft) haben feste Server; Host/Port aus dem Aufruf werden ignoriert. „Anderer Anbieter“ mit eigenem IMAP-/SMTP-Server
  erfordert das Recht **`mail.custom_server`** (Standard: Administration, Schulleitung, Sekretariat; vergebbar an Personal,
  nie an Schüler/innen, Eltern, Hausmeister, Monitor). Begründung: Das Postfach ist für Alltagskonten (Gmail & Co.) gedacht;
  ein eigener Server ist die Ausnahme und kommt nur bei der Schule selbst vor. So bleibt der Port-Scan-Weg zu, ohne Lehrkräfte
  mit Standard-Anbietern einzuschränken.

### Demo-Schutz als Allowlist (`server/demo_guard.py`, für „Demo/Produktiv“-Profil)
Bei `SM_DEMO_PUBLIC` (bzw. dem Demo-Modus des Betriebsprofils) ist **jede schreibende Anfrage gesperrt, die nicht in
`demo_guard.ALLOW` steht**. Freigegeben ist, was eine Vorführung braucht (Stundenplan, Vertretung, Klassen, Konten anlegen,
Kursräume, Nachrichten, Notenbuch …). Gesperrt: SSO-Anbieter, Rechte, Anmelde-Richtlinien, Import (JSON/CSV/Untis), Verlauf/
Rückgängig, API-Zugänge, Mail-Konten, Lizenz, Sicherheits-Einstellungen, Benachrichtigungs-Einstellungen der Schule und
Postausgang, Ferien-Import, Briefversand per E-Mail, Kontakt-/Anbieter-Verknüpfungen, Systemverwaltung, Webhooks in den
Einstellungen. **Neue Routen sind automatisch gesperrt**; wer eine freigibt, ergänzt `ALLOW` (der Test
`tests/test_demo_guard.py` prüft alle Routen, die Pflicht-Sperrliste und dass kein Eintrag veraltet ist).
Hinweis für die Betriebsprofile: Die Prüfung hängt an `config.demo_public`; wird dieses Flag durch ein Profil ersetzt, muss
`deps._guard_demo` weiter `demo_guard.check()` aufrufen.

### Anmelde-Drosselung (`server/login_throttle.py`)
Keine harte Kontosperre mehr (sie ließ sich gegen fremde Konten missbrauchen). Stattdessen wartet bei Überschreiten der
Schwelle (`SM_LOGIN_MAX_FAILURES`, 5) der **Anschluss (IP) für dieses Konto** 30 s, danach doppelt so lange bis höchstens
`SM_LOGIN_LOCK_MINUTES` (15). Weitere Zähler: je IP über alle Konten (`SM_LOGIN_MAX_FAILURES_IP`, 30) und je Konto über alle
Anschlüsse (nur wirksam für IPs, von denen sich das Konto nicht zuletzt erfolgreich angemeldet hat). Gedrosselte Anfragen
zählen nicht mit. Die Inhaberin bleibt über „Passwort vergessen“ und SSO erreichbar. Unter **Sicherheit** sehen
Konten-Verwaltende die aktuellen Bremsen und heben sie auf (Protokoll `login_lock.clear`); CLI `unlock` bleibt.
2FA-Konten (Änderung 16.10.2026, ersetzt die einheitliche Antwort aus S-16): **zweistufige Anmeldung.** Schritt 1 sendet Benutzername und
Passwort. Stimmt das Passwort und hat das Konto 2FA, antwortet der Server `200 {"totp_required": true}` ohne Sitzung, und die Seite fragt den
Code ab (Schritt 2: derselbe Aufruf mit `totp`). Falsches Passwort bleibt `401 invalid_credentials`; ein falscher oder schon benutzter Code ebenso.
Begründung: S-16 wollte verhindern, dass die Antwort verrät, ob das Passwort stimmte; dafür zeigte die Seite für alle ein Code-Feld, das
bei 99 Prozent der Konten sinnlos war. Die Zwei-Schritt-Anmeldung ist der übliche Weg (Google, Microsoft). Der Preis: Wer das Passwort bereits erraten hat,
erfährt, dass das Konto 2FA nutzt. Das ist kein Gewinn für ihn, denn das Passwort allein reicht nicht. Was erhalten bleibt:
(1) Jedes falsche Passwort und jeder falsche Code zählt als Fehlversuch und wird nach S-04 progressiv gedrosselt (Konto/IP-Paar, IP, Konto);
(2) Schritt 1 zählt weder als Fehlversuch noch als Erfolg, sonst ließen sich falsche Codes beliebig oft raten (ein Erfolg setzt die Fehlversuche zurück);
(3) gedrosselte Anfragen werden vor der Passwortprüfung abgewiesen (429), auch für Schritt 2; (4) Codes sind einmalig (Wiederverwendungssperre).
Der Aufruf bleibt zustandslos (das Passwort wird in Schritt 2 erneut geprüft), es gibt kein Zwischentoken, das gestohlen werden könnte.
Gilt genauso für „Weiteres Konto anmelden“ (`?add=true`). Tests: `tests/test_login_security.py` (`test_2fa_*`).

### Startpasswörter
Es wird kein Klartext aufbewahrt. `account_initial_passwords` merkt nur Hash und Ablauf (Standard 14 Tage, einstellbar
unter Sicherheit). Nach Ablauf lehnt die Anmeldung das richtige Startpasswort mit `initial_password_expired` ab; die
Verwaltung erzeugt ein neues („Passwort zurücksetzen“). Die Marke fällt beim Passwortwechsel und beim Reset über
„Passwort vergessen“. Der Briefstapel mit dem Klartext bleibt wie bisher nur verschlüsselt und höchstens 60 Minuten.

### Zwei-Faktor und Sitzungen für Personal
Schul-Einstellung `twofa_mode`: **Aus**, **Empfohlen** (Voreinstellung für Administration, Schulleitung, Sekretariat: Hinweis
auf der Startseite) oder **Pflicht** (Einrichtung unter `/zwei-faktor`, bis dahin ist die API gesperrt). Die feste Pflicht per
`SM_REQUIRE_2FA_ROLES` gilt weiter. Personal wird nach 12 h Inaktivität abgemeldet (einstellbar 15 Minuten bis 7 Tage;
Schüler/innen und Eltern: `SM_SESSION_IDLE_MINUTES`). Der SSO-Hinweis-Cookie `sm_sso_hint` enthält nur noch die
Anbieter-Kennung; die E-Mail steht verschlüsselt im httponly-Cookie `sm_sso_who`.

