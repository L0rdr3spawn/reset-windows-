---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/channels/"
stand: 2026-10-12 22:51
generator: schulmanager-regen
---

# Feature channels

> Frontend · 22 Datei(en) · 6764 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Kursräume (`/kursraeume`, `/kursraeume/:id`): Material in Ordnern, Aufgaben mit Abgabe und Rückmeldung (Hausaufgaben), Pinnwand, Unterricht-Reiter (Klassenbuch-Thema, Termine), Mitglieder, Sichtbarkeit nach Zeitpunkt oder Stunde, Markdown-Textseiten.

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/kursraeume` | `ChannelListPage` | anyOf: ['channels.use', 'channels.manage', 'channels.view_children'] | Kursräume |
| `/kursraeume/:id` | `ChannelPage` | anyOf: ['channels.use', 'channels.manage', 'channels.view_children'] | Kursraum |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/channels/AssignmentsTab.tsx` | 636 | Bereich „Aufgaben“: Lehrende legen Aufgaben an (Beschreibung, Frist, Anhänge, Freigabe), sehen alle Abgaben und geben Rückmeldung… |
| `frontend/src/features/channels/BoardTab.tsx` | 272 | Bereich „Pinnwand“: Beiträge mit einer Ebene Antworten, Anheften (Lehrende), eigene Beiträge bearbeiten, Moderation (Lehrende lös… |
| `frontend/src/features/channels/ChannelListPage.tsx` | 278 | `/kursraeume` – eigene Kursräume (Kursteile, Klassen, eigene) mit Suche nach Kurs/Klasse/Fach/Lehrkraft; Schulleitung/Admin: alle… |
| `frontend/src/features/channels/ChannelPage.tsx` | 241 | `/kursraeume/:id` – ein Kursraum mit den Bereichen Material (Ordner, Dateien, Links, Textseiten, Freigaben), Aufgaben (Abgabe/Rüc… |
| `frontend/src/features/channels/ClassTab.tsx` | 505 | Bereich „Klasse“ (Startansicht des Klassenraums): Regelplan der Klasse, Termine/Elternabende, angeheftete Infokarten (gepflegt vo… |
| `frontend/src/features/channels/MarkdownView.tsx` | 76 | Anzeige von Markdown-Text (siehe `markdown.ts`) – nur React-Elemente, Links in neuem Tab ohne Referrer. |
| `frontend/src/features/channels/MaterialTab.tsx` | 562 | Bereich „Material“: Ordnerbaum + Liste, Hochladen von Dateien und ganzen Ordnern (Auswahl oder Drag & Drop auf die ganze Liste, s… |
| `frontend/src/features/channels/MaterialUpload.tsx` | 399 | Hochladen ins Material in **einem** Schritt (A-45): einzelne Dateien und ganze Ordner (Auswahl mit Unterordnern oder Drag & Drop)… |
| `frontend/src/features/channels/MembersTab.tsx` | 286 | Bereich „Teilnehmende“: Lehrende, Teilnehmende (Stundenplan + eingetragen), ausgetragene Schüler/innen und Eltern. Lehrende des K… |
| `frontend/src/features/channels/UnterrichtTab.tsx` | 211 | Bereich „Unterricht“: die Stunden, die stattgefunden haben (Entfall nicht, Verlegungen am tatsächlichen Tag) – je Stunde das Unte… |
| `frontend/src/features/channels/VisibilityPicker.tsx` | 191 | Sichtbarkeit wählen: sofort, verborgen, ab Zeitpunkt, **zur nächsten Stunde** oder **zur Unterrichtsstunde** (sichtbar ab Stunden… |
| `frontend/src/features/channels/api.ts` | 188 | Endpunkte der Kursräume (§9.4). Dateien werden vorher über `uploadFile` (`src/api/files.ts`) hochgeladen – Zwecke `channel_materi… |
| `frontend/src/features/channels/badge.tsx` | 20 | Unsichtbare Hintergrund-Komponente: Zahl „neue Inhalte“ (Material + Beiträge) am Menüeintrag „Kursräume“. |
| `frontend/src/features/channels/channels.css` | 884 | Stylesheet |
| `frontend/src/features/channels/classInfo.ts` | 42 | Reine Hilfen für den Bereich „Klasse“ des Klassenraums (siehe ClassTab.tsx). |
| `frontend/src/features/channels/components.tsx` | 71 | Kleine Bausteine der Kursräume: Symbole, Status-Abzeichen, Rollen-Abzeichen. |
| `frontend/src/features/channels/dialogs.tsx` | 528 | Dialoge der Kursräume: Ordner anlegen/umbenennen, Link/Textseite anlegen, Material bearbeiten, Sichtbarkeit/„Zur Stunde freigeben… |
| `frontend/src/features/channels/logic.ts` | 358 | Reine Hilfsfunktionen der Kursräume (ohne React, mit vitest getestet): Ordnerbaum, Sortierung, Texte zu Sichtbarkeit/Fristen/Stat… |
| `frontend/src/features/channels/markdown.ts` | 201 | Kleiner, sicherer Markdown-Leser für Textseiten, Aufgaben und Rückmeldungen (ohne HTML, ohne Bibliothek): Überschriften (#–###),… |
| `frontend/src/features/channels/module.tsx` | 49 | Feature-Modul „Kursräume“ (ARCHITECTURE.md §9.4) für die Registry (`features/registry.ts`). * `/kursraeume` – eigene Kursräume (K… |
| `frontend/src/features/channels/types.ts` | 477 | Antworttypen der Kursraum-Endpunkte (`schulmanager/server/routes/features_channels.py`, ARCHITECTURE.md §9.4). Zeitpunkte sind IS… |
| `frontend/src/features/channels/widgets.tsx` | 289 | Startseiten-Kacheln der Kursräume (werden erst bei Bedarf geladen, siehe module.tsx): * Schüler/innen: „Neues Material & fällige… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/channels/{}/klasse/absences` | [[Routen features_absence_log]] · `class_absences` (`features_absence_log.py:55`) |
| GET | `/channels` | [[Routen features_channels]] · `list_channels` (`features_channels.py:1462`) |
| POST | `/channels` | [[Routen features_channels]] · `create_channel` (`features_channels.py:1570`) |
| GET | `/channels/overview` | [[Routen features_channels]] · `channels_overview` (`features_channels.py:1411`) |
| DELETE | `/channels/{}` | [[Routen features_channels]] · `delete_channel` (`features_channels.py:1672`) |
| GET | `/channels/{}` | [[Routen features_channels]] · `get_channel` (`features_channels.py:1592`) |
| PATCH | `/channels/{}` | [[Routen features_channels]] · `patch_channel` (`features_channels.py:1621`) |
| POST | `/channels/{}/copy` | [[Routen features_channels]] · `copy_material` (`features_channels.py:2540`) |
| DELETE | `/channels/{}/excluded/{…}` | [[Routen features_channels]] · `readmit_member` (`features_channels.py:1977`) |
| POST | `/channels/{}/folders` | [[Routen features_channels]] · `create_folder` (`features_channels.py:2024`) |
| DELETE | `/channels/{}/folders/{…}` | [[Routen features_channels]] · `delete_folder` (`features_channels.py:2162`) |
| PATCH | `/channels/{}/folders/{…}` | [[Routen features_channels]] · `patch_folder` (`features_channels.py:2117`) |
| POST | `/channels/{}/items` | [[Routen features_channels]] · `create_item` (`features_channels.py:2252`) |
| DELETE | `/channels/{}/items/{…}` | [[Routen features_channels]] · `delete_item` (`features_channels.py:2490`) |
| GET | `/channels/{}/items/{…}` | [[Routen features_channels]] · `get_item` (`features_channels.py:2342`) |
| PATCH | `/channels/{}/items/{…}` | [[Routen features_channels]] · `patch_item` (`features_channels.py:2358`) |
| DELETE | `/channels/{}/items/{…}/submission` | [[Routen features_channels]] · `withdraw` (`features_channels.py:3058`) |
| GET | `/channels/{}/items/{…}/submission` | [[Routen features_channels]] · `my_submission` (`features_channels.py:2986`) |
| PUT | `/channels/{}/items/{…}/submission` | [[Routen features_channels]] · `submit` (`features_channels.py:3008`) |
| GET | `/channels/{}/items/{…}/submissions` | [[Routen features_channels]] · `list_submissions` (`features_channels.py:3082`) |
| POST | `/channels/{}/items/{…}/viewed` | [[Routen features_channels]] · `mark_viewed` (`features_channels.py:2825`) |
| POST | `/channels/{}/items/files` | [[Routen features_channels]] · `create_file_items` (`features_channels.py:2305`) |
| POST | `/channels/{}/items/visibility` | [[Routen features_channels]] · `set_visibility` (`features_channels.py:2451`) |
| GET | `/channels/{}/lessons` | [[Routen features_channels]] · `upcoming` (`features_channels.py:2745`) |
| GET | `/channels/{}/member-candidates` | [[Routen features_channels]] · `member_candidates` (`features_channels.py:1826`) |
| GET | `/channels/{}/members` | [[Routen features_channels]] · `list_members` (`features_channels.py:1748`) |
| POST | `/channels/{}/members` | [[Routen features_channels]] · `add_members` (`features_channels.py:1868`) |
| DELETE | `/channels/{}/members/{…}` | [[Routen features_channels]] · `remove_member` (`features_channels.py:1931`) |
| GET | `/channels/{}/posts` | [[Routen features_channels]] · `list_posts` (`features_channels.py:3226`) |
| POST | `/channels/{}/posts` | [[Routen features_channels]] · `create_post` (`features_channels.py:3263`) |
| DELETE | `/channels/{}/posts/{…}` | [[Routen features_channels]] · `delete_post` (`features_channels.py:3332`) |
| PATCH | `/channels/{}/posts/{…}` | [[Routen features_channels]] · `patch_post` (`features_channels.py:3303`) |
| POST | `/channels/{}/seen` | [[Routen features_channels]] · `mark_seen` (`features_channels.py:1701`) |
| PUT | `/channels/{}/submissions/{…}/feedback` | [[Routen features_channels]] · `give_feedback` (`features_channels.py:3145`) |
| GET | `/channels/{}/unterricht` | [[Routen features_channels]] · `lesson_log` (`features_channels.py:2840`) |
| GET | `/channels/{}/klasse` | [[Routen features_class_info]] · `class_overview` (`features_class_info.py:130`) |
| GET | `/channels/{}/klasse/plan` | [[Routen features_class_info]] · `class_plan` (`features_class_info.py:147`) |
| POST | `/channels/{}/klasse/termine` | [[Routen features_class_info]] · `add_event` (`features_class_info.py:166`) |
| DELETE | `/channels/{}/klasse/termine/{…}` | [[Routen features_class_info]] · `delete_event` (`features_class_info.py:198`) |

## Backend-Notizen

[[Routen features_absence_log]], [[Routen features_channels]], [[Routen features_class_info]]

## Nutzt (Frontend)

- [[Feature students]] – `AbsenceHistory`
- [[Frontend API-Schicht]] – `client`, `files`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `Abbr`, `FileList`, `FileUpload`, `Help`, `HelpTip` …

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)


## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
