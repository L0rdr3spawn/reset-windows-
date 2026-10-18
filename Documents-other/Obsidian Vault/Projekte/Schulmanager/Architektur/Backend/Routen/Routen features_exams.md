---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_exams.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen features_exams

> API-Routen · 1 Datei(en) · 285 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Klassenarbeiten/Klausuren.

Lehrkräfte (`exam.edit` mit Scope `own_courses`) dürfen nur Klausuren in eigenen Kursen (bzw. im eigenen Kursteil) anlegen/ändern/löschen. Schüler/Eltern sehen die Klausuren ihrer Kurse. Regelverstöße (`exams.check_exam`) → 409 `{"detail":{"conflicts":[...]}}`, außer `force: true` (nicht für Lehrkräfte).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_exams.py` | 285 | Klassenarbeiten/Klausuren. |

## Endpunkte (5)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/exams` | `list_exams` (`features_exams.py:172`) | (angemeldet) | [[Seite ExamsPage]] |
| POST | `/api/v1/exams/check` | `check` (`features_exams.py:209`) | exam.edit | [[Seite ExamsPage]] |
| POST | `/api/v1/exams` | `create_exam` (`features_exams.py:218`) | exam.edit | [[Seite ExamsPage]] |
| PUT | `/api/v1/exams/{exam_id}` | `update_exam` (`features_exams.py:241`) | exam.edit | [[Seite ExamsPage]] |
| DELETE | `/api/v1/exams/{exam_id}` | `delete_exam` (`features_exams.py:268`) | exam.edit | [[Seite ExamsPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `ExamIn` (`schulmanager/server/routes/features_exams.py:28`)
- Funktion `exam_info` (`schulmanager/server/routes/features_exams.py:41`) – Klausur mit Anzeige-Informationen (Fach, Klassen, Lehrkraft, Uhrzeit).
- Funktion `lesson_room` (`schulmanager/server/routes/features_exams.py:58`) – Raum der Unterrichtsstunde, in der die Klausur liegt (Ersatz, solange `exam.room` leer ist).
- Funktion `channel_links` (`schulmanager/server/routes/features_exams.py:82`) – Klausur-ID → Kursraum (Kursteil), den das Konto öffnen darf (sonst kein Eintrag).
- Funktion `exam_names` (`schulmanager/server/routes/features_exams.py:109`) – Volle Namen zu Kürzeln (Lehrkräfte, Fächer, Räume, Klassen) für Sprechblasen.

## Hängt ab von

- [[Modul channels]] – `channels` *(nur zur Laufzeit importiert)*
- [[Modul exams]] – `exams` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Routen features_channels]] – `features_channels` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_data]] – `features_data` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`
- [[Server deps]] – `deps`
- [[Server makeups]] – `makeups` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_calendar]]
- [[Routen features_grades]]
- [[Routen features_makeups]]
- [[Routen features_substitutions]]
- [[Server makeups]]

## Tests

`tests/test_calendar.py`, `tests/test_grades.py`, `tests/test_server_features.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
