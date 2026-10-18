#!/usr/bin/env python3
"""
Lässt die Erkennung über alle gesammelten Screenshots laufen (z.B. aus
captures/, siehe dataset_recorder.py) und sortiert die Ergebnisse nach
Konfidenz in zwei Listen:

  - "gut"  -> Modell war sich sehr sicher (hohe Konfidenz)
  - "schlecht" -> Modell war sich unsicher ODER hat gar nichts erkannt

Aus beiden Listen entsteht eine HTML-Übersicht (review/gallery.html) zum
Durchklicken. So siehst du auf einen Blick, wo das Modell schon gut
funktioniert und wo es (noch) schwächelt - genau die "schlechten" Fälle sind
die wertvollsten fürs nächste Training, weil sie zeigen, wo nachgebessert
werden muss.

Nebenbei schreibt review.py für JEDES verarbeitete Bild eine YOLO-Label-Datei
(Vorschlag, Klasse 0 = player) direkt neben das Original in --source. Diese
Labels kannst du bei Bedarf noch in LabelImg/CVAT korrigieren, bevor
finalize_dataset.py sie ins Training übernimmt.

Nutzung:
    # Einmaliger Durchlauf über alle bisher gesammelten Bilder
    python review.py --source captures --weights yolov8n.pt

    # Dauerhaft laufen lassen, während du weiter spielst/sammelst -
    # verarbeitet neue Bilder automatisch, sobald sie auftauchen
    python review.py --source captures --watch

Danach: review/gallery.html im Browser öffnen. Wenn du zufrieden bist
(oder offensichtlichen Müll aus captures/ gelöscht hast), alles mit
finalize_dataset.py ins Trainingsset übernehmen.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
THUMB_MAX_WIDTH = 480


def parse_args():
    p = argparse.ArgumentParser(description="Erkennung laufen lassen und Bilder nach Konfidenz sortieren")
    p.add_argument("--source", default="captures", help="Ordner mit Screenshots (z.B. von dataset_recorder.py)")
    p.add_argument("--weights", default="yolov8n.pt", help="Zu verwendendes Modell")
    p.add_argument("--conf-threshold", type=float, default=0.1,
                   help="Minimale Konfidenz, damit ein Treffer überhaupt gezählt wird")
    p.add_argument("--good-conf", type=float, default=0.75,
                   help="Ab dieser Konfidenz gilt ein Bild als 'besonders gut' erkannt")
    p.add_argument("--bad-conf", type=float, default=0.40,
                   help="Bei bester Konfidenz UNTER diesem Wert (oder 0 Treffern) gilt ein Bild als 'besonders schlecht'")
    p.add_argument("--out", default="review", help="Ausgabeordner für Galerie/Thumbnails")
    p.add_argument("--watch", action="store_true", help="Dauerhaft laufen und neue Bilder automatisch verarbeiten")
    p.add_argument("--poll-interval", type=float, default=5.0, help="Sekunden zwischen Ordner-Checks im --watch-Modus")
    return p.parse_args()


def load_manifest(manifest_path: Path) -> list[dict]:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return []


def save_manifest(manifest_path: Path, records: list[dict]):
    manifest_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))


def make_thumbnail(frame, boxes_xyxy_conf, out_path: Path):
    h, w = frame.shape[:2]
    if w > THUMB_MAX_WIDTH:
        scale = THUMB_MAX_WIDTH / w
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        scale_factor = scale
    else:
        scale_factor = 1.0

    out = frame.copy()
    for (x1, y1, x2, y2), conf in boxes_xyxy_conf:
        x1, y1, x2, y2 = [int(v * scale_factor) for v in (x1, y1, x2, y2)]
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 220, 0), 2)
        cv2.putText(out, f"{conf:.2f}", (x1, max(0, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 0), 1, cv2.LINE_AA)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), out, [cv2.IMWRITE_JPEG_QUALITY, 80])


def process_image(img_path: Path, model, args, source_dir: Path, out_dir: Path):
    frame = cv2.imread(str(img_path))
    if frame is None:
        return None

    results = model.predict(frame, conf=args.conf_threshold, classes=[0], verbose=False)
    boxes = results[0].boxes

    box_list = []
    confs = []
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            c = float(box.conf[0])
            box_list.append(((x1, y1, x2, y2), c))
            confs.append(c)

    n_boxes = len(box_list)
    best_conf = max(confs) if confs else 0.0
    mean_conf = sum(confs) / len(confs) if confs else 0.0

    # YOLO-Label-Datei neben dem Original schreiben (Klasse 0 = player)
    h, w = frame.shape[:2]
    label_lines = []
    for (x1, y1, x2, y2), c in box_list:
        cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
        bw, bh = (x2 - x1) / w, (y2 - y1) / h
        label_lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    label_path = img_path.with_suffix(".txt")
    label_path.write_text("\n".join(label_lines) + ("\n" if label_lines else ""))

    if n_boxes == 0:
        bucket, reason = "bad", "keine Erkennung"
    elif best_conf >= args.good_conf:
        bucket, reason = "good", f"hohe Konfidenz ({best_conf:.2f})"
    elif best_conf <= args.bad_conf:
        bucket, reason = "bad", f"niedrige Konfidenz ({best_conf:.2f})"
    else:
        bucket, reason = None, f"mittlere Konfidenz ({best_conf:.2f})"

    thumb_rel = None
    if bucket is not None:
        thumb_rel = f"thumbs/{bucket}/{img_path.stem}.jpg"
        make_thumbnail(frame, box_list, out_dir / thumb_rel)

    return {
        "file": str(img_path.relative_to(source_dir)),
        "bucket": bucket,
        "reason": reason,
        "n_boxes": n_boxes,
        "best_conf": round(best_conf, 4),
        "mean_conf": round(mean_conf, 4),
        "thumb": thumb_rel,
        "processed_at": datetime.now().isoformat(timespec="seconds"),
    }


GALLERY_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Player Detector - Review</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #111; color: #eee; margin: 0; padding: 24px; }}
  h1 {{ margin-top: 0; }}
  h2 {{ border-bottom: 2px solid #333; padding-bottom: 6px; }}
  .stats {{ color: #aaa; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; margin-bottom: 40px; }}
  .card {{ background: #1c1c1c; border-radius: 8px; overflow: hidden; border: 1px solid #333; }}
  .card img {{ width: 100%; display: block; }}
  .card .meta {{ padding: 8px 10px; font-size: 13px; }}
  .card .file {{ color: #ccc; word-break: break-all; font-size: 11px; }}
  .good .conf {{ color: #6f6; font-weight: bold; }}
  .bad .conf {{ color: #f66; font-weight: bold; }}
  .empty {{ color: #666; font-style: italic; }}
</style>
</head>
<body>
<h1>Player Detector - Review</h1>
<div class="stats">Erzeugt: {generated_at}  |  Gut: {n_good}  |  Schlecht: {n_bad}  |  Gesamt verarbeitet: {n_total}</div>

<h2>Besonders schlecht erkannt ({n_bad}) - zuerst anschauen</h2>
<div class="grid">
{bad_cards}
</div>

<h2>Besonders gut erkannt ({n_good})</h2>
<div class="grid">
{good_cards}
</div>

</body>
</html>
"""

CARD_TEMPLATE = """<div class="card {bucket}">
  <img src="{thumb}" loading="lazy">
  <div class="meta">
    <div class="conf">{reason}</div>
    <div>{n_boxes} Box(en)</div>
    <div class="file">{file}</div>
  </div>
</div>"""


def render_gallery(records: list[dict], out_dir: Path):
    good = [r for r in records if r["bucket"] == "good"]
    bad = [r for r in records if r["bucket"] == "bad"]
    good.sort(key=lambda r: r["best_conf"], reverse=True)
    bad.sort(key=lambda r: r["best_conf"])  # schlechteste (0 Treffer / niedrigste Konfidenz) zuerst

    good_cards = "\n".join(CARD_TEMPLATE.format(**r) for r in good) or '<div class="empty">Noch nichts hier.</div>'
    bad_cards = "\n".join(CARD_TEMPLATE.format(**r) for r in bad) or '<div class="empty">Noch nichts hier.</div>'

    html = GALLERY_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        n_good=len(good), n_bad=len(bad), n_total=len(records),
        good_cards=good_cards, bad_cards=bad_cards,
    )
    (out_dir / "gallery.html").write_text(html, encoding="utf-8")


def run_once(args, source_dir: Path, out_dir: Path, model, manifest_path: Path) -> int:
    records = load_manifest(manifest_path)
    seen = {r["file"] for r in records}

    images = sorted(p for p in source_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
    new_count = 0
    for img_path in images:
        rel = str(img_path.relative_to(source_dir))
        if rel in seen:
            continue
        record = process_image(img_path, model, args, source_dir, out_dir)
        if record is None:
            continue
        records.append(record)
        seen.add(rel)
        new_count += 1
        tag = record["bucket"] or "neutral"
        print(f"  [{tag}] {rel}: {record['n_boxes']} Box(en), beste Konfidenz {record['best_conf']}")

    if new_count > 0:
        save_manifest(manifest_path, records)
        render_gallery(records, out_dir)
    return new_count


def main():
    args = parse_args()
    source_dir = Path(args.source)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"

    if not source_dir.is_dir():
        print(f"[ERROR] Quellordner nicht gefunden: {source_dir}")
        return

    print(f"Lade Modell: {args.weights}")
    model = YOLO(args.weights)

    if args.watch:
        print(f"Beobachte '{source_dir}/' alle {args.poll_interval}s (Ctrl+C zum Beenden) ...")
        try:
            while True:
                n = run_once(args, source_dir, out_dir, model, manifest_path)
                if n:
                    print(f"  -> {n} neue Bilder verarbeitet, Galerie aktualisiert: {out_dir / 'gallery.html'}")
                time.sleep(args.poll_interval)
        except KeyboardInterrupt:
            print("\nBeendet.")
    else:
        n = run_once(args, source_dir, out_dir, model, manifest_path)
        print(f"\n{n} neue Bilder verarbeitet.")
        print(f"Galerie: {out_dir / 'gallery.html'} - im Browser öffnen zum Durchschauen.")


if __name__ == "__main__":
    main()
