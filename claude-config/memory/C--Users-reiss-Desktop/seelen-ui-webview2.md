---
name: seelen-ui-webview2
description: "Seelen UI (Windows-Shell-Mod, belegt die Win-Taste) rendert mit WebView2 – Edge/WebView2 nie beenden oder deinstallieren; Neustart aus Claude nur über Aufgabenplaner"
metadata:
  node_type: memory
  type: project
  originSessionId: c4f9dd23-7660-44d3-8fab-92aaa2bb7f01
  modified: 2026-10-16T11:05:15.444Z
---

Der User nutzt **Seelen UI** (`C:\Program Files\Seelen UI\seelen-ui.exe`, Dienst `slu-service`, Aufgabe „Seelen UI Service“) als Taskleiste/Launcher. Es belegt die Win-Taste; wenn es kaputt ist, kann der User nichts mehr öffnen. Einstellungen liegen in `AppData\Roaming\com.seelen.seelen-ui`.

**Why:** 2026-10-16 hat eine Haiku-Session beim Debloat versucht, Edge + WebView2 zu deinstallieren und alle Edge-Prozesse beendet. Seelen UI ist eine Tauri-App und rendert mit WebView2 → alle Render-Prozesse starben, nur noch „Widget-Fehler“-Fenster, Win-Taste tot. WebView2 blieb installiert (Uninstaller Exit 93), Neustart hat alles repariert.

**How to apply:**
- WebView2 und `msedgewebview2.exe` nie beenden/deinstallieren, Edge-Debloat nur ohne WebView2.
- Seelen UI neu starten ohne Win-Taste: `Stop-Process -Name seelen-ui -Force`, dann einmalige Aufgabe im Aufgabenplaner (`Register-ScheduledTask` mit `-LogonType Interactive`, `Start-ScheduledTask`, danach `Unregister-ScheduledTask`). Startet außerhalb der Claude-App, umgeht also die MSIX-Umleitung aus [[msix-registry-virtualization]]. „Ausgefallene Symbolleiste“ ist der normale Fenstername der Fancy Toolbar, kein Fehler.
