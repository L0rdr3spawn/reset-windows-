---
name: schulpuls-betatest-openclaw
description: "Local OpenClaw beta-test pipeline for Schulpuls (admin + 2 critical testers, cross-review, update patches in Documents\\Schulpuls-Betatest) and the Claude skill schulpuls-nutzercheck"
metadata:
  node_type: memory
  type: project
  originSessionId: ba61288a-3103-4204-a3ef-1d49a447bf62
  modified: 2026-10-17T14:09:30.153Z
---

Built 2026-10-17 at the user's request: OpenClaw agents beta-test the Schulmanager area by area; the admin bot "always has the current copy from the server (not the official one)"; two testers each do a task, then critique each other's report; admin writes an update patch into a Documents folder; repeat until the whole app is covered. Plus a Claude skill for a "zweiter Check / User-Check".

- Agents (Gemma on 5070, see [[openclaw-heimserver]]): `sm-admin`, `sm-tester-a`, `sm-tester-b`, workspaces `~\.openclaw\workspace-sm-*` with own AGENTS.md/SOUL.md (German, strict, Sie-form rules, report/critique/patch formats), `tools.deny` = exec, process, write, edit, apply_patch, cron, gateway, nodes, message, sessions_send, sessions_spawn, canvas (only read/browser/web left; the script writes files).
- Copy: `Documents\Schulpuls-Betatest\skripte\kopie-holen.ps1` → `~\.openclaw\workspace-sm-admin\schulmanager-kopie` (server `~/schulmanager/src` via ssh tar, without lizenzserver, tests, .env, *.db; `STAND.txt` with image tag).
- Orchestrator: `skripte\betatest-runde.ps1` (deterministic, because Gemma E4B can't coordinate reliably): areas = 24 atlas `features/*.md` from `INDEX.md`, progress in `status.json`; per area admin plan (AUFTRAG A/B) → both testers in parallel (`openclaw agent --agent … --message-file`) → cross-review → admin patch → `patches\<stamp>_<slug>.md` + 4 files in `berichte\`. Must run OUTSIDE the Claude MSIX (Desktop .cmd or one-off scheduled task).
- Desktop: "Betatest naechster Bereich", "Betatest alles durcharbeiten" (-Alle), "Betatest Zugaenge eintragen".
- UI testing target = demo instance (https://schulmanager-demo.l0rdr3spawn.duckdns.org:10489). It no longer has role buttons (owner-issued demo accesses with passwords) → user enters 2 demo accesses via hidden prompt into `~\.openclaw\secrets\betatest-zugaenge.json` (ACL user-only); Claude never reads it or types passwords. Without it testers only see public pages + code.
- OpenClaw browser: `browser.headless=true`, `browser.executablePath` = Edge; verified snapshot of the demo login page.
- Claude skill: `~/.claude/skills/schulpuls-nutzercheck/SKILL.md` (start round via scheduled task, read patch, mandatory own critical re-check, never auto-apply).

Related: [[schulmanager-deploy]], [[schulpuls-atlas]], [[msix-registry-virtualization]].
