---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/config.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Server config

> Server-Kern · 1 Datei(en) · 363 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Konfiguration aus Umgebungsvariablen `SM_*` (`config`-Objekt, `reload()`, `validate()`): Umgebung, Datenbank-URL, Geheimnisse, Cookie/Proxy-Einstellungen, SMTP, OIDC, Auto-Planer, Lizenz, Verschlüsselungsschlüssel, Upload-Limits. Werte gehören in `.env`/Compose, nie in den Code (siehe [[Betrieb und Deploy]]).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/config.py` | 363 | Konfiguration aus Umgebungsvariablen (`SM_*`). |

## Wichtige Funktionen und Klassen

- Klasse `ConfigError` (`schulmanager/server/config.py:49`) – Ungültige oder unsichere Konfiguration – der Server startet nicht.
- Klasse `Config` (`schulmanager/server/config.py:53`) – Alle Einstellungen des Servers. Felder siehe ``.
  - Methoden: `reload`:60, `is_production`:197, `is_development`:201, `db_kind`:205, `oidc_enabled`:211, `smtp_enabled`:215, `secret_key`:219, `validate`:245, `public_dict`:320
- Funktion `mask_url` (`schulmanager/server/config.py:352`) – Entfernt ein Passwort aus einer Datenbank-URL.

## Hängt ab von

- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen admin]]
- [[Routen api_discovery]]
- [[Routen auth]]
- [[Routen events]]
- [[Routen features_api_access]]
- [[Routen features_contact]]
- [[Routen features_holiday_import]]
- [[Routen features_letters]]
- [[Routen features_messages]]
- [[Routen features_planning]]
- [[Routen features_sso]]
- [[Routen me]]
- [[Routen system]]
- [[Routen users]]
- [[Server app]] – `app`
- [[Server autoplan]]
- [[Server betrieb]] – `backups`, `bootstrap`, `cli`, `demo_loader`, `maintenance`
- [[Server crypto]]
- [[Server db]] – `db`, `env`, `migrate`
- [[Server deps]]
- [[Server files]]
- [[Server holiday_import]]
- [[Server konten und anmeldung]] – `accounts`, `auth_messages`, `identities`, `security`, `sms`, `sso_providers`
- [[Server letters und pdf]] – `letters`
- [[Server licensing]]
- [[Server mailbridge]]
- [[Server middleware und metrics]] – `logging_setup`, `middleware`
- [[Server notify]]
- [[Server runtime]]
- [[Server store]]

## Tests

`tests/test_absence_log.py`, `tests/test_api_access.py`, `tests/test_chat_split.py`, `tests/test_contact.py`, `tests/test_demo_public.py`, `tests/test_files_crypto.py`, `tests/test_holiday_import.py`, `tests/test_lead_integration.py`, `tests/test_license.py`, `tests/test_login_policy.py`, `tests/test_messages.py`, `tests/test_migrations.py` …

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
