---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/messages/"
stand: 2026-10-12 22:55
generator: schulmanager-regen
---

# Feature messages

> Frontend · 14 Datei(en) · 4475 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Postfach (`/postfach`): Unterhaltungen, Verfassen mit An/CC/BCC und externen Adressen, Rollengruppen, Moderation, Einstellungen und verbundene E-Mail-Konten.

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/messages/ClassRoster.tsx` | 140 | Klassenansicht in der Empfängerauswahl: nach einer Klasse suchen → Klassenleitung, Lehrkräfte und (für Personal mit Sicht auf die… |
| `frontend/src/features/messages/ComposePage.tsx` | 362 | `/postfach/neu` – Nachricht verfassen: An / CC / BCC (Personen, E-Mail-Adressen; mit `messages.broadcast` auch Gruppen), bei Adre… |
| `frontend/src/features/messages/ConversationView.tsx` | 603 | Ein Brief bzw. eine E-Mail im Chat-Stil: Kopf mit Betreff und Zahnrad (dahinter Archiv, stumm, ungelesen, blockieren, für mich lö… |
| `frontend/src/features/messages/MailAccounts.tsx` | 307 | Verbundene E-Mail-Konten (Postfach-Einstellungen): Konto mit App-Passwort verbinden oder – wenn die Schule es eingerichtet hat –… |
| `frontend/src/features/messages/ModerationPage.tsx` | 367 | `/postfach/moderation` (nur `messages.moderate`): gemeldete Nachrichten prüfen. Die Liste zeigt keine Inhalte; erst „Nachricht an… |
| `frontend/src/features/messages/RecipientPicker.tsx` | 331 | Empfängerauswahl (Combobox nach WAI-ARIA): Suche im Adressbuch des Servers (nur erlaubte Personen und – mit `messages.broadcast`… |
| `frontend/src/features/messages/SettingsPage.tsx` | 210 | `/postfach/einstellungen` – E-Mail-Hinweis, blockierte Personen, Regeln der Schule (Aufbewahrung, Schüler-Austausch); mit `settin… |
| `frontend/src/features/messages/api.ts` | 136 | Endpunkte des Postfachs (§9.5). Anhänge werden vorher über `uploadFile` (`src/api/files.ts`) mit dem Zweck `message` hochgeladen… |
| `frontend/src/features/messages/components.tsx` | 98 | Kleine Bausteine des Postfachs: Symbole, Profilkreis, Personenzeile, Zeitangabe. |
| `frontend/src/features/messages/dialogs.tsx` | 94 | Dialoge des Postfachs: Nachricht melden. |
| `frontend/src/features/messages/logic.ts` | 390 | Reine Hilfsfunktionen der Briefe und E-Mails (ohne React/DOM, mit vitest getestet): Ordner, Zeitangaben, Empfänger, Art der Unter… |
| `frontend/src/features/messages/messages.css` | 977 | Stylesheet |
| `frontend/src/features/messages/types.ts` | 376 | Typen des Postfachs (Backend `schulmanager/server/routes/features_messages.py`, ARCHITECTURE.md §9.5). Zeitstempel sind ISO-8601… |
| `frontend/src/features/messages/widgets.tsx` | 84 | Startseiten-Kachel „Neue Nachrichten“: ungelesene Unterhaltungen (höchstens 5) mit Absender, Betreff und Vorschau; für die Modera… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/settings` | [[Routen features_data]] · `get_settings` (`features_data.py:975`) |
| PUT | `/settings` | [[Routen features_data]] · `put_settings` (`features_data.py:997`) |
| GET | `/mail/accounts` | [[Routen features_mail]] · `list_accounts` (`features_mail.py:313`) |
| POST | `/mail/accounts` | [[Routen features_mail]] · `add_account` (`features_mail.py:354`) |
| DELETE | `/mail/accounts/{…}` | [[Routen features_mail]] · `delete_account` (`features_mail.py:397`) |
| PATCH | `/mail/accounts/{…}` | [[Routen features_mail]] · `patch_account` (`features_mail.py:371`) |
| POST | `/mail/accounts/{…}/sync` | [[Routen features_mail]] · `sync_now` (`features_mail.py:415`) |
| GET | `/mail/oauth/{…}/start` | [[Routen features_mail]] · `oauth_start` (`features_mail.py:422`) |
| GET | `/mail/providers` | [[Routen features_mail]] · `providers` (`features_mail.py:302`) |
| GET | `/messages/blocks` | [[Routen features_messages]] · `list_blocks` (`features_messages.py:1454`) |
| POST | `/messages/blocks` | [[Routen features_messages]] · `block_user` (`features_messages.py:1466`) |
| DELETE | `/messages/blocks/{…}` | [[Routen features_messages]] · `unblock_user` (`features_messages.py:1485`) |
| GET | `/messages/conversations` | [[Routen features_messages]] · `list_conversations` (`features_messages.py:894`) |
| POST | `/messages/conversations` | [[Routen features_messages]] · `create_conversation` (`features_messages.py:1022`) |
| DELETE | `/messages/conversations/{}` | [[Routen features_messages]] · `delete_conversation` (`features_messages.py:1310`) |
| GET | `/messages/conversations/{}` | [[Routen features_messages]] · `get_conversation` (`features_messages.py:1011`) |
| PATCH | `/messages/conversations/{}` | [[Routen features_messages]] · `patch_conversation` (`features_messages.py:1251`) |
| POST | `/messages/conversations/{}/messages` | [[Routen features_messages]] · `reply` (`features_messages.py:1187`) |
| POST | `/messages/conversations/{}/messages/{…}/report` | [[Routen features_messages]] · `report_message` (`features_messages.py:1335`) |
| POST | `/messages/conversations/{}/read` | [[Routen features_messages]] · `mark_read` (`features_messages.py:1266`) |
| POST | `/messages/conversations/{}/unread` | [[Routen features_messages]] · `mark_unread` (`features_messages.py:1280`) |
| GET | `/messages/drafts` | [[Routen features_messages]] · `list_drafts` (`features_messages.py:1606`) |
| POST | `/messages/drafts` | [[Routen features_messages]] · `create_draft` (`features_messages.py:1613`) |
| DELETE | `/messages/drafts/{…}` | [[Routen features_messages]] · `delete_draft` (`features_messages.py:1641`) |
| GET | `/messages/drafts/{…}` | [[Routen features_messages]] · `get_draft` (`features_messages.py:1627`) |
| PUT | `/messages/drafts/{…}` | [[Routen features_messages]] · `update_draft` (`features_messages.py:1632`) |
| GET | `/messages/moderation/reports` | [[Routen features_messages]] · `list_reports` (`features_messages.py:1688`) |
| GET | `/messages/moderation/reports/{…}` | [[Routen features_messages]] · `get_report` (`features_messages.py:1721`) |
| POST | `/messages/moderation/reports/{…}/resolve` | [[Routen features_messages]] · `resolve_report` (`features_messages.py:1799`) |
| POST | `/messages/moderation/retention` | [[Routen features_messages]] · `retention_now` (`features_messages.py:1890`) |
| GET | `/messages/moderation/suspensions` | [[Routen features_messages]] · `list_suspensions` (`features_messages.py:1843`) |
| DELETE | `/messages/moderation/users/{…}/suspend` | [[Routen features_messages]] · `unsuspend_user` (`features_messages.py:1873`) |
| POST | `/messages/moderation/users/{…}/suspend` | [[Routen features_messages]] · `suspend_user` (`features_messages.py:1862`) |
| POST | `/messages/read-all` | [[Routen features_messages]] · `read_all` (`features_messages.py:813`) |
| GET | `/messages/recipients` | [[Routen features_messages]] · `recipients` (`features_messages.py:1368`) |
| GET | `/messages/recipients/class/{…}` | [[Routen features_messages]] · `recipients_class` (`features_messages.py:1392`) |
| GET | `/messages/recipients/lookup` | [[Routen features_messages]] · `lookup_recipient` (`features_messages.py:1406`) |
| GET | `/messages/settings` | [[Routen features_messages]] · `get_settings` (`features_messages.py:1524`) |
| PUT | `/messages/settings` | [[Routen features_messages]] · `put_settings` (`features_messages.py:1530`) |
| GET | `/messages/unread` | [[Routen features_messages]] · `get_unread` (`features_messages.py:806`) |

## Backend-Notizen

[[Routen features_data]], [[Routen features_mail]], [[Routen features_messages]]

## Nutzt (Frontend)

- [[Feature nachrichten]] – `Composer`
- [[Frontend API-Schicht]] – `client`, `files`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `emoji`, `misc`, `permissions` …
- [[Frontend Komponenten]] – `Abbr`, `EmojiPicker`, `FileList`, `FileUpload`, `Icon` …

## Wird genutzt von

- [[Feature chats]]
- [[Feature nachrichten]]
- [[Feature students]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
