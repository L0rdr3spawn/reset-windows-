---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/RightsPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite RightsPage

> Frontend · 1 Datei(en) · 403 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Rollen & Rechte: Matrix Recht × Rolle, Schulzweige der Abteilungsleitung und Zuordnungen; feste Mindestregeln sind gesperrt.

**Route:** `/rechte`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/RightsPage.tsx` | 403 | `/rechte` – Rollen & Rechte: Matrix (Recht × Rolle) gruppiert nach Bereichen, Zweige der Abteilungsleitung und Zuordnungen (Zweig… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/rights` | [[Routen rights]] · `get_rights` (`rights.py:55`) |
| GET | `/rights/assignments` | [[Routen rights]] · `list_assignments` (`rights.py:162`) |
| PUT | `/rights/assignments/{…}` | [[Routen rights]] · `put_assignment` (`rights.py:181`) |
| GET | `/rights/branches` | [[Routen rights]] · `list_branches` (`rights.py:102`) |
| POST | `/rights/branches` | [[Routen rights]] · `create_branch` (`rights.py:112`) |
| DELETE | `/rights/branches/{…}` | [[Routen rights]] · `delete_branch` (`rights.py:146`) |
| PUT | `/rights/branches/{…}` | [[Routen rights]] · `update_branch` (`rights.py:128`) |
| POST | `/rights/roles/{…}/reset` | [[Routen rights]] · `reset_role` (`rights.py:77`) |
| PUT | `/rights/roles/{…}` | [[Routen rights]] · `put_role` (`rights.py:61`) |

## Backend-Notizen

[[Routen rights]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `misc`, `permissions`, `useApi` …
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `SearchSelect`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
