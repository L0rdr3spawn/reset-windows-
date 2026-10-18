---
name: feedback-kein-fable
description: "Avoid the Fable model for subagents — too expensive; use Sonnet for complex work, Haiku for simple scans"
metadata:
  node_type: memory
  type: feedback
  originSessionId: da397a22-9891-46f3-a3ae-94186b69fe15
  modified: 2026-10-16T22:22:18.294Z
---

Do not use `model: "fable"` for subagents anymore. Default to Sonnet for complex build work and Haiku for cheap scans or evaluations. Use Fable only if the user explicitly asks for it.

**Why:** On 2026-10-17 the user said "fabel ist viel zu teuer kannst du inzukunft eher auf fabel versuchen zu verzichten". Before that, every Schulpuls wave package and feature agent ran on Fable.

**How to apply:**
- Applies to all agent launches, including the Schulpuls waves 2–4 ([[schulmanager-deploy]]).
- If a task really seems to need a stronger model, say so and ask first.
- Agents already running on Fable may finish; they are not restarted.
