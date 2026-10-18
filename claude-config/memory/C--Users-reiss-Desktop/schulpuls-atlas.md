---
name: schulpuls-atlas
description: "External code atlas for Schulpuls (outside the repo, never shipped); look things up there first via the schulpuls-atlas skill"
metadata:
  node_type: memory
  type: reference
  originSessionId: da397a22-9891-46f3-a3ae-94186b69fe15
  modified: 2026-10-16T11:40:46.365Z
---

There is a code atlas: `C:\Users\reiss\Documents\claude\schulpuls-atlas\`. It has a local git with no remote and holds INDEX.md, features/<area>.md, design/rezepte.md, api/, db/, frontend/, tests/map.md, symbols.tsv, doku/code (the former docs/code), doku/intern and SCHUTZ-DES-CODES.md.

Generator: `C:\Users\reiss\Documents\claude\tools\schulpuls-atlas\atlas.py`, commands `find|update|check|selftest`, always run with `python -X utf8`. Skill: `~/.claude/skills/schulpuls-atlas/SKILL.md`.

**Why:** created 2026-10-16 because the user wants changes made without reading the whole code. The atlas lives outside the repo so customers who run the code cannot reverse-engineer it from the docs.

**How to apply:**
- Use `atlas.py find` and the area file first, then read only the sections they name.
- After code changes, run `update` and `check`.
- Give subagents the atlas path.
- Never copy anything from the atlas into the repo.

Related: [[schulmanager-deploy]], [[schulpuls-siezen]].

**Code graph (since 2026-10-17, user's wish: "document everything and make it the standard"):** Graphify 0.9.74 (`uv tool install graphifyy==0.9.74`, pinned, runs locally without AI) builds a graph of the whole repo into `schulpuls-atlas/graph/graphify-out/`. Update it with `tools/schulpuls-atlas/graph-update.sh`. Query it with `graphify query|explain|path --graph <...>/graph.json`. After every code change, run atlas `update`/`check` and the graph update. The skill and WELLEN-REGELN say the same.
