---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/ImportExportPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite ImportExportPage

> Frontend · 1 Datei(en) · 430 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Import/Export: Untis GPU, Schulmanager-Online-Paket, CSV mit Spalten-Mapping und Probelauf, JSON, iCal-Links.

**Route:** `/daten`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/ImportExportPage.tsx` | 430 | Import/Export: Untis GPU, Schulmanager-Online-Paket, CSV mit Spalten-Mapping und Probelauf, JSON, iCal-Links. |

## API-Aufrufe

Diese Einheit ruft selbst keine Endpunkte auf.

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `csv`, `csvFields`, `dates` …
- [[Frontend Komponenten]] – `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
