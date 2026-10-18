---
tags: [schulmanager, architektur, lizenzserver]
quelle: "lizenzserver/ (5 Dateien)"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Lizenzserver

> Lizenzserver · 5 Datei(en) · 349 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Eigenständige FastAPI-App des Herstellers (`lizenzserver/`): stellt Ed25519-signierte Lizenzen aus (`issue_license`), widerruft sie und beantwortet `POST /api/v1/check` – immer mit signierter Antwort (`active`, `revoked`, `expired`, `unknown`), Rate-Limit 60 Anfragen / 10 Minuten je IP. Eigene SQLite-Datenbank (`licenses`, `checks`), privater Schlüssel nur im Datenvolumen. Verwaltung per CLI (`keygen`, `issue`, `revoke`, `list`, `show`, `serve`). Der Client dazu ist [[Server licensing]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `lizenzserver/__init__.py` | 2 | Lizenzserver: signiert Lizenzen und bestätigt per Check-Endpunkt, ob sie noch aktiv sind. |
| `lizenzserver/__main__.py` | 4 |  |
| `lizenzserver/app.py` | 78 | FastAPI-Anwendung mit Check- und Health-Endpunkt. |
| `lizenzserver/cli.py` | 135 | Kommandozeile: python -m lizenzserver <befehl>. |
| `lizenzserver/core.py` | 130 | Datenbank, Schlüssel und Signierung. |

## Endpunkte (2)

Eigene App, Pfade ohne Mandanten-Präfix.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/health` | `health` (`app.py:43`) | - | – |
| POST | `/api/v1/check` | `check` (`app.py:47`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Datenbank-Tabellen

- **Eigene Datenbank des Lizenzservers** (nicht die der Schule): `licenses` (`lizenzserver/core.py:37`), `checks` (`lizenzserver/core.py:47`)

## Hängt ab von

- –

## Wird genutzt von

- –

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
