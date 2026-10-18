---
name: mc-server-immer-ueber-crafty
description: "Neue Minecraft-Server auf dem Heimserver immer in Crafty anlegen, nicht als eigenen Docker-Container"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9535a912-837e-4545-bb2f-1e1712071bf4
  modified: 2026-09-22T11:33:59.109Z
---

Alle Minecraft-Server auf dem Heimserver sollen über Crafty laufen (Crafty 4.10.4, Container `crafty-container`), nicht als eigene Docker-Container wie itzg/minecraft-server.

**Why:** Der User will alle Server an einer Stelle verwalten (Start/Stop, RAM, Backups, Konsole). Am 2026-09-22 wunderte er sich, warum Crafty 37 % RAM zeigt, der Server aber nur 2,8 GB braucht. Der Grund war der separate `mc-upgrader`-Container mit 6,5 GB, den Crafty nicht sieht.

**How to apply:** Neue Server in Crafty anlegen (Create New Server oder Import aus `/DATA/AppData/crafty/import`). Crafty bringt Java 8/11/17/21/25 mit (`/usr/lib/jvm/java-XX-openjdk-amd64`) und hat die Ports 25500–25600 schon nach außen offen. Freie Crafty-Ports für neue Server nutzen, Pinholes/Fritz!Box-Weiterleitung entsprechend anpassen. Siehe [[minecraft-server-crafty]], [[mc-upgrader-server]], [[home-server-debian-casaos]].

**Ausnahme 2026-09-22:** Fuer den Gambling-Server (GOLD GOLD GOLD, Fabric 1.21.11) hat der User bewusst wieder den Docker-Container gewaehlt, statt ihn in Crafty zu importieren. Crafty findet vorbereitete Serverordner NICHT von allein; es liest nur seine DB, ein Server muss ueber Create New Server > Import angemeldet werden. Direktes Schreiben in die Crafty-DB (inkl. Container-Stopp) wird vom Auto-Mode-Klassifizierer blockiert. Vorbereiteter Ordner liegt noch unter `/DATA/AppData/crafty/import/gold`.
