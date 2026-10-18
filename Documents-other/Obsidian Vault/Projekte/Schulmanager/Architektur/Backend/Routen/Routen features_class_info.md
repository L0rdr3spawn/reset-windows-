---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_class_info.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Routen features_class_info

> API-Routen · 1 Datei(en) · 216 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Klassenraum, Bereich „Klasse“ (Startansicht): Regelplan, Termine/Elternabende, Ansprechpersonen.

Die angehefteten **Infokarten** sind gewöhnliche Textseiten des Klassenraums mit `info_card = true` (`POST /channels/{id}/items` mit `info_card`; ändern/löschen/sortieren wie jedes Material, siehe `features_channels.py`) – hier gibt es dafür keine zweite Verwaltung.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_class_info.py` | 216 | Klassenraum, Bereich „Klasse“ (Startansicht): Regelplan, Termine/Elternabende, Ansprechpersonen. |

## Endpunkte (4)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/channels/{channel_id}/klasse` | `class_overview` (`features_class_info.py:130`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/klasse/plan` | `class_plan` (`features_class_info.py:147`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/klasse/termine` | `add_event` (`features_class_info.py:166`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/klasse/termine/{event_id}` | `delete_event` (`features_class_info.py:198`) | (angemeldet) | [[Feature channels]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `EventIn` (`schulmanager/server/routes/features_class_info.py:42`)

## Hängt ab von

- [[Modul channels]] – `channels`
- [[Modul models]] – `models`
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Routen features_channels]] – `features_channels`
- [[Routen features_common]] – `features_common`
- [[Routen features_data]] – `features_data` *(nur zur Laufzeit importiert)*
- [[Routen features_timetable]] – `features_timetable`
- [[Server db]] – `db`
- [[Server deps]] – `deps`

## Wird genutzt von

- [[Routen features_absence_log]]

## Tests

`tests/test_absence_log.py`, `tests/test_calendar.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_channels_rooms.py`, `tests/test_class_room_info.py`, `tests/test_homework_links.py`, `tests/test_rights.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
