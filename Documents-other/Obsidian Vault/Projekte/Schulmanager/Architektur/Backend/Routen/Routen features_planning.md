---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_planning.py"
stand: 2026-10-12 22:51
generator: schulmanager-regen
---

# Routen features_planning

> API-Routen · 1 Datei(en) · 300 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Planung: Kurse aus Stundentafeln, Lehrerzuweisung, Qualitätsbericht, Stundenplan-Generierung (Hintergrund-Job), Neuplanung für eine Lehrkraft und Pausenaufsichten.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_planning.py` | 300 | Planung: Kurse aus Stundentafeln, Lehrerzuweisung, Qualitätsbericht, |

## Endpunkte (15)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| POST | `/api/v1/planning/courses-from-curricula` | `courses_from_curricula` (`features_planning.py:69`) | timetable.edit | [[Seite PlanningPage]] |
| GET | `/api/v1/planning/curricula/overview` | `curricula_overview` (`features_planning.py:89`) | (angemeldet) | – |
| POST | `/api/v1/planning/assign-teachers` | `assign_teachers` (`features_planning.py:105`) | timetable.edit | [[Seite PlanningPage]] |
| GET | `/api/v1/planning/report` | `report` (`features_planning.py:119`) | (angemeldet) | [[Seite DashboardPage]], [[Seite PlanningPage]] |
| GET | `/api/v1/planning/report/details` | `report_details` (`features_planning.py:141`) | (angemeldet) | [[Seite PlanningPage]] |
| POST | `/api/v1/planning/generate` | `generate` (`features_planning.py:164`) | timetable.generate | [[Seite PlanningPage]] |
| POST | `/api/v1/planning/replan-teacher/{teacher_id}` | `replan_teacher` (`features_planning.py:183`) | timetable.generate | [[Feature teacher]] |
| GET | `/api/v1/planning/autoplan` | `autoplan_status` (`features_planning.py:226`) | (angemeldet) | [[Seite PlanningPage]] |
| POST | `/api/v1/planning/autoplan/run` | `autoplan_run` (`features_planning.py:233`) | timetable.generate | [[Seite PlanningPage]] |
| GET | `/api/v1/planning/jobs` | `list_jobs` (`features_planning.py:243`) | (angemeldet) | [[Feature teacher]] |
| GET | `/api/v1/planning/jobs/{job_id}` | `get_job` (`features_planning.py:250`) | (angemeldet) | [[Feature teacher]], [[Seite PlanningPage]] |
| POST | `/api/v1/planning/jobs/{job_id}/cancel` | `cancel_job` (`features_planning.py:264`) | timetable.generate | [[Feature teacher]], [[Seite PlanningPage]] |
| DELETE | `/api/v1/planning/jobs/{job_id}` | `delete_job` (`features_planning.py:273`) | timetable.generate | – |
| POST | `/api/v1/planning/jobs/{job_id}/apply` | `apply_job` (`features_planning.py:279`) | timetable.generate | [[Feature teacher]], [[Seite PlanningPage]] |
| POST | `/api/v1/duties/generate` | `generate_duties` (`features_planning.py:289`) | timetable.edit | [[Seite DutiesPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `GenerateIn` (`schulmanager/server/routes/features_planning.py:17`)
- Klasse `ReplanIn` (`schulmanager/server/routes/features_planning.py:24`)
- Klasse `CoursesFromCurriculaIn` (`schulmanager/server/routes/features_planning.py:41`)

## Hängt ab von

- [[Modul autoplan]] – `autoplan` *(nur zur Laufzeit importiert)*
- [[Modul duties]] – `duties` *(nur zur Laufzeit importiert)*
- [[Modul planning]] – `planning` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Server autoplan]] – `autoplan` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config` *(nur zur Laufzeit importiert)*
- [[Server deps]] – `deps`
- [[Server jobs]] – `jobs` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_autoplan.py`, `tests/test_class_curriculum.py`, `tests/test_curricula.py`, `tests/test_report_details.py`, `tests/test_server_features.py`, `tests/test_teacher_profile.py`, `tests/test_teacher_scope.py`, `tests/test_viewer_role.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
