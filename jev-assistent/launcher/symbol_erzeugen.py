"""symbol_erzeugen.py - zeichnet jeff.ico (Mikrofon auf blauem Kreis) für Jeff.exe.

Ohne Pillow: reines Python, Kantenglättung durch Mehrfachabtastung.
Nur nötig, wenn das Symbol neu gezeichnet werden soll:
  python launcher\\symbol_erzeugen.py
"""
import struct
import zlib
from pathlib import Path

ZIEL = Path(__file__).resolve().parent / "jeff.ico"
GROESSEN = [16, 24, 32, 48, 64, 256]
OBEN, UNTEN = (0x3B, 0x82, 0xF6), (0x5B, 0x3D, 0xE0)   # Verlauf des Kreises
WEISS = (0xFF, 0xFF, 0xFF)


def _abgerundet(x, y, x0, y0, x1, y1, r):
    """Punkt in einem Rechteck mit abgerundeten Ecken?"""
    dx = max(x0 + r - x, 0, x - (x1 - r))
    dy = max(y0 + r - y, 0, y - (y1 - r))
    return x0 <= x <= x1 and y0 <= y <= y1 and dx * dx + dy * dy <= r * r


def _mikrofon(x, y):
    if _abgerundet(x, y, 0.40, 0.18, 0.60, 0.56, 0.10):          # Kapsel
        return True
    d = ((x - 0.5) ** 2 + (y - 0.44) ** 2) ** 0.5                  # Bügel (untere Hälfte)
    if y >= 0.44 and 0.175 <= d <= 0.225:
        return True
    if 0.475 <= x <= 0.525 and 0.64 <= y <= 0.76:                  # Stiel
        return True
    return _abgerundet(x, y, 0.36, 0.74, 0.64, 0.79, 0.025)        # Fuß


def _pixel(px, py, n, stufen):
    r = g = b = a = 0.0
    for sy in range(stufen):
        for sx in range(stufen):
            x = (px + (sx + 0.5) / stufen) / n
            y = (py + (sy + 0.5) / stufen) / n
            if (x - 0.5) ** 2 + (y - 0.5) ** 2 > 0.48 ** 2:
                continue
            farbe = WEISS if _mikrofon(x, y) else tuple(o + (u - o) * y for o, u in zip(OBEN, UNTEN))
            r, g, b, a = r + farbe[0], g + farbe[1], b + farbe[2], a + 1
    if not a:
        return 0, 0, 0, 0
    return round(r / a), round(g / a), round(b / a), round(255 * a / stufen ** 2)


def _bild(n):
    stufen = 4 if n >= 64 else 6
    return [[_pixel(x, y, n, stufen) for x in range(n)] for y in range(n)]


def _bmp(n, bild):
    kopf = struct.pack("<IiiHHIIiiII", 40, n, 2 * n, 1, 32, 0, 0, 0, 0, 0, 0)
    farben = b"".join(bytes((b, g, r, a)) for zeile in reversed(bild) for r, g, b, a in zeile)
    maske = bytes(((n + 31) // 32) * 4 * n)            # Alpha reicht, Maske bleibt leer
    return kopf + farben + maske


def _png(n, bild):
    def block(art, daten):
        return struct.pack(">I", len(daten)) + art + daten + struct.pack(">I", zlib.crc32(art + daten))
    roh = b"".join(b"\0" + b"".join(bytes(p) for p in zeile) for zeile in bild)
    return (b"\x89PNG\r\n\x1a\n" + block(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + block(b"IDAT", zlib.compress(roh, 9)) + block(b"IEND", b""))


def main():
    teile = [(_png if n >= 256 else _bmp)(n, _bild(n)) for n in GROESSEN]
    kopf = struct.pack("<HHH", 0, 1, len(teile))
    versatz = 6 + 16 * len(teile)
    eintraege = b""
    for n, daten in zip(GROESSEN, teile):
        eintraege += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(daten), versatz)
        versatz += len(daten)
    ZIEL.write_bytes(kopf + eintraege + b"".join(teile))
    print(f"{ZIEL} geschrieben ({ZIEL.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
