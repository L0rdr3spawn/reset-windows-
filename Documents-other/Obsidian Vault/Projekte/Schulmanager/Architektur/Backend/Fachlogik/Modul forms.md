---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/forms.py"
stand: 2026-10-12 21:44
generator: schulmanager-regen
---

# Modul forms

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 569 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Formular-Baukasten – reine Logik ohne Datenbank (Doku: docs/FORMULARE.md).

* `` prüft und bereinigt die Beschreibung eines Formulars (Felder, Zielgruppe, Ablauf,
  Fristen, Aktionen) – was ein Browser schickt, wird nie ungeprüft gespeichert.
* `` prüft die Antworten einer Einreichung gegen genau diese Fassung.
* `` – fertige Vorlagen für Schulen (Beurlaubung, Entschuldigung, Einverständnisse …).
* `` schützt CSV-Exporte vor Formel-Einschleusung.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/forms.py` | 569 | Formular-Baukasten – reine Logik ohne Datenbank (Doku: docs/FORMULARE.md). |

## Wichtige Funktionen und Klassen

- Klasse `FormError` (`schulmanager/forms.py:58`) – Ungültige Formularbeschreibung oder ungültige Antworten (Text ist für Nutzer/innen gedacht).
- Funktion `clean_text` (`schulmanager/forms.py:63`)
- Funktion `csv_cell` (`schulmanager/forms.py:97`) – CSV-Zelle ohne Formel-Einschleusung (`=`, `+`, `-`, `@`, Tab am Anfang werden entschärft).
- Funktion `normalize_definition` (`schulmanager/forms.py:244`) – Prüft und bereinigt die Beschreibung eines Formulars (`FormError` mit deutschem Text bei Fehlern).
- Funktion `has_student_field` (`schulmanager/forms.py:278`)
- Funktion `field_by_id` (`schulmanager/forms.py:282`)
- Funktion `clean_answers` (`schulmanager/forms.py:291`) – Antworten prüfen und bereinigen. `student_id` füllt das Feld „Schüler/in“ (vom Server geprüft), `today`
- Funktion `display_value` (`schulmanager/forms.py:419`) – Antwort als Text (PDF, CSV, Listen).
- Funktion `fmt_date` (`schulmanager/forms.py:444`)
- Funktion `in_window` (`schulmanager/forms.py:452`) – Ist das Formular heute zum Ausfüllen offen (Frist „ab“/„bis“)?
- Funktion `class_in_target` (`schulmanager/forms.py:460`)
- Funktion `due_date` (`schulmanager/forms.py:470`)
- Funktion `library_entry` (`schulmanager/forms.py:567`)

## Hängt ab von

- –

## Wird genutzt von

- [[Routen features_forms]]
- [[Server form_pdf]]

## Tests

`tests/test_forms.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
