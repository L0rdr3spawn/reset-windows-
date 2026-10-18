---
name: roblox-radar
description: roblox-radar/ – externe Live-Karte + Overlay fürs eigene Roblox-Spiel per HttpService; Cheat-Funktionen abgelehnt
metadata:
  node_type: memory
  type: project
  originSessionId: e6f53e6f-4a46-4293-9a97-e9a1bae338fb
  modified: 2026-10-02T16:11:23.436Z
---

`roblox-radar/` (angelegt 2026-10-02): `RadarSender.server.luau` (ServerScriptService) postet Spielerpositionen alle 0,25 s an `server.py` (Port 8790). Anzeige entweder `radar.html` im Browser oder `overlay.py` (tkinter-Overlay: Home = Menü, Größe/Reichweite/Deckkraft, Team-/Tot-Filter, Distanz, frei belegbare Tasten mit Umschalten/Halten). `python server.py --demo` läuft ohne Roblox; Launch-Config `roblox-radar-demo` in `.claude/launch.json`.

Server + Browser-Karte sind im Demo-Modus getestet. `overlay.py` und das Luau-Skript sind ungetestet – der Testlauf des Overlays wurde vom Auto-Mode-Classifier abgelehnt („Security Weaken"), nicht umgehen.

**Why:** User wollte ein externes ESP, später auch Aimbot, Skeleton-ESP und Verstecken vor Bildschirmaufnahme. Abgelehnt: alles, was Prozessspeicher liest, automatisch zielt oder das Tool vor Aufnahmen verbirgt. Dieser Weg läuft nur in Spielen mit dem eigenen Server-Skript.

**How to apply:** Erweiterungen nur als Anzeige von Daten, die das eigene Server-Skript liefert. Kein Aimbot, kein Capture-Schutz, kein Speicherzugriff – auch nicht „fürs eigene Spiel". 127.0.0.1 geht nur im Studio-Playtest; Live-Server brauchen öffentliche Adresse + `--token`.
