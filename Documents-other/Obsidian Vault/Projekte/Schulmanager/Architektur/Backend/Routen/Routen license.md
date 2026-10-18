---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/license.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen license

> API-Routen · 1 Datei(en) · 53 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Lizenz der Schule (`licensing`): Stand anzeigen, Lizenz einspielen, jetzt online bestätigen.

* `GET /license` – alle Angemeldeten: Kurzstand (für den Hinweis-Balken); Admin (`system.admin`): alles.
* `PUT /license` – Admin: Lizenzdatei (Text) einspielen; wird mit dem Schlüssel des Anbieters geprüft.
* `POST /license/check` – Admin: sofort beim Lizenzserver bestätigen lassen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/license.py` | 53 | Lizenz der Schule (`licensing`): Stand anzeigen, Lizenz einspielen, jetzt online bestätigen. |

## Endpunkte (3)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/license` | `get_license` (`license.py:25`) | (angemeldet) | [[Seite LicensePage]] |
| PUT | `/api/v1/license` | `put_license` (`license.py:35`) | system.admin | [[Seite LicensePage]] |
| POST | `/api/v1/license/check` | `check_license` (`license.py:49`) | system.admin | [[Seite LicensePage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `LicenseIn` (`schulmanager/server/routes/license.py:20`)

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server db]] – `db`
- [[Server deps]] – `deps`
- [[Server licensing]] – `licensing` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_license.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
