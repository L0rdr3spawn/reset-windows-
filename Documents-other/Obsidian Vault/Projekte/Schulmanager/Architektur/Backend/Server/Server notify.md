---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/notify.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server notify

> Server-Kern · 1 Datei(en) · 499 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Benachrichtigungen bei Änderungen im Vertretungsplan: ein Hintergrund-Thread vergleicht nach jedem `change` die Tagespläne für heute und den nächsten Schultag mit dem zuletzt bekannten Stand und legt Einträge in `notifications_outbox` (E-Mail, SMS, Webhook) ab; ein Dispatcher stellt mit Wiederholung zu. Webhooks werden mit [[Modul integrations]] signiert.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/notify.py` | 499 | Benachrichtigungen bei Änderungen im Vertretungsplan. |

## Wichtige Funktionen und Klassen

- Funktion `kick` (`schulmanager/server/notify.py:62`) – Weckt den Dispatcher (nach einer Änderung).
- Funktion `start_dispatcher` (`schulmanager/server/notify.py:72`) – Startet den Hintergrund-Thread (idempotent). `False` wenn per Konfiguration deaktiviert.
- Funktion `stop_dispatcher` (`schulmanager/server/notify.py:96`)
- Funktion `is_running` (`schulmanager/server/notify.py:112`)
- Funktion `reset_state` (`schulmanager/server/notify.py:116`) – Vergisst den zuletzt bekannten Planstand (Tests / nach Komplettimport).
- Funktion `diff_entries` (`schulmanager/server/notify.py:158`) – Vergleicht zwei Stände `{key: entry}` → `{"added","changed","removed"}`.
- Funktion `check_changes` (`schulmanager/server/notify.py:166`) – Vergleicht heute/nächster Schultag mit dem letzten Stand, erzeugt Outbox-Einträge.
- Funktion `backoff_seconds` (`schulmanager/server/notify.py:362`)
- Funktion `prepare_webhook` (`schulmanager/server/notify.py:379`) – Body für die Zustellung: `sent_at` wird beim (erneuten) Senden aktualisiert (Replay-Schutz
- Funktion `send_webhook` (`schulmanager/server/notify.py:407`) – POST mit JSON-Body (signiert); wirft bei Fehler/Nicht-2xx.
- Funktion `send_email` (`schulmanager/server/notify.py:416`) – SMTP-Versand; `attachments` = `[{"filename", "content_type", "data": bytes}]` (§11.2).
- Funktion `dispatch_pending` (`schulmanager/server/notify.py:454`) – Stellt fällige Outbox-Einträge zu (Retry mit exponentiellem Backoff).

## Datenbank-Tabellen

- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul integrations]] – `webhooks` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `auth_messages` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_common]]
- [[Routen features_exchange]]
- [[Routen features_messages]]
- [[Server konten und anmeldung]] – `auth_messages`
- [[Server letters und pdf]] – `letters`

## Tests

`tests/test_contact.py`, `tests/test_server_features.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
