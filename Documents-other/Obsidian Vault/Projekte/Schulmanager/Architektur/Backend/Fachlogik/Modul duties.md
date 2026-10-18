---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/duties.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul duties

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 307 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Pausenaufsichten: `generate_duties` verteilt Aufsichten fair (bevorzugt Lehrkräfte mit Unterricht direkt vor/nach der Pause am Standort), `duty_replacements` ersetzt Aufsichten abwesender Lehrkräfte. Ergebnis fließt als `aufsicht`-Einträge in den Tagesplan von [[Modul substitution]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/duties.py` | 307 | Pausenaufsichten: faire Planung und Vertretung bei Abwesenheit. |

## Wichtige Funktionen und Klassen

- Funktion `duty_variants` (`schulmanager/duties.py:48`) – Gruppen realer Wochen mit gleichen Bedingungen für Aufsichten (Wochenvarianten): Wochen mit denselben
- Funktion `generate_duties` (`schulmanager/duties.py:68`) – Erzeugt einen fairen Aufsichtsplan (ersetzt `school.duties` NICHT – Aufrufer setzt ihn).
- Funktion `duty_load` (`schulmanager/duties.py:177`) – Aufsichten je Lehrkraft pro Woche (über die Wochen des Schuljahres gemittelt).
- Funktion `active_duties` (`schulmanager/duties.py:192`) – Aufsichten, die am Datum `day` stattfinden (Wochentag, Wochen bzw. Rhythmus).
- Funktion `duty_replacements` (`schulmanager/duties.py:198`) – Ersatz für Pausenaufsichten abwesender (oder nicht eingeteilter) Lehrkräfte.

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Modul substitution]]
- [[Routen features_planning]]
- [[Server betrieb]] – `demo_loader`

## Tests

`tests/test_duties.py`, `tests/test_server_features.py`, `tests/test_substitution_demo.py`, `tests/test_weeks_solver.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
