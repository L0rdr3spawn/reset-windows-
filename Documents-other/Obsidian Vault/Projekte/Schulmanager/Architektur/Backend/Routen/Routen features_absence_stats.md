---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_absence_stats.py"
stand: 2026-10-12 22:34
generator: schulmanager-regen
---

# Routen features_absence_stats

> API-Routen · 1 Datei(en) · 376 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Fehlzeiten-Statistik einer Schülerin/eines Schülers (Anzahl und Prozent der Unterrichtsstunden, je Fach, je Tag/Stunde).

`GET /absence-stats?student_id=&period=year|half1|half2|custom&from=&to=` und `GET /absence-stats/class?class_id=` (Klassenleitung/Verwaltung: wer ist nahe an oder über der Grenze).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_absence_stats.py` | 376 | Fehlzeiten-Statistik einer Schülerin/eines Schülers (Anzahl und Prozent der Unterrichtsstunden, je… |

## Endpunkte (2)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/absence-stats` | `absence_stats` (`features_absence_stats.py:313`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/absence-stats/class` | `class_absence_stats` (`features_absence_stats.py:346`) | (angemeldet) | [[Feature students]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `bucket_of` (`schulmanager/server/routes/features_absence_stats.py:62`) – Zustand einer Meldung für die Statistik; `None` = zählt nicht (z. B. noch nicht genehmigte Beurlaubung).
- Funktion `limits` (`schulmanager/server/routes/features_absence_stats.py:73`) – Grenzen in Prozent aus den Schul-Einstellungen (0 = keine).
- Funktion `period_length` (`schulmanager/server/routes/features_absence_stats.py:85`) – Dauer einer Unterrichtsstunde in Minuten (Einstellung `period_minutes`, sonst 45).
- Funktion `limit_state` (`schulmanager/server/routes/features_absence_stats.py:93`) – Ampel und Restzahl einer Gruppe (Fach/Gesamt) gegen die Grenzen – gerechnet in versäumten Minuten.
- Funktion `year_range` (`schulmanager/server/routes/features_absence_stats.py:111`) – Beginn und Ende des laufenden Schuljahres (Einstellungen; ohne Angabe 1. August bis 31. Juli).
- Funktion `resolve_period` (`schulmanager/server/routes/features_absence_stats.py:123`) – `(Schlüssel, von, bis, Bezeichnung)` des gewählten Zeitraums. Halbjahre: 1. bis 31.01., 2. ab 01.02.
- Funktion `held_lessons` (`schulmanager/server/routes/features_absence_stats.py:143`) – Stattgefundene Stunden je Schultag: `{tag: {stunde(0-basiert): fach}}` (je Stunde eine, auch bei parallelen
- Funktion `compute` (`schulmanager/server/routes/features_absence_stats.py:180`) – Reine Auswertung (ohne Datenbank): `held` laut ``, `rows` = Meldungen der Person.

## Datenbank-Tabellen

- **Nutzt:** `student_absences` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `absence_access`

## Wird genutzt von

- –

## Tests

`tests/test_absence_stats_adult.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
