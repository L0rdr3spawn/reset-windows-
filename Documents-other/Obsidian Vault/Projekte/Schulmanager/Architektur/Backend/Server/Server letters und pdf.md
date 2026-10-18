---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/letters.py, schulmanager/server/pdf.py, schulmanager/server/pdf_simple.py"
stand: 2026-10-12 21:38
generator: schulmanager-regen
---

# Server letters und pdf

> Server-Kern · 3 Datei(en) · 1384 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Zugangsbriefe: kurzlebige, verschlüsselte Stapel mit Startpasswörtern (`letters`), eigener minimaler PDF-1.4-Schreiber (`pdf`, optional QR-Codes über `segno`) und einseitige PDFs (`pdf_simple`, z. B. Entschuldigungsformular). Endpunkte: [[Routen features_letters]], [[Routen features_student_absences]]; Oberfläche: [[Feature zugangsdaten]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/letters.py` | 902 | Zugangsbriefe als PDF (§11.3): kurzlebige, verschlüsselte Stapel mit Startpasswörtern, Briefe, ZIP,… |
| `schulmanager/server/pdf.py` | 365 | Kleiner PDF-1.4-Schreiber (nur Standardbibliothek + optional `segno` für QR-Codes) – §11.3. |
| `schulmanager/server/pdf_simple.py` | 117 | Minimaler PDF-Erzeuger (eine A4-Seite, Text in Helvetica, Linien, Kästchen) – ohne Fremdbibliothek. |

## Wichtige Funktionen und Klassen

- Funktion `batch_minutes` (`schulmanager/server/letters.py:58`) – Lebensdauer eines Stapels in Minuten (`SM_LETTER_BATCH_MINUTES`, 1…1440, Standard 60).
- Funktion `login_url` (`schulmanager/server/letters.py:67`)
- Funktion `school_name` (`schulmanager/server/letters.py:71`)
- Funktion `split_name` (`schulmanager/server/letters.py:80`) – „Vorname Nachname“ bzw. „Nachname, Vorname“ → (Vorname, Nachname); Namenszusätze (von, van, de …) gehören
- Funktion `ascii_part` (`schulmanager/server/letters.py:104`) – Teil eines Dateinamens: Umlaute umschreiben, Akzente entfernen, nur `A-Za-z0-9-` (Leerzeichen → `-`).
- Funktion `entry_filename` (`schulmanager/server/letters.py:111`) – ASCII-Dateiname wie `5a_Mustermann_Max.pdf` (Eltern: `…_Eltern.pdf`), eindeutig innerhalb `used`.
- Funktion `entry_for_user` (`schulmanager/server/letters.py:158`) – Stapel-Eintrag für ein Konto (`children` = Schüler-IDs eines Elternkontos).
- Funktion `entries_for_passwords` (`schulmanager/server/letters.py:191`) – Einträge für `{user_id: startpasswort}` (Konten werden in einem Rutsch geladen).
- Funktion `create_batch` (`schulmanager/server/letters.py:210`) – Legt einen Stapel an (ohne Commit). Einträge werden sortiert (Klasse, Name; Eltern nach dem Kind).
- Funktion `batch_ref` (`schulmanager/server/letters.py:235`)
- Funktion `batch_from_passwords` (`schulmanager/server/letters.py:241`) – Stapel zu frisch gesetzten Startpasswörtern (`{user_id: passwort}`) für `reset_password`/`bulk`.
- Funktion `load_batch` (`schulmanager/server/letters.py:256`) – Stapel lesen: nur anlegende Person oder Rolle admin (sonst 404), abgelaufen → gelöscht + 410.
- Funktion `delete_expired` (`schulmanager/server/letters.py:276`) – Abgelaufene Stapel löschen (Wartung).
- Funktion `store_initial_passwords` (`schulmanager/server/letters.py:286`) – Startpasswörter verschlüsselt am Konto speichern (ersetzt ein älteres; ohne Commit).
- Funktion `initial_password_info` (`schulmanager/server/letters.py:303`)
- Funktion `initial_password` (`schulmanager/server/letters.py:307`) – Entschlüsseltes Startpasswort oder `None` (keins gespeichert/nicht lesbar).
- Funktion `led_student_ids` (`schulmanager/server/letters.py:322`) – Schüler/innen der Klassen, die die Lehrkraft `actor` leitet (Klassenleitung).
- Funktion `can_reset` (`schulmanager/server/letters.py:335`) – Darf `actor` das Passwort eines Kontos (`role`/`student_id`) zurücksetzen?
- Funktion `check_reset` (`schulmanager/server/letters.py:355`)
- Funktion `visible_entries` (`schulmanager/server/letters.py:360`) – Einträge eines Stapels, die `actor` (noch) sehen darf.
- Funktion `reset_passwords` (`schulmanager/server/letters.py:367`) – Neue Startpasswörter (wie `POST /users/{id}/reset-password`): Passwortwechsel-Zwang, Sitzungen beendet.
- Funktion `username_base` (`schulmanager/server/letters.py:382`) – `vorname.nachname` (ASCII, Doppelnamen mit `-`).
- Funktion `plan_accounts` (`schulmanager/server/letters.py:397`) – Konten für neue Schüler/innen und ihre Eltern planen (ändert nichts). Rückgabe `(plan, warnungen)`.
- Funktion `create_planned` (`schulmanager/server/letters.py:476`) – Legt die geplanten Konten an bzw. ergänzt Kinder bei vorhandenen Elternkonten (ohne Commit).
- Funktion `policy_info` (`schulmanager/server/letters.py:539`) – `{password: bool, providers: [ids], required: [ids]}` aus `login_policy.effective_policy`.
- Funktion `letter_hints` (`schulmanager/server/letters.py:569`) – Texte für den Brief abhängig von der Richtlinie. `print_password` = Startpasswort drucken.
- Funktion `letter_title` (`schulmanager/server/letters.py:610`)
- Funktion `render_letters` (`schulmanager/server/letters.py:767`) – PDF mit einer Seite je Eintrag (Richtlinien-Hinweise je Konto).
- Funktion `zip_letters` (`schulmanager/server/letters.py:782`) – ZIP mit je einem PDF pro Eintrag (eindeutige ASCII-Dateinamen).
- Funktion `email_message` (`schulmanager/server/letters.py:794`) – Betreff und Text einer E-Mail mit dem Brief im Anhang (ohne Passwort im Text).
- Funktion `is_adult_student` (`schulmanager/server/letters.py:838`) – Volljährige Schülerin/volljähriger Schüler (Stand im Stapel oder aktuell am Konto)?
- Funktion `send_entries` (`schulmanager/server/letters.py:843`) – Je Person eine E-Mail mit ihrem Brief (PDF) über `auth_messages.queue_email` (ohne Commit).
- Funktion `kick_outbox` (`schulmanager/server/letters.py:895`)
- Funktion `encode` (`schulmanager/server/pdf.py:81`) – Text → cp1252-Bytes (WinAnsiEncoding). Nicht darstellbare Zeichen werden ersetzt: bekannte Sonderzeichen
- Funktion `text_width` (`schulmanager/server/pdf.py:100`) – Breite von `text` in Punkt (nach der Ersetzung durch ``).
- Funktion `wrap` (`schulmanager/server/pdf.py:109`) – Bricht `text` an Leerzeichen in Zeilen ≤ `width` um (zu lange Wörter werden geteilt).
- Funktion `qr_matrix` (`schulmanager/server/pdf.py:174`) – QR-Code-Module (True = dunkel) ohne Ruhezone; braucht `segno`.
- Klasse `Page` (`schulmanager/server/pdf.py:203`) – Eine Seite; Zeichenbefehle werden als Inhaltsstrom gesammelt.
  - Methoden: `text`:215, `text_right`:227, `text_center`:232, `paragraph`:237, `line`:248, `rect`:253, `qr`:262, `content`:273
- Klasse `Document` (`schulmanager/server/pdf.py:277`) – PDF-Dokument aus Seiten (``), Ausgabe mit ``.
  - Methoden: `add_page`:288, `output`:307
- Funktion `text_width` (`schulmanager/server/pdf_simple.py:19`) – Grobe Breite (Helvetica-Mittelwert) – reicht für Umbrüche in Formularen.
- Klasse `Page` (`schulmanager/server/pdf_simple.py:25`)
  - Methoden: `text`:29, `line`:33, `box`:36, `para`:43, `field`:61, `check`:71
- Funktion `render` (`schulmanager/server/pdf_simple.py:83`) – PDF-Datei aus Seiten erzeugen.

## Datenbank-Tabellen

- **Nutzt:** `account_initial_passwords`, `letter_batches`, `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server config]] – `config`
- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`, `letters`
- [[Server konten und anmeldung]] – `accounts`, `auth_messages`, `identities`, `login_policy`, `security` *(nur zur Laufzeit importiert)*
- [[Server notify]] – `notify` *(nur zur Laufzeit importiert)*
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_classes]]
- [[Routen features_letters]]
- [[Routen features_student_absences]]
- [[Routen users]]
- [[Server betrieb]] – `maintenance`
- [[Server form_pdf]]

## Tests

`tests/test_letters.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
