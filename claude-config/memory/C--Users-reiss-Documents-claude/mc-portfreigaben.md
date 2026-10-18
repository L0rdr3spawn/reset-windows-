---
name: mc-portfreigaben
description: "Welche Fritz!Box-Ports für den Heimserver belegt/reserviert sind – Reserve-1..5 sind schon offen, NICHT neu einrichten"
metadata:
  node_type: memory
  type: project
  originSessionId: 2fc3c956-3611-4463-89ce-57aa687dd2aa
  modified: 2026-09-23T17:05:00.810Z
---

Stand 2026-09-23. Definiert in `PORTS` in `~/scripts/mc-pinholes.py` auf dem Server (Cron erneuert alle 10 min per UPnP IPv4-Weiterleitung + IPv6-Pinhole). Tabelle auch in `~/README.md` dort.

| Extern IPv4 | Intern/IPv6 | Proto | Status |
|---|---|---|---|
| 10476 | 25565 | TCP | Haupt-Server Java (Crafty) |
| 10477 | 19132 | UDP | Haupt-Server Bedrock (Geyser) |
| 10478 | 10478 | TCP | mc-upgrader (Docker) |
| 10479–10483 | 25501–25505 | TCP | **Reserve-1..5 FREI, schon offen** (Java) |
| 10484–10488 | 25501–25505 | UDP | **Reserve-1..5 FREI, schon offen** (Bedrock) |
| 10489–10495 | – | – | ungenutzt, nicht freigegeben |

Reserve-N = intern 2550N, extern TCP 10478+N / UDP 10483+N.

**Why:** Der User wollte Ports für künftige Server vorab einrichten lassen, damit das nicht jedes Mal neu passieren muss.
**How to apply:** Neuer Server → in Crafty `server-port=2550N` (+ Geyser `port: 2550N`), in `PORTS` und README "Reserve-N" umbenennen. Fritz!Box: gleicher externer Port für TCP und UDP geht nicht (UPnP-Fehler 718), daher getrennte externe Ports. Audit 2026-09-23: Router gibt nur diese Ports frei, online-mode an, RCON/Query nicht nach außen, bungeecord/velocity aus; Haupt-Server hat aber KEINE Whitelist und Grim ist deaktiviert. Siehe [[home-server-debian-casaos]], [[minecraft-server-crafty]].
