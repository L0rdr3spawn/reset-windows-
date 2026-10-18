---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_login_policy.py"
stand: 2026-10-12 22:30
generator: schulmanager-regen
---

# Routen features_login_policy

> API-Routen · 1 Datei(en) · 442 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Anmelde-Richtlinien verwalten (ARCHITECTURE.md §11.5) – Recht `login_policy.manage` (admin, schulleitung).

* `GET /login-policies` – alle Regeln + Auswahl (Rollen, Jahrgänge, Klassen, Anbieter, Wege, Kanäle, Zielgruppen)
* `PUT /login-policies/{scope}/{ref}?audience=` – Regel anlegen/ersetzen (alle Felder `null` = Regel entfernen);
  `scope=default` mit `ref` `-` (oder `PUT /login-policies/default`)
* `DELETE /login-policies/{scope}/{ref}?audience=` – Regel entfernen
* `GET /login-policies/effective?user_id=` | `?class_id=&audience=` | `?grade=&audience=` | `?role=` –
  wirksame Richtlinie mit Herkunft je Feld („Was gilt für …?“)
* `GET /login-policies/report?class_id=&audience=` – Schüler/innen bzw. Eltern der Klasse, denen
  Pflicht-Verknüpfungen fehlen (mit Zählung)

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_login_policy.py` | 442 | Anmelde-Richtlinien verwalten (ARCHITECTURE.md §11.5) – Recht `login_policy.manage` (admin, schulle… |

## Endpunkte (7)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/login-policies` | `list_policies` (`features_login_policy.py:212`) | - | [[Feature anmelderichtlinien]] |
| PUT | `/api/v1/login-policies/default` | `put_default` (`features_login_policy.py:313`) | - | – |
| DELETE | `/api/v1/login-policies/default` | `delete_default` (`features_login_policy.py:319`) | - | – |
| GET | `/api/v1/login-policies/effective` | `effective` (`features_login_policy.py:324`) | - | [[Feature anmelderichtlinien]] |
| GET | `/api/v1/login-policies/report` | `report` (`features_login_policy.py:373`) | - | [[Feature anmelderichtlinien]] |
| PUT | `/api/v1/login-policies/{scope}/{ref}` | `put_rule` (`features_login_policy.py:433`) | - | – |
| DELETE | `/api/v1/login-policies/{scope}/{ref}` | `delete_rule` (`features_login_policy.py:439`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `RuleBody` (`schulmanager/server/routes/features_login_policy.py:41`) – Felder einer Regel – jeweils `null` = erben.

## Datenbank-Tabellen

- **Nutzt:** `login_policy_rules`, `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server audit]] – `audit`
- [[Server db]] – `db`, `db_models`, `login_policy`
- [[Server deps]] – `deps`
- [[Server konten und anmeldung]] – `auth_messages`, `identities`, `login_policy`
- [[Server permissions]] – `permissions`
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_contact.py`, `tests/test_login_policy.py`, `tests/test_self_reset.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
