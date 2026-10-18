---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/HistoryPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite HistoryPage

> Frontend · 1 Datei(en) · 166 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Verlauf des Planungsdokuments (Versionen ansehen, wiederherstellen, rückgängig) und Audit-Protokoll.

**Route:** `/verlauf`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/HistoryPage.tsx` | 166 | Verlauf des Planungsdokuments (Versionen ansehen, wiederherstellen, rückgängig) und Audit-Protokoll. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/audit` | [[Routen history]] · `audit_log` (`history.py:62`) |
| GET | `/history` | [[Routen history]] · `history` (`history.py:21`) |
| POST | `/history/{…}/restore` | [[Routen history]] · `restore` (`history.py:41`) |
| POST | `/history/undo` | [[Routen history]] · `undo` (`history.py:52`) |

## Backend-Notizen

[[Routen history]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `Icon`, `VirtualTable`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
