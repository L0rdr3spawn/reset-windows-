---
tags: [schulmanager, architektur, fachlogik]
quelle: "schulmanager/messaging.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Modul messaging

> Fachlogik (rein, ohne Datenbank und HTTP) · 1 Datei(en) · 828 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Internes Postfach – reine Logik: Empfängerauflösung (Einzelpersonen, Klassen, Kurse, Rollengruppen), Rechte (`check_direct`, `check_group`) und Adressbuch auf Basis von `Directory` (Konten) und `SchoolIndex` (Planungsdokument). Kennt weder Datenbank noch HTTP. **Auffällig:** importiert `server.permissions` und durchbricht damit die Schichtgrenze (Fachlogik → Server).

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/messaging.py` | 828 | Internes Postfach – reine Logik (ARCHITECTURE.md §9.5): Empfängerauflösung, Rechte, Adressbuch. |

## Wichtige Funktionen und Klassen

- Klasse `MessagingError` (`schulmanager/messaging.py:80`) – Fachlicher Fehler (wird von den Routen in `HTTPException(status, message)` übersetzt).
- Funktion `normalize` (`schulmanager/messaging.py:95`) – Für Suche/Vergleich: ohne Akzente, klein (`"Müller"` → `"muller"`; `ß` → `ss`).
- Funktion `clean_subject` (`schulmanager/messaging.py:101`) – Betreff: eine Zeile, ohne Steuerzeichen, Leerraum zusammengefasst.
- Funktion `clean_body` (`schulmanager/messaging.py:106`) – Nachrichtentext: Zeilenumbrüche vereinheitlicht, Steuer- und Richtungszeichen entfernt, außen getrimmt.
- Funktion `query_tokens` (`schulmanager/messaging.py:114`)
- Funktion `snippet` (`schulmanager/messaging.py:118`) – Ausschnitt um den ersten Treffer (für Suchergebnisse).
- Funktion `matches` (`schulmanager/messaging.py:139`) – Alle Suchwörter kommen (akzent-/großschreibungsunabhängig) in den Texten vor.
- Funktion `natural_key` (`schulmanager/messaging.py:148`) – Sortierschlüssel „5a < 10a“.
- Funktion `has` (`schulmanager/messaging.py:154`)
- Funktion `perm_scope` (`schulmanager/messaging.py:158`)
- Funktion `is_staff` (`schulmanager/messaging.py:165`)
- Funktion `rate_class` (`schulmanager/messaging.py:169`)
- Klasse `Account` (`schulmanager/messaging.py:175`) – Ein Konto aus Sicht des Postfachs (Ausschnitt aus `users` + Elternverknüpfungen).
  - Methoden: `reachable`:187, `role_label`:192
- Klasse `Directory` (`schulmanager/messaging.py:196`) – Konten mit Indizes für die Gruppenauflösung (es werden nur erreichbare Konten indiziert).
  - Methoden: `get`:220, `reachable`:226, `students`:229, `parents`:234, `teachers`:237, `roles`:240
- Klasse `SchoolIndex` (`schulmanager/messaging.py:246`) – Schnellzugriffe auf das Planungsdokument (einmal je Planversion aufbauen).
  - Methoden: `build`:263, `class_name`:301, `site_name`:305, `student_class`:309, `subject_name`:313, `course_label`:317, `course_students`:333, `classes_at_site`:354, `teacher_at_site`:357
- Klasse `Group` (`schulmanager/messaging.py:366`)
  - Methoden: `key`:372, `category`:376
- Funktion `split_course_ref` (`schulmanager/messaging.py:380`)
- Funktion `group_label` (`schulmanager/messaging.py:391`) – Beschriftung einer Gruppe; `` (422) bei unbekannter Gruppe/Referenz.
- Funktion `normalize_group` (`schulmanager/messaging.py:435`) – Prüft die Gruppe und normalisiert `ref` (Kursteil eines Ein-Teil-Kurses → ganzer Kurs).
- Funktion `group_student_ids` (`schulmanager/messaging.py:460`) – Schüler-IDs, auf die sich eine Schüler-/Elterngruppe bezieht.
- Funktion `group_members` (`schulmanager/messaging.py:478`) – Konto-IDs (nur erreichbare) einer Gruppe.
- Funktion `check_group` (`schulmanager/messaging.py:506`) – Darf `sender` an diese Gruppe schreiben? Gibt die normalisierte Gruppe zurück, sonst ``.
- Funktion `allowed_groups` (`schulmanager/messaging.py:577`) – Gruppen fürs Adressbuch: ohne Suchtext die „naheliegenden“ (Lehrkraft: eigene Klassen/Kurse; Verwaltung:
- Funktion `check_direct` (`schulmanager/messaging.py:608`) – Darf `sender` dieser Person schreiben? Gibt das Konto zurück, sonst ``.
- Funktion `can_block` (`schulmanager/messaging.py:623`) – Blockieren ist nur für Nicht-Personal möglich (Schulpersonal muss erreichbar bleiben → Melden).
- Funktion `students_conflict` (`schulmanager/messaging.py:628`) – True, wenn ein/e Schüler/in bei abgeschaltetem Schüler-Austausch andere Schüler/innen erreichen würde.
- Funktion `person_card` (`schulmanager/messaging.py:648`) – Darstellung einer Person für den Betrachter (datensparsam).
- Funktion `search_people` (`schulmanager/messaging.py:684`) – Personensuche fürs Adressbuch.
- Funktion `find_classes` (`schulmanager/messaging.py:734`) – Klassen, deren Name/Kennung zum Suchtext passt (für die Klassenansicht im Adressbuch).
- Funktion `class_roster` (`schulmanager/messaging.py:745`) – Klassenansicht im Adressbuch: Klassenleitung und Lehrkräfte für alle; Kinder mit ihren Eltern (inkl. Geschwister
- Funktion `suggestions` (`schulmanager/messaging.py:797`) – Vorschläge ohne Suchtext: Schüler/Eltern → Lehrkräfte der eigenen Klasse(n) und Verwaltung; Personal → keine.
- Funktion `reply_mode` (`schulmanager/messaging.py:818`) – Wie darf ein Teilnehmer antworten? `"all"` (in der Unterhaltung), `"private"` (eigene Unterhaltung mit dem

## Hängt ab von

- [[Modul models]] – `models`
- [[Server permissions]] – `permissions`

## Wird genutzt von

- [[Routen features_chats]]
- [[Routen features_messages]]
- [[Routen features_register]]

## Tests

`tests/test_messages.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
