# Kompetenzraster und Lernstand

Stand 13.10.2026. Schließt die Moodle-Lücken „Kompetenzen / Lernpläne“ und „Abzeichen“ (den internen Moodle-Vergleich) und
trägt Grundschule, Montessori und Lernentwicklungsgespräche (`docs/MONTESSORI-UND-WERKZEUGE.md`, W-23).

Code: `schulmanager/competency.py` (reine Logik), `server/competency_db.py` (Zugriff, Sichtregeln, Aufbereitung),
`server/routes/features_competency.py` (Rahmen, Import, Zuordnung), `server/routes/features_competency_learning.py`
(Lernstand, Pläne, Abzeichen, Bericht), `server/competency_report.py` (PDF), `server/competency_seed.py` (Demo),
`server/feature_models/competency.py`, Migration `0040_competencies`. Oberfläche: `frontend/src/features/kompetenzen/`.

## 1. Begriffe

| Begriff | Bedeutung |
|---|---|
| Rahmen | Fach/Jahrgang als Kompetenzraster: Name, 2–6 **Niveaustufen** (Beschriftungen, z. B. „Ich kann es allein“), Bereiche. Mehrere Rahmen nebeneinander. |
| Bereich | Gliederung im Rahmen („Zahlen und Rechnen“). |
| Kompetenz | „Ich kann …“-Aussage mit optionalem Kürzel und optional einem Beschreibungstext je Stufe. |
| Stufe | 1 bis n. „Nicht eingeschätzt“ ist kein Wert, sondern ein fehlender Eintrag. |
| Lernstand | Stufe je Kind und Kompetenz mit Datum, Nachweis und Kommentar. **Nur anhängend**: Jede Änderung ist ein neuer Eintrag, der Verlauf bleibt. Aktuell zählt der jüngste (Datum, dann ID). |
| Selbsteinschätzung | Eintrag der Schülerin/des Schülers (`kind = self`); die Lehrkraft **bestätigt** (auch mit anderer Stufe) – dabei entsteht ein Lehrkraft-Eintrag, der Selbsteintrag gilt als bestätigt. Beide Werte stehen nebeneinander. |
| Braucht Unterstützung | Stufe der Lehrkraft ≤ „Unterstützung bis Stufe“ des Rahmens (Standard 1; 0 = aus); ohne Lehrkraft-Eintrag zählt die Selbsteinschätzung. Nur für Lehrkräfte sichtbar. |
| Lernplan | Ziele je Kind mit Woche (Montag), Fälligkeit, Status (offen, in Arbeit, erledigt), optional Kompetenz. Passt zur Freiarbeit. |
| Abzeichen | Von der Schule definiertes Symbol (12 eingebaute Zeichnungen, 7 Farben) mit Name, Beschreibung, Vergabe manuell oder automatisch. |

## 2. Rechte und Sicht

Neue Rechte (`permissions.py`, `ARCHITECTURE.md` §6, `ROLLEN-RECHTE.md`):

| Recht | Wer (Standard) | Umfang |
|---|---|---|
| `competency.read` | Schulleitung, Abteilungsleitung, Lehrkraft (+ Zuschauer/in) | Lehrkraft `own_classes`, Abteilungsleitung `own_branch` |
| `competency.assess` | wie `read` | wie `read` |
| `competency.manage` | Schulleitung, Abteilungsleitung, Lehrkraft | – (Rahmen und Abzeichen der Schule, ohne Einblick in Lernstände) |

Die technische Administration bekommt keines der Rechte (personenbezogene Lernstände). **Schüler/innen und Eltern haben kein
Recht**, sondern sehen ihr Kind über `own_student_ids`; Eltern volljähriger Kinder nur mit Freigabe im Bereich
`kompetenzen` (`parent_access`, im Profil der Schülerin/des Schülers einstellbar). Fremde Kinder → 404.

Sichtstufen auf einen Lernstand (`competency_db.Access.view_kind`): `staff` (alles), `self` (eigene Daten; darf
Selbsteinschätzung und eigene Lernplan-Ziele pflegen), `family` (nur lesen). **Schüler/innen und Eltern sehen keine
Beobachtungsnotizen** (`evidence_type = note`) und keine „Unterstützung“-Markierung. Rahmen, Abzeichen-Katalog und
Zuordnungen (Lehrstoff) sehen alle Angemeldeten dieser Gruppen.

## 3. Datenschutz und Audit

* Nachweis (Beobachtungsnotiz bzw. Link), Kommentar, Lernplan-Titel und -Notiz, Notiz zur Abzeichen-Vergabe sind
  **verschlüsselt** (`crypto.encrypt_text`, AAD `comp_assessments.evidence:<id>` usw., Rewrap registriert).
* Jede Schreibaktion steht im Audit: `competency.framework.create|update|archive|delete|import`, `competency.assess`,
  `competency.self`, `competency.confirm`, `competency.plan.create|update|delete`, `competency.badge.create|update|delete|award|revoke|evaluate`,
  `competency.links`, `competency.report` (ohne Inhalte, nur Zählungen und IDs).
* Keine Freigabe als öffentliche API (`/api/v1/open`): Lernstände sind Schülerdaten und nicht für Apps/KIs gedacht.
* Löschen eines Kindes: die Tabellen tragen nur die Schüler-ID aus dem Planungsdokument (wie `exam_results`); eine
  automatische Bereinigung beim Entfernen aus dem Planungsdokument gibt es noch nicht (siehe §9).

## 4. Datenmodell (Tabellen)

`comp_frameworks`, `comp_areas`, `comp_competencies` (Lehrplan-Inhalt), `comp_assessments` (Lernstand-Verlauf),
`comp_links` (Zuordnung Element → Kompetenz), `comp_plans` (Lernplan), `comp_badges`, `comp_badge_awards`.
Rahmen mit Lernständen lassen sich nur archivieren, nicht löschen (409); Kompetenzen mit Lernständen werden beim Bearbeiten
nur mit `?force=1` entfernt (Oberfläche fragt nach); weniger Niveaustufen als vorhandene Lernstände sind nicht möglich.

## 5. API (alle unter `/api/v1`)

| Pfad | Zweck | Recht |
|---|---|---|
| `GET /competency/frameworks` · `GET /competency/frameworks/{id}` | Rahmen (Kurzform, Baum). `?archived=1` auch archivierte | Beteiligte |
| `POST /competency/frameworks` · `PUT …/{id}[?force=1]` · `POST …/{id}/archive?archived=` · `DELETE …/{id}` | anlegen, ersetzen (Einträge mit `id` bleiben), archivieren, löschen | `manage` |
| `POST /competency/frameworks/import` · `GET …/{id}/export?format=json\|csv` | Import/Export | `manage` / Beteiligte |
| `GET /competency/templates` · `POST /competency/templates/{key}/use` | eingebaute Beispielrahmen | `manage` |
| `GET /competency/students/{sid}[?framework_id=]` | Rahmen mit Lehrkraft-Stufe, Selbsteinschätzung, Verlauf, Fortschritt, Abzeichen | Lehrkraft `read`; Schüler/in; Eltern |
| `POST /competency/assessments` `{entries:[{student_id, competency_id, level, date?, evidence_type?, evidence_ref?, evidence_text?, comment?}]}` | Stufe setzen (gleiche Stufe ohne Nachweis/Kommentar wird übersprungen); prüft automatische Abzeichen | `assess` |
| `POST /competency/self` · `POST /competency/self/{id}/confirm` | Selbsteinschätzung / Bestätigung (optional andere Stufe) | Schüler/in / `assess` |
| `GET /competency/overview?framework_id&class_id&area_id` | Klasse × Kompetenzen: Zellen `{t, s, p}` (Lehrkraft, Selbst, offen), je Kind `support`, `pending`, `progress` | `read` |
| `GET /competency/students/{sid}/report.pdf[?framework_id=]` | Lernentwicklungsbericht | Lehrkraft `read` (Eltern/Schüler: 404) |
| `GET /competency/plans?student_id=` · `POST /competency/plans` · `PATCH|DELETE /competency/plans/{id}` | Lernplan; `POST` auch mit `student_ids` (mehrere Kinder) | Sicht wie Lernstand; Schreiben `assess` bzw. Schüler/in (eigene Ziele, Status aller Ziele) |
| `GET|POST /competency/badges` · `PUT|DELETE /competency/badges/{id}` · `POST /competency/badges/evaluate` | Abzeichen definieren, alle automatischen prüfen | Katalog: Beteiligte; Pflege `manage` |
| `POST /competency/badges/{id}/award` · `DELETE /competency/badges/{id}/award/{sid}` | manuell vergeben / zurücknehmen | `assess` |

Live-Hinweis: `change`-Scope `competency`.

## 6. Schnittstelle: Aufgaben und Material einer Kompetenz zuordnen

Ein **generisches** Feld statt Änderungen an fremden Tabellen: `comp_links (competency_id, item_type, item_id)`, eindeutig je
Kombination. Weder Kursräume noch andere Module müssen sich ändern.

* `item_type`: frei gewählter Typ, `[a-z][a-z_]{0,29}`; vereinbart ist `channel_item` (Aufgabe/Material/Beitrag eines
  Kursraums, `item_id` = ID des `ChannelItem`). Andere Module wählen eigene Typen.
* `PUT /competency/links` `{item_type, item_id, competency_ids}` ersetzt die Zuordnung des Elements (Recht `competency.assess`).
* `GET /competency/links?item_type=&item_id=` liefert Titel, Rahmen, Bereich der zugeordneten Kompetenzen (für alle Angemeldeten).
* Die Lernstand-Ansicht der Lehrkraft listet je Kompetenz die zugeordneten Elemente; für `channel_item` mit Titel.
* Eintrag in die Oberfläche der Kursräume: `<ItemCompetencies itemType="channel_item" itemId={String(item.id)} />`
  (`features/kompetenzen/ItemCompetencies.tsx`) zeigt die Zuordnung als Chips und lässt Lehrkräfte sie ändern. Ein
  Aufruf genügt; das Einbinden gehört in die Dateien der Kursräume (noch nicht geschehen, siehe §9).
* Als **Nachweis** eines Lernstands kann ein Element verknüpft werden: `evidence_type = assignment|material` mit
  `evidence_ref = "channel:<kanal-id>"` (führt in den Kursraum) – die Oberfläche der Lehrkraft bietet bisher Beobachtung
  und Link, die Verknüpfung per API.

## 7. Import und Vorlagen

JSON (Export = Import):

```json
{"name": "Mathe Klasse 3", "subject": "", "description": "", "levels": ["Anfang", "Mitte", "Ende"], "support_level": 1,
 "areas": [{"name": "Zahlen", "competencies": [{"code": "Z1", "title": "Ich kann bis 1000 zählen", "descriptors": ["", "mit Material", "ohne"]}]}]}
```

CSV (Trenner `;`, `,` oder Tabulator; erste Zeile Kopf): `Bereich;Kompetenz;Kürzel;Stufe 1;Stufe 2 …`. Leerer Bereich = wie
darüber. Die Stufen-Beschriftungen kommen beim Import aus dem Formular (Standard: Ich fange an / mit Hilfe / allein / erklären).
Grenzen: 40 Bereiche, 600 Kompetenzen, 2–6 Stufen. Fehler → 422 mit deutschem Text.

Beispielrahmen (Seed der Demo und über „Aus Vorlage“ jederzeit anlegbar, `competency.TEMPLATES`):
**Grundschule Mathe und Deutsch** (5 Bereiche, 21 Kompetenzen) und **Montessori-Materialien** (5 Bereiche, 20 Kompetenzen;
Stufen nach dem Dreierschritt). `demo_loader.load_demo` legt sie samt Lernständen für drei Klassen, Selbsteinschätzungen,
Lernplan-Einträgen und zwei Abzeichen an (erfundene Werte).

## 8. Abzeichen und Bericht

* Vergabe automatisch bei `competencies` (alle genannten Kompetenzen mindestens Stufe n), `area` oder `framework` (Anteil der
  Kompetenzen mindestens Stufe n). Geprüft wird nach jeder Lehrkraft-Einschätzung/Bestätigung und über „Automatische
  Abzeichen prüfen“. Vergebene Abzeichen bleiben, bis eine Lehrkraft sie zurücknimmt. Kein Open-Badges-Export.
* **Lernentwicklungsbericht** (PDF, `competency_report.py`): Kopf mit Name/Klasse/Datum, je Rahmen und Bereich die
  Kompetenzen mit Stufenkästchen (Lehrkraft), Selbsteinschätzung, Datum und letztem Kommentar, Abzeichen, Lernplan-Stand und
  Platz für Bemerkungen zum Gespräch. Ohne Beobachtungsnotizen. Grundlage für Zeugnisbemerkungen; kein Zeugnisdruck.

## 9. Offene Punkte

* `ItemCompetencies` in die Kursraum-Oberfläche (Aufgaben/Material) einbauen und beim Anlegen eines Lernstand-Nachweises
  eine Aufgabe/ein Material auswählen können (Dateien der Kursräume gehören anderen Agenten).
* Bereinigung der Lernstände, wenn ein Kind aus dem Planungsdokument entfernt wird (wie bei `exam_results`).
* Ein Schüler-Bereich in der Startseite (Kachel „Mein Wochenplan“) und Benachrichtigung bei offener Selbsteinschätzung
  (Benachrichtigungszentrale, M6).
* Mehrere Kinder gleichzeitig einschätzen (API `entries` kann es, die Oberfläche bisher nur einzeln); Lernplan-Ziele für
  eine ganze Klasse in einem Schritt (API `student_ids` kann es).
