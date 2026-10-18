---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/DashboardPage.tsx"
stand: 2026-10-12 22:51
generator: schulmanager-regen
---

# Seite DashboardPage

> Frontend · 1 Datei(en) · 461 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Startseite je Rolle: heutiger Plan und Vertretungen („für Sie“), Krankmeldung der Lehrkraft, Karten für Schüler/Eltern, Klassenbuch-Einstieg („jetzt laufende Stunde“).

**Route:** `/` (HomeRoute)

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/DashboardPage.tsx` | 461 | Startseite je Rolle: heutiger Plan und Vertretungen („für Sie“), Krankmeldung der Lehrkraft, Karten für Schüler/Eltern, Klassenbu… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/planning/report` | [[Routen features_planning]] · `report` (`features_planning.py:119`) |
| POST | `/absences/report-self` | [[Routen features_substitutions]] · `report_self` (`features_substitutions.py:364`) |
| GET | `/me/today` | [[Routen features_substitutions]] · `me_today` (`features_substitutions.py:539`) |
| GET | `/substitutions` | [[Routen features_substitutions]] · `substitutions` (`features_substitutions.py:151`) |

## Backend-Notizen

[[Routen features_planning]], [[Routen features_substitutions]]

## Nutzt (Frontend)

- [[Feature classes]] – `CalendarWeek`, `RegisterPage`
- [[Feature students]] – `ExamHints`, `FamilyHome`
- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `Abbr`, `EntryTable`, `Help`, `Icon`, `Layout` …
- [[Seite PlanningPage]] – `ReportTiles`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
