---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/ (7 Dateien)"
stand: 2026-10-12 22:30
generator: schulmanager-regen
---

# Server konten und anmeldung

> Server-Kern · 7 Datei(en) · 2427 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Alles rund um Konten und Anmeldewege: `security` (Passwort-Hash scrypt, Token-Hash HMAC, TOTP, Konstantzeit-Vergleich), `accounts` (Konten anlegen/Startpasswörter), `login_policy` (wer darf sich wie anmelden: Person > Klasse > Jahrgang > Rolle), `identities` und `sso_providers` (Microsoft, Apple, Google, Schulkonto/OIDC), `auth_messages` und `sms` (Codes/Links per E-Mail bzw. SMS über die Outbox). Genutzt von [[Routen auth]], [[Routen users]], [[Routen features_sso]], [[Routen features_contact]], [[Routen features_login_policy]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/accounts.py` | 259 | Kontenlogik (von Routern, Bootstrap, Demo und SSO gemeinsam genutzt). |
| `schulmanager/server/auth_messages.py` | 248 | E-Mail/SMS für Konto-Vorgänge (Codes, Links, Zugangsbriefe) – docs/ARCHITECTURE.md §11.2. |
| `schulmanager/server/identities.py` | 203 | Verbundene Anbieter-Konten (Microsoft, Apple, Google, Schulkonto) – docs/ARCHITECTURE.md §11.4. |
| `schulmanager/server/login_policy.py` | 452 | Anmelde-Richtlinien: wer darf sich wie anmelden (docs/ARCHITECTURE.md §11.5). |
| `schulmanager/server/security.py` | 226 | Kryptografische Grundbausteine (nur Standardbibliothek). |
| `schulmanager/server/sms.py` | 207 | SMS-Versand (§11.2) – nur Standardbibliothek (`urllib`), Zustellung über die Outbox (Art `sms`). |
| `schulmanager/server/sso_providers.py` | 832 | Anmeldedienste Microsoft, Apple, Google und Schulkonto (OIDC) – docs/ARCHITECTURE.md §11.4. |

## Wichtige Funktionen und Klassen

- Funktion `user_dict` (`schulmanager/server/accounts.py:36`)
- Funktion `normalize_username` (`schulmanager/server/accounts.py:50`) – Erlaubt: a-z 0-9 . _ - (klein); Umlaute werden umgeschrieben.
- Funktion `username_taken` (`schulmanager/server/accounts.py:56`)
- Funktion `unique_username` (`schulmanager/server/accounts.py:60`) – `base`, sonst `base2`, `base3` … (prüft `reserved` und – mit `check_db` – die DB).
- Funktion `create_user` (`schulmanager/server/accounts.py:73`) – Legt ein Konto an (ohne Commit). Ohne `password` wird ein Startpasswort erzeugt und zurückgegeben.
- Funktion `set_children` (`schulmanager/server/accounts.py:102`)
- Funktion `student_username_base` (`schulmanager/server/accounts.py:122`)
- Funktion `bulk_create` (`schulmanager/server/accounts.py:136`) – Legt Konten für alle Schüler/Lehrkräfte/Eltern ohne Konto an (ohne Commit).
- Funktion `create_session` (`schulmanager/server/accounts.py:206`) – Neue Sitzung (ohne Commit). Gibt (Klartext-Token für das Cookie, Sitzung) zurück.
- Funktion `revoke_sessions` (`schulmanager/server/accounts.py:219`)
- Funktion `session_dict` (`schulmanager/server/accounts.py:226`)
- Funktion `token_dict` (`schulmanager/server/accounts.py:232`)
- Funktion `delete_user` (`schulmanager/server/accounts.py:239`) – Löscht ein Konto vollständig; Protokolle werden pseudonymisiert (ohne Commit).
- Funktion `count_active_admins` (`schulmanager/server/accounts.py:257`)
- Funktion `email_available` (`schulmanager/server/auth_messages.py:42`) – E-Mail lässt sich wirklich zustellen: SMTP eingerichtet **und** Versand (Dispatcher) nicht abgeschaltet.
- Funktion `sms_available` (`schulmanager/server/auth_messages.py:49`) – Ein SMS-Anbieter ist eingerichtet (oder – nur in der Entwicklung – der Test-Postausgang).
- Funktion `dev_outbox_enabled` (`schulmanager/server/auth_messages.py:55`)
- Funktion `valid_email` (`schulmanager/server/auth_messages.py:60`) – Einfache Formatprüfung (eine Adresse, keine Kopfzeilen-Sonderzeichen).
- Funktion `mask_email` (`schulmanager/server/auth_messages.py:65`) – `maria.muster@schule.de` → `m•••@schule.de` (für `notifications_outbox.target` und Anzeigen).
- Funktion `queue_email` (`schulmanager/server/auth_messages.py:96`) – E-Mail (verschlüsselt) in die Outbox. `None`, wenn weder SMTP noch Test-Postausgang verfügbar sind.
- Funktion `queue_sms` (`schulmanager/server/auth_messages.py:122`) – SMS (verschlüsselt) in die Outbox. `None`, wenn weder Anbieter noch Test-Postausgang verfügbar sind.
- Funktion `deliver` (`schulmanager/server/auth_messages.py:159`) – Stellt einen `secure_email`/`sms`-Eintrag zu (vom Dispatcher aufgerufen; wirft bei Fehlern).
- Funktion `dev_outbox_messages` (`schulmanager/server/auth_messages.py:199`) – Die letzten Test-Nachrichten (neueste zuerst), entschlüsselt.
- Funktion `dev_outbox_attachment` (`schulmanager/server/auth_messages.py:216`) – Anhang `index` einer Test-Nachricht oder `None`.
- Funktion `purge_dev_outbox` (`schulmanager/server/auth_messages.py:232`) – Wartung: Test-Nachrichten älter als `` löschen; Klartext (verschlüsselt) endgültig
- Funktion `linked_providers` (`schulmanager/server/identities.py:26`) – Anbieter mit bestätigter Verknüpfung (`subject` gesetzt) – eine Abfrage, wird bei jeder Anfrage genutzt.
- Funktion `available_providers` (`schulmanager/server/identities.py:45`) – `[{id, label, mock, flow, auto, client_id?, redirect_uri?}]` der nutzbaren Anbieter (Reihenfolge wie
- Funktion `provider_label` (`schulmanager/server/identities.py:71`)
- Funktion `identity_rows` (`schulmanager/server/identities.py:80`)
- Funktion `public_identity` (`schulmanager/server/identities.py:90`) – Darstellung für Profil und Benutzerverwaltung – ohne `subject`.
- Funktion `find_login_user` (`schulmanager/server/identities.py:101`) – Anbieter-Konto → `(User | None, UserIdentity | None, wie)` (ohne Commit).
- Klasse `EffectivePolicy` (`schulmanager/server/login_policy.py:60`)
  - Methoden: `public`:68
- Klasse `PolicyError` (`schulmanager/server/login_policy.py:77`) – Ungültige Regel (deutscher Text für die Antwort 422).
- Funktion `role_label` (`schulmanager/server/login_policy.py:99`)
- Funktion `scope_label` (`schulmanager/server/login_policy.py:109`) – Lesbare Herkunft einer Regel, z. B. „Klasse 5a · Schüler/innen“, „Jahrgang 7“, „Rolle Eltern“, „Standard“.
- Funktion `invalidate_cache` (`schulmanager/server/login_policy.py:133`) – Zwischenspeicher der Regeln verwerfen (nach dem Commit einer Änderung).
- Funktion `load_rules` (`schulmanager/server/login_policy.py:167`) – Alle Regeln `(scope, scope_ref, audience) → {feld: wert|None}` (prozessweit kurz zwischengespeichert).
- Funktion `group_levels` (`schulmanager/server/login_policy.py:244`) – Stufen einer Zielgruppe (Klasse, Jahrgang …) – je Bereich die Zielgruppe vor „alle“.
- Funktion `resolve` (`schulmanager/server/login_policy.py:306`) – Löst die Felder über `head` (Person) → je Gruppe (Klasse/Jahrgang) → Rolle → Standard auf.
- Funktion `effective_policy` (`schulmanager/server/login_policy.py:338`) – Wirksame Richtlinie für `user` (`db_models.User` oder `deps.AuthUser`).
- Funktion `method_allowed` (`schulmanager/server/login_policy.py:358`)
- Funktion `group_policy` (`schulmanager/server/login_policy.py:362`) – Vorschau: Richtlinie eines (gedachten) Mitglieds der Klasse bzw. des Jahrgangs (Zielgruppe schueler|eltern).
- Funktion `role_policy` (`schulmanager/server/login_policy.py:369`) – Vorschau: Richtlinie eines Kontos der Rolle ohne Klassen-/Personen-Regeln.
- Funktion `missing_links` (`schulmanager/server/login_policy.py:375`) – Pflicht-Anbieter, die `user` noch nicht verbunden hat (Reihenfolge wie `identities.PROVIDERS`).
- Funktion `available_provider_ids` (`schulmanager/server/login_policy.py:386`)
- … und 68 weitere öffentliche Definitionen (nur die wichtigsten sind aufgeführt)

## Datenbank-Tabellen

- **Nutzt:** `announcements`, `audit_log`, `notifications_outbox`, `school_versions` → [[Datenmodell#Planungsdokument und Protokoll]]
- **Nutzt:** `api_tokens`, `login_attempts`, `login_policy_rules`, `parent_links`, `sessions`, `sso_providers`, `user_identities`, `users` → [[Datenmodell#Konten und Anmeldung]]
- **Nutzt:** `student_absence_events` → [[Datenmodell#Sonstige Tabellen]]
- **Nutzt:** `student_absences` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul models]] – `models`
- [[Routen oidc]] – `oidc` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*
- [[Server db]] – `absence_log`, `db`, `db_models`, `identities`, `login_policy`
- [[Server notify]] – `notify` *(nur zur Laufzeit importiert)*
- [[Server permissions]] – `permissions`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen auth]]
- [[Routen features_api_access]]
- [[Routen features_contact]]
- [[Routen features_letters]]
- [[Routen features_login_policy]]
- [[Routen features_sso]]
- [[Routen me]]
- [[Routen oidc]]
- [[Routen users]]
- [[Server app]] – `app`
- [[Server betrieb]] – `bootstrap`, `cli`, `demo_loader`
- [[Server db]] – `login_policy`
- [[Server deps]]
- [[Server letters und pdf]] – `letters`
- [[Server middleware und metrics]] – `middleware`
- [[Server notify]]

## Tests

`tests/test_contact.py`, `tests/test_lead_integration.py`, `tests/test_letters.py`, `tests/test_login_policy.py`, `tests/test_self_reset.py`, `tests/test_server_core.py`, `tests/test_server_features.py`, `tests/test_sso.py`, `tests/test_sso_browser.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
