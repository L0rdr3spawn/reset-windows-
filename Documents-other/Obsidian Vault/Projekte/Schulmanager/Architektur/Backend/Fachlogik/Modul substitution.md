---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/substitution.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul substitution

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 1779 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Die **Vertretungs-Engine**: berechnet aus regulärem Plan, Abwesenheiten (Lehrkraft, Klasse, Raum, Einzelstunde) und Overrides den Tagesplan (`compute_day_plan` → `DayPlan` mit `Entry`-Arten Vertretung, Betreuung, Entfall, Verlegung, Raumänderung, Aufsicht, Klausur …). Grundregel: Ausfall nur an den Rändern des Schultags, Lücken in der Mitte werden zuerst durch Verlegung geschlossen, sonst Vertretung. `rank_candidates` bewertet Vertretungen (fachlich qualifiziert, Springstunde, faire Verteilung, Wegezeit). Rein funktional und deshalb im Server gecacht ([[Routen features_common]] `day_plan`).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/substitution.py` | 1779 | Vertretungsplan-Engine (Live-Umplanung bei Abwesenheiten). |

## Wichtige Funktionen und Klassen

- Funktion `split_lesson_ref` (`schulmanager/substitution.py:67`) – Referenz einer `lesson`-Abwesenheit → `(course_id, part)`.
- Klasse `DayPlan` (`schulmanager/substitution.py:84`) – Vertretungsplan eines Tages (Format siehe ARCHITECTURE.md §4).
  - Methoden: `to_dict`:103, `from_dict`:116, `substitution_counts`:127
- Funktion `absence_cases` (`schulmanager/substitution.py:136`) – Vertretungsfälle je ursprünglicher Lehrkraft: vertretene, betreute oder entfallene eigene Stunden und
- Funktion `compute_day_plan` (`schulmanager/substitution.py:1411`) – Vertretungsplan für `day`.
- Funktion `week_history` (`schulmanager/substitution.py:1429`) – Vertretungszählung Montag..Vortag der Woche von `day` (faire Historie für Einzeltage).
- Funktion `compute_range` (`schulmanager/substitution.py:1441`) – Pläne für alle Tage (Mo–So) im Bereich, inkl. Ferientage und Tage ohne Unterricht (`holiday` gesetzt,
- Funktion `rank_candidates` (`schulmanager/substitution.py:1473`) – Kandidaten für eine Vertretung, beste zuerst.
- Funktion `effective_day` (`schulmanager/substitution.py:1510`) – Tagesansicht (Klasse/Lehrkraft/Raum/Schüler) inkl. aller Änderungen des Plans.
- Funktion `teacher_stats` (`schulmanager/substitution.py:1712`) – Vertretungs-/Entfall-/Aufsichtsstatistik je Lehrkraft im Zeitraum.

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul duties]] – `duties` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_data]]
- [[Routen features_substitutions]]

## Tests

`tests/test_lesson_absence.py`, `tests/test_substitution.py`, `tests/test_substitution_demo.py`, `tests/test_substitution_rooms.py`, `tests/test_weeks.py`, `tests/test_weeks_r2.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
