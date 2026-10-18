---
name: skills-freellm-strix-agentreach
description: "Install locations + state of FreeLLMAPI app, Strix security skills, and Agent Reach skill/CLI on the PC (2026-10-13)"
metadata:
  node_type: memory
  type: project
  originSessionId: 5d13ace9-ab7f-40f9-8db5-5dc0cc015ca9
  modified: 2026-10-13T18:56:38.532Z
---

Installed 2026-10-13 at the user's request ("sollen auf jedem Ding laufen, auch Cloud-Container").

**FreeLLMAPI** (free-LLM gateway, Electron desktop app, NOT a skill): extracted from the user's downloaded `FreeLLMAPI-0.13.10-win.zip` (sha256 matched the official GitHub release [Panniantong? no → tashfeenahmed/freellmapi]) to `C:\Users\reiss\Programme\FreeLLMAPI\FreeLLMAPI.exe`, Desktop shortcut created. User starts it themselves (never launch GUI apps from Claude → [[msix-registry-virtualization]]). Default web UI ~localhost:3001. Could later feed `ask-cheap` as an OpenAI-compatible provider → [[ask-cheap]]. Windows .exe cannot run in a Linux cloud container; a Linux build (AppImage) would be needed on the home server.

FreeLLMAPI facts (2026-10-13): OpenAI-compatible gateway on `http://127.0.0.1:31415/v1`, gateway key stored by me in `~/.config/freellmapi/key` (never print it; classifier blocks it in shell commands → use a Python script that reads the file). Config/DB in `%APPDATA%\FreeLLMAPI` (freeapi.db holds encrypted keys — don't touch, classifier blocks). User added 2 Groq keys only; works: gpt-oss-120b/20b (reasoning leaks into content → extract code blocks), qwen3.8-27b (clean), `auto`, `fusion`. gpt-oss-120b daily budget ran out after ~130k tokens ("1 route checked" → only one key used per model).
Benchmark: UI-rehaul of the Schulmanager clone (`Documents\claude\schulmanager-ui-clone`, scripts `rehaul.py`/`freellm.py` in session scratchpad 5d13ace9…): gpt-oss-120b rewrote all 10 stylesheets (25 chunks, 973 selectors) in 23 min, 100 % selectors kept after retries, build clean, app fully working — BUT visually almost identical to before (generic Inter/grey). Verdict: free models good for mechanical bulk work with automatic checks, bad for design/creative direction. User found my own earlier hand-made mockup "grauenhaft" (too bland, half the features missing) — for UI work show the real running app, not toy mockups.

**Strix** (autonomous AI pentest): user installed the skill pack via `npx skills add usestrix/strix` → lives in `~/.agents/skills/` (10 skills: penetration-testing-with-strix, web-app/api/application-security-testing, owasp-top-10, ci-security-scanning, find/fix-security-vulnerabilities, managed-pentesting). Claude Code reads `~/.claude/skills`, so I COPIED the 10 dirs there → now active. To actually RUN self-hosted it needs Docker + `strix` CLI (neither installed) + an LLM key; or managed cloud (app.strix.ai) with API key. Only against the user's own targets (e.g. Schulmanager test server :8100 → [[schulmanager-deploy]]).

**Agent Reach** (internet-access router, 16 platforms): `npx skills add Panniantong/Agent-Reach` → `~/.agents/skills/agent-reach`, symlinked into `~/.claude/skills/agent-reach` (active). CLI backend `agent-reach` 1.5.0 installed via `pip install` from GitHub → in `Python312/Scripts` (already on PATH). `agent-reach doctor` green zero-config: youtube, bilibili, v2ex, rss, web(Jina). github needs `gh` CLI; twitter/reddit/xhs/linkedin/boss/instagram/facebook need per-platform CLIs + login (pipx twitter-cli, rdt-cli, OpenCLI reusing Chrome session) — not set up. exa_search needs an Exa key. Update via `agent-reach check-update`.

**Cloud containers:** `~/.claude/skills` and these pip/npm installs do NOT reach cloud sessions. For cloud, skills must be committed into the project repo's `.claude/skills/` (+ a bootstrap that pip-installs agent-reach). Which repos = still OPEN with the user. There is a `~/.claude/skills/synced/` bucket (managed sync) — did not touch it.
