# Lernfortschritt im Kursraum – Abschluss, bedingte Freigabe, Papierkorb

Gebaut für die Moodle-Lücken 6 und 9 und den Papierkorb (den internen Moodle-Vergleich). Code: `schulmanager/server/progress.py`
(Logik), `routes/features_progress.py`, `routes/features_channel_trash.py`, Modelle `feature_models/progress.py`, Migration
`0037_learning_progress`, Oberfläche `frontend/src/features/channels/` (`ProgressTab`, `RulesDialog`, `TrashDialog`, `progress.ts`).

## Was Nutzer sehen

* **Lehrkraft** legt je Material oder Aufgabe unter „Abschluss & Bedingungen“ (Häkchen-Symbol an der Zeile) fest:
  * *Abschlussbedingung*: **Selbst abhaken**, **Angesehen**, **Abgegeben**, **Bewertet**, **Bestanden** (Mindestprozent;
    ohne Prozentwert in der Bewertung gilt Note 4 oder besser). Abgegeben/Bewertet/Bestanden gibt es nur für Aufgaben und
    Material mit „Abgabe möglich“. „Zur Überarbeitung zurückgegeben“ zählt nicht als bewertet.
  * *Freigabe*: Bedingungen mit **UND/ODER** (eine Untergruppe darunter möglich): anderes Element erledigt, Punkte
    mindestens x %, Note x oder besser, Mitglied einer Gruppe, Datum (ab/bis), „Zeitfreigabe erreicht“.
* Reiter **Fortschritt**: Lehrkraft sieht die Tabelle Schüler/in × Elemente (Filter: Name, Klasse, „offen bei …“, „nur mit
  offenen Elementen“; Export als CSV, Semikolon, Formelschutz). Schüler/innen sehen ihre Liste; Eltern die ihres Kindes, wenn die
  Lehrkraft „Eltern sehen den Fortschritt ihres Kindes“ einschaltet (Kursraum-Einstellung `progress_parents`; volljährige Kinder
  steuern den Elternzugriff auf Kursräume weiter über `parent_access`).
* Im Material: „Erledigt“-Häkchen bzw. Symbol, im Kopf des Kursraums ein Fortschrittsbalken (nur wenn Elemente verfolgt werden).
  Gesperrte Elemente zeigen nur Titel und **„Verfügbar, sobald …“**; Inhalt, Dateien, Link, Abgabe und „angesehen“ sind
  serverseitig gesperrt (403), ebenso der Dateizugriff.
* **Papierkorb** (Schaltfläche im Kopf des Kursraums): Löschen von Material, Aufgaben und Ordnern legt sie dort ab. Wiederherstellen
  bringt Abgaben, Dateien und Regeln zurück; fehlt der Ordner, landet der Eintrag oben, ein gleichnamiger Ordner bekommt „(2)“.

## Regeln und Rechte

* Regeln ändern: Lehrende des Kursraums (`channels.manage`, in Klassenräumen nur eigenes Material bzw. Klassenleitung/Verwaltung
  wie beim Bearbeiten). Schüler/innen haken nur eigene Elemente mit Bedingung „Selbst abhaken“ ab; Eltern/Aufsicht nichts.
* Übersicht: nur Lehrende. In Klassenräumen sind Abgabe-Zellen fremder Aufgaben ausgeblendet (Schloss).
* Papierkorb sehen: Lehrende. **Wiederherstellen und endgültig löschen: neues Recht `channels.trash`** (Standard: Admin,
  Schulleitung, Lehrkraft/Abteilungsleitung mit Umfang `own_courses`; in `docs/ROLLEN-RECHTE.md`) und zusätzlich das
  Bearbeitungsrecht am Material (Klassenräume: nur eigenes). Schulleitung/Aufsicht im Kursraum bleibt nur lesend.
* Frist: Schuleinstellung `trash_retention_days` (Standard **30**, 1–365). Oberfläche: Planung → Einstellungen → „Kursräume“ und im
  Papierkorb (mit `settings.edit`). Die stündliche Wartung (`maintenance.run_maintenance` → `run_purge`) löscht Abgelaufenes endgültig
  samt Abgaben, Dateien, Regeln und Häkchen.
* Audit (ohne Inhalte): `completion.rule`, `completion.bulk`, `completion.mark`, `availability.rule`, `channel_item.delete`/
  `channel_folder.delete` (mit `trash: true`), `channel_trash.restore|purge|empty`.

## Technik

* **Papierkorb**: `channel_items` und `channel_folders` haben `deleted_at`, `deleted_by`, `trash_group`. Ein globaler
  `do_orm_execute`-Filter (`feature_models/channels._hide_trashed`) blendet gelöschte Zeilen in **allen** ORM-Abfragen aus;
  nur mit `execution_options={"include_trashed": True}` sieht man sie (Papierkorb, Löschen von Kursräumen). Wer eine Zeile
  per `db.get` aus der Identity-Map holt, prüft `deleted_at` selbst (siehe `_live_folder`).
* **Tabellen**: `completion_rules`, `completion_marks` (nur manuelle Häkchen), `availability_rules` (JSON-Baum). Alles andere
  wird live aus Ansichten, Abgaben und Bewertungen berechnet. Noten/Punkte: `AssignmentSubmission.points/max_points` (Raster) bzw.
  der Bewertungstext („80 %“, „12/15“, „9 von 12“, „2+“, „2,5“, „2-3“; „12 Punkte“ ohne Maximum ist nicht auswertbar).
* Migration `0037_learning_progress` (`down_revision = "0035_plan_proposals"`, Zusammenführung der Köpfe macht der Haupt-Agent).

## Schnittstelle für andere Module (M1 Aufgaben/Gruppen, M3 Abstimmung/Selbsttest)

Elemente sind generisch über `(element_type, element_id)` adressiert (Material/Aufgaben: `"item"`). Neue Elementarten melden sich
mit einem Anbieter an (kein Eingriff in `progress.py`):

```python
from schulmanager.server import progress

class PollProvider:
    type = "poll"                          # element_type in URLs und Regeln
    label = "Abstimmung"
    modes = ("manual", "submitted")        # erlaubte Abschlussbedingungen (Teilmenge von progress.MODES)

    def elements(self, db, channel_id):    # alle Elemente des Kursraums (ohne Gelöschte)
        return [progress.Element("poll", p.id, p.title, "Abstimmung", self.modes) for p in ...]

    def facts(self, db, channel_id, user_ids, ids):   # {(user_id, element_id): progress.Facts}
        return {(uid, pid): progress.Facts(viewed=..., submitted=..., graded=..., score_percent=..., note=...) ...}

    # optional
    def created_by(self, db, element_id): ...         # Ersteller für die Rechteprüfung (sonst jede Lehrkraft des Raums)
    def visible_ids(self, db, channel_id, user_id, ids): ...   # welche Elemente sieht dieses Konto (sonst alle)

progress.register_provider(PollProvider())            # beim Import des Routenmoduls
```

* Danach erscheint das Element in `GET /channels/{id}/elements`, im Fortschrittsbalken und in der Tabelle, lässt sich über
  `PUT /channels/{id}/elements/poll/{id}/completion` mit Bedingung versehen und als Voraussetzung in Freigaberegeln verwenden
  (`completed`/`score`/`note`).
* Soll ein Element selbst **gesperrt** werden können, ruft das Modul beim Ausliefern `progress.Progress(db, [channel_id],
  [user_id]).gate(user_id, "poll", id, visibility, channel_id)` auf (`visibility` = `schulmanager.channels.Visibility`, bei reinem
  Sichtbar-Element `Visibility(True, "visible")`) und zeigt bei `Gate.locked` nur Titel und `Gate.text` („Verfügbar, sobald …“).
  Die Regeln pflegt die vorhandene Oberfläche nur für Material/Aufgaben; ein Modul mit eigenem Editor ruft denselben Endpunkt
  `PUT …/elements/{typ}/{id}/availability` auf.
* Beim endgültigen Löschen eines Elements: `progress.forget_element(db, "poll", id)` (räumt Regeln und Häkchen weg).
* **Gruppen**: `progress.register_group_provider(obj)` mit `list_groups(db, channel_id) -> [{"id", "name"}]` und
  `member_ids(db, channel_id, group_id) -> set[user_id]`. Eingebaut ist `progress.CourseGroups` auf Basis von
  `feature_models/channel_groups.py` (M1), automatisch angemeldet. Ohne Gruppentabellen bleibt die Bedingung ausgeblendet.

## Grenzen

* Regeln werden beim „Kopieren in anderen Kursraum“ nicht mitkopiert.
* Elternansicht zeigt nur „erledigt/offen“, nie Noten oder Abgaben.
* Die Tabelle zeigt Schüler/innen ohne Konto ohne Werte („kein Konto“); gesperrt/frei je Schüler/in zeigt sie nicht.
* Die Übersicht auf der Startseite („neues Material/Hausaufgaben“) lässt gesperrte Elemente weg.
