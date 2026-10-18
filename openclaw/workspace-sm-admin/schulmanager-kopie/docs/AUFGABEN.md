# Aufgaben im Kursraum – Raster, Fristen, Wiederabgabe, Gruppen

Ergänzung zu `ARCHITECTURE.md` §9.4 (Kursräume). Code: `schulmanager/grading.py` (reine Logik),
`server/assignment_tools.py`, `server/channel_groups.py`, `server/routes/features_assignments.py`, Modelle
`feature_models/assignments.py` und `channel_groups.py`, Migration `0036_assignments_groups`; Oberfläche
`frontend/src/features/channels/assign/*` und `AssignmentsTab.tsx`. Tests: `tests/test_assignments.py`,
`assign/logic.test.ts`.

## Bewertung
* Je Aufgabe wählt die Lehrkraft (Knopf „Bewertung“): nur Freitext-Note, **Punkte** (Höchstpunktzahl), **Raster**
  (Kriterien mit Stufen und Punkten) oder **Leitfaden** (Kriterien mit Freitext und Höchstpunkten).
* Das Raster wird beim Zuweisen **kopiert** (spätere Änderungen an einer Vorlage ändern keine ausgefüllten Bewertungen).
  Nach der ersten Bewertung mit Raster lässt es sich nicht mehr ändern. Vorlagen (`/grading/templates`) sind privat je
  Lehrkraft, auch über Kursräume hinweg nutzbar.
* Beim Bewerten werden Stufen angeklickt bzw. Punkte je Kriterium eingetragen; Summe und **Note** ergeben sich nach
  Notenschlüssel. Es gibt keinen schulweiten Schlüssel: Voreinstellung „Noten 1–6“ (ab 92/81/67/50/30 %), dazu
  „Punkte 15–0“ oder eigene Prozentgrenzen je Aufgabe/Vorlage. Die Note ist ein Vorschlag und überschreibbar.
* Schüler/innen sehen die Kriterien vorab und nach der Bewertung das ausgefüllte Raster; Eltern nur bei Freigabe
  (`show_parents`), die Freitext-Note sehen sie wie bisher.
* **Bewertungstabelle** (Lehrende): Schüler/in × Status (abgegeben, verspätet, fehlt, bewertet; dazu „Überarbeitung“),
  mit Abgabezeit, Punkten/Note, geltender Frist, Gruppe und Hinweis „NTA“ (Nachteilsausgleich).

## Fristen und späte Abgaben
* `allow_late` der Aufgabe: späte Abgaben zulassen (Kennzeichnung „verspätet“, bleibt auch nach der Bewertung sichtbar)
  oder sperren.
* **Fristverlängerung** je Schüler/in oder Gruppe (`PUT /channels/{id}/items/{item}/extensions`), mit Begründung
  (verschlüsselt). Im Dialog steht der Nachteilsausgleich-Hinweis aus `support`.

## Wiederabgabe
„Überarbeitung anfordern“ (`status="zurueckgegeben"`, optional neue Frist) hält die Abgabe samt Rückmeldung als **Version**
fest und öffnet die nächste. Rückmeldung/Note der letzten Version bleiben zur Überarbeitung sichtbar und werden bei der
erneuten Abgabe geleert (stehen weiter in der alten Version). Dateien früherer Versionen werden nie gelöscht. Verspätung
bei einer Überarbeitung misst sich an deren eigener Frist. Nach einer Überarbeitung ist kein Zurückziehen mehr möglich.

## Gruppen im Kursraum
* Bereich „Gruppen“ (Lehrende): **Einteilungen** (z. B. „Projektgruppen“) mit Gruppen; Mitglieder von Hand, oder
  automatisch zufällig/alphabetisch nach Gruppenzahl oder -größe (neu oder nur Nicht-Eingeteilte verteilen). Je Einteilung
  gehört eine Person zu höchstens einer Gruppe. Nur Teilnehmende mit Konto können Mitglied sein.
* **Gruppenabgabe** (Knopf „Bewertung“): Jedes Mitglied hat eine eigene Abgabe-Zeile mit gleichem Inhalt; jede Änderung
  eines Mitglieds gilt für alle. Bewertung gilt für die ganze Gruppe; „Nur diese Person“ setzt eine **Einzelanpassung**
  (bleibt bei späteren Gruppenbewertungen erhalten, außer „überschreiben“). Nach Abgaben lässt sich die Gruppenabgabe nicht
  mehr umstellen. Wechselt ein Mitglied die Gruppe, fällt seine Zeile weg, die Dateien bleiben bei der Gruppe.
* **Sichtbarkeit nach Gruppe**: Material, Aufgaben und Ordner lassen sich auf Gruppen beschränken (Knopf „Gruppen“ an der
  Aufgabe bzw. im Bereich „Gruppen“). Lehrende sehen immer alles.

### Schnittstelle für „bedingte Freigabe nach Gruppe“ (M2)
Modul `schulmanager.server.channel_groups`:
`user_group_ids(db, channel_id, user_id)`, `user_in_any_group(db, channel_id, user_id, group_ids)` (leere Liste = „für
alle“), `item_group_ids(db, item_id)`, `folder_group_ids(db, folder_id)`, `item_allowed(db, channel_id, item_id, user_id)`,
`blocked_for(db, channel_ids, user_id)`. Die Gruppen-Beschränkung wirkt bereits über `Clock.restrict(...)` in
`features_channels.py` auf alle Teilnehmenden-Ansichten. Tabellen: `channel_group_gates` (Material/Ordner → Gruppen).

## Schnittstelle für das Notenbuch (M4)
`schulmanager.server.assignment_tools.list_results(db, channel_id=None, item_ids=None, student_user_id=None,
student_id=None, since=None)` und `GET /channels/{id}/assignment-results[?item_id=]` liefern je **bewerteter** Abgabe
(Status `bewertet`, mit Punkten oder Note, jeweils die aktuelle Version):

| Feld | Bedeutung |
|---|---|
| `channel_id`, `item_id`, `title` | Kursraum, Aufgabe, Aufgabentitel |
| `student_user_id`, `student_id` | Konto, Schüler-ID |
| `points`, `max_points`, `percent` | Punkte (Zahl), Höchstpunkte, Prozent |
| `grade` | Note als Text (`"2+"`, `"12"`) |
| `grade_number` | Note als Zahl, wenn eindeutig (`"2+"` → 1,7; sonst `null`) |
| `graded_at` | Zeitpunkt der Bewertung (ISO, UTC) |
| `attempt`, `late`, `group_id` | Version, verspätet abgegeben, Gruppe (Gruppenbewertung gilt je Person) |

Gespeichert in `assignment_submissions` (`points`, `max_points` als Zahl, `grade_enc` verschlüsselt, `feedback_at`).

## Bekannte Grenzen
* Hat eine Schülerin mehrere Konten, zählt für Gruppen und Tabelle das Konto mit der kleinsten ID.
* Eltern anderer Gruppenmitglieder können Dateien der Gruppe nicht öffnen.
* Einzelanpassungen werden bei „Überarbeitung anfordern“ nicht je Person versioniert (die Version hält den Stand der Zeile).
