# Geofinder — Bildausschnitt → mehrere Geo-KIs → Karte → Rangliste

## Context

Gewünscht ist ein Werkzeug, das per Taste einen **Bildausschnitt** aufnimmt, **mehrere unterschiedliche
Bild-KIs parallel** schätzen lässt, wo auf der Welt das Bild entstanden ist, und die Kandidaten samt
Wahrscheinlichkeiten **auf einer Karte** zeigt. Danach trägt der User den echten Ort ein; daraus wird
berechnet, **welches Modell wie gut war**, und beim nächsten Mal steht die Bilanz (besser/schlechter,
Rang, Trend) direkt neben jedem Modell. Das Programm bekommt nur Bilddateien, es greift auf keine
Webseite/kein Spiel zu.

Neu, eigenständig, unter `C:\Users\reiss\Documents\claude\geofinder\`. Im Repo gibt es noch nichts
Vergleichbares (kein Screenshot-/Hotkey-Code außer in `jev-assistent`).

Rahmen des Rechners (geprüft): Python 3.12.10, RTX 5070 (GPU 0, 12 GB) + RTX 3050 (GPU 1, 8 GB, frei),
LM Studio mit `google/gemma-4-e4b`, kein Compiler/Conda/WSL → nur fertige Wheels, torch **cu128**
(wie in `flybrain/.venv`).

## Modelle (5 verschiedene Ansätze = echte Gegenprüfung)

| Modell | Ansatz | Ausgabe |
|---|---|---|
| **GeoCLIP** (`pip geoclip`) | Bild↔GPS-Retrieval | Top-10 Koordinaten + Wahrscheinlichkeit |
| **StreetCLIP** (`geolocal/StreetCLIP`, transformers) | Zero-Shot, 2 Stufen: Land → Städte der Top-5-Länder | Stadt-Koordinaten, p = p(Land)·p(Stadt) |
| **PLONK** (`pip diff-plonk`, `nicolas-dufour/PLONK_YFCC`) | Diffusion, 64 Stichproben | Punktwolke → Cluster mit Anteil |
| **Gemma-Vision** über LM Studio | VLM liest Schilder/Sprache/Vegetation | JSON: Top-3 Orte + Sicherheit + Begründung |
| **Claude** über `claude -p --model sonnet` (Abo, wie in `jev-assistent/claude.py`) | VLM | wie Gemma; in `config.json` abschaltbar |

- Die drei Torch-Modelle laufen in fp16 auf **GPU 1 (3050)**, damit die 5070 frei bleibt (≈3–4 GB,
  passt neben Whisper). `gpu` in `config.json`, Rückfall auf CPU.
- Jedes Modell ist ein Adapter mit gleicher Schnittstelle (`laden()`, `schaetzen(bild) -> [Kandidat(lat, lon, p, label, notiz)]`).
  Fällt eines aus (LM Studio aus, Paket lädt nicht), läuft der Rest weiter und die Karte zeigt „nicht verfügbar“.
- Beim Bauen zuerst prüfen: hat `gemma-4-e4b` Vision (`/api/v0/models`)? Läuft `diff-plonk` unter Windows?
  Wenn PLONK nicht installierbar ist → durch OSV-5M-Baseline ersetzen oder weglassen, im Bericht nennen.

## Ablauf

1. **Hotkey** (Standard `Strg+Alt+G`, in `config.json` änderbar) über `RegisterHotKey` (ctypes) —
   kein Tastatur-Hook, also unkritisch neben Spielen/Anti-Cheat.
2. **Ausschnitt**: `snip.py` friert den Bildschirm ein (`mss`, alle Monitore, DPI-aware), zeigt ihn
   abgedunkelt in einem randlosen tkinter-Fenster, Rechteck ziehen, `Esc` bricht ab. Bild → `daten/bilder/<id>.png`.
3. **Parallel schätzen**: `ThreadPoolExecutor`, jedes Ergebnis wird sofort in den Rundenzustand geschrieben.
4. **Karte**: lokaler Server (`http.server`, nur 127.0.0.1) + Leaflet (lokal mitgeliefert, OSM-Kacheln).
   Fenster über `brave --app=http://127.0.0.1:8777/` (Rückfall `webbrowser`). Seite pollt und zeigt Modelle,
   sobald sie fertig sind:
   - je Modell eine Farbe, Marker-Deckkraft/-Größe = Wahrscheinlichkeit, PLONK zusätzlich als Punktwolke
   - **Konsens**-Marker + Unsicherheitskreis + „3 von 5 Modellen innerhalb 300 km“
   - Seitenleiste: Top-Tipp je Modell (nächste Stadt/Land), p, Begründung der VLMs, **bisherige Bilanz** (Ø km, Rang, Trend ↑/↓)
5. **Auflösen**: Knopf „Wo war es wirklich?“ → Klick auf die Karte → pro Modell Distanz, Punkte, Land getroffen.
   Anzeige „diesmal Rang 1: GeoCLIP (84 km), besser als sein Schnitt (310 km)“.

## Konsens und Bewertung

- `ensemble.py`: Haversine, gieriges Clustern aller Kandidaten (Radius 300 km), Gewicht = Modellgewicht × p;
  Konsens = schwerster Cluster, Position = gewichtetes Mittel auf der Kugel. Das Ensemble wird selbst als
  „Modell“ mitbewertet (schlägt es die Einzelnen?).
- `bewertung.py`: SQLite `daten/geofinder.db` (`runden`, `schaetzungen`, `wahrheit`). Je Modell: Distanz Top-1,
  beste Distanz in Top-k, Punkte `5000·exp(−km/1492.7)`, Land richtig.
  Rangliste: n, Median-km, Ø Punkte, Länderquote, **Trend** (letzte 10 vs. davor).
- **Lernen**: Modellgewicht fürs Ensemble = geglätteter Punkteschnitt `(n·Ø + 5·2500)/(n+5)/5000` —
  neue Modelle starten neutral, gute zählen mit der Zeit mehr.
- `orte.py`: `geonamescache` (offline) für Städte je Land (StreetCLIP-Stufe 2), nächste Stadt als Label, Ländervergleich.

## Dateien (alle neu, `geofinder/`)

`geofinder.py` (Start: Dienst mit Hotkey+Server; `--bild <pfad>` ohne Hotkey; Einzelinstanz per Mutex
`Local\Geofinder`) · `hotkey.py` · `snip.py` · `modelle/{geoclip_m,streetclip_m,plonk_m,vlm_lmstudio,claude_cli}.py` ·
`ensemble.py` · `bewertung.py` · `orte.py` · `web/{index.html,app.js,style.css,leaflet/}` · `config.json` ·
`requirements.txt` · `einrichten.ps1` (venv, torch cu128, Pakete, Gewichte vorladen) ·
`Geofinder starten.cmd` / `Geofinder stoppen.cmd` · `tests.py` · `LIESMICH.md`

Wiederverwendet: `lmstudio.py:187-232` (`api_post`, `server_running`, `BASE_URL`, per `sys.path` wie es
`jev-assistent` mit `voice-browser` macht); Claude-Aufrufmuster aus `C:\Users\reiss\jev-assistent\claude.py`
(`CREATE_NO_WINDOW`, `MAX_THINKING_TOKENS=0`, hier mit `--allowedTools Read` fürs Bild).
Einzige Änderung außerhalb: `.gitignore` um `geofinder/.venv/` und `geofinder/daten/` ergänzen.

## Downloads, die die Einrichtung auslöst

torch cu128 (~3 GB, PyPI/pytorch.org) · `geoclip`, `transformers`, `diff-plonk`, `mss`, `pillow`, `geonamescache` (PyPI) ·
Gewichte von Hugging Face: GeoCLIP + CLIP ViT-L/14 (~1,8 GB), StreetCLIP (~1,7 GB), PLONK_YFCC + DINOv2-L (~1,5 GB) ·
Leaflet 1.9 (150 KB) · 3–4 Testfotos mit bekanntem Ort von Wikimedia Commons. Zusammen ≈ 8–9 GB.

## Verifikation

1. `python tests.py` — Haversine, Clustern, Punkteformel, Gewichte, Trend (offline, ohne Modelle).
2. `python geofinder.py --bild testbilder\<ort>.jpg` für jedes Testfoto: jedes Modell liefert Kandidaten,
   Distanz zum bekannten Ort wird ausgegeben; Laufzeit + VRAM auf GPU 1 notieren.
3. Dienst starten, Karte im eingebauten Browser auf `127.0.0.1:8777` öffnen: Marker, Konsens, Seitenleiste;
   echten Ort klicken → Rangliste; zweite Runde → Bilanz/Trend erscheinen neben den Modellen.
4. Ausschnitt-Overlay über einen Test-Endpunkt `/api/snip` auslösen (keine simulierten Tastendrücke, solange
   der User am PC ist); den echten Hotkey probiert der User selbst.
5. Ausfalltest: LM Studio gestoppt → übrige Modelle + Konsens funktionieren weiter.

Autostart wird nicht eingerichtet (kann später über eine Verknüpfung wie bei Jeff dazukommen).
