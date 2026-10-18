---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_contact.py"
stand: 2026-10-12 22:45
generator: schulmanager-regen
---

# Routen features_contact

> API-Routen · 1 Datei(en) · 971 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Kontakt & Wiederherstellung (Erweiterung 4, §11.2): E-Mail/Handy bestätigen, „Passwort vergessen“, Admin-Pflege der Kontaktdaten und Test-Postausgang.

Endpunkte (Präfix `/api/v1`) ------------------------------ Eigenes Konto (angemeldet, Schreiben nur mit Sitzung + CSRF; aktuelles Passwort, falls das Konto eines hat):

* `GET  /me/contact` – E-Mail (+ bestätigt), Nummer maskiert (+ bestätigt), offene Bestätigungen, verfügbare
  Kanäle, `reset_channels` laut Anmelde-Richtlinie.
* `POST /me/contact/email {email, password}` / `POST /me/contact/phone {phone, password}` – Code an die **neue**
  Adresse/Nummer senden (E-Mail zusätzlich mit Bestätigungslink `/profil?kontakt=<token>`). Gültig wird sie erst
  nach `POST /me/contact/verify {kind, code}` bzw. `POST /me/contact/confirm-link {token}`.
* `POST /me/contact/{email|phone}/remove {password}`.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_contact.py` | 971 | Kontakt & Wiederherstellung (Erweiterung 4, §11.2): E-Mail/Handy bestätigen, „Passwort vergessen“, |

## Endpunkte (16)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/me/contact` | `my_contact` (`features_contact.py:488`) | (angemeldet) | [[Feature konto]] |
| POST | `/api/v1/me/contact/email` | `start_email` (`features_contact.py:494`) | (angemeldet) | [[Feature konto]] |
| POST | `/api/v1/me/contact/phone` | `start_phone` (`features_contact.py:518`) | (angemeldet) | [[Feature konto]] |
| POST | `/api/v1/me/contact/verify` | `verify_contact` (`features_contact.py:569`) | (angemeldet) | [[Feature konto]] |
| POST | `/api/v1/me/contact/confirm-link` | `confirm_link` (`features_contact.py:600`) | (angemeldet) | [[Feature konto]] |
| POST | `/api/v1/me/contact/{kind}/remove` | `remove_contact` (`features_contact.py:617`) | (angemeldet) | [[Feature konto]] |
| GET | `/api/v1/users/{user_id}/contact` | `admin_get_contact` (`features_contact.py:647`) | users.manage | [[Feature konto]] |
| PUT | `/api/v1/users/{user_id}/contact` | `admin_put_contact` (`features_contact.py:655`) | users.manage | [[Feature konto]] |
| POST | `/api/v1/users/{user_id}/send-reset` | `admin_send_reset` (`features_contact.py:712`) | users.manage | [[Feature konto]] |
| GET | `/api/v1/auth/capabilities` | `reset_options` (`features_contact.py:887`) | - | [[Feature anmelderichtlinien]], [[Feature konto]] |
| GET | `/api/v1/auth/password-reset/options` | `reset_options` (`features_contact.py:887`) | - | [[Feature anmelderichtlinien]], [[Feature konto]] |
| POST | `/api/v1/auth/password-reset/request` | `reset_request` (`features_contact.py:894`) | - | [[Feature konto]] |
| POST | `/api/v1/auth/password-reset/verify` | `reset_verify` (`features_contact.py:900`) | - | [[Feature konto]] |
| POST | `/api/v1/auth/password-reset/confirm` | `reset_confirm` (`features_contact.py:906`) | - | [[Feature konto]] |
| GET | `/api/v1/dev-outbox` | `dev_outbox` (`features_contact.py:941`) | - | [[Feature konto]] |
| GET | `/api/v1/dev-outbox/{message_id}/attachments/{index}` | `dev_outbox_attachment` (`features_contact.py:949`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `EmailStart` (`schulmanager/server/routes/features_contact.py:91`)
- Klasse `PhoneStart` (`schulmanager/server/routes/features_contact.py:96`)
- Klasse `VerifyBody` (`schulmanager/server/routes/features_contact.py:101`)
- Klasse `TokenBody` (`schulmanager/server/routes/features_contact.py:106`)
- Klasse `PasswordBody` (`schulmanager/server/routes/features_contact.py:110`)
- Klasse `AdminContactBody` (`schulmanager/server/routes/features_contact.py:114`)
- Klasse `SendResetBody` (`schulmanager/server/routes/features_contact.py:121`)
- Klasse `ResetRequestBody` (`schulmanager/server/routes/features_contact.py:125`)
- Klasse `ResetVerifyBody` (`schulmanager/server/routes/features_contact.py:130`)
- Klasse `ResetConfirmBody` (`schulmanager/server/routes/features_contact.py:136`)
- Funktion `cleanup` (`schulmanager/server/routes/features_contact.py:965`) – Abgelaufene Codes/Token/Rate-Limit-Zeilen (eine Stunde Karenz) und alte Test-Nachrichten löschen.

## Datenbank-Tabellen

- **Nutzt:** `auth_codes`, `login_attempts`, `user_contacts`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen auth]] – `auth` *(nur zur Laufzeit importiert)*
- [[Routen users]] – `users` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server crypto]] – `crypto`
- [[Server db]] – `contact`, `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server files]] – `files` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `accounts`, `auth_messages`, `login_policy`, `security`, `sms`
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen me]]
- [[Server betrieb]] – `maintenance`

## Tests

`tests/test_api_access.py`, `tests/test_contact.py`, `tests/test_demo_public.py`, `tests/test_letters.py`, `tests/test_license.py`, `tests/test_login_policy.py`, `tests/test_messages.py`, `tests/test_multi_account.py`, `tests/test_rights.py`, `tests/test_self_reset.py`, `tests/test_server_core.py`, `tests/test_server_core_store.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
