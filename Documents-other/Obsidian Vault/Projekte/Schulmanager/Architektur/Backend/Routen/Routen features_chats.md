---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_chats.py"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Routen features_chats

> API-Routen · 1 Datei(en) · 1320 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Chats: Einzelchats, selbst erstellte Gruppen, Klassenchats (mit/ohne Lehrkräfte, Elternchats) – Ende-zu-Ende verschlüsselt (siehe `feature_models/chats.py`). Der Server prüft nur, **wer** mit **wem** chatten darf, und verteilt Chiffrate; Inhalte kann er nicht lesen.

Rechte: `messages.use`. Wer wen hinzufügen darf, folgt den Regeln des Postfachs (`schulmanager/messaging.py`: Blockierungen, `messaging_students_to_students`, nur erreichbare Konten). Klassen als Ganzes:

* Personal: eigene Klassen (Lehrkräfte mit Scope `own_classes`) bzw. alle – Schüler/innen, Eltern, Lehrkräfte
* Schüler/innen: die eigene Klasse (nur Mitschüler/innen)
* Eltern: Elternchat der Klassen ihrer Kinder

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_chats.py` | 1320 | Chats: Einzelchats, selbst erstellte Gruppen, Klassenchats (mit/ohne Lehrkräfte, Elternchats) – End… |

## Endpunkte (35)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| POST | `/api/v1/chats/devices` | `register_device` (`features_chats.py:247`) | - | [[Feature chats]] |
| GET | `/api/v1/chats/devices` | `list_devices` (`features_chats.py:266`) | - | [[Feature chats]] |
| DELETE | `/api/v1/chats/devices/{device_id}` | `revoke_device` (`features_chats.py:278`) | - | [[Feature chats]] |
| POST | `/api/v1/chats/devices/{device_id}/ack` | `ack_device` (`features_chats.py:295`) | - | [[Feature chats]] |
| POST | `/api/v1/chats/devices/reset` | `reset_devices` (`features_chats.py:313`) | - | [[Feature chats]] |
| POST | `/api/v1/chat-links` | `create_link` (`features_chats.py:380`) | - | [[Feature chats]] |
| POST | `/api/v1/chat-links/lookup` | `lookup_link` (`features_chats.py:408`) | - | [[Feature chats]] |
| GET | `/api/v1/chat-links/{link_id}` | `get_link` (`features_chats.py:430`) | - | [[Feature chats]] |
| POST | `/api/v1/chat-links/{link_id}/approve` | `approve_link` (`features_chats.py:439`) | - | [[Feature chats]] |
| DELETE | `/api/v1/chat-links/{link_id}` | `cancel_link` (`features_chats.py:456`) | - | [[Feature chats]] |
| GET | `/api/v1/chat-keys/pending` | `pending_keys` (`features_chats.py:479`) | - | [[Feature chats]] |
| POST | `/api/v1/chat-keys` | `add_keys` (`features_chats.py:519`) | - | [[Feature chats]] |
| GET | `/api/v1/chat-keys/backup` | `get_backup` (`features_chats.py:565`) | - | [[Feature chats]] |
| PUT | `/api/v1/chat-keys/backup` | `put_backup` (`features_chats.py:571`) | - | [[Feature chats]] |
| DELETE | `/api/v1/chat-keys/backup` | `delete_backup` (`features_chats.py:593`) | - | [[Feature chats]] |
| POST | `/api/v1/chats` | `create_chat` (`features_chats.py:686`) | - | [[Feature chats]] |
| GET | `/api/v1/chats` | `list_chats` (`features_chats.py:757`) | - | [[Feature chats]], [[Feature nachrichten]], [[Feature students]] |
| GET | `/api/v1/chats/unread` | `unread` (`features_chats.py:786`) | - | [[Feature chats]], [[Feature nachrichten]] |
| GET | `/api/v1/chats/class-options` | `class_options` (`features_chats.py:796`) | - | [[Feature chats]] |
| GET | `/api/v1/chats/{chat_id}` | `chat_detail` (`features_chats.py:819`) | - | [[Feature chats]] |
| PATCH | `/api/v1/chats/{chat_id}` | `patch_chat` (`features_chats.py:852`) | - | [[Feature chats]] |
| POST | `/api/v1/chats/{chat_id}/members` | `add_members` (`features_chats.py:880`) | - | [[Feature chats]] |
| DELETE | `/api/v1/chats/{chat_id}/members/{member_id}` | `remove_member` (`features_chats.py:903`) | - | [[Feature chats]] |
| PATCH | `/api/v1/chats/{chat_id}/members/{member_id}` | `set_admin` (`features_chats.py:939`) | - | [[Feature chats]] |
| GET | `/api/v1/chats/{chat_id}/devices` | `chat_devices` (`features_chats.py:971`) | - | [[Feature chats]] |
| GET | `/api/v1/chats/{chat_id}/messages` | `list_messages` (`features_chats.py:1009`) | - | [[Feature chats]] |
| POST | `/api/v1/chats/{chat_id}/messages` | `send_message` (`features_chats.py:1042`) | - | [[Feature chats]] |
| DELETE | `/api/v1/chats/{chat_id}/messages/{message_id}` | `delete_message` (`features_chats.py:1090`) | - | [[Feature chats]] |
| POST | `/api/v1/chats/{chat_id}/attachments` | `upload_attachment` (`features_chats.py:1128`) | - | – |
| GET | `/api/v1/chats/{chat_id}/attachments/{attachment_id}` | `download_attachment` (`features_chats.py:1157`) | - | – |
| POST | `/api/v1/chats/{chat_id}/read` | `mark_read` (`features_chats.py:1179`) | - | [[Feature chats]] |
| POST | `/api/v1/chats/{chat_id}/messages/{message_id}/report` | `report_message` (`features_chats.py:1210`) | - | [[Feature chats]] |
| GET | `/api/v1/chat-reports` | `list_reports` (`features_chats.py:1257`) | - | [[Feature chats]] |
| GET | `/api/v1/chat-reports/{report_id}/images/{image_id}` | `report_image` (`features_chats.py:1282`) | - | – |
| POST | `/api/v1/chat-reports/{report_id}` | `resolve_report` (`features_chats.py:1301`) | - | [[Feature chats]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `DeviceIn` (`schulmanager/server/routes/features_chats.py:193`)
- Klasse `AckIn` (`schulmanager/server/routes/features_chats.py:290`)
- Klasse `ResetIn` (`schulmanager/server/routes/features_chats.py:308`)
- Klasse `LinkIn` (`schulmanager/server/routes/features_chats.py:373`)
- Klasse `LookupIn` (`schulmanager/server/routes/features_chats.py:403`)
- Klasse `ApproveIn` (`schulmanager/server/routes/features_chats.py:434`)
- Klasse `WrappedIn` (`schulmanager/server/routes/features_chats.py:506`)
- Klasse `WrappedBatch` (`schulmanager/server/routes/features_chats.py:512`)
- Klasse `BackupIn` (`schulmanager/server/routes/features_chats.py:559`)
- Klasse `ClassPick` (`schulmanager/server/routes/features_chats.py:606`)
- Klasse `ChatIn` (`schulmanager/server/routes/features_chats.py:672`)
- Klasse `ChatPatch` (`schulmanager/server/routes/features_chats.py:843`)
- Klasse `MembersIn` (`schulmanager/server/routes/features_chats.py:874`)
- Klasse `AdminIn` (`schulmanager/server/routes/features_chats.py:933`)
- Klasse `KeyIn` (`schulmanager/server/routes/features_chats.py:1026`)
- Klasse `MessageIn` (`schulmanager/server/routes/features_chats.py:1032`)
- Klasse `ReadIn` (`schulmanager/server/routes/features_chats.py:1174`)
- Klasse `ReportImage` (`schulmanager/server/routes/features_chats.py:1190`)
- Klasse `ReportIn` (`schulmanager/server/routes/features_chats.py:1194`)
- Klasse `ResolveIn` (`schulmanager/server/routes/features_chats.py:1296`)

## Datenbank-Tabellen

- **Nutzt:** `chat_attachments`, `chat_key_backups`, `chat_link_requests`, `chat_report_images` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `chat_devices`, `chat_members`, `chat_message_keys`, `chat_messages`, `chat_reports`, `chats` → [[Datenmodell#Postfach und Chats]]

## Hängt ab von

- [[Modul messaging]] – `messaging`
- [[Routen features_common]] – `features_common`
- [[Routen features_messages]] – `features_messages`
- [[Server crypto]] – `crypto`
- [[Server db]] – `chats`, `db`
- [[Server deps]] – `deps`
- [[Server events]] – `events`

## Wird genutzt von

- –

## Tests

`tests/test_chat_devices.py`, `tests/test_chat_split.py`, `tests/test_chats.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
