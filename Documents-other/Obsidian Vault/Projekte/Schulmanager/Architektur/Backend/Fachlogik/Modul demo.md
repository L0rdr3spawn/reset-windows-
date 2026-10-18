---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/demo.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul demo

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 316 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

`build_demo()` erzeugt eine realistische, vollständig erfundene Beispielschule (~2600 Schüler, 98 Klassen, ~170 Lehrkräfte, 2 Standorte, Rhythmusklassen, Oberstufe mit Schienen). Danach sind `assign_teachers` und der Generator nötig. Die Konten dazu legt [[Server betrieb]] (`demo_loader`) an.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/demo.py` | 316 | Erzeugt eine realistische Beispielschule (~2600 Schüler, ~170 Lehrkräfte, 2 Standorte). |

## Wichtige Funktionen und Klassen

- Funktion `build_demo` (`schulmanager/demo.py:86`)

## Hängt ab von

- [[Modul models]] – `models`
- [[Modul planning]] – `planning` *(nur zur Laufzeit importiert)*
- [[Modul teacher_profile]] – `teacher_profile` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Server betrieb]] – `demo_loader`

## Tests

`tests/test_core.py`, `tests/test_integrations.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_substitution_demo.py`, `tests/test_weeks.py`, `tests/test_weeks_solver.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
