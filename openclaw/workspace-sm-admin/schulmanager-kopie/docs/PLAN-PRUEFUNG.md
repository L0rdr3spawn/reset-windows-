# Plan prüfen – Dauerprüfung, Vorschlagspakete, Entscheidung

Stand 13.10.2026. Zielbild des Auftraggebers: Der Stundenplan wird **dauernd und automatisch** auf Probleme geprüft. Ändert
sich etwas (Lehrkraft ändert Sperrzeiten, wird krank, Raum fällt aus, Kurs/Stundentafel wird geändert …), berechnet das
System **mehrere Lösungen** und legt sie den **zuständigen Personen** zur Auswahl vor. Menschen entscheiden („Wir nehmen
diesen Plan“) – es gibt kein „das hat die KI so entschieden“. Der Generator bleibt für den Neuaufbau zum Schuljahr.

## 1. Ablauf

```
Änderung (mutate → Event change)
  └─ server/autoplan.py  AutoPlanner (entprellt SM_AUTOPLAN_DELAY, eigener Thread, blockiert keine Anfrage)
       ├─ autoplan.prepare_repair / find_problems      Probleme im regulären Plan
       ├─ keine Probleme            → offene Pakete „erledigt“, Status „Plan in Ordnung“
       ├─ Stand schon vorgeschlagen → nichts (state_hash gleich)
       ├─ sonst: ältere Pakete „ersetzt“, neues Paket (Status „berechnung“)
       │     └─ server/proposals.py  Builder: je Variante ein Generator-Job (kind="proposal", nacheinander)
       └─ Paket „offen“  → Live-Ereignis change{scope:["proposals"]} → Badge, Toast, Startseiten-Kachel
Entscheidung (Recht timetable.generate, timetable.edit oder settings.edit)
  ├─ „Diesen Plan nehmen“  → accept: nur wenn state_hash unverändert, sonst „veraltet“ + Neuberechnung
  ├─ „Verwerfen“           → Problemlage wird erst nach der nächsten Änderung wieder vorgeschlagen
  └─ „Später“              → 24 h (1–336 h) aus Zähler/Kachel ausgeblendet, Paket bleibt offen
```

Auslöser sind die Scopes `teachers, rooms, classes, courses, curricula, subjects, settings, sites, lessons, timetable,
import` (`autoplan.TRIGGER_SCOPES`). Eigene Änderungen (`autoplan`, `proposals`) und „Rückgängig/Wiederherstellen“ lösen
keine Prüfung aus. Krankmeldungen, Raumsperren und Klassenfahrten **ändern den regulären Plan nicht**; dafür berechnet die
Vertretungs-Engine den Tagesplan sofort selbst. „Lehrkraft meldet: ab nächster Woche mittwochs nicht“ ist dagegen eine
Sperrzeit mit „gilt ab“ (`TimeRule.valid_from`) – nach Genehmigung ergibt sich daraus ein Paket.

## 2. Das Vorschlagspaket

| Variante (`key`) | Inhalt |
|---|---|
| `minimal` | nur die Kurse mit Problemen werden neu gelegt, alles andere bleibt (fixiert samt Räumen) |
| `lokal` | zusätzlich alle Kurse der beteiligten Klassen und Lehrkräfte (`autoplan.expand_courses`), 1,5 × Rechenzeit |
| `gruendlich` | größerer Teilbereich (zweite Erweiterung, höchstens doppelt so groß wie `lokal`, sonst gleicher Umfang), 3 × Rechenzeit, anderer Startwert |
| `vertretung` | „Vertretung statt Planänderung“: Plan bleibt, die betroffenen Stunden werden vertreten – nur, wenn **alle** Probleme fehlende Lehrkräfte (Sperrzeit/Standort) sind |
| `raeume` | nur Raumwechsel/verwaiste Stunden entfernen (kein Generator, sofort fertig) |

Je Variante: Kurzbeschreibung, Kennzahlen **vorher/nachher** (`plan_proposals.metrics`: Probleme, Konflikte, unverplante
Stunden, Hohl-/Springstunden, Standortwechsel, späte Hauptfächer und die Regel-Bausteine `late_start`, `spread`,
`doubles`, `teacher_wish` aus `rules.violations`), Änderungsliste je Kurs (von → nach, Raumwechsel), betroffene Klassen und
Lehrkräfte, danach noch offene Probleme, „gilt ab“-Hinweis (kleinstes `valid_from` der beteiligten Sperrzeiten) und der
**Stundenplan-Entwurf** (`/planung/vorschlaege/<Paket>/<Variante>`: Klassen-/Lehrkraftplan Entwurf ↔ aktuell, nichts wird
gespeichert). Varianten ohne Verbesserung (nicht weniger Probleme oder mehr Konflikte) und doppelte Ergebnisse werden
verworfen; bleibt keine übrig, ist das Paket „fehlgeschlagen“ (Status „Keine bessere Lösung“). Die Oberfläche nennt
sachliche Hinweise („wenigste Änderungen“, „beste Qualität“), spricht aber **keine Empfehlung** aus.

### Veraltet und Ersetzen
`state_hash` = Fingerabdruck der **Stunden** (ID, Kurs, Lage, Wochen, Räume, Fixierung) **und** der Problemlage. Er
ändert sich bei jeder Planänderung und bei Änderungen, die Probleme verschieben (Sperrzeit, Raum, Kurs …), **nicht** bei
Krankmeldungen, Vertretungsentscheidungen oder Texten. Ein neues Paket ersetzt alle offenen mit anderem Stand
(Status `ersetzt`, laufende Berechnung wird abgebrochen). `accept` prüft den Hash ein zweites Mal **innerhalb** der
Transaktion (`store.mutate`) und bricht ab, wenn die Übernahme neue Konflikte oder mehr Probleme als berechnet erzeugen würde.

### Übernahme
`plan_proposals.apply_diff` ersetzt/entfernt nur die Stunden der Variante (`diff = {upsert, delete}`) und löscht
Tagesentscheidungen zu verlegten Stunden. Die Übernahme ist eine normale Version (Meldung „Plan-Vorschlag angenommen: …“,
Scope `timetable`, `autoplan`, `proposals`, Aktion `plan.proposal_accept`) – **rückgängig über „Verlauf & Audit“**.
Danach werden alle anderen offenen Pakete `ersetzt`, die Prüfung läuft erneut (Rest-Probleme → neues Paket). Betroffene
Lehrkräfte werden informiert: E-Mail im Ausgang (`notify`, nur bei SMTP und hinterlegter Adresse) und Live-Ereignis
`plan_proposal_applied` an ihre Konten; die Namen der Informierten stehen im Paket (`informed`).

### „Vertretung statt Planänderung“
Die Annahme ändert den Plan nicht; sie wird im Paket festgehalten. Dieselbe Problemlage (`signature`) wird danach nicht
mehr vorgeschlagen (Status der Prüfung „covered“), bis sie sich ändert.

## 3. Einstellungen (je Schule)

| Feld | Standard | Wirkung |
|---|---|---|
| `auto_replan` | an | Dauerprüfung insgesamt (aus: nur Status „ausgeschaltet“) |
| `plan_auto_apply` | `aus` | `raeume`: **reine Raumänderungen** und das Entfernen verwaister Stunden werden ohne Rückfrage übernommen (Version `timetable`+`autoplan`, rückgängig möglich). Alles andere bleibt Entscheidung. |
| `substitution_confirm` | aus | Bestätigungsmodus der Vertretung (siehe 5) |

Global abschaltbar: `SM_AUTOPLAN=0`; `SM_AUTOPLAN_DELAY` (Ruhezeit, Standard 3 s), `SM_AUTOPLAN_TIME_LIMIT` (Basis der
Rechenzeit je Variante, Standard 15 s; Faktoren 1 / 1,5 / 3).

## 4. Datenmodell (Alembic `0035_plan_proposals`, Kopf nach `0034_teacher_requests_kind`)

* `plan_proposals` – Paket: `status` (berechnung, offen, angenommen, verworfen, ersetzt, erledigt, veraltet,
  fehlgeschlagen), `base_version`, `state_hash`, `signature`, `title`, `reasons`, `trigger_scope`, `problem_count`,
  `valid_from`, `postponed_until/by`, Entscheidung (`decided_at/by/by_id`, `decision_note`, `chosen_variant_id`,
  `applied_version`, `informed`).
* `plan_proposal_variants` – Variante: `key`, `position`, `title`, `description`, `status` (berechnung, bereit,
  keine_loesung, fehlgeschlagen, entfernt), `metrics_before/after`, `changes`, `affected_classes/teachers`,
  `moved_lessons`, `remaining`, `valid_from`, `diff`, `compute_seconds`. Der `diff` wird bei jedem Abschluss (außer der
  gewählten Variante) gelöscht.
* `plan_proposal_log` – Verlauf (nur anhängen, ohne Fremdschlüssel): erzeugt, bereit, später, zurückgeholt, angenommen,
  verworfen, ersetzt, erledigt, veraltet, informiert, keine_loesung. Zusätzlich Audit `plan.proposal_accept` /
  `plan.proposal_discard` und die Plan-Version.

Halb berechnete Pakete (`berechnung`) werden beim Start auf `fehlgeschlagen` gesetzt; die erste Prüfung legt sie bei Bedarf neu an.

## 5. Vertretung: Bestätigungsmodus und schlankere Seite

`settings.substitution_confirm = true`: automatisch berechnete **Vertretungen und Betreuungen** (`substitution.PROPOSAL_KINDS`,
Eintrag ohne `manual`) gelten als Vorschlag. `features_common.day_plan(day, snap, proposals=False)` liefert dann den Plan
**ohne** Vorschläge (Lehrkräfte, Schüler, Eltern, Monitor, Kalender, Benachrichtigungen, offene API); mit `proposals=True`
(nur `GET /substitutions[/range]` für `substitution.edit`, Fairness-Historie) sind sie enthalten und mit `"proposed": true`
markiert (`confirm_mode`, `proposals` im Plan). `POST /substitutions/release {date, entry_ids?}` macht Vorschläge zu manuellen
Entscheidungen (Override `substitute` mit der vorgeschlagenen Lehrkraft); danach sind sie für alle sichtbar und lösen die
üblichen Benachrichtigungen aus. Entfall, Verlegung, Raumänderung und Mitbetreuung sind nicht betroffen.
Die Seite „Vertretungsplan“ zeigt nur noch Datum + Suche; Standort/Klasse/Lehrkraft/Sortierung stehen unter „Filter und
Sortierung“, Warnungen ab vier und Abwesenheiten sind eingeklappt, der Hinweis für Lehrkräfte steht im Hilfe-Symbol.

## 6. Oberfläche

* Planung → **Plan prüfen** (erster Tab, `/planung/pruefung`): Status „Plan in Ordnung / N Probleme“, „Jetzt prüfen“, offene
  Vorschläge mit Variantenvergleich, zuletzt Entschiedenes, Einstellungen. Der Generator heißt jetzt „Neuaufbau (Generator)“
  und enthält die frühere Karte „Automatische Neuplanung“ nicht mehr.
* Menüpunkt **Planvorschläge** (`/planung/vorschlaege`) mit Zähler, Startseiten-Kachel (nur bei offenen/laufenden Paketen),
  Toast bei neuem Paket (Live), Entwurfsansicht `/planung/vorschlaege/:paket/:variante`.
* Alle Erklärungen stehen in Hilfe-Symbolen (`HelpTip`).

## 7. API (Recht: `timetable.generate`, `timetable.edit` oder `settings.edit`)

| Endpunkt | Zweck |
|---|---|
| `GET /planning/proposals` | `{summary, open, recent, check}` (Pakete mit Varianten, Status der Dauerprüfung) |
| `GET /planning/proposals/summary` | Zähler für Badge/Kachel |
| `GET /planning/proposals/{id}` | Paket mit Verlauf, `outdated` |
| `GET /planning/proposals/{id}/variants/{vid}/timetable/{class\|teacher\|room}/{ref}?date=` | Stundenplan-Entwurf |
| `POST …/variants/{vid}/accept {note}` | übernehmen (409: veraltet/entschieden) |
| `POST …/discard {reason}`, `…/postpone {hours}`, `…/wake` | verwerfen / später / zurückholen |
| `GET /planning/autoplan`, `POST /planning/autoplan/run` | Status der Dauerprüfung, sofort prüfen (berechnet neu) |

## 8. Grenzen und offene Punkte

* **Gültigkeit ab Datum**: Pakete tragen nur den Hinweis „Anlass gilt ab …“. Die Übernahme ersetzt den **regulären Plan für alle
  Wochen**; Stunden mit eigenem Gültigkeitsbeginn kennt das Planungsdokument nicht. Wer nur eine Übergangszeit überbrücken
  will, wählt „Vertretung statt Planänderung“.
* Die Jobs laufen nacheinander (ein Generator-Prozess gleichzeitig); ein Paket braucht etwa Summe der Rechenzeiten
  (Standard ca. 15 + 22 + 45 s). Startet jemand währenddessen den Generator von Hand, wartet die Berechnung (bis ca. 3 min).
* Die Kennzahlen „Ø je Woche“ sind Summen über alle Klassen/Lehrkräfte; kleine Änderungen an gekoppelten Kursen
  (Oberstufen-Schienen) bewegen sie stark – deshalb werden sie vor/nach nebeneinander gezeigt.
* Benachrichtigung der Berechtigten: Live (SSE), Menüzähler, Kachel. Eine Nachricht im Postfach gibt es nicht (das
  Briefsystem hat keinen Systemabsender); E-Mail an die Berechtigten ist nicht vorgesehen.
* Lehrkräfte werden nach Annahme informiert, aber nicht vorher beteiligt (kein Einspruchsverfahren).
* Hohl-/Springstundenkennzahlen und Generator berücksichtigen nur den **regulären** Plan, nicht Tagesvertretungen.

## 9. Tests

`tests/test_plan_proposals.py` (Diff/Hash, Paket erscheint und wird angenommen, Ersetzen/veraltet, Verwerfen/Später,
Problem verschwindet, Räume nur mit Zustimmung bzw. Einstellung, Rechte), `tests/test_autoplan.py` (Dauerprüfung ändert nichts
selbst), `tests/test_substitution_confirm.py` (Bestätigungsmodus), Frontend `features/planpruefung/planpruefung.test.ts`.
