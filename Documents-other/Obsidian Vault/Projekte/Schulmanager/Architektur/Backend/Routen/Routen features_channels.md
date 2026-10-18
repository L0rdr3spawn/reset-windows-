---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_channels.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Routen features_channels

> API-Routen · 1 Datei(en) · 3458 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Kursräume (ARCHITECTURE.md §9.4) – Kanäle je Kursteil und Klasse mit Ordnern, Material, Freigabe zur Unterrichtsstunde, Aufgaben mit Abgabe und Rückmeldung, Pinnwand und Teilnehmenden.

Eigene Umsetzung der Moodle-Konzepte (Kurs → Abschnitte/Ordner, Material, Verfügbarkeit, Aufgaben, Forum, Teilnehmerliste) – **kein Moodle-Code**.

Rollen im Kanal (bei jedem Zugriff dynamisch aus Planungsdokument + Konto, Logik in `schulmanager/channels.py`):

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_channels.py` | 3458 | Kursräume (ARCHITECTURE.md §9.4) – Kanäle je Kursteil und Klasse mit Ordnern, Material, Freigabe zur |

## Endpunkte (37)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/channels/overview` | `channels_overview` (`features_channels.py:1411`) | (angemeldet) | [[Feature channels]], [[Feature students]] |
| GET | `/api/v1/channels` | `list_channels` (`features_channels.py:1462`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels` | `create_channel` (`features_channels.py:1570`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}` | `get_channel` (`features_channels.py:1592`) | (angemeldet) | [[Feature channels]] |
| PATCH | `/api/v1/channels/{channel_id}` | `patch_channel` (`features_channels.py:1621`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}` | `delete_channel` (`features_channels.py:1672`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/seen` | `mark_seen` (`features_channels.py:1701`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/members` | `list_members` (`features_channels.py:1748`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/member-candidates` | `member_candidates` (`features_channels.py:1826`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/members` | `add_members` (`features_channels.py:1868`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/members/{user_id}` | `remove_member` (`features_channels.py:1931`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/excluded/{user_id}` | `readmit_member` (`features_channels.py:1977`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/folders` | `create_folder` (`features_channels.py:2024`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/folders/tree` | `create_folder_tree` (`features_channels.py:2055`) | (angemeldet) | – |
| PATCH | `/api/v1/channels/{channel_id}/folders/{folder_id}` | `patch_folder` (`features_channels.py:2117`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/folders/{folder_id}` | `delete_folder` (`features_channels.py:2162`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/reorder` | `reorder` (`features_channels.py:2202`) | (angemeldet) | – |
| POST | `/api/v1/channels/{channel_id}/items` | `create_item` (`features_channels.py:2252`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/items/files` | `create_file_items` (`features_channels.py:2305`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/items/{item_id}` | `get_item` (`features_channels.py:2342`) | (angemeldet) | [[Feature channels]] |
| PATCH | `/api/v1/channels/{channel_id}/items/{item_id}` | `patch_item` (`features_channels.py:2358`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/items/visibility` | `set_visibility` (`features_channels.py:2451`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/items/{item_id}` | `delete_item` (`features_channels.py:2490`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/copy` | `copy_material` (`features_channels.py:2540`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/zip` | `download_zip` (`features_channels.py:2670`) | (angemeldet) | – |
| GET | `/api/v1/channels/{channel_id}/lessons` | `upcoming` (`features_channels.py:2745`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/items/{item_id}/viewed` | `mark_viewed` (`features_channels.py:2825`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/unterricht` | `lesson_log` (`features_channels.py:2840`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/items/{item_id}/submission` | `my_submission` (`features_channels.py:2986`) | (angemeldet) | [[Feature channels]] |
| PUT | `/api/v1/channels/{channel_id}/items/{item_id}/submission` | `submit` (`features_channels.py:3008`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/items/{item_id}/submission` | `withdraw` (`features_channels.py:3058`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/items/{item_id}/submissions` | `list_submissions` (`features_channels.py:3082`) | (angemeldet) | [[Feature channels]] |
| PUT | `/api/v1/channels/{channel_id}/submissions/{submission_id}/feedback` | `give_feedback` (`features_channels.py:3145`) | (angemeldet) | [[Feature channels]] |
| GET | `/api/v1/channels/{channel_id}/posts` | `list_posts` (`features_channels.py:3226`) | (angemeldet) | [[Feature channels]] |
| POST | `/api/v1/channels/{channel_id}/posts` | `create_post` (`features_channels.py:3263`) | (angemeldet) | [[Feature channels]] |
| PATCH | `/api/v1/channels/{channel_id}/posts/{post_id}` | `patch_post` (`features_channels.py:3303`) | (angemeldet) | [[Feature channels]] |
| DELETE | `/api/v1/channels/{channel_id}/posts/{post_id}` | `delete_post` (`features_channels.py:3332`) | (angemeldet) | [[Feature channels]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `LessonRef` (`schulmanager/server/routes/features_channels.py:124`) – Unterrichtsstunde für die Freigabe „zur Stunde“ (`period` = geplanter Beginn, 0-basiert).
- Klasse `ChannelIn` (`schulmanager/server/routes/features_channels.py:132`)
- Klasse `ChannelPatch` (`schulmanager/server/routes/features_channels.py:140`)
- Klasse `MembersIn` (`schulmanager/server/routes/features_channels.py:149`)
- Klasse `FolderIn` (`schulmanager/server/routes/features_channels.py:155`) – `hidden` (alt) oder `visibility` (wie beim Material, auch zur Stunde/ab Zeitpunkt).
- Klasse `FolderPatch` (`schulmanager/server/routes/features_channels.py:166`) – Felder optional; `parent_id: null` verschiebt in die oberste Ebene (nur wenn angegeben).
- Klasse `FolderTreeIn` (`schulmanager/server/routes/features_channels.py:178`) – Ordner-Upload: relative Ordnerpfade (`"Projekt/Bilder"`) unter `parent_id`; die obersten Ordner werden
- Klasse `ReorderIn` (`schulmanager/server/routes/features_channels.py:189`)
- Klasse `ItemIn` (`schulmanager/server/routes/features_channels.py:196`)
- Klasse `ItemPatch` (`schulmanager/server/routes/features_channels.py:216`) – Felder optional; `folder_id`/`due_at` mit `null` = in die oberste Ebene / Frist entfernen.
- Klasse `FilesIn` (`schulmanager/server/routes/features_channels.py:236`) – Mehrfach-Upload: je Datei ein Material im Ordner (gleiche Sichtbarkeit für alle).
- Klasse `VisibilityIn` (`schulmanager/server/routes/features_channels.py:249`)
- Klasse `CopyIn` (`schulmanager/server/routes/features_channels.py:258`)
- Klasse `SubmissionIn` (`schulmanager/server/routes/features_channels.py:267`)
- Klasse `FeedbackIn` (`schulmanager/server/routes/features_channels.py:273`)
- Klasse `PostIn` (`schulmanager/server/routes/features_channels.py:281`)
- Klasse `PostPatch` (`schulmanager/server/routes/features_channels.py:288`)
- Klasse `Ctx` (`schulmanager/server/routes/features_channels.py:427`) – Zugriffskontext einer Anfrage auf einen Kanal.
- Klasse `Clock` (`schulmanager/server/routes/features_channels.py:597`) – Zeitpunkt der Anfrage + Tagespläne: Freigabe „zur Stunde“ mit Verlegung am selben Tag und – bei Entfall oder
- Funktion `takes_submissions` (`schulmanager/server/routes/features_channels.py:782`) – Aufgaben immer; anderes Material, wenn „Abgabe möglich“ gesetzt ist.
- Funktion `homework_due` (`schulmanager/server/routes/features_channels.py:3359`) – Fällige Aufgaben (Hausaufgaben) der Kursräume einer Ansicht im Zeitraum `[d1, d2]` (Ortszeit), je Tag.

## Datenbank-Tabellen

- **Nutzt:** `assignment_submissions`, `channel_extra_members`, `channel_folders`, `channel_item_views`, `channel_items`, `channel_posts`, `channel_reads`, `channels` → [[Datenmodell#Kursräume]]
- **Nutzt:** `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]
- **Nutzt:** `register_lessons`, `student_absences` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul channels]] – `channels`
- [[Routen features_common]] – `features_common`
- [[Routen features_register]] – `features_register` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server crypto]] – `crypto`
- [[Server db]] – `channels`, `db`, `db_models`, `register`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `parent_access`
- [[Server events]] – `events`
- [[Server files]] – `files`
- [[Server permissions]] – `permissions`

## Wird genutzt von

- [[Routen features_calendar]]
- [[Routen features_class_info]]
- [[Routen features_exams]]

## Tests

`tests/test_absence_log.py`, `tests/test_calendar.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_channels_rooms.py`, `tests/test_class_room_info.py`, `tests/test_homework_links.py`, `tests/test_rights.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
