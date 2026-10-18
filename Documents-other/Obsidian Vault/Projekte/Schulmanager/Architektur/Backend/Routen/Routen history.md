---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/history.py"
stand: 2026-10-12 22:27
generator: schulmanager-regen
---

# Routen history

> API-Routen · 1 Datei(en) · 80 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Verlauf des Planungsdokuments (Versionen, Wiederherstellen, Rückgängig) und Audit-Protokoll.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/history.py` | 80 | Verlauf des Planungsdokuments (Versionen, Wiederherstellen, Rückgängig) und Audit-Protokoll. |

## Endpunkte (5)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/history` | `history` (`history.py:21`) | history.restore | [[Seite HistoryPage]] |
| GET | `/api/v1/history/{version}` | `history_version` (`history.py:28`) | history.restore | – |
| POST | `/api/v1/history/{version}/restore` | `restore` (`history.py:41`) | history.restore | [[Seite HistoryPage]] |
| POST | `/api/v1/history/undo` | `undo` (`history.py:52`) | history.restore | [[Seite HistoryPage]] |
| GET | `/api/v1/audit` | `audit_log` (`history.py:62`) | audit.read | [[Seite HistoryPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Datenbank-Tabellen

- **Nutzt:** `audit_log` → [[Datenmodell#Planungsdokument und Protokoll]]

## Hängt ab von

- [[Modul models]] – `models`
- [[Server audit]] – `audit`
- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server store]] – `store`

## Wird genutzt von

- –

## Tests

`tests/test_absence_log.py`, `tests/test_api_access.py`, `tests/test_autoplan.py`, `tests/test_contact.py`, `tests/test_curricula.py`, `tests/test_letters.py`, `tests/test_messages.py`, `tests/test_server_core.py`, `tests/test_server_core_store.py`, `tests/test_student_absence_access.py`, `tests/test_student_self.py`, `tests/test_teacher_profile.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
