---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/features_student_self.py"
stand: 2026-10-12 22:40
generator: schulmanager-regen
---

# Routen features_student_self

> API-Routen · 1 Datei(en) · 566 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Schüler-Selbstbedienung, Atteste & Dokumente (ARCHITECTURE.md §9.6).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/features_student_self.py` | 566 | Schüler-Selbstbedienung, Atteste & Dokumente (ARCHITECTURE.md §9.6). |

## Endpunkte (6)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/student-documents` | `list_documents` (`features_student_self.py:223`) | (angemeldet) | [[Feature students]] |
| POST | `/api/v1/student-documents` | `submit_document` (`features_student_self.py:253`) | (angemeldet) | [[Feature students]] |
| PATCH | `/api/v1/student-documents/{doc_id}` | `handle_document` (`features_student_self.py:313`) | (angemeldet) | [[Feature students]] |
| DELETE | `/api/v1/student-documents/{doc_id}` | `delete_document` (`features_student_self.py:364`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/student-documents/summary` | `documents_summary` (`features_student_self.py:404`) | (angemeldet) | [[Feature students]] |
| GET | `/api/v1/me/student-overview` | `student_overview` (`features_student_self.py:442`) | (angemeldet) | [[Feature students]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Klasse `DocumentIn` (`schulmanager/server/routes/features_student_self.py:52`)
- Klasse `DocumentPatch` (`schulmanager/server/routes/features_student_self.py:61`)
- Funktion `enc` (`schulmanager/server/routes/features_student_self.py:67`)
- Funktion `dec` (`schulmanager/server/routes/features_student_self.py:71`) – Entschlüsselt `SM1.`-Tokens; Altbestand im Klartext bleibt lesbar. Manipulierte Tokens → Platzhalter.
- Funktion `doc_scope` (`schulmanager/server/routes/features_student_self.py:95`) – Schüler-IDs, deren Dokumente `user` sieht (`None` = alle, leer = keine – eigene Einreichungen
- Funktion `adult_student_ids` (`schulmanager/server/routes/features_student_self.py:110`) – Schüler-IDs, die volljährig sind (Geburtsdatum, sonst Konto-Merkmal).
- Funktion `blocked_for_parents` (`schulmanager/server/routes/features_student_self.py:118`) – Volljährige Schüler/innen, deren Eltern Dokumente und Atteste **nicht** sehen dürfen (keine Freigabe im
- Funktion `can_view` (`schulmanager/server/routes/features_student_self.py:136`)
- Funktion `can_handle` (`schulmanager/server/routes/features_student_self.py:142`) – Status/Vermerk setzen: Schulpersonal mit Dokument-Recht für die Schülerin/den Schüler.
- Funktion `doc_out` (`schulmanager/server/routes/features_student_self.py:172`)
- Funktion `attest_map` (`schulmanager/server/routes/features_student_self.py:193`) – Attest-Zustand je Krankmeldung (für Listen der Krankmeldungen).
- Funktion `export_documents` (`schulmanager/server/routes/features_student_self.py:526`) – Metadaten eigener bzw. eigene Kinder betreffender Dokumente (Titel/Vermerk entschlüsselt) – nur, was die
- Funktion `run_retention` (`schulmanager/server/routes/features_student_self.py:550`) – Wartung: Dokumente älter als `days` Tage (samt Datei) löschen; 0 = aus.

## Datenbank-Tabellen

- **Nutzt:** `student_absences`, `student_documents` → [[Datenmodell#Schüler, Klassenbuch und Noten]]

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul student_self]] – `student_self`
- [[Routen features_common]] – `features_common`
- [[Routen features_student_absences]] – `features_student_absences` *(nur zur Laufzeit importiert)*
- [[Routen features_substitutions]] – `features_substitutions` *(nur zur Laufzeit importiert)*
- [[Server absence_log]] – `absence_log`
- [[Server crypto]] – `crypto`
- [[Server db]] – `db`, `db_models`, `student_self`
- [[Server deps]] – `deps`
- [[Server elternzugriff]] – `absence_access`, `parent_access` *(nur zur Laufzeit importiert)*
- [[Server files]] – `files`

## Wird genutzt von

- [[Routen features_forms]]
- [[Routen features_student_absences]]
- [[Routen me]]
- [[Server betrieb]] – `maintenance`

## Tests

`tests/test_attendance.py`, `tests/test_makeups.py`, `tests/test_student_absence_access.py`, `tests/test_student_absence_actions.py`, `tests/test_student_self.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
