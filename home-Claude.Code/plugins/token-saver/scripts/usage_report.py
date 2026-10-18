#!/usr/bin/env python3
"""Token-Verbrauchsbericht für die aktuelle (oder eine angegebene) Session.

Nutzung: usage_report.py [TRANSCRIPT.jsonl]
Ohne Argument wird das neueste Transcript des aktuellen Projekts genommen.
Tool-Ergebnisse werden mit ~4 Zeichen/Token geschätzt; die Summen aus
`usage` sind die echten Zahlen der API.
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

CHARS_PER_TOKEN = 4


def find_transcript():
    home = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    encoded = re.sub(r"[^A-Za-z0-9]", "-", project)
    files = glob.glob(os.path.join(home, "projects", encoded, "*.jsonl"))
    if not files:
        files = glob.glob(os.path.join(home, "projects", "*", "*.jsonl"))
    return max(files, key=os.path.getmtime) if files else None


def text_len(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    total += len(block.get("text", ""))
                elif block.get("type") == "image":
                    total += 1600 * CHARS_PER_TOKEN  # grobe Schätzung pro Bild
                else:
                    total += len(json.dumps(block))
        return total
    return 0


def describe(name, inp):
    for key in ("file_path", "pattern", "command", "url", "description", "prompt"):
        if isinstance(inp, dict) and inp.get(key):
            val = str(inp[key]).replace("\n", " ")
            if key == "file_path":
                val = os.path.basename(val)
            return "%s(%s)" % (name, val[:50] + ("…" if len(val) > 50 else ""))
    return name


def fmt(n):
    return "{:,}".format(int(n)).replace(",", ".")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows-Konsole: sonst cp1252
    except (AttributeError, ValueError):
        pass
    path = sys.argv[1] if len(sys.argv) > 1 else find_transcript()
    if not path or not os.path.exists(path):
        print("Kein Transcript gefunden.")
        return

    usage_by_msg = {}
    tools = {}  # tool_use_id -> (name, label)
    per_tool = defaultdict(lambda: [0, 0])  # name -> [calls, chars]
    results = []  # (chars, label)
    last_usage = None

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            msg = entry.get("message") or {}
            if entry.get("isSidechain"):
                continue
            if entry.get("type") == "assistant":
                usage = msg.get("usage")
                if usage:
                    usage_by_msg[msg.get("id") or entry.get("uuid")] = usage
                    last_usage = usage
                for block in msg.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name", "?")
                        tools[block.get("id")] = (name, describe(name, block.get("input")))
            elif entry.get("type") == "user":
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content or []:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result":
                        name, label = tools.get(block.get("tool_use_id"), ("?", "?"))
                        size = text_len(block.get("content"))
                        per_tool[name][0] += 1
                        per_tool[name][1] += size
                        results.append((size, label))

    totals = defaultdict(int)
    for usage in usage_by_msg.values():
        for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
            totals[key] += usage.get(key) or 0

    print("## Token-Bericht – %s\n" % os.path.basename(path))
    if last_usage:
        ctx = sum(last_usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        print("**Aktueller Kontext:** ~%s Tokens\n" % fmt(ctx))
    print("| API-Summe (%d Antworten) | Tokens |" % len(usage_by_msg))
    print("|---|---:|")
    print("| Input (ungecacht) | %s |" % fmt(totals["input_tokens"]))
    print("| Cache-Schreiben | %s |" % fmt(totals["cache_creation_input_tokens"]))
    print("| Cache-Lesen | %s |" % fmt(totals["cache_read_input_tokens"]))
    print("| Output | %s |" % fmt(totals["output_tokens"]))

    if per_tool:
        print("\n| Tool | Aufrufe | ~Tokens im Kontext |")
        print("|---|---:|---:|")
        for name, (calls, chars) in sorted(per_tool.items(), key=lambda kv: -kv[1][1])[:8]:
            print("| %s | %d | %s |" % (name, calls, fmt(chars / CHARS_PER_TOKEN)))
        print("\n**Größte Einzelergebnisse:**")
        for size, label in sorted(results, reverse=True)[:5]:
            print("- ~%s Tokens – `%s`" % (fmt(size / CHARS_PER_TOKEN), label.replace("`", "'")))

    tips = []
    if last_usage and ctx > 120000:
        tips.append("Kontext ist groß: `/token-saver:checkpoint`, dann `/clear` – oder `/compact <Fokus>`.")
    read_chars = per_tool.get("Read", [0, 0])[1]
    bash_chars = per_tool.get("Bash", [0, 0])[1]
    all_chars = sum(c for _, c in per_tool.values()) or 1
    significant = all_chars / CHARS_PER_TOKEN > 20000  # erst ab relevanter Menge
    if significant and read_chars / all_chars > 0.5:
        tips.append("Read dominiert: erst Grep, dann Read mit offset/limit.")
    if significant and bash_chars / all_chars > 0.4:
        tips.append("Bash-Ausgaben dominieren: `| tail -n 50`, `-q`, Ausgaben in Datei umleiten und greppen.")
    if results and max(results)[0] / CHARS_PER_TOKEN > 10000:
        tips.append("Einzelne Ergebnisse >10k Tokens – solche Recherchen an den `scout`-Agenten auslagern.")
    if tips:
        print("\n**Tipps:**")
        for tip in tips:
            print("- " + tip)


if __name__ == "__main__":
    main()
