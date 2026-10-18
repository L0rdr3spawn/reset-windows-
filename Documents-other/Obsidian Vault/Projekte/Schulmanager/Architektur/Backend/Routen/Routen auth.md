---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/auth.py"
stand: 2026-10-12 22:45
generator: schulmanager-regen
---

# Routen auth

> API-Routen · 1 Datei(en) · 449 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Anmeldung: Login (mit TOTP), Logout, Kontowechsel (mehrere Konten pro Browser über das Cookie `sm_sessions`), Passwortwechsel, Zwei-Faktor, öffentliche Login-Konfiguration.

Aus dem Modulkopf:

Anmeldung, Sitzung, Passwort, Zwei-Faktor-Authentifizierung.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/auth.py` | 449 | Anmeldung, Sitzung, Passwort, Zwei-Faktor-Authentifizierung. |

## Endpunkte (11)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | `login` (`auth.py:168`) | - | [[Frontend Basis]] |
| POST | `/api/v1/auth/logout` | `logout` (`auth.py:232`) | - | [[Frontend Basis]] |
| GET | `/api/v1/auth/accounts` | `accounts` (`auth.py:292`) | - | [[Frontend Komponenten]], [[Seite SignedOutPage]] |
| POST | `/api/v1/auth/accounts/switch` | `switch_account` (`auth.py:310`) | - | [[Frontend Basis]] |
| POST | `/api/v1/auth/accounts/{user_id}/logout` | `logout_other` (`auth.py:331`) | - | [[Seite SignedOutPage]] |
| GET | `/api/v1/auth/me` | `me` (`auth.py:349`) | (angemeldet) | [[Frontend Basis]] |
| GET | `/api/v1/auth/config` | `auth_config` (`auth.py:355`) | - | – |
| POST | `/api/v1/auth/password` | `change_password` (`auth.py:376`) | (angemeldet) | [[Seite ChangePasswordPage]] |
| POST | `/api/v1/auth/2fa/setup` | `totp_setup` (`auth.py:401`) | (angemeldet) | [[Seite ProfilePage]] |
| POST | `/api/v1/auth/2fa/enable` | `totp_enable` (`auth.py:417`) | (angemeldet) | [[Seite ProfilePage]] |
| POST | `/api/v1/auth/2fa/disable` | `totp_disable` (`auth.py:435`) | (angemeldet) | [[Seite ProfilePage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `LoginBody` (`schulmanager/server/routes/auth.py:43`)
- Klasse `PasswordBody` (`schulmanager/server/routes/auth.py:49`)
- Klasse `CodeBody` (`schulmanager/server/routes/auth.py:54`)
- Klasse `PasswordOnlyBody` (`schulmanager/server/routes/auth.py:58`)
- Funktion `user_payload` (`schulmanager/server/routes/auth.py:99`) – `AuthUser.public()` + Namen/Klassen der verknüpften Schüler (`students`).
- Funktion `set_session_cookie` (`schulmanager/server/routes/auth.py:117`)
- Funktion `login_user` (`schulmanager/server/routes/auth.py:122`) – Erzeugt Sitzung + Cookie für einen bereits geprüften Benutzer (auch für SSO).
- Funktion `current_sessions` (`schulmanager/server/routes/auth.py:179`) – Bisher angemeldete Sitzungen dieses Browsers (aktive zuerst) – für den Kontowechsel über SSO (`add=true`).
- Funktion `keep_sessions` (`schulmanager/server/routes/auth.py:185`) – Nach `add=true`: gültige bisherige Sitzungen (außer der des neuen Kontos) als weitere Konten behalten.
- Klasse `SwitchBody` (`schulmanager/server/routes/auth.py:287`)

## Datenbank-Tabellen

- **Nutzt:** `login_attempts`, `sessions`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server konten und anmeldung]] – `accounts`, `login_policy`, `security`
- [[Server licensing]] – `licensing` *(nur zur Laufzeit importiert)*
- [[Server middleware und metrics]] – `metrics`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_contact]]
- [[Routen features_sso]]

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_channels.py`, `tests/test_chat_split.py`, `tests/test_chats.py`, `tests/test_contact.py`, `tests/test_demo_public.py`, `tests/test_lead_integration.py`, `tests/test_license.py`, `tests/test_login_policy.py`, `tests/test_mail.py`, `tests/test_makeups.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
