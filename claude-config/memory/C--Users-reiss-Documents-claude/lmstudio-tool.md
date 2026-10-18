---
name: lmstudio-tool
description: Selbstgebautes CLI lmstudio.py zum Lesen/Verwalten von LM-Studio-Chats und Multi-Agent-Betrieb
metadata: 
  node_type: memory
  type: project
  originSessionId: 2b2dcd41-b640-44f3-aa9b-4c30d79ae194
  modified: 2026-08-28T00:41:09.786Z
---

`C:\Users\reiss\Documents\claude\lmstudio.py` — selbstgebautes Python-CLI, das LM-Studio-Chats liest, verwaltet und lokale Modelle als Agenten laufen lässt. Genutzt für [[delegate-small-tasks-to-local-llm]].

**Befehle:** `server [start]`, `models`, `list`, `read`, `new`, `rename`, `delete <idx|all>`, `say <idx> "..."`, `gen "..."` (stateless One-Shot), `repair`, `agents`, `ask-agent <name> "..."`, `roundtable "..." --turns N`, `team "..." --rounds N` (Agenten arbeiten parallel, Supervisor betreut). Agenten-Rollen in `lmstudio_agents.json`.

**Datei-Agent:** `lmagent.py` gibt einem lokalen Modell echte Werkzeuge (ReAct-Tool-Loop): web_search, fetch_url, list_files, read_file, write_file, finish — kann im Web suchen/Seiten lesen und Dateien lesen, bewerten, umschreiben, neu anlegen. Sandbox (nur innerhalb `--dir`, kein `..`-Ausbruch, kein Löschen). Schreiben nur mit `--write` (sonst Trockenlauf mit Vorschau). Aufruf: `python lmagent.py "<Aufgabe>" --dir . --model qwen3.8-27b --write`.

**Websuche:** `websearch.py` — keyless (DuckDuckGo HTML **POST**-Endpoint), ohne Extra-Pakete. `search(query)` liefert Titel/URL/Snippet, `fetch(url)` holt Seitentext mit SSRF-Schutz (blockt localhost/private IPs, nur http/https). Standalone: `python websearch.py "begriff"` / `--fetch <url>`.

**Team-Agenten** (in `lmstudio_agents.json`) sind arbeitsorientiert: Rechercheur, Coder, Pruefer, Texter (vorher Optimist/Skeptiker/Pragmatiker).

**Wichtige Fakten:**
- Chats liegen als `.conversation.json` in `~/.lmstudio/conversations`. Assistant-Nachrichten brauchen im Schema zwingend `shouldIncludeInContext` (bool) im Step sowie `fromDraftModel`/`tokensCount`/`isStructural` im Text-Content — sonst „invalid_type / Required"-Ladefehler in LM Studio. `make_assistant_msg` erzeugt das korrekt; `repair` rüstet alte Dateien nach.
- LM Studio liest den Chat-Ordner **nur beim Start/Refresh** neu ein, nicht live — neue Chats erscheinen erst nach Neustart der App.
- Modelle: `gemma-4-e4b` (schnell), `qwen3.8-27b-obliterated` (stärker), plus ein nomic-embed (wird bei Modellauswahl übersprungen). Server-Start via `~/.lmstudio/bin/lms.exe server start`.
