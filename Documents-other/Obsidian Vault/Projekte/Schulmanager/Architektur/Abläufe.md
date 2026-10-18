---
tags: [schulmanager, architektur, ablaeufe]
quelle: "schulmanager/server/routes/, schulmanager/server/*.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Abläufe

> Einstieg: [[Schulmanager Architektur]] · Sequenzdiagramme der wichtigsten Abläufe

## 1. Login mit 2FA und Kontowechsel

Beteiligt: [[Seite LoginPage]], [[Frontend API-Schicht]], [[Routen auth]], [[Server deps]], [[Server konten und anmeldung]], [[Server audit]], Tabellen `users`, `sessions`, `login_attempts`.

```mermaid
sequenceDiagram
  autonumber
  participant B as Browser (LoginPage)
  participant A as routes/auth.py
  participant K as login_policy / security
  participant DB as DB (users, sessions)
  B->>A: POST /auth/login {username, password}
  A->>DB: Sperre prüfen (login_attempts, 429 bei zu vielen Fehlversuchen)
  A->>DB: Konto laden, Passwort prüfen (scrypt)
  alt 2FA aktiv und kein Code
    A-->>B: 401 totp_required
    B->>A: POST /auth/login {…, totp}
    A->>K: TOTP prüfen (mit Replay-Schutz)
  end
  A->>K: password_login(user) – Anmelde-Richtlinie (erlaubt / setup / verweigert)
  K-->>A: erlaubt
  A->>DB: Sitzung anlegen (Token nur als Hash), Audit auth.login
  A-->>B: Set-Cookie sm_session (httponly) + {user, csrf_token}
  Note over B,A: Folgeanfragen: Cookie + Header X-CSRF-Token bei POST/PUT/PATCH/DELETE
  B->>A: POST /auth/login?add=true (weiteres Konto)
  A-->>B: neues Cookie sm_session; bisherige Tokens im Cookie sm_sessions (max. 5 Konten)
  B->>A: POST /auth/accounts/switch {user_id}
  A-->>B: Cookie wechselt, neues csrf_token
```

Pflichtseiten erzwingt der Guard: `/passwort` (Startpasswort), `/zwei-faktor` (Rolle laut `SM_REQUIRE_2FA_ROLES`), `/konten-verbinden` (Pflicht-Verknüpfung laut Richtlinie). SSO läuft über [[Routen features_sso]] / [[Routen oidc]] und endet in derselben `login_user`-Funktion.

## 2. Stundenplan erzeugen

Beteiligt: [[Seite PlanningPage]], [[Routen features_planning]], [[Modul planning]], [[Server jobs]], [[Modul scheduler]], [[Server events]], [[Server store]].

```mermaid
sequenceDiagram
  autonumber
  participant P as PlanningPage
  participant R as routes/features_planning
  participant L as planning.py
  participant J as JobManager (jobs.py)
  participant G as Generator-Prozess (spawn)
  participant S as SchoolStore
  participant E as EventBus / SSE
  P->>R: POST /planning/courses-from-curricula
  R->>L: build_courses_from_curricula
  R->>S: mutate(Kurse) → neue Version
  P->>R: POST /planning/assign-teachers
  R->>L: assign_teachers → S.mutate
  P->>R: POST /planning/generate
  R->>J: start_generate(School als Dict, Parameter)
  J->>G: Prozess starten (scheduler.generate_best_of)
  R-->>P: 202 {job_id}
  loop Fortschritt
    G-->>J: progress(msg, fraction)
    J->>E: publish job {id, status, progress}
    E-->>P: SSE job
  end
  G-->>J: Ergebnis (Stunden, unplaced, stats)
  P->>R: GET /planning/jobs/{id}?lessons=1 (Entwurf prüfen)
  P->>R: POST /planning/jobs/{id}/apply
  R->>J: apply(job, user)
  J->>S: mutate → neue Version + Audit (GET /planning/jobs/{id} markiert veraltete Entwürfe mit outdated)
  S->>E: publish change {version, scope: timetable}
  E-->>P: SSE change → Seiten laden neu
```

**Auto-Planer:** Ein `change` mit planungsrelevantem Scope weckt [[Server autoplan]]; nach `SM_AUTOPLAN_DELAY` s Ruhe prüft [[Modul autoplan]] den Plan, repariert direkt oder startet einen Job der Art `autoplan` (nur betroffene Kurse frei, Rest samt Räumen fixiert) und übernimmt das Ergebnis selbstständig, wenn es besser ist (Scope `autoplan`, rückgängig über [[Seite HistoryPage]]). Neuplanung einer Lehrkraft: `POST /planning/replan-teacher/{id}` → Entwurf.

## 3. Krankmeldung → Vertretung → Klassenbuch → Stundenplan

Beteiligt: [[Seite DashboardPage]], [[Seite SubstitutionsPage]], [[Routen features_substitutions]], [[Modul substitution]], [[Server notify]], [[Routen features_register]], [[Feature classes]], [[Routen features_student_absences]], [[Routen features_timetable]], [[Routen features_calendar]].

```mermaid
sequenceDiagram
  autonumber
  participant L as Lehrkraft (Dashboard)
  participant R as routes/features_substitutions
  participant S as SchoolStore
  participant E as EventBus / SSE
  participant N as notify.py
  participant V as substitution.compute_day_plan
  participant U as Sekretariat / Plan-Ansicht
  L->>R: POST /absences/report-self (heute, max. 6 Wochen)
  R->>S: mutate(Absence anlegen, scope absences+substitutions)
  S->>E: change {version, scope, dates}
  S-->>R: Version + Audit plan.change
  R->>N: kick()
  E-->>U: SSE change → Seiten laden neu
  U->>R: GET /substitutions?date=…
  R->>V: day_plan (gecacht je Version)
  V-->>U: DayPlan: Vertretung / Entfall an den Rändern / Verlegung / Aufsicht
  N->>V: Plan heute + nächster Schultag mit letztem Stand vergleichen
  N-->>N: Änderung → notifications_outbox (E-Mail, Webhook)
  Note over U,V: Sekretariat kann Kandidaten wählen (GET /substitutions/candidates) und per POST /overrides entscheiden
  participant K as Klassenbuch (routes/features_register)
  participant D as DB
  U->>K: GET /register/day?class_id&date
  K->>V: effective_cells (tatsächlicher Plan inkl. Vertretung/Entfall)
  K->>D: Krankmeldungen vorausfüllen (student_absences)
  U->>K: PUT /register/lesson (Anwesenheit, Thema, Hausaufgabe)
  K->>D: register_lessons (verschlüsselt) + student_absences (source=lehrkraft, register_id)
  K->>E: publish change [register, student_absences]
  U->>R: GET /timetable/{kind}/{ref} bzw. /calendar/week
  R-->>U: Plan der Woche mit Änderungen und fälligen Hausaufgaben
```

Schüler/Eltern können selbst melden (`POST /student-absences`); Minderjährige nie selbst, Volljährige und Eltern nach den Regeln aus [[Server elternzugriff]]. Das Klassenbuch legt Fehlen/Verspätung als offene Fehlzeit an, entschuldigt wird erst durch Eltern/Volljährige plus Bestätigung.

## 4. Kursraum: Material und Hausaufgabe

Beteiligt: [[Feature channels]], [[Routen features_channels]], [[Modul channels]], [[Routen files]], [[Server files]], [[Routen features_calendar]], [[Routen features_grades]].

```mermaid
sequenceDiagram
  autonumber
  participant T as Lehrkraft (Kursraum)
  participant C as routes/features_channels
  participant F as routes/files + files.py
  participant DB as DB (channel_items, assignment_submissions)
  participant S as Schüler/in
  participant W as /calendar/week
  T->>F: POST /files (Upload, verschlüsselt, Typprüfung, optional ClamAV)
  F-->>T: file_id
  T->>C: POST /channels/{id}/items (Aufgabe mit Frist, Sichtbarkeit nach Zeitpunkt/Stunde)
  C->>DB: channel_items (Beschreibung verschlüsselt als body_enc, file_id)
  C-->>T: Aufgabe angelegt (change-Ereignis mit Scope channel:ID:)
  S->>C: GET /channels/{id} (nur sichtbares Material)
  S->>C: POST /channels/{id}/items/{item}/viewed
  S->>F: POST /files (Abgabe)
  S->>C: PUT /channels/{id}/items/{item}/submission
  C->>DB: assignment_submissions
  T->>C: GET /channels/{id}/items/{item}/submissions
  T->>C: PUT /channels/{id}/submissions/{sid}/feedback (Rückmeldung, Note)
  S->>W: Stundenplan/Woche zeigt fällige Hausaufgaben (homework_due)
  S->>C: GET /grades (bewertete Aufgaben, features_grades)
```

Eltern sehen Kursräume ihrer Kinder nur nach `parent_access` (A-44/A-46); Schulbegleitung wie das begleitete Kind. Live-Updates nutzen Scopes mit Doppelpunkt am Ende (`channel:5:`), weil Scopes per Präfix in beide Richtungen verglichen werden.

## 5. Lizenzprüfung

Beteiligt: [[Server licensing]], [[Server deps]], [[Routen license]], [[Seite LicensePage]], [[Lizenzserver]], [[Server runtime]].

```mermaid
sequenceDiagram
  autonumber
  participant A as Admin (LicensePage)
  participant R as routes/license.py
  participant LI as licensing.py (Schul-Server)
  participant LS as Lizenzserver
  participant D as deps._guard_license
  A->>R: PUT /license (Lizenzdatei, Recht system.admin)
  R->>LI: install – Ed25519-Signatur mit SM_LICENSE_PUBKEY prüfen
  LI->>LS: POST check_url der Lizenz (…/api/v1/check) {license_id, instance_id, version, students, users, nonce}
  LS-->>LI: {result: active|revoked|expired|unknown, nonce, …} + Signatur
  LI->>LI: Signatur und Nonce prüfen, Stand speichern (data_dir/license_state.json)
  loop Hintergrundschleife (runtime.startup → licensing.start)
    LI->>LS: regelmäßige Bestätigung
  end
  Note over LI: Zustände valid / grace (Kulanz grace_days) / readonly / missing / invalid
  A->>R: beliebige POST/PUT/PATCH/DELETE
  R->>D: _guard_license(request)
  D->>LI: status()["read_only"]?
  D-->>A: bei Sperre 4xx – Lesen bleibt möglich
```

Konten-Obergrenze: `licensing.user_limit` (nur mit `SM_LICENSE_ENFORCE`). Die Sauber-Instanz läuft mit Durchsetzung, siehe [[Betrieb und Deploy]].

## 6. Live-Update über SSE

```mermaid
sequenceDiagram
  autonumber
  participant B1 as Browser A
  participant B2 as Browser B
  participant R as Fach-Route
  participant S as store.mutate / publish_change
  participant E as EventBus
  B1->>E: GET /api/v1/events (eine Verbindung je Tab, Reconnect automatisch)
  B2->>E: GET /api/v1/events
  B1->>R: PUT/POST … (Änderung)
  R->>S: mutate(user, Text, fn, scope, dates) bzw. DB-Schreiben + publish_change
  S->>E: publish change {version, scope, dates}
  E-->>B1: SSE change
  E-->>B2: SSE change
  Note over B2: useApi(…, {live:[scope]}) lädt nur passende Daten neu, useCollection invalidiert den Cache
```

Details: [[Server events]], [[Frontend Basis]] (`useLive`, `useApi`), [[Frontend API-Schicht]] (`events.ts`).

<!-- eigene Notizen -->
