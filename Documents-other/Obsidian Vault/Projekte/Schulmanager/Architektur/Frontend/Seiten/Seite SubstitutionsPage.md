---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/SubstitutionsPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite SubstitutionsPage

> Frontend · 1 Datei(en) · 698 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Vertretungsplan eines Tages: Einträge nach Art, Abwesenheiten erfassen (Lehrkraft, Klasse, Raum, Einzelstunde), Kandidaten-Vorschläge, manuelle Entscheidungen (Overrides) und Statistik.

**Route:** `/vertretung`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/SubstitutionsPage.tsx` | 698 | Vertretungsplan eines Tages: Einträge nach Art, Abwesenheiten erfassen (Lehrkraft, Klasse, Raum, Einzelstunde), Kandidaten-Vorsch… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/absences` | [[Routen features_substitutions]] · `list_absences` (`features_substitutions.py:250`) |
| POST | `/absences` | [[Routen features_substitutions]] · `create_absence` (`features_substitutions.py:294`) |
| DELETE | `/absences/{…}` | [[Routen features_substitutions]] · `delete_absence` (`features_substitutions.py:334`) |
| PUT | `/absences/{…}` | [[Routen features_substitutions]] · `update_absence` (`features_substitutions.py:311`) |
| GET | `/overrides` | [[Routen features_substitutions]] · `list_overrides` (`features_substitutions.py:412`) |
| POST | `/overrides` | [[Routen features_substitutions]] · `create_override` (`features_substitutions.py:428`) |
| DELETE | `/overrides/{…}` | [[Routen features_substitutions]] · `delete_override` (`features_substitutions.py:471`) |
| GET | `/substitutions` | [[Routen features_substitutions]] · `substitutions` (`features_substitutions.py:151`) |
| GET | `/substitutions/candidates` | [[Routen features_substitutions]] · `candidates` (`features_substitutions.py:187`) |
| GET | `/substitutions/stats` | [[Routen features_substitutions]] · `stats` (`features_substitutions.py:204`) |

## Backend-Notizen

[[Routen features_substitutions]]

## Nutzt (Frontend)

- [[Feature teacher]] – `hooks`, `scope`, `windows`
- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `AbsentTeachersCard`, `DateNav`, `EntryTable`, `Icon`, `Modal` …

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
