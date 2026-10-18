---
name: home-server-debian-casaos
description: "Heimserver \"server\" (Debian 12 + CasaOS) – Zugang `ssh server`, Ordnerstruktur, README auf dem Server, BIOS-Hänger wegen CMOS-Batterie"
metadata:
  node_type: memory
  type: project
  originSessionId: 2fc3c956-3611-4463-89ce-57aa687dd2aa
  modified: 2026-09-23T17:04:54.149Z
---

Heimserver des Users im LAN 192.168.178.0/24 (Fritz!Box):
- **Zugang direkt ohne User: `ssh server`** (Alias in `C:\Users\reiss\.ssh\config` → luis@192.168.178.185, Key `id_ed25519`, seit 2026-09-23). Überblick: `ssh server scripts/status.sh`. **Zuerst `ssh server cat README.md` lesen** – dort stehen Ordner, Container, Port-Tabelle, Regeln.
- Name `server.fritz.box`, IP per DHCP .185, NIC `enp2s0`, MAC A8-A1-59-54-74-F6, IPv6 link-local fe80::aaa1:59ff:fe54:74f6
- Debian 12.15 (Kernel 6.1.0-53, Updates Stand 2026-09-23 alle drin), CasaOS auf Port 80, Docker, rclone, Samba
- User `luis`: Gruppe docker (Docker ohne sudo), sudo NUR mit Passwort (kennt nur der User) → keine apt/systemctl/journal-Aktionen möglich
- Home aufgeräumt 2026-09-23: `~/scripts/` (status.sh, mc-net-refresh.sh, mc-pinholes.py), `~/logs/`, `~/archive/2026-09/` (alte Skriptversionen, Crafty-DB-Backups, alte Upgrader-Welt), `~/mc-upgrader/`. Cron alle 10 min: `~/scripts/mc-net-refresh.sh`.
- Offene Punkte (vom Auto-Mode blockiert, User muss selbst): Container `duckdns` ist mit Platzhaltern konfiguriert und nutzlos → stoppen; `nginx-ssl` seit Monaten tot → entfernen.
- Hardware: ASRock H410M-HDV, i5-10400F = KEINE iGPU, keine Grafikkarte → Monitor immer schwarz.

**Why:** 2026-09-11 und 2026-09-19 war der Server weg: CMOS-Batterie leer, Board bleibt beim Start im BIOS-Hinweis (F1/F2) stehen, ohne GPU unsichtbar.
**How to apply:** Bei "Server nicht erreichbar" zuerst an BIOS-Halt denken: blind F2 bzw. F1→F10→Enter, dauerhaft CR2032 tauschen + im BIOS "Restore on AC Power Loss = Power On". Erreichbarkeit per IPv6 link-local oder ARP auf MAC prüfen. Ports siehe [[mc-portfreigaben]], MC siehe [[mc-server-immer-ueber-crafty]].
