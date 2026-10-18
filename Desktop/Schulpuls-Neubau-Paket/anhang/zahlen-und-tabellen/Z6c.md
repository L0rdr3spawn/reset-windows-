# Z6c – Datenmodell (Tabellen) der Feature-Module q–z

Quellenbasis: 8 Modul-Dateien mit Namen q–z, vollständig gelesen. Ergebnis: 13 Tabellen, 133 Spalten.

## 0. Konventionen und Querschnittsregeln

**Lesart der Spalten**
- Pflicht = NOT NULL (Typ ohne „optional“ in der Quelle). optional = NULL erlaubt.
- Standard = Vorgabe beim Anlegen durch die Anwendung. „kein“ = keine Vorgabe. „NULL“ = leer, wenn nicht gesetzt.
- Textlängen in Zeichen („max. N Zeichen“). Ganzzahl = Zahl ohne Nachkomma. Boolesch = ja/nein. JSON = strukturierter Wert (Liste oder Objekt). Zeit = Zeitstempel in UTC.
- Fremdschlüssel (FK) mit Löschverhalten:
  - SET NULL = beim Löschen des Zielsatzes wird das Feld leer, der Satz bleibt erhalten.
  - CASCADE = der Satz wird mit dem Zielsatz gelöscht.
  - „kein FK“ = nur logischer Verweis per ID, keine Datenbankbeziehung im Modell.
- Zeitstempel „jetzt (UTC)“ = Zeitpunkt des Anlegens. Keine Tabelle setzt Änderungszeiten automatisch: Die Anwendung muss `updated_at` (und ähnliche Felder) bei jeder Änderung setzen.

**Verschlüsselung und Hash**
- Spalten mit Suffix „_enc“ bzw. ausdrücklich als verschlüsselt markierte Spalten enthalten Text-Chiffrate im Format Version 1 (Präfix „SM1“). Leerer Wert = nichts gespeichert, kein Chiffrat.
- Zusatzdaten (AAD) je Feld im Format `<tabelle>.<feld>:<id>`. Ausnahme: `teacher_change_requests` nutzt `teacher_change_requests:<id>:<feld>`. Die Zusatzdaten binden das Chiffrat an Zeile und Feld. [unklar: ob `<feld>` den Spaltennamen mit Suffix „_enc“ enthält; die Quellen verwenden beides nicht eindeutig.]
- Schlüsselrotation (CLI-Befehl `rotate-keys`) packt die dort registrierten Spalten neu. Registriert sind alle verschlüsselten Spalten der Tabellen 1, 2, 4, 5 und 7 sowie `student_absences.reason` und `student_absences.note`. **Nicht registriert** in den Quellen: die drei verschlüsselten Spalten von `watch_log` (siehe Prüfpunkt P1).
- Gehasht: nur `watch_log.session_hash` (Verfahren [unklar]). Keine Passwörter, Schlüssel oder Tokens in diesen Tabellen.
- Klartext, aber personenbezogen: `watch_log.ip`, `watch_log.user_agent`, `watch_log.path`, `watch_log.username`, sowie alle `*_name`-Spalten (Anzeige- und Namensfelder, Klartext).

**Externe Ziele (nicht Teil dieses Auftrags)**
- `users` (ID), `stored_files` (ID), `student_absences` (ID; Felder `reason`, `note` verschlüsselt; `register_id`-Verweis aus dem Klassenbuch), `role_overrides` (Feld `role`), Löschkonzept-Standardwerte (Schlüssel aus `retention_settings`), Einstellung `teacher_self_service`.

**Übersicht**

| Nr | Tabelle | Zweck | Spalten |
|---|---|---|---|
| 1 | register_lessons | Klassenbuch: eine Zeile je Unterrichtsstunde | 15 |
| 2 | student_support | Förderinformationen je Schüler/in | 16 |
| 3 | support_catalog | Katalog der Merkmale und Nachteilsausgleiche | 8 |
| 4 | student_documents | Vom Schüler eingereichte Dokumente und Atteste | 16 |
| 5 | teacher_change_requests | Änderungsanträge der Lehrkräfte | 15 |
| 6 | retention_settings | Einstellungen des Löschkonzepts | 4 |
| 7 | retention_leavers | Warteliste ausgetretener Personen | 9 |
| 8 | retention_log | Löschprotokoll ohne Inhalte | 9 |
| 9 | security_settings | Sicherheitseinstellungen der Schule | 4 |
| 10 | custom_roles | Eigene Rollen der Schule | 9 |
| 11 | role_settings | Ausblenden eingebauter Rollen | 2 |
| 12 | account_watch | Beobachtete Konten | 7 |
| 13 | watch_log | Protokoll der Anfragen und Anmeldungen beobachteter Konten | 19 |

---

## 1. register_lessons (Klassenbuch)

**Zweck:** Eine Zeile je gehaltener Unterrichtsstunde mit Thema, Hausaufgabe und Anwesenheit.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| date | Text, max. 10 Zeichen | Pflicht | kein | – | – | Unterrichtstag [Format unklar, vermutlich JJJJ-MM-TT] |
| lesson_id | Text, max. 40 Zeichen | Pflicht | kein | – | – | Kennung der Unterrichtseinheit |
| period | Ganzzahl | Pflicht | kein | – | – | Stundennummer |
| part | Ganzzahl | Pflicht | 0 | – | – | Kursteil; 0 = Standard [weitere Werte unklar] |
| course_id | Text, max. 64 Zeichen | Pflicht | kein | kein FK | – | Kurs-Kennung |
| class_ids | JSON, Liste von Texten | optional | NULL | kein FK | – | Klassen-Kennungen der Stunde |
| subject | Text, max. 40 Zeichen | Pflicht | "" (leer) | – | – | Fach [Format unklar] |
| teacher_id | Text, max. 40 Zeichen | optional | NULL | kein FK | – | Kennung der unterrichtenden Lehrkraft |
| topic_enc | Text | Pflicht | "" | – | verschlüsselt | Thema der Stunde |
| homework_enc | Text | Pflicht | "" | – | verschlüsselt | Hausaufgabe |
| attendance_enc | Text | Pflicht | "" | – | verschlüsselt | Anwesenheit als JSON: {Schüler-Kennung: {status, minutes}} |
| checked_by | Ganzzahl | optional | NULL | kein FK | – | Benutzer-ID der prüfenden Person |
| checked_by_name | Text, max. 200 Zeichen | Pflicht | "" | – | – | Name der prüfenden Person |
| checked_at | Zeit | Pflicht | jetzt (UTC) | – | – | Zeitpunkt der Kontrolle |

- **Eindeutigkeit:** Kombination (date, lesson_id, period, part). Je Tag, Unterrichtseinheit, Stunde und Kursteil gibt es genau eine Zeile.
- **Indizes (fachlich wichtig):** date (Tagesansicht), course_id (Kursansicht).
- **Hinweise:**
  - Eine Zeile je gehaltener Stunde.
  - Fehlen, Verspätung und frühes Gehen werden als Abwesenheit (Tabelle `student_absences`, Verweis `register_id`) geführt und müssen dort entschuldigt werden.
  - Statuswerte in `attendance_enc` [unklar]. Einheit von `minutes`: Minuten; Bedeutung [unklar] (vermutlich Verspätung).
  - Schlüsselrotation registriert für `topic_enc`, `homework_enc`, `attendance_enc`.
  - `checked_by`, `teacher_id`, `course_id`, `class_ids` sind logische Verweise ohne FK.

---

## 2. student_support (Förderinformationen je Schüler/in)

**Zweck:** Nachteilsausgleich, Schulbegleitung, Förderplan und Sonstiges je Schüler/in, mit Dokumenten.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| student_id | Text, max. 40 Zeichen | Pflicht | kein | kein FK | – | Schüler-Kennung (Index) |
| kind | Text, max. 30 Zeichen | Pflicht | "nachteilsausgleich" | – | – | Werte: nachteilsausgleich (Nachteilsausgleich), schulbegleitung (Schulbegleitung), foerderplan (Förderplan), sonstiges (Sonstiges) |
| title_enc | Text | Pflicht | "" | – | verschlüsselt | Titel des Eintrags |
| details_enc | Text | Pflicht | "" | – | verschlüsselt | Details |
| valid_from | Text, max. 10 Zeichen | optional | NULL | – | – | Gültig ab [Format unklar] |
| valid_to | Text, max. 10 Zeichen | optional | NULL | – | – | Gültig bis [Format unklar]; NULL = [unklar, ob unbefristet] |
| file_ids | JSON, Liste von Texten | optional | NULL | kein FK (IDs der Dateiablage) | – | angehängte Dokumente, gespeichert in der verschlüsselten Dateiablage mit Verweistyp „student_support“ |
| catalog_id | Ganzzahl | optional | NULL | kein FK (logisch: `support_catalog.id`) | – | Katalogeintrag (Merkmal), Index |
| minutes | Ganzzahl | optional | NULL | – | – | Zeitzuschlag in Minuten (Einheit: Minuten) |
| subjects | JSON, Liste von Texten | optional | NULL | – | – | Fächer, für die der Eintrag gilt; leer = alle Fächer |
| aids_enc | Text | Pflicht | "" | – | verschlüsselt | Hilfsmittel |
| created_by | Ganzzahl | optional | NULL | kein FK | – | Benutzer-ID der anlegenden Person |
| created_by_name | Text, max. 200 Zeichen | Pflicht | "" | – | – | Name der anlegenden Person |
| created_at | Zeit | Pflicht | jetzt (UTC) | – | – | Anlagezeitpunkt |
| updated_at | Zeit | optional | NULL | – | – | letzte Änderung (Anwendung setzt) |

- **Eindeutigkeit:** keine.
- **Indizes (fachlich wichtig):** student_id (Förderinfos je Schüler/in), catalog_id.
- **Hinweise:**
  - Sichtbarkeit für Lehrkräfte richtet sich nach dem Katalogeintrag (`teacher_visible`, siehe Tabelle 3): Bei Sichtbarkeit „ja“ sehen Lehrkräfte Art, Minuten, Fächer und Hilfsmittel bei Klausuren. Bei „nein“ (Diagnose- oder Förderbedarfsmerkmal) sehen nur Klassenleitung, Verwaltung und Familie den Eintrag.
  - [unklar] ob `minutes` beim Anlegen aus dem Standard-Zeitzuschlag des Katalogs übernommen wird.
  - Schlüsselrotation registriert für `title_enc`, `details_enc`, `aids_enc`. Zusatzdaten `student_support.<feld>:<id>`.
  - Dokumente selbst liegen nicht in dieser Tabelle, nur ihre IDs in `file_ids`. Für `file_ids` gibt es keinen FK (anders als bei `student_documents.file_id`, siehe P4).

---

## 3. support_catalog (Katalog der Merkmale und Nachteilsausgleiche)

**Zweck:** Von der Schule gepflegter Katalog der Merkmale und Nachteilsausgleiche, aus dem Förderinfos zugeordnet werden.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| label | Text, max. 120 Zeichen | Pflicht | kein | – | – | Bezeichnung |
| kind | Text, max. 30 Zeichen | Pflicht | "nachteilsausgleich" | – | – | wie `student_support.kind` (vier Werte) |
| uses_minutes | Boolesch | Pflicht | nein (False) | – | – | Eintrag arbeitet mit Zeitzuschlag |
| default_minutes | Ganzzahl | optional | NULL | – | – | Standard-Zeitzuschlag in Minuten |
| teacher_visible | Boolesch | Pflicht | ja (True) | – | – | Sichtbarkeit für Lehrkräfte (Regel unten) |
| active | Boolesch | Pflicht | ja (True) | – | – | Eintrag aktiv [Wirkung im Auswahl-Ablauf unklar] |
| sort | Ganzzahl | Pflicht | 0 | – | – | Sortierwert der Anzeige |

- **Eindeutigkeit:** keine (Bezeichnung nicht erzwungen eindeutig).
- **Indizes:** keine.
- **Regel Sichtbarkeit:**
  - `teacher_visible` = ja: Lehrkräfte sehen Art, Minuten, Fächer und Hilfsmittel bei Klausuren (Ausgleichsart).
  - `teacher_visible` = nein: Diagnose- oder Förderbedarfsmerkmal, nur für Klassenleitung, Verwaltung und Familie.
- **Standardbestand** (11 Einträge, Werte gesetzt; `sort` nicht gesetzt, daher 0; Zeitpunkt des Einspielens [unklar]):

| Bezeichnung | Art | Mit Minuten | Standardminuten | Für Lehrkräfte sichtbar |
|---|---|---|---|---|
| Zeitzuschlag | nachteilsausgleich | ja | 15 min | ja |
| Wörterbuch/Duden erlaubt | nachteilsausgleich | nein | – | ja |
| Eigener Raum | nachteilsausgleich | nein | – | ja |
| Pausen/Bewegungspausen | nachteilsausgleich | nein | – | ja |
| Vergrößerte Schrift/Lesehilfe | nachteilsausgleich | nein | – | ja |
| Laptop/Tablet erlaubt | nachteilsausgleich | nein | – | ja |
| ADHS | sonstiges | nein | – | nein |
| Körperliche Behinderung (k) | sonstiges | nein | – | nein |
| Geistige Behinderung (g) | sonstiges | nein | – | nein |
| Förderbedarf Lernen | foerderplan | nein | – | nein |
| Schulbegleitung | schulbegleitung | nein | – | nein |

Alle Standardeinträge: aktiv (ja).

---

## 4. student_documents (eingereichte Dokumente und Atteste)

**Zweck:** Vom Schüler bzw. von der Schülerin eingereichte Dokumente und Atteste; die Datei liegt verschlüsselt in der Dateiablage, bei reinen Papier-Attesten nur als Vermerk.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| student_id | Text, max. 40 Zeichen | Pflicht | kein | kein FK | – | Schüler-Kennung (Index) |
| absence_id | Ganzzahl | optional | NULL | `student_absences.id`, SET NULL | – | Verknüpfung mit einer Abwesenheit (Index) |
| category | Text, max. 20 Zeichen | Pflicht | kein | – | – | attest, entschuldigung, beurlaubung, einverstaendnis, sonstiges |
| title_enc | Text | Pflicht | "" | – | verschlüsselt | Titel des Dokuments |
| file_id | Text (ID) | optional | NULL | `stored_files.id`, SET NULL | – | Datei in der verschlüsselten Ablage; NULL = nur Papier-Attest vermerkt |
| uploaded_by | Ganzzahl | optional | NULL | `users.id`, SET NULL | – | Einreicher/in (Index) |
| uploaded_by_name | Text, max. 200 Zeichen | Pflicht | "" | – | – | Name des Einreichers |
| status | Text, max. 20 Zeichen | Pflicht | "eingegangen" | – | – | eingegangen, geprueft, abgelehnt (Index) |
| handled_by | Ganzzahl | optional | NULL | `users.id`, SET NULL | – | bearbeitende Person |
| handled_by_name | Text, max. 200 Zeichen | Pflicht | "" | – | – | Name der bearbeitenden Person |
| handled_at | Zeit | optional | NULL | – | – | Zeitpunkt der Bearbeitung |
| note_enc | Text | Pflicht | "" | – | verschlüsselt | Vermerk; leer oder Chiffrat |
| created_at | Zeit | Pflicht | jetzt (UTC) | – | – | Eingangszeitpunkt (Index) |
| withdrawn_at | Zeit | optional | NULL | – | – | zurückgezogen/archiviert seit diesem Zeitpunkt; gesetzt = nicht mehr in Listen |
| withdrawn_by_name | Text, max. 200 Zeichen | Pflicht | "" | – | – | Name der Person, die zurückgezogen hat |

- **Eindeutigkeit:** keine.
- **Indizes (fachlich wichtig):** Kombination (student_id, created_at) für die Liste je Schüler/in; status (Prüfliste); einzeln absence_id, uploaded_by, created_at.
- **Hinweise:**
  - Status: eingegangen (Standard) → geprueft oder abgelehnt. Erlaubte Übergänge [unklar].
  - Datei in der verschlüsselten Ablage mit Zweck „student_document“ und Verweistyp „student_document“.
  - Zurückgezogen/archiviert: Eintrag und Datei bleiben erhalten, erscheinen aber in keiner Liste. Endgültig gelöscht erst durch den Löschlauf nach der Aufbewahrungsfrist des Löschkonzepts [Frist hier nicht angegeben].
  - Schlüsselrotation registriert für `title_enc` und `note_enc` sowie für `student_absences.reason` und `student_absences.note`. Zusatzdaten `student_documents.<feld>:<id>`.
  - Löschverhalten: Datei gelöscht → `file_id` leer. Abwesenheit gelöscht → `absence_id` leer. Benutzerkonto gelöscht → `uploaded_by`/`handled_by` leer; die Namensfelder bleiben.

---

## 5. teacher_change_requests (Änderungsanträge der Lehrkräfte)

**Zweck:** Anträge der Lehrkräfte auf Änderung ihres Profils (Fächer, Klassenwünsche, Stunden, Zeitfenster) oder auf eine einmalige Ausnahme (Abwesenheit).

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| teacher_id | Text, max. 40 Zeichen | Pflicht | kein | kein FK | – | Lehrkraft-Kennung (Index) |
| user_id | Ganzzahl | optional | NULL | `users.id`, SET NULL | – | Benutzerkonto der Lehrkraft (Index) |
| kind | Text, max. 20 Zeichen | Pflicht | "profil" | – | – | profil (Profiländerung), ausnahme (einmalige Ausnahme) (Index) |
| payload | JSON | Pflicht | kein | – | – | bei profil: {subjects, preferred_classes, max_hours, time_windows, wishes}; bei ausnahme: {"exception": {"date", "date_to", "periods", "reason"}} |
| previous | JSON | optional | NULL | – | – | Profil zum Zeitpunkt der Antragstellung (Vergleich alt/neu) |
| note_enc | Text | Pflicht | "" | – | verschlüsselt | Begründung der Lehrkraft; leer oder Chiffrat |
| status | Text, max. 20 Zeichen | Pflicht | "offen" | – | – | offen, genehmigt, abgelehnt, zurueckgezogen (Index) |
| auto | Boolesch | Pflicht | nein (False) | – | – | ja = direkt übernommen ohne Prüfung |
| reviewer_id | Ganzzahl | optional | NULL | `users.id`, SET NULL | – | prüfende Person |
| review_comment_enc | Text | Pflicht | "" | – | verschlüsselt | Kommentar der prüfenden Person; leer oder Chiffrat |
| applied_version | Ganzzahl | optional | NULL | – | – | [unklar; Name legt eine Profil-Versionsnummer nahe, nicht dokumentiert] |
| created_at | Zeit | Pflicht | jetzt (UTC) | – | – | Antragszeitpunkt (Index) |
| updated_at | Zeit | optional | NULL | – | – | letzte Änderung (Anwendung setzt) |
| decided_at | Zeit | optional | NULL | – | – | Entscheidungszeitpunkt |

- **Eindeutigkeit:** keine.
- **Indizes (fachlich wichtig):** Kombination (teacher_id, status) für die Anträge je Lehrkraft; einzeln teacher_id, user_id, kind, status, created_at.
- **Hinweise:**
  - Ablauf: offen → genehmigt, abgelehnt oder zurueckgezogen. Formale Übergangsregeln [unklar].
  - Bei Einstellung `teacher_self_service` = „direct“ wird die Änderung sofort übernommen: status = genehmigt, auto = ja. Andere Werte dieser Einstellung [unklar].
  - Bei kind = ausnahme legt die Genehmigung eine Abwesenheit an (Zieltabelle nicht in diesem Auftrag). Felder: date, date_to (Datum), periods (Stunden), reason (Begründung).
  - Schlüsselrotation registriert für `note_enc` und `review_comment_enc`. Zusatzdaten `teacher_change_requests:<id>:<feld>` (abweichendes Format, siehe Konventionen).
  - Prüfpunkt P2 zu Freitexten in `payload` (siehe unten).

---

## 6. retention_settings (Einstellungen des Löschkonzepts)

**Zweck:** Schlüssel-Wert-Einstellungen des Löschkonzepts (Fristen in Tagen, Schalter).

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| key | Text, max. 80 Zeichen, Primärschlüssel | Pflicht | kein | – | – | Schlüsselname |
| value | Text, max. 200 Zeichen | Pflicht | "" | – | – | Wert als Text; Fristen in Tagen, Schalter [Wertformat je Schlüssel unklar] |
| updated_at | Zeit | Pflicht | jetzt (UTC) | – | – | Änderungszeitpunkt (Anwendung setzt) |
| updated_by | Text, max. 80 Zeichen | Pflicht | "" | kein FK | – | Kennung der ändernden Person |

- **Eindeutigkeit:** key (Primärschlüssel).
- **Indizes:** keine.
- **Hinweise:**
  - Fehlt ein Schlüssel, gilt der Standardwert des Löschkonzepts. Schlüsselliste und Standardwerte sind in diesem Auftrag nicht enthalten: [unklar].

---

## 7. retention_leavers (Warteliste ausgetretener Personen)

**Zweck:** Personen, die nicht mehr im Planungsdokument stehen, bis ihre Daten bereinigt und der Eintrag abgeschlossen ist.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| student_id | Text, max. 40 Zeichen | Pflicht | kein | kein FK | – | Schüler-Kennung; eindeutig; Index |
| status | Text, max. 12 Zeichen | Pflicht | "wartend" | – | – | wartend, erledigt (Index) |
| source | Text, max. 12 Zeichen | Pflicht | "planung" | – | – | planung (aus dem Planungsdokument), abgleich |
| left_at | Zeit | Pflicht | jetzt (UTC) | – | – | Eintragszeitpunkt; Standard = Anlagezeit [unklar, ob Austrittsdatum gemeint] |
| name_enc | Text | Pflicht | "" | – | verschlüsselt | Anzeigename; wird beim Abschluss geleert |
| class_id | Text, max. 40 Zeichen | Pflicht | "" | kein FK | – | Klassen-Kennung |
| purged | JSON, Liste von Texten | optional | NULL | – | – | bereits bereinigte Datenarten |
| done_at | Zeit | optional | NULL | – | – | Abschlusszeitpunkt (bei erledigt) |

- **Eindeutigkeit:** student_id (je Schüler/in genau ein Eintrag).
- **Indizes (fachlich wichtig):** status (Warteliste), student_id.
- **Hinweise:**
  - Quelle: planung (Standard) oder abgleich.
  - Mit Abschluss: status = erledigt, done_at gesetzt, name_enc geleert.
  - Schlüsselrotation registriert für `name_enc`. Zusatzdaten `retention_leavers.name:<id>`.

---

## 8. retention_log (Löschprotokoll)

**Zweck:** Protokoll, welche Datenart wann für wen wie viele Datensätze gelöscht oder anonymisiert wurde, ohne Inhalte.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| at | Zeit | Pflicht | jetzt (UTC) | – | – | Zeitpunkt (Index) |
| kind | Text, max. 40 Zeichen | Pflicht | kein | – | – | Datenart, z. B. „watch_log“ [vollständige Liste unklar] (Index) |
| action | Text, max. 20 Zeichen | Pflicht | "geloescht" | – | – | geloescht, anonymisiert |
| mode | Text, max. 12 Zeichen | Pflicht | "automatik" | – | – | automatik (Standard), frist, sofort [Bedeutung im Einzelnen unklar] |
| subject | Text, max. 60 Zeichen | Pflicht | "" | – | – | student:<Kennung>, user:<Kennung> oder leer; nur IDs |
| count | Ganzzahl | Pflicht | 0 | – | – | Anzahl betroffener Datensätze |
| actor | Text, max. 80 Zeichen | Pflicht | "system" | – | – | ausführende Stelle; „system“ = Automatik |
| note | Text, max. 200 Zeichen | Pflicht | "" | – | – | kurzer Anlass; nie Inhalte |

- **Eindeutigkeit:** keine.
- **Indizes (fachlich wichtig):** at, kind.
- **Hinweise:**
  - Keine Inhalte, keine Namen; nur IDs im Feld subject.
  - Kein FK.

---

## 9. security_settings (Sicherheitseinstellungen)

**Zweck:** Sicherheitseinstellungen der Schule als Schlüssel-Wert-Tabelle; Werte als JSON.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| key | Text, max. 40 Zeichen, Primärschlüssel | Pflicht | kein | – | – | Einstellungsschlüssel [gültige Schlüssel unklar] |
| value | JSON | optional | NULL | – | – | Wert der Einstellung |
| updated_at | Zeit | Pflicht | jetzt (UTC) | – | – | Änderungszeitpunkt (Anwendung setzt) |
| updated_by | Ganzzahl | optional | NULL | `users.id`, SET NULL | – | ändernde Person (Benutzer-ID) |

- **Eindeutigkeit:** key (Primärschlüssel).
- **Indizes:** keine.
- **Hinweise:**
  - Gültige Schlüssel und Standardwerte sind in diesem Auftrag nicht enthalten: [unklar].
  - Die Einstellung `teacher_self_service` (Wert „direct“, siehe Tabelle 5) wird in den Quellen genannt; ob sie in dieser Tabelle liegt, ist [unklar].

---

## 10. custom_roles (Eigene Rollen der Schule)

**Zweck:** Eigene Rolle mit Name, Kurzbeschreibung, Grundtyp, Grundrolle und Vorlage. Ihre Rechte-Abweichungen liegen in einer eigenen Tabelle.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Text, max. 20 Zeichen, Primärschlüssel | Pflicht | kein | – | – | Rollenkennung mit Präfix „x-“ |
| name | Text, max. 80 Zeichen | Pflicht | kein | – | – | Name der Rolle; eindeutig |
| description | Text, max. 300 Zeichen | Pflicht | "" | – | – | Kurzbeschreibung |
| kind | Text, max. 20 Zeichen | Pflicht | kein | – | – | Grundtyp [Werte unklar] |
| base | Text, max. 20 Zeichen | Pflicht | kein | kein FK | – | Grundrolle; steht bei Konten im Feld „Rolle“ des Benutzers [Werte unklar] |
| template | Text, max. 20 Zeichen | Pflicht | kein | kein FK | – | Vorlage: eingebaute Rolle, deren Standardrechte gelten [Werte unklar] |
| created_at | Zeit | Pflicht | jetzt (UTC) | – | – | Anlagezeitpunkt |
| created_by | Text, max. 80 Zeichen | Pflicht | "" | kein FK | – | Kennung der anlegenden Person |
| updated_at | Zeit | Pflicht | jetzt (UTC) | – | – | nur bei Anlage gesetzt; Anwendung setzt bei Änderung neu |

- **Eindeutigkeit:** id (Primärschlüssel); name (eindeutig).
- **Indizes:** keine.
- **Hinweise:**
  - Rechte-Abweichungen von der Vorlage liegen in der Tabelle `role_overrides` (Feld `role` = Rollenkennung mit Präfix „x-“), nicht in diesem Auftrag.
  - Keine FK in diesem Modell.

---

## 11. role_settings (Ausblenden eingebauter Rollen)

**Zweck:** Legt fest, welche eingebauten Rollen ausgeblendet sind.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| role | Text, max. 20 Zeichen, Primärschlüssel | Pflicht | kein | – | – | Kennung einer eingebauten Rolle |
| hidden | Boolesch | Pflicht | nein (False) | – | – | ja = Rolle ist ausgeblendet |

- **Eindeutigkeit:** role (Primärschlüssel).
- **Indizes:** keine.
- **Regeln:**
  - Ausblenden nur, wenn kein Konto diese Rolle hat.
  - Die Rolle admin kann nie ausgeblendet werden.
- Keine Zeitstempel.

---

## 12. account_watch (Beobachtete Konten)

**Zweck:** Markiert einzelne Konten für verstärkte Protokollierung und legt fest, ob sie Admin-Rechte vergeben dürfen.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| user_id | Ganzzahl, Primärschlüssel | Pflicht | kein | `users.id`, CASCADE | – | beobachtetes Konto; eine Zeile je Konto |
| watched | Boolesch | Pflicht | nein (False) | – | – | ja = Konto wird verstärkt protokolliert |
| until | Zeit | optional | NULL | – | – | Ende der Beobachtung; NULL = [unklar] |
| since | Zeit | optional | NULL | – | – | Beginn der Beobachtung [Bedeutung aus dem Namen abgeleitet] |
| set_by | Text, max. 80 Zeichen | Pflicht | "" | kein FK | – | Kennung der setzenden Person |
| no_admin_grant | Boolesch | Pflicht | nein (False) | – | – | ja = Konto darf keine Admin-Konten anlegen und keine Admin-Rechte vergeben |
| updated_at | Zeit | Pflicht | jetzt (UTC) | – | – | letzte Änderung (Anwendung setzt) |

- **Eindeutigkeit:** user_id (Primärschlüssel).
- **Indizes:** keine.
- **Hinweise:**
  - Die Beobachtung wirkt auf `watch_log`: jede Anfrage des Kontos (auch Lesen) und die Anmeldeereignisse werden protokolliert.
  - Wird das Konto gelöscht, wird die Beobachtung mit gelöscht.

---

## 13. watch_log (Protokoll beobachteter Konten)

**Zweck:** Protokoll jeder Anfrage beobachteter Konten (auch lesend) und der Anmeldeereignisse.

| Spalte | Typ | Pflicht | Standard | FK (Löschverhalten) | Schutz | Bedeutung / Werte |
|---|---|---|---|---|---|---|
| id | Ganzzahl, Primärschlüssel | Pflicht | automatisch | – | – | eindeutige ID |
| at | Zeit | Pflicht | jetzt (UTC) | – | – | Zeitpunkt (Index) |
| user_id | Ganzzahl | optional | NULL | `users.id`, SET NULL | – | Konto (Index) |
| username | Text, max. 80 Zeichen | Pflicht | "" | – | – | Benutzername zum Zeitpunkt; bleibt nach Kontolöschung erhalten |
| kind | Text, max. 12 Zeichen | Pflicht | "request" | – | – | request (Anfrage), auth (Anmeldeereignis) |
| action | Text, max. 80 Zeichen | optional | NULL | – | – | Ereignis bei auth, z. B. „auth.login“, „auth.login_failed“ [weitere Werte unklar] |
| method | Text, max. 8 Zeichen | Pflicht | "GET" | – | – | HTTP-Methode |
| path | Text, max. 300 Zeichen | Pflicht | "" | – | – | Pfad der Anfrage, Klartext |
| route | Text, max. 200 Zeichen | Pflicht | "" | – | – | Routenmuster mit Platzhaltern, z. B. /api/v1/users/{user_id} |
| status | Ganzzahl | optional | NULL | – | – | HTTP-Statuscode |
| duration_ms | Ganzzahl | optional | NULL | – | – | Dauer der Anfrage in Millisekunden |
| write | Boolesch | Pflicht | nein (False) | – | – | ja = schreibende Anfrage |
| ip | Text, max. 64 Zeichen | optional | NULL | – | – | IP-Adresse, Klartext (personenbezogen) |
| user_agent | Text, max. 300 Zeichen | optional | NULL | – | – | Client-Kennung, Klartext |
| session_hash | Text, max. 32 Zeichen | optional | NULL | – | gehasht (vermutlich) | Sitzungskennung; Verfahren [unklar] |
| request_id | Text, max. 64 Zeichen | optional | NULL | – | – | Kennung der Anfrage (Zuordnung) |
| query_enc | Text | optional | NULL | – | verschlüsselt, geschwärzt | Query-Parameter, geschwärzt |
| body_enc | Text | optional | NULL | – | verschlüsselt, geschwärzt | Request-Body, geschwärzt |
| changes_enc | Text | optional | NULL | – | verschlüsselt, geschwärzt | Audit-Ereignisse der Anfrage inklusive Vorher-/Nachher-Werte |

- **Eindeutigkeit:** id (Primärschlüssel).
- **Indizes (fachlich wichtig):** at (Zeitabfrage), user_id (Abfrage je Konto).
- **Hinweise:**
  - Aufbewahrung: 180 Tage (Standard) als Datenart „watch_log“ im Löschkonzept.
  - Bewusste, dokumentierte Ausnahme vom Grundsatz „Audit-Protokoll ohne Inhalte“: Inhalte werden nur geschwärzt und verschlüsselt gespeichert.
  - Zusatzdaten `watch_log.<feld>:<id>`.
  - Schlüsselrotation: **in diesen Quellen nicht registriert** (Prüfpunkt P1).
  - Kontolöschung: user_id wird leer, username bleibt.

---

## Prüfpunkte (Widersprüche und Lücken im Quellmaterial)

- **P1** – `watch_log`: die drei verschlüsselten Spalten (`query_enc`, `body_enc`, `changes_enc`) sind in den Quellen nicht für die Schlüsselrotation registriert, obwohl andere Tabellen es sind. Prüfen, ob sie an anderer Stelle registriert werden.
- **P2** – `teacher_change_requests`: die Quelle verlangt, dass Freitexte nur verschlüsselt gespeichert werden. Im JSON-Feld `payload` (unverschlüsselt) stehen aber `wishes` (bei profil) und `reason` (bei ausnahme). Klären, ob diese Felder Freitext sind und ob sie verschlüsselt werden müssen.
- **P3** – Zusatzdaten-Format: `teacher_change_requests` nutzt `<tabelle>:<id>:<feld>`, alle anderen Tabellen `<tabelle>.<feld>:<id>`. Für den Neubau einheitlich festlegen. Zusätzlich offen, ob `<feld>` den Suffix „_enc“ enthält.
- **P4** – Fremdschlüssel-Einheitlichkeit: `student_documents.file_id` hat einen FK auf die Dateiablage, `student_support.file_ids` (Liste) hat keinen. `register_lessons.checked_by`, `student_support.created_by`, `teacher_change_requests.teacher_id` u. a. sind ohne FK.
- **P5** – Zeitstempel: keine Tabelle setzt `updated_at` automatisch; die Anwendung muss das durchgängig regeln.
- **P6** – `watch_log`: personenbezogene Klartextfelder (`ip`, `user_agent`, `path`, `username`) neben den verschlüsselten Feldern; Schutzbedarf für den Neubau festlegen.

## Offene Werte [unklar] (nicht in den Quellen dieses Auftrags)

1. Schlüsselliste und Standardfristen von `retention_settings` (Fristen in Tagen).
2. Gültige Schlüssel und Standardwerte von `security_settings`.
3. Werte von `custom_roles.kind`, `custom_roles.base`, `custom_roles.template` (eingebaute Rollen, Grundtypen).
4. Statuswerte der Anwesenheit in `register_lessons.attendance_enc`; Bedeutung von `minutes`.
5. Format von Text-Datumsfeldern (`register_lessons.date`, `student_support.valid_from`, `student_support.valid_to`).
6. Bedeutung von `register_lessons.part` über 0 hinaus; Bedeutung von `register_lessons.checked_by`.
7. Bedeutung von `teacher_change_requests.applied_version`.
8. Erlaubte Statusübergänge bei `student_documents` und `teacher_change_requests`.
9. Weitere Werte der Einstellung `teacher_self_service` außer „direct“.
10. Übernahme des Standard-Zeitzuschlags in `student_support.minutes` beim Anlegen.
11. Bedeutung von `support_catalog.active` im Auswahl-Ablauf; Einspielzeitpunkt des Standardbestands.
12. Bedeutung von `retention_leavers.left_at` (Standard = Anlagezeit).
13. Vollständige Liste der Datenarten für `retention_log.kind` und `retention_leavers.purged`; Bedeutung der Werte von `retention_log.mode`.
14. Bedeutung von `account_watch.until` bei NULL und von `since`.
15. Verfahren hinter `watch_log.session_hash`.
16. Vollständige Liste der Werte von `watch_log.action`.
17. Frist für endgültiges Löschen zurückgezogener Dokumente (`student_documents.withdrawn_at`).
