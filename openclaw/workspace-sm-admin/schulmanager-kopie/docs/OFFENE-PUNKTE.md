# Offene Punkte – verbindliche Liste

Stand: 11.10.2026, Runden 1 und 2 abgeschlossen und geprüft. Zusammengeführt aus
`docs/code/01`–`09` (jeweils §8 Unstimmigkeiten, §9 Anforderungen), der Analyse der Auftraggeber-Punkte vom 10.10. und
Code-Stichproben am 11.10. Anforderungen im Wortlaut: `docs/ANFORDERUNGEN.md`; Pakete und Abnahmekriterien:
`docs/PRODUKT-BACKLOG.md` (B-xx); Pflege-Routine: `docs/code/README.md` §5.

Regeln für diese Datei:
- Status je Anforderung: **erledigt** | **teilweise** | **fehlt** | **in Arbeit** (gebaut, Prüfung oder Integration läuft).
- Unstimmigkeiten haben feste IDs **U-xx**, die nie neu vergeben werden. In Klammern steht die Herkunft
  (Bereichsdatei + Bereichskennung, z. B. „06 U1“; „Analyse“ = Auftraggeber-Analyse vom 10.10.). Behobenes wird mit Runde
  und Test markiert und nach dem Commit nach §2.4 verschoben.
- Neue Befunde bekommen die nächste freie ID (zurzeit **U-117**).

**Überblick:** 70 Anforderungen – 27 erledigt, 29 teilweise, 0 in Arbeit, 14 fehlen. 101 offene Unstimmigkeiten aus dem
Abgleich (10 hoch, 38 mittel, 53 niedrig) + U-102 … U-110 aus der Prüfrunde 1.

## 1. Stand je Anforderung

| ID | Anforderung (kurz) | Status | Nachweis | Was fehlt | Paket |
|---|---|---|---|---|---|
| A-00 | Verkaufbares Komplettprodukt | teilweise | Kern A-01–A-25 weitgehend fertig; Betrieb: Image, Compose, systemd, Backup-Sidecar, Monitoring, CI/Release, BETRIEB/SICHERHEIT (09) | offene Pflichtpunkte dieser Tabelle; Betriebsfehler U-09, U-10, U-44; In-App-Sicherung ohne Dateien; E2–E6 | alle; B-05, B-49–B-51 |
| A-01 | Import/Export mit Fremdsystemen | teilweise | Untis GPU001–015 Export/Import, Schulmanager-Online-Paket, CSV mit Vorlagen SchILD-NRW/ASV/LUSD/Magellan, JSON mit Probelauf (`integrations/*`, `features_exchange.py`, `ImportExportPage`) | Geburtsdatum (U-20); kein SchILD/ASV-Rückexport; GPU014-Import überspringt Verlegungen/Aufsichten/Klausuren; Untis-Import ohne Vorschau der Zuordnung | B-03, B-17, B-52 |
| A-02 | Pläne für ~2500 Schüler/innen | erledigt | `scheduler.generate_best_of` (Mehrprozess), Job-Prozess `jobs.py`, `GeneratorPanel`; Demo 2644/169/99; `test_core`, `test_substitution_demo` | Lasttest, Generator nur mit kleiner Demo getestet | B-58 |
| A-03 | Live-Umplanung bei Krankheit | erledigt | `compute_day_plan` je Version, `/absences`, SSE `change.dates`, `AbsenceModal`; `test_absence_changes_plan_and_publishes_event` | – (Benachrichtigungsfehler U-46) | – |
| A-04 | Stundentafel je Klasse | erledigt | `Curriculum`, `CurriculaEditor`, `POST /planning/courses-from-curricula` | – | B-01 |
| A-05 | Ausfälle an den Tagesrand | erledigt | `policy.edge_strategy/middle_strategy`, `try_shift`, `WeightsPanel` | – | – |
| A-06 | Web-Oberfläche für alle Rollen | erledigt | 8 Rollen, `App.tsx`, `NAV_ITEMS`, Feature-Module | – | – |
| A-07 | Krankmeldung über die Seite | erledigt | Lehrkraft `POST /absences/report-self` (`SelfReportModal`); Familie `POST /student-absences` (`ReportForm`, `ReportSickCard`) | – | – |
| A-08 | Lehrerkonto pflegt Fächer, Klassen, Stunden, Tagesbeginn | erledigt | `TeacherProfilePage`, `features_teacher_profile.py` (Zeitfenster → Sperrzeiten), Stammdaten-Editor | Deputat soll laut A-49 nicht selbst gesetzt werden (U-14); Muster laut A-50 | B-34, B-35 |
| A-09 | Lehrkräfte nur eigene Fächer/Klassen | teilweise | Scopes `own_classes`/`own_courses` in allen Routern (`test_teacher_scope.py`), Frontend `filterAllowed`; Cache-Leck behoben, „Kein Zugriff“ im Rahmen (R2-D, `lib/session.ts`, `AccessGate`) | `/data/exams` (U-05), `teacher_id` ohne Rollenprüfung (U-26), übrige laut §2 | B-06, B-13, B-02 |
| A-10 | Kursräume mit Ordnern, Freigabe zur Stunde | erledigt | `features_channels.py`, `channels/*`; `test_channels*.py` | eigener Kursraum ohne Mitglieder (U-08) | B-09, B-20 |
| A-11 | Schülerübersicht mit Plan und Krankmeldung | erledigt | `/me/today`, „Meine Übersicht“, `FamilyPanel`; Selbstmeldung nur volljährig (`users.adult`) | Volljährigkeit uneinheitlich (U-25), gemerktes Kind (U-36) | B-07 |
| A-12 | Atteste und Dokumente einreichen | erledigt | `POST /student-documents` (Attest, Entschuldigung, Einverständnis), `/dokumente`, „Meine Übersicht“ | Export-Leck (U-03), Volljährigkeit (U-25) | B-07 |
| A-13 | Internes Postfach, verschlüsselt | erledigt | `features_messages.py`, `messages/*`; `test_messages.py` (kein Klartext, Rotation) | Empfängerkreis zu weit (Bestandsprüfung), Aufbewahrung nicht in der Wartung (U-61) | B-08 |
| A-14 | Vorschau mit Demo-Konten | erledigt | `.devcontainer`, `scripts/preview.sh`, Demo-Konten, Test-Postausgang, Test-Anbieter, `VORSCHAU.md` | Vorschau-Risiken U-29, U-30 (Vorschau-Adressen nicht teilen) | B-21 |
| A-15 | Klassenraum je Klasse | erledigt | `PATCH /classes/{id}` mit Übernahme in den Plan, Stammdaten `home_room` | – | – |
| A-16 | Klasse suchen, Personen sehen | erledigt | `/klassen` (Suche), Detail mit Klassen-/Fachlehrkräften und Schüler/innen | – | – |
| A-17 | Klassen-Wochenplan, „findet nicht statt“ | erledigt | `GET /classes/{id}/week`, `not-taking-place` mit Vorschau und Umplanung, `WeekTab` | Zurücknehmen mit Begleitungen nicht atomar (U-95) | – |
| A-18 | E-Mail/Handy, Passwort zurücksetzen | teilweise | `/me/contact`, „Passwort vergessen“ per Link/Code, Admin-Pflege + `send-reset`; `test_contact.py` (40) | im Docker-Betrieb kein SMS-Anbieter einstellbar (U-09); keine Oberfläche für SMTP/SMS | R2-A, B-49 |
| A-19 | Ganze Klassen, Zugangsdaten als PDF | erledigt | Klassen-Assistent, Massenanlage, Stapel (Sammel-PDF, ZIP, Einzel-PDF, E-Mail) | Listen-Import ordnet Spalten falsch zu (U-33) | B-18 |
| A-20 | Neues Passwort beim ersten Anmelden | erledigt | `must_change_password`, Guard → `/passwort` | – | – |
| A-21 | Microsoft/Apple/Google verbinden | erledigt | `features_sso.py`, `anmeldedienste/*` (Verbinden, Einrichtung über die Oberfläche); `test_sso.py`; `SM_SSO_*` jetzt auch über Compose/systemd wirksam (R2-A, `test_ops_config.py`) | – | R2-A |
| A-22 | Anmeldewege je Person/Klasse/Gruppe | teilweise | Richtlinien Person > Klasse > Jahrgang > Rolle × Schüler/Eltern, Bericht, `/konten-verbinden`; `test_login_policy.py` | Klassengruppen (A-43); „wer darf ein Konto erstellen“ nur als E-Mail-Zuordnung (U-96); API-Tokens umgehen die Methodenwahl (U-02) | B-19, B-21 |
| A-23 | Konten beim Klassen-Anlegen, PDF per E-Mail | erledigt | `POST /classes` mit Konten, Startpasswort und sofortigem Versand (`AccountOptionsForm`) | – | – |
| A-24 | Passwort auf Startpasswort zurücksetzen | teilweise | `PasswordPanel` (Startpasswort oder selbst setzen), `POST /users/{id}/password`; Lehrkräfte als Klassenleitung (`passwords.reset`) | nur eine Klassenleitung (A-42); zwei Reset-Wege uneinheitlich, Stapel erlaubt eigenes Konto (U-70) | B-19, B-05 |
| A-25 | Passwortfeld mit Auge | erledigt | `components/PasswordInput.tsx` (19 Verwendungen) | – | – |
| A-26 | Mehrere Konten, Wechsel | fehlt | ein Cookie `sm_session`, `AuthContext` kennt ein Konto | Kontenwechsler; vorher U-01 beheben | B-21 |
| A-27 | Passwort-Manager, fälschungssicher | teilweise | `autocomplete`, `type=password`, HttpOnly-Cookie, CSRF, TOTP, Login-Sperre; API-Token nur für das eigene Konto, Laufzeit begrenzt (R2-B) | Passkeys, Geräte-Token, Klartext-Token (U-28) | B-21, R2-B |
| A-28 | Woche 1…52, Feiertage | erledigt | Ferien/Feiertage (`holidays`), Wochenangaben jede Woche / ausgewählte Wochen / Rhythmus (k beliebig) | Feiertagsarten/Vorlagen | B-25, B-45 |
| A-29 | Rhythmus je Klasse an der Stundenplan-Stelle | erledigt | Wochenangaben je Regel, Kurs, Stunde, Aufsicht; kein globaler Wochenrhythmus mehr | – | B-45 |
| A-67 | Wochenbuchstaben komplett durch Wochenangaben ersetzen (jede Woche / ausgewählte Wochen / Rhythmus, Woche 1 … 52) | erledigt | 52-Wochen-System (`weeks.py`, `legacy.py`) | – | R3-A (Vorrang) |
| A-68 | Alle Wochen 1–52 anzeigen (auch Ferien), jede Woche 7 Tage | erledigt | Wochenwahl 1–52, KW-Anzeige, Sa/So planbar und sichtbar | – | R3-A (Vorrang) |
| A-69 | Tageszeiten/Zeitraster je Klasse (Abendklasse ab 16 Uhr, eigene 1. Stunde), Lehrkraft früh + abends richtig | fehlt | nur globales `Settings.period_times`; Lehrkraft-Zeitfenster für Abendunterricht | Zeitraster-Vorlagen je Klasse, Konflikte nach Uhrzeit, Lehrkraft-/Raumplan chronologisch | R4-A (Vorrang) |
| A-30 | Doppelstunden zwischen den Pausen | fehlt | nur „Doppelstunde bevorzugt“ je Fach/Kurs | Generator beachtet Pausen nicht (U-06); Doppel + Einzel am selben Tag (U-17) | B-02, B-11 |
| A-31 | Zeitraster frei einstellbar | teilweise | `period_times`, `period_minutes`, `breaks` mit Minuten | Rechner Beginn + Länge + Pausen, Überlappungsprüfung (U-16), Pausen-Grenze (U-82) | B-02, B-16, B-22 |
| A-32 | Einstellungen am Ort, Wochenende bei Terminen | teilweise | Schultage 1–7 global | eigene Einstellungsseite, Sa/So nur bei Terminen, 7 Tage ohne Namen (U-49) | B-16, B-22, B-26, B-32 |
| A-33 | Max. Klassenarbeiten je Klasse und Halbjahr | fehlt | nur je Woche/Tag; 0 wirkt wie 1 (U-50) | Halbjahresgrenzen, Prüfung, Übersicht | B-02, B-27 |
| A-34 | Prioritäten-Tab verständlich | fehlt | `WeightsPanel` unverändert (10 Schieber + Erklärsätze) | Umbau zu „Optimierung“ (U-40) | B-11 |
| A-35 | Stundentafel reparieren | erledigt | R1-U1 (geprüft, 5ff05e4+): Überschneidung → 409/`force`, `curriculum_overview`, Warnung leere Tafel, Fach doppelt → 422, `pinned`, „zu viel verplant“, Editor mit Vorschau; `test_curricula.py` (17), `curricula.test.ts` (8) | Rest siehe U-52 (Kurse mit Wochenangabe zählen anteilig); Übersicht außerhalb des Editors (U-102) | B-01 |
| A-36 | Eigene Fächer, auch durch Lehrkräfte | teilweise | R1-U1 (geprüft, 5ff05e4+): `NewSubjectDialog` (Stundentafel), Stammdaten; Fachvorschlag `new_subjects` im Lehrerprofil → Antrag → Anlage bei Genehmigung (`TeacherProfilePage`, `features_teacher_profile.py`) | Lehrerkonto ohne verknüpfte Lehrkraft kann kein Profil anlegen (409); „auf vorhandenes Fach abbilden“ | B-01, B-34 |
| A-37 | Konfig-Dateien je Bereich | teilweise | JSON gesamt, CSV je Sammlung inkl. Sperrzeiten/Zeitfenster | Konfigurationspaket je Bereich mit Probelauf; Geburtsdatum (U-20) | B-03, B-17 |
| A-38 | Klassentypen, Bildungsgänge, eigene Namen | fehlt | nur freie Klassen-ID/-Name, Jahrgang 0–20 in `/data` (Klassen-Assistent 1–13, U-32) | Bildungsgänge, Klassentypen, Namensmuster | B-14 |
| A-39 | Automatische Versetzung | fehlt | – | Schuljahreswechsel mit Probelauf | B-37 |
| A-40 | „Gilt für Jahrgang“ → eigene Klassen | teilweise | R1-U1 (geprüft, 5ff05e4+): „Gilt für Klassen“ vorn, Jahrgänge optional, Vorrang Klasse > Jahrgang | Gruppen/Bildungsgänge (A-38, A-43) | B-01, B-14 |
| A-41 | Klassenleitungen, Sprecher/in, Verwalter, Eltern | teilweise | Assistent: eine Klassenleitung, bis 2 Eltern je Schüler/in | mehrere Leitungen, Sprecher/in, Verwalter; Elternangaben ohne Konto gehen verloren (U-31) | B-15, B-18, B-19 |
| A-42 | Mehrere Klassenleitungen | fehlt | überall genau `class_teacher` (≥ 16 Stellen) | Liste von Leitungen in Modell und Rechten | B-15, B-19 |
| A-43 | Gruppen von Klassen | fehlt | – (`login_policy.MEMBER_SCOPES` als Erweiterungspunkt) | Klassengruppen für Stundentafeln, Rechte, Postfach, Richtlinien | B-14, B-19 |
| A-44 | Eltern-Kind, Volljährigkeit, Elternfreigabe | teilweise | `parent_links` (n:m); Baustein `parent_access` (R1-U2, in Prüfung): Volljährigkeit aus `birth_date`, Einwilligung je Bereich, `GET/PUT /parent-access`, Profil-Abschnitt; Kursräume angebunden (`test_channels_parents.py`); Krankmeldungen über Elternfreigabe, Selbstmeldung Volljähriger nach Geburtsdatum (R2-B) | Dokumente und Stundenplan über `parent_may_see` (U-04, U-24, U-25, U-103) – R3-B | B-03, B-07, B-18 |
| A-45 | Ordner und Dateien in Kursräume | erledigt | R1-U2 (geprüft): `folders/tree`, `items/files`, `MaterialUpload` (sofort als Material, ganze Ordner per Auswahl/Ziehen), Fachformate; `test_channels_rooms.py` (24) | Ordner verschieben/sortieren in der Oberfläche; leere Unterordner werden nicht angelegt | B-09 |
| A-46 | Material verbergen, zur Stunde freigeben | erledigt | R1-U2 (geprüft): verborgen/ab Zeitpunkt/zur (nächsten) Stunde für Material und Ordner, Entfall und Ferien verschieben (`Clock`) | „nur für Schüler/innen“, Hinweis an die Lehrkraft bei Entfall | B-20 |
| A-47 | Eltern lesend in Kursräumen | erledigt | R1-U2 (geprüft): Rolle `parent` (`channels.view_children`), Kind wählen, nur Freigegebenes | Eltern-Einsicht je Raum abschaltbar (Wunsch, nicht Anforderung) | B-20 |
| A-48 | Wunschklassen ersetzen | fehlt | Profil und Stammdaten pflegen `preferred_classes` („Wunschklassen“, U-57) | Klassenleitung / unterrichtet / kann vertreten | B-34 |
| A-49 | Lehrkraft nur Tage + Wochenstunden, faire Vertretung | teilweise | Score mit Wochenhistorie; Profil ohne Vertretungsgrenzen | Lehrkraft setzt Deputat selbst (U-14); starre `max_subs_per_week/day`; Fairness nur je Woche (U-21) | B-02, B-34, B-36 |
| A-50 | Arbeitszeitfenster mit Rhythmus und Ausnahmen | teilweise | Zeitfenster je Tag und Woche bzw. Rhythmus | Wiederholungen (monatlich, jede n-te Woche), Ausnahmen, Datumsbezug | B-35, B-42 |
| A-51 | Sperrzeiten frei bis zur Stunde | teilweise | `TimeRule` Woche × Tag × Stunde (Stammdaten), Wünsche im Profil | leere Regel sperrt alles (U-15); einzelne Kalendertage; Lehrkräfte selbst nur Wünsche | B-02, B-35, B-42 |
| A-52 | Schriftliche Entschuldigung → entschuldigt | teilweise | Status „entschuldigt“ von Hand, Dokumentart „Entschuldigung“ | Anerkennung setzt die Stunden auf entschuldigt | B-29 |
| A-53 | Fehlstunden je Fach, Verspätungen | fehlt | nur Liste der Meldungen; Familie sieht nur 14 Tage (U-89) | Anwesenheit je Stunde, Auswertung | B-31 |
| A-54 | Stunden-Details im Plan | teilweise | `CellDetails` (Fach, Zeit, Raum, Kurs), Klassen-Wochenplan mit Status | volle Lehrernamen, „findet statt“, Hausaufgaben, Details auch ohne Planrecht | B-30, B-32 |
| A-55 | Hausaufgaben eintragen | teilweise | Kursraum-Aufgaben mit Frist und Abgabe | Hausaufgabe an der Stunde, sichtbar im Stundenplan | B-30 |
| A-56 | Fehlende Lehrkräfte getrennt, keine „fehlenden Klassen“ | teilweise | „Abwesende Lehrkräfte“ getrennt in Vertretung und Druck; R2-A: `absent_teacher_details`/`absent_class_details`, Karte „Abwesende Lehrkräfte“ mit Filter, keine „Abwesenden Klassen“ in Vertretung und Druck, Wandertag eine Zeile, Druck öffentliche Sicht (`test_substitution_b04.py`) | Start-Kennzahl und Monitor (U-11-Rest) – B-12/R3-D | B-04, B-12 |
| A-57 | Krankmeldungen in der Klassenansicht | teilweise | Status + Attest-Zustand, Dokumentstatus, Kachel „heute krank“ für die Klassenleitung | Reiter in der Klasse, „eingesehen“, Anerkennung durch Klassen-/Abteilungsleitung | B-29 |
| A-58 | Krankheitsdaten nur für Berechtigte | teilweise | Gründe verschlüsselt, nur meldende Person, Familie, Personal ohne Scope, Klassenleitung; Atteste nicht für Fachlehrkräfte; R2-B: `absence_access.py` (Klassenleitung, Sekretariat, Schulleitung voll; Fachlehrkraft nichts bzw. Schalter „presence“; Admin ohne Recht; Eltern Volljähriger nur mit Freigabe), `test_student_absence_access.py` | Freigabe an einzelne Lehrkräfte; Audit-Protokoll zeigt Admin Krankmeldungs-Einträge (U-111) | B-06, B-07, B-29 |
| A-59 | Professionelle Designsprache | teilweise | R1-D1 (geprüft): `DESIGN.md`, Tokens hell/dunkel, Komponenten, `designRules.test.ts`; Login, Start, Profil ohne Erklärabsätze | Erklärtexte (U-39), Schieber (U-40), Inline-Styles (U-80), Emojis (U-92), Anrede (U-41) | B-11, B-23, B-43 |
| A-60 | Hilfe nach 2 s, Rechtsklick, Antippen | teilweise | R1-D1 (geprüft): `lib/help.ts`, `components/Help.tsx`, `Field hint` → Hilfe, „Hilfetexte immer anzeigen“; `help.test.ts`, Browser geprüft | übrige Seiten auf Hilfe umstellen (U-39) | B-23, B-43 |
| A-61 | PC, Tablet, Handy | teilweise | R1-D1 (geprüft): Navigation je Gerät, 44-px-Ziele; 390 px ohne Seiten-Scroll (70 Aufrufe in 05/06/08) | Tabellen als Karten (U-81), Breakpoints (U-80), Überlauf „Meine Übersicht“ (U-42), Tastatur (U-79) | B-12, B-24, B-32, B-43, B-44 |
| A-62 | Monitor modular und mobil | teilweise | `MonitorPage` je Standort, Spalten je Tag, statisches Laufband bei reduzierter Bewegung | am Handy abgeschnitten, Neuzeichnen jede Sekunde (U-37), Profile/Kacheln | B-12, B-28, B-33 |
| A-63 | Analyst, Design-Agent, Umsetzung nach Plan | erledigt | `PRODUKT-BACKLOG.md` (59 Pakete), `AUTOPILOT.md`, Spuren A/B/D | Protokoll in `AUTOPILOT.md` nur Runde 0 | – |
| A-64 | Beispielschulen und Testliste | teilweise | `docs/beispielschulen/` (Berufskolleg, Gesamtschule, Gymnasium; MD + JSON) | JSON nicht importierbar, von keinem Test genutzt; Testliste nur als externes Artifact | B-17, B-50 |
| A-65 | Code-Doku und Abgleich als Routine | erledigt | `docs/code/README.md` + 01–09, diese Datei, Routine in `CLAUDE.md` §1–2 | Pflege laufend; 01–04 und 07 haben ältere Stände (R1-Teile nachgezogen) | – |
| A-66 | Keine Hintergrundarbeit, sparsam | erledigt | Regeln `AUTOPILOT.md`, `CLAUDE.md` §4 | Einhaltung nicht im Repo prüfbar | – |

### 1.1 Beim Abgleich aufgelöste Widersprüche

- A-09: 03/04 „erledigt“, 05/09 „teilweise“ → **teilweise**, weil das Frontend-Cache-Leck (U-01) und `/data/exams` (U-05)
  Daten außerhalb des Scopes zeigen bzw. zulassen.
- A-12, A-23: 06 „teilweise“ (bezog sich nur auf `/krankmeldungen` bzw. die Benutzerseite) → **erledigt** über
  `/dokumente`, „Meine Übersicht“ und den Klassen-Assistenten.
- A-02, A-03: 09 bzw. 02 „teilweise“ (kein Lasttest, Benachrichtigungsfehler) → **erledigt**; die Mängel stehen als B-58
  bzw. U-46.
- A-18: 02/04 „erledigt“, 09 „teilweise“ → **teilweise**, weil SMS im Docker-Betrieb nicht einstellbar ist (U-09).
  A-21 dagegen **erledigt**, weil die Anbieter über die Oberfläche eingerichtet werden können.
- A-22: 09 „erledigt“ (Tests grün) → **teilweise** (Klassengruppen, Kontoerstellung, Token-Umgehung).
- A-24: 02 „erledigt“, 03/04/08 „teilweise“ → **teilweise**.
- A-28, A-32: 01/08 „fehlt“, übrige „teilweise“ → **teilweise** (Ferien, Wochenangaben, Schultage vorhanden).
- A-31, A-51: 03 „erledigt“, 01/06 „teilweise“ → **teilweise** (Rechner, Prüfung, Kalendertage fehlen).
- A-36: 07 (Stand c5d0747) „keine neuen Fächer im Profil“ ↔ Code 11.10.: `TeacherProfilePage` schlägt `new_subjects` vor →
  **in Arbeit**. A-45/A-47/A-60: Aussagen vor Runde 1 („teilweise“/„fehlt“) sind durch R1 überholt → **in Arbeit**.
- A-35, A-40: 06 „erledigt“ → **in Arbeit**, bis die Prüfung von R1 abgeschlossen ist.
- A-38: 03/04 „teilweise“, 01/06/08 „fehlt“ → **fehlt** (Kern der Anforderung fehlt; freie Namen vorhanden).
- A-48: 01 „teilweise“, übrige „fehlt“ → **fehlt**. A-55: 03/06 „fehlt“, 04/07 „teilweise“ → **teilweise**
  (Kursraum-Aufgaben).
- A-65: 02/05/08/09 „teilweise“ (README und diese Datei fehlten) → **erledigt** mit diesen beiden Dateien.

## 2. Unstimmigkeiten

### 2.1 hoch

| ID | Befund | Ort | Beleg | Paket |
|---|---|---|---|---|
| U-01 | **behoben (R2-D)** – Sammlungs-Cache überlebt Sitzungsablauf und Kontowechsel im selben Tab; das nächste Konto sieht Daten im Umfang des vorigen | `context/AuthContext.tsx:68-75`, `hooks/useCollection.ts:82-84`, Limits-Cache in `FileUpload`, `overviewShared` in `channels/api.ts` | reproduziert: lehrer1 sieht 666 statt 317 Schüler/innen (05 U1); 11.10.: `onUnauthorized` leert nichts | R2-D |
| U-02 | **behoben (R2-B)** – API-Tokens: wer ein Konto verwalten darf, erzeugt dafür ein Token und meldet sich als diese Person an; ein befristetes Token stellt ein unbefristetes aus | `routes/users.py:94-97,423-439` | reproduziert (03 R2, R3); widerspricht A-27 | R2-B |
| U-03 | **behoben (R2-B)** – DSGVO-Export gibt Eltern Titel, Vermerke und Datei-IDs der Atteste volljähriger Kinder, die Liste und Dateizugriff verbergen | `features_student_self.py:467-483` (`export_documents`), `me.py:93-99` | reproduziert (04 F1); 11.10. unverändert | R2-B |
| U-04 | **teilweise behoben:** kursraeume + krankmeldungen wirksam (R2-B); dokumente/stundenplan offen (R3-B) – Elternfreigabe: das Profil bietet 4 Bereiche an, wirksam ist nur „kursraeume“ | `elternzugriff/ParentAccessSection.tsx:53-71` ↔ `parent_access.py:35-40`; `parent_may_see` nur in `features_channels.py` | reproduziert (08 U1); grep 11.10. | R3-B |
| U-05 | `/data/exams` umgeht alle Klausurregeln (Schultag, Grenzen, Unterricht des Kurses) und das `force`-Verbot für Lehrkräfte | `features_data.py` (`WRITE_PERM`, nur `exam_errors`) ↔ `features_exams.py:140-184` | reproduziert (03 R1) | R3-A |
| U-06 | Generator und manuelles Verschieben beachten Pausen nicht; Doppelstunden liegen über Pausen | `scheduler.py:243-291` (`check`, `_make_blocks`), `timetable._evaluate` | reproduziert 22 von 70 (01 U-1), 30 von 93 (Backlog); `scheduler.py` seitdem unverändert | R3-A |
| U-07 | Klasse löschen mit `force` lässt Kursteil-Teilnehmer und `preferred_classes` stehen, danach scheitern `PUT` mit 422; ohne `force` blockiert `preferred_classes` das Löschen nicht | `features_data.py:226-273,330-343` | reproduziert (03 R4) | R4-A |
| U-08 | Eigener Kursraum: Mitglieder lassen sich nicht eintragen, obwohl der Anlege-Dialog es verspricht (`POST …/members` nur für die Aufsicht, Oberfläche nur „Mich eintragen“) | `channels/ChannelListPage.tsx:94`, `channels/MembersTab.tsx:29,53-59`, `features_channels.py` | Browser (07 U1); Code 11.10. | R4-B |
| U-09 | **behoben (R2-A)** – Compose reicht `SM_REQUIRE_2FA_ROLES`, `SM_SMS_*`, `SM_SSO_*`, `SM_DEV_OUTBOX`, `SM_LETTER_BATCH_MINUTES`, `SM_AUTH_CODE_MINUTES`, `SM_FILES_DIR`, `SM_BACKUP_DIR` nicht an die App; 2FA-Pflicht und SMS sind im Docker-Betrieb still wirkungslos | `docker-compose.yml:52-113` ↔ `.env.example:7`, `SICHERHEIT.md:167-169`, `BETRIEB.md:671-674` | reproduziert mit `docker compose config` (09 U1) | R2-A |
| U-10 | **behoben (R2-A)** – systemd-Backup sichert die eigenen Sicherungen mit; das Datei-Archiv verdoppelt sich je Lauf, die Platte läuft voll | `deploy/systemd/schulmanager-backup.service:18-19`, `scripts/backup.sh:154-158` | reproduziert 201 258 → 403 491 Byte (09 U2) | R2-A |

### 2.2 mittel

| ID | Befund | Ort | Beleg | Paket |
|---|---|---|---|---|
| U-11 | **teilweise behoben:** Vertretung und Druck erledigt (R2-A); Start und Monitor offen (B-12) – „Abwesende/fehlende Klassen“ wird weiter angezeigt (Vertretung, Druck, Start-Kennzahl, Monitor); Klassen mit regulärem Rhythmus erscheinen jede Woche; Monitor zeigt keine abwesenden Lehrkräfte | `SubstitutionsPage.tsx:561`, `PrintSubstitutionsPage.tsx:53`, `DashboardPage.tsx:363`, `MonitorPage.tsx:92`; `substitution.py` `absent_classes` | Code 11.10. (06 U9, 01/03 A-56, Analyse) | R2-A, R3-D |
| U-12 | **behoben (R2-A)** – Lehrkraft löscht jede eigene Abwesenheit mit Ende ≥ heute, auch vom Sekretariat erfasste (Fortbildung, Kur) | `features_substitutions.py:329-338` | reproduziert (03 R7) | R2-A |
| U-13 | `PUT /settings` prüft nicht gegen den Bestand: weniger Stunden lassen Stunden außerhalb des Rasters (Bericht: 0 Konflikte), weniger Schuljahreswochen machen `Course.weeks` ungültig, eine Änderung des Schuljahresbeginns verschiebt die Bedeutung von Wochenangaben | `features_data.py:712-736` | reproduziert (03 R6, Analyse) | R3-A |
| U-14 | Lehrkraft-Profil enthält das Deputat (`max_hours`), im Modus „direkt“ sofort gültig (widerspricht A-49) | `features_teacher_profile.py:75`, `teacher_profile.PROFILE_FIELDS` | Code 11.10. (Analyse) | R3-A |
| U-15 | Sperrzeit-, Wunsch- oder Rhythmusregel ohne Auswahl sperrt die ganze Woche; der Bericht meldet nichts | `lib/rules.ts` (`emptyRule`, leere Liste = alle), `features_data._rules_errors` | Analyse; Code unverändert | R3-A |
| U-16 | Zeitraster-Prüfung erkennt überlappende Stunden und zu kurze Pausen nicht; `core_latest_period ≥ periods` blockiert das Speichern des Zeitrasters über den anderen Reiter | `features_data.settings_errors` (`:783-788`) | Analyse; Code 11.10. | R3-A |
| U-17 | Doppel- und Einzelstunde eines Kurses liegen am selben Tag, obwohl Tage frei sind (14 Fälle in der Demo) | `scheduler.py` (`_make_blocks`, Kosten) | Analyse; Generator unverändert | R3-A |
| U-18 | Aufsichtsersatz prüft Sperren nur, wenn **eine** Regel beide Nachbarstunden trifft; die Planung schließt schon eine gesperrte Nachbarstunde aus | `duties.py:241` vs. `:88` | reproduziert (01 U-2) | R3-A |
| U-19 | Lesson-IDs werden bei Neuplanung und Untis-Import neu vergeben; Overrides verwaisen oder treffen eine andere Stunde | `scheduler.py:894-899`, `untis_gpu.py:1023-1059`, `server/jobs.py:597` | reproduziert (01 U-3) | R4-A |
| U-20 | Geburtsdatum wird weder per CSV noch per GPU010 übernommen oder exportiert (CSV nutzt es nur zur ID-Bildung) | `csv_io.py:132,159,858`, `untis_gpu.py:398-404,1073-1106` | reproduziert (01 U-5, Analyse); Code 11.10. | R4-A |
| U-21 | Vertretungen werden über Wochen nicht fair verteilt; die Wochenhistorie beginnt jeden Montag neu | `substitution.week_history`, `features_common.day_plan` | Analyse (01 §3.5) | B-36 |
| U-22 | **behoben (R2-B)** – Fachlehrkräfte – auch ohne Unterricht bei der Person (Scope über `course.classes`) – sehen, entschuldigen und löschen Krankmeldungen und überschreiben den für sie unsichtbaren Vermerk | `features_student_absences.py:98-113,212-235` | reproduziert (03 R8, Analyse) | R2-B |
| U-23 | **behoben (R2-B)** – Technische Administration (`admin`) sieht alle Krankheitsgründe; der Hinweis „vertraulich“ nennt den falschen Personenkreis | `permissions.py` (admin `student_absence.read`), `StudentAbsencesPage.tsx` | Analyse (B-06) | R2-B |
| U-24 | **teilweise behoben:** Krankmeldungen erledigt (R2-B); Dokumente offen (R3-B) – Eltern volljähriger Kinder sehen Krankheitsgründe und melden krank; Volljährige können das nicht einschränken | `features_student_absences.py:56-61,181-183` | reproduziert (03 R9) | R3-B |
| U-25 | **teilweise behoben:** Krankmeldungen folgen dem Geburtsdatum (R2-B); Dokumente/Upload weiter users.adult – Volljährigkeit uneinheitlich: Kursräume nach Geburtsdatum (+ Einwilligung), Dokumente, Übersicht, Selbstmeldung und Rechte nur nach `users.adult`; bei späterer Kontoanlage wird sie nicht aus dem Geburtsdatum gesetzt | `features_student_self.py:109-127,420-427`, `permissions.py:113-119`, `accounts.bulk_create` | reproduziert (04 F2, Analyse) | R3-B |
| U-26 | `teacher_id`/`student_id` werden nicht gegen die Rolle geprüft; `own_class_ids` wertet `teacher_id` rollenunabhängig aus (Schülerkonto mit `teacher_id` sieht Lehrerpläne) | `users.py:100-112,173-176,219-228`, `features_common.py:361-372` | reproduziert (03 R10) | R7-B |
| U-27 | Kontolöschung pseudonymisiert unvollständig: Benutzername bleibt in `audit_log.details`, Klarnamen in `announcements.author_name`, `student_absences.reported_by_name`, `student_documents.*_by_name`, `channel_posts.author_name` | `accounts.py:238-250`, `users.py:272-274` | reproduziert (02 U3) | R7-B |
| U-28 | iCal-Token und TOTP-Geheimnis liegen im Klartext (Regel „Codes/Token nur als Hash“) | `db_models.py:29,35`, `deps.py:143-150` | statisch (02 U6, 09 U9) | R5-B |
| U-29 | Vorschau: Test-Anbieter „Schulkonto“ meldet als beliebiges vorhandenes Konto an (auch admin), wenn der Teil vor „@“ ein Benutzername ist; die echte OIDC-Zuordnung per Benutzername schließt Admins ebenfalls nicht aus | `sso_providers.py:636-637`, `identities.py:129-132,153-171` | reproduziert (02 U1); Code 11.10. | R5-B |
| U-30 | Vorschau: Test-Postausgang ohne Anmeldung + „Passwort vergessen“ ermöglichen die Übernahme jedes Kontos mit bestätigter E-Mail (laut `VORSCHAU.md` beabsichtigt, Produktion gesperrt) | `features_contact.py:859-927` | reproduziert (04 F3) | R5-B |
| U-31 | Elternangaben aus dem Klassen-Assistenten gehen ohne Elternkonto verloren | `features_classes.py`, `letters.plan_accounts` | Analyse (B-18) | R6-B |
| U-32 | Klassen-Assistent: Standard `create_student_accounts=True` → Planer ohne `users.manage` erhält 403 auch ohne Schülerliste; Jahrgang hart 1–13, `/data/classes` erlaubt 0–20 | `features_classes.py:716,793-800,938-939`, `classes/NewClassPage.tsx:53` | reproduziert (04 F4, 08) | R6-B |
| U-33 | Listen-Import im Klassen-Assistenten ordnet Spalten per Teilstring falsch zu („Geburtsort“ → Geburtsdatum, „Telefon Eltern“ → Name) | `classes/studentList.ts:193-202` | reproduziert (08) | R6-B |
| U-34 | Plan-ID wird doppelt dekodiert; bei „%“ in der ID URIError und leere Seite | `TimetablePage.tsx:238`, `PrintTimetablePage.tsx:20` | reproduziert mit Klasse „7%b“ (06 U1) | R4-A |
| U-35 | Woche am Wochenende aus `todayISO()` (abgelaufene Woche markiert); Aufsichten-Woche nur im `useState`-Initialisierer berechnet | `TimetablePage.tsx:252,312`, `DutiesPage.tsx:109` | reproduziert (06 U4, U5) | R4-A |
| U-36 | Gemerktes Kind (`sm-child`) gilt gerätweit; bei fremdem Kind hängt die Startseite im 403, die Kindauswahl verschwindet | `DashboardPage.tsx:73-78,102-113` | reproduziert (06 U2) | R3-D |
| U-37 | Monitor am Handy abgeschnitten (`100vh`, `overflow: hidden`); die ganze Seite zeichnet jede Sekunde neu; Kommentar „minütlich“ bei 120 s | `styles/monitor.css`, `MonitorPage.tsx:166,181-186` | CSS/Code (05 A-62, 06 U11, Analyse) | R3-D |
| U-38 | **behoben (R2-D)** – „Kein Zugriff“ erscheint ohne App-Rahmen (kein Menü, kein Rückweg) | `App.tsx:79-95,126-129` | reproduziert (05 U2) | R2-D |
| U-39 | KI-typische Erklärtexte auf vielen Seiten; `designRules.test.ts` erfasst nur `className="explain"`, nicht `small muted`, `span.hint` oder Alerts | Basis `RuleEditor`, `FileUpload`, `MyDayView`; Seiten (18× `explain` in 8 Dateien, u. a. `SettingsPanels`, `ImportExportPage`); Features A (`VisibilityPicker`, `TeacherProfilePage`, `ComposePage` …); Features B (`PolicyPage` „So funktioniert es“, `SetupPage`, `classes/dialogs`, `accountsUi`, `BatchPage`, `ContactSection`) | Code/Browser (05 U8, 06 U15, 07 U3, 08) | R4-D, R6-D, B-43 |
| U-40 | Schieberegler und Technikbegriffe (Gewichte, Rechenzeit, „Startwert (Seed)“, „Job … Status“ mit englischen Werten) | `SettingsPanels.tsx:277-317`, `GeneratorPanel.tsx:226-244,274-277`, `teacher/ReplanPanel.tsx:101` | Code (06 U16, 07 U12) | R4-D |
| U-41 | Anrede gemischt: Schülerprofil „Sie“ neben „du“; Kursraum-Kacheln „Ihr Konto“ neben „deinem“ | `ParentAccessSection.tsx:41,54` ↔ `ContactSection.tsx`, `IdentitiesSection.tsx`; `channels/widgets.tsx:40,82`, `BoardTab.tsx:251` | Browser (07 U4, 08) | R3-B, B-43 |
| U-42 | „Meine Übersicht“ läuft bei 390 px über (Knopf „Klassenleitung … schreiben“ 397 px) | `students/OverviewPage.tsx:121-130` | Browser (07 U2) | R3-B |
| U-43 | `/anmeldedienste` hat keine `h1` | `anmeldedienste/SetupPage.tsx:193-195` | Browser (08) | R6-D |
| U-44 | **behoben (R2-A)** – `.env.example` hat Kommentare hinter Werten, dient aber als systemd-`EnvironmentFile`; Mandant, Google-Domain und Apple-Schlüssel werden zu Kommentartext | `.env.example:15,189-192,227,230-234`, `BETRIEB.md:166` | statisch (09 U3) | R2-A |
| U-45 | App meldet immer Version 0.1.0 (`/healthz`, `/version`, Metriken, Systemseite) | `config.py:16` | reproduziert (09 U4) | R7-B |
| U-46 | `notify.check_changes`: die Schleifenvariable überschreibt den Snapshot-Schlüssel; Vertretungspläne werden alle 5 s neu berechnet, der Basis-Reset greift nie | `notify.py:176-203` (Z. 200) | reproduziert (02 U2); Code 11.10. | R7-B |
| U-47 | `SICHERHEIT.md` veraltet: Datei-Allowlist (Quelltext, HTML, neue Formate werden angenommen), DSGVO-Kategorien („keine Geburtsdaten“), fehlende Kategorien (Kontakt, Postfach, Kursräume, SSO, Elternfreigaben, Briefe), Löschfristen ohne Postfach | `SICHERHEIT.md:47`, §2.4, `:288-293` | Tests `test_channels_rooms.py:266-295` (09 U6, U7) | R3-B (DSGVO), R4-B (Allowlist) |
| U-48 | **teilweise behoben:** Rechtematrix §6 abgeglichen (R2-B, test_architecture_matrix_matches_permissions) – `ARCHITECTURE.md` veraltet: Rechtematrix (Lehrkraft mit `monitor.read`, `plans.read_all` ohne Scope; `channels.view_children`, Kursraum- und Postfach-Rechte fehlen), Allowlist, §9.3/§9.4 (Ordner-Freigabe, Eltern-Rolle, `new_subjects`), §10.2/§10.3 (Icon, Begleitungen), Demo-Größe | `ARCHITECTURE.md:63,189,195,287,305,324-343` | Code/Test (02 U7, 09 U6/U8/U15, 04 F14, 08) | R2-B (Matrix), Rest mit dem Bereichspaket |

### 2.3 niedrig

| ID | Befund | Ort | Herkunft | Paket |
|---|---|---|---|---|
| U-49 | `Settings.days` bis 7 erlaubt, `WEEKDAYS` kennt 6 Namen; Oberfläche bietet höchstens 6 | `models.py:20`, `timetable.py:189`, `SettingsPanels.tsx` | 01 U-6, 06 U14 | R3-A (Oberfläche R4-D) |
| U-50 | `max_exams_per_week/day = 0` wirkt wie 1 | `exams.py:119-124` | 01 U-7 | R3-A |
| U-51 | Manuelles Verschieben nutzt `ceil(hours/days)`, der Generator die verfügbaren Tage | `timetable.py:297-304` vs. `scheduler.py:155-168` | 01 U-8 | R3-A |
| U-52 | Manuelle Kurse mit `weeks` (nur ausgewählte Wochen) zählen voll gegen die Stundentafel | `planning.py:33-36` | 01 U-9 | Lückenfüller A |
| U-53 | Kurs mit unbekannter erster Klasse → `KeyError` im Generator | `scheduler.py:147` | 01 U-10 | R4-A |
| U-54 | Schüler/innen und Eltern erhalten über `/data/courses` und `/data/classes` alle Kurse (mit Lehrkraft) und Klassen | `features_data.py:445-464` | 03 R11 | R4-A |
| U-55 | `Student.birth_date` wird nicht geprüft | `features_data.py:146-155` | 03 R18 | R4-A |
| U-56 | Wochen als Buchstaben (ab 27 Wochen „[“) in Backend und Frontend (behoben: nur noch Wochenzahlen, Listen und Rhythmen) | – | 05 U9, 06 U14, 07 U6, 04 F14 | B-25, B-45 |
| U-57 | Begriff „Wunschklassen“ in Meldungen, CSV und Oberfläche | `teacher_profile.py:356,363,572`, `csv_io.py:52`, `MasterDataPage`, `TeacherProfilePage` | 01 U-13 | R7-A |
| U-58 | Webhook: Zeitstempel-Header nicht signiert; `headers()` doppelt zu `notify.prepare_webhook` | `webhooks.py:7-11,132-141` | 01 U-14 | Lückenfüller A |
| U-59 | **behoben (R2-A)** – Wochenstatistik der Vertretung fest Mo–Fr; Lehrkräfte nur mit Aufsichten fehlen | `SubstitutionsPage.tsx:322-325` | 06 U21 | R2-A |
| U-60 | **teilweise behoben:** SubstitutionsPage erledigt (R2-A); DashboardPage.tsx:214 offen – Feldtext „Grund (nur für die Schulleitung sichtbar)“ falsch (sichtbar für alle mit `substitution.edit`) | `DashboardPage.tsx:214`, `SubstitutionsPage.tsx:130` | 06 U12 | R2-A, R3-D |
| U-61 | Postfach-Aufbewahrungsfrist läuft nicht in der Wartung (nur beim Abruf `/messages/unread`) | `features_messages.py:53-55,1806-1817` ↔ `maintenance.py:31-58` | 04 F9 | R4-B |
| U-62 | Outbox-Zeilen `webhook`/`email` werden nie gelöscht; Vertretungs-Mails liegen im Klartext | `maintenance.py:21-62`, `notify.py:236-245` | 02 U4 | R7-B |
| U-63 | `files.delete(hard=True)` + Rollback: ein späterer Commit derselben Session löscht den Blob trotzdem | `files.py:1258-1261,1299-1307` | 02 U5 | R4-B |
| U-64 | 403 statt 404 bei fremden vorhandenen Datensätzen (ID-Erkennung) | `users.py:193-197,387-419`, `features_student_absences.py:216-244`, `features_channels.py:462-479`, `features_classes.py:272-273` | 03 R12, 04 F7 | R7-B (Kern), Lückenfüller B |
| U-65 | `/audit?since/until` mit Zeitzonen-Offset wird nicht nach UTC umgerechnet | `history.py:74-77` | 03 R13 | R7-B |
| U-66 | `/events` liefert den SSE-Strom auch bei Passwortwechsel-, 2FA- oder Verknüpfungszwang | `events.py:23-31` | 03 R14 | R5-B |
| U-67 | Schreibende Aktionen ohne Audit: Wartung, Datei-Upload/-Löschen, iCal-Link, Outbox-Retry, 2FA-Setup, still zurückgezogener Antrag (Modus „direkt“), Pinnwand, Ordner umbenennen/verschieben, Postfach-Nachrichten/Blockieren/Entwürfe/Einstellungen | `admin.py:112-117`, `files.py:57-97`, `me.py:28-57`, `features_exchange.py:381-395`, `auth.py:227-237`, `features_teacher_profile.py:314-315`, `features_channels.py`, `features_messages.py` | 03 R15, 04 F5, F10 | R7-B, R4-B, R7-A |
| U-68 | `/auth/config` meldet `oidc.enabled` nur aus der Umgebung, `auth.config()` ist ungenutzt; Passwortregeln stehen fest im Frontend (≥ 10 + Zeichenklassen) statt vom Server (Schüler/innen 8, Benutzername, häufige Passwörter) | `auth.py:181-187`, `api/endpoints.ts:60-65`, `ChangePasswordPage.tsx:11-17,60-62` | 03 R16, 06 U13 | R5-B |
| U-69 | Scope `history_only` wird nirgends ausgewertet | `permissions.py:93` | 03 R17 | R7-B |
| U-70 | `POST /letters/batches` erlaubt das eigene Konto (eigenes Passwort zurückgesetzt, Sitzung beendet); `/users/{id}/password` verbietet es | `features_letters.py:99-167` ↔ `:299-300` | 04 F6 | R7-B |
| U-71 | Klassen-Schema erlaubt 500 Schüler/innen, die Prüfung danach 60 | `features_classes.py:697,730-745` | 04 F12 | R6-B |
| U-72 | Eingaben uneinheitlich: `extra=forbid` nur bei Kursräumen, Postfach, Profil; Passwortlänge 256 vs. 1024 | `features_student_self.py`, `features_classes.py`, `features_contact.py`, `features_letters.py`, `features_login_policy.py`, `features_sso.py` | 04 F13 | Lückenfüller B |
| U-73 | `reset_confirm` verbraucht das Reset-Token nicht atomar | `features_contact.py:876-890` | 04 F15 | R5-B |
| U-74 | Docstring `permissions.py` ohne `class_teacher`; `db_models.ROLES` unbenutztes Duplikat; `SM_LETTER_BATCH_MINUTES` außerhalb von `config` | `permissions.py:4-7`, `db_models.py:17`, `letters.py:58-64` | 02 U8 | R7-B |
| U-75 | **behoben (R2-D)** – Codes `not_authenticated`/`invalid_token` fehlen in `KNOWN_DETAILS`; Toast „Keine Berechtigung: Keine Berechtigung …“; Kommentar von `AsyncButton` verspricht eine Fehlermeldung | `api/client.ts:90-104`, `context/ToastContext.tsx:52`, `components/ui.tsx` | 05 U3, U5, U17 | R2-D |
| U-76 | **behoben (R2-D)** – `CORE_PATHS` ohne öffentliche Kernpfade (`/passwort-vergessen`, `/passwort-zuruecksetzen`, `/test-postausgang`, `/konten-verbinden`); Doku nennt den Zweck `message_attachment` statt `message` | `features/registry.ts:78-82`, `features/README.md:140,166`, `api/files.ts:214` | 05 U16, U4 | R2-D |
| U-77 | **behoben (R2-D)** – `--motion` ohne Standardwert (Übergang in `channels.css` nie aktiv); `box-shadow … dashed` ungültig | `styles/tokens.css:179-182`, `styles/timetable.css:77` | 05 U13, U12 | R2-D |
| U-78 | „Heute“ ist am Wochenende aktiv und wirkungslos | `components/DateNav.tsx:24` | 05 U14 | R3-D |
| U-79 | Barrierefreiheit: `TimetableList` nur per Maus, `Tabs` ohne `aria-controls`/`tabpanel`, `aria-selected` an `<tr>`, `role="menu"` ohne Pfeiltasten | `TimetableGrid.tsx:239-244`, `ui.tsx:211-229`, `EntryTable.tsx:94`, `VirtualTable.tsx:148`, `Layout.tsx:138` | 05 U15 | R7-D |
| U-80 | Breakpoints 700/800/1200 px statt `DESIGN.md` §11; Inline-Styles für Abstand und Farbe (Seiten 144×, `FileUpload` 19×, `FileList` 11×) | `app.css:1862`, `timetable.css:207`, `TimetablePage.tsx:210`; `pages/*`, `components/*` | 05 U6, U7, 06 U25 | B-43 |
| U-81 | Tabellen mit vielen Spalten scrollen am Handy waagerecht in `.table-wrap`; `.table-cards` wird nirgends genutzt | `ExamsPage.tsx:233-301`, `SubstitutionsPage.tsx:597-649`, `SettingsPanels.tsx:93-170`, `zugangsdaten/BatchPage.tsx:145`, `classes/accountsUi.tsx:134,227`, `anmelderichtlinien/PolicyPage.tsx:168,356` | 06 U26, 08 | B-43 |
| U-82 | Pause „nach Stunde“: Oberfläche erlaubt bis zur letzten Stunde, Backend nur `< periods-1`; Speichern scheitert | `SettingsPanels.tsx:563` ↔ `features_data.py:783` | 06 U6 (reproduziert) | R4-D |
| U-83 | Rohschlüssel in der Oberfläche: „assigned: 0 · open: 0“ (Lehrkräfte zuweisen), Systemseite zeigt `classes`, `lehrer` … | `GeneratorPanel.tsx:31-38`, `AdminPage.tsx:98-119` | 06 U7, U8 (reproduziert) | R4-D, R6-D |
| U-84 | Grenzwerte Oberfläche ↔ Backend: Rhythmus 1–4 (Backend 8), Wochen als Text sortiert, Entfall ab Stufe ≤ 13 (14), Attestpflicht ≤ 30 (60) | `SettingsPanels.tsx:355,452,491-502`, `CoursesEditor.tsx:156-158,277`, `MasterDataPage.tsx:167,655`, `AdminPage.tsx:230` ↔ `features_data.py:747-763` | 06 U14 | R4-D (Einstellungen), R4-A (Kurse, Stammdaten), R7-B (System) |
| U-85 | Entwürfe in Planung und Einstellungen gehen beim Reiterwechsel ohne Rückfrage verloren; Speichern sendet das ganze Settings-Objekt (jede Änderung lädt die Lehrkräfte live neu) | `PlanningPage.tsx:48`, `SettingsPanels.tsx:223-239,265,473`, `CurriculaEditor.tsx:179,212` | 06 U17, U18 | R4-D |
| U-86 | Generator-Hinweis „neuer Lauf erst danach“ widerspricht dem Knopf; fremder Job nur beim Laden ermittelt | `GeneratorPanel.tsx:124-138,246-252` | 06 U23 | R4-D |
| U-87 | Löschen mit `force` nach 409 ohne Fehlerbehandlung | `planning/CoursesEditor.tsx:65-71`, `channels/MaterialTab.tsx:280,297` | 06 U10, 07 U7 | R4-A, R4-B |
| U-88 | Aufsicht entfernen ohne Rückfrage | `DutiesPage.tsx:61-71,78-82` | 06 U29 | R4-A |
| U-89 | **behoben (R2-B)** – Familie sieht nur Krankmeldungen der letzten 14 Tage | `StudentAbsencesPage.tsx:134,203` | 06 U22 | R2-B |
| U-90 | Einzel-Zugangsbrief ohne Klasse; Kinderliste der Eltern doppelt gesendet (PATCH + PUT, halber Stand möglich) | `UsersPage.tsx:79,98-99,150` | 06 U27, U28 | R7-B |
| U-91 | `safeNext` lässt `/\host` durch (nach der Anmeldung leere Seite); Anbieter-URL beim Verbinden uneinheitlich geprüft; `?code=` auf „Passwort vergessen“ ohne Erzeuger | `LoginPage.tsx:24-27`, `IdentitiesSection.tsx:36-37`, `LinkSetupPage.tsx:48`, `ForgotPasswordPage.tsx:28-29` | 06 U3, 08 | R5-B |
| U-92 | Emojis und Glyphen statt Icon (Stecknadel-Emoji für „angeheftet“, „● live“ / „○ verbinde …“) | `AnnouncementsPage.tsx:171`, `MonitorPage.tsx:205` | 06 U24 | R3-D, R6-D |
| U-93 | Rechte-Logik in Seiten dupliziert bzw. an Rollennamen; Casts wegen Lücken in `api/types.ts` | `UsersPage.tsx:28-33`, `ExamsPage.tsx:31`, `AnnouncementsPage.tsx:24,27,127`, `DashboardPage.tsx:78` u. a. | 06 U19, U20 | Lückenfüller |
| U-94 | Kursräume: Anhang-Grenzen zählen vorhandene Dateien nicht (Aufgabe, Abgabe, Rückmeldung) | `AssignmentsTab.tsx:139,188,448` | 07 U8 | R4-B |
| U-95 | Klassen-Logik: `gradeFromName` kennt weniger Formen als das Backend, E-Mail-Prüfung lockerer (Probelauf 422), Jahrgangsfeld zeigt nach dem Leeren „0“, „Zurücknehmen“ mit Begleitungen nicht atomar | `classes/studentList.ts:50,427-435`, `NewClassPage.tsx:44,169`, `WeekTab.tsx:355-363` | 08 | R6-B |
| U-96 | Feld `sso_create` („Konto erstellen“) ordnet nur per E-Mail zu; „wer darf ein Konto erstellen“ fehlt | `anmelderichtlinien/logic.ts:30` ↔ `identities.py:90,127` | 08 | B-19 |
| U-97 | Sprache: Mehrzahl („1 Kursräume“, „3 Attest fehlt“), Grammatik der Vorschau-Sätze („von Herr Schmidt“), doppelte Meldung „noch nichts gespeichert“, „Lehrkraft“ neben „Lehrende“ | `ChannelListPage.tsx:208`, `channels/dialogs.tsx:400`, `students/widgets.tsx:67-69`, `classes/logic.ts:427,436`, `classes/dialogs.tsx:95-97`, `BoardTab.tsx:129` | 07 U5, U9, U11, 08 | B-43 |
| U-98 | Toter bzw. doppelter Code und veraltete Kommentare: `useOnce`, `canAll`, `isForbidden`, `describeEntry`, `formatBytes` doppelt („1.5 KB“ vs. „1,5 KB“), `ROLE_TEXT`, `maskPhone`, `parse_bool("-")`, tote Bedingung `fields == {"archived"}`, Altlogik `users.py:111-112`, Docstring `student_self.py:4-5` | siehe Herkunft | 01 U-11, U-15, 03 R19, 04 F11, 05 U10, U11, 07 U10, 08 | Lückenfüller |
| U-99 | Zeilen über 120 Zeichen; E501 ist in `ruff` nicht aktiv | 17 Stellen in den Feature-Routen, `users.py:321` | 03 R19, 04 F16 | Lückenfüller |
| U-100 | Betrieb: zwei Migrationsschalter (`SM_MIGRATE_ON_START` undokumentiert), falsche Entrypoint-Warnung zu `SM_SECRET_KEY`, `SM_ENCRYPTION_KEYS` nicht geprüft, nginx doppelt Sicherheits-Header (Swagger blockiert), `deploy/caddy/README.md` fehlt, Update-`sed` trifft die auskommentierte Zeile, README/BETRIEB veraltet (Admin-Passwort, CLI, Testzahlen, Inhaltsverzeichnis, `schueler4`), Demo-Größe „98 Klassen“ | `deploy/docker/entrypoint.sh:21-23,51,79-80`, `deploy/nginx/schulmanager.conf:66-72`, `deploy/Caddyfile:16,123`, `BETRIEB.md:9-21,170,198,223-228,254-255,556`, `README.md:91-158`, `.env.example:98,312` | 09 U10–U17, 01 U-12 | R7-B |
| U-101 | Tests: uneinheitliche Importe (`tests.conftest` vs. `conftest`, nur `python -m pytest` läuft), datumsabhängige Hilfen, Lücken (`/version`, `/admin/maintenance`, `/channels/{id}/reorder`, `?archived=1`, 9 CLI-Befehle, Downgrade 0012/0013, keine E2E-Tests) | `test_contact.py:10` u. a.; `test_teacher_scope.py:30-38`, `test_server_features.py:110-122,492-506`, `test_student_self.py:26-38` | 09 U18–U20 | Lückenfüller, je Paket |

### 2.4 In Runde 1 behoben (geprüft)

- Stundentafel (R1-U1): gleichrangige Überschneidung → 409 mit Klassenliste (`force` möglich), leere Tafel und Klasse ohne
  Tafel werden gemeldet, Fach doppelt → 422, `Course.pinned` behält Editor-Änderungen, „zu viel verplant“ im Bericht,
  CSV-Zeile wird bei Fehler ganz zurückgenommen (01 U-4), Kürzel mit Leerzeichen überstehen den CSV-Rundlauf, Jahrgänge
  0–20 geprüft, Editor-Auswahl nach „Neue Stundentafel“, Lehrkraft-Warnung unterscheidet „kein Fach“/„kein Deputat“,
  JSON-Teilimport warnt mit `would_delete`/`danger`, `courses-from-curricula` entfernt verwaiste Overrides (03 R5).
- Kursräume (R1-U2): Klassenräume schützen fremdes Material, Upload speichert sofort als Material, ganze Ordner per
  Auswahl/Ziehen, Fachformate (Quelltext als Text-Download, GeoGebra, SMART, Scratch, EPUB, RTF, TIFF), Hinweis bei
  Lehrerkonto ohne Lehrkraft, „zur Stunde“ verschiebt bei Entfall/Ferien, Eltern lesen Kursräume ihrer Kinder.
- Design (R1-D1): `Field`-Hinweise per `aria-describedby` verknüpft, Laufband bei „Bewegung reduzieren“ statisch, Hilfe-
  Funktion, untere Leiste am Handy, Login/Start/Profil ohne Erklärabsätze.
- Prüfrunde 1 (16 Befunde, alle behoben, je mit Regressionstest): Kopieren in Parallelkurs gab geplante Ordner frei
  (`test_copy_keeps_folder_release`); Profil „Was dürfen meine Eltern sehen?“ ohne Wirkung; Downgrade 0013 machte Ordner
  sichtbar (`test_downgrade_keeps_unreleased_folders_hidden`); „Ordner auswählen“ lud `.git`/`.idea`; Schließen/Reiterwechsel
  verwarf wartende Uploads; Freigabe nach 14 Tagen trotz Ferien (`test_lesson_on_new_holiday_waits_for_first_lesson_after_holidays`);
  CSV-/JSON-Import übernahm überlappende Tafeln still; Stammdaten nur Jahrgang 1–13; Hilfe an eigenständigem Namen nicht
  per Klick/Screenreader; Menü-Fokus hinter dem Hintergrund; Toasts verdeckten die untere Leiste; Druck mit Leiste/Hilfe;
  Touch-Fläche der Hilfe-Beschriftung 16 px (jetzt 37 px).

### 2.5 Neu aus der Prüfrunde 1 (offen)

| ID | Schwere | Befund | Ort/Beleg | Paket |
|---|---|---|---|---|
| U-102 | niedrig | Welche Stundentafel für eine Klasse gilt, sieht man nur im Editor; `GET /planning/curricula/overview` ungenutzt; Jahrgangswechsel einer Klasse (PUT /data/classes) kann still eine Überschneidung erzeugen | `features_planning.py` overview, `features_data.py` classes | B-14 |
| U-103 | **teilweise behoben:** Krankmeldungen erledigt (R2-B); Stundenplan offen (R3-B) – hoch | Eltern volljähriger Kinder sehen weiter Stundenplan und Krankmeldungen samt Grund (pauschal `users.adult`, Baustein `parent_access` dort noch nicht angebunden) | `GET /timetable/student/{id}`, Krankmeldungen | B-06/B-07 (R2-B, R3-B) |
| U-104 | mittel | Fremder, vorhandener Kursraum → 403 statt 404 (CLAUDE.md: fremde Daten → 404) | `features_channels.py`, viele Assertions in `tests/test_channels*.py` | B-07 (R3-B) |
| U-105 | mittel | Kursräume: kein `audit()` bei sichtbaren Ordnern, Umbenennen/Verschieben von Ordnern, `reorder`, neuen Pinnwand-Beiträgen | `features_channels.py` | B-05 (Lückenfüller Spur B) |
| U-106 | niedrig | `parent_access`-Zeilen fehlen im DSGVO-Export und bleiben beim Löschen von Konto/Schüler/in stehen | `me.py` Export, `users.py`/`maintenance.py` Löschen | B-07 (R3-B) |
| U-107 | niedrig | Seitenwechsel in der App während laufender Uploads bricht ohne Rückfrage ab (kein Router-Blocker); leere Unterordner werden nicht angelegt | `features/channels/MaterialUpload.tsx` | Lückenfüller |
| U-108 | mittel | Durch `hint` → Hilfe sind fachlich nötige/dynamische Hinweise nicht mehr sichtbar; Eigner sollen `hintInline` setzen (NewClassPage, TeacherProfilePage, zugangsdaten, UsersPage, AssignmentsTab, channels/dialogs) | `components/ui.tsx` Field | B-23 (R6-D), je Paket |
| U-109 | niedrig | „1 Hinweise“ in der Kachel Stundenplan-Qualität; Lehrkräfte-Antrags-Widget mit Erklärsatz; „Angemeldete Geräte“ mit rohem User-Agent | `DashboardPage.tsx:414`, `features/teacher` Widget, `ProfilePage` | B-12 (R3-D) / B-21 |
| U-110 | niedrig | Stundentafel: Vorschau „Kurse erzeugen“ nennt entfernte Kurse/Klausuren nur per ID; Kurs-Editor max. 20 Wochenstunden (Tafel 40); Fächertabelle bei 390 px innen waagerecht scrollbar; Klassen-Assistent nur Jahrgang 1–13 (sonst 0–20); Untis-Export ohne `Course.pinned` | `CoursesEditor.tsx`, `CurriculaEditor.tsx`, `features_classes.py:938` | B-03 (R4-A) / B-18 (R6-B) |

### 2.6 Runde 2 (geprüft, 11.10.)

Behoben: U-01, U-02, U-03, U-09, U-10, U-12, U-22, U-23, U-38, U-44, U-59, U-75, U-76, U-77, U-89 (je mit Test, Einzelheiten
in `docs/code/*` und im Prüfbericht). Teilweise: U-04, U-11, U-24, U-25, U-48, U-60, U-103. Zusätzlich in der Prüfrunde
behoben: Hinweistexte verloren Teilwörter („Exkursion“ → „Exsion“) in öffentlicher Sicht; eigener Ausfall verschwand mit
Lehrkraft-Filter; Stunden-Meldung einer Fachlehrkraft blockierte die Krankmeldung der Familie (409); Volljährige nach
Geburtsdatum ohne `users.adult` konnten nicht gemeldet werden; datumsabhängiger Test; echter 500 ohne Fehlernummer; Toasts
des vorigen Kontos nach dem Abmelden.

| ID | Schwere | Befund | Ort/Beleg | Paket |
|---|---|---|---|---|
| U-111 | mittel | Admin (`audit.read`) sieht im Audit-Protokoll `student_absence.*` mit Schüler-ID und Zeitraum, also wer wann krank war | `routes/history.py`, `audit.py` | R3-B |
| U-112 | niedrig | Fachlehrkraft erkennt über 409 beim Melden der eigenen Stunde, ob schon eine Meldung vorliegt (ohne Zeitraum/Grund) | `features_student_absences.py` | R3-B |
| U-113 | niedrig | Vor dem Update selbst gemeldete Lehrkraft-Abwesenheiten haben kein `self_reported`; nur das Sekretariat kann sie löschen | `models.Absence.self_reported` | Lückenfüller |
| U-114 | niedrig | B-13 Kriterium 2: Baustein „Fehler am Feld“ (`FormErrors`, `Field name`) fertig, aber in keinem Formular eingesetzt (zuerst Abwesenheits-Dialog, Krankmeldung) | `components/ui.tsx`, `SubstitutionsPage.tsx`, `StudentAbsencesPage.tsx` | R3-D, je Paket |
| U-115 | niedrig | Backend-500 ohne Request-ID in Antwort und Log; Datei-Uploads (XHR) zeigen bei 500 keine Fehlernummer | `server/app.py`, `api/files.ts` | Lückenfüller |
| U-116 | niedrig | „1 Einträge“ in `components/VirtualTable.tsx:174` (wie U-109); sichtbarer Erklärsatz für Lehrkräfte in `SubstitutionsPage` | `VirtualTable.tsx`, `SubstitutionsPage.tsx` | R3-D |

## 3. Nächste Schritte

Reihenfolge nach `docs/AUTOPILOT.md`: Pflicht-Anforderungen des Auftraggebers → P0 → P1 → Feinschliff; hohe
Unstimmigkeiten sind in den Runden 2–4 eingeplant. Je Runde zwei Umsetzungs-Pakete (Spur A, Spur B) und ein Design-Paket
(Spur D), parallel ohne gemeinsame Dateien (Ausnahmen stehen am Paket und werden in `docs/AGENT_NOTES.md` angekündigt).
Jedes Paket erfüllt zusätzlich die Definition of Done (`PRODUKT-BACKLOG.md` §3.3) und endet mit einer Prüfrunde.

### 3.0 Vor Runde 2 (Hauptsitzung)

- Runde 1 abschließen: R1-U1 Stundentafel & Fächer (B-01), R1-U2 Kursräume + Elternzugriff-Baustein (B-09, Teile B-07/B-20),
  R1-D1 Design-Grundlagen (B-10) prüfen; `ruff check .`, komplette Testsuite, `npm run lint`, `npx vitest run`; committen,
  pushen, Protokoll in `AUTOPILOT.md`; diese Datei und `docs/code/README.md`, `06`, `08`, `09` mit einchecken.
- Erledigt am 11.10.: Status gesetzt (A-35/45/46/47 erledigt, A-36/40/59/60/61 teilweise), §2.4 abgehakt, Befunde der
  Prüfrunde als U-102 … U-110 (§2.5). B-05 (im Backlog für Runde 1 vorgesehen) wurde nicht begonnen → Runde 7.

### 3.1 Rundenplan

| Runde | Spur A (Umsetzung) | Spur B (Umsetzung) | Spur D (Design) |
|---|---|---|---|
| 2 | R2-A: B-04 Vertretungsplan + Betrieb sofort (U-09, U-10) | R2-B: B-06 Krankmeldungen + Datenschutz sofort (U-02, U-03) | R2-D: B-13 Fehlermeldungen + Konto-Cache (U-01) |
| 3 | R3-A1 + R3-A2: **Wochen 1–53 mit Wochenangaben, 7 Tage** (A-67, A-68, A-28, A-29; Entwurf `docs/entwurf/KALENDER-ZEITRASTER.md` §11, §14.5, §15, §16) | R3-B: B-07 Volljährigkeit und Elternfreigabe (U-04, U-103) – nach R3-A1 | R3-D: B-12 Monitor und Startseite + Zusatz `week_text`/7 Tage – nach R3-A2 |
| 4 | R4-A1 + R4-A2: **Zeitraster je Klasse + Konflikte nach Uhrzeit** (A-69, A-31, A-30; Entwurf) | R4-B: B-08 Postfach + eigener Kursraum (U-08) | R4-D: B-11 Optimierung statt Prioritäten (nur `WeightsPanel`) |
| 5 | R5-A: B-14 Bildungsgänge, Klassengruppen | R5-B: B-21 Konten wechseln, Passkeys | R5-D: B-42 Bausteine Zeitraster und Wiederholung |
| 6 | R6-A: B-15 Klassenrollen (Modell) | R6-B: B-18 Erziehungsberechtigte + Klassen-Assistent | R6-D: B-23 Textdurchgang 1, System und Verlauf |
| 7 | R7-A: B-34 Lehrkräfte: Rollen statt Wunschklassen | R7-B: B-05 Betriebssicherheit + Konten aufräumen | R7-D: B-44 Barrierefreiheit |

### 3.2 Pakete im Einzelnen

> Hinweis 11.10.: Runden 2 abgeschlossen; für Runde 3 und 4 gilt der Entwurf `docs/entwurf/KALENDER-ZEITRASTER.md` (§11, §14.5, §15.6, §16). B-45 entfällt, B-16 geht in R3/R4 auf, B-02 behält Krit. 2–6 und rückt nach Runde 4.

**R2-A · B-04 Vertretungsplan: abwesende Lehrkräfte getrennt, keine „fehlenden Klassen“ + Betrieb sofort** – Spur A · L ·
A-56, A-18, A-21, A-00 · U-09, U-10, U-11, U-12, U-44, U-59, U-60
- Ziel: Pflichtpunkt A-56 erfüllen und die beiden hohen Betriebsfehler beseitigen.
- Abnahme: B-04 Kriterien 1–6 (`absent_teacher_details`/`absent_class_details` mit `source`, `filter_plan` auch für die
  neuen Felder, Karte „Abwesende Lehrkräfte“ mit Filter, „Abwesende Klassen“ entfällt in Vertretung und Druck, Wandertag als
  eine Zeile je Klasse, Druck in öffentlicher Sicht); Lehrkraft löscht nur selbst gemeldete Krankmeldungen (U-12, Test);
  Wochenstatistik mit `settings.days` und Aufsichtszeilen (U-59); Feldtext zum Grund korrekt (U-60 in
  `SubstitutionsPage`); `docker compose config` zeigt alle dokumentierten `SM_*` im `app`-Container (U-09); das
  systemd-Backup schließt sein Zielverzeichnis aus, zwei Läufe hintereinander wachsen nicht (U-10, Skript-Test im
  Scratchpad); keine Kommentare hinter Werten in `.env.example` (U-44).
- Dateien: `schulmanager/substitution.py`, `server/routes/features_substitutions.py`, `features_common.py` (nur
  `filter_plan`), `models.py` (Einstellung öffentliche Lehrkräfte), `pages/SubstitutionsPage.tsx`,
  `PrintSubstitutionsPage.tsx`, `components/EntryTable.tsx`, `lib/substitution.ts`, `api/types.ts` (geteilt),
  `docker-compose.yml`, `.env.example`, `deploy/systemd/schulmanager-backup.service`, `scripts/backup.sh`, `docs/BETRIEB.md`;
  Tests `test_substitution.py`, `test_lead_integration.py`. Nicht ändern: `MonitorPage.tsx`, `DashboardPage.tsx` (R3-D).

**R2-B · B-06 Krankmeldungen nur für Berechtigte + Datenschutz sofort** – Spur B · L · A-58, A-27, A-44 · U-02, U-03, U-22,
U-23, U-48 (Rechtematrix), U-89
- Ziel: Gesundheitsdaten nur für Zuständige (Pflicht A-58) und die drei hohen Datenschutzfehler im Konto-/Exportbereich
  schließen.
- Abnahme: B-06 Kriterien 1–7 (Rechte-Matrix: Fachlehrkraft 403, ohne Unterricht 404, Klassenleitung 200; Schulschalter
  `subject_teacher_absence_view`; `admin` ohne `student_absence.read`; Überlappungen, Tage ohne Unterricht); API-Token nur
  für das eigene Konto, Laufzeit höchstens die des ausstellenden Tokens bzw. Pflichtangabe (U-02, Tests mit Admin,
  Sekretariat, befristetem Token); `/me/export` enthält für Eltern keine Dokumente volljähriger Kinder (U-03, Test); Familie
  sieht ältere eigene Meldungen (U-89); Rechtetabelle `ARCHITECTURE.md` §6 stimmt mit `permissions.py` überein (U-48).
- Dateien: `server/routes/features_student_absences.py`, neu `server/absence_access.py`, `server/permissions.py`,
  `models.Settings` (nur anhängen), `features_student_self.py` (`export_documents`), `server/routes/users.py`
  (API-Token-Endpunkte), `pages/StudentAbsencesPage.tsx`, `features/students/widgets.tsx`, `docs/ARCHITECTURE.md` §6;
  Tests neu `test_student_absence_access.py`, `test_server_core.py`, `test_student_self.py`, `test_server_features.py:595`.

**R2-D · B-13 Verständliche Fehlermeldungen + Konto-Cache** – Spur D · M · A-59, A-09, A-26 (Vorarbeit) · U-01, U-38,
U-75, U-76, U-77
- Ziel: deutsche, handlungsleitende Fehlermeldungen und kein Datenleck zwischen Konten im selben Tab.
- Abnahme: B-13 Kriterien 1–4 (Validierungsfehler übersetzt, Feldnamen statt Codes, Fehler am Feld, Fehlernummer bei
  Unerwartetem; vitest für die zehn häufigsten Fälle); eine zentrale Sitzungs-Rücksetzung leert bei Abmeldung **und** 401
  `useCollection`, Datei-Limits, Kursraum-Übersicht und Badges (vitest + Browser-Nachstellung aus 05 §8: lehrer1 sieht
  317, nicht 666); „Kein Zugriff“ im App-Rahmen (U-38); `KNOWN_DETAILS` vollständig, kein doppelter Toast-Text (U-75);
  `CORE_PATHS` mit öffentlichen Pfaden (U-76); `--motion` mit Standardwert, gültige `box-shadow` (U-77).
- Dateien: `api/client.ts`, `components/ui.tsx`, `context/AuthContext.tsx`, `context/ToastContext.tsx`,
  `hooks/useCollection.ts`, `App.tsx`, `styles/tokens.css`, `styles/timetable.css`, `features/registry.ts` (geteilt),
  `features/README.md`; Ausnahmen je eine Zeile: `components/FileUpload.tsx`, `features/channels/api.ts`.

**R3-A · B-02 Planungsregeln halten, was sie versprechen + Klausurweg** – Spur A · L · A-30, A-31, A-33, A-49, A-51 ·
U-05, U-06, U-13–U-18, U-49–U-51
- Ziel: Doppelstunden zwischen den Pausen (Pflicht A-30), Regeln ohne stille Nebenwirkungen, kein Umgehen der
  Klausurregeln.
- Abnahme: B-02 Kriterien 1–8 (Demo-Test 0 Doppelstunden über Pausen; Doppel + Einzel nicht am selben Tag; Bericht mit
  Sperrzeit-Verletzungen in Klartext; leere Regel → 422; `0` = keine Grenze; `max_hours` nicht mehr im Profil; Zeitraster-
  Prüfung auf Überlappung und Pausen, `core_latest_period` wird angepasst; Vorschau vor Änderung der Unterrichtstage); `/data/exams`
  läuft durch `exams.check_exam` und dasselbe `force`-Verbot wie `/exams` (U-05, Test Lehrkraft Samstag → 409);
  Aufsichtsersatz schließt gesperrte Nachbarstunden aus (U-18); Schultage und Tagesnamen mit gleicher Obergrenze (U-49);
  Verschieben und Generator nutzen dieselbe Fach-Tagesgrenze (U-51).
- Dateien: `schulmanager/scheduler.py`, `timetable.py`, `exams.py`, `duties.py`, `teacher_profile.py`, `models.py`
  (`Settings`, `WEEKDAYS`), `server/routes/features_data.py`, `features_exams.py`, `features_teacher_profile.py`,
  `frontend/src/lib/rules.ts`, `components/RuleEditor.tsx`, `features/teacher/TeacherProfilePage.tsx`; Tests neu
  `test_planning_rules.py`, `test_exams.py`, `test_teacher_profile.py`, `test_duties.py`. Nicht ändern:
  `SettingsPanels.tsx` (R4-D).

**R3-B · B-07 Volljährigkeit automatisch, Elternfreigabe wirksam** – Spur B · L · A-44, A-11, A-58 · U-04, U-24, U-25,
U-41, U-42, U-47 (DSGVO)
- Ziel: Pflicht A-44 vollständig: Rechte wechseln am 18. Geburtstag, Volljährige steuern jeden angebotenen Bereich.
- Abnahme: B-07 Kriterien 1–7; jeder im Profil angebotene Bereich wirkt (Rechte-Matrix je Bereich: Krankmeldungen,
  Dokumente, Stundenplan, Kursräume, mit/ohne Freigabe; U-04); Eltern volljähriger Kinder ohne Freigabe sehen keine Gründe
  und melden nicht krank (U-24); Volljährigkeit überall über `parent_access.is_adult`, auch bei späterer Kontoanlage
  (U-25); Schülerprofil und Übersicht einheitlich in „du“ (U-41) und bei 390 px ohne Überlauf (U-42);
  `SICHERHEIT.md` §2.2/§2.4 mit Geburtsdatum, Elternfreigaben und den übrigen fehlenden Kategorien (U-47). Migration nur,
  falls die Freigabe je Elternkonto gespeichert wird (Name vorher reservieren, `down_revision` = `0013_parent_access`).
- Dateien: `server/parent_access.py`, `feature_models/parent_access.py` (+ Migration), `routes/features_parent_access.py`,
  `deps.py`, `accounts.py`, `letters.py`, `routes/features_letters.py`, `features_student_self.py`,
  `features_student_absences.py`, `features_channels.py` (nur Elternzugriff), `schulmanager/messaging.py`
  (`class_parents`), `maintenance.py`, `permissions.py`, `models.Settings` (nur anhängen),
  `features/students/OverviewPage.tsx`, `pages/UsersPage.tsx`, `features/elternzugriff/ParentAccessSection.tsx`,
  `features/konto/ContactSection.tsx` und `features/anmeldedienste/IdentitiesSection.tsx` (nur Anrede),
  `features/channels/widgets.tsx`, `BoardTab.tsx` (nur Anrede), `docs/SICHERHEIT.md`; Tests `test_channels_parents.py`,
  `test_student_self.py`, neu `test_parent_access_areas.py`.

**R3-D · B-12 Monitor mobil und ruhig, Startseiten-Kennzahl** – Spur D · M · A-62, A-56, A-61 · U-11 (Anzeige), U-36,
U-37, U-60 (Start), U-78, U-92 (Monitor)
- Ziel: Monitor im Flur, am Tablet und am Handy brauchbar; Startseite ohne „Klassen abwesend“ und ohne 403-Falle.
- Abnahme: B-12 Kriterien 1–6 (unter 48em nativer Bildlauf, eine Spalte, Umschalter „Heute · Morgen“; `100dvh`; „Nicht im
  Haus“ entfällt, abwesende Lehrkräfte als Block aus den B-04-Daten; Uhr als eigene Komponente; `?tage=`; „Stand:“;
  Kennzahl „Klassen abwesend“ entfällt); gemerktes Kind je Konto und Rückfall bei fremdem Kind (U-36, Browser); „Heute“
  am Wochenende sinnvoll (U-78); kein Emoji/Glyph auf dem Monitor (U-92).
- Dateien: `pages/MonitorPage.tsx`, `styles/monitor.css`, `hooks/misc.ts`, `pages/DashboardPage.tsx`,
  `components/DateNav.tsx`, `api/endpoints.ts` (geteilt). Abhängig von R2-A (B-04).

**R4-A · B-03 Import und Stammdaten ohne Datenverlust** – Spur A · L · A-01, A-37, A-44 · U-07, U-19, U-20, U-34, U-35,
U-53–U-55, U-84 (Kurse, Stammdaten), U-87 (Kurse), U-88
- Ziel: Daten aus SchILD/ASV/LUSD/Untis kommen vollständig an (inkl. Geburtsdatum), kein Löschen oder Import hinterlässt
  kaputte Verweise.
- Abnahme: B-03 Kriterien 1–7; Klasse löschen mit `force` bereinigt Kursteil-Teilnehmer und `preferred_classes`, ohne
  `force` blockieren diese Verweise (U-07, Test); Overrides werden nach Neuplanung/Untis-Import umgehängt oder mit Warnung
  entfernt (U-19); `birth_date` als ISO-Datum geprüft (U-55); Familien erhalten über `/data` nur eigene Kurse/Klassen
  (U-54); Plan-IDs mit „%“ öffnen (U-34, Browser); Woche aus dem angezeigten Schultag, Aufsichten-Woche reagiert auf
  spät geladene Einstellungen (U-35); Kurs- und Stammdaten-Grenzen wie im Backend (U-84); Fehlerbehandlung beim
  erzwungenen Löschen und Rückfrage beim Entfernen einer Aufsicht (U-87, U-88).
- Dateien: `integrations/csv_io.py`, `untis_gpu.py`, `_common.py`, `server/routes/features_exchange.py`, `features_data.py`,
  `features_common.py` (nur `check_id`), `server/jobs.py` (Overrides bei `apply`), `scheduler.py` (nur U-53),
  `pages/ImportExportPage.tsx`, `MasterDataPage.tsx`, `TimetablePage.tsx`, `PrintTimetablePage.tsx`, `DutiesPage.tsx`,
  `planning/CoursesEditor.tsx`; Tests `test_integrations.py`, `test_server_features.py` (geteilt).

**R4-B · B-08 Postfach: Empfängerkreis datensparsam + eigener Kursraum** – Spur B · L · A-13, A-10 · U-08, U-47
(Allowlist), U-61, U-63, U-67 (Kursräume/Postfach), U-87 (Material), U-94
- Ziel: Kinder und Eltern finden nur schulisch passende Personen; eigene Kursräume lassen sich wirklich mit Mitgliedern
  füllen.
- Abnahme: B-08 Kriterien 1–5 (Standards Schüler/innen und Eltern, `GET /messages/recipients` nur Erlaubtes, drei
  Auswahlfelder, Umstellung bestehender Schulen mit Hinweis, alte Unterhaltungen lesbar); Lehrende eines eigenen
  Kursraums tragen Schüler/innen und Lehrkräfte per Suche ein, Rechte im Backend geprüft (U-08, Tests + Browser);
  Postfach-Aufbewahrung läuft in `run_maintenance` (U-61); hartes Löschen + Rollback behält den Blob (U-63); Audit für
  Pinnwand, Ordner-Änderungen und Postfach-Einstellungen nach Datensparsamkeits-Regel dokumentiert bzw. ergänzt (U-67);
  Anhang-Grenzen zählen vorhandene Dateien (U-94); Allowlist in `SICHERHEIT.md`/`ARCHITECTURE.md` aktuell (U-47).
- Dateien: `schulmanager/messaging.py`, `server/routes/features_messages.py`, `models.py` (nur `messaging_*`),
  `features/messages/SettingsPage.tsx`, `RecipientPicker.tsx`, `server/routes/features_channels.py`,
  `features/channels/MembersTab.tsx`, `ChannelListPage.tsx`, `MaterialTab.tsx`, `AssignmentsTab.tsx`, `channels/api.ts`,
  `server/files.py`, `server/maintenance.py`, `docs/SICHERHEIT.md` §4.7, `docs/ARCHITECTURE.md` (Allowlist); Tests
  `test_messages.py`, `test_channels.py`, `test_files_crypto.py`.

**R4-D · B-11 Planung: „Optimierung“ statt Prioritäten, Generator ohne Technikbegriffe** – Spur D · M · A-34, A-30, A-59 ·
U-39 (Planung), U-40, U-49 (Oberfläche), U-82, U-83 (Generator), U-84 (Einstellungen), U-85, U-86
- Ziel: Pflichtpunkt A-34 – die Planung versteht ohne Handbuch, was optimiert wird.
- Abnahme: B-11 Kriterien 1–7 (höchstens sechs Ziele mit Stufen, Ist-Wert aus dem Bericht, Doppelstunden als Auswahl aus
  R3-A, eigener Reiter „Regeln“, Rechenzeit „Schnell · Normal · Gründlich“, Rückfrage bei ungespeicherten Änderungen, keine
  Erklärabsätze/Schieber in `SettingsPanels`, `GeneratorPanel`, `ReplanPanel`); Einstellungen speichern nur geänderte
  Felder (U-85); Grenzen von Pausen, Rhythmus, Schultagen, Entfall-Stufe und Attestpflicht wie im Backend (U-49, U-82,
  U-84); Ergebnis von „Lehrkräfte zuweisen“ in Klartext (U-83); Generator-Hinweis passt zum Knopf (U-86).
- Dateien: `pages/PlanningPage.tsx`, `pages/planning/SettingsPanels.tsx`, `GeneratorPanel.tsx`,
  `features/teacher/ReplanPanel.tsx` (Ausnahme); kleine Edit-Ausnahme in `planning/CurriculaEditor.tsx` nur für die
  Rückfrage beim Reiterwechsel (mit Spur A abstimmen). Abhängig von R3-A (B-02).

**R5-A · B-14 Bildungsgänge, Klassentypen, Klassengruppen, freie Namen** – Spur A · L · A-38, A-40, A-43
- Ziel: Pflichtpunkte A-38/A-43 im Datenmodell und in Stammdaten/Stundentafeln.
- Abnahme: B-14 Kriterien 1–6 (Reiter Bildungsgänge und Klassengruppen, Klassentypen anlegen/löschen mit Verweisprüfung,
  freier Name aus Muster, Jahrgangsbereich einstellbar, Vorrang Klasse > Gruppe > Bildungsgang+Jahrgang > Jahrgang,
  `cancel_min_grade` je Bildungsgang, Klassennamen in Plänen, Altdokumente laden, CSV, `group_class_ids`).
- Dateien: `schulmanager/models.py`, `planning.py`, `substitution.py` (`cancel_min_grade`), `server/routes/features_data.py`,
  `integrations/csv_io.py`, `pages/MasterDataPage.tsx`, neu `pages/masterdata/*`, `pages/planning/CurriculaEditor.tsx`,
  `TimetablePage.tsx`, `SubstitutionsPage.tsx`, `lib/csvFields.ts`.

**R5-B · B-21 Mehrere Konten, Passkeys, Passwort-Manager** – Spur B · L · A-26, A-27, A-14 · U-28, U-29, U-30, U-66,
U-68, U-73, U-91
- Ziel: Pflichtpunkte A-26/A-27 – Kontowechsel ohne Datenvermischung, Passkeys, fälschungssichere Geräte.
- Abnahme: B-21 Kriterien 1–5 (Formulare für Passwort-Manager, Passkeys mit simuliertem Authenticator, Geräte-Token nur
  gehasht, Kontenwechsler mit Test „Eltern- und Lehrerkonto parallel“, Audit, `SICHERHEIT.md`); iCal-Token als HMAC,
  TOTP-Geheimnis verschlüsselt, Migration mit Übernahme (U-28); Test-Schulkonto meldet nur verknüpfte bzw. vorgemerkte
  Konten an, OIDC-Benutzername nie für Admins (U-29); Test-Postausgang nur mit Anmeldung als Admin oder nur für eigene
  Nachrichten (U-30, Entscheidung in `VORSCHAU.md`); `/events` beachtet die Zwänge (U-66); Passwortregeln kommen vom
  Server (U-68); `reset_confirm` atomar (U-73); `safeNext` und Anbieter-URLs einheitlich geprüft (U-91).
- Dateien: `server/routes/auth.py`, `deps.py`, `security.py`, `db_models.py` (iCal/TOTP), neu `feature_models/webauthn.py`
  + Migration(en), `routes/events.py`, `routes/me.py` (iCal), `sso_providers.py`, `identities.py`, `routes/features_contact.py`,
  `pages/LoginPage.tsx`, `ChangePasswordPage.tsx`, `components/PasswordInput.tsx`, `features/konto/*` (neu
  `AccountSwitcher.tsx`), `features/anmeldedienste/IdentitiesSection.tsx`, `features/anmelderichtlinien/LinkSetupPage.tsx`,
  `context/AuthContext.tsx`, `components/Layout.tsx` (ein Edit, mit Spur D abgestimmt), `docs/SICHERHEIT.md`,
  `docs/VORSCHAU.md`; Tests `test_server_core.py`, `test_sso.py`, `test_contact.py`, neu `test_webauthn.py`.

**R5-D · B-42 Bausteine Zeitraster-Auswahl und Wiederholung** – Spur D · M · A-50, A-51
- Ziel: Vorarbeit für die Verfügbarkeit mit Ausnahmen (B-35): malen statt Umschalter-Formulare.
- Abnahme: B-42 Kriterien 1–4 (Raster Tage × Stunden per Klick/Ziehen und Tastatur, am Handy als Liste;
  Satzbaukasten „Jeden [1.] [Mittwoch] im [Monat] …“ mit Klartext; vitest Auswahl ↔ Regeldaten; Vorschau-Kalender acht
  Wochen).
- Dateien: neu `components/AvailabilityGrid.tsx`, `RecurrencePicker.tsx`, `styles/app.css`, Tests unter `lib/__tests__/`.

**R6-A · B-15 Klassenrollen im Datenmodell** – Spur A · M · A-41, A-42
- Ziel: mehrere Klassenleitungen, Stellvertretung, Abteilung, Sprecher/innen, Verwalter im Modell (Wirkung in B-19).
- Abnahme: B-15 Kriterien 1–5 (`class_teachers` mit Reihenfolge, `deputies`, `department`, `speakers`, `managers`,
  Sammlung `departments`; `class_teacher` bleibt lesbar/geschrieben; Stammdaten-Mehrfachauswahl; CSV „LUD, KEL“;
  GPU003-Abteilung als Abteilung; `class_leads`, `department_heads`; „Klassenleitung in …“).
- Dateien: `schulmanager/models.py`, `planning.py`, `substitution.py`, `server/routes/features_data.py`,
  `integrations/csv_io.py`, `untis_gpu.py`, `demo.py`, `server/demo_loader.py` (nur Klassenleitungen),
  `pages/MasterDataPage.tsx`, `lib/csvFields.ts`.

**R6-B · B-18 Erziehungsberechtigte und Schülerakte + Klassen-Assistent** – Spur B · L · A-41, A-44, A-19 · U-31, U-32,
U-33, U-71, U-95
- Ziel: Elternangaben gehen nie mehr verloren; der Klassen-Assistent arbeitet fehlerfrei und mit denselben Grenzen wie die
  Stammdaten.
- Abnahme: B-18 Kriterien 1–6 (Tabelle `guardians` verschlüsselt mit Migration, Assistent speichert Eltern immer,
  Konten aus gespeicherten Erziehungsberechtigten mit Geschwister-Zusammenführung, Schülerakte, Status je Kind,
  Zugriffsbeschränkung je Erziehungsberechtigtem); `POST /classes` ohne Konten-Standard für Planer, Jahrgang wie `/data`
  (U-32); Spaltenerkennung ohne Teilstring-Fehler, `gradeFromName` und E-Mail-Prüfung wie das Backend (U-33, U-95,
  vitest); Grenze 60/500 einheitlich (U-71); „Zurücknehmen“ mit Begleitungen atomar (U-95).
- Dateien: neu `feature_models/guardians.py` + Migration, neu `server/routes/features_guardians.py`, `letters.py`,
  `accounts.py`, `routes/features_letters.py`, `routes/features_classes.py`, `parent_access.py`,
  `features/classes/StudentListEditor.tsx`, `studentList.ts`, `accountsUi.tsx`, `StudentAccounts.tsx`, `NewClassPage.tsx`,
  `WeekTab.tsx`, neu `features/students/StudentRecordPage.tsx`, `pages/UsersPage.tsx`; Tests `test_letters.py`,
  `test_classes.py`, neu `test_guardians.py`. `zugangsdaten/*` bleibt für R6-D gesperrt bzw. umgekehrt (abstimmen).

**R6-D · B-23 Textdurchgang 1, lesbare System- und Verlaufsseiten** – Spur D · M · A-59, A-60 · U-39 (Bereiche aus B-23),
U-43, U-83 (System), U-92 (Mitteilungen)
- Ziel: weniger Text, klare Begriffe, Protokolle, die die Schulleitung lesen kann.
- Abnahme: B-23 Kriterien 1–4 (keine Erklärabsätze in Anmeldedienste, Zugangsdaten, System, Verlauf, Mitteilungen,
  Klausuren, Aufsichten; Systemzahlen mit Bezeichnungen; Verlauf als Sätze mit Auswahl-Filtern; Rundgang 390/1280 px);
  `/anmeldedienste` mit `h1` (U-43); kein Emoji bei Mitteilungen (U-92); `designRules.test.ts` erfasst auch
  `small muted`/`span.hint` als Erklärsatz.
- Dateien: `features/anmeldedienste/*`, `features/zugangsdaten/*` (nach Absprache mit R6-B), `pages/AdminPage.tsx`,
  `HistoryPage.tsx`, `AnnouncementsPage.tsx`, `ExamsPage.tsx`, `DutiesPage.tsx` (nur Texte/Darstellung),
  `lib/__tests__/designRules.test.ts`.

**R7-A · B-34 Lehrkräfte: Rollen statt Wunschklassen, schlanke Selbstverwaltung** – Spur A · M · A-48, A-49, A-36, A-08 ·
U-57, U-67 (Profil)
- Ziel: Pflichtpunkt A-48 – „Klassenleitung in“, „Ich unterrichte“, „Ich kann vertreten in“ statt Wunschklassen.
- Abnahme: B-34 Kriterien 1–6 (Felder im Profil, einmalige Übernahme der Wunschklassen, nur Verfügbarkeit und gewünschte
  Höchststunden, Vertretung bevorzugt „kann vertreten in“, Fachvorschlag mit „auf vorhandenes Fach abbilden“, „Ich bin
  neu“ für Konten ohne Lehrkraft); Begriff „Wunschklassen“ entfernt (U-57); stilles Zurückziehen offener Anträge
  auditiert (U-67).
- Dateien: `schulmanager/models.py` (`Teacher`), `teacher_profile.py`, `server/routes/features_teacher_profile.py`,
  `planning.py`, `substitution.py` (`_score`), `integrations/csv_io.py` (Spaltenname), `features/teacher/TeacherProfilePage.tsx`,
  `TeacherRequestsPage.tsx`, `pages/MasterDataPage.tsx`.

**R7-B · B-05 Betriebssicherheit + Konten und Betrieb aufräumen** – Spur B · L · A-00, A-24 · U-26, U-27, U-45, U-46, U-62,
U-64 (Kern), U-65, U-67 (Kern), U-69, U-70, U-74, U-84 (System), U-90, U-100
- Ziel: ein Fehlklick oder das Demo-Passwort kann den Betrieb nicht zerstören, Sicherungen stellen alles wieder her, die
  Betriebsdoku stimmt.
- Abnahme: B-05 Kriterien 1–6 (Demo in Produktion gesperrt, Demo-Passwort-Konten gesperrt, Konten ohne Datensatz,
  Rückgängig mit Vorschau fremder Änderungen, Sicherung mit Dateien und Rundlauf-Test); `teacher_id`/`student_id` passend
  zur Rolle (U-26); vollständige Pseudonymisierung beim Löschen (U-27); Version aus `SM_APP_VERSION` (U-45);
  `notify.check_changes` mit eigenem Variablennamen + Regressionstest (U-46); Aufbewahrung für Outbox-Zeilen (U-62); fremde
  Datensätze → 404 im Kern (U-64); Audit für Wartung, Dateien, iCal, Outbox-Retry, 2FA-Setup (U-67); `/audit` in UTC (U-65);
  `history_only` ausgewertet oder entfernt (U-69); Stapel ohne eigenes Konto (U-70); Zugangsbrief mit Klasse, Kinderliste
  in einem Aufruf (U-90); Betriebsdoku und Skripte laut U-100 korrigiert.
- Dateien: `server/routes/admin.py`, `system.py`, `history.py`, `users.py`, `server/demo_loader.py` (nur Konten), `config.py`,
  `deps.py`, `accounts.py`, `backups.py`, `maintenance.py`, `notify.py`, `letters.py`, `routes/features_letters.py`,
  `pages/AdminPage.tsx`, `HistoryPage.tsx`, `UsersPage.tsx`, `deploy/docker/entrypoint.sh`, `deploy/nginx/schulmanager.conf`,
  `deploy/Caddyfile`, `docs/BETRIEB.md`, `README.md`, `.env.example`; Tests `test_server_core.py`,
  `test_server_core_store.py`, `test_letters.py`.

**R7-D · B-44 Barrierefreiheit prüfen, Erklärung veröffentlichen** – Spur D · M · A-61 · U-79
- Ziel: Nachweis nach BITV 2.0 / WCAG 2.1 AA (Vergabevoraussetzung für Schulen).
- Abnahme: B-44 Kriterien 1–5 (axe-core über Playwright für die 20 wichtigsten Seiten je Rolle in der Testsuite,
  dokumentierte Tastatur-/Screenreader-Prüfung, Kontrast-Test der Tokens, 200 % Zoom, Erklärung zur Barrierefreiheit,
  PDF-Tags durch Spur B angekündigt); `TimetableList` per Tastatur, `Tabs` mit `tabpanel`, Grid-Rollen bzw. ohne
  `aria-selected` an `<tr>`, Menü mit Pfeiltasten (U-79).
- Dateien: neu `frontend/e2e/a11y.spec.ts`, `styles/tokens.css`, neu `pages/AccessibilityPage.tsx`,
  `components/TimetableGrid.tsx`, `ui.tsx`, `VirtualTable.tsx`, `Layout.tsx`, `EntryTable.tsx` (Ausnahme, Spur A
  informieren); `server/pdf.py` als angekündigte Teilaufgabe der Spur B.

### 3.3 Danach (Runde 8 ff., in dieser Reihenfolge)

1. Spur A B-16 Zeitraster-Rechner und Schulwoche (A-31, A-32) → Spur D B-22 Einstellungen an ihrem Ort (A-32).
2. Spur B B-19 Klassenrollen wirksam machen (A-41, A-42, A-43; U-96).
3. Spur A B-25 Schuljahr, Halbjahre, Schulwochen (A-28; U-56) → B-27 Klassenarbeiten je Halbjahr (A-33).
4. Spur B B-29 Krankmeldungen in der Klassenansicht (A-52, A-57, A-58).
5. Spur B B-30 Unterrichtsstunde, Hausaufgaben (A-54, A-55) → Spur D B-32 Stundenplan-Ansichten (A-54, A-32).
6. Spur A B-37 Schuljahreswechsel und Versetzung (A-39).
7. Spur B B-20 Rest: „nur für Schüler/innen“, Eltern-Einsicht je Raum, Hinweis bei Entfall (A-46, A-47).
8. Spur A B-28 Monitor-Profile → Spur D B-33 Monitor modular (A-62).
9. Spur A B-35 Verfügbarkeit mit Ausnahmen (A-50, A-51) → B-36 faire Vertretung (A-49; U-21).
10. Spur B B-31 Anwesenheit und Fehlstunden je Fach (A-53).
11. Spur A B-17 Konfigurationsdateien (A-37, A-64).
12. Spur A B-45 Rhythmus je Klasse (A-29, A-28) → B-46 Plan-Perioden „gültig ab“.
13. Spur B B-49 Systemeinstellungen ohne IT (A-18 Oberfläche), B-38, B-40, B-41, B-39, B-47, B-48.
14. Spur D B-24 Startseiten je Rolle, B-43 Textdurchgang 2 (U-39, U-80, U-81, U-97), B-50, B-51.

### 3.4 Lückenfüller (ohne feste Runde, nur in der Zone der jeweiligen Spur)

- Spur A: U-52 (Kurse mit Wochen gegen die Stundentafel), U-58 (Webhook-Zeitstempel).
- Spur B: U-64 für Kursräume und Klassen-Seite, U-72 (`extra=forbid`, Passwortlängen).
- Alle Spuren im eigenen Bereich: U-93, U-98, U-99; U-101 (Tests) mit dem jeweiligen Paket, `tests/conftest.py` nur nach
  Absprache.

## Nachschreibtermine, Vertretungsplan nur Personal (12.10.2026)
| ID | Status | Nachweis | Offen |
|---|---|---|---|
| A-67 | erledigt | `permissions.py` (`substitution.read`), `features_substitutions.py`, `lib/permissions.ts`, `tests/test_makeups.py` | – |
| A-68 | teilweise | `server/makeups.py`, `routes/features_makeups.py`, Migration `0026_exam_makeups`, `features/makeups/`, Kalender-Einträge | kein Postfach-/E-Mail-Hinweis (nur Startkachel, Zähler, Live); Nachteilsausgleich-Hinweis (`ExamHints`) nennt Nachschreiben noch nicht; `me/today` listet Nachschreibtermine nicht |
| A-69 | erledigt | `features_student_self.py` (Ablehnung mit Grund, Archivieren), `student_self.py` (Beschriftungen) | Dokumentversionen als eigene Ansicht |
| A-70 | erledigt | `ExamsPage.tsx`, `features_exams.py` (`room_lesson`, `channel_id`, `names`) | – |


## Plan prüfen (13.10.2026)
| ID | Status | Nachweis | Offen |
|---|---|---|---|
| Zielbild Dauerprüfung + Vorschlagspakete | erledigt | `docs/PLAN-PRUEFUNG.md`, `server/autoplan.py`, `server/proposals.py`, `plan_proposals.py`, Migration `0035_plan_proposals`, `features/planpruefung/`, `tests/test_plan_proposals.py` | Gültigkeit „ab Datum“ nur als Hinweis (Übernahme gilt für alle Wochen); keine Postfach-Nachricht an die Berechtigten |
| Bestätigungsmodus Vertretung | erledigt | `settings.substitution_confirm`, `features_common.day_plan(proposals=)`, `POST /substitutions/release`, `tests/test_substitution_confirm.py` | betrifft nur Vertretung/Betreuung (nicht Entfall/Verlegung) |
| Vertretungsseite entschlackt | teilweise | `SubstitutionsPage.tsx` (Filter/Abwesenheiten/Warnungen eingeklappt, Hilfe-Symbol) | Eintragsdetail (`EntryPanel`) und Statistik unverändert |

## Benachrichtigungszentrale (13.10.2026)
| ID | Status | Nachweis | Offen |
|---|---|---|---|
| Glocke, Liste, Einstellungen je Ereignis, Schulvorgaben (Moodle-Lücke #3) | erledigt (ohne Push) | `docs/BENACHRICHTIGUNGEN.md`, `server/notifications.py`, `notification_hooks.py`, `routes/features_notifications.py`, Migration `0041_notifications`, `features/benachrichtigungen/`, `tests/test_notifications*.py` | Push/PWA (B-41) bewusst später; Quelle für Nachrichten (`message`) und Freigabe-Zeitpunkte fehlt |

## Produktreife (16.10.2026)

| ID | Status | Nachweis | Offen |
|---|---|---|---|
| Betriebsmodus `SM_MODE`, Abbruch bei fehlenden Pflichtwerten, Demo im Echtbetrieb aus | erledigt | `config.py`, `docs/PRODUKTREIFE.md` §2A, `tests/test_produktreife_betrieb.py` | Hauptinstanz-Umstellung ist Entscheidung E1 |
| Einrichtungsassistent mit gespeichertem Fortschritt, Schuldaten, Ferien, Testmail | erledigt | `routes/setup.py`, `pages/SetupPage.tsx`, `tests/test_setup.py` | Logo in Anmeldeseite/Briefe, Zeitraster-/Stundentafel-Vorlagen, Direktimporte |
| Schuljahreswechsel mit Vorschau und Rückgängig | erledigt | `year_change.py`, `features/schuljahreswechsel/`, `tests/test_year_change.py`, Migration `0046` | Anschluss Löschkonzept (`register_leaver_handler`), Kurse/Oberstufe fortschreiben |
| Statusseite, Fehlerprotokoll, Test-Restore | erledigt | `ops.py`, `features/betrieb/` | E-Mail-Alarm, externe Sicherung auf der Statusseite |
| Installation: `scripts/init-env.sh`, `docs/INSTALLATION.md`, `.env.example` | erledigt | | Images/Release-Prozess |
| Datenschutz-Vorlagen, Hilfe in der App | erledigt (Entwürfe) | `docs/datenschutz/`, `docs/hilfe/` | juristische Prüfung (E5) |
