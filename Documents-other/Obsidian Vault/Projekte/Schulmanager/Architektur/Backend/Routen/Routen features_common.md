---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_common.py"
stand: 2026-10-12 22:26
generator: schulmanager-regen
---

# Routen features_common

> API-Routen · 1 Datei(en) · 749 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Gemeinsame Hilfsfunktionen der Fach-Router **ohne eigene Endpunkte**: `snapshot()`, `mutate()`, `cached`/`day_plan`, Rechte-/Umfangshilfen (`reads_all_plans`, `plan_class_ids`, `students_in_scope`), `publish_change`, `write_audit`, `check_id`. Von 30+ Dateien genutzt.

Aus dem Modulkopf:

Gemeinsame Hilfsfunktionen der Feature-Endpunkte.

Dieses Modul exportiert bewusst **keinen** `router` – es enthält

* den Zugriff auf Store/Event-Bus (`snapshot`, `mutate`),
* LRU-Caches für Vertretungspläne (`(store.version, datum)`) und abgeleitete Daten,
* Rechte-/Sichtbarkeitsregeln (Rollenmatrix aus `docs/ARCHITECTURE.md` §6),
* das Filtern/Bereinigen von Vertretungsplänen je Rolle.

Lehrer-Scope (§9.3): `plans.read_all` ist für Lehrkräfte auf `own_classes` beschränkt. Sie sehen nur Pläne/Einträge ihrer Klassen (unterrichtet oder Klassenleitung), ihren eigenen Plan und Räume – nie fremde Lehrerpläne oder Schülerdaten fremder Klassen. Hilfen: `reads_all_plans`, `is_scoped_teacher`, `teacher_entry_filter`, `plan_class_ids`.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_common.py` | 749 | Gemeinsame Hilfsfunktionen der Feature-Endpunkte. |

## Wichtige Funktionen und Klassen

- Funktion `has` (`schulmanager/server/routes/features_common.py:34`)
- Funktion `need` (`schulmanager/server/routes/features_common.py:38`) – 403, wenn der Benutzer keines der Rechte besitzt.
- Funktion `own_student_ids` (`schulmanager/server/routes/features_common.py:44`) – Schüler: eigene ID; Eltern: Kinder.
- Funktion `perm_scope` (`schulmanager/server/routes/features_common.py:53`) – Einschränkung eines Rechts (`own_classes`, `own`, `own_children`, `own_courses` …)
- Funktion `reads_all_plans` (`schulmanager/server/routes/features_common.py:69`) – `plans.read_all` ohne Einschränkung (alle Klassen, Lehrkräfte, Räume, Schulstatistik).
- Funktion `is_scoped_teacher` (`schulmanager/server/routes/features_common.py:74`) – Lehrkraft mit eingeschränktem Planzugriff (`plans.read_all` → `own_classes`; Abteilungsleitung:
- Funktion `get_store` (`schulmanager/server/routes/features_common.py:81`)
- Klasse `Snap` (`schulmanager/server/routes/features_common.py:86`) – `(version, school)` plus Cache-Schlüssel `key` (Version + Inhalts-Digest).
- Funktion `snapshot` (`schulmanager/server/routes/features_common.py:94`) – Liefert `(version, school)` – Version/Digest zuerst lesen, dann das Dokument
- Funktion `snap_key` (`schulmanager/server/routes/features_common.py:106`)
- Funktion `mutate` (`schulmanager/server/routes/features_common.py:113`) – `store.mutate` mit optionalen `dates` (für gezieltes Neuladen der Clients).
- Funktion `publish` (`schulmanager/server/routes/features_common.py:138`)
- Funktion `publish_change` (`schulmanager/server/routes/features_common.py:146`) – Event für Änderungen außerhalb des Planungsdokuments (DB-Tabellen).
- Funktion `write_audit` (`schulmanager/server/routes/features_common.py:155`)
- Funktion `parse_date` (`schulmanager/server/routes/features_common.py:164`)
- Funktion `date_range` (`schulmanager/server/routes/features_common.py:173`)
- Funktion `check_range` (`schulmanager/server/routes/features_common.py:177`)
- Funktion `iso_dates` (`schulmanager/server/routes/features_common.py:184`)
- Funktion `now_iso` (`schulmanager/server/routes/features_common.py:189`)
- Klasse `LRUCache` (`schulmanager/server/routes/features_common.py:194`) – Thread-sicherer LRU-Cache; gleichzeitige Anfragen für denselben Schlüssel
  - Methoden: `get`:206, `clear`:231
- Funktion `clear_caches` (`schulmanager/server/routes/features_common.py:240`)
- Funktion `day_plan` (`schulmanager/server/routes/features_common.py:245`) – Vertretungsplan eines Tages: `(DayPlan, DayPlan.to_dict())` – gecacht pro `(version, datum)`.
- Funktion `week_history` (`schulmanager/server/routes/features_common.py:263`) – Vertretungen je Lehrkraft von Montag bis zum Vortag (aus gecachten Tagesplänen).
- Funktion `range_plans` (`schulmanager/server/routes/features_common.py:280`) – Pläne aller Schulöffnungstage im Bereich (Mo–So, wie `compute_range`, aber aus dem Cache).
- Funktion `range_plan_objects` (`schulmanager/server/routes/features_common.py:288`)
- Funktion `cached` (`schulmanager/server/routes/features_common.py:295`)
- Funktion `index` (`schulmanager/server/routes/features_common.py:300`) – `school.index(name)` – pro Version gecacht (nicht verändern!).
- Funktion `effective_cells` (`schulmanager/server/routes/features_common.py:306`) – Effektiver Tag (`substitution.effective_day`), gecacht.
- Funktion `student_parts` (`schulmanager/server/routes/features_common.py:328`)
- Funktion `teacher_class_ids` (`schulmanager/server/routes/features_common.py:338`) – Klassen, die eine Lehrkraft unterrichtet (inkl. Klassenleitung).
- Funktion `teacher_course_ids` (`schulmanager/server/routes/features_common.py:355`)
- Funktion `family_student_ids` (`schulmanager/server/routes/features_common.py:366`) – `own_student_ids` für einen Elternzugriffs-Bereich (``): Eltern volljähriger Kinder
- Funktion `own_class_ids` (`schulmanager/server/routes/features_common.py:380`) – Klassen, die der Benutzer „als eigene“ sieht (Schüler/Eltern: Klassen der Kinder,
- Funktion `plan_class_ids` (`schulmanager/server/routes/features_common.py:397`) – Klassen, deren Pläne (und Klassenseiten) der Benutzer sehen darf: `None` = alle (`plans.read_all` ohne
- Funktion `plan_course_ids` (`schulmanager/server/routes/features_common.py:414`) – Kurse, deren Daten (Stunden, Klausuren) ein Benutzer mit `plans.read_all` sehen darf (`None` = alle):
- Funktion `teacher_entry_filter` (`schulmanager/server/routes/features_common.py:426`) – Filter für Vertretungsplan-Einträge einer Lehrkraft: Einträge eigener Klassen sowie eigene
- Funktion `visible_student_ids` (`schulmanager/server/routes/features_common.py:447`) – `None` = alle Schüler sichtbar; sonst Menge der sichtbaren Schüler-IDs.
- Funktion `teacher_student_ids` (`schulmanager/server/routes/features_common.py:461`)
- Funktion `can_see_student` (`schulmanager/server/routes/features_common.py:471`)
- Funktion `students_in_scope` (`schulmanager/server/routes/features_common.py:476`) – Schüler-IDs, für die `perm` gilt (`None` = alle; leere Menge = keine).
- Funktion `absence_reasons` (`schulmanager/server/routes/features_common.py:500`) – Gründe von Lehrkraft-Abwesenheiten (personenbezogen → für Nicht-Editoren entfernen).
- Funktion `scrub` (`schulmanager/server/routes/features_common.py:521`) – Entfernt Abwesenheitsgründe aus Hinweistexten – nur als ganze Wörter (Grund „Kur“ lässt „Exkursion“,
- Funktion `pupil_entry_filter` (`schulmanager/server/routes/features_common.py:552`) – Filter: nur Einträge der eigenen Klasse(n) bzw. gewählten Kursteile
- Funktion `filter_plan` (`schulmanager/server/routes/features_common.py:592`) – Vertretungsplan nach Rolle filtern (gibt eine Kopie zurück).
- Funktion `absences_for_day` (`schulmanager/server/routes/features_common.py:705`)
- … und 4 weitere öffentliche Definitionen (nur die wichtigsten sind aufgeführt)

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul substitution]] – `substitution` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db` *(nur zur Laufzeit importiert)*
- [[Server elternzugriff]] – `parent_access` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server notify]] – `notify` *(nur zur Laufzeit importiert)*
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen api_open]]
- [[Routen features_absence_log]]
- [[Routen features_absence_stats]]
- [[Routen features_announcements]]
- [[Routen features_api_access]]
- [[Routen features_calendar]]
- [[Routen features_channels]]
- [[Routen features_chats]]
- [[Routen features_class_info]]
- [[Routen features_classes]]
- [[Routen features_data]]
- [[Routen features_exams]]
- [[Routen features_exchange]]
- [[Routen features_forms]]
- [[Routen features_grades]]
- [[Routen features_holiday_import]]
- [[Routen features_makeups]]
- [[Routen features_messages]]
- [[Routen features_parent_access]]
- [[Routen features_planning]]
- [[Routen features_register]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]
- [[Routen features_substitutions]]
- [[Routen features_support]]
- [[Routen features_teacher_profile]]
- [[Routen features_timetable]]
- [[Server api_scopes]]
- [[Server autoplan]]
- [[Server elternzugriff]] – `absence_access`
- [[Server jobs]]
- [[Server makeups]]
- [[Server notify]]

## Tests

`tests/test_classes.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_student_self.py`, `tests/test_substitution_b04.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
