---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/ (5 Dateien)"
stand: 2026-10-12 21:42
generator: schulmanager-regen
---

# Server betrieb

> Server-Kern · 5 Datei(en) · 969 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Betriebsfunktionen im Server: `bootstrap` (Erst-Admin, Planungsdokument, Demo), `demo_loader` (Demo-Konten), `backups` (JSON-/SQLite-Sicherungen mit Rotation), `maintenance` (abgelaufene Sitzungen/Tokens, alte Login-Versuche, optional Auto-Backup), `cli` (`schulmanager-admin`: Admin anlegen/zurücksetzen, Schlüsselrotation …). Über [[Routen admin]] bedienbar.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/backups.py` | 169 | Sicherungen nach `config.backup_dir` (Default `data/backups`). |
| `schulmanager/server/bootstrap.py` | 79 | Erststart: Erst-Admin, Planungsdokument, optional Demo-Schule. |
| `schulmanager/server/cli.py` | 354 | Betriebs-CLI: `python -m schulmanager.server.cli <befehl>`. |
| `schulmanager/server/demo_loader.py` | 264 | Demo-Schule laden (`POST /admin/demo`, `SM_LOAD_DEMO=1`) inkl. Demo-Konten. |
| `schulmanager/server/maintenance.py` | 103 | Wartung: abgelaufene Sitzungen/Tokens und alte Login-Versuche löschen, optional Auto-Backup. |

## Wichtige Funktionen und Klassen

- Funktion `backup_dir` (`schulmanager/server/backups.py:39`)
- Funktion `list_backups` (`schulmanager/server/backups.py:45`)
- Funktion `backup_path` (`schulmanager/server/backups.py:61`) – Pfad einer Sicherung oder `None` (Name wird streng geprüft → kein Path-Traversal).
- Funktion `export_tables` (`schulmanager/server/backups.py:95`) – Alle Tabellen als JSON-kompatibles Dict (Planversionen ohne Binärdaten außer der aktuellen).
- Funktion `create_backup` (`schulmanager/server/backups.py:115`) – Erstellt eine Sicherung und rotiert alte. Gibt `{name, size, kind}` zurück.
- Funktion `rotate` (`schulmanager/server/backups.py:149`)
- Funktion `delete_backup` (`schulmanager/server/backups.py:163`)
- Funktion `ensure_admin` (`schulmanager/server/bootstrap.py:21`) – Legt den Erst-Admin an, wenn noch kein Konto existiert. Gibt ein erzeugtes Passwort zurück.
- Funktion `run` (`schulmanager/server/bootstrap.py:65`) – Wird einmal pro Prozess beim Start aufgerufen (nach der Migration).
- Funktion `cmd_migrate` (`schulmanager/server/cli.py:67`)
- Funktion `cmd_create_admin` (`schulmanager/server/cli.py:75`)
- Funktion `cmd_reset_password` (`schulmanager/server/cli.py:107`)
- Funktion `cmd_unlock` (`schulmanager/server/cli.py:127`)
- Funktion `cmd_disable_2fa` (`schulmanager/server/cli.py:136`)
- Funktion `cmd_list_users` (`schulmanager/server/cli.py:147`)
- Funktion `cmd_load_demo` (`schulmanager/server/cli.py:160`)
- Funktion `cmd_backup` (`schulmanager/server/cli.py:175`)
- Funktion `cmd_maintenance` (`schulmanager/server/cli.py:186`)
- Funktion `cmd_migrate_chats` (`schulmanager/server/cli.py:194`) – Postfach-Gruppen/-Einzelchats nach „Chats & Gruppen“ übernehmen bzw. zurücknehmen (siehe chat_migration).
- Funktion `cmd_gen_key` (`schulmanager/server/cli.py:209`) – Gibt einen neuen Eintrag `id:base64` aus (stdout); Hinweise auf stderr.
- Funktion `cmd_rotate_keys` (`schulmanager/server/cli.py:246`)
- Funktion `cmd_crypto_status` (`schulmanager/server/cli.py:269`)
- Funktion `cmd_verify_files` (`schulmanager/server/cli.py:281`)
- Funktion `build_parser` (`schulmanager/server/cli.py:294`)
- Funktion `main` (`schulmanager/server/cli.py:343`)
- Funktion `build_demo_school` (`schulmanager/server/demo_loader.py:35`) – Baut die Demo-Schule und generiert den Stundenplan (CPU-intensiv, `time_limit` Sekunden).
- Funktion `demo_account_specs` (`schulmanager/server/demo_loader.py:97`)
- Funktion `is_demo_account` (`schulmanager/server/demo_loader.py:155`) – Vorgegebene Demo-Konten (inkl. `l-`/`s-`/`e-`-Konten aller Personen, ausgegebene `dz-`-Zugänge, Inhaber)
- Funktion `create_demo_accounts` (`schulmanager/server/demo_loader.py:162`) – Legt fehlende Demo-Konten an bzw. aktualisiert deren Verknüpfungen. Gibt die Kontenliste zurück.
- Funktion `create_directory_accounts` (`schulmanager/server/demo_loader.py:199`) – Demo: Konten für alle Lehrkräfte, Schüler/innen und je ein Elternkonto (falls noch nicht verknüpft).
- Funktion `load_demo` (`schulmanager/server/demo_loader.py:237`) – Baut die Demo, ersetzt das Planungsdokument (neue Version) und legt Demo-Konten an.
- Funktion `run_maintenance` (`schulmanager/server/maintenance.py:21`) – Einmaliger Wartungslauf (synchron). Rückgabe: Anzahl gelöschter Einträge je Tabelle.
- Funktion `maintenance_loop` (`schulmanager/server/maintenance.py:91`)

## Datenbank-Tabellen

- **Nutzt:** `api_tokens`, `login_attempts`, `parent_links`, `sessions`, `user_contacts`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul demo]] – `demo`
- [[Modul duties]] – `duties` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul planning]] – `planning`
- [[Modul scheduler]] – `scheduler`
- [[Modul timetable]] – `timetable` *(nur zur Laufzeit importiert)*
- [[Routen features_contact]] – `features_contact` *(nur zur Laufzeit importiert)*
- [[Routen features_forms]] – `features_forms` *(nur zur Laufzeit importiert)*
- [[Routen features_student_self]] – `features_student_self` *(nur zur Laufzeit importiert)*
- [[Server app]] – `__init__` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server chat_migration]] – `chat_migration` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*
- [[Server db]] – `contact`, `db`, `db_models`, `migrate`
- [[Server events]] – `events`
- [[Server files]] – `files` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `accounts`, `security`
- [[Server letters und pdf]] – `letters` *(nur zur Laufzeit importiert)*
- [[Server runtime]] – `runtime` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen admin]]
- [[Routen users]]
- [[Server deps]]
- [[Server runtime]]

## Tests

`tests/test_contact.py`, `tests/test_files_crypto.py`, `tests/test_letters.py`, `tests/test_server_core_store.py`, `tests/test_student_self.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
