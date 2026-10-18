---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/makeups/"
stand: 2026-10-12 22:34
generator: schulmanager-regen
---

# Feature makeups

> Frontend · 7 Datei(en) · 572 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Feature-Modul „Nachschreibtermine“ für die Registry (`features/registry.ts`). * `/nachschreiben` – Lehrkräfte (Klausur), Klassenleitung, Sekretariat, Leitung: verpasste Klausuren/Tests, Termin festlegen, Attest-Status. * Startseiten-Kachel für Lehrkräfte und Familien (nur sichtbar, wenn etwas ansteht).

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/nachschreiben` | `MakeupsPage` | anyOf: ['exam.edit', 'student_absence.read'] | Nachschreibtermine |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/makeups/MakeupPanel.tsx` | 316 | Nachschreibtermine als Liste je Klausur – für die Seite `/nachschreiben`, die Startseite (Lehrkraft, Familie) und die Klausurseit… |
| `frontend/src/features/makeups/MakeupWidget.tsx` | 7 |  |
| `frontend/src/features/makeups/MakeupsPage.tsx` | 16 |  |
| `frontend/src/features/makeups/api.ts` | 104 | Nachschreibtermine (`/exam-makeups`, siehe schulmanager/server/routes/features_makeups.py). |
| `frontend/src/features/makeups/badge.tsx` | 25 | Menü-Badge der Nachschreibtermine: Lehrkräfte = Termine, die noch festzulegen sind; Klassenleitung/Sekretariat und Familien = feh… |
| `frontend/src/features/makeups/logic.ts` | 69 | Reine Hilfsfunktionen der Nachschreibtermine (ohne React, getestet in makeups.test.ts). |
| `frontend/src/features/makeups/module.tsx` | 35 | Feature-Modul „Nachschreibtermine“ für die Registry (`features/registry.ts`). * `/nachschreiben` – Lehrkräfte (Klausur), Klassenl… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/exam-makeups` | [[Routen features_makeups]] · `list_makeups` (`features_makeups.py:147`) |
| PATCH | `/exam-makeups/{…}` | [[Routen features_makeups]] · `patch_makeup` (`features_makeups.py:291`) |
| POST | `/exam-makeups/dates` | [[Routen features_makeups]] · `create_date` (`features_makeups.py:224`) |
| DELETE | `/exam-makeups/dates/{…}` | [[Routen features_makeups]] · `delete_date` (`features_makeups.py:268`) |
| PUT | `/exam-makeups/dates/{…}` | [[Routen features_makeups]] · `update_date` (`features_makeups.py:245`) |
| GET | `/exam-makeups/summary` | [[Routen features_makeups]] · `summary` (`features_makeups.py:162`) |

## Backend-Notizen

[[Routen features_makeups]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `Icon`, `Modal`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Feature classes]]
- [[Seite ExamsPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
