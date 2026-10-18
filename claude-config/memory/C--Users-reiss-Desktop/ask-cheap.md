---
name: ask-cheap
description: "ask-cheap CLI (Groq→Gemini→OpenRouter) built 2026-10-06 from Downloads\\HANDOFF-PROMPT.md; status, test results, next steps"
metadata:
  node_type: memory
  type: project
  originSessionId: 1c24c93e-6711-4fd0-8614-56213b64a182
  modified: 2026-10-06T15:15:58.412Z
---

`ask-cheap` = `~\.local\bin\ask-cheap.py` (stdlib Python) + shims `ask-cheap` (Git Bash) / `ask-cheap.cmd`. Keys: env var → Windows Credential Manager `ask-cheap:<VAR>` → `~\.config\ask-cheap\env` (ACL user-only). User saves keys via desktop shortcut `API-Keys.lnk` -> tkinter window `~\.local\bin\api-keys.pyw` (paste/save/delete/check per account incl. groq2; user found the old .cmd prompt unusable, it was moved to sicherung). Never store keys for him, even if pasted in chat.

**Status 2026-10-06:** only Groq key set; in his Groq project all 3 Groq models enabled since 2026-10-06 (120b, 20b, qwen3.8-27b; each 18/18 code tests, 7/7 log). Quality test with 120b: log analysis 7/7 correct, code 18/18 tests, JSON extraction correct (minor: kept "Firma" in name), no hallucination on trap question, translations good. Weak spot: causal "most important cause" claims can be temporally wrong → trust facts, not interpretations. Limits: 8k tokens/min → inputs > ~6k tokens fail (413); back-to-back calls wait up to ~30 s.

Gotchas fixed: Claude Code's Bash may give an open-but-silent stdin pipe → script waits max 3 s then ignores stdin (`--stdin` forces waiting). Prompt after `--files` is recovered. Default system prompt makes answers ~3x shorter.

Groq limits are per model → script switches model on 429/413 before waiting (user enabled all 3 → triple minute budget). `--web` = Groq browser_search (~8k tokens, results were partly outdated). Global rule written to `~\.claude\CLAUDE.md` (2026-10-06, user wants it used proactively for everything suitable); `.env` ignored globally via `~\.config\git\ignore`.

**Multi-account (2026-10-06):** user has 2 Groq accounts. Keys `GROQ_API_KEY` + `GROQ_API_KEY_2` (up to `_5`), saved via the API-Keys window (or `--set-key groq2`). `plan()` ranks (account, model) by remaining TPM from x-ratelimit headers, persisted in `~\.config\ask-cheap\limits.json`; 429 -> immediate switch, known-locked combos skipped, waits only when everything is full (on the soonest-free one). 401/org-restricted -> skip account. Blocked-model cache is per account name. `--status` shows budgets. Tested with mocked HTTP (8 scenarios) + live single key. Backup of pre-change version: `Desktop\sicherung\2026-10-06_ask-cheap-2-groq-keys\`. At build time only key 1 was stored — second key still to be entered by user.

**Next:** Gemini key still missing (would handle inputs too big for Groq + provider fallback). Handy autostart check still pending (see [[msix-registry-virtualization]]).
