---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_timetable.py"
stand: 2026-10-12 21:21
generator: schulmanager-regen
---

# Routen features_timetable

> API-Routen · 1 Datei(en) · 209 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Stundenplan-Ansichten, Verschieben (Drag & Drop) und Fixieren von Stunden.

Sichtbarkeit (§6/§9.3): `plans.read_all` ohne Einschränkung → alle Pläne. Lehrkräfte (Scope `own_classes`) → Pläne ihrer Klassen (unterrichtet/Klassenleitung), der eigene Lehrerplan und Räume; Schülerpläne nur für Schüler/innen eigener Klassen. Schüler/Eltern → eigene Klasse(n) und eigener Schülerplan.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_timetable.py` | 209 | Stundenplan-Ansichten, Verschieben (Drag & Drop) und Fixieren von Stunden. |

## Endpunkte (6)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/timetable/lessons` | `list_lessons` (`features_timetable.py:75`) | (angemeldet) | – |
| GET | `/api/v1/timetable/allowed` | `allowed_refs` (`features_timetable.py:85`) | (angemeldet) | [[Feature teacher]] |
| GET | `/api/v1/timetable/lessons/{lesson_id}/options` | `lesson_options` (`features_timetable.py:109`) | timetable.edit | [[Seite TimetablePage]] |
| POST | `/api/v1/timetable/lessons/{lesson_id}/move` | `move` (`features_timetable.py:123`) | timetable.edit | [[Seite TimetablePage]] |
| POST | `/api/v1/timetable/lessons/{lesson_id}/lock` | `lock` (`features_timetable.py:152`) | timetable.edit | [[Seite TimetablePage]] |
| GET | `/api/v1/timetable/{kind}/{ref}` | `view` (`features_timetable.py:189`) | (angemeldet) | [[Seite TimetablePage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `MoveIn` (`schulmanager/server/routes/features_timetable.py:29`)
- Klasse `LockIn` (`schulmanager/server/routes/features_timetable.py:34`)
- Funktion `check_view_access` (`schulmanager/server/routes/features_timetable.py:38`) – Rechte für Stundenplan-Ansichten (Rollenmatrix inkl. Lehrer-Scope).
- Funktion `view_monday` (`schulmanager/server/routes/features_timetable.py:167`) – Woche einer Ansicht: `date` (kanonisch) > `week_no` (laufende Woche des aktuellen Schuljahres) > `week`

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Server deps]] – `deps`

## Wird genutzt von

- [[Routen api_open]]
- [[Routen features_calendar]]
- [[Routen features_class_info]]
- [[Routen features_classes]]

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_rights.py`, `tests/test_server_features.py`, `tests/test_teacher_scope.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
