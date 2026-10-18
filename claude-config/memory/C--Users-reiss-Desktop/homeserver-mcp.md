---
name: homeserver-mcp
description: "Remote MCP server for the home server (GitHub login, local-only rights file) – where code lives, install state, open steps; plus the server's nightly no-internet problem"
metadata:
  node_type: memory
  type: project
  originSessionId: 0cda77ea-0cec-47dd-85ee-a412b8977de8
  modified: 2026-10-12T20:12:52.908Z
---

User wants the home server usable as a remote MCP from everywhere (claude.ai connector → also cloud sessions), with rights settable ONLY locally on the server (anything from status-only to full shell, per project).

Built 2026-10-12 (state: code done + dev-tested, NOT installed yet):
- Source: `~/homeserver-mcp-build/` on server (copy in session scratchpad). Package `homeserver_mcp` (rechte.py, werkzeuge.py, server.py, cli.py, selbsttest.py), `rechte.toml` default, `install.sh` (sudo: apt python3-venv bubblewrap, /opt/homeserver-mcp venv fastmcp==4.1.0, /etc/homeserver-mcp/rechte.toml root-owned, systemd unit `homeserver-mcp`, CLI `sudo mcp-rechte`, runs selftest), `proxy-einrichten.sh` (as luis: LE cert mcp.l0rdr3spawn.duckdns.org, nginx block → unix socket /srv/homeserver-mcp/sock/mcp.sock, compose mount, renew.sh).
- Security design: GitHub OAuth (FastMCP GitHubProvider, only GitHub ID 157418388), redirect URIs only claude.ai/claude.com/localhost; tools registered only if allowed; app-level path checks + systemd sandbox generated from rechte.toml (TemporaryFileSystem /home, Bind(ReadOnly)Paths, InaccessiblePaths for [geheim] + glob matches, docker socket hidden unless needed, NoNewPrivileges); shell runs in bwrap (docker socket + service dirs hidden unless shell.docker=true). Audit log in journald (`sudo mcp-rechte log`).
- Open steps: (1) server internet, (2) user runs `sudo sh ~/homeserver-mcp-build/install.sh`, (3) I run `sh ~/homeserver-mcp-build/proxy-einrichten.sh`, (4) user creates GitHub OAuth App (callback https://mcp.l0rdr3spawn.duckdns.org:10489/auth/callback) + `sudo mcp-rechte github`, (5) claude.ai → Connectors → custom connector URL https://mcp.l0rdr3spawn.duckdns.org:10489/mcp. "Shift-Server" project the user mentioned is unknown – ask.

**Server internet problem (solved 2026-10-12 ~22:10):** server was wrongly in FritzBox Kindersicherung (no outgoing internet after ~22:00). User turned it off themselves. I must not change router security settings myself (refused when asked). If outgoing internet dies again, check that first. See [[homeserver-admin]].
LE cert for mcp.l0rdr3spawn.duckdns.org issued 2026-10-12 (certs/mcp/), so proxy-einrichten.sh skips that step.

Agents Observe (subagent dashboard plugin, github simple10/agents-observe, user chose: local runtime on PC): auto-mode classifier blocked install ("Untrusted Code Integration") – user must install it themselves or allow it. Backup of settings/plugin json taken in ~/.claude/backups/vor-agents-observe-*.
