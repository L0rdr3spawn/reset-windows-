---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/ (25 Dateien)"
stand: 2026-10-12 22:38
generator: schulmanager-regen
---

# Server db

> Server-Kern · 25 Datei(en) · 2281 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Datenbankanbindung (SQLAlchemy 2): Engine für SQLite (WAL-Pragmas) oder PostgreSQL, Session pro Request (`get_db`), `session_scope` für Hintergrundcode. Enthält alle ORM-Modelle: Kerntabellen in `db_models.py`, Feature-Tabellen in `feature_models/*.py` (werden von `load_all` automatisch importiert), Alembic-Integration (`migrate.upgrade_head`) und `migrations/env.py`. Das Schema ändert sich ausschließlich über Revisionen, siehe [[Migrationen]] und [[Datenmodell]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/db.py` | 164 | Datenbankanbindung (SQLAlchemy 2). |
| `schulmanager/server/db_models.py` | 243 | Relationale Tabellen (SQLAlchemy 2, typisierte `Mapped`-Spalten). |
| `schulmanager/server/feature_models/__init__.py` | 19 | SQLAlchemy-Modelle der Feature-Module (Erweiterung 2). |
| `schulmanager/server/feature_models/absence_log.py` | 50 | Meldungsprotokoll der Fehlzeiten (Tabelle `student_absence_events`): unveränderlich, nur anhängen. |
| `schulmanager/server/feature_models/api_access.py` | 27 | Nutzungsprotokoll der API-Zugänge (`api_token_log`; docs/API-ZUGAENGE.md). |
| `schulmanager/server/feature_models/channels.py` | 256 | Kursräume (Agent Kursräume, ARCHITECTURE.md §9.4) – Kanäle, Ordner, Material, Aufgaben, Abgaben, Pi… |
| `schulmanager/server/feature_models/chats.py` | 212 | Chats (Einzel-, Gruppen- und Klassenchats) mit Ende-zu-Ende-Verschlüsselung. |
| `schulmanager/server/feature_models/contact.py` | 82 | Kontakt & Wiederherstellung (Erweiterung 4, §11.2): bestätigte E-Mail/Handynummer und Einmal-Codes. |
| `schulmanager/server/feature_models/files.py` | 71 | Tabelle `stored_files` – Metadaten verschlüsselt abgelegter Dateien (Agent Basis, ARCHITECTURE.md §… |
| `schulmanager/server/feature_models/forms.py` | 89 | Formular-Baukasten (Doku: docs/FORMULARE.md). |
| `schulmanager/server/feature_models/grades.py` | 45 | Noten zu Klausuren/Tests (`exam_results`). Note und Bemerkung verschlüsselt (AAD `exam_results.<fel… |
| `schulmanager/server/feature_models/identities.py` | 73 | Verbundene Anbieter-Konten und Anbieter-Einrichtung (Erweiterung 4, docs/ARCHITECTURE.md §11.4). |
| `schulmanager/server/feature_models/letters.py` | 57 | Zugangsbriefe (§11.3): kurzlebige Stapel mit Startpasswörtern (Tabelle `letter_batches`). |
| `schulmanager/server/feature_models/login_policy.py` | 98 | Anmelde-Richtlinien (Erweiterung 4, §11.5): wer darf sich wie anmelden (Tabelle `login_policy_rules… |
| `schulmanager/server/feature_models/mail.py` | 65 | Verbundene E-Mail-Konten (Google, Apple/iCloud, Microsoft/Outlook, GMX, Web.de, T-Online, Yahoo, ei… |
| `schulmanager/server/feature_models/makeups.py` | 59 | Nachschreibtermine: Wer eine Klausur/einen Test wegen Krankheit oder Fehlens verpasst hat, schreibt… |
| `schulmanager/server/feature_models/messages.py` | 212 | Internes Postfach (ARCHITECTURE.md §9.5, Agent Postfach): Tabellen für Unterhaltungen und Nachricht… |
| `schulmanager/server/feature_models/parent_access.py` | 45 | Elternzugriff volljähriger Schüler/innen (A-44) – Tabelle `parent_access` (Migration 0013_parent_ac… |
| `schulmanager/server/feature_models/register.py` | 54 | Klassenbuch: eine Zeile je gehaltener Unterrichtsstunde (Datum, Stunde, Kurs/Kursteil) mit Thema, H… |
| `schulmanager/server/feature_models/student_self.py` | 67 | Schüler-Selbstbedienung (Erweiterung 2, §9.6): eingereichte Dokumente/Atteste (Tabelle `student_doc… |
| `schulmanager/server/feature_models/support.py` | 90 | Förderinformationen je Schüler/in: Nachteilsausgleich, Schulbegleitung, Förderplan, Sonstiges – mit… |
| `schulmanager/server/feature_models/teacher.py` | 60 | Lehrer-Selbstverwaltung: Änderungsanträge von Lehrkräften (Tabelle `teacher_change_requests`). |
| `schulmanager/server/migrate.py` | 78 | Alembic-Integration: Migrationen programmatisch ausführen (Auto-Upgrade beim Start). |
| `schulmanager/server/migrations/__init__.py` | 2 | Alembic-Migrationen des Schulmanager-Servers. |
| `schulmanager/server/migrations/env.py` | 63 | Alembic-Umgebung des Schulmanagers. |

## Wichtige Funktionen und Klassen

- Klasse `Base` (`schulmanager/server/db.py:36`) – Deklarative Basis aller Tabellen (siehe `db_models`).
- Funktion `utcnow` (`schulmanager/server/db.py:47`) – Aktuelle Zeit als naive UTC-Datetime (Speicherformat aller Zeitstempel).
- Funktion `iso` (`schulmanager/server/db.py:52`) – Naive-UTC-Datetime → ISO-8601 mit `Z` (für JSON-Antworten).
- Funktion `normalize_url` (`schulmanager/server/db.py:61`) – `postgres://`/`postgresql://` → `postgresql+psycopg://` (psycopg 3).
- Funktion `build_engine` (`schulmanager/server/db.py:81`)
- Funktion `configure_engine` (`schulmanager/server/db.py:103`) – (Neu-)Erzeugt die Engine für `url` (Default: `config.database_url`) und bindet `SessionLocal`.
- Funktion `get_engine` (`schulmanager/server/db.py:114`) – Aktuelle Engine (wird bei Bedarf erzeugt).
- Funktion `dispose_engine` (`schulmanager/server/db.py:121`)
- Funktion `get_db` (`schulmanager/server/db.py:129`) – FastAPI-Dependency: eine Session pro Request (Commit durch den Handler).
- Funktion `session_scope` (`schulmanager/server/db.py:142`) – Kontextmanager für Hintergrundcode: committet bei Erfolg, Rollback bei Fehler.
- Funktion `check_db` (`schulmanager/server/db.py:155`) – `SELECT 1` – für `/healthz`.
- Funktion `db_kind` (`schulmanager/server/db.py:162`)
- Klasse `User` (`schulmanager/server/db_models.py:21`)
- Klasse `UserSession` (`schulmanager/server/db_models.py:46`) – Anmeldesitzung (Cookie `sm_session`). Gespeichert wird nur der Hash des Tokens.
- Klasse `ApiToken` (`schulmanager/server/db_models.py:61`) – API-Token (`Authorization: Bearer`), nur als Hash gespeichert.
- Klasse `LoginAttempt` (`schulmanager/server/db_models.py:83`)
- Klasse `ParentLink` (`schulmanager/server/db_models.py:93`) – Eltern-Konto ↔ Kind (`Student.id` im Planungsdokument).
- Klasse `RoleOverride` (`schulmanager/server/db_models.py:103`) – Schulspezifische Abweichung vom Standard der Rollenrechte (`permissions.effective_rights`).
- Klasse `Branch` (`schulmanager/server/db_models.py:118`) – Schulzweig/Abteilung: Klassen über Standort, Klassenstufe oder einzelne Klassen (Abteilungsleitung).
- Klasse `UserBranch` (`schulmanager/server/db_models.py:129`) – Zuordnung Konto (Abteilungsleitung) ↔ Zweig.
- Klasse `AuditLog` (`schulmanager/server/db_models.py:137`)
- Klasse `SchoolVersion` (`schulmanager/server/db_models.py:151`) – Version des Planungsdokuments (`School` als zlib-komprimiertes JSON).
- Klasse `Announcement` (`schulmanager/server/db_models.py:164`) – Mitteilung (Backend-Features).
- Klasse `StudentAbsence` (`schulmanager/server/db_models.py:185`) – Krankmeldung/Abwesenheit eines Schülers (Backend-Features).
- Klasse `NotificationOutbox` (`schulmanager/server/db_models.py:214`) – Ausgehende Benachrichtigungen (Webhook/E-Mail) mit Retry (Backend-Features).
- Funktion `load_all` (`schulmanager/server/feature_models/__init__.py:12`)
- Klasse `AbsenceEvent` (`schulmanager/server/feature_models/absence_log.py:23`)
- Klasse `ApiTokenLog` (`schulmanager/server/feature_models/api_access.py:16`)
- Klasse `EncryptedText` (`schulmanager/server/feature_models/channels.py:47`) – Mixin: verschlüsselte Textspalten `<feld>_enc` mit AAD `<tabelle>.<feld>:<id>`.
  - Methoden: `text_aad`:50, `read_text`:53, `write_text`:66
- Klasse `Channel` (`schulmanager/server/feature_models/channels.py:76`) – Kanal (Kursraum) eines Kursteils, einer Klasse oder frei angelegt.
  - Methoden: `setting`:92
- Klasse `ChannelExtraMember` (`schulmanager/server/feature_models/channels.py:96`) – Zusätzliches Mitglied eines Kanals (nur `channels.manage` ohne Einschränkung legt sie an).
- Klasse `ChannelFolder` (`schulmanager/server/feature_models/channels.py:109`) – Ordner (verschachtelt über `parent_id`).
  - Methoden: `effective_visibility`:131
- Klasse `ChannelItem` (`schulmanager/server/feature_models/channels.py:135`) – Material (Datei, Link, Textseite) oder Aufgabe.
- Klasse `AssignmentSubmission` (`schulmanager/server/feature_models/channels.py:170`) – Abgabe einer Schülerin/eines Schülers zu einer Aufgabe.
- Klasse `ChannelPost` (`schulmanager/server/feature_models/channels.py:192`) – Beitrag auf der Pinnwand (`parent_id` = Antwort auf einen Beitrag).
- Klasse `ChannelRead` (`schulmanager/server/feature_models/channels.py:211`) – Letzter Besuch eines Kontos in einem Kanal (Hervorhebung „neu“).
- Klasse `ChannelItemView` (`schulmanager/server/feature_models/channels.py:222`) – Material, das ein Konto schon geöffnet hat (Bereich „Unterricht“: Hinweis auf noch nicht angesehenes Material).
- Klasse `ChatDevice` (`schulmanager/server/feature_models/chats.py:23`) – Ein Browser/Gerät eines Kontos mit seinem öffentlichen Schlüssel (X25519, Base64).
- Klasse `ChatLinkRequest` (`schulmanager/server/feature_models/chats.py:40`) – Anfrage eines neuen Geräts, den Verlauf von einem eingerichteten Gerät desselben Kontos zu erhalten.
- Klasse `ChatKeyBackup` (`schulmanager/server/feature_models/chats.py:56`) – Optionales Wiederherstellungs-Backup: der private Archivschlüssel des Kontos, im Browser mit einem aus
- Klasse `Chat` (`schulmanager/server/feature_models/chats.py:68`)
  - Methoden: `title_aad`:86
- Klasse `ChatMember` (`schulmanager/server/feature_models/chats.py:90`)
- Klasse `ChatMessage` (`schulmanager/server/feature_models/chats.py:109`)
  - Methoden: `legacy_aad`:131
- Klasse `ChatMessageKey` (`schulmanager/server/feature_models/chats.py:135`) – Nachrichtenschlüssel, verpackt für ein Empfängergerät.
- Klasse `ChatReport` (`schulmanager/server/feature_models/chats.py:149`)
  - Methoden: `aad`:164
- … und 42 weitere öffentliche Definitionen (nur die wichtigsten sind aufgeführt)

## Datenbank-Tabellen

- **Definiert hier:** `account_initial_passwords` ([[Datenmodell#Konten und Anmeldung]]), `announcements` ([[Datenmodell#Planungsdokument und Protokoll]]), `api_token_log` ([[Datenmodell#Sonstige Tabellen]]), `api_tokens` ([[Datenmodell#Konten und Anmeldung]]), `assignment_submissions` ([[Datenmodell#Kursräume]]), `audit_log` ([[Datenmodell#Planungsdokument und Protokoll]]), `auth_codes` ([[Datenmodell#Konten und Anmeldung]]), `branches` ([[Datenmodell#Rollen und Rechte]]), `channel_extra_members` ([[Datenmodell#Kursräume]]), `channel_folders` ([[Datenmodell#Kursräume]]), `channel_item_views` ([[Datenmodell#Kursräume]]), `channel_items` ([[Datenmodell#Kursräume]]), `channel_posts` ([[Datenmodell#Kursräume]]), `channel_reads` ([[Datenmodell#Kursräume]]), `channels` ([[Datenmodell#Kursräume]]), `chat_attachments` ([[Datenmodell#Sonstige Tabellen]]), `chat_devices` ([[Datenmodell#Postfach und Chats]]), `chat_key_backups` ([[Datenmodell#Sonstige Tabellen]]), `chat_link_requests` ([[Datenmodell#Sonstige Tabellen]]), `chat_members` ([[Datenmodell#Postfach und Chats]]), `chat_message_keys` ([[Datenmodell#Postfach und Chats]]), `chat_messages` ([[Datenmodell#Postfach und Chats]]), `chat_report_images` ([[Datenmodell#Sonstige Tabellen]]), `chat_reports` ([[Datenmodell#Postfach und Chats]]), `chats` ([[Datenmodell#Postfach und Chats]]), `conversation_participants` ([[Datenmodell#Postfach und Chats]]), `conversations` ([[Datenmodell#Postfach und Chats]]), `exam_makeup_dates` ([[Datenmodell#Sonstige Tabellen]]), `exam_makeups` ([[Datenmodell#Sonstige Tabellen]]), `exam_results` ([[Datenmodell#Schüler, Klassenbuch und Noten]]), `form_events` ([[Datenmodell#Sonstige Tabellen]]), `form_submissions` ([[Datenmodell#Sonstige Tabellen]]), `form_templates` ([[Datenmodell#Sonstige Tabellen]]), `form_versions` ([[Datenmodell#Sonstige Tabellen]]), `letter_batches` ([[Datenmodell#Konten und Anmeldung]]), `login_attempts` ([[Datenmodell#Konten und Anmeldung]]), `login_policy_rules` ([[Datenmodell#Konten und Anmeldung]]), `mail_accounts` ([[Datenmodell#Postfach und Chats]]), `message_drafts` ([[Datenmodell#Postfach und Chats]]), `message_reports` ([[Datenmodell#Postfach und Chats]]), `message_user_settings` ([[Datenmodell#Postfach und Chats]]), `messages` ([[Datenmodell#Postfach und Chats]]), `notifications_outbox` ([[Datenmodell#Planungsdokument und Protokoll]]), `parent_access` ([[Datenmodell#Rollen und Rechte]]), `parent_links` ([[Datenmodell#Konten und Anmeldung]]), `register_lessons` ([[Datenmodell#Schüler, Klassenbuch und Noten]]), `role_overrides` ([[Datenmodell#Rollen und Rechte]]), `school_versions` ([[Datenmodell#Planungsdokument und Protokoll]]), `sessions` ([[Datenmodell#Konten und Anmeldung]]), `sso_providers` ([[Datenmodell#Konten und Anmeldung]]), `stored_files` ([[Datenmodell#Dateien]]), `student_absence_events` ([[Datenmodell#Sonstige Tabellen]]), `student_absences` ([[Datenmodell#Schüler, Klassenbuch und Noten]]), `student_documents` ([[Datenmodell#Schüler, Klassenbuch und Noten]]), `student_prefs` ([[Datenmodell#Sonstige Tabellen]]), `student_support` ([[Datenmodell#Schüler, Klassenbuch und Noten]]), `support_catalog` ([[Datenmodell#Sonstige Tabellen]]), `teacher_change_requests` ([[Datenmodell#Lehrkräfte]]), `user_blocks` ([[Datenmodell#Postfach und Chats]]), `user_branches` ([[Datenmodell#Rollen und Rechte]]), `user_contacts` ([[Datenmodell#Konten und Anmeldung]]), `user_identities` ([[Datenmodell#Konten und Anmeldung]]), `users` ([[Datenmodell#Konten und Anmeldung]])

## Hängt ab von

- [[Server config]] – `config`
- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*
- [[Server konten und anmeldung]] – `login_policy` *(nur zur Laufzeit importiert)*
- [[Server runtime]] – `runtime` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen admin]]
- [[Routen api_open]]
- [[Routen auth]]
- [[Routen events]]
- [[Routen features_absence_log]]
- [[Routen features_absence_stats]]
- [[Routen features_announcements]]
- [[Routen features_api_access]]
- [[Routen features_calendar]]
- [[Routen features_channels]]
- [[Routen features_chats]]
- [[Routen features_class_info]]
- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_contact]]
- [[Routen features_exams]]
- [[Routen features_exchange]]
- [[Routen features_forms]]
- [[Routen features_grades]]
- [[Routen features_letters]]
- [[Routen features_login_policy]]
- [[Routen features_mail]]
- [[Routen features_makeups]]
- [[Routen features_messages]]
- [[Routen features_parent_access]]
- [[Routen features_register]]
- [[Routen features_sso]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]
- [[Routen features_substitutions]]
- [[Routen features_support]]
- [[Routen features_teacher_profile]]
- [[Routen files]]
- [[Routen history]]
- [[Routen license]]
- [[Routen me]]
- [[Routen oidc]]
- [[Routen rights]]
- [[Routen setup]]
- [[Routen system]]
- [[Routen users]]
- [[Server absence_log]]
- [[Server api_scopes]]
- [[Server app]] – `app`
- [[Server audit]]
- [[Server betrieb]] – `backups`, `bootstrap`, `cli`, `demo_loader`, `maintenance`
- [[Server chat_migration]]
- [[Server crypto]]
- [[Server deps]]
- [[Server elternzugriff]] – `parent_access`
- [[Server files]]
- [[Server konten und anmeldung]] – `accounts`, `auth_messages`, `identities`, `login_policy`, `sso_providers`
- [[Server letters und pdf]] – `letters`
- [[Server licensing]]
- [[Server makeups]]
- [[Server notify]]
- [[Server rights]]
- [[Server runtime]]
- [[Server store]]

## Tests

`tests/test_absence_log.py`, `tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_channels_rooms.py`, `tests/test_chat_devices.py`, `tests/test_chat_split.py`, `tests/test_chats.py`, `tests/test_contact.py`, `tests/test_demo_public.py`, `tests/test_files_crypto.py` …

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
