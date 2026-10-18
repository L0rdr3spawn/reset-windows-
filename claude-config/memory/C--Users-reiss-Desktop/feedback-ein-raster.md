---
name: feedback-ein-raster
description: Every day×lesson grid in the Schulmanager must reuse the timetable grid (TimetableGrid) – never build a new grid type
metadata:
  node_type: memory
  type: feedback
  originSessionId: da397a22-9891-46f3-a3ae-94186b69fe15
  modified: 2026-10-13T15:38:23.643Z
---

Any view laid out as days × lessons (attendance per lesson, availability/blocked times, supervision duties, Klassenbuch week, statistics heatmaps …) must use the one shared timetable grid (`frontend/src/components/TimetableGrid.tsx` + its styles) with custom cell content per use case – not its own table/grid CSS.

**Why:** 2026-10-13 the user got annoyed that the attendance-per-lesson view used yet another new grid type although they had already said to always use the timetable grid; they asked for it as a reusable "stylesheet-like" building block used everywhere.
**How to apply:** In every agent prompt that touches a day×lesson view, require the shared grid component; check new code for hand-made grids. Related: [[schulmanager-nachrichten]].
