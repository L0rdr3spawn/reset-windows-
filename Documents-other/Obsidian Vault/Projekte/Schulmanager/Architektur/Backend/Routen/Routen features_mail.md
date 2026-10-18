---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_mail.py"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Routen features_mail

> API-Routen · 1 Datei(en) · 460 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Verbundene E-Mail-Konten im Postfach (Konten verwalten, Google/Microsoft-Anmeldung, Abruf, Versand an Externe).

* `GET  /mail/providers` – Anbieter mit Voreinstellungen und ob die Anmeldung über Google/Microsoft eingerichtet ist
* `GET  /mail/accounts` · `POST /mail/accounts` (App-Passwort; Verbindung wird vorher geprüft)
* `PATCH /mail/accounts/{id}` (Name, Abruf an/aus, Standard, neues Passwort) · `DELETE /mail/accounts/{id}`
* `POST /mail/accounts/{id}/sync` – sofort abrufen
* `GET  /mail/oauth/{provider}/start` → `{url}` · `GET /mail/oauth/callback` (Weiterleitung des Anbieters)

Eingehende E-Mails werden als Unterhaltung (`kind="email"`) bzw. als Antwort in der passenden Unterhaltung abgelegt (Zuordnung über `Message-ID`/`In-Reply-To`). Versand an Externe: `` (aus dem Postfach).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_mail.py` | 460 | Verbundene E-Mail-Konten im Postfach (Konten verwalten, Google/Microsoft-Anmeldung, Abruf, Versand… |

## Endpunkte (8)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/mail/providers` | `providers` (`features_mail.py:302`) | - | [[Feature messages]] |
| GET | `/api/v1/mail/accounts` | `list_accounts` (`features_mail.py:313`) | - | [[Feature messages]], [[Feature nachrichten]] |
| POST | `/api/v1/mail/accounts` | `add_account` (`features_mail.py:354`) | - | [[Feature messages]] |
| PATCH | `/api/v1/mail/accounts/{account_id}` | `patch_account` (`features_mail.py:371`) | - | [[Feature messages]] |
| DELETE | `/api/v1/mail/accounts/{account_id}` | `delete_account` (`features_mail.py:397`) | - | [[Feature messages]] |
| POST | `/api/v1/mail/accounts/{account_id}/sync` | `sync_now` (`features_mail.py:415`) | - | [[Feature messages]] |
| GET | `/api/v1/mail/oauth/{provider}/start` | `oauth_start` (`features_mail.py:422`) | - | [[Feature messages]] |
| GET | `/api/v1/mail/oauth/callback` | `oauth_callback` (`features_mail.py:432`) | (angemeldet) | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `valid_email` (`schulmanager/server/routes/features_mail.py:44`)
- Funktion `creds_for` (`schulmanager/server/routes/features_mail.py:49`)
- Funktion `store_secret` (`schulmanager/server/routes/features_mail.py:59`)
- Funktion `account_out` (`schulmanager/server/routes/features_mail.py:69`)
- Funktion `accounts_of` (`schulmanager/server/routes/features_mail.py:79`)
- Funktion `sending_account` (`schulmanager/server/routes/features_mail.py:84`) – Konto für den Versand: gewünschtes (falls eigenes), sonst Standard, sonst das erste.
- Funktion `deliver_external` (`schulmanager/server/routes/features_mail.py:95`) – Schickt `msg` per E-Mail an die externen Beteiligten der Unterhaltung (über das Konto der absendenden
- Funktion `import_mail` (`schulmanager/server/routes/features_mail.py:162`) – Legt eine eingegangene E-Mail ins Postfach von `acc.user_id`. Liefert die Unterhaltungs-ID (oder `None`,
- Funktion `sync_account` (`schulmanager/server/routes/features_mail.py:221`) – Neue E-Mails eines Kontos abrufen und ins Postfach legen. Liefert die Zahl übernommener E-Mails.
- Funktion `sync_all` (`schulmanager/server/routes/features_mail.py:256`)
- Klasse `AccountIn` (`schulmanager/server/routes/features_mail.py:272`)
- Klasse `AccountPatch` (`schulmanager/server/routes/features_mail.py:286`)

## Datenbank-Tabellen

- **Nutzt:** `conversation_participants`, `conversations`, `mail_accounts`, `messages` → [[Datenmodell#Postfach und Chats]]

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server crypto]] – `crypto`
- [[Server db]] – `db`, `mail`, `messages`
- [[Server deps]] – `deps`
- [[Server events]] – `events`
- [[Server files]] – `files`
- [[Server mailbridge]] – `mailbridge`

## Wird genutzt von

- [[Routen features_messages]]

## Tests

`tests/test_mail.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
