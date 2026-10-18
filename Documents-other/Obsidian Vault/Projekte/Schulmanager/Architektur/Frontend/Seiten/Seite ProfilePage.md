---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/ProfilePage.tsx"
stand: 2026-10-12 22:45
generator: schulmanager-regen
---

# Seite ProfilePage

> Frontend · 1 Datei(en) · 331 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Eigenes Profil und Sicherheit: Passwort, Zwei-Faktor (TOTP), persönlicher iCal-Link, Datenexport.

**Route:** `/profil`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/ProfilePage.tsx` | 331 | Eigenes Profil und Sicherheit: Passwort, Zwei-Faktor (TOTP), persönlicher iCal-Link, Datenexport. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/auth/2fa/disable` | [[Routen auth]] · `totp_disable` (`auth.py:435`) |
| POST | `/auth/2fa/enable` | [[Routen auth]] · `totp_enable` (`auth.py:417`) |
| POST | `/auth/2fa/setup{…}` | [[Routen auth]] · `totp_setup` (`auth.py:401`) |
| GET | `/me/ical-url` | [[Routen me]] · `get_ical_url` (`me.py:29`) |
| POST | `/me/ical-url` | [[Routen me]] · `reset_ical_url` (`me.py:40`) |
| GET | `/rights/me` | [[Routen rights]] · `my_role` (`rights.py:210`) |
| DELETE | `/sessions/{…}` | [[Routen users]] · `revoke_session` (`users.py:424`) |
| DELETE | `/users/{…}/sessions` | [[Routen users]] · `revoke_all_sessions` (`users.py:412`) |
| GET | `/users/{…}/sessions` | [[Routen users]] · `list_sessions` (`users.py:403`) |

## Backend-Notizen

[[Routen auth]], [[Routen me]], [[Routen rights]], [[Routen users]]

## Nutzt (Frontend)

- [[Feature anmeldedienste]] – `slots`
- [[Feature elternzugriff]] – `ParentAccessSection`
- [[Feature konto]] – `slots`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ThemeContext`, `ToastContext`, `dates`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `Help`, `HelpTip`, `Icon`, `PasswordInput` …
- [[Seite ChangePasswordPage]] – `ChangePasswordPage`

## Wird genutzt von

- [[Frontend App und Routing]]
- [[Seite TwoFactorSetupPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
