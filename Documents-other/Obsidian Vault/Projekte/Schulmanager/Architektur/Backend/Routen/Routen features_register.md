---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_register.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Routen features_register

> API-Routen · 1 Datei(en) · 456 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Klassenbuch: Anwesenheit je Unterrichtsstunde, Thema und Hausaufgabe.

* `GET /register/day?class_id=&date=` – alle Stunden der Klasse an dem Tag (tatsächlicher Plan inkl. Vertretung/
  Entfall) mit Schülerliste; Krankmeldungen (auch „Jetzt krank melden“ der Schüler/innen) sind vorausgefüllt.
* `PUT /register/lesson` – Anwesenheit, Thema, Hausaufgabe speichern. Nur eingetragene Schüler/innen werden
  geschickt (sonst „nicht eingetragen“); `present` / `absent`, `late` = anwesend mit Verspätung (Minuten),
  `left` nur noch für alte Einträge; `note` = Notiz der Lehrkraft (z. B. „krank nach Hause“). Fehlen und
  Verspätung werden als offene Fehlzeiten (`student_absences`, `source=lehrkraft`, `register_id`, Notiz in
  `note`) geführt – entschuldigt erst über Entschuldigung (Eltern bzw. Volljährige) + Bestätigung.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_register.py` | 456 | Klassenbuch: Anwesenheit je Unterrichtsstunde, Thema und Hausaufgabe. |

## Endpunkte (5)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/register/day` | `register_day` (`features_register.py:152`) | (angemeldet) | [[Feature classes]] |
| GET | `/api/v1/register/classes` | `register_classes` (`features_register.py:215`) | (angemeldet) | [[Feature classes]] |
| GET | `/api/v1/register/overview` | `register_overview` (`features_register.py:234`) | (angemeldet) | [[Feature classes]] |
| GET | `/api/v1/register/now` | `register_now` (`features_register.py:314`) | (angemeldet) | [[Feature classes]] |
| PUT | `/api/v1/register/lesson` | `save_lesson` (`features_register.py:363`) | (angemeldet) | [[Feature classes]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `AttendanceIn` (`schulmanager/server/routes/features_register.py:40`)
- Klasse `LessonIn` (`schulmanager/server/routes/features_register.py:47`)

## Datenbank-Tabellen

- **Nutzt:** `register_lessons`, `student_absences` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul channels]] – `channels` *(nur zur Laufzeit importiert)*
- [[Modul messaging]] – `messaging` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Routen features_support]] – `features_support` *(nur zur Laufzeit importiert)*
- [[Server absence_log]] – `absence_log`
- [[Server crypto]] – `crypto`
- [[Server db]] – `db`, `db_models`, `register`
- [[Server deps]] – `deps`
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_channels]]

## Tests

`tests/test_absence_log.py`, `tests/test_register.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
