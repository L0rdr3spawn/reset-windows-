---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_student_absences.py"
stand: 2026-10-12 22:41
generator: schulmanager-regen
---

# Routen features_student_absences

> API-Routen · 1 Datei(en) · 1174 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Krankmeldungen von Schüler/innen (Tabelle `student_absences`, A-58/B-06).

Wer was sieht und darf, entscheidet `` (Stufen `full`/`family`/`teacher`):

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_student_absences.py` | 1174 | Krankmeldungen von Schüler/innen (Tabelle `student_absences`, A-58/B-06). |

## Endpunkte (13)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/student-absences/access` | `student_absence_access` (`features_student_absences.py:224`) | (angemeldet) | [[Seite StudentAbsencesPage]] |
| GET | `/api/v1/student-absences/preview` | `report_preview` (`features_student_absences.py:244`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/student-absences` | `list_student_absences` (`features_student_absences.py:277`) | (angemeldet) | [[Feature students]], [[Seite StudentAbsencesPage]] |
| POST | `/api/v1/student-absences` | `report_student_absence` (`features_student_absences.py:455`) | (angemeldet) | [[Feature students]], [[Seite StudentAbsencesPage]] |
| PATCH | `/api/v1/student-absences/{absence_id}` | `patch_student_absence` (`features_student_absences.py:601`) | (angemeldet) | [[Feature students]], [[Seite StudentAbsencesPage]] |
| DELETE | `/api/v1/student-absences/{absence_id}` | `delete_student_absence` (`features_student_absences.py:641`) | (angemeldet) | [[Feature students]], [[Seite StudentAbsencesPage]] |
| POST | `/api/v1/student-absences/{absence_id}/shorten` | `shorten_absence` (`features_student_absences.py:748`) | (angemeldet) | [[Feature students]] |
| POST | `/api/v1/student-absences/{absence_id}/extend` | `extend_absence` (`features_student_absences.py:812`) | (angemeldet) | [[Feature students]] |
| POST | `/api/v1/student-absences/{absence_id}/request-withdrawal` | `request_withdrawal` (`features_student_absences.py:872`) | (angemeldet) | [[Feature students]] |
| POST | `/api/v1/student-absences/{absence_id}/return-leave` | `return_leave` (`features_student_absences.py:895`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/student-absences/record` | `student_record` (`features_student_absences.py:943`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/student-absences/form.pdf` | `excuse_form` (`features_student_absences.py:1025`) | (angemeldet) | – |
| GET | `/api/v1/student-absences/leave-form.pdf` | `leave_form` (`features_student_absences.py:1106`) | (angemeldet) | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `status_label` (`schulmanager/server/routes/features_student_absences.py:75`)
- Klasse `StudentAbsenceIn` (`schulmanager/server/routes/features_student_absences.py:87`)
- Klasse `StudentAbsencePatch` (`schulmanager/server/routes/features_student_absences.py:100`)
- Funktion `absence_out` (`schulmanager/server/routes/features_student_absences.py:138`) – Krankmeldung in der Sicht des Kontos (`view`). Ohne Zugriff bleiben Grund, Vermerk, Status, Attest leer.
- Funktion `export_rows` (`schulmanager/server/routes/features_student_absences.py:191`) – DSGVO-Export: eigene Meldungen und die der eigenen Person/Kinder – im selben Umfang wie die Liste
- Klasse `ShortenIn` (`schulmanager/server/routes/features_student_absences.py:662`) – Früher zurück: `back_date` = erster Tag, an dem die Person wieder da ist; mit `back_lesson` (1-basiert,
- Klasse `ExtendIn` (`schulmanager/server/routes/features_student_absences.py:669`)

## Datenbank-Tabellen

- **Nutzt:** `student_absences`, `student_documents` → [[Datenmodell#Schüler, Klassenbuch und Noten]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul student_self]] – `student_self` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_student_self]] – `features_student_self` *(nur zur Laufzeit importiert)*
- [[Routen features_substitutions]] – `features_substitutions` *(nur zur Laufzeit importiert)*
- [[Server absence_log]] – `absence_log`
- [[Server db]] – `db`, `db_models`, `student_self`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `absence_access`
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server files]] – `files` *(nur zur Laufzeit importiert)*
- [[Server letters und pdf]] – `pdf_simple` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_absence_log]]
- [[Routen features_calendar]]
- [[Routen features_forms]]
- [[Routen features_register]]
- [[Routen features_student_self]]
- [[Routen me]]
- [[Server absence_log]]

## Tests

`tests/test_absence_log.py`, `tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_attendance.py`, `tests/test_forms.py`, `tests/test_makeups.py`, `tests/test_register.py`, `tests/test_rights.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_student_absence_actions.py`, `tests/test_student_self.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
