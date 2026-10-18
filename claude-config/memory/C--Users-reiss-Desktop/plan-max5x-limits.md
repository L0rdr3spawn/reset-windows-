---
name: plan-max5x-limits
description: "User hat den Max-5x-Plan (get_usage zeigt fälschlich \"Pro\"); 15 parallele Sonnet-Schreiber haben das 5-h-Fenster geleert – Agenten in Wellen starten"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6b3b3b78-3724-4c16-8183-7144a0471201
  modified: 2026-10-18T14:10:15.604Z
---

Der Nutzer hat den **Max-5x-Plan**, auch wenn `mcp__ccd_session_mgmt__get_usage` "Pro" meldet. Die Prozentwerte (5-h-Fenster, Wochenlimit) gelten trotzdem.

**Why:** Am 2026-10-18 haben 15 gleichzeitige Sonnet-Schreiber (Neubau-Paket Schulpuls) das 5-h-Fenster innerhalb von ~10 Minuten geleert (HTTP 429, alle Agenten abgebrochen); Wochenlimit stand danach bei 78 %. Abgebrochene Agenten lassen sich mit SendMessage fortsetzen, ihre Teildateien bleiben erhalten.

**Nie abgebrochene Agenten mit SendMessage fortsetzen, wenn ihr Verlauf groß ist:** das lädt den kompletten Agenten-Kontext neu (bei den Schreibern ~520.000 Token je Agent) – der Nutzer hat das am 2026-10-18 ausdrücklich bemängelt ("so unglaublich unnötig"). Stattdessen frische Agenten mit engem Auftrag (nur die fehlenden Abschnitte, nur die dafür nötigen Quellen) starten; Teildateien bleiben erhalten, der neue Agent hängt an.

**How to apply:** Große Agenten-Schwärme (Sonnet, lange Lesequellen) in Wellen von 3–5 starten, vor der nächsten Welle `get_usage` prüfen und den Verbrauch pro Agent schätzen. Agenten Dateien in Teilen speichern lassen (anhängen, Marker), damit ein Limit-Abbruch nichts kostet. Siehe [[feedback-kein-fable]] für die Modellwahl.
