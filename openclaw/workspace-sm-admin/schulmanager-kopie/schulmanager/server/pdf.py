"""Kleiner PDF-1.4-Schreiber (nur Standardbibliothek + optional ``segno`` für QR-Codes) – §11.3.

Genug für Zugangsbriefe: A4-Seiten, die PDF-Standardschriften Helvetica, Helvetica-Bold, Courier und Courier-Bold
(ohne Einbettung) mit ``WinAnsiEncoding`` (cp1252 – ä ö ü Ä Ö Ü ß „ “ – € werden korrekt dargestellt, nicht
darstellbare Zeichen ersetzt), Textbreiten aus den Adobe-AFM-Breitentabellen (Umbruch, Zentrieren, rechtsbündig),
Linien, Rechtecke (gefüllt/umrandet), QR-Codes als Form-XObject (einmal je Dokument, auf jeder Seite wiederverwendet),
mehrere Seiten, zlib-komprimierte Inhaltsströme und eine korrekte Querverweistabelle (``xref``).

Koordinaten in Punkt (1 pt = 1/72 Zoll) mit Ursprung **oben links** (y wächst nach unten); bei Text ist ``y`` die
Grundlinie. Beispiel::

    doc = Document(title="Zugangsdaten")
    page = doc.add_page()
    page.text(MARGIN, 80, "Grüße aus der Schule", size=18, font="bold")
    y = page.paragraph(MARGIN, 110, "Ein längerer Absatz …", width=page.width - 2 * MARGIN)
    page.qr(MARGIN, y + 10, "https://schule.example/login", size=90)
    data = doc.output()
"""
from __future__ import annotations

import unicodedata
import zlib
from datetime import datetime, timezone

A4 = (595.28, 841.89)
MM = 72 / 25.4

# Schriftnamen → (Ressourcenname, BaseFont)
FONTS: dict[str, tuple[str, str]] = {
    "regular": ("F1", "Helvetica"),
    "bold": ("F2", "Helvetica-Bold"),
    "mono": ("F3", "Courier"),
    "mono-bold": ("F4", "Courier-Bold"),
}

# Breiten (1/1000 em) der Zeichen 32…255 in WinAnsiEncoding laut Adobe-AFM (Helvetica / Helvetica-Bold).
_HELVETICA = (
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584, 350,
    556, 350, 222, 556, 333, 1000, 556, 556, 333, 1000, 667, 333, 1000, 350, 611, 350,
    350, 222, 222, 333, 333, 350, 556, 1000, 333, 1000, 500, 333, 944, 350, 500, 667,
    278, 333, 556, 556, 556, 556, 260, 556, 333, 737, 370, 556, 584, 333, 737, 333,
    400, 584, 333, 333, 333, 556, 537, 278, 333, 333, 365, 556, 834, 834, 834, 611,
    667, 667, 667, 667, 667, 667, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278,
    722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611,
    556, 556, 556, 556, 556, 556, 889, 500, 556, 556, 556, 556, 278, 278, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 584, 611, 556, 556, 556, 556, 500, 556, 500,
)
_HELVETICA_BOLD = (
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
    975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
    333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
    611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584, 350,
    556, 350, 278, 556, 500, 1000, 556, 556, 333, 1000, 667, 333, 1000, 350, 611, 350,
    350, 278, 278, 500, 500, 350, 556, 1000, 333, 1000, 556, 333, 944, 350, 500, 667,
    278, 333, 556, 556, 556, 556, 280, 556, 333, 737, 370, 556, 584, 333, 737, 333,
    400, 584, 333, 333, 333, 611, 556, 278, 333, 333, 365, 556, 834, 834, 834, 611,
    722, 722, 722, 722, 722, 722, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278,
    722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611,
    556, 556, 556, 556, 556, 556, 889, 556, 556, 556, 556, 556, 278, 278, 278, 278,
    611, 611, 611, 611, 611, 611, 611, 584, 611, 611, 611, 611, 611, 556, 611, 556,
)
_WIDTHS = {"regular": _HELVETICA, "bold": _HELVETICA_BOLD}

# Häufige Zeichen außerhalb von cp1252 → lesbarer Ersatz
_REPLACE = {
    " ": " ", " ": " ", " ": " ", " ": " ", "​": "", "­": "",
    "‐": "-", "‑": "-", "‒": "–", "―": "—", "−": "-",
    "′": "'", "″": '"', "→": "->", "←": "<-", "≤": "<=", "≥": ">=",
    "✓": "x", "✔": "x", "•": "•", "\t": " ", "\r": "", "\n": " ",
}


# =================================================================== Text
def encode(text: str) -> bytes:
    """Text → cp1252-Bytes (WinAnsiEncoding). Nicht darstellbare Zeichen werden ersetzt: bekannte Sonderzeichen
    durch Ähnliches, Buchstaben mit fremden Akzenten durch den Grundbuchstaben (ł → l nicht möglich → „?“)."""
    out = bytearray()
    for ch in str(text or ""):
        ch = _REPLACE.get(ch, ch)
        try:
            out += ch.encode("cp1252")
            continue
        except UnicodeEncodeError:
            pass
        base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
        try:
            out += base.encode("cp1252") if base else b"?"
        except UnicodeEncodeError:
            out += b"?"
    return bytes(out)


def text_width(text: str, size: float, font: str = "regular") -> float:
    """Breite von ``text`` in Punkt (nach der Ersetzung durch :func:`encode`)."""
    data = encode(text)
    if font.startswith("mono"):
        return len(data) * 600 * size / 1000
    table = _WIDTHS.get(font, _HELVETICA)
    return sum(table[b - 32] if 32 <= b <= 255 else 0 for b in data) * size / 1000


def wrap(text: str, width: float, size: float, font: str = "regular") -> list[str]:
    """Bricht ``text`` an Leerzeichen in Zeilen ≤ ``width`` um (zu lange Wörter werden geteilt).
    Zeilenumbrüche im Text (``\\n``) bleiben erhalten."""
    lines: list[str] = []
    for para in str(text or "").split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = ""
        for word in words:
            cand = f"{cur} {word}" if cur else word
            if text_width(cand, size, font) <= width:
                cur = cand
                continue
            if cur:
                lines.append(cur)
            # Wort länger als die Zeile → zeichenweise teilen
            while text_width(word, size, font) > width and len(word) > 1:
                cut = len(word)
                while cut > 1 and text_width(word[:cut], size, font) > width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            cur = word
        lines.append(cur)
    return lines


def _pdf_string(data: bytes) -> bytes:
    """Literal-String ``(…)`` mit Escapes; Bytes außerhalb von ASCII als Oktal-Escape."""
    out = bytearray(b"(")
    for b in data:
        if b in (0x28, 0x29, 0x5C):          # ( ) \
            out += b"\\" + bytes([b])
        elif 32 <= b <= 126:
            out.append(b)
        else:
            out += b"\\%03o" % b
    out += b")"
    return bytes(out)


def _text_string(text: str) -> bytes:
    """PDF-Textstring für Metadaten: ASCII als Literal, sonst UTF-16BE mit BOM (hex)."""
    if all(32 <= ord(c) < 127 for c in text):
        return _pdf_string(text.encode("ascii"))
    return b"<FEFF" + text.encode("utf-16-be").hex().upper().encode("ascii") + b">"


def _num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _color(rgb: tuple[float, float, float] | float | None, stroke: bool) -> str:
    if rgb is None:
        return ""
    if isinstance(rgb, (int, float)):
        return f"{_num(rgb)} {'G' if stroke else 'g'} "
    r, g, b = rgb
    return f"{_num(r)} {_num(g)} {_num(b)} {'RG' if stroke else 'rg'} "


# =================================================================== QR-Code
def qr_matrix(data: str, error: str = "m") -> list[list[bool]]:
    """QR-Code-Module (True = dunkel) ohne Ruhezone; braucht ``segno``."""
    import segno

    code = segno.make(data, error=error, micro=False)
    return [[bool(v) for v in row] for row in code.matrix]


def _qr_ops(matrix: list[list[bool]]) -> str:
    """Zeichenoperationen in Modul-Einheiten (1 Modul = 1 Einheit, Ursprung unten links), waagerechte Läufe
    dunkler Module zu einem Rechteck zusammengefasst."""
    n = len(matrix)
    ops = ["0 g"]
    for r, row in enumerate(matrix):
        y = n - r - 1
        c = 0
        while c < n:
            if not row[c]:
                c += 1
                continue
            start = c
            while c < n and row[c]:
                c += 1
            ops.append(f"{start} {y} {c - start} 1 re")
    ops.append("f")
    return "\n".join(ops)


# =================================================================== Dokument
class Page:
    """Eine Seite; Zeichenbefehle werden als Inhaltsstrom gesammelt."""

    def __init__(self, doc: "Document", width: float, height: float) -> None:
        self.doc = doc
        self.width = width
        self.height = height
        self._ops: list[str] = []
        self._xobjects: set[str] = set()
        self._fonts: set[str] = set()

    # ----------------------------------------------------------- Text
    def text(self, x: float, y: float, text: str, *, size: float = 11, font: str = "regular",
             color: tuple[float, float, float] | float | None = None) -> float:
        """Schreibt eine Zeile (Grundlinie ``y``); Rückgabe: Breite in Punkt."""
        res, _ = FONTS.get(font, FONTS["regular"])
        self._fonts.add(font if font in FONTS else "regular")
        data = encode(text)
        op = (f"BT /{res} {_num(size)} Tf {_num(x)} {_num(self.height - y)} Td "
              + _pdf_string(data).decode("latin-1") + " Tj ET")
        # Farbe nur innerhalb von q … Q setzen (BT/ET sichern den Grafikzustand nicht)
        self._ops.append(f"q {_color(color, stroke=False)}{op} Q" if color is not None else op)
        return text_width(text, size, font)

    def text_right(self, x_right: float, y: float, text: str, **kw) -> float:
        w = text_width(text, kw.get("size", 11), kw.get("font", "regular"))
        self.text(x_right - w, y, text, **kw)
        return w

    def text_center(self, x_center: float, y: float, text: str, **kw) -> float:
        w = text_width(text, kw.get("size", 11), kw.get("font", "regular"))
        self.text(x_center - w / 2, y, text, **kw)
        return w

    def paragraph(self, x: float, y: float, text: str, width: float, *, size: float = 11, font: str = "regular",
                  leading: float | None = None, color: tuple[float, float, float] | float | None = None) -> float:
        """Absatz mit Umbruch; ``y`` = Grundlinie der ersten Zeile. Rückgabe: Grundlinie der nächsten Zeile."""
        lead = leading or size * 1.35
        for line in wrap(text, width, size, font):
            if line:
                self.text(x, y, line, size=size, font=font, color=color)
            y += lead
        return y

    # ----------------------------------------------------------- Grafik
    def line(self, x1: float, y1: float, x2: float, y2: float, *, width: float = 0.5,
             color: tuple[float, float, float] | float = 0) -> None:
        self._ops.append(f"q {_color(color, stroke=True)}{_num(width)} w {_num(x1)} {_num(self.height - y1)} m "
                         f"{_num(x2)} {_num(self.height - y2)} l S Q")

    def rect(self, x: float, y: float, w: float, h: float, *, fill: tuple[float, float, float] | float | None = None,
             stroke: tuple[float, float, float] | float | None = None, width: float = 0.5) -> None:
        """Rechteck (``x``/``y`` = linke obere Ecke); gefüllt und/oder umrandet."""
        if fill is None and stroke is None:
            fill = 0
        op = "B" if fill is not None and stroke is not None else ("f" if fill is not None else "S")
        self._ops.append(f"q {_color(fill, stroke=False)}{_color(stroke, stroke=True)}{_num(width)} w "
                         f"{_num(x)} {_num(self.height - y - h)} {_num(w)} {_num(h)} re {op} Q")

    def polyline(self, points: list[tuple[float, float]], *, width: float = 1.0,
                 color: tuple[float, float, float] | float = 0, rounded: bool = True) -> None:
        """Offener Linienzug (``y`` von oben); ``rounded`` = runde Enden und Ecken."""
        if len(points) < 2:
            return
        pts = " ".join(f"{_num(px)} {_num(self.height - py)} {'m' if i == 0 else 'l'}"
                       for i, (px, py) in enumerate(points))
        caps = "1 J 1 j " if rounded else ""
        self._ops.append(f"q {_color(color, stroke=True)}{caps}{_num(width)} w {pts} S Q")

    def circle(self, cx: float, cy: float, r: float, *, fill: tuple[float, float, float] | float = 0) -> None:
        """Gefüllter Kreis (vier Bézier-Bögen; ``cy`` von oben)."""
        k = 0.5523 * r
        y = self.height - cy
        self._ops.append(
            f"q {_color(fill, stroke=False)}{_num(cx + r)} {_num(y)} m "
            f"{_num(cx + r)} {_num(y + k)} {_num(cx + k)} {_num(y + r)} {_num(cx)} {_num(y + r)} c "
            f"{_num(cx - k)} {_num(y + r)} {_num(cx - r)} {_num(y + k)} {_num(cx - r)} {_num(y)} c "
            f"{_num(cx - r)} {_num(y - k)} {_num(cx - k)} {_num(y - r)} {_num(cx)} {_num(y - r)} c "
            f"{_num(cx + k)} {_num(y - r)} {_num(cx + r)} {_num(y - k)} {_num(cx + r)} {_num(y)} c f Q")

    def qr(self, x: float, y: float, data: str, size: float = 90, *, quiet: int = 0) -> float:
        """QR-Code mit linker oberer Ecke (``x``, ``y``) und Kantenlänge ``size`` (Punkt). ``quiet`` = Module
        Ruhezone innerhalb von ``size``. Gleiche Inhalte werden im Dokument nur einmal gespeichert."""
        name, n = self.doc._qr_xobject(data)
        self._xobjects.add(name)
        scale = size / (n + 2 * quiet)
        ox = x + quiet * scale
        oy = self.height - y - size + quiet * scale
        self._ops.append(f"q {_num(scale)} 0 0 {_num(scale)} {_num(ox)} {_num(oy)} cm /{name} Do Q")
        return size

    def content(self) -> bytes:
        return "\n".join(self._ops).encode("latin-1")


class Document:
    """PDF-Dokument aus Seiten (:meth:`add_page`), Ausgabe mit :meth:`output`."""

    def __init__(self, *, title: str = "", author: str = "", subject: str = "", compress: bool = True) -> None:
        self.title = title
        self.author = author
        self.subject = subject
        self.compress = compress
        self.pages: list[Page] = []
        self._qr: dict[str, tuple[str, int, str]] = {}   # Daten → (Name, Modulzahl, Operationen)

    def add_page(self, size: tuple[float, float] = A4) -> Page:
        page = Page(self, *size)
        self.pages.append(page)
        return page

    def _qr_xobject(self, data: str) -> tuple[str, int]:
        if data not in self._qr:
            matrix = qr_matrix(data)
            self._qr[data] = (f"QR{len(self._qr) + 1}", len(matrix), _qr_ops(matrix))
        name, n, _ = self._qr[data]
        return name, n

    # ----------------------------------------------------------- Ausgabe
    def _stream(self, dictionary: str, data: bytes) -> bytes:
        if self.compress:
            data = zlib.compress(data, 9)
            dictionary += " /Filter /FlateDecode"
        return (f"<< {dictionary} /Length {len(data)} >>\nstream\n").encode("latin-1") + data + b"\nendstream"

    def output(self) -> bytes:
        """Serialisiert das Dokument (PDF 1.4) mit korrekten ``xref``-Offsets."""
        if not self.pages:
            self.add_page()
        objects: list[bytes] = []

        def reserve() -> int:
            objects.append(b"")
            return len(objects)

        catalog, pages_id, info = reserve(), reserve(), reserve()
        font_ids = {}
        for key, (_, base) in FONTS.items():
            oid = reserve()
            font_ids[key] = oid
            objects[oid - 1] = (f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} "
                                "/Encoding /WinAnsiEncoding >>").encode("latin-1")
        qr_ids = {}
        for name, n, ops in self._qr.values():
            oid = reserve()
            qr_ids[name] = oid
            objects[oid - 1] = self._stream(f"/Type /XObject /Subtype /Form /BBox [0 0 {n} {n}]",
                                            ops.encode("latin-1"))
        kids = []
        for page in self.pages:
            content_id, page_id = reserve(), reserve()
            objects[content_id - 1] = self._stream("", page.content())
            fonts = " ".join(f"/{FONTS[k][0]} {font_ids[k]} 0 R" for k in sorted(page._fonts or {"regular"}))
            res = f"/Font << {fonts} >>"
            if page._xobjects:
                res += " /XObject << " + " ".join(f"/{n} {qr_ids[n]} 0 R" for n in sorted(page._xobjects)) + " >>"
            objects[page_id - 1] = (f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {_num(page.width)} "
                                    f"{_num(page.height)}] /Resources << {res} >> /Contents {content_id} 0 R >>"
                                    ).encode("latin-1")
            kids.append(page_id)
        objects[catalog - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("latin-1")
        objects[pages_id - 1] = (f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] "
                                 f"/Count {len(kids)} >>").encode("latin-1")
        now = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
        meta = [b"/Producer " + _text_string("Schulmanager"), b"/CreationDate " + _text_string(now)]
        for key, value in (("Title", self.title), ("Author", self.author), ("Subject", self.subject)):
            if value:
                meta.append(f"/{key} ".encode("latin-1") + _text_string(value))
        objects[info - 1] = b"<< " + b" ".join(meta) + b" >>"

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
        out += b"0000000000 65535 f \n"
        for off in offsets:
            out += f"{off:010d} 00000 n \n".encode("latin-1")
        out += (f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R /Info {info} 0 R >>\n"
                f"startxref\n{xref}\n%%EOF\n").encode("latin-1")
        return bytes(out)
