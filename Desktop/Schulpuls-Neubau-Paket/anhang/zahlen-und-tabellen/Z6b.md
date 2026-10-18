# Z6b – Datenmodell als Tabellen (Bereich g bis p)

Quellbereich: Feature-Modelle mit Anfangsbuchstaben g bis p (17 Quelldateien, vollständig gelesen). Zusätzlich geprüft: die gemeinsame Basis für verschlüsselte Textspalten (nur Methoden, keine Spalten). Keine Datei-, Zeilen- oder Funktionsverweise.

---

## 0 Legende

- **Typ:** Ganzzahl = ganze Zahl. Text(n) = Zeichenkette, max. n Zeichen. Langtext = Text ohne Längenbegrenzung. Zahl = Dezimalzahl. Ja/Nein = Wahrheitswert. Zeit = Datum und Uhrzeit (im Modell ohne Zeitzone; Werte in UTC, wo angegeben). JSON = strukturierter Wert (Liste oder Objekt). Binär = Bytefolge.
- **Pflicht** = darf nicht leer sein (NOT NULL). **optional** = leer erlaubt (NULL).
- **Standard** = Vorgabe beim Anlegen (Anwendungs-Standard, im Modell gesetzt). „—“ = kein Standard. „aktuelle Zeit“ = Zeitpunkt des Anlegens.
- **Fremdschlüssel (Löschen):** „Kaskade“ = Kindzeilen werden mitgelöscht. „NULL“ = Verweis wird beim Löschen des Ziels geleert. „ohne Regel“ = kein Löschverhalten im Modell (Datenbank-Standard). „kein FK“ = nur eine Zahl bzw. Kennung ohne Erzwingung.
- **VERSCHLÜSSELT** = Chiffrat in der Datenbank (Endung `_enc`). Leerer Text bleibt leer und unverschlüsselt. Kontextbindung (AAD) siehe Abschnitt 3.
- **GEHASHT** = nur Hash oder HMAC gespeichert, kein Klartext.
- **KLARTEXT-PERSONENBEZUG** = Name, E-Mail oder Schüler-Kennung im Klartext (Datenschutz beachten).

---

## 1 Übersicht (54 Tabellen in 15 Bereichen)

| Bereich | Tabellen |
|---|---|
| A Notenbuch (10) | exam_results, gb_config, gb_books, gb_categories, gb_items, gb_entries, gb_finals, gb_log, gb_source_results, gb_source_links |
| B Anbieter-Konten und Anmeldung (3) | user_identities, sso_providers, login_policy_rules |
| C Zugangsbriefe (2) | letter_batches, account_initial_passwords |
| D Doppelsende-Schutz (1) | send_idempotency |
| E Fremdimporte (2) | import_runs, import_links |
| F Lernaktivitäten (10) | learning_polls, learning_poll_participants, learning_poll_votes, learning_poll_tally, learning_surveys, learning_survey_responses, learning_survey_participants, learning_questions, learning_selftests, learning_attempts |
| G Nachschreiben (2) | exam_makeup_dates, exam_makeups |
| H E-Mail-Konten (1) | mail_accounts |
| I Postfach (7) | conversations, conversation_participants, messages, message_reports, user_blocks, message_user_settings, message_drafts |
| J Benachrichtigungen (5) | notifications, notification_prefs, notification_user_settings, notification_school, notification_config |
| K Betrieb (2) | system_state, error_log |
| L Elternzugriff (2) | parent_access, student_prefs |
| M Plan-Prüfung (3) | plan_proposals, plan_proposal_variants, plan_proposal_log |
| N Plan-Stände (1) | plan_snapshots |
| O Lernfortschritt (3) | completion_rules, completion_marks, availability_rules |

Tabellen außerhalb dieses Bereichs, auf die verwiesen wird: `users` (Konto), `channels` (Kursraum), `stored_files` (Anhänge), `student_documents` (Dokumente zur Fehlzeit), `school_versions` (Versionsverlauf des Planungsdokuments), `plan_periods` (Planzeiträume).

---

## 2 Tabellen je Bereich

### A Notenbuch

#### A1 `exam_results` – Noten zu Klausuren und Tests
**Zweck:** Hält die Note einer Person zu einer Klausur aus dem Planungsdokument fest.
**Eindeutig:** (exam_id, student_id).
**Indizes:** exam_id; student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| exam_id | Text(40) | Pflicht | — | kein FK | Klausur-ID aus dem Planungsdokument |
| course_id | Text(64) | Pflicht | "" | kein FK | Kurs-ID |
| student_id | Text(40) | Pflicht | — | kein FK | Schüler-ID aus dem Planungsdokument |
| grade_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Note; AAD `exam_results.grade:<id>` |
| note_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Bemerkung; AAD `exam_results.note:<id>` |
| graded_by | Ganzzahl | optional | NULL | kein FK | Konto-ID der bewertenden Person |
| graded_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| graded_at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt der Bewertung |

#### A2 `gb_config` – Schulweite Einstellungen des Notenbuchs
**Zweck:** Schlüssel/Wert-Speicher für die schulweiten Einstellungen des Notenbuchs.
**Eindeutig:** key (PK).
**Indizes:** keine weiteren.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| key | Text(40) | Pflicht (PK) | — | — | Name der Einstellung |
| value | JSON | optional | NULL | — | Wert der Einstellung |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |

Hinweis: Standardwerte der Einstellungen liegen nicht in den Quelldateien dieses Bereichs. Siehe Abschnitt 5 [unklar].

#### A3 `gb_books` – Notenbuch je Kursteil und Halbjahr
**Zweck:** Ein Notenbuch gehört zu einem Kursteil in einem Halbjahr.
**Eindeutig:** (course_id, part, term).
**Indizes:** course_id; term.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| course_id | Text(64) | Pflicht | — | kein FK | Kurs-ID |
| part | Ganzzahl | Pflicht | 0 | — | Kursteil-Nummer |
| term | Text(10) | Pflicht | — | — | Halbjahr, Beispiel „2026-1“ |
| scale_id | Text(40) | Pflicht | "note6" | — | Notenskala |
| key_id | Text(40) | Pflicht | "" | — | Bewertungsschlüssel-ID |
| rounding | Text(10) | Pflicht | "ganz" | — | Rundungsart; weitere Werte [unklar] |
| decimals | Ganzzahl | Pflicht | 2 | — | Nachkommastellen (2 Stellen) |
| created_by | Ganzzahl | optional | NULL | kein FK | Konto-ID der anlegenden Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| locked_at | Zeit | optional | NULL | — | Sperrzeitpunkt; gesetzt = gesperrt |
| locked_by | Ganzzahl | optional | NULL | kein FK | Konto-ID der sperrenden Person |
| locked_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |

#### A4 `gb_categories` – Leistungsarten
**Zweck:** Gliedert die Leistungen eines Notenbuchs (z. B. Schriftlich, Sonstige Mitarbeit, darunter Tests); verschachtelbar.
**Eindeutig:** keine.
**Indizes:** book_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| book_id | Ganzzahl | Pflicht | — | gb_books.id, Kaskade | Notenbuch |
| parent_id | Ganzzahl | optional | NULL | kein FK | übergeordnete Leistungsart (Verschachtelung) |
| name | Text(120) | Pflicht | — | — | Bezeichnung |
| weight | Zahl | Pflicht | 1.0 | — | Gewicht (Faktor; 1.0 = normal) |
| position | Ganzzahl | Pflicht | 0 | — | Sortierreihenfolge |

#### A5 `gb_items` – Leistung (Spalte der Notentabelle)
**Zweck:** Eine Klausur, ein Test, ein Referat o. Ä. als Spalte im Notenbuch.
**Eindeutig:** keine.
**Indizes:** book_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| book_id | Ganzzahl | Pflicht | — | gb_books.id, Kaskade | Notenbuch |
| category_id | Ganzzahl | optional | NULL | kein FK | Leistungsart |
| title | Text(120) | Pflicht | — | — | Bezeichnung der Leistung |
| date | Text(10) | Pflicht | "" | — | Datum der Leistung (Format [unklar]) |
| weight | Zahl | Pflicht | 1.0 | — | Gewicht (Faktor) |
| max_points | Zahl | optional | NULL | — | Höchstpunktzahl; leer = nicht gesetzt |
| key_id | Text(40) | Pflicht | "" | — | Bewertungsschlüssel-ID |
| position | Ganzzahl | Pflicht | 0 | — | Spaltenreihenfolge |
| released | Ja/Nein | Pflicht | nein | — | Freigabe; Wirkung außerhalb dieses Bereichs [unklar] |
| makeup_date | Text(10) | Pflicht | "" | — | Nachschreibtermin |
| source_type | Text(30) | Pflicht | "" | — | Herkunftsbereich bei übernommenen Ergebnissen |
| source_id | Text(80) | Pflicht | "" | — | Kennung der Quelle |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |

#### A6 `gb_entries` – Note oder Punkte einer Person bei einer Leistung
**Zweck:** Speichert Note bzw. Punktzahl je Person und Leistung.
**Eindeutig:** (item_id, student_id).
**Indizes:** item_id; student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| item_id | Ganzzahl | Pflicht | — | gb_items.id, Kaskade | Leistung |
| student_id | Text(40) | Pflicht | — | kein FK | Schüler-ID; KLARTEXT-PERSONENBEZUG |
| value_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Note oder Punkte; AAD `gb_entries.value:<id>` |
| note_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Bemerkung; AAD `gb_entries.note:<id>` |
| status | Text(20) | Pflicht | "" | — | Status; Werte und Beschriftungen [unklar] |
| makeup_date | Text(10) | Pflicht | "" | — | Nachschreibtermin dieser Person |
| from_source | Ja/Nein | Pflicht | nein | — | Ergebnis aus einem anderen Bereich übernommen |
| entered_by | Ganzzahl | optional | NULL | kein FK | Konto-ID der eintragenden Person |
| entered_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| entered_at | Zeit | Pflicht | aktuelle Zeit | — | Eintragungszeitpunkt |

#### A7 `gb_finals` – Festgelegte Halbjahres- oder Zeugnisnote
**Zweck:** Speichert die von der Lehrkraft festgelegte Endnote je Person; der Vorschlag wird immer neu berechnet und nicht gespeichert.
**Eindeutig:** (book_id, student_id).
**Indizes:** book_id; student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| book_id | Ganzzahl | Pflicht | — | gb_books.id, Kaskade | Notenbuch |
| student_id | Text(40) | Pflicht | — | kein FK | Schüler-ID; KLARTEXT-PERSONENBEZUG |
| value_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Endnote; AAD `gb_finals.value:<id>` |
| note_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Bemerkung; AAD `gb_finals.note:<id>` |
| set_by | Ganzzahl | optional | NULL | kein FK | Konto-ID der festsetzenden Person |
| set_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| set_at | Zeit | Pflicht | aktuelle Zeit | — | Festsetzungszeitpunkt |

#### A8 `gb_log` – Änderungsprotokoll des Notenbuchs
**Zweck:** Protokolliert je Notenbuch, wer wann was geändert hat (Wert vorher und nachher).
**Eindeutig:** keine.
**Indizes:** book_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| book_id | Ganzzahl | Pflicht | — | kein FK | Protokoll bleibt beim Löschen des Notenbuchs erhalten (Modell ohne FK) |
| at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt der Änderung |
| actor_id | Ganzzahl | optional | NULL | kein FK | Konto-ID der handelnden Person |
| actor_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| action | Text(30) | Pflicht | — | — | Art der Änderung; Werte [unklar] |
| item_id | Ganzzahl | optional | NULL | kein FK | betroffene Leistung |
| student_id | Text(40) | Pflicht | "" | kein FK | betroffene Person; KLARTEXT-PERSONENBEZUG |
| detail_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Einzelheiten der Änderung; AAD `gb_log.detail:<id>` |

#### A9 `gb_source_results` – Ergebnis aus einem anderen Bereich
**Zweck:** Ergebnis aus einem anderen Bereich (z. B. Aufgabe, Selbsttest), das die Lehrkraft in ein Notenbuch übernehmen kann.
**Eindeutig:** (source_type, source_id, student_id).
**Indizes:** source_type; course_id; student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| source_type | Text(30) | Pflicht | — | — | Art der Quelle |
| source_id | Text(80) | Pflicht | — | — | Kennung der Quelle |
| course_id | Text(64) | Pflicht | — | — | Kurs-ID |
| part | Ganzzahl | Pflicht | 0 | — | Kursteil |
| title | Text(120) | Pflicht | "" | — | Titel |
| date | Text(10) | Pflicht | "" | — | Datum |
| student_id | Text(40) | Pflicht | — | — | Schüler-ID; KLARTEXT-PERSONENBEZUG |
| points | Zahl | optional | NULL | — | erreichte Punkte, **KLARTEXT** (nicht verschlüsselt) |
| max_points | Zahl | optional | NULL | — | Höchstpunktzahl, KLARTEXT |
| grade | Text(20) | Pflicht | "" | — | Note als Text, **KLARTEXT** (nicht verschlüsselt, anders als in gb_entries) |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Aktualisierung |

#### A10 `gb_source_links` – Übernahme-Entscheidung je Quelle
**Zweck:** Hält fest, ob eine Quelle in einem Notenbuch übernommen oder abgewählt wurde.
**Eindeutig:** (book_id, source_type, source_id).
**Indizes:** book_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| book_id | Ganzzahl | Pflicht | — | gb_books.id, Kaskade | Notenbuch |
| source_type | Text(30) | Pflicht | — | — | Art der Quelle |
| source_id | Text(80) | Pflicht | — | — | Kennung der Quelle |
| state | Text(12) | Pflicht | "adopted" | — | adopted (übernommen) / dismissed (abgewählt) |
| item_id | Ganzzahl | optional | NULL | kein FK | entstandene Leistung |

---

### B Anbieter-Konten und Anmeldung

#### B1 `user_identities` – Verknüpfte Anbieter-Konten
**Zweck:** Verbindet ein Schulmanager-Konto mit einem Konto bei einem Anbieter (Microsoft, Apple, Google oder Schulkonto).
**Eindeutig:** (provider, subject); (user_id, provider).
**Indizes:** user_id; email.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Konto |
| provider | Text(20) | Pflicht | — | — | Anbieterkennung; Werte [unklar] |
| subject | Text(255) | optional | NULL | — | stabile Kennung beim Anbieter; NULL = vorgemerkt. Schulkonto: Aussteller und Kennung, getrennt durch senkrechten Strich; Testanbieter: „mock:<Wert>“ |
| email | Text(254) | optional | NULL | — | E-Mail beim Anbieter, klein geschrieben |
| email_verified | Ja/Nein | Pflicht | nein | — | E-Mail vom Anbieter bestätigt |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| last_login_at | Zeit | optional | NULL | — | letzte Anmeldung über diese Verknüpfung |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person (Administration oder Sekretariat) |

#### B2 `sso_providers` – Einrichtung der Anbieter
**Zweck:** Einrichtung der Anbieter für die Anmeldung (Microsoft, Apple, Google oder allgemeines OIDC), durch die Administration.
**Eindeutig:** provider (PK).
**Indizes:** keine weiteren.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| provider | Text(20) | Pflicht (PK) | — | — | Anbieterkennung |
| enabled | Ja/Nein | Pflicht | nein | — | Anbieter aktiv |
| client_id | Text(255) | optional | NULL | — | Client-Kennung des Anbieters (keine Geheimzahl) |
| client_secret_enc | Langtext | optional | NULL | — | VERSCHLÜSSELT: Client-Geheimnis; AAD `sso_providers.client_secret:<Anbieter>` |
| tenant | Text(100) | optional | NULL | — | Mandant (Microsoft) |
| hosted_domain | Text(255) | optional | NULL | — | Google-Domäne (Beschränkung auf eine Organisation) |
| team_id | Text(20) | optional | NULL | — | Apple-Team-Kennung |
| key_id | Text(20) | optional | NULL | — | Apple-Schlüsselkennung |
| private_key_enc | Langtext | optional | NULL | — | VERSCHLÜSSELT: Apple-Schlüsseldatei (.p8); AAD `sso_providers.private_key:<Anbieter>` |
| issuer | Text(500) | optional | NULL | — | Aussteller-Adresse (allgemeines OIDC) |
| label | Text(100) | optional | NULL | — | Anzeigename auf dem Anmeldeknopf |
| allowed_domains | JSON | optional | NULL | — | Liste erlaubter E-Mail-Domänen |
| auto_signin | Ja/Nein | Pflicht | nein | — | automatische Anmeldung |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |
| updated_by | Ganzzahl | optional | NULL | users.id, NULL | ändernde Person |

#### B3 `login_policy_rules` – Anmelde-Richtlinie
**Zweck:** Legt je Geltungsbereich fest, wer sich wie anmelden darf (Anmeldewege, Pflichtverknüpfungen, Selbstverknüpfung, Passwort-Rücksetzung, Anlage per SSO).
**Eindeutig:** (scope, scope_ref, audience).
**Indizes:** scope.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| scope | Text(20) | Pflicht | — | — | default (alle Konten), role (Rolle), grade (Jahrgang), class (Klasse), user (Person) |
| scope_ref | Text(80) | Pflicht | "" | kein FK | leer bei default; Rollenname (z. B. schueler), Klassenstufe als Text (z. B. „5“), Klassen-ID, Benutzer-ID als Text |
| audience | Text(20) | Pflicht | "alle" | — | alle / schueler / eltern; ungleich „alle“ nur bei grade und class |
| methods | JSON | optional | NULL | — | erlaubte Anmeldewege (Liste, nie leer); NULL = vom allgemeineren Bereich geerbt |
| required_links | JSON | optional | NULL | — | Anbieter, die verbunden sein müssen (Liste); NULL = geerbt |
| self_link | Ja/Nein | optional | NULL | — | darf eigene Anbieter-Konten verbinden und trennen; NULL = geerbt |
| reset_channels | JSON | optional | NULL | — | Kanäle für „Passwort vergessen“: email, sms; NULL = geerbt |
| sso_create | Ja/Nein | optional | NULL | — | beim ersten Anbieter-Login per bestätigter E-Mail zuordnen; NULL = geerbt |
| note | Text(500) | Pflicht | "" | — | Notiz (Klartext) |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |
| updated_by | Ganzzahl | optional | NULL | users.id, NULL | ändernde Person |

---

### C Zugangsbriefe

#### C1 `letter_batches` – Zugangsbrief-Stapel
**Zweck:** Kurzlebiger Stapel mit Zugangsdaten (Startpasswörter) für gedruckte Briefe; Inhalt nur verschlüsselt.
**Eindeutig:** id (UUID, PK).
**Indizes:** created_by; expires_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Text(36) | Pflicht (PK) | neue UUID | — | UUID |
| created_by | Ganzzahl | optional | NULL | users.id, Kaskade | anlegende Person; Löschen des Kontos löscht den Stapel |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| expires_at | Zeit | Pflicht | — | — | Ablauf; Standard 60 min nach Anlage (Variable SM_LETTER_BATCH_MINUTES) |
| title | Text(200) | Pflicht | "" | — | Titel (Klartext) |
| count | Ganzzahl | Pflicht | 0 | — | Anzahl der Einträge (Klartext) |
| data_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Einträge (Konto, Name, Klasse, Startpasswort, bei Eltern die Kinder); AAD `letter_batches:<id>` |

Hinweise: Zugriff nur für die anlegende Person oder die Rolle admin. Nach Ablauf löscht die Wartung den Stapel oder der nächste Zugriff.

#### C2 `account_initial_passwords` – Startpasswort mit Frist
**Zweck:** Kennzeichnet, dass das aktuelle Passwort eines Kontos ein Startpasswort mit Frist ist; nur als Hash.
**Eindeutig:** user_id (PK).
**Indizes:** expires_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | Konto |
| password_hash | Text(255) | Pflicht | "" | — | GEHASHT: Kopie des Konto-Hashs zum Zeitpunkt der Vergabe; kein Klartext |
| expires_at | Zeit | Pflicht | aktuelle Zeit (Modell); Fachvorgabe 14 Tage ab Vergabe | — | Frist des Startpassworts |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Vergabe |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | vergebende Person |

Hinweise: Die Zeile verschwindet beim Passwortwechsel und beim Löschen des Kontos. Nach Ablauf ist das Startpasswort nicht mehr nutzbar.

---

### D Doppelsende-Schutz

#### D1 `send_idempotency` – Doppelsende-Schutz
**Zweck:** Verhindert, dass ein Absendevorgang doppelt angenommen wird; eine Wiederholung liefert die bereits gesendete Nachricht.
**Eindeutig:** zusammengesetzter PK (user_id, scope, key).
**Indizes:** created_at (Bereinigung).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | Konto |
| scope | Text(40) | Pflicht (PK) | — | — | Bereich: chat:<ID> / conv:<ID> / conv:new |
| key | Text(64) | Pflicht (PK) | — | — | vom Client je Absendevorgang vergebener Schlüssel |
| ref | Ganzzahl | Pflicht | — | — | Nachrichten-ID bzw. Unterhaltungs-ID |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt der Annahme |

Hinweis: Keine Inhalte gespeichert, nur Schlüssel und Verweis. Aufbewahrungsdauer [unklar].

---

### E Fremdimporte

#### E1 `import_runs` – Importlauf (Protokoll)
**Zweck:** Protokolliert jeden echten Import aus einem Fremdsystem; Trockenläufe werden nicht gespeichert.
**Eindeutig:** keine (PK id).
**Indizes:** system.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| system | Text(30) | Pflicht | — | — | Quellsystem; Werte [unklar] |
| instance | Text(60) | Pflicht | "standard" | — | Instanz des Quellsystems |
| source_name | Text(200) | Pflicht | "" | — | Name der Quelle (Klartext) |
| source_hash | Text(64) | Pflicht | "" | — | GEHASHT: Prüfsumme der Quelldatei |
| user_id | Ganzzahl | optional | NULL | users.id, NULL | ausführende Person |
| user_name | Text(80) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| started_at | Zeit | Pflicht | aktuelle Zeit | — | Start |
| finished_at | Zeit | optional | NULL | — | Ende |
| status | Text(16) | Pflicht | "ok" | — | ok / teilweise / fehler / zurueckgenommen |
| options | JSON | optional | NULL | — | Optionen des Laufs |
| summary | JSON | optional | NULL | — | Zähler des Laufs |
| report_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: vollständiger Bericht (enthält Namen); AAD `import_runs.report:<id>` |
| undone_at | Zeit | optional | NULL | — | Zeitpunkt der Rücknahme |
| undone_by | Text(80) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name der zurücknehmenden Person |

#### E2 `import_links` – Zuordnung Quellelement zu Zielobjekt
**Zweck:** Ordnet Elemente des Quellsystems den angelegten Zielobjekten zu; verhindert Dubletten bei erneutem Import und ermöglicht die Rücknahme.
**Eindeutig:** (system, instance, kind, source_key).
**Indizes:** created_run.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| system | Text(30) | Pflicht | — | — | Quellsystem |
| instance | Text(60) | Pflicht | "standard" | — | Instanz des Quellsystems |
| kind | Text(30) | Pflicht | — | — | Art des Quellelements (person, course, group, assign, submission, weitere [unklar]) |
| source_key | Text(120) | Pflicht | — | — | Kennung im Quellsystem |
| target_kind | Text(30) | Pflicht | — | — | Zielart (student, teacher, class, channel, item, weitere [unklar]) |
| target_id | Text(120) | Pflicht | "" | kein FK | ID des Zielobjekts |
| fingerprint | Text(40) | Pflicht | "" | — | Fingerabdruck; unverändertes Element = es wird nichts geschrieben (Form [unklar]) |
| created_run | Ganzzahl | optional | NULL | import_runs.id, NULL | Lauf, der das Zielobjekt angelegt hat (für Rücknahme) |
| updated_run | Ganzzahl | optional | NULL | import_runs.id, NULL | Lauf, der das Zielobjekt zuletzt geändert hat |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage der Zuordnung |

---

### F Lernaktivitäten

#### F1 `learning_polls` – Abstimmung
**Zweck:** Abstimmung im Kursraum oder an einer Chat-Nachricht.
**Eindeutig:** chat_message_id (eindeutig, wenn gesetzt).
**Indizes:** channel_id; chat_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | optional | NULL | channels.id, Kaskade | Kursraum; leer bei Chat-Abstimmung |
| chat_id | Ganzzahl | optional | NULL | kein FK | Chat-Kennung |
| chat_message_id | Ganzzahl | optional | NULL | kein FK | Chat-Nachricht; eindeutig |
| question_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Frage (Kursraum); bei Chat-Abstimmung steht die Frage nur Ende-zu-Ende in der Nachricht; AAD `learning_polls.question:<id>` |
| options_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Antwortmöglichkeiten; AAD `learning_polls.options:<id>` |
| option_count | Ganzzahl | Pflicht | 2 | — | Anzahl Antwortmöglichkeiten |
| multiple | Ja/Nein | Pflicht | nein | — | Mehrfachauswahl erlaubt |
| max_choices | Ganzzahl | optional | NULL | — | höchstens so viele Antworten bei Mehrfachauswahl; NULL-Bedeutung [unklar] |
| anonymous | Ja/Nein | Pflicht | nein | — | anonyme Abstimmung |
| results | Text(12) | Pflicht | "live" | — | Sichtbarkeit der Ergebnisse: live / after_vote / after_end |
| ends_at | Zeit | optional | NULL | — | Ende (UTC) |
| closed_at | Zeit | optional | NULL | — | vorzeitig beendet (UTC) |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |

Hinweis: Bei Chat-Abstimmungen kennt der Server nur die Zahl der Antworten.

#### F2 `learning_poll_participants` – Teilnahme an einer Abstimmung
**Zweck:** Stellt sicher, dass jede Person nur einmal abstimmt; bei anonymen Abstimmungen ohne Personenbezug.
**Eindeutig:** (poll_id, user_id); (poll_id, token).
**Indizes:** poll_id; user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| poll_id | Ganzzahl | Pflicht | — | learning_polls.id, Kaskade | Abstimmung |
| user_id | Ganzzahl | optional | NULL | users.id, Kaskade | nur bei namentlichen Abstimmungen gesetzt |
| token | Text(64) | optional | NULL | — | GEHASHT: HMAC aus Server-Geheimnis, Abstimmung und Konto; eindeutig je Abstimmung |

Hinweis: Expand-und-Contract-Regel: Die alte Eindeutigkeit (poll_id, user_id) bleibt, damit alter Code beim rollenden Update weiter schreiben kann.

#### F3 `learning_poll_votes` – Namentliche Stimme
**Zweck:** Speichert die Stimme einer namentlichen Abstimmung (Person und gewählte Antwort).
**Eindeutig:** (poll_id, user_id, option_index).
**Indizes:** poll_id; user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| poll_id | Ganzzahl | Pflicht | — | learning_polls.id, Kaskade | Abstimmung |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | abstimmende Person |
| option_index | Ganzzahl | Pflicht | — | — | Nummer der gewählten Antwort (Zählweise [unklar]) |

Hinweis: Anonyme Abstimmungen speichern hier nichts.

#### F4 `learning_poll_tally` – Stimmzähler bei anonymen Abstimmungen
**Zweck:** Zählt die Stimmen je Antwort, ohne Bezug zu einer Person.
**Eindeutig:** (poll_id, option_index).
**Indizes:** poll_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| poll_id | Ganzzahl | Pflicht | — | learning_polls.id, Kaskade | Abstimmung |
| option_index | Ganzzahl | Pflicht | — | — | Nummer der Antwort |
| count | Ganzzahl | Pflicht | 0 | — | Stimmen für diese Antwort; wird atomar um 1 erhöht |

#### F5 `learning_surveys` – Umfrage (Feedback-Fragebogen)
**Zweck:** Fragebogen im Kursraum, anonym oder namentlich.
**Eindeutig:** keine.
**Indizes:** channel_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | Pflicht | — | channels.id, Kaskade | Kursraum |
| title | Text(200) | Pflicht | — | — | Titel |
| intro_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Einleitung; AAD `learning_surveys.intro:<id>` |
| fields | JSON | Pflicht | leere Liste | — | Fragen des Fragebogens (Formular-Baukasten; Feldstruktur [unklar]) |
| anonymous | Ja/Nein | Pflicht | nein | — | anonyme Umfrage |
| status | Text(12) | Pflicht | "entwurf" | — | entwurf / offen / geschlossen |
| closes_at | Zeit | optional | NULL | — | Schlusszeit (UTC) |
| results_to_students | Ja/Nein | Pflicht | nein | — | Ergebnisse für Schüler/innen sichtbar |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

#### F6 `learning_survey_responses` – Antwort auf eine Umfrage
**Zweck:** Speichert die Antworten zu einer Umfrage.
**Eindeutig:** (survey_id, user_id); bei anonymen Antworten (NULL) gilt die Eindeutigkeit nicht, der Doppelschutz läuft über das Teilnahme-Token.
**Indizes:** survey_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| survey_id | Ganzzahl | Pflicht | — | learning_surveys.id, Kaskade | Umfrage |
| user_id | Ganzzahl | optional | NULL | users.id, Kaskade | NULL bei anonymen Umfragen |
| answers_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Antworten; AAD `learning_survey_responses.answers:<id>` |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | bei anonymen Umfragen nur das Tagesdatum |

#### F7 `learning_survey_participants` – Teilnahme an einer Umfrage
**Zweck:** Verhindert Doppelabgaben bei Umfragen.
**Eindeutig:** (survey_id, user_id); (survey_id, token).
**Indizes:** survey_id; user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| survey_id | Ganzzahl | Pflicht | — | learning_surveys.id, Kaskade | Umfrage |
| user_id | Ganzzahl | optional | NULL | users.id, Kaskade | nur bei namentlichen Umfragen |
| token | Text(64) | optional | NULL | — | Token gegen Doppelabgaben (Bildung [unklar]) |

#### F8 `learning_questions` – Frage der Fragensammlung
**Zweck:** Fragensammlung eines Kursraums; Frage samt Lösung verschlüsselt.
**Eindeutig:** keine.
**Indizes:** channel_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | Pflicht | — | channels.id, Kaskade | Kursraum |
| qtype | Text(12) | Pflicht | — | — | Fragetyp (Werte [unklar]) |
| category | Text(60) | Pflicht | "" | — | Kategorie (Klartext) |
| data_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Frage samt Lösung; AAD `learning_questions.data:<id>` |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

#### F9 `learning_selftests` – Selbsttest
**Zweck:** Test mit Fragenauswahl, Versuchen, Zeitlimit, Mischung und Rückmeldung.
**Eindeutig:** keine.
**Indizes:** channel_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | Pflicht | — | channels.id, Kaskade | Kursraum |
| title | Text(200) | Pflicht | — | — | Titel |
| description_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Beschreibung; AAD `learning_selftests.description:<id>` |
| status | Text(12) | Pflicht | "entwurf" | — | entwurf / offen / geschlossen |
| question_ids | JSON | Pflicht | leere Liste | kein FK | Auswahl und Reihenfolge der Fragen (IDs aus learning_questions) |
| max_attempts | Ganzzahl | optional | NULL | — | erlaubte Versuche je Person; NULL-Bedeutung [unklar] |
| time_limit_min | Ganzzahl | optional | NULL | — | Zeitlimit in Minuten; NULL-Bedeutung [unklar] |
| shuffle_questions | Ja/Nein | Pflicht | nein | — | Fragen mischen |
| shuffle_answers | Ja/Nein | Pflicht | ja | — | Antworten mischen |
| immediate_feedback | Ja/Nein | Pflicht | nein | — | Rückmeldung direkt nach jeder Antwort |
| review | Text(8) | Pflicht | "full" | — | Einsicht nach Abgabe: none (keine) / score (nur Punkte) / full (vollständig) |
| pass_percent | Zahl | optional | NULL | — | Bestehensgrenze in Prozent |
| opens_at | Zeit | optional | NULL | — | Beginn (UTC) |
| closes_at | Zeit | optional | NULL | — | Ende (UTC) |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

#### F10 `learning_attempts` – Versuch eines Selbsttests
**Zweck:** Ein Versuch einer Person mit Fragenabbild zum Start, Antworten und Ergebnis.
**Eindeutig:** (test_id, user_id, number); höchstens ein laufender Versuch je (test_id, user_id) (partieller Eindeutigkeitsindex, solange finished_at leer ist).
**Indizes:** test_id; user_id; partieller Index für den laufenden Versuch.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| test_id | Ganzzahl | Pflicht | — | learning_selftests.id, Kaskade | Selbsttest |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Person |
| number | Ganzzahl | Pflicht | 1 | — | Versuchsnummer, ab 1 |
| seed | Ganzzahl | Pflicht | 0 | — | Startwert der Zufallsmischung |
| started_at | Zeit | Pflicht | aktuelle Zeit | — | Start |
| deadline_at | Zeit | optional | NULL | — | Frist (UTC); Berechnungsregel [unklar] |
| finished_at | Zeit | optional | NULL | — | Abgabe (UTC); leer = laufend |
| snapshot_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Fragen zum Startzeitpunkt; AAD `learning_attempts.snapshot:<id>` |
| answers_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Antworten; AAD `learning_attempts.answers:<id>` |
| result_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Ergebnis je Frage; AAD `learning_attempts.result:<id>` |
| points | Zahl | optional | NULL | — | erreichte Punkte, KLARTEXT (für Notenbuch und Abschlussbedingung) |
| max_points | Zahl | optional | NULL | — | Höchstpunktzahl, KLARTEXT |
| percent | Zahl | optional | NULL | — | Prozent, KLARTEXT |

---

### G Nachschreiben

#### G1 `exam_makeup_dates` – Nachschreibtermin
**Zweck:** Ein Termin zum Nachschreiben einer Klausur; mehrere Personen können denselben Termin teilen.
**Eindeutig:** keine.
**Indizes:** exam_id; date; room.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| exam_id | Text(80) | Pflicht | — | kein FK | Klausur-ID aus dem Planungsdokument |
| date | Text(10) | Pflicht | — | — | Datum (Format [unklar]) |
| start | Ganzzahl | Pflicht | 0 | — | Beginn als Stundenangabe (Zählweise [unklar]) |
| length | Ganzzahl | Pflicht | 1 | — | Dauer in Stunden (Standard 1 Stunde) |
| room | Text(40) | optional | NULL | — | Raum (Bezeichnung) |
| note | Langtext | Pflicht | "" | — | Notiz, KLARTEXT (nicht verschlüsselt) |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

#### G2 `exam_makeups` – Nachschreib-Vorgang je Person
**Zweck:** Je verpasster Klausur und Person ein Vorgang bis zum Nachschreiben.
**Eindeutig:** (exam_id, student_id).
**Indizes:** exam_id; student_id; exam_date; absence_id; status; date_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| exam_id | Text(80) | Pflicht | — | kein FK | Klausur-ID |
| student_id | Text(40) | Pflicht | — | kein FK | Schüler-ID; KLARTEXT-PERSONENBEZUG |
| course_id | Text(80) | Pflicht | "" | kein FK | Kurs-ID |
| exam_date | Text(10) | Pflicht | — | — | Datum der verpassten Klausur |
| source | Text(20) | Pflicht | "krank" | — | krank / fehlt (aus dem Klassenbuch) |
| absence_id | Ganzzahl | optional | NULL | kein FK | Verweis auf die Fehlzeit |
| status | Text(20) | Pflicht | "offen" | — | offen → angesetzt → erledigt oder entfallen |
| date_id | Ganzzahl | optional | NULL | exam_makeup_dates.id, NULL | festgelegter Nachschreibtermin |
| attest_waived | Ja/Nein | Pflicht | nein | — | Attest-Verzicht durch Klassenleitung oder Sekretariat |
| waived_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| handled_by_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

Hinweise: Das Attest wird nicht hier gespeichert, sondern aus den Dokumenten der Fehlzeit abgeleitet (Tabelle `student_documents`). Anzeigetexte je Status: offen = „Termin offen“, angesetzt = „Termin festgelegt“, erledigt = „nachgeschrieben“, entfallen = „entfällt“.

---

### H E-Mail-Konten

#### H1 `mail_accounts` – Verbundenes E-Mail-Konto
**Zweck:** Externes E-Mail-Konto, über das Nachrichten an externe Adressen versendet und eingehende Mails ins Postfach geholt werden.
**Eindeutig:** (user_id, email).
**Indizes:** user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Konto der Person |
| provider | Text(20) | Pflicht | "custom" | — | google / apple / microsoft / gmx / webde / tonline / yahoo / custom |
| email | Text(254) | Pflicht | — | — | E-Mail-Adresse des Kontos; KLARTEXT-PERSONENBEZUG |
| display_name | Text(200) | Pflicht | "" | — | Anzeigename; KLARTEXT-PERSONENBEZUG |
| auth | Text(10) | Pflicht | "password" | — | password / oauth2 |
| username | Text(254) | Pflicht | "" | — | Benutzername beim Anbieter; KLARTEXT-PERSONENBEZUG |
| secret_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Zugangsdaten als JSON (App-Passwort oder OAuth-Token); AAD `mail_accounts.secret:<id>` |
| imap_host | Text(200) | Pflicht | "" | — | IMAP-Server (Klartext) |
| imap_port | Ganzzahl | Pflicht | 993 | — | IMAP-Port (993) |
| smtp_host | Text(200) | Pflicht | "" | — | SMTP-Server (Klartext) |
| smtp_port | Ganzzahl | Pflicht | 587 | — | SMTP-Port (587) |
| smtp_security | Text(10) | Pflicht | "starttls" | — | ssl / starttls |
| sync_enabled | Ja/Nein | Pflicht | ja | — | Abruf eingehender Mails aktiv |
| is_default | Ja/Nein | Pflicht | nein | — | Standardkonto für den Versand; Eindeutigkeit im Modell nicht festgelegt |
| uidvalidity | Ganzzahl | optional | NULL | — | Gültigkeitskennung des IMAP-Ordners |
| last_uid | Ganzzahl | Pflicht | 0 | — | zuletzt abgerufene Nachrichtennummer |
| last_sync_at | Zeit | optional | NULL | — | letzter Abruf |
| last_error | Text(500) | Pflicht | "" | — | letzte Fehlermeldung (Klartext) |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |

---

### I Postfach

#### I1 `conversations` – Unterhaltung
**Zweck:** Unterhaltung im internen Postfach: direkt, Gruppe oder Rundschreiben; optional mit externen E-Mail-Teilnehmenden.
**Eindeutig:** keine.
**Indizes:** created_by; parent_id; mail_account_id; last_message_at; migrated_chat_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| subject_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT (oder leer): Betreff; AAD `conversations.subject:<conversation_id>` |
| kind | Text(20) | Pflicht | "direct" | — | direct / group / broadcast (Rundschreiben nur mit Recht messages.broadcast) |
| allow_replies | Text(10) | Pflicht | "all" | — | Antworten: all / sender / none |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| parent_id | Ganzzahl | optional | NULL | conversations.id, NULL | bei privater Antwort auf ein Rundschreiben: das Rundschreiben |
| audience | JSON | optional | NULL | — | Zielgruppen eines Rundschreibens: Liste aus kind, ref, label (nur Bezeichnungen, keine Namen) |
| external | JSON | optional | NULL | — | externe E-Mail-Beteiligte: Liste aus email, name, role (to / cc / bcc / from) |
| mail_account_id | Ganzzahl | optional | NULL | kein FK im Modell (nur außerhalb SQLite laut Migration); Löschverhalten [unklar] | verbundenes E-Mail-Konto |
| recipient_count | Ganzzahl | Pflicht | 0 | — | Anzahl Empfänger |
| last_message_id | Ganzzahl | Pflicht | 0 | — | ID der letzten Nachricht |
| last_message_at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt der letzten Nachricht |
| mail_native | Ja/Nein | Pflicht | ja (neue Zeilen); nein (DB-Standard für Bestandszeilen) | — | als Brief angelegt; bleibt im Postfach und wird nie zum Chat |
| migrated_chat_id | Ganzzahl | optional | NULL | kein FK | Chat, in den der Verlauf kopiert wurde (Unterhaltung bleibt erhalten, erscheint nicht mehr im Postfach) |

#### I2 `conversation_participants` – Teilnahme an einer Unterhaltung
**Zweck:** Lesestand, Archiv, Stummschaltung und „für mich gelöscht“ je Konto und Unterhaltung.
**Eindeutig:** PK (conversation_id, user_id).
**Indizes:** user_id; zusammengesetzt (user_id, deleted, archived) für die Ordneransicht.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| conversation_id | Ganzzahl | Pflicht (PK) | — | conversations.id, Kaskade | Unterhaltung |
| user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | Konto |
| last_read_at | Zeit | optional | NULL | — | letzter Lesezeitpunkt |
| last_read_id | Ganzzahl | Pflicht | 0 | — | höchste gelesene Nachrichten-ID (Grundlage des Ungelesen-Zählers) |
| archived | Ja/Nein | Pflicht | nein | — | archiviert |
| deleted | Ja/Nein | Pflicht | nein | — | „für mich gelöscht“ |
| muted | Ja/Nein | Pflicht | nein | — | stummgeschaltet |
| cleared_id | Ganzzahl | Pflicht | 0 | — | Nachrichten bis zu dieser ID sind ausgeblendet |
| has_incoming | Ja/Nein | Pflicht | nein | — | mindestens eine Nachricht anderer (Posteingang) |
| has_sent | Ja/Nein | Pflicht | nein | — | mindestens eine eigene Nachricht (Gesendet) |
| joined_at | Zeit | Pflicht | aktuelle Zeit | — | Beitritt |
| recipient_role | Text(4) | Pflicht | "to" | — | to / cc / bcc; bei bcc sieht die Person nur sich selbst |

#### I3 `messages` – Nachricht
**Zweck:** Eine Nachricht innerhalb einer Unterhaltung, mit Anhängen und Zustellstatus bei externen Adressen.
**Eindeutig:** keine (PK id).
**Indizes:** conversation_id; (conversation_id, id); sender_id; (sender_id, created_at); created_at; mail_message_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| conversation_id | Ganzzahl | Pflicht | — | conversations.id, Kaskade | Unterhaltung |
| sender_id | Ganzzahl | optional | NULL | users.id, NULL | Absender; beim Löschen des Kontos geleert |
| body_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Nachrichtentext; AAD `messages.body:<conversation_id>:<message_id>` |
| attachment_ids | JSON | Pflicht | leere Liste | kein FK | Anhänge (IDs aus der Dateiablage) |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Sendezeitpunkt |
| removed_at | Zeit | optional | NULL | — | von der Moderation ausgeblendet; Inhalt bleibt verschlüsselt als Beleg |
| removed_by | Ganzzahl | optional | NULL | users.id, NULL | ausblendende Person |
| external_from | Text(254) | optional | NULL | — | Absenderadresse einer eingegangenen externen Mail |
| external_name | Text(200) | optional | NULL | — | Absendername einer eingegangenen externen Mail; KLARTEXT-PERSONENBEZUG |
| mail_message_id | Text(500) | optional | NULL | — | Message-ID der Mail (Zuordnung von Antworten) |
| delivery | JSON | optional | NULL | — | Versandstatus an externe Adressen: status (sent / failed / pending), error, at, to (Liste) |

#### I4 `message_reports` – Meldung an die Moderation
**Zweck:** Eine Meldung einer Nachricht an die Moderation, mit Bearbeitung und Maßnahmen.
**Eindeutig:** keine.
**Indizes:** message_id; reporter_id; status; created_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| message_id | Ganzzahl | Pflicht | — | messages.id, Kaskade | gemeldete Nachricht |
| reporter_id | Ganzzahl | optional | NULL | users.id, NULL | meldende Person |
| category | Text(20) | Pflicht | "sonstiges" | — | belaestigung / beleidigung / bedrohung / spam / unangemessen / sonstiges |
| reason_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Begründung; AAD `message_reports.reason:<report_id>` |
| status | Text(20) | Pflicht | "offen" | — | offen / erledigt / abgelehnt |
| handled_by | Ganzzahl | optional | NULL | users.id, NULL | bearbeitende Person |
| handled_at | Zeit | optional | NULL | — | Bearbeitungszeitpunkt |
| resolution_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Vermerk der Moderation; AAD `message_reports.resolution:<report_id>` |
| actions | JSON | optional | NULL | — | getroffene Maßnahmen, z. B. removed, suspended |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Meldezeitpunkt |

#### I5 `user_blocks` – Blockierung
**Zweck:** Eine Person nimmt keine Nachrichten einer blockierten Person mehr an.
**Eindeutig:** PK (user_id, blocked_user_id).
**Indizes:** blocked_user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | blockierende Person |
| blocked_user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | blockierte Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt der Blockierung |

#### I6 `message_user_settings` – Postfach-Einstellungen und Sperre
**Zweck:** E-Mail-Hinweis-Einstellung je Konto und Postfach-Sperre durch die Moderation.
**Eindeutig:** PK user_id.
**Indizes:** suspended_until.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | Konto |
| email_notify | Ja/Nein | Pflicht | ja | — | E-Mail-Hinweis bei neuer Nachricht |
| suspended_until | Zeit | optional | NULL | — | Postfach gesperrt bis zu diesem Zeitpunkt |
| suspended_by | Ganzzahl | optional | NULL | users.id, NULL | sperrende Person |
| suspended_at | Zeit | optional | NULL | — | Zeitpunkt der Sperre |
| suspension_reason_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Grund der Sperre; AAD `message_user_settings.suspension_reason:<user_id>` |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

#### I7 `message_drafts` – Entwurf
**Zweck:** Entwurf einer neuen Nachricht oder einer Antwort.
**Eindeutig:** keine (PK id).
**Indizes:** user_id; conversation_id; updated_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Verfasser |
| conversation_id | Ganzzahl | optional | NULL | conversations.id, Kaskade | Unterhaltung; NULL = neue Nachricht |
| data_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Entwurf als JSON; AAD `message_drafts.data:<user_id>:<draft_id>` |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |

---

### J Benachrichtigungen

#### J1 `notifications` – Benachrichtigung
**Zweck:** Eine Benachrichtigung für genau ein Konto; Titel und Text ohne sensible Einzelheiten.
**Eindeutig:** (user_id, dedupe_key) – verhindert Doppelte je Konto (NULL-Werte sind mehrfach erlaubt).
**Indizes:** user_id; created_at; (user_id, read_at).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Empfänger |
| kind | Text(40) | Pflicht | — | — | Ereignisart (Werte [unklar]) |
| title_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Titel; AAD `notifications.title:<id>` |
| body_enc | Langtext | Pflicht | "" | — | VERSCHLÜSSELT: Text; AAD `notifications.body:<id>` |
| link | Text(300) | Pflicht | "" | — | Verweis innerhalb der App (Klartext) |
| student_id | Text(40) | optional | NULL | kein FK | betroffenes Kind (Eltern sehen es je Kind); KLARTEXT-PERSONENBEZUG |
| ref | Text(80) | optional | NULL | kein FK | Verweis auf das betroffene Objekt |
| dedupe_key | Text(64) | optional | NULL | — | Schlüssel gegen Doppelte je Konto |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Erstellung |
| read_at | Zeit | optional | NULL | — | Lesezeitpunkt; NULL = ungelesen |
| mail_state | Text(10) | Pflicht | "" | — | "" keine Mail / sent sofort versandt / later wartet auf Ende der Ruhezeit / digest wartet auf Tageszusammenfassung / digested in ihr versandt |

#### J2 `notification_prefs` – Einstellung je Konto und Ereignisart
**Zweck:** Legt je Konto und Ereignisart den Versandweg fest.
**Eindeutig:** (user_id, kind).
**Indizes:** user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Konto |
| kind | Text(40) | Pflicht | — | — | Ereignisart |
| mode | Text(10) | Pflicht | "app" | — | aus / app / mail |

#### J3 `notification_user_settings` – Zusammenfassung und Ruhezeit je Konto
**Zweck:** Tägliche Zusammenfassung und Ruhezeiten je Konto (Ruhezeit gilt nur für E-Mails).
**Eindeutig:** PK user_id.
**Indizes:** keine weiteren.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| user_id | Ganzzahl | Pflicht (PK) | — | users.id, Kaskade | Konto |
| digest | Ja/Nein | Pflicht | nein | — | tägliche Zusammenfassung per E-Mail |
| digest_sent_on | Text(10) | optional | NULL | — | Tag der letzten Zusammenfassung |
| quiet_enabled | Ja/Nein | Pflicht | nein | — | Ruhezeit aktiv |
| quiet_from | Text(5) | Pflicht | "21:00" | — | Beginn der Ruhezeit (Uhrzeit HH:MM) |
| quiet_to | Text(5) | Pflicht | "07:00" | — | Ende der Ruhezeit (Uhrzeit HH:MM) |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |

#### J4 `notification_school` – Schulvorgabe je Ereignisart
**Zweck:** Standard-Modus je Ereignisart, der schulweit gilt; kann für Konten gesperrt werden.
**Eindeutig:** PK kind.
**Indizes:** keine.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| kind | Text(40) | Pflicht (PK) | — | — | Ereignisart |
| mode | Text(10) | Pflicht | "app" | — | aus / app / mail |
| locked | Ja/Nein | Pflicht | nein | — | ja = Vorgabe ist Pflicht und für Konten nicht änderbar |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |

#### J5 `notification_config` – Schuleinstellungen der Benachrichtigungen
**Zweck:** Schlüssel/Wert-Speicher für Schuleinstellungen der Benachrichtigungen (z. B. Aufbewahrungsdauer).
**Eindeutig:** PK key.
**Indizes:** keine.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| key | Text(40) | Pflicht (PK) | — | — | Name der Einstellung, z. B. retention_days |
| value | Text(200) | Pflicht | "" | — | Wert als Text; Standardwert von retention_days [unklar] |

---

### K Betrieb

#### K1 `system_state` – Zustandsspeicher
**Zweck:** Kleine Schlüssel/Wert-Ablage für Systemzustand ohne eigene Tabelle (Einrichtung, Schulprofil, Schuljahreswechsel, letzter Wartungslauf).
**Eindeutig:** PK key.
**Indizes:** keine.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| key | Text(80) | Pflicht (PK) | — | — | Schlüssel: setup (Fortschritt Einrichtung), school_profile (Schulprofil), yearchange (Läufe Schuljahreswechsel), maintenance (letzter Wartungslauf) |
| value | JSON | optional | NULL | — | Zustandswert; keine Freitexte über Personen |
| updated_at | Zeit | Pflicht | aktuelle Zeit (bei jeder Änderung neu) | — | letzte Änderung |
| updated_by | Text(80) | optional | NULL | — | bearbeitende Person oder System |

#### K2 `error_log` – Fehlerprotokoll
**Zweck:** Fehlerprotokoll für die Administration; nur Fehler und kritische Meldungen.
**Eindeutig:** keine (PK id).
**Indizes:** created_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt des Fehlers |
| level | Text(10) | Pflicht | "ERROR" | — | ERROR / CRITICAL (nur diese werden gespeichert) |
| logger | Text(120) | Pflicht | "" | — | Name der meldenden Stelle |
| message | Langtext | Pflicht | "" | — | Meldung, gekürzt |
| request_id | Text(40) | optional | NULL | — | Anfrage-Kennung |
| path | Text(300) | optional | NULL | — | Anfragepfad ohne Abfrageteil, Kennungen maskiert |
| trace | Langtext | optional | NULL | — | technische Ablaufverfolgung |

Hinweis: Grenzen 30 Tage bzw. 1000 Einträge (siehe Abschnitt 3).

---

### L Elternzugriff

#### L1 `parent_access` – Freigabe für Eltern je Bereich
**Zweck:** Je volljährige Person und Bereich (z. B. Kursräume, Krankmeldungen, Dokumente, Stundenplan): dürfen die Eltern sehen.
**Eindeutig:** (student_id, area).
**Indizes:** student_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| student_id | Text(40) | Pflicht | — | kein FK | Schüler-ID (Planungsdokument); KLARTEXT-PERSONENBEZUG |
| area | Text(40) | Pflicht | — | — | Bereich: kursraeume / krankmeldungen / dokumente / stundenplan / weitere [unklar] |
| allowed | Ja/Nein | Pflicht | nein | — | Eltern dürfen den Bereich sehen |
| set_by | Ganzzahl | optional | NULL | users.id, NULL | festlegende Person |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |

#### L2 `student_prefs` – Einstellungen zum Elternzugriff je Person
**Zweck:** Legt fest, wohin Schulinformationen für eine volljährige Person gehen und wann sie die Freigaben bewusst gespeichert hat.
**Eindeutig:** PK student_id.
**Indizes:** keine.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| student_id | Text(40) | Pflicht (PK) | — | kein FK | Schüler-ID; KLARTEXT-PERSONENBEZUG |
| delivery | Text(10) | Pflicht | "self" | — | self (nur an die Person) / parents (nur an die Eltern) / both (beide); minderjährig immer both |
| decided_at | Zeit | optional | NULL | — | erstmals bewusst gespeichert; NULL = Hinweis „Du bist volljährig“ bleibt sichtbar |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |

---

### M Plan-Prüfung

#### M1 `plan_proposals` – Vorschlagspaket der Plan-Prüfung
**Zweck:** Ein Paket mit Anlass, Problemliste und Lösungsvarianten, das entsteht, wenn die Prüfung Probleme im regulären Stundenplan findet.
**Eindeutig:** keine.
**Indizes:** status; created_at; state_hash.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| status | Text(20) | Pflicht | "berechnung" | — | berechnung / offen / angenommen / verworfen / ersetzt / erledigt / veraltet / fehlgeschlagen |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | Pflicht | aktuelle Zeit | — | letzte Änderung |
| base_version | Ganzzahl | optional | NULL | kein FK | Stand des Plans zur Anzeige (Planversion) |
| state_hash | Text(32) | Pflicht | "" | — | GEHASHT: Stunden und Problemlage zum Zeitpunkt der Berechnung |
| signature | Text(32) | Pflicht | "" | — | Kennung der Problemlage (Form [unklar]) |
| title | Text(300) | Pflicht | "" | — | Titel |
| reasons | JSON | optional | NULL | — | lesbare Probleme (Liste) |
| trigger_scope | JSON | optional | NULL | — | Änderungsquellen, die die Berechnung ausgelöst haben |
| problem_count | Ganzzahl | Pflicht | 0 | — | Anzahl der Probleme |
| valid_from | Text(10) | optional | NULL | — | ISO-Datum, ab dem der Anlass gilt |
| postponed_until | Zeit | optional | NULL | — | „später“: zurückgestellt bis zu diesem Zeitpunkt |
| postponed_by | Text(80) | optional | NULL | — | zurückstellende Person (Kürzel) |
| decided_at | Zeit | optional | NULL | — | Entscheidungszeitpunkt |
| decided_by_id | Ganzzahl | optional | NULL | kein FK (Nachweis bleibt) | Konto-ID der entscheidenden Person |
| decided_by | Text(200) | optional | NULL | — | KLARTEXT-PERSONENBEZUG: Name der entscheidenden Person |
| decision_note | Text(500) | optional | NULL | — | Begründung der Entscheidung (Freitext, max. 500 Zeichen) |
| chosen_variant_id | Ganzzahl | optional | NULL | kein FK | gewählte Variante |
| applied_version | Ganzzahl | optional | NULL | — | Planversion nach der Übernahme |
| informed | JSON | optional | NULL | — | nach Annahme informierte Lehrkräfte (Liste) |

#### M2 `plan_proposal_variants` – Lösungsvariante eines Pakets
**Zweck:** Eine zur Wahl stehende Lösung mit Kennzahlen vorher und nachher, Änderungsliste und Unterschied zum Plan.
**Eindeutig:** keine.
**Indizes:** package_id; (package_id, position).

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| package_id | Ganzzahl | Pflicht | — | plan_proposals.id, Kaskade | Vorschlagspaket |
| key | Text(20) | Pflicht | — | — | minimal / lokal / gruendlich / vertretung / raeume |
| position | Ganzzahl | Pflicht | 0 | — | Reihenfolge der Varianten |
| title | Text(200) | Pflicht | "" | — | Titel |
| description | Langtext | Pflicht | "" | — | Beschreibung |
| status | Text(20) | Pflicht | "berechnung" | — | berechnung / bereit / keine_loesung / fehlgeschlagen |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| metrics_before | JSON | optional | NULL | — | Kennzahlen vor der Änderung |
| metrics_after | JSON | optional | NULL | — | Kennzahlen nach der Änderung |
| changes | JSON | optional | NULL | — | Änderungsliste (lesbar) |
| affected_classes | JSON | optional | NULL | — | betroffene Klassen |
| affected_teachers | JSON | optional | NULL | — | betroffene Lehrkräfte (Kürzel) |
| moved_lessons | Ganzzahl | Pflicht | 0 | — | Anzahl verschobener Stunden |
| remaining | JSON | optional | NULL | — | danach noch offene Probleme |
| valid_from | Text(10) | optional | NULL | — | ISO-Datum, ab dem die Variante gilt |
| diff | JSON | optional | NULL | — | Unterschied zum Plan: upsert (Stunden) und delete (IDs) |
| compute_seconds | Zahl | Pflicht | 0.0 | — | Rechendauer in Sekunden |

#### M3 `plan_proposal_log` – Verlauf eines Pakets
**Zweck:** Unveränderlicher Verlauf (nur anhängen): erzeugt, ersetzt, später, angenommen, verworfen, informiert usw.
**Eindeutig:** keine.
**Indizes:** package_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| package_id | Ganzzahl | Pflicht | — | kein FK (Verlauf bleibt erhalten) | Vorschlagspaket |
| at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt |
| action | Text(30) | Pflicht | — | — | Aktion (Liste unvollständig [unklar]) |
| actor_id | Ganzzahl | optional | NULL | kein FK | handelnde Person (Konto-ID) |
| actor_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name bzw. Kürzel |
| variant_id | Ganzzahl | optional | NULL | kein FK | betroffene Variante |
| note | Text(500) | optional | NULL | — | Notiz |
| detail | JSON | optional | NULL | — | Einzelheiten |

---

### N Plan-Stände

#### N1 `plan_snapshots` – Gespeicherter Plan-Stand
**Zweck:** Der Stundenplan (nur die Unterrichtsblöcke) unter einem Namen, z. B. „Stand Herbst A“; bleibt bis zum Löschen erhalten.
**Eindeutig:** keine.
**Indizes:** created_at.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| name | Text(120) | Pflicht | — | — | Name des Plan-Stands |
| note | Text(500) | Pflicht | "" | — | Notiz zum Plan-Stand |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Speicherzeitpunkt |
| user_id | Ganzzahl | optional | NULL | users.id, NULL | speichernde Person |
| user_name | Text(200) | Pflicht | "" | — | KLARTEXT-PERSONENBEZUG: Name |
| source | Text(20) | Pflicht | "aktuell" | — | aktuell / entwurf |
| source_version | Ganzzahl | optional | NULL | — | Planversion beim Speichern |
| lessons_count | Ganzzahl | Pflicht | 0 | — | Anzahl der Stunden |
| period | Text(20) | Pflicht | "" | kein FK (Planzeitraum aus plan_periods) | leer = ganzer Plan; sonst nur die Stunden des Zeitraums |
| data | Binär | Pflicht | — | — | Stunden als zlib-komprimiertes JSON |
| metrics | JSON | optional | NULL | — | Kennzahlen zum Zeitpunkt des Speicherns |

Hinweis: Wiederherstellen legt wie jede Änderung eine neue Plan-Version an (rückgängig über den Verlauf).

---

### O Lernfortschritt

#### O1 `completion_rules` – Abschlussbedingung eines Elements
**Zweck:** Legt fest, wie ein Element im Kursraum als erledigt gilt (manuell, angesehen, abgegeben, bewertet, bestanden).
**Eindeutig:** (channel_id, element_type, element_id).
**Indizes:** channel_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | Pflicht | — | channels.id, Kaskade | Kursraum |
| element_type | Text(30) | Pflicht | — | kein FK (generisch) | Art des Elements, z. B. item (Material oder Aufgabe), Abstimmung, Selbsttest |
| element_id | Ganzzahl | Pflicht | — | kein FK (generisch) | ID des Elements |
| mode | Text(20) | Pflicht | "manual" | — | manual / viewed / submitted / graded / passed |
| pass_percent | Ganzzahl | optional | NULL | — | Bestehensgrenze in Prozent (bei passed) |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

#### O2 `completion_marks` – Manuelles Erledigt-Häkchen
**Zweck:** Das Häkchen „Erledigt“, das eine Person bei manuellen Elementen setzt.
**Eindeutig:** (element_type, element_id, user_id).
**Indizes:** channel_id; user_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | Pflicht | — | channels.id, Kaskade | Kursraum |
| element_type | Text(30) | Pflicht | — | kein FK (generisch) | Art des Elements |
| element_id | Ganzzahl | Pflicht | — | kein FK (generisch) | ID des Elements |
| user_id | Ganzzahl | Pflicht | — | users.id, Kaskade | Schüler/in |
| done_at | Zeit | Pflicht | aktuelle Zeit | — | Zeitpunkt des Häkchens |

#### O3 `availability_rules` – Bedingte Freigabe
**Zweck:** Macht ein Element nur verfügbar, wenn verschachtelte UND/ODER-Bedingungen erfüllt sind.
**Eindeutig:** (channel_id, element_type, element_id).
**Indizes:** channel_id.

| Spalte | Typ | Pflicht/optional | Standard | Fremdschlüssel (Löschen) | Hinweise |
|---|---|---|---|---|---|
| id | Ganzzahl | Pflicht (PK) | automatisch | — | Primärschlüssel |
| channel_id | Ganzzahl | Pflicht | — | channels.id, Kaskade | Kursraum |
| element_type | Text(30) | Pflicht | — | kein FK (generisch) | Art des Elements |
| element_id | Ganzzahl | Pflicht | — | kein FK (generisch) | ID des Elements |
| tree | JSON | optional | NULL | — | verschachtelter UND/ODER-Baum der Bedingungen |
| created_by | Ganzzahl | optional | NULL | users.id, NULL | anlegende Person |
| created_at | Zeit | Pflicht | aktuelle Zeit | — | Anlage |
| updated_at | Zeit | optional | NULL | — | letzte Änderung |

---

## 3 Übergreifende Werte und Regeln

Jede Zeile ist ein Wert oder eine Regel. Zahlen mit Einheit.

**Verschlüsselung und Schutz**
1. `_enc`-Spalten liegen nur als Chiffrat in der Datenbank; leerer Text bleibt leer und wird nicht verschlüsselt.
2. Kontextbindung (AAD) je verschlüsseltem Wert: `<tabelle>.<feld>:<id>`, wobei `<feld>` der Spaltenname ohne `_enc` ist.
3. Abweichende AAD: messages.body = `messages.body:<conversation_id>:<message_id>`; message_drafts.data = `message_drafts.data:<user_id>:<draft_id>`; message_user_settings.suspension_reason = `…:<user_id>`; sso_providers = `sso_providers.<feld>:<Anbieter>`; letter_batches = `letter_batches:<id>`.
4. Verschobene oder vertauschte Chiffrate einer Nachricht gelten beim Lesen als Manipulation.
5. Verschlüsselte Werte tragen das Präfix `SM1`.
6. Nicht entschlüsselbare Texte werden als „[nicht lesbar]“ angezeigt (Schlüssel- oder Datenfehler) und protokolliert.
7. Schlüsselrotation über den CLI-Befehl `cli rotate-keys` packt alle `_enc`-Spalten mit dem aktiven Schlüssel neu; Nutzdaten und AAD bleiben gleich.
8. Die Absender-ID einer Nachricht gehört nicht zur AAD; sie wird beim Löschen des Kontos geleert, die Nachricht bleibt lesbar.
9. Chat-Inhalte sind Ende-zu-Ende verschlüsselt; der Server kennt nur Schlüssel, Verweise und Zählwerte (Doppelsende-Schutz, Chat-Abstimmung).
10. Startpasswörter werden nur als Hash gespeichert, kein Klartext.
11. Teilnahme-Token einer Abstimmung: HMAC aus Server-Geheimnis, Abstimmung und Konto.
12. Anonyme Abstimmung: keine Verknüpfung von Stimme und Person; gespeichert wird nur ein Zähler je Antwort.
13. Anonyme Umfrage: ohne user_id; Zeitpunkt nur als Tagesdatum; Antworten werden nie personenbezogen ausgegeben.
14. Zugangsdaten verbundener E-Mail-Konten liegen nur verschlüsselt als JSON vor.

**Fristen, Standards und Grenzen**
15. Zugangsbrief-Stapel läuft 60 min nach Anlage ab (Variable SM_LETTER_BATCH_MINUTES); danach Löschung durch die Wartung oder beim nächsten Zugriff.
16. Startpasswort: Frist 14 Tage ab Vergabe; danach nicht mehr nutzbar.
17. Fehlerprotokoll: nur ERROR und CRITICAL; Grenze 30 Tage bzw. 1000 Einträge; Meldungen gekürzt, Pfade ohne Abfrageteil.
18. Versionsverlauf des Planungsdokuments (außerhalb dieses Bereichs): nach 300 Änderungen gekürzt (Variable SM_KEEP_VERSIONS); gespeicherte Plan-Stände bleiben bis zum Löschen.
19. E-Mail-Konto Standard: IMAP-Port 993, SMTP-Port 587, SMTP-Sicherheit starttls (Alternative ssl).
20. Nachschreibtermin Standard: 1 Stunde Dauer, Beginn bei Stunde 0.
21. Abstimmung Standard: 2 Antwortmöglichkeiten, Mehrfachauswahl aus, Ergebnisse live.
22. Selbsttest Standard: Antworten mischen an, Fragen mischen aus, sofortige Rückmeldung aus, Einsicht vollständig (full).
23. Umfrage und Selbsttest starten im Status „entwurf“.
24. E-Mail-Ruhezeit Standard: aus; 21:00 bis 07:00 Uhr; gilt nur für E-Mails.
25. Benachrichtigung Standard-Modus: app; eine Schulvorgabe kann den Modus festlegen und sperren.
26. Benachrichtigungstexte ohne sensible Einzelheiten (Beispiel: „Neue Krankmeldung“ statt Diagnose).
27. Postfach E-Mail-Hinweis Standard: an.
28. Notenbuch Standard: Notenskala note6, Rundung ganz, 2 Nachkommastellen, Gewicht 1.0 je Leistung und Kategorie, Kursteil 0.
29. Notenbuch: Die Endnote wird nur als festgelegter Wert gespeichert; der Vorschlag wird immer neu berechnet.
30. Doppelsende-Schutz: ein Schlüssel je Konto und Bereich wird genau einmal angenommen; eine Wiederholung liefert die bereits gesendete Nachricht.
31. Moderation: eine ausgeblendete Nachricht bleibt verschlüsselt als Beleg bis zum Ablauf der Aufbewahrungsfrist erhalten.

**Zustände und Abläufe**
32. Nachschreib-Vorgang: offen → angesetzt → erledigt oder entfallen.
33. Plan-Vorschlagspaket: berechnung → offen → Entscheidung (angenommen, verworfen, ersetzt, erledigt, veraltet oder fehlgeschlagen).
34. Plan-Verlauf: nur anhängen; Entscheidungen sind unveränderlich.
35. Plan-Stand wiederherstellen: legt eine neue Plan-Version an (rückgängig über den Verlauf).
36. Lernfortschritt: ein Element ohne Abschlussregel wird nicht verfolgt; das Häkchen „Erledigt“ setzt die Person nur beim Modus manual.
37. Selbsttest: höchstens ein laufender Versuch je Test und Konto; Versuchsnummer ab 1, je Test und Konto eindeutig.
38. Selbsttest: spätere Änderungen an der Fragensammlung ändern kein Ergebnis eines begonnenen Versuchs.
39. Import: Trockenläufe werden nicht gespeichert; unveränderte Elemente werden nicht neu geschrieben; die Rücknahme entfernt alle Objekte, die der Lauf angelegt hat.
40. Abstimmung und Umfrage: Doppelabgaben werden über das Teilnahme-Token verhindert.
41. Postfach „für mich löschen“: ältere Nachrichten werden ausgeblendet; eine neue Nachricht holt die Unterhaltung in den Posteingang zurück.
42. Postfach BCC: Empfänger sieht nur sich selbst.
43. Postfach Blockierung: Wer blockiert, erhält keine Nachrichten der blockierten Person mehr.

**Rechte, Zuständigkeiten und Löschen**
44. Zugangsbriefe: Zugriff nur für die anlegende Person oder die Rolle admin.
45. Anmelde-Richtlinie: erlaubte Anmeldewege sind nie leer; NULL erbt vom allgemeineren Geltungsbereich.
46. Zielgruppe (audience) nur bei Jahrgang und Klasse erlaubt; sonst immer „alle“.
47. Personenbezogene Anmelde-Regel (Geltungsbereich user) wird beim Löschen des Kontos mitgelöscht; Änderungen wirken sofort (Zwischenspeicher wird geleert).
48. Elternzugriff für Volljährige: Standard nein; fehlender Eintrag = nein.
49. Elternzugriff für Minderjährige: Eltern sehen alles, was das Kind sieht.
50. Elternzustellung Standard: self (nur an die Person); minderjährig immer both.
51. Anbieterkonto: je Konto und Anbieter höchstens eine Verknüpfung; je Anbieter-Konto höchstens ein Konto.
52. Vorgemerkte Verknüpfung (subject leer): wird beim ersten Anmelden übernommen, wenn genau diese, vom Anbieter bestätigte E-Mail verwendet wird.
53. Umgebungsvariablen SM_SSO_* und SM_OIDC_* haben Vorrang vor den Werten in sso_providers.
54. Startpasswort-Zeile verschwindet bei Passwortwechsel und Löschen des Kontos.
55. Schulvorgabe der Benachrichtigung mit locked = ja: für Konten nicht änderbar.
56. Kursraum gelöscht: Lernfortschritt-Zeilen werden über channel_id mitgelöscht.
57. Element endgültig gelöscht: Lernfortschritt-Zeilen werden per Logik entfernt (ohne FK).
58. Konto gelöscht: Verknüpfungen, Teilnahmen, Benachrichtigungen, Entwürfe, Blockierungen und Einstellungen werden per Kaskade entfernt; Ersteller- und Absenderfelder werden geleert (NULL).

**Anzahl dieser Liste: 58 Werte/Regeln.**

---

## 4 Verschlüsselte, gehashte und personenbezogene Klartext-Spalten (Übersicht)

**VERSCHLÜSSELT (Chiffrat in der DB):**
- exam_results: grade_enc, note_enc
- gb_entries: value_enc, note_enc
- gb_finals: value_enc, note_enc
- gb_log: detail_enc
- sso_providers: client_secret_enc, private_key_enc
- learning_polls: question_enc, options_enc
- learning_surveys: intro_enc
- learning_survey_responses: answers_enc
- learning_questions: data_enc
- learning_selftests: description_enc
- learning_attempts: snapshot_enc, answers_enc, result_enc
- letter_batches: data_enc
- mail_accounts: secret_enc
- import_runs: report_enc
- conversations: subject_enc
- messages: body_enc
- message_reports: reason_enc, resolution_enc
- message_drafts: data_enc
- message_user_settings: suspension_reason_enc
- notifications: title_enc, body_enc

**GEHASHT (kein Klartext):**
- account_initial_passwords: password_hash (Kopie des Konto-Hashs)
- learning_poll_participants: token (HMAC)
- learning_survey_participants: token (Bildung [unklar])
- import_runs: source_hash (Prüfsumme der Quelldatei)
- import_links: fingerprint (Form [unklar])
- plan_proposals: state_hash (Hash); signature (Form [unklar])

**KLARTEXT MIT PERSONENBEZUG (Auswahl, bei der Spezifikation beachten):**
- Namen: exam_results.graded_by_name, gb_books.locked_by_name, gb_entries.entered_by_name, gb_finals.set_by_name, gb_log.actor_name, exam_makeup_dates.created_by_name, exam_makeups.waived_by_name und handled_by_name, import_runs.user_name und undone_by, plan_proposals.decided_by, plan_proposal_log.actor_name, plan_snapshots.user_name, message-Absendername (messages.external_name), notifications.student_id (betroffenes Kind), mail_accounts (email, display_name, username).
- Schüler-Kennungen im Klartext: gb_entries.student_id, gb_finals.student_id, gb_log.student_id, gb_source_results (student_id mit Note und Punkten im Klartext), exam_makeups.student_id, parent_access.student_id, student_prefs.student_id, learning_attempts (Punkte, Prozent im Klartext).
- Klartext-Notizen: exam_makeup_dates.note, plan_proposals.decision_note, letter_batches.title (Stapel-Titel), learning_questions.category.

---

## 5 Offene Punkte [unklar]

1. Standardwerte der Notenbuch-Einstellungen (gb_config): liegen nicht in den Quelldateien dieses Bereichs.
2. Werte und Beschriftungen des Notenstatus (gb_entries.status).
3. Rundungsarten außer „ganz“ (gb_books.rounding).
4. Werte von gb_log.action; Wirkung von gb_items.released.
5. Anbieterkennungen (user_identities.provider, sso_providers.provider) und Liste der Anmeldewege (login_policy_rules.methods); vollständige Liste der Kanäle für Passwort-Rücksetzung (reset_channels, dokumentiert sind nur email und sms).
6. Ereignisarten der Benachrichtigungen (notifications.kind, notification_prefs.kind) und Standardwert von retention_days.
7. Fragetypen (learning_questions.qtype) und Feldstruktur des Fragebogens (learning_surveys.fields).
8. Zählweise der Stunde (exam_makeup_dates.start); Format der Textdatums-Felder (String 10), außer plan_proposals.valid_from (ISO).
9. Bedeutung von NULL bei learning_selftests.max_attempts, learning_selftests.time_limit_min und learning_polls.max_choices.
10. Zählweise der Antwortnummer (learning_poll_votes.option_index, learning_poll_tally.option_index).
11. Vollständige Werte von import_runs.system, import_links.kind und import_links.target_kind (Liste in der Dokumentation unvollständig).
12. Vollständige Liste der Aktionen in plan_proposal_log.action.
13. Eindeutigkeit des Standardkontos (mail_accounts.is_default) ist im Modell nicht festgelegt.
14. Aufbewahrungsdauer von send_idempotency.
15. Reihenfolge der Geltungsbereiche bei der Vererbung der Anmelde-Richtlinien.
16. Bildung des Teilnahme-Tokens bei Umfragen (learning_survey_participants.token) und Form von import_links.fingerprint und plan_proposals.signature.
17. Löschverhalten von conversations.mail_account_id (kein FK im Modell).
18. Berechnungsregel für learning_attempts.deadline_at.
19. Technische Namen von Eindeutigkeiten stimmen nicht mit den Spalten überein: uq_notifications_user_id umfasst (user_id, dedupe_key); uq_parent_access_student_id umfasst (student_id, area). Maßgeblich sind die Spalten.
20. Vorgaben außerhalb dieses Bereichs, auf die sich die Tabellen beziehen: Tabellen users, channels, stored_files, student_documents, school_versions, plan_periods sowie die Anmeldewege-Liste und die Notenbuch-Standardwerte.
