---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/me.py"
stand: 2026-10-12 21:44
generator: schulmanager-regen
---

# Routen me

> API-Routen · 1 Datei(en) · 127 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Eigenes Konto: DSGVO-Datenexport, persönlicher iCal-Link.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/me.py` | 127 | Eigenes Konto: DSGVO-Datenexport, persönlicher iCal-Link. |

## Endpunkte (4)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/me/ical-url` | `get_ical_url` (`me.py:29`) | (angemeldet) | [[Seite ProfilePage]] |
| POST | `/api/v1/me/ical-url` | `reset_ical_url` (`me.py:40`) | (angemeldet) | [[Seite ProfilePage]] |
| DELETE | `/api/v1/me/ical-url` | `delete_ical_url` (`me.py:51`) | (angemeldet) | – |
| GET | `/api/v1/me/export` | `export_my_data` (`me.py:69`) | (angemeldet) | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `ical_url` (`schulmanager/server/routes/me.py:24`)

## Datenbank-Tabellen

- **Nutzt:** `announcements`, `audit_log` → [[Datenmodell#Planungsdokument und Protokoll]]
- **Nutzt:** `api_tokens`, `login_attempts`, `sessions`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Routen features_contact]] – `features_contact` *(nur zur Laufzeit importiert)*
- [[Routen features_forms]] – `features_forms` *(nur zur Laufzeit importiert)*
- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Routen features_student_self]] – `features_student_self` *(nur zur Laufzeit importiert)*
- [[Routen features_teacher_profile]] – `features_teacher_profile` *(nur zur Laufzeit importiert)*
- [[Server audit]] – `audit`
- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server konten und anmeldung]] – `accounts`, `identities`, `security`
- [[Server store]] – `store`

## Wird genutzt von

- –

## Tests

`tests/test_forms.py`, `tests/test_login_policy.py`, `tests/test_server_core.py`, `tests/test_server_features.py`, `tests/test_student_absence_access.py`, `tests/test_student_self.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
