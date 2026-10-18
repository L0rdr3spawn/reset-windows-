---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/api_scopes.py"
stand: 2026-10-12 20:32
generator: schulmanager-regen
---

# Server api_scopes

> Server-Kern · 1 Datei(en) · 468 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

API-Zugänge mit Umfang: Bereiche, Filter, zentrale Durchsetzung (docs/API-ZUGAENGE.md).

Ein **Zugang** ist ein `ApiToken` mit `scope` (Bereiche + Filter + optional Schreibrechte). Er gilt **nur** für die öffentliche, versionierte API unter `/api/v1/open/…` (`routes/api_open.py`) – jede andere Route lehnt `deps.authenticate` für solche Zugänge ab. Innerhalb der öffentlichen API gilt:

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/api_scopes.py` | 468 | API-Zugänge mit Umfang: Bereiche, Filter, zentrale Durchsetzung (docs/API-ZUGAENGE.md). |

## Wichtige Funktionen und Klassen

- Funktion `strip_private` (`schulmanager/server/api_scopes.py:89`) – Entfernt rekursiv Schlüssel mit Gesundheits-/Förder-/Fehlzeitenbezug aus einer Antwort (Sicherheitsnetz).
- Klasse `Filters` (`schulmanager/server/api_scopes.py:101`)
  - Methoden: `from_scope`:109, `restricted`:114, `plan_allowed`:118, `entry_allowed`:125
- Klasse `Access` (`schulmanager/server/api_scopes.py:151`) – Ergebnis von ``: das Konto (`user`), der Bereich und die Filter des Zugangs.
  - Methoden: `scoped`:159
- Funktion `open_access` (`schulmanager/server/api_scopes.py:163`) – Abhängigkeit jeder Route der öffentlichen API: verlangt Anmeldung, den Bereich `area` (bei `write=True`
- Funktion `public_meta` (`schulmanager/server/api_scopes.py:190`) – Platzhalter-Abhängigkeit für Routen ohne Anmeldung (Struktur-Metadaten).
- Funktion `route_area` (`schulmanager/server/api_scopes.py:198`) – Bereich einer FastAPI-Route (über ihre Abhängigkeiten) oder `None`.
- Funktion `iter_routes` (`schulmanager/server/api_scopes.py:211`) – Alle Routen mit vollem Pfad – auch hinter `include_router` (neuere FastAPI-Versionen hängen eingebundene
- Funktion `open_routes` (`schulmanager/server/api_scopes.py:223`) – Alle Routen der öffentlichen API: `[{method, path, area, write, summary}]` (Reihenfolge wie registriert).
- Funktion `reset_rate_limits` (`schulmanager/server/api_scopes.py:251`)
- Funktion `ip_allowed` (`schulmanager/server/api_scopes.py:268`)
- Funktion `log_use` (`schulmanager/server/api_scopes.py:286`) – Nutzungsprotokoll (letzte `` Zeilen je Zugang); Fehler hier brechen nie die Anfrage ab.
- Funktion `check_request` (`schulmanager/server/api_scopes.py:310`) – Zentrale Vorprüfung für Zugänge mit Umfang (in `deps.authenticate`): nur `/open/…`, IP-Beschränkung,
- Funktion `area_available` (`schulmanager/server/api_scopes.py:329`) – Darf das Konto `user` den Bereich überhaupt freigeben (Rechte des Kontos)?
- Funktion `write_available` (`schulmanager/server/api_scopes.py:335`)
- Funktion `creatable_values` (`schulmanager/server/api_scopes.py:340`) – Werte je Filterart, die das Konto freigeben darf (`None` = alle der Schule). Nie mehr als das Konto selbst
- Funktion `normalize_scope` (`schulmanager/server/api_scopes.py:361`) – Prüft die Wünsche beim Anlegen gegen die Rechte des Kontos und liefert den gespeicherten `scope`.
- Funktion `describe` (`schulmanager/server/api_scopes.py:420`) – „Dieser Zugang darf: …“ für die Oberfläche: `{can: [...], cannot: [...], warnings: [...]}`.
- Funktion `example_paths` (`schulmanager/server/api_scopes.py:450`) – Beispielaufrufe (Pfad ab `/api/v1`) passend zum Umfang.
- Funktion `expires_at` (`schulmanager/server/api_scopes.py:466`)

## Datenbank-Tabellen

- **Nutzt:** `api_token_log` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `api_tokens` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Server db]] – `api_access`, `db`, `db_models`
- [[Server deps]] – `deps` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen api_discovery]]
- [[Routen api_open]]
- [[Routen features_api_access]]
- [[Server deps]]

## Tests

`tests/test_api_access.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
