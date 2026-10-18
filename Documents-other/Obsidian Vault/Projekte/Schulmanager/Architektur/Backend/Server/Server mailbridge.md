---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/mailbridge.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server mailbridge

> Server-Kern · 1 Datei(en) · 519 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

E-Mail-Brücke des Postfachs: verbundene Konten (Google, Microsoft, GMX, Web.de, T-Online, Yahoo, eigener Server) per IMAP/SMTP abrufen und senden, Antworten per Message-ID den Unterhaltungen zuordnen. Zugangsdaten nur verschlüsselt. Steuerung über [[Routen features_mail]], Abruf im Hintergrund (`SM_MAIL_SYNC`).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/mailbridge.py` | 519 | E-Mail-Brücke des Postfachs: verbundene E-Mail-Konten (IMAP/SMTP) senden und empfangen. |

## Wichtige Funktionen und Klassen

- Klasse `Provider` (`schulmanager/server/mailbridge.py:54`)
- Funktion `guess_provider` (`schulmanager/server/mailbridge.py:90`)
- Klasse `OAuthApp` (`schulmanager/server/mailbridge.py:100`)
- Funktion `oauth_app` (`schulmanager/server/mailbridge.py:109`)
- Funktion `oauth_redirect_uri` (`schulmanager/server/mailbridge.py:128`)
- Funktion `make_state` (`schulmanager/server/mailbridge.py:138`)
- Funktion `read_state` (`schulmanager/server/mailbridge.py:145`)
- Funktion `authorize_url` (`schulmanager/server/mailbridge.py:156`)
- Funktion `exchange_code` (`schulmanager/server/mailbridge.py:183`) – Code → Tokens; liefert `{"email", "name", "secret": {...}}`.
- Funktion `refresh_access` (`schulmanager/server/mailbridge.py:197`)
- Klasse `Creds` (`schulmanager/server/mailbridge.py:212`) – Entschlüsselte Zugangsdaten eines Kontos (nur im Speicher).
  - Methoden: `bearer`:224
- Klasse `MailError` (`schulmanager/server/mailbridge.py:234`) – Verständliche Fehlermeldung für die Oberfläche (ohne Zugangsdaten).
- Klasse `FetchedMail` (`schulmanager/server/mailbridge.py:255`)
- Klasse `Transport` (`schulmanager/server/mailbridge.py:260`) – Echter Netzwerkzugriff per `imaplib`/`smtplib`.
  - Methoden: `imap_login`:263, `check`:283, `send`:315, `fetch`:324
- Funktion `new_message_id` (`schulmanager/server/mailbridge.py:370`)
- Funktion `build_mail` (`schulmanager/server/mailbridge.py:375`) – `to`/`cc` = `[(Name, Adresse)]`; BCC-Adressen stehen nicht im Kopf (nur als Empfänger beim Versand).
- Funktion `html_to_text` (`schulmanager/server/mailbridge.py:407`)
- Klasse `ParsedMail` (`schulmanager/server/mailbridge.py:417`)
- Funktion `parse_mail` (`schulmanager/server/mailbridge.py:434`)
- Funktion `start` (`schulmanager/server/mailbridge.py:491`)
- Funktion `stop` (`schulmanager/server/mailbridge.py:507`)
- Funktion `kick` (`schulmanager/server/mailbridge.py:517`)

## Hängt ab von

- [[Server config]] – `config` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_mail]]

## Tests

`tests/test_mail.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
