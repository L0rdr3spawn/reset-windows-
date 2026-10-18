---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/api_open.py"
stand: 2026-10-12 20:32
generator: schulmanager-regen
---

# Routen api_open

> API-Routen · 1 Datei(en) · 275 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Öffentliche, versionierte API für Apps und KI-Werkzeuge: `/api/v1/open/…` (docs/API-ZUGAENGE.md).

Jede Route hängt über `Depends(open_access("<bereich>"))` an einem Bereich (`api_scopes.AREAS`); Zugänge mit Umfang (Token `sma_…`) erreichen nur diese Routen. Die Handler benutzen die bestehenden Funktionen mit dem Konto des Zugangs – es gelten also Rechte und Datenumfang des Kontos – und beschneiden das Ergebnis zusätzlich auf die Filter des Zugangs. Gesundheits-/Förderdaten gibt keine dieser Routen aus.

Neue Funktion für Apps/KIs? Bereich in `api_scopes.AREAS` festlegen, hier die Route mit `open_access` anbinden, Beschreibung (`summary`/`description`/Beispiel) schreiben – `/llms.txt` und `/api/v1/meta/openapi.json` übernehmen sie automatisch.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/api_open.py` | 275 | Öffentliche, versionierte API für Apps und KI-Werkzeuge: `/api/v1/open/…` (docs/API-ZUGAENGE.md). |

## Endpunkte (11)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/open/timetable/{kind}/{ref}` | `timetable` (`api_open.py:86`) | - | – |
| GET | `/api/v1/open/substitutions` | `substitutions_day` (`api_open.py:104`) | - | – |
| GET | `/api/v1/open/substitutions/range` | `substitutions_range` (`api_open.py:117`) | - | – |
| GET | `/api/v1/open/calendar/school-year` | `calendar_school_year` (`api_open.py:139`) | - | – |
| GET | `/api/v1/open/calendar/week` | `calendar_week` (`api_open.py:155`) | - | – |
| GET | `/api/v1/open/rooms` | `rooms` (`api_open.py:174`) | - | – |
| GET | `/api/v1/open/classes` | `classes` (`api_open.py:186`) | - | – |
| GET | `/api/v1/open/teachers` | `teachers` (`api_open.py:198`) | - | – |
| GET | `/api/v1/open/sites` | `sites` (`api_open.py:210`) | - | – |
| GET | `/api/v1/open/announcements` | `announcements` (`api_open.py:226`) | - | – |
| POST | `/api/v1/open/announcements` | `post_announcement` (`api_open.py:272`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Hängt ab von

- [[Routen features_announcements]] – `features_announcements`
- [[Routen features_calendar]] – `features_calendar` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_substitutions]] – `features_substitutions` *(nur zur Laufzeit importiert)*
- [[Routen features_timetable]] – `features_timetable` *(nur zur Laufzeit importiert)*
- [[Server api_scopes]] – `api_scopes`
- [[Server audit]] – `audit` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`

## Wird genutzt von

- –

## Tests

`tests/test_api_access.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
