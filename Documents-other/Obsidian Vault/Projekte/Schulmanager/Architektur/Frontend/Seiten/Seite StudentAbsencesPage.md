---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/StudentAbsencesPage.tsx"
stand: 2026-10-12 22:39
generator: schulmanager-regen
---

# Seite StudentAbsencesPage

> Frontend · 1 Datei(en) · 454 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Krankmeldungen und Fehlzeiten von Schüler/innen: Meldung, Status, Entschuldigung, Rechte je Rolle (Eltern, Volljährige, Sekretariat, Klassenleitung).

**Route:** `/krankmeldungen`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/StudentAbsencesPage.tsx` | 454 | Krankmeldungen und Fehlzeiten von Schüler/innen: Meldung, Status, Entschuldigung, Rechte je Rolle (Eltern, Volljährige, Sekretari… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/student-absences` | [[Routen features_student_absences]] · `list_student_absences` (`features_student_absences.py:277`) |
| POST | `/student-absences` | [[Routen features_student_absences]] · `report_student_absence` (`features_student_absences.py:455`) |
| DELETE | `/student-absences/{…}` | [[Routen features_student_absences]] · `delete_student_absence` (`features_student_absences.py:641`) |
| PATCH | `/student-absences/{…}` | [[Routen features_student_absences]] · `patch_student_absence` (`features_student_absences.py:601`) |
| GET | `/student-absences/access` | [[Routen features_student_absences]] · `student_absence_access` (`features_student_absences.py:224`) |

## Backend-Notizen

[[Routen features_student_absences]]

## Nutzt (Frontend)

- [[Feature students]] – `AbsenceStats`, `FamilyAbsences`
- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `Help`, `Icon`, `SearchSelect`, `VirtualTable` …

## Wird genutzt von

- [[Feature students]]
- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
