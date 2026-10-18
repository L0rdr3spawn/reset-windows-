---
name: mc-arctic-forgelabs
description: "Forge Labs '100 Days Arctic' (CurseForge V.2, MC 1.12.2 Forge 14.23.5.2859): server mc-arctic on home server :10480 + Prism instance 'Arctic 100 Days'; mods removed and why"
metadata:
  node_type: memory
  type: project
  originSessionId: 960d7ad1-3e12-4a5e-a11a-a5bb7709b51d
  modified: 2026-10-18T14:19:49.363Z
---

Set up 2026-10-18. Pack: CurseForge project 1416377 / file 7403596 (manifest + overrides, no saved world inside; the "world" = OTG preset **Far From Home 6**). Local work dir: `Documents\claude\mc-arctic` (pack, mods, srv, client).

- Server: home server `~/mc-arctic`, container `mc-arctic` (itzg java8, TYPE=FORGE 14.23.5.2859, 6 GB, host port **10480**, LEVEL_TYPE=OTG, GENERATOR_SETTINGS="Far From Home 6", OP L0rdr3spawn). Client-only mods left out of the server: DynamicLights, MouseTweaks, DynamicSurroundingsHuds, JEI.
- Client: Prism instance `Arctic 100 Days` (Java 8 jre-legacy, 6 GB), copied into the REAL instances folder via `\\127.0.0.1\C$\...` share (see [[msix-registry-virtualization]]).
- Changes vs. pack: OTG file 3093121 (v9.0) is 404 on CurseForge → used OTG 1.12.2-v9.4 and deleted the shipped stale OTG-Core.jar (OTG regenerates it). Removed **WildNature** (biome id overflow >255) and **Mo' Villages** (ClassCastException with OTGVillageGen) on server AND client.
- Related: [[mc-alaska-awr]], [[homeserver-admin]].

**2026-10-18 update:** The user found the 1.12.2 pack/world did NOT match the video (oFHcxf9L7wM, 2026, custom Arctic with Hot Iron/Butchery). No original map exists (Discord: random seed + pasted builds). Switched to the Discord fan pack by _ajsi "Surviving 100 Days in the Arctic (Inspired by Forge Labs)" (1.20.1 Forge 47.4.10, 76 mods, work dir `Documents\claude\mc-arctic\map`). Server: `~/mc-arctic2` container `mc-arctic2` :10481 (8 GB, random seed, ESAP loot datapack in world/datapacks, MaFgLib removed from server). Prism instance `Arctic 1.20.1` (Java 17, shaders Complementary Reimagined). 1.12.2 container `mc-arctic` is stopped (unless-stopped). Author's own map was never published; Discord access to the Forge Labs server is read-only via [[discord-betterdiscord]].
