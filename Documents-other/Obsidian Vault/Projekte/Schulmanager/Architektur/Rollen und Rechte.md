---
tags: [schulmanager, architektur, rechte]
quelle: "schulmanager/server/permissions.py, rights.py, deps.py, routes/rights.py"
stand: 2026-10-12 21:35
generator: schulmanager-regen
---

# Rollen und Rechte

> Einstieg: [[Schulmanager Architektur]] · Code: [[Server permissions]], [[Server rights]], [[Server deps]] · API: [[Routen rights]] · Oberfläche: [[Seite RightsPage]]

## Drei Ebenen

1. **Rolle** (`users.role`) – grobe Funktion im Haus.
2. **Recht** (z. B. `students.read`) – was eine Rolle tun darf; Katalog an einer Stelle (`CATALOGUE`).
3. **Umfang** (Scope, z. B. `own_classes`) – auf welche Daten sich ein Recht bezieht.

Dazu kommen Zuordnungen (Lehrkraft-Kürzel, Kinder, Zweige) und feste Mindestregeln (Datenschutz), die keine Schul-Einstellung aushebeln kann. Klassenleitung ist **keine** Kontorolle, sondern folgt aus `SchoolClass.class_teacher` im Planungsdokument.

## Rollen

| Rolle (`id`) | Bezeichnung | Art | Rechte (Standard) | Beschreibung |
|---|---|---|---|---|
| `admin` | Administration | tech | 37 | Technischer Betrieb: Konten, Einstellungen, Sicherungen. Sieht keine Gesundheitsdaten. |
| `schulleitung` | Schulleitung | staff | 42 | Leitet die Schule: sieht und verwaltet nahezu alles, vergibt Rollen und Rechte. |
| `abteilungsleitung` | Abteilungsleitung | staff | 24 | Leitet einen Schulzweig (Abteilung): wie Lehrkraft, aber mit Blick auf alle Klassen des eigenen Zweigs. |
| `planer` | Stundenplanung | staff | 21 | Stundenplanung: Stundenplan erstellen und ändern, Vertretungen, Klausuren. |
| `sekretariat` | Sekretariat | staff | 27 | Verwaltung: Stammdaten, Krankmeldungen, Mitteilungen, Konten von Schülern/Eltern. |
| `lehrer` | Lehrkraft | staff | 22 | Unterricht: eigener Plan, eigene Kurse und Klassen; als Klassenleitung zusätzlich die geleitete Klasse. |
| `hausmeister` | Hausmeister/in | limited | 3 | Haustechnik: Raumpläne und Anzeige, keine Schülerdaten. |
| `schulbegleitung` | Schulbegleitung | child | 2 | Begleitet ein Kind im Schulalltag: sieht dessen Stundenplan, Kursräume und Material – ohne Elternrechte (keine Krankmeldung). |
| `schueler` | Schüler/in | child | 4 | Eigener Plan, Kursräume, Postfach. |
| `eltern` | Eltern | child | 6 | Pläne und Krankmeldung der eigenen Kinder. |
| `monitor` | Monitor (Anzeige) | display | 1 | Anzeigegerät (Vertretungsplan im Foyer). |
| `zuschauer` | Zuschauer/in (nur lesen) | display | 39 | Vorführ-/Prüfzugang: sieht wie Leitung/Planung/Sekretariat, ändert nichts. |

Hierarchie der Personalrollen: lehrer → klassenleitung → abteilungsleitung → sekretariat → schulleitung. Kindrollen (Konten verwaltbar durch Sekretariat): eltern, schueler, schulbegleitung. Schreibgeschützt: zuschauer (`deps._guard_read_only`).

## Rechte-Katalog und Standardzuordnung

Zellen: ✔ = Recht vorhanden, mit Umfang in Klammern. Status „geplant“ = angelegt und einstellbar, die Funktion prüft aber noch das ältere Recht.

Spalten: **adm** = Administration, **SL** = Schulleitung, **AL** = Abteilungsleitung, **plan** = Stundenplanung, **sek** = Sekretariat, **lehr** = Lehrkraft, **hm** = Hausmeister/in, **begl** = Schulbegleitung, **sch** = Schüler/in, **elt** = Eltern, **mon** = Monitor (Anzeige), **zus** = Zuschauer/in (nur lesen)

### Pläne & Stammdaten

| Recht | Bedeutung | Status | adm | SL | AL | plan | sek | lehr | hm | begl | sch | elt | mon | zus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `plans.read_all` | Pläne lesen | aktiv | ✔ | ✔ | ✔ (own_branch) | ✔ | ✔ | ✔ (own_classes) |  |  |  |  |  | ✔ |
| `rooms.read` | Raumpläne lesen | aktiv | ✔ | ✔ |  | ✔ | ✔ |  | ✔ |  |  |  |  | ✔ |
| `masterdata.read` | Stammdaten lesen | geplant | ✔ | ✔ |  | ✔ | ✔ |  |  |  |  |  |  | ✔ |
| `masterdata.edit` | Stammdaten bearbeiten | aktiv | ✔ | ✔ |  | ✔ | ✔ |  |  |  |  |  |  | ✔ |
| `timetable.generate` | Stundenplan generieren | aktiv | ✔ |  |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `timetable.edit` | Stundenplan bearbeiten | aktiv | ✔ |  |  | ✔ |  |  |  |  |  |  |  | ✔ |

### Vertretung & Aufsicht

| Recht | Bedeutung | Status | adm | SL | AL | plan | sek | lehr | hm | begl | sch | elt | mon | zus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `substitution.read` | Vertretungsplan lesen | aktiv | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  | ✔ |  |  |  | ✔ |
| `substitution.edit` | Vertretungen bearbeiten | aktiv | ✔ | ✔ |  | ✔ | ✔ |  |  |  |  |  |  | ✔ |
| `substitution.self_study` | Eigenarbeit freigeben | geplant | ✔ | ✔ | ✔ (own_branch) | ✔ |  |  |  |  |  |  |  | ✔ |
| `duties.manage` | Aufsichten verwalten | geplant | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `absence.report_self` | Eigene Krankmeldung | aktiv |  |  | ✔ |  |  | ✔ |  |  |  |  |  |  |
| `monitor.read` | Monitor-Ansicht | aktiv | ✔ | ✔ |  | ✔ | ✔ |  | ✔ |  |  |  | ✔ | ✔ |
| `monitor.manage` | Monitore einstellen | aktiv | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |

### Schüler, Klassenbuch & Prüfungen

| Recht | Bedeutung | Status | adm | SL | AL | plan | sek | lehr | hm | begl | sch | elt | mon | zus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `students.read` | Schülerdaten lesen | aktiv | ✔ | ✔ | ✔ (own_branch) | ✔ | ✔ | ✔ (own_classes) |  |  |  |  |  | ✔ |
| `students.birth_date` | Geburtsdatum pflegen | aktiv | ✔ | ✔ | ✔ (class_teacher) |  | ✔ | ✔ (class_teacher) |  |  |  |  |  | ✔ |
| `register.read_all` | Klassenbuch gesamt lesen | geplant | ✔ | ✔ | ✔ (own_branch) |  | ✔ |  |  |  |  |  |  | ✔ |
| `student_absence.report` | Schüler krankmelden | aktiv |  |  | ✔ (own_branch) |  | ✔ | ✔ (own_lessons) |  |  |  | ✔ (own_children) |  |  |
| `student_absence.read` | Krankmeldungen lesen | aktiv |  | ✔ | ✔ (own_branch) |  | ✔ | ✔ (class_teacher) |  |  | ✔ (own) | ✔ (own_children) |  | ✔ |
| `student_documents.read` | Atteste & Dokumente | aktiv |  | ✔ | ✔ (class_teacher) |  | ✔ | ✔ (class_teacher) |  |  |  | ✔ (own_children) |  | ✔ |
| `support.read` | Nachteilsausgleich & Förderung | aktiv |  | ✔ | ✔ (class_teacher) |  | ✔ | ✔ (class_teacher) |  |  |  |  |  | ✔ |
| `support.manage` | Nachteilsausgleich pflegen | aktiv |  | ✔ | ✔ (class_teacher) |  | ✔ | ✔ (class_teacher) |  |  |  |  |  | ✔ |
| `support.catalog` | Katalog der Merkmale | aktiv | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `support.hints` | Ausgleichs-Hinweis bei Klausuren | aktiv |  | ✔ | ✔ (own_courses) |  | ✔ | ✔ (own_courses) |  |  |  |  |  | ✔ |
| `exam.edit` | Klausuren bearbeiten | aktiv | ✔ | ✔ | ✔ (own_courses) | ✔ |  | ✔ (own_courses) |  |  |  |  |  | ✔ |
| `exam.types.manage` | Klausurarten verwalten | geplant | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |

### Kommunikation & Kursräume

| Recht | Bedeutung | Status | adm | SL | AL | plan | sek | lehr | hm | begl | sch | elt | mon | zus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `forms.submit` | Formulare ausfüllen | aktiv |  | ✔ | ✔ |  | ✔ | ✔ |  |  | ✔ | ✔ |  |  |
| `forms.inbox` | Formular-Eingang | aktiv |  | ✔ | ✔ (class_teacher) |  | ✔ | ✔ (class_teacher) |  |  |  |  |  | ✔ |
| `forms.manage` | Formulare gestalten | aktiv | ✔ | ✔ |  |  | ✔ |  |  |  |  |  |  | ✔ |
| `announcement.post` | Mitteilungen veröffentlichen | aktiv | ✔ | ✔ | ✔ (own_branch) | ✔ | ✔ | ✔ (own_classes) |  |  |  |  |  | ✔ |
| `messages.use` | Postfach nutzen | aktiv | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  | ✔ | ✔ |  | ✔ |
| `messages.broadcast` | An Gruppen senden | aktiv | ✔ | ✔ | ✔ (own_branch) | ✔ | ✔ | ✔ (own_classes) |  |  |  |  |  | ✔ |
| `messages.moderate` | Gemeldete Nachrichten prüfen | aktiv | ✔ | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `chats.review` | Gemeldete Chat-Auszüge | geplant |  | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `channels.use` | Kursräume nutzen | aktiv | ✔ | ✔ | ✔ |  |  | ✔ |  | ✔ | ✔ |  |  | ✔ |
| `channels.view_children` | Kursräume der Kinder lesen | aktiv |  |  |  |  |  |  |  |  |  | ✔ (own_children) |  |  |
| `channels.manage` | Kursräume verwalten | aktiv | ✔ | ✔ | ✔ (own_courses) |  |  | ✔ (own_courses) |  |  |  |  |  | ✔ |

### Konten & Profile

| Recht | Bedeutung | Status | adm | SL | AL | plan | sek | lehr | hm | begl | sch | elt | mon | zus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `users.manage` | Konten verwalten | aktiv | ✔ | ✔ (no_admins) |  |  | ✔ (students_parents) |  |  |  |  |  |  | ✔ |
| `passwords.reset` | Passwörter zurücksetzen | aktiv | ✔ | ✔ | ✔ (class_teacher) |  | ✔ | ✔ (class_teacher) |  |  |  |  |  | ✔ |
| `profile.teacher_self` | Eigenes Lehrerprofil | aktiv |  |  | ✔ |  |  | ✔ |  |  |  |  |  |  |
| `teacher_requests.review` | Profil-Anträge prüfen | aktiv | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |

### Verwaltung & System

| Recht | Bedeutung | Status | adm | SL | AL | plan | sek | lehr | hm | begl | sch | elt | mon | zus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `settings.edit` | Einstellungen bearbeiten | aktiv | ✔ | ✔ |  | ✔ |  |  |  |  |  |  |  | ✔ |
| `rights.manage` | Rollen & Rechte verwalten | aktiv | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |
| `login_policy.manage` | Anmelde-Richtlinien | aktiv | ✔ | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `audit.read` | Protokoll lesen | aktiv | ✔ | ✔ |  |  |  |  |  |  |  |  |  | ✔ |
| `history.restore` | Verlauf & Wiederherstellung | aktiv | ✔ | ✔ |  | ✔ (history_only) |  |  |  |  |  |  |  | ✔ |
| `system.admin` | Systemverwaltung | aktiv | ✔ |  |  |  |  |  |  |  |  |  |  |  |
| `license.manage` | Lizenz verwalten | geplant | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |
| `api.own` | Eigene API-Zugänge | aktiv | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |  |  |  |
| `api.manage` | API-Zugänge verwalten | aktiv | ✔ | ✔ |  |  |  |  |  |  |  |  |  |  |

Umfänge: `all` = Alle, `own_classes` = Eigene Klassen, `own_courses` = Eigene Kurse, `class_teacher` = Eigene Klassenleitung, `own_branch` = Eigener Zweig, `own` = Nur selbst, `own_children` = Eigene Kinder, `no_admins` = Ohne Administration, `students_parents` = Nur Schüler/Eltern, `history_only` = Nur Verlauf, `own_lessons` = Eigene Stunden

## Wie die Prüfung abläuft

1. **Anmeldung** – [[Server deps]] `authenticate`: Bearer-Token oder Cookie `sm_session`; bei ändernden Methoden zusätzlich Header `X-CSRF-Token`.
2. **Rechte laden** – `build_auth_user` berechnet über [[Server permissions]] `effective_rights` die wirksamen Rechte und Umfänge: Standard (`ROLE_PERMISSIONS`) → Schul-Abweichungen aus `role_overrides` ([[Server rights]], bei jeder Anfrage gelesen, wirkt sofort) → feste Regeln (`LOCKED_GRANT`, `LOCKED_DENY`, `ASSIGNABLE_ONLY`, `SCOPE_LIMIT`). Minderjährige Schüler erhalten nie Erwachsenen-Rechte (Flag `users.adult`).
3. **Globale Schutzschalter** – `_guard_read_only` (Rolle `zuschauer` darf nichts ändern), `_guard_demo` (öffentliche Demo schützt Demo-Konten/Admin/Mail), `_guard_license` (gesperrte Lizenz → nur lesen, siehe [[Server licensing]]).
4. **Recht je Endpunkt** – `Depends(require("recht"))` liefert den `AuthUser` oder 403. Viele Endpunkte nutzen nur `current_user` und prüfen im Handler (`need(user, …)`, `has(user, …)`).
5. **Datenumfang im Router** – `require` prüft das Recht, **nicht** den Scope. Jeder Router filtert selbst mit den Hilfen aus [[Routen features_common]] (`reads_all_plans`, `is_scoped_teacher`, `plan_class_ids`, `students_in_scope`, `perm_scope`) und [[Server elternzugriff]] (`parent_may_see`). Fremde Daten antworten mit 404, nicht 403.
6. **Frontend** – `lib/permissions.ts` (`can`, `canAccessPath`, Menü) blendet nur aus; Flags der Antwort (`can_edit` …) statt Rollennamen verwenden ([[Frontend Basis]]).

## Feste Mindestregeln (nicht änderbar)

- Technische Administration: nie `student_documents.read`, `support.read`, `chats.review`; behält `users.manage`, `settings.edit`, `rights.manage`, `system.admin`.
- Schüler, Eltern, Schulbegleitung: nur kleine Positivliste (`ASSIGNABLE_ONLY`), Umfang `own`/`own_children`; Schulbegleitung ohne Elternrechte.
- Hausmeister: nur Raumpläne, Monitor, Postfach. Lehrkräfte: Pläne/Schülerdaten nur eigener Klassen, Atteste/Förderdaten nur als Klassenleitung. Abteilungsleitung: höchstens eigener Zweig.
- `rights.manage`, `license.manage`, `login_policy.manage`, `audit.read` nur Administration und Schulleitung; `system.admin` nur Administration.
- Minderjährige Schüler melden sich nie selbst krank.

## Auffälligkeiten

- Die Lizenz-Endpunkte ([[Routen license]]) prüfen `system.admin`; das Recht `license.manage` ist im Katalog als „geplant“ geführt.
- `docs/code/README.md` nennt noch „8 Rollen, 29 Rechte“ – der Code hat 12 Rollen und 49 Rechte.

## Siehe auch

[[Abläufe]] (Login) · [[Datenmodell]] (`role_overrides`, `branches`, `user_branches`, `parent_links`) · `docs/ROLLEN-RECHTE.md` im Repo

<!-- eigene Notizen -->
