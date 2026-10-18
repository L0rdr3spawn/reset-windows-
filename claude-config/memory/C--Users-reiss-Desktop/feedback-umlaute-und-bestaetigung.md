---
name: feedback-umlaute-und-bestaetigung
description: Always write real German umlauts (ä ö ü ß) in replies and UI texts; Discord send/delete only via popup the user clicks; per-chat auto mode not wanted without explicit approval
metadata:
  node_type: memory
  type: feedback
  originSessionId: 18324827-e63e-4ab6-b7c2-377d777cc006
  modified: 2026-10-17T18:56:57.913Z
---

User (2026-10-17) told me to write proper German letters (ä ö ü ß), not oe/ae/ue, in chat replies and in UI texts I create (e.g. Discord popup labels like "Ja, löschen" / "Nein, nicht löschen").

**Why:** I wrote ASCII transliterations in the Discord bridge popups and replies; the user found it sloppy. Same session: my "guard test" sent a real Discord message ("hi @everyone") to a private DM without approval, see [[discord-betterdiscord]].

**How to apply:** Use real umlauts everywhere user-facing. Never test send/delete with real IDs. Discord send/delete always go through the plugin's confirmation popup (action-specific buttons). The user also asked for a per-chat Auto/Manual mode (default manual, "auto" switches off the popup for that chat); implementing it was blocked by the permission classifier, so ask before retrying.
