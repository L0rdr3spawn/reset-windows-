---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/logging_setup.py, schulmanager/server/metrics.py, schulmanager/server/middleware.py"
stand: 2026-10-12 21:07
generator: schulmanager-regen
---

# Server middleware und metrics

> Server-Kern · 3 Datei(en) · 322 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

ASGI-Middleware (`CoreMiddleware`: Request-ID, Metriken, Access-Log mit maskierten iCal-Token, Security-Header), Prometheus-Textformat ohne Zusatzpaket (`metrics`) und Logging (JSON in Produktion, `request_id` im Kontext).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/logging_setup.py` | 76 | Logging: JSON-Zeilen (Produktion) oder lesbarer Text (Entwicklung), Request-ID im Kontext. |
| `schulmanager/server/metrics.py` | 124 | Prometheus-Metriken ohne Zusatzpaket (Text-Exposition-Format 0.0.4). |
| `schulmanager/server/middleware.py` | 122 | ASGI-Middleware: Request-ID, Metriken, Access-Log, Security-Header. |

## Wichtige Funktionen und Klassen

- Klasse `JsonFormatter` (`schulmanager/server/logging_setup.py:18`)
  - Methoden: `format`:19
- Klasse `TextFormatter` (`schulmanager/server/logging_setup.py:38`)
  - Methoden: `format`:42
- Funktion `setup_logging` (`schulmanager/server/logging_setup.py:51`) – Richtet das Root-Logging ein (idempotent; ersetzt nur den eigenen Handler).
- Klasse `Metrics` (`schulmanager/server/metrics.py:23`)
  - Methoden: `reset`:28, `observe`:38, `login`:51, `render`:55
- Funktion `process_metrics` (`schulmanager/server/metrics.py:94`) – Standard-Prozessmetriken (Linux `/proc`; auf anderen Systemen soweit verfügbar).
- Funktion `csp_for` (`schulmanager/server/middleware.py:30`) – CSP der Seite. Nur Seiten (nicht `/api/`) erhalten die Quellen der **aktiven** Anmeldedienste (Google/Apple);
- Funktion `mask_path` (`schulmanager/server/middleware.py:42`) – Geheime Pfadbestandteile (iCal-Token) für Logs unkenntlich machen.
- Klasse `CoreMiddleware` (`schulmanager/server/middleware.py:60`) – Eine Middleware für alles Querschnittliche (schnell, ohne BaseHTTPMiddleware).

## Datenbank-Tabellen

- **Nutzt:** `messages` → [[Datenmodell#Postfach und Chats]]

## Hängt ab von

- [[Server config]] – `config`
- [[Server konten und anmeldung]] – `sso_providers` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen auth]]
- [[Server app]] – `app`

## Tests

`tests/test_server_core_store.py`, `tests/test_sso_browser.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
