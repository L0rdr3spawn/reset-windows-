---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/exams.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul exams

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 210 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Klassenarbeiten und Klausuren: Konfliktprüfung (`check_exam`) und Abfragen (`exams_for`). Klausuren werden von [[Modul substitution]] nie ohne Warnung verlegt oder gestrichen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/exams.py` | 210 | Klassenarbeiten / Klausuren: Konfliktprüfung und Abfragen. |

## Wichtige Funktionen und Klassen

- Funktion `lessons_active_on` (`schulmanager/exams.py:30`) – Alle Blöcke, die am Datum stattfinden (zentrale Aktiv-Logik) – für Belegungsprüfungen (Nachschreibtermine).
- Funktion `check_exam` (`schulmanager/exams.py:58`) – Prüft eine (neue oder geänderte) Klausur. Leere Liste = in Ordnung.
- Funktion `exams_for` (`schulmanager/exams.py:164`) – Klausuren im Zeitraum für `kind` ∈ `class|teacher|room|student|course|all`.

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Routen features_exams]]
- [[Server makeups]]

## Tests

`tests/test_exams.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
