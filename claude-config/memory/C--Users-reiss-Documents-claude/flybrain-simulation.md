---
name: flybrain-simulation
description: "Fliegenhirn-Simulation (FlyWire-Konnektom, LIF) unter flybrain/ — läuft nativ unter Windows mit PyTorch cu128 auf der RTX 5070"
metadata: 
  node_type: memory
  type: project
  originSessionId: 009b3fbd-3f7e-4d0a-981f-a65b6c59ef62
  modified: 2026-09-19T13:44:15.100Z
---

Aufgebaut am 2026-09-19 in `C:\Users\reiss\Documents\claude\flybrain\`: Repo eonsystemspbc/fly-brain (FlyWire v783, ~139k Neuronen), eigene `.venv` (Python 3.12, torch cu128), `run.ps1` (Simulation + Auswertung), `analyze.py` (Feuerraten + Zelltypen aus `neuron_annotations.tsv` von flyconnectome/flywire_annotations).

**Why:** Kein WSL, kein Conda und kein C++-Compiler auf dem Rechner → nur das PyTorch-Backend funktioniert. Brian2-Standalone, GeNN und NEST GPU laufen nicht. Die RTX 5070 (sm_120) braucht einen cu128-Build, cu126 aus environment.yml reicht nicht.

Sehen (2026-09-19): `brain.py` (schrittweises FlyBrain mit Zustand), `eyes.py`, `vision_test.py`. Photorezeptoren direkt reizen geht nicht: Das LIF-Modell ruht bei 0 und kann die doppelte Hemmung der Lamina (L1 hemmt Mi1) nicht abbilden. Deshalb wird das Bild in die ON-Zellen (Mi1/Tm3) und OFF-Zellen (Tm1/2/4/9) eingespeist, die Blickrichtung kommt über die Verschaltung R1-6 → L → Medulla. Ergebnis: Dunkelheit auf einer Seite aktiviert die Flucht-DNs dieser Seite (LC4, DNp02/04/11). Looming und bloßes Verdunkeln lassen sich aber nicht unterscheiden, und T4/T5 erkennen keine Bewegungsrichtung.

**How to apply:** Neue Experimente = Liste von FlyWire-IDs in `EXPERIMENTS` in `fly-brain/code/benchmark.py`. Die Ausgabe-Datei heißt nur `pytorch_t{sek}s_n{trials}.parquet`, der Experimentname kommt nicht vor, gleiche Einstellungen überschreiben also die alte Datei. Das neuere Male-CNS-Konnektom (Google/Janelia, Sept. 2026) liegt bei janelia.org/project-team/flyem/male-cns-connectome und ist hier noch nicht eingebunden.
