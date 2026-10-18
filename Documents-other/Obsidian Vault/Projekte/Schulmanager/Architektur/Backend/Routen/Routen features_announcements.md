---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_announcements.py"
stand: 2026-10-12 22:56
generator: schulmanager-regen
---

# Routen features_announcements

> API-Routen · 1 Datei(en) · 259 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Mitteilungen (Tabelle `announcements`).

Zielgruppen: `all` (alle), `staff` (Kollegium), `classes` (bestimmte Klassen – Schüler, Eltern und Lehrkräfte dieser Klassen); optional zusätzlich auf Rollen (`audience_roles`) und einen Standort beschränkt. `monitor: true` zeigt die Mitteilung auf der Monitor-Ansicht. Lehrkräfte (`announcement.post` mit Scope `own_classes`) dürfen nur an eigene Klassen schreiben.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_announcements.py` | 259 | Mitteilungen (Tabelle `announcements`). |

## Endpunkte (4)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/announcements` | `list_announcements` (`features_announcements.py:194`) | (angemeldet) | [[Feature nachrichten]], [[Seite AnnouncementsPage]] |
| POST | `/api/v1/announcements` | `create_announcement` (`features_announcements.py:208`) | announcement.post | [[Seite AnnouncementsPage]] |
| PUT | `/api/v1/announcements/{announcement_id}` | `update_announcement` (`features_announcements.py:226`) | announcement.post | [[Seite AnnouncementsPage]] |
| DELETE | `/api/v1/announcements/{announcement_id}` | `delete_announcement` (`features_announcements.py:244`) | (angemeldet) | [[Seite AnnouncementsPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `invalidate_cache` (`schulmanager/server/routes/features_announcements.py:35`)
- Funktion `is_visible` (`schulmanager/server/routes/features_announcements.py:85`)
- Funktion `visible_announcements` (`schulmanager/server/routes/features_announcements.py:113`) – Mitteilungen, die `user` am Tag `day` (bis `until`) sehen darf.
- Funktion `can_delete` (`schulmanager/server/routes/features_announcements.py:136`)
- Klasse `AnnouncementIn` (`schulmanager/server/routes/features_announcements.py:142`)

## Datenbank-Tabellen

- **Nutzt:** `announcements` → [[Datenmodell#Planungsdokument und Protokoll]]

## Hängt ab von

- [[Routen features_common]] – `features_common`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `parent_access` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen api_open]]
- [[Routen features_substitutions]]

## Tests

`tests/test_api_access.py`, `tests/test_rights.py`, `tests/test_server_features.py`, `tests/test_viewer_role.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
