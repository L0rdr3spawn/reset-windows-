---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/MonitorPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite MonitorPage

> Frontend · 1 Datei(en) · 271 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Vollbild-Anzeige des Vertretungsplans für Monitore im Schulhaus (Rolle `monitor`, Standort-Filter).

**Route:** `/monitor/:site?`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/MonitorPage.tsx` | 271 | Vollbild-Anzeige des Vertretungsplans für Monitore im Schulhaus (Rolle monitor, Standort-Filter). |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/monitor` | [[Routen features_substitutions]] · `monitor` (`features_substitutions.py:628`) |

## Backend-Notizen

[[Routen features_substitutions]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `dates`, `misc`, `substitution`, `useApi` …
- [[Frontend Komponenten]] – `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
