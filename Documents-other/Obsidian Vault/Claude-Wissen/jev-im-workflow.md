---
name: jev-im-workflow
description: Jev aktiv in meinen eigenen Arbeitsablauf einbauen – jev.py route/check/choice/noul/score vor Delegieren, Nachfragen und Verifizieren
metadata:
  type: feedback
---

Der User will (2026-09-19), dass ich Jev (TypeSafe System One) aktiv in meinem eigenen Workflow nutze, nicht nur in seinen Projekten. Werkzeug: `C:\Users\reiss\Documents\claude\jev.py` (nur Standardbibliothek, Key aus Env/HKCU/cs2-jev/.env, ~1 s pro Anfrage).

**Why:** ausdrücklicher Wunsch; Jev liefert schnelle, typisierte Urteile mit Wahrscheinlichkeiten und ergänzt [[delegate-small-tasks-to-local-llm]] und [[typesafe-skill]].

**How to apply:**
- Vor dem Auslagern kleiner Aufgaben: `python jev.py route "<aufgabe>"` → LOKAL (dann [[lmstudio-tool]] `gen`), SELBST oder RUECKFRAGE. Policy steckt im Code (lokal nur wenn pruefbar ≥ 0.6 und riskant < 0.4).
- Bei unsicheren/folgenreichen Schritten (Löschen, Überschreiben, Außenwirkung): `route` zeigt RUECKFRAGE → User fragen.
- Zum Gegenprüfen von Aussagen gegen Quellen/Logs: `python jev.py check "<behauptung>" --evidence <datei|->`.
- Ad-hoc-Urteile: `choice "<frage>" a b c --state …`, `noul`, `score "<frage>" stufe0 stufe1 …`; `--json` für rohe Antworten, `raw <req.json>` für eigene Fragen.
- **Entscheidungen abgeben (2026-09-22, Wunsch des Users zum Token-Sparen):** statt den User bei kleinen Fragen zu stören, `python jev.py decide "<frage>" opt1 opt2 --state "<kontext>"` → `JEV ENTSCHEIDET: x` (übernehmen, im Abschluss erwähnen), `NUTZER FRAGEN` (AskUserQuestion) oder `STOPP` (anhalten, User fragen).
- **Automatischer Wächter – AUS seit 2026-09-23** (User: zu viele Rückfragen; Backup `.claude/settings.jev-hook-aus-20260923.json.bak`, nur auf Wunsch wieder an). Früher: PreToolUse-Hook in `Documents/claude/.claude/settings.json` ruft `jev.py hook` für Bash/PowerShell/Write/Edit/AskUserQuestion. Gefährlich → deny (ich muss anhalten und fragen), unsicher → ask (User bekommt Rechte-Dialog), unwichtige AskUserQuestion → deny mit Jevs Antwort (dann damit weitermachen, nicht erneut fragen). Lese-Befehle und Edits im Projekt/Temp werden ohne Jev durchgelassen; bei Fehlern wird nie blockiert. Log: `jev_hook.log`. SSH zum Heimserver ([[home-server-debian-casaos]]) ist auf Wunsch (2026-09-22) vom Nachfragen ausgenommen, nur `stopp` greift dort noch. Build-/Cache-Artefakte löschen gilt als ok.
- Jev ersetzt nie meine eigene Prüfung; Ergebnis ist ein Signal, keine Erlaubnis. Nicht für Trivialitäten aufrufen, wo die Antwort offensichtlich ist.
