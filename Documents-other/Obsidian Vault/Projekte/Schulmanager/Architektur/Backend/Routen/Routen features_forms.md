---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_forms.py"
stand: 2026-10-12 22:26
generator: schulmanager-regen
---

# Routen features_forms

> API-Routen · 1 Datei(en) · 1353 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Formular-Baukasten: Vorlagen, Ausfüllen, Genehmigung, PDF, Export (Doku: docs/FORMULARE.md).

Rechte (`permissions.py`) --------------------------- * `forms.manage` (Administration, Schulleitung, Sekretariat) – Vorlagen anlegen/ändern/archivieren, Ablauf und Aktionen festlegen, Bibliothek übernehmen. **Kein** Einblick in ausgefüllte Formulare. * `forms.inbox` (Schulleitung, Sekretariat; Lehrkräfte/Abteilungsleitung nur als Klassenleitung der eigenen Klasse) – Eingang: Einreichungen ansehen, genehmigen/ablehnen, Scans, Export. Nie für die technische Administration. * `forms.submit` (Eltern, Schüler/innen, Lehrkräfte, Sekretariat, Schulleitung) – ausfüllen; **welche** Formulare, bestimmt die Zielgruppe des Formulars (Rollen, Klassen/Jahrgänge).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_forms.py` | 1353 | Formular-Baukasten: Vorlagen, Ausfüllen, Genehmigung, PDF, Export (Doku: docs/FORMULARE.md). |

## Endpunkte (27)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/forms/meta` | `forms_meta` (`features_forms.py:348`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/approvers` | `forms_approvers` (`features_forms.py:363`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/templates` | `list_templates` (`features_forms.py:417`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/templates` | `create_template` (`features_forms.py:438`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/templates/{template_id}` | `get_template` (`features_forms.py:454`) | (angemeldet) | [[Feature formulare]] |
| PUT | `/api/v1/forms/templates/{template_id}` | `update_template` (`features_forms.py:467`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/templates/{template_id}/status` | `set_template_status` (`features_forms.py:510`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/templates/{template_id}/duplicate` | `duplicate_template` (`features_forms.py:525`) | (angemeldet) | [[Feature formulare]] |
| DELETE | `/api/v1/forms/templates/{template_id}` | `delete_template` (`features_forms.py:542`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/library` | `library` (`features_forms.py:557`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/library/{key}/adopt` | `adopt_library` (`features_forms.py:566`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/templates/{template_id}/blank.pdf` | `blank_pdf` (`features_forms.py:600`) | (angemeldet) | – |
| POST | `/api/v1/forms/preview.pdf` | `preview_pdf` (`features_forms.py:619`) | (angemeldet) | – |
| GET | `/api/v1/forms/submissions/{sub_id}/pdf` | `submission_pdf` (`features_forms.py:673`) | (angemeldet) | – |
| GET | `/api/v1/forms/available` | `available_forms` (`features_forms.py:705`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/templates/{template_id}/fill` | `fill_info` (`features_forms.py:725`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/templates/{template_id}/submit` | `submit_form` (`features_forms.py:768`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/submissions` | `list_submissions` (`features_forms.py:1000`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/submissions/{sub_id}` | `get_submission` (`features_forms.py:1033`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/submissions/{sub_id}/decide` | `decide` (`features_forms.py:1046`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/submissions/{sub_id}/retry-actions` | `retry_actions` (`features_forms.py:1102`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/submissions/{sub_id}/withdraw` | `withdraw` (`features_forms.py:1125`) | (angemeldet) | [[Feature formulare]] |
| POST | `/api/v1/forms/submissions/{sub_id}/scan` | `add_scan` (`features_forms.py:1146`) | (angemeldet) | [[Feature formulare]] |
| DELETE | `/api/v1/forms/submissions/{sub_id}/scan/{file_id}` | `remove_scan` (`features_forms.py:1165`) | (angemeldet) | [[Feature formulare]] |
| GET | `/api/v1/forms/export.csv` | `export_csv` (`features_forms.py:1222`) | (angemeldet) | – |
| GET | `/api/v1/forms/export.pdf` | `export_pdf` (`features_forms.py:1243`) | (angemeldet) | – |
| GET | `/api/v1/forms/summary` | `summary` (`features_forms.py:1267`) | (angemeldet) | [[Feature formulare]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `Ctx` (`schulmanager/server/routes/features_forms.py:83`) – Rechte und Datenumfang eines Kontos für Formulare (je Anfrage).
- Funktion `fill_students` (`schulmanager/server/routes/features_forms.py:238`) – Schüler/innen, für die das Konto das Formular ausfüllen darf (Zielgruppe berücksichtigt); `None` = das Konto
- Klasse `TemplateIn` (`schulmanager/server/routes/features_forms.py:375`)
- Klasse `StatusIn` (`schulmanager/server/routes/features_forms.py:505`)
- Klasse `PreviewIn` (`schulmanager/server/routes/features_forms.py:612`)
- Klasse `SubmitIn` (`schulmanager/server/routes/features_forms.py:740`)
- Funktion `approver_user_ids` (`schulmanager/server/routes/features_forms.py:833`) – Konten, die den aktuellen Prüfschritt bearbeiten können (für Live-Hinweise); die Schulleitung immer.
- Funktion `family_user_ids` (`schulmanager/server/routes/features_forms.py:854`)
- Klasse `DecideIn` (`schulmanager/server/routes/features_forms.py:1040`)
- Klasse `ScanIn` (`schulmanager/server/routes/features_forms.py:1141`)
- Funktion `run_reminders` (`schulmanager/server/routes/features_forms.py:1299`) – Erinnerung an die Prüfenden: offene Einreichungen, deren Vorlage eine Erinnerung (`remind_days`) kennt und die
- Funktion `run_retention` (`schulmanager/server/routes/features_forms.py:1323`) – Wartung: abgeschlossene Einreichungen älter als `days` Tage samt Dateien löschen; 0 = aus.
- Funktion `export_rows` (`schulmanager/server/routes/features_forms.py:1340`) – DSGVO-Export: eigene Einreichungen (Antworten als Text).

## Datenbank-Tabellen

- **Nutzt:** `form_events`, `form_submissions`, `form_templates`, `form_versions` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul forms]] – `forms`
- [[Modul models]] – `models` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_data]] – `features_data` *(nur zur Laufzeit importiert)*
- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Routen features_student_self]] – `features_student_self` *(nur zur Laufzeit importiert)*
- [[Server absence_log]] – `absence_log` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`, `forms`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `absence_access`, `parent_access` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server files]] – `files`
- [[Server form_pdf]] – `form_pdf` *(nur zur Laufzeit importiert)*
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen me]]
- [[Server betrieb]] – `maintenance`

## Tests

`tests/test_forms.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
