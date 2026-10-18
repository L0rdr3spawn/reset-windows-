---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_parent_access.py"
stand: 2026-10-12 21:44
generator: schulmanager-regen
---

# Routen features_parent_access

> API-Routen · 1 Datei(en) · 162 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Elternzugriff (A-44): volljährige Schüler/innen legen je Bereich fest, was ihre Eltern sehen dürfen.

* `GET /parent-access` – eigene Einstellung (nur Schüler/innen): volljährig?, Bereiche mit ja/nein (nur
  `ACTIVE_AREAS` – Bereiche, die die Einwilligung schon prüfen), Zustellung von Rundschreiben (`delivery`:
  `self|parents|both`), `needs_decision` (volljährig, aber noch nie gespeichert → Hinweis in der Oberfläche),
  verknüpfte Elternkonten (Namen).
* `PUT /parent-access` – `{"areas": {"kursraeume": true, …}, "delivery": "both", "confirm": true}`; nur
  volljährig, sonst 403. Jedes Speichern gilt als Entscheidung (der Hinweis verschwindet). Protokolliert.

* `PUT /students/{id}/birth-date` – Geburtsdatum setzen oder löschen (Recht `students.birth_date`; Klassenleitung nur
  für die eigene Klasse). Daraus folgt die Volljährigkeit (``). Protokolliert.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_parent_access.py` | 162 | Elternzugriff (A-44): volljährige Schüler/innen legen je Bereich fest, was ihre Eltern sehen dürfen. |

## Endpunkte (3)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/parent-access` | `get_parent_access` (`features_parent_access.py:70`) | (angemeldet) | [[Feature elternzugriff]] |
| PUT | `/api/v1/parent-access` | `put_parent_access` (`features_parent_access.py:76`) | (angemeldet) | [[Feature elternzugriff]] |
| PUT | `/api/v1/students/{student_id}/birth-date` | `put_birth_date` (`features_parent_access.py:135`) | (angemeldet) | [[Feature students]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `ParentAccessIn` (`schulmanager/server/routes/features_parent_access.py:35`)
- Klasse `BirthDateIn` (`schulmanager/server/routes/features_parent_access.py:106`)
- Funktion `may_set_birth_date` (`schulmanager/server/routes/features_parent_access.py:111`) – Recht `students.birth_date`; mit Scope `class_teacher` nur Schüler/innen der geleiteten Klassen.
- Funktion `check_birth_date` (`schulmanager/server/routes/features_parent_access.py:126`)

## Datenbank-Tabellen

- **Nutzt:** `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen features_common]] – `features_common` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `absence_access`, `parent_access`
- [[Server events]] – `events`

## Wird genutzt von

- [[Routen features_classes]]
- [[Routen features_data]]

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_channels.py`, `tests/test_channels_parents.py`, `tests/test_forms.py`, `tests/test_lead_integration.py`, `tests/test_letters.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_support.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
