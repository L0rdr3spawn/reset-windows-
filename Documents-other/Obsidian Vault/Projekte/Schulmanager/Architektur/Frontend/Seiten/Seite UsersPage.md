---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/pages/UsersPage.tsx"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Seite UsersPage

> Frontend · 1 Datei(en) · 698 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Benutzerverwaltung: Konten anlegen/ändern, Startpasswörter, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens, Massenanlage.

**Route:** `/benutzer`

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/pages/UsersPage.tsx` | 698 | Benutzerverwaltung: Konten anlegen/ändern, Startpasswörter, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens, Massenanlage. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| DELETE | `/api-tokens/{…}` | [[Routen users]] · `delete_api_token` (`users.py:493`) |
| GET | `/demo-access` | [[Routen users]] · `demo_access_info` (`users.py:573`) |
| POST | `/demo-access` | [[Routen users]] · `demo_access` (`users.py:593`) |
| DELETE | `/sessions/{…}` | [[Routen users]] · `revoke_session` (`users.py:424`) |
| GET | `/users` | [[Routen users]] · `list_users` (`users.py:126`) |
| POST | `/users` | [[Routen users]] · `create` (`users.py:175`) |
| DELETE | `/users/{…}` | [[Routen users]] · `remove_user` (`users.py:277`) |
| PATCH | `/users/{…}` | [[Routen users]] · `patch_user` (`users.py:215`) |
| POST | `/users/{…}/api-token` | [[Routen users]] · `create_api_token` (`users.py:447`) |
| GET | `/users/{…}/api-tokens` | [[Routen users]] · `list_api_tokens` (`users.py:485`) |
| PUT | `/users/{…}/children` | [[Routen users]] · `put_children` (`users.py:355`) |
| POST | `/users/{…}/reset-password` | [[Routen users]] · `reset_password` (`users.py:294`) |
| DELETE | `/users/{…}/sessions` | [[Routen users]] · `revoke_all_sessions` (`users.py:412`) |
| GET | `/users/{…}/sessions` | [[Routen users]] · `list_sessions` (`users.py:403`) |
| POST | `/users/bulk` | [[Routen users]] · `bulk` (`users.py:316`) |

## Backend-Notizen

[[Routen users]]

## Nutzt (Frontend)

- [[Feature anmeldedienste]] – `slots`
- [[Feature konto]] – `slots`
- [[Feature zugangsdaten]] – `components`, `types`
- [[Frontend API-Schicht]] – `endpoints`, `types`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Abbr`, `Icon`, `Modal`, `PasswordInput`, `SearchSelect` …

## Wird genutzt von

- [[Frontend App und Routing]]
- [[Seite AccessLettersPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
