"""Gemeinsame Hilfsfunktionen der Integrationen (intern, keine stabile API)."""
from __future__ import annotations

import codecs
import re
import unicodedata
from datetime import date, datetime
from typing import Any, Iterable, Optional

from ..models import School

DAY_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
DAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# Zeichen, die NFKD nicht auf ASCII/Latin-1 zurückführt
_TRANSLIT = {
    "ß": "ss", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "ı": "i", "ø": "o", "Ø": "O",
    "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "–": "-", "—": "-", "„": '"', "“": '"',
    "”": '"', "‚": "'", "‘": "'", "’": "'", "…": "...", "€": "EUR",
}


# ----------------------------------------------------------------- Datum
def as_date(value: date | datetime | str) -> date:
    """``date``, ``datetime`` oder ISO-String (``YYYY-MM-DD`` bzw. ``YYYYMMDD``) → ``date``."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if re.fullmatch(r"\d{8}", s):
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    if re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", s):
        d, m, y = (int(x) for x in s.split("."))
        return date(y, m, d)
    return date.fromisoformat(s[:10])


def plans_by_date(plans: Any) -> dict[str, dict]:
    """Normalisiert Vertretungspläne zu ``{ISO-Datum: DayPlan-Dict}``.

    Akzeptiert ``None``, eine Liste von DayPlan-Dicts/-Objekten (mit ``to_dict``)
    oder ein Dict ``Datum → DayPlan``.
    """
    out: dict[str, dict] = {}
    if not plans:
        return out
    items: Iterable[Any] = plans.values() if isinstance(plans, dict) else plans
    for p in items:
        if p is None:
            continue
        if hasattr(p, "to_dict"):
            p = p.to_dict()
        if not isinstance(p, dict) or not p.get("date"):
            continue
        out[str(p["date"])[:10]] = p
    return out


def holiday_on(school: School, day: date) -> Optional[str]:
    for h in school.holidays:
        try:
            if h.covers(day):
                return h.name or "Ferien"
        except (ValueError, TypeError):
            continue
    return None


# ----------------------------------------------------------- Stundenplan
def week_ranges(weeks: Iterable[int]) -> str:
    """Laufende Wochen (1-basiert) → ``"1,3"`` bzw. ``"1-4,9"`` (Läufe ab drei Wochen als Bereich)."""
    ws = sorted({int(w) for w in weeks if int(w) >= 1})
    out: list[str] = []
    i = 0
    while i < len(ws):
        j = i
        while j + 1 < len(ws) and ws[j + 1] == ws[j] + 1:
            j += 1
        if j - i >= 2:
            out.append(f"{ws[i]}-{ws[j]}")
        else:
            out += [str(w) for w in ws[i:j + 1]]
        i = j + 1
    return ",".join(out)


def parse_week_list(text: str) -> list[int]:
    """``"1,3"``, ``"1-4,9"``, ``"10,27"`` → laufende Wochen (1-basiert, sortiert, eindeutig)."""
    out: list[int] = []
    for tok in re.split(r"[,;/|+\s]+", (text or "").strip()):
        if not tok:
            continue
        m = re.fullmatch(r"(\d{1,2})\s*[-–]\s*(\d{1,2})", tok)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out += list(range(min(a, b), max(a, b) + 1))
        elif tok.isdigit():
            out.append(int(tok))
    return sorted({w for w in out if w >= 1})


def period_bounds(settings, start: int, length: int = 1) -> tuple[int, int]:
    """(Beginn, Ende) in Minuten seit Mitternacht für Stunden ``start``..``start+length-1``."""
    times = list(settings.period_times or [])
    minutes = int(getattr(settings, "period_minutes", 45) or 45)

    def begin(p: int) -> int:
        if 0 <= p < len(times):
            try:
                h, m = (int(x) for x in str(times[p]).split(":")[:2])
                return h * 60 + m
            except ValueError:
                pass
        if times:  # Raster fortschreiben (Stunde + 5 min Wechsel)
            last = len(times) - 1
            return begin(last) + (p - last) * (minutes + 5)
        return 8 * 60 + p * (minutes + 5)

    return begin(start), begin(start + length - 1) + minutes


# ----------------------------------------------------------------- Texte
def norm_key(text: str) -> str:
    """Spaltennamen normalisieren: klein, Umlaute → ae/oe/ue/ss, nur a-z0-9."""
    s = (text or "").strip().lower().replace("﻿", "")
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", s)


def split_name(name: str) -> tuple[str, str]:
    """``"Anna Maria Müller"`` → ``("Anna Maria", "Müller")``."""
    name = " ".join((name or "").split())
    if " " not in name:
        return "", name
    first, _, last = name.rpartition(" ")
    return first, last


def grade_from_name(name: str) -> Optional[int]:
    """Klassenstufe aus Klassennamen ableiten: ``"7a"`` → 7, ``"Q1-2"`` → 11, ``"EF"`` → 10."""
    s = (name or "").strip().upper()
    m = re.match(r"^(\d{1,2})", s)
    if m:
        return int(m.group(1))
    m = re.match(r"^Q\s*([12])", s)
    if m:
        return 10 + int(m.group(1))
    if s.startswith("EF") or s.startswith("E-PHASE") or s.startswith("E1") or s.startswith("E2"):
        return 10
    m = re.match(r"^(?:JG|JAHRGANG|K)\s*(\d{1,2})", s)
    if m:
        return int(m.group(1))
    return None


def decode_bytes(data: bytes | str, encoding: Optional[str] = None) -> tuple[str, str]:
    """Bytes → Text mit Kodierungserkennung.

    Reihenfolge: explizite Kodierung → BOM (UTF-8/UTF-16) → striktes UTF-8 →
    Windows-1252 (ANSI, Untis-Standard) → Latin-1. Liefert ``(text, kodierung)``.
    """
    if isinstance(data, str):
        return data.lstrip("﻿"), "str"
    if encoding:
        return data.decode(encoding, errors="replace").lstrip("﻿"), encoding
    if data.startswith(codecs.BOM_UTF8):
        return data[len(codecs.BOM_UTF8):].decode("utf-8", errors="replace"), "utf-8-sig"
    if data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        return data.decode("utf-16", errors="replace").lstrip("﻿"), "utf-16"
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252"), "cp1252"
    except UnicodeDecodeError:
        return data.decode("latin-1"), "latin-1"


def encode_lossy(text: str, encoding: str) -> bytes:
    """Kodiert ``text``; nicht darstellbare Zeichen werden transliteriert (``ğ`` → ``g``), sonst ``?``."""
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        pass
    out = []
    for ch in text:
        try:
            out.append(ch.encode(encoding))
            continue
        except UnicodeEncodeError:
            pass
        alt = _TRANSLIT.get(ch)
        if alt is None:
            alt = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
        try:
            out.append((alt or "?").encode(encoding))
        except UnicodeEncodeError:
            out.append(b"?")
    return b"".join(out)


def parse_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    s = str(value).strip().replace(",", ".")
    if not s:
        return default
    try:
        return int(round(float(s)))
    except ValueError:
        return default


def parse_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    s = str(value if value is not None else "").strip().replace(",", ".")
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def parse_bool(value: Any) -> Optional[bool]:
    s = norm_key(str(value if value is not None else ""))
    if not s:
        return None
    if s in {"ja", "j", "x", "1", "true", "wahr", "yes", "y", "w"}:
        return True
    if s in {"nein", "n", "0", "false", "falsch", "no", "f", "-"}:
        return False
    return None


def color_to_win32(color: str) -> Optional[int]:
    """``#rrggbb`` → Win32-COLORREF (``0x00BBGGRR``), wie Untis Farben speichert."""
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", (color or "").strip())
    if not m:
        return None
    r, g, b = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    return r | (g << 8) | (b << 16)


def win32_to_color(value: Any) -> str:
    n = parse_int(value)
    if n is None or n < 0:
        return ""
    r, g, b = n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"
