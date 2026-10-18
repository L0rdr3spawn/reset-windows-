---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_classes.py"
stand: 2026-10-12 22:30
generator: schulmanager-regen
---

# Routen features_classes

> API-Routen · 1 Datei(en) · 1130 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Klassen-Seite (ARCHITECTURE.md §10.2): Suche, Personen, Klassenraum/Klassenleitung, Wochenplan und „findet nicht statt“ mit automatischer Umstellung.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_classes.py` | 1130 | Klassen-Seite (ARCHITECTURE.md §10.2): Suche, Personen, Klassenraum/Klassenleitung, Wochenplan und |

## Endpunkte (9)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/classes` | `list_classes` (`features_classes.py:264`) | (angemeldet) | [[Feature classes]] |
| GET | `/api/v1/classes/{class_id}` | `class_detail` (`features_classes.py:278`) | (angemeldet) | [[Feature classes]] |
| PATCH | `/api/v1/classes/{class_id}` | `patch_class` (`features_classes.py:382`) | (angemeldet) | [[Feature classes]] |
| GET | `/api/v1/classes/{class_id}/curriculum` | `get_class_curriculum` (`features_classes.py:506`) | (angemeldet) | [[Feature classes]] |
| PUT | `/api/v1/classes/{class_id}/curriculum` | `put_class_curriculum` (`features_classes.py:516`) | (angemeldet) | [[Feature classes]], [[Seite MasterDataPage]] |
| GET | `/api/v1/classes/{class_id}/week` | `class_week` (`features_classes.py:596`) | (angemeldet) | [[Feature classes]] |
| POST | `/api/v1/classes/{class_id}/not-taking-place` | `not_taking_place` (`features_classes.py:795`) | substitution.edit | [[Feature classes]] |
| POST | `/api/v1/classes` | `create_class` (`features_classes.py:1077`) | masterdata.edit | [[Feature classes]] |
| POST | `/api/v1/classes/{class_id}/students` | `add_students` (`features_classes.py:1118`) | masterdata.edit | [[Feature classes]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `ClassPatchIn` (`schulmanager/server/routes/features_classes.py:300`)
- Klasse `CurriculumEntryIn` (`schulmanager/server/routes/features_classes.py:455`)
- Klasse `ClassCurriculumIn` (`schulmanager/server/routes/features_classes.py:461`)
- Klasse `NotTakingPlaceIn` (`schulmanager/server/routes/features_classes.py:631`)
- Klasse `ParentIn` (`schulmanager/server/routes/features_classes.py:851`)
- Klasse `NewStudentIn` (`schulmanager/server/routes/features_classes.py:856`)
- Klasse `AccountOptionsIn` (`schulmanager/server/routes/features_classes.py:865`)
- Klasse `ClassCreateIn` (`schulmanager/server/routes/features_classes.py:873`)
- Klasse `StudentsAddIn` (`schulmanager/server/routes/features_classes.py:883`)

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul integrations]] – `_common` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul planning]] – `planning` *(nur zur Laufzeit importiert)*
- [[Modul substitution]] – `substitution` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_data]] – `features_data` *(nur zur Laufzeit importiert)*
- [[Routen features_parent_access]] – `features_parent_access` *(nur zur Laufzeit importiert)*
- [[Routen features_substitutions]] – `features_substitutions`
- [[Routen features_timetable]] – `features_timetable`
- [[Routen users]] – `users` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`
- [[Server deps]] – `deps`
- [[Server letters und pdf]] – `letters` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_class_curriculum.py`, `tests/test_classes.py`, `tests/test_curricula.py`, `tests/test_letters.py`, `tests/test_register.py`, `tests/test_self_reset.py`, `tests/test_teacher_scope.py`, `tests/test_weeks.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
