---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/chats/"
stand: 2026-10-12 22:55
generator: schulmanager-regen
---

# Feature chats

> Frontend · 9 Datei(en) · 2767 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Chats: Einzel-, Gruppen- und Klassenchats mit Ende-zu-Ende-Verschlüsselung (Gerätschlüssel im Browser, `tweetnacl`), Moderation gemeldeter Auszüge, Datenschutzseite.

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/chats/ChatsPage.tsx` | 820 | Bausteine der Chats (Einzelchats, eigene Gruppen, Klassenchats mit/ohne Lehrkräfte, Elternchats), eingebunden in die Seite „Nachr… |
| `frontend/src/features/chats/DevicesPanel.tsx` | 646 | „Geräte & Schlüssel“ der Chats: Geräteübersicht, Verlauf auf ein neues Gerät übertragen (Code/QR + Fingerabdruck), Wiederherstell… |
| `frontend/src/features/chats/ModerationPage.tsx` | 83 | `/chats/moderation` – gemeldete Chat-Nachrichten. Inhalte sind Ende-zu-Ende-verschlüsselt; zu sehen ist nur der Text, den die mel… |
| `frontend/src/features/chats/PrivacyPage.tsx` | 86 | `/datenschutz` – Datenschutzhinweise für alle Nutzer/innen (Schüler/innen, Eltern, Lehrkräfte, Verwaltung): welche Daten, wer sie… |
| `frontend/src/features/chats/api.ts` | 179 |  |
| `frontend/src/features/chats/chats.css` | 290 | Stylesheet |
| `frontend/src/features/chats/crypto.ts` | 241 | Ende-zu-Ende-Verschlüsselung der Chats (tweetnacl, dieselben Verfahren wie libsodium): * Jedes Gerät (Browser) hat ein eigenes Sc… |
| `frontend/src/features/chats/images.tsx` | 145 | Bilder & GIFs in Chats: auswählen/einfügen/ziehen (`readImageFile`), im Browser verschlüsseln (siehe `crypto.ts`) und in Nachrich… |
| `frontend/src/features/chats/keys.ts` | 277 | Schlüsselverwaltung der Chats: Verlauf auf ein neues Gerät übertragen, Wiederherstellung mit Passwort, neue Schlüssel erzeugen un… |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/chat-keys` | [[Routen features_chats]] · `add_keys` (`features_chats.py:519`) |
| DELETE | `/chat-keys/backup` | [[Routen features_chats]] · `delete_backup` (`features_chats.py:593`) |
| GET | `/chat-keys/backup` | [[Routen features_chats]] · `get_backup` (`features_chats.py:565`) |
| PUT | `/chat-keys/backup` | [[Routen features_chats]] · `put_backup` (`features_chats.py:571`) |
| GET | `/chat-keys/pending` | [[Routen features_chats]] · `pending_keys` (`features_chats.py:479`) |
| POST | `/chat-links` | [[Routen features_chats]] · `create_link` (`features_chats.py:380`) |
| DELETE | `/chat-links/{…}` | [[Routen features_chats]] · `cancel_link` (`features_chats.py:456`) |
| GET | `/chat-links/{…}` | [[Routen features_chats]] · `get_link` (`features_chats.py:430`) |
| POST | `/chat-links/{…}/approve` | [[Routen features_chats]] · `approve_link` (`features_chats.py:439`) |
| POST | `/chat-links/lookup` | [[Routen features_chats]] · `lookup_link` (`features_chats.py:408`) |
| GET | `/chat-reports` | [[Routen features_chats]] · `list_reports` (`features_chats.py:1257`) |
| POST | `/chat-reports/{…}` | [[Routen features_chats]] · `resolve_report` (`features_chats.py:1301`) |
| GET | `/chats` | [[Routen features_chats]] · `list_chats` (`features_chats.py:757`) |
| POST | `/chats` | [[Routen features_chats]] · `create_chat` (`features_chats.py:686`) |
| GET | `/chats/class-options` | [[Routen features_chats]] · `class_options` (`features_chats.py:796`) |
| GET | `/chats/devices` | [[Routen features_chats]] · `list_devices` (`features_chats.py:266`) |
| POST | `/chats/devices` | [[Routen features_chats]] · `register_device` (`features_chats.py:247`) |
| DELETE | `/chats/devices/{…}` | [[Routen features_chats]] · `revoke_device` (`features_chats.py:278`) |
| POST | `/chats/devices/{…}/ack` | [[Routen features_chats]] · `ack_device` (`features_chats.py:295`) |
| POST | `/chats/devices/reset` | [[Routen features_chats]] · `reset_devices` (`features_chats.py:313`) |
| GET | `/chats/unread` | [[Routen features_chats]] · `unread` (`features_chats.py:786`) |
| GET | `/chats/{}` | [[Routen features_chats]] · `chat_detail` (`features_chats.py:819`) |
| PATCH | `/chats/{}` | [[Routen features_chats]] · `patch_chat` (`features_chats.py:852`) |
| GET | `/chats/{}/devices` | [[Routen features_chats]] · `chat_devices` (`features_chats.py:971`) |
| POST | `/chats/{}/members` | [[Routen features_chats]] · `add_members` (`features_chats.py:880`) |
| DELETE | `/chats/{}/members/{…}` | [[Routen features_chats]] · `remove_member` (`features_chats.py:903`) |
| PATCH | `/chats/{}/members/{…}` | [[Routen features_chats]] · `set_admin` (`features_chats.py:939`) |
| GET | `/chats/{}/messages` | [[Routen features_chats]] · `list_messages` (`features_chats.py:1009`) |
| POST | `/chats/{}/messages` | [[Routen features_chats]] · `send_message` (`features_chats.py:1042`) |
| DELETE | `/chats/{}/messages/{…}` | [[Routen features_chats]] · `delete_message` (`features_chats.py:1090`) |
| POST | `/chats/{}/messages/{…}/report` | [[Routen features_chats]] · `report_message` (`features_chats.py:1210`) |
| POST | `/chats/{}/read` | [[Routen features_chats]] · `mark_read` (`features_chats.py:1179`) |
| GET | `/messages/recipients` | [[Routen features_messages]] · `recipients` (`features_messages.py:1368`) |

## Backend-Notizen

[[Routen features_chats]], [[Routen features_messages]]

## Nutzt (Frontend)

- [[Feature messages]] – `RecipientPicker`, `api`, `components`, `types`
- [[Feature nachrichten]] – `Composer`
- [[Frontend API-Schicht]] – `client`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `emoji`, `misc` …
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `Modal`, `QrCode`, `ui`

## Wird genutzt von

- [[Feature nachrichten]]
- [[Feature students]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->
