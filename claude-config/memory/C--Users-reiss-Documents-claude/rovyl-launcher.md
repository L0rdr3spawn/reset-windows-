---
name: rovyl-launcher
description: "Rovyl = Radial-App-Launcher (Alt+Y), Config-Pfad, Edit-Regeln und bekannte Launch-Bugs"
metadata:
  node_type: memory
  type: reference
  originSessionId: 956c6df0-29a4-4c62-8f66-43933922ec4e
  modified: 2026-10-04T10:38:04.124Z
---

Rovyl (Electron, github HenryCauan/rovyl) unter `%LOCALAPPDATA%\Programs\Rovyl`, Config `%APPDATA%\Rovyl\config-v2.json` (1,2 MB wegen base64-Icons, nur per Grep/Skript anfassen). Workspaces stehen doppelt drin: `workspaces` UND `config.workspaces` – beide ändern. Autostart über HKCU Run `com.henry.rovyl`.

- Vor dem Editieren `Stop-Process -Name Rovyl -Force` (beim normalen Beenden schreibt der Renderer die alte Config zurück), danach neu starten.
- Neue Einträge ohne `customIconUrl` anlegen – IconHealing zieht das Icon beim Start selbst.
- Bug: AppIDs mit Punkt ohne `!` (z. B. `SteelSeries.Gg.Main`) hält Rovyl für Dateipfade → startet nicht. Stattdessen echten exe-Pfad eintragen. Roblox über das Startmenü-.lnk (Versionsordner wechselt bei Updates).
- Workspace „Spotify“ (Taste 4): ruft `%LOCALAPPDATA%\Programs\RovylSpotify\spotify-<aktion>.exe` auf (eine C#-exe, Kopien je Aktion, Quelle in `src\`, Build mit .NET-Framework-csc). Play/Weiter/Zurück per WM_APPCOMMAND ans Spotify-Fenster, Lautstärke = nur Spotify-Audiositzung (alle Ausgabegeräte). Rovyl-Tasten-Simulation kennt keine Medientasten, daher die exe. Lucide-Icons (`iconSource: "lucide"`) werden nicht überschrieben.
- Rad bleibt offen bei Einträgen mit `"keepOpen": true`: eigener Patch in app.asar (Klick-Handler im Renderer-Bundle `dist/assets/index-*.js`), eingespielt mit `python %LOCALAPPDATA%\Programs\RovylSpotify\patch-rovyl.py` (idempotent, Original = app.asar.orig). Rovyl-Updates überschreiben den Patch → Skript erneut laufen lassen. Asar-Integrity-Fuse ist aus, daher geht das Patchen.
- Spotify-Panel (Titel, Cover, Fortschritt, Lautstärke-Slider) unter dem Rad: `panel.js` wird vom Patch ans Bundle gehängt, liest `window.__rovylRadial` (zweiter Patch im Layout-Effekt). Daten von `spotify-agent.exe` (TcpListener 127.0.0.1:8791, SMTC + Core Audio; Build braucht SDK-`UnionMetadata\10.0.26100.0\Windows.winmd`). Agent wird vom Panel per executeCommand gestartet und beendet sich ohne Rovyl. Patch baut immer aus app.asar.orig neu.
- Vor Live-Tests prüfen, ob der User spielt (2026-10-04 lief CS2 im Vordergrund) – dann keine Tasten senden und Rovyl nicht neu starten.
- Nicht blind per SendInput im Rad klicken: User arbeitet parallel am PC, Klicks landeten in seinem Fenster. Alt+Y per keybd_event braucht Scancodes (0x38/0x15).
- 2026-09-29 eingerichtet: GG/Steam/Roblox repariert, ExLoader (`C:\Program Files\ExLoader\ExLoader.exe`) in Workspace „Apps“.
