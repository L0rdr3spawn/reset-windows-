---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/crypto.py"
stand: 2026-10-12 22:04
generator: schulmanager-regen
---

# Server crypto

> Server-Kern · 1 Datei(en) · 634 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Umschlagverschlüsselung mit AES-256-GCM: je Objekt ein eigener Datenschlüssel (DEK), gewrappt mit dem aktiven Master-Schlüssel aus `SM_ENCRYPTION_KEYS`. `encrypt_text(text, aad)` / `decrypt_text` für personenbezogene Freitexte (Nachrichten, Atteste, Gründe, Noten), `StreamEncryptor` für Dateien, `rewrap` für Schlüsselrotation, `register_rewrap` damit jede verschlüsselte Spalte bei der Rotation erfasst wird.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/crypto.py` | 634 | Umschlagverschlüsselung (Envelope Encryption) mit AES-256-GCM. |

## Wichtige Funktionen und Klassen

- Klasse `CryptoError` (`schulmanager/server/crypto.py:79`) – Basisklasse aller Verschlüsselungsfehler.
- Klasse `InvalidToken` (`schulmanager/server/crypto.py:83`) – Token beschädigt, manipuliert, falsches AAD oder falscher Schlüssel.
- Klasse `UnknownKeyError` (`schulmanager/server/crypto.py:87`) – Die Schlüssel-ID des Tokens ist nicht (mehr) im Schlüsselring `SM_ENCRYPTION_KEYS`.
- Klasse `KeyRing` (`schulmanager/server/crypto.py:92`) – Master-Schlüssel (`kid` → 32 Byte); `active` verschlüsselt neue Daten.
  - Methoden: `key_ids`:107, `aead`:110, `fingerprint`:117
- Funktion `parse_keys` (`schulmanager/server/crypto.py:129`) – `"kid:base64,kid2:base64"` → `[(kid, key32), …]` (erster = aktiv). Fehler → ``.
- Funktion `derive_dev_key` (`schulmanager/server/crypto.py:157`) – Entwicklungsschlüssel aus `SM_SECRET_KEY` (HKDF-SHA256) – nie in Produktion verwenden.
- Funktion `generate_key` (`schulmanager/server/crypto.py:163`) – Neuer Eintrag für `SM_ENCRYPTION_KEYS`: `"<kid>:<base64 32 Byte>"` (kid Standard: `kJJJJMMTT`).
- Funktion `keyring` (`schulmanager/server/crypto.py:176`) – Aktueller Schlüsselring (aus `config`; wird bei geänderter Konfiguration neu aufgebaut).
- Funktion `reset` (`schulmanager/server/crypto.py:205`) – Verwirft den zwischengespeicherten Schlüsselring (Tests).
- Funktion `active_key_id` (`schulmanager/server/crypto.py:213`) – ID des Schlüssels, mit dem neue Daten verschlüsselt werden.
- Funktion `describe` (`schulmanager/server/crypto.py:218`) – Status ohne Schlüsselmaterial (für Systemansicht/CLI).
- Funktion `encrypt` (`schulmanager/server/crypto.py:272`) – Verschlüsselt `data` mit eigenem Datenschlüssel → binäres `SM1`-Token.
- Funktion `decrypt` (`schulmanager/server/crypto.py:286`) – Entschlüsselt ein `SM1`-Token; `` bei Manipulation/falschem AAD.
- Funktion `encrypt_text` (`schulmanager/server/crypto.py:317`) – Verschlüsselt Text → ASCII-Token `"SM1.…"` (für `Text`-Spalten).
- Funktion `decrypt_text` (`schulmanager/server/crypto.py:324`) – Gegenstück zu ``.
- Funktion `is_token` (`schulmanager/server/crypto.py:333`) – Sieht `value` wie ein Token dieses Moduls aus (`SM1.`-Text, `SM1`/`SMS1`-Binär)?
- Funktion `key_id_of` (`schulmanager/server/crypto.py:343`) – Schlüssel-ID eines Tokens (Text, `SM1` oder `SMS1`-Kopf) – ohne zu entschlüsseln.
- Funktion `rewrap` (`schulmanager/server/crypto.py:350`) – Schlüsselrotation: wrappt den Datenschlüssel mit dem aktiven Master-Schlüssel neu.
- Funktion `needs_rewrap` (`schulmanager/server/crypto.py:370`)
- Funktion `reencrypt` (`schulmanager/server/crypto.py:374`) – Vollständige Neuverschlüsselung mit neuem Datenschlüssel (z. B. nach Kompromittierung eines Master-Schlüssels).
- Klasse `StreamEncryptor` (`schulmanager/server/crypto.py:393`) – Blockweise Verschlüsselung (`SMS1`). `header` zuerst schreiben, dann `update()`-Ausgaben, dann
  - Methoden: `update`:418, `finalize`:430
- Funktion `stream_header_length` (`schulmanager/server/crypto.py:439`) – Länge des `SMS1`-Kopfs (benötigt die ersten 5 Byte).
- Klasse `StreamDecryptor` (`schulmanager/server/crypto.py:446`) – Gegenstück zu ``; `header` = vollständiger Kopf (siehe ``).
  - Methoden: `update`:478, `finalize`:489
- Funktion `read_stream_header` (`schulmanager/server/crypto.py:500`) – Liest den `SMS1`-Kopf aus einer geöffneten Datei.
- Funktion `encrypt_stream` (`schulmanager/server/crypto.py:510`) – `src` (Klartext) → `dst` (`SMS1`). Gibt die Anzahl Klartext-Bytes zurück.
- Funktion `decrypt_stream` (`schulmanager/server/crypto.py:526`) – Entschlüsselt eine `SMS1`-Datei blockweise (Generator; Fehler erst beim betroffenen Block).
- Funktion `rewrap_stream_file` (`schulmanager/server/crypto.py:539`) – Wrappt den Datenschlüssel einer `SMS1`-Datei mit dem aktiven Schlüssel neu (atomar ersetzt).
- Funktion `register_rewrap` (`schulmanager/server/crypto.py:573`) – Registriert eine Funktion `fn(db) -> int`, die alle Tokens eines Bereichs mit `` neu wrappt.
- Funktion `rewrappers` (`schulmanager/server/crypto.py:584`)
- Funktion `rewrap_column` (`schulmanager/server/crypto.py:588`) – Hilfe für ``: wrappt alle Tokens einer Spalte (Text- oder Binär-Tokens) neu.
- Funktion `rewrap_all` (`schulmanager/server/crypto.py:622`) – Führt alle registrierten Rewrap-Funktionen aus (je eigene Transaktion) → `{name: anzahl}`.

## Hängt ab von

- [[Server config]] – `config`
- [[Server db]] – `db` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_channels]]
- [[Routen features_chats]]
- [[Routen features_contact]]
- [[Routen features_grades]]
- [[Routen features_mail]]
- [[Routen features_messages]]
- [[Routen features_register]]
- [[Routen features_sso]]
- [[Routen features_student_self]]
- [[Routen features_support]]
- [[Routen features_teacher_profile]]
- [[Server betrieb]] – `cli`
- [[Server chat_migration]]
- [[Server config]]
- [[Server db]] – `channels`, `chats`, `contact`, `files`, `grades`, `identities` …
- [[Server files]]
- [[Server konten und anmeldung]] – `auth_messages`, `sso_providers`
- [[Server letters und pdf]] – `letters`

## Tests

`tests/test_channels.py`, `tests/test_files_crypto.py`, `tests/test_messages.py`, `tests/test_student_self.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
