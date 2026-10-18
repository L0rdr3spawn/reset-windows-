---
name: schulpuls-siezen
description: "Schulpuls (formerly Schulmanager) UI and letters address everyone with \"Sie\" – also students, never \"du\""
metadata:
  node_type: memory
  type: feedback
  originSessionId: da397a22-9891-46f3-a3ae-94186b69fe15
  modified: 2026-10-16T11:12:39.408Z
---

All visible texts of Schulpuls address users formally ("Sie", "Ihr"). That covers UI, Zugangsbriefe/PDFs, e-mails and notifications, and applies to students too. Never use "du".

**Why:** 2026-10-16 the user decided "siezen" when asked whether the app should use du or Sie. Before that, some student views used deliberate du-variants, and the logout dialog used du.

**How to apply:** Require "Sie-Form" in agent prompts that write UI texts. When reviewing, grep for du/dein/kannst etc. in string literals. Related: [[schulmanager-deploy]].
