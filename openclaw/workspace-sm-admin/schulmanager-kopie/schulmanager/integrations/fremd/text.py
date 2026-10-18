"""Textwerkzeuge der Fremdsystem-Importe: HTML → Markdown, Datumsformate, Namensvergleich."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from typing import Optional

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PLUGINFILE = re.compile(r"@@PLUGINFILE@@/([^\s\"'<>)]+)")


class _MD(HTMLParser):
    """Sehr schlanker HTML→Markdown-Wandler (Absätze, Listen, Fett/Kursiv, Links, Überschriften, Tabellen als Text)."""

    BLOCK = {"p", "div", "section", "article", "table", "tr", "blockquote", "pre"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.lists: list[list] = []        # [ordered, counter]
        self.href: list[str] = []
        self.skip = 0

    def _nl(self, n: int = 1) -> None:
        text = "".join(self.out)
        if not text:
            return
        have = len(text) - len(text.rstrip("\n"))
        self.out.append("\n" * max(0, n - have))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "br":
            self.out.append("\n")
        elif tag in self.BLOCK:
            self._nl(2)
        elif tag in ("ul", "ol"):
            self._nl(1)
            self.lists.append([tag == "ol", 0])
        elif tag == "li":
            self._nl(1)
            if self.lists:
                self.lists[-1][1] += 1
                mark = f"{self.lists[-1][1]}. " if self.lists[-1][0] else "- "
                self.out.append("  " * (len(self.lists) - 1) + mark)
            else:
                self.out.append("- ")
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("i", "em"):
            self.out.append("*")
        elif tag == "a":
            self.href.append(a.get("href") or "")
            self.out.append("[")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._nl(2)
            self.out.append("#" * min(int(tag[1]) + 1, 6) + " ")
        elif tag == "img":
            alt = a.get("alt") or "Bild"
            self.out.append(f"[{alt}]")
        elif tag in ("td", "th"):
            self.out.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK or tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._nl(2)
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self._nl(1)
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("i", "em"):
            self.out.append("*")
        elif tag == "a":
            href = self.href.pop() if self.href else ""
            self.out.append(f"]({href})" if href and not href.lower().startswith("javascript") else "]")
        elif tag in ("td", "th"):
            self.out.append(" |")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(re.sub(r"[ \t\r\n]+", " ", data))


def html_to_md(source: Optional[str], limit: int = 20000) -> str:
    """HTML (Moodle-Texte) → Markdown/Klartext. Reiner Text ohne Tags bleibt unverändert (außer Leerraum)."""
    s = (source or "")
    if not s.strip():
        return ""
    s = _PLUGINFILE.sub(lambda m: f"[Datei: {m.group(1)}]", s)
    if "<" not in s and "&" not in s:
        return _CTRL.sub("", s).strip()[:limit]
    p = _MD()
    try:
        p.feed(s)
        p.close()
    except Exception:  # noqa: BLE001 - kaputtes HTML nie den Import stoppen
        return _CTRL.sub("", re.sub(r"<[^>]*>", " ", s)).strip()[:limit]
    text = "".join(p.out)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return _CTRL.sub("", text).strip()[:limit]


# --------------------------------------------------------------------------------------------------- Datum
_DATE_RES = [
    (re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T ].*)?$"), (0, 1, 2)),
    (re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\D.*)?$"), (2, 1, 0)),
    (re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$"), (2, 1, 0)),          # TT/MM/JJJJ (europäisch)
    (re.compile(r"^(\d{4})(\d{2})(\d{2})$"), (0, 1, 2)),
    (re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{2})$"), (2, 1, 0)),
]


def parse_date(value) -> str:
    """Beliebiges Datum (ISO, TT.MM.JJJJ, JJJJMMTT, Unix-Sekunden, ``date``/``datetime``) → ISO-Datum oder ``""``."""
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return epoch_to_iso(value)
    s = str(value).strip()
    for rx, (iy, im, idd) in _DATE_RES:
        m = rx.match(s)
        if m:
            y, mo, d = int(m.group(iy + 1)), int(m.group(im + 1)), int(m.group(idd + 1))
            if y < 100:
                y += 2000 if y < 70 else 1900
            try:
                return date(y, mo, d).isoformat()
            except ValueError:
                return ""
    if s.isdigit() and len(s) in (9, 10):
        return epoch_to_iso(int(s))
    return ""


def epoch_to_dt(value) -> Optional[datetime]:
    """Unix-Sekunden → naives UTC-``datetime`` (0/leer/ungültig → ``None``)."""
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    try:
        return datetime.fromtimestamp(n, tz=timezone.utc).replace(tzinfo=None)
    except (OverflowError, OSError, ValueError):
        return None


def epoch_to_iso(value) -> str:
    dt = epoch_to_dt(value)
    return dt.date().isoformat() if dt else ""


def parse_iso_dt(value) -> Optional[datetime]:
    """ISO-8601-Zeitpunkt (auch mit ``Z``/Offset) → naives UTC-``datetime``."""
    s = str(value or "").strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        iso = parse_date(s)
        return datetime.fromisoformat(iso) if iso else None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# --------------------------------------------------------------------------------------------------- Namen
def fold(text: str) -> str:
    """Vergleichsform eines Namens: klein, ä→ae/ö→oe/ü→ue/ß→ss, Akzente weg, nur Buchstaben/Ziffern."""
    s = (text or "").strip().lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = s.replace("ı", "i").replace("ø", "o").replace("æ", "ae").replace("œ", "oe").replace("ł", "l").replace("đ", "d")
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


def clean(value, limit: int = 0) -> str:
    s = _CTRL.sub("", "" if value is None else str(value)).strip()
    return s[:limit] if limit else s
