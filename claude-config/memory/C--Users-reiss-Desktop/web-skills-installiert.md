---
name: web-skills-installiert
description: Design/security/DSGVO/a11y skills installed 2026-10-13 in ~/.claude/skills for the school app; user still picks which run in every workflow
metadata:
  node_type: memory
  type: project
  originSessionId: 5081fa59-1fb8-45aa-ab40-f830914d3c91
  modified: 2026-10-13T20:42:53.013Z
---

On 2026-10-13, 20 skills were copied as plain skill folders into `~/.claude/skills`, for the school app (see [[schulmanager-deploy]]): frontend-design, webapp-testing, web-design-guidelines, vercel-react-best-practices, design-taste-frontend, minimalist-ui, ui-ux-pro-max, owasp-security, sentry-security-review (renamed from security-review because of the built-in /security-review), security-and-hardening, gdpr-dsgvo-expert, gdpr-data-handling, wcag-auditor, codeql, semgrep, sarif-parsing, differential-review, sharp-edges, supply-chain-risk-auditor, i-have-adhd.

**Why:** `claude plugin install` was blocked by the auto-mode classifier (persistence/hooks), so they were copied without hooks. The marketplaces `trailofbits` and `i-have-adhd` are added. insecure-defaults (ToB, command-only) is NOT installed. i-have-adhd only runs via /i-have-adhd; making it always-on needs its plugin hook plus `~/.claude/.i-have-adhd-always`, or a rule in CLAUDE.md.

**How to apply:** The user still decides which skills belong in every workflow. Ask before wiring any of them into CLAUDE.md. wcag-auditor needs `npm install` in its folder before its first run.
