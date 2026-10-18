---
name: jeff-voice-assistant
description: "Where the user's tools live — \"Jeff\" voice assistant vs. C:\\JEEV, and the Claude-Leiste overlay"
metadata:
  node_type: memory
  type: project
  originSessionId: 25f2b5e3-d233-4ec7-a7db-969ea53b3aee
  modified: 2026-10-06T13:59:52.831Z
---

- "Jeff" (user's voice assistant, wake word "hey jeff") = `C:\Users\reiss\jev-assistent\` (jev_assistent.py, config.json, autostart.py, Jeff.exe launcher, einstellungen.pyw settings window). NOT `C:\JEEV` (a separate, older JEEV project).
- Jeff STT: Vosk wake word + faster-whisper `large-v3-turbo` (since 2026-10-04, was "small") on CUDA GPU 1 = RTX 3050 (5070 kept free for games). Handy uses whisper.cpp format, so models can't be shared.
- "Overlay" / Claude-Leiste = `C:\Users\reiss\Desktop\Claude-Leiste\claude_leiste.pyw`, opened with Alt+Space (user may say "Alt+Tab"), Haiku triage with escalation to Sonnet/Opus.
- User speaks German via voice dictation — names get mistranscribed (JEEV/Jev/Jeff). Since 2026-10-04: Handy (local, open source, `%LOCALAPPDATA%\Handy\handy.exe`, settings `%APPDATA%\com.pais.handy\settings_store.json`, hotkey ctrl_left+super_left, lang "de") replaced Wispr Flow (uninstalled). Real setup (as of 2026-10-06) uses model `handy-computer/cohere-transcribe-03-2026-gguf` (Q5_K_M), stored in `~\.cache\huggingface\hub`; the old "turbo" setup only existed in Claude's MSIX copy. User may call it "das Handy". Don't launch Handy from Claude (see msix memory). User refused to pay for Wispr Pro; don't suggest cloud dictation. No git in these folders; backups go into `sicherung\<date>_<topic>\`.

Related: [[msix-registry-virtualization]]
