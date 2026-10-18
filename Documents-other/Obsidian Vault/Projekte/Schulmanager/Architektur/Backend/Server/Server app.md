---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/__init__.py, schulmanager/server/app.py, schulmanager/server/routes/__init__.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Server app

> Server-Kern · 3 Datei(en) · 249 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Erzeugt die FastAPI-Anwendung (`create_app`): Middleware ([[Server middleware und metrics]]), Fehlerbehandlung, **automatisches Einbinden aller `routes/*.py`** (`router` unter `/api/v1`, `public_router` ohne Präfix), Infrastruktur-Routen (`/healthz`, `/metrics`), SPA-Auslieferung des gebauten Frontends (`frontend/dist`) und der Lifespan, der [[Server runtime]] startet. Kernrouter (`auth`, `users`, `history`, `admin`, `me`, `events`, `system`, `oidc`) werden zuerst geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/__init__.py` | 2 | Server des Schulmanagers (FastAPI). |
| `schulmanager/server/app.py` | 244 | FastAPI-Anwendung des Schulmanagers. |
| `schulmanager/server/routes/__init__.py` | 3 | API-Router. Jedes Modul mit Attribut `router` wird automatisch unter `/api/v1` eingebunden, |

## Endpunkte (2)

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/metrics` | `prometheus` (`app.py:110`) | - | – |
| GET | `/{full_path:path}` | `spa` (`app.py:158`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Datenbank-Tabellen

- **Nutzt:** `school_versions` → [[Datenmodell#Planungsdokument und Protokoll]]
- **Nutzt:** `sessions`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `security`
- [[Server middleware und metrics]] – `logging_setup`, `metrics`, `middleware`
- [[Server runtime]] – `runtime`
- [[Server store]] – `store`

## Wird genutzt von

- [[Server betrieb]] – `cli`

## Tests

`tests/test_absence_log.py`, `tests/test_absence_stats_adult.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_chat_split.py`, `tests/test_contact.py`, `tests/test_files_crypto.py`, `tests/test_forms.py`, `tests/test_holiday_import.py`, `tests/test_letters.py`, `tests/test_license.py`, `tests/test_login_policy.py` …

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
