#!/usr/bin/env python3
"""
Letzter Schritt der Sammel-Pipeline: übernimmt ALLE Bilder aus captures/
(die review.py bereits mit einer YOLO-Label-Datei versehen hat - egal ob sie
in der Galerie als "gut" oder "schlecht" aufgetaucht sind oder in der
mittleren Zone lagen) ins eigentliche Trainingsset unter dataset/.

Bevor du das laufen lässt: schau dir review/gallery.html an und lösche in
captures/ die Bild+Label-Paare, die offensichtlicher Müll sind (z.B. leere
Szenen, Fehlerkennungen die du nicht im Training haben willst). Alles, was
danach noch in captures/ liegt, landet im nächsten Training.

Das Skript ist idempotent: bereits übernommene Bilder werden beim nächsten
Aufruf nicht doppelt kopiert (Merkliste in dataset/.finalized_sources.txt).

Nutzung:
    python finalize_dataset.py --source captures --val-split 0.15

Danach:
    python train.py --epochs 50
"""

import argparse
import random
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args():
    p = argparse.ArgumentParser(description="Übernimmt alle gelabelten Screenshots aus captures/ ins Trainingsset")
    p.add_argument("--source", default="captures", help="Ordner mit Screenshots + YOLO-Labels (von review.py)")
    p.add_argument("--dest", default="dataset", help="Ziel-Datensatzordner")
    p.add_argument("--val-split", type=float, default=0.15, help="Anteil für Validierung")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--move", action="store_true",
                   help="Dateien verschieben statt kopieren (Standard: kopieren, Originale bleiben in captures/)")
    return p.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)
    source_dir = Path(args.source)
    dest_dir = Path(args.dest)

    if not source_dir.is_dir():
        print(f"[ERROR] Quellordner nicht gefunden: {source_dir}")
        return

    finalized_log = dest_dir / ".finalized_sources.txt"
    already_done = set()
    if finalized_log.exists():
        already_done = set(finalized_log.read_text().splitlines())

    images = sorted(p for p in source_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS)

    added, skipped_no_label, skipped_done = 0, 0, 0
    newly_done = []

    for img_path in images:
        key = str(img_path.relative_to(source_dir))
        if key in already_done:
            skipped_done += 1
            continue

        label_path = img_path.with_suffix(".txt")
        if not label_path.exists():
            skipped_no_label += 1
            continue  # noch nicht durch review.py gelaufen -> überspringen

        target = "val" if random.random() < args.val_split else "train"
        img_out_dir = dest_dir / "images" / target
        lbl_out_dir = dest_dir / "labels" / target
        img_out_dir.mkdir(parents=True, exist_ok=True)
        lbl_out_dir.mkdir(parents=True, exist_ok=True)

        new_stem = img_path.stem
        transfer = shutil.move if args.move else shutil.copy2
        transfer(str(img_path), str(img_out_dir / f"{new_stem}{img_path.suffix}"))
        transfer(str(label_path), str(lbl_out_dir / f"{new_stem}.txt"))

        newly_done.append(key)
        added += 1

    if newly_done:
        with open(finalized_log, "a") as f:
            f.write("\n".join(newly_done) + "\n")

    print(f"Neu übernommen: {added}")
    print(f"Bereits vorher übernommen (übersprungen): {skipped_done}")
    print(f"Noch ohne Label, also übersprungen (erst review.py laufen lassen): {skipped_no_label}")
    if added:
        print(f"\n-> {dest_dir}/images/{{train,val}} und {dest_dir}/labels/{{train,val}} aktualisiert.")
        print("Nächster Schritt: python train.py --epochs 50")


if __name__ == "__main__":
    main()
