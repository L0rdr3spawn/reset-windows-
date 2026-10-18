#!/usr/bin/env python3
"""
Importiert einen oder mehrere Roboflow-Universe-Exporte (YOLOv8-Format) ins
Projekt und behält dabei NUR die Spieler-Klasse - alle anderen Klassen
(z.B. "Enemy", "Chest", "Zmb"/Zombie) werden komplett verworfen.

Warum filtern statt alles übernehmen?
Öffentliche DayZ-Datensätze auf Roboflow sind teils mit Klassen wie
Enemy/Chest/Zombie gelabelt - das ist das typische Schema für Echtzeit-
ESP-Overlays. Wir nutzen hier bewusst nur "eine Person ist im Bild"
(für die nachträgliche Analyse aufgezeichneten Materials), keine
Freund/Feind-Unterscheidung oder Loot-Erkennung.

Vorgehen zum Herunterladen (einmalig, pro Datensatz):
  1. Kostenlosen Account auf https://roboflow.com anlegen (falls noch nicht vorhanden)
  2. Den Datensatz auf Roboflow Universe öffnen (z.B. die Links, die du geschickt hast)
  3. Button "Download Dataset" -> Format "YOLOv8" -> "zip download"
  4. Die .zip-Datei entpacken, z.B. nach ~/Downloads/dayzv2/ und ~/Downloads/enmy/

Nutzung dieses Skripts:
    python prepare_dataset.py \\
        --export ~/Downloads/dayzv2 --export ~/Downloads/enmy \\
        --keep-classes player people players

    (case-insensitive Teilstring-Match auf die Klassennamen aus der jeweiligen
    data.yaml/README der Exporte - "players-bY8x" oder "Players-fiQb" matchen
    z.B. auf "player")

Ergebnis: gefilterte Bilder + remappte Labels (alles -> Klasse 0 "player")
landen in dataset/images/{train,val} und dataset/labels/{train,val},
bereit für train.py.
"""

import argparse
import random
import shutil
from pathlib import Path

import yaml

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args():
    p = argparse.ArgumentParser(description="Roboflow-Export importieren & auf Spieler-Klasse filtern")
    p.add_argument("--export", action="append", required=True,
                   help="Pfad zu einem entpackten Roboflow-Export (kann mehrfach angegeben werden)")
    p.add_argument("--keep-classes", nargs="+", default=["player", "players", "people", "person"],
                   help="Teilstrings (case-insensitive), die eine Klasse als 'Spieler' qualifizieren")
    p.add_argument("--dest", default="dataset", help="Ziel-Datensatzordner im Projekt")
    p.add_argument("--val-split", type=float, default=0.15,
                   help="Anteil für Validierung, falls der Export keine eigene val/test-Aufteilung hat")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def find_data_yaml(export_dir: Path) -> Path:
    candidates = list(export_dir.glob("data.yaml")) + list(export_dir.glob("*/data.yaml"))
    if not candidates:
        raise FileNotFoundError(f"Keine data.yaml in {export_dir} gefunden - ist das ein YOLOv8-Export?")
    return candidates[0]


def matched_class_ids(names: list[str], keep_classes: list[str]) -> set[int]:
    keep_lower = [k.lower() for k in keep_classes]
    matched = set()
    for idx, name in enumerate(names):
        n = name.lower()
        if any(k in n for k in keep_lower):
            matched.add(idx)
    return matched


def find_split_dirs(export_dir: Path) -> list[tuple[str, Path, Path]]:
    """Liefert Liste von (split_name, images_dir, labels_dir) für train/valid/test, falls vorhanden."""
    splits = []
    for split_name, alt_names in [("train", ["train"]), ("val", ["valid", "val"]), ("test", ["test"])]:
        for alt in alt_names:
            img_dir = export_dir / alt / "images"
            lbl_dir = export_dir / alt / "labels"
            if img_dir.is_dir() and lbl_dir.is_dir():
                splits.append((split_name, img_dir, lbl_dir))
                break
    if not splits:
        # Flache Struktur ohne train/valid/test-Unterordner
        img_dir = export_dir / "images"
        lbl_dir = export_dir / "labels"
        if img_dir.is_dir() and lbl_dir.is_dir():
            splits.append(("all", img_dir, lbl_dir))
    return splits


def filter_and_copy(img_path: Path, lbl_path: Path, matched_ids: set[int],
                     out_img_dir: Path, out_lbl_dir: Path, prefix: str) -> bool:
    """Kopiert Bild + gefiltertes Label, falls nach Filterung mind. 1 Box übrig bleibt.
    Gibt True zurück, wenn kopiert wurde."""
    if not lbl_path.exists():
        return False
    kept_lines = []
    with open(lbl_path) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            cls_id = int(float(parts[0]))
            if cls_id in matched_ids:
                # Remap auf Klasse 0 ("player")
                kept_lines.append("0 " + " ".join(parts[1:]))
    if not kept_lines:
        return False

    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)
    new_name = f"{prefix}_{img_path.stem}"
    shutil.copy2(img_path, out_img_dir / f"{new_name}{img_path.suffix}")
    with open(out_lbl_dir / f"{new_name}.txt", "w") as f:
        f.write("\n".join(kept_lines) + "\n")
    return True


def main():
    args = parse_args()
    random.seed(args.seed)
    dest = Path(args.dest)

    total_kept = 0
    total_seen = 0

    for export_str in args.export:
        export_dir = Path(export_str).expanduser()
        if not export_dir.is_dir():
            print(f"[WARN] Übersprungen, kein Ordner: {export_dir}")
            continue

        try:
            data_yaml_path = find_data_yaml(export_dir)
        except FileNotFoundError as e:
            print(f"[WARN] {e}")
            continue

        with open(data_yaml_path) as f:
            data_cfg = yaml.safe_load(f)
        names = data_cfg.get("names", [])
        if isinstance(names, dict):
            names = [names[i] for i in sorted(names)]

        matched = matched_class_ids(names, args.keep_classes)
        print(f"\n[{export_dir.name}] Klassen im Export: {names}")
        print(f"[{export_dir.name}] Übernommen (-> 'player'): "
              f"{[names[i] for i in matched] if matched else 'KEINE - prüfe --keep-classes!'}")

        prefix = export_dir.name.replace(" ", "_")
        splits = find_split_dirs(export_dir)
        if not splits:
            print(f"[WARN] Keine images/labels-Struktur in {export_dir} gefunden.")
            continue

        for split_name, img_dir, lbl_dir in splits:
            images = sorted([p for p in img_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS])
            for img_path in images:
                total_seen += 1
                lbl_path = lbl_dir / f"{img_path.stem}.txt"

                if split_name == "all":
                    target = "val" if random.random() < args.val_split else "train"
                elif split_name == "test":
                    target = "val"  # Test-Split hängen wir mit an val, um Duplikate/Leakage zu vermeiden
                else:
                    target = split_name

                ok = filter_and_copy(
                    img_path, lbl_path, matched,
                    dest / "images" / target, dest / "labels" / target,
                    prefix,
                )
                if ok:
                    total_kept += 1

    print(f"\nFertig: {total_kept}/{total_seen} Bilder mit mindestens einer Spieler-Box übernommen.")
    print(f"-> {dest}/images/{{train,val}} und {dest}/labels/{{train,val}}")
    print("\nNächster Schritt: python train.py --epochs 50")


if __name__ == "__main__":
    main()
