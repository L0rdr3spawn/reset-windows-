# 03 – Datenmodell: Überblick, Prinzipien, Tabellenverzeichnis, DAT-Regeln

Paketdatei 03 · Kennungen **DAM-nnn** (Datenmodell-Regeln, Kapitel 4; `DAM-001` ff. gelten nur in dieser Datei und sind bewusst nicht „DAT“, damit sie nicht mit den Datenschutz-Anforderungen verwechselt werden) · Stand der Quellen: 2026-10-18.
Die vollständigen Spaltentabellen stehen im Anhang (Kapitel 5). Diese Datei enthält die Prinzipien, das Verzeichnis aller Tabellen, den Beziehungsüberblick und die prüfbaren Regeln.

---

## 0 Gegenstand und Lesehilfe

### 0.1 Gegenstand

- Das System hält Daten in **zwei Speicherformen**: (a) das **Planungsdokument** (ein versioniertes, als Ganzes gespeichertes Dokument für Stammdaten der Planung, Stunden, Abwesenheiten, Ferien, Aufsichten, Klausuren, Termine, Einstellungen) und (b) **relationale Tabellen** (Konten, Rechte, Protokolle und alle Fachdaten mit Personenbezug).
- Diese Datei legt fest, **was wo liegt und warum**, nach welchen Regeln Daten versioniert, verschlüsselt, gehasht, zeitgestempelt, gelöscht und migriert werden, und welche Tabellen es gibt.
- Fachliche Abläufe (Stundenplan, Vertretung, Klassenbuch, Noten, Nachrichten usw.) stehen in den jeweiligen Fachdateien. Rechte-Namen stehen in der Rechte-Datei. Das Löschkonzept im Ganzen (Auskunft, Art. 17, Wartelisten-Ablauf) steht in der Datenschutz-Datei; hier stehen nur die **Fristen je Tabelle** (Kapitel 1.10) und die Regeln, die das Schema betreffen.

### 0.2 Kennzahlen

| Kennzahl | Wert |
|---|---|
| Tabellen der Schul-Instanz | **123** (Anhang Z6a: 56 = 13 Kern + 43 Feature; Anhang Z6b: 54 in 15 Bereichen; Anhang Z6c: 13) |
| Tabellen des Anbieter-Lizenzservers | **13** (nur Anbieterseite, Kapitel 2.17) |
| Tabellen insgesamt (Ist-Zustand) | **136** (123 + 13) |
| Sammlungen des Planungsdokuments | **17** (+ `settings`; optional `monitors`, `holiday_import`) |
| Spalten der Tabellen aus Z6c | 133 (13 Tabellen) |
| Referenzbestand (Echtdaten-Probe, Ist) | 99 Klassen, 169 Lehrkräfte, 2.644 Schüler/innen, 1.554 Stunden, 5.462 Konten; Datenbank 3,3 MB, Dateien 0,8 MB |
| Zielgröße laut Zielbild (Ist) | ca. 2.500 Schüler/innen, ca. 200 Lehrkräfte, 2 Standorte |

### 0.3 Notation im Verzeichnis (Kapitel 2)

| Zeichen | Bedeutung |
|---|---|
| `→ T [K]` | Fremdschlüssel auf Tabelle `T`; **Kaskade**: die Zeile wird mit der Zielzeile gelöscht |
| `→ T [N]` | Fremdschlüssel auf `T`; beim Löschen der Zielzeile wird das Feld **leer** (NULL), die Zeile bleibt |
| `⇢ X` | **ID-Verweis ohne Datenbankbeziehung** (Zahl oder Text); Ziel ist das Planungsdokument oder eine andere Tabelle; die Integrität sichert die Anwendung |
| **V:** | Spalte wird **verschlüsselt** gespeichert (Präfix `SM1`, Bindung an Zeile und Feld, Kapitel 1.4) |
| **H:** | nur **Hash bzw. HMAC** gespeichert, nicht rückrechenbar (Kapitel 1.5) |
| **E2E:** | **Ende-zu-Ende** im Browser verschlüsselt; der Server kennt den Inhalt nicht |
| **K:** | **Klartext** mit Personenbezug (Auswahl der wichtigsten; Namen, Kennungen, IP-Adressen) |
| `Datenart` in Backticks | Eintrag im Löschkonzept (Kapitel 1.10) |
| `Z6a §…`, `Z6b …`, `Z6c §…`, `Z7 §…` | Fundstelle im Anhang (Kapitel 5) |
| [Lücke] | im Ist-Zustand fehlt eine Lösch- bzw. Aufbewahrungsregel (Regel DAM-077) |

### 0.4 Allgemeine Typkonventionen (Anhang Z6a §0, Z6b §0, Z6c §0)

| Typ | Bedeutung |
|---|---|
| Text(n) / Langtext | Text mit höchstens n Zeichen / ohne Längenbegrenzung |
| Zeitpunkt | Datum und Uhrzeit in **UTC**, ohne Zeitzone gespeichert |
| Datum | Text `JJJJ-MM-TT` (10 Zeichen); Uhrzeit-Felder `HH:MM` |
| JSON | strukturierte Liste oder Objekt |
| Binär | Bytefolge |
| Pflicht / optional | NOT NULL / NULL erlaubt |
| Standard | Wert bei Anlage, wenn nichts angegeben wird; „jetzt (UTC)“ = Zeitpunkt der Anlage |
| `updated_at` | wird im Ist-Zustand von der Anwendung bei jeder Änderung selbst gesetzt (keine automatische Aktualisierung im Modell), siehe DAM-059 |

---

## 1 Architekturprinzipien der Datenhaltung

### 1.1 Planungsdokument und relationale Tabellen: was liegt wo und warum

| Merkmal | Planungsdokument | Relationale Tabellen |
|---|---|---|
| Inhalt | `settings` und 17 Sammlungen: `sites`, `subjects`, `teachers`, `rooms`, `classes`, `students`, `curricula`, `grade_profiles`, `courses`, `lessons`, `absences`, `overrides`, `holidays`, `areas`, `duties`, `exams`, `events`; optional `monitors`, `holiday_import` | Konten, Sitzungen, Rechte, Protokolle, Klassenbuch, Fehlzeiten, Noten, Kompetenzen, Kursräume, Aufgaben, Lernaktivitäten, Postfach, Chats, Benachrichtigungen, Formulare, Förderdaten, Löschkonzept, Betrieb |
| Warum so | Ein **konsistenter Gesamtstand**: Generator, Vertretung, Konfliktprüfung und Ansichten lesen das ganze Bild. Änderungen sind **atomar**; Leser sehen nie einen halben Zustand; der **ganze Stand** ist rückgängig machbar und wiederherstellbar | Einzelne Zeilen, die unabhängig, gleichzeitig und von vielen Personen geändert werden; Abfragen, Sortierung, Fremdschlüssel und **Löschfristen je Zeile**; kein Gesamt-Rücksprung |
| Versionierung | **Ja**: jede Änderung = eine Version in `school_versions` (Kapitel 1.3) | **Nein** als Gesamtstand. Verlauf nur dort, wo ausdrücklich angehängt wird: `student_absence_events`, `gb_log`, `plan_proposal_log`, `assignment_submission_versions`, `form_versions`, `comp_assessments` (nur anhängen), `audit_log` |
| Schlüssel | Text-Kennungen (`id`), innerhalb einer Sammlung; Verweise ohne Prüfung im Ist-Zustand (DAM-008) | ganzzahlige Primärschlüssel, UUID (`stored_files`, `letter_batches`) bzw. 32-Zeichen-Kennung (`chat_attachments`) |
| Verschlüsselung | die **ganze Version** als eine Nutzlast | **spaltenweise** (`_enc`) |
| Personenbezug | Namen (`teachers`, `students`), Geburtsdatum, Abwesenheitsgründe: deshalb ist die Nutzlast verschlüsselt (DAM-023) | je Spalte ausgewiesen (Kapitel 2) |
| Brücke | Tabellen verweisen auf Planungsobjekte über **Text-IDs** (`student_id`, `class_id`, `teacher_id`, `course_id`, `exam_id`, `lesson_id`, `site`); Konten verweisen über `users.teacher_id` und `users.student_id` auf Personen des Planungsdokuments | das Planungsdokument kennt keine Konten |

Kernregel: **Personenbezogene Fachdaten mit hohem Änderungsaufkommen (Noten, Fehlzeiten, Nachrichten, Kursraum-Inhalte) liegen nie im Planungsdokument**; das Planungsdokument enthält nur Stamm- und Planungsdaten. (Ist-Zustand: Versionierung gibt es nur für das Planungsdokument.)

### 1.2 Wo liegt welche Einstellung

| Speicher | Inhalt | Beispiele |
|---|---|---|
| Umgebungsvariablen `SM_*` | Betrieb, Geheimnisse, Pfade, Schalter | `SM_ENV`, `SM_DATABASE_URL`, `SM_SECRET_KEY`, `SM_ENCRYPTION_KEYS`, `SM_KEEP_VERSIONS` (300), `SM_AUTH_CODE_MINUTES` (15), `SM_LETTER_BATCH_MINUTES` (60), `SM_STUDENT_DOCS_RETENTION_DAYS` (400), `SM_AUDIT_RETENTION_DAYS` (365), `SM_MAINTENANCE_INTERVAL` (3600 s), `SM_AUTO_BACKUP_HOURS` (0), `SM_BACKUP_KEEP` (30), `SM_SCRYPT_N` (32768) |
| Planungsdokument `settings` (versioniert) | fachliche Schuleinstellungen, auch mit Datenschutzwirkung | `period_times`, `breaks`, `sick_note_after_days` (3), `messaging_retention_days` (365 Tage, 0 = nie), `trash_retention_days` (30 Tage), `public_absent_teachers`, `absence_limit_percent`; Details Anhang Z7 §2.1 |
| `security_settings` | Sicherheitseinstellungen der Schule (Schlüssel/Wert, JSON) | Pflicht zur zweiten Anmeldestufe, Sitzungsvorgaben (Schlüsselliste [unklar], DAM-010) |
| `retention_settings` | Fristen und Schalter des Löschkonzepts | `grace_days`, `auto_purge`, `audit_days`, `log_days`, `<datenart>.days`, `<datenart>.age_days` |
| `gb_config` | Einstellungen des Notenbuchs | Standardwerte [unklar] |
| `notification_school`, `notification_config`, `notification_prefs`, `notification_user_settings` | Benachrichtigungen schulweit bzw. je Konto | `retention_days`, Modus aus/app/mail, Ruhezeit 21:00–07:00 |
| `login_policy_rules` | Anmelde-Richtlinien je Geltungsbereich | default, role, grade, class, user |
| `sso_providers` | Einrichtung der Anmeldedienste | `SM_SSO_*` / `SM_OIDC_*` haben Vorrang |
| `system_state` | Betriebszustand ohne eigene Tabelle | Schlüssel `setup`, `school_profile`, `yearchange`, `maintenance`; Leader-Pacht im Mehr-Knoten-Betrieb |
| Dateien im Datenordner (keine Datenbank) | Lizenz-Zustand, Update-Status und -Plan, Sicherungen, temporäre Erst-Administrator-Datei | siehe Betriebs-Datei |

### 1.3 Planungsdokument: Aufbau, Versionierung, Rückgängig, Synchronisierung

**Aufbau (Anhang Z7 §1, §2).** Genau ein Objekt `settings`, 17 Sammlungen (Listen von Datensätzen mit Text-`id`), optional `monitors` und `holiday_import`. Serialisierung verlustfrei als JSON; beim Lesen werden unbekannte Felder und Sammlungen verworfen; fehlende optionale Felder bekommen den Standardwert; beim Speichern wird das ganze Dokument in das aktuelle Format normalisiert.

**Zeitbasis.**

| Größe | Zählung |
|---|---|
| Wochentag | 0 = Montag … 6 = Sonntag |
| Stunde | 0-basiert (erste Stunde = 0) |
| Laufende Woche | 1-basiert, 1 bis 52 bzw. 53, Montag bis Sonntag, Ferien zählen mit; Zählung nach `week_numbering` ("iso" = Kalenderwochen, Standard; "school_year" = Woche 1 ist Schuljahresbeginn) |
| Datum | ISO `JJJJ-MM-TT` |
| Wochenangabe | `weeks` (Liste laufender Wochen) **oder** `rhythm` {every, from_week, to_week}; ist `rhythm` gesetzt, wird `weeks` ignoriert; beides leer = jede Woche; unbekannte Woche = Regel gilt als aktiv |
| Leere Liste | bedeutet „alle“ (Tage, Stunden, Klassen+Klassenstufen, Standorte, Wochen, Unterrichtstage) |

**Versionierung (Anhang Z7 §4–§8).**

| Regel | Wert |
|---|---|
| Neue Version | jede erfolgreiche Änderung erzeugt genau eine; identischer Stand (SHA-256 über das JSON) erzeugt keine Version, keinen Audit-Eintrag, kein Ereignis; Fehler: nichts gespeichert |
| Arbeitsweise | jede Änderung arbeitet auf einer vollständigen Kopie; erst nach erfolgreichem Speichern ersetzt sie den aktiven Stand |
| Metadaten je Version | Nummer (fortlaufend, nie wiederverwendet), Urheber (leer = System), Notiz (höchstens 500 Zeichen, länger wird gekürzt), Bereich (Liste, Standard `["all"]`; feste Werte `init`, `restore`, `undo`), Ursprungsversion (`restored_from`), Zeitpunkt UTC |
| Aufbewahrung | 300 Versionen (`SM_KEEP_VERSIONS`); nach jedem Speichern werden die ältesten darüber endgültig gelöscht; gelöschte Versionen sind nicht wiederherstellbar; Mindest-/Höchstwert [unklar] |
| Verlauf | neueste zuerst; Standard 50 je Seite, höchstens 1000 je Abfrage; aktuelle Version gekennzeichnet; Anzeigename = Anzeigename, sonst Benutzername, ohne Konto „System“ |
| Audit je Version | Aktionen `plan.init`, `plan.change`, `plan.replace`, `plan.restore`, `plan.undo`; Ziel = Versionsnummer |
| Ereignis | „change“ nach jeder erfolgreichen Änderung (auch Wiederherstellen, Rückgängig, Ersetzen) mit Versionsnummer, Bereich, Datumsliste; keine Inhalte |
| Standard-Notizen | „Leeres Planungsdokument angelegt“; „Version N wiederhergestellt“; „Rückgängig: zurück auf Version N (Notiz der Version N)“ |

**Rückgängig (Entscheidungstabelle).**

| Aktuelle Version ist … | Basis | Zielversion |
|---|---|---|
| normale Änderung | diese Version | jüngste Version mit kleinerer Nummer |
| Rückgängig-Schritt (Bereich enthält `undo`, Ursprung N) | N | jüngste Version mit Nummer kleiner als N |
| Wiederherstellung (Bereich `restore`) | diese Version | jüngste Version mit kleinerer Nummer (Stand vor der Wiederherstellung) |
| Ersetzen ohne Ursprung (Import, Demo) | diese Version | jüngste Version mit kleinerer Nummer |
| keine lesbare aktuelle Version | – | Fehler „Kein aktueller Stand vorhanden“ |
| keine ältere Version | – | Fehler „Es gibt keine ältere Version, die wiederhergestellt werden kann“ |

Rückgängig erzeugt eine neue Version (Bereich `["all","undo"]`, Ursprung = Zielversion); wiederholtes Rückgängig geht Schritt für Schritt zurück; nichts wird gelöscht. Wiederherstellen von Version N erzeugt eine neue Version (Bereich `["all","restore"]`, Ursprung N); fehlt N: Fehler „Version N existiert nicht (mehr)“. Rückgängig und Wiederherstellen laufen unter derselben Sperre wie Änderungen.

**Synchronisierung.**

| Regel | Wert |
|---|---|
| Leser | erhalten eine Momentaufnahme; Schreiben blockiert Lesen nie |
| Prüfung auf neuere Version | höchstens alle **2 s**; nur bei abweichender Versionsnummer wird neu geladen |
| Vor jeder Änderung | die neueste Version wird nachgeladen |
| Änderungen im Prozess | strikt nacheinander (Sperre); empfohlen: genau ein Arbeitsprozess |
| Mehrere Prozesse ohne Mehrserver-Betrieb | **keine** Prüfung, ob zwischenzeitlich eine andere Version entstand: gleichzeitige Änderungen können sich überschreiben (Lost Update) – Lücke, DAM-021 |
| Mehrserver-Betrieb | Prüfung vor dem Speichern; sonst Fehler „Der Plan wurde inzwischen auf einem anderen Server geändert. Bitte erneut versuchen.“; keine automatische Zusammenführung; auf PostgreSQL zusätzlich datenbankweite Schreibsperre bis zum Commit |
| Prüfsumme | SHA-256 des aktuellen Stands; wird nicht gespeichert, sondern beim Laden berechnet |

**Speicherformat der Nutzlast.** JSON (UTF-8, Umlaute unverändert, Schlüssel sortiert, ohne Leerzeichen) → zlib (Stufe 6) → AES-256-GCM mit eigenem Datenschlüssel je Version; Zusatzkontext `school_versions.data:<Versionsnummer>`; die Prüfsumme wird über das JSON **vor** der Verschlüsselung gebildet.

**Start.** Geladen wird die jüngste lesbare Version (geprüft werden höchstens die 5 jüngsten; unlesbare werden übersprungen und protokolliert). Ist die Tabelle leer: leeres Dokument als neue Version (Notiz „Leeres Planungsdokument angelegt“, Bereich `["all","init"]`, Aktion `plan.init`). Sind die 5 jüngsten unlesbar: Ist-Zustand startet mit leerem Dokument (Risiko, DAM-026).

**Gespeicherte Plan-Stände** (`plan_snapshots`): der Stundenplan (nur Unterrichtsblöcke) unter einem Namen; bleibt bis zum Löschen erhalten, unabhängig von der 300er-Grenze; Wiederherstellen legt wie jede Änderung eine neue Plan-Version an.

### 1.4 Verschlüsselungsprinzip (Zusatzdaten und Bindung)

| Parameter | Wert |
|---|---|
| Verfahren | AES-256-GCM (authentifiziert) |
| Hülle | **jeder** Wert (jedes Feld, jede Datei) hat einen eigenen zufälligen 256-Bit-Datenschlüssel; dieser wird mit dem aktiven Hauptschlüssel des Schlüsselrings umschlossen |
| Nonce | 96 Bit, zufällig je Verschlüsselung |
| Textformat | Präfix `SM1.` + Base64-URL ohne Auffüllung (ASCII, für Textspalten) |
| Binärformat | Präfix `SM1` |
| Dateiformat | Präfix `SMS1`, blockweise (Standard 64 KiB, zulässig 1 KiB bis 16 MiB), 32-Bit-Blockzähler mit Schlussblock-Kennzeichen (verhindert Vertauschen, Weglassen, Abschneiden, Anhängen); Dateiprefix 7 Byte zufällig |
| Leere Werte | bleiben leer und werden nicht verschlüsselt |
| **Bindung (AAD)** | Jedes Chiffrat ist an **Tabelle, Feld und Zeilen-ID** gebunden: `<tabelle>.<feld>:<zeilen-id>`. Die ID muss **vor** dem Verschlüsseln feststehen. Ein in eine andere Zeile kopiertes Chiffrat lässt sich nicht entschlüsseln |
| Fehlerarten | „ungültig“ (Manipulation, falsches Zusatzdatum, falscher Schlüssel); „nicht lesbar“ (unbekannte Schlüssel-ID); der Klartext wird nie zurückgegeben; Anzeige „[nicht lesbar]“ plus Protokolleintrag |
| Schlüsselring | `SM_ENCRYPTION_KEYS`, Format `kid:Base64(32 Byte)`; erster Eintrag **aktiv**, weitere nur zum Entschlüsseln; Schlüssel-ID 1–32 Zeichen (A–Z, a–z, 0–9, `_`, `-`), `dev` reserviert; Produktion: Pflicht, sonst bricht der Start ab; Entwicklung: `dev` aus `SM_SECRET_KEY` abgeleitet, Warnung |
| Rotation | neuen Schlüssel vorn eintragen, Neustart, CLI `rotate-keys`: Datenschlüssel werden neu umschlossen, Nutzdaten und AAD bleiben; Dateien: nur der Kopf wird neu geschrieben; `gen-key` erzeugt Schlüssel, `crypto-status` zeigt Fingerabdruck (12 Hex-Zeichen, nicht umkehrbar) |
| Abweichende AAD im Ist-Zustand | `messages.body:<conversation_id>:<message_id>`; `message_drafts.data:<user_id>:<draft_id>`; `message_user_settings.suspension_reason:<user_id>`; `sso_providers.<feld>:<Anbieter>`; `letter_batches:<id>`; `backup.school:<Version>`; `teacher_change_requests:<id>:<feld>`; Löschgrund im Audit mit **festem** Zusatzdatum `audit_log.privacy.erase.grund` (nicht zeilengebunden) – im Neubau vereinheitlicht, DAM-033 |
| Chats | **Ende-zu-Ende** im Browser; der Server speichert nur Chiffrat, Nonce, öffentliche Gerätschlüssel, je Gerät verpackte Nachrichtenschlüssel und das im Browser verschlüsselte Schlüssel-Backup |
| Dateien | nur verschlüsselt auf dem Datenträger; Dateiname verschlüsselt in der Datenbank; SHA-256 über den Klartext zur Integritätsprüfung |

Verschlüsselte Spalten je Tabelle: siehe Kapitel 2 (Spalte „Geschützte Spalten“) und Anhang Z6a §5, Z6b §4, Z6c.

### 1.5 Hashing und Geheimnisse

| Gegenstand | Verfahren / Wert |
|---|---|
| Passwort (`users.password_hash`) | scrypt; `SM_SCRYPT_N` Standard 32768 (2^15), Produktion mindestens 16384 (2^14), Zweierpotenz; r = 8, p = 1; Hash 32 Byte; Salt 16 Byte; Format `scrypt$n$r$p$salt$hash` |
| Startpasswort (`account_initial_passwords.password_hash`) | scrypt mit N = 2048 (2^11); Passwort ist zufällig (ca. 60 Bit); Kopie des Konto-Hashs, nie Klartext |
| Sitzungs- und API-Token | 32 Byte Zufall, URL-sicher; gespeichert wird nur **HMAC-SHA256** mit `SM_SECRET_KEY`; CSRF-Token je Sitzung 24 Byte Zufall |
| Einmal-Codes, Link-/Reset-Token, Kennung beim Zurücksetzen, Telefonnummer zur Suche, Kalender-Abo-Token, Teilnahme-Token von Abstimmungen | nur HMAC (Schlüssel `SM_SECRET_KEY`); beim Zurücksetzen 6 Ziffern |
| Prüfsummen | `stored_files.sha256` (SHA-256 des Klartexts), `import_runs.source_hash`, `plan_proposals.state_hash` |
| `SM_SECRET_KEY` | Produktion Pflicht, mindestens 32 Zeichen; HMAC-Schlüssel auch für SSO-Status, Teilnahmekennungen und OAuth-Status des Postfachs; Wechsel macht bestehende Sitzungs-Hashes ungültig |
| Passwortprüfung gegen bekannte Datenlecks | Einstellung, Standard aus; nur Hash-Präfix (SHA-1) |
| Öffentliche Schlüssel | `chat_devices.public_key` ist kein Geheimnis |

### 1.6 Zeitstempel: UTC

- Alle **Zeitpunkte** (Spalten vom Typ Zeitpunkt, auch `created_at`, `updated_at`, `expires_at`, `deleted_at`) werden in **UTC** gespeichert; Anzeige in Ortszeit ist Sache der Oberfläche. Auch Zeitstempel in Protokollen sind UTC (Beispiel Ist: Eintrag um 22:23 UTC = 00:23 Ortszeit).
- Eingaben in Ortszeit (Europa/Berlin, z. B. Update-Zeitfenster) werden in UTC gespeichert; ein Fensterbeginn in der Sommerzeit-Lücke rutscht nach vorn; Fenster können über Mitternacht gehen.
- **Datumsfelder** ohne Uhrzeit sind `JJJJ-MM-TT` (kein Zeitzonenbezug); Uhrzeiten `HH:MM`.
- Planungsdokument: Stunden 0-basiert, Wochen 1-basiert (Kapitel 1.3).
- Aufbewahrungsfristen rechnen in Tagen ab dem jeweiligen Zeitpunkt (Anlage, Austritt, Ablauf), in Stunden bzw. Minuten bei kurzlebigen Daten.

### 1.7 Löschverhalten und Fremdschlüssel

| Muster | Bedeutung | Beispiele |
|---|---|---|
| **Kaskade** `[K]` | Zeile wird mit der Elternzeile gelöscht | `sessions`, `api_tokens`, `parent_links`, `user_contacts`, `notifications` → `users`; alle `channel_*`, `learning_*` (Kursraum-Bezug), `completion_*`, `availability_rules` → `channels`; `form_versions`, `form_submissions` → `form_templates`; `assignment_submission_versions` → `assignment_submissions`; `gb_categories`, `gb_items`, `gb_finals` → `gb_books`; `comp_*` → `comp_frameworks` |
| **Feld leeren** `[N]` | Urheber-, Verfasser-, Ersteller-Verweis wird NULL, Zeile bleibt | `audit_log.user_id`, `school_versions.user_id`, `announcements.author_id`, `student_absences.reported_by`, `messages.sender_id`, `channels.created_by`, `stored_files.owner_user_id`, `student_documents.file_id` |
| **ID-Verweis ohne Beziehung** `⇢` | nur Zahl oder Text | alle Verweise auf das Planungsdokument; die Chat-Tabellen untereinander; Protokolle, die ihr Ziel überleben sollen (`student_absence_events.absence_id`, `gb_log.book_id`, `plan_proposal_log.package_id`); generische Verweise (`completion_*.element_id`, `comp_links.item_id`) |

Regeln:

1. **Konto wird gelöscht:** alle Zeilen mit Kaskade auf `users` verschwinden (Anmeldedaten, Kontakte, Verknüpfungen, Teilnahmen, Benachrichtigungen, Entwürfe, Blockierungen, Einstellungen, Abgaben, Fortschrittsmarken); Ersteller- und Absenderfelder werden NULL; Anzeigenamen-Spalten (`*_name`, Klartext) bleiben im Ist-Zustand stehen (DAM-062).
2. **Pseudonymisierung** statt Löschung bei Protokollen (Anhang Z3 §6, Kapitel 1.10): Audit `user_id` leer und `username` = `gelöscht#<Konto-ID>` (ebenso alle Einträge mit demselben Benutzernamen); Abwesenheitsereignisse `actor_id` leer und `actor_name` = `gelöscht#<Konto-ID>`; Planversionen und Mitteilungen `user_id`/`author_id` leer; Krankmeldungen `reported_by` leer; Anmeldeversuche des Kontos werden gelöscht; Klassenbuch: nur der Eintrag der Person im Anwesenheitsfeld entfällt (Thema und Hausaufgabe bleiben).
3. **Verweise auf das Planungsdokument** (`student_id`, `class_id`, `teacher_id`, `course_id`, `exam_id`) sind ohne Fremdschlüssel; die Integrität stellt das Löschkonzept her (Person nicht mehr im Planungsdokument → Warteliste → Fristen). Ein **leeres** Schülerverzeichnis wird nie als „alle ausgetreten“ gewertet.
4. **Chat-Tabellen** (`chat_members`, `chat_messages`, `chat_message_keys`, `chat_reports`, `chat_attachments`, `chat_devices`, `chat_link_requests`, `chat_key_backups`, `chat_report_images`) haben im Ist-Zustand keine Fremdschlüssel; die Bereinigung erfolgt durch das Löschkonzept (Datenart `chats`); Regel DAM-064.
5. **Weiches Löschen:** `channel_items`, `channel_folders` (Papierkorb: `deleted_at`, `deleted_by`, `trash_group`), `channel_posts`, `stored_files` (`deleted_at`), `student_documents` (`withdrawn_at`), `messages` (`removed_at` durch die Moderation) bleiben zunächst erhalten; normale Abfragen blenden sie aus; endgültig entfernt nach der Frist (Kapitel 1.10).
6. **Nur anhängen** (kein Ändern/Löschen einzelner Zeilen): `student_absence_events`, `plan_proposal_log`, `comp_assessments`, `form_versions`, `audit_log`, `retention_log`; Löschung nur durch Frist bzw. Löschkonzept.
7. **Schema-Falle:** Umbau von Tabellen mit kaskadierenden Fremdschlüsseln (`users`, `channel_folders`) kann Daten vernichten (SQLite-Tabellenumbau); nur mit Prüfplan (Kapitel 1.8, DAM-097).

### 1.8 Migrationsregeln (Expand/Contract)

| Regel | Inhalt |
|---|---|
| Nur Migrationen | Das Schema ändert sich **ausschließlich** über versionierte Migrationen, linear und lückenlos (keine parallelen Ketten). Ein automatischer Test vergleicht das Datenmodell mit dem migrierten Schema |
| Beim Start | Start-Reihenfolge: Konfiguration prüfen → Schema automatisch migrieren → Erststart-Prüfung (Erst-Administrator) → Hintergrundaufgaben. Manuell: CLI `migrate`. Bei mehreren Knoten gilt der Migrationslauf als Konfliktpunkt (Hinweis) |
| **Expand/Contract** | Jede Schemaänderung muss mit der **Vorgängerversion** zusammenarbeiten (rollendes Update, Rücknahme): erst erweitern (neue Spalten optional bzw. mit Standard, neue Tabellen), später entfernen. Beispiel Ist: Bei `learning_poll_participants` bleibt die alte Eindeutigkeit (`poll_id`, `user_id`), damit der alte Code beim rollenden Update weiter schreiben kann |
| Prüfskript | läuft vor jeder Freigabe und muss sauber sein; Ausnahmen werden bewusst als **„breaking“** freigegeben und im Release gekennzeichnet („Angabe, ob Datenbankänderung“) |
| Standardwerte | Planungsdaten müssen mit Standardwerten auskommen (alte Dokumente bleiben ladbar) |
| Gefährliche Umbauten | Tabellen mit kaskadierenden Fremdschlüsseln (Konten, Kursraum-Ordner) nur mit gesondertem Prüfplan |
| Datenumbauten | Umbauten, die Werte umschreiben (z. B. Verschlüsselungsumstellung), werden von Hand geprüft; vorher Probelauf auf einer Kopie der Echtdaten und Sicherung |
| Anbieter-Tabellen | haben im Ist-Zustand keine Migrationshistorie; Änderungen laufen über eine eigene Anpassung beim Start (Beispiel: Anzeige-Kopie der Lizenzschlüssel seit 16.10.2026) – im Neubau vereinheitlicht, DAM-100 |
| Datenbanken | SQLite (Standard: eine Datei im Datenordner) und PostgreSQL (für große Schulen und Mehr-Server-Betrieb); gleiches Schema, gleiche Migrationen; JSON-Export-Sicherung nur bei PostgreSQL; **eine eigene Datenbank, ein eigener Geheimschlüssel und ein eigenes Datenvolumen je Instanz** |

**Entwicklungsgeschichte (Phasen des Ist-Zustands, nur als Orientierung für die Datenübernahme; Migrationsnummern sind nicht Teil des Vertrags).**

| Phase | Neue fachliche Bereiche / Tabellen |
|---|---|
| 1 Grundgerüst | Konten, Sitzungen, API-Zugänge, Anmeldeversuche, Elternverknüpfungen, Audit, Planversionen, Mitteilungen, Fehlzeiten (Grundform), Ausgangs-Warteschlange |
| 2 Zusammenarbeit | Dateiablage, Lehrkraft-Anträge, Kursräume (Kanäle, Material, Abgaben, Pinnwand, Besuchsstand), Postfach, eingereichte Dokumente |
| 3 Konten und Anmeldung | Kontakt und Wiederherstellung (Einmal-Codes), Zugangsbriefe, Anbieter-Konten und Anmeldedienste, Anmelde-Richtlinien |
| 4 Elternzugriff, Mail, Fehlzeiten | Elternzugriff je Bereich, verbundene E-Mail-Konten mit externen Adressen, Fehlzeiten mit Art, Minuten, Herkunft, Verknüpfung zum Klassenbuch |
| 5 Noten, Klassenbuch, Förderung | Noten zu Klausuren, Klassenbuch, Förderinformationen mit Katalog |
| 6 Chats Ende-zu-Ende | Geräte, Chats, Nachrichten, Schlüssel, Meldungen; Trennung von Postfach und Chats; Anhänge; Geräteverknüpfung und Schlüssel-Backup |
| 7 Feinausbau | schulspezifische Rollen-Abweichungen, Schulzweige, Kursraum-Material mit Datum, Infokarten, Elternzugriffs-Einstellungen, Formular-Baukasten, Nachschreibtermine, archivierte Schülerdokumente, API-Zugänge mit Umfang |
| 8 Aufgaben, Lernen, Notenbuch | Bewertungsraster, Fristverlängerung, Abgabe-Versionen, Gruppen, Plan-Prüfung, Lernfortschritt, Lernaktivitäten, Notenbuch, Kompetenzen, Benachrichtigungszentrale |
| 9 Betrieb und Datenschutz | Löschkonzept, Sicherheits-Härtung (13.10.2026), verschlüsselte Geheimnisse (Kalender-Token nur Hash, Zwei-Faktor-Geheimnis verschlüsselt), Zustandsspeicher, Fehlerprotokoll, Fremdsystem-Importe |
| 10 Plan-Stände und Verschlüsselung | gespeicherte Plan-Stände (je Planzeitraum), Anonymität bei Lernaktivitäten, Verschlüsselung der Freitexte in Lehrkraft-Anträgen |
| 11 Rechte und API (zuletzt) | API-Schreibzugang mit Protokoll, eigene Rollen der Schule, beobachtete Konten, Doppelsende-Schutz (Stand 17.10.2026) |

### 1.9 Alt-Spalten, die im Neubau entfallen

| Spalte | Grund |
|---|---|
| `users.totp_secret` | Klartext-Altbestand, nach Umstellung leer; es gilt `totp_secret_enc` |
| `channel_folders.hidden` und `channel_folders.visibility` = NULL | Altbestand; nur die Sichtbarkeitswerte `visible`/`hidden`/`scheduled`/`lesson` gelten |
| `chat_messages.legacy_body_enc`, `legacy_source_message_id`, `legacy_source_conversation_id` | nur Übernahme aus dem früheren Postfach |
| `chats.only_admins_post` | abgeleitet aus `post_mode` |
| unverschlüsselter Altbestand der Planversionen | im Neubau von Anfang an verschlüsselt (DAM-024) |

### 1.10 Aufbewahrung und Löschung: Fristen je Datenart (Kurzfassung)

Wirksame Frist nach Austritt je Datenart = **Maximum aus eigener Frist und Wartelisten-Frist** (`grace_days`, Standard 30 Tage). Alle Fristen einstellbar von 0 bis 3650 Tage (`<datenart>.days`, `<datenart>.age_days`; 0 = aus). Schalter `auto_purge` (Standard an) steuert die Fristlöschung nach Austritt; Alters-Fristen laufen unabhängig. Löschung ist **hart** (endgültig), außer bei „anonymisieren“. Hauptlauf: alle `SM_MAINTENANCE_INTERVAL` (Standard 3600 s, erster Lauf sofort beim Start).

| Datenart | Tabellen | Frist nach Austritt | Laufende Frist (Alter) | Verfahren |
|---|---|---|---|---|
| `absences` | `student_absences`, `student_absence_events`, `exam_makeups` | 30 Tage | 365 Tage (Meldung abgelaufen, wenn ihr Enddatum vor dem letzten 31. Juli liegt, der vor „heute minus 365 Tage“ liegt) | löschen, Blöcke zu 500 |
| `documents` | `student_documents` (+ Datei) | 30 Tage | 400 Tage ab Erstellung (`SM_STUDENT_DOCS_RETENTION_DAYS`; 0 = aus), durch die Wartung | löschen, höchstens 5000 je Lauf; erfasst auch Dokumente, die das Konto der Person hochgeladen hat |
| `support` | `student_support` (+ Dateien) | 30 Tage | – | löschen |
| `forms` | `form_submissions`, `form_events` (+ Dateien) | 90 Tage | abgeschlossene Einreichungen 400 Tage nach Erstellung | löschen, höchstens 5000 je Lauf |
| `exam_results` | `exam_results` | 180 Tage | – | löschen |
| `gradebook` | `gb_entries`, `gb_finals`, `gb_log`, `gb_source_results` | 180 Tage | – | löschen |
| `competencies` | `comp_assessments`, `comp_plans`, `comp_badge_awards` | 180 Tage | – | löschen |
| `attendance` | `register_lessons` (Anwesenheitsfeld) | 365 Tage | – | **anonymisieren**: nur der Eintrag der Person entfällt; Aufbewahrung des Klassenbuchs nach Landesrecht prüfen [unklar] |
| `submissions` | `assignment_submissions`, `assignment_submission_versions` (+ Dateien) | 90 Tage | – | löschen |
| `learning` | `learning_attempts`, `learning_poll_votes`, `learning_poll_participants`, `learning_survey_responses`, `learning_survey_participants` | 90 Tage | – | löschen; anonym gespeicherte Umfrage-Antworten bleiben (keiner Person zuzuordnen) |
| `progress` | `completion_marks`, `channel_reads`, `channel_item_views`, `channel_group_members`, `channel_extra_members`, `assignment_extensions` | 90 Tage | – | löschen |
| `files` | `stored_files` (Eigentümer = Konto) | 30 Tage | – | hart löschen (Inhalt und Eintrag) |
| `notifications` | `notifications`, `notification_prefs`, `notification_user_settings` | 30 Tage | 90 Tage (Einstellung 7 bis 730) | löschen, auch Benachrichtigungen, die die Person betreffen |
| `messages` | `messages`, `conversations` (leere), `conversation_participants`, `message_drafts`, `user_blocks`, `message_user_settings`, `message_reports` | 30 Tage | `messaging_retention_days` 365 Tage (0 = nie), ausgenommen offen gemeldete | eigene Nachrichten samt Anhängen löschen; Nachrichten anderer bleiben bis zu deren Frist |
| `chats` | alle Chat-Tabellen (Kapitel 2.10) | 30 Tage | – [unklar: keine laufende Frist; aus dem Postfach übernommene Kopien folgen der Postfach-Frist] | Mitgliedschaften, Geräte, Backup, Schlüssel, eigene Nachrichten, Anhänge, Meldungen mit Bildern löschen; **Einzelchats ganz**, Gruppen ohne Mitglieder entfernen |
| `parents` | `parent_links`, `parent_access`, `student_prefs` | 30 Tage | – | löschen; Eltern-Konto (Rolle Eltern oder Schulbegleitung) ohne weiteres Kind wird mit Daten und Konto gelöscht |
| `accounts` | `users` (+ Kaskaden) | 30 Tage, läuft **zuletzt** | – | Konto löschen; Administrator-Konten nie |
| `history` | `school_versions` (Person aus allen Versionen entfernt), Protokollziele | 30 Tage | – | **anonymisieren**: Namen in Versionstexten → „[gelöscht]“; Ziele `student:<ID>` → `student:gelöscht`, Details entfernt; läuft nur bei Schüler/innen |
| `api_log` | `api_token_log` | 30 Tage | 90 Tage | löschen |
| `watch_log` | `watch_log`, `account_watch` | 30 Tage; bei Kontolöschung **sofort** | 180 Tage | löschen; nicht in der Selbstauskunft |

Weitere Fristen:

| Gegenstand | Frist |
|---|---|
| `audit_log` | 365 Tage (`audit_days`; 0 = nie) |
| `retention_log` (Löschprotokoll) | 1095 Tage (`log_days`) |
| `retention_leavers` (erledigte Einträge) | 1095 Tage nach Abschluss; Name wird beim Abschluss geleert |
| `error_log` | 30 Tage, höchstens 1000 Zeilen (älteste zuerst) |
| `login_attempts` | 30 Tage |
| `sessions` | bis Ablauf; Dauer Schüler/innen und Eltern 7 Tage Inaktivität, Personal 12 Stunden Inaktivität (einstellbar 15 Minuten bis 7 Tage, nie länger als der Schüler-Wert), absolut 30 Tage |
| `api_tokens` | persönliche Tokens ohne Umfang: sofort nach Ablauf; Zugänge mit Umfang: 30 Tage nach Ablauf |
| `auth_codes` | gültig 15 Minuten (`SM_AUTH_CODE_MINUTES`), höchstens 5 Fehlversuche je Code, gelöscht 1 Stunde nach Ablauf |
| `letter_batches` | 60 Minuten (`SM_LETTER_BATCH_MINUTES`, 1 bis 1440); danach Löschung durch die Wartung, Zugriff liefert 410 |
| `account_initial_passwords` | Frist 14 Tage (Einstellung 1 bis 90); Zeile verschwindet beim Passwortwechsel |
| `stored_files` | Uploads ohne Anhang 24 Stunden; weich gelöschte Dateien 30 Tage |
| `chat_attachments` | lose (nicht gesendete) Uploads 24 Stunden |
| Kursraum-Papierkorb (`channel_items`, `channel_folders`) | 30 Tage (`trash_retention_days`, 1 bis 365) |
| `school_versions` | 300 Versionen (`SM_KEEP_VERSIONS`) |
| `notifications_outbox` | Inhalt nach Zustellung geleert; Frist der Zeilen [unklar] |
| Sicherungen | Löschkonzept wirkt **nicht** auf Sicherungen; Rotation `SM_BACKUP_KEEP` = 30 neueste Dateien (0 = keine) |

**Lücken im Katalog (Ist):** keine Datenart und keine Frist für `channel_items`/`channel_posts`/`channel_folders` (Kursraum-Inhalte; nur Papierkorb), `teacher_change_requests`, `user_contacts`, `user_identities`, `import_runs`, `plan_proposals`/`plan_proposal_log`/`plan_snapshots`, `mail_accounts`, `announcements` (nur Verfasser pseudonymisiert), `exam_makeup_dates`, `send_idempotency`; Regel DAM-077.

---

## 2 Tabellenverzeichnis

Jede Tabelle der drei Z6-Anhänge steht hier genau einmal (Zählkontrolle in Kapitel 2.19). Spalten: Zweck in einem Satz · wichtigste Beziehungen · verschlüsselte, gehashte und personenbezogene Klartext-Spalten · Aufbewahrung bzw. Löschung · Fundstelle im Anhang. Notation: Kapitel 0.3.

### 2.1 Konten, Sitzungen, Anmeldung (11 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `users` | Konto jeder Person (Schüler/in, Lehrkraft, Eltern, Verwaltung) mit Anmeldedaten, Grundrolle und optionaler eigener Rolle | Wurzel der Konten-Kaskaden; `role` = eine von 12 Grundrollen (admin, schulleitung, abteilungsleitung, planer, sekretariat, lehrer, hausmeister, schulbegleitung, schueler, eltern, monitor, zuschauer); `custom_role` ⇢ `custom_roles.id`; `teacher_id`, `student_id` ⇢ Planungsdokument; eindeutig: `username`, `oidc_sub`, `ical_token` | **H:** `password_hash` (scrypt), `ical_token` (HMAC); **V:** `totp_secret_enc`; **K:** `username`, `display_name`, `email`, `site`; Altfeld `totp_secret` entfällt (Kapitel 1.9) | `accounts`: 30 Tage nach Austritt, zuletzt; Admin-Konten nie; Konto ohne Schüler-Bezug sofort (Art. 17) | Z6a §1.1 |
| `sessions` | Angemeldete Sitzung (Cookie `sm_session`), nur der Hash des Tokens wird gespeichert | `user_id` → `users` [K]; eindeutig `token_hash` | **H:** `token_hash` (HMAC-SHA256); `csrf_token` (Zufallswert je Sitzung); **K:** `ip`, `user_agent` | bis Ablauf; Wartung löscht abgelaufene stündlich; Dauer Kapitel 1.10 | Z6a §1.2 |
| `login_attempts` | Protokoll jedes Anmeldeversuchs (Grundlage von Sperre und Drosselung je Benutzername und je IP) | kein FK (`username` auch für unbekannte Namen) | **K:** `username`, `ip` | 30 Tage (Wartung); bei Kontolöschung gelöscht | Z6a §1.4 |
| `auth_codes` | Einmal-Codes, Link-Token und Zähler für Kontaktbestätigung, Passwort-Zurücksetzen und Rate-Limit | `user_id` → `users` [K] (leer bei unbekannter Kennung) | **H:** `code_hash`, `token_hash`, `ident_hash` (HMAC); **V:** `target_enc`; **K:** `ip` | gültig 15 min, 5 Fehlversuche, 1 h nach Ablauf gelöscht | Z6a §2.4 |
| `user_contacts` | Bestätigte E-Mail-Adresse und Handynummer je Konto (Bestätigung, Passwort-Zurücksetzen) | `user_id` → `users` [K] (PK) | **V:** `phone_enc` (E.164); **H:** `phone_hash` (HMAC, nur zur Suche); **K:** `email_verified_value` | Kaskade mit Konto; keine eigene Datenart [Lücke] | Z6a §2.3 |
| `user_identities` | Verknüpfung eines Kontos mit einem Anbieter-Konto (Microsoft, Apple, Google, Schulkonto) | `user_id` → `users` [K]; `created_by` → `users` [N]; eindeutig (`provider`,`subject`) und (`user_id`,`provider`) | **K:** `subject`, `email` | Kaskade mit Konto; keine eigene Datenart [Lücke] | Z6b B1 |
| `sso_providers` | Einrichtung der Anmeldedienste (Microsoft, Apple, Google, allgemeines OIDC) durch die Administration | `updated_by` → `users` [N]; PK `provider` | **V:** `client_secret_enc`, `private_key_enc` (Apple-Schlüsseldatei); `client_id` ist kein Geheimnis | Konfiguration, keine Frist; `SM_SSO_*`/`SM_OIDC_*` haben Vorrang | Z6b B2 |
| `login_policy_rules` | Anmelde-Richtlinie je Geltungsbereich (default, role, grade, class, user): erlaubte Wege, Pflichtverknüpfungen, Selbstverknüpfung, Rücksetzkanäle, Anlage per SSO | `updated_by` → `users` [N]; `scope_ref` ⇢ Rolle / Klassenstufe / Klasse / Konto; eindeutig (`scope`,`scope_ref`,`audience`) | **K:** `note` (Freitext, im Ist-Zustand unverschlüsselt, DAM-034) | Konfiguration; Regel mit `scope` = user wird mit dem Konto gelöscht | Z6b B3 |
| `security_settings` | Sicherheitseinstellungen der Schule als Schlüssel/Wert (JSON) | `updated_by` → `users` [N]; PK `key` | – | Konfiguration, keine Frist; Schlüsselliste [unklar] | Z6c §9 |
| `account_initial_passwords` | Kennzeichnet, dass das aktuelle Passwort ein Startpasswort mit Frist ist (nur Hash) | `user_id` → `users` [K] (PK); `created_by` → `users` [N] | **H:** `password_hash` (Kopie des Konto-Hashs, scrypt N = 2048) | Frist 14 Tage (1 bis 90); Zeile verschwindet beim Passwortwechsel und bei Kontolöschung | Z6b C2 |
| `letter_batches` | Kurzlebiger Stapel mit Zugangsdaten (Startpasswörter) für gedruckte Briefe | `created_by` → `users` [K] (Konto weg = Stapel weg); PK UUID | **V:** `data_enc` (Bindung `letter_batches:<id>`); **K:** `title`, `count` | 60 min (`SM_LETTER_BATCH_MINUTES`); danach Wartung bzw. nächster Zugriff (410) | Z6b C1 |

### 2.2 Rechte, Rollen, Schulzweige, Beobachtung (7 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `role_overrides` | Schulspezifische Abweichung vom Standard der Rollenrechte (Recht erteilt/entzogen, Umfang) | PK (`role`,`permission`); `role` = Grundrolle oder `custom_roles.id` (Präfix `x-`) ohne FK | **K:** `updated_by` (Name) | Konfiguration, keine Frist | Z6a §1.6 |
| `custom_roles` | Eigene Rollen der Schule (Name, Beschreibung, Grundtyp, Grundrolle, Vorlage) | PK `id` (Präfix `x-`); `base`, `template` ⇢ eingebaute Rolle; `users.custom_role` ⇢ `id`; Name eindeutig | – (`created_by` Kennung Klartext) | Konfiguration, keine Frist | Z6c §10 |
| `role_settings` | Legt fest, welche eingebauten Rollen ausgeblendet sind (`admin` nie; nur wenn kein Konto die Rolle hat) | PK `role` | – | Konfiguration | Z6c §11 |
| `branches` | Schulzweig bzw. Abteilung (Standorte, Klassenstufen, Klassen-IDs als JSON) | `class_ids` ⇢ Planungsdokument; Name eindeutig | – | Konfiguration | Z6a §1.7 |
| `user_branches` | Zuordnung Konto (Abteilungsleitung) ↔ Zweig | `user_id` → `users` [K]; `branch_id` → `branches` [K] | – | Kaskade | Z6a §1.8 |
| `account_watch` | Markiert Konten für verstärkte Protokollierung und sperrt ggf. die Vergabe von Admin-Rechten (`no_admin_grant`) | `user_id` → `users` [K] (PK) | **K:** `set_by` (Kennung) | mit Konto gelöscht; Datenart `watch_log` | Z6c §12 |
| `watch_log` | Protokoll jeder Anfrage beobachteter Konten (auch lesend) und der Anmeldeereignisse | `user_id` → `users` [N]; `username` bleibt | **V:** `query_enc`, `body_enc`, `changes_enc` (geschwärzt); **H:** `session_hash`; **K:** `username`, `ip`, `user_agent`, `path` | 180 Tage; 30 Tage nach Austritt; bei Kontolöschung sofort; nicht in der Selbstauskunft | Z6c §13 |

### 2.3 Schüler/innen, Eltern, Förderung (6 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `parent_links` | Verknüpfung eines Elternkontos mit einem Kind | `parent_user_id` → `users` [K]; `student_id` ⇢ Planungsdokument; eindeutig (`parent_user_id`,`student_id`) | **K:** `student_id` | `parents`: 30 Tage nach Austritt | Z6a §1.5 |
| `parent_access` | Je volljähriger Person und Bereich (kursraeume, krankmeldungen, dokumente, stundenplan, …): dürfen die Eltern sehen | `student_id` ⇢ Planungsdokument; `set_by` → `users` [N]; eindeutig (`student_id`,`area`) | **K:** `student_id` | `parents`: 30 Tage; fehlender Eintrag = nein | Z6b L1 |
| `student_prefs` | Wohin Schulinformationen einer volljährigen Person gehen (self/parents/both) und wann sie die Freigaben bewusst gespeichert hat | PK `student_id` ⇢ Planungsdokument | **K:** `student_id` | `parents`: 30 Tage | Z6b L2 |
| `student_documents` | Von Schüler/innen eingereichte Dokumente und Atteste; Datei verschlüsselt in der Dateiablage, bei Papier-Attest nur Vermerk | `student_id` ⇢; `absence_id` → `student_absences` [N]; `file_id` → `stored_files` [N]; `uploaded_by`, `handled_by` → `users` [N] | **V:** `title_enc`, `note_enc` (+ Datei); **K:** `uploaded_by_name`, `handled_by_name`, `withdrawn_by_name` | `documents`: 30 Tage nach Austritt, laufend 400 Tage; „zurückgezogen“ = archiviert, nie sofort hart gelöscht | Z6c §4 |
| `student_support` | Förderinformationen je Schüler/in (Nachteilsausgleich, Schulbegleitung, Förderplan, Sonstiges) mit Dokumenten | `student_id` ⇢; `catalog_id` ⇢ `support_catalog`; `file_ids` ⇢ `stored_files` | **V:** `title_enc`, `details_enc`, `aids_enc`; **K:** `student_id`, `created_by_name` | `support`: 30 Tage nach Austritt (mit Dateien) | Z6c §2 |
| `support_catalog` | Von der Schule gepflegter Katalog der Merkmale und Nachteilsausgleiche (11 Standardeinträge) | referenziert von `student_support.catalog_id` | – (keine Personendaten) | Konfiguration | Z6c §3 |

### 2.4 Fehlzeiten, Klassenbuch, Nachschreiben (5 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `student_absences` | Krankmeldung bzw. Fehlzeit einer Schülerin/eines Schülers (Art, Zeitraum, Stunden, Status, Entschuldigung) | `student_id` ⇢; `register_id` ⇢ `register_lessons`; `excused_by` ⇢ Konto-ID; `reported_by` → `users` [N] | **V:** `reason`, `note` (Gesundheitsdaten; Z6a: Klartext, Z3/Z6c: als Token gespeichert – im Neubau verschlüsselt, DAM-035); **K:** `student_id`, `excused_by_name`, `reported_by_name` | `absences`: 30 Tage nach Austritt, laufend 365 Tage | Z6a §1.12 |
| `student_absence_events` | Unveränderliche Zeitleiste jeder Fehlzeit: wer, wann, über welchen Kanal, jede Änderung vorher → nachher | `absence_id` ⇢ (kein FK, bleibt nach Löschen der Fehlzeit); `student_id` ⇢ | **K:** `actor_name`, `detail` (ohne Gründe, Vermerke, Diagnosen) | nur anhängen; mit `absences` gelöscht; bei Kontolöschung `actor_id` leer, `actor_name` = `gelöscht#<Konto-ID>` | Z6a §2.2 |
| `register_lessons` | Klassenbuch: eine Zeile je gehaltener Unterrichtsstunde (Thema, Hausaufgabe, Anwesenheit) | `course_id`, `lesson_id`, `teacher_id`, `class_ids` ⇢ Planungsdokument; `checked_by` ⇢; eindeutig (`date`,`lesson_id`,`period`,`part`) | **V:** `topic_enc`, `homework_enc`, `attendance_enc` (JSON `{Schüler-ID: {status, minutes}}`); **K:** `checked_by_name` | `attendance`: 365 Tage nach Austritt, **anonymisiert** (Eintrag der Person entfällt) | Z6c §1 |
| `exam_makeup_dates` | Termin zum Nachschreiben einer Klausur; mehrere Personen können denselben Termin teilen | `exam_id` ⇢ Planungsdokument; `created_by` → `users` [N] | **K:** `note` (Freitext, DAM-034), `created_by_name` | keine eigene Frist [Lücke] | Z6b G1 |
| `exam_makeups` | Je verpasster Klausur und Person ein Vorgang bis zum Nachschreiben (offen → angesetzt → erledigt/entfallen) | `exam_id`, `student_id`, `course_id` ⇢; `absence_id` ⇢ `student_absences`; `date_id` → `exam_makeup_dates` [N]; eindeutig (`exam_id`,`student_id`) | **K:** `student_id`, `waived_by_name`, `handled_by_name` | Teil der Datenart `absences` | Z6b G2 |

### 2.5 Noten und Klausurergebnisse (10 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `exam_results` | Note einer Person zu einer Klausur aus dem Planungsdokument | `exam_id`, `course_id`, `student_id` ⇢; eindeutig (`exam_id`,`student_id`) | **V:** `grade_enc`, `note_enc`; **K:** `student_id`, `graded_by_name` | `exam_results`: 180 Tage nach Austritt | Z6b A1 |
| `gb_config` | Schulweite Einstellungen des Notenbuchs (Schlüssel/Wert) | PK `key` | – | Konfiguration; Standardwerte [unklar] | Z6b A2 |
| `gb_books` | Notenbuch je Kursteil und Halbjahr (Skala, Rundung, Sperre) | `course_id` ⇢; eindeutig (`course_id`,`part`,`term`) | **K:** `locked_by_name` | Struktur ohne Schülerdaten | Z6b A3 |
| `gb_categories` | Leistungsarten eines Notenbuchs (verschachtelbar, mit Gewicht) | `book_id` → `gb_books` [K]; `parent_id` ⇢ | – | Kaskade mit Notenbuch | Z6b A4 |
| `gb_items` | Eine Leistung (Klausur, Test, Referat) als Spalte der Notentabelle | `book_id` → `gb_books` [K]; `category_id` ⇢ | – | Kaskade mit Notenbuch | Z6b A5 |
| `gb_entries` | Note bzw. Punkte einer Person bei einer Leistung | `item_id` → `gb_items` [K]; `student_id` ⇢; eindeutig (`item_id`,`student_id`) | **V:** `value_enc`, `note_enc`; **K:** `student_id`, `entered_by_name` | `gradebook`: 180 Tage nach Austritt | Z6b A6 |
| `gb_finals` | Von der Lehrkraft festgelegte Halbjahres-/Zeugnisnote je Person (der Vorschlag wird nie gespeichert) | `book_id` → `gb_books` [K]; `student_id` ⇢ | **V:** `value_enc`, `note_enc`; **K:** `student_id`, `set_by_name` | `gradebook`: 180 Tage | Z6b A7 |
| `gb_log` | Änderungsprotokoll des Notenbuchs (Wert vorher/nachher) | `book_id` ⇢ (kein FK, Protokoll bleibt erhalten); `item_id`, `student_id` ⇢ | **V:** `detail_enc`; **K:** `actor_name`, `student_id` | `gradebook`: 180 Tage | Z6b A8 |
| `gb_source_results` | Ergebnis aus einem anderen Bereich (Aufgabe, Selbsttest), das die Lehrkraft ins Notenbuch übernehmen kann | eindeutig (`source_type`,`source_id`,`student_id`) | **K:** `student_id`, `points`, `max_points`, `grade` (im Ist-Zustand **Klartext**, anders als `gb_entries`; DAM-036) | `gradebook`: 180 Tage | Z6b A9 |
| `gb_source_links` | Hält fest, ob eine Quelle in einem Notenbuch übernommen oder abgewählt wurde | `book_id` → `gb_books` [K]; `item_id` ⇢; eindeutig (`book_id`,`source_type`,`source_id`) | – | Kaskade mit Notenbuch | Z6b A10 |

### 2.6 Kompetenzen (8 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `comp_frameworks` | Kompetenzrahmen mit Stufen (schulweite Lehrplan-Inhalte, keine Personendaten) | Wurzel der `comp_*`-Kaskade | – | Konfiguration | Z6a §2.36 |
| `comp_areas` | Bereich innerhalb eines Kompetenzrahmens | `framework_id` → `comp_frameworks` [K] | – | Kaskade | Z6a §2.37 |
| `comp_competencies` | Einzelne Kompetenz („Ich kann …“) in einem Bereich | `framework_id` → `comp_frameworks` [K]; `area_id` → `comp_areas` [K] | – | Kaskade | Z6a §2.38 |
| `comp_assessments` | Lernstand einer Person zu einer Kompetenz; nur anhängend, der Verlauf bleibt | `student_id` ⇢; `competency_id` → `comp_competencies` [K] | **V:** `evidence_enc`, `comment_enc`; **K:** `student_id`, `by_name`, `confirmed_by` | `competencies`: 180 Tage nach Austritt | Z6a §2.39 |
| `comp_links` | Zuordnung eines Objekts (Aufgabe, Material) zu einer Kompetenz | `competency_id` → `comp_competencies` [K]; `item_type`, `item_id` ⇢ generisch; eindeutig (`competency_id`,`item_type`,`item_id`) | – | Kaskade mit Kompetenz | Z6a §2.40 |
| `comp_plans` | Lern- bzw. Wochenplan je Schüler/in | `student_id` ⇢; `competency_id` → `comp_competencies` [N] | **V:** `title_enc`, `note_enc`; **K:** `student_id` | `competencies`: 180 Tage | Z6a §2.41 |
| `comp_badges` | Definition eines Abzeichens (Name, Symbol, Farbe, Vergaberegel) | Wurzel für `comp_badge_awards` | – | Konfiguration | Z6a §2.42 |
| `comp_badge_awards` | Vergabe eines Abzeichens an eine Schülerin/einen Schüler | `badge_id` → `comp_badges` [K]; `student_id` ⇢; eindeutig (`badge_id`,`student_id`) | **V:** `note_enc`; **K:** `student_id`, `awarded_by_name` | `competencies`: 180 Tage | Z6a §2.43 |

### 2.7 Kursräume, Aufgaben, Lernfortschritt (19 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `channels` | Kanal (Kursraum) eines Kursteils (`ref` = „Kurs#Teil“), einer Klasse oder frei angelegt; Behälter für Material, Aufgaben, Abgaben, Pinnwand | `created_by` → `users` [N]; `ref` ⇢ Kurs/Klasse im Planungsdokument; **Kaskade-Wurzel** aller kanalbezogenen Tabellen; eindeutig (`kind`,`ref`) | – | Kaskade zu allen Kind-Tabellen | Z6a §2.18 |
| `channel_extra_members` | Zusätzliches Mitglied eines Kanals (z. B. Referendar/in); Anlage nur mit `channels.manage` ohne Einschränkung | `channel_id` → `channels` [K]; `user_id` → `users` [K]; `added_by` → `users` [N] | – | `progress`: 90 Tage nach Austritt | Z6a §2.19 |
| `channel_folders` | Verschachtelte Ordner mit eigener Freigabe und Papierkorb-Markierung | `channel_id` → `channels` [K]; `parent_id` → `channel_folders` [K]; `created_by` → `users` [N]; `lesson_id` ⇢ | – | Papierkorb 30 Tage (1 bis 365); nicht als Datenart geführt [Lücke] | Z6a §2.20 |
| `channel_items` | Material (Datei, Link, Textseite) oder Aufgabe in einem Kanal | `channel_id` → `channels` [K]; `folder_id` → `channel_folders` [K]; `file_id` → `stored_files` [N]; `attachment_ids` ⇢ `stored_files`; `created_by` → `users` [N] | **V:** `body_enc` (Markdown) | Papierkorb 30 Tage; nicht als Datenart geführt [Lücke] | Z6a §2.21 |
| `assignment_settings` | Einstellungen einer Aufgabe (Gruppenabgabe, Punkte, Notenschlüssel, Bewertungsraster als Kopie der Vorlage, Elternsicht) | `item_id` → `channel_items` [K] (1:1, eindeutig); `group_set_id` → `channel_group_sets` [N]; `template_id` → `grading_templates` [N] | **V:** `rubric_enc` | Kaskade mit Aufgabe | Z6a §2.11 |
| `assignment_submissions` | Aktuelle Abgabe einer Schülerin/eines Schülers zu einer Aufgabe (bei Gruppenabgabe eine Zeile je Mitglied) | `item_id` → `channel_items` [K]; `student_user_id` → `users` [K]; `student_id`, `group_id` ⇢; `feedback_by` → `users` [N]; eindeutig (`item_id`,`student_user_id`) | **V:** `text_enc`, `feedback_enc`, `grade_enc`, `rubric_enc` | `submissions`: 90 Tage nach Austritt | Z6a §2.22 |
| `assignment_submission_versions` | Frühere Fassungen einer Abgabe mit Rückmeldung (nach angeforderter Überarbeitung) | `submission_id` → `assignment_submissions` [K]; eindeutig (`submission_id`,`attempt`) | **V:** `text_enc`, `feedback_enc`, `grade_enc`, `rubric_enc` | `submissions`: 90 Tage | Z6a §2.13 |
| `assignment_extensions` | Verlängerte Abgabefrist für eine Person oder eine Gruppe | `item_id` → `channel_items` [K]; `user_id` → `users` [K]; `group_id` → `channel_groups` [K]; `created_by` → `users` [N] | **V:** `reason_enc` | `progress`: 90 Tage | Z6a §2.12 |
| `grading_templates` | Wiederverwendbare Bewertungsvorlage (Raster oder Leitfaden) einer Lehrkraft | `owner_user_id` → `users` [K] | **V:** `criteria_enc` | Kaskade mit Konto; keine Datenart | Z6a §2.10 |
| `channel_group_sets` | Gruppeneinteilung eines Kursraums (z. B. Projektgruppen, Niveaustufen) | `channel_id` → `channels` [K]; `created_by` → `users` [N] | – | Kaskade mit Kursraum | Z6a §2.14 |
| `channel_groups` | Gruppe innerhalb einer Einteilung | `channel_id` → `channels` [K]; `set_id` → `channel_group_sets` [K] | – | Kaskade | Z6a §2.15 |
| `channel_group_members` | Zuordnung einer Schülerin/eines Schülers zu einer Gruppe (je Einteilung höchstens eine) | `channel_id`, `set_id`, `group_id` [K]; `user_id` → `users` [K]; eindeutig (`set_id`,`user_id`) | – | `progress`: 90 Tage | Z6a §2.16 |
| `channel_group_gates` | Material oder Ordner ist nur für Mitglieder bestimmter Gruppen sichtbar | `group_id` → `channel_groups` [K]; `item_id` → `channel_items` [K]; `folder_id` → `channel_folders` [K]; „genau eines von item/folder“ wird nicht erzwungen (DAM-065) | – | Kaskade | Z6a §2.17 |
| `channel_posts` | Pinnwandbeitrag bzw. Antwort (nur eine Ebene) | `channel_id` → `channels` [K]; `parent_id` → `channel_posts` [K]; `author_id` → `users` [N] | **V:** `body_enc`; **K:** `author_name` | weiches Löschen (`deleted_at`); nicht als Datenart geführt [Lücke] | Z6a §2.23 |
| `channel_reads` | Letzter Besuch eines Kontos in einem Kanal (Markierung „neu“) | `channel_id` → `channels` [K]; `user_id` → `users` [K]; eindeutig (`channel_id`,`user_id`) | – | `progress`: 90 Tage | Z6a §2.24 |
| `channel_item_views` | Material, das ein Konto bereits geöffnet hat | `item_id` → `channel_items` [K]; `user_id` → `users` [K]; eindeutig (`item_id`,`user_id`) | – | `progress`: 90 Tage | Z6a §2.25 |
| `completion_rules` | Abschlussbedingung eines Elements (manual, viewed, submitted, graded, passed) | `channel_id` → `channels` [K]; `element_type`/`element_id` ⇢ generisch; `created_by` → `users` [N] | – | Kaskade mit Kursraum; bei endgültig gelöschtem Element per Logik entfernt | Z6b O1 |
| `completion_marks` | Manuelles „Erledigt“-Häkchen einer Person | `channel_id` → `channels` [K]; `user_id` → `users` [K]; `element_*` ⇢ generisch | – | `progress`: 90 Tage | Z6b O2 |
| `availability_rules` | Bedingte Freigabe: Element nur verfügbar, wenn ein verschachtelter UND/ODER-Baum erfüllt ist | `channel_id` → `channels` [K]; `element_*` ⇢ generisch; `created_by` → `users` [N] | – | Kaskade mit Kursraum | Z6b O3 |

### 2.8 Lernaktivitäten (10 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `learning_polls` | Abstimmung im Kursraum oder an einer Chat-Nachricht | `channel_id` → `channels` [K] (leer bei Chat-Abstimmung); `chat_id`, `chat_message_id` ⇢ (eindeutig `chat_message_id`); `created_by` → `users` [N] | **V:** `question_enc`, `options_enc` (bei Chat-Abstimmung steht die Frage nur Ende-zu-Ende in der Nachricht) | Kaskade mit Kursraum | Z6b F1 |
| `learning_poll_participants` | Stellt sicher, dass jede Person nur einmal abstimmt; bei anonymen Abstimmungen ohne Personenbezug | `poll_id` → `learning_polls` [K]; `user_id` → `users` [K] (nur namentlich); eindeutig (`poll_id`,`user_id`) und (`poll_id`,`token`) | **H:** `token` (HMAC aus Server-Geheimnis, Abstimmung, Konto) | `learning`: 90 Tage | Z6b F2 |
| `learning_poll_votes` | Stimme einer namentlichen Abstimmung (Person, gewählte Antwort); anonym: nichts | `poll_id` [K]; `user_id` → `users` [K]; eindeutig (`poll_id`,`user_id`,`option_index`) | – | `learning`: 90 Tage | Z6b F3 |
| `learning_poll_tally` | Stimmzähler je Antwort bei anonymen Abstimmungen, ohne Personenbezug | `poll_id` → `learning_polls` [K]; eindeutig (`poll_id`,`option_index`) | – | Kaskade | Z6b F4 |
| `learning_surveys` | Fragebogen im Kursraum, anonym oder namentlich | `channel_id` → `channels` [K]; `created_by` → `users` [N] | **V:** `intro_enc` | Kaskade mit Kursraum | Z6b F5 |
| `learning_survey_responses` | Antworten zu einer Umfrage; bei anonymen Umfragen ohne `user_id`, Zeitpunkt nur als Tagesdatum | `survey_id` → `learning_surveys` [K]; `user_id` → `users` [K] (NULL bei anonym) | **V:** `answers_enc` | `learning`: 90 Tage; anonyme Antworten bleiben | Z6b F6 |
| `learning_survey_participants` | Verhindert Doppelabgaben bei Umfragen | `survey_id` [K]; `user_id` → `users` [K] (nur namentlich); eindeutig (`survey_id`,`user_id`) und (`survey_id`,`token`) | `token` gegen Doppelabgaben (Bildung [unklar]) | `learning`: 90 Tage | Z6b F7 |
| `learning_questions` | Fragensammlung eines Kursraums; Frage samt Lösung verschlüsselt | `channel_id` → `channels` [K]; `created_by` → `users` [N] | **V:** `data_enc`; **K:** `category` | Kaskade mit Kursraum | Z6b F8 |
| `learning_selftests` | Test mit Fragenauswahl, Versuchen, Zeitlimit, Mischung, Rückmeldung | `channel_id` → `channels` [K]; `question_ids` ⇢ `learning_questions` | **V:** `description_enc` | Kaskade mit Kursraum | Z6b F9 |
| `learning_attempts` | Ein Versuch einer Person mit Fragenabbild zum Start, Antworten und Ergebnis (höchstens ein laufender Versuch je Test und Konto) | `test_id` → `learning_selftests` [K]; `user_id` → `users` [K]; eindeutig (`test_id`,`user_id`,`number`) | **V:** `snapshot_enc`, `answers_enc`, `result_enc`; **K:** `points`, `max_points`, `percent` (bewusst Klartext für Notenbuch und Abschlussbedingung) | `learning`: 90 Tage | Z6b F10 |

### 2.9 Postfach (9 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `conversations` | Unterhaltung im internen Postfach: direkt, Gruppe oder Rundschreiben; optional mit externen E-Mail-Beteiligten | `created_by` → `users` [N]; `parent_id` → `conversations` [N]; `mail_account_id` ⇢ `mail_accounts` (kein FK, Löschverhalten [unklar]); `migrated_chat_id` ⇢ `chats` | **V:** `subject_enc`; **K:** `external` (E-Mail-Adressen und Namen externer Beteiligter, JSON), `audience` (nur Bezeichnungen) | `messages`: leere Unterhaltungen werden entfernt | Z6b I1 |
| `conversation_participants` | Lesestand, Archiv, Stummschaltung, „für mich gelöscht“, Empfängerrolle (to/cc/bcc) je Konto und Unterhaltung | `conversation_id` → `conversations` [K]; `user_id` → `users` [K] (PK beide) | – | `messages`: 30 Tage nach Austritt | Z6b I2 |
| `messages` | Nachricht innerhalb einer Unterhaltung, mit Anhängen und Zustellstatus bei externen Adressen | `conversation_id` → `conversations` [K]; `sender_id`, `removed_by` → `users` [N]; `attachment_ids` ⇢ `stored_files` | **V:** `body_enc` (Bindung `messages.body:<conversation_id>:<message_id>`); **K:** `external_from`, `external_name`, `mail_message_id` | `messages`: 30 Tage nach Austritt; laufend 365 Tage (`messaging_retention_days`, 0 = nie); offen gemeldete ausgenommen | Z6b I3 |
| `message_reports` | Meldung einer Nachricht an die Moderation mit Bearbeitung und Maßnahmen | `message_id` → `messages` [K]; `reporter_id`, `handled_by` → `users` [N] | **V:** `reason_enc`, `resolution_enc` | abgeschlossene Meldungen älter als die Postfach-Frist gelöscht | Z6b I4 |
| `user_blocks` | Eine Person nimmt keine Nachrichten einer blockierten Person mehr an | `user_id`, `blocked_user_id` → `users` [K] (PK beide) | – | `messages`: 30 Tage nach Austritt | Z6b I5 |
| `message_user_settings` | E-Mail-Hinweis-Einstellung je Konto und Postfach-Sperre durch die Moderation | `user_id` → `users` [K] (PK); `suspended_by` → `users` [N] | **V:** `suspension_reason_enc` (Bindung `…:<user_id>`) | `messages`: 30 Tage nach Austritt; abgelaufene Sperren werden beendet | Z6b I6 |
| `message_drafts` | Entwurf einer neuen Nachricht oder Antwort | `user_id` → `users` [K]; `conversation_id` → `conversations` [K] | **V:** `data_enc` (Bindung `message_drafts.data:<user_id>:<draft_id>`) | `messages`: mit der Datenart gelöscht | Z6b I7 |
| `mail_accounts` | Externes E-Mail-Konto, über das Nachrichten an externe Adressen versendet und eingehende Mails geholt werden | `user_id` → `users` [K]; eindeutig (`user_id`,`email`) | **V:** `secret_enc` (App-Passwort bzw. OAuth-Token als JSON); **K:** `email`, `display_name`, `username`, `imap_host`, `smtp_host`, `last_error` | Kaskade mit Konto; keine eigene Datenart [Lücke] | Z6b H1 |
| `send_idempotency` | Doppelsende-Schutz: eine Wiederholung liefert die bereits gesendete Nachricht | `user_id` → `users` [K]; PK (`user_id`,`scope`,`key`); `ref` ⇢ Nachrichten-/Unterhaltungs-ID | – (keine Inhalte) | Aufbewahrungsdauer [unklar]; Bereinigung über `created_at` | Z6b D1 |

### 2.10 Chats (10 Tabellen)

Alle Chat-Tabellen haben im Ist-Zustand **keine Fremdschlüssel** (Regel DAM-064). Löschung: Datenart `chats`, 30 Tage nach Austritt (Kapitel 1.10). Server-seitig sichtbar sind nur Chiffrat, Nonce, öffentliche Schlüssel, Zähler und Verweise.

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `chats` | Einzel-, Gruppen- oder Klassenchat | `created_by` ⇢ Konto; eindeutig `direct_key` | **V:** `title_enc` (serverseitig, damit neue Geräte den Namen anzeigen können) | Einzelchats ganz entfernt; Gruppen ohne Mitglieder entfernt | Z6a §2.29 |
| `chat_members` | Mitgliedschaft mit Lese-, Stummschalt-, Archiv- und Schreibstatus | `chat_id`, `user_id` ⇢; eindeutig (`chat_id`,`user_id`) | – | `chats` | Z6a §2.30 |
| `chat_messages` | Verschlüsselte Chat-Nachricht; der Server speichert nur das Chiffrat | `chat_id`, `sender_id`, `sender_device_id`, `reply_to` ⇢ | **E2E:** `ciphertext`, `nonce`; **V:** `legacy_body_enc` (nur Altbestand); **K:** `system_text` (Systemhinweis, kein Nutzerinhalt) | `chats`; Verbleib des Chiffrats nach `deleted_at` [unklar] | Z6a §2.31 |
| `chat_message_keys` | Nachrichtenschlüssel, verpackt für ein Gerät des Empfängers | `message_id`, `device_id`, `wrapper_device_id` ⇢; eindeutig (`message_id`,`device_id`) | **E2E:** `wrapped`, `nonce` | `chats` | Z6a §2.32 |
| `chat_devices` | Gerät eines Kontos bzw. Wiederherstellungsschlüssel mit öffentlichem Schlüssel | `user_id` ⇢ | `public_key` (X25519, kein Geheimnis) | `chats` | Z6a §2.26 |
| `chat_link_requests` | Anfrage eines neuen Geräts, den Verlauf von einem eingerichteten Gerät zu erhalten (Freigabe nach Fingerabdruck-Vergleich) | `user_id`, `device_id`, `approved_by_device_id` ⇢ | – (`code` kurzlebig) | `chats`; Gültigkeit [unklar] | Z6a §2.27 |
| `chat_key_backups` | Optionales Backup des privaten Archivschlüssels, im Browser verschlüsselt | PK `user_id` ⇢; `archive_device_id` ⇢ | **E2E:** `blob` (aus Passwort bzw. Code im Browser abgeleitet) | `chats` | Z6a §2.28 |
| `chat_attachments` | Bild oder GIF einer Nachricht als im Browser verschlüsseltes Blob | PK `id` (32 Zeichen); `chat_id`, `uploader_id`, `message_id` ⇢ | **E2E:** `data` (Server kennt Inhalt und Typ nicht) | lose Uploads 24 h; sonst `chats` | Z6a §2.34 |
| `chat_reports` | Meldung einer Chat-Nachricht durch ein Mitglied (Klartext und Bild freiwillig mitgeschickt) | `chat_id`, `message_id`, `reporter_id`, `sender_id`, `resolved_by` ⇢ | **V:** `reason_enc`, `content_enc` (serverseitig) | `chats` (als Melder oder Absender) | Z6a §2.33 |
| `chat_report_images` | Bild, das die meldende Person für die Moderation mitschickt | `report_id` ⇢ | **V:** `data_enc` (Binär; Bindung `chat_report_images.data:<id>`) | `chats` | Z6a §2.35 |

### 2.11 Benachrichtigungen und Mitteilungen (7 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `notifications` | Eine Benachrichtigung für genau ein Konto (Titel und Text ohne sensible Einzelheiten) | `user_id` → `users` [K]; `student_id`, `ref` ⇢; eindeutig (`user_id`,`dedupe_key`) | **V:** `title_enc`, `body_enc`; **K:** `student_id`, `link` | `notifications`: 30 Tage nach Austritt; laufend 90 Tage (7 bis 730) | Z6b J1 |
| `notification_prefs` | Versandweg (aus/app/mail) je Konto und Ereignisart | `user_id` → `users` [K]; eindeutig (`user_id`,`kind`) | – | `notifications`: 30 Tage | Z6b J2 |
| `notification_user_settings` | Tageszusammenfassung und Ruhezeit je Konto (Ruhezeit gilt nur für E-Mails; Standard 21:00–07:00) | `user_id` → `users` [K] (PK) | – | `notifications`: 30 Tage | Z6b J3 |
| `notification_school` | Schulweiter Standard-Modus je Ereignisart; kann für Konten gesperrt werden (`locked`) | PK `kind` | – | Konfiguration | Z6b J4 |
| `notification_config` | Schuleinstellungen der Benachrichtigungen (z. B. `retention_days`) | PK `key` | – | Konfiguration | Z6b J5 |
| `notifications_outbox` | Warteschlange ausgehender Benachrichtigungen (Webhook oder E-Mail) mit Wiederholungen | `dedupe_key` gegen Doppelte | **V:** `payload` (E-Mail-Text; Webhook-JSON im Klartext); **K:** `target` (URL bzw. E-Mail-Adresse), `subject` | Inhalt nach Zustellung geleert; Frist der Zeilen [unklar] | Z6a §1.13 |
| `announcements` | Mitteilung für eine Zielgruppe (all/staff/classes) mit Gültigkeitszeitraum | `author_id` → `users` [N]; `class_ids` ⇢ Planungsdokument | **K:** `title`, `body`, `author_name` (im Ist-Zustand Klartext, DAM-034) | Verfasser wird bei Kontolöschung pseudonymisiert; sonst keine Frist [Lücke] | Z6a §1.11 |

### 2.12 Formulare (4 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `form_templates` | Formularvorlage einer Schule mit Status (entwurf/aktiv/archiviert) und aktueller Version | `created_by` → `users` [N]; Wurzel für Versionen und Einreichungen | **K:** `created_by_name` | Konfiguration | Z6a §2.6 |
| `form_versions` | Unveränderliche Fassung einer Vorlage; Einreichungen bleiben bei ihrer Fassung | `template_id` → `form_templates` [K]; eindeutig (`template_id`,`version`) | – | Kaskade | Z6a §2.7 |
| `form_submissions` | Einreichung zu einem Formular: Antworten, Schritt, Status, Entscheidung, Fälligkeit | `template_id` [K]; `version_id` → `form_versions` [K]; `student_id`, `class_id` ⇢; `submitted_by` → `users` [N] | **V:** `answers_enc`, `decision_note_enc`; **K:** `submitted_by_name`, `decided_by_name` | `forms`: 90 Tage nach Austritt; abgeschlossene 400 Tage | Z6a §2.8 |
| `form_events` | Verlauf einer Einreichung (eingereicht, geprüft, genehmigt, abgelehnt, Scan, Erinnerung) | `submission_id` → `form_submissions` [K]; `actor_id` → `users` [N] | **V:** `note_enc`; **K:** `actor_name` | `forms`; Kaskade mit Einreichung | Z6a §2.9 |

### 2.13 Planung, Versionen, Lehrkraft-Anträge (6 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `school_versions` | Versionen (Stände) des Planungsdokuments; Grundlage von Verlauf, Rückgängig und Wiederherstellung | `user_id` → `users` [N]; `restored_from` ⇢ Version | **V:** `data` (zlib, dann AES-256-GCM; Bindung `school_versions.data:<id>`) | 300 Versionen; `history`: Person nach 30 Tagen aus allen Versionen entfernt | Z6a §1.10 |
| `plan_proposals` | Vorschlagspaket der Plan-Prüfung (Anlass, Problemliste, Lösungsvarianten) | `decided_by_id`, `chosen_variant_id` ⇢ (Nachweis bleibt) | **H:** `state_hash`; **K:** `decided_by` (Name), `decision_note` (Freitext, DAM-034) | keine Frist [Lücke] | Z6b M1 |
| `plan_proposal_variants` | Eine zur Wahl stehende Lösung mit Kennzahlen vorher/nachher, Änderungsliste und Unterschied zum Plan | `package_id` → `plan_proposals` [K] | – | Kaskade | Z6b M2 |
| `plan_proposal_log` | Unveränderlicher Verlauf (nur anhängen): erzeugt, ersetzt, später, angenommen, verworfen, informiert | `package_id` ⇢ (kein FK, Verlauf bleibt); `actor_id`, `variant_id` ⇢ | **K:** `actor_name`, `note` (DAM-034) | keine Frist [Lücke] | Z6b M3 |
| `plan_snapshots` | Gespeicherter, benannter Plan-Stand (nur Unterrichtsblöcke), optional je Planzeitraum | `user_id` → `users` [N]; `period` ⇢ `settings.plan_periods` | **K:** `user_name`; `data` zlib-komprimiert und im Ist-Zustand **nicht verschlüsselt** (DAM-024) | bis zum Löschen; keine Frist [Lücke] | Z6b N1 |
| `teacher_change_requests` | Anträge von Lehrkräften auf Änderung ihres Profils (Fächer, Klassenwünsche, Stunden, Zeitfenster) oder auf eine einmalige Ausnahme | `teacher_id` ⇢; `user_id`, `reviewer_id` → `users` [N] | **V:** `note_enc`, `review_comment_enc` (AAD `teacher_change_requests:<id>:<feld>`); **K:** `payload` (JSON mit `wishes`/`reason` als Freitext, DAM-034) | in der Auskunft enthalten, aber keine Löschregel [Lücke] | Z6c §5 |

### 2.14 Datenschutz und Dateiablage (4 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `retention_settings` | Einstellungen des Löschkonzepts (Fristen in Tagen, Schalter) | PK `key` | – | Konfiguration; Schlüsselliste [unklar] | Z6c §6 |
| `retention_leavers` | Warteliste ausgeschiedener Personen bis zur Bereinigung ihrer Daten | `student_id` ⇢ (eindeutig); `class_id` ⇢ | **V:** `name_enc` (beim Abschluss geleert) | erledigte Einträge 1095 Tage nach Abschluss | Z6c §7 |
| `retention_log` | Löschprotokoll: welche Datenart wann für wen wie viele Datensätze gelöscht/anonymisiert wurde, ohne Inhalte | kein FK; `subject` = `student:<ID>` / `user:<ID>` | – (nur IDs) | 1095 Tage | Z6c §8 |
| `stored_files` | Metadaten verschlüsselt abgelegter Dateien (Inhalt liegt verschlüsselt im Dateispeicher) | PK UUID; `owner_user_id` → `users` [N]; `ref_type`/`ref_id` ⇢ Bezugsobjekt (Grundlage der Zugriffsprüfung) | **V:** `filename` (Bindung `stored_files.filename:<id>`) und Inhalt (`SMS1`); **H:** `sha256` (Prüfsumme des Klartexts) | Uploads ohne Anhang 24 h; weich gelöscht 30 Tage; `files`: 30 Tage nach Austritt | Z6a §2.5 |

### 2.15 Integrationen und API (4 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `api_tokens` | API-Zugang eines Kontos: persönliches Token (alle Rechte des Kontos) oder Zugang mit eingeschränktem Umfang (öffentliche API) | `user_id` → `users` [K]; eindeutig `token_hash`; `prefix` `smt_` (persönlich) bzw. `sma_` (mit Umfang) | **H:** `token_hash` (HMAC-SHA256); Klartext nie gespeichert | ohne Umfang: sofort nach Ablauf; mit Umfang: 30 Tage nach Ablauf | Z6a §1.3 |
| `api_token_log` | Nutzungsprotokoll je Anfrage: Zeit, Methode, Pfad ohne Abfrageparameter und Geheimnisse, Bereich, Ergebnis, Status, Dauer, IP | `token_id` → `api_tokens` [K] | **K:** `ip`, `path` (keine Antwortinhalte, keine Personendaten) | `api_log`: 90 Tage; 30 Tage nach Austritt; Obergrenze je Zugang [unklar] | Z6a §2.1 |
| `import_runs` | Protokoll jedes echten Imports aus einem Fremdsystem (Trockenläufe werden nicht gespeichert) | `user_id` → `users` [N] | **V:** `report_enc` (Bericht mit Namen); **H:** `source_hash`; **K:** `source_name`, `user_name`, `undone_by` | keine Frist [Lücke] | Z6b E1 |
| `import_links` | Ordnet Elemente des Quellsystems den angelegten Zielobjekten zu (keine Dubletten, Rücknahme) | `created_run`, `updated_run` → `import_runs` [N]; `target_id` ⇢; eindeutig (`system`,`instance`,`kind`,`source_key`) | `fingerprint` (Hash, Form [unklar]) | keine Frist [Lücke] | Z6b E2 |

### 2.16 Betrieb und Protokolle (3 Tabellen)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Anhang |
|---|---|---|---|---|---|
| `audit_log` | Protokoll von Verwaltungs- und Sicherheitsaktionen (ohne Inhalte) | `user_id` → `users` [N] | **K:** `username`, `target`, `ip`, `details` (JSON, nur was der Aufrufer übergibt) | 365 Tage (`audit_days`; 0 = nie); bei Kontolöschung pseudonymisiert | Z6a §1.9 |
| `error_log` | Fehlerprotokoll für die Administration (nur ERROR und CRITICAL) | kein FK | `message` (gekürzt, höchstens 2000 Zeichen), `path` (ohne Abfrage, Kennungen maskiert), `trace` (höchstens 8000 Zeichen) | 30 Tage, höchstens 1000 Zeilen | Z6b K2 |
| `system_state` | Schlüssel/Wert-Ablage für Systemzustand (`setup`, `school_profile`, `yearchange`, `maintenance`, Leader-Pacht) | PK `key` | – (keine Freitexte über Personen) | Zustand, keine Frist | Z6b K1 |

### 2.17 Anbieter-Lizenzserver (13 Tabellen, nur beim Anbieter)

Diese Tabellen gehören **nicht** zur Schul-Instanz. Eine Spaltenliste liegt im Anhang nicht vor (Z6 deckt nur die Schul-Instanz ab); Spalten werden nur genannt, wo die Quelle sie erwähnt. Fachliche Beschreibung in der Betriebs- und Lizenz-Datei.

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung |
|---|---|---|---|---|
| `schools` | Schulen als Kunden des Anbieters mit Status und Servern | Wurzel | – | [unklar] |
| `license_keys` | Lizenzschlüssel je Schul-Server (Platznummer = Position in der Schule, 1-basiert) | `schools` | **H:** `key_hash` (Prüfwert); **V:** `key_enc` (verschlüsselte Anzeige-Kopie, Schlüssel im Datenordner oder `LZ_KEY_STORE_KEY`); Klartext-Schlüssel nie in der Datenbank | [unklar] |
| `key_events` | Ereignisprotokoll zu Lizenzschlüsseln, einschließlich jeder Anzeige | `license_keys` | – | [unklar] |
| `licenses` | Altbestand früherer Lizenzen, aus dem die Schlüssel übernommen werden | – | – | [unklar] |
| `plans` | Tarife (Abo-Pläne) mit Intervall und Preisregeln | – | – | [unklar] |
| `school_billing` | Abrechnungsstand je Schule (Tarif, Abo-Ende, Zahlungsart, Verlängerung, Pausieren) | `schools`, `plans` | – | [unklar] |
| `payments` | Zahlungen je Schule mit Betrag, Status und Kennung des Zahlungsanbieters (doppelte Meldungen werden anhand der Anbieter-Kennung ignoriert) | `schools` | – | Aufbewahrungsfrist der Zahlungen offen |
| `upd_releases` | Freigegebene, signierte Versionen (Version, Kanal, Image-Verweis mit Digest, Prüfsumme, Signatur) | – | – | [unklar] |
| `upd_rollouts` | Rollout-Pläne mit Wellen, Zeitfenster und Status | `upd_releases` | – | [unklar] |
| `upd_appointments` | Update-Termine je Schule oder Server | `schools` | – | [unklar] |
| `upd_nodes` | Update-Knoten je Server mit zuletzt gemeldetem Stand | `schools` | – | [unklar] |
| `upd_events` | Ereignisprotokoll der Update-Verwaltung | – | – | [unklar] |
| `upd_school_settings` | Update-Einstellungen je Schule, u. a. das Zeitfenster | `schools` | – | [unklar] |

### 2.18 Sammlungen des Planungsdokuments (kein Tabellen-, sondern Dokumentinhalt)

Spaltenweise Definition: Anhang Z7 §2. Alle Sammlungen liegen in der verschlüsselten Nutzlast von `school_versions`.

| Sammlung | Zweck | Wichtigste Verweise | Personenbezug | Anhang |
|---|---|---|---|---|
| `settings` (genau eine Einstellungsgruppe) | Raster, Pausen, Ferien-/Schuljahr-Optionen, Gewichte des Generators (`weights`), Vertretungsregeln (`policy`), Planzeiträume (`plan_periods`), Fristen mit Datenschutzwirkung | `plan_periods[].id` ← `lessons.period` | `webhooks` (Adressen der Schule), `sick_phone` | Z7 §2.1–2.3 |
| `sites` | Standorte | ← Lehrkräfte, Räume, Klassen, Aufsichtsbereiche, Wegezeiten | – | Z7 §2.5 |
| `subjects` | Fächer (Raumtyp, Hauptfach, Höchstzahl je Tag, Farbe) | ← Lehrkräfte, Stundentafeln, Kursteile | – | Z7 §2.6 |
| `teachers` | Lehrkräfte (Kürzel als Kennung, Fächer, Deputat, Sperrzeiten, Wünsche, Zeitfenster, Pendelregeln) | `subjects`, `sites`; ← Kursteile, Aufsichten, Abwesenheiten, Vertretungen, `users.teacher_id` | Name, E-Mail | Z7 §2.7 |
| `rooms` | Räume (Typ, Standort, Kapazität) | `site`; ← Klassen (`home_room`), Kursteile, Blöcke | – | Z7 §2.8 |
| `classes` | Klassen (Klassenstufe, Standort, Stammraum, Klassenleitung, Unterrichtstage, Sperrzeiten, Klausurgrenzen, Jahrgang) | `home_room`, `class_teacher`, `profile`; ← Kurse, Schüler, Termine | – | Z7 §2.9 |
| `students` | Schüler/innen (Kennung, Stammklasse, Kurswahl, optional Geburtsdatum) | `class_id`, `courses`; ← alle Tabellen mit `student_id` | Name, Geburtsdatum | Z7 §2.10 |
| `curricula` | Stundentafeln (Fächer mit Wochenstunden, Ableitung von einer Basis) | `entries[].subject`, `base` | – | Z7 §2.11–2.12 |
| `grade_profiles` | Jahrgänge/Profile (bestimmen die Stundentafel) | `curriculum`; ← `classes.profile` | – | Z7 §2.13 |
| `courses` | Kurse (Unterricht, `hours`-mal je Woche; Kopplung über mehrere Klassen oder Teile) | `classes`, `parts[]` (Fach, Lehrkraft, Raum, Schüler); ← Blöcke, Klausuren, Abwesenheiten | – | Z7 §2.14–2.15 |
| `lessons` | Blöcke im Stundenplan (Tag, Start, Länge, Wochenangabe, Räume je Kursteil, fixiert, Planzeitraum) | `course_id` | – | Z7 §2.16 |
| `absences` | Abwesenheiten von Lehrkraft, Klasse, Raum oder Unterricht (Zeitraum, Stunden, Grund) | `ref` (Lehrkraft/Klasse/Raum oder `Kurs#Teil`) | Grund (`reason`, intern, nie öffentlich) | Z7 §2.17 |
| `overrides` | Vertretungs-Entscheidungen je Tag und Stunde (substitute, cancel, keep, room) | `lesson_id`, `teacher`, `room` | – | Z7 §2.18 |
| `holidays` | Ferien, Feiertage, bewegliche und schulfreie Tage (auch aus automatischem Import) | – | – | Z7 §2.19 |
| `areas` | Aufsichtsbereiche (Ort, Standort, benötigte Aufsichten je Pause) | `site` | – | Z7 §2.20 |
| `duties` | Pausenaufsichten (Bereich, Tag, Pause, Lehrkraft, Wochen) | `area`, `teacher`, `break_index` | – | Z7 §2.21 |
| `exams` | Klassenarbeiten und Klausuren (Kurs, Datum, Stunde, Dauer, Raum, Art) | `course_id`, `room`; ← `exam_results`, `exam_makeups`, `exam_makeup_dates` | – | Z7 §2.23 |
| `events` | Schulkalender-Termine (Zeitraum, Klassen/Klassenstufen, teilnehmende Lehrkräfte) | `classes`, `teachers` | – | Z7 §2.22 |
| `monitors` (optional) | Vertretungsmonitore je Standort (Einstellungen) | Standort-Kennung (leer = alle) | – | Z7 §2.24 |
| `holiday_import` (optional) | Einstellungen des automatischen Ferien-Imports | – | – | Z7 §2.24 |

### 2.19 Zählkontrolle

| Gruppe | Kapitel | Tabellen |
|---|---|---|
| Konten, Sitzungen, Anmeldung | 2.1 | 11 |
| Rechte, Rollen, Schulzweige, Beobachtung | 2.2 | 7 |
| Schüler/innen, Eltern, Förderung | 2.3 | 6 |
| Fehlzeiten, Klassenbuch, Nachschreiben | 2.4 | 5 |
| Noten und Klausurergebnisse | 2.5 | 10 |
| Kompetenzen | 2.6 | 8 |
| Kursräume, Aufgaben, Lernfortschritt | 2.7 | 19 |
| Lernaktivitäten | 2.8 | 10 |
| Postfach | 2.9 | 9 |
| Chats | 2.10 | 10 |
| Benachrichtigungen und Mitteilungen | 2.11 | 7 |
| Formulare | 2.12 | 4 |
| Planung, Versionen, Lehrkraft-Anträge | 2.13 | 6 |
| Datenschutz und Dateiablage | 2.14 | 4 |
| Integrationen und API | 2.15 | 4 |
| Betrieb und Protokolle | 2.16 | 3 |
| **Summe Schul-Instanz** | | **123** (= 56 Z6a + 54 Z6b + 13 Z6c) |
| Anbieter-Lizenzserver | 2.17 | 13 |
| **Summe Ist-Zustand** | | **136** |

Hinweis: `plan_periods` ist **keine Tabelle**, sondern eine Liste in den Einstellungen des Planungsdokuments (`settings.plan_periods`); Z6b führt sie fälschlich unter den Tabellen außerhalb des Bereichs.

---

## 2a Nachträge zum Tabellenverzeichnis

### 2a.1 Ergebnis der Vollständigkeitsprüfung

| Prüfung | Ergebnis |
|---|---|
| Tabellennamen aus Kapitel 2.1–2.16 (123) gegen die Tabellenüberschriften der Anhänge Z6a (56 = 13 Kern + 43 Feature), Z6b (54 in den Bereichen A–O) und Z6c (13) | Jede der 123 Tabellen steht **genau einmal** im Verzeichnis; keine fehlt, keine ist doppelt. Die Zählkontrolle (Kapitel 2.19) stimmt. |
| Umgekehrt: Namen im Verzeichnis, die in Z6 nicht vorkommen | nur die 13 Anbieter-Tabellen (Kapitel 2.17) und die Sammlungen des Planungsdokuments (Kapitel 2.18, keine Tabellen) |
| Tabellenverzeichnis des Ist-Zustands (Anhang I8 §11: 136 Tabellen in 18 Fachgruppen) | 136 = 123 + 13; deckungsgleich mit Kapitel 2 |
| Weitere Quellen (Z3, Z7, I8, I9, Backlog- und Planungsnotizen) | nennen **eine** weitere Tabelle des Ist-Zustands (Kapitel 2a.2) sowie Tabellen und Dokumentfelder, die erst **geplant** sind (Kapitel 2a.3) |

Die Zählung der Kennzahlen in Kapitel 0.2 (123 + 13 = 136) bleibt unverändert: Sie zählt Anwendungstabellen. Neue Tabellen erfüllen vor der Freigabe die Regeln des Kapitels 4 (Schema-Register DAM-044 ff., Datenart und Frist, Migration).

### 2a.2 Nachtrag zum Ist-Zustand (1 Tabelle)

| Tabelle | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Quelle |
|---|---|---|---|---|---|
| Migrationsstand (Tabelle des Migrationswerkzeugs; Name werkzeugabhängig, im Ist-Zustand Alembic) | hält die aktuelle Schemaversion der Schul-Instanz; Grundlage für „Datenbankstand aktuell“ auf der Statusseite und für die automatische Migration beim Start | keine | keine personenbezogenen Daten | Zustand, keine Frist; in jeder Sicherung enthalten | W4 (Migrationen), I8 §1 |

### 2a.3 Geplante Tabellen und Dokumentfelder (alle `Status: offen`)

Quelle: Backlog (W3), Abgleich (W2). Spalten sind in den Quellen **nicht** festgelegt; hier stehen nur die belegten Angaben, Unklares als `[unklar]`. Jede dieser Tabellen braucht beim Bau: Eintrag im Schema-Register (DAM-044), Klassifizierung jeder Spalte (DAM-045), Datenart mit Frist (DAM-076), Migration nach Expand/Contract (DAM-091 ff.).

| Objekt (Arbeitsname laut Backlog) | Zweck | Beziehungen | Geschützte Spalten | Aufbewahrung / Löschung | Quelle |
|---|---|---|---|---|---|
| `guardians` | Erziehungsberechtigte je Schüler/in (Beziehung, Sorgerecht, optional verknüpftes Konto); Geschwister teilen ein Elternkonto (Zusammenführung über E-Mail); Zugriff je Person einschränkbar (z. B. ohne Sorgerecht, Auskunftssperre) | `student_id` ⇢ Planungsdokument; optional Konto → `users` [N] | **V:** Name, E-Mail, Telefon (Backlog: verschlüsselt) | keine Datenart bisher; Frist [unklar], Entscheidung E-35 (Datei 10) | W3 B-18 |
| Schülerakte-Felder | Adresse, Notfallkontakt, Ein-/Austrittsdatum, Bemerkung; Fachlehrkräfte sehen nichts davon | `student_id` ⇢ | **V:** Bemerkung (Backlog: verschlüsselt); übrige Felder [unklar] | [unklar]; Speicherort (Tabelle oder Planungsdokument) [unklar] | W3 B-18 |
| `monitor_profiles` | Layout je Bildschirm: Name, Standort, Kacheln (Positivliste der Kacheltypen), Optionen, zugeordnete Monitor-Konten | Standort ⇢ Planungsdokument; Monitor-Konten → `users` | keine Personendaten | Konfiguration; bei Kontolöschung entfällt die Zuordnung | W3 B-28 |
| Passkeys (`webauthn`-Tabellen) | Passkeys je Konto: hinzufügen, benennen, entfernen; Anmeldung ohne Passwort; ein Passkey erfüllt die Zwei-Faktor-Pflicht | `user_id` → `users` [K] | öffentlicher Schlüssel (kein Geheimnis); Bezeichnung [unklar] | mit dem Konto; entfernbar | W3 B-21, W2 |
| Geräte-Token | „Angemeldet bleiben“ und Monitor-Geräte über widerrufbares Geräte-Token statt Abmeldung nach 30 Tagen | `user_id` → `users` [K] | **H:** Token (nur gehasht; Datenbankinhalt allein ermöglicht keine Anmeldung) | widerrufbar unter „Meine Geräte“; Frist [unklar] | W3 B-21, B-28 |
| `push` (Push-Abos) | Web-Push-Abo je Gerät (widerrufbar); Einstellung je Person, worüber benachrichtigt wird; Ruhezeiten | `user_id` → `users` [K] | Abo-Daten des Geräts personenbezogen; Schutz [unklar] | mit dem Konto; widerrufbar | W3 B-41 |
| `substitution_ledger` (Vertretungskonto) | je Tag Vertretungen, Entfälle und Mitbetreuungen je Lehrkraft für faire Verteilung (Ist, Soll, Abweichung im Halbjahr); nachträgliche Änderungen zählen mit | `teacher_id` ⇢ Planungsdokument | **K:** `teacher_id` (Beschäftigtendaten) | [unklar]; Zeitraum der Abrechnung Standard Halbjahr | W3 B-36 |
| `companies` (Ausbildungsbetriebe) | Stammdaten Betrieb (Name, Adresse, Ansprechpersonen mit E-Mail), Zuordnung Schüler/in ↔ Betrieb mit Zeitraum; Ausbilder-Zugang je Einladung | `student_id` ⇢; Ausbilder-Konto → `users` | Ansprechpersonen: Schutz [unklar] | [unklar] | W3 B-39 |
| `parent_letters` (Elternbriefe, Teilschritte a–c) | Brief an Klasse/Jahrgang/Bildungsgang/Gruppe/Schule mit Lesebestätigung je Familie, Rückmeldung (Ja/Nein, Auswahl, Freitext, Unterschrift auf dem Bildschirm, Frist) und Einwilligungen (versioniert, widerrufbar, Nachweis nach Art. 7 DSGVO) | Empfänger über `parent_links` / Konten; `student_id` ⇢ | Rückmeldungen und Unterschrift: Schutz [unklar]; Freitexte verschlüsselt (Regel DAM-034) | Archiv je Klasse und Schuljahr; Einwilligungsnachweis [unklar] | W3 B-47 |
| `consultations` (Sprechtag, Sprechstunde) | Sprechtag (Datum, Zeitfenster, Anmeldephase, Slotlänge 5 oder 10 Minuten, Puffer, Raum je Lehrkraft, vor Ort oder online) und wöchentliche Sprechstunde mit Buchung, Bestätigung, Absage | `teacher_id` ⇢; buchendes Konto → `users`; Eindeutigkeit je Slot (keine Doppelbuchung) | Freitext verschlüsselt (DAM-034) | [unklar] | W3 B-48 |
| `bookings` (Raum- und Gerätebuchung) | buchbare Räume/Geräte je Standort; belegte Räume laut Plan nicht buchbar | Raum, Standort ⇢ Planungsdokument; Buchende → `users` | – | [unklar] | W3 B-54 |
| Beurlaubungen und Befreiungen (Tabelle unbenannt) | Antrag auf planbare Abwesenheit (Datum oder Stunden, Grund, Nachweis), Status beantragt/genehmigt/abgelehnt mit Begründung, Fachbefreiungen mit Zeitraum | `student_id` ⇢; Antragsteller → `users`; Nachweis → `stored_files` | **V:** Grund, Begründung (Gesundheits-/Freitext, DAM-034) | Datenart `absences` oder eigene [unklar] | W3 B-40 |
| Unterrichtsstunde mit Hausaufgabe (Tabelle unbenannt) | Datensatz je Datum und Stunde: Hausaufgabe mit Fälligkeit, optional Thema; Schüler/innen haken „erledigt“ ab. **Überschneidung mit `register_lessons`** (Thema, Hausaufgabe) klären: [unklar] | `lesson_id`/`course_id` ⇢ | **V:** Thema, Hausaufgabe (wie `register_lessons`) | [unklar] | W3 B-30 |
| Erweiterungen von `student_absences` | Vermerke „eingesehen von/am“ und „anerkannt von/am“, Freigabe der Einsicht an einzelne Lehrkräfte (Stufe „anwesend/abwesend“ oder „vollständig“, befristbar) | wie `student_absences` | wie `student_absences` (Gesundheitsdaten) | wie `absences` | W3 B-29 |
| Schnittstelleneinstellungen (`system_settings`) | SMTP-Server, Port, Absender, Zugang und SMS-Anbieter in der Oberfläche statt nur per Umgebungsvariable; Umgebungsvariablen haben Vorrang | – | **V:** Passwörter (nie wieder angezeigt) | Konfiguration | W3 B-49 |

Erweiterungen des **Planungsdokuments** (keine Tabellen; `Status: offen`; alte Versionen müssen unverändert laden):

| Erweiterung | Inhalt | Quelle |
|---|---|---|
| Bildungsgänge, Klassentypen, Klassengruppen | Bildungsgang (Name, Kurzname, Jahrgänge, Abschlussjahrgang, Namensmuster); Klasse mit Bildungsgang, Typ, Parallelbezeichnung, freiem Namen und `active` (Archivieren statt Löschen); Gruppe aus festen Klassen oder Regel „Bildungsgang × Jahrgänge“; Stundentafel-Vorrang Klasse > Gruppe > Bildungsgang+Jahrgang > Jahrgang; `cancel_min_grade` je Bildungsgang | W3 B-14 |
| Klassenrollen | `class_teachers` (Reihenfolge = Hauptverantwortung), `deputies`, `department`, `speakers` (höchstens zwei Schüler/innen), `managers`; neue Sammlung `departments` (Name, Klassen bzw. Bildungsgänge/Jahrgänge, Leitungen); das alte Feld `class_teacher` wird weiter gelesen und geschrieben (= erste Klassenleitung) | W3 B-15 |

Backlog-Namen, die **keine** neue Tabelle bedeuten (bereits gebaut, kein Nachtrag): `parent_access` (B-07, Kapitel 2.3), `retention` (B-38, Tabellen `retention_*`, Kapitel 2.14), `school_year` (B-37, Zustandsschlüssel `yearchange` in `system_state`, Kapitel 1.2), `grades` (B-52, Tabellen `gb_*` und `exam_results`, Kapitel 2.5; Übergabe an SchILD/SVWS bleibt offen), Benachrichtigungszentrale (Kapitel 2.11).

---

## 3 Beziehungsüberblick

Zeichen: `1──<` eins-zu-viele, `1──1` eins-zu-eins, `──▶` Verweis ohne Fremdschlüssel (Text-ID), `[K]` Kaskade beim Löschen des linken Partners, `[N]` Feld wird leer.

### 3.1 Die zwei Welten und ihre Brücken

```
PLANUNGSDOKUMENT (school_versions, versioniert, verschlüsselt)        RELATIONALE TABELLEN
 sites ─┬─ rooms                                                       users
        ├─ classes ──< students ──(courses[])──┐                        │ teacher_id ──▶ teachers.id   (Kürzel)
        └─ teachers (Kürzel)                    │                        │ student_id ──▶ students.id
 subjects ─ curricula ─ grade_profiles          │                        └─ role / custom_role
 courses ──< parts (Fach, Lehrkraft, Raum) ─────┘
    │ 1──<
 lessons (Block: Tag, Start, Länge, Wochen)                  Verweise aus Tabellen in den Plan (alle ohne FK):
 absences / overrides / holidays / duties / exams / events     student_id · class_id · teacher_id · course_id
                                                                exam_id · lesson_id · site · plan_periods.id
```

### 3.2 ID-Brücken: welche Tabellen verweisen auf welches Planungsobjekt

| Plan-Kennung | Planungsobjekt | Tabellen mit diesem Verweis (ohne FK) |
|---|---|---|
| `student_id` | `students[].id` | `users`, `parent_links`, `parent_access`, `student_prefs`, `student_absences`, `student_absence_events`, `student_documents`, `student_support`, `form_submissions`, `assignment_submissions`, `exam_results`, `exam_makeups`, `gb_entries`, `gb_finals`, `gb_log`, `gb_source_results`, `comp_assessments`, `comp_plans`, `comp_badge_awards`, `notifications`, `retention_leavers` |
| `class_id` / Klassen-IDs | `classes[].id` | `form_submissions`, `retention_leavers`, `branches.class_ids`, `register_lessons.class_ids`, `announcements.class_ids`, `login_policy_rules.scope_ref` (scope = class), `channels.ref` (kind = class) |
| `teacher_id` | `teachers[].id` | `users`, `register_lessons`, `teacher_change_requests` |
| `course_id` | `courses[].id` | `register_lessons`, `exam_results`, `exam_makeups`, `gb_books`, `gb_source_results`, `channels.ref` (kind = course, Format „Kurs#Teil“, Teil 0-basiert) |
| `exam_id` | `exams[].id` | `exam_results`, `exam_makeups`, `exam_makeup_dates` |
| `lesson_id` | `lessons[].id` | `register_lessons`, `channel_items`, `channel_folders` |
| `site` | `sites[].id` | `users`, `announcements` |
| Planzeitraum | `settings.plan_periods[].id` | `plan_snapshots.period` |

Längen der ID-Spalten sind im Ist-Zustand uneinheitlich (40, 64, 80); Regel DAM-106.

### 3.3 Konten-Kern

```
users 1──< sessions                      users 1──< api_tokens 1──< api_token_log
      1──1 user_contacts                       1──< user_identities >──▶ sso_providers.provider
      1──1 account_initial_passwords           1──< auth_codes
      1──< letter_batches  (created_by)        1──1 account_watch 1──< watch_log
      1──< parent_links  ──▶ student_id        1──< user_branches >── branches
      1──< mail_accounts                       role ──▶ role_overrides(role, permission)
      custom_role ──▶ custom_roles ──▶ role_overrides (role = "x-…")
      audit_log.user_id  [N]     announcements.author_id [N]     school_versions.user_id [N]
```

### 3.4 Person → Fachdaten (alles, was an einer Schülerin/einem Schüler hängt)

```
students.id  ──▶ student_absences ──< student_absence_events
(Plan)       ──▶ student_documents      (absence_id, file_id → stored_files)
             ──▶ student_support ──▶ support_catalog        parent_access / student_prefs  (Eltern-Sicht)
             ──▶ exam_results · gb_entries · gb_finals · gb_log · gb_source_results   (Noten)
             ──▶ comp_assessments · comp_plans · comp_badge_awards                    (Kompetenzen)
             ──▶ form_submissions · assignment_submissions · notifications.student_id
             ──▶ retention_leavers  (Warteliste nach Austritt, Löschkonzept)
users.student_id ◀── Konto der Person ── 1──< Sitzungen, Nachrichten, Chats, Abgaben, Fortschritt
```

### 3.5 Kurs → Stunde → Fehlzeit, Klassenbuch, Noten

```
Plan: course ──< lessons (Block)                 Plan: exam (course_id, date, start)
   │ course_id            │ lesson_id, date, period, part        │ exam_id
   ▼                      ▼                                       ▼
 channels (kind=course,  register_lessons                       exam_results ◀─ student_id
   ref="Kurs#Teil")        UNIQUE(date, lesson_id, period, part)  exam_makeups ──▶ exam_makeup_dates [N]
   │                       topic_enc / homework_enc / attendance_enc     │ absence_id
   │                       │ register_id                                 ▼
   │                       ▼                              student_absences ◀── exam_makeups
   │                    student_absences ──< student_absence_events
   │                       ▲   └──< student_documents (absence_id) [N]
   │                       └── Fehlen / Verspätung / frühes Gehen werden aus dem Klassenbuch erzeugt
   ▼
 gb_books (course_id, part, term) 1──< gb_categories 1──< gb_items 1──< gb_entries ◀── student_id
     1──< gb_finals · gb_source_links ──▶ gb_source_results (Quelle: Aufgabe, Selbsttest)
     gb_log (book_id ohne FK, bleibt erhalten)
```

### 3.6 Kursraum

```
channels 1──< channel_folders (Baum über parent_id) 1──< channel_items (Material, Aufgabe)
   │                               │                         │ 1──1 assignment_settings ──▶ grading_templates [N]
   │                               │                         │ 1──< assignment_submissions 1──< assignment_submission_versions
   │                               │                         │ 1──< assignment_extensions (Person oder Gruppe)
   │                               │                         │ 1──< channel_item_views
   │ 1──< channel_extra_members    └── channel_group_gates ──▶ channel_groups ◀── channel_group_sets
   │ 1──< channel_group_sets 1──< channel_groups 1──< channel_group_members
   │ 1──< channel_posts (Pinnwand, parent_id: eine Ebene)    1──< channel_reads
   │ 1──< completion_rules · completion_marks · availability_rules   (element_type/element_id generisch)
   └── 1──< learning_polls · learning_surveys · learning_questions · learning_selftests
              polls 1──< participants / votes / tally     surveys 1──< responses / participants
              selftests 1──< learning_attempts
```

### 3.7 Postfach und Chats

```
conversations 1──< conversation_participants >── users
      │ 1──< messages 1──< message_reports        messages.attachment_ids ──▶ stored_files
      │ parent_id (private Antwort auf Rundschreiben) [N]
      │ mail_account_id ──▶ mail_accounts ;  migrated_chat_id ──▶ chats
users 1──< message_drafts · user_blocks(user, blocked_user) · message_user_settings · send_idempotency

chats ──▶ chat_members ──▶ users              (alle Chat-Verweise ohne Fremdschlüssel)
  └──▶ chat_messages ──▶ chat_message_keys ◀── chat_devices   (Schlüssel je Gerät)
  └──▶ chat_attachments · chat_reports ──▶ chat_report_images
  chat_devices ◀── chat_link_requests · chat_key_backups(user_id)
```

### 3.8 Formulare, Benachrichtigungen, Löschkonzept

```
form_templates 1──< form_versions 1──< form_submissions 1──< form_events
notifications (user_id) · notification_prefs · notification_user_settings ; notification_school/config (schulweit)
notifications_outbox (Webhook/E-Mail, dedupe_key)
Planungsdokument(students) ──Abgleich──▶ retention_leavers ──Frist──▶ Löschung je Datenart ──▶ retention_log
retention_settings (Fristen) ; audit_log ; watch_log
```

---

## 4 Datenmodell-Regeln (DAM) mit Abnahme

### 4.0 Lesehilfe

- **Kennung** `DAM-nnn`, fortlaufend ab 001, gilt nur in dieser Datei. Das Kürzel DAM (Datenmodell) steht bewusst nicht für DAT, damit die Regeln nicht mit den Datenschutz-Anforderungen der Rechts- und Datenschutz-Datei verwechselt werden.
- **Priorität:** P0 Pflicht/Sicherheit/Recht · P1 Kernfunktion · P2 wichtig · P3 Wunsch. **Status:** `Status: Ist` = im Vorgängerbestand vorhanden, vom Neubau mindestens zu erreichen; `Status: offen` = gewünscht, entschieden oder zur Schließung einer belegten Lücke nötig, noch nicht gebaut (bei Lücken steht der Ist-Zustand dabei).
- **Abnahme:** genau eine Zeile `Abnahme:` je Anforderung. Begriffe: *Schema-Test* = automatischer Test gegen das Schema-Register (DAM-044) und das frisch migrierte Schema; *Zählabfrage* = Datenbankabfrage mit Zählergebnis; *feste Uhr* = Test mit eingefrorener Zeit; *Wegwerf-Instanz* = isolierte Testinstanz mit Testdaten (nie Echtdaten). `[Prüfwert]` = Vorschlag des Schreibers, nicht aus den Quellen. „Fremdes Objekt → 404“ = Status 404 ohne Hinweis auf Existenz.
- Werte, die in den Quellen fehlen, stehen als `[unklar: …]`. Fachliche Abläufe (Löschkonzept im Ganzen, Auskunft, Anmeldung, Rechte) sind in den Fachdateien beschrieben; hier stehen nur die Regeln, die das **Schema, die Speicherung und die Migration** betreffen.

### 4.1 Speicherformen und Struktur des Planungsdokuments

- **DAM-001** (P0, Status: Ist) Zwei Speicherformen: Das **Planungsdokument** (`settings`, 17 Sammlungen, optional `monitors` und `holiday_import`) hält Stamm- und Planungsdaten; **relationale Tabellen** halten Konten, Rechte, Protokolle und alle Fachdaten mit Personenbezug. Personenbezogene Fachdaten mit hohem Änderungsaufkommen (Noten, Fehlzeiten, Nachrichten, Kursraum-Inhalte) liegen nie im Planungsdokument.
  Abnahme: Ein Planungsdokument mit zusätzlicher Sammlung `grades` (oder `messages`) gespeichert und neu geladen → die Sammlung fehlt (unbekannte Sammlungen werden verworfen); die Schlüssel des geladenen Dokuments sind genau `settings`, die 17 Sammlungen und höchstens `monitors`, `holiday_import`.
- **DAM-002** (P1, Status: Ist) Brücke zwischen den Welten über **Text-IDs**: Tabellen verweisen auf Planungsobjekte mit `student_id`, `class_id`, `teacher_id`, `course_id`, `exam_id`, `lesson_id`, `site` (ohne Fremdschlüssel); Konten verweisen über `users.teacher_id` und `users.student_id` auf Personen; das Planungsdokument kennt keine Konten.
  Abnahme: Schema-Test: alle genannten Spalten sind Textspalten ohne Datenbank-Fremdschlüssel; ein Scan über alle Versionen des Planungsdokuments findet keine Konto-ID (`users.id`) → 0 Treffer.
- **DAM-003** (P1, Status: Ist) Das Planungsdokument wird verlustfrei als JSON serialisiert; beim Lesen werden unbekannte Felder und Sammlungen verworfen, fehlende optionale Felder erhalten den Standardwert; beim Speichern wird das ganze Dokument in das aktuelle Format normalisiert.
  Abnahme: Dokument laden und unverändert speichern → SHA-256 des JSON identisch zum Zustand vor dem Laden, keine neue Version (DAM-016); Dokument ohne ein optionales Feld laden → Standardwert, kein Fehler.
- **DAM-004** (P2, Status: offen) Vorwärtskompatibilität: Ein älterer Programmstand darf kein Dokument speichern, dessen Formatstufe er nicht kennt (Ist: unbekannte Felder gehen beim Speichern durch ältere Stände verloren, Lücke L6 in Z7). [Vorschlag] Das Dokument trägt eine Formatstufe.
  Abnahme: Dokument mit höherer Formatstufe als der Programmstand kennt → Speichern wird mit Klartextfehler abgelehnt, keine neue Version; gleiche Stufe → Speichern ok.
- **DAM-005** (P1, Status: Ist) Zeitbasis des Planungsdokuments: Wochentag 0 = Montag … 6 = Sonntag; Stunde 0-basiert (erste Stunde = 0); laufende Woche 1-basiert (1 bis 52 bzw. 53, Montag bis Sonntag, Ferien zählen mit), gezählt nach `week_numbering` (`iso` = Kalenderwochen, Standard; `school_year` = Woche 1 ist der Schuljahresbeginn).
  Abnahme: Block mit Tag 0, Start 0 erscheint in Oberfläche und Export als „Montag, 1. Stunde“; Tag 6 als Sonntag; mit `week_numbering` = `school_year` ist die Woche des Schuljahresbeginns Woche 1, mit `iso` die Kalenderwoche.
- **DAM-006** (P1, Status: Ist) Wochenangabe: `weeks` (Liste laufender Wochen) **oder** `rhythm` {every, from_week, to_week}; ist `rhythm` gesetzt, wird `weeks` ignoriert; beides leer = jede Woche. Woche w ist aktiv, wenn `from_week` ≤ w, (`to_week` = 0 oder w ≤ `to_week`) und (w − `from_week`) durch `every` teilbar ist. Fehlende oder ungültige Werte: `every` < 1 → 1, `from_week` 0/fehlend → 1, `to_week` fehlend → offen; nicht lesbare Werte oder unbekannte Woche → Regel gilt als aktiv.
  Abnahme: `rhythm` {every 2, from_week 1, to_week 0} ist in den Wochen 1, 3, 5 aktiv und in 2, 4 nicht; mit zusätzlichem `weeks` = [2] bleibt es bei 1, 3, 5; `every` = 0 verhält sich wie 1; `to_week` = 3 → Woche 5 inaktiv.
- **DAM-007** (P1, Status: Ist) Eine **leere Liste bedeutet „alle“**: `TimeRule.days` = jeder Tag, `TimeRule.periods` und `Absence.periods` = ganzer Tag, `Event.classes` und `Event.grades` beide leer = ganze Schule, `Teacher.sites` = alle Standorte, `weeks` = alle Wochen, `Settings.school_days` = Tage 0 bis `days` − 1.
  Abnahme: Zeitregel ohne `days` und `periods` sperrt jede Stunde jedes Tages; Termin ohne `classes` und `grades` erscheint im Kalender jeder Klasse; Lehrkraft ohne `sites` ist an allen Standorten einsetzbar.
- **DAM-008** (P1, Status: offen) Eindeutigkeit und Verweisprüfung im Planungsdokument: Kennungen (`id`) sind **je Sammlung eindeutig**, Verweise zwischen Datensätzen (Kurs → Klasse, Fach, Lehrkraft, Raum; Block → Kurs; Abwesenheit → Lehrkraft, Klasse, Raum, Kurs; Aufsicht → Bereich, Lehrkraft; Lehrkraft → Fach, Standort) zeigen auf vorhandene Datensätze. Ist: weder Eindeutigkeit noch Verweise werden geprüft (Z7 V2, V3, L4); verwaiste Verweise sind möglich.
  Abnahme: Zwei Klassen mit gleicher `id` speichern → abgelehnt, keine neue Version, Klartextfehler; Kurs mit nicht vorhandener Klassen-`id` speichern → abgelehnt oder Warnliste aller verwaisten Verweise [unklar: ablehnen oder warnen, Entscheidung beim Betreiber]; Löschen eines Faches, das ein Kurs nutzt → 409 mit Verweisliste, Löschen nur mit ausdrücklicher Bestätigung.
- **DAM-009** (P2, Status: offen) Wertebereiche und Auswahlwerte des Planungsdokuments werden beim Speichern erzwungen (Ist: nur in Kommentaren genannt, Z7 V4, V6, L5): `trash_retention_days` 1–365, `work_grid.weeks` 1–52, Wochentage 0–6, Wochen 1–52/53, Auswahlfelder (`kind`, `action`, `mode`) aus fester Liste. Ausnahme bleibt: Ferien-Art ungültig oder fehlend → aus dem Namen abgeleitet.
  Abnahme: `trash_retention_days` = 0 und = 366 speichern → abgelehnt; Wochentag 7 in einer Zeitregel → abgelehnt; unbekannter `action`-Wert → abgelehnt; Ferien ohne Art → Art aus dem Namen abgeleitet, kein Fehler.
- **DAM-010** (P2, Status: offen) Die Einstellungs-Tabellen `security_settings`, `retention_settings`, `gb_config` haben je eine **feste, dokumentierte Schlüsselliste** mit Typ, Standardwert und Wertebereich (Ist: Schlüssellisten und Standardwerte nicht belegt, Z6c Offene Werte 1, 2; Z6b §5). Fristen werden auf 0 bis 3650 Tage begrenzt.
  Abnahme: Schreiben eines unbekannten Schlüssels → 422; Frist 5000 → gespeichert als 3650, Frist −1 → 0; frische Instanz: jeder Schlüssel der Liste hat den dokumentierten Standardwert (Schema-Test gegen das Register).
- **DAM-011** (P1, Status: Ist) Jede Einstellung hat **genau einen Speicherort** (Kapitel 1.2): Umgebungsvariablen `SM_*` (Betrieb, Geheimnisse, Pfade, Schalter), Planungsdokument `settings` (fachlich, versioniert), `security_settings`, `retention_settings`, `gb_config`, `notification_*`, `login_policy_rules`, `sso_providers`, `system_state`. Jede neue Umgebungsvariable ist an allen Stellen hinterlegt (Konfiguration, Beispiel-Umgebungsdatei, Container-Konfiguration, Betriebsdokumentation).
  Abnahme: Test listet jede Einstellung der Oberfläche und ordnet sie genau einem Speicher zu; eine Einstellung in zwei Speichern oder eine Variable, die in einer der vier Stellen fehlt, lässt den Test scheitern.
- **DAM-012** (P0, Status: Ist) Umgebungsvariablen haben Vorrang vor Tabellenwerten (`SM_SSO_*`, `SM_OIDC_*`, SMTP/SMS); Geheimwerte stehen nie im Klartext in Tabellen, Protokollen oder Auskünften.
  Abnahme: `SM_SSO_*` gesetzt und abweichender Wert in `sso_providers` → wirksam ist der Umgebungswert; Suche nach dem Geheimwert in Datenbank, Log und Audit → 0 Treffer.
- **DAM-013** (P0, Status: Ist) Mandantentrennung: Eine Schul-Instanz hält die Daten **genau einer Schule** in einer eigenen Datenbank, mit eigenem Geheimschlüssel (`SM_SECRET_KEY`), eigenem Schlüsselring (`SM_ENCRYPTION_KEYS`) und eigenem Datenvolumen.
  Abnahme: Zwei Instanzen A und B: Sitzungs-Cookie oder API-Token aus A gegen B → 401; eine Zeile mit verschlüsseltem Feld aus A in die Datenbank von B kopiert → Feld nicht lesbar (Fehler „ungültig“ bzw. „nicht lesbar“, nie Klartext).
- **DAM-014** (P1, Status: Ist) Zwei Datenbanken mit gleichem Schema und gleichen Migrationen: SQLite (Standard, eine Datei im Datenordner) und PostgreSQL (große Schulen, Mehrserver-Betrieb); JSON-Export-Sicherung nur bei PostgreSQL, SQLite-Sicherung über die Backup-Schnittstelle der Datenbank.
  Abnahme: Alle Migrationen und die Schema-Tests laufen auf beiden Datenbanken grün; der Schema-Vergleich (Spalten, Eindeutigkeiten, Fremdschlüssel, Indizes) beider Datenbanken ist identisch.
- **DAM-015** (P2, Status: Ist) `system_state` ist ein Schlüssel/Wert-Speicher für den Betriebszustand (`setup`, `school_profile`, `yearchange`, `maintenance`, Leader-Pacht im Mehr-Knoten-Betrieb) und enthält **keine Freitexte über Personen**.
  Abnahme: Stichprobe aller Werte nach Einrichtung, Schuljahreswechsel und Wartungslauf: kein Personenname, keine E-Mail-Adresse, keine IP-Adresse; unbekannter Schlüssel wird nicht angelegt.

### 4.2 Versionierung, Rückgängig und Synchronisierung des Planungsdokuments

- **DAM-016** (P1, Status: Ist) Jede erfolgreiche Änderung erzeugt **genau eine** neue Version in `school_versions`; ein identischer Stand (SHA-256 über das JSON) erzeugt keine Version, keinen Audit-Eintrag, kein Ereignis; schlägt die Änderung fehl (z. B. Berechtigungs- oder Prüffehler), wird nichts gespeichert und kein Ereignis gesendet.
  Abnahme: Dieselbe Einstellung zweimal speichern → Versionsnummer nach dem zweiten Speichern unverändert, kein neuer Audit-Eintrag, kein Live-Ereignis; Änderung ohne Berechtigung → 403, Versionsnummer und Stand unverändert.
- **DAM-017** (P1, Status: Ist) Jede Änderung arbeitet auf einer **vollständigen Kopie**; erst nach erfolgreichem Speichern ersetzt sie den aktiven Stand; Leser erhalten eine Momentaufnahme und sehen nie einen halben Zustand; Schreiben blockiert Lesen nie.
  Abnahme: Eine Änderung wird in der Mitte mit einem Fehler abgebrochen → ein paralleler Lesezugriff sieht ausschließlich den alten Stand; während einer laufenden Änderung antwortet ein Lesezugriff, ohne auf deren Ende zu warten.
- **DAM-018** (P1, Status: Ist) Metadaten je Version: Nummer (fortlaufend, **nie wiederverwendet**), Urheber (`user_id`, leer = System, bei Kontolöschung leer), Notiz (höchstens 500 Zeichen, längere werden gekürzt), Bereich `scope` (Liste, Standard `["all"]`; feste Werte `init`, `restore`, `undo`), Ursprungsversion `restored_from`, `created_at` (UTC). Versionen werden nie geändert; die einzige Löschung ist die Aufbewahrungsgrenze.
  Abnahme: Notiz mit 600 Zeichen → gespeichert mit 500; nach dem Löschen der ältesten Versionen erhält die nächste Änderung eine Nummer größer als jede je vergebene; es gibt keinen Schreibpfad, der eine bestehende Versionszeile ändert.
- **DAM-019** (P1, Status: Ist) Aufbewahrung: **300 Versionen** (`SM_KEEP_VERSIONS`); nach jedem Speichern werden die ältesten darüber endgültig gelöscht (keine Archivierung); gelöschte Versionen sind nicht wiederherstellbar. Mindest- und Höchstwert der Einstellung [unklar].
  Abnahme: `SM_KEEP_VERSIONS` = 3 und vier Änderungen → genau 3 Versionen, die älteste Nummer fehlt; Wiederherstellen der entfallenen Nummer → Fehler „Version N existiert nicht (mehr)“.
- **DAM-020** (P2, Status: offen) Aufbewahrung der Versionen auch **nach Tagen** bemessen (Ist: nur Anzahl; bei 100 Änderungen am Tag decken 300 Versionen rund 3 Tage ab, Optimierung #15 offen; gemessen im Ist: Ø 66 KB je Version). Zielwert [unklar].
  Abnahme: Einstellung „Tage“ = N → Versionen jünger als N Tage bleiben unabhängig von der Anzahl erhalten, ältere über der Anzahlgrenze werden gelöscht (feste Uhr).
- **DAM-021** (P1, Status: offen) **Optimistische Prüfung in jedem Betrieb:** Jede Änderung prüft beim Speichern, dass die Version, auf der sie aufbaut, noch die aktuelle ist; sonst Fehler „Der Plan wurde inzwischen auf einem anderen Server geändert. Bitte erneut versuchen.“; keine automatische Zusammenführung. Ist: Die Prüfung gibt es nur im Mehrserver-Betrieb; bei mehreren Prozessen ohne Mehrserver-Betrieb können sich gleichzeitige Änderungen überschreiben (Lost Update, Z7 S6, L1).
  Abnahme: Zwei gleichzeitige Änderungen auf derselben Basisversion → genau eine wird gespeichert (Versionsnummer +1), die andere erhält den Fehlertext und ändert nichts; 20 parallele Änderungen verschiedener Felder [Prüfwert] → keine geht still verloren (jede ist gespeichert oder wurde mit dem Fehlertext abgelehnt).
- **DAM-022** (P1, Status: Ist) Mehrserver-Betrieb: Vor dem Speichern wird geprüft, ob die Version noch die zuletzt geladene ist; auf PostgreSQL zusätzlich eine datenbankweite Schreibsperre bis zum Commit (ein Schreiber gleichzeitig). Genau ein Arbeitsprozess je Knoten; Live-Ereignisse und Zwischenspeicher liegen im Prozessspeicher. Auf Datenbanken ohne die Sperre bleibt ein Restrisiko (Z7 L2).
  Abnahme: Zwei Knoten auf einer PostgreSQL-Datenbank ändern gleichzeitig → einer speichert, der andere erhält den Fehlertext aus DAM-021; kein Zustand mit zwei Versionen gleicher Nummer (Zählabfrage auf Duplikate der Nummer = 0).
- **DAM-023** (P0, Status: Ist) Die **Nutzlast jeder Version ist verschlüsselt:** JSON (UTF-8, Umlaute unverändert, Schlüssel sortiert, ohne Leerzeichen) → zlib (Stufe 6) → AES-256-GCM mit eigenem Datenschlüssel je Version; Zusatzkontext `school_versions.data:<Versionsnummer>`; die Prüfsumme wird über das JSON **vor** der Verschlüsselung gebildet und nicht gespeichert (beim Laden berechnet).
  Abnahme: Suche in einem Datenbankauszug von `school_versions` nach Namen einer Lehrkraft und einem Abwesenheitsgrund → 0 Treffer; die Nutzlast von Version 5 in die Zeile von Version 6 kopiert → Fehler „ungültig“, Anzeige „[nicht lesbar]“ und Protokolleintrag.
- **DAM-024** (P0, Status: offen) **Jeder** Speicher von Planungsdaten ist von Anfang an verschlüsselt, auch `plan_snapshots.data` und der Bestand beim Anlegen; es gibt keinen unverschlüsselten Altbestand. Ist: `plan_snapshots.data` ist nur zlib-komprimiert, ältere Planversionen waren unverschlüsselt und werden beim Start umgeschrieben (Fehler dabei blockieren den Start nicht).
  Abnahme: Auszug von `plan_snapshots.data` → Präfix `SM1`, ohne Schlüssel nicht lesbar; Zählabfrage „Planversionen oder Plan-Stände ohne Präfix `SM1`“ = 0 auf frischer Instanz und nach jeder Datenübernahme (DAM-102); `rotate-keys` schreibt auch diese Zeilen um.
- **DAM-025** (P1, Status: Ist) Rückgängig und Wiederherstellen erzeugen **eine neue Version** und löschen nichts. Rückgängig: Bereich `["all","undo"]`, Aktion `plan.undo`, Ursprung = Zielversion, Notiz „Rückgängig: zurück auf Version N (Notiz der Version N)“; Basis und Ziel nach der Entscheidungstabelle (Kapitel 1.3). Wiederherstellen von N: Bereich `["all","restore"]`, Aktion `plan.restore`, Ursprung N, Notiz „Version N wiederhergestellt“. Beides läuft unter derselben Sperre wie Änderungen.
  Abnahme: Versionen 1, 2, 3 → Rückgängig → Version 4 hat den Inhalt von Version 2 (`restored_from` = 2); erneut Rückgängig → Version 5 hat den Inhalt von Version 1; bei nur einer Version → Fehler „Es gibt keine ältere Version, die wiederhergestellt werden kann“; Wiederherstellen einer nicht vorhandenen Nummer → „Version N existiert nicht (mehr)“; kein lesbarer aktueller Stand → „Kein aktueller Stand vorhanden“.
- **DAM-026** (P1, Status: offen) **Start bei unlesbarem Planungsdokument:** Sind alle geprüften jüngsten Versionen (höchstens 5) unlesbar, startet der Neubau **nicht** mit einem leeren Dokument und schreibt keine neue Version, sondern meldet den Zustand auf der Statusseite und im Log und lässt die Daten unberührt. Ist: Start mit leerem Dokument, gespeichert als neue Version `plan.init`; ältere Versionen bleiben nur bis zur Aufbewahrungsgrenze (Z7 A3, L3; Risiko bei Schlüsselverlust oder Fehlkonfiguration). [Vorschlag zur Schließung der Lücke]
  Abnahme: Datenbank mit 5 unlesbaren jüngsten Versionen (falscher Schlüssel) → Start meldet „Planungsdokument nicht lesbar“, Zeilenzahl von `school_versions` unverändert, `/betrieb` zeigt einen Fehler; mit richtigem Schlüssel normaler Start; unlesbare ältere Versionen werden übersprungen und protokolliert.
- **DAM-027** (P1, Status: Ist) Erststart: Ist `school_versions` leer, wird ein leeres Dokument als erste Version gespeichert (Notiz „Leeres Planungsdokument angelegt“, Bereich `["all","init"]`, Aktion `plan.init`).
  Abnahme: Frische Instanz → genau eine Version mit dieser Notiz und diesem Bereich, ein Audit-Eintrag `plan.init`; ein zweiter Start erzeugt keine weitere Version.
- **DAM-028** (P2, Status: Ist) Verlauf und Audit: Verlauf neueste zuerst, Standard 50 Einträge je Seite, höchstens 1000 je Abfrage, die geltende Version ist als „aktuell“ gekennzeichnet; Anzeigename = Anzeigename des Kontos, sonst Benutzername, ohne Konto „System“. Je Version ein Audit-Eintrag (Aktionen `plan.init`, `plan.change`, `plan.replace`, `plan.restore`, `plan.undo`; Ziel = Versionsnummer).
  Abnahme: Abfrage mit Limit 5000 → höchstens 1000 Einträge; Version eines gelöschten Kontos → Anzeige „System“; jede der fünf Aktionen erzeugt genau einen Audit-Eintrag mit der Versionsnummer als Ziel.
- **DAM-029** (P2, Status: Ist) Synchronisierung: Die Prüfung auf eine neuere Version erfolgt höchstens alle **2 s** und lädt nur bei abweichender Versionsnummer neu; vor jeder Änderung wird die neueste Version nachgeladen; nach jeder erfolgreichen Änderung (auch Wiederherstellen, Rückgängig, Ersetzen) entsteht ein Ereignis „change“ mit Versionsnummer, Bereich und Datumsliste, **ohne Inhalte**.
  Abnahme: Änderung auf Knoten A → Knoten B zeigt den neuen Stand nach spätestens 2 s plus Antwortzeit [Prüfwert: 5 s]; der Ereignisinhalt enthält keinen Namen und keinen Freitext.
- **DAM-030** (P2, Status: Ist) Gespeicherte Plan-Stände (`plan_snapshots`, nur Unterrichtsblöcke, optional je Planzeitraum) bleiben bis zum Löschen erhalten, unabhängig von der 300er-Grenze; Wiederherstellen legt wie jede Änderung eine neue Planversion an.
  Abnahme: Plan-Stand speichern, danach 301 Änderungen → der Plan-Stand ist weiterhin vorhanden; Wiederherstellen erzeugt eine neue Version und verändert die Plan-Stände nicht.

### 4.3 Verschlüsselung und Schema-Register

- **DAM-031** (P0, Status: Ist) Verfahren und Format: AES-256-GCM; **jeder** verschlüsselte Wert und jede Datei hat einen eigenen zufälligen 256-Bit-Datenschlüssel, umschlossen mit dem aktiven Hauptschlüssel des Schlüsselrings; Nonce 96 Bit zufällig je Verschlüsselung; Textformat Präfix `SM1.` + Base64-URL ohne Auffüllung, Binärformat Präfix `SM1`, Dateiformat Präfix `SMS1` blockweise (Standard 64 KiB, zulässig 1 KiB bis 16 MiB, 32-Bit-Blockzähler mit Schlussblock-Kennzeichen, 7 Byte zufälliges Dateipräfix). Leere Werte bleiben leer und werden nicht verschlüsselt.
  Abnahme: Derselbe Klartext zweimal verschlüsselt → verschiedene Chiffrate; Datei mit vertauschten, fehlenden oder angehängten Blöcken → „ungültig“; leerer Text → leere Spalte, kein Chiffrat; Blockgröße 512 Byte oder 32 MiB → abgelehnt.
- **DAM-032** (P0, Status: Ist) Bindung (AAD): Jedes Chiffrat ist an Tabelle, Feld und Zeilen-ID gebunden, `<tabelle>.<feld>:<zeilen-id>`, mit `<feld>` = Spaltenname ohne Suffix `_enc`; die ID steht **vor** dem Verschlüsseln fest. Ein in eine andere Zeile oder Spalte kopiertes Chiffrat lässt sich nicht entschlüsseln.
  Abnahme: Automatischer Test über **alle** registrierten Chiffrat-Spalten: Chiffrat aus Zeile 1 in dieselbe Spalte von Zeile 2 kopiert → „ungültig“; in eine andere Spalte derselben Zeile kopiert → „ungültig“; unveränderte Zeile → lesbar.
- **DAM-033** (P0, Status: offen) Das Bindungsschema ist **ohne Abweichung** einheitlich. Ist: Abweichungen bei `messages.body:<conversation_id>:<message_id>`, `message_drafts.data:<user_id>:<draft_id>`, `message_user_settings.suspension_reason:<user_id>`, `sso_providers.<feld>:<Anbieter>`, `letter_batches:<id>`, `teacher_change_requests:<id>:<feld>` und beim Löschgrund im Audit mit **festem** Zusatzdatum (`audit_log.privacy.erase.grund`, nicht zeilengebunden, ein Chiffrat ließe sich in einen anderen Eintrag verschieben). Im Neubau gilt für alle das Muster aus DAM-032 mit der ID der Zeile.
  Abnahme: Schema-Test: genau ein AAD-Muster im Register; Löschgrund-Chiffrat von Audit-Eintrag A in Eintrag B kopiert → „ungültig“; nach einer Datenübernahme (DAM-102) Zählabfrage „Chiffrate mit altem Muster“ = 0.
- **DAM-034** (P0, Status: offen) **Jede Freitext-Spalte ist verschlüsselt** (Betreiberregel „Freitexte verschlüsselt“). Ist im Klartext und im Neubau zu verschlüsseln: `login_policy_rules.note`, `exam_makeup_dates.note`, `announcements.title`/`body`, `plan_proposals.decision_note`, `plan_proposal_log.note`, die Freitexte `wishes`/`reason` im JSON `teacher_change_requests.payload`; zu prüfen [unklar]: `letter_batches.title`, `learning_questions.category`. Eine Ausnahme ist nur zulässig, wenn das Schema-Register die Spalte als „kein Personenbezug“ mit Begründung führt (z. B. Rollenname).
  Abnahme: Schema-Test: jede Spalte der Klasse „Freitext“ im Register hat Klasse V oder einen begründeten Ausnahme-Eintrag; Datenbankauszug der genannten Spalten: jede nicht leere Zeile beginnt mit `SM1.`; eine neue Freitext-Spalte ohne Klasse macht den Test rot.
- **DAM-035** (P0, Status: offen) **Gesundheitsdaten** werden ausschließlich verschlüsselt gespeichert und einheitlich benannt: `student_absences.reason_enc` und `note_enc` (Ist: Spalten `reason`/`note` ohne Suffix, Inhalt als Token; Z6a führt sie als Klartext, Altbestand im Klartext nicht ausgeschlossen), ebenso `student_documents.title_enc`/`note_enc`, `student_support.title_enc`/`details_enc`/`aids_enc`, `register_lessons.topic_enc`/`homework_enc`/`attendance_enc`, `form_submissions.answers_enc`/`decision_note_enc`, `form_events.note_enc`. Das Meldungsprotokoll `student_absence_events.detail` enthält keine Gründe, Vermerke oder Diagnosen; Benachrichtigungstexte enthalten keine sensiblen Einzelheiten („Neue Krankmeldung“ statt Diagnose).
  Abnahme: Zählabfrage „nicht leer und ohne Präfix `SM1`“ über alle genannten Spalten = 0 (auf frischer Instanz und nach Datenübernahme); Krankmeldung mit Grund „Grippe“ anlegen → `student_absence_events.detail`, `notifications` und `audit_log.details` enthalten das Wort nicht; Fremdes Kind abrufen → 404.
- **DAM-036** (P0, Status: offen) **Leistungswerte** (Note, Punkte, Prozent einer Person) werden in allen Tabellen gleich geschützt. Ist: verschlüsselt in `gb_entries`, `gb_finals`, `exam_results`, `assignment_submissions.grade_enc`; **Klartext** in `gb_source_results` (`points`, `max_points`, `grade`), `learning_attempts` (`points`, `max_points`, `percent`), `assignment_submissions` und `assignment_submission_versions` (`points`, `max_points`). Klartext bleibt nur die Kennung (`student_id`) für den Berechtigungsfilter.
  Abnahme: Datenbankauszug der genannten Spalten → Chiffrat mit Präfix `SM1` (bzw. leer); Lehrkraft sieht im Notenbuch nur Werte der eigenen Kurse, ein Elternkonto nur Werte des verknüpften Kindes bei freigegebenem Bereich; Berechnung des Notenvorschlags liefert dieselben Werte wie vor der Umstellung.
- **DAM-037** (P0, Status: Ist) Fehlerverhalten: „ungültig“ (Manipulation, falsches Zusatzdatum, falscher Schlüssel) und „nicht lesbar“ (unbekannte Schlüssel-ID); der Klartext wird nie zurückgegeben; Anzeige „[nicht lesbar]“ plus Protokolleintrag; Fehlermeldungen enthalten nie Schlüsselmaterial.
  Abnahme: Zeile mit Schlüssel-ID außerhalb des Rings lesen → Anzeige „[nicht lesbar]“ und ein Log-Eintrag; Suche im Log nach dem Wert eines Schlüssels aus dem Ring → 0 Treffer; die Anwendung bleibt für andere Zeilen benutzbar.
- **DAM-038** (P0, Status: Ist) Schlüsselring `SM_ENCRYPTION_KEYS`, Format `kid:Base64(32 Byte)` (Trenner Komma, Semikolon, Leerzeichen oder Zeilenumbruch); der **erste Eintrag ist aktiv**, weitere dienen nur zum Entschlüsseln; Schlüssel-ID 1–32 Zeichen (A–Z, a–z, 0–9, `_`, `-`), doppelte ID → Fehler, `dev` reserviert; Schlüsselgröße genau 32 Byte. Produktion: Pflicht, sonst bricht der Start ab. Entwicklung ohne Variable: Schlüssel `dev` aus `SM_SECRET_KEY` abgeleitet (HKDF-SHA256) mit Warnung; ändert sich `SM_SECRET_KEY`, sind diese Daten unlesbar.
  Abnahme: Produktion ohne Variable → Start bricht mit Konfigurationsfehler ab; Schlüssel mit 31 Byte oder doppelte ID oder ID `dev` in Produktion → Konfigurationsfehler; Entwicklung ohne Variable → Start mit Warnung, Statusseite zeigt Warnung „abgeleiteter Entwicklungsschlüssel“.
- **DAM-039** (P0, Status: Ist) Rotation: neuen Schlüssel vorn eintragen, Neustart, CLI `rotate-keys`: die Datenschlüssel werden neu umschlossen, Nutzdaten und AAD bleiben; bei Dateien wird nur der Kopf neu geschrieben (atomar ersetzt); `gen-key` erzeugt einen Schlüssel (Standard-ID `k` + Datum JJJJMMTT), `crypto-status` zeigt den Fingerabdruck (12 Hex-Zeichen, nicht umkehrbar).
  Abnahme: Nach `rotate-keys` trägt kein Chiffrat mehr die alte Schlüssel-ID (Zählabfrage = 0), alle Klartexte sind unverändert, Dateien lesbar, Zeilenzahlen gleich; bei fehlendem alten Schlüssel im Ring bleiben die betroffenen Zeilen unverändert und eine Warnung steht im Log.
- **DAM-040** (P1, Status: offen) **Vollständige Registrierung für die Rotation:** Jede Chiffrat-Spalte und jeder Chiffrat-Speicher ist registriert, auch `watch_log.query_enc`/`body_enc`/`changes_enc` (Ist: in den Quellen nicht als registriert belegt, Z6c P1) und die inneren Token im Planungsdokument (`Absence.reason`, Ist: bleiben bei der Rotation am alten Schlüssel, W5). Eine vollständige Neuverschlüsselung (neuer Datenschlüssel je Wert) ist für die Kompromittierung eines Hauptschlüssels vorgesehen; der Aufrufweg ist [unklar].
  Abnahme: Test findet jede Spalte mit Suffix `_enc`, jede Spalte mit Präfix `SM1` im Datenbestand und prüft die Registrierung; eine neue Chiffrat-Spalte ohne Registrierung → Test rot; nach `rotate-keys` Zählabfrage „Chiffrate mit alter Schlüssel-ID“ über alle Tabellen und das Planungsdokument = 0.
- **DAM-041** (P0, Status: Ist) Schlüssel-Aufbewahrung: Die Schlüssel (`SM_ENCRYPTION_KEYS`, `SM_SECRET_KEY`) liegen getrennt von den Sicherungen und dauerhaft (zusätzlich offline gesichert); ein alter Schlüssel wird erst entfernt, wenn alle Sicherungen, die ihn brauchen, abgelaufen sind; Verlust der Schlüssel bedeutet Verlust der verschlüsselten Daten, auch in allen Sicherungen. Ein Weg zur Wiederherstellung bei Schlüsselverlust besteht nicht [unklar: in den Quellen nicht beschrieben].
  Abnahme: Die Installationsanleitung enthält die Pflicht „Schlüssel getrennt und offline sichern“ und den Satz zum Datenverlust bei Schlüsselverlust; die Statusseite zeigt den Fingerabdruck des aktiven Schlüssels; eine Sicherung mit fehlendem Schlüssel meldet bei der Test-Wiederherstellung (DAM-114) „nicht lesbar“, nie Klartext.
- **DAM-042** (P0, Status: Ist) Chats sind **Ende-zu-Ende** im Browser verschlüsselt: Der Server speichert nur Chiffrat, Nonce (32 bis 40 Zeichen), öffentliche Gerätschlüssel, je Gerät verpackte Nachrichtenschlüssel und das im Browser verschlüsselte Schlüssel-Backup (abgeleitet aus Wiederherstellungscode oder Passwort mit PBKDF2-SHA-256, 1 Mio. Runden, Salt im Blob). Serverseitig verschlüsselt (Hauptschlüssel): `chats.title_enc`, `chat_reports.reason_enc`/`content_enc`, `chat_report_images.data_enc` und aus dem Postfach übernommene Kopien.
  Abnahme: Auszug von `chat_messages` zeigt keinen lesbaren Text; der Versuch, ein Nachrichten-Chiffrat mit dem Schlüsselring des Servers zu entschlüsseln, scheitert; die Auskunft zum Konto gibt nur das Chiffrat aus.
- **DAM-043** (P1, Status: offen) **Klartext mit Personenbezug (Klasse K) ist begrenzt und ausgewiesen:** erlaubt sind Kennungen für Filter und Zuordnung (`student_id`, `user_id`, `class_id`, `teacher_id`), Namen in Protokollen und Nachweisen (pseudonymisierbar, DAM-062, DAM-063) und technische Angaben (IP-Adresse, Browserkennung, Pfad ohne Abfrage); keine Freitexte, keine Gesundheitsdaten, keine Leistungswerte. Ist offen: Schutzbedarf der Klartextfelder `watch_log.ip`/`user_agent`/`path`/`username` (Z6c P6) und Kürzungsregel für IP-Adressen in Protokollen [unklar].
  Abnahme: Schema-Test: jede K-Spalte hat im Register Zweck, Begründung und eine Datenart mit Frist (DAM-076); eine K-Spalte vom Typ Freitext → Test rot.
- **DAM-044** (P1, Status: offen) Ein **maschinenlesbares Schema-Register** führt je Tabelle: Zweck, Datenart (Löschkonzept), Besitz-/Bezugsspalte, Löschverhalten, Eindeutigkeiten, Indizes und je Spalte die Klasse (DAM-045). Das Register ist Quelle für das Verzeichnis in Kapitel 2 und für die Schema-Tests; eine Tabelle ohne Eintrag lässt den Test scheitern. (Im Ist-Zustand führen Dokumentation und Verzeichnis dies von Hand.)
  Abnahme: Schema-Test vergleicht die Tabellen der migrierten Datenbank mit dem Register: Differenz = 0 in beide Richtungen; Verzeichnis (Kapitel 2) wird aus dem Register erzeugt und weicht nicht ab.
- **DAM-045** (P1, Status: offen) **Spaltenklassifizierung:** Jede Spalte hat genau eine Klasse: V (serverseitig verschlüsselt), E2E, H (Hash/HMAC/Prüfsumme), K (Klartext mit Personenbezug), F (Freitext), N (kein Personenbezug) und bei V/E2E/H das Bindungs- bzw. Verfahrensmuster.
  Abnahme: Schema-Test: Spalte ohne Klasse → rot; Spalte der Klasse V ohne Präfix im Datenbestand der Testdaten → rot; Spalte der Klasse H mit lesbarem Klartext-Token → rot.

### 4.4 Hashing und Geheimnisse

- **DAM-046** (P0, Status: Ist) Passwörter nur als scrypt-Hash: `SM_SCRYPT_N` Standard 32768 (2^15), Produktion mindestens 16384 (2^14), Zweierpotenz; r = 8, p = 1; Hash 32 Byte, Salt 16 Byte; Format `scrypt$n$r$p$salt$hash`. Startpasswörter (`account_initial_passwords.password_hash`): Kopie des Konto-Hashs, scrypt mit N = 2048 (2^11), das Passwort ist zufällig (ca. 60 Bit), nie Klartext.
  Abnahme: Neues Passwort setzen → gespeicherter Wert hat das Format mit N = 32768; `SM_SCRYPT_N` = 1000 in Produktion → Konfigurationsfehler; Suche nach dem Klartext-Passwort in Datenbank und Log → 0 Treffer.
- **DAM-047** (P0, Status: Ist) Token und Codes nur als **HMAC-SHA256** (Schlüssel `SM_SECRET_KEY`): Sitzungs- und API-Token (32 Byte Zufall, URL-sicher), Einmal-Codes (HMAC über Zweck, Konto und Code), Link-/Reset-Token, Kennung beim Zurücksetzen (`ident_hash`), Telefonnummer zur Suche (`phone_hash`), Kalender-Abo-Token (`users.ical_token`), Teilnahme-Token von Abstimmungen; CSRF-Token je Sitzung 24 Byte Zufall. Der Klartext wird nie gespeichert und steht in keiner Auskunft.
  Abnahme: API-Zugang anlegen → Klartext wird einmal angezeigt; in der Datenbank steht nur der Hash (Text, 64 Zeichen); Suche nach dem Klartext in Datenbank, Log und Audit → 0 Treffer; die Auskunft (`/me/export`) enthält keinen Token-Wert.
- **DAM-048** (P0, Status: Ist) `SM_SECRET_KEY` ist in Produktion Pflicht, mindestens 32 Zeichen; er dient auch als HMAC-Schlüssel für SSO-Status, Teilnahmekennungen im Lernbereich und OAuth-Status des Postfachs. Ein Wechsel macht alle Sitzungs-Hashes ungültig (alle Konten abgemeldet) und `phone_hash` unbrauchbar (Nummern müssen erneut gespeichert werden).
  Abnahme: Produktion mit 31 Zeichen → Start bricht ab; nach einem Wechsel antworten bestehende Sitzungen mit 401; die Betriebsdokumentation nennt die Folge für `phone_hash`.
- **DAM-049** (P0, Status: Ist) Geheimnisse Dritter und Zugangsdaten nur verschlüsselt und nie wieder angezeigt: `sso_providers.client_secret_enc`/`private_key_enc`, `mail_accounts.secret_enc` (JSON), SMTP-/SMS-Zugang, `users.totp_secret_enc` (20 Byte Zufall, Base32), `user_contacts.phone_enc` (E.164), `auth_codes.target_enc`, `letter_batches.data_enc`, `import_runs.report_enc`. Die Altspalte `users.totp_secret` (Klartext) entfällt im Neubau.
  Abnahme: API-Antworten und Oberfläche zeigen für diese Felder nur „gesetzt / nicht gesetzt“; Datenbankauszug nur Chiffrat; die Spalte `totp_secret` existiert im Neubau-Schema nicht; Antworten mit Zugangsdaten tragen `Cache-Control: no-store`.
- **DAM-050** (P1, Status: offen) Das **Verfahren jeder Hash-Spalte ist festgelegt und im Register geführt** (Ist unklar: `sessions.token_hash`, `api_tokens.token_hash`, `watch_log.session_hash`, `import_links.fingerprint`, `plan_proposals.signature`, `learning_survey_participants.token`; Prüfsummen `stored_files.sha256`, `import_runs.source_hash`, `plan_proposals.state_hash` sind SHA-256).
  Abnahme: Schema-Test: jede Spalte der Klasse H hat Verfahren (HMAC-SHA256 oder SHA-256), Schlüssel und Zweck; gleiche Eingabe → gleicher Hash; Verfahren und Länge der Spalte passen zusammen (Text, 64 Zeichen für 32 Byte hexadezimal).
- **DAM-051** (P0, Status: Ist) Anonymität bei Lernaktivitäten ist **technisch** erzwungen: Eine anonyme Abstimmung speichert nur einen Zähler je Antwort (`learning_poll_tally`) und keine Verknüpfung zwischen Stimme und Person; das Teilnahme-Token (HMAC aus Server-Geheimnis, Abstimmung und Konto) verhindert nur die Doppelabgabe; eine anonyme Umfrage speichert Antworten ohne `user_id` und den Zeitpunkt nur als Tagesdatum, Antworten werden nie personenbezogen ausgegeben.
  Abnahme: Anonyme Abstimmung mit drei Personen → Datenbank enthält drei Teilnahme-Token und die Zähler, aber keine Spalte, die Token oder Konto mit der Antwort verbindet; zweite Stimme derselben Person → abgelehnt; die Auskunft zeigt „(anonym gespeichert)“.
- **DAM-052** (P2, Status: Ist) Passwortprüfung gegen bekannte Datenlecks ist eine Einstellung, Standard **aus**; bei „an“ wird nur ein Hash-Präfix (SHA-1) übertragen, nie das Passwort.
  Abnahme: Einstellung aus → kein ausgehender Aufruf bei Passwortänderung; Einstellung an → die Anfrage enthält nur das Präfix, nicht den Hash und nicht das Passwort.

### 4.5 Zeitstempel und Datumsformate

- **DAM-053** (P0, Status: Ist) Alle **Zeitpunkte** (`created_at`, `updated_at`, `expires_at`, `deleted_at`, `at`, Zeitstempel in Protokollen) werden in **UTC** gespeichert (ohne Zeitzone); die Anzeige in Ortszeit ist Sache der Oberfläche; API-Ausgabe im Format ISO 8601 mit Endung `Z` (Beispiel `2026-10-05T08:00:00Z`).
  Abnahme: Ein Eintrag um 00:23 Uhr Ortszeit (Europa/Berlin, Sommerzeit) hat in der Datenbank 22:23 des Vortags; die API gibt ihn mit `Z` aus; Schema-Test: jede Zeitpunktspalte im Register hat den Typ „Zeitpunkt (UTC)“.
- **DAM-054** (P1, Status: Ist) Eingaben in Ortszeit (Europa/Berlin, z. B. das Update-Zeitfenster) werden in UTC gespeichert; ein Fensterbeginn in der Sommerzeit-Lücke rutscht nach vorn, Fenster dürfen über Mitternacht gehen.
  Abnahme: Fenster 23:00–02:00 → gilt über Mitternacht; Eingabe 02:30 am Tag der Umstellung auf Sommerzeit → gespeichert als gültiger Zeitpunkt nach der Lücke [unklar: genauer Ersatzwert], nie als früherer Zeitpunkt.
- **DAM-055** (P1, Status: Ist) Datumsfelder ohne Uhrzeit sind Text `JJJJ-MM-TT` (kein Zeitzonenbezug), Uhrzeiten `HH:MM`; Aufbewahrungsfristen rechnen in Tagen ab dem jeweiligen Zeitpunkt (Anlage, Austritt, Ablauf), bei kurzlebigen Daten in Stunden oder Minuten.
  Abnahme: Schema-Test: jede Datumsspalte hat Länge 10 und das Muster `JJJJ-MM-TT`; eine Frist von 30 Tagen ab Austritt am 2026-10-18 läuft am 2026-11-17 ab (feste Uhr).
- **DAM-056** (P2, Status: offen) Datumsfelder werden **beim Speichern geprüft** (Ist: ein ungültiges Datum führt erst bei der Auswertung zu einem Fehler; `date_to` vor `date_from` wirkt nie und meldet keinen Fehler; Z7 V5). Betrifft Abwesenheit, Ferien, Termine, Klausuren, Vertretungs-Entscheidungen, `school_year_start`, `birth_date`, `valid_from`.
  Abnahme: `2026-02-30` speichern → abgelehnt mit Klartextfehler; `date_to` vor `date_from` → abgelehnt oder Warnung [unklar: Entscheidung]; gültiges Datum → gespeichert.
- **DAM-057** (P1, Status: Ist) Datumsbezogene Fachregeln rechnen in **Ortszeit Europe/Berlin** (Konfiguration `TZ`), nicht in UTC: Volljährigkeit am Stichtag, Schultag, Stundenbeginn, Tageszusammenfassung der Benachrichtigungen (frühestens 7:00 Uhr Ortszeit).
  Abnahme: Person mit 18. Geburtstag am 18.10. ist am 18.10. um 00:30 Ortszeit (Sommerzeit; UTC-Datum noch der 17.10.) volljährig; die Tageszusammenfassung wird nicht vor 7:00 Uhr Ortszeit versendet (feste Uhr).
- **DAM-058** (P2, Status: offen) Audit-Abfragen mit Zeitzonen-Offset (`since`, `until`) werden nach UTC umgerechnet (Ist: nicht, U-65).
  Abnahme: `since=2026-10-05T08:00:00+02:00` liefert Einträge ab 06:00 UTC; ohne Offset gilt UTC.
- **DAM-059** (P1, Status: offen) Änderungs- und Anlagezeiten werden **zentral und automatisch** gesetzt: `created_at` ist Pflicht mit Standard „jetzt (UTC)“; `updated_at` wird bei **jeder** Änderung durch die Datenzugriffsschicht gesetzt, nicht durch den Aufrufer (Ist: keine Tabelle setzt Änderungszeiten automatisch, jede Stelle muss es selbst tun; Z6c P5).
  Abnahme: Schema-Test: jede Tabelle mit veränderbaren Zeilen hat `created_at` (Pflicht) und `updated_at`; Änderung über Oberfläche, API, Import und Wartung setzt `updated_at` jeweils auf den Änderungszeitpunkt (feste Uhr); kein Schreibpfad lässt den Wert unverändert.

### 4.6 Fremdschlüssel, Löschverhalten und Pseudonymisierung

- **DAM-060** (P1, Status: Ist) Jede Beziehung zwischen Tabellen hat genau eines von drei Löschverhalten, und das Verzeichnis (Kapitel 2) nennt es: **Kaskade** `[K]` (Zeile verschwindet mit der Elternzeile), **Feld leeren** `[N]` (Verweis wird NULL, Zeile bleibt) oder **ID-Verweis ohne Beziehung** `⇢` (nur Zahl oder Text). Verweise auf das Planungsdokument sind immer `⇢`.
  Abnahme: Schema-Test vergleicht jeden Fremdschlüssel und sein `ON DELETE`-Verhalten mit dem Register: `sessions.user_id` ist Kaskade, `messages.sender_id` wird leer, `student_absences.student_id` hat keinen Fremdschlüssel; jede Abweichung → rot.
- **DAM-061** (P0, Status: Ist) Konto löschen: Alle Zeilen mit Kaskade auf `users` verschwinden (Anmeldedaten, Kontakte, Verknüpfungen, Teilnahmen, Benachrichtigungen, Entwürfe, Blockierungen, Einstellungen, Abgaben, Fortschrittsmarken); Ersteller- und Absenderfelder werden NULL; eine Nachricht bleibt für die Empfänger lesbar, weil die Absender-ID nicht zur Bindung (AAD) gehört.
  Abnahme: Konto mit je einer Zeile in jeder Kaskadentabelle löschen → Zählabfrage über diese Tabellen = 0; `messages.sender_id` = NULL, Nachrichtentext für den Empfänger weiter lesbar; Administrator-Konten und das eigene Konto lassen sich nicht löschen (409).
- **DAM-062** (P0, Status: offen) **Anzeigenamen-Kopien** (`*_name`-Spalten im Klartext, z. B. `created_by_name`, `author_name`, `user_name`, `actor_name`, `graded_by_name`, `entered_by_name`, `set_by_name`, `handled_by_name`, `waived_by_name`, `locked_by_name`, `decided_by`, `undone_by`) bleiben im Ist-Zustand nach einer Kontolöschung stehen. Im Neubau wird der Name nicht kopiert, sondern über den Konto-Verweis angezeigt; wo ein Nachweis eine Kopie braucht, wird sie bei Kontolöschung pseudonymisiert (`gelöscht#<Konto-ID>`) oder entfernt.
  Abnahme: Konto „X“ (Anzeigename und Benutzername bekannt) mit Einträgen in allen Tabellen mit Namenskopie löschen → Suche nach Anzeigename und Benutzername in allen Tabellen (außer Sicherungen) = 0 Treffer; Verlauf zeigt „gelöscht#<Konto-ID>“ statt des Namens.
- **DAM-063** (P0, Status: Ist) Pseudonymisierung statt Löschung bei Protokollen: Audit `user_id` leer und `username` → `gelöscht#<Konto-ID>` (ebenso alle Einträge mit demselben Benutzernamen); Abwesenheitsereignisse `actor_id` leer, `actor_name` → `gelöscht#<Konto-ID>`; Planversionen `user_id` leer; Mitteilungen `author_id` leer; Krankmeldungen `reported_by` leer; Anmeldeversuche des Kontos werden gelöscht; Klassenbuch: nur der Anwesenheitseintrag der Person entfällt (Thema und Hausaufgabe bleiben); Beobachtungsprotokoll und Kennzeichen werden bei Kontolöschung sofort gelöscht; anonym gespeicherte Umfrage-Antworten bleiben.
  Abnahme: Je Zeile der Aufzählung eine Zählabfrage vor und nach der Kontolöschung mit dem erwarteten Ergebnis; der Audit-Eintrag der Löschung selbst bleibt bis zur Audit-Frist (DAM-083).
- **DAM-064** (P0, Status: offen) **Chat-Tabellen:** Für `chat_members`, `chat_messages`, `chat_message_keys`, `chat_reports`, `chat_attachments`, `chat_devices`, `chat_link_requests`, `chat_key_backups`, `chat_report_images` ist das Löschverhalten verbindlich festgelegt (Ist: keine Fremdschlüssel untereinander; die Bereinigung leistet allein das Löschkonzept, Datenart `chats`). Vorgabe: Fremdschlüssel mit Kaskade (Chat → Mitglieder, Nachrichten, Anhänge, Meldungen; Gerät → Schlüssel, Verknüpfungsanfragen) **oder** eine lückenlose Bereinigung mit Test; Einzelchats werden ganz entfernt, Gruppen ohne Mitglieder entfernt.
  Abnahme: Chat löschen → Zählabfrage mit seiner `chat_id` über alle neun Tabellen = 0; Konto eines Mitglieds löschen → Geräte, Schlüssel-Backup, Nachrichtenschlüssel, eigene Nachrichten, Anhänge und eigene Meldungen samt Bildern weg; verwaiste Zeilen (ohne vorhandenen Chat oder ohne vorhandenes Konto/Gerät) = 0.
- **DAM-065** (P1, Status: offen) Bedingungen „genau eines von“ werden von der Datenbank erzwungen (Ist: nicht erzwungen): `channel_group_gates` (`item_id` **oder** `folder_id`), `assignment_extensions` (eine Person **oder** eine Gruppe).
  Abnahme: Zeile mit beiden oder keinem der Verweise einfügen → abgelehnt (Datenbankfehler, in der API 422); Zeile mit genau einem → angelegt.
- **DAM-066** (P1, Status: Ist) **Weiches Löschen:** `channel_items` und `channel_folders` (Papierkorb mit `deleted_at`, `deleted_by`, `trash_group`; Frist `trash_retention_days`, Standard 30 Tage, Einstellung 1 bis 365), `channel_posts`, `stored_files` (`deleted_at`, 30 Tage), `student_documents` (`withdrawn_at`; Frist bis zum endgültigen Löschen [unklar]), `messages` (`removed_at` durch die Moderation; der ausgeblendete Text bleibt verschlüsselt als Beleg bis zur Aufbewahrungsfrist). Normale Abfragen blenden diese Zeilen aus; endgültig entfernt wird nach der Frist.
  Abnahme: Element löschen → in der Liste weg, Zeile mit `deleted_at` vorhanden, im Papierkorb sichtbar; nach 30 Tagen und einem Wartungslauf Zeile weg (feste Uhr); Wiederherstellen innerhalb der Frist inkl. Namensfolge „(2)“ bei gleichnamigem Ordner; direkter Abruf des gelöschten Elements außerhalb des Papierkorbs → 404.
- **DAM-067** (P1, Status: Ist) **Nur anhängen:** `student_absence_events`, `plan_proposal_log`, `comp_assessments`, `form_versions`, `audit_log`, `retention_log` erlauben kein Ändern und kein Löschen einzelner Zeilen durch die Anwendung; Löschung nur durch Frist oder Löschkonzept; Entscheidungen im Plan-Verlauf und Fassungen einer Formularvorlage sind unveränderlich.
  Abnahme: Es gibt für diese Tabellen keinen Schreibpfad außer Einfügen und der Fristbereinigung (Test über alle Routen und Dienste); ein Änderungsversuch über die API → 404 bzw. 405; eine Fassung `form_versions` mit eingereichten Formularen bleibt nach einer Vorlagenänderung unverändert.
- **DAM-068** (P1, Status: Ist) Verweise auf das Planungsdokument (`student_id`, `class_id`, `teacher_id`, `course_id`, `exam_id`) haben keinen Fremdschlüssel; die Integrität stellt das Löschkonzept her: Person nicht mehr im Planungsdokument → Warteliste → Fristen. Ein **leeres** Schülerverzeichnis wird nie als „alle ausgetreten“ gewertet.
  Abnahme: Schülerverzeichnis leeren (Fehlimport) → keine Wartelisten-Einträge, keine Kontosperren; Schüler/in entfernen → Eintrag `wartend`, Konten gesperrt, Sitzungen beendet; Rückkehr ins Planungsdokument → Eintrag entfernt, Konten entsperrt, Planverlauf unberührt.
- **DAM-069** (P2, Status: offen) Verweise ohne Fremdschlüssel haben beim Löschen des Ziels eine **festgelegte Folge** (leeren oder mitlöschen), per Anwendungslogik mit Test, und Dateiverweise sind einheitlich (Ist: `student_documents.file_id` hat einen Fremdschlüssel auf `stored_files`, `student_support.file_ids` und `register_lessons.checked_by` nicht; `conversations.mail_account_id` ohne Fremdschlüssel, Folge offen; generische Verweise `completion_*.element_id`, `comp_links.item_id`). Ist belegt: Kursraum gelöscht → Lernfortschritt-Zeilen über `channel_id` mitgelöscht; Element endgültig gelöscht → Lernfortschritt-Zeilen per Logik entfernt.
  Abnahme: Element endgültig löschen → Zeilen in `completion_rules`, `completion_marks`, `availability_rules` mit seiner `element_id` = 0; Kursraum löschen → alle Zeilen mit seiner `channel_id` = 0; Datei löschen → jeder Verweis darauf ist NULL oder entfernt (Zählabfrage über alle Dateiverweise); verwaiste Verweise insgesamt = 0.

### 4.7 Eindeutigkeiten und Integrität

Anlage zu DAM-070: Eindeutigkeiten aus dem Ist-Zustand (Spalten maßgeblich).

| Tabelle | Eindeutig über |
|---|---|
| `users` | `username`; `oidc_sub`; `ical_token` |
| `sessions`, `api_tokens` | `token_hash` |
| `user_identities` | (`provider`,`subject`); (`user_id`,`provider`) |
| `login_policy_rules` | (`scope`,`scope_ref`,`audience`) |
| `custom_roles`, `branches` | Name |
| `parent_links` | (`parent_user_id`,`student_id`) |
| `parent_access` | (`student_id`,`area`) |
| `register_lessons` | (`date`,`lesson_id`,`period`,`part`) |
| `exam_results`, `exam_makeups` | (`exam_id`,`student_id`) |
| `gb_books` | (`course_id`,`part`,`term`) |
| `gb_entries` | (`item_id`,`student_id`) |
| `gb_source_results` | (`source_type`,`source_id`,`student_id`) |
| `gb_source_links` | (`book_id`,`source_type`,`source_id`) |
| `comp_links` | (`competency_id`,`item_type`,`item_id`) |
| `comp_badge_awards` | (`badge_id`,`student_id`) |
| `channels` | (`kind`,`ref`) |
| `assignment_settings` | `item_id` (1:1 zur Aufgabe) |
| `assignment_submissions` | (`item_id`,`student_user_id`) |
| `assignment_submission_versions` | (`submission_id`,`attempt`) |
| `channel_group_members` | (`set_id`,`user_id`) |
| `channel_reads` | (`channel_id`,`user_id`) |
| `channel_item_views` | (`item_id`,`user_id`) |
| `learning_polls` | `chat_message_id` |
| `learning_poll_participants` | (`poll_id`,`user_id`); (`poll_id`,`token`) |
| `learning_poll_votes` | (`poll_id`,`user_id`,`option_index`) |
| `learning_poll_tally` | (`poll_id`,`option_index`) |
| `learning_survey_participants` | (`survey_id`,`user_id`); (`survey_id`,`token`) |
| `learning_attempts` | (`test_id`,`user_id`,`number`) |
| `mail_accounts` | (`user_id`,`email`) |
| `chats` | `direct_key` |
| `chat_members` | (`chat_id`,`user_id`) |
| `chat_message_keys` | (`message_id`,`device_id`) |
| `notifications` | (`user_id`,`dedupe_key`) |
| `notification_prefs` | (`user_id`,`kind`) |
| `form_versions` | (`template_id`,`version`) |
| `retention_leavers` | `student_id` |
| `import_links` | (`system`,`instance`,`kind`,`source_key`) |

- **DAM-070** (P1, Status: Ist) Alle Eindeutigkeiten der Anlage sind **Datenbank-Constraints**, nicht nur Anwendungslogik; ein Duplikat wird abgelehnt (in der API als 409 oder 422 mit Klartextfehler).
  Abnahme: Je Zeile der Anlage ein Test, der ein Duplikat einfügt → abgelehnt, und einen Fall mit einem unterscheidenden Spaltenwert → angenommen; Schema-Test: jede Eindeutigkeit der Anlage steht im Register.
- **DAM-071** (P2, Status: offen) Namensschema der Constraints stimmt mit den Spalten überein (Ist: `uq_notifications_user_id` umfasst (`user_id`,`dedupe_key`), `uq_parent_access_student_id` umfasst (`student_id`,`area`); Z6b §5 Nr. 19); Schema `uq_<tabelle>_<spalten>`, `ix_<tabelle>_<spalten>`, `fk_<tabelle>_<spalte>`.
  Abnahme: Schema-Test liest jeden Constraint- und Indexnamen und vergleicht ihn mit den enthaltenen Spalten; Abweichung → rot.
- **DAM-072** (P2, Status: offen) Je Konto gibt es höchstens **ein Standard-E-Mail-Konto** (`mail_accounts.is_default`; Ist nicht eindeutig festgelegt, Z6b §5 Nr. 13).
  Abnahme: Zweites Konto als Standard setzen → das erste verliert die Kennzeichnung oder die Aktion wird mit Klartextfehler abgelehnt [unklar: Entscheidung]; Zählabfrage „Konten mit mehr als einem Standard“ = 0.
- **DAM-073** (P1, Status: Ist) Doppelsende-Schutz (`send_idempotency`): Ein Schlüssel je Konto und Bereich wird genau einmal angenommen; eine Wiederholung liefert die bereits gesendete Nachricht. Aufbewahrungsdauer der Zeilen [unklar], im Neubau festzulegen (DAM-077).
  Abnahme: Zweimal derselbe Schlüssel → genau eine Nachricht, beide Antworten nennen dieselbe Nachrichtenkennung; anderer Schlüssel → neue Nachricht.
- **DAM-074** (P1, Status: Ist) Selbsttests: höchstens ein **laufender Versuch** je Test und Konto; die Versuchsnummer beginnt bei 1 und ist je Test und Konto eindeutig; spätere Änderungen an der Fragensammlung ändern kein Ergebnis eines begonnenen Versuchs (Fragenabbild `snapshot_enc` zum Start).
  Abnahme: Zweiten Versuch starten, solange einer läuft → abgelehnt; Frage nach Versuchsbeginn ändern → Ergebnis und Anzeige des Versuchs unverändert.
- **DAM-075** (P2, Status: Ist) Import ist wiederholbar: `import_links` ist über (`system`,`instance`,`kind`,`source_key`) eindeutig; Trockenläufe werden nicht gespeichert; unveränderte Elemente werden nicht neu geschrieben; die Rücknahme entfernt alle Objekte, die der Lauf angelegt hat.
  Abnahme: Dieselbe Datei zweimal importieren → beim zweiten Lauf 0 neue Datensätze und 0 geänderte; Vorschau lässt alle Zeilenzahlen unverändert; Rücknahme → Zählabfrage der vom Lauf angelegten Objekte = 0.

### 4.8 Aufbewahrung, Löschung und Protokolle

- **DAM-076** (P0, Status: offen) **Jede Tabelle mit personenbezogenen Daten gehört zu einer Datenart mit Frist** im Löschkonzept (Kapitel 1.10) oder ist im Register als Konfiguration bzw. Zustand ohne Personenbezug ausgewiesen. Ist: für mehrere Tabellen fehlt Datenart und Frist (DAM-077).
  Abnahme: Schema-Test: jede Tabelle mit mindestens einer Spalte der Klassen V, E2E, K oder F hat im Register eine Datenart oder eine begründete Ausnahme; eine Tabelle ohne Zuordnung → rot; die Löschvorschau zeigt jede Datenart.
- **DAM-077** (P0, Status: offen) **Lücken im Datenarten-Katalog schließen** (Ist: keine Datenart und keine Frist) für: `channel_items`/`channel_posts`/`channel_folders` (Kursraum-Inhalte, bisher nur Papierkorb), `teacher_change_requests` (in der Auskunft, ohne Löschregel), `user_contacts`, `user_identities`, `import_runs` und `import_links`, `plan_proposals`/`plan_proposal_log`/`plan_snapshots`, `mail_accounts`, `announcements` (bisher nur Verfasser pseudonymisiert), `exam_makeup_dates`, `send_idempotency`, Zeilen von `notifications_outbox` (nur der Inhalt wird nach Zustellung geleert), `student_documents` nach `withdrawn_at`. Die Fristwerte legt der Betreiber fest [unklar: Entscheidung E-35 in Datei 10, Landesrecht in Datei 06]; die Datenarten und das Löschverfahren je Tabelle sind Teil dieser Anforderung.
  Abnahme: Für jede genannte Tabelle zeigt die Löschvorschau eine Datenart; Person tritt aus, Frist verstreicht (feste Uhr) → Zählabfrage der Zeilen mit Bezug zur Person = 0 (bei `kind` = anonymisieren: Personenbezug entfernt); Kontolöschung hinterlässt keine Zeile mit Konto-Bezug außer den ausgewiesenen pseudonymisierten Protokollen.
- **DAM-078** (P0, Status: Ist) Wirksame Frist nach Austritt je Datenart = **Maximum aus eigener Frist und Wartelisten-Frist** (`grace_days`, Standard 30 Tage); alle Fristen sind einstellbar von 0 bis 3650 Tage (`<datenart>.days`, `<datenart>.age_days`; 0 = aus); der Schalter `auto_purge` (Standard an) steuert die Fristlöschung nach Austritt, die Warteliste wird trotzdem abgeglichen, Alters-Fristen laufen unabhängig.
  Abnahme: `grace_days` = 30 und `absences.days` = 10 → Löschung frühestens 30 Tage nach Austritt; Wert 5000 → gespeichert als 3650; `auto_purge` = aus → auch „Jetzt ausführen“ löscht nichts nach Austritt, die Warteliste wächst weiter, Alters-Fristen laufen (feste Uhr).
- **DAM-079** (P0, Status: Ist) Die **Datenarten, Tabellen und Standardfristen aus Kapitel 1.10** sind der Soll-Zustand einer frischen Instanz (u. a. `absences` 30 Tage nach Austritt/365 laufend, `documents` 30/400, `support` 30, `forms` 90/400, `exam_results` 180, `gradebook` 180, `competencies` 180, `attendance` 365 anonymisieren, `submissions` 90, `learning` 90, `progress` 90, `files` 30, `notifications` 30/90, `messages` 30/365, `chats` 30, `parents` 30, `accounts` 30 zuletzt, `history` 30 anonymisieren, `api_log` 30/90, `watch_log` 30/180).
  Abnahme: Auf frischer Instanz zeigt die Einstellungsseite genau diese Werte; je Datenart ein Test mit fester Uhr: am Tag Frist − 1 ist die Zeile vorhanden, nach Fristablauf und Wartungslauf nicht mehr; die Vorschau „Was würde gelöscht“ verändert nichts.
- **DAM-080** (P0, Status: Ist) Löschverfahren: **hart** (endgültig), außer „anonymisieren“ (`attendance`: nur der Eintrag der Person im Anwesenheitsfeld; `history`: Name in Versionstexten → „[gelöscht]“, Ziele `student:<ID>` → `student:gelöscht`, Details entfernt). Reihenfolge nach Ordnungszahl: Gesundheit 10–13, Leistung 20–23, Unterricht 30–32, Kommunikation 40–43, Eltern 50, Planverlauf 800, API-Protokoll 810, Beobachtung 820, Schüler-Konten 900 **zuletzt** (erst wenn alle anderen Datenarten der Person erledigt sind). Blöcke: `absences` 500 je Lauf, `documents` und `forms` höchstens 5000 je Lauf. Ein Fehler einer Datenart lässt sie offen (Wiederholung im nächsten Lauf), die übrigen laufen weiter, die Person wird nicht abgeschlossen, der Fehler geht ins Fehlerprotokoll. Administrator-Konten werden nie gelöscht.
  Abnahme: Fehler in einer Datenart erzwungen → übrige Datenarten gelöscht, Person nicht `erledigt`, Fehlerprotokoll-Eintrag, nächster Lauf wiederholt und schließt ab; 12.000 Dokumente → drei Läufe (5000, 5000, 2000); das Konto wird nie vor einer noch offenen Datenart gelöscht; Administrator-Konto bleibt.
- **DAM-081** (P0, Status: Ist) Löschprotokoll `retention_log`: Datenart, Anzahl, Zeitpunkt, Modus (`automatik`, `frist`, `sofort`), Aktion (`geloescht`, `anonymisiert`, `abgeschlossen`), Akteur, Bezug (`student:<ID>` oder `user:<ID>`), Anlass (höchstens 200 Zeichen); **keine Inhalte**; Aufbewahrung 1095 Tage (`log_days`; 0 = nie).
  Abnahme: Eine Löschung erzeugt Einträge ohne Namen und ohne Inhalte (Stichprobe); Eintrag älter als 1095 Tage ist nach dem Lauf weg (feste Uhr); `log_days` = 0 → bleibt.
- **DAM-082** (P0, Status: Ist) Warteliste `retention_leavers`: Status `wartend`/`erledigt`, Quelle `abgleich`/`planung`; der Name liegt verschlüsselt (`name_enc`, Bindung `retention_leavers.name:<ID>`) und wird beim Abschluss geleert; die Personen-ID bleibt bis 1095 Tage nach Abschluss; bei Austritt werden alle Konten der Person gesperrt und ihre Sitzungen beendet; Rückkehr oder „Austritt zurücknehmen“ (409, wenn die Person nicht im Planungsdokument steht; 404, wenn kein offener Austritt) entsperrt; ein erneuter Austritt nach Abschluss setzt den Eintrag zurück.
  Abnahme: Ablauf Austritt → Warteliste (Name nur als Chiffrat) → Fristlauf → `erledigt` mit leerem Namen; Rücknahme ohne offenen Austritt → 404; Rücknahme bei fehlender Person im Planungsdokument → 409.
- **DAM-083** (P0, Status: Ist) Nach einer Löschung bleibt **nur** folgender Restbestand, abschließend: Audit-Eintrag `privacy.erase` (Personen-ID im Ziel, IP-Adresse, Länge und verschlüsselter Grund) bis zur Audit-Frist (365 Tage); Löschprotokoll (Personen-ID, 1095 Tage); Warteliste (ID, 1095 Tage nach Abschluss); Nachrichten anderer Personen bis zu deren Frist; anonym gespeicherte Umfrage-Antworten; Thema und Hausaufgabe der Klassenbuch-Stunden; Sicherungen bis zur Rotation (DAM-116).
  Abnahme: Nach Art.-17-Löschung einer Test-Person: Suche nach Name, Benutzername, E-Mail, Kennung in allen Tabellen → Treffer nur in den genannten Resten (Kennung) und nie als Name; der Löschgrund ist nur als Chiffrat vorhanden.
- **DAM-084** (P0, Status: Ist) Kurzlebige Zugangsdaten und Sitzungen: Sitzungen Schüler/innen und Eltern 7 Tage Inaktivität (`SM_SESSION_IDLE_MINUTES` = 10080), Personal 12 Stunden Inaktivität (Standard 720 Minuten, einstellbar 15 Minuten bis 7 Tage, nie länger als der Schüler-Wert), absolut 30 Tage (`SM_SESSION_MAX_DAYS`); persönliche API-Tokens ohne Umfang: Löschung sofort nach Ablauf, Zugänge mit Umfang 30 Tage nach Ablauf (Gültigkeit `expires_days` Pflicht, nie länger als die des ausstellenden Tokens); `auth_codes` gültig 15 Minuten (`SM_AUTH_CODE_MINUTES`), höchstens 5 Fehlversuche je Code, gelöscht 1 Stunde nach Ablauf; `login_attempts` 30 Tage.
  Abnahme: Test mit fester Uhr je Zeile: Sitzung eines Schülers nach 7 Tagen Inaktivität → 401, Sitzung einer Lehrkraft nach 12 Stunden → 401, jede Sitzung nach 30 Tagen; Code nach 15 Minuten ungültig, sechster Fehlversuch gesperrt, Zeile 1 Stunde nach Ablauf gelöscht; Token ohne Umfang nach Ablauf sofort weg, mit Umfang erst nach 30 Tagen; Anmeldeversuch älter als 30 Tage weg.
- **DAM-085** (P1, Status: Ist) Weitere kurzlebige Daten: `letter_batches` 60 Minuten (`SM_LETTER_BATCH_MINUTES`, 1 bis 1440), danach Löschung, Zugriff liefert 410; `account_initial_passwords` Frist 14 Tage (Einstellung 1 bis 90), Zeile verschwindet beim Passwortwechsel und bei Kontolöschung; `stored_files` Uploads ohne Anhang 24 Stunden, weich gelöscht 30 Tage, Temp-Reste älter als 6 Stunden; `chat_attachments` lose (nicht gesendete) Uploads 24 Stunden; Test-Postausgang (Entwicklung) 24 Stunden; Inhalt von `notifications_outbox` (E-Mail, SMS) nach Zustellung geleert, Frist der Zeilen [unklar]; Kursraum-Papierkorb 30 Tage.
  Abnahme: Test mit fester Uhr je Zeile: Stapel nach 61 Minuten → 410 und Zeile weg; Startpasswort nach 14 Tagen nicht mehr nutzbar; Upload ohne Anhang nach 25 Stunden weg; zugestellte Benachrichtigung hat leeren Inhalt.
- **DAM-086** (P1, Status: Ist) Protokoll-Fristen: `audit_log` 365 Tage (`audit_days`, Startwert `SM_AUDIT_RETENTION_DAYS`; 0 = nie; die Löschung erzeugt einen Löschprotokoll-Eintrag „audit“ mit der Anzahl), `error_log` 30 Tage und höchstens 1000 Zeilen (älteste zuerst), `retention_log` 1095 Tage, `watch_log` 180 Tage (30 Tage nach Austritt, bei Kontolöschung sofort), `api_token_log` 90 Tage (30 Tage nach Austritt; Obergrenze je Zugang [unklar]).
  Abnahme: 1001 Fehlerzeilen → nach dem Lauf 1000, die älteste fehlt; Audit-Eintrag mit 366 Tagen Alter weg und Löschprotokoll „audit“ mit Anzahl vorhanden; `audit_days` = 0 → nichts gelöscht (feste Uhr).
- **DAM-087** (P0, Status: Ist) **Protokolle enthalten keine Inhalte:** `audit_log.details` nur, was der Aufrufer übergibt (keine Passwörter, Codes, Telefonnummern, Token-Werte); Anfragekörper, Abfrageparameter und Vorher/Nachher-Werte nur bei beobachteten Konten (geschwärzt und verschlüsselt, Obergrenzen Körper 32.000 Byte, Abfrage 2000 Zeichen, einzelne Textwerte 4000 Zeichen, Listen 200 Einträge, Kürzungsvermerk); Löschgründe nur als Länge und verschlüsselter Grund (höchstens 200 Zeichen); Ziel höchstens 200 Zeichen; Fehlerprotokoll: Meldung höchstens 2000 Zeichen, Stacktrace höchstens 8000 Zeichen, Pfad ohne Abfrage mit maskierten Kennungen; Live-Ereignisse tragen keine Inhalte.
  Abnahme: Krankmeldung, Passwortänderung und Nachricht senden → Stichprobe von `audit_log.details`, `error_log` und Ereignisstrom enthält weder Grund, Passwort, Text noch Namen von Kindern; beobachtetes Konto: Körper mit 40.000 Byte → gekürzt mit Vermerk, Inhalt verschlüsselt.
- **DAM-088** (P0, Status: offen) **Jede schreibende Aktion wird protokolliert** (Aktion `Bereich.Verb`, Ziel, IP; ohne Inhalte). Ist: schreibende Aktionen teils ohne Protokoll (U-67); Audit-Einträge zu Krankmeldungen sind für die Administration sichtbar (U-111, A-58). Im Neubau sind Audit-Einträge zu Krankmeldungen nur für Konten mit der Berechtigung für Krankmeldungen abrufbar; zulässige Ausnahmen (z. B. Löschen eigener Benachrichtigungen, „gelesen“-Markierungen) stehen in einer Ausnahmeliste (Entscheidung E-12 in Datei 10).
  Abnahme: Automatisierte Routenliste: jede schreibende Route außerhalb der Ausnahmeliste erzeugt genau einen Audit-Eintrag; Administrator ohne Berechtigung für Krankmeldungen ruft `GET /audit` → Einträge zu Krankmeldungen fehlen; Eintrag einer Ausnahme erscheint nicht.
- **DAM-089** (P1, Status: offen) **Wartung:** Hauptlauf alle `SM_MAINTENANCE_INTERVAL` (Standard 3600 Sekunden, erster Lauf sofort beim Start), Stufen in fester Reihenfolge (Sitzungen, Tokens, Anmeldeversuche, Dateiablage, Dokumente, Formulare, Kontakt-Codes, Zugangsbriefe, Benachrichtigungen, Kursraum-Papierkorb, Fehlerprotokoll, Löschkonzept), jede Stufe mit eigener Fehlerbehandlung. Neubau: Die Postfach-Aufbewahrung ist eine **eigene Stufe** des Hauptlaufs (Ist: Notbehelf, höchstens alle 6 Stunden beim Abruf des Ungelesen-Zählers); Intervall 0 bedeutet eindeutig „aus“ (Ist: die Schleife läuft trotz 0 mindestens alle 5 Sekunden weiter). Offen gemeldete Nachrichten bleiben bis zur Klärung.
  Abnahme: `SM_MAINTENANCE_INTERVAL` = 0 → kein Wartungslauf, auch kein Postfach-Lauf; Postfach-Nachricht mit 366 Tagen Alter ist nach dem nächsten Hauptlauf weg, ohne dass jemand den Ungelesen-Zähler abruft; offen gemeldete Nachricht bleibt; Fehler in einer Stufe stoppt die übrigen nicht (Fehlerprotokoll-Eintrag).
- **DAM-090** (P1, Status: Ist) **Auskunft (Art. 15, 20) ist vollständig:** Jede Tabelle mit Personenbezug erscheint in der Auskunft (JSON bzw. ZIP mit `daten.json` und lesbarer Übersicht); Ausnahme `watch_log` (organisatorisch über CSV-Export der Verwaltungsseite). Obergrenzen: 1000 Anmeldeversuche, 5000 Audit-Einträge, 5000 Benachrichtigungen, 5000 API-Protokolleinträge; Förderdaten nur für minderjährige Kinder; Eltern nur für freigegebene Bereiche; Abschnitte, die nicht gelesen werden konnten, stehen unter `hinweise`, die Auskunft bricht bei Einzelfehlern nicht ab.
  Abnahme: Schema-Test: im Register trägt jede Tabelle mit Personenbezug „in Auskunft: ja“ oder eine begründete Ausnahme; Auskunft eines Test-Kontos enthält Daten aus jeder Datenart mit Zeilen; Elternkonto erhält ohne Freigabe des Bereichs Noten keine Noten des Kindes; Person ohne Konto → 404 mit Hinweis auf manuelle Auskunft.

### 4.9 Migrationen und Datenübernahme

- **DAM-091** (P0, Status: Ist) Das Schema ändert sich **ausschließlich über versionierte Migrationen**, linear und lückenlos (keine parallelen Ketten); ein automatischer Test vergleicht das Datenmodell mit dem migrierten Schema.
  Abnahme: Leere Datenbank durch alle Migrationen → Schema identisch mit dem Modell (Test grün); eine von Hand geänderte Spalte ohne Migration → Test rot; zwei Migrationen mit demselben Vorgänger → Test rot.
- **DAM-092** (P1, Status: Ist) Start-Reihenfolge: Konfiguration prüfen → Schema automatisch migrieren → Erststart-Prüfung (Erst-Administrator) → Hintergrundaufgaben. Manuell: CLI `migrate`. Die Statusseite zeigt den Datenbankstand („aktuell“ oder Hinweis auf eine Migration); der Migrationsstand (Kapitel 2a.2) ist Teil jeder Sicherung.
  Abnahme: Instanz mit älterem Schema starten → Migration läuft vor dem Start der Hintergrundaufgaben, Statusseite zeigt „aktuell“; `migrate` auf aktuellem Stand ändert nichts (Zeilenzahlen und Schema gleich).
- **DAM-093** (P1, Status: offen) **Migration schlägt fehl:** Ist nicht beschrieben (I8). Neubau [Vorschlag]: Die Migration läuft, soweit die Datenbank es erlaubt, in einer Transaktion; bei Fehler bricht der Start ab, der Schemastand bleibt unverändert, es starten keine Hintergrundaufgaben, Fehler und Stand stehen im Log; bei mehreren Knoten migriert genau ein Knoten (Ist: der Migrationslauf gilt bei mehreren Knoten als Konfliktpunkt).
  Abnahme: Migration mit künstlich erzeugtem Fehler → Prozess endet mit Fehlercode, Schemastand und Zeilenzahlen unverändert; zwei Knoten gleichzeitig gestartet → die Migration läuft genau einmal, der zweite Knoten wartet oder startet erst danach.
- **DAM-094** (P0, Status: Ist) **Expand/Contract:** Jede Schemaänderung arbeitet mit der Vorgängerversion zusammen (rollendes Update, Rücknahme): erst erweitern (neue Spalten optional oder mit Standardwert, neue Tabellen), später entfernen. Beispiel im Ist: Bei `learning_poll_participants` bleibt die alte Eindeutigkeit (`poll_id`,`user_id`), damit der alte Code beim rollenden Update weiter schreiben kann.
  Abnahme: Der Vorgänger-Programmstand läuft gegen das Schema des neuen Standes: alle Lese- und Schreibpfade des Vorgängers funktionieren; eine Migration, die eine vom Vorgänger genutzte Spalte im selben Release entfernt oder umbenennt, macht das Prüfskript (DAM-095) rot.
- **DAM-095** (P1, Status: Ist) Das Prüfskript läuft vor jeder Freigabe und muss sauber sein; Ausnahmen werden bewusst als „breaking“ freigegeben und im Release gekennzeichnet (Angabe, ob eine Datenbankänderung enthalten ist).
  Abnahme: Release ohne Angabe zur Datenbankänderung → Freigabeprüfung rot; „breaking“-Migration ohne Kennzeichnung → rot; Prüfskript mit Fund → keine Freigabe.
- **DAM-096** (P1, Status: Ist) Planungsdaten kommen mit Standardwerten aus: alte Dokumente bleiben ladbar; ein neues Feld ist optional oder hat einen Standardwert.
  Abnahme: Test mit gespeicherten Versionen jeder früheren Formatstufe (Fixtures) → jede lädt im aktuellen Stand ohne Fehler und mit Standardwerten für neue Felder; ein neues Pflichtfeld ohne Standardwert → Test rot.
- **DAM-097** (P0, Status: Ist) **Schema-Falle:** Tabellen mit kaskadierenden Fremdschlüsseln (`users`, `channel_folders`) werden nie per Tabellen-Neuaufbau umgebaut (der SQLite-Tabellenumbau löscht abhängige Zeilen); erlaubt sind Hinzufügen und Erstellen; jede Ausnahme braucht einen Prüfplan und einen Regressionstest.
  Abnahme: Test füllt `users` und alle abhängigen Tabellen, führt alle Migrationen aus → Zeilenzahl jeder abhängigen Tabelle vorher = nachher; ein Neuaufbau von `users` ohne Prüfplan → Prüfskript rot.
- **DAM-098** (P1, Status: Ist) Datenumbauten, die Werte umschreiben (z. B. Verschlüsselungsumstellung), werden von Hand geprüft: vorher Sicherung und Probelauf auf einer Kopie der Echtdaten; der Umbau ist wiederholbar (ein zweiter Lauf ändert nichts).
  Abnahme: Umbau zweimal hintereinander → der zweite Lauf ändert 0 Zeilen; die Statusseite zeigt eine Sicherung, die jünger ist als der Umbau-Beginn; Probelauf auf der Kopie liefert gleiche Zählwerte wie Quelle.
- **DAM-099** (P2, Status: offen) Jede Migration, die Daten umschreibt, hat eine **Rücknahme-Migration** und einen Downgrade-Test (Ist: Downgrade-Tests nur für einzelne Migrationen belegt).
  Abnahme: Test: Migration anwenden, Rücknahme ausführen → Schema und Zeilenzahlen entsprechen dem Stand vor der Migration; fehlt die Rücknahme → Prüfskript rot.
- **DAM-100** (P1, Status: offen) Die **Anbieter-Tabellen** (13, Kapitel 2.17) laufen unter denselben Migrationsregeln mit Migrationshistorie (Ist: keine Historie; Änderungen laufen über eine eigene Anpassung beim Start, Beispiel Anzeige-Kopie der Lizenzschlüssel seit 16.10.2026).
  Abnahme: Anbieter-Datenbank leer durch Migrationen → Schema = Modell; der Migrationsstand ist abfragbar; kein Startskript ändert das Schema außerhalb der Migrationen (Schema-Test).
- **DAM-101** (P1, Status: offen) **Alt-Spalten entfallen im Neubau** (Kapitel 1.9): `users.totp_secret`, `channel_folders.hidden` und `visibility` = NULL (nur die Sichtbarkeitswerte `visible`, `hidden`, `scheduled`, `lesson` gelten), `chat_messages.legacy_body_enc`, `legacy_source_message_id`, `legacy_source_conversation_id`, `chats.only_admins_post` (abgeleitet aus `post_mode`), unverschlüsselter Altbestand der Planversionen.
  Abnahme: Das Neubau-Schema enthält keine dieser Spalten (Schema-Test); ein Sichtbarkeitswert außerhalb der vier erlaubten wird abgelehnt.
- **DAM-102** (P2, Status: offen) **Datenübernahme aus dem Ist-Bestand** (falls ein Betreiber Echtdaten mitbringt): Probelauf auf einer Kopie; Zählvergleich je Tabelle vorher/nachher; alle Chiffrate nach neuem Bindungsschema (DAM-033) umgeschlüsselt; alle Planungsdaten verschlüsselt (DAM-024); Sicherung vor dem Lauf; Abbruch ohne Teilzustand bei Abweichung. Referenzbestand des Ist-Zustands: 99 Klassen, 169 Lehrkräfte, 2.644 Schüler/innen, 1.554 Stunden, 5.462 Konten.
  Abnahme: Übernahme des Referenzbestands → Zählwerte je Tabelle gleich der Quelle; Stichprobe von 20 entschlüsselten Feldern je Tabelle [Prüfwert] identisch mit der Quelle; Zählabfragen aus DAM-024 und DAM-033 = 0; künstlicher Fehler mitten im Lauf → Zielinstanz unverändert.

### 4.10 Indizes, Kennungen, Typen und Berechtigungsfilter

- **DAM-103** (P1, Status: Ist) **Indizes für Berechtigungs- und Datenumfangsfilter:** Jede Spalte, nach der ein Datenumfang (eigene Daten, Klasse, Kurs, Kind, Besitzer) gefiltert wird, ist indiziert, darunter `users` (`username`, `role`, `custom_role`, `teacher_id`, `student_id`), `sessions` (`token_hash`, `user_id`, `expires_at`), `api_tokens` (`user_id`, `token_hash`), `parent_links` (`parent_user_id`, `student_id`), `student_absences` (`student_id`, `date_from`, `kind`, `register_id`), `form_submissions` (`template_id`, `version_id`, `student_id`, `class_id`, `submitted_by`, `status`, `due_on`, `created_at`), `stored_files` (`owner_user_id`, `(ref_type, ref_id)`); jede Fremdschlüssel- und jede ID-Verweisspalte, nach der abgefragt wird, ist indiziert. Alle weiteren Indizes der Anhänge Z6a bis Z6c (Zeile „Indizes“ je Tabelle) gelten unverändert.
  Abnahme: Schema-Test: jeder im Register geführte Index existiert; jede Fremdschlüsselspalte hat einen Index; Abfrageplan-Test auf Testdaten in Referenzgröße (5.462 Konten, 2.644 Schüler/innen): „Konten nach Rolle“, „Sitzung nach Token-Hash“, „Fehlzeiten einer Schülerin“, „Kinder eines Elternkontos“ nutzen einen Index (kein Volltabellendurchlauf).
- **DAM-104** (P1, Status: Ist) **Indizes für Wartung und Fristen:** Zeitspalten, nach denen Löschläufe filtern, sind indiziert: `sessions.expires_at`, `auth_codes.expires_at` und (`user_id`,`purpose`,`created_at`), (`ip`,`purpose`,`created_at`), `login_attempts.created_at`, (`username`,`created_at`), (`ip`,`created_at`), `audit_log.created_at`/`user_id`/`action`, `api_token_log.at`/`token_id`, `stored_files.created_at`/`deleted_at`, `notifications_outbox` (`status`, `next_attempt_at`, `dedupe_key`), `student_absence_events` ((`absence_id`,`at`), `student_id`, `at`), `announcements.created_at`.
  Abnahme: Abfrageplan-Test der Löschabfragen (abgelaufene Sitzungen, Audit älter als Frist, weich gelöschte Dateien, fällige Outbox-Einträge) auf Testdaten mit mindestens 1 Mio. Zeilen je Tabelle [Prüfwert] → jede nutzt einen Index.
- **DAM-105** (P0, Status: Ist) **Besitz- oder Bezugsspalte je Fachtabelle:** Jede Tabelle mit Fachdaten trägt mindestens eine Spalte, über die der Datenumfang geprüft wird (`user_id`, `owner_user_id`, `student_id`, `class_id`, `channel_id`, `conversation_id`, `chat_id` u. a.); Tabellen ohne solche Spalte sind im Register als schulweite Konfiguration ausgewiesen. Fremde Datensätze liefern 404.
  Abnahme: Schema-Test: jede Tabelle hat eine Besitz-/Bezugsspalte oder den Vermerk „schulweit“; je Fachtabelle ein Test: Datensatz eines fremden Besitzers per Kennung abrufen und ändern → 404 ohne Hinweis auf Existenz.
- **DAM-106** (P1, Status: offen) **Einheitliche Länge der Kennungen:** Spalten, die auf Planungsobjekte verweisen (`student_id`, `class_id`, `teacher_id`, `course_id`, `exam_id`, `lesson_id`, `site`), haben dieselbe Länge wie die `id` im Planungsdokument (Ist: uneinheitlich 40, 64, 80 Zeichen). Die einheitliche Länge ist mindestens so groß wie der größte Ist-Wert (80 Zeichen) [Festlegung offen].
  Abnahme: Schema-Test: alle genannten Spalten haben denselben Typ und dieselbe Länge; eine Kennung mit mehr Zeichen als erlaubt wird im Planungsdokument abgelehnt (DAM-008); eine 80 Zeichen lange Kennung wird in allen Tabellen gespeichert und wieder gefunden.
- **DAM-107** (P2, Status: Ist) Primärschlüssel: ganzzahlig (Standard), UUID (`stored_files`, `letter_batches`), 32-Zeichen-Kennung (`chat_attachments`); Text-Kennungen im Planungsdokument; eigene Rollen `x-<name>`. Wo eine Kennung allein Zugriff auf Inhalte öffnen würde (Dateien, Briefstapel, Chat-Anhänge), ist sie nicht erratbar und der Zugriff zusätzlich rechtegeprüft.
  Abnahme: Schema-Test der Schlüsseltypen; Kennung einer fremden Datei, eines fremden Briefstapels oder Chat-Anhangs → 404; Stichprobe von 100 Kennungen [Prüfwert] ist nicht aufsteigend.
- **DAM-108** (P2, Status: Ist) Längen- und Mengengrenzen sind im Schema bzw. in der Eingabeprüfung festgelegt: Versionsnotiz 500 Zeichen, Audit-Ziel 200, Löschanlass 200, Fehlerprotokoll Meldung 2000 und Stacktrace 8000 Zeichen; Postfach: Text 20.000 Zeichen, 10 Anhänge, 20.000 Empfänger; Kursraum: 3.000 Einträge je Raum, Abgabetext 50.000 Zeichen, 20 Anhänge; Chat: 400 Mitglieder, 10 Geräte je Person, Chiffrat bis 120.000 Base64-Zeichen, Nonce 32 bis 40 Zeichen.
  Abnahme: Je Grenze ein Test: Wert an der Grenze → angenommen, Wert eins darüber → 422 mit Klartextfehler und ohne Teilspeicherung.
- **DAM-109** (P2, Status: offen) Jede JSON-Spalte (u. a. `form_versions.definition`, `form_submissions.result`, `gb_config`/`grade_scale`, `period_times`, `channels.settings`, `teacher_change_requests.payload`) hat ein dokumentiertes Schema und wird beim Schreiben geprüft (Ist: Aufbau mehrerer Spalten unklar, Z6a/Z6b Offene Punkte).
  Abnahme: Ungültiges Objekt in eine JSON-Spalte schreiben → 422; Schema-Test: jede JSON-Spalte hat im Register ein Schema.
- **DAM-110** (P2, Status: offen) Auswahl- und Statuswerte in Tabellen sind **vollständig definiert und werden geprüft** (Ist: Wertelisten teils unvollständig): `form_submissions.status`, `form_events.action`, `form_templates.category`, `stored_files.kind`, `comp_links.item_type`, `comp_plans.item_type`, `api_token_log.outcome`, `gb_entries.status`, `gb_log.action`, `notifications.kind`, `learning_questions.qtype`, `import_runs.system`, `import_links.kind`/`target_kind`, `plan_proposal_log.action`, `retention_log.kind`/`mode`; Statusübergänge von `student_documents` und `teacher_change_requests` sind festgelegt.
  Abnahme: Schema-Test: jede dieser Spalten hat eine Werteliste im Register; ein Wert außerhalb der Liste wird abgelehnt; ein unzulässiger Statusübergang → 409.

### 4.11 Dateiablage, Sicherung und Kapazität

- **DAM-111** (P0, Status: Ist) Dateien liegen **nur verschlüsselt** (`SMS1`) auf dem Datenträger (Standard `SM_DATA_DIR/files/`), nie im Klartext; der Dateiname liegt verschlüsselt in der Datenbank (Bindung `stored_files.filename:<id>`); `sha256` wird über den Klartext gespeichert; Inhaltserkennung per Magic-Bytes und Allowlist, aktive Inhalte werden blockiert; optionaler Virenscan (`scan_status`: `unscanned`, dann `clean` oder `error`); Zugriff: Eigentümer immer, sonst nur über die für den Bezugstyp (`ref_type`) registrierte Prüfung, **kein automatischer Administrator-Zugriff** (Atteste, Nachrichtenanhänge); Auslieferung mit sicheren Download-Headern (`nosniff`, Dateiname sicher kodiert, Inhalt in Sandbox, HTML und SVG nie inline).
  Abnahme: Datei hochladen → Auszug vom Datenträger ist nicht als Klartext erkennbar; Administrator ohne Bezug ruft ein Attest ab → 403 bzw. 404; ein manipuliertes Byte → Auslieferung scheitert mit „ungültig“; Datei mit aktivem Inhalt (HTML getarnt als Bild) → abgelehnt; fremde Datei-Kennung → 404.
- **DAM-112** (P1, Status: Ist) Größengrenzen und Kontingente: Upload höchstens 25 MB (`SM_UPLOAD_MAX_MB`), Beiträge 10 MB, Schüler-Dokumente 15 MB (nur PDF und Bild), Austausch-Import 50 MiB, Mailanhang beim Abruf 10 MiB; Kontingent je Konto Lehrkraft 2000 MB, Schüler/in 200 MB (`SM_QUOTA_MB_STAFF`, `SM_QUOTA_MB_STUDENT`), es zählen nur nicht gelöschte Dateien; die Größe wird im Durchlauf gezählt.
  Abnahme: Datei mit 26 MB → abgelehnt; Schüler-Konto mit 200 MB belegt lädt eine weitere Datei hoch → abgelehnt; nach Löschen (weich) einer Datei ist wieder Platz; Dokument mit 16 MB oder als nicht erlaubter Typ → abgelehnt.
- **DAM-113** (P0, Status: Ist) Sicherungen: konsistente Kopie (SQLite: Backup-Schnittstelle der Datenbank mit 30 Sekunden Zeitlimit für die Quelle; PostgreSQL: JSON-Export aller Tabellen, gepackt); verschlüsselte Spalten bleiben als Token, Planversionen ohne Binärdaten, das aktuelle Planungsdokument liegt verschlüsselt (Bindung `backup.school:<Version>`); **keine Schlüssel in der Sicherung**; Namensmuster `<Produktkürzel>-JJJJMMTT-HHMMSS.db` bzw. `.json.gz` (bei Kollision `-n`), nur dieses Muster ist abrufbar (kein Pfadzugriff); Dateirechte 0600; Anlegen, Herunterladen, Löschen, Prüfen nur mit `system.admin`; Audit `system.backup` (Name, Größe, Art); vor jedem Update wird gesichert, schlägt die Sicherung fehl, findet das Update nicht statt. Ob die Dateien der Dateiablage selbst in der Sicherung enthalten sind: [unklar].
  Abnahme: Sicherung anlegen → Auszug zeigt Chiffrat-Token statt Klartext; Suche nach dem Wert von `SM_ENCRYPTION_KEYS` und `SM_SECRET_KEY` in der Sicherung → 0 Treffer; Dateirechte 0600; Konto ohne `system.admin` → 403; Abruf eines Namens außerhalb des Musters → 404; Audit-Eintrag mit Name und Größe.
- **DAM-114** (P1, Status: Ist) **Test-Wiederherstellung** in einer Wegwerf-Kopie, Live-Daten bleiben unberührt: SQLite bestanden, wenn Integritätsprüfung „ok“, Zeilen je Tabelle gezählt, Konten > 0 und Planversionen > 0; JSON bestanden, wenn die Format-Kennung stimmt und ein Planungsdokument vorhanden ist; die Kopie wird danach gelöscht; das Ergebnis erscheint als Text auf der Statusseite; auch das ältere Sicherungsformat wird akzeptiert.
  Abnahme: Intakte Sicherung → bestanden; Sicherung mit 0 Konten oder ohne Planversion → nicht bestanden; Zeilenzahlen der Live-Datenbank vor und nach der Prüfung gleich; Kopie nach der Prüfung nicht mehr vorhanden.
- **DAM-115** (P1, Status: offen) Die **Wiederherstellung** (Restore) ist als Ablauf beschrieben und getestet (Ist: kein Weg über Oberfläche oder Schnittstelle, nur im Betriebsdokument): wer, welche Befehle, welche Reihenfolge; sie braucht dieselben Schlüssel (`SM_ENCRYPTION_KEYS`, `SM_SECRET_KEY`) wie zur Zeit der Sicherung; das Verhältnis einer Schlüsselrotation zu älteren Sicherungen ist beschrieben [unklar].
  Abnahme: Wiederherstellung auf frischer Instanz aus Sicherung und Schlüsseln → Zeilenzahl je Tabelle gleich der Quelle, Anmeldung möglich, verschlüsselte Felder lesbar; mit falschen Schlüsseln → Felder „[nicht lesbar]“, Warnung auf der Statusseite, keine Datenveränderung.
- **DAM-116** (P1, Status: Ist) **Löschkonzept und Sicherungen:** Das Löschkonzept wirkt nicht auf Sicherungen; gelöschte Personendaten bleiben bis zur Rotation (`SM_BACKUP_KEEP` = 30 neueste Dateien, 0 = keine Rotation; die Rotation läuft nur bei Anlage einer Sicherung); bei täglicher Sicherung rechnerisch etwa 30 Tage Rückhalt [abgeleitet]; die automatische Sicherung (`SM_AUTO_BACKUP_HOURS`) ist standardmäßig aus (0). [Vorschlag] Die Datenschutzinformation nennt die Rückhaltedauer.
  Abnahme: Person löschen → die Sicherung vom Vortag enthält sie noch; 30 Sicherungen später ist diese Sicherung rotiert und enthält sie nicht mehr; `SM_BACKUP_KEEP` = 0 → keine Datei wird gelöscht; die Statusseite zeigt das Alter der jüngsten Sicherung (bis 48 Stunden ok, darüber Warnung; ohne Sicherung Warnung in Produktion).
- **DAM-117** (P2, Status: Ist) Kapazität: Zielgröße ca. 2.500 Schüler/innen, ca. 200 Lehrkräfte, 2 Standorte. Referenzmessung im Ist: 5.462 Konten → Datenbank 3,3 MB, `users` mit 6 Indizes 1,41 MB (ca. 260 Byte je Konto), `school_versions` 1,0 MB bei 15 Versionen (Ø 66 KB je Version), Dateiablage 0,8 MB (5 Dateien). Rechenmodell der Planversion: 35 / 70 / 130 KB je Schulgröße (klein / mittel / groß).
  Abnahme: Testdaten in Referenzgröße (99 Klassen, 169 Lehrkräfte, 2.644 Schüler/innen, 1.554 Stunden, 5.462 Konten) laden fehlerfrei; eine Planversion dieser Größe bleibt unter 130 KB komprimiert [Prüfwert aus dem Rechenmodell]; nach 4 bis 6 Wochen Echtbetrieb werden die Annahmen der Speicherkalkulation aus der Datenbank nachgemessen.

### 4.12 Zuordnung der Vorgaben zu den Anforderungen

| Vorgabe | Anforderungen |
|---|---|
| Freitexte verschlüsselt; Gesundheits- und Leistungsdaten geschützt | DAM-034, DAM-035, DAM-036, DAM-031 bis DAM-033, DAM-045 |
| Jede Tabelle mit Personenbezug hat Datenart und Löschfrist | DAM-076 bis DAM-079, DAM-044 |
| Alle Zeitstempel in UTC; `updated_at` automatisch | DAM-053 bis DAM-059 |
| Fremdschlüssel und Löschverhalten festgelegt; Pseudonymisierung | DAM-060 bis DAM-069, DAM-062, DAM-063 |
| Eindeutigkeiten als Datenbank-Constraints | DAM-070 bis DAM-075, DAM-065 |
| Migrationen nur versioniert, Expand/Contract, Schema-Falle | DAM-091 bis DAM-102, DAM-094, DAM-097 |
| Indizes für Berechtigungsfilter und Wartung; fremde Daten liefern 404 | DAM-103 bis DAM-105 |
| Versionierung, Rückgängig und Synchronisierung des Planungsdokuments | DAM-016 bis DAM-030 |
| Jede schreibende Aktion wird protokolliert, ohne Inhalte | DAM-087, DAM-088 |
| Schlüssel, Hashes, Geheimnisse | DAM-038 bis DAM-041, DAM-046 bis DAM-052 |
| Sicherung, Wiederherstellung, Kapazität | DAM-113 bis DAM-117 |
| Eine Instanz je Schule; Produktname nur an einer Stelle konfigurierbar (Sicherungsnamen tragen das zentrale Produktkürzel) | DAM-013, DAM-113 |

### 4.13 Zählkontrolle

| Abschnitt | Kennungen | Anzahl | P0 | P1 | P2 | P3 | Ist | offen |
|---|---|---|---|---|---|---|---|---|
| 4.1 Speicherformen und Planungsdokument | DAM-001 bis 015 | 15 | 3 | 8 | 4 | 0 | 11 | 4 |
| 4.2 Versionierung | DAM-016 bis 030 | 15 | 2 | 9 | 4 | 0 | 11 | 4 |
| 4.3 Verschlüsselung und Schema-Register | DAM-031 bis 045 | 15 | 11 | 4 | 0 | 0 | 7 | 8 |
| 4.4 Hashing und Geheimnisse | DAM-046 bis 052 | 7 | 5 | 1 | 1 | 0 | 6 | 1 |
| 4.5 Zeitstempel | DAM-053 bis 059 | 7 | 1 | 4 | 2 | 0 | 4 | 3 |
| 4.6 Fremdschlüssel und Löschverhalten | DAM-060 bis 069 | 10 | 4 | 5 | 1 | 0 | 6 | 4 |
| 4.7 Eindeutigkeiten | DAM-070 bis 075 | 6 | 0 | 3 | 3 | 0 | 4 | 2 |
| 4.8 Aufbewahrung und Protokolle | DAM-076 bis 090 | 15 | 11 | 4 | 0 | 0 | 11 | 4 |
| 4.9 Migrationen | DAM-091 bis 102 | 12 | 3 | 7 | 2 | 0 | 7 | 5 |
| 4.10 Indizes, Kennungen, Typen | DAM-103 bis 110 | 8 | 1 | 3 | 4 | 0 | 5 | 3 |
| 4.11 Dateiablage, Sicherung, Kapazität | DAM-111 bis 117 | 7 | 2 | 4 | 1 | 0 | 6 | 1 |
| **Summe** | DAM-001 bis 117 | **117** | **43** | **52** | **22** | **0** | **78** | **39** |

Ergänzte Tabellen (Kapitel 2a): 14 (1 Ist-Zustand, 13 geplant).

---

## 5 Verweis auf die Anhänge

Die Anhänge liegen im Paket unter `anhang/`. Sie enthalten die vollständigen Spaltentabellen und die Rohwerte; diese Datei enthält Prinzipien, Verzeichnis und prüfbare Regeln.

| Anhang | Pfad | Inhalt |
|---|---|---|
| Z6a | `anhang/zahlen-und-tabellen/Z6a.md` | Spaltentabellen der 56 Tabellen der Konten, Dateiablage, Formulare, Kursräume, Chats und Kompetenzen (13 Kern- und 43 Feature-Tabellen) mit Typen, Standardwerten, Indizes, Wertelisten, Fristen und der Übersicht der verschlüsselten und gehashten Spalten. |
| Z6b | `anhang/zahlen-und-tabellen/Z6b.md` | Spaltentabellen der 54 Tabellen in den Bereichen A bis O (Notenbuch, Anbieter-Konten, Zugangsbriefe, Importe, Lernaktivitäten, Nachschreiben, Postfach, Benachrichtigungen, Betrieb, Elternzugriff, Plan-Prüfung, Lernfortschritt) sowie 58 übergreifende Werte und Regeln. |
| Z6c | `anhang/zahlen-und-tabellen/Z6c.md` | Spaltentabellen der 13 Tabellen Klassenbuch, Förderinformationen, Dokumente, Lehrkraft-Anträge, Löschkonzept, Sicherheitseinstellungen, eigene Rollen und beobachtete Konten mit Prüfpunkten und offenen Werten. |
| Z3 | `anhang/zahlen-und-tabellen/Z3.md` | Löschkonzept (Datenarten, Fristen, Warteliste, Art. 17), Auskunft, Wartungsjobs, Sicherungen, Betrieb, Audit und Verschlüsselung (Verfahren, Schlüsselring, Bindung, verschlüsselte Felder) mit allen Werten. |
| Z7 | `anhang/zahlen-und-tabellen/Z7.md` | Planungsdokument: Feldtabellen aller Datentypen und Sammlungen, Konventionen (Wochen, Rhythmus, leere Listen), Validierung, Versionierung, Rückgängig, Synchronisierung, Speicherformat, Start und die Versionszeile `school_versions`. |
| Z9 | `anhang/zahlen-und-tabellen/Z9.md` | Seiteninventar mit Routen und Rechten, Bausteine-Katalog, Design-Tokens und Menüstruktur je Rolle der Oberfläche; für das Datenmodell relevant als Zuordnung Seite ↔ Recht (z. B. die Statusseite `/betrieb` mit den Prüfpunkten Datenbank, Schema, Speicher, Sicherung). |
| I8 | `anhang/ist-zustand/I8.md` | Betrieb der Schul-Instanz, Sicherung, Einrichtung, Schuljahreswechsel, Lizenz, Updates, Anbieter-Lizenzserver und das Tabellenverzeichnis des Ist-Zustands (136 Tabellen in 18 Fachgruppen) mit der Entwicklungsgeschichte der Datenbank und den Regeln für Schema-Änderungen. |

Weitere Quellen dieser Datei: `anhang/ist-zustand/I9.md` (Kern, Datenhaltung, Verschlüsselung, Audit, Hintergrundarbeit im Querschnitt), `anhang/anforderungen-backlog/W3.md` (Backlog mit den geplanten Tabellen des Kapitels 2a) und `anhang/anforderungen-backlog/W2.md` (Abgleich Wunsch gegen Bestand).

<!--ENDE-->
