#!/usr/bin/env python3
"""PreToolUse-Hook: blockiert Read-/Bash-Aufrufe, die unnötig viele Tokens erzeugen.

Blockieren heißt hier: Claude bekommt einen kurzen Hinweis, wie es günstiger geht
(Grep, offset/limit, head, -n …). Jede Regel hat einen legitimen Ausweg, damit
nichts dauerhaft verhindert wird.
Hinweise an Claude sind bewusst auf Englisch und knapp gehalten (weniger Tokens).
"""
import fnmatch
import json
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SKIP_EXTENSIONS, load_config, utf8_stdio  # noqa: E402

CHARS_PER_TOKEN = 4


def deny(reason):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "[token-saver] " + reason,
        }
    }, sys.stdout)
    sys.exit(0)


def matches(path, patterns):
    norm = path.replace(os.sep, "/")
    base = os.path.basename(norm)
    return any(fnmatch.fnmatch(norm, p) or fnmatch.fnmatch(base, p) for p in patterns)


def file_stats(path):
    """(bytes, lines) oder None, falls keine lesbare reguläre Datei."""
    try:
        if not os.path.isfile(path):
            return None
        size = os.path.getsize(path)
        lines = 0
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                lines += chunk.count(b"\n")
        return size, lines
    except OSError:
        return None


def too_big(path, cfg, max_lines):
    """Grund-String, wenn die Datei zu groß ist, sonst None."""
    stats = file_stats(path)
    if not stats:
        return None
    size, lines = stats
    if lines > max_lines or size > cfg["maxReadBytes"]:
        return "%s has %d lines / %d bytes (~%d tokens)" % (
            os.path.basename(path), lines, size, size // CHARS_PER_TOKEN)
    return None


# ---------------------------------------------------------------- Read

def check_read(tool_input, cfg, cwd):
    if not cfg["readGuard"]:
        return
    path = tool_input.get("file_path") or ""
    if not path:
        return
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    if tool_input.get("limit") or tool_input.get("pages"):
        return  # bewusst eingeschränkt -> ok
    if os.path.splitext(path)[1].lower() in SKIP_EXTENSIONS:
        return
    if matches(path, cfg["allowPatterns"]):
        return
    if matches(path, cfg["blockedPatterns"]):
        deny("%s looks generated/vendored (lockfile, build output, minified). "
             "Use Grep for what you need. If you truly need it, Read again with offset/limit."
             % os.path.basename(path))
    reason = too_big(path, cfg, cfg["maxReadLines"])
    if reason:
        deny(reason + ". Grep for the relevant symbol first, then Read with offset/limit "
             "(or pass limit explicitly if you really need the whole file).")


# ---------------------------------------------------------------- Bash

SEPARATORS = {"&&", "||", ";", "&", "\n"}


def statements(command):
    """Zerlegt in Anweisungen -> Liste von Pipeline-Stufen -> Tokenlisten."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    result, stages, cur = [], [], []
    for tok in lex:
        if tok in SEPARATORS or tok == ";;":
            stages.append(cur)
            result.append(stages)
            stages, cur = [], []
        elif tok == "|":
            stages.append(cur)
            cur = []
        else:
            cur.append(tok)
    stages.append(cur)
    result.append(stages)
    return [[s for s in st if s] for st in result if any(st)]


def redirected(tokens):
    # stdout geht in eine Datei -> landet nicht im Kontext
    for i, tok in enumerate(tokens):
        if tok in (">", ">>", ">|", "&>", "&>>") and not (i > 0 and tokens[i - 1] == "2"):
            return True
    return False


def drop_redirections(tokens):
    out, skip = [], False
    for i, tok in enumerate(tokens):
        if skip:
            skip = False
            continue
        if re.fullmatch(r"[<>&]+\|?", tok):
            skip = True  # nächstes Token ist das Ziel (Datei oder Deskriptor)
            if out and out[-1].isdigit() and i > 0 and tokens[i - 1] == out[-1]:
                out.pop()  # Deskriptor wie "2" in "2>"
            continue
        out.append(tok)
    return out


def strip_env(tokens):
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    while i < len(tokens) and tokens[i] in ("sudo", "command", "time", "nice"):
        i += 1
    return tokens[i:]


def check_bash(tool_input, cfg, cwd):
    if not cfg["bashGuard"]:
        return
    command = tool_input.get("command") or ""
    if "<<" in command:
        return  # Heredocs sind meist Schreibvorgänge
    try:
        parsed = statements(command)
    except ValueError:
        return
    for stages in parsed:
        if len(stages) != 1:
            continue  # Ausgabe wird weiterverarbeitet (| head, | grep …)
        tokens = strip_env(stages[0])
        if not tokens or redirected(tokens):
            continue
        tokens = drop_redirections(tokens)
        if not tokens:
            continue
        prog, args = os.path.basename(tokens[0]), tokens[1:]
        flags = [a for a in args if a.startswith("-")]

        if prog == "cat":
            for arg in args:
                if arg.startswith("-"):
                    continue
                path = arg if os.path.isabs(arg) else os.path.join(cwd, arg)
                if matches(path, cfg["allowPatterns"]):
                    continue
                if matches(path, cfg["blockedPatterns"]):
                    deny("`cat %s` dumps a generated/vendored file. Use grep/head, or the Read tool with offset/limit." % arg)
                reason = too_big(path, cfg, cfg["maxCatLines"])
                if reason:
                    deny("`cat` on large file: %s. Use `grep -n`, `head -n`/`sed -n 'A,Bp'`, "
                         "or the Read tool with offset/limit." % reason)

        elif prog == "ls" and any(re.match(r"^-[A-Za-z]*R", f) or f == "--recursive" for f in flags):
            deny("`ls -R` can be huge. Use the Glob tool, `find . -maxdepth 2`, or `git ls-files | head`.")

        elif prog == "tree" and not any(f.startswith("-L") for f in flags):
            deny("`tree` without -L can be huge. Add `-L 2` (and `-I node_modules`).")

        elif prog == "find":
            limiting = ("-maxdepth", "-name", "-iname", "-path", "-ipath", "-regex",
                        "-iregex", "-newer", "-mtime", "-mmin", "-size", "-quit")
            if not any(a in limiting for a in args):
                deny("Unbounded `find` can list thousands of paths. Use the Glob tool, "
                     "add -maxdepth/-name, or pipe to `head`.")

        elif prog == "git" and args[:1] == ["log"]:
            limited = any(re.match(r"^(-n\d*|-\d+|--max-count(=.*)?|--since.*|--after.*)$", a) for a in args[1:])
            if not limited:
                deny("`git log` without a limit can be huge. Add `-n 20` (and `--oneline`).")


def main():
    utf8_stdio()
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    cwd = data.get("cwd") or os.getcwd()
    cfg = load_config(cwd)
    if not cfg["enabled"]:
        return
    tool = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    if tool == "Read":
        check_read(tool_input, cfg, cwd)
    elif tool == "Bash":
        check_bash(tool_input, cfg, cwd)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # ein kaputter Guard darf nie die Arbeit blockieren
        pass
