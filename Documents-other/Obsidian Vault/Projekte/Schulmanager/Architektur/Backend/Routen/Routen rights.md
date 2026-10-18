---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/rights.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen rights

> API-Routen · 1 Datei(en) · 219 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Rollen & Rechte: Katalog, wirksame Matrix, Änderungen je Rolle, Schulzweige und Zuordnungen.

* `GET  /rights` – Katalog, Rollen, Matrix (Standard vs. wirksam), feste Regeln.
* `PUT  /rights/roles/{role}` / `POST /rights/roles/{role}/reset` – Rechte einer Rolle ändern/zurücksetzen.
* `GET/POST/PUT/DELETE /rights/branches` – Schulzweige (Abteilungsleitung).
* `GET /rights/assignments` / `PUT /rights/assignments/{user_id}` – Zweige bzw. Kinder (Schulbegleitung) zuordnen.
* `GET /rights/me` – „Ihre Rolle“ inkl. abgeleiteter Titel (Klassenleitung, Zweig).
Jede Änderung wird im Audit-Protokoll festgehalten.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/rights.py` | 219 | Rollen & Rechte: Katalog, wirksame Matrix, Änderungen je Rolle, Schulzweige und Zuordnungen. |

## Endpunkte (10)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/rights` | `get_rights` (`rights.py:55`) | - | [[Seite RightsPage]] |
| PUT | `/api/v1/rights/roles/{role}` | `put_role` (`rights.py:61`) | rights.manage | [[Seite RightsPage]] |
| POST | `/api/v1/rights/roles/{role}/reset` | `reset_role` (`rights.py:77`) | rights.manage | [[Seite RightsPage]] |
| GET | `/api/v1/rights/branches` | `list_branches` (`rights.py:102`) | - | [[Seite RightsPage]] |
| POST | `/api/v1/rights/branches` | `create_branch` (`rights.py:112`) | rights.manage | [[Seite RightsPage]] |
| PUT | `/api/v1/rights/branches/{branch_id}` | `update_branch` (`rights.py:128`) | rights.manage | [[Seite RightsPage]] |
| DELETE | `/api/v1/rights/branches/{branch_id}` | `delete_branch` (`rights.py:146`) | rights.manage | [[Seite RightsPage]] |
| GET | `/api/v1/rights/assignments` | `list_assignments` (`rights.py:162`) | rights.manage | [[Seite RightsPage]] |
| PUT | `/api/v1/rights/assignments/{user_id}` | `put_assignment` (`rights.py:181`) | rights.manage | [[Seite RightsPage]] |
| GET | `/api/v1/rights/me` | `my_role` (`rights.py:210`) | (angemeldet) | [[Seite ProfilePage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `PermChange` (`schulmanager/server/routes/rights.py:32`)
- Klasse `RoleChanges` (`schulmanager/server/routes/rights.py:37`)
- Klasse `BranchIn` (`schulmanager/server/routes/rights.py:42`)
- Klasse `AssignmentIn` (`schulmanager/server/routes/rights.py:49`)

## Datenbank-Tabellen

- **Nutzt:** `branches`, `user_branches` → [[Datenmodell#Rollen und Rechte]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server permissions]] – `permissions`
- [[Server rights]] – `rights`
- [[Server store]] – `store`

## Wird genutzt von

- –

## Tests

`tests/test_rights.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
