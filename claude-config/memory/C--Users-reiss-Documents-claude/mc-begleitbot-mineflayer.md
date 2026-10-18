---
name: mc-begleitbot-mineflayer
description: "Mineflayer-Begleitbot (folgt, kämpft, lootet) für den eigenen MC-Server — warum er über Protokoll 26.1 läuft und was er vom Server braucht"
metadata: 
  node_type: memory
  type: project
  originSessionId: 64d37166-1cdd-47bb-a710-2767657ae1ba
  modified: 2026-09-19T18:20:20.355Z
---

Begleitbot für den Zweitaccount auf dem eigenen Server ([[minecraft-server-crafty]]), gebaut 2026-09-13. Code: `C:\Users\reiss\Documents\claude\mc-bot\` (bot.js, config.json, start.cmd).

Kann: folgen (Abstand 3), feindliche Mobs im Umkreis 12 angreifen, Angreifer des Besitzers kontern, beste Waffe anlegen, Drops im Umkreis 16 sammeln, ab Hunger 16 essen, ab Leben 6 Kampf abbrechen, Reconnect nach 15 s. Chat-/Flüsterbefehle: `!folge !stop !kampf !loot !gib !status`. Seit 2026-09-19 zusätzlich Baritone-artig (echtes Baritone gibt es nicht für 26.x): `aufgaben.js` (Rohstoffe abbauen via mineflayer-collectblock, einlagern, heimgehen; Heim/Truhe in `ort.json` via `!heim`), `jev.js` (Befehle verstehen + Modus `!selbst`, in dem Jev aus code-erzeugten Optionen die nächste Aufgabe wählt). Außerdem versteht er zusätzlich freie Sprache über Jev ([[typesafe-skill]], `@typesafe-ai/sdk`): noul „an den Bot gerichtet?“ + choice der Aktion, nur aktiv wenn `TYPESAFE_API_KEY` gesetzt; Schwelle offener Chat per `jevSchwelle` in config.json (Default 0.5 — Test 2026-09-19: echte Befehle im offenen Chat 0.71–0.80, Smalltalk 0.10–0.13; Antwortzeit ~250–800 ms).

**Why:** Mineflayer bzw. minecraft-data unterstützt nur bis **26.1**, der Server läuft **26.2** — direkt verbinden geht nicht. Deshalb `version: "26.1"` in der Config plus ViaBackwards auf dem Server als Übersetzer. Zweitens flaggt GrimAC die Mineflayer-Bewegung sonst als Simulation-Violation.

**How to apply:** Bei MC-Updates prüfen, ob `minecraft-data` inzwischen die Serverversion kennt (`Object.keys(require('minecraft-data/minecraft-data/data/dataPaths.json').pc)`) — dann kann `version` hochgezogen und ViaBackwards ggf. entfernt werden. Der Bot-Account braucht `/lp user <BotName> permission set grim.exempt true`. Login läuft über Microsoft-Device-Code (Token-Cache in `mc-bot/.auth/`), macht der Nutzer selbst.
