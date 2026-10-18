---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/api/, features/*/api.ts"
stand: 2026-10-12 22:55
generator: schulmanager-regen
---

# Frontend API-Schicht

> HTTP-Client, Endpunkte, SSE und Fehlertexte. Einstieg: [[Frontend Übersicht]]

## Zweck

`client.ts` ist der schlanke typisierte HTTP-Client für `/api/v1`: setzt den CSRF-Header `X-CSRF-Token` bei ändernden Methoden, übersetzt Fehler (`errors.ts` → deutsche Meldungen, Feldzuordnung), behandelt 401 (Sitzungs-Reset), 409-Bestätigungen und Passwort-/2FA-Zwang. `endpoints.ts` bündelt die Kern-Endpunkte als typisierte Namensräume; jedes Feature bringt eine eigene `api.ts` mit. `events.ts` hält die **eine** SSE-Verbindung zu `/api/v1/events` (Ereignisse `change`, `job`, `ping`, automatischer Reconnect). `files.ts` kapselt Upload/Download der verschlüsselten Dateiablage ([[Routen files]]). `types.ts` (~1100 Zeilen) spiegelt die Datenverträge des Backends.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/api/client.ts` | 401 | Schlanker, typisierter HTTP-Client für die REST-API (/api/v1). - Cookie-Authentifizierung (credentials: same-origin) - CSRF-Schut… |
| `frontend/src/api/endpoints.ts` | 410 | Typisierte Endpunkte gemäß docs/ARCHITECTURE.md §6. |
| `frontend/src/api/errors.ts` | 289 | Verständliche Fehlermeldungen (B-13, A-59): übersetzt Validierungsfehler des Backends (FastAPI/Pydantic, `detail: [{type, loc, ms… |
| `frontend/src/api/events.ts` | 186 | Gemeinsame Server-Sent-Events-Verbindung zu /api/v1/events mit automatischem Reconnect. Ereignisse: `change` {version,scope,dates… |
| `frontend/src/api/files.ts` | 296 | Dateiablage (Basisdienst, docs/ARCHITECTURE.md §9.2) – Backend: `schulmanager/server/routes/files.py`. - {@link uploadFile}: Uplo… |
| `frontend/src/api/types.ts` | 1247 | Typen gemäß Schnittstellenvertrag (docs/ARCHITECTURE.md §3, §4, §6). Alle Zeitangaben 0-basiert: Tag 0 = Montag, Stunde 0 = 1. St… |

## Endpunkt-Namensräume

| Datei | Namensraum | Aufrufe | Backend-Notizen |
|---|---|---|---|
| `api/endpoints.ts` | `auth` | 13 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `users` | 18 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `history` | 4 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `admin` | 4 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `data` | 4 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `settings` | 3 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `calendar` | 1 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `planning` | 13 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `timetable` | 4 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `substitutions` | 4 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `absences` | 5 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `overrides` | 3 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `me` | 2 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `monitor` | 3 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `exams` | 5 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `announcements` | 4 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `api/endpoints.ts` | `studentAbsences` | 8 | [[Routen admin]], [[Routen auth]], [[Routen features_announcements]], [[Routen features_calendar]], [[Routen features_data]], [[Routen features_exams]] … |
| `features/anmeldedienste/api.ts` | `ssoApi` | 12 | [[Routen features_sso]] |
| `features/anmelderichtlinien/api.ts` | `policyApi` | 4 | [[Routen features_login_policy]], [[Routen features_sso]] |
| `features/anmelderichtlinien/api.ts` | `linkApi` | 2 | [[Routen features_login_policy]], [[Routen features_sso]] |
| `features/api-zugaenge/api.ts` | `accessApi` | 5 | [[Routen features_api_access]] |
| `features/channels/api.ts` | `channelsApi` | 39 | [[Routen features_absence_log]], [[Routen features_channels]], [[Routen features_class_info]] |
| `features/chats/api.ts` | `chatsApi` | 32 | [[Routen features_chats]] |
| `features/classes/api.ts` | `classesApi` | 9 | [[Routen features_classes]] |
| `features/formulare/api.ts` | `formsApi` | 22 | [[Routen features_forms]] |
| `features/konto/api.ts` | `contactApi` | 6 | [[Routen features_contact]] |
| `features/konto/api.ts` | `adminContactApi` | 3 | [[Routen features_contact]] |
| `features/konto/api.ts` | `resetApi` | 5 | [[Routen features_contact]] |
| `features/konto/api.ts` | `devOutboxApi` | 1 | [[Routen features_contact]] |
| `features/makeups/api.ts` | `makeupsApi` | 6 | [[Routen features_makeups]] |
| `features/messages/api.ts` | `mailApi` | 7 | [[Routen features_mail]], [[Routen features_messages]] |
| `features/messages/api.ts` | `messagesApi` | 31 | [[Routen features_mail]], [[Routen features_messages]] |
| `features/students/api.ts` | `studentSelfApi` | 9 | [[Routen features_channels]], [[Routen features_messages]], [[Routen features_student_absences]], [[Routen features_student_self]] |
| `features/students/api.ts` | `documentsApi` | 6 | [[Routen features_channels]], [[Routen features_messages]], [[Routen features_student_absences]], [[Routen features_student_self]] |
| `features/teacher/api.ts` | `teacherProfileApi` | 5 | [[Routen features_planning]], [[Routen features_teacher_profile]], [[Routen features_timetable]] |
| `features/teacher/api.ts` | `teacherRequestsApi` | 5 | [[Routen features_planning]], [[Routen features_teacher_profile]], [[Routen features_timetable]] |
| `features/teacher/api.ts` | `replanApi` | 5 | [[Routen features_planning]], [[Routen features_teacher_profile]], [[Routen features_timetable]] |
| `features/teacher/api.ts` | `timetableScopeApi` | 1 | [[Routen features_planning]], [[Routen features_teacher_profile]], [[Routen features_timetable]] |
| `features/zugangsdaten/api.ts` | `lettersApi` | 3 | [[Routen features_letters]] |
| `features/zugangsdaten/api.ts` | `passwordsApi` | 5 | [[Routen features_letters]] |

## Nutzt (Frontend)

- [[Frontend Basis]] – `live`, `session`

## Wird genutzt von

- [[Feature anmeldedienste]]
- [[Feature anmelderichtlinien]]
- [[Feature api-zugaenge]]
- [[Feature channels]]
- [[Feature chats]]
- [[Feature classes]]
- [[Feature elternzugriff]]
- [[Feature formulare]]
- [[Feature konto]]
- [[Feature makeups]]
- [[Feature messages]]
- [[Feature nachrichten]]
- [[Feature students]]
- [[Feature teacher]]
- [[Feature zugangsdaten]]
- [[Frontend App und Routing]]
- [[Frontend Basis]]
- [[Frontend Komponenten]]
- [[Seite AccessLettersPage]]
- [[Seite AdminPage]]
- [[Seite AnnouncementsPage]]
- [[Seite ChangePasswordPage]]
- [[Seite DashboardPage]]
- [[Seite DutiesPage]]
- [[Seite ExamsPage]]
- [[Seite HistoryPage]]
- [[Seite ImportExportPage]]
- [[Seite LicensePage]]
- [[Seite LoginPage]]
- [[Seite MasterDataPage]]
- [[Seite MonitorAdminPage]]
- [[Seite MonitorPage]]
- [[Seite PlanningPage]]
- [[Seite PrintSubstitutionsPage]]
- [[Seite ProfilePage]]
- [[Seite RightsPage]]
- [[Seite SetupPage]]
- [[Seite SignedOutPage]]
- [[Seite StudentAbsencesPage]]
- [[Seite SubstitutionsPage]]
- [[Seite TimetablePage]]
- [[Seite UsersPage]]

## Siehe auch

- [[Routen Übersicht]] · [[Frontend Übersicht]] · [[Server events]] (Gegenstück zu `events.ts`) · [[Server deps]] (CSRF/Sitzung)

<!-- eigene Notizen -->
