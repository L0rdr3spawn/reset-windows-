# Claude.Code – Addons für Claude Code

## 🔌 token-saver

Plugin, das den Token-Verbrauch in Claude Code senkt – ohne dich beim Arbeiten auszubremsen.

| Baustein | Was es tut | Ersparnis |
|---|---|---|
| **Read-Guard** (Hook) | Blockiert `Read` ohne `offset`/`limit` auf Dateien > 600 Zeilen / 60 KB sowie auf Lockfiles, Build-Output, `node_modules`, `*.min.js` … und schlägt Grep + gezieltes Lesen vor. | oft 5–30k Tokens pro vermiedenem Read |
| **Bash-Guard** (Hook) | Blockiert `cat` großer Dateien, `ls -R`, `tree` ohne `-L`, `find` ohne Filter, `git log` ohne Limit – wenn die Ausgabe ungefiltert im Kontext landen würde (mit `\| head`, `> datei` usw. ist alles erlaubt). | verhindert Ausgabe-Fluten |
| **Session-Hinweis** (Hook) | ~120 Tokens knappe Arbeitsregeln beim Start (Grep vor Read, Limits, kurze Antworten). | spart ein Vielfaches davon |
| **`scout`-Agent** | Günstiger Haiku-Subagent für breite Recherchen; nur seine ~20-Zeilen-Zusammenfassung landet im Hauptkontext. | große Suchen kosten fast nichts im Hauptkontext |
| **`/token-saver:usage`** | Bericht: aktueller Kontext, API-Tokens, welche Tools/Ergebnisse am meisten gekostet haben, Tipps. | Transparenz |
| **`/token-saver:checkpoint`** | Schreibt den Arbeitsstand kompakt nach `.claude/checkpoint.md` → danach `/clear` und frisch weiterarbeiten. | Kontext von 100k+ auf ~1k |
| **Skill `token-efficient-work`** | Wird bei großen Aufgaben automatisch geladen; enthält die Spar-Techniken im Detail. | – |

Blockiert wird nie endgültig: Claude bekommt einen kurzen Hinweis und kann z. B. mit explizitem `limit` trotzdem lesen.

### Installation

In Claude Code:

```
/plugin marketplace add L0rdr3spawn/Claude.Code
/plugin install token-saver@claude-code-addons
```

Oder im Terminal:

```bash
claude plugin marketplace add L0rdr3spawn/Claude.Code
claude plugin install token-saver@claude-code-addons
```

Voraussetzung: Python ≥ 3.8 (`python3`, `python` oder `py -3` – das Plugin nimmt das erste, das funktioniert; ohne Python tun die Hooks einfach nichts).

**Windows:** Claude Code braucht dort Git for Windows (für `sh`). Liegt `claude` nach der Installation nicht im PATH:

```powershell
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:USERPROFILE\.local\bin", "User")
```

Danach das Terminal neu öffnen.

### Konfiguration

Optional `~/.claude/token-saver.json` (global) oder `<projekt>/.claude/token-saver.json` (pro Projekt):

```json
{
  "maxReadLines": 600,
  "maxReadBytes": 60000,
  "maxCatLines": 300,
  "readGuard": true,
  "bashGuard": true,
  "sessionHint": true,
  "extraBlockedPatterns": ["*/generated/*", "*.snap"],
  "allowPatterns": ["*/docs/big-but-important.md"]
}
```

Komplett abschalten für eine Session: `TOKEN_SAVER_DISABLE=1 claude`

### Tests

```bash
python3 -m unittest discover plugins/token-saver/tests
```

### Struktur

```
.claude-plugin/marketplace.json      # Marketplace-Definition
plugins/token-saver/
  .claude-plugin/plugin.json
  hooks/hooks.json                   # SessionStart + PreToolUse(Read|Bash)
  scripts/run.sh                     # startet Skripte mit dem passenden Python (Windows-tauglich)
  scripts/guard.py                   # Read-/Bash-Guard
  scripts/session_start.py           # knapper Session-Hinweis
  scripts/usage_report.py            # Token-Bericht
  scripts/config.py                  # Defaults + Config-Laden
  agents/scout.md                    # Haiku-Recherche-Agent
  commands/usage.md, checkpoint.md
  skills/token-efficient-work/SKILL.md
  tests/test_guard.py
```
