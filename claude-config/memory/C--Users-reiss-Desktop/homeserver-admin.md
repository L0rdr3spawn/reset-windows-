---
name: homeserver-admin
description: "User wants all server stuff (Schulmanager instances incl. the clean one) on the home server, never on their PC; grants admin rights there; Minecraft server may be removed if needed"
metadata:
  node_type: memory
  type: feedback
  originSessionId: da397a22-9891-46f3-a3ae-94186b69fe15
  modified: 2026-10-12T17:19:51.288Z
---

All server deployments (Schulmanager main/demo/clean instance, license server) belong on the home server (`ssh server`), never on the user's own PC. The user said (2026-10-12) Claude gets admin rights on the home server when needed and may remove the Minecraft server running there if it is in the way.

**Why:** the PC is the user's workstation; the home server is the always-on host. A local test server during a check made them think things run on the PC.

**How to apply:** deploy/run long-lived services only on the server; local test servers only briefly and say so. Don't remove the Minecraft server unless resources actually require it — ask/announce first. Note: Claude Code auto mode classifier blocks "Production Deploy" commands to the server regardless; the user must add a Bash allow rule (e.g. `Bash(ssh server:*)`) or run the command. See [[schulmanager-deploy]].

2026-10-16: User allowed starting *temporary* local test servers on the PC for testing (stop them afterwards); long-running services stay on the home server. Before CPU-heavy runs (generator), say so briefly – the user noticed load and got worried.

2026-10-17: User freed disk on the home server. Disk was 161 GB used, of which 124 GB were seven daily Crafty backups (17.7 GB each, nightly 22:00). Only the verified latest backup (2026-10-16_22-00-21.zip) was kept, 55 GB used afterwards. crafty-container and mc-upgrader are stopped (Crafty restart policy changed from always to unless-stopped). Nobody had been online on either server since about 24.-25.09. mc-alaska is the user's current modpack project from another session: never delete it. Stopped Crafty means no more nightly backups; starting it again refills the disk (retention 7). Not deleted, offered: Crafty live server dir (17.7 GB, contained in the backup), mc-upgrader data (0.2 GB) + archive ~/archive/2026-09. The cron mc-net-refresh.sh (router port forwards) is untouched.
