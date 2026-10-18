---
tags: [schulmanager, architektur, backend]
quelle: "schulmanager/, lizenzserver/"
stand: 2026-10-12 22:48
generator: schulmanager-regen
---

# Backend Übersicht

> Einstieg: [[Schulmanager Architektur]] · Python 3.11+, FastAPI, SQLAlchemy 2, Alembic

Das Backend besteht aus drei Schichten, die in dieser Reihenfolge voneinander abhängen sollen: **Fachlogik** (reine Rechenmodule über dem Planungsdokument), **Server-Kern** (App, Anmeldung, Rechte, Store, DB, Dienste) und **Routen** (HTTP-Endpunkte). Daneben steht der eigenständige [[Lizenzserver]]. Abweichungen von dieser Schichtung sind in [[Abhängigkeiten]] unter „Auffälligkeiten“ gelistet.

## Fachlogik (`schulmanager/*.py`)

Reine Funktionen und Dataclasses, kein Datenbank- und kein HTTP-Zugriff. Gemeinsame Grundlage: [[Modul models]] und [[Modul calendar_utils]] / [[Modul weeks]].

| Notiz | Zeilen | Dateien | Aufgabe |
|---|---|---|---|
| [[Modul autoplan]] | 343 | 1 | Reine Logik des Auto-Planers: |
| [[Modul calendar_utils]] | 335 | 1 | Kalender-Hilfen über dem Planungsdokument: |
| [[Modul channels]] | 917 | 1 | Kursräume – reine Logik über dem Planungsdokument: |
| [[Modul demo]] | 316 | 1 | build_demo() erzeugt eine realistische, vollständig erfundene Beispielschule (~2600 Schüler, 98 Klassen, ~170 Lehrkräfte, 2 Standorte, Rhythmusklasse… |
| [[Modul duties]] | 307 | 1 | Pausenaufsichten: |
| [[Modul exams]] | 210 | 1 | Klassenarbeiten und Klausuren: |
| [[Modul forms]] | 569 | 1 |  |
| [[Modul integrations]] | 3626 | 7 | Datenaustausch mit anderen Systemen, alles reine Funktionen auf School: |
| [[Modul legacy]] | 201 | 1 | Umrechnung älterer Planungsdokumente auf das 52-Wochen-System: |
| [[Modul messaging]] | 828 | 1 | Internes Postfach – reine Logik: |
| [[Modul models]] | 564 | 1 | Das Planungsdokument: |
| [[Modul planning]] | 523 | 1 | Vorbereitung der Planung: |
| [[Modul scheduler]] | 1086 | 1 | Der Stundenplan-Generator: |
| [[Modul student_self]] | 99 | 1 | Schüler-Selbstbedienung – reine Logik ohne Datenbank (Regeln für eigene Krankmeldungen, Dokumente und Sichtbarkeit). |
| [[Modul substitution]] | 1779 | 1 | Die Vertretungs-Engine: |
| [[Modul teacher_profile]] | 768 | 1 | Lehrer-Selbstverwaltung: |
| [[Modul timetable]] | 652 | 1 | Ansichten und Prüfungen auf dem regulären Plan: |
| [[Modul weeks]] | 414 | 1 | Wochenangaben im 52-Wochen-System und die zentrale Aktiv-Logik: |

## Server-Kern (`schulmanager/server/*.py`)

Eingang ist [[Server app]]; Start-Reihenfolge steht in [[Server runtime]].

| Notiz | Zeilen | Dateien | Aufgabe |
|---|---|---|---|
| [[Server absence_log]] | 238 | 1 |  |
| [[Server api_scopes]] | 468 | 1 |  |
| [[Server app]] | 249 | 3 | Erzeugt die FastAPI-Anwendung (create_app): |
| [[Server audit]] | 57 | 1 | audit(db, user, aktion, ziel, details): |
| [[Server autoplan]] | 407 | 1 | Hintergrunddienst des Auto-Planers: |
| [[Server betrieb]] | 969 | 5 | Betriebsfunktionen im Server: |
| [[Server chat_migration]] | 286 | 1 |  |
| [[Server config]] | 363 | 1 | Konfiguration aus Umgebungsvariablen SM_ (config-Objekt, reload(), validate()): |
| [[Server crypto]] | 634 | 1 | Umschlagverschlüsselung mit AES-256-GCM: |
| [[Server db]] | 2281 | 25 | Datenbankanbindung (SQLAlchemy 2): |
| [[Server deps]] | 370 | 1 | FastAPI-Abhängigkeiten für Anmeldung und Rechte: |
| [[Server elternzugriff]] | 451 | 2 | Bausteine für Elternsicht: |
| [[Server events]] | 173 | 1 | Ereignisbus für Live-Updates: |
| [[Server files]] | 1584 | 1 | Verschlüsselte Dateiablage als Basisdienst für Kursräume, Postfach und Atteste: |
| [[Server form_pdf]] | 225 | 1 |  |
| [[Server holiday_import]] | 444 | 1 | Übernimmt Feiertage und Schulferien automatisch aus öffentlichen APIs (OpenHolidays; Nager.Date als Rückfall für gesetzliche Feiertage) in das Planun… |
| [[Server jobs]] | 686 | 1 | Hintergrund-Jobs für die Generierung: |
| [[Server konten und anmeldung]] | 2427 | 7 | Alles rund um Konten und Anmeldewege: |
| [[Server letters und pdf]] | 1384 | 3 | Zugangsbriefe: |
| [[Server licensing]] | 334 | 1 | Lizenz der Schule: |
| [[Server mailbridge]] | 519 | 1 | E-Mail-Brücke des Postfachs: |
| [[Server makeups]] | 510 | 1 |  |
| [[Server middleware und metrics]] | 322 | 3 | ASGI-Middleware (CoreMiddleware: |
| [[Server notify]] | 499 | 1 | Benachrichtigungen bei Änderungen im Vertretungsplan: |
| [[Server permissions]] | 556 | 1 | Rollen- und Rechtekatalog als Code: |
| [[Server rights]] | 182 | 1 | Rollen & Rechte pro Schule in der Datenbank: |
| [[Server runtime]] | 136 | 1 | Start und Stopp der Laufzeit: |
| [[Server store]] | 261 | 1 | SchoolStore: |

## Routen (`schulmanager/server/routes/*.py`)

436 Endpunkte in 46 Dateien – Übersicht und Gruppierung: [[Routen Übersicht]]

## Eigenständig

- [[Lizenzserver]] – Lizenzausstellung und -bestätigung des Herstellers

## Querschnitt

- [[Datenmodell]] · [[Migrationen]] · [[Rollen und Rechte]] · [[Abläufe]] · [[Betrieb und Deploy]] · [[Abhängigkeiten]] · [[Stand und Warnungen]]

<!-- eigene Notizen -->
