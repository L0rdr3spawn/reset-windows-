---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/users.py"
stand: 2026-10-12 22:40
generator: schulmanager-regen
---

# Routen users

> API-Routen · 1 Datei(en) · 634 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Benutzerverwaltung: Konten, Massenanlage, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens, Startpasswörter und Demo-Zugänge.

Aus dem Modulkopf:

Benutzerverwaltung: Konten, Massenanlage, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/users.py` | 634 | Benutzerverwaltung: Konten, Massenanlage, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens. |

## Endpunkte (20)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/users` | `list_users` (`users.py:126`) | users.manage | [[Feature anmelderichtlinien]], [[Seite UsersPage]] |
| POST | `/api/v1/users` | `create` (`users.py:175`) | users.manage | [[Seite UsersPage]] |
| GET | `/api/v1/users/{user_id}` | `get_user` (`users.py:208`) | (angemeldet) | – |
| PATCH | `/api/v1/users/{user_id}` | `patch_user` (`users.py:215`) | users.manage | [[Seite UsersPage]] |
| DELETE | `/api/v1/users/{user_id}` | `remove_user` (`users.py:277`) | users.manage | [[Seite UsersPage]] |
| POST | `/api/v1/users/{user_id}/reset-password` | `reset_password` (`users.py:294`) | users.manage | [[Seite UsersPage]] |
| POST | `/api/v1/users/bulk` | `bulk` (`users.py:316`) | users.manage | [[Seite UsersPage]] |
| GET | `/api/v1/users/{user_id}/children` | `get_children` (`users.py:343`) | (angemeldet) | – |
| PUT | `/api/v1/users/{user_id}/children` | `put_children` (`users.py:355`) | users.manage | [[Seite UsersPage]] |
| POST | `/api/v1/users/{user_id}/children/{student_id}` | `add_child` (`users.py:370`) | users.manage | – |
| DELETE | `/api/v1/users/{user_id}/children/{student_id}` | `remove_child` (`users.py:387`) | users.manage | – |
| GET | `/api/v1/users/{user_id}/sessions` | `list_sessions` (`users.py:403`) | (angemeldet) | [[Seite ProfilePage]], [[Seite UsersPage]] |
| DELETE | `/api/v1/users/{user_id}/sessions` | `revoke_all_sessions` (`users.py:412`) | (angemeldet) | [[Seite ProfilePage]], [[Seite UsersPage]] |
| DELETE | `/api/v1/sessions/{session_id}` | `revoke_session` (`users.py:424`) | (angemeldet) | [[Seite ProfilePage]], [[Seite UsersPage]] |
| POST | `/api/v1/users/{user_id}/api-token` | `create_api_token` (`users.py:447`) | (angemeldet) | [[Seite UsersPage]] |
| GET | `/api/v1/users/{user_id}/api-tokens` | `list_api_tokens` (`users.py:485`) | (angemeldet) | [[Seite UsersPage]] |
| DELETE | `/api/v1/api-tokens/{token_id}` | `delete_api_token` (`users.py:493`) | (angemeldet) | [[Seite UsersPage]] |
| POST | `/api/v1/users/letters.pdf` | `letters_pdf` (`users.py:521`) | users.manage | [[Seite AccessLettersPage]] |
| GET | `/api/v1/demo-access` | `demo_access_info` (`users.py:573`) | users.manage | [[Seite UsersPage]] |
| POST | `/api/v1/demo-access` | `demo_access` (`users.py:593`) | users.manage | [[Seite UsersPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `UserCreate` (`schulmanager/server/routes/users.py:34`)
- Klasse `UserPatch` (`schulmanager/server/routes/users.py:48`)
- Klasse `BulkBody` (`schulmanager/server/routes/users.py:63`)
- Klasse `ResetBody` (`schulmanager/server/routes/users.py:68`)
- Klasse `ChildrenBody` (`schulmanager/server/routes/users.py:72`)
- Klasse `TokenBody` (`schulmanager/server/routes/users.py:76`)
- Klasse `LetterIn` (`schulmanager/server/routes/users.py:506`)
- Klasse `LettersBody` (`schulmanager/server/routes/users.py:514`)
- Klasse `DemoAccessBody` (`schulmanager/server/routes/users.py:567`)

## Datenbank-Tabellen

- **Nutzt:** `api_tokens`, `parent_links`, `sessions`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server betrieb]] – `demo_loader` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server files]] – `files` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `accounts`, `security`
- [[Server letters und pdf]] – `letters`, `pdf_simple` *(nur zur Laufzeit importiert)*
- [[Server licensing]] – `licensing` *(nur zur Laufzeit importiert)*
- [[Server permissions]] – `permissions`
- [[Server store]] – `store`

## Wird genutzt von

- [[Routen features_classes]]
- [[Routen features_contact]]
- [[Routen features_letters]]
- [[Routen features_sso]]

## Tests

`tests/test_api_access.py`, `tests/test_contact.py`, `tests/test_demo_public.py`, `tests/test_letters.py`, `tests/test_license.py`, `tests/test_login_policy.py`, `tests/test_messages.py`, `tests/test_multi_account.py`, `tests/test_rights.py`, `tests/test_self_reset.py`, `tests/test_server_core.py`, `tests/test_server_core_store.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
