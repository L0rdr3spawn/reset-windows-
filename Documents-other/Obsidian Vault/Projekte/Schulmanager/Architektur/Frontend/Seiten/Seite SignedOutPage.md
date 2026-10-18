---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/SignedOutPage.tsx"
stand: 2026-10-12 22:40
generator: schulmanager-regen
---

# Seite SignedOutPage

> Frontend · 1 Datei(en) · 107 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Seite nach dem Abmelden: „Sie sind abgemeldet.“ + die in diesem Browser noch angemeldeten weiteren Konten (Klick = weiter als …, × = dieses Konto auch abmelden) + „Mit anderem Konto anmelden“. Ohne weitere Konten geht es direkt zur Anmeldeseite. Die Seite zeigt nie Daten des gerade abgemeldeten Kontos: die Liste kommt vom Server und enthält nur Konten mit gültiger Sitzung (Name, Rolle).

**Route:** (siehe `App.tsx`)

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/SignedOutPage.tsx` | 107 | Seite nach dem Abmelden: „Sie sind abgemeldet.“ + die in diesem Browser noch angemeldeten weiteren Konten (Klick = weiter als …,… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/auth/accounts` | [[Routen auth]] · `accounts` (`auth.py:292`) |
| POST | `/auth/accounts/{…}/logout` | [[Routen auth]] · `logout_other` (`auth.py:331`) |

## Backend-Notizen

[[Routen auth]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `endpoints`
- [[Frontend Basis]] – `AuthContext`, `ThemeContext`, `misc`, `permissions`, `useApi`
- [[Frontend Komponenten]] – `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
