# Formular-Baukasten

Schulen legen **eigene Formulare** an (Beurlaubung, Entschuldigung, Einverständnisse, Anträge, Rückmeldungen …), legen
fest **wer sie ausfüllt**, **wer sie prüft** und **was bei Genehmigung passiert** – ohne Programmierung. Familien füllen
online (Handy-tauglich) aus oder drucken ein PDF; unterschriebene Scans lassen sich hochladen. Alles liegt verschlüsselt
und protokolliert in der Datenbank.

Code: `schulmanager/forms.py` (Logik, Bibliothek), `schulmanager/server/routes/features_forms.py` (API),
`schulmanager/server/form_pdf.py` (PDF), `schulmanager/server/feature_models/forms.py` + Migration `0030_forms`,
Oberfläche `frontend/src/features/formulare/`. Tests: `tests/test_forms.py`, `formulare.test.ts`.

## Rechte

| Recht | Wer | Zweck |
|---|---|---|
| `forms.manage` | Administration, Schulleitung, Sekretariat | Vorlagen gestalten, Ablauf/Aktionen, Bibliothek – **ohne** Einblick in ausgefüllte Formulare |
| `forms.inbox` | Schulleitung, Sekretariat; Lehrkräfte/Abteilungsleitung nur als Klassenleitung der eigenen Klasse (`class_teacher`) | Eingang: ansehen, genehmigen/ablehnen, Scans, Export |
| `forms.submit` | Eltern, Schüler/innen, Lehrkräfte, Sekretariat, Schulleitung | ausfüllen; welche Formulare, bestimmt die Zielgruppe |

Die technische Administration hat `forms.manage`, aber nie `forms.inbox`/`forms.submit` (feste Regel in
`permissions.py`, nicht freischaltbar). Zuschauer-Konten lesen den Eingang wie die Leitung, ändern nichts.

## Aufbau

* **Vorlage** (`form_templates`): Titel, Beschreibung, Kategorie, Status `entwurf → aktiv → archiviert`,
  Kennzeichen „enthält geschützte Angaben“.
* **Version** (`form_versions`): Felder, Zielgruppe, Ablauf, Fristen, Aktionen als JSON. Änderungen an der Fassung
  erzeugen eine **neue Version**, sobald es Einreichungen mit der aktuellen gibt (sonst wird direkt angepasst). Neue
  Einreichungen nutzen die neueste Version; alte bleiben unverändert und zeigen ihre eigene Fassung.
* **Einreichung** (`form_submissions`): Antworten und Vermerk verschlüsselt (AAD `form_submissions.answers:<id>`),
  Status `eingereicht → in_pruefung → genehmigt | abgelehnt | erledigt` (oder `zurueckgezogen`), Schritt, Frist,
  Ergebnis der Aktionen. **Verlauf** in `form_events`.

### Feldarten

Text, langer Text, Zahl (min/max), Datum, Zeitraum von–bis, Auswahl, Mehrfachauswahl, Ja/Nein, „Ich bestätige“
(Häkchen mit Text), Unterschrift (Name; das **Datum setzt der Server**), Datei-Upload (PDF/Foto, max. 5), Schüler/in
(Kind), Stundenauswahl. Je Feld: Beschriftung, Hilfetext, Pflicht, Reihenfolge. Vorschau im Baukasten (Formular und PDF).

## Wer & wohin

**Zielgruppe:** Rollen (Eltern, volljährige Schüler/innen, alle Schüler/innen, Lehrkräfte, Sekretariat, Schulleitung)
× Klassen/Jahrgänge/alle (gilt für die Klasse des Kindes). Eltern volljähriger Kinder sehen und füllen nur mit der
Freigabe „Dokumente“ (`parent_access`); „nur einmal je Kind“ verhindert Doppelabgaben (abgelehnte/zurückgezogene zählen
nicht).

**Prüfschritte** (bis 4, nacheinander): Klassenleitung des Kindes (Klasse ohne Klassenleitung → Sekretariat),
Sekretariat, Schulleitung, bestimmte Person (nur Schulleitung/Sekretariat/Lehrkräfte). Die **Schulleitung kann jeden
Schritt übernehmen**. Ohne Schritt landet die Einreichung im Eingang und wird dort „als erledigt“ abgeschlossen; mit
„Sofort erledigt“ ist sie direkt erledigt (z. B. Rückmeldungen). Ablehnen verlangt eine Begründung, die die Familie sieht.

**Fristen:** „Ausfüllbar ab/bis“, „Bearbeitung innerhalb x Tagen“ (danach *überfällig*), „Erinnerung nach x Tagen“
(Live-Hinweis an die Prüfenden, Wiederholung nach derselben Zeit; Wartung `run_reminders`).

**Aktionen bei Genehmigung** (bzw. sofort bei „Sofort erledigt“):

* *Beurlaubung/Krankmeldung anlegen* – ruft die vorhandene Funktion `POST /student-absences` mit den Rechten der
  entscheidenden Person auf (mit allen Prüfungen: Schultage, Überschneidungen, Rückwirkung). Felder werden dem
  Formular zugeordnet (Kind, Zeitraum, Stunden, Anlass). Status „genehmigt/entschuldigt“ oder „gemeldet“.
* *Lehrkräfte informieren* – Live-Hinweis (ohne Inhalt) an Lehrkräfte des Kindes; die genehmigte Beurlaubung erscheint
  ohnehin in „Fehlt heute in meiner Stunde“.
* *Termin eintragen* – Termin im Kalender der Klasse (Titel fest, keine persönlichen Angaben).

Schlägt eine Aktion fehl (z. B. Wochenende, fehlende Rechte der entscheidenden Person), bleibt die Genehmigung
bestehen; die Meldung steht im Ergebnis und der Eingang kann „Aktionen erneut ausführen“.

## Ausfüllen, PDF, Scans, Export

* Online ausfüllen (`/formulare` → Ausfüllen), danach Einreichung ansehen/zurückziehen (solange noch kein Schritt
  begonnen hat).
* **PDF**: leer zum Ausdrucken (`GET /forms/templates/{id}/blank.pdf`), ausgefüllt zum Archiv
  (`GET /forms/submissions/{id}/pdf`, mit Verlauf), Vorschau ungespeicherter Formulare (`POST /forms/preview.pdf`).
* **Scan**: unterschriebenes Foto/PDF per `POST /files?purpose=form_file` und `POST /forms/submissions/{id}/scan`.
  Zugriff auf die Datei nur für Beteiligte (registrierte Prüfung `form_submission`).
* **Export** für den Eingang: `GET /forms/export.csv?template_id=` (Semikolon, UTF-8 mit BOM, Formel-Schutz) und
  `GET /forms/export.pdf?template_id=` (alle sichtbaren Einreichungen). Jeder Export wird protokolliert.

## Bibliothek (Beispiele)

Beurlaubungsantrag (legt die Beurlaubung an, informiert Lehrkräfte; verweist auf den bisherigen festen Vordruck),
Schriftliche Entschuldigung (legt die Fehlzeit als entschuldigt an), Einverständnis Klassenfahrt, Foto-/Medien-
Einwilligung, Rückmeldung Elternabend, Antrag Nachteilsausgleich (Klassenleitung → Schulleitung), Schulbescheinigung
anfordern. „Übernehmen“ legt eine **Kopie als Entwurf** an, die die Schule anpasst und veröffentlicht. Die festen
Vordrucke (`/student-absences/form.pdf`, `/leave-form.pdf`) und der bisherige Ablauf bleiben unverändert; im
Ausfüllen-Bereich erscheint bei übernommenen Beispielen der Link „Bisheriger Vordruck“.

## Datenschutz

* Antworten, Vermerke und Verlaufsnotizen **verschlüsselt**; Dateien in der verschlüsselten Dateiablage.
* Sichtbar: einreichende Person, Eltern des Kindes (Volljährige nur mit Freigabe „Dokumente“), das Kind selbst,
  Schulleitung/Sekretariat, die **Klassenleitung nur der eigenen Klasse**, benannte Prüfperson im eigenen Schritt.
  Fachlehrkräfte, Planung, Hausmeister und die **technische Administration sehen keine Inhalte** (404/403).
* Formulare mit Kennzeichen „geschützte Angaben“: jedes Ansehen, PDF und jeder Export wird im Audit-Log protokolliert
  (`form_submission.view|pdf|export`).
* DSGVO-Export des eigenen Kontos enthält die eigenen Einreichungen (`/me/export` → `forms`). Aufbewahrung: abgeschlossene
  Einreichungen werden nach `SM_STUDENT_DOCS_RETENTION_DAYS` samt Dateien gelöscht (Wartungslauf).

## API (Auszug)

`GET /forms/meta`, `/forms/summary`, `/forms/approvers`; Vorlagen: `GET|POST /forms/templates`,
`GET|PUT|DELETE /forms/templates/{id}`, `POST …/status|duplicate`; Bibliothek: `GET /forms/library`,
`POST /forms/library/{key}/adopt`; Ausfüllen: `GET /forms/available`, `GET /forms/templates/{id}/fill`,
`POST /forms/templates/{id}/submit`; Einreichungen: `GET /forms/submissions`, `GET …/{id}`, `POST …/{id}/decide`
(`approve|reject|complete|comment`), `…/retry-actions`, `…/withdraw`, `…/scan`.

## Bewusst offen

* Benachrichtigungen laufen **live** (SSE) und über Zähler auf Startseite/Menü; Nachrichten im Postfach oder per
  E-Mail verschickt der Baukasten noch nicht.
* Erinnerungen an Familien („Rückmeldung fehlt noch“) zeigen Zähler/Kachel, aber keine Einzelnachricht.
* Die Aktion „Termin eintragen“ legt einen Klassentermin an; Raumbuchungen o. Ä. gibt es nicht.
* Bei „Beurlaubung anlegen“ braucht die entscheidende Person das Recht, für die Klasse zu melden
  (Klassenleitung, Sekretariat); Schulleitung ohne `student_absence.report` nutzt „Aktionen erneut ausführen“ durch das
  Sekretariat.
