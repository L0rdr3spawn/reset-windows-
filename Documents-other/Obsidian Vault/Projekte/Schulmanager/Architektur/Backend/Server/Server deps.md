---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/deps.py"
stand: 2026-10-12 22:40
generator: schulmanager-regen
---

# Server deps

> Server-Kern · 1 Datei(en) · 370 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

FastAPI-Abhängigkeiten für Anmeldung und Rechte: `authenticate` (Bearer-Token oder Cookie `sm_session`, CSRF-Header `X-CSRF-Token` bei ändernden Methoden), `current_user`, `optional_user`, `require(recht, …)`. `build_auth_user` erzeugt den unveränderlichen `AuthUser` mit wirksamen Rechten (Standard + Schul-Abweichungen aus [[Server rights]]). Schutzschalter pro Anfrage: `_guard_read_only` (Zuschauer), `_guard_demo` (öffentliche Demo), `_guard_license` (gesperrte Lizenz).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/deps.py` | 370 | FastAPI-Abhängigkeiten für Authentifizierung und Rechte. |

## Wichtige Funktionen und Klassen

- Klasse `AuthUser` (`schulmanager/server/deps.py:51`) – Angemeldeter Benutzer (unveränderliche Sicht für Handler).
  - Methoden: `has`:79, `scope`:82, `class_ids`:88, `public`:92, `totp_setup_required`:104
- Funktion `build_auth_user` (`schulmanager/server/deps.py:114`) – ORM-`User` → `` (inkl. Rechte laut Schul-Einstellungen, Kinder-IDs, Zweige).
- Funktion `user_from_ical_token` (`schulmanager/server/deps.py:160`) – Löst das geheime Token eines iCal-Feeds (`users.ical_token`) auf; `None` wenn ungültig/inaktiv.
- Funktion `client_ip` (`schulmanager/server/deps.py:170`) – Client-IP; hinter einem Reverse Proxy (`SM_TRUST_PROXY=1`) aus `X-Forwarded-For`.
- Funktion `request_is_https` (`schulmanager/server/deps.py:184`) – Kam die Anfrage des Browsers per HTTPS? Hinter einem Proxy (`SM_TRUST_PROXY=1`) zählt `X-Forwarded-Proto`.
- Funktion `cookie_secure_for` (`schulmanager/server/deps.py:193`) – `Secure`-Attribut für Cookies: immer bei `SM_COOKIE_SECURE=1`, sonst automatisch bei HTTPS-Anfragen
- Funktion `same_origin` (`schulmanager/server/deps.py:199`) – Passt der `Origin` einer Anfrage zu diesem Server – auch hinter Proxy mit anderem Port/Host-Header?
- Funktion `authenticate` (`schulmanager/server/deps.py:229`) – Ermittelt den Benutzer aus Bearer-Token oder Sitzungs-Cookie (`None` = anonym).
- Funktion `optional_user` (`schulmanager/server/deps.py:338`) – Dependency: angemeldeter Benutzer oder `None`.
- Funktion `current_user` (`schulmanager/server/deps.py:343`) – Dependency: angemeldeter Benutzer, sonst 401 `not_authenticated`.
- Funktion `require` (`schulmanager/server/deps.py:358`) – Dependency-Fabrik: verlangt alle (bzw. mit `any_of=True` mindestens eines der) Rechte, sonst 403.

## Datenbank-Tabellen

- **Nutzt:** `api_tokens`, `sessions`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server api_scopes]] – `api_scopes` *(nur zur Laufzeit importiert)*
- [[Server betrieb]] – `demo_loader` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`
- [[Server elternzugriff]] – `parent_access` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `identities`, `login_policy`, `security`
- [[Server licensing]] – `licensing` *(nur zur Laufzeit importiert)*
- [[Server permissions]] – `permissions`
- [[Server rights]] – `rights` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen admin]]
- [[Routen auth]]
- [[Routen events]]
- [[Routen features_absence_log]]
- [[Routen features_absence_stats]]
- [[Routen features_announcements]]
- [[Routen features_api_access]]
- [[Routen features_calendar]]
- [[Routen features_channels]]
- [[Routen features_chats]]
- [[Routen features_class_info]]
- [[Routen features_classes]]
- [[Routen features_contact]]
- [[Routen features_data]]
- [[Routen features_exams]]
- [[Routen features_exchange]]
- [[Routen features_forms]]
- [[Routen features_grades]]
- [[Routen features_holiday_import]]
- [[Routen features_letters]]
- [[Routen features_login_policy]]
- [[Routen features_mail]]
- [[Routen features_makeups]]
- [[Routen features_messages]]
- [[Routen features_parent_access]]
- [[Routen features_planning]]
- [[Routen features_register]]
- [[Routen features_sso]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]
- [[Routen features_substitutions]]
- [[Routen features_support]]
- [[Routen features_teacher_profile]]
- [[Routen features_timetable]]
- [[Routen files]]
- [[Routen history]]
- [[Routen license]]
- [[Routen me]]
- [[Routen rights]]
- [[Routen setup]]
- [[Routen system]]
- [[Routen users]]
- [[Server api_scopes]]

## Tests

`tests/test_server_core.py`, `tests/test_server_features.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
