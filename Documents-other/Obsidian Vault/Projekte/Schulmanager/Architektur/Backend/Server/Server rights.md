---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/rights.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server rights

> Server-Kern · 1 Datei(en) · 182 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Rollen & Rechte pro Schule in der Datenbank: Abweichungen vom Standard (`role_overrides`), Schulzweige (`branches`, `user_branches`), Zuordnung Eltern/Begleitung → Kinder (`parent_links`). `describe()` liefert alles für die Seite [[Seite RightsPage]]; `effective_matrix()` wird bei jeder Anfrage von [[Server deps]] gelesen, Änderungen wirken sofort.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/rights.py` | 182 | Rollen & Rechte pro Schule: Abweichungen vom Standard laden/speichern, wirksame Matrix, Zweige. |

## Wichtige Funktionen und Klassen

- Funktion `load_overrides` (`schulmanager/server/rights.py:19`)
- Funktion `apply_changes` (`schulmanager/server/rights.py:25`) – Speichert Änderungen `{recht: {"granted": bool, "scope": str|None}}` oder `{recht: None}` (zurück auf
- Funktion `reset_role` (`schulmanager/server/rights.py:68`) – Alle Abweichungen der Rolle löschen (zurück auf Standard). Rückgabe: Anzahl gelöschter Einträge.
- Funktion `effective_matrix` (`schulmanager/server/rights.py:75`) – Rolle → (wirksame Rechte, Umfänge) für die Erwachsenen-Variante (ohne Konto-Flag `adult`).
- Funktion `describe` (`schulmanager/server/rights.py:84`) – Alles, was die Seite „Rollen & Rechte“ braucht (`GET /api/v1/rights`).
- Funktion `branch_dict` (`schulmanager/server/rights.py:134`)
- Funktion `user_branches` (`schulmanager/server/rights.py:139`)
- Funktion `set_user_branches` (`schulmanager/server/rights.py:145`)
- Funktion `user_children` (`schulmanager/server/rights.py:155`) – Verknüpfte Kinder (Eltern, Schulbegleitung) in Anlagereihenfolge.
- Funktion `set_user_children` (`schulmanager/server/rights.py:161`)
- Funktion `role_titles` (`schulmanager/server/rights.py:170`) – Anzeigetitel einer Person, z. B. `["Lehrkraft", "Klassenleitung 5a"]` (Klassenleitung aus den Stammdaten).

## Datenbank-Tabellen

- **Nutzt:** `branches`, `role_overrides`, `user_branches` → [[Datenmodell#Rollen und Rechte]]
- **Nutzt:** `parent_links`, `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server db]] – `db`, `db_models`
- [[Server permissions]] – `permissions`

## Wird genutzt von

- [[Routen rights]]
- [[Routen system]]
- [[Server deps]]

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
