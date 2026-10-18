---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/classes/"
stand: 2026-10-12 22:40
generator: schulmanager-regen
---

# Feature classes

> Frontend · 24 Datei(en) · 6875 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Klassen-Seite (`/klassen`, `/klassen/:id`, `/klassen/neu`) mit Stundentafel, Woche, Personen, Schülerkonten-Assistent und das **Klassenbuch** (`/klassenbuch`: Anwesenheit, Thema, Hausaufgabe je Stunde).

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/klassen` | `ClassesPage` | anyOf: ANY_OF | Klassen |
| `/klassen/neu` | `NewClassPage` | anyOf: ['masterdata.edit'] | Neue Klasse |
| `/klassen/:id` | `ClassDetailPage` | anyOf: ANY_OF | Klassen |
| `/klassenbuch` | `RegisterPage` | anyOf: ['student_absence.read'] | Klassenbuch |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/classes/AddStudentsDialog.tsx` | 96 | „Schüler/in hinzufügen“ auf der Klassen-Seite (§11.3): gleiche Eingabe wie im Klassen-Assistenten, Konten optional, Probelauf → H… |
| `frontend/src/features/classes/CalendarWeek.tsx` | 491 | Kalenderwoche (Stundenplan mit Datum) für Klasse, Lehrkraft, Raum oder Schüler/in – `GET /calendar/week`. KW-Navigation (Vor/Zurü… |
| `frontend/src/features/classes/ClassCurriculumSection.tsx` | 81 | Stundentafel im Dialog „Klasse anlegen/bearbeiten“ (Stammdaten): bei bestehenden Klassen die aktuelle Tafel, bei neuen Klassen vo… |
| `frontend/src/features/classes/ClassDetailPage.tsx` | 122 | Klasse im Detail (`/klassen/:id`): Kopf (Raum/Klassenleitung inline änderbar) und Reiter Wochenplan / Lehrkräfte / Schüler/innen… |
| `frontend/src/features/classes/ClassHeader.tsx` | 369 | Kopf der Klassen-Seite: Jahrgang, Standort, Schülerzahl, Klassenraum und Klassenleitung. Mit `can_edit` (masterdata.edit) direkt… |
| `frontend/src/features/classes/ClassesPage.tsx` | 146 | Klassen suchen (`/klassen`): Suchfeld (Klasse, Klassenleitung, Raum), Filter Standort, Liste nach Jahrgang. Suche und Filter steh… |
| `frontend/src/features/classes/CurriculumTab.tsx` | 215 | Stundentafel einer Klasse: welches Fach wie viele Wochenstunden hat. Ändern dürfen Stammdaten/Planung und die Klassenleitung. Bei… |
| `frontend/src/features/classes/NewClassPage.tsx` | 290 | Klassen-Assistent `/klassen/neu` (§11.3): (1) Klasse → (2) Schülerliste einfügen → (3) Konten (Probelauf) → (4) Ergebnis mit Zuga… |
| `frontend/src/features/classes/PeopleTabs.tsx` | 185 | Reiter „Lehrkräfte“ (Fach → Kurs/Kursteil → Lehrkraft, Klassenleitung markiert) und „Schüler/innen“ (mit Kurswahl). |
| `frontend/src/features/classes/RegisterOverview.tsx` | 175 | Klassenbuch-Übersicht der Klassenleitung (Tab „Klassenbuch“ auf der Klassenseite): Schüler/innen untereinander, die Unterrichtsst… |
| `frontend/src/features/classes/RegisterPage.tsx` | 431 | `/klassenbuch` – Klassenbuch: Klasse und Tag wählen, je Stunde die Anwesenheit eintragen (zuerst niemand eingetragen; anwesend /… |
| `frontend/src/features/classes/StudentAccounts.tsx` | 204 | Reiter „Schüler/innen“ mit Konten & Zugangsdaten (§11.3): * „Schüler/in hinzufügen“ (masterdata.edit), * Auswahl → „Neue Zugangsd… |
| `frontend/src/features/classes/StudentListEditor.tsx` | 218 | Schülerliste eingeben (Klassen-Assistent und „Schüler/in hinzufügen“, §11.3): Liste aus Excel/Word/Text einfügen → Vorschau als b… |
| `frontend/src/features/classes/WeekTab.tsx` | 604 | Reiter „Wochenplan“: konkrete Kalenderwoche der Klasse inkl. Vertretungen (`GET /classes/{id}/week`). * Wochennavigation (`compon… |
| `frontend/src/features/classes/accountsUi.tsx` | 265 | Konten-Bausteine des Klassen-Assistenten und von „Schüler/in hinzufügen“ (§11.3): Konto-Optionen (inkl. sofortigem E-Mail-Versand… |
| `frontend/src/features/classes/api.ts` | 89 | Endpunkte der Klassen-Seite (§10.2). Zurücknehmen eines Ausfalls über das bestehende `DELETE /absences/{id}`. |
| `frontend/src/features/classes/calendarOverlay.ts` | 216 | Kalenderwoche: Prüfungen, Hausaufgaben, Termine und Abwesenheit als Blöcke bzw. kleine Zeichen in den Stundenfeldern (reine Funkt… |
| `frontend/src/features/classes/classes.css` | 712 | Stylesheet |
| `frontend/src/features/classes/components.tsx` | 86 | Kleine Bausteine der Klassen-Seite: Status-Badge (Text + Kurzzeichen, nie nur Farbe), Namensauflösung, Stundenauswahl. |
| `frontend/src/features/classes/dialogs.tsx` | 404 | Dialoge im Wochenplan (nur `can_plan` = substitution.edit): * „Findet nicht statt“ – eine Stunde (bzw. Block) eines Kurses an ein… |
| `frontend/src/features/classes/logic.ts` | 644 | Reine Hilfsfunktionen der Klassen-Seite (ohne React, getestet in classes.test.ts): Kalenderwoche, Klassenliste, Zellen des Wochen… |
| `frontend/src/features/classes/module.tsx` | 39 | Feature-Modul „Klassen“ (ARCHITECTURE.md §10.3) für die Registry (`features/registry.ts`). * `/klassen` – Klasse suchen (Name, Kl… |
| `frontend/src/features/classes/studentList.ts` | 436 | Schülerliste einfügen (Klassen-Assistent, §11.3) – reine Logik, ohne React. Erkannte Formate (je Zeile eine Person, Leerzeilen we… |
| `frontend/src/features/classes/types.ts` | 357 | Typen der Klassen-Seite (ARCHITECTURE.md §10.2) – Spiegel von `schulmanager/server/routes/features_classes.py`. Alle Stunden 0-ba… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/calendar/week` | [[Routen features_calendar]] · `week` (`features_calendar.py:65`) |
| GET | `/classes` | [[Routen features_classes]] · `list_classes` (`features_classes.py:264`) |
| POST | `/classes` | [[Routen features_classes]] · `create_class` (`features_classes.py:1077`) |
| GET | `/classes/{…}` | [[Routen features_classes]] · `class_detail` (`features_classes.py:278`) |
| PATCH | `/classes/{…}` | [[Routen features_classes]] · `patch_class` (`features_classes.py:382`) |
| GET | `/classes/{…}/curriculum` | [[Routen features_classes]] · `get_class_curriculum` (`features_classes.py:506`) |
| PUT | `/classes/{…}/curriculum` | [[Routen features_classes]] · `put_class_curriculum` (`features_classes.py:516`) |
| POST | `/classes/{…}/not-taking-place` | [[Routen features_classes]] · `not_taking_place` (`features_classes.py:795`) |
| POST | `/classes/{…}/students` | [[Routen features_classes]] · `add_students` (`features_classes.py:1118`) |
| GET | `/classes/{…}/week` | [[Routen features_classes]] · `class_week` (`features_classes.py:596`) |
| GET | `/classes/{…}/accounts` | [[Routen features_letters]] · `class_accounts` (`features_letters.py:347`) |
| POST | `/letters/batches` | [[Routen features_letters]] · `create_batch` (`features_letters.py:103`) |
| GET | `/exam-makeups` | [[Routen features_makeups]] · `list_makeups` (`features_makeups.py:147`) |
| GET | `/register/classes` | [[Routen features_register]] · `register_classes` (`features_register.py:215`) |
| GET | `/register/day` | [[Routen features_register]] · `register_day` (`features_register.py:152`) |
| PUT | `/register/lesson?class_id={…}` | [[Routen features_register]] · `save_lesson` (`features_register.py:363`) |
| GET | `/register/now` | [[Routen features_register]] · `register_now` (`features_register.py:314`) |
| GET | `/register/overview` | [[Routen features_register]] · `register_overview` (`features_register.py:234`) |
| DELETE | `/absences/{…}` | [[Routen features_substitutions]] · `delete_absence` (`features_substitutions.py:334`) |

## Backend-Notizen

[[Routen features_calendar]], [[Routen features_classes]], [[Routen features_letters]], [[Routen features_makeups]], [[Routen features_register]], [[Routen features_substitutions]]

## Nutzt (Frontend)

- [[Feature makeups]] – `api`
- [[Feature students]] – `AbsenceHistory`, `BirthDateEditor`, `ExamHints`, `useChild`
- [[Feature zugangsdaten]] – `api`, `components`, `types`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `colors`, `dates`, `format` …
- [[Frontend Komponenten]] – `Abbr`, `ClassPlanningFields`, `ConfirmChanges`, `HelpTip`, `Icon` …

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Feature students]]
- [[Seite DashboardPage]]
- [[Seite MasterDataPage]]
- [[Seite TimetablePage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
