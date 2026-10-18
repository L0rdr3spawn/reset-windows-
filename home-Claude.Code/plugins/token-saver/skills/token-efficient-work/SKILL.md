---
name: token-efficient-work
description: Techniken, um mit möglichst wenig Tokens zu arbeiten. Use when working in a large codebase, when the context is getting large, when a task requires reading many files or long logs/test output, or when the user asks to save tokens / reduce cost.
---

# Token-effizient arbeiten

## Lesen
- Erst finden, dann lesen: `Grep` (mit `output_mode: "files_with_matches"` oder `-n` + `head_limit`) → dann `Read` mit `offset`/`limit` um die Fundstelle (±40 Zeilen).
- Dateien, die schon im Kontext sind oder die du gerade bearbeitet hast, nicht erneut lesen.
- Lockfiles, Build-Output, minifizierte Dateien und `node_modules` nie komplett lesen.

## Befehle
- Ausgabe begrenzen: `| tail -n 50`, `| head -n 50`, `--oneline -n 20`, `-q`/`--silent`.
- Tests: nur betroffene Tests laufen lassen; bei Fehlern `2>&1 | tail -n 80` oder nur die fehlgeschlagenen (`pytest -x -q`, `--reporter=dot`).
- Lange Ausgaben in eine Datei umleiten (`> /tmp/out.log`) und gezielt greppen.

## Delegieren
- Breite Recherchen („wo wird X überall benutzt?“) an den Agenten `token-saver:scout` geben – nur dessen Zusammenfassung landet im Kontext.
- Mehrere unabhängige Tool-Aufrufe in einer Antwort parallel stellen.

## Antworten
- Kein Wiederholen der Frage, keine Zusammenfassung von unverändertem Code.
- Änderungen als gezielte Edits, nicht als komplette Dateien ausgeben.
- Kurze Statusmeldungen statt Erzählung jedes Schritts.

## Kontext pflegen
- Bei großem Kontext: `/token-saver:checkpoint`, dann `/clear`.
- Alternativ `/compact <Fokus>` mit klarem Fokus.
- `/token-saver:usage` zeigt, welche Tool-Ergebnisse am meisten Tokens kosten.
