---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/files.py"
stand: 2026-10-12 21:40
generator: schulmanager-regen
---

# Server files

> Server-Kern · 1 Datei(en) · 1584 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Verschlüsselte Dateiablage als Basisdienst für Kursräume, Postfach und Atteste: ein Durchlauf zählt (Größenlimit), hasht, erkennt den Typ (Magic Bytes + Allowlist, aktive Inhalte blockiert), scannt optional mit ClamAV und verschlüsselt auf die Platte ([[Server crypto]]). Zugriff nur über `register_purpose` / `attach` / `register_access_check` – ohne Prüfung sieht nur der Eigentümer die Datei. Endpunkte: [[Routen files]]. Datei: ~1600 Zeilen, die zweitgrößte im Server-Kern.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/files.py` | 1584 | Verschlüsselte Dateiablage – Basisdienst für Kursräume, Postfach, Atteste (ARCHITECTURE.md §9.2). |

## Wichtige Funktionen und Klassen

- Klasse `FileError` (`schulmanager/server/files.py:75`) – Fehler der Dateiablage (`HTTPException` → kann direkt aus Routen kommen).
- Klasse `FileKind` (`schulmanager/server/files.py:94`)
- Funktion `split_ext` (`schulmanager/server/files.py:234`) – `"bericht.final.pdf"` → `("bericht.final", ".pdf")`; Endungen nur aus 1–10 Buchstaben/Ziffern.
- Funktion `clean_filename` (`schulmanager/server/files.py:240`) – Säubert einen Dateinamen: keine Pfade, Steuer-/Bidi-Zeichen, reservierten Zeichen/Namen; max. 180 Zeichen.
- Funktion `content_disposition` (`schulmanager/server/files.py:282`) – `attachment; filename="ascii"; filename*=UTF-8''…` (RFC 6266/5987, keine Header-Injektion).
- Klasse `Inspector` (`schulmanager/server/files.py:334`) – Erkennt den Dateityp blockweise (Magic Bytes) und sammelt Hinweise auf aktive Inhalte.
  - Methoden: `feed`:353, `finish`:367, `zip_entries`:416
- Funktion `classify` (`schulmanager/server/files.py:607`) – Ermittelt die Dateiart; `` 415 bei nicht erlaubten/aktiven Inhalten, 422 bei leerer Datei.
- Klasse `ClamAVStream` (`schulmanager/server/files.py:673`) – `INSTREAM`-Prüfung über clamd (TCP). Fehler werden gesammelt, nicht geworfen.
  - Methoden: `send`:691, `finish`:706, `close`:731
- Funktion `files_root` (`schulmanager/server/files.py:741`)
- Funktion `blob_path` (`schulmanager/server/files.py:751`) – Pfad des verschlüsselten Inhalts (ID wird streng geprüft → kein Path-Traversal).
- Klasse `UploadSink` (`schulmanager/server/files.py:763`) – Nimmt Klartext-Blöcke an: Limit, SHA-256, Typerkennung, Virenscan, Verschlüsselung → Temp-Datei.
  - Methoden: `write`:783, `write_many`:797, `finish`:801, `discard`:813
- Klasse `Purpose` (`schulmanager/server/files.py:827`)
- Funktion `register_purpose` (`schulmanager/server/files.py:851`) – Optionale Regeln je Zweck, z. B. `register_purpose("student_document", kinds=["pdf", "image"], max_mb=10)`.
- Funktion `purpose_rules` (`schulmanager/server/files.py:867`)
- Funktion `register_access_check` (`schulmanager/server/files.py:871`) – Zugriffsprüfung für angehängte Dateien: `fn(db, user, stored_file) -> bool` (`user` = `AuthUser`).
- Funktion `max_upload_bytes` (`schulmanager/server/files.py:882`)
- Funktion `quota_bytes` (`schulmanager/server/files.py:894`) – Speicherkontingent des Kontos (`None` = unbegrenzt; 0 MB in der Konfiguration = unbegrenzt).
- Funktion `usage_bytes` (`schulmanager/server/files.py:902`)
- Funktion `get_file` (`schulmanager/server/files.py:919`)
- Funktion `can_read` (`schulmanager/server/files.py:928`) – Eigentümer immer; sonst nur die registrierte Prüfung des `ref_type` (kein Admin-Generalschlüssel).
- Funktion `require_readable` (`schulmanager/server/files.py:944`) – Metadaten einer lesbaren Datei, sonst 404 (Existenz fremder Dateien wird nicht verraten).
- Funktion `file_info` (`schulmanager/server/files.py:952`) – JSON-Darstellung (für Listen; Frontend-Typ `StoredFileInfo`).
- Funktion `files_info` (`schulmanager/server/files.py:964`) – Mehrere Dateien (z. B. Anhänge) in gegebener Reihenfolge; fehlende/unlesbare werden ausgelassen.
- Funktion `store_bytes` (`schulmanager/server/files.py:1038`) – Speichert Daten verschlüsselt (gleiche Prüfungen wie der HTTP-Upload; `user=None` = System, ohne Quote).
- Funktion `store_upload` (`schulmanager/server/files.py:1057`) – Streamt einen `multipart/form-data`-Upload (Feld `file`, optional `purpose` bzw. `?purpose=`).
- Funktion `iter_plaintext` (`schulmanager/server/files.py:1183`) – Entschlüsselt den Inhalt blockweise (Generator). Fehlender/beschädigter Inhalt → ``.
- Funktion `read_bytes` (`schulmanager/server/files.py:1199`)
- Funktion `read_file` (`schulmanager/server/files.py:1207`) – Metadaten + Klartext (ohne Rechteprüfung – vorher ``/``!).
- Funktion `download_headers` (`schulmanager/server/files.py:1220`) – Sichere Header: `filename*`, `nosniff`, CSP `sandbox` (PDF inline: ohne sandbox, da sonst die
- Funktion `file_response` (`schulmanager/server/files.py:1241`) – Antwort mit sicheren Download-Headern (aktive Inhalte wie SVG nie inline).
- Funktion `stream_response` (`schulmanager/server/files.py:1246`) – Wie ``, aber kleine Dateien vollständig geprüft und große gestreamt (konstanter Speicher).
- Funktion `audit_download` (`schulmanager/server/files.py:1267`) – Protokolliert den Abruf einer fremden Datei (höchstens einmal je Konto, Datei und Tag). Ohne Commit.
- Funktion `attach` (`schulmanager/server/files.py:1288`) – Bindet eine eigene, noch nicht angehängte Datei an ein Objekt (`ref_type`/`ref_id`). Ohne Commit.
- Funktion `attach_many` (`schulmanager/server/files.py:1317`) – Mehrere Dateien anhängen (z. B. Nachrichtenanhänge); alle oder keine (Ausnahme bricht ab).
- Funktion `detach` (`schulmanager/server/files.py:1326`) – Löst die Bindung (Datei bleibt erhalten und wird nach 24 h ohne neue Bindung von der Wartung gelöscht).
- Funktion `delete` (`schulmanager/server/files.py:1338`) – Löscht eine Datei: weich (`deleted_at`, Inhalt wird nach 30 Tagen entfernt) oder mit `hard=True` sofort.
- Funktion `delete_many` (`schulmanager/server/files.py:1357`)
- Funktion `delete_for_ref` (`schulmanager/server/files.py:1361`) – Alle an ein Objekt gebundenen Dateien löschen (z. B. beim Löschen einer Nachricht/eines Materials).
- Funktion `duplicate` (`schulmanager/server/files.py:1368`) – Kopie mit neuem Datenschlüssel und neuem Eigentümer (z. B. Material in einen anderen Kurs übernehmen,
- Funktion `cleanup` (`schulmanager/server/files.py:1415`) – Wartung: nicht angehängte Uploads > 24 h und gelöschte Dateien > 30 Tage endgültig entfernen,
- Funktion `gc_blobs` (`schulmanager/server/files.py:1438`) – Entfernt Inhalte ohne Datenbankeintrag und alte Temp-Dateien (höchstens alle 12 h, `force` sofort).
- Funktion `verify_all` (`schulmanager/server/files.py:1532`) – Prüft alle Inhalte (Entschlüsselung + Prüfsumme) – für `cli verify-files` nach Restore/Umzug.
- Funktion `limits_info` (`schulmanager/server/files.py:1553`) – Grenzen und Allowlist für das Frontend (`GET /files/limits`).
- Funktion `may_upload` (`schulmanager/server/files.py:1571`)
- Funktion `list_own` (`schulmanager/server/files.py:1576`)

## Datenbank-Tabellen

- **Nutzt:** `stored_files` → [[Datenmodell#Dateien]]

## Hängt ab von

- [[Server audit]] – `audit` *(nur zur Laufzeit importiert)*
- [[Server config]] – `config`
- [[Server crypto]] – `crypto`
- [[Server db]] – `db`, `files`
- [[Server permissions]] – `permissions` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_channels]]
- [[Routen features_contact]]
- [[Routen features_forms]]
- [[Routen features_mail]]
- [[Routen features_messages]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]
- [[Routen features_support]]
- [[Routen files]]
- [[Routen users]]
- [[Server betrieb]] – `cli`, `maintenance`

## Tests

`tests/test_files_crypto.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
