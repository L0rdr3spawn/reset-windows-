# Montessori-Schule im Schulmanager – Aufbau, Protokoll und Werkzeug-Liste

Stand 12.10.2026 · gebaut auf einer **eigenen lokalen Instanz mit leerer Datenbank** (nichts auf dem Server, keine
Code-Änderungen) ausschließlich mit den vorhandenen Funktionen (API wie die Oberfläche). Alle Namen sind erfunden.
Ergebnisdatei: [`beispiele/montessori-schule.json`](beispiele/montessori-schule.json) (Export, ohne Konten/Passwörter,
Rundlauf in eine leere Instanz geprüft). Anleitung: [`SCHULE-EINRICHTEN.md`](SCHULE-EINRICHTEN.md).
Beispieldateien: [`beispiele/import/`](beispiele/import/) (Moodle-/Untis-Exporte), [`beispiele/zugangsbriefe/`](beispiele/zugangsbriefe/).

## 1. Was gebaut wurde

### 1.1 Annahmen
- Fiktive **Waldeck-Montessori-Schule**, Schuljahr 2026/27, Woche 1 = 31.08.2026, Ferien nach NRW-Muster (von Hand eingetragen).
- Montessori-Tag: Offener Anfang/Morgenkreis, **Arbeitszyklus (Freiarbeit) 3 Std. vormittags**, Hofpause, Kurse/Epochen, Mittagspause, Nachmittag, am Abend die Abendschule.
- Eine Zeitscheibe = 45 Minuten (14 Zeitscheiben: 08:00 … 15:15 und 17:30 … 21:15). Pausen: nach 5. (30 min), nach 6. (45 min), nach 9. Zeitscheibe (90 min).
- **Jede Lerngruppe ist eine „Klasse“** (das Programm kennt nur Klassen). Jahrgangsmischung wird nicht abgebildet; das Feld „Jahrgang“ bekommt den Mittelwert.
- **2 Pädagog/innen je Lerngruppe** (Lernbegleitung 1 und 2) sind im Arbeitszyklus **beide anwesend** (Team-Teaching).
- Das Deputat (`max_hours`) ist für Montessori eine **Präsenz-Zahl** (36 Zeitscheiben/Woche), nicht Unterricht im engeren Sinn.
- Kein Kinderhaus; Hochschul-/Berufsschulanteile nur als Abendschule.

### 1.2 Struktur

| Bereich | Lerngruppen (Klassen) | Kinder | Besonderheiten |
|---|---|---|---|
| Grundstufe Jg. 1–3 | GS1 Bienen, GS2 Hummeln, GS3 Schmetterlinge, GS4 Marienkäfer (je 22) | 88 | Freiarbeit 20 Std.; Fr bis 13:00; GS2 mit Schulbegleitung |
| Mittelstufe Jg. 4–6 | MS1 Füchse, MS2 Dachse (je 24), MS3 Igel (24) | 72 | MS3: **jede 2. Woche Mittwoch frei** (Waldtag); MS3 mit Schulbegleitung |
| Erdkinderplan Jg. 7–10 (Hofgut Lindenau) | SEK1 Eichen, SEK2 Buchen, SEK3 Linden (je 20) | 60 | anderer Standort (1 Zeitscheibe Wegezeit); SEK1: **jede 2. Woche Mittwoch frei** (Hoftag); SEK2: Praktikum 01.–12.03.2027 |
| Abendschule | ABD1 Abschlussjahr (16), ABD2 Vorkurs (14) | 30 | **nur abends Mo–Do**; gemeinsame Englischstunde beider Gruppen |
| Gesamt | 12 Gruppen | 250 | 42 Lehrkräfte, 39 Räume, 2 Standorte, 19 „Fächer“, 6 Stundentafeln, 83 Kurse |

- **Personal (42):** 20 Bezugspersonen (A/B je Lerngruppe; drei davon nur vormittags), 3 Englisch (eine mit 2-Wochen-Raster),
  Musik, 2 Sport (eine ohne Mo/Fr), Religion ev./kath. (Teilzeit an wenigen Tagen), Ethik, Kunst, Werkstatt, Garten, Hofleitung,
  Deutsch/Mathe/NaWi Sek, 4 Abendschul-Lehrkräfte (nur abends), 2 Schulbegleitungen (I-Kräfte).
- **Räume (39):** 10 Lernlandschaften (Gruppenräume) + 10 **Nebenräume** + 2 Ruheräume, 6 Seminarräume, Turnhalle, Scheune, Musik,
  Atelier, 2 Werkstätten, 2 Gärten, Mensa.
- **Kurse (83):** 10 Freiarbeits-Teams (2–3 Personen), 12 Epochen (je Stufe 4 Zeiträume mit **Wahlteilen** quer über die Gruppen),
  Bänder (Englisch-Niveaus, Religion/Ethik je Stufe, Deutsch/Mathe-Niveaus und Projektarbeit Sek, 2 AGs), Abend-Englisch gemeinsam,
  49 Kurse aus den Stundentafeln (Morgenkreis, Lernbegleitung, Sport, Musik, Kunst, Werkstatt, Garten, Abendfächer).
- **Termine/Kalender:** 8 Ferien-/freie Zeiträume, 8 Termine (Elternabend, Tag der offenen Tür, Epochenabschluss ×2, Lernentwicklungsgespräche, Erdkinder-Projektwochen, Schulfest am Samstag, Klassenfahrt), 1 Blockphase (Praktikum).
- **Aufsichten:** 3 Bereiche, 593 Aufsichten erzeugt.
- **Konten:** 42 Lehrkräfte, 250 Schüler/innen, 250 Elternkonten, dazu Schulleitung, Abteilungsleitung, Sekretariat, Planung, Hausmeister, Schulbegleitung, Zuschauer.
- **Kursräume (digital):** je Kursteil/Klasse automatisch; 3 eigene angelegt (Epochenplanung, Erdkinderplan, Elternrat).

### 1.3 Wochenplan-Beispiel Lerngruppe GS1 Bienen (Woche 3, Epoche 1)

Der Plan wurde **vom Generator** gebaut (kein Eintrag von Hand). Kürzel: FA = Freiarbeit (Team GS1A + GS1B), KR = Morgenkreis,
EPO = Epoche (4 Gruppen, Wahlteile), REL = Religion/Ethik-Band, ENG = Englisch-Niveaus, SPO/MUS/KUW = Fachkurse.

| Zeit | Mo | Di | Mi | Do | Fr |
|---|---|---|---|---|---|
| 08:00 | EPO | FA | FA | REL (ev/kath/Ethik) | FA |
| 08:45 | EPO | FA | FA | FA | FA |
| 09:30 | FA | ENG (Jg. 1 / Jg. 2–3) | FA | FA | FA |
| 10:15 | FA | ENG | FA | FA | FA |
| 11:00 | KR | KR | KUW | FA | KR |
| 12:15 | MUS | | | | |
| 13:45 | FA | FA | SPO | KR | |
| 14:30 | FA | FA | SPO | KR | |

Erkennbar: Arbeitszyklus-Blöcke von 3 Std. kommen vor (Mo 09:30–11:00 … Di/Mi/Do/Fr), aber **der Generator hält die Montessori-Tagesstruktur nicht ein**:
Morgenkreis liegt oft um 11:00 oder nachmittags, Freiarbeit auch nachmittags. Das ist Lücke W-01/W-02.

Mittelstufe MS3 Igel, Woche 4 (Mittwoch frei, Rhythmus „jede 2. Woche ab Woche 2“): Mi komplett leer, alle Stunden an den übrigen Tagen untergebracht
(Woche 3 hat dagegen den Mittwoch). Abendschule ABD1: Mo–Do 17:30–21:15 mit DEU, MAT, GWL, NAT und gemeinsamem Englisch, am Tag nichts.
Erdkinderplan SEK1 (Woche 3 = „Mi frei“): Mittwoch leer, Projekt, Epoche, Niveaukurse und Freiarbeit liegen an Mo, Di, Do, Fr.

## 2. Protokoll: Schritt → Werkzeug → Ergebnis

Wertung: **direkt** = vorgesehener Weg funktioniert; **Umweg** = geht nur mit dem genannten Behelf; **nein** = nicht möglich.

| # | Schritt | Werkzeug | Ergebnis |
|---|---|---|---|
| 1 | Zeitraster, Pausen, Schuljahr, Gewichte | `PUT /settings` | **direkt** (14 Zeitscheiben, 3 Pausen, Doppelblöcke „nicht über Pausen“) |
| 2 | Abendunterricht | zusätzliche Zeitscheiben 10–14 + Sperrzeiten der Tagesklassen und -lehrkräfte | **Umweg**: ein globales Zeitraster, kein getrenntes Abend-Raster (W-02) |
| 3 | Standorte (Haus, Hofgut) | `POST /data/sites` | **direkt** (Wegezeit nur global 1 Zeitscheibe, W-22) |
| 4 | „Fächer“ Freiarbeit, Morgenkreis, Epoche, Lernbegleitung | `POST /data/subjects` | **Umweg**: es gibt nur „Fach“, keinen Baustein „freie Lernzeit“ (W-08) |
| 5 | Räume: Lernlandschaften, Fachräume | `POST /data/rooms` | **direkt**; „Haupt-/Nebenraum“ als zwei getrennte Räume (W-10) |
| 6 | Lerngruppen (jahrgangsgemischt) | `POST /data/classes` | **Umweg**: nur Klassen mit einem Jahrgangswert (W-03) |
| 7 | Sperrzeiten, „jede 2. Woche Mittwoch frei“, Fr früher frei, Abendklasse | Klasse `unavailable` (Rhythmus), `school_days` | **direkt** |
| 8 | Lehrkräfte aus Moodle-Nutzerliste | `POST /import/csv/teachers` + Mapping | **Umweg**: Liste vorher filtern; Spalte `id` abschalten; Deputat/Arbeitszeit fehlen (W-19) |
| 9 | Teilzeit/Arbeitszeiten (nur vormittags, nur abends, Wechselwochen, freie Tage) | `PUT /data/teachers/{id}` `work_grid` | **direkt**; nicht per CSV importierbar |
| 10 | Schüler/innen aus Moodle-Nutzerliste (Kohorte → Klasse) | `POST /import/csv/students` + Mapping | **Umweg**: Geburtsdatum/Jahrgang werden nicht gespeichert → 250× `PUT /data/students/{id}` |
| 11 | Stundentafeln je Stufe | `POST /data/curricula` (`classes` statt `grades`) | **Umweg** (W-03) |
| 12 | Freiarbeit mit zwei/drei Lernbegleitungen | Kurs mit mehreren Teilen | **Umweg**: jeder Teil braucht einen eigenen Raum; im 1. Lauf blieben alle 1 224 Freiarbeits-Blöcke unverplant, weil beide Teile denselben Raum verlangten (W-04, W-10) |
| 13 | Epochen (andere Wochen, Wahlteile quer über Gruppen) | Kurs mit `weeks`, Teile mit `students` | **Umweg**: 12 getrennte Kurse, keine Epochenfolge (W-06) |
| 14 | Bänder (Englisch-Niveaus, Religion/Ethik, Deutsch/Mathe/Projekt Sek, AGs) | Kurse über mehrere Klassen, parallele Teile | **direkt** |
| 15 | Gemeinsame Stunde zweier Gruppen (Abend-Englisch) | Kurs mit zwei Klassen und einem Teil | **direkt** |
| 16 | Wahl-/Niveauzuordnung der Kinder | `parts[].students` (von Hand) | **Umweg**: keine Kollisionsprüfung je Kind, keine Wahlphase (W-05) |
| 17 | Kurse aus Stundentafeln erzeugen | `POST /planning/courses-from-curricula` | **direkt** (Kopplungen/Epochen werden angerechnet, 49 Kurse neu) |
| 18 | Lehrkräfte zuweisen | Bezugspersonen von Hand, Rest `POST /planning/assign-teachers` | **direkt** (36 Teile automatisch) |
| 19 | Ferien, Feiertage, Termine (auch Samstag), Erdkinder-Projektwochen | `POST /data/holidays`, `/data/events` | **direkt** |
| 20 | Praktikum nur für Jahrgang 9/10 einer Mischgruppe | `POST /absences` (Klasse) | **Umweg**: nur die ganze Gruppe (W-07) |
| 21 | Plan erzeugen | `POST /planning/generate` | **direkt**, drei Läufe (siehe 3) |
| 22 | Plan prüfen | `GET /planning/report`, Wochenansichten | **direkt** |
| 23 | Pausenaufsichten | `POST /data/areas`, `POST /duties/generate` | **Umweg**: Aufsichten je Bereich × alle Pausen, auch Abendpause → 200 unbesetzte Zeilen (W-16) |
| 24 | Vertretung bei Team (GS1A krank) | `POST /absences`, `GET /substitutions` | **direkt**: 3 Vertretungen + 2 Mitbetreuungen, Teilbezeichnung „Lernbegleitung 1“ bleibt erhalten |
| 25 | Konten für alle Rollen | `POST /users/bulk`, `POST /users` | **direkt** (42 + 250 + 250 + 7 Zusatzrollen) |
| 26 | Zugangsbriefe je Rolle (PDF) | `POST /letters/batches`, `GET …/pdf` | **direkt**; **Einmal-Login: nein** (nur Startpasswort + Zwangswechsel, QR führt nur zur Anmeldeseite, W-17) |
| 27 | Kursräume (digital) | automatisch + `POST /channels` | **direkt** (eigene Räume nur durch Schulleitung) |
| 28 | Export/Import des Planungsdokuments | `GET /export/json`, `POST /import/json` | **direkt**, in leere Instanz zurückgelesen: alle Zahlen und die `school`-Daten identisch |
| 29 | Untis-Export und -Rückimport | `GET /export/untis.zip`, `POST /import/untis` | **Umweg/verlustbehaftet**: Kurse und 363 Stunden kommen an, Sperrzeiten, Arbeitszeitraster, Pausen, Stundentafeln, Termine, Aufsichten, Jahrgang, Teilzuordnungen fehlen (W-20) |
| 30 | Moodle: Kohorten, Kurse, Einschreibungen | CSV-Import | Kohorten **Umweg**; Kurse als „Fächer“ **falsch**; Einschreibungen **nein** (W-19) |
| 31 | Eigene Formulare der Schule (Beurlaubung, Krankmeldung, Sonstiges) | – | **nein**: Krankmeldung/Beurlaubung nur als feste Vorgänge und ein festes Formular-PDF (W-18) |
| 32 | Individueller Wochenplan je Kind (Arbeitsplan) | – | **nein**: nur Klassen-/Kursplan und Schüleransicht der eigenen Kurse (W-09) |
| 33 | Aufrücken im Jahrgangsverbund (Jg. 3 → 4 = andere Gruppe) | Versetzung | **nein**: keine Jahrgänge je Kind (W-03) |
| 34 | Lernentwicklungsgespräche, Wortzeugnis, Kompetenzraster | – | **nein** (nur Termin eintragbar, W-23) |

## 3. Generator: Vorgaben → Ergebnis, Grenzen

Vorgaben: 12 Gruppen, 83 Kurse, 301 Wochenstunden, 363 Stundenblöcke, 8 Wochenvarianten (Epochen × „Mi frei“-Rhythmen), Rechenzeit 120–240 s (4 parallele Läufe),
Gewichte angehoben (`core_late` 300, `late_start` 120, `class_gap` 150, `teacher_gap` 1). **Eingegeben wurden nur Regeln**, nie Zeiten.

| Lauf | Änderung der Vorgaben | Ergebnis |
|---|---|---|
| 1 | Freiarbeit-Teile alle im Gruppenraum | **1 224 Blöcke unverplant** (alle 10 Freiarbeits-Kurse + 3 Religion-Bänder): Ein Raum kann nicht zweimal belegt werden, auch nicht vom selben Kurs |
| 2 | Nebenräume je Gruppe (2 Läufe: Standardgewichte 150 s, erhöhte Gewichte 180 s); Religion ev. nur Di/Mi/Fr, kath. nur Mi/Do/Fr (Teilzeit) | 396 bzw. 407 Blöcke, jeweils **8 unverplant** (Religion MS und SEK): ev., kath. und Ethik hatten nur Mi/Fr gemeinsam, und dort fehlten gemeinsame freie Slots der drei Mittelstufen-/Sek-Gruppen. Standardgewichte: 56 Hohlstunden-Punkte Klassen, 704 Lehrkräfte, 115 „Hauptfach spät“; erhöhte Gewichte: 106 „Hauptfach spät“ (kaum besser) |
| 3 | Teilzeit-Tage gelockert (ev. nur Mo gesperrt, kath. Mo/Di gesperrt), 240 s | **363 Blöcke, 0 unverplant, 0 Konflikte**; übernommen. Bericht: 8 Hohlstunden bei Klassen (GS1 3, GS3 2, GS4 2, MS3 1), 101,5 Springstunden, 9,5 Standortwechsel, 107 „Hauptfach zu spät“ |

Was der Generator **konnte**: gekoppelte Kurse über bis zu 4 Klassen, parallele Teile mit Teilzeit-Lehrkräften, Rhythmus „Mi frei“ je 2. Woche, Epochenwochen,
Abendklassen mit Abend-Lehrkräften, Standortwechsel zwischen Haus und Hofgut, Räume nach Typ und Standort, Doppelblöcke.

Wo er an **Grenzen** stieß:
1. **Tagesstruktur:** kein Weg, „Morgenkreis immer in der 1. Zeitscheibe“ oder „Freiarbeit nur 08:45–11:45“ vorzugeben; die Verteilung folgt nur Kosten (Hohlstunden, früh am Tag). Freiarbeit und Morgenkreis landen auch nachmittags (W-01).
2. **Blocklänge:** nur Einzel- und Doppelstunden; 3-Stunden-Arbeitszyklus entsteht nur zufällig durch zwei Doppelblöcke, Warnungen „musste N× an einem Tag gelegt werden“ (GS-Freiarbeit, bis 18×) (W-02).
3. **Gleichzeitig im selben Raum:** zwei Lehrkräfte eines Kurses im selben Raum sind verboten (W-04, W-10).
4. **Keine Begründung:** bei unverplanten Blöcken nennt der Generator nur Kurs und Woche, nicht die Engstelle (Teilzeit-Tage, Raum, Gruppe) – die Ursachen wurden von Hand gesucht (W-13).
5. **Hartes Zusammen:** „Lernbegleitung 1 oder 2 reicht“ ist nicht ausdrückbar; Teilzeit einer Lernbegleitung zwingt zum Sperren der Nachmittage (W-04, W-12).
6. **Stundensoll je Woche statt je Zyklus:** Eine Klasse mit „jede 2. Woche Mi frei“ muss auch in der Freiwoche das volle Wochensoll in vier Tagen erfüllen; MS3 und SEK1 mussten deshalb kleiner geplant werden (W-15).
7. **Kind-Ebene fehlt:** Konflikte einzelner Kinder zwischen Bändern (Wahlteile) werden nicht erkannt (W-05).
8. **Viele Varianten:** 8 Wochenvarianten sind die Grenze, ab der der Generator warnt; Epochen × Rhythmus treiben die Zahl schnell hoch (W-06).
9. **Gesamtqualität:** 101 Springstunden und 107 späte Hauptfach-Blöcke trotz hoher Gewichte; die Rechenzeit von 4 Min. reicht für den Feinschliff nicht.

## 4. Werkzeug-Liste (Lücken)

Prinzip: **Bausteine statt Sonderfälle.** Jedes Werkzeug ist ein kleines, für sich nützliches Teil mit Datenmodell und Oberfläche; Montessori ist der erste Anwendungsfall,
das Teil soll aber ohne „Montessori“ im Namen auskommen. Alle Werkzeuge sind abschaltbar und je Schule konfigurierbar.
Aufwand: S = Tage, M = 1–3 Wochen, L = über 3 Wochen. Priorität: **A** = ohne das bleibt der Planer für diese Schulart untauglich, **B** = deutlich nützlich, **C** = später.

### W-01 Tageszeit-Anker und Tagesrahmen-Vorlagen
- **Problem:** Der Generator kann keine festen Tageszeiten je Fach/Kurs vorgeben (Freiarbeit 08:45–11:45, Morgenkreis 1. Zeitscheibe, Hauptunterricht 2 Std. morgens).
- **Schularten:** Montessori, Waldorf (Hauptunterricht), Jenaplan, Grundschule, Ganztag (Rhythmisierung), Förderschule, Berufsschule (Blocktage), Abendschule.
- **Anwendung:** Unter *Planung → Tagesrahmen* je Klasse/Stufe Zeitfenster benennen („Offener Anfang“ 1, „Arbeitszyklus“ 2–5, „Mittagsband“ 6–7); je Fach/Kurs eintragen „nur in …“ bzw. „bevorzugt in …“ (hart/weich). Die Vorlage wird mit einem Klick auf weitere Gruppen übertragen.
- **Datenmodell:** `DayFrame {id, name, slots:[{name, from, to}]}`, `Class.day_frame`, `Subject.allowed_slots` und `Course.allowed_slots {mode: hard|soft, slots:[{days, periods}]}`.
- **Auswirkung:** Generator (harte Maske + Kosten), Vertretung (Blockerhalt: Freiarbeit nicht verschieben), Kalender (Zeitfenster als Beschriftung), Klassenbuch (Block statt Stundenliste).
- **Aufwand:** M · **Priorität:** A

### W-02 Zeitblöcke beliebiger Länge und mehrere Zeitraster
- **Problem:** Blöcke sind 1 oder 2 Stunden; das Zeitraster gilt schulweit (Abendschule: nur über Zeitscheiben 10–14 und Sperren hingekriegt).
- **Schularten:** Montessori (3-Std.-Zyklus), Berufsschule/Blockunterricht (8 Std.), Hochschul-ähnlich (90 Min.), Waldorf-Epoche, Abendschule, Ganztag mit freier Taktung.
- **Anwendung:** *Einstellungen → Zeitraster*: mehrere Raster anlegen (Tag, Abend, Freitag kurz), Klassen/Standorte/Tage zuweisen. Im Kurs „Blocklänge“: 1–N Zeitscheiben oder Minuten, „zusammenhängend“.
- **Datenmodell:** `TimeGrid {id, periods:[{from,to}], breaks}`, `Class.grid_by_day`, `Course.block_lengths:[3,2]`, `Lesson.length` bis 16.
- **Auswirkung:** Generator (Blockbildung, Pausenregel), Vertretung (Block als Einheit), Kalender (Minutengenauigkeit), Klassenbuch (ein Eintrag je Block).
- **Aufwand:** L · **Priorität:** A

### W-03 Lerngruppen unabhängig von Klassen (Mehrfachzugehörigkeit, Jahrgangsspannen)
- **Problem:** Jedes Kind gehört genau einer „Klasse“ mit **einem** Jahrgang; Jahrgangsgemischte Gruppen, Stammgruppe plus Lerngruppen, Aufrücken im Verbund sind nicht abbildbar.
- **Schularten:** Montessori, Jenaplan, Gesamtschule (Differenzierung), Oberstufe, Förderschule (Gruppen), Berufsschule (Fachklassen + Fachgruppen), Hochschule.
- **Anwendung:** *Stammdaten → Gruppen*: Gruppe anlegen (Art: Stammgruppe, Lerngruppe, Kurs, Fördergruppe; Jahrgangsspanne), Kinder mit Gültigkeitszeitraum zuordnen. Stundentafeln gelten für Gruppenart/Jahrgangsspanne. „Aufrücken“ verschiebt Kinder jahrgangsweise zwischen Gruppen.
- **Datenmodell:** `Group {id, kind, grade_from, grade_to, site}`, `Student.grade`, `Membership {student, group, from, to}`, `Course.groups` ersetzt/ergänzt `Course.classes`.
- **Auswirkung:** Generator (Gruppen als Belegungseinheit), Vertretung (Kinder je Gruppe), Kalender (Termine für Gruppen/Jahrgänge), Klassenbuch (Anwesenheit je Gruppe), Versetzung.
- **Aufwand:** L · **Priorität:** A

### W-04 Team-Teaching mit gleichberechtigten Lehrkräften
- **Problem:** Mehrere Lehrkräfte in einem Kurs gehen nur als parallele Teile mit **je eigenem Raum**; „eine von zwei“ oder Wechsel fehlen; Rollen (Leitung/Begleitung/Schulbegleitung) und Anteile fehlen.
- **Schularten:** Montessori, Gesamtschule (Gemeinsames Lernen, Doppelsteckung), Förderschule, Inklusion, Grundschule (Zweitbesetzung), Berufsschule (Lernfeld im Team).
- **Anwendung:** Im Kurs „Besetzung“: Personen mit Rolle, Pflicht/Wahl („mindestens 1 von A, B“), Anteil in %; Raum gilt für den ganzen Kurs („gemeinsamer Raum“). Teilzeit-Teams werden über Wechselbesetzung (W-12) abgedeckt.
- **Datenmodell:** `Course.staffing {min_present, members:[{teacher, role, required, share}]}`, `Course.shared_room: bool`.
- **Auswirkung:** Generator (Verfügbarkeitsmenge statt UND; gleiche Raumbelegung), Vertretung (Mitbetreuung ist schon da – nutzt Rollen), Klassenbuch (Eintrag nennt alle), Deputat (W-11).
- **Aufwand:** M · **Priorität:** A

### W-05 Schüler-genaue Planung: Konfliktprüfung je Kind und Wahl-/Niveaukurs-System
- **Problem:** Der Generator prüft nur Klassen, Lehrkräfte, Räume. Kinder in zwei gleichzeitigen Bändern fallen nicht auf; Wahlen werden von Hand als Listen eingetragen.
- **Schularten:** Oberstufe mit Kurswahl, Gesamtschule (Wahlpflicht, E-/G-Kurse), Montessori (Epochenwahl), Berufskolleg (Wahlpflicht), Hochschule (Modulanmeldung).
- **Anwendung:** *Planung → Wahlen*: Wahlfenster definieren (Angebot, Kapazität, Erst-/Zweitwunsch, Jahrgang); Kinder/Eltern wählen; Verteilung (Wunsch-Optimierung) erzeugt `parts[].students`; Konfliktbericht „Kind X in zwei Kursen um Di 3.“; Generator nutzt Kindkonflikte als harte Regel optional.
- **Datenmodell:** `Choice {id, window, options:[course_part], capacity, rules}`, `StudentChoice {student, option, rank}`, `Allocation`.
- **Auswirkung:** Generator (Schienenbildung nach Wahlen), Vertretung (Kindzahl je Teil), Kalender (Wahlfristen), Klassenbuch (Teilnehmerlisten).
- **Aufwand:** L · **Priorität:** A

### W-06 Epochen- und Phasenplaner
- **Problem:** Epochen sind nur mehrere Einzelkurse mit Wochenlisten; es fehlen Folge, Rotation durch Gruppen, Archiv und Übersicht. Viele Zeiträume erzeugen viele Wochenvarianten.
- **Schularten:** Montessori (kosmische Erziehung), Waldorf (Epochenunterricht), Berufsschule (Blockwochen), Projektschulen, Oberstufe (Halbjahre), Hochschule (Semester/Module).
- **Anwendung:** *Planung → Epochen*: Zeitachse mit Phasen (Start-/Endwoche, Thema, Leitung, Raum, Teilnehmer/Gruppen); Rotation „Gruppe A: Thema 1, B: Thema 2 …“ per Raster; Kopieren ins nächste Jahr; Abschlusspräsentation als Termin.
- **Datenmodell:** `Phase {id, name, weeks, template_course}`, `PhaseAssignment {phase, group, topic, teacher, room}`; erzeugt Kurse mit `weeks`.
- **Auswirkung:** Generator (Phasen als Zeitbereiche, weniger Varianten durch Bündelung), Vertretung/Kalender (Phasenanzeige), Klassenbuch (Epochenthema je Woche).
- **Aufwand:** M · **Priorität:** A

### W-07 Blockphasen für Teilgruppen (Praktikum, Fahrten)
- **Problem:** Blockphasen gibt es nur je ganze Klasse oder Lehrkraft; Praktikum nur für Jg. 9/10 einer Mischgruppe oder Betrieb je Schülerliste geht nicht, und die Planung nutzt die freie Zeit nicht.
- **Schularten:** Montessori (Erdkinderplan), Berufsschule (Betriebsphasen), Gesamtschule (Praktika, Klassenfahrten), Hochschule (Praxissemester), Abendschule.
- **Anwendung:** *Planung → Blockphasen*: Zeitraum, Teilnehmer (Gruppe, Jahrgang oder Liste), Art (Praktikum, Fahrt, Prüfung), Betreuer/innen (Lehrkräfte werden freigestellt oder eingesetzt).
- **Datenmodell:** `BlockPhase {id, kind, from, to, participants:{groups|grades|students}, supervisors}`.
- **Auswirkung:** Generator (Auslastung ohne diese Kinder, frei werdende Lehrkräfte → Vertretungsreserve), Vertretung, Kalender, Klassenbuch (nicht anwesend „Praktikum“).
- **Aufwand:** M · **Priorität:** B

### W-08 Freie Lernzeit / Betreuungsblock (ohne Fach)
- **Problem:** Freiarbeit, Lernbüro, Ganztag-Betreuung sind „Fächer“; Zahl der Begleitpersonen, mehrere Räume gleichzeitig (Haupt-/Nebenraum/Außen) und Anrechnung fehlen.
- **Schularten:** Montessori, Jenaplan, Ganztag (Lernzeit/Hausaufgaben), Oberstufe (Studienzeit), Gesamtschule (Lernbüro), Abendschule (Selbstlernen).
- **Anwendung:** Blocktyp „Lernzeit“ anlegen: Raumverbund, Mindestbesetzung (z. B. 2 Personen für 24 Kinder), erlaubte Tätigkeiten, ob Klassenbuch-Eintrag je Kind erforderlich ist.
- **Datenmodell:** `BlockType {kind: lesson|open_time|care, min_staff, ratio, room_group}`, `Course.block_type`.
- **Auswirkung:** Generator (Besetzungsregel statt Fach), Vertretung (Aufsichtsschlüssel), Kalender, Klassenbuch (Freiarbeitsprotokoll), Deputat (W-11).
- **Aufwand:** M · **Priorität:** A

### W-09 Individuelle Wochenpläne je Kind
- **Problem:** Es gibt Klassen-, Lehrer-, Raum- und Kursansichten. Kein Arbeitsplan je Kind (Darbietungen, Lernziele, feste Termine innerhalb der freien Zeit).
- **Schularten:** Montessori, Jenaplan, Förderschule (Förderplan), Berufsschule (individuelle Lernzeiten), Hochschule (eigener Stundenplan), Ganztag.
- **Anwendung:** Lernbegleitung öffnet *Kind → Wochenplan*: Wochenziele, Darbietungstermine (mit Lehrkraft/Raum, in den Lernzeit-Block eingebettet), Pflichtanteile; Kind/Eltern sehen und bestätigen; Wochenrückblick.
- **Datenmodell:** `StudentPlanItem {student, week, kind, title, slot?, teacher?, status}`, `PlanTemplate`.
- **Auswirkung:** Generator (Darbietungen als weiche Belegung von Lehrkraft/Raum), Vertretung (Termine absagen), Kalender (Eltern-Ansicht), Klassenbuch (Lerntagebuch).
- **Aufwand:** L · **Priorität:** B

### W-10 Raumverbünde und teilbare Räume
- **Problem:** Ein Raum ist je Zeit einmal belegt (auch vom selben Kurs); Lernlandschaft aus Haupt-/Nebenraum/Außengelände, Turnhalle in Dritteln, Mensa mit Kapazität sind nicht ausdrückbar.
- **Schularten:** Montessori, Waldorf, Förderschule, Ganztag, Berufsschule (Werkstätten), Hochschule (Hörsaal-Kapazität).
- **Anwendung:** *Räume*: „Verbund“ aus mehreren Räumen anlegen, „teilbar in N“ oder Kapazität; im Kurs „Raumverbund X“ wählen – Teile dürfen sich im Verbund aufhalten.
- **Datenmodell:** `RoomGroup {id, rooms}`, `Room.capacity_units`, `CoursePart.room_group`.
- **Auswirkung:** Generator (Kapazitätsrechnung statt Exklusivität), Vertretung (Raumersatz im Verbund), Kalender/Raumplan.
- **Aufwand:** M · **Priorität:** A

### W-11 Deputat-/Präsenz-Modell
- **Problem:** Das Deputat ist eine Zahl in Stunden; Gewichtung nach Tätigkeit (Freiarbeit, Aufsicht, Beratung), Teilzeit in Prozent und Jahreskonten fehlen.
- **Schularten:** Montessori, Berufsschule (Jahresarbeitszeit), Gesamtschule (Entlastungen), Hochschule (Lehrdeputat), Abendschule (Abendzulage).
- **Anwendung:** *Lehrkräfte*: Beschäftigungsgrad, Tätigkeitsgewichte je Fach/Blocktyp, Funktionsstunden, Konto (Soll/Ist/Jahr); Bericht „Auslastung“.
- **Datenmodell:** `Teacher.fte`, `WorkWeights {subject|block_type: factor}`, `Teacher.annual_account`.
- **Auswirkung:** Generator (Kapazität und Fairness), Vertretung (Mehrarbeit zählt), Aufsichten (Verteilung nach Auslastung).
- **Aufwand:** M · **Priorität:** B

### W-12 Verfügbarkeiten: Wechselbesetzung, Wunsch-Stufen, Import
- **Problem:** Das Arbeitszeitraster sperrt hart; Teams mit Wechselbesetzung („A Mo/Di, B Mi–Fr“), Stufen (gern/möglich/ungern) und CSV/Untis-Import der Raster fehlen.
- **Schularten:** alle mit Teilzeit; besonders Montessori, Grundschule, Förderschule, Abendschule (Honorarkräfte).
- **Anwendung:** Lehrkraft/Selbstverwaltung malt Raster mit drei Farben; Team-Tabelle „wer wann“; CSV-Import der Raster; Prüfung „Team ohne Überschneidung“.
- **Datenmodell:** `Availability {teacher, week, day, period, level}`, `Team {members, rule}`.
- **Auswirkung:** Generator (weiche Kosten + harte Menge), Vertretung (Mehrarbeit nur bei „möglich“).
- **Aufwand:** M · **Priorität:** B

### W-13 Generator-Diagnose „Warum nicht verplant?“ und Vorab-Engpassanalyse
- **Problem:** Der Generator nennt nur „Kurs X Woche Y nicht verplant“ (Lauf 1/2 lieferten 1 224 bzw. 8 Blöcke ohne Begründung).
- **Schularten:** alle.
- **Anwendung:** *Planung → Bericht → Engpässe*: je Kurs gemeinsame freie Slots aller Beteiligten (Lehrkräfte, Klassen, Räume), Ursache („nur Mi gemeinsam frei“, „Raum doppelt“), Vorschläge („Lehrkraft B Do freigeben“). Vorab-Check ohne Rechenlauf beim Speichern des Kurses.
- **Datenmodell:** `Diagnosis {course, blockers:[{kind, ref, share}], suggestions}` (berechnet, nicht gespeichert).
- **Auswirkung:** Generator (Zusatzausgabe), Bericht, Auto-Planer (bessere Meldungen).
- **Aufwand:** M · **Priorität:** A

### W-14 Regeleditor für den Generator mit Vorlagen
- **Problem:** Regeln stehen verstreut (Sperren, Fach-Optionen, Gewichte). Eigene Regeln (nicht 2 Tage hintereinander, Fach X nie nach der 5. Stunde, Sport nicht vor Mathe) fehlen.
- **Schularten:** alle; Vorlagen je Schulart.
- **Anwendung:** *Planung → Regeln*: Regelkatalog mit hart/weich, Gültigkeit (Stufe, Fach), Vorschau der Wirkung; Vorlagen „Grundschule“, „Montessori“, „Waldorf“, „Gesamtschule“, „Berufskolleg“.
- **Datenmodell:** `Rule {id, kind, scope, params, hard, weight}`.
- **Auswirkung:** Generator (Regel-Auswertung), Vertretung (dieselben Regeln beim Verschieben).
- **Aufwand:** L · **Priorität:** B

### W-15 Stundenkontingent je Zyklus oder Zeitraum
- **Problem:** Das Soll gilt je Woche; „jede 2. Woche Mi frei“ oder Blockwochen müssen das Wochensoll in kürzerer Zeit erfüllen.
- **Schularten:** Berufsschule (Jahresstunden), Montessori, Waldorf, Schulen mit Wechselwochen/Praktika.
- **Anwendung:** Im Kurs „Soll: 64 Std. je 2 Wochen“ bzw. „je Epoche“; der Generator verteilt frei auf den Zeitraum; Bericht zeigt Ist/Soll je Zeitraum.
- **Datenmodell:** `Course.target {hours, period: week|cycle|phase|year, weeks}`.
- **Auswirkung:** Generator, Stundenplananzeige (Wochenplan weicht ab), Vertretung (Nachholen).
- **Aufwand:** M · **Priorität:** B

### W-16 Aufsichts- und Dienstplaner (Bereich × Zeit)
- **Problem:** Aufsichten entstehen je Bereich und Pause; Bereiche gelten nicht nur für bestimmte Pausen oder Zeiten (Abendpause erzeugte 200 unbesetzte Zeilen), keine Betreuungs-/Bereitschaftsdienste.
- **Schularten:** Grundschule, Ganztag (Mittagsband, Mensa), Montessori (Hofaufsicht, Hofdienst), Förderschule (Busaufsicht), Internat, Abendschule.
- **Anwendung:** Bereich → Gültigkeit (Pausen, Tage, Wochen); Dienste mit Beginn/Ende; Tausch durch Lehrkräfte; Fairness je Deputat.
- **Datenmodell:** `Area.rules [{breaks, days, weeks, needed}]`, `Shift {area, from, to, role}`.
- **Auswirkung:** Generator (Aufsichten), Vertretung (Ausfall im Dienst), Kalender.
- **Aufwand:** S–M · **Priorität:** B

### W-17 Einmal-Login und Einladungscodes
- **Problem:** Zugangsbriefe enthalten ein **Startpasswort** im Klartext; der QR-Code führt nur zur Anmeldeseite. Ein einmaliger Anmeldelink/Code (Passwort setzen, Gerät verknüpfen) existiert nicht, Eltern↔Kind-Verknüpfung per Code ebenfalls nicht.
- **Schularten:** alle; besonders Grundschule (Eltern), Ganztag, Berufsschule (Betriebe), Abendschule (Selbstanmelder).
- **Anwendung:** Brief mit **QR-Code + 8-stelligem Einmalcode** (läuft nach 14 Tagen ab, einmal einlösbar, setzt direkt das eigene Passwort); Einladung per E-Mail; Elterncode „Kind verknüpfen“.
- **Datenmodell:** `OneTimeToken {user, hash, purpose: first_login|link_child, expires, used_at}`.
- **Auswirkung:** Zugangsbriefe-PDF, Anmeldeseite, Verlauf (Audit); Generator/Plan unberührt.
- **Aufwand:** M · **Priorität:** A

### W-18 Formular-Baukasten (Beurlaubung, Krankmeldung, Einverständnis, Sonstiges)
- **Ist-Stand:** Vorhanden sind feste Vorgänge (Krankmeldung, Verspätung, Beurlaubung mit Status beantragt/genehmigt) und ein festes Entschuldigungsformular als PDF
  (`GET /student-absences/form.pdf`). Eigene Formulare oder Änderungen am Wortlaut/den Feldern sind nicht möglich (so auch `NUTZER-MELDUNGEN.md` Nr. 33).
- **Anforderungen aus Sicht der Schularten:**
  | Schulart | braucht zusätzlich |
  |---|---|
  | Grundschule | einfache Sprache, mehrsprachige Fassungen, Abholberechtigung, Mittagessen abmelden |
  | Montessori | Einwilligungen (Erdkinderplan, Fotos), Anmeldung zum Lernentwicklungsgespräch, Materialbeitrag |
  | Waldorf | Berichtszeugnis-Wünsche, Eltern-Beteiligung |
  | Gymnasium/Gesamtschule | Beurlaubung mit Fristen und Zuständigkeit (Klassenleitung ≤ 3 Tage, Schulleitung darüber), Attest ab Tag X |
  | Berufsschule | Ausbildungsbetrieb und Ausbilder/in als Zusatzunterschrift, Info an Betrieb bei Fehlzeiten, Freistellung für Prüfungen |
  | Förderschule | Gesundheitsdaten, Schulbegleitung/Nachteilsausgleich beantragen, Fahrdienst |
  | Ganztag | Anmeldung zu AG/Mittagsband, Abmeldung, Betreuungszeiten |
  | Abendschule | Arbeitgeber-Freistellung, Verspätungs-Regeln für Berufstätige |
- **Anwendung:** *Verwaltung → Formulare*: Vorlage wählen (Beurlaubung, Krankmeldung, Einwilligung, Anmeldung, Freitext) oder neu; Felder per Ziehen (Text, Auswahl, Datum, Datei, Unterschrift, bedingte Felder); Ablauf festlegen (wer reicht ein, wer genehmigt in welcher Reihenfolge, Fristen, Erinnerungen); Aktion bei Genehmigung (Eintrag in Fehlzeiten/Kalender, Mitteilung, PDF ablegen); Briefkopf/Logo; Versionen; Mehrsprachigkeit.
- **Datenmodell:** `FormTemplate {id, title, version, fields:[{key, type, label, required, show_if}], workflow:[{role, action, deadline}], on_approve:[action], pdf_layout}`, `FormSubmission {template, version, student?, data, status, history[], signatures[]}`.
- **Auswirkung:** Klassenbuch/Fehlzeiten (automatisch buchen), Kalender (Termin bei Beurlaubung), Vertretung (Ausfall bekannt), Benachrichtigungen, Datenschutz (Aufbewahrung je Formular), Rechte je Rolle.
- **Aufwand:** L (kann ein anderer Agent als eigenes Paket bauen; vorhandene Beurlaubungslogik als erste Vorlage übernehmen) · **Priorität:** A

### W-19 Moodle-/LMS-Import mit Feldzuordnung und Vorschau
- **Problem (getestet, siehe 5):** Moodle-Nutzerliste mischt Rollen und braucht einen Umweg; Moodle-Spalte `id` überschreibt `idnumber`; Kohorten ohne Jahrgang; Kurse ≠ Fächer; Einschreibungen und Rollen (Teilnehmer/in, Trainer/in) gehen nicht.
- **Schularten:** alle Schulen mit Moodle, itslearning, Schul-Cloud, mebis, Logineo.
- **Anwendung:** *Import → Plattform → Moodle*: Dateien hochladen (Nutzer, Kohorten, Kurse, Einschreibungen); Assistent schlägt Zuordnung vor (Kohorte → Gruppe, Kurs → Kurs/Kursteil, Rolle `editingteacher` → Lehrkraft, `student` → Teilnehmer); Vorschau mit Zahlen, Fehlern, Diff; Mapping als Profil speichern; Wiederholbar (Aktualisieren statt Duplikate).
- **Datenmodell:** `ImportProfile {platform, mappings, role_map}`, `ImportRun {profile, files, report, diff}`; Quellen-ID (`external_id`) an Lehrkraft/Kind/Kurs.
- **Auswirkung:** Stammdaten, Konten (optional anlegen), Kursräume; Generator unberührt.
- **Aufwand:** M · **Priorität:** B

### W-20 Import-Assistent und verlustfreie Austauschformate
- **Problem:** Untis-Rundlauf verliert Sperrzeiten, Arbeitszeitraster, Pausen, Stundentafeln, Termine, Aufsichten und Teilzuordnungen; der CSV-Import speichert Geburtsdatum/Jahrgang nicht; Raster nicht per CSV importierbar.
- **Schularten:** alle (Wechsel von Untis, DaVinci, SPlan, FET, Stundenplan24, ASV, SchILD).
- **Anwendung:** *Import / Export → Assistent*: Quelle wählen, Dateien ziehen, Zuordnung prüfen, Probelauf (Diff), Übernehmen mit Rückgängig; Verlustbericht („nicht übertragbar: …“); Export im selben Format zum Rückweg; OneRoster/CSV-Standard.
- **Datenmodell:** wie W-19 plus `ImportRun.lossless`.
- **Auswirkung:** Stammdaten, Planung, Verlauf (Undo).
- **Aufwand:** M · **Priorität:** B

### W-21 Konzept-Vorlagen je Schulart und anpassbare Begriffe
- **Problem:** Das Programm denkt in Klasse/Fach/Stunde; Montessori sagt Lerngruppe/Lernbereich/Lernbegleitung, Waldorf Epoche/Klasse, Berufsschule Lernfeld/Fachklasse. Neue Schulen müssen alles von Hand einrichten.
- **Schularten:** alle (Montessori, Waldorf, Jenaplan, Gesamtschule, Oberstufe, Berufskolleg, Förderschule, Ganztag, Abendschule, Hochschule).
- **Anwendung:** Beim Einrichten Vorlage wählen: bringt Zeitraster, Tagesrahmen (W-01), Fächerkatalog, Stundentafeln, Rollen/Rechte-Voreinstellung, Formulare (W-18), Begriffe. Danach frei änderbar; eigene Vorlagen exportieren/teilen.
- **Datenmodell:** `ConceptPack {id, name, settings, subjects, curricula, rights, forms, labels:{class:"Lerngruppe", subject:"Lernbereich"}}`; `Settings.labels`.
- **Auswirkung:** Oberfläche (Beschriftungen), Einrichtungsassistent, Generator (Regelvorlagen aus W-14).
- **Aufwand:** M · **Priorität:** A

### W-22 Standorte: Wegezeiten je Paar und tageweise Standorte
- **Problem:** Wegezeit gilt global (eine Zeitscheibe); Gruppen, die an bestimmten Tagen am anderen Standort sind (Hofgut Mi), gibt es nicht.
- **Schularten:** Montessori (Erdkinder), Verbundschulen, Berufskolleg, Förderschule, Hochschule.
- **Anwendung:** *Standorte → Wegezeiten*: Matrix in Minuten; Klasse/Gruppe „Standort je Tag“.
- **Datenmodell:** `SiteDistance {from, to, minutes}`, `Class.site_by_day`.
- **Auswirkung:** Generator (Wegezeit, Standort je Tag), Vertretung (nur nahe Lehrkräfte), Kalender.
- **Aufwand:** S–M · **Priorität:** B

### W-23 Lernentwicklung und Dokumentation (Beobachtung, Kompetenzraster, Berichtszeugnis)
- **Problem:** Kein Platz für Beobachtungen, Kompetenzraster, Lerntagebuch, Wortzeugnis; nur Noten und Fehlzeiten.
- **Schularten:** Montessori, Waldorf, Jenaplan, Gemeinschaftsschule, Förderschule (Förderplan).
- **Anwendung:** je Kind Raster/Beobachtungen pflegen, Gespräche planen, Berichtszeugnis aus Bausteinen erzeugen.
- **Datenmodell:** `Competency {grid, level}`, `Observation {student, date, text, area}`, `Report {student, period, text, status}`.
- **Auswirkung:** Klassenbuch, Elternansicht, Formulare (W-18), Planung (Gesprächstermine als Kalender).
- **Aufwand:** L · **Priorität:** C

### W-24 Planvarianten und Szenarien
- **Problem:** Es gibt genau einen Plan (Versionen im Verlauf). „Was wäre, wenn Hof und Haus Mi tauschen“ lässt sich nicht gefahrlos durchspielen und vergleichen.
- **Schularten:** alle, besonders vor Schuljahresbeginn.
- **Anwendung:** *Planung → Szenarien*: Kopie anlegen, Vorgaben ändern, Generator laufen lassen, Kennzahlen nebeneinander, Szenario zum Plan machen.
- **Datenmodell:** `Scenario {id, base_version, school_json, stats}`.
- **Auswirkung:** Generator (Parameter je Szenario), Verlauf.
- **Aufwand:** M · **Priorität:** C

### Top-10 (Reihenfolge nach Nutzen und Abhängigkeit)
1. **W-01** Tagesrahmen/Zeitanker · 2. **W-04** Team-Teaching · 3. **W-10** Raumverbünde · 4. **W-13** Generator-Diagnose · 5. **W-03** Lerngruppen/Jahrgangsspannen
6. **W-02** Blocklängen und mehrere Zeitraster · 7. **W-05** Wahl-/Konfliktprüfung je Kind · 8. **W-06** Epochenplaner · 9. **W-17** Einmal-Login · 10. **W-18** Formular-Baukasten
(**W-21** Konzept-Vorlagen und **W-08** Lernzeit-Block folgen direkt danach.)

## 5. Import aus anderen Plattformen (Simulation, Ergebnisse)

Erzeugt wurden erfundene **Moodle-Exporte** und ein **Untis-Export** unter [`beispiele/import/`](beispiele/import/):

| Datei | Inhalt | Import |
|---|---|---|
| `moodle_nutzer.csv` | 292 Nutzer (42 Kollegium, 250 Kinder): id, username, idnumber, firstname, lastname, email, department (Fächer), cohort1 (Lerngruppe), profile_field_geburtsdatum | **Umweg:** Datei nach Kollegium/Kindern trennen (`cohort1`), dann CSV-Import mit Mapping `idnumber→id, firstname/lastname→Name, department→Fächer, cohort1→Klasse`; Spalte `id` per `"id": null` abschalten, sonst werden Moodle-Nummern zu IDs. Ergebnis: 42 Lehrkräfte + 250 Kinder angelegt, 0 Fehler. Geburtsdatum nicht übernommen (Nachtrag per Skript) |
| `moodle_kohorten.csv` | 12 Lerngruppen + Kollegium | **Umweg:** als „Klassen“ importierbar, wenn Jahrgang ergänzt wird (Kollegium wird übersprungen) |
| `moodle_kurse.csv` | 28 Kurse (Freiarbeit, Epochen, Bänder, AGs) | **nicht sinnvoll:** nur als „Fächer“ importierbar (28 falsche Fächer); kein Weg zu Kursen/Kursteilen |
| `moodle_einschreibungen.csv` | Einschreibungen mit Rolle (student, editingteacher) | **nein:** 240 Zeilen übersprungen („Klasse fehlt“), kein Ziel für Kurs-Teilnahme/Rollen |
| `untis-export/GPU001–GPU015.TXT` | Export des gebauten Plans im Untis-Format | **direkt, aber verlustbehaftet** (siehe Schritt 29): Rundlauf in eine leere Instanz brachte 83 Kurse, 363 Stunden, 250 Kinder zurück, aber keine Sperren/Raster/Pausen/Tafeln/Termine/Aufsichten |
| `montessori-schule.json` | eigenes Planungsdokument | **direkt, verlustfrei** (Rundlauf geprüft) |

Fehlende Werkzeuge: W-19 (Moodle/LMS-Import), W-20 (Assistent + verlustfreie Formate), W-12 (Raster-Import).
Die Dateien wurden **nicht aus echten Moodle-Instanzen** erzeugt, sondern nach dem dokumentierten Aufbau der Moodle-Listen/Upload-Dateien nachgebaut; Spalten echter Exporte weichen je Version/Plugin ab.

## 6. Zugangsbriefe und Formulare

- Für jede Rolle liegt ein Beispiel-PDF unter [`beispiele/zugangsbriefe/`](beispiele/zugangsbriefe/): Lehrkraft, Schüler/in, Eltern, Schulleitung, Abteilungsleitung, Sekretariat, Stundenplanung,
  Hausmeister/in, Schulbegleitung, Zuschauer/in (je 2 Briefe; Personen erfunden). **Die PDFs enthalten Startpasswörter der lokalen Test-Instanz; hier nicht abgedruckt.**
- Brief = Benutzername + Startpasswort + QR-Code zur Anmeldeseite + Anleitung; bei der ersten Anmeldung Passwortwechsel. Kein Einmal-Login (W-17).
- Formulare: nur feste Vorgänge (W-18).

## 7. Empfehlung: Reihenfolge des Bauens

1. **Diagnose zuerst (W-13)** – kleiner Aufwand, nützt jeder Schule sofort und beschleunigt alle weiteren Tests.
2. **Fundament der Planung:** W-10 (Raumverbünde) → W-04 (Team-Teaching) → W-01 (Tagesrahmen) → W-02 (Blocklängen/Raster). Danach kann der Generator die Montessori-Tagesstruktur planen.
3. **Gruppen und Kinder:** W-03 (Lerngruppen, Jahrgänge) → W-05 (Wahlen/Konfliktprüfung) → W-06 (Epochen) → W-07 (Teilgruppen-Blockphasen).
4. **Einrichten und Zugang:** W-17 (Einmal-Login), W-21 (Konzept-Vorlagen), W-19/W-20 (Importe) – diese drei machen aus dem Programm ein Produkt für viele Schulen.
5. **Formulare (W-18)** parallel als eigenes Paket (anderer Agent), mit der vorhandenen Beurlaubung als erster Vorlage.
6. **Danach:** W-08 (Lernzeit-Block), W-11 (Präsenz-Deputat), W-12 (Verfügbarkeiten), W-15 (Kontingente), W-16 (Dienste), W-22 (Standorte), W-09 (Wochenpläne je Kind), W-14 (Regeleditor).
7. **Später:** W-23 (Lernentwicklung), W-24 (Szenarien).

Vor jedem Werkzeug: Beispieldatei `beispiele/montessori-schule.json` in eine leere Instanz laden und als Regressionstest nutzen (Zahlen unter 1.2, Wochenplan unter 1.3, Generatorlauf 3 ohne unverplante Blöcke).

## 8. Reproduzierbarkeit

Bauskripte (nicht Teil des Repos): `scratchpad/build1.py … build6.py`, Datenerzeugung `data_mont.py`, `gen_moodle.py`; Instanz `scratchpad/montessori_dev.py`
(Backend 127.0.0.1:8796, Vite 5176, eigene Datenbank `montessori.db`, `SM_LOAD_DEMO=0`, `SM_HOLIDAY_IMPORT=0`).
Die Instanz wurde am Ende gestoppt; das Passwort des Test-Administrators steht nur im Skript.
