---
name: feedback-3050-reserviert
description: "RTX 3050 (LM Studio / CUDA GPU index 1) is reserved for Handy, Jeff, Geofinder — LM Studio loads with disabledGpus:[1]; ONE user-approved exception: OpenClaw's qwen3.8-27b via 'OpenClaw starten' uses both GPUs, Handy is slow meanwhile and needs a restart after 'OpenClaw stoppen'"
metadata:
  type: feedback
---

The RTX 3050 (8 GB, PCI 0000:05:00.0, LM Studio/CUDA GPU index 1, Vulkan2) is reserved for Handy's Whisper + cleanup server, Jeff's Whisper and Geofinder. LM Studio models go ONLY on the RTX 5070 (index 0) and must fit there (≤ ~9–10 GB incl. KV cache) — with the single exception at the bottom (OpenClaw's 27B, user-approved).

**Why:** 2026-10-17 an OpenClaw test loaded qwen3.8-27b split across both GPUs (n_gpu_layers 39–56, plus a JIT duplicate with 64k context). 7.2 GB landed on the 3050, Handy's models were evicted from VRAM and dictation took 10–20 s; the user asked for a permanent fix ("dauerhaft"). See [[handy-setup]], [[openclaw-heimserver]].

**How to apply:**
- Every LM Studio load from any session: `gpu: {mainGpu: 0, disabledGpus: [1], splitStrategy: "favorMainGpu"}` + `gpuStrictVramCap: true` (template: `Programme\openclaw-runner\lms-load-5070.py`). Never pick n_gpu_layers so that it spills onto the 3050.
- **User decision 2026-10-17: NO global GPU lock in LM Studio's GUI** (user declined "GPU Split Configuration → disable 3050"; don't propose it again). Protection is only via the load script + this rule.
- JIT loads (OpenClaw gateway → LM Studio with `justInTimeModelLoading: true`) use LM Studio defaults = both GPUs. Pre-load with the script and keep JIT off (the GUI lock exists under "GPU Split Configuration" → "Enable/Disable GPU", but the user does not want it).
- If Handy gets slow: check `lms ps` and the GPU Process Memory counters first, then restart cleanup server + Handy (they do not recover from VRAM eviction by themselves).
- 2026-10-17: JIT loading is now OFF in LM Studio (user approved), so nothing loads with default GPU settings any more; every model must be pre-loaded with the 5070 script.
- **Exception, user decision 2026-10-17 (explicit, after being told Handy gets slow):** OpenClaw's default model is qwen3.8-27b-obliterated loaded on BOTH GPUs (`openclaw-runner\lms-load-beide.py`, strict VRAM cap) by "OpenClaw starten"; "OpenClaw stoppen" frees the 3050 again. All other loads still 5070-only.
- While the 27B is loaded Handy dictation takes 10–20 s (expected, user accepted). After "OpenClaw stoppen" Handy does NOT recover by itself: its Whisper + the cleanup server stay paged out → `openclaw-stop.ps1` therefore restarts both after `lms unload` (implemented + verified by the OpenClaw session 2026-10-17: cleanup 0.5 s/request afterwards). Also: the 27B pushed system RAM to 98 % (~17 GB private), so it may not stay the default.
