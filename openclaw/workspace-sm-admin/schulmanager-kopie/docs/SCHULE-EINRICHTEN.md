# Eine neue Schule einrichten – Schritt für Schritt

Durchgehendes Beispiel: die fiktive **Waldeck-Montessori-Schule** (12 Lerngruppen, 250 Kinder, 42 Pädagog/innen, zwei
Standorte, Abendschule). Alles, was hier steht, wurde auf einer frischen lokalen Instanz mit leerer Datenbank
nachvollzogen (Stand 12.10.2026). Ergebnisse, Lücken und Werkzeug-Wünsche: [`MONTESSORI-UND-WERKZEUGE.md`](MONTESSORI-UND-WERKZEUGE.md).
Beispieldateien: [`beispiele/`](beispiele/) (Planungsdokument, Moodle-/Untis-Exporte, Zugangsbriefe).

> **Einrichtungsassistent:** Die Schritte 0–14 lassen sich in der App unter *Schule einrichten* abarbeiten; der Assistent erkennt den Stand, speichert den Fortschritt und führt zu den Seiten (Installation: [`INSTALLATION.md`](INSTALLATION.md)). Diese Seite bleibt das Nachschlagewerk mit den API-Pfaden.

Die Oberflächenseiten stehen in Klammern, darunter der API-Pfad (für Skripte; Doku unter `/api/docs`, wenn
`SM_ENABLE_DOCS=1` gesetzt ist). Wer nur klickt, braucht die Pfade nicht.

## 0. Voraussetzungen

| Was | Wozu | Beispiel |
|---|---|---|
| Laufende Instanz mit Erst-Administrator (`SM_ADMIN_USER`/`SM_ADMIN_PASSWORD`) | erste Anmeldung | lokal: `uvicorn schulmanager.server.app:app`, leere Datenbank |
| Lizenz (nur Produktivbetrieb, `Lizenz`) | den Lizenzschlüssel vom Anbieter eintragen; ohne gültige Lizenz ist die Instanz gesperrt (nur die Administration kommt weiter) | `/lizenz` |
| Schuljahr: Montag der 1. Schulwoche | Wochenzählung (Wochen 1–52, Ferien zählen mit) | 31.08.2026 |
| Zeitraster der Schule | Anfangszeiten, Pausen, Länge einer Stunde | 14 „Stunden“ à 45 min, davon 5 am Abend |
| Listen: Lehrkräfte, Schüler/innen, Klassen/Lerngruppen, Räume | Stammdaten | CSV aus Moodle/SchILD/ASV/Untis |
| Unterrichtskonzept auf Papier | Wer unterrichtet was, wann gemeinsam, welche Wochen | Freiarbeit, Epochen, Bänder |

Tipp: Erst die **Regeln der Schule aufschreiben** (Stunden je Gruppe und Woche, was parallel liegen muss, welche
Lehrkraft nur an welchen Tagen arbeitet). Der Generator kennt nur das, was als Regel eingetragen ist.

## 1. Reihenfolge (nicht ändern – spätere Schritte verweisen auf frühere)

```
Einstellungen → Standorte → Fächer → Räume → Klassen → Lehrkräfte → Schüler/innen
   → Stundentafeln → Kurse (Teams, Kopplungen, Epochen) → „Kurse aus Stundentafeln“ → Lehrkräfte zuweisen
   → Ferien/Termine/Blockphasen → Regeln für den Generator → Generator → Prüfen → Aufsichten
   → Konten + Zugangsbriefe → Sicherung/Export
```

Die Prüfungen beim Speichern verhindern falsche Reihenfolgen: Ein Raum ohne Standort, eine Klasse mit unbekanntem
Raum oder ein Kurs mit unbekannter Lehrkraft wird abgewiesen (HTTP 422, Klartextmeldung).

## 2. Die Schritte im Einzelnen

### Schritt 1 – Einstellungen (Zeitraster, Schuljahr)  `Schule einrichten` / `Stammdaten → Einstellungen`
`PUT /api/v1/settings`
- `school_year_start` = Montag der Woche 1, `week_numbering` = `school_year`.
- `periods` (höchstens 16), `period_times` (Anfangszeiten, aufsteigend), `period_minutes`, `breaks` (nach welcher Stunde, wie lang).
- Montessori: 14 Zeitscheiben von 08:00 bis 21:15; Pausen nach 5. (Hofpause), 6. (Mittagspause) und 9. Stunde (Abendpause).
- `double_alignment`: `pausen` (Doppelblöcke nur nicht über Pausen); `bloecke` ist für lange Freiarbeit zu streng.
- Vorsicht: Ändert man Zeitraster oder Unterrichtstage, fragt der Server mit 409 nach (`?force=1` bestätigt).
- Für das Aufbauen `auto_replan=false` setzen, sonst plant der Auto-Planer schon zwischendurch.

### Schritt 2 – Standorte, Fächer, Räume  `Stammdaten`
`POST /data/sites|subjects|rooms`
- Fächer: Kürzel, Name, **Raumtyp** (z. B. `Sporthalle`, `Atelier`), „Hauptfach“ (zählt für „früh am Tag“), max. Blöcke je Tag, Farbe.
  Montessori-Bereiche wie Freiarbeit, Morgenkreis und Epoche sind hier „Fächer“.
- Räume: Typ und Standort. Ein Raum kann je Zeit **nur einmal** belegt werden – auch nicht von zwei Teilen desselben Kurses.
  Deshalb braucht jede Lerngruppe mit zwei Lernbegleitungen einen **Nebenraum** (siehe Fehlerliste).

### Schritt 3 – Klassen / Lerngruppen  `Stammdaten → Klassen`
`POST /data/classes` (nur mit Recht „Stundenplan bearbeiten“, wenn Unterrichtstage gesetzt werden)
- Das Feld `grade` (Jahrgang) hat einen Wert. Bei Jahrgangsmischung: Mittelwert eintragen (nur Notbehelf).
- `max_periods_per_day` begrenzt den Tag („nur bis zur 8. Stunde“).
- **Sperrzeiten der Klasse** (`unavailable`): z. B. Freitag ab 6. Stunde; „jede 2. Woche Mittwoch frei“ =
  `{days:[2], rhythm:{every:2, from_week:1, to_week:0}}`; Abendschule = Stunden 1–9 gesperrt.
- `school_days` je Klasse (z. B. Abendschule nur Mo–Do).

### Schritt 4 – Lehrkräfte  `Stammdaten → Lehrkräfte` oder CSV-Import  (`Import / Export`)
`POST /import/csv/teachers` (Datei + `mapping`, mit `?dry_run=true` erst Vorschau)
- Spalten: Kürzel, Name, Fächer, Deputat, E-Mail … (Presets `schild-nrw`, `asv`, `magellan`, `lusd`; sonst eigenes Mapping).
- **Arbeitszeiten** (Teilzeit, nur abends, Wechselwochen) gibt es nur als **Raster** je Lehrkraft:
  `PUT /data/teachers/{id}` mit `work_grid: {weeks: N, blocked: [{week, day, periods}]}`. Der CSV-Import kennt das Raster nicht.
- Standorte (`sites`), Pendeln (`commutes`), Maximalstunden pro Tag, Wunschklassen.
- Deputat (`max_hours`) ist eine Zahl in Stunden à Zeitscheibe. Bei Montessori zählt die Anwesenheit; Werte deshalb höher ansetzen.

### Schritt 5 – Schüler/innen  CSV-Import oder Moodle-Liste
`POST /import/csv/students`
- Pflicht: Klasse (muss vorher existieren), Nachname, Vorname. Die ID kommt aus „ID/Schülernummer“; fehlt sie, wird sie aus Name+Klasse gebildet.
- Das Geburtsdatum aus der Datei wird gespeichert (nur ergänzt, nie überschrieben; Stand 16.10.2026). Import aus Moodle, OneRoster, WebUntis und Listen mit Trockenlauf, Idempotenz und Rückgängig: [`IMPORT-FREMDSYSTEME.md`](IMPORT-FREMDSYSTEME.md).
- Wahlteile (Religion/Niveau): Spalte „Konfession/Religionsunterricht“ ordnet automatisch in eine Religions-Kopplung ein; sonst `courses: ["KURS#TEIL"]` oder `parts[].students` im Kurs.

### Schritt 6 – Stundentafeln  `Planung → Stundentafeln` (`POST /data/curricula`)
- Je Jahrgang **oder je Klassenliste** (`classes` hat Vorrang): Fach → Wochenstunden, Doppelstunde gewünscht.
- Montessori: Tafel je Stufe (Grundstufe, Mittelstufe, Erdkinderplan, Abendschule), Jahrgangsmischung deshalb über `classes`, nicht über `grades`.
- Fächer, die später als Kopplung/Team angelegt werden (Freiarbeit, Epoche, Englisch-Band), trotzdem in der Tafel aufführen – sie werden angerechnet.

### Schritt 7 – Kurse mit besonderem Zuschnitt (von Hand)  `Planung → Kurse` (`POST /data/courses`)
Ein **Kurs** hat Klassen, Wochenstunden und **Teile**. Alle Teile liegen immer gleichzeitig.
| Bedarf | Aufbau |
|---|---|
| Team-Teaching (2 Lernbegleitungen) | 1 Kurs, 2 Teile (Lehrkraft A, Lehrkraft B), **jeder Teil eigener Raum** |
| Band über mehrere Gruppen (Englisch-Niveaus, Religion/Ethik) | 1 Kurs, `classes` = alle beteiligten Gruppen, je Niveau ein Teil mit `students` |
| Gemeinsame Stunde zweier Gruppen | 1 Kurs, 2 Klassen, 1 Teil |
| Epoche (nur einige Wochen) | `weeks: [1..12]` (oder `rhythm`) – je Epoche ein eigener Kurs |
| Schulbegleitung | zusätzlicher Teil im Kurs |
| Doppelblöcke (Freiarbeit) | `double: true`, Stunden gerade |
Kurse mit eigener Wochenangabe zählen in der Stundentafel **anteilig** (12 von 52 Wochen = 0,23 der Stunden).

### Schritt 8 – Kurse aus den Stundentafeln erzeugen, Lehrkräfte zuweisen
- `POST /planning/courses-from-curricula` (erst `{"dry_run": true}`): legt für jede Klasse die noch fehlenden Fächer als Ein-Teil-Kurse an.
- Danach: Klassenleitung/Bezugsperson **selbst eintragen** (`PUT /data/courses/{id}`), den Rest erledigt `POST /planning/assign-teachers`
  (nach Fächern und Deputat). Der Bericht nennt offene Teile.

### Schritt 9 – Ferien, Termine, Blockphasen
- Ferien/Feiertage (`POST /data/holidays`, oder automatischer Ferien-Import nach Bundesland/Land), Termine (`POST /data/events`, auch am Wochenende, nur für Klassen X).
- Blockphase (Praktikum, Klassenfahrt): `POST /absences` mit `kind=class` – wirkt auf Vertretung, nicht auf den Wochenplan-Generator.

### Schritt 10 – Vorgaben für den Generator
Der Generator bekommt **nur Regeln**, nie fertige Zeiten:
- Sperrzeiten (Klassen, Lehrkräfte), Wünsche (weich), Arbeitszeitraster, Unterrichtstage, Rhythmus.
- Kurse: Stunden, Doppelstunden, Wochen/Rhythmus, Kopplungen, feste Räume oder Raumtypen.
- Gewichte `PUT /settings` `weights` (höher = wichtiger): `class_gap`, `teacher_gap`, `late_start`, `position`, `core_late`, `day_balance`, `site_change`, `double_split`, `teacher_wish`.
- Montessori-Ziel „Freiarbeit am Vormittag“: Fach als „Hauptfach“ markieren, `core_latest_period` setzen und `core_late` hoch gewichten – hilft, garantiert aber nichts.
- Start: `POST /planning/generate` `{time_limit, seed, workers:0}`; Fortschritt `GET /planning/jobs/{id}`; Übernahme `POST /planning/jobs/{id}/apply` (Version, Rückgängig im Verlauf).

### Schritt 11 – Prüfen
1. Job-Ergebnis: `unplaced` (nicht verplante Blöcke) muss leer sein, `warnings` lesen.
2. `GET /planning/report` (`Planung → Bericht`): Konflikte, Hohlstunden, Kapazitätswarnungen, offene Kursteile.
3. Wochenansicht je Klasse, Lehrkraft, Raum, Schüler (`Stundenplan`) – Stichprobe jeder Besonderheit (Rhythmuswoche, Epochenwoche, Abendklasse).
4. Vertretungstest: Lehrkraft krank melden (`Vertretung`), Eintrag danach löschen.
5. Auto-Planer wieder einschalten (`auto_replan=true`), wenn der Plan steht.

### Schritt 12 – Pausenaufsichten  `Aufsichten`
Aufsichtsbereiche anlegen (Name, Standort, Anzahl je Pause), dann `POST /duties/generate`. Aufsichten entstehen **je Bereich und je Pause**
– auch für Pausen, in denen niemand da ist (Abendpause) → diese Zeilen bleiben unbesetzt und sind zu löschen.

### Schritt 13 – Konten und Zugangsbriefe  `Benutzer`, `Zugangsbriefe`
Reihenfolge:
1. `POST /users/bulk` je Rolle `lehrer`, `schueler`, `eltern` (Konten mit den Stammdaten verknüpft; Startpasswort wird erzeugt).
2. Besondere Rollen einzeln: `POST /users` (`schulleitung`, `abteilungsleitung`, `sekretariat`, `planer`, `hausmeister`, `schulbegleitung` mit `student_ids`, `zuschauer`).
3. Briefe: `POST /letters/batches` `{user_ids | student_ids (+parents)}` erzeugt neue Startpasswörter und einen Stapel; `GET /letters/batches/{id}/pdf` (Sammel-PDF),
   `…/zip` (Einzelbriefe), `…/send` (per E-Mail). Stapel gelten 1 Stunde und nur für die erstellende Person.
4. Der Brief enthält Benutzername, **Startpasswort** und einen **QR-Code zur Anmeldeseite**. Bei der ersten Anmeldung muss ein eigenes Passwort gesetzt werden.
   Einen echten Einmal-Login (Code/Link, der selbst keine Zugangsdaten enthält) gibt es nicht (Werkzeug W-17).
Beispiele je Rolle: [`beispiele/zugangsbriefe/`](beispiele/zugangsbriefe/) (enthalten Start-Passwörter der Test-Instanz – nicht weitergeben).

### Schritt 14 – Sichern und weitergeben
- `GET /export/json` = komplettes Planungsdokument (verlustfrei, ohne Konten/Passwörter), wieder einlesbar mit `POST /import/json` (ersetzt alles; `?dry_run=true` zeigt vorher Zahlen).
  Beispiel: [`beispiele/montessori-schule.json`](beispiele/montessori-schule.json) – Rundlauf in eine leere Instanz geprüft (erneuter Export = Quelldatei, `school`-Daten inhaltlich gleich).
- `GET /export/untis.zip` (Untis GPU), `GET /export/csv/{teachers|classes|rooms|subjects|students|lessons|curricula}`.
- Datenbank-Sicherung: `POST /admin/backups`.

## 3. Daten aus anderen Plattformen übernehmen

| Quelle | Werkzeug | Ergebnis im Test |
|---|---|---|
| Moodle: Nutzerliste (CSV) | CSV-Import mit Mapping | geht mit Umweg: Liste vorher nach Kollegium/Schüler trennen; Spalte `id` (Moodle-intern) mit `"id": null` abschalten, sonst werden Moodle-Nummern zu IDs |
| Moodle: Kohorten | CSV-Import „Klassen“ | geht, Kohorten ohne Jahrgang (Kollegium) werden übersprungen, Jahrgang fehlt in Moodle |
| Moodle: Kurse | CSV-Import „Fächer“ | technisch möglich, **inhaltlich falsch** (Moodle-Kurs ≠ Fach) – nicht verwenden |
| Moodle: Einschreibungen | – | geht nicht (Import verlangt Klasse; es gibt keinen Weg zu Kursteilen/Rollen) |
| Untis (GPU001–GPU015) | `POST /import/untis` | Klassen, Lehrkräfte, Räume, Kurse und Stunden kommen an; Sperrzeiten, Arbeitszeitraster, Pausen, Stundentafeln, Termine, Aufsichten, Jahrgang gehen verloren |
| SchILD/ASV/Magellan/LUSD | CSV-Import mit Preset | vorhanden (Spaltennamen werden erkannt) |
Details und fehlende Werkzeuge: `MONTESSORI-UND-WERKZEUGE.md`, Abschnitt 4. Beispieldateien: [`beispiele/import/`](beispiele/import/).

## 4. Typische Fehler und ihre Lösung

| Meldung / Symptom | Ursache | Lösung |
|---|---|---|
| Generator: viele Blöcke „nicht verplant“ bei einem Kurs mit mehreren Teilen in **einem** Raum | derselbe Raum kann nicht zweimal gleichzeitig belegt sein (auch nicht vom selben Kurs) | pro Teil einen eigenen Raum (Nebenraum, Ruheraum) |
| Ein Band bleibt unverplant (z. B. Religion/Ethik) | die beteiligten Lehrkräfte (Teilzeit) haben keinen gemeinsamen freien Tag oder die Gruppen haben keinen gemeinsamen freien Slot | Arbeitszeitraster prüfen, gemeinsame Tage schaffen; Stunden/Gruppen reduzieren |
| `Ungültige Daten – … ` / 422 beim Anlegen | Referenz fehlt (Raum, Lehrkraft, Fach, Klasse) | in der Reihenfolge von Abschnitt 1 vorgehen |
| 409 beim Ändern von Zeitraster/Unterrichtstagen | Stunden würden wegfallen | Änderungen lesen, mit `?force=1` bestätigen |
| CSV-Import: „Klasse fehlt“ | Klasse nicht vorher angelegt oder Spalte nicht zugeordnet | Klassen zuerst, `?dry_run=true`, Mapping prüfen |
| CSV-Import: IDs sind Zahlen statt Kürzel | Spalte `id` (z. B. Moodle) wurde automatisch als ID erkannt | Mapping `{"id": null, "idnumber": "id"}` |
| Arbeitszeitraster: „ungültige Sperrliste“ | mehr Einträge als Rasterwochen × 7 (Einträge je Woche+Tag zusammenfassen) | Perioden je (Woche, Tag) in einem Eintrag |
| Freiarbeit liegt auch nachmittags | der Generator kennt keine festen Tageszeiten je Fach | Gewichte erhöhen (`core_late`), mittelfristig Werkzeug W-01 |
| Viele Wochenvarianten (> 8, Warnung) | viele verschiedene Epochen × Rhythmen | Epochen auf wenige Zeitblöcke legen, Blockphasen als Abwesenheit eintragen |
| Aufsichten ohne Lehrkraft | Aufsicht wird für jede Pause und jeden Bereich verlangt | Bereiche/Pausen begrenzen; Abendpause-Zeilen entfernen |
| Brief-Stapel „abgelaufen“ (410) | Stapel gilt 1 Stunde | neuen Stapel erzeugen (setzt neue Startpasswörter) |
| Kind hat zwei Wahlteile zur gleichen Zeit | der Generator prüft nur Klassen, nicht einzelne Schüler | Teile eindeutig zuordnen (`parts[].students`), siehe W-05 |
