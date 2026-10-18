---
name: mc-alaska-awr
description: "Minecraft-Modpack 'Alaskan Wilderness Reimagined' (AWR v3.8, Forge 1.20.1): Server-Container mc-alaska auf dem Heimserver (Port 10479) + Prism-Instanz 'AWR Alaska' mit Account L0rdr3spawn; wo Doku und Client-only-Liste liegen"
metadata:
  node_type: memory
  type: project
  originSessionId: be836e5e-aa0f-4929-a85f-94dd4318cfe8
  modified: 2026-10-17T14:33:54.992Z
---

Set up 2026-10-17 after the Forge Labs video "1 Jahr in Alaska in ultra-realistischem Minecraft" (youtube jccqEa0Qd40). The original Forge Labs pack is unreleased ("Mod-Infos: DEMNÄCHST"); installed the fan recreation **Alaskan Wilderness Reimagined [AWR] v3.8** (Modrinth `alaskan-wilderness-reimagined`, Forge 47.4.20, MC 1.20.1).

- Server: home server `~/mc-alaska/docker-compose.yml`, container `mc-alaska` (itzg/minecraft-server:java17, TYPE=FORGE, 8 GB, host port **10479**, OP L0rdr3spawn). LAN address `192.168.178.185:10479`. Not port-forwarded on the router.
- Server mods = client mods minus client-only ones. WaterMedia crashes servers (remove). Cool Rain, WaterVision, Particular Reforged must stay on the server (MATCH_VERSION), although they look client-only.
- Client: Prism instance `AWR Alaska` (folder `minecraft/`, Java 17 = java-runtime-gamma, 8 GB). Main account = **L0rdr3spawn** (NotL0rdr3spawn is the alt). Start: `Documents\claude\mc-alaska\start-awr.ps1` via one-off scheduled task (see [[msix-registry-virtualization]]); README there.
- Other MC on the server: `mc-upgrader` (Fabric 1.21.11, port 10478) and Crafty (Paper) still running. See [[homeserver-admin]].
