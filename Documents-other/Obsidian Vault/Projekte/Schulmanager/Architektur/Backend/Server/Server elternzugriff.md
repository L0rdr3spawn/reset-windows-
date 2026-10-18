---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/absence_access.py, schulmanager/server/parent_access.py"
stand: 2026-10-12 22:26
generator: schulmanager-regen
---

# Server elternzugriff

> Server-Kern · 2 Datei(en) · 451 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Bausteine für Elternsicht: `parent_access.parent_may_see(db, student, AREA)` (Eltern sehen, was ihr minderjähriges Kind sieht; Volljährige legen je Bereich fest) und `absence_access` (wer sieht und bearbeitet welche Schüler-Krankmeldung). Jede Fach-Route mit Kindbezug muss einen dieser Bausteine nutzen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/absence_access.py` | 229 | Wer sieht und bearbeitet welche Schüler-Krankmeldung (A-58, B-06). |
| `schulmanager/server/parent_access.py` | 222 | Elternzugriff (A-44) – wiederverwendbarer Baustein für alle Bereiche. |

## Wichtige Funktionen und Klassen

- Funktion `subject_view` (`schulmanager/server/absence_access.py:32`) – Schulschalter `subject_teacher_absence_view` (unbekannte Werte zählen als `none`).
- Funktion `part_members` (`schulmanager/server/absence_access.py:39`) – Schüler-IDs je Kursteil – dieselbe Regel wie `timetable.student_parts`: Ein-Teil-Kurs = ganze Klasse(n);
- Funktion `taught_students` (`schulmanager/server/absence_access.py:62`) – Schüler/innen, die einen Kursteil der Lehrkraft tatsächlich besuchen (ohne Klassenleitung).
- Funktion `class_teacher_students` (`schulmanager/server/absence_access.py:78`) – Schüler/innen der Klassen, deren Klassenleitung die Lehrkraft ist.
- Funktion `lesson_periods` (`schulmanager/server/absence_access.py:92`) – Schüler-ID → Stunden am `day`, in denen die Lehrkraft sie unterrichtet (effektiver Tag: Vertretungen und
- Klasse `AbsenceAccess` (`schulmanager/server/absence_access.py:128`) – Rechte und Datenumfang eines Kontos für Krankmeldungen (je Anfrage, Planungsstand `snap`).
  - Methoden: `family_ids`:158, `linked_but_hidden`:170, `class_students`:175, `taught`:182, `level`:188, `own`:201, `visible_level`:204, `can_manage`:211, `can_delete`:215, `presence_enabled`:222, `lesson_periods`:225
- Funktion `age_on` (`schulmanager/server/parent_access.py:76`) – Alter in vollen Jahren am `day` (29.02. zählt im Nicht-Schaltjahr ab 01.03.).
- Funktion `is_adult` (`schulmanager/server/parent_access.py:81`) – Volljährig? Geburtsdatum (Planungsdokument) vor dem Konto-Merkmal `users.adult`.
- Funktion `allowed_areas` (`schulmanager/server/parent_access.py:96`) – Gespeicherte Einstellungen einer/eines Schüler/in (alle Bereiche, ohne Eintrag `False`).
- Funktion `parent_may_see` (`schulmanager/server/parent_access.py:106`) – Dürfen die Eltern den Bereich `area` dieses Kindes sehen? Minderjährig → immer ja; volljährig → nur mit
- Funktion `visible_children` (`schulmanager/server/parent_access.py:121`) – Die Kinder aus `student_ids`, deren Bereich `area` die Eltern sehen dürfen (Reihenfolge bleibt).
- Funktion `set_areas` (`schulmanager/server/parent_access.py:129`) – Speichert Einwilligungen (ohne Commit, ohne Rechteprüfung) und liefert die tatsächlich geänderten Bereiche.
- Funktion `delivery_of` (`schulmanager/server/parent_access.py:151`) – Wohin gehen Rundschreiben der Schule? Minderjährig immer `both`; volljährig die gespeicherte Wahl.
- Funktion `delivery_routing` (`schulmanager/server/parent_access.py:159`) – `{schüler_id: "self"|"parents"}` für alle volljährigen Schüler/innen, deren Rundschreiben nicht an beide gehen
- Funktion `set_delivery` (`schulmanager/server/parent_access.py:182`) – Speichert die Zustellung (ohne Commit); `True` bei Änderung.
- Funktion `mark_decided` (`schulmanager/server/parent_access.py:197`)
- Funktion `decision_pending` (`schulmanager/server/parent_access.py:207`) – Volljährig, aber die Freigaben wurden noch nie bewusst gespeichert (→ Hinweis in der Oberfläche).
- Funktion `effective_adult` (`schulmanager/server/parent_access.py:214`) – Gilt das Konto als volljährig? Schüler: Geburtsdatum vor Konto-Merkmal (`is_adult`); sonst das Merkmal.

## Datenbank-Tabellen

- **Nutzt:** `parent_access` → [[Datenmodell#Rollen und Rechte]]
- **Nutzt:** `student_prefs` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`, `parent_access`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_absence_log]]
- [[Routen features_absence_stats]]
- [[Routen features_announcements]]
- [[Routen features_channels]]
- [[Routen features_common]]
- [[Routen features_forms]]
- [[Routen features_grades]]
- [[Routen features_messages]]
- [[Routen features_parent_access]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]
- [[Server absence_log]]
- [[Server deps]]
- [[Server makeups]]

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_channels_parents.py`, `tests/test_student_absence_access.py`, `tests/test_student_self.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
