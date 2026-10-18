# Z6a – Datenmodell als Tabellen

Stand: 2026-10-18. Quellen: Kerntabellen-Modul sowie alle Feature-Modelle, deren Name mit a–f beginnt (10 Module). Umfang: 56 Tabellen (13 Kerntabellen, 43 Feature-Tabellen). Geheimnisse, Schlüssel und Zugangsdaten sind nicht enthalten.

Hinweis: Die Liste aller Kerntabellen im Quellmodul nennt nur 10 Tabellen. `role_overrides`, `branches` und `user_branches` fehlen dort, sind aber Modelle und hier aufgenommen.

---

## 0. Konventionen

| Begriff | Bedeutung |
|---|---|
| Text(n) | Text, maximal n Zeichen |
| Text | Text ohne Längenbegrenzung |
| Ganzzahl | ganze Zahl |
| Große Ganzzahl | ganze Zahl für Dateigrößen (Bytes) |
| Dezimalzahl | Zahl mit Nachkommastellen (Punkte) |
| Wahrheitswert | ja / nein |
| Zeitpunkt | Datum und Uhrzeit in UTC, ohne Zeitzone |
| Datum | Text im Format YYYY-MM-DD (10 Zeichen) |
| JSON | strukturierte Liste oder Objekt |
| Binär | Bytefolge (BLOB) |
| Pflicht | Feld muss gesetzt sein (ggf. über den Standard) |
| optional | Feld darf leer sein (NULL) |
| Standard | Wert bei Anlage, wenn nichts angegeben wird. "automatisch" = fortlaufende Nummer. "jetzt (UTC)" = Zeitpunkt der Anlage |
| Fremdschlüssel | "Kaskade" = Zeile wird mit dem Elternteil gelöscht. "Feld leeren" = Feld wird NULL. "ID-Verweis" = nur Zahl/Text, keine Datenbankbeziehung |
| verschl. | Inhalt wird verschlüsselt gespeichert. Die Kontext-Bindung (AAD) lautet `Tabelle.Feld:ID`; die ID muss vor dem Verschlüsseln feststehen |
| Hash | nur Hash bzw. HMAC gespeichert, nicht rückrechenbar |
| [unklar] | im Quellmodell nicht festgelegt |

Die Felder "aktualisiert am" setzt die Anwendung bei jeder Änderung selbst. Das Modell hat dafür keine automatische Aktualisierung.

---

## 1. Kerntabellen (13)

### 1.1 users
**Zweck:** Konto jeder Person (Schüler/in, Lehrkraft, Eltern, Verwaltung) mit Anmeldedaten und Rolle.
**Eindeutig:** username, oidc_sub, ical_token.
**Indizes:** username, role, custom_role, teacher_id, student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| username | Text(80) | Pflicht | – | – | eindeutig; Anmeldename |
| display_name | Text(200) | Pflicht | "" | – | Anzeigename |
| role | Text(20) | Pflicht | – | – | Grundrolle, Werte siehe Abschnitt 3; indiziert |
| custom_role | Text(20) | optional | NULL | ID-Verweis auf eigene Schulrolle | indiziert; die Grundrolle steht in role |
| password_hash | Text(255) | optional | NULL | – | Hash des Passworts; Verfahren [unklar] |
| must_change_password | Wahrheitswert | Pflicht | nein | – | Passwortwechsel beim nächsten Anmelden erzwingen |
| totp_secret | Text(64) | optional | NULL | – | veraltet: Klartext-Altbestand, nach Umstellung leer; im Neubau nicht nötig |
| totp_secret_enc | Text(255) | optional | NULL | – | verschl. TOTP-Geheimnis; Kontext users.totp_secret:ID |
| totp_enabled | Wahrheitswert | Pflicht | nein | – | Zwei-Faktor-Anmeldung (TOTP) aktiv |
| teacher_id | Text(40) | optional | NULL | ID-Verweis (Planungsdokument) | indiziert |
| student_id | Text(40) | optional | NULL | ID-Verweis (Planungsdokument) | indiziert |
| site | Text(40) | optional | NULL | – | Schulstandort |
| active | Wahrheitswert | Pflicht | ja | – | nein = Konto deaktiviert |
| ical_token | Text(64) | optional | NULL | – | eindeutig; nur Hash gespeichert (HMAC); für Kalender-Abo |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| last_login | Zeitpunkt | optional | NULL | – | letzte erfolgreiche Anmeldung |
| email | Text(254) | optional | NULL | – | E-Mail-Adresse; Bestätigung siehe user_contacts |
| adult | Wahrheitswert | Pflicht | nein | – | volljährige/r Schüler/in: darf Krankmeldung selbst abgeben |
| oidc_sub | Text(255) | optional | NULL | – | eindeutig; Kennung beim externen Anmeldedienst |

[unklar] Eine Spalte für die Freigabe der Kursräume an Eltern (volljährige Schüler/innen) ist im Modell nicht erkennbar.

### 1.2 sessions
**Zweck:** Angemeldete Sitzung eines Kontos (Cookie `sm_session`). Gespeichert wird nur der Hash des Tokens.
**Eindeutig:** token_hash.
**Indizes:** token_hash, user_id, expires_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| token_hash | Text(64) | Pflicht | – | – | Hash des Sitzungstokens; eindeutig; indiziert |
| csrf_token | Text(64) | Pflicht | – | – | Schutzwert gegen Fremdanfragen, je Sitzung |
| user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | indiziert |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| expires_at | Zeitpunkt | Pflicht | – | – | Ablaufzeitpunkt; indiziert; Dauer [unklar] |
| last_seen | Zeitpunkt | Pflicht | jetzt (UTC) | – | letzte Aktivität |
| ip | Text(64) | optional | NULL | – | IP-Adresse bei Anmeldung |
| user_agent | Text(300) | optional | NULL | – | Browserkennung |

### 1.3 api_tokens
**Zweck:** API-Zugang eines Kontos. Entweder persönliches Token mit allen Rechten des Kontos oder Zugang mit eingeschränktem Umfang (nur öffentliche API).
**Eindeutig:** token_hash.
**Indizes:** user_id, token_hash.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | Inhaber; indiziert |
| name | Text(100) | Pflicht | "" | – | Bezeichnung |
| token_hash | Text(64) | Pflicht | – | – | Hash des Tokens; eindeutig; indiziert; Klartext nicht gespeichert |
| prefix | Text(16) | Pflicht | "" | – | Anzeige-Präfix zur Wiedererkennung (sma_ bzw. smt_, siehe Abschnitt 3) |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| last_used | Zeitpunkt | optional | NULL | – | letzte Nutzung |
| expires_at | Zeitpunkt | optional | NULL | – | Ablauf; NULL = [unklar], ob unbefristet |
| purpose | Text(300) | Pflicht | "" | – | Verwendungszweck (Freitext) |
| scope | JSON | optional | NULL | – | NULL = persönliches Token mit allen Rechten des Kontos; sonst Bereiche und Filter der öffentlichen API |
| ip_allow | JSON | optional | NULL | – | Liste erlaubter IP-Adressen; Format und Bedeutung von NULL [unklar] |
| rate_limit | Ganzzahl | optional | NULL | – | Anfragen pro Minute; NULL = [unklar] |
| revoked_at | Zeitpunkt | optional | NULL | – | gesetzt = widerrufen |
| use_count | Ganzzahl | Pflicht | 0 | – | Zähler der Anfragen |

### 1.4 login_attempts
**Zweck:** Protokoll jedes Anmeldeversuchs. Auswertung je Benutzername und je IP (Sperren/Rate-Limit; Schwelle [unklar]).
**Eindeutig:** –.
**Indizes:** created_at; (username, created_at); (ip, created_at).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| username | Text(80) | Pflicht | – | – | eingegebener Benutzername, kein Fremdschlüssel (auch unbekannte Namen) |
| ip | Text(64) | optional | NULL | – | IP-Adresse |
| success | Wahrheitswert | Pflicht | nein | – | Anmeldung erfolgreich |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |

### 1.5 parent_links
**Zweck:** Verknüpfung eines Elternkontos mit einem Kind.
**Eindeutig:** (parent_user_id, student_id).
**Indizes:** parent_user_id, student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| parent_user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | Elternkonto; indiziert |
| student_id | Text(40) | Pflicht | – | ID-Verweis (Planungsdokument) | Schüler/in-ID; indiziert |

### 1.6 role_overrides
**Zweck:** Schulspezifische Abweichung vom Standard der Rollenrechte.
**Schlüssel:** (role, permission).
**Indizes:** Schlüssel.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| role | Text(20) | Pflicht (Schlüssel) | – | – | Rolle, Werte siehe Abschnitt 3 |
| permission | Text(60) | Pflicht (Schlüssel) | – | – | Rechteschlüssel |
| granted | Wahrheitswert | Pflicht | ja | – | ja = Recht erteilt, nein = entzogen |
| scope | Text(30) | optional | NULL | – | NULL = Standardumfang der Rolle; all = uneingeschränkt; sonst eingeschränkter Umfang (Beispiel own_classes) |
| updated_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_by | Text(80) | Pflicht | "" | – | Name der ändernden Person |

Hinweis: Feste Mindestregeln gelten zusätzlich immer und sind im Modell nicht aufgeführt [unklar].

### 1.7 branches
**Zweck:** Schulzweig bzw. Abteilung. Fasst Klassen nach Standort, Klassenstufe oder einzelnen Klassen zusammen.
**Eindeutig:** name.
**Indizes:** name.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| name | Text(80) | Pflicht | – | – | eindeutig |
| sites | JSON | optional | NULL | – | Liste der Standorte |
| grades | JSON | optional | NULL | – | Liste der Klassenstufen (ganze Zahlen) |
| class_ids | JSON | optional | NULL | – | Liste der Klassen-IDs |

### 1.8 user_branches
**Zweck:** Zuordnung Konto (Abteilungsleitung) zu Zweig.
**Schlüssel:** (user_id, branch_id).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| user_id | Ganzzahl | Pflicht (Schlüssel) | – | users.id, Kaskade | |
| branch_id | Ganzzahl | Pflicht (Schlüssel) | – | branches.id, Kaskade | |

### 1.9 audit_log
**Zweck:** Protokoll von Verwaltungs- und Sicherheitsaktionen.
**Eindeutig:** –.
**Indizes:** created_at, user_id, action.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |
| user_id | Ganzzahl | optional | NULL | users.id, Feld leeren | handelnde Person; indiziert |
| username | Text(80) | Pflicht | "" | – | Benutzername zum Zeitpunkt der Aktion (Klartext) |
| action | Text(80) | Pflicht | – | – | Aktionsname; indiziert |
| target | Text(200) | Pflicht | "" | – | betroffenes Objekt (Klartext) |
| details | JSON | optional | NULL | – | Zusatzangaben |
| ip | Text(64) | optional | NULL | – | IP-Adresse |

### 1.10 school_versions
**Zweck:** Versionen (Stände) des Planungsdokuments, auch als Grundlage für Wiederherstellung.
**Eindeutig:** –.
**Indizes:** –.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| user_id | Ganzzahl | optional | NULL | users.id, Feld leeren | Urheber |
| message | Text(500) | Pflicht | "" | – | Versionsnotiz |
| scope | JSON (Liste von Texten) | optional | NULL | – | betroffene Bereiche |
| data | Binär | Pflicht | – | – | verschl. Inhalt des Planungsdokuments; zuvor komprimiert (zlib); Token-Format SM1; Kontext school_versions.data:ID |
| restored_from | Ganzzahl | optional | NULL | ID-Verweis | ID der Version, aus der wiederhergestellt wurde (Wiederherstellen/Rückgängig) |

Hinweis: Altbestand ohne Verschlüsselung (nur komprimiert) wird beim Start und durch die Schlüsselrotation (CLI-Befehl `rotate-keys`) verschlüsselt.

### 1.11 announcements
**Zweck:** Mitteilung für eine Zielgruppe mit Gültigkeitszeitraum.
**Eindeutig:** –.
**Indizes:** created_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| title | Text(200) | Pflicht | – | – | Titel |
| body | Text | Pflicht | "" | – | Inhalt |
| author_id | Ganzzahl | optional | NULL | users.id, Feld leeren | Autor |
| author_name | Text(200) | Pflicht | "" | – | Name des Autors |
| audience | Text(20) | Pflicht | all | – | all / staff / classes |
| audience_roles | JSON | optional | NULL | – | Liste der Rollen der Zielgruppe (Zuordnung zu audience [unklar]) |
| class_ids | JSON | optional | NULL | – | Liste der Klassen-IDs der Zielgruppe |
| site | Text(40) | optional | NULL | – | Standort |
| valid_from | Datum | optional | NULL | – | gültig ab |
| valid_to | Datum | optional | NULL | – | gültig bis |
| pinned | Wahrheitswert | Pflicht | nein | – | angeheftet |
| priority | Text(20) | Pflicht | normal | – | normal / wichtig |
| monitor | Wahrheitswert | Pflicht | nein | – | für die Monitoranzeige vorgesehen (Wirkung [unklar]) |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |

### 1.12 student_absences
**Zweck:** Krankmeldung oder Fehlzeit eines Schülers (Art, Zeitraum, Stunden, Status, Entschuldigung).
**Eindeutig:** –.
**Indizes:** student_id, date_from, kind, register_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| student_id | Text(40) | Pflicht | – | ID-Verweis (Planungsdokument) | indiziert |
| date_from | Datum | Pflicht | – | – | erster Fehltag; indiziert |
| date_to | Datum | Pflicht | – | – | letzter Fehltag |
| periods | JSON (Liste ganzer Zahlen) | optional | NULL | – | betroffene Stundennummern |
| reason | Text | Pflicht | "" | – | Grund; im Modell Klartext, nicht verschlüsselt (siehe Abschnitt 5 und 6) |
| status | Text(20) | Pflicht | gemeldet | – | gemeldet / teilweise / entschuldigt / unentschuldigt |
| note | Text | Pflicht | "" | – | Vermerk; Klartext, nicht verschlüsselt |
| kind | Text(20) | Pflicht | krank | – | krank / verspaetung / frueh / fehlt; indiziert |
| minutes | Ganzzahl | optional | NULL | – | Minuten bei Verspätung bzw. frühem Gehen |
| source | Text(20) | Pflicht | online | – | online / telefon / schriftlich / lehrkraft |
| excused_by | Ganzzahl | optional | NULL | ID-Verweis | ID der entschuldigenden Person |
| excused_by_name | Text(200) | Pflicht | "" | – | Name der entschuldigenden Person |
| excused_at | Zeitpunkt | optional | NULL | – | Zeitpunkt der Entschuldigung |
| register_id | Ganzzahl | optional | NULL | ID-Verweis (Klassenbuch) | Eintrag, aus dem die Fehlzeit stammt; beim erneuten Speichern der Stunde angepasst; indiziert |
| reported_by | Ganzzahl | optional | NULL | users.id, Feld leeren | meldende Person |
| reported_by_name | Text(200) | Pflicht | "" | – | Name der meldenden Person |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | letzte Änderung |

### 1.13 notifications_outbox
**Zweck:** Warteschlange ausgehender Benachrichtigungen (Webhook oder E-Mail) mit Wiederholungen.
**Eindeutig:** –.
**Indizes:** status, next_attempt_at, dedupe_key.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| kind | Text(20) | Pflicht | – | – | webhook / email |
| target | Text(500) | Pflicht | – | – | Ziel: URL (Webhook) bzw. E-Mail-Adresse |
| subject | Text(300) | optional | NULL | – | Betreff (E-Mail) |
| payload | Text | Pflicht | "" | – | E-Mail-Text: verschl. (Kontext [unklar]); Webhook: JSON im Klartext |
| status | Text(20) | Pflicht | pending | – | pending / sending / sent / failed; indiziert |
| attempts | Ganzzahl | Pflicht | 0 | – | Zahl der Versuche |
| next_attempt_at | Zeitpunkt | optional | NULL | – | nächster Versuch (UTC); indiziert |
| last_error | Text | optional | NULL | – | letzte Fehlermeldung |
| dedupe_key | Text(200) | optional | NULL | – | Schlüssel gegen doppelte Benachrichtigungen; indiziert |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| sent_at | Zeitpunkt | optional | NULL | – | Versandzeitpunkt |

---

## 2. Feature-Tabellen (43)

### 2.1 api_token_log (Nutzungsprotokoll API-Zugang)
**Zweck:** Ein Eintrag je Anfrage mit API-Token: Zeit, Methode, Pfad ohne Abfrageparameter und ohne Geheimnisse, Bereich, Ergebnis, Status, Dauer, IP. Keine Antwortinhalte, keine Personendaten.
**Eindeutig:** –.
**Indizes:** token_id, at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| token_id | Ganzzahl | Pflicht | – | api_tokens.id, Kaskade | indiziert |
| at | Zeitpunkt | Pflicht | jetzt (UTC) | – | Zeitpunkt der Anfrage; indiziert |
| method | Text(8) | Pflicht | GET | – | HTTP-Methode |
| path | Text(200) | Pflicht | "" | – | Pfad ohne Abfrageparameter und ohne Geheimnisse |
| area | Text(32) | Pflicht | "" | – | Bereich des Zugangs |
| outcome | Text(40) | Pflicht | ok | – | ok / error / ip_denied / rate_limited / blocked; weitere [unklar] |
| ip | Text(64) | optional | NULL | – | IP-Adresse |
| status | Ganzzahl | optional | NULL | – | HTTP-Status der Antwort |
| duration_ms | Ganzzahl | optional | NULL | – | Dauer bis zur Antwort in Millisekunden |

### 2.2 student_absence_events (Meldungsprotokoll Fehlzeiten)
**Zweck:** Unveränderliche Zeitleiste jeder Fehlzeit: wer, wann, über welchen Kanal und jede Änderung (vorher → nachher). Gründe, Vermerke und Diagnosen stehen nie im Protokoll.
**Eindeutig:** –.
**Indizes:** (absence_id, at); student_id; at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| absence_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel (bleibt nach Löschen erhalten) | indiziert |
| student_id | Text(40) | Pflicht | – | ID-Verweis | indiziert |
| at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |
| event | Text(30) | Pflicht | – | – | Werte siehe Abschnitt 3 |
| actor_id | Ganzzahl | optional | NULL | ID-Verweis | handelnde Person; bei Kontolöschung pseudonymisiert |
| actor_name | Text(200) | Pflicht | "" | – | Name; bei Kontolöschung pseudonymisiert |
| actor_role | Text(40) | Pflicht | "" | – | Rollenbezeichnung als Text (z. B. Eltern, Sekretariat, Klassenleitung) |
| channel | Text(20) | Pflicht | "" | – | Werte siehe Abschnitt 3 |
| detail | JSON | optional | NULL | – | nur Zeiträume, Stunden, Status, Art und Kanal |

Hinweis: Ändern und Löschen einzelner Zeilen ist verboten (nur anhängen).

### 2.3 user_contacts (Kontakt und Wiederherstellung)
**Zweck:** Bestätigte E-Mail-Adresse und Handynummer je Konto (für Bestätigung und Passwort-Zurücksetzen).
**Schlüssel:** user_id (ein Eintrag je Konto).
**Indizes:** phone_hash.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| user_id | Ganzzahl (Primärschlüssel) | Pflicht | – | users.id, Kaskade | |
| email_verified_value | Text(254) | optional | NULL | – | bestätigte E-Mail-Adresse in Kleinschreibung |
| email_verified_at | Zeitpunkt | optional | NULL | – | Bestätigungszeitpunkt der E-Mail |
| phone_enc | Text | optional | NULL | – | verschl. Handynummer im Format E.164; Kontext user_contacts.phone:user_id |
| phone_hash | Text(64) | optional | NULL | – | Hash (HMAC mit SM_SECRET_KEY) der Nummer zur Suche; indiziert |
| phone_verified_at | Zeitpunkt | optional | NULL | – | Bestätigungszeitpunkt der Handynummer |
| updated_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

Hinweis: Die E-Mail-Adresse selbst steht nur in users.email. Die Adresse gilt als bestätigt, wenn sie der bestätigten Adresse in Kleinschreibung entspricht.

### 2.4 auth_codes (Einmal-Codes und Rate-Limit)
**Zweck:** Einmal-Codes, Link-Token und Zähler für Bestätigung, Passwort-Zurücksetzen und Rate-Limit.
**Eindeutig:** token_hash.
**Indizes:** user_id; token_hash; ident_hash; expires_at; (user_id, purpose, created_at); (ip, purpose, created_at).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| user_id | Ganzzahl | optional | NULL | users.id, Kaskade | leer bei unbekannter Kennung; indiziert |
| purpose | Text(20) | Pflicht | – | – | verify_email / verify_phone / reset / reset_token / rl_reset / rl_fail |
| channel | Text(10) | optional | NULL | – | email / sms |
| code_hash | Text(64) | optional | NULL | – | Hash (HMAC) des Einmal-Codes; beim Zurücksetzen 6 Ziffern |
| token_hash | Text(64) | optional | NULL | – | Hash (HMAC) des Link- bzw. Reset-Tokens; eindeutig |
| target_enc | Text | optional | NULL | – | verschl. neues Ziel (E-Mail-Adresse bzw. Nummer); Kontext auth_codes.target:ID |
| ident_hash | Text(64) | optional | NULL | – | Hash (HMAC) der eingegebenen Kennung; zählt auch für unbekannte Kennungen; indiziert |
| expires_at | Zeitpunkt | Pflicht | – | – | Ablauf; indiziert; Dauer siehe Abschnitt 4 |
| attempts | Ganzzahl | Pflicht | 0 | – | Fehlversuche; maximal 5 je Code |
| used_at | Zeitpunkt | optional | NULL | – | verbraucht am |
| ip | Text(64) | optional | NULL | – | IP-Adresse der Anfrage |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.5 stored_files (Dateiablage, Metadaten)
**Zweck:** Metadaten verschlüsselt abgelegter Dateien. Der Inhalt liegt verschlüsselt im Dateispeicher.
**Schlüssel:** id (UUID).
**Indizes:** created_at; owner_user_id; deleted_at; (ref_type, ref_id).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Text(36) (Primärschlüssel) | Pflicht | – | – | UUID |
| owner_user_id | Ganzzahl | optional | NULL | users.id, Feld leeren | Eigentümer; indiziert |
| filename | Text | Pflicht | – | – | Spaltenname "filename"; verschl. (Token-Format SM1); Kontext stored_files.filename:ID |
| content_type | Text(150) | Pflicht | – | – | MIME-Typ, aus dem Inhalt erkannt |
| kind | Text(20) | Pflicht | – | – | Dateiart, z. B. pdf, png, docx; vollständige Liste [unklar] |
| size | Große Ganzzahl | Pflicht | – | – | Größe des Klartexts in Bytes |
| sha256 | Text(64) | Pflicht | – | – | SHA-256 des Klartexts (hex); Integritätsprüfung |
| purpose | Text(40) | Pflicht | – | – | Verwendungszweck, z. B. channel_material |
| ref_type | Text(40) | optional | NULL | – | Art des Bezugsobjekts (Anhang an …); Grundlage der Zugriffsprüfung |
| ref_id | Text(80) | optional | NULL | – | ID des Bezugsobjekts |
| key_id | Text(32) | Pflicht | – | – | Kennung des Schlüssels, mit dem der Inhalt verschlüsselt ist |
| scan_status | Text(20) | Pflicht | unscanned | – | clean / unscanned / error |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |
| updated_at | Zeitpunkt | optional | NULL | – | letztes Anhängen oder Lösen |
| deleted_at | Zeitpunkt | optional | NULL | – | Löschzeitpunkt; indiziert |

Hinweis: Standard-Speicherort des Inhalts: SM_DATA_DIR/files/ mit Unterordnern aus der ID [Aufbau der Unterordner unklar]. Zeilen nur über die Upload-Funktion anlegen.

### 2.6 form_templates (Formularvorlage)
**Zweck:** Formularvorlage einer Schule mit Status und aktueller Version.
**Eindeutig:** –.
**Indizes:** category, status.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| title | Text(200) | Pflicht | – | – | Titel |
| description | Text | Pflicht | "" | – | Beschreibung |
| category | Text(30) | Pflicht | sonstiges | – | indiziert; weitere Werte [unklar] |
| status | Text(12) | Pflicht | entwurf | – | entwurf / aktiv / archiviert; indiziert |
| version | Ganzzahl | Pflicht | 1 | – | aktuelle Versionsnummer |
| library_key | Text(60) | optional | NULL | – | Kennung einer Vorlage aus der mitgelieferten Bibliothek |
| sensitive | Wahrheitswert | Pflicht | nein | – | als sensibel markiert (Wirkung [unklar]) |
| created_by | Ganzzahl | optional | NULL | users.id, Feld leeren | Ersteller |
| created_by_name | Text(200) | Pflicht | "" | – | Name des Erstellers |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | |

### 2.7 form_versions (Fassung eines Formulars)
**Zweck:** Unveränderliche Fassung einer Formularvorlage. Jede inhaltliche Änderung erzeugt eine neue Version. Einreichungen bleiben bei der Version, mit der sie ausgefüllt wurden.
**Eindeutig:** (template_id, version).
**Indizes:** template_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| template_id | Ganzzahl | Pflicht | – | form_templates.id, Kaskade | indiziert |
| version | Ganzzahl | Pflicht | – | – | Versionsnummer je Vorlage |
| title | Text(200) | Pflicht | "" | – | Titel dieser Fassung |
| definition | JSON | Pflicht | {} (leeres Objekt) | – | Felder, Zielgruppe, Ablauf, Aktionen (Aufbau [unklar]) |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| created_by_name | Text(200) | Pflicht | "" | – | Name des Erstellers |

### 2.8 form_submissions (Einreichung)
**Zweck:** Einreichung zu einem Formular: Antworten, Schritt, Status, Entscheidung, Fälligkeit.
**Eindeutig:** –.
**Indizes:** template_id, version_id, student_id, class_id, submitted_by, status, due_on, created_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| template_id | Ganzzahl | Pflicht | – | form_templates.id, Kaskade | indiziert |
| version_id | Ganzzahl | Pflicht | – | form_versions.id, Kaskade | indiziert |
| student_id | Text(40) | optional | NULL | ID-Verweis (Planungsdokument) | indiziert |
| class_id | Text(40) | optional | NULL | ID-Verweis (Planungsdokument) | indiziert |
| submitted_by | Ganzzahl | optional | NULL | users.id, Feld leeren | einreichendes Konto; indiziert |
| submitted_by_name | Text(200) | Pflicht | "" | – | Name der einreichenden Person |
| submitted_role | Text(20) | Pflicht | "" | – | Rolle beim Einreichen |
| status | Text(14) | Pflicht | eingereicht | – | indiziert; Dokumentation nennt eingereicht, geprüft, genehmigt, abgelehnt; vollständige Liste [unklar] |
| step | Ganzzahl | Pflicht | 0 | – | aktueller Schritt im Ablauf |
| answers_enc | Text | Pflicht | "" | – | verschl. Antworten; Kontext form_submissions.answers:ID |
| decision_note_enc | Text | Pflicht | "" | – | verschl. Entscheidungsvermerk; Kontext [unklar] |
| scan_file_ids | JSON (Liste) | Pflicht | [] | – | IDs der hochgeladenen Scans in der Dateiablage |
| result | JSON | optional | NULL | – | Ergebnis (Aufbau [unklar]) |
| due_on | Datum | optional | NULL | – | Fälligkeit; indiziert |
| reminded_on | Datum | optional | NULL | – | Datum der letzten Erinnerung |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |
| updated_at | Zeitpunkt | optional | NULL | – | |
| decided_at | Zeitpunkt | optional | NULL | – | Entscheidungszeitpunkt |
| decided_by_name | Text(200) | Pflicht | "" | – | Name der entscheidenden Person |

### 2.9 form_events (Verlauf einer Einreichung)
**Zweck:** Verlauf einer Einreichung (eingereicht, geprüft, genehmigt, abgelehnt, Scan, Erinnerung).
**Eindeutig:** –.
**Indizes:** submission_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| submission_id | Ganzzahl | Pflicht | – | form_submissions.id, Kaskade | indiziert |
| step | Ganzzahl | Pflicht | 0 | – | Schritt |
| action | Text(20) | Pflicht | – | – | Aktion; Werte [unklar] (Dokumentation nennt eingereicht, geprüft, genehmigt, abgelehnt, Scan, Erinnerung) |
| actor_id | Ganzzahl | optional | NULL | users.id, Feld leeren | handelnde Person |
| actor_name | Text(200) | Pflicht | "" | – | Name der handelnden Person |
| note_enc | Text | Pflicht | "" | – | verschl. Notiz; Kontext [unklar] |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.10 grading_templates (Bewertungsvorlage)
**Zweck:** Wiederverwendbare Bewertungsvorlage (Raster oder Leitfaden) einer Lehrkraft.
**Eindeutig:** –.
**Indizes:** owner_user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| owner_user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | Eigentümer; indiziert |
| title | Text(200) | Pflicht | – | – | Titel |
| kind | Text(10) | Pflicht | – | – | rubric (Raster) / guide (Leitfaden) |
| criteria_enc | Text | Pflicht | "" | – | verschl. Kriterien als JSON; Kontext grading_templates.criteria:ID |
| grade_scale | JSON | optional | NULL | – | Notenschlüssel (Aufbau [unklar]) |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | |

### 2.11 assignment_settings (Aufgabeneinstellungen)
**Zweck:** Einstellungen einer Aufgabe im Kursraum: Gruppenabgabe, Punkte, Notenschlüssel, Bewertungsraster, Elternsicht. Das Raster ist eine Kopie der Vorlage, damit spätere Änderungen an der Vorlage bereits bewertete Abgaben nicht verfälschen.
**Eindeutig:** item_id.
**Indizes:** item_id (über die Eindeutigkeit).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| item_id | Ganzzahl | Pflicht | – | channel_items.id, Kaskade | 1:1 zur Aufgabe; eindeutig |
| group_mode | Wahrheitswert | Pflicht | nein | – | Gruppenabgabe |
| group_set_id | Ganzzahl | optional | NULL | channel_group_sets.id, Feld leeren | Einteilung für die Gruppenabgabe |
| max_points | Dezimalzahl | optional | NULL | – | Höchstpunktzahl in Punkten; ohne Raster: freie Höchstpunktzahl |
| grade_scale | JSON | optional | NULL | – | Notenschlüssel (Aufbau [unklar]) |
| rubric_kind | Text(10) | optional | NULL | – | rubric / guide |
| rubric_enc | Text | Pflicht | "" | – | verschl. Raster als JSON; Kontext assignment_settings.rubric:ID |
| rubric_title | Text(200) | Pflicht | "" | – | Titel des Rasters |
| template_id | Ganzzahl | optional | NULL | grading_templates.id, Feld leeren | Herkunftsvorlage |
| show_parents | Wahrheitswert | Pflicht | nein | – | Eltern sehen das ausgefüllte Raster |
| updated_at | Zeitpunkt | optional | NULL | – | |

### 2.12 assignment_extensions (Fristverlängerung)
**Zweck:** Verlängerte Abgabefrist für eine Schülerin/einen Schüler oder eine Gruppe.
**Eindeutig:** (item_id, user_id); (item_id, group_id).
**Indizes:** item_id, user_id, group_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| item_id | Ganzzahl | Pflicht | – | channel_items.id, Kaskade | indiziert |
| user_id | Ganzzahl | optional | NULL | users.id, Kaskade | Schüler/in; indiziert |
| group_id | Ganzzahl | optional | NULL | channel_groups.id, Kaskade | Gruppe; indiziert |
| due_at | Zeitpunkt | Pflicht | – | – | neue Frist (UTC) |
| reason_enc | Text | Pflicht | "" | – | verschl. Begründung; Kontext assignment_extensions.reason:ID |
| created_by | Ganzzahl | optional | NULL | users.id, Feld leeren | angelegt von |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

Hinweis: Vorgesehen ist je Eintrag entweder Schüler/in oder Gruppe. Das Modell erzwingt das nicht [unklar].

### 2.13 assignment_submission_versions (frühere Abgabefassungen)
**Zweck:** Frühere Fassungen einer Abgabe mit Rückmeldung, wenn eine Überarbeitung angefordert wurde. Die aktuelle Fassung steht in assignment_submissions.
**Eindeutig:** (submission_id, attempt).
**Indizes:** submission_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| submission_id | Ganzzahl | Pflicht | – | assignment_submissions.id, Kaskade | indiziert |
| attempt | Ganzzahl | Pflicht | – | – | Versuchsnummer (1 = erste Abgabe) |
| text_enc | Text | Pflicht | "" | – | verschl. Abgabetext; Kontext assignment_submission_versions.text:ID |
| file_ids | JSON | optional | NULL | – | Dateien der Abgabe (Dateiablage) |
| submitted_at | Zeitpunkt | optional | NULL | – | Abgabezeitpunkt |
| status | Text(20) | Pflicht | abgegeben | – | Status bei Abschluss: abgegeben / verspaetet / bewertet / zurueckgegeben |
| feedback_enc | Text | Pflicht | "" | – | verschl. Rückmeldung; Kontext assignment_submission_versions.feedback:ID |
| grade_enc | Text | Pflicht | "" | – | verschl. Bewertung; Kontext assignment_submission_versions.grade:ID |
| rubric_enc | Text | Pflicht | "" | – | verschl. ausgefülltes Raster; Kontext assignment_submission_versions.rubric:ID |
| points | Dezimalzahl | optional | NULL | – | erreichte Punkte |
| max_points | Dezimalzahl | optional | NULL | – | Höchstpunktzahl |
| feedback_file_ids | JSON | optional | NULL | – | Dateien der Rückmeldung |
| feedback_by | Ganzzahl | optional | NULL | users.id, Feld leeren | Rückmeldung von |
| feedback_at | Zeitpunkt | optional | NULL | – | Zeitpunkt der Rückmeldung |
| closed_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | Zeitpunkt, zu dem diese Fassung abgeschlossen wurde |

### 2.14 channel_group_sets (Gruppeneinteilung)
**Zweck:** Einteilung eines Kursraums (z. B. Projektgruppen, Niveaustufen). Jedes Mitglied gehört je Einteilung zu höchstens einer Gruppe.
**Eindeutig:** –.
**Indizes:** channel_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| name | Text(120) | Pflicht | – | – | Name der Einteilung |
| created_by | Ganzzahl | optional | NULL | users.id, Feld leeren | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.15 channel_groups (Gruppe)
**Zweck:** Gruppe innerhalb einer Einteilung.
**Eindeutig:** –.
**Indizes:** channel_id, set_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| set_id | Ganzzahl | Pflicht | – | channel_group_sets.id, Kaskade | indiziert |
| name | Text(120) | Pflicht | – | – | Gruppenname |
| position | Ganzzahl | Pflicht | 0 | – | Reihenfolge |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.16 channel_group_members (Gruppenmitglied)
**Zweck:** Zuordnung einer Schülerin/eines Schülers zu einer Gruppe.
**Eindeutig:** (set_id, user_id).
**Indizes:** channel_id, group_id, user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| set_id | Ganzzahl | Pflicht | – | channel_group_sets.id, Kaskade | Eindeutigkeit mit user_id |
| group_id | Ganzzahl | Pflicht | – | channel_groups.id, Kaskade | indiziert |
| user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | indiziert |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.17 channel_group_gates (Gruppen-Freigabe)
**Zweck:** Material oder Ordner ist nur für Mitglieder bestimmter Gruppen sichtbar.
**Eindeutig:** (group_id, item_id); (group_id, folder_id).
**Indizes:** channel_id, group_id, item_id, folder_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| group_id | Ganzzahl | Pflicht | – | channel_groups.id, Kaskade | indiziert |
| item_id | Ganzzahl | optional | NULL | channel_items.id, Kaskade | indiziert |
| folder_id | Ganzzahl | optional | NULL | channel_folders.id, Kaskade | indiziert |

Hinweis: Vorgesehen ist genau eines von item_id und folder_id. Das Modell erzwingt es nicht [unklar]. Ohne Eintrag ist das Material für alle sichtbar. Lehrende sehen immer alles.

### 2.18 channels (Kursraum-Kanal)
**Zweck:** Kanal eines Kursteils, einer Klasse oder frei angelegt. Behälter für Material, Aufgaben, Abgaben und Pinnwand.
**Eindeutig:** (kind, ref).
**Indizes:** kind.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| kind | Text(20) | Pflicht | – | – | course (Kursteil) / class (Klasse) / custom (frei angelegt); indiziert |
| ref | Text(100) | optional | NULL | – | course: "Kurs#Teil"; class: Klassenkennung; custom: NULL |
| title | Text(200) | Pflicht | "" | – | Titel (bei custom frei, sonst letzter bekannter Titel) |
| description | Text | Pflicht | "" | – | Beschreibung |
| settings | JSON | optional | NULL | – | students_can_post (ja), students_can_reply (ja), progress_parents (nein), period_times (Stundenzeiten, Format [unklar]); fehlende Schlüssel nehmen den Standard |
| archived | Wahrheitswert | Pflicht | nein | – | archiviert |
| created_by | Ganzzahl | optional | NULL | users.id, Feld leeren | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | |

Hinweis: Kurs- und Klassenkanäle werden bei Bedarf angelegt. Ihre Mitglieder ergeben sich aus dem Planungsdokument. Zusätzliche Mitglieder stehen in channel_extra_members.

### 2.19 channel_extra_members (zusätzliches Kanalmitglied)
**Zweck:** Zusätzliches Mitglied eines Kanals (z. B. Referendar/in). Anlegen nur mit dem Recht channels.manage ohne Einschränkung.
**Eindeutig:** (channel_id, user_id).
**Indizes:** channel_id, user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | indiziert |
| role | Text(20) | Pflicht | student | – | teacher / student |
| added_by | Ganzzahl | optional | NULL | users.id, Feld leeren | hinzugefügt von |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.20 channel_folders (Ordner im Kursraum)
**Zweck:** Verschachtelte Ordner mit eigener Freigabe und Papierkorb-Markierung.
**Eindeutig:** –.
**Indizes:** channel_id, parent_id, deleted_at, trash_group.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| parent_id | Ganzzahl | optional | NULL | channel_folders.id, Kaskade | übergeordneter Ordner; indiziert |
| name | Text(120) | Pflicht | – | – | Ordnername |
| position | Ganzzahl | Pflicht | 0 | – | Sortierung |
| hidden | Wahrheitswert | Pflicht | nein | – | ausgeblendet (wirkt wie Freigabe hidden) |
| visibility | Text(20) | optional | NULL | – | visible / hidden / scheduled / lesson; NULL = Altbestand (nur hidden-Logik) |
| visible_from | Zeitpunkt | optional | NULL | – | sichtbar ab (UTC) bei scheduled |
| lesson_date | Datum | optional | NULL | – | Unterrichtsdatum bei lesson |
| lesson_id | Text(40) | optional | NULL | – | Stunden-ID |
| lesson_period | Ganzzahl | optional | NULL | – | Stundennummer |
| created_by | Ganzzahl | optional | NULL | users.id, Feld leeren | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | |
| deleted_at | Zeitpunkt | optional | NULL | – | Papierkorb: gelöscht seit; indiziert |
| deleted_by | Ganzzahl | optional | NULL | ID-Verweis | löschendes Konto |
| trash_group | Text(36) | optional | NULL | – | gemeinsame ID aller zusammen gelöschten Elemente; indiziert |

Hinweis: Effektive Sichtbarkeit: ist hidden = ja, gilt hidden; sonst visibility, und ohne Angabe visible.

### 2.21 channel_items (Material und Aufgaben)
**Zweck:** Material (Datei, Link, Textseite) oder Aufgabe in einem Kanal.
**Eindeutig:** –.
**Indizes:** channel_id, folder_id, material_date, (channel_id, lesson_date), deleted_at, trash_group.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| folder_id | Ganzzahl | optional | NULL | channel_folders.id, Kaskade | indiziert |
| type | Text(20) | Pflicht | – | – | file / link / text / assignment |
| title | Text(200) | Pflicht | – | – | Titel |
| body_enc | Text | Pflicht | "" | – | verschl. Inhalt (Markdown); Kontext channel_items.body:ID |
| url | Text(2000) | optional | NULL | – | Linkziel (bei Typ link) |
| file_id | Text (UUID, 36) | optional | NULL | stored_files.id, Feld leeren | Datei (bei Typ file) |
| attachment_ids | JSON | optional | NULL | – | weitere Anhänge (Dateiablage-IDs) |
| visibility | Text(20) | Pflicht | visible | – | visible / hidden / scheduled / lesson |
| visible_from | Zeitpunkt | optional | NULL | – | sichtbar ab (UTC) bei scheduled |
| lesson_date | Datum | optional | NULL | – | Unterrichtsdatum bei lesson; indiziert zusammen mit channel_id |
| lesson_id | Text(40) | optional | NULL | – | Stunden-ID |
| lesson_period | Ganzzahl | optional | NULL | – | Stundennummer; Sichtbarkeit ab Stundenbeginn laut Stundenzeiten |
| due_at | Zeitpunkt | optional | NULL | – | Abgabefrist (UTC) bei Aufgaben |
| allow_late | Wahrheitswert | Pflicht | ja | – | verspätete Abgabe erlaubt |
| position | Ganzzahl | Pflicht | 0 | – | Sortierung |
| created_by | Ganzzahl | optional | NULL | users.id, Feld leeren | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | |
| lesson_material | Wahrheitswert | Pflicht | nein | – | Unterrichtsmaterial: erscheint im Bereich Unterricht am Datum der Stunde (für Nachholende) |
| material_date | Datum | optional | NULL | – | Datum im Bereich Unterricht; indiziert |
| submittable | Wahrheitswert | Pflicht | nein | – | Abgabe möglich (auch bei Material, das keine Aufgabe ist) |
| info_card | Wahrheitswert | Pflicht | nein | – | angeheftete Infokarte im Bereich Klasse (erscheint nicht unter Material) |
| deleted_at | Zeitpunkt | optional | NULL | – | Papierkorb: gelöscht seit; indiziert |
| deleted_by | Ganzzahl | optional | NULL | ID-Verweis | löschendes Konto |
| trash_group | Text(36) | optional | NULL | – | gemeinsame ID der zusammen gelöschten Elemente; indiziert |

### 2.22 assignment_submissions (aktuelle Abgabe)
**Zweck:** Aktuelle Abgabe einer Schülerin/eines Schülers zu einer Aufgabe. Bei Gruppenabgabe hat jedes Mitglied eine Zeile mit gleichem Inhalt.
**Eindeutig:** (item_id, student_user_id).
**Indizes:** item_id, student_user_id, group_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| item_id | Ganzzahl | Pflicht | – | channel_items.id, Kaskade | indiziert |
| student_user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | Konto der abgebenden Person; indiziert |
| student_id | Text(40) | optional | NULL | ID-Verweis (Planungsdokument) | Schüler/in-ID |
| text_enc | Text | Pflicht | "" | – | verschl. Abgabetext; Kontext assignment_submissions.text:ID |
| file_ids | JSON | optional | NULL | – | Dateien der Abgabe |
| submitted_at | Zeitpunkt | optional | NULL | – | Abgabezeitpunkt |
| status | Text(20) | Pflicht | abgegeben | – | abgegeben / verspaetet / bewertet / zurueckgegeben |
| feedback_enc | Text | Pflicht | "" | – | verschl. Rückmeldung; Kontext assignment_submissions.feedback:ID |
| grade_enc | Text | Pflicht | "" | – | verschl. Bewertung; Kontext assignment_submissions.grade:ID |
| feedback_file_ids | JSON | optional | NULL | – | Dateien der Rückmeldung |
| feedback_by | Ganzzahl | optional | NULL | users.id, Feld leeren | Rückmeldung von |
| feedback_at | Zeitpunkt | optional | NULL | – | Zeitpunkt der Rückmeldung |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | optional | NULL | – | |
| attempt | Ganzzahl | Pflicht | 1 | – | Versuch: 1 = erste Abgabe; Überarbeitung legt eine neue Fassung an |
| group_id | Ganzzahl | optional | NULL | ID-Verweis | Gruppe bei Gruppenabgabe; indiziert |
| points | Dezimalzahl | optional | NULL | – | erreichte Punkte |
| max_points | Dezimalzahl | optional | NULL | – | Höchstpunktzahl |
| rubric_enc | Text | Pflicht | "" | – | verschl. ausgefülltes Raster; Kontext assignment_submissions.rubric:ID |
| individual | Wahrheitswert | Pflicht | nein | – | Einzelanpassung einer Gruppenbewertung |
| revision_due_at | Zeitpunkt | optional | NULL | – | Frist der Überarbeitung (UTC) |

### 2.23 channel_posts (Pinnwand)
**Zweck:** Pinnwandbeitrag oder Antwort im Kanal.
**Eindeutig:** –.
**Indizes:** channel_id, parent_id, author_id, created_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | indiziert |
| parent_id | Ganzzahl | optional | NULL | channel_posts.id, Kaskade | Antwort auf diesen Beitrag; indiziert; nur eine Ebene |
| author_id | Ganzzahl | optional | NULL | users.id, Feld leeren | Verfasser; indiziert |
| author_name | Text(200) | Pflicht | "" | – | Name des Verfassers (Klartext) |
| body_enc | Text | Pflicht | "" | – | verschl. Text; Kontext channel_posts.body:ID |
| attachment_ids | JSON | optional | NULL | – | Anhänge (Dateiablage-IDs) |
| pinned | Wahrheitswert | Pflicht | nein | – | angeheftet |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | indiziert |
| edited_at | Zeitpunkt | optional | NULL | – | zuletzt bearbeitet |
| deleted_at | Zeitpunkt | optional | NULL | – | weiches Löschen: gelöscht seit |

### 2.24 channel_reads (letzter Besuch)
**Zweck:** Letzter Besuch eines Kontos in einem Kanal (Markierung "neu").
**Eindeutig:** (channel_id, user_id).
**Indizes:** user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| channel_id | Ganzzahl | Pflicht | – | channels.id, Kaskade | |
| user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | indiziert |
| last_seen_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | letzter Besuch |

### 2.25 channel_item_views (Materialansicht)
**Zweck:** Material, das ein Konto bereits geöffnet hat (Hinweis auf noch nicht angesehenes Material).
**Eindeutig:** (item_id, user_id).
**Indizes:** user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| item_id | Ganzzahl | Pflicht | – | channel_items.id, Kaskade | |
| user_id | Ganzzahl | Pflicht | – | users.id, Kaskade | indiziert |
| viewed_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | Zeitpunkt der Ansicht |

### 2.26 chat_devices (Gerät eines Chat-Kontos)
**Zweck:** Gerät eines Kontos bzw. Wiederherstellungsschlüssel mit öffentlichem Schlüssel für die Ende-zu-Ende-Verschlüsselung der Chats.
**Eindeutig:** –.
**Indizes:** user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| user_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| public_key | Text(64) | Pflicht | – | – | öffentlicher Schlüssel X25519, Base64; kein Geheimnis |
| label | Text(120) | Pflicht | "" | – | Gerätebezeichnung |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| last_seen_at | Zeitpunkt | optional | NULL | – | zuletzt gesehen |
| revoked_at | Zeitpunkt | optional | NULL | – | widerrufen (Zeitpunkt) |
| kind | Text(10) | Pflicht | device | – | device / archive (archive = Wiederherstellungsschlüssel des Kontos) |
| acked_at | Zeitpunkt | optional | NULL | – | von einem anderen eigenen Gerät bestätigt; NULL = unbekannt, dann Hinweis an die anderen Geräte |

### 2.27 chat_link_requests (Geräteverknüpfung)
**Zweck:** Anfrage eines neuen Geräts, den Chatverlauf von einem eingerichteten Gerät desselben Kontos zu erhalten.
**Eindeutig:** –.
**Indizes:** user_id, device_id, code.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| user_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| device_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | anfragendes Gerät; indiziert |
| code | Text(12) | Pflicht | – | – | Auffindecode; kurzlebig; indiziert |
| status | Text(10) | Pflicht | pending | – | pending / approved / cancelled |
| approved_by_device_id | Ganzzahl | optional | NULL | ID-Verweis | freigebendes Gerät |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| expires_at | Zeitpunkt | Pflicht | – | – | Ablauf; Dauer [unklar] |
| approved_at | Zeitpunkt | optional | NULL | – | Freigabezeitpunkt |

Hinweis: Die Freigabe erfolgt erst nach Vergleich des Fingerabdrucks beider Geräte.

### 2.28 chat_key_backups (Schlüssel-Backup)
**Zweck:** Optionales Wiederherstellungs-Backup des privaten Archivschlüssels des Kontos, im Browser verschlüsselt.
**Schlüssel:** user_id.
**Indizes:** –.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| user_id | Ganzzahl (Primärschlüssel) | Pflicht | – | ID-Verweis, kein Fremdschlüssel | |
| archive_device_id | Ganzzahl | Pflicht | – | ID-Verweis (chat_devices) | Archivgerät |
| blob | Text | Pflicht | "" | – | undurchsichtiges Chiffrat; Schlüssel wird aus Passwort bzw. Code im Browser abgeleitet |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | von der Anwendung bei Änderung gesetzt |

### 2.29 chats (Chat)
**Zweck:** Einzel-, Gruppen- oder Klassenchat.
**Eindeutig:** direct_key.
**Indizes:** last_activity_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| kind | Text(10) | Pflicht | group | – | direct / group |
| title_enc | Text | Pflicht | "" | – | verschl. Chatname (Server-seitig); Kontext chats.title:ID |
| direct_key | Text(40) | optional | NULL | – | eindeutig; Schlüssel eines Einzelchats zwischen zwei Konten (Format [unklar]) |
| only_admins_post | Wahrheitswert | Pflicht | nein | – | abgeleitet: ja, wenn post_mode = admins |
| post_mode | Text(10) | Pflicht | all | – | all / admins / selected |
| postfach_import | Wahrheitswert | Pflicht | nein | – | aus dem früheren Postfach übernommen |
| created_by | Ganzzahl | optional | NULL | ID-Verweis | Ersteller |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| last_activity_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | letzte Aktivität (Sortierung); indiziert |

### 2.30 chat_members (Chat-Mitglied)
**Zweck:** Mitgliedschaft in einem Chat mit persönlichem Lese-, Stummschalt-, Archiv- und Schreibstatus.
**Eindeutig:** (chat_id, user_id).
**Indizes:** chat_id, user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| chat_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| user_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| admin | Wahrheitswert | Pflicht | nein | – | Chat-Admin |
| joined_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | Beitrittszeitpunkt |
| first_message_id | Ganzzahl | Pflicht | 0 | – | ab dieser Nachricht sichtbar; ältere bleiben verborgen; Bedeutung von 0 [unklar] |
| last_read_id | Ganzzahl | Pflicht | 0 | – | zuletzt gelesene Nachricht (ID) |
| muted | Wahrheitswert | Pflicht | nein | – | stummgeschaltet |
| archived | Wahrheitswert | Pflicht | nein | – | archiviert; kommt bei neuer Nachricht zurück, außer bei Stummschaltung |
| can_post | Wahrheitswert | Pflicht | ja | – | Schreibrecht; wirkt nur bei post_mode = selected |

### 2.31 chat_messages (Chat-Nachricht)
**Zweck:** Verschlüsselte Chat-Nachricht. Der Server speichert nur das Chiffrat.
**Eindeutig:** legacy_source_message_id.
**Indizes:** chat_id, legacy_source_message_id, legacy_source_conversation_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| chat_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| sender_id | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | Absender |
| sender_device_id | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | Absendergerät |
| nonce | Text(40) | Pflicht | "" | – | Nonce des Chiffrats |
| ciphertext | Text | Pflicht | "" | – | Ende-zu-Ende-Chiffrat (XSalsa20-Poly1305, Zufallsschlüssel je Nachricht) |
| reply_to | Ganzzahl | optional | NULL | ID-Verweis | Antwort auf diese Nachricht (ID) |
| system_text | Text(400) | Pflicht | "" | – | Systemhinweis im Klartext (kein Nutzerinhalt, z. B. "X hat Y hinzugefügt") |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| deleted_at | Zeitpunkt | optional | NULL | – | gelöscht seit; Verbleib des Chiffrats [unklar] |
| legacy_body_enc | Text | Pflicht | "" | – | Altbestand: verschl. Originaltext aus dem früheren Postfach; Kontext messages.body:alte Unterhaltung:alte Nachricht |
| legacy_source_message_id | Ganzzahl | optional | NULL | – | ID der Originalnachricht im früheren Postfach; eindeutig; indiziert |
| legacy_source_conversation_id | Ganzzahl | optional | NULL | – | ID der alten Unterhaltung; indiziert; bei der Markierungsnachricht nur dieses Feld gesetzt |

### 2.32 chat_message_keys (Nachrichtenschlüssel je Gerät)
**Zweck:** Nachrichtenschlüssel, verpackt für ein Gerät des Empfängers.
**Eindeutig:** (message_id, device_id).
**Indizes:** message_id, device_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| message_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| device_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| nonce | Text(40) | Pflicht | – | – | Nonce der Verpackung |
| wrapped | Text(120) | Pflicht | – | – | verpackter Nachrichtenschlüssel (X25519 + XSalsa20-Poly1305; vom Absendergerät authentisiert) |
| wrapper_device_id | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | Gerät, das nachträglich verpackt hat; NULL = Absendergerät |

### 2.33 chat_reports (Meldung)
**Zweck:** Meldung einer Chat-Nachricht durch ein Mitglied. Der Melder kann Klartext und Bild freiwillig mitschicken.
**Eindeutig:** –.
**Indizes:** chat_id, message_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| chat_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| message_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| reporter_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | meldende Person |
| sender_id | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | gemeldete Absenderin bzw. gemeldeter Absender |
| reason_enc | Text | Pflicht | "" | – | verschl. Meldegrund; Kontext chat_reports.reason:ID |
| content_enc | Text | Pflicht | "" | – | verschl. freiwillig mitgeschickter Nachrichtentext; Kontext chat_reports.content:ID |
| status | Text(20) | Pflicht | open | – | open / dismissed / removed |
| resolved_by | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | bearbeitende Person |
| resolved_at | Zeitpunkt | optional | NULL | – | Bearbeitungszeitpunkt |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.34 chat_attachments (Chat-Bild)
**Zweck:** Bild oder GIF einer Chat-Nachricht als im Browser verschlüsseltes Blob.
**Schlüssel:** id (Text, 32 Zeichen).
**Indizes:** chat_id, uploader_id, message_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Text(32) (Primärschlüssel) | Pflicht | – | – | Kennung |
| chat_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| uploader_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | hochladende Person; indiziert |
| message_id | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | leer, bis die Nachricht gesendet ist; lose Uploads verfallen nach 24 Stunden; indiziert |
| size | Ganzzahl | Pflicht | 0 | – | Größe des Blobs in Bytes |
| data | Binär | Pflicht | – | – | verschlüsseltes Blob; Server sieht weder Inhalt noch Dateityp; Schlüssel steckt in der verschlüsselten Nachricht |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.35 chat_report_images (Bild zur Meldung)
**Zweck:** Bild, das die meldende Person für die Moderation mitschickt.
**Eindeutig:** –.
**Indizes:** report_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| report_id | Ganzzahl | Pflicht | – | ID-Verweis, kein Fremdschlüssel | indiziert |
| mime | Text(40) | Pflicht | "" | – | Bildtyp (MIME) |
| data_enc | Binär | Pflicht | – | – | verschl. Bilddaten; Kontext chat_report_images.data:ID |

### 2.36 comp_frameworks (Kompetenzrahmen)
**Zweck:** Kompetenzrahmen mit Bereichen, Kompetenzen und Niveaustufen. Schulweite Lehrplan-Inhalte, keine Personendaten.
**Eindeutig:** –.
**Indizes:** –.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| name | Text(200) | Pflicht | – | – | Name des Rahmens |
| subject | Text(40) | Pflicht | "" | – | Fach |
| description | Text(500) | Pflicht | "" | – | Beschreibung |
| levels | JSON (Liste) | Pflicht | [] | – | Bezeichnungen der Stufen 1 bis n |
| support_level | Ganzzahl | Pflicht | 1 | – | bis einschließlich dieser Stufe gilt "braucht Unterstützung" |
| archived | Wahrheitswert | Pflicht | nein | – | archiviert |
| created_by | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | Ersteller |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | von der Anwendung bei Änderung gesetzt |

### 2.37 comp_areas (Bereich eines Rahmens)
**Zweck:** Bereich innerhalb eines Kompetenzrahmens.
**Eindeutig:** –.
**Indizes:** framework_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| framework_id | Ganzzahl | Pflicht | – | comp_frameworks.id, Kaskade | indiziert |
| name | Text(200) | Pflicht | – | – | Bereichsname |
| position | Ganzzahl | Pflicht | 0 | – | Sortierung |

### 2.38 comp_competencies (Kompetenz)
**Zweck:** Einzelne Kompetenz ("Ich kann …") in einem Bereich.
**Eindeutig:** –.
**Indizes:** framework_id, area_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| framework_id | Ganzzahl | Pflicht | – | comp_frameworks.id, Kaskade | indiziert |
| area_id | Ganzzahl | Pflicht | – | comp_areas.id, Kaskade | indiziert |
| code | Text(20) | Pflicht | "" | – | Kurzkennung |
| title | Text(300) | Pflicht | – | – | Formulierung "Ich kann …" |
| descriptors | JSON (Liste) | Pflicht | [] | – | optionale Beschreibung je Stufe |
| position | Ganzzahl | Pflicht | 0 | – | Sortierung |

### 2.39 comp_assessments (Lernstand)
**Zweck:** Lernstand einer Schülerin/eines Schülers zu einer Kompetenz. Nur anhängend: der Verlauf bleibt erhalten.
**Eindeutig:** –.
**Indizes:** student_id, competency_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| student_id | Text(40) | Pflicht | – | ID-Verweis (Planungsdokument) | indiziert |
| competency_id | Ganzzahl | Pflicht | – | comp_competencies.id, Kaskade | indiziert |
| kind | Text(10) | Pflicht | teacher | – | teacher (Lehrkraft) / self (Selbsteinschätzung) |
| level | Ganzzahl | Pflicht | – | – | erreichte Stufe (1 bis n) |
| assessed_on | Datum | Pflicht | – | – | Datum der Einschätzung |
| evidence_type | Text(20) | Pflicht | "" | – | leer / note / link / assignment / material |
| evidence_ref | Text(100) | Pflicht | "" | – | Verweis auf den Nachweis im Format Typ:ID (z. B. channel:12) |
| evidence_enc | Text | Pflicht | "" | – | verschl. Nachweis; Kontext comp_assessments.Feld:ID |
| comment_enc | Text | Pflicht | "" | – | verschl. Kommentar; Kontext comp_assessments.Feld:ID |
| by_user_id | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | einschätzende Person |
| by_name | Text(200) | Pflicht | "" | – | Name der einschätzenden Person |
| confirmed_at | Zeitpunkt | optional | NULL | – | nur bei Selbsteinschätzung: bestätigt am |
| confirmed_by | Text(200) | Pflicht | "" | – | bestätigt von (Name) |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.40 comp_links (Verknüpfung Kompetenz und Objekt)
**Zweck:** Zuordnung eines Objekts (z. B. Aufgabe oder Material) zu einer Kompetenz.
**Eindeutig:** (competency_id, item_type, item_id).
**Indizes:** competency_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| competency_id | Ganzzahl | Pflicht | – | comp_competencies.id, Kaskade | indiziert |
| item_type | Text(30) | Pflicht | – | – | Objekttyp (Werte [unklar]) |
| item_id | Text(60) | Pflicht | – | – | ID des Objekts (als Text) |
| created_by | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.41 comp_plans (Lern- bzw. Wochenplan)
**Zweck:** Lern- oder Wochenplan je Schüler/in.
**Eindeutig:** –.
**Indizes:** student_id, competency_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| student_id | Text(40) | Pflicht | – | ID-Verweis (Planungsdokument) | indiziert |
| competency_id | Ganzzahl | optional | NULL | comp_competencies.id, Feld leeren | verknüpfte Kompetenz; indiziert |
| title_enc | Text | Pflicht | "" | – | verschl. Titel; Kontext comp_plans.Feld:ID |
| note_enc | Text | Pflicht | "" | – | verschl. Notiz; Kontext comp_plans.Feld:ID |
| week_start | Datum | optional | NULL | – | Montag der Woche |
| due_date | Datum | optional | NULL | – | Fälligkeit |
| status | Text(12) | Pflicht | offen | – | offen / in_arbeit / erledigt |
| source | Text(10) | Pflicht | lehrkraft | – | lehrkraft / schueler (Herkunft des Plans) |
| item_type | Text(30) | Pflicht | "" | – | Verweistyp (Werte [unklar]) |
| item_id | Text(60) | Pflicht | "" | – | Verweis-ID |
| created_by | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |
| updated_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | von der Anwendung bei Änderung gesetzt |
| done_at | Zeitpunkt | optional | NULL | – | erledigt am |

### 2.42 comp_badges (Abzeichen)
**Zweck:** Definition eines Abzeichens (Name, Symbol, Farbe, Vergaberegel).
**Eindeutig:** –.
**Indizes:** –.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| name | Text(100) | Pflicht | – | – | Name |
| description | Text(300) | Pflicht | "" | – | Beschreibung |
| icon | Text(30) | Pflicht | star | – | Symbolname |
| color | Text(20) | Pflicht | gold | – | Farbname |
| criteria | JSON | optional | NULL | – | Vergaberegel; NULL = nur manuell vergeben |
| active | Wahrheitswert | Pflicht | ja | – | aktiv |
| created_by | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | |
| created_at | Zeitpunkt | Pflicht | jetzt (UTC) | – | |

### 2.43 comp_badge_awards (Abzeichen-Vergabe)
**Zweck:** Vergabe eines Abzeichens an eine Schülerin/einen Schüler.
**Eindeutig:** (badge_id, student_id).
**Indizes:** badge_id, student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel | Hinweis |
|---|---|---|---|---|---|
| id | Ganzzahl (Primärschlüssel) | Pflicht | automatisch | – | |
| badge_id | Ganzzahl | Pflicht | – | comp_badges.id, Kaskade | indiziert |
| student_id | Text(40) | Pflicht | – | ID-Verweis (Planungsdokument) | indiziert |
| awarded_on | Datum | Pflicht | – | – | Vergabedatum |
| awarded_by | Ganzzahl | optional | NULL | ID-Verweis, kein Fremdschlüssel | vergebende Person |
| awarded_by_name | Text(200) | Pflicht | "" | – | Name der vergebenden Person |
| auto | Wahrheitswert | Pflicht | nein | – | automatisch nach Regel vergeben (nein = manuell) |
| note_enc | Text | Pflicht | "" | – | verschl. Notiz; Kontext comp_badge_awards.Feld:ID |

---

## 3. Wertelisten (Statuswerte, Auswahlwerte)

| Tabelle.Spalte | Erlaubte Werte | Standard | Bedeutung / Wirkung |
|---|---|---|---|
| users.role | admin, schulleitung, abteilungsleitung, planer, sekretariat, lehrer, hausmeister, schulbegleitung, schueler, eltern, monitor, zuschauer | – | Grundrolle eines Kontos (zwölf Rollen) |
| users.custom_role | ID einer eigenen Schulrolle | NULL | Die Grundrolle steht weiterhin in users.role |
| student_absences.status | gemeldet, teilweise, entschuldigt, unentschuldigt | gemeldet | teilweise = telefonisch gemeldet, schriftliche Entschuldigung fehlt |
| student_absences.kind | krank, verspaetung, frueh, fehlt | krank | Art der Fehlzeit |
| student_absences.source | online, telefon, schriftlich, lehrkraft | online | Herkunft der Meldung |
| student_absence_events.event | angelegt, zusammengefuehrt, aenderung, zurueckgenommen, dokument_eingereicht, dokument_geprueft, dokument_abgelehnt, dokument_zurueckgezogen, verkuerzt, verlaengert, verlaengerung_beantragt, ruecknahme_angefragt, beurlaubung_zurueckgegeben | – | Art des Protokolleintrags (13 Werte) |
| student_absence_events.channel | online, telefon, schriftlich, formular, klassenbuch, lehrkraft, import, system | leer | Kanal der Änderung |
| announcements.audience | all, staff, classes | all | Zielgruppe |
| announcements.priority | normal, wichtig | normal | Priorität |
| notifications_outbox.kind | webhook, email | – | Art der Benachrichtigung |
| notifications_outbox.status | pending, sending, sent, failed | pending | Versandstatus |
| api_token_log.outcome | ok, error, ip_denied, rate_limited, blocked; weitere [unklar] | ok | Ergebnis der Anfrage |
| api_token_log.method | HTTP-Methode | GET | Methode der Anfrage |
| api_tokens.prefix | sma_ (Zugang mit Umfang), smt_ (persönliches Token) | leer | Präfix des Tokens |
| api_tokens.scope | NULL (persönliches Token), sonst Bereiche und Filter | NULL | Umfang des Zugangs |
| role_overrides.scope | NULL (Standardumfang), all (uneingeschränkt), z. B. own_classes; weitere [unklar] | NULL | Umfang einer Rechteabweichung |
| channels.kind | course, class, custom | – | Kanalart |
| channels.ref | course: "Kurs#Teil"; class: Klassenkennung; custom: NULL | NULL | Bezug des Kanals |
| channel_items.type | file, link, text, assignment | – | Materialart |
| channel_items.visibility | visible, hidden, scheduled, lesson | visible | Sichtbarkeit des Materials |
| channel_folders.visibility | visible, hidden, scheduled, lesson; NULL = Altbestand | NULL | Sichtbarkeit des Ordners |
| assignment_submissions.status | abgegeben, verspaetet, bewertet, zurueckgegeben | abgegeben | Status der Abgabe |
| assignment_submission_versions.status | abgegeben, verspaetet, bewertet, zurueckgegeben | abgegeben | Status der Fassung bei Abschluss |
| channel_extra_members.role | teacher, student | student | Rolle im Kanal |
| channels.settings (Schlüssel) | students_can_post = ja; students_can_reply = ja; progress_parents = nein | siehe links | Kanaleinstellungen |
| assignment_settings.rubric_kind | rubric (Raster), guide (Leitfaden) | NULL | Art der Bewertung |
| grading_templates.kind | rubric (Raster), guide (Leitfaden) | – | Art der Bewertungsvorlage |
| chats.kind | direct, group | group | Chatart |
| chats.post_mode | all (alle Mitglieder), admins (nur Admins), selected (Admins und Mitglieder mit can_post) | all | Wer schreiben darf |
| chat_devices.kind | device, archive | device | Gerät oder Wiederherstellungsschlüssel |
| chat_link_requests.status | pending, approved, cancelled | pending | Status der Geräteverknüpfung |
| chat_reports.status | open, dismissed, removed | open | Status der Meldung |
| stored_files.scan_status | clean, unscanned, error | unscanned | Ergebnis der Dateiprüfung |
| stored_files.kind | pdf, png, docx u. a.; vollständige Liste [unklar] | – | Dateiart |
| auth_codes.purpose | verify_email, verify_phone, reset, reset_token, rl_reset, rl_fail | – | Zweck des Codes bzw. Zählers |
| auth_codes.channel | email, sms | – | Versandweg |
| form_templates.status | entwurf, aktiv, archiviert | entwurf | Status der Vorlage |
| form_templates.category | sonstiges (Standard); weitere [unklar] | sonstiges | Kategorie |
| form_submissions.status | eingereicht (Standard); geprueft, genehmigt, abgelehnt laut Dokumentation; vollständige Liste [unklar] | eingereicht | Status der Einreichung |
| form_events.action | Dokumentation: eingereicht, geprueft, genehmigt, abgelehnt, Scan, Erinnerung; vollständig [unklar] | – | Aktion im Verlauf |
| comp_assessments.kind | teacher (Lehrkraft), self (Selbsteinschätzung) | teacher | Herkunft der Einschätzung |
| comp_assessments.evidence_type | leer, note, link, assignment, material | leer | Art des Nachweises |
| comp_plans.status | offen, in_arbeit, erledigt | offen | Status des Plans |
| comp_plans.source | lehrkraft, schueler | lehrkraft | Herkunft des Plans |
| comp_links.item_type, comp_plans.item_type | Objekttypen; vollständig [unklar] | – | Typ des verknüpften Objekts |
| comp_badges.icon, comp_badges.color | Symbolname, Farbname | star, gold | Darstellung |
| chat_members.first_message_id | ID einer Nachricht | 0 | erste sichtbare Nachricht; Bedeutung von 0 [unklar] |

---

## 4. Regeln, Fristen und Grenzen

| Regel / Grenze | Wert | Einheit | Wirkung (wo) |
|---|---|---|---|
| Gültigkeit Einmal-Code | 15 | Minuten | Bestätigung und Passwort-Zurücksetzen; Standard, per Umgebungsvariable SM_AUTH_CODE_MINUTES änderbar (auth_codes.expires_at) |
| Fehlversuche je Einmal-Code | 5 | Versuche (max.) | Eingabe des Codes (auth_codes.attempts) |
| Gültigkeit Reset-Token | [unklar] | – | Zurücksetzen nach erfolgreicher Prüfung (purpose reset_token) |
| Rate-Limit Zurücksetzen | Zähler je Anfrage (rl_reset) und je Fehlversuch (rl_fail); je Kennung (ident_hash), auch für unbekannte Kennungen; je IP | Schwellen [unklar] | Anfrage Passwort-Zurücksetzen (auth_codes) |
| Anmeldeprotokoll | je Benutzername und je IP auswertbar | Schwelle [unklar] | Sperre bei Anmeldung (login_attempts) |
| Sitzungscookie | Name sm_session; nur Hash des Tokens gespeichert | Dauer [unklar] | Anmeldung (sessions.expires_at, sessions.token_hash) |
| Rate-Limit API-Token | Anfragen pro Minute; NULL = [unklar] | Anfragen/Minute | API-Zugang (api_tokens.rate_limit) |
| Ablauf API-Token | NULL = [unklar], ob unbefristet | – | API-Zugang (api_tokens.expires_at) |
| Aufbewahrung API-Protokoll | 90 | Tage | Datenart api_log im Löschkonzept (Standard; api_token_log.at) |
| Obergrenze API-Protokoll je Zugang | [Wert unklar] | Zeilen | zusätzlich zur Aufbewahrung (api_token_log) |
| E-Mail gilt als bestätigt | nur wenn Kleinschreibung von users.email gleich email_verified_value | – | Kontaktbestätigung (user_contacts); Änderung der E-Mail macht unbestätigt |
| Format Handynummer | E.164 | – | Speicherung verschlüsselt (user_contacts.phone_enc) |
| Lose Chat-Anhänge | 24 | Stunden | verfallen, wenn nicht gesendet (chat_attachments.message_id) |
| Geräteverknüpfung Gültigkeit | [unklar] | – | Auffindecode, Freigabe nach Fingerabdruck-Vergleich (chat_link_requests.expires_at) |
| Verlauf für neue Chatmitglieder | nicht älter als first_message_id | Nachrichten-ID | Sichtbarkeit älterer Nachrichten (chat_members.first_message_id) |
| Chat-Archiv | kommt bei neuer Nachricht zurück, außer bei Stummschaltung | – | Chat-Liste (chat_members.archived, muted) |
| Schreibrecht im Chat | nur bei post_mode = selected zählt can_post | – | Schreibrecht (chat_members.can_post) |
| Gerät unbestätigt | acked_at = NULL | – | Hinweis an die anderen Geräte des Kontos (chat_devices.acked_at) |
| Meldungsprotokoll Fehlzeiten | unveränderlich, nur anhängen; bei Kontolöschung nur Konto-Verweis und Name pseudonymisiert | – | Protokoll (student_absence_events) |
| Verspätung / frühes Gehen | Minuten | Minuten | Fehlzeit mit kind verspaetung oder frueh (student_absences.minutes) |
| Stunden der Fehlzeit | Liste der Stundennummern | Stunden | Umfang der Fehlzeit (student_absences.periods) |
| Status teilweise | telefonisch gemeldet, schriftliche Entschuldigung fehlt | – | Fehlzeit (student_absences.status) |
| Volljährige Schüler/innen | adult = ja: Krankmeldung selbst möglich | – | Berechtigung (users.adult) |
| Benachrichtigung: Versuche | attempts zählt; nächster Versuch in next_attempt_at; maximale Versuche und Abstand [unklar] | Versuche / [unklar] | Versand (notifications_outbox) |
| Papierkorb Kursraum | Löschen setzt deleted_at; gelöschte Elemente unsichtbar für normale Abfragen; Frist bis endgültigem Löschen [unklar] | – | Material und Ordner (channel_items, channel_folders) |
| Abgabeversuch | 1 = erste Abgabe; Überarbeitung legt neue Fassung an | Versuch | Abgabe (assignment_submissions.attempt; assignment_submission_versions) |
| Frist der Überarbeitung | revision_due_at (UTC) | Zeitpunkt | Überarbeitung (assignment_submissions.revision_due_at) |
| Verspätete Abgabe | erlaubt, Standard ja | – | Aufgabe (channel_items.allow_late) |
| Fristverlängerung | due_at je Schüler/in oder Gruppe | Zeitpunkt | Aufgabe (assignment_extensions) |
| Gruppe je Einteilung | jedes Mitglied höchstens eine Gruppe | – | Gruppenbildung (channel_group_members, eindeutig) |
| Gruppen-Freigabe | ohne Eintrag für alle; Lehrende sehen immer alles | – | Material und Ordner (channel_group_gates) |
| Kanal-Standards | students_can_post ja, students_can_reply ja, progress_parents nein | – | Kanal (channels.settings; gelten, wenn Schlüssel fehlt) |
| Pinnwand-Antworten | nur eine Ebene | Ebene | Beiträge (channel_posts.parent_id) |
| Sichtbarkeit zur Stunde | ab Stundenbeginn laut Stundenzeiten | – | Material (channel_items.lesson_*; settings.period_times) |
| Ordner-Freigabe | hidden hat Vorrang; visibility NULL = Altbestand | – | Ordner (channel_folders) |
| Kompetenzstufe "braucht Unterstützung" | bis einschließlich Stufe support_level (Standard 1) | Stufe | Rahmen (comp_frameworks.support_level) |
| Lernstand | nur anhängen; Verlauf bleibt | – | Einschätzung (comp_assessments) |
| Bestätigung Selbsteinschätzung | confirmed_at nur bei kind = self | – | Einschätzung (comp_assessments.confirmed_at) |
| Abzeichen-Vergabe | je Schüler/in einmal je Abzeichen; criteria NULL = nur manuell | – | Vergabe (comp_badge_awards, comp_badges.criteria) |
| Wochenplan-Woche | week_start = Montag der Woche | Datum | Plan (comp_plans.week_start) |
| Schulversion wiederherstellen | über restored_from auf die Quellversion | ID | Versionen (school_versions) |
| Altbestand Schulversionen | ohne Verschlüsselung; wird beim Start und durch Schlüsselrotation (CLI rotate-keys) umgeschlüsselt | – | school_versions.data |
| Rechteabweichung | granted ja/nein; scope NULL = Standardumfang, all = uneingeschränkt; feste Mindestregeln zusätzlich [unklar] | – | Rollenrechte (role_overrides) |
| Gültigkeit Ankündigung | valid_from bis valid_to, Datum YYYY-MM-DD | Datum | Ankündigung (announcements) |
| Dateiprüfung | scan_status unscanned, dann clean oder error | – | Dateiablage (stored_files.scan_status) |
| Dateiname | verschlüsselt gespeichert, Klartext nur nach Entschlüsselung | – | Dateiablage (stored_files.filename) |
| Speicherort Datei | SM_DATA_DIR/files/ (Standard) | Pfad | Inhalt der Dateiablage (stored_files; Aufbau Unterordner [unklar]) |
| Meldung im Chat | Melder kann Klartext und Bild freiwillig mitschicken | – | Moderation (chat_reports.content_enc, chat_report_images) |
| Standard Krankmeldung | Status gemeldet, Art krank, Quelle online | – | Fehlzeit (student_absences) |
| Eltern-Verknüpfung | je Paar Elternkonto und Kind einmal | – | Verknüpfung (parent_links, eindeutig) |

---

## 5. Verschlüsselung und Hash: Übersicht

Legende: verschl. = serverseitig verschlüsselt (Token-Format SM1, Kontext-Bindung `Tabelle.Feld:ID`). E2E = Ende-zu-Ende im Browser; der Server kennt den Inhalt nicht. Hash = nur Hash bzw. HMAC gespeichert.

| Tabelle.Spalte | Schutz | Kontext / Bindung | Hinweis |
|---|---|---|---|
| users.password_hash | Hash | – | Verfahren [unklar] |
| users.totp_secret | Klartext (veraltet) | – | Altbestand; nach Umstellung leer |
| users.totp_secret_enc | verschl. | users.totp_secret:ID | TOTP-Geheimnis |
| users.ical_token | Hash (HMAC) | – | nur Hash gespeichert |
| sessions.token_hash | Hash | – | Verfahren [unklar] |
| api_tokens.token_hash | Hash | – | Verfahren [unklar]; Klartext nicht gespeichert |
| school_versions.data | verschl. (nach Komprimierung) | school_versions.data:ID | Altbestand ohne Verschlüsselung |
| student_absences.reason | Klartext | – | Gesundheitsdaten, siehe Abschnitt 6 |
| student_absences.note | Klartext | – | Vermerk, siehe Abschnitt 6 |
| student_absence_events.detail | Klartext | – | ohne Gründe, Vermerke, Diagnosen |
| user_contacts.phone_enc | verschl. | user_contacts.phone:user_id | Handynummer, E.164 |
| user_contacts.phone_hash | Hash (HMAC mit SM_SECRET_KEY) | – | nur zur Suche |
| auth_codes.code_hash | Hash (HMAC) | – | Einmal-Code |
| auth_codes.token_hash | Hash (HMAC) | – | Link- bzw. Reset-Token |
| auth_codes.target_enc | verschl. | auth_codes.target:ID | neues Ziel (E-Mail bzw. Nummer) |
| auth_codes.ident_hash | Hash (HMAC) | – | Kennung, auch unbekannte |
| stored_files.filename | verschl. | stored_files.filename:ID | Klartext nur nach Entschlüsselung |
| stored_files.sha256 | Prüfsumme (SHA-256) | – | Integritätsprüfung, kein Schutz des Inhalts |
| stored_files (Inhalt) | verschl. | Schlüssel über key_id | Inhalt im Dateispeicher |
| form_submissions.answers_enc | verschl. | form_submissions.answers:ID | Antworten |
| form_submissions.decision_note_enc | verschl. | [unklar] | Entscheidungsvermerk |
| form_events.note_enc | verschl. | [unklar] | Notiz im Verlauf |
| grading_templates.criteria_enc | verschl. | grading_templates.criteria:ID | Kriterien als JSON |
| assignment_settings.rubric_enc | verschl. | assignment_settings.rubric:ID | Raster als JSON |
| assignment_extensions.reason_enc | verschl. | assignment_extensions.reason:ID | Begründung |
| assignment_submissions.text_enc / feedback_enc / grade_enc / rubric_enc | verschl. | assignment_submissions.text / feedback / grade / rubric:ID | Abgabe |
| assignment_submission_versions.text_enc / feedback_enc / grade_enc / rubric_enc | verschl. | assignment_submission_versions.text / feedback / grade / rubric:ID | frühere Fassungen |
| channel_items.body_enc | verschl. (Markdown) | channel_items.body:ID | Textseite bzw. Aufgabentext |
| channel_posts.body_enc | verschl. | channel_posts.body:ID | Pinnwandtext |
| notifications_outbox.payload | E-Mail: verschl.; Webhook: Klartext-JSON | [unklar] | Versandinhalt |
| comp_assessments.evidence_enc / comment_enc | verschl. | comp_assessments.Feld:ID | Nachweis, Kommentar |
| comp_plans.title_enc / note_enc | verschl. | comp_plans.Feld:ID | Titel, Notiz |
| comp_badge_awards.note_enc | verschl. | comp_badge_awards.Feld:ID | Notiz |
| chats.title_enc | verschl. (Server) | chats.title:ID | Chatname, damit neue Geräte ihn anzeigen |
| chat_messages.ciphertext | E2E | – | Nachrichtentext; Schlüssel je Gerät |
| chat_messages.legacy_body_enc | verschl. (Server) | messages.body:alte Unterhaltung:alte Nachricht | Altbestand aus dem früheren Postfach |
| chat_message_keys.wrapped | E2E | – | Nachrichtenschlüssel je Empfängergerät |
| chat_devices.public_key | öffentlich | – | kein Geheimnis |
| chat_key_backups.blob | E2E (aus Passwort bzw. Code abgeleitet) | – | Archivschlüssel-Backup |
| chat_attachments.data | E2E | – | Bild/GIF; Server kennt Inhalt und Typ nicht |
| chat_reports.reason_enc / content_enc | verschl. (Server) | chat_reports.reason / content:ID | Meldung |
| chat_report_images.data_enc | verschl. (Server) | chat_report_images.data:ID | Bild zur Meldung |

---

## 6. Offene Punkte und Auffälligkeiten

**Entscheidungen für den Neubau:**
1. Gesundheitsdaten im Klartext: student_absences.reason und student_absences.note sind nicht verschlüsselt. Das Meldungsprotokoll schließt Gründe, Vermerke und Diagnosen dagegen ausdrücklich aus. Verschlüsselung der beiden Felder ist im Modell nicht vorgesehen.
2. Löschverhalten der Chat-Tabellen: chat_members, chat_messages, chat_message_keys, chat_reports, chat_attachments, chat_devices, chat_link_requests, chat_key_backups und chat_report_images haben keine Fremdschlüssel. Was bei Chat- oder Kontolöschung mit ihnen geschieht, ist im Modell nicht festgelegt.
3. Schüler-/Klassen-IDs (student_id, class_id, teacher_id) sind ohne Fremdschlüssel; sie verweisen auf das Planungsdokument. Die Integrität ist nicht durch die Datenbank gesichert.
4. Nicht erzwungene Bedingungen: assignment_extensions (Schüler/in oder Gruppe) und channel_group_gates (item oder folder) sind nicht per Constraint auf "genau eines" begrenzt.
5. Freigabe der Kursräume an Eltern (volljährige Schüler/innen): keine eindeutige Spalte im Modell.
6. Altbestand, der im Neubau entfallen kann: users.totp_secret; channel_folders.hidden und visibility = NULL; chat_messages.legacy_* (Übernahme aus altem Postfach); chats.only_admins_post (abgeleitet aus post_mode).
7. Die Kerntabellen-Liste im Quellmodul ist unvollständig (role_overrides, branches, user_branches fehlen dort).

**Werte, die im Quellmodell nicht stehen [unklar]:**
- Dauer: Sitzung (sessions.expires_at), Reset-Token, Geräteverknüpfung (chat_link_requests.expires_at), Papierkorb bis endgültigem Löschen, Wiederholungen und Abstände bei Benachrichtigungen.
- Schwellen: Sperre bei Anmeldeversuchen, Rate-Limit bei Zurücksetzen, Obergrenze der API-Protokollzeilen je Zugang.
- Bedeutung von NULL bei api_tokens.expires_at, rate_limit und ip_allow; Format von ip_allow und direct_key; Aufbau von definition (form_versions), result (form_submissions), grade_scale und period_times.
- Vollständige Wertelisten: form_submissions.status, form_events.action, form_templates.category, stored_files.kind, comp_links.item_type, comp_plans.item_type, api_token_log.outcome, Aufbau der Unterordner der Dateiablage.
- Verfahren für password_hash, sessions.token_hash und api_tokens.token_hash (Hash-Verfahren nicht angegeben).
- Kontext-Bindung (AAD) für form_submissions.decision_note_enc, form_events.note_enc und notifications_outbox.payload (E-Mail).
- Feldnamen der AAD bei comp_assessments, comp_plans, comp_badge_awards, chat_reports (hier nur als Muster `Feld:ID` angegeben).
- Wirkung von first_message_id = 0 (Chat), monitor (Ankündigung), sensitive (Formularvorlage) und der Schlüssel-Zuordnung von audience_roles.
- Bedeutung von chat_messages.deleted_at für das Chiffrat.
