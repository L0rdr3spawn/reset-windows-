---
name: mc-testen-singleplayer
description: "Mods/Features in Minecraft testen = Prism im Singleplayer starten, NICHT den lokalen Testserver hochfahren"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9cce4e1b-6581-4bb7-af9c-79e09eed34ce
  modified: 2026-09-25T16:45:17.490Z
---

Wenn der User sagt „starte Minecraft/Prism, damit ich teste", nur Prism starten (Instanz passend zur Mod-Version, Hauptaccount `--profile L0rdr3spawn`) und im **Singleplayer** testen lassen. Den lokalen Paper-Testserver ([[mc-testserver-lokal]]) nicht von selbst starten.

**Why:** 2026-09-25 hat der User das ausdrücklich verlangt, nachdem ich den Testserver gestartet hatte. Der ist Paper 26.2, die Mods sind 26.3 („falsche Version"), und der User testet lieber in Singleplayer.

**How to apply:** `prismlauncher.exe --launch 26.3 --profile L0rdr3spawn` ohne `--server`. Test-Kit liegt als Datapack `modtest` in `saves/New World/datapacks` der Instanz „26.3" (Pack-Format 121). Siehe [[eigene-fabric-mods]].
