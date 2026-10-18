---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/App.tsx, main.tsx, features/registry.ts"
stand: 2026-10-12 22:55
generator: schulmanager-regen
---

# Frontend App und Routing

> Einstieg, Routing, Zugriffsschutz und Feature-Registry. Einstieg: [[Frontend Übersicht]]

## Zweck

`main.tsx` startet React; `App.tsx` setzt `ThemeProvider`, `ToastProvider`, `AuthProvider` ([[Frontend Basis]]) und den `BrowserRouter`. Öffentliche Routen (Login, Passwort vergessen/zurücksetzen) stehen direkt in `App.tsx`; alle übrigen hängen hinter einem Zugriffsschutz (`AccessGate`, `canAccessPath`) und laden Seiten per `lazy()`. Zusätzliche Seiten kommen aus Feature-Modulen: `features/registry.ts` lädt `./*/module.tsx`, jedes Modul ruft `defineFeature({id, routes, nav, widgets, background})` auf; Kernpfade stehen in `CORE_PATHS`. Pflichtseiten (`/passwort`, `/zwei-faktor`, `/konten-verbinden`) werden vom Guard erzwungen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/App.tsx` | 300 |  |
| `frontend/src/features/registry.ts` | 320 | Feature-Registry (Erweiterung 2, docs/ARCHITECTURE.md §9.2). Jedes Feature liegt in `src/features/<feature>/` und exportiert aus… |
| `frontend/src/main.tsx` | 26 |  |

## Routenkarte

### Kernseiten

| Route | Seite |
|---|---|
| `/` (HomeRoute) | [[Seite DashboardPage]] |
| `/login` | [[Seite LoginPage]] |
| `/stundenplan`, `/stundenplan/:kind`, `/stundenplan/:kind/:ref` | [[Seite TimetablePage]] |
| `/vertretung` | [[Seite SubstitutionsPage]] |
| `/planung`, `/planung/:tab` | [[Seite PlanningPage]] |
| `/stammdaten`, `/stammdaten/:tab` | [[Seite MasterDataPage]] |
| `/klausuren` | [[Seite ExamsPage]] |
| `/aufsichten` | [[Seite DutiesPage]] |
| `/mitteilungen` | [[Seite AnnouncementsPage]] |
| `/krankmeldungen` | [[Seite StudentAbsencesPage]] |
| `/benutzer` | [[Seite UsersPage]] |
| `/monitore` | [[Seite MonitorAdminPage]] |
| `/monitor/:site?` | [[Seite MonitorPage]] |
| `/lizenz` | [[Seite LicensePage]] |
| `/rechte` | [[Seite RightsPage]] |
| `/einrichtung` | [[Seite SetupPage]] |
| `/daten` | [[Seite ImportExportPage]] |
| `/verlauf` | [[Seite HistoryPage]] |
| `/profil` | [[Seite ProfilePage]] |
| `/system` | [[Seite AdminPage]] |
| `/passwort` | [[Seite ChangePasswordPage]] |
| `/zwei-faktor` | [[Seite TwoFactorSetupPage]] |
| `/druck/stundenplan/:kind/:ref` | [[Seite PrintTimetablePage]] |
| `/druck/vertretung` | [[Seite PrintSubstitutionsPage]] |
| `/druck/zugangsbriefe` | [[Seite AccessLettersPage]] |
| (siehe `App.tsx`) | [[Seite SignedOutPage]] |

### Feature-Module

- [[Feature channels]]
- [[Feature classes]]
- [[Feature students]]
- [[Feature teacher]]
- [[Feature anmeldedienste]]
- [[Feature anmelderichtlinien]]
- [[Feature zugangsdaten]]
- [[Feature api-zugaenge]]
- [[Feature formulare]]
- [[Feature makeups]]

Öffentlich ohne Modul: `/passwort-vergessen`, `/passwort-zuruecksetzen`, `/test-postausgang` ([[Feature konto]]).

## Nutzt (Frontend)

- [[Feature anmelderichtlinien]] – `LinkSetupPage`
- [[Feature konto]] – `DevOutboxPage`, `ForgotPasswordPage`, `ResetPasswordPage`
- [[Frontend API-Schicht]] – `types`
- [[Frontend Basis]] – `AuthContext`, `ThemeContext`, `ToastContext`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `Icon`, `Layout`, `ui`
- [[Seite AccessLettersPage]] – `AccessLettersPage`
- [[Seite AdminPage]] – `AdminPage`
- [[Seite AnnouncementsPage]] – `AnnouncementsPage`
- [[Seite ChangePasswordPage]] – `ChangePasswordPage`
- [[Seite DashboardPage]] – `DashboardPage`
- [[Seite DutiesPage]] – `DutiesPage`
- [[Seite ExamsPage]] – `ExamsPage`
- [[Seite HistoryPage]] – `HistoryPage`
- [[Seite ImportExportPage]] – `ImportExportPage`
- [[Seite LicensePage]] – `LicensePage`
- [[Seite LoginPage]] – `LoginPage`
- [[Seite MasterDataPage]] – `MasterDataPage`
- [[Seite MonitorAdminPage]] – `MonitorAdminPage`
- [[Seite MonitorPage]] – `MonitorPage`
- [[Seite PlanningPage]] – `PlanningPage`
- [[Seite PrintSubstitutionsPage]] – `PrintSubstitutionsPage`
- [[Seite ProfilePage]] – `ProfilePage`
- [[Seite RightsPage]] – `RightsPage`
- [[Seite SetupPage]] – `SetupPage`
- [[Seite SignedOutPage]] – `SignedOutPage`
- [[Seite StudentAbsencesPage]] – `StudentAbsencesPage`
- [[Seite SubstitutionsPage]] – `SubstitutionsPage`
- [[Seite TimetablePage]] – `TimetablePage`
- [[Seite TwoFactorSetupPage]] – `TwoFactorSetupPage`
- [[Seite UsersPage]] – `UsersPage`

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
