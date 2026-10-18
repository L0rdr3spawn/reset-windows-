# Nutzer-Meldungen gegen den Code geprüft

Stand: 12.10.2026, geprüft am zusammengeführten Stand `7e09ba1` (Zweig `claude/magical-newton-dcni3v`).
Nur Lesen und Prüfen, keine Code-Änderung. Zugangsdaten sind absichtlich nicht enthalten.

## 0. Quellen und Grenzen (bitte zuerst lesen)

- **Lokaler Chat** (11.10. 14:56 bis 12.10. 17:13): alle 26 echten Nutzer-Nachrichten ausgewertet. Sie sind diktiert, ich habe sie sinngemäß gelesen. Kürzel in den Tabellen: **L 11.10.** usw.
- **Cloud-Chat `session_01AS141neeSnFBeFmjuHmnM9`: NICHT gelesen.** Claude in Chrome war nicht verbunden („Extension not reachable“). Ersatz: `UEBERGABE-PROMPT.md`, `docs/ANFORDERUNGEN.md` (A-01 bis A-69, die Wünsche vom 05.–11.10.), `docs/OFFENE-PUNKTE.md`, `docs/OFFENE-WUENSCHE.md` und die 59 Commit-Texte der Cloud-Sitzung. Kürzel: **C A-xx**. Die Nutzer-Wortlaute der Cloud-Sitzung sind darin nur zusammengefasst. Einzelne Meldungen können fehlen. Wenn Chrome verbunden ist, sollte der Chat noch einmal direkt gelesen werden.
- Kürzel **W** = `OFFENE-WUENSCHE.md` (Wunschliste vom lokalen Repo, 12.10.).
- Geprüft wurde im Code (Backend, Frontend, Tests gelesen). **Nichts wurde ausgeführt.** Was nur zur Laufzeit sichtbar ist (Layout, Server, Domain), steht als ❓.
- Der Server/die Domain wurde nicht angefasst.
- Bewertung: ✅ umgesetzt, 🟡 teilweise, ❌ fehlt, ❓ nicht prüfbar ohne Laufzeit.
- Achtung: `docs/OFFENE-PUNKTE.md` ist vom 11.10. (Cloud) und veraltet. Vieles von dort ist inzwischen gebaut (z. B. Klassenbuch, Kontowechsel). Ich habe deshalb den Code selbst geprüft.

## 1. Kurzfazit

Ausgewertet: 74 Einzelpunkte (nach Bereichen in §2).

| Status | Anzahl |
|---|---|
| ✅ umgesetzt | 34 |
| 🟡 teilweise | 24 |
| ❌ fehlt | 11 |
| ❓ nicht prüfbar | 5 |

**Wichtigste Befunde:**

1. **A/B-Wochen: der am häufigsten gemeldete Fehler ist nicht behoben (mindestens 4-mal: C A-28, A-29, A-67, A-68; L 11.10.; Übergabe-Prompt; W).** Die Buchstaben „A/B“ sind weg, und Woche 1 bis 52 mit 7 Tagen gibt es. Aber das Zyklus-Modell lebt weiter: Demo mit `cycle_weeks=2` (`schulmanager/demo.py:88`), „Zykluswoche k von N“ im Text (`calendar_utils.py:279-284`), „Wochenzyklus / Eigener Zyklus“ in der Oberfläche (`ClassPlanningFields.tsx:67`, `WeekPatternInput.tsx`), `Settings.cycle_weeks`. Der Nutzer will ausdrücklich keinen Zyklus mehr. Bei der Zusammenführung wurde die Cloud-Fassung sogar wiederhergestellt (Hand-back der Test-Agenten am 12.10.).
2. **Zeitraster je Klasse (Abendklasse ab 16 Uhr, A-69) fehlt komplett** (nur `Settings.period_times`, `models.py:405`).
3. **Klausur anklicken führt nicht in den Kursraum** (L 11.10.): kein Link in `ExamsPage.tsx`.
4. **Einchecken der Lehrkräfte und Mindeststunden-Kontrolle** (L 11.10.): fehlt.
5. **Krankmeldung Lehrkraft → Vertretung mit Material, „Klasse arbeitet selbst“** (W „Als Nächstes“): fehlt; das Recht `substitution.self_study` steht nur als „geplant“ in den Rechten.
6. **Demo-Simulation auf Knopfdruck** (L 12.10. 14:16): fehlt. Code-Schutz (Nuitka/Container-Image) fehlt ebenfalls.
7. Server/Domain/HTTPS: dreimal gemeldet (L 12.10. 12:26, 12:48, 16:12), von hier **nicht prüfbar**.
8. Gut umgesetzt: Klassenbuch, Förderinformationen (Nachteilsausgleich/Schulbegleitung), Hausaufgaben mit anonymer Abgabe, Noten, Beurlaubung, Zurücknehmen, „gemeldet – noch nicht entschuldigt“, Kontowechsel, Lizenzsystem, Ansichts-Konto (Zuschauer), Chats+Gruppen zusammen, Start+Übersicht zusammen.
9. Testlage laut Agenten-Berichten im Chat (nicht von mir geprüft): zuletzt 758 bestanden, 1 Fehler (CRLF in Skripten, per `.gitattributes` behoben). Drei Tests waren noch rot gemeldet: `test_register_flow`, `test_register_access_lead_vs_subject_teacher`, `test_substitution_demo::test_rhythm_classes_absent_on_their_days`. Der Klassenbuch-Test ist wichtig, weil er den Kernfluss absichert.

## 2. Meldung für Meldung

### 2.1 Stundenplan / Raster / Wochen

| # | Meldung (Quelle) | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 1 | **A/B-Wochen komplett weg, kein Zyklus-System** (mehrfach gemeldet: C A-28/29/67, Übergabe, W, L 11.10. 17:55) | 🟡 | Buchstaben weg; aber `demo.py:88` `cycle_weeks=2`; `calendar_utils.py:279-284` „Zykluswoche“; `ClassPlanningFields.tsx:67,80`; `WeekPatternInput.tsx`; `models.py:158-160,414` | Zyklus entfernen; Wochen nur als Nummern des Schuljahres („Woche 3, 7“, „jede 2. Woche ab 3“); Altdaten einmal umrechnen; Demo ohne Zyklus; Test auf verbotene Begriffe |
| 2 | Alle Wochen 1 bis 52 anzeigen, aktuelle Woche automatisch (L 11.10., C A-68) | ✅ | `WeekNav.tsx:1-6` (Auswahlliste aller Wochen, „Heute“), `CalendarWeek.tsx` | – |
| 3 | 7 Tage, Freitag/Samstag/Sonntag im Plan, Termine am Wochenende (L 11.10., C A-32/68) | ✅ | `CalendarWeek.tsx:5,261,310` (Sa/So immer, schraffiert, Trennlinie) | Schalter „nur Unterrichtstage“ prüfen |
| 4 | Feiertage/Ferien/freie Tage, von der Schule definierbar (L 11.10.) | ✅ | `models.py:22,290-299` `Holiday.kind`; `CalendarWeek` zeigt Ferien | Feiertags-Vorlagen je Bundesland fehlen (nur Vorschlag) |
| 5 | **Zeitraster/Tageslänge je Klasse** (Abendklasse ab 16 Uhr, eigene 1. Stunde) (L 11.10.; C A-69, A-31) | ❌ | nur global `Settings.period_times` (`models.py:405`); `SchoolClass` hat keine Zeiten | Zeitraster je Klasse; Konflikte nach Uhrzeit; Lehrkraft-Plan chronologisch |
| 6 | Doppelstunden nur in Pausenblöcken, keine Einzelstunde dazwischen/Lücke in der 1. Stunde (L 11.10. 19:14, C A-30) | 🟡 | `scheduler.py:179`, `models.py:450-475`, `test_scheduler_doubles.py` (Doppel nie über Pausen); `prefer_doubles=True` | Wunsch „2 Doppelstunden Englisch + 1 Einzelstunde“ und „erste Stunde frei“ nicht gesondert abgesichert (OFFENE-PUNKTE U-17) |
| 7 | Generator läuft automatisch bei Planänderungen (L 11.10. 15:50 und 17:55) | ✅ | `server/autoplan.py:1-30` (Auslöser, Job, Auto-Übernahme, `settings.auto_replan`), `test_autoplan.py` | Hinweis: Krankmeldungen ändern den Regelplan nicht, dafür rechnet die Vertretungs-Engine neu (bewusst). Prüfen, ob der Nutzer das so meint |
| 8 | Priorisieren: wenige Einzelstunden, viele Doppelstunden (L 11.10. 17:55) | 🟡 | `prefer_doubles`, `double_split`-Kosten `scheduler.py:554` | Wirkung nur mit Demo-Plan prüfen; Prioritäten-Tab (C A-34) unverändert „10 Schieber“ |
| 9 | Raster: Pausen „Pause 1, 2, 3“, dicke Striche an Pausen, Sa/So schraffiert (W) | ✅ | `CalendarWeek.tsx:261,310`, `TimetableGrid` | Aussehen nur im Browser prüfbar ❓ |
| 10 | Volle Lehrernamen und Raum in den Stundendetails, Klassenraum nicht doppelt (L 11.10. 20:20) | 🟡 | Kalenderwoche: `CalendarWeek.tsx:281,321` (`tName`) ✅; Regelplan-Seitenleiste `TimetablePage.tsx:~98` zeigt `cell.teachers.join` (Kürzel); `TimetableGrid.tsx:18` Kürzel | Im Regelplan ebenfalls volle Namen zeigen |
| 11 | Abkürzungen anklicken → Name (L 11.10. 20:20, C A-54) | 🟡 | siehe 10: nur in der Kalenderwoche | wie 10; auf der Klausurseite fehlt es |
| 12 | Vertretung im Stundenplan statt eigener Seite (L 11.10. 20:20) | 🟡 | Kalenderwoche zeigt Vertretungen (`CalendarWeek.tsx:3`), aber eigener Menüpunkt bleibt (`lib/permissions.ts:114`) | Menüpunkt zusammenführen oder Ansicht im Stundenplan als Reiter |
| 13 | Schülerliste im Stundenplan nach Klassen sortiert, nach Klasse suchbar (L 11.10. 20:20) | 🟡 | `TimetablePage.tsx:49` sortiert nach Name, Klasse nur als Zusatz | Nach Klasse gruppieren/filtern |
| 14 | Räume mit Typen/Tags, Fachräume nur für passendes Fach, Klasse aus Fachraum verdrängen (L 11.10. 20:20) | 🟡 | `Room.type` (`models.py:138-143`), `Subject.room_type` (`:101`), `Course.room_type` (`:209`), `test_substitution_rooms.py`, Auto-Planer repariert „Raum des richtigen Typs“ | Oberfläche zum Pflegen der Raumtypen/Tags prüfen; Verdrängung der Klasse aus Fachraum nicht belegt |
| 15 | Besondere Schulprinzipien: Kurssysteme jahrgangsübergreifend, Sonderstunden (Klassensprecher), Förderkurse nach Noten (L 11.10. 20:20) | 🟡 | `Course.students` (Teilmenge, `models.py:211`), Kurse über mehrere Klassen (`class_ids`), Zusatzmitglieder in Kursräumen | Klassengruppen/Bildungsgänge (C A-38/43) fehlen; Klassensprecher/in nicht vorhanden; Sonderstunde „einmal pro Monat“ fehlt |
| 16 | Tagesplan einzelner Klassen neu erzeugen, Plan „festschreiben“ (W) | ❓ | `fixed`/Fixieren je Stunde vorhanden (`TimetablePage`), Neuerzeugung je Klasse nicht belegt | prüfen |

### 2.2 Vertretung / Lehrkräfte

| # | Meldung | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 17 | Vertretung nur durch qualifizierte Lehrkräfte, sonst zuständige Lehrkraft (L 11.10. 20:20) | 🟡 | `substitution.py:538-540` `qualified` (Fach-Befähigung); Reihenfolge „qualifiziert → Mitbetreuung“ (`:18`) | Prüfen, ob „nicht qualifiziert“ hart ausgeschlossen ist oder nur schlechter bewertet wird |
| 18 | Abwesende Lehrkräfte statt „fehlende Klassen“ (C A-56) | ✅ | `AbsentTeachersCard.tsx`, Commit `e8a5906`, `test_substitution_b04.py` | Start/Monitor-Kennzahl laut OFFENE-PUNKTE ggf. noch alt |
| 19 | Lehrkräfte legen Arbeitstage/Zeiten fest, Rhythmus, Ausnahmen (L 11.10. 20:20; C A-50/51) | 🟡 | `teacher_profile.py:1-45` Zeitfenster mit `weeks`/`rhythm`, `Teacher.time_windows`, `times_self` (Freigabe) | Wiederholungen („jeden 1. Mittwoch im Monat“), einzelne Kalendertage fehlen; Zyklus-Abhängigkeit (siehe #1) |
| 20 | Pendeln: nur einmal hin und her, morgens länger brauchen (L 11.10. 20:20) | 🟡 | `Teacher.commutes` (Ja/Nein, `models.py:126`), globale Wegezeit `site_travel_periods` (`:417`) | Feinere Optionen je Lehrkraft (max. Wechsel pro Tag, Wegezeit je Standort) |
| 21 | **Einchecken der Lehrkräfte, Mindeststunden kontrollieren, Arbeitstage einhalten** (L 11.10. 20:20) | ❌ | keine Treffer für Check-in/Mindeststunden in Modellen und Routen; nur `max_hours` | Einchecken (Anwesenheit Lehrkraft), Soll/Ist-Stunden, Bericht |
| 22 | Standortwechsel den Lehrkräften anzeigen (W) | ❌ | nur Planungsgewicht `site_change` (`models.py:385`) | Hinweis im Lehrerplan zwischen zwei Stunden |
| 23 | Lehrkraft bestimmt nur Tage und Wochenstunden, nicht Vertretungsgrenzen; faire Verteilung (C A-49) | 🟡 | Fairness-Score vorhanden; `max_hours` ist im Profil änderbar (`PROFILE_FIELDS`), `max_subs_per_week` fest (`models.py:115`) | OFFENE-PUNKTE U-14, U-21 |
| 24 | Wunschklassen ersetzen durch Klassenleitung/unterrichtet/kann vertreten (C A-48) | ❌ | `preferred_classes` unverändert (`teacher_profile.py:48`) | umbauen |
| 25 | **Krankmeldung Lehrkraft: verpasste Stunden zeigen, Material hinterlegen, „Klasse arbeitet selbst / Vertretung / frei“, Altersgrenzen** (W „Als Nächstes“) | ❌ | `substitution.self_study` nur als „geplant“ in Rechten; kein Ablauf | Ganzen Ablauf bauen |
| 26 | Pausenaufsichten: Höfe, Bereitschaft, fair, Rasteransicht (W) | 🟡 | `duties.py` (faire Planung nach Deputat, Standort-Regel), Seite `/aufsichten` | Höfe „immer/nur bestimmte Pausen“, Bereitschaft durch Verwaltung, Raster-Ansicht nicht belegt |
| 27 | Rollen-Hierarchie Lehrkraft → Klassenleitung → Abteilungsleitung → Sekretariat/Schulleitung, Hausmeister (W) | ✅ | `permissions.py:27-36`, Seite `/rechte`, `docs/ROLLEN-RECHTE.md` | Rechte mit Status „geplant“ einbauen (W) |
| 28 | Mehrere Klassenleitungen (C A-42) | ❌ | überall nur `class_teacher` (z. B. `features_support.py:_may_edit`) | Liste von Leitungen |

### 2.3 Klassenbuch / Anwesenheit / Krankmeldung

| # | Meldung | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 29 | **Klassenbuch**: je Stunde Anwesenheit, Krankmeldungen schon sichtbar, zu spät, früher gegangen, Notiz (L 11.10. 17:55) | ✅ | `features_register.py:36` (`present/absent/late/left`), `:332` PUT, `:150` Tag, `:226` Übersicht; `RegisterPage.tsx`; Fehlzeiten landen als offene Fehlzeiten beim Kind (`:380-400`) | Tests `test_register_*` waren zuletzt rot gemeldet → klären |
| 30 | Klassenbuch-Zugriff: Fachlehrkraft nur eigene Stunden, Klassenleitung alles + Übersicht (W) | ✅ | `features_register.py` (Zugriff), `RegisterOverview.tsx`, Test `test_register_access_lead_vs_subject_teacher` (rot gemeldet) | Test reparieren |
| 31 | Verspätungen/Fehlstunden eintragen und entschuldigen (L 11.10. 17:55) | ✅ | `features_student_absences.py:61` Arten krank/verspaetung/frueh/fehlt/beurlaubung; Status `:55-58` | – |
| 32 | **Krank gemeldet ≠ entschuldigt** deutlich trennen (L 11.10. 20:20) | ✅ | `STATUS_LABELS`: „gemeldet – noch nicht entschuldigt“ (`:56`) | Eltern-Hinweis „liegt schon vor“ im Frontend prüfen ❓ |
| 33 | Schriftliche Entschuldigung macht Stunden „entschuldigt“; Abnahme durch Eltern/18-Jährige; vorgefertigtes Formular (L 11.10.; C A-52) | 🟡 | `GET /student-absences/form.pdf` (`:665`) ausfüllbares PDF; Status von Hand setzbar | Anerkennung setzt Stunden automatisch; Formular **je Schule/Bildungsgang anpassbar** (L 11.10.) fehlt |
| 34 | Krank melden **rückgängig** machen (L 11.10. 20:20) | ✅ | `students/components.tsx:172-183` „Zurücknehmen“ (`DELETE /student-absences/{id}`, `:554`) | – |
| 35 | **Beurlaubung** (Termin in der Schulzeit, auch durch Eltern) (L 11.10. 20:20) | ✅ | `KINDS` mit `beurlaubung`, Anlass Pflicht, nur im Voraus (`:410-414`), Status „beantragt/genehmigt/abgelehnt“ (`:65-67`) | – |
| 36 | Hinweis „unter 18 darf nicht selbst krank melden“ **nur** im Krankmeldungs-Bereich (L 11.10. 19:21) | ✅ | `student_self.py:86-91`, `ReportSickCard` (`components.tsx:122`) | – |
| 37 | Kalender: rot unten rechts Verspätung/Krank; Eltern sehen fehlende Entschuldigung (L 11.10. 20:20) | ✅ | `CalendarWeek.tsx:197-211` `AbsenceMarks`, Link „Entschuldigung einreichen“ | Layout im Browser prüfen ❓ |
| 38 | Legende („Pflichttermin, Termin, Klausur …“) unten entfernen (L 11.10. 20:20) | ✅ | keine Legende mehr im Frontend gefunden | – |
| 39 | **Nachteilsausgleich, Schulbegleiter, Dokumente (PDF) zu Schülern hinterlegen** (L 11.10. 17:55) | ✅ | `features_support.py` (4 Arten, Dateien verschlüsselt), `SupportSection.tsx`, `test_support.py` | Elternzugriff-Bereich prüfen |
| 40 | Schulbegleitung als eigene Rolle ohne Elternrechte (W) | ✅ | `permissions.py:54,271` | mehrere Kinder je Begleitung offen (W) |
| 41 | Fehlstunden **je Fach**, entschuldigt/unentschuldigt/verspätet zählen (C A-53) | ❌ | `/student-absences/record` (`:596`) liefert Liste, keine Auswertung je Fach | Auswertung je Fach und Art |
| 42 | Krankmeldungen in der Klassenansicht mit „eingesehen/anerkannt“ (C A-57) | 🟡 | Kachel „heute krank“, Status; `/klassenbuch` | Reiter in der Klasse, „eingesehen“ |
| 43 | Admin soll nicht sehen, wer krank war (Datenschutz, Übergabe §4.5) | ❓ | `absence_access.py` begrenzt; Audit-Eintrag laut OFFENE-PUNKTE U-111 offen | Audit-Log prüfen |

### 2.4 Kursräume / Hausaufgaben / Noten / Klausuren

| # | Meldung | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 44 | Hausaufgaben mit Frist (Datum + Uhrzeit), Abgabe, Lehrkraft sieht, wer abgegeben hat (L 11.10. 17:55; W) | ✅ | `features_channels.py:781,2947-3106` (Abgabe, Liste, Rückmeldung), Kalender `CalendarWeek.tsx:185` zeigt `abgegeben x/y` | – |
| 45 | **Abgabe anonym**: Schüler sehen keine fremden Abgaben (L 11.10. 17:55) | ✅ | `my_submission` nur `student_user_id` des Betrachters (`:2947-2965`); Liste nur für Lehrende (`:3043`); `homework_due` „nie Abgaben anderer“ (`:3321`) | – |
| 46 | Hausaufgaben im Stundenplan, Klick führt in den Kursraum (L 11.10. 20:20, mit Linkfehler laut W) | ✅ | `CalendarWeek.tsx:185-191` Link `?tab=aufgaben&aufgabe=`, `test_homework_links.py` | Link nur sichtbar mit Zugang (bewusst) |
| 47 | Noten vergeben, Schüler sehen Noten (L 11.10. 17:55) | ✅ | `features_grades.py` (`/exams/{id}/results`, `/grades`), `GradesPage.tsx` (`/noten`) | – |
| 48 | Tests/Klausuren im Stundenplan, über mehrere Stunden (L 11.10.; W) | ✅ | `CalendarWeek.tsx:116`, `features_exams.py:31` (`length` 1–8) | – |
| 49 | **Klausur anklicken → direkt in den Kursraum** (L 11.10. 20:20) | ❌ | `ExamsPage.tsx` ohne Link/Navigation; kein Bezug Klausur → Kursraum | Link von Klausur/Test zum Kursraum |
| 50 | Klausuren: Prüfung beim Speichern, eigene Arten, max. je Halbjahr (W; C A-33) | 🟡 | `exams.py:52-128` (max. pro Tag/Woche, Konflikte); Arten nur `klausur`/`test` | eigene Arten, Halbjahresgrenze fehlt |
| 51 | **Kursraum „Unterricht“**: nur stattgefundene Stunden, Anwesenheit grün/orange/rot, Material „neu“ bis geöffnet, Klick zu Material und Hausaufgabe (L 12.10. 15:35) | ✅ | `UnterrichtTab.tsx:1-5`, `features_channels.py:2829` | Praxis-Test im Browser ❓; „krank“ rot nur mit Klassenbuchdaten |
| 52 | Ordner/Dateien in Kursräume, Freigabe zur Stunde, Eltern lesend (C A-45–47) | ✅ | OFFENE-PUNKTE (geprüft R1), `test_channels*.py` | – |

### 2.5 Postfach / Chats / Start

| # | Meldung | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 53 | Start und „Meine Übersicht“ zusammenführen; ungelesene Nachrichten dort (L 11.10. 19:21) | ✅ | `students/module.tsx:28` (Weiterleitung `/meine-uebersicht` → `/`), `OverviewPage.tsx:69-109` | – |
| 54 | Chats und Gruppen in einem Bereich (L 11.10. 20:20) | ✅ | `chats/module.tsx:20` „Chats & Gruppen“ | Postfach bleibt getrennt (gewollt?) |
| 55 | Neue Nachrichten im Chat **untereinander statt übereinander** (L 11.10. 20:20) | ❓ | nur Layout-Fehler, im Code nicht eindeutig prüfbar (`chats.css`) | im Browser (Handy + PC) prüfen |
| 56 | Mobil nutzbar, Sicherheit/Datenschutz (L 11.10. 20:20) | 🟡 | `PrivacyPage.tsx` (`/datenschutz`), Browser-Prüfung 390 px laut Doku | Datenschutzseite „neu und professionell“ (W); mobile Tabellen (U-81) |
| 57 | Chat-Regeln: 1 Monat Aufbewahrung, Stern, Meldungen extern speichern, Prüfung nur mit Zustimmung (W) | 🟡 | `feature_models/chats.py` (`chat_reports`), `ModerationPage.tsx` | Aufbewahrung/Löschen/Stern nicht belegt |

### 2.6 Konten / Rechte / Login

| # | Meldung | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 58 | **Mehrere Konten, Kontowechsel** (mehrfach: C A-26, L 12.10. 16:12) | ✅ | `AccountSwitcher.tsx`, `auth.py:130-251` (bis 5 Konten), `test_multi_account.py` | – |
| 59 | **Demo-Rollenwahl auf der Login-Seite entfernen**, Demo-Zugänge nur vom Inhaber (L 12.10. 14:16) | ✅ | keine Rollen-Knöpfe mehr im Frontend; `config.py:76-79` (`demo_all_accounts`, `demo_public=False`) | – |
| 60 | **Ansichts-Konto („Restricted Admin“: alles sehen, nichts ändern)** (L 12.10. 12:26) | ✅ | Rolle `zuschauer` (`permissions.py:27`), `tests/test_viewer_role.py` (alle Änderungen → 403) | – |
| 61 | Demo-Accounts für alle Rollen, PDFs beim Anlegen von Konten/Klassen (L 12.10. 13:39) | ✅ | `demo_loader.py`, `letters.py`, `AccessLettersPage.tsx`, Zugangsbriefe als PDF | – |
| 62 | **Demo-Simulation** (Nachrichten, Newsletter, Klassenwechsel, neue Klassen, Zu-/Abgänge auf Knopfdruck) (L 12.10. 14:16; W) | ❌ | keine Simulationsfunktion im Code (nur Generator-Seed) | Szenario-Knöpfe, nur für Inhaber/Demo |
| 63 | Mehrere Schulen je Konto (Eltern mit zwei Schulen) (W) | ❌ | kein Schulbezug am Konto in `db_models.py` | später |
| 64 | Anmeldedaten stimmen nicht (L 11.10. 15:38) | ❓ | Laufzeit/Server; nicht prüfbar | Nach Neuaufsetzen einmal Login-Liste testen |
| 65 | Passkeys / Passwort-Manager (C A-27) | 🟡 | `autocomplete`, TOTP, Login-Sperre vorhanden | Passkeys fehlen |
| 66 | Klassen anlegen mit Konten und Zugangs-PDFs, Erst-Passwort (C A-19/20/23) | ✅ | OFFENE-PUNKTE „erledigt“, `NewClassPage`, `letters.py` | Listen-Import Spalten (U-33) |
| 67 | Kontakt/Passwort vergessen, SSO (C A-18/21/22) | 🟡 | `features_contact.py`, `features_sso.py` | SMS im Docker-Betrieb (U-09), Klassengruppen (A-43) |

### 2.7 Monitor, Server, Lizenz, Betrieb

| # | Meldung | Status | Beleg | Noch zu tun |
|---|---|---|---|---|
| 68 | Monitore je Standort einstellbar, modular, mobil (C A-62; W) | 🟡 | `MonitorAdminPage.tsx` (`/monitore`), `test_monitor_config.py` | Mobil abgeschnitten (U-37), Kacheln/Profile |
| 69 | **Lizenzsystem** (Online-Prüfung, signiert, Nur-Lesen bei Sperre) (L 12.10. 14:16) | ✅ | `server/licensing.py`, `lizenzserver/`, `LicensePage.tsx`, `tests/test_license.py` | Betrieb des Lizenzservers extern prüfen |
| 70 | **Code muss verschlüsselt/geschützt ausgeliefert werden**, rechtlich (EULA, Patent) (L 12.10. 14:16; W) | ❌ | kein Nuitka/Cython im `Dockerfile`/`Makefile` | Container-Image mit kompiliertem Python; EULA/Anwalt; Patent nicht mit „Software als solcher“ in der EU |
| 71 | Infrastruktur für tausende Nutzer, schnelle verschlüsselte Chats (L 12.10. 14:16) | 🟡 | PostgreSQL in `docker-compose.yml:55,184`; Verklemmung behoben, 150 Nutzer lokal ok (W); Verschlüsselung `crypto.py` | Chat-Liste N+1, Indizes `chat_messages(chat_id,id)`, Ungelesen-Zähler, Lasttest mit tausenden |
| 72 | **Server online, HTTPS-Domain erreichbar** (mehrfach: L 12.10. 12:26, 12:48, 16:12) | ❓ | Serverzugriff war nicht erlaubt | Erreichbarkeit/Zertifikat extern prüfen |
| 73 | Import aus anderen Programmen (C A-01; W) | 🟡 | Untis GPU, CSV, JSON, Schulmanager-Online | SchILD/ASV/LUSD/OneRoster/Moodle |
| 74 | Einrichtungs-Assistent, saubere Instanz (W) | ✅ | `SetupPage.tsx` (`/einrichtung`), `routes/setup.py`, `test_setup.py` | – |

## 3. Was noch fehlt / was mir auffällt (Vorschläge von mir, nicht vom Nutzer)

1. **Einheitliche Begriffe**: Die Hilfs- und Fehlermeldungen sagen „Zykluswoche“, „Wochenzyklus“ (`calendar_utils.py`, `ClassPlanningFields.tsx`, `ical.py:457`, `untis_gpu.py`). Ein Test sollte alle verbotenen Wörter in Oberfläche, Demo, Meldungen und Doku verbieten (Ansatz: `noWeekLetters.test.ts`).
2. **Anrede-Inkonsistenz**: `student_self.py:89` spricht Schüler mit „Du“ an, der Rest (Personal) mit „Sie“. Das ist vermutlich gewollt, sollte aber in `DESIGN.md` festgehalten sein.
3. **Rechte „geplant“ noch nicht eingebaut** (W): `masterdata.read`, `register.read_all`, `support.read`, `substitution.self_study`, `duties.manage`, `exam.types.manage`, `chats.review`, `license.manage`. Solange sie nur in der Matrix stehen, ist ihr Name irreführend.
4. **Klassenbuch ↔ Unterricht ↔ Fehlzeiten**: Ein Eintrag soll an einer Stelle gepflegt werden. Prüfen, ob Verspätung im Klassenbuch auch in der Kalenderansicht (rot unten rechts) und im Kursraum („orange“) identisch erscheint. Ein Ende-zu-Ende-Test über alle drei Stellen fehlt.
5. **Datenschutz**: Zugriff auf Krankheitsgründe, Nachteilsausgleich und Atteste sauber begrenzt, aber: Audit-Protokoll für Admin (U-111), Aufbewahrungsfristen (U-61), DSGVO-Auskunft „vollständiger und kompakter“ (W). Außerdem ein Verzeichnis der Verarbeitungstätigkeiten und Auftragsverarbeitungsvertrag als Vorlage für verkaufende Schulen.
6. **Lehrkraft-Kontrolle** statt nur Einstellungen: Einchecken, Soll/Ist-Stunden und Hinweise bei Überschreitung gehören zusammen (Meldung #21).
7. **Demo-Betrieb**: Wenn Demo-Simulation kommt, muss sie strikt getrennt von echten Daten laufen (eigene Mandanten-/Demo-Flag-Kennzeichnung), damit eine Lizenz-Schule keine Demo-Daten im Echtbetrieb sieht.
8. **Barrierefreiheit** (Kontrast, Tastatur, Screenreader) ist für Schulen oft Pflicht; bisher nur teilweise (U-79).
9. **Backup-Wiederherstellung testen** (Restore-Test), nicht nur Sicherung. Skripte brauchen LF-Zeilenenden; `.gitattributes` ist inzwischen da (`7e09ba1`).
10. **Tests rot gemeldet** (Klassenbuch, Demo-Rhythmus-Klassen): vor dem nächsten Release reparieren. Der Demo-Test erwartet Klassen „10X/10Y“, die Demo hat „10P/9P“, das spricht für zwei Demo-Fassungen im Zusammenführungsstand.
11. **Zwei Wochenmodelle**: Lokaler Zweig und Cloud-Zweig hatten verschiedene Modelle (Rhythmus/„every, anchor“ vs. `weeks=[0]/[1]`). Die Zusammenführung hat das Cloud-Modell gewählt. Wenn der Zyklus entfällt (#1), muss das beim Aufräumen sauber aus beiden Fassungen entfernt werden.
12. **Mehrfachmeldungen vermeiden**: Eine einfache Abnahmeliste („Meldung → Test → grün“) pro Nutzer-Meldung, damit nichts mehr wiederholt gemeldet werden muss. Diese Datei kann dafür die Grundlage sein.

## 4. Priorisierte To-do-Liste

**A. Mehrfach gemeldet / gravierend (zuerst)**

1. A/B- und Zyklus-System komplett entfernen (#1). Wochen nur als Nummern des Schuljahres, Altdaten umrechnen, Test auf verbotene Begriffe.
2. Server online und HTTPS-Domain prüfen und stabil halten (#72), danach Login-Daten neu prüfen (#64).
3. Rote Tests reparieren, besonders Klassenbuch (#29, #30), danach volle Testsuite.
4. Zeitraster je Klasse (A-69) mit Konflikten nach Uhrzeit (#5).

**B. Einmal gemeldet, fehlt**

5. Klausur/Test anklicken → Kursraum (#49).
6. Lehrkraft einchecken und Mindeststunden (#21).
7. Krankmeldung Lehrkraft → Vertretung mit Material und „selbst arbeiten“ (#25).
8. Fehlstunden je Fach und Art (#41).
9. Entschuldigungsformular je Schule/Bildungsgang anpassbar, Anerkennung setzt „entschuldigt“ (#33).
10. Demo-Simulation auf Knopfdruck (#62).
11. Code-Schutz im Auslieferungsimage und rechtliche Grundlagen (#70).

**C. Teilweise, nachziehen**

12. Volle Lehrernamen und Klick auf Kürzel überall, auch Regelplan und Klausurseite (#10, #11).
13. Vertretung als Teil des Stundenplans, Menüpunkt zusammenführen (#12).
14. Schülerliste nach Klassen gruppieren (#13).
15. Mehrere Klassenleitungen, Klassengruppen, Klassensprecher/Sonderstunden (#15, #28).
16. Pendeln feiner einstellbar, Standortwechsel anzeigen (#20, #22).
17. Wunschklassen durch Klassenleitung/unterrichtet/kann vertreten ersetzen (#24).
18. Chat-Layout am Handy prüfen (#55); Chat-Aufbewahrung (#57).
19. Skalierung: Indizes, N+1, Lasttest (#71).

**D. Später**

20. Mehrere Schulen je Konto (#63), Passkeys (#65), weitere Import-Formate (#73), Barrierefreiheit.
