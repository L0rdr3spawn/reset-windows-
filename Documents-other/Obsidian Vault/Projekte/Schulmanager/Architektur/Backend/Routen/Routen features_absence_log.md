---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_absence_log.py"
stand: 2026-10-12 22:29
generator: schulmanager-regen
---

# Routen features_absence_log

> API-Routen · 1 Datei(en) · 103 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Meldungsprotokoll der Fehlzeiten lesen (Schreiben: ``).

* `GET /student-absences/{id}/history` – Verlauf einer Meldung (auch einer zurückgenommenen, solange das Protokoll
  besteht): wer hat wann über welchen Kanal gemeldet, jede Änderung mit vorher → nachher.
* `GET /channels/{id}/klasse/absences?from=&to=` – Klassenraum, Bereich „Klasse“: „Fehlzeiten & Meldungen“ je
  Schüler/in der Klasse (Zeitpunkt, Kanal, bei voller Sicht Verlauf). Nur für Lehrkräfte des Klassenraums und die
  Schulleitung – Schüler/innen und Eltern bekommen 403.

Rechtestufen (Details in ``): Klassenleitung/Sekretariat/Schulleitung sehen den vollen Verlauf, Fachlehrkräfte der Klasse nur „abwesend gemeldet“ mit Zeitpunkt und Kanal (keine Person, Art, Status, Gründe, Dokumente), die technische Administration nichts.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_absence_log.py` | 103 | Meldungsprotokoll der Fehlzeiten lesen (Schreiben: ``). |

## Endpunkte (2)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/student-absences/{absence_id}/history` | `absence_history` (`features_absence_log.py:38`) | (angemeldet) | – |
| GET | `/api/v1/channels/{channel_id}/klasse/absences` | `class_absences` (`features_absence_log.py:55`) | (angemeldet) | [[Feature channels]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Datenbank-Tabellen

- **Nutzt:** `student_absences` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Routen features_class_info]] – `features_class_info`
- [[Routen features_common]] – `features_common`
- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Server absence_log]] – `absence_log`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `absence_access`

## Wird genutzt von

- –

## Tests

`tests/test_absence_log.py`, `tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_attendance.py`, `tests/test_calendar.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_channels_rooms.py`, `tests/test_class_room_info.py`, `tests/test_forms.py`, `tests/test_homework_links.py`, `tests/test_makeups.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
