---
name: jev-plugins
description: Installierte Jev-Plugins (claude-jev MCP-Tools, building-with-jev Skill) + welche bewusst ausgelassen wurden und warum
metadata:
  type: project
---

Stand 2026-09-22, zusätzlich zu [[typesafe-skill]] und dem eigenen Wächter aus [[jev-im-workflow]]:
- `claude-jev@claude-jev` (github.com/buchmark/claude-jev): MCP-Tools jev_ask, jev_pick_option, jev_review_findings, jev_rank_hypotheses, jev_filter_relevance + /jev-ask, /jev-pick, /jev-review, /jev-why. **Lokal gepatchte Kopie** in `~/.claude/local-plugins/claude-jev` (Feld `userConfig.model.options` entfernt, weil Claude Code 2.1.217 das ablehnt). API-Key bleibt leer → nimmt `TYPESAFE_API_KEY` aus der User-Umgebung. Getestet, läuft.
- `jev@building-with-jev` (github.com/dbreunig/building-with-jev-skill): reiner Skill zum Programmieren mit Jev.
- Ausgelassen: tamaratran/jev-pruner + fast-jev-compaction (brauchen Function-Hooks ab 2.1.274), 0x7067/claude-jev (ruft `python3`, gibt's hier nicht), Panebianco00/jev-claude + klukacin/JEV_Claude_plugin (Bash-/Fragen-Gates doppeln den eigenen jev.py-Hook), shitianfang/jev-use (lädt npm-Paket zur Laufzeit).

**Why:** Der User fand zu viele Rückfragen/Einrichtungsdialoge nervig ("viel zu viel") – er will unkompliziert.
**How to apply:** Jev-Tools nur gezielt nutzen, keine zusätzlichen Frage-Hooks installieren; bei Plugin-Setup Optionen selbst per `--config` vorbelegen statt Dialoge auszulösen.
