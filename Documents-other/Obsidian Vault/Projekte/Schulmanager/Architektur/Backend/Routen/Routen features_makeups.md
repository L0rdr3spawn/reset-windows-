---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_makeups.py"
stand: 2026-10-12 22:33
generator: schulmanager-regen
---

# Routen features_makeups

> API-Routen · 1 Datei(en) · 376 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Nachschreibtermine (Klausur/Test verpasst): Liste, Termin festlegen, Attest-Verzicht, Erledigt.

* `GET    /exam-makeups` (`?from=&to=&status=&exam_id=&student_id=`) – Zeilen, die das Konto sehen darf
  (gleicht vorher mit Klausuren und Fehlzeiten ab).
* `GET    /exam-makeups/summary` – Zähler für Menü/Kachel: `{open, attest_missing}`.
* `POST   /exam-makeups/dates` – Termin für eine oder mehrere Zeilen derselben Klausur festlegen
  (`exam.edit` für diese Klausur); Konflikte → 409 `{"detail":{"conflicts":[…]}}`, `force` nur für
  Planung/Leitung.
* `PUT/DELETE /exam-makeups/dates/{id}` – Termin ändern bzw. zurücknehmen (Zeilen wieder „offen“).
* `PATCH  /exam-makeups/{id}` – Status (`offen|erledigt|entfallen`, Lehrkraft der Klausur) und
  `attest_waived` (Klassenleitung/Sekretariat/Schulleitung).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_makeups.py` | 376 | Nachschreibtermine (Klausur/Test verpasst): Liste, Termin festlegen, Attest-Verzicht, Erledigt. |

## Endpunkte (7)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/exam-makeups` | `list_makeups` (`features_makeups.py:147`) | (angemeldet) | [[Feature classes]], [[Feature makeups]] |
| GET | `/api/v1/exam-makeups/summary` | `summary` (`features_makeups.py:162`) | (angemeldet) | [[Feature makeups]] |
| GET | `/api/v1/exam-makeups/suggestions` | `suggestions` (`features_makeups.py:203`) | (angemeldet) | – |
| POST | `/api/v1/exam-makeups/dates` | `create_date` (`features_makeups.py:224`) | (angemeldet) | [[Feature makeups]] |
| PUT | `/api/v1/exam-makeups/dates/{date_id}` | `update_date` (`features_makeups.py:245`) | (angemeldet) | [[Feature makeups]] |
| DELETE | `/api/v1/exam-makeups/dates/{date_id}` | `delete_date` (`features_makeups.py:268`) | (angemeldet) | [[Feature makeups]] |
| PATCH | `/api/v1/exam-makeups/{makeup_id}` | `patch_makeup` (`features_makeups.py:291`) | (angemeldet) | [[Feature makeups]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `DateIn` (`schulmanager/server/routes/features_makeups.py:37`)
- Klasse `DatePut` (`schulmanager/server/routes/features_makeups.py:47`)
- Klasse `MakeupPatch` (`schulmanager/server/routes/features_makeups.py:56`)
- Funktion `calendar_items` (`schulmanager/server/routes/features_makeups.py:328`) – Nachschreibtermine im Zeitraum als Kalender-Einträge (`exams`-Format, `kind="nachschreiben"`):

## Datenbank-Tabellen

- **Nutzt:** `exam_makeup_dates`, `exam_makeups` → [[Datenmodell#Sonstige Tabellen]]

## Hängt ab von

- [[Routen features_common]] – `features_common`
- [[Routen features_exams]] – `features_exams` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `makeups`
- [[Server deps]] – `deps`
- [[Server makeups]] – `makeups`

## Wird genutzt von

- [[Routen features_calendar]]

## Tests

`tests/test_makeups.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
