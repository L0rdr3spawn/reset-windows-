#!/usr/bin/env python3
"""
Dataset Recorder - sammelt automatisch Screenshots WÄHREND du DayZ spielst,
um daraus Trainingsdaten für detect.py / train.py zu bauen.

WICHTIG, damit klar ist was dieses Tool NICHT tut:
  - Es zeigt dir NICHTS auf dem Bildschirm an (kein Overlay, keine Boxen,
    keine Hervorhebungen während des Spiels)
  - Es liest keinen Spiel-Speicher aus und greift nicht in den DayZ-Prozess ein
  - Es beeinflusst dein Gameplay in keiner Weise
  Es macht ausschließlich regelmäßig (und per Hotkey manuell) Screenshots
  deines Bildschirms und speichert sie still im Hintergrund auf die Platte -
  wie ein ganz normales Screenshot-Tool. Was du mit den gesammelten Bildern
  danach machst (labeln, trainieren), passiert komplett offline, NACH der
  Spielsession, über prepare_dataset.py / train.py.

Nutzung:
    # Einfachster Fall: alle 3 Sekunden automatisch ein Bild
    python dataset_recorder.py --interval 3 --out captures

    # Zusätzlich: F8 drückt sofort einen Extra-Screenshot (z.B. genau wenn
    # ein Spieler zu sehen ist), F9 beendet die Aufnahme sauber
    python dataset_recorder.py --interval 5 --hotkey f8 --quit-key f9

    # Optional: Screenshots direkt mit dem aktuellen Modell vorlabeln
    # (Vorschläge, die du danach in LabelImg/CVAT/Roboflow nur noch
    # kontrollieren/korrigieren musst, statt bei null anzufangen)
    python dataset_recorder.py --interval 3 --auto-label --weights yolov8n.pt

Voraussetzungen (auf DEINEM Rechner, während DayZ läuft):
    pip install mss pynput ultralytics opencv-python-headless

Hinweis: pynput (für den Hotkey) braucht auf Windows/Mac keine Sonderrechte.
Falls die Hotkey-Bibliothek auf deinem System nicht startet, fällt das Tool
automatisch auf reines Intervall-Sammeln zurück (dann einfach Ctrl+C zum Beenden).
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import mss

try:
    from pynput import keyboard as pynput_keyboard
    HOTKEYS_AVAILABLE = True
except Exception as e:  # z.B. kein Display / nicht unterstützte Plattform
    HOTKEYS_AVAILABLE = False
    _HOTKEY_IMPORT_ERROR = e


def parse_args():
    p = argparse.ArgumentParser(description="Sammelt automatisch Screenshots während des Spielens (kein Overlay)")
    p.add_argument("--interval", type=float, default=3.0, help="Sekunden zwischen automatischen Screenshots")
    p.add_argument("--out", default="captures", help="Zielordner für Screenshots")
    p.add_argument("--monitor", type=int, default=1, help="Monitor-Index (mss zählt ab 1; 0 = alle Monitore)")
    p.add_argument("--hotkey", default="f8", help="Taste für manuellen Sofort-Screenshot")
    p.add_argument("--quit-key", default="f9", help="Taste zum sauberen Beenden")
    p.add_argument("--dedupe-threshold", type=float, default=2.0,
                   help="Frames, die sich kaum vom letzten gespeicherten unterscheiden, werden übersprungen "
                        "(höher = toleranter/mehr wird als 'gleich' behandelt, 0 = deaktiviert)")
    p.add_argument("--max-shots", type=int, default=0, help="Optional: nach N Screenshots automatisch stoppen (0 = unbegrenzt)")

    p.add_argument("--auto-label", action="store_true",
                   help="Zusätzlich mit YOLO vorlabeln (Vorschläge zum Nachkontrollieren, keine fertigen Labels)")
    p.add_argument("--weights", default="yolov8n.pt", help="Modell für --auto-label")
    p.add_argument("--conf", type=float, default=0.35, help="Konfidenz-Schwelle für --auto-label")
    return p.parse_args()


def frame_diff_score(a: np.ndarray, b: np.ndarray) -> float:
    """Grobes Ähnlichkeitsmaß zwischen zwei Frames (kleines Graustufenbild, mittlere Differenz)."""
    small_a = cv2.resize(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (64, 36))
    small_b = cv2.resize(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), (64, 36))
    return float(np.mean(np.abs(small_a.astype(np.int16) - small_b.astype(np.int16))))


class Recorder:
    def __init__(self, args):
        self.args = args
        self.out_dir = Path(args.out)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.running = True
        self.force_shot = False
        self.count = 0
        self.last_saved_frame = None
        self.model = None

        if args.auto_label:
            from ultralytics import YOLO
            print(f"Lade Modell für Vorlabeln: {args.weights}")
            self.model = YOLO(args.weights)

    def request_stop(self):
        self.running = False

    def request_shot(self):
        self.force_shot = True

    def save(self, frame_bgr: np.ndarray):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        img_path = self.out_dir / f"capture_{ts}.jpg"
        cv2.imwrite(str(img_path), frame_bgr)
        self.count += 1

        if self.model is not None:
            results = self.model.predict(frame_bgr, conf=self.args.conf, classes=[0], verbose=False)
            boxes = results[0].boxes
            h, w = frame_bgr.shape[:2]
            lines = []
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
                    bw, bh = (x2 - x1) / w, (y2 - y1) / h
                    lines.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
            label_path = self.out_dir / f"capture_{ts}.txt"
            label_path.write_text("\n".join(lines) + ("\n" if lines else ""))

        print(f"[{self.count}] gespeichert: {img_path.name}"
              f"{'' if self.model is None else f' ({len(lines)} Vorschlag-Box(en))'}")

    def run(self):
        listener = None
        if HOTKEYS_AVAILABLE:
            def on_press(key):
                try:
                    name = key.char.lower() if hasattr(key, "char") and key.char else key.name.lower()
                except Exception:
                    return
                if name == self.args.hotkey.lower():
                    self.request_shot()
                elif name == self.args.quit_key.lower():
                    self.request_stop()

            listener = pynput_keyboard.Listener(on_press=on_press)
            listener.start()
            print(f"Hotkeys aktiv: [{self.args.hotkey.upper()}] = Sofort-Screenshot, "
                  f"[{self.args.quit_key.upper()}] = Beenden")
        else:
            print(f"[Hinweis] Hotkey-Unterstützung nicht verfügbar ({_HOTKEY_IMPORT_ERROR}). "
                  f"Läuft im reinen Intervall-Modus - Beenden mit Ctrl+C.")

        print(f"Sammle alle {self.args.interval}s einen Screenshot nach '{self.out_dir}/' ...")

        try:
            with mss.MSS() as sct:
                monitor = sct.monitors[self.args.monitor]
                last_auto_shot = 0.0
                while self.running:
                    now = time.time()
                    due_for_auto_shot = (now - last_auto_shot) >= self.args.interval
                    if due_for_auto_shot or self.force_shot:
                        raw = np.array(sct.grab(monitor))
                        frame = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)

                        is_duplicate = False
                        if (not self.force_shot) and self.args.dedupe_threshold > 0 and self.last_saved_frame is not None:
                            if frame_diff_score(frame, self.last_saved_frame) < self.args.dedupe_threshold:
                                is_duplicate = True

                        if not is_duplicate:
                            self.save(frame)
                            self.last_saved_frame = frame

                        last_auto_shot = now
                        self.force_shot = False

                        if self.args.max_shots and self.count >= self.args.max_shots:
                            print(f"Limit von {self.args.max_shots} Screenshots erreicht, beende.")
                            break
                    time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            if listener is not None:
                listener.stop()
            print(f"\nBeendet. {self.count} Screenshots gespeichert in '{self.out_dir}/'.")
            print("Nächster Schritt: Bilder sichten/labeln (z.B. mit LabelImg oder Roboflow) "
                  "und danach mit prepare_dataset.py bzw. manuell nach dataset/ übernehmen.")


def main():
    args = parse_args()
    Recorder(args).run()


if __name__ == "__main__":
    main()
