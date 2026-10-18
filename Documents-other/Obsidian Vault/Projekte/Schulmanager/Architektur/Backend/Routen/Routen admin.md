---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/admin.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen admin

> API-Routen · 1 Datei(en) · 118 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Systemverwaltung (nur `system.admin`): Systeminfo, Sicherungen, Demo-Schule, Wartung.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/admin.py` | 118 | Systemverwaltung (nur `system.admin`): Systeminfo, Sicherungen, Demo-Schule, Wartung. |

## Endpunkte (7)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/admin/system` | `system_info` (`admin.py:33`) | system.admin | – |
| GET | `/api/v1/admin/backups` | `backups` (`admin.py:65`) | system.admin | [[Seite AdminPage]] |
| POST | `/api/v1/admin/backups` | `make_backup` (`admin.py:70`) | system.admin | [[Seite AdminPage]] |
| GET | `/api/v1/admin/backups/{name}` | `download_backup` (`admin.py:76`) | system.admin | – |
| DELETE | `/api/v1/admin/backups/{name}` | `remove_backup` (`admin.py:85`) | system.admin | [[Seite AdminPage]] |
| POST | `/api/v1/admin/demo` | `load_demo_school` (`admin.py:95`) | system.admin | [[Seite AdminPage]] |
| POST | `/api/v1/admin/maintenance` | `maintenance` (`admin.py:113`) | system.admin | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `DemoBody` (`schulmanager/server/routes/admin.py:26`)

## Datenbank-Tabellen

- **Nutzt:** `school_versions` → [[Datenmodell#Planungsdokument und Protokoll]]
- **Nutzt:** `sessions`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server betrieb]] – `backups`, `demo_loader`, `maintenance`
- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`, `migrate`
- [[Server deps]] – `deps`
- [[Server events]] – `events`
- [[Server runtime]] – `runtime`
- [[Server store]] – `store`

## Wird genutzt von

- –

## Tests

`tests/test_demo_public.py`, `tests/test_server_core.py`, `tests/test_server_core_store.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
