---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/"
stand: 2026-10-12 22:48
generator: schulmanager-regen
---

# Routen Übersicht

> Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

Jede Datei unter `routes/` mit einem Objekt `router` wird von [[Server app]] automatisch unter `/api/v1` eingebunden (`public_router` ohne Präfix, z. B. der iCal-Feed). Kernrouter laden zuerst (`auth`, `users`, `history`, `admin`, `me`, `events`, `system`, `oidc`). Rechte werden mit `Depends(require("recht"))` geprüft; **den Datenumfang** (eigene Klassen, eigene Kinder …) prüft jeder Router selbst über die Hilfen in [[Routen features_common]] – fremde Daten ergeben 404. Schreibende Fach-Router ändern das Planungsdokument ausschließlich über `features_common.mutate` ([[Server store]]).

## Anmeldung, Konten, System

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen auth]] | 11 | 449 | Anmeldung: Login (mit TOTP), Logout, Kontowechsel (mehrere Konten pro Browser über das Cookie sm_sessions), Passwortwechsel, Zwei-Faktor, ö… |
| [[Routen users]] | 20 | 634 | Benutzerverwaltung: Konten, Massenanlage, Eltern-Kind-Verknüpfung, Sitzungen, API-Tokens, Startpasswörter und Demo-Zugänge. |
| [[Routen me]] | 4 | 127 | Eigenes Konto: DSGVO-Datenexport, persönlicher iCal-Link. |
| [[Routen oidc]] | 2 | 74 | Single Sign-on über das Schulkonto (OpenID Connect) – alte Pfade /auth/oidc/. |
| [[Routen events]] | 1 | 38 | Server-Sent Events: GET /api/v1/events (Anmeldung nötig). |
| [[Routen system]] | 2 | 33 | Allgemeine Informationen: Rollen-/Rechtematrix, Version. |
| [[Routen admin]] | 7 | 118 | Systemverwaltung (nur system.admin): Systeminfo, Sicherungen, Demo-Schule, Wartung. |
| [[Routen history]] | 5 | 80 | Verlauf des Planungsdokuments (Versionen, Wiederherstellen, Rückgängig) und Audit-Protokoll. |
| [[Routen license]] | 3 | 53 | Lizenz der Schule (licensing): Stand anzeigen, Lizenz einspielen, jetzt online bestätigen. |
| [[Routen setup]] | 1 | 41 | Einrichtungs-Assistent einer neuen Schule: GET /setup/status liefert den Stand je Schritt (Lizenz, Schuldaten, |
| [[Routen rights]] | 10 | 219 | Rollen & Rechte: Katalog, wirksame Matrix, Änderungen je Rolle, Schulzweige und Zuordnungen. |
| [[Routen files]] | 6 | 98 | Dateien: verschlüsselter Upload/Download (Basisdienst, ARCHITECTURE.md §9.2). |

## Stammdaten, Planung, Stundenplan

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen features_data]] | 8 | 1051 | Stammdaten: generisches CRUD über models.COLLECTIONS und Einstellungen. |
| [[Routen features_planning]] | 15 | 300 | Planung: Kurse aus Stundentafeln, Lehrerzuweisung, Qualitätsbericht, |
| [[Routen features_timetable]] | 6 | 209 | Stundenplan-Ansichten, Verschieben (Drag & Drop) und Fixieren von Stunden. |
| [[Routen features_calendar]] | 2 | 308 | Schuljahr und Wochen (Entwurf KALENDER-ZEITRASTER §15.3, R3). |
| [[Routen features_classes]] | 9 | 1130 | Klassen-Seite (ARCHITECTURE.md §10.2): Suche, Personen, Klassenraum/Klassenleitung, Wochenplan und |
| [[Routen features_exchange]] | 11 | 449 | Import/Export (Untis GPU, Schulmanager-Online-Paket, CSV, JSON), iCal-Feed und |
| [[Routen features_holiday_import]] | 6 | 102 | Ferien/Feiertage aus öffentlicher API übernehmen (server/holiday_import.py). |

## Vertretung, Klausuren, Mitteilungen

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen features_substitutions]] | 17 | 671 | Vertretungsplan, Abwesenheiten, manuelle Entscheidungen (Overrides), |
| [[Routen features_exams]] | 5 | 285 | Klassenarbeiten/Klausuren. |
| [[Routen features_announcements]] | 4 | 259 | Mitteilungen (Tabelle announcements). |
| [[Routen features_grades]] | 3 | 219 | Noten: Klausuren/Tests (exam_results) und bewertete Hausaufgaben der Kursräume. |

## Schüler, Klassenbuch, Lehrkräfte

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen features_register]] | 5 | 456 | Klassenbuch: Anwesenheit je Unterrichtsstunde, Thema und Hausaufgabe. |
| [[Routen features_student_absences]] | 13 | 1174 | Krankmeldungen von Schüler/innen (Tabelle student_absences, A-58/B-06). |
| [[Routen features_student_self]] | 6 | 566 | Schüler-Selbstbedienung, Atteste & Dokumente (ARCHITECTURE.md §9.6). |
| [[Routen features_support]] | 11 | 549 | Förderinformationen je Schüler/in: Nachteilsausgleich, Schulbegleitung, Förderplan, Merkmale (mit Nachweisen). |
| [[Routen features_parent_access]] | 3 | 162 | Elternzugriff (A-44): volljährige Schüler/innen legen je Bereich fest, was ihre Eltern sehen dürfen. |
| [[Routen features_teacher_profile]] | 10 | 524 | Lehrer-Selbstverwaltung (ARCHITECTURE.md §9.3). |

## Kommunikation und Kursräume

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen features_channels]] | 37 | 3458 | Kursräume (ARCHITECTURE.md §9.4) – Kanäle je Kursteil und Klasse mit Ordnern, Material, Freigabe zur |
| [[Routen features_messages]] | 31 | 1993 | Internes Postfach (ARCHITECTURE.md §9.5, Agent Postfach) – verschlüsselte Nachrichten für alle Konten. |
| [[Routen features_chats]] | 35 | 1320 | Chats: Einzelchats, selbst erstellte Gruppen, Klassenchats (mit/ohne Lehrkräfte, Elternchats) – Ende-zu-Ende |
| [[Routen features_mail]] | 8 | 460 | Verbundene E-Mail-Konten im Postfach (Konten verwalten, Google/Microsoft-Anmeldung, Abruf, Versand an Externe). |

## Anmeldewege und Zugangsdaten

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen features_contact]] | 16 | 971 | Kontakt & Wiederherstellung (Erweiterung 4, §11.2): E-Mail/Handy bestätigen, „Passwort vergessen“, |
| [[Routen features_sso]] | 17 | 933 | Anmeldedienste: mit Microsoft, Apple, Google oder dem Schulkonto anmelden und Konten verbinden (§11.4). |
| [[Routen features_login_policy]] | 7 | 442 | Anmelde-Richtlinien verwalten (ARCHITECTURE.md §11.5) – Recht login_policy.manage (admin, schulleitung). |
| [[Routen features_letters]] | 9 | 385 | Zugangsbriefe (§11.3): Stapel mit Startpasswörtern als PDF/ZIP herunterladen oder per E-Mail versenden. |

## Hilfsmodul ohne Endpunkte

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen features_common]] | 0 | 749 | Gemeinsame Hilfsfunktionen der Fach-Router ohne eigene Endpunkte: snapshot(), mutate(), cached/day_plan, Rechte-/Umfangshilfen (reads_all_p… |

## Weitere Routen-Dateien (neu, noch nicht eingeordnet)

| Notiz | Endpunkte | Zeilen | Aufgabe |
|---|---|---|---|
| [[Routen api_discovery]] | 7 | 255 | Auffindbarkeit für KIs und Apps: `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/.well-known/…` und die |
| [[Routen api_open]] | 11 | 275 | Öffentliche, versionierte API für Apps und KI-Werkzeuge: `/api/v1/open/…` (docs/API-ZUGAENGE.md). |
| [[Routen features_absence_log]] | 2 | 103 | Meldungsprotokoll der Fehlzeiten lesen (Schreiben: ``). |
| [[Routen features_absence_stats]] | 2 | 376 | Fehlzeiten-Statistik einer Schülerin/eines Schülers (Anzahl und Prozent der Unterrichtsstunden, je Fach, je Tag/Stunde). |
| [[Routen features_api_access]] | 6 | 242 | API-Zugänge verwalten: ausgeben, auflisten, Nutzung ansehen, widerrufen (docs/API-ZUGAENGE.md). |
| [[Routen features_class_info]] | 4 | 216 | Klassenraum, Bereich „Klasse“ (Startansicht): Regelplan, Termine/Elternabende, Ansprechpersonen. |
| [[Routen features_forms]] | 27 | 1353 | Formular-Baukasten: Vorlagen, Ausfüllen, Genehmigung, PDF, Export (Doku: docs/FORMULARE.md). |
| [[Routen features_makeups]] | 7 | 376 | Nachschreibtermine (Klausur/Test verpasst): Liste, Termin festlegen, Attest-Verzicht, Erledigt. |

## Statistik

- Gesamt 436 Endpunkte (inkl. Infrastruktur- und Lizenzserver-Routen): DELETE 46, GET 208, PATCH 13, POST 138, PUT 31
- Meiste Endpunkte: [[Routen features_channels]] (37), [[Routen features_chats]] (35), [[Routen features_messages]] (31), [[Routen features_forms]] (27), [[Routen users]] (20)
- Weitere Routen außerhalb von `routes/`: `/healthz`, `/metrics`, SPA-Fallback `/{full_path:path}` in [[Server app]]; `GET /api/v1/health` und `POST /api/v1/check` im [[Lizenzserver]].
- Spalte „Frontend“ in den Routen-Notizen zeigt, welche Seite/welches Feature den Endpunkt aufruft ([[Frontend Übersicht]]).

<!-- eigene Notizen -->
