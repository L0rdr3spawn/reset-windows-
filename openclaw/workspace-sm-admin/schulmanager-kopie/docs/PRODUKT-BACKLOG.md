# Produkt-Backlog Schulmanager

Stand: 10.10.2026 · Status: Arbeitsgrundlage für den Autopiloten (Laufzeit und Stopp-Regeln: `docs/AUTOPILOT.md`).
Änderungswünsche des Auftraggebers gehen jederzeit vor; neue Wünsche bekommen eine A-ID und werden hier eingeplant.
Verbindlich für die beiden Umsetzungs-Agenten (Spur A, Spur B) und den Design/UX-Agenten (Spur D).

Grundlagen: Anforderungen des Auftraggebers (`docs/ANFORDERUNGEN.md`, IDs A-xx), Funktionsprüfung des Bestands
(Demo-Schule und leere Schule, 10.10.), fünf Bereichsanalysen (Stammdaten, Kursräume, Klassen/Eltern,
Planung/Lehrkräfte, Monitor/Oberfläche) und der Marktvergleich (WebUntis, Schulmanager Online, IServ, Sdui, EduPage,
Moodle/Logineo, itslearning, schul.cloud, beste.schule, DieSchulApp u. a.).

---

## 1. Produktziel

Ein Schulmanager, den man als vollständiges Produkt an eine Schule verkaufen kann und mit dem die Schule ihren
Alltag wirklich darüber abwickelt (A-00). Maßstab ist eine große Schule in NRW: Gymnasium, Gesamtschule und
Berufskolleg mit mehreren Bildungsgängen, rund 2500 Schüler/innen, einige hundert Lehrkräfte, zwei Standorte. Rollen:
Admin, Schulleitung, Stundenplanung, Sekretariat, Lehrkräfte, Schüler/innen, Eltern, Monitor (ab E4 zusätzlich
Ausbilder/innen).

Ohne diese Kernpunkte kauft keine Schule (Marktvergleich): persönlicher Stunden- und Vertretungsplan mit Push,
Krankmeldung und Entschuldigungsverfahren, Fehlzeiten, Elternbriefe mit Rückmeldung, Elternsprechtag, Klausurplan,
Import aus der Schulverwaltung und Untis, Schuljahreswechsel, feine Rechte mit Wechsel zur Volljährigkeit,
Löschfristen, Barrierefreiheit, App bzw. PWA und Hilfe für alle Rollen. Für das Berufskolleg kommen Bildungsgänge und
der Zugang für Ausbildungsbetriebe hinzu.

## 2. Prinzipien

1. **Schulalltag zuerst.** Was jeden Morgen gebraucht wird (Krankmeldung, Vertretung, Stundenplan, Material,
   Hausaufgaben), geht vor Verwaltungskomfort. Ein Fehler im Alltag wiegt schwerer als eine fehlende Sonderfunktion.
2. **Verständlich ohne Erklärtexte.** Kurze Beschriftungen, ein Steuerelement je Wert, Technik nur unter „Erweitert“.
   Erklärungen stehen in der Hilfe an der Beschriftung (2 s Verweilen, Rechtsklick, Antippen; A-60), nicht als Absatz
   auf der Seite. Interne Begriffe (IDs, Feldnamen, „Planungsdokument“, „Block“) erscheinen nie.
3. **Datenschutz vor Funktionsumfang.** Jede Person sieht nur, was sie für ihre Aufgabe braucht. Gesundheitsdaten nur
   für Zuständige, Volljährige entscheiden über ihre Daten, Rechte und Datenumfang werden im Backend geprüft (fremde
   Daten → 404), jede schreibende Aktion steht im Audit, personenbezogene Freitexte sind verschlüsselt.
4. **Mobil gleichwertig.** Jede Funktion für Eltern, Schüler/innen und Lehrkräfte geht am Handy vollständig (390 px
   ohne waagerechten Bildlauf), Verwaltung und Planung zusätzlich gut am PC und Tablet. Hell und dunkel.
5. **Bestand nicht brechen.** Planungsdaten bleiben abwärtskompatibel (neue Felder mit Standardwert, alte Dokumente
   laden), jede Schemaänderung ist eine Alembic-Revision, bestehende Tests bleiben grün oder werden begründet angepasst.

## 3. Arbeitsweise

### 3.1 Prioritäten und Größen

| Kennung | Bedeutung |
|---|---|
| **P0** | Muss: Pflicht-Rückmeldung des Auftraggebers oder ohne das nicht verkaufbar (inkl. Sicherheit/Datenschutz) |
| **P1** | Sollte: deutlicher Mehrwert, verbreitet bei Wettbewerbern, nicht verkaufsblockierend |
| **P2** | Kann: Feinschliff oder Sonderfall |
| **S** | Ein Bereich, wenige Dateien, unter einer Runde |
| **M** | Ein Bereich, etwa eine Runde |
| **L** | Mehrere Bereiche oder neue Tabelle, etwa zwei Runden |
| **XL** | Umbau quer durch den Kern, in Teilschritten liefern (jeder Teilschritt grün) |

Typen: **Fehler** (Verhalten falsch), **Umbau** (vorhandene Funktion neu geschnitten), **Neu** (fehlt ganz),
**Design** (Gestaltung, Sprache, Bedienung).

### 3.2 Spuren und Dateihoheit (Konfliktzonen)

Drei Spuren arbeiten parallel. Innerhalb einer Spur laufen Pakete nacheinander. Jede Datei gehört genau einer Spur;
eine andere Spur ändert sie nur über eine im Paket genannte Ausnahme.

| Zone | Dateien | Spur |
|---|---|---|
| **KZ-1 Planungskern** | `schulmanager/models.py`, `planning.py`, `scheduler.py`, `timetable.py`, `calendar_utils.py`, `exams.py`, `duties.py`, `teacher_profile.py`, `demo.py`, `server/demo_loader.py`, `server/store.py`, `server/routes/features_data.py`, `features_planning.py`, `features_exams.py`, `features_teacher_profile.py`, `features_timetable.py` | A |
| **KZ-2 Vertretung** | `schulmanager/substitution.py`, `server/routes/features_substitutions.py`, `frontend/src/pages/SubstitutionsPage.tsx`, `PrintSubstitutionsPage.tsx`, `components/EntryTable.tsx`, `lib/substitution.ts` | A |
| **KZ-3 Austausch** | `schulmanager/integrations/*`, `server/routes/features_exchange.py`, `frontend/src/pages/ImportExportPage.tsx` | A |
| **KZ-4 Stammdaten-/Planungsoberfläche** | `pages/MasterDataPage.tsx`, `pages/masterdata/*`, `pages/planning/CurriculaEditor.tsx`, `CoursesEditor.tsx`, `pages/ExamsPage.tsx`, `DutiesPage.tsx`, `features/teacher/*` (ohne `ReplanPanel.tsx` in E1), `components/RuleEditor.tsx`, `lib/rules.ts`, `pages/TimetablePage.tsx` (nur E1–E2) | A |
| **KZ-5 Rechte & Konten** | `server/permissions.py`, `deps.py`, `security.py`, `accounts.py`, `letters.py`, `login_policy.py`, `identities.py`, `pdf.py`, `server/routes/auth.py`, `users.py`, `features_letters.py`, `features_login_policy.py`, `features_sso.py`, `features_contact.py`, `pages/UsersPage.tsx`, `LoginPage.tsx`, `ProfilePage.tsx`, `features/konto/*`, `anmeldedienste/*`, `anmelderichtlinien/*`, `zugangsdaten/*` | B |
| **KZ-6 Schulleben** | `schulmanager/messaging.py`, `channels.py`, `student_self.py`, `server/files.py`, `server/routes/features_student_absences.py`, `features_student_self.py`, `features_classes.py`, `features_channels.py`, `features_messages.py`, `features_announcements.py`, `me.py`, `files.py`, `components/FileUpload.tsx`, `FileList.tsx`, `features/classes/*`, `students/*`, `channels/*`, `messages/*`, `pages/StudentAbsencesPage.tsx`, `AnnouncementsPage.tsx` | B |
| **KZ-7 Betrieb** | `server/routes/admin.py`, `system.py`, `history.py`, `server/backups.py`, `maintenance.py`, `notify.py`, `sms.py`, `config.py`, `pages/AdminPage.tsx`, `HistoryPage.tsx` | B |
| **KZ-8 Datenbank** | `server/db_models.py`, `server/feature_models/*`, `server/migrations/versions/*` | B (siehe Regel unten) |
| **KZ-9 Gestaltung & Rahmen** | `components/ui.tsx`, `Help.tsx` (neu), `Layout.tsx`, `Modal.tsx`, `Icon.tsx`, `TimetableGrid.tsx`, `MyDayView.tsx`, `styles/*`, `App.tsx`, `api/client.ts`, `pages/DashboardPage.tsx`, `MonitorPage.tsx`, `PlanningPage.tsx`, `pages/planning/SettingsPanels.tsx`, `GeneratorPanel.tsx`, `features/teacher/ReplanPanel.tsx` (E1), `pages/TimetablePage.tsx` (ab E3), `docs/DESIGN.md` | D |

**Geteilte Dateien** – nur kleine Edits nach frischem Lesen, vorher in `docs/AGENT_NOTES.md` ankündigen:
`frontend/src/api/types.ts`, `api/endpoints.ts`, `lib/permissions.ts`, `features/registry.ts`, `tests/conftest.py`,
`tests/test_server_features.py`, `docs/code/*`, `docs/OFFENE-PUNKTE.md`, `docs/AGENT_NOTES.md`. Sonderregeln:
- `server/routes/features_common.py`: Abschnitt `filter_plan`/`check_id` gehört Spur A, die Scope-Funktionen
  (`students_in_scope`, `teacher_student_ids` …) gehören Spur B.
- `models.Settings`: Spur B darf neue Felder **am Ende** der Klasse anhängen (ein Edit je Paket); alles andere in
  `models.py` gehört Spur A.
- **Migrationen**: Jedes Paket mit neuer Tabelle legt sie in einer eigenen Datei unter `feature_models/` an und
  reserviert beim Start einen Revisionsnamen in `docs/AGENT_NOTES.md`; `down_revision` ist der Kopf bei Paketstart.
  Entstehen zwei Köpfe, legt die Hauptsitzung beim Integrieren eine Merge-Revision an (wie `0007_merge`, `0012_merge`).
- Neue Oberflächen-Texte in allen Spuren folgen ab Paketstart `docs/DESIGN.md` (aus B-10). Der Textdurchgang der
  Spur D (B-23, B-43) räumt nur Bereiche auf, an denen gerade keine andere Spur arbeitet.

### 3.3 Definition of Done (gilt für jedes Paket, zusätzlich zu den Abnahmekriterien)

1. Eigene Tests (pytest bzw. vitest) für jeden Abnahmepunkt mit Logik; danach `ruff check .`, komplette Testsuite,
   `npm run lint`, `npx vitest run` grün.
2. Rechte und Datenumfang im Backend geprüft; Rechte-Matrix-Test bei jeder neuen Sichtbarkeitsregel.
3. Schreibende Aktionen im Audit; personenbezogene Freitexte verschlüsselt; Codes/Token nur als Hash.
4. Browser-Rundgang bei Oberflächenänderung: 1280 px und 390 px, hell und dunkel, Tastatur; keine neuen
   Erklärabsätze (`className="explain"`, lange `hint`-Texte) – Hilfe über die Hilfe-Funktion.
5. `docs/code/*` des Bereichs und `docs/OFFENE-PUNKTE.md` (Status je A-xx/B-xx mit Nachweis) nachgezogen.
6. Kurzer Eintrag in `docs/AGENT_NOTES.md` (Start, Entscheidungen, Ende); keine Commits durch Agenten.
7. Nach dem Paket eine Prüfrunde: Fehler suchen, nachstellen, beheben, Regressionstest.

### 3.4 Entscheidungen mit Standardwert (vom Auftraggeber änderbar)

| Frage | Standard im Backlog | Paket |
|---|---|---|
| A-49: Was bestimmt die Lehrkraft selbst? | Verfügbarkeit und eine gewünschte Höchstzahl an Wochenstunden (als Wunsch); Deputat, Vertretungsgrenzen und Tageshöchstwerte setzt die Schulleitung/Planung | B-02, B-34 |
| Sehen Eltern volljähriger Kinder etwas? | Nein, bis die Schülerin/der Schüler es freigibt; die Schule kann den Standard ändern | B-07 |
| Sehen Fachlehrkräfte Krankmeldungen? | Nein; Schulschalter „fehlt in meiner Stunde“ (Name + Stunde, ohne Grund/Status/Attest) | B-06 |
| Abwesende Lehrkräfte auf Monitor/Aushang? | Nur Kürzel, Gründe nie; Schulleitung kann abschalten | B-04, B-12 |
| Darf das Sekretariat Stundentafeln bearbeiten? | Nein, nur lesen (mit Grund); Recht bleibt bei der Planung | B-01 |
| Fremdes Material in Klassenräumen | Ändern/Löschen nur eigene Inhalte und Klassenleitung; Schalter „gemeinsam pflegen“ je Raum | B-09 |
| Postfach-Standards | Schüler/innen schreiben nicht an Mitschüler/innen; Eltern nur an Personal; bestehende Schulen werden beim Update umgestellt | B-08 |
| Klassenarbeiten-Grenze „0“ | 0 = keine Grenze | B-02 |

---

## 4. Übersicht der Etappen

Jede Etappe ist für sich auslieferbar: Nach ihrem Ende ist das Produkt in sich stimmig, alle Tests sind grün, und keine
Funktion ist halb umgebaut.

| Etappe | Ziel | Pakete |
|---|---|---|
| **E1** Vertrauen herstellen | Sicherheits- und Datenschutzfehler weg, gemeldete Pflichtfunktionen funktionieren, Grundlage für ruhige Oberfläche | B-01 – B-13 |
| **E2** Schulstruktur, Eltern, Anmeldung | Bildungsgänge, Klassengruppen, Klassenrollen, Erziehungsberechtigte, Eltern in Kursräumen, Konten wechseln, Passkeys, Einstellungen am richtigen Ort | B-14 – B-24 |
| **E3** Kalender, Unterricht, Fehlzeiten | Schuljahr und Ferien, Termine mit Wochenende, Krankmeldungen in der Klasse, Hausaufgaben, Stunden-Details, Fehlstunden je Fach, Monitor modular | B-25 – B-33 |
| **E4** Lehrkräfte, Vertretung, Schuljahr, Berufskolleg | Verfügbarkeit mit Ausnahmen, faire Vertretung, Schuljahreswechsel, Abgang/Löschfristen, Ausbilderzugang, Beurlaubung, Push/PWA, Barrierefreiheit | B-34 – B-44 |
| **E5** Kommunikation, Inbetriebnahme ohne IT | Rhythmus je Klasse, Plan-Perioden, Elternbriefe, Elternsprechtag, Systemeinstellungen, Einrichtungsassistent, Handbuch | B-45 – B-51 |
| **E6** Ausbau zum Komplettprodukt | Noten, Klassenbuch Stufe 2, Raumbuchung, Übersetzung, Module, Auskunft, Last, Feinschliff (P1/P2) | B-52 – B-59 |

Die Spurzuordnung ist für E1 verbindlich. Ab E2 ist sie vorläufig und wird zu Beginn jeder Etappe bestätigt. Kleine
Pakete (S) oder Teile aus E6 dürfen vorgezogen werden, wenn eine Spur auf eine Abhängigkeit wartet und keine
Konfliktzone berührt wird.

---

## 5. Etappe E1 – Vertrauen herstellen

**Ziel:** Keine bekannten Sicherheits- oder Datenschutzfehler der Stufe „hoch“; Stundentafel, Kursraum-Upload,
Krankmeldungs-Sichtbarkeit, Volljährigkeit und Vertretungsplan-Abwesenheiten funktionieren so, wie der Auftraggeber
sie verlangt; die Hilfe-Funktion und die Gestaltungsregeln stehen; die Planung ist verständlich.
**Auslieferbar, weil** jedes Paket einen bestehenden Bereich repariert oder vereinfacht, ohne neue Abhängigkeiten zu
offenen Umbauten.

| ID | Paket | Typ | Prio | Größe | Spur | hängt ab von |
|---|---|---|---|---|---|---|
| B-01 | Stundentafel zuverlässig machen | Fehler | P0 | L | A | – |
| B-02 | Planungsregeln halten, was sie versprechen | Fehler | P0 | L | A | – |
| B-03 | Import und Stammdaten ohne Datenverlust | Fehler | P0 | M | A | B-01 |
| B-04 | Vertretungsplan: abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“ | Umbau | P0 | M | A | – |
| B-05 | Betriebssicherheit: Demo, verwaiste Konten, Rückgängig, Sicherung | Fehler | P0 | M | B | – |
| B-06 | Krankmeldungen nur für Berechtigte | Fehler | P0 | M | B | – |
| B-07 | Volljährigkeit automatisch, Elternfreigabe durch Volljährige | Umbau | P0 | L | B | B-06 |
| B-08 | Postfach: Empfängerkreis datensparsam | Fehler | P0 | M | B | – |
| B-09 | Kursräume: Dateien und Ordner hochladen, Rechte in Klassenräumen | Fehler | P0 | L | B | – |
| B-10 | Hilfe-Funktion und Gestaltungsregeln | Design | P0 | M | D | – |
| B-11 | Planung: „Optimierung“ statt Prioritäten, Generator ohne Technikbegriffe | Design | P0 | M | D | B-02, B-10 |
| B-12 | Monitor mobil und ruhig, Startseiten-Kennzahl | Design | P0 | M | D | B-04 |
| B-13 | Verständliche Fehlermeldungen | Design | P0 | S | D | – |

**Stand bei Erstellung (10.10., 23:40):** Im Arbeitsbaum laufen bereits Änderungen, die zu E1-Paketen gehören.
Sie werden nicht neu begonnen, sondern nach Abschluss gegen die Abnahmekriterien geprüft; offene Punkte bleiben im Paket:
- B-01: `tests/test_curricula.py`, `pages/planning/RebuildCourses.tsx`, `NewSubjectDialog.tsx`, `curricula.ts`,
  Änderungen in `planning.py`, `timetable.py`, `features_data.py`, `features_planning.py`, `csv_io.py` (berührt B-03).
- B-07 (Teil) und B-20 (Teil, Eltern in Kursräumen): `server/parent_access.py`, `feature_models/parent_access.py`,
  Migration `0013_parent_access`, `routes/features_parent_access.py`.
- B-09: Änderungen in `channels.py`, `files.py`, `features_channels.py`, `feature_models/channels.py`, `test_channels.py`.
- B-10 (und ggf. B-11): `components/Help.tsx`, `lib/help.ts`, `docs/DESIGN.md`, Änderungen in `ui.tsx`, `tokens.css`,
  `app.css`, `SettingsPanels.tsx`, `GeneratorPanel.tsx`, `Layout.tsx`, `DashboardPage.tsx`.

**Rundenplan E1** (je Runde zwei Umsetzungs- und ein Design-Paket, siehe `docs/AUTOPILOT.md`):

| Runde | Spur A | Spur B | Spur D |
|---|---|---|---|
| 1 | B-01 | B-05 | B-10 |
| 2 | B-04 | B-06 | B-13 |
| 3 | B-02 | B-08 | B-12 |
| 4 | B-03 | B-09 | B-11 |
| 5 | Prüfrunde E1 | B-07 | Rundgang E1 (alle Rollen, 390/1280 px) |

### B-01 · Stundentafel zuverlässig machen
`Fehler` · **P0** · L · umsetzung (Spur A) · A-35, A-36 (Teil), A-40 (Teil)

**Nutzen:** Die Schule legt Wochenstunden je Fach fest und bekommt daraus verlässlich die richtigen Kurse und Stunden,
ohne stille Fehler.

**Abnahmekriterien**
1. Überschneiden sich zwei Stundentafeln gleichen Rangs (beide über Klasse oder beide über Jahrgang) für dieselbe
   Klasse, lehnt das Speichern mit 409 und der Liste der betroffenen Klassen ab; mit Bestätigung wird gespeichert und
   „Kurse erzeugen“ meldet den Konflikt. `GET /planning/curricula/effective` liefert je Klasse die gültige Tafel, die
   Herkunft (Klasse/Jahrgang) und Konflikte.
2. Hat eine Klasse keine Tafel oder eine Tafel ohne Fächer, meldet „Kurse erzeugen“ das mit dem Klassennamen (heute:
   leere Oberstufen-Tafel schluckt neue Klasse 11 ohne Warnung).
3. Dasselbe Fach zweimal in einer Tafel wird mit 422 abgelehnt; doppelte Kurs-IDs können nicht mehr entstehen.
4. Werden Stunden gesenkt, meldet der Qualitätsbericht „X Stunden zu viel verplant“ je Kurs, und „Kurse aktualisieren“
   bietet an, überzählige nicht fixierte Stunden zu entfernen (Vorschau, dann Übernehmen).
5. Im Kurs-Editor geänderte Stundentafel-Kurse (Stunden, Doppelstunde, Raum, Lehrkraft) behalten ihre Änderungen beim
   nächsten „Kurse erzeugen“ (Feld `Course.pinned`); der Bestätigungstext sagt das genau so.
6. Editor: „Neue Stundentafel“ zeigt ein leeres Formular ohne markierten Fremdeintrag, jede Tafel lässt sich danach
   direkt öffnen; „Gilt für“ zeigt die tatsächlich betroffenen Klassen; Jahrgänge kommen aus den vorhandenen Klassen
   statt fest 5–13; ungültige Jahrgänge lehnt die API ab.
7. In Stundentafel- und Kurs-Editor legt „Neues Fach …“ in der Fach-Auswahl ein Fach direkt an (Recht
   `masterdata.edit`); „Lehrkräfte zuweisen“ unterscheidet „keine Lehrkraft mit Fach X“ von „kein freies Deputat“.
8. Nach dem Speichern führt „Kurse der betroffenen Klassen aktualisieren“ (mit Vorschau) direkt zum Ergebnis, ohne
   Umweg über den Generator-Reiter; wer nur lesen darf, sieht den Grund statt gesperrter Felder ohne Hinweis.

**Dateien:** `schulmanager/planning.py` (Z. 47, `curriculum_for_class`, `build_courses_from_curricula`,
`assign_teachers` Z. 178), `timetable.py` (`validate_school` Z. 420), `models.py` (`Course.pinned`),
`server/routes/features_data.py` (`validate_item` curricula), `features_planning.py`,
`frontend/src/pages/planning/CurriculaEditor.tsx` (Z. 11, 34–36), `CoursesEditor.tsx`, neue Tests
`tests/test_curricula.py`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-1, KZ-4. `GeneratorPanel.tsx` wird nicht geändert (gehört in E1 Spur D).

### B-02 · Planungsregeln halten, was sie versprechen
`Fehler` · **P0** · L · umsetzung (Spur A) · A-30, A-31 (Prüfung), A-33 (Teil), A-49 (Teil), A-51 (Teil)

**Nutzen:** Generator, Qualitätsbericht und Lehrer-Selbstverwaltung arbeiten nach den Regeln, die die Schule sieht:
Doppelstunden liegen zwischen den Pausen, und niemand ändert sein Deputat selbst.

**Abnahmekriterien**
1. Generator und manuelles Verschieben legen keine Doppelstunde über eine Pause (`Settings.doubles_across_breaks`,
   Standard aus); Demo-Test: 0 Doppelstunden über Pausen (heute 30 von 93).
2. Ein Kurs mit Doppel- und Einzelstunde liegt nicht an einem Tag, solange genug Tage frei sind (heute 14 Fälle).
3. Der Qualitätsbericht meldet auch Sperrzeit-Verletzungen von Lehrkräften und Klassen, in Klartext („Dienstag,
   1. Stunde: Frau Klein doppelt belegt – D 5a und KR 5b“) statt „Woche 0, Tag 2, L1, L36“; eine Kursänderung, die eine
   Doppelbelegung erzeugt, liefert `warnings`, und der Vertretungsplan des Tages zeigt sie.
4. Eine Sperrzeit-, Wunsch- oder Rhythmus-Regel ohne Auswahl wird abgelehnt (API 422); der Editor speichert erst nach
   einer Auswahl oder dem ausdrücklichen „ganze Woche“.
5. `max_exams_per_week/day = 0` bedeutet „keine Grenze“ (`max(1, …)` entfällt).
6. `max_hours` ist nicht mehr Teil des Lehrkraft-Profils (weder Antrag noch direkt); offene Altanträge mit `max_hours`
   werden ohne Fehler ignoriert.
7. Zeitraster-Prüfung meldet überlappende Stunden (Beginn + Stundenlänge > nächster Beginn) und zu kurze Pausen;
   `core_latest_period` blockiert das Senken der Stundenzahl nicht mehr (wird angepasst, Hinweis); Schultage und
   Wochentagsnamen haben in Modell, API und Oberfläche dieselbe Obergrenze; Servertexte nennen keine Feldnamen
   („Schuljahresbeginn (cycle_start)“).
8. Eine Änderung der Unterrichtstage liefert zuerst eine Vorschau der Stunden und gekoppelten Kurse, die ihre Bedeutung
   ändert, und wird erst nach Bestätigung übernommen (Testfälle 10X, L586, Zeitfenster im Rhythmus).

**Dateien:** `schulmanager/scheduler.py` (`check`, `_blockers`, `_make_blocks`, `course_cost`), `timetable.py`
(`_evaluate`, `move_options`, `validate_school`), `exams.py` (Z. 119–124), `teacher_profile.py` (`PROFILE_FIELDS`,
`windows_to_rules`), `models.py` (`Settings`, `WEEKDAYS`), `server/routes/features_data.py` (`settings_errors`,
`_rule_errors`, Z. 689), `features_teacher_profile.py`, `frontend/src/lib/rules.ts`, `components/RuleEditor.tsx`,
`features/teacher/TeacherProfilePage.tsx`; Tests `tests/test_planning_rules.py`, `test_exams.py`,
`test_teacher_profile.py`.
**Abhängigkeiten:** keine. B-11 baut die Oberfläche für Punkt 1 und 5.
**Konfliktzone:** KZ-1, KZ-4. `SettingsPanels.tsx` wird nicht geändert (Spur D, B-11).

### B-03 · Import und Stammdaten ohne Datenverlust
`Fehler` · **P0** · M · umsetzung (Spur A) · A-01, A-37 (Teil), A-44 (Geburtsdatum)

**Nutzen:** Daten aus SchILD, ASV, LUSD und Untis kommen vollständig und gültig an, inklusive Geburtsdatum für die
Volljährigkeit, und kein Import löscht mehr unbemerkt.

**Abnahmekriterien**
1. CSV-Import (alle Vorlagen) und Untis GPU010 (Feld 13) übernehmen das Geburtsdatum nach `Student.birth_date`;
   CSV- und JSON-Export geben es aus; Rundlauf-Test.
2. Stammdaten › Schüler/innen zeigt und bearbeitet das Geburtsdatum; `GET /data/students` liefert `birth_date` nur an
   Rollen mit `users.manage` und an die Klassenleitung.
3. Jede importierte Zeile läuft durch dieselbe Prüfung wie die API (`validate_item`): unbekannte Verweise, Jahrgang
   außerhalb des Bereichs, doppelte Fächer sind Fehler mit Zeilennummer; der Import gilt ganz oder gar nicht.
4. Listen in CSV-Spalten werden nur an `,`, `;` und `|` getrennt; bestehende Kürzel mit Leerzeichen überstehen den
   Rundlauf; neue Kürzel mit Leerzeichen lehnt die API ab.
5. Untis-Import „ersetzen“ und JSON-Import zeigen im Probelauf eine Vorher-Nachher-Tabelle je Bereich („löscht 12
   Ferien-Einträge, 4 Aufsichtsbereiche, 30 Klausuren“), die Bestätigung nennt diese Zahlen; ein JSON-Dokument, dem
   Bereiche fehlen, wird ohne ausdrückliches „alles ersetzen“ abgelehnt.
6. Abweichende Schüler-IDs beim Untis-Import, die Konten von ihren Daten trennen würden, stehen im Probelauf als
   Warnung mit Namen.
7. Die Schülerzahl einer Klasse wird aus der Schülerliste berechnet; das Handfeld gilt nur, solange niemand zugeordnet
   ist, und ist so gekennzeichnet.

**Dateien:** `schulmanager/integrations/csv_io.py` (Z. 152–153, 542, 697, 792, 922), `untis_gpu.py`, `_common.py`,
`server/routes/features_exchange.py` (`_do_import_json`), `features_data.py`, `features_common.py` (`check_id`
Z. 626, Abschnitt Spur A), `frontend/src/pages/ImportExportPage.tsx`, `MasterDataPage.tsx`; Tests
`tests/test_integrations.py`.
**Abhängigkeiten:** B-01 (gleiche Prüffunktion `validate_item`).
**Konfliktzone:** KZ-1, KZ-3, KZ-4; `features_common.py` nur Abschnitt `check_id`.

### B-04 · Vertretungsplan: abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“
`Umbau` · **P0** · M · umsetzung (Spur A) · A-56

**Nutzen:** Kollegium und Planung sehen auf einen Blick, wer fehlt und wann, ohne die irreführende Liste von Klassen
mit regulärem Praxis- oder Berufsschultag.

**Abnahmekriterien**
1. `DayPlan` liefert zusätzlich `absent_teacher_details` (Kürzel, Name, Stunden oder „ganztägig“, Zahl der
   Vertretungsfälle, ohne Grund) und `absent_class_details` mit `source` = `absence` | `rhythm`; die alten Felder
   bleiben, bestehende Tests (`test_substitution.py:313`, `test_lead_integration.py:75`) bleiben grün.
2. `filter_plan` wendet Rollen-, Standort- und öffentliche Sicht auch auf die neuen Felder an (Test: Schüler/in und
   Monitor sehen keine Lehrkraft-Details ohne Freigabe).
3. /vertretung zeigt eine eigene Karte „Abwesende Lehrkräfte“ mit einer Zeile je Person (Kürzel · Name · Stunden ·
   Fälle); Klick filtert den Plan auf diese Lehrkraft.
4. „Abwesende Klassen“ entfällt auf /vertretung und im Druck; Klassen mit regulärem Rhythmus erscheinen nirgends als
   abwesend.
5. Eine gemeldete Klassenabwesenheit (Wandertag) erscheint als eine Zeile je Klasse („5a · ganztägig nicht im Haus ·
   Wandertag“) statt einer Zeile je Stunde, auch im Druck.
6. Der Druck nutzt die öffentliche Sicht wie der Monitor; ob abwesende Lehrkräfte öffentlich erscheinen, steuert eine
   Einstellung (Standard: nur Kürzel), Gründe nie.

**Dateien:** `schulmanager/substitution.py` (Z. 216–282, 1149–1153, 1172), `server/routes/features_substitutions.py`
(Z. 551), `features_common.py` (`filter_plan` Z. 544–611, Abschnitt Spur A), `models.py` (Einstellung),
`frontend/src/pages/SubstitutionsPage.tsx` (Z. 552–565), `PrintSubstitutionsPage.tsx` (Z. 46–55),
`components/EntryTable.tsx`, `lib/substitution.ts`, `api/types.ts` (geteilt); Tests `tests/test_substitution.py`.
**Abhängigkeiten:** keine. B-12 zeigt die neuen Felder auf Monitor und Startseite.
**Konfliktzone:** KZ-2; `features_common.py` nur Abschnitt `filter_plan`; `MonitorPage.tsx` und `DashboardPage.tsx`
nicht ändern (Spur D).

### B-05 · Betriebssicherheit: Demo, verwaiste Konten, Rückgängig, Sicherung
`Fehler` · **P0** · M · umsetzung (Spur B) · Bestandsprüfung (hoch/mittel)

**Nutzen:** Ein Fehlklick oder das bekannte Demo-Passwort kann den Schulbetrieb nicht mehr zerstören, und eine
Sicherung stellt wirklich alles wieder her.

**Abnahmekriterien**
1. In Produktion (`SM_ENV=production`) ist „Demo laden“ ausgeblendet und `POST /admin/demo` liefert 403; außerhalb der
   Produktion verlangt es die Eingabe des Schulnamens, „Demo-Konten anlegen“ ist standardmäßig aus.
2. In Produktion werden Konten mit dem Demo-Passwort beim Start gesperrt und im Systembereich gemeldet.
3. Wird eine Schülerin, ein Schüler oder eine Lehrkraft aus den Stammdaten gelöscht, kann sich das verknüpfte Konto
   nicht mehr anmelden (laufende Sitzungen enden); die Benutzerverwaltung zeigt es als „ohne Datensatz“ mit
   „deaktivieren“ bzw. „löschen“; Eltern sehen kein Kind „S02303“ ohne Klasse mehr.
4. „Rückgängig“ und „Wiederherstellen“ zeigen vorher, welche Änderungen anderer Personen mit zurückgenommen würden
   (Wer, Was, Wann), und verlangen dann eine Bestätigung; ohne fremde Änderungen bleibt es ein Klick.
5. „Sicherung erstellen“ erzeugt ein Archiv aus Datenbank und Dateien (Atteste, Kursraum-Dateien, Anhänge);
   Schlüssel werden nicht im Klartext mitgesichert, ohne passenden Schlüssel bricht die Wiederherstellung mit klarer
   Meldung ab.
6. Die Seite unterscheidet „Herunterladen“ und „Wiederherstellen“ (nur `system.admin`, mit Bestätigung); Rundlauf-Test:
   Sicherung → leere Instanz → Wiederherstellen → Atteste lesbar.

**Dateien:** `server/routes/admin.py` (Z. 94), `server/demo_loader.py` (Z. 28, 137; nur Passwort-Teil, Ausnahme zu
KZ-1), `config.py`, `deps.py`, `server/routes/users.py`, `backups.py` (Z. 115), `server/routes/history.py`,
`frontend/src/pages/AdminPage.tsx` (Z. 63), `HistoryPage.tsx`, `UsersPage.tsx`; Tests `tests/test_server_core.py`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-5, KZ-7. `demo_loader.py`: nur die Kontenanlage (Ausnahme, in AGENT_NOTES ankündigen).

### B-06 · Krankmeldungen nur für Berechtigte
`Fehler` · **P0** · M · umsetzung (Spur B) · A-58

**Nutzen:** Gesundheitsdaten sieht und bearbeitet nur, wer zuständig ist, wie es Art. 9 DSGVO und der Auftraggeber
verlangen.

**Abnahmekriterien**
1. Status setzen, Vermerk ändern und Löschen dürfen nur Klassenleitung, Sekretariat und Schulleitung (Rechte-Matrix:
   Fachlehrkraft 403, Lehrkraft ohne Unterricht bei der Person 404, Klassenleitung 200).
2. Fachlehrkräfte sehen standardmäßig keine Krankmeldungen; Schuleinstellung `subject_teacher_absence_view` =
   `none` (Standard) | `presence` („fehlt heute in meiner Stunde“: Name und Stunde, ohne Status, Attest, Grund und
   meldende Person); berechnet über tatsächliche Kursteile statt `course.classes` (Test: KEL sieht nur Schüler/innen
   seiner Kursteile, nicht 343).
3. Eine Lehrkraft darf eine Abwesenheit für ihre eigene Stunde melden und die eigene Meldung löschen, solange sie
   „gemeldet“ ist.
4. Die technische Administration sieht weder Gründe noch Vermerke (`student_absence.read` entfällt für `admin`).
5. Überlappende Meldungen für dieselbe Person werden zusammengeführt oder mit verständlicher Meldung abgelehnt;
   Meldungen nur für Tage ohne Unterricht (Wochenende, Ferien) werden abgelehnt.
6. /krankmeldungen nennt den richtigen Personenkreis im Hinweis „vertraulich“; „entschuldigt/unentschuldigt“ erscheint
   nur mit Berechtigung.
7. `tests/test_server_features.py:595` ist an die Regel angepasst; neue Tests `tests/test_student_absence_access.py`.

**Dateien:** `server/routes/features_student_absences.py` (Z. 46, 98, 110, `_sees_reason`), neues Modul
`schulmanager/server/absence_access.py` (Scope über Kursteile, statt `features_common.teacher_student_ids` zu ändern),
`server/permissions.py`, `models.Settings` (Feld anhängen), `frontend/src/pages/StudentAbsencesPage.tsx`,
`features/students/widgets.tsx`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-5, KZ-6; `models.Settings` nur anhängen.

### B-07 · Volljährigkeit automatisch, Elternfreigabe durch Volljährige
`Umbau` · **P0** · L · umsetzung (Spur B) · A-44, A-11

**Nutzen:** Mit dem 18. Geburtstag wechseln die Rechte automatisch zur Schülerin bzw. zum Schüler, und Volljährige
entscheiden selbst, was ihre Eltern sehen.

**Abnahmekriterien**
1. `schulmanager/server/parent_access.py` (`is_adult`, `age_on`) bestimmt die Volljährigkeit aus dem Geburtsdatum
   (Stichtag Europe/Berlin), `users.adult` gilt nur ohne Geburtsdatum; `deps.build_auth_user` rechnet bei jeder
   Anfrage, die Rechte wechseln am Geburtstag ohne Zutun (Test mit fester Uhr).
2. Klassen-Assistent, „Schüler/in hinzufügen“, „fehlende Konten anlegen“ und Massenanlage behandeln Volljährige gleich:
   kein automatisches Elternkonto, Selbst-Krankmeldung möglich (Test je Weg).
3. `parent_may_see(db, student_id, bereich)` (Bereiche in `AREAS`) entscheidet alle Elternzugriffe: Krankmeldungen mit Gründen, krankmelden,
   Dokumente, Kursraum-Übersicht, Stundenplan, Klausuren, Eltern-Gruppe der Klasse im Postfach; `_family_blocked` und
   `restricted` in Kursräumen nutzen sie.
4. Minderjährige: Eltern sehen alles, was das Kind sieht. Volljährige: es gilt die Schulvorgabe
   `adult_parent_access_default` (Standard: keine Einsicht), bis die Person selbst etwas freigibt.
5. Volljährige stellen unter „Meine Übersicht › Was meine Eltern sehen“ je Bereich und Elternkonto an oder aus; jede
   Änderung steht im Audit (ohne Inhalte) und ist jederzeit widerrufbar (Tabelle `parent_access`, Migration).
6. Wer volljährig wird, erhält am Tag eine Mitteilung; die Benutzerverwaltung zeigt „volljährig seit …“, der Haken
   „volljährig“ erscheint nur ohne Geburtsdatum.
7. Rechte-Matrix-Tests: Eltern eines minder- und eines volljährigen Kindes, mit und ohne Freigabe, je Bereich.

**Dateien:** `schulmanager/server/parent_access.py`, `server/routes/features_parent_access.py`, `server/deps.py`, `accounts.py` (`bulk_create`), `letters.py`
(`plan_accounts`), `server/routes/features_letters.py` (`create_missing`), `features_student_self.py`,
`features_student_absences.py`, `features_channels.py` (Z. 1115), `schulmanager/messaging.py` (`class_parents`),
`server/maintenance.py`, `feature_models/parent_access.py` + Migration `0013_parent_access`, `permissions.py`, `models.Settings`
(anhängen), `frontend/src/features/students/OverviewPage.tsx`, `pages/UsersPage.tsx`.
**Abhängigkeiten:** B-06 (gleiche Dateien). Nutzt Geburtsdaten aus B-03, funktioniert aber auch ohne.
**Konfliktzone:** KZ-5, KZ-6, KZ-8; `models.Settings` nur anhängen.

### B-08 · Postfach: Empfängerkreis datensparsam
`Fehler` · **P0** · M · umsetzung (Spur B) · A-13, Bestandsprüfung (K.-o.-Kriterium)

**Nutzen:** Kinder und Eltern finden im Postfach nur Personen, mit denen sie schulisch zu tun haben; eine schulweite
Personensuche mit Klassenangabe verhindert jeden Verkauf.

**Abnahmekriterien**
1. Schüler/innen schreiben standardmäßig an Lehrkräfte ihrer Kurse, Klassenleitung und Sekretariat; an Mitschüler/innen
   nur, wenn die Schule es erlaubt, dann nur innerhalb von Klasse und Kursen (`messaging_students_to_students`
   Standard „aus“).
2. Eltern schreiben standardmäßig an Personal (Lehrkräfte ihrer Kinder, Klassenleitung, Sekretariat, Schulleitung);
   andere Familien und Schüler/innen sind nicht auffindbar.
3. `GET /messages/recipients` liefert nur erlaubte Empfänger und nie Klassen fremder Kinder (Test als `schueler1` mit
   „Theo“, „Fam“ und als `eltern1` mit „Lina“).
4. Die Regeln stehen in Postfach › Einstellungen als drei Auswahlfelder; bestehende Schulen werden beim Update auf die
   neuen Standards gesetzt, der Admin sieht einmal einen Hinweis.
5. Bestehende Unterhaltungen bleiben lesbar; neue Nachrichten an nicht mehr erlaubte Empfänger werden verständlich
   abgelehnt.

**Dateien:** `schulmanager/messaging.py`, `server/routes/features_messages.py`, `models.py` (Z. 346, Ausnahme:
nur `messaging_*`-Felder), `frontend/src/features/messages/SettingsPage.tsx`, `RecipientPicker.tsx`; Tests
`tests/test_messages.py`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-6; `models.Settings` nur `messaging_*`.

### B-09 · Kursräume: Dateien und Ordner hochladen, Rechte in Klassenräumen
`Fehler` · **P0** · L · umsetzung (Spur B) · A-45, A-46 (Teil), A-10

**Nutzen:** Lehrkräfte bringen ihr Material zuverlässig in Kurs- und Klassenräume, auch ganze Ordner und übliche
Fachformate, und niemand ändert fremdes Material.

**Abnahmekriterien**
1. Eine hochgeladene Datei wird ohne zweiten Klick als Material gespeichert (mit der gewählten Sichtbarkeit);
   Schließen des Panels verliert nichts; Ablegen funktioniert über der ganzen Materialliste.
2. Ein ganzer Ordner (Auswahl oder Ziehen) wird mit Unterordnern übernommen (`paths` im Sammel-Upload, eine
   Transaktion, bestehende Grenzen für Tiefe und Anzahl); Browser-Test mit zwei Ebenen.
3. `.py`, `.java`, `.c`, `.cpp`, `.sql`, `.rtf`, `.epub`, `.tif` werden angenommen (Quelltext nur als Text-Download);
   `.ggb`, `.notebook`, `.flipchart` behalten ihre Endung; ausführbare Dateien bleiben gesperrt.
4. In Klassenräumen lesen alle Lehrkräfte der Klasse und legen eigenes Material an; fremdes Material ändern, löschen,
   freigeben und fremde Abgaben sehen nur Klassenleitung und Urheber/in (Schalter „gemeinsam pflegen“ je Raum).
5. Bei gekoppelten Kursen ist eine Lehrkraft nur dort „Lehrende“, wo sie tatsächlich Schüler/innen unterrichtet (Test:
   EK-GK-Lehrkraft nicht mehr in allen fünf Q1-Tutorien).
6. Die Klassenseite hat den Knopf „Kursraum der Klasse“; der physische Raum heißt dort „Raum der Klasse“; ein Lehrerkonto
   ohne verknüpfte Lehrkraft sieht den Hinweis, sich an das Sekretariat zu wenden.
7. Die Start-Kachel „Heute: Material freigeben“ zeigt auch Stunden aus Klassenräumen.

**Dateien:** `server/files.py` (`_KIND_LIST`, `_final_name`), `server/routes/features_channels.py` (`_ctx`,
`list_channels`, `_teacher_overview`), `schulmanager/channels.py` (`class_spec`), `messaging.py`
(`SchoolIndex.teachers_by_class`), `frontend/src/components/FileUpload.tsx` (Z. 295),
`features/channels/MaterialTab.tsx` (Z. 79, 354, 378), `ChannelListPage.tsx` (Z. 211), `widgets.tsx`,
`features/classes/ClassDetailPage.tsx`, `ClassHeader.tsx`; Tests `tests/test_channels.py`, `test_files_crypto.py`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-6.

### B-10 · Hilfe-Funktion und Gestaltungsregeln
`Design` · **P0** · M · design (Spur D) · A-59, A-60, A-61

**Nutzen:** Erklärungen verschwinden aus den Seiten und sind trotzdem da, wenn man sie braucht; Grundlage für eine
ruhige, professionelle Oberfläche in allen Spuren.

**Abnahmekriterien**
1. `components/Help.tsx`: Hilfe an Beschriftungen öffnet nach 2 s Verweilen, sofort per Rechtsklick auf den Namen, per
   Antippen des Namens auf Touch-Geräten und per F1 bzw. Umschalt+? im fokussierten Feld; Esc oder Klick außerhalb
   schließt; bleibt offen, solange der Zeiger darauf liegt (WCAG 1.4.13). Rechtsklick nur auf dem Namen, nicht im
   Eingabefeld.
2. Beschriftungen mit Hilfe sind dezent markiert (gepunktete Unterstreichung, `cursor: help`), ohne Info-Symbole; der
   Text ist über `aria-describedby` für Screenreader verbunden.
3. `Field` hat die Prop `help`; `hint` bleibt für kurze Formathinweise und ist ebenfalls per `aria-describedby`
   verknüpft (heute bei 43 Stellen nicht vorgelesen).
4. Im Benutzermenü lässt sich „Hilfetexte immer anzeigen“ einschalten (für Einsteiger).
5. Timer- und Zustandslogik als reine Funktion mit vitest; Browser-Test Maus, Touch-Emulation 390 px, Tastatur.
6. `docs/DESIGN.md` mit verbindlichen Regeln und Vorher-Nachher-Beispielen: Beschriftungen höchstens drei Wörter, ein
   Wert = ein Steuerelement, Technik unter „Erweitert“, Tokens statt Inline-Styles, Hinweise nur bei echtem Zustand,
   Sie-Form ohne „Tipp:“, Tabellen mit mehr als 5 Spalten werden unter 600 px zu Karten, Glossar der Begriffe.
7. Eine vitest-Prüfung schlägt an, wenn neue Erklärabsätze entstehen (Bestandsliste als Ausnahme, schrumpft mit jedem
   Textdurchgang).
8. Bei „Bewegung reduzieren“ laufen Animationen höchstens einmal (`animation-iteration-count: 1`; behebt das
   flackernde Laufband).

**Dateien:** `frontend/src/components/ui.tsx` (Z. 105–128), neu `components/Help.tsx`, `Layout.tsx`,
`styles/tokens.css` (Z. 163–173), `app.css`, neu `docs/DESIGN.md`, neu `lib/help.ts` (Zustandslogik) mit Test
`lib/__tests__/help.test.ts`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-9.

### B-11 · Planung: „Optimierung“ statt Prioritäten, Generator ohne Technikbegriffe

> Änderung 11.10.: Bereich auf `WeightsPanel` (SettingsPanels.tsx, Z. 223–496) begrenzt; „Schule & Schuljahr“ und Zeitraster gehen nach `CalendarPanel.tsx` (Entwurf Kalender & Zeitraster, V4).
`Design` · **P0** · M · design (Spur D) · A-34, A-30 (Oberfläche), A-59

**Nutzen:** Die Stundenplanung versteht ohne Handbuch, was der Generator optimiert, und sieht die Wirkung.

**Abnahmekriterien**
1. Der Reiter heißt „Optimierung“ und zeigt höchstens sechs Ziele (z. B. Hohlstunden Klassen, Springstunden
   Lehrkräfte, Hauptfächer früh, Fächer über die Woche verteilen, Ausfall am Tagesrand) als Stufen
   „egal · normal · wichtig · sehr wichtig“; die Stufen bilden auf die bestehenden Zahlen ab, Rohwerte nur unter
   „Erweitert“ mit genau einem Steuerelement je Wert (keine Schieberegler).
2. Neben jedem Ziel steht der Ist-Wert aus dem Qualitätsbericht („Hohlstunden Klassen: 3“).
3. „Doppelstunden“ ist eine Auswahl „nur zwischen Pausen · möglichst · egal“ statt eines Gewichts (nutzt B-02).
4. Vertretungsregeln, Lehrer-Selbstverwaltung und Attestpflicht stehen in einem eigenen Reiter „Regeln“ (bis zur
   Einstellungsseite in B-22); Wegezeit und Hauptfach-Grenze stehen beim Zeitraster; „0 = keine Grenze“ bei
   Klassenarbeiten in der Hilfe.
5. Generator: Rechenzeit als „Schnell · Normal · Gründlich“, Startwert und parallele Läufe nur unter „Erweitert“;
   Ergebnis in Klartext („3 Hohlstunden, 0 Konflikte, 12 Kurse verplant“) statt „Kosten 42.6“,
   „Optimierungsschritte“, „removed_lessons: 0“; Status deutsch, ohne Job-ID. Gleiches im Umplanungs-Dialog.
6. Ungespeicherte Änderungen lösen beim Reiter- oder Seitenwechsel eine Rückfrage aus.
7. In `SettingsPanels.tsx`, `GeneratorPanel.tsx` und `ReplanPanel.tsx` stehen keine Erklärabsätze mehr.

**Dateien:** `frontend/src/pages/PlanningPage.tsx`, `pages/planning/SettingsPanels.tsx` (Z. 157–170, 223–429,
433–583), `GeneratorPanel.tsx` (Z. 11–36, 225–238, 270), `features/teacher/ReplanPanel.tsx` (Z. 101; Ausnahme zu
KZ-4 in E1).
**Abhängigkeiten:** B-02 (Doppelstunden-Regel, Bedeutung von 0), B-10 (Hilfe).
**Konfliktzone:** KZ-9.

### B-12 · Monitor mobil und ruhig, Startseiten-Kennzahl

> Änderung 11.10.: Zusatz – Startseite und Monitor nutzen `week_info.week_text` und die 7-Tage-Helfer; abwesende Lehrkräfte/keine „fehlenden Klassen“ wie im Vertretungsplan (Entwurf P1, R2-A Rest U-11).
`Design` · **P0** · M · design (Spur D) · A-62 (Teil), A-56 (Anzeige), A-61

**Nutzen:** Der Vertretungsplan-Monitor funktioniert im Flur, am Tablet und am Handy und zeigt nur, was zählt.

**Abnahmekriterien**
1. Unter 48em Breite oder bei Touch: nativer Bildlauf statt Auto-Scroll, eine Spalte, Tage als Umschalter
   „Heute · Morgen“, Einträge als Karten je Klasse; bei 375 px keine abgeschnittenen Spalten (Playwright-Bildschirmfoto).
2. `100dvh`, umbrechende Kopfzeile, Vollbild-Knopf am Handy ausgeblendet.
3. Die Zeile „Nicht im Haus: …“ entfällt; gemeldete Klassenabwesenheiten erscheinen als eine Zeile je Klasse;
   abwesende Lehrkräfte als eigener Block, wenn die Einstellung es erlaubt (Daten aus B-04).
4. Die Uhr ist eine eigene Komponente; die Tagesspalten rendern nicht mehr jede Sekunde neu; das Laufband ist bei
   „Bewegung reduzieren“ eine statische Liste.
5. Anzahl der Tage per Adresse (`?tage=1..5`), „Stand: 07:42“ sichtbar, die laufende Stunde hervorgehoben.
6. Startseite: die Kennzahl „Klassen abwesend“ entfällt bzw. zählt nur gemeldete Klassenabwesenheiten; „Lehrkräfte
   abwesend“ führt zur neuen Karte auf /vertretung.

**Dateien:** `frontend/src/pages/MonitorPage.tsx` (Z. 83, 92, 166, 181–184), `styles/monitor.css`, `hooks/misc.ts`,
`pages/DashboardPage.tsx` (Z. 353–356), `api/endpoints.ts` (Z. 235, geteilt).
**Abhängigkeiten:** B-04.
**Konfliktzone:** KZ-9.

### B-13 · Verständliche Fehlermeldungen
`Design` · **P0** · S · design (Spur D) · A-59

**Nutzen:** Fehlermeldungen sagen auf Deutsch, was zu tun ist, statt „Field required“ oder interne Feldnamen.

**Abnahmekriterien**
1. `api/client.ts` übersetzt Validierungsfehler (fehlt, ungültiges Datum, zu lang, außerhalb des Bereichs, falscher
   Typ …) ins Deutsche und ersetzt Feldcodes durch die Beschriftung (allgemeine Zuordnungsliste, je Formular
   ergänzbar).
2. Kennt das Formular das Feld, steht der Fehler am Feld, sonst als eine Meldung ohne technische Pfade (`body.date_from`).
3. Vitest für die zehn häufigsten Fehlertypen; Stichprobe `POST /absences` ohne Datum zeigt „Bitte ein Startdatum
   angeben.“
4. Unerwartete Fehler zeigen „Das hat nicht geklappt“ mit einer Fehlernummer für den Support, nie Servertexte auf
   Englisch.

**Dateien:** `frontend/src/api/client.ts` (Z. 118–134), `components/ui.tsx` (Fehleranzeige im `Field`).
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-9.

---

## 6. Etappe E2 – Schulstruktur, Eltern und Anmeldung

**Ziel:** Das Berufskolleg bildet seine Bildungsgänge ab, Klassen haben ihre echten Rollen, Elternangaben gehen nicht
mehr verloren, Eltern sehen die Kursräume ihrer Kinder, Konten lassen sich wechseln, Einstellungen stehen an einem Ort.
**Auslieferbar, weil** die Modellpakete (B-14, B-15) abwärtskompatibel sind und die Wirkungspakete (B-19, B-20) erst
danach umschalten.

| ID | Paket | Typ | Prio | Größe | Spur | hängt ab von |
|---|---|---|---|---|---|---|
| B-14 | Bildungsgänge, Klassentypen, Klassengruppen, freie Namen | Neu | P0 | L | A | B-01 |
| B-15 | Klassenrollen im Datenmodell | Umbau | P0 | M | A | B-14 |
| B-16 | Zeitraster-Rechner und Schulwoche | Umbau | P0 | M | A | B-02 |
| B-17 | Konfigurationsdateien: Schulvorlage übertragen | Neu | P0 | L | A | B-03, B-14, B-15, B-18 |
| B-18 | Erziehungsberechtigte und Schülerakte | Neu | P0 | L | B | B-07 |
| B-19 | Klassenrollen wirksam machen | Umbau | P0 | L | B | B-15 |
| B-20 | Eltern in Kursräumen, Freigabe bei Entfall und für Ordner | Neu | P0 | L | B | B-07, B-09 |
| B-21 | Mehrere Konten, Passkeys, Passwort-Manager | Neu | P0 | L | B | – |
| B-22 | Einstellungen an ihrem Ort | Design | P0 | M | D | B-11, B-16 |
| B-23 | Textdurchgang 1, lesbare System- und Verlaufsseiten | Design | P0 | M | D | B-10 |
| B-24 | Startseiten je Rolle | Design | P1 | M | D | B-12 |

### B-14 · Bildungsgänge, Klassentypen, Klassengruppen, freie Namen
`Neu` · **P0** · L · umsetzung (Spur A) · A-38, A-40, A-43

**Nutzen:** Ein Berufskolleg führt „11 Fachinformatik“ und „11 Maurer“ als eigene Klassen mit eigenen Stundentafeln,
und Gruppen wie „Abi-Klassen“ oder „IT-Zweig 11–13“ gelten überall, wo heute nur Jahrgänge gehen.

**Abnahmekriterien**
1. Stammdaten haben die Reiter „Bildungsgänge“ (Name, Kurzname, Jahrgänge, Abschlussjahrgang, Namensmuster) und
   „Klassengruppen“ (feste Klassen oder Regel „Bildungsgang × Jahrgänge“, die beim Schuljahreswechsel mitwandert);
   Klassentypen werden angelegt und gelöscht (Löschen mit Verweisprüfung).
2. Eine Klasse hat Bildungsgang, Typ, Parallelbezeichnung und einen freien Namen (aus dem Muster vorgeschlagen,
   überschreibbar); der Jahrgangsbereich ist einstellbar (z. B. 0–14); `active` erlaubt Archivieren statt Löschen.
3. Stundentafeln gelten für Bildungsgang × Jahrgänge, Gruppen oder einzelne Klassen; Vorrang Klasse > Gruppe >
   Bildungsgang+Jahrgang > Jahrgang; Gleichrang ist ein Konflikt (Prüfung aus B-01); alte Tafeln verhalten sich wie
   heute.
4. „Entfall erlaubt ab Klassenstufe“ lässt sich je Bildungsgang überschreiben (Berufskolleg-Klassen der Stufe 1–3
   werden nicht wie Grundschüler betreut).
5. Pläne, Listen und Vertretungsplan zeigen Klassennamen statt Kürzel, wo Platz ist (Payload `class_names`).
6. Alte Planungsdokumente laden unverändert (Test mit gespeicherter Version); CSV-Export und -Import der neuen
   Bereiche; `group_class_ids(school, group_id)` steht für Rechte und Postfach bereit (Einbau in B-19).

**Dateien:** `schulmanager/models.py` (`SchoolClass`, neue Sammlungen `tracks`, `groups`, `Settings.class_types`,
`grade_min/max`), `planning.py`, `substitution.py` (`cancel_min_grade`), `server/routes/features_data.py`
(Z. 141–142, `COLLECTIONS`, Verweise), `integrations/csv_io.py`, `frontend/src/pages/MasterDataPage.tsx`,
`pages/masterdata/*` (neu), `pages/planning/CurriculaEditor.tsx`, `TimetablePage.tsx`, `SubstitutionsPage.tsx`.
**Abhängigkeiten:** B-01.
**Konfliktzone:** KZ-1, KZ-2, KZ-3, KZ-4.

### B-15 · Klassenrollen im Datenmodell
`Umbau` · **P0** · M · umsetzung (Spur A) · A-41, A-42, Rückmeldung „Abteilungsleitung“

**Nutzen:** Die Schule trägt ihre echte Verantwortungsstruktur ein; alle anderen Bereiche bauen darauf auf.

**Abnahmekriterien**
1. `SchoolClass` hat `class_teachers` (Reihenfolge = Hauptverantwortung), `deputies`, `department`, `speakers`
   (höchstens zwei Schüler/innen) und `managers`; neue Sammlung `departments` (Name, Klassen bzw. Bildungsgänge/
   Jahrgänge, Leitungen).
2. Abwärtskompatibel: altes `class_teacher` wird gelesen und weiter geschrieben (= erste Klassenleitung); alte
   Versionen, Sicherungen und Exporte laden (Test).
3. Stammdaten: Klassenleitungen als Mehrfachauswahl mit Reihenfolge, Stellvertretung, Abteilung; Reiter „Abteilungen“;
   CSV-Spalte „Klassenleitung“ nimmt „LUD, KEL“; die Untis-Abteilung (GPU003) wird als Abteilung gelesen statt als
   Standort.
4. Helfer `class_leads(cls)` und `department_heads(school, cls)` in der Kern-Domäne; „Klassenleitungen zuweisen“ füllt
   nur leere Listen; der Vertretungsbonus gilt für alle Leitungen.
5. Stammdaten › Lehrkraft zeigt „Klassenleitung in …“ (nur lesen).

**Dateien:** `schulmanager/models.py`, `planning.py` (`assign_class_teachers`), `substitution.py` (Z. 535),
`server/routes/features_data.py`, `integrations/csv_io.py`, `untis_gpu.py`, `demo.py`, `server/demo_loader.py`,
`frontend/src/pages/MasterDataPage.tsx`, `lib/csvFields.ts`.
**Abhängigkeiten:** B-14 (gleiche Dateien).
**Konfliktzone:** KZ-1, KZ-3, KZ-4. Die Rechte-Seite (16 Verwendungsstellen außerhalb KZ-1) folgt in B-19.

### B-16 · Zeitraster-Rechner und Schulwoche
`Umbau` · **P0** · M · umsetzung (Spur A) · A-31, A-32 (Teil)

**Nutzen:** Die Schule stellt Beginn, Stundenlänge und Pausen ein und bekommt korrekte Uhrzeiten, ohne jede Zeit von
Hand zu rechnen.

**Abnahmekriterien**
1. `Settings` hat `day_start`, eine Standard-Stundenlänge, optional Längen je Stunde und Pausen mit Name, Minuten und
   „trennt Doppelstunden“; `period_times` wird daraus berechnet; „Zeiten von Hand“ bleibt möglich; alte Dokumente
   gelten als „von Hand“.
2. Schultage sind einzelne Wochentage (z. B. Mo–Fr oder Mo–Sa); `days` bleibt abgeleitet erhalten; Stundenplan,
   Vertretung, Kalender und iCal nutzen dieselbe Liste.
3. `POST /settings/period-times/preview` liefert die berechneten Zeiten für die Live-Vorschau (Oberfläche in B-22).
4. Nach einer Zeitraster-Änderung werden Lehrkraft-Zeitfenster neu berechnet und der Qualitätsbericht meldet Stunden,
   die nicht mehr ins Raster passen.
5. Tests: 7:50 mit 45 min und Pausen 15/20 min, 8:00 mit 60 min, unterschiedliche Längen; Überlappung ist unmöglich.

**Dateien:** `schulmanager/models.py` (`Settings`), `calendar_utils.py`, `timetable.py`, `teacher_profile.py`
(`refresh_all_windows`), `server/routes/features_data.py` (`settings_errors`).
**Abhängigkeiten:** B-02.
**Konfliktzone:** KZ-1.

### B-17 · Konfigurationsdateien: Schulvorlage übertragen
`Neu` · **P0** · L · umsetzung (Spur A) · A-37

**Nutzen:** Eine Schule exportiert ihre Struktur mit oder ohne Personen, eine andere übernimmt sie mit Probelauf.

**Abnahmekriterien**
1. `GET /config/export.zip?bereiche=…&personen=0|1` liefert ein ZIP mit `manifest.json`, `LIESMICH.txt` und je Bereich
   einer Excel-tauglichen CSV: Standorte, Fächer, Räume, Bildungsgänge, Klassen, Klassengruppen, Abteilungen,
   Lehrkräfte (Verfügbarkeit als lesbarer Text), Schüler/innen mit Erziehungsberechtigten (nur mit Recht),
   Stundentafeln, Kopplungen, Ferien, Aufsichtsbereiche, dazu `einstellungen.json`.
2. `personen=0` ergibt eine Vorlage ohne personenbezogene Daten (Test: keine Namen, E-Mails, Geburtsdaten im ZIP).
3. `POST /config/import` (ZIP oder einzelne CSV) mit Probelauf je Bereich: neu, geändert, unverändert, würde gelöscht,
   Fehler mit Zeilennummer; feste Reihenfolge; ganz oder gar nicht; eine Version im Verlauf (rückgängig machbar).
4. Leere Vorlage je Bereich mit Beispielzeile (`GET /config/template/{bereich}.csv`).
5. Import/Export bietet „Konfiguration übertragen“ (Datei wählen → Unterschiede → Übernehmen); jeder Stammdaten-Reiter
   hat „Als Datei“ und „Aus Datei“.
6. Rundlauf-Test mit `docs/beispielschulen/berufskolleg-nrw.json`: exportieren → leere Instanz → importieren →
   identisch.

**Dateien:** `server/routes/features_exchange.py`, `integrations/csv_io.py`, neu `integrations/config_bundle.py`,
`frontend/src/pages/ImportExportPage.tsx`, `MasterDataPage.tsx`; Tests `tests/test_config_bundle.py`.
**Abhängigkeiten:** B-03, B-14, B-15; B-18 für die Elternspalten.
**Konfliktzone:** KZ-3, KZ-4.

### B-18 · Erziehungsberechtigte und Schülerakte
`Neu` · **P0** · L · umsetzung (Spur B) · A-41 (Eltern je Schüler/in), A-44

**Nutzen:** Elternangaben gehen nicht mehr verloren, Geschwister teilen ein Elternkonto, und das Sekretariat findet im
Notfall die Telefonnummer.

**Abnahmekriterien**
1. Tabelle `guardians` (verschlüsselt Name, E-Mail, Telefon; Beziehung, Sorgerecht, optional verknüpftes Konto) mit
   Migration; bestehende Eltern-Verknüpfungen werden übernommen (Migrationstest).
2. Klassen-Assistent und „Schüler/in hinzufügen“ speichern Elternangaben immer, auch ohne Elternkonto; die Eltern-
   Felder sind nicht mehr eingeklappt.
3. „Neue Zugangsdaten → Eltern“ und die Massenanlage erzeugen Konten aus den gespeicherten Erziehungsberechtigten: ein
   Konto je Person, Geschwister über die E-Mail zusammengeführt (Test: drei Kinder, zwei Elternteile → zwei Konten).
4. Schülerakte für Sekretariat und Schulleitung (Klassenleitung lesend): Geburtsdatum, Adresse, Notfallkontakt,
   Erziehungsberechtigte, Ein- und Austrittsdatum, Bemerkung (verschlüsselt); Fachlehrkräfte sehen nichts davon.
5. Klassenseite › Schüler/innen zeigt je Kind die Erziehungsberechtigten mit Status („Konto aktiv“, „kein Konto“,
   „nur Papier“).
6. Je Erziehungsberechtigtem kann die Schule den Zugriff einschränken (z. B. ohne Sorgerecht, Auskunftssperre);
   `parent_may_see` (B-07) berücksichtigt das.

**Dateien:** neu `feature_models/guardians.py` + Migration, neu `server/routes/features_guardians.py`, `letters.py`,
`accounts.py`, `server/routes/features_letters.py`, `features_classes.py`, `parent_access.py`,
`frontend/src/features/classes/StudentListEditor.tsx`, `accountsUi.tsx`, `StudentAccounts.tsx`, neu
`features/students/StudentRecordPage.tsx`, `pages/UsersPage.tsx`.
**Abhängigkeiten:** B-07.
**Konfliktzone:** KZ-5, KZ-6, KZ-8.

### B-19 · Klassenrollen wirksam machen
`Umbau` · **P0** · L · umsetzung (Spur B) · A-41, A-42, A-43, Rückmeldung „Abteilungsleitung“

**Nutzen:** Jede Klassenleitung, Stellvertretung und Abteilungsleitung hat die Rechte, die sie braucht; Klassensprecher
und Verwalter sind sichtbar.

**Abnahmekriterien**
1. Alles, was heute an „Klassenleitung“ hängt (Krankmeldungen verwalten, Atteste prüfen, Passwörter zurücksetzen,
   Zugangsdaten, Klassen-Kursraum, Postfach-Gruppe, Live-Hinweise), gilt für alle Klassenleitungen und die
   Stellvertretung; Abteilungsleitungen haben es für die Klassen ihrer Abteilung (Rechte-Matrix-Tests).
2. Verwalter einer Klasse pflegen Raum, Rollen und Schülerliste dieser Klasse und erzeugen Zugangsdaten, ohne globale
   Rechte.
3. Klassen-Assistent Schritt 1: Klassenleitungen mit Reihenfolge, Stellvertretung, Abteilung, Verwalter; Schritt 2:
   Markierung „Klassensprecher/in“ (höchstens zwei).
4. Der Klassenkopf zeigt die Rollen als Chips mit „bearbeiten“ (je nach Recht).
5. Anmelde-Richtlinien und Postfach kennen die Bereiche „Klassengruppe“ und „Abteilung“ (`MEMBER_SCOPES`,
   `GROUP_KINDS`).
6. Test: außerhalb der Kompatibilitätsschicht verwendet kein Modul mehr `class_teacher` direkt.

**Dateien:** `server/permissions.py`, `features_common.py` (Scope-Abschnitt), `features_student_absences.py`,
`features_student_self.py`, `letters.py`, `features_letters.py`, `schulmanager/channels.py`, `features_channels.py`,
`messaging.py`, `server/login_policy.py`, `features_classes.py`, `frontend/src/features/classes/NewClassPage.tsx`,
`ClassHeader.tsx`, `PeopleTabs.tsx`, `StudentAccounts.tsx`, `features/students/widgets.tsx`,
`features/anmelderichtlinien/*`.
**Abhängigkeiten:** B-15 (Modell), B-14 (Gruppen).
**Konfliktzone:** KZ-5, KZ-6.

### B-20 · Eltern in Kursräumen, Freigabe bei Entfall und für Ordner
`Neu` · **P0** · L · umsetzung (Spur B) · A-46, A-47

**Nutzen:** Eltern sehen lesend, was ihr Kind im Unterricht bekommt, und Material erscheint zur Stunde, die wirklich
stattfindet.

**Abnahmekriterien**
1. Eltern sehen unter „Kursräume“ (Kind wählen) die Kurs- und Klassenräume des Kindes lesend: freigegebenes Material,
   Aufgaben mit Frist und Status des eigenen Kindes; nie Pinnwand, Teilnehmende oder Daten anderer Kinder (Tests: 403
   beim Schreiben, 404 bei fremden Dateien).
2. Zugriff über `parent_may_see(…, 'kursraeume')`: Minderjährige Standard „Material und Aufgaben“, Volljährige nach
   eigener Freigabe; Rückmeldung und Bewertung nur in der Stufe „alles“ (Recht `channels.parent_view`, nicht
   `channels.use`).
3. Lehrkräfte können Material als „nur für Schüler/innen“ markieren (z. B. Lösungen) und die Eltern-Einsicht je Raum
   abschalten.
4. Fällt eine Stunde aus, bleibt daran gebundenes Material verborgen und die Lehrkraft wird benachrichtigt; „zur
   nächsten stattfindenden Stunde“ verschiebt die Freigabe automatisch; Verlegungen auf andere Tage werden beachtet.
5. Ganze Ordner lassen sich verbergen, zu einer Stunde oder ab einem Zeitpunkt freigeben; die strengste Regel entlang
   des Ordnerpfads gilt.

**Dateien:** `server/routes/features_channels.py` (`_role_for`, `Clock.release` Z. 460–479, Datei-Prüfungen),
`schulmanager/channels.py` (`upcoming_lessons`), `feature_models/channels.py` + Migration, `permissions.py`,
`frontend/src/features/channels/*` (`module.tsx`, `ChannelListPage.tsx`, `ChannelPage.tsx`, `VisibilityPicker.tsx`),
`features/students/OverviewPage.tsx`.
**Abhängigkeiten:** B-07, B-09.
**Konfliktzone:** KZ-6, KZ-8.

### B-21 · Mehrere Konten, Passkeys, Passwort-Manager
`Neu` · **P0** · L · umsetzung (Spur B) · A-26, A-27

**Nutzen:** Wer mehrere Rollen hat (Lehrkraft und Elternteil), wechselt mit einem Klick, und die Anmeldung ist bequem
und fälschungssicher.

**Abnahmekriterien**
1. Anmelde- und Passwortformulare sind für Passwort-Manager eindeutig: `autocomplete` `username`, `current-password`,
   `new-password`, stabile `name`/`id`, eigene Seite für das neue Passwort; Test mit dem Passwortspeicher von Chromium.
2. Passkeys (WebAuthn): unter Konto › Sicherheit hinzufügen, benennen und entfernen; Anmeldung ohne Passwort; ein
   Passkey erfüllt die Zwei-Faktor-Pflicht; Bibliothek mit fester Version; Tests mit simuliertem Authenticator.
3. „Angemeldet bleiben“ bindet das Gerät an einen Passkey oder ein nur gehasht gespeichertes Geräte-Token (HttpOnly,
   Secure, SameSite=Strict); unter „Meine Geräte“ widerrufbar; kein Fingerprinting; Datenbankinhalte allein ermöglichen
   keine Anmeldung.
4. Kontenwechsler im Benutzermenü: gespeicherte Konten (Name, Rolle), Wechsel ohne erneute Eingabe, solange die Sitzung
   gültig ist, „Konto hinzufügen“, einzeln oder alle abmelden; Daten zweier Konten vermischen sich nie (Test:
   Eltern- und Lehrerkonto parallel, jeder Aufruf mit dem aktiven Konto).
5. Audit für Passkey hinzufügen/entfernen, Geräte widerrufen und Kontowechsel; `docs/SICHERHEIT.md` um CSRF,
   Sitzungsfixierung und Kontowechsel ergänzt.

**Dateien:** `server/routes/auth.py`, `deps.py`, `security.py`, neu `feature_models/webauthn.py` + Migration,
`frontend/src/pages/LoginPage.tsx`, `components/PasswordInput.tsx`, `features/konto/*` (neu `AccountSwitcher.tsx`),
`Layout.tsx` (Ausnahme: nur Einhängen des Kontenwechslers), `docs/SICHERHEIT.md`.
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-5, KZ-8; `Layout.tsx` ein kleiner Edit nach Absprache mit Spur D.

### B-22 · Einstellungen an ihrem Ort
`Design` · **P0** · M · beide (Spur D, Backend-Anteil aus B-16) · A-32, A-31 (Oberfläche)

**Nutzen:** Jede Einstellung steht genau einmal dort, wo man sie sucht, und lässt sich ohne Nebenwirkung auf andere
Bereiche speichern.

**Abnahmekriterien**
1. Neue Seite „Einstellungen“ (Recht `settings.edit`) mit den Abschnitten Schule · Schulwoche & Zeitraster ·
   Vertretung · Lehrkräfte · Krankmeldungen & Atteste · Postfach · Schnittstellen; jede Einstellung kommt einmal vor.
2. Zeitraster mit Rechner: Beginn (7:50 / 7:55 / 8:00 / frei), Stundenlänge (45 / 60 / frei), Pausen hinzufügen,
   Live-Tabelle der Uhrzeiten (aus B-16); Schultage als Wochentags-Auswahl.
3. In „Planung“ bleiben Stundentafeln, Kurse, Generator, Optimierung und Bericht; Attestpflicht, Selbstverwaltung,
   Webhooks und API-Tokens sind umgezogen (API-Tokens aus der Kontenverwaltung nach „Schnittstellen“); alte Adressen
   leiten weiter.
4. Jeder Abschnitt speichert für sich; Fehler erscheinen am Feld im selben Abschnitt; ungespeicherte Änderungen lösen
   eine Rückfrage aus.
5. Keine Erklärabsätze, 390 px ohne waagerechten Bildlauf.

**Dateien:** neu `frontend/src/pages/settings/*`, `PlanningPage.tsx`, `pages/planning/SettingsPanels.tsx`, `App.tsx`,
`lib/permissions.ts` (geteilt), `features/messages/SettingsPage.tsx` (nur Verweis), `pages/UsersPage.tsx`
(Ausnahme: API-Token-Abschnitt entfernen, mit Spur B abstimmen).
**Abhängigkeiten:** B-11, B-16.
**Konfliktzone:** KZ-9; Ausnahmen in KZ-5/KZ-6 wie genannt.

### B-23 · Textdurchgang 1, lesbare System- und Verlaufsseiten
`Design` · **P0** · M · design (Spur D) · A-59

**Nutzen:** Weniger Text, klare Begriffe und Protokolle, die die Schulleitung lesen kann.

**Abnahmekriterien**
1. In Anmeldedienste, Zugangsdaten, System, Verlauf, Mitteilungen, Klausuren und Aufsichten stehen keine Erklärabsätze
   mehr; die vitest-Ausnahmeliste schrumpft entsprechend.
2. System: Zahlen mit deutschen Bezeichnungen („Klassen 33“, „Schüler/innen 2480“), keine Schema-Revisionen und
   Konfigurationsschlüssel (für Admin unter „Technik“ einklappbar).
3. Verlauf und Protokoll: Aktionen als Sätze („Frau Pohl hat die Krankmeldung von Theo B. entschuldigt“), Filter als
   Auswahl (Anmeldung, Konten, Krankmeldungen, Planung …) statt Präfix-Eingabe, deutsche Datumsangaben, Kürzel mit Namen.
4. Browser-Rundgang 390/1280 px, hell/dunkel.

**Dateien:** `frontend/src/features/anmeldedienste/*`, `features/zugangsdaten/*`, `pages/AdminPage.tsx`,
`HistoryPage.tsx` (Z. 108–131), `AnnouncementsPage.tsx`, `ExamsPage.tsx`, `DutiesPage.tsx` (Ausnahmen: nur Texte und
Darstellung, mit der jeweiligen Spur abgestimmt).
**Abhängigkeiten:** B-10; Bereiche, an denen in E2 eine andere Spur arbeitet, folgen in B-43.
**Konfliktzone:** KZ-9; Text-Ausnahmen in KZ-4/KZ-5/KZ-6/KZ-7.

### B-24 · Startseiten je Rolle
`Design` · **P1** · M · design (Spur D) · A-59, A-61

**Nutzen:** Jede Rolle sieht morgens zuerst, was sie heute braucht.

**Abnahmekriterien**
1. Sekretariat und Schulleitung sehen keine Planungskacheln (Hohlstunden, unverplante Stunden, Konflikte), die Planung
   schon.
2. Eine leere Schule zeigt eine Liste der nächsten Einrichtungsschritte statt Nullen (Vorstufe zu B-50).
3. „Aktualisieren“ lädt nur die Daten neu, nicht die Seite.
4. Lehrkräfte sehen ihre eigene Krankmeldung auf der Startseite und können sie verkürzen oder zurückziehen („bin doch
   da“); die Vertretungen werden neu berechnet.
5. Feste Kachel-Reihenfolge je Rolle, eine Spalte auf 390 px, keine Erklärabsätze.

**Dateien:** `frontend/src/pages/DashboardPage.tsx`, `features/registry.ts` (geteilt; Kachel-Widgets der Module werden
nur angeordnet, nicht geändert).
**Abhängigkeiten:** B-12.
**Konfliktzone:** KZ-9.

---

## 7. Etappe E3 – Kalender, Unterricht und Fehlzeiten

**Ziel:** Das Schuljahr hat Halbjahre, Schulwochen und Ferien aus der Vorlage; Termine erscheinen im Plan (auch am
Wochenende); die Klasse sieht ihre Krankmeldungen mit Nachweisstatus; Hausaufgaben, Stunden-Details und Fehlstunden je
Fach sind für alle Beteiligten sichtbar; Monitore sind frei gestaltbar.
**Auslieferbar, weil** die Unterrichtsdaten in eigenen Tabellen entstehen und den Plan nicht verändern.

| ID | Paket | Typ | Prio | Größe | Spur | hängt ab von |
|---|---|---|---|---|---|---|
| B-25 | Schuljahr, Halbjahre, Schulwochen, Ferienvorlagen | Neu | P0 | L | A | B-16 |
| B-26 | Termine und Schulkalender | Neu | P0 | L | A | B-25 |
| B-27 | Klassenarbeiten je Klasse und Halbjahr | Neu | P0 | M | A | B-25 |
| B-28 | Monitor-Profile: Datenmodell und Schnittstelle | Neu | P0 | M | A | B-04 |
| B-29 | Krankmeldungen in der Klassenansicht, Entschuldigungsverfahren | Neu | P0 | L | B | B-06, B-19 |
| B-30 | Unterrichtsstunde: Details, Hausaufgaben, Wochenplan mit Änderungen | Neu | P0 | L | B | – |
| B-31 | Anwesenheit je Stunde, Fehlstunden je Fach (Klassenbuch Stufe 1) | Neu | P0 | XL | B | B-29, B-30 |
| B-32 | Stundenplan-Ansichten: Details, Wochenende, mobil | Design | P0 | M | D | B-26, B-30 |
| B-33 | Monitor modular (Oberfläche) | Design | P0 | M | D | B-12, B-28 |

### B-25 · Schuljahr, Halbjahre, Schulwochen, Ferienvorlagen

> Änderung 11.10.: Krit. 1 (ohne Halbjahre), `Holiday.kind` aus Krit. 2 und Krit. 3 (ohne „Bezeichnung einstellbar“) übernimmt Runde 3 (Entwurf V5). Bei B-25 bleiben Halbjahre, Ferienvorlagen je Bundesland und Krit. 4.
`Neu` · **P0** · L · umsetzung (Spur A) · A-28, A-32 (Teil)

**Nutzen:** Die Schule plant in ihrem Schuljahr („Schulwoche 8, 1. Halbjahr“) statt in einem endlosen Takt, und
Ferien kommen per Klick.

**Abnahmekriterien**
1. Schuljahr (Beginn, Ende) und Abschnitte (z. B. 1./2. Halbjahr, frei benennbar); `calendar_utils.school_week(date)`
   liefert Schulwoche 1…N; Pläne zeigen „KW 42 · Schulwoche 8“.
2. Freie Tage haben eine Art (Ferien, Feiertag, beweglicher Ferientag, schulfrei); Vorlage je Bundesland für 2026/27 und
   2027/28 (mindestens NRW, Daten als JSON im Repository mit Quellenangabe) per Klick übernehmbar; Import aus iCal/CSV.
3. „Jede Woche“ ist Standard für neue Schulen; Wochenangaben (ausgewählte Wochen oder Rhythmus) zählen die Wochen 1 … 52
   des Schuljahres; einzelne Wochen lassen sich festlegen.
4. Ohne eingetragene Ferien bietet das Anlegen eines Schuljahres die Vorlage an; der Qualitätsbericht warnt.
5. Tests: Schulwoche über Ferien, Rhythmus über das Schuljahr, Altdokument ohne Schuljahr.

**Dateien:** `schulmanager/models.py` (`Settings.school_year`, `Holiday.kind`, `week_of` Z. 358), `calendar_utils.py`,
`timetable.py`, `substitution.py`, `server/routes/features_data.py`, neu `schulmanager/data/ferien/*.json`,
`frontend/src/pages/MasterDataPage.tsx` (Ferien), neu `pages/settings/CalendarSection.tsx` (Einhängen in die
Einstellungsseite: ein Edit, mit Spur D abgestimmt).
**Abhängigkeiten:** B-16.
**Konfliktzone:** KZ-1, KZ-2, KZ-4.

### B-26 · Termine und Schulkalender
`Neu` · **P0** · L · umsetzung (Spur A) · A-32 (Samstag/Sonntag), Marktvergleich „Schulkalender mit iCal“

**Nutzen:** Konferenzen, Elternabende, Exkursionen und Samstagstermine stehen im Plan aller Betroffenen, und die
Vertretung berücksichtigt sie.

**Abnahmekriterien**
1. Termine (Titel, Datum mit Uhrzeit oder Stunden, Zielgruppe: Schule, Klassen, Gruppen, Jahrgänge, Lehrkräfte;
   Pflicht/freiwillig/Info; Ort) legen Sekretariat und Schulleitung an, Lehrkräfte für ihre eigenen Klassen.
2. Kalender (Monat, Woche, Liste) je Rolle mit Ferien, Terminen und Klausuren; Eltern sehen die Termine der Klassen
   ihrer Kinder.
3. `GET /calendar?from&to` liefert je Ansicht auch Samstag/Sonntag, wenn dort ein Termin liegt; der Tag bleibt sonst
   schulfrei (Anzeige in B-32).
4. Vertretung: Termine mit Lehrkräften gelten als belegt, Klassentermine als „Klasse nicht im Haus“.
5. iCal-Abo enthält Termine und Ferien; Eltern erhalten je Kind einen Feed (behebt „nur das erste Kind“).

**Dateien:** `schulmanager/models.py` (Sammlung `events`), `calendar_utils.py`, `substitution.py`,
`server/routes/features_data.py`, neu `server/routes/features_calendar.py`, `server/routes/me.py` (Ausnahme: iCal je
Kind, Z. 29), neu `frontend/src/features/kalender/*`.
**Abhängigkeiten:** B-25.
**Konfliktzone:** KZ-1, KZ-2; `me.py` als Ausnahme aus KZ-6 (mit Spur B abstimmen, B-30 nutzt dieselbe Datei).

### B-27 · Klassenarbeiten je Klasse und Halbjahr
`Neu` · **P0** · M · umsetzung (Spur A) · A-33

**Nutzen:** Die Schule legt fest, wie viele Klassenarbeiten eine Klasse im Halbjahr schreiben darf, und das System
hält sich daran.

**Abnahmekriterien**
1. Höchstzahlen je Halbjahr für Jahrgang, Bildungsgang, Klasse oder Kurs, optional je Fach; Standardwerte je Jahrgang.
2. Beim Eintragen prüft das System zusätzlich die Halbjahresgrenze und nennt Klasse, Halbjahr und Stand („5a,
   2. Halbjahr: bereits 4 von 4 Arbeiten in Mathematik“).
3. „Klausuren“ zeigt je Klasse und Halbjahr eine Übersicht Fach · erlaubt · eingetragen; die Klassenseite verlinkt
   dorthin (kleiner Edit durch Spur B in B-29).
4. Tages- und Wochengrenzen bleiben, 0 = keine Grenze (B-02); Tests.

**Dateien:** `schulmanager/exams.py`, `models.py`, `server/routes/features_exams.py`, `frontend/src/pages/ExamsPage.tsx`.
**Abhängigkeiten:** B-25.
**Konfliktzone:** KZ-1, KZ-4.

### B-28 · Monitor-Profile: Datenmodell und Schnittstelle
`Neu` · **P0** · M · umsetzung (Spur A) · A-62

**Nutzen:** Jeder Bildschirm (Aula, Lehrerzimmer, zweiter Standort) bekommt sein eigenes Layout, ohne dass die Planung
betroffen ist.

**Abnahmekriterien**
1. Tabelle `monitor_profiles` (Name, Standort, Kacheln, Optionen, zugeordnete Monitor-Konten) mit Migration; Recht
   `monitor.manage` für Admin, Schulleitung, Sekretariat.
2. `GET/POST/PUT/DELETE /monitor/profiles`; Kacheltypen per Positivliste geprüft (Tagesplan, abwesende Lehrkräfte,
   Mitteilungen, Uhr, laufende Stunde, Klausuren, Raumänderungen, Termine).
3. `GET /monitor?profile=` liefert die Daten passend zu den Kacheln (Tage aus dem größten Versatz, höchstens fünf);
   ohne Profil bleibt die Antwort wie heute.
4. Monitor-Geräte bleiben über ein widerrufbares Geräte-Token angemeldet statt nach 30 Tagen abgemeldet zu werden.
5. Tests für Prüfung, Rechte und öffentliche Sicht.

**Dateien:** `server/routes/features_substitutions.py`, neu `feature_models/monitor.py` + Migration,
`server/permissions.py` (Ausnahme: ein Recht ergänzen, angekündigt), `deps.py` (Ausnahme: Sitzungsdauer Monitor, mit
Spur B abgestimmt).
**Abhängigkeiten:** B-04.
**Konfliktzone:** KZ-2, KZ-8; Ausnahmen in KZ-5.

### B-29 · Krankmeldungen in der Klassenansicht, Entschuldigungsverfahren
`Neu` · **P0** · L · umsetzung (Spur B) · A-57, A-52, A-58

**Nutzen:** Die Klassenleitung sieht in ihrer Klasse, wer krank ist, ob ein Nachweis da ist, wer ihn gesehen und wer
ihn anerkannt hat, und schriftliche Entschuldigungen machen Stunden zu entschuldigten.

**Abnahmekriterien**
1. Die Klassenseite hat (nur für Berechtigte) den Reiter „Krankmeldungen“ mit Zähler („3 heute“): Person, seit/bis,
   Stunden, Nachweis (eingereicht/fehlt), eingesehen von/am, anerkannt von/am; live aktualisiert.
2. Aktionen „gesehen“, „Nachweis öffnen“, „anerkennen“ (Nachweis geprüft und Meldung entschuldigt in einem Schritt, mit
   Name und Zeit) und „ablehnen“ mit Begründung.
3. Eine eingereichte schriftliche Entschuldigung (Dokumentart „Entschuldigung“) zählt als Nachweis; nach Anerkennung
   gelten die Stunden als entschuldigt; die Schule legt fest, ob schon die Online-Meldung der Eltern als Entschuldigung
   gilt.
4. Nachweisfrist (Standard 14 Tage nach Rückkehr, einstellbar); danach „Nachweis überfällig“ bei der Klassenleitung;
   automatisch „unentschuldigt“ nur, wenn die Schule es einschaltet.
5. Klassenleitung, Abteilungsleitung oder Schulleitung können einzelnen Lehrkräften Einsicht geben (Stufe „anwesend/
   abwesend“ oder „vollständig“, befristbar).
6. „Atteste & Dokumente“ steht für Lehrkräfte mit Leitungsrolle im Menü.
7. Tests: Rechte-Matrix, Anerkennung, Frist.

**Dateien:** `server/routes/features_student_absences.py`, `features_student_self.py`, `schulmanager/student_self.py`
(`attest_info`), `feature_models/student_self.py` + Migration (`seen_*`, `decided_*`, `absence_viewers`),
`features_classes.py`, `frontend/src/features/classes/ClassDetailPage.tsx`, neu `SickTab.tsx`,
`features/students/DocumentsPage.tsx`, `module.tsx`, `pages/StudentAbsencesPage.tsx`.
**Abhängigkeiten:** B-06, B-19.
**Konfliktzone:** KZ-6, KZ-8.

### B-30 · Unterrichtsstunde: Details, Hausaufgaben, Wochenplan mit Änderungen
`Neu` · **P0** · L · umsetzung (Spur B) · A-54, A-55

**Nutzen:** Ein Tipp auf eine Stunde zeigt alles Wichtige, Lehrkräfte tragen Hausaufgaben ein, und Familien sehen die
echte Woche mit allen Änderungen.

**Abnahmekriterien**
1. Datensatz „Unterrichtsstunde“ je Datum und Stunde (Hausaufgabe mit Fälligkeit, optional Thema) mit Migration;
   Lehrkräfte tragen in eigenen Stunden (auch Vertretungen) Hausaufgaben ein, am PC und am Handy.
2. `GET /lessons/detail?date=&period=&…` liefert vollen Namen der Lehrkraft (bzw. Vertretung), vollen Fachnamen, Raum
   mit Standort, Status (findet statt, Vertretung, Raumänderung, entfällt, verlegt) und Hausaufgabe, im Datenumfang
   der Rolle.
3. Schüler/innen und Eltern sehen Hausaufgaben nach Fälligkeit („bis morgen“, „diese Woche“); Schüler/innen haken
   „erledigt“ ab; Aufgaben aus Kursräumen erscheinen in derselben Liste mit Verweis.
4. `GET /me/week?date=` liefert für Schüler/innen und Eltern (je Kind) die konkrete Kalenderwoche mit Vertretungen,
   Entfall und Raumänderungen (Anzeige in B-32).
5. Tests für den Datenumfang (nur eigene Kurse; Eltern je Kind; Volljährige über `parent_may_see`).

**Dateien:** neu `feature_models/lessons.py` + Migration, neu `server/routes/features_lessons.py`,
`server/routes/me.py`, neu `frontend/src/features/unterricht/*`.
**Abhängigkeiten:** keine (Anzeige im Raster in B-32).
**Konfliktzone:** KZ-6, KZ-8; `me.py` gemeinsam mit B-26 (Abschnitte trennen, ankündigen).

### B-31 · Anwesenheit je Stunde, Fehlstunden je Fach (Klassenbuch Stufe 1)
`Neu` · **P0** · XL · umsetzung (Spur B) · A-53, Marktvergleich „Digitales Klassenbuch“, „Fehlzeiten-Auswertung“

**Nutzen:** Lehrkräfte erfassen Anwesenheit und Verspätung mit einem Klick, und Schüler/innen, Eltern und Lehrkräfte
sehen entschuldigte, unentschuldigte und verspätete Stunden je Fach – Grundlage für Zeugnis und Schulpflicht.

**Abnahmekriterien**
1. In jeder eigenen Stunde (auch Vertretung) eine Anwesenheitsliste: „alle da“ mit einem Klick, je Person „fehlt“ oder
   „verspätet (Minuten)“; Krankmeldungen des Tages sind vorausgefüllt; am Handy bedienbar, bei schlechtem Netz wird
   zwischengespeichert.
2. Eine Fehlstunde ist eine Abwesenheit in einer Unterrichtsstunde; ihr Status folgt der Krankmeldung bzw. Anerkennung
   (B-29), ohne Meldung „offen“.
3. Auswertung je Schüler/in und Halbjahr: entschuldigt, unentschuldigt, offen, Verspätungen (Anzahl und Minuten), je
   Fach; sichtbar für die Person, Eltern (über `parent_may_see`), Klassenleitung; Fachlehrkräfte nur für ihr Fach.
4. Klassenleitung: Klassenübersicht mit einstellbaren Warnschwellen und CSV-Export der Fehlzeiten je Halbjahr (für
   Zeugnis bzw. Schulverwaltung).
5. Klassen- und Schulleitung sehen Stunden ohne Anwesenheitskontrolle und können erinnern.
6. Änderungen nach Stundenende stehen im Audit; Auswertung für 2500 Schüler/innen und ein Halbjahr unter 1 s.

**Dateien:** `feature_models/lessons.py` (Anwesenheit) + Migration, `server/routes/features_lessons.py`,
`features_student_absences.py`, neu `frontend/src/features/klassenbuch/*`, `server/routes/me.py`.
**Abhängigkeiten:** B-29, B-30.
**Konfliktzone:** KZ-6, KZ-8. In Teilschritten liefern: (a) Erfassung, (b) Auswertung, (c) Kontrolle und Export.

### B-32 · Stundenplan-Ansichten: Details, Wochenende, mobil
`Design` · **P0** · M · beide (Spur D, Daten aus B-26/B-30) · A-54, A-32, A-61

**Nutzen:** Der Stundenplan ist am Handy lesbar und erklärt jede Stunde auf Antippen.

**Abnahmekriterien**
1. Antippen oder Klicken auf eine Stunde öffnet die Details (am PC als Einblendung, am Handy als Blatt von unten) mit
   vollem Namen, Fach, Raum, Status und Hausaufgabe.
2. Kürzel bleiben in der Zelle; der Status ist mit Farbe und Text erkennbar.
3. Wochenansicht mit Wochenwechsel und „heute“; Samstag/Sonntag erscheinen nur bei Terminen.
4. Auf 390 px eine Tagesansicht mit Wischen zwischen den Tagen; am Tablet die Woche.
5. Mit der Tastatur bedienbar (Pfeiltasten im Raster, Enter öffnet die Details).

**Dateien:** `frontend/src/components/TimetableGrid.tsx`, `MyDayView.tsx`, `pages/TimetablePage.tsx` (ab E3 Spur D),
`styles/timetable.css`.
**Abhängigkeiten:** B-26, B-30.
**Konfliktzone:** KZ-9.

### B-33 · Monitor modular (Oberfläche)
`Design` · **P0** · M · design (Spur D) · A-62

**Nutzen:** Die Schule stellt Monitore aus Kacheln zusammen, ohne Entwickler.

**Abnahmekriterien**
1. „Monitor einrichten“: Kacheln hinzufügen, entfernen, anordnen und in der Größe ändern; Vorschau mit Beispieldaten;
   Auswahlfelder statt Schieberegler (Bildlauf langsam/normal/schnell, Schriftgröße, Folgetag ab Uhrzeit).
2. Tagesplan-Kachel: heute oder morgen, gruppiert nach Klasse oder Stunde, Spaltenauswahl.
3. `/monitor/p/:profil` zeigt ein Profil, `/monitor/:standort` funktioniert weiter.
4. Kacheln passen sich der Breite an (Tabelle ab 48em, darunter Karten), am Handy eine Spalte mit nativem Bildlauf.
5. Zwei Monitore mit verschiedenen Profilen gleichzeitig getestet (Aula, Lehrerzimmer).

**Dateien:** neu `frontend/src/features/monitor/*`, `pages/MonitorPage.tsx`, `styles/monitor.css`, `App.tsx`.
**Abhängigkeiten:** B-12, B-28.
**Konfliktzone:** KZ-9.

---

## 8. Etappe E4 – Lehrkräfte, Vertretung, Schuljahr und Berufskolleg

**Ziel:** Lehrkräfte pflegen nur Verfügbarkeit und Vertretungsklassen, Vertretungen verteilen sich fair über das
Halbjahr, der Schuljahreswechsel läuft per Assistent, Abgänge und Löschfristen sind geregelt, Ausbildungsbetriebe und
Beurlaubungen sind abgebildet, Push-Nachrichten kommen an.
**Auslieferbar, weil** Verfügbarkeit (B-35) Altdaten verlustfrei übernimmt und der Schuljahreswechsel einen Probelauf
und Rückgängig hat.

| ID | Paket | Typ | Prio | Größe | Spur | hängt ab von |
|---|---|---|---|---|---|---|
| B-34 | Lehrkräfte: Rollen statt Wunschklassen, schlanke Selbstverwaltung | Umbau | P0 | M | A | B-15 |
| B-35 | Verfügbarkeit als Wochenplan mit Ausnahmen, Sperrzeiten frei | Umbau | P0 | XL | A | B-34, B-25, B-42 |
| B-36 | Faire Vertretung: Vertretungskonto und Mehrarbeit | Neu | P0 | L | A | B-35 |
| B-37 | Schuljahreswechsel und Versetzung | Neu | P0 | L | A | B-14, B-15, B-25 |
| B-38 | Abgang, Archiv und Löschfristen | Neu | P0 | L | B | B-18 |
| B-39 | Ausbildungsbetriebe und Ausbilderzugang | Neu | P0 | L | B | B-18, B-31 |
| B-40 | Beurlaubungen und Befreiungen | Neu | P0 | M | B | B-29 |
| B-41 | Push-Benachrichtigungen und installierbare App | Neu | P0 | L | beide (B + D) | – |
| B-42 | Bausteine Zeitraster-Auswahl und Wiederholung | Design | P0 | M | D | B-10 |
| B-43 | Textdurchgang 2 | Design | P0 | M | D | Ende E2/E3 in den Bereichen |
| B-44 | Barrierefreiheit prüfen, Erklärung veröffentlichen | Design | P0 | M | D | B-10 |

### B-34 · Lehrkräfte: Rollen statt Wunschklassen, schlanke Selbstverwaltung
`Umbau` · **P0** · M · umsetzung (Spur A) · A-48, A-49, A-36 (Lehrkraft), A-08

**Nutzen:** Lehrkräfte geben an, wo sie vertreten können und wann sie verfügbar sind; Deputat und Grenzen bleiben bei
der Schulleitung.

**Abnahmekriterien**
1. Das Lehrkraft-Profil zeigt „Klassenleitung in“ (nur lesen), „Ich unterrichte“ (aus den Kursen, nur lesen) und „Ich
   kann vertreten in“ (bearbeitbar, vorgeschlagen: die unterrichteten Klassen).
2. Wunschklassen werden einmalig in „kann vertreten in“ übernommen und sind nicht mehr sichtbar; die Planung liest
   Altwerte weiter.
3. Lehrkräfte geben nur Verfügbarkeit und eine gewünschte Höchstzahl an Wochenstunden an (als Wunsch für die Planung);
   welche Felder sie ändern dürfen, ist einstellbar; Deputat, Vertretungs- und Tagesgrenzen nur über die Stammdaten.
4. Die Vertretung bevorzugt Lehrkräfte mit „kann vertreten in“ für die Klasse (Test).
5. Im Profil lässt sich ein neues Fach vorschlagen (Name, Kürzel); die Planung genehmigt es mit „auf vorhandenes Fach
   abbilden“ gegen Dubletten.
6. Ein Lehrerkonto ohne verknüpfte Lehrkraft kann „Ich bin neu“ beantragen; die Planung legt die Lehrkraft an und
   verknüpft sie.

**Dateien:** `schulmanager/models.py` (`Teacher.substitute_classes`, `requested_max_hours`), `teacher_profile.py`,
`server/routes/features_teacher_profile.py`, `planning.py`, `substitution.py` (`_score`),
`frontend/src/features/teacher/TeacherProfilePage.tsx`, `TeacherRequestsPage.tsx`, `pages/MasterDataPage.tsx`.
**Abhängigkeiten:** B-15.
**Konfliktzone:** KZ-1, KZ-2, KZ-4.

### B-35 · Verfügbarkeit als Wochenplan mit Ausnahmen, Sperrzeiten frei
`Umbau` · **P0** · XL · umsetzung (Spur A) · A-50, A-51, A-08

**Nutzen:** Lehrkräfte beschreiben ihre Arbeitszeit so, wie sie ist („jeden 1. Mittwoch im Monat nicht“, „alle zwei
Wochen erst ab 10“), und Planung wie Vertretung halten sich daran.

**Abnahmekriterien**
1. Verfügbarkeit = Grundwochenplan (leer = immer verfügbar) plus Ausnahmen mit Wiederholung: wöchentlich (alle n Wochen
   ab Datum), monatlich (n-ter Wochentag), jährlich, mit Gültigkeitszeitraum; Arten „nicht verfügbar“, „erst ab“, „nur
   bis“, „nur“.
2. Die Beispiele des Auftraggebers sind Tests: jeden 1. Mittwoch im Monat, jede 3. Woche nicht, alle 2 Wochen erst ab
   10, mittwochs nie nach 12, erst ab 9.
3. Sperrzeiten bis zur einzelnen Stunde an einzelnen Tagen über das Raster aus B-42 (keine Kreuzprodukt-Regeln, keine
   festen Schnellvorlagen).
4. `blocked_periods(teacher, date)` liefert die Sperre je Datum für Vertretung, Klassenwoche und Klausuren; der
   Generator nutzt alle zum Planungsrhythmus passenden Regeln, die übrigen meldet der Bericht („an 5 Terminen im
   Halbjahr Konflikt – Vertretung nötig“).
5. Vorschau: Kalender der nächsten acht Wochen mit den verfügbaren Zeiten.
6. Zeitfenster und Sperrzeiten werden verlustfrei übernommen (Migrationstest); CSV-Export als lesbarer Text.

**Dateien:** `schulmanager/models.py` (`Teacher.availability`), `teacher_profile.py`, `scheduler.py`, `timetable.py`,
`integrations/csv_io.py`, `server/routes/features_teacher_profile.py`, `components/RuleEditor.tsx`, `lib/rules.ts`,
`features/teacher/TeacherFields.tsx`, `TeacherProfilePage.tsx`, `windows.ts`, `pages/MasterDataPage.tsx`.
**Abhängigkeiten:** B-34, B-25 (Datumslogik), B-42 (Bausteine).
**Konfliktzone:** KZ-1, KZ-3, KZ-4. Teilschritte: (a) Datenmodell und Auswertung, (b) Generator und Bericht,
(c) Oberfläche. `substitution.py` wird erst in B-36 angebunden.

### B-36 · Faire Vertretung: Vertretungskonto und Mehrarbeit
`Neu` · **P0** · L · umsetzung (Spur A) · A-49, Marktvergleich „Vertretungszähler, Mehrarbeit“

**Nutzen:** Vertretungen verteilen sich über das Halbjahr gleichmäßig nach Deputat, statt jede Woche dieselben drei
Lehrkräfte zu treffen.

**Abnahmekriterien**
1. Vertretungen, Entfälle und Mitbetreuungen werden je Tag in einem Vertretungskonto gespeichert (Tabelle mit
   Migration); nachträgliche Änderungen zählen mit.
2. Die Auswahl bevorzugt Lehrkräfte unter ihrem Soll (Anteil nach Deputat) im eingestellten Zeitraum (Standard:
   Halbjahr); Simulation aus der Bestandsprüfung (vier Wochen, drei Langzeitkranke): niemand liegt über dem Doppelten
   seines Solls, solange andere unter Soll verfügbar sind (heute 17 von 57 Lehrkräften tragen alles).
3. Keine starren Mindestzahlen; Höchstgrenzen bleiben als Schutz mit Warnung.
4. Vertretungsseite und Lehrkraft-Detail zeigen Ist, Soll und Abweichung im Halbjahr; jede Lehrkraft sieht ihr eigenes
   Konto.
5. Abwesenheitsarten (krank, Fortbildung, Dienstreise, Klassenfahrt, Sonstiges) werden getrennt gezählt;
   Monatsübersicht Mehrarbeit je Lehrkraft als CSV.
6. Vertretungskandidaten zeigen Gründe als Merkmale („Fachlehrkraft“, „kennt die Klasse“, „ohnehin im Haus“, „unter
   Soll“) statt einer nackten Punktzahl; die datumsgenaue Verfügbarkeit aus B-35 wird beachtet.

**Dateien:** `schulmanager/substitution.py` (`_score`, `_Engine.evaluate` Z. 510–518), `server/routes/features_substitutions.py`,
neu `feature_models/substitution_ledger.py` + Migration, `frontend/src/pages/SubstitutionsPage.tsx` (Z. 295–296).
**Abhängigkeiten:** B-35.
**Konfliktzone:** KZ-2, KZ-8.

### B-37 · Schuljahreswechsel und Versetzung
`Neu` · **P0** · L · umsetzung (Spur A) · A-39

**Nutzen:** Zum Schuljahresende rücken alle Klassen per Assistent eine Stufe höher, ohne 2500 Schüler/innen von Hand
umzuhängen.

**Abnahmekriterien**
1. Assistent „Neues Schuljahr“ mit Probelauf: je Klasse versetzen, wiederholen, abschließen oder belassen (Vorschlag:
   versetzen; abschließen im Abschlussjahrgang des Bildungsgangs), neue Namen aus dem Muster („5a“ → „6a“, „11a IT“ →
   „12a IT“), leere Eingangsklassen je Bildungsgang, Klassenleitungen übernehmen ja/nein.
2. Klassen-Kürzel bleiben stabil, nur Jahrgang und Name ändern sich; Kurse, Kursräume, Richtlinien und Mitteilungen
   bleiben gültig (Test).
3. Stundentafel-Kurse und Stunden werden für das neue Jahr neu erzeugt (manuelle Kurse wahlweise behalten); Ferien und
   Halbjahre kommen aus der Vorlage.
4. Einzelne Schüler/innen lassen sich als Wiederholer oder Abgänger markieren; Abgänger-Klassen werden archiviert und
   an den Abgangsablauf (B-38) übergeben.
5. Eine Version im Verlauf, rückgängig bis zur ersten Änderung im neuen Jahr; das alte Schuljahr bleibt lesbar.
6. Test mit den Beispielschulen Gesamtschule und Berufskolleg.

**Dateien:** neu `schulmanager/school_year.py`, neu `server/routes/features_school_year.py`, `models.py`, `planning.py`,
neu `frontend/src/features/schuljahr/*`.
**Abhängigkeiten:** B-14, B-15, B-25; Übergabe an B-38.
**Konfliktzone:** KZ-1.

### B-38 · Abgang, Archiv und Löschfristen
`Neu` · **P0** · L · umsetzung (Spur B) · Marktvergleich „Löschfristen nach Landesrecht“, Bestandsprüfung „Abgang“

**Nutzen:** Abgänge laufen geordnet, Daten werden fristgerecht gelöscht, und die Schulleitung kann die Einhaltung
nachweisen.

**Abnahmekriterien**
1. Abgang einer Person (Datum, Grund) statt Löschen: das Konto endet zum Stichtag, Elternzugänge enden, die Daten werden
   archiviert (nur Sekretariat und Schulleitung lesend); ebenso für Lehrkräfte (Kursräume übergeben).
2. Löschfristen je Datenart einstellbar mit NRW-Vorlage nach VO-DV I (Klassenbuch, Kursbuch, Zeugnislisten 10 Jahre,
   Schülerstammblatt 20 Jahre, übrige Daten 5 Jahre); weitere Länder als eigene Vorlage.
3. Ein täglicher Lauf löscht fällige Daten einschließlich Dateien und protokolliert die Löschung ohne Inhalte; Vorschau
   „wird in den nächsten 30 Tagen gelöscht“.
4. Die bestehende Aufbewahrung im Postfach steht in derselben Oberfläche.
5. Tests mit fester Uhr.

**Dateien:** `server/maintenance.py`, `accounts.py`, `server/routes/users.py`, neu `feature_models/retention.py` +
Migration, neu `server/routes/features_retention.py`, `frontend/src/pages/UsersPage.tsx`, neu
`pages/settings/RetentionSection.tsx`.
**Abhängigkeiten:** B-18.
**Konfliktzone:** KZ-5, KZ-7, KZ-8.

### B-39 · Ausbildungsbetriebe und Ausbilderzugang
`Neu` · **P0** · L · umsetzung (Spur B) · Marktvergleich „Zugang für Ausbildungsbetriebe“ (Berufskolleg)

**Nutzen:** Ohne Ausbilderzugang ist der Berufskolleg-Zweig nicht verkaufbar; Betriebe sehen Plan und Fehlzeiten ihrer
Azubis.

**Abnahmekriterien**
1. Stammdaten „Ausbildungsbetriebe“ (Name, Adresse, Ansprechpersonen mit E-Mail); Zuordnung Schüler/in ↔ Betrieb mit
   Zeitraum; CSV-Import.
2. Rolle „Ausbilder/in“ mit Zugang per Einladung an die hinterlegte E-Mail; sieht nur die eigenen Azubis: Stundenplan
   mit Änderungen, Fehlzeiten mit Stunden, anstehende Klassenarbeiten.
3. Ob der Zugang auch gegen den Wunsch volljähriger Azubis besteht, legt die Schule je Bildungsgang fest; die
   Datenschutzinformation nennt das.
4. Ausbilder/innen sehen Krankmeldungen ihrer Azubis ohne Grund und zeichnen Beurlaubungen mit (B-40).
5. Rechte-Matrix-Tests; fremde Azubis liefern 404.

**Dateien:** `server/permissions.py` (neue Rolle), neu `feature_models/companies.py` + Migration, neu
`server/routes/features_companies.py`, `letters.py`, neu `frontend/src/features/betriebe/*`.
**Abhängigkeiten:** B-18, B-31.
**Konfliktzone:** KZ-5, KZ-6, KZ-8.

### B-40 · Beurlaubungen und Befreiungen
`Neu` · **P0** · M · umsetzung (Spur B) · Marktvergleich „Beurlaubungsanträge“, Bestandsprüfung (Krankmeldung für Juni)

**Nutzen:** Planbare Abwesenheiten laufen als Antrag mit Genehmigung statt als „Krankmeldung“ für die Zukunft.

**Abnahmekriterien**
1. Eltern bzw. volljährige Schüler/innen beantragen planbare Abwesenheiten (Datum oder Stunden, Grund, Nachweis);
   Krankmeldungen, die mehr als einen Tag in der Zukunft beginnen, werden auf „Beurlaubung beantragen“ umgeleitet.
2. Genehmigungsweg nach Dauer einstellbar (z. B. bis zwei Tage Klassenleitung, länger oder direkt vor/nach Ferien
   Schulleitung); bei Azubis zeichnet der Betrieb mit, wenn eingeschaltet.
3. Status beantragt, genehmigt, abgelehnt mit Begründung; Benachrichtigung; genehmigte Beurlaubungen gelten in der
   Anwesenheit (B-31) als entschuldigt.
4. Fachbefreiungen (z. B. Sport mit Attest, Zeitraum) markieren die Person in den betroffenen Stunden.
5. Tests.

**Dateien:** `server/routes/features_student_absences.py`, `features_student_self.py`, `feature_models/student_self.py`
+ Migration, `frontend/src/features/students/*`, `pages/StudentAbsencesPage.tsx`.
**Abhängigkeiten:** B-29 (B-39 für die Mitzeichnung durch Betriebe).
**Konfliktzone:** KZ-6, KZ-8.

### B-41 · Push-Benachrichtigungen und installierbare App
`Neu` · **P0** · L · beide (Spur B Backend, Spur D Rahmen) · Marktvergleich „App/PWA mit Push“, Bestandsprüfung

**Nutzen:** Familien und Lehrkräfte erfahren von „morgen Entfall 1.–2. Stunde“, ohne die Seite zu öffnen.

**Abnahmekriterien**
1. Manifest, Symbole und Service Worker: installierbar auf Android, iOS (ab 16.4) und Desktop; Offline-Seite, der
   zuletzt geladene Stundenplan ist ohne Netz lesbar.
2. Web Push (VAPID, Schlüssel vom Server erzeugt, kein Drittanbieter): Abo je Gerät, widerrufbar; Nachrichten bei
   Vertretung, Entfall oder Raumänderung in eigenen bzw. Kind-Stunden von heute und morgen, neuer Nachricht und
   Krankmeldung in der eigenen Klasse (Klassenleitung).
3. Je Person einstellbar, worüber benachrichtigt wird; Ruhezeiten (z. B. 20–6 Uhr) außer für heutigen Unterricht.
4. Inhalte ohne Gesundheitsdaten und ohne Namen anderer Kinder („Änderung im Plan für morgen“).
5. Test in Chromium; Versand einer Planänderung an 2500 Abos unter 30 s.

**Dateien:** Spur D: neu `frontend/public/manifest.webmanifest`, `sw.js`, Symbole, `main.tsx`, `vite.config.ts`;
Spur B: `server/notify.py`, neu `feature_models/push.py` + Migration, neu `server/routes/features_push.py`,
`features/konto/*` (Einstellungen).
**Abhängigkeiten:** keine.
**Konfliktzone:** KZ-7, KZ-8, KZ-9; Schnittstelle zwischen den Spuren vorab in AGENT_NOTES festlegen.

### B-42 · Bausteine Zeitraster-Auswahl und Wiederholung
`Design` · **P0** · M · design (Spur D) · A-50, A-51

**Nutzen:** Verfügbarkeit und Sperrzeiten lassen sich mit der Maus oder dem Finger malen und in einem Satz wiederholen,
ohne Formulare voller Umschalter.

**Abnahmekriterien**
1. „Zeitraster-Auswahl“: Tage × Stunden bzw. Uhrzeiten, Zellen per Klick und Ziehen umschalten, mit der Tastatur
   bedienbar, am Handy je Tag als Liste.
2. „Wiederholung“: Satzbaukasten („Jeden [1.] [Mittwoch] im [Monat] → [nicht verfügbar]“, „Alle [2] Wochen ab [Datum]
   erst ab [10:00]“) mit Zusammenfassung in Klartext.
3. Vitest für die Umwandlung Auswahl ↔ Regeldaten.
4. Vorschau-Kalender über acht Wochen als eigener Baustein.

**Dateien:** neu `frontend/src/components/AvailabilityGrid.tsx`, `RecurrencePicker.tsx`, `styles/app.css`.
**Abhängigkeiten:** B-10. Wird in B-35 eingesetzt.
**Konfliktzone:** KZ-9.

### B-43 · Textdurchgang 2
`Design` · **P0** · M · design (Spur D) · A-59

**Nutzen:** Die ganze Oberfläche spricht dieselbe ruhige, knappe Sprache.

**Abnahmekriterien**
1. In Stammdaten, Import/Export, Klassen, Kursräumen, Schüler-Ansichten, Lehrkraft-Profil, Vertretung,
   Anmelde-Richtlinien und Konto stehen keine Erklärabsätze mehr; die vitest-Ausnahmeliste ist leer.
2. Begriffe nach dem Glossar in `docs/DESIGN.md` (z. B. „Kursraum“, „Raum der Klasse“, „Woche 1“ statt Wochenbuchstabe,
   „Stunde/Doppelstunde“ statt Block, „Planung“ statt Planungsdokument); ein Test sucht nach verbotenen Begriffen.
3. Inline-Styles in diesen Bereichen um mindestens 80 % reduziert (Tokens und Klassen).
4. Tabellen mit mehr als fünf Spalten werden unter 600 px zu Karten.

**Dateien:** die genannten Bereiche (`pages/*`, `features/*`) nach Abschluss der jeweiligen Umsetzungspakete.
**Abhängigkeiten:** Ende der E2/E3-Pakete in diesen Bereichen; nicht gleichzeitig mit B-35 im Lehrkraft-Profil.
**Konfliktzone:** Text-Ausnahmen in KZ-4/KZ-5/KZ-6, je Bereich mit der Spur abgestimmt.

### B-44 · Barrierefreiheit prüfen, Erklärung veröffentlichen
`Design` · **P0** · M · design (Spur D) · Marktvergleich „BITV 2.0 / WCAG 2.1 AA“, A-61

**Nutzen:** Schulen sind öffentliche Stellen; ohne Nachweis der Barrierefreiheit scheitert die Vergabe.

**Abnahmekriterien**
1. Automatische Prüfung (axe-core über Playwright) der 20 wichtigsten Seiten je Rolle ohne schwere Verstöße, Teil der
   Testsuite.
2. Dokumentierte Prüfung mit Tastatur und Screenreader (NVDA, VoiceOver) für Anmeldung, Krankmeldung, Stundenplan,
   Postfach, Kursraum und Vertretungsplan.
3. Kontraste nach WCAG 2.1 AA in hell und dunkel (Token-Test); 200 % Zoom ohne Verlust; 390 px ohne waagerechten
   Bildlauf.
4. Erklärung zur Barrierefreiheit nach BITV-Vorlage mit Rückmeldeweg ist in der App erreichbar.
5. PDF-Zugangsbriefe mit Struktur-Tags (Umsetzung in `server/pdf.py` durch Spur B, als Teilaufgabe angekündigt).

**Dateien:** neu `frontend/e2e/a11y.spec.ts` (Playwright), `styles/tokens.css`, neu
`frontend/src/pages/AccessibilityPage.tsx`; `server/pdf.py` (Spur B).
**Abhängigkeiten:** B-10.
**Konfliktzone:** KZ-9; `pdf.py` in KZ-5.

---

## 9. Etappe E5 – Kommunikation und Inbetriebnahme ohne IT

**Ziel:** Jede Klasse hat ihren eigenen Rhythmus, Pläne gelten ab einem Datum, Elternbriefe ersetzen Papier, der
Elternsprechtag wird gebucht, und eine neue Schule richtet sich ohne Entwickler ein.
**Auslieferbar, weil** Rhythmus und Plan-Perioden mit Vorschau migrieren und Kommunikation in neuen Modulen entsteht.

| ID | Paket | Typ | Prio | Größe | Spur | hängt ab von |
|---|---|---|---|---|---|---|
| B-45 | Rhythmus je Klasse | Umbau | P0 | XL | A | B-25, B-35 |
| B-46 | Stundenplan-Perioden „gültig ab“ | Umbau | P0 | XL | A | B-45 |
| B-47 | Elternbriefe mit Lesebestätigung, Rückmeldung, Einwilligungen | Neu | P0 | XL | B | B-18, B-41 |
| B-48 | Elternsprechtag und Sprechstunden | Neu | P0 | L | B | B-18, B-26 |
| B-49 | Systemeinstellungen ohne IT: E-Mail, SMS, Zwei-Faktor | Umbau | P0 | M | B | B-22 |
| B-50 | Einrichtungsassistent für neue Schulen | Neu | P0 | L | beide (D + A) | B-16, B-17, B-22, B-25, B-49 |
| B-51 | Hilfecenter, Handbuch je Rolle, Einführungs- und Datenschutzpaket | Neu | P0 | L | beide (D + A/B) | B-10 |

### B-45 · Rhythmus je Klasse

> Änderung 11.10.: **Entfällt** – ersetzt durch `docs/entwurf/KALENDER-ZEITRASTER.md` (Runden 3 und 4, A-67–A-69).
`Umbau` · **P0** · XL · umsetzung (Spur A) · A-29, A-28

**Nutzen:** Praxisklassen, Berufsschul-Turnus und Klassen ohne Wochenangabe leben nebeneinander, ohne dass ein globaler
Takt alles bestimmt.

**Abnahmekriterien**
1. Jede Wochenangabe (auch die einer Klasse) ist jede Woche, ausgewählte Wochen oder ein Rhythmus (alle k Wochen ab Woche s);
   bearbeitet in der Stundenplan-Ansicht der Klasse in der Planung und in Stammdaten › Klasse.
2. Der Generator plant über Wochenvarianten (Gruppen von Wochen mit gleichen Bedingungen) statt über feste Zyklen;
   Klassen ohne Wochenangabe haben jede Woche denselben Plan.
3. Bestehende Schulen werden beim Laden verlustfrei umgerechnet (frühere Wochenfolge mit n Wochen → Rhythmus „alle n Wochen ab Woche …“);
   keine Regel ändert still ihre Bedeutung (Testfälle 10X, L586, Zeitfenster im Rhythmus).
4. Untis-Export und -Import, iCal und Monitor zeigen je Klasse die richtige Woche (Tests in `test_integrations.py`).
5. Generator für die Beispiel-Gesamtschule mit gemischten Rhythmen in der Standardrechenzeit ohne Konflikte.

**Dateien:** `schulmanager/models.py`, `scheduler.py`, `timetable.py`, `substitution.py`, `planning.py`,
`calendar_utils.py`, `integrations/*`, `server/routes/features_data.py` (68 Fundstellen im Backend, 26 Dateien im
Frontend).
**Abhängigkeiten:** B-25, B-35.
**Konfliktzone:** KZ-1, KZ-2, KZ-3; Oberfläche im Klassen-Stundenplan mit Spur D abstimmen. Teilschritte:
(a) Modell und Migration mit Vorschau, (b) Generator, (c) Anzeigen und Schnittstellen.

### B-46 · Stundenplan-Perioden „gültig ab“
`Umbau` · **P0** · XL · umsetzung (Spur A) · Marktvergleich „Unterrichtsrhythmen“, Bestandsprüfung (hoch)

**Nutzen:** Ein neuer Plan zum Halbjahr oder ein Lehrerwechsel gilt ab einem Datum; vergangene Pläne, Vertretungen
und Statistiken bleiben, wie sie waren.

**Abnahmekriterien**
1. Der Stundenplan hat Gültigkeitszeiträume; „Übernehmen“ aus Generator, Untis-Import und Verschieben fragt „gültig ab“
   (Standard: nächster Montag).
2. Vertretungsplan, Klassenwoche, iCal und Statistiken nutzen je Datum den gültigen Plan; die Vergangenheit ändert sich
   nicht mehr (Test).
3. Lehrkräfte und Schüler/innen sehen den künftigen Plan ab Freigabe als Vorschau.
4. Kursräume („zur Stunde“) und Konfliktprüfungen nutzen die gültige Periode.
5. Alte Dokumente gelten als eine Periode ab Schuljahresbeginn.

**Dateien:** `schulmanager/models.py`, `timetable.py`, `substitution.py`, `server/store.py`,
`server/routes/features_timetable.py`, `features_planning.py`, `integrations/untis_gpu.py`; Anbindung
`channels.py` durch Spur B.
**Abhängigkeiten:** B-45 (gleiche Dateien).
**Konfliktzone:** KZ-1, KZ-2, KZ-3.

### B-47 · Elternbriefe mit Lesebestätigung, Rückmeldung, Einwilligungen
`Neu` · **P0** · XL · umsetzung (Spur B) · Marktvergleich (Hauptkaufargument), Bestandsprüfung (hoch)

**Nutzen:** Elternbriefe, Abschnitte zum Abtrennen und Einwilligungen laufen digital mit Nachweis, statt über die
„Ranzenpost“.

**Abnahmekriterien**
1. Brief an Klasse, Jahrgang, Bildungsgang, Gruppe oder Schule mit PDF-Anhang; Benachrichtigung per Push bzw. E-Mail;
   Volljährige erhalten Briefe selbst, Eltern nur mit Freigabe.
2. Lesebestätigung je Familie mit einem Klick, Lesestand für Absender/in („23 von 28 Familien“), Erinnerung an die
   übrigen.
3. Rückmeldung: Ja/Nein, Auswahl, Freitext, Unterschrift auf dem Bildschirm, Frist; Auswertung als Liste und CSV.
4. Einwilligungen (z. B. Fotos, Datenverarbeitung) aus Vorlagen: versioniert, jederzeit widerrufbar, mit Nachweis nach
   Art. 7 DSGVO, Übersicht je Klasse („Wer darf fotografiert werden?“); ab einstellbarem Alter willigen Schüler/innen
   selbst ein.
5. Papier-Fallback: Liste der Familien ohne Konto, Serienbrief als PDF.
6. Archiv aller Briefe je Klasse und Schuljahr.

**Dateien:** `server/routes/features_announcements.py` (Z. 129) oder neues Modul `features_parent_letters.py`, neu
`feature_models/parent_letters.py` + Migration, `messaging.py` (Zielgruppen), `pdf.py`, neu
`frontend/src/features/elternbriefe/*`.
**Abhängigkeiten:** B-18, B-41.
**Konfliktzone:** KZ-5, KZ-6, KZ-8. Teilschritte: (a) Brief und Lesebestätigung, (b) Rückmeldung, (c) Einwilligungen.

### B-48 · Elternsprechtag und Sprechstunden
`Neu` · **P0** · L · umsetzung (Spur B) · Marktvergleich (muss)

**Nutzen:** Eltern buchen Gesprächstermine am Handy, Lehrkräfte bekommen ihre Liste, und niemand verteilt Zettel.

**Abnahmekriterien**
1. Sprechtag anlegen: Datum, Zeitfenster, Anmeldephase, Slotlänge (5 oder 10 min), Puffer, Raum je Lehrkraft, vor Ort
   oder online (Link).
2. Eltern sehen nur Lehrkräfte ihrer Kinder und buchen im Raster am Handy wie am PC; Doppelbuchungen sind
   ausgeschlossen; 500 gleichzeitige Buchungen zur Freischaltung getestet.
3. Lehrkräfte laden gezielt ein und sperren Slots; Eltern erhalten einen Laufzettel (Zeiten, Räume) als PDF und iCal,
   Lehrkräfte ihre Liste.
4. Wöchentliche Sprechstunde je Lehrkraft mit Buchung, Bestätigung und Absage.
5. Tests.

**Dateien:** neu `feature_models/consultations.py` + Migration, neu `server/routes/features_consultations.py`, neu
`frontend/src/features/sprechtag/*`.
**Abhängigkeiten:** B-18, B-26.
**Konfliktzone:** KZ-6, KZ-8.

### B-49 · Systemeinstellungen ohne IT: E-Mail, SMS, Zwei-Faktor
`Umbau` · **P0** · M · umsetzung (Spur B) · Bestandsprüfung (hoch)

**Nutzen:** Eine Schule nimmt E-Mail-Versand, SMS und Zwei-Faktor-Pflicht ohne Serverzugang in Betrieb.

**Abnahmekriterien**
1. Einstellungen › Schnittstellen: SMTP (Server, Port, Absender, Zugang) und SMS-Anbieter in der Oberfläche; Passwörter
   verschlüsselt gespeichert und nie wieder angezeigt; Umgebungsvariablen haben Vorrang und sind als „vom Server
   vorgegeben“ gekennzeichnet.
2. Testversand an eine Adresse bzw. Nummer mit verständlicher Fehlermeldung.
3. Zwei-Faktor-Pflicht je Rolle in der Oberfläche (Standard: Pflicht für Admin, Schulleitung, Sekretariat, Planung;
   Lehrkräfte einstellbar).
4. Sperre nach Fehlversuchen und Wiederherstellungscodes sichtbar und einstellbar.
5. Audit und Tests.

**Dateien:** `server/config.py` (Z. 85–99), `notify.py`, `sms.py`, `features_contact.py` (Z. 481), neu
`feature_models/system_settings.py` + Migration, `server/routes/system.py`, neu
`frontend/src/pages/settings/InterfacesSection.tsx`.
**Abhängigkeiten:** B-22.
**Konfliktzone:** KZ-5, KZ-7, KZ-8.

### B-50 · Einrichtungsassistent für neue Schulen
`Neu` · **P0** · L · beide (Spur D Oberfläche, Spur A Schritte für Planung) · Marktvergleich (muss), Bestandsprüfung (hoch)

**Nutzen:** Eine leere Instanz wird ohne Entwickler zu einer arbeitsfähigen Schule.

**Abnahmekriterien**
1. Geführter Ablauf mit Fortschritt: Schule und Logo → Standorte → Schuljahr und Ferien (Vorlage) → Zeitraster →
   Bildungsgänge → Fächer → Räume → Lehrkräfte → Klassen und Schüler/innen (Import oder Vorlage aus B-17) →
   Stundentafeln → E-Mail-Versand → Konten und Zugangsbriefe.
2. Jeder Schritt lässt sich überspringen und über „Einrichtung fortsetzen“ später öffnen; die Startseite zeigt offene
   Schritte.
3. Die Beispielschulen (Gymnasium, Gesamtschule, Berufskolleg) sind als Startvorlage wählbar.
4. Protokollierter Rundgang: Beispielschule Berufskolleg ohne Entwicklerwissen in unter 60 Minuten eingerichtet.
5. Keine Erklärabsätze; Hilfe an den Feldern.

**Dateien:** neu `frontend/src/features/einrichtung/*`, `pages/DashboardPage.tsx`, `App.tsx`; Backend-Status
`GET /setup/status` in neuem `server/routes/features_setup.py` (Spur A).
**Abhängigkeiten:** B-16, B-17, B-22, B-25, B-49.
**Konfliktzone:** KZ-9; neue Dateien.

### B-51 · Hilfecenter, Handbuch je Rolle, Einführungs- und Datenschutzpaket
`Neu` · **P0** · L · beide (Spur D Hilfecenter, Spur A/B Fachtexte) · Marktvergleich (muss: Handbuch, Einführungspaket, AV-Vertrag)

**Nutzen:** Schulen müssen Anleitungen, Elternbriefe zur Einführung und Datenschutzunterlagen nicht mehr selbst
schreiben – das senkt die Einführungshürde am stärksten.

**Abnahmekriterien**
1. Hilfecenter `/hilfe`, durchsuchbar, je Rolle (Admin, Planung, Sekretariat, Schulleitung, Lehrkräfte, Eltern,
   Schüler/innen, Ausbilder/innen); jede Seite verlinkt ihren Abschnitt, die Hilfe an Feldern verweist auf
   „mehr dazu“.
2. Kurzanleitungen als PDF je Rolle (eine bis zwei Seiten, Bildschirmfotos aus der Demo).
3. Einführungspaket: Muster-Elternbrief, Aushang, FAQ, Pressetext-Vorlage.
4. Datenschutzunterlagen als Vorlagen: Datenschutzinformationen nach Art. 13/14 (Eltern, Schüler/innen, Lehrkräfte),
   Eintrag für das Verzeichnis der Verarbeitungstätigkeiten, Beschreibung der technischen und organisatorischen
   Maßnahmen, Nutzungsordnung, Muster-Auftragsverarbeitungsvertrag mit Liste der Unterauftragnehmer (vor Verkauf
   juristisch prüfen lassen), Hilfe zur Datenschutz-Folgenabschätzung.
5. Texte in einfacher Sprache, geprüft gegen `docs/DESIGN.md`.

**Dateien:** neu `docs/handbuch/*`, `docs/datenschutz/*`, neu `frontend/src/features/hilfe/*`.
**Abhängigkeiten:** B-10; inhaltlich die jeweils fertigen Bereiche.
**Konfliktzone:** neue Dateien; Verweise aus Seiten nur über die Hilfe-Funktion.

---

## 10. Etappe E6 – Ausbau zum Komplettprodukt

**Ziel:** Bereiche, die für „alles über die App“ nötig sind, aber nicht verkaufsblockierend, weil Schulen sie
übergangsweise mit Landes- oder Spezialsystemen abdecken.
**Auslieferbar, weil** jedes Paket ein eigenes, abschaltbares Modul ist.

| ID | Paket | Typ | Prio | Größe | Spur | hängt ab von |
|---|---|---|---|---|---|---|
| B-52 | Notenbuch und Notenübergabe an SchILD/SVWS | Neu | P1 | XL | A | B-14, B-25, B-31 |
| B-53 | Klassenbuch Stufe 2: Thema, Einträge, Kontrolle, offline | Neu | P1 | L | B | B-31 |
| B-54 | Raum- und Gerätebuchung | Neu | P1 | L | A | B-46 |
| B-55 | Übersetzung von Elternbriefen per Klick | Neu | P1 | M | B | B-47 |
| B-56 | Module ein- und ausschalten | Neu | P1 | M | D | B-22 |
| B-57 | Auskunft und Datenexport je Person (Art. 15 DSGVO) | Neu | P1 | M | B | B-18, B-38 |
| B-58 | Lastspitzen, Verfügbarkeit, Statusseite | Neu | P1 | M | A | – |
| B-59 | Alltagsfeinschliff | Fehler | P1/P2 | M | A + B | – |

### B-52 · Notenbuch und Notenübergabe an SchILD/SVWS
`Neu` · **P1** · XL · umsetzung (Spur A) · Marktvergleich (muss: Notenbuch, Notenübergabe)

**Begründung für die Aufnahme:** Der Marktvergleich führt Notenbuch und Notenübergabe als „muss“, und der Auftraggeber
will, dass die Schule „alles darüber“ macht. **P1 statt P0**, weil Zeugnisse in NRW verbindlich in SchILD-NRW bzw.
SVWS gedruckt werden und Lehrkräfte Noten dort heute über das ENM erfassen; WebUntis und IServ werden ohne
Notenmodul verkauft. Deshalb nur Notenbuch und Export, kein eigener Zeugnisdruck.

**Nutzen:** Lehrkräfte führen ihre Noten im selben System und geben sie ohne Abtippen an die Schulverwaltung.

**Abnahmekriterien**
1. Notenbuch je Kurs: Leistungsarten (schriftlich, sonstige Mitarbeit, frei definierbar), Gewichtung, Notensystem je
   Schulform bzw. Bildungsgang (1–6 mit Tendenz, 0–15 Punkte, Lernfelder am Berufskolleg).
2. Halbjahres- bzw. Zeugnisnote als Vorschlag, durch die Lehrkraft festgelegt.
3. Einsicht für Schüler/innen und Eltern von der Schule einstellbar (keine, Einzelnoten ohne Schnitt, ab Rückgabe).
4. Export der Noten, Fehlstunden (aus B-31) und Bemerkungen im ENM- bzw. SVWS-Format; Rundlauf-Test mit der
   öffentlichen Formatbeschreibung.
5. Notenkonferenz-Liste je Klasse mit Markierung von Defiziten.
6. Jede Notenänderung steht im Audit; Noten sieht nur, wer sie braucht (Rechte-Matrix).

**Dateien:** neu `schulmanager/grades.py`, `feature_models/grades.py` + Migration, `server/routes/features_grades.py`,
`integrations/enm.py`, `frontend/src/features/noten/*`.
**Abhängigkeiten:** B-14, B-25, B-31.
**Konfliktzone:** neue Dateien, KZ-3, KZ-8.

### B-53 · Klassenbuch Stufe 2: Thema, Einträge, Kontrolle, offline
`Neu` · **P1** · L · umsetzung (Spur B) · Marktvergleich „Digitales Klassenbuch“, „Kontrolle des Klassenbuchs“

**Nutzen:** Das digitale Klassenbuch ersetzt das amtliche Papier-Klassenbuch.

**Abnahmekriterien**
1. Je Stunde Thema (optional aus einer Stoffverteilung) und Klassenbucheintrag bzw. Bemerkung; Vertretungen und Termine
   fließen automatisch ein.
2. Klassen- und Schulleitung sehen Stunden ohne Thema und erinnern.
3. Erfassung am Tablet ohne Netz mit späterer Synchronisation, Konflikte werden angezeigt.
4. Druck bzw. PDF des Klassenbuchs je Woche und Halbjahr (für Archiv und Löschfrist 10 Jahre).
5. Tests.

**Dateien:** `feature_models/lessons.py`, `server/routes/features_lessons.py`, `frontend/src/features/klassenbuch/*`.
**Abhängigkeiten:** B-31.
**Konfliktzone:** KZ-6, KZ-8.

### B-54 · Raum- und Gerätebuchung
`Neu` · **P1** · L · umsetzung (Spur A) · Marktvergleich (sollte), Bestandsprüfung (fehlt)

**Nutzen:** Lehrkräfte finden einen freien Raum und buchen PC-Raum, Aula oder Tablet-Koffer selbst.

**Abnahmekriterien**
1. Buchbare Räume und Geräte je Standort; belegte Räume laut Plan sind nicht buchbar.
2. „Freien Raum finden“ für Datum und Stunde.
3. Einfache Raumwechsel durch Lehrkräfte selbst (wenn freigeschaltet), sichtbar im Vertretungsplan.
4. Übersicht für Hausmeister bzw. IT; Tests.

**Dateien:** `schulmanager/models.py`, neu `schulmanager/bookings.py`, `server/routes/features_bookings.py`,
`frontend/src/features/buchung/*`.
**Abhängigkeiten:** B-46.
**Konfliktzone:** KZ-1, KZ-2.

### B-55 · Übersetzung von Elternbriefen per Klick
`Neu` · **P1** · M · umsetzung (Spur B) · Marktvergleich (muss)

**Begründung P1:** verlangt einen externen Übersetzungsdienst als Unterauftragnehmer (AV-Vertrag, EU-Standort); als
abschaltbares Modul, damit Schulen ohne diesen Vertrag nicht blockiert sind.

**Nutzen:** Zugewanderte Familien verstehen Elternbriefe und Nachrichten der Schule, ohne dass Lehrkräfte übersetzen.

**Abnahmekriterien**
1. Eltern lesen Briefe und Nachrichten in ihrer Sprache (mindestens TR, AR, UK, RU, PL, RO, EN, FR) mit dem Hinweis
   „maschinell übersetzt“ und Zugriff auf das Original.
2. Dienst in den Einstellungen wählbar und abschaltbar; ohne Dienst keine Übertragung.
3. Übertragen wird nur der Brieftext, keine Namen von Kindern (wo möglich ersetzt).
4. Tests mit simuliertem Dienst.

**Dateien:** neu `server/translation.py`, `features/elternbriefe/*`, `features/messages/*`.
**Abhängigkeiten:** B-47.
**Konfliktzone:** KZ-6.

### B-56 · Module ein- und ausschalten
`Neu` · **P1** · M · design (Spur D, kleiner Backend-Anteil Spur B) · Marktvergleich „modulare Lizenz“

**Nutzen:** Die Schule bezahlt und sieht nur die Module, die sie nutzt; das ermöglicht eine modulare Lizenz wie bei den Wettbewerbern.

**Abnahmekriterien**
1. Admin schaltet Module ein und aus (Kursräume, Postfach, Klassenbuch, Elternbriefe, Sprechtag, Noten, Buchung,
   Monitor …); nicht gebuchte Module verschwinden aus Menü, Startseite und API (404).
2. Ausschalten löscht keine Daten; Wiedereinschalten stellt sie her.
3. Die Feature-Registry liest den Modulstatus zentral.
4. Tests.

**Dateien:** `frontend/src/features/registry.ts`, `App.tsx`, `server/permissions.py` (Spur B), neue Einstellung.
**Abhängigkeiten:** B-22.
**Konfliktzone:** KZ-9, geteilte Registry.

### B-57 · Auskunft und Datenexport je Person (Art. 15 DSGVO)
`Neu` · **P1** · M · umsetzung (Spur B) · Marktvergleich „Betroffenenrechte“

**Nutzen:** Die Schule beantwortet ein Auskunftsersuchen in Minuten statt in Tagen.

**Abnahmekriterien**
1. Sekretariat bzw. Schulleitung erzeugt auf Knopfdruck eine Auskunft über alle gespeicherten Daten einer Person als
   PDF und maschinenlesbare Datei.
2. Berichtigung und Sperrung sind aus der Auskunft heraus erreichbar.
3. Die Auskunft enthält keine Daten Dritter (z. B. Namen anderer Kinder in Nachrichten werden geschwärzt).
4. Audit und Tests.

**Dateien:** neu `server/routes/features_privacy.py`, `server/pdf.py`.
**Abhängigkeiten:** B-18, B-38.
**Konfliktzone:** KZ-5, KZ-6.

### B-58 · Lastspitzen, Verfügbarkeit, Statusseite
`Neu` · **P1** · M · umsetzung (Spur A) · Marktvergleich „SLA, Lastspitzen“

**Nutzen:** Die Schule kann sich darauf verlassen, dass das System um 7:45 Uhr und am Zeugnistag erreichbar bleibt.

**Abnahmekriterien**
1. Lasttest für 7:30–8:00 Uhr (2500 Schüler/innen, 300 Lehrkräfte, Krankmeldungen und Planabrufe) mit Zielwerten
   (95 % unter 500 ms) im Repository.
2. Lasttest Freischaltung Elternsprechtag und Zeugnistag.
3. Öffentliche Statusseite und Wartungshinweis (Wartung außerhalb der Unterrichtszeit planbar).
4. Ergebnisse und Betriebsempfehlung in `docs/BETRIEB.md`.

**Dateien:** neu `scripts/loadtest/*`, `docs/BETRIEB.md`, `server/routes/system.py` (Statusendpunkt, Spur B abstimmen).
**Abhängigkeiten:** keine.
**Konfliktzone:** neue Dateien.

### B-59 · Alltagsfeinschliff
`Fehler` · **P1/P2** · M · umsetzung (Spur A und B, je Punkt) · Bestandsprüfung (mittel/niedrig)

**Nutzen:** Kleine Hürden im Alltag verschwinden, die sonst täglich Rückfragen beim Sekretariat auslösen.

**Abnahmekriterien**
1. (A, P1) „Klasse ist nicht da“ hat auf Klassenseite und im Vertretungsplan dieselbe Höchstdauer (bis Schuljahresende);
   ein dreiwöchiges Betriebspraktikum lässt sich auf der Klassenseite erfassen.
2. (A, P1) Schalter „Kollegium sieht den ganzen Vertretungsplan“ für Lehrkräfte (Lehrerzimmer-Ansicht).
3. (B, P1) Klassenlisten drucken und als Excel/CSV exportieren (Wandertag, Klausuraufsicht, Elternabend); der
   Vertretungs-Aushang nennt den Standort mit Namen statt „S1“.
4. (A, P2) Kürzel unterscheiden nicht mehr nach Groß- und Kleinschreibung („MUE“ und „mue“ sind dieselbe Lehrkraft);
   Abwesenheits-IDs werden nicht wiederverwendet.
5. (A, P2) Die Demo bezeichnet die Oberstufe nach NRW-G9 (EF = 11, Q1 = 12, Q2 = 13).

**Dateien:** `server/routes/features_classes.py` (Z. 42, Spur B), `features_substitutions.py`, `features_data.py`,
`demo.py`, `features/classes/*`, `pages/PrintSubstitutionsPage.tsx`.
**Abhängigkeiten:** keine; als Lückenfüller jederzeit vorziehbar.
**Konfliktzone:** je Punkt in der Zone der zuständigen Spur.

---

## 11. Abdeckung der Auftraggeber-Anforderungen

| Anforderung | Pakete |
|---|---|
| A-26 mehrere Konten wechseln | B-21 |
| A-27 Passwort-Manager, fälschungssichere Geräteerkennung | B-21 |
| A-28 Woche 1…52, Feiertage | B-25, B-45 |
| A-29 Rhythmus je Klasse | B-45 |
| A-30 Doppelstunden zwischen Pausen | B-02, B-11 |
| A-31 Zeitraster frei | B-02 (Prüfung), B-16, B-22 |
| A-32 Einstellungen am Ort, Schultage, Samstag/Sonntag bei Terminen | B-16, B-22, B-26, B-32 |
| A-33 Klassenarbeiten je Klasse und Halbjahr | B-02 (0-Fehler), B-27 |
| A-34 Prioritäten-Tab verständlich | B-11 |
| A-35 Stundentafel reparieren | B-01 |
| A-36 eigene Fächer, auch durch Lehrkräfte | B-01, B-34 |
| A-37 Konfigurationsdateien | B-03 (Teil), B-17 |
| A-38 Klassentypen, Bildungsgänge, eigene Namen | B-14 |
| A-39 automatische Versetzung | B-37 |
| A-40 „gilt für Jahrgang“ ersetzen | B-01 (Teil), B-14 |
| A-41 Klassenleitungen, Klassensprecher, Verwalter, Eltern je Schüler/in | B-15, B-18, B-19 |
| A-42 mehrere Klassenleitungen | B-15, B-19 |
| A-43 Klassengruppen | B-14, B-19 |
| A-44 Eltern-Kind, Volljährigkeit aus Geburtsdatum, Freigabe durch Volljährige | B-03, B-07, B-18 |
| A-45 Ordner und Dateien in Kursräume | B-09 |
| A-46 Material verbergen und zur Stunde freigeben | B-09 (Teil), B-20 |
| A-47 Eltern lesend in Kursräumen | B-20 |
| A-48 Wunschklassen ersetzen | B-34 |
| A-49 Lehrkraft bestimmt nur Tage und Höchststunden, faire Vertretung | B-02 (Deputat), B-34, B-36 |
| A-50 Verfügbarkeit mit Ausnahmen | B-35, B-42 |
| A-51 Sperrzeiten frei | B-02 (leere Regel), B-35, B-42 |
| A-52 schriftliche Entschuldigung → entschuldigt | B-29 |
| A-53 Fehlstunden und Verspätungen je Fach | B-31 |
| A-54 Stunden-Details im Plan | B-30, B-32 |
| A-55 Hausaufgaben eintragen | B-30 |
| A-56 abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“ | B-04, B-12 |
| A-57 Krankmeldungen in der Klassenansicht mit Nachweisstatus | B-29 |
| A-58 Krankheitsdaten nur für Berechtigte | B-06, B-29 |
| A-59 professionelle Designsprache, keine KI-Erklärtexte, weniger Schieber | B-10, B-11, B-13, B-23, B-43 |
| A-60 Hilfe per Verweilen, Rechtsklick, Antippen | B-10 |
| A-61 PC, Laptop, Tablet, Handy | Definition of Done, B-12, B-24, B-32, B-44 |
| A-62 Monitor modular und mobil | B-12, B-28, B-33 |
| Abteilungsleitung (Rückmeldung) | B-15, B-19 |

A-01 bis A-25 sind weitgehend umgesetzt; ihre Fehler aus der Bestandsprüfung stecken in B-03, B-05, B-07 und B-09.
A-63 bis A-66 betreffen die Arbeitsweise (dieses Dokument, `docs/AUTOPILOT.md`, `CLAUDE.md`).

---

## 12. Bewusst nicht im Umfang

| Thema | Grund |
|---|---|
| Eigener Zeugnisdruck mit amtlichen Formularen | Zeugnisse bleiben in SchILD-NRW/SVWS bzw. ASV; wir liefern Noten und Fehlstunden zu (B-52). Hohes Rechtsrisiko je Land und Schulform. |
| Laufbahnplanung und Kurswahl Oberstufe (Ersatz für LuPO) | Starkes Verkaufsargument, aber Belegungsregeln der APO-GOSt je Land sind ein eigenes Produkt; frühestens nach E6. |
| Klassengeld und Online-Bezahlung | Erfordert Zahlungsdienstleister, Kontoabgleich und Klärung der Haftung; Länder schreiben eigene Lösungen aus. |
| Mensa-Bestellung und Guthaben | Spezialanbieter (z. B. MensaMax) sind etabliert; Speiseplan als Mitteilung bzw. Link genügt. |
| Schulbuchausleihe | Landesabhängig, eigener Ablauf mit Barcode-Ausgabe; selten Kaufkriterium. |
| Geräteverwaltung und MDM | Fördervoraussetzung über Spezialanbieter; keine Kernaufgabe. |
| Videokonferenz | Anbindung per Link (Landesdienst oder BigBlueButton der Schule) genügt; Online-Sprechtag nutzt Links (B-48). |
| Office im Browser, gemeinsames Bearbeiten | Collabora/OnlyOffice beim Schulträger; Kursräume liefern Dateien. |
| H5P, Quiz, Lernpfade, E-Portfolio | Landes-Lernplattformen (Logineo, mebis) decken das ab; Verlinkung aus Kursräumen. |
| Native Apps in den Stores | Installierbare PWA mit Push (B-41) statt zweier nativer Apps. |
| Mehrsprachige Oberfläche inkl. Rechts-nach-links | Erst Briefübersetzung (B-55); vollständige Oberflächenübersetzung später. |
| Rückübersetzung von Elternantworten | Folgt frühestens nach B-55. |
| AG-, Projektwochen- und Differenzierungswahl mit automatischer Zuteilung | Sinnvoll, aber nicht verkaufsblockierend; späterer Ausbau. |
| Formular-Baukasten für das Sekretariat | Elternbrief-Rückmeldung (B-47) deckt die häufigsten Fälle ab. |
| Anonyme Umfragen | Namentliche Abfragen über Elternbriefe (B-47); anonyme Auswertung später. |
| Krisen- und Notfallkommunikation mit Räumungsliste | Baut auf Anwesenheit (B-31) und Push (B-41) auf; späterer Ausbau. |
| Praktikumsverwaltung über die Betriebsdaten hinaus | Ausbildungsbetriebe (B-39) genügen für den Start. |
| Aufnahme in den VIDIS-Katalog, Landes-Logins | OIDC-Grundlage besteht; Aufnahme ist Vertrag und Zertifizierung, keine Entwicklungsaufgabe dieses Backlogs. |
| Mehrere Schulen auf einer Instanz | Eine Instanz je Schule bleibt das Betriebsmodell. |
| Hosting-Zertifizierung (ISO 27001), Vertragswerk | Aufgabe des Betreibers; die Software liefert TOM-Beschreibung und Vorlagen (B-51). |
| Anwenderforum, Versionshinweise als Dienst | Organisatorisch; Änderungsprotokoll im Repository genügt vorerst. |
