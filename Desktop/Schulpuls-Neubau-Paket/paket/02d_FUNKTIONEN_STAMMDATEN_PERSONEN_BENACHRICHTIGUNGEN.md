# 02d – Funktionen: Stammdaten, Lehrkräfte, Schüler/innen und Eltern, Benachrichtigungen

Kürzel dieser Datei: **STA** (Stammdaten, Klassen, Jahrgänge, Stundentafeln, Schuljahr, Ferien, Einrichtung, Jahreswechsel), **LEH** (Lehrkräfte), **SCH** (Schüler/innen und Eltern), **BEN** (Benachrichtigungen).

## 0. Lesehinweise und Querschnittsregeln

### 0.1 Schreibweise
- Jede Anforderung hat eine feste Kennung `<KÜRZEL>-<nnn>` (je Kürzel ab 001), eine Priorität, einen Status und genau eine Zeile `Abnahme:`.
- Priorität: **P0** Pflicht/Sicherheit/Recht, **P1** Kernfunktion, **P2** wichtig, **P3** Wunsch.
- Status: **Ist** = im Bestand gebaut (muss der Neubau mindestens leisten); **offen** = gewünscht bzw. geplant, noch nicht gebaut.
- `[unklar: …]` = Wert oder Wirkung ist im Bestand nicht belegt; der Neubau legt ihn fest und hält ihn in Server und Oberfläche identisch.
- Nutzer-Wortlaut steht in Anführungszeichen; Datum `10-12` = 12. Oktober 2026.
- Zählweisen: Wochentage 0 = Montag … 6 = Sonntag. Stunden intern 0-basiert (erste Stunde = 0), in Oberfläche und Texten 1-basiert. Wochen 1 bis 52 (Schuljahreswochen), Ferien zählen mit, jede Woche hat 7 Tage (Montag bis Sonntag). Datum ISO `JJJJ-MM-TT`, Anzeige deutsch `TT.MM.JJJJ`. Zeitzone Europe/Berlin, Speicherung UTC.

### 0.2 Verbindliche Gestaltungs- und Sicherheitsregeln (gelten für jede Anforderung dieser Datei)
- Anrede **Sie** in allen Texten, auch für Schüler/innen („Sie sind jetzt volljährig …“, „Möchten Sie das wirklich löschen?“).
- Keine Erklärabsätze auf Seiten. Erklärungen stehen im Hilfe-Symbol („i“) an der Beschriftung bzw. im Hilfetext; fachlich nötige Warnhinweise sind erlaubt, wenn der Zustand sie auslöst.
- Ein gemeinsames Raster (Tage × Stunden) für alle Ansichten, die Tage und Stunden zeigen (Stundenplan, Verfügbarkeit, Sperrzeiten, Aufsichten, Anwesenheit). Es entsteht nie ein zweiter Rastertyp.
- App-Dialoge statt Browser-Popups (kein `alert`/`confirm`).
- Fremde Daten liefern **404**. **403** nur, wenn die Person den Datensatz sehen, aber nicht ändern darf, oder die Rolle das Recht gar nicht besitzt. Bewusste Ausnahme: Lehrkraft-Konto ohne Zuordnung zu einer Lehrkraft erhält 403 mit hilfreicher Meldung (LEH-027).
- Jede schreibende Aktion wird protokolliert (Audit), **ohne Inhalte** (nur Aktion, Ziel-Kennung, Konto, Zeit).
- Freitexte mit Personenbezug werden verschlüsselt gespeichert (Token-Präfix `SM1`, Kontextbindung `<tabelle>.<feld>:<id>`).
- Fehlertexte der Server in Klartext Deutsch, ohne Feldnamen (nie „Field required“); unerwartete Fehler: „Das hat nicht geklappt“ mit Fehlernummer.
- Sicherheit und Datenschutz gehen vor Komfort.

### 0.3 In dieser Datei benutzte Rechte (Rechte-Katalog: Datei REC)
| Recht | Bedeutung (Kurz) |
|---|---|
| `masterdata.edit` | Lehrkräfte, Räume, Fächer, Klassen, Kurse, Ferien anlegen/ändern |
| `timetable.edit` | Stunden verschieben, Stundentafeln/Jahrgänge schreiben; schließt Lesen aller Pläne ein |
| `timetable.generate` | Generator, Planzeitraum-Pläne kopieren/löschen |
| `settings.edit` | Schuleinstellungen, Schulprofil, Schulvorgaben der Benachrichtigungen, Kalender-Zeiträume |
| `users.manage` | Konten anlegen/ändern/sperren (ohne Administration: nur Schüler/Eltern) |
| `students.read` / `students.birth_date` | Schülerdaten lesen (eigene Klassen) / Geburtsdatum pflegen |
| `support.read` / `support.manage` / `support.catalog` / `support.hints` | Förderdaten lesen / pflegen / Katalog pflegen / Klausur-Hinweis |
| `student_documents.read` | Atteste und Dokumente (Eingang prüfen, einreichen) |
| `student_absence.read` | Fehlzeiten eines Kindes |
| `profile.teacher_self` | eigenes Lehrkraft-Profil (als Antrag) |
| `teacher_requests.review` | Anträge von Lehrkräften prüfen/ablehnen |
| `history.restore` | Verlauf ansehen, Version wiederherstellen, Rückgängig |
| `audit.read` | Audit-Protokoll lesen |
| `system.admin` / `license.manage` | Systemverwaltung (u. a. Demo laden) / Lizenz |
| `substitution.edit` | Vertretung/Ausfall planen |

Grundrollen (zwölf): `admin`, `schulleitung`, `abteilungsleitung`, `planer`, `sekretariat`, `lehrer`, `hausmeister`, `schulbegleitung`, `schueler`, `eltern`, `monitor`, `zuschauer`; dazu eigene Schulrollen mit einem Grundtyp. Die technische Administration (`admin`) sieht nie Gesundheits- und Personaldaten (Atteste, Förderdaten, Lehrkraft-Profile).

---

## 1. Stammdaten, Klassen, Jahrgänge und Stundentafeln, Schuljahr, Ferien, Einrichtung, Jahreswechsel (STA)

### 1.1 Grundprinzipien und Änderungsweg

**STA-001** · P1 · Status: Ist
Keine Festverdrahtung: Klassenstufen, Fächer, Jahrgänge (Bildungsgänge), Raumtypen, Standorte, Zeitraster, Pausen sind Daten, die die Schule anlegt, ändert und löscht. Es gibt keine feste Stufenliste 5–13, keine feste Fächerliste, keine festen Jahrgänge. Nutzer 10-16: „Ich will dass der ganze das alles nicht hart gekodet ist.“ Eine frische Instanz enthält 0 Standorte, 0 Fächer, 0 Räume, 0 Jahrgänge, 0 Klassen.
Abnahme: Auf frischer Instanz sind alle Stammdatenlisten leer; Jahrgang „GIF 26“, Fach „Informatik“ und Klasse mit Klassenstufe 0 sowie mit 20 lassen sich anlegen; Klassenstufe 21 wird mit Klartextfehler abgelehnt; es erscheint nirgends eine Vorbelegung von Fächern oder Stufen außer den abwählbaren Vorschlägen der Einrichtung (STA-070).

**STA-002** · P1 · Status: Ist
Einheitliches Pflegemodell je Sammlung (Liste, Lesen, Anlegen, Ändern, Löschen) für Standorte, Fächer, Lehrkräfte, Räume, Klassen, Schüler/innen, Kurse, Stundentafeln, Jahrgänge (`grade_profiles`), Ferien, Termine, Aufsichtsbereiche. Kennungen haben je Sammlung ein festes Präfix (z. B. `JG` für Jahrgänge). Listen sind rollenabhängig (Schüler/innen und Eltern sehen nur eigene Schüler-IDs; Lehrkräfte nur ihren Ausschnitt; `plans.read_all` erlaubt alle Pläne); Auswahllisten dürfen nie als vollständig angenommen werden. Große Listen sind virtualisiert. Zeitraumabfragen sind auf eine Höchstzahl Tage begrenzt [unklar: Wert].
Abnahme: Als `eltern` angemeldet liefert `GET /data/students` nur die verknüpften Kinder; als Fachlehrkraft nur Schüler/innen der eigenen Kurse; als `planer` alle; eine Abfrage mit Kennung eines fremden Kindes ergibt 404.

**STA-003** · P0 · Status: offen (Ist: Löschen nur „angemeldet“ geprüft)
Schreibrechte: Anlegen und Ändern verlangen `masterdata.edit` oder `timetable.edit` (Klassen-, Fach-, Raum-, Lehrkraft-Dialoge: `masterdata.edit`; Stundentafeln, Jahrgänge und generische Datenschnittstelle: `timetable.edit`). **Löschen verlangt dasselbe Schreibrecht** wie Ändern (im Bestand fehlt die Prüfung). Lesen: angemeldet, rollenabhängig (STA-002). Sekretariat darf Stundentafeln nur lesen (Hinweis mit Grund statt gesperrter Felder).
Abnahme: `DELETE /data/subjects/{id}` mit Konto `sekretariat` ohne `masterdata.edit` → 403 und Datensatz bleibt; mit `planer` → 200; Sekretariat sieht in der Stundentafel gesperrte Felder mit Hinweistext, warum.

**STA-004** · P0 · Status: Ist
Zentraler Änderungsweg für jede Stammdaten- und Planänderung: (1) Recht prüfen, (2) Eingabe prüfen (Fehler 4xx werden vor dem Speichern ausgelöst), (3) neue Version des Planungsstands speichern, (4) Änderung ist rückgängig machbar, (5) Audit-Eintrag `plan.change` (ohne Inhalte), (6) Live-Ereignis `change` an alle Clients mit Bereich und betroffenen Daten; Clients laden nur betroffene Listen neu (ohne Bereich alles). Ergibt die Änderung denselben Stand (Prüfsumme SHA-256 des JSON), entsteht keine Version, kein Audit, kein Ereignis. Bei Fehler wird nichts gespeichert und kein Ereignis gesendet. Jede Änderung arbeitet auf einer vollständigen Kopie; Leser sehen nie einen halben Zustand.
Abnahme: Klasse umbenennen → genau eine neue Version mit Audit `plan.change`; zweiter Browser aktualisiert die Klassenliste ohne Neuladen; erneutes Speichern ohne Änderung → keine neue Version; Speichern mit ungültigem Verweis → 422, Versionsnummer unverändert.

**STA-005** · P1 · Status: Ist
Verlauf und Versionen (Recht `history.restore`): Liste neueste zuerst, 50 Einträge je Seite, Maximum 1000 je Abfrage; Anzeige von Benutzer-Anzeigename (sonst Benutzername, ohne Benutzer „System“); geltende Version mit „aktuell“. Aufbewahrung 300 Versionen (`SM_KEEP_VERSIONS`), ältere werden endgültig gelöscht, Versionsnummern nie wiederverwendet; Änderungsnotiz höchstens 500 Zeichen. **Wiederherstellen** von Version N legt eine neue Version (Bereich `restore`, Ursprung N, Nachricht „Version N wiederhergestellt“) an; fehlt N: „Version N existiert nicht (mehr)“. **Rückgängig** legt eine neue Version (Bereich `undo`, Nachricht „Rückgängig: zurück auf Version N (…)“) an: bei normaler Änderung auf die jüngere Vorversion der aktuellen; bei Rückgängig-Schritt auf die Vorversion des Ursprungs; bei Wiederherstellung/Ersetzen auf den Stand davor; ohne ältere Version Fehler „Es gibt keine ältere Version, die wiederhergestellt werden kann“. Wiederholtes Rückgängig geht Schritt für Schritt zurück; nichts wird gelöscht. Audit-Aktionen `plan.init`, `plan.change`, `plan.replace`, `plan.restore`, `plan.undo`.
Abnahme: Nach 3 Änderungen zweimal Rückgängig → Stand wie nach der 1. Änderung, 5 Versionen im Verlauf, Versionsnummern lückenlos; Konto ohne `history.restore` → 403 auf `/history`; nach der 301. Änderung ist die Version 1 nicht mehr abrufbar (404).

**STA-006** · P1 · Status: offen
Rückgängig und Wiederherstellen zeigen vorher, welche Änderungen **anderer Personen** mit zurückgenommen würden (Wer, Was, Wann) und verlangen dann eine Bestätigung; ohne fremde Änderungen bleibt es ein Klick (Bestand: Rückgängig ist global ohne Benutzerbezug).
Abnahme: Benutzer A ändert Raum, Benutzer B ändert Klasse; A klickt „Rückgängig“ → Dialog nennt B, „Klasse geändert“, Uhrzeit; erst nach Bestätigung wird zurückgenommen.

**STA-007** · P1 · Status: Ist
Gleichzeitigkeit: Leser erhalten eine Momentaufnahme, Schreibaktionen laufen strikt nacheinander (Sperre); vor jeder Änderung wird die neueste Version nachgeladen, beim Lesen höchstens alle 2 s auf neuere Version geprüft; ohne Ereignis sind Änderungen anderer Serverprozesse spätestens nach 15 s sichtbar. Empfohlen ist ein Arbeitsprozess. Im Mehrserver-Betrieb (mehrere Knoten, eine Datenbank) wird vor dem Speichern die Version geprüft; bei Abweichung: „Der Plan wurde inzwischen auf einem anderen Server geändert. Bitte erneut versuchen.“ (keine automatische Zusammenführung).
Abnahme: Zwei Knoten, gleichzeitiges Speichern derselben Basisversion → genau eines gelingt, das andere erhält obige Meldung und keine Daten gehen verloren; Änderung auf Knoten 1 ist auf Knoten 2 binnen 15 s lesbar.

**STA-008** · P1 · Status: offen
Konkurrierende Änderungen werden auch ohne Mehrserver-Betrieb erkannt (Bestand: „Lost Update“ möglich); Stundentafeln melden Konflikte bereits (STA-030).
Abnahme: Zwei Prozesse speichern parallel auf derselben Basisversion → der zweite Speichervorgang wird mit der Meldung aus STA-007 abgewiesen.

**STA-009** · P0 · Status: Ist
Speicherformat und Schutz des Planungsstands: eine Zeile je Version in `school_versions` (`id`, `user_id`, `message` ≤ 500 Zeichen, `scope` Liste, `data`, `restored_from`, `created_at` UTC). `data` = JSON (UTF-8, Schlüssel sortiert) → zlib Stufe 6 → verschlüsselt (Präfix `SM1`, Kontext `school_versions.data:<id>`, Versionsnummer gebunden, Vertauschen = Manipulation = Entschlüsselungsfehler). Altbestand ohne Verschlüsselung wird beim Start umgeschrieben (Fehler blockieren den Start nicht). Schlüsselrotation: CLI `rotate-keys` (z. B. `--only school_versions.data`) verschlüsselt alle Zeilen neu, verlustfrei; Versionen mit entferntem Schlüssel bleiben unverändert (Warnung im Log). Start lädt die jüngste lesbare Version (höchstens die 5 jüngsten werden geprüft); leere Tabelle → „Leeres Planungsdokument angelegt“ (Bereich `init`). `plan_snapshots` (nur Stunden, keine Personendaten) bleiben unverschlüsselt. Messung: Demo-Schule 99 Klassen ≈ 68 KB, Verschlüsselung < 1 ms.
Abnahme: Direktes Lesen der Tabelle `school_versions` zeigt nur Chiffrat mit Präfix `SM1`; Kopieren von `data` in eine andere Zeile führt beim Laden zu Entschlüsselungsfehler; `rotate-keys --only school_versions.data` ändert keinen Inhalt der geladenen Daten.

**STA-010** · P0 · Status: offen
Export des Planungsstands und Stammdaten-Exporte (CSV/JSON/Untis) enthalten Personendaten (Namen, Geburtsdatum, Kontakte) und sind nur mit passendem Recht (`students.read`, Geburtsdatum nur mit `students.birth_date`) und mit Protokolleintrag erlaubt; ein Vollexport als Klartext-Sicherung ist nur für `system.admin`/Berechtigte und wird als solcher gekennzeichnet (Bestand: JSON-Export „nur angemeldet“, Klartext).
Abnahme: `GET /export/json` als `eltern` oder `lehrer` ohne Recht → 403; als Sekretariat mit Recht → 200 und Audit-Eintrag ohne Inhalte; CSV-Export Schüler enthält `birth_date` nur bei `students.birth_date`.

### 1.2 Datenmodell der Stammdaten

**STA-011** · P1 · Status: Ist
Schuleinstellungen (genau ein Satz je Schule), Auszug für Schulstruktur und Zeit. Weitere Einstellungen (Attestschwelle, Abwesenheitsgrenzen, Postfach, Vertretung, Generator-Gewichte) stehen in den Dateien der Bereiche.

| Feld | Typ | Standard | Einheit / Wirkung |
|---|---|---|---|
| `school_name` | Text | „Meine Schule“ | Platzhalter; solange dieser Wert steht, gilt die Einrichtung als „nicht eingerichtet“ |
| `periods` | Ganzzahl | 10 | Stunden je Tag (Einrichtung erlaubt bis 16) |
| `period_times` | Liste HH:MM | 07:55, 08:45, 09:50, 10:40, 11:45, 12:35, 13:30, 14:20, 15:10, 16:00 | Beginn je Stunde (Index = Stunde, aufsteigend); Länge = `periods` |
| `period_minutes` | Ganzzahl | 45 | Minuten je Unterrichtsstunde |
| `breaks` | Liste {after, name, minutes} | {1, „Pause 1“, 20}, {3, „Pause 2“, 20}, {5, „Pause 3“, 45} | `after` = Pause liegt hinter dieser Stunde (0-basiert; `after` 1 = nach der 2. Stunde) |
| `school_days` | Liste Tage 0–6 | leer = Montag … `days`−1 | Unterrichtstage der Schule (einzelne Wochentage, bis 7) |
| `days` | Ganzzahl | 5 | abgeleitet aus `school_days`; Obergrenze 7 |
| `week_numbering` | Auswahl | `iso` | `iso` = Kalenderwochen; `school_year` = Woche 1 ist Schuljahresbeginn |
| `year_start_mode` | Auswahl | `auto` | `auto` = Ende der Sommerferien (aus Ferien); `own` = `school_year_start` |
| `school_year_start` | Datum | leer | eigener Schuljahresbeginn, nur bei `own` |
| `school_year_history` | Liste Datum | [] | Beginne früherer Schuljahre |
| `plan_periods` | Liste {id, name, date_from, date_to, from_week, to_week} | [] | Planzeiträume (Halbjahre), je ein eigener Plan; leer = ein Plan fürs Schuljahr |
| `site_travel_periods` | Ganzzahl | 1 | freie Stunden beim Standortwechsel ohne hinterlegte Wegezeit |
| `site_travel` | Liste {a, b, minutes} | [] | Wegezeit je Standortpaar, beide Richtungen |
| `core_latest_period` | Ganzzahl | 5 | Hauptfächer spätestens bis zu dieser Stunde (0-basiert; 5 = 6. Stunde) |
| `teacher_self_service` | Auswahl | `approval` | `approval` = Selbstauskünfte brauchen Genehmigung; `direct` = sofort gültig |
| `teacher_times_self` | Bool | false | Lehrkräfte dürfen Arbeitszeiten selbst festlegen (je Lehrkraft überschreibbar) |
| `max_exams_per_week` / `max_exams_per_day` | Ganzzahl | 3 / 1 | Klassenarbeiten je Klasse und Woche/Tag; Rangfolge Schule → Jahrgang → Klasse; 0 = keine Grenze |
| `exam_limits_by_grade` | Objekt {Jahrgang: {per_week, per_day}} | {} | Jahrgangsvorgabe |
| `auto_replan` | Bool | true | nach Stammdaten-/Planänderungen werden ungültige/fehlende Stunden automatisch neu angelegt |
| `grade_min` / `grade_max` | Ganzzahl | 0 / 20 | zulässige Klassenstufen (eine einheitliche Grenze für alle Eingaben) |

Einstellungsfelder haben Grenzwerte und Fehlerprüfung; Auswahlwerte außerhalb der Liste werden abgelehnt (Bestand: nicht erzwungen). Lesen/Ändern: `settings.edit`; `POST /settings/calendar-preview` zeigt die Wirkung einer geplanten Kalenderänderung vorab.
Abnahme: Neue Instanz → `GET /settings` liefert genau diese Standardwerte; `PUT /settings` mit `periods` 17 → 422 Klartext; mit `week_numbering` „xyz“ → 422; ohne `settings.edit` → 403.

**STA-012** · P1 · Status: Ist
Standort (`sites`): Kennung (Pflicht), Name (Pflicht). Verweis aus Lehrkräften, Räumen, Klassen, Aufsichtsbereichen, Wegezeiten. Standorte erscheinen in Filtern (Klassenliste) und in Plänen; Pendeln/Wegezeiten werden nur angezeigt, wenn die Schule mehr als einen Standort hat (LEH-017).
Abnahme: Standort „Außenstelle“ anlegen → in Raum-, Klassen- und Lehrkraft-Dialogen wählbar; Löschen eines Standorts mit zugeordneten Räumen zeigt die Folgenvorschau (STA-036).

**STA-013** · P1 · Status: Ist
Fach (`subjects`): `id` Kürzel (Pflicht), `name` (Pflicht), `room_type` (leer = Klassenraum; z. B. Sporthalle, Chemie), `core` Hauptfach (false; zählt für „früh am Tag“ bis `core_latest_period`), `max_per_day` (1 Block je Klasse und Tag), `color` (`#rrggbb`, leer = automatisch). Montessori-Bereiche wie Freiarbeit, Morgenkreis, Epoche sind Fächer.
Abnahme: Fach mit nur Kürzel und Name anlegen → `core` false, `max_per_day` 1, Farbe automatisch; Fach ohne Name → 422 Klartext.

**STA-014** · P1 · Status: Ist
Raum (`rooms`): `id`, `name` (Pflicht), `type` (Standard „Klassenraum“; wird mit dem Raumtyp des Fachs abgeglichen), `site` (Standort; ein Raum gehört zu genau einem Standort), `capacity` (30 Plätze). Ein Raum kann je Zeit nur einmal belegt werden, auch nicht von zwei Teilen desselben Kurses (Team-Teaching braucht Nebenräume).
Abnahme: Raum ohne Standort speichern → 422 „Raum braucht einen Standort“ (Klartext); Raum „101“ mit Standort speichern → Typ „Klassenraum“, Kapazität 30.

**STA-015** · P1 · Status: Ist
Klasse (`classes`): `id` Kürzel (Pflicht), `name` (Pflicht), `grade` Klassenstufe (Pflicht, `grade_min`–`grade_max`), `students` (Richtwert 25; sobald Schüler/innen zugeordnet sind, wird die Zahl aus der Schülerliste berechnet, das Handfeld gilt nur ohne Zuordnung und ist so gekennzeichnet), `home_room` (Klassenraum), `site`, `max_periods_per_day` (8), `unavailable` (Sperrzeiten der Klasse als Zeitregeln, z. B. Praxistag), `class_teacher` (genau eine Person, siehe STA-043), `school_days` (leer = Schulvorgabe; nur mit `timetable.edit` änderbar), `max_exams_per_week/day` (leer = erben), `profile` (Jahrgang, leer erlaubt).
Abnahme: Klasse mit Kürzel, Name, Stufe 5 anlegen → `max_periods_per_day` 8, `students` aus Liste (0 bei leerer Liste); `school_days` ändern als Konto nur mit `masterdata.edit` → 403.

**STA-016** · P1 · Status: Ist
Schüler/in (Stammdaten): `id` (Pflicht; aus Schülernummer, fehlt sie: aus Name und Klasse gebildet), `name` (Pflicht), `class_id` (Pflicht), `courses` (Kurs-Zuordnung als Liste „Kurs#Teil“), `birth_date` (optional). Konten und Eltern-Verknüpfungen liegen in der Datenbank; die Verbindung zum Planungsstand läuft nur über IDs (Konto ↔ `student_id`/`teacher_id`, Eltern ↔ `student_id`). Details zu Selbstbedienung, Förderung und Eltern: Abschnitt 3 (SCH).
Abnahme: Schüler ohne Klasse speichern → 422; `birth_date` „31.02.2010“ → 422; Schüler mit Eltern-Konto: Löschen des Schülers sperrt das verknüpfte Konto (STA-036).

**STA-017** · P1 · Status: Ist
Stundentafel (`curricula`): `id`, `name` (Pflicht), `classes` (gilt nur für diese Klassen; höchster Rang), `entries` Liste {Fach (Pflicht), Wochenstunden (Pflicht, ganze Zahl), Doppelstunde (false)}, `base` (abgeleitet von), `deltas` (nur mit `base`: Stundendifferenz, auch negativ, bzw. Zielwert der Doppelstunde), `grades` (Altbestand nach Klassenstufe, nur Rückfall). Dasselbe Fach zweimal in einer Tafel → 422.
Abnahme: Stundentafel mit Fach „Mathe“ zweimal speichern → 422 „Fach ist doppelt“; Zeile ohne Wochenstunden → 422.

**STA-018** · P1 · Status: Ist
Jahrgang / Bildungsgang (`grade_profiles`): `id` (Präfix `JG`), `name` (Pflicht, frei, z. B. „5“, „5 Informatik“, „Montessori“, „GIF 26“, „Schreiner“), `short`, `grade` (Klassenstufe, optional; für Sortierung/Vorlagen/Regeln), `color` (`#rrggbb`, leer = automatisch), `description`, `department` (Schulform/Abteilung, optional), `curriculum` (Stundentafel des Jahrgangs, leer = keine). Ein Jahrgang ist ein eigener Bildungsgang, nicht nur eine Stufe.
Abnahme: Jahrgang „5 Informatik“ mit Farbe `#2a7de1` anlegen, danach „5“ ohne Stufennummer anlegen → beide in der Übersicht; Farbe `blau` → 422.

**STA-019** · P1 · Status: Ist
Kurs (`courses`) und Kursteil: Kurs = Unterricht, der `hours` Mal je Woche stattfindet: `id`, `classes` (Pflicht), `parts` (Pflicht, parallele Teile), `hours` (Pflicht, Wochenstunden), `double` (false), `label`, `weeks` oder `rhythm` (STA-055), `origin` (`manual` | `curriculum`), `pinned` (Liste manuell geänderter Felder bleibt bei Neuerzeugung). Kursteil: `subject` (Pflicht), `teacher` (leer = automatische Zuweisung), `room` (fest, leer = keiner), `room_type` (überschreibt Fachraumtyp), `label`, `students` (leer = alle Schüler/innen der Klassen des Kurses). Mehrere Klassen und/oder Teile = Kopplung, alle Teile liegen gleichzeitig. Besondere Zuschnitte (Team-Teaching, Band über mehrere Gruppen, gemeinsame Stunde zweier Gruppen, Epoche, Schulbegleitung, Doppelblock) sind Kurse von Hand; Kurse mit eigener Wochenangabe zählen in der Stundentafel anteilig (12 von 52 Wochen = 0,23 der Stunden). Der Kurs-Editor und die Stundentafel haben dieselbe Obergrenze der Wochenstunden (Bestand: 20 gegen 40).
Abnahme: Kurs mit 12 Wochen und 4 Std. zählt 0,92 Std. in der Stundentafelsumme; Teil ohne `teacher` wird bei „Lehrkräfte zuweisen“ befüllt; Kurs mit 25 Wochenstunden lässt sich im Editor speichern, wenn die Stundentafel 25 erlaubt.

**STA-020** · P1 · Status: Ist
Ferien/Feiertag (`holidays`): `id`, `name`, `date_from`, `date_to` (inklusiv), `kind` (`ferien` | `feiertag` | `beweglich` | `schulfrei`; fehlt/unbekannt: Name mit „ferien“ → `ferien`, sonst `feiertag`), `source` (Herkunft Import, leer = von Hand), `source_sig` (Wiedererkennung). An diesen Tagen ist kein Unterricht.
Abnahme: Eintrag „Herbstferien“ 12.–23.10. → in diesem Zeitraum meldet der Schultag-Check „kein Unterricht“; `date_to` vor `date_from` → 422 (Bestand: wirkt nie).

**STA-021** · P1 · Status: Ist
Schulkalender-Termin (`events`): `id`, `title`, `date_from`, `date_to` (leer = `date_from`), `time_from`/`time_to` (leer = ganztägig), `kind` (`termin` = Information, z. B. Elternabend; `pflicht` = Anwesenheit Pflicht, z. B. Tag der offenen Tür am Samstag), `classes`, `grades` (beide leer = ganze Schule), `location`, `note`, `teachers` (teilnehmende Lehrkräfte, z. B. Fortbildung: sie fehlen im Unterricht, die Vertretung behandelt sie wie Abwesende für die Stunden des Termins). Termine erscheinen im Stundenplan der Betroffenen, auch am Wochenende.
Abnahme: Termin „Tag der offenen Tür“ Samstag, `pflicht`, ganze Schule → erscheint in den Plänen aller Schüler/innen am Samstag; Termin mit teilnehmender Lehrkraft 8–10 Uhr → die Vertretungsplanung führt deren Stunden dieser Zeit als Ausfall.

**STA-022** · P2 · Status: Ist
Zweige/Abteilungen (`branches`): `name` (eindeutig), `sites`, `grades`, `class_ids` (Liste Standorte/Klassenstufen/Klassen); Zuordnung Konto (Abteilungsleitung) ↔ Zweig in `user_branches` (Schlüssel Konto + Zweig, Kaskade). Rollen-Hierarchie: Lehrkraft → Klassenleitung → Abteilungsleitung (Schulzweig) → Sekretariat/Schulleitung; dazu Hausmeister/in und Administration; im Profil sichtbar („Ihre Rolle: …“).
Abnahme: Zweig „IT“ mit Klassenstufen 11–13 anlegen, Konto `abteilungsleitung` zuordnen → Rechte mit Umfang „eigener Zweig“ greifen nur für diese Klassen; Zweig löschen entfernt die Zuordnung, nicht das Konto.

**STA-023** · P1 · Status: Ist
Konventionen der Stammdaten: leere Listen bedeuten „alle“ (`days` = jeder Tag, `periods` = ganzer Tag, `Event.classes`+`grades` = ganze Schule, `Teacher.sites` = alle Standorte, `weeks` = alle Wochen); unbekannte Felder werden beim Lesen verworfen, fehlende optionale Felder erhalten den Standardwert (alte Stände laden unverändert); Datumsfelder ISO; Kennungen sind Text.
Abnahme: Ein älterer Stand ohne neues Feld lädt fehlerfrei und zeigt den Standardwert; Abwesenheit ohne `periods` gilt für den ganzen Tag.

**STA-024** · P0 · Status: offen (Ist: Eindeutigkeit/Verweise nicht erzwungen)
Validierung aller Wege (Oberfläche, API, CSV, JSON, Untis) durch dieselbe Prüfung: Pflichtfelder; **Kennungen je Sammlung eindeutig und ohne Beachtung der Groß-/Kleinschreibung** („MUE“ ≠ „mue“ ist ein Fehler); neue Kürzel ohne Leerzeichen; Verweise (Raum→Standort, Klasse→Raum/Lehrkraft/Jahrgang, Kurs→Klasse/Fach/Lehrkraft/Raum, Block→Kurs, Abwesenheit→Lehrkraft/Klasse/Raum/Kurs, Aufsicht→Bereich/Lehrkraft, Lehrkraft→Fach/Standort) müssen existieren (422 mit Klartext, z. B. „Klasse 5a verweist auf den unbekannten Raum 999“); Referenzfelder werden an drei Stellen gepflegt (Feldprüfung, Verweisprüfung, Löschweitergabe), sonst blockieren Altverweise spätere Speicherungen; Datum `date_to` ≥ `date_from`; Wertelisten (Arten, Aktionen) werden erzwungen. Die Prüfung läuft auch bei Import; Import gilt ganz oder gar nicht, Fehler mit Zeilennummer.
Abnahme: Zweiter Datensatz mit Kürzel „mue“ neben „MUE“ → 422; Import-Datei mit einer fehlerhaften Zeile von 100 → nichts wird gespeichert, Meldung nennt Zeilennummer; Kurs mit unbekannter Lehrkraft → 422.

**STA-025** · P2 · Status: offen
Erweiterbarkeit und CSV-Rundlauf (prüfbar am Ergebnis): Ein neues Feld/eine neue Sammlung hat einen Standardwert (alte Stände laden), Eintrag in der Sammlungsliste mit Schreibrecht/Präfix/Bezeichnung/Umfang, Feld-/Verweisprüfung, Löschweitergabe, CSV-Import/-Export und Typen in der Oberfläche; CSV-Import/-Export kennt Stundentafel-Ableitung und Jahrgang (Bestand: Lücke).
Abnahme: CSV-Rundlauf (Export, leere Instanz, Import) ergibt identische Jahrgänge samt Stundentafel-Ableitung (`base`/`deltas`), Farben und Zuordnung der Klassen.

### 1.3 Jahrgänge (Bildungsgänge), Stundentafeln, Fächer, Räume

**STA-026** · P1 · Status: Ist
Jahrgänge frei anlegen und in einer Übersicht pflegen (Stammdaten-Reiter „Jahrgänge“ vor „Klassen“). Je Jahrgang: Klassen, Schüler/innen, Kurse, Kurse ohne Lehrkraft, Stundentafel (direkt zuweisbar); je Klasse: Klassenleitung, Stundentafel, Kurse. Jahrgänge lassen sich abrufen („was hat der Jahrgang?“), hinzufügen, verkleinern, ändern. Neue Klassen können aus der Übersicht angelegt werden. Karten mit Farbe im Kopf; Abschnitt „Ohne Jahrgang“ steht zuletzt; Sortierung natürlich (5a vor 10a). Nutzer 10-12: „dieses Jahrgänge Ding kann weg“ – es gibt keine zweite Aktion „Jahrgänge hinzufügen“ neben der Übersicht („viel zu viele Optionen für genau das gleiche“). Nutzer 10-16: Beispiele „5“, „5 Informatik“, „Montessori“, „GIF 26“, „Schreiner“; „Es gibt nur eine Stundentafel ‚Jahrgang 5‘“ war die Kritik – gewünscht ist eine Stundentafel je Jahrgang.
Abnahme: Übersicht zeigt je Jahrgang die fünf Kennzahlen; Jahrgang ohne Klasse zeigt 0; Klasse ohne Jahrgang steht in „Ohne Jahrgang“; Jahrgang „5 Informatik“ besitzt eine andere Stundentafel als „5“; die Oberfläche enthält keine separate Aktion „Jahrgänge hinzufügen“.

**STA-027** · P1 · Status: Ist
Klassen werden jedem Jahrgang frei und auch nachträglich zugewiesen (Dialog „Klassen zuordnen“, mehrere Klassen auf einmal; `POST /grade-profiles/assign`). Jede Klasse hat höchstens einen Jahrgang. Eine Zuweisung zeigt vorab die Folgen (wirksame Stundentafel, betroffene Kurse); entsteht eine Überschneidung gleichrangiger Tafeln, wird sie gemeldet (STA-030). Nutzer 10-16: „keine Klassen die man für eigene Schuljahrgänge zuweisen kann“ ist behoben.
Abnahme: Klasse 5a von „5“ nach „5 Informatik“ umhängen → neue Version im Verlauf, Kurse der 5a folgen der neuen Tafel erst nach „Kurse aktualisieren“ (Vorschau); Konto ohne `timetable.edit`/`masterdata.edit` → 403.

**STA-028** · P1 · Status: Ist
Stundentafel-Editor als echte Tabelle (Fächer × Jahrgänge, `GET /grade-profiles/matrix`) mit Summen je Jahrgang und farbig markierten Abweichungen. Summe „von höchstens N möglichen Wochenstunden“ (N = Unterrichtstage × Stunden je Tag [unklar: Berechnung]), rot bei Überschreitung. Warnung bei ungespeicherten Änderungen beim Verlassen (App-Dialog). Eine neue Stundentafel wird als Kopie einer bestehenden begonnen; „Neue Stundentafel“ zeigt ein leeres Formular ohne markierten Fremdeintrag; jede Tafel ist direkt öffenbar; „Gilt für“ zeigt die tatsächlich betroffenen Klassen. Am Handy (390 px) ohne waagerechten Seitenbildlauf (Tabelle scrollt innen oder wird zu Karten).
Abnahme: Matrix mit 3 Jahrgängen und 12 Fächern zeigt 3 Summen; weicht „5 Informatik“ bei Informatik um +2 ab, ist die Zelle farbig; Summe > N → rot; Verlassen mit Änderungen → Dialog „Ungespeicherte Änderungen“; kein Browser-Popup.

**STA-029** · P1 · Status: Ist
Stundentafel von einer anderen ableiten („wie 5, plus 2 Std. Informatik“): `base` plus `deltas` (je Fach Stundendifferenz oder Zielwert); wirksame Zeilen werden immer aus der Ableitung berechnet, nie aus gespeicherten Zeilen (`POST /curricula/derive`). Kreisbezüge werden mit 422 abgewiesen. Wird die Basis gelöscht, werden Ableitungen eigenständig übernommen und bleiben erhalten.
Abnahme: Tafel „5 Informatik“ aus „5“ mit +2 Informatik; Basis „5“ um 1 Std. Mathe erhöhen → Ableitung zeigt die Erhöhung ebenfalls; Ableitung von sich selbst oder 5→6→5 → 422; Basis löschen → Ableitung bleibt mit denselben wirksamen Zeilen bestehen.

**STA-030** · P1 · Status: Ist
Wirksame Stundentafel einer Klasse nach Rangfolge: (1) eigene Tafel der Klasse (`classes`-Liste), (2) Tafel des Jahrgangs, (3) Altbestand nach Klassenstufe (nur Rückfall). Die Herkunft (Klasse, Jahrgang, Stufe, keine) wird angezeigt (`GET /planning/curricula/effective` liefert je Klasse die gültige Tafel, Herkunft, Konflikte). Überschneiden sich zwei Tafeln gleichen Rangs für dieselbe Klasse: Speichern → 409 mit Klassenliste; mit Bestätigung (`force`) wird gespeichert und „Kurse erzeugen“ meldet den Konflikt. Hat eine Klasse keine oder eine leere Tafel, meldet „Kurse erzeugen“ dies mit dem Klassennamen. Vorrang künftig Klasse > Klassengruppe > Bildungsgang+Jahrgang > Jahrgang (STA-094).
Abnahme: Zwei Tafeln für Klasse 5a über die Klassenliste → 409 mit „5a“; mit `force` gespeichert, „Kurse erzeugen“ nennt den Konflikt; neue Klasse 11 mit leerer Tafel → Meldung „Klasse 11a: keine Stundentafel mit Fächern“.

**STA-031** · P1 · Status: Ist
Stundentafel pro Klasse (Sonderfall): im Dialog „Klasse anlegen/bearbeiten“ (Verwaltung, `masterdata.edit`) und im Reiter „Stundentafel“ der Klassenseite (auch Klassenleitung der eigenen Klasse). Bei neuen Klassen ist die Tafel des Jahrgangs vorausgefüllt; eine eigene Tafel entsteht erst bei Abweichung. Kurse und Lehrkräfte entstehen sofort, der Stundenplan wird ergänzt; nur die Kurse der betroffenen Klasse werden neu erzeugt. Schreiben: `masterdata.edit` oder `timetable.edit`; Klassenleitung nur für die eigene Klasse.
Abnahme: Klassenleitung 5a setzt Mathe auf 5 Std. → nur Kurse der 5a ändern sich; dieselbe Person ändert die Tafel der 5b → 404; neue Klasse „6a“ zeigt die Jahrgangstafel vorausgefüllt.

**STA-032** · P1 · Status: Ist
Kurse aus Stundentafeln erzeugen (Planung): zuerst Vorschau-Lauf (nichts wird geändert), dann Erzeugen der fehlenden Fächer als Ein-Teil-Kurse je Klasse (`origin` = `curriculum`); Klassenleitung/Bezugsperson trägt man von Hand ein. „Lehrkräfte zuweisen“ weist nach Fächern und Deputat zu, der Bericht nennt offene Teile und unterscheidet „keine Lehrkraft mit Fach X“ von „kein freies Deputat“. Im Kurs-Editor geänderte Felder (Stunden, Doppelstunde, Raum, Lehrkraft) bleiben bei erneutem Erzeugen erhalten (`pinned`; der Bestätigungstext sagt das). Werden Stunden gesenkt, meldet der Qualitätsbericht „X Stunden zu viel verplant“ je Kurs; „Kurse aktualisieren“ bietet an, überzählige nicht fixierte Stunden zu entfernen (Vorschau, dann Übernehmen). Nach dem Speichern einer Tafel führt „Kurse der betroffenen Klassen aktualisieren“ (mit Vorschau) direkt zum Ergebnis. Filter „ohne Lehrkraft“. Doppelte Kurs-IDs dürfen nicht entstehen.
Abnahme: Klasse 5a mit Tafel Mathe 4 → Vorschau zeigt „1 Kurs neu“; Erzeugen legt ihn an; Raum im Kurs ändern, erneut erzeugen → Raum bleibt; Mathe auf 3 senken → Bericht „1 Stunde zu viel verplant“; Vorschau entfernt nur nicht fixierte Stunden.

**STA-033** · P1 · Status: Ist
„Fach hinzufügen“ ist eine einzige Aktion (Planung und Stundentafel der Klasse): durchsuchbare Fachliste, ganz unten „Neues Fach anlegen …“; bei unbekanntem Namen „„Xyz“ als neues Fach anlegen“; Kürzel-Vorschlag (Informatik → INF) mit Kollisionsprüfung; neues Fach startet mit 2 Wochenstunden; Hauptfach und Farbe unter „Mehr Optionen“; Recht `masterdata.edit`. Nutzer 10-12: „die Neues Fachhinzufügen Option in die Fachhinzufügen Option zusammentun … und dann auf Fach ganz unten einfach auf Neues Fach gehst, das reicht.“ Ein separater Knopf „Neues Fach“ entfällt.
Abnahme: Suche „Info“ zeigt „Informatik“; Eingabe „Xyz“ bietet „„Xyz“ als neues Fach anlegen“; Kürzel für „Informatik“ lautet „INF“; ist „INF“ vergeben → Meldung mit Alternativvorschlag; es gibt keine zweite Schaltfläche „Neues Fach“.

**STA-034** · P2 · Status: offen
Raumtypen und Fachbindung: Oberfläche zur Pflege von Raumtypen und Tags; allgemeine Räume (Mathe, Deutsch, Sprachen) und Fachräume (z. B. Fachinformatik, Maler/Lackierer) mit Ausstattung; ein Fach bindet an einen Raumtyp; Klassen dürfen für Fachstunden aus einem Raum verdrängt werden („kann dann den Raum beziehen“). Bestand: Raumtyp als Freitext am Raum/Fach.
Abnahme: Raumtyp „Malerwerkstatt“ anlegen, Fach „Lackieren“ daran binden → der Generator belegt für „Lackieren“ nur Räume dieses Typs; Raumtyp mit zugeordneten Räumen löschen → Folgenvorschau.

**STA-035** · P3 · Status: Ist
Altbestand-Umstellung (nur bei Datenübernahme aus einem Bestand ohne Jahrgänge): Stufenbasierte Stundentafeln werden per Vorschau in Jahrgänge `JG<n>` überführt, nie automatisch beim Laden; bei mehreren abweichenden Tafeln je Stufe bleibt die Stufenangabe stehen und der Konflikt ist sichtbar (Banner in der Jahrgangsansicht). Im Neubau ohne Altbestand entfällt dieser Weg.
Abnahme: Datenübernahme mit Stufentafeln 5–7 → Vorschau listet 3 Jahrgänge `JG5`–`JG7`; ohne Bestätigung ändert sich nichts.

**STA-036** · P0 · Status: Ist
Löschen mit Folgenvorschau und Rückgängig für Jahrgang, Stundentafel, Fach und Klassen: Der Dialog (App-Dialog, Sie-Form: „Möchten Sie das wirklich löschen?“) zeigt die Folgen in Kennzahlen (z. B. „betrifft 3 Klassen, 42 Kurse“; Schüler/innen, Stunden). Bei Datenverlust muss das Wort „löschen“ eingetippt werden (Schwelle [unklar: Wert]). Schüler/innen können in eine andere Klasse verschoben werden; beim Löschen eines Jahrgangs können Klassen in einen anderen Jahrgang umziehen, die Stundentafel kann optional mitgelöscht werden. Alles läuft über den Änderungsweg (STA-004) und ist mit Rückgängig umkehrbar. Nutzer 10-16: „mir fehlt so eine richtige Option Dinger zu löschen“.
Abnahme: Jahrgang mit 3 Klassen löschen → Vorschau „betrifft 3 Klassen, 42 Kurse“, Löschen erst nach Eingabe von „löschen“; danach „Rückgängig“ stellt Jahrgang, Zuordnung und Tafel her; ohne Schreibrecht → 403.

**STA-037** · P1 · Status: offen
Folgenvorschau und Rückgängig auch beim Löschen von Lehrkräften, Räumen, Standorten, Kursen und Schüler/innen (Bestand: nur Klassen, Jahrgänge, Stundentafeln, Fächer); Löschen einer Person sperrt das verknüpfte Konto (laufende Sitzungen enden; die Benutzerverwaltung zeigt „ohne Datensatz“ mit „deaktivieren“/„löschen“; Eltern sehen kein Kind ohne Klasse).
Abnahme: Raum löschen, der in 4 Kursen fest eingetragen ist → Vorschau nennt 4 Kurse; Schüler löschen → sein Konto kann sich nicht mehr anmelden, bestehende Sitzung endet.

### 1.4 Klassen

**STA-038** · P1 · Status: Ist
Klassenliste `/klassen` (Recht `masterdata.edit` oder `substitution.edit`): Freitextsuche nach Klassenbezeichnung, Klassenleitung oder Raum; Filter nach Standort; Liste nach Jahrgang gruppiert mit Anzahl je Gruppe; Suche und Standort sind über Adressparameter setzbar (`/klassen?q=…&standort=…`). Schüler/innen und Eltern haben keinen Zugriff auf die Klassenseiten.
Abnahme: `/klassen?q=5a&standort=Hauptgebäude` zeigt nur passende Klassen, Gruppenüberschrift „5 Informatik (3)“; Konto `eltern` → Menüpunkt fehlt, direkter Aufruf → 403.

**STA-039** · P1 · Status: Ist
Klassen-Detail `/klassen/{id}` (Recht `masterdata.edit`, `substitution.edit` oder `timetable.edit`; Inhalte je Reiter nach Recht): Kopf mit Jahrgang, Standort, Schülerzahl, Klassenraum, Klassenleitung (als Badge); Raum und Klassenleitung direkt änderbar. Reiter über Adressparameter ansteuerbar (`?tab=wochenplan|lehrkraefte|schueler&datum=…`) plus Stundentafel, Klassenbuch-Übersicht, Fehlzeiten-Statistik. „Lehrkräfte“: je Fach Kurse/Kursteile mit Lehrkraft, Klassenleitung markiert. „Schüler/innen“: Liste mit Kursbelegung und Kontostatus; „Schüler/in hinzufügen“ nutzt dieselbe Eingabe wie das Anlegen (STA-041) mit Konto-Optionen und Vorschau und speichert nur bei passender Vorschau. Statusanzeigen immer mit Text und Kurzzeichen, nie nur Farbe. Wochenplan: Raster ab 700 px Breite (Mindestbreite 640 px), darunter Liste; Wahl wird im Browser gemerkt; Planen von Vertretung/Ausfall nur mit `substitution.edit` und nach Vorschau (Datei VER).
Abnahme: `/klassen/{id}?tab=schueler` öffnet den Reiter; Klassenraum im Kopf ändern → sofort gespeichert und im Verlauf; fremde/nicht existente Klasse → 404; Breite 600 px zeigt die Wochenliste statt Raster.

**STA-040** · P1 · Status: Ist
Klasse anlegen (Assistent `/klassen/neu`, Recht `masterdata.edit`): (1) Klasse: Bezeichnung, Jahrgang, Standort, Unterrichtstage, Klassenraum, Klassenleitung, Stundentafel (vom Jahrgang vorbelegt); (2) Schülerliste einfügen (STA-041); (3) Konten als Probelauf mit Vorschau der anzulegenden Konten; Anlegen. Schülerkonten werden standardmäßig mit angelegt (Konto-Optionen: Standardwerte, Empfänger der Zugangsinformationen); die Klasse ist auch ohne Konten anlegbar. Gespeichert wird nur, wenn die Vorschau zur aktuellen Eingabe passt; jede Änderung macht die Vorschau ungültig. Neue Zugangsdaten erscheinen einmalig in einem Dialog und werden nicht im Klartext gespeichert. Mit Schülerkonten ist zusätzlich `users.manage` nötig; **403 nur, wenn tatsächlich Konten angelegt werden** (Bestand: Planer ohne `users.manage` erhält auch ohne Schülerliste 403). Volljährige Schüler/innen erhalten kein automatisches Elternkonto (SCH-004).
Abnahme: `planer` ohne `users.manage` legt Klasse ohne Schülerliste an → 200; mit Schülerliste und Konten → 403 mit Klartext; Schülerliste nach der Vorschau ändern → „Anlegen“ gesperrt bis neue Vorschau; Zugangsdaten sind nach Schließen des Dialogs nicht mehr abrufbar.

**STA-041** · P1 · Status: Ist
Schülerliste einfügen (aus Tabellenkalkulation, Textverarbeitung, Text; Trennzeichen wird erkannt; Formathilfe im Hilfe-Symbol): jede Zeile bearbeitbar, Fehler je Zeile. Zeilenweise Erkennung: Namen (Schreibweise korrigiert, Vor-/Nachname getrennt, Namenszusätze wie „van“, „von“, „de“), Geburtsdatum in mehreren Formaten, E-Mail-Adressen formal geprüft, Ja/Nein-Felder (gängige Wörter), Eltern je Schüler/in mit Kontaktdaten, Begleitung (Begleitperson wird einem Kind zugeordnet). Spalten werden nicht per Teilstring zugeordnet („Geburtsort“ ist nie Geburtsdatum, „Telefon Eltern“ nie Name; Bestand-Mangel). Obergrenze je Eingabe: ein einziger Wert für Server und Oberfläche [unklar: Bestand 60 bzw. 500].
Abnahme: Drei Zeilen mit gemischten Datumsformaten (`TT.MM.JJJJ`, `JJJJ-MM-TT`) werden erkannt; Spalte „Geburtsort“ wird nicht als Geburtsdatum übernommen; E-Mail „max@@x“ → Zeile rot, nichts wird gespeichert; Überschreiten der Obergrenze → Meldung mit dem Wert.

**STA-042** · P1 · Status: Ist
Mehrere Klassen auf einmal anlegen: Serien wie „5a–5d“ werden ausgeschrieben, Namensvorschlag 5a, 5b, 5c; Einstellungen einer vorhandenen Klasse sind kopierbar; Kurse sind direkt anlegbar; Stufe/Jahrgang anlegen und umbenennen; Klassen umbenennen. Massenlöschung von Klassen mit Folgenanzeige (STA-036). Recht `masterdata.edit`.
Abnahme: „5a–5d“ erzeugt vier Klassen mit den Einstellungen der Vorlageklasse; Massenlöschung von 3 Klassen zeigt Folgen und verlangt Bestätigung; ohne Recht → 403.

**STA-043** · P1 · Status: Ist
Klassenleitung: genau eine Person je Klasse (`class_teacher`); im Klassenkopf und im Dialog änderbar; Verhalten ohne Klassenleitung [unklar: Anzeige „keine Klassenleitung“, Funktionen, die eine Leitung brauchen, melden dies]. Mehrere Leitungen siehe STA-044.
Abnahme: Klasse ohne Klassenleitung speichern gelingt; Funktionen „Atteste prüfen“/„Krankmeldungen verwalten“ der Klasse sind dann nur für Sekretariat/Schulleitung erreichbar und die Klassenseite zeigt „Keine Klassenleitung“.

**STA-044** · P1 · Status: offen
Klassenrollen (Pflicht-Rückmeldung des Betreibers, Backlog B-15/B-19): mehrere Klassenleitungen (Reihenfolge = Hauptverantwortung), Stellvertretung, Abteilung, Klassensprecher/in (höchstens 2 Schüler/innen), Verwalter einer Klasse (pflegt Raum, Rollen, Schülerliste und erzeugt Zugangsdaten ohne globale Rechte), Abteilungsleitung mit Rechten für die Klassen ihrer Abteilung; Sammlung `departments` (Name, Klassen bzw. Bildungsgänge/Jahrgänge, Leitungen). Alles, was an „Klassenleitung“ hängt (Krankmeldungen verwalten, Atteste prüfen, Passwörter zurücksetzen, Zugangsdaten, Klassen-Kursraum, Postfach-Gruppe, Live-Hinweise, Vertretungsbonus), gilt für alle Leitungen und die Stellvertretung. Abwärtskompatibel (altes `class_teacher` = erste Leitung). Klassenkopf zeigt die Rollen als Chips mit „bearbeiten“; CSV-Spalte „Klassenleitung“ nimmt „LUD, KEL“; Lehrkraft-Stammdaten zeigen „Klassenleitung in …“ (nur lesen).
Abnahme: Klasse mit zwei Leitungen → beide dürfen Atteste prüfen; Abteilungsleitung der Abteilung darf, die einer anderen Abteilung erhält 404; dritter Klassensprecher → 422 „höchstens zwei“; alter Stand mit nur `class_teacher` lädt unverändert.

**STA-045** · P0 · Status: Ist
Rechte der Klassenfunktionen: Klassenliste `masterdata.edit` oder `substitution.edit`; Klasse neu `masterdata.edit` (mit Schülerkonten zusätzlich `users.manage`, sonst 403); Klassen-Detail `masterdata.edit`, `substitution.edit` oder `timetable.edit`; Klasse ändern `masterdata.edit` oder `timetable.edit`; Schüler/in hinzufügen `masterdata.edit`; Ausfall eintragen und Wochenplan lesen `substitution.edit`; Stundentafel/Jahrgänge lesen: angemeldet, schreiben `masterdata.edit` oder `timetable.edit`; Massenanlage/-löschung `masterdata.edit`. Schüler/innen und Eltern sind von der Klassenseite ausgeschlossen. Fremde Klassen (nicht im eigenen Umfang) liefern 404, fehlendes Recht 403. Mehrere Rechte werden als „eines davon“ gelesen.
Abnahme: Rechte-Matrix-Test je Zeile (Rolle × Aktion → 200/403/404) grün; Lehrkraft ohne Klassenleitung ruft Detail einer fremden Klasse → 404.

**STA-046** · P2 · Status: Ist
Klassen-Kanal: Regelplan (regulärer Wochenplan der Klasse), Termine (z. B. Elternabende) anlegen und löschen, Ansprechpersonen der Klasse. Anzahl Termine je Klasse begrenzt [unklar: Wert]; Sichtbarkeit für Klassenmitglieder und Änderungsrecht [unklar: Vorschlag Klassenleitung und Verwaltung]. Kalenderwoche einer Klasse/Lehrkraft/eines Raums/Schülers zeigt Overlays (Klausuren mit Hinweis, Hausaufgaben mit Link zum Kursraum, Termine, Abwesenheit); je Tag ist die Zahl der Kurzanzeigen begrenzt, der Rest erscheint als Sammelhinweis [unklar: Grenze].
Abnahme: Elternabend anlegen → erscheint im Klassen-Kanal und in der Kalenderwoche; Termin über der Grenze → 422; Termin einer fremden Klasse löschen → 404.

**STA-047** · P2 · Status: offen
Einheitliche Grenzen und Regeln: Klassenstufe überall `grade_min`–`grade_max` (Bestand: Assistent 1–13, Datenschnittstelle 0–20); Klassenstufe aus dem Namen („5a“, „11 IT“) wird in Server und Oberfläche mit derselben Regel erkannt; Klassenbezeichnungsformat [unklar]; Jahrgangsfeld zeigt nach Leeren „leer“, nicht „0“; „Zurücknehmen“ eines Ausfalls mit Begleitungen ist atomar; Klassen haben `active` (archivieren statt löschen).
Abnahme: Klasse mit Stufe 0 über Assistent und über Datenschnittstelle anlegbar, Stufe 21 in beiden → 422; archivierte Klasse erscheint nicht in der Klassenliste, bleibt in Auswertungen lesbar.

### 1.5 Schuljahr, Wochen, Zeitraster, Ferien, Termine

**STA-048** · P1 · Status: Ist
Schuljahresbeginn: `year_start_mode` „Automatisch (nach den Sommerferien)“ = erster Arbeitstag nach den Sommerferien aus dem Ferienimport (STA-057); „Eigener Schulstart“ mit Datum (`school_year_start`) für Schulen mit abweichendem Start. Wird der Start innerhalb des Schuljahres korrigiert, wandern alle gespeicherten Wocheneinträge mit, damit sie dieselben Kalenderwochen treffen; der alte Beginn landet in `school_year_history`. Nutzer 10-12: „Das Beginn des Schuljahrs soll bitte auch automatisch gesetzt werden, genauso wie die Ferien und so, dass das erkannt wird, wann das ist. Und wenn es Custom-Dinger gibt, soll die Schule sagen, ok, wir haben einen Custom-Schulstart und dann können die den setzen.“ Änderung nur mit `settings.edit`.
Abnahme: Modus `auto`, Sommerferien enden am Freitag → Schuljahresstart ist der folgende Montag; Modus `own` mit Datum → dieses Datum; Start um 7 Tage verschieben → eine Regel „ab KW 36“ gilt weiterhin ab KW 36.

**STA-049** · P1 · Status: Ist
Wochenanzeige und -eingabe in Kalenderwochen (KW): Standard `week_numbering` = `iso` („Kalenderwochen (KW)“), unter „Zeitraster & Schuljahr“ umschaltbar auf „Wochen ab Schuljahresbeginn“; intern laufen die Schulwochen fortlaufend 1–52 (Ferien zählen mit). Anzeigeformen: „Ab KW 36“, „KW 36, 38, 40 … (26 von 52)“, über den Jahreswechsel „KW 51, 52, 1–3“; Wochenwahl „‹ Woche 12 · KW 45 · 02.11.–08.11. › Heute“; die 52 Wochen sind durchblätterbar, die aktuelle Woche ist vorausgewählt; keine A/B-Wochen, keine Wochenbuchstaben (alte A/B-Daten wurden verlustfrei in das 52-Wochen-Modell umgewandelt). KW 53 wird als fehlend gemeldet, wenn das Jahr sie nicht hat. Nutzer 10-12: „Diese Zählung für Schuljahr soll bitte ab Woche 1 des Kalenderjahrs sein.“ (Bedeutung vom Nutzer nicht bestätigt; umgesetzt als KW-Anzeige mit interner Zählung und Umschalter; siehe 5.)
Abnahme: Wochenwahl zeigt „Woche 12 · KW 45 · 02.11.–08.11.“; Eingabe „KW 51, 52, 1–3“ speichert 5 Wochen über den Jahreswechsel; „KW 53“ in einem Jahr ohne KW 53 → Hinweis „fehlt“; Umschalten auf „Wochen ab Schuljahresbeginn“ ändert keine gespeicherten Daten, nur die Anzeige.

**STA-050** · P1 · Status: Ist
Planzeiträume (Halbjahre) `plan_periods`: je Zeitraum ein eigener Plan, bestehende Pläne bleiben; leere Liste = ein Plan fürs ganze Schuljahr. Halbjahre fest zum 31.01. und 01.02., weil es kein Zeugnisdatum gibt („C 10-12“). `from_week`/`to_week` werden beim Speichern aus den Daten berechnet. Verwaltung unter Planung → „Zeitraster & Schuljahr“: Speichern `settings.edit`; Plan eines Zeitraums kopieren oder löschen `timetable.generate` (`POST/DELETE /calendar/plan-periods/…`). Ein Zeitraum ohne Plan zeigt „Kein Stundenplan“ (der Knopf „Zum Generator“ nur mit Recht). Der Plan eines Zeitraums wiederholt sich im Folgejahr, bis der Jahreswechsel die Daten verschiebt (STA-079).
Abnahme: Zeiträume „1. Halbjahr bis 31.01.“, „2. Halbjahr ab 01.02.“ anlegen → Wochenwahl gruppiert nach Zeitraum; Zeitraum ohne Plan zeigt „Kein Stundenplan“; Plan kopieren ohne `timetable.generate` → 403.

**STA-051** · P1 · Status: Ist
Zeitraster: Beginn je Stunde (aufsteigend, `HH:MM`), Stundenlänge, Pausen (nach welcher Stunde, Name, Minuten), bis 16 Stunden je Tag (Beispiel der Einrichtungsanleitung: 14 Stunden von 08:00 bis 21:15, Pausen nach der 5., 6. und 9. Stunde). Doppelstunden: `double_alignment` `bloecke` (Standard: nur 1.–2., 3.–4. … innerhalb eines Pausenabschnitts, nie über eine Pause), `pausen` (nur nicht über eine Pause; passend für lange Freiarbeit), `frei`; `prefer_doubles` (Standard true: Fächer ab 2 Wochenstunden möglichst als Doppelstunde). Änderung von Zeitraster oder Unterrichtstagen, die Stunden verlieren würde, → STA-053. Nach einer Zeitraster-Änderung werden Zeitfenster der Lehrkräfte neu berechnet.
Abnahme: 14 Stunden 08:00–21:15 mit Pausen nach 5., 6., 9. Stunde speichern gelingt; Anfangszeiten nicht aufsteigend → 422; 17 Stunden → 422; Zeitfenster einer Lehrkraft wird nach Verschieben des Beginns neu berechnet.

**STA-052** · P1 · Status: offen
Zeitraster-Rechner und Prüfungen: Eingabe von Beginn (7:50 / 7:55 / 8:00 / frei), Stundenlänge (45 / 60 / frei; optional Länge je Stunde) und Pausen (Name, Minuten, „trennt Doppelstunden“); `period_times` wird berechnet, „Zeiten von Hand“ bleibt möglich; Live-Tabelle der Uhrzeiten (`POST /settings/period-times/preview`). Die Prüfung meldet überlappende Stunden (Beginn + Länge > nächster Beginn) und zu kurze Pausen; `core_latest_period` blockiert das Senken der Stundenzahl nicht mehr (wird angepasst, mit Hinweis); eine Pause „nach Stunde“ ist bis zur letzten Stunde zulässig (Server und Oberfläche gleich). Nutzer A-31: Schulbeginn, Stundenlänge, Pausen frei einstellbar.
Abnahme: Beginn 7:50, 45 min, Pausen 15/20 min → Tabelle zeigt korrekte Uhrzeiten ohne Handrechnung; Beginn 8:00 mit 60 min; Stunden, die sich überlappen, werden abgelehnt; Servertexte nennen keine Feldnamen.

**STA-053** · P1 · Status: Ist
Schultage und Unterrichtstage: Schultage der Schule (`school_days`) und je Klasse (`school_days`, nur `timetable.edit`) sind einzelne Wochentage (z. B. Mo–Fr oder Mo–Sa), bis 7 Tage, mit Namen für alle 7. Samstag/Sonntag erscheinen im Plan nur, wenn dort ein Termin liegt (STA-059); sonst schulfrei (schraffiert). Eine Änderung von Unterrichtstagen oder Zeitraster, die Stunden verlieren würde, liefert **409** mit Meldung und wird erst mit Bestätigung (`force=1`) übernommen, nachdem eine Vorschau der Stunden und gekoppelten Kurse zeigt, deren Bedeutung sich ändert. Stundenplan, Vertretung, Kalender und iCal nutzen dieselbe Liste. Eine Stunde findet nur statt, wenn die Wochenlogik zutrifft; Tage werden nur über die Unterrichtstage der Klasse geprüft.
Abnahme: Klasse auf Mo–Do setzen, obwohl freitags 4 Stunden liegen → 409 mit Zahl der betroffenen Stunden; nach Bestätigung entfallen sie; Tag 7 („Sonntag“) hat einen Namen in Modell, API und Oberfläche.

**STA-054** · P2 · Status: offen
Tageszeiten je Klasse (Nutzer A-69, 11.10.): „Beginn und Länge des Tages ergeben sich aus den Stunden der Klasse und sind pro Klasse einstellbar. Beispiel: Der Tag einer Abendklasse beginnt erst um 16 Uhr; eine normale Klasse hat morgens ihre erste Stunde. Jede Klasse hat ihre eigene ‚1. Stunde‘. Hat eine Lehrkraft früh Unterricht und später Abendklassen, wird das im eigenen Plan und überall sonst zeitlich richtig angezeigt.“ Bestand: nur ein globales Zeitraster; benötigt Zeitraster-Vorlagen je Klasse, Konflikte nach Uhrzeit, chronologische Lehrkraft- und Raumpläne.
Abnahme: Abendklasse mit Beginn 16:00 und Tagesklasse mit Beginn 08:00 → Lehrkraft-Plan zeigt beide Blöcke chronologisch mit Uhrzeiten; Konflikt wird nach Uhrzeit erkannt, nicht nach Stundennummer.

**STA-055** · P0 · Status: Ist
Wochenangaben und Zeitregeln (Kurse, Blöcke, Pausenaufsichten, Zeitregeln der Lehrkräfte und Klassen): Was nicht jede Woche gilt, hat `weeks` (Liste laufender Wochen, 1-basiert) **oder** `rhythm`; beides leer = jede Woche; ist ein Rhythmus gesetzt, werden `weeks` ignoriert. Rhythmus `{every, from_week, to_week}`: Woche w ist aktiv, wenn `from_week` ≤ w, (`to_week` = 0 oder w ≤ `to_week`) und (w − `from_week`) durch `every` teilbar ist; Standards bei fehlenden/ungültigen Werten: `every` 1 (auch bei Werten < 1), `from_week` 1 (auch bei 0), `to_week` 0 = offen; nicht lesbare Werte → Regel aktiv. Ist die laufende Woche unbekannt, gelten Regeln als aktiv. Zeitregel: `valid_week` > 0 und aktuelle Woche davor → Regel trifft nicht zu (`valid_week` = Montag der Woche von `valid_from`); eine Zeitregel trifft zu, wenn Gültigkeit, Wochenangabe, Tag (`days`) und Stunde (`periods`) passen; leere Listen = alle. Planzeitraum-Bereich eines Blocks: `from_week`/`to_week` (0 = offen) zusätzlich zu `weeks`/`rhythm`. Oberfläche: drei Modi „Jede Woche“, „Ausgewählte Wochen“ (Chips 1 bis N), „Rhythmus“, Tag-Chips, Textvorschau („Woche 1–2“); Rhythmus-Grenzen in Server und Oberfläche gleich (Bestand: 1–4 gegen 8); Warnung bei mehr als 8 Wochenvarianten.
Abnahme: Rhythmus `{every 2, from 3, to 0}` ist aktiv in Woche 3, 5, 7 …, nicht in 4; `every` 0 verhält sich wie 1; `weeks` [2,4] zusammen mit `rhythm` → `rhythm` gilt; Regel mit `valid_from` 15.01. wirkt nicht in KW 2.

**STA-056** · P1 · Status: Ist
Ferien und Feiertage pflegen (Recht `masterdata.edit`): von Hand anlegen, ändern, löschen; Art `ferien`, `feiertag`, `beweglich`, `schulfrei`; Zeitraum inklusive; an diesen Tagen kein Unterricht, Wochen zählen mit; Tagesköpfe in Plänen sind gekennzeichnet. Nutzer 10-11: Schulen definieren Feiertage und freie Tage selbst.
Abnahme: Eintrag „Brückentag“ als `schulfrei` an einem Freitag → Plan zeigt den Tag als frei, Termin-/Klausurprüfung meldet „kein Schultag“.

**STA-057** · P1 · Status: Ist
Ferien-/Feiertagsimport (Planung → Einstellungen → „Zeitraster & Schuljahr“; Recht `masterdata.edit`): Quelle OpenHolidays (kostenlos, ohne Schlüssel, Länder und Regionen), Fallback Nager.Date (nur gesetzliche Feiertage, ohne Regionen); Land und Bundesland wählbar (aus den Schuldaten vorbelegt); Schaltfläche „Vorschau“ zeigt je Eintrag die Aktion (neu, geändert, schon da, von Hand geändert); „Jetzt übernehmen“; Schalter „Jedes Schuljahr automatisch übernehmen“ → täglicher Abruf für das aktuelle und das nächste Schuljahr. Von Hand angelegte, geänderte oder gelöschte Einträge werden nie überschrieben oder zurückgeholt; nichts wird automatisch gelöscht. Importierte Einträge tragen `source`/`source_sig`. Die Anfrage an die öffentliche Schnittstelle sendet nur Land, Region und Zeitraum; der Produktname in der Anfragekennung stammt aus der zentralen Konfiguration. Nutzer 10-12: „Import per freier Schnittstelle, Land und Bundesland wählbar, Vorschau, ‚jetzt übernehmen‘, jährlich automatisch; eigene Einträge werden nie überschrieben.“
Abnahme: Vorschau für NRW listet neue Einträge; „Jetzt übernehmen“ legt sie an; Eintrag von Hand umbenennen, erneut übernehmen → Name bleibt; Ausfall der Hauptquelle → Fallback liefert gesetzliche Feiertage; ohne `masterdata.edit` → 403.

**STA-058** · P2 · Status: offen
Ferienimport-Ausbau: „Zurücksetzen“ für von Hand gelöschte Ferien; Feiertagsnamen in deutscher Sprache (Nager.Date liefert Landessprache, z. B. Japanisch); Ferienvorlagen je Bundesland als Datei mit Quellenangabe (mindestens NRW 2026/27 und 2027/28) und Import aus iCal/CSV; Qualitätsbericht warnt, wenn keine Ferien eingetragen sind; Browser-Prüfung des Imports.
Abnahme: Von Hand gelöschte „Herbstferien“ lassen sich per „Zurücksetzen“ wiederholen; ein japanischer Feiertagsname wird deutsch angezeigt; Schuljahr ohne Ferien → Warnung im Bericht.

**STA-059** · P1 · Status: Ist
Termin-Maske in den Stammdaten: Termine (Ferien, Feiertage, Test, Klausur/Arbeit, Hausaufgabe mit Frist, Schultermin) sind dort pflegbar und erscheinen im Kalender/Plan der Betroffenen; Schultermine am Wochenende sind möglich (Samstag/Sonntag werden dann im Plan sichtbar, Schüler/innen sehen, ob sie am Wochenende irgendwohin müssen; `pflicht` hebt Anwesenheitspflicht hervor). Teilnehmende Lehrkräfte gelten für die Vertretung als belegt. Nutzer 10-11: Feiertage und freie Tage selbst definieren; Wochenend-Termine (z. B. Schultermin am Samstag) möglich. [unklar: Ablage der Hausaufgabe mit Frist (Aufgabe im Kursraum vs. Termin)].
Abnahme: Termin „Schulfest“ Samstag 10–14 Uhr, Klassenstufe 5, `pflicht` → erscheint nur in Plänen der 5. Klassen und ihrer Eltern, am Samstag sichtbar; Termin ohne `title` → 422.

**STA-060** · P2 · Status: offen
Schulkalender-Ausbau: Kalender (Monat, Woche, Liste) je Rolle mit Ferien, Terminen und Klausuren; Termine mit Zielgruppe Schule, Klassen, Klassengruppen, Jahrgänge, Lehrkräfte und Art Pflicht/freiwillig/Info; Sekretariat und Schulleitung legen sie an, Lehrkräfte für ihre eigenen Klassen; Eltern sehen die Termine der Klassen ihrer Kinder; `GET /calendar?from&to` liefert Samstag/Sonntag nur bei Terminen; Kalender-Abo (iCal) enthält Termine und Ferien, Eltern erhalten je Kind einen Feed (Bestand: nur das erste Kind); Vertretung: Termine mit Lehrkräften = belegt, Klassentermine = „Klasse nicht im Haus“.
Abnahme: Eltern zweier Kinder abonnieren zwei getrennte iCal-Feeds mit den jeweiligen Klassenterminen; Lehrkraft legt Termin für fremde Klasse an → 403.

### 1.6 Einrichtung einer neuen Schule

**STA-061** · P1 · Status: Ist
Einrichtung von Null: „Selbst anlegen ist der Hauptweg.“ Der Import ist in jedem Schritt nur eine Alternative und nie Pflicht („dass man quasi nicht importieren muss, sondern nur kann“). Beim Aufsetzen einer neuen Schule sollen ganze Datensätze-Sätze („Sets“) auf einmal anlegbar sein, „und dass das ein bisschen reibungsloser ist“ (Nutzer 10-16). Der Ablauf folgt der festen Reihenfolge nach Abhängigkeiten (STA-062).
Abnahme: Eine leere Instanz lässt sich vollständig ohne eine einzige Importdatei bis zum fertigen Stundenplan einrichten; jeder Schritt zeigt „Importieren“ als Alternative, nie als Pflicht.

**STA-062** · P1 · Status: Ist
Feste Schrittfolge (nicht umstellbar, spätere Schritte verweisen auf frühere):

| Nr | Schritt | Inhalt / Abhängigkeit |
|---|---|---|
| 0 | Administration sichern | Erst-Administrator, Passwortwechsel (STA-068) |
| 1 | Lizenz | nur Produktivbetrieb; ohne gültige Lizenz nur Begrüßungsseite/Administration (Datei BET) |
| 2 | Schuldaten und Standorte | Name, Schulform, Bundesland, Adresse, Kontakt, Logo; Standorte |
| 3 | Schuljahr und Ferien | Beginn automatisch/eigen, Halbjahre, Ferienimport (Bundesland aus Schuldaten) |
| 4 | Zeitraster | Beginn, Länge, Pausen, Unterrichtstage |
| 5 | Fächer | Kürzel, Name, Raumtyp, Hauptfach, Farbe |
| 6 | Räume | gehören zu einem Standort |
| 7 | Jahrgänge und Stundentafeln | brauchen die Fächer |
| 8 | Lehrkräfte | brauchen die Fächer |
| 9 | Klassen | wählen Klassenraum, Klassenleitung und Jahrgang aus dem vorher Angelegten |
| 10 | Schüler/innen | optional |
| 11 | Kurse | aus Stundentafeln erzeugen (STA-032) und Sonderzuschnitte von Hand |
| 12 | Stundenplan | Generator (Datei STP) |
| 13 | Konten | Massenanlage und Zugangsbriefe (STA-074) |
| – | ergänzend | Rechte (Standardrechte), E-Mail-Versand mit Testmail, Schulkonto/SSO (optional), Impressum und Datenschutz (STA-072) |

Begründung (Nutzer 10-16: „Soll man zuerst Klassen definieren müssen und dann Klassen, Klassenräume und dann Klassen definieren?“): Räume gehören zu einem Standort, Lehrkräfte und Stundentafeln brauchen Fächer, Klassen wählen Raum, Leitung und Jahrgang aus dem Angelegten. Die Zahl der Schritte ist nicht normativ [unklar: Bestand nennt 12 bzw. 13 Schritte].
Abnahme: Der Schritt „Klassen“ bietet nur bereits angelegte Räume, Lehrkräfte und Jahrgänge zur Auswahl; ein Raum ohne Standort wird abgewiesen; Lehrkraft mit unbekanntem Fach → 422.

**STA-063** · P1 · Status: Ist
Verhalten des Assistenten (`/einrichtung`, Menü „Schule einrichten“, später in der Verwaltung „Einrichtung fortsetzen“): Schritt-Navigation in Gruppen mit Fortschrittsanzeige; Stand je Schritt (offen/erledigt); kleines „i“ (Hilfetext) und Direkt-Button zur Zielseite je Schritt; der Schulname ist direkt im Assistenten eingebbar. Eine neue leere Schule führt den Admin automatisch in den Assistenten; bis zum Abschluss zeigt ein Hinweisband die Einrichtung an; die Startseite einer leeren Schule zeigt die nächsten Einrichtungsschritte statt Nullen. Der Assistent führt zum ersten offenen Schritt, vor und zurück ist möglich. **Jeder Schritt ist überspringbar**; der Stand bleibt beim Neuladen erhalten (serverseitig; nicht gespeicherte Tabelleneingaben nur im Browser mit Hinweis „lokaler Entwurf“). Abschließen und Wieder-Öffnen sind möglich; die Abschluss-Zusammenfassung nennt Fehlendes; der Abschluss ist nicht an Vollständigkeit gebunden [unklar: Bestand offen]. Nutzer 10-12: Setup-Assistent mit „Schritte mit Status (erledigt/offen), kleines ‚i‘, Direkt-Button je Schritt, Schulname direkt eingebbar“.
Abnahme: Neue Instanz → Erst-Admin landet automatisch auf `/einrichtung`; Seite neu laden → Stand unverändert; Schritt „Räume“ überspringen und später über „Einrichtung fortsetzen“ öffnen; „Abschließen“ mit offenen Schritten zeigt die Liste des Fehlenden.

**STA-064** · P1 · Status: Ist
Tabelleneingabe in allen Listen-Schritten (Fächer, Räume, Jahrgänge, Lehrkräfte, Klassen, Schüler/innen, Kurse): mehrere Einträge werden wie in einer Tabelle getippt; die Eingabetaste erzeugt die nächste Zeile; Einfügen aus Tabellenkalkulation, Textverarbeitung oder CSV (Trennzeichen wird erkannt); Serien wie „5a–5d“ oder „Raum 101–120“ werden ausgeschrieben; Anlage über `POST /setup/bulk/{sammlung}`; Ja/Nein-Felder akzeptieren gängige Wörter; Obergrenze Zeilen je Vorgang [unklar: Wert].
Abnahme: „5a–5d“ in der Klassentabelle erzeugt vier Zeilen; Einfügen von 40 Zeilen aus einer Tabellenkalkulation erzeugt 40 Zeilen; „Raum 101–120“ erzeugt 20 Räume.

**STA-065** · P1 · Status: Ist
Fehlerbehandlung der Sammel-Anlage: eine fehlerhafte Zeile wird rot markiert, dann wird **nichts** gespeichert (kein halber Stand; alles oder nichts, Fehler je Zeile mit Klartext); lange Fehlertexte brechen in der schmalen Tabelle um statt abgeschnitten zu werden.
Abnahme: 20 Zeilen, Zeile 7 mit unbekanntem Standort → Zeile 7 rot mit vollständigem Text, Datenbestand unverändert; nach Korrektur werden alle 20 gespeichert.

**STA-066** · P0 · Status: Ist
Rechte und Schnittstellen der Einrichtung: Schritte lesen/ändern, Status lesen, Abschließen/Wieder-Öffnen verlangen `settings.edit` und `users.manage` [unklar: beide oder eines]; Schulprofil lesen/ändern `settings.edit`; Sammel-Anlage je Sammlung `masterdata.edit` und `timetable.edit`; Ferienimport `masterdata.edit` (im Assistenten zusätzlich `settings.edit`); Testmail `settings.edit` [Missbrauchsschutz bei frei wählbarem Empfänger unklar]; Schullogo abrufen ohne Anmeldung, hochladen mit Einrichtungsrecht; Demo laden `system.admin`. Schnittstellen: `GET /setup/status`, `PUT /setup/steps/{key}`, `POST`/`DELETE /setup/finish`, `GET`/`PUT /setup/profile`, `POST /setup/bulk/{collection}`, `POST /setup/holidays`, `POST /setup/test-mail`, `GET /school-logo`.
Abnahme: `sekretariat` ohne `settings.edit` ruft `PUT /setup/profile` → 403; ohne Anmeldung ist `GET /school-logo` 200, jede andere Schnittstelle 401.

**STA-067** · P1 · Status: Ist
Schulprofil: Name, Schulform, Bundesland, Adresse, Kontakt, Logo (gespeichert im Zustandsspeicher `system_state` unter `school_profile`; keine Freitexte über Personen). Logo-Upload mit Prüfung von Größe und Dateityp [unklar: Grenzen]; das Logo ist ohne Anmeldung abrufbar, andere Schuldaten nicht. Der Platzhalter-Schulname „Meine Schule“ gilt als „nicht eingerichtet“; der Schritt gilt erst nach Änderung als erledigt. Das Bundesland steuert die Vorbelegung des Ferienimports. Das Logo erscheint auf Anmeldeseite und in Briefen (offen, Bestand: gespeichert, nicht eingebunden).
Abnahme: Logo mit nicht erlaubtem Dateityp → 422; Schulname unverändert „Meine Schule“ → Schritt bleibt „offen“; Bundesland „NRW“ vorbelegt im Ferienimport.

**STA-068** · P0 · Status: Ist
Erst-Administrator: Ist noch kein Administrator vorhanden, legt der Start einen Erst-Administrator mit einmaligem Passwort an; das Passwort steht nur in einer Datei im Datenordner, die nur der Betreiber lesen kann, und die Datei wird gelöscht, sobald ein Administrator sein Passwort ändert; beim ersten Anmelden ist ein neues Passwort Pflicht. Notfall-Befehle (nur Betreiber mit Serverzugang): Administrator anlegen, Passwort zurücksetzen, Konto entsperren, Zwei-Faktor eines Kontos deaktivieren, Konten auflisten, Konfiguration prüfen (`check-config`). Offen (Entscheidung E7): Einrichtungslink mit Ablauf statt Einmalpasswort im Log/Datei.
Abnahme: Frische Instanz → genau ein Konto `admin`, Anmeldung mit Einmalpasswort erzwingt Passwortwechsel, danach existiert die Passwortdatei nicht mehr; Protokoll enthält das Passwort nicht.

**STA-069** · P2 · Status: offen
Schule von Null: Eine leere Instanz enthält nur das Admin-Konto und den Einrichtungsassistenten, keine Demo-/Beispieldaten. Der Betreiber will den Durchlauf selbst erleben („dass ich quasi von null auf die Schule aufsetze“); der Durchlauf durch den Betreiber steht aus. Ob die Hauptinstanz wieder komplett geleert wird (Angebot), ist nicht entschieden. Prüfungen offen: Browser-Prüfung der Fehleranzeige in der Einrichtungstabelle; protokollierter Rundgang „Beispielschule Berufskolleg in unter 60 Minuten ohne Entwicklerwissen“; Schritt-Anzeige und Karten am Handy.
Abnahme: Rundgang mit Berufskolleg-Beispiel: Zeitmessung ≤ 60 Minuten ohne Eingriff in Dateien oder Befehle; Protokoll liegt vor.

**STA-070** · P2 · Status: Ist
Vorschläge: Der Assistent bietet übliche Fächer und ein Zeitraster als Vorschläge an, übernehmbar oder änderbar (nie voreingetragen).
Abnahme: „Übliche Fächer übernehmen“ legt die gewählten Fächer an; abgewählte Vorschläge erscheinen nicht; Zeitraster-Vorschlag lässt sich vor dem Speichern ändern.

**STA-071** · P2 · Status: offen
Vorlagen und Direktimporte: Zeitraster-Vorlagen je Schulform (z. B. Gymnasium 45 Minuten), Stundentafel-Vorlagen je Bundesland und Schulform; Beispielschulen (Gymnasium, Gesamtschule, Berufskolleg NRW) als wählbare Startvorlage und tatsächlich importierbar (Bestand: nur als Dokument, Datei nicht importierbar); Direktimport in Originalformaten (SchILD-XML/SVWS, ASV-XML, LUSD-Datei, OneRoster); Moodle-Nutzerlisten nur mit abgeschalteter Spalte „id“ (sonst Moodle-Nummern als IDs).
Abnahme: Auswahl „Gymnasium NRW“ legt Zeitraster und Beispiel-Stundentafeln als Vorschlag an; Import einer SchILD-NRW-Originaldatei ohne CSV-Umweg liefert Probelauf mit Zählwerten.

**STA-072** · P1 · Status: Ist
Einrichtungsschritt „Impressum und Datenschutz“: eigener Schritt; gilt erst als erledigt, wenn in den Texten keine eckigen Platzhalter mehr stehen. Die Texte der Schule liefert die Schule/der Betreiber (technisch fertig, Texte offen).
Abnahme: Text mit „[Name der Schule]“ → Schritt bleibt „offen“; nach Ersetzen aller `[…]` → „erledigt“.

**STA-073** · P1 · Status: Ist
Import als optionale Alternative (Details Datei INT): CSV mit Vorlagen SchILD-NRW, ASV, LUSD, Magellan oder eigenes Zuordnen; Untis GPU (ZIP); JSON-Vollsicherung mit Integritätsprüfung; jedes mit Probelauf (`dry_run`: nichts wird gespeichert), unveränderte Elemente werden nicht neu geschrieben, Rücknahme entfernt alles, was der Lauf angelegt hat. Regeln für die Einrichtung: Lehrkräfte-CSV mit Kürzel, Name, Fächer, Deputat, E-Mail (Arbeitszeit-Raster nicht im CSV); Schüler-CSV Pflicht Klasse (muss vorher existieren), Nachname, Vorname, ID aus Schülernummer (fehlt sie: aus Name+Klasse), Geburtsdatum wird nur ergänzt, nie überschrieben; Spalte Konfession/Religionsunterricht ordnet in die Religions-Kopplung ein; Listen in CSV-Spalten werden nur an „,“, „;“, „|“ getrennt; Untis-Import verliert Sperrzeiten, Arbeitsraster, Pausen, Stundentafeln, Termine, Aufsichten, Jahrgang (Probelauf warnt); JSON-Teilimport zeigt `would_delete`/Gefahr; Moodle-Kurse sind keine Fächer, Moodle-Einschreibungen nicht importierbar.
Abnahme: Schüler-CSV mit Klasse „9z“, die nicht existiert → Zeile mit Nummer abgelehnt, alles oder nichts; erneuter Import derselben Datei ändert nichts; Import mit anderem Geburtsdatum überschreibt vorhandenes nicht.

**STA-074** · P1 · Status: Ist
Einrichtungsschritt „Konten“: Massenanlage je Rolle (Lehrkräfte, Schüler/innen, Eltern; Startpasswort erzeugt, mit den Stammdaten verknüpft), besondere Rollen einzeln (Schulleitung, Abteilungsleitung, Sekretariat, Planung, Hausmeister, Schulbegleitung mit Schüler-Zuordnung, Zuschauer). Zugangsbriefe als Stapel je Auswahl (Konten bzw. Schüler mit Eltern): Sammel-PDF, ZIP mit Einzelbriefen, Versand per E-Mail; Stapel gelten 60 Minuten (`SM_LETTER_BATCH_MINUTES`) und nur für die erstellende Person (oder `admin`), danach Fehler 410; ein neuer Stapel setzt neue Startpasswörter; Brief enthält Benutzername, Startpasswort (14 Tage gültig) und QR-Code zur Anmeldeseite; erste Anmeldung verlangt ein eigenes Passwort. Offen: Einmal-Anmeldelink statt Startpasswort (Datei FOR/ANM).
Abnahme: Stapel für Klasse 5a → Sammel-PDF mit Briefen; nach 61 Minuten → 410; anderes Konto ohne `admin` → 404; erster Login mit Startpasswort erzwingt Passwortwechsel.

**STA-075** · P2 · Status: Ist
Dokumentation „Eine neue Schule einrichten“ als Hilfeinhalt (Sie-Form): Voraussetzungen (laufende Instanz mit Erst-Administrator, Lizenz, Schuljahresbeginn = Montag der ersten Schulwoche, Zeitraster, Listen als CSV, Unterrichtskonzept auf Papier), Reihenfolge der Abhängigkeiten, Pflichtdaten, Import, Generator-Regeln, Prüfung, Zugänge verteilen, typische Fehler; laufendes Beispiel: fiktive Schule nach Montessori-Art (12 Lerngruppen, 250 Kinder, 42 Pädagog/innen, 2 Standorte, Abendschule). Nutzer 10-12: „ich will, dass du den ganzen Prozess dokumentierst, wie man sowas macht und was benötigt wird.“
Abnahme: Das Hilfecenter enthält die Anleitung mit allen genannten Abschnitten; ein Prüfdurchlauf nach der Anleitung auf leerer Instanz endet mit lauffähigem Stundenplan.

**STA-076** · P2 · Status: offen
Konfigurationsdateien (Schulvorlage übertragen): Export der Schulstruktur mit oder ohne Personen als ZIP (`manifest.json`, `LIESMICH.txt`, je Bereich eine Excel-taugliche CSV: Standorte, Fächer, Räume, Bildungsgänge, Klassen, Klassengruppen, Abteilungen, Lehrkräfte [Verfügbarkeit als lesbarer Text], Schüler/innen mit Erziehungsberechtigten [nur mit Recht], Stundentafeln, Kopplungen, Ferien, Aufsichtsbereiche, `einstellungen.json`); ohne Personen enthält das ZIP keine Namen, E-Mails oder Geburtsdaten; Import mit Probelauf je Bereich (neu, geändert, unverändert, würde gelöscht, Fehler mit Zeilennummer), feste Reihenfolge, ganz oder gar nicht, eine Version im Verlauf; leere Vorlage je Bereich mit Beispielzeile; jeder Stammdaten-Reiter bietet „Als Datei“ und „Aus Datei“.
Abnahme: Rundlauf mit der Berufskolleg-Beispielschule: Export, leere Instanz, Import → identischer Bestand; Export ohne Personen enthält keine personenbezogenen Daten (Stichprobe auf Namen, E-Mails, Geburtsdaten).

### 1.7 Schuljahreswechsel

**STA-077** · P1 · Status: Ist
Assistent „Schuljahreswechsel“ (`/schuljahreswechsel`, Schulleitung und Administration): Vorgaben: Bezeichnung des neuen Schuljahres, Schuljahresbeginn (wird vorgeschlagen), je Klasse eine Aktion (Schalter): **hochstufen** (Klassenstufe +1, Klassenname mit Zahl fortgeschrieben), **Abgänger austragen** (Abschlussjahrgang oder einzelne Schüler/innen), **neue Klasse anlegen** (mit eigenen Angaben); Ausnahmen je Klasse; Optionen: Kursräume archivieren, Notenbücher abschließen, Stundenplan leeren. Liste der bisherigen Läufe. Hinweis „Vorher eine Sicherung erstellen“.
Abnahme: Klasse 5a „hochstufen“ → Vorschau zeigt „6a“; Abschlussklasse „Abgänger austragen“ → alle Schüler/innen in der Abgänger-Liste; Konto ohne Recht → 403.

**STA-078** · P1 · Status: Ist
Vorschau vor Ausführung: zeigt je Klasse die geplante Änderung, die Abgänger-Liste, gesperrte Konten, archivierte Kursräume, abgeschlossene Notenbücher und neue Klassen; es wird nichts geändert. **Ausführen ist nur mit vorheriger Vorschau möglich** und an deren Stand gebunden; ändert man die Vorgaben, wird die Vorschau ungültig.
Abnahme: Ausführen ohne Vorschau → abgewiesen; Vorgabe nach Vorschau ändern → „Ausführen“ gesperrt bis neue Vorschau; Vorschau verändert den Datenbestand nicht (Versionsnummer gleich).

**STA-079** · P0 · Status: Ist
Wirkungen des Ausführens: Klassen hochgestuft; Abgänger aus dem Planungsstand entfernt, ihre Konten **gesperrt** (Sitzungen enden), Eltern-Konten nur gesperrt/ausgetragen, wenn sie kein weiteres Kind haben; neue Klassen angelegt; Kursräume archiviert (bleiben lesbar); Notenbücher abgeschlossen; neues Schuljahr gesetzt (alter Beginn in `school_year_history`; optional Stundenplan geleert); Ferien und Planzeiträume werden mit dem neuen Schuljahr verschoben bzw. neu berechnet. Jeder Lauf wird protokolliert (Zustandsspeicher `yearchange`, Audit ohne Inhalte); die Zahl gespeicherter Läufe ist begrenzt [unklar: Wert]. Danach: neue Schüler/innen importieren und Stundenplan neu erzeugen.
Abnahme: Nach Ausführen sind Konten der Abgänger gesperrt und angemeldete Sitzungen beendet; Eltern mit weiterem Kind bleiben aktiv; archivierter Kursraum bleibt lesbar; Audit enthält den Lauf ohne Namen der Personen.

**STA-080** · P1 · Status: Ist
Rückgängig des Schuljahreswechsels: ganz oder gar nicht (kein Teil-Rückgängig); nur, solange der Plan nicht weiter geändert wurde. Abgänger stehen danach wieder im Planungsstand, ihre Konten werden entsperrt, die Personen werden beim nächsten Abgleich aus der Löschwarteliste entfernt; eine mittendrin gescheiterte Löschung lässt sich neu starten. Nach der nächsten Planänderung ist Rückgängig nicht mehr möglich.
Abnahme: Ausführen, sofort Rückgängig → Klassenstufen, Zuordnungen, Konten-Sperren und Kursräume wie vorher; nach einer Stundenverschiebung → „Rückgängig“ abgelehnt mit Klartext.

**STA-081** · P0 · Status: Ist
Rechte und Schnittstellen des Schuljahreswechsels: Vorschau, Ausführen, Läufe, Rückgängig verlangen `settings.edit`, `masterdata.edit` und `users.manage` [unklar: alle drei oder eines; Bestand: Schulleitung und Administration]; `POST /year-change/preview`, `POST /year-change/execute`, `GET /year-change/runs`, `POST /year-change/undo`.
Abnahme: Konto mit nur `masterdata.edit` ruft `POST /year-change/execute` → 403; Schulleitung → 200 (mit gültiger Vorschau).

**STA-082** · P1 · Status: offen
Hochstufen-Regel: Fortschreibung des Klassennamens („5a“ → „6a“, „11a IT“ → „12a IT“, aus dem Namensmuster) ist festgelegt und prüfbar; die Jahrgangszuordnung folgt (Bestand: Klassenstufe wird angehoben, der Jahrgang bleibt stehen = Widerspruch): Eine hochgestufte Klasse erhält den passenden Folgejahrgang (z. B. „5 Informatik“ → „6 Informatik“), existiert keiner, meldet die Vorschau dies. Profil-Felder werden im CSV-Rundlauf und beim Jahreswechsel geprüft.
Abnahme: Klasse 5a im Jahrgang „5“ → nach Lauf Klasse 6a im Jahrgang „6“; fehlt „6“, nennt die Vorschau „kein Folgejahrgang“ und blockiert nicht.

**STA-083** · P2 · Status: offen
Ausbau des Jahreswechsels: Aktion je Klasse versetzen/wiederholen/abschließen/belassen (Vorschlag versetzen; abschließen im Abschlussjahrgang des Bildungsgangs); einzelne Wiederholer/Abgänger markieren; leere Eingangsklassen je Bildungsgang; Klassenleitungen übernehmen ja/nein; Kurse und Stundentafel automatisch fortschreiben (Stundentafel-Kurse für das neue Jahr neu erzeugen, manuelle Kurse wahlweise behalten), Oberstufen-Kursphasen; Zeugnisdaten und Abschlussnoten der Abgänger archivieren (Export); Test des Anschlusses an das Löschkonzept mit echter Warteliste; ein Eintrag im Verlauf, das alte Schuljahr bleibt lesbar.
Abnahme: Probelauf mit Beispielschulen Gesamtschule und Berufskolleg: Klassenkürzel bleiben stabil, Kurse/Kursräume/Richtlinien bleiben gültig, Wiederholer verbleibt im Jahrgang, Abgänger-Klassen sind archiviert.

**STA-084** · P1 · Status: offen
Atomarität des Jahreswechsels: Ausführen und Rückgängig laufen in einem Ablauf mit Rollback; das Protokoll entsteht in derselben Transaktion; nach erzwungenem Fehler mittendrin ist der Bestand unverändert.
Abnahme: Test mit erzwungenem Fehler beim 3. Schritt → Datenbestand identisch zum Zustand vor dem Lauf, kein Protokolleintrag „ausgeführt“.

**STA-085** · P0 · Status: Ist
Abgänger und Löschkonzept: Personen, die nicht mehr im Planungsstand stehen, kommen im stündlichen Wartungslauf auf die Warteliste `retention_leavers` (`student_id` eindeutig, `status` wartend|erledigt, `source` planung|abgleich, `name_enc` verschlüsselt und bei Abschluss geleert, `class_id`, `purged`, `done_at`); ihre Konten sind gesperrt; Wartefrist mindestens 30 Tage, danach Löschung nach Fristen je Datenart (Datei DAT). Ein leeres Schülerverzeichnis wird nie als „alle ausgetreten“ gewertet. Wer in den Planungsstand zurückkehrt, wird automatisch von der Warteliste genommen und entsperrt.
Abnahme: Schüler aus Stammdaten löschen → nach dem nächsten Wartungslauf steht er als „wartend“ mit verschlüsseltem Namen; leere Schülerliste importieren → keine Masseneinträge; Rückkehr der Person → Eintrag verschwindet, Konto entsperrt.

### 1.8 Beispielschule, Demo, Mengengerüst

**STA-086** · P2 · Status: Ist
Beispielschule (nur erfundene Daten, keine echten personenbezogenen Daten): rund 2.600 Schüler/innen, rund 170 Lehrkräfte, 2 Standorte; Fächer mit Farben, Lehrpläne, Doppelstunden, Fächerkombinationen, erfundene Vor- und Nachnamen; Leistungskurs-/Grundkurs-Bereiche; Abendunterricht mit eigenen Zeiten, Klassen und Lehrplan. Größenvarianten: klein für Tests (je Jahrgang 2 Klassen) und groß (99 Klassen, 2.644 Schüler/innen, 169 Lehrkräfte, 1.554 Unterrichtsstunden, 5.462 Konten; gemessen: Datenbank 3,3 MB, Dateien 0,8 MB). Demo-Konten für alle Rollen mit erkennbarem festem Kennungs-Präfix [Wert legt der Neubau fest], u. a. Schüler/in minderjährig, Schüler/in volljährig, Eltern, Demo-Kind mit Nachteilsausgleich und eines mit Schulbegleitung. Beispieldaten nutzen nur Platzhalter-Domains (`schule.example.org`, Test-Mails nur an `example.org`) und Platzhalter-Namen („Frau Muster“). Beispieltermine liegen nie in Ferien oder auf Wochenenden. Die Demo legt erfundene Benachrichtigungen für die Glocke an.
Abnahme: Laden der kleinen Demo erzeugt je Jahrgang 2 Klassen; sämtliche E-Mail-Adressen der Demo enden auf `example.org`; Test „Beispiel-Klassenarbeit anlegen“ scheitert nicht an Ferien.

**STA-087** · P0 · Status: Ist
Demo laden nur außerhalb des Echtbetriebs: `POST /admin/demo` nur mit Umgebungsvariable `SM_LOAD_DEMO=1` und Recht `system.admin`; in Produktion (`SM_MODE=production` bzw. `SM_ENV=production`) ist „Demo laden“ ausgeblendet und die Schnittstelle liefert 403; außerhalb der Produktion verlangt sie die Eingabe des Schulnamens; „Demo-Konten anlegen“ ist standardmäßig aus; Demo-Passwort nur über `SM_DEMO_PASSWORD`, nie im Protokoll; in Produktion werden Konten mit Demo-Passwort beim Start gesperrt und im Systembereich gemeldet. Betriebsmodus `SM_MODE` ∈ {production, demo, development}; der Start bricht im Echtbetrieb mit klarer Liste ab bei fehlendem Secret/Verschlüsselungsschlüssel, nicht-https-Adresse, Beispielpasswörtern, Platzhaltern, aktivem Demo-Schalter.
Abnahme: Mit `SM_MODE=production` → `POST /admin/demo` 403 und kein Menüeintrag; Start mit Beispielpasswort bricht ab; ein Demo-Passwort-Konto ist nach Start gesperrt.

**STA-088** · P0 · Status: offen (Ist: Sperre erkennt nur wahre Werte)
Schutz der öffentlichen Demo (`SM_DEMO_PUBLIC=1`): Allowlist statt Blocklist – nur ausdrücklich erlaubte Methoden und Pfade; unsichere Methoden (Schreiben) gesperrt, außer ausdrücklich erlaubt (z. B. im Kompetenzbereich nur Bewertungen, eigene Einträge, Pläne, Änderungen von Verknüpfungen); neue Schreibwege sind zunächst gesperrt; Änderungen an außenwirksamen Einstellungsfeldern (Versand-, Kontaktfelder) sind gesperrt, und die Prüfung vergleicht mit dem **aktuellen Wert** (die Oberfläche sendet Einstellungen komplett zurück) und erkennt **jede** Änderung, auch auf 0, falsch und leeren Text; Zuschauer-Rolle schreibgeschützt; Demo-Konten nach Reset gesperrt [unklar: bis zum nächsten Reset oder dauerhaft].
Abnahme: In der öffentlichen Demo `PUT /settings` mit `sick_phone` von „123“ auf leer → abgewiesen; mit `webhooks` von [x] auf [] → abgewiesen; unveränderte Rückgabe aller Felder → erlaubt; Zuschauer-Konto `POST` irgendwo → abgewiesen.

**STA-089** · P1 · Status: offen
Mengengerüst: Das System arbeitet mit rund 2.500 Schüler/innen, einigen hundert Lehrkräften (Planung: 300), 99 und mehr Klassen und zwei Standorten ohne Funktionseinbuße; Stoßzeit 7:30–8:00 Uhr mit 2.500 Schüler/innen und 300 Lehrkräften, 95 % der Anfragen unter 500 ms (Lasttest, Datei QUA). Bestand: Generator nur mit kleiner Demo getestet, Lasttest fehlt.
Abnahme: Lasttest mit der großen Demo (2.644 Schüler/innen) erreicht die 95 %-Marke unter 500 ms; Speichern/Laden des Planungsstands bleibt praktisch unverändert (Verschlüsselung < 1 ms).

### 1.9 Weitere offene und gewünschte Dinge

**STA-090** · P3 · Status: offen
Klassenprinzipien als **Option, nie Standard** (Nutzer 10-11: „soll garantiert nicht der Standard sein“; „dass solche Klassenprinzipien erstellt werden können“): jahrgangsübergreifende/gemischte Klassen (Mischgruppen; Bestand nur Workaround, Notbehelf Mittelwert des Jahrgangs); Sonderstunden für Einzelne (z. B. Klassensprecher: extra Stunde wöchentlich, monatlich oder an bestimmten Tagen, von Schülersprecher bzw. Schule individuell setzbar); pro Schüler festlegen, ob die ganze Klasse etwas macht oder Schüler Sonderstunden erhalten; Förderung pro Person (eine Person braucht Mathe, eine andere Deutsch); Schulprinzip „schlechteste Noten bekommen mehr Unterricht“; Lerngruppen aus verschiedenen Klassen; weitere Prinzipien recherchieren und vorschlagen („Man kann vielleicht noch andere Prinzipien raussuchen.“). Konzept nicht erstellt.
Abnahme: Ist die Option ausgeschaltet (Standard), erscheinen keine Mischgruppen/Sonderstunden in Oberfläche und Plan; eingeschaltet lässt sich eine Lerngruppe aus Schüler/innen zweier Klassen mit eigenem Stundenanteil anlegen und planen.

**STA-091** · P3 · Status: offen
[unklar] Nutzerhinweis zu „Mugs“ und Fächern mit Schrägstrich (z. B. „Mu/Ku“) in den Stammdaten (Fächer) vom 10-12 wurde nicht verstanden; Beispiel fehlt, Rückfrage unbeantwortet. Hauptfach und Raumtyp bei solchen Fächern bleiben zurückgestellt. Der Neubau erlaubt Schrägstriche in Fachnamen und -kürzeln, soweit die Kennungsregel (STA-024) es zulässt; Klärung mit dem Betreiber vor Umsetzung.
Abnahme: Fach „Mu/Ku“ lässt sich als Name anlegen; das Kürzel folgt der Kennungsregel; Rückfrage an den Betreiber ist dokumentiert.

**STA-092** · P2 · Status: offen
Module ein/aus: Funktionsbereiche (z. B. Notenbuch, Klassenbuch, Raumbuchung) lassen sich je Schule ein- und ausschalten (Marktreife-Punkt „Module ein/aus“, Backlog B-56). Ausgeschaltete Module erscheinen weder im Menü noch in der API; Daten bleiben erhalten.
Abnahme: Modul „Notenbuch“ ausschalten → Menüpunkt weg, `GET /gradebook/…` → 404, Daten nach Wiedereinschalten vorhanden.

**STA-093** · P2 · Status: offen
Stammdaten-Rest aus dem Review: Kursassistent mit Teilnehmerübersicht und Zuteilungsvorschau mit Rückgängig; Raumtyp-Verwaltung (STA-034); Setup-Stepper am Handy; Karten statt Tabellen unter 600 px bei mehr als 5 Spalten; Entwürfe in Planung und Einstellungen gehen beim Reiterwechsel nicht verloren; „Fächertabelle“ bei 390 px ohne inneren Seitenscroll-Zwang.
Abnahme: Kursassistent zeigt vor dem Übernehmen eine Teilnehmerliste je Kursteil; „Rückgängig“ stellt die vorige Zuteilung her; Tabelle mit 7 Spalten wird bei 390 px zu Karten.

**STA-094** · P1 · Status: offen
Klassengruppen, Klassentypen, Bildungsgänge (Backlog B-14/B-19, Pflicht-Rückmeldung A-43/A-38): Klassentypen anlegen und löschen (Löschen mit Verweisprüfung); Bildungsgänge (Name, Kurzname, Jahrgänge, Abschlussjahrgang, Namensmuster); Klassengruppen (feste Klassen oder Regel „Bildungsgang × Jahrgänge“, wandert beim Jahreswechsel mit; Beispiele „Abi-Klassen“, „IT-Zweig 11–13“, Fach-Abi, Nachhilfe) gelten überall, wo heute Jahrgänge gelten (Stundentafeln, Rechte, Postfach, Anmelde-Richtlinien); eine Klasse hat Bildungsgang, Typ, Parallelbezeichnung und freien Namen (aus dem Muster vorgeschlagen, überschreibbar); Jahrgangsbereich einstellbar; „Entfall erlaubt ab Klassenstufe“ je Bildungsgang überschreibbar; Stundentafel-Vorrang Klasse > Gruppe > Bildungsgang+Jahrgang > Jahrgang; Pläne zeigen Klassennamen statt Kürzel, wo Platz ist. Nutzer 10-12: „Klassentypen hinzufügen und löschen; verschiedene Bildungsgänge … mit je eigener Klasse 11 und eigenen Namen.“
Abnahme: Bildungsgänge „Fachinformatik“ und „Maurer“ führen je eine Klasse 11 mit eigener Stundentafel und eigenem Namen; Gruppe „IT-Zweig 11–13“ legt eine Anmelde-Richtlinie für alle drei Stufen an; alter Stand lädt unverändert.

**STA-095** · P1 · Status: offen
Einstellungen an ihrem Ort: eigene Seite „Einstellungen“ (`settings.edit`) mit den Abschnitten Schule · Schulwoche & Zeitraster · Vertretung · Lehrkräfte · Krankmeldungen & Atteste · Postfach · Schnittstellen; jede Einstellung kommt genau einmal vor; jeder Abschnitt speichert für sich (nur geänderte Felder, nicht das ganze Objekt), Fehler erscheinen am Feld im selben Abschnitt, ungespeicherte Änderungen lösen eine Rückfrage aus; keine Erklärabsätze; 390 px ohne waagerechten Bildlauf; alte Adressen leiten weiter. Nutzer A-32: „Einstellungen bei ihrer eigenen Sache“.
Abnahme: Zeitraster ändern und speichern lässt die Postfach-Einstellungen unberührt; Reiterwechsel mit ungespeicherter Änderung → App-Dialog; `GET /einstellungen` leitet nicht mehr auf Planung um, alte Adresse leitet weiter.

---

## 2. Lehrkräfte – Profil, Verfügbarkeit, Anträge (LEH)

### 2.1 Stammdaten und Profil

**LEH-001** · P1 · Status: Ist
Lehrkraft (Stammdaten `teachers`): Felder und Standardwerte:

| Feld | Typ | Standard | Einheit / Wirkung |
|---|---|---|---|
| `id` | Text | Pflicht | Kürzel (eindeutig, ohne Beachtung der Groß-/Kleinschreibung, STA-024) |
| `name` | Text | Pflicht | personenbezogen |
| `subjects` | Liste Fach-Kennungen | [] | Fächer, die unterrichtet werden dürfen (Qualifikation); wirkt in Generator und Vertretung |
| `max_hours` | Ganzzahl | 25 | Deputat: Obergrenze Wochenstunden |
| `max_per_day` | Ganzzahl | 7 | Obergrenze Stunden je Tag |
| `unavailable` | Liste Zeitregeln (STA-055) | [] | harte Sperrzeiten: nicht einplanbar, auch nicht als Vertretung |
| `wishes` | Liste Zeitregeln | [] | weiche Wünsche „möglichst kein Unterricht“ (Gewicht `teacher_wish` 5,0) |
| `max_subs_per_week` | Ganzzahl | 3 | Vertretungen je Woche (Obergrenze; Datei VER) |
| `sites` | Liste Standort-Kennungen | [] | Einsatzorte, leer = alle |
| `email` | Text | leer | personenbezogen, nie automatisch (LEH-002) |
| `preferred_classes` | Liste Klassen | [] | Altbegriff „Wunschklassen“ (LEH-022) |
| `time_windows` | Liste {Tage, Beginn, Ende, Wochen} | [] | Arbeitszeitfenster, leer = ganztägig; werden in Sperrzeiten umgerechnet (LEH-014) |
| `work_grid` | Objekt {Wochen, gesperrte Felder} | {} | Arbeitszeitraster 1–52 Wochen (Altform, durch LEH-010 ersetzt) |
| `commutes` | Bool | true | Pendeln am selben Tag erlaubt (false = am Tag nur ein Standort) |
| `commute_mode` | Auswahl | leer | `never` / `once` / `free`; leer = nach `commutes` |
| `commute_gap` | Ganzzahl | 0 | Minuten Mindestabstand beim Standortwechsel zusätzlich zur Wegezeit |
| `times_self` | Bool | false | darf eigene Arbeitszeiten festlegen (LEH-016) |

Abnahme: Lehrkraft nur mit Kürzel und Name anlegen → `max_hours` 25, `max_per_day` 7, `max_subs_per_week` 3, `commutes` true, `times_self` false; zweites Kürzel „mue“ neben „MUE“ → 422.

**LEH-002** · P1 · Status: Ist
Die Lehrkraft-E-Mail wird nie automatisch angelegt; jede Schule hinterlegt sie von Hand (kein Erzeugen aus Namen, auch nicht in Demodaten). Nutzer 10-12: „da kann man die E-Mail hinterlegen lassen, aber das muss quasi jede Schule … manuell“.
Abnahme: Neue Lehrkraft ohne Eingabe → `email` leer; Massenanlage ohne E-Mail-Spalte erzeugt keine Adressen; Demo-Lehrkräfte haben nur Adressen auf `example.org`.

**LEH-003** · P1 · Status: Ist
Seite „Mein Profil als Lehrkraft“ (`/lehrkraft/profil`, Menüpunkt „Profil als Lehrkraft“, Startkachel Profil; Recht `profile.teacher_self`): zeigt Fächer, Wunschklassen, Deputat, Arbeitszeitfenster, Wünsche, Sperrzeiten, „Einmalige Ausnahme beantragen“ (LEH-009), „Stundenplan für diese Lehrkraft neu planen“ (LEH-024) und Pendeln (nur bei mehr als einem Standort, LEH-017). Der Rollenname „Ihre Rolle: …“ ist im Profil sichtbar. Die Rolle `admin` besitzt `profile.teacher_self` nicht und sieht keine Lehrkraft-Profile.
Abnahme: Konto `lehrer` öffnet die Seite; Konto `admin` → 403 und Menüpunkt fehlt; Schule mit einem Standort zeigt keinen Bereich „Pendeln“.

**LEH-004** · P0 · Status: Ist
Änderungen am Profil sind **Anträge** mit vorheriger Vorschau und nicht direkt wirksam. Einstellung `teacher_self_service`: `approval` (Standard) = Genehmigung nötig; `direct` = sofort gültig (Antrag `status` genehmigt, `auto` = ja). Antrag (`teacher_change_requests`): `id`, `teacher_id`, `user_id`, `kind` (`profil` | `ausnahme`), `payload` (bei `profil`: Fächer, Wunschklassen, Wochenstunden, Zeitfenster, Wünsche; bei `ausnahme`: Datum, Datum bis, Stunden, Anlass), `previous` (Profil zum Zeitpunkt des Antrags für den Vergleich), `note_enc` (Begründung), `status` (`offen` → `genehmigt` | `abgelehnt` | `zurueckgezogen`), `auto`, `reviewer_id`, `review_comment_enc`, `created_at`, `updated_at`, `decided_at`. Die Profilprüfung läuft vor dem Speichern gegen den **aktuellen** Stand (Bestand: kann gegen einen älteren Stand laufen). Genehmigung ändert das Stammdaten-Profil.
Abnahme: `approval`: Profiländerung einreichen → Stammdaten unverändert, Antrag `offen`; nach Genehmigung → Stammdaten geändert; `direct` → sofort geändert und `auto` = ja; Antrag gegen veralteten Stand → Konfliktmeldung mit aktuellem Vergleich.

**LEH-005** · P1 · Status: Ist
Vor dem Einreichen zeigt die Vorschau (`POST /me/teacher-profile/preview`) den Vergleich alt/neu als Tabelle samt Konflikten mit dem Stundenplan und Lösungsvorschlägen; Einreichen `PUT /me/teacher-profile`; eine eingereichte Änderung kann zurückgezogen werden (`DELETE /me/teacher-profile/request`); „Verlauf“ zeigt die eigenen Anträge mit Historie. Live-Aktualisierung der Bereiche `teacher_requests` und `teacher_profile`.
Abnahme: Vorschau mit Sperrzeit auf Montag, 1. Stunde, bei vorhandenem Unterricht → Konfliktliste mit mindestens einem Vorschlag; Zurückziehen setzt `zurueckgezogen`; Verlauf zeigt beide Einträge.

**LEH-006** · P2 · Status: Ist
Neues Fach vorschlagen: geht als Antrag an die Planung (Feld `new_subjects` mit Name und Kürzel); bei Genehmigung wird das Fach angelegt. Obergrenze je Profil [unklar: Wert].
Abnahme: Vorschlag „Robotik/ROB“ → Antrag `offen`; Genehmigung legt das Fach an und trägt es der Lehrkraft ein; Überschreiten der Obergrenze → 422.

### 2.2 Anträge prüfen und entscheiden

**LEH-007** · P1 · Status: Ist
Seite „Anträge von Lehrkräften“ (`/planung/antraege?status=&lehrkraft=&antrag=`, Recht `teacher_requests.review`, Menüpunkt mit Anzahl-Abzeichen offener Anträge, Startkachel „Anträge“): Liste mit Filtern nach Status und Lehrkraft, Zusammenfassung mit Zählungen (`GET /teacher-requests/summary`), Detail mit Vergleich, Konflikten und Vorschlägen (`GET /teacher-requests/{id}`), Vorschau für eine Lehrkraft (`POST /teacher-profiles/{teacher_id}/preview`), Neuplanung für beliebige Lehrkraft direkt von der Antragsseite. Fremde Anträge ohne Prüfrecht → 404.
Abnahme: Filter `status=offen&lehrkraft=MUE` zeigt nur passende Anträge; Abzeichen zeigt die Zahl der offenen; `lehrer` ohne Prüfrecht ruft `GET /teacher-requests/5` eines anderen → 404.

**LEH-008** · P0 · Status: Ist
Entscheiden: Ablehnen `teacher_requests.review`; Genehmigen `teacher_requests.review` **und** `masterdata.edit`. Standardinhaber: Planung, Schulleitung, Administration; das Sekretariat genehmigt nicht. Ablehnen mit Kommentar (`review_comment_enc`, verschlüsselt) [unklar: Begründung Pflicht oder optional]. Die Entscheidung benachrichtigt die antragstellende Lehrkraft (Art `request_decided`, BEN-003). Nutzer 10-12: „Eine Anfrageoption und dann können die Hörbestellten das genehmigen“ (gemeint: berechtigte Personen). Lehrkraft und Vorgesetzte antworten einander.
Abnahme: Konto `schulleitung` genehmigt → Profil geändert, Status `genehmigt`, `decided_at` gesetzt; Konto `sekretariat` → 403; Genehmigung ohne `masterdata.edit` → 403; erneutes Genehmigen eines entschiedenen Antrags → 409.

**LEH-009** · P1 · Status: Ist
„Einmalige Ausnahme beantragen“ (`POST /me/teacher-requests/exception`): Datum (optional „bis“-Datum), ab/bis Stunde oder ganztägig, Anlass als Freitext (verschlüsselt), z. B. „Do ab 5. Stunde frei wegen Arzttermin“. Nach Genehmigung entsteht eine Abwesenheit (Art Lehrkraft), der Vertretungsplan übernimmt; der Abwesenheitsgrund bleibt verschlüsselt und wird in jedem Lesepfad (Vertretung, Stammdaten, Klassen, Integrationen) nur über die zentrale Auflösung gelesen. Eigene Ausnahme-Anträge können zurückgezogen werden (`DELETE /me/teacher-requests/{id}`). Dauerhafte Änderungen („ab KW 40 mittwochs nicht“) laufen als Profilantrag mit „Gilt ab“ (LEH-012).
Abnahme: Ausnahme für Donnerstag ab 5. Stunde genehmigen → Abwesenheit ab Stunde 5 (0-basiert 4), Vertretungsplan zeigt Bedarf; Grund im Klartext nirgends in Datenbank oder Protokoll; Zurückziehen vor Entscheidung entfernt den Antrag.

### 2.3 Verfügbarkeit, Sperrzeiten, Rhythmus

**LEH-010** · P1 · Status: Ist
Ein Editor „Verfügbarkeit“ für Arbeitszeiten, Sperrzeiten und Wünsche ersetzt drei alte Bereiche in Profil und Stammdaten. Ein Block hat sein eigenes Raster Tag × Stunde (das gemeinsame Raster, Zellen antippen oder ziehen, Tageskopf sperrt den Tag, Stundenzeile die Stunde, gesperrte Felder schraffiert; Legende), die **Art** (gesperrt | Wunsch), „Wie oft?“ (LEH-011), „Gilt ab“ mit Datum und Notiz. Hinweise bei zu wenigen freien Stunden und bei gesperrten Stunden mit Unterricht. Gesperrte Stunden werden feste Sperrzeiten für Stundenplan-Generator und Vertretungsplanung. Alte Zeitfenster/Raster werden verlustfrei übernommen. Nutzer 10-12: „kann quasi auf die erste Stunde tippen und dann wird die erste Stunde blockiert in der Woche am Montag“.
Abnahme: Block „Montag, 1. Stunde, gesperrt“ anlegen → Generator plant dort keinen Unterricht, Vertretung setzt die Lehrkraft dort nicht ein; Tippen auf eine gesperrte Zelle gibt sie frei; alter Bestand mit `time_windows` lädt ohne Verlust.

**LEH-011** · P1 · Status: Ist
„Wie oft?“ (Rhythmus statt Einzelwochen-Auswahl): jede Woche | alle 2, 3 oder 4 Wochen | eigenes Intervall | nur bestimmte Kalenderwochen; ein Block hat nie mehr Wochenmodell als diesen Satz (Regeln STA-055). Nutzer 10-12: „kein Rhythmus, oder ein Wochenrhythmus, oder ein Zwei-Wochen-Rhythmus, oder ein Drei-Wochen-Rhythmus“; die wöchentliche Mehrfachauswahl ist „Quatsch“. Wochenfenster, die nur alle zwei Wochen gelten, zählen im Wochenplan nicht als verlässliche Verfügbarkeit (konservativ), werden aber exakt gespeichert. Die Eingabe einer Regel ohne Auswahl wird abgelehnt (422); „ganze Woche“ ist nur nach ausdrücklicher Wahl möglich (Bestand: leere Regel sperrt still die ganze Woche).
Abnahme: Block „alle 2 Wochen ab KW 38“ → gesperrt in KW 38, 40, 42; leere Regel speichern → 422; „nur KW 36, 38“ zeigt „KW 36, 38“.

**LEH-012** · P1 · Status: Ist
Änderungen im laufenden Jahr: „Gilt ab“ wirkt ab dem Datum; Konflikte mit dem Stundenplan zählen erst ab diesem Datum. Die Seite zeigt Lösungsvorschläge (Teilneuplanung, Stunde verschieben, Termin später, freie Lehrkräfte mit passendem Fach) mit dem Hinweis „nichts davon geschieht automatisch“; eine automatische Übernahme von Plan-Änderungen ist standardmäßig aus (`plan_auto_apply` = `aus`; Alternative `raeume`: reine Raumänderungen und Entfernen verwaister Stunden gelten sofort, mit Verlauf und Audit). Nutzer 10-12: „… mitten im Jahr sagen kannst, okay, dieser Lehrer kann Mittwochs jetzt auf einmal nicht mehr … und dann wird halt der Stundenplan entsprechend daran umgestellt.“
Abnahme: Sperrzeit „Mittwoch ab 01.12.“ → Konfliktzähler zählt nur Stunden ab 01.12.; es wird nichts verschoben, bis jemand einen Vorschlag annimmt; Vorschlagsliste enthält die vier Arten.

**LEH-013** · P1 · Status: Ist
Sperrzeitregeln: Eine Sperrzeit hat **nie Unterricht**. Sperrzeiten werden jährlich beim Neuaufbau des Gesamtplans festgelegt und sind unterjährig jederzeit mit „Gilt ab“ änderbar (Nutzer 10-12: „nur jedes Jahr … mitten im Jahr sagen kannst“). Wünsche sind weich (Gewichtung, kein Verbot). Zeitregeln von Lehrkräften und Klassen nutzen dieselbe Regelstruktur (STA-055: Wochen/Rhythmus, Tage, Stunden, Notiz, `valid_from`, `valid_week`).
Abnahme: Generator-Lauf nach Anlegen der Sperrzeit enthält keinen Unterricht der Lehrkraft in dem Slot; Wunsch „Freitag, 6. Stunde“ erzeugt Unterricht dort nur bei Strafpunkten (kein harter Konflikt).

**LEH-014** · P1 · Status: Ist
Zeitfenster-Regel (Arbeitszeitfenster): Eine Stunde gilt nur als verfügbar, wenn sie **komplett** im Fenster liegt (gleich in Oberfläche und Server, identisches Ergebnis und identisches Anzeigeformat). Aus Zeitfenstern entstehen Sperrzeiten, gekennzeichnet durch ein eigenes Merkmal (nicht über Notiztext „Zeitfenster …“, sonst entstehen Dubletten, wenn eine Sperrzeit von Hand denselben Text trägt). Beispiele: „erst ab 10 Uhr“, „nur Abendunterricht ab 16 Uhr“ (Nutzer A-08).
Abnahme: Fenster 16:00–21:15 und Stunde 15:10–15:55 → Stunde gesperrt; Stunde 15:55–16:40 → gesperrt (nicht komplett im Fenster); von Hand angelegte Sperrzeit mit Notiz „Zeitfenster“ erzeugt keine Dublette.

**LEH-015** · P1 · Status: Ist
Die „Schnellauswahl“ bei Arbeitszeiten (Presets „Nur vormittags“, „Nur ab Mittag“, „Nicht in der 1. Stunde“, „Nur abends“, „Alles frei“, „Alles sperren“, „Umkehren“) gibt es nicht. Nutzer 10-12: „Die habe ich dir gesagt, die Schnellauswahl kommt weg.“ Ebenso entfällt das Antippfeld als eigener Bereich: „das Antippfeld ist auch komplett überflüssig. Das kommt unten hin mit dem Auswählen, mit diesem Rhythmusauswählen.“ (spätere Aussage gilt).
Abnahme: Der Editor enthält keine Schaltflächen der genannten Presets; Rhythmus wird je Block unten gewählt.

**LEH-016** · P0 · Status: Ist
Arbeitszeiten dürfen Lehrkräfte nur mit Freigabe setzen: Schulvorgabe `teacher_times_self` (Standard false), je Lehrkraft `times_self`; ohne Freigabe legt nur Schulleitung/Planung die Arbeitszeitfenster fest oder die Lehrkraft stellt einen Antrag (LEH-004). Lehrkräfte setzen selbst nur Wünsche (A-51). Frühere Annahme „Lehrkräfte dürfen Arbeitszeiten frei setzen“ war falsch. Gesperrte Zeiten fließen in Generator und Vertretung.
Abnahme: `times_self` false: Lehrkraft versucht `time_windows` direkt zu speichern → als Antrag `offen` bzw. 403; mit `times_self` true → gespeichert; Wünsche sind immer als Antrag/direkt nach `teacher_self_service`.

**LEH-017** · P1 · Status: Ist
Pendeln zwischen Standorten – **nur sichtbar, wenn die Schule mehr als einen Standort hat** („Dass es quasi nur dargestellt wird, wenn das so ist.“). Statt ausgeschriebener Langfassung pro Lehrkraft: nie | höchstens 1× am Tag | beliebig (`commute_mode`), plus „Mindestpause zwischen den Standorten“ (`commute_gap`, Minuten). Nutzer 10-12: „ob man dazwischen eine Pause haben will oder ob man immer pendeln will oder ob man nur einmal pendeln will oder ob man kein Mal pendeln will und dass es auch mit dem Stundenplan passt.“ Generator, Vertretung und Verschieben von Stunden halten sich daran; die Vertretung setzt Nicht-Pendler nicht am anderen Standort ein; einer Lehrkraft wird angezeigt, wenn sie zwischen zwei Stunden den Standort wechseln muss.
Abnahme: Schule mit einem Standort: kein Pendelbereich; zwei Standorte, `never`, Stunden an beiden Standorten am selben Tag → Konflikt im Qualitätsbericht; `once` erlaubt genau einen Wechsel.

**LEH-018** · P1 · Status: Ist
Wegezeiten: Tabelle mit Fahrminuten je Standortpaar (`site_travel`, beide Richtungen); fehlt ein Paar, gelten `site_travel_periods` (Standard 1 freie Stunde); die Mindestpause je Lehrkraft kommt hinzu. Reisezeit-Verstöße werden erkannt.
Abnahme: Paar A–B = 25 min, Lehrkraft `commute_gap` 10 → 35 min Mindestabstand; ohne Eintrag für A–C → 1 freie Stunde.

**LEH-019** · P3 · Status: offen
Sonderfälle beim Schulwechsel (Nutzer 10-11/12, nicht geprüft): Wechsel nur in den Pausen erlaubt oder nicht; morgens zu einer Schule länger, dann dort erste zwei Stunden nicht; „die ersten zwei Stunden … bei Standort A, und die zweiten bei Standort B“. Der Nutzer will **keine festen Optionen**, sondern frei kombinierbare Regeln (LEH-020). Bestand deckt dies nur teilweise über Standort, Rhythmus und Pendelregeln.
Abnahme: Regel „Standort A in Stunde 1–2, Standort B in Stunde 3–4, Wechsel in der Pause erlaubt“ lässt sich mit den Bausteinen der Verfügbarkeit ausdrücken und wird vom Generator eingehalten.

**LEH-020** · P1 · Status: Ist
Modularität: Keine festen Optionen für Arbeitszeiten; alles frei setzbar und kombinierbar. Nutzer 10-11: „es sollen jetzt keine festen optionen sein ich will dass es alles sehr modular und frei setzbar sind“; Beispiele: an bestimmten Tagen nicht verfügbar, später anfangen, Schulwechsel in Pausen, nur einmal hin- und herfahren, erste zwei Stunden an Schule A nicht, an Schule B schon; „auch weitere Anwendungsfälle sollen funktionieren“. Wochentags-Zyklen: Lehrkräfte geben bei der Anlage oder später an, an welchen Wochentagen sie können („jeden Montag dann können, Dienstag dann …“).
Abnahme: Zwei beliebige Blöcke mit verschiedener Art und verschiedenem Rhythmus für dieselbe Lehrkraft lassen sich nebeneinander speichern; der Generator wertet beide aus.

**LEH-021** · P1 · Status: offen
Wiederholungsregeln des Wochenplans mit Ausnahmen (Backlog B-35/B-42, Pflicht-Rückmeldung A-50/A-51): Verfügbarkeit = Grundwochenplan (leer = immer verfügbar) plus Ausnahmen mit Wiederholung: wöchentlich (alle n Wochen ab Datum), monatlich (n-ter Wochentag), jährlich, mit Gültigkeitszeitraum; Arten „nicht verfügbar“, „erst ab“, „nur bis“, „nur“; Sperrzeiten bis zur einzelnen Stunde an einzelnen Kalendertagen; Satzbaukasten („Jeden [1.] [Mittwoch] im [Monat] → [nicht verfügbar]“, „Alle [2] Wochen ab [Datum] erst ab [10:00]“) mit Klartext-Zusammenfassung; Vorschau-Kalender über 8 Wochen; Raster per Tastatur bedienbar, am Handy je Tag als Liste; der Bericht meldet Regeln, die der Generator nicht berücksichtigt („an 5 Terminen im Halbjahr Konflikt – Vertretung nötig“). Testfälle des Betreibers: „jeden 1. Mittwoch im Monat“, „jede 3. Woche nicht“, „alle 2 Wochen erst ab 10“, „mittwochs nie nach 12“, „erst ab 9“.
Abnahme: Alle fünf Testfälle liefern an Beispieldaten die erwarteten gesperrten Termine; Vorschau-Kalender zeigt sie; Eingabe nur per Tastatur möglich.

**LEH-022** · P1 · Status: offen
„Wunschklassen“ entfallen (Pflicht-Rückmeldung A-48): das Profil zeigt „Klassenleitung in“ (nur lesen), „Ich unterrichte“ (aus den Kursen, nur lesen) und „Ich kann vertreten in“ (bearbeitbar, vorgeschlagen: die unterrichteten Klassen); vorhandene Wunschklassen werden einmalig übernommen und danach nicht mehr angezeigt; die Planung liest Altwerte weiter; die Vertretung bevorzugt Lehrkräfte mit „kann vertreten in“ für die Klasse („Vertretung durch Lehrkräfte, die dieselben Klassen unterrichten“). Der Begriff „Wunschklassen“ erscheint in keiner Meldung, CSV-Spalte oder Oberfläche.
Abnahme: Profil enthält die drei Bereiche; Suche nach „Wunschklasse“ in der Oberfläche liefert keinen Treffer; Vertretung schlägt zuerst Lehrkräfte mit passendem „kann vertreten in“ vor.

**LEH-023** · P1 · Status: offen
Selbstverwaltung begrenzt (A-49, Standardwert zu bestätigen): Lehrkräfte bestimmen nicht selbst maximale Stunden oder Vertretungsgrenzen; sie geben **nur Tage/Verfügbarkeit und eine gewünschte Höchstzahl Wochenstunden als Wunsch** an. Deputat (`max_hours`), Vertretungs- und Tagesgrenzen setzt Schulleitung/Planung. Bestand: das Profil enthält das Deputat, im Modus `direct` sofort gültig; offene Altanträge mit Deputat werden ohne Fehler ignoriert. Welche Felder Lehrkräfte ändern dürfen, ist einstellbar. [unklar: Widerspruch – Deputat vollständig aus dem Profil entfernen (B-02) oder Wunschfeld `requested_max_hours` behalten (B-34); Abgrenzung nötig, damit kein Selbst-Deputat entsteht.]
Abnahme: Lehrkraft ändert Deputat im Profil → Antrag wird abgelehnt/Feld nicht angeboten; Wunsch „höchstens 20 Std.“ wird gespeichert und von der Planung nur als Wunsch gelesen.

### 2.4 Plan, Rechte und Datenschutz

**LEH-024** · P2 · Status: Ist
„Stundenplan für diese Lehrkraft neu planen“: startet einen Hintergrundjob (`replan_teacher`); die Oberfläche zeigt laufend/fertig; läuft bereits ein Job, wird er angezeigt statt eines zweiten. Planung kann dies für beliebige Lehrkräfte direkt von der Antragsseite starten. [unklar: Recht für fremde Lehrkräfte; Vorschlag `timetable.generate`.]
Abnahme: Start → Statusanzeige „läuft“, nach Ende „fertig“; zweiter Start während des Laufs zeigt den laufenden Job; Lehrkraft ohne Recht kann den Job einer anderen Lehrkraft nicht starten (403).

**LEH-025** · P0 · Status: Ist
Lehrer-Scope: Lehrkräfte haben keinen Vollzugriff, sondern nur auf eigene Fächer und Klassen. Pläne sehen sie für sich und, als Klassenleitung, für die eigene Klasse und deren Schüler/innen (nicht alle Pläne); Raumpläne, andere Lehrkräfte und Stammdaten nur Administration und Planung. Zugriff auf nicht erlaubte Bezugsobjekte wird abgelehnt (404 für fremde Datensätze; die Oberfläche zeigt einen Hinweis zum Umfang).
Abnahme: Fachlehrkraft ruft Plan einer fremden Lehrkraft → 404; Klassenleitung 5a ruft Plan der 5a → 200 und Plan der 5b → 404; `GET /data/students` liefert nur Schüler/innen der eigenen Kurse.

**LEH-026** · P0 · Status: Ist
Personaldaten schützen: Die technische Administration sieht keine Lehrkraft-Profile, Anlässe und Begründungen (kein `profile.teacher_self`). Prüfer/innen (`teacher_requests.review`) sehen Anträge im Umfang ihrer Aufgabe. [unklar: ob die Administration, die `teacher_requests.review` im Standard besitzt, Freitexte (Anlass, Begründung) sehen darf; Vorschlag: Anlass nur Planung und Schulleitung.]
Abnahme: Konto `admin` ruft `GET /me/teacher-profile` → 403; Anlasstext eines Antrags ist für `admin` verdeckt (nach Entscheidung des Neubaus).

**LEH-027** · P1 · Status: Ist
Lehrkonto ohne Zuordnung zu einer Lehrkraft (Rollenfall „Lehrkonto ohne Zuordnung“) erhält auf Lehrkraft-Funktionen **403** mit hilfreicher Meldung (bewusste Ausnahme von der 404-Regel), z. B. „Ihr Konto ist noch keiner Lehrkraft zugeordnet.“ Eine Verknüpfung Konto ↔ `teacher_id` passt zur Rolle (kein Lehrer-Konto an Schüler-Kennung).
Abnahme: Lehrer-Konto ohne `teacher_id` ruft `/lehrkraft/profil` → 403 mit obiger Meldung; Zuordnung einer Schüler-Kennung an ein Lehrer-Konto → 422.

**LEH-028** · P2 · Status: offen
„Ich bin neu“: ein Lehrerkonto ohne verknüpfte Lehrkraft kann beantragen, dass die Planung die Lehrkraft anlegt und verknüpft (Bestand: kein Profil anlegbar, 409). Vorschlag eines neuen Fachs mit Option „auf vorhandenes Fach abbilden“ gegen Dubletten bei Genehmigung.
Abnahme: Konto ohne Zuordnung stellt „Ich bin neu“ → Antrag bei der Planung; Genehmigung legt die Lehrkraft an und verknüpft das Konto; Fachvorschlag „Mathematik“ wird auf vorhandenes „Mathe“ abgebildet statt neu angelegt.

**LEH-029** · P0 · Status: Ist
Freitexte der Lehrkräfte sind verschlüsselt: Anlass der Ausnahmen (im Antragsinhalt und als Abwesenheitsgrund), `note_enc` (Begründung), `review_comment_enc` (Kommentar der Prüfenden; Kontext `teacher_change_requests:<id>:<feld>`, im Neubau einheitlich `<tabelle>.<feld>:<id>`); Audit-Grund nur als Länge oder verschlüsselt; die Schlüsselrotation (`rotate-keys`) erfasst diese Spalten. Offen: `payload` enthält `wishes` und `reason` unverschlüsselt als JSON – Freitexte darin sind zu verschlüsseln.
Abnahme: Direkter Datenbankzugriff zeigt für `note_enc`/`review_comment_enc` Chiffrat `SM1…`; Ausnahme-Anlass erscheint nicht im Klartext in `payload`; Audit enthält keinen Anlasstext.

**LEH-030** · P2 · Status: Ist
Kennzahl „Lehrkräfte über Deputat“ in der Planung; Anwesenheit der laufenden Stunde auf der Lehrkraft-Startseite (Karte mit Stunde aus dem Klassenbuch); Lehrkraft-Zeitfenster und Deputat fließen in Plan-Prüfung und Vertretungsplanung.
Abnahme: Lehrkraft mit 27 Std. bei Deputat 25 erscheint in der Kachel „über Deputat“; Startseite zeigt die laufende Stunde mit Klassenbuch-Eintrag.

**LEH-031** · P3 · Status: offen
Arbeitstage und Mindeststunden prüfen (Nutzer 10-11: „dass die auch wirklich ihre Arbeitstage halten“): Lehrkräfte „checken ein“, wenn sie unterrichten; Tracking, ob Arbeitstage und Mindeststunden gehalten werden; modular und frei setzbar.
Abnahme: Lehrkraft checkt in der Stunde ein; Auswertung zeigt je Woche gehaltene gegen vereinbarte Arbeitstage.

**LEH-032** · P0 · Status: Ist
„Abwesend bis“ mit automatischer Antwort an Eltern wird **nicht** gebaut (datenschutzkritisch). Automatische Mails sind als solche gekennzeichnet, damit Mailprogramme keine Abwesenheitsnotizen zurückschicken (BEN-018).
Abnahme: Es existiert keine Funktion, die bei Abwesenheit einer Lehrkraft automatisch an Eltern antwortet; Auto-Mails tragen die Auto-Kennzeichnung.

**LEH-033** · P3 · Status: offen
Kleine Wünsche: „Abwesend bis“-Hinweis (nur als Hinweis im Profil/Chat, nie als Auto-Antwort an Eltern); Fortbildungsanträge mit Genehmigung (Termine mit teilnehmenden Lehrkräften sind gebaut, STA-021); Einzelprofil-Seite für Lehrkräfte; Ruhezeiten für Lehrkräfte; Bereitschaftsdienste/Vertretungskonto (Datei VER).
Abnahme: „Abwesend bis 24.10.“ im Profil erscheint als Hinweis in Chat-Kopf und Lehrkraft-Plan, ohne dass eine Nachricht automatisch versendet wird.

**LEH-034** · P2 · Status: offen
Qualitätsbericht zählt Pendelverstöße (Anzahl je Lehrkraft) und zeigt sie auf der Seite; Bestand: Zählung auf der Seite nicht sichtbar.
Abnahme: Lehrkraft mit `never` und 2 Wechseln an einem Tag erscheint im Bericht mit „2 Verstöße“.

---

## 3. Schüler/innen und Eltern – Familie, Selbstbedienung (SCH)

### 3.1 Konten, Geburtsdatum, Volljährigkeit

**SCH-001** · P1 · Status: Ist
Konto-Bezüge: Schüler/innen und Eltern sind Konten (`users`, Rollen `schueler`, `eltern`); die Verbindung zu den Stammdaten läuft nur über IDs (`users.student_id`; Eltern ↔ Kind in `parent_links`). Schüler/innen-Daten (Name, Klasse, Kurse, Geburtsdatum) stehen in den Stammdaten (STA-016). Passwörter von Schüler/innen haben mindestens 8 Zeichen; Benutzername und häufige Passwörter werden abgelehnt (Regel kommt vom Server, Datei ANM).
Abnahme: Schülerkonto mit Passwort „abc123“ → 422 Klartext; Konto `eltern` sieht über `GET /data/students` nur verknüpfte Kinder.

**SCH-002** · P1 · Status: Ist
Schülerdetail (Stammdaten → Schüler/innen; `GET /students/{sid}/people`, Recht `students.read`): Eltern, Klassenleitung, Fachlehrkräfte je Fach, Dokumente, Abschnitt „Förderung & Nachteilsausgleich“ (SCH-014), Spalte „Merkmale“ in der Schülerliste (Kennzeichen aus `GET /students/support-flags` für Berechtigte), Aktion „Konto zurücksetzen“ [unklar: Recht und Ablauf; Vorschlag `passwords.reset` bzw. `users.manage`]. Nutzer 10-12: „Schülerdetail mit Eltern, Klassenleitung und Fachlehrkräften je Fach.“
Abnahme: Detail einer Schülerin der 5a zeigt Eltern, Klassenleitung und je Fach die Lehrkraft; Fachlehrkraft ohne Unterricht bei der Person → 404.

**SCH-003** · P0 · Status: Ist
Geburtsdatum: Das echte Geburtsdatum bestimmt, ob jemand minderjährig ist. Setzen mit Recht `students.birth_date` (`PUT /students/{id}/birth-date`) durch Administration, Schulleitung, Sekretariat und Klassenleitung (eigene Klasse); Datum nur gültig (ISO), fremde Schüler-ID → 404, fehlendes Recht → 403. Geburtsdaten sind nur für Rollen sichtbar, die sie brauchen; CSV-/Untis-Import ergänzt, überschreibt nie (STA-073). Offen (Entscheidung): Nutzer 10-12 nannte „von einem Schüler, von den Lehrern oder von einem Admin“; das Selbst-Ändern durch Schüler/innen ist nicht vorgesehen [unklar].
Abnahme: Klassenleitung der 5a setzt das Datum einer Schülerin der 5a → 200 und Audit-Eintrag ohne Inhalt; für Schüler der 5b → 404; `eltern` → 403; „31.02.2010“ → 422.

**SCH-004** · P0 · Status: Ist
Volljährigkeit: ab 18 Jahren, aus dem Geburtsdatum, Stichtag Europe/Berlin; die Rechte wechseln bei jeder Anfrage am Geburtstag ohne Zutun. `users.adult` gilt nur, solange kein Geburtsdatum vorliegt. Volljährige Schüler/innen dürfen selbst krank melden, Beurlaubung und Unterlagen einreichen (`student_absence.report`, `student_documents.read` im Umfang „nur selbst“) und verwalten die Elternfreigaben (SCH-006). Alle Anlagewege (Klassen-Assistent, „Schüler/in hinzufügen“, „fehlende Konten anlegen“, Massenanlage, Import) behandeln Volljährige gleich: kein automatisches Elternkonto, Selbstmeldung möglich.
Abnahme: Mit fester Uhr: Schüler wird am 18. Geburtstag volljährig → am Folgetag ohne Eingriff Selbst-Krankmeldung möglich; Massenanlage mit Volljährigem erzeugt kein Elternkonto; Schüler mit 17 Jahren und 364 Tagen → kein Krank-melden-Button.

**SCH-005** · P2 · Status: offen
Einheit und Hinweise zur Volljährigkeit: alle Stellen (Kursräume, Dokumente, Übersicht, Selbstmeldung, Rechte, Kontoanlage) nutzen dieselbe Altersprüfung (Bestand uneinheitlich: teils Geburtsdatum, teils `adult`); am Tag der Volljährigkeit erhält die Person eine Mitteilung (Postfach/E-Mail; Bestand: nur In-App-Hinweis „Sie sind jetzt volljährig …“ mit Link zu den Schaltern); die Benutzerverwaltung zeigt „volljährig seit …“; der Haken „volljährig“ erscheint nur ohne Geburtsdatum.
Abnahme: Prüfmatrix über alle Wege ergibt für dieselbe Person überall dieselbe Entscheidung; am Geburtstag liegt eine Nachricht im Postfach der Person; Benutzerverwaltung zeigt „volljährig seit 12.10.2026“.

### 3.2 Eltern und Freigaben

**SCH-006** · P0 · Status: Ist
Eltern-Freigaben ab 18: Im Profil („Mein Konto“, `/profil`, nur für Schüler/innen sichtbar) steht der Abschnitt „Was dürfen meine Eltern sehen?“ mit einem Schalter je Bereich: Kursräume (inklusive Hausaufgaben), Krankmeldungen, Noten, Stundenplan, Dokumente/Atteste, Mitteilungen und Kompetenzen/Lernstand [unklar: Postfach/Kanäle fehlt in der Bestandsliste; Nutzer nannte „Postfach“]. Ablage `parent_access` (`student_id`, `area` ∈ kursraeume | krankmeldungen | dokumente | stundenplan | noten | mitteilungen | kompetenzen, `allowed`, `set_by`, `updated_at`; eindeutig je `student_id`+`area`). Standard **nein**; ein fehlender Eintrag bedeutet nein. Nur die Person selbst (volljährig) setzt die Schalter; jede Änderung steht im Audit (ohne Inhalte) und ist jederzeit widerrufbar. Unter 18 sind die Schalter ausgegraut mit dem Hinweis „ab 18“. Der alte Schalter „Eltern dürfen Kursräume sehen“ entfällt. Nutzer 10-12: „Dass dann, wenn der Schüler 18 wird, der Schüler die Option bekommt …“, dazu Stundenplan, Krankheit/Abwesenheit, Hausaufgaben, Newsletter, Postfach und automatische Weiterleitung „mich / meine Eltern / beide“. Schulvorgabe `adult_parent_access_default` (Standard: keine Einsicht) kann die Schule ändern [offen].
Abnahme: Volljährige Schülerin schaltet „Krankmeldungen“ an → Eltern sehen sie, „Noten“ bleibt aus → Eltern erhalten für Noten 403/leer; Eltern rufen `PUT /parent-access` → 403; Minderjährige: Schalter ausgegraut „ab 18“; Audit-Eintrag je Änderung.

**SCH-007** · P0 · Status: offen
Wirksamkeit der Freigaben überall: Ein zentraler, für alle Bereiche wiederverwendbarer Baustein entscheidet, ob Eltern ein Kind in einem Bereich sehen dürfen (Krankmeldungen mit Gründen, Krankmelden, Dokumente, Kursraum-Übersicht, Stundenplan inkl. `GET /timetable/student/{id}`, Klausuren, Eltern-Gruppe im Postfach, Noten, Lernstand, Mitteilungen); jeder neue Elternbereich muss ihn nutzen. Bestand: wirksam nur Kursräume und Krankmeldungen (Dokumente teilweise, Stundenplan offen, die übrigen nicht).
Abnahme: Rechte-Matrix-Test: Eltern eines minder- und eines volljährigen Kindes, mit und ohne Freigabe, je Bereich → erwartete 200/403/404 für jede Zelle; Stundenplan eines volljährigen Kindes ohne Freigabe → für Eltern verweigert.

**SCH-008** · P1 · Status: Ist
Zustellung von Schulinformationen: `student_prefs.delivery` ∈ `self` (nur an die Person; Standard), `parents`, `both`; für Minderjährige immer `both`. „Informationen der Schule gehen an: mich / meine Eltern / beide.“ `decided_at` leer = die Person hat noch nicht bewusst gespeichert, der Hinweis „Sie sind jetzt volljährig …“ bleibt sichtbar. [unklar: Rundschreiben an volljährige Schüler/innen ohne Wahl – nur Schüler oder beide; Eltern nach der Volljährigkeit automatisch alles oder nur auf Wunsch (Bestand: Standard „nur die Person“).]
Abnahme: Volljährige wählt „meine Eltern“ → Schulmails gehen nur an Eltern; Minderjährige: Auswahl nicht änderbar, `both`; ohne Wahl → Zustellung an die Person.

**SCH-009** · P0 · Status: Ist
Minderjährige: Eltern sehen alles, was das Kind sieht (automatisch aus dem Geburtsdatum); das Kind meldet sich nicht selbst krank (kein Krank-melden-Button, keine Beurlaubung, kein Upload; „Meine Fehlzeiten“ und Statistik nur lesen; Hinweis im Krankmeldungsbereich für unter 18). Eltern minderjähriger Kinder sehen Förderinformationen (Vollansicht). Eltern lesen den Kursraum des Kindes automatisch (nur lesen). Volljährige geben selbst frei (SCH-006).
Abnahme: Elternkonto eines 15-Jährigen sieht Stundenplan, Kursräume, Krankmeldungen ohne Freigabe; Kind (15) ruft `POST /student-absences` → 403; Elternkonto kann krank melden.

**SCH-010** · P0 · Status: Ist
Eltern-Kind-Verknüpfung `parent_links` (n:m): je Paar Elternkonto–Kind höchstens einmal; ein Elternkonto kann mehrere Kinder und Klassen betreffen; Eltern sehen nur verknüpfte Kinder und nur freigegebene Bereiche, Meldungen je Kind. **Migrationen dürfen keine Verknüpfungen löschen** (Lehre vom 10-11: ein Datenbank-Update löschte auf der Demo die Eltern-Kind-Verknüpfungen; Regressionstest gegen die betroffene Migration). Verknüpfung nur passend zur Rolle; wird der Stammdatensatz des Kindes gelöscht, sehen Eltern kein Kind ohne Klasse mehr.
Abnahme: Migrationstest: Bestand mit 3 Verknüpfungen vor und nach jeder Migration identisch; doppelte Verknüpfung → 409/ignoriert; Elternkonto A ruft Kind von Elternkonto B → 404.

**SCH-011** · P1 · Status: offen
Erziehungsberechtigte und Schülerakte (Backlog B-18, Pflicht-Rückmeldung A-41/A-44): Tabelle `guardians` (verschlüsselt: Name, E-Mail, Telefon; Beziehung, Sorgerecht, optional verknüpftes Konto); Elternangaben aus dem Klassen-Assistenten und „Schüler/in hinzufügen“ werden **immer gespeichert**, auch ohne Elternkonto (Bestand: gehen verloren); Konten entstehen aus den gespeicherten Erziehungsberechtigten, Geschwister teilen ein Konto (über die E-Mail zusammengeführt); Schülerakte für Sekretariat und Schulleitung (Klassenleitung lesend): Geburtsdatum, Adresse, Notfallkontakt, Erziehungsberechtigte, Ein- und Austrittsdatum, Bemerkung (verschlüsselt); Fachlehrkräfte sehen nichts davon; Klassenseite zeigt je Kind die Erziehungsberechtigten mit Status „Konto aktiv“, „kein Konto“, „nur Papier“; die Schule kann den Zugriff je Erziehungsberechtigtem einschränken (ohne Sorgerecht, Auskunftssperre), `parent_may_see` berücksichtigt das.
Abnahme: Drei Kinder, zwei Elternteile → zwei Elternkonten; Eltern ohne Konto bleiben als „nur Papier“ gespeichert; Fachlehrkraft ruft die Schülerakte → 404; Auskunftssperre sperrt die Einsicht für diese Person.

**SCH-012** · P1 · Status: Ist
Familie mit mehreren Kindern: Die Kinderauswahl erscheint nur bei mehreren Kindern; das gewählte Kind gilt überall (Startseite, Krankmeldungen, Noten, Kursräume); richtiges Kind ist im Eltern-Plan, bei Krankensymbol und Test-Marken vorausgewählt; Postfach-Klassensuche berücksichtigt Geschwister. Benachrichtigungen kommen je Kind (BEN-006).
Abnahme: Elternkonto mit 2 Kindern: Wechsel auf Kind 2 ändert Startseite, Krankmeldungen, Noten und Kursräume gemeinsam; bei einem Kind fehlt die Auswahl.

**SCH-013** · P2 · Status: offen
Die gemerkte Kinderauswahl gilt pro **Konto** (Bestand: gerätweit im Browser gemerkt); bei einem nicht (mehr) verknüpften Kind fällt die Startseite auf ein verknüpftes Kind zurück statt im 403 zu hängen; auf geteilten Geräten zeigt sie nie die Auswahl eines anderen Kontos.
Abnahme: Eltern A wählt Kind X, meldet sich ab, Eltern B meldet sich am selben Gerät an → B sieht nur eigene Kinder, kein 403; Verknüpfung zu X entfernen → Startseite zeigt das nächste Kind.

### 3.3 Förderung und Nachteilsausgleich

**SCH-014** · P0 · Status: Ist
Förderung je Schüler/in (Stammdaten, Detail, Abschnitt „Förderung & Nachteilsausgleich“; `student_support`): Arten `nachteilsausgleich`, `schulbegleitung`, `foerderplan`, `sonstiges`; Felder: Titel (verschlüsselt), Details (verschlüsselt), Gültig ab/bis (Datum), angehängte Dokumente (PDF/Dateien, verschlüsselte Ablage), Katalogeintrag, Zeitzuschlag in Minuten, Fächer (leer = alle), Hilfsmittel (verschlüsselt), anlegende Person, Zeitstempel. Anlegen, ändern, löschen mit `support.manage`; lesen `support.read`. Nutzer 10-11: Nachteilsausgleich und Schulbegleitung pro Schüler eintragen, „eine PDF … wo dann drin steht, was für einen Nachteilsausgleich der kriegt“.
Abnahme: Eintrag „Zeitzuschlag 15 Min., Duden“ mit PDF anlegen → Chiffrat in Titel/Details/Hilfsmitteln, Datei verschlüsselt; Konto ohne `support.manage` → 403; fremde Schüler-ID → 404.

**SCH-015** · P1 · Status: Ist
Förderkatalog der Schule (`support_catalog`, Dialog „Katalog“, Recht `support.catalog`): `label` (≤ 120), `kind` (vier Arten), `uses_minutes`, `default_minutes`, `teacher_visible` (Standard ja), `active` (ja), `sort`. Standardbestand (11 Einträge, aktiv): Zeitzuschlag (Nachteilsausgleich, mit Minuten, 15 min, für Lehrkräfte sichtbar), Wörterbuch/Duden erlaubt, Eigener Raum, Pausen/Bewegungspausen, Vergrößerte Schrift/Lesehilfe, Laptop/Tablet erlaubt (alle Nachteilsausgleich, sichtbar), ADHS (sonstiges, nicht sichtbar), Körperliche Behinderung (k) und Geistige Behinderung (g) (sonstiges, nicht sichtbar), Förderbedarf Lernen (foerderplan, nicht sichtbar), Schulbegleitung (schulbegleitung, nicht sichtbar). Die Schule legt weitere Einträge an, ändert und löscht sie. [unklar: Übernahme des Standard-Zeitzuschlags in den Eintrag; Wirkung von `active`; Löschen eines verwendeten Eintrags.]
Abnahme: Neue Instanz → Katalog enthält die 11 Einträge; Eintrag „Prüfungsangst“ mit `teacher_visible` nein anlegen → erscheint für Fachlehrkräfte nie; Konto ohne `support.catalog` → 403.

**SCH-016** · P0 · Status: Ist
Zugriff auf Förderdaten: **Nie für Fachlehrkräfte** (Diagnose-/Förderbedarfsmerkmale wie ADHS, Behinderung, Förderbedarf). Vollansicht (Details, Diagnose, Dokumente): Schulleitung, Sekretariat, Klassenleitung der eigenen Klasse, Schüler/in und Eltern (Eltern nur für minderjährige Kinder); technische Administration vollständig gesperrt. Fachlehrkräfte sehen bei Klausuren und Tests nur einen Hinweis aus Art, Minuten, Fächern, Hilfsmitteln (z. B. „+15 Min., Duden“) für Katalogeinträge mit `teacher_visible` = ja (`GET /exams/support-hints`, Recht `support.hints`, nur eigene Kurse), ohne Diagnose. **Jeder Zugriff wird im Audit-Log protokolliert** (ohne Inhalte). Förderdaten sind nie über API-Zugänge erreichbar; Notizen, die nur Lehrpersonal sehen darf, erscheinen nie in Antworten an Eltern oder Schüler/innen. Technische Administration kann nichts ändern. 
Abnahme: Fachlehrkraft ruft `GET /students/{sid}/support` → 404/403, ihr Klausurhinweis zeigt „+15 Min., Duden“ ohne ADHS-Eintrag; Klassenleitung der eigenen Klasse sieht alles; `admin` → 403; API-Token mit Umfang ruft Förderdaten → verweigert; Audit enthält jeden Zugriff.

**SCH-017** · P0 · Status: offen
Rechteprüfung der bislang nur „angemeldet“ geschützten Endpunkte festlegen: Dokument annehmen/ablehnen (`PATCH /student-documents/{id}`) und löschen — Personal im Umfang `student_documents.read` (Klassenleitung eigene Klasse, Sekretariat, Schulleitung); Förder-Einträge anlegen/ändern/löschen — `support.manage`; Katalog anlegen/ändern/löschen — `support.catalog`; Freigaben lesen/setzen (`/parent-access`) — nur die betroffene volljährige Person (lesen für Eltern nur den eigenen Stand, kein Schreiben).
Abnahme: Je Endpunkt ein Test „ohne Recht → 403, fremde ID → 404, mit Recht → 200“; Eltern senden `PATCH /student-documents/…` → 403.

**SCH-018** · P2 · Status: offen
Ausbau Förderung: Bearbeiten-Dialog für bestehende Einträge (Bestand: nur anlegen/löschen); Erinnerung im Wochenkalender; Antrag auf Nachteilsausgleich als Formularvorlage; Vermerk und interne Notiz getrennt (Vermerk für Familie sichtbar, interne Notiz nie); archivierte Dokumente nicht mehr prüfbar.
Abnahme: Eintrag bearbeiten ändert Minuten und schreibt Audit; Formularvorlage „Antrag Nachteilsausgleich“ erscheint bei Schüler/innen und Eltern; interne Notiz ist für Eltern unsichtbar.

**SCH-019** · P1 · Status: Ist
Schulbegleitung (eigene Rolle `schulbegleitung`, ohne Elternrechte, keine Krankmeldung): sieht zugewiesene Schüler/innen; Zugang zu Stundenplan, Kursräumen, Material und Abgaben des Kindes (Mithilfe im Schultag); Standardrechte `channels.use`, `substitution.read`.
Abnahme: Schulbegleitung eines Kindes sieht dessen Kursräume und Plan, aber nicht Krankmeldungen oder Noten; Konto ruft Kind einer anderen Begleitung → 404.

**SCH-020** · P1 · Status: offen
Schulbegleitung für mehrere Kinder mit Parität: Bestand führt das erste Kind als Hauptbezug und weitere nur in einer Liste; Neubau: alle zugewiesenen Kinder gleichberechtigt (Auswahl wie bei Eltern).
Abnahme: Schulbegleitung mit zwei Kindern wählt Kind 2 und sieht dessen Plan/Kursräume vollständig; Demo enthält eine Begleitung mit zwei Kindern.

### 3.4 Selbstbedienung und Ansichten

**SCH-021** · P1 · Status: Ist
Startseite von Schüler/innen und Eltern: Kindauswahl (nur bei mehreren), Wochenplan der laufenden Kalenderwoche, Klausuren, Aufgabenkarte (neues Material, fällige Aufgaben), Mitteilungskarte, Liste ungelesener Nachrichten, Hinweis auf fehlende Angaben, „Klassenleitung schreiben“, Krankmeldung (je nach Alter), Nachschreib-Hinweis (Eltern). „Meine Übersicht“ gibt es nicht mehr; ihre Inhalte stehen in Krankmeldungen (melden, Beurlaubung, Verlauf, Dokumente mit Download, Entschuldigungsformular), Start/Stundenplan (Heute), Kursräumen (Hausaufgaben) und der Notenseite. **Jede Seite ist über Menü, Startkachel oder Link erreichbar; kein Menüeintrag ohne Ziel** (automatischer Test). Der Vertretungsplan ist für Schüler/innen und Eltern ausgeblendet (kein `substitution.read`); sie sehen Entfall, Vertretung und Raumänderung im eigenen Plan. Handy: untere Navigationsleiste, Raster passt sich an, 390 px ohne seitlichen Bildlauf.
Abnahme: Schüler sieht in der Navigation Nachrichten, Kursräume, Noten, Lernstand, Krankmeldungen, Dokumente, Formulare, Benachrichtigungen, Hilfe, Profil; Aufruf `/vertretung` → 403; Menü-Ziele-Test bleibt grün; 390 px ohne waagerechten Bildlauf.

**SCH-022** · P1 · Status: Ist
Atteste und Dokumente einreichen (Selbstbedienung; `student_documents`, Recht `student_documents.read`): Eltern bzw. volljährige Schüler/innen wählen Kategorie (`attest`, `entschuldigung`, `beurlaubung`, `einverstaendnis`, `sonstiges`), laden eine Datei hoch (verschlüsselte Ablage) und senden ab; Hinweistext bei der Selbstmeldung; Status `eingegangen` → `geprueft` | `abgelehnt`, Status-Abzeichen, eigene Dokumente ansehen und Status verfolgen; Ablehnung durch Personal nur mit Begründung im Dialog. Zurückziehen = Archivieren (`withdrawn_at`: erscheint in keiner Liste, Datei bleibt), endgültig gelöscht erst nach der Aufbewahrungsfrist (400 Tage ab Erstellung, 30 Tage nach Austritt; Datei DAT); reine Papier-Atteste nur als Vermerk (ohne Datei). Prüf-Eingang `/dokumente` für Personal (nach Eingang sortiert), Startkachel „Atteste & Dokumente“ (Klassenleitung: eigene Klasse inklusive der heute Erkrankten), Menü-Abzeichen offener Dokumente; Dokumente können je Dokument für Eltern gesperrt werden; Fachlehrkräfte sehen Atteste nie; Upload begrenzt nach Größe und Dateityp [unklar: Werte]. Prüfung und Fehlzeitenlogik: Datei KLB.
Abnahme: Elternkonto reicht ein Attest (PDF) ein → Status „eingegangen“, Klassenleitung sieht es im Eingang; Ablehnen ohne Begründung → 422; Archivieren → nicht mehr in Listen, Datei besteht; Fachlehrkraft → 404.

**SCH-023** · P1 · Status: Ist
Fehlzeiten eines Kindes im Schuljahr (`/fehlzeiten/:Schüler-ID`, Recht `student_absence.read`): Summen in Tagen und Stunden, entschuldigt und unentschuldigt, Protokoll; sichtbar für Schüler/in, Eltern (je Kind), Klassenleitung, Sekretariat, Schulleitung; die ganze Schuljahresliste (nicht nur 14 Tage); Abwesenheit wird in Schultage umgerechnet [unklar: Behandlung von Wochenenden und Ferien].
Abnahme: Kind mit 2 Tagen entschuldigt und 3 Stunden unentschuldigt → Summen „2 Tage / 3 Stunden“ getrennt; Fachlehrkraft → 404; Eltern eines fremden Kindes → 404.

**SCH-024** · P1 · Status: Ist
Namens-Tooltips und Datenumfang: Schüler/innen und Eltern erhalten Namen von Personen nur aus ihren eigenen Stundenplandaten, nicht aus den Stammdaten; Stammdatenlisten sind rollenabhängig (Eltern nur verknüpfte Kinder; Lehrkräfte nur ihre Kurse). Kürzel werden beim Verweilen, Klicken oder langen Drücken zu ausgeschriebenen Namen.
Abnahme: Schüler fährt über das Kürzel einer Lehrkraft seines Plans → voller Name; eine Lehrkraft, die nicht im eigenen Plan steht, ist über die Stammdaten-Schnittstelle nicht abrufbar (404).

**SCH-025** · P0 · Status: Ist
Fremde Daten liefern 404: Selbstauskunft von Schüler/innen, Elternzugang (nur eigenes Kind) und Förderinformationen antworten bei fremden Schüler-IDs mit 404; 403 nur, wenn die Person den Datensatz sehen, aber nicht ändern darf, oder die Rolle das Recht nicht hat (Prüfpaket mit 42 Testfällen).
Abnahme: Rechte-Matrix: je Rolle × (Selbstauskunft, Eltern-Zugang, Förderdaten, Geburtsdatum) eigene ID → 200, fremde ID → 404, fehlendes Recht → 403.

**SCH-026** · P0 · Status: Ist
Auskunft und Export („Meine Daten exportieren“, `GET /me/export?format=json|zip`; Audit `user.export`): Eltern erhalten Daten ihrer Kinder nur für freigegebene Bereiche (`parent_access`); Förderdaten nur für minderjährige Kinder; Dokumente volljähriger Kinder nie an Eltern; volljährige Schüler/innen steuern die Zustellung selbst. Schüler/in ohne Konto: 404 mit Hinweis, die Auskunft manuell aus der Schülerakte zu erstellen. Offen: Elternfreigabe-Zeilen (`parent_access`) fehlen im Export und bleiben beim Löschen stehen; Auskunft vollständiger und kompakter (Alter/Geburtsdatum, Klasse, Eltern, Förderung, hinterlegte Daten; weniger Zeilen).
Abnahme: Export durch Eltern eines volljährigen Kindes ohne Freigabe enthält dessen Dokumente nicht; Export eines minderjährigen Kindes enthält Förderdaten; Audit-Eintrag je Export.

**SCH-027** · P1 · Status: Ist
Anrede der Schüler- und Elternansichten ist durchgängig **Sie** („Sie sind jetzt volljährig …“, „Ihr Konto“, „Was dürfen meine Eltern sehen?“ bleibt als Überschrift); der Bestandswiderspruch („du“ im Schülerprofil) ist zugunsten der Regel „siezt“ entschieden. Wörter wie „1 Einträge“ werden mit richtiger Mehrzahl gebildet.
Abnahme: Textsuche in allen Schüler-/Elternseiten findet kein „du/dein/dir/Du“ außerhalb von Zitaten; Hinweis am 18. Geburtstag beginnt mit „Sie sind jetzt volljährig“.

**SCH-028** · P2 · Status: offen
Schülerauswahl nach Klassen (Nutzer 10-11 20:20): In Auswahllisten (Administration, Lehrkräfte, Stundenplan-Ansicht) sind Schüler/innen nach Klassen gruppiert/sortiert und nach Klasse suchbar. Die Klassensuche im Postfach (mit Geschwistern) ist davon unabhängig und vorhanden.
Abnahme: Auswahl zeigt Gruppen „5a“, „5b“ …; Eingabe „5b“ filtert auf die Klasse.

**SCH-029** · P2 · Status: Ist
Anträge von Schüler/innen und Eltern: kein eigener Antragsweg; die Oberfläche verlinkt auf die vorhandenen Formulare (z. B. Beurlaubung). Nutzerwunsch 10-12: „Sowas soll bitte auch die Kinder zu den Lehrern, sollen die Lehrer zu den höhergestellten da antworten.“ (Weg Schüler/Eltern → Lehrkraft → Vorgesetzte; Datei FOR).
Abnahme: Auf der Startseite führt „Beurlaubung beantragen“ zum Formular; die Klassenleitung erhält den Antrag.

**SCH-030** · P0 · Status: offen
Schutzlücken laut Audit: Hinweise zu Minderjährigen fehlen (niedrig); Schüler-Konten dürfen keine API-Token ausstellen (Pflicht der Sicherheitswelle 1, Datei INT/SIC).
Abnahme: `POST` auf Token-Ausstellung mit Schülerkonto → 403; Minderjährigen-Hinweis erscheint an den betroffenen Stellen.

**SCH-031** · P1 · Status: offen
Offene Entscheidungen zu Eltern/Volljährigen (Betreiber): (a) Eltern nach der Volljährigkeit – automatisch alles oder nur auf Wunsch (Bestand: Standard keine Einsicht); (b) Postfach-Freigabe in der Liste „Was dürfen meine Eltern sehen?“; (c) Rundschreiben an Volljährige ohne Wahl; (d) Eltern-Einsicht je Kursraum durch Lehrkräfte abschaltbar und Material „nur für Schüler/innen“ (Wunsch, nicht Pflicht). Bis zur Entscheidung gilt: Standard „nein“, Zustellung `self`.
Abnahme: Entscheidung dokumentiert; Test je Entscheidung (Matrix SCH-007) angepasst.

**SCH-032** · P3 · Status: offen
Elternsprechtag online (Backlog B-48, „groß, später“): Sprechtag anlegen (Datum, Zeitfenster, Anmeldephase, Slotlänge 5 oder 10 min, Puffer, Raum je Lehrkraft, vor Ort oder online mit Link); Eltern sehen nur Lehrkräfte ihrer Kinder und buchen am Handy wie am PC; Doppelbuchungen ausgeschlossen (500 gleichzeitige Buchungen getestet); automatische Zuteilung mit Wunschlisten, Geschwistern im selben Block, Wegzeiten der Lehrkräfte; Lehrkräfte laden gezielt ein und sperren Slots; Laufzettel als PDF und iCal; wöchentliche Sprechstunde mit Buchung, Bestätigung, Absage. Dazu Elternbriefe mit Lesebestätigung, Rückmeldung und Einwilligungen (B-47) und Übersetzung per Klick (B-55) – ebenfalls „groß, später“.
Abnahme: Freischaltung mit 500 gleichzeitigen Buchungen → keine Doppelbuchung; Eltern zweier Kinder derselben Lehrkraft erhalten Slots im selben Block.

**SCH-033** · P3 · Status: offen
Kleine Familienfunktionen (Nutzen mittel bis hoch, Aufwand S–M): Stundenplan als PDF für Eltern (Woche je Kind, Klasse, Lehrkraft); Hausaufgaben-Übersicht für Eltern und Schüler/innen (eine Liste mit Fälligkeit aus Klassenbuch und Kursräumen); Kalender-Abo je Rolle und Kind (Klausuren, Termine, Ferien, Hausaufgaben; ein Feed je Kind statt nur des ersten); Nachrichtenvorlagen („Kind krank“, „Ausflug“); Lese-Status mit Namensliste und Erinnerung an Nicht-Leser.
Abnahme: PDF der Woche für Kind 2 enthält dessen Klasse; Hausaufgabenliste zeigt Aufgaben aus Klassenbuch und Kursräumen sortiert nach Fälligkeit; zwei Kinder ergeben zwei iCal-Feeds.

**SCH-034** · P3 · Status: offen
Nur auf Nachfrage (Entscheidung offen): Klassendienste (Tafel-/Ordnungsdienst mit Zeitraum und Rotation); Geburtstagsliste für die Klassenleitung (nur Tag und Monat, nur Klassenleitung, standardmäßig aus mit Schalter); QR-Login für Kinder (Zugangsbrief mit QR; Einmal-Token, Ablauf und Anmelderichtlinie vorher klären).
Abnahme: Geburtstagsliste ist standardmäßig aus; eingeschaltet zeigt sie nur Tag/Monat und nur der Klassenleitung der Klasse.

**SCH-035** · P3 · Status: offen
Mehrere Schulen je Konto: Eltern mit Kindern an zwei Schulen wechseln die Schule im Konto (benötigt gemeinsamen Login über mehrere Server; Nutzer 10-12, „später“); Kontowechsel zwischen Rollen (Lehrkraft und Elternteil) siehe Datei ANM.
Abnahme: Ein Eltern-Login zeigt nach Schulwahl nur Daten der gewählten Schule; Daten zweier Schulen vermischen sich nie.

**SCH-036** · P0 · Status: Ist
Löschung und Aufbewahrung schülerbezogener Daten (Fristen: Datei DAT): Eltern-Verknüpfungen, Freigaben (`parent_access`) und Einstellungen (`student_prefs`) werden 30 Tage nach Austritt gelöscht; ein Elternkonto (Rolle Eltern oder Schulbegleitung) ohne weiteres Kind wird mit seinen Daten gelöscht; Förder- und Unterstützungsdaten 30 Tage nach Austritt (keine laufende Frist); Atteste/Dokumente 400 Tage ab Erstellung bzw. 30 Tage nach Austritt; Protokollbezüge werden pseudonymisiert; Administrator-Konten werden nie gelöscht.
Abnahme: Person austragen, Wartefrist 30 Tage verstreichen lassen → `parent_links`, `parent_access`, `student_prefs`, `student_support` der Person sind weg, Elternkonto ohne weiteres Kind gelöscht, Admin-Konto unberührt.

**SCH-037** · P1 · Status: offen
Meldung „Stundenplan bei Schülern nicht sichtbar“ (Nutzer 10-12 18:03, Ursache unbekannt): vor Umsetzung Rückfrage an den Betreiber (Schüler oder Eltern, welche Seite, leer oder Fehler, Bildschirmfoto). Der Neubau stellt sicher, dass `GET /timetable/student/{id}` für Schüler/innen (eigene ID) und Eltern (verknüpftes Kind, freigegebene Bereiche) immer einen Plan oder einen klaren Leerzustand („Kein Stundenplan“) liefert.
Abnahme: Schüler mit zugeordneten Kursen sieht seinen Wochenplan; Schüler ohne Kurse sieht „Kein Stundenplan“ mit Grund statt leerer Seite.

---

## 4. Benachrichtigungen (BEN)

### 4.1 Anzeige: Glocke und Seite

**BEN-001** · P1 · Status: Ist
Glocke in der Kopfleiste (neben Farbschema und Kontomenü, für alle angemeldeten Konten, auch am Handy): Zähler der ungelesenen Meldungen; Antippen öffnet die letzten 10 Meldungen mit den Aktionen „Alle als gelesen“ und „Alle anzeigen und einstellen“. Jeder Eintrag zeigt Titel, Text, relative Zeit, eine Markierung für ungelesen und einen Link zur Zielstelle; der Link ist ein relativer Pfad der Anwendung und wird vor der Anzeige geprüft (keine fremden oder skriptartigen Adressen). Neue Meldungen erscheinen ohne Neuladen (BEN-022). Hell und Dunkel, Zähler mit Textalternative für Screenreader [unklar: Bestand nicht beschrieben].
Abnahme: Elternkonto mit 3 ungelesenen Meldungen zeigt „3“; Antippen listet 3 Einträge, „Alle als gelesen“ setzt den Zähler auf 0; Eintrag mit Link `https://fremd.example/…` wird nicht als Link angezeigt; am Handy (390 px) ist die Glocke bedienbar.

**BEN-002** · P1 · Status: Ist
Seite `/benachrichtigungen` (Menü Konto; angemeldet, keine Rechteprüfung): Liste gruppiert nach „Heute“, „Gestern“, „Diese Woche“, „Früher“ (optional nach Art); Filter „Ungelesen“; je Eintrag gelesen/ungelesen setzen oder löschen; „Gelesene löschen“; „Mehr“ lädt weitere Einträge; Klick führt zum Ziel und markiert als gelesen. Reiter „Einstellungen“ (BEN-009) und, mit Recht `settings.edit`, „Schulvorgaben“ (BEN-013). Schnittstellen: `GET /notifications?unread=&limit=&before=` (Liste, Zähler `unread`, Kennzeichen `more`), `GET /notifications/count`, `POST /notifications/read` (`{ids|null, read}`; ohne `ids` alle), `DELETE /notifications/{id}`, `DELETE /notifications?read=1`.
Abnahme: Liste zeigt Gruppen; Filter „Ungelesen“ blendet gelesene aus; „Gelesene löschen“ entfernt nur gelesene; Klick auf Eintrag springt zur Zielseite und der Eintrag gilt als gelesen; Konto ohne `settings.edit` sieht den Reiter „Schulvorgaben“ nicht.

### 4.2 Arten, Auslöser, Empfänger

**BEN-003** · P1 · Status: Ist
Ereignisarten (`kind`) mit Auslöser und Empfängern:

| Art | Auslöser | Empfänger |
|---|---|---|
| `substitution` | Vertretung, Entfall, Verlegung oder Raumänderung (Vergleich des Vertretungsplans; nur bedeutsame Änderungen) | betroffene Lehrkraft; Schüler/innen der Klasse bzw. des Kursteils; deren Eltern |
| `duty` | Aufsicht im Vertretungsplan geändert | betroffene Lehrkraft |
| `absence` | Krankmeldung eingegangen (Anlegen), bestätigt oder nicht entschuldigt (Statusänderung) | Klassenleitung und Sekretariat (bei „eingegangen“); Familie (bei „bestätigt“ oder wenn die Schule erfasst) |
| `attest_missing` | Erinnerung „Attest fehlt“ (stündlicher Wartungslauf), einmal je Meldung | Familie |
| `request_decided` | Formular genehmigt/abgelehnt/erledigt; Antrag bzw. Ausnahme einer Lehrkraft entschieden | einreichende Person (plus Familie) bzw. Lehrkraft |
| `course_item` | neue Aufgabe oder neues Material (sofort sichtbar) | Schüler/innen des Kursraums plus Eltern (nicht die Lehrenden) |
| `task_graded` | Abgabe bewertet oder zur Überarbeitung zurückgegeben | Schüler/in (plus Eltern, Bereich „Noten“); ohne Note und Rückmeldung im Text |
| `task_due` | „Aufgabe ist morgen fällig“ (Wartungslauf), einmal je Aufgabe und Konto, nur ohne Abgabe | Schüler/innen plus Eltern |
| `exam` | Klausur angesetzt, verschoben oder abgesagt (nur bei Änderung von Datum oder Stunde) | Kursteilnehmende, Eltern, Lehrkräfte des Kurses |
| `plan_proposal` | Plan-Prüfung hat einen Vorschlag zur Entscheidung | Konten mit `timetable.generate`, `timetable.edit` oder `settings.edit` |
| `message` | (keine Quelle angebunden; Art existiert, damit die Wahl „auch Nachrichten“ später greift) | – |

Bewusst **nicht** ausgelöst: zeitlich freigegebene Kursraum-Inhalte beim Freischalten; verborgene Inhalte. Kindbezogene Meldungen an Eltern tragen den Hinweis „für <Kind>“.
Abnahme: Raumänderung im Vertretungsplan → je eine Meldung an Lehrkraft, Schüler/innen des Kursteils und deren Eltern; Aufgabe erstellen → Meldung an Schüler/innen und Eltern, nicht an die Lehrkraft (Auslöser); Klausur ohne Datums-/Stundenänderung erneut speichern → keine Meldung.

**BEN-004** · P2 · Status: Ist
Vorab angelegte Arten für andere Bereiche: `assignment` und `group` (Aufgaben, Gruppen), `progress` (Lernfortschritt), `poll` und `selftest` (Abstimmung, Selbsttest), `gradebook` (Notenbuch), `competence` (Kompetenzen). Eine neue Art wird angemeldet mit Schlüssel, Beschriftung, Bereich (Gruppe), Standard-Wahl, Hilfetext und Voraussetzung, dazu eine Empfängerregel und ein Auslöser im Fachbereich. Unbekannte Arten funktionieren trotzdem: Sie werden als „Sonstiges“ mit Standard „In der App“ gespeichert, erscheinen aber nicht in den Einstellungen. Es gibt getrennte Artenlisten für Schüler/Eltern und Lehrkräfte.
Abnahme: Meldung mit Art `xyz` wird gespeichert und in der Liste als „Sonstiges“ angezeigt; in den Einstellungen fehlt sie; nach Anmeldung der Art (mit Beschriftung) erscheint sie dort.

**BEN-005** · P0 · Status: Ist
Erzeugen einer Benachrichtigung: Angaben sind Empfängerkonten, Art, Titel (ohne sensible Einzelheiten), Ziel als relativer Pfad, optionaler Text, optional das betroffene Kind (Eltern sehen „für <Kind>“), optionaler Deduplizierungsschlüssel (dieselbe Meldung je Konto nur einmal), optional Auslöser (er erhält nichts) und freie Referenz. Inaktive Konten und der Auslöser werden still übersprungen. Die Meldung entsteht **nach dem Speichern** der Fachänderung; ein Fehler beim Erzeugen darf den Fachvorgang nie verhindern oder abbrechen (er wird nur protokolliert). Empfängerhilfen: alle Lehrkräfte, alle Schüler/innen, Eltern je Kind, Familie eines Kindes (Schülerkonto plus Eltern; volljährige nur mit Freigabe), Konten mit einem bestimmten Recht.
Abnahme: Auslöser ist gleichzeitig Empfänger → erhält keine Meldung; derselbe Dedupe-Schlüssel zweimal → eine Meldung je Konto; erzwungener Fehler im Erzeugen (z. B. Zieldatenbank gesperrt) → Fachvorgang (z. B. Krankmeldung) wird trotzdem gespeichert, Fehler steht im Fehlerprotokoll.

**BEN-006** · P0 · Status: Ist
Eltern erhalten Meldungen je Kind mit „für <Kind>“; bei **volljährigen** Kindern nur, wenn der betreffende Bereich über `parent_access` freigegeben ist (Stundenplan, Krankmeldungen, Kursräume, Noten, Dokumente); ohne Freigabe entsteht keine Meldung. Keine Meldungen über andere Kinder. Bei mehreren Kindern ist die Zuordnung eindeutig.
Abnahme: Volljährige Schülerin ohne Freigabe „Noten“ → `task_graded` erzeugt keine Meldung an Eltern, aber an die Schülerin; mit Freigabe → Meldung „für <Kind>“ ohne Note im Text.

**BEN-007** · P0 · Status: Ist
Inhalte: Titel und Text enthalten nie Noten, Gründe, Diagnosen oder Kommentare (z. B. „Neue Krankmeldung“ ohne Grund, „Abgabe bewertet“ ohne Note); Titel und Text sind verschlüsselt gespeichert (BEN-008). Gilt für App, E-Mail und künftige Push-Meldungen (ohne Namen anderer Kinder, ohne Gesundheitsdaten).
Abnahme: Alle Auslöser der Tabelle BEN-003 erzeugen Texte, die in einem Textsuchtest weder „Note“-Werte noch Krankheitsgründe enthalten (Stichproben je Art); Direktzugriff auf die Tabelle zeigt nur Chiffrat in Titel/Text.

### 4.3 Daten, Einstellungen, Zustellung

**BEN-008** · P0 · Status: Ist
Datenmodell: `notifications` (`id`, `user_id` [Kaskade beim Löschen des Kontos], `kind` ≤ 40, `title_enc`, `body_enc` [verschlüsselt, Kontext `notifications.title:<id>` / `notifications.body:<id>`], `link` ≤ 300, `student_id` [betroffenes Kind, Klartext-Personenbezug], `ref` ≤ 80, `dedupe_key` ≤ 64, `created_at`, `read_at` [leer = ungelesen], `mail_state` ∈ „“ keine Mail | `sent` sofort versandt | `later` wartet auf Ende der Ruhezeit | `digest` wartet auf Tageszusammenfassung | `digested` in ihr versandt); eindeutig (`user_id`, `dedupe_key`), Indizes `user_id`, `created_at`, (`user_id`, `read_at`). `notification_prefs` (`user_id`, `kind`, `mode` ∈ aus | app | mail, Standard `app`; eindeutig je Konto+Art). `notification_user_settings` (`user_id`, `digest` [nein], `digest_sent_on`, `quiet_enabled` [nein], `quiet_from` „21:00“, `quiet_to` „07:00“, `updated_at`). `notification_school` (`kind`, `mode` [app], `locked` [nein], `updated_at`). `notification_config` (Schlüssel/Wert, z. B. `retention_days`). Alle personenbezogenen Zeilen werden beim Löschen des Kontos entfernt.
Abnahme: Neues Konto ohne Einstellungen → Standard `app` je Art, Ruhezeit aus (21:00–07:00 vorbelegt); Konto löschen entfernt Meldungen, Einstellungen und Zusammenfassungsstand; Dedupe-Schlüssel doppelt → Eindeutigkeit verhindert die zweite Zeile.

**BEN-009** · P1 · Status: Ist
Einstellungen je Person (Reiter „Einstellungen“): je Art **Aus | In der App | In der App und per E-Mail** (`GET`/`PUT /notifications/settings`; jedes angemeldete Konto ändert nur die eigenen). Wirksamkeit von oben nach unten: (1) gesperrte Schulvorgabe, (2) eigene Wahl, (3) Schulvorgabe, (4) Voreinstellung der Art (meist „In der App“; Art `message` „Aus“). Eine Art, die die Schule zur Pflicht gemacht hat, lässt sich nicht abschalten (Schalter gesperrt). Jede Art hat einen Hilfetext (i-Symbol).
Abnahme: Person wählt `substitution` = Aus → keine Meldung; Schule sperrt `substitution` auf „In der App“ → die Wahl „Aus“ ist nicht möglich und eine frühere Wahl wirkt nicht; neue Art ohne Wahl → Voreinstellung.

**BEN-010** · P1 · Status: Ist
E-Mail-Zustellung nur, wenn der Versand eingerichtet ist (SMTP und Versanddienst) **und** das Konto eine Adresse hat; sonst bleibt es bei „In der App“ und die E-Mail-Option ist ausgegraut (mit Hilfetext, warum). Lehrkraft-Adressen legt die Schule manuell an (LEH-002). Die Zustellung läuft über die verschlüsselte Mail-Warteschlange (BEN-016).
Abnahme: Ohne eingerichtetes SMTP ist „In der App und per E-Mail“ ausgegraut; Konto ohne E-Mail-Adresse ebenfalls; mit Versand und Adresse wählbar.

**BEN-011** · P1 · Status: Ist
Tägliche Zusammenfassung (`digest`): statt einzelner Mails eine Mail pro Tag, frühestens 07:00 Uhr Ortszeit, nur ungelesene Meldungen; Stand je Konto `digest_sent_on`; Meldungen warten mit `mail_state` `digest` und gelten danach als `digested`. Die Versandstunde ist fest 07:00 [kein Nutzerfeld].
Abnahme: `digest` an, drei Meldungen tagsüber → keine Einzelmail, um 07:00 des Folgetags eine Mail mit nur den noch ungelesenen; bereits gelesene Meldungen fehlen darin.

**BEN-012** · P1 · Status: Ist
Ruhezeiten (`quiet_enabled`, `quiet_from` 21:00, `quiet_to` 07:00; Zeiten `HH:MM`, auch über Mitternacht): in der Ruhezeit werden **keine E-Mails** versandt; sie gehen danach gesammelt (`mail_state` `later`) raus; in der App erscheint alles sofort. Die Eingabe wird validiert (ungültige Uhrzeit → Fehler am Feld).
Abnahme: Ruhezeit 21:00–07:00, Meldung um 22:30 → App sofort, Mail um 07:00; „25:00“ → Fehlermeldung am Feld; Ruhezeit aus → Mail sofort.

**BEN-013** · P1 · Status: Ist
Schulvorgaben (Reiter „Schulvorgaben“, Recht `settings.edit`; `GET`/`PUT /notifications/school`): je Art Standardzustellung (aus | app | mail), **Pflicht** (gesperrt, gilt für alle, nicht änderbar) und schulweite Aufbewahrung in Tagen (Bereich 7 bis 730, Standard 90). Die Schulvorgabe überschreibt die persönliche Einstellung bei Pflicht. Änderungen werden im Audit protokolliert (`notification_school.update`, ohne Inhalte). Eine zu kurze Aufbewahrung führt zum vorzeitigen Löschen von Meldungen.
Abnahme: Aufbewahrung 5 → 422 (Bereich 7–730); Pflicht für `exam` gesetzt → Personen können `exam` nicht abschalten; Audit-Eintrag `notification_school.update` ohne Werte der Texte; Konto ohne `settings.edit` → 403.

**BEN-014** · P0 · Status: Ist
Aufbewahrung und Aufräumen: Der stündliche Wartungslauf (`SM_MAINTENANCE_INTERVAL`, Standard 3600 s) löscht Meldungen, die älter als die Aufbewahrung sind (Standard **90 Tage**; 7 bis 730), erledigt Erinnerungen und zurückgestellte E-Mails. Nach Austritt einer Person werden ihre Meldungen und Einstellungen nach 30 Tagen gelöscht (Datei DAT). Das eigene Löschen einer Meldung wirkt sofort und ist eine dokumentierte Ausnahme ohne Audit; die automatische Löschung bleibt ebenfalls ohne Audit. Die Auskunft enthält höchstens 5.000 Benachrichtigungen. [unklar: Bestandsnotizen nennen teils 30 Tage Löschfrist; maßgeblich ist die Schulvorgabe, Standard 90 Tage.]
Abnahme: Meldung mit Alter 91 Tage (Standard) wird im nächsten Lauf gelöscht, eine mit 89 Tagen nicht; nach Änderung der Aufbewahrung auf 30 Tage fallen ältere Meldungen weg; Löschfunktionen erzeugen keinen Audit-Eintrag mit Inhalt.

**BEN-015** · P2 · Status: Ist
Erinnerungen im Wartungslauf: `attest_missing` (Attest fehlt) genau einmal je Meldung an die Familie; `task_due` („Aufgabe ist morgen fällig“) genau einmal je Aufgabe und Konto, nur wenn keine Abgabe vorliegt; zurückgestellte E-Mails nach Ende der Ruhezeit; Tageszusammenfassung.
Abnahme: Zwei Wartungsläufe am Vortag der Frist → eine einzige Erinnerung je Konto; Abgabe vorhanden → keine Erinnerung.

**BEN-016** · P1 · Status: Ist
Mail-Warteschlange (`notifications_outbox`): `kind` ∈ email | webhook, `target`, `subject`, `payload` (E-Mail verschlüsselt, Webhook JSON), `status` ∈ pending | sending | sent | failed, `attempts`, `next_attempt_at`, `last_error`, `dedupe_key`, `created_at`, `sent_at`. Wiederholung bei Fehlern mit wachsender Wartezeit bis zu einer Obergrenze, maximale Versuche und HTTP-Zeitlimit [unklar: Werte]. Hintergrunddienst startet und stoppt mit dem Server, sein Status ist abfragbar und er lässt sich sofort anstoßen; `SM_NOTIFY_DISPATCHER` = 0 schaltet den Mailversand aus (auf der Hauptinstanz aus). Verwaltung der Warteschlange: Liste und „Erneut versuchen“ (`GET /notifications/outbox`, `POST …/{id}/retry`; Recht `settings.edit` oder `system.admin`). Abgeschlossene Zeilen werden nach einer Frist gelöscht [unklar: Frist]. Passwort-vergessen-Optionen erscheinen erst bei eingerichtetem Versand.
Abnahme: SMTP nicht erreichbar → Zeile `pending` mit steigendem `attempts` und späterem `next_attempt_at`, später `sent`; nach maximaler Versuchszahl `failed` mit `last_error`; `SM_NOTIFY_DISPATCHER=0` → keine Mails, Meldungen in der App bleiben.

### 4.4 Abmelden, Kennzeichnung, Rundmail, SMS

**BEN-017** · P0 · Status: Ist
Abbestellen automatischer E-Mails: Jede automatische Mail enthält einen **signierten Abmeldelink** (an Konto und Bereich gebunden; kein Ablaufdatum; ohne Anmeldung nutzbar). `GET /unsubscribe/{token}` zeigt nur die Bestätigungsseite und meldet **nicht** ab; erst `POST` führt die Abmeldung aus. Bereiche: `substitution` (Vertretungs-Rundmail, Art `substitution_mail`, Standard `mail`; abgemeldet = keine Rundmail mehr), `messages` (E-Mail-Benachrichtigung bei neuen Nachrichten, Einstellung `email_notify`), `notifications` (alle Arten mit Mail-Zustellung werden auf „In der App“ gestellt). Die Mails tragen Abmelde-Kopfzeilen für die Ein-Klick-Abmeldung (`List-Unsubscribe`, RFC 2369 und 8058). **Pflicht-Mails** (von der Schule gesperrte Arten) enthalten keinen Abmeldelink; von der Schule gesperrte Arten bleiben bei einer Abmeldung unverändert. [offen: Sicherheitsfrage – Link ohne Ablaufdatum; Widerruf bei Missbrauch nicht beschrieben.]
Abnahme: Abmeldelink im Browser öffnen (GET) ändert nichts, Bestätigen (POST) stellt die Mail-Arten auf „In der App“; Link mit verändertem Token → 404; Pflicht-Art bleibt auf „Mail“; Pflicht-Mail enthält keinen Link.

**BEN-018** · P0 · Status: Ist
Automatische Mails sind als automatisch gekennzeichnet (Kopfzeile für automatisch erzeugte Nachrichten), damit Mailprogramme keine Abwesenheitsnotizen zurückschicken; es gibt keine Auto-Antwort an Eltern (LEH-032). Test-Mails gehen nur an `example.org`; der Test-Postausgang ist standardmäßig aus (live aus); die Zuschauer-Rolle hat keinen Zugriff auf den Postausgang (Namen in Betreffzeilen).
Abnahme: Mail-Kopf enthält die Auto-Kennzeichnung; Zuschauer-Konto `GET /notifications/outbox` → 403/404; im Dev-Modus gehen Test-Mails nur an `example.org`.

**BEN-019** · P2 · Status: Ist
Vertretungs-Rundmail (Bereich `substitution`): bei bedeutsamen Änderungen des Vertretungsplans Mail an abonnierte Personen; Einstellung „aus“ = keine Rundmail; die Auswertung berücksichtigt die E-Mail-Einstellung und die Vertretungsvorschläge; Abmeldelink (BEN-017). Inhalte ohne Namen von Schüler/innen und Gründe (BEN-007).
Abnahme: Plan-Änderung → Mail nur an Abonnenten mit Einstellung „mail“; Abmeldung stoppt weitere Mails; Konten mit „aus“ erhalten keine.

**BEN-020** · P2 · Status: Ist
SMS: nur wenn konfiguriert (Umgebungsvariablen); Gateways Twilio-kompatibel und seven.io, außerdem Webhook; Zustellung über den Postausgang mit der Art `sms`. Telefonnummern werden normalisiert (E.164, Standard-Ländervorwahl [unklar]) und auf Plausibilität geprüft; Anzeige maskiert, gespeichert verschlüsselt (`user_contacts.phone_enc`) und als Hash (`phone_hash`, HMAC) nur zur Suche; maximale Textlänge [unklar]. Planungswert Kosten seven.io ca. 7 bis 10 Cent je SMS. Nutzung vor allem für Bestätigungscodes (Datei ANM); Notfall-SMS siehe BEN-032.
Abnahme: Nummer „0171 1234567“ wird zu E.164 normalisiert; Anzeige „+49 171 ••••567“; ohne Konfiguration ist keine SMS-Option sichtbar.

### 4.5 Rechte, Echtzeit, Abgrenzung

**BEN-021** · P0 · Status: Ist
Rechte und Protokoll: Kein neues Recht – jedes angemeldete Konto verwaltet die **eigenen** Benachrichtigungen; fremde Meldungen sind nie sichtbar (fremde ID → 404, Aktion wirkungslos). Schulvorgaben `settings.edit`. Audit: Änderung eigener Einstellungen `notification_settings.update` (Rechtename einheitlich, kein Recht nötig), Schulvorgaben `notification_school.update`, jeweils ohne Inhalte. Benachrichtigungen sind nicht Teil der offenen API (`/api/v1/open`), weil personenbezogen.
Abnahme: `DELETE /notifications/{id}` einer fremden Meldung → 404 und sie bleibt bestehen; API-Token mit Umfang „offen“ kann `/notifications` nicht lesen; Audit-Eintrag je Einstellungsänderung.

**BEN-022** · P1 · Status: Ist
Echtzeit: Die Oberfläche abonniert Änderungen über die gemeinsame Ereignisverbindung (`/api/v1/events`, Ereignis `change`, Bereich `notifications`, nur an die Empfänger); bei nicht offener Verbindung fragt die Glocke einmal pro Minute ab. Der Live-Hinweis entsteht erst nach dem Speichern des auslösenden Vorgangs. Die Ereignisverbindung wird bei erzwungenem Passwortwechsel, ausstehender Zwei-Faktor-Einrichtung oder Verknüpfungszwang nicht ausgeliefert (Datei SIC).
Abnahme: Auslöser speichert → Glocke des Empfängers zeigt die Meldung ohne Neuladen; bei getrennter Verbindung aktualisiert sich der Zähler binnen 60 s; Meldung eines fremden Kontos erreicht den Browser nicht.

**BEN-023** · P1 · Status: Ist
Abgrenzung zu Nachrichten: Chats und Postfach behalten eigenen Zähler und den Eintrag „Nachrichten“; die Glocke zeigt Systemereignisse. Die Art `message` ist standardmäßig aus und erscheint in der Glocke nur, wenn die Person sie einschaltet (Quelle noch nicht angebunden, BEN-027).
Abnahme: Neue Chat-Nachricht erhöht den Nachrichten-Zähler, nicht die Glocke; Menü zeigt den Zähler ungelesener Nachrichten.

**BEN-024** · P2 · Status: Ist
Weitere Hinweise: Plan-Prüfung-Vorschläge erscheinen als Live-Hinweis, Zähler und Kachel (nicht per E-Mail) und als Meldung `plan_proposal`; jede Aktion an einer Krankmeldung benachrichtigt die Klassenlehrkraft; Lizenz-Vorwarnung zum Abo-Ende 30, 14, 7 und 1 Tag vorher als Banner und Glocke für Administration und Schulleitung (Datei BET).
Abnahme: Krankmeldung eingegangen → Klassenlehrkraft erhält `absence`; 14 Tage vor Abo-Ende erscheint für Schulleitung ein Banner und eine Glocken-Meldung.

**BEN-025** · P1 · Status: Ist
Ungelesene Nachrichten (z. B. von Lehrkräften) erscheinen als Liste auf der Startseite (zusammen mit der Zusammenführung von „Start“ und der früheren „Meine Übersicht“) und als Zähler im Menü. Nutzer 10-11: Ungelesene Benachrichtigungen bzw. Nachrichten „als Liste an Nachrichten“ zeigen. Vollständigkeit der Liste ungelesener Benachrichtigungen ist zu prüfen [offen].
Abnahme: Schüler mit 2 ungelesenen Nachrichten sieht beide in der Startseitenliste und „2“ am Menüpunkt; nach Lesen verschwinden sie.

### 4.6 Zurückgestellt und offen

**BEN-026** · P0 · Status: offen
App-Option und Push-Benachrichtigungen sind **vorerst nicht Teil** des Umfangs (Nutzer 10-13 20:14: „die app option mus noch nicht mit rein“). Die Glocke mit Einstellungen je Ereignis ist davon getrennt und gebaut. Später („groß“, Backlog B-41): installierbare App (Manifest, Symbole, Service Worker; Android, iOS ab 16.4, Desktop; zuletzt geladener Stundenplan offline lesbar), Web Push (VAPID-Schlüssel vom Server erzeugt, Abo je Gerät, widerrufbar; Meldungen bei Vertretung, Entfall, Raumänderung in eigenen bzw. Kind-Stunden von heute und morgen, bei neuer Nachricht und Krankmeldung der eigenen Klasse), je Person einstellbar, Ruhezeiten (z. B. 20–6 Uhr, außer für heutigen Unterricht), Inhalte ohne Gesundheitsdaten und ohne Namen anderer Kinder („Änderung im Plan für morgen“), Versand an 2.500 Abos unter 30 s. [unklar: „kein Drittanbieter“ – Browser-Push läuft technisch über Dienste der Browserhersteller.]
Abnahme: Der Neubau enthält ohne ausdrückliche Freigabe weder Service Worker noch Push-Abonnement; Glocke und Einstellungen funktionieren davon unabhängig.

**BEN-027** · P1 · Status: offen
Fehlende Auslöser: (a) Chat- und Postfach-Nachrichten in der Glocke (Art `message`; benötigt einen Systemabsender im Postfach); (b) Kursraum-Inhalte, die zeitlich freigegeben werden, melden beim Freischalten nichts („Benachrichtigung, wenn ein Kursraum-Element frei wird“); (c) Nachschreibtermine: die Lehrkraft, die die Klausur im Fach gehalten hat, erhält eine Benachrichtigung, dass Nachschreiben anstehen (Nutzer 10-12: „die müssen das noch machen“), ebenso Eltern/Schüler bei angesetztem Termin; (d) Beurlaubungsantrag geht an die Klassenlehrkraft („auch an die Lehrer in den Klassen“) mit Startkachel „offene Anträge“; (e) Volljährigkeit der Person; (f) Ampel-Überschreitung der Fehlzeiten an Klassenleitung und Sekretariat; (g) Aufsichts-Neuberechnung meldet bisher nur über den Vergleich des Vertretungsplans.
Abnahme: Nachschreibtermin ansetzen → Meldung an Lehrkraft (Postfach/Glocke) und an betroffene Familie; Beurlaubungsantrag → Meldung an Klassenlehrkraft; zeitlich freigegebenes Material → Meldung beim Freischalten.

**BEN-028** · P2 · Status: offen
Benachrichtigungs-Feinschliff (Paket W2-13): Neutral-Mail als Schulvorgabe (kein Name im Text der Mail, nur „Sie haben eine neue Meldung“); Rechte für Einstellungen einheitlich festlegen (kein eigenes Recht; Audit-Aktion `notification_settings.update`); keine N+1-Abfragen bei Listen; stille Fehlerbehandlung (leere Ausnahmen) wird protokolliert; Benachrichtigungen für Nachschreibe-Termine an Eltern und Schüler und Ampel-Überschreitung (W4-06).
Abnahme: Schulvorgabe „Neutral-Mail“ an → Mail-Text enthält keinen Personennamen; Fehler beim Erzeugen einer Meldung erscheint im Fehlerprotokoll.

**BEN-029** · P1 · Status: offen
Versand von E-Mail und SMS einrichten: Administration/Betreiber tragen Mailkonto-Daten (Server, Port, Absender, Zugang) in der Konfiguration bzw. künftig in der Oberfläche (Einstellungen › Schnittstellen) ein und schalten den Versand ein; Passwörter werden verschlüsselt gespeichert und nie wieder angezeigt; Umgebungsvariablen haben Vorrang und sind als „vom Server vorgegeben“ gekennzeichnet; Testversand mit verständlicher Fehlermeldung; optionaler SMS-Anbieter. Offen: Test-Postausgang-Standard im Code härten (live aus); SMTP läuft nicht über die Netzschutz-Prüfung (nur Betreiber-Ziele; Audit-Befund niedrig); Lizenzserver als Empfänger in der Datenschutz-Vorlage. Zugangsdaten trägt nur der Betreiber selbst ein, nie ein Entwicklungswerkzeug.
Abnahme: Einstellungen › Schnittstellen: Testmail an eine Adresse liefert „gesendet“ bzw. eine verständliche Fehlermeldung; gespeichertes Passwort erscheint nie im Klartext in Oberfläche, Protokoll oder Export.

**BEN-030** · P3 · Status: Ist
Teil-Demo Benachrichtigungen: Die Demo legt erfundene Benachrichtigungen für die Glocke an (für Eltern, Schüler/in, Lehrkraft); sie enthalten keine echten Personendaten.
Abnahme: Demo-Konto `eltern` sieht nach Laden der Demo mindestens eine Meldung je Art `substitution`, `absence`, `task_due`.

**BEN-031** · P2 · Status: offen
Bedienung der Kopfleiste: Der Betreiber beanstandete am 10-16 Bedienfehler bei Live-Anzeige, Glocke und Hell/Dunkel („… lassen sich falsch anklicken“; Satz abgebrochen, Beschwerde unbeantwortet). Klärung mit dem Betreiber; bis dahin gilt: Trefferflächen mindestens 44 px, Abstand zwischen Glocke, Farbschema und Kontomenü, Tastaturbedienung und sichtbarer Fokus.
Abnahme: Alle Kopfleisten-Elemente haben mindestens 44 × 44 px Trefferfläche und sind per Tastatur erreichbar; Browser-Rundgang bei 390 px und 1280 px ohne Fehlklick.

**BEN-032** · P3 · Status: offen
Erweiterungen (Wunsch): Notfall-SMS; Ruhezeiten für Lehrkräfte (Nachrichten außerhalb des Dienstes); Benachrichtigung, wenn ein Kursraum-Element frei wird (BEN-027 b); Chat-/Postfach-Benachrichtigung mit Systemabsender; Lese-Status mit Namensliste und Erinnerung an Nicht-Leser (Nachrichten, Datei NAC).
Abnahme: Notfall-SMS wird nur nach ausdrücklicher Auslösung durch berechtigte Rolle versandt und im Audit protokolliert (ohne Text).

---

## 5. Entscheidungsbedarf und Widersprüche im Bestand

Der Neubau übernimmt bis zur Entscheidung den jeweils genannten Vorschlag und markiert die Stelle im Code als „Entscheidung offen“.

| Nr | Frage / Widerspruch | Betrifft | Vorschlag bis zur Entscheidung |
|---|---|---|---|
| 1 | Einrichtung: 12 oder 13 Schritte (Schritt „Impressum und Datenschutz“ wird nicht eindeutig mitgezählt) | STA-062 | Schrittzahl nicht normativ; Fachschritte 2–13 plus ergänzende Schritte |
| 2 | Wochen 1–52 oder 1–53 (KW 53 existiert nicht jedes Jahr) | STA-049, STA-055 | intern 1–52; KW-Anzeige mit Hinweis „fehlt“ |
| 3 | Aufbewahrung der Benachrichtigungen: Notizen nennen 30 und 90 Tage | BEN-014 | Schulvorgabe 7–730 Tage, Standard 90; 30 Tage nach Austritt |
| 4 | Anrede „du“ im Schülerprofil gegen Projektregel „siezt“ | SCH-027 | Sie überall (entschieden) |
| 5 | Bereiche der Elternfreigabe: Profil bietet 4, Doku nennt 6 bzw. 7; Postfach-Freigabe fehlt | SCH-006, SCH-031 | 7 Bereiche, Postfach nach Entscheidung |
| 6 | Dürfen Sekretariate Lehrkraft-Anträge genehmigen (Frage 10-13 unbeantwortet; „ein einziger Schalter in der Rechte-Matrix“) | LEH-008 | nein |
| 7 | Deputat im Lehrkraft-Profil: entfernen oder als Wunsch `requested_max_hours` behalten | LEH-023 | Deputat entfernen, Wunsch-Feld behalten |
| 8 | Geburtsdatum durch Schüler/in selbst änderbar? | SCH-003 | nein |
| 9 | Rundschreiben an Volljährige ohne Wahl: nur Schüler/in oder beide | SCH-008 | nur Schüler/in |
| 10 | Obergrenze Schülerliste je Eingabe: 60 (Prüfung) gegen 500 (Schema) | STA-041 | ein gemeinsamer Wert, Betreiber legt fest |
| 11 | Mehrere Klassenleitungen (Bestand: genau eine, fest verdrahtet an mindestens 16 Stellen) | STA-043, STA-044 | Liste mit Reihenfolge |
| 12 | Jahrgangszuordnung beim Hochstufen (Bestand: Stufe steigt, Jahrgang bleibt) | STA-082 | Folgejahrgang zuweisen oder melden |
| 13 | Welche Rechte braucht der Schuljahreswechsel (alle drei oder eines) | STA-081 | `settings.edit` und `masterdata.edit` und `users.manage` |
| 14 | Darf die Administration (`teacher_requests.review` im Standard) Freitexte von Lehrkraft-Anträgen sehen | LEH-026 | nein |
| 15 | Doppelstunden-Standard: Backlog nennt `doubles_across_breaks` „Standard aus“, Ziel ist „nie über Pausen“ | STA-051 | `double_alignment` = `bloecke` |
| 16 | „Zählung für Schuljahr ab Woche 1 des Kalenderjahrs“ – Bedeutung nicht bestätigt | STA-049 | KW-Anzeige mit Umschalter |
| 17 | Fächer „Mugs“/Schrägstrich-Fächer – Beispiel fehlt | STA-091 | Rückfrage |
| 18 | Missbrauchsschutz der Testmail (frei wählbarer Empfänger) | STA-066 | nur an Adresse des angemeldeten Kontos |
| 19 | Abmeldelink ohne Ablaufdatum – Widerruf bei Missbrauch | BEN-017 | Widerrufsliste je Konto |
| 20 | Recht zur Neuplanung einer fremden Lehrkraft | LEH-024 | `timetable.generate` |
| 21 | Abschluss der Einrichtung an Vollständigkeit gebunden | STA-063 | nein, Zusammenfassung zeigt Fehlendes |
| 22 | Ob Hauptinstanz wieder komplett geleert wird (Angebot) | STA-069 | Betreiber entscheidet |
| 23 | Erlaubte Statusübergänge bei Dokumenten und Anträgen; Wirkung `support_catalog.active`; `applied_version` | SCH-015, SCH-022, LEH-004 | Übergänge nur wie beschrieben, Rest nach Entscheidung |

---

## 6. Querverweise auf andere Dateien des Pakets

- **STP** Stundenplan/Generator: Raster, Doppelstunden, Gewichte, Wochenlogik-Auswertung, Stundentafel-Konflikte im Generator. **VER** Vertretung/Aufsichten/Monitore: Abwesenheiten, Vertretungsplanung, Plan-Prüfung, Rundmail. **KLB** Klassenbuch/Fehlzeiten/Atteste: Prüfung von Dokumenten, Entschuldigung, Nachschreiben, Attestschwelle `sick_note_after_days`. **NOT** Noten/Kompetenzen/Klausuren: Klausur-Grenzen, Nachteilsausgleich-Hinweis in der Klausur. **KUR** Kursräume: Eltern-Einsicht je Raum, Archivierung beim Jahreswechsel. **NAC** Nachrichten: Postfach-Empfängerregeln, Lese-Status. **FOR** Formulare/Briefe/Zugangsdaten: Beurlaubung, Zugangsbriefe, Antrag Nachteilsausgleich.
- **REC** Rechte/Rollen: vollständiger Rechte-Katalog, Umfänge, eigene Rollen. **ANM** Anmeldung/SSO/Konten: Passwortregeln, Zwei-Faktor für Lehrkräfte und Administration, Kontenwechsel, Einmal-Anmeldelink. **DAT** Datenschutz: Löschfristen, Warteliste, Verschlüsselung, Auskunft. **INT** Integrationen: CSV/Untis/JSON/iCal/API. **BET** Betrieb/Lizenz: Betriebsmodus, Demo, Lizenz-Vorwarnung, Sicherung. **OBE** Oberfläche: Hilfe-Symbol, Raster, Texte. **SIC/REH/QUA**: Sicherheitsquerschnitt, Recht, Abnahme.

<!--ENDE-->
