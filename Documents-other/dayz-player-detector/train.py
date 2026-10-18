#!/usr/bin/env python3
"""
Fine-Tuning des Player-Detectors auf eigene DayZ-Screenshots.

Voraussetzung: gelabelte Daten in dataset/images/{train,val} und
dataset/labels/{train,val} (siehe dataset.yaml und README.md).

Der vortrainierte YOLOv8-Detector (detect.py mit yolov8n.pt) erkennt Menschen
schon recht gut, weil DayZ-Charaktere wie normale Personen aussehen. Fine-Tuning
lohnt sich vor allem, wenn:
  - viele Fehlerkennungen/Übersehen in typischen DayZ-Szenen auftreten
    (Wald, Dämmerung, Tarnkleidung, Zombies die mit Spielern verwechselt werden),
  - du zwischen Spielern und Zombies/NPCs unterscheiden willst
    (dann in dataset.yaml zusätzlich z.B. "1: zombie" ergänzen und entsprechend labeln).

Nutzung:
    python train.py --epochs 50 --model yolov8n.pt
"""

import argparse
from ultralytics import YOLO


def parse_args():
    p = argparse.ArgumentParser(description="Fine-Tuning des Player-Detectors")
    p.add_argument("--model", default="yolov8n.pt", help="Basis-Modell (yolov8n/s/m.pt)")
    p.add_argument("--data", default="dataset.yaml", help="Pfad zur Datensatz-Konfiguration")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--device", default=None, help="'cpu', '0' (GPU 0), etc. Standard: automatisch")
    return p.parse_args()


def main():
    args = parse_args()
    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
    )
    print("\nFertig! Die trainierten Gewichte liegen unter runs/detect/train*/weights/best.pt")
    print("Nutze sie mit: python detect.py --source <video/bild> --weights runs/detect/train/weights/best.pt")


if __name__ == "__main__":
    main()
