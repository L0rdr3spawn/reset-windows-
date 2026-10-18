---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/chat_migration.py"
stand: 2026-10-12 21:42
generator: schulmanager-regen
---

# Server chat_migration

> Server-Kern · 1 Datei(en) · 286 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Übernahme von Postfach-Unterhaltungen, die eigentlich Chats sind, nach „Chats & Gruppen“.

Kriterium (Postfach = Brief/E-Mail, Chats = Unterhaltung ohne Brief-Charakter):

* `group` (mehrere Einzelpersonen, „alle sehen alle“) → **Chat-Gruppe** (Betreff wird zum Gruppennamen),
* `direct` **ohne Betreff** → **Einzelchat**,

jeweils nur, wenn es kein Brief im engeren Sinn ist: keine externe E-Mail (`external`/`mail_account_id`), keine private Antwort auf ein Rundschreiben (`parent_id`), kein Anhang in irgendeiner Nachricht (Chats kennen nur Bilder/GIFs), keine Kopie/Blindkopie. `direct` mit Betreff, `broadcast` (Rundschreiben) und `email` bleiben im Postfach. Unterhaltungen, die nach der Trennung angelegt wurden (`Conversation.mail_native`), werden nie übernommen.

Vorgehen (verlustfrei, wiederholbar):

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/chat_migration.py` | 286 | Übernahme von Postfach-Unterhaltungen, die eigentlich Chats sind, nach „Chats & Gruppen“. |

## Wichtige Funktionen und Klassen

- Funktion `classify` (`schulmanager/server/chat_migration.py:63`) – `("direct"|"group"|None, Begründung)` – wohin die Unterhaltung gehört.
- Funktion `migrate_conversation` (`schulmanager/server/chat_migration.py:177`) – Prüft/übernimmt eine Unterhaltung (im Aufrufer-Savepoint); setzt `migrated_chat_id`.
- Funktion `migrate_postfach` (`schulmanager/server/chat_migration.py:204`) – Übernimmt alle geeigneten, noch nicht geprüften Postfach-Unterhaltungen. `force` prüft auch bereits
- Funktion `rollback` (`schulmanager/server/chat_migration.py:243`) – Rückweg: kopierte Nachrichten entfernen, Original im Postfach wieder einblenden (`migrated_chat_id = 0`,
- Funktion `run_startup` (`schulmanager/server/chat_migration.py:270`) – Einmalig beim Start (idempotent, billig, wenn nichts mehr zu tun ist). Fehler stoppen den Start nicht.

## Datenbank-Tabellen

- **Nutzt:** `chat_members`, `chat_messages`, `chats`, `conversation_participants`, `conversations`, `messages` → [[Datenmodell#Postfach und Chats]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server crypto]] – `crypto`
- [[Server db]] – `chats`, `db`, `db_models`, `messages`

## Wird genutzt von

- [[Server betrieb]] – `cli`
- [[Server runtime]]

## Tests

`tests/test_chat_split.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
