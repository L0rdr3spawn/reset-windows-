---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/planning.py"
stand: 2026-10-12 22:48
generator: schulmanager-regen
---

# Modul planning

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 523 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Vorbereitung der Planung: aus Stundentafeln (`Curriculum`) werden Kurse erzeugt (`build_courses_from_curricula`), Lehrkräfte automatisch zugewiesen (`assign_teachers`) und Kapazitätswarnungen berechnet (`capacity_warnings`). Löst auch den Konflikt, wenn für eine Klasse mehrere Stundentafeln gelten. Eingang für [[Modul scheduler]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/planning.py` | 523 | Vorbereitung der Planung: Stundentafel -> Kurse, Lehrerzuweisung. |

## Wichtige Funktionen und Klassen

- Funktion `curriculum_for_class` (`schulmanager/planning.py:28`) – Gültige Stundentafel der Klasse (Klasse vor Jahrgang). Bei einem Konflikt die erste – Aufrufer, die
- Funktion `resolve_curricula` (`schulmanager/planning.py:36`) – Je Klasse `{"curriculum": id|None, "source": "class"|"grade"|None, "candidates": [ids],
- Funktion `curriculum_conflicts` (`schulmanager/planning.py:48`) – Überschneidungen gruppiert: `[{"curricula": [ids], "classes": [ids], "source"}]` (optional nur
- Funktion `curriculum_overview` (`schulmanager/planning.py:58`) – Für den Editor: je Tafel die Klassen, für die sie gilt (bzw. im Konflikt steht), und Klassen ohne Tafel.
- Funktion `changed_fields` (`schulmanager/planning.py:86`) – Welche `PINNABLE`-Felder unterscheiden sich (Kurs-Editor → `Course.pinned`).
- Funktion `rebuild_courses` (`schulmanager/planning.py:103`) – Erzeugt für jede Klasse Kurse aus ihrer Stundentafel und liefert einen Bericht.
- Funktion `build_courses_from_curricula` (`schulmanager/planning.py:234`) – Kurse aus den Stundentafeln erzeugen (siehe `rebuild_courses`); gibt nur die Warnungen zurück.
- Funktion `teacher_course_capacity` (`schulmanager/planning.py:263`) – Kleinste Anzahl gemeinsamer freier Stunden (Klassen des Kurses ∩ Verfügbarkeit der Lehrkraft) je
- Funktion `assign_teachers` (`schulmanager/planning.py:294`) – Weist Kursteilen ohne Lehrer eine qualifizierte Lehrkraft zu.
- Funktion `capacity_warnings` (`schulmanager/planning.py:389`) – Prüft, ob Klassen genug verfügbare Stunden für ihre Kurse haben.
- Funktion `assign_class_teachers` (`schulmanager/planning.py:413`) – Setzt für Klassen ohne Klassenleitung eine Lehrkraft, die dort die meisten Stunden unterrichtet.
- Funktion `class_curriculum_id` (`schulmanager/planning.py:452`)
- Funktion `set_class_curriculum` (`schulmanager/planning.py:456`) – Legt die eigene Stundentafel einer Klasse fest (Vorrang vor der Jahrgangs-Stundentafel) und erzeugt die
- Funktion `rebuild_class_courses` (`schulmanager/planning.py:476`) – Erzeugt die Stundentafel-Kurse einer Klasse neu (wie ``, aber nur für diese

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul weeks]] – `weeks` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Modul demo]]
- [[Routen features_classes]]
- [[Routen features_data]]
- [[Routen features_exchange]]
- [[Routen features_planning]]
- [[Server betrieb]] – `demo_loader`

## Tests

`tests/test_class_curriculum.py`, `tests/test_core.py`, `tests/test_curricula.py`, `tests/test_integrations.py`, `tests/test_report_details.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_substitution_demo.py`, `tests/test_teacher_profile.py`, `tests/test_weeks_solver.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
