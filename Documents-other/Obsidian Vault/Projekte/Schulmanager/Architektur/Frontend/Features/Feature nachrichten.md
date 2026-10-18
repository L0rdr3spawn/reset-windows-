---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/nachrichten/"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Feature nachrichten

> Frontend · 4 Datei(en) · 786 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Neues Feature (noch nicht beschrieben).

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/nachrichten/Composer.tsx` | 110 | Eingabezeile wie im Messenger (Chats und Antworten auf Briefe): eine durchgehende, mit dem Text wachsende Zeile; links „+“ (Bilde… |
| `frontend/src/features/nachrichten/NachrichtenPage.tsx` | 484 | `/nachrichten` – EINE Liste für alles wie in einem Messenger: Einzelchats, Gruppen, Briefe/Rundschreiben, E-Mails verknüpfter Kon… |
| `frontend/src/features/nachrichten/badge.tsx` | 37 | Unsichtbare Hintergrund-Komponente: EINE Zahl für alles am Menüeintrag „Nachrichten“ (Chats/Gruppen und Briefe/E-Mails mit ungele… |
| `frontend/src/features/nachrichten/inbox.ts` | 155 | Reine Logik der gemeinsamen Liste „Nachrichten“ (ohne React, mit vitest getestet): Chats, Gruppen, Briefe, E-Mails und Mitteilung… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/announcements` | [[Routen features_announcements]] · `list_announcements` (`features_announcements.py:194`) |
| GET | `/chats` | [[Routen features_chats]] · `list_chats` (`features_chats.py:757`) |
| GET | `/chats/unread` | [[Routen features_chats]] · `unread` (`features_chats.py:786`) |
| GET | `/mail/accounts` | [[Routen features_mail]] · `list_accounts` (`features_mail.py:313`) |
| GET | `/messages/conversations` | [[Routen features_messages]] · `list_conversations` (`features_messages.py:894`) |
| GET | `/messages/drafts` | [[Routen features_messages]] · `list_drafts` (`features_messages.py:1606`) |
| DELETE | `/messages/drafts/{…}` | [[Routen features_messages]] · `delete_draft` (`features_messages.py:1641`) |
| GET | `/messages/moderation/reports` | [[Routen features_messages]] · `list_reports` (`features_messages.py:1688`) |
| POST | `/messages/read-all` | [[Routen features_messages]] · `read_all` (`features_messages.py:813`) |
| GET | `/messages/settings` | [[Routen features_messages]] · `get_settings` (`features_messages.py:1524`) |
| GET | `/messages/unread` | [[Routen features_messages]] · `get_unread` (`features_messages.py:806`) |

## Backend-Notizen

[[Routen features_announcements]], [[Routen features_chats]], [[Routen features_mail]], [[Routen features_messages]]

## Nutzt (Frontend)

- [[Feature chats]] – `ChatsPage`, `DevicesPanel`, `api`
- [[Feature messages]] – `ConversationView`, `api`, `components`, `logic`, `types`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `misc`, `permissions`, `useApi`
- [[Frontend Komponenten]] – `EmojiPicker`, `Icon`, `Modal`, `ui`
- [[Seite AnnouncementsPage]] – `AnnouncementsPage`

## Wird genutzt von

- [[Feature chats]]
- [[Feature messages]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
