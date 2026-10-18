---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_holiday_import.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen features_holiday_import

> API-Routen · 1 Datei(en) · 102 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Ferien/Feiertage aus öffentlicher API übernehmen (`server/holiday_import.py`).

* `GET  /holiday-import`            Einstellungen + Status (Land, Region, Automatik, letzter Lauf)
* `PUT  /holiday-import`            Einstellungen speichern (schaltet bei `enabled` die Automatik an)
* `GET  /holiday-import/countries`  Länderliste (serverseitig abgerufen, 24 h gecacht)
* `GET  /holiday-import/regions?country=DE`  Bundesländer/Regionen
* `POST /holiday-import/preview`    Was würde sich ändern? (ändert nichts)
* `POST /holiday-import/apply`      Jetzt übernehmen

Recht wie bei der Pflege der Ferien in den Stammdaten: `masterdata.edit`.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_holiday_import.py` | 102 | Ferien/Feiertage aus öffentlicher API übernehmen (`server/holiday_import.py`). |

## Endpunkte (6)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/holiday-import` | `get_state` (`features_holiday_import.py:63`) | masterdata.edit | [[Seite PlanningPage]] |
| PUT | `/api/v1/holiday-import` | `put_settings` (`features_holiday_import.py:68`) | masterdata.edit | [[Seite PlanningPage]] |
| GET | `/api/v1/holiday-import/countries` | `list_countries` (`features_holiday_import.py:81`) | masterdata.edit | [[Seite PlanningPage]] |
| GET | `/api/v1/holiday-import/regions` | `list_regions` (`features_holiday_import.py:87`) | masterdata.edit | [[Seite PlanningPage]] |
| POST | `/api/v1/holiday-import/preview` | `preview` (`features_holiday_import.py:94`) | masterdata.edit | [[Seite PlanningPage]] |
| POST | `/api/v1/holiday-import/apply` | `apply` (`features_holiday_import.py:100`) | masterdata.edit | [[Seite PlanningPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `SettingsIn` (`schulmanager/server/routes/features_holiday_import.py:28`)
- Klasse `RunIn` (`schulmanager/server/routes/features_holiday_import.py:36`)

## Hängt ab von

- [[Routen features_common]] – `features_common`
- [[Server config]] – `config`
- [[Server deps]] – `deps`
- [[Server holiday_import]] – `holiday_import`

## Wird genutzt von

- –

## Tests

`tests/test_holiday_import.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
