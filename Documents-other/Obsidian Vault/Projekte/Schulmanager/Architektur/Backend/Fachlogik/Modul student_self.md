---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/student_self.py"
stand: 2026-10-12 21:13
generator: schulmanager-regen
---

# Modul student_self

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 99 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Schüler-Selbstbedienung – reine Logik ohne Datenbank (Regeln für eigene Krankmeldungen, Dokumente und Sichtbarkeit). Die Endpunkte stehen in [[Routen features_student_self]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/student_self.py` | 99 | Schüler-Selbstbedienung (ARCHITECTURE.md §9.6): reine Logik ohne Datenbank. |

## Wichtige Funktionen und Klassen

- Klasse `AttestInfo` (`schulmanager/student_self.py:39`)
  - Methoden: `missing`:46, `to_dict`:50
- Funktion `absence_school_days` (`schulmanager/student_self.py:55`) – Schultage einer Abwesenheit (Tage ohne Unterricht der Klasse und Ferien zählen nicht; `cls` = Klasse bzw.
- Funktion `attest_info` (`schulmanager/student_self.py:65`) – Attest-Zustand einer Krankmeldung aus Zeitraum und den Status der zugeordneten Atteste (gezählt werden die
- Funktion `self_report_hint` (`schulmanager/student_self.py:87`) – Hinweis, warum (bzw. `None`, wenn) eine Person keine eigene Krankmeldung abgeben darf.
- Funktion `clean_title` (`schulmanager/student_self.py:96`)

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils`
- [[Modul models]] – `models`

## Wird genutzt von

- [[Routen features_student_absences]]
- [[Routen features_student_self]]

## Tests

`tests/test_student_self.py`, `tests/test_weeks.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
