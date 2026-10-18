---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/form_pdf.py"
stand: 2026-10-12 21:41
generator: schulmanager-regen
---

# Server form_pdf

> Server-Kern · 1 Datei(en) · 225 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

PDF-Ausgabe des Formular-Baukastens: leer zum Ausdrucken oder ausgefüllt zum Archiv (mehrseitig, A4).

Baut auf `` auf (Helvetica, WinAnsi). Nicht darstellbare Zeichen werden zu `?`.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/form_pdf.py` | 225 | PDF-Ausgabe des Formular-Baukastens: leer zum Ausdrucken oder ausgefüllt zum Archiv (mehrseitig, A4… |

## Wichtige Funktionen und Klassen

- Funktion `render_form` (`schulmanager/server/form_pdf.py:201`) – Formular als PDF. Ohne `answers` leer zum Ausdrucken (Schreiblinien, Kästchen), sonst ausgefüllt.
- Funktion `render_forms` (`schulmanager/server/form_pdf.py:214`) – Mehrere ausgefüllte Formulare in einem PDF (jedes beginnt auf einer neuen Seite). `items`: Argumente von

## Hängt ab von

- [[Modul forms]] – `forms`
- [[Server letters und pdf]] – `pdf_simple`

## Wird genutzt von

- [[Routen features_forms]]

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
