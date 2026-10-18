---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/legacy.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul legacy

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 201 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Umrechnung älterer Planungsdokumente auf das 52-Wochen-System: `migrate_document` wandelt Zykluswochen (`cycle_weeks`, `cycle_start_week`, `cycle_shifts`) verlustfrei in `weeks`/`rhythm` laufender Wochen um und ist idempotent; `strip_legacy_fields` lässt ältere Clients alte Felder noch senden. Wird von [[Modul models]] beim Laden aufgerufen. Neu im Arbeitsstand (noch nicht committet).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/legacy.py` | 201 | Umrechnung älterer Planungsdokumente auf das 52-Wochen-System. |

## Wichtige Funktionen und Klassen

- Funktion `strip_legacy_fields` (`schulmanager/legacy.py:29`) – Entfernt veraltete Zyklusfelder aus einem Request-Wörterbuch (in place) und liefert es zurück.
- Funktion `weeks_to_spec` (`schulmanager/legacy.py:83`) – Wochenliste im Zyklus `n` (0-basiert, Phase `phase`) → `(weeks, rhythm)` in laufenden Wochen.
- Funktion `is_legacy` (`schulmanager/legacy.py:97`)
- Funktion `migrate_document` (`schulmanager/legacy.py:102`) – Altes Dokument (Zykluswochen) → neues Dokument (laufende Wochen). Liefert eine umgerechnete Kopie; Dokumente
- Funktion `migrate_profile_payload` (`schulmanager/legacy.py:179`) – Offener Profilantrag aus der Zeit des Wochenzyklus (Feld `cycle_weeks` im Antrag) → laufende Wochen.

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Modul integrations]] – `untis_gpu`
- [[Modul models]]
- [[Routen features_data]]
- [[Routen features_teacher_profile]]

## Tests

`tests/test_weeks.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
