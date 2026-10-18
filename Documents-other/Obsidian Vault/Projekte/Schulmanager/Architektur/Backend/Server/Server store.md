---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/store.py"
stand: 2026-10-12 21:42
generator: schulmanager-regen
---

# Server store

> Server-Kern · 1 Datei(en) · 261 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

`SchoolStore`: hält das Planungsdokument ([[Modul models]]) als In-Memory-Arbeitskopie und speichert jede Änderung als neue Version in `school_versions` (zlib-JSON mit SHA-256). `store.mutate(user, text, fn, scope, dates)` arbeitet auf einer tiefen Kopie, schreibt Version + Audit (`plan.change`) und veröffentlicht ein `change`-Ereignis über [[Server events]]. Verlauf, Wiederherstellen und Undo laufen darüber ([[Routen history]]). Mehrere Prozesse würden sich nur alle 2 s abgleichen – deshalb ein Worker.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/store.py` | 261 | Versioniertes Planungsdokument (`School`) mit In-Memory-Arbeitskopie. |

## Wichtige Funktionen und Klassen

- Funktion `encode_school` (`schulmanager/server/store.py:44`) – `School` → (zlib-JSON, SHA-256 des JSON).
- Funktion `decode_school` (`schulmanager/server/store.py:50`)
- Funktion `copy_school` (`schulmanager/server/store.py:54`) – Tiefe Kopie über das verlustfreie Dict-Format.
- Klasse `StoreError` (`schulmanager/server/store.py:59`) – Fehler bei Verlauf/Wiederherstellung (z. B. Version existiert nicht).
- Klasse `SchoolStore` (`schulmanager/server/store.py:63`)
  - Methoden: `load`:74, `sync`:101, `mutate`:144, `replace`:160, `history`:172, `count_versions`:185, `get_version`:189, `restore`:197, `undo`:204, `digest`:224, `info`:228
- Funktion `get_store` (`schulmanager/server/store.py:236`) – Globaler Store (lädt bei Bedarf; prüft höchstens alle 2 s auf neuere Versionen anderer Prozesse).
- Funktion `reset_store` (`schulmanager/server/store.py:256`) – Verwirft den globalen Store (Tests / neue App-Instanz).

## Datenbank-Tabellen

- **Nutzt:** `school_versions` → [[Datenmodell#Planungsdokument und Protokoll]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul models]] – `models`
- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`
- [[Server events]] – `events`
- [[Server runtime]] – `runtime` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen admin]]
- [[Routen auth]]
- [[Routen events]]
- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_contact]]
- [[Routen features_data]]
- [[Routen features_exchange]]
- [[Routen features_letters]]
- [[Routen features_login_policy]]
- [[Routen features_messages]]
- [[Routen features_planning]]
- [[Routen features_teacher_profile]]
- [[Routen history]]
- [[Routen me]]
- [[Routen rights]]
- [[Routen setup]]
- [[Routen system]]
- [[Routen users]]
- [[Server app]] – `app`
- [[Server betrieb]] – `backups`, `bootstrap`, `demo_loader`
- [[Server elternzugriff]] – `parent_access`
- [[Server holiday_import]]
- [[Server konten und anmeldung]] – `login_policy`
- [[Server letters und pdf]] – `letters`
- [[Server licensing]]
- [[Server runtime]]

## Tests

`tests/test_api_access.py`, `tests/test_attendance.py`, `tests/test_autoplan.py`, `tests/test_calendar.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_channels_rooms.py`, `tests/test_chat_split.py`, `tests/test_chats.py`, `tests/test_class_curriculum.py`, `tests/test_class_room_info.py`, `tests/test_classes.py` …

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
