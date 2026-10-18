---
name: feedback-weniger-checks
description: "User finds repeated full test runs excessive – only test what changed, full suite only before a deploy"
metadata:
  node_type: memory
  type: feedback
  originSessionId: da397a22-9891-46f3-a3ae-94186b69fe15
  modified: 2026-10-12T20:21:07.148Z
---

Don't re-run the full test suite (or let every agent run it) after each change. Run only the tests of the areas that were actually changed; things already checked and untouched need no re-check. One combined full run right before a deploy is enough.

**Why:** 2026-10-12 the user remarked "fast 1400 Checks … ein bisschen viel" after many agents each ran the whole backend+frontend suites.
**How to apply:** In agent prompts say "nur die Tests der geänderten Bereiche, keinen Gesamtlauf"; do the full run myself once before deploying (see [[schulmanager-deploy]]).
