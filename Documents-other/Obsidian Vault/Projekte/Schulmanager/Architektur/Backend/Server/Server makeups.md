---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/makeups.py"
stand: 2026-10-12 22:30
generator: schulmanager-regen
---

# Server makeups

> Server-Kern · 1 Datei(en) · 510 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Nachschreibtermine – Logik ohne HTTP (Routen: `routes/features_makeups.py`).

Ablauf ------ 1. `` legt für jede Klausur/jeden Test des Planungsdokuments und jede Person, die an dem Tag laut Krankmeldung (`kind=krank`) oder Klassenbuch (`kind=fehlt`) gefehlt hat, eine Zeile `exam_makeups` an (Status `offen`) und räumt Zeilen auf, deren Klausur oder Fehlzeit weggefallen ist. Aufgerufen nach jeder Änderung an Fehlzeiten (SQLAlchemy-Ereignis, ``), nach Klausur-Änderungen und beim Lesen. 2. Die Lehrkraft der Klausur (`exam.edit` für diese Klausur) legt einen Termin fest (`` prüft Schultag, Zeitraster, Raum und Lehrkraft gegen Klausuren, Termine und Stundenplan). 3. Das Attest wird nicht gespeichert, sondern aus den Dokumenten der Fehlzeit abgeleitet (``).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/makeups.py` | 510 | Nachschreibtermine – Logik ohne HTTP (Routen: `routes/features_makeups.py`). |

## Wichtige Funktionen und Klassen

- Funktion `exam_students` (`schulmanager/server/makeups.py:45`) – Schüler-IDs, die die Klausur schreiben (Kursteile wie `timetable.student_parts`).
- Funktion `sync` (`schulmanager/server/makeups.py:79`) – Gleicht `exam_makeups` mit Klausuren und Fehlzeiten ab (siehe Moduldoku). Gibt die Zahl neuer Zeilen zurück;
- Funktion `sync_now` (`schulmanager/server/makeups.py:136`) – Eigene Sitzung: abgleichen, Live-Ereignis senden, wenn sich etwas geändert hat. Fehler werden nur geloggt.
- Funktion `install_hooks` (`schulmanager/server/makeups.py:159`) – Nach jedem Commit, der Fehlzeiten ändert, die Nachschreib-Zeilen abgleichen.
- Funktion `attest_states` (`schulmanager/server/makeups.py:185`) – Attest-Zustand je Zeile aus den Dokumenten der Fehlzeiten, die den Klausurtag abdecken.
- Klasse `MakeupAccess` (`schulmanager/server/makeups.py:230`) – Wer sieht welche Nachschreib-Zeile (siehe Moduldoku).
  - Methoden: `exam`:239, `teaches`:242, `level`:249
- Funktion `own_lessons` (`schulmanager/server/makeups.py:261`) – Unterrichtsblöcke am Tag, die eine Lehrkraft der Klausur selbst hält und in denen mindestens eine der
- Funktion `check_date` (`schulmanager/server/makeups.py:289`) – Konflikte eines Nachschreibtermins (leer = frei): Schultag, Zeitraster, Raum und Lehrkraft gegen Klausuren,
- Funktion `suggest` (`schulmanager/server/makeups.py:358`) – Terminvorschläge für das Nachschreiben von `student_ids`, sortiert nach Eignung.

## Datenbank-Tabellen

- **Nutzt:** `exam_makeup_dates`, `exam_makeups` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `student_absences`, `student_documents` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul exams]] – `exams` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Routen features_exams]] – `features_exams` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`, `makeups`, `student_self`
- [[Server elternzugriff]] – `absence_access`

## Wird genutzt von

- [[Routen features_exams]]
- [[Routen features_makeups]]

## Tests

`tests/test_makeups.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
