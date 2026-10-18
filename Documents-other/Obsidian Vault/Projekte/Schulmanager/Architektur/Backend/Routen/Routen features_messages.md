---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_messages.py"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Routen features_messages

> API-Routen · 1 Datei(en) · 1993 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Internes Postfach (ARCHITECTURE.md §9.5, Agent Postfach) – verschlüsselte Nachrichten für alle Konten.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_messages.py` | 1993 | Internes Postfach (ARCHITECTURE.md §9.5, Agent Postfach) – verschlüsselte Nachrichten für alle Kont… |

## Endpunkte (31)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/messages/unread` | `get_unread` (`features_messages.py:806`) | - | [[Feature messages]], [[Feature nachrichten]], [[Feature students]] |
| POST | `/api/v1/messages/read-all` | `read_all` (`features_messages.py:813`) | - | [[Feature messages]], [[Feature nachrichten]] |
| GET | `/api/v1/messages/conversations` | `list_conversations` (`features_messages.py:894`) | - | [[Feature messages]], [[Feature nachrichten]], [[Feature students]] |
| GET | `/api/v1/messages/conversations/{conversation_id}` | `get_conversation` (`features_messages.py:1011`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/conversations` | `create_conversation` (`features_messages.py:1022`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/conversations/{conversation_id}/messages` | `reply` (`features_messages.py:1187`) | - | [[Feature messages]] |
| PATCH | `/api/v1/messages/conversations/{conversation_id}` | `patch_conversation` (`features_messages.py:1251`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/conversations/{conversation_id}/read` | `mark_read` (`features_messages.py:1266`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/conversations/{conversation_id}/unread` | `mark_unread` (`features_messages.py:1280`) | - | [[Feature messages]] |
| DELETE | `/api/v1/messages/conversations/{conversation_id}` | `delete_conversation` (`features_messages.py:1310`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/conversations/{conversation_id}/messages/{message_id}/report` | `report_message` (`features_messages.py:1335`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/recipients` | `recipients` (`features_messages.py:1368`) | - | [[Feature chats]], [[Feature messages]] |
| GET | `/api/v1/messages/recipients/class/{class_id}` | `recipients_class` (`features_messages.py:1392`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/recipients/lookup` | `lookup_recipient` (`features_messages.py:1406`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/blocks` | `list_blocks` (`features_messages.py:1454`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/blocks` | `block_user` (`features_messages.py:1466`) | - | [[Feature messages]] |
| DELETE | `/api/v1/messages/blocks/{blocked_user_id}` | `unblock_user` (`features_messages.py:1485`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/settings` | `get_settings` (`features_messages.py:1524`) | - | [[Feature messages]], [[Feature nachrichten]] |
| PUT | `/api/v1/messages/settings` | `put_settings` (`features_messages.py:1530`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/drafts` | `list_drafts` (`features_messages.py:1606`) | - | [[Feature messages]], [[Feature nachrichten]] |
| POST | `/api/v1/messages/drafts` | `create_draft` (`features_messages.py:1613`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/drafts/{draft_id}` | `get_draft` (`features_messages.py:1627`) | - | [[Feature messages]] |
| PUT | `/api/v1/messages/drafts/{draft_id}` | `update_draft` (`features_messages.py:1632`) | - | [[Feature messages]] |
| DELETE | `/api/v1/messages/drafts/{draft_id}` | `delete_draft` (`features_messages.py:1641`) | - | [[Feature messages]], [[Feature nachrichten]] |
| GET | `/api/v1/messages/moderation/reports` | `list_reports` (`features_messages.py:1688`) | - | [[Feature messages]], [[Feature nachrichten]] |
| GET | `/api/v1/messages/moderation/reports/{report_id}` | `get_report` (`features_messages.py:1721`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/moderation/reports/{report_id}/resolve` | `resolve_report` (`features_messages.py:1799`) | - | [[Feature messages]] |
| GET | `/api/v1/messages/moderation/suspensions` | `list_suspensions` (`features_messages.py:1843`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/moderation/users/{target_id}/suspend` | `suspend_user` (`features_messages.py:1862`) | - | [[Feature messages]] |
| DELETE | `/api/v1/messages/moderation/users/{target_id}/suspend` | `unsuspend_user` (`features_messages.py:1873`) | - | [[Feature messages]] |
| POST | `/api/v1/messages/moderation/retention` | `retention_now` (`features_messages.py:1890`) | - | [[Feature messages]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `RecipientIn` (`schulmanager/server/routes/features_messages.py:132`) – Empfänger: Einzelperson (`type="user"`, `id`), Gruppe (`type="group"`, `kind`, `ref`) oder E-Mail-Adresse
- Klasse `ConversationIn` (`schulmanager/server/routes/features_messages.py:146`)
- Klasse `ReplyIn` (`schulmanager/server/routes/features_messages.py:157`)
- Klasse `ParticipantPatch` (`schulmanager/server/routes/features_messages.py:164`)
- Klasse `ReadIn` (`schulmanager/server/routes/features_messages.py:170`)
- Klasse `ReportIn` (`schulmanager/server/routes/features_messages.py:175`)
- Klasse `BlockIn` (`schulmanager/server/routes/features_messages.py:181`)
- Klasse `SettingsIn` (`schulmanager/server/routes/features_messages.py:186`)
- Klasse `DraftIn` (`schulmanager/server/routes/features_messages.py:191`)
- Klasse `ResolveIn` (`schulmanager/server/routes/features_messages.py:202`)
- Klasse `SuspendIn` (`schulmanager/server/routes/features_messages.py:210`)
- Funktion `unread_counts` (`schulmanager/server/routes/features_messages.py:452`) – Zähler fürs Menü: `unread` = Unterhaltungen mit Ungelesenem (ohne stummgeschaltete/archivierte),
- Funktion `run_retention` (`schulmanager/server/routes/features_messages.py:1913`) – Wartung des Postfachs (für `maintenance.run_maintenance`):

## Datenbank-Tabellen

- **Nutzt:** `chat_messages`, `conversation_participants`, `conversations`, `message_drafts`, `message_reports`, `message_user_settings`, `messages`, `user_blocks` → [[Datenmodell#Postfach und Chats]]
- **Nutzt:** `notifications_outbox` → [[Datenmodell#Planungsdokument und Protokoll]]
- **Nutzt:** `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]
- **Nutzt:** `stored_files` → [[Datenmodell#Dateien]]

## Hängt ab von

- [[Modul messaging]] – `messaging`
- [[Routen features_common]] – `features_common`
- [[Routen features_mail]] – `features_mail` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server crypto]] – `crypto`
- [[Server db]] – `chats`, `db`, `db_models`, `files`, `messages`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `parent_access` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events`
- [[Server files]] – `files`
- [[Server notify]] – `notify` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_chats]]

## Tests

`tests/test_mail.py`, `tests/test_messages.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
