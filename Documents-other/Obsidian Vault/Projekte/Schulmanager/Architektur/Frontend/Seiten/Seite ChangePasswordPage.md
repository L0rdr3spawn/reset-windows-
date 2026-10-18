---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/ChangePasswordPage.tsx"
stand: 2026-10-12 22:45
generator: schulmanager-regen
---

# Seite ChangePasswordPage

> Frontend · 1 Datei(en) · 106 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Pflichtseite bei Startpasswort bzw. Passwortwechsel-Zwang.

**Route:** `/passwort`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/ChangePasswordPage.tsx` | 106 | Pflichtseite bei Startpasswort bzw. Passwortwechsel-Zwang. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/auth/password` | [[Routen auth]] · `change_password` (`auth.py:376`) |

## Backend-Notizen

[[Routen auth]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `endpoints`
- [[Frontend Basis]] – `AuthContext`, `misc`, `permissions`
- [[Frontend Komponenten]] – `PasswordInput`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]
- [[Seite ProfilePage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
