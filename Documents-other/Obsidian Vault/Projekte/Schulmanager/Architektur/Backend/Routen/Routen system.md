---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/system.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen system

> API-Routen · 1 Datei(en) · 33 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Allgemeine Informationen: Rollen-/Rechtematrix, Version.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/system.py` | 33 | Allgemeine Informationen: Rollen-/Rechtematrix, Version. |

## Endpunkte (2)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/roles` | `roles` (`system.py:18`) | (angemeldet) | – |
| GET | `/api/v1/version` | `version` (`system.py:29`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Hängt ab von

- [[Server config]] – `config`
- [[Server db]] – `db`
- [[Server deps]] – `deps`
- [[Server permissions]] – `permissions`
- [[Server rights]] – `rights`
- [[Server store]] – `store`

## Wird genutzt von

- –

## Tests

`tests/test_rights.py`, `tests/test_server_core.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
