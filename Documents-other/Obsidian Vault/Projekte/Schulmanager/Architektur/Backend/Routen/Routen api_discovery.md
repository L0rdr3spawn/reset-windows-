---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/api_discovery.py"
stand: 2026-10-12 20:32
generator: schulmanager-regen
---

# Routen api_discovery

> API-Routen · 1 Datei(en) · 255 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Auffindbarkeit für KIs und Apps: `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/.well-known/…` und die Struktur-Metadaten der öffentlichen API (`/api/v1/meta/scopes`, `/api/v1/meta/openapi.json`).

Alles hier ist ohne Anmeldung erreichbar und enthält **nur Struktur** (Begriffe, Endpunkte, Bereiche) – nie Schul- oder Personendaten. Die Endpunktlisten werden aus den tatsächlich registrierten Routen unter `/api/v1/open` erzeugt (`api_scopes.open_routes`): neue Routen erscheinen automatisch.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/api_discovery.py` | 255 | Auffindbarkeit für KIs und Apps: `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/.well-known/…` und… |

## Endpunkte (7)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/meta/scopes` | `meta_scopes` (`api_discovery.py:59`) | - | – |
| GET | `/api/v1/meta/openapi.json` | `meta_openapi` (`api_discovery.py:113`) | - | – |
| GET | `/llms.txt` | `llms` (`api_discovery.py:219`) | - | – |
| GET | `/llms-full.txt` | `llms_full` (`api_discovery.py:224`) | - | – |
| GET | `/.well-known/llms.txt` | `well_known_llms` (`api_discovery.py:229`) | - | – |
| GET | `/.well-known/api-catalog` | `api_catalog` (`api_discovery.py:234`) | - | – |
| GET | `/robots.txt` | `robots` (`api_discovery.py:248`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `scopes_document` (`schulmanager/server/routes/api_discovery.py:33`)
- Funktion `public_openapi` (`schulmanager/server/routes/api_discovery.py:75`) – OpenAPI-Dokument nur der öffentlichen API (`/api/v1/open` und `/api/v1/meta`) – unabhängig davon, ob die
- Funktion `llms_txt` (`schulmanager/server/routes/api_discovery.py:146`)

## Hängt ab von

- [[Server api_scopes]] – `api_scopes`
- [[Server config]] – `config`

## Wird genutzt von

- –

## Tests

`tests/test_api_access.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
