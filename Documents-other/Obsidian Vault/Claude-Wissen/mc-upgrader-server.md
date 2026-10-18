---
name: mc-upgrader-server
description: "Zweiter MC-Server Fabric 1.21.11 mit Upgrader-Gambling-Mod (Docker, Port 25620/extern 10478) + passendes Client-Modpack"
metadata:
  type: project
---
Angelegt 2026-09-22. Upgrader (EXEchelNZ, Modrinth `upgrade-items`, ARR-Lizenz) gibt es nur bis 1.21.11, deshalb eigener Server neben dem 26.2-Crafty-Server ([[minecraft-server-crafty]]).

- **Name „GOLD GOLD GOLD“** (MOTD), Welt am 2026-09-22 abends zurueckgesetzt; alte Welt unter `/home/luis/mc-upgrader/data-alt-*`.
- **Server**: Docker-Container `mc-upgrader` (itzg/minecraft-server:java21), Compose unter `/home/luis/mc-upgrader/`, Welt in `./data`. 6 GB RAM, Mods über `MODRINTH_PROJECTS` (fabric-api, upgrade-items, lithium, ferrite-core, krypton). OP: L0rdr3spawn. Kein Whitelist.
- **Port**: Host **10478** = externer Port (seit 2026-09-22 abends). Eine Adresse fuer alle: `l0rdr3spawn.duckdns.org:10478`, LAN `192.168.178.185:10478`. **Warum gleicher Port innen wie aussen:** DuckDNS liefert A+AAAA; IPv6-Clients verbinden sich auf denselben Port, Pinholes setzen KEINE Ports um. Mit Host-Port 25620 war der Server fuer IPv6-Nutzer auf :10478 tot, obwohl IPv4 lief. Freigaben stehen in `/home/luis/mc-pinholes.py` (Backup `.vor-upgrader`) und werden per Cron erneuert.
- **Client**: Prism-Instanz „Upgrader 1.21.11“ (26 Mods: Sodium/Iris/Lithium, Xaero-Karten, JEI, Jade, AppleSkin, Zoomify, Baritone 1.17.0 = die 1.21.11-Version, von GitHub cabaletta/baritone), Build-Skript-Ergebnis + `Documents\claude\upgrader-modpack\Upgrader-1.21.11.mrpack` für Freunde.

- **Sodium-Falle**: Iris 1.10.7 (letzte für 1.21.11) wird von Sodium ≥0.8.13 per `breaks` ausgeschlossen. Festgenagelt: Sodium 0.8.12 + Reese's 2.2.3 + Sodium Extra 0.9.1. Die angezeigten Update-Hinweise NICHT annehmen. Prism erkennt neue Instanzordner erst nach Neustart von Prism.
- **Datapack `world/datapacks/upgrader_start`**: jeder bekommt beim ersten Join und nach jedem Respawn ein `upgrader:upgrader` mit Fluch des Verschwindens (verschwindet beim Tod). Erkennung per Tag `up_starter` + deathCount-Score `up_deaths`, `@e[type=player]` = nur lebende Spieler. Befehle an den Server: `docker exec mc-upgrader rcon-cli <befehl>`.

**Why:** Upgrader muss auf Server UND Client laufen. mcsrvstat.us prüft nur IPv4, IPv6-Ports melden dort immer „offline“, auch beim Hauptserver.
**How to apply:** Neustart: `cd /home/luis/mc-upgrader && docker compose restart`. Mods ergänzen: MODRINTH_PROJECTS erweitern + `docker compose up -d`.
