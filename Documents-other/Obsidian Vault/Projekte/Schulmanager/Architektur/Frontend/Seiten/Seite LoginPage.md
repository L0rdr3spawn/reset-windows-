---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/LoginPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite LoginPage

> Frontend · 1 Datei(en) · 171 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Anmeldung mit Benutzername und Passwort, 2FA-Code bei aktivierter Zwei-Faktor-Anmeldung, Anmeldedienste (SSO), Kontowechsel („weiteres Konto anmelden“) und – in der öffentlichen Demo – Rollen-Schaltflächen.

**Route:** `/login`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/LoginPage.tsx` | 171 | Anmeldung mit Benutzername und Passwort, 2FA-Code bei aktivierter Zwei-Faktor-Anmeldung, Anmeldedienste (SSO), Kontowechsel („wei… |

## API-Aufrufe

Diese Einheit ruft selbst keine Endpunkte auf.

## Nutzt (Frontend)

- [[Feature anmeldedienste]] – `slots`
- [[Feature konto]] – `slots`
- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `AuthContext`, `ThemeContext`, `misc`, `permissions`
- [[Frontend Komponenten]] – `Icon`, `PasswordInput`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
