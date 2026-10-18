# Technische und organisatorische Maßnahmen (Art. 32 DSGVO) – aus dem Code abgeleitet

> **Vorlage, keine Rechtsberatung.** Der Teil „Software“ beschreibt, was Schulpuls tatsächlich tut (mit Fundstelle im Code). Der Teil „Betrieb“ ist von der Schule und ihrem Hoster zu belegen. Weitere Checkliste zum Abhaken: [`../SICHERHEIT.md`](../SICHERHEIT.md) §3.

## 1. Maßnahmen der Software

### Vertraulichkeit

| Maßnahme | Umsetzung | Fundstelle |
|---|---|---|
| Rollen- und Rechtekonzept (Need-to-know) | 12 Rollen, Rechte und Datenumfang (z. B. eigene Klassen) werden im Backend je Anfrage geprüft; fremde Daten liefern „nicht gefunden“. Das Frontend blendet nur aus. | `permissions.py`, `deps.py`, `parent_access.py`, `docs/ROLLEN-RECHTE.md` |
| Passwortschutz | Mindestlänge 10 Zeichen (Schüler 8), Trivialpasswörter und Benutzername im Passwort abgelehnt, Speicherung als scrypt-Hash | `security.py` |
| Zwei-Faktor-Anmeldung | TOTP; je Rolle erzwingbar (`SM_REQUIRE_2FA_ROLES`); Geheimnis verschlüsselt gespeichert | `routes/auth.py`, `crypto.py` |
| Schutz vor Raten von Passwörtern | Sperre je Konto und je IP-Adresse nach Fehlversuchen, Wartezeit | `login_policy.py`, `SM_LOGIN_MAX_FAILURES*` |
| Sitzungen | Ablauf bei Inaktivität und absolut; Cookie `HttpOnly`, `SameSite=Lax`, `Secure`; CSRF-Token bei ändernden Anfragen | `deps.py`, `config.py` |
| Inhaltsverschlüsselung | AES-256-GCM mit Datenschlüssel je Objekt und Master-Schlüssel (`SM_ENCRYPTION_KEYS`): Nachrichten, Dateien samt Dateinamen, Atteste, Gründe und Vermerke von Krankmeldungen, Freitexte in Anträgen; Bindung an Tabelle/Feld/Datensatz | `crypto.py`, `files.py` |
| Schlüsselverwaltung | Schlüsselring mit Kennungen, Rotation ohne Ausfall (`cli rotate-keys`), Anzeige nur von Kennung und Fingerabdruck | `crypto.py`, `cli.py`, Menü *Betrieb* |
| Transportverschlüsselung | HTTPS mit HSTS am Reverse-Proxy; Start im Echtbetrieb nur mit `https://`-Adresse | `deploy/Caddyfile`, `config.py` |
| Schutz vor Schadinhalten | Content-Security-Policy ohne externe Ressourcen, `nosniff`, `X-Frame-Options`, Referrer-Policy; optional Virenscan der Uploads (ClamAV) | `middleware.py`, `files.py` |
| Schutz vor Server-Anfragen an interne Ziele | Ausgehende Verbindungen (Webhooks, Anmeldedienste, Mail-Abruf) werden gegen interne Adressen geprüft | `net_guard`, `SM_OUTBOUND_ALLOW` |
| Geheime Links und Zugänge | iCal-Links und API-Zugänge nur als Hash gespeichert, Anzeige einmalig; Zugangsbriefe nur eine Stunde abrufbar | `security.py`, `letters.py` |
| Datensparsamkeit | keine Abwesenheitsgründe in Exporten, Monitor und iCal; Monitor ohne Gründe; IP-Adressen in Logs gekürzt | `routes/*`, `logging_setup.py` |
| Trennung | je Schule eine eigene Instanz und Datenbank | Betriebskonzept |
| Echtbetrieb ohne Demo | `SM_MODE=production`: keine Demo-Daten, keine Demo-Konten, keine Entwicklungspasswörter, Test-Postausgang und Test-Anmeldedienst verboten; Start bricht sonst ab | `config.py` (`mode_problems`) |

### Integrität

| Maßnahme | Umsetzung | Fundstelle |
|---|---|---|
| Nachvollziehbarkeit | Audit-Protokoll für jede schreibende Aktion (wer, wann, was; ohne Inhalte), Planversionen mit Verlauf und Rückgängig | `audit.py`, `store.py` |
| Manipulationserkennung | Authentifizierte Verschlüsselung erkennt veränderte, abgeschnittene oder vertauschte Daten | `crypto.py` |
| Vorschau vor Massenänderungen | Schuljahreswechsel und Import mit Vorschau, Token-Bindung und Rückgängig | `year_change.py` |
| Signierte Webhooks | HMAC-Signatur (`SM_WEBHOOK_SECRET`) | `notify.py` |

### Verfügbarkeit und Belastbarkeit

| Maßnahme | Umsetzung | Fundstelle |
|---|---|---|
| Sicherung | täglich Datenbank und Dateien, Rotation 14/8/12, GPG-Verschlüsselung, optional Offsite, Healthcheck der Sicherung | `scripts/backup.sh`, `deploy/backup` |
| Wiederherstellung prüfbar | „Prüfen“ (Test-Restore einer App-Sicherung in Wegwerf-Kopie), `make restore-test` | `ops.py`, Menü *Betrieb* |
| Überwachung | Statusseite (Datenbank, Schema, Speicher, Sicherung, Mail, Lizenz, Wartung), Fehlerprotokoll, `/healthz`, Metriken für Prometheus | `ops.py`, `app.py` |
| Wartung | stündlicher Wartungslauf: abgelaufene Sitzungen, Tokens, Anmeldeversuche, verwaiste Dateien | `maintenance.py` |
| Container-Härtung | unprivilegierter Benutzer, schreibgeschütztes Dateisystem, Datenbank nur im internen Netz | `Dockerfile`, `docker-compose.yml` |

### Verfahren zur Überprüfung und Löschung

| Maßnahme | Umsetzung |
|---|---|
| Löschfristen | Wartungslauf löscht Atteste, Formular-Einreichungen, Nachrichten, Papierkorb, Sitzungen und Protokolle nach Frist; Löschkonzept: [`../DATENSCHUTZ-LOESCHKONZEPT.md`](../DATENSCHUTZ-LOESCHKONZEPT.md) |
| Schuljahreswechsel | Abgänger werden ausgetragen, ihre Konten gesperrt; Löschung nach Frist durch das Löschkonzept |
| Auskunft | Auskunft zu einer Person als Export (siehe Löschkonzept) |

## 2. Maßnahmen im Betrieb (von der Schule zu belegen)

| Bereich | Maßnahme | Verantwortlich | Nachweis / Datum |
|---|---|---|---|
| Zutritt | Server in zertifiziertem Rechenzentrum oder abgeschlossenem Serverraum | [ ] | [Zertifikat Hoster] |
| Zugang Server | SSH nur mit Schlüssel, kein Root-Passwort-Login, Zugriff nur aus Admin-Netz/VPN | [ ] | |
| Zugriff Anwendung | Administrationskonten personengebunden, Zwei-Faktor für Administration, Schulleitung, Sekretariat | [ ] | |
| Rechteprüfung | jährlich zum Schuljahreswechsel Konten und Rollen prüfen | [ ] | |
| Schlüssel | `SM_ENCRYPTION_KEYS` und Sicherungs-Passphrase getrennt von Sicherungen im Tresor | [ ] | |
| Sicherung | Offsite-Kopie vorhanden; Test-Restore monatlich, vollständiger Probe-Restore halbjährlich, dokumentiert | [ ] | |
| Updates | monatlicher Patchtag (Betriebssystem, Container, Anwendung) | [ ] | |
| Netz | Firewall: nur 22 (eingeschränkt), 80, 443 | [ ] | |
| Personal | Schulung zu Passwörtern, Zugangsbriefen, Exporten, Meldewegen | [ ] | |
| Datenpanne | Meldeweg und Kontaktliste bekannt (72-Stunden-Frist) | [ ] | `../SICHERHEIT.md` §5 |
| Verträge | AV-Verträge liegen vor (siehe `README.md`) | [ ] | |
| Endgeräte | Bildschirmsperre, aktuelle Browser, keine Passwörter im Browser auf Gemeinschaftsgeräten | [ ] | |
