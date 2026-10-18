---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/autoplan.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server autoplan

> Server-Kern · 1 Datei(en) · 407 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Hintergrunddienst des Auto-Planers: hört auf planungsrelevante `change`-Ereignisse (`TRIGGER_SCOPES`), prüft nach `SM_AUTOPLAN_DELAY` Sekunden Ruhe mit [[Modul autoplan]] und startet bei Bedarf einen Generator-Job der Art `autoplan` über [[Server jobs]]. Das Ergebnis wird automatisch übernommen, wenn der Plan besser wird (Scope `autoplan`, rückgängig über den Verlauf). Abschaltbar je Schule und global (`SM_AUTOPLAN=0`).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/autoplan.py` | 407 | Auto-Planer: hält den regulären Stundenplan nach jeder Änderung automatisch gültig. |

## Wichtige Funktionen und Klassen

- Klasse `AutoPlanner` (`schulmanager/server/autoplan.py:45`)
  - Methoden: `start`:57, `stop`:68, `enabled`:78, `schedule`:100, `run_now`:111, `job_finished`:229, `status`:390
- Funktion `start` (`schulmanager/server/autoplan.py:401`)
- Funktion `stop` (`schulmanager/server/autoplan.py:405`)

## Hängt ab von

- [[Modul autoplan]] – `autoplan` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models` *(nur zur Laufzeit importiert)*
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server jobs]] – `jobs` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_planning]]
- [[Server jobs]]

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
