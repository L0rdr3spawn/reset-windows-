---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_api_access.py"
stand: 2026-10-12 20:34
generator: schulmanager-regen
---

# Routen features_api_access

> API-Routen · 1 Datei(en) · 242 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

API-Zugänge verwalten: ausgeben, auflisten, Nutzung ansehen, widerrufen (docs/API-ZUGAENGE.md).

* Anlegen: nur mit Anmeldung per Sitzung (kein Token stellt Zugänge aus) und Recht `api.own` bzw. `api.manage`.
  Ein Konto gibt **höchstens aus, was es selbst sieht** (`api_scopes.normalize_scope`); Gesundheits-/Förderdaten
  gibt es in keinem Bereich.
* Das Token wird nur in der Antwort des Anlegens im Klartext geliefert, gespeichert wird nur der Hash.
* `api.manage` (Administration, Schulleitung): alle Zugänge sehen, Nutzung prüfen, widerrufen. `api.own`: nur eigene.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_api_access.py` | 242 | API-Zugänge verwalten: ausgeben, auflisten, Nutzung ansehen, widerrufen (docs/API-ZUGAENGE.md). |

## Endpunkte (6)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/api-access/meta` | `access_meta` (`features_api_access.py:125`) | (angemeldet) | [[Feature api-zugaenge]] |
| POST | `/api/v1/api-access/preview` | `access_preview` (`features_api_access.py:164`) | (angemeldet) | [[Feature api-zugaenge]] |
| GET | `/api/v1/api-access` | `list_access` (`features_api_access.py:175`) | (angemeldet) | [[Feature api-zugaenge]] |
| POST | `/api/v1/api-access` | `create_access` (`features_api_access.py:189`) | (angemeldet) | [[Feature api-zugaenge]] |
| GET | `/api/v1/api-access/{access_id}` | `get_access` (`features_api_access.py:220`) | (angemeldet) | [[Feature api-zugaenge]] |
| DELETE | `/api/v1/api-access/{access_id}` | `revoke_access` (`features_api_access.py:232`) | (angemeldet) | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `FiltersIn` (`schulmanager/server/routes/features_api_access.py:33`)
- Klasse `AccessIn` (`schulmanager/server/routes/features_api_access.py:41`)
- Funktion `access_dict` (`schulmanager/server/routes/features_api_access.py:89`)

## Datenbank-Tabellen

- **Nutzt:** `api_token_log` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `api_tokens`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen features_common]] – `features_common`
- [[Server api_scopes]] – `api_scopes`
- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server db]] – `api_access`, `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server konten und anmeldung]] – `security`

## Wird genutzt von

- –

## Tests

`tests/test_api_access.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
