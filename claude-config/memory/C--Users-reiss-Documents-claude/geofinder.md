---
name: geofinder
description: "Geofinder unter Documents\\claude\\geofinder — Bildausschnitt per Taste, 5 Geo-KIs parallel, Karte, Rangliste; Fallen beim Betrieb"
metadata:
  node_type: memory
  type: project
  originSessionId: 270e80b2-e183-4a8f-947f-205972f0ca07
  modified: 2026-10-01T15:48:51.745Z
---

`C:\Users\reiss\Documents\claude\geofinder\` (gebaut 2026-10-01, liegt außerhalb des Git-Repos, da `.gitignore` nur MC-Ordner freigibt).
Dienst `geofinder.py` (pythonw, Mutex `Local\Geofinder`, Karte auf `http://127.0.0.1:8777`), Start/Stopp über die zwei .cmd,
Doku in `LIESMICH.md`. Umschalt+Alt+G = neue Runde (Overlay, Bereich wird in `datenereich.json` gemerkt), Umschalt+Alt+H = weiteres Bild: nimmt sofort denselben Bereich auf, ohne Ziehen (seit 2026-10-04; vorher fror das Overlay das Geofinder-Fenster mit ein → User: „Knopf/Taste gehen nicht“). Knopf klappt das Geofinder-Fenster dafür kurz weg.
Modelle: GeoCLIP, StreetCLIP, PLONK (eigene `.venv`, torch cu128, GPU 1 = RTX 3050, zusammen ~2,3 GB), Gemma über LM Studio,
Claude über `claude -p` (Abo). Konsens = dichtester Haufen, Lage als gewichteter geometrischer Median (User wollte ausdrücklich
kein ausreißeranfälliges Mittel).

**Why / How to apply:**
- Gemma fällt mit „LM Studio läuft nicht“ aus, wenn nach einem PC-Neustart der Server aus ist → `~\.lmstudio\bin\lms.exe server start`.
- `web\index.html` nie als Datei öffnen (file://-Vorschau): ohne Dienst reagiert kein Knopf — das hielt der User für „Buttons gehen nicht“.
- CARTO-Kacheln verlangen inzwischen einen API-Schlüssel; die Karte nutzt Esri + OSM.
- `geolocal/StreetCLIP` nur aus dem lokalen Snapshot laden: transformers zieht sonst bei jedem Laden 1,7 GB safetensors nach und hängt.
- Torch/transformers nie gleichzeitig aus mehreren Threads erstmals importieren (`modelle\_torch_gemeinsam.py` hat dafür eine Sperre).
- Nach Änderungen an Python-Dateien Dienst neu starten; `web\` wird ohne Neustart frisch ausgeliefert.
- Der User testet sofort mit, während noch gebaut wird — Zwischenstände lauffähig halten und sagen, was noch fehlt. Siehe [[jev-plugins]] (wenig Rückfragen).
- Genauigkeit (Stand 2026-10-04, 5 aufgelöste Runden): Claude Median ~5 km, Rest 150–2000 km. Deshalb Claude = Opus mit
  Denken, alle Bilder der Runde gemeinsam (`mehrbild`), Torch-Tipps als schwache Hinweise (`mit_hinweisen`), Grundgewicht
  3 in config; Gewicht = prior × (geglättete Punkte/2500)². Gemma Gewicht 0,25 (liegt meist 500–2000 km daneben).
- Stand 2026-10-04 abends: Tasten auf Wunsch Strg+Alt+F (neu) / Strg+Alt+G (weiteres Bild, wieder MIT Rahmen – die
  Schnellaufnahme ohne Ziehen hat den User verwirrt, nur noch per `dazu_gleicher_bereich`). User will: jedes Bild von allen
  Modellen einzeln neu schätzen, dann über Wahrscheinlichkeiten zusammenrechnen (Claude daher nicht mehr „alle Bilder
  gemeinsam“, sondern 3 Versuche je Bild, parallel). Bild entfernen (×) und Modell-Fokus per Klick auf den Namen gibt es.
