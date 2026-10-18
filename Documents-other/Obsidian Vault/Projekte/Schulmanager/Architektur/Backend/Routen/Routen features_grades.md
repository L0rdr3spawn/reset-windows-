---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_grades.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen features_grades

> API-Routen · 1 Datei(en) · 219 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Noten: Klausuren/Tests (`exam_results`) und bewertete Hausaufgaben der Kursräume.

* `GET  /exams/{exam_id}/results` – Schüler/innen des Kurses (bzw. Kursteils) mit Note/Bemerkung
  (Lehrkraft des Kurses oder Personal mit `exam.edit` ohne Einschränkung)
* `PUT  /exams/{exam_id}/results` – Noten eintragen/ändern (leere Note = löschen)
* `GET  /grades?student_id=` – „Meine Noten“: alle Noten eines Kindes nach Fach (Schüler/in selbst, Eltern –
  bei volljährigen Kindern nur mit deren Freigabe –, Klassenleitung/Lehrkräfte der Klasse, Sekretariat/Leitung)
Noten und Bemerkungen liegen nur verschlüsselt in der Datenbank. Mitschüler/innen sehen nie fremde Noten.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_grades.py` | 219 | Noten: Klausuren/Tests (`exam_results`) und bewertete Hausaufgaben der Kursräume. |

## Endpunkte (3)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/exams/{exam_id}/results` | `get_results` (`features_grades.py:77`) | (angemeldet) | [[Feature students]] |
| PUT | `/api/v1/exams/{exam_id}/results` | `put_results` (`features_grades.py:99`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/grades` | `student_grades` (`features_grades.py:153`) | (angemeldet) | [[Feature students]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `ResultIn` (`schulmanager/server/routes/features_grades.py:31`)
- Klasse `ResultsIn` (`schulmanager/server/routes/features_grades.py:37`)

## Datenbank-Tabellen

- **Nutzt:** `assignment_submissions`, `channel_items`, `channels` → [[Datenmodell#Kursräume]]
- **Nutzt:** `exam_results` → [[Datenmodell#Schüler, Klassenbuch und Noten]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul channels]] – `channels` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_exams]] – `features_exams` *(nur zur Laufzeit importiert)*
- [[Server crypto]] – `crypto`
- [[Server db]] – `channels`, `db`, `db_models`, `grades`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `parent_access` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_calendar]]
- [[Routen features_support]]

## Tests

`tests/test_calendar.py`, `tests/test_grades.py`, `tests/test_server_features.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
