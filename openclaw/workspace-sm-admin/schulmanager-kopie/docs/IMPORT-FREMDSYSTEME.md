# Import aus Fremdsystemen – Stand, Tests, Messwerte, Empfehlungen

Stand 16.10.2026. Auftrag: Daten aus Moodle und gängigen Schulsystemen in die Datenbank übernehmen, mit Testdatenbanken nach
dem echten Schema, Trockenlauf, Idempotenz, Protokoll und Rückgängig. Alle Testpersonen sind erfunden
(`tests/fixtures/fremdsysteme/welt.py`).

## 1. Bestand und Lücken (vorher)

Vorhanden waren: Untis-GPU (001–006, 010, 014, 015, Import und Export), Schulmanager-Online-Paket (nur Export, ZIP mit
GPU + CSV), CSV-Import/-Export für Lehrkräfte, Klassen, Räume, Fächer, Schüler/innen, Stunden, Stundentafeln mit Presets
SchILD-NRW, ASV, LUSD, Magellan, Notenexport (SchILD/ASV/LUSD), iCal, Webhooks. Fehlte: Übernahme von **Lerninhalten**
(Kursräume, Aufgaben, Abgaben, Bewertungen, Selbsttests, Kompetenzen), Moodle, OneRoster, WebUntis, jeglicher
Trockenlauf über Dateiarten hinweg, Idempotenz über Läufe, Protokoll und Rückgängig. Der CSV-Import hat das Geburtsdatum
nur zur ID-Bildung gelesen und **nicht gespeichert** (behoben, siehe §5).

## 2. Was gebaut wurde

| Baustein | Ort |
|---|---|
| Neutrales Austauschmodell `Bundle` | `schulmanager/integrations/fremd/model.py` |
| Leser: Moodle-DB, Moodle-`.mbz`, OneRoster (lesen + schreiben), WebUntis-JSON, Personenlisten-CSV | `integrations/fremd/{moodle_db,moodle_mbz,oneroster,webuntis,csv_persons}.py` |
| Formaterkennung, ZIP-Grenzen | `integrations/fremd/registry.py` |
| Personenzuordnung (Konfliktbericht) | `integrations/fremd/match.py` |
| Anwendungsschicht (Trockenlauf, Idempotenz, Protokoll, Rückgängig) | `server/import_fremd.py`, `server/import_fremd_rooms.py` |
| Tabellen `import_runs`, `import_links` (Migration `0047_import_fremd`, `down_revision = 0042_merge_lernen`) | `server/feature_models/import_fremd.py` |
| API | `server/routes/features_import_fremd.py` |
| Fixtures + Generatoren | `tests/fixtures/fremdsysteme/` |
| Tests | `tests/test_import_fremdsysteme_*.py` (52 Tests) |

Keine neue Oberfläche: Die Funktionen sind für den Einrichtungsassistenten (Agent P) gedacht und hier beschrieben.

### Einbindung für den Einrichtungsassistenten

Rechte: `masterdata.edit` **und** `channels.manage` ohne Einschränkung (Admin, Schulleitung). Lehrkräfte, Sekretariat,
Planer, Eltern, Schüler, Ansichtskonto: 403.

```
GET  /api/v1/import/fremd/systems                 unterstützte Systeme, Dateiendungen, Datenarten (parts), Optionen
POST /api/v1/import/fremd/preview                 Trockenlauf  (multipart: files[], system=auto|moodle-db|moodle-mbz|oneroster|webuntis|csv,
POST /api/v1/import/fremd/run                     echter Lauf   options=JSON, mapping=JSON, preset=schild-nrw|asv|lusd|magellan, prefix=mdl_)
GET  /api/v1/import/fremd/runs[/{id}]             Importprotokoll (Bericht verschlüsselt gespeichert)
POST /api/v1/import/fremd/runs/{id}/undo          Rückgängig
GET  /api/v1/export/oneroster.zip                 Stammdaten als OneRoster-1.2-CSV
```

`options` (alle optional): `instance` (Name der Quellinstanz, trennt zwei Moodle-Systeme), `create_missing_students`,
`create_missing_teachers`, `default_class`, `course_map` (`{"<Quellkurs>": "KURS#TEIL" | "neu" | "ueberspringen"}`),
`person_map` (`{"<Quellperson>": "S0004"}`), `include_hidden_courses`, `publish` (sonst Aufgaben versteckt, Selbsttests als
Entwurf), `parts` (Teilmenge von `personen, kursraeume, gruppen, aufgaben, noten, fragen, kompetenzen, abzeichen, forum,
dateien`), `only_courses`, `update_existing`.

Bericht (`preview` und `run`): `counts` (je Art `created/updated/unchanged/skipped`), `persons` (Zuordnungswege, Listen
`unmatched`, `ambiguous`, `conflicts`, `unsure`), `courses` (Zuordnung je Quellkurs), **`needs_decision`** (Kurse ohne
Zuordnung, mehrdeutige Personen – Antworten als `course_map`/`person_map` zurückgeben), `waiting_for_accounts`,
`problems` (höchstens 400, mit `problem_kinds`), `notes`, `lines` (fertige deutsche Zusammenfassung), `run_id`.

Empfohlene Reihenfolge in der Einrichtung: 1. Stammdaten (OneRoster/WebUntis/Liste, `create_missing_*`), 2. Konten und
Zugangsbriefe, 3. Moodle-Import, 4. Vorschau-Entscheidungen übernehmen und erneut importieren. Jeder Lauf ist idempotent und
ergänzt, was vorher mangels Konto fehlte.

Fallstrick für Aufrufer: Das Planungsdokument wird über `store.mutate` in einer **eigenen** Sitzung geschrieben. Die
Datenbanksitzung des Aufrufers darf vor `run_import` nichts schreiben, sonst „database is locked“ (SQLite). Die Routen
öffnen deshalb eine frische Sitzung im Threadpool.

## 3. Matrix System × Datenart

Legende: **ja** = unterstützt und getestet, **teil** = eingeschränkt (Spalte „Grenze“), **–** = fehlt. „Test“ = automatisierter
Test mit Fixture nach dem Originalformat.

| Datenart | Moodle-DB | Moodle-.mbz | OneRoster 1.2 | WebUntis-JSON | SchILD/ASV/Liste | Untis-GPU (bestehend) |
|---|---|---|---|---|---|---|
| Personen (Zuordnung, Neuanlage) | ja | ja | ja | ja (ohne Klasse) | ja | ja (Stammdaten) |
| Klassen | – (nur Hinweis) | – | ja (homeroom) | ja | ja (aus Spalte) | ja |
| Fächer, Räume | – | – | – | ja | – | ja |
| Stundenplan | – | – | – | – (nur Zeitraster ignoriert) | – | ja (GPU 001–015) |
| Kurse → Kursräume | ja | ja | ja (scheduled) | – | – | – |
| Einschreibungen/Mitglieder | ja | ja | ja | – | – | teil (Kurswahlen) |
| Gruppen | ja | ja | – | – | – | – |
| Aufgaben, Abgaben, Bewertung | ja | teil (nur Textabgaben) | – | – | – | – |
| Bewertungsraster | ja | – | – | – | – | – |
| Notenbuch-Einträge | ja (manuell, Skala, Quiz, Aufgaben) | – | ja (lineItems/results) | – | – | – |
| Fragen/Selbsttests | ja (6 Typen) | – | – | – | – | – |
| Kompetenzen | ja | – | – | – | – | – |
| Abzeichen | ja | – | – | – | – | – |
| Forum → Pinnwand | ja | – | – | – | – | – |
| Dateien | Platzhalter (Metadaten) | ja, mit Inhalt | – | – | – | – |
| Export in das Format | – | – | ja (Stammdaten, ohne Noten) | – | ja (CSV-Exporte, Notenexport) | ja |
| Trockenlauf / Idempotenz / Rückgängig / Protokoll | ja | ja | ja | ja | ja | Trockenlauf ja, sonst nein (Altweg) |

Quellen der Formate (Belege):

* **Moodle-Schema**: 68 Tabellen aus den `install.xml` des Repositories `moodle/moodle` (Zweig `main`, Commit
  `b7260e5`, 6.0dev Build 20261013) – Datei `tests/fixtures/fremdsysteme/moodle/moodle_schema.json`, erzeugt mit
  `build_moodle_schema.py`. Der Generator `gen_moodle.py` legt jede Tabelle mit allen echten Spalten an (Fragenbank mit
  `question_bank_entries`/`question_versions`, Gruppenabgaben mit `userid = 0`, Verzeichniszeilen in `files`, `-1` =
  nicht bewertet, Zeitstempel als Unix-Sekunden, gelöschte und gesperrte Konten, Profilfeld Geburtsdatum).
* **Moodle-Sicherung**: Elementnamen aus `backup/moodle2/backup_stepslib.php` und
  `mod/assign/backup/moodle2/backup_assign_stepslib.php`. **Nicht** gegen eine echte `.mbz` geprüft (kein Moodle zum
  Erzeugen); der Leser ist tolerant gebaut.
* **OneRoster 1.2**: Spaltenlisten aus der Spezifikation (https://www.imsglobal.org/spec/oneroster/v1p2/bind/csv),
  ausgezogen nach `oneroster/oneroster_v1p2_csv_columns.json`; ein Test vergleicht sie mit dem Leser/Schreiber.
* **WebUntis**: Feldnamen aus python-webuntis (`webuntis/objects.py`), das die JSON-RPC-API abbildet. Die offizielle
  PDF-Beschreibung war nicht abrufbar.
* **SchILD/ASV**: Presets in `csv_io.py` (bestehend). **Nicht belegbar** (keine öffentliche Spezifikation gefunden): das
  IServ-Importformat und der Export von Schulmanager Online – diese Dateien sind plausible Listen, die nur die tolerante
  Spaltenerkennung prüfen. **Nicht gemacht**: SVWS-Datenbankauszug, itslearning, Google Classroom (kein belegbares Format
  in der Zeit), neue GPU-Dateien 007–021 (die vorhandenen Tests mit Originalzeilen reichen für die unterstützten
  Dateiarten; 007+ sind Auswertungsexporte ohne Stammdatenwert).

Testabdeckung je Bereich: Moodle-DB 4 + 11 Tests (Rundlauf, Zuordnung, Umlaute, Idempotenz, Änderung, Fehler, Rückgängig,
Konten-Reihenfolge, Entscheidungen), .mbz 5, Stammdatenformate 13, Rechte/HTTP 16, Groß 3.

## 4. Messwerte (Windows-Laptop, SQLite, ein Prozess)

1.500 Schüler/innen, 96 Kurse, 192 Aufgaben, 6.787 Abgaben, 198 Notenspalten:

| Vorgang | Zeit |
|---|---|
| Moodle-Abzug (3,4 MB) lesen | 0,6 s |
| Moodle Vorschau (alles auf Rollback) | 6,2 s |
| Moodle echter Import (6.787 Abgaben, verschlüsselt) | 6,2 s |
| Moodle zweiter Lauf (alles unverändert) | 2,0 s |
| OneRoster (1.505 Personen, 607 KB) lesen / zuordnen | 0,04 s / 0,2 s |
| SchILD-Liste, 1.500 Schüler/innen neu anlegen / zweiter Lauf | 0,3 s / 0,1 s |

Der Engpass ist die Verschlüsselung der Freitexte, nicht die Datenbank.

## 5. Gefundene Probleme

Behoben:
1. `csv_io`: Geburtsdatum wurde gelesen, aber nie gespeichert → wird jetzt ergänzt (nie überschrieben, ungültige Daten
   werden gemeldet). Wichtig für die Zuordnung von Namensvettern.
2. Zwei Schreiber (Planungsdokument über `store.mutate` und Datenbanksitzung des Imports) sperrten sich → Reihenfolge
   festgelegt (erst Dokument, dann Datenbank), in der Doku vermerkt.
3. Beschädigte SQLite-Datei führte zu 500 → jetzt Bericht mit Problem.
4. Das Ansichtskonto („zuschauer“) hat `masterdata.edit` + `channels.manage` auf dem Papier → ausdrücklich ausgeschlossen
   (Protokolle enthalten Namen).

Offen / Grenzen (bewusst):
* **Konten**: Mitgliedschaft, Gruppen und Abgaben hängen an Konten (`users.id`). Personen ohne Konto werden gezählt
  („wartet auf Konto“) und beim nächsten Lauf ergänzt. Der Importer legt keine Konten an.
* WebUntis liefert keine Klassenzugehörigkeit der Schüler/innen → Standardklasse nötig.
* Moodle: nur die jeweils letzte Abgabe; Entwürfe werden übersprungen; Gruppen mit überlappenden Mitgliedern innerhalb
  einer Einteilung werden nicht doppelt geführt; Notenbuch-Überschreibungen in Moodle (`overridden`) werden nicht
  gesondert behandelt; Strafpunkte bei Mehrfachauswahl (negative Brüche) gehen verloren; Fragetypen außer Einfach-/
  Mehrfachauswahl, Richtig/Falsch, Kurzantwort, Numerisch, Zuordnung (z. B. Essay, Lückentext-Cloze, Berechnet) werden
  gemeldet und übersprungen; Kompetenzrahmen werden nur beim ersten Lauf angelegt (spätere neue Kompetenzen kommen
  nicht nach); Notenbuch-Quellen nur für Kurse, die einem Kursteil zugeordnet sind (eigene Kursräume haben kein Notenbuch).
* Dateien aus der Datenbank: nur Platzhalter (Moodle-Dateien liegen nicht in der DB, sondern im `moodledata`-Ordner).
* Rückgängig entfernt nur Neuangelegtes; Geändertes bleibt. Wer einen älteren Lauf zurücknimmt, nachdem ein jüngerer darauf
  aufbaut, bekommt keine Warnung – immer den jüngsten zuerst zurücknehmen.
* Produktive Moodle-Systeme laufen auf MySQL/PostgreSQL: Der Leser verlangt einen SQLite-Abzug.
* Alles Importierte ist zunächst **versteckt/Entwurf** (`publish=false`), damit Lehrkräfte vor der Freigabe prüfen.

## 6. Optimierungen und Alternativen

Aufwand: S = Tage, M = 1–2 Wochen, L = mehrere Wochen.

| Vorschlag | Nutzen | Aufwand | Empfehlung |
|---|---|---|---|
| **Standards statt Einzelformate**: OneRoster ausbauen (REST statt CSV, `lineItems`/`results` auch exportieren), Schulconnex (Bildungsraum/Länder-Schnittstelle) und LTI 1.3 für Lerntools | ein Weg für viele Quellen, kein Format-Pflegeaufwand | M (OneRoster-Export Noten) / L (Schulconnex, braucht Anbindung und Zertifizierung) | OneRoster zuerst fertigstellen; Schulconnex als nächstes Ziel für Länder, die es anbieten |
| **Live-Abgleich per API** statt Datei (täglich Personen/Klassen abgleichen, Abgänge sperren) | keine veralteten Listen, Abgänge automatisch | M (Planer + `import_links` existieren schon) | Empfohlen, sobald ein Standard-Anschluss steht |
| **Moodle-Webservice** statt DB-Zugriff (`core_course_get_courses`, `mod_assign_get_submissions`, `core_enrol_get_enrolled_users`, `gradereport_user_get_grade_items`) | kein DB-Abzug, auch Dateien über `webservice/pluginfile.php`, funktioniert bei MySQL/PG und bei gehosteten Moodle | M–L | **Empfohlen** als Hauptweg; die Bundle-Leser bleiben für Abzüge |
| **Mapping-Assistent in der Oberfläche** (Spalten, Kurse, Personen) | `needs_decision` und `/import/fremd/systems` liefern alles Nötige | M | Zusammen mit dem Einrichtungsassistenten bauen |
| **Konfliktlösung** (Mehrdeutige gegenüberstellen, Namensvettern per Geburtsdatum, „immer so zuordnen“) | weniger Nacharbeit | S–M | Entscheidungen als `import_links` speichern (Backend vorhanden, Oberfläche fehlt) |
| **Stapelverarbeitung im Hintergrund** (Job mit Fortschritt, Datei zwischenspeichern, Vorschau und Lauf auf demselben Upload) | 50-MB-Uploads, mehrere Minuten bei großen Schulen, kein doppeltes Hochladen | M (Jobsystem `jobs.py` vorhanden) | Ab etwa 20.000 Abgaben nötig; vorher reicht der synchrone Weg (6 s für 7.000) |
| **Konten beim Import mitanlegen** (mit Zugangsbriefen) | spart den Zwei-Schritte-Ablauf | S–M | Empfohlen, aber nur als ausdrückliche Option |
| Dateien aus `moodledata` über Pfad oder Webservice einlesen | echte Abgabedateien | M | Zusammen mit dem Webservice |
| Moodle-Sicherung als Hauptweg für Lehrkräfte („Mein Kurs“) | Lehrkräfte importieren selbst, nur eigene Kurse | M (Rechtekonzept) | Nach Webservice |

## 7. Wiederholen der Tests

```
python -m pytest tests/test_import_fremdsysteme_*.py -q         # ca. 40 s
python tests/fixtures/fremdsysteme/gen_moodle.py ZIEL.sqlite [--students 1500]
python tests/fixtures/fremdsysteme/gen_oneroster.py ZIELVERZEICHNIS
```
