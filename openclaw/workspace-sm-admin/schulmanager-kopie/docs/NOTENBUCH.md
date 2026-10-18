# Notenbuch (B-52)

Notenbuch je Kursteil und Halbjahr mit Leistungsarten, Gewichtung, Notenskalen und Notenschlüssel, Halbjahresnoten,
Sichten für Schüler/innen, Eltern und Klassenleitung sowie CSV-Ausgabe für SchILD, ASV und LUSD. **Kein Zeugnisdruck.**

## 1. Aufbau
| Teil | Datei |
|---|---|
| Rechenlogik (rein) | `schulmanager/gradebook.py` |
| Tabellen `gb_*` (Migration `0039_gradebook`) | `server/feature_models/gradebook.py` |
| Datenzugriff, Rechte, Berechnung | `server/gradebook_store.py` |
| Sichten, Klassenübersicht, PDF, Export | `server/gradebook_reports.py`, `integrations/grades_export.py` |
| Übernahme aus anderen Bereichen | `server/gradebook_sources.py` |
| Routen `/api/v1/gradebook/*` | `server/routes/features_gradebook.py` |
| Demo-Noten | `server/gradebook_demo.py` (von `demo_loader.load_demo`) |
| Oberfläche | `frontend/src/features/notenbuch/*`, Schülersicht `MyGradebook` in `features/students/GradesPage.tsx` |

## 2. Skalen und Notenschlüssel
Skalen: `note6` (1–6 mit Tendenz), `punkte15`, `prozent`, `verbal` (Text, keine Rechnung), `bestanden`, eigene (`custom`, Stufen mit
Zahlenwert). Einstellbar je Klassenstufe oder Kurs, Schulstandard in der Verwaltung. Notenschlüssel rechnen Punkte über
Prozentgrenzen („ab“) in Noten um; eingebaut sind `standard6`, `tendenz6`, `oberstufe15`, `bestanden50`, eigene sind möglich.
Tendenzen: `2+` = 1,7, `2-` = 2,3, `1+` zählt wie `1`, `6-` gibt es nicht.

## 3. Rechnung
* Gewichteter Schnitt: Leistungen (Gewicht je Note) und Unterkategorien (Gewicht je Kategorie), bis 4 Ebenen. Kategorien ohne zählende
  Note werden nicht mit 0 gerechnet, die Gewichte der übrigen verteilen sich neu.
* Status `entschuldigt`, `ausgelassen`, `nachschreiben` zählen nicht; `unentschuldigt` zählt als schlechteste Note. Nachschreibtermin je
  Leistung/Person wird angezeigt.
* Runden kaufmännisch (0,5 auf). Vorschlag aus dem auf die eingestellten Nachkommastellen gerundeten Schnitt, „ganz“ oder „mit Tendenz“.
* Die Lehrkraft legt die Endnote fest; weicht sie vom Vorschlag ab, steht „überschrieben“ dabei.
* Versetzungswarnung (einstellbar): Defizit ab Note 5 bzw. bis 4 Punkte; Warnung bei Defiziten in Hauptfächern (Standard 1) oder in allen
  Fächern (Standard 2).

## 4. Rechte (ROLLEN-RECHTE.md)
`gradebook.use` (Fachlehrkraft eigene Kursteile, Schulleitung alle), `gradebook.read_class` (Klassenleitung lesend), `gradebook.manage`
(Schulleitung: Einstellungen, Entsperren), `gradebook.export` (Schulleitung, Sekretariat). Fremde Notenbücher → 404. Admin nie.
Sperren: Fachlehrkraft sperrt, nur die Schulleitung öffnet wieder.

## 5. Einsicht
Einstellung der Schule: `aus`, `sofort`, `freigabe` (je Leistung durch die Lehrkraft), `endnote`; Schnitte ein/aus. Die Endnote erscheint
erst nach dem Sperren. Eltern über `parent_access` Bereich `noten` (volljährige Kinder nur mit Freigabe). Route `GET /gradebook/my`.

## 6. Schnittstelle für andere Bereiche (Aufgaben M1, Selbsttests M3)
Ergebnis = Elementtyp + ID + Punkte (mit Höchstpunktzahl) bzw. Note + Datum:
```python
from schulmanager.server import gradebook_sources as gs
gs.publish_results(db, source_type="selbsttest", source_id="42", course_id=cid, part=0, title="Bruchrechnen",
                   date="2026-10-05", max_points=20, results=[gs.SourceResult("S12", points=18)])
gs.withdraw_results(db, "selbsttest", "42")        # Quelle zurücknehmen
```
Nichts wird automatisch übernommen: die Lehrkraft sieht die Quelle unter „Übernehmen“ und übernimmt oder wählt sie ab. Erneutes
`publish_results` zieht in übernommene Leistungen nach (von Hand geänderte Noten bleiben). Klausurnoten (`exam_results`) sind als
Provider angeschlossen (`register_provider`), Speichern von Klausurnoten gleicht übernommene Leistungen ab.

## 7. Datenschutz und Protokoll
Noten, Punkte, Bemerkungen und Protokolleinzelheiten verschlüsselt (`gb_entries`, `gb_finals`, `gb_log`). Jede Änderung: Audit
(`gradebook.*`, ohne Notenwerte) und Notenbuch-Protokoll (alt → neu, verschlüsselt, `GET /gradebook/books/{id}/log`). Nachteilsausgleich
erscheint nur als Hinweis „NTA“ (mit `support.hints`/`support.read`). Benachrichtigung (Art `gradebook`) beim Sperren, ohne Noten.
Keine Freigabe über die offene API (Noten sind nie API-Bereich).

## 8. Export
`GET /gradebook/export?term=&format=schild|asv|lusd&class_id=` – festgelegte Noten gesperrter Notenbücher (Schulleitung: `include_open`).
Spaltenköpfe nach den Importvorlagen; die Zuordnung in der Zielsoftware ist einmalig zu prüfen (kein Rundlauf-Test mit der amtlichen
Spezifikation, kein ENM-Format).

## 9. Tests
`tests/test_gradebook_calc.py` (Rechnung), `tests/test_gradebook_api.py` (Rechte, Eintragen, Sperren, Übernahme, Sichten, Export),
`tests/test_gradebook_demo.py`, `frontend/src/features/notenbuch/logic.test.ts`.

## 10. Demo
Klassen 5a, 7a, 9P/9a, Q1-1/Q2-1: je Kursteil ein gesperrtes Notenbuch des Vorhalbjahres (mit Endnoten, einzelnen Defiziten) und ein
laufendes (Klausur nach Punkten, Nachschreiben).
