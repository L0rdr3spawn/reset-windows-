---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/autoplan.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul autoplan

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 343 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Reine Logik des **Auto-Planers**: `find_problems` erkennt Fehler im regulären Plan (Doppelbelegung, gesperrte Lehrkraft, fehlende Wochenstunden …), `prepare_repair` repariert, was ohne Verschieben geht, und bestimmt die Kurse, die der Generator neu planen muss. Der Hintergrunddienst dazu ist [[Server autoplan]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/autoplan.py` | 343 | Automatische Neuplanung des regulären Stundenplans (Auto-Planer, reine Logik). |

## Wichtige Funktionen und Klassen

- Klasse `Problems` (`schulmanager/autoplan.py:38`) – Ergebnis von ``.
  - Methoden: `empty`:48, `count`:51, `courses`:56, `signature`:61, `summary`:69
- Funktion `find_problems` (`schulmanager/autoplan.py:100`) – Prüft den regulären Stundenplan gegen die aktuellen Stammdaten (siehe Moduldoku).
- Funktion `repair_rooms` (`schulmanager/autoplan.py:212`) – Wählt für die Stunden `lesson_ids` freie Räume des richtigen Typs zur **selben Zeit** (verändert
- Funktion `expand_courses` (`schulmanager/autoplan.py:295`) – Zweite Stufe, wenn die betroffenen Kurse allein nicht passen: zusätzlich alle Kurse der beteiligten Klassen
- Klasse `RepairPlan` (`schulmanager/autoplan.py:311`) – Ergebnis von ``.
  - Methoden: `free_courses`:320, `changed`:324
- Funktion `prepare_repair` (`schulmanager/autoplan.py:329`) – Arbeitskopie mit allen Reparaturen, die ohne Verschieben gehen (siehe Moduldoku).

## Hängt ab von

- [[Modul models]] – `models`
- [[Modul timetable]] – `timetable`
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Routen features_planning]]
- [[Server autoplan]]

## Tests

`tests/test_autoplan.py`, `tests/test_class_curriculum.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
