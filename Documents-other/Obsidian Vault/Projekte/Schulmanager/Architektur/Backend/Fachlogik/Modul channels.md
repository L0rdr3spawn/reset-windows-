---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/channels.py"
stand: 2026-10-12 21:21
generator: schulmanager-regen
---

# Modul channels

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 917 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Kursräume – reine Logik über dem Planungsdokument: Kanäle je Kursteil, Klasse oder frei, Lehrende/Teilnehmende (über `timetable.student_parts`), Sichtbarkeit von Material und Aufgaben, Regeln für Eltern und Schulbegleitung. Die Persistenz (Material, Abgaben, Pinnwand) liegt in SQL-Tabellen, siehe [[Routen features_channels]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/channels.py` | 917 | Kursräume (ARCHITECTURE.md §9.4) – reine Logik über dem Planungsdokument (ohne Datenbank, ohne Serv… |

## Wichtige Funktionen und Klassen

- Funktion `now_utc` (`schulmanager/channels.py:61`) – Aktuelle Zeit (naive UTC). In Tests per `monkeypatch.setattr(channels, "now_utc", …)` ersetzbar.
- Funktion `local_to_utc` (`schulmanager/channels.py:66`) – Naive Ortszeit (Server-`TZ`) → naive UTC (zeitzonenbehaftete Werte werden direkt umgerechnet).
- Funktion `utc_to_local` (`schulmanager/channels.py:71`) – Naive UTC → naive Ortszeit (Server-`TZ`).
- Funktion `local_today` (`schulmanager/channels.py:78`) – Heutiges Datum in Ortszeit (aus ``).
- Funktion `parse_hhmm` (`schulmanager/channels.py:83`)
- Funktion `period_start_local` (`schulmanager/channels.py:93`) – Beginn der Stunde `period` (0-basiert) am `day` in Ortszeit (`None` ohne Zeitangabe).
- Funktion `period_end_hhmm` (`schulmanager/channels.py:101`) – Ende der Stunde `period` als `HH:MM` (Beginn + `period_minutes`).
- Funktion `lesson_release_utc` (`schulmanager/channels.py:111`) – Freigabezeitpunkt (UTC) für Material „zur Stunde“: Beginn der Stunde in Ortszeit.
- Funktion `course_ref` (`schulmanager/channels.py:118`)
- Funktion `parse_course_ref` (`schulmanager/channels.py:122`) – `"<kurs>#<teil>"` → `(kurs, teil)`; `None` bei ungültiger Schreibweise.
- Klasse `ChannelSpec` (`schulmanager/channels.py:133`) – Beschreibung eines automatischen Kanals (aus dem Planungsdokument berechnet).
  - Methoden: `to_dict`:148
- Klasse `SchoolIndex` (`schulmanager/channels.py:159`) – Abgeleitete Nachschlagetabellen eines Planungsdokuments (je `School`-Objekt einmal berechnet).
  - Methoden: `class_name`:203, `subject_name`:207, `teacher_name`:213
- Funktion `index_for` (`schulmanager/channels.py:224`) – `` des Dokuments (Ein-Platz-Cache – der Store ersetzt das Dokument bei jeder Änderung).
- Funktion `course_part_spec` (`schulmanager/channels.py:249`) – Kanal eines Kursteils, Titel z. B. „Deutsch 5a“, „Kath. Religion · Religion/PP 5a+5b“ oder
- Funktion `class_spec` (`schulmanager/channels.py:276`)
- Funktion `channel_spec` (`schulmanager/channels.py:292`) – Beschreibung eines Kurs-/Klassenkanals oder `None` (Kurs/Teil/Klasse existiert nicht mehr).
- Funktion `all_specs` (`schulmanager/channels.py:306`) – Alle automatischen Kanäle: Kursteile (aller Kurse mit Teilen) und Klassen.
- Funktion `student_course_parts` (`schulmanager/channels.py:323`) – Besuchte Teile eines Kurses (wie `timetable.student_parts` für genau einen Kurs, leer = nicht im Kurs).
- Funktion `channel_teacher_ids` (`schulmanager/channels.py:343`)
- Funktion `channel_student_ids` (`schulmanager/channels.py:348`) – Schüler-IDs (Planungsdokument) eines Kurs-/Klassenkanals.
- Funktion `is_channel_teacher` (`schulmanager/channels.py:369`)
- Funktion `is_channel_student` (`schulmanager/channels.py:373`)
- Funktion `teacher_specs` (`schulmanager/channels.py:389`) – Kanäle, in denen die Lehrkraft lehrt: ihre Kursteile und ihre Klassen (Unterricht oder Klassenleitung).
- Funktion `student_specs` (`schulmanager/channels.py:407`) – Kanäle einer Schülerin/eines Schülers: besuchte Kursteile und die eigene Klasse.
- Klasse `Visibility` (`schulmanager/channels.py:429`) – Sichtbarkeit eines Materials für Teilnehmende zum Zeitpunkt `now`.
- Funktion `item_visibility` (`schulmanager/channels.py:441`) – Sichtbarkeit für Teilnehmende. `release_override` = abweichender Stundenbeginn (Verlegung am Tag);
- Funktion `folder_states` (`schulmanager/channels.py:473`) – Wirksamer Zustand je Ordner für Teilnehmende (eigene Freigabe + alle übergeordneten Ordner).
- Funktion `hidden_folder_ids` (`schulmanager/channels.py:507`) – IDs aller Ordner, die selbst oder über einen übergeordneten Ordner verborgen sind.
- Funktion `folder_path_ids` (`schulmanager/channels.py:524`) – Pfad (Wurzel → Ordner) als ID-Liste; leer für die Wurzel/unbekannte Ordner.
- Funktion `descendant_folder_ids` (`schulmanager/channels.py:535`) – Alle Unterordner (rekursiv, ohne den Ordner selbst).
- Funktion `lesson_active_on` (`schulmanager/channels.py:552`) – Findet der Block am `day` statt (Wochentag + laufende Woche, ohne Ferien/Vertretungsplan)?
- Funktion `channel_class` (`schulmanager/channels.py:558`) – Bezugsklasse eines Kursraums für Unterrichtstage: Klassen-Kanal → die Klasse, Kurs-Kanal → erste Klasse des
- Funktion `day_has_changes` (`schulmanager/channels.py:569`) – Kann der Vertretungsplan an `day` Einträge haben (Abwesenheiten, Overrides, Klausuren)?
- Funktion `channel_lessons` (`schulmanager/channels.py:599`) – Unterrichtsblöcke eines Kanals mit den relevanten Kursteilen.
- Funktion `moved_period` (`schulmanager/channels.py:626`) – Neue Stunde, wenn der Block `lesson_id` (ab `period`) laut Tagesplan verlegt wurde.
- Funktion `lesson_key` (`schulmanager/channels.py:708`)
- Funktion `upcoming_lessons` (`schulmanager/channels.py:746`) – Kommende Unterrichtsblöcke eines Kanals ab `start` (einschließlich) für `days` Tage.
- Funktion `next_held_lesson` (`schulmanager/channels.py:786`) – Erste Stunde des Kanals nach (`after`, `after_period`), die stattfindet (nicht Entfall/schulfrei),
- Funktion `find_lesson` (`schulmanager/channels.py:805`) – Einen Block (Datum, Lesson, geplanter Beginn) eines Kanals prüfen und beschreiben (`None` = gibt es nicht).
- Funktion `clean_url` (`schulmanager/channels.py:822`) – Nur `http`/`https`-Adressen mit Host (keine `javascript:`/`data:`-Links); `None` = ungültig.
- Funktion `clean_text` (`schulmanager/channels.py:836`) – Text säubern: Steuerzeichen (außer Zeilenumbruch/Tab) entfernen, Zeilenenden vereinheitlichen, kürzen.
- Funktion `clean_name` (`schulmanager/channels.py:843`) – Einzeiliger Name (Ordner, Titel): Steuerzeichen/Zeilenumbrüche entfernen, Leerraum zusammenfassen.
- Funktion `lesson_label` (`schulmanager/channels.py:850`) – Kurzbeschreibung einer Unterrichtsstunde, z. B. `Di, 06.10. · 3. Std. · 09:50`.
- Funktion `submission_status` (`schulmanager/channels.py:866`) – Status einer Abgabe aus Sicht der Schülerin/des Schülers.
- Funktion `submit_status` (`schulmanager/channels.py:878`) – Status beim (erneuten) Abgeben: `abgegeben` oder nach Fristende `verspaetet`.
- … und 2 weitere öffentliche Definitionen (nur die wichtigsten sind aufgeführt)

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`
- [[Modul weeks]] – `weeks` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_channels]]
- [[Routen features_class_info]]
- [[Routen features_exams]]
- [[Routen features_grades]]
- [[Routen features_register]]

## Tests

`tests/test_calendar.py`, `tests/test_channels.py`, `tests/test_channels_rooms.py`, `tests/test_weeks.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
