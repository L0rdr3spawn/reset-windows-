---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/AdminPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite AdminPage

> Frontend · 1 Datei(en) · 292 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Systemseite der Administration: Version/Status, Sicherungen, Demo-Daten laden, Wartung.

**Route:** `/system`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/AdminPage.tsx` | 292 | Systemseite der Administration: Version/Status, Sicherungen, Demo-Daten laden, Wartung. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/admin/backups` | [[Routen admin]] · `backups` (`admin.py:65`) |
| POST | `/admin/backups` | [[Routen admin]] · `make_backup` (`admin.py:70`) |
| DELETE | `/admin/backups/{…}` | [[Routen admin]] · `remove_backup` (`admin.py:85`) |
| POST | `/admin/demo` | [[Routen admin]] · `load_demo_school` (`admin.py:95`) |

## Backend-Notizen

[[Routen admin]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `ToastContext`, `dates`, `format`, `misc`, `useApi` …
- [[Frontend Komponenten]] – `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
