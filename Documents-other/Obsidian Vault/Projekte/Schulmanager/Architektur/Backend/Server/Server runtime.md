---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/runtime.py"
stand: 2026-10-12 21:40
generator: schulmanager-regen
---

# Server runtime

> Server-Kern · 1 Datei(en) · 136 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Start und Stopp der Laufzeit: `ensure_started()` (idempotent) führt Alembic-Migrationen aus ([[Server db]]), startet [[Server betrieb]] `bootstrap.run` (Erst-Admin, Planungsdokument, optional Demo) und danach die Hintergrundaufgaben: Benachrichtigungen ([[Server notify]]), Auto-Planer ([[Server autoplan]]), Mail-Abruf ([[Server mailbridge]]), Lizenzprüfung ([[Server licensing]]), Ferien-Import ([[Server holiday_import]]) und die Wartungsschleife. **Genau ein Worker** – Store und SSE-Bus leben im Speicher.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/runtime.py` | 136 | Start/Stopp der Laufzeit: Migration, Bootstrap, Hintergrundaufgaben. |

## Wichtige Funktionen und Klassen

- Funktion `ensure_started` (`schulmanager/server/runtime.py:26`) – Migration + Bootstrap (Erst-Admin, Planungsdokument, ggf. Demo). Idempotent und thread-sicher.
- Funktion `is_started` (`schulmanager/server/runtime.py:56`)
- Funktion `reset` (`schulmanager/server/runtime.py:60`) – Setzt den Laufzeitzustand zurück (neue App-Instanz / Tests).
- Funktion `optional_module` (`schulmanager/server/runtime.py:72`) – Importiert `schulmanager.server.<name>`, falls vorhanden (sonst `None`).
- Funktion `startup` (`schulmanager/server/runtime.py:95`) – Lifespan-Start: Initialisierung im Thread (blockiert den Loop nicht), dann Hintergrundaufgaben.
- Funktion `shutdown` (`schulmanager/server/runtime.py:117`)

## Hängt ab von

- [[Server betrieb]] – `bootstrap`, `maintenance` *(nur zur Laufzeit importiert)*
- [[Server chat_migration]] – `chat_migration` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server db]] – `db`, `migrate` *(nur zur Laufzeit importiert)*
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen admin]]
- [[Routen events]]
- [[Server app]] – `app`
- [[Server betrieb]] – `cli`
- [[Server db]] – `db`
- [[Server store]]

## Tests

`tests/test_server_core_store.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
