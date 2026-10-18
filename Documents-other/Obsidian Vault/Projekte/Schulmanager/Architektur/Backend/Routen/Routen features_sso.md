---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_sso.py"
stand: 2026-10-12 22:45
generator: schulmanager-regen
---

# Routen features_sso

> API-Routen · 1 Datei(en) · 933 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Anmeldedienste: mit Microsoft, Apple, Google oder dem Schulkonto anmelden und Konten verbinden (§11.4).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_sso.py` | 933 | Anmeldedienste: mit Microsoft, Apple, Google oder dem Schulkonto anmelden und Konten verbinden (§11… |

## Endpunkte (17)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/auth/sso/providers` | `sso_provider_list` (`features_sso.py:151`) | - | [[Feature anmeldedienste]], [[Feature anmelderichtlinien]] |
| GET | `/api/v1/auth/sso/{provider}/login` | `sso_login` (`features_sso.py:183`) | - | – |
| GET | `/api/v1/auth/sso/{provider}/callback` | `sso_callback_get` (`features_sso.py:190`) | - | – |
| POST | `/api/v1/auth/sso/{provider}/callback` | `sso_callback_post` (`features_sso.py:196`) | - | – |
| POST | `/api/v1/auth/sso/{provider}/nonce` | `sso_nonce` (`features_sso.py:327`) | - | [[Feature anmeldedienste]] |
| POST | `/api/v1/auth/sso/{provider}/token` | `sso_token` (`features_sso.py:338`) | - | [[Feature anmeldedienste]] |
| GET | `/api/v1/auth/sso/{provider}/mock` | `mock_authorize` (`features_sso.py:482`) | - | – |
| POST | `/api/v1/auth/sso/{provider}/mock` | `mock_submit` (`features_sso.py:494`) | - | – |
| GET | `/api/v1/me/identities` | `my_identities` (`features_sso.py:573`) | (angemeldet) | [[Feature anmeldedienste]] |
| POST | `/api/v1/me/identities/{provider}/link` | `link_start` (`features_sso.py:578`) | (angemeldet) | [[Feature anmeldedienste]], [[Feature anmelderichtlinien]] |
| DELETE | `/api/v1/me/identities/{provider}` | `unlink_mine` (`features_sso.py:609`) | (angemeldet) | [[Feature anmeldedienste]] |
| GET | `/api/v1/users/{user_id}/identities` | `user_identities` (`features_sso.py:664`) | users.manage | [[Feature anmeldedienste]] |
| POST | `/api/v1/users/{user_id}/identities` | `reserve_identity` (`features_sso.py:670`) | users.manage | [[Feature anmeldedienste]] |
| DELETE | `/api/v1/users/{user_id}/identities/{provider}` | `remove_identity` (`features_sso.py:698`) | users.manage | [[Feature anmeldedienste]] |
| GET | `/api/v1/sso/providers/config` | `provider_config` (`features_sso.py:808`) | - | [[Feature anmeldedienste]] |
| PUT | `/api/v1/sso/providers/{provider}` | `update_provider` (`features_sso.py:836`) | - | [[Feature anmeldedienste]] |
| POST | `/api/v1/sso/providers/{provider}/test` | `test_provider` (`features_sso.py:905`) | - | [[Feature anmeldedienste]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `state_cookie` (`schulmanager/server/routes/features_sso.py:76`)
- Funktion `safe_next` (`schulmanager/server/routes/features_sso.py:80`) – Nur interne Pfade (kein Open Redirect, keine Steuer-/Leerzeichen, keine API-Pfade).
- Funktion `with_query` (`schulmanager/server/routes/features_sso.py:91`)
- Funktion `set_state_cookie` (`schulmanager/server/routes/features_sso.py:109`) – Status-Cookie (httponly, 10 min). Apple sendet per POST von appleid.apple.com zurück → bei https SameSite=Non…
- Funktion `set_hint_cookie` (`schulmanager/server/routes/features_sso.py:125`) – Merkt Anbieter + E-Mail für stilles SSO/Auto-Auswahl (lesbar für die Anmeldeseite, 90 Tage).
- Funktion `login_error` (`schulmanager/server/routes/features_sso.py:132`)
- Funktion `start_login` (`schulmanager/server/routes/features_sso.py:156`)
- Funktion `finish` (`schulmanager/server/routes/features_sso.py:203`) – Gemeinsamer Callback (auch für die alten Pfade `/auth/oidc/*`).
- Klasse `TokenBody` (`schulmanager/server/routes/features_sso.py:304`)
- Klasse `LinkBody` (`schulmanager/server/routes/features_sso.py:523`)
- Klasse `ReserveBody` (`schulmanager/server/routes/features_sso.py:637`)
- Funktion `require_admin` (`schulmanager/server/routes/features_sso.py:714`)
- Klasse `ProviderBody` (`schulmanager/server/routes/features_sso.py:720`)

## Datenbank-Tabellen

- **Nutzt:** `sessions`, `sso_providers`, `user_identities`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen auth]] – `auth` *(nur zur Laufzeit importiert)*
- [[Routen users]] – `users` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`, `identities`
- [[Server deps]] – `deps`
- [[Server konten und anmeldung]] – `identities`, `login_policy`, `security`, `sso_providers`

## Wird genutzt von

- [[Routen oidc]]

## Tests

`tests/test_api_access.py`, `tests/test_contact.py`, `tests/test_demo_public.py`, `tests/test_letters.py`, `tests/test_license.py`, `tests/test_login_policy.py`, `tests/test_messages.py`, `tests/test_multi_account.py`, `tests/test_rights.py`, `tests/test_self_reset.py`, `tests/test_server_core.py`, `tests/test_server_core_store.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
