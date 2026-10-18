# DayZ Player Detector

Ein Bilderkennungs-Tool, das Spieler auf **aufgezeichnetem** DayZ-Bild- und
Videomaterial erkennt (Screenshots, Highlight-Clips, Stream-VODs). Basiert auf
YOLOv8 (Ultralytics), vortrainiert auf COCO ("person"-Klasse).

> **Wichtiger Hinweis:** Dieses Tool ist für die nachträgliche Analyse von
> Aufnahmen gedacht - z.B. für Content-Erstellung, Highlight-Reels, Statistiken
> oder als ML-Lernprojekt. Es ist bewusst **nicht** für ein Live-Overlay
> während einer laufenden Multiplayer-Runde gebaut. Ein Echtzeit-Screen-Reader,
> der dir während des Spielens anzeigt, wo Gegner stecken, wäre ein
> ESP-/Wallhack-Cheat, verstößt gegen die DayZ-Nutzungsbedingungen
> (BattlEye-Anticheat) und kann zu einem permanenten Bann führen.

## Was es kann

- Erkennt Personen/Spieler in Einzelbildern, ganzen Bildordnern und Videos
- Zeichnet Bounding Boxes + Konfidenzwert um jeden erkannten Spieler
- Zählt die Anzahl gleichzeitig sichtbarer Spieler pro Bild/Frame
- Optional: gruppiert erkannte Spieler grob nach Kleidungsfarbe (`--cluster-groups`),
  z.B. um Squads in einem Clip visuell zu unterscheiden - rein analytisch,
  nicht in Echtzeit
- Kann später mit eigenen, gelabelten DayZ-Screenshots nachtrainiert werden,
  um die Erkennung in typischen DayZ-Szenen (Wald, Dämmerung, Tarnkleidung)
  zu verbessern, oder um Spieler von Zombies/NPCs zu unterscheiden

## Installation

```bash
pip install -r requirements.txt
```

Python 3.9+ wird empfohlen. Der erste Aufruf lädt automatisch die
vortrainierten YOLOv8-Gewichte (`yolov8n.pt`, ~6 MB) herunter.

## Nutzung

```bash
# Einzelnes Bild
python detect.py --source samples/screenshot.jpg

# Ganzer Ordner mit Screenshots
python detect.py --source samples/

# Aufgezeichnetes Video (z.B. exportierter Highlight-Clip)
python detect.py --source samples/clip.mp4

# Empfindlicher/strenger einstellen (Standard: 0.35)
python detect.py --source samples/clip.mp4 --conf 0.25

# Spieler grob nach Kleidungsfarbe in 2 Gruppen clustern
python detect.py --source samples/clip.mp4 --cluster-groups 2

# Mit eigenem, nachtrainiertem Modell
python detect.py --source samples/clip.mp4 --weights runs/detect/train/weights/best.pt
```

Ergebnisse landen im Ordner `output/` (annotierte Bilder bzw. Videos).

Im `samples/`-Ordner liegen zwei Beispielbilder (`bus.jpg`, `zidane.jpg`), mit
denen du die Pipeline direkt testen kannst, bevor du eigenes DayZ-Material
reinlegst.

## Genauigkeit einschätzen

Das mitgelieferte Modell (`yolov8n.pt`) ist auf echten Fotos von Menschen
trainiert, nicht speziell auf DayZ. Da DayZ-Charaktere wie normale Personen
aussehen, funktioniert die Erkennung oft schon gut - aber:

- In dichtem Wald, bei Dämmerung/Nacht oder bei Tarnkleidung sinkt die
  Trefferquote
- Zombies/Infizierte können gelegentlich fälschlich als Spieler erkannt werden
- Größere Modelle (`--weights yolov8s.pt` oder `yolov8m.pt`) sind genauer,
  aber langsamer - beim ersten Einsatz automatisch heruntergeladen

## Modell mit eigenen DayZ-Daten nachtrainieren (optional)

Wenn dir die Standard-Genauigkeit nicht reicht, kannst du das Modell mit
eigenen, gelabelten DayZ-Screenshots feintunen. Drei Wege, an Trainingsbilder
zu kommen - auch kombinierbar:

### A) Screenshots automatisch sammeln, während du spielst

`dataset_recorder.py` macht in festen Abständen (und per Hotkey auf Wunsch
sofort) einen Screenshot deines Bildschirms und speichert ihn still im
Hintergrund - **ohne dir währenddessen irgendetwas anzuzeigen oder ins Spiel
einzugreifen.** Es ist ein reines Aufnahme-Tool, kein Overlay.

```bash
# Alle 4 Sekunden ein Bild, F8 = Sofort-Screenshot, F9 = Beenden
python dataset_recorder.py --interval 4 --out captures --hotkey f8 --quit-key f9

# Optional: direkt mit dem aktuellen Modell vorlabeln (Vorschläge, die du
# danach nur noch kontrollieren/korrigieren musst, statt bei null anzufangen)
python dataset_recorder.py --interval 4 --out captures --auto-label --weights yolov8n.pt
```

Nahezu identische Frames (z.B. wenn du gerade stillstehst) werden automatisch
übersprungen (`--dedupe-threshold`), damit der Datensatz nicht mit
Duplikaten vollläuft. Am Ende landen die Bilder in `captures/`.

### A2) Erkennung laufen lassen & nach Konfidenz sortieren (review.py)

`review.py` lässt die Erkennung über alle Bilder in `captures/` laufen und
sortiert sie in zwei Listen:

- **gut** - Modell war sich sehr sicher (hohe Konfidenz)
- **schlecht** - Modell war sich unsicher oder hat gar nichts erkannt (das
  sind genau die Fälle, die fürs nächste Training am wertvollsten sind)

Daraus entsteht eine anklickbare HTML-Übersicht:

```bash
# Einmaliger Durchlauf über alles, was bisher in captures/ liegt
python review.py --source captures --weights yolov8n.pt

# Oder dauerhaft laufen lassen, während du weiterspielst/sammelst -
# neue Bilder werden automatisch verarbeitet, sobald sie auftauchen
python review.py --source captures --watch
```

Danach `review/gallery.html` im Browser öffnen - oben die "schlechten" Fälle
zum Drüberschauen, unten die "guten" zur Bestätigung. Nebenbei schreibt das
Skript für jedes Bild automatisch eine YOLO-Label-Datei direkt neben das
Original in `captures/` (Vorschlag, bei Bedarf in LabelImg/CVAT korrigierbar).

Schau dir die Galerie an und lösche in `captures/` die Bild+Label-Paare, die
offensichtlicher Müll sind. Alles, was danach noch übrig ist, geht im
nächsten Schritt vollständig ins Training (siehe unten).

### B) Fertige DayZ-Datensätze von Roboflow Universe importieren

Falls du auf [Roboflow Universe](https://universe.roboflow.com) einen
passenden DayZ-Datensatz gefunden hast: Account anlegen, Datensatz öffnen,
"Download Dataset" → Format "YOLOv8" → zip herunterladen und entpacken.

`prepare_dataset.py` übernimmt daraus **nur die Spieler-Klasse** - andere
Klassen wie "Enemy", "Chest" oder "Zmb" (falls vorhanden) werden bewusst
verworfen, siehe Kommentar im Skript:

```bash
python prepare_dataset.py \
    --export ~/Downloads/dayzv2 --export ~/Downloads/enmy \
    --keep-classes player people players
```

Das Skript matcht Klassennamen case-insensitive per Teilstring, kopiert nur
Bilder mit mindestens einer passenden Box, remapped sie auf Klasse 0
("player") und sortiert sie automatisch in `dataset/images/{train,val}` und
`dataset/labels/{train,val}` ein.

### C) Manuell labeln

Screenshots aus eigenen Aufnahmen extrahieren (z.B. mit
`ffmpeg -i clip.mp4 -vf fps=1 dataset/images/train/frame_%04d.jpg`) und mit
[LabelImg](https://github.com/heartexlabs/labelImg) oder [CVAT](https://www.cvat.ai/)
labeln, als "YOLO"-Format exportieren, dann wie in A/B nach `dataset/` einsortieren.

### Alles ins Training übernehmen & Training starten

Wenn Weg A genutzt wurde (Screenshots + review.py), übernimmt
`finalize_dataset.py` als letzter Schritt ALLE verbliebenen, gelabelten
Bilder aus `captures/` nach `dataset/` (Train/Val-Split automatisch):

```bash
python finalize_dataset.py --source captures --val-split 0.15
```

Das Skript ist idempotent - schon übernommene Bilder werden bei erneutem
Aufruf nicht doppelt kopiert, du kannst es also nach jeder weiteren
Sammel-Session einfach wieder laufen lassen.

Sobald genug Bilder in `dataset/images/{train,val}` und
`dataset/labels/{train,val}` liegen (Faustregel: mindestens ein paar hundert
für spürbare Verbesserung):

```bash
python train.py --epochs 50
```

Die trainierten Gewichte liegen danach unter
`runs/detect/train/weights/best.pt` und können mit `--weights` in
`detect.py` verwendet werden.

Die Klassen-Konfiguration steht in `dataset.yaml` - dort kannst du auch
weitere Klassen ergänzen (z.B. `1: zombie`), wenn du Spieler von Infizierten
unterscheiden willst.

## Projektstruktur

```
dayz-player-detector/
├── detect.py            Haupt-Skript: Erkennung auf Bild/Video
├── dataset_recorder.py  Sammelt automatisch Screenshots während des Spielens (kein Overlay)
├── review.py            Lässt Erkennung laufen, sortiert Bilder nach Konfidenz in gut/schlecht (HTML-Galerie)
├── finalize_dataset.py  Übernimmt alle gelabelten Bilder aus captures/ final ins Trainingsset
├── prepare_dataset.py   Importiert Roboflow-Exporte, filtert auf Spieler-Klasse
├── train.py             Fine-Tuning-Skript für eigene Daten
├── dataset.yaml         Datensatz-Konfiguration für train.py
├── requirements.txt
├── samples/             Beispielbilder zum Testen
├── captures/            Rohe Screenshots von dataset_recorder.py landen hier
├── review/              Von review.py erzeugt: gallery.html, Thumbnails, manifest.json
├── dataset/             Kuratierte Trainingsdaten (nach Review/Filtern)
│   ├── images/{train,val}
│   └── labels/{train,val}
└── output/              Annotierte Ergebnisse von detect.py landen hier
```
