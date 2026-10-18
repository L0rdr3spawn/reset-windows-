"""Minimaler PDF-Erzeuger (eine A4-Seite, Text in Helvetica, Linien, Kästchen) – ohne Fremdbibliothek.

Text wird in WinAnsi (cp1252) kodiert, damit Umlaute und ß korrekt erscheinen. Genug für Formulare zum Ausdrucken
und Ausfüllen (z. B. die schriftliche Entschuldigung), nicht für Fließtext mit Silbentrennung.
"""
from __future__ import annotations

from dataclasses import dataclass, field

A4 = (595.0, 842.0)          # Punkte (1/72 Zoll)
MARGIN = 56.0


def _esc(text: str) -> bytes:
    raw = text.encode("cp1252", errors="replace")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def text_width(text: str, size: float, bold: bool = False) -> float:
    """Grobe Breite (Helvetica-Mittelwert) – reicht für Umbrüche in Formularen."""
    return len(text) * size * (0.56 if bold else 0.52)


@dataclass
class Page:
    ops: list[bytes] = field(default_factory=list)
    y: float = A4[1] - MARGIN

    def text(self, x: float, y: float, text: str, size: float = 10, bold: bool = False, gray: float = 0.0) -> None:
        font = b"/F2" if bold else b"/F1"
        self.ops.append(b"BT %s %.1f Tf %.2f g %.1f %.1f Td (%s) Tj ET" % (font, size, gray, x, y, _esc(text)))

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 0.6, gray: float = 0.0) -> None:
        self.ops.append(b"%.2f G %.2f w %.1f %.1f m %.1f %.1f l S" % (gray, width, x1, y1, x2, y2))

    def box(self, x: float, y: float, w: float, h: float, width: float = 0.8, checked: bool = False) -> None:
        self.ops.append(b"0 G %.2f w %.1f %.1f %.1f %.1f re S" % (width, x, y, w, h))
        if checked:
            self.line(x + 2, y + h / 2, x + w / 2 - 0.5, y + 2, 1.2)
            self.line(x + w / 2 - 0.5, y + 2, x + w - 1.5, y + h - 1.5, 1.2)

    def polyline(self, points: list[tuple[float, float]], width: float = 1.0, gray: float = 0.0) -> None:
        """Offener Linienzug mit runden Enden und Ecken (PDF-Koordinaten, y nach oben)."""
        if len(points) < 2:
            return
        pts = b" ".join(b"%.1f %.1f %s" % (px, py, b"m" if i == 0 else b"l") for i, (px, py) in enumerate(points))
        self.ops.append(b"q %.2f G 1 J 1 j %.2f w %s S Q" % (gray, width, pts))

    def disc(self, cx: float, cy: float, r: float, gray: float = 0.0) -> None:
        """Gefüllter Kreis (vier Bézier-Bögen)."""
        k = 0.5523 * r
        self.ops.append(b"q %.2f g %.1f %.1f m %.1f %.1f %.1f %.1f %.1f %.1f c %.1f %.1f %.1f %.1f %.1f %.1f c "
                        b"%.1f %.1f %.1f %.1f %.1f %.1f c %.1f %.1f %.1f %.1f %.1f %.1f c f Q"
                        % (gray, cx + r, cy, cx + r, cy + k, cx + k, cy + r, cx, cy + r, cx - k, cy + r, cx - r, cy + k,
                           cx - r, cy, cx - r, cy - k, cx - k, cy - r, cx, cy - r, cx + k, cy - r, cx + r, cy - k, cx + r, cy))

    # ------------------------------------------------------------ Fluss von oben nach unten
    def para(self, text: str, size: float = 10, bold: bool = False, gap: float = 4, width: float = 0,
             gray: float = 0.0) -> None:
        """Absatz mit einfachem Wortumbruch."""
        width = width or (A4[0] - 2 * MARGIN)
        words, line = text.split(), ""
        for w in words:
            cand = f"{line} {w}".strip()
            if text_width(cand, size, bold) > width and line:
                self.text(MARGIN, self.y, line, size, bold, gray)
                self.y -= size * 1.35
                line = w
            else:
                line = cand
        if line:
            self.text(MARGIN, self.y, line, size, bold, gray)
            self.y -= size * 1.35
        self.y -= gap

    def field(self, label: str, value: str = "", width: float = 0, x: float = MARGIN, size: float = 10) -> None:
        """Beschriftung über einer Schreiblinie (Wert vorausgefüllt, sonst leer zum Ausfüllen)."""
        width = width or (A4[0] - MARGIN - x)
        self.text(x, self.y, label, 8, gray=0.35)
        self.y -= 15
        if value:
            self.text(x + 2, self.y + 3, value, size)
        self.line(x, self.y, x + width, self.y, 0.5)
        self.y -= 16

    def check(self, label: str, checked: bool = False, x: float = MARGIN, size: float = 10, after: str = "",
              line_width: float = 0) -> None:
        self.box(x, self.y - 2, 10, 10, checked=checked)
        self.text(x + 16, self.y, label, size)
        if line_width:
            lx = x + 16 + text_width(label, size) + 6
            self.line(lx, self.y - 2, lx + line_width, self.y - 2, 0.5)
            if after:
                self.text(lx + 2, self.y, after, size)
        self.y -= 20


def render(pages: list[Page], title: str = "") -> bytes:
    """PDF-Datei aus Seiten erzeugen."""
    objs: list[bytes] = []

    def add(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    font1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    font2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    pages_id = len(objs) + 1 + 2 * len(pages)      # Pages-Objekt kommt nach allen Seiten
    kids = []
    for p in pages:
        stream = b"\n".join(p.ops)
        content = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
        kids.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.0f %.0f] /Contents %d 0 R "
                        b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> >>"
                        % (pages_id, A4[0], A4[1], content, font1, font2)))
    assert add(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids),
                                                             len(kids))) == pages_id
    info = add(b"<< /Title (%s) /Producer (Schulmanager) >>" % _esc(title))
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, catalog, info, xref)
    return bytes(out)
