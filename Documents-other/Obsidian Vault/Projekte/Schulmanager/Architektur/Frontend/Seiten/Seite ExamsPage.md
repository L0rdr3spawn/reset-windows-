---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/ExamsPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite ExamsPage

> Frontend · 1 Datei(en) · 482 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Klassenarbeiten, Klausuren und Tests eintragen, Konflikte/Hinweise anzeigen.

**Route:** `/klausuren`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/ExamsPage.tsx` | 482 | Klassenarbeiten, Klausuren und Tests eintragen, Konflikte/Hinweise anzeigen. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/exams` | [[Routen features_exams]] · `list_exams` (`features_exams.py:172`) |
| POST | `/exams` | [[Routen features_exams]] · `create_exam` (`features_exams.py:218`) |
| DELETE | `/exams/{…}` | [[Routen features_exams]] · `delete_exam` (`features_exams.py:268`) |
| PUT | `/exams/{…}` | [[Routen features_exams]] · `update_exam` (`features_exams.py:241`) |
| POST | `/exams/check` | [[Routen features_exams]] · `check` (`features_exams.py:209`) |

## Backend-Notizen

[[Routen features_exams]]

## Nutzt (Frontend)

- [[Feature makeups]] – `MakeupPanel`
- [[Feature students]] – `ExamHints`, `GradesPage`
- [[Feature teacher]] – `windows`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `Icon`, `Modal`, `SearchSelect`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
