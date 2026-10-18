---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/timetable.py"
stand: 2026-10-12 22:48
generator: schulmanager-regen
---

# Modul timetable

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 652 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Ansichten und Prüfungen auf dem regulären Plan: `timetable_view` (Klasse, Lehrkraft, Raum, Schüler), `lesson_info`, manuelles Verschieben (`check_move`, `move_lesson`, `move_options`) und der Qualitätsbericht `validate_school`. Die harten Regeln hier müssen deckungsgleich zu [[Modul scheduler]] bleiben (`Scheduler.check` und `timetable._evaluate`).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/timetable.py` | 652 | Stundenplan-Ansichten, manuelles Verschieben und Qualitätsbericht. |

## Wichtige Funktionen und Klassen

- Funktion `weeks_text` (`schulmanager/timetable.py:19`) – Wochentext eines Blocks: Wochenangabe der Stunde und/oder des Kurses, sonst „jede Woche“.
- Funktion `course_days` (`schulmanager/timetable.py:25`) – Tage, an denen alle Klassen des Kurses Unterricht haben.
- Funktion `lesson_site` (`schulmanager/timetable.py:34`)
- Funktion `student_parts` (`schulmanager/timetable.py:47`) – Welche Kursteile besucht ein Schüler? `{course_id: [part_index, ...]}`.
- Funktion `lesson_info` (`schulmanager/timetable.py:78`) – Zelle für Ansichten (Format siehe ARCHITECTURE.md §3).
- Funktion `visible_days` (`schulmanager/timetable.py:130`) – Spaltenzahl ab Montag (V10/E2): 7 bzw. 1 + max({4} ∪ Unterrichtstage ∪ Tage mit Zellen/Klausuren).
- Funktion `timetable_view` (`schulmanager/timetable.py:139`) – Wochenraster für Klasse, Lehrer, Raum oder Schüler.
- Funktion `check_move` (`schulmanager/timetable.py:396`)
- Funktion `move_lesson` (`schulmanager/timetable.py:408`) – Verschiebt eine Stunde (Räume werden bei Bedarf getauscht). ValueError bei Konflikten.
- Funktion `move_options` (`schulmanager/timetable.py:420`)
- Funktion `validate_school` (`schulmanager/timetable.py:435`) – Qualitätsbericht: fehlende Stunden, Doppelbelegungen, Hohl-/Springstunden …

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Modul autoplan]]
- [[Modul exams]]
- [[Modul integrations]] – `ical`
- [[Modul substitution]]
- [[Routen features_class_info]]
- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_planning]]
- [[Routen features_timetable]]
- [[Server autoplan]]
- [[Server betrieb]] – `demo_loader`
- [[Server jobs]]

## Tests

`tests/test_core.py`, `tests/test_curricula.py`, `tests/test_report_details.py`, `tests/test_student_absence_access.py`, `tests/test_teacher_profile.py`, `tests/test_weeks.py`, `tests/test_weeks_solver.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
