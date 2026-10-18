#!/usr/bin/env python3
"""
DayZ Player Detector
=====================

Erkennt Spieler (Personen) auf AUFGEZEICHNETEM Bild- und Videomaterial
(z.B. Highlight-Clips, Screenshots, Stream-VODs) mit einem YOLOv8-Modell.

WICHTIG: Dieses Tool ist für die nachträgliche Analyse von Aufnahmen gedacht
(Content-Erstellung, Highlights, Statistiken, ML-Lernprojekt) - NICHT für ein
Live-Overlay während einer laufenden Multiplayer-Runde. Sowas verstößt gegen
die Nutzungsbedingungen von DayZ (BattlEye-Anticheat) und wird hier bewusst
nicht unterstützt.

Nutzung:
    # Einzelbild
    python detect.py --source samples/screenshot.jpg

    # Ganzer Ordner mit Bildern
    python detect.py --source samples/

    # Aufgezeichnetes Video
    python detect.py --source samples/clip.mp4

    # Mit eigenem, nachtrainiertem Modell (siehe train.py)
    python detect.py --source samples/clip.mp4 --weights runs/detect/train/weights/best.pt

    # Optional: Spieler grob nach Kleidungsfarbe in Gruppen clustern
    # (rein analytisch, für Highlight-/Squad-Auswertung - kein Freund/Feind-Overlay)
    python detect.py --source samples/clip.mp4 --cluster-groups 2
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

COCO_PERSON_CLASS_ID = 0
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

GROUP_COLORS = [
    (60, 200, 60),   # Gruppe A - grün
    (60, 60, 220),   # Gruppe B - rot
    (220, 180, 40),  # Gruppe C - blau/gold
    (200, 60, 200),  # Gruppe D - magenta
]


def parse_args():
    p = argparse.ArgumentParser(description="DayZ Player Detector (offline, für aufgezeichnetes Material)")
    p.add_argument("--source", required=True, help="Bild, Ordner mit Bildern, oder Videodatei")
    p.add_argument("--weights", default="yolov8n.pt", help="YOLO-Gewichte (Standard: vortrainiertes COCO-Modell)")
    p.add_argument("--conf", type=float, default=0.35, help="Konfidenz-Schwelle (0-1)")
    p.add_argument("--output", default="output", help="Ausgabeordner")
    p.add_argument("--cluster-groups", type=int, default=0,
                   help="Wenn >0: Spieler anhand der Kleidungsfarbe in N Gruppen clustern (rein analytisch)")
    p.add_argument("--imgsz", type=int, default=640, help="Inferenz-Auflösung")
    return p.parse_args()


def dominant_color(bgr_crop: np.ndarray) -> np.ndarray:
    """Grober Mittelwert der Torso-Region als 'Kleidungsfarbe'."""
    h, w = bgr_crop.shape[:2]
    if h == 0 or w == 0:
        return np.array([0, 0, 0], dtype=np.float32)
    # Torso ~ mittleres Drittel der Box (vermeidet Kopf/Beine/Hintergrundrand)
    y0, y1 = int(h * 0.3), int(h * 0.7)
    x0, x1 = int(w * 0.2), int(w * 0.8)
    region = bgr_crop[y0:y1, x0:x1]
    if region.size == 0:
        region = bgr_crop
    return region.reshape(-1, 3).mean(axis=0)


def cluster_players(colors: list[np.ndarray], k: int) -> list[int]:
    """Sehr einfaches k-means Clustering der Kleidungsfarben -> Gruppen-IDs."""
    if len(colors) == 0:
        return []
    if len(colors) < k:
        k = max(1, len(colors))
    data = np.array(colors, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, labels, _ = cv2.kmeans(data, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)
    return labels.flatten().tolist()


def annotate_frame(frame: np.ndarray, model: YOLO, conf: float, imgsz: int, n_groups: int):
    results = model.predict(frame, conf=conf, imgsz=imgsz, classes=[COCO_PERSON_CLASS_ID], verbose=False)
    boxes = results[0].boxes
    n_players = 0 if boxes is None else len(boxes)

    crops, xyxys, confs = [], [], []
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            crops.append(frame[y1:y2, x1:x2])
            xyxys.append((x1, y1, x2, y2))
            confs.append(float(box.conf[0]))

    group_ids = [0] * len(crops)
    if n_groups and n_groups > 0 and len(crops) > 0:
        colors = [dominant_color(c) for c in crops]
        group_ids = cluster_players(colors, n_groups)

    out = frame.copy()
    for (x1, y1, x2, y2), confv, gid in zip(xyxys, confs, group_ids):
        color = GROUP_COLORS[gid % len(GROUP_COLORS)] if n_groups else (0, 220, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"Player {confv:.2f}" if not n_groups else f"Gruppe {chr(65 + gid % 26)} {confv:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(out, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    cv2.putText(out, f"Spieler erkannt: {n_players}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    return out, n_players


def process_image(path: Path, model, args, out_dir: Path):
    frame = cv2.imread(str(path))
    if frame is None:
        print(f"[WARN] Konnte Bild nicht lesen: {path}")
        return
    annotated, n = annotate_frame(frame, model, args.conf, args.imgsz, args.cluster_groups)
    out_path = out_dir / f"{path.stem}_annotated{path.suffix}"
    cv2.imwrite(str(out_path), annotated)
    print(f"[OK] {path.name}: {n} Spieler erkannt -> {out_path}")


def process_video(path: Path, model, args, out_dir: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"[ERROR] Konnte Video nicht öffnen: {path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path = out_dir / f"{path.stem}_annotated.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    frame_idx = 0
    max_players_seen = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        annotated, n = annotate_frame(frame, model, args.conf, args.imgsz, args.cluster_groups)
        max_players_seen = max(max_players_seen, n)
        writer.write(annotated)
        frame_idx += 1
        if frame_idx % 30 == 0:
            print(f"  ... Frame {frame_idx} verarbeitet")

    cap.release()
    writer.release()
    print(f"[OK] {path.name}: {frame_idx} Frames verarbeitet, max. {max_players_seen} Spieler gleichzeitig -> {out_path}")


def main():
    args = parse_args()
    src = Path(args.source)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Lade Modell: {args.weights}")
    model = YOLO(args.weights)

    if not src.exists():
        print(f"[ERROR] Quelle nicht gefunden: {src}")
        sys.exit(1)

    if src.is_dir():
        images = sorted([p for p in src.iterdir() if p.suffix.lower() in IMAGE_EXTS])
        if not images:
            print(f"[ERROR] Keine Bilder in {src} gefunden.")
            sys.exit(1)
        for img_path in images:
            process_image(img_path, model, args, out_dir)
    elif src.suffix.lower() in IMAGE_EXTS:
        process_image(src, model, args, out_dir)
    elif src.suffix.lower() in VIDEO_EXTS:
        process_video(src, model, args, out_dir)
    else:
        print(f"[ERROR] Nicht unterstütztes Format: {src.suffix}")
        sys.exit(1)


if __name__ == "__main__":
    main()
