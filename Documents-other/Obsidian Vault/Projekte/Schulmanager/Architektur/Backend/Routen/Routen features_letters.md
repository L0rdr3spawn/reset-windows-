---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_letters.py"
stand: 2026-10-12 22:45
generator: schulmanager-regen
---

# Routen features_letters

> API-Routen · 1 Datei(en) · 385 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Zugangsbriefe (§11.3): Stapel mit Startpasswörtern als PDF/ZIP herunterladen oder per E-Mail versenden.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_letters.py` | 385 | Zugangsbriefe (§11.3): Stapel mit Startpasswörtern als PDF/ZIP herunterladen oder per E-Mail versen… |

## Endpunkte (9)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| POST | `/api/v1/letters/batches` | `create_batch` (`features_letters.py:103`) | users.manage | [[Feature classes]], [[Feature zugangsdaten]] |
| GET | `/api/v1/letters/batches/{batch_id}` | `get_batch` (`features_letters.py:175`) | - | [[Feature zugangsdaten]] |
| GET | `/api/v1/letters/batches/{batch_id}/pdf` | `batch_pdf` (`features_letters.py:215`) | - | – |
| GET | `/api/v1/letters/batches/{batch_id}/zip` | `batch_zip` (`features_letters.py:227`) | - | – |
| GET | `/api/v1/letters/batches/{batch_id}/entries/{user_id}.pdf` | `entry_pdf` (`features_letters.py:239`) | - | – |
| POST | `/api/v1/letters/batches/{batch_id}/send` | `send_batch` (`features_letters.py:255`) | - | [[Feature zugangsdaten]] |
| GET | `/api/v1/users/{user_id}/password` | `password_info` (`features_letters.py:277`) | - | [[Feature zugangsdaten]] |
| POST | `/api/v1/users/{user_id}/password` | `set_password` (`features_letters.py:289`) | - | [[Feature zugangsdaten]] |
| GET | `/api/v1/classes/{class_id}/accounts` | `class_accounts` (`features_letters.py:347`) | - | [[Feature classes]], [[Feature students]], [[Feature zugangsdaten]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `BatchIn` (`schulmanager/server/routes/features_letters.py:48`)
- Klasse `PasswordIn` (`schulmanager/server/routes/features_letters.py:55`)
- Klasse `SendIn` (`schulmanager/server/routes/features_letters.py:61`)
- Funktion `resetter` (`schulmanager/server/routes/features_letters.py:73`) – `users.manage` oder `passwords.reset` (Datenumfang prüft `` je Konto).

## Datenbank-Tabellen

- **Nutzt:** `account_initial_passwords`, `auth_codes`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen users]] – `users` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server config]] – `config` *(nur zur Laufzeit importiert)*
- [[Server db]] – `contact`, `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server konten und anmeldung]] – `accounts`, `auth_messages`, `security` *(nur zur Laufzeit importiert)*
- [[Server letters und pdf]] – `letters`
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_class_curriculum.py`, `tests/test_classes.py`, `tests/test_contact.py`, `tests/test_curricula.py`, `tests/test_demo_public.py`, `tests/test_letters.py`, `tests/test_license.py`, `tests/test_login_policy.py`, `tests/test_messages.py`, `tests/test_multi_account.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
