---
name: handy-setup
description: "Handy (dictation app) setup — Ctrl+Win = dictation + local LLM cleanup, everything pinned to RTX 3050, how it's wired, and the 2026-10-17 slowdown caused by LM Studio grabbing the 3050"
metadata:
  node_type: memory
  type: project
  originSessionId: 1c24c93e-6711-4fd0-8614-56213b64a182
  modified: 2026-10-17T12:20:00.000Z
---

User wants a local "Wispr Flow" replacement: Handy + local LLM cleanup, **everything exclusively on the RTX 3050** (5070 stays free for games, user plays CS2), autostart, hotkey Ctrl+Win.

- Apply/repair: `Desktop\Handy reparieren.cmd` → `Desktop\sicherung\2026-10-06_handy-autostart\handy-reparieren.ps1` (optional `-Modell <id>`). Makes timestamped settings backup in the same folder. Claude can run it via a one-off scheduled task (see [[msix-registry-virtualization]]); done that way 2026-10-16, log `reparatur-2026-10-16_140407.log` in the same folder, settings + both Run keys (`Handy`, `Handy-Aufraeumer`) verified in the REAL registry/AppData afterwards.
- Until 2026-10-16 the setup had only ever existed in Claude's virtualized copy; real settings were defaults (whisper-medium, accelerator auto, no post-process). Now applied for real.
- Handy is a Tauri app → needs WebView2 like [[seelen-ui-webview2]]; killing Edge/WebView2 processes leaves it running with a dead UI. Fix = restart via scheduled task.
- Settings helper `~\handy-aufraeumer\handy-einstellen.py`: `transcribe_accelerator="gpu"` + `transcribe_gpu_device='["vulkan","id","0000:05:00.0"]'` (3050 PCI addr; only honored when accelerator=gpu; applies to every GGUF/transcribe.cpp model, NOT to ONNX/ORT models). Bindings swapped: `transcribe_with_post_process`=ctrl_left+super_left (main hotkey never post-processes in Handy), `transcribe`=ctrl+shift+space. Post-process: provider `custom` → `http://127.0.0.1:8091/v1`, model `qwen3-4b`, prompt id `diktat_de_en_lokal` from `~\handy-aufraeumer\prompt.txt` (few-shot German prompt; Handy's default English prompt made Qwen translate German→English).
- Cleanup server: `~\handy-aufraeumer\` = llama.cpp b11443 Vulkan + `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`; `start-aufraeumer.ps1` finds the 3050 by name and sets `GGML_VK_VISIBLE_DEVICES` so other GPUs aren't touched; Run key `Handy-Aufraeumer`. Tested: 0.4–1 s per dictation, 4/4 test dictations correct; first request after start ~24 s (Vulkan warm-up).
- 3050 (8 GB) is shared with Jeff's Whisper (~1.6 GB) and Geofinder (~2.3 GB) → don't put bigger LLMs there; LM Studio must NOT be pinned to the 3050 (qwen3.8-27b etc. need the 5070).
- ASR model: currently `handy-computer/whisper-medium-gguf/whisper-medium-Q8_0.gguf` (lang fixed "de", no auto-detect). Proposed parakeet-tdt-0.6b-v3-gguf (auto DE/EN, 740 MB) — waiting for user OK. Partial canary-1b-flash download (.part, ~400 MB) in HF cache, can be deleted.
- **2026-10-17 "Handy ist langsam" (10–20 s per dictation instead of ~1 s):** cause was NOT Handy. The OpenClaw session loaded qwen3.8-27b (17.7 GB) in LM Studio with layers split over both GPUs (+ a JIT duplicate instance) → 7.2 GB on the 3050, 98 % busy; Handy's Whisper and the Qwen3-4B cleanup server got paged out of VRAM into system RAM (GPU Process Memory counter: aufraeumer 122 MB dedicated / 3 GB shared) and STAYED slow even after the 3050 was free again. Fix = restart both (repair script via one-off task, then Handy via its own task; see [[feedback-3050-reserviert]]). Afterwards cleanup 0.1–0.2 s per request again.
- Diagnosis recipe: `Get-Counter '\GPU Process Memory(*)\Dedicated Usage'` per pid + luid (3050 = luid 0x1579d, 5070 = 0x14127 on this machine); `lms ps`; `~\.lmstudio\server-logs\<month>\*.log` shows who loaded what and with how many gpu layers. Handy log: `%LOCALAPPDATA%\com.pais.handy\logs\handy.log` (UTC timestamps), "Transcription completed in Xs for Ys of audio" — healthy is ≫1x real-time.
- Task-Scheduler gotcha: a task that starts llama-server/Handy stays "Running" while those children live; `Unregister-ScheduledTask` while Running killed the repair script mid-way (aufraeumer came up, Handy didn't). Start long-lived programs with a task whose action is `powershell -Command "Start-Process '<exe>'"` (wrapper exits at once → state Ready → safe to unregister); the started program survives.
