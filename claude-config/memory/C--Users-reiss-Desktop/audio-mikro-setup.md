---
name: audio-mikro-setup
description: "User's audio chain — SteelSeries Sonar in front of everything, mic must ALWAYS be the Torch Streaming Microphone, Bose earbuds never as mic; Sonar local API"
metadata:
  node_type: memory
  type: project
  originSessionId: 1e589eb1-4aa8-4d62-8c4a-65db0b78bf88
  modified: 2026-10-17T15:05:00.000Z
---

"Touch-Mikrofon" in dictation = **Torch Streaming Microphone** (USB). User wants it as the only mic; Bose QC Earbuds II (and second Bose pair "LE-Boooooom") must never become the mic.

- Windows defaults all point to SteelSeries Sonar virtual devices; Sonar picks the physical device. Handy's `selected_microphone` is null → follows Sonar.
- Root cause found 2026-10-12: Sonar's mic fallback list had Bose hands-free mic #1, Torch #17 → every earbud reconnect switched the mic to the earbuds. Fixed via Sonar's local API: all capture devices except Torch excluded (`PUT http://<sonar>/fallbackSettings/excludeDevice/ChatCapture/<url-encoded endpoint id>`; port from `GET https://127.0.0.1:6327/subApps` → sonar.metadata.webServerAddress; GG port from `C:\ProgramData\SteelSeries\GG\coreProps.json`). `GET /classicRedirections` shows current devices. DB backup in `Desktop\sicherung\2026-10-12_sonar-mikro\`.
- Earbud drops: Intel AX210 BT adapter was in USB selective suspend; adapter timeout seen 17:39. Admin script `Desktop\Bluetooth stabil machen.cmd` (disables Bose hands-free profile + BT power saving; undo: `bluetooth-rueckgaengig.ps1` in the sicherung folder). Whether the user ran it: unknown — check `bluetooth-stabil_*.log` there.
- Diagnose drops with `Microsoft-Windows-Audio/Operational` event 65 (NewState 8 = unplugged, 1 = active).
- **2026-10-17 "Handy Whisper geht nicht" = mic too quiet, not Whisper.** Handy's saved WAVs (`%APPDATA%\com.pais.handy\recordings\*.wav`, 16 kHz mono int16) peak at only 0.01–0.03 since 2026-10-12 (0.29 on 10-11 — probably the earbuds back then). Whisper copes with long dictations, short ones come back empty ("Transcription result is empty"). Chain was correct: Sonar mic = "Mikrofon (2- Torch …)", Sonar chatCapture volume 1.0, Windows Sonar-mic endpoint 100 %. Changes made: Windows level of the Torch endpoint 93.5 % → 100 % (+31 dB, via pycaw IAudioEndpointVolume; pycaw installed with pip --user, lands in Claude's private copy); Sonar mic profile "Custom" got `volumeStabilizerState {enabled true, value 0.4}` (noise canceling stays 0.9). Backup of the profile: `Desktop\sicherung\2026-10-17_sonar-mikro-pegel\mikro-config-vorher.json`. **Real root cause (user found it 2026-10-17): the Torch Streaming Microphone has a PHYSICAL gain knob/switch and it was turned down.** First thing to check when Handy dictations come back empty or recordings peak < 0.05. The Windows 100 % level and the Sonar stabilizer were left on (harmless).
- Sonar API recipe (verified 2026-10-17): `GET https://127.0.0.1:6327/subApps` (self-signed cert; PowerShell 5.1 fails on it, use Python with an unverified ssl context) → `subApps.sonar.metadata.webServerAddress` (was http://127.0.0.1:8148; port changes). The 7960 port in coreProps.json is NOT the right one. `GET /configs/selected` = active profile per virtual device (chatCapture = mic); update a profile with `PUT /configs` and the FULL config object as body (`PUT /configs/{id}` → 405). `GET /volumeSettings/classic`, `/classicRedirections`, `/audioDevices` as before.
- Loudness check recipe: Python `wave` over the recordings folder, print peak/RMS per file; healthy speech should peak > 0.1.
