---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_teacher_profile.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen features_teacher_profile

> API-Routen · 1 Datei(en) · 524 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Lehrer-Selbstverwaltung (ARCHITECTURE.md §9.3).

Lehrkräfte (Recht `profile.teacher_self`, Konto mit `teacher_id`) pflegen Fächer, Wunschklassen, Deputat, Arbeitszeitfenster und weiche Wünsche. Je nach `settings.teacher_self_service`:

* `"approval"` – Änderung wird als Antrag gespeichert (ein offener Antrag je Lehrkraft, erneutes Absenden
  aktualisiert ihn); Planung/Schulleitung (`teacher_requests.review`) genehmigt oder lehnt ab (mit Kommentar).
* `"direct"` – Änderung wird sofort übernommen (protokolliert als genehmigter Antrag mit `auto: true`).

Nicht vorhandene Fächer kann die Lehrkraft als `new_subjects` vorschlagen; solche Änderungen gehen **immer** als Antrag an die Planung (auch im Modus `direct`) und legen das Fach erst bei der Genehmigung an (Prüfende brauchen zusätzlich `masterdata.edit`).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_teacher_profile.py` | 524 | Lehrer-Selbstverwaltung (ARCHITECTURE.md §9.3). |

## Endpunkte (10)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/me/teacher-profile` | `my_profile` (`features_teacher_profile.py:279`) | profile.teacher_self | [[Feature teacher]] |
| POST | `/api/v1/me/teacher-profile/preview` | `my_profile_preview` (`features_teacher_profile.py:305`) | profile.teacher_self | [[Feature teacher]] |
| PUT | `/api/v1/me/teacher-profile` | `change_my_profile` (`features_teacher_profile.py:312`) | profile.teacher_self | [[Feature teacher]] |
| DELETE | `/api/v1/me/teacher-profile/request` | `withdraw_my_request` (`features_teacher_profile.py:369`) | profile.teacher_self | [[Feature teacher]] |
| GET | `/api/v1/teacher-requests/summary` | `requests_summary` (`features_teacher_profile.py:385`) | teacher_requests.review | [[Feature teacher]] |
| GET | `/api/v1/teacher-requests` | `list_requests` (`features_teacher_profile.py:398`) | teacher_requests.review | [[Feature teacher]] |
| GET | `/api/v1/teacher-requests/{request_id}` | `get_request` (`features_teacher_profile.py:428`) | teacher_requests.review | [[Feature teacher]] |
| POST | `/api/v1/teacher-requests/{request_id}/approve` | `approve_request` (`features_teacher_profile.py:441`) | teacher_requests.review | [[Feature teacher]] |
| POST | `/api/v1/teacher-requests/{request_id}/reject` | `reject_request` (`features_teacher_profile.py:479`) | teacher_requests.review | [[Feature teacher]] |
| POST | `/api/v1/teacher-profiles/{teacher_id}/preview` | `teacher_preview` (`features_teacher_profile.py:495`) | (angemeldet) | [[Feature teacher]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `WeekPatternIn` (`schulmanager/server/routes/features_teacher_profile.py:45`) – Älteres Muster „jede k. Woche ab Woche s (bis Woche e)“ (nur in Requests; wird zum Rhythmus).
- Klasse `RhythmIn` (`schulmanager/server/routes/features_teacher_profile.py:53`) – Rhythmus in laufenden Wochen (alle k Wochen ab Woche s; `to_week` 0 = offen).
- Klasse `WindowIn` (`schulmanager/server/routes/features_teacher_profile.py:64`)
- Klasse `RuleIn` (`schulmanager/server/routes/features_teacher_profile.py:74`)
- Klasse `NewSubjectIn` (`schulmanager/server/routes/features_teacher_profile.py:84`) – Vorschlag für ein noch nicht vorhandenes Fach.
- Klasse `ProfileIn` (`schulmanager/server/routes/features_teacher_profile.py:92`) – Profil (alle Felder optional – fehlende bleiben unverändert).
- Klasse `ProfileChangeIn` (`schulmanager/server/routes/features_teacher_profile.py:105`)
- Klasse `ReviewIn` (`schulmanager/server/routes/features_teacher_profile.py:109`)
- Funktion `may_edit_times` (`schulmanager/server/routes/features_teacher_profile.py:299`) – Arbeitszeiten selbst festlegen: nur mit Freigabe der Schule (allgemein oder für diese Lehrkraft).
- Funktion `export_requests` (`schulmanager/server/routes/features_teacher_profile.py:508`) – Eigene Anträge (entschlüsselt) für den Datenexport des Kontos.

## Datenbank-Tabellen

- **Nutzt:** `teacher_change_requests` → [[Datenmodell#Lehrkräfte]]
- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul legacy]] – `legacy` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul teacher_profile]] – `teacher_profile`
- [[Routen features_common]] – `features_common`
- [[Server crypto]] – `crypto` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`, `db_models`, `teacher`
- [[Server deps]] – `deps`
- [[Server events]] – `events` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen me]]

## Tests

`tests/test_curricula.py`, `tests/test_teacher_profile.py`, `tests/test_weeks_api.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
