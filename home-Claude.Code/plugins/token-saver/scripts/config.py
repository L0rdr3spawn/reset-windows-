"""Gemeinsame Konfiguration für token-saver.

Reihenfolge (spätere überschreiben frühere):
  1. DEFAULTS
  2. ~/.claude/token-saver.json
  3. <projekt>/.claude/token-saver.json
  4. Umgebungsvariable TOKEN_SAVER_DISABLE=1 schaltet alles ab.
"""
import json
import os
import sys

DEFAULTS = {
    "enabled": True,
    # Kurze Arbeitsregeln beim Sessionstart injizieren.
    "sessionHint": True,
    # Read ohne offset/limit auf große Dateien blockieren.
    "readGuard": True,
    "maxReadLines": 600,
    "maxReadBytes": 60000,
    # Offensichtlich teure Bash-Befehle blockieren.
    "bashGuard": True,
    "maxCatLines": 300,
    # Generierte/uninteressante Dateien (Glob-Muster auf den Pfad).
    "blockedPatterns": [
        "*package-lock.json", "*yarn.lock", "*pnpm-lock.yaml", "*bun.lockb",
        "*Cargo.lock", "*poetry.lock", "*composer.lock", "*Gemfile.lock",
        "*go.sum", "*uv.lock", "*Pipfile.lock",
        "*.min.js", "*.min.css", "*.map",
        "*/node_modules/*", "*/dist/*", "*/build/*", "*/.next/*",
        "*/vendor/*", "*/__pycache__/*", "*/.venv/*", "*/coverage/*",
    ],
    # Zusätzliche Muster, ohne die Defaults zu ersetzen.
    "extraBlockedPatterns": [],
    # Muster, die nie blockiert werden (haben Vorrang).
    "allowPatterns": [],
}

# Binär-/Medienformate liest Read speziell (Bilder, PDFs, Notebooks) – nicht anfassen.
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico",
    ".pdf", ".ipynb",
}


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_config(cwd=None):
    cfg = dict(DEFAULTS)
    home = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    cfg.update(_load(os.path.join(home, "token-saver.json")))
    project = os.environ.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd()
    cfg.update(_load(os.path.join(project, ".claude", "token-saver.json")))
    if os.environ.get("TOKEN_SAVER_DISABLE") == "1":
        cfg["enabled"] = False
    cfg["blockedPatterns"] = list(cfg.get("blockedPatterns") or []) + list(cfg.get("extraBlockedPatterns") or [])
    return cfg


def utf8_stdio():
    """Windows nutzt sonst cp1252 für stdin/stdout -> Umlaute/Pfade kaputt."""
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
