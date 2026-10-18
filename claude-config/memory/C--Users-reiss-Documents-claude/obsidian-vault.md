---
name: obsidian-vault
description: Obsidian-Vault unter Documents\Obsidian Vault; Memory-Ordner + Projekt-Doku sind per Junction/Hardlink eingehängt
metadata:
  node_type: memory
  type: project
  originSessionId: 368865d4-abbb-4ff4-8d64-c0eb74ff8ba5
  modified: 2026-10-01T14:47:30.307Z
---

Vault: `C:\Users\reiss\Documents\Obsidian Vault` (seit 2026-10-01). Der User kennt Obsidian nicht – einfach erklären.

- `Claude-Wissen\` = Junction auf diesen Memory-Ordner (live, keine Kopie). Dateien, die der User in Obsidian ändert oder löscht, sind also die echten Memory-Dateien.
- `Projekte\` = Hardlinks auf eigene Doku aus `Documents\claude` (READMEs, voice-browser; DayZ-Doku seit 2026-10-04 bewusst entfernt), `Projekte\Crew-Reports` = Junction auf `crew_reports\`.
- `Start.md` = Einstiegsseite mit Kurzanleitung und thematisch gruppierten Links. Ist statisch: bei neuen Memories dort einen Link ergänzen (MEMORY.md bleibt der vollständige Index).
- Einrichten/Reparieren: `obsidian-verbinden.ps1` im Repo (idempotent). Neue Doku-Datei → dort in `$dateien` eintragen und Skript laufen lassen.

**Why:** Symlinks gehen ohne Adminrechte/Entwicklermodus nicht; das ganze Repo einzuhängen würde `node_modules` (1400+ .md) in den Vault ziehen.

**How to apply:** `[[slug]]`-Links in Memories müssen dem Dateinamen entsprechen, sonst löst Obsidian sie nicht auf. Hardlinks reißen bei `git checkout`/Ersetzen der Datei → Skript erneut ausführen. Notizen für den User direkt in den Vault schreiben (außerhalb von `Claude-Wissen`).
