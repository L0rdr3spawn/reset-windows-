---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/jobs.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server jobs

> Server-Kern · 1 Datei(en) · 686 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Hintergrund-Jobs für die Generierung: der `JobManager` startet den Generator ([[Modul scheduler]]) in einem **eigenen Prozess**, meldet Fortschritt als `job`-Ereignis, verwaltet Abbruch und Übernahme (`apply`). Enthält die Neuplanungs-Logik für Lehrkräfte (`prepare_replan`, `merge_replan`: fremde Stunden samt Räumen fixieren). Ein laufender Job gleichzeitig, prozesslokal. Endpunkte: [[Routen features_planning]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/jobs.py` | 686 | Hintergrund-Jobs: Stundenplan-Generierung in einem eigenen Prozess. |

## Wichtige Funktionen und Klassen

- Klasse `JobError` (`schulmanager/server/jobs.py:46`) – Fehler beim Starten/Übernehmen eines Jobs (`status` = HTTP-Status).
- Funktion `replan_courses` (`schulmanager/server/jobs.py:157`) – Kurse, die bei der Neuplanung frei bleiben: Kurse der Lehrkraft (`scope="classes"`: zusätzlich alle
- Funktion `prepare_replan` (`schulmanager/server/jobs.py:167`) – Generator-Eingabe für die Neuplanung: alle Stunden außer denen der freien Kurse werden fixiert – samt
- Funktion `merge_replan` (`schulmanager/server/jobs.py:191`) – Führt das Generator-Ergebnis mit dem Ausgangsplan zusammen (siehe Moduldoku).
- Klasse `Job` (`schulmanager/server/jobs.py:292`)
  - Methoden: `public`:313, `event`:334
- Klasse `JobManager` (`schulmanager/server/jobs.py:339`) – Verwaltet Generator-Jobs (prozesslokal, ein laufender Job gleichzeitig).
  - Methoden: `get`:348, `list`:352, `running`:356, `start_generate`:364, `cancel`:490, `apply`:578, `shutdown`:651, `running_count`:664
- Funktion `shutdown` (`schulmanager/server/jobs.py:679`)
- Funktion `running_count` (`schulmanager/server/jobs.py:683`) – Für `/metrics` (`schulmanager_jobs_running`).

## Hängt ab von

- [[Modul models]] – `models` *(nur zur Laufzeit importiert)*
- [[Modul scheduler]] – `scheduler` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Server autoplan]] – `autoplan` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_planning]]
- [[Server autoplan]]

## Tests

`tests/test_server_features.py`, `tests/test_teacher_profile.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
