---
name: typesafe-skill
description: TypeSafe-Plugin (typesafe@typesafe-ai) installiert; bei Arbeit in diesem Projekt den TypeSafe-Skill nutzen
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 741a9993-f7c8-47e3-bed7-1b83afe0566c
  modified: 2026-09-19T18:08:14.701Z
---

User will, dass bei der Arbeit in C:\Users\reiss\Documents\claude der TypeSafe-Skill verwendet wird. Plugin `typesafe@typesafe-ai` v0.5.7 ist user-scope installiert (2026-09-19).

**Why:** ausdrücklicher Wunsch des Users.
**How to apply:** Bei KI-/LLM-Features (Routing, Ranking, Klassifikation, Verifikation) zuerst den TypeSafe-Skill laden und dessen Muster (Choice/Noul/Score, typisierte Urteile statt generiertem Text) anwenden. `claude` liegt nicht im PATH → `$env:USERPROFILE\.local\bin\claude.exe` benutzen.
