---
name: cs2-ping-tools
description: cs2-ping/ – Ping-Scanner für Valve-Relays + Tweak-Skript mit Undo-Log; Messfallen und Befund zur Leitung
metadata:
  node_type: memory
  type: project
  originSessionId: 85c7d70b-6338-43fe-a3e9-7376923de35c
  modified: 2026-10-01T15:04:29.073Z
---

Unter `cs2-ping/` liegen zwei Skripte (Stand 2026-10-01):
- `ping-scan.ps1` – pingt alle Valve-SDR-Relays (Liste von der Steam-API), sortiert Standorte nach Median, CSVs in `scans/`. `-TotalPings 500000` dauert ca. 15 min.
- `cs2-ping.ps1 -Action apply|undo|status -Part cs2|adapter|all` – setzt CS2-Convars (maxping 25, rate 1000000) und optional Realtek-Adapterwerte, protokolliert alt/neu in `changes.jsonl`. Der Adapter-Teil braucht Admin und wurde dem User zum Selbststarten überlassen.

Befunde: Leitung sauber ca. 13 ms zu Frankfurt/Amsterdam. Ein Download auf dem PC mit ~47 Mbit/s (füllt die Leitung, vermutlich 50er-Anschluss) hebt jeden Ping um ~45 ms und bringt Paketverlust – das ist der eigentliche Ping-Killer, nicht die Einstellungen.

**Why:** Zwei Messfallen haben viel Zeit gekostet.
**How to apply:** .NET-`Ping` mit Timeout < 1 s liefert unter Windows sporadisch sofort `TimedOut` (Sekundentakt) – immer >= 3 s OS-Timeout und die Grenze selbst prüfen. Bei auffälligen Pings zuerst den Durchsatz des Adapters prüfen, bevor man dem Messwerkzeug misstraut.
