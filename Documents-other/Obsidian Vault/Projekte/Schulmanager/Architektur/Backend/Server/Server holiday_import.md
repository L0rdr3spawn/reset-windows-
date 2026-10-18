---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/holiday_import.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server holiday_import

> Server-Kern · 1 Datei(en) · 444 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Übernimmt Feiertage und Schulferien automatisch aus öffentlichen APIs (OpenHolidays; Nager.Date als Rückfall für gesetzliche Feiertage) in das Planungsdokument (`School.holiday_import`: Land, Region, Sprache). Importierte `Holiday`-Einträge tragen Quell-ID und Fingerabdruck, sodass Handänderungen nie überschrieben und Handlöschungen nicht wiederhergestellt werden; es wird nie gelöscht. Ein Hintergrund-Thread (`start`, vom [[Server runtime]] aufgerufen) prüft beim Start und danach täglich; abschaltbar mit `SM_HOLIDAY_IMPORT=0`. Ergebnis geht über den [[Server store]] als neue Planversion. Neu im Arbeitsstand (noch nicht committet).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/holiday_import.py` | 444 | Feiertage und Schulferien aus einer öffentlichen API automatisch übernehmen. |

## Wichtige Funktionen und Klassen

- Klasse `HolidayImportError` (`schulmanager/server/holiday_import.py:56`) – Abruf oder Einstellung fehlgeschlagen (`status` = HTTP-Status für die Route).
- Funktion `fetch_json` (`schulmanager/server/holiday_import.py:65`) – GET → JSON mit Timeout. Fehler → ``.
- Funktion `clear_cache` (`schulmanager/server/holiday_import.py:97`)
- Funktion `countries` (`schulmanager/server/holiday_import.py:115`) – `[{code, name, source}]` – `source` = `openholidays` (mit Schulferien) oder `nager` (nur Feiertage).
- Funktion `regions` (`schulmanager/server/holiday_import.py:144`) – `[{code, name, category, parent}]` (Bundesländer usw.); leer, wenn die Quelle keine Regionen kennt.
- Funktion `get_settings` (`schulmanager/server/holiday_import.py:166`)
- Funktion `clean_settings` (`schulmanager/server/holiday_import.py:173`)
- Funktion `school_year_of` (`schulmanager/server/holiday_import.py:185`) – Startjahr des Schuljahres, in dem `day` liegt (Schuljahr: 1.8. – 31.7.).
- Funktion `current_school_years` (`schulmanager/server/holiday_import.py:190`)
- Funktion `sig_of` (`schulmanager/server/holiday_import.py:204`)
- Funktion `fetch_candidates` (`schulmanager/server/holiday_import.py:252`) – Feiertage + Schulferien der Schuljahre `years` (Startjahre), nach Datum sortiert, ohne Doppelte.
- Funktion `plan_changes` (`schulmanager/server/holiday_import.py:269`) – Was ein Import täte (ändert nichts): `[{action, name, date_from, date_to, kind, old?}]`.
- Funktion `counts` (`schulmanager/server/holiday_import.py:301`)
- Funktion `apply_plan` (`schulmanager/server/holiday_import.py:308`) – Führt `` am Schuldokument aus (innerhalb von `store.mutate`).
- Funktion `status` (`schulmanager/server/holiday_import.py:343`)
- Funktion `preview` (`schulmanager/server/holiday_import.py:347`)
- Funktion `run_import` (`schulmanager/server/holiday_import.py:352`) – Ruft die Quelle ab (außerhalb der Sperre) und übernimmt per `store.mutate`. Rückgabe `{changes, counts}`.
- Funktion `auto_check` (`schulmanager/server/holiday_import.py:381`) – Ein Automatik-Durchlauf. Rückgabe: Sekunden bis zum nächsten. Wirft nie.
- Funktion `start` (`schulmanager/server/holiday_import.py:417`)
- Funktion `stop` (`schulmanager/server/holiday_import.py:431`)
- Funktion `kick` (`schulmanager/server/holiday_import.py:441`) – Automatik sofort anstoßen (z. B. nach dem Einschalten).

## Hängt ab von

- [[Modul models]] – `models` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_holiday_import]]

## Tests

`tests/test_holiday_import.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
