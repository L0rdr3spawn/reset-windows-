---
description: Schreibt den Arbeitsstand kompakt in eine Datei, damit du mit /clear frisch (und günstig) weitermachen kannst
argument-hint: "[optionaler Fokus für den nächsten Schritt]"
allowed-tools: Write, Bash(git status:*), Bash(git diff --stat:*)
---

Erstelle einen Checkpoint des aktuellen Arbeitsstands in `.claude/checkpoint.md` (überschreiben, falls vorhanden).

Inhalt, maximal ~40 Zeilen, nur Fakten:
- **Ziel** – was der Nutzer insgesamt will (1–2 Sätze)
- **Erledigt** – Stichpunkte, mit geänderten Dateien
- **Stand / offene Probleme** – inkl. relevanter Fehlermeldungen (gekürzt)
- **Nächste Schritte** – konkret und geordnet
- **Wichtiger Kontext** – Entscheidungen, Constraints, relevante `pfad:zeile`-Stellen

Fokus für den nächsten Schritt: $ARGUMENTS

Antworte danach nur mit einer Zeile:
`Checkpoint gespeichert. Jetzt /clear ausführen und dann: "Lies .claude/checkpoint.md und mach weiter."`
