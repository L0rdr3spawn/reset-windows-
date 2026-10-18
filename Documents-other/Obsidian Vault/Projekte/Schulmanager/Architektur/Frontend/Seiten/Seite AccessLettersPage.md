---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/AccessLettersPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite AccessLettersPage

> Frontend · 1 Datei(en) · 107 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Druckansicht der Zugangsbriefe (Startpasswörter) im Browser.

**Route:** `/druck/zugangsbriefe`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/AccessLettersPage.tsx` | 107 | Druckansicht der Zugangsbriefe (Startpasswörter) im Browser. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/users/letters.pdf` | [[Routen users]] · `letters_pdf` (`users.py:521`) |

## Backend-Notizen

[[Routen users]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `ToastContext`, `dates`, `misc`, `permissions`, `useCollection`
- [[Frontend Komponenten]] – `Icon`, `ui`
- [[Seite UsersPage]] – `UsersPage`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
