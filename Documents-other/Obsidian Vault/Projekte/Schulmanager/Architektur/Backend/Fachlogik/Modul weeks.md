---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/weeks.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul weeks

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 414 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Wochenangaben im 52-Wochen-System und die zentrale Aktiv-Logik: Muster `weeks` (Liste laufender Wochen) oder `rhythm` (`every`/`from_week`/`to_week`) mit Prüfung (`spec_errors`, `rule_errors`) und deutschen Beschreibungstexten (`describe_spec`). `lesson_active_on`, `rule_active_on`, `duty_active_on` und `ActiveIndex` entscheiden, ob ein Block, eine Regel oder eine Aufsicht an einem Datum stattfindet. `Horizon` (reale Wochen 1 … Y) und `group_weeks`/`PlanWeeks` fassen Wochen mit gleicher Signatur zu Varianten zusammen (Generator, Bericht, Aufsichten). Alte Zyklusfunktionen sind entfernt, Altdokumente rechnet [[Modul legacy]] um.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/weeks.py` | 414 | Wochenangaben im 52-Wochen-System und die zentrale Aktiv-Logik. |

## Wichtige Funktionen und Klassen

- Funktion `errors` (`schulmanager/weeks.py:36`) – Prüft eine Wochenliste: nur ganze Zahlen 1 … 53 (laufende Wochen), höchstens 53 Einträge.
- Funktion `normalize` (`schulmanager/weeks.py:47`) – Sortiert, eindeutig, nur 1 … 53; alle Wochen → `[]`.
- Funktion `rhythm_errors` (`schulmanager/weeks.py:54`) – Prüft `{"every": 1…53, "from_week": 1…53, "to_week": 0…53}` (`to_week` 0 = offen).
- Funktion `normalize_rhythm` (`schulmanager/weeks.py:73`) – Gespeicherte Form `{"every", "from_week", "to_week"}` (`None` bleibt `None`).
- Funktion `describe_rhythm` (`schulmanager/weeks.py:84`) – „jede 2. Woche ab Woche 10“, „… bis Woche 30“, „jede Woche ab Woche 5“.
- Funktion `describe` (`schulmanager/weeks.py:115`) – Kürzester Text einer Wochenliste: „jede Woche“, „Woche 1–4, 9“, „jede 3. Woche ab Woche 2“, „… bis Woche 29“.
- Funktion `spec_from_weeks` (`schulmanager/weeks.py:129`) – Laufende Wochen → `(weeks, rhythm)`: alle `total` Wochen → leer; mindestens drei Wochen mit gleichem Abstand
- Funktion `describe_spec` (`schulmanager/weeks.py:143`) – Text einer Wochenangabe (Rhythmus hat Vorrang, sonst Wochenliste).
- Funktion `spec_of` (`schulmanager/weeks.py:150`) – `(weeks, rhythm)` eines Objekts oder Wörterbuchs.
- Funktion `describe_rule_weeks` (`schulmanager/weeks.py:157`) – Wochentext einer Regel/Aufsicht/eines Kurses (Rhythmus oder Wochenliste).
- Funktion `spec_errors` (`schulmanager/weeks.py:163`) – Prüft eine Wochenangabe: Liste 1 … 53 oder Rhythmus (nie beides).
- Funktion `parse_weeks_input` (`schulmanager/weeks.py:173`) – Ältere Anfrage-Felder in einem Request-Dict auf `weeks`/`rhythm` abbilden (in place). Liefert Fehlertexte.
- Funktion `real_week` (`schulmanager/weeks.py:194`) – Laufende Woche am Datum `d` (Grundlage aller Wochenangaben).
- Funktion `lesson_active_in` (`schulmanager/weeks.py:199`) – Liegt der Block in der laufenden Woche `week`? (Stunde ∩ Kurs; unbekannte Woche = ja)
- Klasse `ActiveIndex` (`schulmanager/weeks.py:206`) – Zwischenspeicher für viele Aktiv-Abfragen auf einem Dokument (laufende Woche je Montag).
  - Methoden: `real`:215, `active_on`:222, `in_week`:227
- Funktion `lesson_active_on` (`schulmanager/weeks.py:232`) – Findet der Block am Datum `d` statt (Wochentag und laufende Woche)?
- Funktion `rule_active_on` (`schulmanager/weeks.py:239`) – Gilt die Regel/Aufsicht (Wochen bzw. Rhythmus und Tage) am Datum `d`?
- Funktion `duty_active_on` (`schulmanager/weeks.py:250`) – Findet die Aufsicht am Datum `d` statt (Wochentag, Wochen bzw. Rhythmus)?
- Klasse `Horizon` (`schulmanager/weeks.py:259`) – Reale Wochen 1 … Y des Schuljahres von `today`.
  - Methoden: `members`:280, `spec_members`:287, `lesson_members`:292, `describe`:299, `to_spec`:314
- Funktion `group_weeks` (`schulmanager/weeks.py:319`) – Fasst Wochen 0 … size−1 mit gleicher Signatur (Zugehörigkeit zu jeder Menge) zusammen.
- Funktion `rule_errors` (`schulmanager/weeks.py:331`) – Prüft eine Sperr-/Wunschregel: Wochen oder Rhythmus (nie beides), Tage 0–6, Stunden im Raster, nicht
- Klasse `PlanWeeks` (`schulmanager/weeks.py:347`) – Wochenvarianten eines Dokuments für Belegung, Verschieben und Bericht.
  - Methoden: `lesson_members`:388, `lesson_groups`:394, `spec_groups`:402, `real_week`:406, `label`:409

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`

## Wird genutzt von

- [[Modul autoplan]]
- [[Modul channels]]
- [[Modul duties]]
- [[Modul exams]]
- [[Modul integrations]] – `csv_io`, `ical`, `untis_gpu`
- [[Modul planning]]
- [[Modul scheduler]]
- [[Modul substitution]]
- [[Modul teacher_profile]]
- [[Modul timetable]]
- [[Routen features_calendar]]
- [[Routen features_classes]]
- [[Routen features_data]]
- [[Routen features_substitutions]]
- [[Server jobs]]

## Tests

`tests/test_core.py`, `tests/test_duties.py`, `tests/test_grades.py`, `tests/test_integrations.py`, `tests/test_server_features.py`, `tests/test_substitution_demo.py`, `tests/test_substitution_rooms.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`, `tests/test_weeks.py`, `tests/test_weeks_api.py`, `tests/test_weeks_r2.py` …

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
