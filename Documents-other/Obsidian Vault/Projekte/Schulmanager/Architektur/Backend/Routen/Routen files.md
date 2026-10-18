---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/files.py"
stand: 2026-10-12 21:44
generator: schulmanager-regen
---

# Routen files

> API-Routen · 1 Datei(en) · 98 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Dateien: verschlüsselter Upload/Download (Basisdienst, ARCHITECTURE.md §9.2).

* `POST /files` – `multipart/form-data` mit `file` (+ `purpose` als Feld oder `?purpose=`) → 201
  `{id, filename, size, content_type, kind, …}`. Fehler: 413 `file_too_large`/`quota_exceeded`,
  415 `unsupported_type`/`blocked_type`, 422 `virus_found`/`empty_file`, 503 `scan_failed`
  (`detail = {"code", "message"}`).
* `GET /files/{id}` (`?inline=1` nur für PDF/Bilder außer SVG) – Eigentümer oder registrierter Access-Check des
  `ref_type`; sonst 404. Abrufe fremder Dateien werden protokolliert (`file.download`, je Tag einmal).
* `GET /files/{id}/meta`, `DELETE /files/{id}` (nur Eigentümer, nur nicht angehängte Dateien),
  `GET /files` (eigene Dateien), `GET /files/limits` (Limits, Kontingent, erlaubte Typen).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/files.py` | 98 | Dateien: verschlüsselter Upload/Download (Basisdienst, ARCHITECTURE.md §9.2). |

## Endpunkte (6)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/files/limits` | `file_limits` (`files.py:40`) | (angemeldet) | – |
| GET | `/api/v1/files` | `my_files` (`files.py:49`) | (angemeldet) | – |
| POST | `/api/v1/files` | `upload_file` (`files.py:58`) | (angemeldet) | – |
| GET | `/api/v1/files/{file_id}/meta` | `file_meta` (`files.py:70`) | (angemeldet) | – |
| GET | `/api/v1/files/{file_id}` | `download_file` (`files.py:76`) | (angemeldet) | – |
| DELETE | `/api/v1/files/{file_id}` | `delete_file` (`files.py:87`) | (angemeldet) | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Hängt ab von

- [[Server db]] – `db`
- [[Server deps]] – `deps`
- [[Server events]] – `events`
- [[Server files]] – `files`

## Wird genutzt von

- –

## Tests

`tests/test_attendance.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_channels_rooms.py`, `tests/test_files_crypto.py`, `tests/test_forms.py`, `tests/test_makeups.py`, `tests/test_messages.py`, `tests/test_ops_config.py`, `tests/test_student_self.py`, `tests/test_support.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
