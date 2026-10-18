#!/usr/bin/env python3
"""SessionStart-Hook: injiziert wenige, knappe Arbeitsregeln (~120 Tokens).

Absichtlich kurz: der Hinweis selbst kostet in jeder Session Kontext.
Abschaltbar über "sessionHint": false in token-saver.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import load_config, utf8_stdio  # noqa: E402

HINT = """token-saver active. Keep context lean:
- Locate with Grep/Glob before Read; Read large files with offset/limit.
- Prefer quiet flags and limits (-q, --oneline, -n, | head, | tail -n 50).
- Don't re-read files you just edited or already have in context.
- Delegate broad exploration to the `token-saver:scout` agent; keep only its summary.
- Answer concisely: no restating the question, no recap of unchanged code; show diffs/snippets, not whole files."""


def main():
    utf8_stdio()
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    cfg = load_config(data.get("cwd"))
    if not (cfg["enabled"] and cfg["sessionHint"]):
        return
    json.dump({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": HINT}}, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
