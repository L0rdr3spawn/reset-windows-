---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_support.py"
stand: 2026-10-12 20:29
generator: schulmanager-regen
---

# Routen features_support

> API-Routen · 1 Datei(en) · 549 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Förderinformationen je Schüler/in: Nachteilsausgleich, Schulbegleitung, Förderplan, Merkmale (mit Nachweisen).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_support.py` | 549 | Förderinformationen je Schüler/in: Nachteilsausgleich, Schulbegleitung, Förderplan, Merkmale (mit N… |

## Endpunkte (11)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/support/catalog` | `get_catalog` (`features_support.py:176`) | (angemeldet) | [[Feature students]] |
| POST | `/api/v1/support/catalog` | `create_catalog` (`features_support.py:197`) | (angemeldet) | [[Feature students]] |
| PUT | `/api/v1/support/catalog/{cid}` | `update_catalog` (`features_support.py:216`) | (angemeldet) | [[Feature students]] |
| DELETE | `/api/v1/support/catalog/{cid}` | `delete_catalog` (`features_support.py:232`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/students/{sid}/support` | `list_support` (`features_support.py:253`) | (angemeldet) | [[Feature students]] |
| POST | `/api/v1/students/{sid}/support` | `create_support` (`features_support.py:311`) | (angemeldet) | [[Feature students]] |
| PUT | `/api/v1/students/{sid}/support/{support_id}` | `update_support` (`features_support.py:335`) | (angemeldet) | – |
| DELETE | `/api/v1/students/{sid}/support/{support_id}` | `delete_support` (`features_support.py:350`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/students/support-flags` | `flags` (`features_support.py:391`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/exams/support-hints` | `exam_hints` (`features_support.py:416`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/students/{sid}/people` | `student_people` (`features_support.py:494`) | (angemeldet) | [[Feature students]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `SupportIn` (`schulmanager/server/routes/features_support.py:40`)
- Klasse `CatalogIn` (`schulmanager/server/routes/features_support.py:53`)
- Funktion `ensure_catalog` (`schulmanager/server/routes/features_support.py:73`) – Katalog der Schule; ist er leer, werden die Vorgaben angelegt.
- Funktion `support_flags` (`schulmanager/server/routes/features_support.py:363`) – Kennzeichen je Schüler/in (Bezeichnungen der aktuell gültigen Einträge) für Klassenbuch/Listen.

## Datenbank-Tabellen

- **Nutzt:** `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]
- **Nutzt:** `student_support` → [[Datenmodell#Schüler, Klassenbuch und Noten]]
- **Nutzt:** `support_catalog` → [[Datenmodell#Sonstige Tabellen]]

## Hängt ab von

- [[Routen features_common]] – `features_common`
- [[Routen features_grades]] – `features_grades`
- [[Server crypto]] – `crypto`
- [[Server db]] – `db`, `db_models`, `support`
- [[Server deps]] – `deps`
- [[Server files]] – `files`

## Wird genutzt von

- [[Routen features_register]]

## Tests

`tests/test_absence_stats_adult.py`, `tests/test_api_access.py`, `tests/test_lead_integration.py`, `tests/test_letters.py`, `tests/test_server_features.py`, `tests/test_support.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
