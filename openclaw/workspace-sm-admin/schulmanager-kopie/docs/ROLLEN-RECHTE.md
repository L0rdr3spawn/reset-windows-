# Rollen & Rechte – Zielarchitektur

Stand: 2026-10-12. Code: `schulmanager/server/permissions.py` (Regeln), `server/rights.py` (Datenbank), `routes/rights.py` (API),
`frontend/src/pages/RightsPage.tsx` (Seite `/rechte`). Tests: `tests/test_rights.py`.

## 1. Grundidee

Drei Ebenen, strikt getrennt:

1. **Rolle** (Konto-Eigenschaft `users.role`) – grobe Funktion im Haus.
2. **Recht** (`permission`, z. B. `students.read`) – was eine Rolle tun darf. Der Katalog steht an einer Stelle (`CATALOGUE`).
3. **Umfang** (`scope`, z. B. `own_classes`) – auf welche Daten sich ein Recht bezieht.

Dazu kommen **Zuordnungen** (Lehrkraft-Kürzel, Kinder, Zweige) und **feste Mindestregeln** (Datenschutz), die keine
Einstellung aushebeln kann. Schulweite Entscheidungen (wer beaufsichtigt Pausenbereiche, ab welcher Klassenstufe darf eine
Klasse allein arbeiten, Postfach-Regeln) gehören zu Rechten der Verwaltung bzw. in die zentralen Einstellungen – nie zur
Lehrkraft.

## 2. Rollenhierarchie

```
Lehrkraft → Klassenleitung → Abteilungsleitung → Sekretariat / Schulleitung      (+ Administration technisch)
Außerhalb der Reihe: Stundenplanung, Hausmeister/in, Schulbegleitung, Schüler/in, Eltern, Monitor, Zuschauer
```

| Rolle (`id`) | Zweck | Zuordnung |
|---|---|---|
| `admin` Administration | Technik: Konten, Einstellungen, Sicherungen. Nie Gesundheitsdaten | – |
| `schulleitung` | alles Fachliche, vergibt Rechte | – |
| `sekretariat` | Verwaltung, Krankmeldungen, Konten für Schüler/Eltern/Begleitung | – |
| `planer` Stundenplanung | Plan, Vertretung, Klausuren | – |
| `abteilungsleitung` | wie Lehrkraft, plus alle Klassen des eigenen **Zweigs** | Lehrkraft-Kürzel (optional), Zweige |
| `lehrer` Lehrkraft | eigener Unterricht, eigene Klassen/Kurse | Lehrkraft-Kürzel |
| `hausmeister` | Raumpläne, Monitor, Postfach – keine Schülerdaten | – |
| `schulbegleitung` | begleitet ein Kind: dessen Plan, Kursräume, Material, Abgaben – keine Elternrechte | begleitete Kinder |
| `schueler` / `eltern` | eigene Daten bzw. Daten der Kinder | Schüler bzw. Kinder |
| `monitor` | Anzeige des Vertretungsplans | Standort |
| `zuschauer` | Vorführzugang, lesend wie Leitung/Planung/Sekretariat, ändert nie etwas | – |

**Klassenleitung ist keine Kontorolle.** Sie ergibt sich aus den Stammdaten (`SchoolClass.class_teacher`). Eine Lehrkraft, die
eine Klasse leitet, bekommt dort automatisch mehr Sicht (Plan der Klasse und ihrer Schüler, Klassenbuch-Übersicht, Atteste der
eigenen Klasse – Umfang `class_teacher`). So gibt es keine doppelte Pflege. „Ihre Rolle“ im Profil zeigt z. B.
*Lehrkraft · Klassenleitung 5a*; Abteilungsleitung zeigt *Abteilungsleitung · Zweig Unterstufe*.

**Zweig (Abteilung).** Tabelle `branches`: Name, Standorte, Klassenstufen, einzelne Klassen (eine Klasse gehört zum Zweig, wenn
eines davon passt). Konto ↔ Zweig in `user_branches`. Umfang `own_branch` = eigene Klassen + Klassen der Zweige.

**Schulbegleitung.** Verknüpfung mit Kindern über `parent_links` (wie Eltern). Technisch erscheint das erste Kind als
`student_id`, damit Kursräume und Pläne wie beim Kind greifen; alle Kinder stehen in `student_ids`.

## 3. Rechtekatalog

Status: **aktiv** = der Server prüft das Recht; **geplant** = angelegt, einstellbar und in der Matrix sichtbar, die zugehörige
Funktion prüft aber noch das ältere Recht (Kennzeichnung in der Oberfläche).

| Bereich | Recht | Beschreibung | Umfänge (außer „alle“) | Standardrollen | Status |
|---|---|---|---|---|---|
| Pläne & Stammdaten | `plans.read_all` | Klassen-/Lehrer-/Schülerpläne lesen | `own_classes`, `own_branch` | admin, SL, Planer, Sekr., Lehrkraft (own_classes), AL (own_branch) | aktiv |
| | `rooms.read` | Raumpläne und -belegung | – | admin, SL, Planer, Sekr., Hausmeister | aktiv |
| | `masterdata.read` | Stammdaten lesen (ohne alle Pläne) | – | admin, SL, Planer, Sekr. | geplant |
| | `masterdata.edit` | Stammdaten ändern | – | admin, SL, Planer, Sekr. | aktiv |
| | `timetable.generate` / `timetable.edit` | Plan erzeugen / bearbeiten | – | admin, Planer | aktiv |
| Vertretung & Aufsicht | `substitution.read` | Vertretungsplan ansehen (Seite, API, Startseiten-Kachel); Schüler/innen und Eltern haben es nicht – sie sehen Änderungen im eigenen Stundenplan | – | alle Personal-Rollen, Schulbegleitung | aktiv |
| | `substitution.edit` | Abwesenheiten, Vertretungen | – | admin, SL, Planer, Sekr. | aktiv |
| | `substitution.self_study` | Eigenarbeit freigeben (Klassenstufen-Schwelle in der Verwaltung) | `own_branch` | SL, Planer, AL | geplant |
| | `duties.manage` | Pausenbereiche, Verfügbarkeit, faire Verteilung | – | admin, SL, Planer | geplant |
| | `absence.report_self` | Lehrkraft meldet sich krank | – | Lehrkraft, AL | aktiv |
| | `monitor.read` / `monitor.manage` | Monitor anzeigen / einstellen | – | SL, Sekr., Planer (read), Hausmeister (read) | aktiv |
| Schüler, Klassenbuch, Prüfungen | `students.read` | Schülerdaten | `own_classes`, `own_branch` | admin, SL, Planer, Sekr., Lehrkraft/AL (eingeschränkt) | aktiv |
| | `register.read_all` | Klassenbuch gesamt (Fachlehrkraft: nur eigene Stunden, Klassenleitung: ganze Klasse bleibt in Kraft) | `own_branch`, `class_teacher` | SL, Sekr., AL | geplant |
| | `student_absence.read` / `.report` | Krankmeldungen lesen / eintragen | `own_classes`, `own_branch`, `own`, `own_children` | Sekr., Lehrkraft, Eltern, Schüler (own) | aktiv |
| | `student_documents.read` | Atteste/Dokumente (Gesundheitsdaten) | `class_teacher`, `own`, `own_children` | SL, Sekr., Lehrkraft (Klassenleitung), Eltern | aktiv |
| | `support.read` | Nachteilsausgleich/Förderung samt Nachweisen (Vollsicht), getrennt von `students.read` | `class_teacher`, `own_branch` | SL, Sekr., Lehrkraft (Klassenleitung) | aktiv |
| | `support.manage` | Merkmale, Nachteilsausgleiche und Nachweise je Schüler/in pflegen | `class_teacher` | SL, Sekr., Lehrkraft (Klassenleitung der eigenen Klasse) | aktiv |
| | `support.catalog` | Katalog der Merkmale (Zeitzuschlag, ADHS …; je Art „für Lehrkräfte sichtbar“) | – | admin, SL, Sekr. | aktiv |
| | `support.hints` | Hinweis bei Klausuren/Tests: wer hat welchen Ausgleich (nur Art, Minuten, Fächer, Hilfsmittel) | `own_courses` | SL, Sekr., Lehrkraft/AL (eigene Kurse und Klassenleitung) | aktiv |
| | `exam.edit` | Klausuren | `own_courses` | SL, Planer, Lehrkraft | aktiv |
| | `exam.types.manage` | Klausurarten verwalten | – | SL, Planer | geplant |
| | `gradebook.use` | Notenbuch führen: Noten, Leistungsarten, Gewichtung, Halbjahresnoten festlegen und sperren (`docs/NOTENBUCH.md`) | `own_courses` | SL, Lehrkraft/AL (eigene Kursteile) | aktiv |
| | `gradebook.read_class` | Notenübersicht, Notenkonferenz-Liste und Versetzungswarnung der Klasse lesen | `class_teacher`, `own_branch` | SL, Lehrkraft/AL (Klassenleitung) | aktiv |
| | `gradebook.manage` | Notenskalen, Notenschlüssel, Einsicht und Warnschwellen einstellen; gesperrte Notenbücher öffnen | – | SL | aktiv |
| | `gradebook.export` | Gesperrte Halbjahresnoten als CSV für SchILD/ASV/LUSD ausgeben | – | SL, Sekr. | aktiv |
| Kommunikation | `announcement.post` | Mitteilungen | `own_classes`, `own_branch` | SL, Planer, Sekr., Lehrkraft | aktiv |
| | `messages.use` / `.broadcast` / `.moderate` | Postfach, Gruppennachrichten, Meldungen prüfen | `own_classes`, `own_branch` (broadcast) | je nach Rolle | aktiv |
| | `chats.review` | gemeldete Chat-Auszüge – nur mit Einwilligung von Kind/Eltern | – | SL | geplant |
| | `channels.use` / `channels.manage` | Kursräume | `own_courses` (manage) | alle Beteiligten / Lehrkraft, SL | aktiv |
| | `channels.trash` | Kursraum-Papierkorb: gelöschtes Material, Aufgaben und Ordner wiederherstellen oder endgültig löschen (Löschen selbst gehört zu `channels.manage`; Aufbewahrung: `trash_retention_days`, Standard 30 Tage, siehe `docs/LERNFORTSCHRITT.md`) | `own_courses` | admin, SL, Lehrkraft/AL (eigene Kurse) | aktiv |
| | `forms.submit` | Formulare der Schule ausfüllen (Zielgruppe bestimmt das Formular, siehe `docs/FORMULARE.md`) | – | SL, Sekr., Lehrkraft/AL, Eltern, Schüler | aktiv |
| | `forms.inbox` | Formular-Eingang: ansehen, genehmigen, exportieren (teils Gesundheitsdaten – nie Administration/Planung) | `class_teacher` | SL, Sekr., Lehrkraft/AL (Klassenleitung) | aktiv |
| | `forms.manage` | Formular-Vorlagen gestalten, Ablauf/Aktionen festlegen, Bibliothek – ohne Einblick in Einreichungen | – | admin, SL, Sekr. | aktiv |
| Schüler, Klassenbuch, Prüfungen | `competency.read` | Kompetenzraster und Lernstand ansehen (Klassenübersicht, Lernpläne, Abzeichen, Lernentwicklungsbericht); Schüler/innen und Eltern sehen das Kind ohne dieses Recht (Eltern volljähriger Kinder nur mit Freigabe „Lernstand“) | `own_classes`, `own_branch` | SL, Lehrkraft/AL (eingeschränkt) | aktiv |
| | `competency.assess` | Stufe je Kompetenz setzen, Selbsteinschätzung bestätigen, Lernpläne führen, Abzeichen vergeben | `own_classes`, `own_branch` | SL, Lehrkraft/AL (eingeschränkt) | aktiv |
| | `competency.manage` | Kompetenzrahmen anlegen/importieren/ändern, Abzeichen der Schule definieren – ohne Einblick in Lernstände | – | SL, Lehrkraft, AL | aktiv |
| Konten | `users.manage` | Konten verwalten | `no_admins`, `students_parents` | admin, SL (no_admins), Sekr. (students_parents) | aktiv |
| | `profile.teacher_self`, `teacher_requests.review` | Eigenes Profil als Antrag / Anträge prüfen | – | Lehrkraft / SL, Planer | aktiv |
| Verwaltung & System | `settings.edit` | Einstellungen (auch Postfach-Regeln) | – | admin, SL, Planer | aktiv |
| | `rights.manage` | diese Seite bearbeiten | – | admin, SL | aktiv |
| | `login_policy.manage`, `audit.read`, `history.restore` | Anmelderegeln, Protokoll, Verlauf | `history_only` | admin, SL (Planer: Verlauf) | aktiv |
| | `privacy.manage` | Löschkonzept: Aufbewahrungsfristen, Warteliste „ausgetreten“, Vorschau, Löschprotokoll (nur Zahlen, keine Inhalte), siehe `docs/DATENSCHUTZ-LOESCHKONZEPT.md` | – | admin, SL | aktiv |
| | `privacy.subject` | Betroffenenrechte: Auskunft für eine Person als ZIP (Art. 15/20) und Sofort-Löschen (Art. 17, mit Bestätigung und Audit); enthält Gesundheits-/Notendaten, daher nie die technische Administration | – | SL | aktiv |
| | `mail.custom_server` | Im Postfach ein E-Mail-Konto mit **eigenem IMAP-/SMTP-Server** verbinden (bekannte Anbieter wie Google/GMX stehen allen mit Postfach offen; die Server-Adressen sind dort fest). Nur Personal; der Server prüft Ziel und Port (SSRF-Schutz, `SM_OUTBOUND_ALLOW`) | – | admin, SL, Sekr. | aktiv |
| | `system.admin` | Sicherungen, Schlüssel, Demo | – | admin | aktiv |
| | `license.manage` | Lizenz einspielen/prüfen, Vorwarnungen; auch bei gesperrter Lizenz erreichbar (Admin: fest vergeben) | – | admin, SL | aktiv |
| | `api.own` | Eigene API-Zugänge für Apps/KIs ausgeben (nur Bereiche/Filter, die das Konto selbst sieht; nie Gesundheits-/Förderdaten) | – | admin, SL, AL, Planer, Sekr., Lehrkraft | aktiv |
| | `api.manage` | Alle API-Zugänge sehen, Nutzung prüfen, widerrufen | – | admin, SL | aktiv |

## 4. Anpassung pro Schule

* Tabelle `role_overrides (role, permission, granted, scope, updated_at, updated_by)`. Eine Zeile = Abweichung vom Standard
  (`scope`: leer = Standardumfang, `all` = uneingeschränkt, sonst Umfang). Keine Zeile = Standard; „zurücksetzen“ löscht Zeilen.
* `effective_rights(rolle, adult, overrides)` rechnet **Standard → Abweichungen → feste Regeln** aus. Abweichungen, die gegen eine
  feste Regel verstoßen (z. B. nach einem Programm-Update), werden ignoriert.
* `deps.build_auth_user` lädt die Abweichungen der eigenen Rolle bei jeder Anfrage (kleine Tabelle) – Änderungen wirken sofort,
  auch bei mehreren Serverprozessen. `AuthUser.scope()` liefert die wirksamen Umfänge.
* API: `GET /api/v1/rights` (Katalog, Rollen, Matrix mit Standard/wirksam/gesperrt, feste Regeln),
  `PUT /rights/roles/{rolle}` (`{"permissions": {recht: {"granted": bool, "scope": …} | null}}`), `POST /rights/roles/{rolle}/reset`,
  Zweige `GET/POST/PUT/DELETE /rights/branches`, Zuordnungen `GET /rights/assignments`, `PUT /rights/assignments/{konto}`,
  `GET /rights/me`. Lesen mit `rights.manage`, `users.manage` oder `audit.read`; Ändern nur mit `rights.manage`
  (Administration, Schulleitung). Zuordnungen auch mit `users.manage` (Sekretariat nur für Schulbegleitung). Jede Änderung ist
  im Audit-Protokoll (`rights.update`, `rights.reset`, `rights.assign`, `branch.*`).
* `GET /api/v1/roles` (Benutzerverwaltung) liefert jetzt die **wirksame** Matrix.

## 5. Feste Mindestregeln (nicht änderbar)

Im Code: `LOCKED_GRANT`, `LOCKED_DENY`, `ASSIGNABLE_ONLY`, `RESTRICTED_TO`, `SCOPE_LIMIT`; in der Oberfläche mit Schloss.

* Technische Administration: nie `student_documents.read`, `support.read`, `chats.review`, keine Krankmeldungen/Profile von Lehrkräften.
* Administration behält `users.manage`, `settings.edit`, `rights.manage`, `system.admin` (Schutz vor Aussperrung).
* Schüler, Eltern, Schulbegleitung: erhalten ausschließlich eine kleine Positivliste (`ASSIGNABLE_ONLY`) und sehen nur `own`
  bzw. `own_children`; nie andere Kinder, nie Personalrechte.
* Schulbegleitung: keine Elternrechte (`student_absence.report`, `student_documents.read` ausgeschlossen).
* Hausmeister: nur Raumpläne, Monitor, Postfach.
* Lehrkräfte: Pläne und Schülerdaten nur eigener Klassen (`own_classes`), Atteste/Förderdaten nur als Klassenleitung.
* Abteilungsleitung: höchstens eigener Zweig; Atteste/Förderdaten nur als Klassenleitung.
* Rechte-, Lizenz-, Anmelde-, Protokoll-Rechte nur für Administration und Schulleitung; `system.admin` nur Administration.
* Zuschauer ist schreibgeschützt (`deps._guard_read_only`, nicht konfigurierbar); Monitor zeigt nur `monitor.read`.
* Minderjährige Schüler melden sich nie selbst krank. Volljährig ist, wer laut Geburtsdatum (Stammdaten) 18 ist; nur ohne Geburtsdatum zählt das Konto-Flag „volljährig“. Das Geburtsdatum pflegen Sekretariat, Schulleitung, Administration und die Klassenleitung der eigenen Klasse (Recht `students.birth_date`, Klassenleitung mit Umfang „Eigene Klassenleitung“); der „Krank melden“-Knopf erscheint nur mit `student_absence.report` und fehlt damit bei Minderjährigen.
* Elternfreigabe ab 18 (`parent_access.py`): einstellbar sind Kursräume (inkl. Hausaufgaben), Stundenplan, Krankmeldungen/Fehlzeiten, Dokumente/Atteste, Mitteilungen und Noten; zusätzlich „Informationen der Schule gehen an: mich / meine Eltern / beide“ (Rundschreiben im Postfach, Standard ab 18: nur an die Person selbst; Tabelle `student_prefs`, Migration `0025_student_prefs`). Fehlzeiten-Statistik: `GET /absence-stats` – gleiche Sichtbarkeit wie die Fehlzeiten-Übersicht (Schüler/in, Eltern mit Freigabe „Krankmeldungen“, Klassenleitung, Sekretariat, Schulleitung; nie Fachlehrkräfte, nie die technische Administration).

## 6. Migration vom bisherigen Modell

* Alembic `0016_rights` legt `role_overrides`, `branches`, `user_branches` an. Keine Datenumstellung nötig: ohne Zeilen gelten
  die Standardwerte, die den bisherigen entsprechen.
* Bestehende Rollen-Strings und Rechte-IDs bleiben gültig. `ROLE_PERMISSIONS`/`PERMISSION_SCOPES` sind weiterhin die
  **Standardwerte** (u. a. von `messaging.py` zur Importzeit genutzt); zur Laufzeit gilt `AuthUser.permissions`/`scope()`.
* Neue Rechte wurden ergänzt (siehe Katalog); neue Rollen: `abteilungsleitung`, `hausmeister`, `schulbegleitung`.
* `support.read` wirkt jetzt (Nachteilsausgleich & Förderung, Migration `0023_support_catalog`): Vollsicht nur Schulleitung, Sekretariat, Klassenleitung der eigenen Klasse sowie Schüler/in selbst bzw. Eltern (Volljährige nur mit Freigabe „Dokumente“). Fachlehrkräfte (`support.hints`) sehen nur die Ausgleichsart – nie Diagnose, Details oder Nachweise; welche Katalogarten Lehrkräfte sehen, legt die Schule im Katalog fest („für Lehrkräfte sichtbar“). Die technische Administration hat `support.read/manage/hints` nie (`_ADMIN_DENIED`); Zugriffe und Änderungen stehen im Audit-Protokoll (`student_support.read/create/update/delete`, `support_catalog.*`).

## 7. Einrichtungsassistent (`/einrichtung`)

Schritt 8 „Rollen & Rechte“ verweist auf `/rechte`. Dort prüft die Schule: (1) Standardrechte je Rolle (Spalten), (2) Zweige
anlegen, (3) Konten von Abteilungsleitung und Schulbegleitung zuordnen. Fragen, die sich daraus ergeben: *Gibt es Abteilungen/Zweige?
Welche Klassen gehören dazu? Sollen Lehrkräfte Mitteilungen an alle Klassen senden? Wer prüft gemeldete Nachrichten? Wer verteilt Aufsichten?*

## 8. Offen / Folgearbeiten

* Funktionen mit Status „geplant“ müssen ihr neues Recht prüfen (statt des älteren): Stammdaten lesen, Klassenbuch gesamt, Förderdaten,
  Eigenarbeit, Aufsichten, Klausurarten, Chat-Meldungen, Lizenz.
* Abteilungsleitung: Pläne, Schülerdaten, Krankmeldungen, Mitteilungen sind angebunden; Klassenbuch-Übersicht, Lehrerpläne des Zweigs
  und Vertretung je Zweig stehen aus.
* Schulbegleitung mit mehreren Kindern: Kursräume gelten bisher für das erste Kind.
* Zentrale Einstellungen (Schüler dürfen Schülern schreiben, Aufbewahrung von Nachrichten) liegen noch im Postfach und sollten in die
  Schuleinstellungen umziehen.

## 9. Benachrichtigungen

Kein eigenes Recht: Jedes angemeldete Konto sieht und verwaltet nur die **eigenen** Benachrichtigungen und Einstellungen
(`/notifications`, Rest 404). Die **Schulvorgaben** (Standard je Ereignisart, Pflicht/gesperrt, Aufbewahrung) setzt, wer
`settings.edit` hat. Eltern erhalten Meldungen je Kind; bei volljährigen Kindern nur mit Freigabe über `parent_access`. Siehe
`docs/BENACHRICHTIGUNGEN.md`.

## Aufgaben im Kursraum (Raster, Fristen, Gruppen)

Keine neuen Rechte: Raster, Vorlagen, Fristverlängerung, Wiederabgabe, Gruppen und Sichtbarkeit nach Gruppe verwalten die
Lehrenden eines Kursraums mit `channels.manage` (bei Aufgaben in Klassenräumen nur, wer sie gestellt hat). Vorlagen sind
privat je Lehrkraft. Der Nachteilsausgleich-Hinweis in der Bewertungstabelle folgt `support.hints`/`support.read`
(nur Art und Minuten, nie Diagnosen). Eltern sehen das ausgefüllte Raster nur, wenn die Lehrkraft es freigibt.


## Lernaktivitäten (Abstimmung, Umfrage, Selbsttest)
Keine eigenen Rechte: Es gilt die Rolle im Kursraum (Lehrende legen an und werten aus, Teilnehmende nehmen teil, Eltern und Aufsicht lesen Abstimmungen). Details `docs/LERNAKTIVITAETEN.md` §1.
