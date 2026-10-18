---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/teacher/"
stand: 2026-10-12 22:48
generator: schulmanager-regen
---

# Feature teacher

> Frontend · 16 Datei(en) · 3066 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Lehrer-Selbstverwaltung: eigenes Profil mit Zeitfenstern (`/lehrkraft/profil`), Anträge prüfen (`/planung/antraege`), Neuplanungs-Panel (Replan).

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/lehrkraft/profil` | `TeacherProfilePage` | anyOf: ['profile.teacher_self'] | Mein Profil als Lehrkraft |
| `/planung/antraege` | `TeacherRequestsPage` | anyOf: ['teacher_requests.review'] | Anträge von Lehrkräften |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/teacher/ReplanPanel.tsx` | 213 | „Stundenplan für diese Lehrkraft neu planen“ (§9.3, dynamische Anpassung): startet einen Generator-Job, bei dem alle übrigen Stun… |
| `frontend/src/features/teacher/TeacherFields.tsx` | 246 | Felder für den Lehrer-Editor in den Stammdaten (Planung/Sekretariat): Arbeitszeitfenster mit Vorschau und Konfliktprüfung sowie S… |
| `frontend/src/features/teacher/TeacherProfilePage.tsx` | 430 | „Mein Profil als Lehrkraft“ (/lehrkraft/profil): Fächer, Wunschklassen, Deputat, Arbeitszeitfenster und Wünsche selbst pflegen –… |
| `frontend/src/features/teacher/TeacherRequestsPage.tsx` | 323 | „Anträge von Lehrkräften“ (/planung/antraege, Recht `teacher_requests.review`): Profiländerungen (Fächer, Wunschklassen, Deputat,… |
| `frontend/src/features/teacher/WorkGrid.tsx` | 396 | „Arbeitszeiten festlegen“: Wochenraster (Tage × Stunden) zum Antippen. Stunde antippen sperrt sie (kein Unterricht), nochmal anti… |
| `frontend/src/features/teacher/api.ts` | 52 | Endpunkte der Lehrer-Selbstverwaltung (§9.3) und der Planauswahl (Lehrer-Scope). |
| `frontend/src/features/teacher/badge.tsx` | 26 | Menü-Badge „Anträge von Lehrkräften“ (bewusst klein: wird beim App-Start geladen, siehe module.tsx). |
| `frontend/src/features/teacher/components.tsx` | 323 | Bausteine der Lehrer-Selbstverwaltung: Zeitfenster-Editor, Verfügbarkeitsraster, Konflikte, Vergleich alt/neu. |
| `frontend/src/features/teacher/hooks.ts` | 19 | React-Hooks der Lehrer-Selbstverwaltung / des Lehrer-Scopes. |
| `frontend/src/features/teacher/module.tsx` | 46 | Feature-Modul „Lehrer-Selbstverwaltung“ (ARCHITECTURE.md §9.3) für die Registry (`features/registry.ts`). * `/lehrkraft/profil` –… |
| `frontend/src/features/teacher/replan.ts` | 21 | Neuplanungs-Jobs (`kind: "replan_teacher"`) – reine Hilfsfunktionen (testbar, ohne React). |
| `frontend/src/features/teacher/scope.ts` | 62 | Lehrer-Scope im Frontend (ARCHITECTURE.md §9.3) – reine Hilfsfunktionen (testbar, ohne React). Lehrkräfte haben `plans.read_all`… |
| `frontend/src/features/teacher/teacher.css` | 315 | Stylesheet |
| `frontend/src/features/teacher/types.ts` | 200 | Typen der Lehrer-Selbstverwaltung (ARCHITECTURE.md §9.3) – lokal im Modul, damit geteilte Dateien (api/types.ts) unverändert blei… |
| `frontend/src/features/teacher/widgets.tsx` | 100 | Startseiten-Kacheln der Lehrer-Selbstverwaltung (werden erst bei Bedarf geladen, siehe module.tsx): Lehrkräfte sehen den Stand ih… |
| `frontend/src/features/teacher/windows.ts` | 294 | Reine Hilfsfunktionen für Arbeitszeitfenster (testbar, ohne React). Regel wie im Backend (schulmanager/teacher_profile.py): Eine… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/planning/jobs` | [[Routen features_planning]] · `list_jobs` (`features_planning.py:243`) |
| GET | `/planning/jobs/{…}` | [[Routen features_planning]] · `get_job` (`features_planning.py:250`) |
| POST | `/planning/jobs/{…}/apply` | [[Routen features_planning]] · `apply_job` (`features_planning.py:279`) |
| POST | `/planning/jobs/{…}/cancel` | [[Routen features_planning]] · `cancel_job` (`features_planning.py:264`) |
| POST | `/planning/replan-teacher/{…}` | [[Routen features_planning]] · `replan_teacher` (`features_planning.py:183`) |
| GET | `/me/teacher-profile` | [[Routen features_teacher_profile]] · `my_profile` (`features_teacher_profile.py:279`) |
| PUT | `/me/teacher-profile` | [[Routen features_teacher_profile]] · `change_my_profile` (`features_teacher_profile.py:312`) |
| POST | `/me/teacher-profile/preview` | [[Routen features_teacher_profile]] · `my_profile_preview` (`features_teacher_profile.py:305`) |
| DELETE | `/me/teacher-profile/request` | [[Routen features_teacher_profile]] · `withdraw_my_request` (`features_teacher_profile.py:369`) |
| POST | `/teacher-profiles/{…}/preview` | [[Routen features_teacher_profile]] · `teacher_preview` (`features_teacher_profile.py:495`) |
| GET | `/teacher-requests` | [[Routen features_teacher_profile]] · `list_requests` (`features_teacher_profile.py:398`) |
| GET | `/teacher-requests/{…}` | [[Routen features_teacher_profile]] · `get_request` (`features_teacher_profile.py:428`) |
| POST | `/teacher-requests/{…}/approve` | [[Routen features_teacher_profile]] · `approve_request` (`features_teacher_profile.py:441`) |
| POST | `/teacher-requests/{…}/reject` | [[Routen features_teacher_profile]] · `reject_request` (`features_teacher_profile.py:479`) |
| GET | `/teacher-requests/summary` | [[Routen features_teacher_profile]] · `requests_summary` (`features_teacher_profile.py:385`) |
| GET | `/timetable/allowed` | [[Routen features_timetable]] · `allowed_refs` (`features_timetable.py:85`) |

## Backend-Notizen

[[Routen features_planning]], [[Routen features_teacher_profile]], [[Routen features_timetable]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `HelpTip`, `Icon`, `RuleEditor`, `SearchSelect` …

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Seite DutiesPage]]
- [[Seite ExamsPage]]
- [[Seite MasterDataPage]]
- [[Seite SubstitutionsPage]]
- [[Seite TimetablePage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
