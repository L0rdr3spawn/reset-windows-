---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_data.py"
stand: 2026-10-12 21:40
generator: schulmanager-regen
---

# Routen features_data

> API-Routen · 1 Datei(en) · 1051 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Stammdaten: generisches CRUD über `models.COLLECTIONS` und Einstellungen.

* `GET/POST /data/{collection}`, `GET/PUT/DELETE /data/{collection}/{id}`
  (alle Sammlungen außer `lessons`, `absences`, `overrides` – diese haben eigene Endpunkte)
* `GET/PUT /settings`

Validierung: Typen (Pydantic über die Dataclasses), Referenzen existieren, IDs eindeutig. `DELETE` verweigert mit 409 `{"detail":{"message","references":[...]}}`, solange noch Verweise bestehen – `?force=1` entfernt/leert die Verweise (Kaskade).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_data.py` | 1051 | Stammdaten: generisches CRUD über `models.COLLECTIONS` und Einstellungen. |

## Endpunkte (8)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/data/{collection}` | `list_items` (`features_data.py:559`) | (angemeldet) | [[Frontend Basis]] |
| GET | `/api/v1/data/{collection}/{item_id}` | `get_item` (`features_data.py:578`) | (angemeldet) | – |
| POST | `/api/v1/data/{collection}` | `create_item` (`features_data.py:709`) | (angemeldet) | [[Seite DutiesPage]], [[Seite MasterDataPage]], [[Seite PlanningPage]] |
| PUT | `/api/v1/data/{collection}/{item_id}` | `update_item` (`features_data.py:747`) | (angemeldet) | [[Seite DutiesPage]], [[Seite MasterDataPage]], [[Seite PlanningPage]] |
| DELETE | `/api/v1/data/{collection}/{item_id}` | `delete_item` (`features_data.py:800`) | (angemeldet) | [[Seite DutiesPage]], [[Seite MasterDataPage]], [[Seite PlanningPage]] |
| GET | `/api/v1/settings` | `get_settings` (`features_data.py:975`) | (angemeldet) | [[Feature messages]], [[Frontend Basis]] |
| PUT | `/api/v1/settings` | `put_settings` (`features_data.py:997`) | settings.edit | [[Feature messages]], [[Seite PlanningPage]], [[Seite SetupPage]] |
| POST | `/api/v1/settings/calendar-preview` | `calendar_preview` (`features_data.py:1037`) | settings.edit | [[Seite PlanningPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `parse_item` (`schulmanager/server/routes/features_data.py:85`)
- Funktion `class_plan_errors` (`schulmanager/server/routes/features_data.py:115`)
- Funktion `validate_item` (`schulmanager/server/routes/features_data.py:138`) – Prüft Referenzen und Wertebereiche. Liefert Fehlermeldungen (leer = ok).
- Funktion `curriculum_conflict_error` (`schulmanager/server/routes/features_data.py:280`) – 409-Detail, wenn die Tafel `item_id` (bereits in `school`) sich mit anderen überschneidet.
- Funktion `exam_errors` (`schulmanager/server/routes/features_data.py:294`)
- Funktion `references` (`schulmanager/server/routes/features_data.py:317`) – Lesbare Liste der Stellen, die auf `collection/item_id` verweisen.
- Funktion `cascade_delete` (`schulmanager/server/routes/features_data.py:367`) – Entfernt bzw. leert alle Verweise auf `collection/item_id` (`?force=1`).
- Funktion `readable_items` (`schulmanager/server/routes/features_data.py:505`) – Liste einer Sammlung, gefiltert nach Rolle.
- Funktion `expand_week_patterns` (`schulmanager/server/routes/features_data.py:619`) – Ältere Anfrage-Felder zu Wochen (`week_pattern`) im Request durch `rhythm` ersetzen und veraltete Felder
- Funktion `class_plan_change` (`schulmanager/server/routes/features_data.py:644`) – Planungsfelder einer Klasse geändert (`item` liegt schon im Dokument): Stunden an entfallenen
- Klasse `WeightsIn` (`schulmanager/server/routes/features_data.py:830`)
- Klasse `PolicyIn` (`schulmanager/server/routes/features_data.py:844`)
- Klasse `BreakIn` (`schulmanager/server/routes/features_data.py:853`)
- Klasse `SettingsIn` (`schulmanager/server/routes/features_data.py:860`) – Teil-Update der Einstellungen (nur gesetzte Felder werden übernommen).
- Funktion `settings_errors` (`schulmanager/server/routes/features_data.py:904`)
- Funktion `calendar_errors` (`schulmanager/server/routes/features_data.py:929`) – Prüft Schuljahr, Zählung und Unterrichtstage (Grenzen §14.6/§15.3).
- Klasse `CalendarPreviewIn` (`schulmanager/server/routes/features_data.py:1025`)

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul legacy]] – `legacy` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul planning]] – `planning` *(nur zur Laufzeit importiert)*
- [[Modul substitution]] – `substitution` *(nur zur Laufzeit importiert)*
- [[Modul teacher_profile]] – `teacher_profile` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks`
- [[Routen features_common]] – `features_common`
- [[Routen features_parent_access]] – `features_parent_access` *(nur zur Laufzeit importiert)*
- [[Server deps]] – `deps`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen features_class_info]]
- [[Routen features_classes]]
- [[Routen features_exams]]
- [[Routen features_exchange]]
- [[Routen features_forms]]

## Tests

`tests/test_attendance.py`, `tests/test_autoplan.py`, `tests/test_chats.py`, `tests/test_curricula.py`, `tests/test_messages.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_substitution_b04.py`, `tests/test_teacher_profile.py`, `tests/test_viewer_role.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
