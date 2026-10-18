---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/konto/"
stand: 2026-10-12 22:31
generator: schulmanager-regen
---

# Feature konto

> Frontend · 11 Datei(en) · 1687 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Öffentliche Konto-Seiten (Passwort vergessen/zurücksetzen, Entwicklungs-Postausgang) und Kontakt-Bausteine (E-Mail/Handy bestätigen); direkt in `App.tsx` verdrahtet, nicht über die Registry.

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/konto/ContactSection.tsx` | 330 | Profil: Abschnitt „Kontakt & Wiederherstellung“ (§11.2). E-Mail/Handy anzeigen, ändern (Code an die neue Adresse/Nummer, aktuelle… |
| `frontend/src/features/konto/DevOutboxPage.tsx` | 156 | Öffentliche Seite `/test-postausgang` (§11.2, nur mit `SM_DEV_OUTBOX`): zeigt die E-Mails und SMS, die der Schulmanager verschick… |
| `frontend/src/features/konto/ForgotPasswordPage.tsx` | 183 | Öffentliche Seite „Passwort vergessen“ (§11.2): Kennung + Kanal → neutrale Bestätigung → Code → neues Passwort. Die Antwort des S… |
| `frontend/src/features/konto/ResetPasswordPage.tsx` | 118 | Öffentliche Seite `/passwort-zuruecksetzen?token=…` (Link aus der E-Mail, §11.2): Link prüfen → neues Passwort → `/login?reset=ok… |
| `frontend/src/features/konto/UserContactPanel.tsx` | 179 | Benutzerverwaltung, Reiter „Kontakt“ im Konto-Dialog (§11.2, Admin/Sekretariat): E-Mail/Handynummer setzen, als bestätigt markier… |
| `frontend/src/features/konto/api.ts` | 52 | Endpunkte des Features „konto“ (§11.2). Die öffentlichen Aufrufe („Passwort vergessen“, Test-Postausgang) lösen bei Fehlern keine… |
| `frontend/src/features/konto/components.tsx` | 139 | Gemeinsame Formularbausteine des Features „konto“ (§11.2). Passwort-Manager (Chrome/Google, Safari/iCloud-Schlüsselbund, Edge/Mic… |
| `frontend/src/features/konto/konto.css` | 192 | Stylesheet |
| `frontend/src/features/konto/logic.ts` | 168 | Reine Logik des Features „konto“ (§11.2) – ohne React, mit vitest getestet (logic.test.ts). Die verbindliche Prüfung macht immer… |
| `frontend/src/features/konto/slots.tsx` | 41 | Einhängepunkte des Features „konto“ (§11.2) in geteilten Seiten. LoginPage: <ForgotPasswordLink />, ProfilePage: <ContactSection… |
| `frontend/src/features/konto/types.ts` | 129 | Typen des Features „konto“ (§11.2): Kontakt & Wiederherstellung, „Passwort vergessen“, Test-Postausgang. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/auth/password-reset/confirm` | [[Routen features_contact]] · `reset_confirm` (`features_contact.py:906`) |
| GET | `/auth/password-reset/options` | [[Routen features_contact]] · `reset_options` (`features_contact.py:887`) |
| POST | `/auth/password-reset/request` | [[Routen features_contact]] · `reset_request` (`features_contact.py:894`) |
| POST | `/auth/password-reset/verify` | [[Routen features_contact]] · `reset_verify` (`features_contact.py:900`) |
| GET | `/dev-outbox` | [[Routen features_contact]] · `dev_outbox` (`features_contact.py:941`) |
| GET | `/me/contact` | [[Routen features_contact]] · `my_contact` (`features_contact.py:488`) |
| POST | `/me/contact/{…}/remove` | [[Routen features_contact]] · `remove_contact` (`features_contact.py:617`) |
| POST | `/me/contact/confirm-link` | [[Routen features_contact]] · `confirm_link` (`features_contact.py:600`) |
| POST | `/me/contact/email` | [[Routen features_contact]] · `start_email` (`features_contact.py:494`) |
| POST | `/me/contact/phone` | [[Routen features_contact]] · `start_phone` (`features_contact.py:518`) |
| POST | `/me/contact/verify` | [[Routen features_contact]] · `verify_contact` (`features_contact.py:569`) |
| GET | `/users/{…}/contact` | [[Routen features_contact]] · `admin_get_contact` (`features_contact.py:647`) |
| PUT | `/users/{…}/contact` | [[Routen features_contact]] · `admin_put_contact` (`features_contact.py:655`) |
| POST | `/users/{…}/send-reset` | [[Routen features_contact]] · `admin_send_reset` (`features_contact.py:712`) |

## Backend-Notizen

[[Routen features_contact]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `misc`, `useApi`
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `PasswordInput`, `ui`

## Wird genutzt von

- [[Feature anmelderichtlinien]]
- [[Frontend App und Routing]]
- [[Seite LoginPage]]
- [[Seite ProfilePage]]
- [[Seite UsersPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
