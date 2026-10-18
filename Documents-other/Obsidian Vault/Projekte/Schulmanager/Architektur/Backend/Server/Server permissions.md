---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/permissions.py"
stand: 2026-10-12 22:25
generator: schulmanager-regen
---

# Server permissions

> Server-Kern · 1 Datei(en) · 556 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Rollen- und Rechtekatalog als Code: 12 Rollen, 39 Rechte (`CATALOGUE`, `PERMISSIONS`), Standardzuordnung `ROLE_PERMISSIONS`, Umfänge `PERMISSION_SCOPES`, feste Mindestregeln (`LOCKED_GRANT`, `LOCKED_DENY`, `ASSIGNABLE_ONLY`, `SCOPE_LIMIT`) und `effective_rights` (Standard → Abweichungen → feste Regeln). Hilfen für Datenumfang: `teacher_class_ids`, `own_class_ids`, `branch_class_ids`. Siehe [[Rollen und Rechte]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/permissions.py` | 556 | Rollen- und Rechtematrix (ARCHITECTURE.md §6, docs/ROLLEN-RECHTE.md). |

## Wichtige Funktionen und Klassen

- Funktion `scope_options` (`schulmanager/server/permissions.py:388`) – Wählbare Umfänge (`all` = uneingeschränkt) für ein Recht in einer Rolle; leer = nicht einstellbar.
- Funktion `lock_info` (`schulmanager/server/permissions.py:397`) – `{"state": "granted"|"denied", "reason": …}`, wenn das Recht in der Rolle fest vorgegeben ist.
- Funktion `validate_override` (`schulmanager/server/permissions.py:418`) – Fehlertext, wenn die Änderung gegen eine feste Regel verstößt, sonst `None`.
- Funktion `effective_rights` (`schulmanager/server/permissions.py:436`) – Wirksame Rechte und Einschränkungen einer Rolle: Standard + Schul-Einstellungen, danach feste Regeln.
- Funktion `permissions_for` (`schulmanager/server/permissions.py:472`) – Rechte einer Rolle (Standard bzw. mit Schul-Einstellungen `overrides`). Nur volljährige Schüler
- Funktion `scope_for` (`schulmanager/server/permissions.py:480`) – Einschränkung eines Rechts für die Rolle (`None` = uneingeschränkt).
- Funktion `manageable_roles` (`schulmanager/server/permissions.py:485`)
- Funktion `can_manage_role` (`schulmanager/server/permissions.py:489`) – Darf `actor_role` Konten der Rolle `target_role` verwalten?
- Funktion `teacher_class_ids` (`schulmanager/server/permissions.py:494`) – Klassen, die eine Lehrkraft unterrichtet (irgendein Kursteil) oder als Klassenleitung führt.
- Funktion `lead_class_ids` (`schulmanager/server/permissions.py:508`) – Klassen, die eine Lehrkraft als Klassenleitung führt.
- Funktion `teacher_course_ids` (`schulmanager/server/permissions.py:515`) – Kurse, in denen die Lehrkraft mindestens einen Kursteil unterrichtet.
- Funktion `branch_class_ids` (`schulmanager/server/permissions.py:522`) – Klassen der Zweige (`branches`: Liste von `{sites, grades, class_ids}`): Klasse gehört dazu, wenn ihre ID,
- Funktion `own_class_ids` (`schulmanager/server/permissions.py:534`) – Eigene Klassen eines Benutzers (`AuthUser`): Lehrkraft → unterrichtete Klassen, Abteilungsleitung zusätzlich
- Funktion `matrix` (`schulmanager/server/permissions.py:547`) – Rechtematrix (Standard) für das Frontend (`GET /api/v1/roles`); wirksame Werte: `rights.effective_matrix`.

## Hängt ab von

- [[Modul models]] – `models`

## Wird genutzt von

- [[Modul messaging]]
- [[Routen features_channels]]
- [[Routen features_common]]
- [[Routen features_contact]]
- [[Routen features_forms]]
- [[Routen features_letters]]
- [[Routen features_login_policy]]
- [[Routen features_register]]
- [[Routen rights]]
- [[Routen system]]
- [[Routen users]]
- [[Server absence_log]]
- [[Server deps]]
- [[Server files]]
- [[Server konten und anmeldung]] – `accounts`, `identities`, `login_policy`
- [[Server letters und pdf]] – `letters`
- [[Server rights]]

## Tests

`tests/test_api_access.py`, `tests/test_channels.py`, `tests/test_forms.py`, `tests/test_rights.py`, `tests/test_server_core.py`, `tests/test_student_absence_access.py`, `tests/test_student_self.py`, `tests/test_support_catalog.py`, `tests/test_teacher_scope.py`, `tests/test_viewer_role.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
