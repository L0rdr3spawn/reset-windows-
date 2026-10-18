---
name: cs2-jev-coach
description: "CS2 + Jev unter cs2-jev/ – GSI-Coach fertig; neues Ziel: Jev steuert einen Spieler per Konsole (netcon), blockiert an Workshop Tools"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8f975005-7724-44ab-86b5-841931cb2dc1
  modified: 2026-09-19T20:01:02.280Z
---

cs2-jev/coach.py (Python-Standardbibliothek): CS2 GSI → 127.0.0.1:3000, bei Freezetime Jev-Anfrage (Team-Kauf, Loadout, Plan). API-Key in cs2-jev/.env. GSI-cfg liegt in `Steam/steamapps/common/Counter-Strike Global Offensive/game/csgo/cfg/` (Token jev-coach-7f3a). cs2-jev/netcon.py = Client für die CS2-Konsole über TCP.

**Neues Ziel (Stand 2026-09-19):** Jev soll selbst einen Spieler steuern, damit der User eigene Bots bauen kann. Nur auf dem eigenen Offline-Spiel mit sv_cheats 1, auf dem normalen CS2-Client ohne eigenen Server (Server-Plugin-Variante abgelehnt). Geplant: Steuerung über die Konsole mit `+forward`, `setang`, `+attack`, `buy`.
**Blocker:** `-netconport` öffnet unter Windows keinen Port, wenn CS2 ohne Workshop Tools läuft (Valve-Issue csgo-osx-linux#3603). Die Tools sind nicht installiert (appmanifest_730: DisabledDLC 2279721). Ich habe `steam://install/2279720` geöffnet, der User hat aber noch nicht bestätigt. Morgen: prüfen, ob installiert; dann CS2 mit `-tools -netconport 2121` starten und testen, welche Befehle es für Positionen der Gegner (ent_*/getpos) und Bot-Steuerung gibt.

**Why:** Einen Speicher-Cheat bzw. Aimbot per Bildschirm habe ich abgelehnt, weil er online genauso funktionieren würde und VAC-Risiko hat. Befehle, die sv_cheats brauchen, gehen nur offline, deshalb passt dieser Weg.
**How to apply:** Feste Regeln bleiben im Code, Jev liefert nur die Entscheidungen. TypeSafe-Skill nutzen [[typesafe-skill]]. Ähnliches Muster wie [[jevbaritone-bot]].
