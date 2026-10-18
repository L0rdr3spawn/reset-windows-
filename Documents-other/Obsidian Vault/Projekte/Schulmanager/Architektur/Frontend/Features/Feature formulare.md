---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/formulare/"
stand: 2026-10-12 22:26
generator: schulmanager-regen
---

# Feature formulare

> Frontend · 12 Datei(en) · 2370 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Feature-Modul „Formulare“ (Formular-Baukasten) für die Registry (`features/registry.ts`). * `/formulare` – ausfüllen (Eltern, Schüler, Lehrkräfte), Eingang (Klassenleitung, Sekretariat, Schulleitung), Vorlagen und Bibliothek (Verwaltung). * `/formulare/vorlage/:id` – Baukasten (nur `forms.manage`). * Startseiten-Kachel, wenn etwas wartet.

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/formulare` | `FormsPage` | anyOf: ['forms.submit', 'forms.inbox', 'forms.manage'] | Formulare |
| `/formulare/vorlage/:id` | `TemplateEditor` | anyOf: ['forms.manage'] | Formular bearbeiten |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/formulare/FillDialog.tsx` | 118 | Formular online ausfüllen (Handy-tauglich) – oder leer als PDF zum Ausdrucken öffnen. |
| `frontend/src/features/formulare/FormFields.tsx` | 201 | Eingabefelder eines Formulars (Ausfüllen und Vorschau im Baukasten) – eine Spalte, große Berührflächen, Handy-tauglich. |
| `frontend/src/features/formulare/FormsPage.tsx` | 370 | `/formulare` – Formular-Baukasten: Familien/Schüler/Lehrkräfte füllen aus („Ausfüllen“, „Meine Formulare“), Klassenleitung, Sekre… |
| `frontend/src/features/formulare/FormsWidget.tsx` | 36 |  |
| `frontend/src/features/formulare/SubmissionDetail.tsx` | 202 | Einreichung ansehen: Antworten, Ablauf, Verlauf, Scans/Anhänge, Entscheidung (Genehmigen/Ablehnen/Erledigt) und PDF. |
| `frontend/src/features/formulare/TemplateEditor.tsx` | 519 | Formular-Baukasten (`/formulare/vorlage/:id`): Felder, Zielgruppe, Ablauf, Fristen, Aktionen, Vorschau. Änderungen an Felder/Abla… |
| `frontend/src/features/formulare/api.ts` | 297 | Formular-Baukasten (`/forms`, siehe schulmanager/server/routes/features_forms.py und docs/FORMULARE.md). |
| `frontend/src/features/formulare/badge.tsx` | 25 | Menü-Badge der Formulare: Eingang = Einreichungen, die auf die eigene Entscheidung warten; Familien = erwartete Rückmeldungen (Ei… |
| `frontend/src/features/formulare/components.tsx` | 42 | Kleine gemeinsame Bausteine des Formular-Baukastens: Status-Abzeichen und Liste von Einreichungen. |
| `frontend/src/features/formulare/formulare.css` | 307 | Stylesheet |
| `frontend/src/features/formulare/logic.ts` | 216 | Reine Hilfen des Formular-Baukastens (ohne React): Vorlagen-Gerüst, Felder bearbeiten, Antworten vorbereiten und vorab prüfen (de… |
| `frontend/src/features/formulare/module.tsx` | 37 | Feature-Modul „Formulare“ (Formular-Baukasten) für die Registry (`features/registry.ts`). * `/formulare` – ausfüllen (Eltern, Sch… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/forms/approvers` | [[Routen features_forms]] · `forms_approvers` (`features_forms.py:363`) |
| GET | `/forms/available` | [[Routen features_forms]] · `available_forms` (`features_forms.py:705`) |
| GET | `/forms/library` | [[Routen features_forms]] · `library` (`features_forms.py:557`) |
| POST | `/forms/library/{…}/adopt` | [[Routen features_forms]] · `adopt_library` (`features_forms.py:566`) |
| GET | `/forms/meta` | [[Routen features_forms]] · `forms_meta` (`features_forms.py:348`) |
| GET | `/forms/submissions` | [[Routen features_forms]] · `list_submissions` (`features_forms.py:1000`) |
| GET | `/forms/submissions/{…}` | [[Routen features_forms]] · `get_submission` (`features_forms.py:1033`) |
| POST | `/forms/submissions/{…}/decide` | [[Routen features_forms]] · `decide` (`features_forms.py:1046`) |
| POST | `/forms/submissions/{…}/retry-actions` | [[Routen features_forms]] · `retry_actions` (`features_forms.py:1102`) |
| POST | `/forms/submissions/{…}/scan` | [[Routen features_forms]] · `add_scan` (`features_forms.py:1146`) |
| DELETE | `/forms/submissions/{…}/scan/{…}` | [[Routen features_forms]] · `remove_scan` (`features_forms.py:1165`) |
| POST | `/forms/submissions/{…}/withdraw` | [[Routen features_forms]] · `withdraw` (`features_forms.py:1125`) |
| GET | `/forms/summary` | [[Routen features_forms]] · `summary` (`features_forms.py:1267`) |
| GET | `/forms/templates` | [[Routen features_forms]] · `list_templates` (`features_forms.py:417`) |
| POST | `/forms/templates` | [[Routen features_forms]] · `create_template` (`features_forms.py:438`) |
| DELETE | `/forms/templates/{…}` | [[Routen features_forms]] · `delete_template` (`features_forms.py:542`) |
| GET | `/forms/templates/{…}` | [[Routen features_forms]] · `get_template` (`features_forms.py:454`) |
| PUT | `/forms/templates/{…}` | [[Routen features_forms]] · `update_template` (`features_forms.py:467`) |
| POST | `/forms/templates/{…}/duplicate` | [[Routen features_forms]] · `duplicate_template` (`features_forms.py:525`) |
| GET | `/forms/templates/{…}/fill` | [[Routen features_forms]] · `fill_info` (`features_forms.py:725`) |
| POST | `/forms/templates/{…}/status` | [[Routen features_forms]] · `set_template_status` (`features_forms.py:510`) |
| POST | `/forms/templates/{…}/submit` | [[Routen features_forms]] · `submit_form` (`features_forms.py:768`) |

## Backend-Notizen

[[Routen features_forms]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `files`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `FileList`, `FileUpload`, `Help`, `HelpTip`, `Icon` …

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)


## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
