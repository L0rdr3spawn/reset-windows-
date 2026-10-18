---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/calendar_utils.py"
stand: 2026-10-12 21:44
generator: schulmanager-regen
---

# Modul calendar_utils

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 335 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Kalender-Hilfen über dem Planungsdokument: Schuljahr und Schuljahres-Historie (`year_bounds`, `school_year`), laufende Woche (`week_no`, `plan_week`, 1 … 52/53), Unterrichtstage je Schule/Klasse (`class_days`, `open_days`, `is_school_day`), Ferien und Feiertage (`holiday_of`, `day_kind`) sowie Zeitraster (`period_time`, `break_time`). Liefert auch `week_info` / `school_year_info` für die Kalender-Endpunkte ([[Routen features_calendar]]). Zusammen mit [[Modul weeks]] die einzige Stelle für Kalenderlogik.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/calendar_utils.py` | 335 | Kalender-Hilfen: Schuljahr, laufende Woche, Unterrichtstage, Ferien, Zeitraster. |

## Wichtige Funktionen und Klassen

- Funktion `as_date` (`schulmanager/calendar_utils.py:27`) – Akzeptiert `date`, `datetime` oder ISO-String.
- Funktion `monday_of` (`schulmanager/calendar_utils.py:36`)
- Funktion `base_start` (`schulmanager/calendar_utils.py:55`) – Beginn des (aktuellen) Schuljahres laut Einstellungen: `school_year_start`, sonst `cycle_start`.
- Funktion `year_starts` (`schulmanager/calendar_utils.py:60`) – Beginndaten der Schuljahre (aufsteigend): Verlauf + aktueller Beginn, Lücken > 400 Tage und die Zeit bis
- Funktion `year_bounds` (`schulmanager/calendar_utils.py:86`) – `(Montag der Woche 1, Wochen Y, Beginndatum)` des Schuljahres, zu dem `d` gehört.
- Funktion `school_year` (`schulmanager/calendar_utils.py:103`) – `(Montag der Woche 1, Zahl der Wochen Y)` des Schuljahres von `d`.
- Funktion `week_no` (`schulmanager/calendar_utils.py:109`) – Laufende Woche (Position im Schuljahr; vor Beginn ≤ 0, beim Altdokument nach Y weiter > Y).
- Funktion `plan_week` (`schulmanager/calendar_utils.py:116`) – Laufende Woche für Wochenangaben (`weeks`/`rhythm`): wie `week_no`; beim Altdokument ohne
- Funktion `default_days` (`schulmanager/calendar_utils.py:129`) – Unterrichtstage der Schulvorgabe (0–6).
- Funktion `class_days` (`schulmanager/calendar_utils.py:135`) – Unterrichtstage einer Klasse (eigene, sonst Schulvorgabe).
- Funktion `open_days` (`schulmanager/calendar_utils.py:147`) – Schulöffnungstage: Unterrichtstage mindestens einer Klasse (ohne Klassen: Schulvorgabe).
- Funktion `holiday_of` (`schulmanager/calendar_utils.py:164`) – Ferien/Feiertag an `day` (erster Treffer) oder `None`.
- Funktion `holiday_name` (`schulmanager/calendar_utils.py:175`) – Name der Ferien/des Feiertags an `day` oder `None`.
- Funktion `is_school_day` (`schulmanager/calendar_utils.py:185`) – `(True, None)` an Schultagen, sonst `(False, Grund)` („Wochenende“, „Kein Unterrichtstag“ bzw. Ferienname).
- Funktion `day_kind` (`schulmanager/calendar_utils.py:199`) – `unterricht` | `kein_unterrichtstag` | `ferien` | `feiertag` (Ferienart `ferien` → ferien, sonst
- Funktion `school_days` (`schulmanager/calendar_utils.py:212`) – Alle Schultage im Bereich `[date_from, date_to]` (inklusive), mit `cls` die der Klasse.
- Funktion `holiday_week` (`schulmanager/calendar_utils.py:230`) – `(Ferienwoche, Name)`: alle Unterrichtstage (Klasse bzw. Schulöffnungstage) der Woche sind frei.
- Funktion `week_info` (`schulmanager/calendar_utils.py:246`) – WeekInfo (Vertrag §15.3) der Woche von `d`; Bezug Klasse (Unterrichtstage) bzw. Schule.
- Funktion `day_info` (`schulmanager/calendar_utils.py:261`) – Spaltenkopf eines Tages (`DayInfo`).
- Funktion `monday_of_week_no` (`schulmanager/calendar_utils.py:268`) – Montag der laufenden Woche `no` im Schuljahr von `today` (Standard: heute).
- Funktion `school_year_info` (`schulmanager/calendar_utils.py:274`) – `GET /calendar/school-year`: alle Wochen 1 … Y des Schuljahres von `d` (Standard: heute).
- Funktion `year_warnings` (`schulmanager/calendar_utils.py:299`) – Hinweise zur Wochenzählung (Texte §15.5).
- Funktion `period_time` (`schulmanager/calendar_utils.py:311`) – Beginn der Stunde `period` (0-basiert) als `HH:MM` oder `""`.
- Funktion `period_label` (`schulmanager/calendar_utils.py:318`) – Anzeige-Label einer Stunde: 0 -> `"1."`.
- Funktion `break_time` (`schulmanager/calendar_utils.py:323`) – Beginn einer Pause (`HH:MM`), abgeleitet aus dem Beginn der Folgestunde minus Pausenlänge.

## Hängt ab von

- [[Modul models]] – `models`

## Wird genutzt von

- [[Modul channels]]
- [[Modul duties]]
- [[Modul exams]]
- [[Modul integrations]] – `ical`, `schulmanager_online`, `untis_gpu`
- [[Modul legacy]]
- [[Modul planning]]
- [[Modul scheduler]]
- [[Modul student_self]]
- [[Modul substitution]]
- [[Modul teacher_profile]]
- [[Modul timetable]]
- [[Modul weeks]]
- [[Routen features_absence_stats]]
- [[Routen features_calendar]]
- [[Routen features_channels]]
- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_data]]
- [[Routen features_exchange]]
- [[Routen features_register]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]
- [[Routen features_substitutions]]
- [[Routen features_teacher_profile]]
- [[Routen features_timetable]]
- [[Server makeups]]
- [[Server notify]]

## Tests

`tests/test_classes.py`, `tests/test_exams.py`, `tests/test_forms.py`, `tests/test_grades.py`, `tests/test_makeups.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_student_self.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`, `tests/test_weeks.py`, `tests/test_weeks_api.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
