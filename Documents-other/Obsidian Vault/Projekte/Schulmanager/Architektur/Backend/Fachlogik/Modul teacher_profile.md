---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/teacher_profile.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul teacher_profile

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 768 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Lehrer-Selbstverwaltung: Zeitfenster (`Teacher.time_windows`) werden in Sperrzeiten umgerechnet, Profiländerungen werden auf Konflikte mit dem Plan geprüft und als Antrag formuliert. Endpunkte: [[Routen features_teacher_profile]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/teacher_profile.py` | 768 | Lehrer-Selbstverwaltung: Zeitfenster → Sperrzeiten, Profiländerungen und Konflikte (reine Logik). |

## Wichtige Funktionen und Klassen

- Klasse `ProfileError` (`schulmanager/teacher_profile.py:56`) – Ungültige Profilangaben; `errors` enthält deutsche Meldungen.
- Funktion `to_minutes` (`schulmanager/teacher_profile.py:65`) – `"HH:MM"` → Minuten seit Mitternacht (`"24:00"` nur mit `allow_24`). ValueError bei Unsinn.
- Funktion `fmt_minutes` (`schulmanager/teacher_profile.py:76`)
- Funktion `period_minutes` (`schulmanager/teacher_profile.py:80`)
- Funktion `period_spans` (`schulmanager/teacher_profile.py:87`) – `[(beginn, ende)]` in Minuten je Stunde des Rasters (`None` bei fehlender/ungültiger Zeit).
- Funktion `period_label` (`schulmanager/teacher_profile.py:102`)
- Funktion `normalize_windows` (`schulmanager/teacher_profile.py:126`) – Prüft und normalisiert Zeitfenster → `[{"days","start","end","weeks"}]` (ProfileError bei Fehlern).
- Funktion `window_applies` (`schulmanager/teacher_profile.py:177`) – Gilt das Fenster am (laufende Woche, Tag)? Unbekannte Woche (`None`) = ja.
- Funktion `available_periods` (`schulmanager/teacher_profile.py:184`) – Stunden, die am (laufende Woche, Tag) komplett in einem Zeitfenster liegen (leere Fensterliste = alle).
- Funktion `availability` (`schulmanager/teacher_profile.py:213`) – Vorschau je Tag und Gruppe gleicher Wochen: `[{"weeks","rhythm","weeks_text","day","day_name",
- Funktion `windows_to_rules` (`schulmanager/teacher_profile.py:236`) – Rechnet Zeitfenster in harte Sperrzeiten um (kompakt: gleiche Sperren werden über Tage/Wochen gebündelt).
- Funktion `normalize_work_grid` (`schulmanager/teacher_profile.py:280`) – Prüft das Arbeitszeiten-Raster → `{"weeks": N, "blocked": [{"week","day","periods"}]}` bzw. `{}` (keine
- Funktion `grid_to_rules` (`schulmanager/teacher_profile.py:324`) – Raster → harte Sperrzeiten: in allen Rasterwochen gleich gesperrte Stunden ohne Rhythmus, sonst je Rasterwoche
- Funktion `describe_grid` (`schulmanager/teacher_profile.py:346`)
- Funktion `is_window_rule` (`schulmanager/teacher_profile.py:355`)
- Funktion `strip_window_rules` (`schulmanager/teacher_profile.py:359`) – Sperrzeiten ohne die aus Zeitfenstern erzeugten Regeln.
- Funktion `apply_windows` (`schulmanager/teacher_profile.py:364`) – Ersetzt die Zeitfenster-Sperrzeiten der Lehrkraft (andere Sperrzeiten bleiben unangetastet).
- Funktion `refresh_all_windows` (`schulmanager/teacher_profile.py:370`) – Nach Änderungen am Zeitraster: Zeitfenster-Sperrzeiten aller Lehrkräfte neu berechnen. Gibt die Anzahl
- Funktion `describe_windows` (`schulmanager/teacher_profile.py:419`) – Kurzbeschreibung, z. B. „Mo–Fr 10:00–18:30; Woche 2: Fr 08:00–12:00“.
- Funktion `teacher_profile` (`schulmanager/teacher_profile.py:440`) – Aktuelle Selbstauskunft einer Lehrkraft (Profilfelder als JSON-Dict).
- Funktion `validate_profile` (`schulmanager/teacher_profile.py:458`) – Prüft eine Profiländerung und liefert das vollständige, normalisierte Profil.
- Funktion `apply_profile` (`schulmanager/teacher_profile.py:592`) – Übernimmt ein (validiertes) Profil in `school` (Zeitfenster → Sperrzeiten). KeyError, wenn unbekannt.
- Funktion `diff_profile` (`schulmanager/teacher_profile.py:614`) – Vergleich alt/neu: `[{"field","label","old","new","old_text","new_text"}]` (nur geänderte Felder).
- Funktion `teacher_courses` (`schulmanager/teacher_profile.py:650`) – `[(Kurs, [Teil-Indizes der Lehrkraft])]`.
- Funktion `current_load` (`schulmanager/teacher_profile.py:660`) – Ist-Deputat aus den zugewiesenen Kursteilen (wie `timetable.validate_school`).
- Funktion `lesson_conflicts` (`schulmanager/teacher_profile.py:673`) – Stunden der Lehrkraft, die in den Sperrzeiten `rules` lägen.
- Funktion `conflicts` (`schulmanager/teacher_profile.py:711`) – Konflikte einer (geplanten) Profiländerung gegenüber dem aktuellen Stundenplan.

## Hängt ab von

- [[Modul calendar_utils]] – `calendar_utils` *(nur zur Laufzeit importiert)*
- [[Modul models]] – `models`
- [[Modul weeks]] – `weeks`

## Wird genutzt von

- [[Modul demo]]
- [[Modul integrations]] – `csv_io`
- [[Routen features_data]]
- [[Routen features_teacher_profile]]

## Tests

`tests/test_teacher_profile.py`, `tests/test_weeks_solver.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
