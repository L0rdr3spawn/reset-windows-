---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/scheduler.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul scheduler

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 1086 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Der **Stundenplan-Generator**: Wochenvarianten bilden (Wochen mit gleichen Bedingungen werden zusammengefasst, siehe [[Modul weeks]]), Blöcke (Einzel-/Doppelstunden) aus Kursen erzeugen, nach Schwierigkeit sortiert gierig in den besten gültigen Slot setzen, nicht platzierbare Blöcke durch Verdrängen reparieren und schließlich per Simulated Annealing optimieren (Hohlstunden, Springstunden, späte Hauptfächer, Standortwechsel; Gewichte `Weights`). Harte Regeln: keine Doppelbelegung von Klasse/Lehrkraft/Raum, Sperrzeiten, Unterrichtstage, Tageslimits, Wegezeit zwischen Standorten. Reine Rechenlogik ohne Datenbank; verändert das `School`-Objekt nicht, sondern liefert ein `ScheduleResult`. CPU-lastig – läuft deshalb als Hintergrundprozess über [[Server jobs]]; `generate_best_of` nutzt mehrere Kerne. **Hinweis:** Im Arbeitsstand verweist die Datei noch auf entfernte Zyklus-Funktionen von `weeks` (siehe [[Abhängigkeiten]], „Offene Umbauten“).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/scheduler.py` | 1086 | Stundenplan-Generator. |

## Wichtige Funktionen und Klassen

- Klasse `Block` (`schulmanager/scheduler.py:47`)
  - Methoden: `placed`:59
- Klasse `ScheduleResult` (`schulmanager/scheduler.py:79`)
- Klasse `Scheduler` (`schulmanager/scheduler.py:86`)
  - Methoden: `variants_of_members`:135, `slot`:275, `check`:314, `place`:424, `remove`:439, `class_day_cost`:457, `teacher_day_cost`:487, `block_cost`:516, `course_cost`:530, `total_cost`:563, `move_delta`:572, `best_slot`:601
- Funktion `generate` (`schulmanager/scheduler.py:1043`) – Plan erzeugen (`iterations` = feste Zahl an Optimierungsschritten, reproduzierbar).
- Funktion `generate_best_of` (`schulmanager/scheduler.py:1057`) – Startet mehrere Generatorläufe mit verschiedenen Seeds parallel (je CPU-Kern einen)

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Server betrieb]] – `demo_loader`
- [[Server jobs]]

## Tests

`tests/test_core.py`, `tests/test_integrations.py`, `tests/test_server_features.py`, `tests/test_substitution_demo.py`, `tests/test_teacher_profile.py`, `tests/test_weeks_solver.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
