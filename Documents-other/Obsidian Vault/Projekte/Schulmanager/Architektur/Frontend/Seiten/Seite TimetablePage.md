---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/TimetablePage.tsx"
stand: 2026-10-12 22:51
generator: schulmanager-regen
---

# Seite TimetablePage

> Frontend · 1 Datei(en) · 536 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Stundenplan-Ansichten für Klasse, Lehrkraft, Raum und Schüler/in mit Wochenwahl; Planende verschieben Stunden per Drag & Drop (Konfliktprüfung, `move_options`) und fixieren sie.

**Route:** `/stundenplan`, `/stundenplan/:kind`, `/stundenplan/:kind/:ref`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/TimetablePage.tsx` | 536 | Stundenplan-Ansichten für Klasse, Lehrkraft, Raum und Schüler/in mit Wochenwahl; Planende verschieben Stunden per Drag & Drop (Ko… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/timetable/{…}/{…}` | [[Routen features_timetable]] · `view` (`features_timetable.py:189`) |
| POST | `/timetable/lessons/{…}/lock` | [[Routen features_timetable]] · `lock` (`features_timetable.py:152`) |
| POST | `/timetable/lessons/{…}/move` | [[Routen features_timetable]] · `move` (`features_timetable.py:123`) |
| GET | `/timetable/lessons/{…}/options` | [[Routen features_timetable]] · `lesson_options` (`features_timetable.py:109`) |

## Backend-Notizen

[[Routen features_timetable]]

## Nutzt (Frontend)

- [[Feature classes]] – `CalendarWeek`
- [[Feature teacher]] – `hooks`, `scope`, `windows`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `grid` …
- [[Frontend Komponenten]] – `Abbr`, `Icon`, `SearchSelect`, `TimetableGrid`, `WeekNav` …

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
