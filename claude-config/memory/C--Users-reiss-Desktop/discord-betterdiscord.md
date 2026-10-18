---
name: discord-betterdiscord
description: "Discord + BetterDiscord fully set up 2026-10-17: ClaudeBridge file-queue plugin (read + confirmed send), skill discord-lesen, reinject task w/ iGPU pref, 6 QoL plugins; pitfalls"
metadata:
  node_type: memory
  type: project
  originSessionId: 18324827-e63e-4ab6-b7c2-377d777cc006
  modified: 2026-10-17T18:46:05.376Z
---

Discord lives in real `%LOCALAPPDATA%\Discord\app-1.0.9262` (not MSIX; write via loopback share `\\127.0.0.1\C$\Users\reiss\AppData\...` to bypass Claude's virtualization, see [[msix-registry-virtualization]]). Start Discord only via one-off scheduled task (`Update.exe --processStart Discord.exe`).

State (user approved all of it 2026-10-17): BetterDiscord v1.14.3 injected (index.js patched, `.orig` backup). Task `BetterDiscord-Reinject` runs `~/.local/bin/bd-reinject.ps1` at logon: re-patches new app-* folders every 30 s + sets Discord GPU preference to iGPU (GpuPreference=1) in the real registry. Plugin `ClaudeBridge` (source `Documents\claude\discord\ClaudeBridge.plugin.js`, copy in `%APPDATA%\BetterDiscord\plugins`) + CLI `~/.local/bin/discord-bridge.py` + skill `discord-lesen`: guilds, channels, dms, unread, messages, files, search, download(confirm), send(confirm). BD 1.14 plugin sandbox has NO `http`/`os` and no `fs.appendFileSync` (use writeFileSync flag "a"), so the bridge is a file queue in `~/.config/discord-bridge/{req,res}`, audit log `access.log`. BD disables a plugin that throws on load -> re-enable in `data\stable\plugins.json` with Discord closed. Third-party QoL plugins installed (scanned): DoNotTrack, ReadAllNotificationsButton, ImageUtilities, PinDMs, BetterVolume, ChannelTabs. custom.css = no transitions/backdrop blur.

**Send rule:** user wants Claude able to write text, but ONLY after showing exact text + target and getting a yes for that one message (in skill). Plugin blocks @everyone/@here/role pings, 3 s gap, 8 msgs/10 min.

**Why this matters / mistake:** 2026-10-17 a "guard test" with a real channel id actually sent "hi @everyone" to a private DM because a Python-edited regex had `\b` turned into a backspace char. Never test send guards with a real channel: use a non-existent ID (guard order: ping check -> channel lookup). When patching JS via Python heredocs, avoid `\b`/`\d` in normal strings (use Edit tool or raw strings).

Perf: baseline 1.2 GB RAM / 4.3% CPU; after CSS+DoNotTrack etc. ~0.95-1.3 GB / ~3.9%. Discord is inherently heavy; further saving is only the in-app Reduced Motion / GIF-autoplay toggles.
