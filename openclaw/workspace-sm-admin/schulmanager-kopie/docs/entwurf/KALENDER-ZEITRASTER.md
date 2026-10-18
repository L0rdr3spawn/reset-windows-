# Kalender und Zeitraster – Umsetzungsentwurf (Verlauf)

> **Überholt für Wochen.** Das hier beschriebene Modell mit Wochenzyklus, Zykluswochen und Zyklus je Klasse ist
> ersetzt: Es gibt nur noch laufende Wochen 1–52 und Wochenangaben (jede Woche, ausgewählte Wochen oder Rhythmus
> „jede k. Woche ab Woche s“). Maßgeblich ist `docs/ARCHITECTURE.md` §12; ältere Dokumente rechnet
> `schulmanager/legacy.py` beim Laden um. Abschnitte zu Schuljahr, Zeitraster, Unterrichtstagen und Anzeige gelten
> weiter. Begriffe wie „Zyklus“ stehen unten nur als Beschreibung des früheren Entwurfs.

Stand 11.10.2026, Arbeitsbaum Runde 2. Bezug: A-28, A-29, A-30, A-31, A-32, A-51, A-67, A-68, A-69; U-06, U-13, U-15,
U-16, U-49, U-51, U-52, U-56, U-84. Grundlage sind die Bestandsaufnahmen „Wochen/Tage“ und „Zeitraster“ vom 11.10.
Alle Fundstellen (Datei:Zeile) wurden am 11.10. geprüft. Zeilen in Dateien der Runde 2 (`substitution.py`,
`features_substitutions.py`, `features_common.py`, `SubstitutionsPage`, `EntryTable`, `lib/substitution.ts`,
`SettingsPanels.tsx`) können sich verschieben. Dieser Entwurf ändert keinen Code. Er legt Datenformen, Regeln,
Verträge und Pakete für die Runden 3 und 4 fest. **§14 „Prüfvermerk 1“ geht §1–§13 vor**, wo er etwas anderes sagt;
**§15 „Prüfvermerk 2“ geht §1–§14 vor**. Maßgeblich für Felder und Schnittstellen ist der Vertrag in §15.3.

## 1. Begriffe und Grundsätze

| Begriff | Festlegung |
|---|---|
| Laufende Woche L | Woche 1 … Y des Schuljahres (Y = 52 oder 53), immer Mo–So. Ferienwochen zählen mit. Im KW-Modus ist L die KW. |
| KW | Kalenderwoche nach ISO 8601 (`date.isocalendar()`), wird immer zusätzlich angezeigt. |
| Zyklus N | Anzahl unterschiedlicher Wochen, 1 … 53 (1 = jede Woche gleich). Schulvorgabe `Settings.cycle_weeks`, je Klasse abweichend (§3). |
| Zykluswoche k | k = (L − s) mod N + 1, s = Startwoche des Zyklus (Standard 1). Gespeichert wird w = k − 1 (0-basiert wie heute in allen `weeks`-Listen). |
| Wochenmuster | Menge von Zykluswochen (`weeks: list[int]`, leer = alle). Die Eingabe ist auch als „jede k. Woche ab Woche s“ möglich (§4). |
| Wochenvariante | Nur intern im Generator: Zykluswochen mit identischen Bedingungen werden zusammengefasst (§7.2). Sie wird nie angezeigt. |
| Unterrichtstage | Wochentage 0 = Mo … 6 = So, je Klasse (Standard: Schulvorgabe Mo–Fr). |
| Schultag | Für eine Klasse: einer ihrer Unterrichtstage ohne Ferien oder Feiertag. Schulweit: Unterrichtstag mindestens einer Klasse („Schulöffnungstag“), ohne Ferien oder Feiertag. |
| Zeitraster | Benannte Vorlage mit Stunden (Beginn, Ende) und Pausen. „Standard“ ergibt sich aus den heutigen Settings-Feldern; weitere Raster legt die Schule an (§6). |
| Stunde | Index im Zeitraster der Klasse (0-basiert, Anzeige „1.“). Die Uhrzeit kommt immer aus dem Raster der Klasse. |
| Zeitfenster | Verfügbarkeit einer Lehrkraft in Uhrzeit (`Teacher.time_windows`, models.py:95). Uhrzeit ist hier die maßgebliche Angabe. |
| Zeitachse | Minuten seit 0:00 an einem Wochentag. Darauf werden alle Konflikte über Klassen hinweg geprüft. |

Grundsätze (G1–G9):
- **G1** Nirgends erscheinen Wochenbuchstaben: weder in Anzeige, Meldungen, Export noch Dateinamen. Importe lesen Buchstaben
  als Altformat (A = Woche 1, B = Woche 2 …).
- **G2** Wochen werden durchgehend gezählt. Ferienwochen zählen mit und werden nur markiert (A-68).
- **G3** Die Zykluswoche wird aus der laufenden Woche abgeleitet. In Datumsbezügen heißt sie „Zykluswoche k von N“, in
  Wochenmustern „Woche k“ (Feldname „Wochen im Zyklus“). Bei N = Y fallen beide Zahlen zusammen.
- **G4** Jede Woche hat 7 Tage. Unterrichtstage gelten je Klasse; Sa/So sind planbar und werden angezeigt.
- **G5** Jede Klasse hat ein Zeitraster mit eigener Stundennummer. Die „1. Stunde“ der Abendklasse beginnt um 16:00.
- **G6** Konflikte von Lehrkräften, Räumen, Aufsichten und Kursen über mehrere Klassen gelten bei Überlappung der Uhrzeit
  `[Beginn, Ende)`. Die Stundennummer entscheidet nicht.
- **G7** Innerhalb einer Klasse bleibt der Index im Klassenraster die Einheit (Belegung, Rand, Hohlstunde).
- **G8** Gespeichert wird weiter 0-basiert (`weeks`, `day`, `start`, `periods`). Jedes neue Feld hat einen Standardwert,
  und alte Dokumente rechnen unverändert. Nachgerechnet: Mit Anker = `cycle_start` gilt `week_of(d) == (L−1) mod N` für
  N ∈ {1, 2, 3, 4, 8} über −400 … +800 Tage.
- **G9** Jede Regel liegt an genau einer Stelle: Wochen in `calendar_utils.py`, Muster und Aktiv-Logik im neuen
  `schulmanager/weeks.py`, Raster und Zeitachse im neuen `schulmanager/timegrid.py` (R4). Das Backend liefert fertige Texte
  (`week_text`); das Frontend formatiert nur noch.

## 2. Wochen

### 2.1 Einstellungen (neu in `Settings`, models.py:323ff., jeweils mit Standardwert)
| Feld | Typ / Standard | Bedeutung |
|---|---|---|
| `week_numbering` | `"school_year"` | `"school_year"` (Woche 1 ab Schuljahresbeginn) oder `"iso"` (laufende Woche = KW) |
| `school_year_start` | `""` | ISO-Datum. Leer bedeutet `cycle_start` (Altdokumente, Standard 2026-08-31) |
| `school_year_end` | `""` | Leer: Tag vor dem nächsten Anker mit Woche 1, sonst Beginn + 1 Jahr − 1 Tag |
| `week_anchors` | `[]` | `[{"date": "JJJJ-MM-TT", "week": 1…53, "note": ""}]`: frühere Schuljahre und Korrekturen „ab Datum Woche k“ |
| `school_days` | `[]` | Schulvorgabe der Unterrichtstage 0–6. Leer bedeutet `range(days)` (§5) |
| `cycle_weeks` | `1` | Grenze neu 1 … 53 (heute ≤ 8, features_data.py:750) |
| `cycle_start` | bleibt | Wird nur noch gelesen. `PUT` nimmt das Feld weiter an und setzt dann `school_year_start`, solange dieses leer ist |

### 2.2 Berechnung (`calendar_utils.py`, neue Funktionen)
```
anchors(st)        = sortiert [(monday_of(school_year_start or cycle_start), 1)] + [(monday_of(a.date), a.week) …]
running_week(st,d) = iso:  d.isocalendar().week
                     sonst: m = monday_of(d); A = letzter Anker mit A.monday <= m (sonst der erste)
                            A.week + (m − A.monday).days // 7          # vor dem ersten Anker ≤ 0
cycle_week(st,d,N=st.cycle_weeks,s=1) = (running_week(st,d) − s) mod N    # 0-basiert
weeks_in_year(st)  = (monday_of(Ende + 1 Tag) − monday_of(Beginn)).days // 7   # 52 oder 53
week_info(school, d, cls=None) -> WeekInfo (§11.2)
```
- **Beginn mitten in der Woche**: Ein Anker gilt für die ganze Woche (Mo–So), in der sein Datum liegt. Beispiel 01.08.2026
  (Samstag): Woche 1 = 27.07.–02.08.2026. Gehört eine Woche zu zwei Ankern, gilt der neuere; damit wird keine Woche
  geteilt. Zwei Anker in derselben Woche weist die Prüfung ab (422).
- **Länge des Schuljahres**: Bei 1.8.–31.7. hat 2025/26 52 Wochen, 2026/27 52, 2027/28 53 (nachgerechnet). Bei 53 Wochen
  ist ein Zyklus N = 53 erlaubt. Ist N > Y, warnt die Prüfung „Zykluswoche 53 kommt in diesem Schuljahr nicht vor“.
- **Schuljahreswechsel**: Wird `school_year_start` auf ein späteres Datum gesetzt, legt `PUT /settings` den alten Beginn
  selbst als Anker `{date: alt, week: 1, note: "Schuljahr 2025/26"}` ab. Vergangene Tage behalten so ihre Woche:
  Vertretungspläne, Statistik, iCal-UIDs und Benachrichtigungs-Diffs werden live berechnet (Risiko „Rückwirkung“).
  Anker, die älter als zwei Schuljahre sind, dürfen entfallen.
- **Manuelle Korrektur**: Ein Anker `{date, week: k}` legt „ab der Woche dieses Datums gilt Woche k“ fest, z. B. zum
  Wiederholen oder Überspringen einer Zykluswoche. Das gibt es nur im Modus `school_year`. Im Modus `iso` werden Anker
  ignoriert; die Prüfung meldet das als Warnung.
- **Jahreswechsel im KW-Modus**: Die Zykluswoche ist streng (KW − 1) mod N + 1. In Jahren mit KW 53 (2026, 2032) bricht
  der Wechsel: KW 53 und KW 1 haben bei N = 2 beide Zykluswoche 1 (nachgerechnet). Die Wochenübersicht der Einstellungen
  zeigt das als Warnung. Wer lückenlos zählen will, nimmt den Modus `school_year`. Dort gibt es am Jahreswechsel keinen
  Bruch; er fällt auf den Schuljahreswechsel, weil das neue Schuljahr mit Woche 1 beginnt.
- **Vor dem ersten Anker** zählt die Woche rückwärts weiter (L ≤ 0); die Zykluswoche wird per Modulo berechnet wie
  heute (models.py:366-369). Für L < 1 oder L > Y zeigt die Anzeige nur die KW.

### 2.3 Ferienwochen
`Holiday` bekommt `kind: str = "ferien"` (`ferien | feiertag | beweglich | sonstiges`, models.py:253-262). Damit
entfällt das Raten über den Namen in `features/classes/WeekTab.tsx`. Eine Woche gilt als Ferienwoche
(`holiday_week = true`), wenn alle Schulöffnungstage der Woche Ferien- oder Feiertage sind. Tage tragen zusätzlich
`day_kind ∈ unterricht | kein_unterrichtstag | ferien | feiertag`. `DayPlan.holiday` bleibt erhalten (Name bzw.
„Wochenende“) und wird an Ferien- und Wochenendtagen weiter befüllt (substitution.py:1248-1252).

### 2.4 Anzeige
Den Text `week_text` baut nur das Backend. Das Frontend zeigt ihn an und formatiert Wochenlisten mit `lib/weeks.ts`.
- Schuljahr, N = 1: „Woche 12 · KW 45“. Bei N > 1 und k ≠ L zusätzlich „ · Zykluswoche 3 von 6“; bei N = Y und s = 1
  entfällt der Zusatz, weil k = L ist.
- KW-Modus: „KW 45“, bei N > 1 zusätzlich „ · Zykluswoche 1 von 2“.
- Ferienwoche: ein eigenes Badge „Ferien“ (bzw. der Name der Ferien), nicht Teil von `week_text`.
- Das Altfeld `week_label` ist ab R3 `str(k)` bei N > 1, sonst `""`. Ältere Oberflächen zeigen dann „Woche 2“ statt
  „Woche B“, ohne dass sich etwas anderes ändert. `Settings.week_label(w)` (models.py:371-372) liefert `str(w + 1)`.
  Damit sind alle Backend-Texte mit `week_label` frei von Buchstaben (timetable.py:265/414-426, features_classes.py:108,
  untis_gpu.py:346, csv_io.py:226/321 mit `chr(65 + w)` → Zahl).
- Die Meldung „Woche {0-basiert}“ in timetable.py:414 wird zu „Woche k“ (1-basiert, Zykluswoche).

## 3. Zyklus je Klasse (A-29)
- Neue Felder in `SchoolClass` (models.py:115-131): `cycle_weeks: int = 0` (0 = Schulvorgabe) und
  `cycle_start_week: int = 1`, die laufende Woche, in der Zykluswoche 1 der Klasse liegt. Beispiel Berufskolleg FI11c:
  `zyklus_start` 2026-09-07 bei Schulbeginn 2026-08-31 ergibt 2 (docs/beispielschulen/berufskolleg-nrw.json:581-582).
- Wochenlisten beziehen sich immer auf den Zyklus ihres Eigentümers:
  - Klasse (`SchoolClass.unavailable`) → Zyklus der Klasse.
  - Kurs und Stunde (`Course.weeks`, `Lesson.weeks`) → Zyklus des Kurses, also der gemeinsame Zyklus seiner Klassen.
  - Lehrkraft (Sperren, Wünsche, Zeitfenster) und Aufsicht (`Duty.weeks`) → Schulvorgabe (s = 1).
- **Kopplung über Klassen mit verschiedenem Zyklus** (N oder s verschieden) ist nur wöchentlich erlaubt: `Course.weeks`
  muss leer sein und jedes `Lesson.weeks` auch. Sonst lehnt `validate_item(courses)` mit 422 ab: „Kopplung über Klassen mit
  unterschiedlichem Wochenzyklus ist nur wöchentlich möglich“.
- **Planungshorizont** H = kgV aller verwendeten N (Schulvorgabe und Klassen), höchstens 53. Bei mehr lehnt die Prüfung
  ab: „Zyklen 2 und 27 Wochen ergeben zusammen 54 Wochen – höchstens 53“. Die globale Woche ist g = (L − 1) mod H. Ein
  Wochenmuster W im Zyklus (N, s) ist in g aktiv, wenn (g + 1 − s) mod N ∈ W; das stimmt, weil N ein Teiler von H ist.
  Die Umrechnung macht `weeks.to_global`.
- **Konfliktregel**: Zwei Blöcke stoßen zusammen, wenn sie dieselbe Lehrkraft, denselben Raum oder dieselbe Klasse haben
  und sich in den globalen Wochen, im Wochentag und in der Uhrzeit (§7) überschneiden. Die Meldung nennt die erste
  laufende Woche und den Abstand: „Lehrkraft T doppelt belegt: Mo 08:45–09:30, Woche 1 und jede 6. Woche“.
- **Zykluswechsel (U-13)**: `weeks.convert(weeks, alt, neu)` rechnet um, wenn sich N der Schule oder einer Klasse ändert.
  - neu ist ein Vielfaches von alt: periodisch wiederholen, exakt (2 → 52 ergibt aus [0] die Liste [0, 2, 4, …]).
  - alt ist ein Vielfaches von neu und die Liste ist periodisch: zusammenfassen, exakt.
  - sonst verlustbehaftet: Wochen < neu bleiben, die übrigen fallen weg, Stunden ohne Woche werden gelöscht.
  Umgerechnet werden `SchoolClass.unavailable`, `Course.weeks`, `Lesson.weeks`, `Teacher.unavailable/wishes/time_windows`
  und `Duty.weeks`, danach läuft `refresh_all_windows`. `POST /settings/calendar-preview` zeigt die Wirkung vorab.
  `PUT /settings` und `PUT /data/classes/{id}` antworten bei Verlust mit 409 `{code: "cycle_change", changes}`, außer
  `force_cycle_change: true` ist gesetzt. Der Scope ist dann `["settings", "teachers", "classes", "courses", "timetable",
  "duties"]` (heute nur `settings`/`teachers`, features_data.py:826-827).

## 4. Wochenmuster (A-51)
- **Eine Datenform**: `weeks: list[int]`, 0-basierte Zykluswochen, sortiert und eindeutig; leer heißt alle Wochen, wie
  heute in `Course`, `Lesson`, `TimeRule`, `time_windows` und `Duty`. Eine zweite Form wird nicht gespeichert.
  Requests dürfen statt `weeks` ein Muster `week_pattern: {every: k, from: s, to?: e}` (1-basiert) senden. Der Server
  rechnet es mit `weeks.expand` in eine Liste um und speichert nur die Liste.
- **Text**: `weeks.describe(weeks, N)` gibt den kürzesten Text aus. Leer → „jede Woche“. Eine arithmetische Folge mit
  Schritt k ≥ 2, die bis zum Zyklusende reicht → „jede 3. Woche ab Woche 2“. Sonst → „Woche 1–4, 9“.
  `lib/weeks.ts describeWeeks` macht dasselbe im Frontend (gleiche Testfälle).
- **Validierung** (`weeks.errors`): nur ganze Zahlen mit 0 ≤ w < N, höchstens 53 Einträge, doppelte Einträge entfallen,
  alle Wochen → []. Muster: 1 ≤ k ≤ N, 1 ≤ s ≤ N, e ≥ s. Passt k nicht in N (kein Teiler), gibt es nur einen Hinweis
  „Muster wiederholt sich nicht gleichmäßig“. U-15: Eine `TimeRule` mit leeren `weeks`, `days`, `periods` und ohne
  Uhrzeit wird abgewiesen (features_data.py:93-104, teacher_profile.py:314).
- **Zentrale Aktiv-Logik** `weeks.active_weeks(school, lesson, course) -> frozenset[int]` im Kurszyklus:
  (`Lesson.weeks` ∩ [0, N) oder alle) ∩ (`Course.weeks` ∩ [0, N) oder alle). Ist der Schnitt leer, findet der Block nie
  statt, und `validate_school` meldet „liegt in keiner Woche des Kurses“. `weeks.lesson_active_on(school, les, course, d)`
  prüft Wochentag und Zykluswoche des Kurses am Datum. Diese Funktion ersetzt die fünf heutigen Varianten:

| heute | Stelle | Verhalten heute |
|---|---|---|
| Engine, Kursräume, Klausuren, Aufsichten, Klassen-Seite | substitution.py:316-324, channels.py:552-561, exams.py:23-35, duties.py:33, features_classes.py:93-109 | Lesson, sonst Kurs, sonst alle |
| Integrationen | integrations/_common.py:75-83 `effective_weeks` | Schnitt, leer → Lesson-Wochen |
| Ansicht/Bericht | timetable.py:14-25 `lesson_weeks` | nur Lesson |
| Rasteransicht | timetable.py:163, frontend lib/grid.ts:37-41 `filterWeek` | nur Lesson, ohne Bereichsprüfung |

  Nachgewiesene Folge: `Lesson.weeks = []` mit `Course.weeks = [0]` steht heute im Stundenplan in Woche B, ist aber im
  Kursraum dort inaktiv. Ab R3 filtert der Server die Zellen; `filterWeek` entfällt.
- **Abbildung der heutigen Formen**:
  - Gespeicherte Daten bleiben: `[0]`/`[1]` bei N = 2 heißen ab jetzt „Woche 1“/„Woche 2“.
  - CSV: Export `1,2` statt `A,B` und „Woche 1: Mi Std. 6-8“ statt „Woche A: …“. Der Import liest beide Formen, Bereiche
    „1-4,9“ und mehrstellige Zahlen (heute nur ein Zeichen, csv_io.py:248/326; ab N = 27 `ValueError`).
  - Untis: Text „(Woche 1)“ bzw. „(Woche 1, 3)“; der Import liest auch „Woche A–Z“ und „A-Woche“ (untis_gpu.py:156).
    Meta `cw/lw/cy` bleibt 0-basiert.
  - Blockphasen mit festem Datum (Betriebspraktikum, Blockunterricht) sind kein Wochenmuster, sondern
    `Absence(kind="class")` mit Datumsbereich. gesamtschule-nrw.json:443-447 zählt dort „Schulwochen“ ohne Ferien:
    2027-02-22 heißt dort Woche 23, nach §2 bei Beginn 31.08. Woche 26.

## 5. 7-Tage-Woche (A-32, A-68)
- **Tage**: `WEEKDAYS` bekommt 7 Namen (models.py:20, heute 6, U-49). `SchoolClass.school_days: list[int] = []` (leer
  bedeutet Schulvorgabe). `calendar_utils.class_days(school, cls)` und `open_days(school)` (Vereinigung aller Klassen)
  liefern die Tage. `Settings.days` bleibt gespeichert und wird beim Speichern von `school_days` auf max + 1 gesetzt, damit
  Alt-Aufrufer weiter richtig lesen. Neuer Code nutzt nur die Helfer.
- **Schultag**: `is_school_day(school, d, cls=None)` (calendar_utils.py:33-41) schließt Ferien aus. Mit Klasse entscheidet
  ihr Unterrichtstag, ohne Klasse der Schulöffnungstag. Zurück kommt weiter `(bool, Grund)` mit „Wochenende“ bzw. dem
  Ferienname; dazu `day_kind`.
- **Generator**: D = 7 (scheduler.py:82). Tage außerhalb von `class_days` sind für die Klasse gesperrt. `best_slot` und
  `_repair` durchlaufen nur Tage, an denen alle Klassen des Kurses Unterricht haben. `class_avail_day`/`class_target`
  zählen schon heute nur verfügbare Tage (scheduler.py:186-197). Die Fach-Tagesgrenze im manuellen Verschieben nutzt
  dieselben Tage wie der Generator (U-51, timetable.py:299-300).
- **Vertretung und Tagesplan**: `compute_day_plan` rechnet jeden Tag. Tage ohne Unterricht einer Klasse ergeben
  `day_kind = kein_unterrichtstag` und keine Einträge. `compute_range`, `week_history` (Wochenlimit Mo–So) und
  `features_common.range_plans` laufen über 7 Tage statt `weekday < days` (substitution.py:1305).
- **Monitor und Startseite**: „heute und die nächsten Schultage“ sind die nächsten Schulöffnungstage.
- **Datumsnavigation** (`DateNav`, `lib/dates.ts:41-56`): springt über Schulöffnungstage (`open_days` aus
  `GET /calendar/school-year`). Ferientage werden wie heute nicht übersprungen, sondern als Ferien gezeigt. Wochenweises
  Blättern umfasst immer Mo–So.
- **Termine**: Klausuren an Sa/So sind erlaubt, wenn der Tag ein Unterrichtstag der Klasse ist. Sonst lautet das Problem
  „kein Unterrichtstag der Klasse“ (exams.py:79-84, statt „Wochenende“). Klausuren je Woche zählen weiter Mo–So
  (exams.py:100-101). Attest: `student_self` zählt die Unterrichtstage der Klasse. iCal: alle Unterrichtstage ohne Ferien
  (ical.py:236). Sa/So-Spalten zeigt §8.

## 6. Zeitraster je Klasse (A-31, A-69)
- **Datenmodell**: neue Sammlung `time_grids` (`COLLECTIONS` und `School`, models.py:375-415):
  ```
  TimeGrid(id, name, periods: list[{"start": "HH:MM", "end": "HH:MM"}],
           breaks: list[{"after": int, "name": str, "minutes": int, "splits_double": bool = True}],
           core_latest: Optional[int] = None)
  ```
  „Standard“ (`id="standard"`) ist virtuell. Es entsteht aus `Settings.periods/period_times/period_minutes/breaks/
  core_latest_period`, wird nicht gespeichert und im bisherigen Zeitraster-Reiter bearbeitet. So rechnen alte Dokumente
  ohne Umzug.
- **Stundenlänge frei**: Jede Stunde hat Beginn und Ende. Der Rechner `timegrid.preview(start, lengths|length, breaks,
  count)` erzeugt die Zeiten (Ausbau von B-16 `POST /settings/period-times/preview`).
- **Prüfung** (`timegrid.errors`, auch für Standard, behebt U-16): Beginn < Ende, Ende ≤ 24:00, keine Überlappung (Ende
  i ≤ Beginn i+1), 1 … 16 Stunden. Pause: `after` liegt in 0 … n−2 (U-82), `minutes` ≤ Abstand der Nachbarstunden.
  Heute wird 08:00/08:10 bei 45 min angenommen (features_data.py:770-795); künftig weist die Prüfung das ab.
- **Zuordnung**: `SchoolClass.time_grid: str = ""` (leer = Standard), `SupervisionArea.time_grid: str = ""`. Löschen
  eines verwendeten Rasters gibt 409 (`features_data.references`/`cascade_delete`). Ein Raster je Wochentag ist nicht
  vorgesehen (Entscheidung E3).
- **Stundennummer je Raster**: Im Raster der Klasse bzw. des Kurses zählen `Lesson.start`, `Exam.start`, `Override.period`
  (an der Stunde) und `Absence.periods` für `kind = class|lesson`, außerdem die SQL-Felder `student_absences.periods`
  (db_models.py:149) und `channel_items/folders.lesson_period` (feature_models/channels.py:125/154). „1.“ ist die erste
  Stunde dieses Rasters.
- **Kurse über mehrere Klassen**: Alle Klassen eines Kurses haben dasselbe Raster, sonst 422 „Kopplung nur zwischen
  Klassen mit demselben Zeitraster“. Schüler/innen besuchen nur Kurse ihrer Klasse (`student_parts`, timetable.py:59). Ihre
  Konflikte sind damit Klassenkonflikte im selben Raster. `validate_school` prüft für alle mit gewählten Kursteilen
  zusätzlich nach Uhrzeit.
- **Lehrkraft und Abendunterricht vereinheitlichen**:
  - `TimeRule` erhält `start: str = ""` und `end: str = ""`. Sind sie gesetzt, trifft die Regel jede Stunde, deren
    Zeitspanne [start, end) überschneidet; `periods` wird dann ignoriert. Die Oberfläche erfasst neue Lehrkraft-Sperren in
    Uhrzeit.
  - `windows_to_rules` (teacher_profile.py:204-236) erzeugt Uhrzeit-Regeln statt Index-Regeln (Notiz „Zeitfenster …“
    bleibt). Die Fenster gelten so in jedem Raster; `refresh_all_windows` ist nur noch beim Zykluswechsel nötig.
  - Alte Lehrkraft-Regeln mit `periods` gelten als Stunden des Standard-Rasters und werden über deren Uhrzeit geprüft.
    `Absence` erhält `start`/`end` für `kind = teacher|room`; alte `periods` zählen im Standard-Raster.
- **Weitere Felder**: `Settings.site_travel_minutes: int = 0` (0 = `site_travel_periods × period_minutes`) und
  `Settings.long_gap_minutes: int = 120` (Lücken ab dieser Länge sind keine Springstunden). `max_periods_per_day` gilt als
  Anzahl, nicht mehr als höchster Index (scheduler.py:115, timetable.py:271). Im Standard-Raster bleibt das Ergebnis
  gleich, solange keine Sperre vor der ersten Stunde liegt.
- **Demo** (demo.py:78-80, 86-89, 246-300): Standard wieder mit 10 Stunden. Raster „Abend“: 16:00, 16:50, 17:40, 18:30,
  19:20, 20:10, je 45 min. ABK bekommt „Abend“ und braucht weder die Sperre der Stunden 0–8 noch
  `max_periods_per_day = 12`. SPT (ab 10:00, unterrichtet auch die ABK) bleibt der Prüffall „früh und abends“.

## 7. Konflikte nach echter Uhrzeit
### 7.1 Zeitachse
`timegrid.timeline(school)` sortiert die Grenzen (Beginn und Ende) aller Stunden aller verwendeten Raster. Ein Zeitatom
ist ein Abschnitt zwischen zwei Grenzen, den mindestens eine Stunde überdeckt. Jede Stunde (Raster g, Stunde p) entspricht
einem zusammenhängenden Atombereich `[a0, a1)`. Ein Block der Länge n belegt alle Atome von Beginn(p) bis Ende(p+n−1),
also auch die Pause dazwischen. Nachgerechnet: Standard allein hat 10 Stunden und 10 Atome, also genau das heutige
Gitter. Standard + Abend haben 16 Stunden und 15 Atome (16:00 ist zugleich Standard-Stunde 10 und Abend-Stunde 1). Mit
einem zusätzlichen 90-Minuten-Raster sind es 21 Stunden und 32 Atome.

### 7.2 Generator (scheduler.py)
- **Gitter**: Klasse V × 7 × P_Klasse (Index im eigenen Raster), Lehrkraft und Raum V × 7 × A (A = Zahl der Atome).
  `slot = ((w·D)+d)·P+p` (scheduler.py:204-205) gibt es je Gitterart.
- **Wochenvarianten**:
  - Jede globale Woche g < H bekommt eine Signatur aus der Zugehörigkeit von g zu jeder auf H ausgedehnten Wochenliste:
    Klassen- und Lehrkraft-Regeln, Fenster, `Course.weeks`, fixierte `Lesson.weeks`. Hinzu kommt die Phase
    (g + 1 − s) mod N jedes Klassenzyklus, der von der Schulvorgabe abweicht.
  - Wochen mit gleicher Signatur bilden eine Variante v mit Vielfachheit m_v. Die Kosten werden mit m_v · V / H
    gewichtet; die Summe der Gewichte ist V wie heute bei W = V.
  - Nachgerechnet an der kleinen Demo: N = 1 → 1 Variante, N = 2 → 2, N = 6 mit „jede 3. Woche“ → 4, N = 52 mit Regeln
    nur in Woche 1/2 → 3 (Größen 1, 1, 50). Heute rechnet der Generator bei N = 52 mit 52 Wochen: 3120 Slots je Objekt,
    450 Blöcke unverplant in 3 s, 4695 statt 148 Aufsichten.
- **Phasenregel**: Ein Block umfasst immer vollständige Zykluswochen seines Kurses. Im Schulzyklus ist jede Variante
  schon eine Menge ganzer Zykluswochen. Bei Klassen mit eigenem Zyklus liegt ein Block in allen Varianten derselben Phase
  gleich, damit sich der Plan der Klasse nach N Wochen wiederholt. `_make_blocks` (scheduler.py:208-228) arbeitet über
  Varianten („gemeinsame zuerst“). `_split` (scheduler.py:603-613) teilt nur nach Varianten bzw. Phasen. `result`
  (scheduler.py:881-899) rechnet in `Lesson.weeks` des Kurszyklus zurück; [] heißt weiter alle.
- **Harte Prüfungen** (`check` und `_blockers`, scheduler.py:243-291/547-565): Klassenslots frei und nicht gesperrt.
  Atombereich jeder Lehrkraft und jedes Raumes frei und nicht gesperrt; Lehrkraft-Sperren werden als Atome geführt (aus
  der Uhrzeit-Regel bzw. der Standard-Spanne). Die Tageshöchstzahl der Lehrkraft zählt Stunden. Die Wegezeit zwischen
  Blöcken an verschiedenen Standorten wird in Minuten gerechnet (`site_travel_minutes`).
- **Doppelstunden (A-30, U-06)**: Ein Block der Länge 2 ab p ist verboten, wenn eine Pause des Klassenrasters mit
  `splits_double` nach p liegt. Bei ungerader Stundenzahl bleibt eine Einzelstunde (wie heute `emit`). Heute liegen 22 von
  70 Doppelstunden über einer Pause.
- **Kosten**: Springstunden der Lehrkraft werden in Minuten gemessen und in Stunden-Äquivalente umgerechnet (Lücke ÷
  Standardlänge). Lücken ≥ `long_gap_minutes` zählen nicht; heute zählt die Lücke Vormittag–Abend als Springstunden
  (scheduler.py:413-438, `teacher_gaps` 475 in der Mini-Demo). „Hauptfach spät“, später Beginn und Position gelten je
  Raster (`core_latest`); die ABK ist dann nicht mehr „spät“.
- **Laufzeit**: Je Iteration wächst der Aufwand linear mit V × A; die Zahl der Kandidaten (Tage × Startstunden) bleibt
  wie heute, weil Tage ohne Unterricht übersprungen werden.
  - Beispiel: N = 52 mit 3 Varianten und Abendraster ergibt 3 × 7 × 15 = 315 Atome je Lehrkraft statt heute 3120 Slots.
  - Ersatzlauf kleine Demo, 3 s: W = 2 → 0 unverplant, W = 3 → 9, W = 6 → 36, jeweils ≈ 3,0 s. Mehr Varianten machen den
    Plan schwerer, nicht langsamer. Mit der Standardzeit von 20–30 s ist V ≤ 6 realistisch.
  - Ab V > 8 warnt der Generator „Viele unterschiedliche Wochen – Rechenzeit erhöhen oder Blockphasen als Abwesenheit
    führen“. Ungünstigster Fall V = 53 (53 × 7 × 15 ≈ 5600 Atome je Lehrkraft), vergleichbar mit dem heutigen W = 52.
- **Aufsichtsplaner** (duties.py:51-147): rechnet je Variante statt je Woche; `Duty.weeks` ist die Vereinigung.

### 7.3 Planer, Bericht, Vertretung, Aufsichten, Klausuren
- **Planer** (`timetable._Occupancy/_evaluate`, timetable.py:199-343): Lehrkraft- und Raumbelegung als Intervalle je
  (globale Woche, Tag); die Klasse wie bisher per Index. Meldungen mit Uhrzeit: „unterrichtet bereits (L12) Mo 16:00–16:45“.
- **Bericht** (`validate_school`, timetable.py:376-494): Konflikte per Überlappung; Springstunden und `core_late` wie
  beim Generator.
- **Vertretung** (`_Engine`, substitution.py:212ff.): Jede Einheit trägt (Beginn, Ende) aus dem Raster ihrer Klasse, und
  `t_busy` wird zu Intervallen. Ein Kandidat ist frei, wenn sich nichts überschneidet. „Springstunde (ohnehin im Haus)“
  gilt nur bei einer Lücke < `long_gap_minutes`; heute gilt SPT um 14:20 und 16:00 als Springstunde mit +20 Punkten.
  „Früher kommen/länger bleiben“ und Wegezeit werden in Minuten gerechnet, Lehrkraft-Abwesenheiten nach Uhrzeit. Rand und
  Verlegung bleiben im Klassenraster (`edge`, `try_shift`).
- **Aufsichten**: Die Pause [Ende(after), Beginn(after+1)) gehört zum Raster des Bereichs. Gesperrt ist, wer sich mit der
  Pause überschneidet. „Im Haus“ ist, wer bis 90 min davor oder danach Unterricht hat; heute reicht irgendeine Stunde am
  Tag (duties.py:95-105). Damit bekommt VES (nur abends) keine Vormittagsaufsicht mehr.
- **Klausuren** (exams.py:76-131): Grenzen und Uhrzeit aus dem Kursraster; Raumkonflikte zwischen Klausuren nach Uhrzeit.
- **Kursräume**: `lesson_release_utc` und `period_end_hhmm` (channels.py:93-115) bekommen den Kurs bzw. das Raster.
  Material der Abendklasse wird dann zur richtigen Zeit freigegeben.

## 8. Anzeige
- **Klassen- und Schülerplan**: Zeilen sind die Stunden des eigenen Rasters („1.“ mit „16:00–16:45“), Pausenlinien aus
  dem Raster. Spalten sind die Unterrichtstage der Klasse. Sa/So erscheinen, wenn dort Unterricht oder Termine liegen,
  und immer nach „Ganze Woche“ (E2). Das gilt auch für den Wochenplan der Klassen-Seite (`features/classes/WeekTab`), der
  heute 12 Zeilen mit 9 gesperrten zeigt.
- **Lehrkraft- und Raumplan**:
  - Zeigen alle Zellen ein Raster, bleibt die Darstellung wie heute.
  - Sonst `layout = "timeline"`: Zeilen sind die Zeitabschnitte der beteiligten Raster, links mit Uhrzeit beschriftet
    („07:55–08:40“). Zellen reichen über mehrere Zeilen und zeigen die Stundennummer ihrer Klasse („M · ABK · 1. Std.“).
  - Liegen mehr als 30 min zwischen zwei Abschnitten, trennt eine schmale Zeile mit der Lücke („13:15–16:00“) Vormittag
    und Abend. SPT steht so mit Früh- und Abendunterricht chronologisch und lückentreu in einer Spalte.
  - Neue Funktion `lib/grid.layoutTimeline`; `layoutTimetable` bleibt für Index-Raster.
- **Tagesplan, Monitor, Vertretung, Druck, iCal**: Einträge tragen `time`, `end_time` und `period_label` (Raster der
  Klasse) und werden nach (Beginn, Klasse) sortiert. `MyDayView` und die Startseite nehmen die Zeit nur aus der Zelle,
  nicht mehr aus `settings.period_times`. Die E-Mail-Zeile nimmt die Zeit nur aus dem Eintrag (notify.py:281-286). iCal
  nimmt DTSTART/DTEND aus dem Klassenraster.
- **Wochenwahl**:
  - Neuer Baustein `components/WeekNav.tsx` in Stundenplan, Aufsichten, Klassen-Wochenplan und Druck: „‹ Woche 12 ·
    KW 45 ›“, „Heute“, Auswahlliste 1 … Y mit Datum und „Ferien“.
  - Er ersetzt das `SegmentedControl` mit N Segmenten (TimetablePage.tsx:333-394, DutiesPage.tsx:191); DESIGN.md §5
    erlaubt dort nur 2–5 Optionen.
  - URL `?woche=L` (1-basiert, laufende Woche), auch für den Druck. Alte Links mit `woche=0` zeigen die aktuelle Woche.
- **Muster-Editor** `components/WeekPatternInput.tsx`:
  - `SegmentedControl` „Jede Woche | Bestimmte Wochen | Rhythmus“. „Bestimmte Wochen“: umbrechende Zahlen-Chips 1 … N
    (Tastatur, `aria-pressed`). „Rhythmus“: „alle [k] Wochen ab Woche [s]“ mit einer Zeile Vorschau „Woche 2, 5, 8 …
    (18 von 52)“.
  - Eingesetzt in `CoursesEditor`, `RuleEditor`, den Lehrkraft-Zeitfenstern (`features/teacher/components.tsx`, heute eine
    Tabelle je Zykluswoche) und `DutiesPage`. Die Vorschau im `RuleEditor` zeigt nur noch die unterschiedlichen
    Wochengruppen statt N Spalten (RuleEditor.tsx:45-88). Die Spalte „Wochen“ im Kurs-Editor sortiert numerisch (U-84).
- **Einstellungsort (A-29, A-32)**:
  - Planung → Reiter „Zeitraster & Schuljahr“ (PlanningPage.tsx:19) mit diesen Abschnitten:
    - „Schuljahr“: Beginn, Ende, Zählung „Schuljahr/Kalenderwoche“, Korrekturen.
    - „Wochenzyklus“: 1 … 53.
    - „Unterrichtstage“: Chips Mo–So statt Zahlenfeld mit max. 6 (SettingsPanels.tsx:521-533).
    - „Wochenübersicht“: Tabelle 1 … Y mit KW, Datum, Ferien, Zykluswoche.
    - „Zeitraster“: Standard und weitere, Editor mit Rechner und Vorschau.
  - Je Klasse, im Stammdaten-Klasseneditor und in den Einstellungen der Klassen-Seite: „Zeitraster“, „Unterrichtstage“,
    „Wochenzyklus“ (Schulvorgabe oder eigener mit N und Startwoche).
- **Gestaltung**: nach DESIGN.md §1/§5/§6. Hilfe nur an der Beschriftung (`Field help=…`), keine Erklärabsätze, nur
  Tokens und vorhandene Icons. Hell und dunkel; 390 px ohne waagerechtes Scrollen der Seite. Stundenplan-Raster
  scrollen innerhalb ihrer Karte, WeekNav bricht um. Bedienung per Tastatur: Pfeile in WeekNav, Chips als Knöpfe.

## 9. Abwärtskompatibilität
- **Lesepfad** (`Model.from_dict` ignoriert Unbekanntes, models.py:23-25): Fehlende Felder bekommen die Standardwerte
  aus §2–§6. Für ein altes Dokument gilt dann:
  - Woche 1 ist die Woche von `cycle_start`, die Zykluswoche bleibt wie bisher (G8).
  - Unterrichtstage = `range(days)`; `Holiday.kind = "ferien"`.
  - Alle Klassen liegen im Standard-Raster. Zeitfenster bleiben unverändert, Lehrkraft-Regeln zählen im Standard-Raster.
  Backups, Versionen (`school_versions`), JSON-Teilimport und Undo bleiben lesbar.
- **A/B-Angaben**: `weeks` [0]/[1] bleiben gespeichert und heißen ab jetzt Woche 1/2. Notiztexte wie „Woche A:
  Berufsschule“ ändert nur die Demo; Texte der Schule bleiben, wie sie sind.
- **Schreibpfad**: `to_dict` schreibt die neuen Felder, `cycle_start` bleibt im Dokument (für ältere Programmstände).
- **Alembic**: R3 braucht keine Revision, weil alles im Planungsdokument liegt. Auch R4 braucht keine Schemaänderung:
  Alle SQL-Stundenangaben zählen heute im Standard-Raster und damit im Raster jeder Klasse.
  - Wechselt eine Klasse das Raster (`POST /classes/{id}/time-grid`), rechnet derselbe Vorgang `student_absences.periods`
    sowie `lesson_period`/`visible_from` der Kursraum-Einträge über die Uhrzeit um.
  - Schüler/innen, die die Klasse wechseln, behalten alte Stundenangaben im alten Raster. Ist das nicht hinnehmbar, legt
    R4 die Revision `00xx_period_grid` an: nullable Spalte `time_grid` in `student_absences`, `channel_items` und
    `channel_folders`. Den Namen beim Start in `docs/AGENT_NOTES.md` reservieren; der Kopf ist heute
    `0013_parent_access`.

## 10. Schnittstellen
- **Untis (GPU)**: Was die Dateien können (untis_gpu.py:11-13/24-26/79-86):
  - Tag 1–6 [s] (der Import nimmt 1–7), Stunde ab 1; keine Uhrzeiten, kein Zeitraster, keine Wochenperiodizität.
  - Mehrwochenplan und Zeitraster werden in Untis selbst eingestellt und nicht über GPU getauscht [u].
  - GPU003 Feld 20/21 „Unterrichtsbeginn/-ende“ [s] ist ungenutzt, die Bedeutung unsicher [u].

  Abbildung:
  - **Export** `export_files(…, periods="timeline")` (Standard): Die Stundennummer ist die Position auf der
    Untis-Zeitachse, also die Standard-Nummerierung. Stunden anderer Raster, die nach der letzten Standard-Stunde
    beginnen, werden angehängt (Abend: 11, 12, …), sodass die Schule wie heute nur ein Untis-Raster pflegt. Stunden mit
    Beginn im Standardbereich, die nicht deckungsgleich sind, gehen auf die Standard-Stunde mit gleichem oder früherem
    Beginn; dazu die Warnung „nicht deckungsgleich“. `periods="class"` exportiert die Klassenstunde (für Untis mit Raster
    je Klasse [u]).
  - **Wochen**: Text „(Woche 1)“; Meta `sm1` `cw/lw/cy` unverändert, neu `g=<Raster>`. Sa = 6, So = 7 [u], mit
    Warnung.
  - **Import**: Die Stundennummer wird über die Zeitachse zur Uhrzeit, dann zur Stunde des Klassenrasters mit gleichem
    Beginn; ohne Treffer gibt es eine Warnung, und der Block bleibt unverplant. `_WEEK_RE` liest „Woche 1…53“, Listen,
    „Woche A–Z“ und „A-Woche“. `check_cycle` nimmt Zyklen bis 53 (untis_gpu.py:1062-1069). GPU014 findet den Block über die
    Zykluswoche des Kurses. Abendklassen werden nicht mehr ins Standard-Raster gezogen; `_extend_period_times` dient nur
    noch der Untis-Zeitachse.
- **CSV** (csv_io.py):
  - lessons: „Wochen“ als `1,3` bzw. `1-4,9` (der Import nimmt auch Buchstaben), „Tag“ Mo–So bzw. 1–7, „Stunde“ im
    Klassenraster. Neu „Beginn“ und „Ende“ (nur Export).
  - classes: neu „Zeitraster“, „Unterrichtstage“ (`Mo-Fr`, `Mo,Di,Sa`), „Wochenzyklus“ (leer = Schulvorgabe) und
    „Zyklusbeginn (Woche)“.
  - Sperrzeiten „Woche 1,3: Mi Std. 6-8 (Notiz)“, für Lehrkräfte zusätzlich „Mi 14:00-16:00“; Wochen mehrstellig.
    Import-Hilfe in `lib/csvFields.ts:68`.
- **JSON**: Planungsdokument mit den neuen Feldern und der Sammlung `time_grids`; API-Antworten laut §11.2. Der Webhook
  `substitutions.changed` (notify.py:210-228) bekommt die neuen Felder dazu, Schema v1 bleibt. `week_label` enthält
  Ziffern; das steht in der Webhook-Doku (02).
- **iCal** (ical.py): Zeiten aus dem Klassenraster. DESCRIPTION enthält „Zykluswoche 2 von 2“ statt „, Woche A“
  (ical.py:446-448), und zwar nur bei N > 1. Termine an Sa/So erscheinen; UIDs bleiben (Datum + Block).
- **Schulmanager-Online-ZIP** (schulmanager_online.py:55-62/100-106/197): LIESMICH „Wochenzyklus: N Wochen (Woche 1 …
  N)“, ohne „(Woche A)/(Woche B)“. `manifest.json` zusätzlich mit `week_numbering`, `school_year_start`, `school_days`
  und `time_grids` (IDs, Namen).

## 11. Arbeitspakete
### 11.1 Runden und Pakete
Runde 3 (Wochen, Zyklus, 7 Tage: A-67, A-68, A-28, A-29, Teile von A-32/A-51) beginnt erst nach der Integration von R2
(`substitution.py`, `features_substitutions.py`, `features_common.py`). Runde 4 (Zeitraster je Klasse und
Uhrzeit-Konflikte: A-69, A-31, A-30) baut auf R3 auf. In jeder Runde laufen ein Backend- und ein Oberflächenpaket
parallel, ohne gemeinsame Dateien außer `api/types.ts`. Das Backend liefert den Vertrag §11.2. Die Oberfläche arbeitet
mit Testdaten aus den Typen und macht den Browser-Rundgang nach dem Einspielen des Backends. „Ausnahme“ heißt: kleine
Edits in einer fremden Zone, vorher in `docs/AGENT_NOTES.md` angekündigt.

| Paket | Größe | Dateien | Reihenfolge, Hinweise |
|---|---|---|---|
| **R3-A1** Backend und Schnittstellen | L, Spur A | `schulmanager/models.py` (Settings, SchoolClass, Holiday, WEEKDAYS, `week_of`/`week_label`), `calendar_utils.py`, **neu** `weeks.py`, `scheduler.py` (Varianten, Phasenregel, D = 7, Klassentage), `timetable.py`, `planning.py` (U-52 anteilig), `duties.py`, `exams.py`, `teacher_profile.py`, `substitution.py`, `demo.py`; `integrations/_common.py`, `csv_io.py`, `untis_gpu.py`, `ical.py`, `schulmanager_online.py`; `server/routes/features_data.py`, `features_timetable.py`, `features_teacher_profile.py`, `features_substitutions.py`, `features_exchange.py`, **neu** `features_calendar.py`, `server/jobs.py`; Ausnahmen `channels.py` und `features_classes.py` (KZ-6), `features_common.py` (`range_plans`/`week_history`), `server/notify.py` (KZ-7, Texte); **neu** `tests/test_weeks.py` und die betroffenen Tests; Doku `docs/code/01`, `03`, `04`, `09` | (1) `weeks.py` und `calendar_utils` mit Tests, (2) Felder und Prüfung, (3) Engine, Bericht, Ansichten, (4) Generator, Aufsichten, (5) Schnittstellen, (6) Demo. `week_label` bleibt übergangsweise als Ziffer |
| **R3-A2** Oberfläche | M, Spur A/D | **neu** `lib/weeks.ts`, `components/WeekNav.tsx`, `components/WeekPatternInput.tsx`; `api/types.ts`, `api/endpoints.ts` (geteilt); `lib/dates.ts` (`cycleWeekOf`/`weekLabel` entfallen, `isoWeekNumber` kommt aus `features/classes/logic.ts:44ff.`), `lib/rules.ts`, `lib/grid.ts`; `components/DateNav.tsx`, `TimetableGrid.tsx` (Wochen-Tags), `RuleEditor.tsx`; `pages/TimetablePage.tsx`, `PrintTimetablePage.tsx`, `DutiesPage.tsx`, `ExamsPage.tsx`, `MasterDataPage.tsx` (Ferienart, Klassentage, Klassenzyklus), `planning/SettingsPanels.tsx` (Schuljahr, Zyklus, Unterrichtstage, Wochenübersicht), `planning/CoursesEditor.tsx`; `features/classes/WeekTab.tsx`, `logic.ts`, `types.ts`; `features/teacher/windows.ts`, `components.tsx`, `TeacherFields.tsx`, `TeacherRequestsPage.tsx`, `TeacherProfilePage.tsx`; `features/channels/VisibilityPicker.tsx`; vitest; Doku `05`–`08` | Nicht enthalten: `DashboardPage`, `MonitorPage`, `SubstitutionsPage`, `PrintSubstitutionsPage` (R3-D bzw. KZ-2). Sie zeigen über `week_label` schon Ziffern; R3-D stellt sie mit `lib/weeks.ts` auf `week_info.week_text` um |
| **R4-A1** Backend und Schnittstellen | L, Spur A | **neu** `schulmanager/timegrid.py`; `models.py` (TimeGrid, `time_grid`-Felder, `start`/`end` an TimeRule und Absence, `site_travel_minutes`, `long_gap_minutes`), `calendar_utils.py`, `scheduler.py` (Atome, Doppelstunden), `timetable.py` (Intervalle, `layout`/`rows`), `substitution.py`, `duties.py`, `exams.py`, `planning.py` (`_class_slots`, Kapazität nach Zeit), `teacher_profile.py` (Uhrzeit-Regeln), `demo.py`; `integrations/_common.py` (`period_bounds` mit Raster), `untis_gpu.py`, `csv_io.py`, `ical.py`; `features_data.py` (CRUD `time_grids`, Vorschau, Kopplungsprüfung), `features_timetable.py`, `features_exams.py`, `features_teacher_profile.py`, `features_substitutions.py`; Ausnahmen KZ-6 `channels.py`, `features_classes.py` (Wochenplan im Klassenraster, `POST /classes/{id}/time-grid`), `features_student_absences.py`, `features_student_self.py`, dazu `server/notify.py`; Tests; Doku `01`, `03`, `04`, `09` | (1) `timegrid.py` mit Prüfung und Rechner, (2) Zeitachse und Intervall-Belegung, (3) Generator, (4) Vertretung, Aufsichten, Klausuren, Kursräume, (5) Rasterwechsel und Schnittstellen, (6) Demo-ABK |
| **R4-A2** Oberfläche | L, Spur A/D | **neu** `components/TimeGridEditor.tsx`; `lib/grid.ts` (`layoutTimeline`), `components/TimetableGrid.tsx`, `MyDayView.tsx`; `pages/TimetablePage.tsx`, `MasterDataPage.tsx` (Raster je Klasse, Lehrkraft-Sperren in Uhrzeit über `RuleEditor`), `ExamsPage.tsx`, `DutiesPage.tsx` (Pausen je Raster), `StudentAbsencesPage.tsx`; `features/classes/WeekTab.tsx`, `features/students/components.tsx`, `features/teacher/*` (Verfügbarkeit als Zeitachse); nach R2 `SubstitutionsPage.tsx`, `components/EntryTable.tsx` (Ende, Zeit, Stundenwahl im Klassenraster); `api/types.ts`; vitest; Doku `05`–`08` | `TimetableGrid`, `MyDayView` und `SettingsPanels` gehören zu KZ-9 (Spur D). R4-D (B-11) arbeitet in `SettingsPanels` nur im Reiter „Prioritäten & Regeln“; beide kündigen ihre Edits an |

Danach (R5): B-42-Bausteine (Muster-Editor für Monats- und Jahresregeln, A-50), Termine an Sa/So im Schulkalender
(B-26), Abgleich mit einer echten Untis-Version [u].

### 11.2 Vertrag (fest für R3-A1/A2 und R4-A1/A2)
```ts
// R3 – api/types.ts
export interface WeekInfo {
  week_no: number | null;   // laufende Woche L (1…Y), null außerhalb des Schuljahres
  iso_week: number; iso_year: number;
  week_start: string;       // Montag, ISO-Datum
  cycle_week: number;       // 1-basiert (k)
  cycle_length: number;     // N des Bezugs (Schule bzw. Klasse)
  week_text: string;        // „Woche 12 · KW 45 · Zykluswoche 3 von 6“
  holiday_week: boolean; in_school_year: boolean;
}
export type DayKind = 'unterricht' | 'kein_unterrichtstag' | 'ferien' | 'feiertag';
// Settings += week_numbering: 'school_year'|'iso'; school_year_start: string; school_year_end: string;
//             week_anchors: {date: string; week: number; note?: string}[]; school_days: number[]  (cycle_weeks 1…53)
// SchoolClass += cycle_weeks: number (0 = Schule); cycle_start_week: number; school_days: number[]
// Holiday += kind: 'ferien'|'feiertag'|'beweglich'|'sonstiges'
// TimetableView += week_info: WeekInfo; day_info: {index:number; name:string; date:string; teaching:boolean;
//                  day_kind: DayKind; holiday:string|null}[];  days = sichtbare Spalten (Std.) bzw. 7 mit ?all_days=1
// Cell += weeks_text: string   (weeks = Kurszyklus, 0-basiert; Antwort enthält nur in der Woche aktive Zellen)
// DayPlan/ClassWeek/MyWeek += week_info: WeekInfo; days[]/DayPlan += day_kind; week_label = String(k) | ''
// Lehrkraft-Profiloptionen: week_labels = ['1','2',…], + school_days
```
- **Endpunkte R3**:
  - `GET /calendar/school-year` → `{start, end, numbering, weeks_in_year, open_days, weeks: [{week_no, iso_week,
    week_start, week_end, cycle_week, holiday_week, holidays: string[]}]}`. Lesbar für alle Angemeldeten.
  - `POST /settings/calendar-preview {cycle_weeks?, week_numbering?, school_year_start?, week_anchors?}` → `{exact,
    changes: [{kind, id, label, before, after}], today_before: WeekInfo, today_after: WeekInfo}`. Recht `settings.edit`.
  - `GET /timetable/{kind}/{ref}?week_no=L|date=…|week=<alt, 0-basiert>&all_days=0|1`. `week` wird als L = week + 1
    gelesen.
  - `PUT /settings` und `PUT /data/classes/{id}` antworten mit 409 `cycle_change`, wenn `force_cycle_change` fehlt.
```ts
// R4 – api/types.ts
export interface TimeGrid { id: string; name: string; builtin?: boolean; core_latest: number | null;
  periods: { start: string; end: string }[];
  breaks: { after: number; name: string; minutes: number; splits_double: boolean }[]; }
// SchoolClass += time_grid: string ('' = standard); SupervisionArea += time_grid: string
// TimeRule += start: string; end: string ('' = periods gilt); Absence += start: string; end: string
// Settings += site_travel_minutes: number; long_gap_minutes: number
// TimetableView += layout: 'periods'|'timeline'; grid: {id,name}|null;
//   rows: {key:string; begin:string; end:string; label:string; period_label:string|null; gap_before:number}[]
// Cell += begin: string; end: string; row: number; row_span: number; period_label: string; grid: string
// Entry (DayPlan) += end_time: string; grid: string;  ClassWeek += grid, period_ends: string[], breaks
```
- **Endpunkte R4**: `GET /time-grids` (mit Standard und `builtin`), CRUD `/data/time_grids`, `POST /time-grids/preview`,
  `POST /classes/{id}/time-grid {grid, dry_run}` → `{moved, unmapped, replan_needed}` (Recht `timetable.edit`, Audit).

## 12. Abnahmekriterien und Testplan
**R3-A1**
1. `running_week`/`cycle_week` (Unit, `test_weeks.py`): 01.08.2026 ergibt Woche 1 ab 27.07.; 2027/28 hat 53 Wochen;
   der Anker „ab 11.01.2027 Woche 20“ wirkt; im KW-Modus haben 28.12.2026 und 04.01.2027 bei N = 2 beide Zykluswoche 1.
2. Altdokument mit `cycle_weeks = 2` und `cycle_start`, ohne neue Felder: `week_of` ist für −400…800 Tage identisch zu
   vorher. Untis- und CSV-Rundlauf ohne Verlust (Unit + `test_integrations.py`).
3. Kein Buchstabe als Woche: `grep` nach `chr(ord("A")` und `chr(65` in `schulmanager/` ist leer. Die Antworten von
   `/timetable`, `/substitutions`, `/classes/{id}/week`, `/me/week`, `/planning/report` und `/teacher-profile/options`
   enthalten kein A–Z als Woche (API-Test über alle Endpunkte mit N = 2 und N = 30).
4. N = 30 und N = 53 lassen sich speichern. CSV „Woche 10,27: Mi“ übersteht den Rundlauf, Untis-Text „(Woche 27)“ wird
   erkannt (heute `ValueError` bzw. nicht erkannt).
5. Ein Zykluswechsel 2 → 4 rechnet exakt um: Rhythmusregel, Kurs, Stunde und Aufsicht greifen in denselben
   Kalenderwochen. 2 → 3 gibt 409 mit Liste und mit `force` genau die angezeigte Wirkung (API, behebt U-13).
6. Ferienwochen: Die Herbstferien 2026 zählen mit (Woche 8/9 bei Beginn 31.08.), `holiday_week = true`, die Zykluswoche
   läuft durch (Unit mit den Demo-Ferien).
7. Eine Klasse mit `school_days = [5]` (Sa) bekommt vom Generator nur Samstagsstunden. Der Vertretungsplan am Samstag ist
   für sie berechnet, der Sonntag ist leer mit `day_kind = kein_unterrichtstag` (Solver + Engine).
8. Zyklus je Klasse: X mit N = 2, Y mit N = 3, dieselbe Lehrkraft → H = 6 und keine Doppelbelegung in den Wochen 1…12.
   Eine gekoppelte Kursstunde X+Y mit `weeks = [0]` gibt 422 (Solver + API).
9. Einheitliche Aktiv-Logik: `Lesson.weeks = []` mit `Course.weeks = [0]` ist in Ansicht, Engine, Kursraum, iCal und
   Klassen-Seite nur in Woche 1 aktiv (ein Test über fünf Aufrufer).
10. Generator an der kleinen Demo mit N = 1/2/3/6/52 (Solver; nur N = 52 als `@pytest.mark.slow`): N = 52 mit auf 52
    Wochen wiederholten Regeln der Wochen 1/2 ergibt V = 2 und mit gleichem Seed dasselbe Ergebnis wie N = 2. N = 52 mit
    Regeln nur in Woche 1/2 ergibt V = 3 (3·7·P Slots je Lehrkraft). Aufsichten bei N = 52 ≤ 3 × der Zahl bei N = 1.
11. U-52: Ein manueller Kurs mit `weeks = [0]` bei N = 2 zieht von der Stundentafel die Hälfte ab.

**R3-A2**
1. `lib/weeks.ts`: `describeWeeks` und `expandPattern` liefern dieselben Fälle wie `weeks.py` (gemeinsame Tabelle).
2. Stundenplan: WeekNav 1…Y, `?woche=L`, „Heute“ und Ferien-Badge; der Druck übernimmt die Woche (vitest + Browser).
3. Muster-Editor: alle drei Modi mit Ergebnis `weeks` und Vorschau; N = 52 auf 390 px ohne waagerechtes Scrollen.
4. Einstellungen: Schuljahr, Zählung, Zyklus 1…53, Unterrichtstage Mo–So, Wochenübersicht, Grenzen wie im Backend (U-49,
   U-84). Vorschau vor dem Speichern; ein 409 erscheint als Liste mit „Trotzdem übernehmen“.
5. Unterrichtstage und eigener Zyklus lassen sich im Stammdaten-Editor und auf der Klassen-Seite einstellen. WeekTab zeigt
   Sa, wenn die Klasse dort Unterricht hat.
6. `grep "fromCharCode(65"` in `frontend/src` ist leer, außer in Altformat-Tests.
7. Browser-Rundgang 1280/820/390 px, hell/dunkel, Tastatur: Stundenplan, Aufsichten, Kurs-Editor, Regel-Editor,
   Lehrkraft-Zeitfenster, Einstellungen, Klassen-Wochenplan.

**R4-A1**
1. Zeitraster-Prüfung (Unit, B-16 Punkt 5): Überlappung, zu lange Pausen und Pausen nach der letzten Stunde werden
   abgewiesen, auch im Standard (U-16/U-82). Rechner mit 07:50/45 min und Pausen 15 + 20, mit 08:00/60 min und mit freien
   Längen.
2. Demo-ABK im Raster „Abend“: Der Klassenplan beginnt mit „1.“ um 16:00, hat 6 Zeilen und keine Sperrzeile; Standard hat
   10 Stunden (API).
3. SPT früh + ABK: Der Lehrkraft-Plan hat `layout = timeline` mit chronologischen Zellen, die ABK-Zelle trägt
   `period_label` „1.“ und 16:00. `teacher_gaps` zählt die Lücke Vormittag–Abend nicht (Bericht).
4. Konflikt nur bei Überlappung: 5a „10.“ (16:00–16:45) und ABK „1.“ (16:00–16:45) mit derselben Lehrkraft geben einen
   Konflikt, 5a „1.“ und ABK „1.“ keinen (Solver, `check_move`, Bericht).
5. Keine Doppelstunde liegt über einer Pause mit `splits_double`; in der Demo 0 (heute 22 von 70) (Solver).
6. Vertretung (Engine): VES (nur abends) ist um 08:45 nicht „im Haus“. SPT gilt um 14:20 nicht als „Springstunde“. Eine
   Lehrkraft-Abwesenheit 16:00–18:00 trifft nur die Abendstunden.
7. Aufsichten: VES ohne Zeitfenster bekommt keine Vormittagsaufsicht (Aufsichtsplaner).
8. Rasterwechsel einer Klasse mit `dry_run`: Stunden, Klausuren, Overrides, Krankmeldungen und Kursraum-Freigaben werden
   über die Uhrzeit umgerechnet oder als `unmapped` gemeldet; der Vorgang wird auditiert (API mit DB).
9. Kopplung über verschiedene Raster gibt 422; die Uhrzeit-Sperre einer Lehrkraft gilt in beiden Rastern (API + Solver).
10. Rundläufe (Integration): Untis mit Abendraster exportiert als Zeitachse (ABK 10–15), der Import stellt die
    ABK-Stunden im Raster „Abend“ wieder her; CSV mit „Zeitraster“ und „Unterrichtstage“; iCal zeigt ABK 16:00–16:45.
11. Altdokument ohne `time_grids`: Generator (gleicher Seed), Bericht und Vertretung liefern dasselbe wie in R3
    (Regressionstest mit gespeichertem Dokument).

**R4-A2**
1. `layoutTimeline`: Zeilen, Zellen über mehrere Zeilen, Lückenzeile ab 30 min (vitest).
2. Zeitraster-Editor: Rechner, Vorschau, Fehler aus dem Backend am Feld, Zuordnung je Klasse.
3. Die Stundenwahl bei Krankmeldungen, Abwesenheiten und Klausuren folgt dem Raster der Klasse (ABK: 6 Knöpfe statt 12).
4. Lehrkraft-Sperren und Zeitfenster erscheinen als Zeitachse. Einträge in Vertretung und Monitor zeigen das Ende und sind
   chronologisch sortiert.
5. Browser-Rundgang 1280/820/390 px, hell/dunkel: Klassenplan ABK, Lehrkraftplan SPT, Raumplan, Einstellungen, Vertretung.

**Testplan gesamt**
- Unit: `test_weeks.py`, `test_timegrid.py`. API: `test_server_features.py`, `test_classes.py`, `test_teacher_profile.py`.
- Solver: N = 1/2/3/6/52, Abendklasse mit Lehrkraft früh und abends, Zyklus je Klasse.
- Rundlauf alter Dokumente: festes JSON der heutigen kleinen Demo als Fixture; dazu Untis- und CSV-Rundlauf.
- Frontend: vitest; Browser (Chromium unter `/opt/pw-browsers`, eigener Port 89xx) mit 1280/820/390 px, hell und dunkel.
- Die komplette Suite läuft einmal am Ende jedes Pakets.

## 13. Offene Entscheidungen für den Auftraggeber
- **E1 Wann ist Woche 1?** Empfehlung: **Beginn des Schuljahres laut Schulrecht (z. B. 1. August)**. Damit liegen alle
  52 Wochen samt Sommerferien im Schuljahr. Die Schule kann das Datum ändern, z. B. auf den ersten Schultag; dann liegen
  die Sommerferien am Ende des Vorjahres.
- **E2 Sa/So im Wochenplan**: Empfehlung: **Mo–Fr fest; Sa/So erscheinen automatisch, sobald dort Unterricht oder
  Termine liegen, und immer mit dem Schalter „Ganze Woche“**. In Daten, Navigation und Kalender hat die Woche immer
  7 Tage.
- **E3 Abweichendes Zeitraster je Wochentag** (z. B. Freitag andere Zeiten)? Empfehlung: **Nein, ein Raster je Klasse**.
  Kürzere Tage ergeben sich aus weniger Stunden bzw. Unterrichtstagen. Das Feld lässt sich später ohne Bruch nachrüsten.

## 14. Prüfvermerk 1 (11.10., adversariale Prüfung am Code)

Vorrang vor §1–§13. Nachgerechnet mit Skripten im Prüfer-Scratchpad (`…/scratchpad/zyklus/p_*.py` und `.out`, flüchtig).
Die maßgeblichen Zahlen stehen deshalb hier. Ergebnis: Das Modell ist tragfähig. Tragfähig sind die laufende Woche
1 … Y, die Zykluswoche, die Zeitachse aus Zeitatomen, die Wochenvarianten und die Aktiv-Logik an einer Stelle. Vor dem
Start von R3 müssen W1–W5, Z1–Z4, R1–R2 und P1–P4 in die Pakete übernommen sein.

### 14.1 Wochen und Zyklus (ersetzt Teile von §2.1, §2.2, §3)
- **W1 Eine Korrektur ändert nie die laufende Woche.**
  - Befund: Der Anker „ab 11.01.2027 Woche 20“ ergibt bei Beginn 01.08.2026 (natürlich Woche 25) die Wochen 20–24
    doppelt; 48–52 fehlen, höchste Woche 47. `?woche=L`, WeekNav und „Woche 1 … 52“ (A-68) sind dann mehrdeutig.
    Bei Beginn 31.08.2026 ist derselbe Anker wirkungslos, weil die Woche ohnehin 20 ist. Abnahmetest R3-A1 Nr. 1
    prüft damit nichts.
  - Festlegung: `week_anchors` entfällt. Neu sind `school_year_history: list[str]` (Beginn früherer Schuljahre, ISO) und
    `cycle_shifts: list[{"date", "cycle_week": 1…N, "note"}]`. Ein Shift heißt „ab der Woche dieses Datums gilt
    Zykluswoche k“. Er verschiebt nur die Phase, gilt bis zum Ende seines Schuljahres und ist in beiden Zählmodi
    erlaubt. L bleibt immer die echte laufende Woche.
- **W2 Zyklusbeginn der Schule** `Settings.cycle_start_week: int = 1` (s in §1).
  - Befund: Im Altdokument gilt N = 2 und `cycle_start` 31.08.2026. Wird `school_year_start` auf den 01.08.2026 gesetzt
    (Empfehlung E1), wechselt in **52 von 52** Wochen die Zykluswoche (A↔B). Außerdem begänne Zykluswoche 1 in den
    Sommerferien, und ihre Lage zur ersten Schulwoche wechselte jedes Jahr.
  - Festlegung: Bei einer Änderung von `school_year_start` hält `PUT /settings` standardmäßig die Phase. Dazu setzt es s
    so, dass die Zykluswoche von heute gleich bleibt (`keep_cycle_phase: false` schaltet das ab). Das Beispiel ergibt
    s = 6. Die `calendar-preview` zeigt beide Varianten. Formel: k = (L − s_eff) mod N + 1, s_eff = s bzw. der letzte
    Shift des Schuljahres.
- **W3 Schuljahr in ganzen Wochen.**
  - Befund: Woche 1 beginnt am Montag vor dem Beginndatum (01.08.2026 → 27.07.). Das Standardende „Beginn + 1 Jahr −
    1 Tag“ fällt dann in Woche Y + 1. Das gilt auch bei Beginn an einem Montag: Ende 30.08.2027 hat L = 53 bei Y = 52.
    `week_no = null` „außerhalb des Schuljahres“ widerspricht damit dem Datum.
  - Festlegung: Das Schuljahr endet am Sonntag vor der Woche des nächsten Beginns. Der nächste Beginn ist der nächste
    Eintrag bzw. „Beginn + 1 Jahr“. `school_year_end` ist nur ein abgeleiteter Wert in Antworten und keine Eingabe.
    `in_school_year` richtet sich nach der Woche, nicht nach dem Tag.
  - Ist `school_year_start` gesetzt, beginnt nach Y Wochen automatisch das nächste Schuljahr mit Woche 1 (A-68 jedes
    Jahr ohne Zutun). Ohne `school_year_start` (Altdokument) zählt L weiter, damit G8 gilt. Die Einstellungen warnen
    dann „Schuljahr abgelaufen“.
- **W4 Kein Phantom-Schuljahr.** Der alte Beginn kommt nur in `school_year_history`, wenn der neue mindestens 300 Tage
  später liegt. Sonst ist es eine Korrektur. Nachgerechnet: Die Korrektur 24.08. → 31.08.2026 legte laut §2.2 ein
  Schuljahr von einer Woche an (25.08. und 01.09. beide „Woche 1“).
- **W5 Planungshorizont = Wochen des Schuljahres** statt kgV ≤ 53 (§3).
  - Befund: Die kgV-Grenze verbietet Schule N = 52 mit Klasse N = 3 (kgV 156), obwohl A-29 und A-67 beides verlangen.
  - Festlegung: Jede reale Woche 1 … Y bekommt ihre Signatur aus der Phase jedes Zyklus (aus L, s, Shifts). Der
    KW-Sprung 53 → 1 ist darin enthalten. Gleiche Signaturen bilden die Varianten wie in §7.2, und die 422 für das kgV
    entfällt. `validate_school` prüft über die Wochen 1 … Y. Die Phasenregel (§7.2) bleibt.
- **W6 KW-Modus: KW ist im Schuljahr nicht eindeutig.** Im Schuljahr 2027/28 (53 Wochen ab 26.07.2027) kommt KW 30
  zweimal vor (26.07.2027 und 24.07.2028). Kanonisch in URLs ist daher `?datum=JJJJ-MM-TT` (Montag der Woche, wie in der
  Vertretung). `?woche=L` heißt in beiden Modi „laufende Woche des aktuellen Schuljahres“. Alte Links `?woche=1` (bisher
  B) zeigen danach Woche 1. Das wird hingenommen und in 06 dokumentiert.
- **W7 Schuljahreswechsel.** Bei einem Jahr mit 53 Wochen und N = 2 haben Woche 53 und die neue Woche 1 beide
  Zykluswoche 1 (2028-07-24 / 2028-07-31). Bei N = 3 springt die Phase von 2 auf 1. Der Bruch liegt immer in der Woche
  vor dem neuen Beginn, mit E1 in den Sommerferien. Die Wochenübersicht zeigt ihn als Warnung.
- **W8** Ein `cycle_start` an einem anderen Tag als Montag ist nur über `from_dict` bzw. Import möglich. Hier rechnet
  die neue Formel (`monday_of`) an **343 von 1200** Tagen anders als `week_of` (Wochenwechsel bisher mitten in der
  Woche). Das ist gewollt; Test und Hinweis in 01.
- **W9 Zykluswechsel mit Zeitfenstern (U-13).**
  - Befund: Eine Woche ohne Fenster bedeutet „nicht verfügbar“. Große Demo, 2 → 3 ohne Umrechnung: ZEH (Fenster nur
    Woche 1/2) ist in Woche 3 Mo–Do gesperrt, **15 Blöcke** bleiben je Zusatzwoche unverplant (bei 2 → 6 sind es 60).
  - Festlegung: `weeks.convert` meldet für Zeitfenster jede Zykluswoche, die ohne Fenster bleibt, als Änderung „Woche k:
    nicht verfügbar“ im 409. `duty_load` (duties.py:149-160) gewichtet mit der Vielfachheit der Varianten.

### 14.2 Zeitraster und Uhrzeit (ersetzt Teile von §6, §7, §10)
- **Z1 `max_periods_per_day` bleibt „späteste Stunde im Klassenraster“** (Indexgrenze, scheduler.py:115,
  timetable.py:271), nicht Anzahl.
  - Befund: Standard hat 10 Stunden, Klassen haben `max_periods_per_day = 8`. Heute sind die 9. und 10. Stunde
    gesperrt; als Anzahl würden sie frei. Der Generator plant dann anders, was R4-A1 Nr. 11 widerspricht.
  - Mit eigenem Raster entfällt das Problem der ABK ohnehin. Die Oberfläche beschriftet das Feld „Unterricht bis
    Stunde“. Eine echte Anzahl kommt erst bei Bedarf als neues Feld.
- **Z2 `long_gap_minutes: int = 0`** (0 = aus, wie heute).
  - Befund: „Lücken ≥ 120 min zählen nicht“ ist nicht monoton. Eine Lücke von 340 min kostet nichts, eine von 100 min
    voll, und im Standard ändert sich das Ergebnis.
  - Festlegung: Bei Wert > 0 zählt eine Lücke höchstens mit `long_gap_minutes` (Deckel). In der Vertretung gilt
    „ohnehin im Haus“ nur bei einer Lücke unter diesem Wert. Die Demo setzt 120.
- **Z3 Doppelstunden: ein Mechanismus.**
  - `breaks[].splits_double` (Standard `true`) gilt für das Standard-Raster (`Settings.breaks`) und für jedes
    `TimeGrid`. `BreakIn` (features_data.py:735-739, `extra=forbid`) bekommt das Feld.
  - B-02 Kriterium 1 (`Settings.doubles_across_breaks`) und B-16 Kriterium 1 („trennt Doppelstunden“) werden darauf
    umgestellt, es gibt keinen zweiten Schalter.
- **Z4 Kopplung über verschiedene Raster** (Entscheidung E4, §14.7).
  - Empfehlung: zulassen, wenn jede Stunde des Blocks in allen beteiligten Rastern deckungsgleich ist (gleicher Beginn
    und gleiches Ende). Der Generator wählt dann nur solche Starts, sonst 422.
  - In jedem Fall gilt: Ändert sich das Raster, der Zyklus oder die Unterrichtstage einer Klasse in einem gekoppelten
    Kurs, antworten `PUT /data/classes/{id}`, `PATCH /classes/{id}` und `POST /classes/{id}/time-grid` mit 409 und der
    Kursliste.
- **Z5 Indizes bleiben Klassenraster-Indizes.**
  - In Zellen und Einträgen bleiben `period`/`start` der Index im Raster der Klasse; die Zeitachse kommt nur über
    `row`/`begin`/`end`. `server/absence_access.py:92-124` (`lesson_periods`, Datei aus R2) vergleicht `cell.period`
    mit `student_absences.periods` und bleibt nur so richtig.
  - Verschieben im Zeitachsen-Layout: `move_options` liefert `{day, start, row}`, wobei `start` im Raster des Kurses
    liegt. Ziele sind nur Zeilen, die eine Stunde dieses Rasters beginnen.
  - `blocked` bekommt `begin`/`end`.
- **Z6 Untis.**
  - (a) Die Abbildung „gleicher oder früherer Beginn“ kann zwei Stunden eines Rasters auf dieselbe Untis-Stunde legen.
    Nachgerechnet: 60-Minuten-Raster neben 45 min ergibt `[1, 2, 3, 4, 6, 6]`. Deshalb ist die Abbildung je Raster
    streng steigend (mindestens Vorgänger + 1), mit Warnung.
  - (b) GPU014 schreibt heute `hour = period + 1` bzw. `+ 2` für Aufsichten (untis_gpu.py:455-456). Das läuft künftig
    über dieselbe Zeitachse.
  - (c) Der Import setzt `st.days` (untis_gpu.py:1035-1039) und ab R3 `school_days`.
  - (d) GPU003 Feld 20/21 „Unterrichtsbeginn/-ende“ ist ein Kandidat für die erste/letzte Untis-Stunde der Klasse
    (Abendklasse 10/15) [u], vor Nutzung prüfen.
- **Z7** iCal-UIDs enthalten die Startstunde (ical.py:454, `run[0]`). Wechselt eine Klasse das Raster, ändern sich
  ihre UIDs einmalig (Kalender-Apps löschen und legen neu an). „UIDs bleiben“ (§10) gilt nur ohne Rasterwechsel.
- **Z8** Deputat und Stundentafel zählen je Stunde, unabhängig von der Länge (wie heute). Eine Umrechnung nach Minuten
  ist Entscheidung E5.
- **Z9 Lehrkraft früh und abends** (08:00 „Vormittag“, 16:30 „Abend“, dazu ein 60-Minuten-Raster) nach §7 nachgerechnet:
  - 26 Atome je Tag. 08:00 und 16:30 überlappen nicht, also kein Konflikt.
  - Partielle Überlappung 45/60 wird erkannt (08:50–09:35 gegen 08:00–09:00).
  - Eine Doppelstunde über die Pause belegt die Pausenatome mit.
  - Anzeige (§8 Zeitachse), Vertretung (§7.3 Intervalle, Z2) und Aufsicht (90 min, Raster des Bereichs) decken den
    Fall ab.
- **Z10** Leere Regel (U-15): Das ausdrückliche „ganze Woche“ aus B-02 Kriterium 4 wird als `days = [0…6]`
  gespeichert und nicht abgewiesen.
- **Z11 Downgrade.** Ein R4-Dokument mit eigenem Raster ist für ältere Programmstände nicht verlustfrei lesbar (ABK
  `start = 0` hieße dort 07:55). Das steht in BETRIEB.md (Rückspielen nur per Backup).

### 14.3 Rechte und Datenschutz
- **R1 Planungsfelder der Klasse nur mit `timetable.edit`.**
  - Betroffen sind `SchoolClass.time_grid`, `cycle_weeks`, `cycle_start_week` und `school_days`.
  - `classes` ist heute mit `masterdata.edit` beschreibbar (features_data.py:33-38, `PATCH /classes/{id}`
    features_classes.py:366-367). Das Sekretariat hat `masterdata.edit` ohne `timetable.edit` (permissions.py:76-79)
    und könnte sonst Stunden umrechnen lassen.
  - Eine Änderung dieser Felder ohne `timetable.edit` gibt 403; Test mit Rolle `sekretariat`.
- **R2 `time_grids`:** `WRITE_PERM = "settings.edit"`, `SCOPES = ["settings", "timetable", "classes"]`. `GET /time-grids`
  und `GET /calendar/school-year` sind für alle Angemeldeten lesbar; sie enthalten keine Personendaten.
- **R3 Rasterwechsel und Krankmeldungen.** `POST /classes/{id}/time-grid` rechnet `student_absences.periods`
  (Gesundheitsdaten) um. `dry_run` und Audit nennen dafür nur Anzahlen, keine Namen, Daten oder Gründe. `admin` hat
  bewusst kein `student_absence.read` (permissions.py:64-65).
- Webhook, Monitor und iCal bekommen keine neuen Personendaten. Rechte und Scopes der bestehenden Endpunkte bleiben.

### 14.4 Fehlende Stellen (in keiner Bestandsaufnahme bzw. keinem Paket)
| Stelle | Was | Paket |
|---|---|---|
| `schulmanager/student_self.py:54-66` | Attest zählt `school_days` ohne Klasse | R3-A1, Ausnahme KZ-6 |
| `server/routes/features_student_absences.py:344` | 422 „kein Schultag (Wochenende oder Ferien)“ ohne Klassentage | R3-A1, Ausnahme KZ-6 |
| `server/routes/features_channels.py:627, 1044, 1297, 2523` | `is_school_day` ohne Klasse; Docstring „A/B-Woche“ | R3-A1, Ausnahme KZ-6 (in R4 nicht anfassen, B-08) |
| `server/absence_access.py:92-124` | Stundenvergleich über `cell.period` | Vertrag Z5 |
| `server/routes/features_data.py:99, 227, 735-739` | Regel-/Aufsichtstag `< st.days`; `BreakIn` ohne `splits_double` | R3-A1 / R4-A1 |
| `server/routes/features_timetable.py:27, 120` | Verschieben `day < st.days` | R3-A1 (Tage), R4-A1 (Raster) |
| `integrations/untis_gpu.py:455-456, 1035-1039` | GPU014-Stunde, Import setzt `days` | R3-A1 / R4-A1 |
| `frontend/src/features/students/widgets.tsx:74`, `OverviewPage.tsx:60` | `currentSchoolDay(days)`, `periodTimes` global | R3-A2 / R4-A2 |
| `features/classes/ClassDetailPage.tsx:43`, `features/classes/api.ts:36` | Schultag global, `period_times` global | R3-A2 / R4-A2 |
| `features/teacher/widgets.tsx:74`, `features/teacher/types.ts:40,120-121` | `describeWindows(…, week_labels)` | R3-A2 |
| `pages/StudentAbsencesPage.tsx:54` | `currentSchoolDay(days)` | R3-A2 (Tage), R4-A2 (Raster) |
| `pages/AdminPage.tsx:229` | Demo-Text „A/B-Wochen“ | R3-A2, Ausnahme KZ-7 |
| `api/errors.ts:84` | Feldname „Wochen im Rhythmus“, neue Felder fehlen | R3-A2 (nach R2-D) |
| `lib/substitution.ts` (`statsWeek`), `lib/csvFields.ts:68`, `pages/PrintSubstitutionsPage.tsx:20` | Mo + days, CSV-Hilfe, `currentSchoolDay()` fest 5 | R3-A2 (KZ-2 nach R2) |
| `pages/DashboardPage.tsx:71-81, 117, 127, 236, 262, 273-317`, `pages/MonitorPage.tsx:90, 119` | Schultage, Badge, `periodTimes`, Ende | R3-D (B-12) bzw. R4-A2 |
| `docs/DESIGN.md:109` | Beispiel „2 = A/B-Wochen“ verletzt G1 | R3-A2, Ausnahme KZ-9 |
| `docs/beispielschulen/*.json/.md`, `README.md`, `docs/ARCHITECTURE.md`, `VORSCHAU.md`, `BETRIEB.md`, `docs/code/README.md` §4 | A/B, Schulwochen ohne Ferien, Woche 0 = A | R3-A1 (Doku) |

### 14.5 Pakete (ersetzt Teile von §11.1)
- **P1 R3-D ist B-12** (OFFENE-PUNKTE §3.1, KZ-9). B-12 bekommt als Zusatz: Startseite und Monitor nutzen
  `week_info.week_text` und die 7-Tage-Helfer. Ohne diesen Zusatz macht es niemand.
- **P2 Wer R3-A2/R4-A2 baut.** Spur D ist in R3 (B-12) und R4 (B-11) belegt. R3-A2 und R4-A2 sind daher ein zweiter
  Agent der Spur A. Ausnahmen in fremden Zonen werden vorab in AGENT_NOTES angekündigt:
  - KZ-9: `SettingsPanels.tsx`, `TimetableGrid.tsx`, `TimetablePage.tsx`, `MyDayView.tsx`, `DESIGN.md`.
  - KZ-6: `features/classes/*`, `students/*`, `channels/VisibilityPicker.tsx`, `StudentAbsencesPage.tsx`.
  - KZ-7: eine Zeile in `AdminPage.tsx`.
- **P3 R4-B (B-08) ändert `features_channels.py`.** R4-A1 fasst diese Datei nicht an. Die Umrechnung von `lesson_period`
  und `visible_from` liegt in `channels.py` (Logik) und in `features_classes.py` (Route). Beide hängen an `Settings`
  nur am Ende an.
- **P4 Abgrenzung zu B-02, B-16 und B-42.**
  - R3/R4 übernehmen B-02 Kriterium 1 (über Z3), 7 und 8 sowie B-16 Kriterium 1–5. B-16 entfällt, B-02 behält
    Kriterium 2–6.
  - OFFENE-PUNKTE §3.2 beschreibt noch „R3-A · B-02“; das ist gegenüber §3.1 veraltet und wird korrigiert.
  - B-42 (R5-D) baut `RecurrencePicker` auf `lib/weeks.ts` und `WeekPatternInput` auf.
- **P5** B-43 Kriterium 2 („Woche 1/2 statt Zykluswoche“) kollidiert mit `week_text`. Im Glossar wird festgelegt:
  „Zykluswoche k von N“ nur im Datumsbezug, in Mustern „Woche k“. Der Begriffstest erlaubt „Zykluswoche“.
- **P6 (Empfehlung)** R3-A1 innerhalb der Spur in zwei Schritten: (a) Kern einschließlich Engine und Generator, (b)
  Schnittstellen, Demo und Doku. Dazwischen läuft die komplette Suite einmal.

### 14.6 Vertrag (Ergänzung zu §11.2)
```ts
// R3 – Settings += cycle_start_week: number (1…53, Std. 1); school_year_history: string[];
//   cycle_shifts: {date: string; cycle_week: number; note?: string}[];  week_anchors entfällt (W1)
//   school_year_end nur lesend (abgeleitet, W3); PUT /settings nimmt keep_cycle_phase?: boolean (Std. true)
export interface WeekPattern { every: number; from: number; to?: number }   // 1-basiert, nur in Requests
// week_pattern statt weeks (nie beides → 422) in: /data/courses, /data/duties, /data/classes (unavailable[]),
//   /data/teachers (unavailable[], wishes[], time_windows[]), Lehrkraft-Profil WindowIn/RuleIn
// TimetableView.week bleibt (Zykluswoche, 0-basiert); cells[].day = Wochentag 0–6, nicht Spaltenindex
// ClassWeek.days / MyWeek.days: immer 7 Einträge (Mo–So) mit day_kind und has_items: boolean
// Profil-availability: {weeks: number[]; weeks_text: string; day: number; periods: number[]}[] (gruppiert)
// 409 cycle_change: detail = {message: string; code: 'cycle_change'; changes: {kind,id,label,before,after}[]}
//   (Muster features_channels.py:1636); force_cycle_change: true übernimmt
// URL: ?datum=JJJJ-MM-TT kanonisch, ?woche=L = laufende Woche des aktuellen Schuljahres (W6)
// R4 – TimetableView.blocked[] += begin?: string; end?: string  (layout = 'timeline')
//   move_options: {day: number; start: number; row?: number}[]; Cell/Entry.period|start = Index im Klassenraster
//   Monitor: period_times entfällt (entries[].time/end_time); Schüler-Übersicht und Krankmeldung: grid {id, periods}
//   BreakIn += splits_double: boolean (Std. true)
```

| Feld | Wertebereich |
|---|---|
| `Settings.cycle_weeks` / `SchoolClass.cycle_weeks` | 1 … 53 / 0 … 53 (0 = Schulvorgabe) |
| `cycle_start_week` (Schule, Klasse) | 1 … 53 |
| `cycle_shifts[].cycle_week` | 1 … N; höchstens ein Shift je Woche |
| `school_days` | eindeutige 0 … 6; Schule mindestens 1 Tag, Klasse leer = Schulvorgabe |
| `weeks[]` | 0 … N−1, eindeutig, höchstens 53; alle Wochen → `[]` |
| `WeekPattern` | 1 ≤ every ≤ N, 1 ≤ from ≤ N, from ≤ to ≤ N |
| `TimeGrid.periods` | 1 … 16; HH:MM, start < end ≤ 24:00, Ende i ≤ Beginn i+1 |
| `breaks[]` | after 0 … n−2; minutes 0 … Abstand der Nachbarstunden; splits_double bool |
| `core_latest` | null oder 0 … n−1 |
| `TimeRule.start/end`, `Absence.start/end` | beide leer oder beide HH:MM, start < end ≤ 24:00 |
| `site_travel_minutes` / `long_gap_minutes` | 0 … 240 / 0 … 600 (0 = aus) |
| `SchoolClass.time_grid`, `SupervisionArea.time_grid` | `""` oder eine vorhandene `time_grids.id` |

### 14.7 Abnahme und Tests (Korrekturen zu §12) und Entscheidungen
- **R3-A1 Nr. 1** wird ersetzt durch vier Fälle:
  - Beginn Mi 26.08.2026 ergibt Woche 1 = 24.–30.08.
  - Ein Shift „ab 11.01.2027 Zykluswoche 1“ bei N = 2 (natürlich 2) lässt L = 20.
  - Im KW-Modus haben 28.12.2026 und 04.01.2027 bei N = 2 beide Zykluswoche 1.
  - Im KW-Modus 2027/28 ist KW 30 doppelt; die URL läuft über das Datum.
- **Neu (R3-A1):**
  - W2 mit Phasenerhalt (Altdokument → Beginn 01.08.: identisch, s = 6).
  - W4 ohne Phantom-Schuljahr.
  - W7: 53 Wochen bei N = 2.
  - W9: 2 → 3 mit ZEH-Fenstern gibt 409 mit „Woche 3: nicht verfügbar“.
  - R1: Sekretariat ändert `time_grid` → 403.
  - W5: Schule N = 52 + Klasse N = 3 wird angenommen; das ersetzt den 422-Fall in Nr. 8.
- **R3-A1 Nr. 10** bekommt einen langsamen Test an der großen Demo (14 je Jahrgang): N = 6 periodisch aus N = 2 mit
  0 unverplant.
- **R4-A1 Nr. 4:** 5a braucht im Test `max_periods_per_day ≥ 10`; Standard 8 sperrt die 10. Stunde (Z1).
- **R4-A1 Nr. 11** gilt mit `splits_double = false` und `long_gap_minutes = 0`. Die gewollten Änderungen (Doppelstunden,
  Aufsicht „im Haus“ 90 min) prüfen eigene Tests.
- **Neu (R4-A1):**
  - Konflikt 45/60 bei Teilüberlappung.
  - Untis-Abbildung streng steigend ohne Doppelung (Z6a), GPU014-Stunde über die Zeitachse.
  - `dry_run` ohne Krankmeldungsdetails (R3).
- **Messwerte Generator, große Demo** (99 Klassen, 169 Lehrkräfte, 172 Räume, 1093 Kurse, 20 s):

  | Lauf | Slots je Objekt | Zeit | unverplant |
  |---|---|---|---|
  | W = 2, D = 5, P = 12 (heute) | 120 | 20,1 s | 0 |
  | W = 6 periodisch umgerechnet, D = 7, P = 15 (≥ V = 6 mit Abendatomen) | 630 | 20,4 s | 0 |
  | W = 3 ohne Umrechnung, D = 7, P = 15 | 315 | 20,1 s | 15 (nur ZEH, W9) |
  | W = 52, D = 5, P = 12 (heute bei N = 52) | 3120 | 23,8 s | 750 |

  Konstruktion ohne Optimierung: 2,6 s bei D = 5 und 3,9 s bei D = 7, wenn Tage nicht übersprungen werden. Das
  Überspringen in `best_slot`, `_repair` und `_random_move` ist deshalb Pflicht.
  Fazit: Das Atom- und Variantenmodell passt in den bestehenden Generator und ist bei V ≤ 6 realistisch (gemessen).
  Umbauten: `_slots` (Klassenslots getrennt von Atomslots), `place`/`remove`, `check` (Tageshöchstzahl zählt Blöcke,
  nicht Atome), `_assign_rooms`, `_travel_ok`, `teacher_day_cost`, `best_slot`/`_repair`/`_random_move` (Startbereich
  je Kursraster). `_random_swap` tauscht schon heute nur innerhalb eines Klassengitters.
- **Entscheidungen** (zusätzlich zu §13):
  - **E1 Ergänzung:** Bei Woche 1 = 1. August braucht der Zyklus `cycle_start_week` (W2). Alternative: Woche 1 = erste
    Schulwoche; dann liegen die Sommerferien am Ende des alten Schuljahres.
  - **E4 Kopplung über verschiedene Zeitraster:** Empfehlung **deckungsgleiche Stunden zulassen** (Z4), sonst wie §6
    verbieten.
  - **E5 Deputat bei 60-Minuten-Stunden:** Empfehlung **je Stunde 1 wie heute**; eine Umrechnung nach Minuten wäre
    eine eigene Anforderung.

## 15. Prüfvermerk 2 (11.10., Vollständigkeit für Umsetzung und Abnahme)

Vorrang vor §1–§14. Geprüft wurde, ob zwei Agenten je Runde ohne Rückfragen und ohne Dateikonflikte bauen können und ob
ein Prüf-Agent jedes Kriterium nachweisen kann. Nachgerechnet mit `…/scratchpad/zyklus/q_*.py` und `.out` (flüchtig);
die maßgeblichen Zahlen stehen hier.

Ergebnis: Mit §14 ist das Modell vollständig. Es fehlten aber fünf Dinge:
- ein reproduzierbarer Generator für die Vergleichstests (V1),
- ein Springstunden-Maß, das alte Dokumente nicht verändert (V2),
- Dateigrenzen gegenüber R3-B und R4-D (V3, V4),
- Wochenmuster, die nicht am Schulzyklus hängen (V6, Entscheidung E6),
- ein Vertrag an einer einzigen Stelle (§15.3).

### 15.1 Wünsche des Auftraggebers → Abschnitt (Satz für Satz)
| Satz (11.10.) | erfüllt durch | Nachweis | Rest |
|---|---|---|---|
| (1a) „Das A B Ding war doch Quatsch, das sollte doch komplett durch einen Zyklus, wo alle Wochen im Jahr sind, ersetzt werden.“ | G1, §2.4, §3, §10, W5 (N bis Y), V19 | R3-A1 Nr. 3, 4; R3-A2 Nr. 6; T3 | Muster für Lehrkräfte hängen am Schulzyklus (V6, E6) |
| (1b) „Dieses AB-Wochen-Prinzip kann man doch gar nicht gebrauchen, wenn man mehr unterschiedliche Wochen hat.“ | N = 1 … 53, Zyklus je Klasse (§3), Varianten (§7.2, W5), WeekNav, Muster-Editor (§8) | R3-A1 Nr. 4, 8, 10; Messwerte §14.7 | – |
| (2a) „… es sollen wirklich alle Wochen angezeigt werden von Woche 1 bis Woche 52“ | G2, §2.3, W1, W3, WeekNav 1 … Y, Wochenübersicht (§8) | R3-A1 Nr. 6; R3-A2 Nr. 2, 4 | – |
| (2b) „alle Wochen sollen 7 Tage haben“ | G4, §5, §14.6 (7 Einträge), V10 (Spalten) | R3-A1 Nr. 7; T7 | – |
| (2c) „… eine Option …, die Länge der Tage einzustellen über die aktuellen Stunden, individuell pro Klasse“ | §6 Zeitraster je Klasse, Z1 „Unterricht bis Stunde“, Unterrichtstage je Klasse (§5), V7 (freie Längen auch im Standard), V12 (Einstellung an der Klasse) | R4-A1 Nr. 1, 2; R4-A2 Nr. 2; T12 | – |
| (2d) „… wenn du eine Abendklasse bist, … dann soll ein Tag erst um 16 Uhr … anfangen“ | §6 Demo-Raster „Abend“ ab 16:00 | R4-A1 Nr. 2 | – |
| (2e) „… und eine normale Klasse hat dann morgens ihre erste Stunde“ | G5, Standard-Raster | R4-A1 Nr. 2 | – |
| (2f) „… und die einen Klassen haben nirgends ihre erste Stunde“ (keine gemeinsame 1. Stunde) | G5, G7, §6 „Stundennummer je Raster“, Z5 | R4-A1 Nr. 4 | – |
| (2g) „… wenn ein Lehrer zuerst früh hat und dann auch die späten Klassen hat, dass das richtig angezeigt wird.“ | G6, §7, §8 Zeitachse, Z5, Z9, V2, V18 (Druck, Profilvorschau) | R4-A1 Nr. 3; R4-A2 Nr. 1, 4, 5 | – |

Abweichungen von den Grundsätzen des Leads, zu bestätigen:
- **Formel:** Mit dem Standard s = 1 gilt genau (L − 1) mod N + 1. s ≠ 1 entsteht nur durch Phasenerhalt (W2), einen
  eigenen Klassenzyklus (§3) oder eine Verschiebung (W1).
- **Anzeige:** „Zykluswoche k von N“ steht nur neben der laufenden Woche, sonst „Woche k“ (G3, P5). Zwei verschiedene
  „Woche“-Zahlen in einer Zeile wären missverständlich (Entscheidung E7).
- **N = 53** ist immer speicherbar. In Jahren mit 52 Wochen warnt die Prüfung (§2.2).

### 15.2 Neue Befunde und Festlegungen
- **V1 Generator für Vergleichstests reproduzierbar (hoch).**
  - Befund: `optimize` läuft nach Uhrzeit, die Temperatur folgt der verstrichenen Zeit (scheduler.py:684, 707-730).
    Drei Läufe der kleinen Demo mit `seed = 3` und `time_limit = 1` ergaben drei verschiedene Pläne (70 000, 65 600 und
    72 600 Iterationen, q_pruef2.out). Konstruktion und Reparatur allein sind über Prozesse und `PYTHONHASHSEED` gleich
    (q_determ.out). Mit fester Iterationszahl sind auch die Pläne gleich, auch `teacher_gaps` = 404 (q_determ2.out).
  - Folge: „Gleicher Seed, dasselbe Ergebnis“ (R3-A1 Nr. 10, R4-A1 Nr. 11) ist so nicht prüfbar. Auch die conftest-Demo
    (`demo_school`, conftest.py:91-97) wird in jedem Lauf neu berechnet.
  - Festlegung: `generate(…, iterations: Optional[int] = None)` und `Scheduler.optimize(seconds, iterations=None)`. Mit
    `iterations` endet die Optimierung nach genau so vielen Iterationen, die Temperatur folgt it/iterations. Ohne den
    Parameter (Standard `None`) verhält sich alles wie heute. Vergleichstests nutzen `iterations = 20000` und ein
    gespeichertes Dokument (T0).
- **V2 Springstunden über mehrere Raster (hoch).**
  - Befund: §7.2 misst Lücken in Minuten ÷ Standardlänge. An der Test-Demo (2 Klassen je Jahrgang, generiert) ergibt das
    572,1 statt 404 Springstunden. 230 von 496 Lehrkraft-Tagen weichen ab, weil Pausen mitzählen (q_gaps.out). Damit
    ändert sich jedes Standard-Dokument, gegen R4-A1 Nr. 11.
  - Festlegung (ersetzt §7.2 „Kosten“ Satz 1–2 und Z2 Satz 2):
    - Eine Lücke zwischen zwei Blöcken einer Lehrkraft am selben Tag zählt so viele Springstunden, wie Stunden des
      Rasters ganz in der Lücke liegen. Bei zwei verschiedenen Rastern gilt das größere der beiden Ergebnisse.
    - Bei `long_gap_minutes > 0` zählt eine Lücke höchstens ⌊long_gap_minutes ÷ Standard-Stundenlänge⌋.
  - Im Standard-Raster ist das genau der heutige Wert (404 = 404, q_gaps.out). SPT mit Lücke 13:20–16:00 zählt 3, mit
    dem Demo-Wert 120 zählt sie 2.
- **V3 Dateikonflikt mit R3-B (hoch).**
  - Befund: B-07 (R3-B) ändert in Runde 3 `features_student_self.py`, `features_student_absences.py` und
    `features_channels.py` (PRODUKT-BACKLOG B-07 „Dateien“). §14.4 legt in dieselben Dateien Ausnahmen von R3-A1.
  - Festlegung: R3-A1 ändert diese drei Dateien erst nach der Integration von R3-B (Schritt 7, §15.6), mit je einer
    kleinen Änderung: `features_student_absences.py:343-344`, `features_student_self.py:386-461` sowie
    `features_channels.py:627, 1044, 1297` (Klasse übergeben) und `:2523` (Docstring).
  - Bis dahin rufen diese Dateien `is_school_day(school, d)` ohne Klasse auf. Das bedeutet „Schulöffnungstag“ und
    stimmt, solange keine Klasse abweichende Tage hat.
  - `student_self.py` und `channels.py` (Logik) gehören nicht zu B-07 und bleiben bei R3-A1.
  - Ist R3-B nicht rechtzeitig fertig, geht Schritt 7 an R4-A1 (Ausnahme KZ-6). `features_channels.py` bekommt dann
    R4-B mit (P3).
- **V4 Konflikt mit R4-D in `SettingsPanels.tsx` (mittel).**
  - Befund: B-11 beansprucht die Zeilen 433–583. Darin liegen „Schule & Zyklus“ (Z. 516) und „Zeitraster“ (Z. 545).
  - Festlegung: R3-A2 löst `SchoolSettingsPanel` (ohne Webhooks) in die neue Datei `pages/planning/CalendarPanel.tsx`
    (Spur A) heraus. In `SettingsPanels.tsx` bleibt nur der Einhängepunkt. Das geschieht in Runde 3, in der Spur D dort
    nicht arbeitet. Der Zeitraster-Editor aus R4 hängt in `CalendarPanel`.
  - Der Lead begrenzt B-11 auf `WeightsPanel` (Z. 223–496).
- **V5 Abgrenzung zu B-25, B-45 und B-46 (mittel).**
  - B-45 (Rhythmus je Klasse, Krit. 2 „kgV, Obergrenze 4“) widerspricht W5 und A-67 und entfällt; R3/R4 ersetzen es.
    Krit. 3 (Klassen ohne Wochenregeln auf „kein Zyklus“ setzen) wird nicht übernommen: Klassen erben die
    Schulvorgabe, damit ändert keine Regel still ihre Bedeutung.
  - B-25: R3 übernimmt Krit. 1 ohne Halbjahre, aus Krit. 2 nur `Holiday.kind` und Krit. 3 ohne „Bezeichnung
    einstellbar“, weil diese Option Buchstaben wieder erlauben würde (G1). Bei B-25 bleiben Halbjahre,
    Ferienvorlagen je Bundesland und Krit. 4.
  - Die Werte von `Holiday.kind` folgen B-25: `ferien | feiertag | beweglich | schulfrei` statt `sonstiges`.
  - B-46 („gültig ab“) bleibt unberührt. Verschiebungen und Schuljahre hängen am Datum und vertragen sich damit.
- **V6 Wochenmuster hängen am Schulzyklus (hoch, Entscheidung E6).**
  - Befund: Lehrkraft-Regeln, Zeitfenster und Aufsichten zählen im Schulzyklus (§3). Ein Muster ist nur mit
    1 ≤ every, from ≤ N möglich (§14.6). Bei N = 1 oder 2 lassen sich „jede 3. Woche“ und „alle 2 Wochen ab Woche 10“
    (A-50/A-51, Grundsatz des Leads) nicht speichern. Das geht nur bei N ≥ 10 bzw. wenn N ein Vielfaches von 3 ist. Eine
    Lehrkraft kann den Schulzyklus im Profil nicht ändern.
  - Empfehlung:
    - `TimeRule`, Zeitfenster und `Duty` bekommen optional `rhythm: {"every": k, "from_week": s, "to_week": e}` in
      laufenden Wochen (1-basiert, `to_week` 0 = offen).
    - Mit `rhythm` gilt `weeks` nicht. Die Regel ist in L aktiv, wenn s ≤ L, L ≤ e (bzw. e offen) und
      (L − s) mod k = 0.
    - Der Generator braucht nichts Neues, denn W5 bildet die Signaturen ohnehin je realer Woche 1 … Y. Kurse und Stunden
      bleiben im Kurszyklus (Phasenregel).
  - Ohne E6 bietet der Muster-Editor nur, was in N passt, und zeigt „Im Wochenzyklus der Schule nicht möglich“.
- **V7 Freie Stundenlänge auch im Standard-Raster (mittel, A-31).**
  - Befund: Das virtuelle Standard-Raster leitet jedes Ende aus `period_minutes` ab (§6). „45 min, 60 min, frei“ geht
    so nur in zusätzlichen Rastern.
  - Festlegung: `Settings.period_ends: list[str] = []` (leer = Beginn + `period_minutes`). Der Rechner speichert das
    Standard-Raster über `PUT /settings` (`period_times`, `period_ends`, `breaks`).
  - B-16 Krit. 1 gilt damit ohne gespeichertes `day_start` als erfüllt: Die Zeiten werden berechnet und als Liste
    gespeichert.
- **V8 Ein benutztes Raster ändern (mittel, wie U-13).**
  - Befund: Weniger Stunden, eine entfernte Pause oder ein anderes Raster eines Aufsichtsbereichs lassen Stunden,
    Klausuren und Aufsichten ins Leere zeigen.
  - Festlegung: `PUT /data/time_grids/{id}`, `PUT /settings` (Standard-Raster) und `PUT /data/areas/{id}`
    (`time_grid`) antworten mit 409 `grid_change` (Form §15.3); `?force=1` übernimmt.
  - Danach meldet der Bericht „liegt außerhalb des Zeitrasters“. Aufsichten auf einer entfallenen Pause werden
    gelöscht und in `changes` genannt.
- **V9 Offene Lehrkraft-Anträge beim Zykluswechsel (mittel).**
  - Befund: `teacher_requests.payload` (feature_models/teacher.py:30) enthält `time_windows` und `wishes` mit `weeks`
    im alten Zyklus. `weeks.convert` erreicht diese SQL-Daten nicht.
  - Festlegung: Beim Einreichen schreibt der Server `payload.cycle_weeks`. Weicht der Wert bei der Genehmigung ab, wird
    exakt umgerechnet, sonst gibt es 409 „Der Antrag stammt aus einem anderen Wochenzyklus. Bitte neu einreichen.“
    Alte Anträge ohne das Feld gelten als aktueller Zyklus. Es braucht keine Migration (JSON-Spalte).
- **V10 Spalten der Wochenansicht (mittel, §8 gegen E2).**
  - Befund: §8 sagt „Spalten sind die Unterrichtstage der Klasse“, E2 „Mo–Fr fest“.
  - Festlegung: Die Spalten laufen immer zusammenhängend ab Montag. Ihre Zahl ist n = 1 + max({4} ∪ Unterrichtstage
    der Klasse ∪ Tage mit Zellen oder Klausuren der Woche); die Unterrichtstage zählen nur in Klassen- und
    Schüleransichten. Mit `all_days=1` ist n = 7.
  - `cells[].day` ist damit Wochentag und Spaltenindex zugleich; `TimetableGrid` bleibt indexbasiert. `days[]` bleibt
    die Liste der Spaltennamen.
  - Tage ohne Unterricht der Klasse tragen `day_kind = kein_unterrichtstag` und werden abgeblendet. Ferientage behalten
    die Zellen des Plans; die Spalte trägt das Ferien-Badge.
- **V11 `week_no` im KW-Modus (mittel).**
  - Befund: §1 setzt im KW-Modus L = KW, W6 dagegen „laufende Woche des Schuljahres“.
  - Festlegung: `week_no`, `?woche=` und der API-Parameter `week_no` sind in beiden Modi die Position 1 … Y im
    Schuljahr. Angezeigt wird im Modus `school_year` „Woche {week_no}“, im Modus `iso` nur „KW {iso_week}“. Die
    Zykluswoche rechnet im Modus `iso` weiter mit der KW (§2.2).
- **V12 Planungsfelder an der Klasse (mittel, A-32 „Einstellungen bei ihrer eigenen Sache“).**
  - Befund: Die Klassen-Seite hat keine Einstellungsansicht (Reiter Wochenplan, Lehrkräfte, Schüler). `ClassPatchIn`
    kennt nur Raum und Klassenleitung (features_classes.py:290-293).
  - R3: `PATCH /classes/{id}` nimmt zusätzlich `school_days`, `cycle_weeks` und `cycle_start_week`. Dafür braucht es
    `timetable.edit` (sonst 403); dazu kommen `?force=1` und 409 `cycle_change`.
  - `ClassHeader` bekommt eine Zeile „Planung“ mit Zeitraster, Unterrichtstagen und Wochenzyklus. Sie ist bearbeitbar
    wie Raum und Klassenleitung und erscheint nur mit `can_plan`.
  - R4: `time_grid` ändert nur `POST /classes/{id}/time-grid`. Ein `PUT /data/classes/{id}` mit geändertem `time_grid`
    gibt 409 `time_grid_change`, wenn die Klasse Stunden hat. Beim Anlegen ist jedes Raster erlaubt.
- **V13 Bestätigen über `?force=1` (mittel).**
  - Befund: Die bestehende Konvention ist ein Query-Parameter (features_data.py:611, 646, 683). `SettingsIn` hat
    `extra=forbid`.
  - Festlegung: `PUT /settings?force=1&keep_cycle_phase=0`, `PUT /data/{collection}/{id}?force=1`,
    `PATCH /classes/{id}?force=1`. `force_cycle_change` und `keep_cycle_phase` sind keine Body-Felder (ersetzt §3 und
    §14.6).
- **V14 Feinheiten des Zyklus (niedrig).**
  - `cycle_shifts` gelten für die Schulvorgabe und alle Klassen mit `cycle_weeks = 0`. Klassen mit eigenem Zyklus haben
    keine Verschiebungen.
  - `SchoolClass.cycle_start_week` zählt nur bei `cycle_weeks > 0`. Das Berufskolleg-Beispiel FI11c bekommt deshalb
    `cycle_weeks = 2` und `cycle_start_week = 2`.
  - Der Phasenerhalt (W2) gilt auch beim Wechsel von `week_numbering`.
  - s ist eindeutig: die neue Position des Montags, an dem bisher Zykluswoche 1 begann, wenn sie in 1 … Y liegt
    (Beispiel: 6). Sonst gilt der kleinste Wert ≥ 1 mit derselben Phase.
  - Der Zyklus eines Kurses ist der seiner Klassen, wenn alle gleich sind, sonst der Schulzyklus; dann ist der Kurs nur
    wöchentlich erlaubt (§3).
  - Weicht der Kurszyklus vom Schulzyklus ab, endet `weeks_text` auf „von N“, z. B. „Woche 1 von 3“.
- **V15 Ferienart beim Lesen alter Daten (niedrig).**
  - Fehlt `kind`, gilt `ferien`, wenn der Name „ferien“ enthält (Groß- und Kleinschreibung egal), sonst `feiertag`.
    Das entspricht dem heutigen `holidayTag` (WeekTab.tsx:53-54); der Tag der Deutschen Einheit bleibt „Feiertag“.
  - `day_kind`: `ferien` → `ferien`, alle anderen Arten → `feiertag`.
- **V16 Keine Brüche in fremden Dateien (mittel).**
  - Neue Felder bestehender TS-Typen sind optional (`?`); die Verbraucher setzen Standards. `npm run lint` prüft die
    Tests mit (tsconfig `include: ["src"]`). Pflichtfelder brächen sonst Objektliterale anderer Spuren
    (`pages/planning/curricula.test.ts:14` SchoolClass, `lib/__tests__/substitution*.test.ts` Entry).
  - `lib/dates.ts`: `isWeekend`, `shiftSchoolDay` und `currentSchoolDay` nehmen `schoolDays: number | readonly
    number[]` (eine Zahl heißt wie heute „die ersten n Tage“). `cycleWeekOf` und `weekLabel` entfallen erst in dem
    Schritt, der `TimetablePage`, `DutiesPage` und `dates.test.ts` umstellt.
  - Neue Styles stehen in eigenen Dateien je Baustein (`components/weeks.css`, `components/timegrid.css`) und werden
    im Baustein importiert, wie in `features/konto`. `styles/*` (KZ-9) bekommt höchstens angekündigte Einzeiler.
- **V17 Gemeinsamer Arbeitsbaum (mittel).** Alle Agenten arbeiten im selben Baum auf getrennten Ports (AGENT_NOTES).
  Jeder Zwischenstand ist sofort für alle sichtbar. Deshalb endet jeder Schritt in §15.6 mit grünem `ruff`, den eigenen
  Tests und den Tests der berührten fremden Dateien. Die komplette Suite läuft an den markierten Gates.
- **V18 Weitere fehlende Stellen** (zusätzlich zu §14.4):

| Stelle | Was | Paket |
|---|---|---|
| `server/jobs.py:128, 137, 195, 250, 512` | sechste Aktiv-Logik („Lesson, sonst Kurs“), Schulzyklus statt Kurszyklus, Text „(Woche A/B)“ | R3-A1 (Tabelle §4 ergänzen) |
| `server/routes/features_student_self.py:386-461` | „heute Schultag“ und nächster Schultag ohne Klasse | R3-A1 Schritt 7 (V3) |
| `server/routes/features_classes.py:466, 662` | Klassenwoche `min(7, st.days)`; „findet nicht statt“ mit `weekday() < st.days` | R3-A1 (Ausnahme KZ-6) |
| `integrations/schulmanager_online.py:62, 103-106` | LIESMICH „A/B-Wochen“, „(Woche A)“ | R3-A1 |
| Docstrings `models.py:9, 54-55, 330-331`, `scheduler.py:6, 12`, `channels.py:29`, `duties.py:149`, `ical.py:10`, `integrations/__init__.py:14`, `untis_gpu.py:79-84, 873`, `teacher_profile.py:290`, `csv_io.py:221, 314` | „A/B“, „Woche A/B“ | R3-A1 (Grep T3) |
| Tests `test_classes.py:17, 284`, `test_integrations.py:308, 448, 536, 541`, `test_substitution.py:14, 297, 303-304`, `test_lesson_absence.py:18` | erwarten „A“/„B“ | R3-A1 |
| `server/feature_models/teacher.py:30` (`payload`) | Wochen offener Anträge | R3-A1 (V9) |
| `frontend/src/pages/PrintTimetablePage.tsx:18, 40` | `woche` 0-basiert, Titel „– Woche {week_label}“ | R3-A2 (`?datum=`, `week_text`); R4-A2 prüft die Zeitachse im Druck |
| `features/classes/logic.ts:75`, `classes.test.ts:130` | „KW 41 · 05.10.–09.10.2026 · Woche A“ | R3-A2 |
| `features/teacher/windows.ts:89`, `teacher.test.ts:29, 42` | erwarten „Woche B“ | R3-A2 |
| `pages/MasterDataPage.tsx:167` | Hilfetext „Woche A Mittwoch weg …“ | R3-A2 |
| `features/channels/VisibilityPicker.tsx:4, 162`, `features/channels/types.ts:215` | Kommentar „A/B-Woche“, Badge „Woche {week_label}“ | R3-A2 |
| `components/TimetableGrid.tsx:60, 267`, `components/RuleEditor.tsx:24-25, 63, 88` | Buchstaben | R3-A2 (Ausnahme KZ-9) |
| `features/classes/dialogs.tsx:203-392` | `periodTimes`/`PeriodToggles` der Dialoge | R4-A2 (Klassenraster) |
| `features/teacher/TeacherProfilePage.tsx:372`, `TeacherRequestsPage.tsx:113` | Vorschau nur im Standard-Raster | R4-A2 (Zeitachse der Lehrkraft, A-69 „überall“) |

- **V19 Buchstaben-Grep zu eng (mittel).** R3-A1 Nr. 3 sucht nur `chr(ord("A")` und `chr(65`. Damit fallen
  `schulmanager_online.py:62` („A/B-Wochen“ im LIESMICH der Exportdatei), Demo-Notizen und Hilfetexte durch. Die
  Festlegung steht in T3 (§15.7).

### 15.3 Vertrag an einer Stelle (ersetzt §11.2 und §14.6, wo sie abweichen)
**Python** (`models.py`; neue Settings-Felder der Spur A direkt nach `cycle_start`, Spur B hängt weiter am Ende an)

| Runde | Klasse | Feld | Typ = Standard | Grenzen |
|---|---|---|---|---|
| R3 | – | `WEEKDAYS` | 7 Namen Montag … Sonntag | – |
| R3 | Settings | `week_numbering` | `str = "school_year"` | `school_year` oder `iso` |
| R3 | Settings | `school_year_start` | `str = ""` | ISO-Datum oder leer (leer = `cycle_start`) |
| R3 | Settings | `school_year_history` | `list[str] = []` | ISO-Daten, aufsteigend, je ≥ 300 Tage Abstand (W4) |
| R3 | Settings | `cycle_start_week` | `int = 1` | 1 … 53 |
| R3 | Settings | `cycle_shifts` | `list[dict] = []` | `{"date": ISO, "cycle_week": 1 … N, "note": str ≤ 200}`, höchstens eine je Woche |
| R3 | Settings | `school_days` | `list[int] = []` | eindeutig 0 … 6, mindestens 1; leer = `range(days)` |
| R3 | Settings | `cycle_weeks` (bleibt) | `int = 1` | 1 … 53 |
| R3 | Settings | `cycle_start`, `days` (bleiben) | – | nur gelesen bzw. abgeleitet (§2.1, §5) |
| R3 | SchoolClass | `cycle_weeks`, `cycle_start_week`, `school_days` | `int = 0`, `int = 1`, `list[int] = []` | 0 … 53, 1 … 53, 0 … 6 |
| R3 | Holiday | `kind` | `str = "ferien"` (Lesepfad V15) | `ferien`, `feiertag`, `beweglich`, `schulfrei` |
| R3 (E6) | TimeRule, Zeitfenster-dict, Duty | `rhythm` | `Optional[dict] = None` | `{"every": 1 … 53, "from_week": 1 … 53, "to_week": 0 … 53}` |
| R4 | neu `TimeGrid` | `id`, `name`, `periods`, `breaks`, `core_latest` | `str`, `str`, `list[dict]`, `list[dict] = []`, `Optional[int] = None` | Tabelle §14.6 |
| R4 | Settings | `period_ends` | `list[str] = []` | leer oder eine Zeit je Stunde, Ende > Beginn (V7) |
| R4 | Settings | `site_travel_minutes`, `long_gap_minutes` | `int = 0`, `int = 0` | 0 … 240, 0 … 600 |
| R4 | `Settings.breaks[]`, `TimeGrid.breaks[]` | `splits_double` | fehlt = `True` (`Settings.from_dict` ergänzt) | bool |
| R4 | SchoolClass, SupervisionArea | `time_grid` | `str = ""` | `""` oder vorhandene ID |
| R4 | TimeRule, Absence | `start`, `end` | `str = ""` | beide leer oder beide HH:MM |

Gegenüber §2.1 und §11.2 entfallen `week_anchors` und das eingebbare `school_year_end`. `SettingsIn` erhält dieselben
Felder mit denselben Grenzen, `BreakIn` zusätzlich `splits_double: bool = True`.

**Funktionen** (Namen fest, damit Tests und Prüf-Agent sie finden)
- `calendar_utils`: `monday_of(d)`, `school_year(st, d) -> (start_monday, weeks_in_year)`, `week_no(st, d) -> int`
  (Position, außerhalb ≤ 0 bzw. > Y), `cycle_week(school, d, cls=None) -> int` (0-basiert),
  `week_info(school, d, cls=None) -> dict`, `class_days(school, cls)`, `open_days(school)`,
  `is_school_day(school, d, cls=None) -> (bool, Grund)`, `day_kind(school, d, cls=None) -> str`.
- `weeks`: `cycle_of(school, owner=None) -> Cycle(n, start_week, shifts)`, `expand(pattern, n)`,
  `describe(weeks, n, school_n=None)`, `errors(weeks, n)`, `convert(weeks, old_n, new_n) -> (list[int], exact)`,
  `active_weeks(school, lesson, course) -> frozenset[int]`, `lesson_active_on(school, lesson, course, d)`,
  `rule_active_on(school, rule, d)` (E6).
- `timegrid` (R4): `standard(st) -> TimeGrid`, `grid_of(school, owner=None)`, `errors(grid)`,
  `preview(start, length | lengths, breaks, count)`, `timeline(school)`, `span(grid, start, length) -> (Beginn, Ende)`
  in Minuten.
- `Settings.week_of(d)` bleibt (Zykluswoche der Schule, 0-basiert) und ruft `calendar_utils.cycle_week`.
  `Settings.week_label(w)` gibt `str(w + 1)` bei N > 1, sonst `""`.

**API (JSON)**
- WeekInfo, Beispiel Altdokument am 05.10.2026. Bezug: Klasse und Schüler/in → Klassenzyklus; Lehrkraft, Raum und
  Schule → Schulzyklus.
  ```json
  {"week_no": 6, "iso_week": 41, "iso_year": 2026, "week_start": "2026-10-05", "week_end": "2026-10-11",
   "cycle_week": 2, "cycle_length": 2, "week_text": "Woche 6 · KW 41 · Zykluswoche 2 von 2",
   "holiday_week": false, "holiday_name": null, "in_school_year": true}
  ```
- `GET /calendar/school-year?date=&class_id=` (beide optional; `class_id` nur mit Sichtrecht auf die Klasse, sonst
  404; `open_days` sind dann die Tage der Klasse):
  ```json
  {"start": "2026-08-31", "end": "2027-08-29", "numbering": "school_year", "weeks_in_year": 52, "cycle_weeks": 2,
   "open_days": [0, 1, 2, 3, 4], "warnings": [],
   "weeks": [{"week_no": 8, "iso_week": 43, "week_start": "2026-10-19", "week_end": "2026-10-25",
              "cycle_week": 2, "holiday_week": true, "holidays": ["Herbstferien (Beispiel)"]}]}
  ```
- `GET /timetable/{kind}/{ref}?date=JJJJ-MM-TT | week_no=P | week=<alt, 0-basiert> &all_days=0|1`. Ohne Angabe gilt
  die heutige Woche. Die Antwort trägt `week` (Zykluswoche des Bezugs, 0-basiert), `week_label`, `week_info`, `days`
  (Spaltennamen, V10) und `day_info[]`; sie enthält nur die in dieser Woche aktiven Zellen, jede mit `weeks_text`.
- `POST /settings/calendar-preview?keep_cycle_phase=1`: Body wie `SettingsIn`, aber nur `cycle_weeks`,
  `cycle_start_week`, `cycle_shifts`, `week_numbering`, `school_year_start` und `school_days`. Antwort
  `{exact, changes[], today_before: WeekInfo, today_after: WeekInfo, warnings[]}`.
- 409 für alle Bestätigungen (`cycle_change`, `grid_change`, `time_grid_change`); bestätigt wird mit `?force=1`:
  ```json
  {"detail": {"message": "Der neue Wochenzyklus ändert 3 Einträge", "code": "cycle_change",
              "changes": [{"kind": "course", "id": "K12", "label": "Kurs M 5a", "before": "Woche 2", "after": "entfällt"}]}}
  ```
- R4, Lehrkraftplan SPT (gekürzt). Bei `layout = "timeline"` ist `rows[].period_label` immer `null`; die Nummer trägt
  die Zelle. `start` ist der Index im Raster der Klasse (Z5), `row` die Zeile der Zeitachse. Standard (10 Stunden) und
  „Abend“ ergeben 15 Zeilen; 16:00–16:45 ist eine gemeinsame Zeile.
  ```json
  {"layout": "timeline", "grid": null,
   "rows": [{"key": "0755-0840", "begin": "07:55", "end": "08:40", "label": "07:55–08:40", "period_label": null, "gap_before": 0},
            {"key": "1600-1645", "begin": "16:00", "end": "16:45", "label": "16:00–16:45", "period_label": null, "gap_before": 5}],
   "cells": [{"lesson_id": "L812", "day": 0, "start": 0, "length": 1, "begin": "16:00", "end": "16:45",
              "row": 9, "row_span": 1, "period_label": "1.", "grid": "abend", "classes": ["ABK"]}]}
  ```

**TypeScript** (`api/types.ts`, R3-A2 bzw. R4-A2; neue Felder bestehender Typen optional, V16)
```ts
export type DayKind = 'unterricht' | 'kein_unterrichtstag' | 'ferien' | 'feiertag';
export type HolidayKind = 'ferien' | 'feiertag' | 'beweglich' | 'schulfrei';
export interface WeekInfo { week_no: number | null; iso_week: number; iso_year: number; week_start: string;
  week_end: string; cycle_week: number; cycle_length: number; week_text: string; holiday_week: boolean;
  holiday_name: string | null; in_school_year: boolean }
export interface DayInfo { index: number; name: string; date: string; teaching: boolean; day_kind: DayKind;
  holiday: string | null }
export interface CycleShift { date: string; cycle_week: number; note?: string }
export interface WeekPattern { every: number; from: number; to?: number }          // nur in Requests
export interface WeekRhythm { every: number; from_week: number; to_week?: number } // E6
export interface SchoolYearWeek { week_no: number; iso_week: number; week_start: string; week_end: string;
  cycle_week: number; holiday_week: boolean; holidays: string[] }
export interface SchoolYear { start: string; end: string; numbering: 'school_year' | 'iso'; weeks_in_year: number;
  cycle_weeks: number; open_days: number[]; warnings: string[]; weeks: SchoolYearWeek[] }
export interface ChangeItem { kind: string; id: string; label: string; before: string; after: string }
export interface ConfirmDetail { message: string; code: 'cycle_change' | 'grid_change' | 'time_grid_change';
  changes: ChangeItem[] }
// Settings    += week_numbering?, school_year_start?, school_year_history?, cycle_start_week?, cycle_shifts?,
//                school_days?   (cycle_weeks 1 … 53; cycle_start und days bleiben)
// SchoolClass += cycle_weeks? (0 = Schule), cycle_start_week?, school_days?;  Holiday += kind?: HolidayKind
// TimeRule, Duty, TimeWindow += rhythm?: WeekRhythm | null (E6)
// TimetableView += week_info?, day_info?: DayInfo[]  (days = Spaltennamen ab Montag, V10);  Cell += weeks_text?
// DayPlan += week_info?, day_kind?;  MyDay += day_kind?, has_items?;  MyWeek += week_info? (days: immer 7)
// ClassWeek += week_info? (days: immer 7);  ClassWeekDay += day_kind?, has_items?
// ProfileOptions += school_days?; week_labels = ['1', '2', …];  Availability → {weeks, weeks_text, day, periods}
// R4
export interface TimeGridPeriod { start: string; end: string }
export interface TimeGridBreak { after: number; name: string; minutes: number; splits_double: boolean }
export interface TimeGrid { id: string; name: string; builtin?: boolean; core_latest: number | null;
  periods: TimeGridPeriod[]; breaks: TimeGridBreak[] }
export interface TimelineRow { key: string; begin: string; end: string; label: string; period_label: string | null;
  gap_before: number }
// BreakDef += splits_double?;  Settings += period_ends?, site_travel_minutes?, long_gap_minutes?
// SchoolClass, SupervisionArea += time_grid?;  TimeRule, Absence += start?, end?
// TimetableView += layout?: 'periods' | 'timeline'; grid?: {id: string; name: string} | null; rows?: TimelineRow[]
// Cell += begin?, end?, row?, row_span?, period_label?, grid?;  BlockedSlot += begin?, end?;  MoveOption += row?
// Entry, EffectiveCell += end_time?, grid?;  ClassWeek += grid?, period_ends?, breaks?;  Monitor ohne period_times
```
Endpunkte in `api/endpoints.ts`: `calendar.schoolYear({date, class_id})`, `settings.calendarPreview(body, keep)`,
`classes.patch(id, body, {force})` (erweitert), R4 `timeGrids.list()`, `timeGrids.preview(body)`,
`classes.setTimeGrid(id, {grid, dry_run})`.

### 15.4 Lesepfad alter Daten (Beispiel vorher/nachher)
Vorher (heutiges Dokument, gekürzt):
```json
{"settings": {"days": 5, "periods": 10, "period_minutes": 45, "cycle_weeks": 2, "cycle_start": "2026-08-31",
              "period_times": ["07:55", "08:45", "09:50"], "breaks": [{"after": 1, "name": "1. große Pause", "minutes": 20}]},
 "classes":  [{"id": "10X", "max_periods_per_day": 8,
               "unavailable": [{"weeks": [0], "days": [2], "periods": [], "note": "Woche A: Berufsschule"}]}],
 "courses":  [{"id": "K7", "classes": ["10X"], "weeks": [1], "hours": 2}],
 "teachers": [{"id": "ZEH", "time_windows": [{"days": [0, 1, 2, 3, 4], "start": "10:00", "end": "17:00", "weeks": [0]}]}],
 "holidays": [{"id": "H1", "name": "Herbstferien (Beispiel)", "date_from": "2026-10-17", "date_to": "2026-10-31"},
              {"id": "H3", "name": "Tag der Deutschen Einheit", "date_from": "2026-10-03", "date_to": "2026-10-03"}],
 "duties":   [{"id": "D1", "area": "AUF1", "day": 0, "break_index": 0, "weeks": [1]}]}
```
Gelesen ab R3/R4 (nichts wird umgeschrieben):

| Angabe | gelesen als |
|---|---|
| Schuljahr | Beginn 31.08.2026 (aus `cycle_start`), 52 Wochen, Ende 29.08.2027 |
| 05.10.2026 | „Woche 6 · KW 41 · Zykluswoche 2 von 2“ (heute `week_of` = 1, „B“) |
| 19.10.2026 | Woche 8, Ferienwoche (Herbstferien Woche 8 und 9), Zykluswoche 2 |
| 10X | Zyklus der Schule, Unterrichtstage Mo–Fr, Raster „Standard“; Regel „Woche 1 · Mi“, die Notiz bleibt |
| K7, D1 | „Woche 2“ |
| ZEH | „Woche 1: Mo–Fr 10:00–17:00“ |
| H1, H3 | `kind` = `ferien` bzw. `feiertag` (V15) |
| Pausen (R4) | `splits_double` = true; Standard-Raster mit 45-Minuten-Stunden |
| ab 30.08.2027 | Woche 53 (Altdokument zählt weiter, W3), Warnung „Schuljahr abgelaufen“ |

Nach dem ersten Speichern kommen nur Felder mit Standardwert hinzu:
```json
{"settings": {"week_numbering": "school_year", "school_year_start": "", "school_year_history": [],
              "cycle_start_week": 1, "cycle_shifts": [], "school_days": [],
              "period_ends": [], "site_travel_minutes": 0, "long_gap_minutes": 0,
              "breaks": [{"after": 1, "name": "1. große Pause", "minutes": 20, "splits_double": true}]},
 "classes":  [{"id": "10X", "cycle_weeks": 0, "cycle_start_week": 1, "school_days": [], "time_grid": ""}],
 "holidays": [{"id": "H1", "kind": "ferien"}, {"id": "H3", "kind": "feiertag"}],
 "areas":    [{"id": "AUF1", "time_grid": ""}],
 "time_grids": []}
```
Danach `PUT /settings {"school_year_start": "2026-08-01"}` (Phasenerhalt als Standard): Es entstehen
`school_year_start = "2026-08-01"` und `cycle_start_week = 6`. Woche 1 ist jetzt 27.07.–02.08.2026, und der 05.10.2026
zeigt „Woche 11 · KW 41 · Zykluswoche 2 von 2“, also dieselbe Zykluswoche. `school_year_history` bleibt leer, weil es
eine Korrektur ist (W4). `cycle_start` bleibt im Dokument.

### 15.5 Texte der Oberfläche (verbindlich; Sie-Form, ohne Buchstaben, Hilfe nur an der Beschriftung)
| Ort | Element | Text | Hilfe |
|---|---|---|---|
| Planung › Zeitraster & Schuljahr | Abschnitt „Schuljahr“: Feld „Beginn“ | Datum | „Woche 1 ist die Woche mit diesem Tag. Ferienwochen zählen mit.“ |
| ebd. | Anzeige „Ende“ | „Sonntag, 25.07.2027 · 52 Wochen“ | „Ergibt sich aus dem Beginn des nächsten Schuljahres.“ |
| ebd. | Feld „Wochenzählung“ | „Ab Schuljahresbeginn“ / „Kalenderwoche“ | „Kalenderwoche: Woche = KW. Am Jahreswechsel kann der Zyklus springen.“ |
| ebd. | Abschnitt „Wochenzyklus“: Feld „Wochenzyklus“ | Zahl, Einheit „Wochen“ | „Anzahl unterschiedlicher Wochen. 1 = jede Woche gleich.“ |
| ebd. | Feld „Zyklusbeginn“ | „Woche [s]“ | „Laufende Woche, in der Zykluswoche 1 liegt.“ |
| ebd. | Kästchen „Zykluswochen beibehalten“ (an) | – | „Die heutige Zykluswoche bleibt, wenn Sie Beginn oder Zählung ändern.“ |
| ebd. | Liste „Verschiebungen“ | Spalten „Ab“, „Zykluswoche“, „Notiz“; Knopf „Verschiebung hinzufügen“ | an der Überschrift: „Ab der Woche des Datums gilt die gewählte Zykluswoche, z. B. nach Ferien.“ |
| ebd. | Feld „Unterrichtstage“ | Chips „Mo Di Mi Do Fr Sa So“ (`aria-label` „Montag“ …) | „Gilt für alle Klassen ohne eigene Unterrichtstage.“ |
| ebd. | Tabelle „Wochenübersicht“ | „Woche · KW · Zeitraum · Zykluswoche · Ferien“; Badge „Ferien“ bzw. Ferienname | – |
| ebd. | Warnungen | „Zykluswoche 53 kommt in diesem Schuljahr nicht vor.“ · „Woche 1: Zykluswoche 1 folgt auf Zykluswoche 1.“ · „KW 53 und KW 1 haben dieselbe Zykluswoche.“ · „Schuljahr abgelaufen. Tragen Sie den Beginn des neuen Schuljahres ein.“ | – |
| ebd. | Vorschau | Knopf „Wirkung anzeigen“; Zeile „Heute: Woche 6 · KW 41 · Zykluswoche 2 von 2 → Woche 11 · KW 41 · Zykluswoche 2 von 2“ | – |
| 409-Dialog | Titel, Knöpfe | „Änderungen durch den neuen Wochenzyklus“ bzw. „Änderungen durch das Zeitraster“; Liste „{label}: {before} → {after}“; „Trotzdem übernehmen“, „Abbrechen“ | – |
| Stammdaten › Ferien | Feld „Art“ | „Ferien“, „Feiertag“, „Beweglicher Ferientag“, „Unterrichtsfrei“ | – |
| Stammdaten › Klasse, Klassenkopf „Planung“ | Felder | „Unterrichtstage“: „Wie Schule (Mo–Fr)“ oder Chips; „Wochenzyklus“: „Wie Schule (2 Wochen)“ / „Eigener Zyklus“ mit „Wochen“ und „Zyklusbeginn“; Kopfzeile „Standard · Mo–Fr · 2 Wochen“, Knopf `aria-label` „Planung ändern“ | – |
| Meldung 403 | Klassen-Planungsfelder | „Für Zeitraster, Unterrichtstage und Wochenzyklus brauchen Sie das Recht „Stundenplan bearbeiten“.“ | – |
| WeekNav | Bedienung | Knöpfe `aria-label` „Vorherige Woche“, „Nächste Woche“; Knopf „Heute“; Auswahl (Beschriftung „Woche“, nur für Bildschirmleser) mit „Woche 10 · KW 45 · 02.11.–08.11.“ und „ · Ferien“; Anzeige `week_text` | – |
| WeekPatternInput | Modi | Beschriftung „Wochen“: „Jede Woche“ · „Bestimmte Wochen“ · „Rhythmus“; Chips „1 … N“ (`aria-label` „Woche 3“) | – |
| ebd. | Rhythmus | Felder „Abstand“ (Einheit „Wochen“), „Ab Woche“, „Bis Woche (optional)“; Vorschau „Woche 2, 5, 8 … (18 von 52)“; Hinweise „Muster wiederholt sich nicht gleichmäßig.“, ohne E6 „Im Wochenzyklus der Schule nicht möglich.“ | „Abstand“: „2 = jede zweite Woche.“ |
| `weeks.describe` | Text | „jede Woche“ · „Woche 1“ · „Woche 1–4, 9“ · „jede 3. Woche ab Woche 2“ · „jede 2. Woche ab Woche 10 bis Woche 30“ · „Woche 1 von 3“ | – |
| Meldungen 422 | Wochen | „Wochen: nur 1 bis {N} möglich.“ · „Rhythmus: Abstand 1 bis {N}.“ · „„Bis Woche“ liegt vor „Ab Woche“.“ · „Bitte entweder Wochen oder einen Rhythmus angeben.“ · „Bitte mindestens einen Tag oder eine Stunde wählen.“ (U-15) | – |
| Bericht, Klausur, Krankmeldung | Meldungen | „Kurs {label} liegt in keiner Woche seines Zyklus.“ · „Kein Unterrichtstag der Klasse.“ · „Kein Schultag (kein Unterrichtstag oder Ferien).“ | – |
| Konflikt, Generator | Meldungen | „Lehrkraft {T} doppelt belegt: Mo 08:45–09:30, Woche 1 und jede 6. Woche.“ · „Viele unterschiedliche Wochen ({V}). Erhöhen Sie die Rechenzeit oder tragen Sie Blockphasen als Abwesenheit ein.“ | – |
| Stundenplan, Druck, Klassen-Wochenplan | Anzeige | Zellendetail „Wochen“: `weeks_text`; Schalter „Ganze Woche“; Kopf eines freien Tags „Kein Unterricht“; Drucktitel „Stundenplan Klasse 5a – Woche 10 · KW 45“; Wochenplan „Woche 6 · KW 41 · 05.10.–11.10.2026 · Zykluswoche 2 von 2“ | – |
| Export | Texte | iCal DESCRIPTION „Zykluswoche 2 von 2“ (nur N > 1); CSV „Wochen“ = „1,3“ bzw. „1-4,9“; LIESMICH „Wochenzyklus: 2 Wochen (Woche 1 … 2)“ | – |
| R4 Planung › Zeitraster | Liste, Knöpfe | „Standard“ mit Badge „Schulvorgabe“; „Zeitraster anlegen“, „Bearbeiten“, „Löschen“ | – |
| R4 Zeitraster-Editor | Felder | „Name“, „Beginn“, „Stundenlänge“ (Einheit „min“), „Stunden“; Knopf „Zeiten berechnen“; Tabelle „Stunde · Beginn · Ende“; Pausen „Nach Stunde · Name · Dauer“, Kästchen „Trennt Doppelstunden“; „Hauptfächer bis Stunde“ | „Trennt Doppelstunden“: „Keine Doppelstunde über diese Pause.“ |
| R4 Prüfung | Meldungen | „Stunde {i}: Ende liegt vor dem Beginn.“ · „Stunde {i+1} beginnt vor dem Ende von Stunde {i}.“ · „Pause „{name}“ ist länger als der Abstand der Stunden.“ · „Pause „{name}“ liegt nach der letzten Stunde.“ · „Höchstens 16 Stunden.“ · „Uhrzeit im Format HH:MM.“ · „Zeitraster „{name}“ wird noch verwendet.“ | – |
| R4 Klasse | Feld, Dialog | „Zeitraster“: „Standard“ bzw. Name; Dialog „Zeitraster wechseln“: „{n} Stunden übernommen, {m} ohne passende Stunde“, Knöpfe „Wechseln“, „Abbrechen“; danach bei Bedarf Hinweis „Stundenplan der Klasse neu planen.“ mit Knopf „Neu planen“; „Unterricht bis Stunde“ | „Unterricht bis Stunde“: „Späteste Stunde des Tages im Zeitraster der Klasse.“ |
| R4 Einstellungen | Felder | „Wegezeit“ (Einheit „min“), „Lange Lücke“ (Einheit „min“) | „Zeit zwischen Unterricht an verschiedenen Standorten. 0 = wie bisher in Stunden.“ · „Längere Lücken zählen höchstens so lang als Springstunden. 0 = aus.“ |
| R4 Lehrkraft-Sperre | RuleEditor | Umschalter „Stunden“ · „Uhrzeit“; Felder „Von“, „Bis“ | – |
| R4 Zeitachse | Anzeige | Zeilen „07:55–08:40“; Lückenzeile „13:15–16:00“ (`aria-label` „Unterrichtsfrei 13:15–16:00“); Zelle „M · ABK · 1. Std.“; Vertretung und Monitor „16:00–16:45“ | – |

### 15.6 Reihenfolge, Gates und was dazwischen grün bleibt
| Schritt | Wer | Inhalt | grün bzw. vorhanden am Ende |
|---|---|---|---|
| G0 vor R3 | Hauptsitzung | R2 integriert; Lead bestätigt E1, E4–E7; Backlog B-11 (V4), B-25/B-45 (V5), B-12 (P1) und OFFENE-PUNKTE §3.2 (P4) angepasst | `ruff check .`, `python -m pytest -q`, `npm run lint`, `npx vitest run` |
| R3-A1 (0) | R3-A1 | Fixture T0 aus dem Stand G0, bevor Code geändert wird | Fixture im Repo, Test liest sie |
| R3-A1 (1) | R3-A1 | `tests/data/weeks_cases.json` zuerst, dann `weeks.py`, `calendar_utils` | `test_weeks.py` |
| R3-A2 (1) | R3-A2 | Typen (§15.3, optional), `lib/weeks.ts` gegen `weeks_cases.json`, `lib/dates.ts` kompatibel (V16) | lint, vitest |
| R3-A1 (2)–(4) | R3-A1 | Felder und Prüfung; Engine, Bericht, Ansichten; Generator mit `iterations` (V1), Aufsichten | nach (4) komplette Suite (P6 a) |
| R3-A1 (5) | R3-A1 | Schnittstellen; danach AGENT_NOTES „Vertrag R3 steht“ | Suite der Integrationen |
| R3-A2 (2)–(5) | R3-A2 | WeekNav, Muster-Editor, `CalendarPanel` (V4), Klassenzeile (V12), Seiten; Browser-Rundgang erst nach „Vertrag R3 steht“ | lint, vitest je Schritt |
| R3-D-Zusatz | R3-D | `week_text` und 7 Tage auf Startseite und Monitor (P1), erst nach R3-A2 (1) und „Vertrag R3 steht“ | lint, vitest |
| R3-A1 (6), (7) | R3-A1 | Demo und Doku; Schritt 7 nach Integration von R3-B (V3) | komplette Suite |
| G1 Ende R3 | Prüf-Agent, Hauptsitzung | Abnahme R3 (§12, §14.7, §15.7); Fixture T0b (Stand R3) für R4-A1 Nr. 11 | Suite, lint, vitest, T3 leer bis auf Liste, T0 grün, `scripts/preview.sh` startet, Rundgang, Doku 01/03–09 und OFFENE-PUNKTE |
| R4 | wie R3 | R4-A1 (1)–(6) nach §11.1; R4-A2 erst nach „Vertrag R4 steht“ im Browser; `features_channels.py` unberührt (P3) | wie R3 |
| G2 Ende R4 | Prüf-Agent, Hauptsitzung | Abnahme R4; BETRIEB.md zum Downgrade (Z11); Revision `00xx_period_grid` nur, wenn reserviert | wie G1 |

Zwischen den Runden bleiben gültig: alte Links (`?woche=`, `?week=`), alte Dokumente, Backups und Versionen, die
Demo-Konten (VORSCHAU.md) und die Zahl der Tests. Tests werden umgeschrieben, nicht gelöscht.

### 15.7 Abnahme: Präzisierungen und Testzuordnung
- **T0 Altdokument-Fixture** (vor R3, R3-A1 Schritt 0).
  - Dateien: `tests/fixtures/school_r2.json` (kleine Demo `classes_per_grade=2`, `assign_teachers`, `generate` mit
    `seed=3`, als Dokument samt Stunden gespeichert) und `tests/fixtures/expected_r2.json`.
  - Inhalt von `expected_r2.json`:
    - `week_of` für −400 … 800 Tage;
    - `validate_school().stats`;
    - `compute_day_plan` für 2026-10-05, 2026-10-06, 2026-10-19, 2026-10-24 und 2027-01-11;
    - `timetable_view` für eine Klasse, eine Lehrkraft und einen Raum in Woche 0 und 1;
    - iCal-UIDs einer Lehrkraft;
    - CSV-Export von Stunden und Klassen;
    - GPU002/GPU014.
  - Gewollte Unterschiede listet der Test ausdrücklich: Buchstabe → Ziffer (A → 1, B → 2) in Labels und Texten,
    `days` mit 7 Einträgen, neue Felder. Alles andere muss gleich bleiben.
- **R3-A1 Nr. 1, zweiter Fall:** gilt **bei Beginn 31.08.2026**. Bei Beginn 26.08. ist der 11.01.2027 Woche 21, nicht
  20 (q_pruef2.out).
- **T3 statt R3-A1 Nr. 3 (Grep) und R3-A2 Nr. 6:**
  - Suchbefehl: `rg -n -e 'A/B' -e 'Woche [A-Z]\b' -e '\b[A-Z]-Woche' -e 'chr\((65|ord\("A"\))' -e 'fromCharCode\(65'
    schulmanager frontend/src docs/DESIGN.md docs/beispielschulen`.
  - Erlaubt sind nur die Altformat-Leser (`untis_gpu._WEEK_RE`, CSV-Import in `csv_io.py`) und Tests mit
    „altformat“ im Namen.
  - Umsetzung als `tests/test_weeks.py::test_keine_wochenbuchstaben` (liest die Dateien) und
    `lib/__tests__/noWeekLetters.test.ts`.
  - Der API-Test prüft `week_label` gegen `^\d*$` und alle Texte gegen `Woche [A-Z]\b`.
- **R3-A1 Nr. 10 / R4-A1 Nr. 11:**
  - Vergleiche nur mit `iterations=20000` (V1) und auf T0 bzw. T0b, nicht mit `demo_school`.
  - Langsame Fälle markiert das Testmodul mit
    `pytest.mark.skipif(os.environ.get("SM_SLOW") != "1", …)`, weil der Marker `slow` nicht registriert ist
    (pyproject.toml:33-37).
  - Der Prüf-Agent startet sie mit `SM_SLOW=1 python -m pytest -q tests/test_weeks_solver.py`.
  - Die Varianten liest der Test aus `Scheduler.variants` (Liste mit Wochen und Gewicht).
- **R4-A1 Nr. 3:** Die Lücke Vormittag–Abend von SPT zählt höchstens 2, mit `long_gap_minutes = 0` 3 (V2). Der Satz
  „zählt nicht“ entfällt.
- **R4-A1 Nr. 11** zusätzlich: `teacher_gaps` von T0b bleibt gleich (V2).
- **R3-A2 Nr. 1:** Die gemeinsame Tabelle ist `tests/data/weeks_cases.json`; vitest liest sie mit
  `fs.readFileSync(new URL('../../../../tests/data/weeks_cases.json', import.meta.url))`.
- **„390 px ohne waagerechtes Scrollen“** heißt im Browser-Test `document.documentElement.scrollWidth <=
  window.innerWidth`. Gemessen wird in Stundenplan, Einstellungen, Muster-Editor mit N = 52, WeekNav und Zeitachse.
- **Neue Fälle:**

| Nr. | Kriterium | Test (Vorschlag) | Messgröße |
|---|---|---|---|
| T7 | 7 Spalten-Regel (V10) | `test_weeks.py::test_spalten` | Klasse Mo–Fr: 5 Spalten; Sa-Klasse: 6; Sonntagsstunde: 7; `all_days=1`: 7 |
| T9 | offene Anträge (V9) | `test_teacher_profile.py::test_antrag_nach_zykluswechsel` | 2 → 4 exakt umgerechnet; 2 → 3 gibt 409 |
| T10 | 403 und 409 an der Klasse (V12, V13) | `test_classes.py::test_planungsfelder` | Sekretariat 403; Planung 409 ohne `?force=1`, 200 mit |
| T11 | Raster ändern (V8) | `test_timegrid.py::test_raster_kuerzen` | 409 `grid_change` mit Liste; nach `force` Bericht „außerhalb des Zeitrasters“ |
| T12 | freie Längen im Standard (V7) | `test_timegrid.py::test_standard_period_ends` | 08:00–09:00, 09:05–09:50 gespeichert; Ende aus `period_ends` |
| T13 | Ferienart beim Lesen (V15) | `test_weeks.py::test_holiday_kind_lesepfad` | „Herbstferien (Beispiel)“ → `ferien`; „Tag der Deutschen Einheit“ → `feiertag` |
| T14 | Phasenwahl (V14) | `test_weeks.py::test_phasenerhalt` | Altdokument → Beginn 01.08.2026 ergibt s = 6; Wechsel auf `iso` hält die Zykluswoche von heute |
| T15 | Rhythmus (E6, falls bestätigt) | `test_weeks.py::test_rhythm` | N = 1, `every = 2`, `from_week = 10`: aktiv in Woche 10, 12, …; nicht in 1–9 und 11 |

### 15.8 Entscheidungen (zusätzlich zu §13 und §14.7)
- **E6 Rhythmus unabhängig vom Schulzyklus** für Lehrkraft-Regeln, Zeitfenster und Aufsichten (V6). Empfehlung: **ja**,
  sonst sind „jede 3. Woche“ und „alle 2 Wochen ab Woche 10“ nur mit passendem Schulzyklus möglich.
- **E7 Anzeige der Zykluswoche** neben der laufenden Woche: Empfehlung **„Zykluswoche k von N“** (G3). Der Lead hatte
  „nur als Zahl ‚Woche k‘“ festgelegt.
- **Für den Lead:** Backlog anpassen (B-11 Zeilen, B-25 Rest, B-45 entfällt, B-12 Zusatz). R3-B über Schritt 7
  informieren (V3).

## 16. Entscheidungen des Leads (11.10., Gate G0)

Getroffen nach den Wünschen des Auftraggebers vom 11.10.; der Auftraggeber kann jede davon ändern. §16 geht §13,
§14.7 und §15.8 vor.

- **E1 Woche 1** = die Woche (Mo–So), in der der Schuljahresbeginn liegt; Standard 1. August, in „Zeitraster &
  Schuljahr“ änderbar. Alle Wochen des Schuljahres zählen durch (auch Ferien). Die Zyklusphase alter Daten bleibt über
  `cycle_start_week` erhalten (§14.1).
- **E2 Sa/So**: In Daten, Navigation und Kalender hat jede Woche 7 Tage. Wochenansichten zeigen **standardmäßig Mo–So**
  (Wunsch „alle Wochen sollen 7 Tage haben“); Sa/So ohne Unterricht der Klasse sind schmal und abgeblendet
  (`day_kind = kein_unterrichtstag`). Der Schalter „Nur Unterrichtstage“ blendet leere Tage aus und merkt sich die Wahl
  je Gerät. Damit gilt in V10 standardmäßig n = 7; mit „Nur Unterrichtstage“ die Formel aus V10.
- **E3** Ein Zeitraster je Klasse (kein Raster je Wochentag); später ohne Bruch nachrüstbar.
- **E4** Kopplung über Klassen mit verschiedenen Rastern ist erlaubt, wenn alle Stunden des Blocks in allen Rastern
  deckungsgleich sind; sonst 422.
- **E5** Deputat und Stundentafel zählen je Stunde 1, unabhängig von der Länge.
- **E6** Ja: Lehrkraft-Regeln, Zeitfenster und Aufsichten bekommen einen eigenen Rhythmus in laufenden Wochen
  (`rhythm {every, from_week, to_week}`), unabhängig vom Schulzyklus (V6).
- **E7** Anzeige „Woche 12 · KW 45“ und – nur wenn 1 < N < Wochen des Schuljahres – zusätzlich „Zykluswoche 3 von 6“.
- **Pakete Runde 3**: R3-A1 (Backend) und R3-A2 (Oberfläche) zuerst; R3-B (B-07) nach R3-A1 – Schritt 7 aus V3 macht
  daher R3-A1 selbst, R3-B passt sich an; R3-D (B-12 mit Zusatz P1) nach R3-A2.
