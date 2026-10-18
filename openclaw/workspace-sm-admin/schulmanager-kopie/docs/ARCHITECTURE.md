# Schulmanager – Architektur & Schnittstellenvertrag

> **Geteiltes Gedächtnis aller Agenten.** Diese Datei ist der verbindliche Vertrag.
> Entscheidungen, Abweichungen und Fragen werden in `docs/AGENT_NOTES.md` protokolliert
> (anhängen, nie löschen). Wer eine Schnittstelle hier ändern muss, schreibt das
> zuerst in die Notes, damit die anderen Agenten es sehen.

## 1. Ziel

Full-Stack-Schulverwaltung mit Fokus Stundenplan & Vertretungsplan für eine Schule
mit ~2500 Schülern, ~200 Lehrkräften, 2 Standorten:

* Automatische Stundenplanerstellung aus Stundentafeln (Fächer + Wochenstunden je Jahrgang/Klasse),
  Kopplungen (Religion/Ethik, Oberstufenschienen), Doppelstunden, Fachräume.
* Wochen 1 … 52/53 je Schuljahr, Wochenangaben als jede Woche / ausgewählte Wochen / Rhythmus, 7-Tage-Woche (§12);
  Klassen, die nur teilweise da sind (z. B. jeden Mittwoch Praxistag; jede 2. Woche Mi weg) → `TimeRule`.
* Zwei Standorte mit Wegezeit (`settings.site_travel_periods`) für Lehrer **und** Klassen.
* Live-Vertretungsplanung bei Krankheit: **Ausfall nur am Rand des Schultags** (Priorität),
  Verlegung von Randstunden in Lücken, Vertretung durch passende Lehrkräfte, faire Verteilung.
* Konten serverseitig: Admin, Schulleitung, Stundenplaner, Sekretariat, Lehrer, Schüler, Eltern, Monitor.
* Zusammenarbeit mit anderen Schulmanager-Systemen (Untis GPU, Schulmanager Online, CSV, iCal, REST + Webhooks).

## 2. Verzeichnis-Layout & Besitzer (nur eigene Dateien bearbeiten!)

| Pfad | Besitzer | Inhalt |
|---|---|---|
| `schulmanager/models.py`, `scheduler.py`, `planning.py`, `demo.py`, `timetable.py` | **Lead** | Datenmodell, Generator, Demo-Schule, Stundenplan-Ansichten |
| `schulmanager/substitution.py`, `duties.py`, `exams.py`, `calendar_utils.py` | **Agent Vertretung** | Vertretungsplan-Engine, Pausenaufsichten, Klausuren, Ferien |
| `schulmanager/integrations/*` | **Agent Integrationen** | Untis GPU, Schulmanager Online, CSV, iCal, Webhook-Payloads |
| `schulmanager/server/` außer `server/routes/features_*.py`, `server/notify.py`, `server/jobs.py` | **Agent Backend-Core** | App, Config, DB, Migrationen, Auth, Konten, Rechte, Store/Versionierung, Audit, SSE, Admin |
| `schulmanager/server/routes/features_*.py`, `server/notify.py`, `server/jobs.py` | **Agent Backend-Features** | Fach-Endpunkte (Stammdaten, Planung, Stundenplan, Vertretung, Import/Export, Mitteilungen, Krankmeldungen) |
| `frontend/` | **Agent Frontend** | React + TypeScript + Vite SPA |
| `Dockerfile`, `docker-compose*.yml`, `deploy/`, `.github/`, `Makefile`, `scripts/`, `docs/BETRIEB.md`, `.dockerignore` | **Agent Infrastruktur** | Container, Reverse Proxy/HTTPS, Backups, CI, Betriebsdoku |
| `pyproject.toml` | Backend-Core (Abhängigkeiten); andere melden Bedarf in den Notes | |
| `tests/test_<bereich>*.py` | jeweiliger Agent | pytest |
| `README.md`, `docs/ARCHITECTURE.md` | **Lead** | |

Regeln für alle Agenten:
* **Kein** `git commit/push/checkout/reset` – der Lead committet.
* Fremde Dateien nicht ändern; Wünsche/Fehler in `docs/AGENT_NOTES.md` unter „Anfragen“ eintragen.
* Code-Bezeichner Englisch, UI-Texte & Doku Deutsch, Docstrings Deutsch (wie `models.py`).
* Python ≥ 3.11, Typannotationen, keine schweren Abhängigkeiten ohne Notiz.
* Tests: `python -m pytest -q` muss im Repo-Root grün laufen.

## 3. Kern (vorhanden, Lead)

* `schulmanager/models.py` – Dataclasses (`School`, `Settings`, `Site`, `Subject`, `Teacher`, `Room`,
  `SchoolClass`, `Student`, `Curriculum`, `CurriculumEntry`, `Course`, `CoursePart`, `Lesson`, `Absence`,
  `Override`, `Holiday`, `SupervisionArea`, `Duty`, `Exam`, `TimeRule`, `Weights`, `SubstitutionPolicy`).
  `School.to_dict()/from_dict()` verlustfrei. `COLLECTIONS` = Name → Klasse für generisches CRUD.
  **Alle Zeiten 0-basiert** (Tag 0 = Montag … 6 = Sonntag, Stunde 0 = 1. Stunde; **Wochen 1-basiert**: laufende Woche des Schuljahres).
* `weeks.real_week(school, date) -> int` laufende Woche (Grundlage aller Wochenangaben, nie Buchstaben, §12).
* Ein `Lesson` liegt bei (`day`, `start`, `length`) in den Wochen `weeks` bzw. im `rhythm` (beides leer = **alle** Wochen);
  `rooms[i]` gehört zu `course.parts[i]`.
* Kursteil-Referenz eines Schülers: `"<course_id>#<part_index>"` in `Student.courses`.
  Hat ein Schüler für einen Kurs mit mehreren Teilen keine Wahl → er gehört zu allen Teilen (Anzeige).
* `schulmanager/planning.py`: `build_courses_from_curricula(school) -> warnings`,
  `assign_teachers(school) -> warnings`, `capacity_warnings(school) -> warnings`.
* `schulmanager/scheduler.py`: `generate(school, time_limit=20.0, seed=1, keep_locked=True, progress=cb) -> ScheduleResult`; Mehrkern: `generate_best_of(school, time_limit, workers=0, ...)`
  mit `.lessons: list[Lesson]`, `.unplaced: list[dict]`, `.stats: dict`, `.warnings: list[str]`.
  `progress(msg: str, fraction: float)`. Laufzeit ≈ `time_limit` Sekunden (CPU-bound → im Thread/Prozess ausführen).
  Ändert `school` NICHT; Aufrufer setzt `school.lessons = result.lessons`.
* `schulmanager/demo.py`: `build_demo() -> School` (≈2600 Schüler, 98 Klassen, ~170 Lehrer, 2 Standorte,
  Rhythmus-Beispiele, Rhythmusklassen 9P/10P/10X/10Y, Oberstufe Q1/Q2 mit Schienen). Danach `assign_teachers` + `generate` nötig.
* `schulmanager/timetable.py` (Lead, entsteht parallel – Signaturen fix):
  * `lesson_info(school, lesson) -> dict` (siehe Zelle unten)
  * `timetable_view(school, kind: "class"|"teacher"|"room"|"student", ref: str, week: int = 0) -> dict`
    (`week` = laufende Woche, 0 = Woche 1; ohne Datum)
    → `{"kind","ref","title","week_no","days":[...],"periods":[...times],"cells":[Cell]}`
  * Cell = `{"lesson_id","course_id","day","start","length","weeks","subject","subject_name","color",
    "teachers":[...],"rooms":[...],"classes":[...],"label","locked","parts":[{"subject","teacher","room","label"}]}`
  * `student_parts(school, student_id) -> dict[course_id, list[int]]`
  * `check_move(school, lesson_id, day, start) -> list[str]` (leer = ok), `move_lesson(...)` (ValueError bei Konflikt)
  * `move_options(school, lesson_id) -> list[{"day","start","ok","conflicts"}]`
  * `validate_school(school) -> dict` (`stats`, `warnings`, `unplaced_hours`)

## 4. Vertretungs-Engine (Agent Vertretung)

`schulmanager/substitution.py`:

```python
def compute_day_plan(school: School, day: date, history: dict[str, int] | None = None) -> DayPlan
def compute_range(school: School, date_from: date, date_to: date) -> list[DayPlan]   # mit fairer Historie
def rank_candidates(school: School, day: date, lesson_id: str, period: int, part: int = 0) -> list[dict]
    # [{"teacher","name","score","reasons":[...],"qualified":bool,"free":bool}]
def effective_day(school: School, plan: DayPlan, kind: str, ref: str) -> list[dict]
    # kind wie timetable_view; Zellen des Tages inkl. Änderungen:
    # {"period","subject","teacher","room","classes","status","note","lesson_id","part","kind"}
def teacher_stats(school: School, date_from: date, date_to: date) -> list[dict]
    # [{"teacher","name","substitutions","cancelled_own","duties","supervisions"}]
```

`DayPlan.to_dict()`:
```json
{"date":"2026-10-06","weekday":1,"week_no":6,"holiday":null,"day_kind":"unterricht",
 "week_info":{"week_no":6,"iso_week":41,"week_text":"Woche 6 · KW 41"},
 "entries":[Entry], "warnings":["..."], "stats":{"vertretung":3,"entfall":5,...},
 "absent_teachers":["MUE"], "absent_classes":["7b","9P"],
 "absent_teacher_details":[{"teacher":"MUE","name":"Frau Müller","full_day":true,"periods":[],"cases":4}],
 "absent_class_details":[{"class":"7b","name":"7b","source":"absence","full_day":true,"periods":[],"reason":"Wandertag"},
                         {"class":"9P","name":"9P","source":"rhythm","full_day":true,"periods":[],"reason":"Praxistag"}]}
```
Details (B-04, A-56): je abwesender Lehrkraft eine Zeile ohne Grund (`periods` 0-basiert, leer bei ganztägig; `cases` =
vertretene/betreute/entfallene eigene Stunden und vertretene Aufsichten); je Klasse aus `absent_classes` eine Zeile je
Herkunft – `absence` (gemeldet, z. B. Wandertag) oder `rhythm` (regulärer Praxis-/Berufsschultag, wird nirgends als
abwesend angezeigt). `klasse_abwesend`-Einträge tragen dieselbe `source`. Öffentliche Sicht (Monitor, Druck) siehe §6/`filter_plan`:
Lehrkraft-Details nur laut `settings.public_absent_teachers` (`off` | `short` = Kürzel | `name`), Schüler/Eltern nie.
Entry:
```json
{"id":"2026-10-06:L12:2:0","date":"2026-10-06","period":2,"period_label":"3.","time":"09:50",
 "kind":"vertretung|betreuung|entfall|verlegung|raumaenderung|mitbetreuung|klasse_abwesend|aufsicht|klausur",
 "classes":["7a"],"subject":"M","teacher":"MUE","substitute":"SCH","room":"S1-R7a","new_room":null,
 "moved_from":null,"lesson_id":"L12","part":0,"note":"Entfall am Tagesende","warning":false,"manual":false,"site":"S1"}
```

Verbindliche Regeln (aus den Anforderungen):
1. Ferien/Feiertage (`school.holidays`) und Wochenende → keine Einträge, `holiday` gesetzt.
2. Laufende Woche über `weeks.real_week(school, day)`; nur Lessons mit passender Wochenangabe (Liste/Rhythmus) zählen.
3. Klassen-Sperrregeln (`TimeRule`) gelten auch im Vertretungsplan (Klasse ist dann nicht da).
4. **Ausfall nur an den Rändern**: Klassenstufe ≥ `policy.cancel_min_grade`: betroffene Randstunden entfallen
   (iterativ von außen nach innen); Lücken in der Mitte werden zuerst durch **Verlegung** einer Randstunde
   der Klasse in die Lücke geschlossen (`middle_strategy="shift_first"`), sonst Vertretung, sonst
   Entfall mit `warning: true`. Jüngere Klassen: immer Vertretung/Betreuung.
5. Kandidaten: frei, anwesend, nicht gesperrt, Wegezeit zwischen Standorten eingehalten, unter
   `max_subs_per_week` bzw. `policy.max_subs_per_day`. Bonus: fachlich qualifiziert, kennt die Klasse,
   Springstunde (ohnehin im Haus), durch Klassenfahrt/Entfall freigesetzt, gleicher Standort; Malus: Kollegium
   müsste extra kommen, viele Vertretungen in letzter Zeit.
6. Abwesende Klassen (Exkursion) → `klasse_abwesend`; deren Lehrer sind frei.
7. Raumsperre → `raumaenderung` mit Ersatzraum gleichen Typs/Standorts.
8. Overrides (`school.overrides`) haben Vorrang (`manual: true`).
9. Pausenaufsichten abwesender Lehrer → `kind:"aufsicht"` mit Ersatz (`duties.py`).
10. Klausuren am Tag → Eintrag `kind:"klausur"` (Info), Klausuren werden nie verlegt/entfallen ohne Warnung.

`duties.py`: `generate_duties(school) -> list[Duty]` (fair, bevorzugt Lehrer mit Unterricht direkt vor/nach
der Pause am Standort), `duty_replacements(school, day, plan_busy) -> list[Entry]`.
`exams.py`: `check_exam(school, exam) -> list[str]`, `exams_for(school, kind, ref, date_from, date_to) -> list[dict]`.
`calendar_utils.py`: `is_school_day(school, day) -> tuple[bool, str|None]`, `school_days(school, from, to)`.

## 5. Integrationen (Agent Integrationen)

* `integrations/untis_gpu.py`: `export_zip(school, plans: list[dict] | None = None) -> bytes`
  (GPU001 Stundenplan, GPU002 Unterricht, GPU003 Klassen, GPU004 Lehrer, GPU005 Räume, GPU006 Fächer,
  GPU014 Vertretungen, GPU010 Schüler) und `import_files(files: dict[str, bytes], school: School | None) -> tuple[School, list[str]]`.
* `integrations/schulmanager_online.py`: `export_package(school, plans) -> bytes` (ZIP mit Untis-Dateien +
  Schüler-/Lehrer-CSV + LIESMICH.txt mit Importanleitung). Keine öffentliche API → dateibasiert.
* `integrations/csv_io.py`: `export_csv(school, what) -> str` (`teachers|classes|rooms|subjects|students|lessons|curricula`),
  `import_csv(school, what, text, mapping: dict | None) -> dict` (Report), Trennzeichen `;`, UTF-8-BOM für Excel.
  Unterstützt typische Exporte aus SchILD-NRW/ASV (Spalten-Mapping).
* `integrations/ical.py`: `calendar(school, kind, ref, date_from, date_to, plans: dict[str, dict]) -> str`.
* `integrations/webhooks.py`: `payload(event, data) -> dict` + `sign(body, secret) -> str` (HMAC-SHA256, Header `X-Schulmanager-Signature`).

## 6. Server (Backend-Core + Backend-Features)

FastAPI, SQLAlchemy 2, Alembic, SQLite (Default) oder PostgreSQL (`SM_DATABASE_URL`).

### Konfiguration (Umgebungsvariablen)
`SM_ENV` (development|production), `SM_DATABASE_URL` (default `sqlite:///./data/schulmanager.db`),
`SM_SECRET_KEY`, `SM_BASE_URL`, `SM_COOKIE_SECURE` (1 in Produktion), `SM_ADMIN_USER`, `SM_ADMIN_PASSWORD`
(Erst-Admin beim ersten Start), `SM_LOAD_DEMO` (1 = Demo-Schule beim ersten Start inkl. Generierung),
`SM_SMTP_HOST/PORT/USER/PASSWORD/FROM`, `SM_FRONTEND_DIST` (default `frontend/dist`), `SM_LOG_LEVEL`,
`SM_GENERATE_TIME_LIMIT` (default 30), `SM_OIDC_*` (optional SSO).

### Datenhaltung
* **Planungsdaten** (`School`) als versioniertes Dokument: Tabelle `school_versions(id, created_at, user_id, message,
  scope, data zlib-JSON)`. In-Memory-Arbeitskopie im `SchoolStore`. Jede Änderung = neue Version → Verlauf & Undo.
* **Relationale Tabellen**: `users`, `sessions`, `api_tokens`, `login_attempts`, `parent_links`(parent_user_id, student_id),
  `audit_log`, `announcements`, `student_absences`, `notifications_outbox`.

### Interne Python-API (Backend-Core stellt bereit, Features nutzt)
```python
from schulmanager.server.config import config                # Config-Objekt
from schulmanager.server.db import get_db, SessionLocal, Base  # SQLAlchemy
from schulmanager.server.deps import AuthUser, current_user, optional_user, require
#   AuthUser: id, username, display_name, role, permissions: set[str], teacher_id, student_id,
#             student_ids (Eltern: Kinder; Schüler: [eigene]), site, must_change_password
#   require("timetable.edit") -> FastAPI-Dependency, liefert AuthUser oder 403
from schulmanager.server.store import get_store
#   store = get_store(); store.school (aktuelles School, NUR lesen); store.version
#   store.mutate(user, "Nachricht", fn, scope=["timetable"]) -> Rückgabewert von fn
#       fn bekommt eine Kopie, bei Exception keine Änderung; danach Persistenz, Audit, Event
from schulmanager.server.events import bus
#   bus.publish("change", {"version":..,"scope":[..],"dates":[..]}); SSE unter /api/v1/events
from schulmanager.server.audit import audit   # audit(db, user, action, target, details: dict)
```
Feature-Router: jede Datei `schulmanager/server/routes/features_<name>.py` exportiert `router = APIRouter()`;
Backend-Core bindet **automatisch** alle Module `routes/*.py` mit `router` unter `/api/v1` ein.

### Rollen & Rechte
| Recht | admin | schulleitung | abteilungsleitung | planer | sekretariat | lehrer | hausmeister | schulbegleitung | schueler | eltern | monitor | zuschauer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `plans.read_all` – Pläne lesen | ✔ | ✔ | ✔ (Eigener Zweig) | ✔ | ✔ | ✔ (eigene Klassen) |  |  |  |  |  | ✔ |
| `rooms.read` – Raumpläne lesen | ✔ | ✔ |  | ✔ | ✔ |  | ✔ |  |  |  |  | ✔ |
| `masterdata.read` – Stammdaten lesen | ✔ | ✔ |  | ✔ | ✔ |  |  |  |  |  |  | ✔ |
| `masterdata.edit` – Stammdaten bearbeiten | ✔ | ✔ |  | ✔ | ✔ |  |  |  |  |  |  | ✔ |
| `timetable.generate` – Stundenplan generieren | ✔ |  |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `timetable.edit` – Stundenplan bearbeiten | ✔ |  |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `substitution.read` – Vertretungsplan lesen | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  | ✔ |  |  |  | ✔ |
| `substitution.edit` – Vertretungen bearbeiten | ✔ | ✔ |  | ✔ | ✔ |  |  |  |  |  |  | ✔ |
| `substitution.self_study` – Eigenarbeit freigeben | ✔ | ✔ | ✔ (Eigener Zweig) | ✔ |  |  |  |  |  |  |  | ✔ |
| `duties.manage` – Aufsichten verwalten | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `absence.report_self` – Eigene Krankmeldung |  |  | ✔ |  |  | ✔ |  |  |  |  |  |  |
| `monitor.read` – Monitor-Ansicht | ✔ | ✔ |  | ✔ | ✔ |  | ✔ |  |  |  | ✔ | ✔ |
| `monitor.manage` – Monitore einstellen | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `students.read` – Schülerdaten lesen | ✔ | ✔ | ✔ (Eigener Zweig) | ✔ | ✔ | ✔ (eigene Klassen) |  |  |  |  |  | ✔ |
| `register.read_all` – Klassenbuch gesamt lesen | ✔ | ✔ | ✔ (Eigener Zweig) |  | ✔ |  |  |  |  |  |  | ✔ |
| `student_absence.report` – Schüler krankmelden |  |  | ✔ (Eigener Zweig) |  | ✔ | ✔ (Klassenleitung; sonst nur eigene Stunde) |  |  | (volljährig, eigene) | ✔ (eigene Kinder; Volljährige nur mit Freigabe) |  |  |
| `student_absence.read` – Krankmeldungen lesen |  | ✔ | ✔ (Eigener Zweig) |  | ✔ | ✔ (Klassenleitung; Fachlehrkraft nur „fehlt heute in meiner Stunde“ mit Schulschalter) |  |  | ✔ (eigene) | ✔ (eigene Kinder; Volljährige nur mit Freigabe) |  | ✔ |
| `student_documents.read` – Atteste & Dokumente |  | ✔ | ✔ (Eigene Klassenleitung) |  | ✔ | ✔ (nur Klassenleitung) |  |  | (volljährig, eigene) | ✔ (eigene Kinder, nicht Volljährige) |  | ✔ |
| `support.read` – Nachteilsausgleich & Förderung |  | ✔ | ✔ (Eigene Klassenleitung) |  | ✔ | ✔ (Eigene Klassenleitung) |  |  |  |  |  | ✔ |
| `support.manage` – Nachteilsausgleich pflegen |  | ✔ | ✔ (Eigene Klassenleitung) |  | ✔ | ✔ (Eigene Klassenleitung) |  |  |  |  |  | ✔ |
| `support.catalog` – Katalog der Merkmale | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `support.hints` – Ausgleichs-Hinweis bei Klausuren |  | ✔ | ✔ (Eigene Kurse) |  | ✔ | ✔ (Eigene Kurse) |  |  |  |  |  | ✔ |
| `exam.edit` – Klausuren bearbeiten | ✔ | ✔ | ✔ (Eigene Kurse) | ✔ |  | ✔ (eigene Kurse) |  |  |  |  |  | ✔ |
| `exam.types.manage` – Klausurarten verwalten | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `gradebook.use` – Notenbuch führen |  | ✔ | ✔ (Eigene Kurse) |  |  | ✔ (eigene Kurse) |  |  |  |  |  | ✔ |
| `gradebook.read_class` – Noten der Klasse lesen |  | ✔ | ✔ (Eigene Klassenleitung) |  |  | ✔ (Eigene Klassenleitung) |  |  |  |  |  | ✔ |
| `gradebook.manage` – Notenbuch verwalten |  | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `gradebook.export` – Noten exportieren |  | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `announcement.post` – Mitteilungen veröffentlichen | ✔ | ✔ | ✔ (Eigener Zweig) | ✔ | ✔ | ✔ (eigene Klassen) |  |  |  |  |  | ✔ |
| `messages.use` – Postfach nutzen | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  | ✔ | ✔ |  | ✔ |
| `messages.broadcast` – An Gruppen senden | ✔ | ✔ | ✔ (Eigener Zweig) | ✔ | ✔ | ✔ (eigene Klassen) |  |  |  |  |  | ✔ |
| `mail.custom_server` – Eigene Mailserver eintragen | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `messages.moderate` – Gemeldete Nachrichten prüfen | ✔ | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `chats.review` – Gemeldete Chat-Auszüge |  | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `channels.use` – Kursräume nutzen | ✔ | ✔ | ✔ |  |  | ✔ |  | ✔ | ✔ |  |  | ✔ |
| `channels.view_children` – Kursräume der Kinder lesen |  |  |  |  |  |  |  |  |  | ✔ (eigene Kinder; Volljährige nur mit Freigabe) |  |  |
| `channels.manage` – Kursräume verwalten | ✔ | ✔ | ✔ (Eigene Kurse) |  |  | ✔ (eigene Kurse) |  |  |  |  |  | ✔ |
| `channels.trash` – Kursraum-Papierkorb nutzen | ✔ | ✔ | ✔ (Eigene Kurse) |  |  | ✔ (eigene Kurse) |  |  |  |  |  | ✔ |
| `forms.submit` – Formulare ausfüllen |  | ✔ | ✔ |  | ✔ | ✔ |  |  | ✔ | ✔ |  |  |
| `forms.inbox` – Formular-Eingang |  | ✔ | ✔ (Eigene Klassenleitung) |  | ✔ | ✔ (Eigene Klassenleitung) |  |  |  |  |  | ✔ |
| `forms.manage` – Formulare gestalten | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `competency.read` – Lernstand lesen |  | ✔ | ✔ (Eigener Zweig) |  |  | ✔ (eigene Klassen) |  |  |  |  |  | ✔ |
| `competency.assess` – Lernstand eintragen |  | ✔ | ✔ (Eigener Zweig) |  |  | ✔ (eigene Klassen) |  |  |  |  |  | ✔ |
| `competency.manage` – Kompetenzrahmen & Abzeichen verwalten |  | ✔ | ✔ |  |  | ✔ |  |  |  |  |  | ✔ |
| `users.manage` – Konten verwalten | ✔ | ✔ (keine Admins) |  |  | ✔ (nur Schüler/Eltern) |  |  |  |  |  |  | ✔ |
| `passwords.reset` – Passwörter zurücksetzen | ✔ | ✔ | ✔ (Eigene Klassenleitung) |  | ✔ | ✔ (Schüler/innen der eigenen Klassenleitung) |  |  |  |  |  | ✔ |
| `students.birth_date` – Geburtsdatum pflegen | ✔ | ✔ | ✔ (Eigene Klassenleitung) |  | ✔ | ✔ (Eigene Klassenleitung) |  |  |  |  |  | ✔ |
| `profile.teacher_self` – Eigenes Lehrerprofil |  |  | ✔ |  |  | ✔ |  |  |  |  |  |  |
| `teacher_requests.review` – Profil-Anträge prüfen | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `settings.edit` – Einstellungen bearbeiten | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `rights.manage` – Rollen & Rechte verwalten | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |
| `login_policy.manage` – Anmelde-Richtlinien | ✔ | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `audit.read` – Protokoll lesen | ✔ | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `privacy.manage` – Löschkonzept verwalten | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |
| `privacy.subject` – Betroffenenrechte erfüllen (Auskunft, Sofort-Löschen) |  | ✔ |  |  |  |  |  |  |  |  |  |  |
| `history.restore` – Verlauf & Wiederherstellung | ✔ | ✔ |  | ✔ (nur Verlauf) |  |  |  |  |  |  |  | ✔ |
| `system.admin` – Systemverwaltung | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `license.manage` – Lizenz verwalten | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |
| `api.own` – Eigene API-Zugänge | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `api.manage` – API-Zugänge verwalten | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |

Quelle ist `schulmanager/server/permissions.py` (`ROLE_PERMISSIONS`, `PERMISSION_SCOPES`, `permissions_for`); die Tabelle
wird von `tests/test_server_core.py::test_architecture_matrix_matches_permissions` gegen den Code geprüft. Den Datenumfang
prüft jeder Router selbst (fremde Daten → 404); Krankmeldungen entscheidet `server/absence_access.py` (Stufen `full`/
`family`/`teacher`, Schulschalter `subject_teacher_absence_view`; Schüler/innen, die nach Geburtsdatum volljährig sind,
melden sich dort selbst krank, auch ohne `users.adult`), Elternsicht volljähriger Kinder `parent_access`.
Schüler/Eltern sehen nur den eigenen Plan/die eigene Klasse; Lehrkräfte sehen keine Schülerdaten fremder Klassen.

### REST-Endpunkte (Präfix `/api/v1`, JSON, Fehler: `{"detail": "..."}`)
**Core**
* `POST /auth/login` `{username,password,totp?}` → Cookie `sm_session` (HttpOnly, SameSite=Lax) + `{user, csrf_token}`;
  bei aktivem 2FA ohne `totp` → `401 {"detail":"totp_required"}`. Rate-Limit + Sperre nach Fehlversuchen.
* `POST /auth/logout`, `GET /auth/me` → `{user:{id,username,display_name,role,permissions,teacher_id,student_ids,must_change_password,totp_enabled}, csrf_token}`
* `POST /auth/password` `{old_password,new_password}`; `POST /auth/2fa/setup` → `{secret, otpauth_url}`; `POST /auth/2fa/enable` `{code}`; `POST /auth/2fa/disable` `{password}`
* Zustandsändernde Requests mit Cookie-Auth brauchen Header `X-CSRF-Token`. API-Tokens: `Authorization: Bearer <token>`.
* `GET/POST /users`, `GET/PATCH/DELETE /users/{id}`, `POST /users/{id}/reset-password` → `{temp_password}`,
  `POST /users/bulk` `{role:"schueler"|"lehrer"|"eltern", class_ids?:[]}` → `{created:[{username,display_name,temp_password,class}]}`
  (Zugangsbriefe), `POST /users/{id}/api-token` → `{token}` (nur eigenes Konto; per Token angemeldet: `expires_days`
  Pflicht, höchstens bis zum Ablauf des ausstellenden Tokens), `GET /users/{id}/sessions`, `DELETE /sessions/{id}`
* API-Zugänge mit Umfang (`docs/API-ZUGAENGE.md`): `GET /api-access/meta`, `POST /api-access/preview`, `GET/POST /api-access`,
  `GET/DELETE /api-access/{id}`; öffentliche API `GET /open/{timetable,substitutions,calendar,rooms,announcements,classes,
  teachers,sites}…` (Bearer `sma_…`, Bereiche+Filter), Struktur ohne Login: `GET /meta/scopes`, `GET /meta/openapi.json`,
  `/llms.txt`, `/llms-full.txt`, `/robots.txt`, `/.well-known/api-catalog` (ohne Präfix).
* `GET /history?limit=` → `[{version,created_at,user,message,scope}]`, `POST /history/{version}/restore`, `POST /history/undo`
* `GET /audit?limit=&user=&action=`
* `GET /events` (SSE): `event: change` `{version,scope,dates}`; `event: job` `{id,status,progress,message}`; `event: ping`
* `GET /admin/system`, `GET/POST /admin/backups`, `GET /admin/backups/{name}`, `POST /admin/demo`
* `GET /healthz`, `GET /metrics` (Prometheus, ohne Präfix)
* `GET /me/ical-url` → `{url}` (persönlicher Kalender-Feed mit geheimem Token: `GET /ical/{token}.ics`, Features)

**Features**
* `GET /data/{collection}`, `POST /data/{collection}`, `PUT /data/{collection}/{id}`, `DELETE /data/{collection}/{id}`
  (collection ∈ `COLLECTIONS` außer `lessons`, `absences`, `overrides`), `GET/PUT /settings`; Stundentafeln:
  Überschneidung → 409 `{"detail":{"message","conflicts":[...],"groups":[...]}}`, `?force=1` speichert trotzdem
* `POST /planning/courses-from-curricula` `{dry_run?, reset_manual?}` (Bericht mit `created/removed/changed/kept/
  conflicts/replan_needed`; `Course.pinned` = eigene Anpassungen bleiben), `GET /planning/curricula/overview`,
  `POST /planning/assign-teachers`, `GET /planning/report`,
  `POST /planning/generate` `{time_limit?,keep_locked?,seed?}` → `{job_id}`, `GET /planning/jobs/{id}`,
  `POST /planning/jobs/{id}/apply`, `POST /duties/generate`
* `GET /timetable/{kind}/{ref}?week=`, `GET /timetable/lessons/{id}/options`, `POST /timetable/lessons/{id}/move` `{day,start}`
  (409 `{"detail":{"conflicts":[...]}}`), `POST /timetable/lessons/{id}/lock` `{locked}`
* `GET /substitutions?date=&site=&class_id=&teacher=&public=` → DayPlan (nach Rolle gefiltert; `public=1` = öffentliche Sicht
  wie der Monitor im Datenumfang der Rolle, für Druck/Aushang), `GET /substitutions/range?from=&to=`,
  `GET /substitutions/candidates?date=&lesson_id=&period=&part=`, `GET /substitutions/stats?from=&to=`
* `GET/POST /absences`, `DELETE /absences/{id}` (Lehrkraft ohne `substitution.edit`: nur eigene **selbst gemeldete**
  (`self_reported`) mit Ende ≥ heute), `POST /absences/report-self` `{date_from,date_to,periods?,reason}`
* `GET/POST /overrides`, `DELETE /overrides/{id}`
* `GET /me/today?date=` → `{date, plan_entries:[...], cells:[effective_day], announcements:[...], exams:[...]}`, `GET /me/week?date=`
* `GET /monitor?site=&date=` (Monitor-Ansicht, Recht `monitor.read`)
* `GET/POST /exams`, `PUT/DELETE /exams/{id}`, `POST /exams/check`
* `GET/POST /announcements`, `DELETE /announcements/{id}`
* `GET/POST /student-absences`, `PATCH /student-absences/{id}` `{status, note}` (gemeldet|entschuldigt|unentschuldigt),
  `DELETE /student-absences/{id}` – Antwort mit `view` (`full|family|own|presence`); Status/Vermerk/Löschen nur
  Klassenleitung, Sekretariat, Schulleitung (meldende Person: löschen, solange „gemeldet“); Überschneidung →
  eigene „gemeldete“ Meldung zusammengeführt (200, `merged`) sonst 409; kein Schultag im Zeitraum → 422
* `GET /export/untis.zip`, `GET /export/schulmanager-online.zip`, `GET /export/csv/{what}`, `GET /export/json`,
  `POST /import/untis` (multipart), `POST /import/csv/{what}` (multipart + mapping), `POST /import/json`
* Benachrichtigungen (`server/notify.py`): bei Änderungen der Vertretungen für heute/morgen →
  Webhooks (`settings.webhooks`, signiert) + E-Mail an betroffene Lehrkräfte (wenn SMTP konfiguriert), Outbox mit Retry.

## 7. Frontend (Agent Frontend)

`frontend/` – Vite + React 18/19 + TypeScript + React Router. Keine UI-Riesenbibliothek nötig; eigenes, sauberes CSS
(hell/dunkel), responsive (Handy für Schüler/Eltern!). Build nach `frontend/dist` (wird von FastAPI ausgeliefert,
SPA-Fallback). Dev: `npm run dev` mit Proxy `/api` → `http://localhost:8000`.
Seiten: Login (2FA, Passwortwechsel-Zwang), Start/Dashboard je Rolle, Stundenplan (Klasse/Lehrer/Raum/Schüler, Wochenwahl,
Drag&Drop mit Konfliktanzeige, Fixieren), Vertretungsplan (Datum, Filter, Live-Update via SSE, Abwesenheit erfassen,
Kandidatenliste/Override), Planung (Stundentafeln, Kurse/Kopplungen, Generator mit Fortschritt, Qualitätsbericht,
Prioritäten/Gewichte), Stammdaten (Lehrer, Klassen inkl. Rhythmus-Regeln, Räume, Fächer, Standorte, Ferien), Klausuren,
Pausenaufsichten, Mitteilungen, Krankmeldungen, Benutzer (Massenanlage + druckbare Zugangsbriefe), Import/Export,
Verlauf/Audit, Profil (Passwort, 2FA, iCal-Link), Monitor-Vollbild (`/monitor/:site`, Autoscroll), Druckansichten.

## 8. Infrastruktur (Agent Infrastruktur)

Mehrstufiges `Dockerfile` (Node-Build → Python-Runtime, non-root, Healthcheck), `docker-compose.yml`
(app, postgres:16, caddy mit automatischem HTTPS, backup-Sidecar mit pg_dump + Rotation), `docker-compose.dev.yml`,
`deploy/Caddyfile`, `.env.example`, `scripts/backup.sh`, `scripts/restore.sh`, `.github/workflows/ci.yml`
(pytest, ruff, Frontend typecheck+build, Docker-Build), `Makefile`, `docs/BETRIEB.md` (Installation, Update, Backup/Restore,
Monitoring, DSGVO-Hinweise, Härtung). Start-Kommando der App: `uvicorn schulmanager.server.app:app --host 0.0.0.0 --port 8000`,
Migrationen: `alembic upgrade head` (oder automatisch beim Start).

## 9. Erweiterung 2 – Lehrer-Selbstverwaltung, Kursräume, Postfach, Schüler-Selbstbedienung, Verschlüsselung

### 9.0 Nutzeranforderungen (Original sinngemäß)
* Lehrkräfte haben je ein eigenes Konto, melden sich selbst krank und pflegen selbst: **welche Klassen sie hauptsächlich
  unterrichten, welche Fächer sie unterrichten können, wie viele Wochenstunden (Deputat), wann ihr Tag beginnt/endet**
  (z. B. erst ab 10:00, oder nur Abendunterricht ab 16:00). Der Stundenplan passt sich dynamisch an.
* Lehrkräfte bekommen **keinen Vollzugriff** mehr: nur ihre Fächer/Kurse und die zugehörigen Klassen/Gruppen.
* **Kursräume** (Klassen-/Kursgruppen = „Kanäle“) mit **Ordnern**, in denen Lehrkräfte Unterrichtsmaterial ablegen und
  **zu einzelnen Unterrichtsstunden** für die angemeldeten Schüler freigeben – Funktionsumfang wie Moodle
  (eigene Umsetzung, **kein Moodle-Code**: GPL-Lizenz wäre ansteckend).
* **Schülerübersicht** mit Stundenplänen; **Krankmeldung für den Tag** selbst, wenn von einer berechtigten Person als
  volljährig eingetragen (`users.adult`), sonst durch die **Eltern** über deren Konto; **Atteste und andere Dokumente einreichen**.
* **Internes Postfach für alle**: alle im System können allen schreiben; **verschlüsselt**.

### 9.1 Bereits vom Lead umgesetzt (verbindlich)
* `models.Teacher`: `preferred_classes: list[str]`, `time_windows: list[{"days":[0..], "start":"HH:MM", "end":"HH:MM", "weeks":[]}]`.
  Beim Übernehmen werden Zeitfenster in harte Sperrzeiten `Teacher.unavailable` umgerechnet (Notiz beginnt mit
  `"Zeitfenster"`; alte Zeitfenster-Regeln vorher entfernen). Damit gelten sie automatisch in Generator, Vertretung, Verschieben.
* `models.Settings`: `period_minutes=45`, `teacher_self_service="approval"|"direct"`, `sick_note_after_days=3`,
  `messaging_students_to_students=True`, `messaging_retention_days=365`.
* Neue Rechte (`server/permissions.py`, `frontend/src/api/types.ts`): `profile.teacher_self`, `teacher_requests.review`,
  `channels.use`, `channels.manage`, `messages.use`, `messages.broadcast`, `messages.moderate`, `student_documents.read`.
  Lehrkräfte: `plans.read_all` jetzt mit Scope **`own_classes`**, `channels.manage`→`own_courses`,
  `messages.broadcast`→`own_classes`, `student_documents.read`→`class_teacher` (nur Klassenleitung), **kein `monitor.read`**.
  Eltern `student_documents.read`→`own_children`; volljährige Schüler zusätzlich `student_documents.read`→`own`.

### 9.2 Basisdienste (Agent Basis) – alle anderen bauen darauf auf
* `schulmanager/server/crypto.py` – Umschlagverschlüsselung AES-256-GCM (`cryptography`):
  `encrypt(data: bytes, aad: bytes = b"") -> bytes`, `decrypt(token: bytes, aad: bytes = b"") -> bytes`,
  `encrypt_text(text: str, aad: str = "") -> str` (ASCII-Token), `decrypt_text(token: str, aad: str = "") -> str`,
  `rewrap(token) -> token` (Schlüsselrotation), `active_key_id() -> str`. Je Objekt eigener Datenschlüssel (DEK),
  DEK mit Master-Schlüssel gewrappt, Format versioniert (`SM1…`), zufällige 96-bit-Nonces.
  Schlüssel: `SM_ENCRYPTION_KEYS="kid1:<base64-32-Byte>,kid0:<…>"` (erster = aktiv); in Produktion Pflicht,
  in Entwicklung aus `SM_SECRET_KEY` per HKDF abgeleitet (mit Warnung). CLI `rotate-keys`, `gen-key`.
* `schulmanager/server/files.py` + Tabelle `stored_files` (id UUID-Str, owner_user_id, filename, content_type, size,
  sha256, purpose, ref_type, ref_id, created_at, deleted_at): Blobs **verschlüsselt** unter `data_dir/files/xx/yy/<id>`.
  API: `store_bytes(db, user, data, filename, content_type, purpose) -> StoredFile`, `read_file(db, file_id) -> (StoredFile, bytes)`,
  `attach(db, file_id, user, ref_type, ref_id)` (nur eigene, noch nicht angehängte Dateien), `detach/delete`,
  `register_access_check(ref_type, fn(db, user, stored_file) -> bool)`, `file_response(meta, data, inline=False)`
  (Content-Disposition mit `filename*`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: sandbox`, aktive Inhalte
  wie HTML/SVG nie inline). Limits: `SM_UPLOAD_MAX_MB` (25), `SM_QUOTA_MB_STAFF` (2000), `SM_QUOTA_MB_STUDENT` (200),
  Allowlist (PDF, Bilder, Office/OpenDocument, Text/CSV, Audio/Video gängig, ZIP), Magic-Byte-Prüfung, Dateinamen säubern.
  Optional Virenscan via ClamAV (`SM_CLAMAV_HOST/PORT`, INSTREAM). Nicht angehängte Uploads > 24 h löscht die Wartung.
  Endpunkte: `POST /files` (multipart `file`, `purpose`) → `{id, filename, size, content_type}`; `GET /files/{id}`
  (`?inline=1`) prüft Eigentümer **oder** registrierten Access-Check; `DELETE /files/{id}` (Eigentümer, nur unangehängt).
* **Feature-Tabellen**: jedes Feature legt SQLAlchemy-Modelle in `schulmanager/server/feature_models/<feature>.py` (gleiches `Base`)
  und eine Alembic-Revision `migrations/versions/<nr>_<feature>.py` an (`0003_teacher`: `down_revision = "0001_initial"`;
  `0004`–`0006`: `down_revision = "0002_files"`, da sie `stored_files` referenzieren dürfen). Mehrere Köpfe sind erlaubt:
  `migrate.py` nutzt bereits `upgrade heads`, und `feature_models/__init__.py::load_all()` wird von `db_models.py`
  automatisch aufgerufen (Lead, erledigt) – Feature-Modelle sind damit auch in Tests/`create_all`/Alembic bekannt.
  Revisionsnummern: `0002_files` (Basis), `0003_teacher` (Lehrer), `0004_channels`, `0005_messages`, `0006_student_self`.
  Der Integrations-Agent fügt am Ende eine Merge-Revision `0007_merge` hinzu.
* **Frontend-Registry**: Features liegen in `frontend/src/features/<feature>/` und exportieren aus `module.tsx`
  `export default { id, routes: [{ path, element, anyOf?: Permission[], notRoles?: Role[] }], nav: NavItem[],
  widgets?: [{ id, roles?: Role[], anyOf?: Permission[], element, order }] }`. `features/registry.ts` lädt alle Module per
  `import.meta.glob('./*/module.tsx', { eager: true })`; `App.tsx` (Routen + Guard), `lib/permissions.ts` (Menü/Zugriff) und
  `DashboardPage` (Widgets) lesen die Registry. Gemeinsame Bausteine von Basis: `src/api/files.ts` (upload/download/delete),
  `src/components/FileUpload.tsx` (Drag&Drop, Fortschritt, Mehrfach), `src/components/FileList.tsx`.
  **Feature-Agenten ändern KEINE geteilten Frontend-Dateien** (App.tsx, permissions.ts, types.ts, endpoints.ts, Layout) – nur ihr
  Feature-Verzeichnis; Bedarf an geteilten Änderungen → `docs/AGENT_NOTES.md` (Integrations-Agent erledigt das).
* Live-Ereignisse: `bus.publish("change", {...}, user_ids=[...])` für zielgerichtete Events (z. B. neue Nachricht, neues Material).

### 9.3 Lehrer-Selbstverwaltung & eingeschränkter Lehrerzugriff (Agent Lehrer)
* Tabelle `teacher_change_requests` (id, teacher_id, user_id, payload JSON {subjects, preferred_classes, max_hours,
  time_windows, wishes, note}, status `offen|genehmigt|abgelehnt`, reviewer_id, review_comment, created_at, decided_at).
* `GET/PUT /me/teacher-profile` (eigene Stammdaten lesen, Antrag stellen bzw. bei `direct` sofort übernehmen),
  `GET /teacher-requests?status=`, `POST /teacher-requests/{id}/approve|reject` (`teacher_requests.review`).
  Übernahme per `store.mutate` (Zeitfenster → Sperrzeiten). Antwort enthält **Konflikte**: Stunden, die nun außerhalb der
  Zeitfenster liegen, Deputat-Über-/Unterschreitung. `POST /planning/replan-teacher/{teacher_id}` startet einen Generator-Job,
  bei dem alle Stunden außer denen der Lehrkraft fixiert sind (dynamische Anpassung des Stundenplans).
* `planning.assign_teachers`: Bonus für `preferred_classes`, keine Zuweisung, wenn Zeitfenster für den Kurs nicht reichen.
* Zeitfenster → Stunden über `settings.period_times` + `period_minutes`; Abendunterricht braucht mehr Stunden im Raster
  (`settings.periods` bis 16 erlaubt). Demo: zusätzliche Abendstunden + Lehrkräfte „ab 10:00“ und „nur ab 16:00“ +
  eine Abendklasse.
* **Durchsetzung des Lehrer-Scopes** überall, wo `plans.read_all` geprüft wird (Backend **und** Frontend): Lehrkräfte sehen
  Stundenpläne nur für eigene Klassen, den eigenen Lehrerplan und Räume; Vertretungsplan nur Einträge eigener Klassen sowie
  eigene (vertreten/vertreten werden/Aufsicht); keine fremden Lehrerpläne, keine Schülerdaten fremder Klassen, kein Monitor.

### 9.4 Kursräume (Agent Kursräume) – Moodle-Funktionsumfang, eigene Umsetzung
* Tabellen: `channels` (id, kind `course|class|custom`, ref, title, description, settings JSON {students_can_post}, archived,
  created_at), `channel_extra_members` (channel_id, user_id, role), `channel_folders` (id, channel_id, parent_id, name, position,
  hidden), `channel_items` (id, channel_id, folder_id, type `file|link|text|assignment`, title, body, url, file_id,
  visibility `visible|hidden|scheduled|lesson`, visible_from, lesson_date, lesson_id, lesson_period, due_at, position,
  created_by, created_at, updated_at), `assignment_submissions` (id, item_id, student_user_id, text, file_ids JSON,
  submitted_at, status, feedback, grade, feedback_by, feedback_at), `channel_posts` (id, channel_id, parent_id, author_id,
  body, pinned, created_at).
* Kanäle werden automatisch für jeden Kurs (Mitglieder: Lehrkräfte der Kursteile; Schüler laut `timetable.student_parts`) und
  jede Klasse (Klassenleitung + alle Lehrkräfte der Klasse + Schüler) angelegt; Rolle im Kanal wird **dynamisch** aus dem
  Planungsdokument + Konten-Verknüpfung (`users.teacher_id/student_id`) bestimmt.
* **Freigabe zur Unterrichtsstunde**: Material an (Datum, Lesson, Stunde) binden → sichtbar ab Stundenbeginn
  (`period_times`); Endpunkt für „kommende Stunden dieses Kurses“ (aus Stundenplan inkl. laufender Woche, Ferien, Vertretung/Entfall).
* Aufgaben mit Abgabe (Text + Dateien), Fristen, Rückmeldung/Bewertung; Pinnwand mit Antworten; Live-Events an Mitglieder.
* Datei-Zugriff über `files.register_access_check("channel_item"|"submission"|"channel_post", …)`.
* Runde 1 (A-45–A-47, A-44): Ordner haben dieselbe Freigabe wie Material (`channel_folders.visibility`, `visible_from`,
  `lesson_*`, Migration `0013_parent_access`; `NULL` = alt, nur `hidden`); Eingabe zusätzlich `next_lesson`; entfällt die
  gebundene Stunde oder wird der Tag schulfrei, gilt die nächste stattfindende Stunde desselben Kurses. Ordner-Upload
  `POST /channels/{id}/folders/tree` (+ `…/items/files`). Klassenräume: fremdes Material/fremde Ordner ändern nur
  Ersteller/in, Klassenleitung und Kursraum-Verwaltung; Abgaben sieht nur, wer die Aufgabe gestellt hat. Eltern
  (`channels.view_children`, Scope `own_children`) lesen als Rolle `parent` die Kursräume ihrer Kinder (`?student_id=`).
* **Elternzugriff** (Baustein für alle Bereiche): Tabelle `parent_access` (student_id, area, allowed, set_by,
  updated_at), `server/parent_access.parent_may_see(db, student_id, bereich)` – minderjährig (Geburtsdatum, sonst
  `users.adult`) immer ja, volljährig nur mit Einwilligung; `GET/PUT /parent-access` (nur die volljährige Schüler/in,
  protokolliert). Bereiche `kursraeume` (angebunden), `krankmeldungen`, `dokumente`, `stundenplan`; einstellbar und im
  Profil sichtbar sind nur angebundene Bereiche (`ACTIVE_AREAS`), damit kein Schalter ohne Wirkung Schutz vortäuscht.

### 9.5 Postfach (Agent Postfach)
* Tabellen: `conversations` (id, subject_enc, kind `direct|group|broadcast`, allow_replies `all|sender|none`, created_by,
  created_at), `conversation_participants` (conversation_id, user_id, last_read_at, archived, deleted, muted),
  `messages` (id, conversation_id, sender_id, body_enc, attachment_ids JSON, created_at), `message_reports`
  (id, message_id, reporter_id, reason, status, handled_by, handled_at), `user_blocks` (user_id, blocked_user_id).
* Betreff und Text **verschlüsselt** (`crypto.encrypt_text`, AAD = Konversations-/Nachrichten-ID), Anhänge über `files`
  (verschlüsselt). Jeder darf jedem einzelnen Konto schreiben (Ausnahme: `settings.messaging_students_to_students=False`,
  Blockierungen); Gruppen (Klasse, Eltern einer Klasse, Kurs, Kollegium, Jahrgang, alle) nur mit `messages.broadcast`
  (Lehrkräfte nur eigene Klassen/Kurse). Adressbuch-Suche, ungelesen-Zähler, Live-Event `message` an Empfänger
  (ohne Inhalt), Melden/Blockieren, Moderation (`messages.moderate`), Aufbewahrungsfrist (Wartung löscht).
  Optional E-Mail-Hinweis „Neue Nachricht“ ohne Inhalt.

### 9.6 Schüler-Selbstbedienung, Krankmeldungen & Dokumente (Agent Schüler)
* „Meine Übersicht“ für Schüler (und Eltern je Kind): heute/morgen, Wochenplan, Vertretungen, Klausuren, eigene
  Krankmeldungen, offene Aufgaben (falls Kursräume-Modul vorhanden), ungelesene Nachrichten.
* **„Heute krank melden“** mit einem Klick (optional Stunden, Grund, mehrere Tage): volljährige Schüler (`users.adult`, nur von
  `users.manage`-Rollen setzbar – Schalter in der Benutzerverwaltung) für sich, Eltern für ihre Kinder; sonst gesperrt mit Hinweis.
* **Atteste/Dokumente**: Tabelle `student_documents` (id, student_id, absence_id NULL, category `attest|entschuldigung|
  einverstaendnis|sonstiges`, title, file_id, uploaded_by, status `eingegangen|geprueft|abgelehnt`, handled_by, handled_at,
  note, created_at). Upload verschlüsselt; Sicht: Einreichende, Eltern/volljähriger Schüler, Sekretariat, Schulleitung,
  Klassenleitung (Scope `class_teacher`) – **Fachlehrkräfte sehen Gesundheitsdokumente nicht**.
  Attestpflicht ab `settings.sick_note_after_days` → Markierung „Attest fehlt“.
* **Umgesetzt (Stand Integration):** reine Logik `schulmanager/student_self.py` (Attestpflicht: mindestens
  `sick_note_after_days` **Schultage**, fällig am N-ten Schultag; Zustände `nicht_noetig|erforderlich|fehlt|eingereicht|
  geprueft|abgelehnt`, „fehlt“ zählt auch bei nur abgelehnten Attesten), Modell `feature_models/student_self.py`, Migration
  `0006_student_self` (verschlüsselt zusätzlich vorhandene Klartext-Gründe/-Vermerke in `student_absences`), Routen
  `routes/features_student_self.py`: `GET /me/student-overview?student_id=`, `GET|POST /student-documents`,
  `PATCH|DELETE /student-documents/{id}`, `GET /student-documents/summary` (`{open, attest_missing, class_teacher_of?}`).
  `GET /student-absences` liefert je Eintrag `attest` und `reason_hidden` (Fachlehrkräfte sehen keinen Grund) und filtert mit
  `?attest_missing=1`. Datei-Zweck `student_document` (PDF/Bilder, 15 MB), Access-Check `student_document`.
  Volljährigkeit setzen nur `users.manage`-Rollen (`PATCH /users/{id}` `adult`). Eltern volljähriger Kinder sehen deren
  Dokumente nicht. Admin hat **kein** `student_documents.read`. Aufbewahrung: `SM_STUDENT_DOCS_RETENTION_DAYS` (400).
  Frontend-Modul `features/students` (ID `schueler`): `/meine-uebersicht` (Schüler/Eltern), `/dokumente` (Sekretariat,
  Schulleitung; Klassenleitungen über ihre Kachel), Kacheln „Krank melden“ und „Atteste & Dokumente“ bzw. „Meine Klasse“.
  Neue Krankmeldungen erreichen die Klassenleitung als zielgerichtetes Live-Ereignis (ohne Inhalt) → Kachel lädt neu;
  bewusst **keine** automatische Postfach-Nachricht (keine Kopie von Gesundheitsangaben in Nachrichten).

### 9.7 Integration (abgeschlossen)
* Migration `0007_merge` vereint `0003_teacher`, `0004_channels`, `0005_messages`, `0006_student_self` zu einem Kopf.
* Geteilte Dateien: `api/types.ts` (Settings-, Teacher-, Exam-Felder der Erweiterung, `AttestInfo`), `lib/csvFields.ts`
  (Wunschklassen/Zeitfenster), `components/Icon.tsx` + `NavIcon` (`mail`, `folder`), `ErrorBox` (403 mit Server-Begründung),
  Einstellungen „Krankmeldungen & Atteste“ (`sick_note_after_days`), Spalte „Attest“ und vertrauliche Gründe in
  *Krankmeldungen*. Demo: Klassenleitungen für alle Klassen (`planning.assign_class_teachers`, nur Lehrkräfte der Klasse),
  `schueler3` volljährig, `schueler4` im Kursteil von `lehrer1`.

## 10. Klassen-Seite (Erweiterung 3) – Vertrag

**Nutzerwunsch:** Klasse suchen → Schüler/innen, Klassenleitung, alle Fachlehrkräfte je Fach, Klassenraum sehen; Klassenraum
und Klassenleitung dort setzen (Admin/Schulleitung/Planung/Sekretariat); Wochenstundenplan der Klasse für eine konkrete
Kalenderwoche inkl. Vertretungen; angeben, dass etwas **nicht stattfindet** – das System stellt automatisch um.

### 10.1 Engine: neue Abwesenheitsart `lesson` („Unterricht findet nicht statt“)
* `Absence(kind="lesson", ref="<course_id>" | "<course_id>#<part>", date_from, date_to, periods=[…] (0-basiert, leer = alle
  Stunden des Kurses an dem Tag), reason)`. Bezieht sich auf den **Kurs** (nicht auf `lesson_id` – die ändert sich bei jeder
  Neugenerierung).
* `_Engine._classify`: betroffene Einheit wird `_AFFECTED` (mit Markierung `dropped`, Grund), die Lehrkraft ist **nicht**
  abwesend, sondern **frei** (`t_freed[...] = "Unterricht entfällt"`) und kann anderswo vertreten. Kein `manual`.
  Danach greift die bestehende Logik unverändert: ältere Klassen → Entfall am Rand bzw. Verlegung einer Randstunde in die
  Lücke (sonst Vertretung/Betreuung/Entfall mit Warnung); jüngere Klassen (`< cancel_min_grade`) und Klausuren → Betreuung.
  Die eigene Lehrkraft wird für die eigene Stunde nicht als Vertretung gewählt. Einträge tragen `"dropped": true`; Notizen
  nennen „Unterricht entfällt“ (+ Grund, sofern für die Rolle sichtbar). `teacher_stats` zählt `dropped` nicht als Abwesenheit
  der Lehrkraft. Override `keep` auf einer `dropped`-Einheit hebt die Freigabe wieder auf.
* Routen `/absences`: `kind` um `lesson` erweitern (Validierung: Kurs existiert, `#part` gültig), `ref_name` = Kursbezeichnung;
  Gründe wie bei Klassen-Abwesenheiten sichtbar. Kurs löschen → zugehörige `lesson`-Abwesenheiten entfernen.

### 10.2 Backend: `schulmanager/server/routes/features_classes.py` (Präfix `/api/v1`)
Sichtbarkeit wie Klassenpläne: `plan_class_ids(user)` / `check_view_access(user, "class", id)` (Lehrkräfte nur eigene Klassen);
Schüler/innen, Eltern, Monitor → 403.
* `GET /classes?q=&site=` → `{classes:[{id,name,grade,site,site_name,home_room:{id,name}|null,
  class_teacher:{id,name}|null,student_count,course_count,teacher_count}], can_edit, can_plan}` (sortiert natürlich nach Klasse).
* `GET /classes/{id}` → `{class:{id,name,grade,site,site_name,max_periods_per_day,unavailable:[TimeRule],
  home_room:{id,name,type,capacity,site}|null,class_teacher:{id,name}|null}, subjects:[{course_id,part,label,subject,
  subject_name,teacher:{id,name}|null,hours,classes:[…],coupled:bool}], teachers:[{id,name,is_class_teacher,subjects:[…],hours}],
  students:[{id,name,courses:[{course_id,part,label}]}]|null (nur mit students.read im Scope), student_count,
  room_choices:[{id,name,type,site,capacity,home_of:[class_ids]}] (nur can_edit), teacher_choices:[{id,name}] (nur can_edit),
  can_edit (masterdata.edit), can_plan (substitution.edit)}`.
* `PATCH /classes/{id}` (`masterdata.edit`) Body `{home_room?: str|null, class_teacher?: str|null, apply_to_timetable?: bool}`
  → `{class, warnings:[str], moved_lessons:int, skipped:[str]}`. Warnungen: Raum ist schon Klassenraum einer anderen Klasse,
  anderer Standort, Kapazität < Schülerzahl, Raumtyp kein Klassenraum, Klassenleitung unterrichtet die Klasse nicht.
  `apply_to_timetable`: in Stunden von Kursen nur dieser Klasse den alten Klassenraum durch den neuen ersetzen, wo der neue
  Raum zur selben Zeit (Tag/Stunde/Woche) frei ist; übrige als `skipped` melden. Ein `mutate`, Scope
  `["classes","timetable","substitutions"]`.
* `GET /classes/{id}/week?date=YYYY-MM-DD` → `{class_id, week_start, week_info, periods, period_times,
  days:[{date, weekday, holiday:str|null, cells:EffectiveCell[]}], absences:[{id,kind,ref,ref_name,date_from,date_to,periods,
  reason?,can_delete}], can_plan}`. `cells` wie `/me/today` (`effective_cells(day,"class",id)` + `_clean_cells`), Tagespläne über
  `day_plan` (faire Historie). `absences`: Klassen-Abwesenheiten dieser Klasse und `lesson`-Abwesenheiten ihrer Kurse in der
  Woche (Grund nur mit `substitution.edit`).
* `POST /classes/{id}/not-taking-place` (`substitution.edit`) Body `{mode:"lesson"|"class", date_from, date_to?,
  periods?:[int], course_id?:str, part?:int|null, reason:str, escort_teachers?:[str], dry_run:bool}`.
  `mode=lesson` → `Absence(kind="lesson", ref=course_id[#part])`; `mode=class` → `Absence(kind="class", ref=id)` plus je
  Begleitlehrkraft `Absence(kind="teacher", reason="Begleitung <Klasse>")` für dieselben Tage/Stunden.
  Antwort `{preview:[{date, changes:[{kind, classes, period, subject, teacher, substitute, room, note}]}], summary:str,
  absences?:[…]}`; `dry_run=true` speichert nichts (Vorschau = Unterschied der Tagespläne vorher/nachher, auch andere Klassen).
  Höchstens 14 Tage. Prüft, dass die Stunde/Klasse an dem Datum überhaupt Unterricht hat (sonst 422 mit Text).
* Zurücknehmen über das bestehende `DELETE /absences/{id}`.

### 10.3 Frontend: Feature-Modul `frontend/src/features/classes/` (ID `klassen`)
* Routen `/klassen` (Suche/Liste) und `/klassen/:id` (Detail); Menü „Klassen“, Gruppe `alltag`, `order: 15`, Icon `users`,
  `anyOf: ['plans.read_all','masterdata.edit','substitution.edit']`, `notRoles: ['schueler','eltern','monitor']`.
* Detail: Kopf (Name, Stufe, Standort, Klassenraum, Klassenleitung; mit `can_edit` direkt änderbar inkl. „auch im
  Stundenplan übernehmen“), Reiter **Wochenplan** (Wochennavigation mit KW/Datum/Woche, Raster Tage × Stunden mit Status
  Vertretung/Entfall/Verlegt/Raum/Klasse abwesend/Ferien – Bedeutung nie nur über Farbe; Handy: Liste je Tag), **Lehrkräfte**
  (Fach → Kurs/Kursteil → Lehrkraft, Klassenleitung markiert), **Schüler/innen** (mit Kurswahl).
* Im Wochenplan (mit `can_plan`): Stunde anklicken → „Findet nicht statt“ (Grund, ganzer Block/Kursteil) bzw. Knopf
  „Klasse ist nicht da“ (Datum/Zeitraum, Stunden, Begleitlehrkräfte) → **Vorschau** der automatischen Umstellung
  (`dry_run`) → „Übernehmen“; Liste der Ausfälle der Woche mit „Zurücknehmen“. Live-Aktualisierung über
  `live: ['substitutions','absences','overrides','timetable','classes','courses','holidays','exams']`.

### 10.4 Umsetzungsdetails (Stand Integration)
* Engine: `split_lesson_ref(ref) -> (course_id, part|None)`; betroffene Einträge tragen `"dropped": true`, Zellen aus
  `effective_day` immer `dropped: bool`. In die eigene Ausfall-Lücke wird keine andere Stunde **desselben Kurses** verlegt.
  `teacher_stats` zählt ausgefallenen Unterricht unter `freed`. Klassen-/Schüleransicht: Ist die eigene Klasse laut
  Abwesenheit nicht da, erscheinen auch gekoppelte Stunden, die für andere Klassen stattfinden, als „Klasse abwesend“.
* `/absences`: `ref` bis 80 Zeichen; `ref=<Kurs>` findet auch `<Kurs>#n`. Kurs löschen ohne `force` → 409, solange
  `lesson`-Abwesenheiten bestehen; mit `force` werden sie entfernt.
* `/classes/...`: `reason` und `dry_run` sind Pflichtfelder von `not-taking-place`; gleiche Abwesenheiten werden nicht doppelt
  angelegt; die Vorschau umfasst die Tage des Zeitraums. Begleitungen (`kind="teacher"`, Grund „Begleitung <Klasse>“)
  entfernt die Oberfläche beim Zurücknehmen der Klassen-Abwesenheit mit.

## 11. Konten & Anmeldung (Erweiterung 4) – Vertrag

### 11.0 Nutzeranforderungen (sinngemäß)
E-Mail und Handynummer mit dem Konto verbinden und darüber das Passwort zurücksetzen (auch der Admin darf das
anstoßen). Ganze Klassen anlegen; für jede neue Schülerin/jeden neuen Schüler Zugangsdaten erzeugen und **PDFs**, die
man einzeln verschicken kann; beim ersten Anmelden muss ein neues Passwort gesetzt werden. Microsoft-, Apple- oder
Google-Konto verbinden. Als Admin festlegen, dass sich z. B. Schüler/innen nur mit bestimmten Anbietern anmelden
dürfen bzw. sie verbinden **müssen** („bei uns bekommt jeder ein Apple- und ein Microsoft-Konto“) – je Person,
Klasse, Gruppe in der Klasse (nur Schüler/innen oder nur Eltern), Rolle; wer darf über alles anmelden, wer darf ein
Konto über den Anbieter anlegen. Alles muss in der Vorschau (Codespaces, ohne echte Anbieter/SMTP/SMS) testbar sein.

### 11.1 Gemeinsame Regeln
* Vier Agenten arbeiten **gleichzeitig im selben Checkout**. Jeder bearbeitet nur seine Dateien (unten); geteilte
  Dateien nur an der angegebenen Stelle und mit kleinen, abgegrenzten Änderungen (Edit, nie ganze Datei neu schreiben).
  Andere Agenten können gerade Dateien ändern: Tests/Lint, die in fremden Bereichen scheitern, nicht „reparieren“,
  sondern im Abschlussbericht nennen.
* Schnittstellen-Module (Platzhalter vom Lead, Signaturen stabil – nur der Besitzer ändert die Umsetzung):
  `server/login_policy.py` (Richtlinien), `server/identities.py` (Anbieter), `server/auth_messages.py` (E-Mail/SMS).
  Andere Agenten importieren sie **lazy** (innerhalb von Funktionen) und verlassen sich nur auf die Signaturen.
* Tabellen in `server/feature_models/<feature>.py`, je eine Alembic-Revision mit `down_revision = "0007_merge"`:
  `0008_contact`, `0009_letters`, `0010_identities`, `0011_login_policy` (mehrere Köpfe erlaubt; der Lead ergänzt
  `0012_merge`). Sensible Daten verschlüsselt (`crypto.encrypt_text`), Codes/Token nur als Hash.
* Jede schreibende Aktion → `audit(...)`. Fehlertexte für Nutzer auf Deutsch. Keine neuen Python-Abhängigkeiten außer
  `segno` (QR-Code, Agent Zugangsdaten). Frontend: nur vorhandene Icons (`components/Icon.tsx`), Feature-CSS mit Präfix.
* Tests je Agent in eigener Datei (`tests/test_<feature>.py`), vitest für reine Logik. Prüfen vor Abschluss:
  `ruff check .`, eigene Tests, dann komplette Suite (`python -m pytest -q -x`), `cd frontend && npm run lint && npx vitest run`.
* Abschluss: Unterabschnitt „Umsetzung“ in deinem §11.x ergänzen (Endpunkte, Felder, Entscheidungen) und Status in
  `docs/AGENT_NOTES.md` (`## [Kontakt] …`). Kein Commit/Push – das macht der Lead.

### 11.2 Agent Kontakt – E-Mail/Handy bestätigen, „Passwort vergessen“, Test-Postausgang
Besitz: `server/auth_messages.py` (Umsetzung), `server/sms.py`, `feature_models/contact.py`,
`migrations/versions/0008_contact.py`, `routes/features_contact.py`, `tests/test_contact.py`,
`frontend/src/features/konto/*` (Feature-ID `konto`).
Geteilt (nur diese Stellen): `notify.py` (`_deliver`: Arten `sms` und verschlüsselte `email` mit Anhängen; Klartext nach
Zustellung löschen), `config.py` (Block direkt nach den SMTP-Einstellungen), `maintenance.py` (abgelaufene Codes
löschen), `frontend/src/App.tsx` (öffentliche Routen neben `/login`), `pages/LoginPage.tsx` (Link „Passwort
vergessen?“ unter dem Anmeldeknopf + Erfolgsmeldung nach Zurücksetzen), `pages/ProfilePage.tsx` (Abschnitt
„Kontakt & Wiederherstellung“ direkt nach „Konto“), `pages/UsersPage.tsx` (Kontakt-Block im `UserModal` bestehender Konten).
* Kontakt: E-Mail bleibt `users.email`; neu Tabelle `user_contacts` (user_id PK, email_verified_at, phone_enc,
  phone_hash = HMAC der E.164-Nummer zum Suchen, phone_verified_at). Nummern normalisieren (deutsche Formate, `+49`).
  Ändern der eigenen Kontaktdaten verlangt das aktuelle Passwort (falls gesetzt); neue Adresse/Nummer erst nach Code gültig.
* Codes: Tabelle `auth_codes` (Zweck verify_email | verify_phone | reset, Kanal, Hash von Code und Link-Token, Ablauf
  15 min, Versuche max. 5, used_at, IP). Rate-Limit je Konto und IP.
* „Passwort vergessen“: `POST /auth/password-reset/request {identifier, channel}` (Benutzername, E-Mail oder Nummer)
  antwortet **immer gleich** (keine Konto-Erkennung); zugestellt nur an **bestätigte** Kontakte und nur, wenn
  `login_policy.effective_policy(...).reset_channels` den Kanal und `methods` `password` enthält. Bestätigen per
  Link-Token oder 6-stelligem Code → kurzlebiges Reset-Token → `POST /auth/password-reset/confirm` setzt neues Passwort
  (Passwortregeln), beendet alle Sitzungen, Audit. 2FA bleibt aktiv.
* Admin/Sekretariat (`users.manage` + `_check_manage`): Kontakt eines Kontos sehen/setzen, als bestätigt markieren,
  „Link zum Zurücksetzen senden“ (E-Mail/SMS). Das vorhandene Startpasswort-Zurücksetzen bleibt.
* SMS (`server/sms.py`): `SM_SMS_PROVIDER` = leer (aus) | `log` | `webhook` (`SM_SMS_URL`, optional `SM_SMS_TOKEN`) |
  `twilio` | `seven` (seven.io); Zustellung über die Outbox (Art `sms`).
* **Test-Postausgang** (`SM_DEV_OUTBOX`, Standard an in Entwicklung, in Produktion verboten → `ConfigError`): E-Mails/SMS
  werden statt zugestellt angezeigt – öffentliche Seite `/test-postausgang` (ohne Anmeldung, deutlicher Warnhinweis,
  letzte 50 Nachrichten inkl. Anhänge zum Herunterladen). `auth_messages.email_available()/sms_available()` sind dann wahr.

#### 11.2.1 Umsetzung (Agent Kontakt)
* **Outbox** (`auth_messages.py`): Arten `secure_email`/`sms`; Empfänger, Betreff, Text und Anhänge (base64) nur
  verschlüsselt im `payload` (AAD `notifications_outbox:<id>`), `target` maskiert (`m•••@schule.de`, `+49 171 •••••67`),
  `subject` = Zweck (`password_reset`, `verify_email`, `letters` …). `notify._deliver` → `auth_messages.deliver`
  (SMTP mit `EmailMessage.add_attachment`, SMS über `sms.send_sms`); nach `sent`/`failed` leert `dispatch_pending` den
  Payload; Fehlertexte ohne Empfänger im Klartext. `queue_email` wirft `ValueError` bei ungültiger Adresse oder > 20 MB
  Anhängen. Test-Postausgang: Status `test` (vom Dispatcher nie zugestellt, `deliver` verweigert zusätzlich), Wartung
  löscht nach 24 h. Schlüsselrotation: `notifications_outbox.payload`, `user_contacts.phone_enc`, `auth_codes.target_enc`.
* **SMS** (`sms.py`, nur urllib): `normalize_phone` (`0171 1234567`, `0171/123 45 67`, `+49 (0)171 …`, `+49 (171) …`,
  `0049 …` → `+491711234567`; andere Länder nur mit `+`/`00`; ohne Vorwahl → ungültig), `mask_phone`, `format_phone`,
  `phone_hash` (HMAC mit `SM_SECRET_KEY`). Anbieter `log` (in Produktion ohne Text), `webhook` (JSON `{to, text}`,
  Bearer), `twilio`, `seven` (Erfolg nur bei Code `100`); Zeitlimit `SM_SMS_TIMEOUT` (10 s), Fehler → `SmsError` (Retry).
* **Konfiguration** (Block nach SMTP): `SM_SMS_PROVIDER`, `SM_SMS_URL`, `SM_SMS_TOKEN`, `SM_SMS_ACCOUNT_SID`,
  `SM_SMS_FROM`, `SM_SMS_TIMEOUT`, `SM_DEV_OUTBOX`, `SM_AUTH_CODE_MINUTES` (15). `validate()`: Produktion +
  `SM_DEV_OUTBOX=1` → `ConfigError`; unvollständige Anbieter-Einstellungen → `ConfigError`. `public_dict`:
  `sms_enabled`, `sms_provider`, `dev_outbox`.
* **Tabellen** (`0008_contact`): `user_contacts` (siehe oben; `email_verified_value` = bestätigte Adresse klein →
  bestätigt ⇔ gleich `lower(users.email)`, `users.py` bleibt unverändert; Änderung per PATCH macht sie unbestätigt) und
  `auth_codes` (`purpose` `verify_email|verify_phone|reset|reset_token|rl_reset|rl_fail`; `rl_*` sind reine
  Rate-Limit-Zeilen ohne Code; `code_hash` = HMAC von Zweck+Konto+Code, `token_hash` eindeutig, `target_enc`,
  `ident_hash` = HMAC der Kennung). Neuer Code entwertet ältere offene desselben Zwecks. Wartung löscht Zeilen 1 h nach
  Ablauf.
* **Endpunkte** (`routes/features_contact.py`, Präfix `/api/v1`):
  `GET /me/contact` → `{email, email_verified, email_verified_at, phone (maskiert), phone_verified, phone_verified_at,
  has_password, password_login, reset_channels, channels{email,sms}, pending{email,phone}, code_minutes, dev_outbox}`;
  `POST /me/contact/email {email, password}` (Code + Link `/profil?kontakt=<token>` an die neue Adresse),
  `POST /me/contact/phone {phone, password}`, `POST /me/contact/verify {kind, code}`, `POST /me/contact/confirm-link
  {token}` (nur eigenes Konto), `POST /me/contact/{email|phone}/remove {password}` – Schreiben nur mit Sitzung (CSRF),
  Passwort mit derselben Sperre wie die Anmeldung, je Konto/Art 5 Codes/h, je IP 20/h. Hinweis-E-Mail an die bisher
  bestätigte Adresse bei Änderungen.
  Öffentlich: `GET /auth/password-reset/options`, `POST /auth/password-reset/request {identifier, channel}` (immer
  `{ok, message, code_minutes, dev_outbox}`, Mindestlaufzeit 0,35 s; Kennung = Benutzername, bestätigte E-Mail
  (höchstens 5 Konten) oder bestätigte Nummer; 5/h je Kennung, 20/h je IP → 429 auch für unbekannte Kennungen; je
  Konto höchstens 5 Codes/h über alle Kennungen, darüber still verworfen; nur zustellbare Adressen),
  `POST /auth/password-reset/verify {token}` bzw. `{identifier, code}` (gleiche Fehlermeldung, Fehlversuche zählen je
  Code und je IP 30/h; Versuch wird vor dem Vergleich atomar verbucht, Code/Link atomar verbraucht – auch beim
  Bestätigen eigener Kontakte) → `{reset_token, username, display_name, min_length, expires_at}`,
  `POST /auth/password-reset/confirm {reset_token, new_password}` (Passwortregeln; `must_change_password=False`; alle
  Sitzungen beendet; erfolgreicher `LoginAttempt` hebt eine Anmeldesperre auf; 2FA bleibt). Die Routen nutzen keine
  Sitzung → kein CSRF nötig, `password_change_required`/`link_required` greifen nicht.
  Verwaltung: `GET/PUT /users/{id}/contact` (`{email?, email_verified?, phone? (null = entfernen), phone_verified?}`;
  Antwort mit voller Nummer `phone`, `phone_display`, `can_send_reset{email,sms}`), `POST /users/{id}/send-reset
  {channel}` (nur an bestätigte Kontakte, nur wenn `password` erlaubt, 10/h je Konto; `reset_channels` gilt nur für die
  Selbstbedienung). Audit: `contact.*`, `user.contact_update`, `user.send_reset`, `auth.password_reset_request|verify`,
  `auth.password_reset` – ohne Nummern/Codes.
  Test-Postausgang: `GET /dev-outbox` → `{enabled, hours, items[{id, channel, to, subject, text, purpose, created_at,
  attachments[{index, filename, content_type, size}]}]}`, `GET /dev-outbox/{id}/attachments/{n}` (Download, `nosniff`,
  CSP `sandbox`); sonst 404.
* **Frontend** `features/konto/` (ohne `module.tsx`): `slots.tsx` (`ForgotPasswordLink`, `ContactSection`,
  `UserContactPanel` mit optionalem `onEmailChange`), `ForgotPasswordPage` (Kennung + Kanal → neutrale Bestätigung →
  Code → neues Passwort → `/login?reset=ok`; „Ich habe bereits einen Code“, `?code=1&kennung=` möglich),
  `ResetPasswordPage` (`?token=` prüft den Link einmal beim Laden, Reset-Token in `sessionStorage`), `DevOutboxPage`
  (Warnhinweis, alle 5 s aktualisiert, Kopierknopf für Codes, App-Links als interne Pfade, Anhänge), `ContactSection`,
  `UserContactPanel`, `components.tsx`, `logic.ts` (+ `logic.test.ts`, `forms.test.ts`), `konto.css` (Präfix `ko-`).
  Passwort-Manager: echte `<form>`s, `autocomplete` `username`/`new-password` (zweimal, mit schreibgeschütztem
  Benutzernamen im selben Formular)/`current-password` (mit verstecktem `username`)/`one-time-code`/`email`/`tel`; im
  Admin-Panel `autocomplete="off"`.

### 11.3 Agent Zugangsdaten – Klasse komplett anlegen, Zugangsbriefe als PDF
Besitz: `server/pdf.py` (eigener PDF-Schreiber, Helvetica/WinAnsi für Umlaute, QR-Code per `segno` → `pyproject.toml`),
`server/letters.py`, `feature_models/letters.py`, `migrations/versions/0009_letters.py`, `routes/features_letters.py`,
`tests/test_letters.py`, Frontend-Seite(n) in `frontend/src/features/zugangsdaten/*` (Feature-ID `zugangsdaten`).
Geteilt: `routes/features_classes.py` + `frontend/src/features/classes/*` (Klasse anlegen, Schüler hinzufügen,
Zugangsdaten neu erzeugen), `routes/users.py` (nur `reset_password` und `bulk`: zusätzlich `letter_batch` in der
Antwort), `pages/UsersPage.tsx` (PDF-Knöpfe neben „Zugangsbrief(e) drucken“), `maintenance.py` (abgelaufene Stapel löschen).
* Stapel: Tabelle `letter_batches` (id UUID, created_by, created_at, expires_at = +60 min (`SM_LETTER_BATCH_MINUTES`),
  title, data_enc = verschlüsseltes JSON der Einträge inkl. Startpasswort). Passwörter nie im Klartext gespeichert.
* PDFs: Einzel-PDF je Person, Sammel-PDF (eine Seite je Brief), ZIP mit Einzel-PDFs (`5a_Nachname_Vorname.pdf`).
  Brief: Schulname, Name, Klasse, Anmeldeadresse + QR-Code, Benutzername, Startpasswort, „Beim ersten Anmelden legst du
  ein eigenes Passwort fest“; Elternbrief-Variante. Hinweise aus `login_policy` (Passwort nicht erlaubt → „Melde dich
  mit … an“, Pflicht-Verknüpfungen → „Verbinde danach …“).
* Endpunkte: `POST /classes` (Klasse + Schülerliste + Optionen Schülerkonten/Elternkonten, `dry_run`),
  `POST /classes/{id}/students` (Schüler hinzufügen, Konten optional), `POST /letters/batches {user_ids}` (neue
  Startpasswörter für vorhandene Konten), `GET /letters/batches/{id}` (ohne Passwörter), `…/pdf`, `…/zip`,
  `…/entries/{user_id}.pdf`, `POST /letters/batches/{id}/send {user_ids?, to: student|parents|both}` (E-Mail mit
  PDF-Anhang über `auth_messages.queue_email`). Rechte `masterdata.edit` (Klasse) bzw. `users.manage` + `_check_manage`.
* Frontend: Klassen-Seite „Neue Klasse“ (Assistent: Klasse → Schülerliste einfügen aus Excel/Text mit Vorschau → Konten →
  Ergebnis mit PDF/ZIP/E-Mail), „Schüler hinzufügen“, Auswahl → „Neue Zugangsdaten“; Stapel-Seite `/zugangsdaten/:id`.

#### 11.3.1 Umsetzung (Agent Zugangsdaten)
* **PDF** (`server/pdf.py`, nur Standardbibliothek + `segno`): PDF 1.4, A4, Helvetica/Helvetica-Bold/Courier(-Bold) mit
  `WinAnsiEncoding` (cp1252; fremde Zeichen → Grundbuchstabe bzw. „?“), Breiten aus den Adobe-AFM-Tabellen (`text_width`,
  `wrap`, zentriert/rechtsbündig), Linien/Rechtecke, QR-Code als Form-XObject (einmal je Dokument), Flate-Ströme,
  korrekte `xref`. Brief (`letters._draw_letter`): Schulname (`settings.school_name`), Datum, Titel „Zugangsdaten für
  <Name> (Klasse 5a)“ bzw. „… für die Eltern von <Kind(er)>“, Kasten mit Anmeldeadresse (`SM_BASE_URL` + `/login`, Text
  und QR), Benutzername und Startpasswort (Courier), Schritte, Hinweise. Schüler/innen Du-Form, volljährige Schüler/innen,
  Eltern und Personal Sie-Form; benannte Eltern werden persönlich angesprochen.
* **Richtlinie** (`login_policy.effective_policy`, lazy): Passwort nicht erlaubt → kein Passwort, „Melde dich mit deinem
  Microsoft-Konto an“; **Ausnahme** (Entscheidung): sind zugleich Verknüpfungen Pflicht, wird das Startpasswort gedruckt
  („nur für die erste Anmeldung – danach nur noch mit …“), weil die Ersteinrichtung (§11.5) es zum Verbinden braucht.
  `required_links` → „Verbinde nach dem ersten Anmelden dein …-Konto“ (`identities.PROVIDER_LABELS`).
* **Tabellen** (`0009_letters`, `down_revision="0007_merge"`): `letter_batches` (id UUID, created_by → users CASCADE,
  created_at, expires_at = jetzt + `SM_LETTER_BATCH_MINUTES` (Standard 60, 1…1440, direkt aus der Umgebung), title,
  count, data_enc = `encrypt_text(JSON, aad="letter_batches:<id>")`) und `account_initial_passwords` (user_id PK → users
  CASCADE, password_enc mit AAD `account_initial_passwords:<user_id>`, created_at, created_by) – das zuletzt erzeugte
  Startpasswort jedes Kontos, das in einen Stapel kam (Anlegen, Massenanlage, Zurücksetzen, Klassen-Assistent).
  Beide für `cli rotate-keys` registriert. Abgelaufene Stapel: Wartung (`maintenance.py`) und jeder Zugriff (→ 410).
* **Endpunkte** (`routes/features_letters.py`, Antworten `Cache-Control: no-store`, Downloads/Versand/Zurücksetzen im
  Audit, nie mit Passwort):
  * `POST /letters/batches {user_ids?, student_ids?, parents?, create_missing?}` (`users.manage` + `_check_manage` je
    Konto) → neue Startpasswörter (Hash mit `TEMP_PASSWORD_N`, `must_change_password`, Sitzungen beendet); über
    `student_ids` die Schülerkonten, mit `parents` deren Elternkonten, mit `create_missing` fehlende Konten neu →
    `{id, count, expires_at, reset, created, title}`. Höchstens 500 Konten.
  * `GET /letters/batches/{id}` → `{id,title,count,created_at,expires_at,expires_in,created_by,login_url,
    email_available, entries:[{user_id,username,display_name,role,class_id,class_name,student_id,children,exists,
    adult,has_email,parents,parents_with_email,password_printed,login_methods,required_links,filename,title}]}`
    (volljährig: `parents`/`parents_with_email` = 0);
    `…/pdf` (Sammel-PDF, `?inline=1`), `…/zip` (`5a_Mustermann_Max.pdf`, Eltern `…_Eltern.pdf`, eindeutig),
    `…/entries/{user_id}.pdf`. Nur anlegende Person oder Rolle admin (sonst 404), abgelaufen 410; Einträge nur, soweit
    die Person sie (noch) verwalten darf.
  * `POST /letters/batches/{id}/send {user_ids?, to: student|parents|both}` → `{sent:[{user_id,display_name,role,
    recipients,failed}], no_address, unavailable, email_available}`; je Person eine E-Mail je Adresse mit ihrem PDF
    (`auth_messages.queue_email(..., purpose="letter")`, kein Passwort im Text). `student` = eigene Adresse
    (`users.email`), `parents` = Elternkonten über `ParentLink` (Elternbriefe: eigene Adresse), `both` = beides.
    Volljährige Schüler/innen (Stapel oder Konto `adult`) bekommen ihren Brief immer nur an die eigene Adresse.
  * `GET /users/{id}/password` → `{has_initial, initial_created_at, must_change_password}`;
    `POST /users/{id}/password {mode:"initial"|"set", password?, must_change=true}`: `initial` setzt den Hash wieder
    auf das gespeicherte Startpasswort (Passwortwechsel-Zwang, Sitzungen beendet, neuer Brief-Stapel →
    `letter_batch`), 409 ohne gespeichertes Startpasswort; `set` = selbst gewähltes Passwort (Passwortregeln,
    `must_change`). Eigenes Konto → 409 (Profil).
  * `GET /classes/{id}/accounts` → `{class_id, can_manage, students:[{student_id,name,birth_date,account:{user_id,
    username,display_name,role,active,must_change_password,last_login,has_email,has_initial,can_reset}|null,
    parents:[…] (nur users.manage)}]}`.
* **Neues Recht `passwords.reset`** (admin, schulleitung, sekretariat, lehrer mit Scope `class_teacher`):
  Lehrkräfte nur für Schülerkonten der Klassen, die sie leiten (`SchoolClass.class_teacher`), nie Personal/Admins;
  nur „auf Startpasswort zurücksetzen“, „selbst setzen“ und die eigenen dabei entstandenen Stapel (Ansehen/PDF/E-Mail).
  `users.manage`-Rollen wie bisher je Rolle (`can_manage_role`).
* **Geteilt geändert**: `routes/users.py` – `create` (bei erzeugtem Startpasswort), `reset_password` und `bulk` liefern
  zusätzlich `letter_batch: {id, expires_at, count}` (Stapel per Savepoint, Fehler brechen die Aktion nicht ab);
  `models.Student.birth_date` (optional, ISO) + `api/types.ts` (`Student.birth_date`, `Permission` `passwords.reset`);
  `permissions.py`; `maintenance.py`; `pyproject.toml` (`segno>=1.5`).
* **Klassen** (`routes/features_classes.py`): `POST /classes` (`masterdata.edit`; Konten zusätzlich `users.manage` +
  `_check_manage`) `{id, name?, grade, site?, home_room?, class_teacher?, students:[{first_name, last_name, email?,
  birth_date?, adult?, parents:[{name, email?}] (≤2)}], create_student_accounts=true, create_parent_accounts=false,
  send_email=false, send_to: student|parents|both, dry_run=false}` und `POST /classes/{id}/students` (gleiches Format).
  Prüfungen: ID frei/gültig (409/422), Jahrgang 1–13 (+ Warnung, wenn er nicht zur Bezeichnung passt), Standort/Raum/
  Lehrkraft existieren (422), Raum-Warnungen wie `PATCH` (schon Klassenraum, Standort, Kapazität, Typ), Klassenleitung
  schon anderswo, doppelte Namen (Liste und Schule), ≤ 60 Schüler/innen je Aufruf, E-Mail/Geburtsdatum plausibel
  (Zukunft, vor 1900 oder > 120 Jahre → 422; Alter unter 4 oder über 30 → Warnung wie im Assistenten).
  Volljährig = aus `birth_date` (Stichtag heute), sonst `adult`. Schüler-IDs `S00001…` fortlaufend nach der höchsten
  Nummer; ein `mutate` (Scope `classes`, `students`), dann Konten (`vorname.nachname`, Eltern `eltern.<name>`),
  `ParentLink`s und ein Brief-Stapel. **Elternkonten werden über die E-Mail zusammengeführt** (ein Konto für alle
  Kinder; vorhandenes Elternkonto mit der Adresse → Kind ergänzt, kein neues Passwort, Antwort `linked_parents`);
  ohne Elternangaben ein Konto „Eltern von …“ je Kind. `send_email` verschickt danach sofort je Person ihr PDF
  (Minderjährige laut `send_to`, Volljährige selbst, Elternbriefe an die Eltern). Antwort `{dry_run, class, students:
  [{index,id,name,…,username,parent_accounts,user_id}], warnings, accounts, linked_parents, letter_batch, email}`;
  `dry_run` speichert nichts. Scheitern Konten/Stapel nach dem `mutate`, werden Schüler/innen (und die neue Klasse)
  wieder entfernt → 500 „es wurde nichts gespeichert“. Deaktiviertes Elternkonto mit der Adresse → Kind ergänzt +
  Warnung. Audit `class.create` / `class.add_students`.
* **Frontend**: `features/zugangsdaten` (Route `/zugangsdaten/:id`, `anyOf: users.manage, passwords.reset`, ohne Menü;
  Countdown, Downloads, Tabelle, Versand mit Sicherheitshinweis; Bausteine `LetterBatchActions`, `PasswordPanel`,
  `PasswordDialog`). `features/classes`: „Neue Klasse“ → `/klassen/neu` (Assistent: Klasse → Liste einfügen
  (`studentList.ts`: Tabelle/CSV mit/ohne Kopfzeile inkl. E-Mail, Geburtsdatum, volljährig, Elternteil 1/2 + E-Mail,
  „Nachname, Vorname“, „Vorname Nachname“, Großschreibung normalisiert) → Konten inkl. „sofort per E-Mail senden“ und
  Probelauf → Ergebnis), Reiter Schüler/innen: „Schüler/in hinzufügen“, Auswahl → „Neue Zugangsdaten erzeugen“,
  Konto-Status und „Passwort“ je Schüler/in (Verwaltung; Klassenleitung für die eigene Klasse). `UsersPage`: PDF/ZIP/
  Zugangsdaten-Seite im Startpasswort-Hinweis und nach der Massenanlage, „Auf Startpasswort zurücksetzen / selbst
  setzen“ im Reiter Sicherheit.

### 11.4 Agent Anbieter – Microsoft, Apple, Google, Schulkonto (OIDC)
Besitz: `server/identities.py` (Umsetzung), `server/sso_providers.py`, `feature_models/identities.py`,
`migrations/versions/0010_identities.py` (übernimmt vorhandene `users.oidc_sub` als Anbieter `oidc`),
`routes/features_sso.py`, `tests/test_sso.py`, `frontend/src/features/anmeldedienste/*` (Feature-ID `anmeldedienste`).
Geteilt: `routes/oidc.py` (alte Pfade `/auth/oidc/*` weiter nutzbar), `config.py` (Block direkt nach den OIDC-Einstellungen),
`pages/LoginPage.tsx` (SSO-Knöpfe statt des einen OIDC-Knopfs, Fehlercodes), `pages/ProfilePage.tsx` (Abschnitt
„Verbundene Konten“ direkt nach „Zwei-Faktor-Anmeldung“), `pages/UsersPage.tsx` (Block „Verbundene Konten“ im `UserModal`).
* Tabellen `user_identities` (user_id, provider, subject NULL = vorgemerkt, email, created_at, last_login_at;
  eindeutig (provider, subject) und (user_id, provider)) und `sso_providers` (Admin-Konfiguration; Geheimnisse und
  Apple-Schlüssel verschlüsselt; Umgebungsvariablen haben Vorrang).
* Ablauf Authorization Code + PKCE + nonce wie `oidc.py`; Microsoft (Tenant, `tid`-Aussteller), Google (`hd` optional),
  Apple (`response_mode=form_post` → Callback per POST, Client-Secret als ES256-JWT aus `.p8`), allgemeines OIDC.
  Anmelden: Verknüpfung → Konto; sonst (nur wenn `effective_policy(...).sso_create`) Zuordnung über bestätigte E-Mail
  bzw. vom Admin vorgemerkte Adresse; danach `login_policy.method_allowed(db, user, provider)` prüfen.
  Verbinden aus dem Profil: `POST /me/identities/{provider}/link` → `{url}` (Status an Sitzung gebunden); Trennen nur mit
  `self_link`, nicht bei Pflicht-Verknüpfung und nur, wenn ein anderer erlaubter Anmeldeweg bleibt.
* Admin: Anbieter einrichten (nur Rolle admin), Verknüpfungen je Konto ansehen/lösen, E-Mail vormerken.
* **Test-Anbieter** (`SM_SSO_DEV_MOCK=1` **und** `SM_ENV=development`; Standard aus; in Produktion und Demo verboten): nicht konfigurierte Anbieter
  erscheinen als „Microsoft (Test)“ usw.; eine interne Seite simuliert die Anmeldung (E-Mail/Name eingeben) – derselbe
  Code-Pfad wie echte Anbieter ab dem Token-Austausch.
* Öffentlich: `GET /auth/sso/providers` → `[{id, label, mock}]` (Login-Seite).

#### 11.4.1 Umsetzung (Agent Anbieter)
* **Tabellen** (`feature_models/identities.py`, Migration `0010_identities`, `down_revision = "0007_merge"`):
  `user_identities` (id, user_id FK CASCADE, provider, subject NULL = vorgemerkt, email klein, email_verified,
  created_at, last_login_at, created_by FK SET NULL; eindeutig (provider, subject) und (user_id, provider)) und
  `sso_providers` (provider PK, enabled, client_id, client_secret_enc, tenant, hosted_domain, team_id, key_id,
  private_key_enc, issuer, label, allowed_domains JSON, updated_at, updated_by). Geheimnisse mit
  `crypto.encrypt_text` (AAD `sso_providers.<feld>:<anbieter>`, Rotation über `register_rewrap`). Die Migration übernimmt
  `users.oidc_sub` als Anbieter `oidc` (subject = `"<issuer>|<sub>"`, Spalte bleibt; beim Trennen wird sie geleert).
  Subjects: Microsoft/Google/Apple = `sub`, Schulkonto = `"<issuer>|<sub>"`, Test-Anbieter = `mock:<sha256(anbieter|email)>`.
* **Registry** `server/sso_providers.py`: `resolve(db, provider)` → `ProviderConfig` (Umgebung vor Datenbank je Feld;
  per Umgebung eingerichtet = immer eingeschaltet), `metadata` (Discovery 1 h Cache, Endpunkte nur https außer
  Entwicklung; Apple fest), `new_flow` (signierter Status-Cookie `sm_sso_<anbieter>`, Pfad `/api/v1/auth`, 10 min,
  httponly; Apple bei https `SameSite=None; Secure`, sonst Lax), `fetch_claims` (Token per TLS, `iss`/`aud`/`azp`/`exp`/
  `nonce`/`sub`), `identity_from_claims`, `domain_problem`, `apple_client_secret` (ES256, `kid`, iss=Team-ID, aud=
  `https://appleid.apple.com`, sub=Services-ID, 10 min gültig, höchstens 180 Tage). Signaturen sind zweckgebunden
  (`state` ≠ `mock_code`). Alle Abrufe über `http_json` → `_http_json` (in Tests ersetzbar, auch weiter als
  `routes.oidc._http_json`).
* **Anbieter-Details:** Microsoft `https://login.microsoftonline.com/<tenant>/v2.0` (Standard `organizations`),
  `{tenantid}` gegen `tid`; E-Mail gilt nur als bestätigt aus `preferred_username` (UPN), mit `xms_edov` oder bei festem
  Mandanten (das frei setzbare `mail`-Attribut fremder Mandanten zählt nicht; Gast-UPNs `#EXT#` ignoriert). Google
  `hd` als Parameter und Claim-Prüfung. Apple `response_mode=form_post`, Scope `name email`, **kein PKCE** (Apple
  dokumentiert es nicht; Schutz über state + nonce + JWT-Secret), `email_verified` als String. Microsoft/Google mit
  `prompt=select_account` (gemeinsam genutzte Schulrechner). `allowed_domains` (alle Anbieter): nur bestätigte Adressen
  dieser Domains (`email_unverified` / `domain_not_allowed`).
* **Anmelden** (`identities.find_login_user`): 1. Verknüpfung (provider, subject); 2. Vormerkung (subject NULL) mit gleicher
  bestätigter E-Mail, eindeutig; 3. nur mit `effective_policy(...).sso_create`: eindeutiges Konto mit gleicher
  `users.email` ohne Zeile für diesen Anbieter; 4. nur Schulkonto: **bisherige** Erst-Zuordnung über Benutzername bzw.
  bestätigte E-Mail (IdP der Schule, wie vor §11.4) und `SM_OIDC_AUTO_CREATE`. Danach `method_allowed` (sonst
  `method_not_allowed`, Audit `auth.login_denied`), `active`, `login_user(..., method=<anbieter>)`. Neue Zuordnungen
  → Audit `identity.link` (`via`: reserved/email/legacy/created/profile). Bei Fehlern wird nichts gespeichert.
* **Verbinden:** `POST /me/identities/{p}/link {next?}` → `{url}` (nur Sitzung, CSRF); Status enthält user_id + Sitzungs-ID.
  Der Callback verbindet nur, wenn diese Sitzung noch gültig ist und – falls ein Sitzungs-Cookie mitkommt – genau diese
  ist (GET verlangt das Cookie; Apple-POST ohne Lax-Cookie prüft die Sitzung über die Datenbank). Rückkehr auf `next`
  (Standard `/profil`) mit `?verbunden=<p>` bzw. `?sso_error=` `already_linked` (Anbieter-Konto gehört anderem Konto),
  `already_connected` (eigenes Konto schon mit anderem Konto dieses Anbieters), `link_not_allowed`; abgelaufen →
  `/login?sso_error=link_expired`. Pflicht-Anbieter (`required_links`) dürfen immer verbunden werden.
* **Endpunkte:** `GET /auth/sso/providers`; `GET /auth/sso/{p}/login?next=`; `GET|POST /auth/sso/{p}/callback`;
  `GET|POST /auth/sso/{p}/mock` (Test-Anbieter); `GET /me/identities` → `{providers:[{id, label, mock, available, required,
  linked, identity, can_link, can_unlink, unlink_block:{code,message}}], linked, available, required, self_link, methods}`;
  `DELETE /me/identities/{p}` (403 `link_not_allowed`, 409 `required`/`last_method`); Verwaltung (`users.manage` +
  `_check_manage`): `GET|POST /users/{id}/identities` (`{provider, email}` vormerken; 409 wenn verbunden oder Adresse bei
  anderem Konto vorgemerkt), `DELETE /users/{id}/identities/{p}`; Einrichtung (nur Rolle `admin`):
  `GET /sso/providers/config` (je Anbieter `status` active|mock|disabled|missing, `fields` ohne Geheimnisse,
  `secrets: {client_secret: bool, private_key: bool}`, `env_fields`, `redirect_uri`), `PUT /sso/providers/{p}` (leer =
  unverändert, `clear_client_secret`/`clear_private_key`; Einschalten nur vollständig, sonst 422; Apple-Schlüssel wird
  geprüft), `POST /sso/providers/{p}/test` (`{ok, message, issuer, …}`). Audit: `identity.link|unlink|reserve|admin_unlink`,
  `sso_provider.update` (nur Feldnamen).
* **Offizielle Anmelde-Oberflächen** (Migration `0028_sso_auto_signin`, Spalte `sso_providers.auto_signin`): `GET /auth/sso/providers`
  liefert je Anbieter `flow` (`gis` Google Identity Services, `apple_js` Sign in with Apple JS im Popup, `microsoft` offizieller
  Knopf + Weiterleitung, sonst `redirect`), `auto` und für gis/apple_js die öffentliche `client_id`. Skripte Dritter lädt die
  Login-Seite erst, wenn der Anbieter eingeschaltet ist (`logic.externalScripts`), die CSP wird dann gezielt erweitert
  (`middleware.csp_for` → `sso_providers.csp_sources`, 30 s Cache, bei Änderung sofort). Browser-ID-Tokens:
  `POST /auth/sso/{google|apple}/nonce` (Nonce im Status-Cookie) und `POST …/token {id_token, next?, add?}` – der Server prüft
  **Signatur über JWKS** (RS256, `kid`; unbekannte `kid` lädt höchstens alle 30 s neu), `iss`, `aud`/`azp`, `exp`, `nonce`
  (Apple: Klartext oder SHA-256), `sub`; danach wie der Callback (`_authenticate`: Verknüpfung, Login-Richtlinie, `active`; kein
  Anlegen außer bei `sso_create`). Stilles SSO: `GET …/login?silent=true&hint=<mail>` → `prompt=none&login_hint`; Fehler
  `login_required` & Co. → `/login?sso_silent=failed` ohne Meldung. Hinweis-Cookie `sm_sso_hint` (`<anbieter>|<mail>`, 90 Tage,
  nicht httponly) wird beim Abmelden gelöscht → danach weder Auto-Auswahl noch stilles SSO. Kontowechsel: `?add=true` (bzw.
  `add` im Token-Aufruf) behält die bisherigen Sitzungen (`auth.keep_sessions`). Einrichtungsansicht: `origin`, `js_origins`,
  `warnings` (Port/https), `script_hosts`, `auto_signin`/`auto_kind`.
* **Alte Pfade** `/auth/oidc/login|callback` laufen über dieselbe Umsetzung; das Schulkonto nutzt immer die beim IdP
  eingetragene Redirect-URI `{base}/api/v1/auth/oidc/callback` (auch über `/auth/sso/oidc/login`).
* **Test-Anbieter:** aktiv nur bei ausdrücklichem `SM_SSO_DEV_MOCK=1` und `SM_ENV=development` (Standard aus; Produktion/Demo → `ConfigError`, zur Laufzeit
  zusätzlich gesperrt) für nicht vollständig eingerichtete Anbieter. Relative Adressen (funktioniert hinter
  Vorschau-Proxys ohne `SM_BASE_URL`). Seite ohne JavaScript mit Banner „Test-Anbieter – nur Entwicklung“, E-Mail + Name,
  Abbrechen (→ `cancelled`); Apple simuliert `form_post` (Knopf „Weiter zum Schulmanager“). Test-Code signiert,
  2 min, einmalig, PKCE-geprüft; Claims wie beim echten Anbieter (Microsoft mit `tid`/UPN), danach derselbe Code-Pfad.
  Mit dem Test-Schulkonto meldet `name@…` ein vorhandenes Konto `name` an (bisherige Benutzernamen-Zuordnung) – praktisch
  für Vorführungen.
* **Konfiguration:** `SM_SSO_MICROSOFT_CLIENT_ID/_SECRET/_TENANT`, `SM_SSO_GOOGLE_CLIENT_ID/_SECRET/_HD`,
  `SM_SSO_APPLE_CLIENT_ID/_TEAM_ID/_KEY_ID/_PRIVATE_KEY` (PEM, auch mit `\n`, oder Dateipfad), `SM_OIDC_*` (wie bisher),
  `SM_SSO_DEV_MOCK`. Weiterleitungs-URIs: `{SM_BASE_URL}/api/v1/auth/sso/<anbieter>/callback` (Schulkonto: alter Pfad).
* **Frontend** `features/anmeldedienste/`: `slots.tsx` (`SsoButtons` mit „oder“-Trenner, „(Test)“, `next`;
  `SSO_ERROR_MESSAGES`; `IdentitiesSection` → `IdentitiesSection.tsx`; `UserIdentitiesPanel` → `UserIdentitiesPanel.tsx`),
  Seite `/anmeldedienste` (`SetupPage.tsx`, Menü Verwaltung, nur admin): je Anbieter Status, Felder (Umgebung gesperrt),
  Weiterleitungs-URI kopieren, Speichern, „Verbindung testen“, Hinweis Test-Anbieter. `logic.ts` (+ vitest).

### 11.5 Agent Richtlinien – wer darf sich wie anmelden
Besitz: `server/login_policy.py` (Umsetzung), `feature_models/login_policy.py`, `migrations/versions/0011_login_policy.py`,
`routes/features_login_policy.py`, `tests/test_login_policy.py`, `frontend/src/features/anmelderichtlinien/*`
(Feature-ID `anmelderichtlinien`).
Geteilt: `permissions.py` (Recht `login_policy.manage` für admin + schulleitung), `frontend/src/api/types.ts`
(`Permission`, Feld `login_setup` am `User`), `routes/auth.py` (Passwort-Anmeldung prüft die Richtlinie),
`deps.py` (Sperre `link_required` wie `password_change_required`; Feld `login_setup` in `AuthUser.public()`),
`frontend/src/App.tsx` (Guard leitet bei fehlenden Pflicht-Verknüpfungen auf `/konten-verbinden`).
* Tabelle `login_policy_rules` (scope `default` | `role` | `grade` | `class` | `user`, scope_ref, audience `alle` |
  `schueler` | `eltern` für grade/class; Felder `methods`, `required_links`, `self_link`, `reset_channels`, `sso_create` –
  jeweils NULL = erben). Vorrang je Feld: Person > Klasse (Zielgruppe vor „alle“) > Jahrgang > Rolle > Standard.
  Eltern: Klassen ihrer Kinder, mehrere Kinder → Felder vereinigt (Wege/Kanäle: Vereinigung, Pflicht: Vereinigung,
  Schalter: wahr, wenn eine Regel wahr ist). `sources` nennt die Herkunft je Feld. Admin-Konten: `password` immer erlaubt.
* Passwort nicht erlaubt → Anmeldung 403 `method_not_allowed` (mit erlaubten Wegen) – außer **Ersteinrichtung**
  (Startpasswort, `must_change_password`, fehlende Pflicht-Verknüpfungen): dann Sitzung nur zum Verbinden.
  Fehlende Pflicht-Verknüpfungen → API 403 `link_required` außer `/auth/*`, `/me/identities*`, `/auth/sso/*`;
  Frontend-Seite `/konten-verbinden` (nutzt `POST /me/identities/{provider}/link`).
* Endpunkte: `GET /login-policies` (Regeln + Auswahl Rollen/Jahrgänge/Klassen/Anbieter), `PUT`/`DELETE`
  `/login-policies/{scope}/{ref}?audience=`, `GET /login-policies/effective?user_id=` (mit Herkunft),
  `GET /login-policies/report?class_id=` (wer hat Pflicht-Verknüpfungen noch nicht).
* Frontend: Verwaltungsseite „Anmelde-Richtlinien“ (Standard, Rollen, Jahrgänge, Klassen mit Zielgruppe, Personen;
  je Feld „erben“ oder festlegen), Vorschau „Was gilt für …?“, Bericht fehlender Verknüpfungen.

#### 11.5.1 Umsetzung (Agent Richtlinien)
* **Auswertung** (`server/login_policy.py`): `effective_policy(db, user, *, include_personal=True, rules=None)` nimmt
  `db_models.User` und `deps.AuthUser`. Stufen je Feld: Person → Klasse (Zielgruppe, dann `alle`) → Jahrgang (ebenso) →
  Rolle → Standard → `DEFAULT_POLICY` (Herkunft „Voreinstellung“). Schüler/innen über `student_id` → Planungsdokument
  (Klasse, `grade`), Eltern über `AuthUser.student_ids` bzw. `ParentLink` (Zielgruppe `eltern`); je Kind komplett
  aufgelöst und dann vereinigt. `sources` z. B. „Klasse 5a · Schüler/innen“, „Jahrgang 5“, „Rolle Eltern“, „Standard“,
  „Person“, bei mehreren Kindern „Klasse 5a · Eltern + Klasse 7a · Eltern“. Admin: `password` immer ergänzt (Hinweis
  in `sources`), `required_links` leer. Gespeicherte Werte werden auf bekannte Wege/Anbieter/Kanäle begrenzt, leere
  `methods` gelten als „erben“ (nie aussperren). Weitere Hilfen: `group_policy` (Klasse/Jahrgang + Zielgruppe),
  `role_policy`, `missing_links`, `password_login(db, user) → "ok" | "setup" | "denied"`, `validate_values`
  (`PolicyError`), `invalidate_cache`, `scope_label`.
* **Erweiterbar**: Gruppen-Bereiche stehen in `MEMBER_SCOPES` (heute `class`, `grade`). Ein späterer Bereich `group`
  (Klassengruppen wie „IT-Zweig 11–13“, „Abi-Klassen“) braucht dort einen Eintrag (Funktion Klasse → Gruppen), den Wert
  in `SCOPES`/`AUDIENCE_SCOPES` (`feature_models/login_policy.py`), eine Prüfung in `routes/features_login_policy.py::_target`
  und eine Zeile in `inheritChains` (Frontend-Anzeige).
* **Cache**: Regeln prozessweit 5 s (`CACHE_SECONDS`), Schlüssel = Engine + URL; gelesen in eigener Sitzung (ein Fehler
  stört die Transaktion des Aufrufers nicht → Voreinstellung + Log). ORM-Änderungen an `LoginPolicyRule` leeren den Cache
  nach dem Commit automatisch (Session-Ereignisse in `feature_models/login_policy.py`); Konto gelöscht → seine
  Personen-Regeln werden mitgelöscht (`User.after_delete`). Klassenzuordnung je Planungsversion zwischengespeichert.
* **Durchsetzung**: `routes/auth.py::login` prüft nach Passwort, Aktiv und TOTP: nicht erlaubt → 403
  `method_not_allowed`, erlaubte Wege im Kopf `X-Login-Methods: microsoft,apple` (nur bei korrektem Passwort; Audit
  `auth.login_denied`, zählt als Fehlversuch). **Ersteinrichtung** = `must_change_password` + mindestens eine fehlende
  Pflicht-Verknüpfung, deren Anbieter `identities.available_providers` liefert → Anmeldung (Audit-Methode
  `password_setup`). `deps.build_auth_user` setzt `AuthUser.login_setup = {"missing_links": [...], "setup_only": bool}`
  (`setup_only` = Passwort ist kein erlaubter Weg) und bei nicht erlaubtem Passwort `must_change_password = False`;
  `current_user` → 403 `link_required` außer `LINK_SETUP_ALLOWED = ("/auth/", "/me/identities")`. Reihenfolge:
  `password_change_required` (nur wenn Passwort erlaubt) → `totp_setup_required` → `link_required`. Nach vollständiger
  Verknüpfung läuft die Sitzung normal weiter; eine neue Passwort-Anmeldung wird dann abgelehnt (Startpasswort bleibt nur
  für die Ersteinrichtung nutzbar, solange eine Pflicht-Verknüpfung fehlt **und** noch kein erlaubter, verfügbarer
  Anbieter verbunden ist – kommt später eine Pflicht hinzu, meldet man sich über den Anbieter an und verbindet dann).
* **Endpunkte** (`routes/features_login_policy.py`, Recht `login_policy.manage`):
  * `GET /login-policies` → `{rules: [{id, scope, ref, audience, label, methods…, note, updated_at, updated_by, orphan,
    target}], options: {roles[{id,label,manageable}], grades[{id,label,classes}], classes[{id,name,grade}],
    providers[{id,label,available,mock}], methods, reset_channels[{…,available}], audiences, fields}, defaults,
    can_manage_admins}`.
  * `PUT /login-policies/{scope}/{ref}?audience=` (Standard: `ref` `-` oder `PUT /login-policies/default`), Body
    `{methods?, required_links?, self_link?, reset_channels?, sso_create?, note}` – fehlend/`null` = erben; alle Felder
    `null` → Regel wird entfernt (`{"rule": null}`). 422 bei unbekanntem Bereich/Rolle/Jahrgang/Klasse/Konto, Zielgruppe
    außerhalb grade/class, leeren oder unbekannten Wegen, Anbietern ⊄ `identities.PROVIDERS`, unbekannten Kanälen.
    403: Rolle `admin` und Admin-Konten nur durch admin. 409: Schulleitung würde sich selbst aussperren (kein Passwort
    und kein verbundener, erlaubter **und eingerichteter** Anbieter bzw. Pflicht-Anbieter nicht eingerichtet).
  * `DELETE /login-policies/{scope}/{ref}?audience=` (404 ohne Regel; verwaiste Regeln löschbar).
  * `GET /login-policies/effective?user_id=` → `{target{user, students[{name, class}]}, policy, inherited (ohne
    Personen-Regel), linked, missing_links, password_login}`; `?class_id=&audience=schueler|eltern`, `?grade=&audience=`,
    `?role=` → `{target, policy}`.
  * `GET /login-policies/report?class_id=&audience=alle|schueler|eltern` → `{class, counts{schueler|eltern: {accounts,
    required, complete, missing}}, students_total, students_without_account, items[{user, group, students, required,
    linked, missing, last_login}]}` (nur Konten mit fehlender Verknüpfung).
  * Audit `login_policy.set` / `login_policy.delete` (Ziel `login_policy:<scope>:<ref|->:<audience>`, vorher/nachher).
* **Frontend** `features/anmelderichtlinien/`: `/anmelde-richtlinien` (Menü „Anmelde-Richtlinien“, Gruppe Verwaltung,
  Symbol `shield`) mit Reitern Standard · Rollen · Jahrgänge · Klassen (Suche, „nur mit eigener Regel“, je Klasse Alle /
  Schüler/innen / Eltern) · Personen (Suche über `GET /users`) · Vorschau · Bericht; Regel-Editor (Dialog) je Feld
  „Erben – <Wert> (Herkunft)“ oder festlegen, Hinweise (Pflicht ohne Anmeldeweg, ohne Passwort), Beispiel-Knopf
  „nur Microsoft + Apple, beide Pflicht“ (auch oben auf der Seite für die Rolle Schüler/in). `LinkSetupPage`
  (`/konten-verbinden`): fehlende Pflicht-Anbieter mit „Jetzt verbinden“ (`POST /me/identities/{p}/link {next:
  "/konten-verbinden"}` → `window.location`), nicht verfügbare mit „Bitte an das Sekretariat wenden“, Fehler über
  `?sso_error=` (Texte aus `SSO_ERROR_MESSAGES`), „Erneut prüfen“, „Abmelden“; lädt beim Öffnen den Benutzer neu.
  Reine Logik in `logic.ts` (vitest `logic.test.ts`).

## 12. Wochen (52-Wochen-System) und 7-Tage-Woche – Vertrag

Verbindlich ist dieser Abschnitt; `docs/entwurf/KALENDER-ZEITRASTER.md` beschreibt Kalender und Zeitraster.

* **Begriffe**: laufende Woche L = `calendar_utils.week_no` bzw. `plan_week` (1 … Y, Mo–So, Ferien zählen mit; Woche 1 =
  Woche des Schuljahresbeginns `school_year_start`, leer = Altfeld `cycle_start`). Anzeige nur mit Ziffern (G1);
  `week_text` („Woche 6 · KW 41“) baut das Backend.
* **Wochenangabe** (überall gleich): jede Woche (`weeks` leer, `rhythm` leer) · ausgewählte Wochen (`weeks`, laufende
  Wochen 1-basiert, 1 … 53) · Rhythmus (`rhythm {every: k, from_week: s, to_week: e}`, `to_week` 0 = offen, k beliebig 1 … 53).
  Nie beides zugleich. Felder: `TimeRule`, `Duty`, `Course`, `Lesson`, Zeitfenster der Lehrkraft, Wünsche.
  Lehrkraft-Arbeitszeiten als Raster (`Teacher.work_grid`) werden zu Regeln mit Rhythmus „alle N Wochen ab Woche k+1“.
* **Felder**: `Settings.week_numbering, school_year_start, school_year_history, school_days`; `SchoolClass.school_days`
  (leer = Schule); `Holiday.kind` (`ferien|feiertag|beweglich|schulfrei`, Lesepfad V15); `WEEKDAYS` 7 Namen.
* **Eine Aktiv-Logik**: `weeks.lesson_active_in` = Wochenangabe von Stunde ∩ Kurs; Engine, Ansicht, Bericht, Kursräume,
  Klausuren, Aufsichten, Klassen-Seite, iCal, Untis und Jobs nutzen sie (`ActiveIndex`, `real_week`).
* **Generator** (`scheduler.py`): Wochenvarianten über die laufenden Wochen des Schuljahres (Gruppen mit gleicher Signatur
  aus Regeln, Kursen und fixierten Stunden), Gitter V × 7 × P, Gewicht m_v·V/Y, Blöcke tragen ihre Varianten, Teilung nur
  in einzelne Varianten; Stunden eines Blocks werden als `weeks`/`rhythm` zurückgegeben (`Horizon.to_spec`);
  `generate(…, iterations=…)` reproduzierbar (V1); `Scheduler.variants`. Aufsichten je Variante (`duties.duty_variants`).
* **Bericht** (`timetable.validate_school`): rechnet über `weeks.PlanWeeks` (Varianten, Gewicht = Anteil der Schulwochen),
  Konfliktmeldung mit Wochentext („Woche 1 und jede 2. Woche“), `stats.week_variants`.
* **Bestätigungen**: 409 `{code: "plan_change", message, changes[{kind,id,label,before,after}]}` bei entfallenden
  Unterrichtstagen und gekoppelten Kursen, nur mit `?force=1` übernommen (`PATCH /classes/{id}`, `PUT /data/classes/{id}`).
  Planungsfelder der Klasse nur mit `timetable.edit` (sonst 403, R1).
* **Altdokumente**: `legacy.migrate_document` (beim Laden in `School.from_dict`) rechnet Dokumente mit Schul-/Klassenzyklus
  verlustfrei um (Zykluswoche i im Zyklus n → Rhythmus „alle n Wochen ab Woche …“, mehrere Wochen → Liste); alte
  Request-Felder (`cycle_weeks` …) werden ignoriert, `week_pattern` wird zum Rhythmus.
* **Endpunkte**: `GET /calendar/school-year`, `GET /calendar/week`, `POST /settings/calendar-preview`,
  `GET /timetable/{kind}/{ref}?date=|week_no=&all_days=` (Standard `all_days=1`, E2). Details: `docs/code/03`, `04`.
* **Schnittstellen**: CSV Wochen „1,3“ / „1-4,9“, Rhythmus „jede 3. Woche ab Woche 10: …“ (auch in der Stundenliste),
  Klassen-Spalte „Unterrichtstage“, Stunden „Beginn“/„Ende“ (nur Export); Untis-Text „(Woche 1, 3)“ (Wochenmuster einer
  Untis-Datei werden zu „jede n. Woche ab Woche i“); iCal „Woche n“; Webhook zusätzlich `week_info`, `day_kind`,
  `week_no`, Schema v1.
