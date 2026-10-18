---
name: wallpaper-engine-autostart
description: Wallpaper-Engine-Wächter wallpaper-autostart.ps1 – seit 2026-09-29 DEAKTIVIERT (kein Autostart mehr)
metadata:
  node_type: memory
  type: project
  originSessionId: 1c06255f-7a19-4ccc-8b18-64a1dc95a304
  modified: 2026-09-29T19:52:51.317Z
---

**Stand 2026-09-29: auf Wunsch des Users deaktiviert.** Der Run-Key `WallpaperEngine` ist entfernt und der Wächter beendet. Auch in der config.json von WE ist Autostart aus. Das Skript existiert noch. Nur wieder aktivieren, wenn der User danach fragt.

`C:\Users\reiss\Documents\claude\wallpaper-autostart.ps1` wurde über Run-Key `WallpaperEngine` gestartet (`conhost --headless powershell ...`). Das Skript prüft alle 15 s und startet WE, wenn Steam mit AccountID 3395664 (main, Besitzer von WE, siehe [[steam-mydayz-tool]]) eingeloggt ist. Nach 3 Sofort-Abstürzen pausiert es 5 min. Log liegt unter `%LOCALAPPDATA%\wallpaper-autostart.log`.

**Why:** Der alte Run-Eintrag hat wallpaper64.exe direkt gestartet, oft bevor Steam eingeloggt war, und WE lief dann nicht. Auf den Accounts cs2/smurf fehlt die Lizenz. Diese Prüfung wird nicht umgangen, der legale Weg dafür ist Steam Family.
**How to apply:** WE nicht von selbst wieder in den Autostart eintragen.
