---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/models.py"
stand: 2026-10-12 21:40
generator: schulmanager-regen
---

# Modul models

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 564 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Das **Planungsdokument**: ein einziges `School`-Objekt (Dataclasses, verlustfrei nach/aus JSON) hält Stammdaten (`Site`, `Subject`, `Teacher`, `Room`, `SchoolClass`, `Student`), Stundentafeln (`Curriculum`), Kurse (`Course`, `CoursePart`), Stunden (`Lesson`), Abwesenheiten, Overrides, Ferien (`Holiday`, mit Quelle für den automatischen Import), Aufsichten, Klausuren, Sperrregeln (`TimeRule`) und die Einstellungen (`Settings`, `Weights`, `SubstitutionPolicy`, `holiday_import`). `COLLECTIONS` ordnet Sammlungsnamen den Klassen zu (Grundlage des generischen CRUD in [[Routen features_data]]). Wochen folgen dem **52-Wochen-System**: laufende Wochen 1 … 52/53, Angaben als `weeks` (ausgewählte Wochen) oder `rhythm` (`every`, `from_week`, `to_week`), beides leer = jede Woche; kein Schul-Wochenzyklus, keine Wochenbuchstaben. Tag 0 = Montag, Stunde 0 = 1. Stunde. Ältere Dokumente rechnet [[Modul legacy]] beim Laden um. Neue Felder brauchen Standardwerte, damit alte Versionen in `school_versions` ladbar bleiben.

Das Dokument liegt **nicht** in einzelnen SQL-Tabellen, sondern als Ganzes versioniert im [[Server store]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/models.py` | 564 | Datenmodell des Schulmanagers. |

## Wichtige Funktionen und Klassen

- Klasse `Model` (`schulmanager/models.py:32`)
  - Methoden: `to_dict`:33, `from_dict`:37
- Klasse `Site` (`schulmanager/models.py:42`) – Schulstandort (z. B. Hauptgebäude, Außenstelle).
- Klasse `TimeRule` (`schulmanager/models.py:49`) – Regel, wann eine Klasse/ein Lehrer NICHT verfügbar ist.
  - Methoden: `matches`:70
- Funktion `rhythm_active` (`schulmanager/models.py:78`) – Ist ein Rhythmus `{"every", "from_week", "to_week"}` in der laufenden Woche `real_week` aktiv?
- Funktion `spec_active` (`schulmanager/models.py:93`) – Gilt eine Wochenangabe (`weeks` oder `rhythm`; beides leer = jede Woche) in der laufenden Woche
- Klasse `Subject` (`schulmanager/models.py:107`)
- Klasse `Teacher` (`schulmanager/models.py:117`)
  - Methoden: `from_dict`:143
- Klasse `Room` (`schulmanager/models.py:151`)
- Klasse `SchoolClass` (`schulmanager/models.py:160`)
  - Methoden: `from_dict`:174
- Klasse `Student` (`schulmanager/models.py:181`)
- Klasse `CurriculumEntry` (`schulmanager/models.py:190`) – Eine Zeile der Stundentafel: Fach X mit N Wochenstunden.
- Klasse `Curriculum` (`schulmanager/models.py:198`) – Stundentafel für einen Jahrgang (oder eine einzelne Klasse).
  - Methoden: `from_dict`:207
- Klasse `CoursePart` (`schulmanager/models.py:214`) – Ein paralleler Teil einer (ggf. gekoppelten) Unterrichtseinheit.
- Klasse `Course` (`schulmanager/models.py:225`) – Unterricht, der `hours` Mal pro Woche stattfindet.
  - Methoden: `from_dict`:243
- Klasse `Lesson` (`schulmanager/models.py:250`) – Ein platzierter Block im Stundenplan.
- Klasse `Absence` (`schulmanager/models.py:264`) – Abwesenheit von Lehrer, Klasse oder Raum für einen Datumsbereich.
  - Methoden: `covers`:281
- Klasse `Override` (`schulmanager/models.py:288`) – Manuelle Entscheidung im Vertretungsplan für einen Tag.
- Klasse `Holiday` (`schulmanager/models.py:302`) – Ferien / Feiertag / beweglicher Ferientag – an diesen Tagen kein Unterricht.
  - Methoden: `from_dict`:317, `covers`:323
- Klasse `SupervisionArea` (`schulmanager/models.py:328`) – Aufsichtsbereich für Pausenaufsichten (z. B. Schulhof, Mensa).
- Klasse `Duty` (`schulmanager/models.py:337`) – Pausenaufsicht: Lehrer `teacher` beaufsichtigt `area` in Pause `break_index`.
- Klasse `Event` (`schulmanager/models.py:349`) – Termin im Schulkalender (erscheint im Stundenplan der Betroffenen, auch am Wochenende).
  - Methoden: `covers`:367, `for_class`:370
- Klasse `Exam` (`schulmanager/models.py:377`) – Klassenarbeit / Klausur, die in einer Unterrichtsstunde geschrieben wird.
- Klasse `Weights` (`schulmanager/models.py:391`) – Gewichte der Optimierung (höher = wichtiger).
- Klasse `SubstitutionPolicy` (`schulmanager/models.py:406`) – Regeln für die Vertretungsplanung.
- Klasse `Settings` (`schulmanager/models.py:416`)
  - Methoden: `from_dict`:471, `block_start_ok`:479
- Klasse `School` (`schulmanager/models.py:517`)
  - Methoden: `to_dict`:540, `from_dict`:551, `index`:562

## Hängt ab von

- [[Modul legacy]] – `legacy` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Modul autoplan]]
- [[Modul calendar_utils]]
- [[Modul channels]]
- [[Modul demo]]
- [[Modul duties]]
- [[Modul exams]]
- [[Modul integrations]] – `_common`, `csv_io`, `ical`, `schulmanager_online`, `untis_gpu`
- [[Modul legacy]]
- [[Modul messaging]]
- [[Modul planning]]
- [[Modul scheduler]]
- [[Modul student_self]]
- [[Modul substitution]]
- [[Modul teacher_profile]]
- [[Modul timetable]]
- [[Modul weeks]]
- [[Routen features_class_info]]
- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_data]]
- [[Routen features_exams]]
- [[Routen features_exchange]]
- [[Routen features_forms]]
- [[Routen features_substitutions]]
- [[Routen features_teacher_profile]]
- [[Routen history]]
- [[Server autoplan]]
- [[Server betrieb]] – `demo_loader`
- [[Server holiday_import]]
- [[Server jobs]]
- [[Server konten und anmeldung]] – `accounts`
- [[Server permissions]]
- [[Server store]]

## Tests

`tests/test_autoplan.py`, `tests/test_channels_rooms.py`, `tests/test_class_room_info.py`, `tests/test_classes.py`, `tests/test_core.py`, `tests/test_curricula.py`, `tests/test_duties.py`, `tests/test_exams.py`, `tests/test_holiday_import.py`, `tests/test_integrations.py`, `tests/test_lesson_absence.py`, `tests/test_makeups.py` …

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
