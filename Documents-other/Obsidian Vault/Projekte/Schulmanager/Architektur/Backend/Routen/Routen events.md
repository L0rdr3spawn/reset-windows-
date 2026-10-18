---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/events.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen events

> API-Routen · 1 Datei(en) · 38 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Server-Sent Events: `GET /api/v1/events` (Anmeldung nötig).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/events.py` | 38 | Server-Sent Events: `GET /api/v1/events` (Anmeldung nötig). |

## Endpunkte (1)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/events` | `events` (`events.py:18`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Hängt ab von

- [[Server config]] – `config`
- [[Server db]] – `db`
- [[Server deps]] – `deps` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events`
- [[Server runtime]] – `runtime`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_calendar.py`, `tests/test_license.py`, `tests/test_server_core_store.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
