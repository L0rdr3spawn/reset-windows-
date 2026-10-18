---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/PrintSubstitutionsPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite PrintSubstitutionsPage

> Frontend · 1 Datei(en) · 73 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Druckansicht des Vertretungsplans.

**Route:** `/druck/vertretung`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/PrintSubstitutionsPage.tsx` | 73 | Druckansicht des Vertretungsplans. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/substitutions` | [[Routen features_substitutions]] · `substitutions` (`features_substitutions.py:151`) |

## Backend-Notizen

[[Routen features_substitutions]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`
- [[Frontend Basis]] – `dates`, `misc`, `substitution`, `useApi`, `useCollection` …
- [[Frontend Komponenten]] – `EntryTable`, `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
