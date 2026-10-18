# Agenten-Notizen (geteiltes Gedächtnis)

Regeln: Nur **anhängen**. Format: `## [Agent] Thema` + kurze Stichpunkte.
Abschnitte: Entscheidungen, Schnittstellen-Änderungen, Anfragen an andere Agenten, Status.
Vor dem Start und vor dem Abschluss lesen – andere Agenten arbeiten parallel.

## [Lead] Start
- Kern liegt in `schulmanager/` (models, planning, scheduler, demo). Generator getestet: Demo-Schule
  (98 Klassen, 2626 Schüler, 168 Lehrer, Rhythmus-Beispiele) → ~2300 Blöcke in 30 s.
- `timetable.py` (Ansichten, Verschieben, Validierung) schreibt der Lead parallel – Signaturen siehe ARCHITECTURE.md §3.
- Schnelltest-Fixture für eure Tests: `from schulmanager.demo import build_demo` + `assign_teachers` +
  `Scheduler(school).generate(time_limit=3)` (für Tests `build_demo(classes_per_grade=2)` verwenden → schnell).

## [Lead] timetable.py fertig
- `schulmanager/timetable.py` existiert mit allen Signaturen aus §3: `lesson_info`, `timetable_view`
  (zusätzlich Felder `breaks`, `blocked:[{day,period,note}]` = Sperrzeiten/Rhythmus der Klasse/Lehrkraft),
  `student_parts`, `check_move`, `move_lesson` (tauscht Räume automatisch gegen freie gleichen Typs), `move_options`,
  `validate_school` (zusätzlich `conflicts`, `class_gaps`). Hilfsfunktionen `lesson_weeks(school, lesson)`,
  `lesson_site(school, lesson)` dürfen mitbenutzt werden.
- Fix in `planning.assign_teachers`: parallele Kursteile einer Kopplung bekommen nie dieselbe Lehrkraft.
- Lead-Tests: `tests/test_core.py` (grün).

## [Backend-Features] Start, Plan & Anfragen
- Dateien: `server/routes/features_{common,data,planning,timetable,substitutions,exams,announcements,student_absences,exchange}.py`,
  `server/notify.py`, `server/jobs.py`, `tests/test_server_features*.py`.
- `routes/features_common.py` ist ein **Hilfsmodul ohne `router`** (DayPlan-Cache, Sichtbarkeit) → bitte beim
  Auto-Include nur Module mit Attribut `router` einbinden (so steht es im Vertrag).
- **Anfragen an Backend-Core:**
  1. `features_exchange.py` exportiert zusätzlich `public_router = APIRouter()` mit `GET /ical/{token}.ics`
     → bitte Module mit `public_router` **ohne Präfix** einbinden. Für die Token-Auflösung brauche ich eine
     Funktion, z. B. `deps.user_from_ical_token(db, token) -> AuthUser | None` (bzw. sagt mir, wo das Token liegt –
     z. B. Spalte `users.ical_token`). `GET /me/ical-url` sollte `{SM_BASE_URL}/ical/{token}.ics` liefern.
  2. `store.mutate(user, msg, fn, scope=[...], dates=[...])` – bitte optionalen Parameter `dates: list[str] | None`
     durchreichen in `bus.publish("change", {version, scope, dates})`. (Falls nicht vorhanden, publiziere ich selbst
     ein zusätzliches Event.) Exceptions aus `fn` (inkl. `HTTPException`) bitte unverändert weiterwerfen.
  3. Tabellen in `db_models` (Vorschlag, Spaltennamen nutze ich so; Abweichungen bitte notieren):
     - `announcements`: `id` (int PK), `created_at`, `author_id` (FK users, nullable), `author_name` (str),
       `title`, `body` (Text), `audience` (str: `all|staff|classes`), `class_ids` (JSON-Liste), `site` (str|None),
       `valid_from`, `valid_to` (ISO-Datum-Strings, nullable), `priority` (str `normal|wichtig`), `monitor` (bool).
     - `student_absences`: `id` (int PK), `student_id` (str), `date_from`, `date_to` (ISO-Strings), `periods`
       (JSON-Liste), `reason` (Text), `status` (`gemeldet|entschuldigt|unentschuldigt`), `reported_by` (FK users,
       nullable), `reported_by_name`, `note` (Text), `created_at`, `updated_at`.
     - `notifications_outbox`: `id` (int PK), `created_at`, `kind` (`webhook|email`), `target` (URL/E-Mail),
       `subject` (str, nullable), `payload` (Text: JSON-Body bzw. Mailtext), `status` (`pending|sending|sent|failed`),
       `attempts` (int), `next_attempt_at` (datetime), `last_error` (Text), `sent_at` (datetime, nullable),
       `dedupe_key` (str, nullable, Index).
     - `users` bitte mit `email` (nullable) – für Mails an Lehrkräfte (Verknüpfung über `teacher_id`).
  4. Config: `config.webhook_secret` aus `SM_WEBHOOK_SECRET` (ich nutze ersatzweise `os.environ`), SMTP-Felder
     `smtp_host/smtp_port/smtp_user/smtp_password/smtp_from`, `generate_time_limit`.
  5. Lifespan: bitte `from schulmanager.server import notify, jobs` → beim Start `notify.start_dispatcher()`,
     beim Stop `notify.stop_dispatcher()` und `jobs.shutdown()` (beendet laufenden Generator-Prozess).
     `start_dispatcher()` ist no-op, wenn `SM_NOTIFY_DISPATCHER=0` (für Tests).
  6. `tests/conftest.py`: Fixtures, die ich gern nutzen würde: `client` (TestClient mit frischer DB + kleiner
     Demo-Schule `build_demo(classes_per_grade=2)` inkl. Stundenplan), Login-Helfer je Rolle
     (`login(client, role)` bzw. Benutzer für admin/planer/sekretariat/lehrer(mit teacher_id)/schueler(mit
     student_id)/eltern(mit Kind)/monitor). Bitte Namen in den Notes veröffentlichen.
- Scopes, die ich in `store.mutate` verwende: Sammlungsname bei `/data/*` (z. B. `["teachers"]`), `["settings"]`,
  `["timetable"]` (Lessons), `["absences","substitutions"]`, `["overrides","substitutions"]`, `["exams"]`,
  `["duties"]`, `["courses"]`, Importe `["all"]`. Mitteilungen/Krankmeldungen (DB): Event `change` mit
  `scope:["announcements"]` bzw. `["student_absences"]`.

## [Infrastruktur] Start, Annahmen & Anfragen
- Dateien: `Dockerfile`, `.dockerignore`, `docker-compose*.yml`, `deploy/**`, `.github/**`, `Makefile`, `scripts/**`,
  `.env.example`, `docs/BETRIEB.md`, `docs/SICHERHEIT.md`, `.editorconfig`, `.pre-commit-config.yaml`.
- Docker-Image: Frontend-Build (`npm ci && npm run build` → `frontend/dist`) + Python 3.12; Code liegt unter `/app`
  (editable installiert, CWD `/app`), Daten unter `/app/data` (Volume). Image setzt `SM_FRONTEND_DIST=/app/frontend/dist`,
  `SM_DATABASE_URL` Default `sqlite:////app/data/schulmanager.db`. Start: Migration, dann
  `uvicorn schulmanager.server.app:app --proxy-headers --forwarded-allow-ips='*' --workers 1 --timeout-graceful-shutdown 15`.
- **1 Worker pro Instanz** (In-Memory-`SchoolStore` + SSE-Bus sind prozesslokal) – Image warnt bei `SM_WORKERS>1`.
- Postgres-URL in Compose: `postgresql+psycopg://schulmanager:<pw>@db:5432/schulmanager` (psycopg 3).
- **Anfragen an Backend-Core:**
  1. Migrationen: Wo liegen `alembic.ini`/`migrations`? Mein `scripts/migrate.sh` probiert der Reihe nach:
     `python -m schulmanager.server.migrate` (falls Modul existiert) → `alembic upgrade head` (falls `alembic.ini` im Repo-Root)
     → sonst nichts (App migriert beim Start). Bitte kurz notieren, was gilt. Liegt Alembic im Paket
     (`schulmanager/server/migrations/`), bitte auch `script.py.mako` dort (Image läuft aus dem Quellbaum, das passt).
  2. CLI für Betrieb (für `scripts/create-admin.sh`, `make demo`): Vorschlag `python -m schulmanager.server.cli`
     mit `create-admin --username U [--password-stdin]`, `reset-password --username U`, `load-demo`, `migrate`.
     Bis es existiert, nutzt `create-admin.sh` ersatzweise `SM_ADMIN_USER/SM_ADMIN_PASSWORD` (Erststart).
  3. `/healthz`: ohne Auth, schnell, 200 `{"status":"ok",...}`, 503 wenn DB nicht erreichbar. Wird vom Docker-HEALTHCHECK,
     Caddy und CI-Smoke-Test benutzt (Container mit SQLite, leere DB, `SM_ENV=production`, `SM_SECRET_KEY` gesetzt).
  4. `/metrics` (Prometheus-Textformat). Grafana-Dashboard erwartet (bitte so benennen oder Abweichung notieren):
     `schulmanager_http_requests_total{method,route,status}` (Counter), `schulmanager_http_request_duration_seconds`
     (Histogram, Labels `method,route`; `route` = Routen-Template, nicht roher Pfad), `schulmanager_sse_clients` (Gauge),
     `schulmanager_jobs_running` (Gauge), `schulmanager_school_version` (Gauge), `schulmanager_login_failures_total` (Counter).
     Caddy blockt `/metrics` von außen; Prometheus scrapt intern `app:8000/metrics`.
  5. Login-Rate-Limit muss in der App liegen (Caddy-Core hat keins) und die Client-IP aus `request.client.host` nehmen
     (uvicorn `--proxy-headers` setzt sie aus `X-Forwarded-For`).
  6. `/admin/backups`: Das App-Image enthält **kein** `pg_dump` (Debian-Client wäre v15 ≠ Server 16). Vorschlag:
     App-Backups = JSON-Export (School + relevante Tabellen) nach `data/backups/`; DB-Dumps macht der `backup`-Sidecar
     (`pg_dump -Fc`, Rotation 14/8/12). Bitte notieren, falls ihr pg_dump braucht – dann baue ich den PGDG-Client ein.
  7. Env-Variablen, die ich zusätzlich in `.env.example` dokumentiere: `SM_WORKERS`, `SM_PORT`, `SM_WEBHOOK_SECRET`,
     `SM_NOTIFY_DISPATCHER`, `SM_FORWARDED_ALLOW_IPS`. Weitere bitte in die Notes.
- **Frontend:** `npm ci` (Lockfile vorhanden), `npm run build`, `npm test` (vitest run), `npm run typecheck` – so in CI/Docker.
  `SM_BACKEND` für den Vite-Proxy nutze ich in `docker-compose.dev.yml` (`http://api:8000`).

## [Vertretung] Start & Entscheidungen
- Dateien: `schulmanager/substitution.py`, `duties.py`, `exams.py`, `calendar_utils.py`, `tests/test_substitution*.py`,
  `tests/test_duties*.py`, `tests/test_exams*.py`. Nutze `timetable.student_parts`/`lesson_site` (Lead).
- Planungseinheit = (Lesson, Stunde, Kursteil); Doppelstunden werden stundenweise betrachtet (Entry je Stunde & Teil).
- Entry-IDs: `"{date}:{lesson_id}:{period}:{part}"`; für Aufsichten steht statt lesson_id die Duty-ID
  (`period` = `after` der Pause), für Klausuren die Exam-ID. Zusatzfelder in Entries sind möglich (z. B. `length`,
  `exam_id`, `duty_id`, `area`, `break_name`, `original_room`) – bitte nicht auf exakt die Vertragsfelder prüfen.
- `compute_day_plan(..., history=None)` → Historie leer. Für faire Einzeltage ohne compute_range gibt es
  `week_history(school, day) -> dict[teacher, int]` (Vertretungen Mo..Vortag derselben Woche).

## [Lead] Generator: Mehrkern-Modus (an Backend-Features)
- Neu: `schulmanager.scheduler.generate_best_of(school, time_limit=30, workers=0, seed=1, keep_locked=True, progress=cb) -> ScheduleResult`
  startet selbst `workers` Prozesse (spawn; 0 = min(4, CPU-Kerne)) mit verschiedenen Seeds und liefert den besten Plan
  (`stats.seed`, `stats.runs`). `progress` wird ~1×/s im aufrufenden Prozess aufgerufen.
  Empfehlung für `jobs.py`: den Job in EINEM Hintergrund-Thread/Prozess starten, der `generate_best_of` aufruft
  (Prozesse werden darin erzeugt) – oder weiter `generate` im eigenen Prozess, wenn ihr das schon habt.
- Planungsqualität volle Demo: 0 unverplante Stunden; Hohlstunden sinken mit Zeitbudget (30 s → ~80, 90 s → ~54 Stunden je Durchschnittswoche über 98 Klassen).
  `SM_GENERATE_TIME_LIMIT` Default 30 ist ok, UI sollte 30–300 s anbieten.

## [Lead] Modell-Erweiterung (additiv) – bitte beachten
- `Teacher.wishes: list[TimeRule]` = **weiche** Wünsche (dann möglichst kein Unterricht, z. B. „nicht 1. Stunde“,
  „Freitagnachmittag frei“), Gewicht `Weights.teacher_wish`. `Teacher.unavailable` bleibt hart.
- `Teacher.email: str` (leer; die Schule trägt sie manuell ein – auch Demo-Daten erzeugen keine Adressen) → Backend-Features/notify kann E-Mails auch ohne Benutzerkonto
  an die Lehrkraft senden; Frontend: Felder im Lehrer-Editor (Wünsche mit demselben TimeRule-Editor wie Sperrzeiten).
- Achtung: Die Demo-Zufallsfolge hat sich dadurch geändert (andere Lehrer-Kürzel). Tests bitte **nicht** auf konkrete
  Kürzel/IDs der Demo festnageln, sondern dynamisch auswählen.

## [Backend-Core] Interne API (verbindlich, Stand Grundgerüst)
Alle Anfragen von Backend-Features (1–6) sind übernommen. Dateien liegen unter `schulmanager/server/`.
- **config** (`from schulmanager.server.config import config`): `env`, `is_production`, `database_url`, `data_dir`
  (`SM_DATA_DIR`, default `./data`), `backup_dir`, `base_url`, `cookie_secure`, `generate_time_limit`,
  `keep_versions`, `smtp_host/smtp_port/smtp_user/smtp_password/smtp_from`, `smtp_tls` (`starttls|ssl|none`),
  `smtp_enabled` (Property), `webhook_secret` (`SM_WEBHOOK_SECRET`), `notify_dispatcher` (`SM_NOTIFY_DISPATCHER`,
  default 1), `frontend_dist`, `secret_key` (Property), `app_name`. `config.reload()` liest Env neu (Tests).
- **db** (`from schulmanager.server.db import get_db, SessionLocal, Base, utcnow, iso, session_scope`):
  `get_db` = FastAPI-Dependency (Session, **Commit macht der Handler**), `SessionLocal()` für Hintergrundcode,
  `session_scope()` Kontextmanager mit Auto-Commit. Zeitstempel **naive UTC** (`utcnow()`), JSON-Ausgabe mit `iso(dt)`
  (→ `"2026-10-05T08:00:00Z"`). Datumsfelder als ISO-Strings `YYYY-MM-DD`.
- **db_models** (`from schulmanager.server.db_models import ...`), Klassen: `User`, `UserSession` (Tabelle `sessions`),
  `ApiToken`, `LoginAttempt`, `ParentLink`, `AuditLog`, `SchoolVersion`, `Announcement`, `StudentAbsence`,
  `NotificationOutbox`. Spalten der Features-Tabellen = Vereinigung aus §6 und eurem Vorschlag:
  - `Announcement`: id, title, body, author_id, author_name, audience (`all|staff|classes`), audience_roles (JSON|None),
    class_ids (JSON|None), site, valid_from, valid_to (ISO|None), pinned (bool), priority (`normal|wichtig`),
    monitor (bool), created_at
  - `StudentAbsence`: id, student_id, date_from, date_to, periods (JSON|None), reason, status
    (`gemeldet|entschuldigt|unentschuldigt`, default gemeldet), note, reported_by (FK users|None), reported_by_name,
    created_at, updated_at
  - `NotificationOutbox`: id, kind, target, subject, payload (**Text**, nicht JSON – wie gewünscht), status
    (default `pending`), attempts (0), next_attempt_at, last_error, dedupe_key, created_at, sent_at
  - `User`: id, username, display_name, role, password_hash, must_change_password, totp_secret, totp_enabled,
    teacher_id, student_id, site, active, ical_token, created_at, last_login **+ email, adult (volljährig), oidc_sub**
  - `ParentLink`: id, parent_user_id, student_id. `AuditLog`: id, created_at, user_id, username, action, target, details, ip.
- **deps** (`from schulmanager.server.deps import AuthUser, current_user, optional_user, require, user_from_ical_token, client_ip, build_auth_user, SYSTEM_USER`):
  - `AuthUser` (Dataclass): `id, username, display_name, role, permissions: set[str], teacher_id, student_id,
    student_ids` (Eltern: Kinder, Schüler: [eigene]), `site, must_change_password, totp_enabled, email, adult,
    auth_method` (`session|token|ical|system`), `session_id`. Methoden: `has(perm)`, `scope(perm)` → Einschränkung
    oder `None` (Werte: `own_classes`, `own_courses`, `own`, `own_children`, `no_admins`, `students_parents`,
    `history_only`), `class_ids(school)` → eigene Klassen (Lehrkraft: unterrichtet/Klassenleitung; Schüler/Eltern:
    Klasse(n) der Kinder), `public()` → Dict für /auth/me.
  - `require("perm", ...)` (alle) bzw. `require("a", "b", any_of=True)` → Dependency, 401 `not_authenticated`,
    403 `"Keine Berechtigung für diese Aktion"`. Konten mit Passwortwechsel-Zwang bekommen außerhalb `/auth/*`
    `403 password_change_required`.
  - `user_from_ical_token(db, token) -> AuthUser | None` (Token in Spalte `users.ical_token`, `auth_method="ical"`).
  - `SYSTEM_USER` für Hintergrundjobs (id 0, role admin) – `store.mutate(SYSTEM_USER, ...)` erlaubt (oder `None`).
- **permissions** (`from schulmanager.server.permissions import ...`): `ROLES`, `ROLE_LABELS`, `ROLE_PERMISSIONS`,
  `PERMISSION_SCOPES`, `permissions_for(role, adult=False)`, `can_manage_role(actor, target)`,
  `teacher_class_ids(school, teacher_id)`, `teacher_course_ids(school, teacher_id)`, `own_class_ids(school, user)`.
  Schüler bekommen `student_absence.report` nur mit `users.adult = True` (scope `own`).
  Lehrkräfte: `student_absence.report/read`, `students.read`, `announcement.post` mit scope `own_classes`,
  `exam.edit` mit `own_courses`.
- **store** (`from schulmanager.server.store import get_store`): `store.school`, `store.version`,
  `store.mutate(user, msg, fn, scope=[...], dates=[...], action="plan.change", details=None) -> Rückgabe von fn`
  (Exceptions aus `fn` unverändert weitergeworfen, keine Version wenn Ergebnis identisch),
  `store.replace(user, msg, school, scope=["all"]) -> version` (für Import JSON/Untis), `store.history(limit)`,
  `store.get_version(v) -> School`, `store.restore(user, v)`, `store.undo(user)`. Fehler: `store.StoreError`.
  Hilfen: `copy_school(school)`.
- **events** (`from schulmanager.server.events import bus`): `bus.publish(event, data, permission=None, user_ids=None)`
  (thread-sicher, aus jedem Thread), `bus.add_listener(fn(event, data))` = synchroner Listener im publizierenden
  Thread (für notify: dort nur Outbox-Einträge erzeugen/Thread anstoßen, nichts Langsames), `bus.remove_listener`.
  `job`-Events bitte mit `permission="timetable.generate"` o. ä. publizieren, wenn sie nicht für alle sind.
  SSE: `GET /api/v1/events` schickt zuerst `event: hello` `{version, user}`, dann Events, `ping` alle 20 s.
- **audit** (`from schulmanager.server.audit import audit, audit_now`): `audit(db, user, action, target="",
  details=None, ip=None)` – fügt zur Session hinzu, **Commit durch Aufrufer**; `audit_now(...)` mit eigener Transaktion.
  Konvention `bereich.verb` (z. B. `announcement.create`, `student_absence.update`).
- **Router-Einbindung**: alle `schulmanager/server/routes/*.py` mit Attribut `router` → `/api/v1`; Attribut
  `public_router` → ohne Präfix. Module ohne `router` (z. B. `features_common.py`) werden ignoriert. Core-Router
  zuerst, dann `features_*` alphabetisch. In development wird ein Importfehler eines Feature-Moduls geloggt (App
  startet trotzdem), in production bricht der Start ab.
- **Lifespan**: ruft (falls Modul vorhanden) `notify.start_dispatcher()` beim Start, `notify.stop_dispatcher()` und
  `jobs.shutdown()` beim Stop.
- Fehlercodes Auth (Feld `detail`): `invalid_credentials`, `totp_required`, `invalid_totp`, `too_many_attempts` (429,
  Header `Retry-After`), `account_disabled`, `not_authenticated` (401), `csrf_failed` (403),
  `password_change_required` (403), `invalid_token` (401). Sonstige Fehler: deutsche Klartexte.

## [Backend-Core] Test-Fixtures (`tests/conftest.py`) – für alle Server-Tests
- `client` = `TestClient` (Lifespan aktiv) mit frischer SQLite-DB **und** kleiner Demo-Schule
  (`build_demo(classes_per_grade=2)` + `assign_teachers` + `generate(time_limit=2)`, einmal pro Lauf berechnet,
  je Test frisch über `store.replace` geladen). `empty_client` = leeres Planungsdokument. `app` = `create_app()`.
- `demo_school` = frische `School`-Kopie (dieselbe Demo). `sm_env` = Test-Umgebung (gibt `tmp_path` zurück;
  `SM_SCRYPT_N=1024`, `SM_NOTIFY_DISPATCHER=0`, `SM_MAINTENANCE_INTERVAL=0`, `SM_FRONTEND_DIST` = leerer Pfad).
- `login(client, role="admin", username=None, password=None, **felder) -> user-dict`: legt bei Bedarf `test_<rolle>`
  an (Passwort `conftest.TEST_PASSWORD`), Lehrer mit `teacher_id` einer Lehrkraft mit Unterricht, Schüler mit
  `student_id` (erster Schüler), Eltern mit diesem Kind, Monitor mit erstem Standort; setzt `X-CSRF-Token` als
  Standard-Header des Clients. Eigene Verknüpfungen: `login(client, "lehrer", username="x", teacher_id="ABC")`.
- `as_role(role, **felder) -> TestClient` (eigener Cookie-Speicher, bereits angemeldet) – Demo vorher über `client`
  laden (Fixture-Reihenfolge: `def test_x(client, as_role)`). `new_client()`, `make_user(role, username, password, **felder)`,
  `role_links()`.
- Bootstrap-Admin in Tests: `admin`/`admin12345` (Passwortwechsel-Zwang) – für Tests besser `login(client, "admin")`.

## [Backend-Core] Antworten an Infrastruktur
1. Migrationen: `alembic.ini` im Repo-Root (`script_location = %(here)s/schulmanager/server/migrations`, URL aus
   `SM_DATABASE_URL`), `script.py.mako` liegt im Paket. Zusätzlich `python -m schulmanager.server.migrate`.
   Auto-Upgrade beim App-Start (`SM_AUTO_MIGRATE=1`, Default). Alles getestet mit SQLite **und PostgreSQL 16**.
2. CLI existiert: `python -m schulmanager.server.cli {migrate | create-admin --username U [--password-stdin]
   [--display-name N] [--update] | reset-password --username U [--password-stdin] | unlock --username U |
   disable-2fa --username U | list-users [--role R] | load-demo [--time-limit S] [--classes-per-grade N]
   [--no-accounts] | backup | maintenance}`. Ohne `--password-stdin` wird ein Startpasswort ausgegeben.
3. `/healthz` ohne Auth: 200 `{"status":"ok","db":"ok","version","started","plan_version"}`, 503 bei DB-Fehler.
4. `/metrics` mit euren Namen: `schulmanager_http_requests_total{method,route,status}`,
   `schulmanager_http_request_duration_seconds{method,route}` (Histogram, `route` = Template inkl. `/api/v1`, ungematcht
   `<unmatched>`), `schulmanager_sse_clients`, `schulmanager_jobs_running` (aus `jobs.running_count()`),
   `schulmanager_school_version`, `schulmanager_login_failures_total`, zusätzlich `schulmanager_logins_total{result}`,
   `schulmanager_users{role,active}`, `schulmanager_sessions_active`, `schulmanager_school_versions_stored`,
   `schulmanager_http_requests_in_flight`, `schulmanager_uptime_seconds`, `schulmanager_info{version,env,db}`.
   Optional `SM_METRICS_TOKEN` → `Authorization: Bearer <token>` nötig.
5. Rate-Limit in der App (pro Benutzer 5 Fehlversuche/15 min, pro IP 30/15 min). IP = `request.client.host`
   (uvicorn `--proxy-headers`); alternativ `SM_TRUST_PROXY=1` (+ `SM_PROXY_COUNT`) liest `X-Forwarded-For` selbst.
6. Backups: kein pg_dump nötig. SQLite → `.db` über Backup-API, sonst `.json.gz` (alle Tabellen + Planungsdokument)
   in `SM_BACKUP_DIR` (Default `<SM_DATA_DIR>/backups`), Rotation `SM_BACKUP_KEEP` (30). Optional Auto-Backup
   `SM_AUTO_BACKUP_HOURS` (Default 0 = aus).
7. Weitere Env-Variablen (Defaults): `SM_DATA_DIR` (./data), `SM_BACKUP_DIR`, `SM_BACKUP_KEEP` (30),
   `SM_AUTO_BACKUP_HOURS` (0), `SM_AUTO_MIGRATE` (1), `SM_KEEP_VERSIONS` (300), `SM_LOG_FORMAT` (json in production,
   sonst text), `SM_ACCESS_LOG` (1; JSON-Access-Log `schulmanager.access`, uvicorn-Access-Log bei json aus),
   `SM_SESSION_IDLE_MINUTES` (10080 = 7 Tage, gleitend), `SM_SESSION_MAX_DAYS` (30, absolut),
   `SM_LOGIN_MAX_FAILURES` (5), `SM_LOGIN_MAX_FAILURES_IP` (30), `SM_LOGIN_LOCK_MINUTES` (15), `SM_TRUST_PROXY` (0),
   `SM_PROXY_COUNT` (1), `SM_SCRYPT_N` (32768; Produktion ≥ 16384), `SM_APP_NAME` (Schulmanager, TOTP-Issuer),
   `SM_SSE_PING_SECONDS` (20), `SM_MAINTENANCE_INTERVAL` (3600 s; 0 = aus), `SM_ENABLE_DOCS` (1 → `/api/docs`),
   `SM_METRICS_TOKEN`, `SM_LOAD_DEMO` (0), `SM_DEMO_BACKGROUND` (1 = Demo-Generierung beim Erststart im Hintergrund),
   `SM_SMTP_TLS` (starttls|ssl|none), `SM_OIDC_ISSUER/CLIENT_ID/CLIENT_SECRET/SCOPES/USERNAME_CLAIM/AUTO_CREATE/
   DEFAULT_ROLE/LABEL`. Produktion: Start bricht ab ohne `SM_SECRET_KEY` (≥ 32 Zeichen).

## [Vertretung] Schnittstellen-Details & Status (fertig)
**Dateien:** `schulmanager/substitution.py`, `duties.py`, `exams.py`, `calendar_utils.py`; Tests
`tests/test_substitution.py` (handgebaute Schulen, exakte Erwartungen), `tests/test_substitution_demo.py`
(Demo + Generator, Invarianten, Laufzeit), `tests/test_duties.py`, `tests/test_exams.py` – 66 Tests grün, ruff sauber.
Keine neuen Abhängigkeiten.

**substitution.py** (Signaturen wie §4, additive Erweiterungen):
- `compute_day_plan(school, day, history=None) -> DayPlan` (`day` darf auch ISO-String sein); `DayPlan.to_dict()`,
  `DayPlan.from_dict()`, `DayPlan.substitution_counts() -> {lehrer: n}` (vertretung+betreuung).
- `week_history(school, day)`; `compute_range(school, from, to)` liefert **nur Wochentage < settings.days**
  (Ferientage mit `holiday`, Wochenenden fehlen) und rechnet die Vortage der ersten Woche als Historie mit →
  jeder Tag == `compute_day_plan(s, d, week_history(s, d))` (so macht es auch `features_common.day_plan`).
- `rank_candidates(school, day, lesson_id, period, part=0, history=None)` → alle Lehrkräfte außer der eigenen,
  sortiert (frei zuerst, Score absteigend); Zusatzfeld `current` (aktuell eingeteilt). Gründe deutsch, z. B.
  „Fach M“, „kennt 7a“, „Springstunde (ohnehin im Haus)“, „freigesetzt (…)“, „müsste extra kommen“,
  „belegt: …“, „Wegezeit zwischen Standorten reicht nicht“, „Wochenlimit Vertretungen erreicht“, „Sperrzeit“.
- `teacher_stats(school, from, to, plans=None)` – optional vorhandene DayPlan-Objekte übergeben (Cache).
  Zusatzfelder: `vertretung`, `betreuung`, `mitbetreuung`, `freed`, `moved`, `absent_periods`.
  `substitutions` = vertretung+betreuung+mitbetreuung, `duties` = gehaltene reguläre Aufsichten,
  `supervisions` = übernommene Aufsichtsvertretungen.
- `effective_day(school, plan|plan_dict, kind, ref)` → Zellen `{"period","period_label","time","subject","teacher",
  "room","classes","status","note","lesson_id","part","kind","course_id","original_teacher","original_room",
  "entry_id","exam"}`; **`status` ∈ `normal | geaendert | entfall | neu`**, `kind` = Entry-Art oder `unterricht`
  (bzw. `aufsicht` in der Lehreransicht mit Zusatzfeldern `duty_id`, `break_name`; `period` = `after` der Pause).
  Verlegte Stunde: alte Position `status:"entfall", kind:"verlegung"`, neue Position `status:"neu"`. Lehrkraft-Sicht:
  eigene vertretene Stunden `entfall`, übernommene `neu`. `exam` = Klausurtitel, falls in der Stunde eine Klausur liegt.
- Entry-Zusatzfelder: `course_id`, `part_label`; Klausur: `exam_id`, `exam_part`, `length`, `title`;
  Aufsicht: `duty_id`, `area`, `area_name`, `break_index`, `break_name` (`lesson_id: null`, `period` = `after`).
- `stats`: alle Arten (auch 0) + `entfall_mitte` (Entfälle mit Warnung) + `warnungen`.
- Datenschutz: Abwesenheitsgründe von **Lehrkräften** erscheinen nie in Entries; Gründe von Klassen-Abwesenheiten
  (z. B. „Klassenfahrt“) bzw. TimeRule-Notizen stehen in `note` von `klasse_abwesend`.

**Interpretationen/Entscheidungen:**
- Kursteile gekoppelter Kurse: Rand = Rand aller beteiligten Klassen auf Gruppenebene (parallele Teile zählen nicht
  als belegt). `edge_strategy` gilt auch hier (Oberstufe: LK-Teil am Rand entfällt); in der Mitte:
  Vertretung → `mitbetreuung` (Lehrkraft eines anderen Teils, Gruppe wechselt in deren Raum → `new_room`) →
  Betreuung → Entfall mit Warnung. Verlegungen nur für Ein-Klassen-Ein-Teil-Kurse, nur Einzelstunden.
- Vertretungswahl ganzheitlich per Score (Fach +40, „müsste extra kommen“ −40, Springstunde +20, freigesetzt +30,
  kennt Klasse +15, gleicher Standort, Vertretungen der Woche relativ zum Deputat, Lehrerwunsch `wishes` −8).
  Ist die beste Lehrkraft fachfremd → `betreuung`. `allow_unqualified=False` → nur Qualifizierte (ältere Klassen).
- Unterstufe & Klausuren: Betreuung immer erlaubt (Aufsichtspflicht); als letzter Ausweg werden Vertretungslimits
  ignoriert (Warnung „über Vertretungslimit“), sonst `entfall` mit `warning:true`.
- Override `substitute` mit der eigenen Lehrkraft = `keep`; Override auf eine Duty-ID steuert die Aufsichtsvertretung.
- `duties.generate_duties(school) -> list[Duty]` ersetzt `school.duties` nicht selbst; nicht besetzbare Aufsichten
  kommen mit `teacher=None`. IDs `AU-<area>-<tag>-<pause>-<n>`; `weeks=[]`, wenn A und B gleich besetzt sind.
  `duties.duty_load(school)`, `duties.active_duties(school, week, weekday)` als Hilfen.
- `exams.check_exam` → Liste deutscher Konfliktmeldungen (leer = ok); `exams.exams_for(..., kind)` mit
  `kind ∈ class|teacher|room|student|course|all` → Dicts mit `id, course_id, date, weekday, week_text, start,
  length, period_label, time, title, part, room, classes, subject, subjects, teacher, teachers, label`.
- `calendar_utils`: zusätzlich `as_date`, `holiday_name`, `monday_of`, `period_time`, `period_label`, `break_time`.

**Leistung:** volle Demo (2298 Blöcke, 168 Lehrkräfte) mit 10–25 kranken Lehrkräften: 15–40 ms je Tag
(Test-Grenze 0,5 s). In 50 Zufallsszenarien (10 bzw. 25 Kranke) 0 Entfälle in der Tagesmitte.

**Bekannte Lücken:** Raumkapazität bei Mitbetreuung nicht geprüft; Verlegung verschiebt keine Doppelstunden und
nicht zwischen Tagen; Teilnahme einzelner Schüler an Kursteilen wird beim Rand-Check nur klassenweise betrachtet.

## [Infrastruktur] Abgleich mit Backend-Core (CLI, /metrics, /healthz übernommen)
- Danke – CLI (`python -m schulmanager.server.cli migrate|create-admin|reset-password|load-demo|…`), `/healthz`,
  `/metrics`-Namen passen. Infra nutzt: `scripts/migrate.sh` → `cli migrate`; `scripts/create-admin.sh` → `cli create-admin
  --password-stdin [--update]`; `make demo` → `cli load-demo`; Docker-HEALTHCHECK → `/healthz` (`"status":"ok"`).
- Compose setzt `SM_TRUST_PROXY=1`, `SM_PROXY_COUNT=1` (Caddy überschreibt X-Forwarded-For mit der echten Client-IP;
  nginx-Vorlage ebenso `X-Forwarded-For $remote_addr`), `SM_LOG_FORMAT=json`, `SM_COOKIE_SECURE=1`, read-only Root-FS
  (`/tmp` tmpfs, `/app/data` Volume). Uvicorn läuft mit `--no-access-log` (die App loggt selbst).
- Caddy setzt Security-Header nur als Fallback (`?Header`), die App-eigene CSP (inkl. `/api/docs`) hat Vorrang; HSTS setzt Caddy.
- **Anfragen an Backend-Core:**
  1. `middleware.py` Access-Log schreibt den rohen `path` → `/ical/<token>.ics` landet mit Token im Log. Bitte
     maskieren (z. B. `/ical/***`) oder das Routen-Template loggen. (Caddy-Log maskiert bereits.)
  2. Optional für Grafana/Alarm „Speicher hoch“: `process_resident_memory_bytes`, `process_cpu_seconds_total`,
     `process_open_fds` (Linux: `/proc/self/statm`, `resource.getrusage`, `len(os.listdir('/proc/self/fd'))`).
     Das Dashboard zeigt bis dahin für RSS „No data“, alle anderen Panels nutzen eure vorhandenen Metriken.

## [Backend-Features] Status: fertig – API für Frontend/Lead (verbindlich)
**Dateien:** `server/routes/features_{common,data,planning,timetable,substitutions,exams,announcements,
student_absences,exchange}.py`, `server/notify.py`, `server/jobs.py`, `tests/test_server_features.py`
(26 Tests grün, eigene modulweite Fixtures mit API-Tokens; ruff sauber). Keine neuen Abhängigkeiten.
Alle Pfade unter `/api/v1`, Fehler `{"detail": "..."}` (deutsch), Bodies per Pydantic validiert (422).

**Stammdaten** – `GET /data/{c}` (`?class_id=` für students/courses, `?q=` Suche), `GET /data/{c}/{id}` (neu),
`POST /data/{c}` (201; fehlende `id` wird erzeugt außer teachers/classes/subjects; 409 bei doppelter ID),
`PUT /data/{c}/{id}` (**Merge**: nur geänderte Felder nötig; ID unveränderlich), `DELETE /data/{c}/{id}` →
409 `{"detail":{"message","references":[...]}}` solange Verweise bestehen, `?force=1` entfernt/leert die Verweise
(Kaskade, z. B. Kurs → Stunden/Klausuren/Kurswahlen). Schreibrechte: masterdata.edit (sites, subjects, teachers,
rooms, classes, students, holidays, areas), timetable.edit (curricula, courses, duties), exam.edit (exams, Lehrkraft
nur eigene Kurse). Lesen: students nach Rolle gefiltert (Lehrkraft: eigene Klassen, Schüler/Eltern: eigene), teachers
für Schüler/Eltern/Monitor nur `{id,name,subjects}`, duties nur Personal, curricula nur Personal.
`GET /settings` (Webhook-URLs nur mit settings.edit), `PUT /settings` = **Teil-Update** (weights/policy werden
gemischt; Prüfung: cycle_start Montag, Zeiten HH:MM aufsteigend, Pausen im Raster, Webhook-URL http(s)).

**Planung** – `POST /planning/courses-from-curricula` → `{warnings,courses,before,removed_lessons}`,
`POST /planning/assign-teachers` → `{warnings,assigned,open}`, `GET /planning/report` → `validate_school` +
`capacity_warnings` + `open_parts` + `version`. `POST /planning/generate` `{time_limit?,keep_locked=true,seed=1,
workers=0}` → **202** `{job_id, job}` (409 wenn schon ein Job läuft; `workers` 0 = automatisch/`generate_best_of`,
1 = ein Lauf). `GET /planning/jobs` (Liste), `GET /planning/jobs/{id}` → `{id,status(queued|running|done|failed|
cancelled|applied),progress(0..1),message,params,stats,unplaced,warnings,lessons_count,outdated,error,...}`
(`?lessons=1` liefert den Entwurf mit), `POST /planning/jobs/{id}/cancel` (bzw. `DELETE`), `POST .../apply` →
`{job,lessons,warnings,version}`. SSE `job`-Events nur an Benutzer mit `timetable.generate`. `POST /duties/generate`.

**Stundenplan** – `GET /timetable/{class|teacher|room|student}/{ref}?week=` (Rechte: plans.read_all; Schüler/Eltern
eigene Klasse + eigener Schülerplan; Lehrkraft eigener Plan; Schülerpläne nur eigene Klassen), `GET /timetable/lessons`
(Rohdaten, neu), `GET /timetable/lessons/{id}/options`, `POST .../move` `{day,start}` (409 `{"detail":{"conflicts"}}`),
`POST .../lock` `{locked}` → jeweils die Zelle (`lesson_info`).

**Vertretung** – `GET /substitutions?date=&site=&class_id=&teacher=` → DayPlan + `version`; mit substitution.edit
zusätzlich `absences` (mit Gründen, `ref_name`) und `overrides` des Tages. Lehrkräfte: alles ohne Gründe.
Schüler/Eltern: nur Einträge der eigenen Klasse(n) **und gewählten Kursteile**, ohne `aufsicht`,
`absent_teachers=[]`, `warnings=[]`, `stats` neu gezählt. `GET /substitutions/range?from=&to=` (max 31 Tage, gleiche
Filter), `GET /substitutions/candidates?date=&lesson_id=&period=&part=` (substitution.edit),
`GET /substitutions/stats?from=&to=` → `{from,to,teachers:[...]}` (Lehrkraft sieht nur sich).
`GET /absences?from=(heute)&to=&kind=&ref=` (Personal; Gründe nur substitution.edit bzw. eigene), `POST /absences`
`{kind,ref,date_from,date_to?,periods?,reason}` (201), `PUT /absences/{id}` (neu), `DELETE /absences/{id}`
(Lehrkraft darf eigene, nicht vergangene Abwesenheit zurückziehen). `POST /absences/report-self`
`{date_from,date_to?,periods?,reason="krank"}` → 201 (nur ab heute, max 42 Tage, idempotent → `duplicate:true`;
409 wenn Konto ohne `teacher_id`). Events `change` mit `scope:["absences","substitutions"]` und **`dates`**.
`GET /overrides?date=` bzw. `?from=&to=`, `POST /overrides` `{date,lesson_id,period,part=0,action(substitute|cancel|
keep|room),teacher?,room?,note,all_periods=false}` → ersetzt eine bestehende Entscheidung derselben Stunde/Teil;
`DELETE /overrides/{id}`.

**Persönlich** – `GET /me/today?date=&student_id=` → `{date,weekday,week_no,holiday,kind(teacher|student|
null),ref,plan_entries,cells(effective_day),exams,announcements,version}`; Schüler/Eltern zusätzlich `children:[{id,
name,class_id}]` (Eltern wählen per `student_id`), Personal ohne Lehrkraft `stats`. `GET /me/week?date=` →
`{week_start,week_info,days:[wie today ohne announcements],announcements,version}`.
`GET /monitor?site=&date=&days=2` (monitor.read) → `{site,site_name,school_name,generated_at,version,period_times,
days:[{date,weekday,week_no,holiday,entries(nach Klasse sortiert),absent_classes,stats}],announcements}` –
heute + nächste Schultage, ohne Aufsichten/abwesende Lehrkräfte/Gründe; Mitteilungen nur mit `monitor:true`.

**Klausuren** – `GET /exams?from=(heute)&to=(+8 Wochen)&class_id=&course_id=&teacher=` (Schüler/Eltern: eigene
Kurse) → `{...Exam, classes,label,subject,subjects,teachers,time}`; `POST /exams` / `PUT /exams/{id}` Body Exam +
`force` → bei `check_exam`-Problemen 409 `{"detail":{"conflicts":[...]}}` (`force:true` nur ohne own_courses-Scope);
Antwort enthält `warnings`. `POST /exams/check` → `{ok,warnings,allowed}`. `DELETE /exams/{id}`.

**Mitteilungen** – `GET /announcements?date=` (sichtbar & gültig; `?all=1` mit announcement.post: alle),
`POST` `{title,body,audience(all|staff|classes),audience_roles[],class_ids[],site?,valid_from?,valid_to?,pinned,
priority(normal|wichtig),monitor}` (Lehrkraft: nur `classes` mit eigenen Klassen, kein monitor/pinned),
`PUT/DELETE /announcements/{id}` (Autor oder uneingeschränktes Recht). Felder inkl. `can_delete`, `created_at`.

**Krankmeldungen Schüler** – `GET /student-absences?from=(−30 Tage)&to=&class_id=&student_id=&status=`,
`POST` `{student_id?,date_from,date_to?,periods?,reason,note?}` (Eltern/volljährige Schüler ohne student_id bei
einem Kind), `PATCH /{id}` `{status?,note?}` (nur Personal mit Recht für den Schüler), `DELETE /{id}` (Personal oder
meldende Person solange `gemeldet`). Felder: `student_name,class_id,status,reported_by_name,can_manage,can_delete`.

**Import/Export** (Export: timetable.edit oder masterdata.edit) – `GET /export/untis.zip?from=&to=`,
`GET /export/schulmanager-online.zip?from=&to=&students=1`, `GET /export/csv/{teachers|classes|rooms|subjects|
students|lessons|curricula}` (students nur uneingeschränktes students.read), `GET /export/json` →
`{format:"schulmanager",format_version,version,exported_at,school}`. `POST /import/untis` (multipart `files`
mehrfach oder ZIP, Formfeld `mode=merge|replace`, `?dry_run=1`), `POST /import/csv/{what}` (multipart `file` +
Formfeld `mapping` = JSON, `?dry_run=1`) → Report von `csv_io`, `POST /import/json` (JSON-Body **oder** multipart
`file`; akzeptiert Export-Hülle oder nacktes School-Dict; admin/planer). Importe laufen über `store.mutate`
(Undo möglich), Scope `["all","import"]`.
**iCal** – `GET /ical/{token}.ics?student=&days=21` (ohne Präfix, Token aus `/me/ical-url`; Lehrkraft → eigener
Plan, Schüler/Eltern → Schülerplan; 404 für Konten ohne persönlichen Plan).
**Benachrichtigungen** – `GET /notifications/outbox?status=` + `POST /notifications/outbox/{id}/retry`
(settings.edit/system.admin). Webhook-Event `substitutions.changed` (Payload `integrations.webhooks.payload`,
`data:{date,dates,version,added,changed,removed}`, Header `X-Schulmanager-Signature/-Event/-Delivery/-Timestamp`;
`sent_at` wird bei Retries erneuert, `id` bleibt). E-Mails an betroffene Lehrkräfte (Vertretende, Raum-/Verlegungs-
änderungen; nicht an die abwesende Lehrkraft) an `users.email` bzw. `Teacher.email`, wenn SMTP konfiguriert.
Retry: 30 s · 2^(n−1), max 6 h, nach 8 Versuchen `failed`.

**Technik/Leistung:** Tagespläne LRU-gecacht je `(store.version, digest, datum)` inkl. fairer Wochenhistorie aus
dem Cache (identisch zu `compute_range`); `effective_day` für Schüler je (Klasse, Kurswahl) gecacht. Volle Demo
(2626 Schüler): `/me/today` warm ≈ 4–5 ms, direkt nach einer Planänderung ≈ 13 ms je Anfrage (inkl. Auth).
**Hinweis an Backend-Core (optional):** bitte `SchoolStore.digest` als öffentliche Eigenschaft anbieten – ich lese
derzeit ersatzweise `store._digest` (Cache-Schlüssel, unterscheidet gleiche Versionsnummern verschiedener DBs).

## [Backend-Features] Abschluss-Check
- `tests/test_server_features.py`: 27 Tests grün (u. a. Rollen-Sichtbarkeit, Abwesenheit→Plan+Event mit `dates`,
  Selbst-Krankmeldung, Override, Verschieben mit 409, Generator-Job + Apply + Abbruch, JSON/CSV/Untis-Roundtrip,
  iCal per Token, Mitteilungen, Eltern-Krankmeldung, Webhook-Outbox inkl. Signaturprüfung mit `webhooks.verify`,
  E-Mail-Outbox, Retry/Backoff, Oberstufen-Kursteilfilter). Gesamtsuite: 196 grün.
- E2E mit aktivem Dispatcher (`SM_NOTIFY_DISPATCHER=1`): Änderung → signierter Webhook nach ≈0,2 s; Stopp im Lifespan ok.
- Untis-Import `mode=replace` behält konfigurierte `settings.webhooks`.

## [Integrationen] Schnittstellen, Entscheidungen & Status (fertig)
**Dateien:** `schulmanager/integrations/{__init__,_common,untis_gpu,schulmanager_online,csv_io,ical,webhooks}.py`,
`tests/test_integrations.py` (36 Tests, ~4 s). Nur Standardbibliothek, `ruff check schulmanager/integrations` sauber.

**Signaturen** (§5 eingehalten, nur optionale Keyword-Argumente ergänzt; `plans` überall Liste ODER Dict von
DayPlan-Dicts, auch Objekte mit `to_dict`):
- `untis_gpu.export_zip(school, plans=None, *, encoding="cp1252", include_meta=True, include_reasons=False) -> bytes`,
  `export_files(...) -> {"GPU001.TXT": bytes, …}`, `unit_numbers(school) -> {course_id: Unt-Nr}`,
  `import_files(files, school=None, *, encoding=None, lock=False, replace_lessons=True) -> (school, warnings)`.
  `school=None` → neue Schule, sonst **Merge in place** (gleiches Objekt zurück). Mit GPU001 wird `school.lessons`
  ersetzt (`replace_lessons=False`: nur Stunden der importierten Kurse). `files` darf ZIPs enthalten, Namen
  case-insensitiv/mit Pfad. `ValueError`, wenn keine GPU-Datei dabei ist.
- GPU014-Import → `Absence` (teacher, ID `untis-L-<lehrer>-<datum>`, `periods`) + `Override` (ID
  `untis-<datum>-<lesson>-<stunde>-<teil>`, cancel/substitute/room). Re-Import desselben Tages ersetzt frühere
  `untis-*`. Verlegungen/Aufsichten/Klausuren aus Untis werden nicht übernommen (Sammelwarnung).
- Externe Untis-Unterrichte ohne Schulmanager-Kennung: Kurs-ID `U<Unt-Nr>`, `origin="untis"` (neuer Wert, wird von
  `build_courses_from_curricula` wie „manuell“ behandelt) bzw. Zuordnung zu vorhandenem Kurs mit gleichen Klassen+Fächern.
- `schulmanager_online.export_package(school, plans=None, *, created=None, include_students=True) -> bytes`:
  `LIESMICH.txt` (Anleitung, ehrlich: keine öffentliche API → dateibasiert), `manifest.json`, `untis/GPU*.TXT`,
  `csv/{schueler,lehrer,klassen,raeume,faecher,unterricht}.csv`.
- `csv_io.export_csv(school, what) -> str` **mit führendem `"﻿"`**, `;`, CRLF.
  `import_csv(school, what, text|bytes, mapping=None) -> {"what","rows","created","updated","skipped","errors",
  "warnings","columns","ignored_columns","delimiter","encoding"}`; `mapping` = `{"Spalte": "feld"}` und/oder
  `{"preset": "schild-nrw"|"asv"|"lusd"|"magellan"}` (auch nur Preset-Name als String). **Leere Zellen ändern nichts.**
  Zeilenfehler → `errors` („Zeile N: …“), übrige Zeilen werden importiert. `describe(what)` → Zielfelder + Labels +
  Presets (für einen Mapping-Dialog). Konfession/Religionsunterricht/Religionsabmeldung → `Student.courses`
  `"kurs#teil"` der Religions-/Ethik-Kopplung der Klasse. Helfer: `format_rules`/`parse_rules`
  (TimeRule ↔ „Woche 1: Mi (Notiz) | Fr Std. 6-8“), `religion_category`, `assign_religion`.
- `ical.calendar(school, kind, ref, date_from, date_to, plans=None, *, name=None, now=None, uid_domain="schulmanager",
  include_holidays=True, include_duties=True) -> str`; `ValueError` bei unbekanntem kind/ref, `date_to < date_from`
  oder > 800 Tagen. Semantik wie `substitution.effective_day` (vertretene Lehrkraft: CANCELLED „Vertreten“, Vertreter:
  eigener Termin, Verlegung: alter Platz CANCELLED + neuer Termin „Verlegt“). Lehrkräfte sehen Pausenaufsichten
  (`school.duties` + `aufsicht`-Entries); Klausuren aus `school.exams`. Ferien als ganztägige Termine.
- `webhooks.payload(event, data, *, school=None, sent_at=None, delivery_id=None)` →
  `{"schema","schema_version":1,"id","event","sent_at","school","data"}`; `encode(body) -> bytes` (kanonisch,
  sort_keys); `sign(body, secret) -> "sha256=<hex>"`; `verify(body, secret, signature, *, timestamp=None,
  tolerance=300)`; `headers(body, secret, event)`. Eventnamen `bereich.aktion` (sonst ValueError), `ping` erlaubt.

**Entscheidungen:**
- GPU-Spalten: untis.at ist aus der Umgebung gesperrt → abgeglichen mit der MIT-Bibliothek *enbrea.untis.gpu*
  (Feldindizes + echte Beispielzeilen). Im Modul-Docstring je Datei `[s]`/`[u]` markiert. **Unsicher:** GPU001 Feld 8/9,
  GPU002 Zeilentext 1/2 (Feld 13/39), Text (18), Doppelstunden min/max (28/29), GPU004 Deputat (15), GPU014
  Art-Bitzählung (Bit n = 2^n; enbrea zählt um 1 verschoben, deren Beispielzeilen sprechen für 2^n), GPU014 Feld 22,
  „Stunde“ bei Pausenaufsichten (= vor der Stunde → `after+2`), GPU015 insgesamt.
- Wochenangaben: DIF kennt keine Periodizität → Blöcke nur in ausgewählten Wochen bzw. im Rhythmus als eigene Unt-Nr (Text „… (Woche 1)“, Wst
  anteilig 0.5). Import erkennt „Woche 1“/„Woche 1, 3“ in Text/Zeilentext; solche Unterrichte hängen sich an den
  wöchentlichen Unterricht mit gleichen Klassen/Lehrern/Fächern.
- Verlustfreier Rückimport über Kennung `sm1;c=<kurs>;p=<teil>;h=;d=;cw=;lw=;cy=;o=` in GPU002 Feld 39 (Fach-Meta in
  GPU006 Feld 16), abschaltbar (`include_meta=False`). Export→Import erhält Stundenplan inkl. Block-/Doppelstunden-
  struktur, Wochen und Räumen je Teil, Kopplungen, Kurswahlen (GPU015), Stammdaten soweit in GPU abbildbar
  (nicht: Klassen-Rhythmus/TimeRules, Lehrer-Qualifikationen außerhalb des Unterrichts, Wünsche → dafür JSON-Export).
- Export Windows-1252 mit Transliteration (ğ→g, ı→i); Import erkennt BOM/UTF-8/cp1252 und Trennzeichen `,` `;` Tab.
- **Datenschutz:** Abwesenheitsgründe von Lehrkräften gehen nur mit `include_reasons=True` in GPU014 (Standard aus –
  GPU014 landet oft in Schüler-Apps). iCal enthält keine Abwesenheitsgründe.

**Anfragen (optional):**
- Backend-Features: `GET /import/csv/{what}/fields` → `csv_io.describe(what)` für den Mapping-Dialog. Bitte
  `include_reasons` nicht setzen. Aktuelle Aufrufe in `features_exchange.py`/`notify.py` passen zu meinen Signaturen
  (eure 7 Export/Import/iCal-Tests laufen mit meinen Modulen grün).
- Frontend: CSV-Import mit Preset-Auswahl (schild-nrw, asv, lusd, magellan) + Spaltenzuordnung (Felder aus `describe`),
  Hinweis „leere Zellen ändern nichts“; Untis-Import: Warnungsliste anzeigen.

**Status:** fertig. `python -m pytest -q tests/test_integrations*.py` → 36 passed; ruff sauber. Volle Demo
(2298 Blöcke): GPU-Export 0,1 s, GPU-Import 0,1 s, iCal-Schuljahr einer Lehrkraft 0,3 s, Paket 0,1 s.

## [Lead] Entscheidungen nach Backend-Features-Abschluss
- An Backend-Core: bitte `SchoolStore.digest` als öffentliche Property anbieten (Features nutzt bisher `store._digest`
  als Cache-Schlüssel) und das iCal-Token im Zugriffslog maskieren (`/ical/<token>.ics` → `/ical/***.ics`).
- Entscheidung Lead: Gründe von **Klassen**-Abwesenheiten (z. B. „Klassenfahrt“) dürfen Schüler/Eltern der
  betroffenen Klasse sehen; Gründe von **Lehrkraft**-Abwesenheiten bleiben verborgen. (Lead passt das bei der Integration an.)

## [Backend-Core] Status: fertig – Endpunkte, Entscheidungen, Abweichungen
**Erledigt auf Anfrage:** `store.digest` (öffentliche Property), iCal-Token im Access-Log/Fehlerlog maskiert
(`/ical/***.ics`), Prozessmetriken `process_resident_memory_bytes`, `process_cpu_seconds_total`, `process_open_fds`.
`/auth/me` und Login liefern zusätzlich `user.students: [{id, name, class_id}]` (Kinder bzw. eigener Schüler).

**Dateien:** `schulmanager/server/{app,config,db,db_models,migrate,runtime,bootstrap,security,deps,permissions,accounts,
store,events,audit,backups,maintenance,metrics,middleware,logging_setup,demo_loader,cli}.py`,
`server/migrations/{env.py,script.py.mako,versions/0001_initial.py}`, `server/routes/{auth,users,history,admin,me,events,
system,oidc}.py`, `alembic.ini`, `pyproject.toml` (+ `[project.scripts] schulmanager-admin`, package-data für
`script.py.mako`, pytest-Filter für die httpx/TestClient-Deprecation), `tests/conftest.py`,
`tests/test_server_core.py`, `tests/test_server_core_store.py` (63 Tests grün; +1 PostgreSQL-Test, läuft mit
`SM_TEST_POSTGRES_URL=postgresql://user:pw@host/db` – lokal gegen PostgreSQL 16 grün). Keine neuen Abhängigkeiten.

**Core-Endpunkte (`/api/v1`):**
- Auth: `POST /auth/login` `{username,password,totp?}` → `{user,csrf_token}` + Cookie; `POST /auth/logout`;
  `GET /auth/me`; `GET /auth/config` (öffentlich: `{app_name,env,oidc:{enabled,label,login_url},password_min_length}`);
  `POST /auth/password` `{old_password,new_password}` (beendet andere Sitzungen); `POST /auth/2fa/setup` →
  `{secret,otpauth_url}`; `POST /auth/2fa/enable` `{code}`; `POST /auth/2fa/disable` `{password}`.
  Passwort-/2FA-Änderungen nur mit Sitzung (nicht per API-Token). SSO: `GET /auth/oidc/login?next=`,
  `GET /auth/oidc/callback` (Fehler → Redirect `/login?sso_error=not_configured|state|provider|unknown_user|account_disabled`).
- Benutzer: `GET /users?role=&q=&active=&class_id=&limit=&offset=` (nur verwaltbare Rollen; Schüler mit `class`,
  Eltern mit `student_ids`), `POST /users` (201; ohne `password` → `temp_password`), `GET/PATCH/DELETE /users/{id}`
  (PATCH-Felder: display_name, role, password, must_change_password, teacher_id, student_id, student_ids, site, email,
  adult, active, `totp_enabled:false` = 2FA zurücksetzen), `POST /users/{id}/reset-password` `{disable_2fa?}` →
  `{temp_password,username,display_name}`, `POST /users/bulk` `{role,class_ids?}` → `{created:[{id,username,
  display_name,temp_password,class,role,student_id|teacher_id,student_ids?}], skipped: <Anzahl>}`,
  `GET/PUT /users/{id}/children` (`{student_ids}`; GET zusätzlich `students:[{id,name,class}]`),
  `POST/DELETE /users/{id}/children/{student_id}`, `GET /users/{id}/sessions`, `DELETE /users/{id}/sessions` (alle,
  bei sich selbst außer aktueller), `DELETE /sessions/{id}`, `POST /users/{id}/api-token` `{name?,expires_days?}` →
  `{id,name,prefix,token,...}` (201), `GET /users/{id}/api-tokens`, `DELETE /api-tokens/{id}`, `GET /roles`
  (Matrix, Labels, Scopes, verwaltbare Rollen).
- Eigenes Konto: `GET /me/export` (DSGVO-JSON als Download), `GET /me/ical-url` → `{url}`, `POST /me/ical-url` (neues
  Token), `DELETE /me/ical-url` (deaktivieren).
- Verlauf/Audit: `GET /history?limit=&offset=` → `[{version,created_at,user,user_display_name,user_id,message,scope,
  restored_from,current}]`, `GET /history/{version}` (+ `counts` je Sammlung), `POST /history/{version}/restore`,
  `POST /history/undo` (mehrstufig; 409 wenn nichts mehr da), `GET /audit?limit=&offset=&user=&action=(Präfix)&target=&since=&until=`.
- System (`system.admin`): `GET /admin/system`, `GET/POST /admin/backups`, `GET/DELETE /admin/backups/{name}`,
  `POST /admin/demo` `{time_limit?,accounts=true,classes_per_grade=14}` (synchron, `job`-Events `id:"demo"`),
  `POST /admin/maintenance`. Öffentlich: `GET /version`.
- `GET /events` (SSE): `hello` `{version,user}` sofort, `change`, `job`, `ping` (20 s). Wenn ein Client Ereignisse
  verpasst: `change` mit `{version:null,scope:["all"],resync:true}`.
- Ohne Präfix: `/healthz`, `/metrics`, `/api/docs` + `/api/openapi.json` (abschaltbar `SM_ENABLE_DOCS=0`), SPA aus
  `SM_FRONTEND_DIST` (Fallback `index.html` für alles außer `api/`, `healthz`, `metrics`, `ical/`; `assets/*` mit
  `immutable`-Cache, `index.html` `no-cache`). Unbekannte `/api/*` → 404 JSON.

**Entscheidungen / Abweichungen vom Vertrag:**
- Zusätzliche Spalten: `users.email`, `users.adult` (volljährig → Schüler erhält `student_absence.report`),
  `users.oidc_sub`; `school_versions.restored_from` (für mehrstufiges Undo); Features-Tabellen = Vereinigung aus §6
  und Features-Vorschlag; `notifications_outbox.payload` ist **Text** (statt JSON) auf Wunsch von Features.
- Fehlercodes für Auth als maschinenlesbare `detail`-Strings (siehe oben), sonst deutsche Klartexte.
- Passwortregeln: Schüler ≥ 8, **alle anderen (inkl. Eltern)** ≥ 10 Zeichen, keine Trivialpasswörter, nicht den
  Benutzernamen enthaltend. Startpasswörter: `xxxx-xxxx-xxxx` (ohne 0/o/1/l/i), scrypt mit günstigerem N=2048
  (zufällig, Wechsel erzwungen); Rehash beim Login, wenn Parameter < `SM_SCRYPT_N`.
- Benutzernamen werden normalisiert (klein, ASCII, ä→ae, ß→ss, Leerzeichen → `-`); Eltern-Massenanlage = ein Konto
  je Kind ohne verknüpftes Elternkonto (Geschwister später per `PUT /users/{id}/children` zusammenführen).
- Lehrkräfte: `student_absence.report` mit Scope `own_classes` (Vertrag ohne Einschränkung – konservativ gewählt).
- Undo = Wiederherstellung der Vorgängerversion als **neue** Version (Scope `["all","undo"]`, Restore `["all","restore"]`);
  Undo/Restore ändert nur das Planungsdokument, nicht Konten/Mitteilungen.
- Store: keine neue Version, wenn `fn` nichts geändert hat. Mehrere Worker: Store synchronisiert sich (≤ 2 s), Events
  sind aber prozesslokal → **1 Worker** (wie Infrastruktur).
- `SM_LOAD_DEMO=1`: Demo wird beim Erststart im Hintergrund erzeugt (`SM_DEMO_BACKGROUND=0` = blockierend,
  `SM_DEMO_CLASSES_PER_GRADE` default 14). Server ist sofort erreichbar (zunächst leeres Dokument).
- Dev-Zugangsdaten: Erst-Admin `admin` / `admin12345` (Passwortwechsel-Zwang). Demo-Konten (nach `SM_LOAD_DEMO=1`,
  `POST /admin/demo` oder `cli load-demo`), Passwort für alle **`demo123456`**, in development ohne Wechselzwang:
  `schulleitung`, `planer`, `sekretariat`, `lehrer1`–`lehrer3` (erste drei Lehrkräfte), `schueler1` (Jg. 5),
  `schueler2` (9P), `schueler3` (Oberstufe Q1), `eltern1` (Kinder von schueler1+2), `monitor` (Standort S1).
- Offene Punkte / Hinweise: TOTP-Geheimnisse und iCal-Tokens liegen im Klartext in der DB (Backups schützen!);
  TOTP-Replay-Schutz ist prozesslokal; Lead-Dateien haben 10 ruff-Befunde (E741/E731 in scheduler/timetable/test_core).

## [Frontend] Status: fertig – SPA, Seiten, Annahmen, Tests
**Dateien:** alles unter `frontend/` (Vite 7 + React 19 + TypeScript 5.9 strict + React Router 7, eigenes CSS, einzige
Laufzeit-Abhängigkeit außer React/Router: `qrcode-generator` für den 2FA-QR-Code). `package-lock.json` liegt bei;
`.npmrc` setzt `legacy-peer-deps=true` (npm 10 stolpert sonst beim Neu-Auflösen über optionale vitest-Peers –
`npm ci` mit Lockfile funktioniert so oder so).
- Skripte: `npm run dev` (Port 5173, Proxy `/api` + `/ical` → `SM_BACKEND` bzw. `http://localhost:8000`, SSE geht
  durch), `npm run build` (= `tsc --noEmit` für `src` und `vite.config.ts` + `vite build` → `frontend/dist`),
  `npm run lint` (Typprüfung beider tsconfigs; kein ESLint, um Abhängigkeiten klein zu halten), `npm test`
  (vitest, 31 Tests: Rasteraufbau/Spuren/Doppelstunden, Rechte/Menü/Routing, Datum & Wochenzählung, Vertretungs-Filter/
  Gruppierung, Live-Scope-Abgleich, CSV-Kopf/Mapping, Fehlertexte/409-Konflikte, Monitor-Normalisierung, Virtualisierung).
- Struktur: `src/api/` (`types.ts` Vertragstypen inkl. tatsächlicher Zusatzfelder, `client.ts` fetch + CSRF +
  `ApiError` [401 → Login-Event, `totp_required`, 403 `password_change_required` → Passwortseite, 409 → `conflicts`/
  `references`], `endpoints.ts` alle Endpunkte, `events.ts` gemeinsame SSE-Verbindung mit Backoff-Reconnect,
  Watchdog und Resync nach Wiederverbindung), `src/hooks/` (`useLive(scope)`, `useApi` mit Live-Reload,
  `useCollection` = geteilter Stammdaten-Cache, invalidiert per SSE-Scope), `src/lib/` (reine, getestete Helfer),
  `src/components/` (Layout, Modal/Drawer mit Fokusfalle, Combobox `SearchSelect`/`MultiSelect`, `VirtualTable`,
  `TimetableGrid`, `RuleEditor`, `EntryTable`, `MyDayView`, `QrCode`, `DateNav`), `src/pages/` (lazy geladen).
- Seiten/Routen: `/login` (2FA-Feld bei `totp_required`, SSO-Knopf aus `/auth/config`, `?sso_error=`), `/passwort`
  (Pflichtwechsel), `/` (Schüler/Eltern „Mein Tag“ + Kinderwahl, Lehrkraft heute/morgen + Krankmeldung, Planung/
  Leitung/Sekretariat Kennzahlen + offene Lücken + Qualitätsbericht), `/stundenplan[/:kind/:ref]?woche=` (Raster/Liste,
  Wochenangaben, Fächerfarben, Doppelstunden, Kopplungen, Sperrzeiten schraffiert, DnD mit `options` grün/rot, 409-Konflikte,
  Fixieren, Verschieben per Tastatur), `/vertretung?datum=&standort=&klasse=&lehrer=` (Live, Arten farbig + Kürzel,
  Abwesenheit erfassen/bearbeiten/löschen, Kandidaten-Drawer → Override substitute/cancel/keep/room, zurücknehmen,
  Wochenstatistik), `/planung/{stundentafeln|kurse|generator|bericht|regeln|zeitraster}`, `/stammdaten/{teachers|
  classes|rooms|subjects|sites|holidays|students|areas}` (Rhythmus-Regel-Editor mit Wochenvorschau, Lehrer-Sperrzeiten
  + Wünsche, Löschen mit 409-Verweisen → `?force=1`), `/klausuren`, `/aufsichten`, `/mitteilungen`, `/krankmeldungen`,
  `/benutzer` (Massenanlage → `/druck/zugangsbriefe`, Reset, Sitzungen, API-Tokens, Kinder), `/daten` (Untis/SMO/CSV/
  JSON-Export, Untis-/CSV-/JSON-Import jeweils mit Probelauf `dry_run`, CSV-Spaltenzuordnung + Presets),
  `/verlauf` (Undo, Wiederherstellen, Audit), `/profil` (Passwort, 2FA mit QR + otpauth-Text, iCal-Abo inkl. Neu-Link,
  Geräte, DSGVO-Export), `/system`, `/monitor/:site` (Vollbild, Uhr, heute+nächster Schultag, Autoscroll, Ticker,
  Live + 2-min-Polling), Druck: `/druck/stundenplan/:kind/:ref`, `/druck/vertretung` (Print-CSS, A4).
- Barrierearm: Skip-Link, Fokus-Ring, ARIA-Tabs/Combobox/Dialog, Arten nie nur über Farbe (Kurzzeichen), Kontrast-
  Textfarbe auf Fächerfarben, `prefers-reduced-motion` (Monitor blättert seitenweise), hell/dunkel per System +
  Umschalter (localStorage `sm-theme`). Handy: Liste statt Raster, kein horizontales Scrollen (Playwright geprüft).
- Leistung: 2626 Schüler / ~5000 Konten in `VirtualTable` (misst Zeilenhöhe), Combobox zeigt max. 60 Treffer,
  Stammdaten werden einmal geladen und geteilt; Start-Bundle ≈ 100 kB gzip, Seiten als eigene Chunks.

**Annahmen/Abweichungen (alle gegen die laufende API geprüft):** `timetable_view.periods` als `{index,label,time}`
oder Strings; `effective_day`-Zellen (`status`, `original_teacher/_room`, `exam`); Job-Ergebnis direkt am Job;
`/substitutions/stats` → `{teachers:[…]}`; Listen-Antworten werden tolerant gelesen (`[]` oder `{items}`); CSV-Zielfelder
sind aus `integrations/csv_io.describe()` nach `frontend/src/lib/csvFields.ts` übernommen (bei Änderungen dort bitte
hier notieren – ein `GET /import/csv/{what}/fields` würde das überflüssig machen).

**Test (Playwright, Chromium aus /opt/pw-browsers) gegen `uvicorn` mit `SM_LOAD_DEMO=1` und eigener SQLite im
Scratchpad:** Rundgang Planer/Lehrkraft/Eltern (Handy 390 px)/Schüler (dunkel)/Monitor (1920×1080)/Admin über alle
Seiten inkl. Generator-Lauf + Übernehmen, Massenanlage + Zugangsbriefe (Print-Emulation), 2FA-Einrichtung; interaktiv:
Abwesenheit per API in Sitzung B → Vertretungsplan in Sitzung A aktualisiert sich live (8 → 11 Einträge), Override
setzen/zurücknehmen, Fixieren/Lösen, Verschieben per Tastatur, Undo. Keine JS-Fehler, keine unerwarteten 4xx/5xx
(einziger 4xx: erwartetes 401 von `/auth/me` vor dem Login).

**Hinweise an andere Agenten (optional):**
- Backend-Core: `GET /auth/me` ohne Sitzung loggt im Browser einen 401-Konsolenfehler; ein `200 {"user":null}` (z. B.
  `?optional=1`) wäre kosmetisch schöner – Frontend kommt mit beidem zurecht.
- Vertretung/Backend-Features: Auf dem öffentlichen Monitor steht im Hinweis „Vertretung für Frau Arnold“ – also der
  Name der abwesenden Lehrkraft (kein Grund). Falls das für Monitore nicht gewünscht ist, bitte in `filter_plan(...,
  public=True)` kürzen; das Frontend zeigt `note` unverändert an.
- Infrastruktur: Docker/CI wie notiert (`npm ci && npm run build`, `npm test`, `npm run typecheck`) passt; Node ≥ 20.

## [Infrastruktur] Status: fertig
**Dateien:** `Dockerfile` (Stages frontend → pydeps → dev → source → runtime; non-root UID 10001, Healthcheck
`/healthz`, optional `--secret id=ca_bundle` für TLS-inspizierende Proxys), `.dockerignore` (Whitelist),
`docker-compose.yml` (app, db, caddy, backup; Profile `monitoring` = Prometheus+Grafana, `uptime` = Uptime-Kuma),
`docker-compose.sqlite.yml` (ohne Postgres, per `extends`), `docker-compose.dev.yml` (uvicorn --reload + Vite,
Profile `postgres`, `mail`=Mailpit), `deploy/{Caddyfile, caddy/(Dockerfile mit Rate-Limit-Plugin, conf.d/), nginx/,
systemd/ (App + Backup-Timer), backup/ (Sidecar-Image + Zeitsteuerung), docker/entrypoint.sh, prometheus/
(scrape + alerts), grafana/ (Datenquelle, Dashboard, Alarme)}`, `scripts/{backup,restore,migrate,create-admin,
healthcheck,dev}.sh`, `.env.example`, `Makefile`, `.github/{workflows/ci.yml, codeql.yml, release.yml,
dependabot.yml}`, `.editorconfig`, `.pre-commit-config.yaml`, `docs/BETRIEB.md`, `docs/SICHERHEIT.md`.

**Validiert (lokal, Docker 29):** Image gebaut, Container mit SQLite read-only/cap_drop ALL → healthy nach ~8 s,
SPA/Login/SSE/CLI ok; kompletter Compose-Stack (Postgres+Caddy `localhost`+Backup+Monitoring) healthy, HTTPS,
Security-Header, zstd, SSE ungepuffert, `/metrics` extern 404, Log-Maskierung (iCal, IP), Prometheus scrapt
`up=1`, Grafana-Dashboard + 3 Alarmregeln provisioniert; Backup→Restore→Re-Backup→Restore gegen PostgreSQL 16
(inkl. kaputtem Dump → DB unverändert, Sicherheits-Backup `vor-restore`), `restore.sh --compose` Ende-zu-Ende,
SQLite-Backup/Restore inkl. GPG, Rotation 14/8/12; SQLite-Variante mit Demo (2626 Schüler, App-RSS ≈ 85 MB);
Dev-Stack (Vite-Proxy → api) und `scripts/dev.sh`; nginx-Vorlage live (Rate-Limit 429, `/metrics` 403, SSE);
Caddy-Rate-Limit-Plugin gebaut + Snippet live (429 nach 10/min); shellcheck, actionlint, promtool, caddy
validate, `docker compose config` (4 Varianten), systemd-analyze, pre-commit validate-config; Testsuite im
Dev-Image: 203 passed, 1 skipped; Postgres-Test (`SM_TEST_POSTGRES_URL`) grün.
**Nicht validiert:** Backup-Sidecar-Image selbst (Alpine-Paketquellen in der Sandbox gesperrt – Skripte im
`postgres:16-alpine`-Basisimage getestet), echtes Let's Encrypt, Release-Workflow/GHCR-Push, Uptime-Kuma-UI.

**Anfragen an Lead:**
- `.gitignore` ergänzen: `app.env`, `.env.dev`, `deploy/prometheus/metrics_token` (lokale Geheimnisse).
- `scripts/dev.sh` ist jetzt ausführbar (Modus 100755 mitcommitten).
- README: Abschnitt „Installation/Betrieb“ mit Verweis auf `docs/BETRIEB.md`, `docs/SICHERHEIT.md`, `make help`,
  `make dev` (Login admin / schulmanager-dev), `make up`.
**Optional an Backend-Core:** `HEAD /` und `HEAD /healthz` liefern 405 (manche Monitore nutzen HEAD);
`SM_REQUIRE_2FA_ROLES` (z. B. `admin,schulleitung,planer,sekretariat`) zur technischen Durchsetzung von 2FA –
SICHERHEIT.md fordert 2FA derzeit organisatorisch (Kontrolle via `schulmanager-admin list-users`).

## [Lead] Abschluss-Integration
- Alle sechs Agenten fertig. Lead-Integration: Klassen-Abwesenheitsgründe für Schüler sichtbar (Lehrkraft-Gründe nicht),
  `GET /import/csv/{what}/fields`, Monitor-Standortfilter für abwesende Klassen, doppelte Verlegungshinweise entfernt,
  `SM_REQUIRE_2FA_ROLES` (Backend `403 totp_setup_required` + Frontend-Pflichtseite `/zwei-faktor`), `HEAD /healthz`,
  TOTP-Replay-Schlüssel enthält Secret-Fingerprint, `.gitignore`-Ergänzungen.
- Verifikation: 206 Python-Tests grün (1 übersprungen: Postgres ohne DB), ruff sauber, Frontend tsc + 31 vitest + Build,
  Playwright-Rundgang (Live-Update 0 → 14 Einträge, keine JS-/5xx-Fehler), Docker-Image gebaut + Produktionscontainer healthy.

## [Lead] Start Erweiterung 2
- Vertrag: `docs/ARCHITECTURE.md` §9. Modell + Rechtematrix bereits angepasst (siehe §9.1), alle 206 Tests grün.
- Ablauf: Basis + Lehrer parallel → danach Kursräume, Postfach, Schüler parallel → Integration → Review.
- Notizen bitte nur per Shell anhängen (`cat >> docs/AGENT_NOTES.md <<'X'`), nicht per Editor – parallele Schreiber.
- Frontend-Prüfung ohne Kollision: `cd frontend && npx tsc --noEmit -p tsconfig.json` und `npx vitest run`; Build nur mit
  eigenem Ausgabeordner (`npx vite build --outDir <scratchpad>`). Typfehler in fremden, gerade entstehenden Dateien ignorieren.

## [Lehrer] Start Erweiterung 2 (§9.3) – Plan, Schnittstellen, Verhaltensänderungen
**Dateien (nur diese):** `schulmanager/teacher_profile.py` (neu, reine Logik), `server/feature_models/teacher.py`,
`server/migrations/versions/0003_teacher.py`, `server/routes/features_teacher_profile.py`, `planning.py`, `demo.py`,
`server/jobs.py`, `routes/features_{planning,common,timetable,substitutions,exams,announcements,data,exchange,student_absences}.py`
(Lehrer-Scope), `routes/me.py` (nur Lehrer-Teil), `tests/test_teacher_{profile,scope}.py`, Frontend `src/features/teacher/**`
+ eigene Seiten/Komponenten laut Auftrag.
**Endpunkte (geplant, `/api/v1`):**
- `GET /me/teacher-profile` (profile.teacher_self, Konto mit teacher_id – sonst 409) → `{teacher_id,name,mode,profile:{subjects,
  preferred_classes,max_hours,time_windows,wishes},load,pending,requests,availability,conflicts,options}`;
  `POST /me/teacher-profile/preview` (nur Vorschau), `PUT /me/teacher-profile` (+`note`) → approval: Antrag `offen`
  (ein offener Antrag je Lehrkraft, erneutes PUT aktualisiert ihn) / direct: sofort übernommen; `DELETE /me/teacher-profile/request`
  (eigenen offenen Antrag zurückziehen → Status `zurueckgezogen`).
- `GET /teacher-requests?status=&teacher_id=`, `GET /teacher-requests/{id}`, `POST /teacher-requests/{id}/approve|reject`
  `{comment}` (teacher_requests.review), `POST /teacher-profiles/{teacher_id}/preview` (Stammdaten-Editor, masterdata.edit|review).
- `POST /planning/replan-teacher/{teacher_id}` `{time_limit?,seed?,scope:"teacher"|"classes"}` (timetable.generate) → 202
  `{job_id,job}`; Job `kind:"replan_teacher"`, Übernehmen wie bisher über `POST /planning/jobs/{id}/apply` (ersetzt nur die
  Stunden der freigegebenen Kurse, unveränderte Stunden behalten ihre IDs).
- Live: `change` mit `scope:["teacher_requests"]` (an Prüfende per permission, an die Lehrkraft per user_ids).
**Entscheidungen:** Zeitfenster = Verfügbarkeit („Tage ohne Fenster = nicht verfügbar“, leere Liste = ganztägig). Freitext
(`note`, `review_comment`) wird mit `crypto.encrypt_text` verschlüsselt gespeichert (Spalten `note_enc`, `review_comment_enc`).
`PUT /settings` akzeptiert jetzt auch `period_minutes`, `teacher_self_service`, `sick_note_after_days`,
`messaging_students_to_students`, `messaging_retention_days`, `weights.teacher_wish` (bisher 422 beim Speichern aus der UI!) und
rechnet bei Rasteränderungen die Zeitfenster-Sperrzeiten neu. `PUT /data/teachers/{id}` mit `time_windows` erzeugt die Sperrzeiten.
**Lehrer-Scope (Verhaltensänderung, bricht 3 alte Assertions in `tests/test_server_features.py`, die nicht mir gehören):**
Lehrkräfte sehen fremde Klassenpläne nicht mehr (`test_timetable_visibility`: `lehrer_b` → `/timetable/class/5a` jetzt **403**),
im Vertretungsplan nur Einträge eigener Klassen + eigene; `absent_teachers` nur noch Lehrkräfte aus sichtbaren Einträgen;
`GET /absences` nur eigene Abwesenheiten + Klassenabwesenheiten eigener Klassen (`test_reason_privacy_and_pupil_filter`:
`assert c.ids["teacher_a"] in colleague.json()["absent_teachers"]` und `lst = ...; assert lst and ...` passen dann nicht mehr).
→ Anfrage an Integration: diese Assertions an §9.3 anpassen (Details in meiner Abschlussnotiz).

## [Basis] Start Erweiterung 2 (§9.2) – Plan, Schnittstellen-Details, frühe Anfrage
**Dateien (nur diese):** `server/{crypto,files}.py`, `server/feature_models/files.py`, `migrations/versions/0002_files.py`,
`server/routes/files.py`, `server/config.py` (nur neue Felder/Validierung), `server/maintenance.py`/`server/cli.py`
(Ergänzungen), `pyproject.toml` (`cryptography`), `.env.example`, `docker-compose.yml` (Profil `antivirus` + Env),
`.github/workflows/ci.yml` (Env), `docs/{SICHERHEIT,BETRIEB}.md` (neue Abschnitte), `tests/test_files_crypto.py`;
Frontend `src/features/{registry.ts,registry.test.ts,README.md}`, `App.tsx`, `lib/permissions.ts`(+Test), `pages/DashboardPage.tsx`,
`components/{Layout,FileUpload,FileList}.tsx`, `api/files.ts`.
**crypto (Signaturen wie §9.2, additiv):** Fehler `crypto.CryptoError` (Basis, `ValueError`), `InvalidToken` (manipuliert/falsches
AAD/kaputt), `UnknownKeyError` (Key-ID nicht im Schlüsselring). Zusätzlich `key_id_of(token)`, `is_token(value)`,
`register_rewrap(name, fn(db)->int)`, `rewrap_all(db)`, Stream-Format für Dateien (blockweise AES-GCM). Text-Token = ASCII
`"SM1." + base64url(…)` → Spalten bitte `Text` (Länge ≈ 1,4 × Klartext + ~120 Zeichen).
**Empfehlung an alle Feature-Agenten:** AAD immer mit Tabellen-/Feldbezug + ID, z. B. `encrypt_text(body, f"messages.body:{msg.id}")`
(ID vorher per `db.flush()` erzeugen). Für die Schlüsselrotation bitte je verschlüsselter Spalte
`crypto.register_rewrap("messages.body_enc", fn)` registrieren (im `feature_models`-Modul, dann lädt die CLI es sicher mit) –
`fn(db)` ruft für jede Zeile `crypto.rewrap(token)` auf (AAD wird dafür NICHT gebraucht) und gibt die Anzahl geänderter Zeilen zurück.
**⚠ Frühe Anfrage an Backend-Core/Integration (blockiert sonst 1 fremden Test):** Produktion startet ohne `SM_ENCRYPTION_KEYS`
nicht mehr (Vertrag §9.2). Dadurch schlägt `tests/test_server_core_store.py::test_production_requires_secret` fehl (erwartet
Start mit nur `SM_SECRET_KEY`). Bitte in `tests/conftest.py::_test_env` ergänzen:
`"SM_ENCRYPTION_KEYS": "test:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="` (fester Test-Schlüssel, 32 Byte). Bis dahin ist
dieser eine Fehlschlag erwartet – andere Agenten bitte nicht irritieren lassen. Ebenso `Makefile` (`lint-shell`: Compose-Prüfung)
um `SM_ENCRYPTION_KEYS=x` ergänzen, weil `docker-compose.yml` den Schlüssel jetzt wie `SM_SECRET_KEY` per `:?` verlangt.

## [Basis] Zwischenstand Backend (crypto + Dateien fertig, Frontend folgt)
- Backend-API steht und ist getestet (`tests/test_files_crypto.py`, 64 Tests grün). Details/Signaturen in meiner Abschlussnotiz;
  Kurzfassung für Feature-Agenten: `from schulmanager.server import files, crypto` – `files.store_bytes`, `read_file`,
  `attach`/`attach_many`, `detach`, `delete`/`delete_for_ref`, `register_access_check`, `register_purpose`, `file_info`/`files_info`,
  `require_readable`, `stream_response`/`file_response`, `audit_download`, `duplicate`. Fehler = `files.FileError` (HTTPException,
  `detail={"code","message"}`) → einfach weiterwerfen.
- Erwartete fremde Testanpassungen durch neue Migrationen: `tests/test_server_core_store.py::test_admin_system` prüft
  `db_revision == "0001_initial"` – mit `0002_files` (+ weiteren Köpfen) ist das jetzt z. B. `"0002_files,0003_teacher"`.
  Bitte (Integration) auf „enthält 0002_files“ bzw. `migrate.head_revision()` umstellen.
- Anfrage an Backend-Core/Integration (`app.py`): Die globale `GZipMiddleware` komprimiert auch Datei-Downloads
  (`/api/v1/files/…`: PDFs, Bilder, Videos, ZIP – schon komprimiert, kostet nur CPU, entfernt `Content-Length` bei Streams).
  Vorschlag: Unterklasse/Wrapper, die für Pfade `/api/v1/files/` (und `Content-Type` image/*, video/*, audio/*, application/pdf,
  application/zip) den `IdentityResponder` nimmt. Funktional korrekt ist es auch ohne (getestet).
- Fremde Fehlschläge im Gesamtlauf (nicht von Basis): `test_integrations.py::test_gpu_roundtrip_*`, `test_csv_roundtrip[teachers]`,
  `test_substitution_demo.py::test_rank_candidates_on_demo` (vermutlich Demo-Änderung „ABK“/Abendunterricht des Lehrer-Agenten),
  `test_server_features.py::test_timetable_visibility`/`test_reason_privacy_and_pupil_filter` (Lehrer-Scope, angekündigt).

## [Lehrer] Zwischenstand Backend + Anfragen an Integration (fremde Tests)
- Backend §9.3 steht: `teacher_profile.py`, `features_teacher_profile.py`, `feature_models/teacher.py`, `0003_teacher`,
  Replan-Job (`jobs.py`: `kind="replan_teacher"`, `prepare_replan`/`merge_replan`), Lehrer-Scope in allen Feature-Routen,
  Demo (12 Stunden: + 16:50/17:40, Abendklasse `ABK` „13 Abendkurs (Erwachsenenbildung)“, VES nur ab 16:00, SPT/ZEH ab 10:00,
  lehrer1 mit `preferred_classes`). `tests/test_teacher_profile.py` (22) + `tests/test_teacher_scope.py` (6) grün;
  `test_core.py`, `test_substitution*.py` grün.
- Neu für Frontend/andere: `GET /timetable/allowed` → `{all, kinds, classes|null, teachers|null, rooms|null, students|null}`
  (erlaubte Planauswahl je Benutzer); Helfer in `features_common`: `reads_all_plans(user)`, `is_scoped_teacher(user)`,
  `plan_class_ids`, `plan_course_ids`, `teacher_entry_filter` – gern für Kursräume/Postfach nutzen.
- **Anfragen an Integration (fremde Tests, durch Vertrag §9.1/§9.3 bedingt):**
  1. `tests/test_server_features.py::test_timetable_visibility`: `lehrer_b` → `/timetable/class/5a` jetzt **403** (statt 200).
  2. `tests/test_server_features.py::test_reason_privacy_and_pupil_filter`: Lehrkraft-Kollegin sieht `teacher_a` nur noch in
     `absent_teachers`, wenn dessen Einträge sie betreffen → Zeile `assert c.ids["teacher_a"] in colleague.json()["absent_teachers"]`
     ersetzen durch `assert set(colleague.json()["absent_teachers"]) <= {x for e in colleague.json()["entries"] for x in
     (e.get("teacher"), e.get("substitute")) if x} | {c.ids["teacher_b"]}`; `lst = c.get("lehrer_b", "/absences…")`: Liste enthält
     nur noch eigene/Klassen-Abwesenheiten → `assert all(a["reason"] == "" for a in lst)` reicht (ohne `lst and`).
  3. `tests/test_server_core_store.py::test_admin_system`: `db_revision == "0001_initial"` → mit neuen Migrationen
     (`0002_files`, `0003_teacher`, …) z. B. `== migrate.head_revision()` prüfen.
  4. `tests/test_integrations.py::test_gpu_roundtrip_new_school` + `test_gpu_roundtrip_utf8_and_zip_input`: Demo hat jetzt
     12 Stunden (Abendunterricht) – GPU kennt keine Uhrzeiten, Import in eine **neue** Schule warnt „Unterrichtszeiten
     (period_times) unvollständig“. Vorschlag `untis_gpu`: bei neuer Schule fehlende Zeiten fortschreiben (letzte Zeit +
     `period_minutes` + 5 min) ohne Warnung – oder der Test erlaubt genau diese Warnung.
  5. `tests/test_integrations.py::test_csv_roundtrip[teachers]`: CSV kennt `preferred_classes`/`time_windows` (neu in §9.1,
     Demo nutzt sie jetzt) nicht → Vorschlag `csv_io` Lehrkräfte: Spalten „Wunschklassen“ (kommagetrennt) und „Zeitfenster“
     (z. B. `teacher_profile.describe_windows`-Format „Mo–Fr 10:00–18:30; Woche 2: Mo–Do 10:00–17:00“ oder JSON) und nach dem
     Import `teacher_profile.apply_windows(t, settings)` aufrufen (erzeugt die Sperrzeiten; vorhandene „Zeitfenster…“-Regeln
     aus der Sperrzeiten-Spalte werden dabei ersetzt).

## [Lehrer] Fortsetzung – Zusatzaufgabe erledigt (fremde Tests grün)
- `tests/test_server_features.py`: 3 Zeilen in `test_timetable_visibility`/`test_reason_privacy_and_pupil_filter` an §9.3
  angepasst (lehrer_b → fremder Klassenplan 403; `absent_teachers` ⊆ sichtbare Einträge; `/absences` ohne fremde
  Lehrkraft-Abwesenheiten). Zusätzlich `features_timetable.check_view_access`: unbekannte Klasse/Lehrkraft/Raum → **404**
  vor der Scope-Prüfung (Kürzel sind nicht geheim); unbekannte/fremde Schüler-IDs bleiben **403** (keine ID-Erkundung).
- `integrations/untis_gpu.py`: Import in **neue** Schule schreibt fehlende `period_times` fort (letzte Zeit + `period_minutes`
  + 5 min → Demo 16:50/17:40), keine Warnung mehr; Merge in bestehende Schule warnt weiterhin.
- `integrations/csv_io.py`: Lehrkräfte-Spalten **„Wunschklassen“** (`preferred_classes`, kommagetrennt) und **„Zeitfenster“**
  (`time_windows`, Format `Mo-Fr 10:00-18:30 | Woche 2: Mi 08:00-12:00`; Import versteht auch `;`, `–`, „bis“, „8.00 Uhr“,
  `ganztägig` = Fenster löschen). Neue Helfer `csv_io.format_windows`/`parse_windows`. Fenster werden vor jeder Änderung
  geprüft (`teacher_profile.normalize_windows` → Zeilenfehler), danach `apply_windows` (ersetzt nur „Zeitfenster…“-Sperrzeiten).
  Neue Tests in `tests/test_integrations.py` (Spalten/Format/Fehler, GPU-Zeiten).
- **Anfrage an Integration (Frontend, geteilte Datei):** `frontend/src/lib/csvFields.ts` → `teachers` um
  `{ key: "preferred_classes", label: "Wunschklassen", aliases: ["wunschklassen","bevorzugteklassen","hauptklassen","stammklassen"] }`
  und `{ key: "time_windows", label: "Zeitfenster", aliases: ["zeitfenster","arbeitszeiten","arbeitszeit","verfuegbarkeit","unterrichtszeiten"] }`
  ergänzen (automatische Spaltenerkennung funktioniert schon serverseitig; nur der Mapping-Dialog bietet die Felder sonst nicht an).
- Verbleibend rot in der Gesamtsuite (nicht von mir): `test_server_core_store.py::test_admin_system` (Revision) und
  `::test_production_requires_secret` (SM_ENCRYPTION_KEYS in conftest) – siehe Basis-Notiz.

## [Basis] Frontend-Registry: verbindliche Details (früh, für Lehrer-Agent und Feature-Agenten)
- **Importzyklus beachten:** Vite stellt die Glob-Importe an den Anfang von `features/registry.ts` – `module.tsx` wird
  ausgewertet, BEVOR der Rest der Registry läuft. Deshalb in `module.tsx`/Feature-Code: Typen nur per `import type`;
  zur Ladezeit sicher sind nur die Funktionsdeklarationen `defineFeature`, `setBadge`, `getBadge`, `badgeStore`.
  `badges` (Objekt) bleibt als Komfort-Alias, aber **nur in Funktionen/Effekten** benutzen, nie auf Modulebene.
- **Badges:** Menüeintrag `badge: () => getBadge('lehrer.antraege')`, setzen in einer `background`-Komponente
  (`useEffect` → `setBadge(key, n)`, `null`/0 entfernt), lesen in Komponenten `useBadge(key)`. Layout zeichnet
  bei jeder Änderung neu; `badgeLabel?: (n) => string` für Bildschirmleser (Standard „n neu“).
- **Rechte von Feature-Routen:** Route MIT eigenen Regeln (`anyOf`/`roles`/`notRoles`) → NUR diese gelten (auch im
  Guard über `canAccessPath`), z. B. `/planung/antraege` mit `anyOf: ['teacher_requests.review']` ist für Prüfende
  ohne `timetable.generate` erreichbar. Route OHNE eigene Regeln → Regeln des Menüeintrags mit längstem Präfix.
  Kernpfade (`/`, `/planung`, `/stundenplan`, …) selbst sind gesperrt, Unterpfade erlaubt. Optional `title` (Kopfzeile),
  `layout: false` (ohne App-Rahmen).

## [Lehrer] Status: fertig – §9.3 vollständig (Backend, Frontend, Browsertest)
**Backend seit dem Zwischenstand**
- `server/jobs.py` – **Fix Neuplanung:** Der Generator verteilt die Räume fixierter Stunden beim Vorbelegen neu
  (`scheduler._preplace_locked` → `_assign_rooms`, erster freier Raum des Typs). Mit der vollen Demo gerieten so 49 fremde
  Stunden an den anderen Standort, scheiterten an der Wegezeit („kollidiert und wurde verworfen“), 52 Kurse änderten sich
  und die Übernahme brach mit 409 „neue Konflikte“ ab. Jetzt wird jede fremde Stunde in der Generator-Eingabe zu einem
  Ein-Stunden-Hilfskurs `<kurs>@fix:<stunde>` mit ihren bisherigen Räumen als festen Räumen (`jobs.PIN_SEP`,
  `_pin_foreign_lessons`); `merge_replan` übernimmt nur die freien Kurse, alle anderen Stunden kommen 1:1 aus dem Ausgangsplan,
  neu gelegte Stunden, die doch kollidieren würden, entfallen (`dropped` → unverplant, Hinweis). Volle Demo (lehrer1 „ab 10:00“):
  8 Kurse, 17 Blöcke verlegt, 0 unverplant, 0 Konflikte, 0 Stunden außerhalb der Zeitfenster, alle 2288 fremden Stunden unverändert.
  Job-Statistik `changed_courses` = tatsächlich geänderte Kurse.
- `features_exams.py`: `GET /exams` liefert je Klausur `can_edit` (Lehrkräfte: nur eigene Kurse → Knöpfe im Frontend).
- `features_timetable.py`: unbekannte Klasse/Lehrkraft/Raum → 404 vor der Scope-Prüfung; unbekannte Schüler-ID → 403 wie fremde.
- Tests: `tests/test_teacher_profile.py` (+ Pinning/Merge-Test, jetzt 23), `tests/test_teacher_scope.py` (+ `can_edit`, 404/403).

**Frontend `src/features/teacher/` (Modul-ID `lehrkraft`, Registry-Format §9.2)**
- `module.tsx`: Routen `/lehrkraft/profil` (`profile.teacher_self`) und `/planung/antraege` (`teacher_requests.review`, eigene
  Regeln → auch Schulleitung ohne Generator-Recht), Menü „Profil als Lehrkraft“ (Konto) und „Anträge von Lehrkräften“ (Planung,
  Badge = offene Anträge über `background: RequestsBadge`, Schlüssel `lehrkraft.antraege`), Kacheln `profil`/`antraege` (lazy).
- Dateien: `api.ts`, `types.ts`, `windows.ts`, `scope.ts` (Lehrer-Scope rein), `replan.ts`, `hooks.ts` (`useAllowedRefs`),
  `components.tsx`, `TeacherFields.tsx` (Stammdaten-Felder), `ReplanPanel.tsx`, `TeacherProfilePage.tsx`, `TeacherRequestsPage.tsx`,
  `widgets.tsx`, `badge.tsx`, `teacher.css`, `teacher.test.ts` (11 vitest-Tests).
- Antragsseite: Liste/Detail (Handy: Status als Auswahlfeld), Vergleich alt/neu, Konflikte, Verfügbarkeitsraster, Kommentar,
  Genehmigen/Ablehnen (Live-Event an die Lehrkraft), danach „Stundenplan für diese Lehrkraft neu planen“ (nur mit
  `timetable.generate`, erst nach Genehmigung): Rechenzeit, Umfang (Lehrkraft/Klassen), Fortschritt live, Änderungsliste, Übernehmen.
  Zusätzlich „beliebige Lehrkraft neu planen“ (`?lehrkraft=` vorbelegt, z. B. aus dem Stammdaten-Editor).
- Seiten mit Lehrer-Scope: `TimetablePage` (Ansichten/Auswahl über `GET /timetable/allowed`, eigener Lehrerplan ohne Auswahl,
  verständliche 403-Seite mit Links auf eigene Pläne, Standardplan nur für die passende Ansicht), `SubstitutionsPage` (Klassenfilter
  nur eigene Klassen, „nur meine“ statt Lehrerliste, Hinweis), `ExamsPage` (`can_edit`), `AnnouncementsPage` (Lehrkraft: nur
  „bestimmte Klassen“, kein Anheften), `DutiesPage` (Lehrkraft: eigene Aufsichten als Liste statt Gesamtplan mit falschen
  „offen“-Zahlen), `MasterDataPage` (Wunschklassen, Zeitfenster-Editor + Rastervorschau + Server-Konflikte, Sperrzeiten getrennt
  manuell/aus Zeitfenstern, Deep-Link `/stammdaten/teachers?lehrkraft=KÜRZEL`), `planning/SettingsPanels` (Lehrer-Selbstverwaltung
  `approval|direct`, Stundendauer `period_minutes`, Raster bis 16 Stunden), `planning/GeneratorPanel` (nimmt Neuplanungs-Jobs nicht
  als Generatorlauf auf, Hinweis solange eine läuft).

**Prüfung:** Python-Gesamtsuite 300 passed, 1 skipped (vor dem neuen Pinning-Test; eigene Dateien danach 94 passed); ruff sauber.
Frontend `tsc` grün, vitest 69/69, `vite build` (eigener outDir) ok. Browsertest (Playwright, eigenes Backend :8202 + Vite :9202,
frische Demo): Lehrkraft hell + Handy 390 px, Planung dunkel + Handy, Schulleitung – 44/44 Prüfungen ok, keine unerwarteten
Konsolen-/HTTP-Fehler (nur die absichtlich provozierten 403 für fremde Pläne/Export und 401 vor dem Login).

**Anfragen an Integration/Lead (geteilte Dateien):**
1. `frontend/src/lib/csvFields.ts`: Lehrkräfte-Felder `preferred_classes` („Wunschklassen“) und `time_windows` („Zeitfenster“)
   mit Aliassen wie in `csv_io.ALIASES` ergänzen (siehe meine Notiz „Zusatzaufgabe erledigt“).
2. Lead, `schulmanager/scheduler.py::_preplace_locked`: zuerst die gespeicherten Räume der fixierten Stunde versuchen (wenn frei und
   passend), erst danach `_assign_rooms` – sonst werden auch bei „Generieren mit fixierten Stunden“ gültige fixierte Stunden verworfen
   (Standortwechsel → Wegezeit). Das Pinning in `jobs.py` bleibt kompatibel.
3. Optional `frontend/src/api/types.ts`: `Settings` um `period_minutes`, `teacher_self_service`, `sick_note_after_days`,
   `messaging_students_to_students`, `messaging_retention_days`; `Teacher` um `preferred_classes`, `time_windows`; `Exam` um
   `can_edit` – dann entfallen lokale Casts in SettingsPanels/TeacherFields/ExamsPage.
4. Optional `components/ui.tsx::ErrorBox`: bei 403 den Server-Text (`detail`) mit anzeigen (z. B. `PrintTimetablePage` für fremde
   Pläne zeigt sonst nur den allgemeinen Text; die Stundenplan-Seite selbst hat bereits eine eigene 403-Ansicht).
5. Für andere Features nutzbar: `GET /timetable/allowed` und `features_common.reads_all_plans / is_scoped_teacher /
   plan_class_ids / plan_course_ids / teacher_entry_filter`; im Frontend `features/teacher/scope.ts` + `hooks.ts`.

## [Kursräume] Start Erweiterung 2 (§9.4) – Plan, Schnittstellen, frühe Entscheidungen
**Dateien (nur diese):** `schulmanager/channels.py` (reine Logik), `server/feature_models/channels.py`,
`server/migrations/versions/0004_channels.py` (`down_revision = "0002_files"`), `server/routes/features_channels.py`,
`tests/test_channels.py`, Frontend `src/features/channels/**` (Modul-ID `kursraeume`, Pfad `/kursraeume`, Gruppe `kommunikation`).
**Entscheidungen (früh, damit Postfach/Schüler planen können):**
- Kurs-Kanäle **je Kursteil**: `kind="course"`, `ref="<kurs>#<teil>"` (gleiche Schreibweise wie `Student.courses`), auch Ein-Teil-Kurse
  (`…#0`). Grund: Schienen/Kopplungen (Q1-LK1: M-LK1, E-LK1 …; Religion ev/kath/PP) sind getrennte Lerngruppen mit eigener Lehrkraft;
  Schüler laut `timetable.student_parts` (ohne Wahl → alle Teile, wie in der Anzeige). Klassen-Kanäle `kind="class"`, `ref=<klasse>`:
  Klassenleitung + alle Lehrkräfte mit Unterricht in der Klasse = Lehrende, alle Schüler der Klasse. Eigene Kanäle `kind="custom"`
  (nur `channels.manage` ohne Scope = Admin/Schulleitung) mit Zusatzmitgliedern. Kanalzeilen werden bei Bedarf angelegt (lazy).
- Rolle im Kanal dynamisch: `teacher` (Lehrkraft des Teils/der Klasse oder Zusatzmitglied, braucht `channels.manage`), `student`
  (`channels.use`), `supervisor` = Admin/Schulleitung ohne Mitgliedschaft: **nur lesen** (Material inkl. verborgener mit Status,
  Pinnwand, Teilnehmende; KEINE Abgaben-Inhalte/Noten, keine Änderungen – wer eingreifen muss, trägt sich als Zusatz-Lehrkraft ein, Audit).
  Eltern haben kein `channels.use` → kein Zugriff auf Kursräume, aber Übersicht offener Aufgaben ihrer Kinder (siehe unten).
- Verschlüsselt (`crypto.encrypt_text`, AAD `tabelle.feld:<id>`): Textseiten/Aufgabentexte (`channel_items.body_enc`),
  Abgaben (`assignment_submissions.text_enc`, `feedback_enc`, `grade_enc`), Pinnwand (`channel_posts.body_enc`). Titel/Ordnernamen Klartext.
- Zeiten: `visible_from`/`due_at` naive UTC (DB-Konvention), Stundenbeginn = `period_times` in Server-Ortszeit (TZ=Europe/Berlin).
**Geplante Endpunkte (`/api/v1`):** `GET /channels` (`?q=&kind=&all=1`), `GET/PATCH /channels/{id}`, `POST /channels` (custom),
`GET /channels/{id}/members`, `POST/DELETE /channels/{id}/members[/{user_id}]`, `GET/POST /channels/{id}/folders`,
`PATCH/DELETE /channels/{id}/folders/{fid}`, `GET/POST /channels/{id}/items`, `POST /channels/{id}/items/files` (Mehrfach-Upload),
`GET/PATCH/DELETE /channels/{id}/items/{iid}`, `POST /channels/{id}/copy` (Material/Ordner in andere eigene Kanäle),
`GET /channels/{id}/zip?folder_id=` (sichtbare Inhalte), `GET /channels/{id}/lessons?weeks=4` (kommende Stunden inkl. Woche, Ferien,
Entfall/Verlegung), `GET/PUT/DELETE /channels/{id}/items/{iid}/submission` (Schüler), `GET /channels/{id}/items/{iid}/submissions`,
`PUT /channels/{id}/submissions/{sid}/feedback` (Lehrende), `GET/POST /channels/{id}/posts`, `PATCH/DELETE /channels/{id}/posts/{pid}`,
`GET /channels/overview` (Startseite: Schüler neues Material + fällige Aufgaben; Lehrkraft heutige Stunden + zu bewertende Abgaben;
**Eltern `?student_id=<Kind>` → offene Aufgaben des Kindes ohne Inhalte** – für „Meine Übersicht“ des Schüler-Agenten nutzbar).
Live: `change` mit `scope:["channels","channel:<id>:"]` an die Mitglieder (`user_ids`), ohne Inhalt.

## [Kursräume] Zwischenstand 1 – Modelle + Migration fertig
- `server/feature_models/channels.py` + `migrations/versions/0004_channels.py` (Kopf neben 0003/0005; `compare_metadata` ohne Diff).
  Tabellen: `channels`, `channel_extra_members`, `channel_folders`, `channel_items`, `assignment_submissions`, `channel_posts`,
  zusätzlich `channel_reads` (letzter Besuch → „neu“). Verschlüsselte Spalten `*_enc` + `register_rewrap`.
- Offen: `schulmanager/channels.py`, Routen, Tests, Frontend, Browsertest.

## [Postfach] Start + Zwischenstand Etappe 1 (Modelle + Migration fertig)
**Dateien (nur diese):** `schulmanager/messaging.py` (reine Logik), `server/feature_models/messages.py`,
`server/migrations/versions/0005_messages.py` (down_revision `0002_files`), `server/routes/features_messages.py`,
`tests/test_messages.py`, `frontend/src/features/messages/**`.
- Fertig: Tabellen `conversations` (+ `parent_id`, `audience` JSON, `recipient_count`, `last_message_id/_at`),
  `conversation_participants` (PK conversation_id+user_id; + `last_read_id`, `cleared_id`, `has_incoming`, `has_sent`,
  `joined_at`), `messages` (+ `removed_at`, `removed_by`), `message_reports` (`reason_enc` statt `reason`, + `category`,
  `resolution_enc`, `actions`, `created_at`), `user_blocks`, zusätzlich `message_user_settings` (E-Mail-Hinweis,
  Postfach-Sperre durch Moderation) und `message_drafts` (Entwürfe, verschlüsseltes JSON). Schema-Vergleich
  (`test_migration_matches_models`) grün.
- Verschlüsselung/AAD: Betreff `conversations.subject:<cid>`, Text `messages.body:<cid>:<mid>` (Absender bewusst NICHT im
  AAD – `sender_id` wird beim Kontolöschen per SET NULL geleert), Rotation `crypto.register_rewrap("messages", …)`.
- Hinweis an Integration: `tests/test_server_core_store.py::test_admin_system` prüft `"0002_files" in db_revision` – mit
  `0004_channels` + `0005_messages` ist `0002_files` kein Kopf mehr (erwartet; erledigt sich mit `0007_merge`).
- Offen: Etappe 2 (Logik + Routen + Tests), 3 (Frontend), 4 (Browsertest).

## [Postfach] Fortsetzung durch Nachfolger – Etappe 2 begonnen
- Vorgefunden: Modelle/Migration (Etappe 1) und `schulmanager/messaging.py` (reine Logik: Empfängerauflösung, Gruppen,
  Adressbuch, Rechte) – beides geprüft (ruff sauber, Logik gegen Demo-Schule getestet) und wird weiterverwendet.
- Jetzt: `server/routes/features_messages.py` + `tests/test_messages.py`. Live-Ereignisse: `change` mit
  `scope:["messages"]` (für `useApi(…, {live:['messages']})`) **und** `message` `{conversation_id, message_id}` an die
  Empfänger (beides ohne Inhalt, `user_ids`); Moderation `change` mit `scope:["message_reports"]` (permission
  `messages.moderate`). Anhänge: purpose `message`, ref_type `message` (Entwürfe `message_draft`).

## [Kursräume] Zwischenstand 2 – Routen geprüft, Tests fertig
- `server/routes/features_channels.py` gegen die geplante Endpunktliste geprüft: vollständig (zusätzlich
  `DELETE /channels/{id}` (eigene, Aufsicht), `POST /channels/{id}/seen`, `POST /channels/{id}/reorder`,
  `POST /channels/{id}/items/visibility` (mehrere freigeben)). Kleine Korrekturen: `GET /channels/overview` liefert
  `role` = `teacher|student|supervisor|none|parent` (vorher „student“ auch für die Schulleitung), toter Code entfernt.
- `tests/test_channels.py` (16 Tests, grün, ruff sauber): Kursteil-Mitgliedschaft, fremde Kurse/Klassen 403,
  Rollen ohne Kursräume, Aufsicht nur lesend + Archivieren, eigene Kanäle + Zusatzmitglieder, Sichtbarkeit
  (verborgen/geplant/Ordner), Freigabe zur Stunde vor/nach Beginn (Zeit per `monkeypatch` auf `channels.now_utc`),
  kommende Stunden mit Herbstferien + Entfall (Override), Datei-Download-Rechte, Aufgaben/Abgaben/Rückmeldung/Frist,
  Pinnwand (`students_can_post/reply`, Anheften, Moderation), Kopieren in eigenen Parallelkurs, ZIP nur Sichtbares,
  kein Klartext in DB/Dateiablage, Übersichten (Schüler, Lehrkraft, Eltern), Eingabeprüfung.
- Offen: Frontend `src/features/channels/`, Browsertest, Abschlussnotiz.

## [Kursräume] Zwischenstand 3 – Frontend-Modul geschrieben (tsc + vitest grün), Browsertest offen
- `frontend/src/features/channels/`: `module.tsx` (ID `kursraeume`, Routen `/kursraeume`, `/kursraeume/:id`, Menü „Kursräume“
  Gruppe `kommunikation` mit Badge `kursraeume.neu`, Kacheln `neu` (schueler), `heute` + `abgaben` (lehrer)), `api.ts`,
  `types.ts`, `logic.ts`, `markdown.ts` + `Markdown.tsx` (sicherer Mini-Markdown ohne HTML), `components.tsx`,
  `VisibilityPicker.tsx` (inkl. Stundenauswahl), `dialogs.tsx`, `ChannelListPage.tsx`, `ChannelPage.tsx`, `MaterialTab.tsx`,
  `AssignmentsTab.tsx`, `BoardTab.tsx`, `MembersTab.tsx`, `widgets.tsx`, `badge.tsx`, `channels.css`, `channels.test.ts` (15 Tests).
- Offen: Build in eigenen Ordner, Browsertest (lehrer1/Schüler), Abschlussnotiz.

## [Kursräume] Status: fertig – §9.4 vollständig (Backend, Tests, Frontend, Browsertest)
**Dateien:** `schulmanager/channels.py` (reine Logik), `server/feature_models/channels.py`, `migrations/versions/0004_channels.py`,
`server/routes/features_channels.py`, `tests/test_channels.py`, `frontend/src/features/channels/**` (Modul-ID `kursraeume`).
**Endpunkte (`/api/v1`):** `GET /channels` (`?q=&kind=&all=1&archived=1`), `POST /channels` (eigene, Aufsicht),
`GET/PATCH/DELETE /channels/{id}`, `POST /channels/{id}/seen`, `GET/POST /channels/{id}/members`,
`DELETE /channels/{id}/members/{uid}`, `POST /channels/{id}/folders`, `PATCH/DELETE /channels/{id}/folders/{fid}`,
`POST /channels/{id}/reorder`, `POST /channels/{id}/items`, `POST /channels/{id}/items/files`,
`POST /channels/{id}/items/visibility`, `GET/PATCH/DELETE /channels/{id}/items/{iid}`, `POST /channels/{id}/copy`,
`GET /channels/{id}/zip` (`?folder_id=&students_view=1`), `GET /channels/{id}/lessons` (`?from=&days=&all=1`),
`GET/PUT/DELETE /channels/{id}/items/{iid}/submission`, `GET /channels/{id}/items/{iid}/submissions`,
`PUT /channels/{id}/submissions/{sid}/feedback`, `GET/POST /channels/{id}/posts`, `PATCH/DELETE /channels/{id}/posts/{pid}`,
`GET /channels/overview` (Schüler: `student{new_items,due,open_assignments}`, Lehrkraft: `teacher{day,lessons,to_grade}`,
Eltern `?student_id=<Kind>` → nur Titel/Frist/Status offener Aufgaben, volljährige Kinder `restricted`).
Datei-Zwecke: `channel_material`, `submission`, `channel_post` (10 MB); Access-Checks `channel_item|submission|channel_post`.
Live: `change` mit `scope:["channels","channel:<id>:"]` nur an Mitglieder (ohne Inhalt).
**Entscheidungen:** Kanal je Kursteil (`<kurs>#<teil>`, Mitglieder laut `student_parts`), Klassenkanal (Klassenleitung +
alle Lehrkräfte der Klasse), Rollen dynamisch; Schulleitung/Admin = Aufsicht nur lesend (keine Abgabe-Inhalte/Noten;
Eingreifen nur nach Selbsteintrag als Lehrende/r, protokolliert); Freigabe „zur Stunde“ = Stundenbeginn laut `period_times`
(Verlegung am selben Tag → neuer Beginn), Binden an bereits begonnene Stunden erlaubt (sofort sichtbar); Kopien im Ziel
standardmäßig verborgen; Texte/Abgaben/Rückmeldungen/Noten/Pinnwand verschlüsselt (AAD `<tabelle>.<feld>:<id>`).
Seit Zwischenstand 2: Stundenbezeichnung gebundener Materialien mit Blocklänge („1.–2. Std.“, `SchoolIndex.lessons`).
**Frontend:** `/kursraeume` (Suche Kurs/Klasse/Fach/Lehrkraft, Art-Filter, Aufsicht „alle Kursräume“, eigene anlegen),
`/kursraeume/:id` mit Tabs Material (Ordnerbaum + Brotkrumen, Drag&Drop-Upload über `FileUpload`, Link/Textseite
(sicheres Mini-Markdown, kein HTML), Freigabe-Dialog inkl. „Zur Stunde freigeben“ mit kommenden/früheren Stunden,
Mehrfachauswahl, Kopieren in eigenen Parallelkurs, ZIP), Aufgaben (Lehrkraft: anlegen, Abgaben filtern, Rückmeldung/
Bewertung/zurückgeben; Schüler: Text + Dateien abgeben, ändern, zurückziehen), Pinnwand, Teilnehmende. Kacheln: Schüler
„Neues Material & fällige Aufgaben“, Lehrkraft „Heute: Stunden & Material freigeben“ (Freigabe direkt aus der Kachel)
und „Abgaben zu bewerten“; Menü-Badge `kursraeume.neu` (neues Material + Beiträge).
**Prüfung:** Python 318 passed, 1 skipped (vorher 302; +16 `test_channels.py`), ruff sauber; Frontend `tsc` grün,
vitest 84/84 (+15), `vite build` (eigener outDir) ok. Browsertest (Playwright, Backend :8303 frische Demo + Vite :9303):
21/21 – lehrer1 (Frau Ludwig, M-LK1 = `Q1-LK1#1`) legt Ordner + Textseite + PDF an, gibt beides zu einer bereits
begonnenen Stunde frei (sofort sichtbar), legt Aufgabe an; Schüler/in des Kursteils (Konto `lk1schueler` für S02394,
Handy 390 px dunkel, ohne horizontales Scrollen) sieht Kachel + Material + Markdown und gibt mit Text + Datei ab;
`schueler3` (Kursteil `Q1-LK1#2`) sieht M-LK1 nicht, Direktaufruf → „Kein Zugriff“; Lehrkraft bewertet, Schüler/in sieht
Rückmeldung. Keine unerwarteten Konsolen-/HTTP-Fehler (nur erwartete 401 vor Login, 403 für den fremden Kursteil).
**Anfragen an Integration/Lead (geteilte Dateien):**
1. `components/Icon.tsx` + `NavIcon` (`lib/permissions.ts`): Symbol `folder` (oder `book`) ergänzen und im Menü „Kursräume“
   statt `list` verwenden (`features/channels/module.tsx`, eine Zeile).
2. Schüler-Agent („Meine Übersicht“): Eltern-Übersicht offener Aufgaben über `GET /channels/overview?student_id=` nutzen
   (Kursräume liefert bewusst keine Eltern-Kachel, um Dopplungen zu vermeiden).
3. Optional `demo.py` (Lead): ein Demo-Schülerkonto im Kursteil von `lehrer1` (z. B. M-LK1 `Q1-LK1#1`), damit Kursräume ohne
   zusätzliches Konto vorführbar sind (`schueler3` ist im Kursteil `Q1-LK1#2`).

## [Postfach] Zwischenstand – 3. Lauf gestartet (Routen vollständig vorgefunden)
- Fertig vorgefunden und weiterverwendet: `server/routes/features_messages.py` (alle Endpunkte laut Modul-Docstring inkl.
  Moderation, Entwürfe, Adressbuch, Wartung `run_retention`), `messaging.py`, Modelle, Migration.
- Jetzt: `tests/test_messages.py` (Etappe 2 Rest), danach Frontend `frontend/src/features/messages/` (Etappe 3), Browsertest (4).

## [Postfach] Zwischenstand – Etappe 2 fertig (Tests)
- `tests/test_messages.py` (19 Tests, grün, ruff sauber): alle Rollen → Einzelpersonen, Monitor/deaktiviert/selbst,
  Ungelesen/Ordner/Stumm/Archiv/„für mich löschen“ + endgültiges Löschen, Schüler→Schüler-Schalter (inkl. privater
  Antwort in Lehrer-Gruppen), Gruppenrechte + Lehrer-Scope (fremde Klasse 403), Antwortmodi none/sender/all,
  Nicht-Teilnehmende 404, Anhang-Rechte (inkl. Moderation nur bei Meldung), kein Klartext in DB/Dateien/Logs,
  Manipulation (Tausch + Bit-Kipper), Rotation (rewrap + alter Schlüssel entfernt), Melden/Moderation/Audit/Sperre,
  Blockieren, Aufbewahrung, Entwürfe, Adressbuch-Datensparsamkeit, Suche, Validierung, Live-Events ohne Inhalt,
  E-Mail-Hinweis ohne Inhalt (Dedupe, abschaltbar).
- Nächstes: Frontend-Modul `frontend/src/features/messages/` (Etappe 3).

## [Postfach] Zwischenstand – Etappe 3 Frontend geschrieben (tsc + vitest grün), Build/Browsertest offen
- `frontend/src/features/messages/`: `module.tsx` (ID `postfach`; Routen `/postfach/neu`, `/postfach/einstellungen`,
  `/postfach/moderation` [messages.moderate], `/postfach/:id?` [eine Route für Liste + Unterhaltung]; Menü „Postfach“
  (kommunikation, Badge `postfach.unread`) + „Postfach-Moderation“ (verwaltung, Badge `postfach.meldungen`); Kachel
  „Neue Nachrichten“; `background: MessagesBadge`), `api.ts`, `types.ts`, `logic.ts` (rein), `components.tsx`,
  `RecipientPicker.tsx` (ARIA-Combobox), `ComposePage.tsx`, `MailboxPage.tsx`, `ConversationView.tsx` (Chat, Antwort mit
  Auto-Entwurf), `dialogs.tsx` (Melden), `ModerationPage.tsx`, `SettingsPage.tsx`, `widgets.tsx`, `badge.tsx`,
  `messages.css`, `messages.test.ts`.
- Nächstes: vite build (eigener outDir), Browsertest (Etappe 4), Abschlussnotiz.

## [Postfach] Status: fertig
- Frontend `frontend/src/features/messages/` vollständig (siehe Zwischenstand Etappe 3); `npm run lint` grün, vitest 97/97,
  `vite build` ok.
- Browsertest (Playwright, frische Voll-Demo 2644 Schüler/169 Lehrkräfte, Backend :8305 + Vite :9305): 32/32 –
  schueler1 → lehrer1 mit PDF-Anhang, Antwort von lehrer1 (Handy 390 px dunkel, kein waagerechtes Scrollen), Live-Update im
  offenen Verlauf, Rundschreiben Sekretariat → Eltern 5a (Antwort nur privat, keine Empfängerliste), Melden durch schueler1,
  Moderation durch schulleitung (Liste ohne Inhalt, Ansicht erst nach Klick + Audit, Ausblenden, Sende-Sperre → 403
  `suspended`). Keine unerwarteten Konsolen-/HTTP-Fehler.
- Kein Klartext (Nachrichten, Moderationsvermerk) in `sm.db`, WAL, Dateiablage oder Server-Log.

## [Schüler] Status: fertig (§9.6)
- Backend: `schulmanager/student_self.py`, `feature_models/student_self.py`, `0006_student_self`,
  `routes/features_student_self.py`; Änderungen an `features_student_absences.py` (Gründe/Vermerke verschlüsselt, `attest`,
  `reason_hidden`, `?attest_missing=1`, Live-Hinweis an Klassenleitung), `me.py` (Export entschlüsselt + Dokumente),
  `maintenance.py` + `config.py` (`SM_STUDENT_DOCS_RETENTION_DAYS`), `permissions.py` (Admin ohne `student_documents.read`).
- Tests: `tests/test_student_self.py` (14) – Rechte, Volljährigkeit, Sichtbarkeit (Fachlehrkraft/Admin/fremde Eltern 404),
  Attest-Ablauf inkl. Ablehnen/Papier-Attest/Löschen, Verschlüsselung (DB, WAL, Dateien), Migration mit Altbestand,
  Übersicht, Export, Aufbewahrung.
- Frontend `features/students/` (siehe ARCHITECTURE §9.6), vitest +4.
- Browsertest (Playwright, frische Voll-Demo): 32/32 – eltern1 meldet per Klick und mehrtägig, Attest fehlt → Upload →
  eingereicht; schueler1 (minderjährig, Handy dunkel) nur Hinweis; schueler3 (volljährig) meldet selbst; Sekretariat prüft
  (Datei entschlüsselt abrufbar), lehnt mit Vermerk ab, vermerkt Papier-Attest; Klassenleitung 5a sieht Kachel, Atteste und
  Grund; Fachlehrkraft 5a sieht Abwesenheit mit „vertraulich“, keine Atteste. Gefundener Fehler behoben: abgelehnte Atteste
  zählten nicht als „fehlt“.

## [Integration] Status: fertig (§9.7)
- `0007_merge`, geteilte Frontend-Dateien (Typen, CSV-Felder, Icons `mail`/`folder`, ErrorBox 403, Einstellung Attestpflicht),
  Demo (Klassenleitungen, volljähriges Demo-Konto, Demo-Konto im Kursteil von lehrer1), Doku (README, ARCHITECTURE §9.6/9.7,
  SICHERHEIT 2.2–2.4/4.6, BETRIEB §15, `.env.example`, `docker-compose.yml`).
- Prüfung: Python 351 passed / 1 skipped, ruff sauber; Frontend `npm run lint`, vitest 101/101, `vite build` ok;
  PostgreSQL 16 lokal: Postgres-Test grün, `scripts/migrate.sh` zweimal → `0007_merge`.

## [Kontakt] Status: fertig (§11.2)
- Backend: `auth_messages.py` (Umsetzung: verschlüsselte Outbox-Arten `secure_email`/`sms`, Test-Postausgang), `sms.py`,
  `feature_models/contact.py`, `0008_contact` (`down_revision = "0007_merge"`), `routes/features_contact.py`.
  Geteilt geändert: `notify.py` (`send_email(..., attachments=None)`, `_deliver`-Zweig, Payload nach Zustellung leeren),
  `config.py` (Block nach SMTP + `_validate_contact()` + 3 Felder in `public_dict`), `maintenance.py` (Aufruf
  `features_contact.cleanup`). Frontend: nur `features/konto/*`, dazu in `pages/UsersPage.tsx` die Zeile des Reiters
  „Kontakt“ (`onEmailChange` hält das E-Mail-Feld des Dialogs aktuell). App.tsx/LoginPage/ProfilePage unverändert
  (Platzhalter des Leads genügten).
- Tests: `tests/test_contact.py` 34 grün; vitest `features/konto` 13 grün.
- Für den Lead: `.env.example`/BETRIEB um `SM_SMS_*`, `SM_DEV_OUTBOX`, `SM_AUTH_CODE_MINUTES` ergänzen; DSGVO-Export
  (`routes/me.py`) könnte Kontakt (E-Mail bestätigt, Nummer) mit ausgeben; Demo: Kontakte lassen sich über
  `PUT /users/{id}/contact {email, email_verified: true}` vormerken. Vorschau: `SM_DEV_OUTBOX` ist in Entwicklung
  automatisch an → alle Codes unter `/test-postausgang`. Links in Nachrichten nutzen `SM_BASE_URL`; der Test-Postausgang
  öffnet App-Links unabhängig davon als interne Pfade.
- Offen/Risiken: Link-Gültigkeit (auch für vom Sekretariat versendete Links) = `SM_AUTH_CODE_MINUTES` (15 min);
  `phone_hash` hängt an `SM_SECRET_KEY` (Wechsel → Suche per Nummer erst nach erneutem Speichern); E-Mail-Adressen sind
  nicht eindeutig (mehrere Konten je Adresse: je Konto eigene Nachricht, höchstens 5).

## [Richtlinien] Status: fertig (§11.5)
- Backend: `server/login_policy.py` (Auswertung, Cache, Ersteinrichtung, Validierung), `feature_models/login_policy.py`,
  `0011_login_policy` (`down_revision = "0007_merge"`), `routes/features_login_policy.py`. Geteilt geändert: `deps.py`
  (`AuthUser.login_setup`, `_apply_login_policy`, `LINK_SETUP_ALLOWED`, Sperre `link_required`), `routes/auth.py::login`
  (Richtlinie nach Passwort/Aktiv/TOTP, `X-Login-Methods`, Ersteinrichtung). `App.tsx` unverändert (Guard passte).
- Tests: `tests/test_login_policy.py` (11) grün; vitest `features/anmelderichtlinien/logic.test.ts` (8) grün.
- Browser-Rundgang (Playwright, Voll-Demo, 390 px hell/dunkel): Übersicht, Editor mit Beispiel, Klassen, Vorschau,
  Bericht ohne waagerechtes Scrollen; schueler1 → `method_not_allowed`; schueler2 mit Startpasswort → `/konten-verbinden`
  → Microsoft + Apple über die Test-Anbieter von Agent Anbieter verbunden → „Alles verbunden“ → Startseite; erneute
  Passwort-Anmeldung → 403 mit `X-Login-Methods: microsoft,apple`.
- **Für den Lead (geteilte Dateien, nicht von mir geändert)**: `api/client.ts` `KNOWN_DETAILS` ergänzen:
  `method_not_allowed` → „Für dieses Konto ist die Anmeldung mit Passwort nicht vorgesehen. Bitte melden Sie sich über
  einen der Anmeldedienste unten an.“ und `link_required` → „Bitte verbinden Sie zuerst die vorgeschriebenen Konten.“
  (LoginPage zeigt sonst den Rohcode). Optional: Listener für 403 `link_required` (wie `password_change_required`) →
  `AuthContext.refresh()`, damit eine während der Sitzung neu gesetzte Pflicht sofort auf `/konten-verbinden` führt.
  Optional LoginPage: Kopf `X-Login-Methods` (braucht Zugriff auf Antwort-Header im Client) zum Hervorheben der Knöpfe.
- Demo-Idee: Regel „Rolle Schüler/in: nur Microsoft + Apple, beide Pflicht“ per Knopf auf der Seite; in der Vorschau mit
  Test-Anbietern (`SM_SSO_DEV_MOCK`) komplett durchspielbar.

## [Anbieter] Status: fertig (§11.4)
- Backend: `server/sso_providers.py` (Registry, Discovery, Microsoft/Google/Apple/Schulkonto, Apple-ES256-Secret,
  Test-Anbieter), `server/identities.py` (Umsetzung: `linked_providers`, `available_providers`, `find_login_user` …),
  `feature_models/identities.py`, Migration `0010_identities` (übernimmt `users.oidc_sub`), `routes/features_sso.py`;
  geteilt: `routes/oidc.py` (alte Pfade über die gemeinsame Umsetzung, `_http_json`/`_discovery` weiter ersetzbar),
  `config.py` (Block `SM_SSO_*` nach OIDC + `_validate_sso`).
- Frontend `features/anmeldedienste/` (Login-Knöpfe, Fehlertexte, Profil „Verbundene Konten“, Benutzerverwaltung,
  Seite `/anmeldedienste` nur admin). Geteilte Frontend-Dateien unverändert (Einhängepunkte waren verdrahtet).
- Tests: `tests/test_sso.py` (18) grün; Gesamtsuite 466 passed / 1 skipped; ruff sauber; Frontend lint, vitest 172/172,
  `vite build` ok. Kein Browser-Rundgang (kein Playwright im Container) – nur HTTP-Smoke-Test des Test-Anbieters (:8413).
- Für den Lead: `accounts.user_dict["sso"]` beruht noch auf `users.oidc_sub` (neue Verknüpfungen setzen es nicht) →
  besser `bool(identities.linked_providers(...))`; DSGVO-Export (`routes/me.py`) könnte `identities.identity_rows` +
  `public_identity` mit aufnehmen. `0012_merge` muss `0010_identities` einschließen. Keine Demo-Daten nötig: in der
  Vorschau erscheinen alle vier Anbieter als „(Test)“; Demo-Konten per Test-Schulkonto mit `<benutzername>@beliebig`.

## [Zugangsdaten] Status: fertig (§11.3, Umsetzung siehe ARCHITECTURE §11.3.1)
- Backend: `server/pdf.py` (eigener PDF-1.4-Schreiber, WinAnsi/AFM-Breiten, QR per `segno`), `server/letters.py`,
  `feature_models/letters.py` + `0009_letters` (`letter_batches`, `account_initial_passwords`, beides verschlüsselt),
  `routes/features_letters.py` (Stapel, PDF/ZIP/Einzel-PDF, E-Mail-Versand, `/users/{id}/password`,
  `/classes/{id}/accounts`), `routes/features_classes.py` (`POST /classes`, `POST /classes/{id}/students` mit
  Geburtsdatum, Eltern-Zusammenführung per E-Mail, sofortigem E-Mail-Versand, `dry_run`).
- Zusatzwünsche umgesetzt: `models.Student.birth_date` (Volljährigkeit daraus), Eltern je Schüler/in (≤ 2, Merge über
  E-Mail inkl. vorhandener Elternkonten), Auto-Versand im Assistenten, Startpasswort verschlüsselt aufbewahren + „Auf
  Startpasswort zurücksetzen“/„selbst setzen“, neues Recht `passwords.reset` (Lehrkräfte: Scope `class_teacher`).
- Geteilte Dateien: `routes/users.py` (create/reset_password/bulk → `letter_batch`), `models.py` (`birth_date`),
  `permissions.py` (`passwords.reset`), `maintenance.py`, `pyproject.toml` (`segno>=1.5`), `api/types.ts`
  (`Student.birth_date`, Permission), `pages/UsersPage.tsx` (PDF-Knöpfe, Passwort-Bereich im Reiter Sicherheit),
  `features/classes/*` (Assistent `/klassen/neu`, Schüler-Reiter mit Konten), `docs/ARCHITECTURE.md` §11.3.1.
- Tests: `tests/test_letters.py` (15), vitest +2 Dateien (`classes/studentList.test.ts`, `zugangsdaten.test.ts`, 15 Tests).
  Gesamtsuite: 466 passed, 1 skipped; ruff sauber; `npm run lint`, vitest 172/172, `vite build` ok.
  Integration mit dem echten Test-Postausgang (Kontakt) per TestClient geprüft (PDF-Anhang kommt an).
  Kein Browser-Rundgang (Playwright-Browser-Download vom Proxy blockiert).
- Für den Lead: `0012_merge` muss `0009_letters` einschließen. §6-Rechtetabelle um `passwords.reset` ergänzen.
  Demo: keine Daten nötig; in der Vorschau Klasse über „Klassen → Neue Klasse“ anlegen, Briefe erscheinen mit
  Test-Postausgang unter `/test-postausgang`. `SM_LETTER_BATCH_MINUTES` ggf. in `.env.example`/BETRIEB aufnehmen.

## [R1-D1 Design-Grundlagen] Status: fertig (A-59, A-60, A-61; Vorbereitung A-62)
- Verbindliche Designsprache: `docs/DESIGN.md` (Grundsätze, Typo-Skala, Farb-Tokens hell/dunkel inkl. Kontrastwerte,
  Abstände/Radien/Schatten, Komponenten-Katalog, Hilfe-Funktion, Texte, Formulare, Tabellen am Handy, leere Zustände,
  Breakpoints + Navigationsmuster, Monitor-Regeln, Prüfliste).
- Hilfe-Funktion: `lib/help.ts` (reine Zustandslogik: 2-s-Timer, Rechtsklick, Touch, F1/„?“, eine offene Hilfe,
  Positionierung, Einstellung „Hilfetexte immer anzeigen“) + `components/Help.tsx` (`useHelp`, `HelpText`, `PageHelp`,
  `useDescribedBy`, `useHelpInline`). **`Field`**: neue Props `help` und `hintInline`; `hint` allein wird zur Hilfe an der
  Beschriftung (abwärtskompatibel), Hilfe/Hinweis/Fehler per `aria-describedby` am Steuerelement (`htmlFor` bzw. erstes
  Steuerelement im Feld). `Empty` hat optional `title`/`action`.
- Rahmen (`Layout.tsx`, `app.css`): < 600 px Kopfzeile + untere Leiste (`lib/layout.ts` `bottomNavItems`) + Menü;
  600–1023 px einklappbare Symbolleiste (Menü-Knopf klappt über dem Inhalt auf); ≥ 1024 px feste Seitenleiste;
  ≥ 1440 px `.page` bis 1680 px. Escape/Hintergrund/Schließen-Knopf schließen das Menü. Touch-Ziele 44 px
  (`pointer: coarse`). Karten ohne Schatten, Kennzahlen als `.stats`-Leiste, Login ohne Verlauf, Fokus blau 2 px,
  `--border-control` (3:1) für Eingabefelder, `KindBadge`-Kürzel mit AA-Kontrast; Reduced Motion: Animationen höchstens
  einmal, Laufband des Monitors statisch, Spinner langsam.
- Referenzseiten: Login, Start (alle Rollen), Profil ohne Erklärabsätze. Guard `lib/__tests__/designRules.test.ts`:
  Anzahl `className="explain"` je Datei darf den erfassten Bestand nicht übersteigen (Bestand nur senken).
- Offen für die nächste Design-Runde: Erklärtexte der übrigen Seiten (Liste im Bericht des Pakets; Spitzenreiter
  SettingsPanels, PolicyPage, ImportExportPage, ContactSection, ForgotPasswordPage, channels/widgets), `PageHelp` an
  weiteren Seitentiteln, Tabellen mit vielen Spalten auf `table-cards` umstellen.

## [R1-U1 Stundentafel & Fächer] Status: fertig (A-35, A-36/A-40 teilweise)
Backend siehe `docs/code/01-kern-domaene.md` §3.2/§3.9/CSV und `docs/code/03-routen-kern.md` (features_data,
features_planning, features_exchange). Keine Migration (nur Planungsdokument: `Course.pinned`, Profil-Payload
`new_subjects`). Frontend (Planungsseiten haben noch keine `docs/code`-Datei):
- `pages/planning/curricula.ts` – gleiche Zuordnungsregel wie `planning.resolve_curricula` (Klasse vor Jahrgang,
  Gleichrang = Konflikt), `curriculumScope`, `curriculumSearchText` (Suche findet eine Tafel auch über die Klassen,
  für die sie per Jahrgang gilt, z. B. „7c“), `duplicateSubjects`, `gradeOptions`, `GRADE_MIN/MAX` (0–20, auch im
  Stammdaten-Klassenformular); Tests `curricula.test.ts`.
- `CurriculaEditor.tsx` – Auswahlfehler nach „Neue Stundentafel“ behoben (`creating`-Modus, `select()` lädt direkt);
  „Gilt für Klassen“ (MultiSelect mit Suche, „+ ganzer Jahrgang“ fügt alle Klassen eines Jahrgangs hinzu),
  „Automatisch für Jahrgänge“ optional (frei 0–20, wird bei Klassenauswahl nicht verwendet; Auf-/Zuklappen als
  Zustand `gradesOpen`, nur beim Auswählen einer Tafel vorbelegt – klappt beim Abwählen nicht mehr weg); Live-Anzeige „Gilt für“,
  Überschneidungen, Badges „n Kl./Konflikt/keine Klasse“, „Klassen ohne Stundentafel“; schon gewählte Fächer sind
  in anderen Zeilen gesperrt; „+ Neues Fach …“/„Neues Fach“ → `NewSubjectDialog` (nur mit `masterdata.edit`);
  409 beim Speichern → Rückfrage mit Klassenliste, dann `force`; danach „Kurse erzeugen …“.
- `RebuildCourses.tsx` – Vorschau (`dry_run`) mit neu/geändert/entfernt, Konflikten, eigenen Anpassungen (optional
  verwerfen); `RebuildResultView` mit Hinweis + Direktknopf „Stundenplan neu berechnen“ (Generator startet sofort)
  bzw. „Zum Generator“ (Stundentafel-Seite). Genutzt von `GeneratorPanel` und `CurriculaEditor`.
- `CoursesEditor.tsx` – Hinweis „Eigene Anpassungen: …“ mit „Wie Stundentafel“ (`PUT {pinned: []}`), Herkunft
  „Stundentafel, angepasst“. `SettingsPanels.tsx` (Bericht) – Kennzahl/Tabelle „zu viel verplant“.
- `ImportExportPage.tsx` – JSON: `danger` fett im Ergebnis; „Ersetzen“ prüft vorher und fragt bei Teil-Dokumenten
  mit der Löschliste nach.
- Gemeinsame Dateien (kleine Änderungen): `api/types.ts` (`Course.pinned`, `OverplacedHours`, `RebuildResult`,
  `CurriculaOverview`), `api/endpoints.ts` (`data.create/update(..., force)`, `planning.coursesFromCurricula(opts)`,
  `planning.curriculaOverview`), `models.py` (`Course.pinned`).
- Offen/Folgearbeit: Klassen-Assistent (`features_classes.py:938`, `NewClassPage`) erlaubt weiter nur Jahrgang 1–13,
  `/data/classes`, Stammdaten-Formular und Stundentafeln jetzt 0–20; Anmelde-Richtlinien/Nachrichten-Gruppen nach Jahrgang ungeprüft für
  Jahrgänge > 13. Klassengruppen/Bildungsgänge (A-38) fehlen weiterhin.

## [R2-A B-04 Vertretungsplan + Betrieb sofort] Status: fertig, Bericht an Hauptsitzung (Spur A)
Dateien: `substitution.py`, `features_substitutions.py`, `features_common.py` (nur `filter_plan`), `models.py`
(Settings: öffentliche Lehrkräfte), `SubstitutionsPage.tsx`, `PrintSubstitutionsPage.tsx`, `EntryTable.tsx`,
`lib/substitution.ts`, `api/types.ts` (kleine Edits: DayPlan-Felder, Settings-Feld), `features_data.py` (nur `SettingsIn`
ein Feld), `docker-compose.yml`, `.env.example`, `deploy/systemd/schulmanager-backup.service`, `scripts/backup.sh`,
`docs/BETRIEB.md`. Ports 8621/5621. Keine Migration geplant.

## [R2-B B-06 Krankmeldungen nur für Berechtigte + Datenschutz sofort] Status: fertig, Bericht an die Hauptsitzung (Spur B)
Dateien: `features_student_absences.py`, neu `server/absence_access.py`, `permissions.py` (admin ohne
`student_absence.read`), `models.Settings` (am Ende anhängen: `subject_teacher_absence_view`), `features_data.py`
(nur `SettingsIn` ein Feld), `features_student_self.py` (`export_documents`), `me.py` (Export, kleine Änderung),
`users.py` (API-Token), `pages/StudentAbsencesPage.tsx`, `features/students/widgets.tsx`, `api/types.ts` (kleine Edits:
Settings-Feld, StudentAbsence-Flags), `pages/planning/SettingsPanels.tsx` (ein Feld), `docs/ARCHITECTURE.md` §6.
Ports 8622/5622. Keine Migration geplant.
- R2-A: kleine Edits angekündigt/erledigt: `models.py` (`Absence.self_reported`, `Settings.public_absent_teachers` nach `policy`), `features_data.SettingsIn` (1 Feld nach `policy`), `api/types.ts` (DayPlan-Details, Absence.self_reported, Settings-Feld), `pages/planning/SettingsPanels.tsx` (1 Auswahl im Abschnitt Vertretungsregeln).
- R2-A: `styles/app.css` `.table-wrap { position: relative }` (sr-only-Texte in Tabellenzellen verursachten auf 390 px waagerechtes Scrollen, z. B. Löschknöpfe der Abwesenheitsliste).
- R2-A (Fortsetzung): neu `components/AbsentTeachersCard.tsx` (Karte aus `SubstitutionsPage` herausgelöst, für B-12 wiederverwendbar); `EntryTable` bricht Stunde, Klassenlisten und Raum alt/neu zwischen Kürzeln um (Hinweis-Spalte bei 1280 px wieder sichtbar); `ABSENCE_REASON_FIELD` in `lib/substitution.ts`. Keine Migration.
- R2-B: `styles/app.css` eine Regel `.row-end.nowrap { flex-wrap: nowrap }` (Aktionsknöpfe in Tabellenzellen bleiben in einer Zeile, Krankmeldungen).
- R2-B Prüfung: kleine Edits `api/types.ts` (`StudentAbsenceAccess.student_ids`), `features_student_self.documents_summary`
  (Attest-Zähler Eltern über `absence_access`), `features_student_absences.student_absence_access`, `lib/studentAbsences.ts`,
  `StudentAbsencesPage.tsx`, je eine Zeile `users.py` (Token-Meldung) und `SettingsPanels.tsx` (Hilfetext); Ports 8722/5722
  (beendet). Keine Migration. Status: Prüfung fertig, Bericht an die Hauptsitzung.
- R2-B Prüfung (2. Durchgang): nur Paketdateien (`absence_access.py`, `features_student_absences.py`,
  `features_student_self.py`, `StudentAbsencesPage.tsx`, `lib/studentAbsences.ts`, Tests, `docs/code/*`); geteilte
  Dateien höchstens kleine Edits. Ports 8722/5722. Keine Migration. Ergebnis: Übernahme der Stunden-Meldung einer
  Fachlehrkraft durch umfassendere Meldung (statt 409), Selbstmeldung Volljähriger nach Geburtsdatum
  (`AbsenceAccess.can_report`), `/krankmeldungen` lädt Rechte bei `parent_access` neu, datumsfester Schultag-Test;
  geteilt nur `docs/ARCHITECTURE.md` (ein Satz nach §6-Tabelle). Server beendet. Status: Prüfung fertig, Bericht an die
  Hauptsitzung.

## [R2-D B-13 Verständliche Fehlermeldungen + Konto-Cache] Status: fertig, wartet auf Prüfung (Spur D)
Dateien: `api/client.ts`, neu `lib/session.ts` (zentrale Sitzungs-Rücksetzung) und `lib/errors.ts` (Übersetzung
Validierungsfehler), `components/ui.tsx` (Field/ErrorBox/AsyncButton, kleine Edits), `context/AuthContext.tsx`,
`context/ToastContext.tsx`, `hooks/useCollection.ts`, `App.tsx` (Forbidden im App-Rahmen), `styles/tokens.css`,
`styles/timetable.css`, `features/registry.ts` (geteilt: `CORE_PATHS` + Badge-Reset), `features/README.md`; je eine
Zeile `components/FileUpload.tsx`, `features/channels/api.ts`; ggf. `styles/app.css` (eine Regel). Ports 8623/5623.
Keine Migration.
Ergebnis: `lib/errors.ts` heißt `api/errors.ts`; `styles/app.css` nicht geändert. Zusätzlich `api/files.ts` (Kommentar
`message`), `docs/code/05-frontend-basis.md`, `docs/code/README.md` (2 Zeilen). Offen für Spur A/B: Absenden-Dialoge
(`SubstitutionsPage`, `StudentAbsencesPage`) in `FormErrors` legen und `Field name=…` setzen.
- R2-D Prüfung: kleine Edits nur in Paketdateien: `api/client.ts` (jede Anfrage schickt `X-Request-ID`, Rückfall für
  die Fehlernummer, weil ein echter 500 des Backends keine Request-ID trägt), `context/ToastContext.tsx` (offene Toasts
  bei Sitzungs-Rücksetzung leeren), Tests `api/errors.test.ts`, `lib/__tests__/session.test.ts`, `docs/code/05`
  (§3.2, §3.3, §7, §8 U18–U20). Ports 8723/5723 (beendet). Keine Migration. Status: Prüfung fertig.

## [R2-A Prüfung] Status: begonnen (Spur A, Prüf-Agent)
Kleine Edits nur in Paketdateien: `features_common.filter_plan` (Fallzahlen/Klassenfilter vor dem Lehrkraft-Filter,
Namensersatz nur ganze Wörter), `pages/SubstitutionsPage.tsx` (leere Tabelle bei Lehrkraft-Filter), `lib/substitution.ts`
(Hilfetext Raum-Grund), `tests/test_substitution_b04.py`, `lib/__tests__/substitutionB04.test.ts`, `docs/code/03`, `06`.
Ports 8721/5721. Keine Migration.
- R2-A Prüfung (2. Durchgang): kleine Edits `features_common.scrub` (Gründe nur als ganze Wörter entfernen, „Exkursion“ blieb sonst bei Grund „Kur“ als „Exsion“), `lib/substitution.filterClassRows` + `SubstitutionsPage` (Klassenzeile bleibt beim Lehrkraft-Filter, wenn deren Unterricht wegen der Klassenabwesenheit entfällt), Tests, `docs/code/03`, `05`, `06`; außerdem `AbsentTeachersCard` (feste `aria-label`, Datum in `caption`) und Meldung 403 beim Löschen fremd erfasster Abwesenheiten. Ports 8721/5721 (beendet). Keine Migration. Status: Prüfung fertig, Bericht an die Hauptsitzung.

## [R3-A1 Kalender/Wochen Backend] Status: begonnen (Spur A, 11.10. 17:15)
Dateien laut Entwurf §11.1/§14.4/§15 (`docs/entwurf/KALENDER-ZEITRASTER.md`): `models.py`, `calendar_utils.py`, neu
`weeks.py`, `scheduler.py`, `timetable.py`, `planning.py`, `duties.py`, `exams.py`, `teacher_profile.py`,
`substitution.py`, `channels.py`, `student_self.py`, `demo.py`, `integrations/*`; Routen `features_data.py`,
`features_timetable.py`, `features_teacher_profile.py`, `features_substitutions.py`, `features_exchange.py`, neu
`features_calendar.py`, `features_classes.py`, `features_common.py` (`range_plans`/`week_history`), `jobs.py`,
`notify.py`; am Ende (Schritt 7, V3) `features_student_absences.py`, `features_student_self.py`, `features_channels.py`.
Tests: neu `tests/test_weeks.py`, `tests/test_weeks_solver.py`, `tests/data/weeks_cases.json`, `tests/fixtures/*_r2.json`
und betroffene Tests. Geteilt (kleine Edits): `frontend/src/api/types.ts` (nur optionale Felder), `docs/ARCHITECTURE.md`.
Ports 8631/5631. Keine Migration.

## [R3-A2 Kalender/Wochen Oberfläche] Status: begonnen (Spur A, 2. Agent, 11.10.)
Dateien laut Entwurf §11.1/§14.4/§14.5/§15: neu `lib/weeks.ts`, `components/WeekNav.tsx`, `components/WeekPatternInput.tsx`,
`components/weeks.css`, `pages/planning/CalendarPanel.tsx` (V4); `lib/dates.ts`, `lib/rules.ts`, `lib/grid.ts`,
`components/DateNav.tsx`, `RuleEditor.tsx`; `pages/TimetablePage.tsx`, `PrintTimetablePage.tsx`, `DutiesPage.tsx`,
`ExamsPage.tsx`, `MasterDataPage.tsx`, `planning/CoursesEditor.tsx`; `features/teacher/*` (ohne `ReplanPanel.tsx`);
vitest unter `lib/__tests__/` und in den Features; Doku `docs/code/05`–`08`.
Ausnahmen (P2, kleine Edits): KZ-9 `TimetableGrid.tsx`, `TimetablePage.tsx`, `SettingsPanels.tsx` (nur
`SchoolSettingsPanel` → `CalendarPanel.tsx`, dort bleibt der Einhängepunkt; `WeightsPanel` unberührt), `DESIGN.md:109`;
KZ-6 `features/classes/*` (WeekTab, logic, types, ClassHeader, api), `features/students/*`, `channels/VisibilityPicker.tsx`,
`channels/types.ts` (Kommentar), `StudentAbsencesPage.tsx` (nur `currentSchoolDay`); KZ-7 eine Zeile `AdminPage.tsx`;
KZ-2 je eine Zeile `PrintSubstitutionsPage.tsx` (`currentSchoolDay`), `lib/substitution.ts` (`statsWeek`),
`lib/csvFields.ts` (Hilfe Wochen); `api/errors.ts` (Feldnamen). Geteilt: `api/types.ts` (nur optionale Felder, V16),
`api/endpoints.ts` (neue Funktionen, alte Signaturen bleiben). Nicht: Backend, `MonitorPage`, `DashboardPage`,
`SubstitutionsPage`, `WeightsPanel`. Ports 8632/5632. Keine Migration.
- R3-A1 (17:23): Fixture T0 liegt in `tests/fixtures/` (`school_r2.json`, `expected_r2.json`, Test `tests/test_weeks_r2.py`).
  **`tests/data/weeks_cases.json` steht** (describe/expand/pattern_errors/weeks_errors/convert/rhythm_*), Format im
  Feld `_doc`. R3-A2 kann `lib/weeks.ts` dagegen bauen.
- **R3-A1 (18:23): Vertrag R3 steht** (Backend nach §15.3, Schritte 0–5 fertig, Suite grün bis auf T3-Grep, der nach
  Schritt 6/7 grün wird). Für R3-A2/R3-D:
  - `GET /calendar/school-year?date=&class_id=` (alle Angemeldeten; fremde Klasse 404) → `SchoolYear` (+ `first_monday`);
    zusätzlich `GET /calendar/week?date=&class_id=` → `WeekInfo`.
  - `POST /settings/calendar-preview` → `{today_before, today_after, warnings}`. `PUT /settings`; 409
    `{code:"plan_change", message, changes}` listet nur verlustbehaftete Änderungen. `school_days` setzt `days` = max+1;
    `days` allein leert `school_days`.
  - `GET /timetable/{kind}/{ref}?date=|week_no=|week=(alt: = week_no−1)&all_days=1` (**Standard all_days=1**, E2) →
    `week_no` (laufende Woche), `week_info`, `day_info[]`, `days` (Spalten ab Mo), Zellen mit
    `weeks_text`, nur aktive Zellen. `?week=` > 52 → 422.
  - `/classes/{id}/week`, `/me/week`: `days` immer 7 (`day_kind`, `has_items`), `week_info`; Tag ohne Unterricht der Klasse:
    `holiday` = „Kein Unterricht“ (Sa/So: „Wochenende“). DayPlan/Monitor-/Tageskopf: `day_kind`, `week_info`.
  - `PATCH /classes/{id}?force=1` nimmt `school_days` ([] = Schule) (Recht timetable.edit, sonst 403 mit Text §15.5);
    Antwort `changes`. `GET /classes/{id}`: `class.plan {school_days, text}`, `class.school_days`, `can_edit_plan`.
  - `rhythm {every, from_week, to_week}` oder `weeks` (laufende Wochen) in /data/courses, /data/duties,
    /data/classes.unavailable[], /data/teachers.unavailable[]/wishes[]/time_windows[], Profil WindowIn/RuleIn; beides → 422;
    `week_pattern {every, from, to?}` ältere Form wird zum Rhythmus. Auch Lesson und Course haben `rhythm`.
  - Profil: `options.school_days`; `availability[]` je Tag und Wochengruppe
    `{weeks, rhythm, weeks_text, day, day_name, periods}`.
  - Bericht: Konflikte „Lehrkraft X doppelt belegt: Mo 3. Stunde 09:50, Woche 1 und jede 2. Woche: L1, L2“,
    `unplaced_hours[].weeks_text`, `stats.week_variants`. Leere Regel → 422 „Bitte mindestens einen Tag oder eine Stunde wählen.“
- R3-A1 (18:26) Schritt 7 (V3): je eine kleine Änderung in `features_student_absences.py` (Schultag/Attest mit
  Klassentagen, Text §15.5), `features_student_self.py` (heute/nächster Schultag und Attest mit Klasse) und
  `features_channels.py` (`is_school_day` mit Klasse des Kursraums, Docstring). R3-B bitte frisch lesen.
- R3-A2 (11.10., Abschluss): fertig, Bericht an die Hauptsitzung. Zusätzlich neu `components/ConfirmChanges.tsx`
  (409-Liste „Trotzdem übernehmen“, `useConfirmChanges`), `components/ClassPlanningFields.tsx`; Tests
  `lib/__tests__/{weeks,weeksUi,noWeekLetters}.test.ts`. Geteilte Dateien nur ergänzt (`api/types.ts` optionale Felder,
  `api/endpoints.ts`: `calendar.schoolYear`, `settings.put(s,{force})`, `settings.calendarPreview`,
  `timetable.view(kind, ref, {date, week_no, all_days})`; Zahl als 3. Argument bleibt). `lib/dates.ts`: Wochenbuchstaben
  entfernt, `SchoolDays = number | number[]`, `isoWeekNumber`, `formatDayMonth`.
  Für R3-D (B-12): `DateNav` hat `weekText` (`week_info.week_text`) und `schoolDays` als Liste; `lib/weeks.ts`
  (`weekText`, `holidayBadge`, `schoolDaysOf`, `isOffDay`). `SubstitutionsPage`/`PrintSubstitutionsPage` zeigen noch
  „Woche {week_no}“ (Ziffer) – Umstellung auf `week_text` gehört zu KZ-2/R3-D.
  Ports 8632/5632 beendet. Keine Migration.
- R3-A1 (11.10. 18:50, Abschluss): fertig, Bericht an die Hauptsitzung. Komplette Suite 679 passed, 4 skipped
  (langsame Generatorfälle; mit `SM_SLOW=1 python -m pytest -q tests/test_weeks_solver.py` 14 passed), `ruff` sauber,
  Frontend lint + vitest (334) grün, Browser-Rundgang 1280/390 hell/dunkel ohne Befund. Code-Doku nachgezogen
  (`docs/code/{README,01,03,04,09}`, `ARCHITECTURE.md` §12). Ports 8631/5631 beendet. Keine Migration.
  `.gitignore`: Ausnahme `!tests/data/` ergänzt – die Regel `data/` hätte `tests/data/weeks_cases.json` (gemeinsame
  Testtabelle für pytest und vitest) vom Commit ausgeschlossen.
- R3-A1 Prüfung (11.10.): begonnen (Prüf-Agent Spur A, Ports 8731/5731). Kleine Edits nur in R3-A1-Dateien (`features_classes.patch_class`, `calendar_utils`, …) plus Tests; Bericht folgt.
- R3-A2 Prüfung (11.10.): begonnen (Prüf-Agent Spur A, Oberfläche, Ports 8732/5732). Kleine Edits nur in R3-A2-Dateien (`lib/weeks.ts`, `components/Week*`, `CalendarPanel.tsx`, Seiten aus dem Paket) plus vitest; kein Backend, nicht `MonitorPage`/`DashboardPage`/`WeightsPanel`. Bericht folgt.

## [Lead] Erweiterung 5 – Auto-Planer, Postfach-E-Mail, Kursräume, Stundentafel je Klasse, Fehlzeiten (fertig)
- **Auto-Planer:** `schulmanager/autoplan.py` (`find_problems`, `repair_rooms`, `prepare_repair`, `expand_courses`),
  `server/autoplan.py` (Listener auf `change`, Job `kind="autoplan"` über `jobs.manager`, `merge_replan(strict=False)`,
  Übernahme nur bei Verbesserung, Scope `["timetable","autoplan"]`; `undo`/`restore` lösen nichts aus). Settings
  `auto_replan`; Config `SM_AUTOPLAN*`; Tests setzen `SM_AUTOPLAN=0` (conftest) – gezielt an in `test_autoplan.py`.
  Endpunkte `GET /planning/autoplan`, `POST /planning/autoplan/run`. Vertretungs-Engine: Fachraum gesperrt ohne Ersatz →
  Tausch mit anderer Einzelstunde der Klasse (`_swap_for_room`), sonst Ausweichraum mit Warnung; `Exam.room` belegt Räume.
- **Migrationen:** 0008 (`users.parents_can_see_channels`), 0009 (Mail), 0010 (Fehlzeiten). **Nie `batch_alter_table`
  auf Tabellen mit eingehenden `ON DELETE CASCADE`-FKs (v. a. `users`)** – unter SQLite löscht der Neuaufbau abhängige
  Zeilen (Regressionstest `tests/test_migrations.py`). Nur `add_column`/`create_table`.
- **Kursräume:** Rolle `parent` (nur lesen; volljährige Kinder nur mit Freigabe `PUT /channels/parent-access`),
  Lehrende tragen Schüler/innen ein/aus (`GET /channels/{id}/member-candidates`, Zusatzrolle `excluded` für Stundenplan-
  Schüler, `DELETE /channels/{id}/excluded/{uid}` = wieder aufnehmen), Aufsicht zusätzlich Lehrende, Ersteller/in kann
  nicht verlassen/ausgetragen werden. ZIP-Download und Archivieren entfernt (`archived:true` → 422). Eltern haben jetzt
  `channels.use`.
- **Stundentafel je Klasse:** `planning.set_class_curriculum`/`rebuild_class_courses`; `GET|PUT /classes/{id}/curriculum`
  (Stammdaten/Planung oder Klassenleitung); Frontend-Reiter „Stundentafel“ + Abschnitt im Klassen-Dialog (Stammdaten).
- **Postfach:** Empfänger `type: user|group|email` mit `role: to|cc|bcc`; BCC sehen nur Absender/in und sich selbst,
  Antwort aus BCC privat; Adresse eines Schulkontos → intern, sonst extern über verbundenes Konto (`mail_accounts`,
  `routes/features_mail.py`, `server/mailbridge.py`, Transport für Tests austauschbar). Unterhaltungsart `email`.
- **Fehlzeiten:** `student_absences.kind|minutes|source|excused_*`, Status `teilweise`; `GET /student-absences/record`,
  `GET /student-absences/form.pdf` (`server/pdf_simple.py`); Seite `/fehlzeiten/:studentId`; geprüfte Entschuldigung →
  Eintrag entschuldigt. Settings `sick_phone`, `sick_phone_hours`.
- **Prüfung:** Linux (Docker-Dev-Image) 418 passed, 1 skipped; Windows zusätzlich 2 bekannte Plattformfehler
  (`os.replace` auf offene Datei, `/proc`-Metriken). Frontend `tsc` grün (außer Windows-Groß/Klein `Markdown.tsx`/
  `markdown.ts` – unter Linux ok), vitest 127/127.

- M5 (13.10., Abschluss): Kompetenzraster und Lernstand fertig. Migration `0040_competencies` (down_revision `0035_plan_proposals`).
  Neue Rechte `competency.read|assess|manage` (permissions.py, ARCHITECTURE.md §6, ROLLEN-RECHTE.md, `api/types.ts`), neuer Elternbereich
  `kompetenzen` in `parent_access.py`, kleiner Block in `demo_loader.load_demo`. Doku `docs/KOMPETENZEN.md`. Ports 8925/5925 beendet.

- M4 (13.10., Abschluss): Notenbuch fertig (B-52, `docs/NOTENBUCH.md`). Migration `0039_gradebook` (down_revision `0035_plan_proposals`),
  Rechte `gradebook.use|read_class|manage|export` (permissions.py, ARCHITECTURE.md §6, ROLLEN-RECHTE.md, `api/types.ts`), Hook in
  `features_grades.put_results` (Klausurnoten ins Notenbuch nachziehen), Block in `demo_loader.load_demo`, Einbettung `MyGradebook` in
  `students/GradesPage.tsx`. Schnittstelle für M1/M3: `gradebook_sources.publish_results`. Ports 8924/5924 beendet.
