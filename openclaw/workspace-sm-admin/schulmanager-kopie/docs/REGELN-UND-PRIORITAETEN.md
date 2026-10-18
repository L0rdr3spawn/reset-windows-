# Regeln und Prioritäten der Stundenplan-Optimierung

Stand: 13.10.2026. Betrifft Planung → Tab **„Regeln“** (`/planung/regeln`), Backend `schulmanager/rules.py`,
Route `server/routes/features_rules.py`, Frontend `pages/planning/rules/*`. Dazu: klassenbezogene Einstellungen
(Klassenarbeiten je Woche/Tag) mit Vererbung Schule → Jahrgang → Klasse.

## 1. Was vorher schlecht war

* Zehn nackte Zahlen („class_gap = 100“, „position = 0,6“) mit Schiebereglern, deren Maximum (50/300) feste
  Werte abschnitt; niemand außer dem Entwickler wusste, was „6“ bei „Hauptfächer nicht spät“ bedeutet (B-10).
* Alles galt pauschal für die ganze Schule: Hohlstunden in der Oberstufe wurden genauso bestraft wie in Klasse 5;
  eine Grundschule sah Standortwechsel und Lehrerwünsche, die sie gar nicht hat.
* Der Tab mischte vier fremde Themen (Optimierung, Vertretung, Lehrer-Selbstverwaltung, Krankmeldungen/Atteste)
  (B-11, B-31). Keine Rückmeldung, was eine Einstellung bewirkt; keine Vorschau; nichts exportierbar.
* Klausur-Höchstzahlen lagen unter „Zeitraster & Schuljahr → Schule“ (B-31/B-41), obwohl sie je Klasse gelten.

## 2. Konzept

### 2.1 Bausteine statt Zahlen

Jede weiche Regel ist ein **Baustein** mit Titel, Erklärung und **Wichtigkeit**:

| Stufe | Faktor auf das Grundgewicht | Bedeutung |
|---|---|---|
| Aus | 0 | wird nicht beachtet |
| Nett | ¼ | zählt wenig |
| Wichtig | 1 | normales Gewicht = bisheriger Standardwert |
| Sehr wichtig | 4 | |
| Muss | 20 | praktisch hart; bei „Hauptfächer früh am Tag“ echte harte Regel im Generator |

Das Grundgewicht (`RuleDef.base`) ist je Baustein der bisherige Standardwert (`Weights`-Defaults). Die Zahlen bleiben
die Wahrheit für den Generator: `rules.apply_to_settings` schreibt aus den Bausteinen `settings.weights`,
`core_latest_period`, `site_travel_periods`, `prefer_doubles`, `double_alignment`, `auto_replan`;
`rules.sync_from_numbers` geht den umgekehrten Weg, wenn eine ältere Oberfläche oder API nur Zahlen setzt.
Unter „Erweitert“ bleibt je Baustein ein **eigener Zahlenwert** möglich (Feinsteuerung, verlustfrei für alte
Werte, die keiner Stufe entsprechen).

Katalog (`rules.RULES`), gruppiert:

* **Für die Schülerinnen und Schüler**: Keine Hohlstunden für Klassen · Unterricht beginnt zur ersten Stunde ·
  Gleichmäßig lange Schultage · Hauptfächer früh am Tag (Parameter „spätestens bis Stunde“; nur wenn ein Fach als
  Hauptfach markiert ist)
* **Unterricht und Fächer**: Fächer über die Woche verteilen · Doppelstunden als Block (Parameter: alle Fächer ab
  2 Wochenstunden, Lage in Pausenblöcken) · Unterricht möglichst früh am Tag (Feinsteuerung, nur „Erweitert“)
* **Für die Lehrkräfte**: Wenige Springstunden · Wünsche der Lehrkräfte berücksichtigen (nur wenn Wünsche vorliegen)
  · Standortwechsel vermeiden (Parameter Wegezeit; nur bei mehr als einem Standort)
* **Automatik**: Nach Änderungen automatisch neu planen (Schalter)

Dazu eine Karte **„Gilt immer (harte Regeln)“** mit Links zu den Daten (Sperrzeiten/Unterrichtstage/Höchststunden
je Klasse, Sperrzeiten/Arbeitszeiten/Deputat je Lehrkraft, Fachräume, Blöcke eines Fachs pro Tag, Wegezeit) und der
Zahl der Einträge mit eigenen Angaben.

### 2.2 Schulart als Vorlage – nur zeigen, was die Schule braucht

Beim ersten Öffnen wählt die Schule eine **Vorlage** (`rules.TEMPLATES`): Allgemein, Grundschule, Gymnasium/Oberstufe,
Gesamtschule, Berufsschule/Blockunterricht, Förderschule, Montessori/offen, Abendschule, Ganztag. Eine Vorlage bringt
Stufen, Parameter und Ausnahmen mit (z. B. Gymnasium: Hohlstunden „Sehr wichtig“, Ausnahme Jahrgang 11–13 „Nett“)
und eine Liste `show`, welche Bausteine sie ohne „Erweitert“ zeigt (Berufsschule sieht keine „erste Stunde“-Regel,
Abendschule keine „früh am Tag“-Regel).

Sichtbar ist ein Baustein, wenn (a) er **Datenbezug** hat (`RuleDef.requires`: Standorte > 1, Hauptfächer, Wünsche)
und (b) die Vorlage ihn zeigt **oder** die Schule ihn gegenüber der Vorlage verändert hat. **„Erweitert“** zeigt alles
(auch Bausteine ohne Datenbezug mit dem Hinweis warum, und die Zahlenwerte). Kein Feature fällt weg.

Vorlagen sind **Daten**: Export als JSON (`GET /settings/rules/export`, im Frontend auch ohne Server-Roundtrip),
Import (`PUT /settings/rules` mit dem Inhalt), **eigene Vorlage sichern** (`POST /settings/rules/templates`, gespeichert
in `settings.rules.templates`, löschbar).

### 2.3 Gültigkeit und Wochen (Ausnahmen)

Jeder Baustein kann **Ausnahmen** haben: `{level, grades, classes, subjects, teachers, weeks, rhythm, params, note}`.
Welche Dimensionen möglich sind, sagt `RuleDef.scope` (Klassenregeln: Jahrgänge/Klassen; Kursregeln zusätzlich Fächer;
Lehrkraftregeln: Lehrkräfte). Wochen wie überall: jede Woche, ausgewählte Wochen oder Rhythmus
(`WeekPatternInput`). Mehrere Ausnahmen gelten der Reihe nach, die letzte passende gewinnt. Bei „Hauptfächer früh am
Tag“ darf die Ausnahme auch den Parameter „spätestens bis Stunde“ ändern (Grundschule bis 4., Oberstufe bis 8.).

Generator (`scheduler.py`): `rules.PlanWeights` liefert je Klasse/Lehrkraft/Kurs und **Wochenvariante** die
wirksamen Gewichte (`class_w`, `teacher_w`, `course_w`). Ausnahmen mit Wochenangabe werden in `_variants` als eigene
Wochenmengen aufgenommen, sodass die Varianten sauber entlang der Ausnahmen geschnitten werden; gilt eine Ausnahme nur
in einem Teil der Wochen einer Variante, wirkt sie anteilig. „Muss“ bei Hauptfächern ist in `check()` hart.
Qualitätsbericht (`timetable.validate_school`) zählt „Hauptfächer spät“ mit der je Kurs gültigen Stunde
(`rules.core_latest_for`).

### 2.4 Wirkung sichtbar, Vorher/Nachher

`GET /settings/rules` liefert je Baustein `affects`/`affects_text` („betrifft 12 Klassen“) und `violations`
(aktuelle Verstöße im gültigen Plan: Hohl-/Springstunden, Standortwechsel, späte Hauptfächer aus dem Qualitätsbericht;
später Beginn, Fach an Folgetagen, zerlegte Doppelstunden, Treffer in Wunschzeiten gezählt in `rules.violations`) mit
Link in den Qualitätsbericht (`/planung/bericht?detail=class_gaps` öffnet die Liste hinter der Kachel).

**Probelauf**: `POST /planning/generate` mit `rules` (Entwurf) rechnet einen Generatorlauf mit diesen Regeln, ohne die
Einstellungen zu ändern (`params.rules_preview = true`). Der Tab „Regeln“ zeigt die Kennzahlen aktuell ↔ Entwurf
(unverplant, Hohl-/Springstunden, Hauptfächer spät, Standortwechsel). Nichts wird automatisch übernommen; der
Entwurf liegt wie jeder Lauf im Tab „Generator“, der auf den Probelauf hinweist.

### 2.5 Migration

Keine Datenbank-Migration nötig: Das Planungsdokument ist ein JSON-Blob (`store.encode_school`). `Settings.rules` ist
neu und standardmäßig leer; `rules.resolve` leitet fehlende Bausteine aus den Zahlen ab (`derive_from_numbers`):
Gewicht 0 → Aus, exaktes Vielfaches → Stufe, sonst nächste Stufe **plus eigener Wert** (verlustfrei). Dokumente ohne
Bausteine gelten als Vorlage „standard“. Alte Clients, die `PUT /settings` mit `weights` senden, funktionieren weiter;
die Bausteine folgen (`sync_from_numbers`), Ausnahmen bleiben erhalten.

## 3. Klassenbezogene Einstellungen (Aufgabe 2)

Verlegt: **Max. Klassenarbeiten je Woche / je Tag**. Modell:

* `Settings.max_exams_per_week/-day` = **Vorgabe der Schule** (bleibt, Altwerte gelten weiter).
* `Settings.exam_limits_by_grade = {"5": {"per_week": 2, "per_day": 1}}` = Vorgabe je **Jahrgang** (optional je Wert).
* `SchoolClass.max_exams_per_week/-day = None | int` = eigener Wert der **Klasse** (`None` = erbt).
* `rules.exam_limits_for_class(school, cls)` löst Klasse → Jahrgang → Schule auf und nennt die Quelle;
  `exams.check_exam` nutzt die Klassenwerte.

Oberfläche: Vorgaben (Schule, je Jahrgang mit Tabelle aller vorhandenen Jahrgänge, Spalte „Klassen mit eigenen
Werten“) auf der Seite **Klausuren** (`components/ExamLimits.tsx`, Recht `settings.edit`); Klassen-Editor in
**Stammdaten → Klassen** (Feld „Klassenarbeiten / Klausuren“: „Wie Vorgabe (Jahrgang 7: 2 je Woche, 1 je Tag)“ oder
eigene Werte, Spalte „Klausuren“) und **Klassen-Seite → Kopf** (Zeile „Klassenarbeiten“ mit wirksamen Werten und
Quelle, Ändern mit `masterdata.edit`; `PATCH /classes/{id}` mit `max_exams_per_week/day` oder
`exam_limits_inherit: true`). Unter „Zeitraster & Schuljahr“ steht nur noch ein Verweis.

Geprüft und (noch) nicht verlegt: `policy.cancel_min_grade` („Entfall erlaubt ab Klassenstufe“, Vertretung – ist
schon jahrgangsbezogen, eine Klassenausnahme wäre sinnvoll, gehört aber zur Vertretungsarbeit),
`absence_limit_percent` (Fehlzeitgrenze – je Jahrgang denkbar), `core_latest_period` (jetzt über Ausnahmen je
Jahrgang/Klasse/Fach abgedeckt), `max_periods_per_day`/`school_days`/Sperrzeiten (waren schon je Klasse).

## 4. Datei-Übersicht

| Bereich | Dateien |
|---|---|
| Katalog, Vorlagen, Stufen, Gültigkeiten, Wirkung, Klausurgrenzen | `schulmanager/rules.py` |
| Modell | `models.py` (`Settings.rules`, `Settings.exam_limits_by_grade`, `SchoolClass.max_exams_per_*`) |
| Generator / Bericht / Klausuren | `scheduler.py` (`class_w`, `teacher_w`, `course_w`, harte Hauptfachregel), `timetable.py`, `exams.py` |
| API | `routes/features_rules.py` (`/settings/rules*`), `features_data.py` (`SettingsIn.rules`, `exam_limits_by_grade`, Sync, Klassenprüfung), `features_classes.py` (`PATCH` + `exam_limits`), `features_planning.py` (`GenerateIn.rules`) |
| Frontend | `pages/planning/rules/{model.ts,api.ts,RulesPanel.tsx,RuleCard.tsx,LevelPicker.tsx,OverrideEditor.tsx,ProfilePicker.tsx,Simulation.tsx,rules.css}`, `components/ExamLimits.tsx`, Edits in `PlanningPage.tsx` (Tabs „Regeln“ / „Vertretung & Abwesenheit“), `SettingsPanels.tsx`, `CalendarPanel.tsx`, `ReportTiles.tsx` (`initialOpen`), `GeneratorPanel.tsx`, `MasterDataPage.tsx`, `features/classes/ClassHeader.tsx`, `ExamsPage.tsx` |
| Tests | `tests/test_rules.py`, `frontend/src/pages/planning/rules/rules.test.ts` |

## 5. Offen / Ideen

* Weitere Bausteine, die der Generator heute nicht kennt (Tageszeit-Anker, Blocklänge 3, „Fach X nie nach Fach Y“,
  Stundensoll je Zyklus – W-01/W-02/W-14/W-15 in `MONTESSORI-UND-WERKZEUGE.md`): Der Katalog ist dafür vorbereitet
  (`RuleDef` + `PlanWeights`), die Bewertung im Scheduler fehlt.
* Wegezeit je Standortpaar (Minuten) steht noch im Tab „Vertretung & Abwesenheit“ (parallele Arbeit eines anderen
  Agenten); gehört fachlich zum Baustein „Standortwechsel vermeiden“.
* Vertretungsregeln an den Ort der Wirkung (Vertretungsseite, B-25) – unverändert gelassen.
* `violations` für „Gleichmäßig lange Schultage“ und „früh am Tag“ sind nicht als Zählwert darstellbar (Kosten statt
  Verstöße) – bewusst ohne Zahl.
