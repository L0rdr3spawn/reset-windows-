---
name: msix-registry-virtualization
description: "Claude desktop app is MSIX: HKCU registry AND %APPDATA%/%LOCALAPPDATA% writes from its process tree land in a private copy; never launch GUI apps from Claude"
metadata:
  node_type: memory
  type: project
  originSessionId: 25f2b5e3-d233-4ec7-a7db-969ea53b3aee
  modified: 2026-10-06T13:59:49.383Z
---

The Claude desktop app on this machine runs as an MSIX package (`Claude_pzs8sxrjxfjjc`). From its process tree (incl. apps I launch):
- HKCU registry writes go to the package's private hive; real Windows never sees them.
- Writes under `%APPDATA%` / `%LOCALAPPDATA%` go to `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\{Roaming,Local}\...`. Reads inside Claude show a merged view, so it LOOKS fine from inside.
- Not affected: other paths in the user profile (Desktop, `~\.cache`, `~\.config`, `~\.local`), Windows Credential Manager.

**Why:** 2026-10-04 Jeff's Run key looked enabled but wasn't. 2026-10-06 found that Handy had been set up from inside Claude: its settings, 1.6 GB turbo model and autostart lived only in the private copy → after reboot Handy didn't autostart and "everything was reset".

**How to apply:** Never launch GUI apps (Handy, Jeff, installers) from Claude directly. Workaround that works (verified 2026-10-16): run the program or script through a one-off Task Scheduler task — `Register-ScheduledTask` with `New-ScheduledTaskPrincipal -LogonType Interactive`, `Start-ScheduledTask`, wait, `Unregister-ScheduledTask`. The Task Scheduler service launches it outside Claude's process tree, so registry and AppData writes land in the real locations (used for Seelen UI, Handy and `handy-reparieren.ps1`). Registry/autostart changes: user runs the command outside Claude, or the app's own UI toggles it. Inspect the REAL state read-only via WMI (StdRegProv for registry, CIM_DataFile/CIM_Directory) or the loopback share `\\127.0.0.1\C$\Users\reiss\AppData\...` (bypasses the redirection). Related: [[jeff-voice-assistant]]
