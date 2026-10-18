---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/integrations/ (7 Dateien)"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul integrations

> Fachlogik (rein, ohne Datenbank und HTTP) · 7 Datei(en) · 3626 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Datenaustausch mit anderen Systemen, alles reine Funktionen auf `School`: Untis GPU (Export/Import der GPU001–GPU014/DIF-Dateien), Schulmanager-Online-Paket (ZIP), CSV (Stammdaten, Excel-tauglich, Spalten-Mapping), iCalendar (RFC 5545) und Webhook-Nutzlasten mit HMAC-SHA256-Signatur. Die HTTP-Seite ist [[Routen features_exchange]]; Webhooks versendet [[Server notify]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/integrations/__init__.py` | 18 | Integrationen: Datenaustausch mit anderen Schul- und Kalendersystemen. |
| `schulmanager/integrations/_common.py` | 254 | Gemeinsame Hilfsfunktionen der Integrationen (intern, keine stabile API). |
| `schulmanager/integrations/csv_io.py` | 1132 | CSV-Import/-Export der Stammdaten (Excel-tauglich, deutsche Spaltennamen). |
| `schulmanager/integrations/ical.py` | 503 | iCalendar-Export (RFC 5545) für Klassen, Lehrkräfte, Räume und Schüler. |
| `schulmanager/integrations/schulmanager_online.py` | 214 | Exportpaket für *Schulmanager Online* und andere Schulsysteme. |
| `schulmanager/integrations/untis_gpu.py` | 1363 | Untis-Datenaustausch über die GPU-/DIF-Textdateien. |
| `schulmanager/integrations/webhooks.py` | 142 | Webhook-Nutzlasten und Signaturen (HMAC-SHA256). |

## Wichtige Funktionen und Klassen

- Funktion `as_date` (`schulmanager/integrations/_common.py:24`) – `date`, `datetime` oder ISO-String (`YYYY-MM-DD` bzw. `YYYYMMDD`) → `date`.
- Funktion `plans_by_date` (`schulmanager/integrations/_common.py:39`) – Normalisiert Vertretungspläne zu `{ISO-Datum: DayPlan-Dict}`.
- Funktion `holiday_on` (`schulmanager/integrations/_common.py:60`)
- Funktion `week_ranges` (`schulmanager/integrations/_common.py:71`) – Laufende Wochen (1-basiert) → `"1,3"` bzw. `"1-4,9"` (Läufe ab drei Wochen als Bereich).
- Funktion `parse_week_list` (`schulmanager/integrations/_common.py:88`) – `"1,3"`, `"1-4,9"`, `"10,27"` → laufende Wochen (1-basiert, sortiert, eindeutig).
- Funktion `period_bounds` (`schulmanager/integrations/_common.py:103`) – (Beginn, Ende) in Minuten seit Mitternacht für Stunden `start`..`start+length-1`.
- Funktion `norm_key` (`schulmanager/integrations/_common.py:124`) – Spaltennamen normalisieren: klein, Umlaute → ae/oe/ue/ss, nur a-z0-9.
- Funktion `split_name` (`schulmanager/integrations/_common.py:133`) – `"Anna Maria Müller"` → `("Anna Maria", "Müller")`.
- Funktion `grade_from_name` (`schulmanager/integrations/_common.py:142`) – Klassenstufe aus Klassennamen ableiten: `"7a"` → 7, `"Q1-2"` → 11, `"EF"` → 10.
- Funktion `decode_bytes` (`schulmanager/integrations/_common.py:159`) – Bytes → Text mit Kodierungserkennung.
- Funktion `encode_lossy` (`schulmanager/integrations/_common.py:183`) – Kodiert `text`; nicht darstellbare Zeichen werden transliteriert (`ğ` → `g`), sonst `?`.
- Funktion `parse_int` (`schulmanager/integrations/_common.py:206`)
- Funktion `parse_float` (`schulmanager/integrations/_common.py:218`)
- Funktion `parse_bool` (`schulmanager/integrations/_common.py:228`)
- Funktion `color_to_win32` (`schulmanager/integrations/_common.py:239`) – `#rrggbb` → Win32-COLORREF (`0x00BBGGRR`), wie Untis Farben speichert.
- Funktion `win32_to_color` (`schulmanager/integrations/_common.py:248`)
- Funktion `describe` (`schulmanager/integrations/csv_io.py:206`) – Zielfelder (mit Beschriftung und erkannten Spaltennamen) und Presets – für Mapping-Dialoge.
- Funktion `format_week_spec` (`schulmanager/integrations/csv_io.py:229`) – Wochenangabe für Tabellen: Rhythmus als Text, Wochenliste als `"1-4,9"`, sonst leer (= jede Woche).
- Funktion `parse_week_spec` (`schulmanager/integrations/csv_io.py:236`) – Gegenstück zu ``: `"1-4,9"` oder `"jede 3. Woche ab Woche 10 [bis Woche 30]"`.
- Funktion `format_rules` (`schulmanager/integrations/csv_io.py:257`) – TimeRules → `"Woche 1: Mi (Praxistag) | Fr Std. 6-8 | Woche 1-4,9: Di"` (Wochen und Stunden 1-basiert;
- Funktion `parse_rules` (`schulmanager/integrations/csv_io.py:306`) – Gegenstück zu `` (ValueError bei unlesbaren Angaben).
- Funktion `format_windows` (`schulmanager/integrations/csv_io.py:356`) – Arbeitszeitfenster → `"Mo-Fr 10:00-18:30 | Woche 2: Mo,Mi 16:00-21:00"` (leer = ganztägig verfügbar).
- Funktion `parse_windows` (`schulmanager/integrations/csv_io.py:398`) – Gegenstück zu ``; versteht auch „Mo–Fr 10:00–18:30; Woche 2: …“, Rhythmus „jede 3. Woche ab Woche 10: …“ und „ganztägi…
- Funktion `religion_category` (`schulmanager/integrations/csv_io.py:438`) – Konfession/Religionsunterricht → `ev | kath | islam | orth | jued | ethik` (`None` = leer).
- Funktion `assign_religion` (`schulmanager/integrations/csv_io.py:490`) – Ordnet `student` dem passenden Teil der Religions-Kopplung seiner Klasse zu.
- Funktion `export_csv` (`schulmanager/integrations/csv_io.py:582`) – CSV (`;`, CRLF) mit führender UTF-8-BOM (`"\ufeff"`) – als UTF-8 speichern/ausliefern.
- Funktion `import_csv` (`schulmanager/integrations/csv_io.py:1083`) – Importiert eine CSV-Datei in `school` (Upsert). Siehe Modul-Doku für Format und Report.
- Funktion `escape_text` (`schulmanager/integrations/ical.py:55`) – TEXT-Escaping nach RFC 5545 §3.3.11.
- Funktion `fold_line` (`schulmanager/integrations/ical.py:62`) – Faltet eine Inhaltszeile: max. `limit` Oktette je physischer Zeile (Fortsetzung mit Leerzeichen).
- Funktion `calendar` (`schulmanager/integrations/ical.py:200`) – Erzeugt einen iCalendar-Text (`text/calendar; charset=utf-8`).
- Funktion `unfold` (`schulmanager/integrations/ical.py:500`) – Hilfsfunktion (Tests/Debug): entfaltet einen iCalendar-Text zu logischen Zeilen.
- Funktion `readme_text` (`schulmanager/integrations/schulmanager_online.py:52`) – Deutsche Importanleitung (Inhalt von `LIESMICH.txt`).
- Funktion `export_package` (`schulmanager/integrations/schulmanager_online.py:167`) – ZIP-Paket (Untis-GPU + CSV + LIESMICH.txt + manifest.json) als Bytes.
- Funktion `unit_numbers` (`schulmanager/integrations/untis_gpu.py:329`) – Kurs-ID → (erste) Untis-Unterrichtsnummer, wie sie `` vergibt.
- Funktion `export_files` (`schulmanager/integrations/untis_gpu.py:515`) – Alle GPU-Dateien als `{"GPU001.TXT": bytes, ...}` (CRLF, Standard Windows-1252).
- Funktion `export_zip` (`schulmanager/integrations/untis_gpu.py:541`) – ZIP mit GPU001–006, GPU010, GPU014 (aus `plans`: Liste/Dict von DayPlan-Dicts) und GPU015.
- Funktion `import_files` (`schulmanager/integrations/untis_gpu.py:1321`) – Importiert Untis-GPU-Dateien.
- Funktion `payload` (`schulmanager/integrations/webhooks.py:64`) – Baut die Webhook-Nutzlast.
- Funktion `encode` (`schulmanager/integrations/webhooks.py:89`) – Kanonische JSON-Bytes (UTF-8, sortierte Schlüssel, kompakt) – genau diese Bytes signieren & senden.
- Funktion `sign` (`schulmanager/integrations/webhooks.py:95`) – `sha256=<hex>` = HMAC-SHA256(secret, body).
- Funktion `verify` (`schulmanager/integrations/webhooks.py:104`) – Prüft die Signatur (konstante Laufzeit).
- Funktion `headers` (`schulmanager/integrations/webhooks.py:132`) – HTTP-Header für eine Zustellung (Content-Type, Event, Delivery, Timestamp, Signatur).

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul legacy]] – `legacy` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul teacher_profile]] – `teacher_profile` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Routen features_classes]]
- [[Routen features_exchange]]
- [[Server notify]]

## Tests

`tests/test_curricula.py`, `tests/test_integrations.py`, `tests/test_server_features.py`, `tests/test_weeks.py`, `tests/test_weeks_r2.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
