---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/zugangsdaten/"
stand: 2026-10-12 22:26
generator: schulmanager-regen
---

# Feature zugangsdaten

> Frontend · 7 Datei(en) · 849 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Stapel-Seite `/zugangsdaten/:id`: Zugangsbriefe als PDF/ZIP laden oder per E-Mail versenden; ohne Menüeintrag.

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/zugangsdaten/:id` | `BatchPage` | anyOf: ['users.manage', 'passwords.reset'] | Zugangsdaten |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/zugangsdaten/BatchPage.tsx` | 280 | Stapel-Seite `/zugangsdaten/:id` (§11.3): Ablauf-Countdown, Einträge, Downloads (Sammel-PDF, ZIP, einzeln) und Versand per E-Mail… |
| `frontend/src/features/zugangsdaten/api.ts` | 49 | Endpunkte der Zugangsbriefe (§11.3). Downloads laufen über normale Links (Cookie-Anmeldung, GET ohne CSRF). |
| `frontend/src/features/zugangsdaten/components.tsx` | 223 | Wiederverwendbare Bausteine der Zugangsbriefe (§11.3) – auch für Benutzerverwaltung und Klassen-Seite: * `LetterBatchActions` – K… |
| `frontend/src/features/zugangsdaten/logic.ts` | 77 | Reine Logik der Zugangsdaten-Seite (§11.3): Ablauf-Countdown, Versand-Vorschau, Texte. |
| `frontend/src/features/zugangsdaten/module.tsx` | 16 | Feature-Modul „Zugangsdaten“ (§11.3): Stapel-Seite `/zugangsdaten/:id` mit Downloads (PDF/ZIP) und E-Mail-Versand. Ohne Menüeintr… |
| `frontend/src/features/zugangsdaten/types.ts` | 139 | Typen der Zugangsbriefe (§11.3) – Spiegel von `schulmanager/server/routes/features_letters.py`. Passwörter kommen nie über diese… |
| `frontend/src/features/zugangsdaten/zugangsdaten.css` | 65 | Stylesheet |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/classes/{…}/accounts` | [[Routen features_letters]] · `class_accounts` (`features_letters.py:347`) |
| POST | `/letters/batches` | [[Routen features_letters]] · `create_batch` (`features_letters.py:103`) |
| GET | `/letters/batches/{…}` | [[Routen features_letters]] · `get_batch` (`features_letters.py:175`) |
| POST | `/letters/batches/{…}/send` | [[Routen features_letters]] · `send_batch` (`features_letters.py:255`) |
| GET | `/users/{…}/password` | [[Routen features_letters]] · `password_info` (`features_letters.py:277`) |
| POST | `/users/{…}/password` | [[Routen features_letters]] · `set_password` (`features_letters.py:289`) |

## Backend-Notizen

[[Routen features_letters]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `dates`, `misc`, `permissions`, `useApi`
- [[Frontend Komponenten]] – `Icon`, `Modal`, `PasswordInput`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Feature classes]]
- [[Feature students]]
- [[Seite UsersPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
