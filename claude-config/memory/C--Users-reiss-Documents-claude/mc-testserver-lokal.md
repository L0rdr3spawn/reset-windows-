---
name: mc-testserver-lokal
description: "Lokaler Paper-26.2-Testserver auf dem PC (127.0.0.1:25566, offline-mode) für den Jev-Bot, getrennt von der echten Welt"
metadata: 
  node_type: memory
  type: project
  originSessionId: 741a9993-f7c8-47e3-bed7-1b83afe0566c
  modified: 2026-09-19T18:26:34.895Z
---

Angelegt 2026-09-19 unter `C:\Users\reiss\Documents\claude\mc-testserver\`: Paper 26.2 + ViaVersion/ViaBackwards + WorldEdit, kopiert vom Heimserver ([[minecraft-server-crafty]]), läuft mit Prisms JDK (`start.cmd`). `server-ip=127.0.0.1`, Port 25566, `online-mode=false`, User hat EULA-Annahme ausdrücklich erlaubt. `L0rdr3spawn` ist OP über die Offline-UUID in `ops.json`.

Bot dort: `mc-bot\start-test.cmd` → `node bot.js config-test.json` (`auth: offline`, Name `notL0rdr3spawn`, eigene `ort-config-test.json`). Siehe [[mc-begleitbot-mineflayer]].

**Why:** Der selbstständig abbauende Bot soll nicht die echte Welt umgraben; offline-mode spart den Microsoft-Login des Zweitaccounts (in `config.json` war noch keine Bot-Email eingetragen).
**How to apply:** Client direkt verbinden: `prismlauncher.exe --launch 26.2 --server 127.0.0.1:25566` (Prism unter `%LOCALAPPDATA%\Programs\PrismLauncher`). Bot auf den echten Server braucht weiterhin Email + Device-Code-Login + `grim.exempt`.
