---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_calendar.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Routen features_calendar

> API-Routen · 1 Datei(en) · 308 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Schuljahr und Wochen (Entwurf KALENDER-ZEITRASTER §15.3, R3).

* `GET /calendar/school-year?date=&class_id=` – alle Wochen 1 … Y des Schuljahres von `date` (Standard: heute)
  mit KW, Zeitraum, Ferien; dazu Beginn/Ende, Zählung, Schulöffnungstage und Hinweise.
  Für alle Angemeldeten lesbar (keine Personendaten); `class_id` nur mit Sichtrecht auf die Klasse (sonst 404),
  dann gelten die Unterrichtstage der Klasse.
* `GET /calendar/week?date=&class_id=` – `WeekInfo` einer Woche (gleiche Rechte).

Die Vorschau einer Kalenderänderung liegt bei den Einstellungen (`POST /settings/calendar-preview`).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_calendar.py` | 308 | Schuljahr und Wochen (Entwurf KALENDER-ZEITRASTER §15.3, R3). |

## Endpunkte (2)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/calendar/school-year` | `school_year` (`features_calendar.py:53`) | (angemeldet) | [[Frontend Komponenten]] |
| GET | `/api/v1/calendar/week` | `week` (`features_calendar.py:65`) | (angemeldet) | [[Feature classes]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `calendar_week` (`schulmanager/server/routes/features_calendar.py:198`)

## Datenbank-Tabellen

- **Nutzt:** `student_absences` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks` *(nur zur Laufzeit importiert)*
- [[Routen features_channels]] – `features_channels` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_exams]] – `features_exams` *(nur zur Laufzeit importiert)*
- [[Routen features_grades]] – `features_grades` *(nur zur Laufzeit importiert)*
- [[Routen features_makeups]] – `features_makeups` *(nur zur Laufzeit importiert)*
- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Routen features_substitutions]] – `features_substitutions`
- [[Routen features_timetable]] – `features_timetable`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`

## Wird genutzt von

- [[Routen api_open]]

## Tests

`tests/test_api_access.py`, `tests/test_calendar.py`, `tests/test_homework_links.py`, `tests/test_makeups.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
