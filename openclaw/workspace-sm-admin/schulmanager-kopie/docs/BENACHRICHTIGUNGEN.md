# Benachrichtigungszentrale (Glocke)

Stand 13.10.2026 · Lücke #3 aus den internen Moodle-Vergleich · **ohne** Push, App oder Service Worker (die App-Option ist
ausdrücklich noch nicht Teil davon; B-41 bleibt offen).

## Was Nutzende sehen

- **Glocke in der Kopfleiste** (neben Farbschema und Kontomenü, am Handy ebenso) mit Zähler. Antippen öffnet die letzten
  zehn Benachrichtigungen; „Alle als gelesen“ und „Alle anzeigen und einstellen“.
- **Seite `/benachrichtigungen`** (Menü Konto): Liste nach Heute/Gestern/Diese Woche/Früher, Filter „Ungelesen“, einzeln
  gelesen/ungelesen/löschen, „Gelesene löschen“, Klick führt zum Ziel und markiert als gelesen. Reiter „Einstellungen“
  und – mit dem Recht `settings.edit` – „Schulvorgaben“.
- **Live**: über die bestehende SSE-Verbindung (`/api/v1/events`, Ereignis `change` mit Bereich `notifications`, nur an die
  Empfänger). Ist die Verbindung nicht offen, fragt die Glocke einmal pro Minute nach.
- **Abgrenzung zu „Nachrichten“**: Chats und Postfach behalten Zähler und Eintrag „Nachrichten“. Die Glocke zeigt
  Systemereignisse; die Art `message` ist standardmäßig **aus** und erscheint nur, wenn die Person sie einschaltet.
- **Eltern** bekommen die Meldungen **je Kind** (Hinweis „für <Kind>“). Bei volljährigen Kindern nur, wenn der Bereich über
  `parent_access` freigegeben ist (Stundenplan, Krankmeldungen, Kursräume, Noten, Dokumente).

## Ereignisquellen (angebunden)

| Art (`kind`) | Auslöser | Empfänger |
|---|---|---|
| `substitution` | Vertretung/Entfall/Verlegung/Raumänderung in `notify.check_changes` (`notification_hooks.plan_changes`) | betroffene Lehrkraft; Schüler/innen der Klasse bzw. des Kursteils; deren Eltern |
| `duty` | Aufsicht im Vertretungsplan geändert (dieselbe Prüfung) | betroffene Lehrkraft |
| `absence` | Krankmeldung eingegangen (`POST /student-absences`), bestätigt/nicht entschuldigt (`PATCH`) | Klassenleitung + Sekretariat (eingegangen); Familie (bestätigt, oder wenn die Schule erfasst) |
| `attest_missing` | Erinnerung (stündlicher Wartungslauf), einmal je Meldung | Familie |
| `request_decided` | Formular genehmigt/abgelehnt/erledigt; Antrag/Ausnahme einer Lehrkraft entschieden | einreichende Person (+ Familie) bzw. Lehrkraft |
| `course_item` | neue Aufgabe/neues Material, sofort sichtbar (`create_item`, `create_file_items`) | Schüler/innen des Kursraums + Eltern (nicht die Lehrenden) |
| `task_graded` | Abgabe bewertet oder zur Überarbeitung zurückgegeben | Schüler/in (+ Eltern, Bereich „Noten“) – ohne Note und Rückmeldung im Text |
| `task_due` | „Aufgabe ist morgen fällig“ (Wartungslauf), einmal je Aufgabe und Konto, nur ohne Abgabe | Schüler/innen + Eltern |
| `exam` | Klausur angesetzt/verschoben/abgesagt (nur bei Änderung von Datum oder Stunde) | Kursteilnehmende, Eltern, Lehrkräfte des Kurses |
| `plan_proposal` | Plan-Prüfung hat einen Vorschlag zur Entscheidung | Konten mit `timetable.generate`, `timetable.edit` oder `settings.edit` |
| `message` | – (keine Quelle angebunden; Art vorhanden, damit die Wahl „auch Nachrichten“ später greift) | – |

Bewusst nicht ausgelöst: zeitlich freigegebene Inhalte (Freigabe „ab Zeitpunkt/zur Stunde“) beim Freischalten; verborgene Inhalte.

## `notify` aufrufen (für alle Funktionen)

```python
from schulmanager.server import notifications

notifications.notify(
    user_ids,                       # Konten (int); inaktive und actor_id werden übersprungen
    "course_item",                  # Ereignisart, siehe notifications.KINDS
    "Neue Aufgabe im Kursraum",     # Titel: OHNE sensible Einzelheiten
    "/kursraeume/5",                # Ziel: relativer Pfad der Oberfläche (sonst leer)
    body="Mathe 8a: Steckbrief",    # optional, ebenfalls unkritisch
    student_id="S00012",            # optional: Kind, um das es geht (Eltern sehen „für <Kind>“)
    dedupe="item:41",               # optional: dieselbe Meldung je Konto nur einmal
    actor_id=user.id,               # optional: wer es ausgelöst hat (bekommt nichts)
    ref="channel:5",                # optional, freie Referenz
)
```

- Aufruf **nach dem Commit** der Fachänderung. Ohne `db=` läuft `notify` in einer eigenen Transaktion und löst danach den
  Live-Hinweis aus. Mit `db=session` wird nur die Zeile hinzugefügt (Commit und Live-Hinweis macht der Aufrufer).
- `notify` wirft nie; Fehler werden geloggt (Rückgabe: Liste der angelegten IDs, leer bei „aus“ oder Fehler).
- Hilfen für Empfänger: `users_of_teachers(db, teacher_ids)`, `users_of_students(db, student_ids)`,
  `parents_by_student(db, student_ids, area)`, `family_of(db, student_id, area)` (Schülerkonto + Eltern, volljährige nur mit
  Freigabe), `users_with_permission(db, *rechte)`.
- **Neue Art anmelden** (damit sie in den Einstellungen mit Beschriftung erscheint):
  `notifications.register_kind("poll", "Abstimmung oder Umfrage", "Kursräume", default="app", help="…")`.
  Unbekannte Arten funktionieren trotzdem (als „Sonstiges“, Standard „in der App“).
- Vorab angelegte Arten für andere Bereiche: `assignment` und `group` (M1), `progress` (M2), `poll` und `selftest` (M3),
  `gradebook` (M4), `competence` (M5). Titel/Text nie mit Noten, Gründen, Diagnosen oder Kommentaren füllen.

**Datenschutz**: Titel und Text werden verschlüsselt gespeichert (`title_enc`, `body_enc`, Schlüsselrotation
registriert); die Texte enthalten nach Konvention nichts Sensibles („Neue Krankmeldung“, nie Grund/Diagnose;
„Abgabe bewertet“, nie Note). Beispiele für zulässige Texte stehen in `notification_hooks.py`.

## Einstellungen

Je Ereignisart: **Aus** · **In der App** · **In der App und per E-Mail**. Wirksam wird, von oben nach unten:
gesperrte Schulvorgabe → eigene Wahl → Schulvorgabe → Voreinstellung der Art (meist „In der App“, `message` „Aus“).

- **E-Mail** nur, wenn der Versand eingerichtet ist (`auth_messages.email_available()`, also SMTP + Dispatcher) und das Konto
  eine Adresse hat; sonst bleibt es bei der App (die Option ist dann ausgegraut). Zustellung über die bestehende
  Mail-Warteschlange (`auth_messages.queue_email`, verschlüsselt, mit Wiederholung).
- **Tägliche Zusammenfassung**: statt einzelner Mails eine Mail pro Tag (frühestens 07:00 Ortszeit), nur ungelesene.
- **Ruhezeiten** (von/bis, auch über Mitternacht): in dieser Zeit keine E-Mails; sie gehen danach gesammelt raus. In der App
  erscheint alles sofort.
- **Schulvorgaben** (`settings.edit`): Standard je Art, **Pflicht** (gesperrt: gilt für alle, nicht änderbar) und
  **Aufbewahrung** in Tagen (7–730, Standard 90). Änderungen stehen im Audit (`notification_school.update`), eigene
  Einstellungen als `notification_settings.update` (ohne Inhalte).
- **Aufräumen**: der stündliche Wartungslauf (`maintenance.run_maintenance` → `notifications.run_periodic`) löscht
  Benachrichtigungen, die älter als die Aufbewahrung sind, und erledigt Erinnerungen und zurückgestellte E-Mails.

## API (`routes/features_notifications.py`)

Alle Routen nur für Angemeldete und **nur für die eigenen Daten** (fremde IDs: 404 bzw. wirkungslos).

| Route | Zweck |
|---|---|
| `GET /notifications?unread=&limit=&before=` | Liste + `unread` + `more` |
| `GET /notifications/count` | Zähler |
| `POST /notifications/read` | `{ids|null, read}` gelesen/ungelesen (ohne `ids`: alle) |
| `DELETE /notifications/{id}`, `DELETE /notifications?read=1` | löschen |
| `GET/PUT /notifications/settings` | eigene Einstellungen |
| `GET/PUT /notifications/school` | Schulvorgaben (`settings.edit`) |

Kein neues Recht: jedes Konto verwaltet seine Benachrichtigungen; die Schulvorgaben hängen an `settings.edit`.
Nicht Teil der offenen API (`/api/v1/open`): personenbezogen.

## Technik

- Tabellen (Migration `0041_notifications`): `notifications`, `notification_prefs`, `notification_user_settings`,
  `notification_school`, `notification_config`; Modelle `feature_models/notifications.py`.
- Code: `server/notifications.py` (Kern, `notify`), `server/notification_hooks.py` (Ereignisquellen),
  `server/notifications_demo.py` (Demo-Beispiele), Frontend `features/benachrichtigungen/` (Glocke in
  `components/Layout.tsx`, Seite, Logik, `logic.test.ts`).
- Anbindungen in bestehenden Dateien (je wenige Zeilen, nach dem Commit): `notify.check_changes`,
  `features_student_absences` (anlegen, Status), `features_forms.decide`, `features_teacher_profile._notify`,
  `features_exams` (anlegen/ändern/löschen), `features_channels` (neue Inhalte), `features_assignments.give_feedback`,
  `proposals.finish_package`, `maintenance.run_maintenance`, `demo_loader.load_demo`.
- Tests: `tests/test_notifications.py` (Kern, Rechte, Einstellungen, Eltern, E-Mail, Quellen),
  `tests/test_notifications_channels.py`, `tests/test_notifications_forms.py`; Frontend `logic.test.ts`.

## Offen

- Push/PWA/Service Worker (B-41) – ausdrücklich später.
- Quelle für `message` (Postfach/Chats → Glocke), falls gewünscht.
- Zeitlich freigegebene Kursraum-Inhalte melden beim Freischalten noch nichts.
- Aufsichts-Neuberechnung (`/duties/generate`) meldet nur über den Vertretungsplan-Vergleich.
