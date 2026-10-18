---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_exchange.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen features_exchange

> API-Routen · 1 Datei(en) · 449 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Import/Export (Untis GPU, Schulmanager-Online-Paket, CSV, JSON), iCal-Feed und Benachrichtigungs-Outbox.

* Exporte: `timetable.edit` oder `masterdata.edit` (enthalten Schülerdaten)
* Importe laufen über `store.mutate` (neue Version, Undo möglich); `?dry_run=1` prüft nur.
* `public_router`: `GET /ical/{token}.ics` (ohne `/api/v1`, Token aus `GET /me/ical-url`)

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_exchange.py` | 449 | Import/Export (Untis GPU, Schulmanager-Online-Paket, CSV, JSON), iCal-Feed und |

## Endpunkte (11)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/export/untis.zip` | `export_untis` (`features_exchange.py:73`) | (angemeldet) | – |
| GET | `/api/v1/export/schulmanager-online.zip` | `export_smo` (`features_exchange.py:84`) | (angemeldet) | – |
| GET | `/api/v1/export/csv/{what}` | `export_csv` (`features_exchange.py:96`) | (angemeldet) | – |
| GET | `/api/v1/export/json` | `export_json` (`features_exchange.py:112`) | (angemeldet) | – |
| POST | `/api/v1/import/untis` | `import_untis` (`features_exchange.py:160`) | timetable.edit | – |
| GET | `/api/v1/import/csv/{what}/fields` | `import_csv_fields` (`features_exchange.py:201`) | (angemeldet) | – |
| POST | `/api/v1/import/csv/{what}` | `import_csv` (`features_exchange.py:209`) | (angemeldet) | – |
| POST | `/api/v1/import/json` | `import_json` (`features_exchange.py:287`) | timetable.edit | – |
| GET | `/ical/{token}.ics` | `ical_feed` (`features_exchange.py:388`) | - | – |
| GET | `/api/v1/notifications/outbox` | `outbox` (`features_exchange.py:417`) | settings.edit | – |
| POST | `/api/v1/notifications/outbox/{item_id}/retry` | `outbox_retry` (`features_exchange.py:435`) | settings.edit | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `curriculum_conflict_warnings` (`schulmanager/server/routes/features_exchange.py:228`) – Überschneidende Stundentafeln (`planning.curriculum_conflicts`) als Hinweise mit Klassenliste – mit
- Funktion `json_integrity` (`schulmanager/server/routes/features_exchange.py:308`) – Kurzprüfung eines importierten Dokuments (fehlende Referenzen).

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul integrations]] – `csv_io`, `ical`, `schulmanager_online`, `untis_gpu` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul planning]] – `planning` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_data]] – `features_data` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server notify]] – `notify` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_curricula.py`, `tests/test_lead_integration.py`, `tests/test_server_features.py`, `tests/test_teacher_scope.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
