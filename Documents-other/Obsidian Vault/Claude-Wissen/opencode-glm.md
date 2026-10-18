---
name: opencode-glm
description: "OpenCode 1.18.34 global per npm (hermes-Node) installiert, Standardmodell zai/glm-5.3-flash; Stand 2026-10-02 fehlte noch der Z.ai-Schlüssel"
metadata:
  node_type: memory
  type: project
  originSessionId: 01d63dc1-a65b-40fd-96f0-7175d8a1452c
  modified: 2026-10-02T15:52:24.498Z
---

OpenCode liegt unter `C:\Users\reiss\AppData\Local\hermes\node\opencode.cmd` (npm global, Paket
`opencode-ai`), Konfiguration in `C:\Users\reiss\.config\opencode\opencode.json` mit
`model` = `zai/glm-5.3` (am 2026-10-02 vom User von Flash umgestellt), `small_model` =
`zai/glm-5.3-flash`. Anmeldedaten: `~\.local\share\opencode\auth.json`.

Stand 2026-10-02: 0 Credentials – der User muss `opencode auth login` (Z.AI) selbst ausführen.
Ohne Schlüssel listet `opencode models` nur die Gratis-Modelle von OpenCode Zen, und
`opencode models zai` meldet „Provider not found“ (kein Fehler in der Config).

**Why:** Der User wollte OpenCode mit GLM 5.3 Flash; welcher Anbieter (Z.ai-API, GLM Coding Plan,
Zen, OpenRouter) blieb offen, Z.ai direkt ist die Vorgabe.

**How to apply:** Bei Coding Plan die Modell-ID auf `zai-coding-plan/glm-5.3-flash` ändern, bei
OpenRouter auf `openrouter/z-ai/glm-5.3-flash`. Updates/Neuinstallation über
`opencode/install.ps1` per WMI starten, siehe [[claude-app-container-virtualisiert-hkcu]].
