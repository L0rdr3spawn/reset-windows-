---
name: mc-settings-sync
description: "Minecraft-Einstellungen (Tasten, Sensitivity, FOV, Lautstärke) laufen über eine Master-Datei, Prism spielt sie vor jedem Start ein"
metadata:
  node_type: memory
  type: project
  originSessionId: 9cce4e1b-6581-4bb7-af9c-79e09eed34ce
  modified: 2026-09-25T17:18:35.954Z
---

Seit 2026-09-25: `C:\Users\reiss\Documents\claude\mc-settings\settings.txt` ist der Master für Tastenbelegung, mouseSensitivity, fov, soundCategory_*, gamma, guiScale, renderDistance u. a. `sync-options.ps1 apply|save` spielt ihn ein bzw. sichert zurück (liest `$env:INST_MC_DIR`, schreibt UTF-8 ohne BOM, setzt `onboardAccessibility:false`).

In den Prism-Instanzen 26.3, 26.2, 26.2(1), Upgrader 1.21.11, Gambling addiction, ATM10 stehen `PreLaunchCommand` (apply) und `PostExitCommand` (save) mit `OverrideCommands=true`; Backups als `instance.cfg.vor-settings-sync`. Ausgenommen: Jev-Bot (Bot-Client, Ton aus) und RLCraft (1.12, anderes Tastenformat).

**Why:** Der User will, dass beim Starten von Minecraft immer seine Einstellungen geladen sind.
**How to apply:** Neue Instanzen bekommen die zwei Befehle ebenso (install-prism-hooks.ps1 anpassen, nur bei geschlossenem Prism schreiben, sonst überschreibt Prism instance.cfg). Siehe [[mc-testen-singleplayer]].
