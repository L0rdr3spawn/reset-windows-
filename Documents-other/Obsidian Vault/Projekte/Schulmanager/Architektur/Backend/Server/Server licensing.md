---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/licensing.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Server licensing

> Server-Kern · 1 Datei(en) · 334 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Lizenz der Schule: Lizenzdatei mit Ed25519-Signatur des Anbieters (`SM_LICENSE_PUBKEY`), Zustände `valid`, `grace`, `readonly`, `missing`, `invalid`. Eine Hintergrundschleife bestätigt die Lizenz regelmäßig beim [[Lizenzserver]] (`check_now`). Bei Durchsetzung (`SM_LICENSE_ENFORCE`, in Produktion an) sperrt `_guard_license` in [[Server deps]] alle ändernden Anfragen (Nur-Lesen), nie das Lesen. `user_limit` begrenzt aktive Konten. Ablauf: siehe [[Abläufe]].

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/licensing.py` | 334 | Lizenz der Schule: vom Anbieter signiert (Ed25519), regelmäßig beim Lizenzserver des Anbieters best… |

## Wichtige Funktionen und Klassen

- Funktion `canonical` (`schulmanager/server/licensing.py:43`)
- Funktion `verify` (`schulmanager/server/licensing.py:59`)
- Funktion `license_path` (`schulmanager/server/licensing.py:72`)
- Funktion `state_path` (`schulmanager/server/licensing.py:76`)
- Funktion `load_state` (`schulmanager/server/licensing.py:95`)
- Funktion `parse_license` (`schulmanager/server/licensing.py:106`) – Prüft einen Lizenztext. Gibt `(lizenz, "")` oder `(None, Fehlermeldung)` zurück.
- Funktion `load_license` (`schulmanager/server/licensing.py:125`)
- Funktion `install` (`schulmanager/server/licensing.py:133`) – Neue Lizenz speichern (nach Prüfung) und sofort online bestätigen.
- Funktion `status` (`schulmanager/server/licensing.py:175`) – Aktueller Lizenzstand. `read_only`: Änderungen gesperrt (nur wenn `SM_LICENSE_ENFORCE`).
- Funktion `has_feature` (`schulmanager/server/licensing.py:236`) – Lizenz-Merkmal (z. B. `demo`). Ohne Durchsetzung immer erlaubt.
- Funktion `user_limit` (`schulmanager/server/licensing.py:244`) – Höchstzahl aktiver Konten (nur mit Durchsetzung): Testbetrieb bzw. `max_users` der Lizenz.
- Funktion `check_now` (`schulmanager/server/licensing.py:264`) – Lizenz jetzt beim Lizenzserver bestätigen lassen; speichert das Ergebnis und gibt den neuen Stand zurück.
- Funktion `start` (`schulmanager/server/licensing.py:320`) – Hintergrund-Prüfung starten (`runtime.startup`).
- Funktion `stop` (`schulmanager/server/licensing.py:331`)

## Datenbank-Tabellen

- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server config]] – `config`
- [[Server db]] – `db`, `db_models` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- [[Routen auth]]
- [[Routen license]]
- [[Routen setup]]
- [[Routen users]]
- [[Server deps]]

## Tests

`tests/test_license.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
