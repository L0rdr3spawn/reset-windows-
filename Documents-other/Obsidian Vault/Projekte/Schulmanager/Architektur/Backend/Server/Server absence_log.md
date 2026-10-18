---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/absence_log.py"
stand: 2026-10-12 22:38
generator: schulmanager-regen
---

# Server absence_log

> Server-Kern · 1 Datei(en) · 238 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Meldungsprotokoll der Fehlzeiten: schreiben und – je nach Rechtestufe – ausgeben.

Geschrieben wird mit `` in derselben Transaktion wie die Änderung an der Meldung (der Aufrufer committet). Das Protokoll ist nur anhängend (siehe ``).

Wer was sieht (``, Stufen aus ``):

* `full`     – Klassenleitung, Sekretariat, Schulleitung: der volle Verlauf mit Person, Rolle, Kanal und jeder
  Änderung (vorher → nachher). Gründe, Vermerke und Diagnosen stehen auch hier nie im Protokoll.
* `presence` – Lehrkräfte, die in der Klasse unterrichten: nur „abwesend gemeldet“ mit Zeitpunkt und Kanal – keine
  Person, keine Art (krank/Beurlaubung), kein Status, keine Dokumente.
* `None`     – alle anderen (Familie, technische Administration, fremde Lehrkräfte): nichts.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/absence_log.py` | 238 | Meldungsprotokoll der Fehlzeiten: schreiben und – je nach Rechtestufe – ausgeben. |

## Wichtige Funktionen und Klassen

- Funktion `channel_override` (`schulmanager/server/absence_log.py:44`) – Alle Einträge in diesem Block tragen den Kanal (z. B. `formular` für Aktionen von Formularen).
- Funktion `role_label` (`schulmanager/server/absence_log.py:53`)
- Funktion `channel_for` (`schulmanager/server/absence_log.py:60`) – Kanal einer neuen Meldung: Eltern/Schüler/innen melden online, Personal nach der gewählten Herkunft.
- Funktion `record` (`schulmanager/server/absence_log.py:67`) – Hängt einen Eintrag an das Protokoll (ohne Commit). `changes`: `{feld: [vorher, nachher]}`.
- Funktion `log_level` (`schulmanager/server/absence_log.py:84`) – `full` | `presence` | `None` – siehe Moduldoku.
- Funktion `events_for` (`schulmanager/server/absence_log.py:101`)
- Funktion `events_by_absence` (`schulmanager/server/absence_log.py:113`)
- Funktion `describe` (`schulmanager/server/absence_log.py:158`) – Kurzer Text zu einem Eintrag (nur für die volle Sicht).
- Funktion `event_out` (`schulmanager/server/absence_log.py:200`) – Eintrag in der Sicht der Stufe (`presence`: nur Zeitpunkt und Kanal der Meldung).
- Funktion `timeline` (`schulmanager/server/absence_log.py:210`) – Verlauf einer Meldung: voll = alle Einträge; `presence` = nur die Meldung selbst (Zeitpunkt/Kanal).
- Funktion `first_events` (`schulmanager/server/absence_log.py:218`) – Der Eintrag „angelegt“ je Meldung (Zeitpunkt, Person, Kanal der Meldung).
- Funktion `report_info` (`schulmanager/server/absence_log.py:228`) – Wann/von wem/wie eine Meldung einging (Fallback ohne Protokoll: Felder der Meldung selbst).

## Datenbank-Tabellen

- **Nutzt:** `student_absence_events` → [[Datenmodell#Sonstige Tabellen]]

## Hängt ab von

- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Server db]] – `absence_log`, `db`
- [[Server elternzugriff]] – `absence_access`
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_absence_log]]
- [[Routen features_forms]]
- [[Routen features_register]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
