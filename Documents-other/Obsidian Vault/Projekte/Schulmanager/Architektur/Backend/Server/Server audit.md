---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/audit.py"
stand: 2026-10-12 20:28
generator: schulmanager-regen
---

# Server audit

> Server-Kern · 1 Datei(en) · 57 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

`audit(db, user, aktion, ziel, details)`: schreibt das Audit-Protokoll (`audit_log`). Jede schreibende Aktion muss auditieren; committet nicht selbst. Lesen über `GET /audit` ([[Routen history]]).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/audit.py` | 57 | Audit-Protokoll. |

## Wichtige Funktionen und Klassen

- Funktion `audit` (`schulmanager/server/audit.py:33`) – Protokolliert eine Aktion. `user`: `AuthUser`, ORM-`User` oder `None` (System).
- Funktion `audit_now` (`schulmanager/server/audit.py:43`) – Wie ``, aber sofort in eigener Transaktion (Fehler werden nur geloggt).
- Funktion `audit_dict` (`schulmanager/server/audit.py:52`)

## Datenbank-Tabellen

- **Nutzt:** `audit_log` → [[Datenmodell#Planungsdokument und Protokoll]]

## Hängt ab von

- [[Server db]] – `db`, `db_models`

## Wird genutzt von

- [[Routen admin]]
- [[Routen api_open]]
- [[Routen auth]]
- [[Routen features_api_access]]
- [[Routen features_channels]]
- [[Routen features_classes]]
- [[Routen features_common]]
- [[Routen features_contact]]
- [[Routen features_letters]]
- [[Routen features_login_policy]]
- [[Routen features_mail]]
- [[Routen features_messages]]
- [[Routen features_parent_access]]
- [[Routen features_sso]]
- [[Routen history]]
- [[Routen license]]
- [[Routen me]]
- [[Routen rights]]
- [[Routen users]]
- [[Server betrieb]] – `backups`, `cli`
- [[Server files]]
- [[Server store]]

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
