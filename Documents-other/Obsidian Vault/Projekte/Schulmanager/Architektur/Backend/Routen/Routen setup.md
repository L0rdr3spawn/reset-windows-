---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/setup.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen setup

> API-Routen · 1 Datei(en) · 41 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Einrichtungs-Assistent einer neuen Schule: `GET /setup/status` liefert den Stand je Schritt (Lizenz, Schuldaten, Stammdaten, Stundenplan, Konten) – die Schritte selbst nutzen die vorhandenen Seiten/Importe.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/setup.py` | 41 | Einrichtungs-Assistent einer neuen Schule: `GET /setup/status` liefert den Stand je Schritt (Lizenz… |

## Endpunkte (1)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/setup/status` | `setup_status` (`setup.py:17`) | settings.edit | [[Frontend Komponenten]], [[Seite SetupPage]] |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Datenbank-Tabellen

- **Nutzt:** `users` → [[Datenmodell#Konten und Anmeldung]]

## Hängt ab von

- [[Server db]] – `db`, `db_models`
- [[Server deps]] – `deps`
- [[Server licensing]] – `licensing` *(nur zur Laufzeit importiert)*
- [[Server store]] – `store` *(nur zur Laufzeit importiert)*

## Wird genutzt von

- –

## Tests

`tests/test_setup.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->
