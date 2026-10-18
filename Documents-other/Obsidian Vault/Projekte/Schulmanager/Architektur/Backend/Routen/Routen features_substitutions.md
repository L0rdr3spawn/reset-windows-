---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_substitutions.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Routen features_substitutions

> API-Routen · 1 Datei(en) · 671 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Vertretungsplan, Abwesenheiten, manuelle Entscheidungen (Overrides), persönliche Tages-/Wochenansicht und Monitor.

Alle Änderungen laufen über `store.mutate` (Version, Audit, Event `change` mit `dates`). Vertretungspläne werden pro `(store.version, datum)` gecacht.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_substitutions.py` | 671 | Vertretungsplan, Abwesenheiten, manuelle Entscheidungen (Overrides), |

## Endpunkte (17)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/substitutions` | `substitutions` (`features_substitutions.py:151`) | substitution.read | [[Seite DashboardPage]], [[Seite PrintSubstitutionsPage]], [[Seite SubstitutionsPage]] |
| GET | `/api/v1/substitutions/range` | `substitutions_range` (`features_substitutions.py:173`) | substitution.read | – |
| GET | `/api/v1/substitutions/candidates` | `candidates` (`features_substitutions.py:187`) | substitution.edit | [[Seite SubstitutionsPage]] |
| GET | `/api/v1/substitutions/stats` | `stats` (`features_substitutions.py:204`) | (angemeldet) | [[Seite SubstitutionsPage]] |
| GET | `/api/v1/absences` | `list_absences` (`features_substitutions.py:250`) | (angemeldet) | [[Seite SubstitutionsPage]] |
| POST | `/api/v1/absences` | `create_absence` (`features_substitutions.py:294`) | substitution.edit | [[Seite SubstitutionsPage]] |
| PUT | `/api/v1/absences/{absence_id}` | `update_absence` (`features_substitutions.py:311`) | substitution.edit | [[Seite SubstitutionsPage]] |
| DELETE | `/api/v1/absences/{absence_id}` | `delete_absence` (`features_substitutions.py:334`) | (angemeldet) | [[Feature classes]], [[Seite SubstitutionsPage]] |
| POST | `/api/v1/absences/report-self` | `report_self` (`features_substitutions.py:364`) | absence.report_self | [[Seite DashboardPage]] |
| GET | `/api/v1/overrides` | `list_overrides` (`features_substitutions.py:412`) | substitution.edit | [[Seite SubstitutionsPage]] |
| POST | `/api/v1/overrides` | `create_override` (`features_substitutions.py:428`) | substitution.edit | [[Seite SubstitutionsPage]] |
| DELETE | `/api/v1/overrides/{override_id}` | `delete_override` (`features_substitutions.py:471`) | substitution.edit | [[Seite SubstitutionsPage]] |
| GET | `/api/v1/me/today` | `me_today` (`features_substitutions.py:539`) | (angemeldet) | [[Seite DashboardPage]] |
| GET | `/api/v1/me/week` | `me_week` (`features_substitutions.py:552`) | (angemeldet) | – |
| GET | `/api/v1/monitor/config` | `monitor_config_list` (`features_substitutions.py:603`) | monitor.manage | [[Seite MonitorAdminPage]] |
| PUT | `/api/v1/monitor/config/{site}` | `monitor_config_save` (`features_substitutions.py:612`) | monitor.manage | [[Seite MonitorAdminPage]] |
| GET | `/api/v1/monitor` | `monitor` (`features_substitutions.py:628`) | monitor.read | [[Seite MonitorPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `AbsenceIn` (`schulmanager/server/routes/features_substitutions.py:226`)
- Klasse `SelfReportIn` (`schulmanager/server/routes/features_substitutions.py:236`)
- Klasse `OverrideIn` (`schulmanager/server/routes/features_substitutions.py:399`)
- Funktion `build_day_view` (`schulmanager/server/routes/features_substitutions.py:497`) – Persönlicher Tag: eigene Vertretungsplan-Einträge, effektive Stunden, Klausuren.
- Klasse `MonitorNoticeIn` (`schulmanager/server/routes/features_substitutions.py:578`)
- Klasse `MonitorConfigIn` (`schulmanager/server/routes/features_substitutions.py:584`)
- Funktion `monitor_config` (`schulmanager/server/routes/features_substitutions.py:594`) – Einstellungen des Monitors (Standort, sonst „alle“), abgelaufene Hinweise ausgeblendet.

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul substitution]] – `substitution` *(nur zur Laufzeit importiert)*
- [[Modul weeks]] – `weeks` *(nur zur Laufzeit importiert)*
- [[Routen features_announcements]] – `features_announcements` *(nur zur Laufzeit importiert)*
- [[Routen features_common]] – `features_common`
- [[Routen features_exams]] – `features_exams` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`
- [[Server deps]] – `deps`

## Wird genutzt von

- [[Routen api_open]]
- [[Routen features_calendar]]
- [[Routen features_classes]]
- [[Routen features_student_absences]]
- [[Routen features_student_self]]

## Tests

`tests/test_absence_log.py`, `tests/test_api_access.py`, `tests/test_channels.py`, `tests/test_channels_rooms.py`, `tests/test_classes.py`, `tests/test_lead_integration.py`, `tests/test_lesson_absence.py`, `tests/test_makeups.py`, `tests/test_monitor_config.py`, `tests/test_server_features.py`, `tests/test_substitution_b04.py`, `tests/test_teacher_scope.py` …

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
